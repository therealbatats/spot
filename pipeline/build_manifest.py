# SPOT pipeline - collect built fields into site/data/manifest.json.
# Written with AI assistance under the direction of Ali (team AITHMAC).
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CONFIG = json.loads((ROOT / "config.json").read_text())
TARGETS = {t["id"]: t for t in json.loads((Path(__file__).parent / "targets.json").read_text())["fields"]}
KIND_LABEL = {"mover": "moves", "variable": "changes brightness", "control": "control: nothing changes", "custom": "custom"}

ABOUT = """
<h3>What is SPHEREx?</h3>
<p>SPHEREx is a NASA space telescope launched in March 2025. It photographs the whole sky every six months in 102 colours of infrared light, from 0.75 to 5 micrometres (µm). Infrared means "redder than red": light our eyes cannot see, which is good for cold things like brown dwarfs and dust.</p>
<p>Its camera has six detectors. Each detector sits behind a special filter whose colour changes smoothly from one edge to the other. So every time SPHEREx takes a picture, the same star is seen in a slightly different colour. That is clever for building a spectrum, but it means you must be careful when comparing two pictures.</p>
<h3>How SPOT compares images fairly</h3>
<ol>
<li><strong>Find every image.</strong> For each patch of sky we find every SPHEREx Level-2 image that contains it, using the image headers in NASA/IPAC's public cloud copy of the archive.</li>
<li><strong>Cut out only what we need.</strong> We read just the small square around the target from each image (a few megabytes instead of 65).</li>
<li><strong>Clean.</strong> We remove the smooth background glow, mostly zodiacal light (sunlight scattered by dust between the planets), by subtracting a robust (sigma-clipped) median brightness measured in each cutout, and we hide pixels the SPHEREx pipeline flagged as unreliable (cosmic-ray hits, hot pixels, ghosts and so on).</li>
<li><strong>Line up.</strong> Every image is reprojected onto one shared grid with north up, using each image's own sky coordinates, so stars land on the same pixels.</li>
<li><strong>Compare like with like.</strong> "Whole detector band" adds all images one detector took during one visit, then compares visits. "One exact wavelength" only compares single images whose colour at the target differs by less than half a filter width.</li>
<li><strong>Same brightness scale.</strong> All dates in one view share a single brightness scale, so a star that looks brighter really is brighter, not just displayed differently.</li>
</ol>
<h3>Comparing with WISE (2010)</h3>
<p>For the fast movers, SPOT can also show the same patch as seen by NASA's earlier WISE telescope around 2010, put on exactly the same grid. Sixteen years make motions about ten times larger: Barnard's Star moved a measured 27.1 pixels (predicted 27.3) and WISE 0855 moved 20.7 pixels (predicted 20.9).</p>
<h3>Why things move</h3>
<p>Nearby stars travel through the Galaxy, so over months they creep across the sky (<em>proper motion</em>). Earth also circles the Sun, so nearby objects seem to wobble back and forth once a year (<em>parallax</em>). Pluto was found in 1930 exactly this way: by comparing two photographs and spotting the dot that moved.</p>
<h3>Limits (please read)</h3>
<ul>
<li>SPHEREx pixels are large: 6.2 arcseconds. A motion smaller than about one pixel is hard to see by eye.</li>
<li>Brightness here is measured inside a small circle and is not fully calibrated. Use it to compare dates, not as a final science measurement.</li>
<li>Artifacts (cosmic rays, ghosts of bright stars, satellites) can look like new objects. A real object must appear in more than one image. If you think you found something, it is a <em>candidate needing follow-up</em>, not a discovery.</li>
<li>The ready-made fields were processed on November 15, 2026 from the data releases available that day. Any new position can be processed with the open pipeline (one command).</li>
<li>The Planet X simulator draws a pretend planet. It is clearly labelled SIMULATED and is much brighter than a real distant planet would be.</li>
</ul>
<h3>Could SPHEREx see Planet X?</h3>
<p>Probably not, except perhaps in the most favourable case. Planet Nine would shine only by faint reflected sunlight. Brown &amp; Batygin (2016) put it at about visual magnitude 22 to 25; their 2021 update finds a closer orbit (about 380 AU) and says its brightest cases could already have been detected by existing surveys. SPHEREx is designed to reach magnitude 18.4 (AB) or fainter per wavelength channel at 2 µm after its full two-year survey (Crill et al. 2020, Table 1), and a single six-month pass is shallower. Visible and infrared magnitudes are different scales and the planet's infrared brightness depends on its unknown atmosphere, so this comparison is approximate, but a gap of 3.5 magnitudes or more is a factor of 25 or more in brightness.  Sources: Brown, M. E. &amp; Batygin, K. 2016, ApJL 824, L23 (arXiv:1603.05712); Brown &amp; Batygin 2021, AJ 162, 219 (arXiv:2108.09868); Crill, B. P. et al. 2020, Proc. SPIE 11443 (arXiv:2404.11017).</p>
<h3>Data and credits</h3>
<p>SPHEREx Level-2 spectral images: NASA/IPAC Infrared Science Archive (IRSA). DR1 spectral images DOI <a href="https://doi.org/10.26131/IRSA678">10.26131/IRSA678</a>; QR3 spectral images DOI <a href="https://doi.org/10.26131/IRSA662">10.26131/IRSA662</a>. Read from IRSA's public AWS mirror (bucket <code>nasa-irsa-spherex</code>). "This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."</p>
<p>Older epoch: NASA's Wide-field Infrared Survey Explorer (WISE), AllWISE Atlas images in the W2 band (4.6 µm), observed in 2010, read from IRSA's public AWS mirror (bucket <code>nasa-irsa-wise</code>). "This publication makes use of data products from the Wide-field Infrared Survey Explorer, which is a joint project of the University of California, Los Angeles, and the Jet Propulsion Laboratory/California Institute of Technology, funded by the National Aeronautics and Space Administration." WISE and SPHEREx are different telescopes: compare positions between them, not brightness.</p>
<p>Star positions and motions: ESA Gaia DR3 (via MAST). WISE 0855−0714 parallax and motion: Luhman &amp; Esplin 2016, AJ 152, 78, Table 4. R Draconis period: AAVSO Variable Star Index (VSX). Software: Astropy, astroquery, reproject, NumPy, Pillow (Python); the website is plain HTML and JavaScript.</p>
<h3>Use of artificial intelligence</h3>
<p>Parts of the code and text were written with AI assistance and reviewed by the author. <strong>All sky images are real SPHEREx telescope data</strong>, except the Planet X dot, which is a labelled simulation drawn by the website. No image on this site was generated by AI.</p>
"""


