# NEXT — Klose Learning

Last updated: 2026-09-06

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Expressions 任务继续读取：

```text
docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/expressions/review/grade3-grade4-baseline.md
→ anki/klose/expressions/review/identity_resolution.csv
→ anki/klose/expressions/review/full-baseline-review.md
→ anki/klose/expressions/master/expression_registry.csv
→ anki/klose/expressions/master/expression_occurrences.csv
→ anki/klose/expressions/master/source_expression_map.csv
→ anki/klose/expressions/learner/current.csv
→ anki/klose/expressions/learner/learning_admission.csv
→ anki/klose/expressions/learner/presentation_review_registry.csv
→ anki/klose/expressions/master/release_registry.csv
→ anki/klose/expressions/anki/README.md
→ anki/klose/expressions/publish/anki-import.csv
```

当前第三方 Vocabulary corpus 任务读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ anki/klose/source_reference/beijing_start1_staging/PREMERGE_STATUS.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Vocabulary status

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

FSRS / Due / Interval / Review History / Card State 继续以 Anki 为唯一真源。

---

## 2. Expressions source / identity baseline

当前复习范围只纳入 Klose 已学过的三、四年级实际教材 Expressions；一年级、二年级暂不复习。

```text
Grade 3 Source Occurrences = 94
Grade 4 Source Occurrences = 72
Total Source Occurrences   = 166

Curated Pattern Candidates = 64
Stable Expressions          = 66
Grade-4 priority            = 37
Grade-3-only                = 29
LearningOrder               = 000001..000066
```

学习顺序冻结为：

```text
KE000001..KE000037  = Grade-4 priority
KE000038..KE000066  = Grade-3 only
```

跨年级相同 Pattern 只学习一次，并归入 Grade-4 priority block。

64 Candidate 最终得到 66 Stable Expressions，因为 Identity Review 拆分：

```text
EC0035
→ It's time for [noun].
→ It's time to [verb].

EC0058
→ Excuse me?   # 没听清时请求重复
→ Excuse me.   # 礼貌引起注意
```

其他显式 Identity 调整：

```text
What's this? / What's that? → What's [demonstrative]?
Can I [verb phrase], please? → Can I [verb phrase]?  # please 可选
It's [weather adjective]... → It's [weather description]...
What about [thing]? → ExpressionType=slot_frame
```

---

## 3. Full 66-card Presentation / approval

全部 66 个 Stable Expressions 已生成 Stage-A Learner Presentation，并已建立 source provenance / admission / LearningOrder。

Front：

```text
中文短场景 / communicative intent
+ English minimal slot cue
→ active English production
```

Back：

```text
Target + Target TTS
Pattern
Meaning / Usage
1–2 Examples
```

TTS contract：

```text
Target      = 自动 TTS
Examples    = 当前只显示文字，不自动 TTS
```

长期 Front 演进仍为：

```text
Stage A — 中文短场景 + English cue
→ Stage B — concise English intent + English cue
→ Stage C — English-only situation / context
```

只修改 Learner Presentation，不修改 Stable ExpressionID，也不重建 Anki FSRS / Review History。

2026-09-06 用户明确授权将尚未逐张人工检查的剩余 57 张先按通过处理。为保留审计语义，ReviewBasis 记录为：

```text
user-authorized-batch-approval-without-individual-review
```

当前：

```text
approved       = 66
model-reviewed = 0
admitted       = 66
publishable    = 66
release-ready  = 66
```

---

## 4. Deterministic publish / Anki operational status

Expressions 生成链：

```text
upstream registries
→ tools/build_klose_expressions.py
→ publish/study.csv
→ publish/anki-import.csv
→ tools/check_klose_expressions_release_ready.py
```

正式唯一导入文件：

```text
anki/klose/expressions/publish/anki-import.csv
```

2026-09-06 用户已完成首次正式 Anki Desktop 导入并确认：

```text
Deck              = Klose-English::Expressions
Note Type         = Klose Expression
Card Type         = Production
Notes / Cards     = 66 / 66
LearningOrder     = 000001..000066
New #             = 1..66
AnkiWeb Sync       = completed
```

New # 只在全部 66 张仍为 `is:new` 时按 LearningOrder materialize；后续一旦进入真实 Learning / Review，不再用 repo 重建调度状态。

