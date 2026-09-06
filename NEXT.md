# NEXT — Klose Learning

Last updated: 2026-09-06

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前第三方 Vocabulary corpus 任务继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
```

涉及 Klose 实际教材 reconciliation 时再读取：

```text
docs/SOURCE_RECONCILIATION.md
```

Expressions 任务读取：

```text
docs/EXPRESSIONS_SYSTEM.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Vocabulary operational baseline

Grade-4 Vocabulary 已闭环并正常学习：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

完整 Klose Stable Vocabulary Identity Registry：

```text
note_registry.csv + note_registry_extensions.csv
= 901 identities
```

GitHub 管 Source / Identity / Learner / Release；Anki 继续是 FSRS / Review History / Due / Interval / Card State 真源。

---

## 2. Expressions operational baseline

三、四年级 Expressions 已完成首次正式闭环：

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
LearningOrder       = 000001..000066
approved            = 66
admitted            = 66
release-ready       = 66
```

Anki：

```text
Deck              = Klose-English::Expressions
Note Type         = Klose Expression
Cards             = 66
New/day           = 2
FSRS              = ON
Desired retention = 90%
AnkiWeb Sync       = completed
```

当前处于 real-learning pilot。一个月后主要观察 Again ratio、slot substitution、unseen-situation transfer、over-generalization、pronunciation/fluency 和 daily review load。不要因 repo 重建改变已经进入 Learning / Review 的 Card 调度状态。

---

## 3. Current repo task — Third-party Multi-Edition Vocabulary Corpus

用户已冻结长期目标：

> 把北京版、人教版、沪教版及其他第三方小学教材词汇汇总成一个统一、sense-aware 去重的第三方词源。教材来源、最早年级、覆盖教材数、出现次数、年级分布不参与学习决策。所有第三方来源处理完成后，再与 Klose Full Stable Identity Registry 做一次最终去重，剩余 learning units 全部作为 Klose 当前教材之外的新词学习。

两阶段流程：

```text
Stage A
所有第三方 Source Occurrences
→ 第三方内部 sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后才执行）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 不因 Klose 当前已有某词而删除第三方 learning unit。

---

## 4. Simplified Stage-A architecture — CURRENT

2026-09-06 已完成一次工程复杂度复核。结论：业务规则正确，但原来的多层 `audit → apply → recheck` 专项流水线过度复杂，因此已经收敛为最简长期架构。

唯一 active 数据流：

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

核心边界：

```text
Source Adapter = 只解析 Source Fact
CandidateSignals = 只提供匹配证据
identity_decisions.csv = 唯一内容决策真源
review_queue.csv = 纯派生 unresolved/blocker view
unified_vocabulary_preview.csv = reviewed Vocabulary preview
```

不再为 exact / morphology / multiword / semantic / expression routing 分别创建长期 pipeline。

当前 `identity_decisions.csv` Action：

```text
keep-identity
reuse-identity
split-required
held
route-expression
source-only
pending
```

Content decision 是 data；通用 Python 只负责生成和校验。

---

## 5. Enabled third-party Source Adapters

配置真源：

```text
anki/klose/third_party_vocabulary/config/source_adapters.csv
```

当前：

```text
beijing_start1
  Source books       = 12
  Source occurrences = 808
  MatchKeys          = 734

renjiao_start1
  Source books       = 12
  Source occurrences = 908
  MatchKeys          = 802
```

人教版目录另有“三年级起点”，未来必须作为独立 adapter，不能静默混入 `renjiao_start1`。

Renjiao Source Adapter 当前物理职责已收敛为：

```text
Raw 12 XLSX
→ source_reference/renjiao_start1_staging/occurrences.csv
```

它不再自己比较北京版，也不再生成 exact/morph/new 等 identity 队列。

北京版现有 staging 中历史的 Klose comparison / semantic audit 仍可作为来源审计证据，但不代表 Stage-B 最终 Klose diff。

---

## 6. Current unified Stage-A baseline

当前北京 + 人教一年级起点：

```text
Source occurrences      = 1716
Normalized surfaces     = 1144
Durable decisions       = 1144
Vocabulary preview      = 851
Review/blocker surfaces = 254

keep-identity     = 849
reuse-identity    = 13
held              = 50
pending           = 192
split-required    = 12
route-expression  = 3
source-only       = 25
```

`403 Renjiao new surfaces = 403 new words` 已明确否定。原始第三方“单词”列可能包含 lexical word、multiword lexical unit、format alias、inflected form、Expression、event/source chunk；最终对象类型由统一 Identity Resolution 决定。

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master modified      = no
Klose Learner modified     = no
Klose Publish modified     = no
Anki modified              = no
```

---

## 7. Completion Recheck protections

每次阶段完成后必须执行独立 Completion Recheck；CI success 不能单独等同“做对了”。

当前通用 checker 至少验证：

```text
enabled adapter occurrence union 完整闭合
SourceOccurrenceKey 唯一
surface set 与 occurrences 闭合
DecisionKey 唯一且只引用 enabled surfaces
new undecided surface 自动进入 pending
review_queue 是纯派生 blocker/pending view
reuse-identity 必须有 CanonicalMatchKey
Vocabulary / Expression / source-only 对象边界一致
Klose Master / Learner / Publish / Anki 无改动
```

代表性语义边界持续锁定：

```text
May(月份) / may(情态动词)
like=喜欢 / weather-like construction
square=正方形 / square=广场
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
study=学习 / study=书房
```

代表性 morphology/form 边界：

```text
danced → dance          reuse candidate
cartoons → cartoon      reuse candidate
gloves → glove          reuse candidate
scissors                 keep lexicalized learning unit
crossroads               keep lexicalized learning unit
slept / swam / were / won held irregular-form policy
```

工程简化后的 Completion Recheck 还发现并修正过一次迁移偏差：北京 seed 的 `a few / get well / how many / ice cream / make use of / pencil case / sweet potato / take part in / the U.K. / the U.S.A. / the United States of America` 未经过 Vocabulary/Expression/object routing，不能因 seed 身份自动当 Vocabulary Identity；现已回到统一 review queue。

---

## 8. NEXT TASK

不要恢复旧 multi-pass 专项流水线。

下一步只操作统一入口：

```text
anki/klose/third_party_vocabulary/staging/review_queue.csv
```

处理原则：

```text
1. 只审核真正 unresolved / held / split-required 的 learning-unit 问题；
2. 结果只写入 review/identity_decisions.csv；
3. rebuild；
4. independent Completion Recheck；
5. 不为了 pending=0 强行猜测缺乏 source context 的义项；
6. 在 corpus 足够稳定前不 mint Stable ThirdPartyID；
7. 所有计划第三方来源完成前不执行 Stage-B Klose diff。
```

当前优先事项是把 254 个统一 blocker/review surface 进一步区分：

```text
可直接 resolve 的 Vocabulary learning unit
可 canonicalize/reuse 的 form/alias
Expression
source-only chunk
真实 semantic split
必须继续 held 的 source-context / identity-policy blocker
```

不再按“138 phrase + 42 routing + 其他 form pass”分别维护工作流。

完成当前两 adapter 的统一 queue 后，再接入下一个第三方 Source Adapter；新增 adapter 只增加标准 occurrences + `source_adapters.csv` 配置，不复制 builder/checker。

---

## 9. Deferred

仍保留但不是当前任务：

```text
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（对应 admission 前）
Expressions one-month real-learning evaluation
```

---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。