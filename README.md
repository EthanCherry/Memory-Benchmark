# LarkMemory Benchmark

> 飞书 OpenClaw 赛道 — 企业级长程协作 Memory 系统 评测数据集  
> **Benchmark Version**: v0.2 (4-direction structure, 40 cases)  
> **目标版本**: v1.0 (4 × 30 = 120 cases)

---

## 设计理念

本 benchmark 按**比赛文档的四个业务方向**（A/B/C/D）组织为 4 个独立 benchmark，每个 benchmark 内部包含该方向适用的**测试类型**。

> **为什么按方向而不是按测试类型分？**
> 比赛文档定义了 4 个探索方向（CLI 命令记忆、飞书决策记忆、个人偏好记忆、团队知识健康），同时要求至少包含 3 类测试（抗干扰、矛盾更新、效能验证）。每个方向不一定适用所有测试类型（例如 CLI 命令是规律统计，不存在矛盾更新），因此按方向分 benchmark 更合理，每个内部标注适用的测试类型和占比。

---

## Benchmark 总览

| Benchmark | 比赛方向 | 测试类型分布 | v0.2 条数 | v1 目标 |
|-----------|---------|-------------|----------|---------|
| **command_memory** | A：CLI 高频命令与工作流记忆 | 召回 50% · 效能 30% · 抗干扰 20% | 10 | 30 |
| **decision_memory** | B：飞书项目决策与上下文记忆 | 召回 25% · 抗干扰 17% · 矛盾更新 25% · 效能 17% · 长时序 16% | 12 | 30 |
| **preference_memory** | C：个人工作习惯与偏好记忆 | 召回 40% · 抗干扰 20% · 矛盾更新 20% · 效能 20% | 10 | 30 |
| **knowledge_health** | D：团队知识断层与遗忘预警 | 召回 25% · 抗干扰 25% · 矛盾更新 25% · 长时序 25% | 8 | 30 |
| **总计** | | | **40** | **120** |

### 测试类型说明

| 测试类型 | 比赛要求 | 说明 |
|---------|---------|------|
| `retrieval_recall` | — | 基础记忆召回能力 |
| `anti_interference` | ⭐ 比赛强制 | 大量无关信息干扰下仍能召回关键记忆 |
| `contradiction_update` | ⭐ 比赛强制 | 新旧信息冲突时保留最新版本、抑制旧版本 |
| `efficiency` | ⭐ 比赛强制 | 使用记忆后减少操作成本（字符/步骤/时间） |
| `long_term_retention` | — | 跨周/月/季度后的记忆保持能力 |

> ⭐ 比赛文档明确要求参赛队伍至少包含**抗干扰测试、矛盾更新测试、效能指标验证**三类测试。  
> command_memory 方向不含 contradiction_update，因为 CLI 命令是统计规律而非事实声明，不存在"新旧冲突"语义。

---

## 快速开始

### 1. 验证数据格式

```bash
python scripts/validate_schema.py
```

### 2. 运行 benchmark（需先启动 Memory Engine）

```bash
export MEMORY_ENGINE_BASE_URL=http://localhost:8000

# 运行全量评测
python scripts/run_benchmark.py --all

# 运行单个 benchmark
python scripts/run_benchmark.py --dataset datasets/decision_memory.jsonl

# 按测试类型过滤
python scripts/run_benchmark.py --all --test-type anti_interference

# 输出 JSON 报告
python scripts/run_benchmark.py --all --output reports/eval_$(date +%Y%m%d).json
```

### 3. 扩展数据集到 v1（需 Qwen30B 或其他 LLM）

```bash
export LLM_BASE_URL=http://your-qwen-service:11434
export LLM_MODEL=qwen-30b

python scripts/generate_cases.py --all --count 30
python scripts/validate_schema.py
```

---

## 文件结构

```
benchmarks/
├── README.md                          # 本文件
├── schema.json                        # 数据格式 JSON Schema v2
├── datasets/                          # 4 个方向 benchmark（JSONL格式）
│   ├── command_memory.jsonl           # 方向 A：CLI 命令记忆（10条 → 30条）
│   ├── decision_memory.jsonl          # 方向 B：飞书决策记忆（12条 → 30条）
│   ├── preference_memory.jsonl        # 方向 C：个人偏好记忆（10条 → 30条）
│   └── knowledge_health.jsonl         # 方向 D：团队知识健康（8条 → 30条）
├── scripts/
│   ├── validate_schema.py             # 数据格式验证工具
│   ├── run_benchmark.py               # 评测运行器（支持按 test_type 过滤）
│   └── generate_cases.py             # LLM 批量生成用例工具
└── docs/
    ├── benchmark_generation_plan.md   # 评测方案设计文档
    ├── metrics_definition.md          # 指标体系定义
    └── benchmark_report_template.md  # 报告模板（填写实际数字后提交）
```

---

## 数据格式

每行一个 JSON 对象（JSONL）。核心字段：

```json
{
  "case_id": "dec_anti_001",
  "category": "decision_memory",
  "test_type": "anti_interference",
  "scenario": "大量群聊噪声后的关键决策召回",
  "difficulty": "medium",
  "time_span_days": 5,
  "input_events": [
    {
      "event_id": "e1",
      "timestamp": "2026-04-01T09:00:00",
      "source": "feishu_group",
      "speaker": "项目负责人",
      "content": "客户Alpha的周报固定使用表格视图。",
      "context": { "project": "ProjectName" }
    }
  ],
  "query": "客户Alpha的报告应该用什么视图？",
  "expected": {
    "should_retrieve": true,
    "memory_type": "decision",
    "answer_keywords": ["客户Alpha", "表格视图"],
    "should_not_contain": ["列表视图"],
    "evidence_event_ids": ["e1"]
  },
  "metrics": ["recall_at_3", "keyword_match", "noise_robustness"]
}
```

**关键字段说明**：

| 字段 | 说明 |
|------|------|
| `category` | 所属方向（command_memory / decision_memory / preference_memory / knowledge_health） |
| `test_type` | 测试类型（retrieval_recall / anti_interference / contradiction_update / efficiency / long_term_retention） |
| `time_span_days` | 事件时间跨度（天），用于量化长时序记忆难度 |
| `difficulty` | easy（≤1天）/ medium（≤14天）/ hard（>14天 或 大量噪声） |

完整字段定义见 [`schema.json`](schema.json)。

---

## 评分标准

```
总分 = Σ (方向得分 × 权重) × 100

方向权重：
  command_memory:     15%（比赛方向 A）
  decision_memory:    30%（比赛方向 B，核心场景）
  preference_memory:  25%（比赛方向 C）
  knowledge_health:   30%（比赛方向 D）

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
| v0.1 | 方案文档 + schema + 8 类 mini benchmark（40条） | ✅ 已归档 |
| v0.2 | 重构为 4 方向 × 多测试类型结构（40条） | ✅ **当前** |
| v1.0 | 4 × 30 = 120 条 + 自动评测脚本 + benchmark report | ⏳ 规划中 |

---

## Contributors

- **[Ethan](https://github.com/EthanCherry)** — Benchmark 设计、数据集构建、文档编写
