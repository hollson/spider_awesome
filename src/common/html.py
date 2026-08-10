"""
HTML 处理工具模块
提供 HTML 压缩、DOM 提取等通用功能
"""
import re
from typing import Optional


def compress_html(html: str) -> str:
    """
    压缩 HTML 文档
    删除注释、多余空格和换行

    Args:
        html: HTML 文本

    Returns:
        压缩后的 HTML 文本
    """
    # 删除注释
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # 压缩空白字符
    html = re.sub(r"\s+", " ", html)
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r">\s+", ">", html)
    html = re.sub(r"\s+<", "<", html)
    return html.strip()


def extract_body(html: str) -> str:
    """
    提取 HTML body 内容

    Args:
        html: HTML 文本

    Returns:
        body 内容
    """
    start = html.find("<body")
    end = html.find("</body>")
    if start != -1 and end != -1:
        return html[start:end + len("</body>")]
    return html


def remove_scripts_and_styles(html: str) -> str:
    """
    移除 script 和 style 标签

    Args:
        html: HTML 文本

    Returns:
        清理后的 HTML
    """
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    html = re.sub(r"<link.*?>", "", html, flags=re.DOTALL)
    html = re.sub(r"<meta.*?>", "", html, flags=re.DOTALL)
    return html


def clean_html(html: str, keep_style: bool = False) -> str:
    """
    全面清理 HTML

    Args:
        html: HTML 文本
        keep_style: 是否保留 style 标签

    Returns:
        清理后的 HTML
    """
    html = remove_scripts_and_styles(html)
    if not keep_style:
        html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    html = compress_html(html)
    return html


class HtmlProcessor:
    """
    HTML 处理器（链式调用）

    用法:
        result = HtmlProcessor(html).dom().compress().get()
    """

    def __init__(self, content: str):
        self._content = content

    def compress(self) -> "HtmlProcessor":
        """压缩 HTML"""
        self._content = compress_html(self._content)
        return self

    def body(self) -> "HtmlProcessor":
        """提取 body"""
        self._content = extract_body(self._content)
        return self

    def dom(self, keep_style: bool = False) -> "HtmlProcessor":
        """获取 DOM 结构"""
        self._content = remove_scripts_and_styles(self._content)
        if not keep_style:
            self._content = re.sub(r"<style.*?</style>", "", self._content, flags=re.DOTALL)
        return self

    def get(self) -> str:
        """获取结果"""
        return self._content

    def __str__(self) -> str:
        return self._content
