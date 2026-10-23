"""数量和配置分值共用一批工作项；完成情况表示当前状态，不是历史快照。"""
from datetime import datetime
from fastapi import HTTPException
from repositories import dashboard_repository as repo


def period_bounds(period, year, month, quarter):
    first = month if period == "month" else (quarter - 1) * 3 + 1 if period == "quarter" else 1
    length = 1 if period == "month" else 3 if period == "quarter" else 12
    index = year * 12 + first - 1 + length
    return datetime(year, first, 1), datetime(index // 12, index % 12 + 1, 1)

def summarize_by_time(items, period, year, quarter, year_granularity="month"):
    # 时间汇总函数
    if period not in ("quarter", "year"):
        raise HTTPException( status_code=422, detail="时间维度只支持季度或年度查询")
    if year_granularity not in ("month", "quarter"):
        raise HTTPException(status_code=422, detail="年度时间粒度只能是 month 或 quarter")
    if period == "quarter" and quarter not in (1, 2, 3, 4):
        raise HTTPException( status_code=422, detail="季度必须为1到4")

    # 季度查询固定按月；年度查询使用用户选择的粒度。
    group_by_month = (period == "quarter" or year_granularity == "month")

    if period == "quarter":
        # 第1季度从1月开始，第2季度从4月开始，以此类推。
        first_month = (quarter - 1) * 3 + 1
        bucket_numbers = range(first_month, first_month + 3)
    elif group_by_month:
        bucket_numbers = range(1, 13)
    else:
        bucket_numbers = range(1, 5)

    groups = {} # 用于保存每个时间格子的统计结果

    for number in bucket_numbers:
        if group_by_month: # 时间粒度为月 
            bucket_id = f"{year}-{number:02d}"
            bucket_name = f"{number}月"
        else: # 时间粒度为季
            bucket_id = f"{year}-Q{number}"
            bucket_name = f"第{number}季度"

        groups[number] = {
            "id": bucket_id,
            "name": bucket_name,
            "order": number,
            "count": 0,
            "completed_count": 0,
            "pending_count": 0,
            "score": 0.0,
            "completed_score": 0.0,
            "pending_score": 0.0,
        }

    for item in items:
        deadline = item.deadline
        if deadline is None or deadline.year != year: continue

        if group_by_month: bucket_number = deadline.month
        else: bucket_number = (deadline.month - 1) // 3 + 1

        row = groups.get(bucket_number)
        if row is None:continue

        score = float(item.score or 0)
        row["count"] += 1
        row["score"] += score

        if item.complete_status:
            row["completed_count"] += 1
            row["completed_score"] += score

    for row in groups.values():
        row["pending_count"] = (row["count"] - row["completed_count"])

        row["score"] = round(row["score"], 2)
        row["completed_score"] = round(row["completed_score"], 2)

        row["pending_score"] = round(row["score"] - row["completed_score"], 2)

    return sorted(
        groups.values(),
        key=lambda row: row["order"],
    )


def summarize(items, dimension):
    groups = {}
    for item in items:
        owner = item.owner
        project = item.work_package.project if item.work_package else None
        if dimension == "department":
            name = (owner.department or "").strip() if owner else ""
            key, name = name or "未分配科室", name or "未分配科室"
        elif dimension == "person":
            key = str(item.owner_id or "unassigned")
            name = f"{owner.username}（{owner.id}）" if owner else "未分配人员"
        else:
            key = str(project.id) if project else "unassigned"
            name = f"{project.name or project.code}（{project.code}）" if project else "未分配项目"
        row = groups.setdefault(key, 
                                {"id": key, 
                                 "name": name,
                                 "project_code": project.code if dimension == "project" and project else None, 
                                 "count": 0, 
                                 "completed_count": 0,
                                  "score": 0.0, 
                                  "completed_score": 0.0}
                                )
        row["count"] += 1
        row["score"] += float(item.score or 0)
        if item.complete_status:
            row["completed_count"] += 1
            row["completed_score"] += float(item.score or 0)
    for row in groups.values():
        row["pending_count"] = row["count"] - row["completed_count"]
        row["score"] = round(row["score"], 2)
        row["completed_score"] = round(row["completed_score"], 2)
        row["pending_score"] = round(row["score"] - row["completed_score"], 2)
    return sorted(groups.values(), key=lambda row: (-row["count"], row["name"]))


def overview(db, user, period, year, month, quarter, dimension, year_granularity):
    role = getattr(user.role, "value", user.role)
    if str(role).upper() not in ("ADMIN", "LEADER"):
        raise HTTPException(status_code=403, detail="数据看板仅对领导和管理员开放")
    if period == "month" and dimension == "time":
        raise HTTPException(status_code=422, detail="月度查询不支持时间维度，请选择科室、人员或项目")
    start, end = period_bounds(period, year, month, quarter)
    items = repo.list_items(db, start, end)
    if dimension == "time":
        result = summarize_by_time(items, period, year, quarter, year_granularity)
    else:
        result = summarize(items, dimension)

    return {"items": result, 
            "start": start.date().isoformat(), 
            "end_exclusive": end.date().isoformat()}
