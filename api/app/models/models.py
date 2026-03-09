from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUESTIONNAIRE_SUBMITTED = "questionnaire_submitted"
    ANALYZING = "analyzing"
    ANALYSIS_READY = "analysis_ready"
    ANALYSIS_FAILED = "analysis_failed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(128), unique=True, index=True, nullable=False)
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # File info
    file_name = Column(String(256), nullable=False)
    file_type = Column(String(32), nullable=False)  # pdf, jpg, png
    file_url = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)

    # Report content
    report_text = Column(Text, nullable=True)  # OCR extracted text
    questionnaire_data = Column(Text, nullable=True)  # JSON string

    # Analysis
    analysis_result = Column(Text, nullable=True)
    analysis_error_message = Column(Text, nullable=True)  # 分析失败原因
    summary = Column(Text, nullable=True)  # 免费摘要
    question_count = Column(Integer, default=0)  # Track Q&A usage
    qa_active = Column(Integer, default=1)  # 1 = can ask, 0 = reached limit
    status = Column(String(32), default=ReportStatus.UPLOADED.value, nullable=False)

    # Payment
    is_paid = Column(Boolean, default=False)  # 是否已支付（兼容旧逻辑）
    is_unlocked = Column(Boolean, default=False, nullable=False)  # 是否解锁完整报告
    paid_at = Column(DateTime, nullable=True)  # 支付时间
    order_id = Column(String(64), nullable=True)  # 订单号（报告维度）

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reports")
    qa_history = relationship("QAHistory", back_populates="report", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="report", uselist=False)


class Payment(Base):
    """支付记录表（唯一 ORM 定义）"""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)

    # Required normalized fields
    order_no = Column(String(64), unique=True, index=True, nullable=False)
    amount = Column(Integer, default=990, nullable=False)  # 分
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    provider = Column(String(32), default="wechat", nullable=False)
    provider_txn_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")
    report = relationship("Report", back_populates="payment", uselist=False)


class QAHistory(Base):
    __tablename__ = "qa_history"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="qa_history")
