"""INKBOLT kit-riviera: the zone walls (see rv_base.py for the conventions).

Zone 1, the ground floor (9 m rooms, two-sided interior modules): white plaster over a marble skirting and a dado of
sea-glass panels under a blue rail, the belt course at the gallery's height, a white cornice; arched French windows
to the sea in pairs (each cell one half of the arch, SW_A / SW_B) between white pilasters (SW_P); doorways; the closed
doors of the guest suites; the restaurant's service doors; the corridor fronts of the walk-in suites.
Zone 2, the pool terrace: the hotel's white stucco facades (four storeys to 14.4 m and a terracotta eave) in 3 m bays
of a window between the two leaves of its blue shutters (F_ShA, F_Win, F_ShB: the leaves stand on the cells either
side), wrought-iron balconettes on the first floor; the podium's spa front (PW_*) under the roof garden's parapet;
the sea balustrade and the infinity pool's vanishing edge on the cliff.
"""
import math

from rv_base import (H, DECK, WALLH, FH, WATER, RKit, srt, txt, disc, vdisc, frame_y, arch_pts, shutter, balconette,
                     bougainvillea, potted)
from hotel_base import sconce, painting, flowers

Y0 = -0.497          # a module's face plane (3 mm in from the cell edge: a corner neighbour's bands end on it)


# ================================================================ zone 1: interior walls
def iw_face(k, kind, v=0, dz=0.0):
    """One face of an interior module (face at y = Y0, facing -Y). dz lifts the protruding bands (the _V modules of
    N-S runs, so bands crossing in a room corner never share a plane)."""
    y = Y0
    k.bx(-0.5, 0.5, y - 0.03, y, dz, 0.16 + dz, 'marble2')
    k.bx(-0.5, 0.5, y - 0.02, y, 0.16 + dz, 1.04 + dz, 'stucco', ink=False)
    for (x0, x1) in ((-0.43, -0.04), (0.04, 0.43)):
        k.qy(x0, x1, 0.27, 0.93, y - 0.023, -1, 'silk')
        frame_y(k, x0 + 0.03, x1 - 0.03, 0.3, 0.9, y - 0.026, -1, 'silk2', 0.018)
    k.bx(-0.5, 0.5, y - 0.05, y, 1.04 + dz, 1.1 + dz, 'wine', ink=False)
    k.bx(-0.5, 0.5, y - 0.06, y, DECK - 0.4 + dz, DECK - 0.03 + dz, 'stuccoD')
    k.bx(-0.5, 0.5, y - 0.03, y, DECK - 0.52 + dz, DECK - 0.4 + dz, 'stucco', ink=False)
    frame_y(k, -0.38, 0.38, DECK + 0.35, H - 0.95, y - 0.004, -1, 'stuccoD', 0.025)
    k.bx(-0.5, 0.5, y - 0.12, y, H - 0.42 + dz, H - 2 * dz, 'stone')
    for i in range(3):
        x = -0.4 + i * 0.33
        k.bx(x, x + 0.12, y - 0.15, y - 0.12, H - 0.42, H - 0.32, 'stuccoD', ink=False)
    if kind == 'Sconce':
        sconce(k, 0, y - 0.003, 2.7)
        sconce(k, 0, y - 0.003, 6.6)
    elif kind == 'Art':
        painting(k, 0, y - 0.003, 1.65, 0.7, 0.9 if v % 2 else 1.05, scheme=v % 4, frame='stone')
        painting(k, 0, y - 0.003, 5.4, 0.74, 1.8, scheme=(v + 1) % 4, frame='gold')
    elif kind == 'Mirror':
        k.bx(-0.36, 0.36, y - 0.05, y, 1.35, 3.6, 'ivory')
        k.qy(-0.3, 0.3, 1.41, 3.54, y - 0.053, -1, 'crystal2')
        k.poly([(-0.2, y - 0.056, 2.0), (-0.12, y - 0.056, 2.0), (0.05, y - 0.056, 2.9), (-0.03, y - 0.056, 2.9)], 'glint', (0, -1, 0))
        k.bx(-0.1, 0.1, y - 0.07, y, 3.6, 3.74, 'ivory', ink=False)
        sconce(k, 0, y - 0.003, 6.6)


