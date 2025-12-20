import os
import shutil
from pathlib import Path

# ===================== 配置项（根据需求调整）=====================
# 要清理的根目录（当前项目根目录，可改为绝对路径如：Path("E:/ai/llama3.2-projec/src")）
ROOT_DIR = Path("./src/app")
# 排除的目录（这些目录下的.pyc和__pycache__不删除，如dist目录保留编译后的产物）
EXCLUDE_DIRS = [
    Path("./dist"),  # 保留编译后的.pyc产物目录
    Path("./venv"),  # 可选：保留虚拟环境（若有）
    Path("./.git"),  # 可选：保留git目录
]
# ==================================================================

def is_excluded(path: Path) -> bool:
    """判断路径是否在排除目录中"""
    for exclude_dir in EXCLUDE_DIRS:
        # 转为绝对路径，避免相对路径判断错误
        abs_exclude = exclude_dir.absolute()
        abs_path = path.absolute()
        if abs_path.is_relative_to(abs_exclude):
            return True
    return False

def clean_pyc_and_cache():
    """递归删除.pyc文件和__pycache__目录"""
    pyc_count = 0  # 统计删除的.pyc文件数
    cache_count = 0  # 统计删除的__pycache__目录数

    # 递归遍历所有目录和文件
    for root in ROOT_DIR.rglob("*"):
        # 跳过排除目录
        if is_excluded(root):
            continue

        # 处理__pycache__目录（删除整个目录）
        if root.is_dir() and root.name == "__pycache__":
            try:
                shutil.rmtree(root, ignore_errors=True)  # 忽略文件占用错误
                cache_count += 1
                print(f"🗑️ 删除__pycache__目录：{root.absolute()}")
            except Exception as e:
                print(f"⚠️ 无法删除__pycache__目录：{root.absolute()} → 错误：{str(e)}")

        # 处理.pyc文件（逐个删除）
        elif root.is_file() and root.suffix == ".pyc":
            try:
                root.unlink()  # 删除文件
                pyc_count += 1
                # 可选：打印删除的.pyc文件路径（如需精简，注释掉下面这行）
                # print(f"🗑️ 删除.pyc文件：{root.absolute()}")
            except Exception as e:
                print(f"⚠️ 无法删除.pyc文件：{root.absolute()} → 错误：{str(e)}")

    # 输出清理结果
    print(f"\n===== 清理完成！=====")
    print(f"✅ 共删除 {pyc_count} 个.pyc文件")
    print(f"✅ 共删除 {cache_count} 个__pycache__目录")

if __name__ == "__main__":
    print(f"===== 开始清理项目中的.pyc文件和__pycache__目录 =====\n🔍 根目录：{ROOT_DIR.absolute()}\n🔍 排除目录：{[d.absolute() for d in EXCLUDE_DIRS]}")
    clean_pyc_and_cache()