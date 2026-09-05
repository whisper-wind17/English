# Klose Expressions System

本文定义 Klose 从小学延续到高中、大学的长期 Expressions 学习系统。目标不是保存教材句子，而是把已经理解和接触过的高价值英语表达，稳定转化为可主动调用的语言能力。

动态状态和当前 pilot 以根目录 `NEXT.md` 为准。

---

## 1. Learning objective

Vocabulary 与 Expressions 是不同 Learning Object：

```text
Vocabulary  = word / phrase / target sense
Expressions = communicative production unit
```

Expression 的学习目标不是“看到英文能理解”，而是：

```text
communicative intent / situation
→ actively produce appropriate English
```

因此 Anki Expressions 属于 **consolidation / retrieval layer**，不承担首次 acquisition。

理想学习链：

```text
Meaningful Input / Interaction
→ understand meaning and usage
→ notice useful expression / pattern
→ guided production
→ Anki retrieval + spacing
→ real speaking / writing reuse
```

只有已经通过教材、听力、阅读、对话或其他真实输入理解过的表达，才适合进入正式 Learning Admission。

---

## 2. Long-term architecture

正式链路：

```text
Source Evidence / Learner Need
→ Expression Occurrence
→ Candidate Extraction
→ Expression Identity Resolution
→ Stable ExpressionID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Release Registry
→ generated study.csv
→ generated anki-import.csv
→ Expression Release Gate
→ Anki
→ FSRS / Review History / Card State
→ Real-learning Feedback
```

小学阶段 Source 主要来自实际教材；以后可扩展到：

```text
Textbook
Reading / Listening
Teacher correction
Klose speaking / writing errors
Exam material
Authentic English content
Curated academic expressions
```

系统入口因此定义为 `Source Evidence / Learner Need`，而不是只绑定 textbook Useful Expressions。

---

## 3. Source Occurrence ≠ Expression Identity

教材原句属于 Source Fact，必须完整保存，但：

```text
一条教材原句 ≠ 一张 Anki Card
```

多个 Source Occurrence 可以映射到同一 Expression Identity。例如：

```text
She's a doctor.
Our neighbour is a firefighter.
→ [Person] is a/an [job].

We can do some chores.
We can go to the library.
→ We can [verb phrase].
```

反过来，一条较长原句也可能包含多个值得长期学习的 production units，因此逻辑关系允许：

```text
Occurrence 0..N ↔ 0..N ExpressionID
```

Pattern / slot 相似只用于 candidate matching；不能仅靠字符串或模板相似自动 merge。

---

## 4. Stable Expression Identity

Expression 使用独立长期主键：

```text
KE000001
KE000002
...
```

一个 Expression Identity 表示：

> 在一个明确 communicative function 下，值得长期主动调用的 canonical English realization。

最小 Identity：

```text
ExpressionID
CanonicalForm
FunctionKey
ExpressionType
SlotSchema
Status
CreatedFromOccurrence
```

Identity 判断不能只看 surface form。核心依据是：

```text
CanonicalForm + CommunicativeFunction
```

例如：

```text
KE000001
FunctionKey: ask_job
CanonicalForm: What's [person]'s job?
ExpressionType: slot_frame

KE000002
FunctionKey: request_permission
CanonicalForm: Can I [verb phrase]?
ExpressionType: slot_frame
```

ExpressionType 长期只保留必要分类：

```text
fixed
slot_frame
discourse_frame
```

spoken / written / formal / informal / academic 等属于 metadata，不制造新的 Identity 类型体系。

Stable ExpressionID 与 Vocabulary NoteID 同样受长期稳定性约束：普通内容修正、来源增加、教材升级、排序变化不得重编号或复用 ID；split / merge 必须显式 migration。

---

## 5. Vocabulary boundary

判断归属以 learning objective 为准。

例如：

```text
take part in
be responsible for
```

若训练目标是理解并记住词义/搭配，属于 Vocabulary。

```text
Would you mind [doing ...]?
One possible reason is that [clause].
```

若训练目标是面对交际意图时主动产出，属于 Expressions。

不得为了方便把完整 communicative pattern 塞进 Vocabulary，破坏 Vocabulary 的 `1 Note = 1 target sense`。

---

## 6. Learner Presentation

Stable ExpressionID 可以长期不变；Klose 在不同年龄阶段如何学习它，可以变化。

Presentation 至少包含：

```text
LearnerProfile
LearnerLevel
ExpressionID
Prompt
PromptHint
Target
Pattern
FunctionLabel
ContextNote
```

小学阶段 Prompt 可以使用中文场景提示；随着能力提高可以逐步转为英文 situation cue。不要把字段命名硬编码为 `ChinesePrompt`。

例如同一个 Expression：

