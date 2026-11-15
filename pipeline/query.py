# SPOT pipeline - query step.
# Written with AI assistance under the direction of Ali (team AITHMAC).
# Queries IRSA TAP for every SPHEREx spectral image (all 6 detectors) whose footprint contains a sky position.
# Method follows the IRSA "SPHEREx cutouts" tutorial:
#   https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/
import json
import sys
import time
from pathlib import Path

from astroquery.ipac.irsa import Irsa

CACHE = Path(__file__).resolve().parent.parent / "cache"


def query_position(ra, dec, name, retries=4):
    """Return list of dicts: uri (full image), time_bounds_lower (MJD), bandpass, obs_id. Cached on disk."""
    CACHE.mkdir(exist_ok=True)
    out = CACHE / f"query_{name}.json"
    if out.exists():
        return json.loads(out.read_text())
    adql = f"""
SELECT a.uri, p.time_bounds_lower, p.time_bounds_upper, p.energy_bandpassname, p.obsid, a.planeid
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
ORDER BY p.time_bounds_lower
"""
    last = None
    for k in range(retries):
        try:
            t0 = time.time()
            res = Irsa.query_tap(adql).to_table()
            print(f"TAP query {name}: {len(res)} rows in {time.time()-t0:.1f}s", file=sys.stderr)
            rows = []
            for r in res:
                rows.append({
                    "uri": str(r["uri"]),
                    "mjd_start": float(r["time_bounds_lower"]),
                    "mjd_end": float(r["time_bounds_upper"]),
                    "bandpass": str(r["energy_bandpassname"]),
                    "obsid": str(r["obsid"]),
                })
            out.write_text(json.dumps(rows, indent=1))
            return rows
        except Exception as e:  # network / service errors: back off and retry
            last = e
            wait = 5 * 2 ** k
            print(f"TAP query failed ({e!r}); retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"TAP query failed after {retries} tries: {last!r}")


if __name__ == "__main__":
    ra, dec, name = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    rows = query_position(ra, dec, name)
    from collections import Counter
    print(len(rows), Counter(r["bandpass"] for r in rows))
    for r in rows[:3]:
        print(r)
