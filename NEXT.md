# NEXT — Klose Learning

Last updated: 2026-09-07

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary blocker audit 继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/decision_proposals.csv
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

动态进度/当前计数只以本 `NEXT.md` 为准；`docs/THIRD_PARTY_VOCABULARY_CORPUS.md` 中旧 checkpoint 是历史记录。不要仅凭聊天历史推测当前状态。

---

## 1. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Note Type          = Klose Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 identities

Expressions Stable = 66
Grade-4 priority   = 37
Grade-3-only       = 29
Expressions New/day = 2
FSRS               = ON / 90%
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus

```text
Stage A
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit；当前未进入 Stage B。

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv`、`review_bundle.csv`、`decision_proposals.csv` 都是 generated/derived views。Reviewed decision 必须显式绑定当前 JSON `OccurrenceKeys`；evidence 变化必须自动 requeue。

---

## 3. Enabled Source Adapters

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

`waiyan_start3` Source Inventory 已完成，但 **尚未启用**。

---

## 4. Current Stage-A content checkpoint

本轮是 throughput architecture 优化，没有应用新的 durable vocabulary decisions，因此内容 baseline 与上一批一致：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1578
Review/blocker surfaces   = 314
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1569
reuse-identity    =   62
held              =  269
split-required    =   45
route-expression  =   83
source-only       =   34
```

最近一次实际 content audit batch：

```text
GitHub Actions run        = 34122486998
content decision commit   = c645748cf6f454f462d6413131970664f6960692
content data commit       = ac64eec02210b0a8dd004b73fa3c111dea34256a
batch decisions           = 25 = 24 keep + 1 reuse
```

累计从历史 A–Z checkpoint：

```text
444 blockers → 314 blockers
1451 preview → 1578 preview
81 Expressions → 83 Expressions
39 split-required → 45 split-required
```

---

## 5. Throughput architecture v2 — IMPLEMENTED / FROZEN

目标：提高审计吞吐，但不降低 source-evidence / target-sense / identity 边界门槛。

### 5.1 Review Bundle v2

`tools/build_third_party_review_bundle.py` 生成：

```text
anki/klose/third_party_vocabulary/audit/review_bundle.csv
```

每个当前 blocker 一行，包含：

```text
ActionabilityScore
ReviewLane
RecommendedBatchSize
BlockerClass
Current Decision + Definitions
all active occurrences + 同书前后 ±8 words
CandidateCanonical
CanonicalRelation
CanonicalAction / Status / TargetSense / Definitions / OccurrenceCount
PolicyRecommendedAction
DeferReason
```

硬约束：

```text
Review Bundle MatchKey set == review_queue MatchKey set
canonical evidence 必须 directional，不再把 corpus builder 的对称 morphology signal 当作 canonical 方向
bundle 仅用于审计调度，不是 content truth
```

当前 314 blockers 的分类：

```text
abbreviation-policy       = 14
form-policy               = 99
functional-polysemy       = 18
multiword-object-boundary = 39
semantic-cross-source     = 59
semantic-easy             = 36
semantic-hard             = 4
split-resolution          = 45
```

当前 execution lanes：

```text
actionable-semantic           = 2
deferred-high-ambiguity       = 97
object-boundary               = 39
policy-executable             = 31
policy-review                 = 80
semantic-review               = 3
source-reconciliation-needed  = 17
split-resolution              = 45
```

Actionability bands：

```text
80–100 = 23
65–79  = 12
45–64  = 47
0–44   = 232
```

这意味着后续默认不再重复扫描 97 个 `deferred-high-ambiguity`；只有 source evidence / policy 变化才重新激活。

### 5.2 Adaptive batch size

不再所有 blocker 固定一个 batch size：

```text
policy proposal confirmation = 60–100 / scan
actionable-semantic          = 40–60
semantic-review              = 20–40
split-resolution             = 20–30
object-boundary              = 20–30
source-reconciliation        = 10–15
deferred-high-ambiguity      = 0 / default scan
```

每个独立 batch 仍然只允许：

```text
1 decision_updates.csv
1 workflow
1 core Completion Recheck
1 batch-aware Completion Recheck
1 independent sample/high-risk/diff recheck
完成后立即更新 NEXT.md
```

### 5.3 Deterministic policy proposal engine

`tools/propose_third_party_policy_decisions.py` 生成：

```text
anki/klose/third_party_vocabulary/audit/decision_proposals.csv
```

当前生成 **21 条高置信 directional form reuse proposals**。例如：

```text
became → become
brought → bring
came → come
drew → draw
forgot → forget
learnt → learn
met → meet
ran → run
rode → ride
sent → send
swam → swim
taught → teach
told → tell
wore → wear
wrote → write
ate → eat
bought → buy
gave → give
slept → sleep
went → go
won → win
```

Proposal engine 的硬边界：

```text
AutoApply = no
ReviewMode = confirm-or-reject
explicit current OccurrenceKeys required
canonical must be reviewed keep-identity + non-empty TargetSense
canonical relation must be directional and in safe form set
multi-POS / lexicalized-form risk is filtered out
special grammar canonical is forced back to manual review
proposal cannot write identity_decisions.csv / decision_updates.csv
```

Independent quality recheck 曾捕获第一版 proposal 的过宽 canonicalization（例如 `glass → glasses`、`sweets → sweet`、`pleased → please`、部分 -ing form）；已修正。最终 engine 从 31 个 executable candidates 中保留 21 个高置信 proposal，过滤 9 个 multi-POS/lexicalization-risk + 1 个 special grammar canonical。

### 5.4 Decision-only fast path

仅 review/proposal/decision 变化时：

```text
reuse committed adapter occurrences
→ skip all unchanged source parsers/validators
→ apply
→ build corpus
→ TargetSense gate
→ core recheck
→ Review Bundle
→ policy proposals
→ batch-aware recheck
→ Klose untouched guard
```

最终 throughput-v2 validation run 中四套 source parser/validator 均正确 skipped。

---

## 6. Throughput-v2 validation checkpoint

最终验证：

```text
GitHub Actions run                         = 34130291047   SUCCESS
latest throughput code commit             = 4211246cf53f6e4eef53bb9935fd6934980d8b84
bot-generated audit data commit           = 16db0a42279cfb41d5fa11830be5139e98b25fc4
Vocabulary Preview TargetSense complete    = 1578 / 1578
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Independent post-workflow recheck           = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 314 / 314 PASS
Directional canonical evidence              = PASS
Policy proposals                            = 21 high-confidence
Policy proposal AutoApply                   = NO
Source occurrence closure                   = PASS
Explicit reviewed OccurrenceKeys            = PASS
Changed source evidence requeues decision   = PASS
Canonical blocker bypass                    = NO
Transient decision inbox                    = removed
Klose Master/Learner/Publish/Anki touched   = NO
Stable ThirdPartyID minted                  = NO
Final Klose diff executed                   = NO
```

Git compare 从上一个 NEXT checkpoint `03d5078...` 到最终 bot commit `16db0a4...` 只包含：

```text
.github/workflows/prepare-third-party-renjiao-start1.yml
anki/klose/third_party_vocabulary/audit/review_bundle.csv
anki/klose/third_party_vocabulary/audit/decision_proposals.csv
docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
tools/build_third_party_review_bundle.py
tools/propose_third_party_policy_decisions.py
```

没有改变 durable vocabulary decisions，也没有触碰 Klose Master / Learner / Publish / Anki。

---

## 7. Representative unresolved boundaries

```text
about      → held / functional polysemy
bright     → held / source evidence insufficient
study      → held / multiple target senses
quarter    → held / cross-source sense evidence insufficient
CD         → held / abbreviation review
cycling    → held / -ing lexicalized-activity boundary
dancing    → held / -ing lexicalized-activity boundary
sweets     → held / plural noun 糖果 vs canonical sweet adjective，禁止机械 reuse
pleased    → held / lexical adjective vs please form，禁止机械 reuse
lost       → held / inflected lose + lexical adjective，禁止机械 reuse
save       → split-required / 节约资源 vs 救助人
break      → split-required / 物理损坏 vs 课间休息
dish       → split-required / 盘子 vs 菜肴
cut        → split-required / 剪切 vs 伤口
drop       → split-required / 掉落动作 vs 水滴
dream      → split-required / 梦想愿望 vs 睡梦
saw/watch/may/like/square/left/cook/cold → split-required
```

---

## 8. NEXT TASK — USE V2 LANES; DO NOT ENABLE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

执行顺序：

```text
1. 先批量 confirm/reject 当前 21 条 high-confidence policy proposals；
   - 一次读取全部 proposal + occurrence evidence；
   - 只确认 same lexical sense 的 reuse；
   - 一次 decision_updates + 一次 fast workflow。

