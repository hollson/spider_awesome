"""
代理池管理器
支持多个代理轮换使用，自动检测代理有效性

默认关闭，需在配置中启用：
  PROXY_POOL_ENABLED=true
"""

import random
import threading
import time
from dataclasses import dataclass
from enum import StrEnum

import requests

from src.common.logger import logger


class ProxyStrategy(StrEnum):
    """代理轮换策略"""
    RANDOM = "random"           # 随机选择
    ROUND_ROBIN = "round_robin"  # 轮询
    LEAST_USED = "least_used"   # 最少使用


@dataclass
class ProxyInfo:
    """代理信息"""
    url: str
    username: str | None = None
    password: str | None = None
    is_valid: bool = True
    last_check: float = 0.0
    fail_count: int = 0
    success_count: int = 0

    def to_dict(self) -> dict[str, str]:
        """转换为 requests 代理格式"""
        proxies = {}
        if self.url:
            if self.url.startswith("socks"):
                proxies["http"] = self.url
                proxies["https"] = self.url
            else:
                proxies["http"] = self.url
                proxies["https"] = self.url
        return proxies

    @property
    def auth(self) -> tuple[str, str] | None:
        """获取认证信息"""
        if self.username and self.password:
            return (self.username, self.password)
        return None


class ProxyPool:
    """
    代理池管理器

    功能：
    - 支持多个代理轮换使用
    - 支持随机/轮询/最少使用三种策略
    - 自动检测代理有效性
    - 线程安全
    """

    def __init__(
        self,
        proxies: list[str] | None = None,
        strategy: ProxyStrategy = ProxyStrategy.RANDOM,
        check_interval: int = 300,
        timeout: int = 10,
    ):
        """
        初始化代理池

        Args:
            proxies: 代理地址列表，格式: http://host:port 或 user:pass@host:port
            strategy: 轮换策略
            check_interval: 有效性检测间隔（秒）
            timeout: 检测超时时间（秒）
        """
        self.strategy = strategy
        self.check_interval = check_interval
        self.timeout = timeout
        self._lock = threading.Lock()
        self._index = 0  # 轮询索引

        # 解析代理列表
        self._proxies: list[ProxyInfo] = []
        if proxies:
            for proxy_str in proxies:
                proxy_info = self._parse_proxy(proxy_str)
                if proxy_info:
                    self._proxies.append(proxy_info)

        logger.info(f"[ProxyPool] 初始化完成: {len(self._proxies)} 个代理, 策略: {strategy.value}")

    def _parse_proxy(self, proxy_str: str) -> ProxyInfo | None:
        """
        解析代理字符串

        支持格式：
        - http://host:port
        - http://user:pass@host:port
        - socks5://host:port
        - user:pass@host:port
        """
        if not proxy_str or not proxy_str.strip():
            return None

        proxy_str = proxy_str.strip()
        username = None
        password = None

        # 处理带认证的代理
        if "@" in proxy_str:
            scheme_end = proxy_str.find("://")
            if scheme_end != -1:
                scheme = proxy_str[:scheme_end + 3]
                rest = proxy_str[scheme_end + 3:]
            else:
                scheme = "http://"
                rest = proxy_str

            if "@" in rest:
                auth_part, host_part = rest.rsplit("@", 1)
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
                proxy_str = scheme + host_part

        return ProxyInfo(
            url=proxy_str,
            username=username,
            password=password,
        )

    def get_proxy(self) -> dict[str, str] | None:
        """
        获取一个可用代理

        Returns:
            代理配置字典，格式: {"http": "http://...", "https": "http://..."}
            没有可用代理时返回 None
        """
        with self._lock:
            # 过滤有效代理
            valid_proxies = [p for p in self._proxies if p.is_valid]

            if not valid_proxies:
                logger.debug("[ProxyPool] 没有可用代理，使用直连")
                return None

            if self.strategy == ProxyStrategy.RANDOM:
                proxy = random.choice(valid_proxies)
            elif self.strategy == ProxyStrategy.ROUND_ROBIN:
                proxy = valid_proxies[self._index % len(valid_proxies)]
                self._index += 1
            elif self.strategy == ProxyStrategy.LEAST_USED:
                proxy = min(valid_proxies, key=lambda p: p.success_count)
            else:
                proxy = random.choice(valid_proxies)

            logger.debug(f"[ProxyPool] 使用代理: {proxy.url}")
            return proxy.to_dict()

    def report_success(self, proxy_dict: dict[str, str]) -> None:
        """报告代理使用成功"""
        with self._lock:
            proxy_url = proxy_dict.get("http") or proxy_dict.get("https")
            for p in self._proxies:
                if p.url == proxy_url:
                    p.success_count += 1
                    p.fail_count = 0
                    p.is_valid = True
                    break

    def report_failure(self, proxy_dict: dict[str, str]) -> None:
        """报告代理使用失败"""
        with self._lock:
            proxy_url = proxy_dict.get("http") or proxy_dict.get("https")
            for p in self._proxies:
                if p.url == proxy_url:
                    p.fail_count += 1
                    if p.fail_count >= 3:
                        p.is_valid = False
                        logger.warning(f"[ProxyPool] 代理已失效: {p.url}")
                    break

    def check_proxy(self, proxy_info: ProxyInfo) -> bool:
        """
        检测代理有效性

        Args:
            proxy_info: 代理信息

        Returns:
            是否有效
        """
        test_url = "http://httpbin.org/ip"
        try:
            proxies = proxy_info.to_dict()
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=self.timeout,
                auth=proxy_info.auth,
            )
            is_valid = response.status_code == 200
            proxy_info.is_valid = is_valid
            proxy_info.last_check = time.time()
            if is_valid:
                logger.debug(f"[ProxyPool] 代理有效: {proxy_info.url}")
            else:
                logger.debug(f"[ProxyPool] 代理无效: {proxy_info.url}")
            return is_valid
        except Exception as e:
            logger.debug(f"[ProxyPool] 代理检测失败: {proxy_info.url} - {e}")
            proxy_info.is_valid = False
            proxy_info.last_check = time.time()
            return False

    def check_all(self) -> dict[str, bool]:
        """
        检测所有代理有效性

        Returns:
            代理地址 -> 是否有效 的映射
        """
        results = {}
        for proxy_info in self._proxies:
            results[proxy_info.url] = self.check_proxy(proxy_info)
        return results

    def add_proxy(self, proxy_str: str) -> None:
        """动态添加代理"""
        proxy_info = self._parse_proxy(proxy_str)
        if proxy_info:
            with self._lock:
                # 检查是否已存在
                existing = [p for p in self._proxies if p.url == proxy_info.url]
                if not existing:
                    self._proxies.append(proxy_info)
                    logger.info(f"[ProxyPool] 添加代理: {proxy_str}")

    def remove_proxy(self, proxy_str: str) -> None:
        """动态移除代理"""
        with self._lock:
            self._proxies = [p for p in self._proxies if p.url != proxy_str]
            logger.info(f"[ProxyPool] 移除代理: {proxy_str}")

    @property
    def proxy_count(self) -> int:
        """代理数量"""
        return len(self._proxies)

    @property
    def valid_count(self) -> int:
        """有效代理数量"""
        return len([p for p in self._proxies if p.is_valid])


# 全局代理池实例
_proxy_pool: ProxyPool | None = None


def get_proxy_pool(
    proxies: list[str] | None = None,
    strategy: str = "random",
) -> ProxyPool:
    """
    获取全局代理池实例

    Args:
        proxies: 代理列表
        strategy: 轮换策略

    Returns:
        代理池实例
    """
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool(
            proxies=proxies,
            strategy=ProxyStrategy(strategy),
        )
    return _proxy_pool


def reset_proxy_pool() -> None:
    """重置全局代理池"""
    global _proxy_pool
    _proxy_pool = None
