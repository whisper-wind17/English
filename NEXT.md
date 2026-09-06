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
```

不要仅凭聊天历史推测当前状态。

---

## 1. Grade-4 Vocabulary status

Grade-4 Vocabulary 闭环已经完成：

```text
Build Valid                 = yes
Content Releasable          = yes
Anki content updated        = yes
Learning Admitted           = yes
LearningOrder in repo       = yes
LearningOrder in Anki New # = yes
```

当前 Anki：

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

Anki Expressions 可以承担：

```text
已有输入后的 retrieval / consolidation
+ 简单新表达的 lightweight acquisition
```

`Again` 不区分首次遇见还是遗忘，统一表示“当前还不能稳定主动产出”。

### Current source scope

本次 pilot 只使用 Klose 已学过的三、四年级实际教材 Expressions：

```text
Grade 3 upper + lower = 94 Source Occurrences
Grade 4 upper + lower = 72 Source Occurrences
Total                 = 166
```

一年级、二年级 Expressions 当前不纳入复习范围，因为对 Klose 已过于简单。这是当前 Learning Scope 决策，不改变长期系统可接收更低年级 Source Evidence 的能力。

年级合并 Source：

```text
anki/klose/source_reference/rj_start1-grade3-klose-expressions.csv
anki/klose/source_reference/rj_start1-grade4-klose-expressions.csv
```

### Candidate baseline complete

166 条教材原始表达已完成第一次统一 Pattern curation / 跨年级去重：

```text
Curated Pattern Candidates = 64
core                       = 38
secondary                  = 26
pilot_candidate            = 19
```

按学习优先级进一步分为：

```text
Grade-4 priority block = 36  # SourceGrades=4 或 3|4
Grade-3-only block      = 28  # SourceGrades=3
Total                   = 64
```

凡一个 Pattern 同时在三、四年级出现，只学习一次，并归到 Grade-4 priority block。

正式学习顺序已经冻结为：

```text
Grade 4 related first
→ Grade 3 only second
```

因此未来正式 LearningOrder 必须先覆盖 36 个 Grade-4 priority Expressions，再进入 28 个 Grade-3-only Expressions。Candidate Registry 当前行序不等于正式 LearningOrder。

当前 64 个 Candidate 对应理论最多 64 张卡；Identity Review 如果进一步 merge / reject，最终数量可以少于 64。不得为了保留年级来源而重复创建同一个 Pattern 的卡。

结构化结果：

```text
anki/klose/expressions/review/candidate_registry.csv
anki/klose/expressions/review/grade3-grade4-baseline.md
```

当前 `ECxxxx` 只是 candidate review 临时编号，不是 Stable ExpressionID。

### NEXT TASK — pilot identity resolution

下一步处理 `PilotCandidate=yes`，并首先处理 Grade-4 priority candidates：

```text
review communicative function
→ review CanonicalForm
→ review ExpressionType / SlotSchema
→ resolve overlaps / answer-pair boundaries
→ freeze first Expression identities
→ assign stable KE000001...
```

Stable KE IDs 不承担学习顺序语义；实际先后由 LearningOrder 表达。

identity review 完成后再进入：

```text
Learner Presentation
→ card-back micro-lesson
→ Review / Approval
→ Learning Admission + LearningOrder
→ deterministic publish
→ Expression Release Gate
→ Anki schema / first import
```

当前不要直接从 candidate_registry.csv 生成 Anki 卡。

### Pilot Anki direction

```text
Deck      = Klose-English::Expressions
Note Type = Klose Expression
Card      = Intent / Situation → English Production
```

Front 优先采用：

```text
communicative intent / situation
+ minimal slot cue
```

Back 至少包含：

```text
Target
Canonical Pattern
简短 Meaning / Usage
1–2 个替换例子
TTS
```

Pilot `New/day` 仍未冻结；等正式 batch 与卡片复杂度确定后，再结合 Vocabulary `New/day=8` 和总复习负担设置。

---

## 3. One-month evaluation

只观察有决策价值的指标：

```text
Again ratio
slot substitution success
transfer to unseen situations
pattern over-generalization
pronunciation / fluency issues
actual daily review load
```

核心问题：Klose 是记住了一条卡片原句，还是获得了可迁移、可主动调用的 Expression。

不额外分析“第一次 Again”。

---

## 4. Deferred work

- Grade 1–3 Vocabulary actual-source reconciliation：Expressions pilot 建立后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 5. Frozen long-term rules

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
