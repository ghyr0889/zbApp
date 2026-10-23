"""Admin historical summaries: draft first, immutable publication second."""
import json
from fastapi import HTTPException
import models
from services import score_confirmation_service as confirmation


def admin(user):
    if str(user.role).upper() != "ADMIN":
        raise HTTPException(403, "仅管理员可补录历史积分")


def lock_config(db):
    cfg = db.query(models.ScoreConfirmationConfig).filter_by(id=1).with_for_update().first()
    if cfg is None:
        raise HTTPException(503, "积分确认尚未初始化")
    return cfg


def validate_target(db, user_id, month, cfg):
    if month >= cfg.start_month:
        year, mm = map(int, cfg.start_month.split("-"))
        previous_year, previous_month = (year - 1, 12) if mm == 1 else (year, mm - 1)
        raise HTTPException(409, f"本系统从{year}年{mm}月起执行积分确认，仅允许补录{previous_year}年{previous_month}月及以前的历史积分。")
    if db.query(models.MonthlyScoreConfirmation.id).filter_by(user_id=user_id, month=month).first():
        raise HTTPException(409, "该人员月份已有确认记录，禁止覆盖")
    person = db.get(models.User, user_id)
    if person is None:
        raise HTTPException(404, "人员不存在")
    return person


def listing(db, user):
    admin(user)
    cfg = db.get(models.ScoreConfirmationConfig, 1)
    rows = db.query(models.HistoricalScoreDraft).order_by(models.HistoricalScoreDraft.id.desc()).all()
    return {"code": 200, "data": {"start_month": cfg.start_month if cfg else None,
        "people": [{"user_id": u.id, "username": u.username} for u in db.query(models.User).all()],
        "drafts": [{"id": r.id, "user_id": r.user_id, "month": r.month, "status": r.status,
                    "reason": r.reason, "snapshot": json.loads(r.snapshot),
                    "fingerprint": confirmation.encode({"snapshot": json.loads(r.snapshot), "reason": r.reason})[1], "updated_at": r.updated_at,
                    "updated_by_id": r.updated_by_id, "published_at": r.published_at} for r in rows]}}


def save(db, user, body):
    admin(user)
    cfg = lock_config(db)
    person = validate_target(db, body.user_id, body.month, cfg)
    reason = body.reason.strip()
    if not reason:
        raise HTTPException(422, "补录说明不能为空")
    row = db.query(models.HistoricalScoreDraft).filter_by(user_id=body.user_id, month=body.month).first()
    if row and row.status != "DRAFT":
        raise HTTPException(409, "已入账记录不能修改")
    if row is None:
        row = models.HistoricalScoreDraft(user_id=body.user_id, month=body.month)
        db.add(row)
    data = body.model_dump(exclude={"user_id", "month", "reason"})
    data.update(user_id=person.id, username=person.username, role=person.role, details=[],
                total_score=body.total_calculated, final_calculated=body.converted_score,
                source="HISTORICAL_IMPORT", summary_only=True)
    row.snapshot, fingerprint = confirmation.encode(data)
    row.reason, row.updated_by_id, row.updated_at = reason, user.id, confirmation.now_local()
    row.status = "DRAFT"
    db.commit()
    return {"code": 200, "message": "草稿已保存", "data": {"id": row.id}}


def publish(db, user, draft_id, fingerprint):
    admin(user)
    cfg = lock_config(db)
    row = db.query(models.HistoricalScoreDraft).filter_by(id=draft_id).first()
    if row is None:
        raise HTTPException(404, "草稿不存在")
    if row.status != "DRAFT":
        raise HTTPException(409, "该记录已入账")
    validate_target(db, row.user_id, row.month, cfg)
    data = json.loads(row.snapshot)
    payload, current = confirmation.encode({"snapshot": data, "reason": row.reason})
    if fingerprint != current:
        raise HTTPException(409, "草稿已变化，请刷新核对后再入账")
    snapshot, score_hash = confirmation.encode(data)
    now = confirmation.now_local()
    db.add(models.MonthlyScoreConfirmation(user_id=row.user_id, month=row.month, status="IMPORTED",
           snapshot=snapshot, fingerprint=score_hash, confirmed_at=now))
    row.status, row.published_at, row.updated_by_id = "PUBLISHED", now, user.id
    db.commit()
    return {"code": 200, "message": "历史积分已入账并锁定"}