def inner_wall(k, kind, v=0, dz=0.0):
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stucco', ink=False)
    iw_face(k, kind, v, dz)
    k.push(0, 0, 180)
    iw_face(k, kind, v + 1, dz)
    k.pop()
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def suite_front(k, kind):
    """One-sided corridor wall in front of a walk-in suite (the suite piece draws the room side)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stucco', ink=False)
    iw_face(k, kind, 0)
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def core(k):
    """Four-sided white block (corners, junctions, ends of runs): marble skirting, the belt course, the cornice."""
    k.begin()
    k.bx(-0.497, 0.497, -0.497, 0.497, 0.16, H - 0.36, 'stucco')
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.16, 'marble2', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, DECK - 0.4, DECK - 0.04, 'stuccoD', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, H - 0.36, H - 0.012, 'stone', ink=False)
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def suite_door(k, num=0):
    """A closed guest-suite door in the corridor wall (face toward -Y): white panelled leaf in a moulded architrave,
    a brass plate and handle, the 'do not disturb' card, a sconce over it."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stucco', ink=False)
    y = Y0
    k.bx(-0.5, 0.5, y - 0.03, y, 0, 0.16, 'marble2')
    k.bx(-0.5, 0.5, y - 0.06, y, DECK - 0.4, DECK - 0.03, 'stuccoD')
    k.bx(-0.5, 0.5, y - 0.12, y, H - 0.42, H, 'stone')
    frame_y(k, -0.38, 0.38, DECK + 0.35, H - 0.95, y - 0.004, -1, 'stuccoD', 0.025)
    for sx in (-1, 1):
        a, b = srt(sx * 0.4, sx * 0.49)
        k.bx(a, b, y - 0.07, y, 0.16, 2.62, 'ivory')                       # architrave jambs
    k.bx(-0.4, 0.4, y - 0.07, y, 2.5, 2.62, 'ivory')                        # and head
    k.bx(-0.4, 0.4, y - 0.04, y - 0.006, 0.0, 2.5, 'wine2')                      # the leaf, set back in the frame
    for (z0, z1) in ((0.2, 1.1), (1.3, 2.3)):
        k.qy(-0.32, -0.03, z0, z1, y - 0.043, -1, 'wine')
        k.qy(0.03, 0.32, z0, z1, y - 0.043, -1, 'wine')
    k.bx(-0.52, 0.52, y - 0.1, y, 2.62, 2.78, 'stone')
    k.bx(0.27, 0.33, y - 0.08, y - 0.04, 1.0, 1.06, 'brass', ink=False)
    k.qy(-0.1, 0.1, 1.55, 1.71, y - 0.046, -1, 'brass')
    txt(k, str(100 + num), 0, y - 0.049, 1.63, 0.1, 'black', font='display', valign='m', maxw=0.17)
    k.qy(0.2, 0.3, 0.6, 0.8, y - 0.046, -1, 'emerald')
    sconce(k, 0, y - 0.003, 3.3, arms=1)
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def service_door(k):
    """The restaurant's swing doors to the kitchen (face toward -Y): two steel-faced leaves with porthole windows, kick
    plates, a CUISINE sign over them."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stucco', ink=False)
    y = Y0
    k.bx(-0.5, 0.5, y - 0.06, y, DECK - 0.4, DECK - 0.03, 'stuccoD')
    k.bx(-0.5, 0.5, y - 0.12, y, H - 0.42, H, 'stone')
    k.bx(-0.48, 0.48, y - 0.06, y, 0, 2.5, 'ivory')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.015, s * 0.42)
        k.qy(x0, x1, 0.02, 2.36, y - 0.063, -1, 'steel')
        k.qy(x0 + 0.02, x1 - 0.02, 0.05, 0.32, y - 0.066, -1, 'steel2')
        vdisc(k, s * 0.215, y - 0.066, 1.62, 0.13, 'black', n=10)
        vdisc(k, s * 0.215, y - 0.069, 1.62, 0.1, 'crystal2', n=10)
    k.bx(-0.5, 0.5, y - 0.1, y, 2.5, 2.92, 'navy')
    txt(k, 'CUISINE', 0, y - 0.103, 2.71, 0.17, 'cream', font='sans', valign='m', maxw=0.86)
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def doorway(k, part, lintel=2.7):
    """Passage cell (two-sided): open below the lintel, a white architrave on the outer jamb(s), a fanlight of blue
    glass in a radial frame over the opening, the belt course and the cornice."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, lintel, H, 'stucco', ink=False)
    for f in (-1, 1):
        y = f * 0.497

        def B(x0, x1, d0, d1, z0, z1, c, ink=True):
            a, b = srt(y + f * d0, y + f * d1)
            k.bx(x0, x1, a, b, z0, z1, c, ink=ink)
        B(-0.497, 0.497, 0, 0.09, lintel, lintel + 0.16, 'ivory')
        B(-0.5, 0.5, 0, 0.06, DECK - 0.4, DECK - 0.03, 'stuccoD')
        B(-0.5, 0.5, 0, 0.12, H - 0.42, H, 'stone')
        # the fanlight: a blue glass half-disc segment per cell with white glazing bars
        pts = [(-0.48, y + f * 0.004, lintel + 0.22), (0.48, y + f * 0.004, lintel + 0.22), (0.48, y + f * 0.004, lintel + 0.95), (-0.48, y + f * 0.004, lintel + 0.95)]
        k.poly(pts, 'glassT', (0, f, 0))
        for i in range(4):
            x = -0.36 + i * 0.24
            k.poly([(x - 0.012, y + f * 0.007, lintel + 0.22), (x + 0.012, y + f * 0.007, lintel + 0.22), (x + 0.012, y + f * 0.007, lintel + 0.95), (x - 0.012, y + f * 0.007, lintel + 0.95)], 'ivory', (0, f, 0))
        k.poly([(-0.48, y + f * 0.010, lintel + 0.56), (0.48, y + f * 0.010, lintel + 0.56), (0.48, y + f * 0.010, lintel + 0.59), (-0.48, y + f * 0.010, lintel + 0.59)], 'ivory', (0, f, 0))
        B(-0.5, 0.5, 0, 0.08, lintel + 0.95, lintel + 1.08, 'stone')
        frame_y(k, -0.38, 0.38, DECK + 0.35, H - 0.95, y + f * 0.004, f, 'stuccoD', 0.025)
    for (side, xs) in (('L', -1), ('R', 1)):
        if part == side:
            x0, x1 = srt(xs * 0.494, xs * 0.34)
            k.bx(x0, x1, -0.6, 0.6, 0, lintel + 0.22, 'ivory')
            k.bx(x0 - 0.01, x1 + 0.01, -0.62, 0.62, 0, 0.16, 'marble2', ink=False)
    k.col(-0.5, 0.5, -0.5, 0.5, WALLH, H)
    return k


