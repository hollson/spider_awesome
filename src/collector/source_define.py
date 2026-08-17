"""
数据源定义（代码即配置）
============================================================
新增数据源只需两步：
  1. 在下方 SOURCES 字典中注册 SourceMeta
  2. 创建 source_resolve_xxx.py 实现 BaseCollector 子类

【配置优先级】
  1. ENV 环境变量：COLLECTOR_{NAME}_{FIELD}
  2. 本文件默认值

【ENV 覆盖示例】
  COLLECTOR_EXAMPLE_ALERION_enabled=True    # 临时禁用
  COLLECTOR_EXAMPLE_ASL_CRON=0 */3 * * *     # 改频率
  COLLECTOR_EXAMPLE_LUX_TIMEOUT=600          # 改超时

【cron 调度格式】（分 时 日 月 周）
  "0 0 * * *"     → 每天 00:00
  "0 */2 * * *"   → 每 2 小时（00:00, 02:00, ...）
  "30 0 * * *"    → 每天 00:30
  "0 */3 * * *"   → 每 3 小时（00:00, 03:00, ...）
  "*/5 * * * *"   → 每 5 分钟
  "0 9 * * 1-5"   → 工作日 09:00
  "0 0 * * 0"     → 每周日 00:00

【采集器发现机制】
  采集器自动扫描 src/collector/source_resolve_*.py 文件
  - 文件名：source_resolve_{name}.py → 采集器名称 {name}
  - 类名：任意（继承 BaseCollector 即可）
  无需手动注册，只需创建文件即可
============================================================
"""

from dataclasses import dataclass, field
from enum import Enum


class SourceType(Enum):
    """数据源类型"""

    API_JSON = "api_json"
    API_XML = "api_xml"
    HTML_PAGE = "html_page"
    HTML_CARD = "html_card"
    FILE_CSV = "file_csv"


@dataclass
class SourceMeta:
    """数据源完整定义"""

    # ---- 基本信息 ----
    name: str                         # 唯一标识（必须与 source_*.py 对应）
    display_name: str                 # 显示名称
    source_type: SourceType           # 数据源类型
    description: str = ""             # 说明
    url: str = ""                     # 数据源地址
    operator_id: str = ""             # 运营商 ID（可选）

    # ---- 调度配置 ----
    enabled: bool = True              # 是否启用
    cron: str = "0 */1 * * *"         # 默认每小时一次
    timeout: int = 300                # 超时（秒）
    retry: int = 3                    # 重试次数
    retry_delay: int = 60             # 重试间隔（秒）
    persist: bool = True              # 是否入库

    # ---- 示例 ----
    example_output: dict | None = field(default=None, repr=False)  # 示例数据结构
    example_notes: str = ""           # 示例说明


# ============================================================
# 所有数据源定义
# ============================================================
# 新增数据源：在下方添加 SourceMeta 即可

