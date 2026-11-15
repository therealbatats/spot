# SPOT pipeline - build one field for the website.
# Written with AI assistance under the direction of Ali (team AITHMAC).
#
# Usage:
#   python pipeline/make_field.py --target barnard            (a field from pipeline/targets.json)
#   python pipeline/make_field.py --ra 210.8 --dec 54.35 --name myfield [--size 0.2]
#
# Output: site/data/fields/<id>/*.png and site/data/fields/<id>/field.json (merged into manifest by
# build_manifest.py). Everything shown on the site is real SPHEREx Level-2 data except the Planet X
# simulation, which the site draws on top and labels SIMULATED.
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import astropy.units as u
from astropy.coordinates import (SkyCoord, get_body_barycentric, CartesianRepresentation,
                                 BarycentricTrueEcliptic, ICRS)
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp

import frames as F
from search import find_frames

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BANDS = {1: (0.75, 1.09), 2: (1.10, 1.62), 3: (1.63, 2.41), 4: (2.42, 3.82), 5: (3.83, 4.41), 6: (4.42, 5.00)}
# Approximate SPHEREx band edges (um) per detector array; the exact wavelength of every frame is
# computed from its own spectral WCS and shown on the site.
BAND_LABEL = {1: "0.75–1.1 µm: deep red / near-IR starlight",
              2: "1.1–1.6 µm: near-infrared starlight",
              3: "1.6–2.4 µm: infrared starlight (K-band-like)",
              4: "2.4–3.8 µm: warm dust, water-ice band",
              5: "3.8–4.4 µm: CO₂ band region",
              6: "4.4–5.0 µm: thermal glow of cold brown dwarfs"}
EPOCH_GAP_DAYS = 60
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


# ------------------------------------------------------------------ astrometry
def star_position(t, mjd):
    """Astrometric (no aberration) geocentric RA/Dec of the target at time mjd, from catalogue
    position + proper motion + parallax. For plx=0 (galaxy) returns the fixed position."""
    if not t.get("plx"):
        return t["ra"], t["dec"]
    c = SkyCoord(ra=t["ra"] * u.deg, dec=t["dec"] * u.deg, distance=(1000.0 / t["plx"]) * u.pc,
                 pm_ra_cosdec=t["pmra"] * u.mas / u.yr, pm_dec=t["pmdec"] * u.mas / u.yr,
                 radial_velocity=(t.get("rv") or 0.0) * u.km / u.s,
                 obstime=Time(t["epoch"], format="jyear"), frame="icrs")
    tt = Time(mjd, format="mjd")
    c2 = c.apply_space_motion(new_obstime=tt)
    star = c2.cartesian.xyz.to(u.au)
    earth = get_body_barycentric("earth", tt).xyz.to(u.au)
    v = (star - earth).value
    ra = np.degrees(np.arctan2(v[1], v[0])) % 360
    dec = np.degrees(np.arcsin(v[2] / np.linalg.norm(v)))
    return float(ra), float(dec)


# ------------------------------------------------------------------ images
def fill_nan(img):
    """Replace NaNs by the mean of valid 3x3 neighbours (repeat) so interpolation does not spread
    holes; the mask is carried separately and re-applied after reprojection."""
    a = img.copy()
    for _ in range(4):
        bad = ~np.isfinite(a)
        if not bad.any():
            break
        p = np.pad(a, 1, constant_values=np.nan)
        stack = np.stack([p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)])
        with np.errstate(all="ignore"):
            m = np.nanmean(stack, axis=0)
        a[bad] = m[bad]
    a[~np.isfinite(a)] = 0.0
    return a


def clean_frame(meta, name, gw, shape):
    a = F.load_arrays(meta, name)
    img = a["img"].astype(np.float64) - a["zod"]  # zodi model (full extractor) or zeros (lean extractor)
    bad = F.display_bad(a["flg"]) | ~np.isfinite(img)
    img[bad] = np.nan
    _, med, std = sigma_clipped_stats(img[np.isfinite(img)], sigma=3, maxiters=5)
    img -= med  # robust residual background
    var = a["var"].astype(np.float64)
    var[bad] = np.nan
    src = WCS(fits.Header.fromstring(meta["wcs_header"], sep="\n"))
    out, foot = reproject_interp((fill_nan(img), src), gw, shape_out=shape, order="bilinear")
    mk, _ = reproject_interp((bad.astype(float), src), gw, shape_out=shape, order="bilinear")
    vo, _ = reproject_interp((fill_nan(var), src), gw, shape_out=shape, order="bilinear")
    out[(foot < 0.99) | (mk > 0.4)] = np.nan
    vo[~np.isfinite(out)] = np.nan
    return out, vo, a, src, float(std)


