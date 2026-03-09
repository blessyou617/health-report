from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
    summary = Column(Text, nullable=True)  # 免费摘要
    question_count = Column(Integer, default=0)  # Track Q&A usage
    qa_active = Column(Integer, default=1)  # 1 = can ask, 0 = reached limit
    status = Column(String(32), default=ReportStatus.PENDING.value)
    
    # Payment
    is_paid = Column(Boolean, default=False)  # 是否已支付
    paid_at = Column(DateTime, nullable=True)  # 支付时间
    order_id = Column(String(64), nullable=True)  # 订单号
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    qa_history = relationship("QAHistory", back_populates="report", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="report", uselist=False)


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    
    # Payment info
    order_id = Column(String(64), unique=True, index=True)  # 商户订单号
    transaction_id = Column(String(64), nullable=True)   # 微信订单号
    amount = Column(Integer, default=990)                  # 支付金额(分), 9.9元
    
    # Status
    status = Column(String(32), default="pending")  # pending/success/failed/closed
    
    # Payment method
    pay_type = Column(String(32), default="wechat")   # wechat/alipay
    
    # Timestamps
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
