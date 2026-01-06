from pathlib import Path
from typing import Optional

PROJECT_ROOT_PATH: Path = Path(__file__).parents[1]

models_cache_path: Path = PROJECT_ROOT_PATH / "cache"

import logging

logger = logging.getLogger(__name__)
_local_data_path: Optional[Path] = None

def get_local_data_path() -> Path:
    """延迟获取本地数据路径，仅在首次使用时初始化，打破循环导入"""
    global _local_data_path
    if _local_data_path is not None:
        return _local_data_path  # 缓存结果，避免重复计算
    
    # 延迟导入：仅在函数被调用时才导入 settings（此时所有模块已初始化完成）
    from backend_app.api.settings.settings import settings
    
    def _absolute_or_from_project_root(path: str) -> Path:
        if path.startswith("/"):
            return Path(path)
        return PROJECT_ROOT_PATH / path
    
    # 计算并缓存路径
    _local_data_path = _absolute_or_from_project_root(settings().data.local_data_folder)
    logger.info(f"Local data path set to: {_local_data_path}")
    return _local_data_path


def get_local_kg_data_path() -> Path:
    """延迟获取本地数据路径，仅在首次使用时初始化，打破循环导入"""
    global _local_data_path
    if _local_data_path is not None:
        return _local_data_path  # 缓存结果，避免重复计算
    
    # 延迟导入：仅在函数被调用时才导入 settings（此时所有模块已初始化完成）
    from backend_app.api.settings.settings import settings
    
    def _absolute_or_from_project_root(path: str) -> Path:
        if path.startswith("/"):
            return Path(path)
        return PROJECT_ROOT_PATH / path
    
    # 计算并缓存路径
    _local_data_path = _absolute_or_from_project_root(settings().data.local_kg_data_folder)
    logger.info(f"Local kg data path set to: {_local_data_path}")
    return _local_data_path
