"""
示例采集器3: Noble
演示 GET JSON API 采集方式

注意：这是一个示例采集器，衍生项目可参考或删除
"""

import json
import re
from typing import Any

from src.collector.base_collector import BaseCollector
from src.common.logger import logger
from src.common.utils import parse_datetime


class NobleExampleCollector(BaseCollector):
    """
    Noble Air Charter 示例采集器
    通过 GET JSON API 获取空退航班数据
    """

    OPERATOR_ID: str = "0837f31300214e05a9aa24990a16d4e4"
    API_URL: str = "https://portal.nobleaircharter.com/api/nac-connector-empty-leg-trips/get-available-empty-leg-trips"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @property
    def name(self) -> str:
        return "example_noble"

    def _make_request(self) -> str:
        response = self.http_client.get(url=self.API_URL, headers=self.HEADERS, verify=False)
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        content = self.fetch_with_cache(
            cache_filename="Noble_raw.json",
            fetch_func=self._make_request,
        )

        flights = json.loads(content)
        records: list[dict[str, Any]] = []

        for flight in flights:
            try:
                record = self._parse_flight(flight)
                if record:
                    records.append(record)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"[{self.name}] Parse error: {e}")
                continue

        logger.info(f"[{self.name}] Fetched {len(records)} records")
        return records

    def _parse_flight(self, flight: dict) -> dict[str, Any] | None:
        airport_from = flight.get("airport_from", {})
        airport_to = flight.get("airport_to", {})

        depart_date = flight.get("departure_date", "")
        destination_date = flight.get("destination_date", "")
        depart_time = parse_datetime(depart_date, "%Y-%m-%d %H:%M:%S")
        dest_time = parse_datetime(destination_date, "%Y-%m-%d %H:%M:%S")

        flight_minutes = None
        if depart_time and dest_time:
            delta = dest_time - depart_time
            flight_minutes = int(delta.total_seconds() / 60)

        origin_city = self._build_city_name(airport_from)
        dest_city = self._build_city_name(airport_to)

        available = flight.get("available", "").strip()
        start_time = None
        end_time = None
        if available:
            date_range = available.replace("Available ", "").split(" - ")
            if len(date_range) == 2:
                start_time = parse_datetime(date_range[0], "%m/%d/%y")
                end_time = parse_datetime(date_range[1], "%m/%d/%y")

        seats = 0
        seats_str = flight.get("seats", "")
        if seats_str:
            seats_match = re.findall(r"\d+", seats_str)
            seats = int(seats_match[0]) if seats_match else 0

        record_id = self.generate_record_id(
            airport_from.get("identification", ""),
            airport_to.get("identification", ""),
            depart_date,
        )

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.OPERATOR_ID,
            "title": flight.get("plane", ""),
            "tail_num": None,
            "origin_code": airport_from.get("identification", ""),
            "origin_city": origin_city,
            "dest_code": airport_to.get("identification", ""),
            "dest_city": dest_city,
            "start_time": start_time,
            "end_time": end_time,
            "take_off_time": depart_time,
            "cost_minutes": flight_minutes,
            "flight_cost": None,
            "currency": None,
            "currency_symbol": None,
            "seats": seats,
            "thumb": flight.get("plane_image_url"),
            "preview": None,
            "source_url": self.API_URL,
            "raw_data": flight,
        }

    def _build_city_name(self, airport: dict) -> str:
        municipality = airport.get("municipality", "")
        region = airport.get("iso_region", "")
        country = airport.get("iso_country", "")

        parts = [municipality]
        if region:
            parts.append(region.split("-")[-1])
        if country:
            parts.append(country)

        return ", ".join(parts)


def collect() -> list[dict[str, Any]]:
    with NobleExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
