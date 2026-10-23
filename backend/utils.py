# xiangmu/backend/utils.py
"""共享工具函数：工作包/工作项的分值、节点聚合与日期解析。"""
import re
from datetime import datetime

# 各角色在「审批查阅」里需要处理的拆分申请状态
PENDING_STATUS_BY_ROLE = {
    "DEPARTMENT": "PENDING",    # 科室主任：待科室审核
    "LEADER": "SUBMITTED",      # 领导：待领导审核
    "ADMIN": "SUBMITTED",       # 管理员：等同领导
    "EMPLOYEE": "REJECTED",     # 员工：自己被驳回、待修改重提的申请
}


def pending_status_for(role):
    """返回该角色需要处理的拆分申请状态；未知角色返回空串（视为没有待办）。

    唯一的状态映射表：审批查阅列表、待办计数接口都用它，
    避免多处各写一套导致前后端口径分叉。
    """
    return PENDING_STATUS_BY_ROLE.get(str(role or "").upper(), "")


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
    满分 0（无工作量）视为已满——即“天然可提交”，与 effective_complete 口径一致。
    """
    total = item.score or 0.0
    if not total:
        return True
    filled = sum((ms.score or 0.0) for ms in (item.monthly_scores or []))
    return filled >= total - 1e-6

def effective_complete(item):
    """可提交申请 = 手动确认完成 或 进度已满。"""
    return bool(item.complete_status) or has_full_progress(item)

def is_completed(item):
    """是否已完成：以 complete_status（审核通过后置位）为准。"""
    return bool(item.complete_status)

def item_progress(item):
    """工作项进度百分比（0~100）；满分 0 视为 100%。
    要求调用前已预加载 item.monthly_scores，避免 N+1。
    """
    total = item.score or 0.0
    filled = sum((ms.score or 0.0) for ms in (item.monthly_scores or []))
    if not total:
        return 100.0
    return calc_progress(filled, total)

def package_effective_complete(pkg):
    """工作包有效完成 = 手动确认完成 或 其下所有工作项都已审核通过。
    空工作包（无工作项）不自动完成，需手动确认。
    要求调用前已预加载 pkg.work_items -> monthly_scores，避免 N+1 查询。
    """
    if bool(pkg.complete_status):
        return True
    items = list(pkg.work_items or [])
    if not items:
        return False
    return all(is_completed(it) for it in items)

def project_effective_complete(project):
    """A project is complete only when manually confirmed or every package is complete.
    An empty project or an unfinished empty package does not complete automatically.
    Package relationships must be loaded by the caller.
    """
    if bool(project.complete_status):
        return True
    wps = list(project.work_packages or [])
    if not wps:
        return False
    return all(package_effective_complete(wp) for wp in wps)
