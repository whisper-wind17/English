# 人教版一年级起点：Source Adapter / Curation

本目录负责把“人教版一年级起点”1–6 年级原始 XLSX 整理成可追溯、可审校的 **source-specific 数据层**。它现在是 Klose Vocabulary System 的第一个 Source Adapter，而不再是长期 Anki 牌组的最终发布入口。

长期机制见：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
```

真正给 Klose 长期导入 Anki 的默认文件是：

```text
anki/klose/publish/study.csv
```

如果已经导入过旧版 Word-first CSV，先执行：

```text
docs/ANKI_MIGRATION.md
```

---

## 当前来源数据

人教版一年级起点共处理：

- 12 册：1–6 年级，上/下册；
- 908 次教材词条出现；
- 当前 source-specific 去重后 802 个 learning units；
- 96 个词/短语跨册重复出现；
- 802/802 已有显式 `MeaningPrimary`、学习例句和中文翻译；
- 原始 XLSX 不修改，继续作为 provenance 来源。

注意：这里的“审校”是项目内逐项审校/模型辅助结果，不代表出版社或英语教师认证。原始 XLSX 也缺少完整 Unit/课文上下文，因此不能把自动质检通过等同于“教材语义完全人工确认”。

---

## 本目录在长期架构中的职责

```text
Raw XLSX
   ↓
anki/人教版一年级起点/
   ├── curation/          # source-specific 释义/例句维护
   ├── master/            # source master + occurrences
   ├── review_input/      # 紧凑审校视图
   └── import/            # 旧版/兼容 source views
          ↓
anki/klose/               # 跨来源统一 Vocabulary System
   ├── master/
   ├── learner/
   ├── publish/
   └── review/
```

本目录负责“人教版这个来源说了什么”；`anki/klose/` 负责“这个 learning unit 在整个 Klose 词汇系统中的身份是什么、现在怎样学习、怎样发布到 Anki”。

---

## 数据原则

- 仅处理 `1.全国各大教材版本中小学同步/人教版/` 中的 12 个“人教版一年级起点”文件。
- 原始 XLSX 保持不变。
- `MeaningRaw` 保留原词典释义，用于审计；儿童卡片不默认展示。
- `MeaningPrimary` / `ExampleSentence` / `ExampleTranslation` 在 `curation/` 中维护。
- source-specific 构建要求 802 个当前唯一项都有审校记录；缺失、重复、空例句或结构异常会失败。
- source-specific 例句检查仍可用于发现明显的“提前使用后续教材词汇”问题，但长期 learner 难度以 `anki/klose/` 的 `LearnerLevel` 为准。
- 本目录当前按 surface form 去重，是首批来源的 adapter 行为；跨教材后的最终 identity 由 `anki/klose/master/note_registry.csv` 决定，不得把 surface form 当作永久业务主键。

---

## 目录

```text
anki/人教版一年级起点/
├── curation/
│   ├── 1年级上.csv
│   ├── 1年级下.csv
│   ├── ...
│   └── 6年级下.csv
├── master/
│   ├── vocabulary_master.csv
│   ├── vocabulary_occurrences.csv
│   ├── curation_review.csv
│   ├── example_vocab_review.csv
│   └── build_stats.csv
├── review_input/
└── import/
    ├── 1年级上.csv
    ├── ...
    └── 6年级下.csv
```

`curation/` 是 source-specific 显式维护层；`master/`、`review_input/` 和 `import/` 由脚本重建。

### 关于 `import/*.csv`

这些 12 个 CSV 是早期按“首次出现教材册”生成的兼容产物。它们仍可用于 source 数据检查，但**不再推荐作为 Klose 长期 Anki 导入入口**，也不再推荐按 12 个子 Deck 维护。

长期统一使用：

```text
Klose-English::Vocabulary
```

以及：

```text
anki/klose/publish/study.csv
```

年级/来源通过 Tags、release scope、Suspend/Filtered Deck 管理。

---

## source-specific 各册统计

| 教材册 | 原始出现词条 | 首次出现 Note |
|---|---:|---:|
| 1年级上 | 53 | 53 |
| 1年级下 | 45 | 45 |
| 2年级上 | 54 | 54 |
| 2年级下 | 55 | 55 |
| 3年级上 | 104 | 74 |
| 3年级下 | 84 | 62 |
| 4年级上 | 116 | 96 |
| 4年级下 | 87 | 79 |
| 5年级上 | 66 | 60 |
| 5年级下 | 101 | 95 |
| 6年级上 | 102 | 90 |
| 6年级下 | 41 | 39 |

这些数字用于理解来源分布，不再决定 Anki Deck 结构。

---

## 维护与重建

修改人教版 source-specific 内容后：

```bash
python tools/build_anki_rj_start1.py
python tools/check_anki_example_vocab.py
python tools/export_anki_review_input.py
```

随后全局 Klose Vocabulary 会通过对应 workflow 重新构建；本地完整验证可执行：

```bash
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/check_klose_learner.py
```

CI：

```text
.github/workflows/build-anki-rj-start1.yml
.github/workflows/build-klose-vocabulary.yml
```

长期维护时，source-specific 数据只负责来源事实；Stable NoteID、release 状态和 Anki 发布契约以 `anki/klose/` 为准。