from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import json
import os
from app.core.database import get_db
from app.core.config import settings
from app.models import User, Report, QAHistory, ReportStatus
from app.models.schemas import (
    WeChatLoginRequest, AuthResponse, UserResponse,
    ReportUploadResponse, QuestionnaireSubmit, AnalyzeReportResponse, ReportDetailResponse, ReportStatusResponse,
    AskQuestionRequest, AskQuestionResponse, QAHistoryResponse
)
from app.services import wechat_service, ai_service, file_service
from app.core.security import create_access_token, verify_token


router = APIRouter()


# ============= Dependency =============

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ============= Auth Routes =============

@router.post("/auth/login", response_model=AuthResponse)
async def login(
    request: WeChatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    WeChat login - get openid and create/return user
    """
    try:
        # Get openid from WeChat
        wechat_data = await wechat_service.get_openid(request.code)
        openid = wechat_data["openid"]
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.openid == openid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(openid=openid)
            db.add(user)
            await db.flush()
            await db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


# ============= Report Routes =============

@router.post("/upload/report", response_model=ReportUploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # TODO: Add auth dependency
):
    """
    Upload health report file (PDF/JPG/PNG)
    """
    try:
        # Save file
        file_info = await file_service.save_file(file)
        
        # Create report record
        report = Report(
            user_id=current_user.id,
            file_name=file_info["original_filename"],
            file_type=file_info["file_type"],
            file_url=file_info["file_url"],
            file_size=file_info["file_size"],
            status=ReportStatus.UPLOADED.value
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        
        return ReportUploadResponse(
            report_id=report.id,
            file_url=file_info["file_url"],
            message="Report uploaded successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/questionnaire/submit")
async def submit_questionnaire(
    report_id: int,
    request: QuestionnaireSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit lifestyle questionnaire
    """
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    if report.status == ReportStatus.ANALYZING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is currently analyzing"
        )

    report.questionnaire_data = request.questionnaire_data
    report.status = ReportStatus.QUESTIONNAIRE_SUBMITTED.value
    await db.flush()
    
    return {"message": "Questionnaire submitted successfully"}


@router.post("/analyze/report/{report_id}", response_model=AnalyzeReportResponse)
async def analyze_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger AI analysis for the report
    """
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    if report.status == ReportStatus.ANALYZING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already being analyzed"
        )

    # Update status
    report.status = ReportStatus.ANALYZING.value
    report.analysis_error_message = None
    await db.flush()
    
    try:
        # Get local file path
        import os
        file_path = os.path.join(settings.UPLOAD_DIR, report.file_name)
        
        # Parse questionnaire data
        questionnaire = None
        if report.questionnaire_data:
            try:
                questionnaire = json.loads(report.questionnaire_data)
            except:
                pass
        
        # Call AI service to analyze file directly
        analysis_result = await ai_service.analyze_report_with_file(
            file_path=file_path,
            file_type=report.file_type,
            questionnaire_data=questionnaire
        )
        
        # Convert result to JSON string for storage
        analysis_text = json.dumps(analysis_result, ensure_ascii=False, indent=2)
        
        # Update report
        report.analysis_result = analysis_text
        report.analysis_error_message = None
        report.status = ReportStatus.ANALYSIS_READY.value
        
        return AnalyzeReportResponse(
            report_id=report_id,
            status=ReportStatus.ANALYSIS_READY,
            message="Analysis completed successfully"
        )
        
    except Exception as e:
        report.status = ReportStatus.ANALYSIS_FAILED.value
        report.analysis_error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/report/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get report details by ID
    """
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportDetailResponse.model_validate(report)


