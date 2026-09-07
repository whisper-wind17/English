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

## 4. Current Stage-A checkpoint — SOURCE RECONCILIATION LANE CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1586
Review/blocker surfaces   = 285
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1577
reuse-identity    =   83
held              =  238
split-required    =   47
route-expression  =   83
source-only       =   34
```

本批处理原 `source-reconciliation-needed = 17`：

```text
6 keep-identity
├─ maybe     → 也许；可能；大概
├─ parrot    → 鹦鹉
├─ surprise  → 惊喜；惊讶
├─ tomb      → 坟墓；陵墓
├─ true      → 真实的；正确的
└─ tunnel    → 隧道

2 held → split-required
├─ past   → 方向“经过” vs 时间“……过”
└─ point  → point to 动作 vs 分数/数值 point

9 held refinements
├─ won't / don't → frozen contraction policy
├─ Australian    → nationality POS boundary
└─ ever / player / coin / line / matter / report
   → current source neighborhood insufficient; do not force release
```

结果：

```text
blockers 291 → 285
preview  1580 → 1586
keep     1571 → 1577
held      246 → 238
split      45 → 47
source-reconciliation-needed 17 → 0
```

blocker 数下降不是质量目标；9 个 held refinement 只改善分类/审计状态，不靠强行 release 降数量。

---

## 5. Latest batch validation

```text
GitHub Actions run                         = 34134125248   SUCCESS
decision commit                            = 487ed5bbe3d469d63ec0d10917d178b7d59d00ce
bot-generated data commit                  = 6307238
batch decisions                            = 17 = 6 keep + 9 held + 2 split
Vocabulary Preview TargetSense complete    = 1586 / 1586
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Independent post-workflow recheck           = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 285 / 285 PASS
Source-reconciliation lane                  = 0
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

- `maybe / parrot / surprise / tomb / true / tunnel` 均已进入 Preview，TargetSense 与本批 decision 一致；
- `past / point` 均为 `split-required`，没有泄漏进 Preview；
- `study` 仍 held，`may` 仍 split-required；
- `decision_updates.csv` 已删除；
- compare 本批前 checkpoint `28df4379...` → bot `6307238...` 只变化 third-party audit/review/staging 六个文件，无 Klose Master/Learner/Publish/Anki、无 tool/code 修改。

注意：`ever` 与 `player` 已完成一次 source audit 并明确应 defer，但当前 score heuristic 仍将它们显示为 `semantic-review`；没有新 source evidence 时 **不要再次扫描这两个词**。这是 derived triage 的已知轻微欠拟合，不改变 durable decision truth。

---

## 6. Throughput architecture v2 — FROZEN

当前 285 blockers 分类：

```text
abbreviation-policy       = 14
form-policy               = 81
functional-polysemy       = 18
multiword-object-boundary = 39
semantic-cross-source     = 56
semantic-easy             = 28
semantic-hard             = 2
split-resolution          = 47
```

当前 execution lanes：

```text
source-reconciliation-needed  = 0
actionable-semantic           = 0
semantic-review               = 2   # ever/player; audited-defer exceptions
policy-executable             = 10  # proposal engine outputs 0
policy-review                 = 85
object-boundary               = 39
deferred-high-ambiguity       = 102
split-resolution              = 47
```

Actionability bands：

```text
80–100 = 2
65–79  = 10
45–64  = 47
0–44   = 226
```

`policy-executable = 10` 仍全部被 proposal guard 拦截：1 grammar-special + 9 multi-POS/lexicalization-risk，不能机械 reuse。

`deferred-high-ambiguity` 默认不扫描；`ever/player` 也按人工 audited-defer 处理，除非 evidence 改变。

---

## 7. Representative unresolved boundaries

```text
about      → held / functional polysemy
bright     → held / insufficient context
study      → held / multiple target senses
quarter    → held / sense evidence insufficient
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
past       → split-required / direction vs clock-time
point      → split-required / point-to vs numeric/score
save       → split-required / 节约资源 vs 救助人
break      → split-required / 物理损坏 vs 课间休息
dish       → split-required / 盘子 vs 菜肴
cut        → split-required / 剪切 vs 伤口
drop       → split-required / 掉落动作 vs 水滴
dream      → split-required / 梦想愿望 vs 睡梦
saw/watch/may/like/square/left/cook/cold → split-required
```

---

## 8. NEXT TASK — OBJECT / POLICY BOUNDARIES BEFORE SPLIT ARCHITECTURE

**当前不要自动启用 `waiyan_start3`。**

下一阶段：

```text
1. 不再扫描 source-reconciliation（已清零）。
2. ever/player 虽显示 semantic-review，但已人工 defer；无新 evidence 不重复处理。
3. 下一 active batch 优先 `object-boundary = 39`：每批 20–25，区分 Vocabulary / Expression / source-only / held。
4. 之后处理 `policy-review = 85`，按 frozen form/-ing/abbreviation policy 批量 evidence application；不要机械 reuse。
5. `policy-executable = 10` 不直接处理，除非 proposal guard 条件变化；当前 proposal = 0。
6. `deferred-high-ambiguity = 102` 默认不扫描。
7. `split-resolution = 47` 仍独立排队，等待 occurrence-partitioned multiple provisional Stage-A identity 架构，不把多义词压成单一 TargetSense。
8. 每个 batch：1 decision_updates + 1 fast workflow + core/batch/independent recheck；闭环后立即更新 NEXT.md。
9. blocker 数量下降不是质量目标。
10. blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 waiyan_start3。
11. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
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