def sea_win(k, side):
    """One cell of an arched French window pair in the outer wall (room toward -Y), side +1: the arch's centre line on
    this cell's +X edge. White-painted frame, French-door transom, drapes of the Riviera blue; the sea behind."""
    k.begin()
    sx = side
    ox, far = 0.5 * sx, -0.5 * sx
    AZ, R = 7.2, 1.0
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.42, 'stucco')
    k.bx(-0.5, 0.5, -0.53, -0.5, 0, 0.16, 'marble2', ink=False)
    k.bx(-0.5, 0.5, -0.56, -0.497, 0.42, 0.5, 'marble')
    a0, a1 = (math.pi, math.pi / 2) if sx > 0 else (0.0, math.pi / 2)
    curve = arch_pts(ox, AZ, R, a0, a1, 8)
    pts = curve + [(curve[-1][0], H), (far, H)]
    if sx < 0:
        pts = list(reversed(pts))
    k.prism(pts, -0.5, 0.5, 'stucco')
    k.bx(-0.5, 0.5, -0.62, -0.5, H - 0.42, H, 'stone')
    k.bx(-0.5, 0.5, -0.56, -0.5, DECK - 0.4, DECK - 0.03, 'stuccoD')
    fe = far * 0.994
    k.bx(min(fe, fe + sx * 0.08), max(fe, fe + sx * 0.08), -0.05, 0.05, 0.45, AZ, 'ivory')
    oe = ox * 0.994
    k.bx(min(oe, oe - sx * 0.04), max(oe, oe - sx * 0.04), -0.04, 0.04, 0.45, AZ + R, 'ivory')
    ta, tb = srt(fe + sx * 0.08, oe - sx * 0.04)
    for z in ((2.7, 2.78), (DECK - 0.36, DECK - 0.24), (AZ - 0.06, AZ)):
        k.bx(ta, tb, -0.03, 0.03, z[0], z[1], 'ivory', ink=False)
    for i in range(len(curve) - 1):
        (x0, z0), (x1, z1) = curve[i], curve[i + 1]
        q0 = (ox + (x0 - ox) * 0.92, AZ + (z0 - AZ) * 0.92)
        q1 = (ox + (x1 - ox) * 0.92, AZ + (z1 - AZ) * 0.92)
        k.prism([(x0, z0), (x1, z1), q1, q0] if sx < 0 else [(x0, z0), q0, q1, (x1, z1)], -0.025, 0.025, 'ivory', ink=False)
    for a in ((2.2, 2.75) if sx > 0 else (0.94, 0.39)):
        k.beam((ox + math.cos(a) * 0.16, 0, AZ + math.sin(a) * 0.16), (ox + math.cos(a) * R * 0.92, 0, AZ + math.sin(a) * R * 0.92), 0.03, 'ivory', ink=False)
    k.bx(min(oe, oe - sx * 0.13), max(oe, oe - sx * 0.13), -0.58, -0.5, AZ + R - 0.1, AZ + R + 0.35, 'stone')
    for s in (-1, 1):
        lo = -0.38 if sx > 0 else -0.22
        for (z0, z1) in ((0.8, 2.5), (2.95, 3.9), (4.6, 6.6)):
            k.poly([(lo, s * 0.006, z0 + 0.3), (lo + 0.05, s * 0.006, z0 + 0.3), (lo + 0.05 + 0.3, s * 0.006, z1 - 0.2), (lo + 0.3, s * 0.006, z1 - 0.2)], 'glint', (0, s, 0))
    # drapes in the reveal on the pier side, a brass tie-back, the pelmet
    dx0, dx1 = srt(far + sx * 0.02, far + sx * 0.28)
    k.bx(dx0, dx1, -0.42, -0.3, 0.5, AZ - 0.34, 'wine')
    for i in range(3):
        fx = dx0 + 0.04 + i * 0.08
        k.qy(fx, fx + 0.03, 0.55, AZ - 0.34, -0.423, -1, 'wine2')
    k.bx(dx0 - 0.01, dx1 + 0.01, -0.44, -0.29, 2.9, 3.0, 'brass', ink=False)
    k.bx(-0.5, 0.5, -0.46, -0.28, AZ - 0.3, AZ - 0.05, 'wine2')
    k.bx(-0.5, 0.5, -0.47, -0.27, AZ - 0.34, AZ - 0.3, 'brass', ink=False)
    return k


