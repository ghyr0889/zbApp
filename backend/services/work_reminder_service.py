# 工作待办文件，包括拆包提示、工作项到期提醒.
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

import models

# 待办仅需北京时间的日期；固定 UTC+8 可避免 Windows 打包时缺失 tzdata 导致启动失败。
SHANGHAI = timezone(timedelta(hours=8))


def list_work_reminders(db: Session, user_id: str, today=None):
    today = today or datetime.now(SHANGHAI).date()
    latest_deadline = datetime.combine(today + timedelta(days=4), time.min)

    # 未分解的工作包
    packages = db.query(models.WorkPackage).join(models.Project).filter(
        models.WorkPackage.owner_id == user_id,
        models.WorkPackage.isclosed.isnot(True),
        models.WorkPackage.complete_status.isnot(True),
        models.Project.isclosed.isnot(True),
        ~models.WorkPackage.work_items.any(),
        ~models.WorkPackage.split_requests.any(
            models.WorkPackageSplitRequest.status.in_(("PENDING", "SUBMITTED"))
        ),
    ).order_by(models.WorkPackage.id).all()

    # 过期或即将到期的工作项
    items = db.query(models.WorkItem).join(models.WorkPackage).join(models.Project).filter(
        models.WorkItem.owner_id == user_id,
        models.WorkItem.complete_status.isnot(True),
        models.WorkItem.isclosed.isnot(True),
        models.WorkItem.deadline < latest_deadline,
        models.WorkPackage.isclosed.isnot(True),
        models.Project.isclosed.isnot(True),
    ).order_by(models.WorkItem.deadline, models.WorkItem.id).all()

    reminders = []
    for package in packages:
        reminders.append({
            "key": f"package:{package.id}", "kind": "undecomposed", "severity": "info",
            "title": f"工作包 {package.code} 尚未分解",
            "description": f"{package.name or package.code}：请添加并提交工作项。",
            "project_id": package.project_id, "work_package_id": package.id,
            "work_item_id": None, "deadline": None, "days": None,
        })

    for item in items:
        days = (item.deadline.date() - today).days
        if days < 0:
            kind, severity, message = "overdue", "danger", f"已超期 {-days} 天"
        elif days == 0:
            kind, severity, message = "due_today", "warning", "今天到期"
        else:
            kind, severity, message = "due_soon", "warning", f"还有 {days} 天到期"
        package = item.work_package
        reminders.append({
            "key": f"item:{item.id}", "kind": kind, "severity": severity,
            "title": f"工作项 {item.name} {message}",
            "description": f"工作包 {package.code} · 截止日期 {item.deadline.date().isoformat()}",
            "project_id": package.project_id, "work_package_id": package.id,
            "work_item_id": item.id, "deadline": item.deadline.date().isoformat(),
            "days": days,
        })

    # 生成跳转信息并排序
    if reminders:
        project_ids = {row["project_id"] for row in reminders}
        package_pages = {}
        last_project = None
        position = 0
        for project_id, package_id in db.query(models.WorkPackage.project_id, models.WorkPackage.id).filter(
            models.WorkPackage.project_id.in_(project_ids)
        ).order_by(models.WorkPackage.project_id, models.WorkPackage.id):
            if project_id != last_project:
                last_project, position = project_id, 0
            package_pages[package_id] = position // 20 + 1
            position += 1
        for reminder in reminders:
            reminder["package_page"] = package_pages.get(reminder["work_package_id"], 1)

    order = {"overdue": 0, "due_today": 1, "due_soon": 2, "undecomposed": 3}
    reminders.sort(key=lambda row: (order[row["kind"]], row["deadline"] or "", row["key"]))
    return reminders
