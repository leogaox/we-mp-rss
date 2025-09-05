# 群晖Chat (Synology Chat) 故障排除指南

## 常见问题与解决方案

### 1. 连接测试失败

#### 症状
- WebUI测试连接返回错误
- API测试返回非200状态码
- 日志中出现连接错误

#### 解决方案

**SSL证书错误**
```bash
# 如果是自签名证书，设置 verify_ssl=false
SYNOLOGY_CHAT_VERIFY_SSL=false

# 或者在 config.yaml 中设置
notice:
  synology_chat:
    verify_ssl: false
```

**连接超时**
- 检查NAS网络可达性
- 确认防火墙允许出站连接
- 默认超时时间：10秒

**认证失败**
- 检查webhook token是否正确
- 确认webhook未被禁用
- 在群晖Chat中重新生成webhook

### 2. Webhook URL格式错误

#### 症状
- "无效的webhook URL"错误
- 消息发送失败但连接测试成功

#### 正确格式
```
https://[NAS地址]:[端口]/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=[您的token]
```

#### 验证步骤
1. 在浏览器中打开webhook URL
2. 应该返回JSON响应（即使认证失败）
3. 如果返回404，检查URL格式

### 3. 消息格式问题

#### 症状
- 消息发送成功但显示乱码
- 消息格式不正确

#### 解决方案
- 确保使用 `application/x-www-form-urlencoded` Content-Type
- 中文消息需要正确编码
- 支持Markdown格式：`**粗体**`、`*斜体*`、`- 列表`

### 4. 冷却时间限制

#### 症状
- "操作过于频繁，请10秒后再试"
- 测试连接按钮禁用

#### 解决方案
- 测试功能有10秒冷却时间
- 这是防止滥用的安全措施
- 等待10秒后重试

### 5. 环境变量不生效

#### 症状
- 设置了环境变量但配置未更新
- WebUI中显示旧配置

#### 解决方案
- 环境变量只在首次启动时初始化到数据库
- 后续修改需要通过WebUI或API更新
- 重启服务使环境变量生效

## 错误代码说明

| 错误代码 | 说明 | 解决方案 |
|---------|------|----------|
| 400 | 请求格式错误 | 检查消息格式和Content-Type |
| 401 | 认证失败 | 检查webhook token是否正确 |
| 403 | 权限不足 | 检查webhook是否被禁用 |
| 404 | URL不存在 | 检查webhook URL格式 |
| 500 | 服务器错误 | 检查群晖Chat服务状态 |
| 0 | 网络错误 | 检查网络连接和防火墙 |

## 日志调试

### 启用详细日志
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### 查看日志
```bash
# 查看实时日志
tail -f logs/app.log

# 搜索Synology Chat相关日志
grep -i "synology\|synochat" logs/app.log
```

### 常见日志消息

**连接成功**
```
INFO - Synology Chat message sent successfully, status: 200
```

**SSL错误**
```
ERROR - SSLError: certificate verify failed
```

**超时错误**
```
ERROR - Timeout: Request timeout after 10 seconds
```

**网络错误**
```
ERROR - ConnectionError: Failed to connect to NAS
```

## 网络诊断

### 测试网络连通性
```bash
# 测试NAS端口连通性
telnet your-nas.example.com 5001

# 测试HTTPS连接
curl -v https://your-nas.example.com:5001

# 测试webhook（不发送消息）
curl -I "您的webhook URL"
```

### 防火墙检查
- 确认出站HTTPS (端口5001) 允许
- 检查本地防火墙设置
- 检查NAS防火墙设置

## 性能问题

### 消息发送慢
- 检查网络延迟
- 考虑增加超时时间（需要修改代码）
- 检查NAS性能

### 大量消息队列
- 消息发送是同步操作
- 大量消息可能导致阻塞
- 考虑使用异步发送（需要修改代码）

## 配置验证

### 验证当前配置
```bash
# 通过API获取当前设置
curl http://localhost:8001/api/v1/settings/synochat
```

### 验证环境变量
```bash
# 检查环境变量是否设置
echo $SYNOLOGY_CHAT_WEBHOOK
echo $SYNOLOGY_CHAT_VERIFY_SSL
```

### 验证数据库配置
```sql
-- 查询数据库中的配置
SELECT * FROM config WHERE config_key LIKE '%synology%' OR config_key LIKE '%synochat%';
```

## 恢复默认设置

### 通过WebUI
1. 访问系统设置 → 通知设置
2. 清空群晖Chat配置
3. 保存设置

### 通过数据库
```sql
-- 删除群晖Chat配置
DELETE FROM config WHERE config_key = 'notice.synology_chat.webhook';
DELETE FROM config WHERE config_key = 'notice.synology_chat.verify_ssl';
```

### 通过环境变量
```bash
# 取消设置环境变量
unset SYNOLOGY_CHAT_WEBHOOK
unset SYNOLOGY_CHAT_VERIFY_SSL

# 重启服务使更改生效
```

## 联系支持

如果以上解决方案都无法解决问题：

1. 收集日志文件
2. 记录错误信息
3. 提供webhook URL（脱敏后）
4. 在GitHub提交Issue

**注意**: 提交Issue时请不要包含真实的webhook URL或token。