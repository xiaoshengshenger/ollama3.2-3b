# project_verify_tool.py（项目运行）
import base64
import hashlib
import os
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="cryptography")

# ==================== 核心配置（与本地完全一致） ====================
MODEL_CODE = {0: "llama3-8B", 1: "llama3-70B", 2: "GPT-4"}
PACKAGE_CONFIG = {
    0: {"days":7, "maxQ":-1, "models":[0,1,2], "fileL":-1, "dbL":-1, "name":"weekly"},
    1: {"days":30, "maxQ":-1, "models":[0,1,2], "fileL":-1, "dbL":-1, "name":"monthly"},
    2: {"days":90, "maxQ":-1, "models":[0,1,2], "fileL":-1, "dbL":-1, "name":"quarterly"},
    3: {"days":365, "maxQ":-1, "models":[0,1,2], "fileL":-1, "dbL":-1, "name":"annual"},
    4: {"days":0, "maxQ":-1, "models":[0,1,2], "fileL":-1, "dbL":-1, "name":"permanent"},
    5: {"days":0, "maxQ":100, "models":[0], "fileL":10, "dbL":1, "name":"free"}
}
DEV_MASTER_KEY = "1BCAF67D3F0A4D008CCCD0232E035DFC!@7IAtnQBkLZY="
FIXED_SALT = "PGPT_SALT_2025"

PROJECT_PUBLIC_KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    "user_public.pem"
)
os.makedirs(os.path.dirname(PROJECT_PUBLIC_KEY_PATH), exist_ok=True)

# ==================== 验证激活码 ====================
def verify_permission_code(permission_code: str) -> tuple[bool, dict]:
    # 1. 格式校验
    if not permission_code.startswith("PGPT"):
        return False, {"error": "激活码必须以PGPT开头"}

    try:
        # 2. 解码：还原原文+签名
        b64_code = permission_code[4:].replace("-", "+").replace("_", "/")
        # 补全Base64填充
        padding_needed = (4 - len(b64_code) % 4) % 4
        b64_code += "=" * padding_needed
        raw_data = base64.b64decode(b64_code)

        # 3. 分离原文（16字节）和签名（剩余字节）
        perm_plaintext = raw_data[:16].decode("utf-8")
        signature = raw_data[16:]
        print(f"📝 验证侧签名原文：{perm_plaintext}")
        print(f"📝 验证侧签名长度：{len(signature)}字节")

        # 4. 校验和验证
        plain_data = perm_plaintext[:15]
        checksum = perm_plaintext[15]
        calc_checksum = str(sum(ord(c) for c in plain_data) %10)
        if calc_checksum != checksum:
            return False, {"error": "校验和不匹配（数据损坏）"}

        # 5. 加载公钥验签（核心步骤）
        if not os.path.exists(PROJECT_PUBLIC_KEY_PATH):
            return False, {"error": f"公钥缺失：{PROJECT_PUBLIC_KEY_PATH}"}
        
        with open(PROJECT_PUBLIC_KEY_PATH, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        
        try:
            public_key.verify(
                signature,
                perm_plaintext.encode("utf-8"),
                asym_padding.PKCS1v15(),
                hashes.SHA256()
            )
        except Exception as e:
            return False, {"error": f"签名验证失败：{str(e)}"}

        # 6. 解析业务数据
        pkg_type = int(plain_data[0])
        maxQ_str = plain_data[1:3]
        model_str = plain_data[3:5]
        expire_str = plain_data[5:11]
        fileL_str = plain_data[11:13]
        dbL_str = plain_data[13:15]

        # 还原数据
        maxQ = -1 if maxQ_str == "01" else int(maxQ_str)
        models = [MODEL_CODE[int(c)] for c in model_str if c in ["0","1","2"]] or [MODEL_CODE[0]]
        if expire_str == "000000":
            expire_time = "永久"
            is_expired = False
        else:
            expire_dt = datetime.strptime(f"20{expire_str}", "%Y%m%d")
            expire_time = expire_dt
            is_expired = datetime.now() > expire_dt
        fileL = -1 if fileL_str == "01" else int(fileL_str)
        dbL = -1 if dbL_str == "01" else int(dbL_str)

        # 7. 组装结果
        return True, {
            "package_type": pkg_type,
            "package_name": PACKAGE_CONFIG[pkg_type]["name"],
            "max_queries": maxQ,
            "allowed_models": models,
            "expire_time": expire_time,
            "file_limit_mb": fileL,
            "db_limit_gb": dbL,
            "is_valid": not is_expired
        }
    except Exception as e:
        return False, {"error": f"验证失败：{str(e)}"}

# ==================== 测试入口 ====================
if __name__ == "__main__":
    print("=== 激活码验证工具 ===")
    user_code = input("请输入激活码：").strip()
    is_valid, info = verify_permission_code(user_code)
    if is_valid:
        print("✅ 验证成功！")
        for k,v in info.items():
            print(f"  {k}: {v}")
    else:
        print(f"❌ {info['error']}")