# VALIDATION — SPOT

<!-- Written with AI assistance under the direction of Ali (team AITHMAC). Numbers below are pasted from commands run on November (11) 15, 2026. -->

Scripts: `pipeline/validate.py` (checks 1–4), `pipeline/check_provenance.py` (check 5). A check not run is marked "not run".

## Summary

| # | Check | Result |
|---|---|---|
| 1 | Alignment | **Pass.** Median distance between measured centroids and Gaia DR3 positions (moved to each date) of isolated G = 9–14 stars: 0.03–0.29 px (0.2–1.8″) in the five star fields, every band and visit. M101: 0.37–0.57 px from only 1–3 stars sitting on galaxy light; the value is the same in every visit (an offset, not a misalignment between dates). |
| 2 | Wavelength matching | **Pass.** All 36 exact-wavelength channels (6 per field): every pair of frames differs by less than half the narrowest bandwidth (tables below). Band views use only the wavelength range shared by all visits; visits with too little shared range are dropped from that band (logged). |
| 3 | Known mover | **Pass.** Barnard's Star measured in all 18 band-visits: 0.07–0.44 px (0.4–2.7″) from the Gaia prediction; measured northward motion in D6 between Aug 2025 and Aug 2026 = 1.69 px vs predicted 1.67 px (10.2″). Epsilon Indi B: within ~0.1 px of prediction over 4 visits; measured shift 0.91–0.98 px vs predicted 1.06 px over 1.4 yr. WISE 0855: in D5 the centroid moves +1.28 px west in a year vs +1.35 px predicted, while at 0.75–3.8 µm the light near the position stays fixed (a Gaia G = 16.3 star 7.8″ away). *Consistent with* SPHEREx seeing WISE 0855; not proven. Solar-system movers (asteroids/comets) were not attempted (cut for time). |
| 4 | Control field (M101) | **Pass.** No candidates flagged. Difference images: fraction of pixels at ± full scale of the symmetric stretch 0.07–0.73% per band (≈0.5% expected from the 99.5th-percentile stretch alone). Band brightness of the galaxy core varies 2–6% between visits — this is our stated noise floor for "brightness over time". |
| 5 | Provenance | **Pass.** 10 random frames (two samples of 5): IRSA source link opened (HTTP 206, range request) and the file's DETECTOR, OBSID and DATE-AVG match what the site shows. 10/10 MATCH. |
| 6 | Simulation labelling | Checked locally: banner "SIMULATED planet shown — not real data" visible whenever the simulator is on; dot drawn inside a dashed pink box labelled "SIMULATED"; off-field case shows an arrow labelled "SIMULATED planet: off field". Live-site screenshot: SEE_LIVE_6 |
| 7 | Live site | SEE_LIVE_7 |
| 8 | Size and speed | Initial page (HTML+CSS+JS+manifest) 79 KB + 6 thumbnails 35 KB ≈ 115 KB uncompressed (limit 2 MB). Opening a field: field.json 130–200 KB + 2–3 PNGs (10–25 KB each). Live mode: visit index 4.0 MB raw / 1.5 MB gzip, loaded only on first live request; a Barnard's Star live request (D2, 0.1°) finished in < 40 s locally (31 frames). Time to first image on the public site: SEE_LIVE_8 |
| 9 | Links | All links a visitor can click return 200/206: DOIs (2), IRSA pages (3), IRSA tutorials, WiseView, MAST Gaia, MAST TAP, AWS bucket, challenge page, GitHub. Expected non-OK: IRSA TAP 502 (the outage we describe); two Canadian Space Agency pages timed out from Baghdad (only in `CHALLENGE.md`, copied resource list). |
| 10 | Text truth | SEE_LIVE_10 |

## Independent check of the file search
IRSA's own cutouts tutorial lists 17 detector-2 files covering its M101 example position. Our search (our own index of 97,434 visits) finds **17/17** (after removing a coarse pre-filter that had missed one week folder; see PLAN.md decision 5). It finds 371 files on all six detectors.

