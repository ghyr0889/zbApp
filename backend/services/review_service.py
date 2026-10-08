"""业务层：负责权限规则、状态流转、结果组装和事务；数据查询交给 repository。"""
from repositories import review_repository as repo
import json
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models
from schemas import (
    SplitRequestCreate,
    SplitRequestReview,
    SplitRequestEdit,
    RemoveSplitItem
)
from utils import parse_deadline, ensure_open, pending_status_for



# 角色判断函数（状态映射表见 utils.pending_status_for，全站唯一）
def _pending_status_for(role: str) -> str:
    status = pending_status_for(role)
    if not status:
        raise HTTPException(status_code=403, detail=f"未知角色，无法统计待办: {role}")
    return status

# 工作包拆分申请
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
        "pkg_closed": work_package.isclosed,
        "project_id": work_package.project_id if work_package else None,
        "project_name": project.name if project else "-",
        "project_owner_id": project.owner_id,
        "project_owner_name": project.owner.username if project.owner else "",
        "project_closed": project.isclosed,
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
            "client_id": it.client_id or uuid4().hex,  # 前端生成的唯一标识，便于删除
            "work_item_id": it.work_item_id,
            "name": it.name,
            "standard": it.standard,
            "difficulty": it.difficulty,
            "importance": it.importance,
            "innovation": it.innovation,
            "deadline": it.deadline,
            "score": it.score,
            "owner_id": it.owner_id,
            "tech_owner_id": it.tech_owner_id,
            "notes": it.notes,
        }
        for it in items
    ], ensure_ascii=False)

# 除 name 外，还要必填的字段
REQUIRED_ITEM_FIELDS = ["difficulty", "importance", "innovation", "deadline", "tech_owner_id"]
ITEM_FIELD_LABELS = {
    "difficulty": "难度",
    "importance": "重要度",
    "innovation": "创新度",
    "deadline": "截止时间",
    "tech_owner_id": "技术负责人",
}

def require_work_item_fields(items, label="工作项"):
    for idx, it in enumerate(items or [], 1):
        missing = []
        # 兼容 Pydantic 对象 和 dict
        for f in REQUIRED_ITEM_FIELDS:
            v = it.get(f) if isinstance(it, dict) else getattr(it, f, None)
            if v is None or str(v).strip() == "":
                missing.append(ITEM_FIELD_LABELS.get(f, f))
        if missing:
            raise HTTPException(status_code=400,
                                detail=f"第 {idx} 个工作项缺少必填项：{', '.join(missing)}")
        # 截止时间格式校验（可并入）
        dl = it.get("deadline") if isinstance(it, dict) else (it.deadline or "")
        if parse_deadline(dl) is None:
            raise HTTPException(status_code=400, detail=f"第 {idx} 个工作项截止时间格式不正确")


def create_split_request(req: SplitRequestCreate, db: Session = None):
    """员工提交“拆解工作包为多个工作项”的申请。"""
    applicant = repo.get_user(db, req.applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="申请人不存在")

    work_package = repo.get_package(db, req.work_package_id)
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
    for it in req.split_items:
        if not it.work_item_id:
            if role == "EMPLOYEE" and work_package.owner_id != applicant.id:
                    raise HTTPException(status_code=403, detail="只能申请拆分自己负责的工作包")
        else:
            # 带 work_item_id 的，表示编辑已有工作项；普通员工只能编辑自己负责的工作项
            item = repo.get_item(db, it.work_item_id)
            if not item or str(item.work_package_id) != str(work_package.id):
                raise HTTPException(status_code=400, detail="待编辑的工作项不存在或不属于该工作包")
            if role == "EMPLOYEE" and str(item.owner_id) != str(applicant.id):
                raise HTTPException(status_code=403, detail="只能编辑自己负责的工作项")

    require_work_item_fields(req.split_items)

    for item in req.split_items:
        item_dict = item.model_dump()  # 转为字典
        if not item_dict.get("client_id"):
            item_dict["client_id"] = uuid4().hex
        # 后续使用 item_dict，或者如果需要转回模型：
        # item = SplitItemIn(**item_dict)

    new_req = models.WorkPackageSplitRequest(
        work_package_id=req.work_package_id,
        applicant_id=req.applicant_id,
        reason=reason,
        split_items=_split_items_payload(req.split_items),
        status="PENDING"
    )
    repo.add(db, new_req)
    db.commit()
    db.refresh(new_req)
    return {"code": 200, "message": "拆分申请已提交，等待领导审核", "data": {"id": new_req.id}}


