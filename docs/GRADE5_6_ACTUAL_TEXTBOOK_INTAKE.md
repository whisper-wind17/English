# Grade 5–6 Actual Textbook Intake

本文定义 Klose 实际使用的 Grade 5–6 教材资料从图片证据进入 repo、完成 Source capture、Morphology 拆分和后续与 Klose 现有 Stable Identity reconciliation 的当前任务规则。

动态状态和下一步以根目录 `NEXT.md` 为准；长期 Vocabulary / Expressions 规则分别见 `docs/KLOSE_VOCABULARY_SYSTEM.md`、`docs/EXPRESSIONS_SYSTEM.md`。

## 1. Scope

当前用户已提供以下实际教材图片证据：

```text
Grade 5 Upper: Vocabulary + Useful Expressions
Grade 5 Lower: Vocabulary + Useful Expressions + Appendix Proverbs (6)
Grade 6 Upper: Vocabulary + Useful Expressions
Grade 6 Lower: Vocabulary + Useful Expressions
```

这些材料在结构化写入 `anki/klose/source_reference/` 之前仍属于 received evidence，不得把“对话中收到”误记为“repo source 已完成”。

## 2. Authoritative path

用户已明确要求：Grade 5–6 实际教材数据 **不先与第三方词库做匹配**。

固定路径：

```text
Klose actual textbook evidence
→ Source capture / completeness verification
→ Vocabulary / Expression / Morphology boundary resolution
→ direct reconciliation against Klose existing Stable Vocabulary / Expressions
→ reviewed reuse / new / held decisions
→ stable ID allocation only after reconciliation closure
→ learner presentation / admission / review / release
→ generated publish / Anki update
```

禁止使用：

```text
actual textbook → third-party vocabulary → Klose
```

第三方 vocabulary corpus 保持独立冻结，除非用户未来单独启动其 merge/allocation。

## 3. Source capture contract

实际教材 Source 至少保留：

```text
SourceID
SourceEdition
Grade
Semester
Unit
Order
Starred
Entry / RawExpression
Meaning / Translation
Page
SourceStatus
```

原则：

- 实际教材照片/扫描件是本任务最高优先级 Source Evidence；
- Source Grade 只表示教材出现位置，不决定 LearnerLevel；
- SourceID / SourceEdition 若不能从现有 repo 与教材证据可靠确认，不得凭版式或记忆猜测；
- 同一词在不同 Unit / Book 再次出现时保留独立 occurrence；
- Source Reference 不直接获得 NoteID / ExpressionID，也不直接进入 publish。

## 4. Learning-object boundaries

### Vocabulary

教材词汇表中的普通 word / lexical phrase 先作为 Vocabulary Source。后续 identity 仍按 `surface + target sense` 判断；同词异义允许多个 Stable NoteID。

### Useful Expressions

Useful Expressions 原句完整保存为 Source Occurrence，但：

```text
1 source sentence != 1 Expression card
```

后续按 `CanonicalForm + CommunicativeFunction` 与 Klose 现有 Stable ExpressionID 做 function-aware reconciliation。低迁移或强上下文句可以只保留 Source，不自动 release。

### Proverbs

Grade 5 Lower Appendix 的 6 条谚语单独保存为 `Proverb Source`，不得与 Unit Useful Expressions 混成同一对象。是否进入 Expressions learner set 后续独立判断。

### Morphology Registry

Grade 6 开始系统出现过去式、比较级等显式词形。它们应进入独立 Morphology Registry，而不是仅因词形变化创建新的 Vocabulary Note。

建议最小字段：

```text
Lemma
FormType
InflectedForm
IPA
Grade
Semester
Unit
Page
SourceEntry
```

当前至少覆盖：

```text
verb past
adjective/adverb comparative
```

规则：

- 教材原始词形仍保留在 Source occurrence；
- Morphology Registry 建立 `lemma → inflected form` 关系；
- morphology similarity 不能自动 merge identity；
- morphology alone 不 mint 新 Vocabulary NoteID；
- `read → read /red/` 这类拼写不变、发音变化必须保留 IPA/读音事实；
- 将来若需要训练词形变化，应作为独立 learning object 设计，不污染 Vocabulary Note identity。

## 5. Materialization plan

第一阶段只做 Source，不做 Klose identity mutation：

```text
1. Transcribe Grade 5 Upper / Lower Vocabulary
2. Transcribe Grade 6 Upper / Lower Vocabulary
3. Transcribe all four books' Useful Expressions
4. Capture Grade 5 Lower Proverbs separately
5. Build Morphology Registry from explicit textbook inflections
6. Build completeness manifest
```

文件命名应沿用 `anki/klose/source_reference/` 的实际教材模式；在 SourceID / SourceEdition 未验证前，不得仅为了命名便利伪造 source identity。

## 6. Source Completion Gate

进入 Klose reconciliation 前必须独立确认：

```text
all 4 books covered
all Units represented
Vocabulary rows closed
Useful Expressions rows closed
Grade 5 Lower Proverbs = 6 and separately classified
Morphology entries traceable to source rows
Grade / Semester / Unit / Page / starred metadata preserved where visible
representative image-to-row spot checks pass
no third-party source mixed into this dataset
no Klose Master / Learner / Publish / Anki mutation
```

只有该 gate 通过后，才能开始 direct Klose reconciliation。

## 7. Direct Klose reconciliation

Vocabulary 直接与 Klose 当前 Stable NoteID registry 比较：

```text
same learning unit / same target sense → reuse existing NoteID
same surface / different target sense → separate identity
related morphology only → review, not auto-merge
truly new learning unit → propose new Stable NoteID
uncertain boundary → held
```

Expressions 直接与 Klose Stable ExpressionID 比较：

```text
same communicative function + same canonical realization → reuse
same surface but different function → separate identity/review
new reusable production unit → propose new ExpressionID
low-transfer / context-only → held or source-only
```

任何新 Stable ID allocation 都必须发生在 reconciliation closure 之后，并继续保护已有 Anki FSRS / Review History。

## 8. Mutation boundary

在 Source materialization + Source Completion Gate 完成前，禁止：

```text
third-party merge/allocation
Grade 5–6 Stable NoteID allocation
Grade 5–6 Stable ExpressionID allocation
Klose Master mutation
Klose Learner / Release mutation
publish regeneration for this task
Anki update
```

本任务当前阶段的 Definition of Done 是：**实际教材 Source 结构化、Morphology Registry 建立、完整性独立验证通过**；不是发布到 Anki。
