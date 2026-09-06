# Hujiao Start3 — Third-party Source Adapter

Scope:

```text
沪教版三年级起点 3-6 年级上下册 = 8 primary-school books
```

Grade 7-9 Oxford English XLSX files in the same raw directory are explicitly excluded.

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 8
Source occurrences = 1111
Distinct MatchKeys = 1067
```

No cross-source identity state and no Klose final-diff state are stored here.
