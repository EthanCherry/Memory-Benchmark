# LarkMemory Benchmark 生成方案 v0.1

> **项目**: 飞书 OpenClaw 赛道 — 企业级长程协作 Memory 系统  
> **文档版本**: v0.1  
> **创建时间**: 2026-04-30  
> **参考基准**: LONGMEMEVAL (ICLR 2025)、LOCOMO (ACL Findings 2024)

---

## 1. 方案定位

本 benchmark 面向"飞书 OpenClaw 赛道 — 企业级长程协作 Memory 系统"设计，目标不是单纯测试大模型问答能力，而是评估一个 Memory Engine 是否真正具备以下核心能力：

1. 能从飞书/CLI/文档/任务等上下文中**识别有长期价值的信息**
2. 能将原始信息**抽取为结构化记忆**
3. 能在后续任务中**精准检索**相关记忆
4. 能在大量无关信息干扰下**保持记忆召回能力**（抗干扰）
5. 能处理新旧信息冲突，并**使用最新有效记忆**（矛盾更新）
6. 能通过命令推荐、偏好复用、决策召回等方式产生**实际效率提升**

比赛文档明确要求参赛队伍自证系统价值，并至少包含**抗干扰测试、矛盾更新测试、效能指标验证**三类测试，因此本 benchmark 以这三类为基础，同时扩展到四个业务方向：CLI 命令记忆、飞书项目决策记忆、个人偏好记忆、团队知识健康/遗忘预警。

---

## 2. 理论基础

### 2.1 参考公开基准

| 基准 | 核心设计借鉴点 |
|------|---------------|
| **LONGMEMEVAL** (ICLR 2025) | 7种问题类型分类、Recall@k 指标、haystack 干扰设计、时间推理评测 |
| **LOCOMO** (ACL Findings 2024) | single-hop/multi-hop/temporal/adversarial 四类分法、对抗性测试设计 |

| **LarkCopilot Benchmark Report** | PRD指标映射表格、可复现命令入口、失败分类与修复建议格式 |

### 2.2 与公开基准的对比

| 对比维度 | LONGMEMEVAL | LOCOMO | **本 Benchmark** |
|----------|-------------|--------|-----------------|
| 样本数 | 500 | 1,813 | 40 (v0) → 240 (v1) |
| 会话跨度 | 40-500会话 | 35会话 | 2年时间跨度 |
| 评测方式 | LLM-as-judge | 人工+自动 | 规则判分（v0），LLM judge（v1） |
| 问题类型 | 7种 | 4种 | 8维度×子类别 |
| 业务场景 | 通用对话 | 日常对话 | 企业办公/研发协作 |
| 核心指标 | QA准确率 | QA准确率 | 命中率 + 效能指标 |

---

## 3. Benchmark 总体结构

本 benchmark 设计为 **8 个子数据集**，覆盖比赛强制要求和四个业务方向：

| 数据集名称 | 对应能力 | 对应比赛要求/方向 | 权重 | v0 数量 | v1 数量 |
|-----------|---------|-----------------|------|---------|---------|
| `anti_interference.jsonl` | 抗干扰召回 | **比赛强制要求** | 15% | 5 | 30 |
| `contradiction_update.jsonl` | 矛盾更新 | **比赛强制要求** | 15% | 5 | 30 |
| `efficiency.jsonl` | 效能指标 | **比赛强制要求** | 15% | 5 | 30 |
| `command_memory.jsonl` | CLI高频命令记忆 | 方向 A | 10% | 5 | 30 |
| `decision_memory.jsonl` | 飞书项目决策记忆 | 方向 B | 15% | 5 | 30 |
| `preference_memory.jsonl` | 个人工作习惯/偏好记忆 | 方向 C | 15% | 5 | 30 |
| `knowledge_health.jsonl` | 团队知识健康/遗忘预警 | 方向 D | 10% | 5 | 30 |
| `long_term_memory.jsonl` | 长时序记忆保持 | 跨方向综合 | 5% | 5 | 30 |

**v0 阶段**：共 40 条，用于快速跑通系统接口和评测逻辑。  
**v1 阶段**：扩展到 240 条，用于正式报告和答辩展示。

---

## 4. 数据格式规范

### 4.1 通用字段结构

所有 benchmark 数据统一采用 **JSONL 格式**（每行一个 JSON 对象），完整字段规范见 `../schema.json`。

```json
{
  "case_id": "decision_001",
  "category": "decision_memory",
  "scenario": "一句话描述业务场景",
  "difficulty": "easy | medium | hard",
  "input_events": [ /* 事件列表 */ ],
  "query": "检索问题或任务触发语",
  "expected": { /* 标准答案 */ },
  "metrics": [ /* 判分指标列表 */ ]
}
```

### 4.2 input_events 格式

