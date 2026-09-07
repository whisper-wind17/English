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

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
LearningOrder       = 000001..000066
approved/admitted/release-ready = 66
```

Anki：`Klose-English::Expressions`，66 cards，New/day=2，FSRS ON，Desired retention=90%，AnkiWeb Sync completed。当前处于 real-learning pilot。

---

## 3. Current repo task — Third-party Multi-Edition Vocabulary Corpus

长期目标：多个第三方小学教材统一进入一个 independent corpus，按 **learning unit / target sense** 做 sense-aware Identity Resolution；所有计划第三方来源完成后，才与 Klose Full Stable Identity Registry 做一次 Stage-B diff。

```text
Stage A
第三方 Source Occurrences
→ 第三方内部 sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit。

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

职责：Source Adapter 只解析 Source Fact；CandidateSignals 只提供候选证据；`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是纯派生 blocker/pending view；content decision 是 data，Python 只做通用生成和校验。不要恢复 edition-specific exact/morphology/semantic/routing 多层 pipeline。

内容审校使用 transient inbox：

```text
review/decision_updates.csv
→ apply_third_party_identity_decision_updates.py
→ identity_decisions.csv
→ inbox 删除
```

成功 workflow 后 `review/` 必须重新只剩 `identity_decisions.csv`。

---

## 5. Evidence-aware decision binding — FROZEN

`OccurrenceKeys` 持久化为审校时实际覆盖的 SourceOccurrenceKey JSON array。

```text
current occurrence set == reviewed occurrence set
→ decision 有效

current occurrence set != reviewed occurrence set
→ pending
→ CandidateSignals += decision-evidence-changed
→ 回到统一 review_queue
→ stale SourceMatchKey 不得进入 preview provenance
```

历史 wildcard/legacy serialization 已完成一次性迁移。新增教材不能静默继承旧 surface decision。

---

## 6. Enabled Source Adapters — CURRENT

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

hujiao_start3
  books       = 8
  occurrences = 1111
  MatchKeys   = 1067
```

`hujiao_start3` 只包含沪教版三年级起点 3–6 年级上下册；同目录 7–9 年级牛津英语未纳入当前小学 corpus。Hujiao source baseline `1111 / 1067` 已冻结并由 checker 强制校验。

每个 adapter 只输出 standardized `occurrences.csv`，不自行做跨教材比较或 Identity Resolution。

---

## 7. Current Stage-A baseline — 4 adapters / Hujiao residual review

三-adapter 闭合基线曾为：

```text
Source occurrences        = 2567
Normalized surfaces       = 1443
Durable decisions         = 1443
Vocabulary preview        = 1223
pending                   = 0
evidence-changed          = 0
true blockers             = 125
```

启用 `hujiao_start3` 后自动产生：

```text
722 previously reviewed surfaces with changed evidence
345 completely new surfaces
= 1067 pending
```

这验证了 evidence-aware gate：旧 decision 没有因 surface 相同而静默沿用。

Hujiao 第一轮 A–Z 已逐批完成统一审校，并且每批都通过 independent Completion Recheck。最新可信基线（run `34070209190`）为：

```text
Enabled adapters          = 4
Source occurrences        = 3678
Normalized surfaces       = 1788
Durable decisions         = 1703
Vocabulary preview        = 1242
Review/blocker surfaces   = 428
Evidence-changed surfaces = 158

Generated current surface state:
keep-identity     = 1225
reuse-identity    = 51
held              = 153
pending           = 243
split-required    = 32
route-expression  = 51
source-only       = 33
```

Hujiao 收敛变化：

```text
pending            1067 → 243
review/blocker     1134 → 428
evidence-changed    722 → 158
Vocabulary preview  582 → 1242
```

注意：**A–Z 第一轮完成 ≠ Hujiao Identity Resolution 完成。** 当前 `243 pending` 是各字母批次中尚未处理的 residual surfaces；下一阶段继续统一 residual sweep。真正的 `held / split-required` blocker 不应为了追求 `pending=0` 被猜测性合并。

当前显式保护的代表性边界包括：

```text
can        = modal / container → held
chicken    = 鸡 / 鸡肉 → split-required
cold       = 寒冷 / 感冒 → split-required
cook       = 烹饪 / 厨师 → split-required
kind       = 种类 / 友善 → split-required
left       = 左边 / leave过去式 → split-required
light      = 多个小学核心义项 → split-required
like       = 喜欢 / 像等 → split-required
mouse      = 老鼠 / 鼠标 → split-required
orange     = 水果 / 颜色 → split-required
plant      = 植物 / 种植 → split-required
play       = 玩/运动 / 演奏 → split-required
present    = 礼物 / 现在 → split-required
right      = 右边 / 正确 → split-required
sound      = 声音 / 听起来 → split-required
square     = 正方形 / 广场 → split-required
taste      = 味道 / 尝、尝起来 → split-required
thin       = 瘦的 / 薄的 → split-required
too        = 也 / 太、过度 → split-required
watch      = 手表 / 观看 → split-required
water      = 水 / 浇水 → split-required
will       = 当前来源锁定 future modal“将/会”
way/well/wish/with = Source Fact 不足 → held
wild goose / wild geese = irregular-form policy → held
tooth / teeth = irregular-form policy → held
your / yours、their / theirs = 独立 grammar learning units，不做 morphology merge
wash ... face、weak in、try ... on = route-expression
```

最近通过：

```text
GitHub Actions run     = 34070209190
Completion Recheck     = PASS
Generated data commit  = 63c3a68
Klose publishing state = untouched
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

## 8. NEXT TASK — residual sweep

继续只处理统一 `review_queue.csv`，不增加新的 edition-specific 审校流水线：

```text
1. residual pending = 243：从统一 review_queue 做第二轮 sweep；
2. 优先处理 evidence-changed = 158，再处理其余 genuinely new pending；
3. target sense 清晰的稳定义项 → keep/reuse/revalidate；
4. morphology / irregular form → 按既有 policy canonicalize 或 held；
5. Vocabulary vs Expression → 显式 route；
6. 同 surface 多个真实 target sense → split-required；
7. Source Fact 不足 → held，不为了 pending=0 猜测；
8. 每批 update 后 rebuild + independent Completion Recheck；
9. 串行写入，前一 workflow 完成前不提交下一批；
10. residual pending 收敛后再评估是否达到当前四-adapter Stage-A identity closure；
11. 仍不 mint Stable ThirdPartyID；
12. 所有计划第三方来源完成前不执行 Stage-B Klose diff。
```

目标不是机械 `pending=0`；目标是 **pending 只因尚未审校而存在，而真正无法安全定案的项目必须显式落到 held / split-required blocker。**

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
当前 held/split 第三方 blocker：等更多教材上下文、actual textbook 或 form policy 后收敛
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（admission 前）
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
