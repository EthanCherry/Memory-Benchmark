# LarkMemory Benchmark 生成方案 v1.0

> **项目**: 飞书 OpenClaw 赛道 — 企业级长程协作 Memory 系统  
> **文档版本**: v1.0  
> **创建时间**: 2026-04-30  
> **参考基准**: LONGMEMEVAL (ICLR 2025)、LOCOMO (ACL Findings 2024)、MemBench (ACL Findings 2025)

---

## 1. 方案定位

本 benchmark 不以"短文本问答准确率"为核心，而以**企业协作记忆的真实可用性**为目标。围绕飞书日常协作中的决策沉淀、偏好学习、命令复用和知识健康场景，构造包含噪声干扰、时序变化、矛盾更新、项目隔离、拒答和效能验证的多维测试集。

评估一个 Memory Engine 是否真正具备以下能力：

1. 能从飞书/CLI/文档/任务等上下文中识别有长期价值的信息；
2. 能将原始信息抽取为结构化记忆；
3. 能在后续任务中精准检索相关记忆，并**追溯证据来源**；
4. 能在大量无关信息干扰下保持记忆召回能力；
5. 能处理新旧信息冲突，区分历史旧值和当前有效值；
6. 能在无相关记忆时**正确拒答**，不编造答案；
7. 能在多项目场景下**隔离记忆**，防止跨项目泄漏；
8. 能通过命令推荐、偏好复用、决策召回等方式产生实际效率提升。

**比赛文档硬性要求**：参赛队伍自证系统价值，并至少包含以下三类测试：
- ⭐ **抗干扰测试** (Anti-Interference)
- ⭐ **矛盾更新测试** (Contradiction Update)
- ⭐ **效能指标验证** (Efficiency Validation)

---

## 2. 架构设计：4 方向 × 7 测试类型

### 2.1 为什么按方向分而不是按测试类型分？

比赛文档定义了 4 个探索方向（A/B/C/D），同时要求至少包含 3 类测试。但实际上：

- **command_memory**（CLI 命令记忆）是规律统计，不存在"矛盾更新"语义
- **knowledge_health**（知识健康）的重点是遗忘预警和版本管理，"效能指标"不直接适用
- 按测试类型分 benchmark 会导致**方向和测试类型交叉**，数据归属不清

因此，我们按 4 个方向组织 benchmark，每个内部用 `test_type` 字段标注测试类型。

### 2.2 Benchmark 总览

| Benchmark | 比赛方向 | 记忆类型 | 适用测试类型 | 不适用测试类型 | 理由 |
|-----------|---------|---------|-------------|--------------|------|
| **command_memory** | A | 命令记忆 | 召回、效能、抗干扰、跨项目 | 矛盾更新、拒答 | CLI 命令是统计规律，无新旧冲突和拒答语义 |
| **decision_memory** | B | 决策记忆 | 召回、抗干扰、矛盾更新、效能、长时序、拒答、跨项目 | — | 全覆盖 |
| **preference_memory** | C | 偏好记忆 | 召回、抗干扰、矛盾更新、效能、拒答、跨项目 | 长时序 | 偏好会变更，需矛盾更新 |
| **knowledge_health** | D | 知识健康 | 召回、抗干扰、矛盾更新、长时序、拒答 | 效能、跨项目 | 知识管理不直接产生操作提效 |

### 2.3 长时序记忆的处理

"长时序记忆"不再作为独立 benchmark，而是：
- 作为 `time_span_days` 字段量化每个 case 的时间跨度
- 作为 `long_term_retention` 测试类型，融入各方向 benchmark
- difficulty 由 `time_span_days` 和噪声数量共同决定

---

## 3. 理论基础

### 3.1 参考公开基准

| 基准 | 核心设计借鉴点 |
|------|---------------|
| **LONGMEMEVAL** (ICLR 2025) | 7种问题类型分类、Recall@k 指标、haystack 干扰设计、时间推理评测 |
| **LOCOMO** (ACL Findings 2024) | single-hop/multi-hop/temporal/adversarial 四类分法、对抗性测试设计、Temporal Event Graph |
| **MemBench** (ACL Findings 2025) | 事实/反思双层次记忆、参与/观察双场景、准确/召回/容量/效率四指标体系 |

### 3.2 与公开基准的对比