def photometry(meta, a, src, ra, dec, r_ap=2.0, r_in=5.0, r_out=8.0):
    """Forced aperture photometry on the native (not reprojected) cutout at the predicted position.
    Returns flux in microJansky inside a 2-pixel (~12 arcsec) radius aperture (not aperture-corrected)."""
    img = a["img"].astype(np.float64) - a["zod"]
    bad = (a["flg"] & F.BAD_MASK) != 0
    x, y = (float(v) for v in src.world_to_pixel_values(ra, dec))
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    rr = np.hypot(xx - x, yy - y)
    ap = rr <= r_ap
    ann = (rr >= r_in) & (rr <= r_out) & ~bad
    if ap.sum() == 0 or ann.sum() < 10:
        return None
    bkg = np.median(img[ann])
    nbad = int((ap & bad).sum())
    pix_sr = (meta["pixel_scale_arcsec"] / 206264.806) ** 2
    # wing photometry (for saturated stars): the unflagged ring 3-6 px from the centre, background 9-14 px
    wres = {}
    sc = 1e6 * (meta["pixel_scale_arcsec"] / 206264.806) ** 2 * 1e6
    for tag, (r1, r2, b1, b2) in (("wing", (3, 6, 9, 14)), ("wing2", (6, 10, 14, 20))):
        wing = (rr >= r1) & (rr <= r2)
        wuse = wing & ~bad & np.isfinite(img)
        wb = (rr >= b1) & (rr <= b2) & ~bad & np.isfinite(img)
        if wuse.sum() >= 0.5 * wing.sum() and wb.sum() > 20:
            wcorr = wing.sum() / wuse.sum()
            wres[f"{tag}_ujy"] = round(float(np.sum(img[wuse] - np.median(img[wb]))) * wcorr * sc, 2)
            wres[f"{tag}_err_ujy"] = round(float(np.sqrt(np.sum(a["var"][wuse]))) * wcorr * sc, 2)
    use = ap & ~bad & np.isfinite(img)  # flagged pixels are excluded (and the point is marked)
    if use.sum() < 0.6 * ap.sum():
        return {"flux_ujy": None, "err_ujy": None, "bad_in_aperture": nbad, "x": round(x, 2), "y": round(y, 2), **wres}
    corr = ap.sum() / use.sum()  # scale up for the excluded pixels (approximate)
    flux = float(np.sum(np.where(use, img - bkg, 0.0))) * corr * 1e6 * pix_sr * 1e6  # MJy/sr -> uJy
    var = float(np.sum(np.where(use, a["var"], 0.0))) * corr ** 2 * (1e6 * pix_sr * 1e6) ** 2
    return {"flux_ujy": round(flux, 2), "err_ujy": round(float(np.sqrt(max(var, 0))), 2), "bad_in_aperture": nbad,
            "x": round(x, 2), "y": round(y, 2), **wres}


def stretch_params(stack):
    v = np.concatenate([s[np.isfinite(s)].ravel() for s in stack if np.isfinite(s).any()])
    lo, hi = np.percentile(v, [2, 99.8])
    return float(lo), float(max(hi, lo + 1e-6))


def display_fill(img, hi, signed=False):
    """DISPLAY ONLY. Masked (NaN) pixels in holes inside the image are filled so bright stars are
    not drawn as black holes: a hole touching a bright source (5x5 neighbourhood reaches the top of
    the display stretch) is drawn at display maximum (white); any other hole gets the local median.
    In difference images every hole becomes 0 (no change). Holes connected to the image border
    (no coverage) stay empty. Photometry and the true mask are not affected."""
    from scipy import ndimage
    a = np.array(img, dtype=float)
    nan = ~np.isfinite(a)
    if not nan.any():
        return a, nan
    lab, n = ndimage.label(nan)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    holes = nan & ~np.isin(lab, list(edge))
    out = a.copy()
    if signed:
        out[holes] = 0.0
        return out, holes
    for _ in range(12):
        todo = holes & ~np.isfinite(out)
        if not todo.any():
            break
        fin = np.isfinite(out)
        mx = ndimage.maximum_filter(np.where(fin, out, -np.inf), size=5)
        pad = np.pad(np.where(fin, out, np.nan), 2, constant_values=np.nan)
        win = np.lib.stride_tricks.sliding_window_view(pad, (5, 5))
        cnt = np.isfinite(win).sum(axis=(2, 3))
        cand = todo & (cnt > 0)
        with np.errstate(all="ignore"), __import__("warnings").catch_warnings():
            __import__("warnings").simplefilter("ignore")
            med = np.nanmedian(win, axis=(2, 3))
        bright = cand & (mx >= hi)
        out[bright] = hi * 4.0
        rest = cand & ~bright
        out[rest] = med[rest]
    return out, holes


def to_png(img, lo, hi, path, signed=False):
    """8-bit grey + alpha. Alpha 255 = real pixel, 254 = flagged pixel filled for display
    (see display_fill), 0 = no data. Rows flipped so north is up, east left."""
    img, filled = display_fill(img, hi, signed)
    if signed:
        z = 0.5 + 0.5 * np.clip(img / hi, -1, 1)
    else:
        z = np.clip((img - lo) / (hi - lo), 0, 1)
        z = np.arcsinh(8 * z) / np.arcsinh(8)
    g = np.nan_to_num(z * 255, nan=0).astype(np.uint8)[::-1]
    al = np.where(np.isfinite(img), np.where(filled, 254, 255), 0).astype(np.uint8)[::-1]
    Image.fromarray(np.dstack([g, al]), mode="LA").save(path, optimize=True)


