# Third-party Vocabulary — High-throughput Review Policy

本文件定义 Stage-A blocker 审计的批处理策略与类级 policy。它不改变 Source/Identity 真源边界：`identity_decisions.csv` 仍是唯一内容决策真源；`review_queue.csv`、`review_bundle.csv`、`decision_proposals.csv` 都是 generated/derived views。

## 1. Batch review contract

不再采用 2–3 个词一个 workflow 的微批次，也不再给所有 blocker 使用同一 batch size。

```text
policy-executable          = 60–100 / batch
actionable-semantic        = 40–60 / batch
semantic-review            = 20–40 / batch
split-resolution           = 20–30 / batch
object-boundary            = 20–30 / batch
source-reconciliation      = 10–15 / batch
deferred-high-ambiguity    = 0 / default scan
```

每个独立批次仍然只允许：

```text
1 个 decision_updates.csv
1 次 Stage-A workflow
1 次 core Completion Recheck
1 次 batch-aware Completion Recheck
1 次 independent sample/high-risk/diff recheck
完成后立即更新 NEXT.md
```

吞吐提升不能通过降低内容门槛实现。仍遵守：

```text
source context 明确单一 elementary learning unit → keep-identity
多个真实 source-level learning units            → split-required / occurrence partition
对象应属于 Expressions                           → route-expression
仅为 source/event chunk                          → source-only
证据不足 / policy 未满足                         → held
```

## 2. Review Bundle v2

`anki/klose/third_party_vocabulary/audit/review_bundle.csv` 是 generated audit aid，一行一个当前 blocker。除原有 source neighborhood 外，v2 还直接提供：

```text
ActionabilityScore
ReviewLane
RecommendedBatchSize
BlockerClass
CandidateCanonical
CanonicalExists
CanonicalAction / CanonicalStatus
CanonicalTargetSense
CanonicalDefinitions
CanonicalOccurrenceCount
PolicyRecommendedAction
DeferReason
所有 active SourceOccurrenceKey
每个 occurrence 同书前后各 8 个 source words
```

Review Bundle 必须与 `review_queue.csv` MatchKey 集合完全闭合；不允许出现缺项或额外项。

### 2.1 Actionability

`semantic-easy` 不再仅凭“single source + single occurrence”决定执行优先级。Actionability 结合：

```text
正向：单一 POS / source context 可读 / canonical 已 reviewed / evidence 一致
负向：多 POS / 多小学义项 / 当前 rationale 明示 evidence insufficient /
      source-gloss conflict / functional polysemy / unresolved canonical
```

分数只是 review scheduling 信号，不是内容真源，不得自动产生 identity decision。

### 2.2 Execution lanes

当前 derived lane：

```text
policy-executable             # frozen policy + reviewed canonical，可快速确认
policy-review                 # policy 已冻结，但 occurrence/object boundary 仍需判断
actionable-semantic           # 高 actionability semantic review
semantic-review               # 普通 semantic review
split-resolution              # 已知 occurrence-level 多义
object-boundary               # multiword / Vocabulary vs Expression/source-only
source-reconciliation-needed  # glossary/source evidence 冲突
deferred-high-ambiguity       # 无新 evidence 时默认不重复扫描
```

`deferred-high-ambiguity` 的意义是减少重复推理，不等于永久放弃；source evidence 或 policy 变化后可以重新进入 active lane。

## 3. Canonical evidence rule

对于 form / alias blocker，Review Bundle 必须直接展示 canonical current state，避免模型第二次 lookup：

```text
CandidateCanonical
CanonicalAction
CanonicalStatus
CanonicalTargetSense
CanonicalDefinitions
CanonicalOccurrenceCount
```

只有：

```text
canonical exists
AND CanonicalAction = keep-identity
AND CanonicalStatus = reviewed
AND occurrence 与 canonical 是同一 lexical sense
```

才可以把 form proposal 确认为 `reuse-identity`。canonical 仍是 held/split/pending 时严禁绕过 blocker。

## 4. Deterministic policy proposal engine

`tools/propose_third_party_policy_decisions.py` 读取 Review Bundle，生成：

```text
anki/klose/third_party_vocabulary/audit/decision_proposals.csv
```

Proposal 只针对机械可检查的 frozen-policy 情况，例如 reviewed canonical 上的 transparent inflected/form reuse。

硬规则：

```text
decision_proposals.csv = derived-only
AutoApply               = no
ReviewMode              = confirm-or-reject
proposal 必须显式包含当前 OccurrenceKeys
proposal canonical 必须 reviewed keep-identity + 非空 TargetSense
proposal 不得写 identity_decisions.csv
proposal 不得写 decision_updates.csv
```

模型/人工仍需依据 occurrence evidence 确认“该 occurrence 与 canonical 同义”，确认后才可转换成 transient `decision_updates.csv`。

## 5. Irregular / inflected-form policy

原则：**词形不是新的 lexical sense。**

- 规则/不规则过去式、过去分词、普通复数、第三人称单数等，若只是 base lexical unit 的形态实现，默认不 mint 新 Vocabulary identity。
- 当 base surface 已存在、target sense 已 reviewed 且 source occurrence 与其语义一致时，可 `reuse-identity → base`。
- 若 base identity 仍被 semantic blocker 阻塞，form 不得绕过 canonical blocker。
- 若教材把某 form 作为具有独立记忆价值的明确 pedagogical learning unit，允许显式例外；必须有 rationale。
- 已冻结 pedagogical exception（例如 `women`）不因 proposal engine 被自动重写。

因此 `won / wrote / ate / bought / came / rode / swam ...` 不再逐词重新讨论“是不是过去式”；只检查 canonical readiness + occurrence same-sense。

