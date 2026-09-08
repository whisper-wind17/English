# Third-party Vocabulary — Stage-A Review Policy

本文件定义第三方 Vocabulary Stage A 的正式 review policy。2026-09-08 起采用 **Minimal Learner Identity**：普通 singleton Identity 不再因新增教材 occurrence 自动失效；只有真正多义词的 sense partition 继续绑定 occurrence。

详细数据模型：

```text
docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
```

## 1. Review 的目标

Review 只解决真正需要判断的问题：

```text
new MatchKey
true learner-relevant polysemy
multipart sense assignment
canonical relation ambiguity
Vocabulary / Expression boundary
source reconciliation conflict
```

以下情况不再进入 semantic review：

```text
已有 reviewed singleton Identity
+ 同 MatchKey 新增/减少教材 occurrence
```

这类 occurrence provenance 由 workflow 自动刷新。

## 2. Review output

每个 active MatchKey 必须明确为：

```text
keep-identity
reuse-identity
route-expression
source-only
split-required
held
pending
```

目标不是 blocker 数字机械归零，而是把普通词快速收敛，把模型/人工时间只留给真实语义冲突。

## 3. Default learner-core policy

Stage A 不建立完整 dictionary sense inventory。

默认：

```text
一个 surface
→ 一个明确、适龄、教材支持的 learner core sense
```

Dictionary 中存在其它义项不构成 blocker。只有 actual textbook evidence 已出现第二个独立 elementary learning unit，才 split。

例如：

```text
capital
教材只在 country / map / language 语境
→ 首都

以后教材真的出现 capital letter
→ reopen → split
```

## 4. Multipart split — 严格路径

当 current source evidence 已证明两个以上真实 learner senses：

```text
one MatchKey
+ multiple decision rows
+ explicit OccurrenceKeys subsets
→ provisional sense identities
```

硬约束：

```text
每个 subgroup OccurrenceKeys 非空
subsets disjoint
union == current occurrence set 才能 release
TargetSense 非空
keep subgroup 使用 MatchKey#variant
新增/删除 occurrence 不自动归组
partition 不完整 → blocker
```

因此 occurrence-level 精细审核只保留在 multipart。

## 5. Singleton binding — 自动路径

一个 MatchKey 只有一条 durable decision 时：

```text
Identity content = Action + Canonical + ObjectType + TargetSense + Status
OccurrenceKeys   = current provenance snapshot
```

workflow 每次自动：

```text
singleton OccurrenceKeys := current enabled occurrence set
```

新增/删除 occurrence 不重审 TargetSense。

实现：

```text
tools/apply_third_party_identity_decision_updates.py
```

## 6. Canonical / morphology

优先规则化，不逐词重复审核：

```text
regular/irregular inflection → base Identity
orthographic alias           → canonical Identity
transparent abbreviation     → reviewed canonical Identity
```

若 canonical 已 multipart，必须显式指向具体 subgroup：

```text
broke   → break#damage
drank   → drink#verb
flew    → fly#verb
dropped → drop#verb
```

不得绕过 unresolved multipart canonical。

## 7. Learner Admission 独立

Identity resolved 不等于 Klose 当前学习。

当前 pure one-word past / past-participle 等继续由：

```text
learner/grammar_form_quarantine.csv
```

隔离。

```text
studied → study          # Identity
studied → quarantine     # Learner Admission
```

Lexicalized adjective/noun 不因 `-ed` 外观自动 gate；homograph 必须 DecisionKey-scoped。

## 8. Vocabulary / Expression boundary

优先 deterministic rule：

```text
contraction
explicit slot-bearing grammar frame
communicative formula
→ Expression

stable lexical word / noun phrase / phrasal verb / collocation
→ Vocabulary

one-off tense/event chunk
→ source-only
```

只有规则不能确定时进入 object-boundary review。

## 9. Review queue priority

简化后优先级：

```text
1. split-resolution / multipart evidence change
2. new object-boundary MatchKeys
3. new semantic MatchKeys
4. source reconciliation
5. audited defer
```

不再建立大规模 `evidence-revalidation` 人工 lane；singleton additive evidence 已从架构上取消重复审核。

现有 v5 delta tooling 可以继续作为兼容机制，但不再是正常 singleton source-expansion 的必要路径。

## 10. Batch execution

仍保持：

```text
next_batch.json
→ selected-only review packet/view
→ decision_updates.csv
→ apply
→ corpus build/check
→ learner build/check
→ audit recheck
→ Klose isolation
→ bot persist
```

对于真实 decision batch：

```text
planner selected set == submitted MatchKey set
selected batch closure = 100%
source mutation 与 decision mutation 不混合
```

## 11. Completion Recheck

Stage A 必须继续验证：

```text
source occurrence closure
TargetSense complete
singleton provenance current
multipart subsets disjoint
multipart complete before release
partial split remains blocker
canonical blocker bypass = NO
learner grammar gate integrity
past-form leak = NO
Klose Master/Learner/Publish/Anki untouched
Stable ThirdPartyID minted = NO
Stage-B Klose diff executed = NO
```

CI success 是证据，但较大架构修改仍需独立 diff / state-transition recheck。

## 12. Stage A boundary

在所有计划第三方来源完成前：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run final Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
```
