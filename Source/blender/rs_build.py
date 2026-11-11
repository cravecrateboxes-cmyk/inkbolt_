"""INKBOLT kit-resort: built things -- the lobby pavilion, the lagoon pool and its swim-up bar, cabanas, loungers,
umbrellas, tiki torches, lounge sets, planters, kayaks, the towel hut, signposts, crates, the broken-down golf cart,
tree-platform plank decals, rails, rope bridges, deck posts, hammocks, the treehouse villas, the gate, the hatch and
the overwater bungalows of the backdrop (see rs_base.py for the conventions)."""
import math
import random

from rs_base import RKit, TOP, SLAB, leafcol, blob, palm, flowers, rope_sag, tuft  # noqa: F401


def thcol(f):
    n = f.normal
    return 'thatch' if n.z > 0.35 else ('thatch2' if n.z < -0.2 else 'thatch3')


def hip_roof(k, x0, x1, y0, y1, ze, rx, zr, th=0.22, col=thcol):
    """thatched hip roof: eave rectangle at ze (thickness th), ridge from -rx..rx (centre y) at zr"""
    cy = (y0 + y1) / 2
    cx = (x0 + x1) / 2
    pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (ze, ze - th)]
    pts += [(cx - rx, cy, zr), (cx + rx, cy, zr), (cx - rx, cy, zr - th * 1.6), (cx + rx, cy, zr - th * 1.6)]
    k.hullp(pts, col)
    if rx > 0.05:
        k.beam((cx - rx - 0.1, cy, zr + 0.02), (cx + rx + 0.1, cy, zr + 0.02), 0.16, 'thatch2')


def cone_roof(k, x, y, ze, r, zt, seg=8, th=0.18):
    pts = []
    for i in range(seg):
        a = i / seg * 2 * math.pi + math.pi / seg
        pts += [(x + math.cos(a) * r, y + math.sin(a) * r, ze), (x + math.cos(a) * r, y + math.sin(a) * r, ze - th)]
    pts += [(x, y, zt), (x, y, zt - th * 1.5)]
    k.hullp(pts, thcol)


def bamboo_post(k, x, y, z0, h, r=0.06, c='bamboo'):
    k.cyl(x, y, z0, r, r * 0.92, h, c, seg=6)
    for z in (z0 + h * 0.3, z0 + h * 0.65):
        k.cyl(x, y, z, r * 1.12, r * 1.12, 0.035, 'bamboo2', seg=6, caps=False, ink=False)


# ================================================================ tree platform decals, rails, bridges, posts
def build_decks(k, ao):
    # plank seams (and joists for the tree platforms) over the engine's deck slab: [4, 2] along X, planks along Y
    for name, joists in (('Planks', False), ('PlanksJ', True)):
        k.begin()
        for i in range(1, 8):
            x = -2 + i * 0.5
            k.qz(x - 0.014, x + 0.014, -0.995, 0.995, 0.004, 1, 'wood2')
        if joists:
            for y in (-0.6, 0.6):
                k.bx(-2, 2, y - 0.09, y + 0.09, -SLAB - 0.26, -SLAB - 0.004, 'woodD', ink=False)
        k.finish(name, ao=False)
    # bamboo-and-rope railing (along Blender Y; the run placer links half modules)
    def rail(y0, y1, post):
        k.cyl(0, y0, 1.0, 0.055, 0.055, y1 - y0, 'bamboo', seg=5, rot=(-90, 0, 0), caps=False)
        k.beam((0, y0, 0.55), (0, y1, 0.55), 0.035, 'rope', ink=False)
        if post:
            k.cyl(0, 0, 0.0, 0.04, 0.04, 1.0, 'bamboo2', seg=4, ink=False)
    k.begin(); rail(-0.5, 0.5, True); k.col(-0.06, 0.06, -0.5, 0.5, 0.0, 1.06); k.finish('RailFull', ao=ao)
    k.begin(); rail(-0.5, -0.07, False); k.col(-0.06, 0.06, -0.5, 0.0, 0.0, 1.06); k.finish('RailHalf', ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 0.08, 0.075, 1.12, 'bamboo', seg=6)
    k.cyl(0, 0, 1.12, 0.09, 0.02, 0.1, 'bamboo2', seg=6)
    k.finish('RailPost', ao=ao)
    # rope bridge [3, 2] along X: plank treads on two stringers, posts at both ends, sagging rope rails
    k.begin()
    for i in range(6):
        x0 = -1.5 + i * 0.5 + 0.015
        k.bx(x0, x0 + 0.47, -0.86, 0.86, -0.08, 0.0, 'wood3' if i % 3 else 'wood')
    for y in (-0.9, 0.9):
        k.bx(-1.5, 1.5, y - 0.07, y + 0.07, -0.26, -0.08, 'woodD')
        for x in (-1.42, 1.42):
            k.cyl(x, y, -0.2, 0.06, 0.055, 1.36, 'bamboo', seg=5)
        for z, sag in ((1.08, 0.12), (0.56, 0.08)):
            rope_sag(k, (-1.42, y, z), (1.42, y, z), sag, n=2)
        for x in (-0.6, 0.6):
            k.beam((x, y * 0.967, 0.02), (x, y * 0.967, 0.98), 0.025, 'rope', ink=False)
    k.wcol(-1.5, 1.5, -0.9, 0.9, -0.26, 0.0)
    k.col(-1.5, 1.5, -0.98, -0.86, 0.0, 1.1)
    k.col(-1.5, 1.5, 0.86, 0.98, 0.0, 1.1)
    k.finish('Bridge', ao=ao)
    # deck post (ground to the slab underside)
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, -0.05, 0.3, 'stone2')
    k.bx(-0.15, 0.15, -0.15, 0.15, 0.3, TOP - SLAB - 0.01, 'wood2')
    for z in (2.0, 4.6):
        k.bx(-0.165, 0.165, -0.165, 0.165, z, z + 0.12, 'rope', ink=False)
    k.col(-0.16, 0.16, -0.16, 0.16, 0.0, TOP - SLAB)
    k.finish('DeckPost', ao=ao)