def sea_pier(k):
    """White pilaster between window pairs: marble plinth, a fluted shaft, a sconce on each storey, a capital."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stucco', ink=False)
    k.bx(-0.36, 0.36, -0.58, -0.5, 0, 0.7, 'marble2')
    k.bx(-0.3, 0.3, -0.56, -0.497, 0.7, H - 0.95, 'marble')
    for x in (-0.18, -0.06, 0.06, 0.18):
        k.qy(x - 0.02, x + 0.02, 0.8, H - 0.95, -0.563, -1, 'marble2')
    k.bx(-0.38, 0.38, -0.62, -0.5, H - 0.85, H - 0.6, 'stone')
    k.bx(-0.497, 0.497, -0.6, -0.494, DECK - 0.4, DECK - 0.03, 'stuccoD', ink=False)
    k.bx(-0.497, 0.497, -0.62, -0.494, H - 0.42, H - 0.004, 'stone')
    sconce(k, 0, -0.563, 2.9)
    sconce(k, 0, -0.563, 6.6)
    return k


def gate_frame(k):
    """Portal of the 3 m doors between the zones (both faces alike): a white architrave and pediment with the hotel's
    crest, white plaster to the 9 m ceiling. Closes the trail end (|x| <= 2.5)."""
    k.begin()
    D3 = 3.2
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.5)
        k.bx(x0, x1, -0.5, 0.5, 0, H, 'stucco')
        a0, a1 = srt(s * 1.497, s * 1.78)
        k.bx(a0, a1, -0.6, 0.6, 0, D3, 'ivory')
        b0, b1 = srt(s * 1.494, s * 1.72)
        k.bx(b0, b1, -0.62, 0.62, 0, 0.16, 'marble2', ink=False)
    k.bx(-1.78, 1.78, -0.6, 0.6, D3, D3 + 0.3, 'stone')
    k.bx(-1.5, 1.5, -0.5, 0.5, D3 + 0.3, H, 'stucco')
    for f in (-1, 1):
        y = f * 0.6
        k.poly([(-1.95, y + f * 0.003, D3 + 0.4), (1.95, y + f * 0.003, D3 + 0.4), (0, y + f * 0.003, D3 + 1.25)], 'stuccoD', (0, f, 0))
        k.poly([(-1.6, y + f * 0.006, D3 + 0.5), (1.6, y + f * 0.006, D3 + 0.5), (0, y + f * 0.006, D3 + 1.1)], 'stone', (0, f, 0))
        k.poly([(math.cos(a) * 0.3, y + f * 0.009, D3 + 0.78 + math.sin(a) * 0.24) for a in [i * math.pi * 2 / 12 for i in range(12)]], 'wine', (0, f, 0))
        txt(k, 'R', 0, y + f * 0.012, D3 + 0.78, 0.3, 'gold', face='y-' if f < 0 else 'y+', font='serif', valign='m')
        yb0, yb1 = srt(f * 0.5, f * 0.56)
        k.bx(-2.5, 2.5, yb0, yb1, DECK - 0.4, DECK - 0.03, 'stuccoD', ink=False)
        k.bx(-2.5, 2.5, srt(f * 0.5, f * 0.6)[0], srt(f * 0.5, f * 0.6)[1], H - 0.42, H, 'stone')
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        for s in (-1, 1):
            k.bx(s * 2.15 - 0.3, s * 2.15 + 0.3, -0.53, -0.5, 0.14, 0.2, 'marble2', ink=False)
            sconce(k, s * 2.15, -0.5, 2.5, arms=1)
        k.pop()
    k.col(-2.5, -1.5, -0.6, 0.6, 0, H)
    k.col(1.5, 2.5, -0.6, 0.6, 0, H)
    return k


def gate_shutter(k):
    """A pair of white French doors with small panes (they roll up like every gate)."""
    k.begin()
    Hs = 3.05
    k.bx(-1.5, 1.5, -0.05, 0.05, 0, Hs, 'ivory', ink=False)
    for f in (-1, 1):
        y = f * 0.053
        for i in range(2):
            x0 = -1.42 + i * 1.47
            for j in range(4):
                z0 = 0.95 + j * 0.5
                for q in range(2):
                    k.qy(x0 + q * 0.68, x0 + q * 0.68 + 0.6, z0, z0 + 0.42, y, f, 'glassT')
            k.qy(x0, x0 + 1.34, 0.15, 0.8, y, f, 'stuccoD')
        k.qy(-0.015, 0.015, 0.1, Hs - 0.1, f * 0.056, f, 'stuccoD')
        k.qy(-1.5, 1.5, Hs - 0.18, Hs - 0.1, f * 0.059, f, 'brass')
    return k


def trail_wall(k, kind=''):
    """The orangery passage between the zones (1 m along Blender Y, corridor toward +X): white plaster over a blue
    and white tiled dado, frosted arched windows, wall lanterns, half the passage's ceiling at 4.2 m (the theme's 9 m
    ceiling plane stays hidden above it) with a strip of cove light."""
    k.begin()
    TH = 4.2
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, H, 'stucco', ink=False)
    x = 0.253
    k.bx(0.25, 0.28, -0.5, 0.5, 0, 0.14, 'marble2', ink=False)
    k.qx(-0.5, 0.5, 0.14, 1.0, x, 1, 'silk')
    for i in range(4):
        yy = -0.5 + i * 0.25
        k.qx(yy + 0.02, yy + 0.23, 0.22, 0.42, x + 0.003, 1, 'wine' if i % 2 else 'ivory')
        k.qx(yy + 0.02, yy + 0.23, 0.52, 0.72, x + 0.003, 1, 'ivory' if i % 2 else 'wine')
    k.bx(0.25, 0.3, -0.5, 0.5, 1.0, 1.06, 'wine', ink=False)
    k.bx(0.25, 0.34, -0.5, 0.5, TH - 0.3, TH - 0.08, 'stone', ink=False)
    k.bx(0.25, 2.25, -0.5, 0.5, TH - 0.08, TH, 'stucco')
    k.qz(0.42, 0.56, -0.5, 0.5, TH - 0.083, -1, 'glow')
    if kind == 'Win':
        pts = [(-0.34, 1.3), (0.34, 1.3)] + [(math.cos(a) * 0.34, 3.0 + math.sin(a) * 0.34) for a in [i * math.pi / 8 for i in range(9)]]
        k.poly([(x + 0.003, p[0], p[1]) for p in pts], 'crystal2', (1, 0, 0))
        for yy in (-0.12, 0.12):
            k.qx(yy - 0.015, yy + 0.015, 1.3, 3.3, x + 0.006, 1, 'ivory')
        for z in (1.9, 2.5):
            k.qx(-0.34, 0.34, z - 0.015, z + 0.015, x + 0.009, 1, 'ivory')
        k.bx(0.25, 0.33, -0.42, 0.42, 1.22, 1.3, 'marble')
    elif kind == 'Lamp':
        k.bx(0.25, 0.29, -0.08, 0.08, 2.3, 2.6, 'black')
        k.beam((0.29, 0, 2.45), (0.45, 0, 2.55), 0.025, 'black', ink=False)
        k.cyl(0.47, 0, 2.3, 0.08, 0.1, 0.3, 'glow', seg=6)
        k.cyl(0.47, 0, 2.6, 0.1, 0.03, 0.08, 'black', seg=6, ink=False)
    elif kind == 'Art':
        k.push(0.25, 0, 90)
        painting(k, 0, -0.003, 1.5, 0.72, 0.9, scheme=1, s=-1, frame='gold')
        k.pop()
    return k


def hatch(k):
    """Exit: the hotel's lift down to the private beach: a brass car (open to the south) with a mirrored back, a
    handrail, a glowing ceiling, floor chevrons and the PLAGE sign."""
    k.begin()
    W, D, Hc = 1.3, 1.25, 2.7
    k.bx(-W, W, -D, D, 0, 0.06, 'nero')
    for i in range(3):
        y = -0.7 + i * 0.5
        k.poly([(-0.6, y, 0.065), (0, y + 0.34, 0.065), (0, y + 0.48, 0.065), (-0.6, y + 0.14, 0.065)], 'gold', (0, 0, 1))
        k.poly([(0, y + 0.34, 0.066), (0.6, y, 0.066), (0.6, y + 0.14, 0.066), (0, y + 0.48, 0.066)], 'gold', (0, 0, 1))
    k.bx(-W, W, D - 0.08, D, 0.06, Hc, 'bronze')
    k.qy(-W + 0.15, W - 0.15, 1.0, Hc - 0.25, D - 0.083, -1, 'crystal2')
    for s in (-1, 1):
        x0, x1 = srt(s * W, s * (W - 0.08))
        k.bx(x0, x1, -D, D - 0.08, 0.06, Hc, 'bronze')
        k.poly([(s * (W - 0.083), -D + 0.15, 0.9), (s * (W - 0.083), D - 0.2, 0.9), (s * (W - 0.083), D - 0.2, Hc - 0.25), (s * (W - 0.083), -D + 0.15, Hc - 0.25)], 'wine', (-s, 0, 0))
        k.bx(min(s * (W - 0.12), s * (W - 0.16)), max(s * (W - 0.12), s * (W - 0.16)), -D + 0.2, D - 0.2, 0.92, 0.97, 'brass', ink=False)
    k.bx(-W, W, -D, D, Hc, Hc + 0.12, 'bronze')
    k.qz(-W + 0.2, W - 0.2, -D + 0.2, D - 0.2, Hc - 0.003, -1, 'glow')
    k.bx(-W - 0.1, W + 0.1, -D - 0.1, -D + 0.05, Hc + 0.12, Hc + 0.45, 'bronze')
    k.qy(-0.6, 0.6, Hc + 0.16, Hc + 0.41, -D - 0.103, -1, 'wine2')
    txt(k, 'PLAGE', 0, -D - 0.106, Hc + 0.285, 0.17, 'gold', font='display', valign='m')
    return k


# ================================================================ zone 2: the facades round the pool terrace
FL = (4.5, 7.8, 11.1)        # upper floor levels (window sills 0.55 above)


def f_shell(k):
    """the facade block of one cell: plinth, rusticated ground floor, the first-floor string course, the cornice and
    the terracotta eave"""
    k.bx(-0.5, 0.5, -0.497, 0.5, 0, FH, 'stucco', ink=False)
    k.bx(-0.5, 0.5, -0.56, -0.497, 0, 0.42, 'stone2')
    for z in (1.1, 1.8, 2.5, 3.2):
        k.qy(-0.5, 0.5, z - 0.02, z + 0.02, -0.5, -1, 'stuccoD')
    k.bx(-0.5, 0.5, -0.6, -0.497, 4.15, 4.5, 'stone')
    k.bx(-0.5, 0.5, -0.56, -0.497, FL[1] - 0.1, FL[1], 'stuccoD', ink=False)
    k.bx(-0.5, 0.5, -0.56, -0.497, FL[2] - 0.1, FL[2], 'stuccoD', ink=False)
    k.bx(-0.5, 0.5, -0.72, -0.497, FH - 0.5, FH, 'stone')
    k.bx(-0.5, 0.5, -0.66, -0.497, FH - 0.7, FH - 0.5, 'stuccoD', ink=False)
    # the eave: a sloped terracotta roof edge over the cornice (prism in the YZ plane along X)
    k.prism_y([(-0.95, FH), (-0.7, FH), (0.5, FH + 1.4), (0.5, FH + 1.55), (-0.95, FH + 0.18)], -0.5, 0.5, 'terra')


def f_window(k, x0, x1, z0, z1, y=-0.497):
    """a glazed window (dark glass, white frame, glazing bars, a glint) on the face plane y"""
    k.qy(x0, x1, z0, z1, y - 0.006, -1, 'ivory')
    k.qy(x0 + 0.05, x1 - 0.05, z0 + 0.05, z1 - 0.05, y - 0.009, -1, 'navy2')
    xm = (x0 + x1) / 2
    k.qy(xm - 0.018, xm + 0.018, z0 + 0.05, z1 - 0.05, y - 0.012, -1, 'ivory')
    zm = z0 + (z1 - z0) * 0.62
    k.qy(x0 + 0.05, x1 - 0.05, zm - 0.018, zm + 0.018, y - 0.015, -1, 'ivory')
    k.poly([(x0 + 0.1, y - 0.018, z0 + 0.3), (x0 + 0.16, y - 0.018, z0 + 0.3), (x0 + 0.3, y - 0.018, zm - 0.1), (x0 + 0.24, y - 0.018, zm - 0.1)], 'glint', (0, -1, 0))


def f_win(k, closed_top=False):
    """the middle cell of a bay: a tall French window on the ground floor, a window on each upper floor (a
    wrought-iron balconette on the first), drip mouldings; closed_top: the top floor's shutters are closed."""
    k.begin()
    f_shell(k)
    f_window(k, -0.42, 0.42, 0.42, 3.55)
    k.bx(-0.5, 0.5, -0.58, -0.497, 3.6, 3.72, 'stone', ink=False)
    for i, z in enumerate(FL):
        zs = z + 0.5
        if closed_top and i == 2:
            shutter(k, -0.42, 0.0, zs, zs + 1.75, -0.506, n=10)
            shutter(k, 0.0, 0.42, zs, zs + 1.75, -0.506, n=10)
            k.qy(-0.44, 0.44, zs - 0.02, zs + 1.77, -0.503, -1, 'ivory')
        else:
            f_window(k, -0.4, 0.4, zs, zs + 1.75)
        k.bx(-0.48, 0.48, -0.6, -0.497, zs - 0.08, zs, 'stone', ink=False)
        k.bx(-0.48, 0.48, -0.58, -0.497, zs + 1.8, zs + 1.9, 'stone', ink=False)
        if i == 0:
            balconette(k, -0.46, 0.46, z + 0.02, -0.5)
    return k


