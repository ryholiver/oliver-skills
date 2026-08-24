#!/usr/bin/env python3
"""将 Review 视图 JSON 嵌入 OFDD 单文件 HTML 模板。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# 模板中的数据块由两个稳定标记界定，避免生成时重写 CSS 和交互逻辑。
DATA_BLOCK_PATTERN = re.compile(
    r"(?P<start>/\* REVIEW_DATA_START.*?\*/\s*const REVIEW_DATA = )"
    r"(?P<data>.*?)"
    r"(?P<end>;\s*/\* REVIEW_DATA_END \*/)",
    re.DOTALL,
)

# 旧契约（v2）字段；保留兼容旧数据。
LEGACY_REQUIRED_TOP_LEVEL = (
    "meta",
    "objective",
    "summary",
    "reasoningChains",
    "questions",
    "directions",
    "recommendation",
    "decision",
    "unresolved",
    "writeback",
)

# v3 契约字段：模块化 + 条目式，由 build_review_from_md.py 生成。
V3_REQUIRED_TOP_LEVEL = (
    "meta",
    "modules",
    "declaration",
    "facts",
    "verification",
    "inferences",
    "judgments",
    "directions",
    "questions",
    "unresolved",
    "conclusion",
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    skill_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="把 Review 视图 JSON 嵌入 OFDD HTML Review 模板。"
    )
    parser.add_argument("--data", required=True, type=Path, help="Review 视图 JSON 文件")
    parser.add_argument("--output", required=True, type=Path, help="生成的 HTML 文件")
    parser.add_argument(
        "--template",
        type=Path,
        default=skill_root / "assets" / "review-template-v3.html",
        help="HTML 模板；默认使用 skill 自带模板",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    """读取并验证 JSON 顶层类型。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"找不到数据文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 格式错误：{exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Review 数据顶层必须是 JSON 对象。")
    return data


def validate_review_data(data: dict[str, Any]) -> list[str]:
    """验证模板运行所需的最小结构，并返回非阻塞警告。"""
    is_v3 = "modules" in data
    required = V3_REQUIRED_TOP_LEVEL if is_v3 else LEGACY_REQUIRED_TOP_LEVEL
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"缺少顶层字段：{', '.join(missing)}")

    warnings: list[str] = []
    if is_v3:
        # v3 契约校验：模块配置与内容字段
        if not isinstance(data.get("modules"), list) or not data["modules"]:
            warnings.append("modules 为空，页面将缺少主体模块。")
        if not data.get("facts"):
            warnings.append("没有观察条目，页面将缺少事实主体。")
        if not data.get("directions"):
            warnings.append("没有方向条目，应确认本次 Review 是否有候选方向。")
        if not isinstance(data.get("facts"), list) or not isinstance(data.get("inferences"), list) \
                or not isinstance(data.get("judgments"), list) or not isinstance(data.get("questions"), list):
            raise ValueError("v3 内容字段（facts/inferences/judgments/questions）必须是数组。")
    else:
        for key in ("reasoningChains", "questions", "directions", "unresolved", "writeback"):
            if not isinstance(data[key], list):
                raise ValueError(f"字段 {key} 必须是数组。")
        for key in ("meta", "objective", "summary", "recommendation", "decision"):
            if not isinstance(data[key], dict):
                raise ValueError(f"字段 {key} 必须是对象。")
        if not data["reasoningChains"]:
            warnings.append("没有判断链，页面将缺少 Judgment → Evidence 追溯主体。")
        if len(data["directions"]) < 2:
            warnings.append("候选方向少于两个，应确认是否存在可比较的替代方向。")
        decision_status = str(data["decision"].get("status", ""))
        if "已拍板" in decision_status:
            if not data["decision"].get("decisionMaker") or data["decision"].get("decisionMaker") == "待补":
                warnings.append("决定标记为已拍板，但决策人仍待补。")
            if not data["decision"].get("decidedAt") or data["decision"].get("decidedAt") == "待补":
                warnings.append("决定标记为已拍板，但决定时间仍待补。")

    return warnings


def build_document(template: str, data: dict[str, Any]) -> str:
    """替换模板数据块和浏览器标题。"""
    match = DATA_BLOCK_PATTERN.search(template)
    if not match:
        raise ValueError("模板缺少 REVIEW_DATA_START / REVIEW_DATA_END 数据标记。")

    # JSON 本身是合法 JavaScript 对象字面量；关闭 ASCII 转义以保留中文可读性。
    serialized = json.dumps(data, ensure_ascii=False, indent=6)
    document = DATA_BLOCK_PATTERN.sub(
        lambda found: f"{found.group('start')}{serialized}{found.group('end')}",
        template,
        count=1,
    )

    meta = data.get("meta", {})
    title_parts = [meta.get("title"), meta.get("subtitle"), "OFDD Review"]
    browser_title = " · ".join(str(part) for part in title_parts if part)
    document = re.sub(
        r"<title>.*?</title>",
        f"<title>{escape_html(browser_title)}</title>",
        document,
        count=1,
        flags=re.DOTALL,
    )
    return document


def escape_html(value: str) -> str:
    """转义浏览器标题中的特殊字符。"""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def main() -> int:
    """执行生成流程并输出可审计摘要。"""
    args = parse_args()
    try:
        data = load_json(args.data)
        warnings = validate_review_data(data)
        template = args.template.read_text(encoding="utf-8")
        document = build_document(template, data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 1

    print(f"已生成：{args.output}")
    print(f"Review ID：{data.get('meta', {}).get('id', '未提供')}")
    for warning in warnings:
        print(f"警告：{warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
