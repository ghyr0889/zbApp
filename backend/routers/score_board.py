
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import MonthScoreIn, MonthlyExtraScoreIn

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

def compute_deducted(item):
    """扣分计算函数，超时扣1分"""
    if item.completed_at and item.deadline and item.completed_at > item.deadline:
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
        "work_item_difficulty": item.difficulty if item else "-",
        "work_item_importance": item.importance if item else "-",
        "work_item_innovation": item.innovation if item else "-",
        "work_package_id": wp.id if wp else None,
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
        factor_map.setdefault((lv.variable, lv.job_grade or "", lv.level), lv.factor or 1.0)

    owner_grade = owner_job_grade or ""
    difficulty_f = round(factor_map.get(("difficulty", owner_grade, item.difficulty), 0), 3)
    importance_f = round(factor_map.get(("importance", owner_grade, item.importance), 0), 3)
    innovation_f = round(factor_map.get(("innovation", "", item.innovation), 0), 3)

    return round((month_score or 0.0) * (difficulty_f + innovation_f + importance_f) + (quality_score or 0.0), 3)


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

    # 周期内月份集合
    if period == "month":
        m = int(month or now.month)
        months = [f"{y:04d}-{m:02d}"]
    elif period == "quarter":
        q = int(quarter or ((now.month - 1) // 3 + 1))
        base = (q - 1) * 3 + 1
        months = [f"{y:04d}-{mm:02d}" for mm in (base, base + 1, base + 2)]
    elif period == "year":
        months = [f"{y:04d}-{mm:02d}" for mm in range(1, 13)]
    else:  # all
        months = None

    users = db.query(models.User).all()
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
        total_calculated = round(calc_total + tech_total + daily_total, 2)          # 计算总分

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
            "total_score": total_calculated,   # 得分（季度/年度=各月计算总分之和）
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
    month = data.month or datetime.now().strftime("%Y-%m")
    rec = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == work_item_id,
        models.WorkItemMonthlyScore.month == month).first()

    wp = item.work_package
    owner_job_grade = wp.owner.job_grade if (wp and wp.owner) else ""

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
    if item.complete_status:
        raise HTTPException(status_code=400, detail="工作项已完成，不能填写分值")

    user = db.query(models.User).filter(models.User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 权限：该工作包负责人本人
    role = str(user.role).upper()
    work_package = item.work_package
    if role not in["LEADER","ADMIN"] and (not work_package or work_package.owner_id != user.id):
        raise HTTPException(status_code=403, detail="只有工作包负责人本人、领导和管理员可以填写本月分值")

    month = (body.month or "").strip()
    if not month:
        raise HTTPException(status_code=400, detail="月份不能为空")

    score = round(float(body.score or 0.0), 3)
    if score > (item.score or 0.0):
        raise HTTPException(status_code=400, detail=f"本月分值不能超过该工作项分值 {item.score or 0.0}")
    rec = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == work_item_id,
        models.WorkItemMonthlyScore.month == month
    ).first()
    # 积分归属：记给工作包负责人（领导/管理员代填也不改变归属）；无负责人时兜底记给填写人
    owner_id = work_package.owner_id if (work_package and work_package.owner_id) else user.id
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
    owner_job_grade = work_package.owner.job_grade if (work_package and work_package.owner) else ""
    rec.calculate_score = compute_calc_score(score, item, db, owner_job_grade, q)

    # 记录完成时间：本次保存后累计分值首次达到工作项分值 → 锁定完成时间
    # 会话 autoflush=False，必须先手动 flush，本次 rec 才会计入下面的累计查询
    db.flush()
    acc = sum(r.score or 0.0 for r in db.query(models.WorkItemMonthlyScore)
              .filter(models.WorkItemMonthlyScore.work_item_id == work_item_id).all())
    if (item.score or 0) > 0 and round(acc, 2) >= round(item.score or 0.0, 2) and item.completed_at is None:
        item.completed_at = datetime.now()

    # ---- 完成状态联动：工作项 → 工作包 → 项目（全部子项完成才置为 COMPLETED）----
    if item.completed_at and not item.complete_status:
        item.complete_status = True
    if work_package and all(it.complete_status for it in (work_package.work_items or [])):
        if not work_package.complete_status:
            work_package.complete_status = True
        project = work_package.project
        if project and all(w.complete_status for w in (project.work_packages or [])):
            if not project.complete_status:
                project.complete_status = True
    db.commit()
    return {
        "code": 200,
        "message": "本月分值已保存",
        "data": {"work_item_id": work_item_id, "month": month, "score": score, "calculate_score": rec.calculate_score}
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
        tech = round((r.patent_score or 0.0) + (r.knowledge_score or 0.0) + (r.train_score or 0.0), 2)
        daily = round((r.deduct_score or 0.0) + (r.quality_event_score or 0.0) + (r.carrier_inspection_score or 0.0), 2)
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
