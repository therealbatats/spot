# SPOT pipeline - per-frame extraction, alignment and wavelength matching.
# Written with AI assistance under the direction of Ali (team AITHMAC).
#
# A "frame" = one SPHEREx Level-2 spectral image (one exposure, one detector), cut to a small box
# around the target. We read only the bytes we need from the public S3 mirror.
import json
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.wcs import WCS, FITSFixedWarning

from s3index import BUCKET

warnings.filterwarnings("ignore", category=FITSFixedWarning)
warnings.filterwarnings("ignore", message=".*SIP.*")
logging.getLogger("astropy").setLevel(logging.ERROR)

CACHE = Path(__file__).resolve().parent.parent / "cache" / "frames"
CACHE.mkdir(parents=True, exist_ok=True)
NPIX = 2040
PIXSCALE_ARCSEC = 6.15  # verified from PC matrix (~0.001708 deg); recomputed per frame below

# FLAGS bits that mean "do not trust this pixel" (names from the FLAGS header MSKNnnnn cards).
# Bit 21 SOURCE (pixel mapped to a known source) is NOT bad. Bit 12 FULLSAMPLE is informational.
BAD_BITS = {0: "TRANSIENT", 1: "OVERFLOW", 2: "SUR_ERROR", 6: "NONFUNC", 7: "DICHROIC", 9: "MISSING_DATA",
            10: "HOT", 11: "COLD", 15: "NONLINEAR", 17: "PERSIST", 19: "OUTLIER", 20: "CROSSTALK",
            22: "GHOST", 23: "GHOST_FPA", 24: "GHOST_EXT", 25: "STREAK", 26: "BLOOM", 27: "SNOWBALL"}
BAD_MASK = sum(1 << b for b in BAD_BITS)


def https_url(key):
    return BUCKET + key


def irsa_url(key):
    """The same file on IRSA's own server (what we show as the source link)."""
    return "https://irsa.ipac.caltech.edu/ibe/data/spherex/" + key


def cache_name(key, name):
    return CACHE / name / (Path(key).stem + ".npz")


