# LarkMemory Benchmark

> 飞书 OpenClaw 赛道 — 企业级长程协作 Memory 系统 评测数据集  
> **Benchmark Version**: v0.1 (mini, 40 cases)  
> **目标版本**: v1.0 (240 cases)

---

## 快速开始

### 1. 验证数据格式

```bash
python scripts/validate_schema.py
```

### 2. 运行 benchmark（需先启动 Memory Engine）

```bash
# 设置 Memory Engine 地址
export MEMORY_ENGINE_BASE_URL=http://localhost:8000

# 运行全量评测
python scripts/run_benchmark.py --all

# 运行单个数据集
python scripts/run_benchmark.py --dataset datasets/decision_memory.jsonl

# 输出 JSON 报告
python scripts/run_benchmark.py --all --output reports/eval_$(date +%Y%m%d).json
```

### 3. 扩展数据集到 v1（需 Qwen30B 或其他 LLM）

```bash
# 设置 LLM 服务地址
export LLM_BASE_URL=http://your-qwen-service:11434
export LLM_MODEL=qwen-30b

# 扩展所有类别到 30 条
python scripts/generate_cases.py --all --count 30

# 重新验证格式
python scripts/validate_schema.py
```

---

## 文件结构

```
benchmarks/
├── README.md                          # 本文件
├── schema.json                        # 数据格式 JSON Schema
├── datasets/                          # 评测数据集（JSONL格式）
│   ├── anti_interference.jsonl        # 抗干扰测试（5条 → 30条）
│   ├── contradiction_update.jsonl     # 矛盾更新测试（5条 → 30条）
│   ├── efficiency.jsonl               # 效能指标测试（5条 → 30条）
│   ├── command_memory.jsonl           # CLI命令记忆（5条 → 30条）
│   ├── decision_memory.jsonl          # 飞书决策记忆（5条 → 30条）
│   ├── preference_memory.jsonl        # 个人偏好记忆（5条 → 30条）
│   ├── knowledge_health.jsonl         # 团队知识健康（5条 → 30条）
│   └── long_term_memory.jsonl         # 长时序记忆（5条 → 30条）
├── scripts/
│   ├── validate_schema.py             # 数据格式验证工具
│   ├── run_benchmark.py               # 评测运行器（调用 Memory Engine）
│   └── generate_cases.py             # LLM 批量生成用例工具
└── docs/
    ├── benchmark_generation_plan.md   # 评测方案设计文档
    ├── metrics_definition.md          # 指标体系定义
    └── benchmark_report_template.md  # 报告模板（填写实际数字后提交）
```

---

## 数据集总览

| 数据集 | 测试能力 | 对应要求 | 权重 | 当前数量 | 目标数量 |
|--------|---------|---------|------|---------|---------|
| `anti_interference` | 抗干扰召回 | **比赛强制要求** | 15% | 5 | 30 |
| `contradiction_update` | 矛盾更新 | **比赛强制要求** | 15% | 5 | 30 |
| `efficiency` | 效能指标 | **比赛强制要求** | 15% | 5 | 30 |
| `command_memory` | CLI命令记忆 | 方向 A | 10% | 5 | 30 |
| `decision_memory` | 飞书决策记忆 | 方向 B | 15% | 5 | 30 |
| `preference_memory` | 个人偏好记忆 | 方向 C | 15% | 5 | 30 |
| `knowledge_health` | 团队知识健康 | 方向 D | 10% | 5 | 30 |
| `long_term_memory` | 长时序记忆 | 综合能力 | 5% | 5 | 30 |
| **总计** | | | 100% | **40** | **240** |

---

## 数据格式

每行一个 JSON 对象（JSONL）。核心字段：

```json
{
  "case_id": "decision_001",
  "category": "decision_memory",
  "scenario": "一句话描述业务场景",
  "difficulty": "easy | medium | hard",
  "input_events": [
    {
      "event_id": "e1",
      "timestamp": "2026-04-01T10:00:00",
      "source": "feishu_group | feishu_doc | cli | ...",
      "speaker": "发言人",
      "content": "事件内容",
      "context": { "project": "ProjectName" }
    }
  ],
  "query": "检索问题或任务触发语",
  "expected": {
    "should_retrieve": true,
    "memory_type": "decision | preference | command | knowledge",
    "answer_keywords": ["关键词1", "关键词2"],
    "should_not_contain": ["禁止出现的旧信息"],
    "evidence_event_ids": ["e1"]
  },
  "metrics": ["recall_at_3", "keyword_match", "evidence_match"]
}
```

完整字段说明见 [`schema.json`](schema.json)。

---

## 评分标准

```
总分 = Σ (数据集得分 × 权重) × 100

评级：
  优秀：≥ 85 分
  良好：70~85 分
  待改进：< 70 分
```

---

## 理论依据

本 benchmark 设计参考了以下公开评测基准：

- **LONGMEMEVAL** (ICLR 2025, arXiv:2410.10813) — 长时序记忆评测、Recall@k 指标设计
- **LOCOMO** (ACL Findings 2024, arXiv:2402.17753) — 对抗性测试、多跳推理评测
- **MemBench** (ACL Findings 2025, arXiv:2506.21605) — 事实/反思双层次 × 参与/观察双场景 × 准确/召回/容量/效率四指标
- **Memory for Autonomous LLM Agents** (Survey, 2026, arXiv:2603.07670) — Agent 记忆机制与评测系统性综述


详见 [`docs/benchmark_generation_plan.md`](docs/benchmark_generation_plan.md)。

---

## 版本规划

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1 | 方案文档 + schema + mini benchmark（40条） | ✅ **当前** |
| v0.2 | 每类扩展到 30 条（240条），格式确认后 | ⏳ 待扩展 |
| v1.0 | 240条 + 自动评测脚本 + benchmark report | ⏳ 规划中 |

---

## Contributors

- **[Ethan](https://github.com/EthanCherry)** — Benchmark 设计、数据集构建、文档编写
