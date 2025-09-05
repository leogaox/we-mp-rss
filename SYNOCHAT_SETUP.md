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

### 方法1: 环境变量配置（首次初始化）
```bash
export SYNOLOGY_CHAT_WEBHOOK="您的群晖Chat webhook URL"
export SYNOLOGY_CHAT_VERIFY_SSL="true"  # 或 "false" 用于自签名证书
```

应用启动时会自动将环境变量同步到数据库，遵循"WebUI为单一真源"原则。

### 方法2: 配置文件配置
在 `config.yaml` 中添加：
```yaml
notice:
  synology_chat:
    webhook: "您的群晖Chat webhook URL"
    verify_ssl: true  # 或 false 用于自签名证书
```

### 方法3: WebUI界面配置（推荐）
1. 访问Web管理界面 → 系统设置 → 通知设置
2. 找到"群晖Chat"配置部分
3. 输入webhook URL和SSL验证设置
4. 点击"测试连接"验证配置
5. 保存设置

### 方法4: 使用通用webhook配置
项目会自动识别群晖Chat格式的URL，您也可以直接使用：
```yaml
notice:
  webhook: "您的群晖Chat webhook URL"
```

## 4. API接口

### 获取当前设置
```bash
GET /api/v1/settings/synochat
```

响应示例：
```json
{
  "webhook": "https://your-nas.example.com:5001/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=abc123",
  "verify_ssl": true,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 更新设置
```bash
PUT /api/v1/settings/synochat
Content-Type: application/json

{
  "webhook": "新的webhook URL",
  "verify_ssl": false
}
```

### 测试连接
```bash
POST /api/v1/settings/synochat/test
Content-Type: application/json

{
  "webhook": "要测试的webhook URL",
  "verify_ssl": true
}
```

响应包含测试结果和状态码。

## 5. 测试群晖Chat连接

### 使用WebUI测试
1. 在通知设置页面点击"测试连接"按钮
2. 系统会发送测试消息到配置的webhook
3. 查看测试结果和响应状态

### 使用API测试
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"webhook":"您的webhook URL","verify_ssl":true}' \
  http://localhost:8001/api/v1/settings/synochat/test
```

### 手动测试：
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "payload={\"text\": \"WeRSS测试消息\"}" \
  "您的群晖Chat webhook URL"
```

## 6. 支持的消息格式

群晖Chat支持以下格式的消息：

### 基本文本消息：
```json
{
  "text": "您的消息内容"
}
```

### 带格式的消息：
```json
{
  "text": "**WeRSS 更新公众号**\\n• 公众号A\\n• 公众号B"
}
```

### 公众号更新通知格式：
```
**WeRSS 更新公众号**
• 公众号名称1
• 公众号名称2
• 公众号名称3
```

## 7. 故障排除

### 常见问题：

1. **SSL证书错误**
   - 如果使用自签名证书，设置 `verify_ssl: false`
   - 生产环境建议使用有效SSL证书
   - 错误信息: `SSLError` 或证书验证失败

2. **连接超时**
   - 检查NAS的网络可达性
   - 确认防火墙设置允许外部访问
   - 默认超时时间: 10秒
   - 错误信息: `Timeout` 或连接超时

3. **认证失败**
   - 检查webhook token是否正确
   - 确认webhook未被禁用或重新生成
   - 错误信息: HTTP 401 或 403

4. **格式错误**
   - 群晖Chat要求使用Form格式，而不是纯JSON
   - 确保使用 `application/x-www-form-urlencoded` Content-Type
   - 错误信息: HTTP 400 或格式不正确

5. **冷却时间限制**
   - 测试功能有10秒冷却时间，防止滥用
   - 错误信息: "操作过于频繁，请10秒后再试"

6. **Webhook URL格式错误**
   - 确保URL包含正确的API路径和参数
   - 格式: `https://nas-address:port/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=YOUR_TOKEN`

## 8. 安全注意事项

- 不要将webhook URL提交到版本控制系统
- 使用环境变量或配置文件管理敏感信息
- 定期轮换webhook token
- 限制webhook的访问权限
- WebUI中会脱敏显示webhook URL（隐藏token参数）
- API响应中也会脱敏敏感信息

## 9. 高级配置

### 消息模板自定义：
您可以在 `app/notify/synochat_sender.py` 中修改 `build_text()` 函数来自定义消息格式：

```python
def build_text(feeds):
    """构建群晖Chat消息内容"""
    if not feeds:
        return "**WeRSS 更新公众号**"
    
    message = "**WeRSS 更新公众号**\\n"
    for feed in feeds:
        message += f"• {feed}\\n"
    return message.strip()
```

### 多个通知渠道：
项目支持同时配置多个通知渠道，包括：
- 群晖Chat (Synology Chat)
- 钉钉 (DingTalk) 
- 飞书 (Feishu)
- 微信企业号 (WeChat Work)
- 自定义webhook

只需在配置中指定不同的webhook URL即可。

### 调试模式：
设置环境变量开启详细日志：
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

## 10. 版本要求

- We-MP-RSS 版本: 1.4.6+
- Python 版本: 3.13.1+
- Synology Chat 套件: 2.0+

## 11. 更新日志

### v1.4.6 (2024-01-15)
- 新增群晖Chat通知支持
- 添加WebUI配置界面
- 实现API端点用于设置管理
- 添加完整的单元测试覆盖
- 支持环境变量初始化
- 添加冷却时间限制防止滥用

如需更多帮助，请参考项目文档或提交Issue。