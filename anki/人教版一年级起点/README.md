# 人教版一年级起点 → Anki

本目录面向“人教版一年级起点”小学英语教材，将原始 XLSX 词表整理为适合 Anki 长期复习的 CSV 数据。

## 数据原则

- 仅处理 `1.全国各大教材版本中小学同步/人教版/` 下 1–6 年级、上下册共 12 个“人教版一年级起点”文件。
- 原始 XLSX 保持不变。
- 同一个英文单词只保留一个主 Note，避免 FSRS 对同一词维护多份独立记忆状态。
- 单词第一次出现在哪一册，就进入该册的导入 CSV；后续重复出现只记录在 `Books` 和 `Tags` 中，不再次生成新 Note。
- `MeaningRaw` 保存原仓库的完整词典释义；`MeaningPrimary` 是给小学阶段卡片使用的精简释义。
- `MeaningStatus=override` 表示已用人工规则修正常见功能词；`auto` 表示从原始释义自动抽取，后续仍可人工校订。

## 目录

```text
anki/人教版一年级起点/
├── README.md
├── master/
│   ├── vocabulary_master.csv       # 去重后的唯一主表
│   ├── vocabulary_occurrences.csv  # 保留每一次教材出现位置，便于审计
│   └── build_stats.csv             # 构建统计
└── import/
    ├── 1年级上.csv
    ├── 1年级下.csv
    ├── ...
    └── 6年级下.csv
```

`master/` 是数据真源；`import/` 是按首次出现教材册切分后的 Anki 导入文件，不应单独手工维护。

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

一个单词如果首次出现在二年级上、又在四年级上出现，它只会存在于二年级上牌组，但 `Books` 会同时记录 `2年级上|4年级上`，Tags 也会保留后续出现信息。

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

建议建立一个自定义 Note Type：`Klose Vocabulary`。

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

如果需要训练主动拼写，再增加反向 Card；不建议刚开始同时大量引入正反两张新卡，否则每日新卡量会翻倍。

## Klose 推荐学习设置

- FSRS：开启
- Desired Retention：`0.93`
- Learning Steps：`10m`
- Relearning Steps：`10m`
- 每天先从约 5 个新单词开始；如果每个 Note 只生成一张 Card，即 `New cards/day ≈ 5`
- Reviews first
- Bury new/review siblings：开启（如启用了正反卡）
- 评分规则先简化为：记得 → `Good`；忘记/答错 → `Again`

## 重新生成

仓库根目录执行：

```bash
python tools/build_anki_rj_start1.py
```

脚本使用 Python 标准库直接解析 XLSX，不需要安装 pandas/openpyxl。每次构建会重建 `master/` 与 `import/`，并输出统计文件。

## 关于精简释义

当前 `MeaningPrimary` 的生成策略是保守的：常见功能词使用人工 override，其余从 `MeaningRaw` 中自动抽取第一主要中文义项。自动抽取无法保证完全等同于教材当课语境，因此 `MeaningStatus=auto` 的词条适合继续做人工抽查；`MeaningRaw` 始终保留，便于回溯和修正。