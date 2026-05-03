#!/usr/bin/env python3
"""
Convert Memory-Benchmark JSONL files to MemScope-style conversational JSON format.

Changes:
- JSONL (one JSON per line) -> JSON array with metadata header
- input_events -> setup.messages (with role field for conversational style)
- query: string -> object {type, content, ...} (structured like MemScope)
- Add: name, description, priority, tags fields to each test case
- Metadata header: dataset_name, version, description, total_cases, difficulty_distribution
"""

import json
import os
from collections import defaultdict

# Priority mapping
DIFFICULTY_TO_PRIORITY = {
    "easy": "P0",
    "medium": "P1",
    "hard": "P2",
}

# Map test_type to tags
TEST_TYPE_TAG_MAP = {
    "retrieval_recall": ["recall"],
    "efficiency": ["efficiency"],
    "anti_interference": ["anti-interference", "noise"],
    "contradiction_update": ["contradiction", "update"],
    "long_term_retention": ["long-term", "retention"],
    "abstention": ["abstention", "safety"],
    "cross_project": ["cross-project", "isolation"],
}

# Map source to role (for events that come from CLI, feishu_group, etc.)
# For feishu_group/feishu_chat: use speaker as role
# For CLI: role is always "user" (command executor)
# For feishu_doc: role is "system" or speaker
# For feishu_task: role is "system"


def map_event_to_message(event):
    """Convert an input_event to a MemScope-style message."""
    timestamp = event.get("timestamp", "")
    source = event.get("source", "unknown")
    speaker = event.get("speaker", "user")
    content = event.get("content", "")
    context = event.get("context", {})
    event_id = event.get("event_id", "")

    # Determine role based on source
    if source == "cli":
        role = "user"
    elif source in ("feishu_group", "feishu_chat"):
        role_map = {
            "user": "user",
            "assistant": "assistant",
            "系统": "system",
        }
        role = role_map.get(speaker.lower(), speaker)
    elif source == "feishu_doc":
        role = "system"
    elif source == "feishu_task":
        role = "system"
    elif source == "feishu_meeting":
        role = speaker if speaker != "user" else "participant"
    else:
        role = speaker if speaker != "user" else "user"

    msg = {
        "role": role,
        "content": content,
        "timestamp": timestamp,
    }

    # Preserve event_id so evidence_event_ids can still reference it
    if event_id:
        msg["event_id"] = event_id

    # Add context as metadata (not in MemScope original, but useful)
    if context:
        msg["context"] = context

    return msg


def convert_query(old_query, test_type, case_id):
    """Convert query from string to structured object like MemScope."""
    if not old_query or not old_query.strip():
        return {"type": "unknown", "content": old_query or ""}

    # Infer query type from test_type
    type_map = {
        "retrieval_recall": "search",
        "efficiency": "recommendation",
        "anti_interference": "search",
        "contradiction_update": "search",
        "long_term_retention": "search",
        "abstention": "search",
        "cross_project": "search",
    }

    query_type = type_map.get(test_type, "search")

    return {
        "type": query_type,
        "content": old_query.strip(),
    }


def convert_case(old_case):
    """Convert a single test case from old JSONL format to new JSON format."""
    case_id = old_case.get("case_id", "")
    category = old_case.get("category", "")
    test_type = old_case.get("test_type", "")
    scenario = old_case.get("scenario", "")
    difficulty = old_case.get("difficulty", "medium")
    time_span_days = old_case.get("time_span_days", 0)
    input_events = old_case.get("input_events", [])
    query = old_case.get("query", "")
    expected = old_case.get("expected", {})
    metrics = old_case.get("metrics", [])

    # Build setup object with messages (conversational style)
    messages = [map_event_to_message(e) for e in input_events]

    setup = {
        "messages": messages,
    }

    # Add metadata to setup if present in first event's context
    if input_events:
        first_context = input_events[0].get("context", {})
        if first_context:
            setup["context"] = first_context

    # Build new case
    new_case = {
        "test_id": case_id,
        "name": scenario,
        "test_type": test_type,
        "description": _build_description(old_case),
        "setup": setup,
        "query": convert_query(query, test_type, case_id),
        "expected": expected,
        "difficulty": difficulty,
        "priority": DIFFICULTY_TO_PRIORITY.get(difficulty, "P1"),
        "tags": _build_tags(old_case),
    }

    # Only include metrics if present
    if metrics:
        new_case["metrics"] = metrics

    # Include time_span_days for reference
    if time_span_days:
        new_case["time_span_days"] = time_span_days

    return new_case


