# AGENTS.md

## 1. Mission

本仓库除保存原始英语词库外，还长期维护 **Klose Vocabulary System**：多来源统一 Vocabulary Knowledge Base + 可升级 Learner Presentation + 与 Anki FSRS/Review History 向后兼容的发布数据。

先读：

- `docs/KLOSE_VOCABULARY_SYSTEM.md`：完整架构与长期机制；
- `docs/ANKI_SYNC_WORKFLOW.md`：第一次导入之后的长期重复同步 SOP；
- `docs/LEARNER_REVIEW_REGISTRY.md`：LearnerLevel 级别的学习呈现审校状态；
- `docs/ANKI_FIRST_IMPORT.md`：第一次正式导入与一个主 Deck 的操作规则；
- `docs/ANKI_MIGRATION.md`：旧 Word-first Anki 数据的一次性迁移。

---

## 2. 不可破坏的规则

1. **Stable NoteID 最高优先级。** 已分配 ID 不得因排序、重建、教材增加或内容修改而重编号、复用或漂移。
2. **NoteID 来自 committed Registry。** 不得从 Master 每次重新 enumerate；Registry/Source Identity Map/Release Registry 缺失时必须失败，不能静默重建。
3. **一个 Note = 一个明确 learning unit / target sense，不等于一个字符串。** 同形异义允许多个 NoteID。
4. `CanonicalWord` / `MatchKey` 只用于候选匹配，不是业务主键；词性/义项/大小写/短语边界有歧义时进入 review，禁止静默 merge。
5. 同一已学 learning unit 不创建第二套 FSRS 记忆状态；新增来源优先扩展 provenance。
6. **FirstGrade 与 LearnerLevel 分离。** 前者是来源事实，后者决定今天怎么学。
7. 学习范围必须按 **source-scoped occurrence** 判断，不得用全局 FirstGrade 推导。
8. **Learner Review 必须按 LearnerLevel 分离。** Grade 4 的审核状态不能自动继承为 Grade 5；唯一键为 `LearnerProfile + LearnerLevel + NoteID`。
9. **Review 必须绑定 ContentFingerprint。** `MeaningPrimary / ExampleSentence / ExampleTranslation / LearnerLevel` 等受审内容变化后，旧 approval 必须失效为 `pending`，禁止沿用 reviewed 状态。
10. 原始 Source 不覆盖；generated output 不作为长期手工维护入口。
11. **禁止手工编辑 `publish/study.csv` 和 `publish/anki-import.csv`。** 内容修正必须发生在 Source / Identity / Fact / Learner / Release 等上游层，再通过构建生成发布文件。
12. identity merge/split 是高风险迁移，必须先评估现有 Anki history。
13. 任何架构优化优先保护已有 Anki Review History / FSRS state。
14. 自动结构检查、模型审校、人工确认、教材原文核对必须明确区分，不能互相冒充；`review queue = 0` 不等于全部内容已显式审校。
15. `approve_klose_learner_review.py` 只能在完成真实逐条审校后显式执行；approval manifest 是审计记录，不得覆盖旧批次。
16. **Anki 正式同步只使用 `publish/anki-import.csv`。** `study.csv` 是 repo 内部 released-data 标准快照/审计文件，不直接作为 Anki 导入包。
17. **1 Note = 1 Card。** 当前 Note Type 只保留一个 `Recognition` Card Type；不得误用 reversed card 使学习量翻倍。
18. **Suspend 只用于尚未学习的 New Cards 的准入控制。** 已进入 Learning/Review 的旧卡不得因教材、年级或 active scope 变化而重新 Suspend，避免中断 FSRS 复习链。
19. 对需求假设保持质疑；发现 Anki 行为、数据或学习机制前提不成立时先验证。

---

## 3. 真源与数据流

内容侧：

```text
Raw Source
→ Source Adapter / Curation
→ Identity Registry + Source Identity Map + Source Occurrences
→ Vocabulary Master
→ Learner Layer + Learner Review Registry
→ Release Registry
→ study.csv            # generated internal released snapshot
→ anki-import.csv      # generated Anki release artifact
→ Release Gate
→ Anki
```

学习侧：Anki 是 `Review History / FSRS state / Due / Interval / Learning / Review / Suspended` 的唯一真源；repo 不重建这些状态。

长期统一区：

