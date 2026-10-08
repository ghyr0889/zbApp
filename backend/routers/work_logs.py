"""接口层：只接收参数、注入数据库会话并调用业务层。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import ConfirmCompletionIn, ConfirmClosed
from services import work_logs_service as service

router = APIRouter(prefix='/api/v1/work-logs', tags=['Work Logs'])


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
                              db: Session = Depends(get_db)):
    """我的工作：当前用户负责的工作包（分页 + 进度统计）。"""
    return service.get_my_work_packages_paged(user_id=user_id, page=page, page_size=page_size, db=db)


@router.get("/work-packages/{work_package_id}/work-items")
def get_work_items(work_package_id: str, month: str = None, db: Session = Depends(get_db)):
    """查询某个工作包下的全部工作项（含指定月份的分值，默认当月，供工作项页面使用）。"""
    return service.get_work_items(work_package_id=work_package_id, month=month, db=db)


@router.delete("/work-items/{work_item_id}")
def delete_work_item(work_item_id: int, db: Session = Depends(get_db)):
    """删除工作项。"""
    return service.delete_work_item(work_item_id=work_item_id, db=db)


@router.put("/confirm-completion")
def confirm_completion(data: ConfirmCompletionIn, db: Session = Depends(get_db)):
    """确认/取消完成。

    - 工作项：改为“提交完成申请 / 撤回申请”，由技术负责人在 complete_review 里审核，
      审核通过后才置 complete_status 并写 completed_at。
    - 工作包 / 项目：仍是负责人（或领导/管理员）直接手动确认。
    """
    return service.confirm_completion(data=data, db=db)


@router.put("/confirm-closed")
def confirm_closed(data: ConfirmClosed, db: Session = Depends(get_db)):
    """确认关闭：或领导/管理员可操作。"""
    return service.confirm_closed(data=data, db=db)
