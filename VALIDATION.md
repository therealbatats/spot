# VALIDATION — SPOT (Sky Patches Over Time)

Version 1.0.0 · November (11) 15, 2026 · Every number below was produced by a command run that day. A check that was not run is marked "not run".

Scripts: `pipeline/validate.py` (checks 1–3), `pipeline/check_diff.py` (check 4), `pipeline/check_provenance.py` (check 5). Written with AI assistance under the direction of Ali (team AITHMAC).

## Summary

| # | Check | Result |
|---|---|---|
| 1 | Alignment | **Pass.** Median distance between measured centroids and Gaia DR3 positions (moved to each date) of isolated G = 9–14 stars, per band and visit: Barnard's Star 0.05–0.13 px (13–17 stars per image), Epsilon Indi B 0.04–0.24, R Draconis 0.03–0.35, RW Aurigae 0.12–0.25, Pluto 0.11–0.56 (4–7 stars, single days), WISE 0855 0.10–0.26 (1–2 stars). M101: 0.03–0.72 px from only 1–3 stars sitting on galaxy light. 1 px = 6.15″. |
| 2 | Wavelength matching | **Pass.** 42/42 exact-wavelength channels (6 per field): every pair of frames differs by less than half the narrowest bandwidth. Band views use only the wavelength range every visit covered (except Pluto's by-day view, which is labelled "positions only"). |
| 3 | Known movers | **Pass.** Barnard's Star: 0.01–0.43 px from the Gaia prediction in all 18 band-visits; WISE (2010) → SPHEREx (2026) shift measured 27.1 px vs 27.3 predicted; WISE-epoch residual 0.14 px. Epsilon Indi B: 0.01–0.32 px in 20 band-visits. WISE 0855: SPHEREx 0.29–1.96 px in 14 band-visits (faint; neighbour star 7.8″ away); 2010 → 2026 shift measured 20.7 px vs 20.9 predicted; WISE-epoch residual 1.12 px. **Pluto (solar system):** 0.07–1.05 px from the JPL Horizons ephemeris in 28 band-days and 0.17–0.57 px in the 8 daily all-band images; it moves about 12 px in 8 days. |
| 4 | Control field (new test) | **Pass.** Significance map S = (B − A) / √(σ² + (f·max(A,B))²), f = 0.12 measured as the median residual of 1,555 isolated non-changing Gaia stars in all fields (84th percentile 0.205). M101: **2 regions with |S| ≥ 5 in 18 differences**, none at the centre. Other fields: the targets appear at their positions; isolated spots elsewhere are mostly single-visit artifacts (satellite trails, reflections of bright stars, residual cosmic rays), stated on the site. |
| 5 | Provenance | **Pass.** 15 random frames (three samples of 5): the IRSA source link opened (HTTP 206) and the file's DETECTOR, OBSID and DATE-AVG match the site. 15/15 MATCH. The WISE source link for Barnard's Star also opens (HTTP 206). |
| 6 | Simulation labelling | SEE_CHECK6 |
| 7 | Live site | SEE_CHECK7 |
| 8 | Size and speed | Initial page including the hero's real data and fonts ≈ 414 KB, plus 7 thumbnails 56 KB (uncompressed; limit 2 MB). Opening a field: field.json 130–260 KB plus 2–3 PNGs (10–25 KB). Live mode: visit index 4.5 MB raw / 1.6 MB gzip, loaded only on first live request; Orion Nebula (D2, 0.1°) built in about 6 s on the public site with 180/180 requests OK. |
| 9 | Links | All visitor-facing links returned 200/206 when checked: DOIs, IRSA pages and tutorials, AWS buckets, MAST, challenge page, repository. Expected non-OK: IRSA TAP and image search (HTTP 502 all afternoon), CDS services ("page unavailable"), two Canadian Space Agency pages (time-out, only in a private notes file). |
| 10 | Text truth | SEE_CHECK10 |

## Photometry floors (what counts as a real brightness change)
| Method | Test object | Scatter |
|---|---|---|
| Core aperture, per frame, relative to the star's own median at that wavelength | M101 core (control) | 4.3% rms per frame; band averages 1–6% between visits |
| Outer glow (saturated stars), per frame | Barnard's Star | 10.2% rms per frame |

Results: R Draconis per-frame brightness runs 0.46× to 1.98× its median (5th–95th percentile). A fit with the period fixed at 246.12 d (AAVSO VSX) and one shared phase reduces the scatter from 0.187 to 0.116 dex, and the fitted maximum lands 10 days from the maximum predicted by the AAVSO ephemeris (JD 2457370 + n·P). RW Aurigae: 2.4–5 µm brightness fell 1.7–1.9× from Sept 2025 to Sept 2026 (band averages); per-frame 5th–95th percentile 0.64×–1.47×.

## Independent check of the file search
IRSA's own cutouts tutorial lists 17 detector-2 files for its M101 example position; our index finds 17/17 (371 files on all detectors).

## Check 4 — regions with |S| ≥ 5 per field
```
m101: regions |S|>=5 away from the target = 2; at the target = 0
barnard: regions |S|>=5 away from the target = 97; at the target = 41
rwaur: regions |S|>=5 away from the target = 164; at the target = 28
epsindb: regions |S|>=5 away from the target = 410; at the target = 42
wise0855: regions |S|>=5 away from the target = 203; at the target = 3
rdra: regions |S|>=5 away from the target = 725; at the target = 79
```

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
| epsindb | 2026W18_1A_0475_2 D6 | 2026-04-29T07:13:34Z | HTTP 206 in 1.2s | file says D6, 2026W18_1A_0475_2, DATE-AVG 2026-04-29T07:13:34.821 | MATCH |
| rwaur | 2025W36_1A_0606_1 D1 | 2025-09-03T17:23:21Z | HTTP 206 in 2.8s | file says D1, 2025W36_1A_0606_1, DATE-AVG 2025-09-03T17:23:21.055 | MATCH |
| m101 | 2026W24_2B_0446_2 D6 | 2026-06-13T22:52:34Z | HTTP 206 in 2.0s | file says D6, 2026W24_2B_0446_2, DATE-AVG 2026-06-13T22:52:34.160 | MATCH |
| rwaur | 2026W11_1A_0285_3 D4 | 2026-03-10T10:38:00Z | HTTP 206 in 1.3s | file says D4, 2026W11_1A_0285_3, DATE-AVG 2026-03-10T10:38:00.616 | MATCH |
| m101 | 2025W22_1B_0283_4 D3 | 2025-05-27T15:14:23Z | HTTP 206 in 1.2s | file says D3, 2025W22_1B_0283_4, DATE-AVG 2025-05-27T15:14:23.124 | MATCH |

## Detailed output of `pipeline/validate.py`

### Barnard's Star (`barnard`)
Frames: 207; visits: 3; releases: ['DR1', 'QR3']; dates 2025-08-15 to 2026-09-22

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 14, 0.08); (2, 13, 0.09); (3, 14, 0.08) |
| D2 | (1, 14, 0.07); (2, 13, 0.10); (3, 13, 0.08) |
| D3 | (1, 16, 0.07); (2, 15, 0.10); (3, 14, 0.08) |
| D4 | (1, 17, 0.06); (2, 17, 0.12); (3, 16, 0.06) |
| D5 | (1, 17, 0.05); (2, 17, 0.12); (3, 17, 0.06) |
| D6 | (1, 17, 0.08); (2, 17, 0.13); (3, 17, 0.08) |

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
| D1 | 1 (2025-08-28) | 58.06, 58.49 | 57.83, 58.56 | 0.24 | 1.5 |
| D1 | 2 (2026-03-11) | 57.95, 57.64 | 58.00, 57.40 | 0.25 | 1.5 |
| D1 | 3 (2026-08-23) | 58.18, 56.85 | 58.19, 56.84 | 0.01 | 0.1 |
| D2 | 1 (2025-08-24) | 58.05, 58.53 | 57.62, 58.57 | 0.43 | 2.7 |
| D2 | 2 (2026-03-15) | 57.95, 57.62 | 57.93, 57.51 | 0.11 | 0.7 |
| D2 | 3 (2026-08-18) | 58.18, 56.85 | 57.98, 56.89 | 0.20 | 1.3 |
| D3 | 1 (2025-08-15) | 58.05, 58.54 | 58.15, 58.70 | 0.19 | 1.2 |
| D3 | 2 (2026-03-19) | 57.96, 57.54 | 57.84, 57.16 | 0.40 | 2.5 |
| D3 | 3 (2026-08-17) | 58.17, 56.88 | 58.33, 57.07 | 0.25 | 1.5 |
| D4 | 1 (2025-08-28) | 58.06, 58.49 | 57.83, 58.48 | 0.23 | 1.4 |
| D4 | 2 (2026-03-11) | 57.95, 57.64 | 57.86, 57.61 | 0.09 | 0.6 |
| D4 | 3 (2026-08-23) | 58.18, 56.84 | 58.22, 57.02 | 0.18 | 1.1 |
| D5 | 1 (2025-08-24) | 58.05, 58.53 | 57.80, 58.59 | 0.26 | 1.6 |
| D5 | 2 (2026-03-15) | 57.95, 57.61 | 57.94, 57.57 | 0.04 | 0.3 |
| D5 | 3 (2026-08-18) | 58.18, 56.85 | 58.30, 56.82 | 0.12 | 0.8 |
| D6 | 1 (2025-08-15) | 58.05, 58.55 | 57.98, 58.56 | 0.07 | 0.4 |
| D6 | 2 (2026-03-19) | 57.96, 57.55 | 57.88, 57.49 | 0.10 | 0.6 |
| D6 | 3 (2026-08-17) | 58.17, 56.87 | 58.24, 56.94 | 0.10 | 0.6 |

