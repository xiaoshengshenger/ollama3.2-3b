import logging
from pathlib import Path
from typing import Any
import os

from backend_app.constants import PROJECT_ROOT_PATH
from backend_app.api.settings.yaml import load_yaml_with_envvars

logger = logging.getLogger(__name__)

# 仅使用单一配置文件settings.yaml，不支持多profile
_settings_folder = os.environ.get("PGPT_SETTINGS_FOLDER", PROJECT_ROOT_PATH / "backend_app")


def load_active_settings() -> dict[str, Any]:
    """加载单一配置文件settings.yaml"""
    path = Path(_settings_folder) / "settings.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    
    with path.open("r", encoding="utf-8") as f:
        config = load_yaml_with_envvars(f)
    
    if not isinstance(config, dict):
        raise TypeError(f"配置文件顶级结构必须是映射类型: {path}")
    return config