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

## 4. Current Stage-A content checkpoint — FORM POLICY BATCH CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1578
Review/blocker surfaces   = 293
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1569
reuse-identity    =   83
held              =  248
split-required    =   45
route-expression  =   83
source-only       =   34
```

与上一 checkpoint 相比：

```text
blockers 314 → 293   (-21)
held     269 → 248   (-21)
reuse     62 →  83   (+21)
preview 1578 → 1578  (unchanged)
```

Preview 不增加是正确结果：本批 21 个 surface 全部是现有 reviewed canonical identity 的 form aliases，不应产生新的 provisional Vocabulary identity。

### 最新 content batch — 21 deterministic form reuses

全部 proposal 经 source definition / occurrence neighborhood / canonical current state 复核后确认：

```text
became  → become
brought → bring
came    → come
drew    → draw
forgot  → forget
learnt  → learn
met     → meet
ran     → run
rode    → ride
sent    → send
swam    → swim
taught  → teach
told    → tell
wore    → wear
wrote   → write
ate     → eat
bought  → buy
gave    → give
slept   → sleep
went    → go
won     → win
```

所有 21 个 durable rows 均为：

```text
Action           = reuse-identity
Status           = reviewed
Confidence       = high
OccurrenceKeys   = explicit current JSON array
Canonical        = reviewed keep-identity + non-empty TargetSense
DecisionBasis    = frozen-form-policy-proposal-confirmed
```

受保护的非机械 form boundaries 仍保持 blocker：

```text
were     → held / grammar-special canonical boundary
sweets   → held / plural noun 糖果 vs sweet adjective/noun
pleased  → held / lexical adjective vs please form
lost     → held / lose form + lexical adjective
```

高风险 semantic blockers `study` 仍 held，`may` 仍 split-required；没有被本批误改。

---

## 5. Validation / Completion Recheck

第一次提交 21 decisions 后，workflow run `34132499562` 在 core Completion Recheck 中失败：

```text
Irregular-form blocker lost: slept
```

原因不是 content decision 错误，而是 `tools/check_third_party_corpus.py` 仍保留旧 hardcoded contract，要求 `slept / swam / won` 永久 held，与已经冻结并实现的 form-reuse policy 冲突。

已修正 checker：

```text
slept → sleep / swam → swim / won → win
必须保持 reviewed reuse-identity

were / sweets / pleased / lost
必须继续 held
```

该修改使 regression guard 与冻结 policy 对齐，同时保留对 lexicalized / grammar-special 边界的保护。

最终 authoritative validation：

```text
successful GitHub Actions run               = 34132821989
21-decision commit                          = 8902011e96dabc3e9bde25bbf000191774879ae8
recheck-contract fix commit                 = b408fe56dde2880777c32d48dfca172055f59423
bot-generated data commit                  = 8d03dfddfad3a3fc0e7f1da7d6955bce8edbff9a
Vocabulary Preview TargetSense complete    = 1578 / 1578
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Independent post-workflow recheck           = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 293 / 293 PASS
Policy proposals remaining                  = 0
Source occurrence closure                   = PASS
Explicit reviewed OccurrenceKeys            = PASS
Changed source evidence requeues decision   = PASS
Canonical blocker bypass                    = NO
Canonical TargetSense precedence            = PASS
Transient decision inbox                    = removed
Klose Master/Learner/Publish/Anki touched   = NO
Stable ThirdPartyID minted                  = NO
Final Klose diff executed                   = NO
```

Independent diff recheck from prior checkpoint `a42db5a...` to `8d03dfd...` contains only third-party audit/review/staging files plus `tools/check_third_party_corpus.py`。没有 Klose Master / Learner / Publish / Anki 变化。

`decision_proposals.csv` 现在只有 header：21 条 high-confidence proposal 已全部消费；剩余 10 个 `policy-executable` derived rows 被 proposal engine 主动过滤，其中 1 个 grammar-special + 9 个 multi-POS/lexicalization-risk，不能机械 reuse。

---

## 6. Throughput architecture v2 — FROZEN

### Review Bundle v2

每个 blocker 一行，直接包含：

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

当前 293 blockers 分类：

```text
abbreviation-policy       = 14
form-policy               = 78
functional-polysemy       = 18
multiword-object-boundary = 39
semantic-cross-source     = 59
semantic-easy             = 36
semantic-hard             = 4
split-resolution          = 45
```

当前 lanes：

```text
actionable-semantic           = 2
deferred-high-ambiguity       = 97
object-boundary               = 39
policy-executable             = 10
policy-review                 = 80
semantic-review               = 3
source-reconciliation-needed  = 17
split-resolution              = 45
```

Actionability bands：

```text
80–100 = 2
65–79  = 12
45–64  = 47
0–44   = 232
```

`deferred-high-ambiguity` 默认不再重复扫描，只有 source evidence / policy 变化才重新激活。

### Batch sizes

```text
policy proposal confirmation = 60–100 / scan
actionable-semantic          = 40–60
semantic-review              = 20–40
split-resolution             = 20–30
object-boundary              = 20–30
source-reconciliation        = 10–15
deferred-high-ambiguity      = 0 / default scan
```

每个 independently closed batch：

```text
1 decision_updates.csv
1 workflow
1 core Completion Recheck
1 batch-aware Completion Recheck
1 independent sample/high-risk/diff recheck
完成后立即更新 NEXT.md
```

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
were       → held / grammar-special form boundary
save       → split-required / 节约资源 vs 救助人
break      → split-required / 物理损坏 vs 课间休息
dish       → split-required / 盘子 vs 菜肴
cut        → split-required / 剪切 vs 伤口
drop       → split-required / 掉落动作 vs 水滴
dream      → split-required / 梦想愿望 vs 睡梦
saw/watch/may/like/square/left/cook/cold → split-required
```

---

## 8. NEXT TASK — ACTIVE SEMANTIC LANES; DO NOT ENABLE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

21 条 deterministic proposal 已完成。下一批执行顺序：

```text
1. actionable-semantic (2)
   - cannot
   - heavier
   注意：Actionability 表示“适合快速决策”，不等于应该 release。
   cannot 实际靠近 contraction/form boundary；
   heavier 是 comparative，base heavy 当前不在 reviewed canonical source unit 中。
   如分类不准确，应修正 lane/class，而不是为降低 blocker 数强行 release。

2. semantic-review (3)
   一次读取全部 bundle evidence，批量决策。

3. source-reconciliation-needed (17)
   每批 10–15；先处理 source/gloss 可直接校正的项目。

4. object-boundary / policy-review
   按 evidence 和冻结 policy 批量处理。

5. deferred-high-ambiguity (97)
   默认不扫描。

6. split-resolution (45)
   仍作为独立 architecture task：
   one MatchKey + occurrence-partitioned reviewed decisions
   → multiple provisional Stage-A identities
   当前不为降低 blocker 数强压成单一 TargetSense。
```

每个 batch 完成后必须立即更新 NEXT.md，再开始下一批。

blocker 数量下降不是质量目标。blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 `waiyan_start3`。所有计划第三方小学来源完成前不执行 Stage-B Klose diff。

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
