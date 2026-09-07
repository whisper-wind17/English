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

## 4. Current Stage-A checkpoint — POLICY REVIEW BATCH 1 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1600
Review/blocker surfaces   = 226
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1591
reuse-identity    =   83
held              =  179
split-required    =   47
route-expression  =  128
source-only       =   34
```

Source reconciliation lane remains closed at `0`.

### Object-boundary active pass

此前两批已关闭：39 个原 object-boundary 中，29 个解除 blocker，10 个明确 `object-boundary-audited-defer`；无新 source evidence 不重复扫描。

### Policy-review batch 1

推荐上限 30 个一次处理：

```text
24 route-expression
├─ contractions / grammar forms:
│  i'm / it's / he's / she's / couldn't / didn't / doesn't / here's / isn't
│  shouldn't / they're / wasn't / weren't / what's / where's / won't / don't
│  you'll / wouldn't / can't / cannot / have got
└─ false abbreviation reactions: hm / mm

6 keep-identity
├─ CD         → 光盘；激光唱片
├─ DVD        → DVD；数字光盘
├─ p.m.       → 下午；午后（p.m.）
├─ make peace → 讲和；和解
├─ stairs     → 楼梯
└─ skating    → 滑冰；溜冰
```

第一次尝试把 `sweets` 作为 lexicalized plural release，被独立 checker 正确拦截：`sweets` 是当前显式 protected form-policy blocker。该尝试未持久化。修正后保留 `sweets=held`，用 source 明确的 `skating` activity noun 替换，并整批重新通过。

结果：

```text
blockers 256 → 226
preview  1594 → 1600
```

---

## 5. Latest batch validation

```text
failed pre-gate attempt commit              = c767cec9981e918a4ce3b5ea1cb637954b2f9d5c
failed run                                  = 34139599060  # blocked by protected sweets invariant; no data persisted
corrected decision commit                   = 9c0f6cac7e754c0c62abdd53bd0fd60e9d265cd7
GitHub Actions run                          = 34139721820   SUCCESS
bot-generated data commit                   = 329cd6bbdf0c1166c3895f891ecf423c1a1405df
batch decisions                             = 30 = 24 route-expression + 6 keep
Vocabulary Preview TargetSense complete     = 1600 / 1600
Third-party core Completion Recheck          = PASS
Audit-batch Completion Recheck               = PASS
Decision-only fast path                      = PASS
Source adapters reparsed                     = NO
Explicit reviewed OccurrenceKeys             = PASS
Changed source evidence requeues decision    = PASS
Canonical blocker bypass                     = NO
Protected form-policy blockers               = PASS
Transient decision inbox                     = removed
Klose Master/Learner/Publish/Anki touched    = NO
Stable ThirdPartyID minted                   = NO
Final Klose diff executed                    = NO
```

The failed first attempt is useful gate evidence: the independent checker caught a semantic-policy regression after build succeeded, demonstrating that script/build success alone does not bypass frozen invariants.

---

## 6. Throughput architecture v2 — CURRENT

Current blockers = 226.

Active scheduling rules：

```text
source-reconciliation-needed  = 0
object-boundary               = 10  # all audited-defer; inactive without new evidence
semantic-review               = 2   # ever/player; audited-defer
policy-executable             = 10  # proposal engine remains guarded; do not mechanically apply
policy-review                 ≈55  # NEXT ACTIVE LANE; batch 1 removed 30
split-resolution              = 47  # separate architecture task
deferred-high-ambiguity       = default skip
```

Exact derived lane/class counts after each workflow should be read from the current generated `review_bundle.csv`; do not infer release decisions from the count alone.

Protected invariants currently enforced by `check_third_party_corpus.py` include：

```text
were / sweets / pleased / lost = held
slept -> sleep reuse
swam  -> swim reuse
won   -> win reuse
```

Do not attempt to reduce blockers by violating these regression guards.

---

## 7. NEXT TASK — CONTINUE HIGH-THROUGHPUT POLICY REVIEW

**当前不要自动启用 `waiyan_start3`。**

下一批继续从 current `policy-review` 派生视图按 policy family 分组：

```text
1. -ing / activity boundary：
   source 明确稳定 activity noun → keep-identity；
   纯透明进行时/动名词 + reviewed canonical same-sense → reuse candidate；
   canonical held/split → 保留 held。
2. irregular plural / pedagogical form：
   只在教材明确作为独立学习单元且符合 frozen exception 时 keep；
   split/semantic canonical 不得绕过。
3. past/comparative/3sg forms：
   canonical reviewed keep + same-sense 才 reuse；
   canonical held/split/missing 保留 held/audited-defer。
4. abbreviation：
   source 明确单一 lexical expansion 才 keep；
   communicative sound/frame route-expression；
   多 expansion 或 evidence 不足保持 held。
5. policy-executable 当前仍受 proposal guard；proposal=0 时不机械处理。
6. 每批目标 25–30；不要退回微批次。
7. 每批仍必须：1 transient inbox + 1 fast workflow + core/batch/independent recheck + 更新 NEXT。
8. blocker 数下降不是质量目标；audited-defer 也是完成的审计结果。
9. split-resolution = 47 等待 occurrence-partitioned provisional identity 架构。
10. blocker quality 稳定后经用户确认才考虑启用 waiyan_start3。
11. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
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
