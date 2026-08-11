"""
数据校验模块
使用 Pydantic 进行数据结构校验
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.common.logger import logger
from src.processor.base_processor import BaseProcessor


class DataRecordSchema(BaseModel):
    """数据记录校验模型"""

    id: str = Field(..., description="数据唯一标识")
    source: str = Field(..., description="数据来源")
    collector_name: str = Field(..., description="采集器名称")
    operator_id: str | None = None

    title: str | None = None
    tail_num: str | None = None
    model: str | None = None

    origin_code: str | None = None
    origin_city: str | None = None
    dest_code: str | None = None
    dest_city: str | None = None

    start_time: datetime | None = None
    end_time: datetime | None = None
    take_off_time: datetime | None = None

    cost_minutes: int | None = None
    flight_cost: float | None = None
    currency: str | None = None
    currency_symbol: str | None = None

    seats: int | None = None
    thumb: str | None = None
    preview: list | None = None
    source_url: str | None = None

    raw_data: dict | None = None

    @field_validator("seats", mode="before")
    @classmethod
    def parse_seats(cls, v):
        """座位数转换"""
        if isinstance(v, str):
            import re

            match = re.search(r"\d+", v)
            return int(match.group()) if match else None
        return v

    @field_validator("cost_minutes", mode="before")
    @classmethod
    def parse_cost_minutes(cls, v):
        """飞行时长转换"""
        if isinstance(v, str):
            from src.common.utils import cost_minutes

            return cost_minutes(v)
        return v


class Validator(BaseProcessor):
    """
    数据校验器

    功能：
    - 校验数据结构是否符合规范
    - 过滤不合格数据
    - 将不合格数据记录到日志
    """

    def process(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        执行数据校验

        Args:
            records: 待校验的数据列表

        Returns:
            校验通过的数据列表
        """
        if not records:
            return []

        initial_count = len(records)
        valid_records = []
        invalid_records = []

        for record in records:
            try:
                # 校验数据
                validated = DataRecordSchema(**record)
                valid_records.append(validated.dict())
            except Exception as e:
                invalid_records.append((record.get("id"), str(e)))
                logger.warning(f"[Validator] 数据校验失败: {record.get('id')} - {e}")

        if invalid_records:
            logger.warning(f"[Validator] {len(invalid_records)} 条数据校验失败")

        logger.info(
            f"[Validator] 校验完成: {len(valid_records)} 通过, {len(invalid_records)} 失败 (共 {initial_count} 条)"
        )
        return valid_records
