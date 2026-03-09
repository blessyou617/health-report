from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.models import ReportStatus, PaymentStatus


# ============= User Schemas =============
class UserCreate(BaseModel):
    openid: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    openid: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Auth Schemas =============
class WeChatLoginRequest(BaseModel):
    code: str  # WeChat login code


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============= Report Schemas =============
class ReportUploadResponse(BaseModel):
    report_id: int
    file_url: str
    message: str


class QuestionnaireSubmit(BaseModel):
    questionnaire_data: str = Field(..., description="JSON string of questionnaire")


class AnalyzeReportResponse(BaseModel):
    report_id: int
    status: ReportStatus
    message: str



class ReportStatusResponse(BaseModel):
    report_id: int
    status: ReportStatus
    is_unlocked: bool
    error_message: Optional[str] = None


class ReportDetailResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    file_url: str
    report_text: Optional[str]
    questionnaire_data: Optional[str]
    analysis_result: Optional[str]
    analysis_error_message: Optional[str]
    status: ReportStatus
    is_unlocked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Q&A Schemas =============
class AskQuestionRequest(BaseModel):
    report_id: int
    question: str


class QAHistoryResponse(BaseModel):
    id: int
    report_id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class AskQuestionResponse(BaseModel):
    qa_id: int
    question: str
    answer: str
    message: str


# ============= TTS Schemas =============
class TTSRequest(BaseModel):
    text: str
    output_filename: Optional[str] = None


class TTSResponse(BaseModel):
    audio_url: str
    filename: str
    message: str


# ============= Payment Schemas =============
class CreatePaymentRequest(BaseModel):
    report_id: int


class CreatePaymentResponse(BaseModel):
    order_id: str
    prepay_id: str
    pay_params: dict
    amount: int


class PaymentStatusResponse(BaseModel):
    order_id: str
    status: PaymentStatus
    amount: int
    paid_at: Optional[datetime]
