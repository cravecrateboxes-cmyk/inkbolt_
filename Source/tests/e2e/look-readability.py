"""Robot readability from two shots (look-readability.js): python3 look-readability.py empty.png bot.png
Robot pixels: where the shots differ by more than 6/255 (largest connected blob near the centre, the HUD excluded by
ignoring the outer 12% border). Ring: 16 px around the robot (dilation minus the robot). Prints JSON:
{ px: robot pixel count, robot: mean luminance, ring: mean luminance, diff: |robot - ring| }."""
import json
import sys

import numpy as np
from PIL import Image


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def dilate(m, r):
    out = m.copy()
    ys, xs = np.nonzero(m)
    if not len(ys):
        return out
    H, W = m.shape
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy ** 2 + xx ** 2) <= r * r
    # separable approximation is enough here: box then disk test via distance transform-free loop on the bbox
    y0, y1, x0, x1 = max(0, ys.min() - r), min(H, ys.max() + r + 1), max(0, xs.min() - r), min(W, xs.max() + r + 1)
    sub = m[y0:y1, x0:x1]
    acc = np.zeros_like(sub)
    for dy, dx in zip(yy[disk], xx[disk]):
        sh = np.roll(np.roll(sub, dy, 0), dx, 1)
        acc |= sh
    out[y0:y1, x0:x1] = acc
    return out


def main(a, b):
    A = np.asarray(Image.open(a).convert('RGB')).astype(float) / 255
    B = np.asarray(Image.open(b).convert('RGB')).astype(float) / 255
    H, W = A.shape[:2]
    d = np.abs(A - B).max(axis=2) > 6 / 255
    by, bx = int(H * 0.12), int(W * 0.12)
    keep = np.zeros_like(d)
    keep[by:H - by, bx:W - bx] = True
    d &= keep
    if d.sum() < 4:
        print(json.dumps({'px': int(d.sum()), 'robot': None, 'ring': None, 'diff': 0}))
        return
    ring = dilate(d, 16) & ~d
    LB = lum(B)
    r, g = float(LB[d].mean()), float(LB[ring].mean())
    print(json.dumps({'px': int(d.sum()), 'robot': round(r, 4), 'ring': round(g, 4), 'diff': round(abs(r - g), 4)}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
