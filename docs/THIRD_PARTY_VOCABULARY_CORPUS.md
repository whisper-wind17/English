# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的统一第三方教材 Vocabulary corpus。目标是把多个第三方小学英语教材词表汇总、按 **learning unit / target sense** 去重，形成一个独立统一词源；等计划中的第三方来源全部处理完成后，再与 Klose Full Stable Vocabulary Identity 做一次最终差集。

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
→ 后续全部作为 Klose 当前教材之外的新词学习
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

成功 workflow 后 `review/` 必须重新只剩 `identity_decisions.csv`。

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

## 7. Generated views

- `surface_candidates.csv`：每个 normalized surface 一行，展示来源聚合、CandidateSignals 和派生 decision；signal 只是证据。
- `review_queue.csv`：纯派生 view，只包含 `pending / held / split-required` 等需处理 surface，不是第二套决策真源。
- `unified_vocabulary_preview.csv`：只包含 evidence 完整、已 reviewed 的 `keep-identity / reuse-identity` Vocabulary candidates；尚未 mint Stable ThirdPartyID。

## 8. 新教材标准接入方式

```text
1. 新增 Source Adapter，只输出 occurrences.csv
2. source_adapters.csv 增加 Enabled=yes
3. generic builder 合并
4. 全新 surface 自动 pending
5. 已审 surface 若新增 occurrence evidence，也自动 pending
6. 所有内容判断只写 identity_decisions.csv
7. rebuild
8. check_third_party_corpus.py 独立 Completion Recheck
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

## 11. 当前基线 — 2026-09-07 — five-adapter review closure

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
- `waiyan_start3` 已完成 Source Inventory，确认是独立完整 8-book family，但尚未启用；当前先暂停新增 adapter，供用户审视五教材 corpus。

启用 `waiyan_start1` 时，generic builder 识别：

```text
797 previously reviewed surfaces with changed evidence
274 completely new surfaces
= 1071 pending
= Waiyan start1 distinct MatchKeys
```

本轮已完成：

```text
797 existing surfaces → explicit five-adapter evidence revalidation
274 new surfaces       → conservative learning-unit/object/form review
independent content recheck → correction pass
```

独立 content recheck 曾发现并修正几类规则误判：

```text
aah / hey / whoops / sh
→ broad dictionary noise or interjection misrouting
→ corrected to route-expression with learner-relevant meaning

here's / what's / where's / they're / couldn't / ...
→ contractions were incorrectly admitted by dictionary-format heuristics
→ corrected to held form-policy blockers

leaves / sometime / sweets / watches
→ morphology similarity produced unsafe canonicalization
→ corrected to held

of / ever / ticket
→ first dictionary gloss could not safely determine textbook target sense
→ corrected to held
```

最终可信状态来自 GitHub Actions run `34076701208`，generated data commit `aa2dcc0`：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1484
Review/blocker surfaces   = 424
Evidence-changed surfaces = 0
pending                   = 0

Durable decision actions:
keep-identity     = 1470
reuse-identity    =   55
held              =  385
split-required    =   39
route-expression  =   80
source-only       =   33
```

关键解释：

```text
2062 normalized surfaces = 2062 explicit durable decisions
pending = 0
Evidence-changed = 0
```

这表示五个 adapter 的每个当前 surface 都已有显式 Stage-A 决策并绑定完整 current Source Occurrence evidence；不表示 2062 个 surface 都是 Vocabulary Identity。

`unified_vocabulary_preview = 1484` 是当前可进入 Third-party Vocabulary identity preview 的 provisional learning-unit candidates；它仍不是 Stable ThirdPartyID，也尚未与 Klose 做差集。

`review_queue = 424` 现在全部是真实 blocker：

```text
held           = 385
split-required = 39
```

它们保留的原因是 source sense、object boundary、morphology/form policy 或 occurrence-level split 仍需更多证据；不得为了清零而猜测性合并。

代表性边界继续正确：

```text
study      = 学习 / 研究等 semantic collision → held
saw        = see过去式 / 锯子 → split-required
watch      = 手表 / 观看 → split-required
may        = May / modal may → split-required
like       = 喜欢 / 像等 → split-required
square     = 正方形 / 广场 → split-required
left       = 左边 / leave过去式 → split-required
cook       = 烹饪 / 厨师 → split-required
cold       = 寒冷 / 感冒 → split-required
stronger   = reuse-identity → strong
swing      = keep-identity / 秋千
candies    = reuse-identity → candy
goes       = reuse-identity → go
stories    = reuse-identity → story
```

新增明确 Expression routing 示例：

```text
hey
how are you?
nice to meet you.
here you are.
how about ...?
what about ...?
why not?
how much ...?
you're welcome!
happy new year!
excuse me
hurry up
trick or treat
see you!
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master / Learner / Publish / Anki modified = no
```

下一步暂不启用 `waiyan_start3`。先对当前 `unified_vocabulary_preview.csv` / blocker composition 做用户侧审视；确认 corpus 状态与质量符合预期后，再决定继续接入外研三年级起点，仍属于 Stage A。所有计划第三方小学来源完成前不进入 Stage B。
