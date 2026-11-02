# NEXT — Klose Learning

更新：2026-11-02。本轮：NCE1 首批 Lesson 1–17 的真实笔记合入与审核发布。

## 当前检查点

首批150条有实物照片证据的来源记录完成明确义项核对：109条复用既有稳定身份，41条新增KV003016–KV003056。复用项中108条此前已发布，KV000746 Danish是既有库存首次发布。因此Vocabulary发布2,995条、allowed 2,937、held 58；Expressions仍176条。动态数值和哈希以 `anki/klose/releases/current.json` 为准。

旧3,015个注册身份记录完整保留；四年级前221条顺序保持；14个本批目标留在更早四年级段，136个进入NCE1段。已释放的同义笔记只补来源并调整尚未学习新卡的课程位置，不重新创建卡。

区别处理：excuse原谅/借口、watch手表/观看、make品牌/制作、well健康/很好地、clean干净/打扫、smart外表/才智及语言/国籍义。Mr.复用Mr。too原有也义例句曾误用太义，本批以原ID修正例句。Japanese和clean的已有核心释义与其原有例句对齐，不改稳定身份字段。

52条变化的呈现已经逐条模型审校，凭据绑定当前内容指纹；不是家长人工确认。普通pipeline不能自动批准。实物来源原始CSV和旧ID/审批/发布历史保留。

验证记录：`anki/klose/review/nce1_reconciliation/batch_001_transaction_validation.json`、统一pipeline状态与回归日志。只有完整历史校验、重复构建、独立前后对账、负向测试通过后，本检查点才随事务提交。

## 尚未完成的全册工作

本批只完成Lesson 1–17。总906条来源中，其余756条仍未做完目标义项确认，尚未纳入NCE1学习段。不得把首批发布或Build Valid/Release Ready解释为全册完成。

后续先补充教材语境对应的目标词性/义项，再分批进行复用/新增身份、适龄内容和显式审核。不要把通用词典的全部释义当作本课目标，不按拼写直接批量复用。后续阶段继续沿用四年级 → 新概念 → 五六年级 → 第三方顺序；已学卡的调度始终归Anki。

任务文档：`docs/NCE1_INTEGRATION.md`；首批导入：`docs/NCE1_BATCH001_IMPORT.md`。本批未操控Anki设备，尚无本次Desktop/iPad导入凭据。

## 设备与学习状态

上一正式发布对应 release `35b833e58397e5f0f4df36e65e63bbf7aaffe3561f0e68c80de51ce2898bfaad`：

- Vocabulary：2,953 条；用户已确认 Desktop 导入并同步 AnkiWeb。
- Expressions：176 条；用户已确认 Desktop 导入并同步 AnkiWeb。
- 五条重复目标 KV001461、KV001481、KV001808、KV002569、KV002636 仍按 Admission held / New 卡暂停。
- 2,864 张未暂停 Vocabulary New Cards 已按当时 LearningOrder 完成 Reposition。
- iPad 未实际确认同步或抽查，不记为已验收。
- 学习试点仍为 `awaiting-observation`，没有记录实际学习周、学习效果或成绩。
