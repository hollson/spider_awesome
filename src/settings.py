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
    APP_NAME: str = os.getenv("APP_NAME", "data-collector")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENV_MODE: str = os.getenv("ENV_MODE", "dev")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # ========== 服务器 ==========
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # ========== MySQL ==========
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "data_collector")

    # ========== Redis ==========
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD") or None
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # ========== 日志 ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")

    # ========== 代理 ==========
    HTTP_PROXY: Optional[str] = os.getenv("HTTP_PROXY") or None
    HTTPS_PROXY: Optional[str] = os.getenv("HTTPS_PROXY") or None

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
    def MYSQL_URL(self) -> str:
        """数据库连接 URL"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

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
