"""公共层模块"""

from app.common.color import banner_label, banner_line, banner_title, colored  # 颜色
from app.common.convert_utils import (  # 类型转换
    format_price,
    safe_json,
    to_bool,
    to_float,
    to_int,
)
from app.common.data_utils import (  # 数据处理
    chunk_list,
    deduplicate,
    filter_none,
    flatten_dict,
    merge_dicts,
    safe_get,
)
from app.common.exceptions import (
    CollectorError,
    DatabaseError,
    DataCollectorError,
    ParseError,
    ProcessorError,
    RequestError,
    SchedulerError,
    StorageError,
    ValidationError,
)
from app.common.file_utils import (  # 文件操作
    file_hash,
    load_json,
    load_jsonl,
    safe_filename,
    save_csv,
    save_json,
)
from app.common.html import HtmlProcessor, compress_html
from app.common.http_client import HttpClient, create_client
from app.common.logger import logger, setup_logger
from app.common.text_utils import (  # 文本清洗
    clean_text,
    extract_between,
    extract_ints,
    extract_numbers,
    remove_html_tags,
    truncate_text,
)
from app.common.url_utils import (  # URL 处理
    decode_url,
    encode_url,
    extract_domain,
    extract_query_params,
    is_same_domain,
    is_valid_url,
    join_url,
    normalize_url,
)
from app.common.utils import (  # 基础工具
    cost_minutes,
    ensure_dir,
    generate_id,
    parse_datetime,
    read_file,
    write_file,
)

__all__ = [
    # 颜色
    "colored",
    "banner_line",
    "banner_title",
    "banner_label",
    # 日志
    "logger",
    "setup_logger",
    # HTTP
    "HttpClient",
    "create_client",
    # 基础工具
    "generate_id",
    "parse_datetime",
    "cost_minutes",
    "ensure_dir",
    "read_file",
    "write_file",
    # 文本清洗
    "clean_text",
    "truncate_text",
    "extract_numbers",
    "extract_ints",
    "extract_between",
    "remove_html_tags",
    # 类型转换
    "to_int",
    "to_float",
    "to_bool",
    "safe_json",
    "format_price",
    # 数据处理
    "safe_get",
    "deduplicate",
    "chunk_list",
    "merge_dicts",
    "filter_none",
    "flatten_dict",
    # URL 处理
    "normalize_url",
    "is_valid_url",
    "extract_domain",
    "join_url",
    "extract_query_params",
    "encode_url",
    "decode_url",
    "is_same_domain",
    # 文件操作
    "save_json",
    "load_json",
    "load_jsonl",
    "save_csv",
    "safe_filename",
    "file_hash",
    # HTML
    "compress_html",
    "HtmlProcessor",
    # 异常
    "DataCollectorError",
    "CollectorError",
    "RequestError",
    "ParseError",
    "ProcessorError",
    "ValidationError",
    "StorageError",
    "DatabaseError",
    "SchedulerError",
]
