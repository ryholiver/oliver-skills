#!/usr/bin/env python3
"""
发布插件到 claude-code-plugins-plus 市场

用法：
    python scripts/publish.py --plugin-path ./my-plugin
    python scripts/publish.py --plugin-path ./my-plugin --category productivity
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, check=True):
    """执行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        print(f"命令执行失败: {cmd}")
        sys.exit(1)
    return result


def get_github_username():
    """获取 GitHub 用户名"""
    result = run("gh auth status", check=False)
    if result.returncode != 0:
        print("错误: 请先登录 GitHub: gh auth login")
        sys.exit(1)
    result = run("gh api user", check=True)
    user = json.loads(result.stdout)
    return user.get("login", "")


def fork_and_clone_marketplace():
    """Fork 并克隆市场仓库"""
    username = get_github_username()
    repo = "jeremylongshore/claude-code-plugins-plus"

    print(f"Forking {repo}...")
    run(f"gh repo fork {repo} --clone --remote")

    local_path = Path(username) / "claude-code-plugins-plus"
    if local_path.exists():
        os.chdir(local_path)
    else:
        os.chdir("claude-code-plugins-plus")

    print(f"当前目录: {os.getcwd()}")
    return username


def copy_plugin(plugin_path, category="productivity"):
    """复制插件到市场仓库"""
    plugin_path = Path(plugin_path)
    plugin_name = plugin_path.name

    dest = Path("plugins") / category / plugin_name
    if dest.exists():
        print(f"警告: {dest} 已存在，将被覆盖")
        shutil.rmtree(dest)

    print(f"复制 {plugin_path} -> {dest}")
    shutil.copytree(plugin_path, dest)


def update_marketplace_json(plugin_path, category="productivity"):
    """更新 marketplace.json"""
    plugin_path = Path(plugin_path)
    plugin_name = plugin_path.name

    # 读取 plugin.json
    plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"
    if plugin_json_path.exists():
        with open(plugin_json_path, encoding="utf-8") as f:
            plugin_data = json.load(f)
    else:
        plugin_data = {
            "name": plugin_name,
            "description": "插件描述",
            "version": "1.0.0"
        }

    # 读取 marketplace.json
    marketplace_path = Path("marketplace") / "marketplace.json"
    if marketplace_path.exists():
        with open(marketplace_path, encoding="utf-8") as f:
            marketplace = json.load(f)
    else:
        marketplace_path.parent.mkdir(parents=True, exist_ok=True)
        marketplace = {"plugins": []}

    # 检查是否已存在
    existing = [p for p in marketplace["plugins"] if p["name"] == plugin_name]
    if existing:
        print(f"插件 {plugin_name} 已存在，更新...")
        existing[0].update({
            "description": plugin_data.get("description", ""),
            "version": plugin_data.get("version", "1.0.0"),
            "author": plugin_data.get("author", {}),
            "license": plugin_data.get("license", "MIT"),
            "category": category
        })
    else:
        marketplace["plugins"].append({
            "name": plugin_name,
            "description": plugin_data.get("description", ""),
            "version": plugin_data.get("version", "1.0.0"),
            "author": plugin_data.get("author", {}),
            "license": plugin_data.get("license", "MIT"),
            "category": category
        })

    # 写入
    with open(marketplace_path, "w", encoding="utf-8") as f:
        json.dump(marketplace, f, indent=2, ensure_ascii=False)

    print(f"已更新 {marketplace_path}")


def commit_and_pr(plugin_name, message=None):
    """提交并创建 PR"""
    if message is None:
        message = f"feat: add {plugin_name}"

    print("提交更改...")
    run("git add .")

    # 检查是否有更改
    result = run("git diff --cached --stat", check=False)
    if not result.stdout.strip():
        print("没有更改需要提交")
        return

    run(f"git commit -m '{message}'")
    run("git push origin main")

    print("创建 PR...")
    result = run(
        f"gh pr create --title '{message}' --body '添加 {plugin_name} 到市场'",
        check=False
    )

    if result.returncode == 0:
        print("✅ PR 创建成功!")
    else:
        print("PR 可能已存在或创建失败")


def main():
    parser = argparse.ArgumentParser(description="发布插件到 claude-code-plugins-plus")
    parser.add_argument("--plugin-path", required=True, help="插件路径")
    parser.add_argument("--category", default="productivity", help="分类（默认: productivity）")
    parser.add_argument("--no-pr", action="store_true", help="只提交不创建 PR")
    parser.add_argument("--message", help="提交信息")

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not plugin_path.exists():
        print(f"错误: 插件路径不存在: {plugin_path}")
        sys.exit(1)

    plugin_name = plugin_path.name

    # 1. Fork 并克隆
    fork_and_clone_marketplace()

    # 2. 复制插件
    copy_plugin(plugin_path, args.category)

    # 3. 更新 marketplace.json
    update_marketplace_json(plugin_path, args.category)

    # 4. 提交并创建 PR
    if args.no_pr:
        print("提交更改（跳过 PR）...")
        run("git add .")
        run(f"git commit -m '{args.message or f'feat: add {plugin_name}'}'")
        run("git push origin main")
        print("✅ 提交成功!")
    else:
        commit_and_pr(plugin_name, args.message)

    print(f"\n✅ 插件 {plugin_name} 已发布!")
    print(f"\n安装代码:")
    print(f"/plugin install {plugin_name}@claude-code-plugins-plus")


if __name__ == "__main__":
    main()
