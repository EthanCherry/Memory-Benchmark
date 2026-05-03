#!/usr/bin/env python3
"""Validate benchmark dataset files against schema.json, with extra semantic checks.

Supports both formats:
- Legacy JSONL (.jsonl): one JSON case per line, validated against v3 schema root
- MemScope-style JSON (.json): metadata header + test_cases array, validated against v4 schema
"""

import json
import sys
import jsonschema
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent

# Valid test_type per category
VALID_TEST_TYPES = {
    "command_memory": {"retrieval_recall", "anti_interference", "efficiency", "cross_project"},
    "decision_memory": {"retrieval_recall", "anti_interference", "contradiction_update", "efficiency", "long_term_retention", "abstention", "cross_project"},
    "preference_memory": {"retrieval_recall", "anti_interference", "contradiction_update", "efficiency", "abstention", "cross_project"},
    "knowledge_health": {"retrieval_recall", "anti_interference", "contradiction_update", "long_term_retention", "abstention"},
}

# Difficulty -> time_span_days ranges
DIFFICULTY_RANGES = {
    "easy": (0, 7),
    "medium": (8, 90),
    "hard": (91, 9999),
}


def load_schema_v4():
    with open(BASE_DIR / "schema.json") as f:
        return json.load(f)


def load_schema_v3():
    with open(BASE_DIR / "schema.v3.json") as f:
        return json.load(f)


def is_jsonl_file(filepath: Path) -> bool:
    return filepath.suffix == ".jsonl"


def read_cases_from_file(filepath: Path):
    """Read all cases from a dataset file. Returns list of (case, source_line) tuples."""
    cases = []
    if is_jsonl_file(filepath):
        with open(filepath) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line:
                    case = json.loads(line)
                    cases.append((case, i + 1))
    else:
        with open(filepath) as f:
            data = json.load(f)
        for i, case in enumerate(data.get("test_cases", [])):
            cases.append((case, i + 1))
    return cases


def get_case_field(case, field, legacy_field=None):
    if field in case:
        return case[field]
    if legacy_field and legacy_field in case:
        return case[legacy_field]
    return None


def get_input_events(case):
    setup = case.get("setup", {})
    if setup and "messages" in setup:
        return setup["messages"]
    return case.get("input_events", [])


def get_case_id(case):
    return case.get("test_id") or case.get("case_id", "?")


def semantic_checks(case, filepath, line_num):
    """Run semantic checks on a case. Supports both formats."""
    cid = get_case_id(case)
    input_events = get_input_events(case)
    expected = case.get("expected", {})

    # Support both v3 and v4 field names
    test_type = case.get("test_type", "")
    category = case.get("category", "")
    difficulty = case.get("difficulty", "")

    warnings = []

    time_span_days = case.get("time_span_days", 0)

    # Check test_type is valid for category
    if category and test_type:
        valid = VALID_TEST_TYPES.get(category, set())
        if test_type not in valid:
            raise ValueError(f"test_type '{test_type}' not valid for category '{category}'")

    # Check difficulty matches time_span_days
    if difficulty and difficulty in DIFFICULTY_RANGES:
        lo, hi = DIFFICULTY_RANGES[difficulty]
        if time_span_days < lo or time_span_days > hi:
            raise ValueError(f"time_span_days={time_span_days} does not match difficulty '{difficulty}' ({lo}-{hi})")

    # Check evidence_event_ids refer to valid events
    evid_ids = expected.get("evidence_event_ids", [])
    if input_events:
        valid_ids = {e.get("event_id", "") for e in input_events}
        for eid in evid_ids:
            if eid not in valid_ids:
                raise ValueError(f"evidence_event_id '{eid}' not found in input_events")

    # Check superseded_event_ids
    sup_ids = expected.get("superseded_event_ids", [])
    if input_events:
        valid_ids = {e.get("event_id", "") for e in input_events}
        for sid in sup_ids:
            if sid not in valid_ids:
                raise ValueError(f"superseded_event_id '{sid}' not found in input_events")

    # Abstention tests: should_retrieve should be false
    if test_type == "abstention" and expected.get("should_retrieve", True):
        raise ValueError("abstention test must have should_retrieve=false")

    if test_type == "abstention" and not expected.get("abstention_keywords"):
        warnings.append("abstention test missing abstention_keywords (recommended)")

    if test_type != "abstention" and not expected.get("answer_keywords"):
        raise ValueError("non-abstention test must have answer_keywords")

    # Cross-project tests: should have events from multiple projects
    if test_type == "cross_project" and input_events:
        projects = set()
        for e in input_events:
            ctx = e.get("context") or {}
            p = ctx.get("project", "")
            if p:
                projects.add(p)
        if len(projects) < 2:
            warnings.append(f"cross_project test has only {len(projects)} project(s), expected >=2")

    # Noise count checks
    if input_events:
        noise_count = sum(1 for e in input_events if e.get("event_id", "").startswith("noise_"))
        if difficulty == "hard" and noise_count < 20:
            warnings.append(f"hard difficulty with only {noise_count} noise events (recommended >=30)")

    if test_type == "contradiction_update" and not expected.get("latest_value"):
        warnings.append("contradiction_update missing latest_value")

    return warnings