## Check 5 — provenance samples
| Field | Frame | Date shown | Request | What the file header says | Result |
|---|---|---|---|---|---|
| barnard | 2025W34_2B_0030_3 D6 | 2025-08-21T15:25:41Z | HTTP 206 in 1.1s | file says D6, 2025W34_2B_0030_3, DATE-AVG 2025-08-21T15:25:41.407 | MATCH |
| m101 | 2026W22_2A_0431_4 D1 | 2026-05-30T23:15:27Z | HTTP 206 in 2.3s | file says D1, 2026W22_2A_0431_4, DATE-AVG 2026-05-30T23:15:27.977 | MATCH |
| barnard | 2025W35_1A_0484_1 D3 | 2025-08-27T11:35:53Z | HTTP 206 in 1.0s | file says D3, 2025W35_1A_0484_1, DATE-AVG 2025-08-27T11:35:53.582 | MATCH |
| barnard | 2026W34_1A_0431_4 D6 | 2026-08-19T05:04:08Z | HTTP 206 in 1.1s | file says D6, 2026W34_1A_0431_4, DATE-AVG 2026-08-19T05:04:08.847 | MATCH |
| epsindb | 2025W17_4B_0222_4 D5 | 2025-04-26T05:10:41Z | HTTP 206 in 1.1s | file says D5, 2025W17_4B_0222_4, DATE-AVG 2025-04-26T05:10:41.240 | MATCH |
| rdra | 2025W48_2A_0243_2 D2 | 2025-11-28T14:01:12Z | HTTP 206 in 1.0s | file says D2, 2025W48_2A_0243_2, DATE-AVG 2025-11-28T14:01:12.180 | MATCH |
| epsindb | 2026W17_1B_0184_4 D4 | 2026-04-20T22:55:09Z | HTTP 206 in 1.0s | file says D4, 2026W17_1B_0184_4, DATE-AVG 2026-04-20T22:55:09.502 | MATCH |
| rwaur | 2025W37_1A_0366_3 D2 | 2025-09-09T20:12:43Z | HTTP 206 in 1.0s | file says D2, 2025W37_1A_0366_3, DATE-AVG 2025-09-09T20:12:43.653 | MATCH |
| barnard | 2026W11_2A_0513_3 D5 | 2026-03-15T02:28:37Z | HTTP 206 in 1.1s | file says D5, 2026W11_2A_0513_3, DATE-AVG 2026-03-15T02:28:37.707 | MATCH |
| barnard | 2026W34_1A_0308_1 D3 | 2026-08-18T14:17:26Z | HTTP 206 in 1.0s | file says D3, 2026W34_1A_0308_1, DATE-AVG 2026-08-18T14:17:26.464 | MATCH |

## Photometry method floors (used to word the variable-star results)
| Method | Test object | Visit-to-visit scatter (max/min across visits, per band) |
|---|---|---|
| Core aperture r = 2 px, synthetic band photometry | M101 core (control) | 1.02–1.06 |
| Wings, ring 3–6 px (saturated stars) | Barnard's Star (saturated D1–D6) | 1.02–1.17 |
| Outer wings, ring 6–10 px (very saturated) | Barnard's Star | 1.02–1.37 |

Results: RW Aurigae D4/D5/D6 fall by 1.67/1.91/1.83× (Sept 2025 → Sept 2026); D1–D3 change ≤ 1.22×. R Draconis (outer wings): D1 range 2.70×, D3 2.21×, D6 2.12×, varying smoothly month to month. Epsilon Indi B D2/D3 show single-visit jumps of ~30% not seen in D5/D6 (4–6%): treated as artifacts on the site.

## Detailed output of `pipeline/validate.py`

