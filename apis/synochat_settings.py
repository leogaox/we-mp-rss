from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from core.models.config_management import ConfigManagement
from core.db import DB
from core.auth import get_current_user
from .base import success_response, error_response
from app.notify.synochat_sender import send, build_text
import time
import logging

router = APIRouter(prefix="/settings/notify/synochat", tags=["Synology Chat 设置"])
logger = logging.getLogger(__name__)

# 冷却时间控制（10秒）
last_test_time = 0


class SynochatSettings(BaseModel):
    enabled: bool
    webhook: Optional[str] = None
    verify_ssl: Optional[bool] = True


class TestResponse(BaseModel):
    ok: bool
    status: int
    snippet: str
    error: Optional[str] = None


def _get_config_value(key: str, default: str = None) -> str:
    """从数据库获取配置值"""
    db = DB.get_session()
    config = db.query(ConfigManagement).filter(ConfigManagement.config_key == key).first()
    return config.config_value if config else default


def _set_config_value(key: str, value: str, description: str = ""):
    """设置配置值到数据库"""
    db = DB.get_session()
    config = db.query(ConfigManagement).filter(ConfigManagement.config_key == key).first()
    
    if config:
        config.config_value = value
        if description:
            config.description = description
    else:
        config = ConfigManagement(
            config_key=key,
            config_value=value,
            description=description or f"Synology Chat {key.split('.')[-1]} 配置"
        )
        db.add(config)
    
    db.commit()


@router.get("", summary="获取 Synology Chat 配置")
def get_synochat_settings(current_user: dict = Depends(get_current_user)):
    """获取 Synology Chat 通知配置"""
    try:
        enabled = _get_config_value("notify.synochat.enabled", "false").lower() == "true"
        webhook = _get_config_value("notify.synochat.webhook")
        verify_ssl = _get_config_value("notify.synochat.verify_ssl", "true").lower() == "true"
        
        return success_response(data={
            "enabled": enabled,
            "webhook": webhook,
            "verify_ssl": verify_ssl
        })
    except Exception as e:
        logger.error(f"获取 Synology Chat 配置失败: {str(e)}")
        return error_response(code=500, message="获取配置失败")


@router.put("", summary="更新 Synology Chat 配置")
def update_synochat_settings(
    settings: SynochatSettings = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """更新 Synology Chat 通知配置"""
    try:
        # 校验：如果启用，webhook 必填
        if settings.enabled and not settings.webhook:
            return error_response(code=400, message="启用通知时 Webhook URL 不能为空")
        
        # 保存配置到数据库
        _set_config_value("notify.synochat.enabled", str(settings.enabled).lower(), "Synology Chat 通知是否启用")
        
        if settings.webhook:
            _set_config_value("notify.synochat.webhook", settings.webhook, "Synology Chat Webhook URL")
        
        _set_config_value(
            "notify.synochat.verify_ssl", 
            str(settings.verify_ssl if settings.verify_ssl is not None else True).lower(),
            "是否验证 SSL 证书"
        )
        
        return success_response(message="配置保存成功")
    except Exception as e:
        logger.error(f"更新 Synology Chat 配置失败: {str(e)}")
        return error_response(code=500, message="保存配置失败")


@router.post("/test", summary="测试 Synology Chat 通知", response_model=TestResponse)
def test_synochat_notification(current_user: dict = Depends(get_current_user)):
    """测试 Synology Chat 通知通道"""
    global last_test_time
    
    # 检查冷却时间
    current_time = time.time()
    if current_time - last_test_time < 10:
        remaining = int(10 - (current_time - last_test_time))
        raise HTTPException(
            status_code=429,
            detail={
                "ok": False,
                "status": 429,
                "snippet": f"请等待 {remaining} 秒后再试",
                "error": "Cooling period"
            }
        )
    
    try:
        # 从数据库读取配置
        webhook = _get_config_value("notify.synochat.webhook")
        if not webhook:
            raise HTTPException(
                status_code=400,
                detail={
                    "ok": False,
                    "status": 400,
                    "snippet": "Webhook URL 未配置",
                    "error": "Webhook not configured"
                }
            )
        
        verify_ssl = _get_config_value("notify.synochat.verify_ssl", "true").lower() == "true"
        
        # 构建测试消息
        test_message = build_text(["测试通道连通性"])
        
        # 发送测试消息
        result = send(test_message, webhook, verify_ssl)
        
        # 更新最后测试时间
        last_test_time = current_time
        
        # 记录日志（脱敏）
        from app.notify.synochat_sender import _mask_url
        masked_url = _mask_url(webhook)
        logger.info(f"Synology Chat 测试消息发送到: {masked_url}, 状态码: {result['status_code']}")
        
        if 200 <= result['status_code'] < 300:
            return {
                "ok": True,
                "status": result['status_code'],
                "snippet": result['snippet']
            }
        else:
            return {
                "ok": False,
                "status": result['status_code'],
                "snippet": result['snippet'],
                "error": f"HTTP {result['status_code']}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synology Chat 测试失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "status": 500,
                "snippet": str(e)[:200],
                "error": "Internal server error"
            }
        )