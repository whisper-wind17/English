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
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

动态进度/当前计数只以本 `NEXT.md` 为准；`docs/THIRD_PARTY_VOCABULARY_CORPUS.md` 中旧 checkpoint 视为历史记录，不用其数字覆盖 NEXT。

涉及 Klose 实际教材 reconciliation 时再读取 `docs/SOURCE_RECONCILIATION.md`；Expressions 任务读取 `docs/EXPRESSIONS_SYSTEM.md`。不要仅凭聊天历史推测当前状态。

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

GitHub 管 Source / Identity / Learner / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

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

Frozen core flow：

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/occurrences.csv
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv
→ TargetSense gate
→ tools/check_third_party_corpus.py
```

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 与 `audit/review_bundle.csv` 都是 generated/derived views。Reviewed decision 必须显式绑定当前 JSON `OccurrenceKeys`；evidence 变化必须自动 requeue。

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

## 4. Current Stage-A checkpoint — HIGH-THROUGHPUT BLOCKER AUDIT

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

当前验证：

```text
GitHub Actions run                         = 34122486998
latest blocker-audit commit                = c645748cf6f454f462d6413131970664f6960692
bot-generated data commit                  = ac64eec02210b0a8dd004b73fa3c111dea34256a
Vocabulary Preview TargetSense complete    = 1578 / 1578
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Independent post-workflow recheck           = PASS
Decision-only fast path                     = PASS
Source adapters reparsed in latest batch    = NO
Review Bundle generated                     = 314 / 314 blockers
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

Independent post-workflow recheck confirms：

- 25 intended decisions all persisted; 24 `keep-identity` + 1 `reuse-identity`；
- all 25 left `review_queue`；
- `fixed → fix` is a canonical reuse, so it does not create a duplicate Preview identity; `candidate:fix` provenance is now `fix|fixed`；
- representative released rows such as `reading` / `ticket` carry the intended TargetSense；
- known blockers including `study` / `won` remain blocked；
- transient `decision_updates.csv` is absent；
- bot diff contains only third-party audit/review/staging files; no Klose Master/Learner/Publish/Anki changes。

### 累计 blocker audit 进展

Historical A–Z checkpoint：

```text
Vocabulary preview      = 1451
Review/blocker surfaces = 444
route-expression        = 81
split-required          = 39
```

Current：

```text
444 blockers → 314 blockers
1451 preview → 1578 preview
81 Expressions → 83 Expressions
39 split-required → 45 split-required
```

累计 136 次 decision refinement：

```text
130 个 surface 离开 review_queue
  ├─ 127 个净增加 Vocabulary Preview identity
  ├─   2 个 route-expression
  └─   1 个 fixed → fix reuse alias（离开 blocker，但不增加 Preview identity）

6 个 held → split-required
  save / break / dish / cut / drop / dream
  仍作为 blocker 保留
```

blocker 数量下降不是质量目标。

### 最新 high-throughput batch — 25 decisions

```text
fixed   → reuse fix
hide    → 躲藏；隐藏
Italian → 意大利的
lie     → 说谎；撒谎
plus    → 加；加上
pound   → 英镑
reading → 阅读；阅读活动
real    → 真实的；真正的
reply   → 回复；答复
ring    → （电话、铃等）响；铃声
rise    → 升起；上升
row     → 划船
rubber  → 橡胶；橡胶材料
rule    → 规则；规定
running → 跑步；跑步活动
sharp   → 尖的；锋利的
shout   → 喊叫；大声喊
singing → 唱歌；歌唱活动
skip    → 跳；跳绳
stage   → 舞台
stuck   → 卡住的；陷住的
ticket  → 票；票券
tower   → 塔；塔楼
tweet   → 啾啾叫；鸟叫声
upset   → 心烦的；难过的
```

本批不是仅挑 25 个词逐个 lookup；实际先用 Review Bundle 扫描约 50 个低风险 blocker，再一次性提交 25 个证据充分的 refinement。decision-only workflow 正确跳过全部 unchanged Source Adapter parser/validator。

---

## 5. High-throughput operating mode — FROZEN

后续 blocker audit 默认使用：

```text
一次扫描              = 30–50 blockers
目标有效 refinement   = 10–25（证据允许可更高）
一次 decision_updates = 1 batch
一次 workflow          = 1 batch
Completion Recheck     = core + batch-aware + independent sample/diff recheck
批次完成               = 立即更新 NEXT.md，再开始下一批
```

