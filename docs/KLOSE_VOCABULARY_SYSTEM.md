# Klose Vocabulary System

> 本文定义本仓库中面向 Klose 的长期英语词汇学习系统。目标不是做一套一次性 Anki 牌组，而是建立一个可持续多年扩展、可追溯、可升级、不会破坏既有记忆历史的 Vocabulary Knowledge Base，并由 Anki 负责 SRS/FSRS 调度。

## 1. 核心目标

系统需要同时支持两条长期演进轴：

1. **Vocabulary Expansion**：随着教材、阅读材料和学习阶段扩展，不断增加新单词；已经进入 Anki 的旧词继续沿用原有 FSRS 记忆历史。
2. **Learner Presentation Evolution**：随着 Klose 年级和英语能力提升，已有单词的例句、表达复杂度等学习呈现可以整体升级，但不能因此创建新的 Note 或重置既有复习历史。

教材来源可以逐步扩展到：人教版一年级起点、北京版、沪教版、新概念、分级阅读等。Anki 中仍尽量维护一个统一词汇系统，而不是每增加一个教材就创建一套互相独立的记忆状态。

---

## 2. 两个系统，各自负责什么

### GitHub Repository：内容真源

GitHub 负责回答：

- 这个词是什么？
- 标准词形是什么？
- 音标和核心释义是什么？
- 出现在哪些教材、年级、册次？
- 当前 Learner Level 应该展示什么例句？
- 哪些字段来自原始教材，哪些字段经过审校或生成？

### Anki：学习状态真源

Anki 负责回答：

- Klose 是否已经见过这个词？
- 记忆稳定度如何？
- 下次什么时候复习？
- 当前 Card 是 New / Learning / Review / Suspended 中哪种状态？
- 完整 Review History 是什么？

**禁止反向依赖。** GitHub 不保存或重建 Anki 的 FSRS 记忆状态；Anki 也不是词汇事实数据的唯一真源。

---

## 3. 数据模型：三层分离

### 3.1 Vocabulary Identity / Fact Layer

这是长期稳定层。

推荐字段：

```text
NoteID
CanonicalWord
Word
British
American
MeaningPrimary
```

其中：

- `NoteID`：永久 ID；创建后原则上永不修改、永不复用。
- `CanonicalWord`：用于跨来源识别同一 lexical item 的标准形式。
- `Word`：当前显示词形。
- `MeaningPrimary`：面向当前基础教育阶段的核心释义，不直接展示成人词典的全部多义项。

### 3.2 Source / Provenance Layer

这是可持续增加的来源层。

推荐字段：

```text
FirstSource
FirstGrade
FirstSemester
Sources
SourceBooks
SourceOccurrences
```

示例：

```text
NoteID: KV000001
CanonicalWord: apple
Sources: 人教版一年级起点|北京版
SourceBooks: 人教版一年级起点::1年级上|北京版::2年级上
```

新增教材时，如果是已有词，只增加来源元数据，不产生第二套 Note。

### 3.3 Learner Presentation Layer

这是可以随着 Klose 成长而升级的层。

推荐字段：

```text
LearnerLevel
ExampleSentence
ExampleTranslation
```

关键原则：

> `FirstGrade` 描述教材事实；`LearnerLevel` 决定今天怎么教。

例如 `apple` 可能是一年级首次出现的词，但 Klose 四年级复习时，不需要继续使用一年级句型。

```text
FirstGrade: 1
LearnerLevel: 4
ExampleSentence: I usually eat an apple after lunch.
```

到了五年级，可以更新为更符合 Grade 5 的例句，但 `NoteID` 和 Anki Review History 保持不变。

---

## 4. Stable NoteID 是整个系统的关键不变量

长期更新不能依赖 `Word` 作为唯一身份。

推荐：

```text
KV000001
KV000002
KV000003
...
```

或者使用其他稳定、不可变的机器 ID。

任何后续动作都必须遵守：

```text
同一 lexical item
    ↓
同一 NoteID
    ↓
Anki Update Existing Note
    ↓
保留原 Card / FSRS History
```

新增北京版、沪教版、新概念时：

- 已存在的词 → 更新原 Note 的 `Sources/SourceBooks/...`
- 真正的新词 → 分配新的 `NoteID`

五年级升级例句时：

- `NoteID` 不变
- `LearnerLevel` 更新
- `ExampleSentence` / `ExampleTranslation` 更新
- 不重新创建 Note

