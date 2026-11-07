"""Galleria Mall zone layers (src/data/zones/mall_{1,2,3}.txt).

The floor plan and the mezzanine grid ("@layer 4.5") are the hand-laid gameplay layout; this script adds the
dressing that follows from them and rewrites the files in place (idempotent: it strips what it generated before):
  * columns on the mezzanine edge: 'I' on the floor plan under the slab edge, 'i' in the rail line above it
  * downlights under the deck ('l' on mezzanine deck cells, a 4 m lattice along the middle of the ring)
  * food stalls 'Y' against the east wall of the food court (mall_2), in place of the east kiosks
  * "@layer 0" floor inlays: a border band round the atrium under the rail line, diamond tiles over the atrium,
    compass roses under the fountain / Guest Services, the food-court checker, entrance mats at both gates
  * "@layer 9.5" roof: glazed coffer tiles over the atrium (4 m), trusses on the column lines with banners (kept
    clear of escalators), none over the lift shaft; downlights over the mezzanine ring
Run: python3 tools/mall_zones.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ZD = os.path.join(HERE, '..', 'src', 'data', 'zones')
GEN = {'0', '9.5'}


def parse(text):
    base, layers, cur = [], [], None
    for line in text.rstrip('\n').split('\n'):
        if line.startswith('@layer'):
            cur = [line.split()[1], []]
            layers.append(cur)
        elif cur is None:
            base.append(list(line))
        else:
            cur[1].append(list(line))
    return base, layers


def find(g, ch):
    return [(c, r) for r, row in enumerate(g) for c, x in enumerate(row) if x == ch]


def bbox(cells):
    cs, rs = [c for c, _ in cells], [r for _, r in cells]
    return min(cs), min(rs), max(cs), max(rs)


def build(name):
    path = os.path.join(ZD, name + '.txt')
    base, layers = parse(open(path).read())
    mez = next(L for L in layers if L[0] == '4.5')[1]
    H, W = len(base), len(base[0])
    # undo earlier generation
    for g in (base, mez):
        for r in range(H):
            for c in range(W):
                if g is base and g[r][c] in 'IY':
                    g[r][c] = '.'
                if g is mez and g[r][c] == 'i':
                    g[r][c] = 'r'
                if g is mez and g[r][c] == 'l':
                    g[r][c] = 'u'
    # the atrium void (open cells of the mezzanine grid) and the rail line one cell outside it
    void = [(c, r) for r in range(1, H - 1) for c in range(1, W - 1) if mez[r][c] == '.']
    c0, r0, c1, r1 = bbox(void)
    cl, cr, rt, rb = c0 - 1, c1 + 1, r0 - 1, r1 + 1
    assert (c1 - c0 + 1) % 4 == 0 and (r1 - r0 + 1) % 4 == 0, (name, c0, r0, c1, r1)
    lifts = find(base, 'L') + find(base, 'J')
    lift_rows = {r for _, r in lifts}

    # ---- columns: W / E rail lines on the truss rows, N / S rail lines at a third of the span
    truss_rows = [r for r in range(r0 + 2, r1, 8) if all(abs(r - lr) > 2 for lr in lift_rows)]
    spots = [(cl, r) for r in truss_rows] + [(cr, r) for r in truss_rows]
    span = c1 - c0 + 1
    for c in (c0 + span // 4 + 1, c1 - span // 4 - 1):
        spots += [(c, rt), (c, rb)]
    columns = []
    for (c, r) in spots:
        if mez[r][c] in 'ru' and base[r][c] == '.':
            mez[r][c] = 'i'
            base[r][c] = 'I'
            columns.append((c, r))
    # ---- downlights under the deck: middle of the ring, every 4 m, on plain deck cells
    mid = [3, H - 4]
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            on_ring = (r in mid and 2 <= c <= W - 3 and c % 4 == 1 and abs(c - (W - 4)) > 1) or (c in (3, W - 4) and 2 <= r <= H - 3 and r % 4 == 1)
            if on_ring and mez[r][c] == 'u' and base[r][c] in '.':
                mez[r][c] = 'l'
    # ---- food stalls (mall_2): east kiosks become stalls against the east wall
    if name == 'mall_2':
        for (c, r) in find(base, 'K'):
            if c > W // 2:
                base[r][c] = '.'
        if base[45][W - 3] == 'd':   # the directory totem by the south-east stall moves out of its way
            base[45][W - 3], base[45][W - 6] = '.', 'd'
        for rr in (8, 20, 32, 44):   # (r - 1) % 6 in 1..2: a stall never stands in front of a pilaster
            for r in range(rr, rr + 4):
                for c in (W - 3, W - 2):
                    assert base[r][c] == '.', (name, c, r, base[r][c])
                    base[r][c] = 'Y'

    # ---- "@layer 0": floor inlays
    fl = [['.'] * W for _ in range(H)]
    for c in range(cl, cr + 1):
        fl[rt][c] = fl[rb][c] = '='
    for r in range(rt, rb + 1):
        fl[r][cl] = fl[r][cr] = '='
    for (c, r) in ((cl, rt), (cr, rt), (cl, rb), (cr, rb)):
        fl[r][c] = '+'
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (c - c0) % 2 == 1 and (r - r0) % 2 == 1:   # a diamond every 2 m, terracotta and teal alternating
                fl[r][c] = 'xy'[((c - c0) // 2 + (r - r0) // 2) % 2]
    if name == 'mall_2':   # food-court checker under the tables
        tc0, tr0, tc1, tr1 = bbox(find(base, 'T'))
        for r in range(tr0 - 1, tr1 + 2):
            for c in range(tc0 - 1, tc1 + 2):
                fl[r][c] = 'k'
    for ch in 'FQ':   # compass roses (8 x 8) centred on the fountain / Guest Services
        cells = find(base, ch)
        if not cells:
            continue
        a, b, _, _ = bbox(cells)
        for r in range(b - 2, b + 6):
            for c in range(a - 2, a + 6):
                fl[r][c] = 'M'
    for ch in 'GE':   # entrance mats in front of the gates
        a, b, a2, _ = bbox(find(base, ch))
        rr = 1 if b == 0 else H - 3
        for r in (rr, rr + 1):
            for c in range(a, a2 + 1):
                fl[r][c] = 'w'

    # ---- "@layer 9.5": roof
    rf = [['.'] * W for _ in range(H)]
    lift_tiles = set()
    for (c, r) in lifts:
        lift_tiles.add(((c - c0) // 4, (r - r0) // 4))
    esc = find(base, 'N') + find(base, 'V')
    for ty in range((r1 - r0 + 1) // 4):
        for tx in range((c1 - c0 + 1) // 4):
            if (tx, ty) in lift_tiles:
                continue
            x0, y0 = c0 + tx * 4, r0 + ty * 4
            truss = any(y0 <= tr < y0 + 4 for tr in truss_rows)
            ch = '~'
            if truss:
                over_esc = any(x0 - 1 <= c <= x0 + 4 and y0 - 1 <= r <= y0 + 4 for (c, r) in esc)
                ch = '&' if (tx % 2 == 0 or over_esc) else ('%' if (tx // 2 + ty) % 2 else '$')
            for r in range(y0, y0 + 4):
                for c in range(x0, x0 + 4):
                    rf[r][c] = ch
    for r in range(1, H - 1):   # downlights over the mezzanine ring
        for c in range(1, W - 1):
            on_ring = (r in mid and c % 4 == 3 and abs(c - (W - 4)) > 1) or (c in (3, W - 4) and r % 4 == 3)
            if on_ring and mez[r][c] in 'uSoBcah' and not (r0 - 1 <= r <= r1 + 1 and c0 - 1 <= c <= c1 + 1):
                rf[r][c] = ':'

    out = [''.join(row) for row in base]
    for y, g in (('0', fl), ('4.5', mez), ('9.5', rf)):
        out.append('@layer ' + y)
        out += [''.join(row) for row in g]
    open(path, 'w').write('\n'.join(out) + '\n')
    print(name, 'void', (c0, r0, c1, r1), 'columns', len(columns), 'truss rows', truss_rows)


if __name__ == '__main__':
    for n in ('mall_1', 'mall_2', 'mall_3'):
        build(n)
