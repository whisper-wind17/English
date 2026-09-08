# NEXT — Klose Learning

Last updated: 2026-09-08

## 1. 启动顺序

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
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
→ anki/klose/third_party_vocabulary/learner/learner_vocabulary_preview.csv
```

动态进度只以 repo 当前文件为准。

---

## 2. Klose operational baseline

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

## 3. Current task — Third-party Multi-Edition Vocabulary Corpus / Stage A

```text
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Unified Vocabulary Identity View
→ current Learner Admission gate
→ Klose learner-stage vocabulary view
```

Durable truth 分层：

```text
review/identity_decisions.csv
= Identity content truth

learner/grammar_form_quarantine.csv
= current Klose Learner Admission gate
```

Reviewed Identity decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

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

仍处于 Stage A：不得 mint Stable ThirdPartyID，不得运行 Stage-B Klose diff，不得修改 Klose Master/Learner/Publish/Anki。

---

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #7 CHECKPOINTED

```text
Enabled adapters                   = 6
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2103
Identity-level Vocabulary Preview  = 1015
Review/blocker surfaces            = 952
Evidence-changed surfaces          = 857
Multipart resolved                 = 10
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 1003
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 34
Explicit decision-bound past-form requirements = 13
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1015   (+30)
Learner Preview    979  → 1003   (+24)
Blockers          1010  →  952   (-58)
Evidence-changed   911  →  857   (-54)
Multipart            7  →   10   (+3)
```

Identity / Learner separation 仍是硬边界：被 gate 的 Identity 没有被删除，只是不进入当前 learner-facing view。

---

## 5. Grammar-stage quarantine — FROZEN

Klose 当前尚未系统学习过去式、过去分词/完成时，因此 pure one-word past/past-participle forms 暂不进入 learner vocabulary。

```text
Identity resolved
≠ current Learner Admission
```

不得按字面形态粗暴过滤；lexicalized adjective/noun 保留。Homograph 必须 decision-scoped，例如：

```text
left#direction   → 保留
left#leave-past  → quarantine
saw#tool         → 保留
saw#see-past     → quarantine
```

当前 explicit past-form requirements = 13；新增 `drank → drink#verb` 与 `flew → fly#verb` 已纳入 gate，past-form leak = no。

Machine checker 不得把第三方 dictionary/free-text Definition 当 grammar identity truth。

---

## 6. Completed deterministic policy batches

```text
#2  swam / taught / told / took / went / were / won / wore / wrote / goes
#3  noodles / sweets / thanks / women / sports / found / had / left
#4  lost / made / said / saw / spent / spoke / er / hasn't / children / men
#5  you're / am / can't / cd / dvd / he's / i'm / it / it's / mm / mr / ms
#6  o'clock / pe / physical education / pop / she's / tv / clothes / couldn't / didn't / doesn't
#7  drank / flew / her / here's / isn't / mrs / our / parent
```

关键已冻结判断：

- 过去式 Identity adjudication 与 Learner quarantine 分离；
- `left`、`saw` 使用 occurrence-partitioned homograph split；
- contractions 默认 route-expression；
- `er / mm` 按教材上下文识别为反应/犹豫语气词，第三方缩写释义为 glossary noise；
- `CD / DVD / TV / Mr / Ms / Mrs` 在教材明确绑定小学 lexical concept 时可保留 Vocabulary；
- `PE` 与 `physical education` 是同一 school-subject Identity：full form canonical keep，`PE → physical education` reuse；
- `clothes` 是 lexicalized clothing noun，不是 `cloth` 的普通复数；
- `her` 在 six-source evidence 下出现真实 functional split：
  - `her#possessive` = 她的（形容词性物主代词）
  - `her#object` = 她（宾格）
  两个 partition 对 8 个 current occurrences complete/disjoint cover，不把两个 target senses 合并成一个 Note。

### Latest validation — Batch #7

```text
run 34187602262 / #200 = SUCCESS
batch commit = f8903a36877afc75774396f5a5df025d998c6c06
bot persist  = 6645ebc99a154730480530131d412e7aab7da4ac
```

```text
selected active batch closure              = 100%
Batch decisions                            = 9 rows / 8 MatchKeys
keep-identity                              = 5
reuse-identity                             = 2
route-expression                           = 2
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1015 / 1015
Third-party learner-stage quarantine       = PASS
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
homograph decision-scope gate              = ENFORCED
split occurrence cover                     = COMPLETE / DISJOINT
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

---

## 7. Identity / Learner / Source — HARD INVARIANT

```text
Source Fact
≠ Vocabulary Identity
≠ Learner Admission
≠ Anki learning state
```

Future Stage B 不能直接把 `unified_vocabulary_preview.csv` 当当前学习清单；必须再经过 learner-stage gate。

---

## 8. V4 learner-first Identity policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频 pedagogical form
→ Identity 层可显式 keep，必须有 rationale
→ 是否当前学习由 Learner Admission 独立决定

显式 slot / grammar pattern / communicative formula / contraction
→ route-expression

event / tense-specific source chunk
→ source-only

多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

Lexical abbreviation 只有 source 能绑定明确小学概念时才 keep；若 full form 同时存在且 identity 等价，优先 canonicalize，避免 duplicate Identity。

---

## 9. High-throughput execution mechanism — FROZEN

```text
review_bundle.csv
→ normalize lanes
→ decision proposals
→ deterministic next_batch.json
→ batch_manifest.json + decision_updates.csv
→ manifest closure check
→ apply/build Identity view
→ build/check learner-stage view
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

---

## 10. NEXT TASK — POLICY-REVIEW BATCH #8

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 9
EvidenceWeight    = 54 / 60
ExecutionReady    = true
SelectedMatchKeys =
  shorts
  sometimes
  they're
  wasn't
  weren't
  what's
  where's
  woman
  won't
```

本批重点：

```text
shorts
→ lexicalized plural clothing noun vs morphology

sometimes
→ lexical adverb vs false morphology relation

they're / wasn't / weren't / what's / where's / won't
→ contraction / Expression routing

woman
→ singular lexical identity vs pedagogical irregular plural women
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 9/9 closure，不 cherry-pick。
5. apply + rebuild Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview delta。
8. Klose isolation 必须 PASS。
9. bot persist 后重新 planner；阶段结束更新 NEXT.md。
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
DO NOT admit grammar-quarantined forms into current learner view.
```

---

## 11. Long-term invariants

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
