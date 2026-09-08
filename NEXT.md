# NEXT — Klose Learning

Last updated: 2026-09-08

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary Stage A 继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

动态进度只以 repo 当前文件为准。

---

## 1. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 identities
Expressions Stable = 66
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus / Stage A

```text
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary
```

内容决策真源：

```text
anki/klose/third_party_vocabulary/review/identity_decisions.csv
```

Reviewed decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

Enabled adapters：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
```

`waiyan_start3` 已启用并独立完成 source parse + validation：8 books / 1157 occurrences / 1023 MatchKeys。

---

## 3. Current checkpoint — SIX-ADAPTER / POLICY BATCH #1 CLOSED

当前 corpus：

```text
Enabled adapters          = 6
Source occurrences        = 6005
Normalized surfaces       = 2161
Durable decisions         = 2098
Vocabulary preview        = 985
Review/blocker surfaces   = 1010
Evidence-changed surfaces = 911
Multipart resolved        = 7
```

与 sixth-source expansion 初始 checkpoint 相比：

```text
Review throughput         = 14
Net blocker release       = 14
Blockers                  = 1024 → 1010
Evidence-changed          = 924  → 911
Vocabulary preview        = 984  → 985
Durable decisions         = 2097 → 2098
```

本批 14/14 deterministic closure：

```text
did     → reuse do
ate     → reuse eat
became  → reuse become
bought  → reuse buy
brought → reuse bring
came    → reuse come
drew    → reuse draw
gave    → reuse give
got     → keep learner-first pedagogical form
learnt  → reuse learn
met     → reuse meet
ran     → reuse run
rode    → reuse ride
sent    → reuse send
```

Action count：

```text
reuse-identity = 13
keep-identity  = 1
```

`got` 保留既有 narrow learner-facing identity：

```text
TargetSense = 得到；获得（get 的过去式）
```

新增 Waiyan evidence 同时含“明白”义，但本批不把 broader get semantics 注入该学习单元。

Preview 只增加 1 是正确状态：`got` 独立 keep 立即进入 Preview；其余 13 个 alias 已完成 identity routing，但多数 canonical 自身仍因 sixth-source evidence change 待复审，因此 alias 不得绕过 canonical blocker 提前进入 Preview。

---

## 4. Validation checkpoint

Decision commit：

```text
4a7021e05e9d4948a5283d6a70b394f313dbaf14
review: adjudicate next policy batch
```

Workflow：

```text
run 34181676332 / #190 = SUCCESS
```

机器验证：

```text
planner selected surfaces             = 14
batch touched MatchKeys               = 14
selected active batch closure         = 100%
decision updates applied              = 14
replaced durable decisions            = 13
appended durable decisions            = 1
batch reuse-identity                  = 13
batch keep-identity                   = 1
Third-party Completion Recheck        = PASS
Preview TargetSense                   = 985 / 985
Explicit reviewed OccurrenceKeys      = PASS
Changed source evidence requeue       = PASS
Partial split remains blocker         = PASS
Canonical blocker bypass              = NO
Stable ThirdPartyID minted            = NO
Final Klose diff executed             = NO
Klose Master/Learner/Publish/Anki     = UNTOUCHED
```

Generated Stage-A workspace 已由 bot persist：

```text
be005495ca3f249d7d9838cad1978e2cd1a61024
data: refresh simplified third-party Stage A workspace
```

独立 diff-scope：`f5138d3... → be00549...` 仅修改 third-party decision / audit / staging 派生状态；source adapters、raw/source staging、Klose Master/Learner/Publish/Anki 均未修改。

---

## 5. Source-expansion state-machine hardening — FROZEN

Sixth-source expansion 已验证以下状态：

```text
decision-evidence-changed
→ always active re-review

new pending
→ always schedulable
→ 不得伪装成 deferred

accepted audited-defer + same context
→ zero-scan

accepted audited-defer + changed context
→ active re-review

multipart canonical stale
→ dependent scoped reuse 暂时退出 Preview
→ durable alias decision 保留
→ canonical 复审后再恢复/验证
```

若 scoped reuse 请求的 `#variant` 在已 resolved multipart canonical 中不存在，仍 hard FAIL。

---

## 6. V4 learner-first policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频、直接有 recall value 的 pedagogical form
→ 可显式 keep，必须有 rationale

显式 slot / reusable grammar pattern / communicative formula
→ route-expression

event / tense-specific source chunk
→ source-only

已证明存在多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

Source evidence 变化不能由旧 decision 静默继承；所有 reviewed decision 以 exact current `OccurrenceKeys` 为 validity boundary。

---

## 7. High-throughput execution mechanism — FROZEN

```text
review_bundle.csv
→ normalize lanes
→ decision proposals
→ deterministic next_batch.json
→ batch_manifest.json + decision_updates.csv
→ manifest closure check
→ apply/build
→ core Completion Recheck
→ batch Completion Recheck
→ Klose isolation
→ bot persist
```

硬规则：

```text
ExecutionReady must be true
manifest set == planner selected set
decision_updates MatchKey set == selected set
selected active batch closure = 100%
source mutation 与 decision mutation 不得混合
```

持续区分 `Review throughput` 与 `Net blocker release`。

---

## 8. NEXT TASK — POLICY-REVIEW BATCH #2

当前 deterministic planner：

```text
ReviewLane         = policy-review
SelectedCount      = 10
EvidenceWeight     = 53 / 60
ExecutionReady     = true
SelectedMatchKeys  =
  swam
  taught
  told
  took
  went
  were
  won
  wore
  wrote
  goes
```

下一任务：完整 adjudicate 这 10 个 surface。不得只处理容易项。

执行要求：

```text
1. 读取 current review_bundle.csv / next_batch.json 与 exact source evidence。
2. 不修改 source/raw/parser/config。
3. 精确生成 planner 对应的 batch_manifest.json + decision_updates.csv。
4. manifest / decision_updates / planner MatchKey set 100% 一致。
5. apply 后 rebuild + core Completion Recheck + batch Completion Recheck。
6. 核对 blocker delta、Preview delta、canonical dependency。
7. 重新 normalize/propose/plan。
8. Klose isolation 必须 PASS。
9. 更新 NEXT.md。
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
```

---

## 9. Long-term invariants

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 用于回溯，不等于学习优先级；
- MatchKey / morphology / alias 只做 candidate evidence；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- complete cover 前 partial split 不得 release；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
