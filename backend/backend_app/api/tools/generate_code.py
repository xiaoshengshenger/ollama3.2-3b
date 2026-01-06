import base64
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as sym_padding  # 重命名避免冲突
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import warnings

# 忽略cryptography的后端警告（新版本已默认使用最佳后端）
warnings.filterwarnings("ignore", category=DeprecationWarning, module="cryptography")
# 获取项目根目录（backend_app 的上级目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 拼接公钥文件路径
PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "tools", "user_public_key.pem")
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "tools", "developer_private_key.pem")
# -------------------------- 1. 生成RSA密钥对（仅开发者执行1次）--------------------------
def generate_rsa_keys(private_key_path: str = PRIVATE_KEY_PATH, public_key_path: str = PUBLIC_KEY_PATH):
    """
    生成RSA私钥（仅开发者保存）和公钥（嵌入用户端）
    :param private_key_path: 私钥保存路径
    :param public_key_path: 公钥保存路径
    """
    try:
        # 检查密钥是否已存在，避免覆盖
        if os.path.exists(private_key_path) or os.path.exists(public_key_path):
            confirm = input("⚠️  密钥文件已存在，是否覆盖？(y/n)：").strip().lower()
            if confirm != "y":
                print("✅ 取消生成，保留原有密钥")
                return

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # 保存私钥（生产环境建议用密码加密，这里提供可选参数）
        with open(private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()  # 生产环境改为：serialization.BestAvailableEncryption(b"你的强密码")
            ))

        # 生成公钥（嵌入用户端）
        public_key = private_key.public_key()
        with open(public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        print("✅ RSA密钥对生成完成！")
        print(f"📁 私钥路径：{os.path.abspath(private_key_path)}")
        print(f"📁 公钥路径：{os.path.abspath(public_key_path)}")
        print("⚠️  重要警告：私钥切勿上传到代码仓库、服务器或分享给他人！")
        print("💡 生产环境建议：用强密码加密私钥，定期轮换密钥对")
    except Exception as e:
        print(f"❌ 生成RSA密钥失败：{str(e)}")

# -------------------------- 2. 核心配置（开发者维护）--------------------------
# 主密钥（建议用os.urandom(32)生成真正的随机密钥，示例：base64.b64encode(os.urandom(32)).decode()）
DEV_MASTER_KEY = "1BCAF67D3F0A4D008CCCD0232E035DFC!@7IAtnQBkLZY="
# 固定盐值（必须和用户端完全一致，建议至少16位）
FIXED_SALT = "PGPT_SALT_2025"
# 模型列表配置（集中管理，方便修改）
MODEL_CONFIG = {
    "basic": ["llama3-8B"],
    "advanced": ["llama3-8B", "llama3-70B", "GPT-4"]
}
# 套餐配置（结构化，易扩展）
PACKAGE_CONFIG = {
    0: {  # 一周体验
        "days": 7,
        "maxQueries": -1,
        "allowedModels": MODEL_CONFIG["advanced"],
        "fileSizeLimit": -1,
        "dbSizeLimit": -1,
        "package": "weekly"
    },
    1: {  # 月会员
        "days": 30,
        "maxQueries": -1,
        "allowedModels": MODEL_CONFIG["advanced"],
        "fileSizeLimit": -1,
        "dbSizeLimit": -1,
        "package": "monthly"
    },
    2: {  # 季会员
        "days": 90,
        "maxQueries": -1,
        "allowedModels": MODEL_CONFIG["advanced"],
        "fileSizeLimit": -1,
        "dbSizeLimit": -1,
        "package": "quarterly"
    },
    3: {  # 年会员
        "days": 365,
        "maxQueries": -1,
        "allowedModels": MODEL_CONFIG["advanced"],
        "fileSizeLimit": -1,
        "dbSizeLimit": -1,
        "package": "annual"
    },
    4: {  # 永久会员
        "days": 0,
        "maxQueries": -1,
        "allowedModels": MODEL_CONFIG["advanced"],
        "fileSizeLimit": -1,
        "dbSizeLimit": -1,
        "package": "permanent"
    },
    5: {  # 免费用户
        "days": 0,
        "maxQueries": 100,
        "allowedModels": MODEL_CONFIG["basic"],
        "fileSizeLimit": 10,  # 10MB
        "dbSizeLimit": 1,     # 1GB
        "package": "free"
    }
}

# -------------------------- 3. 生成带签名的权限码（核心功能）--------------------------
def generate_permission_code(
    package_type: int,
    model_type: list = None,
    private_key_path: str = PRIVATE_KEY_PATH
) -> str:
    """
    生成RSA签名+AES-256-CBC加密的权限码
    :param package_type: 套餐类型（0-5对应不同会员）
    :param model_type: 自定义允许的模型列表（免费用户无效）
    :param private_key_path: 开发者私钥路径
    :return: 格式化的权限码（PGPT-前缀，分段显示）
    """
    try:
        # 1. 校验套餐类型
        if package_type not in PACKAGE_CONFIG:
            raise ValueError(f"套餐类型仅支持0-5，当前输入：{package_type}\n"
                             "对应关系：0=一周体验 | 1=月会员 | 2=季会员 | 3=年会员 | 4=永久会员 | 5=免费用户")

        # 2. 获取套餐配置（免费用户强制使用基础模型）
        perm = PACKAGE_CONFIG[package_type].copy()
        if package_type != 5 and model_type:
            # 非免费用户允许自定义模型（去重+校验有效性）
            valid_models = MODEL_CONFIG["basic"] + MODEL_CONFIG["advanced"]
            custom_models = list(set([m for m in model_type if m in valid_models]))
            perm["allowedModels"] = custom_models if custom_models else perm["allowedModels"]

        # 3. 计算过期时间（0=永久）
        expire_time = "0" if perm["days"] == 0 else (datetime.now() + timedelta(days=perm["days"])).strftime("%Y%m%d%H%M%S")

        # 4. 构建权限原文（必须和用户端校验格式完全一致！）
        models_str = ",".join(perm["allowedModels"])
        unique_id = uuid.uuid4().hex[:8]  # 8位唯一标识（防重复激活）
        perm_plaintext = (
            f"{perm['days']}|"
            f"{perm['maxQueries']}|"
            f"{models_str}|"
            f"{expire_time}|"
            f"{unique_id}|"
            f"{perm['fileSizeLimit']}|"
            f"{perm['dbSizeLimit']}"
        )

        # 5. 加载私钥并签名
        if not os.path.exists(private_key_path):
            raise FileNotFoundError(f"未找到私钥文件：{private_key_path}")

        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,  # 若私钥加密，这里传入密码字节（如b"你的密码"）
                backend=default_backend()
            )

        # RSA签名（SHA256哈希+PKCS1v15填充，防篡改）
        signature = private_key.sign(
            perm_plaintext.encode("utf-8"),
            asym_padding.PKCS1v15(),  # 填充方式（保持不变）
            hashes.SHA256()           # 正确：从hashes模块导入SHA256
        )
        signature_b64 = base64.b64encode(signature).decode("utf-8")

        # 6. AES-256-CBC加密（保护原文+签名隐私）
        # 生成AES密钥（主密钥+盐 → SHA256 → 32字节）
        key_bytes = hashlib.sha256((DEV_MASTER_KEY + FIXED_SALT).encode("utf-8")).digest()
        # 生成随机IV（16字节，CBC模式必需）
        iv = os.urandom(16)
        # 拼接原文+签名，进行PKCS7填充（AES要求明文长度是16的倍数）
        aes_plaintext = f"{perm_plaintext}###{signature_b64}".encode("utf-8")
        padder = sym_padding.PKCS7(128).padder()  # 128=16*8位
        padded_data = padder.update(aes_plaintext) + padder.finalize()

        # 7. 执行加密
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 8. 构建最终权限码（IV+密文 → Base64 → 格式化）
        iv_encrypted = iv + encrypted_data
        b64_code = base64.b64encode(iv_encrypted).decode("utf-8")
        # 强制补充填充（确保长度是4的倍数，避免遗漏）
        padding_needed = 4 - (len(b64_code) % 4)
        if padding_needed != 4:
            b64_code += "=" * padding_needed
        # 按12位分段（保留所有字符，包括 =）
        formatted_code = "PGPT-" + "-".join([b64_code[i:i+12] for i in range(0, len(b64_code), 12)])

        # 附加套餐信息（仅显示用，不影响验证）
        package_name = perm["package"]
        validity = "永久" if perm["days"] == 0 else f"{perm['days']}天"
        return f"✅ {package_name}套餐码（有效期：{validity}）：\n{formatted_code}"

    except FileNotFoundError as e:
        return f"❌ 错误：{str(e)}\n请先运行generate_rsa_keys()生成密钥对"
    except ValueError as e:
        return f"❌ 参数错误：{str(e)}"
    except Exception as e:
        return f"❌ 生成权限码失败：{str(e)}"

