"""
微信支付服务
WeChat Pay Integration for Health Report
"""

import hashlib
import hmac
import random
import string
import time
import httpx
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.config import settings


# ============= Database Models =============

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
    report = relationship("Report", back_populates="payment")


# ============= Pydantic Schemas =============

class CreatePaymentRequest(BaseModel):
    report_id: int


class CreatePaymentResponse(BaseModel):
    order_id: str
    prepay_id: str
    pay_sign: str
    timestamp: str
    nonce_str: str
    package: str


class PaymentCallbackRequest(BaseModel):
    return_code: str
    return_msg: str
    result_code: str
    transaction_id: str
    out_trade_no: str
    time_end: str
    total_fee: int
    sign: str


class PaymentStatusResponse(BaseModel):
    order_id: str
    status: str
    amount: int
    paid_at: Optional[datetime]


# ============= WeChat Pay Service =============

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
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_order_id(self, report_id: int) -> str:
        """生成商户订单号"""
        timestamp = int(time.time())
        return f"HRP{timestamp}{report_id:04d}"
    
    def sign(self, params: dict) -> str:
        """生成签名"""
        # 按key升序排列
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接成字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        sign_str += f"&key={self.api_key}"
        # MD5加密并转大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    async def create_unified_order(
        self, 
        order_id: str, 
        amount: int,
        description: str,
        openid: str
    ) -> dict:
        """创建统一下单"""
        url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
        
        # 构建请求参数
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "description": description,
            "out_trade_no": order_id,
            "notify_url": self.notify_url,
            "amount": {
                "total": amount,  # 单位: 分
                "currency": "CNY"
            },
            "payer": {
                "openid": openid
            }
        }
        
        # 生成签名
        timestamp = str(int(time.time()))
        nonce_str = self.generate_nonce_str()
        
        # 构建签名原串
        sign_str = f"POST\n/v3/pay/transactions/jsapi\n{timestamp}\n{nonce_str}\n{params}\n"
        sign = hmac.new(
            self.api_key.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest().hexdigest().upper()
        
        # 添加认证头
        auth = f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce_str}",timestamp="{timestamp}",signature="{sign}"'
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': auth
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=params, headers=headers)
                result = response.json()
                
                if response.status_code == 200:
                    return {
                        "prepay_id": result.get("prepay_id"),
                        "order_id": order_id
                    }
                else:
                    raise Exception(f"WeChat Pay API error: {result}")
            except Exception as e:
                raise Exception(f"Payment creation failed: {str(e)}")
    
    def generate_jsapi_params(self, prepay_id: str) -> dict:
        """生成JSAPI支付参数"""
        timestamp = str(int(time.time()))
        nonce_str = self.generate_nonce_str()
        package = f"prepay_id={prepay_id}"
        
        # 签名
        sign_str = f"{self.app_id}\n{timestamp}\n{nonce_str}\n{package}\n"
        pay_sign = hmac.new(
            self.api_key.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest().hexdigest().upper()
        
        return {
            "appId": self.app_id,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "HMAC-SHA256",
            "paySign": pay_sign
        }
    
    async def verify_callback(self, params: dict) -> bool:
        """验证微信支付回调签名"""
        # 获取签名
        sign = params.get('sign', '')
        # 移除sign字段
        params_copy = {k: v for k, v in params.items() if k != 'sign'}
        # 验证签名
        calculated_sign = self.sign(params_copy)
        return sign == calculated_sign
    
    def parse_callback_xml(self, xml_data: str) -> dict:
        """解析微信支付回调XML"""
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(xml_data)
        result = {}
        for child in root:
            result[child.tag] = child.text
        
        return result


# ============= Payment Service =============

class PaymentService:
    """支付业务服务"""
    
    def __init__(self):
        self.wechat_pay = WeChatPayService()
    
    async def create_payment(
        self,
        user_id: int,
        report_id: int,
        openid: str,
        amount: int = 990  # 默认9.9元
    ) -> dict:
        """创建支付订单"""
        # 生成订单号
        order_id = self.wechat_pay.generate_order_id(report_id)
        
        # 创建微信支付订单
        result = await self.wechat_pay.create_unified_order(
            order_id=order_id,
            amount=amount,
            description="体检报告解读服务",
            openid=openid
        )
        
        # 生成小程序支付参数
        pay_params = self.wechat_pay.generate_jsapi_params(result['prepay_id'])
        
        return {
            "order_id": order_id,
            "prepay_id": result['prepay_id'],
            "pay_params": pay_params
        }
    
    async def handle_callback(self, xml_data: str) -> bool:
        """处理支付回调"""
        # 解析XML
        params = self.wechat_pay.parse_callback_xml(xml_data)
        
        # 验证签名
        if not await self.wechat_pay.verify_callback(params):
            return False
        
        # 检查返回码
        if params.get('return_code') != 'SUCCESS':
            return False
        
        # 检查业务结果
        if params.get('result_code') != 'SUCCESS':
            return False
        
        # 更新订单状态
        order_id = params.get('out_trade_no')
        transaction_id = params.get('transaction_id')
        
        # TODO: 更新数据库订单状态
        # await self.update_payment_status(order_id, transaction_id)
        
        # TODO: 解锁报告内容
        # await self.unlock_report(order_id)
        
        return True


# Singleton
payment_service = PaymentService()
