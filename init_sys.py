from core.models.user import User
from core.models.article import Article
from core.models.config_management import ConfigManagement
from core.models.feed import Feed
from core.models.message_task import MessageTask
from core.db import Db,DB
from core.config import cfg
from core.auth import pwd_context
import time
import os
from core.print import print_info, print_error


def init_synochat_from_env_if_missing():
    """初始化 Synology Chat 配置（从环境变量到数据库）
    
    如果 DB 中缺失 notify.synochat.* 配置，则从环境变量读取默认值一次性写入 DB
    """
    try:
        session = DB.get_session()
        
        # 检查 webhook 配置是否存在
        webhook_config = session.query(ConfigManagement).filter(
            ConfigManagement.config_key == 'notify.synochat.webhook'
        ).first()
        
        # 如果 webhook 配置不存在，且环境变量存在，则初始化
        if not webhook_config and os.getenv('SYNOLOGY_CHAT_WEBHOOK'):
            print_info("Initializing Synology Chat configuration from environment variables")
            
            # 读取环境变量
            webhook_url = os.getenv('SYNOLOGY_CHAT_WEBHOOK')
            verify_ssl_env = os.getenv('SYNOLOGY_CHAT_VERIFY_SSL', 'true').lower()
            verify_ssl = verify_ssl_env in ('true', '1', 'yes')
            
            # 写入配置到数据库
            configs_to_store = [
                ('notify.synochat.enabled', 'false', 'Synology Chat 通知是否启用'),
                ('notify.synochat.webhook', webhook_url, 'Synology Chat Webhook URL'),
                ('notify.synochat.verify_ssl', str(verify_ssl).lower(), '是否验证 SSL 证书')
            ]
            
            for key, value, description in configs_to_store:
                session.merge(ConfigManagement(
                    config_key=key,
                    config_value=value,
                    description=description
                ))
            
            session.commit()
            print_info("Synology Chat configuration initialized successfully")
            
    except Exception as e:
        print_error(f"Failed to initialize Synology Chat configuration: {str(e)}")
        session.rollback()
def init_user(_db: Db):
    try:
      username,password=os.getenv("USERNAME", "admin"),os.getenv("PASSWORD", "admin@123")
      session=_db.get_session()
      session.add(User(
          id=0,
          username=username,
          password_hash=pwd_context.hash(password),
          ))
      session.commit()
      print_info(f"初始化用户成功,请使用以下凭据登录：{username}")
    except Exception as e:
        # print_error(f"Init error: {str(e)}")
        pass
def sync_models():
     # 同步模型到表结构
         from data_sync import DatabaseSynchronizer
         DB.create_tables()
         time.sleep(3)
         synchronizer = DatabaseSynchronizer(db_url=cfg.get("db",""))
         synchronizer.sync()
         print_info("模型同步完成")

     

 
def init():
    sync_models()
    init_user(DB)
    init_synochat_from_env_if_missing()

if __name__ == '__main__':
    init()