def f_shut(k, sx, closed_top=False):
    """a cell beside a window: the blue shutter leaves folded open against the wall on the window's side (sx: the
    window lies toward local sx * X), on every floor; a lantern on the ground floor"""
    k.begin()
    f_shell(k)
    e = 0.5 * sx
    a, b = srt(e - sx * 0.44, e - sx * 0.02)
    shutter(k, a, b, 0.5, 3.5, -0.506, n=16)
    for i, z in enumerate(FL):
        if closed_top and i == 2:
            continue
        zs = z + 0.5
        shutter(k, a, b, zs, zs + 1.75, -0.506, n=10)
    # a bracket lantern between the bays on the ground floor
    lx = -sx * 0.28
    k.bx(lx - 0.05, lx + 0.05, -0.53, -0.497, 2.55, 2.85, 'black', ink=False)
    k.beam((lx, -0.53, 2.75), (lx, -0.75, 2.8), 0.03, 'black', ink=False)
    k.cyl(lx, -0.78, 2.45, 0.07, 0.09, 0.3, 'glow', seg=6)
    k.cyl(lx, -0.78, 2.75, 0.09, 0.03, 0.08, 'black', seg=6, ink=False)
    return k


def f_plain(k, bloom=False, seed=0):
    """a facade cell without a window (ends of a front): stucco, quoins; bloom: bougainvillea climbing from a pot"""
    k.begin()
    f_shell(k)
    for i in range(10):
        z0 = 0.5 + i * 1.38
        if z0 + 1.2 > FH - 0.7:
            break
        w = 0.42 if i % 2 else 0.3
        if i >= 3:
            k.bx(-0.496, -0.5 + w, -0.525, -0.501, z0, z0 + 1.2, 'stone', ink=False)
    if bloom:
        potted(k, 0, -0.85, 0.24, 0.5, 'geranium')
        k.beam((0, -0.75, 0.5), (0.1, -0.56, 3.2), 0.05, 'walnut2', ink=False)
        bougainvillea(k, 0.05, -0.5, 3.3, 0.9, 1.6, seed=seed)
        k.col(-0.25, 0.25, -1.1, -0.6, 0, 0.6)
    return k


