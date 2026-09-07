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

动态进度/当前计数只以本 `NEXT.md` 为准；旧 checkpoint 只作历史记录。不要仅凭聊天历史推测当前状态。

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

## 4. Current Stage-A checkpoint — OBJECT BOUNDARY ACTIVE PASS CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1594
Review/blocker surfaces   = 256
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1585
reuse-identity    =   83
held              =  209
split-required    =   47
route-expression  =  104
source-only       =   34
```

Source reconciliation lane remains closed at `0`.

### Object-boundary audit result

Batch 1：25 个一次处理：

```text
19 route-expression
6 keep-identity
blockers 285 → 260
preview  1586 → 1592
```

Residual batch：14 个一次审完：

```text
2 route-expression
├─ all right → 好；没问题；没事
└─ has got   → 有；拥有

2 keep-identity
├─ go out          → 出去；外出
└─ street sweeper  → 扫街车；道路清扫车

10 held / audited-defer
├─ in one hour / get through / keep on / out of / see the world
├─ take away / take down / take off / all over / a lot
└─ 无新 source evidence 时不再重复扫描
```

Residual batch 结果：

```text
blockers       260 → 256
preview        1592 → 1594
object-boundary 14 → 10 derived blockers
```

这 10 个仍会被 heuristic 显示为 `object-boundary`，但 durable decision 已明确 `object-boundary-audited-defer`。调度层应视为 inactive exception，除非 evidence 改变。

---

## 5. Latest batch validation

```text
GitHub Actions run                         = 34139028904   SUCCESS
decision commit                            = 151277258cdc6049bc99f51ba03ca467d7a9ac2b
bot-generated data commit                  = 8a6f95b054b76766f023c1b20f9ec013cb819448
batch decisions                            = 14 = 2 route + 2 keep + 10 held-refinement
Vocabulary Preview TargetSense complete    = 1594 / 1594
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 256 / 256 PASS
Source-reconciliation lane                  = 0
Policy proposals remaining                  = 0
Explicit reviewed OccurrenceKeys            = PASS
Changed source evidence requeues decision   = PASS
Canonical blocker bypass                    = NO
Transient decision inbox                    = removed
Klose Master/Learner/Publish/Anki touched   = NO
Stable ThirdPartyID minted                  = NO
Final Klose diff executed                   = NO
```

Independent diff recheck：checkpoint `18eaf211...` → bot `8a6f95b...` 只变化 third-party audit/review/staging 六个文件；`review_queue -4`，Vocabulary Preview `+2`。无 Klose Master/Learner/Publish/Anki、无 tool/code 修改。

---

## 6. Throughput architecture v2 — CURRENT

当前 256 blockers 分类：

```text
abbreviation-policy       = 14
form-policy               = 81
functional-polysemy       = 18
multiword-object-boundary = 10   # audited-defer exceptions
semantic-cross-source     = 56
semantic-easy             = 28
semantic-hard             =  2
split-resolution          = 47
```

当前 derived execution lanes：

```text
source-reconciliation-needed  = 0
actionable-semantic           = 0
semantic-review               = 2   # ever/player; audited-defer exceptions
policy-executable             = 10  # proposal engine outputs 0
policy-review                 = 85  # NEXT ACTIVE LANE
object-boundary               = 10  # all audited-defer; inactive without new evidence
deferred-high-ambiguity       = 102
split-resolution              = 47
```

Actionability bands：

```text
80–100 =   2
65–79  =  10
45–64  =  47
0–44   = 197
```

`decision_proposals.csv` 当前仍为空；policy proposal 不能机械 AutoApply。

`ever/player` 与 10 个 object-boundary residual 均按 audited-defer 处理；无新 evidence 不重复扫描。`deferred-high-ambiguity` 默认不扫描。

---

## 7. NEXT TASK — HIGH-THROUGHPUT POLICY REVIEW

**当前不要自动启用 `waiyan_start3`。**

下一 active batch = `policy-review = 85`。

处理原则：

```text
1. 先按 policy family 分组，而不是逐词扫描：
   - transparent past / participle forms
   - plural / irregular plural forms
   - third-person forms
   - -ing / lexicalized activity boundary
   - contractions / abbreviations
2. canonical = reviewed keep-identity 且 occurrence same-sense 才可 reuse。
3. canonical held/split/pending 时严禁绕过 blocker。
4. -ing activity noun、plural pedagogical unit、abbreviation expansion 必须保留人工/object evidence 判断。
5. 优先一次处理可共享同一 frozen policy 的大组；不要退回 2–3 个词的微批次。
6. policy-executable = 10 当前 proposal = 0，不脱离 proposal guard 机械处理。
7. 10 个 object-boundary audited-defer、ever/player、deferred-high-ambiguity 默认跳过。
8. split-resolution = 47 等待 occurrence-partitioned multiple provisional Stage-A identity 架构。
9. 每个 batch：1 decision_updates + 1 fast workflow + core/batch/independent recheck；闭环后立即更新 NEXT.md。
10. blocker 数量下降不是质量目标。
11. blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 waiyan_start3。
12. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
```

---

## 8. Completion Recheck contract

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

## 9. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
