#!/usr/bin/env python3
"""Shared learner-presentation fingerprint for Klose Expressions."""
from __future__ import annotations

import hashlib

VERSION = "expression-presentation-v1"
FIELDS = (
    "LearnerProfile",
    "LearnerLevel",
    "ExpressionID",
    "Prompt",
    "PromptHint",
    "Target",
    "Pattern",
    "MeaningUsage",
    "Examples",
    "FunctionLabel",
    "ContextNote",
)


def fingerprint(row: dict[str, str]) -> str:
    payload = "\x1f".join((row.get(field, "") or "").strip() for field in FIELDS)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