---

## 5. “同一个词”如何判定

不能简单认为“字符串一样 = 永远是同一个 Note”。

默认规则：

1. 统一 Unicode、前后空格、连续空格、大小写等格式后比较 `CanonicalWord`。
2. 固定短语视为独立 lexical item，例如 `look at`、`go fishing`、`ice cream`，不能拆词后去重。
3. 如果同形词在词性、核心义项或学习目标上明显不同，可以保留多个 lexical item，但必须有不同 `NoteID`。
4. 多教材合并时，优先合并“相同词形 + 相同核心义项”的记录；存在歧义时进入 review queue，不允许静默自动合并。

因此，`CanonicalWord` 是重要索引，但**不是唯一业务主键**；真正的长期主键是 `NoteID`。

---

## 6. Anki 组织方式

### 6.1 推荐一个主 Deck

长期推荐：

```text
Klose-English
└── Vocabulary
```

教材、年级、阶段主要通过 Tags 表达，而不是继续拆成大量 Deck。

推荐 Tag 维度：

```text
source::rj_start1
source::beijing
source::shanghai
source::newconcept

grade::1
grade::2
...
grade::6

semester::上
semester::下

stage::review
stage::current
stage::preview
```

这样同一个词只维护一份 FSRS 状态，但可以属于多个来源。

### 6.2 当前学习范围与库存范围分离

可以把全部词汇导入 Anki，但不代表全部立即投入学习。

例如 Klose 当前四年级：

```text
库存：人教版 1-6 年级 + 其他来源
开放学习：人教版 1-4 年级
暂不开放：人教版 5-6 年级、北京版、新概念等
```

长期学习边界推荐通过 **Suspend / Unsuspend + Tags** 控制。

临时专项复习，例如只复习四年级或某个教材，可以使用 **Filtered Deck / Browser Search**。

---

## 7. 发布文件策略

### 推荐主发布文件

```text
anki/publish/all.csv
```

这是默认导入 Anki 的文件，包含所有已经进入 Master 的 Note。

推荐同时生成便利视图：

```text
anki/publish/grade1.csv
anki/publish/grade2.csv
...
anki/publish/grade6.csv
```

它们用于检查、局部分析、特殊导入，不应该形成另一套独立数据真源。

### 推荐字段顺序

```text
NoteID
CanonicalWord
Word
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
Sources
SourceBooks
Tags
```

第一字段固定为 `NoteID`，便于 Anki 重新导入时可靠更新已有 Note。

---

## 8. Anki 更新模型

假设今天已经导入人教版：

```text
KV000001 | apple | ... | source::rj_start1
```

一周后加入北京版，Master 更新为：

```text
KV000001 | apple | ... | source::rj_start1 source::beijing
KV000803 | suburb | ... | source::beijing
```

重新生成并导入完整 `all.csv`：

- `KV000001` 已存在 → Update Existing Note，原 FSRS/Review History 保留。
- `KV000803` 不存在 → 创建新 Note，从 New 状态开始。

因此，日常更新必须走：

```text
Source Data
    ↓
Normalize / Merge / Curate
    ↓
Vocabulary Master
    ↓
Learner Layer
    ↓
all.csv
    ↓
Anki: Update Existing + Add New
```

不建议把“北京版.csv”“新概念.csv”分别作为长期独立导入入口，否则容易形成重复 Note 和多份记忆状态。

---

## 9. 两级扩展模型

### Level 1：Vocabulary Expansion

不断增加词：

```text
人教版
  ↓
+ 北京版
  ↓
+ 沪教版
  ↓
+ 新概念
  ↓
+ 分级阅读
```

已有词只增加 Source 元数据；新词获得新 NoteID。

### Level 2：Learner Level Evolution

随着 Klose 年级提高：

```text
Grade 4 Learner Layer
    ↓
Grade 5 Learner Layer
    ↓
Grade 6 Learner Layer
```

升级的是例句、语言复杂度和必要时的学习提示，而不是词汇身份和 Anki 记忆历史。

这是未来几年最重要的演进机制。

---

## 10. 例句生成与升级原则

例句不是教材事实字段，而是 Learner Presentation。

要求：