| 对比维度 | LONGMEMEVAL | LOCOMO | MemBench | **本 Benchmark** |
|----------|-------------|--------|----------|-----------------|
| 组织方式 | 按能力类型 | 按能力类型 | 按能力类型 | **按业务方向**（每方向含多测试类型） |
| 样本数 | 500 | 1,813 | ~65k | 51 (v1.0) |
| 业务场景 | 通用对话 | 日常对话 | 通用 Agent | **企业办公/研发协作** |
| 测试类型 | 记忆召回 | 记忆召回 | 准确/召回/容量/效率 | **召回 + 抗干扰 + 矛盾更新 + 效能 + 长时序 + 拒答 + 跨项目** |
| 核心指标 | QA准确率 | QA准确率 | 准确/召回/容量/效率 | **命中率 + 效能指标 + 更新准确性 + 拒答率 + 项目隔离率** |
| 比赛对齐 | — | — | — | ✅ 4方向对齐比赛 + 3类测试覆盖硬性要求 |
| 证据追溯 | — | — | — | ✅ evidence_event_ids 必填 + 双层判分 |

### 3.3 能力维度设计

从 LongMemEval、LOCOMO、MemBench 借鉴并转化为企业场景的 7 类测试能力：

| 测试能力 | 来源借鉴 | 企业场景转化 | 判分核心 |
|---------|---------|-------------|---------|
| 信息抽取 | LongMemEval 抽取 | 从群聊/文档/会议纪要中抽取决策、理由、结论 | answer_keywords + evidence_match |
| 抗干扰 | LongMemEval haystack + LOCOMO adversarial | 群聊噪声、高相似干扰、跨项目污染 | noise_robustness |
| 矛盾更新 | LongMemEval 知识更新 + LOCOMO temporal | 决策变更、偏好变更、知识版本覆盖 | latest_value_accuracy + allow_historical_mention |
| 拒答能力 | LongMemEval 拒答 | 无记忆时不编造答案，正确表示不确定 | abstention_accuracy + hallucination_rate |
| 跨项目隔离 | 企业场景原创 | 同名客户/同名模块/同名负责人的记忆隔离 | cross_project_leakage_rate + scope_accuracy |
| 效能验证 | MemBench 效率 | 命令补全、偏好复用、决策召回的字符/步骤节省 | char_saving_rate + step_saving_rate |
| 长时序保持 | LongMemEval 长程 + LOCOMO temporal graph | 跨季度/跨年的记忆保持和遗忘曲线 | long_term_recall |

---

## 4. 数据格式

### 4.1 Schema 概览

| 字段 | 类型 | 说明 |
|------|------|------|
| `case_id` | string | `{direction}_{test_type}_{NNN}` |
| `category` | enum | 4 个方向之一 |
| `test_type` | enum | 7 种测试类型之一 |
| `scenario` | string | 业务场景描述 |
| `difficulty` | enum | easy (≤7d) / medium (8-90d) / hard (>90d) |
| `time_span_days` | int | 事件时间跨度（天） |
| `input_events` | array | 事件链序列，按时间排序 |
| `query` | string | 检索问题 |
| `expected` | object | 标准答案（双层判分：answer_correct + evidence_correct） |
| `metrics` | array | 判分指标列表 |

### 4.2 test_type 枚举

| test_type | 说明 | 适用方向 | 比赛要求 |
|-----------|------|---------|---------|
| `retrieval_recall` | 基础记忆召回 | A, B, C, D | — |
| `anti_interference` | ⭐ 抗干扰召回 | A, B, C, D | ⭐ 比赛硬性要求 |
| `contradiction_update` | ⭐ 矛盾更新 | B, C, D | ⭐ 比赛硬性要求 |
| `efficiency` | ⭐ 效能验证 | A, B, C | ⭐ 比赛硬性要求 |
| `long_term_retention` | 长时序保持 | B, D | — |
| `abstention` | 拒答能力 | B, C, D | — |
| `cross_project` | 跨项目隔离 | A, B, C | — |

### 4.3 expected 结构详解

本 benchmark 采用**双层判分**机制：答案正确性 + 证据正确性。

#### 基础字段

```json
{
  "should_retrieve": true,
  "memory_type": "decision",
  "answer_keywords": ["PostgreSQL", "复杂事务"],
  "evidence_event_ids": ["e1", "e3"]
}
```

#### 矛盾更新精细判分（contradiction_update）

```json
{
  "current_value": "Memcached",
  "inactive_values": ["Redis"],
  "forbidden_active_values": ["Redis"],
  "allow_historical_mention": true,
  "answer_keywords": ["Memcached", "内存占用过高"],
  "evidence_event_ids": ["e2"],
  "superseded_event_ids": ["e1"]
}
```

