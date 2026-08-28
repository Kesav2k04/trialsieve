"""Build the vendored candidate panel from the Synthea sample archive.

Run once. The output is committed, so a judge reproduces from the repository and
never downloads 94 MB or parses 1.1 GB of FHIR.

    python scripts/build_panel.py --zip data/raw/synthea_r4.zip

There is no patient selection beyond two facts about the record: the patient is
alive, and the patient is an adult at their index date. Every remaining patient
in the archive is in the panel. Sampling would raise the question of what the
sample was chosen to show, and refusing to sample is cheaper than answering it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialsieve.chart import chart_to_dict, load_chart  # noqa: E402

EXPECTED_SHA256 = "6d3c5433bcae4791bc5c30469d1445b430fb4894d5c13bda15fee0584bbd7778"
SOURCE_URL = ("https://synthetichealth.github.io/synthea-sample-data/downloads/"
              "synthea_sample_data_fhir_r4_nov2021.zip")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="data/raw/synthea_r4.zip")
    ap.add_argument("--out", default="data/vendor/panel.jsonl.gz")
    ap.add_argument("--work", default="data/work/synthea")
    ap.add_argument("--min-age", type=int, default=18)
    a = ap.parse_args()

    digest = sha256(a.zip)
    if digest != EXPECTED_SHA256:
        print(f"WARNING: archive sha256 is {digest}, expected {EXPECTED_SHA256}.\n"
              f"         The panel will not match the committed one.", file=sys.stderr)

    src = Path(a.work) / "fhir"
    if not src.exists():
        print(f"extracting {a.zip} ...", flush=True)
        with zipfile.ZipFile(a.zip) as z:
            z.extractall(a.work)

    files = sorted(f for f in os.listdir(src)
                   if f.endswith(".json") and not f.startswith(("hospital", "practitioner")))

    kept, skipped_dead, skipped_minor = [], 0, 0
    for i, f in enumerate(files):
        c = load_chart(str(src / f))
        if c.deceased_date is not None:
            skipped_dead += 1
            continue
        if c.age is None or c.age < a.min_age:
            skipped_minor += 1
            continue
        c.source_file = f
        kept.append(c)
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{len(files)}", flush=True)

    # Sort by patient id so the committed file order does not depend on the
    # filesystem, which orders differently on Windows and Linux.
    kept.sort(key=lambda c: c.patient_id)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    for c in kept:
        buf.write(json.dumps(chart_to_dict(c), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")))
        buf.write("\n")
    raw = buf.getvalue().encode("utf-8")
    # mtime=0 so the archive is byte-identical across runs.
    with open(a.out, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", compresslevel=9, mtime=0) as gz:
            gz.write(raw)

    prov = {
        "source_url": SOURCE_URL,
        "archive_sha256": digest,
        "archive_bytes": os.path.getsize(a.zip),
        "licence": "Apache-2.0 (Synthea synthetic data, no real patients)",
        "bundles_in_archive": len(files),
        "excluded_deceased": skipped_dead,
        "excluded_under_18": skipped_minor,
        "panel_size": len(kept),
        "selection_rule": f"alive at index date and age >= {a.min_age}; no other selection",
        "panel_sha256": hashlib.sha256(raw).hexdigest(),
        "panel_bytes_uncompressed": len(raw),
    }
    Path("data/vendor/panel_provenance.json").write_text(
        json.dumps(prov, indent=1) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps(prov, indent=1))
    print(f"\nwrote {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB compressed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
