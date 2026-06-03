# HTML 卡片模板规范

## 设计原则

- 移动端优先（375px 基准宽度）
- 科技感深色主题（默认）/ 简洁浅色主题（可选）
- 每条资讯独立卡片，方便截图分享
- 原文链接必须可点击

---

## 颜色系统

### 深色主题（默认）
```css
--bg-primary: #0f0f13
--bg-card: #1a1a24
--bg-card-hover: #22222f
--text-primary: #f0f0f5
--text-secondary: #9090a8
--accent-blue: #4f8ef7
--accent-purple: #a78bfa
--border: #2a2a3a
```

### 分类颜色
```css
🔥 重磅发布: #ff6b6b (红)
🧠 研究进展: #4ecdc4 (青)
🏢 公司动态: #ffd93d (黄)
🛠️ 工具&开源: #6bcb77 (绿)
📊 行业观察: #4d96ff (蓝)
💡 产品观察: #c77dff (紫)
```

---

## 卡片 HTML 结构模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 资讯 · 第X期 · YYYY年MM月DD日</title>
  <style>
    /* 全局 */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
      background: #0f0f13;
      color: #f0f0f5;
      padding: 16px;
      max-width: 420px;
      margin: 0 auto;
    }
    
    /* 头部 */
    .header {
      text-align: center;
      padding: 24px 0 20px;
      border-bottom: 1px solid #2a2a3a;
      margin-bottom: 20px;
    }
    .header-badge {
      display: inline-block;
      background: linear-gradient(135deg, #4f8ef7, #a78bfa);
      color: white;
      font-size: 11px;
      padding: 3px 10px;
      border-radius: 20px;
      margin-bottom: 10px;
      letter-spacing: 1px;
    }
    .header h1 { font-size: 20px; font-weight: 700; color: #f0f0f5; }
    .header .date { font-size: 13px; color: #9090a8; margin-top: 6px; }
    .header .count { font-size: 12px; color: #6060a0; margin-top: 4px; }
    
    /* 分类标题 */
    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #9090a8;
      margin: 20px 0 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .section-title::after {
      content: '';
      flex: 1;
      height: 1px;
      background: #2a2a3a;
    }
    
    /* 资讯卡片 */
    .card {
      background: #1a1a24;
      border: 1px solid #2a2a3a;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 10px;
      position: relative;
      overflow: hidden;
    }
    .card::before {
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 3px;
      background: var(--accent-color, #4f8ef7);
      border-radius: 3px 0 0 3px;
    }
    .card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }
    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: #f0f0f5;
      line-height: 1.4;
      flex: 1;
    }
    .card-stars { font-size: 11px; white-space: nowrap; }
    .card-summary {
      font-size: 13px;
      color: #9090a8;
      line-height: 1.6;
      margin-bottom: 10px;
    }
    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .card-tags { display: flex; gap: 6px; flex-wrap: wrap; }
    .tag {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 20px;
      background: #22222f;
      color: #6060a0;
      border: 1px solid #2a2a3a;
    }
    .card-link {
      font-size: 11px;
      color: #4f8ef7;
      text-decoration: none;
      white-space: nowrap;
    }
    .card-link:hover { text-decoration: underline; }
    
    /* 页脚 */
    .footer {
      text-align: center;
      padding: 20px 0 10px;
      border-top: 1px solid #2a2a3a;
      margin-top: 24px;
    }
    .footer p { font-size: 11px; color: #6060a0; }
  </style>
</head>
<body>

  <!-- 头部 -->
  <div class="header">
    <div class="header-badge">AI DIGEST</div>
    <h1>AI 资讯周报</h1>
    <div class="date">2025年XX月XX日 · 第X期</div>
    <div class="count">本期收录 X 条资讯</div>
  </div>

  <!-- 重磅发布 -->
  <div class="section-title">🔥 重磅发布</div>
  
  <div class="card" style="--accent-color: #ff6b6b">
    <div class="card-header">
      <div class="card-title">资讯标题（20字内）</div>
      <div class="card-stars">⭐⭐⭐</div>
    </div>
    <div class="card-summary">一句话摘要，说清楚是什么、为什么重要。控制在50字以内。</div>
    <div class="card-footer">
      <div class="card-tags">
        <span class="tag">OpenAI</span>
        <span class="tag">英文</span>
      </div>
      <a href="#" class="card-link">查看原文 →</a>
    </div>
  </div>

  <!-- 更多分类和卡片按同样结构继续... -->

  <!-- 页脚 -->
  <div class="footer">
    <p>由 AI 资讯 Skill 生成 · Oliver · {日期}</p>
  </div>

</body>
</html>
```

---

## 生成注意事项

1. **每条资讯**对应一个 `.card` 组件
2. **accent-color** 根据分类使用对应颜色
3. **原文链接** href 必须填入真实 URL
4. **期号** 根据当前日期自动计算（2024-01-01 为第1期，每天+1，每周报则每周+1）
5. 如果资讯超过 15 条，考虑拆分为多个 HTML 文件（避免单文件过长）
6. 最终文件名格式：`ai-digest-YYYYMMDD.html`

---

## 浅色主题覆盖（用户选择时替换 CSS）

```css
body { background: #f5f5fa; color: #1a1a2e; }
.card { background: #ffffff; border-color: #e0e0f0; }
.card-title { color: #1a1a2e; }
.card-summary { color: #6060a0; }
.tag { background: #f0f0fa; color: #8080c0; border-color: #e0e0f0; }
.section-title { color: #8080c0; }
.header h1 { color: #1a1a2e; }
.footer p { color: #c0c0e0; }
```

---

## 🆕 新兴话题分区（卡片末尾独立展示）

新兴话题区放在所有常规分类之后、页脚之前，用不同的视觉语言与常规资讯区分。

```html
<!-- 新兴话题分区 -->
<div class="emerging-section">
  <div class="emerging-header">
    <span class="emerging-icon">🆕</span>
    <span class="emerging-title">新兴话题雷达</span>
    <span class="emerging-sub">本期首次出现，尚未进入你的关注列表</span>
  </div>

  <div class="emerging-card">
    <div class="emerging-topic-name">话题名称</div>
    <div class="emerging-summary">一句话描述这个话题是什么，为什么值得注意。</div>
    <div class="emerging-signals">
      <span class="signal-tag">多源共振</span>
      <span class="signal-tag">权威首发</span>
    </div>
    <div class="emerging-action">
      <span class="source-count">3 个信源提及</span>
      <a href="#" class="card-link" target="_blank">查看原文 →</a>
    </div>
  </div>
</div>
```

### 新兴话题区对应 CSS

```css
.emerging-section {
  margin-top: 28px;
  border: 1px dashed #3a3a5a;
  border-radius: 14px;
  padding: 16px 14px;
  background: rgba(167, 139, 250, 0.04);
}
.emerging-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.emerging-icon { font-size: 16px; }
.emerging-title {
  font-size: 13px;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 0.5px;
}
.emerging-sub {
  font-size: 11px;
  color: #5050a0;
}
.emerging-card {
  background: #16161f;
  border: 1px solid #2a2a3a;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
}
.emerging-card:last-child { margin-bottom: 0; }
.emerging-topic-name {
  font-size: 14px;
  font-weight: 700;
  color: #c4b5fd;
  margin-bottom: 6px;
}
.emerging-summary {
  font-size: 12.5px;
  color: #7070a0;
  line-height: 1.6;
  margin-bottom: 10px;
}
.emerging-signals {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.signal-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(167, 139, 250, 0.1);
  color: #a78bfa;
  border: 1px solid rgba(167, 139, 250, 0.2);
}
.emerging-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.source-count { font-size: 11px; color: #4040a0; }
```
