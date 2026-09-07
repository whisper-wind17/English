# NEXT — Klose Learning

Last updated: 2026-09-07

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前第三方 Vocabulary corpus 任务继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

涉及 Klose 实际教材 reconciliation 时再读取 `docs/SOURCE_RECONCILIATION.md`；Expressions 任务读取 `docs/EXPRESSIONS_SYSTEM.md`。不要仅凭聊天历史推测当前状态。

---

## 1. Klose operational baseline

Vocabulary：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
Stable Identity Registry = 901 identities
```

Expressions：

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
approved/admitted/release-ready = 66
Anki New/day = 2
FSRS = ON / 90%
```

GitHub 管 Source / Identity / Learner / Release；Anki 是 FSRS / Review History / Due / Interval / Card State 真源。

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

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit；当前仍未进入 Stage B。

Frozen physical architecture：

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/occurrences.csv
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv
→ learner-facing TargetSense gate
→ tools/check_third_party_corpus.py
```

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是 derived blocker view。新增教材导致 occurrence evidence 改变时，旧 decision 必须自动 pending，不能静默继承。

Vocabulary Preview 有硬门禁：任何 provisional Vocabulary candidate 的 `TargetSense` 为空，Stage-A workflow 必须失败。

---

## 3. Enabled Source Adapters — five-adapter closure

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

`waiyan_start3` 已完成 Source Inventory，确认为 3–6 年级上下册独立完整 8-book family，但 **尚未启用**。

---

## 4. Current Stage-A baseline — BLOCKER QUALITY AUDIT CHECKPOINT

当前五-adapter 可信状态：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1532
Review/blocker surfaces   = 361
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1523
reuse-identity    =   61
held              =  322
split-required    =   39
route-expression  =   83
source-only       =   34
```

当前验证：

```text
GitHub Actions run                         = 34103856793
latest blocker-audit commit                = 2a9ec5c61401e5d6896a2cfc5c2d6a8b4abe1a16
bot-generated data commit                  = 10d997360db523e2d742b0a49bac3dd4581bb2c2
Vocabulary Preview TargetSense complete    = 1532 / 1532
Third-party Completion Recheck             = PASS
Independent post-workflow recheck          = PASS
Source occurrence closure                  = PASS
Explicit reviewed OccurrenceKeys           = PASS
Changed source evidence requeues decision  = PASS
Canonical blocker bypass                   = NO
Canonical TargetSense precedence           = PASS
Transient decision inbox                   = removed
Klose Master/Learner/Publish/Anki touched  = NO
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

### 从 A–Z quality closure 到当前 blocker audit 的累计变化

旧 checkpoint `8bc04ffa74914e02ecbf453b47cbf93c837acb53`：

```text
Vocabulary preview      = 1451
Review/blocker surfaces = 444
route-expression        = 81
```

到当前 `10d997360db523e2d742b0a49bac3dd4581bb2c2`，累计重新审定 83 个 blocker：

```text
review_queue            -83
Vocabulary preview      +81
route-expression         +2
```

因此：

```text
444 blockers → 361 blockers
1451 preview → 1532 preview
81 Expressions → 83 Expressions
```

最新独立批次只更新 2 条 decision：

```text
date     → keep-identity → 日期；日子
crossing → keep-identity → 十字路口；交叉路口
```

最新批次的 source-context 依据：

```text
date：北京版一年级起点三上 source neighborhood 为 eleventh / November / right /
      twelfth / December / date / today / thirteenth / seventeenth / eighteenth，
      明确处于月份、序数和日期语境，可绑定 calendar-date learning unit。

crossing：人教版三年级起点六上 source neighborhood 为 museum / post office / bookstore /
          cinema / hospital / crossing / turn / left / straight / right，
          明确处于地点与问路语境，可绑定 road-intersection noun，而不是 cross 的 -ing form。
```

Completion Recheck：workflow 中 TargetSense gate、独立 Third-party Completion Recheck、Klose publishing untouched assertion 均 PASS；Git compare 显示 bot commit 只修改 `anki/klose/third_party_vocabulary/` 下的 durable decision 与 derived staging 文件，并删除 transient inbox。Preview 已确认包含 `date` 与 `crossing` 的新 TargetSense；`study` 仍 held，`won` 仍 held，`saw` 仍 split-required。第二批筛查中 `American / Australian / Canadian / British / all right / central / diamond / dark` 因义项、词性或 source boundary 仍不足，继续保守 held。

代表性已释放 learning units：

```text
blow → 吹；刮
blow off → 吹掉；刮掉
land → 陆地；土地
smoke → 烟；冒烟
tape → 胶带
attention → 注意；注意力
jam → 果酱
flute → 长笛
hiking → 徒步旅行
a bit → 有点儿；稍微
a knife and fork → 一副刀叉
all over the world → 世界各地；遍及全世界
at first → 起初；一开始
at the same time → 同时；与此同时
be able to → 能够；可以
be interested in → 对……感兴趣
bench → 长凳
bicycle → 自行车
bike ride → 骑自行车出行；骑车兜风
cashier → 收银员
cheese → 奶酪；干酪
hot dog → 热狗
lion dance → 舞狮
long ago → 很久以前；从前
date → 日期；日子
crossing → 十字路口；交叉路口
```

高风险 blocker 继续保留，不因“压数量”而释放：

```text
about      → held
study      → held
won        → held / irregular-form policy
saw        → split-required
watch      → split-required
may        → split-required
like       → split-required
square     → split-required
left       → split-required
cook       → split-required
cold       → split-required
```

---

## 5. NEXT TASK — CONTINUE BLOCKER QUALITY AUDIT BEFORE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

下一步：

```text
1. 继续审计当前 361 个 held/split blocker；
2. 只释放 source neighborhood / glossary 已能明确绑定单一 elementary learning unit 的条目；
3. 功能词、多义词、同形异义、irregular/form-policy 项继续保守 held/split；
4. 每批 decision update 后必须运行 workflow + 独立 Completion Recheck；
5. 每个独立闭环批次完成后立即更新 NEXT.md，再开始下一批；
6. 不以 blocker 数量下降作为质量目标；
7. blocker 质量达到稳定 checkpoint 后，向用户展示当前结构与代表性边界；
8. 用户确认后，才考虑启用 waiyan_start3；
9. waiyan_start3 接入仍只做 Stage A；
10. 仍不 mint Stable ThirdPartyID；
11. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
```

---

## 6. Completion Recheck contract

每个 adapter 接入或每批 decision update 后必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Stale SourceMatchKey excluded from preview provenance
review_queue 纯派生
Vocabulary Preview TargetSense 全部非空
known semantic/morphology blockers preserved
simplified physical layout
legacy multi-pass tools absent
transient decision inbox removed
Klose Master/Learner/Publish/Anki untouched
```

CI / script success 不能单独作为“结果正确”的结论；必须再做独立 Completion Recheck。若单批 update 数量与最终 count delta 不一致，必须先用 Git compare 解释历史累计变更，再接受新 baseline。

---

## 7. Deferred

```text
waiyan_start3 adapter enablement — wait for blocker audit checkpoint + user review
剩余 361 held/split blockers — continue evidence-driven audit; true blockers remain deferred
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（admission 前）
Expressions one-month real-learning evaluation
```

---

## 8. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
