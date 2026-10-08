"""接口层：只接收参数、注入数据库会话并调用业务层。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import MonthScoreIn, MonthlyExtraScoreIn
from services import score_board_service as service

router = APIRouter(prefix='/api/v1/score-board', tags=['Score Board'])


@router.get("/score-board/{user_id}")
def get_score_board(user_id: str,
                    period: str = "all",
                    year: int = None,
                    month: int = None,
                    quarter: int = None,
                    db: Session = Depends(get_db)):
    return service.get_score_board(
        user_id=user_id,
        period=period,
        year=year,
        month=month,
        quarter=quarter,
        db=db,
    )


@router.get("/public-score-board")
def get_public_score_board(period: str = "all",
                           year: int = None,
                           month: int = None,
                           quarter: int = None,
                           db: Session = Depends(get_db)):
    """所有人员积分面板：按 月/季/年 计算 技术提升、日常管理、技术成长分、计算总分、折算得分、等级。"""
    return service.get_public_score_board(period=period, year=year, month=month, quarter=quarter, db=db)


@router.put("/work-items/{work_item_id}/quality_score")
def put_quality_score(work_item_id: int, data: MonthScoreIn, db: Session = Depends(get_db)):
    return service.put_quality_score(work_item_id=work_item_id, data=data, db=db)


@router.put("/work-items/{work_item_id}/month-score")
def save_month_score(work_item_id: int, body: MonthScoreIn, db: Session = Depends(get_db)):
    """保存工作项本月分值：员工直接填写、直接生效，不经过审核。"""
    return service.save_month_score(work_item_id=work_item_id, body=body, db=db)


@router.put("/monthly-extra-scores")
def put_monthly_extra_scores(data: MonthlyExtraScoreIn, db: Session = Depends(get_db)):
    """领导按月为人员设置 技术提升/日常管理 附加分（存在则更新，否则创建）。"""
    return service.put_monthly_extra_scores(data=data, db=db)


@router.get("/monthly-extra-scores")
def get_monthly_extra_scores(user_id: str = None, month: str = None, db: Session = Depends(get_db)):
    """查询月度附加分：传 user_id+month 查单条；只传 month 查该月所有人员；都不传查全部。"""
    return service.get_monthly_extra_scores(user_id=user_id, month=month, db=db)


@router.get("/completed-situation")
def get_completed_situation(target_type: str = "project",
                            currentUserId: str = None,
                            target_id: int = None,
                            category_name: str = None,
                            month: str = None,
                            db: Session = Depends(get_db)):
    """按 项目 / 工作包类别 查看该对象下每位工作人员的完成情况（分值口径）：
    total_score    = 其负责工作项的基础总分值之和
    filled_score   = 这些工作项已填月度分值之和（传 month 只算该月，缺省累计全部月份）
    unfilled_score = total_score - filled_score（还没填的分）
    仅领导/管理员可查看。"""
    return service.get_completed_situation(
        target_type=target_type,
        currentUserId=currentUserId,
        target_id=target_id,
        category_name=category_name,
        month=month,
        db=db,
    )


@router.get("/project-summary")
def get_project_summary(currentUserId: str = None,
                        period: str = "all",
                        year: int = None,
                        month: int = None,
                        quarter: int = None,
                        target_type: str = "project",
                        db: Session = Depends(get_db)):
    """按项目汇总分值（可按 月 / 季 / 年 / 全部 统计）。仅领导、管理员可查看。
    - total_score    = 项目下所有工作项满分之和（不随周期变化）
    - filled_score   = 这些工作项在周期内已填的月度基础分值之和
    - unfilled_score = total_score - filled_score
    """
    return service.get_project_summary(
        currentUserId=currentUserId,
        period=period,
        year=year,
        month=month,
        quarter=quarter,
        target_type=target_type,
        db=db,
    )
