from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., description="工号 / 用户 ID")
    password: str = Field(..., description="登录密码")


class UserCreate(BaseModel):
    id: str = Field(..., description="工号")
    username: str = Field(..., description="姓名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色")


class ProjectCreate(BaseModel):
    name: str = Field(..., description="项目名称")
    owner_id: Optional[str] = Field(None, description="项目负责人 ID")


class WorkPackageCreate(BaseModel):
    original_name: Optional[str] = Field(None, description="修改时的原工作包名称")
    name: str = Field(..., description="工作包名称")
    score: float = Field(..., description="基础积分")
    deadline: str = Field("", description="节点要求")
    node_requirement: Optional[str] = Field(None, description="旧字段兼容")
    project_name: str = Field(..., description="所属项目名称")
    category_name: str = Field(..., description="工作类型")
    assignee_id: Optional[str] = Field(None, description="负责员工 ID")
    owner_id: Optional[str] = Field(None, description="旧字段兼容")
    assigner_id: Optional[str] = Field(None, description="指派人 ID")


class TaskAssignCreate(BaseModel):
    assigner_id: str = Field(..., description="指派人 ID")
    assignee_id: str = Field(..., description="被指派员工 ID")
    work_package_name: str = Field(..., description="工作包名称")


class TransferCreate(BaseModel):
    task_id: str = Field(..., description="任务分配记录 ID")
    task_name: str = Field(..., description="工作包名称")
    from_user_id: str = Field(..., description="发起人 ID")
    to_user_id: str = Field(..., description="接收人 ID")


class LogCreate(BaseModel):
    user_id: str = Field(..., description="提交员工 ID")
    work_package_name: str = Field(..., description="工作包名称")
    score_earned: Optional[float] = Field(0.0, description="申请分值")


class WorkLogCreate(BaseModel):
    user_id: str = Field(..., description="提交员工 ID")
    project_name: str = Field(..., description="所属项目")
    work_package_name: str = Field(..., description="选中的工作包名称")
    log_date: str = Field(..., example="2026-07-27", description="工作日期")
    duration_hours: float = Field(..., gt=0, description="耗时（必须大于0）")
    content: str = Field(..., min_length=5, description="工作详细描述")
    applied_score: Optional[float] = Field(None, description="申请分值，选填")


class ReviewAction(BaseModel):
    reviewer_id: int = Field(..., description="审核人 OWNER ID")
    approved: bool = Field(..., description="True 通过，False 驳回")
    override_score: Optional[float] = Field(None, description="最终认定分值，选填")
    remark: Optional[str] = Field(None, description="审核意见/驳回原因")


class ReviewDecision(BaseModel):
    reviewer_id: str = Field(..., description="审核人 ID")
    approved: bool = Field(..., description="是否通过")
    remark: Optional[str] = Field("", description="审核意见/驳回原因")
    weight: float = Field(1.0, description="分值权重")


class WorkLogResponse(BaseModel):
    id: int
    log_date: str
    duration_hours: float
    content: str
    applied_score: float
    final_score: float
    status: str

class DeleteUser(BaseModel):
    id: str

    class Config:
        from_attributes = True
