# xiangmu/backend/routers/review.py
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import (
    SplitRequestCreate,
    SplitRequestReview,
    SplitRequestEdit
)
from utils import work_package_summary, deadline_str, parse_deadline, ensure_open

router = APIRouter(prefix="/api/v1/review", tags=["Owner Review"])


# ---------------------------------------------------------------- 工作包拆分申请
def _split_request_view(req):
    """把拆分申请展开为前端需要的结构。"""
    work_package = req.work_package
    project = work_package.project if work_package else None
    try:
        items = json.loads(req.split_items or "[]")
    except Exception:
        items = []
    return {
        "id": req.id,
        "work_package_id": req.work_package_id,
        "work_package_code": work_package.code if work_package else "-",
        "work_package_name": work_package.name if work_package else "-",
        "work_package_objective": work_package.objective if work_package else "-",
        "project_id": work_package.project_id if work_package else None,
        "project_name": project.name if project else "-",
        "project_owner_id": project.owner_id,
        "project_owner_name": project.owner.username if project.owner else "",
        "category_name": work_package.category_name if work_package else "-",
        "applicant_id": req.applicant_id,
        "applicant_name": req.applicant.username if req.applicant else req.applicant_id,
        "reason": req.reason,
        "split_items": items,
        "status": req.status,
        "reviewer_id": req.reviewer_id or "",
        "review_comment": req.review_comment or "",
        "created_at": req.created_at.strftime("%Y-%m-%d %H:%M") if req.created_at else "-",
        "reviewed_at": req.reviewed_at.strftime("%Y-%m-%d %H:%M") if req.reviewed_at else "-",
    }


def _split_items_payload(items):
    """把工作项变更列表序列化为 JSON 字符串（带 work_item_id 表示编辑）。"""
    return json.dumps([
        {
            "work_item_id": it.work_item_id,
            "name": it.name,
            "standard": it.standard,
            "difficulty": it.difficulty,
            "importance": it.importance,
            "innovation": it.innovation,
            "deadline": it.deadline,
            "score": it.score,
            "owner_id": it.owner_id,
            "notes": it.notes
        }
        for it in items
    ], ensure_ascii=False)

# 除 name 外，还要必填的字段
REQUIRED_ITEM_FIELDS = ["difficulty", "importance", "innovation", "deadline"]

def require_work_item_fields(items, label="工作项"):
    for idx, it in enumerate(items or [], 1):
        missing = []
        # 兼容 Pydantic 对象 和 dict
        for f in REQUIRED_ITEM_FIELDS:
            v = it.get(f) if isinstance(it, dict) else getattr(it, f, None)
            if v is None or str(v).strip() == "":
                missing.append(f)
        if missing:
            raise HTTPException(status_code=400,
                                detail=f"第 {idx} 个工作项缺少必填项：{', '.join(missing)}")
        # 截止时间格式校验（可并入）
        dl = it.get("deadline") if isinstance(it, dict) else (it.deadline or "")
        if parse_deadline(dl) is None:
            raise HTTPException(status_code=400, detail=f"第 {idx} 个工作项截止时间格式不正确")