`audit/review_bundle.csv` 每个 blocker 一行，直接提供 Current Decision + Definitions + all active occurrences + 同书前后各 8 个词，避免逐词重复 GitHub evidence lookup。

当前 314 blockers 自动分层：

```text
semantic-easy             = 38
semantic-cross-source     = 62
split-resolution          = 45
semantic-hard             = 4
multiword-object-boundary = 39
form-policy               = 94
abbreviation-policy       = 14
functional-polysemy       = 18
```

默认优先级：semantic-easy → cross-source → split → hard/multiword → form/abbreviation/functional。已确认 policy blocker 不与普通 semantic blocker 混在同一思路里反复研究。

Class-level policies 已冻结在 `docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md`：

```text
Irregular/inflected forms:
  词形本身默认不是新 lexical sense；base 已 reviewed 且 occurrence 同义时可 reuse base；
  canonical 仍 blocked 时 form 不得绕过；显式 pedagogical exception 可保留（如 women）。

-ing / activity:
  透明形态 → form/reuse candidate；
  教材明确作为活动类别独立 headword → 可 keep lexicalized activity；
  hiking / boating / reading / running / singing 属于 evidence-based 个案，不是所有 -ing 自动 keep。

Abbreviation/contraction:
  grammatical contraction 不因缩写本身 mint lexical identity；
  lexical abbreviation 只有 source context 绑定单一学习单元才 keep，否则 held / route-expression。
```

Decision-only CI fast path 已实现：只改 decision 时直接复用 committed adapter occurrences，跳过教材 parser/validator，但仍执行 apply → build → TargetSense gate → core recheck → review bundle → batch recheck → Klose untouched guard。

---

## 6. Representative unresolved boundaries

```text
about      → held / functional polysemy
bright     → held / source evidence insufficient
study      → held / multiple target senses
quarter    → held / cross-source sense evidence insufficient
CD         → held / lexical abbreviation context/policy application pending
won        → held / frozen form policy 尚未应用到该 occurrence/base relation
cycling    → held / -ing policy evidence application pending
dancing    → held / -ing policy evidence application pending
save       → split-required / 节约资源 vs 救助人
break      → split-required / 物理损坏 vs 课间休息
dish       → split-required / 盘子 vs 菜肴
cut        → split-required / 剪切 vs 伤口
drop       → split-required / 掉落动作 vs 水滴
dream      → split-required / 梦想愿望 vs 睡梦
saw        → split-required
watch      → split-required
may        → split-required
like       → split-required
square     → split-required
left       → split-required
cook       → split-required
cold       → split-required
```

注意：form / -ing / abbreviation **policy 已冻结**，但剩余相应 blocker 仍需按 current occurrence + canonical evidence 批量应用 policy；不能仅因 policy 存在就机械全部 release。

---

## 7. NEXT TASK — CONTINUE HIGH-THROUGHPUT AUDIT BEFORE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

```text
1. 从 Review Bundle 继续每批扫描 30–50 个 blocker。
2. 优先处理剩余 38 semantic-easy，再处理 semantic-cross-source。
3. 每批只提交 evidence 足够的 10–25+ refinement；未充分者保持 held。
4. 多义 occurrence 明确时升级 split-required，不强行压成一个 TargetSense。
5. 对 94 form-policy / 14 abbreviation-policy / -ing items 按冻结 policy 做批量 evidence application，不再逐词重新讨论 policy 本身。
6. 每批只跑一次 workflow；decision-only 必须走 fast path。
7. 每批 core + batch-aware + independent Completion Recheck 全部 PASS 后，立即更新 NEXT.md。
8. 不以 blocker 数下降作为质量目标。
9. blocker 质量达到稳定 checkpoint 后，向用户展示结构与代表性边界；用户确认后才考虑启用 waiyan_start3。
10. 仍不 mint Stable ThirdPartyID；所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
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
Vocabulary Preview TargetSense all non-empty
batch intended decisions exactly persisted
keep/reuse/split/route derived state correct
known semantic/morphology/policy blockers preserved unless explicitly changed in batch
transient decision inbox removed
Git diff scope contains only intended third-party layers
Klose Master/Learner/Publish/Anki untouched
```

CI success 不能单独作为“结果正确”；仍需 independent sample + high-risk boundary + diff recheck。

---

## 9. Deferred

```text
waiyan_start3 adapter enablement — wait for blocker audit checkpoint + user review
remaining 314 blockers — continue evidence-driven high-throughput audit
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes British/American IPA completion before admission
Expressions one-month real-learning evaluation
```

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
