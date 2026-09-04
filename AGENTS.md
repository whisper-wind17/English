# AGENTS.md

## 1. Project Mission

本仓库当前除保存原始英语词库外，还承担一个长期任务：构建并维护可持续多年演进的 **Klose Vocabulary System**。

目标不是生成一次性 Anki 牌组，而是维护：

- 可持续增加教材/阅读来源的统一词汇知识库；
- 稳定的 Vocabulary Identity；
- 可随 Learner Level 升级的释义/例句呈现；
- 与 Anki FSRS 长期记忆历史兼容的发布数据。

完整架构见：`docs/KLOSE_VOCABULARY_SYSTEM.md`。

---

## 2. Non-negotiable Rules

1. **Stable NoteID 优先级最高。** 已发布并进入 Anki 的 NoteID 不得随意修改、复用或重新分配。
2. **不要为同一个已学 lexical item 创建第二套记忆状态。** 新教材出现已有词时，扩展 Source/Provenance，而不是复制 Note。
3. **FirstGrade 与 LearnerLevel 必须分离。** 前者是教材事实，后者决定当前学习呈现。
4. **Learner Layer 可以升级，Vocabulary Identity 不应因此变化。** 升年级更新例句时不得重建 Note。
5. **原始 Source 保留且可追溯。** 不覆盖原始 XLSX/来源文件来“修复”生成结果。
6. **生成文件不是长期手工维护入口。** 修改 source / curation / learner rules 后重新构建。
7. **存在 identity/义项歧义时进入 review queue，不允许静默自动猜测。**
8. **不得把结构检查通过表述成“逐词人工老师审核”。** 明确区分：规则检查、模型审校、人工确认、教材原文核对。
9. **任何架构优化都必须优先保护已有 Anki FSRS/Review History。**
10. **不要无质疑接受需求假设。** 发现数据、学习机制或 Anki 行为上的错误前提时，应先指出并验证。

---

## 3. Source of Truth

### 内容事实

优先级：

```text
原始 Source
    ↓
标准化 / Curation
    ↓
Vocabulary Master
    ↓
Learner Layer
    ↓
Publish CSV
```

- 原始 Source：教材/词书原始数据，负责 provenance。
- Master/Curation：repo 中的内容真源。
- Learner Layer：当前 LearnerLevel 对应的呈现内容。
- Publish：Anki 导入产物，可重建。

### 学习状态

Anki 是以下状态的唯一真源：

- Review History
- FSRS memory state
- Due / Interval
- New / Learning / Review / Suspended

repo 不尝试重建这些状态。

---

## 4. Current Data Area

当前已实现的人教版一年级起点数据位于：

```text
anki/人教版一年级起点/
```

现有关键文件/目录：

```text
curation/                       # 已审校释义与例句
master/                         # 当前去重 Master 与质量报告
import/                         # 当前 Anki 导入 CSV
review_input/                   # 紧凑复核视图
README.md                       # 当前数据集说明
```

原始教材词表位于：

```text
1.全国各大教材版本中小学同步/人教版/
```

---

## 5. Current Build Entry Points

当前主要脚本：

```text
tools/build_anki_rj_start1.py
tools/check_anki_example_vocab.py
tools/export_anki_review_input.py
```

CI：

```text
.github/workflows/build-anki-rj-start1.yml
```

修改相关数据/规则后，应保证构建与 CI 成功后再认为任务完成。

---

## 6. Target Architecture

后续逐步迁移到：

```text
sources/       # 多教材来源及标准化数据
master/        # 跨来源统一 Vocabulary Master
learner/       # Klose 当前 LearnerLevel 呈现层
publish/       # all.csv + 年级便利视图
review/        # 歧义、冲突、待核对项
```

不要求一次性重构整个上游词库仓库；按实际接入教材逐步迁移。

长期推荐 Anki 结构：

```text
一个主 Deck
+ Stable NoteID
+ Tags 表达来源/年级
+ Suspend/Unsuspend 控制当前学习范围
+ Filtered Deck 做临时专项复习
```

不要因为新增一个教材就创建新的长期独立牌组体系。

---

## 7. Schema Direction

Master/Publish 至少应逐步包含：

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
FirstSource
FirstGrade
Sources
SourceBooks
Tags
```

规则：

- `NoteID` = 永久业务主键。
- `CanonicalWord` = 跨来源匹配索引，不等于业务主键。
- 同形异义/不同 lexical item 可拥有不同 NoteID。
- 固定短语是独立 lexical item，不拆分后去重。

---

## 8. Change Workflow

### 新增教材/词书

1. 保留原始 Source。
2. 解析并标准化。
3. 与 Master 做 canonical matching。
4. 已有 lexical item：合并来源。
5. 真正新词：分配新 NoteID。
6. 歧义项进入 review。
7. 更新 Learner Layer。
8. 重建 publish CSV。
9. 运行质量检查/CI。

### 升级 Learner Level

1. 保留 NoteID/Canonical identity/Source facts。
2. 更新 `LearnerLevel`。
3. 批量升级例句/翻译等 Learner Presentation。
4. 质量检查。
5. 重新导出，以 Update Existing Note 的方式更新 Anki。

### 修正已有词

先判断是：

- source transcription error；
- fact/meaning correction；
- identity merge/split；
- learner presentation change。

涉及 NoteID merge/split 时不得直接批量修改，必须评估对现有 Anki history 的影响。

---

## 9. Quality Gates

至少检查：

- NoteID 唯一且稳定；
- canonical duplicate / identity conflict；
- Source 可追溯；
- `MeaningPrimary` 非空且适合目标学习阶段；
- `ExampleSentence` / `ExampleTranslation` 非空；
- 例句难度与 `LearnerLevel` 匹配，而不是机械跟随 `FirstGrade`；
- 生成文件 deterministic；
- 不允许静默 fallback 到未经审校的通用词典首义；
- publish 中不得出现重复 NoteID。

当前自动检查不能覆盖的语义问题，应明确写入 review，而不是用 `0 issues` 代表“全部语义正确”。

---

## 10. Working Style

- 优先检查现有 repo 状态，再修改；不要凭历史对话假设文件仍然一致。
- 先判断问题属于 Source / Identity / Learner / Publish / Anki 哪一层。
- 大批量生成前先用少量样本验证规则。
- 修改后必须 re-check 代表性边界案例和全量统计。
- 能通过脚本/CI 固化的规则，不只写在 Prompt 或文档里。
- AGENTS.md 只维护项目规则和能力地图；详细机制放 `docs/`。