### Barnard's Star (`barnard`)
Frames: 207; visits: 3; releases: ['DR1', 'QR3']; dates 2025-08-15 to 2026-09-22

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 14, 0.07); (2, 13, 0.09); (3, 14, 0.08) |
| D2 | (1, 14, 0.07); (2, 14, 0.09); (3, 13, 0.08) |
| D3 | (1, 15, 0.07); (2, 15, 0.10); (3, 14, 0.08) |
| D4 | (1, 17, 0.06); (2, 16, 0.10); (3, 16, 0.06) |
| D5 | (1, 17, 0.05); (2, 17, 0.11); (3, 17, 0.05) |
| D6 | (1, 17, 0.08); (2, 17, 0.12); (3, 17, 0.08) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-08-28, 2026-03-11, 2026-08-23 | 0.8041, 0.7987, 0.7944 | 0.0097 | 0.0098 | yes |
| c2 D2 | 2025-08-25, 2026-03-15, 2026-08-18 | 1.5536, 1.5536, 1.5476 | 0.0060 | 0.0189 | yes |
| c3 D3 | 2025-08-27, 2026-05-05, 2026-08-17 | 2.2501, 2.2563, 2.2735 | 0.0234 | 0.0280 | yes |
| c4 D4 | 2025-08-28, 2026-03-11, 2026-08-23 | 2.5665, 2.5476, 2.5309 | 0.0356 | 0.0365 | yes |
| c5 D5 | 2025-08-25, 2026-03-15, 2026-08-18 | 4.3328, 4.3331, 4.3269 | 0.0062 | 0.0188 | yes |
| c6 D6 | 2025-08-16, 2026-03-23, 2026-08-16 | 4.4501, 4.4436, 4.4337 | 0.0164 | 0.0180 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D1 | 1 (2025-08-28) | 58.06, 58.49 | 57.82, 58.53 | 0.24 | 1.5 |
| D1 | 2 (2026-03-11) | 57.95, 57.64 | 58.02, 57.48 | 0.17 | 1.1 |
| D1 | 3 (2026-08-23) | 58.18, 56.85 | 58.15, 56.91 | 0.07 | 0.4 |
| D2 | 1 (2025-08-24) | 58.05, 58.53 | 57.61, 58.59 | 0.44 | 2.7 |
| D2 | 2 (2026-03-15) | 57.95, 57.62 | 57.90, 57.52 | 0.11 | 0.7 |
| D2 | 3 (2026-08-18) | 58.18, 56.85 | 57.92, 56.93 | 0.27 | 1.7 |
| D3 | 1 (2025-08-15) | 58.05, 58.54 | 57.97, 58.73 | 0.21 | 1.3 |
| D3 | 2 (2026-03-19) | 57.96, 57.54 | 57.95, 57.27 | 0.27 | 1.7 |
| D3 | 3 (2026-08-17) | 58.17, 56.88 | 58.21, 57.04 | 0.16 | 1.0 |
| D4 | 1 (2025-08-28) | 58.06, 58.49 | 57.86, 58.54 | 0.21 | 1.3 |
| D4 | 2 (2026-03-11) | 57.95, 57.64 | 57.87, 57.61 | 0.09 | 0.5 |
| D4 | 3 (2026-08-23) | 58.18, 56.84 | 58.17, 57.01 | 0.17 | 1.0 |
| D5 | 1 (2025-08-24) | 58.05, 58.53 | 57.88, 58.58 | 0.18 | 1.1 |
| D5 | 2 (2026-03-15) | 57.95, 57.61 | 57.92, 57.55 | 0.07 | 0.4 |
| D5 | 3 (2026-08-18) | 58.18, 56.85 | 58.27, 56.84 | 0.09 | 0.6 |
| D6 | 1 (2025-08-15) | 58.05, 58.55 | 57.99, 58.59 | 0.07 | 0.4 |
| D6 | 2 (2026-03-19) | 57.96, 57.55 | 57.90, 57.50 | 0.08 | 0.5 |
| D6 | 3 (2026-08-17) | 58.17, 56.87 | 58.27, 56.90 | 0.10 | 0.6 |

Predicted total shift first→last visit: 1.67 px (10.2″) between 2025-08-28 and 2026-08-22.

