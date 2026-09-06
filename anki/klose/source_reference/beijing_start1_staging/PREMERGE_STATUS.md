# Beijing Edition Grade 1–6 Vocabulary — Pre-merge Status

Last updated: 2026-09-06

## Long-term role

北京版 staging 现在明确定位为统一第三方教材词源的 **第一个 seed / Source Adapter**，而不是长期维护的“北京版主词表”。

长期设计见：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
```

后续人教版、沪教版及其他第三方教材词表都会进入同一个 sense-aware 去重流程。

当前长期流程已经冻结为两阶段：

```text
阶段 A：所有第三方教材内部统一、sense-aware 去重
→ Third-party Unified Vocabulary

阶段 B：全部第三方来源处理完成后
→ 与 Klose Full Stable Identity Registry 做最终 sense-aware diff
→ Third-party New Vocabulary Pool
```

这个 New Vocabulary Pool 的业务含义是：**Klose 当前实际教材之外、后续计划全部学习的新 Vocabulary learning units**。

教材版本、最早出现年级、覆盖教材数、跨册出现次数、年级分布都不作为学习决策维度；来源信息只在 raw / Source Occurrence 层保留用于回溯。

## State

```text
Source Extracted       = yes
Cross-book Surface Dedup = yes
Compared to Stable Identity Registry = yes   # historical diagnostic / candidate comparison
High-risk Identity Review = yes
Inflection Variant Review = yes
Occurrence Semantic Risk Review = partial / blocker-aware
Merge Authorized       = no
Klose Master Modified  = no
Release/Publish Modified = no
Anki Modified          = no
```

This is a **staging-only** work area. Nothing in this directory is an input that automatically changes the current Klose Vocabulary inventory.

## Scope and counts

Source scope: repository Beijing Edition, one-year-start, Grade 1–6, upper + lower, 12 XLSX books.

```text
Source occurrences              = 808
Distinct normalized MatchKeys   = 734
Existing stable Klose identities compared = 901

surface exact-single            = 433
surface exact-multiple          = 7
surface format-alias            = 1
surface morphology              = 2
surface no-existing-match       = 291
```

The 734 MatchKeys are a surface index, not the final Vocabulary Identity count.

These counts are audit/build facts for this seed only. They are not intended to become learning priority or curriculum statistics.

The previous comparison against 901 Klose Stable Identities is retained as useful staging evidence, but under the two-stage design it is **not** the final Klose dedup. Final `existing-in-klose` / `third-party-new` classification happens only after the complete third-party corpus is built.

## Completed pre-merge work

1. All 12 XLSX books are parsed deterministically from the repository without inventing Unit metadata.
2. Every source row is preserved in `occurrences.csv` with grade, semester, source row, word, UK/US IPA, definition and source file.
3. Every occurrence was compared against both committed stable identity registries as an early diagnostic/candidate analysis:
   - `note_registry.csv`
   - `note_registry_extensions.csv`
4. Candidate matching is deliberately conservative:
   - exact MatchKey can only become a reuse candidate;
   - multiple same-key identities require sense review;
   - punctuation/ellipsis aliases require review;
   - morphology is candidate-only;
   - phrase substring matching is forbidden.
5. The 10 primary high-risk identity candidates have explicit staging review records in `identity_resolution_review.csv`.
6. The inflection audit is separately enforced. False positives such as `hi -> his` and `Mr -> Mrs` were removed. The remaining six form relations have explicit review records in `source_variant_resolution_review.csv`.
7. Occurrence-level semantic collisions that a surface-only dedup would miss are explicitly recorded in `semantic_resolution_review.csv`.
8. CI runs `check_klose_beijing_premerge.py` and also asserts that Klose master/release/learner/publish state is untouched.

## Important semantic findings

The Beijing XLSX `释义` field is a broad dictionary gloss, not a reliable textbook target-sense field. Source order sometimes provides stronger evidence than the gloss.

Examples:

- `May` in Grade 3 upper appears in a month/date sequence and maps to existing `KV000270 = 五月`, even though the XLSX gloss incorrectly contains only modal `may` meanings.
- lowercase `may` in Grade 3 lower appears in `drink / may / tea / sure` context and must **not** reuse `KV000270`; it is a new modal-sense candidate.
- `like` inside `weather / like / sunny / warm / ...` is not safely the existing `like = 喜欢` identity; it is a different usage/sense candidate.
- `square` inside a shape block must not reuse existing `square = 广场`.
- directional `left` inside a location/directions block must not reuse existing `left = leave 的过去式`.

These cases prove that `lower(word)` / MatchKey dedup is not sufficient.

## High-risk / held cases

Current staging review includes:

```text
High-confidence proposed reuse:
- can -> KV000074 (modal)
- cook -> KV000805 (verb)
- How old ...? -> KV000210
- milk -> KV000088
- men -> KV000112 (provisional morphology policy)
- women -> KV000110 (provisional morphology policy)

Provisional:
- over -> KV000863 (likely 结束（的）)
- watch -> KV000851 (likely verb 看/观看)

Held for source context / identity policy:
- fan
- kind
- speak
- cold
- light
- pass
- dress
- child / children
- tooth / teeth
```

Regular singular/plural pairs `noodle/noodles`, `shoe/shoes`, `sock/socks` are high-confidence reuse candidates. `glass/glasses` must not be merged merely by morphology because the target senses may be glass/material vs eyeglasses.

## Remaining blocker before any Klose merge

The current repository Beijing XLSX data lacks Unit/sentence context and uses dictionary-style glosses. Therefore it is not sufficient to source-confirm every ambiguous target sense.

Before any ambiguous third-party Identity is eventually merged into Klose, remaining held cases must be resolved from one of:

```text
Klose actual textbook evidence
> confirmed same-edition official textbook material
> otherwise explicit model/human decision marked as non-source-confirmed
```

This blocker does **not** prevent keeping Beijing as Source Adapter #1 or continuing to add other third-party versions into the unified corpus. It only prevents treating every MatchKey candidate as a safe identity merge.

## Merge boundary

During stage A — third-party corpus construction:

- do not write Beijing provenance into Klose `master/source_occurrences.csv`;
- do not append Beijing-driven identities to Klose `note_registry_extensions.csv`;
- do not delete a third-party learning unit merely because an early Klose comparison appears to match it;
- do not classify the current Beijing-only result as the final `Third-party New Vocabulary Pool`;
- do not change Klose release/admission/learner/publish state;
- do not generate or import new Anki cards from this staging directory;
- keep every Klose merge review row `MergeAuthorized=no`.

When the unified third-party corpus implementation starts, first convert this Beijing staging into Source Adapter #1, then add other third-party versions into the same Third-party Identity Registry. Each additional version is deduplicated only against the Third-party Unified Vocabulary at this stage.

Only after all planned third-party sources are incorporated should stage B run once against the complete Klose Stable Identity Registry. That final sense-aware diff produces `existing-in-klose` and `third-party-new`.

When Klose merge is eventually approved, apply only resolved `third-party-new` learning units to the normal Klose Identity / Learner / Admission / Review / Release chain. Existing NoteIDs remain stable and new NoteIDs are append-only.
