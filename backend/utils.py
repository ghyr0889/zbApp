# xiangmu/backend/utils.py
"""共享工具函数：工作包/工作项的分值、节点聚合与日期解析。"""
import re
from datetime import datetime

import models


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