# -------------------------- 4. 辅助功能：验证权限码（开发者测试用）--------------------------
def verify_permission_code(permission_code: str, public_key_path: str = PUBLIC_KEY_PATH) -> tuple[bool, dict]:
    try:
        # 1. 去除前缀和分段符（严格还原原始 Base64 字符串）
        if not permission_code.startswith("PGPT-"):
            return False, {"error": "权限码格式错误，必须以PGPT-开头"}
        raw_code = permission_code.replace("PGPT-", "").replace("-", "").strip()

        # 2. 清理非法字符（避免用户输入时混入空格、换行等）
        raw_code = raw_code.replace(" ", "").replace("\n", "").replace("\r", "")

        # 3. 强制补充 Base64 填充（确保长度是4的倍数）
        padding_needed = 4 - (len(raw_code) % 4)
        if padding_needed != 4:
            raw_code += "=" * padding_needed

        # 4. 严格 Base64 解码（validate=True 强制校验格式）
        try:
            iv_encrypted = base64.b64decode(raw_code, validate=True)
        except base64.binascii.Error as e:
            return False, {"error": f"Base64 解码失败：{str(e)}（权限码可能被篡改）"}

        # 5. 分离 IV 和密文（IV 固定16字节，CBC模式必需）
        if len(iv_encrypted) < 16:
            return False, {"error": "权限码数据不完整（IV 缺失）"}
        iv = iv_encrypted[:16]
        encrypted_data = iv_encrypted[16:]

        # 6. AES 解密（后续逻辑不变，但补充异常捕获）
        key_bytes = hashlib.sha256((DEV_MASTER_KEY + FIXED_SALT).encode("utf-8")).digest()
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        try:
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        except Exception as e:
            return False, {"error": f"AES 解密失败：{str(e)}（权限码可能被篡改或密钥不匹配）"}

        # 7. 去除 PKCS7 填充（补充异常捕获，避免填充错误）
        try:
            unpadder = sym_padding.PKCS7(128).unpadder()
            aes_plaintext = unpadder.update(padded_data) + unpadder.finalize()
        except Exception as e:
            return False, {"error": f"PKCS7 解填充失败：{str(e)}（权限码数据损坏）"}

        # 8. 解析原文和签名（补充格式校验）
        try:
            perm_plaintext, signature_b64 = aes_plaintext.decode("utf-8").split("###", 1)
        except ValueError:
            return False, {"error": "权限码数据格式错误（原文和签名分离失败）"}

        # 9. RSA 签名验证（后续逻辑不变）
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

        try:
            signature = base64.b64decode(signature_b64, validate=True)
        except base64.binascii.Error:
            return False, {"error": "签名数据 Base64 解码失败"}

        try:
            public_key.verify(
                signature,
                perm_plaintext.encode("utf-8"),
                asym_padding.PKCS1v15(),
                hashes.SHA256()
            )
        except InvalidSignature:
            return False, {"error": "签名验证失败，权限码可能被篡改"}

        # 10. 解析权限信息（补充格式校验）
        try:
            days, max_queries, models_str, expire_time, unique_id, file_limit, db_limit = perm_plaintext.split("|")
        except ValueError:
            return False, {"error": "权限信息解析失败（格式不匹配）"}

        permission_info = {
            "package_type": next(k for k, v in PACKAGE_CONFIG.items() if v["days"] == int(days) and v["maxQueries"] == int(max_queries)),
            "days": int(days),
            "max_queries": int(max_queries),
            "allowed_models": models_str.split(","),
            "expire_time": "永久" if expire_time == "0" else datetime.strptime(expire_time, "%Y%m%d%H%M%S"),
            "unique_id": unique_id,
            "file_size_limit_mb": int(file_limit),
            "db_size_limit_gb": int(db_limit),
            "is_valid": True
        }

        # 11. 校验过期时间（非永久套餐）
        if expire_time != "0":
            expire_dt = datetime.strptime(expire_time, "%Y%m%d%H%M%S")
            if datetime.now() > expire_dt:
                permission_info["is_valid"] = False
                permission_info["error"] = f"权限码已过期（过期时间：{expire_dt.strftime('%Y-%m-%d %H:%M:%S')}）"

        return True, permission_info

    except StopIteration:
        return False, {"error": "套餐类型解析失败（权限信息不合法）"}
    except ValueError as e:
        return False, {"error": f"权限信息格式错误：{str(e)}"}
    except Exception as e:
        return False, {"error": f"验证失败：{str(e)}"}
# -------------------------- 5. 测试用例（开发者验证）--------------------------
if __name__ == "__main__":
    # 第一步：生成RSA密钥对（仅需执行1次，执行后注释）
    generate_rsa_keys()

    # 第二步：生成不同套餐的权限码
    print("=== 测试生成权限码 ===")
    # 1. 一周体验套餐（默认高级模型）
    print(generate_permission_code(package_type=0))
    # 2. 永久会员套餐（自定义模型）
    print(generate_permission_code(package_type=4, model_type=["GPT-4", "llama3-70B"]))
    # 3. 免费用户套餐（强制基础模型）
    print(generate_permission_code(package_type=5))

    # 第三步：测试验证权限码（复制上面生成的任意一个码）
    print("\n=== 测试验证权限码 ===")
    test_code = input("请输入要验证的权限码：").strip()
    is_valid, info = verify_permission_code(test_code)
    if is_valid:
        print("✅ 权限码有效！权限信息：")
        for k, v in info.items():
            print(f"  {k}: {v}")
    else:
        print(f"❌ 权限码无效：{info['error']}")