```json
{
  "event_id": "e1",
  "timestamp": "2026-04-01T10:00:00",
  "source": "feishu_group | feishu_doc | feishu_task | feishu_meeting | feishu_chat | cli",
  "speaker": "角色名称",
  "content": "事件内容",
  "context": {
    "project": "项目名",
    "cwd": "/workspace/path",
    "user_id": "user_demo_001",
    "chat_id": "chat_demo_001"
  }
}
```

### 4.3 expected 格式

```json
{
  "should_retrieve": true,
  "memory_type": "decision | preference | command | knowledge | event",
  "answer_keywords": ["关键词1", "关键词2"],
  "should_not_contain": ["禁止出现的词"],
  "latest_value": "矛盾更新类的正确最新值",
  "evidence_event_ids": ["e1", "e2"],
  "superseded_event_ids": ["旧版事件ID"],
  "suggested_command": "命令记忆类的推荐命令",
  "baseline_chars": 68,
  "actual_chars": 10,
  "min_saving_rate": 0.85
}
```

---

## 5. 八类 Benchmark 设计规则

### 5.1 抗干扰测试 (`anti_interference`)

**测什么？** 系统在大量无关信息干扰后，是否仍能召回早期关键记忆。

**生成模板：**
```
关键记忆 1 条
+ 无关噪声 N 条
+ 后续查询 1 条
= 判断系统能否召回关键记忆
```

**难度分级：**

| 难度 | 噪声数量 | 时间跨度 | 干扰类型 |
|------|---------|---------|---------|
| easy | ≤5 条 | 同一天 | 纯无关内容 |
| medium | 10~20 条 | 一周内 | 混合相关/无关 |
| hard | ≥50 条 | 一个月以上 | 高相似度干扰/角色混淆 |

**子类别（v1 扩展）：**
- 单轮噪声干扰（6条）
- 多轮连续噪声干扰（6条）
- 高相似度干扰（6条）
- 时间跨度干扰（6条）
- 角色混淆干扰（6条）

---

### 5.2 矛盾更新测试 (`contradiction_update`)

**测什么？** 系统能否处理"先说 A，后改成 B"，并在回答中使用最新版本。

**生成模板：**
```
旧记忆（e1）
+ 新冲突记忆（e2）
+ 查询
= 判断是否使用新记忆、抑制旧记忆
```

**子类别（v1 扩展）：**
- 直接覆盖型（6条）
- 部分更新型（6条）
- 时间线矛盾（6条）
- 多实体并发矛盾（6条）
- 撤回/取消型（6条）

---

### 5.3 效能指标测试 (`efficiency`)

**测什么？** 使用记忆前后是否减少操作成本。比赛文档举例：使用前需要敲 50 个字符，使用后只需 10 个，提效 80%。

**核心指标公式：**
```
字符节省率 = 1 - actual_chars / baseline_chars
命令命中率 = 推荐命令是否为 expected_command
步骤节省率 = (使用前步骤数 - 使用后步骤数) / 使用前步骤数
```

---

### 5.4 CLI 命令记忆 (`command_memory`)

**测什么？** 对应比赛方向 A，系统是否能记住高频命令、常用参数、项目路径偏好，并根据当前上下文推荐命令。

**生成模板：**
```
同一项目路径下多次执行命令（2~5次）
+ 当前目录/命令前缀
= 推荐对应高频命令
```

---

### 5.5 飞书决策记忆 (`decision_memory`)

**测什么？** 对应比赛方向 B，系统是否能从飞书群聊或文档中抽取项目决策、理由、被否方案，并在后续讨论中召回。

**关键字段：**
- `decision`：决策结论
- `rejected_option`：被否决方案
- `reason`：决策理由
- `evidence_event_ids`：原始证据来源

---

### 5.6 个人偏好记忆 (`preference_memory`)

**测什么？** 对应比赛方向 C，系统是否能识别用户的显式偏好、隐式习惯，并在合适场景中主动使用。

**偏好类型：**
- 显式偏好（用户直接声明）
- 隐式偏好（从行为模式推断）
- 周期性偏好（时间/场景触发）
- 偏好冲突（以最新显式声明为准）

---

### 5.7 团队知识健康 (`knowledge_health`)

**测什么？** 对应比赛方向 D，系统是否能识别团队长期知识、知识过期和遗忘风险。

**参考艾宾浩斯遗忘曲线**，知识新鲜度分级：
- `fresh`：最近 30 天内访问
- `aging`：30~90 天
- `stale`：90~180 天  
- `forgotten`：>180 天

---

### 5.8 长时序记忆 (`long_term_memory`)

**测什么？** 系统在跨周、跨月、跨季度、跨年场景下是否仍能保持记忆连续性。

**时间跨度分布（v1）：**
- 3~6个月回忆（8条）
- 6~12个月回忆（8条）
- 1~2年回忆（8条）
- 跨年度信息更新（6条）

---