2. 再处理 active semantic lanes：
   actionable-semantic → semantic-review → source-reconciliation-needed。
   不再默认遍历 deferred-high-ambiguity。

3. policy-review 中的 -ing / plural / multi-POS form 只按 evidence 个案处理；
   不机械 canonicalize。

4. split-resolution = 45 暂时独立排队。
   当前 builder 能表达 split-required，但还未完整 materialize occurrence-partitioned
   multiple provisional Stage-A identities。后续将该能力作为独立 architecture batch：

   one MatchKey
   + occurrence-partitioned reviewed decisions
   → multiple provisional Stage-A identities

   该能力仍不得 mint Stable ThirdPartyID，也不得进入 Stage B。

5. 每个 independently closed batch 后立即更新 NEXT.md。
6. blocker 数量下降不是质量目标。
7. blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 waiyan_start3。
8. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
```

---

## 9. Completion Recheck contract

每批必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Stale SourceMatchKey excluded from preview provenance
review_queue remains pure derived blocker view
Review Bundle closes exactly over current blockers
Policy proposals remain derived-only / AutoApply=no
Vocabulary Preview TargetSense all non-empty
batch intended decisions exactly persisted
known semantic/morphology/policy blockers preserved unless explicitly changed
transient decision inbox removed
Git diff scope contains only intended third-party layers
Klose Master/Learner/Publish/Anki untouched
```

CI/script success 不能单独作为“结果正确”；必须再做 independent sample + high-risk boundary + diff recheck。

---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
