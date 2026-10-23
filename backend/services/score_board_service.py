"""业务层：负责权限规则、状态流转、结果组装和事务；数据查询交给 repository。"""
from repositories import score_board_repository as repo

import re
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models
from schemas import MonthScoreIn, MonthlyExtraScoreIn
from utils import ensure_open, item_filled_score
import logging




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


def compute_deducted(item, today=None):
    """按当前日期累计扣分：前30天每满7天扣0.5分，超过30天的部分每满7天扣1分。

    today 是可选的日期参数，供边界测试使用；业务调用默认取北京时间当天。
    按日历日期计算，已完成工作项最多计算到完成日期。
    """
    if not item or not item.deadline:
        return 0.0

    # 截止日期当天不扣分；只比较日期，忽略截止时间中的时分秒。
    today = today if today is not None else datetime.now(timezone(timedelta(hours=8))).date()
    if getattr(item, "complete_status", False):
        completed_at = getattr(item, "completed_at", None)
        if completed_at is None:
            # 不能伪造历史完成日期，也不能继续以今天累计扣分。
            logging.warning("Completed work item %s has no completion date; live deduction skipped", getattr(item, "id", None))
            return 0.0
        completed_date = completed_at.astimezone(timezone(timedelta(hours=8))).date() if completed_at.tzinfo else completed_at.date()
        today = min(today, completed_date)
    overdue_days = (today - item.deadline.date()).days
    if overdue_days <= 0:
        return 0.0

    # 第一阶段：前30天，最多计算4个完整的7天。
    first_days = min(overdue_days, 30)
    first_deducted = (first_days // 7) * 0.5

    # 第二阶段：超过30天的部分，重新计算完整的7天。
    extra_days = max(overdue_days - 30, 0)
    extra_deducted = (extra_days // 7) * 1.0

    return first_deducted + extra_deducted

def monthly_quality_score(db, work_item_id, month):
    """质量分只读取指定月份，不向后续月份继承。"""
    rec = repo.get_month_score(db, work_item_id, month)
    return float(rec.quality_score or 0.0) if rec else 0.0

def apply_completion_quality(db, item, score, reviewed_at):
    """由完成审批事务调用：仅审批当月有质量分，不在这里提交事务。"""
    month = reviewed_at.strftime("%Y-%m")
    owner_id = item.owner_id or (item.work_package.owner_id if item.work_package else None)
    if not owner_id:
        raise HTTPException(400, "工作项未指定责任人，无法归属质量分")
    records = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id == item.id).with_for_update().all()
    target = next((rec for rec in records if rec.month == month), None)
    if target is None:
        target = models.WorkItemMonthlyScore(work_item_id=item.id, user_id=owner_id,
            month=month, score=0.0)
        db.add(target)
        records.append(target)
    grade = item.owner.job_grade if item.owner else ""
    for rec in records:
        rec.quality_score = round(float(score), 2) if rec.month == month else 0.0
        rec.quality_score_updated_at = reviewed_at
        if rec.month == month:
            rec.user_id = owner_id
        rec.calculate_score = compute_calc_score(rec.score or 0.0, item, db, grade, rec.quality_score)
    return month


def get_my_progress_deductions(db, user_id):
    """当前负责工作项截至今天的累计扣分，只用于个人积分展示。"""
    today = datetime.now(timezone(timedelta(hours=8))).date() # 获取该时区当前的日期和时间
    details = []
    for item in repo.list_owned_items(db, user_id):
        deducted = compute_deducted(item, today=today)
        if deducted <= 0:
            continue
        wp = item.work_package
        project = wp.project if wp else None
        details.append({
            "work_item_id": item.id,
            "work_item_name": item.name,
            "work_item_standard": item.standard,
            "work_item_deadline": item.deadline.date().isoformat() if item.deadline else None,
            "work_item_difficulty": item.difficulty,
            "work_item_importance": item.importance,
            "work_item_innovation": item.innovation,
            "work_package_id": wp.id if wp else None,
            "work_package_code": wp.code if wp else None,
            "work_package_category": wp.category_name if wp else None,
            "project_name": project.name if project else None,
            "project_code": project.code if project else None,
            "score": 0,
            "calculate_score": 0,
            "quality_score": None,
            "deducted_score": deducted,
        })
    return {"code": 200, "data": {"as_of": today.isoformat(), "details": details,
            "deducted_score": round(sum(row["deducted_score"] for row in details), 2)}}


def get_my_period_progress_deductions(db, user_id, period, year, month=None, quarter=None):
    """个人页按周期显示扣分；已入账取快照，未入账的当前月份取实时预览。"""
    from services.score_confirmation_service import now_local, official_board

    official = official_board(db, period, year, month, quarter)["data"]
    person = next((p for p in official["people"] if p["user_id"] == user_id), None)
    details = [d for d in (person or {}).get("details", []) if (d.get("deducted_score") or 0) > 0]
    total = float((person or {}).get("deducted_score") or 0)

    if period != "month":
        now = now_local()
        current_month = now.strftime("%Y-%m")
        cfg = db.get(models.ScoreConfirmationConfig, 1)
        selected_months = months_of_period(period, year, month, quarter)
        if selected_months is None:
            selected_months = [current_month]
        settled = {r.month for r in db.query(models.MonthlyScoreConfirmation).filter(
            models.MonthlyScoreConfirmation.user_id == user_id,
            models.MonthlyScoreConfirmation.status != "PENDING",
        ).all()}
        for mm in selected_months:
            if mm > current_month or mm in settled or (cfg and mm < cfg.start_month):
                continue
            preview = calculate_public_score_board(
                "month", int(mm[:4]), int(mm[5:]), db=db, as_of=now.date())["data"]
            preview_person = next((p for p in preview["people"] if p["user_id"] == user_id), None)
            if preview_person:
                details.extend(d for d in preview_person["details"] if (d.get("deducted_score") or 0) > 0)
                total += float(preview_person.get("deducted_score") or 0)

    return {"code": 200, "data": {"deducted_score": round(total, 2), "details": details}}


def _work_item_score_detail(item, month, score=0.0, calculate_score=0.0,
                            quality_score=0.0, deducted_score=0.0):
    """有无月度填分记录都使用相同的工作项明细结构。"""
    wp = item.work_package if item else None
    project = wp.project if wp else None
    return {
        "work_item_id": item.id if item else None,
        "work_item_name": item.name if item else "-",
        "work_item_standard": item.standard if item else "-",
        "work_item_difficulty": item.difficulty if item else "-",
        "work_item_importance": item.importance if item else "-",
        "work_item_innovation": item.innovation if item else "-",
        "work_item_deadline": item.deadline.date().isoformat() if item and item.deadline else None,
        "work_package_id": wp.id if wp else None,
        "work_package_code": wp.code if wp else None,
        "work_package_category": wp.category_name if wp else "-",
        "project_id": project.id if project else None,
        "project_name": project.name if project else "-",
        "project_code": project.code if project else "-",
        "month": month,
        "score": score,
        "quality_score": quality_score,
        "calculate_score": calculate_score,
        "deducted_score": deducted_score,
    }


def monthly_score_detail(rec, db, deducted_score=None):
    """把一条月度分值记录展开为积分面板需要的明细结构。"""
    return _work_item_score_detail(
        rec.work_item, rec.month, rec.score,
        rec.calculate_score if rec.calculate_score is not None else 0.0,
        monthly_quality_score(db, rec.work_item_id, rec.month),
        monthly_progress_deduction(rec.work_item, rec.month)
        if deducted_score is None else deducted_score,
    )


def _deduction_date(month, as_of=None, include_grace=False):
    """历史月份取月末，当前月份取今天；结算预览可显式指定核算日。"""
    year, number = map(int, month.split("-"))
    today = as_of or datetime.now(timezone(timedelta(hours=8))).date()
    if isinstance(today, datetime):
        today = today.date()
    first_day = date(year, number, 1)
    if first_day > today:
        return None
    if as_of is not None and include_grace:
        return today
    return min(today, date(year, number, monthrange(year, number)[1]))


def monthly_progress_deduction(item, month, as_of=None, include_grace=False):
    """本月新增扣分＝本月核算日累计扣分－上月末累计扣分。"""
    cutoff = _deduction_date(month, as_of, include_grace)
    if cutoff is None:
        return 0.0
    year, number = map(int, month.split("-"))
    previous_month_end = date(year, number, 1) - timedelta(days=1)
    return max(0.0, round(
        compute_deducted(item, today=cutoff)
        - compute_deducted(item, today=previous_month_end), 2))

def compute_calc_score(month_score, item, db, owner_job_grade, quality_score=None):
    """计算得分 = 本月基础得分 × (难度系数 + 创新度系数 + 重要度系数)＋质量分。
    难度/重要度系数按工作包负责人职级查；创新度系数按工作项创新度查。
    """
    if quality_score is None:
        quality_score = 0.0

    factor_map = {}
    for lv in repo.list_dimension_levels(db):
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
def get_score_board(user_id: str,
                    period: str = "all",
                    year: int = None,
                    month: int = None,
                    quarter: int = None,
                    db: Session = None):
    now = datetime.now()
    y = year or now.year #未指定年份默认当前年

    records = repo.list_user_month_scores(db, user_id)
    filtered = [r for r in records if month_in_selection(r.month, period, y, month, quarter)]
    total_score = sum(r.score or 0.0 for r in filtered)
    details = [monthly_score_detail(
        r, db, deducted_score=monthly_progress_deduction(r.work_item, r.month)
        if r.work_item and r.work_item.owner_id == user_id else 0.0)
        for r in filtered]
    deducted = sum(monthly_progress_deduction(r.work_item, r.month) for r in filtered
                   if r.work_item and r.work_item.owner_id == user_id)
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


def calculate_public_score_board(period: str = "all",
                           year: int = None,
                           month: int = None,
                           quarter: int = None,
                           db: Session = None, as_of=None):
    """所有人员积分面板：按 月/季/年 计算 技术提升、日常管理、技术成长分、计算总分、折算得分、等级。"""
    period = str(period or "all").lower()
    now = datetime.now()
    y = year or now.year

    # 周期内月份集合（month / quarter / year / all）
    months = months_of_period(period, y, month, quarter)

    users = repo.list_score_board_users(db)
    all_records = repo.list_all_month_scores(db)
    owned_items = {}
    for item in repo.list_all_owned_items(db):
        owned_items.setdefault(item.owner_id, []).append(item)

    # 周期内的月度附加分（技术提升 / 日常管理）
    extras = repo.list_period_extra_scores(db, months)

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
            months_used = sorted(set(month_score_map) | set(extra_map) |
                                 {datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m")})

        # 扣分归属当前工作项负责人，与本月是否填分无关。
        deductions_by_month = {}
        for mm in months_used:
            deductions_by_month[mm] = {
                item.id: (item, deducted)
                for item in owned_items.get(user.id, [])
                for deducted in [monthly_progress_deduction(
                    item, mm, as_of, include_grace=period == "month")]
                if deducted > 0
            }
        deduct_total = round(sum(
            deducted for penalties in deductions_by_month.values()
            for _, deducted in penalties.values()
        ), 2)

        details = []
        recorded_keys = set()
        for rec in user_records:
            deducted = deductions_by_month.get(rec.month, {}).get(rec.work_item_id, (None, 0.0))[1]
            details.append(monthly_score_detail(rec, db, deducted_score=deducted))
            recorded_keys.add((rec.month, rec.work_item_id))
        for mm, penalties in deductions_by_month.items():
            for item_id, (item, deducted) in penalties.items():
                if (mm, item_id) not in recorded_keys:
                    details.append(_work_item_score_detail(item, mm, deducted_score=deducted))

        # 各月「计算总分」= 该月计算分 + 该月技术提升合计 + 该月日常管理合计
        period_scores = []
        for mm in months_used:
            calc = calc_map.get(mm, 0.0)
            p, k, t, dd, qe, ci = extra_map.get(mm, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            month_deducted = sum(value for _, value in deductions_by_month[mm].values())
            period_scores.append(round(calc + p + k + t + dd + qe + ci - month_deducted, 2))

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
            "final_calculated": 0.0,           # 折算得分（季度/年度），下方计算
            "grade": "-",
            "period_scores": period_scores,
            # 动态切片求和：如果是年度，则把12个月的数据按季度(每3个月)累加；否则正常取单月值
            "period_1": round(sum(period_scores[0:3]), 2) if period == "year" else (period_scores[0] if len(period_scores) >= 1 else 0),
            "period_2": round(sum(period_scores[3:6]), 2) if period == "year" else (period_scores[1] if len(period_scores) >= 2 else 0),
            "period_3": round(sum(period_scores[6:9]), 2) if period == "year" else (period_scores[2] if len(period_scores) >= 3 else 0),
            "period_4": round(sum(period_scores[9:12]), 2) if period == "year" else 0,
            "deducted_score": deduct_total,
            "details": details,
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

def get_public_score_board(period="all", year=None, month=None, quarter=None, db=None):
    from services.score_confirmation_service import official_board
    return official_board(db, period, year, month, quarter)


def put_quality_score(work_item_id: int, data: MonthScoreIn, db: Session = None):
    raise HTTPException(403, "质量分只能由工作项技术负责人在完成审批通过时填写")


def save_month_score(work_item_id: int, body: MonthScoreIn, db: Session = None):
    """保存工作项本月分值：员工直接填写、直接生效，不经过审核。"""
    item = repo.get_item(db, work_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")
    ensure_open(item, item.work_package,
                item.work_package.project if item.work_package else None)  # 已关闭不能再填本月分值

    user = repo.get_user(db, body.user_id)
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
    rec = repo.get_month_score(db, work_item_id, month)

    old_score = rec.score if rec else 0.0

    acc_all = item_filled_score(db, work_item_id)

    acc_other = acc_all - (old_score or 0.0)
    # 与工作项列表口径一致：按分值精度收敛，避免浮点尾差影响校验提示
    remain = round((item.score or 0.0) - acc_other, 3)

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
        repo.add(db, rec)

    # 按当时规则固化计算得分（改规则后不影响已保存的历史月份）
    q = monthly_quality_score(db, work_item_id, month)
    owner_job_grade = item.owner.job_grade if (item.owner) else ""
    rec.calculate_score = compute_calc_score(score, item, db, owner_job_grade, q)

    db.flush()  # 确保上面的 rec 新增/修改已经反映到查询里

    # 保存分值不提交完成申请；完成申请仅由用户主动发起。

    db.commit()
    return {
        "code": 200,
        "message": "本月分值已保存",
        "data": {
            "work_item_id": work_item_id,
            "month": month,
            "score": score,
            "calculate_score": rec.calculate_score,
            "auto_complete_request_id": None,  # 保留响应字段兼容旧客户端，不再自动建单
        }
    }

def put_monthly_extra_scores(data: MonthlyExtraScoreIn, db: Session = None):
    """领导按月为人员设置 技术提升/日常管理 附加分（存在则更新，否则创建）。"""
    # 权限：只有领导/管理员可设置
    updater = repo.get_user(db, data.updated_by_id)
    if not updater:
        raise HTTPException(status_code=404, detail="操作人不存在")
    if str(updater.role).upper() not in ["LEADER", "ADMIN", "DEPARTMENT"]:
        raise HTTPException(status_code=403, detail="只有领导、管理员或者科室主任可以设置月度附加分")

    target = repo.get_user(db, data.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    month = (data.month or "").strip()
    if not month:
        raise HTTPException(status_code=400, detail="月份不能为空")

    rec = repo.get_extra_score(db, data.user_id, month)
    if not rec:
        rec = models.MonthlyExtraScore(user_id=data.user_id, month=month)
        repo.add(db, rec)

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


def get_monthly_extra_scores(user_id: str = None, month: str = None, db: Session = None):
    """查询月度附加分：传 user_id+month 查单条；只传 month 查该月所有人员；都不传查全部。"""
    rows = repo.list_extra_scores(db, user_id, month)
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


# ---------------------------------------------------------------- 项目/工作包汇总
def get_project_summary(currentUserId: str = None,
                        period: str = "all",
                        year: int = None,
                        month: int = None,
                        quarter: int = None,
                        target_type: str = "project",
                        db: Session = None):
    """按项目汇总分值（可按 月 / 季 / 年 / 全部 统计）。仅领导、管理员可查看。
    - total_score    = 项目下所有工作项满分之和（不随周期变化）
    - filled_score   = 这些工作项在周期内已填的月度基础分值之和
    - unfilled_score = total_score - filled_score
    """
    user = repo.get_user(db, currentUserId)
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
    total_rows = (repo.package_score_totals(db))

    # ---- 每个工作包：周期内已填分 ----
    filled_pkg = repo.package_filled_scores(db, months)

    proj_map = {p.id: p for p in repo.list_projects(db)}
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
        wp_map = {wp.id: wp for wp in repo.list_packages(db)}
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

