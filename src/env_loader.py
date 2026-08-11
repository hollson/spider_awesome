"""
统一环境配置加载器
负责加载 .env 系列配置文件，实现配置与代码分离
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def _get_configs_dir() -> Path:
    """获取 configs 目录绝对路径（与代码目录同级）"""
    return Path(__file__).resolve().parent.parent / "configs"


def load_all_env() -> str:
    """
    统一加载所有环境配置文件

    加载顺序：公共基础 → 环境专属 → 个人本地
    全部开启 override，后加载覆盖先加载

    Returns:
        当前环境模式 (dev/test/prod)
    """
    configs_dir = _get_configs_dir()
    env_mode = os.getenv("ENV_MODE", "dev")

    env_file_list = [
        configs_dir / ".env",
        configs_dir / f".env.{env_mode}",
        configs_dir / ".env.local",
    ]

    for file_path in env_file_list:
        if file_path.exists():
            load_dotenv(
                dotenv_path=str(file_path),
                override=True,
                encoding="utf-8",
            )

    return env_mode


# 程序入口自动加载（导入模块即触发）
ENV_MODE = load_all_env()