def extract(key, ra, dec, name, half=60):
    """Cut a (2*half+1)^2 box around (ra, dec) from one S3 file. Returns dict or None if the target
    is not on the detector. Result cached as .npz + .json."""
    out = cache_name(key, name)
    meta_path = out.with_suffix(".json")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        return meta if meta.get("ok") else None
    out.parent.mkdir(parents=True, exist_ok=True)
    coord = SkyCoord(ra * u.deg, dec * u.deg)
    meta = {"key": key, "ok": False}
    try:
        with fits.open(https_url(key), use_fsspec=True, fsspec_kwargs={"block_size": 1024 * 1024}) as h:
            hdr = h["IMAGE"].header
            w = WCS(hdr)
            x, y = (float(v) for v in w.world_to_pixel(coord))
            xi, yi = int(round(x)), int(round(y))
            if not (half <= xi < NPIX - half and half <= yi < NPIX - half):
                meta["reason"] = f"target at pixel ({x:.0f},{y:.0f}) too close to edge/off chip"
                meta_path.write_text(json.dumps(meta))
                return None
            sw = WCS(hdr, fobj=h, key="W")
            sw.sip = None
            wl, bw = sw.pixel_to_world(x, y)
            ys, xs = slice(yi - half, yi + half + 1), slice(xi - half, xi + half + 1)
            img = np.array(h["IMAGE"].section[ys, xs], dtype=np.float32)
            flg = np.array(h["FLAGS"].section[ys, xs], dtype=np.int64)
            var = np.array(h["VARIANCE"].section[ys, xs], dtype=np.float32)
            zod = np.array(h["ZODI"].section[ys, xs], dtype=np.float32)
            sub_wcs = w[ys, xs]
            version = h[0].header.get("VERSION", "")
        cd = sub_wcs.pixel_scale_matrix
        scale = float(np.sqrt(abs(np.linalg.det(cd)))) * 3600
        mjd = float(hdr["MJD-AVG"]) if "MJD-AVG" in hdr else float(hdr["MJD-OBS"])
        cflags = int(np.bitwise_or.reduce(flg[half - 2:half + 3, half - 2:half + 3].ravel()))
        meta.update({
            "ok": True, "obsid": hdr.get("OBSID"), "detector": int(hdr.get("DETECTOR")),
            "mjd": mjd, "utc": Time(mjd, format="mjd").isot[:19] + "Z",
            "exptime_s": float(hdr.get("XPOSURE", 0)),
            "wavelength_um": float(wl.to(u.um).value), "bandwidth_um": float(bw.to(u.um).value),
            "x_full": x, "y_full": y, "pixel_scale_arcsec": scale, "version": version,
            "release": key.split("/")[0].upper(), "source_uri": irsa_url(key), "s3_uri": https_url(key),
            "psf_fwhm_arcsec": float(hdr.get("PSF_FWHM", np.nan)),
            "sc_xyz_km": [float(hdr.get("X_SC", np.nan)), float(hdr.get("Y_SC", np.nan)), float(hdr.get("Z_SC", np.nan))],
            "bad_fraction": float(np.mean((flg & BAD_MASK) != 0)),
            "bad_fraction_center": float(np.mean((flg[half - 3:half + 4, half - 3:half + 4] & BAD_MASK) != 0)),
            "center_flags": cflags,
            "wcs_header": sub_wcs.to_header(relax=True).tostring(sep="\n"),
        })
        np.savez_compressed(out, img=img, flg=flg, var=var, zod=zod)
    except Exception as e:  # network or file problems: record and skip
        meta["reason"] = f"error: {e!r}"[:300]
        if "too close" not in meta["reason"]:
            # do not cache transient errors
            return None
    meta_path.write_text(json.dumps(meta))
    return meta if meta["ok"] else None


def load_arrays(meta, name):
    d = np.load(cache_name(meta["key"], name))
    return {k: d[k] for k in d.files}


def extract_many(keys, ra, dec, name, half=60, workers=6):
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda k: extract(k, ra, dec, name, half), keys))
    return [r for r in res if r]


# ---------------------------------------------------------------- alignment
def target_grid(ra, dec, size_deg, scale_arcsec=6.15):
    """North-up TAN grid centred on the target. Returns (WCS, shape)."""
    n = int(round(size_deg * 3600 / scale_arcsec))
    n += (n + 1) % 2  # odd so the target sits on a pixel centre
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(n + 1) / 2, (n + 1) / 2]
    w.wcs.cdelt = [-scale_arcsec / 3600, scale_arcsec / 3600]
    return w, (n, n)


def clean_and_reproject(meta, name, grid_wcs, shape):
    """Zodi-subtract, robust-background-subtract, mask bad pixels, reproject to the common grid."""
    from reproject import reproject_interp
    a = load_arrays(meta, name)
    img = a["img"].astype(np.float64) - a["zod"]
    bad = (a["flg"] & BAD_MASK) != 0
    img[bad] = np.nan
    _, med, _ = sigma_clipped_stats(img[np.isfinite(img)], sigma=3)
    img -= med
    src_wcs = WCS(fits.Header.fromstring(meta["wcs_header"], sep="\n"))
    out, foot = reproject_interp((img, src_wcs), grid_wcs, shape_out=shape, order="bilinear")
    var = a["var"].astype(np.float64)
    var[bad] = np.nan
    vout, _ = reproject_interp((var, src_wcs), grid_wcs, shape_out=shape, order="bilinear")
    out[foot < 0.5] = np.nan
    return out, vout


