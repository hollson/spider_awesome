"""
Playwright 浏览器客户端
支持 JavaScript 渲染页面采集，内置反检测

使用前需安装依赖：
  pip install playwright
  playwright install chromium
"""

from __future__ import annotations

from typing import Any

from src.common.logger import logger


class BrowserClient:
    """
    Playwright 浏览器客户端

    功能：
    - 支持 JavaScript 渲染
    - 内置反检测（stealth）
    - 支持 headless 模式
    - 支持代理配置
    - 自动等待页面加载
    """

    def __init__(
        self,
        headless: bool = True,
        proxy: dict[str, str] | None = None,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
        timeout: int = 30000,
    ):
        """
        初始化浏览器客户端

        Args:
            headless: 是否无头模式
            proxy: 代理配置，格式: {"server": "http://proxy:8080"}
            user_agent: 自定义 User-Agent
            viewport: 视口大小，格式: {"width": 1920, "height": 1080}
            timeout: 页面加载超时（毫秒）
        """
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.timeout = timeout
        self._playwright: Any = None
        self._browser: Any = None

    def _ensure_playwright(self) -> None:
        """确保 Playwright 已启动"""
        if self._playwright is None:
            try:
                from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

                self._playwright = sync_playwright().start()
                logger.debug("[Browser] Playwright 已启动")
            except ImportError as err:
                raise ImportError("请安装 playwright: pip install playwright && playwright install chromium") from err

    def _ensure_browser(self) -> None:
        """确保浏览器已启动"""
        self._ensure_playwright()

        if self._browser is None or not self._browser.is_connected():
            # 浏览器启动参数
            launch_args = {
                "headless": self.headless,
            }

            # 配置代理
            if self.proxy:
                launch_args["proxy"] = self.proxy

            self._browser = self._playwright.chromium.launch(**launch_args)
            logger.debug("[Browser] 浏览器已启动")

    def _create_context(self) -> Any:
        """创建浏览器上下文"""
        self._ensure_browser()

        context_args = {
            "viewport": self.viewport,
            "user_agent": self.user_agent,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            # 反检测设置
            "java_script_enabled": True,
            "bypass_csp": True,
        }

        # 代理认证
        if self.proxy and "username" in self.proxy:
            context_args["http_credentials"] = {
                "username": self.proxy["username"],
                "password": self.proxy["password"],
            }

        return self._browser.new_context(**context_args)

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
            wait_until: 等待条件 (load/domcontentloaded/networkidle)
            wait_selector: 等待特定元素出现
            extra_headers: 额外请求头
            cookies: Cookie 列表

        Returns:
            渲染后的 HTML 内容
        """
        context = self._create_context()
        page = context.new_page()

        try:
            # 设置额外请求头
            if extra_headers:
                page.set_extra_http_headers(extra_headers)

            # 设置 Cookie
            if cookies:
                context.add_cookies(cookies)

            # 注入反检测脚本
            self._inject_stealth(page)

            # 访问页面
            logger.info(f"[Browser] 访问页面: {url}")
            page.goto(url, wait_until=wait_until, timeout=self.timeout)

            # 等待特定元素
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.timeout)

            # 获取页面内容
            content = page.content()
            logger.info(f"[Browser] 页面获取成功: {url} ({len(content)} 字符)")

            return content

        except Exception as e:
            logger.error(f"[Browser] 页面获取失败: {url} - {e}")
            raise
        finally:
            page.close()
            context.close()

    def execute_js(self, url: str, script: str) -> Any:
        """
        执行 JavaScript 脚本并返回结果

        Args:
            url: 页面 URL
            script: JavaScript 脚本

        Returns:
            脚本执行结果
        """
        context = self._create_context()
        page = context.new_page()

        try:
            logger.info(f"[Browser] 执行 JS: {url}")
            page.goto(url, wait_until="networkidle", timeout=self.timeout)

            # 注入反检测脚本
            self._inject_stealth(page)

            # 执行脚本
            result = page.evaluate(script)
            logger.info(f"[Browser] JS 执行完成: {url}")

            return result

        except Exception as e:
            logger.error(f"[Browser] JS 执行失败: {url} - {e}")
            raise
        finally:
            page.close()
            context.close()

    def fetch_with_interception(
        self,
        url: str,
        intercept_urls: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        带请求拦截的页面获取

        Args:
            url: 页面 URL
            intercept_urls: 要拦截的 URL 模式
            **kwargs: 传递给 fetch_page 的参数

        Returns:
            包含页面内容和拦截数据的字典
        """
        context = self._create_context()
        page = context.new_page()
        intercepted_data: list[dict[str, Any]] = []

        try:
            # 设置请求拦截
            if intercept_urls:

                def handle_route(route):
                    request = route.request
                    # 检查是否需要拦截
                    should_intercept = any(pattern in request.url for pattern in intercept_urls)
                    if should_intercept:
                        intercepted_data.append(
                            {
                                "url": request.url,
                                "method": request.method,
                                "headers": request.headers,
                            }
                        )
                    route.continue_()

                page.route("**/*", handle_route)

            # 访问页面
            extra_headers = kwargs.pop("extra_headers", None)
            if extra_headers:
                page.set_extra_http_headers(extra_headers)

            page.goto(url, wait_until="networkidle", timeout=self.timeout)
            content = page.content()

            return {
                "html": content,
                "intercepted": intercepted_data,
            }

        except Exception as e:
            logger.error(f"[Browser] 拦截请求失败: {url} - {e}")
            raise
        finally:
            page.close()
            context.close()

    def _inject_stealth(self, page: Any) -> None:
        """注入反检测脚本"""
        stealth_js = """
        // 覆盖 navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // 覆盖 chrome runtime
        window.chrome = {
            runtime: {},
        };

        // 覆盖 permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // 覆盖 plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // 覆盖 languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        """
        page.evaluate(stealth_js)

    def close(self) -> None:
        """关闭浏览器和 Playwright"""
        try:
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
            logger.debug("[Browser] 已关闭")
        except Exception as e:
            logger.warning(f"[Browser] 关闭时出错: {e}")

    def __enter__(self) -> BrowserClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def create_browser_client(
    headless: bool = True,
    proxy_server: str | None = None,
    proxy_username: str | None = None,
    proxy_password: str | None = None,
    user_agent: str | None = None,
) -> BrowserClient:
    """
    创建浏览器客户端的便捷函数

    Args:
        headless: 是否无头模式
        proxy_server: 代理服务器地址
        proxy_username: 代理用户名
        proxy_password: 代理密码
        user_agent: 自定义 User-Agent

    Returns:
        浏览器客户端实例
    """
    proxy = None
    if proxy_server:
        proxy = {"server": proxy_server}
        if proxy_username and proxy_password:
            proxy["username"] = proxy_username
            proxy["password"] = proxy_password

    return BrowserClient(
        headless=headless,
        proxy=proxy,
        user_agent=user_agent,
    )
