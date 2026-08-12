"""
示例采集器: ChartRight
演示 HTML 页面解析采集方式

数据源: https://chartright.com/empty-legs/
特点: 解析 HTML 卡片结构，提取航班信息
"""

import json
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class ChartRightExampleCollector(BaseCollector):
    """
    ChartRight 示例采集器
    通过 HTML 解析获取空退航班数据
    """

    OPERATOR_ID: str = "62a7050b3fb646c8b7011687ae7ed9a9"
    URL: str = "https://chartright.com/empty-legs/"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @property
    def name(self) -> str:
        return "example_chartright"

    def _make_request(self) -> str:
        """发送请求获取HTML"""
        response = self.http_client.get(url=self.URL, headers=self.HEADERS)
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """执行采集"""
        content = self.fetch_with_cache(
            cache_filename="Chartright_raw.html",
            fetch_func=self._make_request,
        )

        records: list[dict[str, Any]] = []
        if not content:
            return records

        soup = BeautifulSoup(content, "html.parser")
        items = soup.find_all("div", class_="quick-quotes")

        for item in items:
            try:
                record = self._parse_item(item)
                if record:
                    records.append(record)
            except Exception as e:
                logger.debug(f"[{self.name}] 解析项目失败: {e}")
                continue

        logger.info(f"[{self.name}] 采集完成，共 {len(records)} 条数据")
        return records

    def _parse_item(self, item) -> dict[str, Any] | None:
        """解析单个航班项目"""
        # 解析机型
        title_span = item.find("span", class_="title")
        title = title_span.text.strip() if title_span else ""

        # 解析出发地
        origin_city_span = item.find("span", class_="airportFrom_city")
        origin_city = origin_city_span.text.strip() if origin_city_span else ""

        origin_span = item.find("span", class_="airportFrom")
        origin_code = origin_span.text.strip() if origin_span else ""

        # 解析目的地
        dest_city_span = item.find("span", class_="airportTo_city")
        dest_city = dest_city_span.text.strip() if dest_city_span else ""

        dest_span = item.find("span", class_="airportTo")
        dest_code = dest_span.text.strip() if dest_span else ""

        # 解析时间
        date_div = item.find("div", class_="date")
        depart_time_text = date_div.text.replace("Departure", "").strip() if date_div else ""
        start_time = self._parse_time(depart_time_text)

        # 解析飞行时长
        time_div = item.find("div", class_="time")
        flight_time_text = time_div.text.replace("Time In Air", "").strip() if time_div else ""
        cost_minutes = self._parse_duration(flight_time_text)

        # 解析价格
        price_div = item.find("div", class_="price-trip-price")
        flight_cost = None
        if price_div:
            price_text = price_div.text.strip().replace("$", "").replace(",", "").replace("CAD", "").strip()
            try:
                flight_cost = float(price_text)
            except ValueError:
                pass

        # 解析座位
        passenger_div = item.find("div", class_="passenger")
        seats = 0
        if passenger_div:
            strong = passenger_div.find("strong")
            if strong and strong.text.isdigit():
                seats = int(strong.text)

        # 解析图片
        img = item.find("img")
        thumb = img.get("src") if img else None

        # 解析data-id
        esid = item.get("data-id")

        # 生成唯一ID
        record_id = self.generate_record_id(
            origin_code,
            dest_code,
            depart_time_text,
        )

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
            "start_time": start_time,
            "end_time": None,
            "take_off_time": start_time,
            "cost_minutes": cost_minutes,
            "flight_cost": flight_cost,
            "currency": "CAD",
            "currency_symbol": "$",
            "seats": seats,
            "thumb": thumb,
            "preview": [thumb] if thumb else [],
            "source_url": self.URL,
            "raw_data": {"data_id": esid},
        }

    def _parse_time(self, text: str) -> datetime | None:
        """解析时间文本"""
        try:
            # 尝试多种格式
            for fmt in ["%m/%d/%y", "%m/%d/%Y", "%b %d, %Y", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(text.strip(), fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    def _parse_duration(self, text: str) -> int | None:
        """解析时长文本: '2h 30m' -> 150分钟"""
        try:
            hours = 0
            minutes = 0
            h_match = re.search(r"(\d+)\s*h", text)
            m_match = re.search(r"(\d+)\s*m", text)
            if h_match:
                hours = int(h_match.group(1))
            if m_match:
                minutes = int(m_match.group(1))
            return hours * 60 + minutes if (hours + minutes) > 0 else None
        except Exception:
            return None


def collect() -> list[dict[str, Any]]:
    """执行采集的便捷函数"""
    with ChartRightExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
