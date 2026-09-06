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
→ anki/klose/source_reference/rj_start1-grade3-klose-expressions.csv
→ anki/klose/source_reference/rj_start1-grade4-klose-expressions.csv
→ anki/klose/expressions/review/grade3-grade4-baseline.md
→ anki/klose/expressions/review/candidate_registry.csv
→ anki/klose/expressions/review/grade4-pilot-review.md
→ anki/klose/expressions/master/expression_registry.csv
→ anki/klose/expressions/learner/current.csv
→ anki/klose/expressions/learner/learning_admission.csv
→ anki/klose/expressions/learner/presentation_review_registry.csv
→ anki/klose/expressions/anki/README.md
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

## 2. Expressions source baseline

当前只纳入 Klose 已学过的三、四年级实际教材 Expressions；一年级、二年级过于简单，暂不进入复习范围。

```text
Grade 3 Source Occurrences = 94
Grade 4 Source Occurrences = 72
Total                      = 166
```

166 条 Source Fact 已整理为：

```text
Curated Pattern Candidates = 64
core                       = 38
secondary                  = 26
pilot_candidate            = 19
```

学习优先级冻结为：

```text
Grade-4 priority block = 36  # SourceGrades=4 或 3|4
Grade-3-only block      = 28

Grade 4 related first
→ Grade 3 only second
```

跨年级相同 Pattern 只学习一次，并归到 Grade-4 priority block。

---

## 3. Current Grade-4 pilot — 9 formal identities

Grade-4 priority 的 pilot candidates 已完成第一轮 Identity Resolution，共 9 个 Stable Expressions：

```text
KE000001  What's [person]'s job?
KE000002  There is a/an [singular noun].
KE000003  Let's [verb phrase].
KE000004  What's the weather like in [place]?
KE000005  Whose [noun] is this?
KE000006  Can I [verb phrase]?
KE000007  What time is it?
KE000008  Can you please [verb phrase]?
KE000009  Would you like [thing]?
```

LearningOrder：

```text
000001..000009
```

当前全部属于 Grade-4 priority pilot；三年级独有 Expressions 尚未进入正式 Identity。

`EC0014` 在 Identity Review 中做了显式修正：Candidate 草案 `Can I [verb phrase], please?` 冻结为更通用的 `Can I [verb phrase]?`；`please` 作为可选礼貌成分进入 Usage，不作为 Identity 的强制组成部分。

Source Occurrence / mapping 已覆盖当前 9 个 Identity，包括跨三、四年级重复来源；Source Fact 与 Stable Identity 仍分离。

---

## 4. Learner Presentation / review state

Front 当前统一采用 Stage A：

```text
中文短场景 / communicative intent
+ English minimal slot cue
→ active English production
```

中文只建立意图，不写成完整中译英目标句。

长期演进保持：

```text
Stage A — 中文短场景 + English cue
→ Stage B — concise English intent + English cue
→ Stage C — English-only situation / context
```

语言升级只修改 Learner Presentation；Stable ExpressionID、CanonicalForm 和 Anki FSRS / Review History 不变。Presentation 变化后 fingerprint 必须重新 review。

当前 review state：

```text
approved       = 1  # KE000001，用户已确认
model-reviewed = 8  # KE000002..KE000009，尚未视为人工确认
```

`model-reviewed != approved`。模型生成并审校的卡片不得因为模板已获认可就自动冒充用户逐条确认。

人工 review 入口：

```text
anki/klose/expressions/review/grade4-pilot-review.md
```

---

## 5. Deterministic publish / release gate implemented

Expressions 独立发布链已经建立：

```text
upstream registries
→ tools/build_klose_expressions.py
→ publish/study.csv
→ publish/anki-import.csv
→ tools/check_klose_expressions_release_ready.py
```

共享 fingerprint：

```text
tools/klose_expression_review_fingerprint.py
```

关键门禁：

- Stable `KE000001...` Identity 唯一且 active；
- Candidate / CreatedFromOccurrence / confirmed source mapping 可追溯；
- 当前 pilot 只允许 Grade-4 priority identities；
- LearningOrder 六位、唯一、连续；
- current learner fingerprint 必须与 review registry 一致；
- 只有 `ReviewStatus=approved` 的 Presentation 能进入 publish；
- `model-reviewed` drafts 必须保持 `PublishStatus=pending / ReleaseStatus=pending`；
- `study.csv` 必须完全可由上游推导；
- `anki-import.csv` 数据必须与 `study.csv` 完全一致，且 Anki headers 固定。

本轮用当前上游状态执行同一生成/检查逻辑，结果：

```text
Built Klose Expressions:
approved = 1
drafts   = 8

Expression Release Gate PASS:
publishable            = 1
model_reviewed_drafts   = 8
admitted                = 9
```

当前 generated artifact 因此只包含已明确批准的 `KE000001`：

```text
anki/klose/expressions/publish/study.csv
anki/klose/expressions/publish/anki-import.csv
```

这不是缺失，而是门禁按设计阻止 8 张仅 model-reviewed 的 draft 泄漏到 Anki。

Anki 尚未更新。

---

## 6. NEXT TASK — approve Grade-4 pilot batch, then rebuild

下一步优先 review `KE000002..KE000009` 的 Stage-A Presentation：

```text
Front intent / cue
Target
Pattern
Meaning / Usage
Examples
```

确认后：

```text
ReviewStatus → approved
release PresentationStatus → approved
PublishStatus / ReleaseStatus 按生成与 gate 结果推进
→ rerun tools/build_klose_expressions.py
→ rerun tools/check_klose_expressions_release_ready.py
```

预期正式 publish 从 1 张扩展为 9 张。

随后才进入：

```text
Desktop 创建/确认 Klose Expression Note Type
→ import publish/anki-import.csv
→ LearningOrder materialize New #（仅 is:new）
→ Sync
→ iPad 实学一个月
```

Pilot `New/day` 仍不提前冻结；等 9 张正式 batch 与实际卡片复杂度确定后，再结合 Vocabulary `New/day=8` 和总复习负担设定。

---

## 7. One-month evaluation

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

不记录首次见过 / 首次 Again 等细粒度 acquisition history。

---

## 8. Deferred work

- Grade 1–3 Vocabulary actual-source reconciliation：Expressions pilot 建立后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 9. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- Expression 训练方向固定为 communicative intent → active production；
- 简单新 Expression 可以通过 Back micro-lesson 首次学习；
- Grade-4-related Expressions 当前优先于 Grade-3-only Expressions；
- Front 语言从中文支撑逐步演进到 English-only，但只修改 Presentation；
- `model-reviewed` 不等于人工 `approved`；
- LearningOrder 不进入内容 fingerprint；
- generated publish 文件禁止手工维护，只能由确定性生成链得到；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
