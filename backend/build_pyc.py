import os
import shutil
import sys
import marshal
from pathlib import Path
# 自动获取当前Python的magic number（推荐，避免手动配置错误）
try:
    import importlib._bootstrap_external as bootstrap
    MAGIC_NUMBER = bootstrap.MAGIC_NUMBER
except ImportError:
    # 手动指定Python 3.13的magic number（备用）
    MAGIC_NUMBER = b'\x40\x3e\x00\x00'

# ===================== 配置项（仅需调整这两个）=====================
SOURCE_DIR = Path("./app")  # 你的源码根目录：E:\ai\llama3.2-projec\src
OUTPUT_DIR = Path("./dist")  # .pyc产物输出目录
# ==================================================================

def clean_old_build():
    """清空旧的dist目录，避免残留文件"""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)  # 忽略Windows文件占用错误
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ 已清空并创建输出目录：{OUTPUT_DIR.absolute()}")

def compile_single_py(src_file: Path, dst_pyc: Path):
    """
    编译单个.py文件为.pyc文件，直接写入目标路径
    :param src_file: 源.py文件的路径
    :param dst_pyc: 目标.pyc文件的路径
    """
    # 1. 读取源码文件（二进制模式，避免编码问题）
    try:
        with open(src_file, "rb") as f:
            source_content = f.read()
    except Exception as e:
        raise RuntimeError(f"读取源码失败：{src_file} → {str(e)}") from e

    # 2. 编译源码为Python字节码对象
    try:
        code_obj = compile(
            source_content,
            filename=str(src_file),  # 报错时显示的文件名
            mode="exec",            # 编译整个模块（exec模式）
            dont_inherit=True,      # 不继承当前环境的编译标志
            optimize=0              # 优化级别（0/1/2，0为默认）
        )
    except SyntaxError as e:
        raise RuntimeError(f"源码语法错误：{src_file} → 行{e.lineno}：{e.msg}") from e
    except Exception as e:
        raise RuntimeError(f"编译源码失败：{src_file} → {str(e)}") from e

    # 3. 写入.pyc文件（遵循Python的.pyc文件格式）
    try:
        with open(dst_pyc, "wb") as f:
            f.write(MAGIC_NUMBER)          # 写入版本标识（magic number）
            f.write(b'\x00\x00\x00\x00')   # 写入时间戳（0表示不验证时间）
            marshal.dump(code_obj, f)      # 写入字节码对象（序列化）
    except Exception as e:
        raise RuntimeError(f"写入.pyc失败：{dst_pyc} → {str(e)}") from e

def compile_all_py_to_dist():
    """遍历所有.py文件，编译为.pyc并写入dist目录（保留原目录结构）"""
    print("📝 开始编译所有.py文件为.pyc...")
    compiled_count = 0
    skipped_count = 0

    # 递归遍历源码目录下的所有.py文件
    for src_file in SOURCE_DIR.rglob("*.py"):
        # 跳过无关文件：脚本自身、__pycache__目录下的文件、隐藏文件
        if (src_file.name == "build_pyc.py" or 
            "__pycache__" in src_file.parts or 
            src_file.name.startswith(".")):
            skipped_count += 1
            continue

        # 计算目标.pyc文件的路径（保留原目录结构，替换后缀为.pyc）
        rel_path = src_file.relative_to(SOURCE_DIR)
        dst_pyc = OUTPUT_DIR / rel_path.with_suffix(".pyc")

        # 创建目标目录（如果不存在）
        dst_pyc.parent.mkdir(parents=True, exist_ok=True)

        # 编译并写入
        try:
            compile_single_py(src_file, dst_pyc)
            compiled_count += 1
            # 可选：打印编译日志（如需精简，注释掉下面这行）
            # print(f"   ✅ {rel_path} → {dst_pyc.relative_to(OUTPUT_DIR)}")
        except Exception as e:
            print(f"⚠️ 跳过文件：{src_file} → {str(e)}")
            skipped_count += 1

    print(f"✅ 编译完成：成功{compiled_count}个，跳过{skipped_count}个")

def verify_compile_result():
    """验证编译结果，显示dist目录下的.pyc文件数量"""
    pyc_files = list(OUTPUT_DIR.rglob("*.pyc"))
    print(f"\n📌 编译结果验证：")
    print(f"   - 输出目录：{OUTPUT_DIR.absolute()}")
    print(f"   - 生成.pyc文件总数：{len(pyc_files)}")
    # 显示前5个.pyc文件的路径（便于确认结构）
    for i, file in enumerate(pyc_files[:5]):
        print(f"     - {file.relative_to(OUTPUT_DIR)}")
    if len(pyc_files) > 5:
        print(f"     - ... 还有{len(pyc_files)-5}个文件")

if __name__ == "__main__":
    # 打印环境信息
    print(f"===== 开始编译Python源码为.pyc =====\n🔍 Python版本：{sys.version.split()[0]}\n🔍 Magic Number：{MAGIC_NUMBER.hex()}（{MAGIC_NUMBER}）\n🔍 源码目录：{SOURCE_DIR.absolute()}")
    # 执行核心流程
    clean_old_build()
    compile_all_py_to_dist()
    verify_compile_result()
    print(f"\n===== 全部操作完成！=====")