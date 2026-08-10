# xiangmu/backend/models.py
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

FIXED_WORK_CATEGORIES = ["类型1", "类型2", "类型3", "类型4"]

class LogStatus(str, enum.Enum):
    PENDING = "PENGING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"#用户表

    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), default="123456", nullable=False)
    role = Column(String(20), default="EMPLOYEE")  # EMPLOYEE / OWNER / ADMIN

    submitted_logs = relationship("WorkLog", foreign_keys="WorkLog.user_id", back_populates="user")
    reviewed_logs = relationship("WorkLog", foreign_keys="WorkLog.reviewer_id", back_populates="reviewer")


class Project(Base):
    __tablename__ = "projects"#项目表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), index=True, nullable=False)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    level = Column(String(10), nullable=False, default="C")  # 项目级别: A/B/C/D（可扩展）
    category = Column(String(100), nullable=True)  # 项目类别

    owner = relationship("User", foreign_keys=[owner_id])
    work_packages = relationship("WorkPackage", back_populates="project")


class WorkProjectCategory(Base):
    __tablename__ = "work_project_categories"#工作包类别表

    name = Column(String(100), primary_key=True, index=True)

    work_packages = relationship("WorkPackage", back_populates="category")


class WorkPackage(Base):
    __tablename__ = "work_packages" # 工作包表

    id = Column(String(50), primary_key=True, index=True)  # 工作包ID为字符串，由业务方指定，不可自增
    next_step_work= Column(Text, nullable=True)  # 下阶段工作
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True)  # 工作包负责人
    objective = Column(Text, nullable=True)  # 工作目标

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category_name = Column(String(100), ForeignKey("work_project_categories.name"), nullable=False)

    project = relationship("Project", back_populates="work_packages")
    category = relationship("WorkProjectCategory", back_populates="work_packages")
    work_items = relationship("WorkItem", back_populates="work_package")
    owner = relationship("User", foreign_keys=[owner_id])  # 工作包负责人


class WorkItem(Base):
    __tablename__ = "work_items"  # 工作项表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 工作项名称
    standard = Column(Text, nullable=True)  # 工作项标准
    difficulty = Column(String(50), nullable=True)  # 工作项难度
    importance = Column(String(50), nullable=True)  # 工作项重要性
    innovation = Column(String(50), nullable=True)  # 工作项创新性
    deadline = Column(DateTime, nullable=True)  # 工作项完成节点要求
    score = Column(Float, default=0.0)  # 工作项分值
    category= Column(String(100), nullable=True)  # 工作项类别（冗余字段，便于查询）

    work_package_id = Column(String(50), ForeignKey("work_packages.id"), nullable=False)

    work_package = relationship("WorkPackage", back_populates="work_items")


class WorkLog(Base):
    __tablename__ = "work_logs"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False)
    base_score = Column(Float, default=0.0) # 基础分值
    status = Column(String(20), default="PENDING")  # PENDING / APPROVED / REJECTED
    reviewer_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True) # 驳回/审核意见
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id], back_populates="submitted_logs")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviewed_logs")
    work_item = relationship("WorkItem")


class TaskTransfer(Base):
    __tablename__ = "task_transfers"#工作转办表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_assignment_id = Column(String(50), nullable=False, comment="任务分配记录 ID")
    work_package_id = Column(String(50), ForeignKey("work_packages.id"), nullable=False)
    task_name = Column(String(100), nullable=False, comment="任务名称")
    from_user_id = Column(String(50), nullable=False, comment="发起人(原负责人)")
    to_user_id = Column(String(50), nullable=False, comment="接收人(新负责人)")
    status = Column(String(20), default="PENDING", comment="状态: PENDING/ACCEPTED/REJECTED")
    created_at = Column(DateTime, default=datetime.now)

    work_package = relationship("WorkPackage")
