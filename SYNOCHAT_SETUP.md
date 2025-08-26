# 群晖Chat (Synology Chat) 设置指南

## 1. 在群晖NAS中设置Chat机器人

### 步骤1: 安装Synology Chat套件
1. 登录群晖DSM管理界面
2. 打开"套件中心"
3. 搜索并安装"Synology Chat"套件

### 步骤2: 创建 incoming webhook
1. 打开Synology Chat应用
2. 创建一个新的频道或选择现有频道
3. 点击频道设置 → 集成 → 创建 incoming webhook
4. 设置webhook名称和描述
5. 复制生成的webhook URL

## 2. 群晖Chat webhook URL格式

群晖Chat的webhook URL格式通常为：
```
https://[您的NAS地址]:[端口]/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=[您的token]
```

示例：
```
https://your-nas.example.com:5001/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=abc123def456
```

## 3. 在We-MP-RSS中配置群晖Chat

### 方法1: 环境变量配置
```bash
export SYNOLOGY_CHAT_WEBHOOK="您的群晖Chat webhook URL"
```

### 方法2: 配置文件配置
在 `config.yaml` 中添加：
```yaml
notice:
  synology_chat:
    webhook: "您的群晖Chat webhook URL"
```

### 方法3: 使用通用webhook配置
项目会自动识别群晖Chat格式的URL，您也可以直接使用：
```yaml
notice:
  webhook: "您的群晖Chat webhook URL"
```

## 4. 测试群晖Chat连接

### 使用测试脚本：
```bash
# 设置环境变量
export CUSTOM_WEBHOOK="您的群晖Chat webhook URL"

# 测试连接
python scripts/test_synology_chat.py

# 或者使用Form格式测试
python scripts/test_synology_chat.py --form
```

### 手动测试：
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "payload={\"text\": \"测试消息\"}" \
  "您的群晖Chat webhook URL"
```

## 5. 支持的消息格式

群晖Chat支持以下格式的消息：

### 基本文本消息：
```json
{
  "text": "您的消息内容"
}
```

### 带标题的消息：
```json
{
  "text": "[标题]\\n内容"
}
```

## 6. 故障排除

### 常见问题：

1. **SSL证书错误**
   - 如果使用自签名证书，需要在代码中设置 `verify=False`
   - 生产环境建议使用有效SSL证书

2. **连接超时**
   - 检查NAS的网络可达性
   - 确认防火墙设置允许外部访问

3. **认证失败**
   - 检查webhook token是否正确
   - 确认webhook未被禁用或重新生成

4. **格式错误**
   - 群晖Chat要求使用Form格式，而不是纯JSON
   - 确保使用 `application/x-www-form-urlencoded` Content-Type

## 7. 安全注意事项

- 不要将webhook URL提交到版本控制系统
- 使用环境变量或配置文件管理敏感信息
- 定期轮换webhook token
- 限制webhook的访问权限

## 8. 高级配置

### 消息模板：
您可以在 `core/notice/custom.py` 中自定义消息格式：

```python
# 自定义消息格式
message_content = f"🚀 [WeRSS通知]\\n📖 {title}\\n📝 {text}\\n⏰ {datetime.now()}"
```

### 多个通知渠道：
项目支持同时配置多个通知渠道，包括：
- 群晖Chat (Synology Chat)
- 钉钉 (DingTalk) 
- 飞书 (Feishu)
- 微信企业号 (WeChat Work)
- 自定义webhook

只需在配置中指定不同的webhook URL即可。