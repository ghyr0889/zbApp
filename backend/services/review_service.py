#数据库事务与核心业务。将复杂的“审核状态更新 + 账号积分增加 + 插入流水账”原子化打包在事务层。

from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import WorkLog, User, WorkLog, LogStatus
from schemas import ReviewAction

def process_log_review(log_id: int, action: ReviewAction, db: Session):
    log = db.query(WorkLog).filter(WorkLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="工作日志不存在")

    if log.status != LogStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"该日志已被处理，当前状态为: {log.status.value}")

    reviewer = db.query(User).filter(User.id == action.reviewer_id).first()
    if not reviewer or reviewer.role not in ["OWNER"]:
        raise HTTPException(status_code=403, detail="无权操作：需要负责人权限")

    try:
        now = datetime.now()
        log.reviewer_id = action.reviewer_id
        log.review_remark = action.remark
        log.reviewed_at = now

        # 场景 1: 驳回
        if not action.approved:
            log.status = LogStatus.REJECTED
            log.final_score = 0.0
            db.commit()
            return {"log_id": log.id, "status": log.status.value, "score_added": 0.0}

        # 场景 2: 通过 (开启事务控制)
        log.status = LogStatus.APPROVED
        final_score = action.override_score if action.override_score is not None else log.applied_score
        log.final_score = final_score

        worker = db.query(User).filter(User.id == log.user_id).first()
        worker.current_score += final_score

        score_log = WorkLog(
            user_id=log.user_id,
            work_log_id=log.id,
            score_change=final_score,
            balance_after=worker.current_score,
            created_at=now
        )
        db.add(score_log)

        # 事务统一提交
        db.commit()
        return {
            "log_id": log.id,
            "status": log.status.value,
            "added_score": final_score,
            "new_total_score": worker.current_score
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库事务执行失败: {str(e)}")