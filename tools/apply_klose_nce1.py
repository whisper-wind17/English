"""Derive NCE1 Master/Learner/provenance from reviewed persistent identities."""
from __future__ import annotations
import csv
from collections import defaultdict
from klose_nce1_state import BASE, SOURCE_ID, EDITION, read, reviewed_state

def write(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def pipe(value, item):
    return "|".join(dict.fromkeys([p for p in value.split("|") if p] + [item]))

def main():
    source, decisions, proposed = reviewed_state()
    by_order = {int(r["CurriculumOrder"]): r for r in source}
    master_path = BASE / "master/vocabulary_master.csv"; learner_path = BASE / "learner/current.csv"
    master = read(master_path); learner = read(learner_path)
    mf, lf = list(master[0]), list(learner[0])
    mb, lb = {r["NoteID"]: r for r in master}, {r["NoteID"]: r for r in learner}
    for nid, row in proposed.items():
        if nid in mb or nid in lb:
            raise SystemExit(f"NCE1 overlay must follow a fresh upstream rebuild: {nid}")
        src = by_order[int(row["Order"])]
        m = dict.fromkeys(mf, "")
        m.update({k:row[k] for k in ("NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "British", "American", "MeaningPrimary")})
        m.update(Word=row["CanonicalWord"], MeaningRaw=src["Meaning"], FirstSource=SOURCE_ID,
                 FirstSourceBook=EDITION+"::Book1", FirstGrade="", FirstSemester="", Sources=SOURCE_ID,
                 SourceBooks=SOURCE_ID+"::"+EDITION+"::Book1", Released="no",
                 Tags="source::"+SOURCE_ID+" learner::klose::level::4")
        l = dict.fromkeys(lf, "")
        l.update({k:row[k] for k in ("NoteID", "LearnerProfile", "LearnerLevel", "ExampleSentence", "ExampleTranslation")})
        l.update(PresentationStatus="nce1-curated-pending-review", PresentationSource=("nce1:batch001" if int(row["Order"])<=150 else "nce1:full-book-reviewed"))
        master.append(m); learner.append(l); mb[nid]=m; lb[nid]=l
    occurrences_path = BASE / "master/source_occurrences.csv"
    occurrences=read(occurrences_path); of=list(occurrences[0])
    if any(r.get("SourceID")==SOURCE_ID for r in occurrences):
        raise SystemExit("NCE1 occurrences already exist before source overlay")
    for dec in decisions.values():
        nid=dec["NoteID"]; src=by_order[int(dec["CurriculumOrder"])]
        if nid not in mb or nid not in lb: raise SystemExit(f"Missing NCE1 reuse target in Master: {nid}")
        m=mb[nid]
        m["Sources"]=pipe(m["Sources"],SOURCE_ID)
        m["SourceBooks"]=pipe(m["SourceBooks"],SOURCE_ID+"::"+EDITION+"::Book1")
        m["Tags"]=" ".join(sorted(set(m["Tags"].split()) | {"source::"+SOURCE_ID,"source::"+SOURCE_ID+"::edition::"+EDITION}))
        occurrences.append(dict(NoteID=nid,SourceID=SOURCE_ID,SourceEdition=EDITION,SourceBook="Book1",Grade="",Semester="",
          Unit=src["LessonStart"],SourceWord=src["Entry"],SourceFile="new_concept_english_1_staging/vocabulary-smart-2022.csv",
          SourceRow=str(int(src["CurriculumOrder"])+1),Page=""))
    master.sort(key=lambda r:r["NoteID"]); learner.sort(key=lambda r:r["NoteID"])
    occurrences.sort(key=lambda r:(r["NoteID"],r["SourceID"],r.get("SourceEdition",""),r["SourceBook"],int(r["SourceRow"] or 0)))
    write(master_path,mf,master);write(learner_path,lf,learner);write(occurrences_path,of,occurrences)
    stats_path=BASE/"master/build_stats.csv";stats=read(stats_path)
    values={"master_notes":len(master),"inventory_notes":len(master),"source_occurrences":len(occurrences),
            "nce1_reviewed_occurrences":len(decisions),"nce1_new_notes":len(proposed)}
    for key,value in values.items():
        found=next((r for r in stats if r["Metric"]==key),None)
        if found is None:stats.append(dict(Metric=key,Value=str(value)))
        else:found["Value"]=str(value)
    write(stats_path,["Metric","Value"],stats)
    print(f"NCE1 overlay: {len(decisions)} reviewed source rows; {len(proposed)} new stable units; no scheduling writes")
if __name__ == "__main__":main()
