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

waiyan_start1
  books       = 12
  occurrences = 1170
  MatchKeys   = 1071
```

Source-family boundaries：

- `hujiao_start3` 只包含沪教版三年级起点 3–6 年级上下册；同目录 7–9 年级牛津英语未纳入；source baseline `1111 / 1067` 已冻结。
- `waiyan_start1` 只包含外研版一年级起点 1–6 年级上下册；同目录外研三年级起点、初中、高中资料均未泄漏；source baseline `1170 / 1071` 已冻结。
- 外研版三年级起点 3–6 年级上下册已完成 Source Inventory，确认是独立完整 8-book family，但 **尚未启用**，待当前 `waiyan_start1` evidence revalidation 闭合后再接入。

每个 adapter 只输出 standardized `occurrences.csv`，不自行做跨教材比较或 Identity Resolution。

---

## 7. Current Stage-A baseline — Waiyan start1 enabled, unified revalidation OPEN

四-adapter 阶段曾达到完整 review closure：

```text
Enabled adapters          = 4
Source occurrences        = 3678
Normalized surfaces       = 1788
Durable decisions         = 1788
Vocabulary preview        = 1441
Review/blocker surfaces   = 219
Evidence-changed surfaces = 0
pending                   = 0
```

这是历史可信里程碑，不是当前工作状态。

现已启用 `waiyan_start1`。最新可信五-adapter rebuild：GitHub Actions run `34074078620`，generated data commit `2bedfeb249ce2acef975b920f2420f3b931b310b`。

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 1788
Vocabulary preview        = 799
Review/blocker surfaces   = 1169
Evidence-changed surfaces = 797
pending                   = 1071

Generated current surface actions:
keep-identity     = 765
reuse-identity    = 50
held              = 92
pending           = 1071
split-required    = 6
route-expression  = 45
source-only       = 33
```

关键集合闭合：

```text
Source occurrence delta:
4848 - 3678 = 1170
= Waiyan start1 source occurrences

Surface delta:
2062 - 1788 = 274
= completely new normalized surfaces

Waiyan MatchKeys:
797 evidence-changed existing surfaces
+ 274 completely new surfaces
= 1071 pending
= Waiyan start1 distinct MatchKeys
```

因此 `pending=1071` 是 evidence-aware binding 的正确结果，而不是旧 review 丢失：

- `identity_decisions.csv` 仍保留原 1788 条 durable decisions；
- 新外研 occurrence 加入旧 surface 时，旧 decision 的 OccurrenceKeys 不再覆盖完整 evidence，于是 current state 自动 pending；
- 全新外研 surface 也自动 pending；
- 旧 decision 不得静默继承到新 evidence。

旧四-adapter blocker 中有一部分现在也因外研新增 evidence 转为 current pending。例如：

```text
study durable decision = held
saw   durable decision = split-required
```

但两者当前都因 Waiyan occurrence 新增而显示 `decision-evidence-changed → pending`。这不是 blocker 被覆盖，而是要求基于五-adapter evidence 重新确认。相反，证据未变化的旧决策仍保持有效，例如：

```text
stronger = reuse-identity → strong
swing    = keep-identity / 秋千
save     = held（当前无 Waiyan evidence，继续有效）
```

代表性历史 semantic/form 边界仍必须保护：

```text
may        = May / modal may → split-required
like       = 喜欢 / 像等 → split-required
square     = 正方形 / 广场 → split-required
left       = 左边 / leave过去式 → split-required
cook       = 烹饪 / 厨师 → split-required
cold       = 寒冷 / 感冒 → split-required
study      = 学习 / 研究等 source sense boundary → durable held; current revalidation pending
saw        = see过去式 / 锯子 → durable split-required; current revalidation pending
watch      = 手表 / 观看 → split-required
water      = 水 / 浇水 → split-required
stronger   = reuse strong
swing      = 秋千 → keep-identity
wild goose / wild geese = irregular-form policy → held
tooth / teeth = irregular-form policy → held
```

最新验证：

```text
GitHub Actions run             = 34074078620
Waiyan start1 frozen baseline  = 12 books / 1170 occurrences / 1071 MatchKeys
Completion Recheck             = PASS
Source occurrence closure      = PASS
Evidence-aware requeue         = PASS
Known semantic blockers        = preserved as durable decisions
Known morphology decisions     = preserved
Klose publishing state         = untouched
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
```

独立 Completion Recheck 另外确认：

```text
274 new + 797 evidence-changed = 1071 pending
review_queue example old surface: apple / afraid / study / saw → decision-evidence-changed
review_queue example new surface: a bit / a knife and fork / aah / able → pending
stronger → strong remains reviewed
swing → 秋千 remains reviewed
waiyan staging spans Grade 1 upper through Grade 6 lower
bot commit 2bedfeb touched only third-party staging views
Klose Master/Learner/Publish/Anki = untouched
```

---

## 8. NEXT TASK — resolve Waiyan-induced unified queue; still Stage A

当前任务不是新增 edition-specific Waiyan semantic pipeline，也不是进入 Stage B；而是用唯一 `review_queue.csv` 对 `waiyan_start1` 导致的 1071 个 pending surface 做统一 revalidation。

执行顺序：

```text
1. 只从 staging/review_queue.csv 读取当前 pending；
2. 优先处理 evidence-changed 的高风险 semantic/form surfaces，确认旧 decision 是否仍成立；
3. 稳定、单义、证据一致的旧 surface 可批量 revalidate，并把五-adapter OccurrenceKeys 写入 durable decision；
4. 274 个全新 surface 继续按 learning unit / target sense 审校；
5. 真实歧义落 held / split-required，不为了 pending 清零而强行合并；
6. 每批通过 decision_updates.csv → apply → rebuild → independent Completion Recheck；
7. Klose Master/Learner/Publish/Anki 必须继续 untouched；
8. 不 mint Stable ThirdPartyID；
9. 当前 1071 pending 闭合后，再接入已盘点完成但尚未启用的 waiyan_start3 8-book family；
10. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
```

推荐 batching：先做 known semantic collisions / morphology/form edge cases，再按 surface 字母区间批量收敛稳定项。每批都必须保持 evidence binding 精确闭合。

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

CI / script success 不能单独作为“结果正确”的结论；必须再做独立 Completion Recheck。

---

## 10. Deferred

```text
当前五-adapter held/split blockers：等待更多教材上下文、actual textbook 或 form policy 后继续收敛
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
