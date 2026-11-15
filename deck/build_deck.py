# Fill deck.html placeholders and print to PDF with headless Chrome.
# Written with AI assistance under the direction of Ali (team AITHMAC).
import subprocess, sys
from pathlib import Path
here = Path(__file__).parent
live, repo = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("(live link added at deploy)", "(repository link added at deploy)")
rows = """
<tr><td>Barnard's Star</td><td>Moves <strong>1.69 px north</strong> in a year (predicted 1.67 px = 10.2″); measured within 0.07–0.44 px of Gaia's prediction on every date and band.</td></tr>
<tr><td>Epsilon Indi B</td><td>Brown-dwarf pair shines at 4 µm; moves ~1 px south-east in 1.4 years, within ~0.1 px of prediction.</td></tr>
<tr><td>WISE 0855−0714</td><td>Near SPHEREx's limit: at 3.8–4.4 µm a faint dot shifts west 1.28 px/yr (predicted 1.35) beside a fixed background star. <em>Consistent with</em> a detection; not proven.</td></tr>
<tr><td>R Draconis</td><td>Saturated; measured from its outer glow: brightness swings by ~2–2.7× over months, smoothly — a pulsating giant.</td></tr>
<tr><td>RW Aurigae</td><td>Infrared glow (2.4–5 µm) fell ~1.7–1.9× from Sept 2025 to Sept 2026 in three bands; shorter wavelengths within noise.</td></tr>
<tr><td>M101 (control)</td><td>Nothing changes: differences at noise level; galaxy brightness steady to 2–6%.</td></tr>"""
h = (here / "deck.html").read_text()
h = h.replace("LIVE_URL", live).replace("REPO_URL", repo)
(here / "deck_filled.html").write_text(h)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={here / 'SPOT_deck.pdf'}",
                "--virtual-time-budget=3000", (here / "deck_filled.html").as_uri()], check=True, capture_output=True)
print("wrote", here / "SPOT_deck.pdf")
