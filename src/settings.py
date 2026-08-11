"""
全局配置模块
集中管理所有配置项，封装类型转换与派生属性
"""
import os
from pathlib import Path
from typing import Dict, Optional


class Settings:
    """应用配置集中管理"""

    # ========== 应用基础 ==========
    APP_NAME: str = os.getenv("APP_NAME", "spider_awesome")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENV_MODE: str = os.getenv("ENV_MODE", "dev")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # ========== 服务器 ==========
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # ========== 数据库类型 ==========
    # 可选: sqlite, postgresql, mysql
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")

    # ========== SQLite 配置 ==========
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "var/database/spider_awesome.sqlite3")

    # ========== PostgreSQL 配置 ==========
    PG_HOST: str = os.getenv("PG_HOST", "127.0.0.1")
    PG_PORT: int = int(os.getenv("PG_PORT", "5432"))
    PG_USER: str = os.getenv("PG_USER", "postgres")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "")
    PG_DATABASE: str = os.getenv("PG_DATABASE", "spider_awesome")

    # ========== MySQL 配置 ==========
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "spider_awesome")

    # ========== 数据目录 ==========
    RAW_DATA_DIR: str = os.getenv("RAW_DATA_DIR", "var/raw")

    # ========== 代理 ==========
    HTTP_PROXY: Optional[str] = os.getenv("HTTP_PROXY") or None
    HTTPS_PROXY: Optional[str] = os.getenv("HTTPS_PROXY") or None

    # ========== 日志 ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "var/logs")

    # ========== 调度 ==========
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_PARALLEL: bool = os.getenv("SCHEDULER_PARALLEL", "false").lower() == "true"
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))
    TASK_TIMEOUT: int = int(os.getenv("TASK_TIMEOUT", "300"))
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "60"))

    # ========== 采集器调度时间 ==========
    COLLECTOR_CRON_HOUR: int = int(os.getenv("COLLECTOR_CRON_HOUR", "0"))
    COLLECTOR_CRON_MINUTE: int = int(os.getenv("COLLECTOR_CRON_MINUTE", "0"))

    @property
    def COLLECTOR_CRON(self) -> Dict[str, dict]:
        """
        获取采集器调度配置

        从环境变量读取，格式:
        COLLECTOR_CRON_{NAME}_HOUR=0
        COLLECTOR_CRON_{NAME}_MINUTE=30

        Returns:
            采集器调度配置字典
        """
        from src.collector import list_collectors

        cron_config = {}
        for name in list_collectors():
            hour = int(os.getenv(f"COLLECTOR_CRON_{name.upper()}_HOUR", str(self.COLLECTOR_CRON_HOUR)))
            minute = int(os.getenv(f"COLLECTOR_CRON_{name.upper()}_MINUTE", str(self.COLLECTOR_CRON_MINUTE)))
            cron_config[name] = {"hour": hour, "minute": minute}

        return cron_config

    # ========== 派生属性 ==========
    @property
    def DATABASE_URL(self) -> str:
        """
        根据 DB_TYPE 返回对应的数据库连接 URL

        Returns:
            数据库连接 URL
        """
        if self.DB_TYPE == "sqlite":
            # SQLite 相对路径基于项目根目录
            db_path = Path(self.SQLITE_PATH)
            if not db_path.is_absolute():
                db_path = Path(__file__).parent.parent / db_path
            return f"sqlite:///{db_path}"

        elif self.DB_TYPE == "postgresql":
            return (
                f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}"
                f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
            )

        elif self.DB_TYPE == "mysql":
            return (
                f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            )

        else:
            raise ValueError(f"Unsupported DB_TYPE: {self.DB_TYPE}")

    @property
    def PROXIES(self) -> Optional[dict]:
        """代理配置"""
        if self.HTTP_PROXY or self.HTTPS_PROXY:
            proxies = {}
            if self.HTTP_PROXY:
                proxies["http"] = self.HTTP_PROXY
            if self.HTTPS_PROXY:
                proxies["https"] = self.HTTPS_PROXY
            return proxies
        return None

    @property
    def is_dev(self) -> bool:
        return self.ENV_MODE == "dev"

    @property
    def is_test(self) -> bool:
        return self.ENV_MODE == "test"

    @property
    def is_prod(self) -> bool:
        return self.ENV_MODE == "prod"


# 全局配置实例
settings = Settings()
