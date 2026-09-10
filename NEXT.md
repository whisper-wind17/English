# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. 启动顺序

所有 Klose 任务固定读取：

```text
AGENTS.md
→ NEXT.md
→ 当前任务 docs
→ 与任务相关的 anki/klose/ 真源与 machine state
```

当前主任务：**Klose Grade 5–6 真实教材 Source intake / identity merge preparation**。

当前规则文档：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
docs/EXPRESSIONS_SYSTEM.md
anki/klose/source_reference/README.md
```

第三方词库 Stage-B 已闭合，`docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md` 仅作为独立历史/审计参考，不是当前 Grade 5–6 真实教材 intake 的输入链。

---

## 2. Current phase

```text
Third-party Phase A1 Source Ingestion      = CLOSED
Third-party Phase A2 Identity Closure      = CLOSED
Third-party Stage B Reconciliation         = CLOSED
Third-party actual merge/allocation        = GATED / NOT STARTED

Grade 5–6 Klose actual textbook capture   = MATERIALS RECEIVED IN CURRENT CONVERSATION
Grade 5–6 structured source materialize   = NOT STARTED
Grade 5–6 → existing Klose reconciliation = NOT STARTED
Grade 5–6 Stable NoteID / ExpressionID add = NOT STARTED
Klose Publish / Anki update                = NOT STARTED
```

第三方词库当前 machine checkpoint 保持不变：

```text
Stage-A checkpoint                 = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
Identity Vocabulary Preview        = 2820
Learner Vocabulary Preview         = 2794
Stage-B durable decisions          = 2820 / 2820
Stage-B review queue               = 0
Stage-B mutation authorized        = false
```

第三方 learner content policy 当前只显式排除 `a / an / the`；71 个 cardinal / ordinal number units 已重新 admitted。

---

## 3. Grade 5–6 Klose actual textbook materials received

用户已在当前对话提供 Klose 实际使用教材的图片资料，覆盖：

```text
Grade 5 Upper
  Vocabulary          = received
  Useful Expressions  = received

Grade 5 Lower
  Vocabulary          = received
  Useful Expressions  = received
  Appendix Proverbs   = received (6 proverbs; separate Source Object)

Grade 6 Upper
  Vocabulary          = received
  Useful Expressions  = received

Grade 6 Lower
  Vocabulary          = received
  Useful Expressions  = received
```

这些图片目前是**用户提供的真实教材证据**；尚未结构化写入 `anki/klose/source_reference/` CSV，因此不能把 `received` 误写成 `repo source materialized`。

正式落库时必须保留教材事实：

```text
SourceID / SourceEdition
Grade
Semester
Unit
Order
Starred (若教材有 *)
Raw Entry / Raw Expression
Meaning / Translation
Page
SourceStatus
```

SourceID / SourceEdition 若仅凭当前图片无法可靠确定，不得猜测；先标待确认或沿既有可证明的教材 source identity 规则处理。

---

## 4. User-confirmed integration policy — IMPORTANT

用户明确要求：

> Grade 5 / Grade 6 真实教材词汇与 Expressions **不要先与第三方词库做匹配处理**。

固定处理链：

```text
Klose actual Grade 5–6 textbook Source
→ structure / verify actual textbook occurrences
→ resolve Vocabulary / Expression / Morphology boundaries
→ directly reconcile against Klose existing Stable Vocabulary / Expressions
→ reuse existing stable IDs where same learning unit
→ allocate new IDs only for genuinely new learning units
→ learner presentation / admission / review
→ release / generated publish
→ Anki update only after explicit release gate
```

禁止改写为：

```text
actual textbook
→ third-party vocabulary reconciliation
→ Klose
```

第三方 2820 Vocabulary Identity 保持独立冻结状态，除非用户未来单独明确要求启动第三方 merge/allocation。

正式与 Klose 现有词库 reconciliation 时仍必须保护 Stable NoteID / ExpressionID：

- existing exact learning unit → reuse stable ID；
- same surface but different target sense → separate identity；
- genuinely new unit → append new stable ID；
- existing Anki FSRS / Review History 不得因新教材来源而重建或丢失；
- 不允许简单按字符串 append 造成重复卡。

---

## 5. Learning-object boundaries for Grade 5–6

### Vocabulary

普通教材词条进入 Vocabulary Source；一个 Vocabulary Note 仍对应一个明确 learning unit / target sense。

### Useful Expressions

教材 Useful Expressions 完整保存为 Source Occurrence，但：

```text
1 source sentence != 1 Expression card
```

后续按 `CanonicalForm + CommunicativeFunction` 与 Klose 现有 Stable ExpressionID 做 identity resolution；只把高迁移、值得主动产出的表达进入学习系统。

### Proverbs

Grade 5 Lower Appendix 5 的 6 条 Proverbs 单独保存为 `Proverb Source`，不与 Unit Useful Expressions 混为同一 Source Object。后续独立判断是否值得进入 Expressions learner set，不因教材列出而自动 release。

### Morphology Registry — NEW REQUIRED LAYER

从 Grade 6 开始，教材系统出现动词过去式、形容词比较级等 inflection。用户要求先单独存放；当前设计决定为统一 **Morphology Registry**，而不是把每个词形创建为普通 Vocabulary Note。

至少支持：

```text
Lemma | FormType | InflectedForm | IPA | Grade | Semester | Unit | Page
```

当前已观察的典型类型：

```text
verb past:
  be → was
  go → went
  see → saw
  eat → ate
  take → took
  run → ran
  read → read /red/
  make → made
  sing → sang
  wear → wore
  wake → woke
  begin → began
  win → won
  clean → cleaned
  stay → stayed
  wash → washed
  watch → watched
  have → had
  sleep → slept
  drink → drank
  ride → rode
  hurt → hurt
  buy → bought
  fall → fell
  can → could
  lick → licked
  laugh → laughed
  think → thought
  feel → felt

