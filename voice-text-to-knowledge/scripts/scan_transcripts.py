"""
scan_transcripts.py
===================
扫描所有授权目录，找出符合转写稿格式的文件（.docx / .txt）。
判断依据：文件内容中包含「X号讲话人  HH:MM:SS」格式。

用法：
    python scan_transcripts.py
    → 打印候选文件列表

也可作为模块导入：
    from scan_transcripts import find_transcripts
    candidates = find_transcripts()
"""

import re
import sys
import platform
from pathlib import Path

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ── 转写稿识别规则 ────────────────────────────────────────────
# 满足以下任一条件即认定为转写稿
SPEAKER_PATTERN = re.compile(r'\d+\s*号\s*讲话人\s+\d{1,2}:\d{2}:\d{2}')
TIMESTAMP_PATTERN = re.compile(r'\d{1,2}:\d{2}:\d{2}')

# 一个文件至少要有这么多个时间戳，才算是转写稿（过滤误判）
MIN_TIMESTAMP_COUNT = 3

# ── 授权目录检测 ──────────────────────────────────────────────

def get_authorized_dirs() -> list[Path]:
    """
    返回当前环境中挂载的授权目录列表。
    在 Cowork 中，授权目录挂载在 /sessions/*/mnt/ 下。
    """
    candidates = []

    # Cowork 挂载目录
    mnt_base = Path("/sessions")
    if mnt_base.exists():
        for session_dir in mnt_base.iterdir():
            mnt = session_dir / "mnt"
            if mnt.exists():
                for d in mnt.iterdir():
                    if d.is_dir() and not d.name.startswith("."):
                        candidates.append(d)

    # 本地常见目录（非 Cowork 环境）
    home = Path.home()
    system = platform.system()

    if system == "Darwin":
        icloud = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        if icloud.exists():
            candidates.append(icloud)
    elif system == "Windows":
        username = home.name
        for p in [
            Path(f"C:/Users/{username}/iCloudDrive"),
            Path(f"C:/Users/{username}/Apple/iCloud Drive"),
        ]:
            if p.exists():
                candidates.append(p)

    # 去重
    seen = set()
    result = []
    for d in candidates:
        resolved = str(d.resolve())
        if resolved not in seen:
            seen.add(resolved)
            result.append(d)

    return result


# ── 文件内容检测 ──────────────────────────────────────────────

def read_text_sample(filepath: Path, max_chars: int = 3000) -> str:
    """读取文件的前 max_chars 个字符用于格式判断"""
    suffix = filepath.suffix.lower()

    if suffix == ".txt" or suffix == ".md":
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars)
        except Exception:
            return ""

    if suffix == ".docx":
        if not HAS_DOCX:
            return ""
        try:
            doc = DocxDocument(str(filepath))
            text = "\n".join(p.text for p in doc.paragraphs[:60])
            return text[:max_chars]
        except Exception:
            return ""

    return ""


def is_transcript(filepath: Path) -> bool:
    """判断文件是否是转写稿"""
    sample = read_text_sample(filepath)
    if not sample:
        return False

    # 优先：含有标准「X号讲话人  HH:MM:SS」格式
    if SPEAKER_PATTERN.search(sample):
        return True

    # 次选：含有足够多的时间戳
    timestamps = TIMESTAMP_PATTERN.findall(sample)
    if len(timestamps) >= MIN_TIMESTAMP_COUNT:
        return True

    return False


# ── 主扫描逻辑 ────────────────────────────────────────────────

def find_transcripts(max_depth: int = 4) -> list[dict]:
    """
    扫描授权目录，返回候选转写稿列表。
    每项包含：path, name, size_kb, modified
    """
    authorized_dirs = get_authorized_dirs()
    candidates = []

    for base_dir in authorized_dirs:
        # 递归查找 .docx 和 .txt 文件（限制深度避免过慢）
        for suffix in ("*.docx", "*.txt"):
            for filepath in base_dir.rglob(suffix):
                # 跳过隐藏文件、临时文件、系统文件
                if any(part.startswith(".") for part in filepath.parts):
                    continue
                if filepath.name.startswith("~"):
                    continue
                # 跳过已处理过的 cleaned 文件
                if "_cleaned" in filepath.name:
                    continue
                # 跳过太小的文件（<5KB，可能不是真正的转写稿）
                size_kb = filepath.stat().st_size / 1024
                if size_kb < 5:
                    continue
                # 深度限制
                depth = len(filepath.relative_to(base_dir).parts)
                if depth > max_depth:
                    continue
                # 格式判断
                if is_transcript(filepath):
                    candidates.append({
                        "path": filepath,
                        "name": filepath.name,
                        "size_kb": round(size_kb, 1),
                        "modified": filepath.stat().st_mtime,
                        "base_dir": base_dir.name,
                    })

    # 按修改时间倒序（最新的在前）
    candidates.sort(key=lambda x: x["modified"], reverse=True)
    return candidates


# ── 入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔍 正在扫描授权目录中的转写稿...\n")

    results = find_transcripts()

    if not results:
        print("⚠️  未找到符合格式的转写稿文件。")
        print("   请确认文件已放入授权目录，且格式包含「X号讲话人  HH:MM:SS」。")
        sys.exit(1)

    print(f"找到 {len(results)} 个候选文件：\n")
    for i, r in enumerate(results, 1):
        print(f"  [{i}] {r['name']}")
        print(f"       来源：{r['base_dir']}")
        print(f"       大小：{r['size_kb']} KB")
        print(f"       路径：{r['path']}\n")

    # 输出路径列表供外部捕获（每行一个路径）
    print("---PATHS---")
    for r in results:
        print(str(r["path"]))
