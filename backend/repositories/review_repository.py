"""数据访问层：封装查询和持久化操作，不决定业务权限，不提交事务。"""
from sqlalchemy import case
import models


def list_split_requests(db, user_id, pending_status, show_all):
    """按可见范围查询申请，待处理优先、提交时间倒序。"""
    Request = models.WorkPackageSplitRequest
    query = db.query(Request)

    # 保留原来的查看范围
    if not show_all:
        query = query.filter(Request.applicant_id == user_id)

    requests = query.order_by(
        # 当前用户未处理的排最前面
        case(
            (Request.status == pending_status, 0),
            else_=1,
        ).asc(),
        # 每组内部按提交时间倒序
        Request.created_at.desc(),
        # 时间相同时保证顺序稳定
        Request.id.desc(),
    ).all()

    return requests


def get_user(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.User).filter(models.User.id == entry_id).first()


def get_package(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.WorkPackage).filter(models.WorkPackage.id == entry_id).first()


def get_item(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return db.query(models.WorkItem).filter(models.WorkItem.id == entry_id).first()


def get_split_request(db, entry_id):
    """按主键查询，找不到返回 None，业务层决定如何报错。"""
    return (
        db.query(models.WorkPackageSplitRequest)
        .filter(models.WorkPackageSplitRequest.id == entry_id)
        .first()
    )


def add(db, entity):
    """登记数据变更，由业务层统一提交或回滚事务。"""
    db.add(entity)
