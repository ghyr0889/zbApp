"""Configurable charts. All grouping/metrics are server-owned expressions."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Integer, case, cast, func, literal
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(prefix="/api/v1/analytics", tags=["自定义看板"])
DIMENSIONS = {"employee": "员工", "department": "科室", "month": "月份", "quarter": "季度",
              "project": "项目", "work_package": "工作包", "work_item": "工作项", "category": "工作包类型",
              "status": "当前完成状态"}
METRICS = {"filled_score": ("填报工作量", "分"), "calculated_score": ("计算得分", "分"),
           "item_count": ("填报工作项数（去重）", "项"), "completed_count": ("期间完成工作项数", "项")}
STATUS_LABELS = {"not_started": "未填报", "in_progress": "进行中", "pending": "待完成审核", "completed": "已完成"}


class ChartQuery(BaseModel):
    user_id: str
    period: Literal["month", "quarter", "year"] = "month"
    year: int = Field(ge=2000, le=2100)
    month: int = Field(default=1, ge=1, le=12)
    quarter: int = Field(default=1, ge=1, le=4)
    departments: list[str] = Field(default_factory=list, max_length=200)
    employee_ids: list[str] = Field(default_factory=list, max_length=500)
    project_ids: list[int] = Field(default_factory=list, max_length=500)
    work_package_ids: list[int] = Field(default_factory=list, max_length=500)
    work_item_ids: list[int] = Field(default_factory=list, max_length=500)
    status: Literal["", "not_started", "in_progress", "pending", "completed"] = ""
    dimension: str = "employee"
    metric: str = "filled_score"
    series_dimension: str = ""
    chart_type: Literal["bar", "horizontal_bar", "line", "stacked_bar"] = "horizontal_bar"


def require_viewer(db, user_id):
    # Matches the application's existing user-id based permission mechanism.
    viewer = db.query(models.User).filter(models.User.id == user_id).first()
    if not viewer or viewer.is_deleted or str(viewer.role).upper() not in ("LEADER", "ADMIN"):
        raise HTTPException(403, "数据看板仅对领导 / 管理员开放")


def period_bounds(body):
    first = body.month if body.period == "month" else (body.quarter - 1) * 3 + 1 if body.period == "quarter" else 1
    length = {"month": 1, "quarter": 3, "year": 12}[body.period]
    start = datetime(body.year, first, 1)
    next_month = first + length
    end = datetime(body.year + (next_month - 1) // 12, (next_month - 1) % 12 + 1, 1)
    months = [f"{body.year:04d}-{m:02d}" for m in range(first, first + length)]
    return start, end, months


@router.get("/options")
def options(user_id: str, db: Session = Depends(get_db)):
    require_viewer(db, user_id)
    users = db.query(models.User).filter(models.User.is_deleted == False).order_by(models.User.username).all()
    return {"code": 200, "data": {
        "dimensions": [{"value": k, "label": v} for k, v in DIMENSIONS.items()],
        "metrics": [{"value": k, "label": v[0]} for k, v in METRICS.items()],
        "departments": sorted({u.department or "未分配科室" for u in users}),
        "employees": [{"value": u.id, "label": f"{u.username}（{u.id}）", "department": u.department or "未分配科室"} for u in users],
        "projects": [{"value": p.id, "label": f"{p.name or '-'}（{p.code or p.id}）"} for p in db.query(models.Project).all()],
        "packages": [{"value": p.id, "label": f"{p.name or '-'}（{p.code or p.id}）", "project_id": p.project_id} for p in db.query(models.WorkPackage).all()],
        "items": [{"value": i.id, "label": f"{i.name}（{i.id}）", "package_id": i.work_package_id} for i in db.query(models.WorkItem).all()],
        "statuses": [{"value": k, "label": v} for k, v in STATUS_LABELS.items()],
    }}


@router.post("/chart")
def chart(body: ChartQuery, db: Session = Depends(get_db)):
    require_viewer(db, body.user_id)
    if body.dimension not in DIMENSIONS or body.metric not in METRICS or (body.series_dimension and body.series_dimension not in DIMENSIONS):
        raise HTTPException(422, "不支持的维度或指标")
    if body.dimension == body.series_dimension:
        raise HTTPException(422, "横轴与分组不能相同")
    if body.chart_type == "line" and body.dimension not in ("month", "quarter"):
        raise HTTPException(422, "折线图请选择月份或季度横轴")
    if body.chart_type == "stacked_bar" and not body.series_dimension:
        raise HTTPException(422, "堆叠图需要选择分组")

    U, I, W, P, M = models.User, models.WorkItem, models.WorkPackage, models.Project, models.WorkItemMonthlyScore
    start, end, months = period_bounds(body)
    completed = body.metric == "completed_count"
    pending = db.query(models.WorkItemCompletionReview.id).filter(
        models.WorkItemCompletionReview.work_item_id == I.id,
        models.WorkItemCompletionReview.status == "PENDING").exists()
    has_score = db.query(M.id).filter(M.work_item_id == I.id, M.score > 0).correlate(I).exists()
    state = case((I.complete_status == True, "completed"), (pending, "pending"),
                 (has_score, "in_progress"), else_="not_started")
    department = func.coalesce(func.nullif(U.department, ""), "未分配科室")
    month_expr = func.extract("month", I.completed_at) if completed else cast(func.substr(M.month, 6, 2), Integer)
    quarter_expr = case((month_expr <= 3, 1), (month_expr <= 6, 2), (month_expr <= 9, 3), else_=4)
    dimensions = {
        "employee": (U.id, U.username), "department": (department, department),
        "month": (month_expr, month_expr), "quarter": (quarter_expr, quarter_expr),
        "project": (P.id, P.name), "work_package": (W.id, W.name),
        "work_item": (I.id, I.name), "category": (W.category_name, W.category_name), "status": (state, state),
    }
    xkey, xlabel = dimensions[body.dimension]
    skey, slabel = dimensions[body.series_dimension] if body.series_dimension else (literal("total"), literal("合计"))
    metric = func.count(func.distinct(I.id)) if body.metric in ("item_count", "completed_count") else func.coalesce(func.sum(M.score if body.metric == "filled_score" else M.calculate_score), 0)
    query = db.query(xkey, xlabel, skey, slabel, metric)
    if completed:
        query = query.select_from(I).join(U, U.id == I.owner_id).filter(I.complete_status == True, I.completed_at >= start, I.completed_at < end)
    else:
        query = query.select_from(M).join(I, I.id == M.work_item_id).join(U, U.id == M.user_id).filter(M.month.in_(months))
    query = query.join(W, W.id == I.work_package_id).join(P, P.id == W.project_id)
    for values, column in ((body.departments, department), (body.employee_ids, U.id), (body.project_ids, P.id),
                           (body.work_package_ids, W.id), (body.work_item_ids, I.id)):
        if values:
            query = query.filter(column.in_(values))
    if body.status:
        query = query.filter(state == body.status)
    rows = query.group_by(xkey, xlabel, skey, slabel).all()
    # SQL counts distinct work items at the final grouping level, not summed monthly counts.
    axes, series_names, values = {}, {}, {}

    def label(dimension, key, name):
        if dimension == "month":
            return f"{body.year}-{int(key):02d}"
        if dimension == "quarter":
            return f"{body.year}年第{int(key)}季度"
        if dimension == "status":
            return STATUS_LABELS.get(str(key), str(key))
        if dimension in ("employee", "project", "work_package", "work_item"):
            return f"{name or '未命名'}（{key}）"
        return str(name or "未分类")

    if body.dimension in ("month", "quarter"):
        for m in months:
            key = int(m[5:7]) if body.dimension == "month" else (int(m[5:7]) - 1) // 3 + 1
            axes[str(key)] = label(body.dimension, key, key)
    # Include people with no records: a zero indicates no recorded amount, not a workload verdict.
    if body.dimension in ("employee", "department") and not body.series_dimension and not body.status and not any((body.project_ids, body.work_package_ids, body.work_item_ids)):
        people = db.query(U).filter(U.is_deleted == False)
        if body.employee_ids:
            people = people.filter(U.id.in_(body.employee_ids))
        if body.departments:
            people = people.filter(department.in_(body.departments))
        for person in people.all():
            key = person.id if body.dimension == "employee" else person.department or "未分配科室"
            axes[str(key)] = label(body.dimension, key, person.username if body.dimension == "employee" else key)
    for x, name, s, sname, value in rows:
        axes[str(x)] = label(body.dimension, x, name)
        series_names[str(s)] = label(body.series_dimension, s, sname)
        values[(str(x), str(s))] = round(float(value or 0), 3)
    if not series_names:
        series_names["total"] = METRICS[body.metric][0]
    if len(axes) > 500 or len(series_names) > 30:
        raise HTTPException(422, "图表最多展示500个横轴分类、30个分组，请缩小筛选范围")
    axis_ids = sorted(axes, key=lambda k: int(k)) if body.dimension in ("month", "quarter") else sorted(axes, key=lambda k: (-sum(v for (x, _), v in values.items() if x == k), axes[k]))
    series = [{"name": series_names[s], "data": [values.get((x, s), 0) for x in axis_ids]} for s in sorted(series_names, key=lambda k: series_names[k])]
    note = "按完成时间统计，人员归属采用当前工作项负责人。" if completed else "按填报月份统计，人员归属采用月度记录中的人员；填报工作项数在每个分类内去重，跨分类不应直接相加。"
    note += " 科室和完成状态均采用当前信息；0表示没有匹配数值，不代表工作量不足。计算得分包含系数和质量分。"
    return {"code": 200, "data": {"categories": [axes[x] for x in axis_ids], "series": series,
            "unit": METRICS[body.metric][1], "metric_label": METRICS[body.metric][0],
            "dimension_label": DIMENSIONS[body.dimension], "note": note,
            "period_label": f"{months[0]} 至 {months[-1]}", "has_records": bool(rows)}}
