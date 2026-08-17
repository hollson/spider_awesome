"""
支持 JavaScript 渲染的采集器抽象基类
继承自 BaseCollector，添加浏览器渲染能力

适用场景：
- 需要 JavaScript 渲染的动态页面
- 单页应用（SPA）数据采集
- 需要模拟用户交互的场景
"""

from typing import Any

from app.collector.base_collector import BaseCollector
from app.common.browser_client import BrowserClient
from app.common.logger import logger


class BaseBrowserCollector(BaseCollector):
    """
    支持 JavaScript 渲染的采集器基类

    所有需要浏览器渲染的采集器必须继承此类并实现：
    - name: 采集器名称
    - fetch(): 执行采集并返回数据列表

    特性：
    - 自动管理浏览器生命周期
    - 支持 headless 模式
    - 支持代理配置
    - 内置反检测脚本
    """

    _browser_client: BrowserClient | None

    def __init__(
        self,
        headless: bool = True,
        proxy: dict[str, str] | None = None,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
        timeout: int = 30000,
    ):
        """
        初始化浏览器采集器

        Args:
            headless: 是否无头模式
            proxy: 代理配置
            user_agent: 自定义 User-Agent
            viewport: 视口大小
            timeout: 页面加载超时（毫秒）
        """
        super().__init__()
        self._browser_client = None
        self._headless = headless
        self._proxy = proxy
        self._user_agent = user_agent
        self._viewport = viewport
        self._timeout = timeout

    @property
    def browser_client(self) -> BrowserClient:
        """获取浏览器客户端"""
        if self._browser_client is None:
            self._browser_client = BrowserClient(
                headless=self._headless,
                proxy=self._proxy,
                user_agent=self._user_agent,
                viewport=self._viewport,
                timeout=self._timeout,
            )
        return self._browser_client

    def fetch_page(
        self,
        url: str,
        wait_until: str = "networkidle",
        wait_selector: str | None = None,
        extra_headers: dict[str, str] | None = None,
        cookies: list[dict[str, str]] | None = None,
    ) -> str:
        """
        获取渲染后的页面 HTML

        Args:
            url: 页面 URL
            wait_until: 等待条件
            wait_selector: 等待特定元素出现
            extra_headers: 额外请求头
            cookies: Cookie 列表

        Returns:
            渲染后的 HTML 内容
        """
        return self.browser_client.fetch_page(
            url=url,
            wait_until=wait_until,
            wait_selector=wait_selector,
            extra_headers=extra_headers,
            cookies=cookies,
        )

    def execute_js(self, url: str, script: str) -> Any:
        """
        执行 JavaScript 脚本并返回结果

        Args:
            url: 页面 URL
            script: JavaScript 脚本

        Returns:
            脚本执行结果
        """
        return self.browser_client.execute_js(url, script)

    def fetch_page_with_cache(
        self,
        cache_filename: str,
        url: str,
        force_refresh: bool = False,
        **kwargs,
    ) -> str:
        """
        带缓存的页面获取

        Args:
            cache_filename: 缓存文件名
            url: 页面 URL
            force_refresh: 是否强制刷新缓存
            **kwargs: 传递给 fetch_page 的参数

        Returns:
            页面 HTML 内容
        """
        if not force_refresh:
            cached = self.read_cache(cache_filename)
            if cached is not None:
                return cached

        logger.info(f"[{self.name}] 开始获取页面: {url}")
        content = self.fetch_page(url, **kwargs)
        logger.info(f"[{self.name}] 页面获取完成，长度: {len(content)} 字符")

        self.write_cache(cache_filename, content)
        return content

    def close(self) -> None:
        """释放资源"""
        if self._browser_client:
            self._browser_client.close()
            self._browser_client = None
        # 调用父类的 close 方法
        super().close()

    def __enter__(self) -> "BaseBrowserCollector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
