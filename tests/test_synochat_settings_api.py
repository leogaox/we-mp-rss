import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session
from core.models.config_management import ConfigManagement
from core.db import DB
import time

# Create test app
app = FastAPI()

# Import and include the router
from apis.synochat_settings import router
app.include_router(router)

client = TestClient(app)


class TestSynochatSettingsAPI:
    """测试 Synology Chat 设置 API"""
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_get_settings_empty(self, mock_get_session):
        """测试获取空配置"""
        # Mock empty database
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/settings/notify/synochat")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["enabled"] == False
        assert data["data"]["webhook"] is None
        assert data["data"]["verify_ssl"] == True
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_get_settings_with_data(self, mock_get_session):
        """测试获取已有配置"""
        # Mock database with data
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock config items
        enabled_config = MagicMock()
        enabled_config.config_value = "true"
        
        webhook_config = MagicMock()
        webhook_config.config_value = "https://example.com/webhook"
        
        ssl_config = MagicMock()
        ssl_config.config_value = "false"
        
        def mock_filter(config_key):
            mock_query = MagicMock()
            if config_key == "notify.synochat.enabled":
                mock_query.first.return_value = enabled_config
            elif config_key == "notify.synochat.webhook":
                mock_query.first.return_value = webhook_config
            elif config_key == "notify.synochat.verify_ssl":
                mock_query.first.return_value = ssl_config
            return mock_query
        
        mock_session.query.return_value.filter.side_effect = mock_filter
        
        response = client.get("/settings/notify/synochat")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["enabled"] == True
        assert data["data"]["webhook"] == "https://example.com/webhook"
        assert data["data"]["verify_ssl"] == False
    
    @patch('apis.synochat_settings._set_config_value')
    def test_update_settings_success(self, mock_set_config):
        """测试更新配置成功"""
        payload = {
            "enabled": True,
            "webhook": "https://example.com/webhook",
            "verify_ssl": False
        }
        
        response = client.put("/settings/notify/synochat", json=payload)
        
        assert response.status_code == 200
        assert response.json()["code"] == 0
        assert mock_set_config.call_count == 3
    
    def test_update_settings_missing_webhook_when_enabled(self):
        """测试启用时缺少 webhook 报错"""
        payload = {
            "enabled": True,
            "webhook": None,
            "verify_ssl": True
        }
        
        response = client.put("/settings/notify/synochat", json=payload)
        
        assert response.status_code == 200  # FastAPI returns 200 even for business errors
        data = response.json()
        assert data["code"] == 400
        assert "Webhook URL 不能为空" in data["message"]
    
    @patch('apis.synochat_settings._get_config_value')
    @patch('apis.synochat_settings.send')
    def test_test_notification_success(self, mock_send, mock_get_config):
        """测试通知成功"""
        # Mock config values
        mock_get_config.side_effect = lambda key, default=None: {
            "notify.synochat.webhook": "https://example.com/webhook",
            "notify.synochat.verify_ssl": "true"
        }.get(key, default)
        
        # Mock successful send
        mock_send.return_value = {
            "status_code": 200,
            "snippet": "success"
        }
        
        response = client.post("/settings/notify/synochat/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] == True
        assert data["status"] == 200
        assert data["snippet"] == "success"
    
    @patch('apis.synochat_settings._get_config_value')
    def test_test_notification_missing_webhook(self, mock_get_config):
        """测试缺少 webhook 配置"""
        # Mock missing webhook
        mock_get_config.return_value = None
        
        response = client.post("/settings/notify/synochat/test")
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] == False
        assert data["status"] == 400
        assert "Webhook not configured" in data["detail"]["error"]
    
    @patch('apis.synochat_settings._get_config_value')
    @patch('apis.synochat_settings.send')
    def test_test_notification_http_error(self, mock_send, mock_get_config):
        """测试 HTTP 错误"""
        # Mock config values
        mock_get_config.side_effect = lambda key, default=None: {
            "notify.synochat.webhook": "https://example.com/webhook",
            "notify.synochat.verify_ssl": "true"
        }.get(key, default)
        
        # Mock HTTP error
        mock_send.return_value = {
            "status_code": 401,
            "snippet": "Unauthorized"
        }
        
        response = client.post("/settings/notify/synochat/test")
        
        assert response.status_code == 200  # Business error, not HTTP error
        data = response.json()
        assert data["ok"] == False
        assert data["status"] == 401
        assert data["snippet"] == "Unauthorized"
    
    @patch('apis.synochat_settings._get_config_value')
    @patch('apis.synochat_settings.send')
    def test_test_notification_timeout(self, mock_send, mock_get_config):
        """测试超时错误"""
        # Mock config values
        mock_get_config.side_effect = lambda key, default=None: {
            "notify.synochat.webhook": "https://example.com/webhook",
            "notify.synochat.verify_ssl": "true"
        }.get(key, default)
        
        # Mock timeout
        mock_send.return_value = {
            "status_code": 0,
            "snippet": "Request timeout"
        }
        
        response = client.post("/settings/notify/synochat/test")
        
        assert response.status_code == 200  # Business error, not HTTP error
        data = response.json()
        assert data["ok"] == False
        assert data["status"] == 0
        assert "timeout" in data["snippet"].lower()
    
    @patch('apis.synochat_settings._get_config_value')
    @patch('apis.synochat_settings.send')
    def test_test_notification_cooling_period(self, mock_send, mock_get_config):
        """测试冷却时间"""
        # Mock config values
        mock_get_config.side_effect = lambda key, default=None: {
            "notify.synochat.webhook": "https://example.com/webhook",
            "notify.synochat.verify_ssl": "true"
        }.get(key, default)
        
        # Mock successful send
        mock_send.return_value = {
            "status_code": 200,
            "snippet": "success"
        }
        
        # First request should succeed
        response1 = client.post("/settings/notify/synochat/test")
        assert response1.status_code == 200
        
        # Second request within 10 seconds should fail
        response2 = client.post("/settings/notify/synochat/test")
        assert response2.status_code == 429
        data = response2.json()
        assert data["ok"] == False
        assert data["status"] == 429
        assert "Cooling period" in data["detail"]["error"]
    
    @patch('apis.synochat_settings._get_config_value')
    @patch('apis.synochat_settings.send')
    def test_test_notification_after_cooling_period(self, mock_send, mock_get_config):
        """测试冷却时间过后可以再次请求"""
        # Mock config values
        mock_get_config.side_effect = lambda key, default=None: {
            "notify.synochat.webhook": "https://example.com/webhook",
            "notify.synochat.verify_ssl": "true"
        }.get(key, default)
        
        # Mock successful send
        mock_send.return_value = {
            "status_code": 200,
            "snippet": "success"
        }
        
        # First request
        response1 = client.post("/settings/notify/synochat/test")
        assert response1.status_code == 200
        
        # Mock time passing (11 seconds later)
        with patch('apis.synochat_settings.time.time') as mock_time:
            mock_time.return_value = time.time() + 11
            
            # Second request should succeed after cooling period
            response2 = client.post("/settings/notify/synochat/test")
            assert response2.status_code == 200
            assert response2.json()["ok"] == True


class TestSynochatSettingsValidation:
    """测试配置验证"""
    
    def test_verify_ssl_default_true(self):
        """测试 verify_ssl 默认值为 true"""
        payload = {
            "enabled": False,
            "webhook": None
            # verify_ssl not provided, should default to True
        }
        
        response = client.put("/settings/notify/synochat", json=payload)
        
        assert response.status_code == 200
        # Should succeed without explicit verify_ssl
    
    def test_verify_ssl_explicit_false(self):
        """测试显式设置 verify_ssl=false"""
        payload = {
            "enabled": False,
            "webhook": None,
            "verify_ssl": False
        }
        
        response = client.put("/settings/notify/synochat", json=payload)
        
        assert response.status_code == 200
        # Should succeed with explicit false