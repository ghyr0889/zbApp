
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import MonthScoreIn, MonthlyExtraScoreIn
from utils import ensure_open, item_filled_score, auto_create_complete_request
import logging
from datetime import timedelta

router = APIRouter(prefix="/api/v1/score-board", tags=["Score Board"])


def pearse_node_dat(node_str):
    if not node_str:
        return datetime.max
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(node_str))
    if match:
        try:
            return datetime.strptime(match.group(), "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.max



def month_in_selection(month_str, period, year, month = None, quarter = None):
    """月度分值(YYYY-MM)是否落在所选周期内（month / quarter / year / all）。"""
    period = str(period).lower()
    if not month_str:
        return False
    try:
        y = int(str(month_str)[:4])
        m = int(str(month_str)[5:7])
    except (ValueError, IndexError):
        return False
    if period == "month":
        return y == year and m == month
    if period == "quarter":
        return y == year and (m - 1) // 3 + 1 == quarter
    if period == "year":
        return y == year
    return True  # all


def months_of_period(period, year, month=None, quarter=None):
    """某个周期包含的月份列表（YYYY-MM）；period=all 返回 None（表示不限月份）。

    month → 该月；quarter → 该季度 3 个月；year → 12 个月。
    """
    period = str(period or "all").lower()
    now = datetime.now()
    y = year or now.year

    if period == "month":
        m = int(month or now.month)
        return [f"{y:04d}-{m:02d}"]
    if period == "quarter":
        q = int(quarter or ((now.month - 1) // 3 + 1))
        base = (q - 1) * 3 + 1
        return [f"{y:04d}-{mm:02d}" for mm in (base, base + 1, base + 2)]
    if period == "year":
        return [f"{y:04d}-{mm:02d}" for mm in range(1, 13)]
    return None  # all


# ---------------------------------------------------------------- 可填写月份窗口（每月前2天可补填上月）
def _prev_month_str(now):
    """上个月 YYYY-MM（跨年处理）。"""
    y, m = now.year, now.month
    if m == 1:
        return f"{y - 1:04d}-12"
    return f"{y:04d}-{m - 1:02d}"


def fillable_months(now=None):
    """当前可填写分值的月份集合：本月；若今天是当月前2天，则还包括上个月。"""
    now = now or datetime.now()
    months = {now.strftime("%Y-%m")}
    if now.day <= 2:
        months.add(_prev_month_str(now))
    return months


def assert_month_fillable(month):
    """校验填写目标月份是否在当前允许窗口内。"""
    month = (month or "").strip()
    if not month:
        raise HTTPException(status_code=400, detail="月份不能为空")
    if month not in fillable_months():
        raise HTTPException(status_code=400, detail="只能填写本月分值；每月前2天可补填上月分值，窗口过后不可补填")
    return month


def compute_deducted(item):
    """通过时间超出 deadline 7 天以上才扣 1 分。"""
    if not item.completed_at or not item.deadline:
        return 0.0
    if item.completed_at > item.deadline + timedelta(days=7):
        return 1.0
    return 0.0

def monthly_quality_score(db, work_item_id, month):
    """M月质量分 = 当月显式值 → 之前最近显式值 → 0（不再使用工作项全局默认）"""
    rows = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == work_item_id,
        models.WorkItemMonthlyScore.quality_score.isnot(None),
        models.WorkItemMonthlyScore.month <= month
    ).order_by(models.WorkItemMonthlyScore.month.desc()).all()
    if rows:
        return rows[0].quality_score
    return 0.0

def monthly_score_detail(rec, db):
    """把一条月度分值记录展开为积分面板需要的明细结构。"""
    item = rec.work_item
    wp = item.work_package if item else None
    project = wp.project if wp else None
    return {
        "work_item_id": item.id if item else None,
        "work_item_name": item.name if item else "-",
        "work_item_standard": item.standard if item else "-",
        "work_item_difficulty": item.difficulty if item else "-",
        "work_item_importance": item.importance if item else "-",
        "work_item_innovation": item.innovation if item else "-",
        "work_package_id": wp.id,
        "work_package_code": wp.code if wp else None,
        "work_package_category": wp.category_name if wp else "-",
        "project_id": project.id if project else None,
        "project_name": project.name if project else "-",
        "project_code": project.code if project else "-",
        "month": rec.month,
        "score": rec.score,
        "quality_score": monthly_quality_score(db, rec.work_item_id, rec.month),
        "calculate_score": rec.calculate_score if rec.calculate_score is not None else 0.0,
        "deducted_score": compute_deducted(item),
    }

def compute_calc_score(month_score, item, db, owner_job_grade, quality_score=None):
    """计算得分 = 本月基础得分 × (难度系数 + 创新度系数 + 重要度系数)＋质量分。
    难度/重要度系数按工作包负责人职级查；创新度系数按工作项创新度查。
    """
    if quality_score is None:
        quality_score = 0.0

    factor_map = {}
    for lv in db.query(models.ScoreDimensionLevel).all():
        factor_map.setdefault((lv.variable, lv.job_grade or "", lv.level), lv.factor or 0)

    owner_grade = owner_job_grade or ""
    difficulty_f = round(factor_map.get(("difficulty", owner_grade, item.difficulty), 0), 3)
    importance_f = round(factor_map.get(("importance", owner_grade, item.importance), 0), 3)
    innovation_f = round(factor_map.get(("innovation", "", item.innovation), 0), 3)

    logging.debug(f"计算得分: 工作项：{item.name}, 分值={month_score}, 困难度系数={difficulty_f},  重要度系数={importance_f}, 创新度系数={innovation_f}, 质量分={quality_score}")
    result = round((month_score or 0.0) * (difficulty_f + innovation_f + importance_f) + (quality_score or 0.0), 3)
    logging.debug(f"结果:result = {result}")

    return result


# ---------------------------------------------------------------- 积分（数据源：工作项月度分值）
@router.get("/score-board/{user_id}")
def get_score_board(user_id: str, 
                    period: str = "all", 
                    year: int = None,
                    month: int = None,
                    quarter: int = None,
                    db: Session = Depends(get_db)):
    now = datetime.now()
    y = year or now.year #未指定年份默认当前年

    records = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.user_id == user_id
    ).all()
    filtered = [r for r in records if month_in_selection(r.month, period, y, month, quarter)]
    total_score = sum(r.score or 0.0 for r in filtered)
    details = [monthly_score_detail(r, db) for r in filtered]
    deducted = sum(compute_deducted(r.work_item) for r in {r.work_item_id: r for r in filtered}.values())
    return {
        "code": 200,
        "data": {
            "total_score": total_score,
            "deducted_score": deducted,
            "period": period,
            "details": details,
            "year": y,
            "month": month,
            "quarter": quarter
        }
    }

def grade_of(score):
    """等级：>95:S  90~95:A  75~90:B  60~75:C  <60:D"""
    if score > 95:
        return "S"
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"


@router.get("/public-score-board")
def get_public_score_board(period: str = "all",
                           year: int = None,
                           month: int = None,
                           quarter: int = None,
                           db: Session = Depends(get_db)):
    """所有人员积分面板：按 月/季/年 计算 技术提升、日常管理、技术成长分、计算总分、折算得分、等级。"""
    period = str(period or "all").lower()
    now = datetime.now()
    y = year or now.year

    # 周期内月份集合（month / quarter / year / all）
    months = months_of_period(period, y, month, quarter)

    users = db.query(models.User).filter(
        models.User.role.notin_(["LEADER", "ADMIN"]),
        models.User.is_deleted.isnot(True)).all()
    all_records = db.query(models.WorkItemMonthlyScore).all()

    # 周期内的月度附加分（技术提升 / 日常管理）
    extra_q = db.query(models.MonthlyExtraScore)
    if months:
        extra_q = extra_q.filter(models.MonthlyExtraScore.month.in_(months))
    extras = extra_q.all()

    people = []
    for user in users:
        # 周期内该用户的月度记录
        user_records = []
        for rec in all_records:
            if rec.user_id != user.id:
                continue
            if months is None or rec.month in months:
                user_records.append(rec)

        # 按月统计：本月分值、计算分
        month_score_map = {}
        calc_map = {}
        for r in user_records:
            month_score_map[r.month] = month_score_map.get(r.month, 0.0) + (r.score or 0.0)
            calc_map[r.month] = calc_map.get(r.month, 0.0) + (r.calculate_score or 0.0)

        # 按月统计：技术提升 / 日常管理 子项
        extra_map = {}
        for e in extras:
            if e.user_id != user.id:
                continue
            extra_map[e.month] = (
                (e.patent_score or 0.0),
                (e.knowledge_score or 0.0),
                (e.train_score or 0.0),
                (e.deduct_score or 0.0),
                (e.quality_event_score or 0.0),
                (e.carrier_inspection_score or 0.0),
            )

        # 该用户涉及的所有月份
        if months is not None:
            months_used = months
        else:
            months_used = sorted(set(list(month_score_map) + list(extra_map) + [r.month for r in user_records]))

        # 各月「计算总分」= 该月计算分 + 该月技术提升合计 + 该月日常管理合计
        period_scores = []
        for mm in months_used:
            calc = calc_map.get(mm, 0.0)
            p, k, t, dd, qe, ci = extra_map.get(mm, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            period_scores.append(round(calc + p + k + t + dd + qe + ci, 2))

        month_score_total = round(sum(month_score_map.values()), 2)
        calc_total = round(sum(calc_map.values()), 2)
        deduct_total = round(sum(compute_deducted(r.work_item) for r in {r.work_item_id: r for r in user_records}.values()), 2) #进度扣分
        patent = round(sum(v[0] for v in extra_map.values()), 2)
        knowledge = round(sum(v[1] for v in extra_map.values()), 2)
        train = round(sum(v[2] for v in extra_map.values()), 2)
        deduct = round(sum(v[3] for v in extra_map.values()), 2)
        quality_event = round(sum(v[4] for v in extra_map.values()), 2)
        carrier_inspection = round(sum(v[5] for v in extra_map.values()), 2)
        tech_total = round(patent + knowledge + train, 2)          # 技术提升总得分
        daily_total = round(deduct + quality_event + carrier_inspection, 2)  # 日常管理总得分

        # 公式
        tech_growth_score = round(calc_total - month_score_total + tech_total, 2)  # 技术成长分
        total_calculated = round(calc_total + tech_total + daily_total - deduct_total, 2)          # 计算总分

        people.append({
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "month_score": month_score_total,
            "calculate_score": calc_total,
            "patent_score": patent,
            "knowledge_score": knowledge,
            "train_score": train,
            "tech_improve": tech_total,
            "deduct_score": deduct,
            "quality_event_score": quality_event,
            "carrier_inspection_score": carrier_inspection,
            "daily_manage": daily_total,
            "tech_growth_score": tech_growth_score,
            "total_calculated": total_calculated,
            "total_score": total_calculated,   # 计算总分（季度/年度=各月计算总分之和）
            "converted_score": 0.0,            # 折算得分（月度），下方计算
            "final_calculated": 0.0,           # 计算得分（季度/年度），下方计算
            "grade": "-",
            "period_scores": period_scores,
            # 动态切片求和：如果是年度，则把12个月的数据按季度(每3个月)累加；否则正常取单月值
            "period_1": round(sum(period_scores[0:3]), 2) if period == "year" else (period_scores[0] if len(period_scores) >= 1 else 0),
            "period_2": round(sum(period_scores[3:6]), 2) if period == "year" else (period_scores[1] if len(period_scores) >= 2 else 0),
            "period_3": round(sum(period_scores[6:9]), 2) if period == "year" else (period_scores[2] if len(period_scores) >= 3 else 0),
            "period_4": round(sum(period_scores[9:12]), 2) if period == "year" else 0,
            "deducted_score": sum(compute_deducted(r.work_item) for r in {r.work_item_id: r for r in user_records}.values()),
            "details": [monthly_score_detail(r, db) for r in user_records],
        })

    # 计算系数 = 计算总分第5名 / 90.01（不足5人取最高分）
    sorted_calc = sorted([p["total_calculated"] for p in people], reverse=True)
    rank5 = sorted_calc[4] if len(sorted_calc) >= 5 else (sorted_calc[0] if sorted_calc else 0.0)
    factor = rank5 / 90.01 if rank5 else 1.0

    for p in people:
        final = round(p["total_calculated"] / factor, 2) if factor else p["total_calculated"]
        p["converted_score"] = final
        p["final_calculated"] = final
        p["grade"] = grade_of(final)

    people.sort(key=lambda p: p["total_calculated"], reverse=True)
    return {"code": 200, "data": {"period": period, "people": people, "year": y, "month": month, "quarter": quarter}}

@router.put("/work-items/{work_item_id}/quality_score")
def put_quality_score(work_item_id: int, data: MonthScoreIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = str(user.role).upper()

    if role != "LEADER":
        raise HTTPException(status_code = 403, detail = "只有领导可以编辑质量分")

    score = round(float(data.quality_score or 0.0), 2)
    item = db.query(models.WorkItem).filter(models.WorkItem.id == work_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")
    ensure_open(item, item.work_package,
                item.work_package.project if item.work_package else None)  # 已关闭不能再填质量分
    month = data.month or datetime.now().strftime("%Y-%m")
    rec = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == work_item_id,
        models.WorkItemMonthlyScore.month == month).first()

    owner_job_grade = item.owner.job_grade if (item and item.owner) else ""

    if rec:
        rec.quality_score = score
        rec.quality_score_updated_at = datetime.now()

        # 本月分值已填过 → 用新质量分重算本月计算分
        rec.calculate_score = compute_calc_score(rec.score, item, db, owner_job_grade, score)
    else:
        rec = models.WorkItemMonthlyScore(
            work_item_id=work_item_id, 
            user_id=data.user_id,      # 修改为 data.user_id
            month=month, 
            score=0.0,
            quality_score=score, 
            quality_score_updated_at=datetime.now() # 修改为 datetime.now()
        )
        db.add(rec)

    db.commit()

    return{
        "code": 200,
        "message": "质量分已保存",
        "data":{
            "work_item_id": work_item_id,
            "quality_score": data.quality_score
        }
    }

@router.put("/work-items/{work_item_id}/month-score")
def save_month_score(work_item_id: int, body: MonthScoreIn, db: Session = Depends(get_db)):
    """保存工作项本月分值：员工直接填写、直接生效，不经过审核。"""
    item = db.query(models.WorkItem).filter(models.WorkItem.id == work_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")
    ensure_open(item, item.work_package,
                item.work_package.project if item.work_package else None)  # 已关闭不能再填本月分值

    user = db.query(models.User).filter(models.User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 权限：工作包/工作项负责人本人，或领导/管理员
    role = str(user.role).upper()
    work_package = item.work_package
    is_item_owner = bool(item.owner_id and item.owner_id == user.id)
    if role not in ["LEADER", "ADMIN"] and not is_item_owner:
        raise HTTPException(status_code=403, detail="只有工作项负责人本人、领导和管理员可以填写本月分值")

    month = (body.month or "").strip()
    if not month:
        raise HTTPException(status_code=400, detail="月份不能为空")
    assert_month_fillable(month) # 只能填写本月；每月前2天可补填上月（窗口校验）

    db.flush()
    rec = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == work_item_id,
        models.WorkItemMonthlyScore.month == month
    ).first()

    old_score = rec.score if rec else 0.0

    acc_all = item_filled_score(db, work_item_id)

    acc_other = acc_all - (old_score or 0.0)
    remain = (item.score or 0.0) - acc_other

    score = round(float(body.score or 0.0), 3)
    if score > remain + 1e-6:
        raise HTTPException(status_code=400, detail=f"本月分值不能超过剩余分值 {remain}")

    # 积分归属：优先记给工作项负责人（转办拆分后接收人负责的工作项归接收人），
    # 其次记给工作包负责人（领导/管理员代填也不改变归属）；都没有再兜底记给填写人
    if item.owner_id:
        owner_id = item.owner_id
    elif work_package and work_package.owner_id:
        owner_id = work_package.owner_id
    else:
        owner_id = user.id
    if rec:
        rec.score = score
        rec.user_id = owner_id
    else:
        rec = models.WorkItemMonthlyScore(
            work_item_id=work_item_id,
            user_id=owner_id,
            month=month,
            score=score
        )
        db.add(rec)

    # 按当时规则固化计算得分（改规则后不影响已保存的历史月份）
    q = monthly_quality_score(db, work_item_id, month)
    owner_job_grade = item.owner.job_grade if (item.owner) else ""
    rec.calculate_score = compute_calc_score(score, item, db, owner_job_grade, q)

    db.flush()  # 确保上面的 rec 新增/修改已经反映到查询里

    # 进度已满 → 自动提交完成申请（等待工作项技术负责人审核）
    db.expire(item, ["monthly_scores"])   # 丢弃关系缓存，确保读到刚写入的分值
    auto_review = auto_create_complete_request(db, item, applicant_id=owner_id)

    db.commit()
    return {
        "code": 200,
        "message": "本月分值已保存" + ("，进度已满，已自动提交完成申请待技术负责人审核" if auto_review else ""),
        "data": {
            "work_item_id": work_item_id,
            "month": month,
            "score": score,
            "calculate_score": rec.calculate_score,
            "auto_complete_request_id": auto_review.id if auto_review else None, 
        }
    }

@router.put("/monthly-extra-scores")
def put_monthly_extra_scores(data: MonthlyExtraScoreIn, db: Session = Depends(get_db)):
    """领导按月为人员设置 技术提升/日常管理 附加分（存在则更新，否则创建）。"""
    # 权限：只有领导/管理员可设置
    updater = db.query(models.User).filter(models.User.id == data.updated_by_id).first()
    if not updater:
        raise HTTPException(status_code=404, detail="操作人不存在")
    if str(updater.role).upper() not in ["LEADER", "ADMIN", "DEPARTMENT"]:
        raise HTTPException(status_code=403, detail="只有领导、管理员或者科室主任可以设置月度附加分")

    target = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    month = (data.month or "").strip()
    if not month:
        raise HTTPException(status_code=400, detail="月份不能为空")

    rec = db.query(models.MonthlyExtraScore).filter(
        models.MonthlyExtraScore.user_id == data.user_id,
        models.MonthlyExtraScore.month == month
    ).first()
    if not rec:
        rec = models.MonthlyExtraScore(user_id=data.user_id, month=month)
        db.add(rec)

    rec.patent_score = round(float(data.patent_score or 0.0), 2)
    rec.knowledge_score = round(float(data.knowledge_score or 0.0), 2)
    rec.train_score = round(float(data.train_score or 0.0), 2)
    rec.deduct_score = round(float(data.deduct_score or 0.0), 2)
    rec.quality_event_score = round(float(data.quality_event_score or 0.0), 2)
    rec.carrier_inspection_score = round(float(data.carrier_inspection_score or 0.0), 2)
    rec.updated_by_id = data.updated_by_id

    db.commit()
    return {
        "code": 200,
        "message": "月度附加分已保存",
        "data": {
            "user_id": rec.user_id,
            "month": rec.month,
            "tech_improve": round((rec.patent_score or 0.0) + (rec.knowledge_score or 0.0) + (rec.train_score or 0.0), 2),
            "daily_manage": round((rec.deduct_score or 0.0) + (rec.quality_event_score or 0.0) + (rec.carrier_inspection_score or 0.0), 2),
        }
    }


@router.get("/monthly-extra-scores")
def get_monthly_extra_scores(user_id: str = None, month: str = None, db: Session = Depends(get_db)):
    """查询月度附加分：传 user_id+month 查单条；只传 month 查该月所有人员；都不传查全部。"""
    query = db.query(models.MonthlyExtraScore)
    if month:
        query = query.filter(models.MonthlyExtraScore.month == month)
    if user_id:
        query = query.filter(models.MonthlyExtraScore.user_id == user_id)
    rows = query.all()
    data = []
    for r in rows:
        u = r.user
        tech = round((r.patent_score or 0.0) + (r.knowledge_score or 0.0) + (r.train_score or 0.0), 3)
        daily = round((r.deduct_score or 0.0) + (r.quality_event_score or 0.0) + (r.carrier_inspection_score or 0.0), 3)
        data.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": u.username if u else r.user_id,
            "month": r.month,
            "patent_score": r.patent_score or 0.0,
            "knowledge_score": r.knowledge_score or 0.0,
            "train_score": r.train_score or 0.0,
            "tech_improve": tech,
            "deduct_score": r.deduct_score or 0.0,
            "quality_event_score": r.quality_event_score or 0.0,
            "carrier_inspection_score": r.carrier_inspection_score or 0.0,
            "daily_manage": daily,
            "updated_by_id": r.updated_by_id,
        })
    return {"code": 200, "data": data}

# ---------------------------------------------------------------- 工作完成情况
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
    user = db.query(models.User).filter(models.User.id == currentUserId).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if str(user.role).upper() not in ["LEADER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="只有领导和管理员可以查看完成情况")

    target_type = (target_type or "project").lower()
    if target_type not in ("project", "category"):
        raise HTTPException(status_code=400, detail="target_type 只能是 project / category")

    # ----  定位目标对象并取其下工作项 ----
    q = (db.query(models.WorkItem, models.WorkPackage)
         .join(models.WorkPackage, models.WorkPackage.id == models.WorkItem.work_package_id))

    if target_type == "project":
        if not target_id:
            raise HTTPException(status_code=400, detail="target_type=project 时必须传 target_id")
        project = db.query(models.Project).filter(models.Project.id == target_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        rows = q.filter(models.WorkPackage.project_id == target_id).all()
        target_name = project.name
    else:
        category_name = (category_name or "").strip()
        if not category_name:
            raise HTTPException(status_code=400, detail="target_type=category 时必须传 category_name")
        rows = q.filter(models.WorkPackage.category_name == category_name).all()
        target_name = category_name

    # ---- 按负责人聚合基础总分，并记录每个工作项所属负责人 ----
    owner_of = {}          # work_item_id -> owner_id
    total_by_owner = {}    # owner_id -> sum(item.score)
    for wi, _wp in rows:
        if not wi.owner_id:
            continue
        owner_of[wi.id] = wi.owner_id
        total_by_owner[wi.owner_id] = total_by_owner.get(wi.owner_id, 0.0) + (wi.score or 0.0)

    # ---- 已填分：这些工作项上的月度分值（可选月份）合计 → 归到所属负责人 ----
    filled_by_owner = {}
    if owner_of:
        fq = db.query(models.WorkItemMonthlyScore).filter(
            models.WorkItemMonthlyScore.work_item_id.in_(list(owner_of.keys())))
        if month:
            fq = fq.filter(models.WorkItemMonthlyScore.month == month)
        for m in fq.all():
            owner_id = owner_of.get(m.work_item_id)
            if owner_id:
                filled_by_owner[owner_id] = filled_by_owner.get(owner_id, 0.0) + (m.score or 0.0)

    # ----组装人员 ----
    owner_ids = sorted(total_by_owner.keys())
    user_map = {}
    if owner_ids:
        user_map = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(owner_ids)).all()}

    people = []
    for owner_id in owner_ids:
        u = user_map.get(owner_id)
        total_score = round(total_by_owner.get(owner_id, 0.0), 3)
        filled_score = round(filled_by_owner.get(owner_id, 0.0), 3)
        people.append({
            "user_id": owner_id,
            "username": u.username if u else owner_id,
            "role": u.role if u else "",
            "total_score": total_score,
            "filled_score": filled_score,
            "unfilled_score": round(total_score - filled_score, 3),
        })
    people.sort(key=lambda p: p["total_score"], reverse=True)

    return {
        "code": 200,
        "data": {
            "target_type": target_type,
            "target_name": target_name,
            "month": month or None,
            "people": people,
        }
    }

# ---------------------------------------------------------------- 项目/工作包汇总
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
    user = db.query(models.User).filter(models.User.id == currentUserId).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if str(user.role).upper() not in ["LEADER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="只有领导和管理员可以查看项目汇总")

    target_type = (target_type or "project").lower()
    if target_type not in ("project", "work_package"):
        raise HTTPException(status_code=400, detail="查看类型只能是项目/工作包")

    period = str(period or "all").lower()
    now = datetime.now()
    y = int(year or now.year)
    months = months_of_period(period, y, month, quarter)

    # 每个工作包：工作项个数 + 满分合计 
    total_rows = (db.query(
        models.WorkPackage.id.label("wp_id"),
        models.WorkPackage.project_id.label("project_id"),
        func.count(models.WorkItem.id).label("item_count"),
        func.coalesce(func.sum(models.WorkItem.score), 0.0).label("total_score"),
    ).outerjoin(models.WorkItem, models.WorkItem.work_package_id == models.WorkPackage.id)
        .group_by(models.WorkPackage.id, models.WorkPackage.project_id).all())

    # ---- 每个工作包：周期内已填分 ----
    filled_q = (db.query(
        models.WorkItem.work_package_id.label("wp_id"),
        func.coalesce(func.sum(models.WorkItemMonthlyScore.score), 0.0).label("filled_score"),
    ).join(models.WorkItem, models.WorkItem.id == models.WorkItemMonthlyScore.work_item_id)
        .group_by(models.WorkItem.work_package_id))
    if months is not None:
        filled_q = filled_q.filter(models.WorkItemMonthlyScore.month.in_(months))
    filled_pkg = {r.wp_id: float(r.filled_score or 0.0) for r in filled_q.all()}

    proj_map = {p.id: p for p in db.query(models.Project).order_by(models.Project.id).all()}
    items = []

    if target_type == "project":
        agg = {}                                    # pid -> 累计
        for p in proj_map.values():                 # 先铺满所有项目（空项目也在）
            agg[p.id] = {"wp": 0, "item": 0, "total": 0.0, "filled": 0.0}
        for r in total_rows:
            if r.project_id is None:
                continue
            s = agg[r.project_id]
            s["wp"] += 1
            s["item"] += int(r.item_count or 0) 
            s["total"] += float(r.total_score or 0.0)
            s["filled"] += filled_pkg.get(r.wp_id, 0.0)
        for pid, s in agg.items():
            p = proj_map[pid]
            items.append({
                "id": pid, "type": "project",
                "code": p.code, "name": p.name,
                "parent_name": "",
                "child_count": s["wp"],             # 所含工作包个数
                "child_label": "工作包",
                "work_item_count": s["item"],
                "total_score": round(s["total"], 3),
                "filled_score": round(s["filled"], 3),
                "unfilled_score": round(s["total"] - s["filled"], 3),
                "closed_status": bool(p.isclosed),
                "complete_status": bool(p.complete_status),
            })

    else:  # work_package
        wp_map = {wp.id: wp for wp in db.query(models.WorkPackage).all()}
        for r in total_rows:                        # 已含"没有工作项的工作包"
            wp = wp_map.get(r.wp_id)
            if not wp:
                continue
            total = float(r.total_score or 0.0)
            filled = filled_pkg.get(r.wp_id, 0.0)
            items.append({
                "id": wp.id, "type": "work_package",
                "code": wp.code, "name": wp.name or "-",
                "parent_code": proj_map[wp.project_id].code if wp.project_id in proj_map else "-",
                "category_name": wp.category_name or "-",
                "child_count": int(r.item_count or 0),   # 所含工作项个数
                "child_label": "工作项",
                "work_item_count": int(r.item_count or 0),
                "total_score": round(total, 3),
                "filled_score": round(filled, 3),
                "unfilled_score": round(total - filled, 3),
                "closed_status": bool(wp.isclosed),
                "complete_status": bool(wp.complete_status),
            })

    items.sort(key=lambda r: r["total_score"], reverse=True)

    return {"code": 200, "data": {
    "target_type": target_type,          # 前端知道当前是什么模式
    "period": period, "year": y, "month": month, "quarter": quarter, "months": months,
    "totals": {
        "count": len(items),                                        # 当前模式下的"共多少个"
        "work_package_count": sum(r["child_count"] for r in items) if target_type == "project" else len(items),
        "work_item_count": sum(r["work_item_count"] for r in items),
        "total_score": round(sum(r["total_score"] for r in items), 3),
        "filled_score": round(sum(r["filled_score"] for r in items), 3),
        "unfilled_score": round(sum(r["unfilled_score"] for r in items), 3),
    },
    "items": items,                       # ← 建议改名：叫 projects 但装工作包会很误导
}}

