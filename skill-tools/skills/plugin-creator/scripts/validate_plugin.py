#!/usr/bin/env python3
"""
Plugin Validator - validates plugin structure and metadata

Usage:
    python scripts/validate_plugin.py <plugin-path>

Validation checks (high standard — plugins created with this tool should pass all):
    1. Plugin path exists and is a directory
    2. .claude-plugin/plugin.json exists and is valid JSON
    3. plugin.json has required fields: name, description, version
    4. skills/ directory exists and contains at least one SKILL.md
    5. README.md exists
"""

import json
import sys
from pathlib import Path


def validate_plugin(plugin_path):
    """
    Validate plugin structure and metadata.

    Returns:
        (is_valid, message)
    """
    plugin_path = Path(plugin_path)

    # Check plugin exists
    if not plugin_path.exists():
        return False, "Plugin not found: " + str(plugin_path)

    if not plugin_path.is_dir():
        return False, "Path is not a directory: " + str(plugin_path)

    # Check .claude-plugin directory
    claude_plugin_dir = plugin_path / ".claude-plugin"
    if not claude_plugin_dir.exists():
        return False, "Missing .claude-plugin directory"

    # Check plugin.json
    plugin_json = claude_plugin_dir / "plugin.json"
    if not plugin_json.exists():
        return False, "Missing .claude-plugin/plugin.json"

    # Validate JSON
    try:
        with open(plugin_json, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, "Invalid JSON in plugin.json: " + str(e)

    # Check required fields
    required_fields = ["name", "description", "version"]
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return False, "Missing fields in plugin.json: " + ", ".join(missing_fields)

    # Validate field values
    if not isinstance(data["name"], str) or not data["name"]:
        return False, "plugin.json 'name' must be a non-empty string"

    if not isinstance(data["description"], str) or not data["description"]:
        return False, "plugin.json 'description' must be a string"

    if not isinstance(data["version"], str) or not data["version"]:
        return False, "plugin.json 'version' must be a string"

    # Check skills directory
    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        return False, "Missing skills directory"
    skill_files = list(skills_dir.rglob("SKILL.md"))
    if not skill_files:
        return False, "No SKILL.md found in skills directory"

    # Check README
    readme = plugin_path / "README.md"
    if not readme.exists():
        return False, "Missing README.md"

    return True, "Valid: " + data["name"] + " v" + data["version"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_plugin.py <plugin-path>")
        sys.exit(1)

    plugin_path = sys.argv[1]

    is_valid, message = validate_plugin(plugin_path)

    if is_valid:
        print("[OK] " + message)
        sys.exit(0)
    else:
        print("[FAIL] " + message)
        sys.exit(1)


if __name__ == "__main__":
    main()
