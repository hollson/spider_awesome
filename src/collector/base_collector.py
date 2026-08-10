"""
采集器抽象基类
定义所有采集器必须实现的统一接口
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.common.http_client import HttpClient
from src.common.logger import logger
from src.common.utils import generate_id, read_file, write_file


class BaseCollector(ABC):
    """
    采集器抽象基类

    所有采集器必须继承此类并实现以下方法：
    - name: 采集器名称
    - fetch(): 执行采集并返回数据列表
    """

    def __init__(self):
        self._http_client: Optional[HttpClient] = None

    @property
    def name(self) -> str:
        """采集器名称（子类必须重写）"""
        raise NotImplementedError

    @property
    def http_client(self) -> HttpClient:
        """获取 HTTP 客户端"""
        if self._http_client is None:
            self._http_client = HttpClient()
        return self._http_client

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        执行采集

        Returns:
            采集到的数据列表（字典格式）
        """
        raise NotImplementedError

    def close(self):
        """释放资源"""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
        cache_dir = Path("./data/raw")
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / filename

    def read_cache(self, filename: str) -> Optional[str]:
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
        fetch_func,
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

        logger.info(f"[{self.name}] 从 HTTP 读取")
        content = fetch_func()
        self.write_cache(cache_filename, content)
        return content
