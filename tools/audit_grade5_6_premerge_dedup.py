#!/usr/bin/env python3
"""Audit allocated Grade 5-6 Vocabulary identities for pre-merge duplicates.

This is a review-only, non-mutating audit.  It compares Grade 5-6 allocated
identities against the pre-existing Klose Stable Vocabulary registry and against
other Grade 5-6 allocated identities.  Candidate generation is intentionally
form-aware rather than meaning-only: synonyms such as gift/present are different
learning units and must not be merged merely because their Chinese glosses match.

The audit maximizes throughput by reducing the Cartesian product to pairs with
strong identity-risk signals: same surface, allocation-origin surface match,
orthographic variants, inflectional equivalence, determiner/possessive phrase
variants, and high-overlap proper-name variants.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
OUT_DIR = BASE / "review" / "grade5_6_premerge_dedup"
CANDIDATES = OUT_DIR / "candidates.csv"
STATUS = OUT_DIR / "status.json"

REGISTRIES = [MASTER / "note_registry.csv", MASTER / "note_registry_extensions.csv"]
GRADE56_SOURCE = "klose-grade5-6-current"

FIELDS = [
    "CandidateID", "Scope", "NewNoteID", "OtherNoteID",
    "NewWord", "NewMatchKey", "NewSense", "NewOriginSurface",
    "OtherWord", "OtherMatchKey", "OtherSense", "OtherCreatedSource",
    "Signals", "RiskScore", "ReviewStatus", "Decision", "MergeIntoNoteID", "Rationale",
]

IRREGULAR = {
    "went": "go", "gone": "go",
    "took": "take", "taken": "take",
    "had": "have",
    "ate": "eat", "eaten": "eat",
    "saw": "see", "seen": "see",
    "made": "make",
    "sang": "sing", "sung": "sing",
    "woke": "wake", "woken": "wake",
    "began": "begin", "begun": "begin",
    "bought": "buy",
    "felt": "feel",
    "left": "leave",
    "slept": "sleep",
    "swam": "swim", "swum": "swim",
    "won": "win",
    "were": "be", "was": "be",
    "did": "do", "done": "do",
    "wrote": "write", "written": "write",
    "spoke": "speak", "spoken": "speak",
    "ran": "run",
    "children": "child", "feet": "foot", "teeth": "tooth",
    "mice": "mouse", "people": "person",
}

UK_US = {
    "centre": "center", "centres": "centers",
    "colour": "color", "colours": "colors",
    "favourite": "favorite", "favourites": "favorites",
    "theatre": "theater", "theatres": "theaters",
    "metre": "meter", "metres": "meters",
    "kilometre": "kilometer", "kilometres": "kilometers",
    "labour": "labor",
}

DROP_TOKENS = {
    "a", "an", "the", "my", "your", "his", "her", "our", "their", "its", "one's", "ones",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip()).casefold()
    return value


def words(value: str) -> list[str]:
    value = norm(value)
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", value)


def orth_key(value: str) -> str:
    out = []
    for token in words(value):
        out.append(UK_US.get(token, token))
    return " ".join(out)


def lemma_token(token: str) -> str:
    token = UK_US.get(token, token)
    if token in IRREGULAR:
        return IRREGULAR[token]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        stem = token[:-3]
        if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in "lsz":
            stem = stem[:-1]
        # dancing -> dance; making -> make, while reading/eating remain read/eat.
        if stem.endswith(("anc", "ak", "ik", "ov", "us")):
            stem += "e"
        return stem
    if len(token) > 4 and token.endswith("ied"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("ed"):
        stem = token[:-2]
        if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in "lsz":
            stem = stem[:-1]
        if stem.endswith(("at", "iz", "iv", "ov", "us")):
            stem += "e"
        return stem
    if len(token) > 4 and token.endswith("es") and not token.endswith(("ses", "xes")):
        return token[:-1]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def lemma_key(value: str) -> str:
    return " ".join(lemma_token(t) for t in words(value))


def phrase_skeleton(value: str) -> str:
    toks = [lemma_token(t) for t in words(value) if t not in DROP_TOKENS]
    return " ".join(toks)


def origin_surface(row: dict[str, str]) -> str:
    origin = row.get("PrimaryOriginKey", "").strip()
    marker = "|new::"
    if marker not in origin:
        return ""
    tail = origin.split(marker, 1)[1]
    return tail.split("::", 1)[0].strip()


def properish(value: str) -> bool:
    # Multi-token title/place candidates only; this is candidate generation, not a merge decision.
    toks = words(value)
    return len(toks) >= 2 and any(c.isupper() for c in value)


def risk_signals(left: dict[str, str], right: dict[str, str]) -> tuple[list[str], int]:
    lm = norm(left.get("MatchKey", ""))
    rm = norm(right.get("MatchKey", ""))
    lo = norm(origin_surface(left))
    signals: list[str] = []
    score = 0

    if lm and lm == rm:
        signals.append("same-surface")
        score = max(score, 78)
    if lo and lo == rm and lm != rm:
        signals.append("allocation-origin-surface-match")
        score = max(score, 100)
    if lm != rm and orth_key(lm) and orth_key(lm) == orth_key(rm):
        signals.append("orthographic-equivalent")
        score = max(score, 94)
    if lm != rm and lemma_key(lm) and lemma_key(lm) == lemma_key(rm):
        signals.append("morphology-equivalent")
        score = max(score, 92)

    ls = phrase_skeleton(lm)
    rs = phrase_skeleton(rm)
    if lm != rm and ls and ls == rs and len(ls.split()) >= 2:
        signals.append("phrase-determiner-or-inflection-variant")
        score = max(score, 90)

    ok_l, ok_r = orth_key(lm), orth_key(rm)
    if lm != rm and ok_l and ok_r:
        ratio = SequenceMatcher(None, ok_l, ok_r).ratio()
        lt, rt = set(ok_l.split()), set(ok_r.split())
        overlap = len(lt & rt) / max(1, len(lt | rt))
        if ratio >= 0.90 and overlap >= 0.5:
            signals.append("high-form-overlap")
            score = max(score, 82)
        if (
            left.get("SenseLabel", "").strip() == right.get("SenseLabel", "").strip()
            and properish(left.get("CanonicalWord", ""))
            and properish(right.get("CanonicalWord", ""))
            and overlap >= 0.25
        ):
            signals.append("proper-name-same-gloss-overlap")
            score = max(score, 80)

    return signals, score


def main() -> None:
    for p in REGISTRIES:
        if not p.exists():
            raise SystemExit(f"Missing registry: {p.relative_to(ROOT)}")

    registry = [r for p in REGISTRIES for r in read_csv(p)]
    active = [r for r in registry if r.get("Status", "").strip() == "active"]
    incoming = [
        r for r in registry
        if r.get("CreatedSource", "").strip() == GRADE56_SOURCE
        and r.get("Status", "").strip() in {"active", "merged"}
    ]
    baseline = [r for r in active if r.get("CreatedSource", "").strip() != GRADE56_SOURCE]

    if len(incoming) != 293:
        raise SystemExit(f"Expected 293 allocated Grade 5-6 identities, got {len(incoming)}")
    if len(baseline) != 901:
        raise SystemExit(f"Expected 901 pre-existing identities, got {len(baseline)}")

    out: list[dict[str, str]] = []
    signal_counts: Counter[str] = Counter()
    cid = 0

    def add_pair(scope: str, left: dict[str, str], right: dict[str, str]) -> None:
        nonlocal cid
        signals, score = risk_signals(left, right)
        if score < 78:
            return
        cid += 1
        for s in signals:
            signal_counts[s] += 1
        out.append({
            "CandidateID": f"G56D{cid:04d}",
            "Scope": scope,
            "NewNoteID": left["NoteID"].strip(),
            "OtherNoteID": right["NoteID"].strip(),
            "NewWord": left.get("CanonicalWord", "").strip(),
            "NewMatchKey": left.get("MatchKey", "").strip(),
            "NewSense": left.get("SenseLabel", "").strip(),
            "NewOriginSurface": origin_surface(left),
            "OtherWord": right.get("CanonicalWord", "").strip(),
            "OtherMatchKey": right.get("MatchKey", "").strip(),
            "OtherSense": right.get("SenseLabel", "").strip(),
            "OtherCreatedSource": right.get("CreatedSource", "").strip(),
            "Signals": "|".join(signals),
            "RiskScore": str(score),
            "ReviewStatus": "pending",
            "Decision": "",
            "MergeIntoNoteID": "",
            "Rationale": "",
        })

    for left in incoming:
        for right in baseline:
            add_pair("new-vs-existing", left, right)

    for i, left in enumerate(incoming):
        for right in incoming[:i]:
            add_pair("new-vs-new", left, right)

    # Deterministic highest-risk-first review order.
    out.sort(key=lambda r: (-int(r["RiskScore"]), r["NewNoteID"], r["OtherNoteID"]))
    for i, row in enumerate(out, 1):
        row["CandidateID"] = f"G56D{i:04d}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CANDIDATES.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)

    status = {
        "BaselineStableIdentities": len(baseline),
        "AllocatedGrade56Identities": len(incoming),
        "CartesianPairsAvoided": len(incoming) * len(baseline) + (len(incoming) * (len(incoming) - 1) // 2) - len(out),
        "CandidatePairs": len(out),
        "NewVsExisting": sum(r["Scope"] == "new-vs-existing" for r in out),
        "NewVsNew": sum(r["Scope"] == "new-vs-new" for r in out),
        "SignalCounts": dict(sorted(signal_counts.items())),
        "PendingReview": len(out),
        "MasterMutation": False,
        "ReleaseMutation": False,
        "AnkiMutation": False,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
