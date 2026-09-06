# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose Vocabulary 的统一第三方教材词源。目标不是研究不同教材版本本身，而是把多个第三方小学英语教材词表合并成一个 **sense-aware、去重、可继续增量扩展的统一 Vocabulary corpus**；只有在所有第三方来源处理完成后，才与 Klose Stable Vocabulary Identity 做最终差集，得到真正的新词学习池。

## 1. 目标与两阶段去重

长期流程固定为两阶段：

```text
阶段 A：第三方 corpus 内部去重

北京版
人教版
沪教版
其他版本
    ↓
各版本 Source Adapter
    ↓
统一解析 / normalize
    ↓
sense-aware Identity Resolution
    ↓
Third-party Unified Vocabulary

阶段 B：全部第三方来源完成后，才与 Klose 做最终去重

Third-party Unified Vocabulary
    ↓
vs Klose Full Stable Vocabulary Identity Registry
    ↓
Third-party New Vocabulary Pool
```

核心公式：

```text
Third-party New Vocabulary Pool
= 完整 Third-party Unified Vocabulary
  - Klose 已存在的同一 learning unit / target sense
```

这些剩余 learning units 的产品定义是：**Klose 当前实际教材之外、后续计划学习的新词**。

## 2. 为什么必须分成两阶段

构建第三方 corpus 时，不因为 Klose 当前是否已有某个词而删除第三方 Identity。

例如第二个教材加入时，只回答：

```text
它与当前 Third-party Unified Vocabulary
是否是同一 learning unit / target sense？
```

而不是同时回答：

```text
Klose 现在是否已经学过它？
```

这样可以避免：

- 第三方来源的加入顺序影响最终 corpus；
- 某个 surface 因为与 Klose 暂时匹配而过早被过滤，后续才发现其实是不同 target sense；
- Klose 当前 Stable Registry 的演进反向污染第三方 corpus；
- 每加入一个教材版本都重复执行一遍 Klose reconciliation。

因此在所有第三方教材完成前，与 Klose 的匹配只能作为 diagnostic / candidate 信息存在，**不能据此从第三方 corpus 删除 Identity，也不能生成最终 New Vocabulary Pool**。

## 3. 北京版的角色

北京版 1–6 年级当前 staging 是这个统一词源的第一个 seed，不具有长期语义优先级。

后续加入人教版、沪教版或其他版本时，不再维护“北京版主表 + 其他版本附加”的概念，而是统一进入同一个第三方 corpus：

```text
Beijing = Source Adapter / Seed #1
Renjiao = Source Adapter #2
Shanghai = Source Adapter #3
...
```

任何一个第三方版本都不能因为先加入而覆盖其他版本的不同 target sense。

## 4. 什么重要，什么不重要

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

## 5. 去重单位：learning unit / target sense

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

## 6. 阶段 A：增量构建完整第三方 corpus

每加入一个新教材版本，只执行第三方内部 Identity Resolution：

```text
1. parse raw vocabulary occurrences
2. normalize presentation form
3. 与 Third-party Unified Vocabulary 做 candidate matching
4. same sense → reuse third-party identity
5. same surface / different sense → split identity
6. morphology / phrase ambiguity → review
7. genuinely new → append third-party identity
8. rebuild Third-party Unified Vocabulary
```

阶段 A 明确禁止：

```text
- 因 Klose 已存在而删除第三方 Identity
- 把 Klose NoteID 当第三方 corpus 的 Identity
- 每加入一个版本就生成最终 Third-party New Vocabulary Pool
- 把 staging 自动写入 Klose learner / release / publish / Anki
```

新增教材不重新编号已有第三方 Identity。

## 7. 阶段 B：全部第三方完成后，与 Klose 做最终差集

只有当计划纳入的第三方教材版本都已经完成解析和内部 sense-aware 去重后，才执行一次最终 reconciliation：

```text
Third-party Unified Vocabulary
vs
Klose Full Stable Identity Registry
```

Klose 比较范围必须是完整 Stable Identity Registry：

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
Third-party Unified Vocabulary:
bank = 银行
bank = 河岸

Klose Stable Vocabulary:
bank = 银行

最终：
bank = 银行 → existing-in-klose
bank = 河岸 → third-party-new
```

这一步也是 sense-aware reconciliation，不是 `MatchKey` 字符串差集。

## 8. 学习语义

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

“全部计划学习”不等于 corpus 构建阶段自动写入当前 Master / Release / Anki。

## 9. Source Truth 边界

统一第三方 corpus 即使已经充分清洗，仍然是第三方数据，不升级为 Klose 实际教材真源。

优先级继续保持：

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

如果第三方 corpus 与 Klose 实际教材发生冲突，按 `docs/SOURCE_RECONCILIATION.md` 处理，不能反向覆盖实际教材 Source Fact。

## 10. 当前实现状态

当前第一个 seed：

```text
anki/klose/source_reference/beijing_start1_staging/
```

北京版已完成 12 册解析、surface inventory、主要高风险 review，并曾与 Klose Stable Identity 做 candidate matching。该匹配结果保留为北京版 staging 的审计/诊断信息，但根据本设计，**不再把它视为第三方 corpus 构建阶段的最终去重结果**。

当前仍保持：

```text
MergeAuthorized = no
```

下一阶段应把北京版 staging 演进为统一第三方 corpus 的 Source Adapter #1，然后继续加入其他教材版本。等计划中的第三方教材都完成内部 sense-aware 去重后，再执行阶段 B 的最终 Klose diff。