Predicted total shift first→last visit: 1.67 px (10.2″) between 2025-08-28 and 2026-08-22.

### Epsilon Indi B (brown-dwarf pair) (`epsindb`)
Frames: 179; visits: 4; releases: ['DR1', 'QR3']; dates 2025-04-24 to 2026-10-02

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (2, 5, 0.06); (3, 5, 0.04) |
| D2 | (1, 5, 0.07); (2, 5, 0.07); (3, 5, 0.04); (4, 5, 0.06) |
| D3 | (1, 5, 0.08); (2, 5, 0.11); (3, 5, 0.06); (4, 5, 0.07) |
| D4 | (2, 5, 0.09); (3, 5, 0.11) |
| D5 | (1, 5, 0.18); (2, 5, 0.07); (3, 5, 0.14); (4, 5, 0.19) |
| D6 | (1, 5, 0.16); (2, 5, 0.24); (3, 5, 0.09); (4, 5, 0.19) |

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
| D1 | 2 (2025-10-05) | 88.14, 87.96 | 88.17, 88.08 | 0.12 | 0.8 |
| D1 | 3 (2026-04-20) | 87.74, 88.11 | 87.79, 88.13 | 0.05 | 0.3 |
| D2 | 1 (2025-04-27) | 88.37, 87.72 | 88.27, 87.89 | 0.20 | 1.2 |
| D2 | 2 (2025-10-02) | 88.15, 87.95 | 88.14, 87.96 | 0.01 | 0.1 |
| D2 | 3 (2026-04-25) | 87.73, 88.12 | 87.92, 88.05 | 0.20 | 1.2 |
| D2 | 4 (2026-09-29) | 87.51, 88.34 | 87.66, 88.34 | 0.15 | 0.9 |
| D3 | 1 (2025-04-29) | 88.37, 87.72 | 88.05, 87.75 | 0.32 | 2.0 |
| D3 | 2 (2025-09-29) | 88.15, 87.95 | 88.16, 88.05 | 0.10 | 0.6 |
| D3 | 3 (2026-04-29) | 87.72, 88.12 | 87.73, 88.17 | 0.05 | 0.3 |
| D3 | 4 (2026-09-26) | 87.52, 88.34 | 87.65, 88.32 | 0.13 | 0.8 |
| D4 | 2 (2025-10-05) | 88.14, 87.96 | 88.10, 88.05 | 0.10 | 0.6 |
| D4 | 3 (2026-04-20) | 87.74, 88.11 | 87.68, 88.14 | 0.07 | 0.4 |
| D5 | 1 (2025-04-27) | 88.37, 87.72 | 88.29, 87.78 | 0.10 | 0.6 |
| D5 | 2 (2025-10-02) | 88.15, 87.95 | 88.13, 88.09 | 0.14 | 0.9 |
| D5 | 3 (2026-04-25) | 87.73, 88.12 | 87.65, 88.16 | 0.09 | 0.6 |
| D5 | 4 (2026-09-29) | 87.51, 88.34 | 87.48, 88.54 | 0.20 | 1.2 |
| D6 | 1 (2025-04-29) | 88.37, 87.72 | 88.26, 87.77 | 0.12 | 0.7 |
| D6 | 2 (2025-09-29) | 88.15, 87.95 | 88.05, 88.23 | 0.30 | 1.8 |
| D6 | 3 (2026-04-29) | 87.72, 88.12 | 87.62, 88.23 | 0.15 | 0.9 |
| D6 | 4 (2026-09-26) | 87.52, 88.34 | 87.51, 88.44 | 0.10 | 0.6 |

