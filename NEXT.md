# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ anki/klose/source_reference/README.md
→ anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
```

## Current objective

采用简化路径：**以 Klose 实际四年级上 + 下教材作为 Grade 4 权威学习范围，合并进入长期 Vocabulary study，再通过显式 Learning Admission / Tag 让 Klose 只学习真实 Grade 4 词汇。**

不再把第三方 XLSX 中的“4年级”范围作为 Klose 当前学习范围依据。

核心不变量：

```text
Source Grade ≠ LearnerLevel ≠ Learning Admission
```

Klose 当前仍使用 `LearnerLevel=4`。

## Actual Grade 4 source completed

四上：

```text
anki/klose/source_reference/rj_start1-grade4-upper-klose-actual.csv
110 occurrence rows
109 unique surface strings
```

四下：

```text
anki/klose/source_reference/rj_start1-grade4-lower-klose-actual.csv
111 occurrence rows
111 unique surface strings
```

四上 + 四下权威合并表：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
Grade         = 4
221 occurrence rows
219 unique surface strings
```

重复 surface 只有两个，且义项不同：

```text
cook
  上 U1 = 烹饪；煮
  上 U4 = 厨师

over
  上 U3 = 在……的远端（或对面）
  下 U3 = 结束（的）
```

因此这两项必须按不同 target sense 处理，不能按 Word 去重。

## Simplified target workflow

```text
Actual Grade 4 merged source
→ sense-aware match against current Vocabulary Identity / study
→ exact same-sense: reuse NoteID
→ genuine new learning unit: append NoteID
→ same word / different sense: separate NoteID
→ merge all resulting Notes into long-lived study
→ explicit Learning Admission / Tag = current Grade 4
→ Anki: suspend old baseline, unsuspend current Grade 4 learning set
```

`study.csv` 的角色固定为长期已纳入 Klose 系统的 released vocabulary，不再等同于“当前正在学习的词”。

当前学习范围由 Learning Admission / Tag 决定。

计划 Tag：

```text
learning::klose::grade4
```

## Current Anki state

历史结果：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Cards             = 518
Suspended         = 343
Unsuspended       = 175
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

Klose 尚未产生真实 Review History。

当前操作原则：

```text
保留全部已有 NoteID / Cards
不删除历史 study Notes
下一次正式同步后：现有 baseline 全部 Suspend
只 Unsuspend tag:learning::klose::grade4
```

注意：CSV 导入只负责 Note 内容更新；Suspend / Unsuspend 在 Anki 中按 Tag 执行。

## Next work order

1. 用 `rj_start1-grade4-klose-actual.csv` 的 221 条 occurrence 与当前 Vocabulary Master / study 做匹配。
2. 优先自动处理 `exact word + same target sense`，复用已有 NoteID。
3. 只把以下情况进入小型 review queue：
   - same word / different sense；
   - phrase vs single word；
   - morphology / plural；
   - Meaning 与当前 Note 核心义项明显不一致。
4. `cook` 和 `over` 明确拆成独立 target sense；保留已有合适 NoteID，新增必要 NoteID。
5. genuine new learning unit append NoteID。
6. 将全部真实 Grade 4 learning units 纳入 long-lived study，并打 `learning::klose::grade4`。
7. 建立对应 `learning_admission.csv`；不再依赖 legacy Grade-4 staging fallback。
8. 保持 `LearnerLevel=4`，生成/修正 learner presentation。
9. fingerprint v2 review / approval，直到 pending=0。
10. release gate 通过后生成新的 `anki-import.csv`。
11. Anki 原地导入；全部旧 baseline Suspend，再 Unsuspend `tag:learning::klose::grade4`。

## Source reconciliation state

结构化状态仍保持 blocked，直到 identity merge 和 learning admission 完成：

```text
anki/klose/master/source_reconciliation_registry.csv
```

四上、四下都已完成教材 evidence capture；当前 blocker 已从“缺教材”转为“尚未完成 identity merge / learning admission”。

## Deferred

Homograph front-side disambiguation（例如 `cook n.` / `cook v.`）仍需单独 Note Type migration，引入 `PromptHint` 字段；不要为了本轮 Grade 4 merge 临时破坏现有 Anki Note Type。

四下 Useful Expressions 暂不处理，当前先完成 Vocabulary learning set。
