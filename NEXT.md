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
→ learner-facing TargetSense gate
→ tools/check_third_party_corpus.py
```

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是 derived blocker view。新增教材导致 occurrence evidence 改变时，旧 decision 必须自动 pending，不能静默继承。

Vocabulary Preview 有硬门禁：任何 provisional Vocabulary candidate 的 `TargetSense` 为空，Stage-A workflow 必须失败。

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

## 4. Current Stage-A baseline — REVIEW + PREVIEW QUALITY CLOSURE

五个 adapter 最终可信状态：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1451
Review/blocker surfaces   = 444
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1442
reuse-identity    =   61
held              =  405
split-required    =   39
route-expression  =   81
source-only       =   34
```

最终验证：

```text
GitHub Actions run                         = 34084215849
content-audit commit                       = ba1c0afe5e1107447f46084f9462a3aa554f6374
bot-generated data commit                  = 8bc04ffa74914e02ecbf453b47cbf93c837acb53
Vocabulary Preview TargetSense complete    = 1451 / 1451
Third-party Completion Recheck             = PASS
Source occurrence closure                  = PASS
Explicit reviewed OccurrenceKeys           = PASS
Changed source evidence requeues decision  = PASS
Canonical blocker bypass                   = NO
Canonical TargetSense precedence           = PASS
Klose Master/Learner/Publish/Anki touched  = NO
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

本轮对原 1477 条 Vocabulary Preview 做了 A–Z 内容质量审计。原则不是“空义项就翻译”，而是逐项判断：

```text
明确 learning unit       → 补窄义 TargetSense
证据不足/边界不稳        → held
规则词形/表现变体         → reuse canonical identity
交际句型                 → route-expression
过度具体事件块            → source-only
```

新增/强化典型 blocker：

```text
a lot / as / British / broke / date / dish / excuse
has / hold / in one hour / jam / model
order / out / out of / pop
stage / tie / upset / would
```

典型 canonicalization / routing：

```text
be afraid of → afraid of
dropped → drop
grapes → grape
happened → happen
stayed at home → stay at home
walking the dog → walk the dog
watering the plants → water the plants
How old ...? → Expression
climb on the window ledge → source-only
women → 保留独立 pedagogically salient plural-form identity
```

已知 semantic blockers 继续保留：

```text
study      → held
saw        → split-required
watch      → split-required
may        → split-required
like       → split-required
square     → split-required
left       → split-required
cook       → split-required
cold       → split-required
```

---

## 5. NEXT TASK — USER REVIEW, THEN DECIDE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

下一步：

```text
1. 向用户展示当前五-adapter corpus 最终结构与计数；
2. 解释 1451 Vocabulary preview、444 blockers、81 Expressions、34 source-only 的含义；
3. 抽样展示 keep / reuse / held / split / expression 的真实例子；
4. 根据用户反馈决定是否需要进一步质量抽查或 Identity policy 调整；
5. 用户确认后，才考虑启用 waiyan_start3；
6. waiyan_start3 接入仍只做 Stage A；
7. 仍不 mint Stable ThirdPartyID；
8. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
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
Vocabulary Preview TargetSense 全部非空
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
当前 444 held/split blockers — wait for more source context / actual textbook / form policy
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
