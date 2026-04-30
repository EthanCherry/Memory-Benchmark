#!/usr/bin/env python3
"""
validate_schema.py — LarkMemory Benchmark Schema Validator

验证 datasets/ 目录下所有 JSONL 文件是否符合 schema.json 规范。

Usage:
    python scripts/validate_schema.py
    python scripts/validate_schema.py --dataset datasets/decision_memory.jsonl
    python scripts/validate_schema.py --dir datasets/
"""

import json
import sys
import argparse
from pathlib import Path

VALID_CATEGORIES = {
    "anti_interference",
    "contradiction_update",
    "efficiency",
    "command_memory",
    "decision_memory",
    "preference_memory",
    "knowledge_health",
    "long_term_memory",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

VALID_SOURCES = {
    "cli",
    "feishu_group",
    "feishu_doc",
    "feishu_task",
    "feishu_meeting",
    "feishu_chat",
}

VALID_METRICS = {
    "recall_at_1", "recall_at_3", "keyword_match", "evidence_match",
    "should_not_contain_match", "latest_value_accuracy", "old_value_suppression",
    "noise_robustness", "top1_hit", "command_exact_match", "char_saving_rate",
    "step_saving_rate", "decision_match", "reason_match", "rejected_option_match",
    "preference_match", "condition_match", "conflict_resolution_accuracy",
    "freshness_accuracy", "expired_memory_suppression", "reminder_timing_accuracy",
    "long_term_recall",
}


def validate_case(case: dict, file_path: str, line_num: int) -> list[str]:
    """Validate a single benchmark case. Returns list of error messages."""
    errors = []
    prefix = f"[{file_path}:{line_num}] case_id={case.get('case_id', 'UNKNOWN')}"

    # Required top-level fields
    required_fields = ["case_id", "category", "scenario", "difficulty",
                       "input_events", "query", "expected", "metrics"]
    for field in required_fields:
        if field not in case:
            errors.append(f"{prefix}: Missing required field '{field}'")

    if errors:
        return errors  # Stop early if missing required fields

    # Validate case_id format
    if not isinstance(case["case_id"], str) or "_" not in case["case_id"]:
        errors.append(f"{prefix}: case_id should be format 'category_NNN'")

    # Validate category
    if case["category"] not in VALID_CATEGORIES:
        errors.append(f"{prefix}: Invalid category '{case['category']}'. Must be one of {VALID_CATEGORIES}")

    # Validate difficulty
    if case["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(f"{prefix}: Invalid difficulty '{case['difficulty']}'. Must be easy/medium/hard")

    # Validate input_events
    if not isinstance(case["input_events"], list) or len(case["input_events"]) == 0:
        errors.append(f"{prefix}: input_events must be a non-empty array")
    else:
        for i, event in enumerate(case["input_events"]):
            evt_prefix = f"{prefix} event[{i}]"
            for ef in ["event_id", "timestamp", "source", "content"]:
                if ef not in event:
                    errors.append(f"{evt_prefix}: Missing required field '{ef}'")
            if "source" in event and event["source"] not in VALID_SOURCES:
                errors.append(f"{evt_prefix}: Invalid source '{event['source']}'")

    # Validate query
    if not isinstance(case["query"], str) or len(case["query"].strip()) == 0:
        errors.append(f"{prefix}: query must be a non-empty string")

    # Validate expected
    expected = case["expected"]
    if "should_retrieve" not in expected:
        errors.append(f"{prefix}: expected.should_retrieve is required")
    if "answer_keywords" not in expected or not isinstance(expected["answer_keywords"], list):
        errors.append(f"{prefix}: expected.answer_keywords must be an array")

    # Validate metrics
    if not isinstance(case["metrics"], list) or len(case["metrics"]) == 0:
        errors.append(f"{prefix}: metrics must be a non-empty array")
    else:
        for metric in case["metrics"]:
            if metric not in VALID_METRICS:
                errors.append(f"{prefix}: Unknown metric '{metric}'")

    return errors


def validate_file(file_path: Path) -> tuple[int, int, list[str]]:
    """Validate all cases in a JSONL file. Returns (total, valid, errors)."""
    total = 0
    valid = 0
    all_errors = []
    case_ids = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"[{file_path}:{line_num}]: Invalid JSON: {e}")
                continue

            # Check for duplicate case_ids
            cid = case.get("case_id", "")
            if cid in case_ids:
                all_errors.append(f"[{file_path}:{line_num}]: Duplicate case_id '{cid}'")
            case_ids.add(cid)

            errors = validate_case(case, str(file_path), line_num)
            if errors:
                all_errors.extend(errors)
            else:
                valid += 1

    return total, valid, all_errors


def main():
    parser = argparse.ArgumentParser(description="Validate LarkMemory benchmark JSONL files")
    parser.add_argument("--dataset", help="Path to a single JSONL file")
    parser.add_argument("--dir", help="Path to directory containing JSONL files",
                        default="datasets/")
    args = parser.parse_args()

    files_to_validate = []

    if args.dataset:
        files_to_validate = [Path(args.dataset)]
    else:
        dataset_dir = Path(args.dir)
        if not dataset_dir.exists():
            print(f"❌ Directory not found: {dataset_dir}")
            sys.exit(1)
        files_to_validate = sorted(dataset_dir.glob("*.jsonl"))

    if not files_to_validate:
        print("⚠️  No JSONL files found.")
        sys.exit(0)

    total_cases = 0
    valid_cases = 0
    total_errors = []

    for file_path in files_to_validate:
        total, valid, errors = validate_file(file_path)
        total_cases += total
        valid_cases += valid
        total_errors.extend(errors)
        status = "✅" if not errors else "❌"
        print(f"{status} {file_path.name}: {valid}/{total} cases valid")

    print("\n" + "="*60)
    print(f"Total: {valid_cases}/{total_cases} cases passed validation")

    if total_errors:
        print(f"\n❌ {len(total_errors)} error(s) found:\n")
        for err in total_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ All cases are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
