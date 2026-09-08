# Third-party Vocabulary — Stage-A Review Policy

本文件定义第三方词汇 Stage A 的正式 review policy。内容决策真源只有：

```text
anki/klose/third_party_vocabulary/review/identity_decisions.csv
```

`review_queue.csv`、`review_bundle.csv`、`decision_proposals.csv`、`defer_context.csv`、`next_batch.json` 均为 generated / derived view，不得成为第二套内容真源。

目标不是把 blocker 数字机械降到 0，而是在不破坏 Source Fact、Identity、Vocabulary / Expression 边界和 future Stage-B 的前提下，最大化可安全完成的 learner-facing identity resolution。

## 1. Review output contract

每个 active surface 一次 adjudication 必须得到明确结果：

```text
keep-identity
reuse-identity
route-expression
source-only
split-required / occurrence-partition
held + explicit audited-defer
```

一旦 deterministic planner 选定一个 batch：

```text
set(decision_updates.MatchKey)
==
set(next_batch.SelectedMatchKeys)
```

必须 `selected active batch closure = 100%`。禁止只做容易 release 的子集。

必须区分：

```text
Review throughput   = 本批完成 adjudication 的 surface 数
Net blocker release = 本批安全离开 blocker 的 surface 数
```

二者不得混为一谈。Evidence 不足时，`Net blocker release = 0` 完全可以是正确结果。

## 2. Learner-first v4 resolution

Stage A 不再把“没有 textbook sentence / Unit metadata”本身视为永久 blocker。Raw source 已验证为 flat vocabulary list；因此 review 要在可审计 Source Fact 基础上，为小学学习者选择最有价值的学习单元。

### 2.1 可直接收敛为一个 Vocabulary identity

满足以下条件之一时，可 `keep-identity`：

- source / neighborhood 明确支持一个小学核心义；
- dictionary 存在大量无关义，但小学阶段有明显高价值 core sense；
- noun / verb / adjective 等语法实现仍属于同一个紧密 learner concept；
- 固定 phrasal verb / collocation / time phrase / multiword preposition 本身是稳定可 recall 的 lexical unit；
- 某个高频 form 具有独立 pedagogical recall value，并有显式 rationale。

TargetSense 必须窄，不得把整本词典的所有义项塞进一张卡。

例如：

```text
fixed lexical phrase     → Vocabulary
explicit open-slot frame → Expression
communicative formula    → Expression
event / inflected chunk  → source-only
```

### 2.2 不得用 learner-first 覆盖真实 semantic collision

若 current source evidence 已证明同一 surface 对应两个或以上真正不同的 elementary learning units，则不得用“核心义”把它们强行压成一个 identity。

此时必须：

```text
完整 occurrence evidence 可分
→ occurrence-partitioned split

至少一个 current occurrence 无法安全归组
→ split-required + audited-defer
```

Known split 不允许为了 blocker=0 猜 occurrence。

### 2.3 Vocabulary / Expression object boundary

优先按学习对象本身判断，而不是按“是否多词”判断：

```text
稳定 lexical phrase / phrasal verb / collocation
→ Vocabulary

显式 ... / slot-bearing reusable grammar pattern
→ Expression

主要作为问候、应答、警告等 communicative formula
→ Expression

只描述一次 source event / tense-specific event chunk
→ source-only
```

“需要宾语”本身不等于 Expression；`throw away / tidy up / look at` 一类稳定 phrasal unit 可以是 Vocabulary。

## 3. Occurrence-partitioned split — FROZEN

一个 MatchKey 可以解析为多个 Stage-A provisional learning identities：

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint explicit OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional identities
```

硬约束：

```text
OccurrenceKeys                         = 非空 JSON array
同 MatchKey subgroup subsets           = disjoint
release 前 subgroup union              = current occurrences 的完整集合
任一 subgroup 未 resolved              = 整个 MatchKey 仍是 blocker
source evidence 新增/变化               = stale partition requeue
multipart keep TargetSense             = 非空
```

Multipart keep 使用：

```text
<MatchKey>#<variant>
```

例如 `dish#plate / dish#food / break#damage / look#see`。这些只是 Stage-A provisional key，不是 Stable ThirdPartyID。

Partial partition 不得进入 Preview。

## 4. Canonical / morphology / form policy

MatchKey、morphology、alias 只是 candidate evidence，不是 identity truth。

### 4.1 Canonical reuse

只有：

```text
canonical exists
AND CanonicalAction = keep-identity
AND CanonicalStatus = reviewed
AND CanonicalTargetSense 非空
AND current occurrence 与 canonical 同一 lexical sense
```

才可 `reuse-identity`。Canonical 仍是 held / split 时不得绕过。

若 canonical 已 multipart，form/alias 只能显式 reuse 到已 reviewed 的具体 subgroup，例如：

```text
broke → break#damage
drank → drink#verb
flew  → fly#verb
```

### 4.2 Inflected forms

规则/不规则过去式、过去分词、普通复数、第三人称单数等，若只是 base lexical unit 的形态实现，默认 reuse base，不 mint 新 lexical identity。

若教材把某个 form 作为有直接 recall 价值的 pedagogical unit，可以显式 `keep-identity`；必须说明 learner value，不得自动泛化为“所有 form 都独立”。

### 4.3 `-ing`

```text
transparent progressive / gerund, same lexical concept
→ reuse candidate

教材明确把 -ing surface 当稳定 activity noun/headword
→ 可独立 keep
```

不得“所有 -ing 自动 reuse”或“所有 -ing 自动 keep”。

### 4.4 Contractions / abbreviations

Grammatical contractions 默认属于 grammatical presentation / Expression object，不因缩写 mint lexical identity。

Lexical abbreviation 只有 source 能绑定一个明确小学概念时才 keep；多 expansion 或证据不足则 held。

