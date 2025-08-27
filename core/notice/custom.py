import requests
import json


def send_custom_message(webhook_url: str, title: str, text: str) -> None:
    """
    发送自定义Webhook消息（通用JSON格式）
    
    参数:
    - webhook_url: Webhook地址
    - title: 消息标题
    - text: 消息内容
    
    使用标准JSON格式发送消息
    """
    # 组合标题和内容
    message_content = "[%s]\n%s" % (title, text) if title else text
    
    # 使用JSON格式
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({
        "text": message_content
    })
    
    try:
        response = requests.post(
            url=webhook_url,
            headers=headers,
            data=data,
            timeout=10,
            verify=False  # 忽略SSL证书验证
        )
        if response.status_code == 200:
            print("自定义Webhook通知发送成功")
        else:
            print("自定义Webhook通知发送失败: %s - %s" % (response.status_code, response.text))
    except Exception as e:
        print('自定义Webhook通知发送失败: %s' % e)