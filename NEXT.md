# NEXT — Klose Learning

Last updated: 2026-09-06

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前任务继续读取：

```text
docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/rj_start1-grade3-klose-expressions.csv
→ anki/klose/source_reference/rj_start1-grade4-klose-expressions.csv
→ anki/klose/expressions/review/grade3-grade4-baseline.md
→ anki/klose/expressions/review/candidate_registry.csv
→ anki/klose/expressions/master/expression_registry.csv
→ anki/klose/expressions/learner/current.csv
→ anki/klose/expressions/learner/learning_admission.csv
→ anki/klose/expressions/anki/README.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Grade-4 Vocabulary status

Grade-4 Vocabulary 闭环已经完成并正常学习：

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

## 2. Current Phase B — Expressions one-month pilot

长期定位：

```text
Vocabulary  = recognition of word / phrase / target sense
Expressions = communicative intent / situation → active English production
```

Anki Expressions 可以承担已有输入后的 retrieval / consolidation，也可以承担简单新表达的 lightweight acquisition。`Again` 不区分首次遇见还是遗忘，统一表示“当前还不能稳定主动产出”。

### Current source scope

```text
Grade 3 upper + lower = 94 Source Occurrences
Grade 4 upper + lower = 72 Source Occurrences
Total                 = 166
```

一年级、二年级 Expressions 当前不纳入复习范围。

166 条 Source Occurrences 已整理为：

```text
Curated Pattern Candidates = 64
core                       = 38
secondary                  = 26
pilot_candidate            = 19
```

学习优先级：

```text
Grade-4 priority block = 36  # SourceGrades=4 或 3|4
Grade-3-only block      = 28
Total                   = 64
```

凡同一 Pattern 同时在三、四年级出现，只学习一次，并归入 Grade-4 priority block。正式顺序固定为：

```text
Grade 4 related first
→ Grade 3 only second
```

理论最多 64 张卡；Identity Review 允许进一步 merge / reject，因此最终数量可以更少。

---

## 3. First formal Expression completed

第一张正式卡已经从 Candidate 进入 Identity / Learner / Admission 层：

```text
ExpressionID   = KE000001
Candidate      = EC0021
FunctionKey    = ask_job
CanonicalForm  = What's [person]'s job?
ExpressionType = slot_frame
SlotSchema     = person
LearnerLevel   = 4
LearningOrder  = 000001
```

Source：

```text
Grade 4 upper / Unit 1 / Order 1
What's your mother's job?
```

Learner Presentation：

```text
FunctionLabel = 询问职业
Prompt        = 你刚认识一个同学，想了解他妈妈的职业。
PromptHint    = person: your mother
Target        = What's your mother's job?
Pattern       = What's [person]'s job?
MeaningUsage  = 询问某人是做什么工作的。
Examples      = What's your father's job? | What's your uncle's job?
```

当前正式状态：

```text
Identity      = active
Presentation  = approved
Admission     = allowed
LearningOrder = 000001
Publish       = pending
Release       = pending
```

Presentation approval 已绑定 `expression-presentation-v1` fingerprint；本轮用户确认的卡片设计作为 approval basis。

已建立首个 Expression bounded-context 文件：

```text
anki/klose/expressions/master/expression_registry.csv
anki/klose/expressions/master/expression_occurrences.csv
anki/klose/expressions/master/source_expression_map.csv
anki/klose/expressions/master/release_registry.csv
anki/klose/expressions/learner/current.csv
anki/klose/expressions/learner/learning_admission.csv
anki/klose/expressions/learner/presentation_review_registry.csv
```

Anki Contract 已建立：

```text
Deck      = Klose-English::Expressions
Note Type = Klose Expression
Card Type = Production
```

模板：

```text
anki/klose/expressions/anki/README.md
anki/klose/expressions/anki/card_front.html
anki/klose/expressions/anki/card_back.html
anki/klose/expressions/anki/styling.css
```

训练方向：

```text
Function / Situation + minimal cue
→ active English production
```

Back：

```text
Target + TTS
Pattern
Meaning / Usage
1–2 Examples
```

当前没有手工生成 `study.csv / anki-import.csv`，符合 generated publish 禁止手工编辑的长期规则。

---

## 4. NEXT TASK — expand Grade-4 pilot + build publish chain

下一步继续处理 Grade-4 priority 的 pilot candidates：

```text
identity review
→ freeze KE IDs
→ learner presentations
→ presentation review / approval
→ LearningOrder 000002...
```

随后实现 Expressions 独立生成链：

```text
upstream registries
→ deterministic study.csv
→ deterministic anki-import.csv
→ Expression Release Gate
→ first Anki import
```

在 release gate 完成前，不手工创建 publish artifact，也不声称第一张卡已经进入 Anki。

Pilot `New/day` 暂不冻结；首批正式 batch 与卡片复杂度确定后，再结合 Vocabulary `New/day=8` 和总复习负担设置。

---

## 5. One-month evaluation

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

## 6. Deferred work

- Grade 1–3 Vocabulary actual-source reconciliation：Expressions pilot 建立后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 7. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- Expression 训练方向固定为 communicative intent → active production；
- 简单新 Expression 可以通过 Back micro-lesson 首次学习；
- 不为首次见过 / 首次 Again 建额外状态；
- Grade-4-related Expressions 当前优先于 Grade-3-only Expressions；
- LearningOrder 不进入内容 fingerprint；
- generated publish 文件禁止手工修改；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
