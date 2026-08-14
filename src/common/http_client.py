"""
统一 HTTP 客户端封装
支持重试、代理、超时、指数退避
支持代理池轮换、User-Agent 轮换、请求间隔控制

代理逻辑：
- 优先级：构造参数 > 代理池 > 静态代理
- 代理池启用且有配置 → 使用代理池轮换
- 代理池未启用或无配置 → 使用静态代理（HTTP_PROXY/HTTPS_PROXY）
"""

import random
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.common.logger import logger
from src.settings import settings


class HttpClient:
    """统一 HTTP 客户端"""

    def __init__(
        self,
        timeout: int = 30,
        retries: int = 3,
        backoff_factor: float = 1.0,
        proxies: dict | None = None,
        use_proxy_pool: bool | None = None,
        use_ua_rotation: bool | None = None,
        use_delay: bool | None = None,
    ):
        """
        初始化 HTTP 客户端

        Args:
            timeout: 请求超时时间（秒）
            retries: 重试次数
            backoff_factor: 重试退避系数
            proxies: 代理配置（静态代理，优先级最高）
            use_proxy_pool: 是否使用代理池（None 则读取配置）
            use_ua_rotation: 是否启用 UA 轮换（None 则读取配置）
            use_delay: 是否启用请求间隔（None 则读取配置）
        """
        self.timeout = timeout
        self.session = requests.Session()

        # 解析代理池列表
        pool_list = settings.PROXY_POOL_LIST
        self._pool_proxies = [p.strip() for p in pool_list.split("|") if p.strip()] if pool_list else None

        # 保存配置
        # 代理池逻辑：启用 且 有配置 → 用代理池；否则用静态代理
        self._use_proxy_pool = (
            (use_proxy_pool if use_proxy_pool is not None else settings.PROXY_POOL_ENABLED)
            and bool(self._pool_proxies)
        )
        # UA 轮换始终开启
        self._use_ua_rotation = use_ua_rotation if use_ua_rotation is not None else True
        # 请求间隔：通过 min/max 是否相等判断是否启用（相等=禁用）
        self._use_delay = use_delay if use_delay is not None else (settings.REQUEST_DELAY_MIN != settings.REQUEST_DELAY_MAX)
        self._current_proxy = None

        # 配置重试策略
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 配置代理（静态代理兜底）
        if proxies:
            self.session.proxies.update(proxies)
            self._current_proxy = proxies
        elif settings.PROXIES:
            self.session.proxies.update(settings.PROXIES)
            self._current_proxy = settings.PROXIES

        # 默认请求头
        self._setup_default_headers()

        # 日志
        if self._use_proxy_pool:
            logger.debug(f"[HTTP] 代理模式: 代理池 ({len(self._pool_proxies)} 个代理)")
        elif self._current_proxy:
            logger.debug("[HTTP] 代理模式: 静态代理")
        else:
            logger.debug("[HTTP] 代理模式: 直连")

    def _setup_default_headers(self) -> None:
        """设置默认请求头（支持 UA 轮换）"""
        if self._use_ua_rotation:
            from src.common.user_agent import get_ua_manager
            ua_manager = get_ua_manager()
            user_agent = ua_manager.get_random()
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "application/json, text/html, */*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _get_proxy_from_pool(self) -> dict[str, str] | None:
        """从代理池获取代理"""
        if not self._use_proxy_pool or not self._pool_proxies:
            return None

        from src.common.proxy_pool import get_proxy_pool

        pool = get_proxy_pool(
            proxies=self._pool_proxies,
            strategy=settings.PROXY_POOL_STRATEGY,
        )
        return pool.get_proxy()

    def _apply_proxy(self, proxy_dict: dict[str, str] | None) -> None:
        """应用代理配置"""
        if proxy_dict:
            self.session.proxies.update(proxy_dict)
            self._current_proxy = proxy_dict
        elif settings.PROXIES:
            # 代理池未返回结果，回退到静态代理
            self.session.proxies.update(settings.PROXIES)
            self._current_proxy = settings.PROXIES
        else:
            self.session.proxies.clear()
            self._current_proxy = None

    def _apply_ua_rotation(self) -> None:
        """应用 UA 轮换"""
        if self._use_ua_rotation:
            from src.common.user_agent import get_ua_manager
            ua_manager = get_ua_manager()
            self.session.headers["User-Agent"] = ua_manager.get_random()

    def _apply_delay(self) -> None:
        """应用请求间隔"""
        if self._use_delay:
            delay_min = settings.REQUEST_DELAY_MIN
            delay_max = settings.REQUEST_DELAY_MAX
            delay = random.randint(delay_min, delay_max) / 1000.0
            logger.debug(f"[HTTP] 请求间隔: {delay:.2f}s")
            time.sleep(delay)

    def _report_proxy_success(self) -> None:
        """报告代理使用成功"""
        if self._use_proxy_pool and self._current_proxy:
            from src.common.proxy_pool import get_proxy_pool
            pool = get_proxy_pool(proxies=self._pool_proxies)
            pool.report_success(self._current_proxy)

    def _report_proxy_failure(self) -> None:
        """报告代理使用失败"""
        if self._use_proxy_pool and self._current_proxy:
            from src.common.proxy_pool import get_proxy_pool
            pool = get_proxy_pool(proxies=self._pool_proxies)
            pool.report_failure(self._current_proxy)

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        data: str | bytes | dict | None = None,
        params: dict[str, str] | None = None,
        timeout: int | None = None,
        **kwargs,
    ) -> requests.Response:
        """
        发送 HTTP 请求

        Args:
            method: 请求方法 (GET, POST, etc.)
            url: 请求 URL
            headers: 请求头
            json: JSON 请求体
            data: 表单数据
            params: URL 参数
            timeout: 超时时间（覆盖默认值）
            **kwargs: 其他参数

        Returns:
            响应对象

        Raises:
            requests.RequestException: 请求失败
        """
        timeout = timeout or self.timeout
        merged_headers = {**self.session.headers, **(headers or {})}

        # 应用防反爬策略
        self._apply_ua_rotation()
        self._apply_delay()

        # 代理池轮换
        if self._use_proxy_pool:
            proxy_dict = self._get_proxy_from_pool()
            self._apply_proxy(proxy_dict)

        logger.debug(f"[HTTP] {method} {url}")
        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=merged_headers,
                json=json,
                data=data,
                params=params,
                timeout=timeout,
                **kwargs,
            )
            elapsed = time.time() - start_time
            logger.debug(f"[HTTP] {method} {url} -> {response.status_code} ({elapsed:.2f}s)")
            response.raise_for_status()

            # 报告代理成功
            self._report_proxy_success()

            return response
        except requests.RequestException as e:
            elapsed = time.time() - start_time
            hint = self._error_hint(e)
            logger.error(f"[HTTP] {method} {url} ({elapsed:.1f}s) - {hint}")

            # 报告代理失败
            self._report_proxy_failure()

            raise

    @staticmethod
    def _error_hint(e: requests.RequestException) -> str:
        """将异常转为简短中文提示"""
        msg = str(e)
        if "SSLError" in msg or "CERTIFICATE_VERIFY_FAILED" in msg:
            return "SSL证书验证失败，请检查网络或站点证书配置"
        if "ConnectionError" in msg or "ConnectionRefused" in msg:
            return "连接失败，请检查网络或站点是否可访问"
        if "Timeout" in msg:
            return "请求超时，请稍后重试"
        if "404" in msg:
            return "接口不存在（404），请确认地址是否正确"
        if "403" in msg:
            return "访问被拒绝（403），请检查权限或IP是否被限制"
        if "500" in msg or "502" in msg or "503" in msg:
            return "服务端异常，请稍后重试"
        return str(e)[:120]

    def get(self, url: str, **kwargs) -> requests.Response:
        """GET 请求"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """POST 请求"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT 请求"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        """关闭会话"""
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        self.close()


def create_client(**kwargs) -> HttpClient:
    """创建 HTTP 客户端的便捷函数"""
    return HttpClient(**kwargs)
