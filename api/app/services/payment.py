"""
微信支付服务
WeChat Pay Integration for Health Report
"""

import hashlib
import hmac
import random
import string
import time
from datetime import datetime
from typing import Any, Dict

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Payment, PaymentStatus, Report


class WeChatPayService:
    """微信支付服务"""

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL

    def generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def generate_order_no(self, report_id: int) -> str:
        """生成商户订单号"""
        timestamp = int(time.time())
        return f"HRP{timestamp}{report_id:04d}"

    def sign(self, params: dict) -> str:
        """生成签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        sign_str += f"&key={self.api_key}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    async def create_unified_order(
        self,
        order_no: str,
        amount: int,
        description: str,
        openid: str,
    ) -> dict:
        """创建统一下单"""
        url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"

        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "description": description,
            "out_trade_no": order_no,
            "notify_url": self.notify_url,
            "amount": {"total": amount, "currency": "CNY"},
            "payer": {"openid": openid},
        }

        timestamp = str(int(time.time()))
        nonce_str = self.generate_nonce_str()

        sign_str = f"POST\n/v3/pay/transactions/jsapi\n{timestamp}\n{nonce_str}\n{params}\n"
        sign = hmac.new(
            self.api_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).digest().hex().upper()

        auth = (
            'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",nonce_str="{nonce_str}",timestamp="{timestamp}",signature="{sign}"'
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": auth,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=params, headers=headers)
            result = response.json()
            if response.status_code == 200:
                return {"prepay_id": result.get("prepay_id"), "order_no": order_no}
            raise Exception(f"WeChat Pay API error: {result}")

    def generate_jsapi_params(self, prepay_id: str) -> dict:
        """生成JSAPI支付参数"""
        timestamp = str(int(time.time()))
        nonce_str = self.generate_nonce_str()
        package = f"prepay_id={prepay_id}"

        sign_str = f"{self.app_id}\n{timestamp}\n{nonce_str}\n{package}\n"
        pay_sign = hmac.new(
            self.api_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).digest().hex().upper()

        return {
            "appId": self.app_id,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "HMAC-SHA256",
            "paySign": pay_sign,
        }

    async def verify_callback(self, params: dict) -> bool:
        """验证微信支付回调签名

        TODO: 示例项目使用简化签名校验；生产环境应基于微信支付 v3 官方签名/证书校验流程实现。
        """
        sign = params.get("sign", "")
        params_copy = {k: v for k, v in params.items() if k != "sign"}
        return sign == self.sign(params_copy)

    def parse_callback_xml(self, xml_data: str) -> dict:
        """解析微信支付回调XML"""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(xml_data)
        return {child.tag: child.text for child in root}


class PaymentService:
    """支付业务服务"""

    def __init__(self):
        self.wechat_pay = WeChatPayService()

    async def create_payment(
        self,
        db: AsyncSession,
        user_id: int,
        report_id: int,
        openid: str,
        amount: int = 990,
    ) -> dict:
        """创建支付订单并落库 Payment 模型"""
        order_no = self.wechat_pay.generate_order_no(report_id)

        result = await self.wechat_pay.create_unified_order(
            order_no=order_no,
            amount=amount,
            description="体检报告解读服务",
            openid=openid,
        )

        payment = Payment(
            user_id=user_id,
            report_id=report_id,
            order_no=order_no,
            amount=amount,
            status=PaymentStatus.PENDING,
            provider="wechat",
        )
        db.add(payment)
        await db.flush()

        pay_params = self.wechat_pay.generate_jsapi_params(result["prepay_id"])
        return {"order_id": order_no, "prepay_id": result["prepay_id"], "pay_params": pay_params}

    async def handle_callback(self, db: AsyncSession, xml_data: str) -> Dict[str, Any]:
        """处理支付回调（幂等 + 事务）并更新 Payment/Report"""
        params = self.wechat_pay.parse_callback_xml(xml_data)

        order_no = params.get("out_trade_no")
        provider_txn_id = params.get("transaction_id")
        return_code = params.get("return_code")
        result_code = params.get("result_code")

        if not order_no:
            return {"success": False, "message": "Missing order number in callback", "idempotent": False}

        if not await self.wechat_pay.verify_callback(params):
            return {"success": False, "message": "Invalid callback signature", "idempotent": False}

        async with db.begin_nested():
            payment_result = await db.execute(
                select(Payment).where(Payment.order_no == order_no).with_for_update()
            )
            payment = payment_result.scalar_one_or_none()

            if not payment:
                return {"success": False, "message": "Payment not found", "idempotent": False}

            # 幂等：已支付订单重复回调直接成功返回
            if payment.status == PaymentStatus.PAID:
                return {"success": True, "message": "Payment already processed", "idempotent": True}

            callback_success = return_code == "SUCCESS" and result_code == "SUCCESS"
            if callback_success:
                paid_at = datetime.utcnow()
                payment.status = PaymentStatus.PAID
                payment.paid_at = paid_at
                payment.provider_txn_id = provider_txn_id

                report_result = await db.execute(
                    select(Report).where(Report.id == payment.report_id).with_for_update()
                )
                report = report_result.scalar_one_or_none()
                if report:
                    report.is_paid = True
                    report.is_unlocked = True
                    report.paid_at = paid_at
                    report.order_id = order_no

                return {
                    "success": True,
                    "message": "Payment callback processed",
                    "idempotent": False,
                }

            # 支付失败：落库失败状态，不解锁
            payment.status = PaymentStatus.FAILED
            payment.provider_txn_id = provider_txn_id
            return {
                "success": False,
                "message": "Payment failed in callback",
                "idempotent": False,
            }


# Singleton
payment_service = PaymentService()
