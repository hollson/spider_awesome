"""
示例采集器: LuxAviation（Luxaviation）
演示 POST JSON API 分页采集方式

Luxaviation 是一家卢森堡的全球公务航空集团，为全球最大的
公务机运营商之一（luxaviation.com）。本采集器对接其官网
空退航班（Empty Legs）接口（lms-api.luxaviation.com），
POST JSON 请求、分页采集。

数据源: https://www.luxaviation.com/jets/jet-charter/empty-legs/
API: https://lms-api.luxaviation.com/ext-lead/load-emptylegs
特点: 分页采集，每页200条，支持多页
"""

import json
from datetime import datetime
from typing import Any

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class LuxAviationExampleCollector(BaseCollector):
    """
    LuxAviation 示例采集器
    通过 POST JSON API 获取空退航班数据（分页）
    """

    OPERATOR_ID: str = "804d5f81fee1458dbf5140679f60c65c"
    API_URL: str = "https://lms-api.luxaviation.com/ext-lead/load-emptylegs"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.luxaviation.com",
        "Referer": "https://www.luxaviation.com/",
    }

    @property
    def name(self) -> str:
        return "example_lux"

    def _make_request(self, page: int = 1, per_page: int = 200) -> str:
        """发送分页请求"""
        payload = {
            "perPage": per_page,
            "page": page,
            "totalCount": 0,
            "pages": [],
            "region": "",
        }
        response = self.http_client.post(
            url=self.API_URL,
            headers=self.HEADERS,
            json=payload,
        )
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """分页采集所有数据"""
        records: list[dict[str, Any]] = []

        # 第一页
        content = self._make_request(page=1)
        data = json.loads(content)
        total_count = int(data.get("total", 0))
        first_page_records = self._parse_page(data)
        records.extend(first_page_records)

        logger.info(f"[{self.name}] 第1页: {len(first_page_records)} 条, 总计: {total_count}")

        # 计算总页数
        per_page = 200
        total_pages = (total_count // per_page) + (1 if total_count % per_page != 0 else 0)

        # 采集剩余页
        for page in range(2, total_pages + 1):
            content = self._make_request(page=page)
            data = json.loads(content)
            page_records = self._parse_page(data)
            records.extend(page_records)
            logger.info(f"[{self.name}] 第{page}页: {len(page_records)} 条")

        logger.info(f"[{self.name}] 采集完成，共 {len(records)} 条数据")
        return records

    def _parse_page(self, data: dict) -> list[dict[str, Any]]:
        """解析单页数据"""
        records: list[dict[str, Any]] = []
        items = data.get("records", [])

        for item in items:
            try:
                record = self._parse_record(item)
                if record:
                    records.append(record)
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"[{self.name}] 解析记录失败: {e}")
                continue

        return records

    def _parse_record(self, item: dict) -> dict[str, Any] | None:
        """解析单条记录"""
        aircraft = item.get("aircraft", {})
        reg_num = aircraft.get("regNum", "").replace("-", "")

        # 生成唯一ID
        record_id = self.generate_record_id(
            reg_num,
            item.get("fromIcao", ""),
            item.get("toIcao", ""),
            item.get("depDate", ""),
        )

        # 解析时间
        dep_date = item.get("depDate")
        arr_date = item.get("arrDate")
        start_time = None
        end_time = None
        if dep_date:
            try:
                start_time = datetime.fromisoformat(dep_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if arr_date:
            try:
                end_time = datetime.fromisoformat(arr_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # 图片URL
        cover_img = item.get("coverImgPath", "")
        thumb = f"https://lms-api.luxaviation.com/{cover_img}" if cover_img else None

        images = item.get("aircraftImages", [])
        preview = [f"https://lms-api.luxaviation.com/{img.get('path', '')}" for img in images if img.get("path")]

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.OPERATOR_ID,
            "title": aircraft.get("displayName", ""),
            "tail_num": reg_num,
            "origin_code": item.get("fromIcao", ""),
            "origin_city": item.get("from", ""),
            "dest_code": item.get("toIcao", ""),
            "dest_city": item.get("to", ""),
            "start_time": start_time,
            "end_time": end_time,
            "take_off_time": start_time,
            "cost_minutes": item.get("flightTimeMin"),
            "flight_cost": item.get("flightCost"),
            "currency": item.get("currency"),
            "currency_symbol": None,
            "seats": aircraft.get("passengers"),
            "thumb": thumb,
            "preview": preview,
            "source_url": self.API_URL,
            "raw_data": item,
        }


def collect() -> list[dict[str, Any]]:
    """执行采集的便捷函数"""
    with LuxAviationExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    for record in records[:3]:
        print(json.dumps(record, indent=2, default=str))
