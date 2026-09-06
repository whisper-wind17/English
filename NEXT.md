# NEXT — Klose Learning

Last updated: 2026-09-07

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

GitHub 管 Source / Identity / Learner / Release；Anki 是 FSRS / Review History / Due / Interval / Card State 真源。

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

当前处于 real-learning pilot。不要因 repo 重建改变已经进入 Learning / Review 的 Card 调度状态。

---

## 3. Current repo task — Third-party Multi-Edition Vocabulary Corpus

长期目标已冻结：

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

## 4. Simplified Stage-A architecture — FROZEN

长期 active model：

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/occurrences.csv
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

职责：

```text
Source Adapter = 只解析 Source Fact
CandidateSignals = 只提供匹配证据
identity_decisions.csv = 唯一内容决策真源
review_queue.csv = 纯派生 unresolved/blocker view
unified_vocabulary_preview.csv = reviewed Vocabulary preview
```

`identity_decisions.csv` Action：

```text
keep-identity
reuse-identity
split-required
held
route-expression
source-only
pending
```

Content decision 是 data；Python 只负责通用生成和校验。不要恢复旧的 exact / morphology / semantic / multiword / routing 专项 pipeline。

内容审校使用通用 transient inbox：

```text
review/decision_updates.csv
→ tools/apply_third_party_identity_decision_updates.py
→ merge 到 identity_decisions.csv
→ inbox 删除
```

`decision_updates.csv` 不是第二套状态真源；成功 workflow 结束后 `review/` 必须重新只剩 `identity_decisions.csv`。

---

## 5. Enabled Source Adapters

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

Renjiao adapter 物理职责：

```text
Raw XLSX
→ source_reference/<adapter>_staging/README.md
→ source_reference/<adapter>_staging/occurrences.csv
```

它不比较其他教材，不生成 exact/morph/new/semantic 队列。

人教版“三年级起点”应作为独立 adapter，不能混入 `renjiao_start1`。

---

## 6. Current Stage-A baseline — Beijing + Renjiao start1

2026-09-07 已完成当前两个 adapter 的全部 `pending` surface 审校，并逐批执行独立 Completion Recheck。

最终：

```text
Enabled adapters        = 2
Source occurrences      = 1716
Normalized surfaces     = 1144
Durable decisions       = 1144
Vocabulary preview      = 1028
Review/blocker surfaces = 64

keep-identity     = 1017
reuse-identity    = 32
held              = 52
pending           = 0
split-required    = 12
route-expression  = 5
source-only       = 26
```

最后一批 72 条 workflow：

```text
GitHub Actions run = 34045105706
Completion Recheck = pass
Klose publishing state untouched = yes
```

当前 64 条 review queue **全部是真实 blocker**：

```text
held           = 52
split-required = 12
pending        = 0
```

不要为了 queue=0 强行猜测。典型 blocker：

```text
May(月份) / may(情态动词)
like=喜欢 / weather-like construction
square=正方形 / square=广场
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
study=学习 / study=书房
child / children
feet / foot
slept / swam / were / won
```

这批统一审校还明确完成：

```text
rowed a boat → row a boat
jumped/jumping rope → jump rope
listened/listening to music → listen to music
watched/watching TV → watch TV
washed clothes → wash clothes
walking the dog → walk the dog
watering the plants → water the plants

the U.K. → the UK
the U.S.A. → the USA
the United States of America → the USA

the matter → route-expression
excuse me → route-expression
saw flowers → source-only
```

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

## 7. Completion Recheck contract

当前 checker 同时验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
review_queue 纯派生
known semantic blockers preserved
known morphology blockers preserved
Beijing multiword 必须经过显式 review
simplified physical layout
legacy multi-pass tools absent
Klose Master/Learner/Publish/Anki untouched
```

每个 adapter 接入或每批 decision update 后都必须重新通过。

---

## 8. NEXT TASK — add the next Source Adapter

当前两个 adapter 已没有普通 pending；剩余 64 项需要真实上下文或 identity policy，不应阻塞继续扩大第三方 corpus。

下一步：

```text
1. 接入下一个独立第三方 Source Adapter；
2. adapter 只输出 standardized Source Occurrences；
3. 在 source_adapters.csv 中启用；
4. 通用 builder 自动把新增 surface 变成 pending / candidate signals；
5. 只审新增/受影响的 unresolved decisions；
6. rebuild + independent Completion Recheck；
7. 不 mint Stable ThirdPartyID；
8. 所有计划第三方来源完成前不执行 Stage-B Klose diff。
```

优先候选：repo 内人教版“三年级起点”，作为 `renjiao_start3` 独立 adapter。

---

## 9. Deferred

```text
当前 64 个 held/split 第三方 blocker：等更多教材上下文、actual textbook 或 form policy 提供证据后再收敛
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