- `current_value`：当前有效值
- `inactive_values`：历史旧值（允许作为历史叙述出现，但不允许作为当前答案）
- `forbidden_active_values`：绝对禁止作为当前有效值的字符串（即使部分匹配也算错）
- `allow_historical_mention`：为 true 时，"之前用 Redis，现在改用 Memcached" 算正确
- `superseded_event_ids`：已废弃的事件，不应被引用为当前有效证据

#### 拒答测试（abstention）

```json
{
  "should_retrieve": false,
  "abstention_keywords": ["未找到", "不确定", "没有相关记忆"],
  "hallucination_triggers": ["月结30天", "季度结算", "预付款"],
  "evidence_event_ids": []
}
```

- `abstention_keywords`：表示正确拒答的关键词
- `hallucination_triggers`：系统不应编造的常见合理答案

### 4.4 噪声设计规范

噪声不是随机文本，必须模拟真实飞书群聊场景：

| 难度 | 噪声数量 | 噪声类型 | 示例 |
|------|---------|---------|------|
| **easy** | 0~5 条 | 明显无关 | "收到"、请假、表情包 |
| **medium** | 5~15 条 | 同项目弱相关 | 进度同步、文档更新、站会通知 |
| **hard** | 10~50 条 | 高相似干扰 + 跨项目污染 | 同名方案讨论、其他项目的同类决策、被否方案的多次提及 |

**高相似噪声设计**：目标记忆是"Alpha 项目使用 PostgreSQL"，高相似噪声应包含：
- "Beta 项目使用 MySQL"
- "Gamma 项目讨论过 PostgreSQL 但未采用"
- "Alpha 项目早期提过 MongoDB"
- "有人觉得 PostgreSQL 太重了"

这样才能测试系统是否真正理解了项目、时间和状态，而不是简单关键词匹配。

---

## 5. 难度分级规则

基于企业时间锚点（日/周/迭代/季度/年）和学术记忆保持研究（LongMemEval、LOCOMO、MemBench、Agent Memory Survey 2026）：

| 难度 | time_span_days | 企业时间锚点 | 学术对标 | 场景特征 |
|------|---------------|-------------|---------|---------|
| **easy** | ≤ 7 天 | 同一迭代内，活跃工作记忆窗口 | LOCOMO 单 session 内记忆范围 | 同项目、无/极少噪声、无冲突 |
| **medium** | 8~90 天 | 跨迭代/跨月 | LongMemEvalS (~50 sessions) 跨会话推理 | 跨项目、轻-中噪声、单次冲突 |
| **hard** | > 90 天 | 跨季度/跨年 | 学术界公认"尚未解决"的长期保留挑战 (Agent Memory Survey 2026) | 大量高相似噪声、多次冲突/撤回、长时间无复现 |

> **设计依据**：
> - LongMemEval (ICLR 2025) 以 ~50~500 个 session 衡量长程记忆，对应企业场景的跨周/跨月
> - LOCOMO (ACL Findings 2024) 最多 35 个 session + Temporal Event Graph，短期记忆范围
> - MemBench (ACL Findings 2025) 在 100k tokens 上下文后记忆性能显著下降
> - Agent Memory Survey (2026) 明确指出"跨数周到数月的可靠知识保留尚未解决"，一周滚动摘要经 3 次压缩后丢失关键信息
> - 企业协作有自然时间锚点：日报（1天）、周会（7天）、迭代周期（2~4周）、季度复盘（90天）、年度规划（365天）
>
> **每个 hard 级别的 case 应至少覆盖半年（180天）或一年（365天）的时间跨度**，以真正测试"长时序"能力。

---

## 6. 生成规则

### 6.1 command_memory

| test_type | 生成逻辑 | 指标 |
|-----------|---------|------|
| retrieval_recall | 同项目路径多次执行 + 当前前缀 → 推荐命令 | top1_hit, command_exact_match |
| efficiency | 历史行为 + 当前输入 → 计算字符节省率 | command_hit_rate, char_saving_rate |
| anti_interference | 关键命令 + 跨项目/高相似噪声 → 仍能推荐正确命令 | top1_hit, noise_robustness |
| cross_project | 不同项目的同类命令 → 按项目上下文隔离 | scope_accuracy, cross_project_leakage_rate |

**不可用**：contradiction_update、abstention（命令是统计规律，无新旧冲突和拒答语义）

### 6.2 decision_memory

