# Data Collector Template

通用数据采集模板项目，支持 API 接口、网页爬虫、文件等多种数据源采集。

## 架构设计

```
src/
├── collector/      # 采集层：数据拉取
│   ├── base_collector.py   # 采集器抽象基类
│   ├── registry.py         # 采集器注册表
│   └── providers/          # 具体采集器实现
├── processor/      # 处理层：清洗、校验
│   ├── cleaner.py          # 数据清洗
│   └── validator.py        # 数据校验
├── storage/        # 存储层：持久化（SQLAlchemy）
│   └── mysql_store.py      # MySQL 存储
├── scheduler/      # 调度层：定时任务
│   ├── task_manager.py     # 任务管理器（并发控制、失败重试）
│   └── tasks.py            # 任务定义
├── common/         # 公共层：工具库
│   ├── logger.py           # 日志
│   ├── http_client.py      # HTTP 客户端
│   └── utils.py            # 工具函数
├── db/             # ORM：数据模型（SQLAlchemy）
├── env_loader.py   # 环境配置加载器
├── settings.py     # 配置类
└── main.py         # 主入口
```

## 快速开始

### 1. 初始化环境

```bash
make init
# 或手动执行
uv sync
```

### 2. 配置环境变量

```bash
# 编辑开发环境配置
vim configs/.env.dev

# 如需个人覆盖（不提交 Git）
vim configs/.env.local
```

### 3. 运行采集

```bash
# 执行单个采集器
uv run python src/main.py run --source=alerion

# 执行所有采集器（串行）
uv run python src/main.py run-all

# 并行执行采集器
uv run python src/main.py run-parallel

# 并行指定采集器
uv run python src/main.py run-parallel --collectors=alerion,asl

# 试运行（不保存）
uv run python src/main.py run-all --dry-run
```

### 4. 启动定时调度

```bash
uv run python src/main.py scheduler
```

## 环境切换

通过 `ENV_MODE` 环境变量切换配置，零代码改动：

```bash
# Linux / macOS
ENV_MODE=dev uv run python src/main.py run-all
ENV_MODE=prod uv run python src/main.py scheduler

# Windows PowerShell
$env:ENV_MODE="prod"; uv run python src/main.py scheduler
```

## 调度配置

### 串行模式（默认）

每个采集器独立调度，在 `configs/.env` 中配置：

```ini
# 全局默认调度时间
COLLECTOR_CRON_HOUR=0
COLLECTOR_CRON_MINUTE=0

# 单独配置某个采集器（可选）
# COLLECTOR_CRON_ALERION_HOUR=6
# COLLECTOR_CRON_ALERION_MINUTE=30
```

### 并行模式

所有采集器并行执行：

```ini
SCHEDULER_PARALLEL=true
MAX_WORKERS=5
```

### 任务配置

```ini
TASK_TIMEOUT=300      # 单任务超时（秒）
RETRY_COUNT=3         # 失败重试次数
RETRY_DELAY=60        # 重试间隔（秒）
```

## 内置采集器示例

| 采集器 | 类型 | 说明 |
|--------|------|------|
| `alerion` | POST JSON API | 演示 POST 请求采集 |
| `asl` | HTML 分页 | 演示 HTML 解析和分页采集 |
| `noble` | GET JSON API | 演示 GET 请求采集 |

## 添加新采集器

1. 在 `src/collector/providers/` 下创建新文件
2. 继承 `BaseCollector` 并实现 `fetch()` 方法
3. 在 `src/collector/registry.py` 中注册

```python
from src.collector.base_collector import BaseCollector

class MyCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "my_collector"

    def fetch(self):
        # 实现采集逻辑
        return [{"id": "1", "source": "my_source", ...}]
```

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make init` | 初始化环境 |
| `make run SOURCE=alerion` | 运行单个采集器 |
| `make run-all` | 运行所有采集器（串行） |
| `make run-parallel` | 并行运行采集器 |
| `make dry-run` | 试运行（不保存） |
| `make scheduler` | 启动定时调度 |
| `make list` | 列出所有采集器 |
| `make status` | 查看任务状态 |
| `make format` | 格式化代码 |
| `make lint` | 代码检查 |
| `make test` | 运行测试 |
| `make clean` | 清理项目 |

## 开发规范

1. **分层解耦**: 采集 / 处理 / 存储 / 调度四层独立
2. **配置分离**: `.env` 存敏感信息，代码通过 `settings` 单例访问
3. **单条容错**: 单条数据失败不阻断整批任务
4. **原始留存**: `data/raw` 目录永久保留原始数据
5. **依赖管理**: 使用 uv 管理依赖，通过 pyproject.toml 定义

## License

MIT
