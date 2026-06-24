#!/usr/bin/env python3
"""
插件打包器 - 将插件打包成分发包

用法：
    python scripts/package_plugin.py <插件路径> [输出目录]

示例：
    python scripts/package_plugin.py ./my-plugin
    python scripts/package_plugin.py ./my-plugin ./dist
"""

import fnmatch
import sys
import zipfile
import json
from pathlib import Path

# 打包时排除的目录和文件。
EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", "test", "tests"}
EXCLUDE_GLOBS = {"*.pyc", "*.log", "*.tmp"}
EXCLUDE_FILES = {".DS_Store", "*.swp"}


def should_exclude(rel_path: Path) -> bool:
    """检查路径是否应该被排除。"""
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def validate_plugin(plugin_path):
    """验证插件结构。"""
    plugin_path = Path(plugin_path)

    errors = []
    warnings = []

    # 检查 .claude-plugin/plugin.json 是否存在
    plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        errors.append("缺少 .claude-plugin/plugin.json")
    else:
        try:
            with open(plugin_json, encoding="utf-8") as f:
                data = json.load(f)

            # 检查必需字段
            if "name" not in data:
                errors.append("plugin.json 缺少 'name' 字段")
            if "description" not in data:
                errors.append("plugin.json 缺少 'description' 字段")
            if "version" not in data:
                errors.append("plugin.json 缺少 'version' 字段")
        except json.JSONDecodeError as e:
            errors.append(f"plugin.json JSON 格式无效: {e}")

    # 检查 README.md
    readme = plugin_path / "README.md"
    if not readme.exists():
        warnings.append("缺少 README.md - 建议添加文档")

    # 检查 skills 目录
    skills_dir = plugin_path / "skills"
    if skills_dir.exists():
        skill_count = 0
        for skill_path in skills_dir.rglob("SKILL.md"):
            skill_count += 1
        if skill_count == 0:
            warnings.append("skills/ 目录存在但没有 SKILL.md 文件")

    # 检查 commands 目录
    commands_dir = plugin_path / "commands"
    if commands_dir.exists():
        cmd_count = len(list(commands_dir.glob("*.md")))
        if cmd_count == 0:
            warnings.append("commands/ 目录存在但没有 .md 文件")

    return errors, warnings


def package_plugin(plugin_path, output_dir=None):
    """
    将插件文件夹打包成 .zip 文件。

    参数：
        plugin_path: 插件文件夹路径
        output_dir: 可选的输出目录

    返回：
        创建的包路径，或 None（如果出错）
    """
    plugin_path = Path(plugin_path).resolve()

    # 验证插件文件夹存在
    if not plugin_path.exists():
        print(f"❌ 错误: 找不到插件文件夹: {plugin_path}")
        return None

    if not plugin_path.is_dir():
        print(f"❌ 错误: 路径不是目录: {plugin_path}")
        return None

    # 验证插件结构
    print("验证插件结构...")
    errors, warnings = validate_plugin(plugin_path)

    if errors:
        print("❌ 验证失败:")
        for error in errors:
            print(f"   - {error}")
        return None

    for warning in warnings:
        print(f"⚠️  警告: {warning}")

    if not warnings:
        print("✅ 验证通过\n")

    # 确定输出位置
    plugin_name = plugin_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    # 创建 .zip 文件
    zip_filename = output_path / f"{plugin_name}.zip"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in plugin_path.rglob("*"):
                if not file_path.is_file():
                    continue
                arcname = file_path.relative_to(plugin_path.parent)
                if should_exclude(arcname):
                    print(f"  跳过: {arcname}")
                    continue
                zipf.write(file_path, arcname)
                print(f"  添加: {arcname}")

        print(f"\n✅ 插件已打包至: {zip_filename}")
        return zip_filename

    except Exception as e:
        print(f"❌ 创建包时出错: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/package_plugin.py <插件路径> [输出目录]")
        print("\n示例:")
        print("  python scripts/package_plugin.py ./my-plugin")
        print("  python scripts/package_plugin.py ./my-plugin ./dist")
        sys.exit(1)

    plugin_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"打包插件: {plugin_path}")
    if output_dir:
        print(f"   输出目录: {output_dir}")
    print()

    result = package_plugin(plugin_path, output_dir)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
