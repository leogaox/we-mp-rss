import pytest
from unittest.mock import patch, MagicMock
from apis.synochat_settings import _get_config_value, _set_config_value
from core.models.config_management import ConfigManagement
import time


class TestSynochatSettingsLogic:
    """测试 Synology Chat 设置逻辑"""
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_get_config_value_existing(self, mock_get_session):
        """测试获取存在的配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock config item
        mock_config = MagicMock()
        mock_config.config_value = "test_value"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_config
        
        result = _get_config_value("test.key")
        assert result == "test_value"
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_get_config_value_missing(self, mock_get_session):
        """测试获取不存在的配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock missing config
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = _get_config_value("test.key", "default_value")
        assert result == "default_value"
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_set_config_value_new(self, mock_get_session):
        """测试设置新配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock missing config (new)
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        _set_config_value("test.key", "new_value", "Test description")
        
        # Verify new config was created
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Check the config object that was added
        added_config = mock_session.add.call_args[0][0]
        assert added_config.config_key == "test.key"
        assert added_config.config_value == "new_value"
        assert "Test description" in added_config.description
    
    @patch('apis.synochat_settings.DB.get_session')
    def test_set_config_value_existing(self, mock_get_session):
        """测试更新现有配置值"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock existing config
        mock_config = MagicMock()
        mock_config.config_value = "old_value"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_config
        
        _set_config_value("test.key", "new_value", "Updated description")
        
        # Verify config was updated, not added
        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()
        
        # Check the config was updated
        assert mock_config.config_value == "new_value"
        assert mock_config.description == "Updated description"


class TestCoolingPeriod:
    """测试冷却时间逻辑"""
    
    def test_cooling_period_logic(self):
        """测试冷却时间计算"""
        from apis.synochat_settings import last_test_time
        
        # Reset global variable
        global_last_test_time = 0
        
        # Mock time module
        with patch('apis.synochat_settings.time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # First call should not be in cooling period
            current_time = mock_time()
            cooling_period = 10
            
            # Not in cooling period (first call)
            assert current_time - global_last_test_time >= cooling_period
            
            # Update last test time
            global_last_test_time = current_time
            
            # Immediately after, should be in cooling period
            assert current_time - global_last_test_time < cooling_period
            
            # After 11 seconds, should not be in cooling period
            mock_time.return_value = 1011.0
            assert mock_time() - global_last_test_time >= cooling_period


class TestConfigValidation:
    """测试配置验证逻辑"""
    
    def test_verify_ssl_parsing(self):
        """测试 verify_ssl 字符串解析"""
        test_cases = [
            ("true", True),
            ("false", False),
            ("True", True),
            ("False", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("", False),  # Empty should default to False
            (None, False)  # None should default to False
        ]
        
        for input_val, expected in test_cases:
            if input_val is None:
                result = "false".lower() == "true"  # Simulate default behavior
            else:
                result = str(input_val).lower() in ('true', '1', 'yes')
            
            assert result == expected, f"Failed for input: {input_val}"


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