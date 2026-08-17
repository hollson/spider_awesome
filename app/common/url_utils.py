"""
URL 处理工具
URL 格式化、域名提取、有效性校验等
"""

import re
from urllib.parse import quote, unquote, urljoin, urlparse


def normalize_url(url: str, base_url: str = "") -> str:
    """
    标准化 URL

    - 补全 scheme（默认 https）
    - 移除尾部斜杠
    - 解码特殊字符

    Args:
        url: 原始 URL
        base_url: 基础 URL（用于相对路径补全）

    Returns:
        标准化后的 URL
    """
    if not url:
        return ""

    url = url.strip()

    # 相对路径补全
    if base_url and not url.startswith(("http://", "https://", "//")):
        url = urljoin(base_url, url)

    # 补全 scheme
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith(("http://", "https://")):
        url = "https://" + url

    # 解析并重建
    parsed = urlparse(url)
    # 移除默认端口
    netloc = parsed.netloc
    if netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif netloc.endswith(":443"):
        netloc = netloc[:-4]

    # 移除尾部斜杠（保留路径根的 /）
    path = parsed.path.rstrip("/") or "/"

    # 重建 URL（保留 fragment）
    normalized = f"{parsed.scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"

    return normalized


def is_valid_url(url: str) -> bool:
    """
    校验 URL 格式是否有效

    Args:
        url: URL 字符串

    Returns:
        是否有效
    """
    if not url:
        return False
    pattern = re.compile(
        r"^https?://"  # scheme
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def extract_domain(url: str, include_subdomain: bool = False) -> str:
    """
    提取域名

    Args:
        url: URL 字符串
        include_subdomain: 是否包含子域名

    Returns:
        域名字符串

    Examples:
        >>> extract_domain("https://www.example.com/path")
        'example.com'
        >>> extract_domain("https://www.example.com/path", include_subdomain=True)
        'www.example.com'
    """
    if not url:
        return ""

    parsed = urlparse(url if "://" in url else "https://" + url)
    host = parsed.hostname or ""

    if not host:
        return ""

    if include_subdomain:
        return host

    # 移除 www 前缀
    if host.startswith("www."):
        host = host[4:]

    return host


def join_url(base_url: str, path: str) -> str:
    """
    安全拼接 URL

    Args:
        base_url: 基础 URL
        path: 路径或相对 URL

    Returns:
        完整 URL
    """
    if not path:
        return base_url
    if not base_url:
        return path

    # 绝对路径直接返回
    if path.startswith(("http://", "https://")):
        return path

    return urljoin(base_url, path)


def extract_query_params(url: str) -> dict[str, str]:
    """
    提取 URL 查询参数

    Args:
        url: URL 字符串

    Returns:
        参数字典
    """
    if not url:
        return {}

    parsed = urlparse(url)
    if not parsed.query:
        return {}

    params = {}
    for pair in parsed.query.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[unquote(key)] = unquote(value)
        else:
            params[unquote(pair)] = ""

    return params


def encode_url(text: str) -> str:
    """
    URL 编码

    Args:
        text: 原始文本

    Returns:
        编码后的文本
    """
    return quote(text, safe="")


def decode_url(text: str) -> str:
    """
    URL 解码

    Args:
        text: 编码文本

    Returns:
        解码后的文本
    """
    return unquote(text)


def is_same_domain(url1: str, url2: str) -> bool:
    """
    判断两个 URL 是否属于同一域名

    Args:
        url1: URL 1
        url2: URL 2

    Returns:
        是否同域
    """
    return extract_domain(url1) == extract_domain(url2)
