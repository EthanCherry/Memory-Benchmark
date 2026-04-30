# LarkMemory Benchmark 指标定义

> **文档版本**: v0.1  
> **创建时间**: 2026-04-30  
> **适用阶段**: v0（规则判分）、v1（LLM-as-Judge 扩展）

---

## 1. 指标体系总览

指标分为两层：**通用指标**（所有类型都适用）和**专项指标**（特定数据集专用）。

### 1.1 维度权重

| 维度 | 权重 | 评测数据集 |
|------|------|-----------|
| 抗干扰能力 | 15% | `anti_interference` |
| 矛盾信息更新 | 15% | `contradiction_update` |
| 效率指标 | 15% | `efficiency` |
| CLI 命令记忆 | 10% | `command_memory` |
| 飞书决策记忆 | 15% | `decision_memory` |
| 个人偏好记忆 | 15% | `preference_memory` |
| 团队知识健康 | 10% | `knowledge_health` |
| 长时序记忆 | 5% | `long_term_memory` |

---

## 2. 通用指标

所有数据集类型均可使用的基础指标。

### 2.1 recall_at_1

| 属性 | 说明 |
|------|------|
| **定义** | 系统返回的第 1 条结果是否为正确记忆 |
| **判分** | 正确为 1，否则为 0（二值） |
| **公式** | `1 if correct_memory in top1_result else 0` |
| **目标** | ≥ 0.75 |
| **适用** | 所有数据集 |

### 2.2 recall_at_3

| 属性 | 说明 |
|------|------|
| **定义** | 系统返回的前 3 条结果中是否包含正确记忆 |
| **判分** | 包含为 1，否则为 0（二值） |
| **公式** | `1 if correct_memory in top3_results else 0` |
| **目标** | ≥ 0.85 |
| **适用** | 所有数据集 |
| **来源** | 借鉴 LONGMEMEVAL 的 Recall@k 设计 |

### 2.3 keyword_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答是否覆盖标准关键词 |
| **判分** | 命中关键词数 / 总关键词数 |
| **公式** | `len(hit_keywords) / len(expected.answer_keywords)` |
| **目标** | ≥ 0.80 |
| **适用** | 所有数据集 |

### 2.4 evidence_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否返回了正确的证据来源（event_id） |
| **判分** | 返回了 `expected.evidence_event_ids` 中的 event_id 则为 1 |
| **公式** | `1 if any(eid in returned_event_ids for eid in expected.evidence_event_ids) else 0` |
| **目标** | ≥ 0.80 |
| **适用** | 所有数据集 |
| **说明** | 体现系统的"可解释性"，不只给答案，还给证据 |

### 2.5 should_not_contain_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答是否避免使用了错误的旧信息 |
| **判分** | `expected.should_not_contain` 中的词均未出现则为 1 |
| **公式** | `1 if all(word not in response for word in expected.should_not_contain) else 0` |
| **目标** | ≥ 0.90 |
| **适用** | contradiction_update、anti_interference、preference_memory |

---

## 3. 专项指标

### 3.1 抗干扰专项：noise_robustness

| 属性 | 说明 |
|------|------|
| **定义** | 在加入噪声事件后，系统仍能正确召回关键记忆的能力 |
| **判分** | 等同于 `recall_at_3`，但特别标注为噪声场景 |
| **说明** | 噪声量级（easy/medium/hard）影响评分权重 |
| **目标** | hard 场景 ≥ 0.70，medium ≥ 0.85 |

### 3.2 矛盾更新专项

#### latest_value_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 冲突更新后，系统是否使用了 `expected.latest_value` 中的最新值 |
| **判分** | `expected.latest_value` 出现在回答中为 1 |
| **目标** | ≥ 0.90 |

#### old_value_suppression

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否成功抑制了旧版本的记忆，不将其作为当前有效答案 |
| **判分** | `expected.superseded_event_ids` 对应的内容未被引用为 active memory 则为 1 |
| **目标** | ≥ 0.90 |
| **说明** | 与 `should_not_contain_match` 配合使用 |

### 3.3 效能专项

#### char_saving_rate

| 属性 | 说明 |
|------|------|
| **定义** | 字符节省率：使用记忆推荐后用户需输入的字符减少比例 |
| **公式** | `1 - expected.actual_chars / expected.baseline_chars` |
| **目标** | ≥ 0.60（比赛要求量化提效） |
| **示例** | baseline=68字符，actual=10字符 → saving_rate=0.85 |

#### step_saving_rate

| 属性 | 说明 |
|------|------|
| **定义** | 步骤节省率：使用记忆后完成任务所需操作步骤减少比例 |
| **公式** | `1 - steps_with_memory / steps_without_memory` |
| **目标** | ≥ 0.50 |

### 3.4 命令记忆专项

#### top1_hit

| 属性 | 说明 |
|------|------|
| **定义** | 系统第一个推荐命令是否命中正确命令 |
| **判分** | 二值（0/1） |
| **目标** | ≥ 0.80 |

#### command_exact_match

| 属性 | 说明 |
|------|------|
| **定义** | 推荐命令与 `expected.suggested_command` 完全匹配（字符串相等） |
| **判分** | 二值（0/1） |
| **目标** | ≥ 0.70 |

### 3.5 决策记忆专项

#### decision_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统召回的决策结论是否与 `expected.decision` 语义一致 |
| **判分** | v0: keyword_match；v1: LLM judge |
| **目标** | ≥ 0.85 |

#### reason_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否正确召回了决策理由 |
| **判分** | 理由关键词是否出现在回答中 |
| **目标** | ≥ 0.80 |

