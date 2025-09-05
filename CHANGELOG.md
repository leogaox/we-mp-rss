# 更新日志

## [1.4.6] - 2024-01-15

### 新增功能
- **群晖Chat (Synology Chat) 通知支持**
  - 新增完整的群晖Chat通知发送器实现
  - 支持 application/x-www-form-urlencoded 格式的消息发送
  - 支持中文字符和Markdown格式消息
  - 可配置SSL证书验证 (支持自签名证书)
  
- **WebUI配置界面**
  - 在系统设置中添加群晖Chat配置页面
  - 支持webhook URL和SSL验证设置
  - 集成测试连接功能（带10秒冷却时间限制）
  - 实时显示连接测试结果
  
- **API端点**
  - `GET /api/v1/settings/synochat` - 获取当前设置
  - `PUT /api/v1/settings/synochat` - 更新设置
  - `POST /api/v1/settings/synochat/test` - 测试连接
  
- **环境变量支持**
  - `SYNOLOGY_CHAT_WEBHOOK` - 群晖Chat webhook URL
  - `SYNOLOGY_CHAT_VERIFY_SSL` - SSL证书验证设置
  - 支持从环境变量初始化数据库配置
  
- **安全特性**
  - Webhook URL脱敏显示（隐藏token参数）
  - API响应中敏感信息脱敏
  - 测试功能冷却时间限制（10秒）
  
### 技术实现
- **后端实现**: `app/notify/synochat_sender.py`
  - 完整的HTTP客户端实现
  - 超时和错误处理
  - 消息构建和格式化
  
- **数据库集成**: `init_sys.py`
  - 环境变量到数据库的自动同步
  - 遵循"WebUI为单一真源"原则
  
- **单元测试**: 20个完整测试用例
  - 消息构建逻辑测试
  - HTTP请求模拟测试
  - 错误处理测试
  - URL脱敏测试
  - 冷却时间逻辑测试
  
### 配置文件
```yaml
notice:
  synology_chat:
    webhook: "https://your-nas.example.com:5001/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=YOUR_TOKEN"
    verify_ssl: true
```

### 文档
- 新增 `SYNOCHAT_SETUP.md` 详细配置指南
- 更新 `README.md` 包含群晖Chat支持说明
- 新增故障排除文档

## [1.4.5] - 2023-12-20

### 修复
- 修复微信公众号内容抓取稳定性问题
- 优化RSS生成性能
- 改进数据库连接池管理

## [1.4.0] - 2023-11-15

### 新增功能
- 新增钉钉通知支持
- 新增飞书通知支持
- 新增微信企业号通知支持
- 改进Web管理界面

### 技术升级
- 升级到Python 3.13.1
- 升级FastAPI到最新版本
- 优化前端构建流程

---

*更新日志遵循[Keep a Changelog](https://keepachangelog.com/)规范*