def f_door(k):
    """the ground floor of a bay as a glazed double door under a fanlight and a blue awning (upper floors as f_win)"""
    k.begin()
    f_shell(k)
    k.qy(-0.46, 0.46, 0.0, 3.6, -0.503, -1, 'ivory')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.02, s * 0.42)
        k.qy(x0, x1, 0.05, 2.6, -0.506, -1, 'navy2')
        k.poly([(x0 + 0.06, -0.509, 0.5), (x0 + 0.12, -0.509, 0.5), (x0 + 0.24, -0.509, 1.6), (x0 + 0.18, -0.509, 1.6)], 'glint', (0, -1, 0))
        k.bx(min(s * 0.06, s * 0.12), max(s * 0.06, s * 0.12), -0.54, -0.506, 1.05, 1.1, 'brass', ink=False)
    k.qy(-0.42, 0.42, 2.7, 3.5, -0.506, -1, 'glassT')
    k.bx(-0.5, 0.5, -0.56, -0.5, 2.6, 2.7, 'ivory', ink=False)
    # awning: a sloped canvas with blue and white stripes and a valance
    for i in range(4):
        x = -0.5 + i * 0.25
        k.poly([(x, -0.5 - 0.004, 3.85), (x + 0.25, -0.5 - 0.004, 3.85), (x + 0.25, -1.3, 3.15), (x, -1.3, 3.15)], 'wine' if i % 2 else 'canvas', (0, -0.66, 0.75))
    k.bx(-0.5, 0.5, -1.33, -1.28, 2.95, 3.15, 'wine', ink=False)
    for i, z in enumerate(FL):
        zs = z + 0.5
        f_window(k, -0.4, 0.4, zs, zs + 1.75)
        k.bx(-0.48, 0.48, -0.6, -0.497, zs - 0.08, zs, 'stone', ink=False)
        if i == 0:
            balconette(k, -0.46, 0.46, z + 0.02, -0.5)
    return k