Predicted total shift first→last visit: 1.05 px (6.4″) between 2025-05-04 and 2026-09-29.

### Pinwheel Galaxy M101 (control) (`m101`)
Frames: 198; visits: 3; releases: ['DR1', 'QR3']; dates 2025-05-09 to 2026-06-19

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 1, 0.06); (2, 1, 0.03); (3, 0, –) |
| D2 | (1, 2, 0.37); (2, 2, 0.38); (3, 2, 0.37) |
| D3 | (1, 2, 0.39); (2, 2, 0.38); (3, 1, 0.03) |
| D4 | (1, 2, 0.43); (2, 2, 0.49); (3, 2, 0.43) |
| D5 | (1, 3, 0.54); (2, 3, 0.57); (3, 2, 0.55) |
| D6 | (1, 3, 0.51); (2, 2, 0.72); (3, 3, 0.49) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-05-24, 2025-12-01, 2026-05-23 | 0.8211, 0.8292, 0.8313 | 0.0102 | 0.0103 | yes |
| c2 D2 | 2025-05-10, 2025-12-07, 2026-05-22 | 1.5429, 1.5385, 1.5567 | 0.0182 | 0.0188 | yes |
| c3 D3 | 2025-05-27, 2025-12-13, 2026-06-18 | 2.0988, 2.1172, 2.1187 | 0.0199 | 0.0262 | yes |
| c4 D4 | 2025-05-24, 2025-12-02, 2026-05-23 | 2.7732, 2.7912, 2.8125 | 0.0393 | 0.0394 | yes |
| c5 D5 | 2025-05-10, 2025-12-07, 2026-05-22 | 4.2858, 4.2815, 4.2993 | 0.0178 | 0.0186 | yes |
| c6 D6 | 2025-05-27, 2025-12-13, 2026-06-18 | 4.7837, 4.7967, 4.7979 | 0.0142 | 0.0183 | yes |


