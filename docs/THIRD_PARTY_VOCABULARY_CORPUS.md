# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的统一第三方教材 Vocabulary corpus。目标是把多个第三方小学英语教材词表汇总、按 **learning unit / target sense** 去重，同时严格分离：

```text
Source Fact
→ Vocabulary Identity
→ Learner Admission / Presentation
```

第三方教材来源、Identity 判断和 Klose 当前是否适合学习，是三层不同问题。

## 1. 两阶段流程

```text
Stage A — 第三方内部
多个第三方教材 Raw Vocabulary
→ 各 Source Adapter 只解析 Source Occurrence
→ 通用 candidate matching
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary Identity View
→ current Learner Admission gate
→ Klose learner-stage vocabulary view

Stage B — 所有计划第三方来源完成后
Third-party Unified Vocabulary Identity View
→ vs Klose Full Stable Identity Registry
→ identity reconciliation / new-learning-unit candidates
→ current Learner Admission gate
→ 后续学习管线
```

Stage A 不因为 Klose 当前已有某词而删除第三方 learning unit；Stage B 才执行最终 Klose identity diff。

但 **Identity resolved ≠ 当前允许学习**。例如 `went → go` 的 identity relation 可以明确，同时 `went` 因当前 grammar stage 被隔离，不进入 Klose learner-facing vocabulary。

## 2. 产品上真正重要的内容

统一第三方词源的 Identity 层关心 learning unit 本身：

```text
CanonicalWord
TargetSense
BritishIPA
AmericanIPA
Meaning
IdentityStatus
```

来源字段：

```text
SourceID / Book / Grade / Row / SourceOccurrenceKey
```

只用于追溯、重建和 source reconciliation，不直接决定学习排序、LearnerLevel 或 Anki admission。

Learner Admission 是独立层，可以依据 Klose 当前学习阶段暂缓某些已 resolved identity/form，而不改写 Source Fact 或 Vocabulary Identity。

## 3. Identity 原则

去重单位不是字符串，而是明确的 learning unit / target sense。

```text
apple = 苹果
→ 一个 Identity

bank = 银行
bank = 河岸
→ 两个 Identity

square = 正方形
square = 广场
→ 两个 Identity
```

Morphology、format alias、multiword、punctuation、substring 等只产生 candidate signal，不能自动等同 Identity。

Vocabulary / Expression / source-only chunk 必须分开，不能因为原始 XLSX 都放在“单词”列里就全部 mint Vocabulary Identity。

## 4. 当前长期架构 — FROZEN

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/occurrences.csv
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv        # Identity-level

staging/unified_vocabulary_preview.csv
+ learner/grammar_form_quarantine.csv            # durable Learner gate
→ tools/build_third_party_learner_view.py
→ learner/learner_vocabulary_preview.csv         # current Klose learner-stage view
→ learner/grammar_form_quarantine_view.csv        # generated audit view
→ tools/check_third_party_learner_view.py
```

物理路径：

```text
anki/klose/third_party_vocabulary/
├── config/
│   └── source_adapters.csv
├── review/
│   └── identity_decisions.csv
├── staging/
│   ├── occurrences.csv
│   ├── surface_candidates.csv
│   ├── review_queue.csv
│   └── unified_vocabulary_preview.csv
└── learner/
    ├── grammar_form_quarantine.csv
    ├── grammar_form_quarantine_view.csv
    └── learner_vocabulary_preview.csv
```

其中：

```text
identity_decisions.csv
= durable Identity decision truth

grammar_form_quarantine.csv
= durable current Learner Admission gate

*_preview.csv / *_view.csv
= generated / derived state
```

不得让 learner gate 反向改写 identity truth。

## 5. `identity_decisions.csv` — Identity 内容决策真源

核心字段：

```text
DecisionKey
MatchKey
OccurrenceKeys
Action
CanonicalMatchKey
ObjectType
TargetSense
Status
Confidence
DecisionBasis
Rationale
```

`Action`：

```text
keep-identity
reuse-identity
split-required
held
route-expression
source-only
pending
```

内容审校使用 transient inbox：

```text
review/decision_updates.csv
→ tools/apply_third_party_identity_decision_updates.py
→ identity_decisions.csv
→ inbox 删除
```

成功 workflow 后 transient decision inbox / manifest 不得残留。

## 6. Evidence-aware decision binding

Reviewed decision 必须绑定审校时实际覆盖的 exact `OccurrenceKeys` JSON array。

```text
current occurrence set == reviewed occurrence set
→ decision 有效

