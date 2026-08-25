#!/usr/bin/env bash
# okr-feishu 写入脚本：消费「数字中转站 JSON」+ 工作副本模型，完成 O→KR 写入
#
# 固化（来自真实测试）：
#   - link/user 字段自动数组包裹（CellValue 用 [{"id":"..."}]，不再手拼）
#   - 批量 payload 写 .okrsetting/tmp/，用相对路径传给 lark-cli（@- / 绝对路径会报错）
#   - 写入前 --dry-run 校验形状（字段名/必填/值形状），不匹配就报错不写
#
# 用法：
#   ./okr-write.sh --relay <relay.json> [--dry-run]
#   环境变量：BASE_TOKEN / MODEL_JSON / CYCLE（relay 里带 period 时以 relay 为准）
#
# 前置：
#   - 已跑 setup.sh --ensure-model 物化工作副本 okr-model.json（本脚本不物化，缺失即报错）
#   - 已通过 Obsidian 审核文件确认（本脚本不再渲染审核视图，只负责执行写入）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_TOKEN="${BASE_TOKEN:-BCC3bXivFaq2DBs1UbucpyWvn3c}"
MODEL_JSON="${MODEL_JSON:-$PWD/.okrsetting/okr-model.json}"
RELAY_JSON="${RELAY_JSON:-}"
CYCLE="${CYCLE:-}"
DRY_RUN=0
DEFAULT_OWNER="ou_7c81df7a7e93d9c5cd5679d54e908004"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --relay) RELAY_JSON="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "未知参数: $1（支持 --relay / --dry-run）" >&2; exit 2 ;;
  esac
done

if [[ -z "$RELAY_JSON" ]]; then
  echo "错误：需要 --relay <数字中转站 JSON 路径>" >&2
  exit 2
fi
if [[ ! -f "$RELAY_JSON" ]]; then
  echo "错误：找不到中转站 JSON: $RELAY_JSON" >&2
  exit 2
fi
if [[ ! -f "$MODEL_JSON" ]]; then
  echo "错误：找不到工作副本模型 $MODEL_JSON（先跑 scripts/setup.sh --ensure-model）" >&2
  exit 2
fi

echo "== 1. 校验 base 授权 =="
REQUIRED_SCOPES="base:record:create base:record:read base:record:update"
if ! lark-cli auth check --scope "$REQUIRED_SCOPES" >/dev/null 2>&1; then
  echo "缺少 base 授权，请先运行: lark-cli auth login --domain base" >&2
  exit 1
fi
echo "OK（identity: user）"

export OKR_BASE_TOKEN="$BASE_TOKEN" OKR_MODEL_JSON="$MODEL_JSON" \
       OKR_RELAY_JSON="$RELAY_JSON" OKR_CYCLE="$CYCLE" OKR_DRY_RUN="$DRY_RUN" \
       OKR_DEFAULT_OWNER="$DEFAULT_OWNER"

python3 - <<'PY'
import json, os, subprocess, sys, datetime

BASE = os.environ["OKR_BASE_TOKEN"]
MODEL_JSON = os.environ["OKR_MODEL_JSON"]
RELAY_JSON = os.environ["OKR_RELAY_JSON"]
CYCLE = os.environ.get("OKR_CYCLE", "") or None
DRY_RUN = os.environ.get("OKR_DRY_RUN", "0") == "1"
DEFAULT_OWNER = os.environ.get("OKR_DEFAULT_OWNER", "")

