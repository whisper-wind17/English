# Learner Presentation Review Registry

`anki/klose/learner/presentation_review_registry.csv` 是 Klose Vocabulary System 的长期审校状态之一，用来回答：**某个 NoteID 在某个 LearnerLevel 下，是否已经显式检查过学习呈现。**

## 为什么需要单独 Registry

`FirstGrade` 是来源事实；`LearnerLevel` 是当前学习者能力。一个词在 Grade 4 审核过例句，不代表 Grade 5 的例句也已经审核。因此审校状态不能只挂在 NoteID 上，也不能用“自动检查没有报错”代替。

唯一键：

```text
LearnerProfile + LearnerLevel + NoteID
```

字段：

```text
LearnerProfile
LearnerLevel
NoteID
ReviewStatus       # pending / model-reviewed / human-reviewed
ReviewedAt
ReviewerType
ReviewNote
```

## 生命周期

- 新 Note 被 release：为当前 LearnerLevel 创建一条 review 记录；未显式检查时为 `pending`。
- LearnerLevel 从 4 升到 5：同一个 NoteID 新增 Level-5 review 记录，Level-4 历史保留。
- 修改 Grade-4 例句：只影响 Level-4 presentation；不得借此修改 NoteID、source identity 或 Anki scheduling。
- `model-reviewed` 表示模型逐条审校，不等于教师人工确认；`human-reviewed` 才表示人工确认。

## 当前 Grade-4 基线

人教版一年级起点当前 release scope 为 1–4 年级，共 518 Notes。Registry 将所有 518 条显式登记；已经经过 Grade-4 override 审校的记录标为 `model-reviewed`，其余记录明确保留为 `pending`，直到完成逐条 Learner-Level review。

同步工具：

```bash
python tools/sync_klose_learner_review_registry.py
```

该工具只追加缺失的 `(profile, level, NoteID)` 状态，不会静默覆盖已有 review 决策。统计写入 `anki/klose/master/build_stats.csv`：

```text
learner_review_registry_current
learner_model_reviewed_current
learner_review_pending_current
```

这三个数字比 `learner_review_suggestions=0` 更能表达实际审核完成度。后者只表示启发式 review queue 当前为空。
