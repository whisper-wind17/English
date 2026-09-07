# NEXT — Klose Learning

Last updated: 2026-09-08

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

## 4. Current Stage-A checkpoint — POLICY REVIEW BATCH 2 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1615
Review/blocker surfaces   = 207
Evidence-changed surfaces = 0
pending                   = 0
```

Source reconciliation lane remains closed at `0`.

### Object-boundary active pass

39 个原 object-boundary 中，29 个解除 blocker，10 个明确 `object-boundary-audited-defer`；无新 source evidence 不重复扫描。

### Policy-review batch 1

30 个：24 route-expression + 6 keep-identity；结果 `blockers 256 → 226`、`preview 1594 → 1600`。

### Policy-review batch 2

30 个按 form-policy family 处理：

```text
真正解除 blocker = 19
├─ irregular plural / pedagogical unit
├─ stable activity noun / lexicalized -ing
└─ transparent same-sense form reuse where canonical was reviewed keep

audited-defer = 11
└─ canonical held / split / missing，不允许 form 绕过 canonical blocker
```

结果：

```text
blockers 226 → 207
preview  1600 → 1615
```

`decision_proposals.csv` 当前仍只有 header，proposal = 0；因此没有机械执行 `policy-executable`。

---

## 5. Latest batch validation

```text
policy batch 2 decision commit               = 4cf7fc9b45f8e6ae02ea07ef6fabf8c679191865
GitHub Actions run                           = 34140101533   SUCCESS
bot-generated data commit                    = ac155fe97ad9680f9b9376d3e14c0bc76dbf0c5c
batch decisions                              = 30
net blocker release                          = 19
Vocabulary Preview                           = 1615
Review/blocker surfaces                      = 207
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

Protected invariants remain：

```text
were / sweets / pleased / lost = held
slept -> sleep reuse
swam  -> swim reuse
won   -> win reuse
```

---

## 6. Throughput architecture v2 — CURRENT

Current blockers = 207.

Active scheduling rules：

```text
source-reconciliation-needed = 0
object-boundary              = audited-defer set; inactive without new evidence
semantic-review              = ever/player audited-defer plus remaining semantic items
policy-executable            = derived candidates exist, but proposal=0; manual confirmation only
policy-review                = NEXT ACTIVE LANE
split-resolution             = separate architecture task
deferred-high-ambiguity      = default skip
```

Exact lane/class counts以当前 generated `review_bundle.csv` 为准；不要从历史数字推断。

---

## 7. NEXT TASK — CONTINUE HIGH-THROUGHPUT POLICY REVIEW

**当前不要自动启用 `waiyan_start3`。**

下一批：

```text
1. 先人工确认 current policy-executable 中 canonical=reviewed keep 且 occurrence same-sense 的 form reuse；
   proposal=0 表示不能机械 apply，不表示人工确认后禁止 reuse。
2. protected blockers were / sweets / pleased / lost 必须保持 held。
3. 剩余 policy-review 中：
   canonical held/split/missing → audited-defer；
   abbreviation source 单义明确 → keep；
   多 expansion/evidence 不足 → held；
   source 明确是 communicative form → route-expression。
4. 每批目标 25–30；若当前高置信 active set 少于 25，不为凑数跨越语义门槛。
5. 每批仍必须：1 transient inbox + 1 fast workflow + core/batch/independent recheck + 更新 NEXT。
6. blocker 数下降不是质量目标；audited-defer 也是完成的审计结果。
7. split-resolution 等待 occurrence-partitioned provisional identity 架构。
8. blocker quality 稳定后经用户确认才考虑启用 waiyan_start3。
9. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
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
