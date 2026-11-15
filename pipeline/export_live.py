# SPOT pipeline - export the small static files that let the website build ANY field live in the browser.
# Written with AI assistance under the direction of Ali (team AITHMAC).
#   site/data/live/index.json    one row per SPHEREx visit: folder, visit no., D2/exp-1 centre, time, angle
#   site/data/live/geometry.json affine maps from D2/exp-1 pixels to the pixels of every (exposure, detector)
#   site/data/live/wave.json     pixel->wavelength node tables for the 6 detectors (identical in every file)
import json
import random
import sys
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import s3index as S

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "live"
OUT.mkdir(parents=True, exist_ok=True)


def tan_wcs(h):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [h["CRVAL1"], h["CRVAL2"]]
    w.wcs.crpix = [h["CRPIX1"], h["CRPIX2"]]
    w.wcs.pc = [[h["PC1_1"], h["PC1_2"]], [h["PC2_1"], h["PC2_2"]]]
    return w


def phi_of(h):
    return float(np.degrees(np.arctan2(h["PC1_2"], h["PC1_1"])))


def geometry(n_visits=12):
    """Fit, for each (exposure 1-4, detector 1-3), an affine map from D2/exp-1 pixel coords to that
    frame's pixel coords, using real headers (TAN without SIP on both sides). Report scatter."""
    dirs = S.week_dirs()
    random.seed(1)
    picks = []
    for d in random.sample(dirs, n_visits):
        rows = S.dir_keys(d)
        visits = sorted({r["visit"] for r in rows})
        v = random.choice(visits[10:-10])
        sel = {(r["exp"], r["det"]): r["key"] for r in rows if r["visit"] == v and r["det"] in "123"}
        if len(sel) == 12:
            picks.append(sel)
    fits_ = {}
    scales, crp = [], []
    for sel in picks:
        hs = {k: S.read_header(key) for k, key in sel.items()}
        ref = hs[("1", "2")]
        wr = tan_wcs(ref)
        scales.append(float(np.sqrt(abs(np.linalg.det(np.array([[ref["PC1_1"], ref["PC1_2"]], [ref["PC2_1"], ref["PC2_2"]]]))))))
        crp.append(ref["CRPIX1"])
        # reference PC rebuilt from (scale, phi) exactly as the browser does
        k, ph = scales[-1], np.radians(phi_of(ref))
        wr2 = WCS(naxis=2)
        wr2.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        wr2.wcs.crval = [ref["CRVAL1"], ref["CRVAL2"]]
        wr2.wcs.crpix = [ref["CRPIX1"], ref["CRPIX2"]]
        wr2.wcs.pc = [[k * np.cos(ph), k * np.sin(ph)], [k * np.sin(ph), -k * np.cos(ph)]]
        for (e, dd), h in hs.items():
            w = tan_wcs(h)
            xs, ys = np.meshgrid(np.linspace(0, 2039, 6), np.linspace(0, 2039, 6))
            sky = w.pixel_to_world_values(xs.ravel(), ys.ravel())
            X, Y = wr2.world_to_pixel_values(*sky)
            fits_.setdefault((e, dd), []).append((np.c_[X, Y], np.c_[xs.ravel(), ys.ravel()]))
    frames = []
    report = []
    for (e, dd), lst in sorted(fits_.items()):
        A = np.vstack([np.c_[p[:, 0], p[:, 1], np.ones(len(p))] for p, _ in lst])
        bx = np.concatenate([q[:, 0] for _, q in lst])
        by = np.concatenate([q[:, 1] for _, q in lst])
        cx, *_ = np.linalg.lstsq(A, bx, rcond=None)
        cy, *_ = np.linalg.lstsq(A, by, rcond=None)
        res = np.hypot(A @ cx - bx, A @ cy - by)
        frames.append({"exp": int(e), "det": int(dd), "a": [round(float(v), 6) for v in (*cx, *cy)]})
        report.append(f"exp{e} D{dd}: median resid {np.median(res):.1f}px, max {res.max():.1f}px (n={len(lst)} visits)")
    geo = {"scale_deg": float(np.median(scales)), "crpix": float(np.median(crp)), "margin": 120, "frames": frames,
           "note": "Affine maps D2/exp-1 pixel (0-based) -> (exp, det) pixel; detectors 4-6 share the sky of 1-3."}
    return geo, report, Counter(crp)


