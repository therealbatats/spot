// SPOT interface effects: 3D sky globe (real target coordinates), click sparks, magnetic buttons, 3D card tilt, section reveals.
// ClickSpark and Magnet are plain-JavaScript ports of React Bits components by David Haz (https://reactbits.dev),
// used under the React Bits license (MIT + Commons Clause): "Copyright (c) 2026 David Haz. Permission is hereby granted,
// free of charge, ... to use, copy, modify, merge, publish, and distribute the Software as part of an application, website,
// or product ... You may not sell, sublicense, or redistribute the components themselves." Full text: vendor/REACTBITS_LICENSE.md
// Everything here is decoration: no sky image is ever animated or blended. Off under prefers-reduced-motion.
// Written with AI assistance under the direction of Ali (team AITHMAC).
"use strict";
(function () {
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const coarse = window.matchMedia && matchMedia("(pointer: coarse)").matches;
  const FLAME = "#FE5101", WHITE = "#FFFFFF";

  /* ---------- 3D sky globe ---------- */
  const cv = document.getElementById("globe");
  if (cv) (async function () {
    let man;
    try { man = await (await fetch("data/manifest.json", { cache: "no-cache" })).json(); } catch (e) { cv.closest("section").hidden = true; return; }
    const pts = man.fields.map(f => ({ id: f.id, name: f.title.split(" (")[0].replace(/ — .*/, ""), ra: f.ra_deg, dec: f.dec_deg }));
    const r = Math.PI / 180, vec = (ra, dec) => [Math.cos(dec * r) * Math.cos(ra * r), Math.cos(dec * r) * Math.sin(ra * r), Math.sin(dec * r)];
    const eps = 23.439 * r, ecl = []; // ecliptic (beta = 0) in equatorial coordinates
    for (let l = 0; l <= 360; l += 4) { const L = l * r; ecl.push([Math.cos(L), Math.sin(L) * Math.cos(eps), Math.sin(L) * Math.sin(eps)]); }
    let yaw = -1.2, pitch = 0.35, vyaw = reduce ? 0 : 0.0016, drag = null, hover = null, W = 0, H = 0, R = 0, dpr = 1, proj = [];
    const ctx = cv.getContext("2d");
    function size() { dpr = devicePixelRatio || 1; W = cv.clientWidth; H = cv.clientHeight; cv.width = W * dpr; cv.height = H * dpr; R = Math.min(W, H) * 0.42; }
    function P(v) { // rotate (yaw about z, pitch about x) then perspective
      const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      const x1 = v[0] * cy - v[1] * sy, y1 = v[0] * sy + v[1] * cy, z1 = v[2];
      const y2 = y1 * cp - z1 * sp, z2 = y1 * sp + z1 * cp; // y2 = depth (towards viewer is negative)
      const k = 3.2 / (3.2 + y2);
      return [W / 2 + x1 * R * k, H / 2 - z2 * R * k, y2];
    }
    function line(vs, col, width, dash) {
      ctx.lineWidth = width; ctx.setLineDash(dash || []);
      for (let i = 1; i < vs.length; i++) {
        const a = P(vs[i - 1]), b = P(vs[i]), front = (a[2] + b[2]) / 2 < 0;
        ctx.strokeStyle = col.replace("A", front ? "1" : "0.25"); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      }
      ctx.setLineDash([]);
    }
    function draw() {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
      const g = ctx.createRadialGradient(W / 2 - R * 0.3, H / 2 - R * 0.3, R * 0.1, W / 2, H / 2, R * 1.05);
      g.addColorStop(0, "rgba(255,255,255,0.10)"); g.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(W / 2, H / 2, R * 1.02, 0, 2 * Math.PI); ctx.fill();
      for (let d = -60; d <= 60; d += 30) { const v = []; for (let a = 0; a <= 360; a += 6) v.push(vec(a, d)); line(v, "rgba(255,255,255,A)", d === 0 ? 1.2 : 0.5); }
      for (let a = 0; a < 360; a += 30) { const v = []; for (let d = -90; d <= 90; d += 6) v.push(vec(a, d)); line(v, "rgba(255,255,255,A)", 0.5); }
      ctx.globalAlpha = 0.7; line(ecl, "rgba(254,81,1,A)", 1, [5, 5]); ctx.globalAlpha = 1;
      proj = pts.map(p => { const q = P(vec(p.ra, p.dec)); return { p, x: q[0], y: q[1], z: q[2] }; }).sort((a, b) => b.z - a.z);
      ctx.font = "600 13px Plex, system-ui";
      for (const q of proj) {
        const front = q.z < 0, on = hover === q.p.id, rad = (on ? 7 : 5) * (front ? 1 : 0.7);
        ctx.globalAlpha = front ? 1 : 0.3;
        ctx.fillStyle = FLAME; ctx.beginPath(); ctx.arc(q.x, q.y, rad, 0, 2 * Math.PI); ctx.fill();
        if (on) { ctx.strokeStyle = WHITE; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(q.x, q.y, rad + 5, 0, 2 * Math.PI); ctx.stroke(); }
        if (front) { ctx.fillStyle = WHITE; ctx.shadowColor = "#000000"; ctx.shadowBlur = 4; ctx.fillText(q.p.name, q.x + 10, q.y + 4); ctx.shadowBlur = 0; }
        ctx.globalAlpha = 1;
      }
    }
    function pick(e) {
      const b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top;
      let best = null, bd = 22;
      for (const q of proj) { if (q.z >= 0) continue; const d = Math.hypot(q.x - x, q.y - y); if (d < bd) { bd = d; best = q.p; } }
      return best;
    }
    cv.addEventListener("pointerdown", e => { drag = { x: e.clientX, y: e.clientY, yaw, pitch, moved: 0 }; cv.setPointerCapture(e.pointerId); });
    cv.addEventListener("pointermove", e => {
      if (drag) { const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.moved = Math.max(drag.moved, Math.hypot(dx, dy));
        yaw = drag.yaw - dx * 0.008; pitch = Math.max(-1.3, Math.min(1.3, drag.pitch + dy * 0.008)); if (reduce) draw(); }
      else { const h = pick(e); if ((h && h.id) !== hover) { hover = h && h.id; cv.style.cursor = h ? "pointer" : "grab"; if (reduce) draw(); } }
    });
    cv.addEventListener("pointerup", e => { const d = drag; drag = null; if (d && d.moved < 6) { const h = pick(e); if (h && window.openField) openField(h.id); } });
    cv.addEventListener("keydown", e => { if (e.key === "ArrowLeft") yaw += 0.15; if (e.key === "ArrowRight") yaw -= 0.15; draw(); });
    window.addEventListener("resize", () => { size(); draw(); });
    size(); draw();
    if (!reduce) { let vis = true; new IntersectionObserver(es => { vis = es[0].isIntersecting; }).observe(cv);
      (function loop() { if (vis && !drag) { yaw += vyaw; draw(); } requestAnimationFrame(loop); })(); }
  })();

  if (reduce) return;

  /* ---------- ClickSpark (port) ---------- */
  const sc = document.createElement("canvas"); sc.setAttribute("aria-hidden", "true");
  Object.assign(sc.style, { position: "fixed", inset: "0", width: "100vw", height: "100vh", pointerEvents: "none", zIndex: 60 });
  document.body.appendChild(sc);
  const sx = sc.getContext("2d"), bursts = [];
  const ease = t => 1 - Math.pow(1 - t, 3);
  function fit() { const d = devicePixelRatio || 1; sc.width = innerWidth * d; sc.height = innerHeight * d; sx.setTransform(d, 0, 0, d, 0, 0); }
  fit(); addEventListener("resize", fit);
  let running = false;
  function frame(now) {
    sx.clearRect(0, 0, innerWidth, innerHeight);
    for (let i = bursts.length - 1; i >= 0; i--) {
      const b = bursts[i], p = (now - b.t) / 500;
      if (p >= 1) { bursts.splice(i, 1); continue; }
      const e = ease(p), dist = 30 * e, len = 14 * (1 - e);
      sx.lineWidth = 2; sx.lineCap = "round";
      b.sparks.forEach((a, k) => {
        sx.strokeStyle = k % 2 ? WHITE : FLAME; sx.globalAlpha = 1 - p;
        sx.beginPath(); sx.moveTo(b.x + Math.cos(a) * dist, b.y + Math.sin(a) * dist);
        sx.lineTo(b.x + Math.cos(a) * (dist + len), b.y + Math.sin(a) * (dist + len)); sx.stroke();
      });
    }
    sx.globalAlpha = 1;
    if (bursts.length) requestAnimationFrame(frame); else running = false;
  }
  document.addEventListener("pointerdown", e => {
    if (!e.target.closest("button, a, .card, summary, select, label.chk, #globe")) return;
    const n = 8, off = Math.random() * Math.PI;
    bursts.push({ x: e.clientX, y: e.clientY, t: performance.now(), sparks: Array.from({ length: n }, (_, i) => off + i * 2 * Math.PI / n) });
    if (bursts.length > 32) bursts.shift();
    if (!running) { running = true; requestAnimationFrame(frame); }
  }, { passive: true });

  if (coarse) return; // magnet and tilt need a mouse

  /* ---------- Magnet (port): spring pull towards the pointer ---------- */
  function magnet(el, { padding = 40, strength = 3, tilt = 0 } = {}) {
    const cur = { x: 0, y: 0, rx: 0, ry: 0 }, vel = { x: 0, y: 0, rx: 0, ry: 0 }, tgt = { x: 0, y: 0, rx: 0, ry: 0 };
    let raf = 0, last = 0;
    function step(t) {
      const dt = Math.min(0.032, (t - (last || t)) / 1000) || 0.016; last = t; let rest = true;
      for (const k in cur) { const f = 170 * (tgt[k] - cur[k]) - 16 * vel[k]; vel[k] += f * dt; cur[k] += vel[k] * dt;
        if (Math.abs(tgt[k] - cur[k]) > 0.05 || Math.abs(vel[k]) > 0.05) rest = false; }
      el.style.transform = `perspective(700px) translate(${cur.x.toFixed(2)}px, ${cur.y.toFixed(2)}px) rotateX(${cur.rx.toFixed(2)}deg) rotateY(${cur.ry.toFixed(2)}deg)`;
      if (rest) { raf = 0; last = 0; if (!tgt.x && !tgt.y) el.style.transform = ""; } else raf = requestAnimationFrame(step);
    }
    function wake() { if (!raf) raf = requestAnimationFrame(step); }
    addEventListener("pointermove", e => {
      if (e.pointerType === "touch") return;
      const b = el.getBoundingClientRect(), dx = e.clientX - (b.left + b.width / 2), dy = e.clientY - (b.top + b.height / 2);
      const out = Math.hypot(Math.max(0, Math.abs(dx) - b.width / 2), Math.max(0, Math.abs(dy) - b.height / 2));
      const near = out <= padding && b.width > 0;
      const nx = near ? dx / strength : 0, ny = near ? dy / strength : 0;
      const rx = near && tilt ? -(dy / (b.height / 2)) * tilt : 0, ry = near && tilt ? (dx / (b.width / 2)) * tilt : 0;
      if (nx !== tgt.x || ny !== tgt.y || rx !== tgt.rx || ry !== tgt.ry) { Object.assign(tgt, { x: nx, y: ny, rx, ry }); wake(); }
    }, { passive: true });
  }
  document.querySelectorAll(".btn.primary, #examples button, .heroPlay").forEach(el => magnet(el, { padding: 30, strength: 4 }));
  const cardsBox = document.getElementById("cards");
  const tiltCards = () => cardsBox && cardsBox.querySelectorAll(".card:not([data-mag])").forEach(c => { c.dataset.mag = "1"; magnet(c, { padding: 0, strength: 18, tilt: 8 }); });
  if (cardsBox) { tiltCards(); new MutationObserver(tiltCards).observe(cardsBox, { childList: true }); }

  /* ---------- Section reveals (GSAP) ---------- */
  if (window.gsap && "IntersectionObserver" in window && !/[?&]capture=/.test(location.search)) {
    const els = [...document.querySelectorAll("main > section:not(.hero):not(#viewer), .foot")];
    els.forEach(el => { if (el.getBoundingClientRect().top > innerHeight) gsap.set(el, { opacity: 0, y: 24 }); });
    const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { io.unobserve(en.target);
      gsap.to(en.target, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out", clearProps: "transform,opacity" }); } }), { rootMargin: "0px 0px -10% 0px" });
    els.forEach(el => io.observe(el));
  }
})();