当前独立 Deck Options preset：

```text
Preset                = Klose Expressions
New cards/day         = 2
Maximum reviews/day   = 9999
Learning steps        = 1m 10m
New card gather order = Ascending position
New card sort order   = Order gathered
New/review order      = Show after reviews
FSRS                  = ON
Desired retention     = 90%
FSRS parameters       = Default parameters
FSRS search scope     = deck:"Klose-English::Expressions" -is:suspended
Reschedule on change  = OFF
```

当前状态：

```text
Build Valid        = yes
Content Releasable = yes
Anki Updated       = yes
Learning Admitted  = yes
Pilot Ready        = yes
```

Anki 是 FSRS / Review History / Due / Interval / Card State 真源；repo 这里只记录用户确认过的 operational baseline，不回写真实记忆状态。

---

## 5. NEXT TASK — real-learning pilot

Expressions 内容侧和首次 Anki 部署已经结束。下一步不是继续扩卡，而是让 Klose 按当前设置真实学习。

首月保持：

```text
New/day = 2
四年级优先 → 三年级
不因为 repo 顺序变化重排已进入 Learning / Review 的 Cards
```

第一周先观察实际负担，再决定是否需要调整 `New/day`；不要为了更快清完 66 张而提前提高。

建议第一周检查一次：

```text
Again ratio
actual daily review load
明显卡住的 Expression
是否只能背原句、不能替换 slot
Target TTS / 发音是否有问题
```

一个月后再做完整 pilot review。

---

## 6. One-month evaluation

只观察有决策价值的指标：

```text
Again ratio
slot substitution success
transfer to unseen situations
pattern over-generalization
pronunciation / fluency issues
actual daily review load
```

核心问题：Klose 是记住了一条原句，还是获得了可迁移、可主动调用的 Expression。

Front 是否从 Stage A 向 Stage B 演进，也只根据真实学习表现决定。

---

## 7. Next repo engineering work / deferred

Expressions pilot 可以在 Anki 中独立运行；仓库侧当前可并行推进第三方 Vocabulary corpus 构建。

原计划仍保留：

```text
Grade 1–3 Vocabulary actual-source reconciliation
```

仍 deferred：

- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 8. Beijing Edition Grade 1–6 Vocabulary pre-merge staging

2026-09-06 用户要求先整理 repo 内北京版一年级起点 1–6 年级上下册，并与当前 Klose Vocabulary 做 sense-aware 去重，但**暂时不得加入当前词表**。

当前 staging 入口：

```text
anki/klose/source_reference/beijing_start1_staging/PREMERGE_STATUS.md
```

当前基线：

```text
Source books                    = 12
Source occurrences              = 808
Distinct normalized MatchKeys   = 734
Existing stable identities compared = 901

surface exact-single            = 433
surface exact-multiple          = 7
surface format-alias            = 1
surface morphology              = 2
surface no-existing-match       = 291

Beijing Premerge Valid          = yes
Merge Authorized                = no
Klose Master / Release / Publish / Anki changed = no
```

已完成：

- 12 册 XLSX deterministic parsing；
- occurrence-level source row 保留；
- 与 `note_registry.csv + note_registry_extensions.csv` 全量比较；
- exact / multiple / format alias / morphology / new candidate 分桶；
- 10 个高风险 identity candidate 显式 review；
- 6 个真实 inflection candidate 显式 review，并清除 `hi -> his`、`Mr -> Mrs` 等误报；
- occurrence-level semantic collision review；
- 独立 CI + `tools/check_klose_beijing_premerge.py` gate；
- 所有 review 保持 `MergeAuthorized=no`。

已确认 surface-only 去重会产生错误。例如：

```text
May(月份) vs may(情态动词)
like=喜欢 vs weather ... like ...
square=广场 vs square=正方形
left=leave过去式 vs left=左边
```

北京版 XLSX 的 `释义` 是 dictionary-style broad gloss，不可直接当教材 target sense 真源；缺少 Unit / sentence context 的 held 项在未来 merge 前仍需 actual textbook / same-edition context 或明确标注为非 source-confirmed 的人工/模型决策。

当前北京版与 Klose Stable Identity 的比较结果现在只视为 staging diagnostic / candidate evidence；根据统一第三方 corpus 的长期设计，它**不是最终 Klose 去重结果**。

