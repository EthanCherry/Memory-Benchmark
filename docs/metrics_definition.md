# LarkMemory Benchmark 指标定义

> **文档版本**: v0.2  
> **创建时间**: 2026-04-30  
> **适用阶段**: v0（规则判分）、v1（LLM-as-Judge 扩展）

---

## 1. 指标体系总览

指标分为两层：**通用指标**（所有方向都适用）和**测试类型专项指标**。

### 1.1 方向权重

| 方向 Benchmark | 权重 | 对应比赛方向 |
|---------------|------|------------|
| command_memory | 15% | 方向 A：CLI 命令记忆 |
| decision_memory | 30% | 方向 B：飞书决策记忆 |
| preference_memory | 25% | 方向 C：个人偏好记忆 |
| knowledge_health | 30% | 方向 D：团队知识健康 |

### 1.2 评分公式

```
方向得分 = 该方向所有 case 指标得分的加权平均
总分 = Σ (方向得分 × 方向权重) × 100

评级：
  优秀：≥ 85 分
  良好：70~85 分
  待改进：< 70 分
```

---

## 2. 通用指标

适用于所有方向和测试类型。

### 2.1 recall_at_3

| 属性 | 说明 |
|------|------|
| **定义** | 系统返回的前 3 条结果中是否包含正确记忆 |
| **判分** | 包含为 1，否则为 0（二值） |
| **公式** | `1 if correct_memory in top3_results else 0` |
| **目标** | ≥ 0.85 |
| **适用** | 所有方向 |
| **来源** | 借鉴 LONGMEMEVAL (ICLR 2025) 的 Recall@k 设计，MemBench (ACL 2025) 同样采用类似召回指标 |

### 2.2 keyword_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答中命中标准关键词的比例 |
| **判分** | `len(matched_keywords) / len(expected_keywords)` |
| **目标** | ≥ 0.80 |
| **适用** | 所有方向 |

### 2.3 evidence_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统返回结果是否包含原始事件证据 |
| **判分** | 返回的 evidence 中包含 expected_event_id 为 1 |
| **目标** | ≥ 0.80 |
| **适用** | 所有方向（contradiction_update 类要求返回最新证据） |

### 2.4 should_not_contain_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答中是否避免了错误/过时信息 |
| **判分** | 未出现任何 should_not_contain 中的字符串为 1 |
| **目标** | ≥ 0.90 |
| **适用** | 所有方向（矛盾更新、知识废弃类必检） |

---

## 3. 测试类型专项指标

### 3.1 anti_interference（抗干扰）

#### noise_robustness

| 属性 | 说明 |
|------|------|
| **定义** | 加入噪声后系统是否仍能召回正确记忆 |
| **判分** | `recall_at_3 的得分在加入噪声后是否保持 ≥ 原始得分的 80%` |
| **目标** | ≥ 0.80 |
| **适用** | command_memory, decision_memory, preference_memory, knowledge_health |

### 3.2 contradiction_update（矛盾更新）

#### latest_value_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 冲突更新后，系统返回的是否为最新值 |
| **判分** | `1 if response contains latest_value else 0` |
| **目标** | ≥ 0.90 |
| **适用** | decision_memory, preference_memory, knowledge_health |

#### old_value_suppression

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否不再使用已被覆盖的旧值 |
| **判分** | `1 if none of should_not_contain strings appear in response` |
| **目标** | ≥ 0.90 |
| **适用** | decision_memory, preference_memory, knowledge_health |

### 3.3 efficiency（效能验证）

#### char_saving_rate

| 属性 | 说明 |
|------|------|
| **定义** | 使用记忆推荐后用户输入字符的节省比例 |
| **判分** | `1 - actual_chars / baseline_chars` |
| **目标** | ≥ min_saving_rate（通常 0.5~0.8） |
| **适用** | command_memory, decision_memory, preference_memory |

#### step_saving_rate

| 属性 | 说明 |
|------|------|
| **定义** | 使用记忆后操作步骤的减少比例 |
| **判分** | `1 - actual_steps / baseline_steps` |
| **目标** | ≥ 0.50 |
| **适用** | command_memory, preference_memory |

### 3.4 长时序保持

#### long_term_recall

| 属性 | 说明 |
|------|------|
| **定义** | 跨时间跨度后是否仍能召回早期关键记忆 |
| **判分** | `recall_at_3 得分，但仅统计 time_span_days > 30 的 case` |
| **目标** | ≥ 0.70 |
| **适用** | decision_memory, knowledge_health |

### 3.5 命令记忆专项

#### top1_hit

| 属性 | 说明 |
|------|------|
| **定义** | 第一条推荐结果是否为正确命令 |
| **判分** | `1 if top1_result == expected_command else 0` |
| **目标** | ≥ 0.85 |
| **适用** | command_memory |

#### command_exact_match

| 属性 | 说明 |
|------|------|
| **定义** | 推荐命令是否与期望完全一致（含参数） |
| **判分** | `1 if exact match else 0` |
| **目标** | ≥ 0.70 |
| **适用** | command_memory |

### 3.6 决策记忆专项

#### decision_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答是否包含正确的决策结论 |
| **判分** | `1 if decision keyword present else 0` |
| **目标** | ≥ 0.85 |
| **适用** | decision_memory |

#### reason_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答是否包含正确的决策理由 |
| **判分** | `1 if reason keyword present else 0` |
| **目标** | ≥ 0.80 |
| **适用** | decision_memory |

#### rejected_option_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统回答是否正确识别被否决的方案 |
| **判分** | `1 if rejected_option correctly identified else 0` |
| **目标** | ≥ 0.75 |
| **适用** | decision_memory |

### 3.7 偏好记忆专项

#### preference_match

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否正确应用用户的偏好设置 |
| **判分** | `1 if preference correctly reflected in response else 0` |
| **目标** | ≥ 0.85 |
| **适用** | preference_memory |

#### condition_match

| 属性 | 说明 |
|------|------|
| **定义** | 偏好条件（如时间段、场景）是否正确匹配 |
| **判分** | `1 if condition correctly applied else 0` |
| **目标** | ≥ 0.80 |
| **适用** | preference_memory |

### 3.8 知识健康专项

#### expired_memory_suppression

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否不再使用已过期/废弃的知识 |
| **判分** | `1 if expired knowledge not cited as active else 0` |
| **目标** | ≥ 0.90 |
| **适用** | knowledge_health |

#### freshness_accuracy

| 属性 | 说明 |
|------|------|
| **定义** | 系统是否返回最新版本的知识 |
| **判分** | `1 if latest knowledge version returned else 0` |
| **目标** | ≥ 0.85 |
| **适用** | knowledge_health |

---

## 4. 判分阶段

### 4.1 v0：规则判分

优先使用规则判断，保证可复现：
1. 是否召回 expected.evidence_event_ids 中的事件
2. 回答是否包含 expected.answer_keywords
3. 回答是否不包含 expected.should_not_contain
4. 矛盾更新类是否使用 latest_value
5. 效率类是否达到 min_saving_rate

### 4.2 v1：LLM-as-Judge

接入 Qwen30B 进行语义等价判断，适用于：
- 同义不同表述的决策理由匹配
- 隐式偏好的正确性判断
- 回答是否存在幻觉
- 语义层面的旧值抑制判断
