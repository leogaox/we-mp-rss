from core.models.message_task import MessageTask
from core.models.feed import Feed
from core.models.article import Article
from core.print import print_success
from core.notice import notice
from dataclasses import dataclass
from core.lax import TemplateParser
from datetime import datetime
from core.log import logger
from core.config import cfg
from bs4 import BeautifulSoup
from core.content_format import format_content
from core.notice import send_synology_message
import re
@dataclass
class MessageWebHook:
    task: MessageTask
    feed:Feed
    articles: list[Article]
    pass

def send_message(hook: MessageWebHook) -> str:
    """
    发送格式化消息
    
    参数:
        hook: MessageWebHook对象，包含任务、订阅源和文章信息
        
    返回:
        str: 格式化后的消息内容
    """
    template = hook.task.message_template if hook.task.message_template else """
### {{feed.mp_name}} 订阅消息：
{% if articles %}
{% for article in articles %}
- [**{{ article.title }}**]({{article.url}}) ({{ article.publish_time }})\n
{% endfor %}
{% else %}
- 暂无文章\n
{% endif %}
    """
    parser = TemplateParser(template)
    data = {
        "feed": hook.feed,
        "articles": hook.articles,
        "task": hook.task,
        'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    message = parser.render(data)
    # 这里可以添加发送消息的具体实现
    print("发送消息:", message)
    notice(hook.task.web_hook_url, hook.task.name, message)
    return message

def call_webhook(hook: MessageWebHook) -> str:
    """
    调用webhook接口发送数据
    
    参数:
        hook: MessageWebHook对象，包含任务、订阅源和文章信息
        
    返回:
        str: 调用结果信息
        
    异常:
        ValueError: 当webhook调用失败时抛出
    """
    template = hook.task.message_template if hook.task.message_template else """{
  "feed": {
    "id": "{{ feed.id }}",
    "name": "{{ feed.mp_name }}"
  },
  "articles": [
    {% if articles %}
     {% for article in articles %}
        {
          "id": "{{ article.id }}",
          "mp_id": "{{ article.mp_id }}",
          "title": "{{ article.title }}",
          "pic_url": "{{ article.pic_url }}",
          "url": "{{ article.url }}",
          "description": "{{ article.description }}",
          "publish_time": "{{ article.publish_time }}"
        }{% if not loop.last %},{% endif %}
      {% endfor %}
    {% endif %}
  ],
  "task": {
    "id": "{{ task.id }}",
    "name": "{{ task.name }}"
  },
  "now": "{{ now }}"
}
"""
    
    # 检查template是否需要content
    template_needs_content = "content" in template.lower()
    
    # 根据content_format处理内容
    content_format = cfg.get("webhook.content_format", "html")
    logger.info(f'Content将以{content_format}格式发送')
    processed_articles = []
    for article in hook.articles:
        if isinstance(article, dict) and "content" in article and article["content"]:
            processed_article = article.copy()
            # 只有template需要content时才进行格式转换
            if template_needs_content:
              processed_article["content"] = format_content(processed_article["content"], content_format)
            processed_articles.append(processed_article)
        else:
            processed_articles.append(article)
    
    data = {
        "feed": hook.feed,
        "articles": processed_articles,
        "task": hook.task,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
   
   # 预处理content字段
    import json
    def process_content(content):
        if content is None:
            return ""
        # 进行JSON转义处理引号
        json_escaped = json.dumps(content, ensure_ascii=False)
        # 去掉外层引号避免重复
        return json_escaped[1:-1]
    
    # 处理articles中的content字段，进行JSON转义
    if "articles" in data:
        for i, article in enumerate(data["articles"]):
            if isinstance(article, dict):
                if "content" in article:
                    data["articles"][i]["content"] = process_content(article["content"])
            elif hasattr(article, "content"):
                setattr(data["articles"][i], "content", process_content(getattr(article, "content")))
    
    parser = TemplateParser(template)
    
    payload = parser.render(data)
    # logger.info(payload)

    # 检查web_hook_url是否为空
    if not hook.task.web_hook_url:
        logger.error("web_hook_url为空")
        return 
    # 发送webhook请求
    import requests
    # print_success(f"发送webhook请求{payload}")
    try:
        response = requests.post(
            hook.task.web_hook_url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return "Webhook调用成功"
    except Exception as e:
        raise ValueError(f"Webhook调用失败: {str(e)}")

def send_synochat_message(hook: MessageWebHook, force_empty: bool = False) -> str:
    """
    发送Synology Chat消息
    
    参数:
        hook: MessageWebHook对象，包含任务、订阅源和文章信息
        force_empty: 是否为强制推送（无新增时推送）
        
    返回:
        str: 发送结果消息
    """
    try:
        # 使用模板解析器格式化消息内容
        if force_empty:
            # 强制推送模板：无新增时发送测试消息
            template = """
【测试】{{task.name}} - 无更新通知
公众号: {{feed.mp_name}}
时间: {{now}}
新增文章数: 0
状态: 联调测试推送
"""
        else:
            template = hook.task.message_template if hook.task.message_template else """
### {{feed.mp_name}} 订阅消息：
{% if articles %}
{% for article in articles %}
- [**{{ article.title }}**]({{article.url}}) ({{ article.publish_time }})\n
{% endfor %}
{% else %}
- 暂无文章\n
{% endif %}
        """
        parser = TemplateParser(template)
        template_data = {
            'feed': hook.feed,
            'articles': hook.articles
        }
        
        # 为强制推送添加额外数据
        if force_empty:
            template_data.update({
                'task': hook.task,
                'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        message_content = parser.render(template_data)
        
        # 发送到Synology Chat
        title = f"【测试】{hook.feed.mp_name} 无更新通知" if force_empty else f"{hook.feed.mp_name} 更新通知"
        send_synology_message(
            webhook_url=hook.task.web_hook_url,
            title=title,
            text=message_content
        )
        
        return "Synology Chat消息发送成功"
    except Exception as e:
        raise ValueError(f"Synology Chat发送失败: {str(e)}")

def web_hook(hook:MessageWebHook, force:bool=False):
    """
    根据消息类型路由到对应的处理函数
    
    参数:
        hook: MessageWebHook对象，包含任务、订阅源和文章信息
        force: 是否强制推送（无新增时也推送）
        
    返回:
        对应处理函数的返回结果
        
    异常:
        ValueError: 当消息类型未知时抛出
    """
    try:
        # 调试日志：记录进入时的消息类型和参数
        logger.debug(f"web_hook called with message_type: {hook.task.message_type}, type: {type(hook.task.message_type)}, force: {force}")
        
        # 保存原始消息类型用于后续验证
        original_message_type = hook.task.message_type
        
        # 处理articles参数，兼容Article对象和字典类型
        processed_articles = []
        if len(hook.articles)<=0:
            # raise ValueError("没有更新到文章")
            logger.warning("没有更新到文章")
            
            # 强制推送逻辑：无新增时也推送Synology Chat消息
            from core.config import cfg
            config_value = cfg.get("debug_force_notify_on_empty")
            debug_force = str(config_value).lower() in ("true", "1", "yes", "on") if config_value is not None else False
            logger.debug(f"Force push config - config_value: {config_value}, debug_force: {debug_force}, force_param: {force}")
            
            if (force or debug_force) and hook.task.message_type == 2:
                force_source = "parameter" if force else "config"
                logger.info(f"force_push_on_empty=true, source={force_source}, task={hook.task.name}, feed={hook.feed.mp_name}")
                logger.debug(f"Routing -> synochat, Force empty notify -> True")
                return send_synochat_message(hook, force_empty=True)
            
            return 
        for article in hook.articles:
            if isinstance(article, dict):
                # 如果是字典类型，直接使用
                processed_article = {
                    field.name: (
                        datetime.fromtimestamp(article[field.name]).strftime("%Y-%m-%d %H:%M:%S")
                        if field.name == "publish_time" and field.name in article
                        else article.get(field.name, "")
                    )
                    for field in Article.__table__.columns
                }
            else:
                # 如果是Article对象，使用getattr获取属性
                processed_article = {
                    field.name: (
                        datetime.fromtimestamp(getattr(article, field.name)).strftime("%Y-%m-%d %H:%M:%S")
                        if field.name == "publish_time"
                        else getattr(article, field.name)
                    )
                    for field in Article.__table__.columns
                }
            processed_articles.append(processed_article)
        
        hook.articles = processed_articles
        
        # 验证消息类型是否在文章处理过程中被意外修改
        if hook.task.message_type != original_message_type:
            logger.warning(f"Message type changed during processing: {original_message_type} -> {hook.task.message_type}")
            # 恢复原始消息类型
            hook.task.message_type = original_message_type
        
        # 调试日志：记录路由前的消息类型
        logger.debug(f"Routing message_type: {hook.task.message_type}, type: {type(hook.task.message_type)}")
        
        # 验证消息类型是否为有效整数
        try:
            message_type = int(hook.task.message_type)
        except (ValueError, TypeError):
            logger.error(f"Invalid message_type: {hook.task.message_type}, type: {type(hook.task.message_type)}")
            raise ValueError(f"无效的消息类型: {hook.task.message_type}")
        
        if message_type == 0:  # 发送消息
            logger.debug("Routing -> message")
            return send_message(hook)
        elif message_type == 1:  # 调用webhook
            logger.debug("Routing -> webhook")
            return call_webhook(hook)
        elif message_type == 2:  # Synology Chat
            logger.debug("Routing -> synochat")
            return send_synochat_message(hook)
        else:
            raise ValueError(f"未知的消息类型: {message_type}")
    except Exception as e:
        raise ValueError(f"处理消息时出错: {str(e)}")