# SPOT — Sky Patches Over Time

*The sky looks still. It isn't.*

<!-- Written with AI assistance under the direction of Ali (team AITHMAC). -->

**Live site:** https://therealbatats.github.io/spot/  
**Demo deck (PDF):** https://therealbatats.github.io/spot/deck/SPOT_deck.pdf
**Team:** AITHMAC (Ali, Baghdad) — 2026 NASA Space Apps Challenge, challenge *"Planet X and SPHEREx"*.

SPOT (Sky Patches Over Time) is a free public website that shows real images from NASA's SPHEREx infrared space telescope and makes it easy to see how a patch of sky changes over time. Pick a ready-made field or type any coordinates, then **blink**, **swipe**, **subtract**, **add** or **play** the images taken months apart. Stars that are close to us drift; variable stars change brightness; distant galaxies stay still.

## What it does
- **Any coordinates (live mode):** type RA/Dec (or put `?ra=..&dec=..` in the URL). If the position is not a ready-made field, the browser finds every SPHEREx image that contains it using our visit index, reads only the needed bytes of each file straight from NASA/IPAC's public AWS copy, lines the images up and shows them. No server of ours is involved.
- **Ready-made fields:** the five test targets from the challenge (Barnard's Star, Epsilon Indi B, WISE 0855−0714, RW Aurigae, R Draconis) plus a control galaxy (M101), processed with the full pipeline.
- **Compare modes:** Blink, Swipe, Difference (B − A), Timeline (a little video), Add all.
- **Two kinds of comparison:** *whole detector band* (all frames one of SPHEREx's six detectors took during a visit, added for signal-to-noise) and *one exact wavelength* (single frames whose wavelength at the target agrees to within half a filter width).
- **Spectrum on the fly:** brightness of the target in every frame, plotted against wavelength and coloured by date.
- **WISE 2010 ↔ SPHEREx 2026:** for the fast movers, blink an AllWISE image from 2010 against SPHEREx on the same grid. Barnard's Star moves a measured 27.1 px (predicted 27.3), WISE 0855 20.7 px (predicted 20.9).
- **Overlays:** predicted target position for each date (proper motion + parallax), Gaia DR3 stars moved to the image date, flagged/missing pixels.
- **Provenance:** every frame with date, detector, wavelength, flagged-pixel fraction and a link to the original file.
- **Spot the wanderer:** a small game: markers hidden, tap what moved.
- **Planet X simulator:** draws a clearly labelled SIMULATED planet into the real images at a distance you choose, moving as parallax and orbital motion would move it; plus an honest note on whether SPHEREx could see such a planet.
- **Shareable links:** field, band, mode and dates are kept in the URL.

## How it works
```
IRSA public AWS bucket (nasa-irsa-spherex)
   │  list folders + read 32 KB header of every visit        pipeline/s3index.py
   ▼
visit index (pointing, time) ──► search: which files contain RA/Dec?   pipeline/search.py
   │                                   │
   │                                   ▼
   │                     byte-range cutouts: IMAGE + FLAGS rows only   pipeline/frames.py
   │                                   ▼
   │       robust median background subtraction, flag masking, reprojection to one north-up grid,
   │       per-visit band coadds, wavelength-matched channels, differences, photometry   pipeline/make_field.py
   │                                   ▼
   └──► site/data/live/*.json     site/data/fields/<id>/*.png + field.json + manifest.json
                    │                              │
                    ▼                              ▼
          live mode in the browser (site/live.js)   viewer (site/index.html, app.js) on GitHub Pages
```
Why the index? On November 15, 2026, IRSA's search API (TAP and SIA) returned HTTP 502 in our probes from 1:41 PM until at least 5:55 PM Baghdad time. The same files are mirrored on AWS, and every file header holds its pointing and time, so we built our own index of 97,434 SPHEREx visits in DR1 and QR3 (one 32 KB header read per visit). About 3.7% of visits (those without an exposure-1, detector-2 file) are not in the index.

## Run the pipeline
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python pipeline/s3index.py 1            # index every visit (≈20–30 min, cached)
.venv/bin/python pipeline/make_field.py --target barnard
.venv/bin/python pipeline/make_field.py --ra 210.80227 --dec 54.34895 --name myfield --size 0.2
.venv/bin/python pipeline/export_live.py          # files for live mode
.venv/bin/python pipeline/build_manifest.py
python3 -m http.server 8765 --directory site      # open http://localhost:8765
```
New data releases: re-run `s3index.py` (it lists the bucket folders again) and the field builds.

## Data and citation
- SPHEREx Level-2 spectral images, NASA/IPAC Infrared Science Archive (IRSA): DR1 spectral images DOI [10.26131/IRSA678](https://doi.org/10.26131/IRSA678); QR3 spectral images DOI [10.26131/IRSA662](https://doi.org/10.26131/IRSA662). Read from IRSA's AWS mirror `s3://nasa-irsa-spherex` (https://irsa.ipac.caltech.edu/cloud_access/).
- Required acknowledgement: "This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."
- Gaia DR3 (ESA), queried through MAST TAP. WISE 0855−0714 motion: Luhman & Esplin 2016 (AJ 152, 78).
- Method follows the IRSA SPHEREx tutorials: https://caltech-ipac.github.io/irsa-tutorials/spherex/

## How this was made
Parts of the code and text were written with AI assistance and reviewed by the author. Every source file starts with an AI-assistance note, and the data manifest carries `"ai_assisted": true`. **All sky images are real SPHEREx data**; the only simulated element is the Planet X dot, which is drawn by the website and labelled SIMULATED. No images were generated by AI. No NASA or mission logos are used.

## License
Code: MIT License (see `LICENSE`). SPHEREx data are NASA data distributed by IRSA; see IRSA's terms and the citation above.

Not an official NASA product.