# ---------------------------------------------------------------- lean extractor (exact byte ranges)
# Reads ~2 MB per frame instead of ~7 MB: IMAGE rows + tile-compressed FLAGS rows only.
# Wavelength comes from the per-detector WCS-WAVE node tables, verified identical in every file and
# exported by export_live.py (bilinear interpolation matches astropy to 1e-15 um).
# Background: robust (sigma-clipped) median of the cutout, instead of the ZODI model; zodiacal light
# is smooth on the 0.2-0.3 deg scale of a cutout. Noise: sigma-clipped standard deviation.
_WAVE = None


def wave_at(det, x, y):
    global _WAVE
    if _WAVE is None:
        _WAVE = json.loads((Path(__file__).resolve().parent.parent / "site" / "data" / "live" / "wave.json").read_text())
    T = _WAVE[str(det)]
    nx, ny = np.array(T["nodes_x"], float), np.array(T["nodes_y"], float)
    from scipy.interpolate import RegularGridInterpolator
    wl = RegularGridInterpolator((ny, nx), np.array(T["wl"]), bounds_error=False, fill_value=None)([[y, x]])[0]
    bw = RegularGridInterpolator((ny, nx), np.array(T["bw"]), bounds_error=False, fill_value=None)([[y, x]])[0]
    return float(wl), float(bw)


def _hdr_at(key, off, nbytes=31680):
    import s3index as S
    r = S._get(BUCKET + key, headers={"Range": f"bytes={off}-{off + nbytes - 1}"})
    s = r.content.decode("latin-1")
    for i in range(0, len(s), 80):
        if s[i:i + 8] == "END     ":
            n = (i + 80 + 2879) // 2880 * 2880
            return fits.Header.fromstring(s[:i + 80]), n
    raise ValueError("no END")


def _range(key, a, b):
    import s3index as S
    return S._get(BUCKET + key, headers={"Range": f"bytes={a}-{b}"}).content


def _rice_row(codec, buf):
    """Decode one RICE_1 tile (one image row) to int32 values."""
    out = codec.decode(np.frombuffer(bytes(buf), dtype=np.uint8))
    a = np.frombuffer(out, dtype=np.int32) if isinstance(out, (bytes, bytearray, memoryview)) else np.asarray(out).view(np.int32).ravel()
    return a[:NPIX]