# ================================================================ treehouse villas (open front -Y)
def villa(k, W, D, grand=False):
    hx, hy = W / 2, D / 2
    fl = 0.14
    k.bx(-hx, hx, -hy, hy, 0.0, fl, 'wood3')
    for i in range(1, int(W * 2)):
        x = -hx + i * 0.5
        k.qz(x - 0.01, x + 0.01, -hy + 0.02, hy - 0.02, fl + 0.003, 1, 'wood2')
    wh = 3.0 if not grand else 3.3
    t = 0.18
    # back and side walls: woven bamboo panels with timber frames, a window in each side wall
    k.bx(-hx, hx, hy - t, hy, fl, wh, 'bamboo')
    for sx in (-1, 1):
        x0, x1 = (-hx, -hx + t) if sx < 0 else (hx - t, hx)
        k.bx(x0, x1, -hy + 0.9, hy - t, fl, wh, 'bamboo')
        xf = x1 + 0.004 if sx > 0 else x0 - 0.004
        k.qx(-0.6, 0.8, 1.1, 2.2, xf, sx, 'woodD')
        k.qx(-0.6, 0.8, 1.6, 1.66, xf + sx * 0.003, sx, 'wood2')
        k.qx(0.07, 0.13, 1.1, 2.2, xf + sx * 0.006, sx, 'wood2')
        xi = x0 - 0.004 if sx > 0 else x1 + 0.004
        k.qx(-0.6, 0.8, 1.1, 2.2, xi, -sx, 'woodD')
    for i in range(int(W / 0.5) - 1):   # panel seams on the inner face of the back wall
        x = -hx + 0.5 + i * 0.5
        k.qy(x - 0.012, x + 0.012, fl + 0.05, wh - 0.05, hy - t - 0.004, -1, 'bamboo2')
    # corner posts, front beam, front railing either side of the doorway
    for sx in (-1, 1):
        k.bx(sx * hx - (0.22 if sx > 0 else 0), sx * hx + (0.22 if sx < 0 else 0), -hy, -hy + 0.22, fl, wh, 'wood2')
        k.bx(sx * hx - (0.12 if sx > 0 else 0), sx * hx + (0.12 if sx < 0 else 0), -hy + 0.25, -hy + 0.89, fl, wh, 'wood')
        xa, xb = sorted((sx * (hx - 0.22), sx * 1.05))
        k.cyl(xa, -hy + 0.11, 0.95, 0.05, 0.05, xb - xa, 'bamboo', seg=6, rot=(0, 90, 0))
        for x in (xa + 0.3, (xa + xb) / 2, xb - 0.05):
            k.cyl(x, -hy + 0.11, fl, 0.035, 0.035, 0.82, 'bamboo2', seg=5)
    k.bx(-hx, hx, -hy, -hy + 0.22, wh, wh + 0.3, 'wood2')
    # roof
    ov = 0.7
    ze = wh + 0.32
    if grand:
        hip_roof(k, -hx - ov, hx + ov, -hy - ov, hy + ov, ze, hx * 0.55, ze + 1.4)
        hip_roof(k, -hx * 0.62, hx * 0.62, -hy * 0.55, hy * 0.55, ze + 0.95, hx * 0.3, ze + 2.6)
    else:
        hip_roof(k, -hx - ov, hx + ov, -hy - ov, hy + ov, ze, hx * 0.4, ze + 2.0)
    # bed against the back wall, nightstands with lamps, a rug
    bw = 1.25 if not grand else 1.5
    k.bx(-bw, bw, hy - t - 2.1, hy - t - 0.02, fl, fl + 0.38, 'wood2')
    k.bx(-bw + 0.05, bw - 0.05, hy - t - 2.05, hy - t - 0.1, fl + 0.38, fl + 0.58, 'canvas')
    k.bx(-bw + 0.04, bw - 0.04, hy - t - 2.08, hy - t - 1.2, fl + 0.5, fl + 0.62, 'cushion')
    for x in (-bw * 0.5, bw * 0.5):
        k.bx(x - 0.42, x + 0.42, hy - t - 0.55, hy - t - 0.15, fl + 0.58, fl + 0.78, 'canvas2')
    k.bx(-bw - 0.05, bw + 0.05, hy - t - 0.1, hy - t - 0.004, fl + 0.38, fl + 1.3, 'woodD')
    for sx in (-1, 1):
        x = sx * (bw + 0.45)
        k.bx(x - 0.28, x + 0.28, hy - t - 0.6, hy - t - 0.04, fl, fl + 0.55, 'wood')
        k.cyl(x, hy - t - 0.32, fl + 0.55, 0.06, 0.05, 0.3, 'wood2', seg=6)
        k.cyl(x, hy - t - 0.32, fl + 0.85, 0.2, 0.13, 0.25, 'canvas2', seg=8)
    k.qz(-bw - 0.3, bw + 0.3, -hy + 1.0, hy - t - 2.3, fl + 0.007, 1, 'coral')
    k.qz(-bw - 0.1, bw + 0.1, -hy + 1.2, hy - t - 2.5, fl + 0.010, 1, 'canvas')
    # collision: floor (walkable), walls, posts, railing, bed and nightstands
    k.wcol(-hx, hx, -hy, hy, 0.0, fl)
    k.col(-hx, hx, hy - t, hy, fl, wh)
    for sx in (-1, 1):
        x0, x1 = (-hx, -hx + t) if sx < 0 else (hx - t, hx)
        k.col(x0, x1, -hy + 0.9, hy - t, fl, wh)
        k.col(min(sx * hx, sx * 1.05), max(sx * hx, sx * 1.05), -hy, -hy + 0.22, fl, 1.0)
        k.col(min(sx * hx, sx * (hx - 0.12)), max(sx * hx, sx * (hx - 0.12)), -hy + 0.22, -hy + 0.89, fl, wh)
    k.col(-bw - 0.75, bw + 0.75, hy - t - 2.1, hy - t, fl, fl + 0.6)