### Epsilon Indi B (brown-dwarf pair) (`epsindb`)
Frames: 179; visits: 4; releases: ['DR1', 'QR3']; dates 2025-04-24 to 2026-10-02

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (2, 5, 0.07); (3, 5, 0.04) |
| D2 | (1, 5, 0.04); (2, 5, 0.05); (3, 5, 0.03); (4, 5, 0.03) |
| D3 | (1, 5, 0.09); (2, 5, 0.05); (3, 5, 0.05); (4, 5, 0.05) |
| D4 | (2, 5, 0.08); (3, 5, 0.08) |
| D5 | (1, 5, 0.24); (2, 5, 0.29); (3, 5, 0.26); (4, 5, 0.22) |
| D6 | (1, 5, 0.22); (2, 5, 0.23); (3, 5, 0.16); (4, 5, 0.27) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-11-11, 2026-04-20 | 0.7946, 0.7920 | 0.0026 | 0.0097 | yes |
| c2 D2 | 2025-04-27, 2025-10-02, 2026-04-25, 2026-10-02 | 1.3051, 1.3063, 1.3050, 1.2914 | 0.0149 | 0.0156 | yes |
| c3 D3 | 2025-04-29, 2025-09-29, 2026-05-04, 2026-09-26 | 1.9790, 1.9970, 1.9787, 1.9782 | 0.0188 | 0.0242 | yes |
| c4 D4 | 2025-04-27, 2026-05-03 | 3.6422, 3.6423 | 0.0001 | 0.0500 | yes |
| c5 D5 | 2025-04-27, 2025-10-06, 2026-04-25, 2026-10-02 | 4.1036, 4.1047, 4.1035, 4.0878 | 0.0169 | 0.0182 | yes |
| c6 D6 | 2025-04-30, 2025-09-29, 2026-04-29, 2026-09-26 | 4.7293, 4.7433, 4.7292, 4.7294 | 0.0141 | 0.0182 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D1 | 2 (2025-10-05) | 88.14, 87.96 | 88.19, 88.03 | 0.09 | 0.5 |
| D1 | 3 (2026-04-20) | 87.74, 88.11 | 87.86, 88.13 | 0.12 | 0.7 |
| D2 | 1 (2025-04-27) | 88.37, 87.72 | 88.30, 87.81 | 0.11 | 0.7 |
| D2 | 2 (2025-10-02) | 88.15, 87.95 | 88.16, 88.01 | 0.06 | 0.4 |
| D2 | 3 (2026-04-25) | 87.73, 88.12 | 87.70, 88.17 | 0.06 | 0.4 |
| D2 | 4 (2026-09-29) | 87.51, 88.34 | 87.59, 88.38 | 0.09 | 0.6 |
| D3 | 1 (2025-04-29) | 88.37, 87.72 | 88.29, 87.80 | 0.11 | 0.7 |
| D3 | 2 (2025-09-29) | 88.15, 87.95 | 88.14, 88.06 | 0.11 | 0.7 |
| D3 | 3 (2026-04-29) | 87.72, 88.12 | 87.68, 88.20 | 0.09 | 0.6 |
| D3 | 4 (2026-09-26) | 87.52, 88.34 | 87.59, 88.41 | 0.10 | 0.6 |
| D4 | 2 (2025-10-05) | 88.14, 87.96 | 88.11, 88.07 | 0.11 | 0.7 |
| D4 | 3 (2026-04-20) | 87.74, 88.11 | 87.69, 88.14 | 0.06 | 0.4 |
| D5 | 1 (2025-04-27) | 88.37, 87.72 | 88.29, 87.78 | 0.10 | 0.6 |
| D5 | 2 (2025-10-02) | 88.15, 87.95 | 88.12, 88.09 | 0.14 | 0.9 |
| D5 | 3 (2026-04-25) | 87.73, 88.12 | 87.66, 88.16 | 0.08 | 0.5 |
| D5 | 4 (2026-09-29) | 87.51, 88.34 | 87.49, 88.51 | 0.17 | 1.1 |
| D6 | 1 (2025-04-29) | 88.37, 87.72 | 88.23, 87.78 | 0.15 | 0.9 |
| D6 | 2 (2025-09-29) | 88.15, 87.95 | 88.02, 88.24 | 0.32 | 2.0 |
| D6 | 3 (2026-04-29) | 87.72, 88.12 | 87.63, 88.23 | 0.14 | 0.9 |
| D6 | 4 (2026-09-26) | 87.52, 88.34 | 87.51, 88.44 | 0.10 | 0.6 |

