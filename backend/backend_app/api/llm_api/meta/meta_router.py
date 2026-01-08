from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend_app.api.tools.generate_code import verify_permission_code
import logging

logger = logging.getLogger(__name__)

meta_router = APIRouter()

# 定义前端请求体模型（匹配前端传递的 JSON 结构）
class CodeRequest(BaseModel):
    code: str

# 修正响应模型：字段类型和实际返回值匹配
# 核心修改：将原本错误的 str 改为 int，package 单独处理为字符串（套餐名称）
class MetaResponse(BaseModel):
    package_type: int
    package_name: str
    max_queries: int
    allowed_models: list[str]
    expire_time: str
    file_limit_mb: int
    db_limit_gb: int
    is_valid: bool

# 套餐类型数字 → 名称映射（解决 package 字段字符串要求）
PACKAGE_NAME_MAP = {
    0: "weekly",    # 一周体验
    1: "monthly",   # 月会员
    2: "quarterly", # 季会员
    3: "annual",    # 年会员
    4: "permanent", # 永久会员
    5: "free"       # 免费用户
}

@meta_router.post("/code", response_model=MetaResponse)
def validate_code(code_request: CodeRequest):
    """验证激活码接口，修复字段类型不匹配问题"""
    try:
        # 1. 获取前端传递的激活码
        code = code_request.code
        logger.info(f"开始验证激活码：{code}...") 

        # 2. 调用验证函数（解构返回值：是否有效 + 信息字典）
        is_valid, info = verify_permission_code(code)
        
        # 3. 验证失败：抛出 400 错误
        if not is_valid:
            error_msg = info.get("error", "激活码验证失败")
            logger.error(f"激活码验证失败：{error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        # 4. 验证成功：组装响应数据（类型完全匹配 MetaResponse）
        # 核心：将 package_type（数字）映射为字符串名称
        # package_name = PACKAGE_NAME_MAP.get(info["package_type"], "unknown")
        logger.info(f"激活码验证成功，用户信息：{info}")
        return MetaResponse(
            package_type=info["package_type"],
            package_name=info["package_name"],
            max_queries=info["max_queries"],
            allowed_models=info["allowed_models"],
            expire_time=str(info["expire_time"]),
            file_limit_mb=info["file_limit_mb"],
            db_limit_gb=info["db_limit_gb"],
            is_valid=info["is_valid"]
        )

    except HTTPException as e:
        # 主动抛出的验证失败异常，直接向上抛
        raise
    except Exception as e:
        # 其他未知异常：记录日志 + 返回 500 错误
        logger.error(f"验证激活码时发生未知错误：{str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误：{str(e)}"
        )