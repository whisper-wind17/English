# Learner Presentation Review Registry

`anki/klose/learner/presentation_review_registry.csv` 是 Klose Vocabulary System 的长期审校状态，用来回答：**某个 NoteID 在某个 LearnerLevel 下，当前这版学习呈现是否已经显式检查过。**

## 1. Registry identity

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

`FirstGrade` 是来源事实；`LearnerLevel` 是学习难度；二者都不能替代 learner presentation review。

## 2. ContentFingerprint

当前 fingerprint v2 绑定：

```text
CanonicalWord
SenseLabel
Word
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerProfile
LearnerLevel
PromptHint（仅非空时）
```

实现统一由：

```text
tools/klose_review_fingerprint.py
```

提供，review sync / approval / release gate 不应各自维护不同版本的 hash 逻辑。

### PromptHint compatibility rule

`PromptHint` 是正面可见的 Learner Presentation，因此非空值必须进入 fingerprint。但为了不给历史普通 Notes 制造无意义的全量 re-review：

```text
PromptHint == ""    -> 保持原 fingerprint-v2 hash 不变
PromptHint != ""    -> 在 v2 payload 后追加 PromptHint，再计算 hash
```

因此新增一个空 `PromptHint` 字段不会让 638 个 Notes 全部 pending；真正新增/修改 hint 的 Note 才失效旧审批。

任何 fingerprint 内容变化后，`tools/sync_klose_learner_review_registry.py` 都必须把该 Note 置为 `pending`，清空旧 reviewer metadata，禁止内容变化后静默继承 approval。

## 3. Lifecycle

- 新 Note 被 release：当前 LearnerLevel 创建 review 记录，默认 `pending`。
- LearnerLevel 变化：同一 NoteID 创建对应 level 的 review 状态，旧 level 历史保留。
- Meaning / IPA / Example / PromptHint 等 release-visible presentation 变化：旧 approval 自动失效。
- `model-reviewed` 表示模型显式审校，不等于出版社/教师认证。
- `human-reviewed` 只用于真实人工确认。

正常同步：

```bash
python tools/sync_klose_learner_review_registry.py
```

同步工具只负责检测、失效和记录，不自动把新的 `pending` 提升为 reviewed。

## 4. Explicit approval

审校完成后使用：

```text
tools/approve_klose_learner_review.py
```

审批工具要求 review reports 为空、Registry fingerprint 与当前内容一致，并生成不可覆盖 manifest：

```text
anki/klose/learner/review_approvals/<batch-id>.csv
```

审批工具不应长期自动运行在日常 CI 中。

历史 Grade-4 主要批次：

```text
grade4-baseline-v1.csv
grade4-baseline-v2-revalidated.csv
grade4-current-v2-model-reviewed.csv
grade4-current-v2-model-reviewed-r2.csv
```

PromptHint migration 使用：

```text
grade4-prompthint-v1.csv
```

该批次的语义是：原 638 release 中只有 4 个 active homograph Notes 新增非空 PromptHint；其余 Notes 的原有 release-visible 内容保持不变。

## 5. Current Grade-4 target state

```text
released/current review scope = 638
model-reviewed                = 638
pending                       = 0
actual Grade-4 allowed        = 221
held                          = 417
```

PromptHint migration 的预期 invalidation：

```text
KV000424 cook [n.]
KV000805 cook [v.]
KV000816 over [位置]
KV000863 over [结束]

invalidated = 4
```

完成显式 approval 后必须恢复：

```text
pending = 0
```

另外普通 review queues 应保持：

```text
identity_review.csv      = 0 rows
learner_review.csv       = 0 rows
future_vocab_review.csv  = 0 rows
```

最终发布由：

```bash
python tools/check_klose_release_ready.py
```

统一验证 publish derivation、review state、fingerprint、Learning Admission 与 Anki import contract。只有该检查通过，当前 `anki-import.csv` 才可以视为正式 Anki release。
