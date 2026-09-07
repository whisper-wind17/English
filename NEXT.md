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

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit；当前仍未进入 Stage B。

Frozen Stage-A flow：

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

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv` 只是 derived blocker view。`OccurrenceKeys` 必须显式绑定当前审校 evidence；evidence 变化必须自动 requeue。Vocabulary Preview 的 TargetSense 不能为空。

---

## 3. Enabled Source Adapters

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

`waiyan_start3` 已完成 Source Inventory，但 **尚未启用**。

---

## 4. Current Stage-A checkpoint — BLOCKER QUALITY AUDIT

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1552
Review/blocker surfaces   = 341
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1543
reuse-identity    =   61
held              =  296
split-required    =   45
route-expression  =   83
source-only       =   34
```

当前验证：

```text
GitHub Actions run                         = 34118265725
latest blocker-audit commit                = f1e010c758670f1b2e6cb128f78531ebc3c5f292
bot-generated data commit                  = 6dbcf9b2f473183c258af560515090ce26f09eb6
Vocabulary Preview TargetSense complete    = 1552 / 1552
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

### 累计 blocker audit 进展

历史 A–Z checkpoint：

```text
Vocabulary preview      = 1451
Review/blocker surfaces = 444
route-expression        = 81
split-required          = 39
```

当前：

```text
444 blockers → 341 blockers
1451 preview → 1552 preview
81 Expressions → 83 Expressions
39 split-required → 45 split-required
```

累计完成 109 次 blocker decision refinement：103 个 blocker 被证据充分地释放/路由出 review_queue（其中 101 个进入 Vocabulary Preview、2 个 route-expression）；6 个 `save / break / dish / cut / drop / dream` 因 source-level 多义证据从普通 held 提升为 `split-required`，仍保留为 blocker。blocker 数量下降不是质量目标。

### 最新独立批次

```text
bump      → held → keep-identity → 碰；撞
fall off  → held → keep-identity → 从……掉下来；跌落
fall over → held → keep-identity → 跌倒；摔倒
```

Source evidence：

```text
bump
- waiyan_start1|g4-upper|r100|bump
- 位于 bike ride / carried / bump / hurt / knee / cut / finger 的连续事故与受伤词汇序列中；可明确绑定物理“碰；撞”动作，肿块/隆起物等名词义不是本 occurrence 的学习单元。

fall off
- waiyan_start1|g4-upper|r094|fall off
- 紧邻 bike ride，且处于同一事故/受伤序列；可绑定“从……掉下来；跌落”的物理 phrasal-verb learning unit，抽象下降/脱离等扩展义不属于本 source occurrence。

fall over
- waiyan_start1|g4-upper|r053|fall over
- 教材连续出现 fell / fall over / hurt，直接锁定物理“跌倒；摔倒”事件；软件故障等扩展义不属于本 source occurrence。
```

本批 workflow 全部 PASS。独立复核确认三条 decision 均以显式 JSON `OccurrenceKeys` 持久化并进入 Preview，三条均已从 `review_queue` 消失；transient `decision_updates.csv` 已删除。Git compare 显示 bot commit 只修改 third-party Stage-A transient inbox、durable decision 与 derived staging 文件，没有触碰 Klose Master / Learner / Publish / Anki。

本批同时复核但继续保留的代表性 blocker：

```text
board     → held / project-meeting neighborhood 仍不足以唯一确定 board 的具体 noun learning unit
central   → held / place-travel neighborhood 仍不足以确定 adjective / named-place fragment / 其他 target use
all right → held / health-state context 有提示，但 lexical chunk vs communicative Expression/object boundary 尚不足以冻结
```

近期已确认的 split-required 边界：

```text
save  → 节约资源 vs 救助人
break → 物理损坏 vs 课间休息
dish  → 盘；盘子 vs 菜肴；一道菜
cut   → 剪；切 vs 伤口；割伤
drop  → 掉落；使掉下 vs 水滴
dream → 梦想；愿望 vs 梦；做梦
```

代表性已释放 learning units：

```text
blow → 吹；刮
attention → 注意；注意力
hiking → 徒步旅行
a bit → 有点儿；稍微
a knife and fork → 一副刀叉
all over the world → 世界各地；遍及全世界
be able to → 能够；可以
be interested in → 对……感兴趣
bench → 长凳
bicycle → 自行车
bike ride → 骑自行车出行；骑车兜风
boating → 划船；划船活动
cashier → 收银员
cheese → 奶酪；干酪
chug → 轧轧声；发出轧轧声
clap → 拍手；鼓掌
clapping game → 拍手游戏
come back → 回来；返回
comic → 漫画；连环漫画
crisp → 薯片；炸薯片
dark → 黑暗的；昏暗的
dry → 干的；干燥的
grab → 抓住；抓取
fast food → 快餐；速食
physical education → 体育；体育课
miaow → 猫叫；猫叫声
bump → 碰；撞
fall off → 从……掉下来；跌落
fall over → 跌倒；摔倒
hot dog → 热狗
lion dance → 舞狮
long ago → 很久以前；从前
```

高风险 blocker 继续保留：

```text
about      → held
bright     → held
study      → held
CD         → held / abbreviation policy
won        → held / irregular-form policy
cycling    → held / gerund-form boundary
dancing    → held / gerund-form boundary
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

---

## 5. NEXT TASK — CONTINUE BLOCKER QUALITY AUDIT BEFORE WAIYAN START3

**当前不要自动启用 `waiyan_start3`。**

```text
1. 继续审计当前 341 个 held/split blocker。
2. 只释放 source neighborhood / glossary 已能明确绑定单一 elementary learning unit 的条目。
3. 若 source occurrences 明确暴露多个真实 learning units，升级为 split-required，不强行释放。
4. 功能词、多义词、同形异义、irregular/form-policy/abbreviation-policy 项继续保守 held/split。
5. 每批 decision update 后运行 workflow + 独立 Completion Recheck。
6. 每个独立闭环批次完成后立即更新 NEXT.md，再开始下一批。
7. 不以 blocker 数量下降作为质量目标。
8. blocker 质量达到稳定 checkpoint 后，向用户展示当前结构与代表性边界。
9. 用户确认后才考虑启用 waiyan_start3；其接入仍只属于 Stage A。
10. 仍不 mint Stable ThirdPartyID。
11. 所有计划第三方小学来源完成前，不执行 Stage-B Klose diff。
```

---

## 6. Completion Recheck contract

每批必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Stale SourceMatchKey excluded from preview provenance
review_queue 纯派生
Vocabulary Preview TargetSense 全部非空
known semantic/morphology/policy blockers preserved
transient decision inbox removed
Klose Master/Learner/Publish/Anki untouched
```

CI / script success 不能单独作为“结果正确”的结论；必须再做独立 Completion Recheck。

---

## 7. Deferred

```text
waiyan_start3 adapter enablement — wait for blocker audit checkpoint + user review
剩余 341 held/split blockers — continue evidence-driven audit
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes British/American IPA completion before admission
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
