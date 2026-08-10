# Data Collector Template

通用数据采集模板项目，支持 API 接口、网页爬虫、文件等多种数据源采集。

## 架构设计

```
├── src/
│   ├── collector/      # 采集层：数据拉取
│   ├── processor/      # 处理层：清洗、校验
│   ├── storage/        # 存储层：持久化
│   ├── expose/         # API 层：对外服务
│   ├── scheduler/      # 调度层：定时任务
│   ├── common/         # 公共层：工具库
│   ├── db/             # ORM：数据模型
│   ├── env_loader.py   # 环境配置加载器
│   └── settings.py     # 配置类
├── configs/            # 环境配置文件
│   ├── .env            # 公共基础配置
│   ├── .env.dev        # 开发环境
│   ├── .env.test       # 测试环境
│   ├── .env.prod       # 生产环境（占位符）
│   └── .env.local      # 个人本地覆盖（不提交）
├── data/               # 数据目录
├── logs/               # 日志目录
└── tests/              # 测试目录
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

# 执行所有采集器
uv run python src/main.py run-all

# 仅采集不保存（Dry Run）
uv run python src/main.py run-all --dry-run

# 列出所有可用采集器
uv run python src/main.py list
```

### 4. 启动定时调度

```bash
uv run python src/main.py scheduler
```

### 5. 启动 API 服务

```bash
uv run python src/main.py api
# 访问 http://localhost:8000/docs 查看接口文档
```

## 环境切换

通过 `ENV_MODE` 环境变量切换配置，零代码改动：

```bash
# Linux / macOS
ENV_MODE=dev uv run python src/main.py run-all
ENV_MODE=test uv run python src/main.py run-all
ENV_MODE=prod uv run python src/main.py run-all

# Windows CMD
set ENV_MODE=prod && uv run python src/main.py run-all

# Windows PowerShell
$env:ENV_MODE="prod"; uv run python src/main.py run-all
```

**配置加载优先级**（高 → 低）：
1. 系统环境变量
2. `configs/.env.local`（个人覆盖）
3. `configs/.env.{mode}`（环境专属）
4. `configs/.env`（公共基础）

## 内置采集器示例

| 采集器 | 类型 | 说明 |
|--------|------|------|
| `alerion` | POST JSON API | 演示 POST 请求采集 |
| `asl` | HTML 分页 | 演示 HTML 解析和分页采集 |
| `noble` | GET JSON API | 演示 GET 请求采集 |

## 添加新采集器

1. 在 `src/collector/` 下创建新文件
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

## 开发规范

1. **分层解耦**: 采集 / 处理 / 存储 / 暴露四层独立
2. **配置分离**: `.env` 存敏感信息，代码通过 `settings` 单例访问
3. **单条容错**: 单条数据失败不阻断整批任务
4. **原始留存**: `data/raw` 目录永久保留原始数据
5. **依赖管理**: 使用 uv 管理依赖，通过 pyproject.toml 定义

## License

MIT
