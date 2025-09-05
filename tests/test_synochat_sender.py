import json
from unittest.mock import patch, MagicMock
import pytest
import requests
from app.notify.synochat_sender import build_text, send, SendResult


class TestBuildText:
    """测试 build_text 函数"""
    
    def test_build_text_with_feeds(self):
        """测试有公众号列表的情况"""
        feeds = ["公众号A", "公众号B"]
        result = build_text(feeds)
        expected = "**WeRSS 更新公众号**\n• 公众号A\n• 公众号B"
        assert result == expected
    
    def test_build_text_empty_feeds(self):
        """测试空公众号列表的情况"""
        result = build_text([])
        expected = "**WeRSS 更新公众号**"
        assert result == expected
    
    def test_build_text_single_feed(self):
        """测试单个公众号的情况"""
        result = build_text(["测试公众号"])
        expected = "**WeRSS 更新公众号**\n• 测试公众号"
        assert result == expected


class TestSendFunction:
    """测试 send 函数"""
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_success(self, mock_post):
        """测试成功发送消息"""
        # 模拟成功的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "success"
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证请求参数
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['url'] == "https://example.com/webhook"
        assert "payload=" in kwargs['data']
        assert kwargs['timeout'] == 10
        assert kwargs['verify'] is True
        
        # 验证返回结果
        assert result['status_code'] == 200
        assert result['snippet'] == "success"
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_with_chinese_and_newlines(self, mock_post):
        """测试包含中文和换行符的消息"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "success"
        mock_post.return_value = mock_response
        
        text = "**WeRSS 更新公众号**\n• 中文测试\n• 另一个公众号"
        result = send(text, "https://example.com/webhook")
        
        # 验证请求体包含正确的中文和换行符
        args, kwargs = mock_post.call_args
        payload_data = kwargs['data']
        assert "payload=" in payload_data
        
        # 提取并验证 JSON 内容
        from urllib.parse import unquote
        payload_json = unquote(payload_data.split("payload=", 1)[1])
        payload_dict = json.loads(payload_json)
        assert payload_dict['text'] == text
        assert "\\n" in payload_json  # 确保换行符被正确编码
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_verify_ssl_false(self, mock_post):
        """测试 verify_ssl=False"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "success"
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook", verify_ssl=False)
        
        # 验证 verify=False
        args, kwargs = mock_post.call_args
        assert kwargs['verify'] is False
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_timeout(self, mock_post):
        """测试超时情况"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证超时处理
        assert result['status_code'] == 0
        assert "timeout" in result['snippet'].lower()
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_network_error(self, mock_post):
        """测试网络错误情况"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证网络错误处理
        assert result['status_code'] == 0
        assert "failed" in result['snippet'].lower()
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_5xx_error(self, mock_post):
        """测试 5xx 错误"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error" * 10  # 长文本测试片段截取
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证 5xx 错误处理
        assert result['status_code'] == 500
        assert len(result['snippet']) <= 200  # 确保片段被截断
        assert "Internal Server Error" in result['snippet']
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_401_error(self, mock_post):
        """测试 401 未授权错误"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证 401 错误处理
        assert result['status_code'] == 401
        assert "Unauthorized" in result['snippet']
    
    @patch('app.notify.synochat_sender.requests.post')
    def test_send_403_error(self, mock_post):
        """测试 403 禁止访问错误"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response
        
        result = send("测试消息", "https://example.com/webhook")
        
        # 验证 403 错误处理
        assert result['status_code'] == 403
        assert "Forbidden" in result['snippet']


class TestSendResultType:
    """测试 SendResult 类型定义"""
    
    def test_send_result_structure(self):
        """验证 SendResult 的结构"""
        result: SendResult = {
            "status_code": 200,
            "snippet": "success"
        }
        
        assert isinstance(result, dict)
        assert 'status_code' in result
        assert 'snippet' in result
        assert isinstance(result['status_code'], int)
        assert isinstance(result['snippet'], str)