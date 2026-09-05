# Klose Vocabulary Data Area

本目录是 Klose 长期英语学习系统的数据区。

开始任何任务前先读：

```text
/AGENTS.md
/NEXT.md
```

长期架构与 SOP：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
docs/LEARNER_REVIEW_REGISTRY.md
docs/ANKI_FIRST_IMPORT.md
docs/ANKI_SYNC_WORKFLOW.md
```

## 当前状态

不要把历史 `Grade-4 Baseline v1` 的计数永久理解成“当前可学习状态”。2026-09-05 已发现 Klose 实际四年级上教材与当前第三方 `rj_start1::4年级上` Source 数据存在版本冲突。

当前 blocker、Anki 状态和 work order 统一以：

```text
/NEXT.md
```

为准。

当前四上实际教材证据与专项 reconciliation 位于：

```text
source_reference/
```

在 `NEXT.md` 明确解除 blocker 前，不应仅凭历史 release gate 或历史 `518 / 343 / 175` 结果让 Klose 开始正式学习。

## 核心原则

```text
Source Grade   = 教材在哪里出现
LearnerLevel   = Klose 今天怎么学
```

二者独立。Klose 可以在 `LearnerLevel=4` 下学习 Grade 5/6 来源词汇。

Vocabulary 与 Expressions 也是不同 Learning Object：

```text
Vocabulary  = word / phrase / target sense
Expressions = raw expression / reusable communicative pattern
```

Useful Expressions 不直接塞入 `Klose Vocabulary`。

## 目录

```text
anki/klose/
├── config/                    # learner / release scope config
├── master/                    # NoteID / source identity / release registries + master
├── learner/                   # current presentation / review registry / approvals
├── source_reference/          # Klose 实际教材证据与 reconciliation input
├── anki/                      # Note/Card template contract
├── publish/                   # generated outputs
└── review/                    # identity / learner / future review queues
```

### Persistent state

```text
master/note_registry.csv
master/source_identity_map.csv
master/release_registry.csv
learner/presentation_review_registry.csv
learner/review_approvals/
```

这些文件不是普通 generated cache；Stable NoteID、identity decision、release history 和 review approval 必须长期保留。

### Generated publish

```text
publish/study.csv       # internal released snapshot；不直接导入 Anki
publish/anki-import.csv # 唯一正式 Anki 导入文件
publish/all.csv         # inventory view
publish/onboarding/     # stage convenience views
publish/by-source/      # source/grade convenience views
```

禁止手工修改 `study.csv` / `anki-import.csv`。应修改上游 Source / Identity / Fact / Learner / Release，再 rebuild。

## Anki Contract

主 Deck：

```text
Klose-English::Vocabulary
```

Note Type：

```text
Klose Vocabulary
```

只保留一个：

```text
Recognition Card
```

所以：

```text
1 Note = 1 Card
```

正式导入第一数据字段固定为 `NoteID`。长期更新使用同一 Note Type、`Existing notes = Update`、`Match scope = Note Type`，保护现有 FSRS / Review History。

Card template 在：

```text
anki/
```

当前 Front 只显示 Word；Back 含 Word TTS、UK/US IPA、Meaning、Example、Translation。

## Source Reference

Klose 手中实际教材的人工核对资料进入：

```text
source_reference/
```

它是 source reconciliation input，不是 publish output。发生实际教材与第三方 XLSX 冲突时，按 `docs/SOURCE_RECONCILIATION.md` 处理，并优先确认 Edition / Revision，不能静默覆盖 provenance。

## 当前执行入口

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
```

显式 approval：

```text
tools/approve_klose_learner_review.py
```

只有真实逐条审校完成后才能执行。
