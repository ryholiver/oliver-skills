#!/usr/bin/env python3
"""【已废弃，仅兼容】将 OFDD JSON 转换为旧版 Review View JSON（全量映射）。

新流程请使用 build_review_from_md.py（review.md 配置 + 自动筛选补链）。

这个脚本负责“上游 OFDD → 下游 Review 视图”的结构转换，
不负责渲染 HTML，也不修改事实源文件。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any


# Review 页面需要的顶层字段固定，先在这里定义，避免生成半成品数据。
REQUIRED_TOP_LEVEL = (
    "meta",
    "objective",
    "summary",
    "reasoningChains",
    "questions",
    "directions",
    "recommendation",
    "decision",
    "unresolved",
    "writeback",
)


# 这份映射是展示层的语义映射，不等于上游事实本身。
STATUS_MAP = {
    "blocked": "阻塞中",
    "blocked_by_questions": "问题阻塞",
    "partially_ready": "部分就绪",
    "ready_for_decision": "待决策",
    "needs_human_review": "待负责人确认",
    "approved": "已完成",
    "draft": "草稿",
    "review_required": "待负责人确认",
    "decision_ready": "待决策",
    "awaiting_decision": "待决策",
    "exploring": "探索中",
    "superseded": "已替代",
    "revoked": "已撤销",
}


DECISION_STATUS_MAP = {
    "proposed": "拟议",
    "approved": "已拍板",
    "revoked": "已撤销",
    "superseded": "已替代",
    "defer": "暂缓",
    "deferred": "暂缓",
}


INFERENCE_STATUS_MAP = {
    "pending": "待验证",
    "supported": "已支持",
    "refuted": "已否定",
    "inconclusive": "不确定",
    "conflicted": "冲突",
}


STATUS_TONE_MAP = {
    "pending": "pending",
    "supported": "supported",
    "selected": "selected",
    "decided": "decided",
    "blocked": "blocked",
    "neutral": "neutral",
}


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    skill_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="把 OFDD JSON 转换成 Review View JSON。")
    parser.add_argument("--input", required=True, type=Path, help="OFDD JSON 文件")
    parser.add_argument("--output", required=True, type=Path, help="输出的 Review View JSON 文件")
    parser.add_argument(
        "--focus-decision-id",
        default=None,
        help="本次 Review 的焦点 Decision ID；不填时自动挑选，但会保留多决策提示",
    )
    parser.add_argument(
        "--review-id",
        default=None,
        help="显式指定 Review ID；不填时按日期自动生成",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Review 日期，默认使用当天 YYYY-MM-DD",
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=skill_root,
        help="skill 根目录；默认取当前脚本上两级目录",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 并保证顶层是对象。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"找不到输入文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 格式错误：{exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("OFDD 输入顶层必须是 JSON 对象。")
    return data


def as_str(value: Any, default: str = "") -> str:
    """把任意值转成展示用字符串。"""
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def dedupe(items: list[str]) -> list[str]:
    """保持原顺序去重。"""
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def split_tags(text: str) -> list[str]:
    """把判断标准切成适合展示的标签。"""
    if not text:
        return []
    raw_parts = []
    for separator in ("；", ";", "，", ",", "、", "\n"):
        if separator in text:
            raw_parts = [part.strip() for part in text.split(separator)]
            break
    if not raw_parts:
        raw_parts = [text.strip()]
    return [part for part in raw_parts if part]


def join_non_empty(parts: list[str], separator: str = "；") -> str:
    """拼接非空字符串。"""
    filtered = [part for part in parts if part]
    return separator.join(filtered)


def build_source_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Source ID 建索引，方便证据和回链查找。"""
    return {item["id"]: item for item in ofdd.get("sources", []) if isinstance(item, dict) and item.get("id")}


def build_evidence_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Evidence ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("evidence_refs", []) if isinstance(item, dict) and item.get("id")}


def build_observation_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Observation ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("observations", []) if isinstance(item, dict) and item.get("id")}


def build_inference_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Inference ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("findings", {}).get("inferences", []) if isinstance(item, dict) and item.get("id")}


def build_judgment_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Judgment ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("findings", {}).get("judgments", []) if isinstance(item, dict) and item.get("id")}