```text
KE000010
CanonicalForm: What's the weather like in [place]?
```

小学 Presentation：

```text
Prompt: 询问悉尼的天气
slot: Sydney
Target: What's the weather like in Sydney?
```

以后可以变成：

```text
Prompt: Ask about the weather in Melbourne.
Target: What's the weather like in Melbourne?
```

Identity 与已有 Anki Review History 不因此改变。

Presentation fingerprint 应覆盖当前发布可见学习内容，例如：

```text
Prompt
PromptHint
Target
Pattern
FunctionLabel
ContextNote
LearnerLevel
```

这些字段变化后旧 approval 失效；`LearningOrder` 不进入内容 fingerprint。

---

## 7. Learning Admission

Source Grade、LearnerLevel、Learning Admission 必须继续分离。

一个 Candidate 不因为出现在教材 Useful Expressions 中就自动进入 Anki。

正式 admission 至少要求：

```text
communicative function clear
high transfer value
appropriate for current LearnerLevel
already understood through meaningful input
worth active production practice
presentation reviewed
```

低迁移、强上下文依赖、一次性叙述句应保留为 Source Fact，但可以永久 held。

LearningOrder 是 repo 中 curriculum/admission 状态；FSRS / Due / Interval / Review History / Card State 仍以 Anki 为真源。

---

## 8. Anki contract direction

长期 Deck / Note Type：

```text
Deck:      Klose-English::Expressions
Note Type: Klose Expression
```

不按年级建立 Deck。小学、高中、大学 Expressions 共用长期 Identity 与 Deck；来源和学习阶段通过 metadata / tags / admission 管理。

主 Card 训练方向固定为：

```text
Intent / Situation
→ English Production
```

典型 Front：

```text
【询问职业】
person: your mother
```

Klose 主动说：

```text
What's your mother's job?
```

Back：

```text
What's your mother's job?

Pattern:
What's [person]'s job?

TTS
```

正面优先使用场景 / intent / slot cue，避免长期形成机械的“完整中文句子 → 英文翻译”通路。

具体字段、模板和 tag contract 在 pilot implementation 时冻结。

---

## 9. Physical layout

Expressions 使用独立 bounded context，不复用 Vocabulary 的 Registry / Review / Publish 文件：

```text
anki/klose/expressions/
├── master/
│   ├── expression_registry.csv
│   ├── expression_occurrences.csv
│   ├── source_expression_map.csv
│   └── release_registry.csv
├── learner/
│   ├── current.csv
│   ├── learning_admission.csv
│   └── presentation_review_registry.csv
├── review/
│   └── candidate_registry.csv
├── anki/
│   └── note_contract.md
└── publish/
    ├── study.csv
    └── anki-import.csv
```

实际教材证据继续保存在：

```text
anki/klose/source_reference/
```

现有四上输入：

```text
rj_start1-grade4-upper-klose-expressions.csv
rj_start1-grade4-upper-pattern-candidates.csv
```

它们仍是 Source / Candidate，不直接成为正式 KE Notes。

---

## 10. Release gate

Expressions 必须建立与 Vocabulary 独立但同等级别的 executable gate。至少验证：

- ExpressionID stable，无静默重编号/复用；
- Source Occurrence 可追溯；
- candidate → identity 决策无 unresolved blocker；
- released Expression 的 communicative function 明确；
- Learning Admission 显式；
- current Presentation fingerprint 已 review / approve；
- allowed LearningOrder 唯一、连续、格式稳定；
- held Expression 无 LearningOrder；
- `study.csv` 可由当前上游状态确定性生成；
- `anki-import.csv` 与 released/admitted set 一致；
- 已存在 Anki FSRS / Review History 不因 repo rebuild 被重建。

---

## 11. Real-learning feedback

系统优化必须主要依据真实学习，而不是为了 schema 完整性不断增加字段。

Expressions 重点观察：

```text
Again ratio
response latency
can produce without Chinese translation
slot substitution success
pattern over-generalization
speaking pronunciation / fluency
transfer to unseen situations
real speaking / writing reuse
actual daily review load
```

尤其要区分：

```text
memorized one sentence
vs
acquired reusable production pattern
```

如果 Klose 只能复现卡片原句、不能替换 slot 或迁移到新场景，应优先修改 Presentation / practice design，而不是增加更多相似卡。

---

## 12. Current design decision

Phase B 先采用小规模 one-month pilot：

```text
freeze identity/release contract
→ resolve Grade-4 upper candidates
→ select a small high-value batch
→ create reviewed learner presentations
→ build deterministic publish + release gate
→ create formal Anki Note Type / Deck
→ run real learning for one month
→ evaluate before scaling
```

Pilot 的具体批次、LearningOrder、New/day 和评估状态以 `NEXT.md` 为准。
