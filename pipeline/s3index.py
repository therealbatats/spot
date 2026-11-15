# SPOT pipeline - S3 pointing index (fallback when IRSA TAP search is unavailable).
# Written with AI assistance under the direction of Ali (team AITHMAC).
#
# The SPHEREx Level-2 spectral images are mirrored in the public AWS bucket `nasa-irsa-spherex`
# (https://irsa.ipac.caltech.edu/cloud_access/). Key paths mirror IRSA's IBE paths, e.g.
#   qr3/level2/2026W20_2A/l2b-v27-2026-267/2/level2_2026W20_2A_0464_4D2_spx_l2b-v27-2026-267.fits
# This module lists keys and reads only the first ~32 KB of a file (an HTTP Range request) to
# get the IMAGE header (pointing, time). No credentials needed.
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from astropy.io import fits

BUCKET = "https://nasa-irsa-spherex.s3.amazonaws.com/"
CACHE = Path(__file__).resolve().parent.parent / "cache" / "s3"
CACHE.mkdir(parents=True, exist_ok=True)
KEY_RE = re.compile(r"(?P<rel>dr1|qr3|qr2)/level2/(?P<week>[^/]+)/(?P<ver>[^/]+)/(?P<det>\d)/"
                    r"level2_(?P=week)_(?P<visit>\d{4})_(?P<exp>\d+)D(?P=det)_spx_(?P=ver)\.fits$")
SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=48, pool_maxsize=48, max_retries=3)
SESSION.mount("https://", adapter)


def _get(url, **kw):
    for k in range(5):
        try:
            r = SESSION.get(url, timeout=60, **kw)
            if r.status_code in (200, 206):
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * 2 ** k)
    raise RuntimeError(f"S3 GET failed: {url}")


def list_prefix(prefix, delimiter=None):
    keys, prefixes, tok = [], [], None
    while True:
        p = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if delimiter:
            p["delimiter"] = delimiter
        if tok:
            p["continuation-token"] = tok
        t = _get(BUCKET, params=p).text
        keys += re.findall(r"<Key>([^<]+)</Key>", t)
        prefixes += re.findall(r"<Prefix>([^<]+)</Prefix>", t)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", t)
        if not m:
            return keys, [x for x in prefixes if x != prefix]
        tok = m.group(1)


def week_dirs(releases=("dr1", "qr3")):
    out = CACHE / "weekdirs.json"
    if out.exists():
        return json.loads(out.read_text())
    dirs = []
    for rel in releases:
        dirs += list_prefix(f"{rel}/level2/", "/")[1]
    out.write_text(json.dumps(dirs))
    return dirs


def dir_keys(d):
    """All FITS keys in one week dir, parsed. Cached. If a visit/exp/det has several processing
    versions (e.g. 'l2b' and 'l2b_retry'), keep the lexically last version string."""
    out = CACHE / ("keys_" + d.strip("/").replace("/", "_") + ".json")
    if out.exists():
        return json.loads(out.read_text())
    keys, _ = list_prefix(d)
    best = {}
    for k in keys:
        m = KEY_RE.search(k)
        if not m:
            continue
        g = m.groupdict()
        ident = (g["visit"], g["exp"], g["det"])
        if ident not in best or g["ver"] > best[ident]["ver"]:
            best[ident] = {"key": k, **g}
    rows = sorted(best.values(), key=lambda r: (r["visit"], r["exp"], r["det"]))
    out.write_text(json.dumps(rows))
    return rows


HDR_CARDS = ["OBSID", "DETECTOR", "MJD-OBS", "MJD-END", "DATE-OBS", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
             "PC1_1", "PC1_2", "PC2_1", "PC2_2", "CTYPE1", "CTYPE2", "SPS_FLAGS", "NON_SURVEY", "SPS_ELON",
             "SPS_ELAT", "L2DQAFLG", "PSF_FWHM", "X_SC", "Y_SC", "Z_SC"]


def read_header(key, nbytes=31680):
    """IMAGE (HDU 1) header from the first bytes of the file, via one HTTP Range request."""
    r = _get(BUCKET + key, headers={"Range": f"bytes=0-{nbytes - 1}"})
    if r is None:
        return None
    s = r.content[2880:].decode("latin-1")
    for i in range(0, len(s), 80):
        if s[i:i + 8] == "END     ":
            return fits.Header.fromstring(s[:i + 80])
    if nbytes < 60000:
        return read_header(key, nbytes * 2)
    raise ValueError("no END card in " + key)


def header_summary(key):
    h = read_header(key)
    if h is None:
        return None
    d = {"key": key}
    for c in HDR_CARDS:
        v = h.get(c)
        d[c] = v.item() if hasattr(v, "item") else v
    return d


def sample_dir(d, every=1, exp="1", det="2"):
    """Header summaries for exposure `exp` of every `every`-th visit, detector `det`. Cached."""
    out = CACHE / f"sample_{d.strip('/').replace('/', '_')}_e{exp}_d{det}_n{every}.json"
    if out.exists():
        return json.loads(out.read_text())
    rows = [r for r in dir_keys(d) if r["exp"] == exp and r["det"] == det]
    visits = sorted({r["visit"] for r in rows})[::every]
    sel = [r["key"] for r in rows if r["visit"] in set(visits)]
    with ThreadPoolExecutor(32 if every == 1 else 16) as ex:
        res = [x for x in ex.map(header_summary, sel) if x]
    out.write_text(json.dumps(res))
    return res


if __name__ == "__main__":
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t0 = time.time()
    dirs = week_dirs()
    print(len(dirs), "week dirs", flush=True)
    with ThreadPoolExecutor(6) as ex:
        for d, rows in zip(dirs, ex.map(dir_keys, dirs)):
            pass
    print(f"listed all dirs in {time.time() - t0:.0f}s", flush=True)
    for i, d in enumerate(dirs):
        s = sample_dir(d, every=every)
        print(i, d, len(s), f"{time.time() - t0:.0f}s", flush=True)
