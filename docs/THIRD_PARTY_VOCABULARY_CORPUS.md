# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose Vocabulary 的统一第三方教材词源。目标不是研究不同教材版本本身，而是把多个第三方小学英语教材词表合并成一个 **sense-aware、去重、可继续增量扩展的新词候选池**。

## 1. 目标

多个教材版本只作为原始输入：

```text
北京版
人教版
沪教版
其他版本
    ↓
统一解析
    ↓
Sense-aware 去重
    ↓
Third-party Unified Vocabulary
    ↓
与 Klose Stable Vocabulary Identity 做差集
    ↓
Third-party New Vocabulary Pool
```

最终真正有学习价值的是：

```text
Third-party New Vocabulary Pool
= 统一第三方 Vocabulary Identity
  - Klose 当前已存在的同一 learning unit / target sense
```

这些剩余 learning units 的产品定义是：**Klose 当前实际教材之外、后续计划学习的新词**。

## 2. 北京版的角色

北京版 1–6 年级当前 staging 是这个统一词源的第一个 seed，不具有长期语义优先级。

后续加入人教版、沪教版或其他版本时，不再维护“北京版主表 + 其他版本附加”的概念，而是统一进入同一个第三方 corpus：

```text
Beijing = Source Adapter / Seed #1
Renjiao = Source Adapter #2
Shanghai = Source Adapter #3
...
```

任何一个第三方版本都不能因为先加入而覆盖其他版本的不同 target sense。

## 3. 什么重要，什么不重要

### 核心业务字段

统一第三方 Vocabulary Identity 只需要围绕 learning unit 本身建模：

```text
ThirdPartyID          # 第三方 corpus 内稳定身份；正式 schema 落地时再确定编号格式
CanonicalWord
MatchKey
SenseLabel
BritishIPA
AmericanIPA
MeaningPrimary
IdentityStatus
```

`MatchKey` 只用于 candidate matching，不等于 Identity。

### 不作为学习决策字段

以下统计不进入学习排序、LearnerLevel、Anki Presentation 或是否学习的决策：

```text
来自哪个教材版本
最早出现年级
多少套教材包含
跨教材/跨册出现次数
主要分布年级
```

这些指标当前没有产品价值，不构建 Coverage / Frequency / GradeSpan 排序体系。

### provenance 仍保留，但仅用于回溯

第三方原始数据的来源信息仍保存在 Source Occurrence / Raw staging 层，用于：

- 数据错误追溯；
- 义项冲突调查；
- Edition / Revision reconciliation；
- 重建统一 corpus。

它们不进入 Klose 正常学习界面，也不决定是否学习。

## 4. 去重单位：learning unit / target sense

禁止按字符串简单去重。

### 同一 surface + 同一 target sense

合并为一个第三方 Identity：

```text
apple = 苹果
```

无论来自多少教材，统一 corpus 只保留一个 learning unit。

### 同一 surface + 不同 target sense

必须保留多个 Identity：

```text
bank = 银行
bank = 河岸

square = 正方形
square = 广场

cook = 烹饪；煮
cook = 厨师
```

### morphology / phrase / punctuation

只产生 candidate，不自动 merge：

```text
sock vs socks
child vs children
fly vs fly a kite
How old ...? vs how old
```

必须按当前 Vocabulary Identity 规则做 sense-aware review。

## 5. 与 Klose 当前词库做差集

统一第三方 corpus 内部去重完成后，再与完整 Klose Stable Identity Registry 比较：

```text
note_registry.csv
+ note_registry_extensions.csv
```

不能只与当前 Released / Unsuspended / Anki active cards 比较。

判定规则：

```text
同一 learning unit / target sense 已存在于 Klose
→ existing-in-klose
→ 不进入 Third-party New Vocabulary Pool

Klose 没有该 learning unit / target sense
→ third-party-new
→ 进入 Third-party New Vocabulary Pool
```

例：

```text
Klose 已有 bank = 银行
第三方还有 bank = 河岸

bank = 银行 → existing-in-klose
bank = 河岸 → third-party-new
```

## 6. 学习语义

`third-party-new` 的含义不是“可有可无的参考词”，而是：

> 当前教材之外，计划让 Klose 后续学习的新 Vocabulary learning unit。

因此长期目标是把所有已经完成 Identity Resolution 的 `third-party-new` 纳入学习。

但为了保护现有 Stable NoteID、Learner Presentation、Review / Release / Anki 历史，仍保持系统层分离：

```text
Third-party New Vocabulary Pool
→ Klose Identity append / reuse decision
→ Learner Presentation
→ explicit Learning Admission
→ Review / Release
→ Anki
```

“全部计划学习”不等于 staging 阶段自动写入当前 Master / Release / Anki。

## 7. 增量加入新教材版本

每加入一个新版本，执行固定流程：

```text
1. parse raw vocabulary occurrences
2. normalize presentation form
3. 与 Third-party Unified Vocabulary 做 candidate matching
4. same sense → reuse third-party identity
5. same surface / different sense → split identity
6. morphology / phrase ambiguity → review
7. genuinely new → append third-party identity
8. 重新计算与 Klose Stable Identity 的差集
9. 更新 Third-party New Vocabulary Pool
```

新增教材不重新编号已有第三方 Identity；真正并入 Klose 时也不重编号已有 Klose NoteID。

## 8. Source Truth 边界

统一第三方 corpus 即使已经充分清洗，仍然是第三方数据，不升级为 Klose 实际教材真源。

优先级继续保持：

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

如果第三方 corpus 与 Klose 实际教材发生冲突，按 `docs/SOURCE_RECONCILIATION.md` 处理，不能反向覆盖实际教材 Source Fact。

## 9. 当前实现状态

当前第一个 seed：

```text
anki/klose/source_reference/beijing_start1_staging/
```

北京版已完成 12 册解析、surface inventory、与 Klose Stable Identity candidate matching、主要高风险 review；当前仍保持：

```text
MergeAuthorized = no
```

下一阶段应把北京版 staging 从“单版本 pre-merge 工作区”演进为这个统一第三方 corpus 的第一个 Source Adapter，然后按同一规则继续加入其他教材版本。