| test_type | 生成逻辑 | 指标 |
|-----------|---------|------|
| retrieval_recall | 事件链（讨论→反对→决策→更新）+ 追问 → 召回决策卡片 | decision_match, reason_match, rejected_option_match |
| anti_interference | 关键决策 + 高相似群聊噪声/跨项目干扰 → 召回正确决策 | recall_at_3, noise_robustness |
| contradiction_update | 旧决策 + 新冲突决策 → 使用最新版，允许历史叙述 | latest_value_accuracy, old_value_suppression |
| efficiency | 历史决策 + 当前问题 → 节省重复沟通 | recall_at_3, char_saving_rate |
| long_term_retention | 早期决策 + 跨季度噪声 → 召回早期记忆 | long_term_recall, recall_at_3 |
| abstention | 无相关记忆 + 噪声中含暗示 → 正确拒答不编造 | abstention_accuracy, hallucination_rate |
| cross_project | 同名客户/同名方案在不同项目中的不同决策 → 按项目隔离 | cross_project_leakage_rate, scope_accuracy |

### 6.3 preference_memory

| test_type | 生成逻辑 | 指标 |
|-----------|---------|------|
| retrieval_recall | 显式/隐式偏好 + 后续任务 → 个性化建议 | preference_match, condition_match |
| anti_interference | 偏好 + 工作噪声 → 仍能记住偏好 | preference_match, noise_robustness |
| contradiction_update | 旧偏好 + 新偏好 → 使用最新版 | latest_value_accuracy, old_value_suppression |
| efficiency | 习惯记忆 + 当前任务 → 减少设置步骤 | preference_match, step_saving_rate |
| abstention | 无相关偏好 → 正确拒答不编造 | abstention_accuracy, hallucination_rate |
| cross_project | 不同项目的不同偏好 → 按项目隔离 | cross_project_leakage_rate, scope_accuracy |

### 6.4 knowledge_health

| test_type | 生成逻辑 | 指标 |
|-----------|---------|------|
| retrieval_recall | 知识注入 + 版本变化 → 正确值 | recall_at_3, latest_value_accuracy |
| anti_interference | 关键知识 + 日常消息噪声 → 召回关键知识 | recall_at_3, noise_robustness |
| contradiction_update | 旧知识 + 更新知识 → 废弃旧版 | latest_value_accuracy, expired_memory_suppression |
| long_term_retention | 早期知识 + 长时间跨度 → 仍能召回 | long_term_recall, recall_at_3 |
| abstention | 无相关知识 → 正确拒答不编造 | abstention_accuracy, hallucination_rate |

**不可用**：efficiency、cross_project（知识管理不直接产生操作提效，且知识通常是全局的）

---

## 7. 质量约束

1. **可判分性**：每条 case 的 `expected` 必须能用规则客观判分
2. **双层判分**：答案正确 + 证据来源正确，防止"碰巧答对"
3. **真实性**：场景贴近真实企业协作，噪声模拟真实群聊
4. **难度梯度**：每个 benchmark easy:medium:hard ≈ 3:5:2
5. **比赛覆盖**：⭐ 抗干扰、⭐ 矛盾更新、⭐ 效能 三类测试必须出现在至少 2 个方向中
6. **证据必填**：所有 case 的 `evidence_event_ids` 必须填写
7. **禁止冒高**：不得通过删除难例来虚高通过率
8. **拒答测试**：abstention 类 case 的 `should_retrieve` 必须为 false

---

## 8. 生成流程

```
人工确定 4 方向 × 各适用测试类型（7 种）
    ↓
每个 (方向, 测试类型) 手写 2-3 条高质量种子
    ↓
事件链设计：讨论 → 反对 → 决策 → 噪声 → 更新（模拟真实协作流程）
    ↓
人工审核 expected 是否清晰可判分
    ↓
噪声填充：按难度等级填充真实群聊噪声（easy 0~5 / medium 5~15 / hard 10~50）
    ↓
统一 JSONL + validate_schema.py（含语义校验）
    ↓
run_benchmark.py 输出报告（双层判分）
```

---

## 9. 参考文献

1. Wu, D., et al. (2025). LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. *ICLR 2025*. arXiv:2410.10813.
2. Maharana, A., et al. (2024). Evaluating Very Long-Term Conversational Memory of LLM Agents. *ACL Findings 2024*. arXiv:2402.17753.
3. Tan, H., Zhang, Z., Ma, C., Chen, X., Dai, Q., & Dong, Z. (2025). MemBench: Towards More Comprehensive Evaluation on the Memory of LLM-based Agents. *ACL Findings 2025*. arXiv:2506.21605.
4. Du, P. (2026). Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers. arXiv:2603.07670.
5. 飞书 OpenClaw 赛道-企业级长程协作 Memory 系统（公开版）. https://bytedance.larkoffice.com/wiki/TYewweOPuiHMtBkA1aXcldJonic
