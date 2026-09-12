# 当前发布导入 Anki

使用 [current.json](../anki/klose/releases/current.json) 中同一 release_id 对应的正式包，先确认完整 Release Ready 通过。数量、allowed/held、最大 LearningOrder、PromptHint 数量和 SHA-256 均读取清单；本文不维护第二份当前计数。

| 对象 | 正式文件 | Note Type | 匹配字段 | Deck |
| --- | --- | --- | --- | --- |
| Vocabulary | anki/klose/publish/anki-import.csv | Klose Vocabulary | NoteID（第一字段） | Klose-English::Vocabulary |
| Expressions | anki/klose/expressions/publish/anki-import.csv | Klose Expression | ExpressionID（第一字段） | Klose-English::Expressions |

## 导入前

1. 备份 Collection，记录几张已有卡的 ID、Review History、Due/Interval 与 UserMemo。
2. 核对本地正式 CSV 的 SHA-256 与清单；当前待审为零。`study.csv` 只用于审计，不导入。
3. 使用已有 Note Type，Existing Notes = Update，Match scope = Note Type；不要创建第二套类型或删除重建 Cards。
4. 按 CSV `#columns` 映射字段。Vocabulary 最后一列 Tags → Anki Tags；UserMemo → Nothing / 不映射。Expressions 按其 12 列契约映射，UserMemo 同样不覆盖。

Vocabulary 类型字段依次为 NoteID、CanonicalWord、Word、PromptHint、British、American、MeaningPrimary、ExampleSentence、ExampleTranslation、LearnerLevel、LearningOrder、Sources、SourceBooks、UserMemo。Expressions 类型契约见 [Expressions Anki README](../anki/klose/expressions/anki/README.md)。只有设备确实缺少字段时才按对应 migration 原地补字段；历史 migration 数量不能用作当前验收。

## 导入和新卡准入

每类卡分别导入，按清单的 ID 集合和最终行数核对。新增数取决于设备已有 ID；相同总数也可能包含内容更新，不能据此跳过本次 Expressions 更新。

只对仍为 `is:new` 的卡物化准入：allowed 可以进入新增队列；held 保持 suspended。以当前 learning_admission.csv 的 ID 集合为准，不能把累计的旧 Tags 当作唯一依据，因为导入未必删除旧标签。

本轮五条重复学习目标的 hold 记录见 Vocabulary `learner/admission_decisions.csv`。这些 NoteID 保留在发布包中供原地更新；若仍未学习，应暂停新增。若已经进入 Learning / Review，不因 repo hold 批量改 suspension、Due 或历史。

仅对 allowed、is:new、未 suspended 的卡按 LearningOrder 升序 Reposition：Start=1、Step=1、Randomize=OFF、Shift existing=ON。已有学习卡不参与，不为凑满清单中的 allowed 数量重排旧卡。

## 验收和同步

核对最终稳定 ID、Notes/Cards 数量、每 Note 一张卡、当前模板和字段。抽查同词不同义提示（如 cook、over、may/May）、sure 的回应请求例句、一般大小的 size；Expressions 抽查 KE000137 的建议提示和 KE000147 的地点句型。

再核对几张旧卡的 Review History、Due/Interval、Card identity 与 UserMemo 保留；出现重置则停止后续操作，排查匹配与类型，必要时从备份恢复。

Desktop 验收后 Sync 到 AnkiWeb，再由 iPad Sync 并抽查。只有用户实际确认后，才在 [device_receipts.json](../anki/klose/releases/device_receipts.json) 中记录确切 release_id、日期和凭据。之前的用户确认保留为历史；本轮不会自动宣称设备已更新。

长期边界见 [Anki 同步契约](ANKI_SYNC_WORKFLOW.md)，实际学习观察见 [学习反馈](LEARNING_FEEDBACK.md)。
