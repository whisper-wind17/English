# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的统一第三方教材 Vocabulary corpus。目标是把多个第三方小学英语教材词表汇总、按 **learning unit / target sense** 去重，形成独立统一词源；等计划中的第三方来源全部处理完成后，再与 Klose Full Stable Vocabulary Identity 做一次最终差集。

## 1. 两阶段流程

```text
Stage A — 第三方内部
多个第三方教材 Raw Vocabulary
→ 各 Source Adapter 只解析 Source Occurrence
→ 通用 candidate matching
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B — 所有计划第三方来源完成后
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
→ 后续学习管线
```

Stage A 不因为 Klose 当前已有某词而删除第三方 learning unit；Stage B 才执行最终 Klose diff。

## 2. 产品上真正重要的内容

统一第三方词源只关心 learning unit 本身：

```text
CanonicalWord
TargetSense
BritishIPA
AmericanIPA
Meaning
IdentityStatus
```

教材版本、最早年级、覆盖教材数、出现次数、年级分布不参与学习排序、LearnerLevel、Anki Presentation 或是否学习。`SourceID / Book / Grade / Row / SourceOccurrenceKey` 保留在 Source Occurrence 层，仅用于追溯、重建和 source reconciliation。

## 3. Identity 原则

去重单位不是字符串，而是明确的 learning unit / target sense。

```text
apple = 苹果
→ 一个 Identity

bank = 银行
bank = 河岸
→ 两个 Identity

square = 正方形
square = 广场
→ 两个 Identity
```

Morphology、format alias、multiword、punctuation、substring 等都只能产生 candidate signal，不能自动等同 Identity。Vocabulary / Expression / source-only chunk 必须分开，不能因为原始 XLSX 都放在“单词”列里就全部 mint Vocabulary Identity。

## 4. 最简长期实现 — FROZEN

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

物理路径：

```text
anki/klose/third_party_vocabulary/
├── config/source_adapters.csv
├── review/identity_decisions.csv
└── staging/
    ├── occurrences.csv
    ├── surface_candidates.csv
    ├── review_queue.csv
    └── unified_vocabulary_preview.csv
```

每个 Source Adapter 只做 `Raw source → standardized occurrences.csv`；不负责跨教材比较、morphology/sense 决策、对象路由或 Klose diff。不要恢复 edition-specific `audit → apply → recheck` 多层流水线。

## 5. `identity_decisions.csv` 是唯一内容决策真源

核心字段：

```text
DecisionKey
MatchKey
OccurrenceKeys
Action
CanonicalMatchKey
ObjectType
TargetSense
Status
Confidence
DecisionBasis
Rationale
```

`Action`：

```text
keep-identity       # 独立 Vocabulary learning unit
reuse-identity      # canonicalize / alias / form reuse
split-required      # 同 surface 需要 occurrence-level 拆义
held                # 证据或 identity/form policy 不足
route-expression    # Expression 对象
source-only         # 只保留 Source Fact
pending             # 尚未审校 / evidence 已变化需重审
```

内容审校使用 transient inbox：

```text
review/decision_updates.csv
→ tools/apply_third_party_identity_decision_updates.py
→ identity_decisions.csv
→ inbox 删除
```

成功 workflow 后 `review/` 必须重新只剩 durable decision truth；`decision_updates.csv` 不得残留。

## 6. Evidence-aware decision binding

一个 surface 已经 reviewed，不代表未来新增教材出现同一字符串时可以自动沿用旧判断。durable decision 的 `OccurrenceKeys` 必须记录审校时实际覆盖的 SourceOccurrenceKey 集合，并持久化为无歧义 JSON array。

```text
当前 MatchKey occurrence set == reviewed occurrence set
→ decision 有效

新增/变化 Source Occurrence 导致集合不同
→ DecisionAction=pending
→ CandidateSignals += decision-evidence-changed
→ 自动回到 review_queue.csv
→ stale SourceMatchKey 不得进入 preview provenance
```

历史 wildcard / legacy serialization 已完成一次性迁移；当前 durable decisions 不允许长期 wildcard。

## 7. Generated views 与 learner-facing gate

- `surface_candidates.csv`：每个 normalized surface 一行，展示来源聚合、CandidateSignals 和派生 decision；signal 只是证据。
- `review_queue.csv`：纯派生 view，只包含 `pending / held / split-required` 等需处理 surface，不是第二套决策真源。
- `unified_vocabulary_preview.csv`：只包含 evidence 完整、已 reviewed 的 `keep-identity / reuse-identity` Vocabulary candidates；尚未 mint Stable ThirdPartyID。
- Vocabulary Preview 中任何 candidate 的 `TargetSense` 为空，Stage-A workflow 必须失败。不能以 dictionary 第一义项或广义 gloss 自动补空值。

## 8. 新教材标准接入方式

```text
1. 新增 Source Adapter，只输出 occurrences.csv
2. source_adapters.csv 增加 Enabled=yes
3. generic builder 合并
4. 全新 surface 自动 pending
5. 已审 surface 若新增 occurrence evidence，也自动 pending
6. 所有内容判断只写 identity_decisions.csv
7. rebuild
8. TargetSense gate
9. check_third_party_corpus.py 独立 Completion Recheck
```

不复制 builder/checker，不建立 edition-specific semantic pipeline。

## 9. Stage B：最终 Klose diff

只有计划中的第三方教材都完成 Stage A 后才执行：

