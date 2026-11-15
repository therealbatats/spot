# SPOT — Sky Patches Over Time

*The sky looks still. It isn't.*

Version 1.0.0 · November (11) 15, 2026 · Team AITHMAC (Ali, Baghdad) · 2026 NASA Space Apps Challenge, "Planet X and SPHEREx"

**Live site:** https://aithmac.earth/
**Demo deck (PDF):** https://aithmac.earth/deck/SPOT_deck.pdf
**Demo video (28 s):** https://aithmac.earth/deck/SPOT_demo.mp4

SPOT is a free website that turns real images from NASA's SPHEREx infrared space telescope into a little video of any patch of sky. Type coordinates, or pick a target, and blink, swipe, subtract, add or play images taken days, months or (with NASA's older WISE telescope) sixteen years apart. Nearby stars and brown dwarfs drift, Pluto walks past the stars, variable stars change brightness, and distant galaxies stay still.

## What it does
- **Any coordinates, live.** Type RA/Dec (or put `?ra=..&dec=..` in the URL). If the position is not a ready-made field, the visitor's browser finds every SPHEREx image that contains it, reads only the bytes it needs straight from NASA/IPAC's public AWS copy of the archive, lines the images up and plays them. No server of ours is involved.
- **Seven ready-made fields:** the five test targets named in the challenge (Barnard's Star, Epsilon Indi B, WISE 0855−0714, RW Aurigae, R Draconis), Pluto, and the galaxy M101 as a control where nothing should change.
- **Compare:** Blink (starts by itself), Swipe, Difference, Timeline, Add all. Zoom 1–4×, brightness, contrast, plate view, compass, scale bar and live RA/Dec readout.
- **Honest Difference:** by default a significance map, so stars that did not change stay grey; the raw difference is one click away.
- **WISE 2010 ↔ SPHEREx 2026:** for the fast movers, an AllWISE image is put on the same grid. Barnard's Star moves a measured 27.1 px (predicted 27.3); WISE 0855 20.7 px (predicted 20.9).
- **Pluto, the first Planet X:** 75 SPHEREx frames over eight days of October 2025, one image per day, with the JPL Horizons track.
- **Light:** each of SPHEREx's six detector bands added per visit (more signal, using only wavelengths every visit covered), or single frames at one exact wavelength. A wavelength ruler shows where each band sits.
- **Brightness over time and spectrum by date,** with the measured noise floor shown, and CSV download.
- **Provenance:** every frame with date, detector, wavelength, flagged-pixel share and a link to the original file.
- **Spot the wanderer** game and a **Planet X simulator** that draws a clearly labelled SIMULATED planet with real parallax geometry.

## How it works
```
IRSA public AWS mirrors (nasa-irsa-spherex, nasa-irsa-wise)
   │ list week folders, read the 32 KB header of every SPHEREx visit           pipeline/s3index.py
   ▼
visit index (97,434 visits) ─► which files contain RA/Dec?                       pipeline/search.py
   │                                 │
   │                                 ▼
   │                  byte-range cutouts: IMAGE + RICE-compressed FLAGS rows    pipeline/frames.py
   │                                 ▼
   │   outer-border median background, flag masking, reprojection to one north-up grid,
   │   per-visit band coadds with outlier rejection, wavelength-matched channels,
   │   significance differences, photometry, light curves, WISE epoch           pipeline/make_field.py
   │                                 ▼
   └─► site/data/live/*.json   site/data/fields/<id>/*.png + field.json + manifest.json
                 │                               │
                 ▼                               ▼
      live mode in the browser (site/live.js)    viewer (site/index.html, app.js, hero.js)
```
Why our own index? On November 15, 2026, IRSA's search API (TAP, SIA and the image search) returned HTTP 502 in our probes from 1:41 PM until at least 5:55 PM Baghdad time. The same files are mirrored on AWS and every file header holds its pointing and time, so we indexed 97,434 SPHEREx visits in DR1 and QR3 ourselves. About 3.7% of visits (those without an exposure-1, detector-2 file) are not in the index.

## Validation (details in `VALIDATION.md`)
- Alignment: Gaia stars land 0.03–0.35 px from their catalogue positions in the star fields (Pluto's single-day images 0.11–0.56 px; 1 px = 6.15″).
- Movers: Barnard's Star within 0.43 px of prediction in all 18 band-visits; Pluto within 1.05 px of JPL Horizons in all 26 band-days.
- Control: 2 regions with |S| ≥ 5 in 18 M101 differences; galaxy brightness steady to 1–6%.
- Provenance: 15/15 random frames traced to IRSA's original files.
- Our search finds all 17 files that IRSA's own tutorial lists for its example position.

## Run the pipeline
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python pipeline/s3index.py 1            # index every visit (about 20–30 min, cached)
.venv/bin/python pipeline/export_live.py          # files for live mode
.venv/bin/python pipeline/make_field.py --target barnard
.venv/bin/python pipeline/make_field.py --ra 210.80227 --dec 54.34895 --name myfield --size 0.2
.venv/bin/python pipeline/build_manifest.py
python3 -m http.server 8765 --directory site      # open http://localhost:8765
```
New data releases: re-run `s3index.py` (it lists the bucket folders again), then the field builds.

## Data and credits
- SPHEREx Level-2 spectral images, NASA/IPAC Infrared Science Archive (IRSA): DR1 DOI [10.26131/IRSA678](https://doi.org/10.26131/IRSA678); QR3 DOI [10.26131/IRSA662](https://doi.org/10.26131/IRSA662). Read from `s3://nasa-irsa-spherex`. "This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."
- AllWISE Atlas W2 images (NASA WISE, 2010) from `s3://nasa-irsa-wise`. "This publication makes use of data products from the Wide-field Infrared Survey Explorer, which is a joint project of the University of California, Los Angeles, and the Jet Propulsion Laboratory/California Institute of Technology, funded by the National Aeronautics and Space Administration."
- Gaia DR3 (ESA), through MAST. Pluto ephemeris: NASA JPL Horizons. R Draconis period: AAVSO Variable Star Index. WISE 0855 motion: Luhman & Esplin 2016, AJ 152, 78, Table 4.
- Method follows the IRSA SPHEREx tutorials: https://caltech-ipac.github.io/irsa-tutorials/spherex/
- Font: IBM Plex Sans (SIL Open Font License, `site/fonts/OFL.txt`), self-hosted.
- Animation: GSAP 3.12.5 core (GSAP Standard "No Charge" License, https://gsap.com/standard-license; notice kept in `site/vendor/gsap.min.js`) and Lenis 1.1.13 (MIT, `site/vendor/LENIS_LICENSE.txt`), both self-hosted. Neither ever animates between two sky images; both are off under reduced motion.
- Click sparks and magnetic buttons: plain-JavaScript ports of the React Bits components ClickSpark and Magnet by David Haz (https://reactbits.dev), used under the React Bits license (MIT + Commons Clause, `site/vendor/REACTBITS_LICENSE.md`). The site has no React or build step, so the effects were ported rather than installed.
- No cookies, no analytics, no accounts. Outside requests: the AWS data mirrors (live mode only).

## How this was made
Parts of the code and text were written with AI assistance and reviewed by the author. Every source file starts with an AI-assistance note, and the data manifest carries `"ai_assisted": true`. All sky images are real telescope data (SPHEREx and WISE); the only simulated element is the Planet X dot, which the website draws and labels SIMULATED. The twinkling star background behind the page is decoration, not data, and never appears inside the image viewer. No images were generated by AI. No NASA or mission logos are used.

## License
Code: MIT License (`LICENSE`), except the third-party files in `site/vendor/` and `site/fonts/`, which keep their own licenses. SPHEREx and WISE data are NASA data distributed by IRSA; cite them as above.

Not an official NASA product.
