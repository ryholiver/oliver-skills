#!/usr/bin/env bash
# okr-feishu setup：对齐「🟡 个人 OKR 执行与复盘」模板到当前周期（幂等、增量、可复跑）
#
# 数据模型 = 演进中的用户数据，默认在【当前目录 .okrsetting/】okr-model.json（不在 skill 内）。
# 当前目录没有模型时，自动从 skill 的 seed（okr-model.default.json）复制一份。
#
# 用法：
#   ./setup.sh                      # 默认：物化模型 + 给两张表「季度」补当前周期选项 + 落快照
#   ./setup.sh --ensure-model       # 仅物化模型（.okrsetting/ 无则从 seed 复制），不读表、不改表
#   ./setup.sh --sync-model         # 只读：全量读表 diff，更新【工作副本】okr-model.json + 快照（= /okr-sync）
#   ./setup.sh --ensure-fields      # 除默认对齐外，补缺的必需字段（只增）
#   ./setup.sh --clean-samples      # 除默认对齐外，删除 2022 模板示例数据（不可逆！）
#
# 环境变量：BASE_TOKEN / CYCLE / MODEL_JSON / SNAPSHOT_DIR / SEED_JSON
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_TOKEN="${BASE_TOKEN:-BCC3bXivFaq2DBs1UbucpyWvn3c}"
CYCLE="${CYCLE:-2026-Q3}"
MODEL_JSON="${MODEL_JSON:-$PWD/.okrsetting/okr-model.json}"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-$PWD/.okrsetting/snapshots}"
SEED_JSON="${SEED_JSON:-$SCRIPT_DIR/../references/okr-model.default.json}"

SYNC=0; ENSURE=0; CLEAN=0; ENSURE_MODEL=0
for a in "$@"; do
  case "$a" in
    --sync-model) SYNC=1 ;;
    --ensure-fields) ENSURE=1 ;;
    --clean-samples) CLEAN=1 ;;
    --ensure-model) ENSURE_MODEL=1 ;;
    *) echo "未知参数: $a（支持 --sync-model / --ensure-fields / --clean-samples / --ensure-model）" >&2; exit 2 ;;
  esac
done

echo "== 1. 校验 base 授权 =="
REQUIRED_SCOPES="base:table:read base:field:read base:record:create base:record:read base:record:update base:field:update"
if ! lark-cli auth check --scope "$REQUIRED_SCOPES" >/dev/null 2>&1; then
  echo "缺少 base 授权，请先运行: lark-cli auth login --domain base" >&2
  exit 1
fi
echo "OK（identity: user）"

# 物化数据模型：当前目录无模型时，从 skill 的 seed 复制一份（只增不覆盖已有演进）
if [ ! -f "$MODEL_JSON" ]; then
  if [ ! -f "$SEED_JSON" ]; then
    echo "错误：找不到 seed 模型 $SEED_JSON" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$MODEL_JSON")"
  cp "$SEED_JSON" "$MODEL_JSON"
  echo "== 0. 物化数据模型（.okrsetting/ 无 okr-model.json，已从 seed 复制）=="
  echo "    → $MODEL_JSON"
else
  echo "== 0. 数据模型已存在（演进保留）=="
  echo "    → $MODEL_JSON"
fi

if [ "$ENSURE_MODEL" = "1" ]; then
  MODEL_VERSION="$(grep -oE '"version"[[:space:]]*:[[:space:]]*[0-9]+' "$MODEL_JSON" | grep -oE '[0-9]+' | head -1)"
  echo "模型就绪: $MODEL_JSON (version=$MODEL_VERSION)，可用 /okr-sync 同步模板最新结构"
  exit 0
fi

export OKR_BASE_TOKEN="$BASE_TOKEN" OKR_CYCLE="$CYCLE" OKR_MODEL_JSON="$MODEL_JSON" \
       OKR_SNAPSHOT_DIR="$SNAPSHOT_DIR" OKR_SYNC="$SYNC" OKR_ENSURE="$ENSURE" OKR_CLEAN="$CLEAN"

python3 - <<'PY'
import json, os, subprocess, sys, datetime

BASE = os.environ["OKR_BASE_TOKEN"]
CYCLE = os.environ["OKR_CYCLE"]
MODEL_JSON = os.environ["OKR_MODEL_JSON"]
SNAPSHOT_DIR = os.environ["OKR_SNAPSHOT_DIR"]
SYNC = os.environ.get("OKR_SYNC", "0") == "1"
ENSURE = os.environ.get("OKR_ENSURE", "0") == "1"
CLEAN = os.environ.get("OKR_CLEAN", "0") == "1"

