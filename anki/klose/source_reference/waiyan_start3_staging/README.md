# Waiyan Start3 — Third-party Source Adapter

Scope:

```text
外研版三年级起点 3-6 年级上下册 = 8 primary-school books
```

The start-from-grade-1 primary family and middle/high-school XLSX files in the
same raw directory are explicitly excluded.

Expected source schema:

```text
A 单词 | B 英音 | C 美音 | D 释义
```

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 8
Source occurrences = 1157
Distinct MatchKeys = 1023
```

No cross-source identity state and no Klose final-diff state are stored here.
