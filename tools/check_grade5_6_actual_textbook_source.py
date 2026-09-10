#!/usr/bin/env python3
"""Compatibility entry point for the Grade 5–6 actual-textbook Source gate."""
from __future__ import annotations

import json
from pathlib import Path

from check_grade5_6_actual_textbook_source_resolved import main as check_source

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "anki" / "klose" / "source_reference"


def main() -> None:
    check_source()
    config = json.loads((SRC / "grade5_6_source_provenance.json").read_text(encoding="utf-8"))
    if config.get("ResolutionState") == "applied":
        manifest = (SRC / "grade5_6_actual_textbook_manifest.csv").read_text(encoding="utf-8-sig").casefold()
        if "source identity pending confirmation" in manifest or "source identity pending-confirmation" in manifest:
            raise SystemExit("Grade 5–6 actual-source FAIL: stale pending-provenance text remains in resolved manifest")


if __name__ == "__main__":
    main()
