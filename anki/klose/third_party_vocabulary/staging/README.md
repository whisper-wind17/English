# Third-party Vocabulary — Simplified Stage A

Active data flow:

```text
config/source_adapters.csv
+ standardized adapter occurrences
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ surface_candidates.csv
→ review_queue.csv
→ unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

```text
Enabled adapters          = 2
Source occurrences        = 1716
Normalized surfaces       = 1144
Vocabulary preview        = 1028
Review/blocker surfaces   = 64
```

Candidate signals are evidence only. `identity_decisions.csv` is the single
content-decision truth. Stable ThirdPartyID is not minted and Stage-B Klose diff
is not executed here.
