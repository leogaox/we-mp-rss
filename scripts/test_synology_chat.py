#!/usr/bin/env python3
"""
Synology Chat Webhook 测试脚本
从环境变量 CUSTOM_WEBHOOK 读取 URL 并测试连接
"""

import os
import sys
import argparse
import requests
import json
from urllib.parse import urlparse, quote

def mask_url(url):
    """掩码显示 URL，保护 token 信息"""
    parsed = urlparse(url)
    if parsed.query:
        # 显示协议和域名部分，掩码查询参数
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return f"{base_url}?***masked***"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def main():
    parser = argparse.ArgumentParser(description="测试 Synology Chat Webhook 连接")
    parser.add_argument("--json", action="store_true", default=True, help="使用 JSON 格式 (默认)")
    parser.add_argument("--form", action="store_true", help="使用 Form 格式")
    args = parser.parse_args()
    
    # 读取环境变量
    webhook_url = os.getenv("CUSTOM_WEBHOOK")
    if not webhook_url:
        print("错误: 未设置 CUSTOM_WEBHOOK 环境变量")
        print("请设置: export CUSTOM_WEBHOOK='你的webhook_url'")
        sys.exit(2)
    
    print(f"测试 URL: {mask_url(webhook_url)}")
    
    # 准备测试数据
    test_data = {"text": "WeRSS 测试：JSON" if args.json else "WeRSS 测试：FORM"}
    
    try:
        if args.form:
            # Form 格式
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            payload_data = f"payload={quote(json.dumps(test_data))}"
            response = requests.post(
                webhook_url, 
                data=payload_data, 
                headers=headers, 
                timeout=10
            )
        else:
            # JSON 格式 (默认)
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                webhook_url, 
                json=test_data, 
                headers=headers, 
                timeout=10
            )
        
        # 输出结果
        response_text = response.text[:500] + ("..." if len(response.text) > 500 else "")
        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应内容: {response_text}")
        
        # 返回码: 2xx 成功, 其他失败
        sys.exit(0 if 200 <= response.status_code < 300 else 1)
        
    except Exception as e:
        print(f"请求失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()