### Pluto — the first Planet X (`pluto`)
Frames: 75; visits: 8; releases: ['DR1']; dates 2025-10-04 to 2025-10-12

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D0 | (1, 6, 0.27); (2, 6, 0.25); (3, 6, 0.25); (4, 6, 0.23); (5, 6, 0.26); (6, 7, 0.11); (7, 6, 0.24); (8, 6, 0.24) |
| D1 | (3, 4, 0.27); (4, 5, 0.42); (5, 4, 0.28); (7, 5, 0.42); (8, 4, 0.29) |
| D2 | (1, 5, 0.37); (3, 5, 0.46); (5, 5, 0.39); (6, 5, 0.56) |
| D3 | (1, 6, 0.26); (2, 6, 0.19); (3, 6, 0.25); (4, 6, 0.17) |
| D4 | (3, 6, 0.23); (4, 6, 0.26); (5, 7, 0.12); (7, 7, 0.12); (8, 7, 0.13) |
| D5 | (1, 6, 0.27); (3, 6, 0.27); (5, 6, 0.30); (6, 7, 0.16) |
| D6 | (1, 6, 0.28); (2, 6, 0.28); (3, 6, 0.26); (4, 6, 0.33) |

**Check 2 — wavelength matching** (exact-wavelength channels)

| Channel | Dates | λ per frame (µm) | max pairwise Δλ (µm) | half bandwidth (µm) | Δλ < half bandwidth |
|---|---|---|---|---|---|
| c1 D1 | 2025-10-06, 2025-10-12 | 1.0541, 1.0464 | 0.0077 | 0.0140 | yes |
| c2 D2 | 2025-10-04, 2025-10-10 | 1.5600, 1.5480 | 0.0120 | 0.0188 | yes |
| c3 D3 | 2025-10-05, 2025-10-07 | 2.3223, 2.3056 | 0.0167 | 0.0288 | yes |
| c4 D4 | 2025-10-06, 2025-10-12 | 3.5911, 3.5621 | 0.0290 | 0.0495 | yes |
| c5 D5 | 2025-10-04, 2025-10-10 | 4.3393, 4.3274 | 0.0119 | 0.0187 | yes |
| c6 D6 | 2025-10-05, 2025-10-07 | 4.9392, 4.9278 | 0.0114 | 0.0188 | yes |

