#!/usr/bin/env python3
"""Shared Klose learner-presentation fingerprint.

Compatibility rule: an empty PromptHint must preserve the existing v2 fingerprint.
A non-empty PromptHint is release-visible front-side content, so it extends the
fingerprint and invalidates prior approval for that Note only.
"""
from __future__ import annotations

import hashlib


def fingerprint(master: dict[str, str], learner: dict[str, str]) -> str:
    payload = "\x1f".join([
        "klose-presentation-v2",
        master.get("CanonicalWord", "").strip(),
        master.get("SenseLabel", "").strip(),
        master.get("Word", "").strip(),
        master.get("British", "").strip(),
        master.get("American", "").strip(),
        master.get("MeaningPrimary", "").strip(),
        learner.get("ExampleSentence", "").strip(),
        learner.get("ExampleTranslation", "").strip(),
        learner.get("LearnerProfile", "").strip(),
        learner.get("LearnerLevel", "").strip(),
    ])
    prompt_hint = learner.get("PromptHint", "").strip()
    if prompt_hint:
        payload += "\x1fPromptHint=" + prompt_hint
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
