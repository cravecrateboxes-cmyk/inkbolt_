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
  * walk-in shops: a 7-cell band behind the west and east walls; 5 bays per side whose doorway approach is clear on
    both storeys (props in the way move to the bay's pilaster rows) become 5 x 6 m rooms: room symbols on the plan and
    the mezzanine layer, doorway cells 'n' (three per bay) with deck in the upper doorways, a pickup in two ground-floor
    shops per zone (layer 0). Re-running strips the band first, so the hand-laid hall stays the source.
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


# ---- walk-in shops: a band of shop rooms behind the west and east shop fronts (both storeys)
BAND = 7                      # band depth in cells: the back wall + a 6 m deep room
LO_ROOMS = 'AZCRWU'           # ground storey: Atelier, SIGNAL, The Coffee House, Northfield Books, Toy Workshop, Aurum
UP_ROOMS = 'gvbmt'            # mezzanine storey: Shoe Gallery, Lumen Optics, Bakehouse, Hearth & Home, Leatherworks
PICK = {'W': (0, 2, 3, 5, 7), 'E': (1, 2, 4, 6, 7)}   # preferred bays per side (5 of 8), topped up from the rest
PER_SIDE = 5


def strip_band(base, mez):
    """undo an earlier band: drop its columns, close the doorways again"""
    b = 0
    while base[1][b] == '#':
        b += 1
    b -= 1
    if b <= 0:
        return base, mez
    base = [row[b:len(row) - b] for row in base]
    mez = [row[b:len(row) - b] for row in mez]
    for g in (base, mez):
        for row in g:
            for c in (0, len(row) - 1):
                row[c] = '#'
    return base, mez


def add_band(name, zi, base, mez, fl, rf):
    """rooms behind the chosen bays of the west / east walls; returns the new grids and the room list"""
    H, W = len(base), len(base[0])
    rooms = []
    for side, front, inw in (('W', 0, 1), ('E', W - 1, -1)):
        cand = []
        for b in range(8):
            r0 = 1 + 6 * b
            if r0 + 5 > H - 3:
                continue
            door = range(r0 + 2, r0 + 5)
            # props that would stand in front of the doorway move to the pilaster rows of the bay
            for g, movable, rows in ((base, 'dc', door), (mez, 'oc', door), (base, 'd', range(r0 + 1, r0 + 6))):
                for r in rows:
                    for j in (1, 2):
                        c = front + inw * j
                        if g[r][c] in movable:
                            for rr in (r0, r0 + 6, r0 - 1, r0 + 7):
                                if g[rr][c] in '.u':
                                    g[rr][c], g[r][c] = g[r][c], ('.' if g is base else 'u')
                                    break
            ok = all(base[r][front + inw * j] in '.ah' and mez[r][front + inw * j] in 'ul' for r in door for j in (1, 2))
            ok = ok and all(base[r][front + inw] != 'Y' for r in range(r0 + 1, r0 + 6))
            if ok:
                cand.append(b)
        pick = [b for b in PICK[side] if b in cand]
        pick += [b for b in cand if b not in pick][:max(0, PER_SIDE - len(pick))]
        for b in sorted(pick[:PER_SIDE]):
            rooms.append((side, 1 + 6 * b))
    # room identities: every shop of the storey turns up in turn (the open-front Field & Court stays shuttered)
    rooms.sort(key=lambda t: (t[1], t[0]))
    out_b = [['#'] * BAND + row + ['#'] * BAND for row in base]
    out_m = [['#'] * BAND + row + ['#'] * BAND for row in mez]
    out_f = [['.'] * BAND + row + ['.'] * BAND for row in fl]
    out_r = [['.'] * BAND + row + ['.'] * BAND for row in rf]
    W2 = W + 2 * BAND
    info = []
    for i, (side, r0) in enumerate(rooms):
        lo = LO_ROOMS[(i + zi * 2) % len(LO_ROOMS)]
        up = UP_ROOMS[(i + zi * 3) % len(UP_ROOMS)]
        front = BAND if side == 'W' else W2 - 1 - BAND
        cols = range(1, BAND) if side == 'W' else range(W2 - BAND, W2 - 1)
        for r in range(r0 + 1, r0 + 6):
            for c in cols:
                out_b[r][c] = lo
                out_m[r][c] = up
        for r in range(r0 + 2, r0 + 5):
            out_b[r][front] = 'n'
            out_m[r][front] = 'u'
        if i in (2, 7):   # a pickup in the aisle of two ground-floor shops per zone
            c = BAND - 2 if side == 'W' else W2 - BAND + 1
            out_f[r0 + 3][c] = 'ah'[i == 7]
        info.append((side, r0, lo, up))
    return out_b, out_m, out_f, out_r, info


def build(name):
    path = os.path.join(ZD, name + '.txt')
    base, layers = parse(open(path).read())
    mez = next(L for L in layers if L[0] == '4.5')[1]
    base, mez = strip_band(base, mez)
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

    zi = ('mall_1', 'mall_2', 'mall_3').index(name)
    base, mez, fl, rf, rooms = add_band(name, zi, base, mez, fl, rf)
    out = [''.join(row) for row in base]
    for y, g in (('0', fl), ('4.5', mez), ('9.5', rf)):
        out.append('@layer ' + y)
        out += [''.join(row) for row in g]
    open(path, 'w').write('\n'.join(out) + '\n')
    print(name, 'void', (c0, r0, c1, r1), 'columns', len(columns), 'truss rows', truss_rows)
    for side, r, lo, up in rooms:
        print('   shop', side, 'rows', r + 1, '-', r + 5, 'ground', lo, 'upper', up)


if __name__ == '__main__':
    for n in ('mall_1', 'mall_2', 'mall_3'):
        build(n)
