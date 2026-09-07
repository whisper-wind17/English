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

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是 derived blocker/pending view。新增教材导致 occurrence evidence 改变时，旧 decision 必须自动 pending，不能静默继承。

Vocabulary Preview 现在有额外发布前门禁：任何 reviewed provisional Vocabulary candidate 的 `TargetSense` 为空都会直接使 Stage-A workflow 失败。

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

五个 adapter 合计：

```text
Enabled adapters    = 5
Source occurrences  = 4848
Normalized surfaces = 2062
Durable decisions   = 2062
pending             = 0
evidence-changed    = 0
```

在五-adapter decision closure 后，又对当时的 1477 条 Vocabulary Preview 执行了 A–Z 全量内容质量审计，重点检查：

```text
TargetSense 空值
canonical / alias 语义污染
reuse 是否绕过 canonical held/split blocker
漏掉的 morphology canonicalization
Vocabulary vs Expression object routing
过度具体 event chunk
```

结构层修复：

```text
reuse alias 不得绕过 canonical held/split/pending blocker
canonical surface 的 TargetSense 高于 alias/form TargetSense
ice-cream → ice cream
listening to music → listen to music
smart → 聪明的；机灵的
```

内容层审计把原有空 TargetSense 全部重新分类，而不是按字典首义硬填：

```text
1. source evidence 足够清楚 → 补窄义 TargetSense
2. 证据不足/语义或语法边界不稳 → held
3. 规则词形/表现变体 → reuse canonical identity
4. 交际句型 → route-expression
5. 过度具体事件块 → source-only
```

新增/强化的典型 blocker：

```text
a lot
as
British
broke
date
dish
excuse
has
hold
in one hour
jam
model
order
out
out of
pop
stage
tie
upset
would
```

典型 canonicalization / routing：

```text
be afraid of → afraid of
dropped → drop
grapes → grape
happened → happen
How old ...? → Expression
climb on the window ledge → source-only
women → 保留独立 pedagogically salient plural-form identity
```

当前 workflow 还必须通过：

```text
Vocabulary Preview TargetSense complete = all / all
```

本轮最终计数以 `data: close vocabulary preview content audit` 对应 workflow 及其 bot-generated data commit 为准；在 workflow 完成前不要手工填写计数。

仍未 mint Stable ThirdPartyID，仍未执行 Stage-B Klose diff。

---

## 5. NEXT TASK — REVIEW FINAL FIVE-ADAPTER CORPUS, THEN DECIDE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

下一步：

```text
1. 读取最新 generated staging 与 workflow 结果，确认最终 preview / blocker / action counts；
2. 向用户展示五-adapter corpus 的最终质量闭合结果与代表性边界；
3. 若用户认可当前质量，再启用 waiyan_start3；
4. waiyan_start3 接入仍只做 Stage A：Source Adapter → evidence requeue → identity review → preview；
5. 仍不 mint Stable ThirdPartyID；
6. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
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
当前 held/split blockers — wait for more source context / actual textbook / form policy
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
