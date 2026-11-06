"""审批与转办流程的统一终止规则：仅发起人能终止尚在处理中的申请。"""

from fastapi import HTTPException


def terminate_request(db, model, request_id, applicant_id, applicant_field, pending_statuses):
    # 将发起人和可终止状态写进同一条 UPDATE 条件，避免与审核/接收操作并发时重复流转。
    updated = db.query(model).filter(
        model.id == request_id,
        applicant_field == applicant_id,
        model.status.in_(pending_statuses),
    ).update({model.status: "TERMINATED"}, synchronize_session=False)
    if not updated:
        # 区分记录不存在、无权操作、流程已结束，供页面显示准确的错误原因。
        request = db.get(model, request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="申请不存在")
        if str(getattr(request, applicant_field.key)) != str(applicant_id):
            raise HTTPException(status_code=403, detail="只有发起人可以终止流程")
        raise HTTPException(status_code=409, detail="该流程已结束，不能终止")
    db.commit()
    return {"code": 200, "message": "流程已终止", "data": {"id": request_id, "status": "TERMINATED"}}
