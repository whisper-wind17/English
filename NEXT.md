# NEXT — Klose Vocabulary System

Last updated: 2026-09-05

This file is the handoff entry for the next conversation. Read `AGENTS.md` first, then this file, then the referenced reconciliation document before changing any Klose vocabulary data.

## Current objective

Fix the discovered textbook-version mismatch before Klose starts formal Anki study, then continue with Klose's actual Grade 4 lower textbook and later Grade 5/6 expansion.

The key design remains unchanged:

- `Source Grade` = where an item appears in a textbook.
- `LearnerLevel` = how Klose should learn it now.
- Klose remains `LearnerLevel = 4` even when later learning Grade 5/6 source vocabulary.
- One Vocabulary Note = one stable learning unit / target sense.
- GitHub is content/identity/release truth; Anki is FSRS/review-state truth.

## Critical blocker discovered

Klose's actual 人教版一年级起点《四年级上》 textbook does **not** match the repo's existing third-party `rj_start1::4年级上` source dataset.

Existing repo Grade 4 upper starts with topics/items such as:

`running / basketball / roller skating / jumping rope / ...`

Klose's actual Grade 4 upper has six units centered on:

1. jobs / chores
2. personal traits
3. places / community
4. jobs
5. weather
6. clothes / seasons

This is a source-version mismatch, not a small omission.

Full diagnosis and acceptance criteria:

`anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md`

Status there is **BLOCKED FOR SOURCE RECONCILIATION**.

## Actual Grade 4 upper material already captured

From Klose's physical textbook screenshots:

- Core vocabulary:
  `anki/klose/source_reference/rj_start1-grade4-upper-klose-actual.csv`
  - 6 Units
  - 110 occurrence rows
  - 109 unique surface entries
  - `cook` appears twice with different target senses

- Useful Expressions:
  `anki/klose/source_reference/rj_start1-grade4-upper-klose-expressions.csv`
  - 41 raw textbook expression rows
  - preserve as Source Facts

- Pattern candidates:
  `anki/klose/source_reference/rj_start1-grade4-upper-pattern-candidates.csv`
  - extracted reusable patterns
  - candidate only; do not release as Anki cards yet

- Source-reference rules:
  `anki/klose/source_reference/README.md`

Important expression design decision:

- Vocabulary and Expressions are different learning-object types.
- Do not stuff full textbook expressions into `Klose Vocabulary` Notes.
- Raw expressions are preserved 100%; only reusable communicative patterns may later become a separate Expression learning system / Note Type.

## Identity issue already confirmed

`cook` is a real sense-split blocker:

- Unit 1: `cook` = 烹饪；煮 (verb)
- Unit 4: `cook` = 厨师 (noun)

Current released `KV000424` incorrectly combines the two senses (`厨师；做饭`) while its example is noun-sense.

Expected migration direction:

- keep `KV000424` for `cook` noun / 厨师
- append a new NoteID for `cook` verb / 烹饪；煮

Do not renumber an existing NoteID and do not silently merge target senses.

## Current Anki state

First Desktop import and AnkiWeb upload have been completed.

Current baseline:

- Deck: `Klose-English::Vocabulary`
- Note Type: `Klose Vocabulary`
- 1 Note = 1 Recognition Card
- 518 Cards imported
- 343 Suspended
- 175 Unsuspended
- New cards/day = 8
- Maximum reviews/day = 9999
- Learning step = `10m`
- Relearning step = `10m`
- New cards: ascending position / order gathered
- Reviews before new cards
- FSRS = ON
- Desired retention = 90%
- FSRS parameters = default; do not optimize yet
- `Reschedule cards on change` = OFF

Card contract:

- Front: `Word` only
- Back: `Word` via `FrontSide`, word TTS `{{tts en_US:Word}}`, UK/US IPA, `MeaningPrimary`, example, translation
- Example sentence is not auto-read yet

AnkiWeb was empty before first sync; Desktop data was uploaded to AnkiWeb successfully.

### Temporary safety rule

**Do not let Klose start formal study yet.**

The 175 active `stage::grade4-new` cards were staged from the mismatched Grade 4 source. Klose currently has no real Review History, so this is the lowest-risk point to fix source/identity/staging before FSRS history is created.

Do not delete/renumber existing NoteIDs and do not hand-edit generated `study.csv` / `anki-import.csv`.

## Next conversation — work order

1. Read:
   - `AGENTS.md`
   - this `NEXT.md`
   - `anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md`
   - `anki/klose/source_reference/README.md`

2. Complete Grade 4 upper reconciliation first:
   - classify all 110 actual Core Vocabulary occurrences against current Master/Identity
   - reuse existing NoteIDs when the same learning unit/sense already exists
   - add Klose-actual textbook provenance where source placement was wrong/missing
   - separately review phrase/morphology candidates such as `office worker` vs `worker`, `football` vs `play football`, `sock` vs `socks`, etc.
   - append NoteIDs only for genuinely new learning units
   - perform explicit `cook` noun/verb split migration
   - keep `LearnerLevel = 4`
   - re-review changed/new MeaningPrimary / ExampleSentence / ExampleTranslation
   - rebuild staging from upstream truth
   - run release/readiness gates
   - regenerate `study.csv` and the only formal Anki artifact `anki-import.csv`

3. Only after Grade 4 upper is understood, accept the user's Grade 4 lower textbook screenshots (core vocabulary + Useful Expressions) and capture them in the same source-reference structure.

4. Once Grade 4 upper/lower actual edition is established, decide whether the existing third-party files represent another edition and model editions explicitly instead of overwriting provenance.

5. Only after Grade 4 source correction is stable, continue Grade 5/6 vocabulary expansion. Grade 5/6 source words must still be prepared for current `LearnerLevel = 4`; source grade must never be used as learner level.

## Definition of done for Grade 4 upper

Do not mark Grade 4 upper complete until all are true:

- [ ] all 110 core-vocabulary occurrences have explicit identity decisions
- [ ] exact existing Notes reuse stable NoteIDs and gain correct actual-textbook provenance
- [ ] phrase/morphology candidates are resolved sense-aware, not by substring matching
- [ ] genuinely new learning units receive appended NoteIDs
- [ ] `cook` noun/verb split migration is complete
- [ ] `LearnerLevel` remains 4
- [ ] all changed/new learner presentations are reviewed/current-fingerprint valid
- [ ] active-card staging is rebuilt from corrected source truth
- [ ] release readiness gate passes
- [ ] corrected `anki-import.csv` is generated for re-import/update
- [ ] only then may Klose begin formal study

## Relevant operating docs

- `docs/KLOSE_VOCABULARY_SYSTEM.md`
- `docs/ANKI_FIRST_IMPORT.md`
- `docs/ANKI_FIRST_IMPORT_GUIDE.md`
- `docs/ANKI_SYNC_WORKFLOW.md`
- `anki/klose/README.md`

First-import flow is already complete; the next conversation should not repeat setup unless troubleshooting. The priority is **source reconciliation and safe correction before study begins**.
