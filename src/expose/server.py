"""
FastAPI 服务模块
对外提供数据查询和任务管理接口
"""
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from src.settings import settings
from src.common.logger import logger
from src.collector import list_collectors
from src.storage.mysql_store import MySQLStorage

app = FastAPI(
    title=settings.SERVER_NAME,
    description="数据采集模板项目 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """根路径"""
    return {
        "name": settings.SERVER_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/collectors")
def get_collectors():
    """获取所有可用采集器"""
    collectors = list_collectors()
    return {
        "collectors": collectors,
        "total": len(collectors),
    }


@app.get("/api/data")
def query_data(
    source: Optional[str] = Query(None, description="数据来源"),
    origin_code: Optional[str] = Query(None, description="出发地编码"),
    dest_code: Optional[str] = Query(None, description="目的地编码"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """查询数据"""
    storage = MySQLStorage(auto_create=False)
    records = storage.query(
        source=source,
        origin_code=origin_code,
        dest_code=dest_code,
        limit=limit,
        offset=offset,
    )
    return {
        "data": records,
        "total": len(records),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/stats")
def get_stats():
    """获取统计数据"""
    storage = MySQLStorage(auto_create=False)
    total = storage.count()
    return {
        "total_records": total,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/collect/{collector_name}")
def trigger_collect(collector_name: str):
    """手动触发采集任务"""
    from src.scheduler.tasks import run_collector
    from threading import Thread

    try:
        collectors = list_collectors()
        if collector_name not in collectors:
            return {"error": f"Unknown collector: {collector_name}"}

        # 在后台线程中执行
        thread = Thread(target=run_collector, args=(collector_name,))
        thread.start()

        return {
            "message": f"Collection task started: {collector_name}",
            "status": "running",
        }
    except Exception as e:
        logger.error(f"Trigger collect error: {e}")
        return {"error": str(e)}
