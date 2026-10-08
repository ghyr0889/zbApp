# xiangmu/backend/models.py
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Integer, UniqueConstraint,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class WorkTimeSession(Base):
    """一次个人计时。快照保留历史归属，工作项删除后仍可查询和结束计时。"""
    __tablename__ = "work_time_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True, index=True)
    original_item_id = Column(Integer, nullable=False, index=True) #工作项id历史备份
    work_item_name = Column(String(100), nullable=False)
    work_package_id = Column(Integer, nullable=False, index=True)
    work_package_name = Column(String(100), nullable=False)
    project_id = Column(Integer, nullable=False, index=True)
    project_name = Column(String(100), nullable=False)
    department = Column(String(255), nullable=False, default="")
    username = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="RUNNING")
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    total_seconds = Column(Float, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    # 非空时唯一，从数据库层保证每人最多一条未结束记录，结束时清空。
    active_user_id = Column(String(50), nullable=True, unique=True)
    # 同一次开始操作重试使用相同请求号，防止超时重试重复创建。
    request_key = Column(String(64), nullable=False)
    segments = relationship("WorkTimeSegment", back_populates="session", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("user_id", "request_key", name="uq_time_start_request"),)


class WorkTimeSegment(Base):
    """连续工作的时间段；保留旧版多段历史，所有时间按 UTC 保存。"""
    __tablename__ = "work_time_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("work_time_sessions.id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    # 一个会话最多一个开放时间段，结束时清空。
    open_session_id = Column(Integer, nullable=True, unique=True)
    session = relationship("WorkTimeSession", back_populates="segments")


class LogStatus(str, enum.Enum):
    PENDING = "PENGING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"#用户表

    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), default="123456", nullable=False)
    role = Column(String(20), default="EMPLOYEE")  # EMPLOYEE / DEPARTMENT / LEADER / ADMIN
    job_grade = Column(String(20), nullable=False)  # 职级（必填）
    department = Column(String(255), nullable=True) # 所属科室

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(10), nullable=True)


class Project(Base):
    __tablename__ = "projects"#项目表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), nullable = False) #项目编号
    name = Column(String(100), index=True, nullable=False)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    level = Column(String(10), nullable=False, default="C")  # 项目级别: A/B/C/D（可扩展）
    complete_status = Column(Boolean, default=False, nullable=True) # 完成状态
    category = Column(String(100), default=False,nullable=True)  # 项目类别
    tech_owner_id = Column(String(50),ForeignKey("users.id"),nullable=True) #机型主管/责任人
    isclosed = Column(Boolean, default=False, nullable=True) # 是否关闭

    owner = relationship("User", foreign_keys=[owner_id])
    tech_owner = relationship("User", foreign_keys=[tech_owner_id])
    work_packages = relationship("WorkPackage", back_populates="project", cascade="all, delete-orphan")


