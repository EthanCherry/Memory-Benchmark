#!/usr/bin/env python3
"""Benchmark runner for LarkMemory evaluation.

Supports both formats:
- Legacy JSONL (.jsonl): one JSON case per line
- MemScope-style JSON (.json): metadata header + test_cases array

Usage:
    python scripts/run_benchmark.py --all
    python scripts/run_benchmark.py --dataset datasets/decision_memory.json
    python scripts/run_benchmark.py --dataset datasets/command_memory.jsonl
    python scripts/run_benchmark.py --all --test-type anti_interference
    python scripts/run_benchmark.py --all --output reports/eval.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"


def is_jsonl_file(filepath: Path) -> bool:
    return filepath.suffix == ".jsonl"


def load_cases(dataset_path: Path, test_type_filter: str = None):
    """Load cases from a dataset file. Supports both JSONL and JSON formats."""
    cases = []
    if is_jsonl_file(dataset_path):
        with open(dataset_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    case = json.loads(line)
                    if test_type_filter and case.get("test_type") != test_type_filter:
                        continue
                    cases.append(case)
    else:
        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)
        raw_cases = data.get("test_cases", [])
        for case in raw_cases:
            if test_type_filter and case.get("test_type") != test_type_filter:
                continue
            cases.append(case)
    return cases


def get_case_id(case):
    return case.get("test_id") or case.get("case_id", "?")


def get_input_events(case):
    """Get input events from a case (supports both new and legacy formats)."""
    # New format: setup.messages
    setup = case.get("setup", {})
    if setup and "messages" in setup:
        return setup["messages"]
    # Legacy format: input_events
    return case.get("input_events", [])


def get_query(case):
    """Get the query from a case (supports both formats)."""
    return case.get("query", "")


def ingest_events(events):
    """Send events to Memory Engine for ingestion. TODO: implement."""
    print(f"  [mock] Ingested {len(events)} events")
    return True


def retrieve_memory(query):
    """Query Memory Engine for relevant memories. TODO: implement."""
    query_str = query if isinstance(query, str) else json.dumps(query, ensure_ascii=False)
    print(f"  [mock] Retrieved memories for: {query_str[:50]}...")
    return []


def score_case(case, retrieved):
    """Score a single case. TODO: implement with actual metrics."""
    results = {}
    for metric in case.get("metrics", []):
        results[metric] = 0.0  # placeholder
    return results


def run_benchmark(cases, direction_name: str):
    results = {"direction": direction_name, "total": len(cases), "cases": []}

    for case in cases:
        case_result = {
            "case_id": get_case_id(case),
            "test_type": case.get("test_type", ""),
            "difficulty": case.get("difficulty", ""),
            "scenario": case.get("scenario", "") or case.get("name", ""),
            "passed": False,
            "scores": {},
        }

        try:
            input_events = get_input_events(case)
            ingest_events(input_events)
            query = get_query(case)
            retrieved = retrieve_memory(query)
            scores = score_case(case, retrieved)
            case_result["scores"] = scores
            case_result["passed"] = all(v >= 0.8 for v in scores.values()) if scores else False
        except Exception as e:
            case_result["error"] = str(e)

        results["cases"].append(case_result)

    return results


def main():
    parser = argparse.ArgumentParser(description="LarkMemory Benchmark Runner")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--dataset", type=str, help="Run a specific dataset file (.jsonl or .json)")
    parser.add_argument("--test-type", type=str, help="Filter by test_type")
    parser.add_argument("--output", type=str, help="Output JSON report path")
    args = parser.parse_args()

    if not args.all and not args.dataset:
        parser.error("Specify --all or --dataset")

    if args.all:
        files = sorted(DATASETS_DIR.glob("*.jsonl")) + sorted(DATASETS_DIR.glob("*.json"))
    else:
        files = [Path(args.dataset)]

    all_results = []
    for filepath in files:
        print(f"\n{'=' * 60}")
        print(f"Running: {filepath.name}")
        print(f"{'=' * 60}")

        cases = load_cases(filepath, args.test_type)
        print(f"Loaded {len(cases)} cases" + (f" (filtered: {args.test_type})" if args.test_type else ""))

        direction_name = filepath.stem
        result = run_benchmark(cases, direction_name)
        all_results.append(result)

        passed = sum(1 for c in result["cases"] if c["passed"])
        print(f"Result: {passed}/{result['total']} passed")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "v1.0",
            "test_type_filter": args.test_type,
            "results": all_results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to {output_path}")

    print("\n⚠️  NOTE: This is a mock runner. Implement ingest_events() and retrieve_memory() to run actual evaluation.")


if __name__ == "__main__":
    main()
