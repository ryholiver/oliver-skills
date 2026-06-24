"""
setup_storage.py
================
自动检测当前操作系统，找到 iCloud Drive 路径，
在其中创建「转写稿处理」文件夹（若不存在则创建），
返回最终存储路径。

用法：
    python setup_storage.py
    → 输出可用的存储路径（供其他脚本调用）

也可作为模块导入：
    from setup_storage import get_storage_path
    path = get_storage_path()
"""

import os
import sys
import platform
from pathlib import Path


# ── 文件夹名称（可修改）──────────────────────────────────────
FOLDER_NAME = "转写稿处理"


# ── 各系统 iCloud Drive 候选路径 ─────────────────────────────

def find_icloud_mac() -> Path | None:
    """Mac：iCloud Drive 标准路径"""
    candidates = [
        Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
        Path("/Library/Mobile Documents/com~apple~CloudDocs"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def find_icloud_windows() -> Path | None:
    """
    Windows：iCloud Drive 有两种常见位置
    1. 较新版本：C:\\Users\\<用户名>\\iCloudDrive
    2. 老版本：C:\\Users\\<用户名>\\Apple\\iCloud Drive
    """
    username = os.environ.get("USERNAME") or os.environ.get("USER", "")
    candidates = [
        Path(f"C:/Users/{username}/iCloudDrive"),
        Path(f"C:/Users/{username}/Apple/iCloud Drive"),
        Path(os.environ.get("USERPROFILE", "")) / "iCloudDrive",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def find_icloud_linux() -> Path | None:
    """
    Linux：通常没有原生 iCloud，
    但如果挂载了 iCloud 或使用了第三方同步，尝试常见路径
    """
    candidates = [
        Path.home() / "iCloud",
        Path.home() / "iCloudDrive",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── 主逻辑 ────────────────────────────────────────────────────

def get_storage_path() -> Path:
    """
    返回「转写稿处理」文件夹的绝对路径。
    自动检测系统，定位 iCloud，文件夹不存在则创建。
    """
    system = platform.system()

    # 1. 尝试找 iCloud Drive
    icloud_root = None
    if system == "Darwin":       # macOS
        icloud_root = find_icloud_mac()
    elif system == "Windows":
        icloud_root = find_icloud_windows()
    else:                        # Linux / 其他
        icloud_root = find_icloud_linux()

    # 2. 找到 iCloud → 在其中创建子文件夹
    if icloud_root:
        storage_path = icloud_root / FOLDER_NAME
        storage_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 存储位置（iCloud）：{storage_path}")
        return storage_path

    # 3. 没找到 iCloud → 回退到用户主目录下的文件夹
    fallback = Path.home() / FOLDER_NAME
    fallback.mkdir(parents=True, exist_ok=True)
    print(f"⚠️  未找到 iCloud Drive，使用回退路径：{fallback}")
    print(f"   （如需同步，请手动将此文件夹移入 iCloud Drive）")
    return fallback


def check_existing(storage_path: Path, doc_stem: str) -> dict:
    """
    检查某份文档是否已有处理过的文件。
    返回各文件的存在状态。
    """
    cleaned = storage_path / f"{doc_stem}_cleaned.json"
    knowledge_map = storage_path / f"{doc_stem}_知识地图.md"

    return {
        "cleaned_json": cleaned if cleaned.exists() else None,
        "knowledge_map": knowledge_map if knowledge_map.exists() else None,
        "has_cleaned": cleaned.exists(),
        "has_knowledge_map": knowledge_map.exists(),
    }


# ── 入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    path = get_storage_path()

    # 如果传入了文档名，顺便检查已有文件
    if len(sys.argv) > 1:
        doc_stem = Path(sys.argv[1]).stem
        status = check_existing(path, doc_stem)
        print(f"\n📂 检查文档「{doc_stem}」的处理状态：")
        print(f"   cleaned.json  : {'✅ 已存在' if status['has_cleaned'] else '⬜ 不存在'}")
        print(f"   知识地图.md   : {'✅ 已存在' if status['has_knowledge_map'] else '⬜ 不存在'}")

    # 最后一行输出纯路径，方便其他脚本捕获
    print(str(path))
