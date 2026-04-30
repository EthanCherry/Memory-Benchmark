# LarkMemory Benchmark Report

> **Evaluation ID**: eval-YYYYMMDD-NNN  
> **System Version**: LarkMemory vX.Y.Z  
> **Report Date**: YYYY-MM-DD  
> **Benchmark Version**: v0.1 (40 cases) / v1.0 (240 cases)  
> **Evaluation Mode**: Rule-based (v0) / Rule + LLM-as-Judge (v1)

---

## 先看这个（执行摘要）

> 用 3~5 句话说明本次评测的核心结论，让评委 10 秒内抓住重点。

```
本次评测运行了 8 个维度共 40 条样例（mini benchmark v0），系统整体通过率 XX%，加权总分 XX/100。
比赛强制要求的三类测试：抗干扰通过率 XX%、矛盾更新通过率 XX%、效能指标（字符节省率）平均 XX%，均达到目标线。
四个业务方向中，决策记忆和偏好记忆表现最佳（通过率 XX%），知识健康和长时序记忆仍有改进空间。
```

---

## 可复现实验命令

```bash
# 运行全量 benchmark（需先启动 Memory Engine 服务）
python scripts/run_benchmark.py --all --output reports/benchmark_YYYYMMDD.json

# 单独运行某个数据集
python scripts/run_benchmark.py --dataset datasets/decision_memory.jsonl

# 验证数据格式
python scripts/validate_schema.py --dataset datasets/

# 生成 Markdown 报告
python scripts/run_benchmark.py --all --report-format markdown --output reports/
```

---

## PRD 指标映射

> 对应比赛文档中"挑战三：证明它的价值"的三项强制测试要求。

| PRD 指标 | 本轮评测入口 | 当前结果 | 目标线 | 结论 |
|---------|------------|---------|--------|------|
| 抗干扰召回（Noise Robustness） | `anti_interference.jsonl` | X.XX | ≥ 0.80 | ✅ / ❌ |
| 矛盾更新准确率（Conflict Update Accuracy） | `contradiction_update.jsonl` | X.XX | ≥ 0.85 | ✅ / ❌ |
| 字符节省率（Char Saving Rate） | `efficiency.jsonl` + `command_memory.jsonl` | X.XX | ≥ 0.60 | ✅ / ❌ |
| 步骤节省率（Step Saving Rate） | `efficiency.jsonl` | X.XX | ≥ 0.50 | ✅ / ❌ |
| 决策召回命中率（Decision Recall@3） | `decision_memory.jsonl` | X.XX | ≥ 0.85 | ✅ / ❌ |
| 偏好识别准确率（Preference Match） | `preference_memory.jsonl` | X.XX | ≥ 0.85 | ✅ / ❌ |
| 知识健康新鲜度（Freshness Accuracy） | `knowledge_health.jsonl` | X.XX | ≥ 0.80 | ✅ / ❌ |
| 长时序记忆召回（Long-term Recall@3） | `long_term_memory.jsonl` | X.XX | ≥ 0.75 | ✅ / ❌ |

---

## 分项结果

### 总览

| 数据集 | 样本数 | 通过数 | 通过率 | 加权得分 | 权重 | 目标 |
|--------|-------|-------|-------|---------|------|------|
| anti_interference | 5 | X | X.XX | X.XX | 15% | ≥ 0.80 |
| contradiction_update | 5 | X | X.XX | X.XX | 15% | ≥ 0.85 |
| efficiency | 5 | X | X.XX | X.XX | 15% | ≥ 0.70 |
| command_memory | 5 | X | X.XX | X.XX | 10% | ≥ 0.80 |
| decision_memory | 5 | X | X.XX | X.XX | 15% | ≥ 0.85 |
| preference_memory | 5 | X | X.XX | X.XX | 15% | ≥ 0.85 |
| knowledge_health | 5 | X | X.XX | X.XX | 10% | ≥ 0.80 |
| long_term_memory | 5 | X | X.XX | X.XX | 5% | ≥ 0.75 |
| **总计** | **40** | **X** | **X.XX** | **X.XX/100** | 100% | ≥ 70 |

### 详细指标

#### 抗干扰测试

| 指标 | 结果 | 目标 |
|------|------|------|
| recall_at_3 | X.XX | ≥ 0.85 |
| keyword_match | X.XX | ≥ 0.80 |
| noise_robustness | X.XX | ≥ 0.80 |
| evidence_match | X.XX | ≥ 0.80 |
| should_not_contain_match | X.XX | ≥ 0.90 |

#### 矛盾更新测试

| 指标 | 结果 | 目标 |
|------|------|------|
| latest_value_accuracy | X.XX | ≥ 0.90 |
| old_value_suppression | X.XX | ≥ 0.90 |
| evidence_match | X.XX | ≥ 0.80 |

#### 效能指标测试

| 指标 | 结果 | 目标 |
|------|------|------|
| char_saving_rate | X.XX | ≥ 0.60 |
| step_saving_rate | X.XX | ≥ 0.50 |
| top1_hit | X.XX | ≥ 0.80 |

#### CLI 命令记忆

| 指标 | 结果 | 目标 |
|------|------|------|
| top1_hit | X.XX | ≥ 0.80 |
| command_exact_match | X.XX | ≥ 0.70 |
| char_saving_rate | X.XX | ≥ 0.60 |

#### 飞书决策记忆

| 指标 | 结果 | 目标 |
|------|------|------|
| recall_at_3 | X.XX | ≥ 0.85 |
| decision_match | X.XX | ≥ 0.85 |
| reason_match | X.XX | ≥ 0.80 |
| rejected_option_match | X.XX | ≥ 0.75 |
| evidence_match | X.XX | ≥ 0.80 |

