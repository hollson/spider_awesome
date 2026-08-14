"""
示例采集器: Silver（Silverhawk Aviation）
演示 HTML 页面解析采集方式

Silverhawk Aviation 是一家美国公务机运营商（总部位于内布拉斯加州林肯市），
主营包机、飞机管理与维护。本采集器解析其空退航班（Empty Legs）
小部件页面（portal.silverhawkaviation.com FlightWidget）中的 HTML 卡片。

数据源: https://silverhawkaviation.com/empty-leg-flights/
特点: 解析 HTML 卡片结构，提取航班信息
"""

import json
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class SilverExampleCollector(BaseCollector):
    """
    Silver 示例采集器
    通过 HTML 解析获取空退航班数据
    """

    OPERATOR_ID: str = "a081e1cc46c64ad39f88b14de6b4ecf6"
    URL: str = "https://portal.silverhawkaviation.com/Widgets/Flights/FlightWidget"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @property
    def name(self) -> str:
        return "example_silver"

    def _make_request(self) -> str:
        """发送请求获取HTML"""
        response = self.http_client.get(url=self.URL, headers=self.HEADERS)
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """执行采集"""
        content = self.fetch_with_cache(
            cache_filename="Silver_raw.html",
            fetch_func=self._make_request,
        )

        records: list[dict[str, Any]] = []
        if not content:
            return records

        soup = BeautifulSoup(content, "html.parser")
        cards = soup.find_all("div", class_="flight-card")

        for card in cards:
            try:
                record = self._parse_card(card)
                if record:
                    records.append(record)
            except Exception as e:
                logger.debug(f"[{self.name}] 解析卡片失败: {e}")
                continue

        logger.info(f"[{self.name}] 采集完成，共 {len(records)} 条数据")
        return records

    def _parse_card(self, card) -> dict[str, Any] | None:
        """解析单个航班卡片"""
        # 解析航线信息: "LAS VEGAS, NEVADA (KLAS) ➡ LINCOLN, NEBRASKA (KLNK)"
        header = card.find("h4", class_="card-header")
        if not header:
            return None

        route_text = header.contents[0].strip() if header.contents else ""
        origin_code, origin_city, dest_code, dest_city = self._parse_route(route_text)

        # 解析座位数
        seats_span = header.find("span", class_="float-right")
        seats = 0
        if seats_span:
            seats_spans = seats_span.find_all("span")
            if len(seats_spans) >= 2:
                seats_text = seats_spans[1].text.strip().replace(" Seats", "")
                seats = int(seats_text) if seats_text.isdigit() else 0

        # 解析机型
        model_p = card.find("p", class_="card-text")
        title = model_p.text.strip() if model_p else ""

        # 解析时间
        time_h5 = card.find("h5", class_="card-title")
        start_time = None
        if time_h5:
            time_text = time_h5.text.strip()
            start_time = self._parse_time(time_text)

        # 解析飞行时长
        duration_p = card.find("p", class_="card-text", style="font-weight: bold;")
        cost_minutes = None
        if duration_p:
            duration_text = duration_p.text.split(": ")[-1].strip()
            cost_minutes = self._parse_duration(duration_text)

        # 解析图片
        images = [img["src"] for img in card.find_all("img", class_="d-block w-100") if img.get("src")]

        # 生成唯一ID
        record_id = self.generate_record_id(
            origin_code,
            dest_code,
            str(start_time.timestamp()) if start_time else "",
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
            "flight_cost": None,
            "currency": None,
            "currency_symbol": None,
            "seats": seats,
            "thumb": images[0] if images else None,
            "preview": images,
            "source_url": self.URL,
            "raw_data": {"html": str(card)},
        }

    def _parse_route(self, text: str) -> tuple[str, str, str, str]:
        """解析航线文本: 'LAS VEGAS (KLAS) ➡ LINCOLN (KLNK)'"""
        parts = text.split("➡")
        if len(parts) != 2:
            return "", "", "", ""

        def extract(text: str) -> tuple[str, str]:
            match = re.match(r"^(.+?)\s+\(([^)]+)\)", text.strip())
            if match:
                return match.group(2), match.group(1)
            return "", text.strip()

        origin_code, origin_city = extract(parts[0])
        dest_code, dest_city = extract(parts[1])
        return origin_code, origin_city, dest_code, dest_city

    def _parse_time(self, text: str) -> datetime | None:
        """解析时间文本"""
        for fmt in ["%m/%d/%Y %I:%M %p", "%Y-%m-%d %H:%M", "%b %d, %Y"]:
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
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
    with SilverExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
