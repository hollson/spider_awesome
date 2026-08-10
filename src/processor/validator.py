"""
数据校验模块
使用 Pydantic 进行数据结构校验
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from src.common.logger import logger
from src.processor.base_processor import BaseProcessor


class DataRecordSchema(BaseModel):
    """数据记录校验模型"""
    id: str = Field(..., description="数据唯一标识")
    source: str = Field(..., description="数据来源")
    collector_name: str = Field(..., description="采集器名称")
    operator_id: Optional[str] = None

    title: Optional[str] = None
    tail_num: Optional[str] = None
    model: Optional[str] = None

    origin_code: Optional[str] = None
    origin_city: Optional[str] = None
    dest_code: Optional[str] = None
    dest_city: Optional[str] = None

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    take_off_time: Optional[datetime] = None

    cost_minutes: Optional[int] = None
    flight_cost: Optional[float] = None
    currency: Optional[str] = None
    currency_symbol: Optional[str] = None

    seats: Optional[int] = None
    thumb: Optional[str] = None
    preview: Optional[list] = None
    source_url: Optional[str] = None

    raw_data: Optional[dict] = None

    @validator("seats", pre=True)
    def parse_seats(cls, v):
        """座位数转换"""
        if isinstance(v, str):
            import re
            match = re.search(r"\d+", v)
            return int(match.group()) if match else None
        return v

    @validator("cost_minutes", pre=True)
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

    def process(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            logger.warning(
                f"[Validator] {len(invalid_records)} 条数据校验失败"
            )

        logger.info(
            f"[Validator] 校验完成: {len(valid_records)} 通过, "
            f"{len(invalid_records)} 失败 (共 {initial_count} 条)"
        )
        return valid_records
