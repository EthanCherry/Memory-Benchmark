#!/usr/bin/env python3
"""Generate benchmark cases using LLM (Qwen30B).

Usage:
    python scripts/generate_cases.py --direction command_memory --count 30
    python scripts/generate_cases.py --all --count 30
"""

import argparse
import json
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"

DIRECTIONS = {
    "command_memory": {
        "test_types": ["retrieval_recall", "efficiency", "anti_interference"],
        "source": "cli",
        "description": "CLI 高频命令与工作流记忆",
    },
    "decision_memory": {
        "test_types": ["retrieval_recall", "anti_interference", "contradiction_update", "efficiency", "long_term_retention"],
        "source": "feishu_group",
        "description": "飞书项目决策与上下文记忆",
    },
    "preference_memory": {
        "test_types": ["retrieval_recall", "anti_interference", "contradiction_update", "efficiency"],
        "source": "feishu_chat",
        "description": "个人工作习惯与偏好记忆",
    },
    "knowledge_health": {
        "test_types": ["retrieval_recall", "anti_interference", "contradiction_update", "long_term_retention"],
        "source": "feishu_doc",
        "description": "团队知识断层与遗忘预警",
    },
}

PROMPT_TEMPLATE = """你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【{description}】方向生成 {count} 条评测用例。
测试类型为：{test_type}

要求：
1. 每条用例必须包含 case_id, category, test_type, scenario, difficulty, time_span_days, input_events, query, expected, metrics
2. category 固定为 "{category}"
3. test_type 固定为 "{test_type}"
4. case_id 格式为 {prefix}_{NNN}（NNN 从 {start:03d} 开始）
5. input_events 要模拟真实企业协作场景
6. query 不能直接复述原句，要模拟自然追问
7. expected 中必须包含 should_retrieve, answer_keywords, evidence_event_ids
8. 输出 JSON 数组，不要输出解释文字
9. 所有内容使用中文（英文场景除外）
10. difficulty 分布：easy 30%, medium 50%, hard 20%
"""

def generate_via_llm(direction: str, test_type: str, count: int, start_id: int):
    """Call LLM to generate cases. TODO: implement with actual LLM call."""
    config = DIRECTIONS[direction]
    prefix = direction[:3] + "_" + test_type[:5]
    prompt = PROMPT_TEMPLATE.format(
        description=config["description"],
        count=count,
        test_type=test_type,
        category=direction,
        prefix=prefix,
        start=start_id,
    )

    print(f"  [mock] Would send prompt to LLM for {direction}/{test_type} × {count}")
    print(f"  Prompt preview: {prompt[:100]}...")

    # TODO: Actual LLM call
    # import requests
    # response = requests.post(f"{os.environ['LLM_BASE_URL']}/v1/chat/completions", ...)
    # return response.json()["choices"][0]["message"]["content"]

    return []


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark cases")
    parser.add_argument("--direction", type=str, help="Target direction")
    parser.add_argument("--all", action="store_true", help="Generate for all directions")
    parser.add_argument("--count", type=int, default=30, help="Cases per test_type per direction")
    parser.add_argument("--test-type", type=str, help="Generate for specific test_type only")
    args = parser.parse_args()

    if not args.all and not args.direction:
        parser.error("Specify --all or --direction")

    if args.all:
        directions = list(DIRECTIONS.keys())
    else:
        directions = [args.direction]

    for direction in directions:
        if direction not in DIRECTIONS:
            print(f"ERROR: Unknown direction '{direction}'")
            sys.exit(1)

        config = DIRECTIONS[direction]
        test_types = [args.test_type] if args.test_type else config["test_types"]

        print(f"\n{'='*60}")
        print(f"Direction: {direction} ({config['description']})")
        print(f"Test types: {test_types}")
        print(f"{'='*60}")

        all_cases = []
        for test_type in test_types:
            print(f"\nGenerating {args.count} cases for {direction}/{test_type}...")
            cases = generate_via_llm(direction, test_type, args.count, len(all_cases) + 1)
            all_cases.extend(cases)

        if all_cases:
            output_path = DATASETS_DIR / f"{direction}.jsonl"
            with open(output_path, "w") as f:
                for case in all_cases:
                    f.write(json.dumps(case, ensure_ascii=False) + "\n")
            print(f"\nSaved {len(all_cases)} cases to {output_path}")

    print("\n⚠️  NOTE: This is a mock generator. Set LLM_BASE_URL and implement generate_via_llm() for actual generation.")


if __name__ == "__main__":
    main()