## 5. Audited-defer zero-scan state machine — FROZEN

`defer_context.csv` 只保存 scheduling / validity metadata。至少记录：

```text
MatchKey
DecisionSignature
ContextFingerprint
DeferReasonCode
DeferDependency
PolicyVersion
```

当前 `PolicyVersion = v4-learner-first`。

`DecisionSignature` 绑定当前 durable decision metadata；`ContextFingerprint` 至少绑定：

```text
OccurrenceEvidenceJSON
CandidateCanonical / CanonicalRelation
CanonicalAction / Status / TargetSense / Definitions
CanonicalOccurrenceCount
PolicyVersion
```

状态机：

```text
decision-evidence-changed
→ 始终 active
→ 保留 last accepted context，不能提前盖章新 context

audited-defer + no accepted context
→ stamp current context
→ deferred-high-ambiguity / zero-scan

same decision + same accepted context
→ deferred-high-ambiguity / zero-scan

same decision + context changed
→ active re-review
→ 继续保留 old accepted fingerprint
→ 在 durable decision 真正复审前不得再次隐藏

durable decision changed after re-review
→ accept current context
→ 若仍 audited-defer，则重新 zero-scan
```

因此：

```text
audited-defer ≠ 未处理
audited-defer ≠ 永久忽略
```

它表示“当前 evidence 下已经完整 adjudicate；没有 context 变化时禁止重复消耗 review throughput”。

Normalizer 必须 machine-check：

- changed evidence 不能藏在 deferred；
- unchanged accepted defer 不能重新 active；
- stale-context defer 不能被隐藏；
- deferred row 必须存在匹配的 accepted decision/context fingerprint。

## 6. High-throughput execution safeguards — FROZEN

### 6.1 Deterministic planner

`tools/plan_third_party_review_batch.py` 从 normalized Review Bundle 生成：

```text
anki/klose/third_party_vocabulary/audit/next_batch.json
```

计划同时满足：

```text
SurfaceCount <= lane surface cap
AND
EvidenceWeight <= lane evidence budget
```

典型 review throughput 目标：

```text
policy-executable          60–100
actionable-semantic        40–60
semantic-review            20–40
split-resolution           20–30
object-boundary            20–30
source-reconciliation      10–15
deferred-high-ambiguity     0
```

EvidenceWeight 考虑 occurrence/source 数、split complexity、canonical dependency、evidence payload。

若无 active lane：

```text
SelectedCount  = 0
ExecutionReady = false
GateReason     = no active review batch
```

不得伪造空 batch 或重扫 unchanged defer。

### 6.2 Manifest closure

真正 decision batch 必须同时提交：

```text
review/decision_updates.csv
review/batch_manifest.json
```

Manifest 绑定：

```text
PlanVersion
ReviewLane
SelectedMatchKeys
SelectedCount
ReviewBundleFingerprint
```

`tools/check_third_party_batch_manifest.py` 强制：

```text
ExecutionReady = true
manifest set == deterministic plan set
decision_updates MatchKey set == selected set
selected active batch closure = 100%
```

少处理、额外处理、stale plan、fingerprint/lane 不一致直接 FAIL。

成功 apply 后 transient inbox / manifest 必须删除。

### 6.3 Deterministic proposals

`decision_proposals.csv` 是 derived-only、`AutoApply=no`。

Proposal 只用于机械可检查的 frozen policy，例如 reviewed canonical 上 transparent form reuse。模型/人工仍需 confirm occurrence 与 canonical 同义后，才能写 transient decision update。

Proposal guard 拦截的 row 不得饿死后续 lane。

## 7. Source mutation / decision mutation separation

Source/raw/parser/config 变化：

```text
parse + validate
→ rebuild/requeue
→ normalize/propose/plan
→ 后续独立 decision batch
```

禁止 source-changing mutation 与 `decision_updates.csv` 同 commit/workflow，避免 stale plan review 新 evidence。

Decision-only update 使用 fast path，不重新 parse 未变化 source。

Stage-A workflow 使用：

```text
concurrency group = third-party-stage-a-${ref}
cancel-in-progress = false
```

同一 branch 串行 mutation，不通过并行 bot persist 换吞吐。

## 8. Completion Recheck — mandatory

每个 batch 至少通过：

```text
TargetSense complete
source occurrence closure
explicit reviewed OccurrenceKeys
changed source evidence requeue
split subsets disjoint
split complete before release
partial split remains blocker
canonical blocker cannot be bypassed
Review Bundle closes current blockers
batch manifest closure
batch decisions persisted exactly
transient inbox removed
Klose Master/Learner/Publish/Anki untouched
Stable ThirdPartyID minted = no
Final Klose diff executed = no
```

`tools/check_third_party_corpus.py` 与 `tools/recheck_third_party_audit_batch.py` 互补，任何一个不能代替另一个。

## 9. Stage-A / Stage-B boundary

Stage A 只构建第三方 unified vocabulary corpus，不以 Klose 当前 deck 是否已有某词决定删除第三方 learning unit。

在所有计划中的 third-party source 完成前：

```text
不得做 Stage-B Klose diff
不得 mint Stable ThirdPartyID
不得修改 Klose Master/Learner/Publish/Anki
不得破坏已有 NoteID / FSRS history
```

第三方 source evidence 与 Klose learner admission 是两层不同问题。

## 10. Review quality rule

最终判断优先级：

```text
真实教材 evidence
> source neighborhood / cross-source evidence
> learner-facing elementary core concept
> morphology / dictionary / heuristic
```

Dictionary 是辅助证据，不得把明显无关的长尾义项导入 TargetSense。

当“更多 release”与“保持 identity/object/split 边界正确”冲突时，选择后者。
