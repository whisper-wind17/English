# Klose Vocabulary Data Area

本目录是 Klose 长期统一词汇系统的数据区。完整机制见：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
```

旧 Word-first Anki 数据迁移见：

```text
docs/ANKI_MIGRATION.md
```

## 当前基线

```text
LearnerProfile = klose
LearnerLevel   = 4
SourceID       = rj_start1
Inventory      = 802 Notes
Released       = 518 Notes（人教版 1–4 年级）
```

人教版 1–6 年级共有 908 次 source occurrences。Stable NoteID Registry 已建立为 `KV000001`–`KV000802`。

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
│   ├── current.csv                # 当前 Grade-4 presentation
│   ├── grade4_overrides.csv
│   └── grade4_guardrail_overrides.csv
├── publish/
│   ├── study.csv                  # 默认长期 Anki 导入
│   ├── all.csv                    # 完整库存
│   ├── migration/
│   └── by-source/
└── review/
    ├── identity_review.csv
    ├── learner_review.csv
    └── future_vocab_review.csv
```

## 哪个文件导入 Anki

默认：

```text
publish/study.csv
```

`study.csv` 是已经释放给 Klose 学习、且以后需要持续获得内容更新的 Notes。`all.csv` 是完整 Master inventory，不是默认日常导入入口。

如果已经导入过早期 `anki/人教版一年级起点/import/*.csv`，不要直接导入 NoteID-first `study.csv`，先按 `docs/ANKI_MIGRATION.md` 完成一次性迁移。

## 持久化状态

以下三个文件不能视为普通缓存：

```text
master/note_registry.csv
master/source_identity_map.csv
master/release_registry.csv
```

规则：

- 旧 NoteID 不重排、不复用；
- 新 learning unit 只追加新 NoteID；
- 已 release Note 原则上持续留在 `study.csv`；
- identity merge/split 必须单独设计迁移。

## 当前首批 Source Adapter

```text
anki/人教版一年级起点/
```

它负责 source-specific 清洗、释义审校和原始 occurrence；`anki/klose/` 负责 Stable Identity、跨来源 Master、Learner Layer 和 Anki 发布。

## 构建

完整本地验证顺序：

```bash
python tools/check_klose_persistent_state.py
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/check_klose_learner.py
```

CI：

```text
.github/workflows/build-klose-vocabulary.yml
```

构建后必须检查：

```text
master/build_stats.csv
review/identity_review.csv
review/learner_review.csv
review/future_vocab_review.csv
```

当前三个 review queue 均为空。这里的 `0` 只表示对应自动/显式检查没有遗留项，不代表全部内容已经由出版社或英语教师人工认证。

## Grade-4 Learner Layer

当前四年级呈现层与教材首次出现年级解耦。低年级词可以使用适合四年级当前理解水平的自然例句。

同时保留一条严格 guardrail：已 release 的 Grade-4 例句不能无意使用人教版词表中明确到五/六年级才首次列出的内容词。该规则由：

```text
tools/check_klose_learner.py
```

在 CI 中强制执行。

未来升 Grade 5 时，升级 Learner Layer 即可；`NoteID`、source occurrences 和 Anki FSRS/Review History 不变。