def wmean(stack, vstack):
    """Per-pixel mean across frames with 3-sigma clipping (rejects cosmic rays that slipped through)."""
    from astropy.stats import sigma_clip
    s = np.array(stack, dtype=float)
    v0 = np.array(vstack, dtype=float)
    if len(s) >= 3:
        # reject single-frame outliers (cosmic rays, hot pixels missed by the flags): more than
        # 5 sigma + 30% of the median away from the per-pixel median of all frames of this visit
        with np.errstate(all="ignore"), __import__("warnings").catch_warnings():
            __import__("warnings").simplefilter("ignore")
            med = np.nanmedian(s, axis=0)
        lim = 5 * np.sqrt(np.clip(v0, 0, None)) + 0.3 * np.abs(med)
        s = np.where(np.abs(s - med) > lim, np.nan, s)
    if len(s) >= 3:
        c = sigma_clip(np.ma.masked_invalid(s), sigma=3, axis=0, maxiters=2)
        m = c.mean(axis=0).filled(np.nan)
        n = (~c.mask).sum(axis=0)
    else:
        with np.errstate(all="ignore"):
            m = np.nanmean(s, axis=0)
        n = np.isfinite(s).sum(axis=0)
    v = np.array(vstack, dtype=float)
    with np.errstate(all="ignore"):
        mv = np.nanmean(v, axis=0) / np.maximum(n, 1)
    m[n == 0] = np.nan
    return m, mv


def _wmean_unused(stack, vstack):
    s = np.array(stack)
    v = np.array(vstack)
    w = np.where(np.isfinite(s) & np.isfinite(v) & (v > 0), 1.0 / np.where(v > 0, v, 1), 0.0)
    num = np.nansum(np.where(w > 0, s * w, 0), axis=0)
    den = w.sum(axis=0)
    with np.errstate(all="ignore"):
        m = num / den
        mv = 1.0 / den
    m[den == 0] = np.nan
    mv[den == 0] = np.nan
    return m, mv


def centroid(img, x0, y0, r=3):
    """Flux-weighted centroid in a small box (grid pixel coords, unflipped)."""
    xi, yi = int(round(x0)), int(round(y0))
    if not (r <= xi < img.shape[1] - r and r <= yi < img.shape[0] - r):
        return None
    box = img[yi - r:yi + r + 1, xi - r:xi + r + 1]
    if np.isfinite(box).mean() < 0.85:  # tolerate a few empty (overflowed) core pixels
        return None
    b = box - np.median(img[np.isfinite(img)])
    b = np.clip(np.nan_to_num(b, nan=0.0), 0, None)
    if b.sum() <= 0:
        return None
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return float(xi + (b * xx).sum() / b.sum()), float(yi + (b * yy).sum() / b.sum())


# ------------------------------------------------------------------ Planet X (simulation geometry)
def planetx_offsets(ra0, dec0, epochs_mjd, gw, shape, distances_au):
    """Pixel position on the field grid of a hypothetical distant planet observed from Earth at each
    epoch. Model: circular heliocentric orbit at distance D (AU), inclination equal to the field's
    ecliptic latitude, body at its highest point at the first epoch, moving east (prograde) at
    angular rate 2*pi/D**1.5 rad/yr (Kepler's third law, solar mass). Positions are then offset so
    the whole track is centred in the field. This is SIMULATION GEOMETRY ONLY."""
    c0 = SkyCoord(ra=ra0 * u.deg, dec=dec0 * u.deg).transform_to(BarycentricTrueEcliptic(equinox="J2000"))
    lam0, beta = c0.lon.rad, c0.lat.rad
    t0 = Time(epochs_mjd[0], format="mjd")
    out = {}
    for D in distances_au:
        n = 2 * np.pi / D ** 1.5  # rad / yr
        pts = []
        for m in epochs_mjd:
            t = Time(m, format="mjd")
            dt = (t - t0).to(u.yr).value
            lam = lam0 + n * dt / max(np.cos(beta), 0.05)
            hel = D * np.array([np.cos(beta) * np.cos(lam), np.cos(beta) * np.sin(lam), np.sin(beta)])
            sun = get_body_barycentric("sun", t)
            body = SkyCoord(CartesianRepresentation(hel * u.au), frame=BarycentricTrueEcliptic(equinox="J2000"))
            # heliocentric ecliptic -> barycentric ICRS vector, then subtract Earth
            bvec = body.transform_to(ICRS()).cartesian.xyz.to(u.au).value + sun.xyz.to(u.au).value
            evec = get_body_barycentric("earth", t).xyz.to(u.au).value
            v = bvec - evec
            ra = np.degrees(np.arctan2(v[1], v[0])) % 360
            dec = np.degrees(np.arcsin(v[2] / np.linalg.norm(v)))
            x, y = gw.world_to_pixel_values(ra, dec)
            pts.append([float(x), float(y)])
        pts = np.array(pts)
        pts -= pts.mean(axis=0)
        out[str(D)] = [[round(float(px), 2), round(float(py), 2)] for px, py in pts]
    return out




