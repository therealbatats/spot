# SPOT pipeline - find every SPHEREx frame that contained Pluto when it was taken (JPL Horizons ephemeris).
# Written with AI assistance under the direction of Ali (team AITHMAC).
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from astropy.table import Table
from astropy.time import Time

import s3index as S
from search import angsep, contains

ROOT = Path(__file__).resolve().parent.parent
EPH = ROOT / "cache" / "pluto_ephem.ecsv"
OUT = ROOT / "cache" / "search_pluto.json"


def ephem():
    e = Table.read(EPH)
    mjd = Time([str(x) for x in e["datetime_str"]], format="iso", scale="utc").mjd if False else \
        np.array([Time(str(x).replace("Jan", "01").replace("Feb", "02").replace("Mar", "03").replace("Apr", "04")
                       .replace("May", "05").replace("Jun", "06").replace("Jul", "07").replace("Aug", "08")
                       .replace("Sep", "09").replace("Oct", "10").replace("Nov", "11").replace("Dec", "12")).mjd for x in e["datetime_str"]])
    return mjd, np.array(e["RA"], float), np.array(e["DEC"], float)


def pos(mjd, E):
    m, ra, dec = E
    return float(np.interp(mjd, m, np.unwrap(np.radians(ra)) * 180 / np.pi) % 360), float(np.interp(mjd, m, dec))


def find():
    if OUT.exists():
        return json.loads(OUT.read_text())
    E = ephem()
    near = []
    for d in S.week_dirs():
        for x in S.sample_dir(d, every=1):
            ra, dec = pos(x["MJD-OBS"], E)
            if angsep(ra, dec, x["CRVAL1"], x["CRVAL2"]) < 8.5:
                near.append((d, x["key"].split("/")[-1].split("_")[3]))
    cand = [r["key"] for d, v in near for r in S.dir_keys(d) if r["visit"] == v]
    print(len(near), "visits near Pluto;", len(cand), "files to check", flush=True)

    def chk(key):
        h = S.read_header(key)
        if h is None:
            return None
        ra, dec = pos(float(h["MJD-OBS"]), E)
        ok, x, y = contains(h, ra, dec, margin=90)
        return {"key": key, "x": x, "y": y, "mjd": float(h["MJD-OBS"]), "det": int(h["DETECTOR"]), "obsid": h["OBSID"],
                "ra": ra, "dec": dec} if ok else None

    with ThreadPoolExecutor(16) as ex:
        hits = [h for h in ex.map(chk, cand) if h]
    hits.sort(key=lambda r: r["mjd"])
    OUT.write_text(json.dumps(hits))
    return hits


if __name__ == "__main__":
    t0 = time.time()
    h = find()
    print(len(h), "frames contain Pluto", round(time.time() - t0), "s")
    from collections import Counter
    print(Counter(Time(x["mjd"], format="mjd").isot[:10] for x in h).most_common(25))
