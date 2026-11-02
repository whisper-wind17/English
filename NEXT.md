# NEXT — Klose Learning

更新：2026-11-02。本轮：新概念英语一全册词汇合入。

## 当前检查点

全册906条来源记录均完成显式目标义项映射，形成889个学习目标；前150条照片事实保持，后756条由独立SourceSense审核记录绑定来源指纹。原始来源、首批决定和旧审核不改写。不将旧版网络参考升级为2022智慧版逐页实物核验。

全册目标618个复用旧身份，271个为新词或独立义项（含首批41个）。本次续批新增230个ID：KV003057–KV003286；旧3,056个身份完整保留。已有58条呈现补提示或按原例句收窄释义，9个旧library-held目标准入，明确暂停的重复目标不解除。

本次Vocabulary发布由2,995增至3,226；allowed3,177、held49。新增发布231条含230个新身份及既有库存with。Expressions仍176条；模板不变。具体release_id、SHA256和动态数量读取 `anki/klose/releases/current.json`。

四年级前221个目标保持；新概念段782个目标，另107个新概念目标沿用更早四年级位置。后续仍为五六年级、第三方。已学卡调度归Anki，GitHub不写FSRS或历史。

## 验证与边界

新增全册覆盖门禁、来源义项指纹、每个批次封存哈希；完整pipeline、确定性复建、回归和独立事务对账通过后才随事务保存本检查点。真实Git历史验证由远端最终事务/PR执行，不用本地浅快照冒充。报告：`anki/klose/review/nce1_reconciliation/full_book_transaction_validation.json`。模型审校凭据不是家长人工确认，也不代表学习效果。

当前全册任务文档：`docs/NCE1_FULL_BOOK_RELEASE.md`；设备导入：`docs/NCE1_FULL_BOOK_IMPORT.md`。旧检查点原样归档 `docs/archive/checkpoints/2026-11-02-before-nce1-full/NEXT.md`。

## 设备与学习状态

2026-11-02 用户已确认 Windows Anki Desktop 将全册正式 `Klose Vocabulary` CSV 导入现有 Collection，并成功执行 Desktop → AnkiWeb Sync。导入结果截图：文件 3,226 条；273 new、2,800 updated、153 already present，旧 2,953 条均按 `NoteID` 匹配（未新建第二套 Note Type），`UserMemo` 未映射。对应仓库 `release_id=50dca1d95a9f2c9f307672d2117f0683fe1c84ec2813d7437872aae42bf50e2f`；仓库预期文件 SHA-256 为 `ff2b4e747c2015dc09aa71165ebc685f5a31b512a4fdba2e39a81df9ef241831`，设备本地未提供独立哈希计算，不声称逐字节验收。

完成设备抽查：一张旧 Review 卡保有 3 条历史复习记录以及 FSRS / Interval 信息；一张新卡 Reviews=0；`LearningOrder` 空值 49 张，与 held 数一致，未暂停的 New 卡中空值 0；2965 张未暂停 New 卡经升序 Reposition，`000198` 对应 `New #1`，四年级与新概念交界和出卡配置已由用户检查。**仅为抽样与用户确认，不能推断所有卡均已逐张验收。**

**iPad 仍未收到同步与复习历史抽查的用户确认**，故当前设备 rollout 状态保留为 Desktop 已同步、iPad 待验收；不把整个 release 标为跨设备完成。设备凭据写在 `anki/klose/releases/device_receipts.json`，未修改仓库的学习内容、NoteID、Release、FSRS 或调度数据。Expressions 本次未重新导入，沿用此前已确认的 176 条；学习反馈仍为 `awaiting-observation`。
