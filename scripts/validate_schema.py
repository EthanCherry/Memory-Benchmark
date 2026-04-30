#!/usr/bin/env python3
"""Validate all benchmark JSONL files against schema.json, with extra semantic checks."""

import json
import sys
import jsonschema
from pathlib import Path

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

def main():
    schema_path = BASE_DIR / "schema.json"
    datasets_dir = BASE_DIR / "datasets"

    with open(schema_path) as f:
        schema = json.load(f)

    total = 0
    passed = 0
    failed = 0
    warnings = []

    jsonl_files = sorted(datasets_dir.glob("*.jsonl"))
    if not jsonl_files:
        print("ERROR: No JSONL files found in datasets/")
        sys.exit(1)

    for jsonl_file in jsonl_files:
        cases = []
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    cases.append(json.loads(line))

        file_ok = 0
        for i, case in enumerate(cases):
            total += 1
            cid = case.get("case_id", f"?")
            try:
                # JSON schema validation
                jsonschema.validate(case, schema)

                # Semantic checks
                cat = case["category"]
                tt = case["test_type"]
                diff = case["difficulty"]
                tsd = case["time_span_days"]
                evts = case["input_events"]
                expected = case["expected"]

                # Check test_type is valid for category
                if tt not in VALID_TEST_TYPES.get(cat, set()):
                    raise ValueError(f"test_type '{tt}' not valid for category '{cat}'")

                # Check difficulty matches time_span_days
                lo, hi = DIFFICULTY_RANGES[diff]
                if tsd < lo or tsd > hi:
                    raise ValueError(f"time_span_days={tsd} does not match difficulty '{diff}' ({lo}-{hi})")

                # Check evidence_event_ids refer to valid events
                evid_ids = expected.get("evidence_event_ids", [])
                valid_ids = {e["event_id"] for e in evts}
                for eid in evid_ids:
                    if eid not in valid_ids:
                        raise ValueError(f"evidence_event_id '{eid}' not found in input_events")

                # Check superseded_event_ids
                sup_ids = expected.get("superseded_event_ids", [])
                for sid in sup_ids:
                    if sid not in valid_ids:
                        raise ValueError(f"superseded_event_id '{sid}' not found in input_events")

                # Abstention tests: should_retrieve should be false
                if tt == "abstention" and expected.get("should_retrieve", True):
                    raise ValueError("abstention test must have should_retrieve=false")

                # Abstention tests: should have abstention_keywords
                if tt == "abstention" and not expected.get("abstention_keywords"):
                    warnings.append(f"[{cid}] abstention test missing abstention_keywords (recommended)")

                # Non-abstention tests: should have answer_keywords
                if tt != "abstention" and not expected.get("answer_keywords"):
                    raise ValueError(f"non-abstention test must have answer_keywords")

                # Cross-project tests: should have events from multiple projects
                if tt == "cross_project":
                    projects = set()
                    for e in evts:
                        p = (e.get("context") or {}).get("project", "")
                        if p:
                            projects.add(p)
                    if len(projects) < 2:
                        warnings.append(f"[{cid}] cross_project test has only {len(projects)} project(s), expected ≥2")

                # Noise count checks
                noise_count = sum(1 for e in evts if e["event_id"].startswith("noise_"))
                signal_count = len(evts) - noise_count
                if diff == "hard" and noise_count < 20:
                    warnings.append(f"[{cid}] hard difficulty with only {noise_count} noise events (recommended ≥30)")

                # Contradiction update: should have latest_value
                if tt == "contradiction_update" and not expected.get("latest_value"):
                    warnings.append(f"[{cid}] contradiction_update missing latest_value")

                passed += 1
                file_ok += 1
            except jsonschema.ValidationError as e:
                failed += 1
                print(f"  FAIL [{jsonl_file.name}] case {i} ({cid}): {e.message}")
            except ValueError as e:
                failed += 1
                print(f"  FAIL [{jsonl_file.name}] case {i} ({cid}): {e}")

        status = "✅" if file_ok == len(cases) else "❌"
        print(f"{status} {jsonl_file.name}: {file_ok}/{len(cases)} passed")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN: {w}")

    print(f"\nTotal: {passed}/{total} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
