"""工时状态机与时间计算，不依赖浏览器提交的时间或用户 ID。"""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

import models


def utcnow():
    return datetime.utcnow()

# 时间转化为字符串
def stamp(value):
    return value.isoformat(timespec="milliseconds") + "Z" if value else None 

# 计算两个时间之间的秒数
def seconds_between(start, end):
    return max(0.0, (end - start).total_seconds())

# 计算一个工作时间段在指定期间内的有效秒数
def overlap_seconds(segment, now, start=None, end=None):
    """按时间段与统计周期的交集累计，跨天、跨月自动分配，保留历史时间段的统计口径。"""
    left = max(segment.started_at, start) if start else segment.started_at
    right = min(segment.ended_at or now, now)
    if end:
        right = min(right, end)
    return seconds_between(left, right)

# 把数据库记录整理成字典返回接口
def session_view(row, now=None, start=None, end=None):
    now = now or utcnow()
    return {
        "id": row.id, "work_item_id": row.original_item_id,
        "work_item_name": row.work_item_name, "work_package_id": row.work_package_id,
        "work_package_name": row.work_package_name, "project_id": row.project_id,
        "project_name": row.project_name, "user_id": row.user_id,
        "username": row.username, "department": row.department,
        "status": row.status, "version": row.version,
        "started_at": stamp(row.started_at), "ended_at": stamp(row.ended_at),
        "elapsed_seconds": round(sum(overlap_seconds(s, now) for s in row.segments), 3),
        "period_seconds": round(sum(overlap_seconds(s, now, start, end) for s in row.segments), 3),
        "server_now": stamp(now),
    }


def query_sessions(db):
    return db.query(models.WorkTimeSession).options(selectinload(models.WorkTimeSession.segments))


def current(db, user_id):
    row = query_sessions(db).filter(models.WorkTimeSession.active_user_id == user_id).first()
    return session_view(row) if row else None

# 检查工作项是否允许开始计时
def check_item(db, item_id, user_id):
    item = db.query(models.WorkItem).filter(models.WorkItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "工作项不存在")
    if item.owner_id != user_id:
        raise HTTPException(403, "只能为自己负责的工作项开始计时")
    pkg = item.work_package
    project = pkg.project if pkg else None
    if not pkg or not project or any(x.isclosed or x.complete_status for x in (item, pkg, project)):
        raise HTTPException(400, "工作项、工作包或项目已完成/关闭，不能开始计时")
    return item, pkg, project


def lock_user(db, user_id):
    # 所有计时写操作先锁同一用户行，保证多标签页请求按照顺序处理。
    db.query(models.User).filter(models.User.id == user_id).with_for_update().one()

# 开始计时
def start(db, user, item_id, request_key):
    try:
        lock_user(db, user.id)
        existing = query_sessions(db).filter(models.WorkTimeSession.user_id == user.id,
                                              models.WorkTimeSession.request_key == request_key).with_for_update().populate_existing().first()
        if existing:
            if existing.original_item_id != item_id:
                raise HTTPException(409, "请求号已用于其他工作项，请刷新后重试")
            result = session_view(existing)
            db.commit()
            return result
        active = query_sessions(db).filter(models.WorkTimeSession.active_user_id == user.id).with_for_update().first()
        if active:
            raise HTTPException(409, "已有未结束计时，请先在“我的工时”中处理")
        item, pkg, project = check_item(db, item_id, user.id)
        now = utcnow()
        row = models.WorkTimeSession(
            user_id=user.id, active_user_id=user.id, work_item_id=item.id,
            original_item_id=item.id, work_item_name=item.name,
            work_package_id=pkg.id, work_package_name=pkg.name or "未命名工作包",
            project_id=project.id, project_name=project.name or "未命名项目",
            username=user.username, department=user.department or "未分配科室",
            request_key=request_key, status="RUNNING", started_at=now,
        )
        db.add(row)
        db.flush()
        row.segments.append(models.WorkTimeSegment(started_at=now, open_session_id=row.id))
        db.flush()
        result = session_view(row, now)
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "计时状态已变化，请刷新当前计时后重试")
    except Exception:
        db.rollback()
        raise


def finish(db, user_id, session_id, version):
    """结束本次计时；只保留此前已记录工时。"""
    try:
        lock_user(db, user_id)
        row = query_sessions(db).filter(models.WorkTimeSession.id == session_id,
                                        models.WorkTimeSession.user_id == user_id).with_for_update().populate_existing().first()
        if not row:
            raise HTTPException(404, "计时记录不存在或无权操作")
        # MySQL 可重复读事务中，关联查询可能仍读取旧快照；时间段也用锁定读取获取最新状态。
        row.segments = db.query(models.WorkTimeSegment).filter_by(session_id=row.id).with_for_update().populate_existing().all()
        # 重复结束直接返回原结果，不重复累计工时。
        if row.status == "FINISHED":
            result = session_view(row)
            db.commit()
            return result
        if row.version != version:
            raise HTTPException(409, "计时状态已变化，请刷新后重试")
        now = utcnow()
        if row.status == "RUNNING":
            segment = next((s for s in row.segments if s.ended_at is None), None)
            if segment is None:
                raise HTTPException(409, "计时数据异常，请联系管理员")
            # 服务器时钟短暂回拨时也不产生负工时或反向时间段。
            segment.ended_at = max(now, segment.started_at)
            segment.open_session_id = None
            row.total_seconds += seconds_between(segment.started_at, segment.ended_at)
        row.status = "FINISHED"
        row.version += 1
        row.ended_at = max([now, row.started_at] + [s.ended_at for s in row.segments if s.ended_at])
        row.active_user_id = None
        db.flush()
        result = session_view(row, now)
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "计时状态冲突，请刷新后重试")
    except Exception:
        db.rollback()
        raise


def date_bounds(date_from, date_to):
    # 界面按北京时间选择日期，结束日期包含当天，查询内部使用右开区间。
    start = datetime.combine(date_from, datetime.min.time()) - timedelta(hours=8) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), datetime.min.time()) - timedelta(hours=8) if date_to else None
    if start and end and start >= end:
        raise HTTPException(400, "开始日期不能晚于结束日期")
    return start, end
