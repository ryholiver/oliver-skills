"""
generate_map_html.py
====================
根据知识地图数据（JSON格式）生成可交互的 HTML 知识地图文件。
生成后自动在默认浏览器打开（可选）。

知识地图数据由 LLM 在 Step 2 提取后以 JSON 格式输出，
本脚本负责将其渲染为 HTML，之后所有进度更新由 update_progress.py 完成。

用法：
    python generate_map_html.py \
      --data  <知识地图JSON路径> \
      --output <HTML输出路径> \
      [--no-open]   # 不自动打开浏览器

知识地图 JSON 格式：
{
  "doc_title": "文档标题",
  "doc_meta": "2026-03-26 · 直播连麦 · 5位说话人",
  "groups": [
    {
      "title": "主题组标题",
      "desc": "这组话题在解决什么问题",
      "cards": [
        {
          "id": "card-a",
          "label": "A · 知识点标题",
          "title": "知识点完整标题",
          "status": "todo",            // todo / active / done
          "note": "",                   // 进行中时的备注（卡在哪里）
          "done_date": "",              // 完成日期
          "background": "背景说明文字",
          "conclusions": [
            {"type": "key",  "text": "🔑 结论内容", "link": "", "link_text": ""},
            {"type": "warn", "text": "⚠️ 需要验证的内容", "link": "https://...", "link_text": "查看文档"},
            {"type": "info", "text": "📌 背景信息"}
          ],
          "questions": [
            "预置问题1",
            "预置问题2"
          ]
        }
      ]
    }
  ]
}
"""

import json
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

# ── HTML 模板 ─────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f0f0eb; color: #2c2c2c; font-size: 14px; line-height: 1.6;
}
.header {
  position: sticky; top: 0; z-index: 100;
  background: #16213e; color: #fff;
  padding: 10px 20px; display: flex; align-items: center; gap: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}
.header-label { font-size: 11px; font-weight: 700; color: #4a5568;
  text-transform: uppercase; letter-spacing: 0.08em; flex-shrink: 0; }
