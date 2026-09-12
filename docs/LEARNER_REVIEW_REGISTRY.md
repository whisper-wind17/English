# 呈现审核与凭据

审核回答的是：某个稳定 ID 在该 LearnerProfile / LearnerLevel 下的当前内容是否被显式检查。模型审校、人工确认和自动 gate 分开记录。

| 对象 | 状态 | 显式审核工具 | 凭据 |
| --- | --- | --- | --- |
| Vocabulary | pending / model-reviewed / human-reviewed | tools/approve_klose_learner_review.py | learner/review_approvals/ |
| Expressions | pending / model-reviewed / approved（人工） | tools/approve_klose_expression_review.py | expressions/learner/review_approvals/ |

两个命名体系保留兼容，不要求 model-reviewed 恒定为某个历史数量；有真实人工审核凭据时可以升级。

Vocabulary fingerprint v2 覆盖 CanonicalWord、SenseLabel、Word、UK/US IPA、Meaning、Example、Translation、Profile、Level，以及非空 PromptHint。空 PromptHint 保持原 v2 hash；新增、修改或清空原有非空提示均使旧审核失效。LearningOrder 属于准入元数据，不进入内容 fingerprint。

Expressions fingerprint v1 覆盖 Profile、Level、ExpressionID、Prompt、PromptHint、Target、Pattern、MeaningUsage、Examples、FunctionLabel、ContextNote。

日常 `klose_pipeline.py build` 只同步失效状态。改变内容、缺少 fingerprint 或 Expressions 缺少匹配凭据会进入 pending；release gate 对两类审核都要求当前 fingerprint 与不可变凭据一致。生成脚本不授予批准，手改 registry 状态不能替代审核记录。

Vocabulary 逐条审校后：

```bash
python tools/approve_klose_learner_review.py --batch-id <新批次> --profile klose --level 4 --expected-count <本次待审数量> --reviewer-type model --review-note '<实际审校范围和结论>' --confirm-all-current --pending-only
```

Expressions 逐条填写审核 CSV，包含 registry 的全部字段以及 ReviewerType、Evidence；Fingerprint 必须是当前内容，由 `klose_expression_review_fingerprint` 计算。随后：

```bash
python tools/approve_klose_expression_review.py --review-file <审核CSV> --batch-id <新批次> --confirm-reviewed
```

人工状态只用于实际人工确认，模型不得代填。审批批次不可覆盖、删除或重写；新审核追加新批次。历史审批只证明其自己的内容版本，不能授权其他内容。历史人工凭据迁移保留既有确认来源，不代表本轮新增人工审核。

审批后运行 `python tools/klose_pipeline.py all` 和必要回归检查。当前数量以 [发布清单](../anki/klose/releases/current.json) 为准，历史 Grade-4 snapshot 见 [归档审核文档](archive/checkpoints/2026-09-12-before-maintenance/LEARNER_REVIEW_REGISTRY.md)。
