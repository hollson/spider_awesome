"""
示例：如何创建自定义采集器

本示例演示如何继承 BaseCollector 创建一个新的采集器
"""
import json
from typing import Any, Dict, List

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class ExampleCollector(BaseCollector):
    """
    示例采集器

    这是一个简单的示例，演示如何创建自定义采集器
    """

    # 运营商 ID（如果需要）
    OPERATOR_ID = "example_operator_id"

    # API URL
    API_URL = "https://jsonplaceholder.typicode.com/posts"

    @property
    def name(self) -> str:
        return "example"

    def _make_request(self) -> str:
        """发送请求"""
        response = self.http_client.get(url=self.API_URL)
        return response.text

    def fetch(self) -> List[Dict[str, Any]]:
        """
        执行采集

        Returns:
            采集到的数据列表
        """
        # 获取数据（带缓存）
        content = self.fetch_with_cache(
            cache_filename="example_raw.json",
            fetch_func=self._make_request,
        )

        # 解析 JSON
        data = json.loads(content)
        records = []

        for item in data:
            try:
                record = self._parse_item(item)
                if record:
                    records.append(record)
            except Exception as e:
                logger.warning(f"[{self.name}] 解析数据失败: {e}")
                continue

        logger.info(f"[{self.name}] 采集完成，共 {len(records)} 条数据")
        return records

    def _parse_item(self, item: dict) -> Dict[str, Any]:
        """解析单条数据"""
        record_id = self.generate_record_id(item.get("id"))

        return {
            "id": record_id,
            "source": self.name,
            "collector_name": self.name,
            "operator_id": self.OPERATOR_ID,
            "title": item.get("title", ""),
            "description": item.get("body", ""),
            "source_url": self.API_URL,
            "raw_data": item,
        }


# 便捷函数
def collect() -> List[Dict[str, Any]]:
    """执行采集的便捷函数"""
    with ExampleCollector() as collector:
        return collector.fetch()


if __name__ == "__main__":
    records = collect()
    print(f"采集到 {len(records)} 条数据")
    for record in records[:3]:
        print(json.dumps(record, indent=2, ensure_ascii=False))
