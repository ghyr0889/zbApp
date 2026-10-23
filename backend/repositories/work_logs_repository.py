"""数据访问层：封装查询和持久化操作，不决定业务权限，不提交事务。"""
from sqlalchemy import or_, exists
from sqlalchemy.orm import selectinload, aliased
import models


def list_projects_page(db, page, page_size, keyword, owner_id, level, complete_status):
    """查询项目分页及其统计所需关联数据。"""
    q = db.query(models.Project)
    if keyword and str(keyword).strip():
        kw = f"%{str(keyword).strip()}%"
        q = q.filter(or_(models.Project.code.like(kw),
                         models.Project.name.like(kw),
                         models.Project.tech_owner.has(models.User.username.like(kw)),
                        )
                    )
    if owner_id:
        q = q.filter(models.Project.owner_id == owner_id)
    if level:
        q = q.filter(models.Project.level == level)
    if complete_status is not None and str(complete_status) != "":
        flag = str(complete_status).lower() in ("1", "true", "yes")
        q = q.filter(models.Project.complete_status == flag)

    total = q.count()
    projects = q.options(
        selectinload(models.Project.owner),
        selectinload(models.Project.work_packages).selectinload(
            models.WorkPackage.work_items
        ).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.Project.id).offset((page - 1) * page_size).limit(page_size).all()

    return total, projects


def list_project_packages_page(db, project_id, page, page_size, keyword):
    """查询项目下工作包分页，保留原筛选口径。"""
    q = db.query(models.WorkPackage).filter(models.WorkPackage.project_id == project_id)
    if keyword and str(keyword).strip():
        kw = f"%{str(keyword).strip()}%"
        q = q.filter(or_(
            models.WorkPackage.id.like(kw),
            models.WorkPackage.category_name.like(kw),
        ))

    total = q.count()
    pkgs = q.options(
        selectinload(models.WorkPackage.owner),
        selectinload(models.WorkPackage.project).selectinload(models.Project.owner),
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.WorkPackage.id).offset((page - 1) * page_size).limit(page_size).all()

    return total, pkgs


def personal_item_condition(user_id, show_completed=True, show_related=False):
    """关联范围为当前仍含本人负责工作项的工作包，不依赖转办记录。"""
    condition = models.WorkItem.owner_id == user_id
    if show_related:
        own_item = aliased(models.WorkItem)
        from sqlalchemy import select
        owned_packages = select(own_item.work_package_id).where(own_item.owner_id == user_id)
        condition = models.WorkItem.work_package_id.in_(owned_packages)
    if not show_completed:
        condition = condition & models.WorkItem.complete_status.isnot(True)
    return condition


def list_my_packages_page(db, user_id, page, page_size, show_completed=True, show_related=False):
    """本人负责的工作包和本人工作项所属工作包都参与分页，包括未分解工作包。"""
    q = db.query(models.WorkPackage).filter(or_(
        models.WorkPackage.owner_id == user_id,
        models.WorkPackage.work_items.any(
            personal_item_condition(user_id, show_completed, show_related)),
    ))
    total = q.count()
    pkgs = q.options(
        selectinload(models.WorkPackage.owner),
        selectinload(models.WorkPackage.project).selectinload(models.Project.owner),
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.WorkPackage.id).offset((page - 1) * page_size).limit(page_size).all()

    return total, pkgs


def list_assigned_packages(db, user_id):
    """查询本人负责的工作包。"""
    return db.query(models.WorkPackage).filter(models.WorkPackage.owner_id == user_id).all()


def get_project_detail(db, project_id):
    """读取项目及进度统计所需关联。"""
    return (
        db.query(models.Project)
        .options(
            selectinload(models.Project.owner),
            selectinload(models.Project.tech_owner),
            selectinload(models.Project.work_packages).selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
        )
        .filter(models.Project.id == project_id)
        .first()
    )


def get_project(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.Project).filter(models.Project.id == entry_id).first()


def get_package(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.WorkPackage).filter(models.WorkPackage.id == entry_id).first()


def list_package_items(db, work_package_id, owner_id=None, show_completed=True, show_related=False):
    """读取工作项；提供 owner_id 时只查询该负责人。"""
    query = db.query(models.WorkItem).filter(models.WorkItem.work_package_id == work_package_id)
    if owner_id is not None:
        query = query.filter(personal_item_condition(owner_id, show_completed, show_related))
    if not show_completed:
        query = query.filter(models.WorkItem.complete_status.isnot(True))
    return (
        query.options(
            selectinload(models.WorkItem.owner),
            selectinload(models.WorkItem.tech_owner),
            selectinload(models.WorkItem.monthly_scores),
        )
        .filter(models.WorkItem.work_package_id == work_package_id)
        .order_by(models.WorkItem.id)
        .all()
    )


def list_item_scores_in_month(db, item_ids, cur_month):
    """读取指定月份的工作项分值。"""
    return (
        db.query(models.WorkItemMonthlyScore)
        .filter(
            models.WorkItemMonthlyScore.work_item_id.in_(item_ids),
            models.WorkItemMonthlyScore.month == cur_month,
        )
        .all()
    )


def list_item_scores(db, item_ids):
    """读取工作项全部月度分值。"""
    return (
        db.query(models.WorkItemMonthlyScore)
        .filter(models.WorkItemMonthlyScore.work_item_id.in_(item_ids))
        .all()
    )


def list_items_by_ids(db, item_ids):
    """按主键集合查询工作项。"""
    return db.query(models.WorkItem).filter(models.WorkItem.id.in_(item_ids)).all()


def list_pending_completion_reviews(db, item_ids):
    """读取工作项待审核完成申请。"""
    return (
        db.query(models.WorkItemCompletionReview)
        .filter(
            models.WorkItemCompletionReview.work_item_id.in_(item_ids),
            models.WorkItemCompletionReview.status == 'PENDING',
        )
        .all()
    )


def get_item_with_scores(db, work_item_id):
    """读取待删除工作项及其月度分值。"""
    return (
        db.query(models.WorkItem)
        .options(selectinload(models.WorkItem.monthly_scores))
        .filter(models.WorkItem.id == work_item_id)
        .first()
    )


def list_pending_split_requests(db, package_id):
    """查询工作包待审批的变更申请。"""
    return (
        db.query(models.WorkPackageSplitRequest)
        .filter(
            models.WorkPackageSplitRequest.work_package_id == package_id,
            models.WorkPackageSplitRequest.status.in_(['PENDING', 'SUBMITTED']),
        )
        .all()
    )


def get_pending_completion_review(db, work_item_id):
    """查询待审核完成申请。"""
    return (
        db.query(models.WorkItemCompletionReview)
        .filter(
            models.WorkItemCompletionReview.work_item_id == work_item_id,
            models.WorkItemCompletionReview.status == 'PENDING',
        )
        .first()
    )


def delete_completion_reviews(db, work_item_id):
    """清理工作项完成申请，不提交事务。"""
    return (
        db.query(models.WorkItemCompletionReview)
        .filter(models.WorkItemCompletionReview.work_item_id == work_item_id)
        .delete(synchronize_session=False)
    )


def get_user(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.User).filter(models.User.id == entry_id).first()


def get_item(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.WorkItem).filter(models.WorkItem.id == entry_id).first()


def add(db, entity):
    """登记数据变更，由业务层统一提交或回滚事务。"""
    db.add(entity)


def delete(db, entity):
    """登记数据变更，由业务层统一提交或回滚事务。"""
    db.delete(entity)
