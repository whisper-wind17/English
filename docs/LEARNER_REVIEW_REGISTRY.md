# Learner Presentation Review Registry

`anki/klose/learner/presentation_review_registry.csv` 是 Klose Vocabulary System 的长期审校状态，用来回答：**某个 NoteID 在某个 LearnerLevel 下，当前这版学习呈现是否已经显式检查过。**

## 为什么需要单独 Registry

`FirstGrade` 是来源事实；`LearnerLevel` 是当前学习者能力。一个词在 Grade 4 审核过，不代表 Grade 5 也审核过；同样，昨天审核过的 Grade-4 例句如果今天被修改，也不能继续沿用昨天的 `reviewed` 状态。

唯一键：

```text
LearnerProfile + LearnerLevel + NoteID
```

字段：

```text
LearnerProfile
LearnerLevel
NoteID
ContentFingerprint
ReviewStatus       # pending / model-reviewed / human-reviewed
ReviewedAt
ReviewerType
ReviewNote
```

`ContentFingerprint` 绑定当前：

```text
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerProfile
LearnerLevel
```

只要这些内容发生变化，`tools/sync_klose_learner_review_registry.py` 就会把旧审批失效为 `pending`，禁止“内容已经改了但审核状态还显示 reviewed”。

## 生命周期

- 新 Note 被 release：为当前 LearnerLevel 创建 review 记录，默认 `pending`。
- LearnerLevel 从 4 升到 5：同一个 NoteID 新增 Level-5 review 状态；Level-4 历史保留。
- learner content 变化：fingerprint 变化，旧审批自动失效为 `pending`。
- `model-reviewed` 表示模型逐条审校，不等于出版社/教师认证。
- `human-reviewed` 只用于真实人工确认。

正常同步：

```bash
python tools/sync_klose_learner_review_registry.py
```

同步工具不会自动把新的 `pending` 内容提升为 reviewed。

## 显式审批

完整内容审校完成后，使用：

```text
tools/approve_klose_learner_review.py
```

审批工具不会进入日常 CI；它要求 review reports 为空、当前 fingerprint 与 Registry 一致，并生成不可覆盖的 approval manifest：

```text
anki/klose/learner/review_approvals/<batch-id>.csv
```

这样以后可以追溯“哪一批内容、哪个 fingerprint、何时、由哪类 reviewer 确认过”。

## 当前 Grade-4 Baseline v1

人教版一年级起点当前 release scope 为 1–4 年级，共 518 Notes。2026-09-05 完成 Grade-4 learner presentation 的逐条模型审校并生成审批批次：

```text
review_approvals/grade4-baseline-v1.csv
```

当前状态：

```text
learner_review_registry_current = 518
learner_model_reviewed_current  = 518
learner_human_reviewed_current  = 0
learner_review_pending_current  = 0
```

另外：

```text
identity_review.csv      = 0 rows
learner_review.csv       = 0 rows
future_vocab_review.csv  = 0 rows
```

最终发布前由：

```bash
python tools/check_klose_release_ready.py
```

统一验证 `study.csv`、review reports、Registry review state 和 ContentFingerprint。只有该检查通过，当前 `study.csv` 才可以视为正式 Anki release。