# ------------------------------------------------------------------ honest differences
# F_RESID: fraction of a star's peak that remains in B - A for stars that did NOT change (sub-pixel
# registration and PSF differences between visits). Measured on isolated Gaia stars in all six fields
# (pipeline/diff_floor.json, written by pass 1); default used until measured.
def f_resid():
    fp = Path(__file__).parent / "diff_floor.json"
    return json.loads(fp.read_text())["f"] if fp.exists() else 0.1


def sig_map(A, B, f, vA=None, vB=None):
    """Significance of a change: S = (B - A) / sqrt(sigma^2 + (f * max(A, B))^2).
    sigma is per pixel: sqrt(vA + vB) from the tracked variance, rescaled so that the robust scatter of
    (B - A) / sqrt(vA + vB) on empty sky (pixels fainter than the 60th percentile) is exactly 1 (this
    absorbs the noise correlation introduced by reprojection). Without variance maps, one sky value."""
    d = B - A
    m = np.fmax(A, B)
    ok = np.isfinite(d) & np.isfinite(m)
    if ok.sum() < 50:
        return d * np.nan, np.nan
    sky = ok & (m < np.nanpercentile(m[ok], 60))
    if vA is not None and vB is not None:
        sv = np.sqrt(np.clip(np.asarray(vA, float) + np.asarray(vB, float), 0, None))
        good = sky & np.isfinite(sv) & (sv > 0)
        if good.sum() > 50:
            z = d[good] / sv[good]
            scale = 1.4826 * np.nanmedian(np.abs(z - np.nanmedian(z)))
            sig = sv * scale
            sig = np.where(np.isfinite(sig) & (sig > 0), sig, np.nanmedian(sig[good]))
            return d / np.sqrt(sig ** 2 + (f * np.clip(m, 0, None)) ** 2), float(np.nanmedian(sig[good]))
    sig = 1.4826 * np.nanmedian(np.abs(d[sky] - np.nanmedian(d[sky])))
    return d / np.sqrt(sig ** 2 + (f * np.clip(m, 0, None)) ** 2), float(sig)


def star_resid(A, B, stars):
    """For each star (grid x, y): max |B - A| within 2 px divided by max(A, B) peak within 2 px."""
    out = []
    yy, xx = np.mgrid[:A.shape[0], :A.shape[1]]
    for x, y in stars:
        r = np.hypot(xx - x, yy - y) <= 2
        a, b = A[r], B[r]
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            continue
        pk = max(a.max(), b.max())
        if pk <= 0:
            continue
        out.append(float(np.abs(b - a).max() / pk))
    return out

# ------------------------------------------------------------------ Gaia overlay (ESA Gaia DR3 via MAST TAP)
def gaia_sources(fid, ra, dec, radius_deg, gmax=17.5):
    cache = ROOT / "cache" / f"gaia_{fid}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    try:
        import pyvo
        tap = pyvo.dal.TAPService("https://mast.stsci.edu/vo-tap/api/v0.1/gaiadr3")
        q = (f"SELECT TOP 500 ra, dec, pmra, pmdec, phot_g_mean_mag FROM dbo.gaia_source WHERE "
             f"1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra},{dec},{radius_deg})) AND phot_g_mean_mag < {gmax} "
             f"ORDER BY phot_g_mean_mag")
        t = tap.search(q).to_table()
        col = lambda c: np.ma.filled(np.ma.asarray(t[c], dtype=float), np.nan)
        ra_, de_, pa_, pd_, g_ = (col(c) for c in ("ra", "dec", "pmra", "pmdec", "phot_g_mean_mag"))
        rows = [[round(float(a), 7), round(float(b), 7), round(float(c), 2) if np.isfinite(c) else 0.0,
                 round(float(d), 2) if np.isfinite(d) else 0.0, round(float(e), 2)]
                for a, b, c, d, e in zip(ra_, de_, pa_, pd_, g_) if np.isfinite(e)]
        cache.write_text(json.dumps(rows))
        return rows
    except Exception as e:
        log(f"[{fid}] Gaia query failed: {e!r}")
        return None

