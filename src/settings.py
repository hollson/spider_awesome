"""
全局配置模块
集中管理所有配置项，封装类型转换与派生属性
"""
import os
from pathlib import Path
from typing import Optional


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
    COLLECTOR_CRON_HOUR: int = int(os.getenv("COLLECTOR_CRON_HOUR", "0"))
    COLLECTOR_CRON_MINUTE: int = int(os.getenv("COLLECTOR_CRON_MINUTE", "0"))

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
