<div align="center">
<h1>Spider Awesome 🕷️</h1>
<a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=fff" /></a>
<a href="https://www.sqlalchemy.org"><img src="https://img.shields.io/badge/SQLAlchemy-2.0-009688?logo=sqlalchemy&logoColor=fff" /></a>
<a href="https://pydantic.dev"><img src="https://img.shields.io/badge/Pydantic-2.x-E92063?logo=pydantic&logoColor=fff" /></a>
<a href="https://github.com/microsoft/playwright"><img src="https://img.shields.io/badge/Playwright-Browser-2EAD33?logo=playwright&logoColor=fff" /></a>
<a href="https://www.chromium.org"><img src="https://img.shields.io/badge/Chromium-Headless-4285F4?logo=googlechrome&logoColor=fff" /></a>
<p>Layered-architecture data collection framework with scheduled scheduling, parallel collection, and multi-database support</p>
<a href="README.en.md">English</a> | <a href="README.md">中文</a>
</div>

<br/>

## 📋 Overview

- 🕷️ **Layered Architecture**: Collection / Processing / Storage / Scheduling — four independent layers with clear responsibilities
- 📡 **Plug and Play**: Add a new collector with a single file; auto-discovered and auto-registered
- 🗄️ **Multi-Database**: Unified interface for SQLite / PostgreSQL / MySQL; switch with one config
- ⏰ **Independent Scheduling**: Each collector has its own cron schedule; no interference
- 🔄 **Controlled Concurrency**: Thread pool parallel collection with retry and timeout protection
- 🌍 **Environment Isolation**: dev / test / prod configs; zero-code switching
- 🛡️ **Robustness**: Graceful degradation, log-level control, and auto-retry for unattended operation


<br/>


## 🏗️ Architecture

```mermaid
graph LR
    subgraph Collection Layer
        A1["API Collection<br/>source_api.py"]
        A2["Web Scraping<br/>source_html.py"]
        A3["File Collection<br/>source_file.py"]
    end

    subgraph Processing Layer
        B1["Data Cleaning<br/>Cleaner"]
        B2["Data Validation<br/>Validator"]
    end

    subgraph Storage Layer
        C1["SQLite<br/>Development"]
        C2["PostgreSQL<br/>Production"]
        C3["MySQL<br/>Production"]
    end

    subgraph Scheduling Layer
        D1["Concurrency<br/>ThreadPool"]
        D2["Scheduler<br/>Cron"]
        D3["Retry<br/>Backoff"]
    end

    A1 & A2 & A3 --> B1
    B1 --> B2
    B2 --> C1 & C2 & C3
    D2 -->|Trigger| A1 & A2 & A3

    style A1 fill:#4A90D9,color:#fff
    style A2 fill:#4A90D9,color:#fff
    style A3 fill:#4A90D9,color:#fff
    style B1 fill:#7B68EE,color:#fff
    style B2 fill:#7B68EE,color:#fff
    style C1 fill:#27AE60,color:#fff
    style C2 fill:#27AE60,color:#fff
    style C3 fill:#27AE60,color:#fff
    style D1 fill:#E67E22,color:#fff
    style D2 fill:#E67E22,color:#fff
    style D3 fill:#E67E22,color:#fff
```


<br/>


## 🚀 Quick Start

```bash
$ make
Usage:  make [command] [options]

Available Commands:
   init           Initialize project
   format         Format code
   lint           Lint code
   bandit         Security scan
   clean          Clean project
   dev            Run in dev mode (serial)
   run            Run in production mode (parallel)
   scheduler      Run scheduler
   test           Run tests
   status         Task status
   list           Collector list
   logs           Audit logs
   help           Show help
```

**Switch Environment:**

```bash
# Linux / macOS
ENV_MODE=dev make dev
ENV_MODE=prod make scheduler

# Windows PowerShell
$env:ENV_MODE="prod"; make scheduler
```

**Example Output:**
```bash
$ make dev
🚀  DEV MODE (SERIAL) ...
==================================================
  Starting spider_awesome v1.0.0
  Env: dev | Debug: True
  Database: SQLite
  Log Level: DEBUG
==================================================

12-01 00:47:34 INF __main__:cmd_run_all:63 Running all collectors
12-01 00:47:34 INF src.scheduler.tasks:run_all_collectors:82 [Task] Running all collectors
12-01 19:47:34 INF src.scheduler.tasks:run_collector:28 [Task] Collecting: example_alerion
```
_For more details, see the [Project Documentation](docs/数据采集项目说明文档.md)_

<br/>

## 📄 License

See [MIT License](LICENSE) file.