@router.post("/split-requests")
def create_split_request(req: SplitRequestCreate, db: Session = Depends(get_db)):
    """员工提交“拆解工作包为多个工作项”的申请。"""
    applicant = db.query(models.User).filter(models.User.id == req.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="申请人不存在")

    work_package = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == req.work_package_id
    ).first()
    if not work_package:
        raise HTTPException(status_code=404, detail="工作包不存在")
    ensure_open(work_package, work_package.project)  # 已关闭的工作包/项目不能再提交变更

    reason = (req.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="请填写拆分原因")
    if not req.split_items or not any((it.name or "").strip() for it in req.split_items):
        raise HTTPException(status_code=400, detail="请至少填写一个拆分出的工作项")

    # 权限：普通员工只能拆自己负责的工作包；领导/管理员可代拆
    role = str(applicant.role).upper()
    if role == "EMPLOYEE" and work_package.owner_id != applicant.id:
        raise HTTPException(status_code=403, detail="只能申请拆分自己负责的工作包")

    require_work_item_fields(req.split_items)

    new_req = models.WorkPackageSplitRequest(
        work_package_id=req.work_package_id,
        applicant_id=req.applicant_id,
        reason=reason,
        split_items=_split_items_payload(req.split_items),
        status="PENDING"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return {"code": 200, "message": "拆分申请已提交，等待领导审核", "data": {"id": new_req.id}}


@router.get("/split-requests")
def get_split_requests(user_id: str = Query(...), db: Session = Depends(get_db)):
    """查询拆分申请。
    - 普通员工：只看自己的申请
    - 科室主任 / 领导 / 管理员：查看全部申请（各自审核对应状态的申请）
    """
    viewer = db.query(models.User).filter(models.User.id == user_id).first()
    if not viewer:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = str(viewer.role).upper()
    if role in ["LEADER", "ADMIN", "DEPARTMENT"]:
        requests = db.query(models.WorkPackageSplitRequest).order_by(
            models.WorkPackageSplitRequest.created_at.desc()
        ).all()
    else:
        requests = db.query(models.WorkPackageSplitRequest).filter(
            models.WorkPackageSplitRequest.applicant_id == user_id
        ).order_by(models.WorkPackageSplitRequest.created_at.desc()).all()

    return {"code": 200, "data": [_split_request_view(r) for r in requests]}


@router.post("/split-requests/{request_id}/review")
def review_split_request(request_id: int, body: SplitRequestReview, db: Session = Depends(get_db)):
    """两级审核：
    - 科室主任 DEPARTMENT 审核 PENDING：同意(APPROVE)→直接生效 / 驳回(REJECT) / 提交(SUBMIT)→转领导
    - 领导 LEADER/ADMIN 审核 SUBMITTED：通过(APPROVE)→生效 / 驳回(REJECT)
    """
    req = db.query(models.WorkPackageSplitRequest).filter(
        models.WorkPackageSplitRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="拆分申请不存在")

    reviewer = db.query(models.User).filter(models.User.id == body.reviewer_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="审核人不存在")
    reviewer_role = str(reviewer.role).upper()

    action = (body.action or "APPROVE").upper()
    if action not in ["APPROVE", "REJECT", "SUBMIT"]:
        raise HTTPException(status_code=400, detail="无效的审核动作，只能是 APPROVE / REJECT / SUBMIT")

    # 按角色校验：谁、在什么状态下、能做什么操作
    if reviewer_role == "DEPARTMENT":
        # 科室主任：只审待科室主任的申请，三种操作均可
        if req.status != "PENDING":
            raise HTTPException(status_code=400, detail="该申请当前不在科室主任待审状态，不能重复处理")
    elif reviewer_role in ["LEADER", "ADMIN"]:
        # 领导/管理员：只审科室主任提交上来的申请，可通过或驳回，不能再提交
        if req.status != "SUBMITTED":
            raise HTTPException(status_code=400, detail="只有科室主任提交(SUBMITTED)的申请才由领导审核")
        if action == "SUBMIT":
            raise HTTPException(status_code=400, detail="领导审核时不能再次提交")
    else:
        raise HTTPException(status_code=403, detail="当前角色没有审核权限")

    try:
        if action == "SUBMIT":
            # 科室主任提交 → 转给领导
            req.status = "SUBMITTED"
            req.review_comment = (body.comment or "").strip() or "科室主任已提交，等待领导审核"
        elif action == "REJECT":
            comment = (body.comment or "").strip()
            if not comment:
                raise HTTPException(status_code=400, detail="驳回时必须填写驳回原因")
            req.status = "REJECTED"
            req.review_comment = comment
        else:  # APPROVE —— 同意/通过，最终生效，生成工作项
            work_package = db.query(models.WorkPackage).filter(
                models.WorkPackage.id == req.work_package_id
            ).first()
            if not work_package:
                raise HTTPException(status_code=400, detail="工作包不存在，无法拆分")
            ensure_open(work_package, work_package.project)  # 已关闭的工作包/项目不能再审批生效

            items = json.loads(req.split_items or "[]")
            if not items:
                raise HTTPException(status_code=400, detail="变更内容为空，无法处理")

            require_work_item_fields(items)

            for it in items:
                # 带 work_item_id → 编辑已有工作项；否则 → 新增
                if it.get("work_item_id"):
                    item = db.query(models.WorkItem).filter(
                        models.WorkItem.id == it["work_item_id"]
                    ).first()
                    if not item or str(item.work_package_id) != str(work_package.id):
                        raise HTTPException(status_code=400, detail="待编辑的工作项不存在或不属于该工作包")
                    ensure_open(item)  # 已关闭的工作项不能再被审批修改
                else:
                    # 新建的工作项默认归属工作包负责人，便于转办/后续负责人展示
                    item = models.WorkItem(work_package_id=work_package.id, owner_id=work_package.owner_id)
                    db.add(item)

                item.name = (it.get("name") or "").strip() or "未命名工作项"
                item.standard = it.get("standard")
                item.difficulty = it.get("difficulty")
                item.importance = it.get("importance")
                item.innovation = it.get("innovation")
                item.deadline = parse_deadline(it.get("deadline")) if it.get("deadline") else None
                item.score = it.get("score") or 0.0
                item.owner_id = it.get("owner_id") or work_package.owner_id
                item.notes = it.get("notes") if it.get("notes") else "-"
            req.status = "APPROVED"
            req.review_comment = (body.comment or "").strip() or "审核通过"

        req.reviewer_id = reviewer.id
        req.reviewed_at = datetime.now()
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理拆分申请失败: {str(e)}")

    message = {
        "APPROVE": "申请已通过并生成工作项",
        "REJECT": "申请已驳回",
        "SUBMIT": "已提交，等待领导审核",
    }.get(action, "操作成功")
    return {"code": 200, "message": message, "data": {"id": req.id, "status": req.status}}

@router.put("/split-requests/{request_id}")
def edit_split_request(request_id: int, body: SplitRequestEdit, db:Session = Depends(get_db)):
    req = db.query(models.WorkPackageSplitRequest).filter(models.WorkPackageSplitRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="拆分申请不存在")

    editor = db.query(models.User).filter(models.User.id == body.editor_id).first()
    if not editor:
        raise HTTPException(status_code=404, detail="操作人不存在")
    editor_role = str(editor.role).upper()

    ensure_open(req.work_package,
                req.work_package.project if req.work_package else None)  # 已关闭不能再改申请

    if not body.split_items or not any((it.name or "").strip() for it in body.split_items):
        raise HTTPException(status_code=400, detail="请至少保留一个有名的工作项")

    require_work_item_fields(body.split_items)

    reason = (body.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="请填写拆分原因")

    if editor_role == "EMPLOYEE":
    # 只能改自己的、且必须是被驳回的
        if str(req.applicant_id) != str(editor.id):
            raise HTTPException(status_code=403, detail="只能修改自己发起的申请")
        if req.status != "REJECTED":
            raise HTTPException(status_code=400, detail="只有被驳回的申请才能修改并重新提交")

        req.split_items = _split_items_payload(body.split_items)   # 存 JSON 字符串
        req.reason = reason
        req.status = "PENDING"                    # 重置为待科室审核（重新提交）
        req.reviewer_id = None                     # 清空上次的审核记录
        req.reviewed_at = None
        req.review_comment = None
        message = "已修改并重新提交，等待科室审核"

    elif editor_role in ["LEADER"]:
        # 领导只能改提交到领导这级的申请
        if req.status != "SUBMITTED":
            raise HTTPException(status_code=400, detail="只有提交到领导审核的申请才能修改")

        req.split_items = _split_items_payload(body.split_items)
        req.reason = reason
        # 状态保持 SUBMITTED，改完由领导再点“通过”生效
        message = "内容已更新，可继续审核"

    elif editor_role == "DEPARTMENT":
        # 可选：科室主任在待审(PENDING)时也能直接改内容
        if req.status != "PENDING":
            raise HTTPException(status_code=400, detail="当前状态不允许修改")
        req.split_items = _split_items_payload(body.split_items)
        req.reason = reason
        message = "内容已更新"

    else:
        raise HTTPException(status_code=403, detail="当前角色没有编辑权限")

    db.commit()
    db.refresh(req)
    return {"code": 200, "message": message,
            "data": {"id": req.id, "status": req.status}}

