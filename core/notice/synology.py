import requests
import json
from urllib.parse import quote


def send_synology_message(webhook_url: str, title: str, text: str) -> None:
    """
    发送群晖 Chat 消息
    
    参数:
    - webhook_url: 群晖 Chat Webhook地址
    - title: 消息标题
    - text: 消息内容
    
    群晖Chat使用Form格式发送消息
    """
    # 组合标题和内容
    message_content = "[%s]\n%s" % (title, text) if title else text
    
    # 群晖Chat需要使用Form格式
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload_data = {
        "text": message_content
    }
    data = "payload=" + quote(json.dumps(payload_data))
    
    try:
        response = requests.post(
            url=webhook_url,
            headers=headers,
            data=data,
            timeout=10,
            verify=False  # 忽略SSL证书验证
        )
        if response.status_code == 200:
            print("群晖Chat通知发送成功")
        else:
            print("群晖Chat通知发送失败: %s - %s" % (response.status_code, response.text))
    except Exception as e:
        print('群晖Chat通知发送失败: %s' % e)