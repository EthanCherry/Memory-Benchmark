#!/usr/bin/env python3
"""
run_benchmark.py — LarkMemory Benchmark Runner

对 Memory Engine 接口运行评测，计算各维度指标并输出报告。

Usage:
    python scripts/run_benchmark.py --all
    python scripts/run_benchmark.py --dataset datasets/decision_memory.jsonl
    python scripts/run_benchmark.py --all --output reports/eval_20260430.json
    python scripts/run_benchmark.py --all --report-format markdown

Environment Variables:
    MEMORY_ENGINE_BASE_URL  Memory Engine 服务地址（默认 http://localhost:8000）
    MEMORY_ENGINE_API_KEY   API 密钥（可选）
"""

import json
import sys
import argparse
import time
import datetime
from pathlib import Path
from typing import Any

# ─── Configuration ────────────────────────────────────────────────────────────

import os
BASE_URL = os.environ.get("MEMORY_ENGINE_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("MEMORY_ENGINE_API_KEY", "")

DATASETS_DIR = Path(__file__).parent.parent / "datasets"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

DATASET_WEIGHTS = {
    "anti_interference": 0.15,
    "contradiction_update": 0.15,
    "efficiency": 0.15,
    "command_memory": 0.10,
    "decision_memory": 0.15,
    "preference_memory": 0.15,
    "knowledge_health": 0.10,
    "long_term_memory": 0.05,
}

# ─── Memory Engine Client (stub — replace with real implementation) ────────────

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def ingest_events(events: list[dict]) -> dict:
    """Ingest a list of events into the Memory Engine.
    
    POST /api/v1/ingest
    Replace this stub with actual HTTP call to your Memory Engine.
    """
    if not HAS_REQUESTS:
        raise RuntimeError("requests library not installed. Run: pip install requests")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/ingest",
        json={"events": events},
        headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def retrieve_memory(query: str, top_k: int = 3) -> dict:
    """Retrieve relevant memories for a query.
    
    POST /api/v1/retrieve
    Replace this stub with actual HTTP call to your Memory Engine.
    """
    if not HAS_REQUESTS:
        raise RuntimeError("requests library not installed. Run: pip install requests")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/retrieve",
        json={"query": query, "top_k": top_k},
        headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def reset_memory_store() -> None:
    """Reset the memory store to a clean state between test cases.
    
    DELETE /api/v1/memories (or equivalent reset endpoint)
    Replace this stub with your actual reset logic.
    """
    if not HAS_REQUESTS:
        return
    try:
        requests.delete(
            f"{BASE_URL}/api/v1/memories",
            headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {},
            timeout=10,
        )
    except Exception:
        pass  # Best-effort reset


# ─── Metric Computation ────────────────────────────────────────────────────────

def compute_recall_at_k(result: dict, expected: dict, k: int) -> float:
    """Check if any evidence event_id appears in top-k retrieved memories."""
    evidence_ids = set(expected.get("evidence_event_ids", []))
    if not evidence_ids:
        return 1.0  # No evidence required, pass by default
    
    retrieved_ids = set()
    memories = result.get("memories", [])[:k]
    for mem in memories:
        for src_event in mem.get("source_events", []):
            retrieved_ids.add(src_event.get("event_id", ""))
    
    return 1.0 if evidence_ids & retrieved_ids else 0.0


def compute_keyword_match(result: dict, expected: dict) -> float:
    """Fraction of expected keywords found in response text."""
    keywords = expected.get("answer_keywords", [])
    if not keywords:
        return 1.0
    
    response_text = _get_response_text(result).lower()
    hits = sum(1 for kw in keywords if kw.lower() in response_text)
    return hits / len(keywords)


def compute_should_not_contain(result: dict, expected: dict) -> float:
    """Returns 1 if none of the forbidden terms appear in the response."""
    forbidden = expected.get("should_not_contain", [])
    if not forbidden:
        return 1.0
    
    response_text = _get_response_text(result).lower()
    violations = [term for term in forbidden if term.lower() in response_text]
    return 0.0 if violations else 1.0


def compute_latest_value_accuracy(result: dict, expected: dict) -> float:
    """Returns 1 if the latest_value appears in the response."""
    latest = expected.get("latest_value", "")
    if not latest:
        return 1.0
    return 1.0 if latest.lower() in _get_response_text(result).lower() else 0.0


def compute_old_value_suppression(result: dict, expected: dict) -> float:
    """Returns 1 if superseded content does NOT appear as active memory."""
    should_not = expected.get("should_not_contain", [])
    if not should_not:
        return 1.0
    response_text = _get_response_text(result).lower()
    violations = [term for term in should_not if term.lower() in response_text]
    return 0.0 if violations else 1.0


def compute_char_saving_rate(expected: dict) -> float:
    """Compute character saving rate from expected fields."""
    baseline = expected.get("baseline_chars")
    actual = expected.get("actual_chars")
    min_rate = expected.get("min_saving_rate", 0.6)
    if baseline is None or actual is None:
        return 1.0  # No char count specified, skip
    saving_rate = 1.0 - actual / baseline
    return 1.0 if saving_rate >= min_rate else saving_rate


def compute_top1_hit(result: dict, expected: dict) -> float:
    """Returns 1 if the first recommended command matches expected."""
    suggested = expected.get("suggested_command", "")
    if not suggested:
        return 1.0
    memories = result.get("memories", [])
    if not memories:
        return 0.0
    top1_content = memories[0].get("content", "").strip()
    return 1.0 if suggested.strip() == top1_content else 0.0


def compute_command_exact_match(result: dict, expected: dict) -> float:
    """Returns 1 if suggested_command appears exactly in any top-3 result."""
    suggested = expected.get("suggested_command", "")
    if not suggested:
        return 1.0
    response_text = _get_response_text(result)
    return 1.0 if suggested.strip() in response_text else 0.0


def compute_evidence_match(result: dict, expected: dict) -> float:
    """Returns 1 if at least one expected evidence event_id is in the result."""
    evidence_ids = set(expected.get("evidence_event_ids", []))
    if not evidence_ids:
        return 1.0
    result_text = json.dumps(result)
    hits = sum(1 for eid in evidence_ids if eid in result_text)
    return 1.0 if hits > 0 else 0.0


def _get_response_text(result: dict) -> str:
    """Extract the main text content from a retrieve result."""
    # Try common response fields — adapt to your actual API response structure
    if "answer" in result:
        return result["answer"]
    if "response" in result:
        return result["response"]
    memories = result.get("memories", [])
    texts = []
    for mem in memories[:3]:
        texts.append(mem.get("content", ""))
        texts.append(mem.get("summary", ""))
    return " ".join(texts)


# ─── Metric Dispatcher ─────────────────────────────────────────────────────────

METRIC_FUNCTIONS = {
    "recall_at_1": lambda r, e: compute_recall_at_k(r, e, 1),
    "recall_at_3": lambda r, e: compute_recall_at_k(r, e, 3),
    "keyword_match": compute_keyword_match,
    "evidence_match": compute_evidence_match,
    "should_not_contain_match": compute_should_not_contain,
    "latest_value_accuracy": compute_latest_value_accuracy,
    "old_value_suppression": compute_old_value_suppression,
    "noise_robustness": lambda r, e: compute_recall_at_k(r, e, 3),
    "top1_hit": compute_top1_hit,
    "command_exact_match": compute_command_exact_match,
    "char_saving_rate": lambda r, e: compute_char_saving_rate(e),
    "step_saving_rate": lambda r, e: 1.0,  # TODO: implement step counting
    "decision_match": compute_keyword_match,
    "reason_match": compute_keyword_match,
    "rejected_option_match": lambda r, e: compute_keyword_match(r, {
        "answer_keywords": [e.get("rejected_option", "")] if e.get("rejected_option") else []
    }),
    "preference_match": compute_keyword_match,
    "condition_match": lambda r, e: 1.0,  # TODO: implement condition checking
    "conflict_resolution_accuracy": compute_latest_value_accuracy,
    "freshness_accuracy": lambda r, e: 1.0,  # TODO: implement freshness checking
    "expired_memory_suppression": compute_old_value_suppression,
    "reminder_timing_accuracy": lambda r, e: 1.0,  # TODO: implement timing check
    "long_term_recall": lambda r, e: compute_recall_at_k(r, e, 3),
}


def evaluate_case(case: dict) -> dict:
    """Run a single benchmark case and return detailed results."""
    case_id = case["case_id"]
    result = {"case_id": case_id, "category": case["category"],
              "difficulty": case["difficulty"], "passed": False,
              "metric_scores": {}, "overall_score": 0.0, "error": None,
              "latency_ms": 0.0}

    start_time = time.time()
    try:
        # 1. Reset memory store
        reset_memory_store()

        # 2. Ingest events
        ingest_events(case["input_events"])

        # 3. Retrieve
        retrieve_result = retrieve_memory(case["query"], top_k=3)

        # 4. Compute metrics
        metric_scores = {}
        for metric in case["metrics"]:
            fn = METRIC_FUNCTIONS.get(metric)
            if fn:
                score = fn(retrieve_result, case["expected"])
            else:
                score = 0.0
                print(f"  ⚠️  Unknown metric: {metric}", file=sys.stderr)
            metric_scores[metric] = round(score, 4)

        overall = sum(metric_scores.values()) / len(metric_scores) if metric_scores else 0.0
        passed = overall >= 0.7  # A case passes if average metric score >= 0.7

        result.update({
            "passed": passed,
            "metric_scores": metric_scores,
            "overall_score": round(overall, 4),
            "latency_ms": round((time.time() - start_time) * 1000, 1),
        })

    except Exception as e:
        result["error"] = str(e)
        result["latency_ms"] = round((time.time() - start_time) * 1000, 1)

    return result


def run_dataset(jsonl_path: Path) -> dict:
    """Run all cases in a JSONL file and return aggregated results."""
    category = jsonl_path.stem
    case_results = []
    total = 0
    passed = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            total += 1
            print(f"  Running {case['case_id']}...", end=" ")
            result = evaluate_case(case)
            case_results.append(result)
            if result["passed"]:
                passed += 1
                print(f"✅ ({result['overall_score']:.2f})")
            else:
                print(f"❌ ({result['overall_score']:.2f}) {result.get('error', '')}")

    pass_rate = passed / total if total > 0 else 0.0
    avg_score = sum(r["overall_score"] for r in case_results) / total if total > 0 else 0.0

    return {
        "category": category,
        "total": total,
        "passed": passed,
        "pass_rate": round(pass_rate, 4),
        "avg_score": round(avg_score, 4),
        "weight": DATASET_WEIGHTS.get(category, 0.0),
        "cases": case_results,
    }


def generate_report(dataset_results: list[dict], output_path: Path | None = None) -> dict:
    """Aggregate all dataset results into a final report."""
    total_cases = sum(d["total"] for d in dataset_results)
    total_passed = sum(d["passed"] for d in dataset_results)
    pass_rate = total_passed / total_cases if total_cases > 0 else 0.0

    overall_score = sum(
        d["avg_score"] * d["weight"] for d in dataset_results
    ) * 100  # Scale to 100

    report = {
        "evaluation_id": f"eval-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.datetime.now().isoformat(),
        "system_base_url": BASE_URL,
        "total_cases": total_cases,
        "passed": total_passed,
        "failed": total_cases - total_passed,
        "pass_rate": f"{pass_rate:.1%}",
        "overall_score": round(overall_score, 1),
        "grade": "优秀" if overall_score >= 85 else ("良好" if overall_score >= 70 else "待改进"),
        "dimension_scores": {
            d["category"]: {
                "pass_rate": d["pass_rate"],
                "avg_score": d["avg_score"],
                "weight": d["weight"],
                "passed": d["passed"],
                "total": d["total"],
            }
            for d in dataset_results
        },
        "datasets": dataset_results,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Report saved to: {output_path}")

    return report


def print_summary(report: dict) -> None:
    """Print a human-readable summary to stdout."""
    print("\n" + "=" * 60)
    print("LarkMemory Benchmark Report")
    print("=" * 60)
    print(f"Evaluation ID : {report['evaluation_id']}")
    print(f"Total Cases   : {report['total_cases']}")
    print(f"Passed        : {report['passed']} ({report['pass_rate']})")
    print(f"Overall Score : {report['overall_score']}/100  [{report['grade']}]")
    print()
    print(f"{'Dataset':<30} {'Pass Rate':>10} {'Avg Score':>10} {'Weight':>8}")
    print("-" * 62)
    for cat, scores in report["dimension_scores"].items():
        print(f"{cat:<30} {scores['pass_rate']:>10.1%} {scores['avg_score']:>10.2f} {scores['weight']:>8.0%}")
    print("=" * 60)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run LarkMemory Benchmark")
    parser.add_argument("--all", action="store_true", help="Run all datasets in datasets/ dir")
    parser.add_argument("--dataset", help="Path to a single JSONL file")
    parser.add_argument("--output", help="Output JSON report path")
    parser.add_argument("--report-format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    if not args.all and not args.dataset:
        parser.print_help()
        sys.exit(1)

    files_to_run = []
    if args.all:
        files_to_run = sorted(DATASETS_DIR.glob("*.jsonl"))
    elif args.dataset:
        files_to_run = [Path(args.dataset)]

    if not files_to_run:
        print("❌ No JSONL files found.")
        sys.exit(1)

    dataset_results = []
    for f in files_to_run:
        print(f"\n📂 Running dataset: {f.name}")
        result = run_dataset(f)
        dataset_results.append(result)

    output_path = Path(args.output) if args.output else None
    report = generate_report(dataset_results, output_path)
    print_summary(report)


if __name__ == "__main__":
    main()
