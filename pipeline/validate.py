# SPOT - validation checks 1-4 (numbers pasted into VALIDATION.md).
# Written with AI assistance under the direction of Ali (team AITHMAC).
#  1 Alignment: centroids of isolated Gaia stars (G 9-14) in every band-epoch coadd vs their Gaia
#    positions moved to that date -> residual in pixels (both alignment between dates and absolute).
#  2 Wavelength matching: every exact-wavelength channel, both wavelengths and |dlambda| / bandwidth.
#  3 Known mover: measured centroid of the target vs catalogue prediction, per band and visit.
#  4 Control field: count of strong residuals in M101 difference images.
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ROOT / "site" / "data" / "fields"


def grid_xy(f, ra, dec):
    r = np.pi / 180
    n, s = f["grid_px"], f["pixel_scale_arcsec"] / 3600
    a0, d0, a, d = f["ra_deg"] * r, f["dec_deg"] * r, ra * r, dec * r
    cosc = np.sin(d0) * np.sin(d) + np.cos(d0) * np.cos(d) * np.cos(a - a0)
    xi = np.cos(d) * np.sin(a - a0) / cosc / r
    eta = (np.cos(d0) * np.sin(d) - np.sin(d0) * np.cos(d) * np.cos(a - a0)) / cosc / r
    return (n - 1) / 2 - xi / s, (n - 1) / 2 - eta / s


def centroid(img, alpha, x0, y0, r=3):
    xi, yi = int(round(x0)), int(round(y0))
    if not (r <= xi < img.shape[1] - r and r <= yi < img.shape[0] - r):
        return None
    box = img[yi - r:yi + r + 1, xi - r:xi + r + 1].astype(float)
    if (alpha[yi - r:yi + r + 1, xi - r:xi + r + 1] == 0).any():
        return None
    b = np.clip(box - np.median(img[alpha > 0]), 0, None)
    if b.sum() <= 0 or box.max() >= 254:  # skip saturated-in-display stars
        return None
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xi + (b * xx).sum() / b.sum(), yi + (b * yy).sum() / b.sum()


def alignment(f, d):
    """Residuals measured on the display PNGs (8-bit, asinh stretch). Centroids on a monotonic stretch
    of a symmetric PSF are unbiased to first order; good enough to verify sub-pixel alignment."""
    out = []
    g = f.get("gaia") or []
    stars = [s for s in g if 9 < s[4] < 14]
    # isolated: no other Gaia G<16 star within 20 arcsec
    iso = []
    for s in stars:
        near = [t for t in g if t is not s and t[4] < 16 and np.hypot((t[0] - s[0]) * np.cos(np.radians(s[1])), t[1] - s[1]) * 3600 < 20]
        if not near:
            iso.append(s)
    for b in f["bands"]:
        per_epoch = []
        for e in b["epochs"]:
            im = np.array(Image.open(d / e["png"]))
            img, al = im[..., 0], im[..., 1]
            yr = 2000 + (e["mjd_mean"] - 51544.5) / 365.25
            res = []
            for s in iso:
                dt = yr - 2016.0
                dec = s[1] + s[3] * dt / 3.6e6
                ra = s[0] + s[2] * dt / 3.6e6 / np.cos(np.radians(s[1]))
                x, y = grid_xy(f, ra, dec)
                c = centroid(img.astype(float), al, x, y)
                if c:
                    res.append(np.hypot(c[0] - x, c[1] - y))
            per_epoch.append((e["epoch"], len(res), float(np.median(res)) if res else None))
        out.append((b["detector"], per_epoch))
    return out


def main():
    lines = []
    P = lambda s="": lines.append(s)
    for d in sorted(FIELDS.iterdir()):
        fj = d / "field.json"
        if not fj.exists():
            continue
        f = json.loads(fj.read_text())
        P(f"### {f['title']} (`{f['id']}`)")
        P(f"Frames: {len(f['frames'])}; visits: {len(f.get('track', []))}; releases: {sorted({x['release'] for x in f['frames']})}; "
          f"dates {min(x['utc'] for x in f['frames'])[:10]} to {max(x['utc'] for x in f['frames'])[:10]}")
        P()
        P("**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)")
        P()
        P("| Detector | per visit: (visit, n stars, median residual px) |")
        P("|---|---|")
        for det, pe in alignment(f, d):
            P(f"| D{det} | " + "; ".join(f"({e}, {n}, {m:.2f})" if m is not None else f"({e}, {n}, –)" for e, n, m in pe) + " |")
        P()
        P("**Check 2 — wavelength matching** (exact-wavelength channels)")
        P()
        P("| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |")
        P("|---|---|---|---|---|---|")
        for c in f["channels"]:
            wl = [x["wavelength_um"] for x in c["frames"]]
            dl = max(wl) - min(wl)
            hb = 0.5 * min(x["bandwidth_um"] for x in c["frames"])
            # pairwise rule used by the pipeline is relative to the seed frame; report the full spread too
            P(f"| {c['id']} D{c['detector']} | {', '.join(x['utc'][:10] for x in c['frames'])} | {', '.join(f'{w:.4f}' for w in wl)} | {dl:.4f} | {hb:.4f} | {'yes' if dl < hb else 'NO'} |")
        P()
        if f.get("objects"):
            P("**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)")
            P()
            P("| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |")
            P("|---|---|---|---|---|---|")
            for b in f["bands"]:
                for e in b["epochs"]:
                    p, m = e.get("pred_xy"), e.get("meas_xy")
                    if p and m:
                        r = np.hypot(p[0] - m[0], p[1] - m[1])
                        P(f"| D{b['detector']} | {e['epoch']} ({e['utc_first'][:10]}) | {p[0]:.2f}, {p[1]:.2f} | {m[0]:.2f}, {m[1]:.2f} | {r:.2f} | {r * 6.15:.1f} |")
                    else:
                        P(f"| D{b['detector']} | {e['epoch']} ({e['utc_first'][:10]}) | {p} | not measured | – | – |")
            P()
            tr = f.get("track", [])
            if len(tr) >= 2:
                P(f"Predicted total shift first→last visit: {np.hypot(tr[-1]['x'] - tr[0]['x'], tr[-1]['y'] - tr[0]['y']):.2f} px "
                  f"({np.hypot(tr[-1]['x'] - tr[0]['x'], tr[-1]['y'] - tr[0]['y']) * 6.15:.1f}″) between {tr[0]['utc'][:10]} and {tr[-1]['utc'][:10]}.")
                P()
        # (old check 4 removed: a fixed-percentile stretch makes it pass by construction; see check_diff.py)
    text = "\n".join(lines)
    (ROOT / "cache" / "validation_auto.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