def validate_file(filepath: Path, schema_v4, schema_v3):
    """Validate a single dataset file. Returns (passed, failed, warnings)."""
    is_legacy = is_jsonl_file(filepath)
    cases = read_cases_from_file(filepath)
    if not cases:
        print(f"  WARN: No cases found in {filepath.name}")
        return 0, 0, []

    file_passed = 0
    file_failed = 0
    all_warnings = []

    if is_legacy:
        # v3: validate each line (case) against schema_v3 root
        for case, line_num in cases:
            cid = get_case_id(case)
            try:
                jsonschema.validate(case, schema_v3)
                warnings = semantic_checks(case, filepath, line_num)
                for w in warnings:
                    all_warnings.append(f"[{cid}] {w}")
                file_passed += 1
            except jsonschema.ValidationError as e:
                file_failed += 1
                print(f"  FAIL [{filepath.name}] line {line_num} ({cid}): {e.message}")
            except ValueError as e:
                file_failed += 1
                print(f"  FAIL [{filepath.name}] line {line_num} ({cid}): {e}")
    else:
        # v4: validate the whole file against schema_v4
        with open(filepath) as f:
            data = json.load(f)
        try:
            jsonschema.validate(data, schema_v4)
        except jsonschema.ValidationError as e:
            print(f"  FAIL [{filepath.name}]: {e.message}")
            return 0, 1, []

        # Semantic checks case by case
        for case, idx in cases:
            cid = get_case_id(case)
            try:
                warnings = semantic_checks(case, filepath, idx)
                for w in warnings:
                    all_warnings.append(f"[{cid}] {w}")
                file_passed += 1
            except ValueError as e:
                file_failed += 1
                print(f"  FAIL [{filepath.name}] case {idx} ({cid}): {e}")

    status = "✅" if file_failed == 0 else "❌"
    total = file_passed + file_failed
    print(f"{status} {filepath.name}: {file_passed}/{total} passed")
    return file_passed, file_failed, all_warnings


def main():
    schema_v4 = load_schema_v4()
    schema_v3 = load_schema_v3()
    datasets_dir = BASE_DIR / "datasets"

    all_files = sorted(datasets_dir.glob("*.jsonl")) + sorted(datasets_dir.glob("*.json"))

    if not all_files:
        print("ERROR: No .jsonl or .json files found in datasets/")
        sys.exit(1)

    total = 0
    passed = 0
    failed = 0
    all_warnings = []

    for fpath in all_files:
        fpassed, ffailed, fwarnings = validate_file(fpath, schema_v4, schema_v3)
        total += fpassed + ffailed
        passed += fpassed
        failed += ffailed
        all_warnings.extend(fwarnings)

    if all_warnings:
        print(f"\n⚠️  {len(all_warnings)} warning(s):")
        for w in all_warnings:
            print(f"  WARN: {w}")

    print(f"\nTotal: {passed}/{total} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
