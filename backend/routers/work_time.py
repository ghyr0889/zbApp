"""工时接口：身份来自登录令牌，开始、结束均使用服务器时间。"""
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from services import work_time_service as service

router = APIRouter(prefix="/api/v1/work-time", tags=["工时记录"])

class StartInput(BaseModel):
    work_item_id: int = Field(gt=0)
    request_key: str = Field(min_length=16, max_length=64) #请求号，每次请求时唯一


class ActionInput(BaseModel):
    version: int = Field(ge=1)


@router.post("/start") 
# 开始新计时
def start(body: StartInput, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"code": 200, "data": service.start(db, user, body.work_item_id, body.request_key)}


@router.get("/current")
# 获取未结束的计时
def current(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"code": 200, "data": service.current(db, user.id)}


@router.get("/options")
# 获取工作项下拉框选项
def options(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """选项包含本人负责的工作项和本人的历史工时，转办后仍可筛选历史。"""
    items = db.query(models.WorkItem, models.WorkPackage, models.Project).join(
        models.WorkPackage, models.WorkItem.work_package_id == models.WorkPackage.id).join(
        models.Project, models.WorkPackage.project_id == models.Project.id).filter(models.WorkItem.owner_id == user.id).all()
    mapped = {}
    for item, pkg, project in items:
        mapped[item.id] = {"id": item.id, "name": item.name, "work_package_id": pkg.id,
                           "work_package_name": pkg.name, "work_package_code": pkg.code,
                           "project_id": project.id, "project_name": project.name,
                           "is_owned": True,
                           "can_start": not any(x.isclosed or x.complete_status for x in (item, pkg, project))}
    # 使用业务编号 code，而不是数据库主键；历史工作包已删除时编号留空。
    history = db.query(models.WorkTimeSession, models.WorkPackage.code).outerjoin(
        models.WorkPackage, models.WorkTimeSession.work_package_id == models.WorkPackage.id
    ).filter(models.WorkTimeSession.user_id == user.id).order_by(models.WorkTimeSession.id.desc()).all()
    for row, package_code in history:
        mapped.setdefault(row.original_item_id, {"id": row.original_item_id, "name": row.work_item_name,
            "work_package_id": row.work_package_id, "work_package_name": row.work_package_name,
            "work_package_code": package_code,
            "project_id": row.project_id, "project_name": row.project_name, "can_start": False, "is_owned": False})
    return {"code": 200, "data": list(mapped.values())}


def filtered_query(db, user_id=None, project_id=None, work_package_id=None, work_item_id=None):
# 统一添加人员、项目、工作包和工作项筛选条件
    S = models.WorkTimeSession
    query = service.query_sessions(db)
    for field, value in ((S.user_id, user_id), (S.project_id, project_id),
                         (S.work_package_id, work_package_id), (S.original_item_id, work_item_id)):
        if value is not None:
            query = query.filter(field == value)
    return query


def period_query(query, start, end):
# 筛选实际工作时间段与所选日期范围相交的记录
    S, G = models.WorkTimeSession, models.WorkTimeSegment
    # 根据实际工作时间段是否与周期相交筛选，不使用会话开始月份。
    criteria = [G.session_id == S.id]
    if start:
        criteria.append(or_(G.ended_at.is_(None), G.ended_at > start))
    if end:
        criteria.append(G.started_at < end)
    return query.filter(query.session.query(G.id).filter(*criteria).exists())


@router.get("/mine")
# 本人工时记录
def mine(date_from: Optional[date] = None, date_to: Optional[date] = None,
         project_id: Optional[int] = None, work_package_id: Optional[int] = None, work_item_id: Optional[int] = None,
         page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
         db: Session = Depends(get_db), user=Depends(get_current_user)):
    start, end = service.date_bounds(date_from, date_to)
    query = period_query(filtered_query(db, user.id, project_id, work_package_id, work_item_id), start, end)
    total = query.count()
    rows = query.order_by(models.WorkTimeSession.started_at.desc(), models.WorkTimeSession.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    now = service.utcnow()
    # 汇总全部匹配记录，而不是只汇总当前页。时间段直接查询，避免重复加载会话信息。
    ids = query.with_entities(models.WorkTimeSession.id).subquery()
    segments = db.query(models.WorkTimeSegment).join(ids, models.WorkTimeSegment.session_id == ids.c.id).all()
    total_seconds = sum(service.overlap_seconds(s, now, start, end) for s in segments)
    return {"code": 200, "data": {"total": total, "total_seconds": round(total_seconds, 3),
            "items": [service.session_view(row, now, start, end) for row in rows]}}


@router.get("/report")
# 查询汇总数据
def report(date_from: date, date_to: date,
           dimension: Literal["employee", "department", "project", "work_package", "work_item", "day", "month"] = "employee",
           user_id: Optional[str] = None, project_id: Optional[int] = None,
           work_package_id: Optional[int] = None, work_item_id: Optional[int] = None,
           db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role not in ("ADMIN", "LEADER"):
        raise HTTPException(403, "仅领导和管理员可以查看工时汇总")
    if (date_to - date_from).days > 366:
        raise HTTPException(400, "单次汇总请限制在367天以内")
    start, end = service.date_bounds(date_from, date_to)
    rows = period_query(filtered_query(db, user_id, project_id, work_package_id, work_item_id), start, end).all()
    now, totals, labels = service.utcnow(), {}, {}
    for row in rows:
        keys = {"employee": (row.user_id, f"{row.username}（{row.user_id}）"), "department": (row.department, row.department),
                "project": (row.project_id, f"{row.project_name}（{row.project_id}）"),
                "work_package": (row.work_package_id, f"{row.work_package_name}（{row.work_package_id}）"),
                "work_item": (row.original_item_id, f"{row.work_item_name}（{row.original_item_id}）")}
        for segment in row.segments:
            if dimension in ("day", "month"):
                left, right = max(start, segment.started_at), min(end, segment.ended_at or now, now)
                while left < right:
                    local = left + timedelta(hours=8)
                    day_end = service.date_bounds(None, local.date())[1]
                    stop = min(day_end, right)
                    key = local.strftime("%Y-%m-%d" if dimension == "day" else "%Y-%m")
                    totals[key] = totals.get(key, 0) + service.seconds_between(left, stop)
                    labels[key] = key
                    left = stop
            else:
                key, label = keys[dimension]
                totals[key] = totals.get(key, 0) + service.overlap_seconds(segment, now, start, end)
                labels[key] = label
    if dimension in ("day", "month"):
        day = date_from
        while day <= date_to:
            key = day.strftime("%Y-%m-%d" if dimension == "day" else "%Y-%m")
            totals.setdefault(key, 0)
            labels[key] = key
            day += timedelta(days=1)
    ordered = sorted(totals) if dimension in ("day", "month") else sorted(totals, key=lambda k: (-totals[k], str(k)))
    return {"code": 200, "data": {"items": [{"key": k, "name": labels[k], "seconds": round(totals[k], 3), "hours": round(totals[k] / 3600, 4)} for k in ordered],
            "total_seconds": round(sum(totals.values()), 3), "server_now": service.stamp(now),
            "note": "按北京时间分配工时，按实际记录时间段累计；包含正在计时部分。人员、科室和工作名称按开始计时时的快照归属。"}}


@router.get("/work-items/{item_id}/summary")
# 一个工作项的累计工时
def item_summary(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.query(models.WorkItem).filter_by(id=item_id).first()
    if not item or (user.role not in ("ADMIN", "LEADER") and item.owner_id != user.id and item.tech_owner_id != user.id):
        raise HTTPException(404, "工作项不存在或无权查看")
    now = service.utcnow()
    rows = filtered_query(db, work_item_id=item_id).all()
    return {"code": 200, "data": {"total_seconds": sum(service.session_view(r, now)["elapsed_seconds"] for r in rows),
            "my_seconds": sum(service.session_view(r, now)["elapsed_seconds"] for r in rows if r.user_id == user.id)}}


@router.post("/{session_id}/finish")
# 结束计时
def finish(session_id: int, body: ActionInput,
           db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"code": 200, "data": service.finish(db, user.id, session_id, body.version)}
