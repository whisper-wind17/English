# AGENTS.md

## Mission

本仓库长期维护 **Klose 英语学习系统**。目标不是堆积词卡，而是让 Klose 在可持续复习负担下，准确回忆目标义项、读音和适龄语境，并长期保留 Anki FSRS / Review History。

任何涉及 Klose 的教材、Vocabulary、Expressions、Anki、FSRS、数据处理或 GitHub 修改，启动顺序固定为：

1. `/AGENTS.md`
2. `/NEXT.md`
3. `NEXT.md` 引用的当前任务文档
4. 与任务相关的 `docs/`、`anki/klose/`、`tools/`

不要仅凭聊天历史或模型记忆推测当前状态。

---

## Core invariants

1. **Stable NoteID 最高优先级。** 已存在 NoteID 不得因排序、重建、教材增加或普通内容修正而删除、重编号、复用或漂移；identity split/merge 必须有显式 migration。
2. **一个 Vocabulary Note = 一个明确 learning unit / target sense。** 同形异义允许多个 NoteID；Word / MatchKey / morphology 只用于 candidate matching。
3. **Source Fact 与 Vocabulary Identity 分离。** 教材中的 occurrence、Edition、Book、Unit、位置是来源事实；NoteID 是长期学习身份。
4. **Source Grade ≠ LearnerLevel。** Klose 可以在 `LearnerLevel=4` 下学习 Grade 5/6 来源词汇；Source Grade 不能作为学习资格的硬替代。
5. **学习准入必须显式。** staging / admission 不应长期由 Source Grade 推导。Legacy Grade-4 staging 仅用于迁移兼容，不代表长期模型。
6. **实际教材优先于第三方整理数据。** 发生冲突先做 Source Reconciliation；不同 Edition / Revision 不得静默混入同一来源事实集合。
7. **Vocabulary 与 Expressions 分离。** Useful Expressions 原文是 Source Fact，不机械执行“一句 = 一张卡”。
8. **GitHub 管内容与发布；Anki 管记忆状态。** GitHub 是 Source / Identity / Learner Presentation / Review / Release 真源；Anki 是 FSRS / Review History / Due / Interval / Card State 真源。
9. **禁止手工编辑 generated publish 文件。** `publish/study.csv`、`publish/anki-import.csv` 必须由上游状态确定性生成。
10. **正式 Anki 同步只使用 `publish/anki-import.csv`，并在同一 Note Type 原地 Update Existing Notes。**
11. **Review approval 必须绑定当前发布可见内容。** Word、Sense、IPA、Meaning、Example、Translation、LearnerLevel、非空 PromptHint 等变化后旧 approval 必须失效；缺失 fingerprint 默认 `pending`。
12. **自动检查、模型审校、人工确认、教材原文核对必须区分。** `queue=0` 不等于人工确认。
13. **Release Gate 必须消费结构化状态。** Markdown 中的 blocker 不能只停留在说明层；Source Reconciliation、Identity、Review、Publish derivation 等必须进入可执行 gate。
14. **能写成脚本/CI 的约束，不只写在 Prompt。**
15. **LearningOrder 与 Anki New # 分离。** LearningOrder 是 GitHub 中的 curriculum/admission 真源；New Card Position / Due 是 Anki 状态。对尚未学习的新卡可以按 LearningOrder materialize New #，但不得用 repo 重建已经进入 FSRS 的调度状态。

---

## Architecture map

长期逻辑：

```text
Raw Source / Actual Textbook Evidence
→ Source Occurrence + Edition / Reconciliation
→ Sense-aware Identity Resolution
→ Stable Vocabulary NoteID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Release Registry
→ generated study.csv / anki-import.csv
→ Release Gate
→ Anki
```

关键目录：

```text
anki/klose/
├── config/
├── master/             # NoteID / source identity / reconciliation / release
├── learner/            # presentation / learning admission / review registry
├── source_reference/   # 实际教材证据与 reconciliation input
├── anki/               # Note/Card contract
├── publish/            # generated outputs
└── review/             # unresolved queues
```

能力成熟度：

```text
Stable NoteID / NoteID-first Anki update      implemented
LearnerLevel independent from FirstGrade     implemented in model; legacy staging fallback remains
Learner review fingerprint / invalidation    implemented (release-visible v2 + optional PromptHint)
Structured source reconciliation gate        implemented
Git-baseline identity stability check        implemented
Source Edition physical schema               partial
Sense-aware source identity for duplicate word partial; extension registry introduced
Explicit learning admission                  implemented for current Grade-4 set; legacy fallback retained
Deterministic curriculum LearningOrder       implemented for current Grade-4 set
Homograph front-side disambiguation          implemented via optional PromptHint
Multiple source adapters                     planned
Expressions release system                   source/pattern layer only
```

当前物理兼容策略：既有 `source_identity_map.csv` 作为 legacy baseline 保持不动；新 Edition / 同词多义 identity 使用 `source_identity_extensions.csv`，避免为了升级 schema 重写已有 518 条 identity。

---

## Executable states and Definition of Done

必须区分：

```text
Build Valid        # 数据结构与生成链内部一致
Content Releasable # Source/Identity/Review/Publish gate 全部通过
Anki Updated       # 正式发布文件已原地更新到现有 Note Type
Learning Admitted  # 当前真实学习批次已显式核对，可让 Klose 开始学习
```

任何一项都不能用另一项代替。

发布前至少验证：

- committed Registry / Source Identity / Release state 存在且一致；
- Git baseline 下旧 NoteID 未消失或静默改义；
- Source Edition / reconciliation 无 blocker；
- released identity 无未决歧义；
- learner review fingerprint current，`pending=0`；
- allowed LearningOrder 与当前教材顺序一致且唯一连续；held LearningOrder 为空；
- `study.csv` 内容可逐字段由当前 Master + Learner + Admission 上游推导；
- `anki-import.csv` 与 `study.csv` 完全一致，headers / encoding 正确；
- 每个 released Note 恰好一个 stage；
- CI / release readiness 成功。

当前执行入口：

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/build_klose_learning_admission.py
tools/apply_klose_learner_overrides.py
tools/apply_klose_prompt_hints.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
tools/approve_klose_learner_review.py  # explicit only
```

---

## Working rules

- 开始任务先判断变更属于 Source / Edition / Occurrence / Identity / Learner / Admission / Review / Release / Publish / Anki 哪一层。
- 较大批量处理先验证样本和边界案例，再全量执行。
- 发现用户建议与长期不变量冲突时，先给判断、证据和影响，不因“用户同意”而破坏稳定身份或学习历史。
- `AGENTS.md` 只维护项目规则、能力地图和完成标准；架构细节与 SOP 放 `docs/`。
- 较大阶段结束或切换新对话前更新 `/NEXT.md`。

常用文档：

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
docs/LEARNER_REVIEW_REGISTRY.md
docs/ANKI_SYNC_WORKFLOW.md
docs/ANKI_FIRST_IMPORT.md
docs/ANKI_MIGRATION.md
docs/ANKI_PROMPTHINT_MIGRATION.md
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```
