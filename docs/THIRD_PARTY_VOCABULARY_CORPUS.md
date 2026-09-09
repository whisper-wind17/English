# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的第三方教材 Vocabulary Stage A。目标是把多个教材来源合并为可审计的 learner Identity corpus，同时避免重复审核已经确定的普通词义。

## 1. 核心分层

```text
Raw Source / Textbook Evidence
→ Source Adapter
→ Source Occurrence
→ MatchKey / surface
→ Learner Identity
→ [仅真实多义词] Sense Partition
→ Learner Admission
→ Stage B / Klose reconciliation
```

必须保持：

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
Source Grade ≠ LearnerLevel
```

第三方 source occurrence 只描述教材事实；Identity 描述“学什么”；Learner Admission 描述“Klose 现在是否学”。

## 2. Minimal Learner Identity — FROZEN 2026-09-08

详细合约见：

```text
docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
```

### 2.1 Singleton Identity

一个 MatchKey 只有一条 durable decision 时：

- `Action / CanonicalMatchKey / ObjectType / TargetSense / Status` 是 Identity 内容；
- `OccurrenceKeys` 是当前 provenance/audit snapshot；
- 新增或删除同 MatchKey source occurrence **不使 Identity stale**；
- workflow 自动刷新 singleton `OccurrenceKeys` 到 current occurrence set；
- 不再因为第 7/8 套教材重复出现 `apple` 就重新审核“苹果”。

### 2.2 Multipart Identity

只有教材证据真正证明多个 elementary learner senses 时才 split：

```text
cold#temperature
cold#illness

cook#person
cook#verb
```

Multipart 的 `OccurrenceKeys` 仍是 semantic partition truth：

```text
subsets 必须 non-empty + disjoint
union == current occurrences 才能 release
新增/删除 occurrence 不自动归 sense
partition 不完整 → requeue/blocker
```

## 3. Reopen 条件

普通 singleton 不因 evidence 数变化 reopen。只有以下情况才重审：

- actual textbook evidence 明确出现第二个 learner-relevant sense；
- source reconciliation 发现原 source / edition 判断错误；
- canonical relation 被证明错误；
- Vocabulary / Expression boundary 被证明错误；
- explicit `split-required / held / pending` decision。

Dictionary 多义、POS 数量、第三方 glossary 宽义本身不是 reopen 条件。

## 4. Durable / generated truth

```text
anki/klose/third_party_vocabulary/
├── config/source_adapters.csv
├── review/identity_decisions.csv              # durable Identity truth
├── learner/grammar_form_quarantine.csv        # durable Learner Admission gate
├── staging/occurrences.csv                    # generated Source union
├── staging/surface_candidates.csv             # generated surface state
├── staging/review_queue.csv                   # generated blockers
├── staging/unified_vocabulary_preview.csv     # generated Identity view
├── learner/learner_vocabulary_preview.csv     # generated current learner view
└── audit/stage_a_status.json                  # machine checkpoint
```

关键执行入口：

```text
tools/apply_third_party_identity_decision_updates.py
→ singleton occurrence snapshot auto-rebind
→ multipart partition preserved

tools/build_third_party_corpus.py
tools/check_third_party_corpus.py
tools/build_third_party_learner_view.py
tools/check_third_party_learner_view.py
```

Generated staging / learner view 不得手工编辑。

## 5. Identity action

```text
keep-identity
reuse-identity
route-expression
source-only
split-required
held
pending
```

默认目标不是词典级完整 sense inventory，而是小学 learner 的明确 learning unit。

```text
apple = 苹果
→ 一个 Identity

bank = 银行
bank = 河岸
→ 只有教材真的出现两个 learning unit 时才拆成两个 Identity
```

## 6. Morphology / form

Form 关系优先 canonicalize：

```text
studied → study
carried → carry
dropped → drop#verb
does    → do
better / best → good
```

但 Identity Resolution 与 Learner Admission 分离。Klose 当前 past / past-participle 等 grammar form 继续由：

```text
learner/grammar_form_quarantine.csv
```

控制。

Lexicalized adjective/noun 不得按外观误 gate；homograph 必须 DecisionKey-scoped。

## 7. Vocabulary / Expressions

```text
stable lexical word / phrase / phrasal verb / collocation
→ Vocabulary

contraction / explicit open-slot grammar pattern / communicative formula
→ Expression

