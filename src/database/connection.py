"""
数据库连接管理
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str = None):
        """
        初始化数据库管理器
        
        Args:
            database_url: 数据库连接URL，如果为None则从环境变量获取
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _get_database_url(self) -> str:
        """从环境变量获取数据库连接URL"""
        # 优先使用环境变量
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        
        # 从单独的环境变量构建连接URL
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        username = os.getenv('DB_USERNAME', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        database = os.getenv('DB_NAME', 'trading_system')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _initialize_engine(self):
        """初始化数据库引擎"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("数据库引擎初始化成功")
            
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise
    
    def create_tables(self):
        """创建所有表"""
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("所有数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def get_session_dependency(self) -> Generator[Session, None, None]:
        """用于依赖注入的会话获取器"""
        return self.get_session()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入函数"""
    return db_manager.get_session()


def init_database():
    """初始化数据库（创建表等）"""
    if db_manager.test_connection():
        db_manager.create_tables()
        logger.info("数据库初始化完成")
    else:
        raise Exception("数据库连接失败，无法初始化")


def init_db():
    """初始化数据库的别名函数"""
    return init_database()


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return db_manager
