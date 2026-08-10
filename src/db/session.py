"""
SQLAlchemy 数据库会话管理
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.settings import settings
from src.common.logger import logger
from src.db.models import Base


class Database:
    """数据库连接管理"""

    def __init__(self, url: str = None):
        """
        初始化数据库连接

        Args:
            url: 数据库连接 URL，默认使用 settings.MYSQL_URL
        """
        self.url = url or settings.MYSQL_URL
        self.engine = create_engine(
            self.url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise

    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败，事务回滚: {e}")
            raise
        finally:
            session.close()


# 全局数据库实例
db = Database()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入用的数据库会话生成器"""
    with db.get_session() as session:
        yield session