def f_corner(k):
    """the outer corner of the ring (both faces hidden behind the neighbours): a plain block to the eave"""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, FH, 'stucco')
    k.bx(-0.5, 0.5, -0.5, 0.5, FH, FH + 1.2, 'terra')
    return k


def f_gate_top(k):
    """the facade over a 5 m gate portal (placed by the theme's backdrop), from the frame's 9 m top to the eave: the
    hotel's name in gilt letters on a white band, windows either side of a central balcony"""
    k.begin()
    W = 2.5
    k.bx(-W, W, -0.497, 0.5, H, FH, 'stucco', ink=False)
    k.bx(-W, W, -0.72, -0.497, FH - 0.5, FH, 'stone')
    k.bx(-W, W, -0.66, -0.501, FH - 0.7, FH - 0.5, 'stuccoD', ink=False)
    k.prism_y([(-0.95, FH), (-0.7, FH), (0.5, FH + 1.4), (0.5, FH + 1.55), (-0.95, FH + 0.18)], -W, W, 'terra')
    k.bx(-W, W, -0.58, -0.497, H, H + 0.1, 'stuccoD', ink=False)
    k.bx(-W, W, -0.56, -0.497, FL[2] - 0.1, FL[2], 'stuccoD', ink=False)
    for x in (-1.6, 1.6):
        f_window(k, x - 0.4, x + 0.4, FL[2] + 0.5, FL[2] + 2.25)
        k.bx(x - 0.48, x + 0.48, -0.6, -0.497, FL[2] + 0.42, FL[2] + 0.5, 'stone', ink=False)
    f_window(k, -0.45, 0.45, FL[2] + 0.5, FL[2] + 2.3)
    balconette(k, -0.7, 0.7, FL[2] + 0.02, -0.5)
    k.qy(-2.2, 2.2, 9.3, 10.6, -0.503, -1, 'wine2')
    txt(k, 'HOTEL RIVIERA', 0, -0.506, 9.95, 0.62, 'gold', font='serif', valign='m', maxw=4.2)
    return k


def f_back(k):
    """the backs of the facades seen from outside along the exit lane: a plain wall"""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 4.2, 'stucco')
    return k


# ---------------------------------------------------------------- the podium (spa wing) under the roof garden
def p_parapet(k, gap=False):
    """the roof garden's parapet on a podium cell: a stucco wall 1.0 m over the 4.5 m roof with a stone coping and a
    band of blue tiles (collision over the roof); gap: no parapet (the head of a stair)"""
    if gap:
        return
    k.bx(-0.5, 0.5, -0.5, -0.2, DECK, DECK + 0.92, 'stucco')
    k.bx(-0.5, 0.5, -0.54, -0.16, DECK + 0.92, DECK + 1.02, 'stone')
    for i in range(4):
        x = -0.5 + i * 0.25
        for s in (-1, 1):
            yy = -0.5 - 0.003 if s < 0 else -0.2 + 0.003
            k.qy(x + 0.03, x + 0.22, DECK + 0.35, DECK + 0.55, yy, s, 'wine' if i % 2 else 'tile')
    k.col(-0.5, 0.5, -0.5, -0.2, DECK, DECK + 1.02)


def p_shell(k, top=DECK):
    k.bx(-0.5, 0.5, -0.497, 0.5, 0, top, 'stucco', ink=False)
    k.bx(-0.5, 0.5, -0.56, -0.497, 0, 0.38, 'stone2')
    k.bx(-0.5, 0.5, -0.62, -0.497, top - 0.32, top, 'stone')


def p_win(k, gap=False):
    """the spa's front: an arched window with white glazing bars and open blue shutters"""
    k.begin()
    p_shell(k)
    f_window(k, -0.3, 0.3, 0.7, 3.3)
    pts = [(math.cos(a) * 0.3, -0.509, 3.3 + math.sin(a) * 0.3) for a in [i * math.pi / 8 for i in range(9)]]
    k.poly([(0.3, -0.509, 3.3)] + pts[1:-1] + [(-0.3, -0.509, 3.3)], 'navy2', (0, -1, 0))
    for s in (-1, 1):
        a, b = srt(s * 0.3, s * 0.48)
        shutter(k, a, b, 0.7, 3.3, -0.506, n=14)
    k.bx(-0.36, 0.36, -0.62, -0.497, 0.62, 0.7, 'stone', ink=False)
    p_parapet(k, gap)
    return k


