// SPOT - viewer. Written with AI assistance under the direction of Ali (team AITHMAC).
// Vanilla JS, no build step. Reads data/manifest.json and data/fields/<id>/field.json + PNGs.
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const SCALE = 6; // canvas pixels per data pixel
const reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

const S = {
  manifest: null, field: null, fieldId: null, mode: "blink", data: "band", det: 2, chan: null,
  a: 0, b: 1, t: 0, playing: false, timer: null, speed: 1, phase: 0,
  ovTarget: true, ovGaia: false, ovFlags: false, game: null, px: false, pxD: 500, swipeX: 0.5,
  imgs: new Map(),
};

// ------------------------------------------------------------ helpers
function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function fmtDate(utc) { return utc ? utc.slice(0, 10) : "?"; }
function fmtDT(utc) { return utc ? utc.replace("T", " ").replace("Z", " UTC") : "?"; }
function loadImg(src) {
  if (S.imgs.has(src)) return S.imgs.get(src);
  const p = new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("image failed: " + src)); im.src = src; });
  S.imgs.set(src, p);
  return p;
}
function fieldPath(f) { return f.startsWith("data:") ? f : `data/fields/${S.fieldId}/${f}`; }

// Parse "08h55m10.8s", "08:55:10.8", "8 55 10.8" (hours) or decimal degrees.
function parseRA(s) {
  s = s.trim().toLowerCase();
  if (/^[+-]?\d+(\.\d+)?$/.test(s)) return +s;
  const p = s.replace(/[hms:]/g, " ").trim().split(/\s+/).map(Number);
  if (p.some(isNaN) || p.length < 2) return NaN;
  return 15 * (p[0] + (p[1] || 0) / 60 + (p[2] || 0) / 3600);
}
function parseDec(s) {
  s = s.trim().toLowerCase().replace(/[−–]/g, "-");
  if (/^[+-]?\d+(\.\d+)?$/.test(s)) return +s;
  const neg = s.startsWith("-");
  const p = s.replace(/^[+-]/, "").replace(/[d°m's"]/g, " ").replace(/:/g, " ").trim().split(/\s+/).map(Number);
  if (p.some(isNaN) || !p.length) return NaN;
  const v = p[0] + (p[1] || 0) / 60 + (p[2] || 0) / 3600;
  return neg ? -v : v;
}
function sepDeg(ra1, d1, ra2, d2) {
  const r = Math.PI / 180, c = Math.sin(d1 * r) * Math.sin(d2 * r) + Math.cos(d1 * r) * Math.cos(d2 * r) * Math.cos((ra1 - ra2) * r);
  return Math.acos(Math.min(1, Math.max(-1, c))) / r;
}
// sky -> data-grid pixel (0-based, canvas convention: x right = west, y down = south)
function skyToGrid(ra, dec) {
  const f = S.field, r = Math.PI / 180, n = f.grid_px, s = f.pixel_scale_arcsec / 3600;
  const a0 = f.ra_deg * r, d0 = f.dec_deg * r, a = ra * r, d = dec * r;
  const cosc = Math.sin(d0) * Math.sin(d) + Math.cos(d0) * Math.cos(d) * Math.cos(a - a0);
  const xi = Math.cos(d) * Math.sin(a - a0) / cosc / r, eta = (Math.cos(d0) * Math.sin(d) - Math.sin(d0) * Math.cos(d) * Math.cos(a - a0)) / cosc / r;
  return [(n - 1) / 2 - xi / s, (n - 1) / 2 - eta / s];
}
function mjdToYear(mjd) { return 2000 + (mjd - 51544.5) / 365.25; }

// ------------------------------------------------------------ sequence for current selection
function band() { return S.field.bands.find(b => b.detector === S.det); }
function chan() { return S.field.channels.find(c => c.id === S.chan) || S.field.channels[0]; }
function seq() {
  if (S.data === "chan") {
    const c = chan();
    if (!c) return [];
    return c.frames.map((fr, i) => ({ i, png: fr.png, epoch: fr.epoch, utc: fr.utc, mjd: null,
      label: `${fmtDT(fr.utc)} · detector ${fr.detector} · λ = ${fr.wavelength_um.toFixed(3)} µm (±${(fr.bandwidth_um / 2).toFixed(3)})`, fr }));
  }
  const b = band();
  if (!b) return [];
  const wiseItem = (S.wiseOn && S.field.wise) ? [{ i: 0, png: S.field.wise.png, epoch: 0, utc: S.field.wise.utc + "T00:00:00Z", mjd: S.field.wise.mjd,
    pred: S.field.wise.pred_xy, wise: true, label: S.field.wise.label }] : [];
  return wiseItem.concat(b.epochs.map((e, i) => ({ i: i + wiseItem.length, png: e.png, epoch: e.epoch, utc: e.utc_first, mjd: e.mjd_mean, pred: e.pred_xy,
    label: `SPHEREx ${fmtDate(e.utc_first)}${e.utc_last.slice(0, 10) !== e.utc_first.slice(0, 10) ? " → " + fmtDate(e.utc_last) : ""} · ${e.n_frames} frames added · ${e.wl_min_um}–${e.wl_max_um} µm${partial(b, e) ? " · ⚠ covers only part of this band, so colour differences can look like brightness changes" : ""}`, e })));
}
function partial(b, e) {
  const full = Math.max(...b.epochs.map(x => x.wl_max_um - x.wl_min_um));
  return (e.wl_max_um - e.wl_min_um) < 0.6 * full;
}
function trackFor(epoch) { return (S.field.track || []).find(t => t.epoch === epoch); }
function itemMJD(it) { if (it.mjd) return it.mjd; const t = trackFor(it.epoch); return t ? t.mjd : null; }
function targetXY(it) {
  if (it.pred) return it.pred;
  const t = trackFor(it.epoch); return t && isFinite(t.x) ? [t.x, t.y] : null;
}

// ------------------------------------------------------------ init
async function init() {
  try {
    S.manifest = await (await fetch("data/manifest.json", { cache: "no-cache" })).json();
  } catch (e) { $("#cards").textContent = "Could not load the data manifest."; return; }
  const m = S.manifest;
  $("#appName").textContent = m.app_name || "SPOT";
  $("#citation").textContent = m.citation || "";
  if (m.repo_url) $("#repoLink").href = m.repo_url;
  renderCards();
  renderAbout();
  bindUI();
  const q = new URLSearchParams(location.search);
  if (q.get("ra") && q.get("dec")) { $("#raIn").value = q.get("ra"); $("#decIn").value = q.get("dec"); goCoords(q.get("ra"), q.get("dec"), true, q.get("live") === "1"); }
  else if (q.get("field")) {
    await openField(q.get("field"), q);
    if (q.get("px") === "1") { $("#pxOn").checked = true; S.px = true; if (q.get("au")) { S.pxD = +q.get("au"); $("#pxDistVal").textContent = S.pxD; $("#pxDist").value = Math.log10(S.pxD / 100); } $("#pxPanel").open = true; syncButtons(); pxInfo(); draw(); }
    if (location.hash === "#viewer") $("#viewer").scrollIntoView();
  }
}

function renderCards() {
  $("#cards").innerHTML = S.manifest.fields.map(f => `
    <button class="card" data-id="${esc(f.id)}" aria-label="Open ${esc(f.title)}">
      <img src="data/fields/${esc(f.id)}/${esc(f.thumb)}" alt="" loading="lazy" width="117" height="117">
      <div class="cbody"><h3>${esc(f.title)}</h3><span class="badge ${esc(f.kind)}">${esc(f.kind_label || f.kind)}</span><p>${esc(f.hook)}</p></div>
    </button>`).join("");
  $$(".card").forEach(c => c.addEventListener("click", () => { openField(c.dataset.id); }));
}

async function openField(id, q) {
  const meta = S.manifest.fields.find(f => f.id === id);
  if (!meta) return;
  const f = await (await fetch(`data/fields/${id}/field.json`)).json();
  await showField(f, meta, q);
}
window.SpotOpenFieldObject = async (f) => { await showField(f, { kind_label: "live", hook: f.story.hook }, null); };
async function showField(f, meta, q) {
  stop();
  S.fieldId = f.id;
  S.field = f;
  $("#viewer").hidden = false;
  $("#viewerTitle").textContent = f.title;
  const kb = $("#kindBadge"); kb.textContent = meta.kind_label || f.kind; kb.className = "badge " + f.kind;
  $("#hook").textContent = (f.story && f.story.hook) || meta.hook || "";
  $("#scaleNote").textContent = `Each square pixel is ${f.pixel_scale_arcsec.toFixed(1)} arcseconds wide (the Moon is about 1,800 arcseconds). Field: ${f.size_deg}° across. North up, east left.`;
  // defaults
  S.det = (f.story && f.story.best_band) || (f.bands[0] && f.bands[0].detector) || 2;
  S.data = "band"; S.chan = f.channels[0] ? f.channels[0].id : null; S.mode = "blink";
  if (q) {
    if (q.get("data")) S.data = q.get("data") === "chan" ? "chan" : "band";
    if (q.get("det")) S.det = +q.get("det");
    if (q.get("chan")) S.chan = q.get("chan");
    if (q.get("mode")) S.mode = q.get("mode");
  }
  S.wiseOn = !!(f.wise && f.story && f.story.wise_default);
  if (q && q.get("wise")) S.wiseOn = q.get("wise") === "1" && !!f.wise;
  if (!band()) S.det = f.bands[0].detector;
  if (S.data === "chan" && !f.channels.length) S.data = "band";
  const n = seq().length;
  S.a = 0; S.b = Math.max(0, n - 1); S.t = 0;
  if (q) {
    if (q.get("a")) S.a = Math.min(n - 1, +q.get("a")); if (q.get("b")) S.b = Math.min(n - 1, +q.get("b")); if (q.get("t")) S.t = Math.min(n - 1, +q.get("t"));
  }
  S.game = null; $("#gameMsg").textContent = ""; $("#gameBtn").textContent = "Start";
  renderBandBtns(); renderDates(); renderExplain(); renderProv(); renderSpectrum(); renderLightCurve(); syncButtons();
  await draw();
  if (!reduceMotion && seq().length > 1 && (S.mode === "blink" || S.mode === "timeline")) play(); // start moving at once
  if (!q) $("#viewer").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
}

function renderBandBtns() {
  const f = S.field, box = $("#bandBtns");
  if (S.data === "band") {
    box.innerHTML = [1, 2, 3, 4, 5, 6].map(d => {
      const b = f.bands.find(x => x.detector === d);
      return `<button data-det="${d}" ${b ? "" : "disabled"} aria-pressed="${d === S.det}" title="${b ? esc(b.label) : "no data"}">D${d}<br>${b ? b.range_um[0] + "–" + b.range_um[1] + " µm" : "—"}</button>`;
    }).join("");
    const b = band();
    $("#dataHelp").innerHTML = b ? `<strong>${esc(b.label)}.</strong> All frames this detector took of this spot during one visit are added together for a cleaner picture (the challenge's suggestion). Each visit is compared with the same detector at the other visits.` : "";
  } else {
    box.innerHTML = f.channels.map(c => `<button data-chan="${c.id}" aria-pressed="${c.id === S.chan}">${c.wavelength_um.toFixed(2)} µm<br>D${c.detector}</button>`).join("") || "<p class='small muted'>No matched wavelengths for this field.</p>";
    const c = chan();
    $("#dataHelp").innerHTML = c ? `Single frames whose wavelength at the target differs by less than half a bandwidth (${(c.bandwidth_um / 2).toFixed(3)} µm). This is the strictest comparison: same colour of light, different dates.` : "";
  }
  $$("#bandBtns button[data-det]").forEach(bt => bt.addEventListener("click", () => { S.det = +bt.dataset.det; resetDates(); }));
  $$("#bandBtns button[data-chan]").forEach(bt => bt.addEventListener("click", () => { S.chan = bt.dataset.chan; resetDates(); }));
}
function resetDates() { const n = seq().length; S.a = 0; S.b = Math.max(0, n - 1); S.t = 0; renderBandBtns(); renderDates(); syncButtons(); draw(); }

function renderDates() {
  const items = seq();
  const opts = items.map((it, i) => `<option value="${i}">${it.wise ? "WISE " + esc(fmtDate(it.utc)) + " (older telescope)" : "SPHEREx " + esc(fmtDate(it.utc)) + " (visit " + it.epoch + ")"}</option>`).join("");
  $("#selA").innerHTML = opts; $("#selB").innerHTML = opts;
  $("#selA").value = S.a; $("#selB").value = S.b;
  const sl = $("#tSlider"); sl.max = Math.max(0, items.length - 1); sl.value = S.t;
}

function syncButtons() {
  $$("#modeSeg button").forEach(b => b.setAttribute("aria-checked", b.dataset.mode === S.mode));
  $$("#dataSeg button").forEach(b => b.setAttribute("aria-checked", b.dataset.data === S.data));
  $("#dataSeg button[data-data=chan]").disabled = !S.field.channels.length;
  const sumBtn = $("#modeSeg button[data-mode=sum]"); sumBtn.disabled = S.data === "chan";
  const help = {
    blink: "Flips between dates A and B. Things that jump are moving; things that flash are changing brightness.",
    swipe: "Drag the orange line. Left of it: date A. Right of it: date B.",
    diff: S.rawDiff
      ? "Raw difference, later minus earlier. Even stars that do not change leave small black-and-white pairs here, because the pixels are coarse and the two visits are never perfectly sharp in the same way."
      : "Significance of change, later minus earlier. Grey: nothing changed beyond what steady stars show. White: brighter later. Black: brighter earlier. A moving star leaves a black-and-white pair. Full white or black means about 5 times the change steady stars show: a bright star must change by more than about 60% of its peak, or move by roughly one pixel (6 arcseconds) or more. Lone dots are usually artifacts (cosmic rays, satellite trails, reflections of very bright stars): check the frames before trusting one.",
    timeline: "Plays every date in order, like a little video. Drag the slider to scrub.",
    sum: "All dates added together: fainter things become easier to see, but anything that moved gets smeared.",
  };
  $("#modeHelp").textContent = help[S.mode];
  $("#rawWrap").hidden = S.mode !== "diff";
  $("#wiseWrap").hidden = !(S.field && S.field.wise) || S.data !== "band"; $("#wiseOn").checked = !!S.wiseOn;
  $("#playBtn").textContent = S.playing ? "❚❚ Pause" : "▶ Play";
  $("#swipeHandle").hidden = S.mode !== "swipe";
  $("#simBanner").hidden = !S.px;
  updateURL();
}

function updateURL() {
  if (!S.fieldId) return;
  if (S.field && S.field.live) { history.replaceState(null, "", "?" + new URLSearchParams({ ra: S.field.ra_deg.toFixed(5), dec: S.field.dec_deg.toFixed(5) }).toString()); return; }
  const q = new URLSearchParams({ field: S.fieldId, data: S.data, mode: S.mode, a: S.a, b: S.b, t: S.t });
  if (S.data === "band") q.set("det", S.det); else q.set("chan", S.chan);
  if (S.px) { q.set("px", 1); q.set("au", S.pxD); }
  if (S.field && S.field.wise) q.set("wise", S.wiseOn ? 1 : 0);
  history.replaceState(null, "", "?" + q.toString() + location.hash);
}

// ------------------------------------------------------------ drawing
let drawToken = 0;
async function draw() {
  const tok = ++drawToken;
  const cv = $("#cv"), ctx = cv.getContext("2d"), f = S.field, n = f.grid_px;
  cv.width = n * SCALE; cv.height = n * SCALE;
  const items = seq();
  if (!items.length) { ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cv.width, cv.height); $("#frameLabel").textContent = "No data for this selection."; return; }
  const A = items[S.a] || items[0], B = items[S.b] || items[items.length - 1];
  let cur = A, label = "", srcs = [];
  if (S.mode === "blink") { cur = S.phase ? B : A; srcs = [fieldPath(cur.png)]; label = `${S.phase ? "B" : "A"}: ${cur.label}`; }
  else if (S.mode === "timeline") { cur = items[S.t] || A; srcs = [fieldPath(cur.png)]; label = `${S.t + 1}/${items.length}: ${cur.label}`; }
  else if (S.mode === "swipe") { srcs = [fieldPath(A.png), fieldPath(B.png)]; label = `Left A: ${fmtDate(A.utc)} · Right B: ${fmtDate(B.utc)}`; }
  else if (S.mode === "sum") { const b = band(); srcs = [fieldPath(b.all_png)]; label = `All ${items.length} visits added together (detector ${S.det})`; cur = null; }
  else if (S.mode === "diff") {
    const d = findDiff(A, B);
    if (d) { srcs = [fieldPath(d.png)]; label = d.note || `${S.rawDiff || !S.field.bands[0].diffs[0]?.sig_png ? "Raw difference" : "Significance of change"}: ${fmtDate(d.B.utc)} minus ${fmtDate(d.A.utc)}`; }
    else { label = "No difference image for these two dates."; }
    cur = null;
  }
  let ims;
  try { ims = await Promise.all(srcs.map(loadImg)); } catch (e) { $("#frameLabel").textContent = "Image failed to load."; return; }
  if (tok !== drawToken) return;
  ctx.imageSmoothingEnabled = false;
  // background: missing / flagged pixels show through (transparent in the PNG)
  if (S.ovFlags) { ctx.fillStyle = "#ff2fa8"; } else { ctx.fillStyle = S.mode === "diff" ? "#808080" : "#000"; }
  ctx.fillRect(0, 0, cv.width, cv.height);
  if (S.mode === "swipe") {
    ctx.drawImage(S.ovFlags ? flagged(ims[0]) : ims[0], 0, 0, cv.width, cv.height);
    const x = Math.round(S.swipeX * cv.width);
    ctx.save(); ctx.beginPath(); ctx.rect(x, 0, cv.width - x, cv.height); ctx.clip();
    if (S.ovFlags) { ctx.fillStyle = "#ff2fa8"; ctx.fillRect(x, 0, cv.width - x, cv.height); } else { ctx.fillStyle = "#000"; ctx.fillRect(x, 0, cv.width - x, cv.height); }
    ctx.drawImage(S.ovFlags ? flagged(ims[1]) : ims[1], 0, 0, cv.width, cv.height); ctx.restore();
    $("#swipeHandle").style.left = (S.swipeX * 100) + "%";
  } else if (ims[0]) {
    ctx.drawImage(S.ovFlags ? flagged(ims[0]) : ims[0], 0, 0, cv.width, cv.height);
  }
  drawOverlays(ctx, cur, A, B, items);
  $("#frameLabel").textContent = label;
  renderLegend();
}

// Pixels SPHEREx flagged are stored with alpha 254 (filled for display) or 0 (no data).
// With the flag overlay on, paint both kinds pink so nothing is hidden.
const flagCache = new WeakMap();
function flagged(im) {
  if (flagCache.has(im)) return flagCache.get(im);
  const c = document.createElement("canvas"); c.width = im.naturalWidth; c.height = im.naturalHeight;
  const x = c.getContext("2d"); x.drawImage(im, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height);
  for (let i = 0; i < d.data.length; i += 4) if (d.data[i + 3] < 255) { d.data[i] = 255; d.data[i + 1] = 47; d.data[i + 2] = 168; d.data[i + 3] = 255; }
  x.putImageData(d, 0, 0); flagCache.set(im, c); return c;
}

function dpng(d) { return (!S.rawDiff && d.sig_png) ? d.sig_png : d.png; }
function findDiff(A, B) {
  if (A.wise || B.wise) {
    const items = seq().filter(x => !x.wise); if (items.length < 2) return null;
    const r = findDiff(items[0], items[items.length - 1]);
    if (r) r.note = `Difference only compares SPHEREx with SPHEREx (WISE is a different telescope). Showing ${fmtDate(items[items.length - 1].utc)} minus ${fmtDate(items[0].utc)}.`;
    return r;
  }
  if (S.data === "chan") {
    const c = chan(); const d = c.diffs.find(x => x.a === A.i && x.b === B.i);
    if (d) return { png: dpng(d), A, B };
    const d2 = c.diffs.find(x => x.b === B.i) || c.diffs[0];
    const items = seq();
    return d2 ? { png: dpng(d2), A: items[d2.a], B: items[d2.b], note: `Showing ${fmtDate(items[d2.b].utc)} minus ${fmtDate(items[d2.a].utc)} (differences are made for neighbouring dates)` } : null;
  }
  const b = band();
  const d = b.diffs.find(x => x.a === A.epoch && x.b === B.epoch);
  if (d) return { png: dpng(d), A, B };
  const items = seq();
  const d2 = b.diffs.find(x => x.b === B.epoch) || b.diffs[0];
  if (!d2) return null;
  const IA = items.find(x => x.epoch === d2.a), IB = items.find(x => x.epoch === d2.b);
  return { png: dpng(d2), A: IA, B: IB, note: `Showing ${fmtDate(IB.utc)} minus ${fmtDate(IA.utc)} (precomputed for neighbouring visits and first→last)` };
}

function drawOverlays(ctx, cur, A, B, items) {
  const f = S.field, k = SCALE, hidden = S.game && !S.game.revealed;
  const pts = [];
  if (cur) pts.push(cur); else { pts.push(A); if (B !== A) pts.push(B); }
  // target marker(s)
  if (S.ovTarget && !hidden && f.kind !== "control" && f.kind !== "custom") {
    // faint trail of all predicted positions
    ctx.strokeStyle = "rgba(111,211,255,0.45)"; ctx.lineWidth = 2; ctx.beginPath();
    items.forEach((it, i) => { const p = targetXY(it); if (!p) return; const x = (p[0] + 0.5) * k, y = (p[1] + 0.5) * k; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    pts.forEach((it, j) => {
      const p = targetXY(it); if (!p) return;
      const x = (p[0] + 0.5) * k, y = (p[1] + 0.5) * k;
      ctx.strokeStyle = "#6fd3ff"; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x, y, 5 * k, 0, 2 * Math.PI); ctx.stroke();
      ctx.fillStyle = "#6fd3ff"; ctx.font = `bold ${4 * k}px system-ui`;
      const lab = pts.length > 1 ? (j ? "later" : "earlier") : "target";
      ctx.fillText(lab, Math.min(x + 5.5 * k, ctx.canvas.width - ctx.measureText(lab).width - 4), y - 4 * k + (j ? 9 * k : 0));
    });
  }
  // Gaia overlay (positions moved to the image date with Gaia proper motions)
  if (S.ovGaia && f.gaia && !hidden) {
    const it = pts[0]; const mjd = it ? itemMJD(it) : null; const yr = mjd ? mjdToYear(mjd) : 2016.0;
    ctx.strokeStyle = "rgba(255,181,71,0.9)"; ctx.lineWidth = 2;
    for (const g of f.gaia) {
      const dt = yr - 2016.0;
      const dec = g[1] + (g[3] || 0) * dt / 3.6e6, ra = g[0] + (g[2] || 0) * dt / 3.6e6 / Math.cos(g[1] * Math.PI / 180);
      const [x, y] = skyToGrid(ra, dec); const X = (x + 0.5) * k, Y = (y + 0.5) * k, r = 2.2 * k;
      ctx.beginPath(); ctx.moveTo(X - r, Y); ctx.lineTo(X - r / 3, Y); ctx.moveTo(X + r / 3, Y); ctx.lineTo(X + r, Y); ctx.moveTo(X, Y - r); ctx.lineTo(X, Y - r / 3); ctx.moveTo(X, Y + r / 3); ctx.lineTo(X, Y + r); ctx.stroke();
    }
  }
  // Planet X simulation
  if (S.px && f.planetx) {
    pts.forEach((it, j) => {
      const p = pxPos(it.epoch); if (!p) return;
      const [x, y] = p, X = (x + 0.5) * k, Y = (y + 0.5) * k, n = f.grid_px;
      if (x < 0 || y < 0 || x >= n || y >= n) {
        // off the field: arrow at the edge pointing to where it is
        const cx = (n - 1) / 2, cy = (n - 1) / 2, dx = x - cx, dy = y - cy, sc = (n / 2 - 6) / Math.max(Math.abs(dx), Math.abs(dy));
        const ex = (cx + dx * sc + 0.5) * k, ey = (cy + dy * sc + 0.5) * k, ang = Math.atan2(dy, dx);
        ctx.save(); ctx.translate(ex, ey); ctx.rotate(ang); ctx.fillStyle = "#ff6bd6";
        ctx.beginPath(); ctx.moveTo(4 * k, 0); ctx.lineTo(-3 * k, -3 * k); ctx.lineTo(-3 * k, 3 * k); ctx.closePath(); ctx.fill(); ctx.restore();
        const off = Math.hypot(dx, dy) * f.pixel_scale_arcsec / 60;
        ctx.fillStyle = "#ff6bd6"; ctx.font = `bold ${3.4 * k}px system-ui`;
        const tx = Math.min(Math.max(ex - 30 * k, 2 * k), (n - 62) * k), ty = Math.min(Math.max(ey + (ey > n * k / 2 ? -5 * k : 8 * k), 5 * k), (n - 2) * k);
        ctx.fillText(`SIMULATED planet${pts.length > 1 ? (j ? " (B)" : " (A)") : ""}: off field, ${off.toFixed(0)}′ from centre`, tx, ty);
        return;
      }
      const g = ctx.createRadialGradient(X, Y, 0, X, Y, 1.6 * k);
      const neg = S.mode === "diff" && j === 0;
      g.addColorStop(0, neg ? "rgba(0,0,0,1)" : "rgba(255,255,255,1)"); g.addColorStop(1, neg ? "rgba(0,0,0,0)" : "rgba(255,255,255,0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(X, Y, 1.6 * k, 0, 2 * Math.PI); ctx.fill();
      if (!hidden) {
        ctx.setLineDash([6, 5]); ctx.strokeStyle = "#ff6bd6"; ctx.lineWidth = 2; ctx.strokeRect(X - 5 * k, Y - 5 * k, 10 * k, 10 * k); ctx.setLineDash([]);
        ctx.fillStyle = "#ff6bd6"; ctx.font = `bold ${3.6 * k}px system-ui`;
        const tw = ctx.measureText("SIMULATED").width;
        ctx.fillText("SIMULATED", Math.max(2, Math.min(X - 5 * k, ctx.canvas.width - tw - 2)), Y + 9 * k > ctx.canvas.height - 4 ? Y - 6 * k : Y + 9 * k);
      }
    });
  }
  // game taps
  if (S.game) for (const t of S.game.taps) { ctx.strokeStyle = "#ffb547"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(t[0] * k - 12, t[1] * k - 12); ctx.lineTo(t[0] * k + 12, t[1] * k + 12); ctx.moveTo(t[0] * k + 12, t[1] * k - 12); ctx.lineTo(t[0] * k - 12, t[1] * k + 12); ctx.stroke(); }
}

function pxPos(epoch) {
  const P = S.field.planetx; if (!P) return null;
  const ei = P.epochs.indexOf(epoch); if (ei < 0) return null;
  const ds = P.distances_au, D = S.pxD;
  let i = 0; while (i < ds.length - 2 && D > ds[i + 1]) i++;
  const t = (Math.log(D) - Math.log(ds[i])) / (Math.log(ds[i + 1]) - Math.log(ds[i]));
  const a = P.offsets_px[String(ds[i])][ei], b = P.offsets_px[String(ds[i + 1])][ei];
  const n = S.field.grid_px, base = [(n - 1) / 2, (n - 1) / 2 + 0.28 * n];
  return [base[0] + a[0] + (b[0] - a[0]) * t, base[1] + a[1] + (b[1] - a[1]) * t];
}

function renderLegend() {
  const parts = [];
  if (S.ovTarget && S.field.kind !== "control") parts.push("○ blue circle = where catalogue data predict the target on that date");
  if (S.ovGaia) parts.push("+ orange = Gaia stars (ESA), moved to the image date");
  parts.push("very bright stars overload SPHEREx; their centres are drawn white");
  if (S.ovFlags) parts.push("pink = no data or pixel flagged unreliable by the SPHEREx pipeline (shown filled when the overlay is off)");
  if (S.px) parts.push("dashed pink square = SIMULATED planet (not real)");
  $("#legend").textContent = parts.join(" · ");
}

// ------------------------------------------------------------ panels
function renderExplain() {
  const f = S.field, st = f.story || {};
  const tr = f.track || [];
  let motion = "";
  if (tr.length >= 2 && f.catalog && f.catalog.plx) {
    const a = tr[0], b = tr[tr.length - 1];
    const dx = (b.x - a.x) * f.pixel_scale_arcsec, dy = (b.y - a.y) * f.pixel_scale_arcsec;
    motion = `<p>Between ${fmtDate(a.utc)} and ${fmtDate(b.utc)} the catalogue predicts a shift of <strong>${Math.hypot(dx, dy).toFixed(1)} arcseconds</strong> (${(Math.hypot(dx, dy) / f.pixel_scale_arcsec).toFixed(1)} pixels).</p>`;
  }
  $("#explain").innerHTML = `
    ${st.what_to_look_for ? `<h3>What to look for</h3><p>${st.what_to_look_for}</p>` : ""}
    ${st.what_it_is ? `<h3>What it is</h3><p>${st.what_it_is}</p>` : ""}
    ${motion}
    ${st.honest ? `<h3>Honest limits</h3><p>${st.honest}</p>` : ""}
    <p class="small muted">Position data: ${esc(f.astrometry_source)}. Field centre RA ${f.ra_deg.toFixed(5)}°, Dec ${f.dec_deg.toFixed(5)}°. ${f.frames.length} SPHEREx frames in ${(f.track || []).length || "?"} visits.</p>`;
}

function renderProv() {
  const rows = S.field.frames.slice().sort((a, b) => a.mjd - b.mjd).map(fr => `<tr>
    <td>${esc(fmtDT(fr.utc))}</td><td>D${fr.detector}</td><td>${fr.wavelength_um.toFixed(3)}</td><td>${fr.bandwidth_um.toFixed(3)}</td>
    <td>${(fr.bad_fraction * 100).toFixed(1)}%${fr.bad_fraction_center > 0 ? " <span title='flagged pixels near the target'>⚠ centre</span>" : ""}</td>
    <td>${fr.phot && fr.phot.flux_ujy != null ? fr.phot.flux_ujy.toFixed(0) + " ± " + fr.phot.err_ujy.toFixed(0) : "—"}</td>
    <td>${esc(fr.release)}${fr.version ? " v" + esc(fr.version) : ""}</td><td><a href="${esc(fr.source_uri)}" rel="noopener">${esc(fr.obsid)}</a></td></tr>`).join("");
  $("#provTable tbody").innerHTML = rows + `<tr><td colspan="8" class="muted">Real SPHEREx data. Nothing in this table is simulated.</td></tr>`;
}

function renderSpectrum() {
  const f = S.field;
  const hideBad = S.hideFlagged;
  const pts = f.frames.filter(fr => fr.phot && fr.phot.flux_ujy != null && isFinite(fr.phot.flux_ujy) && !(hideBad && fr.phot.bad_in_aperture > 0));
  const ctl = `<label class="chk small"><input type="checkbox" id="hideFlag" ${hideBad ? "checked" : ""}> Hide frames with flagged pixels in the measuring circle</label>`;
  if (!pts.length) { $("#spec").innerHTML = ctl + "<p class='small'>No measurements to show.</p>"; bindHide(); return; }
  const W = 720, H = 300, L = 70, R = 12, T = 12, Bm = 40;
  const ys0 = pts.map(p => p.phot.flux_ujy), mx = Math.max(...ys0.map(Math.abs));
  const [div, unit] = mx > 2e6 ? [1e6, "Jy"] : mx > 2e3 ? [1e3, "mJy"] : [1, "µJy"];
  const ys = ys0.map(v => v / div), lo = Math.min(0, ...ys), hi = Math.max(...ys) * 1.08 || 1;
  const X = w => L + (w - 0.7) / (5.05 - 0.7) * (W - L - R), Y = v => T + (1 - (v - lo) / (hi - lo)) * (H - T - Bm);
  const eps = [...new Set(pts.map(p => p.epoch))].sort((a, b) => a - b);
  const cols = ["#6fd3ff", "#ffb547", "#7be08f", "#ff6bd6", "#c9a0ff", "#ff7b7b", "#ffffff"];
  const marks = ["circle", "square", "diamond", "triangle", "circle", "square", "diamond"];
  const shape = (m, x, y, c, hollow) => {
    const fill = hollow ? "none" : c, s = `stroke="${c}" stroke-width="1.5" fill="${fill}"`;
    if (m === "square") return `<rect x="${x - 3.5}" y="${y - 3.5}" width="7" height="7" ${s}/>`;
    if (m === "diamond") return `<path d="M${x} ${y - 4.5}L${x + 4.5} ${y}L${x} ${y + 4.5}L${x - 4.5} ${y}Z" ${s}/>`;
    if (m === "triangle") return `<path d="M${x} ${y - 4.5}L${x + 4.5} ${y + 4}L${x - 4.5} ${y + 4}Z" ${s}/>`;
    return `<circle cx="${x}" cy="${y}" r="3.8" ${s}/>`;
  };
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Target brightness versus wavelength, coloured by visit date">`;
  for (let w = 1; w <= 5; w++) svg += `<line x1="${X(w)}" x2="${X(w)}" y1="${T}" y2="${H - Bm}" stroke="#2a3754"/><text x="${X(w)}" y="${H - Bm + 16}" fill="#9fb0cc" font-size="12" text-anchor="middle">${w}</text>`;
  svg += `<text x="${(W + L) / 2}" y="${H - 6}" fill="#9fb0cc" font-size="12" text-anchor="middle">wavelength (µm)</text>`;
  for (let i = 0; i <= 4; i++) { const v = lo + (hi - lo) * i / 4; svg += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#1d2840"/><text x="${L - 6}" y="${Y(v) + 4}" fill="#9fb0cc" font-size="11" text-anchor="end">${+v.toPrecision(3)}</text>`; }
  svg += `<text x="14" y="${(H - Bm) / 2}" fill="#9fb0cc" font-size="12" transform="rotate(-90 14 ${(H - Bm) / 2})" text-anchor="middle">flux (${unit})</text>`;
  for (const p of pts) {
    const ei = eps.indexOf(p.epoch), c = cols[ei % cols.length], x = X(p.wavelength_um), fv = p.phot.flux_ujy / div, y = Y(fv);
    const e = p.phot.err_ujy / div; svg += `<line x1="${x}" x2="${x}" y1="${Y(fv - e)}" y2="${Y(fv + e)}" stroke="${c}" stroke-opacity=".5"/>`;
    svg += shape(marks[ei % marks.length], x, y, c, p.phot.bad_in_aperture > 0);
  }
  svg += `</svg>`;
  const legend = eps.map((e, i) => { const fr = pts.find(p => p.epoch === e); return `<span style="color:${cols[i % cols.length]}">● visit ${e} (${fmtDate(fr.utc)})</span>`; }).join(" &nbsp; ");
  $("#spec").innerHTML = ctl + svg + `<p class="small">${legend}. Hollow symbols: some pixels in the measuring circle were flagged (often a saturated bright star); treat them with care.</p>`;
  bindHide();
}
function bindHide() { const h = $("#hideFlag"); if (h) h.addEventListener("change", e => { S.hideFlagged = e.target.checked; renderSpectrum(); }); }

function renderLightCurve() {
  const f = S.field, cols = { 1: "#c9a0ff", 2: "#6fd3ff", 3: "#7be08f", 4: "#ffb547", 5: "#ff7b7b", 6: "#ff6bd6" };
  const series = f.bands.map(b => {
    const pts = b.epochs.filter(e => e.flux_ujy != null && isFinite(e.flux_ujy) && e.flux_ujy > 0);
    if (pts.length < 2) return null;
    const ref = pts;
    const mean = ref.reduce((a, e) => a + e.flux_ujy, 0) / ref.length;
    return { det: b.detector, pts: pts.map(e => ({ t: e.mjd_mean, y: 100 * (e.flux_ujy / mean - 1), err: 100 * (e.noise_ujy || 0) / mean, sat: (e.phot_method || "core") !== "core", utc: e.utc_first })) };
  }).filter(Boolean);
  if (!series.length || f.kind === "control" && false) { $("#lc").innerHTML = "<p class='small'>Not enough measurements for a light curve.</p>"; return; }
  const all = series.flatMap(s => s.pts), W = 720, H = 280, L = 60, R = 12, T = 12, Bm = 40;
  const t0 = Math.min(...all.map(p => p.t)) - 10, t1 = Math.max(...all.map(p => p.t)) + 10;
  let ylo = Math.min(-10, ...all.map(p => p.y - p.err)), yhi = Math.max(10, ...all.map(p => p.y + p.err));
  ylo = Math.max(ylo, -100); yhi = Math.min(yhi, 300);
  const X = t => L + (t - t0) / (t1 - t0) * (W - L - R), Y = v => T + (1 - (Math.min(yhi, Math.max(ylo, v)) - ylo) / (yhi - ylo)) * (H - T - Bm);
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Target brightness change over time by detector band">`;
  for (let i = 0; i <= 4; i++) { const v = ylo + (yhi - ylo) * i / 4; svg += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#1d2840"/><text x="${L - 6}" y="${Y(v) + 4}" fill="#9fb0cc" font-size="11" text-anchor="end">${v > 0 ? "+" : ""}${Math.round(v)}%</text>`; }
  svg += `<line x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}" stroke="#56688a" stroke-dasharray="4 4"/>`;
  const months = []; for (let m = Math.ceil(t0 / 30.44); m * 30.44 < t1; m += 2) months.push(m * 30.44);
  for (const t of months) { const d = new Date((t - 40587) * 864e5).toISOString().slice(0, 7); svg += `<text x="${X(t)}" y="${H - Bm + 16}" fill="#9fb0cc" font-size="11" text-anchor="middle">${d}</text>`; }
  for (const s of series) {
    const c = cols[s.det];
    svg += `<polyline fill="none" stroke="${c}" stroke-opacity=".5" points="${s.pts.map(p => `${X(p.t)},${Y(p.y)}`).join(" ")}"/>`;
    for (const p of s.pts) { svg += `<line x1="${X(p.t)}" x2="${X(p.t)}" y1="${Y(p.y - p.err)}" y2="${Y(p.y + p.err)}" stroke="${c}" stroke-opacity=".5"/><circle cx="${X(p.t)}" cy="${Y(p.y)}" r="4" stroke="${c}" stroke-width="1.5" fill="${p.sat ? "none" : c}"><title>D${s.det} ${p.utc.slice(0, 10)}: ${p.y.toFixed(0)}%</title></circle>`; }
  }
  svg += `</svg>`;
  $("#lc").innerHTML = svg + `<p class="small">${series.map(s => `<span style="color:${cols[s.det]}">● D${s.det}</span>`).join(" &nbsp; ")} (detector bands). Values outside −100% to +300% are clipped to the edge.</p>`;
}

function renderAbout() {
  const m = S.manifest;
  $("#aboutBody").innerHTML = m.about_html || "";
}

// ------------------------------------------------------------ play / game / coords
function stop() { S.playing = false; clearInterval(S.timer); S.timer = null; S.phase = 0; if ($("#playBtn")) $("#playBtn").textContent = "▶ Play"; }
function play() {
  stop(); S.playing = true;
  if (S.mode !== "blink" && S.mode !== "timeline") S.mode = "blink";
  S.timer = setInterval(() => {
    if (S.mode === "blink") S.phase ^= 1;
    else { const n = seq().length; S.t = (S.t + 1) % n; $("#tSlider").value = S.t; }
    draw();
  }, 1000 / Math.min(2.5, S.speed));
  syncButtons();
}

function startGame() {
  if (S.game && !S.game.revealed) { revealGame(); return; }
  S.game = { taps: [], revealed: false };
  S.mode = "blink"; syncButtons(); if (!reduceMotion) play();
  $("#gameBtn").textContent = "Give up & reveal";
  $("#gameMsg").textContent = "Markers hidden. Tap the spot where something moved or changed brightness.";
  draw();
}
function revealGame(msg) {
  S.game.revealed = true; $("#gameBtn").textContent = "Play again";
  const st = S.field.story || {};
  $("#gameMsg").innerHTML = (msg ? msg + " " : "") + (st.answer || st.what_it_is || "");
  draw();
}
function gameTap(gx, gy) {
  const f = S.field; S.game.taps.push([gx, gy]);
  if (f.kind === "control") { revealGame("<strong>Trick question!</strong> Nothing real changes here: this is our control field."); return; }
  const items = seq(); const cand = [items[S.a], items[S.b]].map(targetXY).filter(Boolean);
  if (S.px && f.planetx) { const p1 = pxPos(items[S.a].epoch), p2 = pxPos(items[S.b].epoch); [p1, p2].forEach(p => p && cand.push(p)); }
  const best = Math.min(...cand.map(p => Math.hypot(p[0] - gx, p[1] - gy)));
  if (best <= 6) revealGame(`<strong>Yes!</strong> You found it (within ${(best * f.pixel_scale_arcsec).toFixed(0)} arcseconds).`);
  else if (S.game.taps.length >= 3) revealGame("<strong>Not quite.</strong> Here it is.");
  else { $("#gameMsg").textContent = `Not there (${S.game.taps.length}/3 tries). Look for a dot that jumps or flashes.`; draw(); }
}

function goCoords(raS, decS, fromURL, fromURLForceLive) {
  const ra = parseRA(raS), dec = parseDec(decS), msg = $("#coordMsg");
  if (!isFinite(ra) || !isFinite(dec) || ra < 0 || ra >= 360 || dec < -90 || dec > 90) { msg.textContent = "Please enter a Right Ascension (0–24h or 0–360°) and a Declination (−90° to +90°)."; return; }
  let best = null;
  for (const f of S.manifest.fields) { const d = sepDeg(ra, dec, f.ra_deg, f.dec_deg); if (!best || d < best.d) best = { f, d }; }
  if (best && best.d < best.f.size_deg / 2 && !fromURLForceLive) {
    msg.textContent = `RA ${ra.toFixed(4)}°, Dec ${dec.toFixed(4)}° is inside the ready-made field "${best.f.title}" (${(best.d * 60).toFixed(1)} arcmin from its centre). Opening it.`;
    openField(best.f.id); return;
  }
  if (window.SpotLive && window.SpotLive.available()) { window.SpotLive.run(ra, dec, msg); return; }
  msg.innerHTML = `RA ${ra.toFixed(4)}°, Dec ${dec.toFixed(4)}° is not one of the ready-made fields yet${best ? ` (nearest: ${esc(best.f.title)}, ${best.d.toFixed(1)}° away)` : ""}. Anyone can add it with one command from our open pipeline: <code>python pipeline/make_field.py --ra ${ra.toFixed(5)} --dec ${dec.toFixed(5)} --name myfield</code>`;
}

function bindUI() {
  $("#coordForm").addEventListener("submit", e => { e.preventDefault(); goCoords($("#raIn").value, $("#decIn").value); });
  $$("#modeSeg button").forEach(b => b.addEventListener("click", () => { if (b.disabled) return; S.mode = b.dataset.mode; if (S.mode !== "blink" && S.mode !== "timeline") stop(); syncButtons(); draw(); }));
  $$("#dataSeg button").forEach(b => b.addEventListener("click", () => { if (b.disabled) return; S.data = b.dataset.data; if (S.data === "chan" && S.mode === "sum") S.mode = "blink"; resetDates(); }));
  $("#selA").addEventListener("change", e => { S.a = +e.target.value; syncButtons(); draw(); });
  $("#selB").addEventListener("change", e => { S.b = +e.target.value; syncButtons(); draw(); });
  $("#tSlider").addEventListener("input", e => { S.t = +e.target.value; if (S.mode !== "timeline") { S.mode = "timeline"; syncButtons(); } draw(); updateURL(); });
  $("#playBtn").addEventListener("click", () => { S.playing ? (stop(), syncButtons()) : play(); });
  $("#speed").addEventListener("input", e => { S.speed = Math.min(2.5, +e.target.value); $("#speedVal").textContent = S.speed; if (S.playing) play(); });
  $("#ovTarget").addEventListener("change", e => { S.ovTarget = e.target.checked; draw(); });
  $("#ovGaia").addEventListener("change", e => { S.ovGaia = e.target.checked; draw(); });
  $("#ovFlags").addEventListener("change", e => { S.ovFlags = e.target.checked; draw(); });
  $("#rawDiff").addEventListener("change", e => { S.rawDiff = e.target.checked; syncButtons(); draw(); });
  $("#wiseOn").addEventListener("change", e => { S.wiseOn = e.target.checked; resetDates(); });
  $("#gameBtn").addEventListener("click", startGame);
  $("#pxOn").addEventListener("change", e => { S.px = e.target.checked; $("#pxPanel").open = true; syncButtons(); pxInfo(); draw(); });
  $("#pxDist").addEventListener("input", e => { S.pxD = Math.round(100 * Math.pow(10, +e.target.value)); $("#pxDistVal").textContent = S.pxD; pxInfo(); draw(); });
  const cv = $("#cv");
  cv.addEventListener("click", e => {
    if (!S.game || S.game.revealed) return;
    const r = cv.getBoundingClientRect(), n = S.field.grid_px;
    gameTap((e.clientX - r.left) / r.width * n, (e.clientY - r.top) / r.height * n);
  });
  // swipe handle drag
  const stage = $("#stage"), h = $("#swipeHandle");
  const move = e => { const r = stage.getBoundingClientRect(); S.swipeX = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)); draw(); };
  h.addEventListener("pointerdown", e => { h.setPointerCapture(e.pointerId); h.onpointermove = move; });
  h.addEventListener("pointerup", () => { h.onpointermove = null; });
  stage.addEventListener("pointerdown", e => { if (S.mode === "swipe" && e.target === cv && !S.game) { move(e); } });
  document.addEventListener("keydown", e => {
    if (!S.field || ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
    if (e.code === "Space") { e.preventDefault(); S.playing ? (stop(), syncButtons()) : play(); }
    if (e.code === "ArrowRight" || e.code === "ArrowLeft") {
      e.preventDefault(); const n = seq().length, d = e.code === "ArrowRight" ? 1 : -1;
      if (S.mode === "blink") S.phase ^= 1; else { S.mode = "timeline"; S.t = (S.t + d + n) % n; $("#tSlider").value = S.t; syncButtons(); }
      draw();
    }
  });
}
function pxInfo() {
  const P = S.field && S.field.planetx;
  if (!S.px || !P) { $("#pxInfo").textContent = P ? "" : "Not available for this field."; return; }
  const items = seq(); const a = pxPos(items[0].epoch), b = pxPos(items[items.length - 1].epoch);
  const sh = a && b ? Math.hypot(b[0] - a[0], b[1] - a[1]) * S.field.pixel_scale_arcsec : 0;
  let mx = 0; for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) { const p = pxPos(items[i].epoch), q = pxPos(items[j].epoch); if (p && q) mx = Math.max(mx, Math.hypot(p[0] - q[0], p[1] - q[1])); }
  const mxa = mx * S.field.pixel_scale_arcsec;
  $("#pxInfo").textContent = `At ${S.pxD} AU the simulated planet's largest jump between two visits here is ${(mxa / 60).toFixed(1)} arcminutes (${mx.toFixed(0)} pixels), mostly parallax from Earth being on a different side of the Sun; first to last visit: ${(sh / 60).toFixed(1)} arcminutes. ${mx > S.field.grid_px * 0.8 ? "That is bigger than this whole field, which is why searches for distant planets need wide fields of view. " : ""}Model: ${P.model}. A real Planet X would be far fainter than this dot.`;
}

init();
