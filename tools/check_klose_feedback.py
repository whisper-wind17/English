"""Validate observational records without inventing learning history."""
from __future__ import annotations
import csv
import math
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'anki/klose/feedback'


def rows(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    observations = rows('observations.csv')
    for row in observations:
        if date.fromisoformat(row['PeriodEnd']) < date.fromisoformat(row['PeriodStart']):
            raise SystemExit('Observation period is reversed')
        if not row['Source'].strip() or not row['Observation'].strip():
            raise SystemExit('Observation requires an actual source and explanation')
        for field in ('ReviewMinutesPerDay', 'BacklogCards', 'AgainRatio', 'TransferTrials', 'TransferSuccesses'):
            if row[field] and (not math.isfinite(float(row[field])) or float(row[field]) < 0):
                raise SystemExit(f'Invalid numeric observation: {field}')
        if row['AgainRatio'] and float(row['AgainRatio']) > 1:
            raise SystemExit('AgainRatio must be 0..1')
        if row['TransferSuccesses'] and (not row['TransferTrials'] or float(row['TransferSuccesses']) > float(row['TransferTrials'])):
            raise SystemExit('Transfer successes exceed recorded trials')
    seen = set()
    for row in rows('decisions.csv'):
        if not row['DecisionID'] or row['DecisionID'] in seen or not row['EvidenceRef']:
            raise SystemExit('Learning decision needs unique identity and evidence')
        seen.add(row['DecisionID'])
        date.fromisoformat(row['Date'])
        if row['Status'] not in {'proposed', 'applied', 'verified'}:
            raise SystemExit('Invalid learning decision state')
    print(f'Learning feedback records valid: observations={len(observations)}; effectiveness={"recorded-not-automatically-proven" if observations else "not-yet-observed"}')


if __name__ == '__main__':
    main()