def run(args):
    r = subprocess.run(["lark-cli", *args, "--as", "user"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + "\n" + r.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)

relay = json.load(open(RELAY_JSON, encoding="utf-8"))
model = json.load(open(MODEL_JSON, encoding="utf-8"))

period = relay.get("period") or CYCLE
if not period:
    print("错误：relay 缺 period，且未提供 CYCLE"); sys.exit(1)

# ---------- 模型：semantic -> 字段定义 ----------
def field_map(tname):
    return {f["semantic"]: f for f in model["tables"].get(tname, {}).get("fields", [])}

obj_fields = field_map("目标管理")
kr_fields = field_map("OKR")

def field_name(fields, semantic):
    """返回该 semantic 对应模型字段的当前首选名；deprecated 或缺失返回 None"""
    f = fields.get(semantic)
    if not f or f.get("deprecated"):
        return None
    return f["preferred_names"][0]

def cell_shape(fields, semantic):
    f = fields.get(semantic) or {}
    if f.get("cell_shape"):
        return f["cell_shape"]
    return {"link": "object_array", "user": "object_array",
            "select": "string", "text": "string", "datetime": "string",
            "number": "number", "checkbox": "boolean"}.get(f.get("type"), "string")

def wrap_value(shape, val):
    if shape == "object_array":
        return [{"id": val}]
    return val

def required_check(fields, table_label, names):
    missing = []
    for sem, fn in names:
        if fn is None and fields.get(sem, {}).get("required"):
            missing.append(f"{table_label}.{sem}")
    return missing

# ---------- 解析 relay -> 写记录 ----------
objectives = relay.get("objectives") or []
if not objectives:
    print("错误：relay 无 objectives"); sys.exit(1)

o_name = field_name(obj_fields, "period")
o_obj  = field_name(obj_fields, "objective")
if not o_name or not o_obj:
    print("错误：目标管理表模型缺 period/objective 映射，先跑 /okr-sync"); sys.exit(1)

kr_link = field_name(kr_fields, "objective_link")
kr_kr   = field_name(kr_fields, "key_result")
kr_per  = field_name(kr_fields, "period")
kr_stat = field_name(kr_fields, "status")
kr_owner= field_name(kr_fields, "owner")
kr_start= field_name(kr_fields, "start")
kr_due  = field_name(kr_fields, "due")

o_payloads = []   # [{name: fn, text:..., fields: {...}}]
kr_rows = []      # [{o_index, fields: {...}}]

for i, obj in enumerate(objectives):
    owner_open_id = (obj.get("owner") or {}).get("open_id") or DEFAULT_OWNER
    ofields = {o_name: period, o_obj: obj.get("objective", "")}
    o_payloads.append({"index": i, "text": obj.get("objective", ""), "fields": ofields})
    for kr in obj.get("key_results") or []:
        kf = {}
        if kr_link: kf[kr_link] = {"__link_placeholder__": True}   # 由 O 的 record_id 填充
        if kr_kr:   kf[kr_kr] = kr.get("key_result", "")
        if kr_per:  kf[kr_per] = period
        if kr_stat: kf[kr_stat] = kr.get("status", "未开始")
        if kr_owner and owner_open_id:
            kf[kr_owner] = wrap_value(cell_shape(kr_fields, "owner"), owner_open_id)
        if kr_start and kr.get("start"):
            kf[kr_start] = kr.get("start")
        if kr_due and kr.get("due"):
            kf[kr_due] = kr.get("due")
        kr_rows.append({"o_index": i, "fields": kf, "text": kr.get("key_result", "")})

# ---------- dry-run：校验 + 预览，不写 ----------
if DRY_RUN:
    print("== 2. dry-run 校验（不写表）==")
    o_missing = required_check(obj_fields, "目标管理", [("period", o_name), ("objective", o_obj)])
    kr_missing = required_check(kr_fields, "OKR", [("objective_link", kr_link), ("key_result", kr_kr), ("period", kr_per), ("status", kr_stat)])
    errs = o_missing + kr_missing
    if errs:
        print("  ✗ 模型缺必需字段: " + ", ".join(errs)); sys.exit(1)
    print(f"  将写入 {len(o_payloads)} 条 O + {len(kr_rows)} 条 KR（季度 {period}）")
    for op in o_payloads:
        print(f"  ■ O{op['index']+1}: {op['text']}")
        for kr in [k for k in kr_rows if k['o_index'] == op['index']]:
            print(f"      KR: {kr['text']}")
    print("  字段映射 OK（link/user 已自动数组包裹，payload 走相对路径 .okrsetting/tmp/）")
    sys.exit(0)

# ---------- 写入 ----------
obj_tid = model["tables"]["目标管理"].get("table_id")
kr_tid = model["tables"]["OKR"].get("table_id")
if not obj_tid or not kr_tid:
    print("错误：模型缺 table_id，先跑 /okr-sync"); sys.exit(1)
# 再次校验必需字段（dry-run 之外真写前也兜底）
o_missing = required_check(obj_fields, "目标管理", [("period", o_name), ("objective", o_obj)])
kr_missing = required_check(kr_fields, "OKR", [("objective_link", kr_link), ("key_result", kr_kr), ("period", kr_per), ("status", kr_stat)])
errs = o_missing + kr_missing
if errs:
    print("错误：模型缺必需字段，先跑 /okr-sync: " + ", ".join(errs)); sys.exit(1)

print(f"== 2. 建 O 记录（目标管理，{len(o_payloads)} 条）==")
o_ids = {}
for op in o_payloads:
    out = run(["base", "+record-upsert", "--base-token", BASE, "--table-id", obj_tid,
               "--json", json.dumps(op["fields"], ensure_ascii=False)])
    rid = out["data"]["record"]["record_id_list"][0]
    o_ids[op["index"]] = rid
    print(f"  - O{op['index']+1}: {rid}｜{op['text']}")

print(f"== 3. 批量建 KR（OKR，{len(kr_rows)} 条）==")
# 组装 fields + rows（列序一致，空值显式 null）
cols = [c for c in [kr_link, kr_kr, kr_per, kr_stat, kr_owner, kr_start, kr_due] if c]
rows = []
for kr in kr_rows:
    f = dict(kr["fields"])
    f[kr_link] = [{"id": o_ids[kr["o_index"]]}]
    rows.append([f.get(c) for c in cols])
payload = {"fields": cols, "rows": rows}

# payload 放当前目录 .okrsetting/tmp/，用相对路径传给 lark-cli（@- / 绝对路径会被拒）
tmp_rel = os.path.join(".okrsetting", "tmp", "okr_kr_batch.json")
os.makedirs(os.path.dirname(tmp_rel), exist_ok=True)
with open(tmp_rel, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False)
print(f"  payload → {tmp_rel}")

out = run(["base", "+record-batch-create", "--base-token", BASE, "--table-id", kr_tid,
           "--json", "@" + tmp_rel])
kr_ids = out["data"].get("record_id_list") or []
os.remove(tmp_rel)

print(f"== 完成 ==")
print(f"  O 写入 {len(o_ids)} 条 / KR 写入 {len(kr_ids)} 条")
for i, op in enumerate(o_payloads):
    ks = [k for k in kr_rows if k["o_index"] == i]
    print(f"  ■ O{i+1} ({o_ids[i]})｜{op['text']} → {len(ks)} KR")
print(f"  Base: https://ycni0mrctdn4.feishu.cn/base/{BASE}")
PY
