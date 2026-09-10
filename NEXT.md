# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5–6 Klose 实际教材 Source materialization**。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md / docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/ relevant truth
```

## 2. Current state

```text
Grade 5 Upper  Vocabulary + Useful Expressions       = RECEIVED
Grade 5 Lower  Vocabulary + Useful Expressions       = RECEIVED
Grade 5 Lower  Appendix Proverbs (6)                 = RECEIVED
Grade 6 Upper  Vocabulary + Useful Expressions       = RECEIVED
Grade 6 Lower  Vocabulary + Useful Expressions       = RECEIVED

Grade 5–6 structured repo source                     = NOT STARTED
Morphology Registry                                  = NOT STARTED
Grade 5–6 → Klose Stable Identity reconciliation     = NOT STARTED
Grade 5–6 NoteID / ExpressionID allocation           = NOT STARTED
Klose Publish / Anki update                          = NOT STARTED
```

“RECEIVED”只表示用户已在当前对话提供真实教材图片；尚未结构化写入 `anki/klose/source_reference/`。

## 3. Hard decisions

- Grade 5–6 真实教材 **不先与第三方词库匹配**；固定路径是 `actual textbook → directly reconcile with Klose existing stable identities`。
- Vocabulary 按明确 target sense 建 identity；同词异义不可字符串合并。
- Useful Expressions 原句是 Source Fact，`1 source sentence != 1 Expression card`；后续按 `CanonicalForm + CommunicativeFunction` resolution。
- Grade 5 Lower 的 6 条 Proverbs 单独作为 Proverb Source。
- Grade 6 的过去式、比较级等进入独立 **Morphology Registry**；词形变化本身不 mint Vocabulary NoteID。
- Stable NoteID / ExpressionID 与已有 Anki FSRS / Review History 必须保持稳定。

详细 schema、边界、Completion Gate 与 reconciliation SOP：`docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md`。

## 4. Immediate next work

```text
1. Materialize all received Grade 5–6 Vocabulary / Useful Expressions / Proverbs
2. Build Morphology Registry from explicit textbook inflections
3. Run independent Source Completion Recheck
4. Only after 1–3 PASS: direct reconciliation against Klose existing Vocabulary / Expressions
```

Source Completion Recheck 至少确认四册/Units/对象类型覆盖完整、教材 metadata 可追溯、代表性 image-to-row spot check 通过，且没有第三方数据混入。

## 5. Mutation boundary

当前阶段禁止：

```text
third-party merge/allocation
Grade 5–6 Stable NoteID / ExpressionID allocation
Klose Master / Learner / Release mutation
publish regeneration for this task
Anki update
```

当前 DoD 是 **Grade 5–6 actual Source + Morphology 结构化并通过独立完整性验证**，不是合入或发布。

## 6. Third-party corpus — hold

第三方词库保持独立冻结：Stage A/B CLOSED，`2820` Vocabulary identities / `2794` learner candidates，实际 merge/allocation 未启动；当前显式 content exclusion 仅 `a / an / the`。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
