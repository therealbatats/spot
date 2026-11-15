// SPOT hero: real images of Barnard's Star, WISE 2010 and SPHEREx 2026, blinking once per second.
// The O of SPOT is the ring around the star's 2010 position; in 2026 the star has left it.
// Written with AI assistance under the direction of Ali (team AITHMAC).
"use strict";
(async function () {
  const cv = document.getElementById("heroCv"), btn = document.getElementById("heroPlay");
  if (!cv) return;
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  let f;
  try { f = await (await fetch("data/fields/barnard/field.json")).json(); } catch (e) { cv.parentElement.hidden = true; return; }
  const b6 = f.bands.find(b => b.detector === 6);
  if (!f.wise || !b6) { cv.parentElement.hidden = true; return; }
  const last = b6.epochs[b6.epochs.length - 1];
  const load = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
  const [imW, imS] = await Promise.all([load("data/fields/barnard/" + f.wise.png), load("data/fields/barnard/" + last.png)]);
  document.getElementById("heroCap").textContent =
    `Real data: Barnard's Star. WISE ${f.wise.utc_range[0]} to ${f.wise.utc_range[1]} (4.6 µm) and SPHEREx ${last.utc_first.slice(0, 10)} (${last.wl_min_um}–${last.wl_max_um} µm). Tap to open.`;
  const pW = f.wise.meas_xy || f.wise.pred_xy, pS = last.meas_xy || last.pred_xy;
  let phase = 0, playing = !reduce, timer = null;
  function draw() {
    const ctx = cv.getContext("2d"), W = cv.clientWidth * devicePixelRatio, H = cv.clientHeight * devicePixelRatio;
    cv.width = W; cv.height = H;
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
    // crop: grid region around both positions, filling the hero
    // frame so the 2026 position sits near the top and the 2010 position (the O) about 60% down
    const dy = Math.abs(pW[1] - pS[1]) + 0.01, hgrid = dy / 0.42, s = H / hgrid, wgrid = W / s;
    const sx = (pW[0] + pS[0]) / 2 + 0.5 - wgrid / 2, sy = Math.min(pW[1], pS[1]) + 0.5 - 0.18 * hgrid;
    ctx.drawImage(phase ? imS : imW, sx, sy, wgrid, hgrid, 0, 0, W, H);
    // wordmark: S P (ring) T, the ring centred on the 2010 position
    const rx = (pW[0] + 0.5 - sx) * s, ry = (pW[1] + 0.5 - sy) * s, R = 0.075 * hgrid * s, lw = Math.max(3, R * 0.2);
    ctx.strokeStyle = "#E8EEF7"; ctx.lineWidth = lw; ctx.lineCap = "square"; ctx.shadowColor = "#000"; ctx.shadowBlur = 6;
    ctx.beginPath(); ctx.arc(rx, ry, R, 0, 2 * Math.PI); ctx.stroke();
    const cap = 2 * R, gap = R * 0.55, Lw = cap * 0.62;
    const xP = rx - R - gap - Lw, xS = xP - gap - Lw, xT = rx + R + gap, top = ry - R, bot = ry + R, mid = ry;
    ctx.beginPath(); // S
    ctx.moveTo(xS + Lw, top); ctx.lineTo(xS, top); ctx.lineTo(xS, mid); ctx.lineTo(xS + Lw, mid); ctx.lineTo(xS + Lw, bot); ctx.lineTo(xS, bot);
    ctx.moveTo(xP, bot); ctx.lineTo(xP, top); ctx.lineTo(xP + Lw, top); ctx.lineTo(xP + Lw, mid); ctx.lineTo(xP, mid); // P
    ctx.moveTo(xT, top); ctx.lineTo(xT + Lw * 1.1, top); ctx.moveTo(xT + Lw * 0.55, top); ctx.lineTo(xT + Lw * 0.55, bot); // T
    ctx.stroke(); ctx.shadowBlur = 0;
    ctx.fillStyle = "#E8EEF7"; ctx.font = `600 ${Math.max(13, 0.022 * W)}px Plex, system-ui`;
    ctx.fillText(phase ? "SPHEREx " + last.utc_first.slice(0, 4) : "WISE " + f.wise.utc.slice(0, 4), 16, 16 + Math.max(13, 0.022 * W));
  }
  function tick() { phase ^= 1; draw(); }
  function setPlay(p) { playing = p; clearInterval(timer); timer = p ? setInterval(tick, 1000) : null; btn.textContent = p ? "Pause" : "Play"; }
  btn.addEventListener("click", e => { e.stopPropagation(); setPlay(!playing); });
  cv.addEventListener("click", () => { if (window.openField) { openField("barnard"); } });
  window.addEventListener("resize", draw);
  draw(); setPlay(playing);
})();
