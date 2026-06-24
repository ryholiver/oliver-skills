#!/usr/bin/env python3
"""
通用 Skill 状态管理脚本
可被任何 skill 复用，用于在 Cowork 环境下持久化工作流状态

用法：
  保存：python scripts/save_state.py save --skill <name> --step <n> --data '<json>'
  读取：python scripts/save_state.py load [--skill <name>]
  清除：python scripts/save_state.py clear [--skill <name>]
  列出：python scripts/save_state.py list

状态文件位置：/tmp/skill_state_{skill_name}.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

STATE_DIR = Path("/tmp")


def state_file(skill_name: str) -> Path:
    return STATE_DIR / f"skill_state_{skill_name}.json"


def save(skill_name: str, step: int, data: dict):
    state = {
        "skill": skill_name,
        "step": step,
        "updated_at": datetime.now().isoformat(),
        **data
    }
    path = state_file(skill_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"[STATE SAVED] {skill_name} | step:{step} | {path}")
    print(json.dumps(state, ensure_ascii=False))


def load(skill_name: str = None):
    if skill_name:
        path = state_file(skill_name)
        if not path.exists():
            print(f"[NO STATE] No saved state for skill: {skill_name}")
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        # 读取最近修改的状态文件
        files = sorted(STATE_DIR.glob("skill_state_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("[NO STATE] No saved state files found")
            sys.exit(1)
        with open(files[0], encoding="utf-8") as f:
            state = json.load(f)
        print(f"[LATEST STATE] from {files[0].name}:")
        print(json.dumps(state, ensure_ascii=False, indent=2))


def clear(skill_name: str = None):
    if skill_name:
        path = state_file(skill_name)
        if path.exists():
            path.unlink()
            print(f"[CLEARED] {path}")
        else:
            print(f"[NOT FOUND] No state file for: {skill_name}")
    else:
        files = list(STATE_DIR.glob("skill_state_*.json"))
        for f in files:
            f.unlink()
        print(f"[CLEARED] {len(files)} state file(s) removed")


def list_all():
    files = list(STATE_DIR.glob("skill_state_*.json"))
    if not files:
        print("[EMPTY] No state files found")
        return
    for f in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
        with open(f, encoding="utf-8") as fh:
            try:
                state = json.load(fh)
                print(f"  {state.get('skill','?')} | step:{state.get('step','?')} | {state.get('updated_at','?')}")
            except Exception:
                print(f"  {f.name} (unreadable)")


def main():
    parser = argparse.ArgumentParser(description="Skill state manager")
    subparsers = parser.add_subparsers(dest="command")

    # save
    p_save = subparsers.add_parser("save")
    p_save.add_argument("--skill", required=True)
    p_save.add_argument("--step", type=int, required=True)
    p_save.add_argument("--data", default="{}", help="JSON string of extra state data")

    # load
    p_load = subparsers.add_parser("load")
    p_load.add_argument("--skill", default=None)

    # clear
    p_clear = subparsers.add_parser("clear")
    p_clear.add_argument("--skill", default=None)

    # list
    subparsers.add_parser("list")

    args = parser.parse_args()

    if args.command == "save":
        try:
            extra = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in --data: {e}")
            sys.exit(1)
        save(args.skill, args.step, extra)

    elif args.command == "load":
        load(getattr(args, "skill", None))

    elif args.command == "clear":
        clear(getattr(args, "skill", None))

    elif args.command == "list":
        list_all()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