def build_villas(k, ao):
    k.begin(); villa(k, 6, 5); k.finish('Villa', ao=ao)
    k.begin()
    villa(k, 8, 6, grand=True)
    # the suite's sign on the front beam
    k.bx(-1.9, 1.9, -3.06, -2.99, 3.66, 4.1, 'woodD', ink=False)
    k.text('CANOPY SUITE', 0.0, -3.066, 3.74, 0.28, 'thatch3', maxw=3.5)
    # lounge chairs on the veranda
    for sx in (-1, 1):
        x = sx * 2.6
        k.bx(x - 0.4, x + 0.4, -2.45, -1.5, 0.14, 0.5, 'wood')
        k.bx(x - 0.36, x + 0.36, -2.4, -1.55, 0.5, 0.62, 'cushion' if sx < 0 else 'coral')
        k.bx(x - 0.4, x + 0.4, -1.55, -1.45, 0.5, 1.0, 'wood')
        k.col(x - 0.4, x + 0.4, -2.45, -1.45, 0.14, 0.62)
    k.finish('Landmark_Villa', ao=ao)


# ================================================================ lobby pavilion [14, 10], open-air, thatched
def build_lobby(k, ao):
    k.begin()
    k.bx(-7, 7, -5, 5, 0.0, 0.06, 'tile')
    for i in range(1, 14):
        k.qz(-7 + i - 0.012, -7 + i + 0.012, -4.98, 4.98, 0.063, 1, 'stone2')
    for j in range(1, 10):
        k.qz(-6.98, 6.98, -5 + j - 0.012, -5 + j + 0.012, 0.066, 1, 'stone2')
    k.qz(-2.6, 2.6, -3.2, -0.6, 0.07, 1, 'coral')
    k.qz(-2.3, 2.3, -2.9, -0.9, 0.073, 1, 'canvas')
    xs, ys = (-6.4, -2.1, 2.1, 6.4), (-4.4, 0.0, 4.4)
    for x in xs:
        for y in ys:
            k.bx(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0.06, 0.45, 'stone')
            k.cyl(x, y, 0.45, 0.2, 0.18, 3.8, 'wood', seg=8)
            k.cyl(x, y, 1.1, 0.215, 0.215, 0.1, 'rope', seg=8, caps=False, ink=False)
    for y in ys:
        k.bx(-7.0, 7.0, y - 0.18, y + 0.18, 4.25, 4.6, 'woodD')
    for x in xs:
        k.bx(x - 0.16, x + 0.16, -4.6, 4.6, 4.6, 4.85, 'woodD')
    hip_roof(k, -8.2, 8.2, -6.2, 6.2, 5.05, 5.2, 7.1, th=0.28)
    hip_roof(k, -5.4, 5.4, -3.7, 3.7, 6.0, 2.6, 8.6, th=0.24)
    # ceiling fans
    for x in (-4.2, 0.0, 4.2):
        k.cyl(x, 0.0, 3.9, 0.03, 0.03, 0.55, 'woodD', seg=5)
        k.cyl(x, 0.0, 3.8, 0.14, 0.12, 0.14, 'wood2', seg=8)
        for a in range(4):
            r = math.radians(a * 90 + 20)
            k.bxr(x + math.cos(r) * 0.55, math.sin(r) * 0.55, 3.86, 0.9, 0.2, 0.025, 'wood3', rot=(0, 0, math.degrees(r)))
    # reception: carved desk in front of a woven screen with the resort's name
    k.bx(-5.6, -1.4, 2.5, 3.3, 0.06, 1.05, 'wood2')
    k.bx(-5.7, -1.3, 2.42, 3.38, 1.05, 1.15, 'stone')
    for i in range(5):
        x = -5.2 + i * 0.85
        k.qy(x - 0.22, x + 0.22, 0.25, 0.85, 2.496, -1, 'woodD')
    k.bx(-6.3, -0.7, 3.75, 3.95, 0.06, 3.4, 'bamboo')
    for i in range(1, 11):
        x = -6.3 + i * 0.509
        k.qy(x - 0.01, x + 0.01, 0.12, 3.35, 3.746, -1, 'bamboo2')
    k.bx(-5.9, -1.1, 3.65, 3.746, 2.15, 3.15, 'woodD', ink=False)
    k.text('PALMYRA COVE', -3.5, 3.642, 2.55, 0.42, 'thatch3', maxw=4.4, font='serif')
    k.text('RESORT  &  CANOPY VILLAS', -3.5, 3.642, 2.25, 0.16, 'bloom', font='cond', maxw=4.2)
    # bell, orchids and a flower bowl on the desk
    k.cyl(-2.0, 2.9, 1.15, 0.12, 0.05, 0.12, 'amber', seg=8)
    k.cyl(-4.8, 2.9, 1.15, 0.14, 0.18, 0.22, 'stone2', seg=8)
    rnd = random.Random(201)
    flowers(k, rnd, [(-4.8 + math.cos(a) * 0.12, 2.9 + math.sin(a) * 0.12, 1.42) for a in (0, 2.1, 4.2)], 'pink', 0.09)
    # hanging sign under the front beam
    k.bx(-1.8, 1.8, -4.66, -4.58, 3.45, 4.2, 'woodD')
    k.text('PALMYRA COVE', 0.0, -4.664, 3.62, 0.44, 'thatch3', maxw=3.4, font='serif')
    k.beam((-1.6, -4.62, 4.2), (-1.6, -4.62, 4.25), 0.03, 'rope', ink=False)
    k.beam((1.6, -4.62, 4.2), (1.6, -4.62, 4.25), 0.03, 'rope', ink=False)
    k.wcol(-7, 7, -5, 5, 0.0, 0.06)
    for x in xs:
        for y in ys:
            k.col(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.06, 4.25)
    k.col(-5.7, -1.3, 2.42, 3.38, 0.06, 1.15)
    k.col(-6.3, -0.7, 3.75, 3.95, 0.06, 3.4)
    k.finish('Landmark_Lobby', ao=ao)


