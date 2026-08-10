"""
数据清洗模块
去重、空值处理、脏数据过滤
"""
from typing import Any, Dict, List, Optional

from src.common.logger import logger
from src.processor.base_processor import BaseProcessor


class Cleaner(BaseProcessor):
    """
    数据清洗器

    功能：
    - 去除重复数据（基于 ID）
    - 过滤空值记录
    - 去除无效字符
    """

    def __init__(self, required_fields: Optional[List[str]] = None):
        """
        初始化清洗器

        Args:
            required_fields: 必填字段列表，空值记录将被过滤
        """
        self.required_fields = required_fields or ["source"]

    def process(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行数据清洗

        Args:
            records: 待清洗的数据列表

        Returns:
            清洗后的数据列表
        """
        if not records:
            return []

        initial_count = len(records)
        logger.info(f"[Cleaner] 开始清洗 {initial_count} 条数据")

        # 1. 去重（基于 ID）
        records = self._deduplicate(records)

        # 2. 过滤空值记录
        records = self._filter_empty(records)

        # 3. 清理字符串字段
        records = self._clean_strings(records)

        logger.info(f"[Cleaner] 清洗完成，保留 {len(records)} 条数据 (过滤 {initial_count - len(records)} 条)")
        return records

    def _deduplicate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重（基于 ID）"""
        seen_ids = set()
        unique_records = []

        for record in records:
            record_id = record.get("id")
            if record_id and record_id not in seen_ids:
                seen_ids.add(record_id)
                unique_records.append(record)
            elif not record_id:
                unique_records.append(record)

        return unique_records

    def _filter_empty(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤空值记录"""
        filtered = []
        for record in records:
            if all(record.get(field) for field in self.required_fields):
                filtered.append(record)
            else:
                logger.debug(f"过滤空值记录: {record.get('id')}")
        return filtered

    def _clean_strings(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清理字符串字段"""
        for record in records:
            for key, value in record.items():
                if isinstance(value, str):
                    # 去除首尾空白
                    record[key] = value.strip()
                    # 去除不可见字符
                    record[key] = "".join(c for c in value if c.isprintable())
        return records
