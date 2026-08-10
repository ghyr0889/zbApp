# xiangmu/backend/schemas.py
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., description="工号 / 用户 ID")
    password: str = Field(..., description="登录密码")


class UserCreate(BaseModel):
    id: str = Field(..., description="工号")
    username: str = Field(..., description="姓名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色：EMPLOYEE / OWNER / ADMIN")


class ProjectCreate(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="项目名称")
    owner_id: Optional[str] = Field(None, description="项目负责人 ID")
    category: Optional[str] = Field(None, description="项目类别")
    level: Optional[str] = Field("C", description="项目级别：A/B/C/D（可扩展）")


class WorkPackageCreate(BaseModel):
    """创建/更新工作包。
    工作包本身在数据库中不再存 分值/截止节点（已下沉到工作项 WorkItem），
    但前端仍在工作包层面维护 score / deadline，后端负责：
    - 保存：写入工作包下第一个工作项（若无工作项则自动创建“默认工作项”承载）
    - 读取：从工作项聚合出工作包分值（各工作项分值之和）与最早截止节点
    """
    work_package_id: Optional[str] = Field(None, description="工作包 ID，新增时为空，修改时传入")
    project_id: Optional[int] = Field(None, description="所属项目 ID")
    project_name: Optional[str] = Field(None, description="所属项目名称（兼容前端）")
    category_name: str = Field(..., description="工作类型：类型1-4")
    owner_id: Optional[str] = Field(None, description="工作包负责人 ID")
    objective: Optional[str] = Field(None, description="工作目标")
    next_step_work: Optional[str] = Field(None, description="下一阶段工作")


class WorkItemCreate(BaseModel):
    """创建/更新工作项。"""
    work_item_id: Optional[int] = Field(None, description="工作项 ID，新增时为空，修改时传入")
    work_package_id: str = Field(..., description="所属工作包 ID")
    name: str = Field(..., description="工作项名称")
    standard: Optional[str] = Field(None, description="工作项完成标准")
    difficulty: Optional[str] = Field(None, description="工作项难度")
    importance: Optional[str] = Field(None, description="工作项重要性")
    innovation: Optional[str] = Field(None, description="工作项创新性")
    deadline: Optional[str] = Field(None, description="完成节点要求（YYYY-MM-DD）")
    score: Optional[float] = Field(0.0, description="分值（可选，若不传则按默认分值计算）")
    category: Optional[str] = Field(None, description="工作类型")


# class LogCreate(BaseModel):
#     """提交工作日志。支持按工作项(work_item_id)或按工作包(work_package_id)提交。"""
#     user_id: str = Field(..., description="提交员工 ID")
#     work_item_id: Optional[int] = Field(None, description="工作项 ID")
#     work_package_id: Optional[str] = Field(None, description="工作包 ID（兼容旧接口，自动取其默认工作项）")
#     base_score: Optional[float] = Field(0.0, description="基础分值，为空时取工作项分值")


class ReviewDecision(BaseModel):
    reviewer_id: str = Field(..., description="审核人 ID")
    approved: bool = Field(..., description="True 通过，False 驳回")
    remark: Optional[str] = Field("", description="审核意见/驳回原因")
    weight: float = Field(1.0, description="分值权重，如 1.2 表示加 20%")
    decision: Optional[str] = Field(None, description="兼容前端 'pass' 字样，可忽略")


class ReviewApprove(BaseModel):
    """备用审核通过接口的请求体。"""
    weight: float = Field(1.0, description="分值权重")


# class TaskAssignCreate(BaseModel):
#     assigner_id: str = Field(..., description="指派人（项目负责人）ID")
#     assignee_id: str = Field(..., description="被指派员工 ID")
#     work_package_id: str = Field(..., description="工作包 ID")


class TransferCreate(BaseModel):
    task_id: Optional[str] = Field(None, description="任务分配记录 ID（兼容，可空）")
    work_package_id: str = Field(..., description="工作包 ID")
    from_user_id: str = Field(..., description="发起人 ID（当前负责人）")
    to_user_id: str = Field(..., description="接收人 ID（新负责人）")
