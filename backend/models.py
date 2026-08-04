# xiangmu/backend/models.py
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Integer
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

    name = Column(String(100), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id])
    work_packages = relationship("WorkPackage", back_populates="project")


class WorkCategory(Base):
    __tablename__ = "work_categories"#工作类型表

    name = Column(String(100), primary_key=True, index=True)

    work_packages = relationship("WorkPackage", back_populates="category")


class WorkPackage(Base):
    __tablename__ = "work_packages" # 工作包表

    name = Column(String(100), primary_key=True, index=True)
    score = Column(Float, default=1.0)
    deadline = Column(Text, nullable=False)

    project_name = Column(String(100), ForeignKey("projects.name"), nullable=False)
    category_name = Column(String(100), ForeignKey("work_categories.name"), nullable=False)

    project = relationship("Project", back_populates="work_packages")
    category = relationship("WorkCategory", back_populates="work_packages")


class TaskAssignment(Base):
    __tablename__ = "task_assignments"# 任务分配表

    id = Column(String(50), primary_key=True, index=True) 
    assignee_id = Column(String(50), ForeignKey("users.id"), nullable=False) # 分配者id
    assigner_id = Column(String(50), ForeignKey("users.id"), nullable=False) # 被分配者id
    work_package_name = Column(String(100), ForeignKey("work_packages.name"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="IN_PROGRESS")# 状态

    assignee = relationship("User", foreign_keys=[assignee_id])
    assigner = relationship("User", foreign_keys=[assigner_id])
    work_package = relationship("WorkPackage")


class WorkLog(Base):
    __tablename__ = "work_logs"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    work_package_name = Column(String(100), ForeignKey("work_packages.name"), nullable=False)
    content = Column(Text, nullable=False) # 工作完成情况
    score_earned = Column(Float, default=0.0) # 通过后获得分值
    status = Column(String(20), default="PENDING")  # PENDING / APPROVED / REJECTED
    reviewer_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True) # 驳回/审核意见
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id], back_populates="submitted_logs")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviewed_logs")
    work_package = relationship("WorkPackage")


class TaskTransfer(Base):
    __tablename__ = "task_transfers"#工作转办表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(100), nullable=False, comment="任务名称")
    from_user_id = Column(String(50), nullable=False, comment="发起人(原负责人)")
    to_user_id = Column(String(50), nullable=False, comment="接收人(新负责人)")
    status = Column(String(20), default="PENDING", comment="状态: PENDING/ACCEPTED/REJECTED")
    created_at = Column(DateTime, default=datetime.now)