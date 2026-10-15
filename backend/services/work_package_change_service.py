"""科室/管理员提交申请，领导通过或驳回；提交时不改正式工作包。"""
import json
from datetime import datetime
from fastapi import HTTPException
import models
from repositories import work_package_change_repository as repo
from utils import ensure_open, package_effective_complete

# 规定允许申请修改哪些字段
FIELDS = ('code', 'name', 'project_id', 'category_name', 'owner_id', 'tech_owner_id', 'objective')

# 生成工作包快照
def snapshot(pkg):
    # 现有表没有工作包版本列，用完整原值快照检测提交后的字段变化。
    return {**{key: getattr(pkg, key) for key in FIELDS},
            'isclosed': pkg.isclosed, 'complete_status': pkg.complete_status}

# 复制工作包当前信息，生成快照
def validate(db, data):
    project = db.query(models.Project).filter_by(id=data['project_id']).with_for_update().first()
    if not project:
        raise HTTPException(400, '所属项目不存在')
    ensure_open(project)
    if not data['code'] or len(data['code']) > 50 or len(data['name']) > 100:
        raise HTTPException(400, '工作包编号不能为空且不能超过50字，名称不能超过100字')
    if not db.query(models.WorkPackageCategory).filter_by(name=data['category_name']).first():
        raise HTTPException(400, '工作包类型不存在')
    for key in ('owner_id', 'tech_owner_id'):
        if data[key] and not db.query(models.User).filter_by(id=data[key], is_deleted=False).first():
            raise HTTPException(400, '所选负责人不存在或已删除')

# 判断工作包是否可以删除
def check_delete(db, pkg):
    ensure_open(pkg, pkg.project)
    if package_effective_complete(pkg):
        raise HTTPException(400, '工作包已完成，不能删除')
    # 不级联销毁工时、积分和拆分记录；有业务数据时使用已有关闭功能。
    for model in (models.WorkItem, models.WorkTimeSession, models.TaskTransfer, models.WorkPackageSplitRequest):
        if db.query(model).filter_by(work_package_id=pkg.id).first():
            raise HTTPException(400, '工作包存在工作项或历史记录，请使用关闭功能')

# 提交新增、修改、删除申请
def submit(db, user, body=None, package_id=None, reason=None):
    if user.role.upper() not in ('ADMIN', 'DEPARTMENT'):
        raise HTTPException(403, '只有科室或管理员可以提交工作包增删改申请')
    # 去除首尾空白后验证，防止只输入空格；不把原因写进正式工作包。
    reason = (body.reason if body is not None else reason) or ''
    reason = reason.strip()
    if not reason or len(reason) > 2000:
        raise HTTPException(400, '请填写申请原因，且不能超过2000字')
    action = 'delete' if body is None else ('update' if body.id else 'create') # 申请类型
    target_id = package_id if body is None else body.id # 目标工作包
    pkg = repo.package(db, target_id) if target_id else None # 检查现有工作包是否允许申请

    if action != 'create' and not pkg:
        raise HTTPException(404, '工作包不存在')
    if pkg:
        ensure_open(pkg, pkg.project)
        if repo.pending(db, pkg.id):
            raise HTTPException(409, '该工作包已有待审核申请，请等待领导处理')
    data = None
    if body is not None:
        project_id = body.project_id
        if not project_id:
            project = db.query(models.Project).filter_by(name=body.project_name).first()
            project_id = project.id if project else None
        data = dict(code=(body.work_package_code or '').strip(), 
                    name=(body.name or '-').strip(),
                    project_id=project_id, 
                    category_name=body.category_name,
                    owner_id=body.owner_id or None, 
                    tech_owner_id=body.tech_owner_id or None,
                    objective=(body.objective or '').strip())
        validate(db, data)
    else:
        check_delete(db, pkg)
    req = models.WorkPackageChangeRequest(
        action=action,
        work_package_id=pkg.id if pkg else None,
        project_id=data['project_id'] if data else pkg.project_id,
        applicant_id=user.id, status='PENDING', 
        base_version=1, reason=reason,
        before_data=json.dumps(snapshot(pkg), ensure_ascii=False) if pkg else None,
        after_data=json.dumps(data, ensure_ascii=False) if data else None)
    db.add(req)
    db.commit()
    return {'code': 200, 'message': '申请已提交，等待领导审核', 'data': {'request_id': req.id}}

# 整理申请列表，返回给前端
def list_requests(db, user):
    result = []
    for req in repo.requests(db, user):
        before = json.loads(req.before_data) if req.before_data else None
        after = json.loads(req.after_data) if req.after_data else None
        reviewer = db.get(models.User, req.reviewer_id) if req.reviewer_id else None
        project = db.get(models.Project, req.project_id)
        result.append(dict(id=req.id, action=req.action, status=req.status,
            before_data=before, after_data=after, reason=req.reason, project_name=project.name if project else '-',
            applicant_name=req.applicant.username if req.applicant else req.applicant_id,
            reviewer_name=reviewer.username if reviewer else '-', review_comment=req.review_comment,
            created_at=req.created_at, reviewed_at=req.reviewed_at))
    return {'code': 200, 'data': result}

# 领导审核申请
def review(db, user, request_id, decision, comment):
    if user.role.upper() != 'LEADER':
        raise HTTPException(403, '只有领导可以审核工作包变更')
    if decision not in ('APPROVE', 'REJECT'):
        raise HTTPException(400, '审核只能选择通过或驳回')
    
    try:
        req = repo.request(db, request_id)
        if not req:
            raise HTTPException(404, '申请不存在')
        if req.status != 'PENDING':
            raise HTTPException(409, '申请已处理，请刷新列表')
        
        if decision == 'APPROVE':
            if req.action not in ('create', 'update', 'delete'):
                raise HTTPException(400, '未知申请类型')
            pkg = repo.package(db, req.work_package_id) if req.work_package_id else None
            if req.action != 'create':
                if not pkg:
                    raise HTTPException(409, '原工作包已不存在')
                ensure_open(pkg, pkg.project)
                if snapshot(pkg) != json.loads(req.before_data):
                    raise HTTPException(409, '工作包已变化，请驳回后重新提交申请')
            if req.action == 'delete':
                check_delete(db, pkg)
                # 保留申请快照；先解除全部历史申请的外键，再删除正式工作包。
                db.query(models.WorkPackageChangeRequest).filter_by(work_package_id=pkg.id).update(
                    {'work_package_id': None}, synchronize_session='fetch')
                db.flush()
                db.delete(pkg)
            else:
                data = json.loads(req.after_data)
                validate(db, data)  # 审批时重新验证，防止字典/人员已失效。
                if req.action == 'create':
                    pkg = models.WorkPackage(**{key: data[key] for key in FIELDS})
                    db.add(pkg)
                    db.flush()
                    req.work_package_id = pkg.id
                else:
                    for key in FIELDS:
                        setattr(pkg, key, data[key])
        req.status = 'APPROVED' if decision == 'APPROVE' else 'REJECTED'
        req.reviewer_id = user.id
        req.review_comment = comment
        req.reviewed_at = datetime.now()
        db.commit()  # 工作包变更与审批结果在同一事务中生效。
    except Exception:
        db.rollback()
        raise
    return {'code': 200, 'message': '已通过并生效' if decision == 'APPROVE' else '已驳回'}
