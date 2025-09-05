import os
from unittest.mock import patch, MagicMock
import pytest
from core.models.config_management import ConfigManagement
from init_sys import init_synochat_from_env_if_missing


class TestBootstrapSynochat:
    """测试 Synology Chat 引导初始化"""
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    def test_init_when_missing_config_and_env_exists(self, mock_getenv, mock_get_session):
        """测试当配置缺失且环境变量存在时的初始化"""
        # 模拟数据库会话
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # 模拟查询返回空（配置不存在）
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # 模拟环境变量存在
        mock_getenv.side_effect = lambda key, default=None: {
            'SYNOLOGY_CHAT_WEBHOOK': 'https://example.com/webhook?token=secret',
            'SYNOLOGY_CHAT_VERIFY_SSL': 'true'
        }.get(key, default)
        
        # 执行初始化
        init_synochat_from_env_if_missing()
        
        # 验证配置被正确写入
        assert mock_session.merge.call_count == 3  # enabled, webhook, verify_ssl
        
        # 获取所有调用的参数
        merge_calls = mock_session.merge.call_args_list
        
        # 验证配置项
        config_keys = [call[0][0].config_key for call in merge_calls]
        config_values = [call[0][0].config_value for call in merge_calls]
        
        assert 'notify.synochat.enabled' in config_keys
        assert 'notify.synochat.webhook' in config_keys
        assert 'notify.synochat.verify_ssl' in config_keys
        
        assert 'false' in config_values  # enabled 默认 false
        assert 'https://example.com/webhook?token=secret' in config_values
        assert 'true' in config_values  # verify_ssl
        
        # 验证提交
        mock_session.commit.assert_called_once()
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    def test_init_when_config_exists(self, mock_getenv, mock_get_session):
        """测试当配置已存在时不进行初始化"""
        # 模拟数据库会话
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # 模拟查询返回现有配置（配置已存在）
        mock_config = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_config
        
        # 执行初始化
        init_synochat_from_env_if_missing()
        
        # 验证没有进行任何配置写入
        mock_session.merge.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    def test_init_when_missing_config_and_no_env(self, mock_getenv, mock_get_session):
        """测试当配置缺失且环境变量也不存在时不进行初始化"""
        # 模拟数据库会话
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # 模拟查询返回空（配置不存在）
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # 模拟环境变量不存在
        mock_getenv.return_value = None
        
        # 执行初始化
        init_synochat_from_env_if_missing()
        
        # 验证没有进行任何配置写入
        mock_session.merge.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    def test_init_with_verify_ssl_false(self, mock_getenv, mock_get_session):
        """测试 verify_ssl=false 的环境变量"""
        # 模拟数据库会话
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # 模拟查询返回空（配置不存在）
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # 模拟环境变量，verify_ssl 为 false
        mock_getenv.side_effect = lambda key, default=None: {
            'SYNOLOGY_CHAT_WEBHOOK': 'https://example.com/webhook',
            'SYNOLOGY_CHAT_VERIFY_SSL': 'false'
        }.get(key, default)
        
        # 执行初始化
        init_synochat_from_env_if_missing()
        
        # 验证 verify_ssl 配置为 false
        merge_calls = mock_session.merge.call_args_list
        config_values = {call[0][0].config_key: call[0][0].config_value for call in merge_calls}
        
        assert config_values['notify.synochat.verify_ssl'] == 'false'
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    def test_init_with_different_verify_ssl_values(self, mock_getenv, mock_get_session):
        """测试不同的 verify_ssl 环境变量值"""
        test_cases = [
            ('true', 'true'),
            ('false', 'false'),
            ('1', 'true'),
            ('0', 'false'),
            ('yes', 'true'),
            ('no', 'false'),
            ('TRUE', 'true'),
            ('FALSE', 'false')
        ]
        
        for env_value, expected_db_value in test_cases:
            # 重置 mock
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            mock_getenv.side_effect = lambda key, default=None: {
                'SYNOLOGY_CHAT_WEBHOOK': 'https://example.com/webhook',
                'SYNOLOGY_CHAT_VERIFY_SSL': env_value
            }.get(key, default)
            
            # 执行初始化
            init_synochat_from_env_if_missing()
            
            # 验证 verify_ssl 配置值
            merge_calls = mock_session.merge.call_args_list
            config_values = {call[0][0].config_key: call[0][0].config_value for call in merge_calls}
            
            assert config_values['notify.synochat.verify_ssl'] == expected_db_value, f"Failed for env value: {env_value}"
            
            # 重置 mock 用于下一个测试用例
            mock_session.reset_mock()
            mock_getenv.reset_mock()
    
    @patch('init_sys.DB.get_session')
    @patch('init_sys.os.getenv')
    @patch('init_sys.print_error')
    def test_init_exception_handling(self, mock_print_error, mock_getenv, mock_get_session):
        """测试异常处理"""
        # 模拟数据库会话抛出异常
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")
        
        # 执行初始化
        init_synochat_from_env_if_missing()
        
        # 验证错误被记录且回滚
        mock_print_error.assert_called_once()
        mock_session.rollback.assert_called_once()