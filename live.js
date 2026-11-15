// SPOT - LIVE mode: build a field for any RA/Dec in the visitor's browser.
// Written with AI assistance under the direction of Ali (team AITHMAC).
//
// How: (1) a compact index of every SPHEREx visit (pointing + time), made by our pipeline from the
// file headers in IRSA's public AWS bucket; (2) the fixed layout of the 6 detectors; (3) the fixed
// pixel->wavelength tables. The browser predicts which files contain the target, reads each file's
// header (32 KB) to confirm with the exact sky coordinates, then reads only the rows it needs
// (HTTP Range requests; the bucket allows this from any website). No server of ours is involved.
"use strict";
(function () {
  const BUCKET = "https://nasa-irsa-spherex.s3.amazonaws.com/";
  const IRSA = "https://irsa.ipac.caltech.edu/ibe/data/spherex/";
  const NPIX = 2040, ROWB = NPIX * 4, IMG_BYTES = NPIX * NPIX * 4; // 16,646,400 = 5780 FITS blocks
  const BAD = [0, 1, 2, 6, 7, 9, 10, 11, 15, 17, 19, 20, 22, 23, 24, 25, 26, 27].reduce((m, b) => m | (1 << b), 0);
  // Saturation-type flags are kept for display on pixels SPHEREx maps to a known source (bit 21),
  // so bright stars do not turn into holes (same rule as the Python pipeline).
  const SAT = [0, 2, 15, 26].reduce((m, b) => m | (1 << b), 0), SOURCE = 1 << 21;
  const isBad = f => (f & BAD) !== 0 && !((f & SOURCE) && !(f & (BAD & ~SAT)));
  const D2R = Math.PI / 180;
  let IDX = null, GEO = null, WAVE = null;
  const BANDS = { 1: [0.75, 1.09], 2: [1.10, 1.62], 3: [1.63, 2.41], 4: [2.42, 3.82], 5: [3.83, 4.41], 6: [4.42, 5.00] };

  async function loadAll() {
    if (IDX) return;
    const [a, b, c] = await Promise.all(["data/live/index.json", "data/live/geometry.json", "data/live/wave.json"].map(u => fetch(u).then(r => { if (!r.ok) throw new Error(u); return r.json(); })));
    IDX = a; GEO = b; WAVE = c;
  }
  async function range(key, start, end) {
    for (let k = 0; k < 4; k++) {
      try {
        const r = await fetch(BUCKET + key, { headers: { Range: `bytes=${start}-${end}` } });
        if (r.status === 206 || r.status === 200) return new DataView(await r.arrayBuffer());
      } catch (e) { /* retry */ }
      await new Promise(res => setTimeout(res, 800 * 2 ** k));
    }
    throw new Error("download failed");
  }
  function parseHeader(dv, off) {
    const cards = {}; let i = off;
    const dec = new TextDecoder("latin1");
    for (; i + 80 <= dv.byteLength; i += 80) {
      const s = dec.decode(new Uint8Array(dv.buffer, dv.byteOffset + i, 80));
      const k = s.slice(0, 8).trim();
      if (k === "END") { const len = Math.ceil((i + 80 - off) / 2880) * 2880; return { cards, len }; }
      if (s[8] === "=") {
        let v = s.slice(10).split("/")[0].trim();
        if (v.startsWith("'")) v = s.slice(10).match(/'([^']*)'/)?.[1]?.trim() ?? v;
        else v = isNaN(+v) ? v : +v;
        cards[k] = v;
      }
    }
    return null;
  }
  // ---- RICE_1 decompression of one tile (cfitsio algorithm, 4-byte pixels, blocksize 32)
  const NZ = new Uint8Array(256); for (let v = 1; v < 256; v++) NZ[v] = 32 - Math.clz32(v);
  function riceDecode(bytes, nx, nblock) {
    const out = new Int32Array(nx), fsbits = 5, fsmax = 25, bbits = 32;
    let c = 0;
    let lastpix = ((bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3]) | 0; c = 4;
    let b = bytes[c++], nbits = 8;
    for (let i = 0; i < nx; i += nblock) {
      const imax = Math.min(i + nblock, nx);
      nbits -= fsbits;
      while (nbits < 0) { b = ((b << 8) | bytes[c++]) >>> 0; nbits += 8; }
      const fs = (b >>> nbits) - 1;
      b &= (1 << nbits) - 1;
      if (fs < 0) { for (let j = i; j < imax; j++) out[j] = lastpix; }
      else if (fs === fsmax) {
        for (let j = i; j < imax; j++) {
          let k = bbits - nbits;
          let diff = k >= 32 ? 0 : (b << k) >>> 0;
          for (k -= 8; k >= 0; k -= 8) { b = bytes[c++]; diff = (diff | (b << k)) >>> 0; }
          if (nbits > 0) { b = bytes[c++]; diff = (diff | (b >>> (-k))) >>> 0; b &= (1 << nbits) - 1; } else b = 0;
          const d = (diff & 1) === 0 ? (diff >>> 1) : ~(diff >>> 1);
          out[j] = (d + lastpix) | 0; lastpix = out[j];
        }
      } else {
        for (let j = i; j < imax; j++) {
          while (b === 0) { nbits += 8; b = bytes[c++]; }
          const nzero = nbits - NZ[b];
          nbits -= nzero + 1;
          b ^= 1 << nbits;
          nbits -= fs;
          while (nbits < 0) { b = ((b << 8) | bytes[c++]) >>> 0; nbits += 8; }
          const diff = ((nzero << fs) | (b >>> nbits)) >>> 0;
          b &= (1 << nbits) - 1;
          const d = (diff & 1) === 0 ? (diff >>> 1) : ~(diff >>> 1);
          out[j] = (d + lastpix) | 0; lastpix = out[j];
        }
      }
    }
    return out;
  }
  // FLAGS rows y0..y1 from the tile-compressed (one tile per row) FLAGS extension
  async function flagRows(key, fOff, y0, y1) {
    const fh = parseHeader(await range(key, fOff, fOff + 25919), 0);
    const C = fh.cards, dataOff = fOff + fh.len;
    if (C.ZCMPTYPE !== "RICE_1" || C.ZTILE2 !== 1) throw new Error("unexpected FLAGS compression " + C.ZCMPTYPE);
    const rowLen = C.NAXIS1, heap = dataOff + (C.THEAP || C.NAXIS1 * C.NAXIS2), nblock = C.ZVAL1 || 32;
    const desc = await range(key, dataOff + y0 * rowLen, dataOff + (y1 + 1) * rowLen - 1);
    const ds = []; for (let y = 0; y <= y1 - y0; y++) ds.push([desc.getInt32(y * rowLen, false), desc.getInt32(y * rowLen + 4, false)]);
    const lo = Math.min(...ds.map(d => d[1])), hi = Math.max(...ds.map(d => d[1] + d[0]));
    const hv = await range(key, heap + lo, heap + hi - 1);
    const u8 = new Uint8Array(hv.buffer, hv.byteOffset, hv.byteLength);
    return ds.map(([n, o]) => riceDecode(u8.subarray(o - lo, o - lo + n), C.ZNAXIS1, nblock));
  }
  // ---- WCS (TAN-SIP), world -> pixel using the inverse SIP polynomials AP/BP
  function makeWCS(c) {
    const pc = [c.PC1_1, c.PC1_2, c.PC2_1, c.PC2_2].map(v => v * (c.CDELT1 || 1));
    const det = pc[0] * pc[3] - pc[1] * pc[2];
    const inv = [pc[3] / det, -pc[1] / det, -pc[2] / det, pc[0] / det];
    const poly = (pre, ord) => { const t = []; for (let p = 0; p <= ord; p++) for (let q = 0; q <= ord - p; q++) { const v = c[`${pre}_${p}_${q}`]; if (v) t.push([p, q, v]); } return t; };
    const AP = poly("AP", c.AP_ORDER || 0), BP = poly("BP", c.BP_ORDER || 0);
    return { crval: [c.CRVAL1, c.CRVAL2], crpix: [c.CRPIX1, c.CRPIX2], inv, AP, BP };
  }
  function tanProject(ra, dec, ra0, dec0) { // degrees of intermediate world coords (xi, eta)
    const a = ra * D2R, d = dec * D2R, a0 = ra0 * D2R, d0 = dec0 * D2R;
    const cosc = Math.sin(d0) * Math.sin(d) + Math.cos(d0) * Math.cos(d) * Math.cos(a - a0);
    return [Math.cos(d) * Math.sin(a - a0) / cosc / D2R, (Math.cos(d0) * Math.sin(d) - Math.sin(d0) * Math.cos(d) * Math.cos(a - a0)) / cosc / D2R, cosc];
  }
  function tanDeproject(xi, eta, ra0, dec0) {
    const x = xi * D2R, y = eta * D2R, d0 = dec0 * D2R;
    const rho = Math.hypot(x, y), c = Math.atan(rho);
    if (rho === 0) return [ra0, dec0];
    const dec = Math.asin(Math.cos(c) * Math.sin(d0) + y * Math.sin(c) * Math.cos(d0) / rho);
    const ra = ra0 * D2R + Math.atan2(x * Math.sin(c), rho * Math.cos(d0) * Math.cos(c) - y * Math.sin(d0) * Math.sin(c));
    return [((ra / D2R) % 360 + 360) % 360, dec / D2R];
  }
  function world2pix(w, ra, dec) { // 0-based pixel
    // FITS TAN uses xi = -(RA offset) convention through the PC matrix; standard native: x = xi(east positive)
    const [xi, eta, cosc] = tanProject(ra, dec, w.crval[0], w.crval[1]);
    if (cosc <= 0) return [NaN, NaN];
    const U = w.inv[0] * xi + w.inv[1] * eta, V = w.inv[2] * xi + w.inv[3] * eta;
    let du = 0, dv = 0;
    for (const [p, q, v] of w.AP) du += v * U ** p * V ** q;
    for (const [p, q, v] of w.BP) dv += v * U ** p * V ** q;
    return [w.crpix[0] + U + du - 1, w.crpix[1] + V + dv - 1];
  }
  // ---- wavelength at a pixel from the shipped node table (bilinear; the FITS -TAB lookup is linear)
  function wave(det, x, y) {
    const T = WAVE[String(det)];
    const f = (v, n) => { let i = 0; while (i < n.length - 2 && v > n[i + 1]) i++; return [i, Math.min(1, Math.max(0, (v - n[i]) / (n[i + 1] - n[i])))]; };
    const [i, tx] = f(x, T.nodes_x), [j, ty] = f(y, T.nodes_y);
    const g = (A) => (A[j][i] * (1 - tx) + A[j][i + 1] * tx) * (1 - ty) + (A[j + 1][i] * (1 - tx) + A[j + 1][i + 1] * tx) * ty;
    return [g(T.wl), g(T.bw)];
  }
  function sep(ra1, d1, ra2, d2) {
    const c = Math.sin(d1 * D2R) * Math.sin(d2 * D2R) + Math.cos(d1 * D2R) * Math.cos(d2 * D2R) * Math.cos((ra1 - ra2) * D2R);
    return Math.acos(Math.min(1, Math.max(-1, c))) / D2R;
  }
  // ---- candidate files from the index + rigid focal-plane geometry
  function candidates(ra, dec, dets) {
    const out = [], R = IDX.rows, F = IDX.folders;
    for (const r of R) {
      const [fi, visit, ra4, dec4, mjd3, phi2, mask] = r;
      const rc = ra4 / 1e4, dc = dec4 / 1e4;
      if (Math.abs(dc - dec) > 9) continue;
      if (sep(ra, dec, rc, dc) > 8.5) continue;
      // target in the visit's detector-2 exposure-1 frame (TAN, no distortion)
      const phi = phi2 / 100 * D2R, k = GEO.scale_deg;
      const pc = [k * Math.cos(phi), k * Math.sin(phi), k * Math.sin(phi), -k * Math.cos(phi)];
      const det = pc[0] * pc[3] - pc[1] * pc[2], inv = [pc[3] / det, -pc[1] / det, -pc[2] / det, pc[0] / det];
      const [xi, eta] = tanProject(ra, dec, rc, dc);
      const X = GEO.crpix - 1 + inv[0] * xi + inv[1] * eta, Y = GEO.crpix - 1 + inv[2] * xi + inv[3] * eta;
      for (const g of GEO.frames) { // affine map from D2/exp1 pixels to (exp, det) pixels
        const x = g.a[0] * X + g.a[1] * Y + g.a[2], y = g.a[3] * X + g.a[4] * Y + g.a[5];
        if (x < -GEO.margin || y < -GEO.margin || x > NPIX + GEO.margin || y > NPIX + GEO.margin) continue;
        for (const d of [g.det, g.det + 3]) {
          if (!dets.includes(d)) continue;
          if (mask !== undefined && !(mask & (1 << ((g.exp - 1) * 6 + d - 1)))) continue; // file does not exist
          const fol = F[fi], vs = String(visit).padStart(4, "0"), ek = `${vs}_${g.exp}_${d}`;
          const ver = (fol.exc && fol.exc[ek]) || fol.ver;
          const key = `${fol.rel}/level2/${fol.week}/${ver}/${d}/level2_${fol.week}_${vs}_${g.exp}D${d}_spx_${ver}.fits`;
          out.push({ key, mjd: IDX.mjd0 + mjd3 / 1e3, det: d, exp: g.exp, px: x, py: y });
        }
      }
    }
    return out;
  }
  // keep at most `cap` files per (detector, visit), nearest to a fixed wavelength grid (same grid every visit)
  function selectCands(cand, cap) {
    cand.sort((a, b) => a.mjd - b.mjd);
    let ep = 0, last = null; for (const c of cand) { if (last === null || c.mjd - last > 60) ep++; c.ep = ep; last = c.mjd; c.wl = wave(c.det, Math.min(2039, Math.max(0, c.px)), Math.min(2039, Math.max(0, c.py)))[0]; }
    const out = [];
    for (const d of [1, 2, 3, 4, 5, 6]) for (let e = 1; e <= ep; e++) {
      const g = cand.filter(c => c.det === d && c.ep === e && c.px > 0 && c.py > 0 && c.px < NPIX && c.py < NPIX); if (!g.length) continue;
      const [lo, hi] = BANDS[d], chosen = new Set();
      for (let k = 0; k < cap; k++) { const wl = lo + 0.02 + (hi - lo - 0.04) * k / (cap - 1); let best = null; for (const c of g) if (!best || Math.abs(c.wl - wl) < Math.abs(best.wl - wl)) best = c; chosen.add(best); }
      out.push(...chosen);
    }
    return out;
  }
  async function frame(c, ra, dec, half, grid) {
    const dv = await range(c.key, 0, 31679);
    const h1 = parseHeader(dv, 2880); if (!h1) return null;
    const w = makeWCS(h1.cards);
    const [x, y] = world2pix(w, ra, dec);
    const xi = Math.round(x), yi = Math.round(y);
    if (!(xi >= half && yi >= half && xi < NPIX - half && yi < NPIX - half)) return null;
    const dataOff = 2880 + h1.len, y0 = yi - half, y1 = yi + half, x0 = xi - half, n = 2 * half + 1;
    const img = await range(c.key, dataOff + y0 * ROWB, dataOff + (y1 + 1) * ROWB - 1);
    const flg = await flagRows(c.key, dataOff + IMG_BYTES, y0, y1);
    const a = new Float32Array(n * n);
    let nbad = 0;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      let v = img.getFloat32(j * ROWB + (x0 + i) * 4, false);
      if (isBad(flg[j][x0 + i])) { v = NaN; nbad++; }
      a[j * n + i] = v;
    }
    // robust background (median of valid pixels)
    const vals = Array.from(a).filter(Number.isFinite).sort((p, q) => p - q);
    const med = vals.length ? vals[vals.length >> 1] : 0;
    for (let i = 0; i < a.length; i++) a[i] -= med;
    // reproject onto the north-up grid by bilinear sampling
    const G = grid.n, out = new Float32Array(G * G).fill(NaN), s = grid.scale / 3600;
    for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
      const [r2, d2] = tanDeproject(-((i - (G - 1) / 2) * s), ((G - 1) / 2 - j) * s, ra, dec);
      const [px, py] = world2pix(w, r2, d2);
      const u = px - x0, v = py - y0, iu = Math.floor(u), iv = Math.floor(v);
      if (iu < 0 || iv < 0 || iu >= n - 1 || iv >= n - 1) continue;
      const fu = u - iu, fv = v - iv, q = iv * n + iu;
      const val = (a[q] * (1 - fu) + a[q + 1] * fu) * (1 - fv) + (a[q + n] * (1 - fu) + a[q + n + 1] * fu) * fv;
      out[j * G + i] = val;
    }
    const [wl, bw] = wave(c.det, x, y);
    const mjd = +h1.cards["MJD-AVG"] || +h1.cards["MJD-OBS"];
    return { img: out, mjd, utc: h1.cards["DATE-AVG"] || h1.cards["DATE-OBS"], det: c.det, obsid: h1.cards.OBSID, wl, bw,
      bad: nbad / (n * n), key: c.key, release: c.key.split("/")[0].toUpperCase() };
  }
  // ---- turn float images into PNG data URLs with a shared stretch
  function stretch(imgs) {
    const v = []; for (const im of imgs) for (let i = 0; i < im.length; i += 3) if (Number.isFinite(im[i])) v.push(im[i]);
    v.sort((a, b) => a - b); if (!v.length) return [0, 1];
    return [v[Math.floor(v.length * 0.02)], Math.max(v[Math.floor(v.length * 0.998)], v[Math.floor(v.length * 0.02)] + 1e-6)];
  }
  function toURL(im, G, lo, hi, signed) {
    const c = document.createElement("canvas"); c.width = G; c.height = G;
    const ctx = c.getContext("2d"), d = ctx.createImageData(G, G);
    const as = Math.asinh(8);
    for (let i = 0; i < G * G; i++) {
      const v = im[i]; let z;
      if (!Number.isFinite(v)) { d.data[4 * i + 3] = 0; continue; }
      if (signed) z = 0.5 + 0.5 * Math.max(-1, Math.min(1, v / hi));
      else { z = Math.max(0, Math.min(1, (v - lo) / (hi - lo))); z = Math.asinh(8 * z) / as; }
      const g = Math.round(z * 255); d.data[4 * i] = d.data[4 * i + 1] = d.data[4 * i + 2] = g; d.data[4 * i + 3] = 255;
    }
    ctx.putImageData(d, 0, 0); return c.toDataURL("image/png");
  }
  function mean(arrs, G) {
    const out = new Float32Array(G * G).fill(NaN);
    for (let i = 0; i < G * G; i++) { let s = 0, n = 0; for (const a of arrs) if (Number.isFinite(a[i])) { s += a[i]; n++; } if (n) out[i] = s / n; }
    return out;
  }
  async function run(ra, dec, msgEl, opts) {
    const box = document.getElementById("liveBox");
    const dets = opts.dets, size = opts.size, half = Math.ceil(size / 2 * Math.SQRT2 * 3600 / 6.15) + 3;
    const G = Math.round(size * 3600 / 6.15) | 1, grid = { n: G, scale: 6.15 };
    const say = (t, p) => { msgEl.innerHTML = t; if (p != null) document.getElementById("liveBar").style.width = (100 * p) + "%"; };
    box.hidden = false;
    say("Loading the SPHEREx visit index…", 0.02);
    await loadAll();
    const all = candidates(ra, dec, dets);
    const cand = selectCands(all, 12);
    if (!cand.length) { say(`No SPHEREx images in our index contain RA ${ra.toFixed(4)}°, Dec ${dec.toFixed(4)}° on the chosen detector(s). Try another detector band.`, 0); return null; }
    say(`Found ${all.length} possible SPHEREx images; using up to 12 per detector per visit, spread across wavelength (${cand.length} files). Reading only the small part you need from NASA/IPAC's public cloud copy…`, 0.05);
    const frames = []; let done = 0, i = 0;
    async function worker() { while (i < cand.length) { const c = cand[i++]; try { const f = await frame(c, ra, dec, half, grid); if (f && f.bad < 0.3) frames.push(f); } catch (e) { } done++; say(`Reading images: ${done}/${cand.length} (kept ${frames.length})`, 0.05 + 0.9 * done / cand.length); } }
    await Promise.all([1, 2, 3, 4, 5, 6].map(worker));
    if (!frames.length) { say("The candidate images did not fully contain this position. Try a smaller field of view.", 0); return null; }
    frames.sort((a, b) => a.mjd - b.mjd);
    let ep = 0, last = null; for (const f of frames) { if (last === null || f.mjd - last > 60) ep++; f.epoch = ep; last = f.mjd; }
    const field = { id: "live", title: `Live: RA ${ra.toFixed(4)}°, Dec ${dec.toFixed(4)}°`, kind: "custom", ra_deg: ra, dec_deg: dec, size_deg: size,
      grid_px: G, pixel_scale_arcsec: 6.15, astrometry_source: "Position typed by you", catalog: {}, story: { hook: "Built live in your browser from real SPHEREx images.", what_to_look_for: "Flip between visits. A dot that jumps is moving; a dot that flashes changed brightness. Check the flags before believing anything new: cosmic rays and ghosts can fool you.", honest: "Live mode uses a simpler cleaning than the ready-made fields (median background instead of the zodiacal-light model) and does not measure spectra." },
      bands: [], channels: [], track: [], live: true,
      frames: frames.map(f => ({ obsid: f.obsid, detector: f.det, epoch: f.epoch, utc: (f.utc || "") + "Z", mjd: f.mjd, wavelength_um: f.wl, bandwidth_um: f.bw, release: f.release, version: "", source_uri: IRSA + f.key, bad_fraction: f.bad, bad_fraction_center: 0, phot: null })) };
    for (const d of dets) {
      let fd = frames.filter(f => f.det === d); if (!fd.length) continue;
      // fair comparison: keep only the wavelength range shared by every visit (drop a visit if too narrow)
      let eps = [...new Set(fd.map(f => f.epoch))];
      const width = BANDS[d][1] - BANDS[d][0];
      let lo, hi;
      for (;;) {
        const r = eps.map(e => { const w = fd.filter(f => f.epoch === e).map(f => f.wl); return [Math.min(...w), Math.max(...w), e]; });
        lo = Math.max(...r.map(x => x[0])) - 0.005; hi = Math.min(...r.map(x => x[1])) + 0.005;
        const ok = hi - lo >= 0.35 * width && eps.every(e => fd.filter(f => f.epoch === e && f.wl >= lo && f.wl <= hi).length >= 1);
        if (ok || eps.length <= 1) break;
        const narrow = r.sort((a, b) => (a[1] - a[0]) - (b[1] - b[0]))[0][2];
        eps = eps.filter(e => e !== narrow);
      }
      if (eps.length > 1) fd = fd.filter(f => eps.includes(f.epoch) && f.wl >= lo && f.wl <= hi);
      else fd = fd.filter(f => eps.includes(f.epoch));
      const imgs = eps.map(e => mean(fd.filter(f => f.epoch === e).map(f => f.img), G));
      const [slo, shi] = stretch(imgs);
      const items = eps.map((e, k) => { const fe = fd.filter(f => f.epoch === e); const wl = fe.map(f => f.wl);
        return { epoch: e, n_frames: fe.length, utc_first: fe[0].utc + "Z", utc_last: fe[fe.length - 1].utc + "Z", mjd_mean: fe.reduce((s, f) => s + f.mjd, 0) / fe.length,
          wl_min_um: +Math.min(...wl).toFixed(3), wl_max_um: +Math.max(...wl).toFixed(3), png: toURL(imgs[k], G, slo, shi) }; });
      const diffs = [];
      const pairs = []; for (let k = 0; k < imgs.length - 1; k++) pairs.push([k, k + 1]); if (imgs.length > 2) pairs.push([0, imgs.length - 1]);
      for (const [a, b] of pairs) { const dd = imgs[b].map((v, q) => v - imgs[a][q]); const av = Array.from(dd).filter(Number.isFinite).map(Math.abs).sort((p, q) => p - q); const dh = av.length ? av[Math.floor(av.length * 0.995)] || 1 : 1; diffs.push({ a: eps[a], b: eps[b], png: toURL(dd, G, 0, dh, true) }); }
      field.bands.push({ detector: d, label: `${BANDS[d][0]}–${BANDS[d][1]} µm (detector ${d})`, range_um: BANDS[d], epochs: items, all_png: toURL(mean(imgs, G), G, slo, shi), diffs, stretch: [slo, shi] });
      for (const it of items) if (!field.track.find(t => t.epoch === it.epoch)) field.track.push({ epoch: it.epoch, mjd: it.mjd_mean, utc: it.utc_first });
    }
    field.track.sort((a, b) => a.epoch - b.epoch);
    say(`Done: ${frames.length} real SPHEREx images in ${ep} visit(s).`, 1);
    return field;
  }
  window.SpotLive = {
    _dbg: { isBad, loadAll, candidates, frame, flagRows, riceDecode, world2pix, makeWCS, parseHeader, range, wave, get IDX() { return IDX; } },
    available: () => true,
    run: async (ra, dec, msgEl) => {
      const dets = [...document.querySelectorAll("#liveDets input:checked")].map(i => +i.value);
      const size = +document.getElementById("liveSize").value;
      try {
        const f = await run(ra, dec, msgEl, { dets: dets.length ? dets : [2], size });
        if (f) await window.SpotOpenFieldObject(f);
      } catch (e) { msgEl.textContent = "Live mode failed: " + e.message + ". The ready-made fields still work."; }
    },
  };
})();
