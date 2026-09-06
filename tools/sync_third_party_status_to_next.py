#!/usr/bin/env python3
"""Synchronize the current third-party vocabulary Stage A progress into NEXT.md."""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXT = ROOT / "NEXT.md"
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
RESOLUTION = STAGING / "cross_source_identity_resolution.csv"
MORPH = BASE / "third_party_vocabulary" / "review" / "renjiao_start1_morphology_resolution.csv"
NEW_SURFACE = BASE / "source_reference" / "renjiao_start1_staging" / "new_surface_candidates.csv"
RISK = STAGING / "cross_source_semantic_risk_queue.csv"
TYPE_AUDIT = STAGING / "renjiao_new_surface_type_audit.csv"
ROUTE_RESOLUTION = STAGING / "renjiao_new_surface_route_resolution.csv"
ROUTE_QUEUE = STAGING / "renjiao_new_surface_identity_review_queue.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    resolution = read_csv(RESOLUTION)
    morph = read_csv(MORPH)
    new_surface = read_csv(NEW_SURFACE)
    risk = read_csv(RISK)
    type_audit = read_csv(TYPE_AUDIT)
    route_resolution = read_csv(ROUTE_RESOLUTION)
    route_queue = read_csv(ROUTE_QUEUE)

    statuses = Counter(r["ResolutionStatus"] for r in resolution)
    decisions = Counter(r["ProposedDecision"] for r in resolution)
    morph_held = sum(r["ProposedDecision"].startswith("held-") for r in morph)
    morph_resolved = len(morph) - morph_held
    type_counts = Counter(r["CandidateType"] for r in type_audit)
    route_statuses = Counter(r["ResolutionStatus"] for r in route_resolution)
    route_decisions = Counter(r["ProposedObjectDecision"] for r in route_resolution)

    section = f'''## 9. Third-party Multi-Edition Vocabulary Corpus — two-stage design + current progress

2026-09-06 用户确认长期目标：北京版只是第一个 seed，后续把人教版、沪教版及其他第三方小学教材词表持续累加到同一个统一第三方 corpus，按 learning unit / target sense 做 sense-aware 去重。

长期设计：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
```

两阶段流程冻结为：

```text
Stage A — 第三方内部

多个第三方教材 Raw Vocabulary
→ Source Adapters
→ 与 Third-party Unified Vocabulary 做 sense-aware 去重
→ 完整 Third-party Unified Vocabulary

Stage B — 所有第三方来源完成后

完整 Third-party Unified Vocabulary
→ 与 Klose Full Stable Identity Registry 做一次最终 sense-aware diff
→ Third-party New Vocabulary Pool
→ 后续全部作为 Klose 当前教材之外的新词学习
```

当前已接入两个独立 Source Adapter：

```text
Adapter #1  beijing_start1
Source books             = 12
Source occurrences       = 808
Distinct MatchKeys       = 734

Adapter #2  renjiao_start1
Source books             = 12
Source occurrences       = 908
Distinct MatchKeys       = 802
```

人教版目录同时存在“一年级起点”和“三年级起点”；当前只接入 `renjiao_start1`。三年级起点未来作为独立 adapter，不能静默混入一年级起点。

北京 + 人教一年级起点当前联合 Stage A 工作区：

```text
anki/klose/third_party_vocabulary/staging/

Total source occurrences       = 1716
Distinct normalized MatchKeys  = 1144
Cross-source exact overlaps    = 392
Single-source surfaces         = 752
Renjiao morphology candidates  = {len(morph)}
Renjiao new-surface candidates = {len(new_surface)}
Cross-source context reviews   = {len(resolution)}
Semantic-risk queue            = {len(risk)}
```

Cross-source exact-overlap Identity Resolution：

```text
rule-reviewed reuse             = {statuses.get('rule-reviewed', 0)}
model-reviewed rows             = {statuses.get('model-reviewed', 0)}
pending semantic review         = {statuses.get('pending', 0)}

reuse-learning-unit             = {decisions.get('reuse-learning-unit', 0)}
partial-overlap-split-required  = {decisions.get('partial-overlap-split-required', 0)}
do-not-merge                    = {decisions.get('do-not-merge', 0)}
held / policy-context blocker   = {sum(v for k, v in decisions.items() if k.startswith('held-'))}

morphology resolved             = {morph_resolved}
morphology held                 = {morph_held}
```

当前已显式保护的 cross-source semantic collision 包括：

```text
May(月份) vs may(情态动词)
like=喜欢 vs weather ... like ...
square=正方形 vs square=广场
left=左边 vs left=leave过去式
cook=烹饪/煮 vs cook=厨师
cold=寒冷 vs cold=感冒
study=学习 vs study=书房
```

人教版 403 个原始 `new surface` 已完成对象类型审计；**403 surface 不等于 403 Vocabulary Identity**：

```text
single-token lexical             = {type_counts.get('single-token-lexical-review', 0)}
multiword lexical                = {type_counts.get('multiword-lexical-review', 0)}
multiword routing                = {type_counts.get('multiword-routing-review', 0)}
expression / event chunk         = {type_counts.get('expression-or-chunk-review', 0)}
ordinal format alias             = {type_counts.get('ordinal-format-alias-review', 0)}
single-token form                = {type_counts.get('single-token-form-review', 0)}
```

其中 `shopping centre / shopping list / shopping mall` 已显式保护为 lexical compounds，不能因为首词为 `shopping` 就被 gerund heuristic 错误路由成 event chunk。

当前 Renjiao new-surface Object / Sense Resolution：

```text
rule-reviewed rows                       = {route_statuses.get('rule-reviewed', 0)}
model-reviewed rows                      = {route_statuses.get('model-reviewed', 0)}
pending rows                             = {route_statuses.get('pending', 0)}

new Vocabulary learning-unit candidates = {route_decisions.get('new-vocabulary-learning-unit-candidate', 0)}
single-token sense pending               = {route_decisions.get('pending-vocabulary-sense-review', 0)}
multiword phrase sense pending           = {route_decisions.get('pending-vocabulary-phrase-sense-review', 0)}
Vocabulary-vs-Expression pending         = {route_decisions.get('pending-vocabulary-vs-expression-review', 0)}
ordinal aliases                          = {route_decisions.get('canonical-form-alias-candidate', 0)}
Expression candidates                    = {route_decisions.get('route-expression-candidate', 0)}
source chunks / no Vocabulary identity   = {route_decisions.get('route-source-chunk-no-vocabulary-identity', 0)}
held source-context blockers             = {route_decisions.get('held-source-context-required', 0)}
held form-policy blockers                = {route_decisions.get('held-identity-form-policy', 0)}
within-source split-required             = {route_decisions.get('within-source-split-required', 0)}
identity/object review queue             = {len(route_queue)}
```

Single-token semantic-risk review 已完成独立闭合：原 90 条中，73 条明确为新 Vocabulary learning-unit candidate，16 条因 source context 不足保持 held，`French` 因同时出现“法语”和国籍/形容词用法标记为 within-source split-required。

当前工程状态：

```text
Renjiao Stage A Valid                    = yes
Combined Stage A build                   = yes
Cross-source context audit               = yes
Cross-source Identity Resolution         = complete / pending 0
New-surface type audit                   = complete
New-surface object routing               = complete
Single-token sense review                = complete / pending 0
Independent Completion Rechecks          = pass
Stable ThirdPartyID minted               = no
Final Klose diff executed                = no
Klose Master/Release/Publish/Anki changed = no
```

重要约束继续有效：

- 北京版只有 seed 身份，没有语义优先级；
- 第二个及后续教材在 Stage A **只和第三方 Unified Vocabulary 去重**，不因 Klose 当前已有同词而删除第三方 Identity；
- 在所有计划中的第三方来源处理完成前，不生成最终 `existing-in-klose / third-party-new` 结论；
- 早期与 Klose 的比较可以保留为 diagnostic / candidate evidence，但不能作为第三方 corpus 删除依据；
- 去重单位是 `learning unit / target sense`，不是字符串；
- 同 surface 不同义项必须允许多个第三方 Identity；
- morphology / phrase / punctuation 只产生 candidate，不自动 merge；
- Vocabulary 与 Expressions 是不同学习对象；不能因为第三方词表里出现一个短语/句块就自动 mint Vocabulary Identity；
- 教材版本、最早年级、覆盖教材数、出现次数、年级分布都不作为学习决策维度；
- provenance 只在 raw / Source Occurrence 层保留用于回溯，不进入正常学习界面；
- 第三方统一 corpus 永远低于 Klose 实际教材 Source Truth 优先级。

当前下一步：

```text
1. 处理 {route_decisions.get('pending-vocabulary-phrase-sense-review', 0)} 个 multiword lexical phrase sense reviews；
2. 处理 {route_decisions.get('pending-vocabulary-vs-expression-review', 0)} 个 Vocabulary-vs-Expression routing reviews；
3. 复核 held / form-policy blockers 与 within-source split，再判断是否足够稳定到 mint 第一版 Stable ThirdPartyID；
4. Stable ThirdPartyID 建立后继续接入后续第三方 adapter；
5. 所有计划第三方来源完成前，不执行 Klose Stage-B final diff；
6. 每个阶段完成后必须执行独立 Completion Recheck。
```
'''

    text = NEXT.read_text(encoding="utf-8")
    pattern = re.compile(
        r"## 9\. Third-party Multi-Edition Vocabulary Corpus.*?(?=\n---\n\n## 10\. Frozen long-term rules)",
        flags=re.S,
    )
    if not pattern.search(text):
        raise SystemExit("Cannot locate Third-party section in NEXT.md")
    updated = pattern.sub(section.rstrip(), text)
    if updated != text:
        NEXT.write_text(updated, encoding="utf-8")
        print("NEXT third-party status updated = yes")
    else:
        print("NEXT third-party status updated = no-change")


if __name__ == "__main__":
    main()
