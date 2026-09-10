#!/usr/bin/env python3
"""Fail-closed quality gate for Grade 5-6 new-note learner examples.

Checks exact active-ID coverage, non-empty bilingual examples, short presentation,
target-form coverage (with light inflection handling), duplicate examples, selected
high-risk homograph/sense cues, and explicitly later auxiliary vocabulary based on
the legacy PEP inventory. Source Grade remains a difficulty signal rather than a
hard LearnerLevel gate; the target lexical item itself is excluded from the
auxiliary-vocabulary check.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
REG = BASE / "master" / "note_registry_extensions.csv"
BATCHES = [
    BASE / "learner" / "grade5_6_content_batch_a.csv",
    BASE / "learner" / "grade5_6_content_batch_b.csv",
    BASE / "learner" / "grade5_6_content_batch_c.csv",
]
LEGACY = ROOT / "anki" / "人教版一年级起点" / "master" / "vocabulary_master.csv"
CREATED_SOURCE = "klose-grade5-6-current"
TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
FUNCTION_WORDS = {
    "a","an","the","i","you","he","she","it","we","they","me","him","her","us","them",
    "my","your","his","our","their","this","that","these","those","who","what","where","when","why","how",
    "am","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "can","could","will","would","shall","should","may","might","must","not","don't","doesn't","didn't",
    "and","or","but","so","because","if","then","than","as","in","on","at","to","from","of","for","with","by",
    "near","under","behind","between","before","after","into","out","around","about","over","here","there",
    "very","too","also","only","just","more","most","less","some","any","many","much","all","every","each",
    "please","let","now","today","yesterday",
}
IRREGULAR = {
    "went":"go","gone":"go","saw":"see","seen":"see","took":"take","taken":"take","ate":"eat","eaten":"eat",
    "ran":"run","made":"make","began":"begin","became":"become","fell":"fall","gave":"give","given":"give",
    "wrote":"write","written":"write","won":"win","bought":"buy","kept":"keep","read":"read","had":"have",
}
HIGH_RISK_CUES = {
    "KV000913": {"tv star"},
    "KV000937": {"tv show"},
    "KV000977": {"class"},
    "KV000985": {"play"},
    "KV000993": {"best"},
    "KV001014": {"art show"},
    "KV001028": {"like"},
    "KV001035": {"turn"},
    "KV001039": {"show"},
    "KV001055": {"took", "walk"},
    "KV001056": {"view"},
    "KV001071": {"as"},
    "KV001085": {"cold"},
    "KV001134": {"times"},
    "KV001141": {"light"},
    "KV001142": {"cools"},
    "KV001143": {"runs", "fan"},
    "KV001158": {"top"},
    "KV001170": {"camp"},
    "KV001172": {"fish"},
    "KV001176": {"off"},
    "KV001182": {"part"},
    "KV001193": {"trip"},
    "KV001194": {"dream"},
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing learner-content input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tokens(text: str) -> list[str]:
    return [x.lower().replace("’", "'") for x in TOKEN_RE.findall(text or "")]


def lemmas(token: str) -> set[str]:
    out = {token}
    if token in IRREGULAR:
        out.add(IRREGULAR[token])
    if token.endswith("'s"):
        out.add(token[:-2])
    if len(token) > 4 and token.endswith("ies"):
        out.add(token[:-3] + "y")
    if len(token) > 4 and token.endswith("ing"):
        stem = token[:-3]; out.update({stem, stem + "e"})
        if len(stem) > 2 and stem[-1] == stem[-2]: out.add(stem[:-1])
    if len(token) > 3 and token.endswith("ed"):
        stem = token[:-2]; out.update({stem, stem + "e"})
        if len(stem) > 2 and stem[-1] == stem[-2]: out.add(stem[:-1])
    if len(token) >= 4 and token.endswith("es"):
        out.update({token[:-2], token[:-1]})
    if len(token) > 3 and token.endswith("s"):
        out.add(token[:-1])
    return out


def target_tokens(word: str) -> list[str]:
    word = re.sub(r"\s*\([^)]*\)\s*$", "", word or "").strip()
    return tokens(word)


def main() -> None:
    active_rows = [
        r for r in read_csv(REG)
        if r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("Status", "").strip() == "active"
    ]
    active = {r["NoteID"].strip(): r for r in active_rows}
    if len(active) != 288:
        raise SystemExit(f"Expected 288 active Grade 5-6 new identities, got {len(active)}")

    rows = [r for p in BATCHES for r in read_csv(p)]
    by_id = {r["NoteID"].strip(): r for r in rows}
    if len(rows) != 288 or len(by_id) != 288 or set(by_id) != set(active):
        raise SystemExit(f"Learner-content coverage mismatch: rows={len(rows)} unique={len(by_id)} active={len(active)}")

    examples_seen: dict[str, str] = {}
    structural_errors: list[str] = []
    for nid, row in by_id.items():
        sentence = row.get("ExampleSentence", "").strip()
        translation = row.get("ExampleTranslation", "").strip()
        if row.get("ContentStatus", "").strip() != "model-curated" or row.get("ContentSource", "").strip() != "grade5-6-learner-content-v1":
            structural_errors.append(f"{nid}: invalid content provenance")
        if not sentence or not translation:
            structural_errors.append(f"{nid}: blank bilingual example")
            continue
        if len(tokens(sentence)) > 14:
            structural_errors.append(f"{nid}: example too long ({len(tokens(sentence))} tokens)")
        key = re.sub(r"\s+", " ", sentence.casefold())
        if key in examples_seen:
            structural_errors.append(f"{nid}: duplicate English example with {examples_seen[key]}")
        examples_seen[key] = nid

        sent_lemmas = set().union(*(lemmas(t) for t in tokens(sentence))) if tokens(sentence) else set()
        targets = target_tokens(active[nid].get("CanonicalWord", ""))
        missing_targets = [t for t in targets if not (lemmas(t) & sent_lemmas)]
        if missing_targets:
            structural_errors.append(f"{nid}: target form not represented in example: {missing_targets}")
        lower = sentence.casefold()
        cues = HIGH_RISK_CUES.get(nid, set())
        for cue in cues:
            if cue not in lower:
                structural_errors.append(f"{nid}: high-risk sense cue missing: {cue!r}")

    if structural_errors:
        print("Grade 5-6 learner-content structural errors:")
        for item in structural_errors[:50]: print(item)
        raise SystemExit(f"Grade 5-6 learner-content structure failed: {len(structural_errors)} errors")

    # Auxiliary vocabulary signal: derive earliest legacy PEP grade by token/lemma.
    earliest: dict[str, int] = {}
    for row in read_csv(LEGACY):
        grade_s = row.get("Grade", "").strip()
        if not grade_s.isdigit():
            continue
        grade = int(grade_s)
        for token in tokens(row.get("Word", "")):
            for lemma in lemmas(token):
                earliest[lemma] = min(grade, earliest.get(lemma, grade))

    future: list[str] = []
    for nid, row in by_id.items():
        target_lemmas: set[str] = set()
        for t in target_tokens(active[nid].get("CanonicalWord", "")):
            target_lemmas.update(lemmas(t))
        offenders: dict[str, int] = {}
        for token in tokens(row["ExampleSentence"]):
            if token in FUNCTION_WORDS:
                continue
            tl = lemmas(token)
            if tl & target_lemmas:
                continue
            grades = [earliest[x] for x in tl if x in earliest]
            if grades and min(grades) > 4:
                offenders[token] = min(grades)
        if offenders:
            future.append(f"{nid}: " + " ".join(f"{k}->G{v}" for k,v in sorted(offenders.items())))
    if future:
        print("Grade 5-6 learner-content later auxiliary vocabulary:")
        for item in future: print(item)
        raise SystemExit(f"Grade 5-6 learner-content has {len(future)} examples with explicitly later auxiliary vocabulary")

    print(f"Grade 5-6 learner content OK: active=288, bilingual=288, unique_examples=288, high_risk_cues={len(HIGH_RISK_CUES)}, later_aux=0")


if __name__ == "__main__":
    main()
