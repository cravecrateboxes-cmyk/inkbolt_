#!/usr/bin/env python3
"""Zone maps for the Galleria Mall theme (src/data/zones/mall_*.txt).

Each zone is a two-storey atrium: the floor plan (ground floor) and an "@layer 4.5" grid for the mezzanine. The
mezzanine is a 7 m deck ring along the walls ('u'), glass rails ('r') along its edge over the open atrium ('.'),
reached by two escalators ('N' rises north, 'V' rises south) and a glass elevator ('L' opens west, 'J' opens east).

    python3 tools/mall_zones.py          # writes mall_1..3
"""
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data', 'zones')
W, H, RING = 48, 52, 7


class Grid:
    def __init__(self, fill):
        self.g = [[fill] * W for _ in range(H)]

    def put(self, c, r, ch, w=1, h=1):
        for y in range(r, r + h):
            for x in range(c, c + w):
                self.g[y][x] = ch

    def at(self, c, r):
        return self.g[r][c] if 0 <= r < H and 0 <= c < W else '#'

    def text(self):
        return '\n'.join(''.join(row) for row in self.g)


def deck_cell(c, r):
    return 1 <= c <= W - 2 and 1 <= r <= H - 2 and (c <= RING or c >= W - 1 - RING or r <= RING or r >= H - 1 - RING)


def base_shell():
    b = Grid('.')
    for c in range(W):
        b.put(c, 0, '#'); b.put(c, H - 1, '#')
    for r in range(H):
        b.put(0, r, '#'); b.put(W - 1, r, '#')
    cx = W // 2
    b.put(cx - 1, 0, 'G', 3, 1)
    b.put(cx - 1, H - 1, 'E', 3, 1)
    b.put(cx, H - 3, 'P')
    return b