当前用户要求仍是 staging only，因此不要把北京版 provenance 写入 `master/source_occurrences.csv`，不要 append 北京版 NoteID，不改 learner/release/publish/Anki。

---

## 9. Third-party Multi-Edition Vocabulary Corpus — two-stage design + current progress

2026-09-06 用户确认长期目标：北京版只是第一个 seed，后续把人教版、沪教版及其他第三方小学教材词表持续累加到同一个统一第三方 corpus，按 learning unit / target sense 做 sense-aware 去重。

长期设计：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
```

两阶段流程冻结为：

```text
Stage A — 第三方内部

多个第三方教材 Raw Vocabulary
→ Source Adapters
→ 与 Third-party Unified Vocabulary 做 sense-aware 去重
→ 完整 Third-party Unified Vocabulary

Stage B — 所有第三方来源完成后

完整 Third-party Unified Vocabulary
→ 与 Klose Full Stable Identity Registry 做一次最终 sense-aware diff
→ Third-party New Vocabulary Pool
→ 后续全部作为 Klose 当前教材之外的新词学习
```

当前已接入两个独立 Source Adapter：

```text
Adapter #1  beijing_start1
Source books             = 12
Source occurrences       = 808
Distinct MatchKeys       = 734

Adapter #2  renjiao_start1
Source books             = 12
Source occurrences       = 908
Distinct MatchKeys       = 802
```

人教版目录同时存在“一年级起点”和“三年级起点”；当前只接入 `renjiao_start1`。三年级起点未来作为独立 adapter，不能静默混入一年级起点。

北京 + 人教一年级起点当前联合 Stage A 工作区：

```text
anki/klose/third_party_vocabulary/staging/

Total source occurrences       = 1716
Distinct normalized MatchKeys  = 1144
Cross-source exact overlaps    = 392
Single-source surfaces         = 752
Renjiao morphology candidates  = 6
Renjiao new-surface candidates = 403
Cross-source context reviews   = 392
Semantic-risk queue            = 287
```

当前工程状态：

```text
Renjiao Stage A Valid          = yes
Combined Stage A build         = yes
Cross-source context audit     = yes
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
Klose Master/Release/Publish/Anki changed = no
```

重要约束继续有效：

- 北京版只有 seed 身份，没有语义优先级；
- 第二个及后续教材在 Stage A **只和第三方 Unified Vocabulary 去重**，不因 Klose 当前已有同词而删除第三方 Identity；
- 在所有计划中的第三方来源处理完成前，不生成最终 `existing-in-klose / third-party-new` 结论；
- 早期与 Klose 的比较可以保留为 diagnostic / candidate evidence，但不能作为第三方 corpus 删除依据；
- 去重单位是 `learning unit / target sense`，不是字符串；
- 同 surface 不同义项必须允许多个第三方 Identity；
- morphology / phrase / punctuation 只产生 candidate，不自动 merge；
- 教材版本、最早年级、覆盖教材数、出现次数、年级分布都不作为学习决策维度；
- provenance 只在 raw / Source Occurrence 层保留用于回溯，不进入正常学习界面；
- 第三方统一 corpus 永远低于 Klose 实际教材 Source Truth 优先级。

当前下一步：

```text
1. 对 392 个北京/人教 exact-surface overlap 做 context-aware sense review；
2. 处理 6 个 morphology candidates；
3. 对人教 403 个 new-surface candidates 做 within-source homograph / sense split 检查；
4. 只有 Identity Resolution 足够稳定后，才开始 mint stable ThirdPartyID；
5. 然后再接入下一个教材 adapter，仍只执行 Stage A。
```
---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Expression Identity 分离；
- Expression Identity 以 `CanonicalForm + CommunicativeFunction` 判断；同 surface form 不同 function 必须允许 split；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- Expression 训练方向固定为 communicative intent → active production；
- Grade-4-related Expressions 当前优先于 Grade-3-only Expressions；
- Front 语言从中文支撑逐步演进到 English-only，但只修改 Presentation；
- Target 有 TTS；Examples 当前不自动 TTS；
- review basis 必须准确区分逐张确认、批量授权与 model review；
- LearningOrder 不进入内容 fingerprint；
- generated publish 文件禁止手工维护，只能由确定性上游状态得到；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
