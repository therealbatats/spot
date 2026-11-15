# SPOT - validation check 5: random frames' source links open and match date + detector shown.
# Written with AI assistance under the direction of Ali (team AITHMAC).
import json, random, sys, time
from pathlib import Path
import requests
from astropy.io import fits
ROOT = Path(__file__).resolve().parent.parent
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 15)
frames = []
for fj in sorted((ROOT / "site/data/fields").glob("*/field.json")):
    f = json.loads(fj.read_text())
    frames += [(f["id"], fr) for fr in f["frames"]]
for fid, fr in random.sample(frames, 5):
    url = fr["source_uri"]
    t0 = time.time()
    try:
        r = requests.get(url, headers={"Range": "bytes=0-31679"}, timeout=90)
        b = r.content
        s = b[2880:].decode("latin-1")
        end = next(i for i in range(0, len(s), 80) if s[i:i + 8] == "END     ")
        h = fits.Header.fromstring(s[:end + 80])
        ok = (int(h["DETECTOR"]) == fr["detector"]) and (h["OBSID"] == fr["obsid"]) and abs(float(h["MJD-AVG"]) - fr["mjd"]) < 1e-5
        print(f"| {fid} | {fr['obsid']} D{fr['detector']} | {fr['utc']} | HTTP {r.status_code} in {time.time()-t0:.1f}s | file says D{h['DETECTOR']}, {h['OBSID']}, DATE-AVG {h['DATE-AVG']} | {'MATCH' if ok else 'MISMATCH'} |")
    except Exception as e:
        print(f"| {fid} | {fr['obsid']} D{fr['detector']} | {fr['utc']} | FAILED: {e!r:.120} | – | not verified |")
