# 人教版一年级起点 → Anki

本目录面向“人教版一年级起点”小学英语教材，将原始 XLSX 词表整理为适合 Anki 长期复习的 CSV 数据。

## 当前数据

本次构建处理 1–6 年级上下册共 12 个源文件：

- 教材词条出现次数：908
- 去重后唯一 Note：802
- 在多册教材中重复出现的单词：96
- 自动质量检查待复核项：0

详细统计见 `master/build_stats.csv`。其中 `meaning_review_items=0` 只表示当前规则没有发现空释义、词性残留、异常长释义等结构性问题，不代表 802 个 `MeaningPrimary` 已逐条按教材语境人工审核。

## 数据原则

- 仅处理 `1.全国各大教材版本中小学同步/人教版/` 下 1–6 年级、上下册共 12 个“人教版一年级起点”文件。
- 原始 XLSX 保持不变。
- 同一个英文单词只保留一个主 Note，避免 FSRS 对同一词维护多份独立记忆状态。
- 单词第一次出现在哪一册，就进入该册的导入 CSV；后续重复出现只记录在 `Books` 和 `Tags` 中，不再次生成新 Note。
- `MeaningRaw` 保存原仓库完整词典释义；`MeaningPrimary` 是给小学阶段卡片使用的精简释义。
- `MeaningStatus=override` 表示使用明确规则修正常见功能词、数字等；`auto` 表示从原始释义自动抽取第一主要义项。

## 目录

```text
anki/人教版一年级起点/
├── README.md
├── master/
│   ├── vocabulary_master.csv       # 802 个去重后的唯一 Note
│   ├── vocabulary_occurrences.csv  # 908 条原始教材出现记录，便于审计
│   ├── meaning_review.csv           # 自动质量检查待人工复核项
│   └── build_stats.csv             # 构建与分册统计
└── import/
    ├── 1年级上.csv
    ├── 1年级下.csv
    ├── ...
    └── 6年级下.csv
```

`master/` 是数据真源；`import/` 是按“首次出现教材册”切分后的 Anki 导入文件，不应单独手工维护。

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

例如 3 年级上原始有 104 条词条，但其中 30 个此前已经出现，因此只新增 74 个 Note。这样同一个词不会在不同 Deck 中产生两套独立的 FSRS 记忆状态。

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

导入某一册 CSV 时，将目标 Deck 选择为对应子牌组。例如 `4年级上.csv` 导入：

```text
Klose-English::人教版一年级起点::4年级上
```

一个单词如果首次出现在二年级上、又在四年级上出现，它只存在于二年级上牌组，但 `Books` 会记录 `2年级上|4年级上`，Tags 也保留后续出现信息。

如果要建立完整的小学词库，应按 1 年级上 → 6 年级下依次导入 12 个 CSV，而不是只导入当前年级；后续日常学习可以从父牌组统一复习，也可以只进入当前册学习新词。

## CSV 字段与 Anki 映射

| CSV 字段 | Anki 字段 | 用途 |
|---|---|---|
| `Word` | Word | 单词 |
| `British` | British | 英音 |
| `American` | American | 美音 |
| `MeaningPrimary` | MeaningPrimary | 卡片主要显示的精简释义 |
| `MeaningRaw` | MeaningRaw | 原始完整释义，建议默认不显示 |
| `Books` | Books | 出现过的教材册 |
| `Tags` | Tags | 年级/学期/教材出现位置标签 |

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
<div class="phonetic">英 {{British}} · 美 {{American}}</div>
```

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

## 重新生成

仓库根目录执行：

```bash
python tools/build_anki_rj_start1.py
```

脚本仅使用 Python 标准库直接解析 XLSX。每次构建会重建 `master/` 与 `import/`，并生成质量检查和统计文件。GitHub Actions 也会在源 XLSX 或构建脚本发生变化后自动重建并提交生成数据。

## 关于精简释义

原 XLSX 的“释义”来自通用词典，往往包含多个词性和成人词典义项，不适合直接显示给小学生。当前规则保留完整 `MeaningRaw`，同时生成较短的 `MeaningPrimary`：高频功能词、数字以及少量已识别异常词使用 override，其余取原始释义的第一主要中文义项。

这种处理能显著降低卡片噪声，但源数据没有 Unit、例句或教材上下文，因此无法仅靠词表判断每个多义词在具体课文中的目标义项。`MeaningPrimary` 应视为“适合第一版 Anki 使用的精简词义”，`MeaningRaw` 则作为可追溯依据。