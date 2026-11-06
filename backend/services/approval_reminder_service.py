"""根据当前登录用户的身份，从数据库找出他有权处理、且仍待审批的申请，并整理成右下角“待办”框使用的提醒数据"""

import models
from utils import pending_status_for


def list_approval_reminders(db, viewer):
    role = str(viewer.role or "").upper()
    reminders = []

    if role in ("DEPARTMENT", "LEADER", "ADMIN"):
        status = pending_status_for(role)
        requests = db.query(models.WorkPackageSplitRequest).filter(
            models.WorkPackageSplitRequest.status == status
        ).order_by(models.WorkPackageSplitRequest.created_at, models.WorkPackageSplitRequest.id).all()
        for req in requests:
            package = req.work_package
            reminders.append({
                "key": f"split-approval:{req.id}", "kind": "split_approval", "severity": "info",
                "title": f"工作项变更申请待{'科室' if role == 'DEPARTMENT' else '部门'}审批",
                "description": f"工作包 {package.code if package else req.work_package_id} · 申请人 {req.applicant.username if req.applicant else req.applicant_id}",
                "tab": "review", "request_id": req.id,
            })

    if role == "LEADER":
        requests = db.query(models.WorkPackageChangeRequest).filter_by(status="PENDING").order_by(
            models.WorkPackageChangeRequest.created_at, models.WorkPackageChangeRequest.id
        ).all()
        actions = {"create": "新增", "update": "修改", "delete": "删除"}
        for req in requests:
            reminders.append({
                "key": f"package-change-approval:{req.id}", "kind": "package_change_approval", "severity": "info",
                "title": f"工作包{actions.get(req.action, '变更')}申请待审批",
                "description": f"工作包 {req.work_package.code if req.work_package else '新增'} · 申请人 {req.applicant.username if req.applicant else req.applicant_id}",
                "tab": "packageChanges", "request_id": req.id,
            })

    # Completing an item is reviewed by its technical owner, irrespective of role.
    requests = db.query(models.WorkItemCompletionReview).join(models.WorkItem).filter(
        models.WorkItemCompletionReview.status == "PENDING",
        models.WorkItem.tech_owner_id == viewer.id,
    ).order_by(models.WorkItemCompletionReview.created_at, models.WorkItemCompletionReview.id).all()
    for req in requests:
        reminders.append({
            "key": f"completion-approval:{req.id}", "kind": "completion_approval", "severity": "info",
            "title": f"工作项 {req.work_item.name} 完成申请待审批",
            "description": f"申请人 {req.applicant.username if req.applicant else req.applicant_id} · 请审核完成情况并填写质量系数",
            "tab": "complete", "request_id": req.id,
        })

    return reminders
