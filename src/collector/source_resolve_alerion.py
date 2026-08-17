"""
示例采集器1: Alerion（Alerion Aviation）
演示 POST JSON API 采集方式

Alerion Aviation 是一家美国公务机包机运营商（总部位于纽约），
主营私人包机、飞机管理与飞行部运营业务。本采集器对接其
空退航班（Empty Legs）报价数据：由 Tuvoli 报价引擎
（widgets-ecs.tuvoli.com / flyeasy.co）提供，POST JSON 请求。

注意：这是一个示例采集器，衍生项目可参考或删除
"""

import json
from typing import Any

from dateutil import parser as date_parser

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class AlerionResolver(BaseCollector):
    """
    Alerion 解析器
    通过 POST JSON API 获取空退航班数据
    """

    # 请求头
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://widgets-ecs.tuvoli.com",
        "Referer": "https://widgets-ecs.tuvoli.com/",
    }

    # 请求体
    PAYLOAD: dict[str, Any] = {
        "source": "eq",
        "trip": "offers",
        "promoteOpIds": "all",
        "opIds": ["57da0aaac1fe036a3c70e966"],
    }

    @property
    def name(self) -> str:
        return "example_alerion"

    def _make_request(self) -> str:
        """发送请求并返回响应内容"""
        response = self.http_client.post(
            url=self.meta.url,
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
        records: list[dict[str, Any]] = []

        # 提取航班数据
        flights = data.get("flights", {}).get("departing", [])
        for flight in flights:
            try:
                record = self._parse_flight(flight)
                if record:
                    records.append(record)
            except (KeyError, ValueError, TypeError) as e:
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
        except (ValueError, TypeError) as e:
            logger.debug(f"时间解析失败: {e}")

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.meta.operator_id,
            "title": ac.get("title", ""),
            "tail_num": ac.get("reg", ""),
            "origin_code": airport_from.get("icao", ""),
            "origin_city": airport_from.get("city", ""),
            "dest_code": airport_to.get("icao", ""),
            "dest_city": airport_to.get("city", ""),
            "start_time": start_time,
            "end_time": end_time,
            "take_off_time": take_off_time,
            "cost_minutes": int(flight["flightTimeDec"] * 60) if flight.get("flightTimeDec") else None,
            "flight_cost": flight.get("acPrice"),
            "currency": ac.get("currency", ""),
            "currency_symbol": "$",
            "seats": ac.get("pax"),
            "thumb": next((img for img in ac.get("minImages", [])), None),
            "preview": ac.get("images", []),
            "source_url": self.meta.url,
            "raw_data": flight,
        }


# 便捷函数
def collect() -> list[dict[str, Any]]:
    """执行采集的便捷函数"""
    with AlerionResolver() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