# ================================================================ lagoon pool [20, 12] with the swim-up bar
def pool_outline(n=32, sx=9.4, sy=5.5, inset=0.0):
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        e = 0.32   # superellipse exponent factor (rounded rectangle)
        r = 1.0 / (abs(c) ** (2 / e) + abs(s) ** (2 / e)) ** (e / 2)
        bump = 1.0 + 0.05 * math.sin(3 * a + 0.7) + 0.03 * math.sin(5 * a)
        pts.append(((sx - inset) * c * r * bump, (sy - inset) * s * r * bump))
    return pts


def build_pool(k, ao):
    k.begin()
    outer = pool_outline()
    inner = pool_outline(inset=0.55)
    n = len(outer)
    for i in range(n):   # coping stones
        a, b, c, d = outer[i], outer[(i + 1) % n], inner[(i + 1) % n], inner[i]
        k.hullp([(p[0], p[1], z) for p in (a, b, c, d) for z in (0.0, 0.13)], lambda f: 'stone' if f.normal.z > 0.5 else 'stone2')
    k.poly([(p[0], p[1], 0.06) for p in inner], 'water', (0, 0, 1))
    k.poly([(p[0] * 0.8, p[1] * 0.72, 0.064) for p in inner], 'water2', (0, 0, 1))
    k.poly([(p[0] * 0.45 - 1.2, p[1] * 0.42, 0.068) for p in inner], 'waterD', (0, 0, 1))
    rnd = random.Random(211)
    for i in range(14):
        x, y = rnd.uniform(-7.5, 7.5), rnd.uniform(-3.8, 3.8)
        if abs(x - 5.0) < 2.4 and abs(y) < 2.4:
            continue
        L = rnd.uniform(0.3, 0.7)
        k.qz(x - L / 2, x + L / 2, y - 0.03, y + 0.03, 0.072, 1, 'foam')
    # swim-up bar: a square counter (open at the east for the bartender), thatched canopy, stools in the water
    bx, H = 5.0, 1.5
    for (x0, x1, y0, y1) in ((bx - H, bx + H, -H, -H + 0.5), (bx - H, bx + H, H - 0.5, H), (bx - H, bx - H + 0.5, -H + 0.5, H - 0.5),
                             (bx + H - 0.5, bx + H, -H + 0.5, -0.4), (bx + H - 0.5, bx + H, 0.4, H - 0.5)):
        k.bx(x0, x1, y0, y1, 0.0, 1.05, 'wood2')
        side = (x1 - x0) < 1.0   # the west / east counters' tops butt against the north / south ones
        k.bx(x0 - 0.06, x1 + 0.06, y0 + (0.06 if side else -0.06), y1 - (0.06 if side else -0.06), 1.05, 1.13, 'stone')
        k.col(x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, 0.0, 1.13)
    k.bx(bx - 0.5, bx + 0.5, -0.5, 0.5, 0.0, 1.6, 'woodD')   # back bar with bottles
    for i in range(8):
        a = i / 8 * 2 * math.pi
        k.cyl(bx + math.cos(a) * 0.36, math.sin(a) * 0.36, 1.6, 0.05, 0.035, 0.28, ('bloom', 'coral', 'water2', 'leaf')[i % 4], seg=5)
    k.col(bx - 0.5, bx + 0.5, -0.5, 0.5, 0.0, 1.6)
    for (x, y) in ((bx - H, -H), (bx + H, -H), (bx - H, H), (bx + H, H)):
        bamboo_post(k, x + (0.12 if x < bx else -0.12), y + (0.12 if y < 0 else -0.12), 1.13, 2.1, r=0.09)
    cone_roof(k, bx, 0.0, 3.25, 3.0, 4.9, seg=8)
    k.bx(bx - 1.5, bx + 1.5, -H - 0.12, -H - 0.06, 2.75, 3.15, 'woodD', ink=False)
    k.text('SWIM-UP BAR', bx, -H - 0.126, 2.83, 0.26, 'thatch3', maxw=2.8)
    for i in range(10):   # stools round the west, north and south sides
        if i < 4:
            x, y = bx - H - 0.5, -1.05 + i * 0.7
        elif i < 7:
            x, y = bx - 1.0 + (i - 4) * 1.0, -H - 0.5
        else:
            x, y = bx - 1.0 + (i - 7) * 1.0, H + 0.5
        k.cyl(x, y, 0.0, 0.07, 0.07, 0.62, 'metal2', seg=6)
        k.cyl(x, y, 0.62, 0.22, 0.22, 0.09, 'cushion', seg=8)
    k.finish('Landmark_Pool', ao=ao)