**Check 3 — target position, measured vs predicted** (band coadds; pixels, canvas coords)

| Detector | Visit | Predicted (x,y) | Measured (x,y) | Residual px | Residual ″ |
|---|---|---|---|---|---|
| D0 | 1 (2025-10-04) | 49.21, 56.94 | 49.46, 56.60 | 0.42 | 2.6 |
| D0 | 2 (2025-10-05) | 51.75, 57.31 | 51.87, 56.92 | 0.41 | 2.5 |
| D0 | 3 (2025-10-06) | 53.73, 57.57 | 53.49, 57.86 | 0.38 | 2.3 |
| D0 | 4 (2025-10-07) | 56.12, 57.85 | 56.24, 58.09 | 0.27 | 1.7 |
| D0 | 5 (2025-10-08) | 57.95, 58.00 | 58.50, 58.15 | 0.57 | 3.5 |
| D0 | 6 (2025-10-10) | 60.22, 58.06 | 60.09, 58.21 | 0.20 | 1.2 |
| D0 | 7 (2025-10-11) | 60.73, 58.05 | 60.57, 58.10 | 0.17 | 1.0 |
| D0 | 8 (2025-10-12) | 61.57, 57.93 | 61.25, 57.96 | 0.32 | 2.0 |
| D1 | 3 (2025-10-06) | 53.98, 57.60 | 53.83, 57.85 | 0.29 | 1.8 |
| D1 | 4 (2025-10-07) | 56.33, 57.87 | 56.26, 57.87 | 0.07 | 0.4 |
| D1 | 5 (2025-10-09) | 58.40, 58.03 | 58.60, 58.04 | 0.20 | 1.2 |
| D1 | 7 (2025-10-11) | 60.73, 58.05 | 60.62, 58.07 | 0.11 | 0.7 |
| D1 | 8 (2025-10-12) | 61.57, 57.93 | 61.36, 57.94 | 0.21 | 1.3 |
| D2 | 1 (2025-10-04) | 49.71, 57.01 | 50.19, 56.81 | 0.52 | 3.2 |
| D2 | 3 (2025-10-06) | 54.12, 57.62 | 53.64, 57.92 | 0.57 | 3.5 |
| D2 | 5 (2025-10-08) | 57.56, 57.97 | 58.17, 58.09 | 0.62 | 3.8 |
| D2 | 6 (2025-10-10) | 60.22, 58.06 | 60.11, 58.10 | 0.12 | 0.7 |
| D3 | 1 (2025-10-04) | 48.20, 56.79 | 48.23, 56.10 | 0.69 | 4.2 |
| D3 | 2 (2025-10-05) | 51.75, 57.31 | 51.57, 57.01 | 0.35 | 2.2 |
| D3 | 3 (2025-10-06) | 53.14, 57.50 | 52.90, 57.32 | 0.30 | 1.8 |
| D3 | 4 (2025-10-07) | 55.71, 57.80 | 56.29, 58.45 | 0.87 | 5.4 |
| D4 | 3 (2025-10-06) | 53.84, 57.59 | 53.16, 57.96 | 0.77 | 4.8 |
| D4 | 4 (2025-10-07) | 56.33, 57.87 | 56.54, 58.08 | 0.30 | 1.8 |
| D4 | 5 (2025-10-09) | 58.40, 58.03 | 58.98, 58.19 | 0.60 | 3.7 |
| D4 | 7 (2025-10-11) | 60.73, 58.05 | 60.26, 58.22 | 0.50 | 3.1 |
| D4 | 8 (2025-10-12) | 61.57, 57.93 | 60.58, 58.07 | 1.00 | 6.1 |
| D5 | 1 (2025-10-04) | 49.71, 57.01 | 49.97, 56.28 | 0.77 | 4.8 |
| D5 | 3 (2025-10-06) | 54.12, 57.62 | 53.87, 58.35 | 0.77 | 4.7 |
| D5 | 5 (2025-10-08) | 57.56, 57.97 | 58.51, 58.42 | 1.05 | 6.5 |
| D5 | 6 (2025-10-10) | 60.22, 58.06 | 60.07, 58.48 | 0.45 | 2.7 |
| D6 | 1 (2025-10-04) | 48.20, 56.79 | 47.96, 56.77 | 0.24 | 1.5 |
| D6 | 2 (2025-10-05) | 51.75, 57.31 | 52.04, 56.85 | 0.54 | 3.3 |
| D6 | 3 (2025-10-06) | 53.14, 57.50 | 52.62, 56.84 | 0.84 | 5.2 |
| D6 | 4 (2025-10-07) | 55.71, 57.80 | 56.03, 58.75 | 1.00 | 6.2 |

