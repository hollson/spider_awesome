.SILENT:
SHELL := /bin/bash
all: help

# ======================================================================================================
# 数据采集模板项目 Makefile
# ======================================================================================================

# 公共命令：自动检测可用的 Python 解释器
PYTHON_CMD := $(shell set -e; for X in python3 python py; do if command -v $$X >/dev/null 2>&1; then if $$X --version >/dev/null 2>&1; then echo $$X; break; fi; fi; done)

# 检查是否在WSL或Linux/Mac环境
define check_wsl_linux_mac
	@if [ -n "$(ComSpec)" ] || [ -n "$${COMSPEC}" ]; then \
		echo "❌ 仅限WSL或Linux/Mac环境..."; \
		exit 1; \
	fi
endef


# UV安装函数
define install_uv
	@bash -c ' \
		if command -v uv >/dev/null 2>&1; then \
			echo "✅ UV 已安装: $$(uv --version)"; \
		else \
			echo "📦 UV 未安装，正在自动安装..."; \
			case "$$(uname -s)" in \
				Linux*|Darwin*) \
					echo "🌐 正在从 https://astral.sh/uv/install.sh 下载安装..."; \
					if curl -LsSf https://astral.sh/uv/install.sh | sh; then \
						export PATH="$${HOME}/.local/bin:$${PATH}"; \
						echo "🎉 UV 安装成功: $$(uv --version)"; \
					else \
						echo "❌ 网络错误或超时，请手动安装 uv"; \
						exit 1; \
					fi \
					;; \
				MINGW*|MSYS*|CYGWIN*|Windows*) \
					echo "🔧 检测到 Windows 系统，尝试使用 PowerShell 安装..."; \
					powershell -ExecutionPolicy ByPass -Command "\
						$$tempFile = \"$$env:TEMP\\uv_install.ps1\"; \
						(New-Object System.Net.WebClient).DownloadFile('https://astral.sh/uv/install.ps1', $$tempFile); \
						& $$tempFile \
					" && \
					echo "🎉 UV 安装完成，请重启终端"; \
					;; \
				*) \
					echo "❌ 不支持的操作系统: $$(uname -s)"; \
					exit 1 \
					;; \
			esac; \
		fi'
endef


# 检查并安装全局工具
define install_tool
	@if ! uv tool list | grep -q "$1"; then \
		echo "📦 Installing $1..."; \
		uv tool install $1 --quiet; \
		echo "✅ $1 installed"; \
	fi
endef


# 基础清理函数
define clean_handler
	@echo ""
	@echo "📂 将清理以下内容："
	@echo "   - Python 字节码（*.pyc, *.pyo, __pycache__）"
	@echo "   - 测试产物（.pytest_cache, .coverage, var/pytest_cache, var/coverage, var/output）"
	@echo "   - 工具缓存（.ruff_cache）"
	@echo "   - 构建产物（dist/, build/, *.egg-info/）"
	@echo ""
	@echo "⚠️  保留：数据库(var/database)、原始缓存(var/raw)、日志(var/logs)"
	@echo ""
	@read -p "确认清理？[y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "📂 清理 Python 字节码..."; \
		find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true; \
		find . -type d -name "__pycache__" -delete 2>/dev/null || true; \
		echo "💾 清理测试产物..."; \
		rm -rf .pytest_cache .coverage var/pytest_cache var/coverage var/output; \
		echo "🔧 清理工具缓存..."; \
		rm -rf .ruff_cache; \
		echo "📦 清理构建产物..."; \
		rm -rf dist/ build/ .eggs/ *.egg-info/; \
		echo "✅ 清理完成"; \
	else \
		echo "⏭️  已跳过清理"; \
	fi
endef

# ======================================================================================================

#HELP init@初始化
.PHONY: init
init:
	@echo "🌌 初始化环境..."
	$(call install_uv)
	@if [ ! -d ".venv" ]; then \
		echo "📦 创建虚拟环境..."; \
		uv venv; \
	fi
	@echo "📥 安装依赖..."
	uv sync
	@echo "✅ 环境初始化完成"


#HELP lint@代码检查
.PHONY: lint
lint:
	$(call install_tool,ruff)
	@echo "🔍 代码检查..."
	@uv tool run ruff check src/ --fix || true
	@echo "✅ 检查完成"


#HELP bandit@安全扫描
.PHONY: bandit
bandit:
	$(call install_tool,bandit)
	@echo "🔒 安全漏洞扫描..."
	@uv tool run bandit -r src/ -s B101 -f screen
	@echo "✅ 安全扫描完成"


#HELP format@格式化代码
.PHONY: format
format:
	$(call install_tool,ruff)
	@echo "📝 格式化代码..."
	@uv tool run ruff format .
	@echo "✅ 格式化完成"


#HELP clean@清理项目
.PHONY: clean
clean:
	$(call clean_handler)
	@echo "✅ 项目清理完成"


#HELP dev@开发运行（串行）
.PHONY: dev
dev:
	@echo "🚀 开发运行（串行）..."
	@mkdir -p var && echo "dev" > var/.env_mode
	@ENV_MODE=dev uv run python src/main.py run-all


#HELP run@生产运行（并行）
.PHONY: run
run:
	@echo "🚀 生产运行（并行）..."
	@mkdir -p var && echo "prod" > var/.env_mode
	@ENV_MODE=prod uv run python src/main.py run-parallel


#HELP scheduler@生产运行（定时）
.PHONY: scheduler
scheduler:
	@echo "⏰ 启动定时调度..."
	@mkdir -p var && echo "prod" > var/.env_mode
	@ENV_MODE=prod uv run python src/main.py scheduler


#HELP test@运行测试
.PHONY: test
test:
	@echo "🧪 运行测试..."
	@mkdir -p var && echo "test" > var/.env_mode
	@mkdir -p var/coverage/data var/coverage/report
	@ENV_MODE=test COVERAGE_FILE=var/coverage/data/.coverage uv run pytest tests/ -v --cov=src --cov-report=html:var/coverage/report/htmlcov --cov-report=xml:var/coverage/report/coverage.xml --cov-report=term-missing
	@echo "✅ 测试完成，报告位于 var/coverage/report/htmlcov/"


#HELP status@任务状态
.PHONY: status
status:
	@uv run python src/main.py status


#HELP list@采集列表
.PHONY: list
list:
	@uv run python src/main.py list


#HELP logs@审计日志
.PHONY: logs
logs:
	@if [ -f var/.env_mode ]; then \
		ENV=$$(cat var/.env_mode); \
		echo "📋 查看审计日志 (环境: $$ENV)"; \
		ENV_MODE=$$ENV uv run python src/main.py logs; \
	else \
		echo "⚠️  未找到运行记录，请先执行 make dev/make run/make scheduler"; \
	fi


#HELP help@查看帮助
.PHONY: help
help: Makefile
	@echo "Usage:  make [command] [options]"
	@echo
	@echo "Available Commands:"
	@sed -n "s/^#HELP//p" $(firstword $(MAKEFILE_LIST)) | awk -F'@' '{ printf "  \033[1;31m%-16s\033[0m%s\n", $$1, $$2 }'
	@echo

