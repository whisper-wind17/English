# Third-party Vocabulary — Learner-first Final Blocker Resolution

本文件定义 Third-party Vocabulary Stage A 在拿不到教材正文时的最终 blocker 处理规则。它用于终结 `held / split-required`，不改变 Source Fact 真源，也不替代 `identity_decisions.csv` 作为唯一内容决策真源。

## 1. 核心目标

Stage A 的目标不是还原每本第三方教材当时究竟用了词典中的哪一个义项，而是形成一个适合 Klose 后续学习的、可追溯的 elementary learning-unit corpus。

因此必须区分：

```text
Source Fact               = 第三方词表实际出现了什么 surface / gloss / book / row
Learner-facing Identity   = 小学阶段值得独立学习的 core sense / phrase / pedagogical form
```

Source evidence 足够时优先使用；source evidence 不足且拿不到教材正文时，不得把 blocker 永久留在 `held`。

## 2. Learner-first fallback — FROZEN

当 source glossary / neighborhood 不能唯一确定义项时，按以下顺序处理：

```text
1. 选择小学阶段最高价值、最高频、最可教学的 core sense；
2. TargetSense 保持窄而清楚，不抄完整词典义项；
3. 需要消歧时，后续 Learner Presentation 使用 phrase / example sentence 承载语境；
4. multiword 若本身是自然且有学习价值的固定表达，可直接 keep-identity；
5. 只有两个语义明显不同、且小学阶段都值得独立 recall 的义项，才 split；
6. dictionary 中存在其他低频/POS 义项，不构成 blocker；
7. 无学习价值的 source/event chunk 才 source-only；完整交际句/功能表达才 route-expression。
```

例：

```text
about      → 关于
back       → 背部；后面
board      → 上车；登机
American   → 美国的；美国人
Australian → 澳大利亚的；澳大利亚人
all over   → 到处；遍及
```

这些 TargetSense 可以在后续卡片背面用例句进一步消歧，不要求 Stage A 重建原教材原句。

## 3. Phrase policy

不要因为 surface 是 multiword 就默认 object-boundary blocker。

如果一个 phrase：

```text
- 小学阶段自然常用；
- 可以作为一个整体理解/回忆；
- 后续能用例句稳定呈现；
```

则可以直接 `keep-identity`。

例如：

```text
a lot      → 很；非常 / 许多（按选定 core use 呈现）
all over   → 到处；遍及
get through → 通过；完成
in one hour → 一小时后 / 在一小时内（按 learner-facing use 选一个）
keep on    → 继续
out of     → 从……出来；离开
```

完整句子、课堂口令、问答模板仍属于 Expressions。

## 4. Semantic split policy

Split 从“只要可能多义就拆”收紧为：

```text
两个义项语义距离明显
AND
两个义项都在小学阶段具有独立学习价值
AND
合并后会让一张卡无法明确回答
```

才创建多个 learning units。

否则只保留一个 learner-first core sense；未来真实学习/教材需要第二义项时，再新增 identity。

典型真正值得 split 的例子：

```text
bank = 银行 / 河岸
```

而 nationality adjective + person noun、普通名词/动词的紧密概念簇，不要求机械 split。

## 5. Pedagogically salient form policy

词形是否保留独立 learning unit，不只由 lexical lemma 决定，还看是否需要独立 recall。

```text
规则透明词形：played / cleaned 等
→ 默认 reuse base，除非已 lexicalized

小学高频不规则/比较级/最高级或稳定形容词：
better / best / were / was / pleased / lost / sweets 等
→ 若独立记忆价值明显，可 keep-identity
```

这类 `keep-identity` 必须：

```text
Status        = reviewed
TargetSense   = 非空、learner-facing
DecisionBasis = 含 learner-first 或 pedagogical marker
Rationale     = 说明为什么独立 recall 有价值
```

## 6. Finalization state machine

在本阶段：

```text
held / split-required
→ 必须重新进入 active review
→ learner-first resolve
→ keep / reuse / route-expression / source-only / complete split
```

`deferred-high-ambiguity` 不再是 Stage-A 终态。

允许因为单批尚未处理而暂时存在 blocker；不允许在 Stage-A Exit 时仍把“无教材正文”作为永久 held 理由。

## 7. Stage-A Exit Gate

所有 planned third-party adapters 完成后，进入 Stage B 前必须满足：

```text
pending                    = 0
held                       = 0
unresolved split-required  = 0
review_queue               = 0
Vocabulary Preview TargetSense complete = 100%
```

只有 resolved actions 可以离开 Stage A：

```text
keep-identity
reuse-identity
route-expression
source-only
complete reviewed multipart split
```

`reviewed` 只表示“看过”；`resolved` 才表示“可以进入下一阶段”。二者不得混用。

## 8. Validation

每批 learner-first finalization 仍必须遵守 `AGENTS.md`：

```text
IMPLEMENTED → VALIDATED → CHECKPOINTED
```

并至少检查：

```text
- selected batch closure = 100%
- learner-first keep 必须有非空 TargetSense
- 旧 semantic/form guards 不得被无 marker 随意绕过
- source occurrence / provenance 不丢失
- canonical reuse 不绕过 blocker
- Preview 无重复 identity / 空 TargetSense
- Klose Master/Learner/Publish/Anki 不被 Stage A 修改
```
