# 新概念英语一全册更新：Anki导入

本包的 `Klose_Vocabulary_NCE1_Full_anki-import.csv` 是现有Klose Vocabulary的完整更新文件，含3,226条笔记，**不是另建一个新牌组或另建同名词笔记**。全册词表CSV仅供查看，不用于导入。

## 导入

先同步当前设备并导出Collection备份（含学习调度）。在Anki Desktop导入正式CSV，选择已有 `Klose Vocabulary` 类型和 `Klose-English::Vocabulary` 牌组；以第一字段 `NoteID` 匹配并更新已有笔记，不选择把匹配项也作为新笔记加入。沿用文件中的字段顺序和标签列，UserMemo不要映射，不改笔记类型或卡片模板。

完整字段：NoteID、CanonicalWord、Word、PromptHint、British、American、MeaningPrimary、ExampleSentence、ExampleTranslation、LearnerLevel、LearningOrder、Sources、SourceBooks、Tags。

设备如果还是2,953条的旧发布，本次相对旧版本增加273条发布笔记；如果已导入前17课、当前为2,995条，则增加231条。实际新增/更新数依设备已有NoteID为准。出现大量原有词被重复新增时先停止并检查匹配字段，不连续导入第二遍尝试修复。

## 准入与新卡顺序

只对 `Klose Vocabulary` 中当前allowed、未暂停、仍为New的卡重排。可沿用项目SOP的学习标签范围筛选；核对LearningOrder非空后按六位LearningOrder升序排序，再Reposition：Start=1、Step=1、Randomize关闭、Shift existing开启。不要对Learning或Review卡操作，不使用Forget，不改FSRS参数。

目标课程顺序：四年级上 → 四年级下 → 新概念一 → 五年级上 → 五年级下 → 六年级上 → 六年级下 → 第三方。已在四年级出现的相同目标不在新概念段重复。

仍为held的笔记LearningOrder为空，不应批量启用。尤其既有重复目标KV001461、KV001481、KV001808、KV002569、KV002636继续保留原暂停策略。用户自己暂停的卡也不要批量解除。9个由library-held变为allowed的目标及具体ID见更新包的准入变更表；仅在确认它们此前因旧课程范围而暂停、且仍为New时，按新准入选择是否恢复。

## 核对

检查同一词不同目标的提示，例如bank河岸/银行、full满的/饱的；检查ice cream仍使用原ice-cream身份。抽查一张旧Review卡的复习历史仍在。确认没有把全册词表误当导入文件、没有生成第二套重复笔记后，再同步AnkiWeb及其他设备。

3,177是当前允许学习的目标数，**不是设备当前New卡数量**；已有Learning/Review卡仍按原调度出现。Expressions176条和卡片模板未改，本次不需重新导入Expressions。本包未自动操作任何Anki设备。

## 2026-11-02 Desktop 导入验收记录

用户在 Windows Anki Desktop 完成正式 Vocabulary CSV 导入，报告：3,226 in file = 273 newly imported + 2,800 updated + 153 unchanged；已按 `NoteID` 原地更新 `Klose Vocabulary`，`UserMemo` 没有映射。用户先完成 Collection 备份，随后确认了旧 Review 卡复习历史、New 卡 Reviews=0、held 空 LearningOrder 共 49、可用 New 卡 2965 张按 `LearningOrder` 升序重新定位，并确认 Desktop → AnkiWeb Sync 成功。

这属于**用户确认的 Desktop 端导入与同步证据**，不是设备上所有卡片的逐项检查，也没有独立取得本地导入 CSV 的 SHA-256。iPad 尚未报告同步/抽查，因此全端完成状态不能标记为 confirmed。正式设备凭据记录在 `../anki/klose/releases/device_receipts.json`；下一次 iPad 实际验收后再更新对应项。当前内容、审核、发布及 FSRS/Review History 的真源边界不变。