def get_split_requests(user_id: str, db: Session = None):
    """查询拆分申请。
    - 普通员工：只看自己的申请
    - 科室主任 / 领导 / 管理员：查看全部申请（各自审核对应状态的申请）
    """
    viewer = repo.get_user(db, user_id)
    if not viewer:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = str(viewer.role).upper()
    pending_status = _pending_status_for(role)

    requests = repo.list_split_requests(db, user_id, pending_status, role in ("LEADER", "ADMIN", "DEPARTMENT"))
    return {
        "code": 200,
        "pending_status": pending_status,
        "data": [_split_request_view(r) for r in requests]}


def review_split_request(request_id: int, body: SplitRequestReview, db: Session = None):
    """两级审核：
    - 科室主任 DEPARTMENT 审核 PENDING：同意(APPROVE)→直接生效 / 驳回(REJECT) / 提交(SUBMIT)→转领导
    - 领导 LEADER/ADMIN 审核 SUBMITTED：通过(APPROVE)→生效 / 驳回(REJECT)
    """
    req = repo.get_split_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="拆分申请不存在")

    reviewer = repo.get_user(db, body.reviewer_id)
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
            work_package = repo.get_package(db, req.work_package_id)
            if not work_package:
                raise HTTPException(status_code=400, detail="工作包不存在，无法拆分")
            ensure_open(work_package, work_package.project)  # 已关闭的工作包/项目不能再审批生效

            items = json.loads(req.split_items or "[]")
            if not items:
                raise HTTPException(status_code=400, detail="变更内容为空，无法处理")

            require_work_item_fields(items)

            affected = []  # 本次审批生效的工作项，最后统一同步 completed_at
            for it in items:
                # 带 work_item_id → 编辑已有工作项；否则 → 新增
                if it.get("work_item_id"):
                    item = repo.get_item(db, it['work_item_id'])
                    if not item or str(item.work_package_id) != str(work_package.id):
                        raise HTTPException(status_code=400, detail="待编辑的工作项不存在或不属于该工作包")
                    ensure_open(item)  # 已关闭的工作项不能再被审批修改
                else:
                    # 新建的工作项默认归属工作包负责人，便于转办/后续负责人展示
                    item = models.WorkItem(work_package_id=work_package.id, owner_id=work_package.owner_id)
                    repo.add(db, item)

                item.name = (it.get("name") or "").strip() or "未命名工作项"
                item.standard = it.get("standard")
                item.difficulty = it.get("difficulty")
                item.importance = it.get("importance")
                item.innovation = it.get("innovation")
                item.deadline = parse_deadline(it.get("deadline")) if it.get("deadline") else None
                item.score = it.get("score") or 0.0
                item.owner_id = it.get("owner_id") or work_package.owner_id
                # 技术负责人：仅当申请里明确带了该字段时才覆盖（兼容历史申请 JSON）
                if "tech_owner_id" in it:
                    item.tech_owner_id = it.get("tech_owner_id") or None
                item.notes = it.get("notes") if it.get("notes") else "-"

                affected.append(item)  # 记录受影响的工作项，后续批量同步 completed_at

            db.flush()                              # 先把 item.score 落库，SUM 查询才准
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