def main():
    fields = []
    order = CONFIG.get("field_order", [])
    for d in sorted((SITE / "data" / "fields").iterdir(), key=lambda p: order.index(p.name) if p.name in order else 99):
        fj = d / "field.json"
        if not fj.exists():
            continue
        f = json.loads(fj.read_text())
        t = TARGETS.get(f["id"], {})
        story = t.get("story", {})
        if story:
            f["story"] = story
            fj.write_text(json.dumps(f, indent=1))
        thumb_det = story.get("best_band") or (f["bands"][0]["detector"] if f["bands"] else 2)
        b = next((x for x in f["bands"] if x["detector"] == thumb_det), f["bands"][0] if f["bands"] else None)
        if not b:
            continue
        fields.append({"id": f["id"], "title": f["title"], "kind": f["kind"], "kind_label": KIND_LABEL.get(f["kind"], f["kind"]),
                       "hook": story.get("hook", ""), "thumb": b["epochs"][0]["png"], "ra_deg": f["ra_deg"], "dec_deg": f["dec_deg"],
                       "size_deg": f["size_deg"], "n_frames": len(f["frames"]), "n_visits": len(f.get("track", []))})
    rel = sorted({fr["release"] for d in (SITE / "data" / "fields").iterdir() if (d / "field.json").exists()
                  for fr in json.loads((d / "field.json").read_text())["frames"]})
    man = {"app_name": CONFIG["app_name"], "tagline": CONFIG["tagline"], "repo_url": CONFIG.get("repo_url", ""),
           "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "data_releases": rel,
           "citation": "SPHEREx DR1 spectral images, DOI 10.26131/IRSA678; SPHEREx QR3 spectral images, DOI 10.26131/IRSA662 (NASA/IPAC IRSA).",
           "generator": "SPOT pipeline 1.0.0",
           "ai_assisted": True,
           "about_html": ABOUT, "fields": fields}
    (SITE / "data" / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print(len(fields), "fields:", [f["id"] for f in fields])


if __name__ == "__main__":
    main()
