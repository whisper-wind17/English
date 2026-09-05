# Klose Vocabulary Data Area

本目录是 Klose 长期统一词汇系统的数据区。完整机制见：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
```

第一次正式导入 Anki：

```text
docs/ANKI_FIRST_IMPORT.md
```

旧 Word-first Anki 数据迁移：

```text
docs/ANKI_MIGRATION.md
```

## 当前正式基线

```text
LearnerProfile = klose
LearnerLevel   = 4
SourceID       = rj_start1
Inventory      = 802 Notes
Released       = 518 Notes（人教版 1–4 年级）
```

人教版 1–6 年级共有 908 次 source occurrences。Stable NoteID Registry 已建立为 `KV000001`–`KV000802`。

Grade-4 Baseline v1 已完成逐条模型审校并通过 release gate：

```text
review registry      = 518
model-reviewed       = 518
human-reviewed       = 0
pending              = 0
identity review      = 0
learner review       = 0
future vocab review  = 0
```

审批批次：

```text
learner/review_approvals/grade4-baseline-v1.csv
```

## 当前学习阶段

518 个 released Notes 全部进入同一个 Anki 主 Deck，但学习阶段通过 Tags 控制：

```text
stage::grade4-new             175
stage::grade4-review           26
stage::lower-grade-backfill   317
```

第一次使用时完整导入 `publish/anki-import.csv`，然后只保持 `stage::grade4-new` 为 Unsuspended；另外两组先 Suspend。

这三组不是三个 Deck。长期主 Deck 始终是：

```text
Klose-English::Vocabulary
```

## 目录

```text
anki/klose/
├── config/
│   └── profile.json
├── master/
│   ├── note_registry.csv          # 永久身份 Registry
│   ├── source_identity_map.csv    # SourceItem → NoteID 持久映射
│   ├── release_registry.csv       # 已释放学习集合及实际释放日期
│   ├── vocabulary_master.csv
│   ├── source_occurrences.csv
│   └── build_stats.csv
├── learner/
│   ├── current.csv
│   ├── grade4_*                   # Grade-4 显式 learner review/override 层
│   ├── presentation_review_registry.csv
│   └── review_approvals/          # 不可覆盖的显式审批批次
├── anki/
│   ├── card_front.html            # 唯一 Recognition Card 正面
│   ├── card_back.html             # 唯一 Recognition Card 背面
│   ├── styling.css
│   └── README.md                  # 1 Note = 1 Card 契约
├── publish/
│   ├── study.csv                  # released Notes 内部数据真源/审计 CSV
│   ├── anki-import.csv            # 唯一正式 Anki 导入文件
│   ├── all.csv                    # 完整库存
│   ├── onboarding/                # 学习阶段便利视图，不是独立 Deck
│   ├── migration/
│   └── by-source/
└── review/
    ├── identity_review.csv
    ├── learner_review.csv
    └── future_vocab_review.csv
```

## 哪个文件导入 Anki

第一次以及以后长期更新都使用：

```text
publish/anki-import.csv
```

`study.csv` 不直接导入 Anki。它有普通 CSV 表头，用于 repo 内部构建、审计和与 Released Set 对账。`anki-import.csv` 使用 Anki 官方 `#...` file headers，并由 release gate 验证其数据与 `study.csv` 完全一致。

不要同时额外导入 `onboarding/*.csv` 或 `by-source/*.csv`。这些只是同一批 Master Notes 的视图。

如果已经导入过早期 `anki/人教版一年级起点/import/*.csv`，不要直接导入 NoteID-first 新发布文件，先按 `docs/ANKI_MIGRATION.md` 完成一次性迁移。

## 持久化状态

以下文件不是普通缓存：

```text
master/note_registry.csv
master/source_identity_map.csv
master/release_registry.csv
learner/presentation_review_registry.csv
learner/review_approvals/*.csv
```

规则：

- 旧 NoteID 不重排、不复用；
- 新 learning unit 只追加新 NoteID；
- 已 release Note 原则上持续留在 `study.csv` / `anki-import.csv`；
- review 状态绑定 ContentFingerprint；Meaning/Example/Translation 变化会使旧 approval 失效；
- identity merge/split 必须单独设计迁移。

## 当前首批 Source Adapter

```text
anki/人教版一年级起点/
```

它负责 source-specific 清洗、释义审校和原始 occurrence；`anki/klose/` 负责 Stable Identity、跨来源 Master、Learner Layer 和 Anki 发布。

## 构建与发布检查

完整验证顺序：

```bash
python tools/check_klose_persistent_state.py
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/sync_klose_learner_review_registry.py
python tools/check_klose_learner.py
python tools/check_klose_release_ready.py
```

显式 Learner Review 审批工具：

```text
tools/approve_klose_learner_review.py
```

它不进入日常 CI，只能在完成真实逐条审校后使用，并会生成 fingerprint-bound approval manifest。

CI：

```text
.github/workflows/build-klose-vocabulary.yml
```

Release gate 必须在 generated data commit/push 之前通过，避免“先发布错误数据、后报 CI 失败”。

## Grade-4 Learner Layer

当前四年级呈现层与教材首次出现年级解耦。低年级词使用适合 Klose 当前四年级理解水平的自然例句，同时不机械增加句子复杂度。

严格 guardrail：已 release 的 Grade-4 例句不能无意使用人教版词表中明确到五/六年级才首次列出的内容词。

未来升 Grade 5 时，只升级 Learner Layer 并建立新的 Level-5 review/approval；`NoteID`、source occurrences 和 Anki FSRS/Review History 不变。
