"""
支付相关API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.models import User, Report, Payment
from app.core.security import verify_token
from app.models.schemas import (
    CreatePaymentRequest, CreatePaymentResponse,
    PaymentStatusResponse
)
from app.services.payment import payment_service


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


@router.post("/create")
async def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建支付订单
    
    用户上传报告后，需要支付才能查看完整报告
    """
    # 获取报告
    result = await db.execute(
        select(Report).where(
            Report.id == request.report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # 检查是否已支付
    if report.is_unlocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report already paid"
        )
    
    # 获取用户openid (需要从小程序传递)
    # 这里从数据库获取
    openid = current_user.openid
    
    try:
        # 创建支付订单
        payment_result = await payment_service.create_payment(
            db=db,
            user_id=current_user.id,
            report_id=request.report_id,
            openid=openid,
            amount=990  # 9.9元
        )
        
        return {
            "order_id": payment_result["order_id"],
            "prepay_id": payment_result["prepay_id"],
            "pay_params": payment_result["pay_params"],
            "amount": 990
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询支付状态
    """
    result = await db.execute(select(Payment).where(Payment.order_no == order_id))
    payment = result.scalar_one_or_none()

    if not payment or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return PaymentStatusResponse(
        order_id=order_id,
        status=payment.status,
        amount=payment.amount,
        paid_at=payment.paid_at
    )


@router.post("/callback")
async def payment_callback(
    xml_data: str,
    db: AsyncSession = Depends(get_db)
):
    """
    微信支付回调
    
    支付成功后，微信会POST XML数据到此接口
    """
    try:
        # 处理回调（以后端回调为最终支付依据）
        result = await payment_service.handle_callback(db=db, xml_data=xml_data)

        if result["success"]:
            return {"code": "SUCCESS", "message": result["message"]}

        return {"code": "FAIL", "message": result["message"]}
            
    except Exception as e:
        print(f"Payment callback error: {e}")
        return {"code": "FAIL", "message": str(e)}


@router.post("/verify")
async def verify_payment(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    验证支付状态（小程序轮询调用）
    
    小程序支付完成后，轮询此接口确认支付结果
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
    
    return {
        "is_paid": report.is_paid,
        "is_unlocked": report.is_unlocked,
        "can_view_full": report.is_unlocked,
        "can_use_tts": report.is_unlocked,
        "can_ask_question": report.is_unlocked,
        "remaining_questions": 2 if report.is_unlocked else 0
    }