## 6. Benchmark 生成流程

推荐采用"**模板化生成 + 人工审核 + 程序扩展**"的三阶段流程：

```
Step 1：人工确定 8 类 benchmark 类型和难度分布
    ↓
Step 2：每类人工写 3~5 条高质量种子样例（即本 v0 交付）
    ↓
Step 3：使用 Qwen30B 扩写同类变体（每类扩展到 30 条）
    ↓
Step 4：人工检查 expected 字段是否清晰可判分
    ↓
Step 5：统一转为 JSONL 格式，通过 validate_schema.py 验证
    ↓
Step 6：开发同学编写 runner 调用 Memory 系统接口
    ↓
Step 7：运行 run_benchmark.py 输出评测报告
```

### 6.1 Qwen30B 扩写 Prompt 模板

```
你是企业级长程记忆系统 benchmark 数据生成器。
请围绕【飞书项目决策记忆】生成 10 条评测用例。

要求：
1. 每条用例必须包含 case_id、category、scenario、difficulty、input_events、query、expected、metrics。
2. input_events 要模拟真实飞书群聊或文档讨论。
3. 每条必须包含一个明确的项目决策、一个决策理由、一个被否定方案。
4. query 不能直接复述原句，要模拟用户后续自然追问。
5. expected 中必须包含 should_retrieve、memory_type、answer_keywords、evidence_event_ids。
6. 输出 JSON 数组，不要输出解释文字。
7. 所有内容使用中文。
```

---

## 7. 判分方式

### 7.1 v0：规则判分（优先）

第一版 benchmark 不依赖大模型判分，优先使用规则判分，保证可复现。

判分规则：
1. 是否召回 `expected.evidence_event_ids` 中的事件
2. 回答是否包含 `expected.answer_keywords` 中的关键词
3. 回答是否不包含 `expected.should_not_contain` 中的禁用词
4. 矛盾更新类是否使用 `latest_value`
5. 效率类是否达到 `min_saving_rate`

### 7.2 v1：LLM-as-Judge

第二版接入 Qwen30B，用于判断语义等价。

**适合 LLM judge 的场景：**
- "采用混合检索" 与 "使用关键词+向量结合的方案" 是否等价
- "接入成本低" 与 "方案落地成本更小" 是否等价
- 偏好表达是否被正确理解
- 回答是否使用了过期记忆
- 回答是否存在幻觉

**LLM judge 输出格式：**
```json
{
  "semantic_correctness": 0.9,
  "uses_latest_memory": 1,
  "evidence_supported": 1,
  "hallucination": 0,
  "comment": "回答正确使用了最新记忆，并包含原始决策理由。"
}
```

---

## 8. 交付计划

### v0.1（当前交付）

- [x] `docs/benchmark_generation_plan.md`（本文档）
- [x] `docs/metrics_definition.md`
- [x] `schema.json`
- [x] `datasets/anti_interference.jsonl`（5条）
- [x] `datasets/contradiction_update.jsonl`（5条）
- [x] `datasets/efficiency.jsonl`（5条）
- [x] `datasets/command_memory.jsonl`（5条）
- [x] `datasets/decision_memory.jsonl`（5条）
- [x] `datasets/preference_memory.jsonl`（5条）
- [x] `datasets/knowledge_health.jsonl`（5条）
- [x] `datasets/long_term_memory.jsonl`（5条）

**合计：40 条 mini benchmark**

### v0.2（格式确认后）

待队友确认格式后，使用 Qwen30B 批量扩写，每类扩展到 30 条。

### v1.0（正式 benchmark）

- 8 类数据集 × 每类 30 条 = **240 条**
- 自动判分脚本（`scripts/run_benchmark.py`）
- benchmark report（`docs/benchmark_report_template.md`）

---

## 9. 注意事项

1. **样本独立性**：每个样本彼此独立，不同样本之间不共享公司名、人名、项目名等实体
2. **可判分性**：每条 case 的 `expected` 字段必须能用规则客观判分，不依赖主观理解
3. **真实性**：场景描述应贴近真实企业协作场景，避免过于抽象
4. **难度梯度**：每个数据集 easy:medium:hard ≈ 3:5:2
5. **禁止冒高**：不得通过删除难例来虚高通过率

---

## 参考文献

1. Wu, D., et al. (2025). LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. *ICLR 2025*. arXiv:2410.10813.
2. Maharana, A., et al. (2024). Evaluating Very Long-Term Conversational Memory of LLM Agents. *ACL Findings 2024*. arXiv:2402.17753.
4. Feishu Memory Copilot Benchmark Report. adjcjh777/lark_ai_challenge_openclaw_longterm_memory, 2026.
5. 飞书 OpenClaw 赛道-企业级长程协作 Memory 系统（公开版）. https://bytedance.larkoffice.com/wiki/TYewweOPuiHMtBkA1aXcldJonic
