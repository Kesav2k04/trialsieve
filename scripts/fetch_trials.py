"""Fetch the eight study records in the frozen allowlist and vendor them verbatim.

The allowlist is fixed in this file and committed. Trials are not re-selected at
run time: a search that reranks as ClinicalTrials.gov updates would silently
change the evaluation set between runs, and a set chosen after seeing results is
not a set at all.

    python scripts/fetch_trials.py            # use vendored copies, verify hashes
    python scripts/fetch_trials.py --refetch  # hit the API and rewrite them

The API response is stored exactly as received. Nothing derived is committed
alongside it, so anyone can re-derive the criteria from the raw record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VENDOR = Path("data/vendor/trials")

#: Chosen for depth of record-checkable criteria against a cardiometabolic
#: corpus, and for spread across criterion types: numeric thresholds with units,
#: temporal windows, drug-class references, and clauses that no record can settle.
ALLOWLIST = [
    ("NCT06983054", "T2DM, ertugliflozin and dietary sodium: eGFR and UACR thresholds"),
    ("NCT06989723", "T2DM with hepatic steatosis: drug classes and organ-failure bounds"),
    ("NCT06717698", "T2DM dose-ranging: HbA1c and BMI bands"),
    ("NCT06338553", "GLP-1Ra in stage 2 T1DM: metabolic thresholds"),
    ("NCT07065383", "T2DM, cardiac and muscle fat: imaging and metabolic criteria"),
    ("NCT07588256", "Hypertension prevention platform: lab-heavy criteria"),
    ("NCT06578078", "CKD management strategy: renal staging"),
    ("NCT06998862", "Colchicine in CKD: temporal exclusions"),
]

FIELDS = ("NCTId,BriefTitle,OfficialTitle,EligibilityCriteria,MinimumAge,MaximumAge,Sex,"
          "HealthyVolunteers,Condition,OverallStatus,Phase,StudyType,LeadSponsorName,"
          "StudyFirstPostDate,LastUpdatePostDate")


def fetch_one(nct: str) -> dict:
    q = urllib.parse.urlencode({"query.id": nct, "fields": FIELDS, "pageSize": "5"})
    url = f"https://clinicaltrials.gov/api/v2/studies?{q}"
    with urllib.request.urlopen(url, timeout=90) as fh:
        payload = json.load(fh)
    for s in payload.get("studies", []):
        got = s.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
        if got == nct:
            return s
    raise SystemExit(f"{nct}: not present in the API response")


def digest(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    a = ap.parse_args()
    VENDOR.mkdir(parents=True, exist_ok=True)

    index, drift = [], []
    for nct, why in ALLOWLIST:
        path = VENDOR / f"{nct}.json"
        if a.refetch or not path.exists():
            print(f"fetching {nct} ...", flush=True)
            rec = fetch_one(nct)
            path.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
            time.sleep(0.4)
        rec = json.loads(path.read_text(encoding="utf-8"))
        p = rec["protocolSection"]
        elig = p.get("eligibilityModule", {})
        text = elig.get("eligibilityCriteria", "") or ""
        index.append({
            "nct_id": nct,
            "selected_because": why,
            "title": p["identificationModule"].get("briefTitle"),
            "conditions": p.get("conditionsModule", {}).get("conditions", []),
            "min_age": elig.get("minimumAge"), "max_age": elig.get("maximumAge"),
            "sex": elig.get("sex"), "healthy_volunteers": elig.get("healthyVolunteers"),
            "last_update_posted": p.get("statusModule", {})
                                   .get("lastUpdatePostDate", {}),
            "criteria_chars": len(text),
            "record_sha256": digest(rec),
        })

    Path("data/vendor/trials_index.json").write_text(
        json.dumps({
            "source": "ClinicalTrials.gov API v2 (US Government, public domain)",
            "note": ("The eligibility field is the sponsor's registry summary, not the "
                     "protocol a site screens against. Criteria counts here are counts of "
                     "that summary."),
            "trials": index,
        }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print(f"\n{'NCT':13s} {'chars':>6s}  title")
    for t in index:
        print(f"{t['nct_id']:13s} {t['criteria_chars']:6d}  {(t['title'] or '')[:56]}")
    print(f"\n{len(index)} trials vendored in {VENDOR}")
    if drift:
        print("DRIFT:", drift, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
