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

## 4. Current Stage-A checkpoint — ACTIVE SEMANTIC LANES CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1580
Review/blocker surfaces   = 291
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1571
reuse-identity    =   83
held              =  246
split-required    =   45
route-expression  =   83
source-only       =   34
```

与上一 checkpoint（293 blockers / 1578 preview）相比：

```text
5 intended decision refinements
├─ hall     held → keep   = 大厅；礼堂
├─ poor     held → keep   = 贫穷的；贫困的
├─ cannot   held → held   = reclassified to form-policy
├─ heavier  held → held   = reclassified to form-policy
└─ has      held → held   = reclassified to form-policy

blockers 293 → 291
preview  1578 → 1580
keep     1569 → 1571
held      248 → 246
```

三个 held refinement 没有为了减少 blocker 数而强行 release；它们通过新的 DecisionBasis/Rationale 自动进入正确的 `form-policy / policy-review` lane，无需扩张代码 heuristics。

当前 `actionable-semantic = 0`、`semantic-review = 0`，这两个 active semantic lanes 已清空。

---

## 5. Latest batch validation

```text
GitHub Actions run                         = 34133509823   SUCCESS
decision commit                            = ca9978473fce9ae7b68cde98973deff233a51f91
bot-generated data commit                  = ab8211b46681684940c592742ad65f4e93339afc
batch decisions                            = 5 = 2 keep + 3 held refinement
Vocabulary Preview TargetSense complete    = 1580 / 1580
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Independent post-workflow recheck           = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 291 / 291 PASS
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

Independent verification：

- `hall` durable row = reviewed keep-identity，TargetSense `大厅；礼堂`；Preview 已出现 `candidate:hall`；
- `poor` durable row = reviewed keep-identity，TargetSense `贫穷的；贫困的`；Preview 已出现 `candidate:poor`；
- `cannot` / `heavier` / `has` 仍 held，但 Review Bundle 已正确归到 `form-policy / policy-review`；
- `study` 仍 held，`may` 仍 split-required；
- transient `decision_updates.csv` 已删除；
- compare `75855905... → ab8211b...` 只包含 third-party audit/review/staging 六类 derived/content files，没有 Klose Master/Learner/Publish/Anki，也没有额外代码变更。

---

## 6. Throughput architecture v2 — FROZEN

Review Bundle 每个 blocker 一行，提供：

```text
ActionabilityScore
ReviewLane
RecommendedBatchSize
BlockerClass
Current Decision + Definitions
all active occurrences + 同书前后 ±8 words
CandidateCanonical + CanonicalRelation
CanonicalAction / Status / TargetSense / Definitions / OccurrenceCount
PolicyRecommendedAction
DeferReason
```

当前 291 blockers 分类：

```text
abbreviation-policy       = 14
form-policy               = 81
functional-polysemy       = 18
multiword-object-boundary = 39
semantic-cross-source     = 56
semantic-easy             = 34
semantic-hard             = 4
split-resolution          = 45
```

当前 execution lanes：

```text
actionable-semantic           = 0
semantic-review               = 0
source-reconciliation-needed  = 17
policy-executable             = 10
policy-review                 = 83
object-boundary               = 39
deferred-high-ambiguity       = 97
split-resolution              = 45
```

Actionability bands：

```text
80–100 = 2
65–79  = 10
45–64  = 45
0–44   = 234
```

`policy-executable = 10` 但 deterministic proposal engine 输出 0：1 个 grammar-special + 9 个 multi-POS/lexicalization-risk 被 guard 拦截，不能机械 reuse。

`deferred-high-ambiguity = 97` 默认不扫描；只有 source evidence / policy 变化才重新激活。

---

## 7. Representative unresolved boundaries

```text
about      → held / functional polysemy
bright     → held / source evidence insufficient
study      → held / multiple target senses
quarter    → held / cross-source sense evidence insufficient
CD         → held / abbreviation review
cannot     → held / full grammatical form + contraction boundary
heavier    → held / comparative; base heavy not reviewed canonical
has        → held / third-person form; canonical have blocked
were       → held / grammar-special form boundary
sweets     → held / plural noun 糖果 vs sweet adjective/noun
pleased    → held / lexical adjective vs please form
lost       → held / lose form + lexical adjective
cycling    → held / -ing lexicalized-activity boundary
dancing    → held / -ing lexicalized-activity boundary
save       → split-required / 节约资源 vs 救助人
break      → split-required / 物理损坏 vs 课间休息
dish       → split-required / 盘子 vs 菜肴
cut        → split-required / 剪切 vs 伤口
drop       → split-required / 掉落动作 vs 水滴
dream      → split-required / 梦想愿望 vs 睡梦
saw/watch/may/like/square/left/cook/cold → split-required
```

---

## 8. NEXT TASK — SOURCE RECONCILIATION LANE

**当前不要自动启用 `waiyan_start3`。**

下一批：

```text
1. 处理 source-reconciliation-needed = 17。
2. 推荐每批 10–15；先处理 source/gloss conflict 可以靠 current occurrence neighborhood 明确校正的项目。
3. 对真正存在 source conflict / dictionary-noise-vs-source ambiguity 的项，不为降低 blocker 数强行 release；必要时保持 held 或升级 split-required。
4. 每个 batch 只做一次 decision_updates + 一次 fast workflow。
5. core + batch-aware + independent sample/high-risk/diff recheck 全部 PASS 后，立即更新 NEXT.md。
6. 后续再处理 object-boundary / policy-review；deferred-high-ambiguity 默认不扫描。
7. split-resolution = 45 仍独立排队，等待 occurrence-partitioned multiple provisional Stage-A identity 架构。
8. blocker 数量下降不是质量目标。
9. blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 waiyan_start3。
10. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
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
