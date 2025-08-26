import requests
import json


def send_custom_message(webhook_url: str, title: str, text: str) -> None:
    """
    发送自定义Webhook消息，兼容Synology Chat格式
    
    参数:
    - webhook_url: Webhook地址，支持Synology Chat等通用格式
    - title: 消息标题
    - text: 消息内容
    
    对于群晖Chat使用Form格式，其他使用JSON格式
    """
    # 组合标题和内容
    message_content = "[%s]\n%s" % (title, text) if title else text
    
    # 检测是否为群晖Chat URL
    if 'webapi.synology' in webhook_url or '/webapi/entry.cgi' in webhook_url:
        # 群晖Chat需要使用Form格式
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        from urllib.parse import quote
        payload_data = {
            "text": message_content
        }
        data = "payload=" + quote(json.dumps(payload_data))
    else:
        # 其他Webhook使用JSON格式
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