def build_direction_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Direction ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("directions", []) if isinstance(item, dict) and item.get("id")}


def build_question_index(ofdd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按 Question ID 建索引。"""
    return {item["id"]: item for item in ofdd.get("findings", {}).get("questions", []) if isinstance(item, dict) and item.get("id")}


def pick_primary_evidence_id(evidence_ids: list[str], evidence_index: dict[str, dict[str, Any]]) -> str | None:
    """优先挑选完整证据，否则使用第一个可用证据。"""
    if not evidence_ids:
        return None
    complete = [eid for eid in evidence_ids if evidence_index.get(eid, {}).get("integrity") == "complete"]
    if complete:
        return complete[0]
    return evidence_ids[0]


def build_evidence_object(evidence_id: str | None, evidence_index: dict[str, dict[str, Any]], source_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """把 OFDD Evidence Reference 转成 Review 证据对象。"""
    if not evidence_id or evidence_id not in evidence_index:
        return {
            "id": "N/A",
            "label": "待补证据",
            "quote": "待补",
            "locator": "待补",
            "integrity": "needs_anchor",
            "href": "",
        }

    evidence = evidence_index[evidence_id]
    source = source_index.get(as_str(evidence.get("source_id")), {})
    href = as_str(source.get("file_or_url"))
    if not href:
        href = as_str(source.get("title"))

    return {
        "id": evidence_id,
        "label": as_str(evidence.get("label"), "未命名证据"),
        "quote": as_str(evidence.get("quote_snapshot"), "待补"),
        "locator": as_str(evidence.get("locator"), "待补"),
        "integrity": as_str(evidence.get("integrity"), "needs_locator"),
        "href": href,
    }


def build_meta(ofdd: dict[str, Any], review_date: str, review_id: str) -> dict[str, Any]:
    """构造 Review 顶层 meta。"""
    document_meta = ofdd.get("document_meta", {}) if isinstance(ofdd.get("document_meta"), dict) else {}
    review_gate = ofdd.get("review_gate", {}) if isinstance(ofdd.get("review_gate"), dict) else {}
    title = as_str(document_meta.get("title")) or as_str(document_meta.get("project_name")) or "未命名项目"
    subtitle = as_str(review_gate.get("summary")) or "本次 Review"
    source_of_truth = Path(as_str(ofdd.get("_source_file", "ofdd-data.json"))).name

    return {
        "id": review_id,
        "title": title,
        "subtitle": subtitle,
        "type": "决策型 Review",
        "date": review_date,
        "status": normalize_review_status(as_str(review_gate.get("review_status")) or as_str(document_meta.get("status"))),
        "owner": as_str(document_meta.get("owner"), "待补"),
        "sourceOfTruth": source_of_truth,
        "timeBasis": f"截至 {review_date}",
    }


def normalize_review_status(status: str) -> str:
    """把 OFDD 状态映射为 Review 展示状态。"""
    return STATUS_MAP.get(status, as_str(status, "待负责人确认"))


def normalize_decision_status(status: str) -> str:
    """把 OFDD Decision 状态映射为 Review 展示状态。"""
    return DECISION_STATUS_MAP.get(status, as_str(status, "待决策"))


def normalize_inference_status(status: str) -> str:
    """把推断状态映射为更适合页面阅读的说法。"""
    return INFERENCE_STATUS_MAP.get(status, as_str(status, "待验证"))


def normalize_direction_status(status: str) -> str:
    """把方向状态映射为页面可读文案。"""
    return STATUS_MAP.get(status, as_str(status, "待确认"))


def format_question_blocking(blocking: bool, blocking_targets: list[str]) -> str:
    """把问题阻塞性转换为模板可直接展示的文字。"""
    if blocking and blocking_targets:
        return "阻塞：" + "、".join(blocking_targets)
    if blocking:
        return "阻塞当前决定"
    return "当前不阻塞"


def normalize_chain_tone(judgment_status: str, inference_status: str) -> str:
    """根据判断与推断状态给出页面颜色语气。"""
    if inference_status == "supported" or judgment_status == "supported":
        return STATUS_TONE_MAP["supported"]
    if judgment_status in {"refuted", "conflicted"} or inference_status in {"refuted", "conflicted"}:
        return STATUS_TONE_MAP["blocked"]
    if judgment_status == "selected":
        return STATUS_TONE_MAP["selected"]
    return STATUS_TONE_MAP["pending"]


def build_objective(ofdd: dict[str, Any], review_gate: dict[str, Any]) -> dict[str, Any]:
    """构造本次 Review 的核心问题、范围和评价标准。"""
    document_meta = ofdd.get("document_meta", {}) if isinstance(ofdd.get("document_meta"), dict) else {}
    findings = ofdd.get("findings", {}) if isinstance(ofdd.get("findings"), dict) else {}
    questions = findings.get("questions", []) if isinstance(findings.get("questions"), list) else []
    judgments = findings.get("judgments", []) if isinstance(findings.get("judgments"), list) else []
    recommended_questions = review_gate.get("recommended_review_questions", []) if isinstance(review_gate.get("recommended_review_questions"), list) else []

    core_question = ""
    if recommended_questions:
        core_question = as_str(recommended_questions[0])
    elif questions:
        core_question = as_str(questions[0].get("question"))
    else:
        core_question = "本次 Review 应如何理解当前 OFDD 结论并决定是否继续推进？"

    criteria: list[str] = []
    for judgment in judgments:
        criterion = as_str(judgment.get("criterion"))
        if criterion:
            criteria.extend(split_tags(criterion))
    if not criteria:
        criteria = ["评价标准待补"]
    criteria = dedupe(criteria)

    out_of_scope = document_meta.get("out_of_scope", []) if isinstance(document_meta.get("out_of_scope"), list) else []
    excluded = "；".join(as_str(item) for item in out_of_scope if as_str(item)) or "无"

    goal = as_str(review_gate.get("recommended_decision_wording", {}).get("content"))
    if not goal:
        goal = as_str(review_gate.get("summary"), "形成本次 Review 的结论与回写项")

    return {
        "question": core_question,
        "goal": goal,
        "scope": as_str(document_meta.get("scope"), "待补"),
        "excluded": excluded,
        "criteria": criteria,
    }


def build_summary(ofdd: dict[str, Any], review_gate: dict[str, Any], unresolved: list[dict[str, Any]]) -> dict[str, Any]:
    """构造首屏摘要。"""
    summary_text = as_str(review_gate.get("summary"))
    recommended_wording = as_str(review_gate.get("recommended_decision_wording", {}).get("content"))
    if not recommended_wording:
        recommended_wording = "当前建议仍需结合阻塞问题和证据完整性再判断。"

    uncertainty_items = [item.get("issue", "") for item in unresolved if item.get("blocking")]
    uncertainty = "；".join([item for item in uncertainty_items if item]) or summary_text or "阻塞问题尚未闭合。"

    return {
        "current": summary_text or "当前核心判断待补。",
        "recommendation": recommended_wording,
        "uncertainty": uncertainty,
    }


def build_reasoning_chains(ofdd: dict[str, Any], source_index: dict[str, dict[str, Any]], evidence_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """把 Judgment / Inference / Observation / Evidence 串成判断链。"""
    findings = ofdd.get("findings", {}) if isinstance(ofdd.get("findings"), dict) else {}
    judgments = findings.get("judgments", []) if isinstance(findings.get("judgments"), list) else []
    inferences = findings.get("inferences", []) if isinstance(findings.get("inferences"), list) else []
    observations = ofdd.get("observations", []) if isinstance(ofdd.get("observations"), list) else []

    inference_index = build_inference_index(ofdd)
    observation_index = build_observation_index(ofdd)
    judgment_order = [item["id"] for item in judgments if isinstance(item, dict) and item.get("id")]
    inference_order = [item["id"] for item in inferences if isinstance(item, dict) and item.get("id")]

    chains: list[dict[str, Any]] = []
    chain_counter = 1

    for judgment_id in judgment_order:
        judgment = next((item for item in judgments if item.get("id") == judgment_id), None)
        if not judgment:
            continue

        supported_ids = judgment.get("supported_by_ids", []) if isinstance(judgment.get("supported_by_ids"), list) else []
        matched_inferences = [inference_index.get(inf_id) for inf_id in supported_ids if inference_index.get(inf_id)]
        if not matched_inferences:
            matched_inferences = [{
                "id": "N/A",
                "content": "本判断直接基于观察，未新增独立推断。",
                "status": "pending",
                "based_on_observation_ids": judgment.get("supported_by_ids", []) if isinstance(judgment.get("supported_by_ids"), list) else [],
            }]

        for inference in matched_inferences:
            based_obs_ids = inference.get("based_on_observation_ids", []) if isinstance(inference.get("based_on_observation_ids"), list) else []
            matched_observations = [observation_index.get(obs_id) for obs_id in based_obs_ids if observation_index.get(obs_id)]

            if not matched_observations and observations:
                # 如果推断没有直接映射到观察，就尽量保留同一判断下所有观察，避免整条链空掉。
                judgment_obs_ids: list[str] = []
                for candidate_inference_id in supported_ids:
                    candidate = inference_index.get(candidate_inference_id)
                    if candidate and isinstance(candidate.get("based_on_observation_ids"), list):
                        judgment_obs_ids.extend([as_str(obs_id) for obs_id in candidate.get("based_on_observation_ids", []) if as_str(obs_id)])
                judgment_obs_ids = dedupe(judgment_obs_ids)
                matched_observations = [observation_index.get(obs_id) for obs_id in judgment_obs_ids if observation_index.get(obs_id)]

            chain_observations: list[dict[str, Any]] = []
            for obs in matched_observations:
                evidence_ids = obs.get("evidence_ref_ids", []) if isinstance(obs.get("evidence_ref_ids"), list) else []
                primary_evidence_id = pick_primary_evidence_id([as_str(eid) for eid in evidence_ids if as_str(eid)], evidence_index)
                evidence_obj = build_evidence_object(primary_evidence_id, evidence_index, source_index)
                chain_observations.append({
                    "id": as_str(obs.get("id"), "O-N/A"),
                    "text": as_str(obs.get("content"), "待补观察"),
                    "evidence": evidence_obj,
                })

            judgment_status = as_str(judgment.get("status"), "pending")
            inference_status = as_str(inference.get("status"), "pending")
            result_text = as_str(judgment.get("result"))
            evaluation_object = as_str(judgment.get("evaluation_object"), "判断")
            criterion = as_str(judgment.get("criterion"))
            condition = result_text if result_text and len(result_text) <= 120 else "N/A"

            chain_status = normalize_inference_status(inference_status)
            chain_tone = normalize_chain_tone(judgment_status, inference_status)

            chains.append({
                "id": f"CHAIN-{chain_counter:02d}",
                "title": evaluation_object,
                "status": chain_status,
                "statusTone": chain_tone,
                "judgment": {
                    "id": as_str(judgment.get("id"), "F-J-N/A"),
                    "text": result_text or evaluation_object,
                    "criteria": split_tags(criterion),
                    "condition": condition,
                },
                "inference": {
                    "id": as_str(inference.get("id"), "F-I-N/A"),
                    "text": as_str(inference.get("content"), "本判断暂无独立推断。"),
                },
                "observations": chain_observations,
            })
            chain_counter += 1

    # 如果没有任何判断链，至少保留一个占位链，避免 HTML 首页失焦。
    if not chains:
        chains.append({
            "id": "CHAIN-01",
            "title": "本轮尚未形成可展示的判断链",
            "status": "待验证",
            "statusTone": "pending",
            "judgment": {
                "id": "N/A",
                "text": "暂无可展示判断。",
                "criteria": ["待补"],
                "condition": "N/A",
            },
            "inference": {
                "id": "N/A",
                "text": "本轮未抽取到可展示的独立推断。",
            },
            "observations": [],
        })

    return chains


def build_questions(ofdd: dict[str, Any]) -> list[dict[str, Any]]:
    """把 OFDD Questions 转成 Review Questions。"""
    findings = ofdd.get("findings", {}) if isinstance(ofdd.get("findings"), dict) else {}
    questions = findings.get("questions", []) if isinstance(findings.get("questions"), list) else []

    review_questions: list[dict[str, Any]] = []
    for question in questions:
        blocking = bool(question.get("blocking"))
        blocking_targets = [as_str(item) for item in question.get("blocking_targets", []) if as_str(item)] if isinstance(question.get("blocking_targets"), list) else []
        review_questions.append({
            "id": as_str(question.get("id"), "F-Q-N/A"),
            "text": as_str(question.get("question"), "待补问题"),
            "purpose": as_str(question.get("verification_method"), "待补"),
            "impact": join_non_empty([
                "阻塞对象：" + "、".join(blocking_targets) if blocking_targets else "",
                "触发来源：" + "、".join([as_str(item) for item in question.get("triggered_by_ids", []) if as_str(item)]) if isinstance(question.get("triggered_by_ids"), list) else "",
            ]),
            "blocking": format_question_blocking(blocking, blocking_targets),
            "evidenceNeeded": as_str(question.get("verification_method"), "待补"),
            "owner": as_str(question.get("owner"), "待补"),
            "tone": "blocking" if blocking else "later",
        })
    return review_questions


def build_directions(ofdd: dict[str, Any]) -> list[dict[str, Any]]:
    """把方向转换成可比较的 Review 卡片。"""
    findings = ofdd.get("findings", {}) if isinstance(ofdd.get("findings"), dict) else {}
    directions = ofdd.get("directions", []) if isinstance(ofdd.get("directions"), list) else []

    judgment_index = build_judgment_index(ofdd)
    inference_index = build_inference_index(ofdd)
    review_gate = ofdd.get("review_gate", {}) if isinstance(ofdd.get("review_gate"), dict) else {}
    ready_direction_ids = set([as_str(item) for item in review_gate.get("ready_direction_ids", []) if as_str(item)]) if isinstance(review_gate.get("ready_direction_ids"), list) else set()
    blocked_question_ids = set([as_str(item) for item in review_gate.get("blocking_question_ids", []) if as_str(item)]) if isinstance(review_gate.get("blocking_question_ids"), list) else set()

    review_directions: list[dict[str, Any]] = []
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for idx, direction in enumerate(directions):
        direction_id = as_str(direction.get("id"), f"DIR-{idx+1:03d}")
        basis_ids = direction.get("basis_ids", []) if isinstance(direction.get("basis_ids"), list) else []
        basis_texts: list[str] = []
        for basis_id in basis_ids:
            if basis_id in judgment_index:
                judgment = judgment_index[basis_id]
                basis_texts.append(as_str(judgment.get("result")) or as_str(judgment.get("evaluation_object")))
            elif basis_id in inference_index:
                inference = inference_index[basis_id]
                basis_texts.append(as_str(inference.get("content")))
        if not basis_texts:
            basis_texts = ["方向依据待补"]

        boundary = as_str(direction.get("boundary"), "范围待补")
        related_open_questions = [
            as_str(item) for item in direction.get("open_question_ids", []) if as_str(item)
        ] if isinstance(direction.get("open_question_ids"), list) else []
        blocking_questions = [qid for qid in related_open_questions if qid in blocked_question_ids]
        risk_parts = []
        if blocking_questions:
            risk_parts.append("阻塞问题：" + "、".join(blocking_questions))
        risk_parts.append(boundary)
        title = as_str(direction.get("direction"), "未命名方向")

        review_directions.append({
            "id": direction_id,
            "letter": letters[idx] if idx < len(letters) else f"D{idx+1}",
            "title": title,
            "goal": as_str(direction.get("goal"), "待补"),
            "benefits": basis_texts,
            "risk": join_non_empty(risk_parts),
            "boundary": boundary,
            "status": normalize_direction_status(as_str(direction.get("status"), "awaiting_decision")),
            "reviewReady": direction_id in ready_direction_ids,
            "selected": False,
        })
    return review_directions


def choose_focal_decision(ofdd: dict[str, Any], focus_decision_id: str | None) -> dict[str, Any] | None:
    """选择本次 Review 的焦点 Decision。"""
    decisions = ofdd.get("decisions", []) if isinstance(ofdd.get("decisions"), list) else []
    if not decisions:
        return None

    if focus_decision_id:
        for decision in decisions:
            if as_str(decision.get("id")) == focus_decision_id:
                return decision

    approved = [item for item in decisions if as_str(item.get("status")) == "approved"]
    if approved:
        return approved[0]

    proposed = [item for item in decisions if as_str(item.get("status")) == "proposed"]
    if proposed:
        return proposed[0]

    return decisions[0]


def build_recommendation(ofdd: dict[str, Any], review_directions: list[dict[str, Any]], focal_decision: dict[str, Any] | None, unresolved: list[dict[str, Any]]) -> dict[str, Any]:
    """构造推荐方向卡片。"""
    review_gate = ofdd.get("review_gate", {}) if isinstance(ofdd.get("review_gate"), dict) else {}
    recommended_wording = as_str(review_gate.get("recommended_decision_wording", {}).get("content"))

    # 只从显式推荐语义中取推荐方向，不从 ready_direction_ids 或首个方向猜测。
    direction_id = "N/A"
    if focal_decision and isinstance(focal_decision.get("target_direction_ids"), list) and focal_decision.get("target_direction_ids"):
        direction_id = as_str(focal_decision.get("target_direction_ids")[0], "N/A")

    direction = next((item for item in review_directions if item.get("id") == direction_id), None)
    if direction:
        title = f"建议优先采用：{as_str(direction.get('title'))}"
    elif recommended_wording:
        title = "建议先按当前拟议口径继续审查"
    else:
        title = "当前尚无可直接落地的推荐方向"

    condition_parts = [item.get("issue", "") for item in unresolved if item.get("blocking")]
    condition = recommended_wording
    if condition_parts:
        condition = join_non_empty([condition, "需先关闭：" + "；".join(condition_parts[:3])])

    rationale_parts = [recommended_wording, as_str(review_gate.get("summary"))]
    rationale = join_non_empty([part for part in rationale_parts if part]) or "当前建议仍需等待阻塞问题闭合后再确认。"

    return {
        "directionId": direction_id,
        "title": title,
        "rationale": rationale,
        "condition": condition or "待补",
    }


def apply_direction_selection(review_directions: list[dict[str, Any]], recommendation: dict[str, Any], focal_decision: dict[str, Any] | None) -> list[dict[str, Any]]:
    """根据推荐方向或已批准决定回填方向选中状态。"""
    recommended_id = as_str(recommendation.get("directionId"), "N/A")
    approved_selected_ids: set[str] = set()
    if focal_decision and as_str(focal_decision.get("status")) == "approved":
        approved_selected_ids = set(
            as_str(item) for item in focal_decision.get("target_direction_ids", []) if as_str(item)
        ) if isinstance(focal_decision.get("target_direction_ids"), list) else set()

    updated: list[dict[str, Any]] = []
    for direction in review_directions:
        copied = dict(direction)
        direction_id = as_str(direction.get("id"))
        copied["selected"] = direction_id == recommended_id or direction_id in approved_selected_ids
        updated.append(copied)
    return updated


def build_decision(ofdd: dict[str, Any], focal_decision: dict[str, Any] | None, recommendation: dict[str, Any], review_directions: list[dict[str, Any]]) -> dict[str, Any]:
    """把上游 Decision 映射成 Review 单个决策对象。"""
    if focal_decision is None:
        return {
            "id": "N/A",
            "title": "本次尚未形成正式决定",
            "status": "待决策",
            "selected": "无",
            "rejected": "无",
            "deferred": "无",
            "decisionMaker": "待补",
            "decidedAt": "待补",
            "scope": as_str(ofdd.get("document_meta", {}).get("scope"), "待补"),
            "rationale": as_str(recommendation.get("rationale"), "待补"),
            "reconsiderWhen": "待补",
        }

    decision_status = as_str(focal_decision.get("status"), "proposed")
    decision_action = as_str(focal_decision.get("action"), "select")
    target_ids = [as_str(item) for item in focal_decision.get("target_direction_ids", []) if as_str(item)] if isinstance(focal_decision.get("target_direction_ids"), list) else []
    selected = "、".join(target_ids) or "无"
    rejected = "无"
    deferred = "无"

    if decision_action == "defer":
        deferred = selected
        selected = "无"
    elif decision_action in {"reject", "revoke"}:
        rejected = selected
        selected = "无"

    title = as_str(focal_decision.get("decision_action"), "本次尚未形成正式决定")
    if decision_status == "proposed":
        title = f"拟议：{title}" if title else "本次尚未形成正式决定"
    elif decision_status == "approved":
        title = f"已拍板：{title}" if title else "已拍板"

    reevaluation_conditions = focal_decision.get("reevaluation_conditions", []) if isinstance(focal_decision.get("reevaluation_conditions"), list) else []
    rationale_parts: list[str] = []
    for basis_id in focal_decision.get("basis_ids", []) if isinstance(focal_decision.get("basis_ids"), list) else []:
        rationale_parts.append(as_str(basis_id))
    rationale = as_str(focal_decision.get("decision_action")) or as_str(recommendation.get("rationale"), "待补")
    if rationale_parts:
        rationale = join_non_empty([rationale, "依据：" + "、".join(rationale_parts)])

    return {
        "id": as_str(focal_decision.get("id"), "N/A"),
        "title": title,
        "status": normalize_decision_status(decision_status),
        "selected": selected,
        "rejected": rejected,
        "deferred": deferred,
        "decisionMaker": as_str(focal_decision.get("decision_maker"), "待补"),
        "decidedAt": as_str(focal_decision.get("decision_date"), "待补"),
        "scope": as_str(focal_decision.get("scope"), as_str(ofdd.get("document_meta", {}).get("scope"), "待补")),
        "rationale": rationale,
        "reconsiderWhen": "；".join([as_str(item) for item in reevaluation_conditions if as_str(item)]) or "待补",
    }


def build_unresolved(ofdd: dict[str, Any], focal_decision: dict[str, Any] | None) -> list[dict[str, Any]]:
    """汇总阻塞问题和证据完整性问题。"""
    findings = ofdd.get("findings", {}) if isinstance(ofdd.get("findings"), dict) else {}
    questions = findings.get("questions", []) if isinstance(findings.get("questions"), list) else []
    review_gate = ofdd.get("review_gate", {}) if isinstance(ofdd.get("review_gate"), dict) else {}
    evidence_issues = review_gate.get("evidence_issues", []) if isinstance(review_gate.get("evidence_issues"), list) else []
    unresolved: list[dict[str, Any]] = []

    for question in questions:
        if not question.get("blocking"):
            continue
        blocking_targets = question.get("blocking_targets", []) if isinstance(question.get("blocking_targets"), list) else []
        unresolved.append({
            "id": as_str(question.get("id"), "F-Q-N/A"),
            "issue": as_str(question.get("question"), "待补问题"),
            "blocking": "、".join([as_str(item) for item in blocking_targets if as_str(item)]) or "decision",
            "owner": as_str(question.get("owner"), "待补"),
            "due": "待确认",
        })

    for issue in evidence_issues:
        unresolved.append({
            "id": as_str(issue.get("target_id"), "E-N/A"),
            "issue": as_str(issue.get("message"), "证据完整性待核验"),
            "blocking": as_str(issue.get("type"), "evidence"),
            "owner": "待补",
            "due": "待确认",
        })

    decisions = ofdd.get("decisions", []) if isinstance(ofdd.get("decisions"), list) else []
    if len(decisions) > 1:
        focal_id = as_str(focal_decision.get("id")) if focal_decision else "N/A"
        other_ids = [as_str(item.get("id")) for item in decisions if as_str(item.get("id")) and as_str(item.get("id")) != focal_id]
        unresolved.append({
            "id": "DEC-MULTI",
            "issue": f"上游存在多个 Decision；当前焦点为 {focal_id or 'N/A'}，其余决定需继续跟踪：{'、'.join(other_ids) or '待补'}。",
            "blocking": "decision",
            "owner": "待补",
            "due": "待确认",
        })

    return unresolved


def build_writeback(ofdd: dict[str, Any], unresolved: list[dict[str, Any]], focal_decision: dict[str, Any] | None) -> list[dict[str, Any]]:
    """给出本轮 Review 建议回写 OFDD 的内容。"""
    writeback: list[dict[str, Any]] = []

    blocking_items = [item for item in unresolved if item.get("blocking")]
    evidence_items = [item for item in unresolved if as_str(item.get("blocking")) in {"needs_anchor", "needs_locator", "drifted", "evidence"}]
    decisions = ofdd.get("decisions", []) if isinstance(ofdd.get("decisions"), list) else []

    if blocking_items:
        writeback.append({
            "title": "回写阻塞问题",
            "detail": "将本轮阻塞性问题与责任人状态回写 OFDD Review Gate，避免后续 Review 误判为可执行。",
            "complete": False,
        })

    if evidence_items:
        writeback.append({
            "title": "补充证据定位",
            "detail": "为证据完整性问题补齐稳定锚点、定位或重新核验结果。",
            "complete": False,
        })

    if focal_decision is None:
        writeback.append({
            "title": "确认焦点 Decision",
            "detail": "当前上游存在多个或未收敛的 Decision，需要先明确本次 Review 的焦点决定，再继续下游渲染。",
            "complete": False,
        })

    if len(decisions) > 1:
        writeback.append({
            "title": "补记其他 Decision 跟踪状态",
            "detail": "本次 Review 只展示一个焦点 Decision，其余 Decision 的状态、阻塞问题和重评条件也应继续回写维护。",
            "complete": False,
        })

    if not writeback:
        writeback.append({
            "title": "更新 Review 结论",
            "detail": "如有新的判断、方向或决策变化，请回写 OFDD 并重新生成 Review。",
            "complete": False,
        })

    return writeback


def validate_review_view(data: dict[str, Any]) -> list[str]:
    """在写出前做最小结构校验。"""
    missing = [field for field in REQUIRED_TOP_LEVEL if field not in data]
    if missing:
        raise ValueError(f"缺少顶层字段：{', '.join(missing)}")

    warnings: list[str] = []
    if not data.get("reasoningChains"):
        warnings.append("没有判断链，页面将缺少 Judgment → Evidence 追溯主体。")
    if len(data.get("directions", [])) < 2:
        warnings.append("候选方向少于两个，应确认是否存在可比较的替代方向。")
    if as_str(data.get("decision", {}).get("status")) == "已拍板" and as_str(data.get("decision", {}).get("decisionMaker")) == "待补":
        warnings.append("决定标记为已拍板，但决策人仍待补。")
    return warnings


def build_review_view(ofdd: dict[str, Any], review_date: str, review_id: str, focus_decision_id: str | None) -> dict[str, Any]:
    """把 OFDD 数据组装成 Review View JSON。"""
    source_index = build_source_index(ofdd)
    evidence_index = build_evidence_index(ofdd)
    review_gate = ofdd.get("review_gate", {}) if isinstance(ofdd.get("review_gate"), dict) else {}

    focal_decision = choose_focal_decision(ofdd, focus_decision_id)
    unresolved = build_unresolved(ofdd, focal_decision)
    meta = build_meta(ofdd, review_date, review_id)
    objective = build_objective(ofdd, review_gate)
    reasoning_chains = build_reasoning_chains(ofdd, source_index, evidence_index)
    questions = build_questions(ofdd)
    directions = build_directions(ofdd)
    recommendation = build_recommendation(ofdd, directions, focal_decision, unresolved)
    directions = apply_direction_selection(directions, recommendation, focal_decision)
    decision = build_decision(ofdd, focal_decision, recommendation, directions)
    summary = build_summary(ofdd, review_gate, unresolved)
    writeback = build_writeback(ofdd, unresolved, focal_decision)

    review_view = {
        "meta": meta,
        "objective": objective,
        "summary": summary,
        "reasoningChains": reasoning_chains,
        "questions": questions,
        "directions": directions,
        "recommendation": recommendation,
        "decision": decision,
        "unresolved": unresolved,
        "writeback": writeback,
    }

    validate_review_view(review_view)
    return review_view


def main() -> int:
    """命令行入口。"""
    args = parse_args()
    try:
        ofdd = load_json(args.input)
        # 记录输入来源，方便生成 Review 时回溯。
        ofdd["_source_file"] = str(args.input)
        review_date = args.date or date.today().isoformat()
        review_id = args.review_id or f"REV-{review_date.replace('-', '')}-01"
        review_view = build_review_view(ofdd, review_date, review_id, args.focus_decision_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(review_view, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 1

    print(f"已生成：{args.output}")
    print(f"Review ID：{review_view['meta']['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
