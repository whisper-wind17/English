# AGENTS.md

## 1. Mission

本仓库除保存原始英语词库外，还长期维护 **Klose Vocabulary System**：多来源统一 Vocabulary Knowledge Base + 可升级 Learner Presentation + 与 Anki FSRS/Review History 向后兼容的发布数据。

先读：

- `docs/KLOSE_VOCABULARY_SYSTEM.md`：完整架构与长期机制；
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
8. 原始 Source 不覆盖；生成文件不作为长期手工维护入口。
9. identity merge/split 是高风险迁移，必须先评估现有 Anki history。
10. 任何架构优化优先保护已有 Anki Review History / FSRS state。
11. 自动结构检查、模型审校、人工确认、教材原文核对必须明确区分，不能互相冒充。
12. 对需求假设保持质疑；发现 Anki 行为、数据或学习机制前提不成立时先验证。

---

## 3. 真源与数据流

内容侧：

```text
Raw Source
→ Source Adapter / Curation
→ Identity Registry + Source Occurrences
→ Vocabulary Master
→ Learner Layer
→ Publish
```

学习侧：Anki 是 `Review History / FSRS state / Due / Interval / Suspended` 的唯一真源；repo 不重建这些状态。

长期统一区：

```text
anki/klose/
├── config/                    # learner/scope config
├── master/                    # NoteID registry / source identity map / release registry / master / occurrences
├── learner/                   # current learner layer + explicit overrides
├── publish/                   # study.csv / all.csv / migration / views
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

---

## 5. Anki 发布契约

长期 Note Type：`Klose Vocabulary`；一个主 Deck：`Klose-English::Vocabulary`。

正式发布字段第一列必须是 `NoteID`。长期重新导入使用同一 Note Type、Update Existing Notes、Match scope = Note Type。

默认入口：

```text
anki/klose/publish/study.csv   # 已释放 Notes，日常推荐导入
anki/klose/publish/all.csv     # 完整库存，不是默认日常入口
```

`release_registry.csv` 是长期增长状态：Note 一旦进入 Anki，原则上持续留在 `study.csv` 以接受后续内容升级。

repo 生成的来源/年级 Tags 属于 system-managed；个人长期备注使用不参与 CSV mapping 的 `UserMemo` 或 Card Flag。

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
tools/check_klose_learner.py
```

本地完整顺序：

```bash
python tools/check_klose_persistent_state.py
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/check_klose_learner.py
```

CI：

```text
.github/workflows/build-anki-rj-start1.yml
.github/workflows/build-klose-vocabulary.yml
```

任何相关修改完成前，都要确认对应 CI 成功，并检查：

```text
anki/klose/master/build_stats.csv
anki/klose/review/identity_review.csv
anki/klose/review/learner_review.csv
anki/klose/review/future_vocab_review.csv
```

---

## 7. 变更流程

### 新增教材/词书

1. 保留 Raw Source；
2. 解析为 source-scoped occurrences；
3. 与 Registry 做 sense-aware candidate matching；
4. 将确认后的 `SourceItemKey → NoteID` 决策写入 committed `source_identity_map.csv`；
5. 明确已有 unit → 原 NoteID + 扩展 provenance；
6. 明确新 unit → 追加新 NoteID，旧 ID 不重排；
7. 模糊项 → review；
8. 生成当前 Learner Layer；
9. 根据带 `released_at` 的 release scope 决定新 Note 是否进入 `study.csv`；
10. 重建并跑 CI。

### 升 Learner Level

只升级 Learner Presentation；NoteID / identity / source facts 不变。重新导入 `study.csv` 更新已有 Notes，不重建 Card。

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
- Grade-4 learner examples 不无意使用同来源明确到后续年级才首次列出的词；
- `study.csv ⊆ all.csv`，publish NoteID 唯一；
- by-source/by-grade 文件只是视图；
- deterministic build；
- 不静默 fallback 到未经审校的成人词典首义。

`0 issues` 只代表对应自动规则未发现问题，不等于全部语义已经教师人工确认。

---

## 9. Working Style

- 开始任务先读本文件和相关 docs，再检查 repo 当前状态；
- 先判断变更属于 Source / Identity / Fact / Learner / Publish / Anki Migration 哪一层；
- 批量处理前先验证样本和边界案例；
- 修改后 re-check 代表性词、全量统计、review queue、CI；
- 能写成脚本/CI 的约束，不只写在 Prompt/文档；
- `AGENTS.md` 只维护项目规则和能力地图，详细机制放 `docs/`。