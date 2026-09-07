# Third-party Vocabulary — High-throughput Review Policy

本文件只定义 Stage-A blocker 审计的批处理策略与类级 policy。它不改变 Source/Identity 真源边界：`identity_decisions.csv` 仍是唯一内容决策真源，`review_queue.csv` / `review_bundle.csv` 都是 derived views。

## 1. Batch review contract

默认不再采用 2–3 个词一个 workflow 的微批次。

```text
每批扫描 blocker        = 30–50
目标有效 refinement     = 10–25（证据允许时可更高）
每批 decision_updates   = 1 次
每批 Stage-A workflow   = 1 次
每批 Completion Recheck = 1 次 core + 1 次 batch-aware
每批完成后              = 立即更新 NEXT.md
```

吞吐提升不能通过降低内容门槛实现。仍遵守：

```text
source context 明确单一 elementary learning unit → keep-identity
多个真实 source-level learning units            → split-required
对象应属于 Expressions                           → route-expression
仅为 source/event chunk                          → source-only
证据不足 / policy 未满足                         → held
```

## 2. Review Bundle

`staging/review_bundle.csv` 是 generated audit aid，一行一个当前 blocker，按 AuditPriority 排序，包含：

```text
BlockerClass / AuditPriority
当前 DecisionAction / Status / Confidence / Basis / Rationale
Definitions / CandidateSignals / SourceIDs / SourceBooks
所有 active SourceOccurrenceKey
每个 occurrence 同书前后各 8 个 source words
```

用途是让一次模型上下文直接覆盖 30–50 个 blocker，避免逐词反复 GitHub lookup。它不允许被手工编辑，也不能反向覆盖 `identity_decisions.csv`。

## 3. Blocker classes

```text
semantic-easy             priority 10
semantic-cross-source     priority 20
split-resolution          priority 30
semantic-hard             priority 40
multiword-object-boundary priority 45
form-policy               priority 60
abbreviation-policy       priority 70
functional-polysemy       priority 80
```

审计顺序默认从低 priority 到高 priority。目的不是优先“容易降 blocker 数量”，而是先处理证据充分且决策成本低的内容，再把系统性 policy blocker 与真正高歧义词分离。

## 4. Irregular / inflected-form policy

原则：**词形不是新的 lexical sense。**

- 规则/不规则过去式、过去分词、普通复数、第三人称单数等，若只是 base lexical unit 的形态实现，默认不 mint 新 Vocabulary identity。
- 当 base surface 已存在、其 target sense 已 reviewed 且 source occurrence 与其语义一致时，可 `reuse-identity → base`。
- 若 base identity 仍被 semantic blocker 阻塞，form 不得绕过 canonical blocker；继续 held，直到 base resolved。
- 若教材把某 form 作为具有独立记忆价值的明确 pedagogical learning unit，允许显式例外；必须有 rationale，不通过 morphology 自动决定。
- 已冻结的 pedagogical exceptions（如当前系统明确保留的 `women`）不因本 policy 被自动重写。

因此，`won / wrote / ate / bought / came / rode / swam ...` 不再逐词重新讨论“是不是过去式”；只需要检查：base 是否存在、base sense 是否已冻结、该 occurrence 是否同义。其余属于机械 policy application。

## 5. `-ing` / activity policy

不能把所有 `-ing` 都视为 form，也不能把所有 `-ing` 都视为独立词。

- 透明进行时/动名词形态，仅表达 base verb 同一 lexical concept → 默认 form alias / reuse candidate。
- 教材把 `-ing` surface 作为独立 headword，并在活动/运动类别中作为稳定 activity noun 使用 → 可保留独立 Vocabulary learning unit。
- `hiking`、`boating` 属于已由 source context 确认的 lexicalized activity units；它们不是“所有 -ing 自动 keep”的先例。
- `cycling / dancing / reading / running ...` 按同一规则审 evidence，不因词尾自动释放或自动 collapse。

## 6. Abbreviation / contraction policy

分两类处理：

### 6.1 Grammatical contractions

`won't / you'll / you're / where's / wouldn't ...` 是 grammatical presentation forms，不因缩写形式本身 mint 新 lexical identity。

- expansion/canonical object 已明确且可复用 → reuse candidate；
- canonical/object boundary 仍未冻结 → held；
- 不允许用错误 dictionary gloss 把 contraction 解释成无关 lexical sense。

### 6.2 Lexical abbreviations

`CD / a.m. / p.m. / PS / RSVP ...` 只有在 source context 能明确绑定一个小学 learning unit 时才释放。

- 单一、稳定且教材明确教授的 abbreviation concept 可 keep-identity；
- 多 expansion / source context 不足 → held；
- 实际是 communicative instruction/formula 的，可 route-expression。

## 7. Fast workflow path

Decision-only 更新不需要重新 parse 未变化的教材 source。

```text
Source/raw/parser/config changed
→ parse + validate all affected adapters
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
Klose Master/Learner/Publish/Anki untouched
```

## 8. Batch-aware Completion Recheck

`tools/recheck_third_party_audit_batch.py` 在 apply 前 capture 本批 transient decisions，在 build 后 verify：

- 每个 intended DecisionKey 已持久化；
- action/status/TargetSense/basis/rationale 与本批输入一致；
- keep-identity 已进入 Preview；
- held/split/pending 仍在 review queue；
- route-expression/source-only 不泄漏到 Preview；
- reuse 不绕过 canonical blocker；
- Preview TargetSense 全非空；
- transient inbox 已删除。

该检查补充 `tools/check_third_party_corpus.py`，不替代 core Completion Recheck。
