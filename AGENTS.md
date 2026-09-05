# AGENTS.md

## 1. Mission & Startup

本仓库长期维护 **Klose 英语学习系统**：多来源 Vocabulary Knowledge Base、Learner Presentation、Expressions Source Facts，以及与 Anki FSRS/Review History 向后兼容的发布链。

任何涉及 Klose 的教材、词汇、Expressions、Anki 或 repo 数据修改，先按顺序读取：

1. 根目录 `NEXT.md`：当前状态、blocker、下一步；
2. `docs/KLOSE_VOCABULARY_SYSTEM.md`：长期架构；
3. 当前任务对应 SOP；
4. 相关 `anki/klose/` 数据和代码。

常用 SOP：

```text
docs/SOURCE_RECONCILIATION.md    # 实际教材 vs Source Adapter 冲突
docs/EXPRESSIONS_SYSTEM.md       # Useful Expressions / Pattern
docs/ANKI_SYNC_WORKFLOW.md       # 首次导入后的长期同步
docs/ANKI_FIRST_IMPORT.md        # 首次导入契约
docs/ANKI_FIRST_IMPORT_GUIDE.md  # 2026-09-05 首次导入实操记录
docs/LEARNER_REVIEW_REGISTRY.md  # Learner review / fingerprint
docs/ANKI_MIGRATION.md           # Word-first → NoteID-first
```

不要仅凭旧聊天、模型记忆或历史 baseline 推测当前状态。动态状态以 `NEXT.md` 为准。

---

## 2. 不可破坏的规则

1. **Stable NoteID 最高优先级。** 已分配 ID 不得因排序、重建、教材增加或内容修改而重编号、复用或漂移。
2. NoteID 必须来自 committed Registry；Registry / Source Identity Map / Release Registry 缺失时失败，禁止静默重建。
3. **一个 Vocabulary Note = 一个明确 learning unit / target sense，不等于一个 surface string。** 同形异义允许多个 NoteID。
4. `CanonicalWord / MatchKey / substring / morphology` 只用于 candidate matching；词性、义项、大小写、短语边界有歧义时必须 review，禁止静默 merge。
5. 同一已学 learning unit 不创建第二套 FSRS 记忆状态；新增来源优先扩展 provenance。
6. **Source Grade 与 LearnerLevel 完全独立。** Source Grade 描述教材事实；LearnerLevel 描述 Klose 今天怎么学。Klose 可以在 `LearnerLevel=4` 下学习 Grade 5/6 来源词汇。
7. 学习范围必须按 source-scoped occurrence / release 判断，不得用全局 FirstGrade 推导。
8. **Learner Review 按 `LearnerProfile + LearnerLevel + NoteID` 隔离。** ContentFingerprint 变化后旧 approval 必须失效。
9. 原始 Source 不覆盖；generated output 不作为手工维护入口。
10. **禁止手工编辑 `publish/study.csv` 和 `publish/anki-import.csv`。** 修正必须发生在 Source / Identity / Fact / Learner / Release 上游层。
11. identity merge/split 是高风险 migration；先评估现有 Anki history，再显式处理。
12. GitHub 是 Source / Identity / Learner Presentation / Release 的真源；Anki 是 Review History / FSRS / Due / Interval / Learning state 的真源。
13. **正式 Anki 同步只使用 `publish/anki-import.csv`。** `study.csv` 是 generated internal released snapshot，不直接导入。
14. 当前 Vocabulary Note Type 只保留一个 `Recognition` Card Type：**1 Note = 1 Card**。
15. Suspend 只用于尚未学习的 New Cards 准入控制；已进入 Learning/Review 的旧卡不能因 source scope 变化重新 Suspend。
16. 自动检查、模型审校、人工确认、教材原文核对必须区分；`queue=0` 不等于内容已由人工验证。
17. `approve_klose_learner_review.py` 只能在真实逐条审校后显式执行，approval manifest 不得覆盖旧批次。
18. Release readiness 必须在发布之前通过，禁止先 commit/push generated release 再校验。

---

## 3. Source / Edition / Actual Textbook

现有第三方 XLSX 是 Source Adapter 输入，不自动等于 Klose 实际教材真相。

如果 Klose 手中教材与 repo Source 冲突：

```text
实际教材证据
→ source_reference capture
→ Edition / Revision 判断
→ 三方 reconciliation
   actual textbook vs source occurrences vs Master/Identity
→ sense-aware identity decision
→ rebuild / review / release gate
```

Klose 实际使用教材是当前学习场景的高优先级证据。若冲突来自不同 Edition / Revision，应显式建模版本，而不是把两个版本静默混入同一 `SourceBook`。

详细流程：`docs/SOURCE_RECONCILIATION.md`。

---

## 4. Vocabulary / Expressions 边界

Vocabulary：

```text
word / phrase / target sense
```

Expressions：

