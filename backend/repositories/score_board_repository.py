"""数据访问层：封装查询和持久化操作，不决定业务权限，不提交事务。"""
from sqlalchemy import func
import models


def list_period_extra_scores(db, months):
    """查询指定月份集合内的月度附加分。"""
    extra_q = db.query(models.MonthlyExtraScore)
    if months:
        extra_q = extra_q.filter(models.MonthlyExtraScore.month.in_(months))
    extras = extra_q.all()

    return extras


def list_extra_scores(db, user_id, month):
    """按人员和月份查询附加分，空条件不限制。"""
    query = db.query(models.MonthlyExtraScore)
    if month:
        query = query.filter(models.MonthlyExtraScore.month == month)
    if user_id:
        query = query.filter(models.MonthlyExtraScore.user_id == user_id)
    rows = query.all()

    return rows


def package_filled_scores(db, months):
    """按工作包聚合指定周期内已填写的分值。"""
    filled_q = (db.query(
        models.WorkItem.work_package_id.label("wp_id"),
        func.coalesce(func.sum(models.WorkItemMonthlyScore.score), 0.0).label("filled_score"),
    ).join(models.WorkItem, models.WorkItem.id == models.WorkItemMonthlyScore.work_item_id)
        .group_by(models.WorkItem.work_package_id))
    if months is not None:
        filled_q = filled_q.filter(models.WorkItemMonthlyScore.month.in_(months))
    filled_pkg = {r.wp_id: float(r.filled_score or 0.0) for r in filled_q.all()}

    return filled_pkg


def list_items_for_project(db, target_id):
    """查询目标范围内的工作项及所属工作包。"""
    return (
        db.query(models.WorkItem, models.WorkPackage)
        .join(models.WorkPackage, models.WorkPackage.id == models.WorkItem.work_package_id)
        .filter(models.WorkPackage.project_id == target_id)
        .all()
    )


def list_items_for_category(db, category_name):
    """查询目标范围内的工作项及所属工作包。"""
    return (
        db.query(models.WorkItem, models.WorkPackage)
        .join(models.WorkPackage, models.WorkPackage.id == models.WorkItem.work_package_id)
        .filter(models.WorkPackage.category_name == category_name)
        .all()
    )


def list_item_month_scores(db, item_ids, month):
    """查询一组工作项的月度分值，可限定月份。"""
    fq = db.query(models.WorkItemMonthlyScore).filter(
        models.WorkItemMonthlyScore.work_item_id.in_(item_ids))
    if month:
        fq = fq.filter(models.WorkItemMonthlyScore.month == month)

    return fq.all()


def list_quality_scores_through_month(db, work_item_id, month):
    """读取截至指定月份的显式质量分，按月份倒序。"""
    return (
        db.query(models.WorkItemMonthlyScore)
        .filter(
            models.WorkItemMonthlyScore.work_item_id == work_item_id,
            models.WorkItemMonthlyScore.quality_score.isnot(None),
            models.WorkItemMonthlyScore.month <= month,
        )
        .order_by(models.WorkItemMonthlyScore.month.desc())
        .all()
    )


def list_dimension_levels(db):
    """读取积分计算系数。"""
    return db.query(models.ScoreDimensionLevel).all()


def list_user_month_scores(db, user_id):
    """读取人员月度分值。"""
    return (
        db.query(models.WorkItemMonthlyScore)
        .filter(models.WorkItemMonthlyScore.user_id == user_id)
        .all()
    )


def list_score_board_users(db):
    """读取积分看板人员，保留角色和停用过滤。"""
    return (
        db.query(models.User)
        .filter(models.User.role.notin_(['LEADER', 'ADMIN']), models.User.is_deleted.isnot(True))
        .all()
    )


def list_all_month_scores(db):
    """读取所有月度分值。"""
    return db.query(models.WorkItemMonthlyScore).all()


def get_user(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.User).filter(models.User.id == entry_id).first()


def get_item(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.WorkItem).filter(models.WorkItem.id == entry_id).first()


def get_month_score(db, work_item_id, month):
    """读取工作项指定月份分值。"""
    return (
        db.query(models.WorkItemMonthlyScore)
        .filter(
            models.WorkItemMonthlyScore.work_item_id == work_item_id,
            models.WorkItemMonthlyScore.month == month,
        )
        .first()
    )


def get_extra_score(db, user_id, month):
    """读取人员指定月份的附加分。"""
    return (
        db.query(models.MonthlyExtraScore)
        .filter(
            models.MonthlyExtraScore.user_id == user_id,
            models.MonthlyExtraScore.month == month,
        )
        .first()
    )


def get_project(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.Project).filter(models.Project.id == entry_id).first()


def list_users_by_ids(db, owner_ids):
    """读取负责人信息。"""
    return db.query(models.User).filter(models.User.id.in_(owner_ids)).all()


def package_score_totals(db):
    """按工作包聚合工作项数量和基础分值。"""
    return (
        db.query(
            models.WorkPackage.id.label('wp_id'),
            models.WorkPackage.project_id.label('project_id'),
            func.count(models.WorkItem.id).label('item_count'),
            func.coalesce(func.sum(models.WorkItem.score), 0.0).label('total_score'),
        )
        .outerjoin(models.WorkItem, models.WorkItem.work_package_id == models.WorkPackage.id)
        .group_by(models.WorkPackage.id, models.WorkPackage.project_id)
        .all()
    )


def list_projects(db):
    """按主键读取项目。"""
    return db.query(models.Project).order_by(models.Project.id).all()


def list_packages(db):
    """读取所有工作包。"""
    return db.query(models.WorkPackage).all()


def add(db, entity):
    """登记数据变更，由业务层统一提交或回滚事务。"""
    db.add(entity)
