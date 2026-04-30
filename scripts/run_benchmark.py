#!/usr/bin/env python3
"""Benchmark runner for LarkMemory evaluation.

Usage:
    python scripts/run_benchmark.py --all
    python scripts/run_benchmark.py --dataset datasets/decision_memory.jsonl
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


def load_cases(dataset_path: Path, test_type_filter: str = None):
    cases = []
    with open(dataset_path) as f:
        for line in f:
            line = line.strip()
            if line:
                case = json.loads(line)
                if test_type_filter and case.get("test_type") != test_type_filter:
                    continue
                cases.append(case)
    return cases


def ingest_events(events):
    """Send events to Memory Engine for ingestion. TODO: implement."""
    # POST to MEMORY_ENGINE_BASE_URL /api/v1/ingest
    # for event in events: ingest(event)
    print(f"  [mock] Ingested {len(events)} events")
    return True


def retrieve_memory(query):
    """Query Memory Engine for relevant memories. TODO: implement."""
    # POST to MEMORY_ENGINE_BASE_URL /api/v1/retrieve
    # return results
    print(f"  [mock] Retrieved memories for: {query[:50]}...")
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
            "case_id": case["case_id"],
            "test_type": case["test_type"],
            "difficulty": case["difficulty"],
            "scenario": case["scenario"],
            "passed": False,
            "scores": {},
        }

        try:
            ingest_events(case["input_events"])
            retrieved = retrieve_memory(case["query"])
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
    parser.add_argument("--dataset", type=str, help="Run a specific dataset file")
    parser.add_argument("--test-type", type=str, help="Filter by test_type")
    parser.add_argument("--output", type=str, help="Output JSON report path")
    args = parser.parse_args()

    if not args.all and not args.dataset:
        parser.error("Specify --all or --dataset")

    if args.all:
        jsonl_files = sorted(DATASETS_DIR.glob("*.jsonl"))
    else:
        jsonl_files = [Path(args.dataset)]

    all_results = []
    for jsonl_file in jsonl_files:
        print(f"\n{'='*60}")
        print(f"Running: {jsonl_file.name}")
        print(f"{'='*60}")

        cases = load_cases(jsonl_file, args.test_type)
        print(f"Loaded {len(cases)} cases" + (f" (filtered: {args.test_type})" if args.test_type else ""))

        direction_name = jsonl_file.stem
        result = run_benchmark(cases, direction_name)
        all_results.append(result)

        passed = sum(1 for c in result["cases"] if c["passed"])
        print(f"Result: {passed}/{result['total']} passed")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "v0.2",
            "test_type_filter": args.test_type,
            "results": all_results,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to {output_path}")

    print("\n⚠️  NOTE: This is a mock runner. Implement ingest_events() and retrieve_memory() to run actual evaluation.")


if __name__ == "__main__":
    main()
