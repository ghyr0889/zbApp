# announcement 的数据连接层

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

import models


def create(db: Session, data: dict):
    """创建公告对象，事务由 service 层统一提交。"""
    announcement = models.Announcement(**data)
    db.add(announcement)
    return announcement


def get_by_id(db: Session, announcement_id: int):
    """查询公告 ORM 对象，不存在时返回 None。"""
    return (
        db.query(models.Announcement)
        .filter(models.Announcement.id == announcement_id)
        .first()
    )


def find_existing_roles(db: Session, roles: list[str]):
    """返回所选角色中，当前未删除用户实际使用的角色。"""
    if not roles:
        return []

    rows = (
        db.query(models.User.role)
        .filter(
            models.User.role.in_(roles),
            models.User.is_deleted == False,
        )
        .distinct()
        .all()
    )

    return [role for (role,) in rows]


def replace_roles(
    db: Session,
    announcement_id: int,
    roles: list[str],
):
    """删除公告原有角色关联，再写入新的角色列表。"""
    db.query(models.AnnouncementRole).filter(
        models.AnnouncementRole.announcement_id == announcement_id
    ).delete(synchronize_session=False)

    # 去重，避免违反公告 ID + 角色的唯一约束。
    unique_roles = list(dict.fromkeys(roles))

    db.add_all([
        models.AnnouncementRole(
            announcement_id=announcement_id,
            role=role,
        )
        for role in unique_roles
    ])


def get_roles(db: Session, announcement_id: int):
    """查询公告允许查看的角色列表。"""
    rows = (
        db.query(models.AnnouncementRole.role)
        .filter(
            models.AnnouncementRole.announcement_id == announcement_id
        )
        .order_by(models.AnnouncementRole.role)
        .all()
    )

    return [role for (role,) in rows]


def get_detail(db: Session, announcement_id: int):
    """返回普通字典；调用方负责检查查看权限。"""
    announcement = get_by_id(db, announcement_id)

    if announcement is None:
        return None

    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "publisher_id": announcement.publisher_id,
        "audience_mode": announcement.audience_mode,
        "status": announcement.status,
        "is_pinned": announcement.is_pinned,
        "published_at": announcement.published_at,
        "created_at": announcement.created_at,
        "roles": get_roles(db, announcement.id),
    }


def list_received(db, current_user, page=1, page_size=20):
    """ 获取公告列表 """
    Announcement = models.Announcement
    AnnouncementRole = models.AnnouncementRole

    role_matches = ( db.query(AnnouncementRole.id).filter(
            AnnouncementRole.announcement_id == Announcement.id,
            AnnouncementRole.role == current_user.role, ).exists() )

    query = db.query(Announcement).filter(
        Announcement.status == "PUBLISHED", or_( Announcement.audience_mode == "ALL",
            and_( Announcement.audience_mode == "ROLE", role_matches, ), ), )

    total = query.count()

    items = (query.order_by(
            Announcement.is_pinned.desc(),
            Announcement.published_at.desc(),
            Announcement.id.desc(),
        ).offset((page - 1) * page_size).limit(page_size) .all()
    )

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "publisher_id": item.publisher_id,
                "is_pinned": item.is_pinned,
                "published_at": item.published_at,
            }
            for item in items
        ],
    }


def list_mine(
    db: Session,
    publisher_id: str,
    page: int = 1,
    page_size: int = 20,
):
    """分页查询某位发布者创建的全部公告，包括草稿和已撤回记录。"""
    Announcement = models.Announcement
    # 只按发布者筛选，不限制为 PUBLISHED。
    # 否则创建的草稿和撤回的公告就无法在管理页面找到。
    query = db.query(Announcement).filter(
        Announcement.publisher_id == publisher_id
    )

    # 分页前统计总数，供前端分页组件使用。
    total = query.count()

    items = (query.order_by( # “我的公告”侧重管理，默认把最近创建的记录放在前面。
            Announcement.created_at.desc(),
            Announcement.id.desc(),
        ).offset((page - 1) * page_size).limit(page_size).all()
    )

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "publisher_id": item.publisher_id,
                "audience_mode": item.audience_mode,
                "status": item.status,
                "is_pinned": item.is_pinned,
                "created_at": item.created_at,
                "published_at": item.published_at,
            }
            for item in items
        ],
    }
    