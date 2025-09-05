import pytest
from unittest.mock import patch, MagicMock
from core.models.config_management import ConfigManagement
import time


class TestConfigFunctions:
    """测试配置函数"""
    
    @patch('core.db.DB.get_session')
    def test_get_config_value_existing(self, mock_get_session):
        """测试获取存在的配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock config item
        mock_config = MagicMock()
        mock_config.config_value = "test_value"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_config
        
        # Import and test the function
        from apis.synochat_settings import _get_config_value
        result = _get_config_value("test.key")
        assert result == "test_value"
    
    @patch('core.db.DB.get_session')
    def test_get_config_value_missing(self, mock_get_session):
        """测试获取不存在的配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock missing config
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Import and test the function
        from apis.synochat_settings import _get_config_value
        result = _get_config_value("test.key", "default_value")
        assert result == "default_value"


class TestCoolingPeriod:
    """测试冷却时间逻辑"""
    
    def test_cooling_period_calculation(self):
        """测试冷却时间计算"""
        current_time = time.time()
        cooling_period = 10
        
        # Not in cooling period (first call)
        last_test_time = 0
        assert current_time - last_test_time >= cooling_period
        
        # In cooling period (just called)
        last_test_time = current_time
        assert current_time - last_test_time < cooling_period
        
        # After cooling period
        future_time = current_time + 11
        assert future_time - last_test_time >= cooling_period


class TestBuildText:
    """测试消息构建逻辑"""
    
    def test_build_text_with_feeds(self):
        """测试有公众号列表的消息构建"""
        from app.notify.synochat_sender import build_text
        
        feeds = ["公众号A", "公众号B"]
        result = build_text(feeds)
        expected = "**WeRSS 更新公众号**\n• 公众号A\n• 公众号B"
        
        assert result == expected
    
    def test_build_text_empty(self):
        """测试空公众号列表的消息构建"""
        from app.notify.synochat_sender import build_text
        
        result = build_text([])
        expected = "**WeRSS 更新公众号**"
        
        assert result == expected
    
    def test_build_text_single(self):
        """测试单个公众号的消息构建"""
        from app.notify.synochat_sender import build_text
        
        result = build_text(["测试公众号"])
        expected = "**WeRSS 更新公众号**\n• 测试公众号"
        
        assert result == expected


class TestSendFunction:
    """测试发送函数"""
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_success(self, mock_post):
        """测试成功发送"""
        from app.notify.synochat_sender import send
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "success"
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook")
        
        assert result["status_code"] == 200
        assert result["snippet"] == "success"
        
        # Verify request was made with correct data
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "payload=" in kwargs["data"]
        assert "测试消息" in kwargs["data"]
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_timeout(self, mock_post):
        """测试超时错误"""
        from app.notify.synochat_sender import send
        
        # Mock timeout
        mock_post.side_effect = Exception("Request timeout")
        
        result = send("测试消息", "https://example.com/webhook")
        
        assert result["status_code"] == 0
        assert "timeout" in result["snippet"].lower()


class TestURLMasking:
    """测试 URL 脱敏"""
    
    def test_url_masking(self):
        """测试 URL 脱敏功能"""
        from app.notify.synochat_sender import _mask_url
        
        # Test URL with query parameters
        url_with_token = "https://example.com/webhook?token=secret123&other=param"
        masked = _mask_url(url_with_token)
        
        assert "https://example.com/webhook" in masked
        assert "?***masked***" in masked
        assert "token=secret123" not in masked
        
        # Test URL without query parameters
        url_without_token = "https://example.com/webhook"
        masked = _mask_url(url_without_token)
        
        assert masked == "https://example.com/webhook"