Predicted total shift first→last visit: 12.40 px (76.3″) between 2025-10-04 and 2025-10-12.

### R Draconis (Mira variable) (`rdra`)
Frames: 190; visits: 17; releases: ['DR1', 'QR3']; dates 2025-04-25 to 2026-09-24

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (3, 7, 0.10); (4, 7, 0.09); (5, 7, 0.06); (6, 7, 0.03); (14, 7, 0.04); (15, 7, 0.05); (16, 7, 0.09) |
| D2 | (2, 7, 0.09); (7, 7, 0.09); (14, 7, 0.07) |
| D3 | (2, 7, 0.12); (8, 7, 0.12); (10, 7, 0.11); (11, 7, 0.08); (12, 7, 0.08) |
| D4 | (3, 7, 0.08); (4, 7, 0.07); (5, 7, 0.06); (6, 7, 0.04); (14, 7, 0.07); (15, 7, 0.09); (16, 7, 0.12) |
| D5 | (2, 7, 0.06); (14, 7, 0.07) |
| D6 | (1, 7, 0.17); (2, 6, 0.35); (8, 7, 0.14); (10, 7, 0.16); (11, 7, 0.19); (12, 7, 0.07); (13, 7, 0.07) |

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
| D1 | 4 (2025-08-29) | 58.00, 58.00 | 57.80, 58.07 | 0.21 | 1.3 |
| D1 | 5 (2025-09-24) | 58.00, 58.00 | 57.81, 57.89 | 0.22 | 1.4 |
| D1 | 6 (2025-10-25) | [58.0, 58.0] | not measured | – | – |
| D1 | 14 (2026-07-06) | [58.0, 58.0] | not measured | – | – |
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
| D5 | 14 (2026-06-21) | 58.00, 58.00 | 58.14, 58.03 | 0.14 | 0.9 |
| D6 | 1 (2025-04-25) | [58.0, 58.0] | not measured | – | – |
| D6 | 2 (2025-06-12) | [58.0, 58.0] | not measured | – | – |
| D6 | 8 (2025-12-26) | [58.0, 58.0] | not measured | – | – |
| D6 | 10 (2026-03-08) | [58.0, 58.0] | not measured | – | – |
| D6 | 11 (2026-04-01) | [58.0, 58.0] | not measured | – | – |
| D6 | 12 (2026-05-03) | 58.00, 58.00 | 58.06, 57.96 | 0.07 | 0.4 |
| D6 | 13 (2026-05-23) | 58.00, 58.00 | 58.10, 58.12 | 0.16 | 1.0 |