# ================================================================ cabana [4, 4], loungers, umbrellas, torches
def build_beach(k, ao):
    k.begin()
    k.bx(-1.85, 1.85, -1.85, 1.85, 0.0, 0.15, 'wood3')
    for i in range(1, 14):
        y = -1.85 + i * 0.264
        k.qz(-1.83, 1.83, y - 0.01, y + 0.01, 0.153, 1, 'wood2')
    for x in (-1.68, 1.68):
        for y in (-1.68, 1.68):
            k.cyl(x, y, 0.15, 0.08, 0.075, 2.5, 'wood', seg=6)
    hip_roof(k, -2.0, 2.0, -2.0, 2.0, 2.75, 0.0, 3.75, th=0.12, col=lambda f: 'canvas' if f.normal.z > -0.2 else 'canvas2')
    for e in (-1, 1):   # coral valance under the canopy's eaves
        k.bx(-1.97, 1.97, e * 2.0 - 0.015, e * 2.0 + 0.015, 2.4, 2.66, 'coral', ink=False)
        k.bx(e * 2.0 - 0.015, e * 2.0 + 0.015, -1.97, 1.97, 2.4, 2.66, 'coral', ink=False)
    k.bx(-1.58, 1.58, 1.6, 1.66, 0.16, 2.62, 'canvas2', ink=False)
    for x in (-1.6, 1.6):   # tied-back curtains at the front posts
        k.hullp([(x - 0.12, -1.55, 2.6), (x + 0.12, -1.55, 2.6), (x, -1.45, 2.6), (x - 0.06, -1.5, 1.2), (x + 0.06, -1.5, 1.2), (x - 0.15, -1.5, 0.3), (x + 0.15, -1.5, 0.3)], 'canvas')
        k.cyl(x, -1.5, 1.25, 0.09, 0.09, 0.06, 'coral', seg=6, ink=False)
    k.bx(-1.3, 1.3, -0.4, 1.5, 0.15, 0.55, 'wood2')
    k.bx(-1.25, 1.25, -0.35, 1.45, 0.55, 0.72, 'canvas')
    for x in (-0.65, 0.0, 0.65):
        k.bx(x - 0.28, x + 0.28, 1.15, 1.42, 0.72, 1.12, 'cushion' if x else 'coral')
    k.bx(-1.25, -0.6, -0.35, 0.3, 0.72, 0.76, 'coral', ink=False)
    k.wcol(-1.85, 1.85, -1.85, 1.85, 0.0, 0.15)
    for x in (-1.68, 1.68):
        for y in (-1.68, 1.68):
            k.col(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.15, 2.6)
    k.col(-1.3, 1.3, -0.4, 1.5, 0.15, 0.72)
    k.col(-1.62, 1.62, 1.55, 1.66, 0.15, 2.62)
    k.finish('Cabana', ao=ao)
    # sun loungers [1, 2] (head end +Y)
    for name, cush in (('Lounger_A', 'cushion'), ('Lounger_B', 'coral')):
        k.begin()
        for x in (-0.32, 0.32):
            for y in (-0.8, 0.5):
                k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.3, 'wood2')
        k.bx(-0.34, 0.34, -0.9, 0.55, 0.3, 0.36, 'wood3')
        k.bx(-0.3, 0.3, -0.86, 0.5, 0.36, 0.44, cush)
        k.bxr(0.0, 0.72, 0.62, 0.68, 0.5, 0.1, 'wood3', rot=(-55, 0, 0))
        k.bxr(0.0, 0.69, 0.66, 0.6, 0.42, 0.06, cush, rot=(-55, 0, 0))
        k.bx(-0.3, 0.3, -0.5, -0.1, 0.44, 0.47, 'canvas', ink=False)
        k.col(-0.34, 0.34, -0.9, 0.55, 0.0, 0.44)
        k.col(-0.34, 0.34, 0.55, 0.92, 0.0, 0.85)
        k.finish(name, ao=ao)
    # thatched beach umbrella with a side table and two drinks
    k.begin()
    k.cyl(0, 0, 0, 0.04, 0.04, 2.35, 'bamboo', seg=6)
    cone_roof(k, 0, 0, 2.2, 1.25, 2.8, seg=8, th=0.12)
    k.cyl(0.35, -0.3, 0.0, 0.05, 0.05, 0.5, 'wood2', seg=6)
    k.cyl(0.35, -0.3, 0.5, 0.24, 0.24, 0.04, 'wood3', seg=8)
    k.cyl(0.28, -0.25, 0.54, 0.04, 0.035, 0.14, 'bloom', seg=5)
    k.cyl(0.43, -0.36, 0.54, 0.04, 0.035, 0.12, 'coral', seg=5)
    k.col(-0.05, 0.05, -0.05, 0.05, 0.0, 2.3)
    k.col(0.12, 0.58, -0.53, -0.07, 0.0, 0.54)
    k.finish('Umbrella', ao=ao)
    # tiki torch (the flame is its glow companion Torch_Flame)
    k.begin()
    k.cyl(0, 0, 0, 0.055, 0.045, 1.85, 'bamboo', seg=6)
    for z in (0.6, 1.2):
        k.cyl(0, 0, z, 0.062, 0.062, 0.04, 'bamboo2', seg=6, caps=False, ink=False)
    k.cyl(0, 0, 1.8, 0.07, 0.16, 0.28, 'thatch2', seg=6)
    k.cyl(0, 0, 2.08, 0.1, 0.1, 0.02, 'barkD', seg=6, ink=False)
    k.col(-0.08, 0.08, -0.08, 0.08, 0.0, 2.08)
    k.finish('Torch', ao=ao)
    k.begin()
    k.cyl(0, 0, 2.1, 0.11, 0.02, 0.36, 'flame', seg=5, ink=False)
    k.cyl(0, 0, 2.11, 0.06, 0.01, 0.22, 'flame2', seg=5, ink=False)
    k.finish('Torch_Flame', ao=False)


