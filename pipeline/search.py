# SPOT pipeline - find every SPHEREx frame covering a sky position, using the S3 pointing index.
# Written with AI assistance under the direction of Ali (team AITHMAC).
#
# Step 1 (coarse): the sampled index (every 10th visit, detector 2, exposure 1) tells which week
#   folders point near the target at all.
# Step 2 (fine): in those folders, read the header of exposure 1 / detector 2 of every visit.
# Step 3 (exact): for visits whose detector-2 centre is within ~8 deg, read the headers of all
#   4 exposures x 6 detectors and keep the files whose pixel grid contains the target.
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from astropy.wcs import WCS

import s3index as S

CACHE = Path(__file__).resolve().parent.parent / "cache"


def radec_center(h):
    return float(h["CRVAL1"]), float(h["CRVAL2"])  # tangent point ~ array centre region


def angsep(ra1, dec1, ra2, dec2):
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    c = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def center_of(summary):
    """Sky position of the array centre pixel from a header summary (TAN, no SIP: fine for search)."""
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [summary["CRVAL1"], summary["CRVAL2"]]
    w.wcs.crpix = [summary["CRPIX1"], summary["CRPIX2"]]
    w.wcs.pc = [[summary["PC1_1"], summary["PC1_2"]], [summary["PC2_1"], summary["PC2_2"]]]
    c = w.pixel_to_world_values(1019.5, 1019.5)
    return float(c[0]), float(c[1])


def coarse_dirs(ra, dec, max_deg=25.0):
    out = []
    for d in S.week_dirs():
        s = S.sample_dir(d, every=10)
        if not s:
            continue
        cen = np.array([center_of(x) for x in s])
        sep = angsep(ra, dec, cen[:, 0], cen[:, 1])
        if sep.min() < max_deg:
            out.append((d, float(sep.min())))
    return out


def contains(h, ra, dec, margin=2):
    w = WCS(h)
    x, y = w.world_to_pixel_values(ra, dec)
    return (margin <= x < 2040 - margin) and (margin <= y < 2040 - margin), float(x), float(y)


def find_frames(ra, dec, name, coarse_deg=25.0, fine_deg=8.0, workers=16, log=print):
    out = CACHE / f"search_{name}.json"
    if out.exists():
        return json.loads(out.read_text())
    t0 = time.time()
    # Full visit index: detector-2 / exposure-1 header of EVERY visit in every folder (cached).
    # (An earlier coarse pre-filter based on every 10th visit missed whole folders; removed.)
    near_visits = []
    for d in S.week_dirs():
        s = S.sample_dir(d, every=1)
        if not s:
            continue
        cra = np.array([x["CRVAL1"] for x in s])  # CRPIX is the array centre (1020.5)
        cde = np.array([x["CRVAL2"] for x in s])
        for i in np.where(angsep(ra, dec, cra, cde) < fine_deg)[0]:
            near_visits.append((d, s[i]["key"]))
    log(f"[{name}] fine: {len(near_visits)} visits with detector-2 centre within {fine_deg} deg ({time.time()-t0:.0f}s)")
    # all exposures x detectors of those visits
    cand = []
    for d, k in near_visits:
        visit = k.split("/")[-1].split("_")[3]
        for r in S.dir_keys(d):
            if r["visit"] == visit:
                cand.append(r["key"])
    log(f"[{name}] exact: checking {len(cand)} files")

    def check(key):
        h = S.read_header(key)
        if h is None:
            return None
        ok, x, y = contains(h, ra, dec)
        if not ok:
            return None
        return {"key": key, "x": x, "y": y, "mjd": float(h["MJD-OBS"]), "det": int(h["DETECTOR"]),
                "obsid": h["OBSID"]}

    with ThreadPoolExecutor(workers) as ex:
        hits = [h for h in ex.map(check, cand) if h]
    hits.sort(key=lambda r: (r["mjd"], r["det"]))
    out.write_text(json.dumps(hits, indent=0))
    log(f"[{name}] {len(hits)} files contain the target ({time.time()-t0:.0f}s)")
    return hits


if __name__ == "__main__":
    ra, dec, name = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    hits = find_frames(ra, dec, name)
    from collections import Counter
    print(Counter(h["det"] for h in hits))
    print(Counter(h["key"].split("/")[2] for h in hits))
