"""
示例采集器1: Alerion
演示 POST JSON API 采集方式
"""

import json
from typing import Any

from dateutil import parser as date_parser

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class AlerionCollector(BaseCollector):
    """
    Alerion 采集器
    通过 POST JSON API 获取空退航班数据
    """

    # 运营商 ID
    OPERATOR_ID = "cc2f0c109f7811ec81a473925ff7fe99"

    # API 配置
    API_URL = "https://int-quoting-legacy.flyeasy.co/api/search"

    # 请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://widgets-ecs.tuvoli.com",
        "Referer": "https://widgets-ecs.tuvoli.com/",
    }

    # 请求体
    PAYLOAD = {
        "source": "eq",
        "trip": "offers",
        "promoteOpIds": "all",
        "opIds": ["57da0aaac1fe036a3c70e966"],
    }

    @property
    def name(self) -> str:
        return "Alerion"

    def _make_request(self) -> str:
        """发送请求并返回响应内容"""
        response = self.http_client.post(
            url=self.API_URL,
            headers=self.HEADERS,
            json=self.PAYLOAD,
        )
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """
        执行采集

        Returns:
            采集到的数据列表
        """
        # 获取数据（带缓存）
        content = self.fetch_with_cache(
            cache_filename="Alerion_raw.json",
            fetch_func=self._make_request,
        )

        # 解析 JSON
        data = json.loads(content)
        records = []

        # 提取航班数据
        flights = data.get("flights", {}).get("departing", [])
        for flight in flights:
            try:
                record = self._parse_flight(flight)
                if record:
                    records.append(record)
            except Exception as e:
                logger.warning(f"[{self.name}] 解析航班数据失败: {e}")
                continue

        logger.info(f"[{self.name}] 采集完成，共 {len(records)} 条数据")
        return records

    def _parse_flight(self, flight: dict) -> dict[str, Any] | None:
        """解析单条航班数据"""
        ac = flight.get("ac", {})
        airport_from = flight.get("airportFrom", {})
        airport_to = flight.get("airportTo", {})
        schedule_item = flight.get("scheduleItem", {})

        # 生成唯一 ID
        record_id = self.generate_record_id(
            ac.get("reg", ""),
            ac.get("title", ""),
            airport_from.get("icao", ""),
            airport_to.get("icao", ""),
        )

        # 解析时间
        start_time = None
        end_time = None
        take_off_time = None
        try:
            if flight.get("date1"):
                start_time = date_parser.isoparse(flight["date1"])
            if flight.get("date2"):
                end_time = date_parser.isoparse(flight["date2"])
            if schedule_item.get("takeOffDate"):
                take_off_time = date_parser.isoparse(schedule_item["takeOffDate"])
        except Exception as e:
            logger.debug(f"时间解析失败: {e}")

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.OPERATOR_ID,
            "title": ac.get("title", ""),
            "tail_num": ac.get("reg", ""),
            "origin_code": airport_from.get("icao", ""),
            "origin_city": airport_from.get("city", ""),
            "dest_code": airport_to.get("icao", ""),
            "dest_city": airport_to.get("city", ""),
            "start_time": start_time,
            "end_time": end_time,
            "take_off_time": take_off_time,
            "cost_minutes": int(flight["flightTimeDec"] * 60)
            if flight.get("flightTimeDec")
            else None,
            "flight_cost": flight.get("acPrice"),
            "currency": ac.get("currency", ""),
            "currency_symbol": "$",
            "seats": ac.get("pax"),
            "thumb": next((img for img in ac.get("minImages", [])), None),
            "preview": ac.get("images", []),
            "source_url": self.API_URL,
            "raw_data": flight,
        }


# 便捷函数
def collect() -> list[dict[str, Any]]:
    """执行采集的便捷函数"""
    with AlerionCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