def assign_epochs(items, gap=EPOCH_GAP_DAYS, bin_days=None, key="mjd", field="_ep"):
    """Group frames into visits: by time gaps (default) or by fixed-width bins (dense deep-field targets)."""
    items.sort(key=lambda h: h[key])
    if bin_days:
        m0 = items[0][key]
        raw = [int((h[key] - m0) // bin_days) for h in items]
        ren = {b: i + 1 for i, b in enumerate(sorted(set(raw)))}
        for h, b in zip(items, raw):
            h[field] = ren[b]
        return len(ren)
    ep, last = 0, None
    for h in items:
        if last is None or h[key] - last > gap:
            ep += 1
        h[field] = ep
        last = h[key]
    return ep


def select_frames(hits, cap=12, gap=EPOCH_GAP_DAYS, bin_days=None):
    """At most `cap` frames per (detector, visit), chosen evenly across the wavelengths available.
    Wavelengths come from the hit's pixel position and the fixed per-detector tables."""
    hs = sorted(hits, key=lambda h: h["mjd"])
    ep = assign_epochs(hs, gap, bin_days)
    for h in hs:
        h["_wl"] = F.wave_at(h["det"], h["x"], h["y"])[0]
    keys = []
    for det in range(1, 7):
        lo, hi = BANDS[det]
        grid = np.linspace(lo + 0.02, hi - 0.02, cap)  # same target wavelengths in every visit
        for e in range(1, ep + 1):
            g = [h for h in hs if h["det"] == det and h["_ep"] == e]
            chosen = []
            for wl in grid:
                if not g:
                    break
                best = min(g, key=lambda h: abs(h["_wl"] - wl))
                if best["key"] not in chosen:
                    chosen.append(best["key"])
            keys += chosen
    return keys


# ------------------------------------------------------------------ main
def build(t, half=None):
    t0 = time.time()
    fid, size = t["id"], t.get("size_deg", 0.2)
    if half is None:  # cutout must cover the square grid at any rotation
        half = int(np.ceil(size / 2 * np.sqrt(2) * 3600 / 6.15)) + 3
    outdir = SITE / "data" / "fields" / fid
    outdir.mkdir(parents=True, exist_ok=True)
    ra_mid, dec_mid = star_position(t, Time("2026-01-01").mjd)
    hits = find_frames(ra_mid, dec_mid, fid, log=log)
    if not hits:
        log(f"[{fid}] no SPHEREx frames found")
        return None
    # per-frame predicted position (moves for high proper-motion stars)
    pos = {h["key"]: star_position(t, h["mjd"]) for h in hits}
    # cutouts are centred on the mid position; half=86 px covers a 0.2 deg square at any rotation
    gap = t.get("epoch_gap_days", EPOCH_GAP_DAYS)
    bin_days = t.get("epoch_bin_days")
    keys = select_frames(hits, cap=t.get("cap", 12), gap=gap, bin_days=bin_days)
    log(f"[{fid}] selected {len(keys)} of {len(hits)} frames (max {t.get('cap', 12)} per detector per visit, spread in wavelength)")
    metas = F.extract_many_fast(keys, ra_mid, dec_mid, fid, half=half, workers=8)
    log(f"[{fid}] {len(metas)}/{len(hits)} cutouts extracted ({time.time()-t0:.0f}s)")
    metas = [m for m in metas if m["bad_fraction"] < 0.25]
    ep = assign_epochs(metas, gap, bin_days, field="epoch")
    gw, shape = F.target_grid(ra_mid, dec_mid, size)
    n_ep = ep
    log(f"[{fid}] {len(metas)} usable frames in {n_ep} epochs")
    # isolated Gaia stars (G 9-15, no G<17 neighbour within 20", >25" from the target) for the
    # difference floor; positions on the grid at 2026.0 (stars with pm > 50 mas/yr skipped)
    gstars = []
    gall = gaia_sources(fid, ra_mid, dec_mid, size * 0.72) or []
    for k, g in enumerate(gall):
        if not (9 < g[4] < 15) or abs(g[2]) > 50 or abs(g[3]) > 50:
            continue
        if any(j != k and o[4] < 17 and np.hypot((o[0] - g[0]) * np.cos(np.radians(g[1])), o[1] - g[1]) * 3600 < 20 for j, o in enumerate(gall)):
            continue
        if np.hypot((g[0] - ra_mid) * np.cos(np.radians(dec_mid)), g[1] - dec_mid) * 3600 < 25:
            continue
        gx, gy = gw.world_to_pixel_values(g[0], g[1])
        if 4 <= gx < shape[1] - 4 and 4 <= gy < shape[0] - 4:
            gstars.append((float(gx), float(gy)))
    FRES = f_resid()
    resid_all = []

    cleaned = {}
    for m in metas:
        img, var, a, src, std = clean_frame(m, fid, gw, shape)
        tra, tdec = pos[m["key"]]
        ph = photometry(m, a, src, tra, tdec)
        cleaned[m["key"]] = (img, var)
        m["phot"] = ph
        m["target_radec"] = [round(tra, 7), round(tdec, 7)]
        m["noise_mjysr"] = std
    log(f"[{fid}] cleaned + reprojected ({time.time()-t0:.0f}s)")

    field = {"id": fid, "title": t["title"], "kind": t["kind"], "ra_deg": ra_mid, "dec_deg": dec_mid,
             "size_deg": size, "grid_px": shape[0], "pixel_scale_arcsec": 6.15,
             "astrometry_source": t.get("astrometry_source", ""),
             "catalog": {k: t.get(k) for k in ("ra", "dec", "epoch", "pmra", "pmdec", "plx")},
             "story": t.get("story", {}), "bands": [], "channels": [], "frames": []}

    # ---- frame table (provenance for every frame used)
    for m in metas:
        field["frames"].append({
            "obsid": m["obsid"], "detector": m["detector"], "epoch": m["epoch"], "utc": m["utc"], "mjd": round(m["mjd"], 6),
            "wavelength_um": round(m["wavelength_um"], 4), "bandwidth_um": round(m["bandwidth_um"], 4),
            "release": m["release"], "version": m["version"], "source_uri": m["source_uri"],
            "bad_fraction": round(m["bad_fraction"], 4), "bad_fraction_center": round(m["bad_fraction_center"], 4),
            "center_flags": m["center_flags"], "phot": m["phot"], "target_radec": m["target_radec"]})

    # ---- band coadds per epoch (all frames of one detector array within one epoch, inverse-variance mean)
    by = defaultdict(list)
    for m in metas:
        by[(m["detector"], m["epoch"])].append(m)
    for det in range(1, 7):
        eps = sorted(e for (d, e) in by if d == det)
        if len(eps) < 1:
            continue
        # Fair comparison: use only the wavelength range covered by EVERY visit. If that common range is
        # narrower than 35% of the band, drop the visit with the narrowest coverage and try again.
        width = BANDS[det][1] - BANDS[det][0]
        dropped = []
        while True:
            lo_c = max(min(m["wavelength_um"] for m in by[(det, e)]) for e in eps) - 0.005
            hi_c = min(max(m["wavelength_um"] for m in by[(det, e)]) for e in eps) + 0.005
            ok = hi_c - lo_c >= 0.35 * width and all(
                sum(lo_c <= m["wavelength_um"] <= hi_c for m in by[(det, e)]) >= 2 for e in eps)
            if ok or len(eps) <= 1:
                break
            narrow = min(eps, key=lambda e: max(m["wavelength_um"] for m in by[(det, e)]) - min(m["wavelength_um"] for m in by[(det, e)]))
            eps.remove(narrow)
            dropped.append(narrow)
        if len(eps) < 2 and len({e for (d, e) in by if d == det}) >= 2:
            log(f"[{fid}] D{det}: visits do not share enough wavelength range for a fair band comparison; band shows {eps}")
        if dropped:
            log(f"[{fid}] D{det}: dropped visit(s) {dropped} from the band view (too little shared wavelength range)")
        imgs, items, vmaps = [], [], []
        for e in eps:
            ms = [m for m in by[(det, e)] if lo_c <= m["wavelength_um"] <= hi_c] or by[(det, e)]
            im, vm = wmean([cleaned[m["key"]][0] for m in ms], [cleaned[m["key"]][1] for m in ms])
            imgs.append(im)
            vmaps.append(vm)
            wl = [m["wavelength_um"] for m in ms]
            items.append({"epoch": e, "n_frames": len(ms), "utc_first": ms[0]["utc"], "utc_last": ms[-1]["utc"],
                          "mjd_mean": round(float(np.mean([m["mjd"] for m in ms])), 4),
                          "wl_min_um": round(min(wl), 3), "wl_max_um": round(max(wl), 3),
                          "obsids": [m["obsid"] for m in ms], "_img": im})
        lo, hi = stretch_params(imgs)
        for it in items:
            p = f"b{det}_e{it['epoch']}.png"
            to_png(it.pop("_img"), lo, hi, outdir / p)
            it["png"] = p
        # all-epoch sum ("add together")
        allm, _ = wmean(imgs, [np.ones_like(i) for i in imgs])
        to_png(allm, lo, hi, outdir / f"b{det}_all.png")
        # differences between consecutive epochs and first->last ("subtract")
        diffs = []
        pairs = [(i, i + 1) for i in range(len(imgs) - 1)]
        if len(imgs) > 2:
            pairs.append((0, len(imgs) - 1))
        dd = [imgs[j] - imgs[i] for i, j in pairs]
        if dd:
            v = np.concatenate([d[np.isfinite(d)] for d in dd if np.isfinite(d).any()] or [np.zeros(1)])
            dh = float(np.percentile(np.abs(v), 99.5)) if v.size else 1.0
            for (i, j), d in zip(pairs, dd):
                p = f"b{det}_d{items[i]['epoch']}_{items[j]['epoch']}.png"
                to_png(d, 0, dh or 1.0, outdir / p, signed=True)
                S, sky_sig = sig_map(imgs[i], imgs[j], FRES, vmaps[i], vmaps[j])
                ps = f"b{det}_s{items[i]['epoch']}_{items[j]['epoch']}.png"
                to_png(S, 0, 5.0, outdir / ps, signed=True)  # fixed range: grey 0, white +5, black -5
                rs = star_resid(imgs[i], imgs[j], gstars)
                resid_all += rs
                big = int((np.abs(np.nan_to_num(S)) > 5).sum())
                diffs.append({"a": items[i]["epoch"], "b": items[j]["epoch"], "png": p, "sig_png": ps,
                              "n_pix_over_5": big, "sky_sigma": sky_sig,
                              "star_resid_median": round(float(np.median(rs)), 3) if rs else None, "n_stars": len(rs)})
        field["bands"].append({"detector": det, "label": BAND_LABEL[det], "range_um": BANDS[det],
                               "common_um": [round(lo_c, 3), round(hi_c, 3)], "dropped_visits": dropped,
                               "epochs": items, "all_png": f"b{det}_all.png", "diffs": diffs,
                               "stretch": [lo, hi]})

    # ---- narrow channels: same wavelength (|dlambda| < half bandwidth) in 2+ epochs, same detector
    used = set()
    for det in range(1, 7):
        ms = [m for m in metas if m["detector"] == det]
        best = None
        for a in ms:
            group = {}
            for b in ms:
                if abs(b["wavelength_um"] - a["wavelength_um"]) < 0.5 * min(a["bandwidth_um"], b["bandwidth_um"]):
                    e = b["epoch"]
                    if e not in group or abs(b["wavelength_um"] - a["wavelength_um"]) < abs(group[e]["wavelength_um"] - a["wavelength_um"]):
                        group[e] = b
            # strict rule: EVERY pair of chosen frames differs by less than half the narrowest bandwidth
            while len(group) >= 2:
                wls = [g["wavelength_um"] for g in group.values()]
                hb = 0.5 * min(g["bandwidth_um"] for g in group.values())
                if max(wls) - min(wls) < hb:
                    break
                far = max(group, key=lambda e: abs(group[e]["wavelength_um"] - a["wavelength_um"]))
                del group[far]
            score = (len(group), -np.mean([g["bad_fraction"] for g in group.values()]))
            if len(group) >= 2 and (best is None or score > best[0]):
                best = (score, a, group)
        if not best:
            continue
        _, a, group = best
        sel = [group[e] for e in sorted(group)]
        imgs = [cleaned[m["key"]][0] for m in sel]
        lo, hi = stretch_params(imgs)
        cid = f"c{det}"
        ch = {"id": cid, "detector": det, "wavelength_um": round(a["wavelength_um"], 4),
              "bandwidth_um": round(a["bandwidth_um"], 4), "frames": [], "diffs": []}
        for m, im in zip(sel, imgs):
            p = f"{cid}_{m['obsid']}.png"
            to_png(im, lo, hi, outdir / p)
            ch["frames"].append({"epoch": m["epoch"], "utc": m["utc"], "obsid": m["obsid"], "png": p,
                                 "wavelength_um": round(m["wavelength_um"], 4), "bandwidth_um": round(m["bandwidth_um"], 4),
                                 "source_uri": m["source_uri"], "release": m["release"], "detector": det,
                                 "bad_fraction": round(m["bad_fraction"], 4), "center_flags": m["center_flags"]})
        for i in range(len(imgs) - 1):
            d = imgs[i + 1] - imgs[i]
            dh = float(np.nanpercentile(np.abs(d), 99.5)) if np.isfinite(d).any() else 1.0
            p = f"{cid}_d{i}.png"
            to_png(d, 0, dh or 1.0, outdir / p, signed=True)
            S, _ = sig_map(imgs[i], imgs[i + 1], FRES, cleaned[sel[i]["key"]][1], cleaned[sel[i + 1]["key"]][1])
            ps = f"{cid}_s{i}.png"
            to_png(S, 0, 5.0, outdir / ps, signed=True)
            ch["diffs"].append({"a": i, "b": i + 1, "png": p, "sig_png": ps})
        field["channels"].append(ch)

    # ---- target track: predicted vs measured (band with best S/N chosen later in validation)
    track = []
    for e in range(1, n_ep + 1):
        ms = [m for m in metas if m["epoch"] == e]
        if not ms:
            continue
        mjd = float(np.mean([m["mjd"] for m in ms]))
        ra, dec = star_position(t, mjd)
        x, y = gw.world_to_pixel_values(ra, dec)
        track.append({"epoch": e, "mjd": round(mjd, 4), "utc": Time(mjd, format="mjd").isot[:19] + "Z",
                      "ra_deg": round(ra, 7), "dec_deg": round(dec, 7),
                      "x": round(float(x), 2), "y": round(float(shape[0] - 1 - y), 2)})
    # measured centroid of the target in each band coadd, next to the prediction (validation)
    sat_bits_all = (1 << 1) | (1 << 26)
    for b in field["bands"]:
        det = b["detector"]
        bm = [m for it in b["epochs"] for m in by[(det, it["epoch"])] if m["obsid"] in set(it["obsids"])]
        sat = any((m["center_flags"] & sat_bits_all) != 0 for m in bm)
        n_in = sum(1 for m in bm if m.get("phot") and m["phot"].get("wing_ujy") is not None)
        b["_wing"] = (False if not sat else ("wing" if n_in >= 0.8 * max(len(bm), 1) else "wing2"))
        b["phot_method"] = {False: "core aperture (r = 2 px)", "wing": "wings: ring 3-6 px (centre saturated)",
                            "wing2": "outer wings: ring 6-10 px (centre and inner ring saturated)"}[b["_wing"]]
        for it in b["epochs"]:
            ms = [m for m in by[(det, it["epoch"])] if m["obsid"] in set(it["obsids"])]
            im, _ = wmean([cleaned[m["key"]][0] for m in ms], [cleaned[m["key"]][1] for m in ms])
            ra, dec = star_position(t, it["mjd_mean"])
            x, y = gw.world_to_pixel_values(ra, dec)
            c = centroid(im, float(x), float(y))
            # light-curve point = synthetic band photometry: this visit's per-frame fluxes (forced photometry
            # at the predicted position) interpolated onto ONE wavelength grid shared by all visits, then
            # averaged. Same weighting of wavelengths every visit, so steep spectra cannot fake a change.
            lo_c, hi_c = b["common_um"]
            sat_bits = (1 << 1) | (1 << 26)  # OVERFLOW, BLOOM at the target = saturated
            it["saturated_frac"] = round(float(np.mean([(m["center_flags"] & sat_bits) != 0 for m in ms])), 2)
            # saturated star -> measure the unsaturated outer glow ("wings") instead of the core
            fk, ek = (f"{b['_wing']}_ujy", f"{b['_wing']}_err_ujy") if b.get("_wing") else ("flux_ujy", "err_ujy")
            ph = sorted([(m["wavelength_um"], m["phot"][fk], m["phot"][ek]) for m in ms
                         if m.get("phot") and m["phot"].get(fk) is not None], key=lambda r: r[0])
            it["phot_method"] = b["_wing"] or "core"
            if len(ph) >= 3:
                wl_, fl_, er_ = (np.array(v) for v in zip(*ph))
                grid = np.linspace(max(lo_c, wl_.min()), min(hi_c, wl_.max()), 8)
                if grid[-1] - grid[0] >= 0.5 * (hi_c - lo_c):
                    it["flux_ujy"] = round(float(np.mean(np.interp(grid, wl_, fl_))), 1)
                    it["noise_ujy"] = round(float(np.sqrt(np.mean(er_ ** 2) / len(ph))), 1)
                    it["synth_grid_um"] = [round(float(grid[0]), 3), round(float(grid[-1]), 3)]
            it["pred_xy"] = [round(float(x), 2), round(float(shape[0] - 1 - y), 2)]
            it["meas_xy"] = [round(c[0], 2), round(float(shape[0] - 1 - c[1]), 2)] if c else None
    for b in field["bands"]:
        b.pop("_wing", None)
    field["track"] = track
    field["objects"] = [{"name": t["title"], "type": t["kind"], "status": "known",
                         "evidence": t.get("astrometry_source", ""), "track": track}] if t.get("plx") or t["kind"] != "control" else []

    # ---- Planet X simulation geometry (per epoch, several distances)
    ep_mjd = [tr["mjd"] for tr in track]
    if len(ep_mjd) >= 2:
        dists = [100, 150, 200, 300, 500, 700, 1000]
        off = planetx_offsets(ra_mid, dec_mid, ep_mjd, gw, shape, dists)
        field["planetx"] = {"distances_au": dists, "epochs": [tr["epoch"] for tr in track],
                            "offsets_px": {k: [[x, -y] for x, y in v] for k, v in off.items()},
                            "model": "circular orbit, inclination = field ecliptic latitude, prograde, Kepler rate; observer = Earth centre"}
    g = gaia_sources(fid, ra_mid, dec_mid, size * 0.72)
    if g:
        field["gaia"] = g
        field["gaia_note"] = "ESA Gaia DR3 (via MAST), G < 17.5; [ra, dec, pmra mas/yr, pmdec mas/yr, G] at epoch 2016.0"
    field["diff_floor"] = {"f_used": FRES, "star_resid_this_field": round(float(np.median(resid_all)), 3) if resid_all else None,
                           "n_star_measurements": len(resid_all), "stars": len(gstars)}
    (Path(__file__).parent / "resid" ).mkdir(exist_ok=True)
    (Path(__file__).parent / "resid" / f"{fid}.json").write_text(json.dumps(resid_all))
    (outdir / "field.json").write_text(json.dumps(field, indent=1))
    (outdir / "build.log").write_text("\n".join(LOG))
    log(f"[{fid}] done in {time.time()-t0:.0f}s: {len(field['bands'])} bands, {len(field['channels'])} channels")
    return field


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target")
    ap.add_argument("--ra", type=float)
    ap.add_argument("--dec", type=float)
    ap.add_argument("--name")
    ap.add_argument("--size", type=float, default=0.2)
    a = ap.parse_args()
    if a.target:
        T = {x["id"]: x for x in json.loads((Path(__file__).parent / "targets.json").read_text())["fields"]}
        build(T[a.target])
    else:
        build({"id": a.name, "title": a.name, "kind": "custom", "ra": a.ra, "dec": a.dec, "epoch": 2016.0,
               "pmra": 0, "pmdec": 0, "plx": 0, "size_deg": a.size})
