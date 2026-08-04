#Pydantic校验模型
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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

class WorkLogResponse(BaseModel):
    id: int
    log_date: str
    duration_hours: float
    content: str
    applied_score: float
    final_score: float
    status: str

    class Config:
        from_attributes = True
