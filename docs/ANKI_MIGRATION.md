# Anki 一次性迁移：Word-first → NoteID-first

本文只处理当前旧版人教版 CSV 已经导入 Anki 的兼容问题。

## 为什么必须迁移

旧版 CSV 第一字段是：

```text
Word
```

新版长期系统第一字段改为：

```text
NoteID
```

Anki 文本导入默认使用第一字段 + Note Type 识别重复 Note。若旧 Notes 已经存在，直接导入 NoteID-first CSV，会把 `KV000001` 与原来的 `book/apple/...` 视为不同第一字段，产生重复 Note。

因此必须先给现有 Notes 补上 NoteID，再把 NoteID reposition 为 Note Type 的第一字段。

---

## 场景 A：还没有导入过旧版数据

最简单：

1. 创建/修改 Note Type：`Klose Vocabulary`。
2. 字段顺序直接使用：

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
UserMemo   # 可选，本地字段，不映射 CSV
```

3. 导入：

```text
anki/klose/publish/study.csv
```

4. 将第一列 `NoteID` 映射到 NoteID。
5. Tags 列映射到 Anki Tags。
6. Deck 使用统一 Main Deck，例如：

```text
Klose-English::Vocabulary
```

以后持续重新导入 `study.csv` 即可。

---

## 场景 B：已经导入过旧版 Word-first 数据

### Step 0：先备份

在 Anki 中先导出 Collection/Deck 备份。不要跳过。

### Step 1：保持当前 Word 仍是第一字段

不要先 reposition。

在原来的 `Klose Vocabulary` Note Type 中增加以下字段（不存在才加）：

```text
NoteID
CanonicalWord
LearnerLevel
Sources
SourceBooks
```

建议另外增加：

```text
UserMemo
```

`UserMemo` 以后不映射任何 repo CSV，可用于 Anki 本地个人备注。

### Step 2：导入兼容迁移文件

如果当前 Anki 中只希望保留/迁移人教版 1–4 年级：

```text
anki/klose/publish/migration/word-first-study.csv
```

如果此前已经把 1–6 年级全部导入：

```text
anki/klose/publish/migration/word-first-all.csv
```

迁移 CSV 的第一列仍然是：

```text
Word
```

因此可以匹配旧 Notes。

导入选项：

- Note Type：现有 `Klose Vocabulary`
- Duplicate / Update：Update Existing Notes
- Match scope：Note Type
- 第一列 Word → Word
- NoteID → NoteID
- 其他字段按名称映射
- Tags → Anki Tags

确认导入结果显示的是“updated existing notes”，而不是批量新增重复 Notes。

### Step 3：抽样检查 Review History

至少检查 3–5 张已经复习过的卡：

- Card Info 中 Reviews 未清零；
- Due / Interval 正常；
- Note 中已经出现 `KVxxxxxx` NoteID。

### Step 4：把 NoteID reposition 为第一字段

Anki：

```text
Tools
→ Manage Note Types
→ Klose Vocabulary
→ Fields
→ 选择 NoteID
→ Reposition
→ 1
```

这一步修改的是 Note Type 字段顺序，不会新建 Note。

此时字段顺序应以 NoteID 开头。

### Step 5：以后只使用 NoteID-first 发布文件

完成迁移后，永久改用：

```text
anki/klose/publish/study.csv
```

导入规则：

```text
第一字段 = NoteID
Note Type = Klose Vocabulary
Match scope = Note Type
Update Existing Notes
```

不要再导入旧 `anki/人教版一年级起点/import/*.csv` 作为长期入口。

---

## Tags 的边界

来源/年级 Tags 由 repo 管理，重新导入时允许整体更新。

因此不要在这些 Notes 的 Anki Tags 中混入需要永久保留、但 repo 不知道的个人标签。

个人数据建议放：

- `UserMemo`（不参与 CSV mapping）；或
- Card Flag。

---

## study.csv 与 all.csv

默认只导入：

```text
study.csv
```

它表示已经释放给 Klose 学习并需要持续更新的 Notes。

`all.csv` 是完整库存。除非明确要把全部库存都加入 Anki，否则不要把它作为日常重新导入入口。

当前默认 release scope：

```text
人教版一年级起点 1–4 年级
```

如果此前旧版 Anki 已经实际导入 5–6 年级，应先把 repo 的 release registry 与真实 Anki 库同步，再以 `study.csv` 作为后续入口。

---

## 迁移完成的验收标准

- 旧卡数量没有因迁移大幅翻倍；
- 旧 Review History / Due / Interval 保留；
- 每个 Note 有稳定 NoteID；
- NoteID 已成为 Note Type 第一字段；
- 新版 `study.csv` 重新导入只更新已有 Notes + 增加真正新 Note；
- 以后新增教材不会为已有 learning unit 创建第二套 FSRS 记忆状态。