```text
raw textbook expression
→ reusable pattern candidate
→ optional released expression
```

Useful Expressions 原文是 Source Fact，但**一条原句不等于一张 Anki Card**。完整表达法不得塞进 `Klose Vocabulary` 破坏 Vocabulary Identity。

Expression 中出现但未列入 Core Vocabulary 的词可以作为 Context Vocabulary 证据，但不能自动升级为 Core Vocabulary 或自动 release。

详细规则：`docs/EXPRESSIONS_SYSTEM.md`。

---

## 5. 核心数据流

```text
Raw Source / Actual Textbook Reference
→ Source Adapter / Reconciliation / Curation
→ Identity Registry + Source Identity Map + Source Occurrences
→ Vocabulary Master
→ Learner Layer + Learner Review Registry
→ Release Registry
→ study.csv            # generated internal snapshot
→ anki-import.csv      # generated formal Anki artifact
→ Release Gate
→ Anki
```

长期数据区：

```text
anki/klose/
├── config/
├── master/             # NoteID / source identity / release registries
├── learner/            # current presentation / review registry / approvals
├── source_reference/   # Klose 实际教材证据与 reconciliation input
├── anki/               # Note/Card template contract
├── publish/            # generated outputs
└── review/             # identity / learner / future queues
```

当前 Source Adapter：

```text
anki/人教版一年级起点/
SourceID = rj_start1
```

在 Edition 问题解决前，不假定一个 `SourceID + SourceBook` 就唯一对应 Klose 手中教材版本。

---

## 6. Anki 发布契约

主 Deck：

```text
Klose-English::Vocabulary
```

Note Type：

```text
Klose Vocabulary
```

正式 Note 第一字段固定为 `NoteID`。长期重新导入：

```text
Existing notes = Update
Match scope    = Note Type
```

发布文件：

```text
anki/klose/publish/study.csv       # generated；内部审计快照
anki/klose/publish/anki-import.csv # generated；唯一正式 Anki 导入文件
anki/klose/publish/all.csv         # generated；完整库存
```

固定发布链：

```text
修改上游
→ rebuild
→ sync learner review registry
→ 审校 / approval
→ release gate
→ anki-import.csv
→ 同一 Note Type 原地更新
```

Card contract 在：

```text
anki/klose/anki/
```

当前正面只显示 `Word`；答案面含 Word TTS、UK/US IPA、Meaning、Example、Translation。Card Template 变化不改变 Vocabulary Identity。

---

## 7. 变更流程

### 新增/修正教材

1. 保存 Raw Source / actual-textbook reference；
2. 明确 SourceID 与 Edition/Revision；
3. 解析 source-scoped occurrences；
4. sense-aware candidate matching；
5. 确认 `SourceItemKey → NoteID` 并持久化；
6. 同一 learning unit → 复用 NoteID + 扩展 provenance；
7. 新 learning unit → append NoteID；
8. 歧义 → review，不自动 merge；
9. 生成当前 LearnerLevel presentation；
10. review / fingerprint / approval；
11. 根据显式 release scope 决定是否进入 Anki；
12. rebuild + release gate；
13. 用户侧只重新导入最新版 `anki-import.csv`。

### 升 LearnerLevel

只升级 Learner Presentation；NoteID / Source Facts / Anki Review History 不变。新 level review 默认 `pending`，不能继承旧 level approval。

### 修正 identity

merge/split 单独设计 migration。尤其已发布/已学习 Note，不得作为普通数据清洗删除重建。

---

## 8. Quality Gates

至少检查：

- Registry / Source Identity Map / Release Registry 一致；
- NoteID 唯一稳定；
- source provenance 可追溯且 Edition 不混淆；
- identity 歧义已显式处理；
- released Notes 的 current LearnerLevel 内容完整；
- review status 与当前 ContentFingerprint 匹配；
- `pending=0` 才能描述为 ready；
- `study.csv` 与 Released Set 一致；
- `anki-import.csv` 与 `study.csv` 数据一致、UTF-8 无 BOM、file headers 正确；
- 每个 released Note 恰好一个当前 staging tag；
- deterministic build；
- CI / release readiness 成功。

当前执行入口：

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
tools/approve_klose_learner_review.py  # explicit only
```

---

## 9. Working Style

- 开始任务先读 `NEXT.md` 和相关 SOP；
- 先判断变更属于 Source / Edition / Identity / Fact / Learner / Expression / Review / Release / Publish / Anki 哪一层；
- 批量处理前先验证样本和边界案例；
- 修改后 re-check 代表性项、全量统计、review queue、fingerprint、release readiness 和 CI；
- 能写成脚本/CI 的约束，不只写在 Prompt；
- `AGENTS.md` 只维护项目规则和能力地图，详细机制放 `docs/`；
- 较大阶段结束或切换对话前更新根目录 `NEXT.md`。