## 6. `-ing` / activity policy

不能把所有 `-ing` 都视为 form，也不能把所有 `-ing` 都视为独立词。

- 透明进行时/普通动名词，仅表达 base verb 同一 lexical concept → form/reuse candidate。
- 教材把 `-ing` surface 作为独立 headword，并在活动/运动类别中作为稳定 activity noun → 可保留独立 Vocabulary learning unit。
- `hiking / boating / reading / running / singing` 是 evidence-based 个案，不是“所有 -ing 自动 keep”。
- Review Bundle 检测到 hobby/activity neighborhood 时，必须进入 `policy-review`，不得由 deterministic proposal engine 自动 reuse。

## 7. Abbreviation / contraction policy

### 7.1 Grammatical contractions

`won't / you'll / you're / where's / wouldn't ...` 是 grammatical presentation forms，不因缩写本身 mint 新 lexical identity。

- expansion/canonical object 已明确且可复用 → reuse candidate；
- canonical/object boundary 未冻结 → held / policy-review；
- 不允许使用错误 dictionary gloss 定义 contraction。

### 7.2 Lexical abbreviations

`CD / a.m. / p.m. / PS / RSVP ...` 只有 source context 能明确绑定一个小学 learning unit 时才释放。

- 单一、稳定且教材明确教授的 abbreviation concept → keep-identity；
- 多 expansion / source context 不足 → held；
- communicative instruction/formula → route-expression。

## 8. Fast workflow path

Decision-only 更新不重新 parse 未变化教材 source。

```text
Source/raw/parser/config changed
→ parse + validate affected adapters
→ apply decisions
→ build corpus
→ core recheck

Only decision_updates / identity decisions changed
→ reuse committed adapter occurrences
→ apply decisions
→ build corpus
→ core recheck
```

无论 fast path 还是 source path，以下门禁不变：

```text
TargetSense complete
source occurrence closure
explicit OccurrenceKeys
changed evidence requeues
canonical blocker cannot be bypassed
Review Bundle closes over current blockers
policy proposals never auto-apply
Klose Master/Learner/Publish/Anki untouched
```

## 9. Batch-aware Completion Recheck

`tools/recheck_third_party_audit_batch.py` 在 apply 前 capture transient decisions，在 build 后 verify：

- 每个 intended DecisionKey 已持久化；
- action/status/TargetSense/basis/rationale 与本批输入一致；
- explicit `OccurrenceKeys` subset 与 durable decision 完全一致；
- single keep-identity 已进入 Preview；
- held/split/pending 仍在 review queue；
- route-expression/source-only 不泄漏到 Preview；
- reuse 不绕过 canonical blocker；
- multipart decision 按 MatchKey 整体验证，不把 subgroup 当成完整 surface；
- complete reviewed multipart 的 keep/reuse provenance 正确进入 Preview；
- unresolved multipart 不得逃离 review queue；
- Preview TargetSense 全非空；
- transient inbox 已删除。

该检查补充 `tools/check_third_party_corpus.py`，不替代 core Completion Recheck。

## 10. Occurrence-partitioned split policy

Stage A 已正式支持一个 normalized `MatchKey` 解析成多个 provisional learning identities。

```text
one MatchKey
+ multiple reviewed decision rows
+ occurrence-partitioned evidence
→ multiple provisional Stage-A identities
```

硬约束：

```text
每个 decision 的 OccurrenceKeys    = 非空 explicit JSON subset
同一 MatchKey 各 subset            = disjoint，不允许 overlap
完整解除 split blocker 前           = union 必须覆盖全部 current occurrences
任一 subgroup 未 reviewed/resolved  = 整个 MatchKey 仍是 blocker
新增 source evidence 导致 cover 变化 = requeue，不静默沿用旧 partition
multipart keep TargetSense          = 必须非空
```

Multipart `keep-identity` 使用现有 `CanonicalMatchKey` 存放 Stage-A scoped provisional key：

```text
<MatchKey>#<variant>
```

例如：

```text
dish#plate
dish#food
cut#verb
cut#injury
dream#aspiration
dream#sleep
```

这些 key 只是 Stage-A provisional identity scope，**不是 Stable ThirdPartyID**，不得提前进入 Stage B 或 Klose Stable Registry。

Multipart `reuse-identity` 仍指向现有 reviewed canonical，并继续受 canonical blocker rule 约束。`route-expression` / `source-only` 可以作为某个 occurrence subgroup，但只有整个 partition complete 且所有 subgroup resolved 后，Source MatchKey 才能退出 review。

### 10.1 Preview materialization

完整 partition 后：

- 每个 multipart keep subgroup 生成一条独立 Preview row；
- `ProvisionalIdentityKey = candidate:<MatchKey>#<variant>`；
- `CanonicalMatchKey = <MatchKey>#<variant>`；
- `SourceOccurrenceCount` 只统计该 subgroup；
- `SourceMatchKeys` 保留原始 Source MatchKey provenance；
- multipart reuse 合并到 reviewed canonical，不新建重复 identity。

partial partition 不进入 multipart Preview，仍留在 review queue。

### 10.2 Frozen smoke baseline

首个真实 smoke 已通过：

```text
dish  → dish#plate / dish#food
cut   → cut#verb / cut#injury
dream → dream#aspiration / dream#sleep
```

结果：

```text
resolved multipart surfaces = 3
blockers                    200 → 197
Vocabulary Preview          1615 → 1621
```

core checker、batch checker、TargetSense gate、Klose isolation 均 PASS。该能力因此从“待实现 architecture task”升级为正式 Stage-A review mechanism。
