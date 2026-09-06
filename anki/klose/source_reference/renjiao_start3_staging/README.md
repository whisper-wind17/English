# Renjiao Start3 — Third-party Source Adapter

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 8
Source occurrences = 851
Distinct MatchKeys = 818
```

No cross-source identity state and no Klose final-diff state are stored here.
