# xiangmu/backend/schemas.py
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., description="工号 / 用户 ID")
    password: str = Field(..., description="登录密码")


class ChangePasswordRequest(BaseModel):
    user_id: str = Field(..., description="当前登录用户 ID")
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")


class ConfirmCompletionIn(BaseModel):
    target_type: str = Field(..., description="目标类型：work_item / work_package / project")
    target_id: int = Field(..., description="目标 ID（工作包为字符串，其余为数字字符串）")
    user_id: str = Field(..., description="操作人 ID")
    confirmed: bool = Field(True, description="True=确认完成，False=取消完成")


class UserCreate(BaseModel):
    id: str = Field(..., description="工号")
    username: str = Field(..., description="姓名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色：EMPLOYEE / LEADER / ADMIN / DEPARTMENT")
    job_grade: str = Field(..., description="工号级别: P1/P2/P3/P4")

class UserUpdate(BaseModel):
    updated_by_id: str = Field(..., description="修改人工号")
    username: str = Field(..., description="姓名")
    role: str = Field(..., description="角色：EMPLOYEE / LEADER / ADMIN / DEPARTMENT")
    job_grade: str = Field(..., description="工号级别: P1/P2/P3/P4")

class ProjectCreate(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="项目名称")
    code: str = Field(..., description="项目编号")
    owner_id: Optional[str] = Field(None, description="项目负责人 ID")
    tech_owner_id: Optional[str] = Field(None, description="机型主管/责任人 ID")
    category: Optional[str] = Field(None, description="项目类别")
    level: Optional[str] = Field("C", description="项目级别：A/B/C/D（可扩展）")


class WorkPackageCreate(BaseModel):
    """创建/更新工作包。 """
    id: Optional[int] = None
    work_package_code: str = Field(None, description="工作包code")
    project_id: Optional[int] = Field(None, description="所属项目 ID")
    project_name: Optional[str] = Field(None, description="所属项目名称（兼容前端）")
    project_code:Optional[str] = Field(None, description="所属项目编号（兼容前端）")
    category_name: str = Field(..., description="工作类型：类型1-4")
    owner_id: Optional[str] = Field(None, description="工作包负责人 ID")
    objective: Optional[str] = Field(None, description="工作目标")


class WorkItemCreate(BaseModel):
    """创建/更新工作项。"""
    work_item_id: Optional[int] = Field(None, description="工作项 ID，新增时为空，修改时传入")
    work_package_id: int = Field(..., description="所属工作包 ID")
    name: str = Field(..., description="工作项名称")
    standard: Optional[str] = Field(None, description="工作项完成标准")
    difficulty: Optional[str] = Field(None, description="工作项难度")
    importance: Optional[str] = Field(None, description="工作项重要性")
    innovation: Optional[str] = Field(None, description="工作项创新性")
    deadline: Optional[str] = Field(None, description="完成节点要求（YYYY-MM-DD）")
    score: Optional[float] = Field(0.0, description="分值（可选，若不传则按默认分值计算）")
    category: Optional[str] = Field(None, description="工作类型")


class MonthScoreIn(BaseModel):
    """保存工作项本月分值（员工直接填写、直接生效，不经过审核）。"""
    user_id: str = Field(..., description="填写人（员工）ID")
    month: str = Field(..., description="月份 YYYY-MM")
    score: Optional[float] = Field(0.0, description="本月分值")
    quality_score: Optional[float] = Field(0.0,description="该项目质量分")


class MonthlyExtraScoreIn(BaseModel):
    """领导按月为人员设置 技术提升/日常管理 附加分。"""
    user_id: str = Field(..., description="人员 ID")
    month: str = Field(..., description="月份 YYYY-MM")
    updated_by_id: str = Field(..., description="填写人（领导）ID")
    patent_score: Optional[float] = Field(0.0, description="专利分（技术提升）")
    knowledge_score: Optional[float] = Field(0.0, description="知识库得分（技术提升）")
    train_score: Optional[float] = Field(0.0, description="培训得分（技术提升）")
    deduct_score: Optional[float] = Field(0.0, description="扣分（日常管理）")
    quality_event_score: Optional[float] = Field(0.0, description="质量事件得分（日常管理）")
    carrier_inspection_score: Optional[float] = Field(0.0, description="载体检查得分（日常管理）")


class LevelDefsUpdate(BaseModel):
    """管理员维护 职级/难度/重要度/创新度 档位定义。"""
    user_id: str = Field(..., description="操作人（管理员）ID")
    job_grade: list[str] = Field(..., description="职级列表")
    difficulty: list[str] = Field(..., description="难度档位列表")
    importance: list[str] = Field(..., description="重要度档位列表")
    innovation: list[str] = Field(..., description="创新度档位列表")


class SplitItemIn(BaseModel):
    """申请中携带的一个工作项（新增或编辑）。"""
    work_item_id: Optional[int] = Field(None, description="工作项 ID（编辑时传入；新增时为空）")
    name: str = Field(..., description="工作项名称")
    standard: Optional[str] = Field(None, description="完成标准")
    difficulty: Optional[str] = Field(None, description="难度")
    importance: Optional[str] = Field(None, description="重要性")
    innovation: Optional[str] = Field(None, description="创新性")
    deadline: Optional[str] = Field(None, description="截止节点（YYYY-MM-DD）")
    score: Optional[float] = Field(0.0, description="分值")
    category: Optional[str] = Field(None, description="类别")


class SplitRequestCreate(BaseModel):
    """提交工作包拆分申请。"""
    applicant_id: str = Field(..., description="申请人 ID")
    work_package_id: int = Field(..., description="被拆分的工作包 ID")
    reason: str = Field(..., description="拆分原因")
    split_items: list[SplitItemIn] = Field(..., description="拆分出的工作项列表")


class SplitRequestReview(BaseModel):
    """审核拆分申请。"""
    reviewer_id: str = Field(..., description="审核人 ID")
    action: str = "APPROVE"  #  # APPROVE=同意 / REJECT=驳回 / SUBMIT=提交给领导
    comment: str = Field("", description="审核意见 / 驳回原因（驳回必填）")



class TransferCreate(BaseModel):
    task_id: Optional[str] = Field(None, description="任务分配记录 ID（兼容，可空）")
    work_package_id: int = Field(..., description="工作包 ID")
    from_user_id: str = Field(..., description="发起人 ID（当前负责人）")
    to_user_id: str = Field(..., description="接收人 ID（新负责人）")


class TaskAssignCreate(BaseModel):
    """工作包指派（负责人把工作包指派给员工）。"""
    assigner_id: str = Field(..., description="指派人（项目负责人）ID")
    assignee_id: str = Field(..., description="被指派员工 ID")
    work_package_id: int = Field(..., description="工作包 ID")


class ScoreLevelFactorIn(BaseModel):
    """单个档位的系数。"""
    job_grade: Optional[str] = Field("", description="职级 P1-P4（创新度可为空）")
    level: str = Field(..., description="档位值，如 P1 / 无 / Ⅰ级")
    factor: float = Field(0.0, description="该档位系数")


class ScoreDimensionItemIn(BaseModel):
    """单个评分维度的档位系数。"""
    variable: str = Field(..., description="difficulty / innovation / importance")
    levels: list[ScoreLevelFactorIn] = Field([], description="该维度下各档位系数")


class ScoreRuleUpdate(BaseModel):
    """管理员保存评分维度权重与档位系数。"""
    user_id: str = Field(..., description="操作人 ID")
    items: list[ScoreDimensionItemIn] = Field(..., description="维度权重与档位系数列表")
