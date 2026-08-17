"""
代理池管理器
支持多个代理轮换使用，自动检测代理有效性

配置方式：
- PROXY_POOL_LIST：自定义代理池（一个=静态，多个=轮换）
- PROXY_POOL_API：从 API 获取代理列表

支持的代理 API 格式：
- 纯文本：每行一个 IP:PORT
- JSON 数组：["ip:port", ...]
- JSON 对象：{"data": ["ip:port", ...]} 或 {"ip": "ip", "port": port}
"""

from __future__ import annotations

import json
import random
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import requests

from app.common.logger import logger


class ProxyStrategy(StrEnum):
    """代理轮换策略"""

    RANDOM = "random"  # 随机选择
    ROUND_ROBIN = "round_robin"  # 轮询
    LEAST_USED = "least_used"  # 最少使用


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


class ProxyAPIClient:
    """
    代理 API 客户端

    支持多种 API 格式：
    - 纯文本：每行一个 IP:PORT
    - JSON 数组：["ip:port", ...]
    - JSON 对象：{"data": ["ip:port", ...]} 或 {"ip": "ip", "port": port}
    """

    def __init__(
        self,
        api_url: str,
        parse_func: Callable[[str], list[str]] | None = None,
        interval: int = 300,
        timeout: int = 10,
    ):
        """
        初始化代理 API 客户端

        Args:
            api_url: 代理 API 地址
            parse_func: 自定义解析函数，接收响应文本，返回代理列表
            interval: 刷新间隔（秒）
            timeout: 请求超时（秒）
        """
        self.api_url = api_url
        self.parse_func = parse_func or self._default_parse
        self.interval = interval
        self.timeout = timeout
        self._lock = threading.Lock()
        self._proxies: list[ProxyInfo] = []
        self._last_refresh: float = 0
        self._running = False

    def _default_parse(self, text: str) -> list[str]:
        """
        默认解析器：自动识别 API 响应格式

        支持格式：
        1. 纯文本：每行一个 IP:PORT
        2. JSON 数组：["ip:port", ...]
        3. JSON 对象：{"data": [...]} 或 {"ip": "...", "port": ...}
        """
        text = text.strip()

        # 尝试 JSON 解析
        try:
            data = json.loads(text)

            # JSON 数组
            if isinstance(data, list):
                return [str(item) for item in data if item]

            # JSON 对象
            if isinstance(data, dict):
                # {"data": ["ip:port", ...]}
                if "data" in data and isinstance(data["data"], list):
                    return [str(item) for item in data["data"] if item]

                # {"proxies": ["ip:port", ...]}
                if "proxies" in data and isinstance(data["proxies"], list):
                    return [str(item) for item in data["proxies"] if item]

                # {"ip": "1.2.3.4", "port": 8080}
                if "ip" in data and "port" in data:
                    return [f"{data['ip']}:{data['port']}"]

                # {"ip": "1.2.3.4:8080"}
                if "ip" in data:
                    return [str(data["ip"])]

        except (json.JSONDecodeError, TypeError):
            pass

        # 纯文本：每行一个代理
        lines = text.splitlines()
        proxies = []
        for line in lines:
            line = line.strip()
            # 匹配 IP:PORT 格式
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$", line):
                proxies.append(line)
        return proxies

    def fetch(self) -> list[ProxyInfo]:
        """
        从 API 获取代理列表

        Returns:
            代理信息列表
        """
        try:
            logger.debug(f"[ProxyAPI] 正在获取代理: {self.api_url}")
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()

            proxy_list = self.parse_func(response.text)
            if not proxy_list:
                logger.warning(f"[ProxyAPI] 未获取到代理: {self.api_url}")
                return []

            proxies = []
            for proxy_str in proxy_list:
                proxy_info = self._parse_proxy(proxy_str)
                if proxy_info:
                    proxies.append(proxy_info)

            logger.info(f"[ProxyAPI] 获取 {len(proxies)} 个代理")
            return proxies

        except Exception as e:
            logger.error(f"[ProxyAPI] 获取代理失败: {e}")
            return []

    def _parse_proxy(self, proxy_str: str) -> ProxyInfo | None:
        """解析代理字符串"""
        if not proxy_str or not proxy_str.strip():
            return None

        proxy_str = proxy_str.strip()
        username = None
        password = None

        # 处理带认证的代理
        if "@" in proxy_str:
            scheme_end = proxy_str.find("://")
            if scheme_end != -1:
                scheme = proxy_str[: scheme_end + 3]
                rest = proxy_str[scheme_end + 3 :]
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

        # 确保有协议前缀
        if not proxy_str.startswith(("http://", "https://", "socks")):
            proxy_str = "http://" + proxy_str

        return ProxyInfo(url=proxy_str, username=username, password=password)

    def get_proxies(self, force_refresh: bool = False) -> list[ProxyInfo]:
        """
        获取代理列表（带缓存）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            代理信息列表
        """
        with self._lock:
            now = time.time()
            if force_refresh or (now - self._last_refresh > self.interval):
                self._proxies = self.fetch()
                self._last_refresh = now
            return self._proxies.copy()