def upper_shell(openings):
    """deck ring + rails along the void edge, except the cells in `openings` (escalator tops, elevator door)"""
    u = Grid('.')
    for r in range(H):
        for c in range(W):
            if deck_cell(c, r):
                u.put(c, r, 'u')
            elif c in (0, W - 1) or r in (0, H - 1):
                u.put(c, r, '#')   # the walls (nothing is built from '#' in a layer)
    for r in range(H):
        for c in range(W):
            if u.at(c, r) != 'u' or (c, r) in openings:
                continue
            if any(0 <= c + dc < W and 0 <= r + dr < H and not deck_cell(c + dc, r + dr) and u.g[r + dr][c + dc] == '.'
                   for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                u.put(c, r, 'r')
    return u


def zone(n):
    b, cx = base_shell(), W // 2
    lo, hi = RING + 1, W - 2 - RING          # first / last void column
    top, bot = RING + 1, H - 2 - RING        # first / last void row
    # escalators: west one rises north to the north deck, east one rises south to the south deck
    ew, ee = lo + 2, hi - 3
    b.put(ew, top, 'N', 2, 10)
    b.put(ee, bot - 9, 'V', 2, 10)
    openings = {(ew, top - 1), (ew + 1, top - 1), (ee, bot + 1), (ee + 1, bot + 1)}
    # elevator: 3 x 3 in the void against the west (zones 1, 2) or east (zone 3) deck edge, door toward the deck
    er = H // 2 - 2
    if n == 3:
        b.put(hi - 2, er, 'J', 3, 3); openings |= {(hi + 1, er + k) for k in range(3)}
    else:
        b.put(lo, er, 'L', 3, 3); openings |= {(lo - 1, er + k) for k in range(3)}
    u = upper_shell(openings)

    # ground floor arcade under the deck: kiosks, benches, ad pillars, bins, planters (all lower than the 4.1 m slab)
    def safe(c, r, w=1, h=1):
        return all(b.at(x, y) == '.' for x in range(c - 1, c + w + 1) for y in range(r - 1, r + h + 1))

    def place(c, r, ch, w=1, h=1):
        if safe(c, r, w, h):
            b.put(c, r, ch, w, h)
            return True
        return False
    for r in (10, 20, 31, 41):
        place(3, r, 'K', 2, 3)
        place(W - 5, r, 'K', 2, 3)
    for r in (6, 15, 26, 36, 45):
        place(2, r, 'd'); place(W - 3, r, 'd')
    for c in (6, 15, 32, 41):
        place(c, 3, 'B', 2, 1); place(c, H - 4, 'B', 2, 1)
        place(c + 3, 2, 'c'); place(c + 3, H - 3, 'c')
    for c in (10, 37):
        place(c, 5, 'o'); place(c, H - 6, 'o')
    # atrium: the centrepiece per zone, big planters (tall canopies stay under the open skylights) and seating
    if n == 1:
        place(cx - 2, H // 2 - 4, 'F', 4, 4)
        place(cx - 2, H // 2 + 6, 'Q', 4, 4)
        for (c, r) in ((cx - 9, 12), (cx + 7, 12), (cx - 9, H - 16), (cx + 7, H - 16)):
            place(c, r, 'O', 2, 2)
        for (c, r) in ((cx - 7, H // 2 - 3), (cx + 5, H // 2 - 3), (cx - 7, H // 2 + 4), (cx + 5, H // 2 + 4)):
            place(c, r, 'B', 2, 1)
    elif n == 2:   # food court
        place(cx - 2, 11, 'Q', 4, 4)
        for r in range(17, H - 13, 5):
            for c in range(lo + 6, hi - 5, 5):
                place(c, r, 'T', 2, 2)
        for (c, r) in ((cx - 1, H - 12), (lo + 5, 12), (hi - 6, H - 13)):
            place(c, r, 'O', 2, 2)
        for (c, r) in ((lo + 6, 13), (hi - 8, 13)):
            place(c, r, 'K', 3, 2)
    else:          # department store floor
        place(cx - 2, H // 2 - 2, 'F', 4, 4)
        for r in range(12, H - 12, 6):
            for c in (lo + 6, hi - 9):
                place(c, r, 'D', 2, 1)
        for (c, r) in ((cx - 7, 13), (cx + 5, 13), (cx - 7, H - 15), (cx + 5, H - 15)):
            place(c, r, 'O', 2, 2)
        for r in (17, 33):
            place(cx - 1, r, 'd')
    # spawn cans: ground floor (atrium corners, arcades) and on the mezzanine
    for (c, r) in ((lo + 1, top + 12), (hi - 1, top + 12), (lo + 1, bot - 10), (hi - 1, bot - 10), (cx - 6, 8), (cx + 6, 8),
                   (3, 25), (W - 4, 25)):
        if b.at(c, r) == '.' and safe(c, r):
            b.put(c, r, 'S')
    for (c, r) in ((4, 4), (W - 5, 4), (4, H - 7), (W - 5, H - 9), (cx, 3)):
        if u.at(c, r) == 'u':
            u.put(c, r, 'S')
    # pickups: ammo/health on both floors
    for (c, r, ch) in ((cx - 4, H - 6, 'a'), (cx + 4, 10, 'h'), (6, H // 2, 'a'), (W - 7, H // 2 + 3, 'h')):
        if b.at(c, r) == '.' and safe(c, r):
            b.put(c, r, ch)
    for (c, r, ch) in ((3, H // 2 + 6, 'a'), (W - 4, 12, 'h')):
        if u.at(c, r) == 'u':
            u.put(c, r, ch)
    # mezzanine furniture against the shop fronts (walkway stays clear)
    for r in range(9, H - 9, 7):
        for c in (2, W - 3):
            if u.at(c, r) == 'u' and u.at(c, r + 1) == 'u':
                u.put(c, r, 'o')
    for c in range(9, W - 9, 8):
        for r in (2, H - 3):
            if all(u.at(c + k, r) == 'u' for k in range(2)):
                u.put(c, r, 'B', 2, 1)
    return b.text() + '\n@layer 4.5\n' + u.text() + '\n'


def main(argv):
    for n in (1, 2, 3):
        with open(os.path.join(OUT, 'mall_%d.txt' % n), 'w') as f:
            f.write(zone(n))
        print('wrote mall_%d.txt' % n)


if __name__ == '__main__':
    main(sys.argv[1:])
