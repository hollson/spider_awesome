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
    PROXY_POOL_API: str | None = os.getenv("PROXY_POOL_API") or None  # 代理 API 地址
    PROXY_POOL_LIST: str = os.getenv("PROXY_POOL_LIST", "")  # 自定义代理池：一个=静态，多个=轮换，空=直连
    PROXY_POOL_STRATEGY: str = os.getenv("PROXY_POOL_STRATEGY", "random")  # random/round_robin/least_used

    # ========== 请求间隔控制（防反爬）==========
    # 注意：这是每次 HTTP 请求的间隔，分页采集会累积延迟，严重影响效率
    # 建议：默认禁用（MIN=MAX=0），只在遇到反爬时按需开启
    REQUEST_DELAY_MIN: int = int(os.getenv("REQUEST_DELAY_MIN", "0"))  # 毫秒
    REQUEST_DELAY_MAX: int = int(os.getenv("REQUEST_DELAY_MAX", "0"))  # 毫秒

    # ========== 浏览器渲染 ==========
    BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # 毫秒

    # ========== 日志 ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "var/logs/spider_awesome.log")
    LOG_RETENTION: int = int(os.getenv("LOG_RETENTION", "7"))

    # ========== 调度（全局默认值）==========
    # 注意：采集器调度配置在 src/collector/source_define.py 中
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_PARALLEL: bool = os.getenv("SCHEDULER_PARALLEL", "false").lower() == "true"
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))
    TASK_TIMEOUT: int = int(os.getenv("TASK_TIMEOUT", "300"))
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "60"))

    @property
    def PROXIES(self) -> dict | None:  # noqa: N802
        """代理配置（从 PROXY_POOL_LIST 读取第一个）"""
        if self.PROXY_POOL_LIST:
            proxies = self.PROXY_POOL_LIST.split("|")[0].strip()
            if proxies:
                return {"http": proxies, "https": proxies}
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
