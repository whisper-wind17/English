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

## 7. Current Stage-A baseline — four-adapter review closure reached

北京一年级起点 + 人教一年级起点 + 人教三年级起点 + 沪教三年级起点的统一 residual review 已闭合。

最新可信基线（GitHub Actions run `34072447467`，generated data commit `4d91766852b22027882b939eb8d6c53c96b5b0a9`）：

```text
Enabled adapters          = 4
Source occurrences        = 3678
Normalized surfaces       = 1788
Durable decisions         = 1788
Vocabulary preview        = 1441
Review/blocker surfaces   = 219
Evidence-changed surfaces = 0
pending                   = 0

Durable decision actions:
keep-identity     = 1427
reuse-identity    = 52
held              = 180
split-required    = 39
route-expression  = 57
source-only       = 33
```

关键解释：

```text
1788 surfaces = 1788 durable decisions
pending = 0
```

表示当前四个 adapter 的每个 surface 都已经得到显式 Stage-A 决策；并不表示 1788 个 surface 都已成为 Vocabulary Identity。

`review_queue = 219` 全部是真实 blocker：

```text
held          = 180
split-required = 39
```

这些 blocker 不应为了“清零队列”被猜测性合并。`evidence-changed=0` 表示所有当前 decision 都绑定了完整的现行 Source Occurrence evidence。

本轮 Completion Recheck 曾准确拦截一次错误：`study` 被误压成单一 learning unit 时 checker 报 `Known semantic collision flattened: study`。修正为 `held` 后重新执行全流程并 PASS。因此 `study` 继续作为显式 semantic blocker。

代表性已确认边界：

```text
may        = May / modal may → split-required
like       = 喜欢 / 像等 → split-required
square     = 正方形 / 广场 → split-required
left       = 左边 / leave过去式 → split-required
cook       = 烹饪 / 厨师 → split-required
cold       = 寒冷 / 感冒 → split-required
study      = 学习 / 研究等 source sense boundary → held
saw        = see过去式 / 锯子 → split-required
watch      = 手表 / 观看 → split-required
water      = 水 / 浇水 → split-required
taste      = 味道 / 尝、尝起来 → split-required
thin       = 瘦的 / 薄的 → split-required
too        = 也 / 太、过度 → split-required
right      = 右边 / 正确 → split-required
mouse      = 老鼠 / 鼠标 → split-required
orange     = 水果 / 颜色 → split-required
plant      = 植物 / 种植 → split-required
present    = 礼物 / 现在 → split-required
sound      = 声音 / 听起来 → split-required
save/second/stand/star/stay/stick/stop = Source Fact 不足 → held
stronger   = reuse strong
swing      = 秋千 → keep-identity
wild goose / wild geese = irregular-form policy → held
tooth / teeth = irregular-form policy → held
```

最新验证：

```text
GitHub Actions run             = 34072447467
Completion Recheck             = PASS
Source occurrence closure      = PASS
Known semantic blockers        = PASS
Known morphology blockers      = PASS
Klose publishing state         = untouched
Transient decision inbox       = removed
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
```

独立人工 Completion Recheck 亦确认：

```text
review_queue contains pending  = no
study                          = held
saw                            = split-required
swing                          = keep-identity / 秋千
stronger                       = reuse-identity → strong
save / second                  = held
bot commit touched only Stage-A third-party files
Klose Master/Learner/Publish/Anki = untouched
```

---

## 8. NEXT TASK — continue Stage A, not Stage B

当前四-adapter **review closure 已达到**，但整个 Third-party Stage A 是否结束取决于是否还有计划纳入的小学第三方教材来源。

下一步按以下顺序：

```text
1. 检查第三方教材源目录与 source_adapters.csv，确认下一个尚未接入的计划小学 Source Adapter；
2. 若仍有计划来源：按 Source Adapter → unified rebuild → evidence-aware requeue → unified review_queue 的同一架构继续接入；
3. 新 adapter 只能新增 Source Fact，不得自行做 edition-specific Identity Resolution；
4. 新来源导致已有 surface evidence 改变时，旧 decision 必须自动回到 pending；
5. 每批 review 后继续执行 independent Completion Recheck；
6. 不为当前 219 held/split blockers 做猜测性清零；更多教材上下文可用于后续收敛它们；
7. 仍不 mint Stable ThirdPartyID；
8. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
```

如果确认 **没有更多计划第三方小学来源**，再进入 Stage-A finalization 设计：先评估 219 blockers 的处理策略与 Stable ThirdPartyID mint gate，完成后才有资格讨论 Stage B。

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
当前 219 held/split 第三方 blocker：等待更多教材上下文、actual textbook 或 form policy 后继续收敛
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
