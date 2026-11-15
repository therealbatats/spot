// SPOT: more React Bits effects, ported to plain JavaScript (the site has no React or build step), plus GSAP ScrollTrigger
// scroll motion synced with Lenis. Ported components: StarBorder, SpotlightCard, CircularText, DecryptedText, by David Haz
// (https://reactbits.dev), used under the React Bits license (MIT + Commons Clause, see vendor/REACTBITS_LICENSE.md):
// "Copyright (c) 2026 David Haz ... use ... as part of an application, website, or product."
// Decoration only: nothing here draws over, fades or moves the sky images. Off under prefers-reduced-motion.
// Written with AI assistance under the direction of Ali (team AITHMAC).
"use strict";
(function () {
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const capture = /[?&]capture=/.test(location.search);
  const coarse = window.matchMedia && matchMedia("(pointer: coarse)").matches;
  if (reduce || capture) return;
  const gs = window.gsap;

  /* ---------- StarBorder: a light orbiting the primary buttons (CSS-driven) ---------- */
  document.querySelectorAll(".btn.primary").forEach(b => b.classList.add("star-border"));

  /* ---------- SpotlightCard: glow follows the pointer inside panels and cards ---------- */
  const spots = () => document.querySelectorAll(".controls .group, .card, .note, .coords");
  function wireSpots() { spots().forEach(el => { if (el.dataset.spot) return; el.dataset.spot = "1"; el.classList.add("spotlight"); }); }
  wireSpots();
  const cards = document.getElementById("cards"); if (cards) new MutationObserver(wireSpots).observe(cards, { childList: true });
  if (!coarse) addEventListener("pointermove", e => {
    const el = e.target.closest && e.target.closest(".spotlight"); if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--sx", (e.clientX - r.left) + "px"); el.style.setProperty("--sy", (e.clientY - r.top) + "px");
  }, { passive: true });

  /* ---------- CircularText: rotating ring of text around the 3D globe ---------- */
  const globe = document.getElementById("globe");
  if (globe) {
    const wrap = document.createElement("div"); wrap.className = "globewrap"; globe.parentNode.insertBefore(wrap, globe); wrap.appendChild(globe);
    const ring = document.createElement("div"); ring.className = "circtext"; ring.setAttribute("aria-hidden", "true");
    const text = "SPHEREx · 102 COLOURS OF INFRARED · THE WHOLE SKY EVERY SIX MONTHS · ";
    [...text].forEach((ch, i, a) => { const s = document.createElement("span"); s.textContent = ch; s.style.transform = `rotate(${(360 / a.length) * i}deg)`; ring.appendChild(s); });
    wrap.appendChild(ring);
    let spin = 0, boost = 0;
    gs.ticker.add((_, dt) => { spin += (6 + boost) * dt / 1000; boost *= 0.94; ring.style.transform = `translate(-50%, -50%) rotate(${spin}deg)`; });
    if (window.ScrollTrigger) ScrollTrigger.create({ trigger: wrap, start: "top bottom", end: "bottom top", onUpdate: s => { boost = Math.min(120, Math.abs(s.getVelocity()) / 12); } });
  }

  /* ---------- DecryptedText: the hero tagline resolves out of random characters ---------- */
  const tag = document.querySelector(".heroText p");
  if (tag) {
    const final = tag.textContent, chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789*+<>/\\";
    tag.setAttribute("aria-label", final);
    const run = () => {
      let frame = 0; const total = 28;
      const id = setInterval(() => {
        frame++;
        tag.textContent = [...final].map((c, i) => (c === " " || i < (frame / total) * final.length) ? c : chars[Math.floor(Math.random() * chars.length)]).join("");
        if (frame >= total) { clearInterval(id); tag.textContent = final; }
      }, 40);
    };
    run(); tag.parentElement.addEventListener("pointerenter", run);
  }

  /* ---------- ScrollTrigger + Lenis ---------- */
  if (window.ScrollTrigger && gs) {
    gs.registerPlugin(ScrollTrigger);
    const lenis = window.SpotMotion && SpotMotion.lenis;
    if (lenis) lenis.on("scroll", ScrollTrigger.update);
    // hero text drifts up and fades as you scroll past (the sky image itself is not changed)
    gs.to(".heroText", { yPercent: -60, opacity: 0, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });
    // target cards rise in, staggered
    const batchCards = () => {
      const cs = document.querySelectorAll("#cards .card:not([data-st])"); if (!cs.length) return;
      cs.forEach(c => c.dataset.st = "1");
      gs.set(cs, { opacity: 0, y: 30 });
      ScrollTrigger.batch(cs, { start: "top 92%", onEnter: b => gs.to(b, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out", stagger: 0.08, overwrite: true, clearProps: "opacity,transform" }) });
      setTimeout(() => cs.forEach(c => { if (getComputedStyle(c).opacity === "0") gs.set(c, { clearProps: "opacity,transform" }); }), 4000); // never leave a card hidden
      ScrollTrigger.refresh();
    };
    batchCards(); if (cards) new MutationObserver(batchCards).observe(cards, { childList: true });
    // smooth glide for in-page links
    document.addEventListener("click", e => {
      const a = e.target.closest('a[href^="#"]'); if (!a || !lenis) return;
      const t = document.querySelector(a.getAttribute("href")); if (!t || t.hidden) return;
      e.preventDefault(); const off = innerWidth > 600 ? -80 : -12; lenis.scrollTo(t, { offset: off, duration: 1.2 }); setTimeout(() => { if (Math.abs(t.getBoundingClientRect().top + off) > 40) t.scrollIntoView(); }, 1600); history.replaceState(null, "", location.search + a.getAttribute("href"));
    });
  }
})();