1. 难度接近当前 `LearnerLevel`，而不是目标词的 `FirstGrade`。
2. 例句必须明显低于学习者阅读理解上限，避免卡片变成阅读理解题。
3. 目标词必须在句中承担清晰、自然的目标义项。
4. 优先使用已经掌握或当前阶段常见的词和语法。
5. 通常保持短句；需要更丰富上下文时再适度增长。
6. 不为“提高难度”而堆砌陌生词或复杂从句。
7. 例句不是原教材句时必须明确视为生成/审校内容，不声称是教材原句。

---

## 11. Source 数据与 Curated 数据的边界

必须保留原始输入，不能为了方便直接覆盖原 XLSX 或未来其他来源文件。

建议：

```text
sources/          # 原始/标准化后的来源数据
master/           # 跨来源合并后的词汇事实层
learner/          # Klose 当前 Learner Level 的呈现层
publish/          # Anki 可导入结果
review/           # 需要人工/模型复核的问题队列
```

当前仓库历史目录不必一次性重构，但新增机制应逐步向这一结构迁移。

生成文件必须可以从源数据 + curation + learner rules 重建，不能手工修改生成结果作为长期维护方式。

---

## 12. 必须自动检查的质量门槛

随着词库变大，人工逐文件检查不可持续，CI 必须逐步承担以下检查：

### Identity

- `NoteID` 唯一
- `NoteID` 不被重新分配
- 同一 canonical item 的潜在重复检测
- 不同义项的误合并检测队列

### Source / Provenance

- 每条记录至少有一个 Source
- SourceBook / FirstSource / FirstGrade 可追溯
- 原始 Source 数据不可被构建脚本覆盖

### Learner Layer

- `LearnerLevel` 存在
- `MeaningPrimary` 非空
- `ExampleSentence` / Translation 非空
- 例句包含目标词或其合理词形时优先通过；特殊短语允许例外
- 明确晚于当前学习范围的新教材词不应无意提前大量引入

### Publish

- `all.csv` 中 NoteID 唯一
- 便利 CSV 是 Master 的子集或视图
- 重复构建结果 deterministic
- 生成文件不得出现静默 fallback 到未经审校的成人词典首义

---

## 13. 变更分类

后续修改必须先判断属于哪一类：

### A. Source Expansion

例如：加入北京版、新概念。

动作：解析 → 标准化 → canonical merge → 分配新 NoteID（仅真正新词）→ 更新来源 → 重新发布。

### B. Fact Correction

例如：音标、拼写、核心释义确有错误。

动作：修改 Master/Curation 的事实字段；如果涉及 identity 变化，必须评估是否会破坏 NoteID 映射。

### C. Learner Upgrade

例如 Klose 从四年级升五年级。

动作：更新 Learner Layer；原则上不修改 NoteID / Canonical identity / 来源事实。

### D. Anki Presentation

例如 Card Template、CSS、显示字段顺序变化。

动作：只修改呈现，不应改变 Vocabulary Identity。

---

## 14. 不变量（必须长期保持）

以下规则优先级高于任何局部便利：

1. **Stable NoteID cannot be casually changed.**
2. **同一个已学 lexical item 不创建第二套 FSRS 记忆状态。**
3. **新增教材优先扩展 Source，不复制已有词。**
4. **Learner Level 与 FirstGrade 解耦。**
5. **更新例句不能通过重建 Note 来实现。**
6. **原始 Source 保留、可追溯。**
7. **Master/Curation 是内容层真源；publish 文件是生成物。**
8. **Anki 是学习历史真源；repo 不重建 FSRS history。**
9. **任何自动合并存在歧义时进入 review，不静默猜测。**
10. **长期优化优先保证旧数据和旧记忆历史的向后兼容。**

---

## 15. 当前实现与下一阶段

当前已经完成“人教版一年级起点”1–6 年级词表的第一轮清洗、去重、释义审校和例句建设，并建立了自动构建与质量检查。

下一阶段迁移目标：

1. 为现有 802 个唯一 Note 分配稳定 `NoteID`。
2. 从“按首次出现册输出 12 个 CSV”迁移到“一个 `all.csv` + 年级便利视图”。
3. 将 `FirstGrade` 与 `LearnerLevel` 正式分离。
4. 将当前例句升级为 `LearnerLevel=4` 的 Klose 学习层。
5. Anki 统一使用一个主 Deck，来源/年级通过 Tags 与 Suspend/Filtered Deck 控制。
6. 后续新增教材全部接入统一 Master，而不是建立独立长期牌组。

这套机制应持续多年演进；每次修改架构时优先评估：**是否破坏 Stable NoteID、Source Provenance 或已有 Anki FSRS History。**