```text
anki/klose/
├── config/                    # learner/scope config
├── master/                    # NoteID/source identity/release registries + master + occurrences
├── learner/                   # current presentation / overrides / review registry / approval manifests
├── anki/                      # frozen Note/Card template contract
├── publish/                   # generated study/anki-import/all/onboarding/migration/views
└── review/                    # identity / semantic / learner queues
```

当前首批 Source Adapter：

```text
anki/人教版一年级起点/
SourceID = rj_start1
```

---

## 4. Identity / Scope / Learner Contract

Identity 至少区分：

```text
NoteID          # 永久主键
CanonicalWord   # 规范词形
MatchKey        # 候选匹配 key
SenseLabel      # target sense 锚点
```

`SourceItemKey` 是 source adapter 内部的持久 item key；当前 `rj_start1` 基线可以使用规范化词形，但**不得把这一实现泛化成“所有未来来源都按 surface word 自动 merge”**。未来来源存在同形异义、词性或短语边界歧义时必须使用更细粒度的 source-native/sense-aware key 并进入 identity review。

Provenance 必须保留来源作用域，例如：

```text
source::rj_start1::grade::4::上
source::beijing::grade::3::下
source::newconcept::book::1
```

Learner Layer：

```text
LearnerProfile
LearnerLevel
ExampleSentence
ExampleTranslation
PresentationStatus
```

例句按 LearnerLevel 判断：自然、目标义项清晰、明显低于阅读上限；不要机械追求复杂，也不要机械跟随 FirstGrade。

Learner Review Registry：

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

---

## 5. Anki 发布契约

长期 Note Type：`Klose Vocabulary`；**始终一个主 Deck**：`Klose-English::Vocabulary`。

正式 Note Type 字段第一列必须是 `NoteID`。长期重新导入使用同一 Note Type、`Existing notes = Update`、`Match scope = Note Type`。

发布文件职责：

```text
anki/klose/publish/study.csv       # generated：Released Set 的内部标准快照/审计 CSV，不直接导入 Anki
anki/klose/publish/anki-import.csv # generated：唯一正式 Anki 导入文件，带官方 #file headers
anki/klose/publish/all.csv         # generated：完整库存，不是默认导入入口
```

长期更新固定为：

```text
修改上游
→ rebuild study.csv
→ generate anki-import.csv
→ release gate
→ 导入最新版 anki-import.csv
```

严禁：

```text
直接修改 study.csv
直接修改 anki-import.csv
把 onboarding/by-source CSV 当成另一套正式导入源
```

`anki-import.csv` 必须：

- 数据与 `study.csv` 完全一致；
- UTF-8 无 BOM；
- 没有普通 CSV 数据表头行；
- 使用 `#separator / #notetype / #deck / #tags column / #columns`；
- 第一数据字段始终为 `NoteID`。

Note/Card contract：

```text
anki/klose/anki/
```

只保留一个 Card Type：`Recognition`，因此 `1 Note = 1 Card`。

CSV/教材/年级不是 Deck。学习阶段通过 system-managed Tags + Suspend/Unsuspend 控制；Klose 日常不切换牌组。

当前 Grade-4 onboarding Tags：

```text
stage::grade4-new             # 四年级首次出现，当前优先学习
stage::grade4-review          # 四年级再次出现的低年级旧词
stage::lower-grade-backfill   # 1–3 年级其余查漏词
```

三个 onboarding CSV 只是便利视图，不是三个牌组，也不是正式导入包。

`release_registry.csv` 是长期增长状态：Note 一旦进入 Anki，原则上持续留在 `study.csv`/`anki-import.csv` 以接受后续内容升级。每次新增 release scope 必须显式记录 `released_at`，不能复用项目初始日期。

repo 生成的来源/年级/stage Tags 属于 system-managed；长期重新导入可能更新这些 Tags。个人长期备注使用不参与 CSV mapping 的 `UserMemo` 或 Card Flag。

---

## 6. 当前执行入口

Source-specific：

```text
tools/build_anki_rj_start1.py
tools/check_anki_example_vocab.py
tools/export_anki_review_input.py
```

