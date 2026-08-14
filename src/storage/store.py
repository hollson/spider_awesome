"""
数据存储实现
使用 SQLAlchemy 进行数据持久化

支持两种存储模式：
- BaseRecordStorage: 通用存储，使用 BaseRecord 表，适用于所有类型的爬虫
- DataStorage: 航空业务存储，使用 DataRecord 表，包含航空业务特定字段

支持 upsert 模式：
- 数据已存在则更新，不存在则插入
- 无需关心数据是否重复
"""

from typing import Any

from sqlalchemy import func

from src.common.logger import logger
from src.storage.base_storage import BaseStorage
from src.storage.models import BaseRecord, DataRecord
from src.storage.session import get_db_instance


class BaseRecordStorage(BaseStorage):
    """
    通用数据存储（使用 BaseRecord 表）

    适用于所有类型的爬虫，只包含公共字段
    衍生项目可直接使用此类
    """

    def __init__(self, auto_create: bool = True):
        """
        初始化存储

        Args:
            auto_create: 是否自动创建表
        """
        if auto_create:
            get_db_instance().create_tables()

    def save(self, records: list[dict[str, Any]]) -> int:
        """
        保存数据（upsert 模式：存在则更新，不存在则插入）

        Args:
            records: 待保存的数据列表

        Returns:
            成功保存的数量（新增 + 更新）
        """
        if not records:
            return 0

        logger.info(f"[Storage] 开始保存 {len(records)} 条数据")
        saved_count = 0
        updated_count = 0

        with get_db_instance().get_session() as session:
            for record in records:
                try:
                    record_id = record.get("id")
                    if not record_id:
                        continue

                    # 检查是否已存在
                    existing = session.query(BaseRecord).filter_by(id=record_id).first()
                    if existing:
                        # 已存在 → 更新
                        existing.title = record.get("title", existing.title)
                        existing.description = record.get("description", existing.description)
                        existing.url = record.get("url") or record.get("source_url") or existing.url
                        existing.raw_data = record.get("raw_data", existing.raw_data)
                        existing.extra = record.get("extra", existing.extra)
                        updated_count += 1
                        logger.debug(f"记录已更新: {record_id}")
                    else:
                        # 不存在 → 插入
                        db_record = BaseRecord(
                            id=record_id,
                            source=record.get("source", ""),
                            collector_name=record.get("collector_name", ""),
                            title=record.get("title"),
                            description=record.get("description"),
                            url=record.get("url") or record.get("source_url"),
                            raw_data=record.get("raw_data"),
                            extra=record.get("extra"),
                        )
                        session.add(db_record)
                        saved_count += 1
                        logger.debug(f"记录新增: {record_id}")
                except Exception as e:
                    logger.warning(f"记录保存失败: {record.get('id')} - {e}")
                    continue

            session.commit()

        # 输出统计
        if updated_count > 0:
            logger.info(f"[Storage] 保存完成: 新增 {saved_count} 条, 更新 {updated_count} 条")
        else:
            logger.info(f"[Storage] 保存完成: 新增 {saved_count} 条")
        return saved_count + updated_count

    def exists(self, record_id: str) -> bool:
        """检查数据是否存在"""
        with get_db_instance().get_session() as session:
            return session.query(BaseRecord).filter_by(id=record_id).count() > 0

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """统计数据数量"""
        with get_db_instance().get_session() as session:
            query = session.query(func.count(BaseRecord.id))
            if filters:
                if "source" in filters:
                    query = query.filter(BaseRecord.source == filters["source"])
                if "collector_name" in filters:
                    query = query.filter(BaseRecord.collector_name == filters["collector_name"])
            return query.scalar()

    def query(
        self,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        查询数据

        Args:
            source: 数据来源
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            数据列表
        """
        with get_db_instance().get_session() as session:
            query = session.query(BaseRecord)

            if source:
                query = query.filter(BaseRecord.source == source)

            records = query.order_by(BaseRecord.create_time.desc()).offset(offset).limit(limit).all()
            return [r.to_dict() for r in records]


class DataStorage(BaseRecordStorage):
    """
    航空业务数据存储（使用 DataRecord 表）

    继承 BaseRecordStorage，添加航空业务特定字段的支持
    如果你的项目不是航空业务，请直接使用 BaseRecordStorage
    """

    def save(self, records: list[dict[str, Any]]) -> int:
        """
        保存航空业务数据（upsert 模式）

        Args:
            records: 待保存的数据列表

        Returns:
            成功保存的数量
        """
        if not records:
            return 0

        logger.info(f"[Storage] 开始保存 {len(records)} 条数据")
        saved_count = 0
        updated_count = 0

        with get_db_instance().get_session() as session:
            for record in records:
                try:
                    record_id = record.get("id")
                    if not record_id:
                        continue

                    # 检查是否已存在
                    existing = session.query(DataRecord).filter_by(id=record_id).first()
                    if existing:
                        # 已存在 → 更新（只更新可变字段）
                        existing.title = record.get("title", existing.title)
                        existing.description = record.get("description", existing.description)
                        existing.raw_data = record.get("raw_data", existing.raw_data)
                        existing.extra = record.get("extra", existing.extra)
                        # 航空业务字段
                        existing.start_time = record.get("start_time", existing.start_time)
                        existing.end_time = record.get("end_time", existing.end_time)
                        existing.take_off_time = record.get("take_off_time", existing.take_off_time)
                        existing.flight_cost = record.get("flight_cost", existing.flight_cost)
                        existing.seats = record.get("seats", existing.seats)
                        updated_count += 1
                        logger.debug(f"记录已更新: {record_id}")
                    else:
                        # 不存在 → 插入
                        db_record = DataRecord(
                            id=record_id,
                            source=record.get("source", ""),
                            collector_name=record.get("collector_name", ""),
                            title=record.get("title"),
                            description=record.get("description"),
                            raw_data=record.get("raw_data"),
                            extra=record.get("extra"),
                            operator_id=record.get("operator_id"),
                            tail_num=record.get("tail_num"),
                            model=record.get("model"),
                            origin_code=record.get("origin_code"),
                            origin_city=record.get("origin_city"),
                            dest_code=record.get("dest_code"),
                            dest_city=record.get("dest_city"),
                            start_time=record.get("start_time"),
                            end_time=record.get("end_time"),
                            take_off_time=record.get("take_off_time"),
                            cost_minutes=record.get("cost_minutes"),
                            flight_cost=record.get("flight_cost"),
                            currency=record.get("currency"),
                            seats=record.get("seats"),
                            thumb=record.get("thumb"),
                            source_url=record.get("url") or record.get("source_url"),
                        )
                        session.add(db_record)
                        saved_count += 1
                        logger.debug(f"记录新增: {record_id}")
                except Exception as e:
                    logger.warning(f"记录保存失败: {record.get('id')} - {e}")
                    continue

            session.commit()

        if updated_count > 0:
            logger.info(f"[Storage] 保存完成: 新增 {saved_count} 条, 更新 {updated_count} 条")
        else:
            logger.info(f"[Storage] 保存完成: 新增 {saved_count} 条")
        return saved_count + updated_count

    def query(
        self,
        source: str | None = None,
        origin_code: str | None = None,
        dest_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        查询航空业务数据

        Args:
            source: 数据来源
            origin_code: 出发地编码
            dest_code: 目的地编码
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            数据列表
        """
        with get_db_instance().get_session() as session:
            query = session.query(DataRecord)

            if source:
                query = query.filter(DataRecord.source == source)
            if origin_code:
                query = query.filter(DataRecord.origin_code == origin_code)
            if dest_code:
                query = query.filter(DataRecord.dest_code == dest_code)

            records = query.order_by(DataRecord.create_time.desc()).offset(offset).limit(limit).all()
            return [r.to_dict() for r in records]
