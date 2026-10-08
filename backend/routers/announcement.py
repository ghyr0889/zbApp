# 公告板
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import AnnouncementCreate, AnnouncementOut
from services import announcement_service
from dependencies import get_current_user

router = APIRouter( prefix="/api/v1/announcements",tags=["公告板"])

# 新建公告
@router.post("", response_model=AnnouncementOut, status_code=201)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return announcement_service.create_announcement( db=db, payload=payload, current_user=current_user, )


# 发布公告
@router.post( "/{announcement_id}/publish", response_model=AnnouncementOut,)
def publish_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return announcement_service.publish_announcement(
        db,
        announcement_id,
        current_user,
    )

# 获取收到的公告列表
@router.get("")
def list_received(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "code": 200,
        "data": announcement_service.list_received(
            db,
            current_user,
            page,
            page_size,
        ),
    }


# 查询本人创建的公告
@router.get("/mine")
def list_my_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "code": 200,
        "data": announcement_service.list_my_announcements(
            db=db,
            current_user=current_user,
            page=page,
            page_size=page_size,
        ),
    }


# 撤回一条已发布公告
@router.post("/{announcement_id}/withdraw", response_model=AnnouncementOut,)
def withdraw_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return announcement_service.withdraw_announcement(
        db=db,
        announcement_id=announcement_id,
        current_user=current_user,
    )


# 查询自己创建的草稿、已发布和已撤回公告
@router.get("/{announcement_id}")
def get_announcement_detail(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
): 
    return announcement_service.get_announcement_detail(
    db,
    announcement_id,
    current_user,
)