class Department(Base):
    """统一维护科室名称；人员仍沿用现有 department 字段，无需重建人员表。"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)


class WorkPackageCategory(Base):
    __tablename__ = "work_package_categories"#工作包类别表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100),nullable=False)

    work_packages = relationship("WorkPackage", back_populates="category")



class WorkPackage(Base):
    __tablename__ = "work_packages" # 工作包表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), nullable=False)  # 工作包ID为字符串，由业务方指定，不可自增
    name = Column(String(100),  nullable=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True)  # 工作包负责人
    objective = Column(Text, nullable=True)  # 工作目标
    complete_status = Column(Boolean, default=False, nullable=True) # 完成状态
    tech_owner_id = Column(String(50),ForeignKey("users.id"),nullable=True) #技术负责人
    isclosed = Column(Boolean, default=False, nullable=True) # 是否关闭

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category_name = Column(String(100), ForeignKey("work_package_categories.name"), nullable=False)
    

    project = relationship("Project", back_populates="work_packages")
    category = relationship("WorkPackageCategory", back_populates="work_packages")
    work_items = relationship("WorkItem", back_populates="work_package", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])  # 工作包负责人
    tech_owner = relationship("User", foreign_keys=[tech_owner_id])#技术负责人
    split_requests = relationship("WorkPackageSplitRequest", back_populates="work_package", cascade="all, delete-orphan")



class WorkItem(Base):
    __tablename__ = "work_items"  # 工作项表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 工作项名称
    standard = Column(Text, nullable=True)  # 工作项标准
    difficulty = Column(String(50), nullable=False)  # 工作项难度
    importance = Column(String(50), nullable=False)  # 工作项重要性
    innovation = Column(String(50), nullable=False)  # 工作项创新性
    deadline = Column(DateTime, nullable=False)  # 工作项完成节点要求
    completed_at = Column(DateTime, nullable=True) # 工作完成时间
    score = Column(Float, default=0.00, nullable=False)  # 工作项分值
    complete_status = Column(Boolean, default=False, nullable=True) # 完成状态
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True) #工作项负责人
    tech_owner_id = Column(String(50),ForeignKey("users.id"),nullable=False) #技术负责人
    notes = Column(Text, nullable=True) # 备注
    isclosed = Column(Boolean, default=False, nullable=True) # 是否关闭

    work_package_id = Column(Integer, ForeignKey("work_packages.id"), nullable=False)
    
    work_package = relationship("WorkPackage", back_populates="work_items")
    owner = relationship("User", foreign_keys=[owner_id])
    tech_owner = relationship("User", foreign_keys=[tech_owner_id])#技术负责人
    monthly_scores = relationship("WorkItemMonthlyScore", back_populates="work_item", cascade="all, delete-orphan")


class WorkItemCompletionReview(Base):
    """工作项完成确认审核：进度满/手动提交后，由工作项技术负责人审核。"""
    __tablename__ = "work_item_completion_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    applicant_id = Column(String(50), ForeignKey("users.id"), nullable=False)   # 提交人（负责人）
    reviewer_id  = Column(String(50), ForeignKey("users.id"), nullable=True)    # 技术负责人
    status       = Column(String(20), default="PENDING")   # PENDING / APPROVED / REJECTED
    reason       = Column(Text, nullable=True)             # 提交说明
    review_comment = Column(Text, nullable=True)           # 审核意见 / 驳回原因
    created_at   = Column(DateTime, default=datetime.now)
    reviewed_at  = Column(DateTime, nullable=True)         # = 审核通过时间

    work_item = relationship("WorkItem", foreign_keys=[work_item_id])
    applicant = relationship("User", foreign_keys=[applicant_id])
    reviewer  = relationship("User", foreign_keys=[reviewer_id])

class TaskTransfer(Base):
    __tablename__ = "task_transfers"#工作转办表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    work_package_id = Column(Integer, ForeignKey("work_packages.id"), nullable=False)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False) 
    transfer_score = Column(Float, default=0.00) #转移的分数
    from_user_id = Column(String(50), nullable=False, comment="发起人(原负责人)")
    to_user_id = Column(String(50), nullable=False, comment="接收人(新负责人)")
    status = Column(String(20), default="PENDING", comment="状态: PENDING/ACCEPTED/REJECTED")
    created_at = Column(DateTime, default=datetime.now)
    transfer_type = Column(String(20), default="work_item", nullable=False, comment="转移类型")

    work_package = relationship("WorkPackage")
    work_item = relationship("WorkItem")


class WorkPackageSplitRequest(Base):
    """工作包拆分申请：普通员工申请把工作包拆分为多个工作项，由领导/管理员审核。"""
    __tablename__ = "work_package_split_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    work_package_id = Column(Integer, ForeignKey("work_packages.id"), nullable=False)
    applicant_id = Column(String(50), ForeignKey("users.id"), nullable=False)  # 申请人
    reason = Column(Text, nullable=False)  # 拆分原因
    split_items = Column(Text, nullable=False)  # 拆分方案（JSON：工作项数组）
    status = Column(String(20), default="PENDING")  # PENDING / APPROVED / REJECTED
    reviewer_id = Column(String(50), ForeignKey("users.id"), nullable=True)  # 审核人
    review_comment = Column(Text, nullable=True)  # 审核意见 / 驳回原因
    created_at = Column(DateTime, default=datetime.now) # 提交原因
    reviewed_at = Column(DateTime, nullable=True)  # 审核时间

    work_package = relationship("WorkPackage", back_populates="split_requests")
    applicant = relationship("User", foreign_keys=[applicant_id])


class WorkItemMonthlyScore(Base):
    """工作项月度分值：员工每月自填、直接生效，作为积分面板唯一数据来源。"""
    __tablename__ = "work_item_monthly_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    month = Column(String(7), nullable=False, index=True)  # 哪个月
    score = Column(Float, default=0.00)  # 本月分值（基础得分）
    calculate_score = Column(Float, default=0.00, nullable=True) #计算得分
    quality_score = Column(Float, default=0.00, nullable=True) # 质量分
    quality_score_updated_at = Column(DateTime, nullable=True)  # 该月质量分填写时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("work_item_id", "month", name="uq_work_item_month"),
    ) #同一个工作项在同一个月里，只能有一条分数记录

    work_item = relationship("WorkItem", back_populates="monthly_scores")
    user = relationship("User")


class ScoreDimensionLevel(Base):
    """计算得分 - 各维度档位系数表（管理员配置各档位系数）。"""
    __tablename__ = "score_dimension_levels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    variable = Column(String(50), nullable=False)  # 变量（difficulty / innovation / importance）
    level = Column(String(50), nullable=False)    # 档位
    factor = Column(Float, default=1.00)                 # 该档位系数
    job_grade = Column(String(50))   # 职级值：P1-P4（创新度可为空）


class MonthlyExtraScore(Base):
    """人员月附加分"""
    __tablename__ = "monthly_extra_score"

    id = Column(Integer,primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False) 
    patent_score = Column(Float, default=0.00, nullable=True) # 专利分，属于技术提升
    knowledge_score = Column(Float, default=0.00, nullable=True) # 知识库得分，属于技术提升
    train_score = Column(Float, default=0.00, nullable=True) # 培训得分，数据技术提升
    deduct_score = Column(Float, default=0.00, nullable=True) # 扣分，属于日常管理
    quality_event_score = Column(Float, default=0.00, nullable=True) # 质量事件得分，属于日常管理
    carrier_inspection_score = Column(Float, default=0.00, nullable=True) # 载体检查得分，属于日常管理
    updated_by_id = Column(String(50), ForeignKey("users.id"), nullable=False) # 填写人id
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    # + 唯一约束 (user_id, month)
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_user_month"),)

    user = relationship("User", foreign_keys=[user_id])


class ScoreLevelDef(Base):
    """计算得分 - 档位字典表（管理员维护职级、难度、重要度、创新度的档位定义）。"""
    __tablename__ = "score_level_defs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # job_grade / difficulty / importance / innovation
    name = Column(String(50), nullable=False)                  # 档位名称，如 P1 / Ⅰ级 / 无
    sort_order = Column(Integer, default=0)                    # 显示顺序
    is_active = Column(Integer, default=1)                     # 是否启用

    __table_args__ = (UniqueConstraint("category", "name", name="uq_def_category_name"),)


class Announcement(Base):
    """公告 主表"""
    __tablename__ = "announcement"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False) #标题
    content = Column(Text, nullable=False) #正文
    publisher_id = Column(String(50), ForeignKey("users.id"), nullable=False) # 发布人id
    audience_mode = Column(String(30),default="all", nullable=False) # 可见范围
    status = Column(String(20), default="DRAFT") # 状态 草稿DRAFT，已发布PUNLISHED，已撤回WITHRAWN
    is_pinned = Column(Boolean, default=False) # 是否置顶 TRUE为置顶
    published_at = Column(DateTime, nullable=True) # 发布时间
    created_at = Column(DateTime, default=datetime.now, nullable=True) # 创建时间


class AnnouncementRole(Base):
    """ 公告角色表 """
    __tablename__ = "announcement-role"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    announcement_id = Column(Integer, ForeignKey("announcement.id"), nullable=False)
    role = Column(String(20), nullable=True)

    __table_args__ = (UniqueConstraint( "announcement_id", "role",name="uq_announcement_role"),)


class LoginSession(Base):
    """登录会话表：一条记录对应一次登录，退出时删除对应记录。"""
    __tablename__ = "login_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column( String(50), ForeignKey("users.id"), nullable=False, index=True, )
    # 只保存原始令牌的 SHA-256 哈希，原始令牌仅在登录成功时返回前端。
    token_hash = Column( String(64),unique=True, nullable=False, index=True, )
    expires_at = Column(DateTime, nullable=False)  # UTC 到期时间，与签发和验证逻辑一致。
