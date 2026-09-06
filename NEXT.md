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

涉及 Klose 实际教材 reconciliation 时再读取 `docs/SOURCE_RECONCILIATION.md`；Expressions 任务读取 `docs/EXPRESSIONS_SYSTEM.md`。不要仅凭聊天历史推测当前状态。

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

三、四年级 Expressions 首次正式闭环：

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
LearningOrder       = 000001..000066
approved/admitted/release-ready = 66
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

当前处于 real-learning pilot。不要因 repo 重建改变已进入 Learning / Review 的 Card 调度状态。

---

## 3. Current repo task — Third-party Multi-Edition Vocabulary Corpus

长期目标已冻结：

> 把北京版、人教版、沪教版及其他第三方小学教材词汇汇总成一个统一、sense-aware 去重的第三方词源。教材来源、最早年级、覆盖教材数、出现次数、年级分布不参与学习决策。所有计划第三方来源完成后，再与 Klose Full Stable Identity Registry 做最终去重，剩余 learning units 全部作为 Klose 当前教材之外的新词学习。

```text
Stage A
所有第三方 Source Occurrences
→ 第三方内部 sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 不因 Klose 当前已有某词而删除第三方 learning unit。

---

## 4. Simplified Stage-A architecture — FROZEN

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
Source Adapter             = 只解析 Source Fact
CandidateSignals           = 只提供匹配证据
identity_decisions.csv     = 唯一内容决策真源
review_queue.csv            = 纯派生 unresolved/blocker view
unified_vocabulary_preview = reviewed Vocabulary preview
```

Action：

```text
keep-identity
reuse-identity
split-required
held
route-expression
source-only
pending
```

Content decision 是 data；Python 只负责通用生成和校验。不要恢复旧 exact / morphology / semantic / multiword / routing 专项 pipeline。

内容审校使用 transient inbox：

```text
review/decision_updates.csv
→ apply_third_party_identity_decision_updates.py
→ identity_decisions.csv
→ inbox 删除
```

成功 workflow 结束后 `review/` 必须重新只剩 `identity_decisions.csv`。

---

## 5. Evidence-aware decision binding — FROZEN

新增教材可能给已 reviewed 的同一 surface 带来新义项，因此 decision 不能只按 MatchKey 永久复用。

`OccurrenceKeys` 持久化为审校时实际覆盖的 SourceOccurrenceKey **JSON array**：

```text
current occurrence set == reviewed occurrence set
→ 原 decision 有效

current occurrence set != reviewed occurrence set
→ pending
→ CandidateSignals += decision-evidence-changed
→ 回到统一 review_queue
→ stale SourceMatchKey 不得进入 preview provenance
```

历史 `*` / 歧义 pipe serialization 已在 GitHub Actions run `34063545296` 完成一次性迁移。当前 durable decision 禁止长期 wildcard OccurrenceKeys。

---

## 6. Enabled Source Adapters

配置真源：`anki/klose/third_party_vocabulary/config/source_adapters.csv`

```text
beijing_start1
  books       = 12
  occurrences = 808
  MatchKeys   = 734

renjiao_start1
  books       = 12
  occurrences = 908
  MatchKeys   = 802

renjiao_start3
  books       = 8
  occurrences = 851
  MatchKeys   = 818
```

`renjiao_start3` = 人教版三年级起点 3–6 年级上下册，共 8 册；作为独立 adapter，不与 `renjiao_start1` 混合。

每个 adapter 只负责：

```text
Raw source
→ source_reference/<adapter>_staging/README.md
→ source_reference/<adapter>_staging/occurrences.csv
```

Adapter 不比较其他教材，不生成 edition-specific exact/morph/semantic 队列。

---

## 7. Current Stage-A baseline — 3 adapters CLOSED

`renjiao_start3` 接入时产生：

```text
299 completely new surfaces
519 previously reviewed surfaces with changed evidence
= 818 pending
```

随后累计完成 14 批统一 review，并逐批通过 independent Completion Recheck。现在所有普通 pending 和 evidence-changed 项均已闭合：

```text
Enabled adapters          = 3
Source occurrences        = 2567
Normalized surfaces       = 1443
Durable decisions         = 1443
Vocabulary preview        = 1223
Review/blocker surfaces   = 125
Evidence-changed surfaces = 0

keep-identity     = 1212
reuse-identity    = 52
held              = 115
pending           = 0
split-required    = 10
route-expression  = 21
source-only       = 33
```

完整收敛变化：

```text
pending            818 → 0
review/blocker     848 → 125
evidence-changed   519 → 0
Vocabulary preview 553 → 1223
```

最终批次：

```text
Decision updates       = 46
replaced               = 28
appended               = 18
GitHub Actions run     = 34065794743
Completion Recheck     = PASS
Generated data commit  = da96f8a
```

当前 125 条 `review_queue.csv` **全部是真实 blocker**：

```text
held           = 115
split-required = 10
pending        = 0
```

不要为了 queue=0 强行猜测。典型 blocker 包括：

```text
May(月份) / may(情态动词)
like=喜欢 / similarity construction
square=正方形 / square=广场
chicken=鸡 / chicken=鸡肉
do=实义动词 / do=助动词
dress=连衣裙 / dress=穿衣
fish=鱼 / fish=钓鱼
plant=植物 / plant=种植
play=玩 / 参加运动 / 演奏
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
hot=温度 / hot=辣或食物语义
orange=水果 / orange=颜色
kind=种类 / kind=友好的
live=居住 / live=活着
mouse=动物 / mouse=电脑鼠标
best/better、ate/bought/drank/fell/felt/gave/had/lost/rode/saw/slept/swam/took/went/woke/won 等 irregular/form policy
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

## 8. NEXT TASK — add the next Source Adapter

当前三个 adapter 已没有普通 pending；剩余 125 项需要真实上下文、更多来源证据或 identity/form policy，不应阻塞扩大第三方 corpus。

下一步：

```text
1. 检查并接入 repo 内下一个独立第三方 Source Adapter；
2. 优先处理沪教版；
3. adapter 只输出 standardized Source Occurrences；
4. 在 source_adapters.csv 中 Enabled=yes；
5. generic builder 自动把全新 surface 和 evidence-changed surface 放入统一 review_queue；
6. 只审新增/受影响 decisions；
7. rebuild + independent Completion Recheck；
8. 不 mint Stable ThirdPartyID；
9. 所有计划第三方来源完成前不执行 Stage-B Klose diff。
```

新增来源本身也可能给当前 125 个 blocker 带来可用证据；如果 occurrence set 变化，evidence-aware gate 会自动重新排队。

---

## 9. Completion Recheck contract

每个 adapter 接入或每批 decision update 后必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Stale SourceMatchKey excluded from preview provenance
review_queue 纯派生
known semantic/morphology blockers preserved
simplified physical layout
legacy multi-pass tools absent
Klose Master/Learner/Publish/Anki untouched
```

---

## 10. Deferred

```text
当前 125 个 held/split 第三方 blocker：等更多教材上下文、actual textbook 或 form policy 后收敛
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（对应 admission 前）
Expressions one-month real-learning evaluation
```

---

## 11. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
