#!/usr/bin/env python3
"""
快速插件验证器 - 简单验证插件结构
"""

import json
from pathlib import Path


def validate_skill(plugin_path):
    """
    验证插件结构。

    返回：
        (is_valid, message)
    """
    return validate_plugin(plugin_path)


def validate_plugin(plugin_path):
    """验证插件。"""
    plugin_path = Path(plugin_path)

    # 检查 .claude-plugin/plugin.json 是否存在
    plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        return False, "缺少 .claude-plugin/plugin.json"

    # 验证 JSON
    try:
        with open(plugin_json, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False, "plugin.json JSON 格式无效"

    # 检查必需字段
    required = ["name", "description", "version"]
    missing = [f for f in required if f not in data]
    if missing:
        return False, f"缺少字段: {', '.join(missing)}"

    return True, f"有效的插件: {data.get('name', 'unknown')}"
