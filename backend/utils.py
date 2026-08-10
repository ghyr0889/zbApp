# xiangmu/backend/utils.py
"""共享工具函数：工作包/工作项的分值、节点聚合与日期解析。"""
import re
from datetime import datetime

import models


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
        return datetime(y, m, d)
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


def ensure_default_work_item(db, pkg, score=None, deadline_str_val=""):
    """确保工作包至少有一个承载“分值/节点”的工作项。
    - 工作包尚无工作项：自动创建一个“默认工作项”（名称取工作包名），写入 score/deadline
    - 工作包已有工作项：把第一个工作项视为默认工作项，更新其 score/deadline
    调用前需先 db.flush() 保证 pkg.id 与关系可访问。
    """
    items = list(pkg.work_items or [])
    if items:
        first = items[0]
        if score is not None:
            first.score = score
        parsed = parse_deadline(deadline_str_val)
        if parsed:
            first.deadline = parsed
        return first

    item = models.WorkItem(
        name=pkg.name or "默认工作项",
        work_package_id=pkg.id,
        score=score if score is not None else 0.0,
        deadline=parse_deadline(deadline_str_val) if deadline_str_val else None
    )
    db.add(item)
    return item
