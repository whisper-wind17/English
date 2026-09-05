# Source Reconciliation SOP

本文定义当 **Klose 实际教材** 与 repo 中现有第三方 Source Adapter 数据不一致时的处理流程。目标是修正 Source Fact，同时保护 Stable NoteID、Learner Presentation 和 Anki Review History。

## 1. 触发条件

出现以下任一情况，必须进入 reconciliation，不能直接改 publish 文件：

- 实际教材词表与现有 SourceBook 大量不一致；
- 同一 surface word 在教材中出现不同词性/target sense；
- 实际教材出现当前 Master 没有的词或短语；
- 当前 Master 有相近词，但粒度不同，例如 `worker` vs `office worker`；
- Useful Expressions 暴露出新的 Context Vocabulary 或 Source Edition 差异。

## 2. 证据优先级

对 Klose 当前实际使用教材，优先级为：

```text
Klose 手中实际教材照片/扫描件
> 可确认同 Edition 的官方材料
> 第三方整理 XLSX
```

第三方 XLSX 不是权威事实。发生冲突时，先识别 Edition / Revision；不要把两个版本静默合并成一个来源事实集合。

## 3. 先冻结学习影响

若错误 staging 尚未产生真实 Review History：

- 暂停正式学习；
- 不继续扩大 release scope；
- 不删除/重编号已有 NoteID；
- 不手改 `publish/study.csv` / `publish/anki-import.csv`。

若已经产生 Review History，则进一步要求：不得通过删除 Note/Card 清理错误来源；必须设计保留 scheduling state 的 migration。

## 4. Capture：先保存实际教材事实

实际教材先进入：

```text
anki/klose/source_reference/
```

Core Vocabulary 至少保存：

```text
Unit
Order
Entry
Meaning
Page
SourceStatus
```

Useful Expressions 保存原句和教材译文。Source Reference 是 reconciliation input，不直接进入 publish。

## 5. 三方核对

逐条比较：

```text
实际教材 Source Reference
vs 当前 source_occurrences / Source Adapter
vs 当前 Vocabulary Master / Identity
```

每个实际教材 item 必须得到明确决策，不能只做字符串存在性检查。

## 6. 决策分类

### A. 同一 learning unit / 同一 target sense 已存在

复用现有 NoteID，只补充正确的 actual-textbook provenance。

### B. Note 已存在，但当前只记录在其他年级/书册

仍复用 NoteID；新增当前教材 occurrence。Source Grade 是 occurrence 事实，不影响 LearnerLevel。

### C. surface 相近、词形变化或短语包含

进入 sense-aware review，例如：

```text
worker vs office worker
football vs play football
fly vs fly a kite
sock vs socks
child vs children
```

包含关系或词形相似只产生 candidate，不能自动 merge。

### D. 相同 surface，不同 target sense

必须 split identity。例如：

```text
cook = 厨师      # noun
cook = 烹饪；煮  # verb
```

已发布 NoteID 保留其已有明确 sense；新增 sense append 新 NoteID。不得重编号旧 Note。

### E. 真正新的 learning unit

追加新 NoteID，并建立 Source Identity Map、Fact、Learner Presentation 和 review 状态。

### F. 当前第三方 source 中有、实际教材没有

不要直接删除。先判断是否属于另一个 Edition / Revision；如果是，保留为另一个 source-edition provenance。只有证据充分时才做 source correction。

## 7. Source Edition / Revision

逻辑模型必须能够表达：

```text
SourceID
SourceEdition / Revision
SourceBook
Grade
Semester
Unit
```

当前物理 schema 若还没有 `SourceEdition` 字段，发生版本冲突时必须先完成建模设计，再把两个版本混入同一个 `SourceBook`。不要用文件名相同来假定版本相同。

## 8. Learner Presentation

Reconciliation 修的是 Source Fact / Identity，不自动升级 LearnerLevel。

Klose 可以：

```text
LearnerLevel = 4
学习 Grade 4 / 5 / 6 来源词汇
```

新增或修改的 `MeaningPrimary / ExampleSentence / ExampleTranslation` 必须按当前 LearnerLevel 重新审校；ContentFingerprint 变化后旧 approval 失效。

## 9. Useful Expressions

Useful Expressions 原文属于 Source Fact，但不等于 Vocabulary Note。处理规则见：

```text
docs/EXPRESSIONS_SYSTEM.md
```

Expression 中出现但未列入 Core Vocabulary 的词，可作为 Context Vocabulary 证据，用于例句难度与教材暴露范围判断，但不能自动升级为 Core Vocabulary。

## 10. Rebuild 与发布

完成全部 identity/source 决策后：

```text
更新上游 Source / Identity / Fact / Learner / Release
→ rebuild
→ sync learner review registry
→ 完成真实审校 / approval
→ release readiness gate
→ 生成 study.csv
→ 生成 anki-import.csv
→ 重新导入同一 Anki Note Type
```

必须验证：

- Stable NoteID 未漂移；
- Source provenance 可追溯；
- identity review / learner review / future vocab review 无未决 blocker；
- ContentFingerprint current；
- staging 基于纠正后的 source truth；
- `anki-import.csv` 与 Released Set 一致；
- 已有 Anki Review History 不被破坏。

## 11. 当前四上专项

当前实际工作入口：

```text
anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md
```

动态 blocker 和下一步始终以根目录 `NEXT.md` 为准。
