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

## 4. Current Stage-A checkpoint — POLICY REVIEW BATCH 3 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1615
Review/blocker surfaces   = 200
Evidence-changed surfaces = 0
pending                   = 0
```

Source reconciliation lane remains closed at `0`.

### Completed active passes

```text
object-boundary original 39
├─ released / routed = 29
└─ audited-defer     = 10

policy batch 1 = 30
├─ route-expression = 24
└─ keep-identity     = 6
blockers 256 → 226
preview  1594 → 1600

policy batch 2 = 30
├─ released          = 19
└─ audited-defer     = 11
blockers 226 → 207
preview  1600 → 1615

policy batch 3 = 28
├─ transparent form reuse = 7
└─ held/audited-defer     = 21
blockers 207 → 200
preview  1615 → 1615
```

Batch 3 的 7 个 reuse：

```text
carried -> carry
drove   -> drive
found   -> find
painted -> paint
said    -> say
spent   -> spend
spoke   -> speak
```

这些只是 source-form alias reuse，因此 blocker 减少 7，但不会增加 canonical Preview 行数。

Batch 3 其余 21 个将 canonical split/missing、surface ambiguity、protected exception 固化为明确 audited-defer；无新 evidence 不重复审查。

`decision_proposals.csv` 当前仍为 derived-only；不得机械 AutoApply。

---

## 5. Latest batch validation

```text
policy batch 3 decision commit               = b20bea79f0193f321df7b99c791878102cacdab7
GitHub Actions run                           = 34166009732   SUCCESS
bot-generated data commit                    = 5534e141d94e3d372ab790109c599c1c66026fc7
batch decisions                              = 28
net blocker release                          = 7
Vocabulary Preview                           = 1615
Review/blocker surfaces                      = 200
Third-party core Completion Recheck          = PASS
Audit-batch Completion Recheck               = PASS
Decision-only fast path                      = PASS
Source adapters reparsed                     = NO
Explicit reviewed OccurrenceKeys             = PASS
Changed source evidence requeues decision    = PASS
Canonical blocker bypass                     = NO
Transient decision inbox                     = removed
Independent durable sample                   = PASS
Independent diff-scope recheck               = PASS
Klose Master/Learner/Publish/Anki touched    = NO
Stable ThirdPartyID minted                   = NO
Final Klose diff executed                    = NO
```

Independent sample confirmed：

```text
carried = reuse-identity -> carry
sweets  = held / policy-protected-form-held
```

Protected invariants remain：

```text
were / sweets / pleased / lost = held
slept -> sleep reuse
swam  -> swim reuse
won   -> win reuse
```

---

## 6. Current throughput bottleneck

Current blockers = 200.

After three policy batches：

```text
policy-executable = effectively only protected blockers remain
policy-review     = mostly explicit canonical-blocked / canonical-missing / ambiguity defers
actionable-semantic = limited high-value release set; many rows are already audited-defer
deferred-high-ambiguity = skip without stronger evidence
split-resolution = major unresolved blocker family
```

继续重复扫描 held form / low-evidence semantic rows收益很低。当前真正的架构瓶颈是：

```text
一个 normalized MatchKey
→ 多个 Source Occurrence groups
→ 多个 provisional Stage-A learning identities
```

现有 corpus 必须支持 occurrence-partitioned provisional identity，才能正确解决 `split-required`，而不是把多义 surface 强行 flatten 成一个 Vocabulary identity。

---

## 7. NEXT TASK — OCCURRENCE-PARTITIONED SPLIT ARCHITECTURE

**当前不要自动启用 `waiyan_start3`。**

下一步：

```text
1. 审查 build_third_party_corpus.py / decision update workflow / check_third_party_corpus.py 当前是否已部分支持一个 MatchKey 多 decision rows。
2. 定义最小 split decision schema：
   - 每个 provisional identity 有稳定的 Stage-A scoped key（非 Stable ThirdPartyID）；
   - 每个 identity 绑定互斥、非空 OccurrenceKeys subset；
   - reviewed split groups 对该 MatchKey 的 current occurrences 必须 complete cover；
   - 不允许 occurrence overlap；
   - 每个 group 独立 ObjectType / TargetSense / canonical relation；
   - source evidence 变化后只允许安全 requeue，不静默沿用旧 partition。
3. Preview 必须能一 surface 输出多个 provisional learning-unit rows，同时保留 source provenance。
4. review_queue 对已 complete-partition 的 split surface 必须解除 blocker；partial partition 仍 blocker。
5. checker 增加 partition completeness / disjointness / TargetSense / canonical-integrity / stale-evidence regression guards。
6. transient decision batch workflow 必须支持同 MatchKey 多 rows，不允许覆盖成一行。
7. 架构完成后先选 2–3 个清晰 split surface 做 smoke test，例如：
   - dish = 盘子 / 菜肴
   - cut = 剪/切 / 伤口
   - dream = 梦想 / 睡梦
8. smoke test 完成独立 recheck 后，再按 20–25 split surface / batch 批量处理。
9. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
```

---

## 8. Completion Recheck contract

每批/每次架构修改必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Split occurrence groups disjoint + complete
Partial split remains blocker
Completed split leaves review_queue
Each provisional learning unit has non-empty TargetSense
Stale SourceMatchKey excluded from preview provenance
review_queue remains pure derived blocker view
Review Bundle closes exactly over current blockers
Policy proposals remain derived-only / AutoApply=no
batch intended decisions exactly persisted
known semantic/morphology/policy blockers preserved unless explicitly changed
transient decision inbox removed
Git diff scope contains only intended third-party layers/tools/docs
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