#### rejected_option_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否正确识别了被否决的方案 |
| **判分** | `expected.rejected_option` 出现在回答中为 1 |
| **目标** | ≥ 0.75 |

### 3.6 偏好记忆专项

#### preference_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否正确识别并应用了用户的偏好 |
| **判分** | 偏好关键词出现在回答中 |
| **目标** | ≥ 0.85 |

#### condition_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否在正确的触发条件下应用了偏好（时间、任务类型等） |
| **判分** | 二值（0/1） |
| **目标** | ≥ 0.75 |

#### conflict_resolution_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 偏好发生冲突时，系统是否以最新显式声明为准 |
| **判分** | 等同于 `latest_value_accuracy` |
| **目标** | ≥ 0.85 |

### 3.7 知识健康专项

#### freshness_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 系统对知识新鲜度状态的判断是否准确（fresh/aging/stale/forgotten） |
| **判分** | 状态判断与 ground truth 一致为 1 |
| **目标** | ≥ 0.80 |

#### expired_memory_suppression

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否成功避免返回已过期或已废弃的知识 |
| **判分** | 过期知识未被引用为 active 则为 1 |
| **目标** | ≥ 0.90 |

#### reminder_timing_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否在合适时机发出遗忘预警（过期前合理范围内） |
| **判分** | 预警时机在合理范围内为 1 |
| **目标** | ≥ 0.75 |

### 3.8 长时序记忆专项

#### long_term_recall

| 属性 | 说明 |
|------|------|
| **定义** | 系统在跨越较长时间后（≥3个月）仍能正确召回早期记忆 |
| **判分** | 等同于 `recall_at_3`，但特别标注跨时间场景 |
| **目标** | ≥ 0.75（时间越长，容错度适当放宽） |

---

## 4. 指标汇总表

### 4.1 通用指标

| 指标 ID | 含义 | 判分方式 | v0 目标 |
|---------|------|---------|---------|
| `recall_at_1` | 第1条召回是否正确 | 规则，二值 | ≥ 0.75 |
| `recall_at_3` | 前3条中是否含正确记忆 | 规则，二值 | ≥ 0.85 |
| `keyword_match` | 关键词覆盖率 | 规则，比例 | ≥ 0.80 |
| `evidence_match` | 证据来源匹配 | 规则，二值 | ≥ 0.80 |
| `should_not_contain_match` | 旧信息不出现 | 规则，二值 | ≥ 0.90 |

### 4.2 专项指标

| 指标 ID | 适用数据集 | 含义 | v0 目标 |
|---------|-----------|------|---------|
| `noise_robustness` | anti_interference | 噪声下的召回能力 | ≥ 0.80 |
| `latest_value_accuracy` | contradiction_update, knowledge_health | 使用最新值 | ≥ 0.90 |
| `old_value_suppression` | contradiction_update, preference_memory | 抑制旧值 | ≥ 0.90 |
| `char_saving_rate` | efficiency, command_memory | 字符节省率 | ≥ 0.60 |
| `step_saving_rate` | efficiency | 步骤节省率 | ≥ 0.50 |
| `top1_hit` | command_memory | 命令推荐第1条命中 | ≥ 0.80 |
| `command_exact_match` | command_memory | 命令完全匹配 | ≥ 0.70 |
| `decision_match` | decision_memory | 决策结论匹配 | ≥ 0.85 |
| `reason_match` | decision_memory | 决策理由匹配 | ≥ 0.80 |
| `rejected_option_match` | decision_memory | 被否方案匹配 | ≥ 0.75 |
| `preference_match` | preference_memory | 偏好内容匹配 | ≥ 0.85 |
| `condition_match` | preference_memory | 触发条件匹配 | ≥ 0.75 |
| `conflict_resolution_accuracy` | preference_memory | 偏好冲突解决 | ≥ 0.85 |
| `freshness_accuracy` | knowledge_health | 新鲜度判断 | ≥ 0.80 |
| `expired_memory_suppression` | knowledge_health | 过期知识抑制 | ≥ 0.90 |
| `reminder_timing_accuracy` | knowledge_health | 遗忘预警时机 | ≥ 0.75 |
| `long_term_recall` | long_term_memory | 长时序召回 | ≥ 0.75 |

---

## 5. 评分系统

### 5.1 单样本得分

每条 case 的 `metrics` 字段列出了该 case 使用的指标列表，各指标等权平均：

```
case_score = mean(metric_score for metric in case.metrics)
```

### 5.2 数据集得分

```
dataset_score = sum(case_score for case in dataset) / len(dataset)
```

### 5.3 总分

```
total_score = sum(dataset_score * weight for dataset in all_datasets)
```

| 分数段 | 评定 |
|--------|------|
| ≥ 85 | 优秀 |
| 70~85 | 良好（及格） |
| < 70 | 待改进 |

---

## 6. v1 扩展：LLM-as-Judge 指标

当规则判分无法覆盖语义等价性时，v1 引入 Qwen30B 作为裁判模型：

```json
{
  "semantic_correctness": 0.9,
  "uses_latest_memory": 1,
  "evidence_supported": 1,
  "hallucination": 0,
  "reasoning_quality": 0.85,
  "comment": "回答正确使用了最新记忆，包含原始决策理由，无幻觉。"
}
```

| LLM judge 字段 | 含义 | 取值范围 |
|---------------|------|---------|
| `semantic_correctness` | 回答语义是否正确 | 0.0~1.0 |
| `uses_latest_memory` | 是否使用最新记忆 | 0 或 1 |
| `evidence_supported` | 是否有证据支撑 | 0 或 1 |
| `hallucination` | 是否存在幻觉内容 | 0（无）或 1（有） |
| `reasoning_quality` | 推理过程质量 | 0.0~1.0 |
