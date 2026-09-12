# 2026-09-12 全面体检整改记录

状态：IMPLEMENTED / VALIDATED / CHECKPOINTED。审计基线为 `a64a4ad0d108da5dc41d2f863a0a205cd9c53bcb`。本轮只修改 repo 内容与机制，设备导入和真实学习观察另行记录。

结论：当前工程机制已能更可靠地保护学习身份、区分目标义项和审核状态，并支持日常修订。是否达到可持续复习和迁移使用目标，仍需实际学习反馈验证；构建成功不能代替效果证据。

## 逐项整改前后对比

| 整改项 | 整改前 | 整改后 | 验收证据 |
| --- | --- | --- | --- |
| 1. 题面与重复目标 | allowed 中有 40 组、84 条完全相同的 Word+PromptHint 题面；大小写归一后 43 组、91 条。提示仅 4 条；五组单复数来源重复目标同时进入新卡 | 必要提示扩展到 81 条，所有 allowed 同词题面均有可区分的提示；五条新增重复目标 held，保留较早学习身份与全部发布 ID | front gate 歧义为零；总发布仍 2,953；allowed 2,894→2,889，held 59→64 |
| 2. Expressions 审核独立 | materialize/refine 会生成 model-reviewed 并同步新 hash；生成与审核混在一起 | 生成器只产生/保留待审状态；逐条审校后追加不可变凭据。改 Prompt 等内容会失效，伪造 registry 状态不能发布；日常构建不重跑历史模板生成器 | 故意改错 Prompt、重跑两种历史生成器均不能自动批准；110 条显式模型审校凭据，既有 66 条人工确认保留 |
| 3. 历史身份与审核保护 | 某 NoteID 曾有 approved migration 就可能长期跳过改义检查；缺失基线可能跳过历史检查 | migration 限定唯一新批次、确切 Git 基线、before/after identity fingerprint 和理由；审批/迁移历史不可改写；缺少 Git 基线阻断 | 旧 KV000901 审批不能豁免新改义；缺基线、旧凭据改写、重复消费迁移均被拒绝 |
| 4. 日常规则与一次性交易分开 | 日常 gate 锁定 2,894 准入、2,720 计划、16 条修正、110 条模型审核等历史数量，合法 hold 或人工升级会误报 | 当前 gate 检查集合、身份、审核凭据、连续顺序；历史交易单独对冻结 commit/manifest 校验；held 可以保留已审核音标 | 第 17 条修正、五条 Vocabulary hold、Expressions hold→恢复、model→human 均通过；冻结交易仍受保护 |
| 5. 统一构建和发布状态 | 本地/CI 长命令链分散，部分依赖未触发；release 失败可被 continue-on-error 隐藏；生成后 rebase 存在未验证输入风险 | 单入口 klose_pipeline.py；Build Valid / Release Ready 分开；覆盖 tools、tests 和全部 Klose 输入；完整 all 自带第二次重建的字节一致性检查；远端变化时拒绝保存旧产物 | Build Valid=true / Release Ready=false 的反向测试通过；并发远端变化不会执行 commit/rebase；完整重建 byte drift=0 |
| 6. 学习反馈和掌握边界 | allowed 可被用作例句支撑词已经掌握的替代，缺少最小效果回路 | 添加真实观察、支撑词证据、调整决策和试点状态；未知词为 advisory，已观察困难进入 blocker；未观察不填写成绩或开始时间 | unknown 不等于 mastered；needs-support→阻断、supported→恢复测试通过；现有观察记录为零，未声明学习有效 |
| 7. 文档与当前状态 | 首页仍是通用词库宣传；AGENTS/NEXT 过长，多处“当前”计数停留在旧迁移 | 首页改为 Klose 工作入口；稳定规则、日常 SOP 和历史检查点分开；current.json 汇总当前计数、内容/模板 hash；设备凭据独立 | 历史文档保留且标注适用条件；当前导入 SOP 从清单取数，不再套用旧全量重置流程 |

## 本轮具体内容修正

| 对象 | 修改前 | 修改后 |
| --- | --- | --- |
| KV000424 cook | 核心释义混写“厨师；做饭”，但题面和例句是名词 | 当前展示收窄为“厨师”；Stable Identity 不改 |
| KV002132 miss | 动词题面显示大写 Miss，与称谓混淆 | 展示为小写 miss，并加 v. 提示；CanonicalWord 历史记录保留 |
| KV000075 sure | “当然；可以”却配 Are you sure… 的确定性例句 | 请求帮助后回答 Sure!，与 KV002731 的判断义区分 |
| KV002597 size | 一般“大小”仍用鞋服尺码例句，和既有 size 目标重叠 | The boxes are the same size. / 这些盒子的大小相同。 |
| KE000137 | Prompt 直接给出 Maybe you should 句式 | 中文情境“朋友身体不舒服，你想委婉地建议他去看医生” |
| KE000147 | 把 too 填入 place phrase 槽位 | There is soil on the ground.，地点槽位为 on the ground |
| PromptHint | cook/over 的少量提示覆盖不足 | 词性、月份/情态、天气/重量、购物/课程等最小线索；77 条新增、2 条旧提示修订 |

五条重复准入决策（不删除、不合并身份）：

| 暂缓新增 ID | 学习目标 | 优先保留 ID |
| --- | --- | --- |
| KV001461 | child | KV000333 |
| KV001481 | chopstick | KV000672 |
| KV001808 | glove | KV000259 |
| KV002569 | shoe | KV000256 |
| KV002636 | sock | KV000096 |

这些 hold 只作用于新增学习；已经进入 Anki Learning/Review 的卡不由 repo 重置。原前 627 条 curriculum 顺序保持，后续 2,195 条顺序字段因五条退出而连续重排。

## 最终验证与边界

完整 `python tools/klose_pipeline.py all --baseline a64a4ad0d108da5dc41d2f863a0a205cd9c53bcb` 通过，内置重复构建字节漂移为零。`python -m unittest discover -s tests -v` 的 16 项回归通过；故障注入使用隔离数据副本，并校验没有修改正式源文件。

独立 diff 核对：11 个关键身份、来源与历史发布文件和审计基线字节一致；Vocabulary/Expressions ID 集合无增删。Vocabulary 仅两条例句/翻译、一条释义、一处展示大小写、必要提示与五条新卡准入变化；Expressions 仅两条呈现内容变化。发布 manifest 中两个正式 artifact SHA-256 均与文件一致。

本轮显式重新审核 80 条待审 released Vocabulary；2 条原本处于发布范围外的历史 pending 保留，不被“清零”误批准。Expressions 当前仍为 176 条，其中历史人工 66、显式模型 110；没有制造新的人工确认。

当前发布范围内 review pending=0、歧义题面=0、已观察支撑词 blocker=0。仍有 18 条 held-library 音标缺口，继续保留；2,866 条例句包含未评估支撑词，属于后续抽查线索，不能解释成已经发现 2,866 条不合格例句。

最新可导入内容与设备当前内容是两个状态。Vocabulary 上一版和 Expressions 原版的用户同步确认仅保存为历史；本次两份更新包均等待实际设备导入/同步确认。学习效果也尚未观察，下一步按 [当前导入 SOP](ANKI_CURRENT_RELEASE_IMPORT.md) 与 [反馈流程](LEARNING_FEEDBACK.md) 执行。

云端交叉验证补充：修正旧 Grade 5–6 completion checker 将全仓固定为 1,189 个 active ID、准入仅等于早期教材集合的问题。保留已接受教材的来源、映射、去重和内容闭合核验；全仓准入交给当前策略验证，并把该独立检查加入统一 pipeline。
