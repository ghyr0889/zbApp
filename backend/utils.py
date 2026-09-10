# xiangmu/backend/utils.py
"""共享工具函数：工作包/工作项的分值、节点聚合与日期解析。"""
import re
from datetime import datetime



def ensure_open(*objs):
    """校验给定的 项目/工作包/工作项 未被“关闭”；任一已关闭即抛 403。

    供各写操作入口调用：对象关闭后不允许再编辑；
    项目关闭会连带锁住其下工作包/工作项（调用时把整条链的对象都传入即可）。
    """
    from fastapi import HTTPException
    for o in objs:
        if o is not None and getattr(o, "isclosed", False):
            raise HTTPException(status_code=403, detail="该对象已关闭，不能进行此操作")


def parse_deadline(date_str):
    """把 '2026.7.29' / '2026-08-15' / '2026/8/1' 等字符串解析为 datetime；解析失败返回 None。"""
    if not date_str:
        return None
    text = str(date_str).strip()
    match = re.search(r"(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})", text)
    if not match:
        return None
    y, m, d = (int(x) for x in match.groups())
    try:
        return datetime(y, m, d, 23, 59, 59)
    except ValueError:
        return None


def deadline_str(value):
    """把 deadline 统一转成 'YYYY-MM-DD' 字符串。"""
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)


def work_package_summary(pkg):
    """聚合工作包在“工作包层面”的分值与截止节点：
    - 分值   = 其下所有工作项分值之和
    - 截止   = 其下最早的工作项截止节点
    因为数据库中 WorkPackage 不再存 score/deadline（已下沉到 WorkItem）。
    """
    items = list(pkg.work_items or [])
    total_score = round(sum((it.score or 0.0) for it in items), 2)
    deadlines = [it.deadline for it in items if it.deadline]
    earliest = min(deadlines) if deadlines else None
    return total_score, deadline_str(earliest)


def calc_progress(month_score, full_score):
    """完成度：month_score(累计完成量) / full_score(满分)，封顶 100%，返回百分比。"""
    if not full_score:
        return 0
    return round(min(month_score / full_score, 1.0) * 100, 1)

def item_filled_score(db, item_id):
    """该工作项累计已填月度分值。"""
    from sqlalchemy import func
    import models
    return db.query(func.coalesce(func.sum(models.WorkItemMonthlyScore.score), 0.0)) \
             .filter(models.WorkItemMonthlyScore.work_item_id == item_id).scalar() or 0.0

def has_full_progress(item):
    """进度是否已满：累计月度分值 >= 工作项分值。
    满分 0（无工作量）视为已满——即“天然完成”，与 item_is_completed 口径一致。
    """
    total = item.score or 0.0
    if not total:
        return True
    filled = sum((ms.score or 0.0) for ms in (item.monthly_scores or []))
    return filled >= total - 1e-6

def effective_complete(item):
    """完成状态 = 手动确认完成 或 进度已满。"""
    return bool(item.complete_status) or has_full_progress(item)

def package_effective_complete(pkg):
    """工作包有效完成 = 手动确认完成 或 其下所有工作项都有效完成。
    空工作包（无工作项）不自动完成，需手动确认。
    要求调用前已预加载 pkg.work_items -> monthly_scores，避免 N+1 查询。
    """
    if bool(pkg.complete_status):
        return True
    items = list(pkg.work_items or [])
    if not items:
        return False
    return all(effective_complete(it) for it in items)

def project_effective_complete(project):
    """项目有效完成 = 手动确认完成 或 其下所有工作包都有效完成。

    空项目不自动完成；空工作包不阻塞项目（自身不自动完成，但不影响父级）。
    要求调用前已预加载 project.work_packages -> work_items -> monthly_scores。
    """
    if bool(project.complete_status):
        return True
    wps = list(project.work_packages or [])
    if not wps:
        return False
    return all(
        package_effective_complete(wp) or not list(wp.work_items or [])
        for wp in wps
    )

def item_is_completed(db, item):
    """完成判定（库版）：手动确认完成 或 累计分值已达满分（满分 0 视为已完成）。"""
    if bool(item.complete_status): return True
    total = item.score or 0.0
    if not total:                      # 满分为 0：无工作量，视为已完成
        return True
    return item_filled_score(db, item.id) >= total - 1e-6   # 浮点容差

def sync_item_completed_at(db, item, at=None):
    """按判定自动维护 completed_at：达成则记首次时间，未达成则清空。"""
    from datetime import datetime
    if item_is_completed(db, item):
        if not item.completed_at:
            item.completed_at = at or datetime.now()
    else:
        item.completed_at = None
    return item.completed_at


def sync_items_completed_at(db, items, at=None):
    """批量版 sync_item_completed_at：一次 GROUP BY 算出全部工作项的累计分值，
    避免逐个工作项查询（拆分审批、转办等批量场景）。

    判定口径与 item_is_completed 一致：手动确认完成、满分 0、或 累计月度分值 >= 工作项分值。
    注意：调用前请先 db.flush()，确保刚修改的 score 已进入数据库。
    """
    from sqlalchemy import func
    import models

    items = [it for it in (items or []) if it is not None]
    if not items:
        return

    ids = [it.id for it in items if it.id]
    sums = {}
    if ids:
        sums = dict(db.query(
            models.WorkItemMonthlyScore.work_item_id,
            func.coalesce(func.sum(models.WorkItemMonthlyScore.score), 0.0)
        ).filter(models.WorkItemMonthlyScore.work_item_id.in_(ids))
            .group_by(models.WorkItemMonthlyScore.work_item_id).all())

    now = at or datetime.now()
    for it in items:
        total = it.score or 0.0
        # 手动确认 / 满分 0（无工作量）/ 累计分值达到满分 → 视为完成
        done = bool(it.complete_status) or (not total) or (
            sums.get(it.id, 0.0) >= total - 1e-6
        )
        if done:
            if not it.completed_at:
                it.completed_at = now
        else:
            it.completed_at = None