Global Klose Vocabulary：

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
```

显式审批工具（**不属于日常 CI**）：

```text
tools/approve_klose_learner_review.py
```

本地完整验证顺序：

```bash
python tools/check_klose_persistent_state.py
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/sync_klose_learner_review_registry.py
python tools/check_klose_learner.py
python tools/check_klose_release_ready.py
```

CI：

```text
.github/workflows/build-anki-rj-start1.yml
.github/workflows/build-klose-vocabulary.yml
```

**Release readiness 必须先通过，之后 CI 才能 commit/push generated release。** 禁止先发布再校验。

任何相关修改完成前，都要确认对应 CI 成功，并检查：

```text
anki/klose/master/build_stats.csv
anki/klose/master/source_identity_map.csv
anki/klose/learner/presentation_review_registry.csv
anki/klose/learner/review_approvals/
anki/klose/review/identity_review.csv
anki/klose/review/learner_review.csv
anki/klose/review/future_vocab_review.csv
anki/klose/publish/study.csv
anki/klose/publish/anki-import.csv
```

---

## 7. 变更流程

### 新增教材/词书

1. 保留 Raw Source；
2. 解析为 source-scoped occurrences，并定义稳定的 source-native `SourceItemKey`；
3. 与 Registry 做 sense-aware candidate matching；
4. 将确认后的 `SourceItemKey → NoteID` 决策写入 committed `source_identity_map.csv`；
5. 明确已有 unit → 原 NoteID + 扩展 provenance；
6. 明确新 unit → 追加新 NoteID，旧 ID 不重排；
7. 模糊项 → review，禁止仅凭相同 surface word 静默 merge；
8. 生成当前 Learner Layer；
9. 为当前 LearnerLevel 建立/补齐 Learner Review Registry；
10. 逐条审校后才允许显式 approval；
11. 根据带 `released_at` 的 release scope 决定新 Note 是否进入 released set；
12. 从上游重建 `study.csv` 与 `anki-import.csv`；
13. release readiness 通过后才允许 commit/push generated release；
14. 用户侧只重新导入最新版 `anki-import.csv` 到同一 Note Type / 主 Deck。

### 升 Learner Level

只升级 Learner Presentation；NoteID / identity / source facts 不变。新 LearnerLevel 的 review 默认 `pending`，不能继承旧 Level 结论。完成逐条审校和 approval 后，从上游重建，再重新导入同一个 `anki-import.csv` 更新已有 Notes，不重建 Card。

### 修正 learner content

任何已 reviewed Note 的 Meaning/Example/Translation 变化都必须导致 fingerprint 变化；`sync_klose_learner_review_registry.py` 应把它重新置为 `pending`，待再次审校。不得直接改 publish CSV 绕过 review。

### 修正 identity

merge/split 必须单独设计 migration，禁止当作普通清洗直接执行。

---

## 8. Quality Gates

必须检查：

- Persistent Registry / Source Identity Map / Release Registry 存在且内部一致；
- Registry 中 NoteID 唯一且长期稳定；
- canonical/case/homograph 候选冲突；
- 每条 Master 有可追溯 source occurrence；
- source-scoped grade/level 不被全局字段覆盖；
- released Notes 的 LearnerLevel / Meaning / Example / Translation 完整；
- 每个 released Note 都有当前 `LearnerProfile + LearnerLevel` 的 Learner Review Registry 记录；
- 必须显式报告 `model-reviewed / human-reviewed / pending` 数量；
- **只有 `pending=0` 且 ContentFingerprint 全部匹配，才能描述为“可正式导入”。**
- Grade-4 learner examples 不无意使用同来源明确到后续年级才首次列出的词；
- `study.csv` 必须与 Released Set 一致，NoteID 唯一；
- `anki-import.csv` 必须与 `study.csv` 数据完全一致、UTF-8 无 BOM且 Anki file headers 正确；
- 每个当前 released Note 必须恰好属于一个 `stage::`；
- 当前 Note Type 必须只有一个 Card Type，首次基线应满足 `518 Notes = 518 Cards`；
- by-source/by-grade/onboarding 文件只是视图；
- deterministic build；
- 不静默 fallback 到未经审校的成人词典首义。

`0 issues` 只代表对应自动规则未发现问题；`model-reviewed` 也不等于出版社或英语教师认证。

---

## 9. Working Style

- 开始任务先读本文件和相关 docs，再检查 repo 当前状态；
- 先判断变更属于 Source / Identity / Fact / Learner / Review / Release / Publish / Anki Migration 哪一层；
- 批量处理前先验证样本和边界案例；
- 修改后 re-check 代表性词、全量统计、review queue、fingerprint、release readiness 和 CI；
- 能写成脚本/CI 的约束，不只写在 Prompt/文档；
- `AGENTS.md` 只维护项目规则和能力地图，详细机制放 `docs/`。
