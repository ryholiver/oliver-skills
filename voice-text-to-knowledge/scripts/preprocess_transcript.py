"""
transcript_preprocess.py
========================
对带时间戳的多人语音转写稿（docx/txt）进行结构化预处理。

输出：cleaned JSON 文件，供后续 LLM 知识提取使用。

用法：
    python preprocess_transcript.py --input <文件路径> --output <输出路径>
"""

import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── 依赖检查 ──────────────────────────────────────────────────
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# ── 已知 ASR 替换词典（可持续追加）──────────────────────────────
ASR_GLOSSARY = {
    # LangGraph 相关
    r"long\s*rag\s*h": "LangGraph",
    r"朗格拉夫": "LangGraph",
    r"长格拉夫": "LangGraph",
    r"lon\s*graph": "LangGraph",
    r"long\s*graph": "LangGraph",
    # LangChain 相关
    r"lan\s*chang": "LangChain",
    r"lang\s*chain": "LangChain",
    r"兰changge": "LangChain",
    # 其他常见工具（根据使用中积累，在此追加）
}

# ── 噪音清洗规则 ──────────────────────────────────────────────

# 填充词：独立出现时删除
FILLER_WORDS = ["嗯", "啊", "哦", "唉", "呢", "呀", "哈", "额"]

# 卡顿重复：连续重复3次以上，压缩为1次
STUTTER_PATTERN = re.compile(r'(.{1,4})\1{2,}')

# 纯应答片段：整段只有这些词组合，标记为 skip
ACK_ONLY_PATTERN = re.compile(
    r'^[\s,，。！？]*'
    r'(对|好|嗯|行|是|啊|哦|可以|没问题|好的|好好好|行行行|对对对|嗯嗯|嗯嗯嗯)'
    r'[\s,，。！？]*$'
)

# 社交闲聊关键词（用于辅助判断，不单独决定 skip）
SOCIAL_KEYWORDS = [
    "哈哈哈", "加钱", "假装没在", "串场", "沙漠开车", "麦登",
    "大姐", "粉丝", "吓走", "缘分"
]

# 转写稿行格式：「X号讲话人  HH:MM:SS」
SPEAKER_LINE_PATTERN = re.compile(
    r'^(\d+)\s*号\s*讲话人\s+(\d{1,2}:\d{2}:\d{2})\s*$'
)


# ── 工具函数 ──────────────────────────────────────────────────

def timestamp_to_seconds(ts: str) -> int:
    """HH:MM:SS → 秒数"""
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    elif len(parts) == 2:
        h, m, s = 0, int(parts[0]), int(parts[1])
    else:
        return 0
    return h * 3600 + m * 60 + s


def apply_asr_glossary(text: str) -> str:
    """应用 ASR 词典，纠正已知语音识别错误"""
    for pattern, replacement in ASR_GLOSSARY.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def clean_noise(text: str) -> str:
    """清洗口语噪音：填充词、卡顿重复"""
    # 去卡顿重复（连续重复3次以上 → 1次）
    text = STUTTER_PATTERN.sub(r'\1', text)
    # 去行内独立填充词（前后是标点或空格）
    for fw in FILLER_WORDS:
        text = re.sub(rf'(?<=[，。！？\s]){fw}(?=[，。！？\s]|$)', '', text)
    # 多余空格清理
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def judge_skip(text: str) -> tuple[bool, str]:
    """
    判断片段是否应该跳过（status: skip）
    返回 (should_skip: bool, reason: str)
    """
    stripped = text.strip()

    # 规则1：纯应答片段
    if ACK_ONLY_PATTERN.match(stripped):
        return True, "纯应答片段"

    # 规则2：极短且无实质内容（少于6字）
    if len(stripped) < 6:
        return True, "过短片段"

    # 规则3：社交闲聊辅助判断（含关键词且不超过20字）
    if len(stripped) <= 20 and any(kw in stripped for kw in SOCIAL_KEYWORDS):
        return True, "社交闲聊"

    return False, ""


# ── 文档读取 ──────────────────────────────────────────────────

def read_docx(filepath: str) -> list[str]:
    """读取 docx 文件，返回段落文本列表"""
    if DocxDocument is None:
        raise ImportError("请先安装 python-docx：pip install python-docx")
    doc = DocxDocument(filepath)
    return [p.text for p in doc.paragraphs]


def read_txt(filepath: str) -> list[str]:
    """读取 txt 文件，返回行列表"""
    with open(filepath, encoding="utf-8") as f:
        return f.readlines()


def parse_lines(lines: list[str]) -> list[dict]:
    """
    将原始行列表解析为结构化片段列表。
    格式：X号讲话人  HH:MM:SS\n内容
    """
    segments = []
    current_speaker = None
    current_timestamp = None
    current_lines = []

    def flush():
        if current_speaker and current_lines:
            text = " ".join(l.strip() for l in current_lines if l.strip())
            if text:
                segments.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "seconds": timestamp_to_seconds(current_timestamp),
                    "text_raw": text,
                })

    for line in lines:
        line_stripped = line.strip()
        m = SPEAKER_LINE_PATTERN.match(line_stripped)
        if m:
            flush()
            current_speaker = m.group(1)
            current_timestamp = m.group(2)
            current_lines = []
        elif current_speaker is not None and line_stripped:
            current_lines.append(line_stripped)

    flush()
    return segments


# ── 主处理流程 ────────────────────────────────────────────────

def process(input_path: str, output_path: str):
    path = Path(input_path)
    suffix = path.suffix.lower()

    # 读取原始行
    if suffix == ".docx":
        lines = read_docx(input_path)
    elif suffix in (".txt", ".md"):
        lines = read_txt(input_path)
    else:
        raise ValueError(f"不支持的文件格式：{suffix}，请使用 .docx 或 .txt")

    # 解析结构
    raw_segments = parse_lines(lines)

    # 处理每个片段
    processed = []
    for i, seg in enumerate(raw_segments):
        text = seg["text_raw"]

        # ASR 纠错
        text = apply_asr_glossary(text)

        # 噪音清洗
        text = clean_noise(text)

        # 判断是否跳过
        should_skip, reason = judge_skip(text)

        processed.append({
            "id": i + 1,
            "speaker": seg["speaker"],
            "timestamp": seg["timestamp"],
            "seconds": seg["seconds"],
            "text": text,
            "text_raw": seg["text_raw"],
            "status": "skip" if should_skip else "keep",
            "skip_reason": reason if should_skip else "",
        })

    # 构建 topic_index（占位，供 LLM 后续填充）
    output = {
        "source": path.name,
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_segments": len(processed),
        "kept_segments": sum(1 for s in processed if s["status"] == "keep"),
        "skipped_segments": sum(1 for s in processed if s["status"] == "skip"),
        "asr_glossary_applied": list(ASR_GLOSSARY.values()),
        "segments": processed,
        "topic_index": {},  # 由 LLM 在知识提取阶段填充
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"✅ 预处理完成")
    print(f"   来源文件：{path.name}")
    print(f"   总片段数：{output['total_segments']}")
    print(f"   保留片段：{output['kept_segments']}")
    print(f"   跳过片段：{output['skipped_segments']}")
    print(f"   输出文件：{output_path}")


# ── 入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="转写稿预处理工具")
    parser.add_argument("--input", required=True, help="输入文件路径（.docx 或 .txt）")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    args = parser.parse_args()
    process(args.input, args.output)
