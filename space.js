// SPOT space theme: decorative starfield with parallax and shooting stars, orbit cursor, heading reveals,
// scroll progress, tab-panel transitions. Decoration only: it sits behind the content and never touches the sky images.
// Static (no motion) under prefers-reduced-motion. Written with AI assistance under the direction of Ali (team AITHMAC).
"use strict";
(function () {
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const capture = /[?&]capture=/.test(location.search);
  const coarse = window.matchMedia && matchMedia("(pointer: coarse)").matches;
  const gs = !reduce && !capture && window.gsap ? window.gsap : null;

  /* ---------- starfield (decorative, behind everything) ---------- */
  const cv = document.createElement("canvas");
  cv.className = "starfield"; cv.setAttribute("aria-hidden", "true");
  document.body.prepend(cv);
  const ctx = cv.getContext("2d");
  let W = 0, H = 0, dpr = 1, stars = [], shots = [], last = 0;
  function build() {
    dpr = Math.min(2, devicePixelRatio || 1); W = innerWidth; H = innerHeight;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round(W * H / 2600);
    stars = Array.from({ length: n }, () => {
      const layer = Math.random() < 0.7 ? 0 : Math.random() < 0.75 ? 1 : 2;
      return { x: Math.random() * W, y: Math.random() * H * 3, r: [0.5, 0.9, 1.4][layer], depth: [0.05, 0.12, 0.25][layer],
        tw: Math.random() * Math.PI * 2, sp: 0.6 + Math.random() * 1.6, flame: Math.random() < 0.04 };
    });
  }
  function frame(t) {
    const dt = Math.min(0.05, (t - (last || t)) / 1000); last = t;
    ctx.clearRect(0, 0, W, H);
    const sy = scrollY;
    for (const s of stars) {
      const y = ((s.y - sy * s.depth) % (H * 3) + H * 3) % (H * 3);
      if (y > H) continue;
      const a = reduce ? 0.7 : 0.45 + 0.55 * (0.5 + 0.5 * Math.sin(s.tw + t / 1000 * s.sp));
      ctx.globalAlpha = a; ctx.fillStyle = s.flame ? "#FE5101" : "#FFFFFF";
      ctx.beginPath(); ctx.arc(s.x, y, s.r, 0, 6.2832); ctx.fill();
    }
    if (!reduce) {
      if (Math.random() < dt * 0.12 && shots.length < 2) {
        const ang = 0.35 + Math.random() * 0.35;
        shots.push({ x: Math.random() * W * 0.8, y: Math.random() * H * 0.4, vx: Math.cos(ang) * 900, vy: Math.sin(ang) * 900, life: 0 });
      }
      for (let i = shots.length - 1; i >= 0; i--) {
        const s = shots[i]; s.life += dt; s.x += s.vx * dt; s.y += s.vy * dt;
        if (s.life > 0.9) { shots.splice(i, 1); continue; }
        const k = 1 - s.life / 0.9, g = ctx.createLinearGradient(s.x, s.y, s.x - s.vx * 0.12, s.y - s.vy * 0.12);
        g.addColorStop(0, "rgba(255,255,255," + k + ")"); g.addColorStop(0.3, "rgba(254,81,1," + 0.6 * k + ")"); g.addColorStop(1, "rgba(254,81,1,0)");
        ctx.globalAlpha = 1; ctx.strokeStyle = g; ctx.lineWidth = 1.6; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x - s.vx * 0.12, s.y - s.vy * 0.12); ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
    if (!reduce) requestAnimationFrame(frame);
  }
  build(); addEventListener("resize", () => { build(); if (reduce) frame(0); });
  if (reduce) { frame(0); addEventListener("scroll", () => frame(0), { passive: true }); } else requestAnimationFrame(frame);

  /* ---------- scroll progress bar ---------- */
  const bar = document.createElement("div"); bar.className = "scrollbar"; bar.setAttribute("aria-hidden", "true"); document.body.appendChild(bar);
  const setBar = () => { const h = document.documentElement.scrollHeight - innerHeight; bar.style.transform = `scaleX(${h > 0 ? scrollY / h : 0})`; };
  addEventListener("scroll", setBar, { passive: true }); setBar();

  if (!gs) return;

  /* ---------- heading reveals: words rise in ---------- */
  const heads = [...document.querySelectorAll("main h2:not(#viewerTitle)")];
  heads.forEach(h => {
    if (h.querySelector(".w")) return;
    h.innerHTML = h.textContent.split(/(\s+)/).map(w => /\s+/.test(w) ? w : `<span class="w"><span>${w}</span></span>`).join("");
  });
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return; io.unobserve(e.target);
    gs.from(e.target.querySelectorAll(".w > span"), { yPercent: 110, opacity: 0, duration: 0.8, ease: "power4.out", stagger: 0.06 });
    const sp = e.target.querySelectorAll(".w > span"); setTimeout(() => gs.set(sp, { clearProps: "all" }), 2500); // never leave a heading hidden
  }), { rootMargin: "0px 0px -8% 0px" });
  heads.forEach(h => io.observe(h));

  /* ---------- tab panels and viewer title animate in ---------- */
  document.addEventListener("click", e => {
    const t = e.target.closest(".tabs button"); if (!t) return;
    requestAnimationFrame(() => { const p = document.getElementById(t.dataset.tab); if (p) gs.from(p, { opacity: 0, y: 14, duration: 0.45, ease: "power3.out", clearProps: "all" }); });
  });
  const vt = document.getElementById("viewerTitle");
  if (vt) new MutationObserver(() => gs.fromTo(vt, { opacity: 0, x: -16 }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out", clearProps: "all" })).observe(vt, { childList: true, characterData: true, subtree: true });

  /* ---------- orbit cursor (mouse only) ---------- */
  if (coarse) return;
  const dot = document.createElement("div"), ring = document.createElement("div");
  dot.className = "cur-dot"; ring.className = "cur-ring"; dot.setAttribute("aria-hidden", "true"); ring.setAttribute("aria-hidden", "true");
  document.body.append(ring, dot);
  const dx = gs.quickTo(dot, "x", { duration: 0.08, ease: "power3" }), dy = gs.quickTo(dot, "y", { duration: 0.08, ease: "power3" });
  const rx = gs.quickTo(ring, "x", { duration: 0.45, ease: "power3" }), ry = gs.quickTo(ring, "y", { duration: 0.45, ease: "power3" });
  addEventListener("pointermove", e => {
    if (e.pointerType !== "mouse") return;
    dx(e.clientX); dy(e.clientY); rx(e.clientX); ry(e.clientY);
    const over = e.target.closest("#cv, .stage, input, select");
    const hot = !over && e.target.closest("button, a, .card, summary, #globe, label.chk");
    document.documentElement.classList.toggle("cur-hide", !!over);
    ring.classList.toggle("hot", !!hot);
  }, { passive: true });
  document.documentElement.classList.add("cur-on");
  addEventListener("pointerdown", () => gs.fromTo(ring, { scale: 0.6 }, { scale: 1, duration: 0.4, ease: "back.out(3)" }));
})();
