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

而不是伪装成逐张人工审核。

当前：

```text
approved       = 66
model-reviewed = 0
admitted       = 66
publishable    = 66
release-ready  = 66
```

`presentation_review_registry.csv` 是 approval 状态真源；`full-baseline-review.md` 主要作为内容 review sheet，不以其中历史统计替代当前 registry/NEXT 状态。

---

## 4. Deterministic publish / release status

Expressions 生成链：

```text
upstream registries
→ tools/build_klose_expressions.py
→ publish/study.csv
→ publish/anki-import.csv
→ tools/check_klose_expressions_release_ready.py
```

当前 full baseline 已按同一 deterministic derivation 重建；结构校验通过：

```text
publishable     = 66
grade4_priority = 37
grade3_only     = 29
drafts          = 0
LearningOrder   = 000001..000066
```

正式唯一导入文件：

```text
anki/klose/expressions/publish/anki-import.csv
```

当前状态：

```text
Build Valid        = yes
Content Releasable = yes
Anki Updated       = no
Learning Admitted  = yes
```

不要手工修改 generated `study.csv` / `anki-import.csv`。后续 Presentation / Admission 变化仍必须从上游确定性重建。

---

## 5. NEXT TASK — first full Anki import

现在内容侧已经完成，下一步等待用户有条件操作 Anki Desktop：

```text
1. 创建/确认 Deck: Klose-English::Expressions
2. 创建/确认 Note Type: Klose Expression
3. 按 anki/klose/expressions/anki/README.md 配置 12 fields / Production template / styling
4. 导入 anki/klose/expressions/publish/anki-import.csv
5. 验证 Notes = Cards = 66
6. 仅对 is:new Cards 按 LearningOrder materialize New #
7. 设置 Expressions Deck Options / New cards per day
8. Sync 到 AnkiWeb / iPad
9. 开始真实学习
```

Anki 是 FSRS / Review History / Due / Interval / Card State 真源；repo 不重建这些状态。

Expressions `New/day` 尚未冻结。首次导入时结合 Vocabulary `New/day=8` 和实际总负担设置；不要一次性引入全部 66 张。

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

---

## 7. Deferred work

- Grade 1–3 Vocabulary actual-source reconciliation：Expressions 首次正式导入后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 8. Frozen long-term rules

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
