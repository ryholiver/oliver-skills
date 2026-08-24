#!/usr/bin/env python3
"""从 review.md 配置 + OFDD JSON 自动生成 Review 视图数据。

筛选逻辑：
1. review.md 的 include 声明本次任务范围（观察/推断/判断）；
2. 脚本沿 OFDD 已有关系自动补全上下游链路（判断→推断→观察→证据）；
3. 合并 extra_*（本次新增的候选推断/判断/方向/疑问，标注待回写）；
4. 疑问：extra_questions + OFDD 中阻塞且与链路相关的疑问；
5. 生成带 modules 配置的 v3 数据，供通用模板渲染。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


def parse_front_matter(md_path: Path) -> dict[str, Any]:
    """解析 Markdown 的 YAML front-matter。"""
    text = md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError("review.md 必须以独立行的 --- 包裹 YAML front-matter")
    return yaml.safe_load(match.group(1)) or {}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_indices(ofdd: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "observation": {o["id"]: o for o in ofdd.get("observations", []) if isinstance(o, dict) and o.get("id")},
        "inference": {i["id"]: i for i in ofdd.get("findings", {}).get("inferences", []) if isinstance(i, dict) and i.get("id")},
        "judgment": {j["id"]: j for j in ofdd.get("findings", {}).get("judgments", []) if isinstance(j, dict) and j.get("id")},
        "direction": {d["id"]: d for d in ofdd.get("directions", []) if isinstance(d, dict) and d.get("id")},
    }


def filter_chain(ofdd: dict[str, Any], cfg: dict[str, Any]) -> dict[str, list[str]]:
    """从 include 任务范围出发，自动补全上下游链路。"""
    indices = build_indices(ofdd)
    include = cfg.get("include", {})
    exclude = cfg.get("exclude", {})

    obs_ids = list(include.get("observations", []))
    inf_ids = list(include.get("inferences", []))
    jud_ids = list(include.get("judgments", []))
    dir_ids = list(include.get("directions", []))

    changed = True
    while changed:
        changed = False
        # 判断 → 支撑推断
        for jid in list(jud_ids):
            j = indices["judgment"].get(jid, {})
            for iid in j.get("supported_by_ids", []):
                if iid in indices["inference"] and iid not in inf_ids:
                    inf_ids.append(iid)
                    changed = True
        # 推断 → 基于的观察
        for iid in list(inf_ids):
            i = indices["inference"].get(iid, {})
            for oid in i.get("based_on_observation_ids", []):
                if oid in indices["observation"] and oid not in obs_ids:
                    obs_ids.append(oid)
                    changed = True
        # 方向 → 依据的判断/推断
        for did in list(dir_ids):
            dr = indices["direction"].get(did, {})
            for bid in dr.get("basis_ids", []):
                if bid in indices["judgment"] and bid not in jud_ids:
                    jud_ids.append(bid)
                    changed = True
                if bid in indices["inference"] and bid not in inf_ids:
                    inf_ids.append(bid)
                    changed = True
        # include.directions 为空且无候选方向时：由筛选出的判断反查 OFDD 方向
        if not dir_ids:
            for dr in ofdd.get("directions", []):
                basis = dr.get("basis_ids", [])
                if any(b in jud_ids or b in inf_ids for b in basis) and dr["id"] not in dir_ids:
                    dir_ids.append(dr["id"])
                    changed = True

    # 显式排除
    obs_ids = [x for x in obs_ids if x not in exclude.get("observations", [])]
    inf_ids = [x for x in inf_ids if x not in exclude.get("inferences", [])]
    jud_ids = [x for x in jud_ids if x not in exclude.get("judgments", [])]
    dir_ids = [x for x in dir_ids if x not in exclude.get("directions", [])]

    return {"observations": obs_ids, "inferences": inf_ids, "judgments": jud_ids, "directions": dir_ids}


def filter_questions(ofdd: dict[str, Any], chain: dict[str, list[str]], cfg: dict[str, Any]) -> list[str]:
    """疑问筛选：extra_questions + OFDD 中阻塞且与链路相关的疑问。"""
    extra = [q.get("id", "") for q in cfg.get("extra_questions", [])]
    ids = set(extra)
    chain_ids = set(chain["observations"]) | set(chain["inferences"]) | set(chain["judgments"])
    for q in ofdd.get("findings", {}).get("questions", []):
        blocking = bool(q.get("blocking"))
        if not blocking:
            continue
        triggers = set(q.get("triggered_by_ids", []))
        if triggers & chain_ids:
            ids.add(q["id"])
    return [qid for qid in extra if qid] + [qid for qid in ids if qid not in extra]


def evidence_for(obs: dict[str, Any], ev_idx: dict[str, dict[str, Any]], src_idx: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for eid in obs.get("evidence_ref_ids", []):
        e = ev_idx.get(eid)
        if not e:
            continue
        src = src_idx.get(e.get("source_id", ""), {})
        out.append({
            "id": eid,
            "label": e.get("label", "未命名证据"),
            "quote": e.get("quote_snapshot", "待补"),
            "locator": e.get("locator", "待补"),
            "integrity": e.get("integrity", "needs_locator"),
            "href": src.get("file_or_url", ""),
        })
    return out


def build_verification_data(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    return cfg.get("verification", [])


def collect_extra_items(filter_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """收集 Review 现场新增的候选内容，用于判断是否需要回写或暂停执行。"""
    items: list[dict[str, Any]] = []
    for key in ("extra_inferences", "extra_judgments", "extra_directions", "extra_questions"):
        for item in filter_cfg.get(key, []) or []:
            if isinstance(item, dict):
                items.append(item)
    return items


def build_lifecycle(ofdd: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """生成 Review 生命周期和执行闸门，避免现场补充直接穿透到执行层。"""
    filter_cfg = cfg.get("filter", {}) or {}
    extra_items = collect_extra_items(filter_cfg)
    declared_impact = cfg.get("execution_impact", "none")
    item_impacts = {
        item.get("execution_impact")
        or ("blocking" if item.get("blocking") is True or item.get("blocking") == "是" else "none")
        for item in extra_items
    }
    valid_impacts = {"none", "potential", "blocking"}
    invalid_impacts = ({declared_impact} | item_impacts) - valid_impacts
    if invalid_impacts:
        raise ValueError(f"execution_impact 只能是 none / potential / blocking，发现：{sorted(invalid_impacts)}")
    warnings: list[str] = []

    # 影响等级按 blocking > potential > none 取最高值。
    if "blocking" in item_impacts or declared_impact == "blocking":
        impact = "blocking"
    elif "potential" in item_impacts or declared_impact == "potential":
        impact = "potential"
    else:
        impact = "none"

    # 候选内容默认尚未进入 OFDD，但是否必须回写由其 writeback_status 决定。
    writeback_required = bool(cfg.get("writeback_required", False)) or any(
        item.get("writeback_status") == "pending" for item in extra_items
    )

    review_id = cfg.get("review_id", "REV-UNSET")
    review_version = int(cfg.get("review_version", 1))
    parent_review_id = cfg.get("parent_review_id")
    resumes_from_review_id = cfg.get("resumes_from_review_id") or parent_review_id
    instance_id = cfg.get("review_instance_id") or f"{review_id}-v{review_version}"
    activation_mode = cfg.get("activation_mode", "initial" if not parent_review_id else "inherited_resume")

    # 继承式重启必须能定位父实例和承接成果，防止误做成清空式重开。
    if activation_mode == "inherited_resume":
        if review_version <= 1:
            warnings.append("继承式重启的 review_version 必须大于 1。")
        if not parent_review_id or not resumes_from_review_id:
            warnings.append("继承式重启缺少 parent_review_id 或 resumes_from_review_id。")
        if not cfg.get("inherited_artifacts"):
            warnings.append("继承式重启未声明 inherited_artifacts，无法确认上一轮成果是否被承接。")

    session_state = cfg.get("session_state", "running")
    if impact == "blocking" and session_state == "running":
        session_state = "paused_for_writeback"
        warnings.append("发现会影响执行的新内容，当前 Review 已自动标记为暂停待回写。")
    elif activation_mode == "inherited_resume" and session_state == "running":
        # 续轮默认标记为已继承续作；若仍有新的 blocking，则上面的暂停状态优先。
        session_state = "resumed_inherited"

    source_ofdd_version = cfg.get("source_ofdd_version") or ofdd.get("ofdd_version", "unknown")
    actual_ofdd_version = ofdd.get("ofdd_version", "unknown")
    version_mismatch = (
        cfg.get("source_ofdd_version") is not None
        and cfg.get("source_ofdd_version") != actual_ofdd_version
    )
    if version_mismatch:
        warnings.append(
            f"Review 声明基于 OFDD {cfg.get('source_ofdd_version')}，实际输入为 OFDD {actual_ofdd_version}，需要确认是否续接正确版本。"
        )

    # blocking 只冻结受影响范围；未受影响的执行项仍可按旧的已批准 OFDD 继续。
    if impact == "blocking":
        execution_action = "freeze_and_replan"
        can_continue_affected = False
        can_continue_unaffected = True
        execution_status = "partially_frozen"
    elif impact == "potential":
        execution_action = "continue_with_monitoring"
        can_continue_affected = True
        can_continue_unaffected = True
        execution_status = "active_with_monitoring"
    else:
        execution_action = "continue"
        can_continue_affected = True
        can_continue_unaffected = True
        execution_status = "active"

    affected_scope: list[str] = list(cfg.get("affected_scope", []) or [])
    for item in extra_items:
        for scope_id in item.get("affected_scope", []) or []:
            if scope_id not in affected_scope:
                affected_scope.append(scope_id)

    return {
        "review_id": review_id,
        "review_instance_id": instance_id,
        "review_version": review_version,
        "parent_review_id": parent_review_id,
        "resumes_from_review_id": resumes_from_review_id,
        "source_ofdd_version": source_ofdd_version,
        "activation_mode": activation_mode,
        "session_state": session_state,
        "writeback_required": writeback_required,
        "execution_impact": impact,
        "execution_action": execution_action,
        "can_continue_execution": can_continue_affected,
        "can_continue_affected_scope": can_continue_affected,
        "can_continue_unaffected_scope": can_continue_unaffected,
        "execution_status": execution_status,
        "affected_scope": affected_scope,
        "resume_conditions": cfg.get("resume_conditions", []),
        "inherited_artifacts": cfg.get("inherited_artifacts", []),
        "validation_warnings": warnings,
        "ofdd_version_mismatch": version_mismatch,
    }


def build_v3(ofdd: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    indices = build_indices(ofdd)
    ev_idx = {e["id"]: e for e in ofdd.get("evidence_refs", []) if isinstance(e, dict) and e.get("id")}
    src_idx = {s["id"]: s for s in ofdd.get("sources", []) if isinstance(s, dict) and s.get("id")}
    filter_cfg = cfg.get("filter", {})

    chain = filter_chain(ofdd, filter_cfg)
    extra_inf = {i["id"]: i for i in filter_cfg.get("extra_inferences", [])}
    extra_jud = {j["id"]: j for j in filter_cfg.get("extra_judgments", [])}
    extra_dir = filter_cfg.get("extra_directions", [])
    extra_q = filter_cfg.get("extra_questions", [])

    # 合并 extra 到筛选结果
    inf_ids = chain["inferences"] + [iid for iid in extra_inf if iid not in chain["inferences"]]
    jud_ids = chain["judgments"] + [jid for jid in extra_jud if jid not in chain["judgments"]]
    dir_ids = chain["directions"] + [d["id"] for d in extra_dir if d["id"] not in chain["directions"]]
    obs_ids = chain["observations"]

    def obs_entry(oid: str) -> dict[str, Any]:
        o = indices["observation"][oid]
        relations = {"inferences": [], "judgments": [], "directions": []}
        for iid, i in indices["inference"].items():
            if oid in i.get("based_on_observation_ids", []):
                relations["inferences"].append(iid)
        for jid, j in indices["judgment"].items():
            if any(iid in (j.get("supported_by_ids") or []) for iid in relations["inferences"]):
                relations["judgments"].append(jid)
        for did, dr in indices["direction"].items():
            if any(b in relations["judgments"] or b in relations["inferences"] for b in dr.get("basis_ids", [])):
                relations["directions"].append(did)
        for d in extra_dir:
            if oid in d.get("basis", []):
                relations["directions"].append(d["id"])
        # 疑问触发来源也算关系
        return {
            "id": oid,
            "text": o.get("content", ""),
            "status": "待核验",
            "evidence": evidence_for(o, ev_idx, src_idx),
            "relations": relations,
        }

    facts = [obs_entry(oid) for oid in obs_ids]

    inferences = [
        {"id": iid, "text": indices["inference"][iid].get("content", ""),
         "status": "已支持" if indices["inference"][iid].get("status") == "supported" else "待验证",
         "observations": indices["inference"][iid].get("based_on_observation_ids", [])}
        for iid in inf_ids if iid in indices["inference"]
    ]
    for iid, i in extra_inf.items():
        if iid not in [x["id"] for x in inferences]:
            inferences.append({"id": iid, "text": i.get("text", ""), "status": i.get("status", "候选（待回写）"),
                               "observations": i.get("observations", [])})

    judgments = [
        {"id": jid, "text": indices["judgment"][jid].get("result") or indices["judgment"][jid].get("content") or "",
         "evaluation_object": indices["judgment"][jid].get("evaluation_object", ""),
         "criterion": indices["judgment"][jid].get("criterion", ""),
         "status": "已支持" if indices["judgment"][jid].get("status") == "supported" else "待验证",
         "inferences": indices["judgment"][jid].get("supported_by_ids", [])}
        for jid in jud_ids if jid in indices["judgment"]
    ]
    for jid, j in extra_jud.items():
        if jid not in [x["id"] for x in judgments]:
            judgments.append({"id": jid, "text": j.get("text", ""), "evaluation_object": j.get("evaluation_object", ""),
                              "criterion": j.get("criterion", ""), "status": j.get("status", "候选（待回写）"),
                              "inferences": j.get("inferences", [])})

    # 既展示 OFDD 已有方向，也展示本次 Review 现场产生的候选方向。
    directions = [
        {"id": did, "title": indices["direction"][did].get("direction", indices["direction"][did].get("title", "")),
         "responds": (indices["direction"][did].get("responds") or ""),
         "goal": indices["direction"][did].get("goal", ""),
         "basis": indices["direction"][did].get("basis_ids", indices["direction"][did].get("basis", [])),
         "risk": indices["direction"][did].get("boundary", indices["direction"][did].get("risk", "")),
         "status": indices["direction"][did].get("status", "候选，待回写")}
        for did in chain["directions"] if did in indices["direction"]
    ]
    directions.extend(
        {"id": d["id"], "title": d.get("title", ""), "responds": d.get("responds", ""),
         "goal": d.get("goal", ""), "basis": d.get("basis", d.get("basis_ids", [])), "risk": d.get("risk", ""),
         "status": d.get("status", "候选，待回写")}
        for d in extra_dir if d.get("id") not in {item["id"] for item in directions}
    )

    question_ids = filter_questions(ofdd, chain, filter_cfg)
    q_by_id = {q["id"]: q for q in ofdd.get("findings", {}).get("questions", [])}
    questions = [
        {"id": q["id"], "text": q.get("text", ""), "trigger": q.get("trigger", ""),
         "impact": q.get("impact", ""), "blocking": "是" if q.get("blocking") else "否"}
        for q in extra_q
    ]
    for qid in question_ids:
        if qid in q_by_id and qid not in [x["id"] for x in questions]:
            q = q_by_id[qid]
            questions.append({"id": qid, "text": q.get("question", ""), "trigger": "",
                              "impact": "；".join(q.get("blocking_targets", [])) or "决定", "blocking": "是"})

    unresolved = [
        {"id": q["id"], "issue": q["text"], "impact": q["impact"], "owner": "待补"}
        for q in questions if q["blocking"] == "是"
    ]

    declaration = [
        {"label": "为什么 Review", "value": f"{cfg.get('task', '')}；时间基准：{cfg.get('time_basis', '')}"},
        {"label": "核心问题", "value": cfg.get("core_question", "")},
        {"label": "预期结果", "value": cfg.get("expected_result", "")},
        {"label": "谁拍板", "value": cfg.get("decider", "")},
        {"label": "范围", "value": cfg.get("scope", "")},
        {"label": "不包含", "value": "；".join(cfg.get("excluded", [])) or "无"},
        {"label": "时间基准", "value": cfg.get("time_basis", "")},
    ]

    modules = cfg.get("modules", [])
    lifecycle = build_lifecycle(ofdd, cfg)
    meta = {
        "id": lifecycle["review_id"],
        "instanceId": lifecycle["review_instance_id"],
        "reviewVersion": lifecycle["review_version"],
        "title": cfg.get("title", ""),
        "subtitle": cfg.get("subtitle", ""),
        "date": cfg.get("date", ""),
        "type": cfg.get("type", ""),
        "owner": cfg.get("owner", "待补"),
        "timeBasis": cfg.get("time_basis", ""),
        "sessionState": lifecycle["session_state"],
        "activationMode": lifecycle["activation_mode"],
        "sourceOfddVersion": lifecycle["source_ofdd_version"],
        "parentReviewId": lifecycle["parent_review_id"],
    }

    view = {
        "meta": meta,
        "lifecycle": lifecycle,
        "executionGate": {
            "impact": lifecycle["execution_impact"],
            "action": lifecycle["execution_action"],
            # canContinue 保持兼容，表示受影响范围；未受影响范围单独表达，避免误读为全项目暂停。
            "canContinue": lifecycle["can_continue_affected_scope"],
            "canContinueAffectedScope": lifecycle["can_continue_affected_scope"],
            "canContinueUnaffectedScope": lifecycle["can_continue_unaffected_scope"],
            "executionStatus": lifecycle["execution_status"],
            "affectedScope": lifecycle["affected_scope"],
            "resumeConditions": lifecycle["resume_conditions"],
            "writebackRequired": lifecycle["writeback_required"],
        },
        "declaration": declaration,
        "facts": facts,
        "verification": build_verification_data(cfg),
        "inferences": inferences,
        "judgments": judgments,
        "directions": directions,
        "questions": questions,
        "unresolved": unresolved,
        "conclusion": cfg.get("conclusion", {}),
        "modules": modules,
        "observationPool": {oid: o.get("content", "") for oid, o in indices["observation"].items()},
        "inferencePool": {iid: i.get("content", "") for iid, i in indices["inference"].items()},
        "judgmentPool": {jid: (j.get("result") or j.get("content") or "") for jid, j in indices["judgment"].items()},
    }
    return view


def main() -> int:
    parser = argparse.ArgumentParser(description="从 review.md + OFDD 生成 Review 视图数据")
    parser.add_argument("--review-md", required=True, type=Path)
    parser.add_argument("--ofdd", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cfg = parse_front_matter(args.review_md)
    ofdd = load_json(args.ofdd)
    view = build_v3(ofdd, cfg)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(view, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"已生成：{args.output}")
    print(f"模块数：{len(view.get('modules', []))} | 观察：{len(view.get('facts', []))} | 推断：{len(view.get('inferences', []))} | "
          f"判断：{len(view.get('judgments', []))} | 方向：{len(view.get('directions', []))} | 疑问：{len(view.get('questions', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
