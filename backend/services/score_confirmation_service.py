"""月度积分确认。配置行充当结算互斥锁；确认记录写入后不再修改。"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import models
from services import score_board_service as scores

TZ = timezone(timedelta(hours=8))
SUM_FIELDS = ("month_score", "calculate_score", "patent_score", "knowledge_score",
              "train_score", "tech_improve", "deduct_score", "quality_event_score",
              "carrier_inspection_score", "daily_manage", "tech_growth_score",
              "total_calculated", "total_score", "deducted_score")


def now_local():
    # 页面测试结束：固定使用真实北京时间，忽略终端遗留的模拟时间变量。
    return datetime.now(TZ).replace(tzinfo=None)


def next_month(month):
    year, mm = map(int, month.split("-"))
    return f"{year + (mm == 12):04d}-{1 if mm == 12 else mm + 1:02d}"


def deadline(month):
    return datetime.strptime(next_month(month) + "-04", "%Y-%m-%d")


def previous_month(now):
    return (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")


def encode(person):
    payload = json.dumps(person, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return payload, hashlib.sha256(payload.encode("utf-8")).hexdigest()


def initialize(db, now=None):
    if db.get(models.ScoreConfirmationConfig, 1) is None:
        from sqlalchemy.exc import IntegrityError
        try:
            db.add(models.ScoreConfirmationConfig(id=1, start_month=(now or now_local()).strftime("%Y-%m")))
            db.commit()
        except IntegrityError:
            db.rollback()


def synchronize(db, now=None):
    now = now or now_local()
    cfg = db.query(models.ScoreConfirmationConfig).filter_by(id=1).with_for_update().first()
    if cfg is None:
        raise HTTPException(503, "积分确认功能尚未初始化，请重启后端")
    month = next_month(cfg.closed_through) if cfg.closed_through else cfg.start_month
    last = previous_month(now)
    while month <= last:
        cutoff = deadline(month)
        calculation_date = min(now, cutoff - timedelta(microseconds=1)).date()
        data = scores.calculate_public_score_board("month", int(month[:4]), int(month[5:]), db=db, as_of=calculation_date)["data"]
        records = {r.user_id: r for r in db.query(models.MonthlyScoreConfirmation).filter_by(month=month).all()}
        for person in data["people"]:
            rec = records.get(person["user_id"])
            if rec is not None and rec.status != "PENDING":
                continue
            # Details use the same fixed date as totals.
            for detail in person.get("details", []):
                item = db.get(models.WorkItem, detail["work_item_id"])
                if item:
                    detail["deducted_score"] = scores.monthly_progress_deduction(
                        item, month, as_of=calculation_date, include_grace=True)
            payload, fingerprint = encode(person)
            if rec is None:
                rec = models.MonthlyScoreConfirmation(user_id=person["user_id"], month=month)
                db.add(rec)
            rec.snapshot, rec.fingerprint = payload, fingerprint
            rec.status = "AUTO" if now >= cutoff else "PENDING"
            rec.confirmed_at = cutoff if now >= cutoff else None
        if now >= cutoff:
            # Pending rows for subsequently removed people also settle without being lost.
            for rec in records.values():
                if rec.status == "PENDING":
                    rec.status, rec.confirmed_at = "AUTO", cutoff
            cfg.closed_through = month
        month = next_month(month)
    db.flush()
    return cfg


def mine(db, user, now=None):
    now = now or now_local()
    synchronize(db, now)
    records = db.query(models.MonthlyScoreConfirmation).filter_by(user_id=user.id).order_by(
        models.MonthlyScoreConfirmation.month.desc()).all()
    result = [dict(id=r.id, month=r.month, status=r.status, fingerprint=r.fingerprint,
                   deadline=deadline(r.month).isoformat(), confirmed_at=r.confirmed_at,
                   score=json.loads(r.snapshot), self_evaluation=evaluation_info(db, r)) for r in records]
    db.commit()
    return {"code": 200, "data": {"records": result, "server_time": now.isoformat()}}


def confirm(db, user, request_id, fingerprint, now=None):
    now = now or now_local()
    synchronize(db, now)
    rec = db.query(models.MonthlyScoreConfirmation).filter_by(id=request_id, user_id=user.id).first()
    if rec is None:
        db.rollback()
        raise HTTPException(404, "确认记录不存在")
    if rec.status != "PENDING":
        db.commit()
        if rec.status == "CONFIRMED":
            return {"code": 200, "message": "该月份已确认"}
        raise HTTPException(409, "确认期限已过，已按系统得分入账并锁定")
    if rec.fingerprint != fingerprint:
        db.commit()
        raise HTTPException(409, "积分发生变化，请刷新核对后再确认")
    rec.status, rec.confirmed_at = "CONFIRMED", now
    db.commit()
    return {"code": 200, "message": "月度积分已确认并入账"}


def assert_editable(db, user_id, month):
    cfg = db.get(models.ScoreConfirmationConfig, 1)
    rec = db.query(models.MonthlyScoreConfirmation).filter_by(user_id=user_id, month=month).first()
    if rec and rec.status == "IMPORTED":
        raise HTTPException(409, "历史补录积分已锁定")
    if not cfg or month < cfg.start_month:
        return
    if (rec and rec.status != "PENDING") or now_local() >= deadline(month):
        raise HTTPException(409, "该月份积分已入账锁定，不能修改")


def official_board(db, period, year, month, quarter):
    cfg = synchronize(db)
    now = now_local()
    year = year or now.year
    months = scores.months_of_period(period, year, month, quarter)
    records = db.query(models.MonthlyScoreConfirmation).all()
    if months is not None and all(mm < cfg.start_month for mm in months) and not any(r.month in months and r.status == "IMPORTED" for r in records):
        db.commit()
        return scores.calculate_public_score_board(period, year, month, quarter, db)
    # Keep pre-activation history; new months contribute only immutable snapshots.
    historical = scores.calculate_public_score_board(period, year, month, quarter, db)["data"]
    historical_months = sorted({r.month for r in scores.repo.list_all_month_scores(db) if r.month < cfg.start_month} |
                              {r.month for r in scores.repo.list_period_extra_scores(db, None) if r.month < cfg.start_month})
    selected_months = months if months is not None else sorted(set(historical_months + [r.month for r in records]))
    legacy = {}
    for mm in selected_months:
        if mm < cfg.start_month:
            legacy[mm] = scores.calculate_public_score_board("month", int(mm[:4]), int(mm[5:]), db=db)["data"]["people"]
    grouped = {p["user_id"]: [] for p in historical["people"]}
    pending = {}
    for rec in records:
        if rec.month not in selected_months:
            continue
        grouped.setdefault(rec.user_id, [])
        if rec.status == "PENDING":
            pending[rec.user_id] = pending.get(rec.user_id, 0) + 1
        else:
            grouped[rec.user_id].append((rec.month, json.loads(rec.snapshot), rec.status))
    frozen_keys = {(r.user_id, r.month) for r in records if r.status != "PENDING"}
    for mm, people in legacy.items():
        for person in people:
            if (person["user_id"], mm) in frozen_keys:
                continue
            grouped.setdefault(person["user_id"], []).append((mm, person, "HISTORY"))
    identities = {p["user_id"]: p for p in historical["people"]}
    result = []
    for uid, entries in grouped.items():
        identity = identities.get(uid) or (entries[0][1] if entries else {"user_id": uid, "username": uid})
        row = {k: identity.get(k) for k in ("user_id", "username", "role")}
        row.update({key: round(sum(p.get(key, 0) or 0 for _, p, _ in entries), 2) for key in SUM_FIELDS})
        row["details"] = [detail for _, p, _ in entries for detail in p.get("details", [])]
        by_month = {mm: p.get("total_calculated", 0) for mm, p, _ in entries}
        row["period_scores"] = [by_month.get(mm, 0) for mm in selected_months]
        for i in range(4):
            values = row["period_scores"][i*3:i*3+3] if period == "year" else row["period_scores"][i:i+1]
            row[f"period_{i+1}"] = round(sum(values), 2)
        row["confirmation_status"] = entries[0][2] if period == "month" and entries else ("PENDING" if period == "month" else "PARTIAL") if pending.get(uid) else "SETTLED" if entries else "UNCONFIRMED"
        row["confirmed_months"] = len(entries)
        if period == "month":
            record = next((r for r in records if r.user_id == uid and r.month == selected_months[0]), None)
            row["self_evaluation"] = evaluation_info(db, record)
        row["month_locked"] = bool(period == "month" and entries and (selected_months[0] >= cfg.start_month or any(status == "IMPORTED" for _, _, status in entries)))
        if period == "month" and not row["month_locked"]:
            row["_draft_extra"] = {key: identity.get(key, 0) for key in
                ("patent_score", "knowledge_score", "train_score", "deduct_score", "quality_event_score", "carrier_inspection_score")}
        if period == "month" and entries:
            row["summary_only"] = bool(entries[0][1].get("summary_only"))
            if row["summary_only"]:
                for key in ("patent_score", "knowledge_score", "train_score", "deduct_score", "quality_event_score", "carrier_inspection_score"):
                    row[key] = None
            row.update({k: entries[0][1].get(k, 0) for k in ("converted_score", "final_calculated", "grade")})
        # 月度未入账结果用于预览，季度／年度仍只汇总正式结果。
        row["is_provisional"] = bool(period == "month" and not entries)
        if row["is_provisional"]:
            for key in SUM_FIELDS + ("converted_score", "final_calculated", "grade", "details"):
                if key in identity:
                    row[key] = identity[key]
        result.append(row)
    if period != "month":
        ranked = sorted([p["total_calculated"] for p in result], reverse=True)
        base = ranked[4] if len(ranked) >= 5 else (ranked[0] if ranked else 0)
        factor = base / 90.01 if base else 1
        for row in result:
            row["converted_score"] = row["final_calculated"] = round(row["total_calculated"] / factor, 2)
            row["grade"] = scores.grade_of(row["final_calculated"]) if row["confirmed_months"] else "-"
    for row in result:
        row.setdefault("converted_score", 0)
        row.setdefault("final_calculated", 0)
        row.setdefault("grade", "-")
    result.sort(key=lambda p: p["total_calculated"], reverse=True)
    db.commit()
    return {"code": 200, "data": {"period": period, "people": result, "year": year, "month": month,
            "quarter": quarter, "confirmation_start_month": cfg.start_month}}


SELF_EVALUATION_GRADES = {"S", "A", "C", "D"}


def evaluation_info(db, record):
    if record is None or record.status == "IMPORTED":
        return {"status": "NOT_REQUIRED", "content": ""}
    eligible = json.loads(record.snapshot).get("grade") in SELF_EVALUATION_GRADES
    pending = db.query(models.MonthlyScoreConfirmation.id).filter_by(month=record.month, status="PENDING").first()
    evaluation = db.query(models.MonthlyScoreSelfEvaluation).filter_by(confirmation_id=record.id).first()
    status = "SUBMITTED" if evaluation else "NOT_REQUIRED" if not eligible else "WAITING" if pending else "REQUIRED"
    return {"status": status, "content": evaluation.content if evaluation else "",
            "submitted_at": evaluation.submitted_at if evaluation else None}


def save_evaluation(db, user, request_id, content):
    synchronize(db)
    record = db.query(models.MonthlyScoreConfirmation).filter_by(id=request_id, user_id=user.id).first()
    if record is None:
        raise HTTPException(404, "确认记录不存在")
    info = evaluation_info(db, record)
    if info["status"] in ("NOT_REQUIRED", "WAITING") or json.loads(record.snapshot).get("grade") not in SELF_EVALUATION_GRADES:
        raise HTTPException(409, "仅在本月所有人员积分入账后，S、A、C、D等级人员可填写自评")
    content = content.strip()
    if not content or len(content) > 500:
        raise HTTPException(422, "请填写1—500字自评")
    evaluation = db.query(models.MonthlyScoreSelfEvaluation).filter_by(confirmation_id=record.id).first()
    if evaluation is None:
        evaluation = models.MonthlyScoreSelfEvaluation(confirmation_id=record.id)
        db.add(evaluation)
    evaluation.content = content
    evaluation.submitted_at = now_local()
    db.commit()
    return {"code": 200, "message": "自评已保存"}