.pills { display: flex; gap: 5px; flex-wrap: wrap; flex: 1; }
.pill {
  padding: 3px 11px; border-radius: 20px; font-size: 11px;
  font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.pill:hover { opacity: 0.85; transform: translateY(-1px); }
.pill-done   { background:#1c4532; color:#68d391; border:1px solid #276749; }
.pill-active { background:#652b19; color:#fbd38d; border:1px solid #9c4221; }
.pill-todo   { background:#1a202c; color:#718096; border:1px solid #2d3748; }
.progress-wrap { display:flex; align-items:center; gap:8px; flex-shrink:0; }
.progress-bar  { width:80px; height:4px; background:#2d3748; border-radius:2px; overflow:hidden; }
.progress-fill { height:100%; background:linear-gradient(90deg,#38a169,#68d391);
  border-radius:2px; transition:width 0.5s ease; }
.progress-text { font-size:11px; color:#718096; white-space:nowrap; min-width:36px; text-align:right; }
.main { max-width:820px; margin:0 auto; padding:20px 16px 60px; }
.doc-meta { margin-bottom:18px; padding-bottom:14px; border-bottom:1px solid #e2e8f0; }
.doc-title { font-size:17px; font-weight:700; color:#1a202c; margin-bottom:3px; }
.doc-sub   { font-size:11px; color:#a0aec0; }
.group { margin-bottom:22px; }
.group-head { display:flex; align-items:flex-start; gap:8px; margin-bottom:10px; padding-left:2px; }
.group-icon  { font-size:15px; margin-top:1px; }
.group-title { font-size:13px; font-weight:700; color:#2d3748; }
.group-desc  { font-size:11px; color:#718096; margin-top:2px; font-style:italic; }
.card {
  background:#fff; border-radius:10px; margin-bottom:8px;
  overflow:hidden; transition:box-shadow 0.2s; border:1px solid #e8e8e3;
}
.card:hover { box-shadow:0 3px 10px rgba(0,0,0,0.07); }
.card[data-status=done]   { border-left:4px solid #48bb78; }
.card[data-status=active] { border-left:4px solid #ed8936; }
.card[data-status=todo]   { border-left:4px solid #cbd5e0; }
.card-head {
  display:flex; align-items:center; padding:11px 14px;
  cursor:pointer; gap:10px; user-select:none;
}
.status-btn { font-size:17px; flex-shrink:0; cursor:pointer;
  transition:transform 0.15s; line-height:1; }
.status-btn:hover { transform:scale(1.2); }
.card-title { font-weight:600; color:#2d3748; flex:1; font-size:13px; }
.card[data-status=done] .card-title { color:#2f855a; }
.card-badge { font-size:10px; padding:2px 7px; border-radius:10px;
  flex-shrink:0; font-weight:600; }
.badge-done   { background:#f0fff4; color:#276749; }
.badge-active { background:#fffaf0; color:#744210; }
.badge-todo   { background:#f7fafc; color:#a0aec0; }
.expand-icon { font-size:10px; color:#cbd5e0; transition:transform 0.2s; flex-shrink:0; }
.card-head.open .expand-icon { transform:rotate(180deg); }
.card-body { display:none; padding:0 14px 14px; border-top:1px solid #f7fafc; }
.card-body.open { display:block; }
.note-bar {
  margin:10px 0 6px; padding:6px 10px;
  background:#fffbeb; border-left:3px solid #f6ad55;
  border-radius:0 6px 6px 0; font-size:12px; color:#744210;
}
.done-bar {
  margin:10px 0 6px; padding:6px 10px;
  background:#f0fff4; border-left:3px solid #68d391;
  border-radius:0 6px 6px 0; font-size:12px; color:#276749;
}
.sec-label {
  font-size:10px; font-weight:700; color:#b0b8c8;
  text-transform:uppercase; letter-spacing:0.07em; margin:12px 0 5px;
}
.bg-text { font-size:13px; color:#4a5568; line-height:1.7; }
.conclusions { display:flex; flex-direction:column; gap:5px; }
.ci { display:flex; gap:7px; font-size:12px; line-height:1.6;
  padding:5px 9px; border-radius:6px; }
.ci-key  { background:#f0fff4; color:#276749; }
.ci-warn { background:#fffaf0; color:#744210; }
.ci-info { background:#f7fafc; color:#4a5568; }
.ci em { flex-shrink:0; } .ci-text { flex:1; }
.ci-link {
  display:inline-flex; align-items:center; font-size:10px;
  color:#4299e1; text-decoration:none; margin-left:5px;
  padding:1px 5px; background:#ebf8ff; border-radius:3px;
}
.ci-link:hover { background:#bee3f8; }
.qs { display:flex; flex-direction:column; gap:4px; }
.qi { font-size:12px; color:#4a5568; padding:5px 9px;
  background:#f7fafc; border-radius:5px; cursor:pointer; transition:background 0.15s; }
.qi:hover { background:#edf2f7; color:#2b6cb0; }
.qi::before { content:"→ "; color:#cbd5e0; }
.toast {
  position:fixed; bottom:24px; left:50%;
  transform:translateX(-50%) translateY(80px);
  background:#1c4532; color:#68d391; padding:10px 20px;
  border-radius:24px; font-size:13px; font-weight:600;
  box-shadow:0 4px 16px rgba(0,0,0,0.2); transition:transform 0.3s ease;
  z-index:999; white-space:nowrap;
}
.toast.show { transform:translateX(-50%) translateY(0); }
.hint-wrap { text-align:center; margin-bottom:14px; }
.hint { font-size:11px; color:#b0b8c8; padding:7px 12px;
  background:#fff; border-radius:20px; display:inline-block; }
"""

JS = """
const STATUS_CYCLE = ['todo','active','done'];
const STATUS_ICON  = {todo:'⬜',active:'🔄',done:'✅'};
const STATUS_BADGE = {todo:'未开始',active:'进行中',done:'已吸收 · 今天'};
const STATUS_CLASS = {todo:'badge-todo',active:'badge-active',done:'badge-done'};
const PILL_CLASS   = {todo:'pill-todo',active:'pill-active',done:'pill-done'};

function cycleStatus(cardId, e) {
  e.stopPropagation();
  const card = document.getElementById(cardId);
  const cur  = card.dataset.status;
  const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(cur)+1)%STATUS_CYCLE.length];
  card.dataset.status = next;
  card.querySelector('.status-btn').textContent = STATUS_ICON[next];
  const badge = card.querySelector('.card-badge');
  badge.textContent = STATUS_BADGE[next];
  badge.className   = 'card-badge '+STATUS_CLASS[next];
  const body = card.querySelector('.card-body');
  const existing = body.querySelector('.note-bar,.done-bar');
  if (next==='done') {
    if (existing) existing.remove();
    const bar = document.createElement('div');
    bar.className='done-bar';
    bar.textContent='✅ 已吸收 · 知识已保存到 Obsidian';
    body.insertBefore(bar,body.firstChild);
    showToast('🎉 '+card.dataset.label+' 已吸收！');
  } else if (next==='active') {
    if (existing) existing.remove();
    const bar = document.createElement('div');
    bar.className='note-bar'; bar.textContent='🔄 进行中...';
    body.insertBefore(bar,body.firstChild);
  } else { if (existing) existing.remove(); }
  updateProgress();
}

function toggleCard(cardId, e) {
  if (e.target.classList.contains('status-btn')||e.target.classList.contains('qi')) return;
  const card=document.getElementById(cardId);
  card.querySelector('.card-head').classList.toggle('open');
  card.querySelector('.card-body').classList.toggle('open');
}

function updateProgress() {
  const cards=[...document.querySelectorAll('.card')];
  const total=cards.length;
  const done=cards.filter(c=>c.dataset.status==='done').length;
  document.getElementById('progressFill').style.width=Math.round(done/total*100)+'%';
  document.getElementById('progressText').textContent=done+' / '+total;
  buildPills();
  if (done===total) setTimeout(()=>showToast('🎉 全部知识点已吸收！可以清理文件了'),300);
}

function buildPills() {
  const container=document.getElementById('pills');
  container.innerHTML='';
  document.querySelectorAll('.card').forEach(card=>{
    const pill=document.createElement('span');
    pill.className='pill '+PILL_CLASS[card.dataset.status];
    pill.textContent=card.dataset.label;
    pill.onclick=()=>{
      card.scrollIntoView({behavior:'smooth',block:'start'});
      const head=card.querySelector('.card-head');
      const body=card.querySelector('.card-body');
      if (!body.classList.contains('open')){head.classList.add('open');body.classList.add('open');}
    };
    container.appendChild(pill);
  });
}

let toastTimer;
function showToast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.remove('show'),2800);
}

document.addEventListener('DOMContentLoaded',()=>{
  buildPills(); updateProgress();
  const active=document.querySelector('.card[data-status=active]');
  if (active){
    active.querySelector('.card-head').classList.add('open');
    active.querySelector('.card-body').classList.add('open');
  }
});
"""


def render_card(card: dict) -> str:
    status    = card.get("status", "todo")
    card_id   = card["id"]
    label     = card.get("label", card["title"])
    title     = card["title"]
    note      = card.get("note", "")
    done_date = card.get("done_date", "今天")

    status_icon  = {"todo": "⬜", "active": "🔄", "done": "✅"}[status]
    badge_text   = {"todo": "未开始", "active": "进行中", "done": f"已吸收 · {done_date}"}[status]
    badge_class  = {"todo": "badge-todo", "active": "badge-active", "done": "badge-done"}[status]
    body_open    = "open" if status in ("active", "done") else ""

    # 状态提示条
    state_bar = ""
    if status == "active" and note:
        state_bar = f'<div class="note-bar">⚠️ 上次卡在：{note}</div>'
    elif status == "active":
        state_bar = '<div class="note-bar">🔄 进行中...</div>'
    elif status == "done":
        state_bar = f'<div class="done-bar">✅ 已吸收 · {done_date} · 知识已保存到 Obsidian</div>'

    # 背景
    bg = ""
    if card.get("background"):
        bg = f'<div class="sec-label">背景</div><div class="bg-text">{card["background"]}</div>'

    # 结论
    conclusion_html = ""
    if card.get("conclusions"):
        items = ""
        type_map = {"key": "ci-key", "warn": "ci-warn", "info": "ci-info"}
        emoji_map = {"key": "🔑", "warn": "⚠️", "info": "📌"}
        for c in card["conclusions"]:
            css   = type_map.get(c["type"], "ci-info")
            emoji = emoji_map.get(c["type"], "📌")
            link  = f'<a class="ci-link" href="{c["link"]}" target="_blank">{c.get("link_text","查看")} ↗</a>' if c.get("link") else ""
            items += f'<div class="ci {css}"><em>{emoji}</em><span class="ci-text">{c["text"]}{link}</span></div>'
        conclusion_html = f'<div class="sec-label">核心结论</div><div class="conclusions">{items}</div>'

    # 预置问题
    questions_html = ""
    if card.get("questions"):
        qs = "".join(f'<div class="qi">{q}</div>' for q in card["questions"])
        questions_html = f'<div class="sec-label">你可能会问</div><div class="qs">{qs}</div>'

    return f"""
<div class="card" id="{card_id}" data-status="{status}" data-label="{label}">
  <div class="card-head" onclick="toggleCard('{card_id}', event)">
    <span class="status-btn" onclick="cycleStatus('{card_id}', event)" title="点击切换状态">{status_icon}</span>
    <span class="card-title">{title}</span>
    <span class="card-badge {badge_class}">{badge_text}</span>
    <span class="expand-icon">▼</span>
  </div>
  <div class="card-body {body_open}">
    {state_bar}{bg}{conclusion_html}{questions_html}
  </div>
</div>"""


def render_html(data: dict) -> str:
    doc_title = data.get("doc_title", "知识地图")
    doc_meta  = data.get("doc_meta", "")
    generated = datetime.now().strftime("%Y-%m-%d")

    groups_html = ""
    for group in data.get("groups", []):
        cards_html = "".join(render_card(c) for c in group.get("cards", []))
        groups_html += f"""
<div class="group">
  <div class="group-head">
    <span class="group-icon">🗂</span>
    <div>
      <div class="group-title">{group["title"]}</div>
      <div class="group-desc">{group.get("desc","")}</div>
    </div>
  </div>
  {cards_html}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>知识地图 · {doc_title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <span class="header-label">进度</span>
  <div class="pills" id="pills"></div>
  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
    <span class="progress-text" id="progressText">0 / 0</span>
  </div>
</div>
<div class="main">
  <div class="doc-meta">
    <div class="doc-title">{doc_title}</div>
    <div class="doc-sub">{doc_meta} · 生成于 {generated}</div>
  </div>
  <div class="hint-wrap"><span class="hint">💡 点击左侧状态图标切换进度 · 点击标题展开详情</span></div>
  {groups_html}
</div>
<div class="toast" id="toast"></div>
<script>{JS}</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="生成知识地图 HTML")
    parser.add_argument("--data",   required=True, help="知识地图 JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)

    html = render_html(data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"✅ 知识地图已生成：{output_path}")

    if not args.no_open:
        webbrowser.open(output_path.as_uri())
        print("   已在浏览器中打开")


if __name__ == "__main__":
    main()