class ProxyPool:
    """
    代理池管理器

    功能：
    - 支持多个代理轮换使用
    - 支持随机/轮询/最少使用三种策略
    - 支持从 API 动态获取代理
    - 自动检测代理有效性
    - 线程安全
    """

    def __init__(
        self,
        proxies: list[str] | None = None,
        strategy: ProxyStrategy = ProxyStrategy.RANDOM,
        api_url: str | None = None,
        api_interval: int = 300,
        check_interval: int = 300,
        timeout: int = 10,
    ):
        """
        初始化代理池

        Args:
            proxies: 代理地址列表，格式: http://host:port 或 user:pass@host:port
            strategy: 轮换策略
            api_url: 代理 API 地址
            api_interval: API 刷新间隔（秒）
            check_interval: 有效性检测间隔（秒）
            timeout: 检测超时时间（秒）
        """
        self.strategy = strategy
        self.check_interval = check_interval
        self.timeout = timeout
        self._lock = threading.Lock()
        self._index = 0  # 轮询索引

        # 代理 API 客户端
        self._api_client: ProxyAPIClient | None = None
        if api_url:
            self._api_client = ProxyAPIClient(
                api_url=api_url,
                interval=api_interval,
                timeout=timeout,
            )
            logger.info(f"[ProxyPool] 已配置代理 API: {api_url}")

        # 解析手动配置的代理列表
        self._static_proxies: list[ProxyInfo] = []
        if proxies:
            for proxy_str in proxies:
                proxy_info = self._parse_proxy(proxy_str)
                if proxy_info:
                    self._static_proxies.append(proxy_info)

        logger.info(f"[ProxyPool] 初始化完成: 手动代理 {len(self._static_proxies)} 个, 策略: {strategy.value}")

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
                scheme = proxy_str[: scheme_end + 3]
                rest = proxy_str[scheme_end + 3 :]
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

    def _get_all_proxies(self) -> list[ProxyInfo]:
        """获取所有可用代理（手动配置 + API）"""
        all_proxies = self._static_proxies.copy()

        # 从 API 获取代理
        if self._api_client:
            api_proxies = self._api_client.get_proxies()
            all_proxies.extend(api_proxies)

        return all_proxies

    def get_proxy(self) -> dict[str, str] | None:
        """
        获取一个可用代理

        Returns:
            代理配置字典，格式: {"http": "http://...", "https": "http://..."}
            没有可用代理时返回 None
        """
        with self._lock:
            # 获取所有代理
            all_proxies = self._get_all_proxies()

            # 过滤有效代理
            valid_proxies = [p for p in all_proxies if p.is_valid]

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
            all_proxies = self._get_all_proxies()
            for p in all_proxies:
                if p.url == proxy_url:
                    p.success_count += 1
                    p.fail_count = 0
                    p.is_valid = True
                    break

    def report_failure(self, proxy_dict: dict[str, str]) -> None:
        """报告代理使用失败"""
        with self._lock:
            proxy_url = proxy_dict.get("http") or proxy_dict.get("https")
            all_proxies = self._get_all_proxies()
            for p in all_proxies:
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
        return len(self._get_all_proxies())

    @property
    def valid_count(self) -> int:
        """有效代理数量"""
        return len([p for p in self._get_all_proxies() if p.is_valid])

    def refresh_api(self) -> int:
        """
        强制刷新 API 代理

        Returns:
            刷新后代理数量
        """
        if self._api_client:
            with self._lock:
                self._api_client._last_refresh = 0  # 强制刷新
                proxies = self._api_client.get_proxies(force_refresh=True)
                return len(proxies)
        return 0


# 全局代理池实例
_proxy_pool: ProxyPool | None = None


def get_proxy_pool(
    proxies: list[str] | None = None,
    strategy: str = "random",
    api_url: str | None = None,
) -> ProxyPool:
    """
    获取全局代理池实例

    Args:
        proxies: 代理列表
        strategy: 轮换策略
        api_url: 代理 API 地址

    Returns:
        代理池实例
    """
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool(
            proxies=proxies,
            strategy=ProxyStrategy(strategy),
            api_url=api_url,
        )
    return _proxy_pool


def reset_proxy_pool() -> None:
    """重置全局代理池"""
    global _proxy_pool
    _proxy_pool = None