def wave_tables():
    """Evaluate each detector's spectral WCS at its 11x11 table nodes (0-based pixel = node - 1)."""
    out = {}
    d0 = S.week_dirs()[-3]
    rows = S.dir_keys(d0)
    for det in "123456":
        key = next(r["key"] for r in rows if r["det"] == det and r["exp"] == "1")
        with fits.open(S.BUCKET + key, use_fsspec=True, fsspec_kwargs={"block_size": 512 * 1024}) as h:
            hd = h[1].header
            sw = WCS(hd, fobj=h, key="W")
            sw.sip = None
            nodes = [int(v) - 1 for v in h["WCS-WAVE"].data["X"][0]]
            ny = [int(v) - 1 for v in h["WCS-WAVE"].data["Y"][0]]
            xx, yy = np.meshgrid(nodes, ny)  # rows = y, cols = x
            wl, bw = sw.pixel_to_world(xx, yy)
            wl, bw = wl.to("um").value, bw.to("um").value
            # check bilinear interpolation of nodes against astropy at random pixels
            rx, ry = np.random.uniform(0, 2039, 200), np.random.uniform(0, 2039, 200)
            tw, _ = sw.pixel_to_world(rx, ry)
            from scipy.interpolate import RegularGridInterpolator
            it = RegularGridInterpolator((ny, nodes), wl)  # (y, x)
            err = np.abs(it(np.c_[ry, rx]) - tw.to("um").value).max()
            out[det] = {"nodes_x": nodes, "nodes_y": ny, "wl": np.round(wl, 5).tolist(), "bw": np.round(bw, 5).tolist(),
                        "check_max_err_um": float(err), "from": key}
            print(f"D{det}: wl {wl.min():.3f}-{wl.max():.3f} um; bilinear check max err {err:.2e} um", flush=True)
    return out


def index():
    dirs = S.week_dirs()
    folders, rows = [], []
    mjd0 = None
    for fi, d in enumerate(dirs):
        samp = S.CACHE / f"sample_{d.strip('/').replace('/', '_')}_e1_d2_n1.json"
        if not samp.exists():
            print("missing index for", d)
            continue
        s = json.loads(samp.read_text())
        keys = S.dir_keys(d)
        vers = Counter(r["ver"] for r in keys)
        ver = vers.most_common(1)[0][0]
        exc = {f"{r['visit']}_{r['exp']}_{r['det']}": r["ver"] for r in keys if r["ver"] != ver}
        rel, _, week = d.strip("/").split("/")
        folders.append({"rel": rel, "week": week, "ver": ver, "exc": exc})
        fidx = len(folders) - 1
        masks = {}
        for r in keys:  # bit (exp-1)*6 + (det-1) set if that file exists
            masks[r["visit"]] = masks.get(r["visit"], 0) | (1 << ((int(r["exp"]) - 1) * 6 + int(r["det"]) - 1))
        for x in s:
            if mjd0 is None:
                mjd0 = int(x["MJD-OBS"])
            ra, dec = tan_wcs(x).pixel_to_world_values(x["CRPIX1"] - 1, x["CRPIX2"] - 1)
            visit = int(x["key"].split("/")[-1].split("_")[3])
            rows.append([fidx, visit, int(round(float(ra) * 1e4)), int(round(float(dec) * 1e4)),
                         int(round((x["MJD-OBS"] - mjd0) * 1e3)), int(round(phi_of(x) * 100)),
                         masks.get(f"{visit:04d}", (1 << 24) - 1)])
    return {"mjd0": mjd0, "folders": folders, "rows": rows,
            "note": "Row = [folder, visit, RA*1e4, Dec*1e4 of D2/exp-1 reference pixel, (MJD-mjd0)*1e3, PC angle*100, existing-files bitmask: bit (exp-1)*6+(det-1)]"}


if __name__ == "__main__":
    what = sys.argv[1:] or ["geometry", "wave", "index"]
    if "geometry" in what:
        geo, rep, crp = geometry()
        print("\n".join(rep)); print("CRPIX values:", crp)
        (OUT / "geometry.json").write_text(json.dumps(geo))
    if "wave" in what:
        (OUT / "wave.json").write_text(json.dumps(wave_tables()))
    if "index" in what:
        idx = index()
        (OUT / "index.json").write_text(json.dumps(idx, separators=(",", ":")))
        print(len(idx["rows"]), "visits;", len(idx["folders"]), "folders;", (OUT / "index.json").stat().st_size // 1024, "KB")