adjective/adverb comparative:
  young → younger
  old → older
  tall → taller
  short → shorter
  long → longer
  thin → thinner
  heavy → heavier
  big → bigger
  small → smaller
  strong → stronger
  smart → smarter
  low → lower
  well → better
  fast → faster
```

规则：

```text
Source occurrence retains the exact textbook form.
Inflected form is linked to lemma through Morphology Registry.
Morphology alone does not mint a new Vocabulary NoteID.
Future morphology training may consume this registry as a separate learning object.
```

---

## 6. Next execution task

下一步不是第三方 merge，也不是直接修改 Klose Master。

按以下顺序执行：

```text
1. Materialize Grade 5–6 actual textbook evidence
   - transcribe all received Vocabulary / Useful Expressions / Proverbs
   - preserve Grade / Semester / Unit / page / starred / raw meaning
   - build an explicit completeness manifest for all four books

2. Build Morphology Registry
   - extract past / comparative and other explicit textbook inflections
   - retain irregular pronunciation facts such as read → read /red/
   - verify no morphology form is silently treated as an independent Vocabulary identity

3. Independent source completion recheck
   - all 4 books covered
   - Unit coverage complete
   - Vocabulary / Expressions / Proverbs counts and source rows closed
   - representative image-to-row spot checks
   - no third-party source mixed into this dataset

4. Direct Klose reconciliation
   - actual textbook Vocabulary ↔ existing Klose Stable NoteIDs
   - actual textbook Expressions ↔ existing Klose Stable ExpressionIDs
   - sense-aware / function-aware, not string-only
   - produce reviewed reuse/new/held decisions before mutation

5. Only after reconciliation closure
   - append genuinely new stable IDs
   - build Learner Presentation / Admission / Review
   - regenerate publish deterministically
   - protect existing Anki FSRS / Review History
```

Do not start step 4 until step 1–3 have passed an independent Completion Recheck.

---

## 7. Current mutation boundary

Until the Grade 5–6 actual textbook source has been materialized and independently checked:

```text
Third-party merge/allocation       = prohibited
Grade 5–6 NoteID allocation        = prohibited
Grade 5–6 ExpressionID allocation  = prohibited
Klose Master mutation              = prohibited
Klose Learner/Release mutation     = prohibited
Publish regeneration for this task = prohibited
Anki update                        = prohibited
```

The immediate next work is **source materialization and completeness verification**, not learning-state mutation.