Predicted total shift first→last visit: 1.05 px (6.4″) between 2025-05-04 and 2026-09-29.

### Pinwheel Galaxy M101 (control) (`m101`)
Frames: 198; visits: 3; releases: ['DR1', 'QR3']; dates 2025-05-09 to 2026-06-19

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 1, 0.06); (2, 0, –); (3, 1, 0.06) |
| D2 | (1, 2, 0.37); (2, 2, 0.38); (3, 2, 0.37) |
| D3 | (1, 2, 0.37); (2, 2, 0.37); (3, 2, 0.38) |
| D4 | (1, 2, 0.41); (2, 2, 0.49); (3, 2, 0.42) |
| D5 | (1, 3, 0.54); (2, 3, 0.57); (3, 2, 0.55) |
| D6 | (1, 3, 0.50); (2, 3, 0.50); (3, 3, 0.49) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-05-24, 2025-12-01, 2026-05-23 | 0.8211, 0.8292, 0.8313 | 0.0102 | 0.0103 | yes |
| c2 D2 | 2025-05-10, 2025-12-07, 2026-05-22 | 1.5429, 1.5385, 1.5567 | 0.0182 | 0.0188 | yes |
| c3 D3 | 2025-05-27, 2025-12-13, 2026-06-18 | 2.0988, 2.1172, 2.1187 | 0.0199 | 0.0262 | yes |
| c4 D4 | 2025-05-24, 2025-12-02, 2026-05-23 | 2.7732, 2.7912, 2.8125 | 0.0393 | 0.0394 | yes |
| c5 D5 | 2025-05-10, 2025-12-07, 2026-05-22 | 4.2858, 4.2815, 4.2993 | 0.0178 | 0.0186 | yes |
| c6 D6 | 2025-05-27, 2025-12-13, 2026-06-18 | 4.7837, 4.7967, 4.7979 | 0.0142 | 0.0183 | yes |

**Check 4 — control field** (fraction of difference-image pixels at the ±saturation of the symmetric display stretch, per band; the stretch is set at the 99.5th percentile so ~0.5% is expected from noise alone)

- D1: 1→2: 0.55%, 2→3: 0.42%, 1→3: 0.55%
- D2: 1→2: 0.53%, 2→3: 0.50%, 1→3: 0.50%
- D3: 1→2: 0.28%, 2→3: 0.53%, 1→3: 0.69%
- D4: 1→2: 0.39%, 2→3: 0.65%, 1→3: 0.49%
- D5: 1→2: 0.35%, 2→3: 0.67%, 1→3: 0.53%
- D6: 1→2: 0.07%, 2→3: 0.73%, 1→3: 0.72%