```text
Third-party Unified Vocabulary
vs
note_registry.csv + note_registry_extensions.csv
```

同一 learning unit 已在 Klose → `existing-in-klose`；Klose 没有该 target sense → `third-party-new`。

Stage B 之前禁止：

```text
- 因 Klose 已存在而删除第三方 Identity
- 把 Klose NoteID 当第三方 corpus Identity
- 把 Stage-A staging 自动写入 Klose Master / Learner / Release / Publish / Anki
```

## 10. Source Truth 边界

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

冲突按 `docs/SOURCE_RECONCILIATION.md` 处理。

## 11. Five-adapter Source closure

当前已启用五个小学 Source Adapter：

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

Source-family boundaries：

- `hujiao_start3` 只纳入沪教版三年级起点 3–6 年级上下册；同目录 7–9 年级牛津英语未纳入；真实源基线 `1111 / 1067` 已冻结。
- `waiyan_start1` 只纳入外研版一年级起点 1–6 年级上下册；外研三年级起点与初高中资料均排除；真实源基线 `1170 / 1071` 已冻结。
- `waiyan_start3` 已完成 Source Inventory，确认是独立完整 8-book family，但尚未启用。

五个 adapter 合计：

```text
Source occurrences  = 4848
Normalized surfaces = 2062
Durable decisions   = 2062
Evidence-changed    = 0
pending             = 0
```

这表示当前 2062 个 surface 都有显式 durable Stage-A decision 并绑定完整 occurrence evidence；不表示 2062 个 surface 都是 Vocabulary。

## 12. A–Z Vocabulary Preview content-quality closure — historical checkpoint

2026-09-07 完成 five-adapter Vocabulary Preview A–Z 内容质量审计，重点检查 TargetSense、canonical/alias 污染、reuse blocker bypass、morphology canonicalization、Vocabulary/Expression routing 和 event chunk。

当时可信 checkpoint：

```text
GitHub Actions run        = 34084215849
content-audit commit      = ba1c0afe5e1107447f46084f9462a3aa554f6374
bot-generated data commit = 8bc04ffa74914e02ecbf453b47cbf93c837acb53

Vocabulary preview      = 1451
Review/blocker surfaces = 444
keep-identity           = 1442
reuse-identity          =   61
held                    =  405
split-required          =   39
route-expression        =   81
source-only             =   34
TargetSense complete    = 1451 / 1451
```

典型 canonicalization / routing：

```text
be afraid of → afraid of
dropped → drop
grapes → grape
happened → happen
stayed at home → stay at home
walking the dog → walk the dog
watering the plants → water the plants
How old ...? → route-expression
climb on the window ledge → source-only
women → 保留独立 pedagogically salient plural-form identity
```

这个 `1451 / 444` 仅是历史 checkpoint，不再是当前 baseline。

## 13. Blocker quality audit — current checkpoint

A–Z closure 后继续对 `held / split-required` 做 context-bound recheck。原则不是追求 blocker 数量下降，而是用 source neighborhood / source glossary 判断是否已经能绑定一个明确的小学 learning unit：

```text
source context 足够明确       → keep-identity + 窄义 TargetSense
同形不同义                   → split-required
功能词/广泛多义               → held
irregular / form-policy 未定   → held
交际句型                      → route-expression
```

从历史 data commit `8bc04ffa74914e02ecbf453b47cbf93c837acb53` 到当前 `fa5e97a47c8a972316723aed58fc1a6aa949e879`，Git compare 显示共有 16 个连续提交，累计重新审定 79 个 blocker：

```text
review_queue        -79
Vocabulary preview  +77
route-expression     +2
```

因此当前可信 baseline：

```text
GitHub Actions run                         = 34100218425
latest blocker-audit commit                = 1b46a6e4fdd66378656ccb303eb05e5b779980a3
bot-generated data commit                  = fa5e97a47c8a972316723aed58fc1a6aa949e879

Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1528
Review/blocker surfaces   = 365
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1519
reuse-identity    =   61
held              =  326
split-required    =   39
route-expression  =   83
source-only       =   34
```

硬门禁与 Completion Recheck：

```text
Vocabulary Preview TargetSense complete = 1528 / 1528
Source occurrence closure               = PASS
Decision / occurrence closure           = PASS
Explicit reviewed OccurrenceKeys        = PASS
Changed source evidence requeues        = PASS
Canonical blocker bypass                = NO
Canonical TargetSense precedence        = PASS
Known semantic blockers preserved       = PASS
Known morphology decisions preserved    = PASS
Transient decision inbox                = removed
Klose Master/Learner/Publish/Anki        = untouched
Stable ThirdPartyID minted               = NO
Final Klose diff executed                = NO
```

代表性被安全释放的 blocker：

```text
blow → 吹；刮
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
cashier → 收银员
cheese → 奶酪；干酪
hot dog → 热狗
lion dance → 舞狮
long ago → 很久以前；从前
```

高风险边界继续保留：

```text
about      = held
study      = held
won        = held / irregular-form policy
saw        = split-required
watch      = split-required
may        = split-required
like       = split-required
square     = split-required
left       = split-required
cook       = split-required
cold       = split-required
```

下一步继续审计当前 365 个 blocker；只有 source evidence 足够时才释放。**暂不自动启用 `waiyan_start3`**。待 blocker 质量形成稳定 checkpoint 并经用户确认后，再决定是否接入 `waiyan_start3`；其接入仍只属于 Stage A。所有计划第三方小学来源完成前不进入 Stage B。