# ================================================================ furniture and props
def build_props(k, ao):
    # rattan lounge set [3, 2]: sofa (back to +Y), two armchairs, a coffee table
    k.begin()
    k.bx(-1.2, 1.2, 0.35, 0.95, 0.0, 0.42, 'wood3')
    k.bx(-1.2, 1.2, 0.8, 0.95, 0.42, 0.9, 'wood3')
    k.bx(-1.07, 1.07, 0.38, 0.79, 0.42, 0.55, 'canvas')
    for x in (-0.6, 0.6):
        k.bx(x - 0.45, x + 0.45, 0.62, 0.8, 0.55, 0.85, 'cushion')
    for sx in (-1, 1):
        k.bx(1.08 if sx > 0 else -1.2, 1.2 if sx > 0 else -1.08, 0.35, 0.79, 0.42, 0.65, 'wood3')
        x = sx * 1.05
        k.bx(x - 0.38, x + 0.38, -0.95, -0.25, 0.0, 0.4, 'wood3')
        k.bx(x - 0.38, x + 0.38, -0.95, -0.82, 0.4, 0.8, 'wood3')
        k.bx(x - 0.34, x + 0.34, -0.82, -0.28, 0.4, 0.52, 'canvas')
    k.bx(-0.5, 0.5, -0.45, 0.15, 0.0, 0.38, 'wood2')
    k.cyl(0.0, -0.15, 0.38, 0.12, 0.08, 0.12, 'stone2', seg=6)
    k.col(-1.2, 1.2, 0.35, 0.95, 0.0, 0.9)
    for sx in (-1, 1):
        k.col(sx * 1.05 - 0.38, sx * 1.05 + 0.38, -0.95, -0.25, 0.0, 0.8)
    k.col(-0.5, 0.5, -0.45, 0.15, 0.0, 0.38)
    k.finish('LoungeSet', ao=ao)
    # stone planter with a young palm
    rnd = random.Random(221)
    k.begin()
    k.cyl(0, 0, 0, 0.3, 0.42, 0.7, 'stone', seg=8)
    k.cyl(0, 0, 0.7, 0.44, 0.44, 0.08, 'stone2', seg=8)
    k.cyl(0, 0, 0.74, 0.38, 0.38, 0.02, 'barkD', seg=8, ink=False)
    palm(k, rnd, 0, 0, 2.2, lean=0.08, fronds=6, flen=1.4, fw=0.5, r=(0.07, 0.05), rings=2, nuts=0, z0=0.74, seg=5)
    k.col(-0.36, 0.36, -0.36, 0.36, 0.0, 0.8)
    k.finish('Planter', ao=ao)
    # kayak rack [3, 1]
    k.begin()
    for x in (-1.3, 1.3):
        k.beam((x - 0.045, -0.4, 0.0), (x - 0.045, 0.0, 1.45), 0.08, 'wood2')
        k.beam((x + 0.045, 0.4, 0.0), (x + 0.045, 0.0, 1.45), 0.08, 'wood2')
        for z in (0.45, 0.95):
            k.bx(x - 0.05, x + 0.05, -0.3, 0.3, z - 0.04, z + 0.04, 'wood')
    for z, c in ((0.49, 'coral'), (0.99, 'cushion'), (1.38, 'bloom')):
        pts = [(-1.5, 0, z + 0.12), (1.5, 0, z + 0.12)] + [(x, s * 0.3, z + dz) for x in (-0.6, 0.6) for s in (-1, 1) for dz in (0.0, 0.2)]
        k.hullp(pts, c)
    k.col(-1.4, 1.4, -0.42, 0.42, 0.0, 1.45)
    k.finish('Kayaks', ao=ao)
    # towel hut [3, 2]: closed kiosk, counter to -Y, little thatch roof
    k.begin()
    k.bx(-1.45, 1.45, -0.95, -0.7, 0.0, 1.05, 'wood2')
    k.bx(-1.5, 1.5, -1.0, -0.6, 1.05, 1.12, 'wood3')
    k.bx(-1.45, 1.45, 0.75, 0.95, 0.0, 2.25, 'bamboo')
    for sx in (-1, 1):
        k.bx(sx * 1.45 - (0.2 if sx > 0 else 0), sx * 1.45 + (0.2 if sx < 0 else 0), -0.7, 0.75, 0.0, 2.25, 'bamboo')
        k.cyl(sx * 1.35, -0.85, 1.12, 0.06, 0.06, 1.13, 'wood', seg=6)
    hip_roof(k, -1.9, 1.9, -1.45, 1.35, 2.3, 0.9, 3.25, th=0.14)
    cols = ['cushion', 'coral', 'canvas', 'bloom', 'water2', 'pink']
    for i in range(3):
        for j in range(4):
            x = -1.0 + i * 1.0
            k.bx(x - 0.35, x + 0.35, 0.45, 0.74, 0.3 + j * 0.42, 0.66 + j * 0.42, cols[(i * 4 + j) % 6])
    for i in range(3):
        k.bx(-1.1 + i * 0.75, -0.5 + i * 0.75, -0.95, -0.65, 1.12, 1.2 + 0.05 * i, cols[i], ink=False)
    k.bx(-1.2, 1.2, -1.006, -0.95, 0.35, 0.85, 'canvas', ink=False)
    k.text('TOWELS', 0.0, -1.012, 0.45, 0.32, 'cushion', maxw=2.0)
    k.col(-1.5, 1.5, -1.0, 0.95, 0.0, 1.12)
    k.col(-1.45, 1.45, -0.7, 0.95, 1.12, 2.25)
    k.finish('TowelHut', ao=ao)
    # signpost (boards to -Y / +Y)
    k.begin()
    k.cyl(0, 0, 0, 0.07, 0.06, 2.4, 'wood2', seg=6)
    for z, word, ang in ((2.05, 'LOBBY', 12), (1.6, 'CANOPY VILLAS', -14), (1.15, 'BEACH', 8)):
        k.push(0, 0, ang)
        k.bx(0.08, 1.15, -0.04, 0.04, z, z + 0.3, 'wood3')
        k.hullp([(1.15, y, zz) for y in (-0.04, 0.04) for zz in (z, z + 0.3)] + [(1.32, -0.04, z + 0.15), (1.32, 0.04, z + 0.15)], 'wood3')
        k.text(word, 0.66, -0.044, z + 0.08, 0.16, 'woodD', font='cond', maxw=0.95)
        k.text(word, 0.66, 0.044, z + 0.08, 0.16, 'woodD', font='cond', maxw=0.95, face='y+')
        k.pop()
    k.col(-0.08, 0.08, -0.08, 0.08, 0.0, 2.4)
    k.finish('Signpost', ao=ao)
    # supply crates
    for name, stack in (('Crate_A', False), ('Crate_B', True)):
        k.begin()
        def crate(x, y, z, s, yaw):
            k.push(x, y, yaw, z=z)
            k.bx(-s, s, -s, s, 0.0, 2 * s, 'crate')
            for e in (-1, 1):
                k.qy(-s + 0.03, s - 0.03, s * 0.9, s * 1.1, e * (s + 0.004), e, 'wood2')
                k.qx(-s + 0.03, s - 0.03, s * 0.9, s * 1.1, e * (s + 0.004), e, 'wood2')
            k.pop()
        crate(0, 0, 0, 0.44, 0)
        k.text('PALMYRA', 0.0, -0.448, 0.5, 0.14, 'woodD', font='cond', maxw=0.8)
        k.text('COVE', 0.0, -0.448, 0.25, 0.12, 'woodD', font='cond', maxw=0.8)
        if stack:
            crate(0.05, 0.02, 0.88, 0.28, 18)
        k.col(-0.44, 0.44, -0.44, 0.44, 0.0, 0.88)
        if stack:
            k.col(-0.3, 0.38, -0.32, 0.36, 0.88, 1.44)
        k.finish(name, ao=ao)
    # broken-down golf cart [2, 3] (front to -Y): the front-left wheel is off and lies beside it, the body rests on
    # a crate, the roof canopy is bent down at that corner
    k.begin()
    k.bx(-0.6, 0.6, -1.3, 1.25, 0.32, 0.52, 'metal2')
    k.hullp([(x, y, z) for x in (-0.62, 0.62) for (y, z) in ((-1.36, 0.45), (-1.36, 0.9), (-0.9, 1.0), (-0.75, 0.52))], 'cart')
    k.bx(-0.6, 0.6, -0.55, 0.1, 0.52, 0.78, 'cart')
    k.bx(-0.56, 0.56, -0.5, 0.05, 0.78, 0.92, 'canvas')
    k.bx(-0.56, 0.56, 0.0, 0.12, 0.92, 1.35, 'canvas')
    k.bx(-0.6, 0.6, 0.15, 1.25, 0.52, 0.85, 'cart')
    k.bx(-0.55, 0.55, 0.6, 1.2, 0.85, 1.3, 'metal')
    k.text('PALMYRA COVE', 0.0, -1.366, 0.6, 0.12, 'cushion', maxw=1.0, font='serif')
    k.beam((-0.18, -0.75, 0.95), (-0.25, -0.5, 1.25), 0.04, 'tire', ink=False)
    k.cyl(-0.25, -0.5, 1.25, 0.17, 0.17, 0.04, 'tire', seg=8, rot=(30, 0, 0))
    for (x, y, on) in ((-0.6, -0.95, False), (0.6, -0.95, True), (-0.6, 0.85, True), (0.6, 0.85, True)):
        if on:
            k.cyl(x + (0.12 if x > 0 else -0.12), y, 0.26, 0.26, 0.26, 0.16, 'tire', seg=10, rot=(0, 90, 0))
            k.cyl(x + (0.1 if x > 0 else -0.1), y, 0.26, 0.1, 0.1, 0.17, 'metal', seg=6, rot=(0, 90, 0), ink=False)
    k.cyl(-0.98, -0.2, 0.0, 0.26, 0.26, 0.16, 'tire', seg=10)   # the lost wheel, lying flat
    k.cyl(-0.98, -0.2, 0.16, 0.1, 0.1, 0.01, 'metal', seg=6, ink=False)
    k.bx(-0.55, -0.15, -1.15, -0.75, 0.0, 0.32, 'crate')
    for (x, y, top) in ((-0.55, -0.85, 1.65), (0.55, -0.85, 1.9), (-0.55, 1.15, 1.9), (0.55, 1.15, 1.9)):
        k.cyl(x, y, 0.87 if y > 0 else 0.92, 0.03, 0.03, top - (0.87 if y > 0 else 0.92), 'metal', seg=5)
    k.hullp([(-0.7, -1.05, 1.62), (0.7, -1.05, 1.9), (-0.7, 1.3, 1.9), (0.7, 1.3, 1.9), (-0.7, -1.05, 1.68), (0.7, -1.05, 1.96), (-0.7, 1.3, 1.96), (0.7, 1.3, 1.96)],
            lambda f: 'leaf' if f.normal.z > 0.3 else 'leafD')
    k.col(-0.62, 0.62, -1.36, 1.25, 0.0, 1.3)
    k.col(-1.24, -0.72, -0.46, 0.06, 0.0, 0.17)
    k.finish('GolfCart', ao=ao)
    # hammock on bamboo posts [3, 1]
    k.begin()
    for x in (-1.38, 1.38):
        bamboo_post(k, x, 0.0, 0.0, 1.6, r=0.07)
    pts = []
    for i in range(7):
        u = i / 6
        x = -1.0 + 2.0 * u
        z = 1.05 - 0.55 * 4 * u * (1 - u)
        for y in (-0.38, 0.38):
            pts.append((x, y * (0.4 + 0.6 * 4 * u * (1 - u)), z))
    for i in range(6):
        a, b = pts[i * 2:i * 2 + 2], pts[i * 2 + 2:i * 2 + 4]
        k.hullp(a + b + [(p[0], p[1], p[2] - 0.05) for p in a + b], 'coral' if i % 2 else 'canvas')
    for sx in (-1, 1):
        k.beam((sx * 1.38, 0, 1.3), (sx * 1.0, 0, 1.05), 0.03, 'rope', ink=False)
    k.col(-1.45, -1.31, -0.07, 0.07, 0.0, 1.6)
    k.col(1.31, 1.45, -0.07, 0.07, 0.0, 1.6)
    k.col(-1.0, 1.0, -0.36, 0.36, 0.5, 1.0)
    k.finish('Hammock', ao=ao)