SOURCES: dict[str, SourceMeta] = {

    # ==================================================================
    # 航空数据（示例）
    # ==================================================================

    # Alerion（Alerion Aviation，美国公务机包机商）
    # POST JSON API 采集
    "example_alerion": SourceMeta(
        name="example_alerion",
        display_name="Alerion Aviation",
        source_type=SourceType.API_JSON,
        description="美国公务机包机商，POST JSON API",
        url="https://int-quoting-legacy.flyeasy.co/api/search",
        operator_id="cc2f0c109f7811ec81a473925ff7fe99",
        cron="0 */2 * * *",
        example_output={
            "id": "xxx",
            "tail_num": "N12345",
            "origin_code": "KJFK",
            "dest_code": "KLAX",
            "start_time": "2024-01-01T10:00:00",
            "cost_minutes": 360,
            "flight_cost": 25000,
            "currency": "USD",
        },
        example_notes="API 返回 flights.departing 数组",
    ),

    # ASL（ASL Group，比利时公务航空集团）
    # HTML 分页采集
    "example_asl": SourceMeta(
        name="example_asl",
        display_name="ASL Group",
        source_type=SourceType.HTML_CARD,
        description="比利时公务航空集团，HTML 分页采集",
        url="https://www.aslgroup.eu/en/empty-legs",
        operator_id="5da241f1177e4a41b9ae94f83b44a063",
        cron="30 0 * * *",
        timeout=600,
    ),

    # LuxAviation（卢森堡全球公务航空集团）
    # POST JSON API 分页采集（数据量最大，200+条）
    "example_lux": SourceMeta(
        name="example_lux",
        display_name="LuxAviation",
        source_type=SourceType.API_JSON,
        description="卢森堡全球公务航空集团，POST 分页采集，数据量最大（200+条）",
        url="https://lms-api.luxaviation.com/ext-lead/load-emptylegs",
        operator_id="804d5f81fee1458dbf5140679f60c65c",
        cron="0 */3 * * *",
    ),

    # Silver（Silverhawk Aviation，美国公务机运营商）
    # HTML 卡片解析采集（190+条）
    "example_silver": SourceMeta(
        name="example_silver",
        display_name="Silverhawk Aviation",
        source_type=SourceType.HTML_CARD,
        description="美国公务机运营商，HTML 卡片解析（190+条）",
        url="https://portal.silverhawkaviation.com/Widgets/Flights/FlightWidget",
        operator_id="a081e1cc46c64ad39f88b14de6b4ecf6",
        cron="0 */4 * * *",
    ),

    # ChartRight（Chartright Air Group，加拿大包机公司）
    # HTML 卡片解析采集（40+条）
    "example_chartright": SourceMeta(
        name="example_chartright",
        display_name="Chartright Air Group",
        source_type=SourceType.HTML_CARD,
        description="加拿大包机公司，HTML 卡片解析（40+条）",
        url="https://chartright.com/empty-legs/",
        operator_id="62a7050b3fb646c8b7011687ae7ed9a9",
        cron="30 */2 * * *",
    ),

    # ==================================================================
    # 并发模拟采集器（用于测试并发，不入库）
    # ==================================================================
    # 这三个采集器的唯一用途是验证 run_parallel_collectors 是否真正并行执行
    # 它们通过不同延迟（2s/1s/0.5s）模拟不同速度的网站
    # 串行执行需 3.5s，并行执行只需 ~2s（取决于最慢的那个）

    "example_slow": SourceMeta(
        name="example_slow",
        display_name="慢速模拟（2s）",
        source_type=SourceType.API_JSON,
        description="模拟采集器，延迟 2s，用于测试并行调度",
        enabled=False,
        cron="*/5 * * * *",
        persist=True,
        timeout=30,
    ),

    "example_medium": SourceMeta(
        name="example_medium",
        display_name="中速模拟（1s）",
        source_type=SourceType.API_JSON,
        description="模拟采集器，延迟 1s，用于测试并行调度",
        enabled=False,
        cron="*/5 * * * *",
        persist=True,
        timeout=30,
    ),

    "example_fast": SourceMeta(
        name="example_fast",
        display_name="快速模拟（0.5s）",
        source_type=SourceType.API_JSON,
        description="模拟采集器，延迟 0.5s，用于测试并行调度",
        enabled=False,
        cron="*/5 * * * *",
        persist=True,
        timeout=30,
    ),
}


# ============================================================
# 查询接口
# ============================================================


def get_source(name: str) -> SourceMeta:
    """
    获取指定数据源定义

    Args:
        name: 数据源名称

    Returns:
        数据源元信息

    Raises:
        ValueError: 数据源不存在
    """
    if name not in SOURCES:
        raise ValueError(f"Unknown source: {name}. Available: {list(SOURCES.keys())}")
    return SOURCES[name]


def list_sources(enabled_only: bool = False) -> list[SourceMeta]:
    """
    列出所有数据源

    Args:
        enabled_only: 是否只返回已启用的数据源
    """
    sources = list(SOURCES.values())
    if enabled_only:
        sources = [s for s in sources if s.enabled]
    return sources


def list_source_names(enabled_only: bool = False) -> list[str]:
    """列出所有数据源名称"""
    return [s.name for s in list_sources(enabled_only)]
