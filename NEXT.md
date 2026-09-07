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
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

涉及 Klose 实际教材 reconciliation 时再读取 `docs/SOURCE_RECONCILIATION.md`；Expressions 任务读取 `docs/EXPRESSIONS_SYSTEM.md`。不要仅凭聊天历史推测当前状态。

---

## 1. Klose operational baseline

Vocabulary：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
Stable Identity Registry = 901 identities
```

Expressions：

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
approved/admitted/release-ready = 66
Anki New/day = 2
FSRS = ON / 90%
```

GitHub 管 Source / Identity / Learner / Release；Anki 是 FSRS / Review History / Due / Interval / Card State 真源。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus

```text
Stage A
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit；当前仍未进入 Stage B。

Frozen physical architecture：

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

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是 derived blocker/pending view。新增教材导致 occurrence evidence 改变时，旧 decision 必须自动 pending，不能静默继承。

---

## 3. Enabled Source Adapters — five-adapter closure

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

`waiyan_start3` 已完成 Source Inventory，确认为 3–6 年级上下册独立完整 8-book family，但 **尚未启用**。

---

## 4. Current Stage-A baseline — REVIEW CLOSURE REACHED

外研一年级起点接入时产生：

```text
797 existing surfaces with changed evidence
274 completely new surfaces
= 1071 pending
```

处理过程：

```text
797 → five-adapter exact-surface evidence revalidation
274 → conservative new learning-unit/object/form review
→ independent content-quality Completion Recheck
→ correction pass for confirmed false positives
```

独立 Recheck 抓到并修正的典型问题：

```text
aah / hey / whoops / sh
→ dictionary noise / interjection misrouting
→ route-expression

here's / what's / where's / they're / couldn't / ...
→ contraction false-positive Vocabulary
→ held

leaves / sometime / sweets / watches
→ unsafe morphology canonicalization
→ held

of / ever / ticket
→ broad or conflicting dictionary gloss cannot fix target sense
→ held
```

最新可信数据：GitHub Actions run `34076701208`，generated data commit `aa2dcc0`。

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1484
Review/blocker surfaces   = 424
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1470
reuse-identity    =   55
held              =  385
split-required    =   39
route-expression  =   80
source-only       =   33
```

Closure meaning：

```text
2062 surfaces = 2062 explicit durable decisions
pending = 0
evidence-changed = 0
```

不是说 2062 个 surface 都是 Vocabulary。当前 `unified_vocabulary_preview.csv = 1484` 才是 evidence 完整、已 reviewed 的 provisional Vocabulary candidates；仍未 mint Stable ThirdPartyID。

当前 `review_queue = 424` 全部是真 blocker：

```text
held           = 385
split-required = 39
```

不能为了清零而猜测性合并。

代表性边界：

```text
study      = 学习 / 研究等 → held
saw        = see过去式 / 锯子 → split-required
watch      = 手表 / 观看 → split-required
may        = May / modal may → split-required
like       = 喜欢 / 像等 → split-required
square     = 正方形 / 广场 → split-required
left       = 左边 / leave过去式 → split-required
cook       = 烹饪 / 厨师 → split-required
cold       = 寒冷 / 感冒 → split-required
stronger   = reuse → strong
swing      = keep / 秋千
candies    = reuse → candy
goes       = reuse → go
stories    = reuse → story
```

新增 Expression routing 示例：

```text
hey
how are you?
nice to meet you.
here you are.
how about ...?
what about ...?
why not?
how much ...?
you're welcome!
happy new year!
excuse me
hurry up
trick or treat
see you!
```

最新验证：

```text
GitHub Actions run             = 34076701208
Completion Recheck             = PASS
Source occurrence closure      = PASS
pending                        = 0
evidence-changed               = 0
Known semantic blockers        = preserved
Known morphology boundaries    = preserved
Transient decision inbox       = removed
Klose Master/Learner/Publish/Anki = untouched
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
```

---

## 5. NEXT TASK — PAUSE FOR USER REVIEW

**不要继续启用 `waiyan_start3`。** 用户明确要求：本轮处理完成后，先查看当前第三方词汇表情况。

下一步：

```text
1. 向用户展示当前五-adapter corpus 总体结构与计数；
2. 解释 1484 Vocabulary preview、424 blockers、80 Expressions、33 source-only 的含义；
3. 抽样展示 keep / reuse / held / split / expression 的真实例子；
4. 根据用户反馈决定是否需要进一步质量抽查或调整 Identity policy；
5. 用户确认后，才考虑启用 waiyan_start3；
6. 仍不 mint Stable ThirdPartyID；
7. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
```

---

## 6. Completion Recheck contract

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

CI / script success 不能单独作为“结果正确”的结论；必须再做独立 Completion Recheck。

---

## 7. Deferred

```text
waiyan_start3 adapter enablement — wait for user review
当前 424 held/split blockers — wait for more source context / actual textbook / form policy
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（admission 前）
Expressions one-month real-learning evaluation
```

---

## 8. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