### R Draconis (Mira variable) (`rdra`)
Frames: 190; visits: 17; releases: ['DR1', 'QR3']; dates 2025-04-25 to 2026-09-24

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (3, 7, 0.04); (4, 7, 0.05); (5, 7, 0.05); (6, 7, 0.03); (14, 7, 0.04); (15, 7, 0.07); (16, 7, 0.06) |
| D2 | (2, 7, 0.06); (7, 7, 0.06); (14, 7, 0.04) |
| D3 | (2, 7, 0.11); (8, 7, 0.11); (10, 7, 0.09); (11, 7, 0.04); (12, 7, 0.05) |
| D4 | (3, 7, 0.13); (4, 7, 0.07); (5, 7, 0.08); (6, 7, 0.10); (14, 7, 0.17); (15, 7, 0.08); (16, 7, 0.07) |
| D5 | (2, 7, 0.10); (14, 7, 0.07) |
| D6 | (1, 7, 0.08); (2, 6, 0.18); (8, 7, 0.08); (10, 7, 0.17); (11, 7, 0.19); (12, 7, 0.10); (13, 7, 0.06) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-06-06, 2025-07-18, 2025-08-29, 2025-10-19, 2025-10-30, 2026-07-11, 2026-08-03, 2026-09-05 | 0.9436, 0.9406, 0.9512, 0.9416, 0.9492, 0.9412, 0.9502, 0.9499 | 0.0106 | 0.0119 | yes |
| c2 D2 | 2025-06-08, 2025-11-18, 2026-06-22 | 1.4047, 1.4096, 1.4204 | 0.0157 | 0.0169 | yes |
| c3 D3 | 2025-04-25, 2025-06-12, 2025-12-30, 2026-03-10, 2026-03-25, 2026-04-22, 2026-06-12 | 1.9527, 1.9490, 1.9388, 1.9434, 1.9464, 1.9415, 1.9553 | 0.0165 | 0.0236 | yes |
| c4 D4 | 2025-06-06, 2025-07-07, 2025-09-08, 2025-10-19, 2025-10-30, 2026-07-14, 2026-08-05, 2026-09-17 | 3.2557, 3.2436, 3.2546, 3.2482, 3.2782, 3.2460, 3.2537, 3.2374 | 0.0408 | 0.0466 | yes |
| c5 D5 | 2025-06-08, 2025-11-18, 2025-12-03 | 4.1797, 4.1851, 4.1767 | 0.0084 | 0.0184 | yes |
| c6 D6 | 2025-05-04, 2025-06-12, 2026-01-13, 2026-03-09, 2026-03-25, 2026-05-06, 2026-06-08 | 4.4393, 4.4418, 4.4506, 4.4387, 4.4414, 4.4376, 4.4466 | 0.0130 | 0.0179 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D1 | 3 (2025-07-04) | [58.0, 58.0] | not measured | – | – |
| D1 | 4 (2025-08-29) | 58.00, 58.00 | 57.77, 58.02 | 0.23 | 1.4 |
| D1 | 5 (2025-09-24) | 58.00, 58.00 | 57.95, 57.95 | 0.07 | 0.4 |
| D1 | 6 (2025-10-25) | 58.00, 58.00 | 58.01, 58.00 | 0.01 | 0.1 |
| D1 | 14 (2026-07-06) | 58.00, 58.00 | 58.03, 57.99 | 0.03 | 0.2 |
| D1 | 15 (2026-08-03) | [58.0, 58.0] | not measured | – | – |
| D1 | 16 (2026-08-25) | [58.0, 58.0] | not measured | – | – |
| D2 | 2 (2025-06-08) | [58.0, 58.0] | not measured | – | – |
| D2 | 7 (2025-12-01) | [58.0, 58.0] | not measured | – | – |
| D2 | 14 (2026-06-21) | [58.0, 58.0] | not measured | – | – |
| D3 | 2 (2025-06-02) | [58.0, 58.0] | not measured | – | – |
| D3 | 8 (2025-12-26) | [58.0, 58.0] | not measured | – | – |
| D3 | 10 (2026-02-20) | [58.0, 58.0] | not measured | – | – |
| D3 | 11 (2026-03-25) | [58.0, 58.0] | not measured | – | – |
| D3 | 12 (2026-04-22) | [58.0, 58.0] | not measured | – | – |
| D4 | 3 (2025-07-07) | [58.0, 58.0] | not measured | – | – |
| D4 | 4 (2025-09-08) | [58.0, 58.0] | not measured | – | – |
| D4 | 5 (2025-10-18) | [58.0, 58.0] | not measured | – | – |
| D4 | 6 (2025-10-30) | [58.0, 58.0] | not measured | – | – |
| D4 | 14 (2026-07-06) | [58.0, 58.0] | not measured | – | – |
| D4 | 15 (2026-08-05) | [58.0, 58.0] | not measured | – | – |
| D4 | 16 (2026-09-04) | [58.0, 58.0] | not measured | – | – |
| D5 | 2 (2025-06-08) | [58.0, 58.0] | not measured | – | – |
| D5 | 14 (2026-06-21) | 58.00, 58.00 | 58.10, 58.05 | 0.11 | 0.7 |
| D6 | 1 (2025-04-25) | [58.0, 58.0] | not measured | – | – |
| D6 | 2 (2025-06-12) | [58.0, 58.0] | not measured | – | – |
| D6 | 8 (2025-12-26) | [58.0, 58.0] | not measured | – | – |
| D6 | 10 (2026-03-08) | [58.0, 58.0] | not measured | – | – |
| D6 | 11 (2026-04-01) | [58.0, 58.0] | not measured | – | – |
| D6 | 12 (2026-05-03) | 58.00, 58.00 | 58.06, 57.96 | 0.07 | 0.4 |
| D6 | 13 (2026-05-23) | 58.00, 58.00 | 58.15, 58.00 | 0.15 | 0.9 |