def extract_fast(key, ra, dec, name, half=60):
    out = cache_name(key, name)
    meta_path = out.with_suffix(".json")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        return meta if meta.get("ok") else None
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {"key": key, "ok": False}
    try:
        from astropy.io.fits.hdu.compressed._codecs import Rice1
        hdr, hlen = _hdr_at(key, 2880)
        assert hdr["NAXIS1"] == NPIX and hdr["BITPIX"] == -32
        w = WCS(hdr)
        x, y = (float(v) for v in w.world_to_pixel(SkyCoord(ra * u.deg, dec * u.deg)))
        xi, yi = int(round(x)), int(round(y))
        if not (half <= xi < NPIX - half and half <= yi < NPIX - half):
            meta["reason"] = f"target at pixel ({x:.0f},{y:.0f}) too close to edge/off chip"
            meta_path.write_text(json.dumps(meta))
            return None
        y0, y1, x0, x1 = yi - half, yi + half, xi - half, xi + half
        doff = 2880 + hlen
        raw = _range(key, doff + y0 * NPIX * 4, doff + (y1 + 1) * NPIX * 4 - 1)
        img = np.frombuffer(raw, ">f4").reshape(y1 - y0 + 1, NPIX)[:, x0:x1 + 1].astype(np.float32)
        foff = doff + NPIX * NPIX * 4
        fh, flen = _hdr_at(key, foff, 25920)
        assert fh.get("ZCMPTYPE") == "RICE_1" and fh.get("ZTILE2") == 1, "unexpected FLAGS compression"
        fdoff = foff + flen
        rowlen = fh["NAXIS1"]
        heap = fdoff + fh.get("THEAP", fh["NAXIS1"] * fh["NAXIS2"])
        desc = np.frombuffer(_range(key, fdoff + y0 * rowlen, fdoff + (y1 + 1) * rowlen - 1), ">i4").reshape(-1, 2)
        lo, hi = int(desc[:, 1].min()), int((desc[:, 1] + desc[:, 0]).max())
        hv = _range(key, heap + lo, heap + hi - 1)
        codec = Rice1(blocksize=int(fh.get("ZVAL1", 32)), bytepix=4, tilesize=NPIX)
        flg = np.stack([_rice_row(codec, hv[o - lo:o - lo + n]) for n, o in desc]).astype(np.int64)[:, x0:x1 + 1]
        bad = (flg & BAD_MASK) != 0
        good = img[~bad & np.isfinite(img)]
        _, med, std = sigma_clipped_stats(good, sigma=3, maxiters=5)
        var = np.full(img.shape, std ** 2, dtype=np.float32)
        zod = np.zeros_like(img)
        wl, bw = wave_at(int(hdr["DETECTOR"]), x, y)
        ys, xs = slice(y0, y1 + 1), slice(x0, x1 + 1)
        sub_wcs = w[ys, xs]
        cd = sub_wcs.pixel_scale_matrix
        scale = float(np.sqrt(abs(np.linalg.det(cd)))) * 3600
        mjd = float(hdr["MJD-AVG"]) if "MJD-AVG" in hdr else float(hdr["MJD-OBS"])
        cflags = int(np.bitwise_or.reduce(flg[half - 2:half + 3, half - 2:half + 3].ravel()))
        meta.update({
            "ok": True, "obsid": hdr.get("OBSID"), "detector": int(hdr.get("DETECTOR")),
            "mjd": mjd, "utc": Time(mjd, format="mjd").isot[:19] + "Z", "exptime_s": float(hdr.get("XPOSURE", 0)),
            "wavelength_um": wl, "bandwidth_um": bw, "x_full": x, "y_full": y, "pixel_scale_arcsec": scale,
            "version": "", "release": key.split("/")[0].upper(), "source_uri": irsa_url(key), "s3_uri": https_url(key),
            "psf_fwhm_arcsec": float(hdr.get("PSF_FWHM", np.nan)),
            "sc_xyz_km": [float(hdr.get("X_SC", np.nan)), float(hdr.get("Y_SC", np.nan)), float(hdr.get("Z_SC", np.nan))],
            "bad_fraction": float(np.mean(bad)),
            "bad_fraction_center": float(np.mean(bad[half - 3:half + 4, half - 3:half + 4])),
            "center_flags": cflags, "background_method": "sigma-clipped median (lean extractor)",
            "noise_std_mjysr": float(std),
            "wcs_header": sub_wcs.to_header(relax=True).tostring(sep="\n"),
        })
        np.savez_compressed(out, img=img, flg=flg, var=var, zod=zod)
    except Exception as e:
        meta["reason"] = f"error: {e!r}"[:300]
        return None
    meta_path.write_text(json.dumps(meta))
    return meta


def extract_many_fast(keys, ra, dec, name, half=60, workers=8):
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda k: extract_fast(k, ra, dec, name, half), keys))
    return [r for r in res if r]


# Saturation-type flags: kept for DISPLAY on pixels SPHEREx maps to a known source (bit 21), so bright
# stars do not become holes. Their brightness is unreliable; photometry still treats them as bad.
SAT_BITS = {0: "TRANSIENT", 2: "SUR_ERROR", 15: "NONLINEAR", 26: "BLOOM"}
SAT_MASK = sum(1 << b for b in SAT_BITS)
SOURCE_BIT = 1 << 21


def display_bad(flg):
    bad = (flg & BAD_MASK) != 0
    keep = ((flg & SOURCE_BIT) != 0) & ((flg & (BAD_MASK & ~SAT_MASK)) == 0)
    return bad & ~keep
