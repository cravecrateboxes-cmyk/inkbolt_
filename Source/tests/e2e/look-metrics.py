#!/usr/bin/env python3
"""Look metrics (tactical look plan, Stage 0.4 / section 4.2).

    python3 look-metrics.py <dir> [--check] [--md]

For every PNG: centre crop (12-80% width, 10-74% height), luminance 0.2126 R + 0.7152 G + 0.0722 B, mean,
median, darkest 5% (5th percentile), share of pixels over 0.92 and under 0.06, mean HSV saturation.
The scene type comes from look-spots.json (per spot, else per plan). With --check, exits 1 when a shot is
outside its type's range. --md prints a markdown table (for PROGRESS.md).
"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
#            mean          median        p5            >0.92  <0.06
RANGES = {
    'ext-day':   ((0.32, 0.46), (0.25, 0.42), (0.04, 0.14), 0.04, 0.06),
    'ext-snow':  ((0.40, 0.55), (0.38, 0.56), (0.06, 0.18), 0.06, 0.04),
    'ext-dusk':  ((0.16, 0.32), (0.12, 0.28), (0.02, 0.08), 0.02, 0.20),
    'ext-night': ((0.16, 0.32), (0.12, 0.28), (0.02, 0.08), 0.02, 0.20),
    'int-lit':   ((0.26, 0.40), (0.22, 0.38), (0.04, 0.12), 0.03, 0.06),
    'int-ind':   ((0.20, 0.32), (0.16, 0.30), (0.03, 0.10), 0.02, 0.10),
    'int-dark':  ((0.15, 0.26), (0.12, 0.24), (0.02, 0.07), 0.02, 0.18),
}


def measure(path):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    h, w = im.shape[:2]
    c = im[int(h * 0.10):int(h * 0.74), int(w * 0.12):int(w * 0.80)]
    lum = c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722
    mx, mn = c.max(-1), c.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return {
        'mean': float(lum.mean()), 'median': float(np.median(lum)), 'p5': float(np.percentile(lum, 5)),
        'hi': float((lum > 0.92).mean()), 'lo': float((lum < 0.06).mean()), 'sat': float(sat.mean()),
    }


def type_of(name, spots):
    base = name[:-4]
    for plan, v in spots.items():
        if plan.startswith('_') or not base.startswith(plan + '-'):
            continue
        for s in v.get('spots', []) or []:
            if base == plan + '-' + s['name'] and s.get('type'):
                return s['type']
        zt = v.get('zoneTypes') or {}
        z = base[len(plan) + 1:].split('-')[0]
        if z.startswith('z') and z[1:] in zt:
            return zt[z[1:]]
        return v.get('type')
    return None


def check(m, t):
    if t not in RANGES:
        return []
    (a0, a1), (b0, b1), (c0, c1), hi, lo = RANGES[t]
    bad = []
    if not a0 <= m['mean'] <= a1: bad.append('mean')
    if not b0 <= m['median'] <= b1: bad.append('median')
    if not c0 <= m['p5'] <= c1: bad.append('p5')
    if m['hi'] > hi: bad.append('>0.92')
    if m['lo'] > lo: bad.append('<0.06')
    return bad


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    d = sys.argv[1]
    spots = json.load(open(os.path.join(HERE, 'look-spots.json')))
    rows, nbad = [], 0
    for n in sorted(os.listdir(d)):
        if not n.endswith('.png'):
            continue
        m = measure(os.path.join(d, n)); t = type_of(n, spots) or '?'
        bad = check(m, t); nbad += bool(bad)
        rows.append((n[:-4], t, m, bad))
    md = '--md' in sys.argv
    if md:
        print('| shot | type | mean | median | p5 | >0.92 | <0.06 | sat | out of range |')
        print('|---|---|---|---|---|---|---|---|---|')
    for n, t, m, bad in rows:
        if md:
            print('| %s | %s | %.3f | %.3f | %.3f | %.1f%% | %.1f%% | %.2f | %s |' % (n, t, m['mean'], m['median'], m['p5'], m['hi'] * 100, m['lo'] * 100, m['sat'], ', '.join(bad)))
        else:
            print('%-34s %-9s mean %.3f  med %.3f  p5 %.3f  >.92 %5.1f%%  <.06 %5.1f%%  sat %.2f  %s' % (n, t, m['mean'], m['median'], m['p5'], m['hi'] * 100, m['lo'] * 100, m['sat'], ('OUT: ' + ','.join(bad)) if bad else ''))
    if rows:
        a = np.array([[r[2]['mean'], r[2]['median'], r[2]['p5']] for r in rows]).mean(0)
        print(('| all | | %.3f | %.3f | %.3f | | | | %d of %d |' if md else 'ALL  mean %.3f  med %.3f  p5 %.3f   out of range: %d of %d') % (a[0], a[1], a[2], nbad, len(rows)))
    if '--check' in sys.argv and nbad:
        sys.exit(1)


if __name__ == '__main__':
    main()
