import logging
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


def send_synology_message(webhook_url: str, title: str, text: str, *, verify_ssl: Optional[bool] = None) -> None:
    """
    发送群晖 Chat 消息（兼容适配层，委托到新实现）
    
    参数:
    - webhook_url: 群晖 Chat Webhook地址，为空时使用DB配置
    - title: 消息标题
    - text: 消息内容
    - verify_ssl: 是否验证SSL证书，None时使用DB配置
    
    群晖Chat使用Form格式发送消息
    """
    # 延迟导入以避免循环依赖
    from app.notify.synochat_sender import send, _mask_url
    
    # 组合标题和内容
    message_content = f"{title}\n{text}" if title else text
    
    # 确定使用的webhook URL：优先使用参数，否则从DB读取
    final_webhook_url = webhook_url
    if not final_webhook_url:
        # 从数据库获取配置
        try:
            from core.db import DB
            from core.models.config_management import ConfigManagement
            
            db = DB.get_session()
            config = db.query(ConfigManagement).filter(
                ConfigManagement.config_key == "notify.synochat.webhook"
            ).first()
            
            if config and config.config_value:
                final_webhook_url = config.config_value
                logger.debug(f"Using DB-configured webhook URL: {_mask_url(final_webhook_url)}")
            else:
                raise RuntimeError("Synology Chat send failed: Webhook URL not configured in DB and no URL provided")
        except Exception as e:
            logger.error(f"Failed to access DB for webhook configuration: {e}")
            raise RuntimeError("Synology Chat send failed: Database access error for webhook configuration") from e
    
    # 确定verify_ssl设置：优先使用参数，否则从DB读取，默认True
    final_verify_ssl = verify_ssl
    if final_verify_ssl is None:
        try:
            db = DB.get_session()
            config = db.query(ConfigManagement).filter(
                ConfigManagement.config_key == "notify.synochat.verify_ssl"
            ).first()
            
            if config and config.config_value:
                final_verify_ssl = config.config_value.lower() == "true"
                logger.debug(f"Using DB-configured SSL verification: {final_verify_ssl}")
            else:
                final_verify_ssl = True  # 默认验证SSL
                logger.debug("Using default SSL verification: True")
        except Exception as e:
            logger.error(f"Failed to access DB for SSL configuration: {e}")
            final_verify_ssl = True  # 数据库访问失败时使用默认值
            logger.debug("Using default SSL verification due to DB access error: True")
    
    # 记录脱敏URL
    masked_url = _mask_url(final_webhook_url)
    logger.info(f"Sending Synology Chat message via compatibility layer: {masked_url}")
    
    try:
        # 委托到新sender实现
        result = send(message_content, final_webhook_url, final_verify_ssl)
        
        # 检查结果，非2xx状态码视为失败
        if not (200 <= result['status_code'] < 300):
            raise RuntimeError(
                f"Synology Chat send failed: status={result['status_code']}, "
                f"error={result['snippet']}"
            )
        
        logger.info(f"Synology Chat message sent successfully via compatibility layer: {result['status_code']}")
        
    except RuntimeError:
        raise  # 重新抛出已有的RuntimeError
    except Exception as e:
        error_msg = f"Synology Chat send failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e