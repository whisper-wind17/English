# Klose Actual Textbook Source References

本目录保存 Klose 手中实际教材的人工核对资料。这里是 **source reference / reconciliation input**，不是 generated publish output。

通用规则：

```text
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
```

动态任务入口：`/NEXT.md`。

## Grade 5–6 actual textbook provenance

Grade 5–6 已完成 book-level provenance resolution。当前 canonical 教材家族：

```text
SourceID = renjiao_start3
```

`SourceEdition` 表示教材 **revision lineage**，不是某一次物理印刷年份：

```text
Grade 5 Upper = 2024-revision
Grade 5 Lower = pre-2024-revision   # captured legacy source; allocation held
Grade 6 Upper = 2024-revision
Grade 6 Lower = pre-2024-revision   # captured legacy source; allocation held
```

详细结构化判定与证据：

```text
grade5_6_source_provenance.json
grade5_6_actual_textbook_manifest.csv
```

Grade 5 Lower 已确认与当前 revised PEP 下册不一致；Grade 6 Lower 的 captured material 也属于旧 lineage，Klose 将来实际使用的 revised lower volume 尚未确认。因此这两册继续作为真实已收到 Source Evidence 保存，但不得据此进入 Grade 5–6 Stable NoteID / ExpressionID allocation。

Grade 3–4 既有 actual-textbook 数据历史上使用：

```text
SourceID      = rj_start1
SourceEdition = klose-current
```

该标签已经进入现有 stable source mapping 与构建链，当前视为 **legacy alias / migration-deferred**。Grade 5–6 provenance resolution 不原地重写它；若未来统一 source naming，必须单独设计 source-identity migration，保护 Stable NoteID / ExpressionID 与 Anki Review History。

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

当前历史来源标签：

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

四年级 actual-textbook Useful Expressions 已保存为 Source Fact。Useful Expressions 不机械执行“一句 = 一张卡”；正式 learning object 由独立 Expressions identity / learner / release 链决定。

## 使用规则

1. Klose actual-textbook source 是当前学习范围的权威教材输入；第三方 XLSX 不用于覆盖 actual source truth。
2. Source Reference 不直接赋予 NoteID / ExpressionID；identity resolution 必须 sense-aware / function-aware。
3. exact surface 只能产生 candidate；真正同一 learning unit 才复用已有 stable ID，同词异义必须拆分。
4. 不删除或重编号已有 Stable ID，不手工修改 generated `publish/study.csv` / `publish/anki-import.csv`。
5. Source Grade、LearnerLevel、Learning Admission 独立。
6. 学习范围由显式 Learning Admission / LearningOrder 决定，不由 FirstGrade 或第三方教材年级替代。
7. Anki FSRS / Review History 必须保留；source provenance 修正不能重建 scheduling state。