def _build_description(case):
    """Build a description string for the test case."""
    scenario = case.get("scenario", "")
    test_type = case.get("test_type", "")
    difficulty = case.get("difficulty", "")
    input_events = case.get("input_events", [])
    noise_count = sum(1 for e in input_events if e.get("event_id", "").startswith("noise_"))

    desc_parts = [scenario]
    if noise_count > 0:
        desc_parts.append(f"包含{noise_count}条噪声事件")
    desc_parts.append(f"测试类型: {test_type}")
    desc_parts.append(f"难度: {difficulty}")

    return "；".join(desc_parts)


def _build_tags(case):
    """Build tags list from case metadata."""
    tags = []
    test_type = case.get("test_type", "")
    category = case.get("category", "")
    difficulty = case.get("difficulty", "")

    # Add test_type-based tags
    if test_type in TEST_TYPE_TAG_MAP:
        tags.extend(TEST_TYPE_TAG_MAP[test_type])

    # Add category tag
    tags.append(category.replace("_", "-"))

    # Add difficulty tag
    tags.append(difficulty)

    return tags


def _dataset_description(dataset_name):
    """Get description for a dataset."""
    desc_map = {
        "command_memory": "命令记忆能力评测：测试系统对用户历史命令的记录、频率统计、上下文关联、智能推荐、多跳推理、实体追踪和时序推理能力",
        "decision_memory": "决策记忆能力评测：测试系统对团队/用户决策的提取、存储、搜索、长时序回忆、多跳推理和实体追踪能力",
        "preference_memory": "偏好记忆能力评测：测试系统对用户工作习惯、偏好设置的记忆、更新和抗干扰能力",
        "knowledge_health": "知识健康度评测：测试系统对团队关键知识的追踪、过期检测、矛盾更新和遗忘预警能力",
    }
    return desc_map.get(dataset_name, f"{dataset_name} 测试用例集")


def process_file(input_path, output_path):
    """Process a single JSONL file and write JSON output."""
    cases = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                old_case = json.loads(line)
                new_case = convert_case(old_case)
                cases.append(new_case)
            except json.JSONDecodeError as e:
                print(f"  Warning: JSON decode error in {input_path}: {e}")
                continue

    # Build metadata header + test_cases array (MemScope style)
    difficulty_dist = defaultdict(int)
    for c in cases:
        difficulty_dist[c.get("difficulty", "unknown")] += 1

    # Infer dataset_name from filename
    basename = os.path.basename(input_path)
    dataset_name = basename.replace(".jsonl", "")

    output = {
        "dataset_name": dataset_name,
        "version": "3.0",
        "description": _dataset_description(dataset_name),
        "total_cases": len(cases),
        "difficulty_distribution": dict(difficulty_dist),
        "test_cases": cases,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Converted {len(cases)} cases: {input_path} -> {output_path}")
    return len(cases)


def main():
    # The scripts dir is one level down from repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    datasets_dir = os.path.join(repo_root, "datasets")

    files = [
        ("command_memory.jsonl", "command_memory.json"),
        ("decision_memory.jsonl", "decision_memory.json"),
        ("preference_memory.jsonl", "preference_memory.json"),
        ("knowledge_health.jsonl", "knowledge_health.json"),
    ]

    total = 0
    for input_file, output_file in files:
        input_path = os.path.join(datasets_dir, input_file)
        output_path = os.path.join(datasets_dir, output_file)
        if os.path.exists(input_path):
            count = process_file(input_path, output_path)
            total += count
        else:
            print(f"  Skipping {input_file} (not found)")

    print(f"\nTotal cases converted: {total}")
    print(f"Output directory: {datasets_dir}")


if __name__ == "__main__":
    main()
