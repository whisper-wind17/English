# Klose Vocabulary Data Area

本目录是 Klose 长期统一词汇系统的数据区。完整机制见：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
```

Anki 从旧版 Word-first 迁移到 NoteID-first 的一次性步骤见：

```text
docs/ANKI_MIGRATION.md
```

## 目录

```text
anki/klose/
├── config/
│   └── profile.json
├── master/
│   ├── note_registry.csv
│   ├── release_registry.csv
│   ├── vocabulary_master.csv
│   ├── source_occurrences.csv
│   └── build_stats.csv
├── learner/
│   └── current.csv
├── publish/
│   ├── study.csv
│   ├── all.csv
│   ├── migration/
│   └── by-source/
└── review/
    ├── identity_review.csv
    └── learner_review.csv
```

## 哪个文件导入 Anki

长期默认只使用：

```text
publish/study.csv
```

`study.csv` 包含已经释放给 Klose 学习并需要持续更新的 Notes。

`publish/all.csv` 是完整 Master inventory，不是默认日常导入入口。

当前 profile：

```text
LearnerProfile = klose
LearnerLevel   = 4
Released       = rj_start1 1–4 年级
```

## 哪些文件不能随便重建

`master/note_registry.csv` 是长期身份 Registry。它虽然由第一次 bootstrap 建立，但此后属于持久化状态：

- 旧 NoteID 不得重排；
- 旧 NoteID 不得复用；
- 新 learning unit 只能追加新 NoteID。

`master/release_registry.csv` 记录已经释放给 Klose 的 Notes。release 默认是长期增长集合，不能因为当前关注范围改变就静默删除。

## 当前首批来源

```text
SourceID = rj_start1
人教版一年级起点 1–6 年级
```

source-specific 清洗/审校仍位于：

```text
anki/人教版一年级起点/
```

这个目录是当前来源的数据 adapter / curation 层；`anki/klose/` 才是未来多来源统一层。

## 构建

仓库根目录：

```bash
python tools/build_klose_vocabulary.py
```

对应 CI：

```text
.github/workflows/build-klose-vocabulary.yml
```

构建完成后必须检查：

```text
master/build_stats.csv
review/identity_review.csv
review/learner_review.csv
```

`identity_review.csv` 中的歧义不能通过自动规则静默合并。`learner_review.csv` 是语义/难度建议队列，不应把“0 条结构问题”表述成“所有内容已由老师人工确认”。