Predicted total shift first→last visit: 0.00 px (0.0″) between 2025-04-29 and 2026-09-24.

### RW Aurigae (young variable star) (`rwaur`)
Frames: 205; visits: 3; releases: ['DR1', 'QR3']; dates 2025-09-01 to 2026-09-16

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 10, 0.15); (2, 8, 0.19); (3, 10, 0.17) |
| D2 | (1, 11, 0.18); (2, 10, 0.19); (3, 9, 0.19) |
| D3 | (1, 11, 0.20); (2, 12, 0.20); (3, 11, 0.19) |
| D4 | (1, 14, 0.17); (2, 13, 0.20); (3, 14, 0.18) |
| D5 | (1, 15, 0.16); (2, 15, 0.18); (3, 16, 0.17) |
| D6 | (1, 16, 0.12); (2, 16, 0.14); (3, 16, 0.19) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-09-03, 2026-03-04, 2026-09-09 | 0.8790, 0.8788, 0.8872 | 0.0084 | 0.0109 | yes |
| c2 D2 | 2025-09-09, 2026-03-01, 2026-09-14 | 1.3025, 1.2992, 1.2907 | 0.0118 | 0.0155 | yes |
| c3 D3 | 2025-09-18, 2026-02-20, 2026-09-16 | 1.9921, 1.9809, 1.9732 | 0.0189 | 0.0240 | yes |
| c4 D4 | 2025-09-03, 2026-03-04, 2026-09-09 | 2.9207, 2.9190, 2.9523 | 0.0333 | 0.0425 | yes |
| c5 D5 | 2025-09-10, 2026-03-02, 2026-09-15 | 4.2071, 4.2037, 4.1931 | 0.0140 | 0.0184 | yes |
| c6 D6 | 2025-09-17, 2026-02-27, 2026-09-14 | 4.5045, 4.4870, 4.4915 | 0.0175 | 0.0179 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D1 | 1 (2025-09-02) | 58.00, 58.00 | 57.91, 57.96 | 0.10 | 0.6 |
| D1 | 2 (2026-03-04) | 58.00, 58.00 | 58.06, 58.04 | 0.07 | 0.4 |
| D1 | 3 (2026-09-02) | 58.00, 58.00 | 57.84, 57.93 | 0.17 | 1.1 |
| D2 | 1 (2025-09-08) | 58.00, 58.00 | 57.90, 57.99 | 0.10 | 0.6 |
| D2 | 2 (2026-03-01) | 58.00, 58.00 | 57.93, 58.01 | 0.07 | 0.4 |
| D2 | 3 (2026-09-10) | 58.00, 58.00 | 57.75, 57.91 | 0.27 | 1.6 |
| D3 | 1 (2025-09-17) | 58.00, 58.00 | 57.96, 57.94 | 0.07 | 0.4 |
| D3 | 2 (2026-02-20) | 58.00, 58.00 | 57.91, 57.90 | 0.13 | 0.8 |
| D3 | 3 (2026-09-13) | 58.00, 58.00 | 57.67, 57.91 | 0.34 | 2.1 |
| D4 | 1 (2025-09-01) | 58.00, 58.00 | 57.94, 57.95 | 0.08 | 0.5 |
| D4 | 2 (2026-03-04) | 58.00, 58.00 | 57.66, 57.91 | 0.35 | 2.2 |
| D4 | 3 (2026-09-02) | 58.00, 58.00 | 57.87, 57.96 | 0.14 | 0.8 |
| D5 | 1 (2025-09-08) | 58.00, 58.00 | 57.77, 57.76 | 0.33 | 2.0 |
| D5 | 2 (2026-03-01) | 58.00, 58.00 | 57.81, 58.02 | 0.19 | 1.2 |
| D5 | 3 (2026-09-10) | 58.00, 58.00 | 57.69, 57.90 | 0.33 | 2.0 |
| D6 | 1 (2025-09-17) | 58.00, 58.00 | 57.77, 57.93 | 0.24 | 1.5 |
| D6 | 2 (2026-02-20) | 58.00, 58.00 | 57.90, 57.87 | 0.16 | 1.0 |
| D6 | 3 (2026-09-13) | 58.00, 58.00 | 57.54, 57.96 | 0.46 | 2.8 |

