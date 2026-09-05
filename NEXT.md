# NEXT — Klose Learning

Last updated: 2026-09-05

新对话启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/SOURCE_RECONCILIATION.md
→ anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md
```

## Current objective

先完成 **Klose 实际四年级上教材与当前第三方 `rj_start1::4年级上` 的 Source Edition / Identity reconciliation**，再重新建立正式 learning admission，之后才让 Klose 开始学习。

核心不变量：

```text
Source Grade ≠ LearnerLevel
```

Klose 当前仍使用 `LearnerLevel=4`；未来学习 Grade 5/6 来源词汇也不自动提升 LearnerLevel。

## Architecture hardening completed

2026-09-05 已完成一轮“规则 → 可执行约束”的架构加固：

### Release gate

新增结构化状态：

```text
anki/klose/master/source_reconciliation_registry.csv
```

当前四上状态明确为：

```text
ReconciliationStatus = blocked
IdentityStatus       = pending
LearningAdmission    = blocked
```

`check_klose_release_ready.py` 现在会直接消费该状态，因此当前内容必须失败，不能再出现“文档 BLOCKED、程序却 Klose release ready”。

同时新增 upstream derivation 校验：`study.csv` 与 `anki-import.csv` 即使被同步篡改，也必须逐字段与当前 Master + Learner 上游一致，否则 gate 失败。

### Review fingerprint v2

当前 approval fingerprint 已覆盖：

```text
CanonicalWord
SenseLabel
Word
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerProfile
LearnerLevel
```

缺失 ContentFingerprint 不再自动继承旧审批，默认转 `pending`。旧 v1 approval 在下一次 sync 时会失效，需要在教材 reconciliation 后重新真实审校。

### Stable NoteID historical check

新增：

```text
anki/klose/master/identity_migrations.csv
```

`check_klose_persistent_state.py` 会比较 Git 父版本；旧 NoteID 不能消失，也不能静默改变：

```text
CanonicalWord
MatchKey
SenseLabel
PrimaryOriginKey
```

真正 identity split/merge 必须留下 approved migration 记录。

### Sense-aware identity extension

保留现有 legacy：

```text
source_identity_map.csv
```

新增：

```text
source_identity_extensions.csv
```

schema：

```text
SourceID
SourceEdition
SourceItemKey
NoteID
Decision
Status
```

目的：允许新 Edition / 同词多义拥有独立稳定 source item identity，同时避免一次性重写现有 518 条 baseline mapping。

### Learning admission

新增：

```text
anki/klose/learner/learning_admission.csv
```

以后正式 staging 应由：

```text
LearnerProfile + LearnerLevel + NoteID → Stage
```

显式决定，而不是由 Source Grade 推导。

当前文件尚为空，因此构建器保留 legacy Grade-4 staging fallback 仅用于迁移兼容；由于 Source Reconciliation gate 当前为 blocked，这个 fallback 不代表正式学习准入。

### Learner example checker

`check_klose_learner.py` 已区分：

```text
target vocabulary
vs
auxiliary vocabulary used to explain it
```

目标词自身不再因为 Source Grade > LearnerLevel 被判违规；这允许 `LearnerLevel=4` 学习 Grade 5/6 来源词汇。

### CI

CI 已扩展覆盖：

```text
source_reference/**
anki/klose/anki/**
source reconciliation / identity extension / migration registries
learning_admission.csv
approval manifests
```

并增加 PR 检查、`fetch-depth: 2`，用于 Git-baseline identity stability。

## Critical blocker

当前 repo 第三方四上 source 与 Klose 实际教材存在完整 Edition / Revision mismatch。

Klose 实际四上：

1. jobs / chores
2. personal traits
3. places / community
4. jobs
5. weather
6. clothes / seasons

当前专项诊断：

```text
anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md
```

状态：**BLOCKED FOR SOURCE RECONCILIATION**，且现在已经由程序 gate 同步表达。

## Identity blocker: cook

Klose 实际教材：

```text
Unit 1 cook = 烹饪；煮  # verb
Unit 4 cook = 厨师      # noun
```

当前 released `KV000424` 合并了两个 sense。

目标 migration：

```text
保留 KV000424 -> cook noun / 厨师
append 新 NoteID -> cook verb / 烹饪；煮
```

新 `cook verb` 应通过 `source_identity_extensions.csv` 建立带 Edition + sense-aware SourceItemKey 的 mapping；不得重编号旧 NoteID。

## Current Anki state

第一次 Desktop 导入与 AnkiWeb Upload 已完成，历史结果：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Cards             = 518
Suspended         = 343
Unsuspended       = 175
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

Klose 尚未产生真实 Review History。

### Safety rule

**不要让 Klose 开始正式学习。**

当前 175 active cards 的 staging 来自错误 Edition 的 legacy baseline。必须先完成 reconciliation 和 learning admission。

## Next work order

1. 完成 110 条实际四上 Core Vocabulary occurrence 的 identity decision。
2. 明确第三方四上数据属于哪个 Edition / Revision，并为 Klose 当前实际教材定义 `SourceEdition`。
3. 将实际教材 occurrence 物理落地为带 Edition / Unit / Page / stable source item identity 的记录。
4. 完成 `cook` noun/verb split migration：保留 KV000424，新增 verb NoteID。
5. 对 exact same-sense Notes 复用 NoteID + 增加实际教材 provenance；phrase/morphology 仅作为 candidate。
6. reconciliation 完成后，将 `source_reconciliation_registry.csv` 更新为 `reconciled / confirmed / allowed`。
7. 建立当前 released set 的显式 `learning_admission.csv`，停止依赖 legacy Grade-4 staging fallback。
8. 重新生成 learner presentation；review fingerprint v2 会使变化项/旧 v1 approval 转 pending。
9. 完成真实 review / approval，直到 pending=0。
10. rebuild + release gate，通过后重新生成 `anki-import.csv`。
11. 用同一 Note Type 原地更新 Anki，保护 NoteID 与未来 FSRS history。
12. 四上稳定后再接收四下；Grade 5/6 仍保持 `LearnerLevel=4` 准备。

## Deferred explicit migration

Homograph front-side disambiguation（如 `cook n.` / `cook v.`）方向已确认，但当前 Note Type 没有 `PromptHint` 字段。

不要直接向 `anki-import.csv` 偷加字段。后续单独设计一次 Note Type migration：

```text
add PromptHint field
→ update card front contract
→ ordinary words PromptHint=""
→ ambiguous homographs use minimal non-answer cue
→ preserve same NoteID / Card / FSRS history
```

## Grade 4 upper Definition of Done

- [ ] 110 条实际 Core Vocabulary occurrence 均有明确 identity decision
- [ ] SourceEdition / Revision 已显式建模
- [ ] same-sense Notes 复用稳定 NoteID并补 provenance
- [ ] phrase/morphology candidates 均做 sense-aware decision
- [ ] genuine new learning units append NoteID
- [ ] `cook` noun/verb split 完成
- [ ] source reconciliation registry = reconciled / confirmed / allowed
- [ ] LearnerLevel 保持 4
- [ ] explicit learning admission 覆盖全部 current released Notes
- [ ] release-visible v2 fingerprint current，pending=0
- [ ] corrected staging 重建完成
- [ ] content release gate 通过
- [ ] corrected `anki-import.csv` 可安全原地更新 Anki
- [ ] blocker 解除后 Klose 才开始正式学习

## Relevant docs

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
docs/LEARNER_REVIEW_REGISTRY.md
docs/ANKI_FIRST_IMPORT.md
docs/ANKI_FIRST_IMPORT_GUIDE.md
docs/ANKI_SYNC_WORKFLOW.md
anki/klose/source_reference/README.md
```