one-off tense/event chunk
→ source-only
```

多词本身不是 Expression 判据。

## 8. Source Adapter contract — CHECKPOINTED 2026-09-08

### 8.1 当前启用基线

```text
beijing_start1   =  808 occurrences /  734 MatchKeys / 12 books
beishida_start1  =  925 occurrences /  798 MatchKeys / 12 books
hujiao_start3    = 1111 occurrences / 1067 MatchKeys /  8 books
jijiao_start3    =  605 occurrences /  510 MatchKeys /  8 books
renjiao_start1   =  908 occurrences /  802 MatchKeys / 12 books
renjiao_start3   =  851 occurrences /  818 MatchKeys /  8 books
waiyan_start1    = 1170 occurrences / 1071 MatchKeys / 12 books
waiyan_start3    = 1157 occurrences / 1023 MatchKeys /  8 books
---------------------------------------------------------------
Total            = 7535 source occurrences / 80 books
Corpus surfaces  = 2362 normalized MatchKeys
```

`source_adapters.csv` 中所有 enabled adapter 必须遵守同一 source-only boundary：

```text
Raw XLSX
→ tools/prepare_third_party_<SourceID>.py
→ source_reference/<SourceID>_staging/occurrences.csv
→ tools/check_third_party_<SourceID>.py
→ tools/check_third_party_source_adapters.py
→ generic corpus builder
```

每个 enabled adapter 必须：

- 有独立 `prepare_third_party_<SourceID>.py`；
- 有独立 `check_third_party_<SourceID>.py`；
- 输出统一 occurrence schema；
- `SourceOccurrenceKey` 在 adapter 内和跨 adapter 均唯一；
- Source Adapter 不包含 Klose NoteID matching、Identity decision、Learner Admission 或 release state；
- raw source、adapter tool、config 或任一 enabled `occurrences.csv` 变化都会触发 Stage-A source rebuild；
- 每次 Stage-A workflow 都重新执行 enabled edition-specific validators，再执行全局 closure gate。

北京版旧的 pre-merge candidate/review 文件仅保留作历史审计；当前 Third-party Stage A 和 Stage B 不消费它们。北京版正式 source adapter 输出只有标准 `occurrences.csv`，不再依赖旧的 Klose pre-merge generator。

### 8.2 Source Fact 不得被 adapter 修饰

Adapter 负责忠实保留原始教材表格，不在这一层“纠正”词义。例如当前外研两套 source 各存在 2 条原始空 `Definition`：均为 contraction / expanded-form 邻域中的源表事实。Generic gate 只要求所有 adapter 共有的不变量；是否允许空 gloss 由 edition-specific checker 决定，不能为了统一格式擅自补写释义。

新增教材只输出标准 occurrence；generic corpus builder 负责合并，不复制 edition-specific semantic pipeline。

### 8.3 Source-first execution — FROZEN

当前多 Adapter 建库阶段采用：

```text
Phase A1 — Source Adapter Bulk Ingestion
→ SOURCE FREEZE
→ Phase A2 — Global Identity Closure
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

完整执行规则见：

```text
docs/THIRD_PARTY_SOURCE_FIRST_EXECUTION.md
```

Phase A1 中，每个 Adapter 只要求完成 Source-level Definition of Done：parser、edition-specific checker、global adapter closure、corpus rebuild、Source truth regression check、Klose isolation。**不要求**逐 Adapter 把 semantic review / multipart / audited-defer / orthographic duplicate 清零后才接下一个 Adapter。

只有 Source/Adapter blocker 会阻止继续接入下一个 Adapter。Identity-layer blocker 默认累积到所有计划 Adapter 完成后的 SOURCE FREEZE，再基于最终跨来源 evidence 统一处理。

如果一个看似 semantic 的问题实际暴露 parser/source mapping 错误，则立即升级为 Source blocker，当场修复。

## 9. Stage B boundary

所有计划第三方来源完成前：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run final Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
```

Stage B 同时消费：

```text
Identity Preview
+ Learner-stage view / gate
```

前者解决“是不是同一 learning unit”，后者解决“当前是否适合 Klose 学”。

## 10. Source Truth

```text
Klose 实际教材
> 可确认同 Edition 的官方材料
> Third-party corpus
```

冲突按 `docs/SOURCE_RECONCILIATION.md` 处理。
