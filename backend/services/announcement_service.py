# backend/services/announcement_service.py

from datetime import datetime

from exceptions import BusinessError, PermissionDenied, NotFound
from repositories import announcement_repositories as repo


PUBLISH_ROLES = {"ADMIN", "LEADER"}

AUDIENCE_MODES = { "ALL","ROLE",}


def _check_publish_permission(current_user):
    if current_user.role not in PUBLISH_ROLES:
        raise PermissionDenied("当前用户没有发布公告的权限")


def _check_edit_permission(announcement, current_user):
    is_admin = current_user.role == "ADMIN"
    is_publisher = announcement.publisher_id == current_user.id

    if not (is_admin or is_publisher):
        raise PermissionDenied("只能管理自己发布的公告")


def _validate_content(title, content):
    if not title or not title.strip():
        raise BusinessError("公告标题不能为空")

    if not content or not content.strip():
        raise BusinessError("公告正文不能为空")


def _validate_audience(db, mode, roles):
    """校验发布范围，并返回去重后的角色。"""

    if mode not in AUDIENCE_MODES:
        raise BusinessError("不支持的公告发布范围")

    if roles is None:
        raise BusinessError("角色列表不能为 null，请使用 []")

    roles = list(dict.fromkeys(roles))

    needs_roles = mode in {"ROLE"}

    if needs_roles and not roles:
        raise BusinessError("请选择至少一个角色")
    if not needs_roles and roles:
        raise BusinessError("当前发布范围不需要角色列表")

    # 这些函数返回数据库中实际存在的角色编码。
    if roles:
        existing_roles = set(repo.find_existing_roles(db, roles))
        if set(roles) - existing_roles:
            raise BusinessError("所选角色不存在")

    return roles

def create_announcement(db, payload, current_user):
    """新建公告"""
    try:
        _check_publish_permission(current_user)
        _validate_content(payload.title, payload.content)
        roles = _validate_audience( db, payload.audience_mode, payload.roles )

        announcement = repo.create( db,
            {
                "title": payload.title.strip(),
                "content": payload.content,
                "audience_mode": payload.audience_mode,
                "is_pinned": payload.is_pinned,
                # 发布人从登录信息中获取
                "publisher_id": current_user.id,
            },
        )
        # 写入数据库以取得自增 ID，但此时还没有提交事务。
        db.flush()
        repo.replace_roles(db, announcement.id, roles)
        db.flush()
        # 在提交前构造普通字典，避免返回后依赖 ORM 延迟加载。
        result = repo.get_detail(db, announcement.id)
        # 公告、角色、部门关联一起提交。
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result


def publish_announcement(db, announcement_id, current_user):
    """发布公告"""
    try:
        announcement = repo.get_by_id(db, announcement_id)

        if announcement is None:
            raise NotFound("公告不存在")

        _check_publish_permission(current_user)
        _check_edit_permission(announcement, current_user)

        if announcement.status == "PUBLISHED":
            raise BusinessError("公告已经发布")

        _validate_content(announcement.title, announcement.content, )

        roles = repo.get_roles(db, announcement.id)

        _validate_audience(db, announcement.audience_mode, roles, )

        announcement.status = "PUBLISHED"
        announcement.published_at = datetime.now()

        db.flush()
        result = repo.get_detail(db, announcement.id)

        db.commit()
        return result

    except Exception:
        db.rollback()
        raise

def list_received(db, current_user, page=1, page_size=20):
    """获取我的公告列表"""
    return repo.list_received(
        db,
        current_user,
        page,
        page_size,
    )

def get_announcement_detail(db, announcement_id, current_user):
    """查看公告详情：先检查权限，再返回正文。"""
    announcement = repo.get_by_id(db, announcement_id)
    if announcement is None:
        raise NotFound("公告不存在或无权查看")

    # 管理员和发布者可以查看公告，用于管理草稿、已发布及已撤回记录。
    is_admin = current_user.role == "ADMIN"
    is_publisher = announcement.publisher_id == current_user.id
    if is_admin or is_publisher:
        return repo.get_detail(db, announcement.id)

    if announcement.status != "PUBLISHED":
        raise NotFound("公告不存在或无权查看")
    if announcement.status != "PUBLISHED":
        raise NotFound("公告不存在或无权查看")

    # 面向全员的公告：所有有效登录用户都可以查看。
    if announcement.audience_mode == "ALL":
        return repo.get_detail(db, announcement.id)

    # 面向指定角色的公告：当前用户角色必须在接收范围内。
    if announcement.audience_mode == "ROLE":
        allowed_roles = repo.get_roles(db, announcement.id)

        if current_user.role in allowed_roles:
            return repo.get_detail(db, announcement.id)

    # 角色不匹配或范围类型不支持时，不返回正文。
    raise NotFound("公告不存在或无权查看")

def list_my_announcements( db, current_user, page=1, page_size=20, ):
    """查询当前登录用户创建的公告。"""
    # 发布者 ID 来自已验证的登录用户，不接收前端任意指定的用户 ID。
    return repo.list_mine(
        db=db,
        publisher_id=current_user.id,
        page=page,
        page_size=page_size,
    )


def withdraw_announcement(db, announcement_id, current_user):
    """撤回已发布公告；保留数据库记录，不做物理删除。"""
    try:
        announcement = repo.get_by_id(db, announcement_id)
        if announcement is None:
            raise NotFound("公告不存在")
        # 复用现有管理权限：
        # 管理员可以管理所有公告，发布者可以管理自己的公告。
        _check_edit_permission(announcement, current_user)

        # 只有已经发布的公告才能撤回。
        # 草稿尚未公开，不需要撤回；已撤回记录不重复处理。
        if announcement.status != "PUBLISHED":
            raise BusinessError("只有已发布的公告才能撤回")

        announcement.status = "WITHDRAWN"
        db.flush()

        # 在提交前整理返回数据。
        result = repo.get_detail(db, announcement.id)
        db.commit()
        return result

    except Exception:
        db.rollback()
        raise