def edit_split_request(request_id: int, body: SplitRequestEdit, db:Session = None):
    req = repo.get_split_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="拆分申请不存在")

    editor = repo.get_user(db, body.editor_id)
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

    old_items = json.loads(req.split_items or "[]") if req.split_items else []
    old_map = {}
    for old in old_items:
        name = old.get("name", "").strip()
        if name:
            old_map[name] = old

    # 合并client_id：如果新项有对应的旧项，保留旧项的client_id
    merged_items = []
    for new_item in body.split_items:
        new_item_dict = new_item if isinstance(new_item, dict) else new_item.dict()
        name = new_item_dict.get("name", "").strip()
        if name in old_map and old_map[name].get("client_id"): # 如果存在同名旧项，且旧项有client_id，新项没有，则复制
            if not new_item_dict.get("client_id"):
                new_item_dict["client_id"] = old_map[name]["client_id"]
        merged_items.append(new_item_dict)

    # ---- 权限与状态流转判定：全部基于【原始状态】，必须在写库之前完成 ----
    old_status = req.status
    is_applicant = str(req.applicant_id) == str(editor.id)

    if old_status == "PENDING":
        if editor_role not in ("DEPARTMENT", "ADMIN"):
            raise HTTPException(status_code=403, detail="待科室审核的申请只能由科室主任修改")
        new_status = "PENDING"
        message = "内容已更新，等待科室审核"
        reset_review = False

    elif old_status == "SUBMITTED":
        if editor_role not in ("LEADER", "ADMIN"):
            raise HTTPException(status_code=403, detail="待领导审核的申请只能由领导修改")
        new_status = "SUBMITTED"
        message = "内容已更新，可继续审核"
        reset_review = False

    elif old_status == "REJECTED":
        if not is_applicant:
            raise HTTPException(status_code=403, detail="只有申请人本人可以修改被驳回的申请")
        new_status = "PENDING"            # 改完重新提交，回到科室审核
        message = "已修改并重新提交，等待科室审核"
        reset_review = True               # 只有这条路径要清空上一次的审核痕迹

    else:  # APPROVED
        raise HTTPException(status_code=400, detail="已通过的申请不能再修改")

    # ---- 判定通过后才写库 ----
    req.split_items = _split_items_payload(body.split_items)
    req.reason = reason
    req.status = new_status
    if reset_review:
        req.reviewer_id = None
        req.reviewed_at = None
        req.review_comment = None

    db.commit()
    db.refresh(req)
    return {"code": 200, "message": message, "data": {"id": req.id, "status": req.status}}

def remove_item_from_split_request(request_id: int, body: RemoveSplitItem, db: Session = None):
    """从拆分申请中移除一个工作项（编辑时使用）。"""
    req = repo.get_split_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")

    editor = repo.get_user(db, body.editor_id)
    if not editor:
        raise HTTPException(status_code=404, detail="操作人不存在")
    editor_role = str(editor.role).upper()

    ensure_open(req.work_package,
                req.work_package.project if req.work_package else None)  # 已关闭不能再改申请

    if editor_role == "EMPLOYEE":
        if str(req.applicant_id) != str(editor.id):
            raise HTTPException(status_code=403, detail="只能修改自己发起的申请")
        if req.status != "REJECTED":
            raise HTTPException(status_code=400, detail="只有被驳回的申请才能修改并重新提交")
    elif editor_role == "DEPARTMENT":
        if req.status != "PENDING":
            raise HTTPException(status_code=400, detail="当前状态不允许修改")
    elif editor_role in ["LEADER"]:
        # 领导只能改提交到领导这级的申请
        if req.status != "SUBMITTED":
            raise HTTPException(status_code=400, detail="只有提交到领导审核的申请才能修改")
    else:
        raise HTTPException(status_code=403, detail="当前角色没有编辑权限")

    try:
        client = json.loads(req.split_items or "[]") #原始拆分列表
        new_client = [it for it in client if it.get("client_id") != body.client_id] #新拆分列表
        if len(new_client) == 0:
            raise HTTPException(status_code=400, detail="拆分申请中至少要保留一个工作项")

        if len(new_client) == len(client): # 长度没变，说明没有找到要删除的工作项
            raise HTTPException(status_code=404, detail="指定的工作项在申请中不存在")

        req.split_items = json.dumps(new_client, ensure_ascii=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除工作项失败: {str(e)}")

    return {"code": 200, "message": "工作项已从拆分申请中移除", "data": {"id": req.id}}
