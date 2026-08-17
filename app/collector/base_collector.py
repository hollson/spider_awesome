"""
采集器抽象基类
定义所有采集器必须实现的统一接口

健壮性设计：
- fetch 异常自动降级，返回空列表，不阻塞调度
- HTTP 请求自带超时和重试
- 单个采集器失败不影响其他采集器执行
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.common.http_client import HttpClient
from app.common.logger import logger
from app.common.utils import generate_id, read_file, write_file

if TYPE_CHECKING:
    from app.collector.source_define import SourceMeta


class BaseCollector(ABC):
    """
    采集器抽象基类

    所有采集器必须继承此类并实现以下方法：
    - name: 采集器名称
    - fetch(): 执行采集并返回数据列表

    健壮性保证：
    - fetch() 异常时返回空列表，不会抛出异常
    - HTTP 请求自带超时和重试
    - 单个采集器失败不影响其他采集器
    """

    _http_client: HttpClient | None
    _meta: "SourceMeta | None"

    def __init__(self) -> None:
        self._http_client = None
        self._meta = None

    @property
    def name(self) -> str:
        """采集器名称（子类必须重写）"""
        raise NotImplementedError

    @property
    def meta(self) -> "SourceMeta":
        """获取数据源元信息（从 source_define.py 加载）"""
        if self._meta is None:
            from app.collector.source_define import get_source

            self._meta = get_source(self.name)
        return self._meta

    @property
    def http_client(self) -> HttpClient:
        """获取 HTTP 客户端"""
        if self._http_client is None:
            self._http_client = HttpClient()
        return self._http_client

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """
        执行采集（子类必须实现）

        Returns:
            采集到的数据列表（字典格式）

        Raises:
            允许抛出异常，会被 safe_fetch 捕获
        """
        raise NotImplementedError

    def safe_fetch(self) -> list[dict[str, Any]]:
        """
        安全执行采集（带异常捕获和降级）

        - 捕获所有异常，返回空列表
        - 记录错误日志，不阻塞调度
        - 适用于无人值守场景

        Returns:
            采集到的数据列表，失败时返回空列表
        """
        try:
            records = self.fetch()
            return records if isinstance(records, list) else []
        except KeyboardInterrupt:
            raise  # 允许用户中断
        except Exception as e:
            logger.error(f"[{self.name}] 采集异常，已降级: {e}")
            return []

    def close(self) -> None:
        """释放资源"""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "BaseCollector":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        self.close()

    def generate_record_id(self, *fields) -> str:
        """
        生成数据记录唯一 ID

        Args:
            *fields: 用于生成 ID 的字段

        Returns:
            MD5 哈希值
        """
        return generate_id(*fields)

    def get_cache_path(self, filename: str) -> Path:
        """
        获取缓存文件路径

        Args:
            filename: 文件名

        Returns:
            缓存文件完整路径
        """
        from app.settings import settings

        cache_dir = Path(settings.RAW_DATA_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / filename

    def read_cache(self, filename: str) -> str | None:
        """
        读取缓存文件

        Args:
            filename: 文件名

        Returns:
            文件内容，不存在返回 None
        """
        cache_path = self.get_cache_path(filename)
        if cache_path.exists():
            logger.info(f"[{self.name}] 从缓存读取: {cache_path}")
            return read_file(cache_path)
        return None

    def write_cache(self, filename: str, content: str) -> None:
        """
        写入缓存文件

        Args:
            filename: 文件名
            content: 文件内容
        """
        cache_path = self.get_cache_path(filename)
        write_file(cache_path, content)
        logger.debug(f"[{self.name}] 写入缓存: {cache_path}")

    def fetch_with_cache(
        self,
        cache_filename: str,
        fetch_func: Callable[[], str],
        force_refresh: bool = False,
    ) -> str:
        """
        带缓存的采集

        Args:
            cache_filename: 缓存文件名
            fetch_func: 实际采集函数（返回字符串）
            force_refresh: 是否强制刷新缓存

        Returns:
            采集到的内容
        """
        if not force_refresh:
            cached = self.read_cache(cache_filename)
            if cached is not None:
                return cached

        logger.info(f"[{self.name}] 开始 HTTP 请求...")
        content = fetch_func()
        logger.info(f"[{self.name}] HTTP 请求完成，内容长度: {len(content)} 字符")
        self.write_cache(cache_filename, content)
        return content
