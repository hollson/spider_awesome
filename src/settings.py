"""
全局配置模块
集中管理所有配置项，封装类型转换与派生属性
"""

import os


class Settings:
    """应用配置集中管理"""

    # ========== 应用基础 ==========
    APP_NAME: str = os.getenv("APP_NAME", "spider_awesome")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENV_MODE: str = os.getenv("ENV_MODE", "dev")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # ========== 服务器 ==========
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")  # nosec B104
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # ========== 数据库 ==========
    # 统一连接串，支持: sqlite / postgresql / mysql
    # 格式示例:
    #   sqlite:///var/database/spider_awesome.sqlite3
    #   postgresql://user:pass@host:port/dbname
    #   mysql+pymysql://user:pass@host:port/dbname
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///var/database/spider_awesome.sqlite3",
    )

    # ========== 数据目录 ==========
    RAW_DATA_DIR: str = os.getenv("RAW_DATA_DIR", "var/raw")

    # ========== 输出目录 ==========
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "var/output")

    # ========== 缓存目录 ==========
    CACHE_DIR: str = os.getenv("CACHE_DIR", "var/cache")

    # ========== 代理 ==========
    HTTP_PROXY: str | None = os.getenv("HTTP_PROXY") or None
    HTTPS_PROXY: str | None = os.getenv("HTTPS_PROXY") or None

    # ========== 日志 ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "var/logs/spider_awesome.log")
    LOG_RETENTION: int = int(os.getenv("LOG_RETENTION", "7"))

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
    def COLLECTOR_CRON(self) -> dict[str, dict]:  # noqa: N802
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

    @property
    def PROXIES(self) -> dict | None:  # noqa: N802
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
