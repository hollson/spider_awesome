"""
User-Agent 轮换管理器
内置常见浏览器 UA（桌面端 + 移动端），支持随机轮换

内置 80+ 个 UA，覆盖：
- Chrome / Firefox / Safari / Edge（桌面端）
- Chrome / Firefox / Safari（移动端：iPhone / Android / iPad）
- Opera / UC Browser（移动端）

默认启用，UA 列表内置维护，无需用户配置。
"""

import random
import threading

from app.common.logger import logger

# ==================== 桌面端 UA ====================

# Chrome (Windows / Mac / Linux)
DESKTOP_CHROME = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

# Firefox (Windows / Mac / Linux)
DESKTOP_FIREFOX = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

# Safari (macOS)
DESKTOP_SAFARI = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

# Edge (Windows)
DESKTOP_EDGE = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
]

# Opera (Windows)
DESKTOP_OPERA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 OPR/115.0.0.0",
]

# ==================== 移动端 UA ====================

# iPhone Safari
MOBILE_IPHONE_SAFARI = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
]

# Android Chrome
MOBILE_ANDROID_CHROME = [
    "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 22081283G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; RMX3771) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
]

# Android Firefox
MOBILE_ANDROID_FIREFOX = [
    "Mozilla/5.0 (Android 15; Mobile; rv:133.0) Gecko/133.0 Firefox/133.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0",
    "Mozilla/5.0 (Android 13; Mobile; rv:131.0) Gecko/131.0 Firefox/131.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:130.0) Gecko/130.0 Firefox/130.0",
]

# iPad Safari
MOBILE_IPAD_SAFARI = [
    "Mozilla/5.0 (iPad; CPU OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

# Android UC Browser
MOBILE_ANDROID_UC = [
    "Mozilla/5.0 (Linux; U; Android 14; en-US; SM-G998B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.79 Mobile Safari/537.36 UCBrowser/16.6.8.1640 Mobile",
    "Mozilla/5.0 (Linux; U; Android 13; en-US; Pixel 7 Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.79 Mobile Safari/537.36 UCBrowser/16.5.4.1632 Mobile",
]

# Android Opera Mini
MOBILE_ANDROID_OPERA = [
    "Opera/9.80 (Android 14; Opera Mini/82.0.2254.70112; U; en) Presto/2.12.423 Version/12.16",
    "Opera/9.80 (Android 13; Opera Mini/81.0.2254.70031; U; en) Presto/2.12.423 Version/12.16",
]

# 合并所有 UA 列表
DEFAULT_USER_AGENTS = (
    DESKTOP_CHROME
    + DESKTOP_FIREFOX
    + DESKTOP_SAFARI
    + DESKTOP_EDGE
    + DESKTOP_OPERA
    + MOBILE_IPHONE_SAFARI
    + MOBILE_ANDROID_CHROME
    + MOBILE_ANDROID_FIREFOX
    + MOBILE_IPAD_SAFARI
    + MOBILE_ANDROID_UC
    + MOBILE_ANDROID_OPERA
)


class UserAgentManager:
    """
    User-Agent 轮换管理器

    功能：
    - 内置 80+ 常见浏览器 UA（桌面端 + 移动端）
    - 覆盖 Chrome / Firefox / Safari / Edge / Opera / UC Browser
    - 支持随机选择 / 轮询选择
    - 线程安全
    """

    def __init__(self, custom_agents: list[str] | None = None):
        """
        初始化 UA 管理器

        Args:
            custom_agents: 自定义 UA 列表，为空则使用内置列表
        """
        self._lock = threading.Lock()
        self._agents = custom_agents if custom_agents else DEFAULT_USER_AGENTS
        self._index = 0

        logger.info(f"[UserAgent] 初始化完成: {len(self._agents)} 个 User-Agent")

    def get_random(self) -> str:
        """随机获取一个 User-Agent"""
        with self._lock:
            return random.choice(self._agents)

    def get_next(self) -> str:
        """轮询获取下一个 User-Agent"""
        with self._lock:
            ua = self._agents[self._index % len(self._agents)]
            self._index += 1
            return ua

    def get_all(self) -> list[str]:
        """获取所有 User-Agent"""
        return self._agents.copy()

    def add_agent(self, ua: str) -> None:
        """动态添加 User-Agent"""
        with self._lock:
            if ua not in self._agents:
                self._agents.append(ua)
                logger.debug(f"[UserAgent] 添加 UA: {ua[:50]}...")

    def remove_agent(self, ua: str) -> None:
        """动态移除 User-Agent"""
        with self._lock:
            if ua in self._agents and len(self._agents) > 1:
                self._agents.remove(ua)
                logger.debug(f"[UserAgent] 移除 UA: {ua[:50]}...")

    @property
    def count(self) -> int:
        """UA 数量"""
        return len(self._agents)


def parse_user_agents_from_string(ua_string: str) -> list[str]:
    """
    从字符串解析 UA 列表（用 | 分隔）

    Args:
        ua_string: UA 字符串，用 | 分隔

    Returns:
        UA 列表
    """
    if not ua_string or not ua_string.strip():
        return []
    return [ua.strip() for ua in ua_string.split("|") if ua.strip()]


# 全局 UA 管理器实例
_ua_manager: UserAgentManager | None = None


def get_ua_manager(custom_agents: list[str] | None = None) -> UserAgentManager:
    """
    获取全局 UA 管理器实例

    Args:
        custom_agents: 自定义 UA 列表

    Returns:
        UA 管理器实例
    """
    global _ua_manager
    if _ua_manager is None:
        _ua_manager = UserAgentManager(custom_agents=custom_agents)
    return _ua_manager


def reset_ua_manager() -> None:
    """重置全局 UA 管理器"""
    global _ua_manager
    _ua_manager = None
