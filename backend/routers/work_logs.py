"""接口层：只接收参数、注入数据库会话并调用业务层。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from schemas import ConfirmCompletionIn, ConfirmClosed
from services import work_logs_service as service

router = APIRouter(prefix='/api/v1/work-logs', tags=['Work Logs'])


def require_leader(user):
    if str(user.role).upper() != "LEADER":
        raise HTTPException(status_code=403, detail="仅部门领导可以查看分配工作")


def assignment_person(db, user_id):
    import models
    person = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted.isnot(True)).first()
    if not person:
        raise HTTPException(status_code=404, detail="人员不存在")
    return person


@router.get("/assignments")
def list_assignments(page: int = 1, page_size: int = 20, keyword: str = "",
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_leader(user)
    from sqlalchemy import func, or_
    import models
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    totals = db.query(models.WorkItem.owner_id.label("owner_id"),
                      func.count(models.WorkItem.id).label("item_count"),
                      func.sum(models.WorkItem.score).label("total_score")).group_by(models.WorkItem.owner_id).subquery()
    query = db.query(models.User, totals.c.item_count, totals.c.total_score).outerjoin(
        totals, totals.c.owner_id == models.User.id).filter(models.User.is_deleted.isnot(True))
    if keyword.strip():
        term = f"%{keyword.strip()}%"
        query = query.filter(or_(models.User.username.like(term), models.User.id.like(term)))
    total = query.count()
    rows = query.order_by(models.User.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"code": 200, "data": {"total": total, "items": [
        {"user_id": person.id, "username": person.username, "department": person.department or "",
         "work_item_count": count or 0, "total_score": round(float(score or 0), 3)}
        for person, count, score in rows]}}


@router.get("/assignments/{user_id}/packages")
def assigned_packages(user_id: str, page: int = 1, page_size: int = 20,
                      show_completed: bool = False, show_related: bool = False,
                      db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_leader(user)
    person = assignment_person(db, user_id)
    result = service.get_my_work_packages_paged(user_id, page, page_size, db, show_completed, show_related)
    result["data"]["username"] = person.username
    return result


@router.get("/my-assigned-work-packages/{user_id}")
def get_my_assigned_work_packages(user_id: str, db: Session = Depends(get_db)):
    """返回当前用户负责的工作包（用于申请拆分工作包等场景）。"""
    return service.get_my_assigned_work_packages(user_id=user_id, db=db)


@router.get("/projects")
def get_paged_projects(page: int = 1,
                       page_size: int = 20,
                       keyword: str = None,
                       owner_id: str = None,
                       level: str = None,
                       complete_status: str = None,
                       db: Session = Depends(get_db)):
    """项目分页 + 筛选 + 聚合统计：keyword(编号/名称)、owner_id、level、complete_status。"""
    return service.get_paged_projects(
        page=page,
        page_size=page_size,
        keyword=keyword,
        owner_id=owner_id,
        level=level,
        complete_status=complete_status,
        db=db,
    )


@router.get("/projects/{project_id}")
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """项目详情（含聚合统计），供项目详情页标题/信息卡使用。"""
    return service.get_project_detail(project_id=project_id, db=db)


@router.get("/projects/{project_id}/work-packages")
def get_paged_project_work_packages(project_id: int,
                                    page: int = 1,
                                    page_size: int = 20,
                                    keyword: str = None,
                                    db: Session = Depends(get_db)):
    """某项目下的工作包分页 + 筛选：keyword(工作包编号/类别/下阶段工作)。"""
    return service.get_paged_project_work_packages(
        project_id=project_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        db=db,
    )


@router.get("/my-work-packages/{user_id}")
def get_my_work_packages_paged(user_id: str,
                              page: int = 1,
                              page_size: int = 20,
                              show_completed: bool = False,
                              show_related: bool = False,
                              db: Session = Depends(get_db),
                              user=Depends(get_current_user)):
    """我的工作：查询本人负责的工作包及本人工作项所属工作包。"""
    if str(user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="只能查看自己的工作")
    return service.get_my_work_packages_paged(user_id=user.id, page=page, page_size=page_size, db=db,
                                               show_completed=show_completed, show_related=show_related)


@router.get("/work-packages/{work_package_id}/work-items")
def get_work_items(work_package_id: str,
                   month: str = None,
                   view_user_id: str = None,
                   only_mine: bool = False,
                   show_completed: bool = False,
                   show_related: bool = False,
                   db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    """我的工作按登录用户筛选；项目详情默认保留全部工作项。"""
    if view_user_id is not None:
        require_leader(user)
        assignment_person(db, view_user_id)
        only_mine = True
    return service.get_work_items(work_package_id=work_package_id, month=month, db=db,
                                  owner_id=(view_user_id or user.id) if only_mine else None,
                                  show_completed=show_completed if only_mine else True,
                                  show_related=show_related if only_mine else False)


@router.delete("/work-items/{work_item_id}")
def delete_work_item(work_item_id: int, db: Session = Depends(get_db)):
    """删除工作项。"""
    return service.delete_work_item(work_item_id=work_item_id, db=db)


@router.put("/confirm-completion")
def confirm_completion(data: ConfirmCompletionIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """确认/取消完成。

    - 工作项：改为“提交完成申请 / 撤回申请”，由技术负责人在 complete_review 里审核，
      审核通过后才置 complete_status 并写 completed_at。
    - 工作包 / 项目：仍是负责人（或领导/管理员）直接手动确认。
    """
    return service.confirm_completion(data=data.model_copy(update={"user_id": user.id}), db=db)


@router.put("/confirm-closed")
def confirm_closed(data: ConfirmClosed, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """确认关闭：或领导/管理员可操作。"""
    return service.confirm_closed(data=data.model_copy(update={"user_id": user.id}), db=db)
