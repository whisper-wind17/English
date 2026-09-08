# Third-party Vocabulary — Minimal Learner Identity

本文件冻结 2026-09-08 起 Stage A 的简化 Identity 合约。目标是避免把“新增一个教材 occurrence”误当成“必须重新审核一个已经确定的单词”。

## 1. 核心模型

```text
Source Fact
→ MatchKey / surface
→ Learner Identity
→ [仅真实多义词] Sense Partition
→ Learner Admission
→ Stage B / Klose reconciliation
```

必须保持：

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
```

一个 Vocabulary Identity 仍然只对应一个明确 learning unit / TargetSense。

## 2. Singleton Identity — 默认路径

一个 MatchKey 只有一条 durable decision 时，Identity 内容由：

```text
Action
CanonicalMatchKey
ObjectType
TargetSense
Status
```

决定。

`OccurrenceKeys` 只作为当前 provenance / audit snapshot，不再是 semantic approval boundary。

因此：

```text
已有 reviewed singleton Identity
+ 新教材增加/减少同 MatchKey occurrence
→ 自动刷新 OccurrenceKeys provenance
→ 不重新进入 semantic review
→ 不因 evidence count 变化失效 TargetSense
```

例如：

```text
apple = 苹果
```

以后第 7/8 套教材再次出现 `apple`，直接挂到该 Identity；不再重复审核“苹果是不是苹果”。

## 3. Multipart Identity — 唯一需要 occurrence partition 的路径

只有 current source evidence 已证明同一 surface 存在两个或以上真正不同、且对小学 learner 有价值的 learning units，才建立 multipart：

```text
cold#temperature = 冷的；寒冷的
cold#illness     = 感冒

cook#person      = 厨师；厨子
cook#verb        = 做饭；烹饪
```

Multipart 继续执行严格规则：

```text
每个 subgroup OccurrenceKeys 非空
subgroup subsets disjoint
subgroup union == current occurrences 才能 release
新增/删除 source occurrence 不自动分配
partition 不完整 → MatchKey requeue / blocker
```

这部分 `OccurrenceKeys` 是 semantic truth，不是普通 provenance。

## 4. 什么时候 reopen singleton

新增 occurrence 本身不触发 reopen。只有出现明确的 Identity 风险才 reopen，例如：

- actual textbook evidence 明确出现第二个 elementary sense；
- source reconciliation 发现原判断使用了错误 source / edition；
- canonical relation 被证明错误；
- Vocabulary / Expression object boundary 被证明错误；
- 人工/模型显式将该 MatchKey 改成 `split-required`。

Dictionary 多义、POS 列表、第三方 glossary 宽义本身不构成 reopen 条件。

## 5. Form / morphology

规则/不规则词形优先 canonicalize 到 base learning unit；不要逐词重复做 Identity 研究。

```text
studied → study
carried → carry
dropped → drop#verb
does    → do
better/best → good
```

Learner Admission 独立处理。Klose 当前 past / past-participle gate 继续存在：

```text
Identity resolved
≠
current learner admitted
```

Irregular pedagogical forms（如 `children / women / men`）若已明确决定单独学习，可保留独立 Identity。

## 6. Vocabulary / Expressions

优先规则化：

```text
contraction / grammar frame / explicit slot / communicative formula
→ Expression

stable lexical word / noun phrase / phrasal verb / collocation
→ Vocabulary

one-off inflected event chunk
→ source-only
```

只有规则不能确定时进入 review。

## 7. 当前物理实现

为避免迁移 2000+ 条历史 decision，仍保留：

```text
review/identity_decisions.csv
```

以及原字段 `OccurrenceKeys`。

物理兼容策略：

```text
len(decisions for MatchKey) == 1
→ apply workflow 自动将 OccurrenceKeys 重绑 current occurrence set

len(decisions for MatchKey) > 1
→ 不自动刷新
→ 继续由 multipart exact partition 管理
```

执行入口：

```text
tools/apply_third_party_identity_decision_updates.py
```

这是 Minimal Learner Identity 合约的 machine-enforced 实现点。

## 8. Stage A / Stage B boundary

Stage A 仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run final Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
```

Stage B 才把第三方 resolved Identity 与 Klose Stable Registry 做最终 reconciliation。
