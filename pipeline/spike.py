# SPOT - Phase 1 data spike (G1).
# Written with AI assistance under the direction of Ali (team AITHMAC).
# One sky position (IRSA tutorial example, M101 area, RA 210.80227 Dec 54.34895), frames from 2+ dates
# at the same wavelength, aligned to one north-up grid, saved as PNGs + one JSON line of provenance each.
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from s3index import dir_keys
from frames import extract_many, target_grid, clean_and_reproject

RA, DEC, NAME = 210.80227, 54.34895, "spike_m101"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cache" / "spike"
OUT.mkdir(parents=True, exist_ok=True)

# Files that IRSA's own tutorial lists as covering this position (from its printed output).
KNOWN = [l.strip().removeprefix("spherex/") for l in open(sys.argv[1]) if "D2_" in l]


def siblings(key):
    """All 4 exposures of the same visit, on D2 and D5 (D5 sees the same sky as D2)."""
    rel, _, week = key.split("/")[:3]
    visit = key.split("_")[-4] if False else key.split("/")[-1].split("_")[3]
    rows = dir_keys(f"{rel}/level2/{week}/")
    return [r["key"] for r in rows if r["visit"] == visit and r["det"] in ("2", "5")]


keys = sorted({k for kk in KNOWN for k in siblings(kk)})
print(len(KNOWN), "known ->", len(keys), "candidate frames", flush=True)
metas = extract_many(keys, RA, DEC, NAME, half=60)
print(len(metas), "frames contain the target", flush=True)

# epochs: gap > 60 days starts a new epoch
metas.sort(key=lambda m: m["mjd"])
ep, last = 0, None
for m in metas:
    if last is None or m["mjd"] - last > 60:
        ep += 1
    m["epoch"] = ep
    last = m["mjd"]
for m in metas:
    print(m["epoch"], m["utc"], "D%d" % m["detector"], f"{m['wavelength_um']:.4f}um bw={m['bandwidth_um']:.4f}",
          f"bad={m['bad_fraction']:.3f}", m["release"])

# best wavelength-matched pair(s) across different epochs, same detector
best = []
for i, a in enumerate(metas):
    for b in metas[i + 1:]:
        if a["epoch"] == b["epoch"] or a["detector"] != b["detector"]:
            continue
        d = abs(a["wavelength_um"] - b["wavelength_um"])
        tol = 0.5 * min(a["bandwidth_um"], b["bandwidth_um"])
        if d < tol:
            best.append((d / tol, a, b))
best.sort(key=lambda t: t[0])
print(len(best), "matched cross-epoch pairs")
if not best:
    sys.exit("NO MATCHED PAIR")

# build a channel around the best pair: all frames within half-bandwidth of the pair's mean wavelength
_, a, b = best[0]
lam = 0.5 * (a["wavelength_um"] + b["wavelength_um"])
chan = [m for m in metas if m["detector"] == a["detector"] and abs(m["wavelength_um"] - lam) < 0.5 * m["bandwidth_um"]]
# one frame per epoch (closest in wavelength)
per_ep = {}
for m in chan:
    if m["epoch"] not in per_ep or abs(m["wavelength_um"] - lam) < abs(per_ep[m["epoch"]]["wavelength_um"] - lam):
        per_ep[m["epoch"]] = m
chan = [per_ep[e] for e in sorted(per_ep)]
print("channel", f"{lam:.4f}um", [(m["epoch"], m["utc"], round(m["wavelength_um"], 4)) for m in chan])

gw, shape = target_grid(RA, DEC, 0.2)
ims = [clean_and_reproject(m, NAME, gw, shape)[0] for m in chan]
allv = np.concatenate([im[np.isfinite(im)] for im in ims])
lo, hi = np.percentile(allv, [1, 99.7])  # one shared stretch for the whole channel
with open(OUT / "provenance.jsonl", "w") as f:
    for m, im in zip(chan, ims):
        z = np.clip((np.nan_to_num(im, nan=lo) - lo) / (hi - lo), 0, 1)
        z = np.arcsinh(10 * z) / np.arcsinh(10)
        png = OUT / f"{NAME}_ep{m['epoch']}.png"
        Image.fromarray((z[::-1] * 255).astype(np.uint8)).resize((shape[1] * 4, shape[0] * 4), Image.NEAREST).save(png)
        rec = {k: m[k] for k in ("utc", "epoch", "detector", "wavelength_um", "bandwidth_um", "release", "version",
                                 "source_uri", "obsid", "bad_fraction")}
        rec["png"] = png.name
        f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec))
np.save(OUT / "aligned_stack.npy", np.array(ims))
print("stretch", lo, hi)
