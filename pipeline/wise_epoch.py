# SPOT pipeline - an older epoch from NASA's WISE mission (AllWISE Atlas, W2 = 4.6 um), on a field's exact grid.
# Written with AI assistance under the direction of Ali (team AITHMAC).
#
# AllWISE Atlas images are mirrored in IRSA's public AWS bucket `nasa-irsa-wise` (us-west-2):
#   wise/allwise/images/p3am_cdd/RR/RRRR/<coadd_id>/<coadd_id>-w2-int-3.fits
# coadd_id = RRRR[p|m]DDD_ac51, tile centre RA = RRRR/10 deg, Dec = +/-DDD/10 deg; tiles are 1.56 deg square.
# (IRSA's image search API and CDS hips2fits were unavailable on November 15, 2026, so we locate the
# tile from the bucket's folder names.)
import json
import re
import sys
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_adaptive

BUCKET = "https://nasa-irsa-wise.s3.us-west-2.amazonaws.com/"
PREFIX = "wise/allwise/images/p3am_cdd/"
CACHE = Path(__file__).resolve().parent.parent / "cache" / "wise"
CACHE.mkdir(parents=True, exist_ok=True)


def _list(prefix):
    out, tok = [], None
    while True:
        p = {"list-type": "2", "prefix": prefix, "delimiter": "/"}
        if tok:
            p["continuation-token"] = tok
        for k in range(4):
            try:
                t = requests.get(BUCKET, params=p, timeout=60).text
                break
            except requests.RequestException:
                if k == 3:
                    raise
        out += [x for x in re.findall(r"<Prefix>([^<]+)</Prefix>", t) if x != prefix]
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", t)
        if not m:
            return out
        tok = m.group(1)


def find_tile(ra, dec):
    cache = CACHE / f"tile_{ra:.4f}_{dec:.4f}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    span = min(180, 2.0 / max(np.cos(np.radians(dec)), 0.05))
    rr_wanted = set()
    for d in np.arange(-span, span + 0.05, 0.1):
        r = (ra + d) % 360
        rr_wanted.add(int(r * 10))
    best = None
    rr_dirs = {}
    for rrrr in sorted(rr_wanted):
        top = f"{rrrr // 100:02d}" if rrrr >= 100 else "00"
        rr_dirs.setdefault(top, None)
    folders = []
    for top in rr_dirs:
        folders += _list(f"{PREFIX}{top}/")
    folders = [f for f in folders if int(f.rstrip("/").split("/")[-1]) in rr_wanted]
    for fo in folders:
        for tile in _list(fo):
            cid = tile.rstrip("/").split("/")[-1]
            m = re.match(r"(\d{4})([pm])(\d{3})_ac51", cid)
            if not m:
                continue
            tra = int(m.group(1)) / 10
            tdec = (1 if m.group(2) == "p" else -1) * int(m.group(3)) / 10
            dx = ((ra - tra + 180) % 360 - 180) * np.cos(np.radians(dec))
            dd = dec - tdec
            if abs(dx) < 0.78 and abs(dd) < 0.78:
                sep = max(abs(dx), abs(dd))  # most margin from the tile edge
                if best is None or sep < best["sep"]:
                    best = {"coadd_id": cid, "ra": tra, "dec": tdec, "sep": float(sep), "prefix": tile}
    cache.write_text(json.dumps(best))
    return best


def wise_on_grid(ra, dec, gw, shape, fid):
    """AllWISE W2 image reprojected (flux-conserving adaptive resampling) onto the SPHEREx grid."""
    out = CACHE / f"{fid}_w2.npz"
    meta_p = CACHE / f"{fid}_w2.json"
    if out.exists() and meta_p.exists():
        return np.load(out)["img"], json.loads(meta_p.read_text())
    t = find_tile(ra, dec)
    if not t:
        return None, None
    key = f"{t['prefix']}{t['coadd_id']}-w2-int-3.fits"
    url = BUCKET + key
    with fits.open(url, use_fsspec=True, fsspec_kwargs={"block_size": 1024 * 1024}) as h:
        hd = h[0].header
        w = WCS(hd)
        x, y = (float(v) for v in w.world_to_pixel_values(ra, dec))
        half = int(np.ceil(shape[0] * 6.15 / 1.375 * 0.75)) + 10
        xi, yi = int(round(x)), int(round(y))
        y0, y1 = max(0, yi - half), min(hd["NAXIS2"], yi + half + 1)
        x0, x1 = max(0, xi - half), min(hd["NAXIS1"], xi + half + 1)
        cut = np.array(h[0].section[y0:y1, x0:x1], dtype=float)
        sub = w[y0:y1, x0:x1]
        meta = {"coadd_id": t["coadd_id"], "source_uri": f"https://irsa.ipac.caltech.edu/ibe/data/wise/allwise/p3am_cdd/{key.split('p3am_cdd/')[1]}",
                "s3_uri": url, "band": "W2 (4.6 um)", "bunit": hd.get("BUNIT"),
                "date_first": hd.get("DATEOBS1"), "date_last": hd.get("DATEOBS2"), "n_frames": hd.get("NUMFRMS")}
        from astropy.time import Time
        t1, t2 = Time(hd["DATEOBS1"]), Time(hd["DATEOBS2"])
        meta.update({"mjd_min": t1.mjd, "mjd_max": t2.mjd, "mjd_mean": 0.5 * (t1.mjd + t2.mjd)})
    img, foot = reproject_adaptive((cut, sub), gw, shape_out=shape, conserve_flux=False)
    img[foot < 0.5] = np.nan
    np.savez_compressed(out, img=img)
    meta_p.write_text(json.dumps(meta))
    return img, meta


if __name__ == "__main__":
    print(find_tile(float(sys.argv[1]), float(sys.argv[2])))