#### 个人偏好记忆

| 指标 | 结果 | 目标 |
|------|------|------|
| preference_match | X.XX | ≥ 0.85 |
| condition_match | X.XX | ≥ 0.75 |
| old_value_suppression | X.XX | ≥ 0.90 |

#### 团队知识健康

| 指标 | 结果 | 目标 |
|------|------|------|
| latest_value_accuracy | X.XX | ≥ 0.90 |
| expired_memory_suppression | X.XX | ≥ 0.90 |
| reminder_timing_accuracy | X.XX | ≥ 0.75 |
| keyword_match | X.XX | ≥ 0.80 |

#### 长时序记忆

| 指标 | 结果 | 目标 |
|------|------|------|
| recall_at_3 | X.XX | ≥ 0.85 |
| long_term_recall | X.XX | ≥ 0.75 |
| keyword_match | X.XX | ≥ 0.80 |
| latest_value_accuracy | X.XX | ≥ 0.90 |

---

## 样例证据

> 选取代表性样例展示系统实际表现，尤其是通过和失败的典型 case。

### 通过样例（展示系统能力）

**Case: `decision_001` — 方案选择决策召回**

- **输入场景**: 技术负责人在飞书群发布了采用混合检索方案的决策
- **查询**: 为什么我们没有采用纯向量检索？
- **系统回答**: `[粘贴实际系统输出]`
- **命中关键词**: ✅ 混合检索、✅ 纯向量检索、✅ 关键词型问题、✅ 不稳定
- **证据 event_id**: ✅ e1
- **得分**: 1.0

---

**Case: `conflict_001` — 周报接收人变更**

- **输入**: 先说发给小王 → 后更正为发给小李
- **查询**: 项目周报现在应该发给谁？
- **系统回答**: `[粘贴实际系统输出]`
- **latest_value_accuracy**: ✅（回答包含"小李"）
- **old_value_suppression**: ✅（回答未提及"发给小王"）
- **得分**: 1.0

---

### 失败样例（分析失败原因）

**Case: `XXX_00X` — [失败场景描述]**

- **失败类型**: `[见失败分类表]`
- **实际输出**: `[系统实际输出]`
- **期望输出**: `[expected.answer_keywords]`
- **失败原因分析**: `[具体原因]`
- **修复建议**: `[针对此类失败的改进方向]`

---

## 失败分类

| 失败类型 | 说明 | 代表 case | 影响指标 | 修复建议 |
|---------|------|---------|---------|---------|
| 召回失败 | 应该召回的记忆未被召回 | `anti_00X` | recall_at_3 | 改进检索策略，增加关键词/向量双路召回 |
| 旧值泄露 | 新记忆存在但仍返回旧值 | `conflict_00X` | old_value_suppression | 加强 supersede 状态的过滤逻辑 |
| 证据缺失 | 返回了正确答案但无来源证据 | `decision_00X` | evidence_match | 确保检索结果附带 source event_id |
| 幻觉生成 | 召回了不存在的记忆 | `longterm_00X` | keyword_match | 增加置信度阈值过滤 |
| 噪声混淆 | 噪声事件被误判为有效记忆 | `anti_00X` | noise_robustness | 提升记忆价值判断阈值 |
| 偏好混用 | 将A用户偏好应用到B用户 | `preference_00X` | preference_match | 加强用户上下文隔离 |

---

## 效能量化展示

> 对应比赛文档要求的"量化展示成果"。

### CLI 命令节省对比

| 场景 | 无记忆输入字符数 | 有记忆输入字符数 | 节省率 |
|------|----------------|----------------|-------|
| pytest 命令 | 76 | 11 | **85.5%** |
| docker-compose 命令 | 66 | 10 | **84.8%** |
| 部署脚本 | 68 | 10 | **85.3%** |
| **平均** | **70** | **10.3** | **85.2%** |

### 决策召回节省沟通成本

| 场景 | 无记忆（需重新确认） | 有记忆（直接获取） | 节省 |
|------|-------------------|-----------------|------|
| 方案选型决策 | 需重开评审会（1~2小时） | 直接召回历史记忆（<3秒） | ~99% |
| 部署参数确认 | 需找运维确认（10~30分钟） | 直接从记忆获取（<3秒） | ~98% |

---

## 当前局限

> 诚实说明系统当前的不足，体现评测的客观性。

1. **v0 阶段规则判分局限**：keyword_match 无法判断语义等价（如"成本低"和"接入成本更低"），v1 将引入 Qwen30B 做语义裁判
2. **样本规模有限**：当前 mini benchmark 每类仅 5 条，统计显著性较低，v1 扩展到 30 条后结论更可靠
3. **真实飞书接入未完成**：当前测试数据为人工构造，尚未接入真实飞书群聊流量
4. **向量检索未启用**：当前检索依赖关键词匹配，向量检索接入后预期指标会进一步提升
5. **长时序测试**：跨越 6 个月以上的样例在 v0 中为模拟场景，真实长期记忆质量待验证

---

## 下一步

| 优先级 | 工作项 | 预计完成时间 |
|--------|-------|------------|
| P0 | 修复矛盾更新类失败 case（旧值泄露问题） | 下一个 Sprint |
| P0 | 扩展每类数据集到 30 条（v1） | 确认格式后 3 天内 |
| P1 | 接入 Qwen30B LLM-as-Judge | 视部署情况 |
| P1 | 补充抗干扰 hard 难度样例（噪声 50+ 条） | 下一个 Sprint |
| P2 | 接入真实飞书群聊数据做真实场景测试 | 系统联调完成后 |
