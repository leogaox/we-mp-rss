import json
import logging
import re
from typing import TypedDict, List
from urllib.parse import urlparse, quote

import requests

logger = logging.getLogger(__name__)


class SendResult(TypedDict):
    status_code: int
    snippet: str


def build_text(feeds: List[str]) -> str:
    """构建消息文本
    
    Args:
        feeds: 更新的公众号列表
        
    Returns:
        格式化后的消息文本
    """
    base_text = "**WeRSS 更新公众号**"
    if feeds:
        feed_lines = "\n".join(f"• {feed}" for feed in feeds)
        return f"{base_text}\n{feed_lines}"
    return base_text


def _mask_url(url: str) -> str:
    """掩码 URL，保护 token 信息"""
    parsed = urlparse(url)
    if parsed.query:
        # 显示协议和域名部分，掩码查询参数
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return f"{base_url}?***masked***"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def send(text: str, url: str, verify_ssl: bool = True) -> SendResult:
    """发送消息到 Synology Chat
    
    Args:
        text: 消息文本
        url: Webhook URL
        verify_ssl: 是否验证 SSL 证书
        
    Returns:
        发送结果，包含状态码和响应片段
    """
    masked_url = _mask_url(url)
    logger.info(f"Sending message to Synology Chat: {masked_url}")
    
    # 准备请求数据
    payload_data = {"text": text}
    data = "payload=" + quote(json.dumps(payload_data, ensure_ascii=False))
    
    try:
        response = requests.post(
            url=url,
            data=data,
            timeout=10,
            verify=verify_ssl
        )
        
        # 记录响应
        status_code = response.status_code
        snippet = response.text[:200]
        
        if 200 <= status_code < 300:
            logger.info(f"Synology Chat message sent successfully: {status_code}")
        else:
            logger.error(f"Synology Chat message failed: {status_code} - {snippet}")
        
        return {
            "status_code": status_code,
            "snippet": snippet
        }
        
    except requests.exceptions.Timeout:
        error_msg = "Synology Chat request timeout"
        logger.error(error_msg)
        return {
            "status_code": 0,
            "snippet": error_msg[:200]
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Synology Chat request failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status_code": 0,
            "snippet": error_msg[:200]
        }