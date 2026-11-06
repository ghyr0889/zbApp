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


def source_edit_deadline(month):
    # 原始积分编辑锁定规则独立于确认，取消确认期限不改变填报窗口。
    return datetime.strptime(next_month(month) + "-06", "%Y-%m-%d")


def calculation_cutoff(month):
    # 月度积分仅核算所属月份，之后可随时确认。
    return datetime.strptime(next_month(month) + "-01", "%Y-%m-%d")


def previous_month(now):
    return (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")


def encode(person):
    payload = json.dumps(person, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return payload, hashlib.sha256(payload.encode("utf-8")).hexdigest()


def confirmation_payload(person):
    # 不将其他人的得分决定的折算结果放进个人确认快照和指纹。
    return {key: value for key, value in person.items()
            if key not in ("converted_score", "final_calculated", "grade")}


def finalize_month_if_ready(db, settlement, now):
    if settlement.status == "SETTLED":
        return True
    db.flush()
    records = db.query(models.MonthlyScoreConfirmation).filter_by(month=settlement.month).all()
    if any(record.status not in ("CONFIRMED", "AUTO") for record in records):
        return False
    if not records:
        return False
    if settlement.status == "LEGACY":
        # 已按旧规则确认的折算分快照不可重算。
        return True
    totals = [float(json.loads(record.snapshot).get("total_calculated") or 0) for record in records]
    ranked = sorted(totals, reverse=True)
    base = ranked[4] if len(ranked) >= 5 else (ranked[0] if ranked else 0)
    factor = base / 90.01 if base else 1
    for record, total in zip(records, totals):
        converted = round(total / factor, 2)
        db.add(models.MonthlyScoreConversion(settlement_id=settlement.id,
            confirmation_id=record.id, converted_score=converted, grade=scores.grade_of(converted)))
    settlement.status, settlement.conversion_factor, settlement.settled_at = "SETTLED", factor, now
    db.flush()
    return True


def initialize(db, now=None):
    if db.get(models.ScoreConfirmationConfig, 1) is None:
        from sqlalchemy.exc import IntegrityError
        try:
            db.add(models.ScoreConfirmationConfig(id=1, start_month=(now or now_local()).strftime("%Y-%m")))
            db.commit()
        except IntegrityError:
            db.rollback()


def advance_closed_through(cfg, month):
    """只推进连续完成的月份，未确认的较早月份不能被跳过。"""
    expected = next_month(cfg.closed_through) if cfg.closed_through else cfg.start_month
    if month == expected:
        cfg.closed_through = month


def synchronize(db, now=None):
    now = now or now_local()
    cfg = db.query(models.ScoreConfirmationConfig).filter_by(id=1).with_for_update().first()
    if cfg is None:
        raise HTTPException(503, "积分确认功能尚未初始化，请重启后端")
    month = next_month(cfg.closed_through) if cfg.closed_through else cfg.start_month
    last = previous_month(now)
    # 兼容旧版本可能已将游标推进到仍有未确认记录之后的情况。
    pending_months = {row[0] for row in db.query(models.MonthlyScoreConfirmation.month).filter(
        models.MonthlyScoreConfirmation.status == "PENDING",
        models.MonthlyScoreConfirmation.month >= cfg.start_month,
        models.MonthlyScoreConfirmation.month <= last,
    ).distinct().all()}
    if pending_months:
        month = min(month, min(pending_months))
    while month <= last:
        if cfg.closed_through and month <= cfg.closed_through and month not in pending_months:
            month = next_month(month)
            continue
        calculation_date = min(now, calculation_cutoff(month) - timedelta(microseconds=1)).date()
        data = scores.calculate_public_score_board("month", int(month[:4]), int(month[5:]), db=db, as_of=calculation_date)["data"]
        records = {r.user_id: r for r in db.query(models.MonthlyScoreConfirmation).filter_by(month=month).all()}
        settlement = db.query(models.MonthlyScoreSettlement).filter_by(month=month).first()
        first_sync = settlement is None
        if first_sync and not records and not data["people"]:
            # 无参与人员时不提前冻结空名单，稍后有人员时仍可初始化。
            month = next_month(month)
            continue
        # 部署前已全部入账的月份保留原快照及原折算结果。
        if first_sync and records and all(r.status in ("CONFIRMED", "AUTO", "IMPORTED") for r in records.values()):
            advance_closed_through(cfg, month)
            month = next_month(month)
            continue
        if first_sync:
            legacy = any(r.status in ("CONFIRMED", "AUTO", "IMPORTED") for r in records.values())
            settlement = models.MonthlyScoreSettlement(month=month, status="LEGACY" if legacy else "WAITING")
            db.add(settlement)
            db.flush()
        if settlement.status == "SETTLED":
            advance_closed_through(cfg, month)
            month = next_month(month)
            continue
        for person in data["people"]:
            rec = records.get(person["user_id"])
            if rec is None and not first_sync:
                continue  # 首次同步固定当月参与名单
            if rec is not None and rec.status != "PENDING":
                continue
            payload, fingerprint = encode(person if settlement.status == "LEGACY" else confirmation_payload(person))
            if rec is None:
                rec = models.MonthlyScoreConfirmation(user_id=person["user_id"], month=month)
                db.add(rec)
            rec.snapshot, rec.fingerprint = payload, fingerprint
            rec.status = "PENDING"
            rec.confirmed_at = None
        if finalize_month_if_ready(db, settlement, now):
            advance_closed_through(cfg, month)
        month = next_month(month)
    db.flush()
    return cfg


def mine(db, user, now=None):
    now = now or now_local()
    synchronize(db, now)
    records = db.query(models.MonthlyScoreConfirmation).filter_by(user_id=user.id).order_by(
        models.MonthlyScoreConfirmation.month.desc()).all()
    settlements = {s.month: s for s in db.query(models.MonthlyScoreSettlement).all()}
    result = [dict(id=r.id, month=r.month, status=r.status, fingerprint=r.fingerprint,
                   deadline=None, confirmed_at=r.confirmed_at,
                   score=json.loads(r.snapshot), self_evaluation=evaluation_info(db, r),
                   settlement_status=settlements[r.month].status if r.month in settlements else None) for r in records]
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
        raise HTTPException(409, "该积分记录已入账并锁定")
    if rec.fingerprint != fingerprint:
        db.commit()
        raise HTTPException(409, "积分发生变化，请刷新核对后再确认")
    rec.status, rec.confirmed_at = "CONFIRMED", now
    db.flush()
    settlement = db.query(models.MonthlyScoreSettlement).filter_by(month=rec.month).first()
    if settlement:
        finalize_month_if_ready(db, settlement, now)
    # 按月份顺序重扫；补确认旧月份后也能安全推进已结算的后续月份。
    synchronize(db, now)
    db.commit()
    message = ("月度积分已确认并入账" if settlement and settlement.status == "LEGACY" else
               "计算总分已确认，折算结果已生成" if settlement and settlement.status == "SETTLED" else
               "计算总分已确认，等待其他人员确认")
    return {"code": 200, "message": message}

# 锁定状态
def assert_editable(db, user_id, month):
    cfg = db.get(models.ScoreConfirmationConfig, 1)
    rec = db.query(models.MonthlyScoreConfirmation).filter_by(user_id=user_id, month=month).first()
    if rec and rec.status == "IMPORTED":
        raise HTTPException(409, "历史补录积分已锁定")
    if not cfg or month < cfg.start_month:
        return
    if (rec and rec.status != "PENDING") or now_local() >= source_edit_deadline(month):
        raise HTTPException(409, "该月份原始积分填报已截止或已锁定，不能修改")


def official_board(db, period, year, month, quarter):
    cfg = synchronize(db)
    now = now_local()
    year = year or now.year
    months = scores.months_of_period(period, year, month, quarter)
    records = db.query(models.MonthlyScoreConfirmation).all()
    settlements = {s.month: s for s in db.query(models.MonthlyScoreSettlement).all()}
    conversions = {c.confirmation_id: c for c in db.query(models.MonthlyScoreConversion).all()}
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
        settlement = settlements.get(rec.month)
        if rec.status == "PENDING" or (period != "month" and settlement and settlement.status == "WAITING"):
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
            pending_record = next((r for r in records if r.user_id == uid and r.month == selected_months[0] and r.status == "PENDING"), None)
            preview = json.loads(pending_record.snapshot) if pending_record else identity
            for key in SUM_FIELDS + ("converted_score", "final_calculated", "grade", "details"):
                if key in preview:
                    row[key] = preview[key]
        active_month = period == "month" and selected_months[0] >= cfg.start_month and (not cfg.closed_through or selected_months[0] > cfg.closed_through)
        if period == "month" and ((selected_months[0] in settlements and settlements[selected_months[0]].status != "LEGACY") or (selected_months[0] not in settlements and active_month)):
            settlement = settlements.get(selected_months[0])
            record = next((r for r in records if r.user_id == uid and r.month == selected_months[0]), None)
            conversion = conversions.get(record.id) if record else None
            row["settlement_status"] = settlement.status if settlement else "WAITING"
            row["converted_score"] = conversion.converted_score if conversion else None
            row["final_calculated"] = conversion.converted_score if conversion else None
            row["grade"] = conversion.grade if conversion else None
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
    settlement = db.query(models.MonthlyScoreSettlement).filter_by(month=record.month).first()
    if settlement and settlement.status != "LEGACY":
        if settlement.status != "SETTLED":
            return {"status": "WAITING", "content": ""}
        conversion = db.query(models.MonthlyScoreConversion).filter_by(confirmation_id=record.id).first()
        eligible = bool(conversion and conversion.grade in SELF_EVALUATION_GRADES)
    else:
        eligible = json.loads(record.snapshot).get("grade") in SELF_EVALUATION_GRADES
    pending = db.query(models.MonthlyScoreConfirmation.id).filter_by(month=record.month, status="PENDING").first()
    evaluation = db.query(models.MonthlyScoreSelfEvaluation).filter_by(confirmation_id=record.id).first()
    status = "NOT_REQUIRED" if not eligible else "SUBMITTED" if evaluation else "WAITING" if pending else "REQUIRED"
    return {"status": status, "content": evaluation.content if evaluation else "",
            "submitted_at": evaluation.submitted_at if evaluation else None}


def save_evaluation(db, user, request_id, content):
    synchronize(db)
    record = db.query(models.MonthlyScoreConfirmation).filter_by(id=request_id, user_id=user.id).first()
    if record is None:
        raise HTTPException(404, "确认记录不存在")
    info = evaluation_info(db, record)
    if info["status"] in ("NOT_REQUIRED", "WAITING"):
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
