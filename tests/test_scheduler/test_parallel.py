"""
并行任务执行测试
验证 run_parallel_collectors 是否真正并行执行
"""

import time
from unittest.mock import patch, MagicMock

import pytest

from src.collector.source_example import (
    ExampleSlowCollector,
    ExampleMediumCollector,
    ExampleFastCollector,
)


# 模拟采集器配置：name -> collector_class
MOCK_COLLECTORS = {
    "example_slow": ExampleSlowCollector,
    "example_medium": ExampleMediumCollector,
    "example_fast": ExampleFastCollector,
}


def _mock_get_collector(name: str):
    """模拟获取采集器实例"""
    cls = MOCK_COLLECTORS.get(name)
    if not cls:
        raise ValueError(f"Unknown collector: {name}")
    return cls()


def _mock_list_collectors():
    """模拟列出所有采集器"""
    return list(MOCK_COLLECTORS.keys())


def _mock_save(records):
    """模拟存储层：直接返回记录数"""
    return len(records)


class TestParallelExecution:
    """并行执行测试"""

    @patch("src.scheduler.tasks.MySQLStorage")
    @patch("src.scheduler.tasks.get_collector", side_effect=_mock_get_collector)
    @patch("src.scheduler.tasks.list_collectors", side_effect=_mock_list_collectors)
    def test_parallel_faster_than_serial(self, mock_list, mock_get, mock_storage_cls):
        """并行执行总耗时应远小于串行执行"""
        mock_storage_cls.return_value.save.side_effect = _mock_save

        from src.scheduler.tasks import run_parallel_collectors

        # 串行预估耗时: 2 + 1 + 0.5 = 3.5s
        serial_estimated = 2 + 1 + 0.5

        start = time.time()
        result = run_parallel_collectors()
        elapsed = time.time() - start

        # 并行耗时应接近最慢的采集器（2s），而非总和（3.5s）
        assert elapsed < serial_estimated - 0.5, (
            f"并行执行耗时 {elapsed:.2f}s，接近串行 {serial_estimated}s，说明并行未生效"
        )

        # 验证所有采集器都执行了
        assert result["total"] == 6  # 2 + 1 + 3 条数据
        assert result["success"] == 6
        assert result["failed"] == 0

    @patch("src.scheduler.tasks.MySQLStorage")
    @patch("src.scheduler.tasks.get_collector", side_effect=_mock_get_collector)
    @patch("src.scheduler.tasks.list_collectors", side_effect=_mock_list_collectors)
    def test_parallel_subset_collectors(self, mock_list, mock_get, mock_storage_cls):
        """并行执行指定采集器子集"""
        mock_storage_cls.return_value.save.side_effect = _mock_save

        from src.scheduler.tasks import run_parallel_collectors

        start = time.time()
        result = run_parallel_collectors(collector_names=["example_medium", "example_fast"])
        elapsed = time.time() - start

        # 中速(1s) + 快速(0.5s) 并行 → 应 < 1.5s
        assert elapsed < 1.5, f"子集并行耗时 {elapsed:.2f}s 过长"

        # medium 1条 + fast 3条 = 4条
        assert result["total"] == 4
        assert result["success"] == 4

    @patch("src.scheduler.tasks.MySQLStorage")
    @patch("src.scheduler.tasks.get_collector", side_effect=_mock_get_collector)
    @patch("src.scheduler.tasks.list_collectors", side_effect=_mock_list_collectors)
    def test_parallel_single_collector(self, mock_list, mock_get, mock_storage_cls):
        """单个采集器并行执行（退化为串行）"""
        mock_storage_cls.return_value.save.side_effect = _mock_save

        from src.scheduler.tasks import run_parallel_collectors

        start = time.time()
        result = run_parallel_collectors(collector_names=["example_slow"])
        elapsed = time.time() - start

        # 单个采集器耗时应约 2s
        assert 1.5 < elapsed < 3.0
        assert result["total"] == 2

    @patch("src.scheduler.tasks.MySQLStorage")
    @patch("src.scheduler.tasks.get_collector", side_effect=_mock_get_collector)
    @patch("src.scheduler.tasks.list_collectors", side_effect=_mock_list_collectors)
    def test_parallel_partial_failure(self, mock_list, mock_get, mock_storage_cls):
        """并行执行中部分采集器失败不影响其他"""
        mock_storage_cls.return_value.save.side_effect = _mock_save

        from src.scheduler.tasks import run_parallel_collectors

        def get_collector_with_error(name: str):
            if name == "example_slow":
                raise RuntimeError("模拟采集失败")
            return _mock_get_collector(name)

        with patch("src.scheduler.tasks.get_collector", side_effect=get_collector_with_error):
            result = run_parallel_collectors()

        # slow 失败，medium(1条) + fast(3条) 成功
        assert result["total"] == 4
        assert result["success"] == 4

    @patch("src.scheduler.tasks.MySQLStorage")
    @patch("src.scheduler.tasks.get_collector", side_effect=_mock_get_collector)
    @patch("src.scheduler.tasks.list_collectors", side_effect=_mock_list_collectors)
    def test_parallel_result_structure(self, mock_list, mock_get, mock_storage_cls):
        """验证返回结果结构正确"""
        mock_storage_cls.return_value.save.side_effect = _mock_save

        from src.scheduler.tasks import run_parallel_collectors

        result = run_parallel_collectors()

        assert isinstance(result, dict)
        assert "total" in result
        assert "success" in result
        assert "failed" in result
        assert result["total"] == result["success"] + result["failed"]
