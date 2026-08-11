"""
SQLAlchemy 数据库会话管理
支持 SQLite、PostgreSQL、MySQL
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.common.logger import logger
from src.settings import settings
from src.storage.models import Base


class Database:
    """数据库连接管理"""

    @staticmethod
    def _detect_db_type(url: str) -> str:
        """从连接串推断数据库类型"""
        if url.startswith("sqlite"):
            return "sqlite"
        elif url.startswith("postgresql"):
            return "postgresql"
        elif url.startswith("mysql"):
            return "mysql"
        return "unknown"

    def __init__(self, url: str | None = None):
        """
        初始化数据库连接

        Args:
            url: 数据库连接 URL，默认使用 settings.DATABASE_URL
        """
        self.url = url or settings.DATABASE_URL
        self.db_type = self._detect_db_type(self.url)
        logger.info(f"[Database] 初始化 {self.db_type} 连接")

        # 根据数据库类型配置不同的参数
        if self.db_type == "sqlite":
            # SQLite 需要确保目录存在
            db_path = Path(self.url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self.engine = create_engine(
                self.url,
                echo=False,
                connect_args={"check_same_thread": False},
            )

            # SQLite 启用外键支持
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL 和 MySQL 使用连接池
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
            logger.info(f"数据库表创建成功 ({self.db_type})")
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
    """获取数据库会话生成器"""
    with db.get_session() as session:
        yield session