# ================================================================ gate, shutter, hatch
def build_gate(k, ao):
    rnd = random.Random(231)
    k.begin()
    for sx in (-1, 1):
        x = sx * 1.85
        k.bx(x - 0.32, x + 0.32, -0.32, 0.32, 0.0, 0.5, 'stone')
        k.cyl(x, 0, 0.5, 0.22, 0.2, 3.6, 'wood', seg=8)
        k.cyl(x, 0, 1.4, 0.235, 0.235, 0.12, 'rope', seg=8, caps=False, ink=False)
        blob(k, rnd, sx * 2.55, 0.05, 0.0, 0.5, 0.5, 3.4, leafcol('frond3', 'leaf', 'leafD'), n=6)
        flowers(k, rnd, [(sx * 2.55 + rnd.uniform(-0.2, 0.2), -0.48, rnd.uniform(0.8, 2.8)) for _ in range(3)], 'hibis', 0.1)
    k.bx(-2.4, 2.4, -0.25, 0.25, 4.1, 4.4, 'woodD')
    hip_roof(k, -2.9, 2.9, -1.0, 1.0, 4.65, 1.9, 5.7, th=0.2)
    k.bx(-1.55, 1.55, -0.33, -0.25, 3.45, 4.05, 'woodD', ink=False)
    k.text('PALMYRA COVE', 0.0, -0.334, 3.58, 0.34, 'thatch3', maxw=2.9, font='serif')
    k.bx(-1.55, 1.55, 0.25, 0.33, 3.45, 4.05, 'woodD', ink=False)
    k.text('PALMYRA COVE', 0.0, 0.334, 3.58, 0.34, 'thatch3', maxw=2.9, face='y+', font='serif')
    for sx in (-1, 1):
        k.cyl(sx * 1.85, -0.38, 2.6, 0.12, 0.1, 0.28, 'teal', seg=6)
    k.finish('GateFrame', ao=ao)
    k.begin()
    Hs, n = 3.05, 12
    for i in range(n):
        x = -1.5 + (i + 0.5) * 3.0 / n
        k.cyl(x, 0, 0.0, 0.12, 0.12, Hs - 0.06 * (i % 2), 'bamboo' if i % 2 else 'bamboo2', seg=6, ink=False)
    for z in (0.9, 2.2):
        k.bx(-1.5, 1.5, -0.18, -0.12, z, z + 0.14, 'rope', ink=False)
    for i in range(8):
        k.bx(-1.5 + i * 3 / 8, -1.5 + (i + 1) * 3 / 8, -0.1, 0.1, 0.0, 0.42, 'ink' if i % 2 else 'amber', ink=False)
    obj = k.finish('GateShutter', ao=False)
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)
    k.tris[k.prefix + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.2, 0.12, 'stone', seg=16)
    k.cyl(0, 0, 0.12, 0.95, 0.95, 0.02, 'teal', seg=16, ink=False)
    for i in range(8):
        a = i / 8 * math.pi * 2
        k.cyl(math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12, 0.06, 0.06, 0.05, 'amber', seg=6)
    k.finish('Hatch', ao=ao)