@router.get("/report/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report analysis status for polling."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    return ReportStatusResponse(
        report_id=report.id,
        status=ReportStatus(report.status),
        is_unlocked=report.is_unlocked,
        error_message=report.analysis_error_message,
    )


# ============= Q&A Routes =============

from app.models.schemas import AskQuestionRequest, QAHistoryResponse, AskQuestionResponse
from app.services import qa_service


@router.post("/qa/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ask follow-up question about the report (max 2 questions per report)
    """
    # 1) Report existence + ownership
    result = await db.execute(
        select(Report).where(
            Report.id == request.report_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied",
        )

    # 2) Unlock check
    if not report.is_unlocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report is locked. Please complete payment first.",
        )

    # 3) Analysis readiness check
    if not report.analysis_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please analyze the report first",
        )

    # 4) Strong backend limit check (source of truth: persisted qa_history count)
    check_result = await qa_service.check_question_limit(db, request.report_id)
    if not check_result["can_ask"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=check_result["message"],
        )

    history = await qa_service.get_qa_history(db, request.report_id)

    try:
        # Include report summary + questionnaire + historical QA context
        answer_result = await qa_service.answer_question(
            question=request.question,
            analysis_result=report.analysis_result,
            questionnaire_data=report.questionnaire_data,
            qa_history=history,
        )
        answer = answer_result["answer"]

        qa = QAHistory(
            report_id=request.report_id,
            question=request.question,
            answer=answer,
        )
        db.add(qa)
        await db.flush()
        await db.refresh(qa)

        # keep denormalized counter in sync with persisted history
        await qa_service.sync_question_count(db, report)

        return AskQuestionResponse(
            qa_id=qa.id,
            question=request.question,
            answer=answer,
            message=f"Question accepted. {check_result['remaining'] - 1} question(s) remaining",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )


@router.get("/qa/status/{report_id}")
async def get_qa_status(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Q&A status for a report"""
    # Check report ownership
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    check_result = await qa_service.check_question_limit(db, report_id)
    
    qa_result = await db.execute(
        select(QAHistory).where(QAHistory.report_id == report_id)
    )
    qa_history = qa_result.scalars().all()
    
    return {
        "report_id": report_id,
        "can_ask": check_result["can_ask"],
        "remaining": check_result["remaining"],
        "question_count": check_result["count"],
        "history": [
            {
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "created_at": qa.created_at.isoformat()
            }
            for qa in qa_history
        ]
    }


# ============= TTS Routes =============

from app.models.schemas import TTSRequest, TTSResponse
from app.services import tts_service


@router.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate TTS audio from text
    """
    try:
        result = await tts_service.generate_tts(
            text=request.text,
            output_filename=request.output_filename
        )
        
        return TTSResponse(
            audio_url=result["audio_url"],
            filename=result["filename"],
            message="TTS generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.post("/tts/report/{report_id}")
async def generate_report_tts(
    report_id: int,
    include_advice: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate TTS for health report analysis
    """
    # Get report
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if not report.analysis_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please analyze the report first"
        )

    if not report.is_unlocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete payment to unlock this report"
        )
    
    try:
        # Parse analysis result
        analysis_data = None
        lifestyle_advice = None
        
        try:
            analysis_data = json.loads(report.analysis_result)
            lifestyle_advice = analysis_data.get("lifestyle_advice")
        except:
            analysis_data = report.analysis_result
        
        # Generate TTS
        result = await tts_service.generate_health_summary_tts(
            analysis_result=analysis_data,
            lifestyle_advice=lifestyle_advice if include_advice else None
        )
        
        return {
            "audio_url": result["audio_url"],
            "filename": result["filename"],
            "message": "Health report TTS generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.post("/tts/qa/{qa_id}")
async def generate_qa_tts(
    qa_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate TTS for Q&A response
    """
    # Get QA history
    result = await db.execute(
        select(QAHistory).where(QAHistory.id == qa_id)
    )
    qa = result.scalar_one_or_none()
    
    if not qa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QA not found"
        )
    
    # Verify ownership
    report_result = await db.execute(
        select(Report).where(Report.id == qa.report_id)
    )
    report = report_result.scalar_one_or_none()
    
    if not report or report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        result = await tts_service.generate_question_answer_tts(
            question=qa.question,
            answer=qa.answer
        )
        
        return {
            "audio_url": result["audio_url"],
            "filename": result["filename"],
            "message": "QA TTS generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )
