import httpx
from app.core.config import settings


class WeChatService:
    """WeChat login service"""
    
    @staticmethod
    async def get_openid(code: str) -> dict:
        """
        Get user openid from WeChat code
        https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/login/auth.code2Session.html
        """
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if "openid" in data:
                return {
                    "openid": data["openid"],
                    "session_key": data.get("session_key"),
                    "unionid": data.get("unionid")
                }
            else:
                raise Exception(f"WeChat API error: {data.get('errmsg', 'Unknown error')}")