# ================================================================ backdrop: overwater bungalows and a jetty
def build_backdrop_built(k):
    k.begin()   # overwater bungalow on stilts (sea level 0)
    for x in (-2.2, 2.2):
        for y in (-1.8, 1.8):
            k.cyl(x, y, -0.6, 0.12, 0.12, 2.3, 'wood2', seg=5)
    k.bx(-2.6, 2.6, -2.6, 2.2, 1.6, 1.8, 'wood3')
    k.bx(-2.0, 2.0, -0.6, 2.0, 1.8, 3.8, 'bamboo')
    k.qy(-0.6, 0.6, 2.0, 3.2, -0.604, -1, 'woodD')
    hip_roof(k, -2.7, 2.7, -1.6, 2.6, 4.0, 1.0, 6.2, th=0.2)
    k.finish('Backdrop_Bungalow')
    k.begin()   # jetty: 12 m of planks on piles (along Y)
    k.bx(-0.9, 0.9, -6.0, 6.0, 1.4, 1.6, 'wood3')
    for y in (-5.5, -2.0, 1.5, 5.0):
        for x in (-0.8, 0.8):
            k.cyl(x, y, -0.6, 0.1, 0.1, 2.4, 'wood2', seg=5)
    k.finish('Backdrop_Jetty')


def build_built(k, ao):
    build_decks(k, ao)
    build_villas(k, ao)
    build_lobby(k, ao)
    build_pool(k, ao)
    build_beach(k, ao)
    build_props(k, ao)
    build_gate(k, ao)
    build_backdrop_built(k)
