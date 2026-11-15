# SPOT - validation check 4 (new): connected regions with |S| >= 5 in every significance difference.
# Written with AI assistance under the direction of Ali (team AITHMAC).
import json, sys, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
ROOT = Path(__file__).resolve().parent.parent
for fid in (sys.argv[1:] or ['m101', 'barnard', 'rwaur', 'epsindb', 'wise0855', 'rdra']):
    f = json.loads((ROOT / f'site/data/fields/{fid}/field.json').read_text())
    rows, tot, tgt = [], 0, 0
    for b in f['bands']:
        for d in b['diffs']:
            im = np.array(Image.open(ROOT / f"site/data/fields/{fid}/{d['sig_png']}"))
            S = (im[..., 0].astype(float) / 255 - 0.5) * 10
            over = (np.abs(S) >= 4.95) & (im[..., 1] == 255)
            lab, n = ndimage.label(over)
            c = im.shape[0] // 2
            at = len(set(np.unique(lab[c - 4:c + 5, c - 4:c + 5])) - {0})
            tot += n - at; tgt += at
            rows.append(f"D{b['detector']} {d['a']}->{d['b']}: {n}" + (f" ({at} at target)" if at else ""))
    print(f"{fid}: regions |S|>=5 away from the target = {tot}; at the target = {tgt} | " + "; ".join(rows))
