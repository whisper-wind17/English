# 新概念一首批导入：Lesson 1–17

本批仅包含有实物照片证据的前17课150条来源记录。后续756条仍待逐项核对，不能将本包称为全册合入。

## 发布范围

109条复用已有稳定身份，41条新增；复用项中108条已经发布、Danish（KV000746）是既有库存首次发布。Vocabulary总发布从2,953增至2,995，allowed从2,889增至2,937，held为58。Expressions维持176条，本批无需重复导入其未变化文件。

当前允许的新卡课程顺序：四上 → 四下 → 已审核的新概念首批 → 五上 → 五下 → 六上 → 六下 → 第三方。四年级前221条顺序不变；本批14个学习目标已在四年级段，其余136个排入新概念段。后续全册尚未完成，此顺序不代表已经收齐所有新概念卡。

## 导入

先备份 Collection。以 `anki/klose/releases/current.json` 的 release_id 和 SHA-256 核对正式 `anki/klose/publish/anki-import.csv`。

使用已有 **Klose Vocabulary** Note Type，第一字段 **NoteID** 匹配，Existing Notes = Update，Match scope = Note Type。遵循文件的 #columns 映射；Tags映射Anki标签；UserMemo不映射。不要新建第二套类型、删除旧卡或重新编号。

若设备此前完整导入2,953条发布内容且没有另外新增同ID笔记，本次预计新增42条，其余按同ID原地更新。实际报告以设备已有ID集合为准，不能为了凑数删除笔记。

以下六个原held目标在本批来源中明确准入：KV000035 how、KV000044 colour、KV000116 name、KV000117 her、KV000122 thin、KV000148 too。仅当它们仍是New卡且因旧准入暂停时，解除对应暂停。已进入Learning/Review的卡保留现有状态；其他58条held新卡继续暂停。累计旧标签可能残留，以本次 `learner/learning_admission.csv` 和非空 LearningOrder 为准。

只对本次allowed、仍为New、未暂停的卡，按LearningOrder升序Reposition：Start=1、Step=1、Randomize=OFF、Shift existing=ON。学习中/复习中的卡不选入，不改Due、Interval或FSRS状态。

## 验收

抽查 excuse（原谅/借口）、watch（手表/看）、clean（干净的/打扫）、smart（时髦/聪明）、well（健康/很好地）题面提示；Mr.复用原Mr笔记；too例句已改为“I like apples, too.”。

核对几张旧卡的Card ID、Review History、Due/Interval和UserMemo保持不变，再同步AnkiWeb及iPad。仓库只生成发布内容；未取得用户实际导入确认前，不记录设备已更新。