Predicted total shift first→last visit: 0.00 px (0.0″) between 2025-04-29 and 2026-09-24.

### RW Aurigae (young variable star) (`rwaur`)
Frames: 205; visits: 3; releases: ['DR1', 'QR3']; dates 2025-09-01 to 2026-09-16

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (1, 10, 0.16); (2, 9, 0.18); (3, 10, 0.18) |
| D2 | (1, 10, 0.19); (2, 10, 0.22); (3, 9, 0.20) |
| D3 | (1, 11, 0.17); (2, 11, 0.25); (3, 11, 0.20) |
| D4 | (1, 14, 0.14); (2, 13, 0.15); (3, 15, 0.16) |
| D5 | (1, 15, 0.18); (2, 15, 0.19); (3, 15, 0.18) |
| D6 | (1, 16, 0.12); (2, 16, 0.15); (3, 16, 0.20) |

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
| D1 | 1 (2025-09-02) | 58.00, 58.00 | 57.91, 57.89 | 0.14 | 0.9 |
| D1 | 2 (2026-03-04) | 58.00, 58.00 | 58.08, 58.04 | 0.09 | 0.6 |
| D1 | 3 (2026-09-02) | 58.00, 58.00 | 57.82, 57.91 | 0.20 | 1.2 |
| D2 | 1 (2025-09-08) | 58.00, 58.00 | 57.85, 57.94 | 0.16 | 1.0 |
| D2 | 2 (2026-03-01) | 58.00, 58.00 | 57.88, 57.99 | 0.12 | 0.7 |
| D2 | 3 (2026-09-10) | 58.00, 58.00 | 57.66, 57.90 | 0.35 | 2.2 |
| D3 | 1 (2025-09-17) | 58.00, 58.00 | 57.89, 57.91 | 0.14 | 0.9 |
| D3 | 2 (2026-02-20) | 58.00, 58.00 | 57.97, 57.85 | 0.15 | 0.9 |
| D3 | 3 (2026-09-13) | 58.00, 58.00 | 57.64, 57.88 | 0.38 | 2.3 |
| D4 | 1 (2025-09-01) | 58.00, 58.00 | 57.90, 57.94 | 0.12 | 0.7 |
| D4 | 2 (2026-03-04) | 58.00, 58.00 | 57.73, 57.92 | 0.28 | 1.7 |
| D4 | 3 (2026-09-02) | 58.00, 58.00 | 57.88, 57.99 | 0.12 | 0.7 |
| D5 | 1 (2025-09-08) | 58.00, 58.00 | 57.77, 57.75 | 0.34 | 2.1 |
| D5 | 2 (2026-03-01) | 58.00, 58.00 | 57.85, 58.04 | 0.16 | 1.0 |
| D5 | 3 (2026-09-10) | 58.00, 58.00 | 57.65, 57.86 | 0.38 | 2.3 |
| D6 | 1 (2025-09-17) | 58.00, 58.00 | 57.83, 57.97 | 0.17 | 1.1 |
| D6 | 2 (2026-02-20) | 58.00, 58.00 | 57.96, 57.84 | 0.16 | 1.0 |
| D6 | 3 (2026-09-13) | 58.00, 58.00 | 57.58, 57.90 | 0.43 | 2.7 |

