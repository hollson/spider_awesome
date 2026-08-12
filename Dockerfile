# =============================================================================
# Spider Awesome - 通用数据采集模板项目
# =============================================================================
# 构建: docker build -t spider_awesome .
#
# 运行模式:
#   docker run spider_awesome                  # 默认: scheduler (定时调度)
#   docker run spider_awesome run-all          # 串行开发运行
#   docker run spider_awesome run-parallel     # 并行生产运行
#   docker run spider_awesome scheduler        # 定时调度
#   docker run spider_awesome status           # 查看任务状态
#   docker run spider_awesome list             # 查看采集列表
#
# 环境变量:
#   docker run -e ENV_MODE=prod spider_awesome # 指定环境(prod/dev/test)
# =============================================================================

# 基础镜像 (slim 版本体积更小)
FROM python:3.12-slim AS base

# 禁止生成 .pyc 文件，启用无缓冲输出(确保日志实时输出)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 从官方 uv 镜像复制 uv 包管理器(比 pip 更快)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先复制依赖声明文件(利用 Docker 层缓存，依赖不变则跳过安装)
COPY pyproject.toml uv.lock ./

# 安装依赖但不安装项目本身(仅缓存依赖层)
RUN uv sync --frozen --no-dev --no-install-project

# 复制源码
COPY src/ src/

# 安装项目本身
RUN uv sync --frozen --no-dev

# 入口点: 使用 uv run 执行 Python 脚本
ENTRYPOINT ["uv", "run", "python", "src/main.py"]

# 默认命令: 定时调度模式 (可通过 docker run <image> <command> 覆盖)
CMD ["scheduler"]