source evidence 新增/变化
→ decision-evidence-changed
→ 自动 requeue
→ stale evidence 不得进入 Identity Preview provenance
```

因此新增教材不能静默继承旧 sense 判断。

## 7. Generated Identity views

- `surface_candidates.csv`：每个 normalized surface 一行，汇总 source evidence 与派生 decision state；signal 只是证据。
- `review_queue.csv`：当前 `pending / held / split-required` 等需处理 surface；不是第二套决策真源。
- `unified_vocabulary_preview.csv`：evidence 完整、已 reviewed、Identity 层可成立的 Vocabulary candidates；尚未 mint Stable ThirdPartyID。
- Identity Preview 中任何 candidate 的 `TargetSense` 为空，workflow 必须失败。

`unified_vocabulary_preview.csv` 是 **Identity-level view**，不是 Klose 当前可学习清单。

## 8. Learner-stage grammar-form quarantine — FROZEN

Klose 当前尚未进入系统性的过去时、过去分词/完成时学习阶段。因此 pure one-word grammar forms 必须与 Identity Resolution 分层处理：

```text
went → go
broke → break#damage
ate → eat
was → be

Identity relation
→ 正常保留 / 可 resolved

Learner Admission
→ grammar-form quarantine
→ 当前不进入 learner_vocabulary_preview.csv
```

Durable gate：

```text
learner/grammar_form_quarantine.csv
```

核心字段：

```text
GateKey
MatchKey
DecisionKey
BaseForm
FormType
Scope
PolicyVersion
Rationale
```

当前 `PolicyVersion = klose-grammar-gate-v1`。

### 8.1 不能按字符串外观粗暴过滤

```text
broken = 坏的；破损的
scared = 害怕的；受惊的
lost   = 迷路的 / 丢失的
```

若当前 learning unit 已 lexicalized 为独立 adjective/noun，不因 `-ed` 或 participle 外观自动 quarantine。

普通复数、第三人称单数、`-ing` 也不属于本规则自动过滤范围。因此 `goes` 不能因为与 `went` 同属 verb morphology 就被隔离。

### 8.2 Homograph 必须按 DecisionKey 精确 gate

```text
left = 左边/左侧
→ 可保留

left = leave 的过去式
→ quarantine

saw = 锯子
→ 可保留

saw = see 的过去式
→ quarantine
```

因此 multipart/homograph 不允许 MatchKey 一刀切。

### 8.3 Quarantine 不是 blocker

```text
Identity unresolved
→ review/blocker

Identity resolved but grammar stage too early
→ learner quarantine
```

二者必须分开计数。以后 Klose grammar stage 提升，只需显式解除 learner gate；不需要重新 mint Identity，也不需要破坏 Source provenance。

## 9. Learner view machine gate

`tools/check_third_party_learner_view.py` 必须保证：

```text
gate registry referential integrity       = PASS
learner preview subset of identity preview = PASS
past-form leak into learner view          = NO
lexicalized adjective/noun over-gating    = NO
homograph decision-scope gate             = enforced
identity truth mutated by learner gate     = NO
```

Machine checker 只把 **decision-bound 明确信号** 当 hard classification；不得把第三方 dictionary/free-text `Definition` 中出现“过去式/过去分词”字样直接当 identity truth。否则会把 `go / hold / party / ground` 等 dictionary noise 误判为过去式。

## 10. 新教材标准接入方式

```text
1. 新增 Source Adapter，只输出 occurrences.csv
2. source_adapters.csv 增加 Enabled=yes
3. generic builder 合并
4. 新 surface 自动 pending
5. 已审 surface 若 occurrence evidence 变化，也自动 pending
6. 所有 Identity 内容判断只写 identity_decisions.csv
7. rebuild Identity views
8. apply current Learner Admission gate
9. core Completion Recheck + learner-view Completion Recheck
```

不复制 builder/checker，不建立 edition-specific semantic pipeline。

## 11. Current six-adapter source baseline

当前启用：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
```

当前 source/corpus 动态进度必须以 `NEXT.md` 与 repo generated state 为准，不在本文长期冻结 blocker 数字。

2026-09-08 grammar-stage gate 建立时的 validation checkpoint：

```text
Source occurrences               = 6005
Normalized surfaces              = 2161
Durable Identity decisions       = 2098
Identity-level Vocabulary Preview = 985
Learner-stage Vocabulary Preview  = 979
Grammar-form quarantine gates     = 56
Review/blocker surfaces           = 1010
```

该 checkpoint 只用于架构验证；后续 decision batch 会继续改变动态数量。

## 12. Stage B boundary

所有计划第三方来源完成前：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run final Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
```

Stage B 必须同时使用两层信息：

```text
Identity-level corpus
→ 判断“是不是同一个 learning unit / Klose 是否已有”

Learner-stage view / gate
→ 判断“这个 learning unit/form 当前是否允许进入学习管线”
```

不得直接把 Identity Preview 当作当前 Learning Admission 结果。

## 13. Source Truth 边界

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

冲突按 `docs/SOURCE_RECONCILIATION.md` 处理。
