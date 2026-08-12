"""
示例采集器2: ASL
演示 HTML 分页采集方式

注意：这是一个示例采集器，衍生项目可参考或删除
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.collector.base_collector import BaseCollector
from src.common.logger import logger
from src.common.utils import compress_html


class ASLExampleCollector(BaseCollector):
    """
    ASL Group 示例采集器
    通过 HTML 分页采集空退航班数据
    """

    # 运营商 ID
    OPERATOR_ID: str = "5da241f1177e4a41b9ae94f83b44a063"

    # 基础 URL
    BASE_URL: str = "https://www.aslgroup.eu/en/empty-legs"

    # 请求头
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    current_url: str

    def __init__(self) -> None:
        super().__init__()
        self.current_url = self.BASE_URL

    @property
    def name(self) -> str:
        return "example_asl"

    def fetch(self) -> list[dict[str, Any]]:
        """
        执行采集（支持分页）

        Returns:
            采集到的数据列表
        """
        all_records: list[dict[str, Any]] = []

        # 尝试从缓存读取
        cache_pattern = "ASL_raw_*.html"
        from src.settings import settings

        cache_files = list(Path(settings.RAW_DATA_DIR).glob(cache_pattern))

        if cache_files:
            logger.info(f"[{self.name}] 从缓存读取 {len(cache_files)} 个文件")
            for cache_file in cache_files:
                content = cache_file.read_text(encoding="utf-8")
                records, _ = self._parse_html(content)
                all_records.extend(records)
        else:
            # 从 HTTP 采集
            logger.info(f"[{self.name}] 从 HTTP 采集")
            records, next_pages = self._fetch_page(self.BASE_URL)
            all_records.extend(records)

            # 处理分页
            for page_url in next_pages:
                try:
                    page_records, _ = self._fetch_page(page_url)
                    all_records.extend(page_records)
                except Exception as e:
                    logger.warning(f"[{self.name}] 分页采集失败: {e}")

        logger.info(f"[{self.name}] 采集完成，共 {len(all_records)} 条数据")
        return all_records

    def _fetch_page(self, url: str) -> tuple[list[dict[str, Any]], list[str]]:
        """
        采集单页数据

        Args:
            url: 页面 URL

        Returns:
            (数据列表, 下一页 URL 列表)
        """
        response = self.http_client.get(url, headers=self.HEADERS)
        content = compress_html(response.text)

        # 保存缓存
        page_num = self._extract_page_number(url)
        cache_filename = f"ASL_raw_{page_num}.html"
        self.write_cache(cache_filename, content)

        # 解析 HTML
        records, next_pages = self._parse_html(content)
        return records, next_pages

    def _extract_page_number(self, url: str) -> int:
        """从 URL 提取页码"""
        match = re.search(r"page=(\d+)", url)
        return int(match.group(1)) if match else 1

    def _parse_html(self, html: str) -> tuple[list[dict[str, Any]], list[str]]:
        """
        解析 HTML

        Args:
            html: HTML 内容

        Returns:
            (数据列表, 下一页 URL 列表)
        """
        records: list[dict[str, Any]] = []
        next_pages: list[str] = []

        soup = BeautifulSoup(html, "html.parser")

        # 提取分页链接
        pagination = soup.find_all("a", class_="pagination-page")
        for link in pagination:
            classes = link.get("class")
            if classes and "is-active" not in classes:
                href = link.get("href", "")
                if isinstance(href, str):
                    next_pages.append(href)

        # 提取航班数据
        articles = soup.find_all("article", class_="plane")
        for article in articles:
            try:
                record = self._parse_article(article)
                if record:
                    records.append(record)
            except Exception as e:
                logger.warning(f"[{self.name}] 解析文章失败: {e}")
                continue

        return records, next_pages

    def _parse_article(self, article: Any) -> dict[str, Any] | None:
        """解析单篇文章（航班数据）"""
        # 提取标题
        title_elem = article.find("span", class_="plane-name")
        title = title_elem.text.strip() if title_elem else ""

        # 提取航线信息
        route_elem = article.find("div", class_="leading-headline plane-headline")
        route_text = route_elem.text.strip() if route_elem else ""
        origin_city, origin_code, dest_city, dest_code = self._parse_route(route_text)

        # 提取图片
        img = article.find("img")
        thumb = f"https://www.aslgroup.eu{img['src']}" if img and img.get("src") else ""

        # 提取日期和时间
        spec_items = article.find_all("li", class_="plane-spec-item")
        take_off_time = None
        if len(spec_items) >= 2:
            date_str = spec_items[0].text.strip().split()[-1]
            time_str = spec_items[1].text.strip().split()[-1]
            try:
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                take_off_time = dt.replace(
                    hour=int(time_str.split(":")[0]),
                    minute=int(time_str.split(":")[1]) if ":" in time_str else 0,
                )
            except (ValueError, IndexError):
                pass

        # 提取座位数
        seats = 0
        seats_elem = article.find("li", class_="plane-spec-item-muted")
        if seats_elem:
            seats_match = re.findall(r"\d+", seats_elem.text)
            seats = int(seats_match[0]) if seats_match else 0

        # 生成唯一 ID
        record_id = self.generate_record_id(title, origin_code, dest_code)

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.OPERATOR_ID,
            "title": title,
            "tail_num": None,
            "origin_code": origin_code,
            "origin_city": origin_city,
            "dest_code": dest_code,
            "dest_city": dest_city,
            "start_time": None,
            "end_time": None,
            "take_off_time": take_off_time,
            "cost_minutes": None,
            "flight_cost": None,
            "currency": None,
            "currency_symbol": None,
            "seats": seats,
            "thumb": thumb,
            "preview": None,
            "source_url": self.BASE_URL,
            "raw_data": {"route": route_text},
        }

    def _parse_route(self, route: str) -> tuple[str, str, str, str]:
        """
        解析航线文本

        格式: "origin_city(origin_code)dest_city(dest_code)"

        Returns:
            (origin_city, origin_code, dest_city, dest_code)
        """
        route = route.replace(" ", "")
        match = re.match(r"([^(]+)\(([^)]+)\)(.+)\(([^)]+)\)", route)
        if match:
            groups = match.groups()
            return groups[0], groups[1], groups[2], groups[3]
        return "", "", "", ""


# 便捷函数
def collect() -> list[dict[str, Any]]:
    """执行采集的便捷函数"""
    with ASLExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    import json

    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
