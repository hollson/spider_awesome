"""
统一 HTTP 客户端封装
支持重试、代理、超时、指数退避
"""

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
    ):
        """
        初始化 HTTP 客户端

        Args:
            timeout: 请求超时时间（秒）
            retries: 重试次数
            backoff_factor: 重试退避系数
            proxies: 代理配置
        """
        self.timeout = timeout
        self.session = requests.Session()

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

        # 配置代理
        if proxies:
            self.session.proxies.update(proxies)
        elif settings.PROXIES:
            self.session.proxies.update(settings.PROXIES)

        # 默认请求头
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/html, */*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

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
            return response
        except requests.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"[HTTP] {method} {url} failed ({elapsed:.2f}s): {e}")
            raise

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
