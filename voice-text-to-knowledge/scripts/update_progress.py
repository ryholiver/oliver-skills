"""
update_progress.py
==================
零 token 更新知识地图 HTML 文件中的话题进度状态。

用法：
    python update_progress.py --html <html文件路径> --card <卡片标题关键词> --status <状态>

状态选项：
    todo        → ⬜ 未开始
    doing       → 🔄 进行中
    done        → ✅ 已吸收

示例：
    python update_progress.py --html 知识地图.html --card "LangGraph" --status done
    python update_progress.py --html 知识地图.html --card "Agent编排" --status doing --note "卡在工具调用循环那里"
    python update_progress.py --html 知识地图.html --list    # 列出所有卡片和当前状态

也可作为模块导入：
    from update_progress import update_card_status, list_cards
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import date

# ── 状态映射 ──────────────────────────────────────────────────
STATUS_MAP = {
    "todo":  {"emoji": "⬜", "label": "未开始",  "css_class": "status-todo"},
    "doing": {"emoji": "🔄", "label": "进行中",  "css_class": "status-doing"},
    "done":  {"emoji": "✅", "label": "已吸收",  "css_class": "status-done"},
}

# HTML 中状态标记的模式（匹配 data-card-id 和 data-status 属性）
CARD_PATTERN = re.compile(
    r'(<div[^>]+data-card-id="([^"]+)"[^>]*data-status=")([^"]+)(")',
    re.DOTALL
)

STATUS_BADGE_PATTERN = re.compile(
    r'(<span[^>]+class="[^"]*status-badge[^"]*"[^>]*data-card-id="([^"]+)"[^>]*>)'
    r'([^<]*)'
    r'(</span>)',
    re.DOTALL
)

CARD_TITLE_PATTERN = re.compile(
    r'data-card-id="([^"]+)"[^>]*>[^<]*<[^>]+class="[^"]*card-title[^"]*"[^>]*>([^<]+)',
    re.DOTALL
)


# ── 核心函数 ──────────────────────────────────────────────────

def load_html(html_path: Path) -> str:
    """读取 HTML 文件内容"""
    with open(html_path, encoding="utf-8") as f:
        return f.read()


def save_html(html_path: Path, content: str) -> None:
    """写回 HTML 文件"""
    with open(html_path, encoding="utf-8", mode="w") as f:
        f.write(content)


def list_cards(html_path: Path) -> list[dict]:
    """
    列出 HTML 中所有知识卡片及其当前状态。
    返回：[{"id": ..., "title": ..., "status": ...}, ...]
    """
    content = load_html(html_path)

    # 提取所有卡片的 id + status
    cards = {}
    for m in CARD_PATTERN.finditer(content):
        card_id = m.group(2)
        status_key = m.group(3)
        cards[card_id] = {"id": card_id, "status": status_key, "title": card_id}

    # 尝试提取标题（更友好的展示）
    # 匹配 <div ... data-card-id="xxx" ...> ... <h3 class="card-title">标题</h3>
    title_pattern = re.compile(
        r'data-card-id="([^"]+)".*?class="[^"]*card-title[^"]*"[^>]*>\s*([^\n<]{1,80})',
        re.DOTALL
    )
    for m in title_pattern.finditer(content):
        card_id = m.group(1)
        title = m.group(2).strip()
        if card_id in cards:
            cards[card_id]["title"] = title

    return list(cards.values())


def find_card_id(html_path: Path, keyword: str) -> str | None:
    """
    根据关键词（卡片标题或 ID 的部分匹配）找到对应的 card_id。
    如果有多个匹配，返回第一个；如果没有，返回 None。
    """
    cards = list_cards(html_path)
    keyword_lower = keyword.lower()

    # 精确匹配优先
    for card in cards:
        if card["id"].lower() == keyword_lower:
            return card["id"]
        if card["title"].lower() == keyword_lower:
            return card["id"]

    # 模糊匹配
    for card in cards:
        if keyword_lower in card["id"].lower():
            return card["id"]
        if keyword_lower in card["title"].lower():
            return card["id"]

    return None


def update_card_status(
    html_path: Path,
    card_id: str,
    new_status: str,
    note: str = "",
    today: str = ""
) -> bool:
    """
    更新指定卡片的状态。

    - 修改 data-status 属性（驱动 CSS 颜色变化）
    - 修改状态徽章文字
    - 如果是 done，附加今天日期；如果是 doing，附加 note
    - 更新顶部进度统计（todo/doing/done 计数）

    返回 True 表示成功，False 表示未找到该卡片。
    """
    if new_status not in STATUS_MAP:
        raise ValueError(f"无效状态：{new_status}，可选：{list(STATUS_MAP.keys())}")

    content = load_html(html_path)
    status_info = STATUS_MAP[new_status]

    if not today:
        today = date.today().strftime("%Y-%m-%d")

    # 生成新的状态标签文字
    if new_status == "done":
        badge_text = f"{status_info['emoji']} {status_info['label']} · {today}"
    elif new_status == "doing" and note:
        badge_text = f"{status_info['emoji']} {status_info['label']} · {note}"
    else:
        badge_text = f"{status_info['emoji']} {status_info['label']}"

    # ── 步骤1：更新 data-status 属性 ──────────────────────────
    # 匹配 <div ... data-card-id="CARD_ID" ... data-status="OLD_STATUS" ...>
    card_div_pattern = re.compile(
        r'(<div\b[^>]*\bdata-card-id="' + re.escape(card_id) + r'"[^>]*\bdata-status=")[^"]+(")',
        re.DOTALL
    )
    new_content, count1 = card_div_pattern.subn(
        r'\g<1>' + new_status + r'\g<2>',
        content
    )
    if count1 == 0:
        return False  # 未找到该卡片

    # ── 步骤2：更新状态徽章文字 ────────────────────────────────
    # 匹配 <span ... data-card-id="CARD_ID" ...>旧文字</span>
    badge_pattern = re.compile(
        r'(<span\b[^>]*\bdata-card-id="' + re.escape(card_id) + r'"[^>]*>)'
        r'([^<]*)'
        r'(</span>)',
        re.DOTALL
    )
    new_content, count2 = badge_pattern.subn(
        r'\g<1>' + badge_text + r'\g<3>',
        new_content
    )

    # ── 步骤3：更新顶部进度统计 ────────────────────────────────
    new_content = _recalculate_progress(new_content)

    save_html(html_path, new_content)
    return True


def _recalculate_progress(content: str) -> str:
    """
    重新计算所有卡片的状态分布，更新顶部进度栏中的统计数字。
    匹配：data-counter="todo/doing/done" 的元素
    """
    # 统计各状态数量
    all_statuses = re.findall(r'data-status="(todo|doing|done)"', content)
    counts = {"todo": 0, "doing": 0, "done": 0}
    for s in all_statuses:
        counts[s] += 1
    total = sum(counts.values())

    # 更新 data-counter 元素的文本
    for key, val in counts.items():
        counter_pattern = re.compile(
            r'(<[^>]+\bdata-counter="' + key + r'"[^>]*>)'
            r'(\d+)'
            r'(</[^>]+>)',
            re.DOTALL
        )
        content, _ = counter_pattern.subn(
            r'\g<1>' + str(val) + r'\g<3>',
            content
        )

    # 更新进度条宽度（done 占比）
    if total > 0:
        pct = round(counts["done"] / total * 100)
        progress_bar_pattern = re.compile(
            r'(id="progress-bar"[^>]*style="[^"]*width:\s*)\d+(%[^"]*")',
            re.DOTALL
        )
        content, _ = progress_bar_pattern.subn(
            r'\g<1>' + str(pct) + r'\g<2>',
            content
        )

        # 也更新进度百分比文字（如果有）
        pct_text_pattern = re.compile(
            r'(id="progress-pct"[^>]*>)\d+(%</)',
            re.DOTALL
        )
        content, _ = pct_text_pattern.subn(
            r'\g<1>' + str(pct) + r'\g<2>',
            content
        )

    return content


# ── CLI 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="零 token 更新知识地图 HTML 的话题进度状态"
    )
    parser.add_argument("--html", required=True, help="知识地图 HTML 文件路径")
    parser.add_argument("--card", help="卡片标题或 ID 关键词（模糊匹配）")
    parser.add_argument(
        "--status",
        choices=["todo", "doing", "done"],
        help="新状态：todo（未开始）/ doing（进行中）/ done（已吸收）"
    )
    parser.add_argument("--note", default="", help="进行中时的备注（可选）")
    parser.add_argument("--list", action="store_true", help="列出所有卡片和当前状态")
    parser.add_argument("--card-id", help="直接指定精确的 card_id（跳过模糊匹配）")

    args = parser.parse_args()
    html_path = Path(args.html)

    if not html_path.exists():
        print(f"❌ 文件不存在：{html_path}")
        sys.exit(1)

    # ── 列出所有卡片 ───────────────────────────────────────────
    if args.list:
        cards = list_cards(html_path)
        if not cards:
            print("⚠️  未找到任何知识卡片（请确认 HTML 包含 data-card-id 属性）")
            sys.exit(1)
        print(f"\n📋 共 {len(cards)} 个知识卡片：\n")
        for c in cards:
            status_info = STATUS_MAP.get(c["status"], {"emoji": "❓", "label": c["status"]})
            print(f"  {status_info['emoji']}  {c['title']}")
            print(f"      ID: {c['id']}\n")
        return

    # ── 更新单个卡片状态 ───────────────────────────────────────
    if not args.status:
        parser.print_help()
        sys.exit(1)

    # 确定 card_id
    if args.card_id:
        card_id = args.card_id
    elif args.card:
        card_id = find_card_id(html_path, args.card)
        if not card_id:
            print(f"❌ 未找到匹配「{args.card}」的卡片")
            print("   提示：运行 --list 查看所有卡片 ID")
            sys.exit(1)
    else:
        print("❌ 请指定 --card <关键词> 或 --card-id <精确ID>")
        sys.exit(1)

    # 执行更新
    success = update_card_status(
        html_path=html_path,
        card_id=card_id,
        new_status=args.status,
        note=args.note,
    )

    if success:
        status_info = STATUS_MAP[args.status]
        print(f"✅ 已更新：{card_id}  →  {status_info['emoji']} {status_info['label']}")
        print(f"   文件：{html_path}")
        print(f"   刷新页面即可看到最新状态（无需重新生成，零 token）")
    else:
        print(f"❌ 更新失败：未在 HTML 中找到 card_id='{card_id}'")
        print("   提示：运行 --list 查看所有卡片 ID")
        sys.exit(1)


if __name__ == "__main__":
    main()
