#!/usr/bin/env python3
"""
generate_cases.py — LarkMemory Benchmark Case Generator

使用大模型（Qwen30B / OpenAI API 兼容接口）批量生成 benchmark 用例，
从 v0 种子样例扩展到 v1 正式数据集（每类 30 条）。

Usage:
    python scripts/generate_cases.py --category decision_memory --count 25
    python scripts/generate_cases.py --all --count 25
    python scripts/generate_cases.py --validate-only

Environment Variables:
    LLM_BASE_URL    LLM API 基础地址（如 Qwen30B 部署地址）
    LLM_API_KEY     API 密钥
    LLM_MODEL       模型名称（默认 qwen-30b）
"""

import json
import sys
import os
import argparse
import time
from pathlib import Path

# ─── Configuration ─────────────────────────────────────────────────────────────

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-30b")

DATASETS_DIR = Path(__file__).parent.parent / "datasets"

CATEGORY_PROMPTS = {
    "decision_memory": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【飞书项目决策记忆】生成 {count} 条评测用例。

要求：
1. 每条用例必须包含 case_id、category、scenario、difficulty、input_events、query、expected、metrics。
2. case_id 格式：decision_0XX（从 {start_id:03d} 开始编号）。
3. input_events 要模拟真实飞书群聊或飞书文档讨论，source 只允许：feishu_group 或 feishu_doc。
4. 每条必须包含一个明确的项目决策、一个决策理由、一个被否定方案。
5. query 不能直接复述原句，要模拟用户后续自然追问。
6. expected 中必须包含 should_retrieve=true, memory_type="decision", answer_keywords（数组）, evidence_event_ids（数组）。
7. metrics 必须包含：["decision_match", "reason_match", "rejected_option_match", "evidence_match"]。
8. difficulty 在 easy/medium/hard 中分配，比例约 3:5:2。
9. 不同样例使用不同的项目名、公司名、人名，禁止跨样例复用实体。
10. 所有内容使用中文。
11. 输出纯 JSON 数组，不要输出解释文字、markdown 代码块标记或其他内容。
""",

    "anti_interference": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【抗干扰测试】生成 {count} 条评测用例。

要求：
1. case_id 格式：anti_0XX（从 {start_id:03d} 开始编号）。
2. 每条用例的结构：1条关键记忆事件 + N条无关噪声事件 + 查询。
3. easy 难度：噪声 3~5 条；medium 难度：噪声 10~20 条；hard 难度：噪声 30~50 条（可简写为3条并注明"[实际测试中扩展到50条]"）。
4. input_events 中噪声事件的 event_id 以 noise_ 开头（如 noise_1, noise_2）。
5. expected 必须包含 should_retrieve=true, answer_keywords, should_not_contain（可为空数组）, evidence_event_ids（只包含关键记忆的event_id）。
6. metrics 必须包含：["recall_at_3", "keyword_match", "noise_robustness", "evidence_match"]。
7. 不同样例使用不同场景（客户偏好、技术选型、项目规范、人员分工等）。
8. 所有内容使用中文。
9. 输出纯 JSON 数组，不要输出解释文字。
""",

    "contradiction_update": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【矛盾信息更新测试】生成 {count} 条评测用例。

要求：
1. case_id 格式：conflict_0XX（从 {start_id:03d} 开始编号）。
2. 每条必须有至少2个事件：旧指令（e1）+ 新的覆盖指令（e2），时间戳 e2 必须晚于 e1。
3. expected 中必须包含：latest_value（字符串）、should_not_contain（包含旧值的关键词）、superseded_event_ids: ["e1"]、evidence_event_ids: ["e2"]。
4. metrics 必须包含：["latest_value_accuracy", "old_value_suppression", "evidence_match"]。
5. 涵盖不同类型矛盾：直接覆盖、参数更新、方案推翻、撤回取消、截止日期变更等。
6. 所有内容使用中文。
7. 输出纯 JSON 数组，不要输出解释文字。
""",

    "preference_memory": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【个人工作习惯偏好记忆】生成 {count} 条评测用例。

要求：
1. case_id 格式：preference_0XX（从 {start_id:03d} 开始编号）。
2. 覆盖：显式偏好声明、隐式行为推断（3次以上相同行为）、周期性提醒、偏好更新。
3. expected 中包含：memory_type="preference"、answer_keywords、should_not_contain（旧偏好）。
4. metrics 包含：["preference_match", "condition_match", "old_value_suppression"]。
5. 使用不同场景：输出格式偏好、报告接收人偏好、工具使用偏好、工作时间安排等。
6. 所有内容使用中文。
7. 输出纯 JSON 数组，不要输出解释文字。
""",

    "command_memory": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【CLI 高频命令与工作流记忆】生成 {count} 条评测用例。

要求：
1. case_id 格式：command_0XX（从 {start_id:03d} 开始编号）。
2. input_events 的 source 必须是 "cli"，context 中包含 cwd（工作目录）和 project。
3. 同一case中同一命令至少出现 2~3 次，模拟高频使用。
4. query 格式："当前目录 {cwd}，用户输入前缀 {prefix}"。
5. expected 中包含：suggested_command（完整命令）、baseline_chars（完整命令字符数）、actual_chars（前缀字符数）、min_saving_rate（≥0.7）。
6. metrics 包含：["top1_hit", "command_exact_match", "char_saving_rate"]。
7. 使用不同类型命令：pytest、git、docker、python、npm、uvicorn 等。
8. 所有内容使用中文说明，命令本身使用英文。
9. 输出纯 JSON 数组，不要输出解释文字。
""",

    "knowledge_health": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【团队知识健康与遗忘预警】生成 {count} 条评测用例。

要求：
1. case_id 格式：knowledge_0XX（从 {start_id:03d} 开始编号）。
2. 覆盖：API Key/Token过期更新、架构文档版本迭代、安全规范定期复习提醒、知识缺口检测。
3. expected 中包含：latest_value（最新有效知识）、should_not_contain（旧版本/已废弃内容）、evidence_event_ids。
4. 时间戳需体现"知识老化"：e1 较早，e2 较晚（覆盖或废弃 e1）。
5. metrics 包含：["latest_value_accuracy", "expired_memory_suppression", "evidence_match"]。
6. 所有内容使用中文。
7. 输出纯 JSON 数组，不要输出解释文字。
""",

    "long_term_memory": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【长时序记忆保持】生成 {count} 条评测用例（跨越3个月到2年的场景）。

要求：
1. case_id 格式：longterm_0XX（从 {start_id:03d} 开始编号）。
2. 关键记忆事件 e1 的时间戳至少比 query 时间早 3 个月，hard 难度至少早 1 年。
3. e1 和 query 之间插入若干噪声事件（noise_1、noise_2...），时间分散。
4. 跨越的场景：年初制定的规范、季度约定、半年前签订的合同条款、长期技术决策。
5. metrics 包含：["recall_at_3", "long_term_recall", "keyword_match", "evidence_match"]。
6. 所有内容使用中文。
7. 输出纯 JSON 数组，不要输出解释文字。
""",

    "efficiency": """
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【效能指标验证】生成 {count} 条评测用例。

要求：
1. case_id 格式：efficiency_0XX（从 {start_id:03d} 开始编号）。
2. 每条需要体现"有记忆"vs"无记忆"的效率对比。
3. CLI类：包含 baseline_chars（完整输入字符数）和 actual_chars（使用记忆后用户需输入字符数）。
4. 决策/知识召回类：体现节省"重新沟通确认"的时间成本，用 step_saving_rate 指标。
5. min_saving_rate ≥ 0.5。
6. metrics 包含：["char_saving_rate", "step_saving_rate"] 或 ["char_saving_rate", "top1_hit"]。
7. 所有内容使用中文。
8. 输出纯 JSON 数组，不要输出解释文字。
""",
}


def call_llm(prompt: str, max_retries: int = 3) -> str:
    """Call the LLM API and return the response text."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests not installed. Run: pip install requests")

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{LLM_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Attempt {attempt + 1} failed: {e}. Retrying...", file=sys.stderr)
                time.sleep(2 ** attempt)
            else:
                raise


def parse_json_from_response(text: str) -> list[dict]:
    """Extract JSON array from LLM response, stripping markdown fences."""
    text = text.strip()
    # Strip markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def count_existing_cases(jsonl_path: Path) -> int:
    """Count existing cases in a JSONL file."""
    if not jsonl_path.exists():
        return 0
    count = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def generate_for_category(category: str, target_total: int = 30) -> None:
    """Generate cases for a specific category up to target_total."""
    jsonl_path = DATASETS_DIR / f"{category}.jsonl"
    existing = count_existing_cases(jsonl_path)
    needed = target_total - existing

    if needed <= 0:
        print(f"✅ {category}: already has {existing} cases (target: {target_total})")
        return

    print(f"📝 {category}: {existing} existing, generating {needed} more...")

    prompt_template = CATEGORY_PROMPTS.get(category)
    if not prompt_template:
        print(f"❌ No prompt template for category: {category}")
        return

    prompt = prompt_template.format(count=needed, start_id=existing + 1)

    try:
        response_text = call_llm(prompt)
        new_cases = parse_json_from_response(response_text)
    except Exception as e:
        print(f"  ❌ LLM call failed: {e}")
        return

    # Append to JSONL file
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for case in new_cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"  ✅ Appended {len(new_cases)} cases to {jsonl_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Generate LarkMemory benchmark cases using LLM")
    parser.add_argument("--category", help="Specific category to generate for")
    parser.add_argument("--all", action="store_true", help="Generate for all categories")
    parser.add_argument("--count", type=int, default=30, help="Target total cases per category (default: 30)")
    parser.add_argument("--validate-only", action="store_true", help="Only show current case counts")
    args = parser.parse_args()

    categories = list(CATEGORY_PROMPTS.keys())

    if args.validate_only:
        print("Current case counts:")
        for cat in categories:
            path = DATASETS_DIR / f"{cat}.jsonl"
            count = count_existing_cases(path)
            status = "✅" if count >= args.count else f"⏳ ({count}/{args.count})"
            print(f"  {cat:<30} {count:>3} cases  {status}")
        return

    if not args.all and not args.category:
        parser.print_help()
        sys.exit(1)

    if args.all:
        for cat in categories:
            generate_for_category(cat, args.count)
    elif args.category:
        if args.category not in categories:
            print(f"❌ Unknown category: {args.category}. Valid: {categories}")
            sys.exit(1)
        generate_for_category(args.category, args.count)

    print("\n✅ Generation complete!")
    print("Run 'python scripts/validate_schema.py' to validate the generated cases.")


if __name__ == "__main__":
    main()
