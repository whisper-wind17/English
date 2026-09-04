# 人教版一年级起点 → Anki

本目录面向“人教版一年级起点”小学英语教材，将原始 XLSX 词表整理为适合 Anki 长期复习的 CSV 数据。

## 当前数据

本次构建处理 1–6 年级上下册共 12 个源文件：

- 教材词条出现次数：908
- 去重后唯一 Note：802
- 在多册教材中重复出现的单词：96
- 已显式人工审校 `MeaningPrimary`：802 / 802
- 已补充年级适配例句与中文翻译：802 / 802
- 当前自动结构质检待复核项：0

详细统计见 `master/build_stats.csv`。`curation_review_items=0` 表示没有发现空释义、词性残留、空例句、异常长字段等结构性问题。

需要区分两种质量概念：当前 802 个词已经逐词检查并重新确定小学阶段主释义，但原始 XLSX 没有 Unit、课文原句等完整教材上下文，因此例句是按首次出现年级和已学基础词汇生成的学习例句，并非教材原句。

## 数据原则

- 仅处理 `1.全国各大教材版本中小学同步/人教版/` 下 1–6 年级、上下册共 12 个“人教版一年级起点”文件。
- 原始 XLSX 保持不变，作为拼写、音标、原始词典释义与出现位置的来源。
- 同一个英文单词只保留一个主 Note，避免 FSRS 对同一词维护多份独立记忆状态。
- 单词第一次出现在哪一册，就进入该册的导入 CSV；后续重复出现只记录在 `Books` 和 `Tags` 中。
- `MeaningRaw` 完整保留原词典释义，仅用于审计，不建议在儿童卡片上默认显示。
- `MeaningPrimary`、`ExampleSentence`、`ExampleTranslation` 来自 `curation/` 下的逐词审校数据。
- 构建时要求 802 个唯一词全部存在审校记录；缺一条、多一条、重复一条或缺少例句都会直接构建失败，不允许静默退回词典第一义项。

## 目录

```text
anki/人教版一年级起点/
├── README.md
├── curation/                       # 人工维护的数据层
│   ├── 1年级上.csv
│   ├── 1年级下.csv
│   ├── ...
│   └── 6年级下.csv
├── master/
│   ├── vocabulary_master.csv       # 802 个最终唯一 Note
│   ├── vocabulary_occurrences.csv  # 908 条原始教材出现记录
│   ├── curation_review.csv         # 自动结构质检待复核项
│   └── build_stats.csv             # 构建与分册统计
├── review_input/                    # 从 Master 导出的紧凑审校视图
└── import/                          # 真正导入 Anki 的文件
    ├── 1年级上.csv
    ├── 1年级下.csv
    ├── ...
    └── 6年级下.csv
```

`curation/` 是人工维护层；`master/` 和 `import/` 都由脚本生成，不应直接手工修改。

## 各册导入 Note 数

| 教材册 | 原始出现词条 | 首次出现、需要导入的 Note |
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

例如 3 年级上原始有 104 条词条，其中 30 个此前已经出现，因此只新增 74 个 Note。这样同一个词不会在不同 Deck 中产生两套独立 FSRS 记忆状态。

## 推荐 Anki 牌组结构

```text
Klose-English
└── 人教版一年级起点
    ├── 1年级上
    ├── 1年级下
    ├── 2年级上
    ├── 2年级下
    ├── ...
    └── 6年级下
```

导入某一册 CSV 时，将目标 Deck 选择为对应子牌组。例如：

```text
4年级上.csv
→ Klose-English::人教版一年级起点::4年级上
```

一个单词如果首次出现在二年级上、又在四年级上出现，它只存在于二年级上牌组，但 `Books` 会记录两个出现位置。

建立完整小学词库时，应按 1 年级上 → 6 年级下依次导入 12 个 `import/*.csv`，不要再额外导入 `master/vocabulary_master.csv`。

## CSV 字段与 Anki 映射

| CSV 字段 | Anki 字段 | 用途 |
|---|---|---|
| `Word` | Word | 单词或教材短语 |
| `British` | British | 英式音标；源数据为空则保持为空 |
| `American` | American | 美式音标；源数据为空则保持为空 |
| `MeaningPrimary` | MeaningPrimary | 经审校的小学阶段核心释义 |
| `ExampleSentence` | ExampleSentence | 与首次出现年级匹配的学习例句 |
| `ExampleTranslation` | ExampleTranslation | 例句中文翻译 |
| `MeaningRaw` | MeaningRaw | 原始完整词典释义；建议隐藏 |
| `Books` | Books | 该词出现过的教材册 |
| `Tags` | Tags | 年级、学期和出现位置标签 |

建议建立自定义 Note Type：`Klose Vocabulary`。

### Card 1：英文 → 中文

正面：

```html
<div class="word">{{Word}}</div>
<div class="phonetic">{{British}}</div>
```

背面：

```html
{{FrontSide}}
<hr id="answer">
<div class="meaning">{{MeaningPrimary}}</div>
<div class="example">{{ExampleSentence}}</div>
<div class="example-cn">{{ExampleTranslation}}</div>
<div class="phonetic">英 {{British}} · 美 {{American}}</div>
```

不建议默认显示 `MeaningRaw`。它包含成人词典中的多词性、多义项，主要用于后续核对。

### Card 2：中文 → 英文

需要训练主动拼写时再增加反向 Card。刚开始不建议同时大量引入正反两张新卡，否则每天实际新卡量会翻倍。

## Klose 推荐学习设置

- FSRS：开启
- Desired Retention：`0.93`
- Learning Steps：`10m`
- Relearning Steps：`10m`
- 先从约 5 个新单词/天开始；如果每个 Note 只生成一张 Card，则 `New cards/day ≈ 5`
- Reviews first
- Bury new/review siblings：开启（启用正反卡时）
- 评分先简化为：记得 → `Good`；忘记/答错 → `Again`

## 维护与重新生成

如果发现某个释义或例句需要调整，修改对应的：

```text
anki/人教版一年级起点/curation/<教材册>.csv
```

然后在仓库根目录执行：

```bash
python tools/build_anki_rj_start1.py
python tools/export_anki_review_input.py
```

脚本仅使用 Python 标准库。GitHub Actions 会在源 XLSX、构建脚本或 `curation/*.csv` 变化后自动重建并提交 `master/`、`import/` 和 `review_input/`。

## 释义与例句质量边界

原 XLSX 的“释义”来自通用词典，存在大量不适合小学语境的首义，例如 `running→运转`、`present→现在`、`May→可以`、`safe→保险箱`、`doctor→修理`、`hot pot→英式炖肉`。这些错误已经在 `curation/` 层按小学教材语境重新确定。

例句遵循“短、直接、体现目标义项、难度不高于首次出现年级”的原则，通常优先复用已学或同阶段基础词汇。由于源数据缺少完整教材正文，例句不声称与课文逐句一致；若以后补充教材 Unit/课文文本，可以进一步做严格的词汇可见性和语法进度校验。
