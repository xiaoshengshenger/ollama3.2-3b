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
    days: int               # 整数（0=永久，7=一周等）
    maxQueries: int         # 整数（-1=无限制，100=免费用户限制）
    allowedModels: list[str]# 字符串列表（允许的模型）
    fileSizeLimit: int      # 整数（MB）
    dbSizeLimit: int        # 整数（GB）
    package: str            # 字符串（套餐名称：free/weekly/monthly 等）
    is_valid: bool = True   # 新增：标识激活码是否有效
    error: str = ""         # 新增：错误信息（可选）

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
        logger.info(f"开始验证激活码：{code[:20]}...")  # 只打印前20位，避免日志过长

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
        package_name = PACKAGE_NAME_MAP.get(info["package_type"], "unknown")
        
        return MetaResponse(
            days=info["days"],                    # int → 匹配模型的 int
            maxQueries=info["max_queries"],       # int → 匹配模型的 int
            allowedModels=info["allowed_models"], # list[str] → 匹配模型
            fileSizeLimit=info["file_size_limit_mb"], # int → 匹配模型的 int
            dbSizeLimit=info["db_size_limit_gb"], # int → 匹配模型的 int
            package=package_name,                 # str → 匹配模型的 str（关键修复）
            is_valid=info.get("is_valid", True),
            error=info.get("error", "")
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