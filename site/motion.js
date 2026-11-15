// SPOT motion: light use of GSAP (self-hosted) and Lenis (landing page scrolling only).
// Rules: the blink between sky images is always a hard cut; nothing moves under prefers-reduced-motion.
// Written with AI assistance under the direction of Ali (team AITHMAC).
"use strict";
(function () {
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const gs = !reduce && window.gsap ? window.gsap : null;
  const M = { ok: !!gs };

  // A copy of the clicked thumbnail flies to the stage, then disappears at once (no cross-fade over sky data).
  M.fly = function (img, target) {
    if (!gs || !img || !target) return;
    const a = img.getBoundingClientRect(), sx = scrollX, sy = scrollY;
    const c = img.cloneNode(); c.alt = ""; c.setAttribute("aria-hidden", "true");
    Object.assign(c.style, { position: "absolute", left: a.left + sx + "px", top: a.top + sy + "px", width: a.width + "px", height: a.height + "px",
      margin: 0, zIndex: 50, pointerEvents: "none", imageRendering: "pixelated", border: "1px solid rgba(255,255,255,.3)" });
    document.body.appendChild(c);
    requestAnimationFrame(() => {
      const b = target.getBoundingClientRect();
      gs.to(c, { left: b.left + sx, top: b.top + sy, width: b.width, height: b.height, duration: 0.6, ease: "power3.inOut", onComplete: () => c.remove() });
    });
  };

  // Chart points appear in date order (data-mjd on each point).
  M.inOrder = function (svg) {
    if (!gs || !svg) return;
    const pts = [...svg.querySelectorAll("[data-mjd]")].sort((p, q) => p.dataset.mjd - q.dataset.mjd);
    if (pts.length) gs.from(pts, { opacity: 0, duration: 0.25, stagger: Math.min(0.02, 1.2 / pts.length), ease: "none" });
  };

  // Lenis smooth scrolling: landing page only; off on touch, under reduced motion, and inside the viewer.
  if (!reduce && window.Lenis && !(window.matchMedia && matchMedia("(pointer: coarse)").matches)) {
    const v = document.getElementById("viewer"); if (v) v.setAttribute("data-lenis-prevent", "");
    try {
      const lenis = new Lenis({ duration: 1.0 });
      const raf = t => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf);
      M.lenis = lenis;
    } catch (e) { /* keep native scrolling */ }
  }
  window.SpotMotion = M;
})();
