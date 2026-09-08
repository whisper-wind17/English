# Beijing Start1 — Third-party Source Adapter

Scope:

```text
北京版一年级起点 1-6 年级上下册 = 12 primary-school books
```

Active source-only output:

```text
occurrences.csv
```

Expected source schema:

```text
A 单词 | B 英音 | C 美音 | D 释义
```

The adapter captures source facts only. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 12
Source occurrences = 808
Distinct MatchKeys = 734
```

Legacy Beijing pre-merge review artifacts may remain in this directory for audit
history, but they are deprecated and are not consumed by the Third-party Stage-A
source adapter or by Stage-B reconciliation.
