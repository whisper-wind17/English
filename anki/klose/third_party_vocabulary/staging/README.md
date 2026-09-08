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
Enabled adapters          = 6
Source occurrences        = 6005
Normalized surfaces       = 2161
Vocabulary preview        = 1060
Review/blocker surfaces   = 899
Evidence-changed surfaces = 805
Multipart resolved        = 11
```

Each durable decision is bound to the exact Source Occurrences it reviewed via an
unambiguous JSON array in `OccurrenceKeys`. Additional source evidence automatically
re-queues that MatchKey. Multipart split decisions must form a disjoint, complete
occurrence partition before leaving review. Candidate signals are evidence only.
Canonical blockers cannot be bypassed by reuse aliases. Stable ThirdPartyID is not
minted and Stage-B Klose diff is not executed here.