def run(args):
    r = subprocess.run(["lark-cli", *args, "--as", "user"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + "\n" + r.stderr)
        sys.exit(r.returncode)
    return r.stdout

def jload(s):
    return json.loads(s)

print("== 2. 读取表结构 ==")
tables = jload(run(["base", "+table-list", "--base-token", BASE]))["data"]["tables"]
existing = {t["name"]: t["id"] for t in tables}
for n, i in existing.items():
    print(f"  - {n} ({i})")

model = json.load(open(MODEL_JSON, encoding="utf-8"))
missing = [t for t in model["tables"] if t not in existing]
if missing:
    print("警告：模板表缺失:", ", ".join(missing), "（脚本不自动建表，请在飞书里确认）")

structure = {}
for tname in model["tables"]:
    if tname not in existing:
        structure[tname] = {}
        continue
    structure[tname] = {f["name"]: f for f in
        jload(run(["base", "+field-list", "--base-token", BASE, "--table-id", existing[tname]]))["data"]["fields"]}

def resolve_tid(tname):
    return existing.get(tname, model["tables"][tname].get("table_id"))

def save_snapshot():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    date = datetime.date.today().isoformat()
    snap = {"date": date, "base_token": BASE, "model_version": model.get("version"), "tables": {}}
    for tname, fields in structure.items():
        snap["tables"][tname] = {
            "table_id": resolve_tid(tname),
            "fields": {k: {"type": v["type"], "id": v["id"]} for k, v in fields.items()},
        }
    path = os.path.join(SNAPSHOT_DIR, f"snapshot-{date}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=2)
    return path

# ---------- 同步数据模型（只读） ----------
if SYNC:
    print("== 3. 同步数据模型（只读，diff 缓存模型）==")
    changes = []
    for tname, spec in model["tables"].items():
        cur = structure.get(tname, {})
        for f in spec["fields"]:
            actual = next((cur[pn] for pn in f.get("preferred_names", []) if pn in cur), None)
            if actual is None:
                if not f.get("deprecated"):
                    f["deprecated"] = True
                    changes.append(f"移除(标记deprecated): {tname}.{f['semantic']} ({'、'.join(f['preferred_names'])})")
            else:
                if f.get("deprecated"):
                    f["deprecated"] = False
                    changes.append(f"恢复: {tname}.{f['semantic']} → {actual['name']}")
                if f.get("type") != actual["type"]:
                    changes.append(f"类型变化: {tname}.{f['semantic']} {f.get('type')}→{actual['type']}")
                if actual["name"] not in f["preferred_names"]:
                    f["preferred_names"].insert(0, actual["name"])
                    changes.append(f"字段名适配: {tname}.{f['semantic']} 现匹配「{actual['name']}」")
        known = {pn for f in spec["fields"] for pn in f.get("preferred_names", [])}
        for fname, fdef in cur.items():
            if fname not in known:
                spec["fields"].append({
                    "semantic": f"field_{fname}", "preferred_names": [fname],
                    "required": False, "type": fdef["type"],
                    "deprecated": False, "auto_discovered": True,
                })
                changes.append(f"新增(自动纳入可选): {tname}.{fname} type={fdef['type']}")
    model["version"] = model.get("version", 0) + 1
    model["updated_at"] = datetime.date.today().isoformat()
    with open(MODEL_JSON, "w", encoding="utf-8") as fh:
        json.dump(model, fh, ensure_ascii=False, indent=2)
    if changes:
        print("\n".join("  - " + c for c in changes))
    else:
        print("  - 无变化")
    print(f"模型已更新: {MODEL_JSON} (version={model['version']})")
    print("快照:", save_snapshot())
    sys.exit(0)

# ---------- 对齐季度选项（默认） ----------
print(f"== 3. 对齐「季度」选项，补 {CYCLE} ==")
for tname, spec in model["tables"].items():
    if tname not in existing:
        continue
    cur = structure[tname]
    qfield = next((cur[pn] for f in spec["fields"] if f["semantic"] == "period"
                   for pn in f.get("preferred_names", []) if pn in cur), None)
    if qfield is None:
        print(f"  - {tname}: 未找到「季度」字段，跳过")
        continue
    opts = [o["name"] for o in (qfield.get("options") or [])]
    if CYCLE in opts:
        print(f"  - {tname}: {CYCLE} 已存在，跳过")
        continue
    new_opts = list(qfield.get("options") or []) + [{"name": CYCLE, "hue": "Blue", "lightness": "Lighter"}]
    body = {"name": qfield["name"], "type": "select",
            "multiple": qfield.get("multiple", False), "options": new_opts}
    run(["base", "+field-update", "--base-token", BASE, "--table-id", existing[tname],
         "--field-id", qfield["id"], "--json", json.dumps(body, ensure_ascii=False), "--yes"])
    print(f"  - {tname}: 已追加 {CYCLE}（保留原 {len(opts)} 个选项）")

# ---------- 补必需字段（只增） ----------
if ENSURE:
    print("== 4. 补必需字段（只增，不改不删）==")
    for tname, spec in model["tables"].items():
        if tname not in existing:
            continue
        cur = structure[tname]
        for f in spec["fields"]:
            if not f.get("required") or any(pn in cur for pn in f.get("preferred_names", [])):
                continue
            if f.get("type") == "link":
                print(f"  - 跳过(link 需指定目标表): {tname}.{f['semantic']}")
                continue
            body = {"name": f["preferred_names"][0], "type": f["type"]}
            if f.get("type") == "select":
                body["multiple"] = False
                body["options"] = [{"name": o, "hue": "Blue", "lightness": "Lighter"} for o in f.get("options", [])]
            run(["base", "+field-create", "--base-token", BASE, "--table-id", existing[tname],
                 "--json", json.dumps(body, ensure_ascii=False)])
            print(f"  - 已新增: {tname}.{body['name']} type={f['type']}")

# ---------- 清理 2022 示例（不可逆） ----------
if CLEAN:
    print("== 5. 清理 2022 模板示例数据（不可逆）==")
    for tname in model["tables"]:
        if tname not in existing:
            continue
        out = run(["base", "+record-list", "--base-token", BASE, "--table-id", existing[tname], "--limit", "200"])
        ids = []
        for line in out.splitlines():
            if "2022" in line and line.strip().startswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if cells and cells[0].startswith("rec"):
                    ids.append(cells[0])
        ids = list(dict.fromkeys(ids))
        if ids:
            argv = ["base", "+record-delete", "--base-token", BASE, "--table-id", existing[tname], "--yes"]
            for rid in ids:
                argv += ["--record-id", rid]
            run(argv)
            print(f"  - {tname}: 删除 {len(ids)} 条: {', '.join(ids)}")
        else:
            print(f"  - {tname}: 无 2022 示例")

print("完成。快照:", save_snapshot())
PY
