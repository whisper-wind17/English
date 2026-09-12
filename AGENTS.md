# Klose Learning — 项目规则

目标：Klose 在可持续复习负担下，准确回忆目标义项、读音和适龄语境，并能主动使用 Expressions；长期保留 Anki FSRS / Review History。

启动顺序固定为 `AGENTS.md` → `NEXT.md` → 当前任务文档 → 相关代码和数据。不得仅凭聊天记忆推断 repo 状态。

## 长期不变量

1. Stable NoteID / ExpressionID 不得因排序、重建、普通修正而删除、重编号、复用或改义；split/merge 必须显式 migration。
2. 一个 Vocabulary Note 对应一个明确学习目标义项；同形异义可有多个 ID。Word、MatchKey、词形只用于候选匹配。
3. Source Fact / Edition / Occurrence 与学习身份分离；新来源不能覆盖旧来源事实。
4. Source Grade ≠ LearnerLevel；不得用来源年级代替学习能力或学习资格。
5. Admission 必须显式，allowed 仅表示准入，不能视为已经掌握。Legacy staging 只用于兼容。
6. 实际教材优先于第三方整理；版本冲突先 reconciliation，不静默混入同一来源集合。
7. Vocabulary 与 Expressions 分离；一条教材原句不机械等于一张卡。
8. GitHub 管 Source / Identity / Presentation / Admission / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。
9. 禁止手工编辑 generated publish；必须通过上游状态确定性生成。
10. 正式同步只用各自 `publish/anki-import.csv`，同一 Note Type 按稳定 ID 原地更新；UserMemo 不映射，不重建旧 Cards。
11. 审批绑定当前发布可见内容 fingerprint；内容变化或缺少匹配审核凭据即待审，生成器和 CI 不自动批准。
12. 自动校验、模型审校、人工确认、教材原文核对分别记录；queue=0 不等于人工确认或真实学习有效。
13. Source Reconciliation、Identity、Review、Admission、Publish derivation 等约束必须进入结构化 gate。
14. 能机器化的约束下沉为脚本/CI；历史批次数量仅验证冻结交易，不能锁死日常合法状态变化。
15. LearningOrder 固定六位零填充、allowed 唯一连续、held 为空；只用于仍为 New 的卡，不覆盖已学习卡的调度。

## 状态与完成标准

Build Valid、Release Ready、Anki Updated、Learning Admitted 和学习效果证据独立；任何一个不能替代其他状态。

所有代码、数据、规则和 workflow 变更必须经过 `IMPLEMENTED → VALIDATED → CHECKPOINTED`。

最后一次修改后必须在最终集成状态完成：

- 直接目标、原有不变量、代表性样本及计数/集合闭合核对；
- 独立于实现过程的第二遍反向检查，主动寻找二阶和三阶失败模式；
- 受影响状态的进入、退出、失效、重排队、重试和回退检查；
- durable / generated / transient / Anki 真源边界及 Git diff 范围检查；
- 全量 pipeline 与必要回归测试，再在 NEXT 和任务文档记录结论。

CI 成功只是证据之一。发现问题即退回 IMPLEMENTED；修复后重跑完整 Validation Gate。未完成第二遍检查不得宣告完成。批量工作先看样本和边界，再全量执行。

## 执行入口

日常本地与 CI 统一使用 `python tools/klose_pipeline.py build|verify|all`，详见 [变更流程](docs/CHANGE_WORKFLOW.md)。显式审核命令不属于自动构建。

Git 基线必须可读取（PR base / push before；本地默认 HEAD^）；缺失时阻断。已批准 identity migration 只授权记录中的一次 before → after，不提供永久豁免。

架构、导入和历史见 [Vocabulary](docs/KLOSE_VOCABULARY_SYSTEM.md)、[Expressions](docs/EXPRESSIONS_SYSTEM.md)、[审核](docs/LEARNER_REVIEW_REGISTRY.md)、[当前导入 SOP](docs/ANKI_CURRENT_RELEASE_IMPORT.md)。较大阶段结束更新 NEXT；AGENTS 只保存稳定规则。
