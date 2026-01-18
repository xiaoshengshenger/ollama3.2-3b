import logging
import os
# 配置日志
logger = logging.getLogger(__name__)


# ======================
# 新增：本地模型路径配置函数
# ======================
def get_local_embedding_model_path() -> str:
    """
    获取本地BAAI/bge-small-zh模型路径（根目录固定，直接拼接）
    前提：当前函数所在文件位于backend/目录下（根目录）
    目标路径：backend/cache/models--BAAI--bge-small-zh
    """
    CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 2. 向上跳1级，拿到真正的backend/目录（核心修正）
    BACKEND_ROOT_DIR = os.path.abspath(os.path.join(CURRENT_FILE_DIR, "../../../"))

    # 2. 直接拼接模型路径（一步到位，无冗余逻辑）
    LOCAL_MODEL_DIR = os.path.normpath(
        os.path.join(BACKEND_ROOT_DIR, "cache/models/BAAI--bge--small--zh")
    )
    return LOCAL_MODEL_DIR


# 检查本地模型目录是否有效
def is_model_dir_valid(model_dir: str) -> bool:
    """
    用路径拼接的方式检查模型目录是否有效（替代遍历，更高效）
    规则：必需文件（config.json、tokenizer.json）全部存在 + 权重文件至少一个存在
    """
    # 定义需要检查的文件
    required_files = ["config.json", "tokenizer.json"]  # 必需文件（全要存在）
    optional_files = ["pytorch_model.bin", "model.safetensors"]  # 可选文件（二选一）
    
    # 第一步：检查模型目录是否存在
    if not os.path.exists(model_dir):
        logger.error(f"模型目录不存在：{model_dir}")
        return False
    
    # 第二步：检查必需文件（拼接路径 + 逐个验证）
    has_required = True
    missing_required = []
    for file_name in required_files:
        # 核心：拼接「模型目录 + 文件名」得到完整路径
        file_path = os.path.join(model_dir, file_name)
        if not os.path.exists(file_path):
            has_required = False
            missing_required.append(file_name)
    
    if not has_required:
        logger.error(f"缺少必需文件：{missing_required}，模型目录：{model_dir}")
        return False
    
    # 第三步：检查可选文件（拼接路径 + 至少一个存在）
    has_weights = False
    found_optional = []
    for file_name in optional_files:
        file_path = os.path.join(model_dir, file_name)
        if os.path.exists(file_path):
            has_weights = True
            found_optional.append(file_name)
    
    if not has_weights:
        logger.error(f"缺少权重文件（需至少一个）：{optional_files}，模型目录：{model_dir}")
        return False
    
    # 所有检查通过
    logger.info(f"模型目录验证通过")
    return True