def p_door(k, sign=None):
    """a glazed door into the spa with a blue awning; sign: lettering over it"""
    k.begin()
    p_shell(k)
    k.qy(-0.46, 0.46, 0.0, 3.0, -0.503, -1, 'ivory')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.02, s * 0.42)
        k.qy(x0, x1, 0.05, 2.9, -0.506, -1, 'navy2')
        k.poly([(x0 + 0.06, -0.509, 0.5), (x0 + 0.12, -0.509, 0.5), (x0 + 0.24, -0.509, 1.6), (x0 + 0.18, -0.509, 1.6)], 'glint', (0, -1, 0))
    for i in range(4):
        x = -0.5 + i * 0.25
        k.poly([(x, -0.504, 3.5), (x + 0.25, -0.504, 3.5), (x + 0.25, -1.25, 2.95), (x, -1.25, 2.95)], 'wine' if i % 2 else 'canvas', (0, -0.6, 0.8))
    if sign:
        k.qy(-0.5, 0.5, 3.62, 4.0, -0.503, -1, 'wine2')
        txt(k, sign, 0, -0.506, 3.81, 0.17, 'gold', font='serif', valign='m', maxw=0.92, clip=None)
    p_parapet(k)
    return k


def p_plain(k, bloom=False, seed=0, gap=False):
    k.begin()
    p_shell(k)
    if bloom:
        potted(k, 0, -0.85, 0.26, 0.55, 'geranium')
        k.beam((0, -0.75, 0.55), (0.08, -0.56, 2.6), 0.05, 'walnut2', ink=False)
        bougainvillea(k, 0.0, -0.5, 3.0, 0.95, 1.5, seed=seed)
        k.col(-0.28, 0.28, -1.12, -0.58, 0, 0.62)
    else:
        k.qy(-0.32, 0.32, 1.1, 2.6, -0.503, -1, 'silk')
        frame_y(k, -0.32, 0.32, 1.1, 2.6, -0.506, -1, 'wine', 0.04)
    p_parapet(k, gap)
    return k


def p_corner(k, gap=False):
    """an inner or outer corner of the podium: a plain block with its parapet on both open faces"""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, DECK, 'stucco')
    if not gap:
        k.bx(-0.5, 0.5, -0.5, 0.5, DECK, DECK + 0.92, 'stucco')
        k.bx(-0.54, 0.54, -0.54, 0.54, DECK + 0.92, DECK + 1.02, 'stone')
        k.col(-0.5, 0.5, -0.5, 0.5, DECK, DECK + 1.02)
    return k


# ---------------------------------------------------------------- the cliff edge
def sea_bal(k, lamp=False):
    """the stone balustrade over the cliff (sea toward +Y): a plinth, turned balusters, the handrail; lamp: a white
    lamp post on a pier"""
    k.begin()
    k.bx(-0.5, 0.5, -0.3, 0.3, 0, 0.22, 'stone')
    k.bx(-0.5, 0.5, -0.34, 0.34, 0.95, 1.1, 'stone')
    for i in range(3):
        x = -0.333 + i * 0.333
        k.cyl(x, 0, 0.22, 0.07, 0.1, 0.32, 'stone', seg=6, ink=False)
        k.cyl(x, 0, 0.54, 0.1, 0.06, 0.41, 'stone', seg=6, ink=False)
    if lamp:
        k.bx(-0.16, 0.16, -0.36, 0.36, 0, 1.18, 'stone')
        k.cyl(0, 0, 1.18, 0.05, 0.04, 2.1, 'ivory', seg=6)
        k.cyl(0, 0, 3.28, 0.16, 0.2, 0.36, 'glow', seg=8)
        k.cyl(0, 0, 3.64, 0.2, 0.04, 0.16, 'ivory', seg=8)
    return k


def inf_edge(k):
    """the infinity pool's vanishing edge (pool toward -Y, the cliff toward +Y): the water runs on to the lip and
    falls in a sheet into the catch channel below the edge; a frameless glass screen on the far side"""
    k.begin()
    k.qz(-0.5, 0.5, -0.5, -0.06, WATER, 1, 'water')
    k.qz(-0.5, 0.5, -0.22, -0.12, WATER + 0.003, 1, 'waterL')
    k.bx(-0.5, 0.5, -0.06, 0.04, -1.6, WATER - 0.004, 'tile')
    k.qy(-0.5, 0.5, -1.4, WATER - 0.01, 0.043, 1, 'waterL')
    k.bx(-0.5, 0.5, 0.04, 0.5, -1.6, -1.2, 'stone2')
    k.qz(-0.5, 0.5, 0.06, 0.48, -1.25, 1, 'water')
    k.bx(-0.5, 0.5, 0.42, 0.5, -1.2, 0.95, 'glassT', ink=False)
    k.poly([(-0.3, 0.417, 0.2), (-0.24, 0.417, 0.2), (0.0, 0.417, 0.8), (-0.06, 0.417, 0.8)], 'glint', (0, -1, 0))
    k.bx(-0.5, 0.5, 0.41, 0.5, 0.95, 0.99, 'chrome', ink=False)
    return k
