# Klose Actual Textbook Source References

本目录保存 Klose 手中实际教材的人工核对资料。这里是 **source reference / reconciliation input**，不是 generated publish output。

通用规则：

```text
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
```

动态任务入口：`/NEXT.md`。

## 当前 Grade 4 真实 Vocabulary 基准

Klose 实际四年级上、下册词表已经完整采集并合并。

### 四上

```text
rj_start1-grade4-upper-klose-actual.csv
6 Units
110 occurrence rows
109 unique surface entries
```

### 四下

```text
rj_start1-grade4-lower-klose-actual.csv
6 Units
111 occurrence rows
111 unique surface entries
```

### 四上 + 四下合并表

```text
rj_start1-grade4-klose-actual.csv
```

字段：

```text
SourceID
SourceEdition
Grade
Semester
Unit
Order
Starred
Entry
Meaning
Page
SourceStatus
```

当前固定来源身份：

```text
SourceID      = rj_start1
SourceEdition = klose-current
Grade         = 4
```

全学年统计：

```text
221 occurrence rows
219 unique surface strings
```

只有两个 surface string 重复，且都属于不同 target sense：

```text
cook
  四上 Unit 1 = 烹饪；煮
  四上 Unit 4 = 厨师

over
  四上 Unit 3 = 在……的远端（或对面）
  四下 Unit 3 = 结束（的）
```

因此后续 identity merge 不能按 Word 直接去重；这两项至少需要两个独立 NoteID / target sense。

## Useful Expressions

四上已保存：

```text
rj_start1-grade4-upper-klose-expressions.csv
rj_start1-grade4-upper-pattern-candidates.csv
```

Useful Expressions 是 Source Fact，不机械执行“一句 = 一张卡”。四下 Expressions 尚未进入当前工作范围。

## 使用规则

1. `rj_start1-grade4-klose-actual.csv` 是当前 Klose Grade 4 学习范围的权威教材输入；第三方 XLSX 不再用于决定 Klose 当前四年级学什么。
2. 该文件不直接赋予 NoteID；下一步与现有 Vocabulary Identity / study 做 sense-aware merge。
3. exact word + same sense 可复用已有 NoteID；真正新 learning unit append NoteID；同词异义必须拆分。
4. 不删除或重编号已有 NoteID，不手工修改 `publish/study.csv` / `publish/anki-import.csv`。
5. Source Grade、LearnerLevel、Learning Admission 独立。Klose 当前 `LearnerLevel=4`。
6. 后续真正决定当前学习范围的是显式 Learning Admission / Anki Tag，而不是 FirstGrade 或第三方教材年级。
7. Anki 中已有学习历史必须保留；当前 Klose 尚未产生真实 Review History，因此这是调整 learning set 的低风险窗口。
