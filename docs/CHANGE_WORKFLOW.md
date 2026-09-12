# 日常变更与发布

本地与 GitHub Actions 统一执行 `tools/klose_pipeline.py`。从仓库根目录运行，使用 Python 3.12 标准库和完整 Git 历史。

## 输入与状态

| 修改对象 | 持久输入 | 结果 |
| --- | --- | --- |
| 来源、教材版本 | source_reference / reconciliation / source registries | 核对来源后才能进入 Identity |
| 稳定身份 | note_registry / expression_registry、显式 migration | 新增可追加；既有身份受 Git 基线保护 |
| Vocabulary 题面、例句 | learner/prompt_hint_overrides.csv、presentation_adjustments.csv；第三方例句优先使用 content_corrections.csv | 重建后对应内容退回 pending |
| Vocabulary 新卡准入 | learner/admission_decisions.csv | allowed/held 按当前决策生成，不改稳定身份 |
| Expressions 呈现 | expressions/learner/current.csv | 日常 durable 输入；历史 materialize/refine 工具不在日常流水线 |
| Expressions 准入 | expressions/learner/learning_admission.csv | held 保留身份、清空顺序；allowed 顺序需重新连续排列 |
| 审核 | 各自 learner/review_approvals/ 的新批次 | 逐条核对后显式批准；既有凭据不可改写 |
| 学习证据 | feedback/ | 未观察不推断；困难支撑词进入发布 blocker |

`Vocabulary Master`、Vocabulary `learner/current.csv`、review 同步状态和 publish 由上游生成；不要手工修改发布 CSV 修结果。Expressions 的 `current.csv` 是当前人工/模型维护呈现，不在每日构建中重新套用历史生成模板。

## 执行

```bash
python tools/klose_pipeline.py build --baseline <本轮修改前的commit>
```

构建包括历史身份/发布/审批保护、全部 Vocabulary overlay、准入、题面、review 同步和 Expressions 构建。`build_valid=true` 允许存在待审内容。随后逐条审校发生变化的内容，使用 [显式审核流程](LEARNER_REVIEW_REGISTRY.md)。

```bash
python tools/klose_pipeline.py all --baseline <本轮修改前的commit> --report /tmp/klose-status.json
python -m unittest discover -s tests -v
```

`verify` 仅检查当前已生成状态，不能替代变更后的完整 `all`。`all` 会完整重建两次并比较字节一致性；成功后生成 [current.json](../anki/klose/releases/current.json)。发布状态 JSON 分别报告 Build Valid 与 Release Ready；失败返回非零。没有通过 gate 的本地 CSV 不可导入。

PR 使用 base SHA；main push 使用 event.before；本地默认 HEAD^。浅克隆或找不到基线必须补齐 Git 历史，不能跳过检查。历史一次性数量在固定 commit 与 manifest 下校验；当前数量从集合及准入策略推导。

CI 的 `Build Valid` 与 `Release Ready` 是两个独立检查名。路径覆盖 `tools/**`、`tests/**`、Klose 全部输入和基础 Master；审批不由 CI 自动生成。只有完整 gate 和回归检查通过的 main push 才保存派生产物。

`all --persist` 仅用于当前 main 的干净 checkout：重新读取 origin/main，确认未发生并发变化，检查生成文件范围，普通 fast-forward push。远端已前进时失败，必须从新 main 重建；不把旧产物 rebase 到未验证输入上。

## Identity migration

Vocabulary 既有身份变更必须在 identity_migrations.csv 追加未用过的 MigrationID，包含 `NoteID, Status=approved, BaselineCommit, BeforeFingerprint, AfterFingerprint, Reason`；前后 fingerprint 由 `klose_git_history.identity_fingerprint` 对 `check_klose_persistent_state.IDENTITY_FIELDS` 计算。原有字段和历史行保留。

授权只匹配该基线和该次精确变化；同一个 ID 的旧批准不能给以后改义豁免。Expressions 当前直接阻止历史身份变化；若确需 split/merge，应先设计显式迁移及回归验证，不可删掉保护绕过。

## 完成标准

遵守 AGENTS 的 `IMPLEMENTED → VALIDATED → CHECKPOINTED`：最终代码状态完整重建、独立反向验证、状态转换与 diff 范围检查后，记录 NEXT 和对应任务文档。再重复重建一次，确认派生文件无漂移。提交代码不代表设备已导入，也不代表学习效果已验证。

已完成的一次性 Expressions release 与第三方自动批准 workflow 移到 [历史 workflow](archive/workflows/)。其他来源摄取/分配交易工具仍按各自历史范围使用，不属于日常内容维护命令。