Predicted total shift first→last visit: 0.00 px (0.0″) between 2025-09-10 and 2026-09-11.

### WISE 0855−0714 (coldest known brown dwarf) (`wise0855`)
Frames: 149; visits: 3; releases: ['DR1']; dates 2025-05-05 to 2026-05-14

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (2, 1, 0.10); (3, 1, 0.14) |
| D2 | (1, 1, 0.16); (2, 1, 0.13); (3, 1, 0.20) |
| D3 | (2, 1, 0.22); (3, 1, 0.23) |
| D4 | (2, 1, 0.20); (3, 1, 0.24) |
| D5 | (1, 2, 0.16); (2, 2, 0.27); (3, 2, 0.11) |
| D6 | (2, 1, 0.05); (3, 1, 0.15) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-11-03, 2026-05-02 | 0.7666, 0.7613 | 0.0053 | 0.0092 | yes |
| c2 D2 | 2025-05-06, 2025-11-07, 2026-05-13 | 1.5152, 1.5176, 1.5151 | 0.0025 | 0.0185 | yes |
| c3 D3 | 2025-05-05, 2025-11-14, 2026-05-11 | 2.3634, 2.3854, 2.3632 | 0.0222 | 0.0293 | yes |
| c4 D4 | 2025-05-06, 2025-10-31 | 3.6382, 3.6324 | 0.0058 | 0.0495 | yes |
| c5 D5 | 2025-05-06, 2025-11-07, 2026-05-13 | 4.2950, 4.2972, 4.2950 | 0.0022 | 0.0186 | yes |
| c6 D6 | 2025-11-10, 2026-04-23 | 4.6337, 4.6511 | 0.0174 | 0.0181 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D1 | 2 (2025-10-31) | 57.75, 58.00 | 58.88, 57.41 | 1.27 | 7.8 |
| D1 | 3 (2026-05-03) | 58.56, 57.91 | 58.94, 57.32 | 0.70 | 4.3 |
| D2 | 1 (2025-05-06) | 57.23, 58.02 | 58.91, 57.33 | 1.82 | 11.2 |
| D2 | 2 (2025-11-07) | 57.79, 58.00 | 58.89, 57.38 | 1.26 | 7.8 |
| D2 | 3 (2026-05-03) | 58.58, 57.90 | 59.16, 57.24 | 0.88 | 5.4 |
| D3 | 2 (2025-11-10) | 57.79, 58.00 | 58.82, 57.42 | 1.18 | 7.3 |
| D3 | 3 (2026-04-22) | 58.53, 57.91 | 59.25, 57.21 | 1.00 | 6.2 |
| D4 | 2 (2025-10-31) | 57.75, 58.00 | 58.76, 57.45 | 1.15 | 7.1 |
| D4 | 3 (2026-05-03) | 58.56, 57.91 | 59.35, 57.26 | 1.02 | 6.3 |
| D5 | 1 (2025-05-06) | 57.23, 58.02 | 57.58, 57.65 | 0.51 | 3.1 |
| D5 | 2 (2025-11-07) | 57.81, 58.00 | 58.18, 57.78 | 0.43 | 2.6 |
| D5 | 3 (2026-05-03) | 58.58, 57.90 | 58.86, 57.64 | 0.38 | 2.3 |
| D6 | 2 (2025-11-10) | 57.79, 58.00 | 57.91, 57.96 | 0.13 | 0.8 |
| D6 | 3 (2026-04-22) | 58.53, 57.91 | 58.82, 57.63 | 0.40 | 2.5 |

Predicted total shift first→last visit: 1.32 px (8.1″) between 2025-05-06 and 2026-05-03.

