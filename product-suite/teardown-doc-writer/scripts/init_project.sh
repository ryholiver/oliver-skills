#!/bin/bash
# 初始化产品拆解文档项目
# 用法：bash init_project.sh "产品名称" "用途"

PRODUCT_NAME="${1:-未命名产品}"
PURPOSE="${2:-学习研究}"
DATE=$(date +%Y-%m-%d)
SAFE_NAME=$(echo "$PRODUCT_NAME" | tr ' ' '_' | tr -d '/' | tr -d '\\')

# 创建项目目录（桌面）
PROJECT_DIR=~/Desktop/${SAFE_NAME}_拆解
mkdir -p "$PROJECT_DIR"

echo "📁 创建项目目录：$PROJECT_DIR"

# 生成主文档（替换占位符）
cat > "$PROJECT_DIR/${SAFE_NAME}_逆向工程拆解_${DATE}.md" << EOF
# ${PRODUCT_NAME} 逆向工程拆解报告

> 拆解用途：${PURPOSE} | 拆解日期：${DATE}
> 本文档为逆向工程推导结果，技术层内容均基于外部观察和合理推断。

---

## 文档元信息

| 字段 | 内容 |
|------|------|
| 产品 | ${PRODUCT_NAME} |
| 拆解用途 | ${PURPOSE} |
| 拆解日期 | ${DATE} |
| 文档版本 | v1.0 (初稿) |

---

## 六层拆解进度

| 层级 | 状态 | 核心发现 |
|------|------|---------|
| 市场层 | ⬜ 未开始 | - |
| 商业层 | ⬜ 未开始 | - |
| 用户层 | ⬜ 未开始 | - |
| 技术层 | ⬜ 未开始 | - |
| 模型层 | ⬜ 未开始 | - |
| 基础层 | ⬜ 未开始 | - |

状态：⬜未开始 | 🔄进行中 | ✅已完成 | ⏭️已跳过

---

## 信息缺口（待补充）

- [ ]

---

*拆解开始：${DATE}*
EOF

echo "✅ 主文档已创建：${SAFE_NAME}_逆向工程拆解_${DATE}.md"
echo "📂 项目路径：$PROJECT_DIR"
echo ""
echo "🚀 开始拆解 ${PRODUCT_NAME}（${PURPOSE}模式）..."