Predicted total shift first→last visit: 0.00 px (0.0″) between 2025-09-10 and 2026-09-11.

### WISE 0855−0714 (coldest known brown dwarf) (`wise0855`)
Frames: 149; visits: 3; releases: ['DR1']; dates 2025-05-05 to 2026-05-14

**Check 1 — alignment** (median distance between measured centroid and Gaia position of isolated G=9–14 stars, pixels; 1 px = 6.15″)

| Detector | per visit: (visit, n stars, median residual px) |
|---|---|
| D1 | (2, 1, 0.11); (3, 1, 0.14) |
| D2 | (1, 1, 0.19); (2, 0, –); (3, 1, 0.23) |
| D3 | (2, 0, –); (3, 1, 0.23) |
| D4 | (2, 2, 0.17); (3, 1, 0.25) |
| D5 | (1, 2, 0.15); (2, 2, 0.26); (3, 2, 0.11) |
| D6 | (2, 2, 0.10); (3, 2, 0.14) |

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
| D1 | 2 (2025-10-31) | 57.75, 58.00 | 59.06, 57.37 | 1.45 | 8.9 |
| D1 | 3 (2026-05-03) | 58.55, 57.91 | 59.08, 57.34 | 0.78 | 4.8 |
| D2 | 1 (2025-05-06) | 57.24, 58.02 | 59.08, 57.34 | 1.96 | 12.1 |
| D2 | 2 (2025-11-07) | 57.79, 58.00 | 59.07, 57.38 | 1.42 | 8.7 |
| D2 | 3 (2026-05-03) | 58.57, 57.90 | 59.19, 57.30 | 0.86 | 5.3 |
| D3 | 2 (2025-11-10) | 57.79, 58.00 | 58.99, 57.40 | 1.34 | 8.3 |
| D3 | 3 (2026-04-22) | 58.53, 57.91 | 59.29, 57.26 | 1.00 | 6.2 |
| D4 | 2 (2025-10-31) | 57.75, 58.00 | 58.87, 57.46 | 1.24 | 7.6 |
| D4 | 3 (2026-05-03) | 58.55, 57.91 | 59.34, 57.30 | 1.00 | 6.1 |
| D5 | 1 (2025-05-06) | 57.24, 58.02 | 57.73, 57.59 | 0.65 | 4.0 |
| D5 | 2 (2025-11-07) | 57.81, 58.00 | 58.29, 57.78 | 0.53 | 3.2 |
| D5 | 3 (2026-05-03) | 58.57, 57.90 | 58.90, 57.70 | 0.39 | 2.4 |
| D6 | 2 (2025-11-10) | 57.79, 58.00 | 58.08, 57.96 | 0.29 | 1.8 |
| D6 | 3 (2026-04-22) | 58.53, 57.91 | 58.87, 57.63 | 0.44 | 2.7 |

Predicted total shift first→last visit: 1.31 px (8.1″) between 2025-05-06 and 2026-05-03.

