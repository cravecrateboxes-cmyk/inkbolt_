"""INKBOLT kit-hotel: walls, gate, service-stair trail, hatch, stand, grand stair, balustrades, columns, ceilings and
floor inlays (see hotel_base.py for the conventions).

Facade windows come in arched pairs: an arch spans two cells, so each cell draws one half. Win_A has its arch's
centre line on its local +X edge, Win_B on its -X edge (the theme's wall chooser picks the half from the cell's place
in the bay and the way the engine turns the module). Revolve_A / _B are the same halves round a revolving door.
"""
import math

from hotel_base import (H, DECK, RH, DROP, HKit, srt, txt, disc, vdisc, ring, sconce, painting, flowers, palm)
import hotel_detail as D


def glints_x(k, x, y0, y1, z0, z1, s=-1, y=None):
    """Two slanted streaks on a glass plane x..(y0..y1) facing s * Y at depth y."""
    w = y1 - y0
    for (f, ww) in ((0.15, 0.06), (0.32, 0.03)):
        a = y0 + w * f
        h = (z1 - z0) * 0.3
        zz = z0 + (z1 - z0) * 0.35
        k.poly([(a, y, zz), (a + ww, y, zz), (a + ww + h * 0.4, y, zz + h), (a + h * 0.4, y, zz + h)], 'glint', (0, s, 0))


# ================================================================ lobby facade
def arch_pts(cx, cz, r, a0, a1, n=8):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cz + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]


def win_half(k, side, revolve=False):
    """One cell of an arched window pair (room toward -Y). side +1: the arch centre on this cell's +X edge."""
    k.begin()
    sx = side
    ox = 0.5 * sx                 # arch centre line x
    far = -0.5 * sx               # the cell edge at the pier
    AZ, R = 7.4, 1.0              # arch springing height, radius (spans the two cells)
    # stone: plinth (sill) and the solid wall above the arch, full depth
    if not revolve:
        k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.55, 'stone')
        k.bx(-0.5, 0.5, -0.56, -0.5, 0, 0.14, 'nero', ink=False)
        k.bx(-0.5, 0.5, -0.53, -0.5, 0.5, 0.58, 'stone2', ink=False)
    # the spandrel over the arch: polygon between the arch curve and the cornice, extruded through the wall
    a0, a1 = (math.pi, math.pi / 2) if sx > 0 else (0.0, math.pi / 2)
    curve = arch_pts(ox, AZ, R, a0, a1, 8)
    pts = curve + [(curve[-1][0], H), (far, H)]
    if sx < 0:
        pts = list(reversed(pts))
    k.prism(pts, -0.5, 0.5, 'stone')
    # mezzanine belt course (4.1 - 4.5), a frieze and the cornice
    k.bx(-0.5, 0.5, -0.5, 0.5, DECK - 0.4, DECK, 'stone')
    k.bx(-0.5, 0.5, -0.56, -0.5, DECK - 0.36, DECK - 0.04, 'stone2', ink=False)
    k.bx(-0.5, 0.5, -0.6, -0.5, H - 0.35, H, 'stone2')
    for i in range(3):
        x = -0.42 + i * 0.33
        k.bx(x, x + 0.12, -0.63, -0.6, H - 0.35, H - 0.25, 'stone', ink=False)
    # bronze frame in the glass plane (y = 0): outer jamb (at the pier), the shared centre mullion (half), transoms
    fe = far * 0.994                      # 3 mm in from the cell edge (the stone courses own that plane)
    k.bx(min(fe, fe + sx * 0.07), max(fe, fe + sx * 0.07), -0.05, 0.05, 0.55, AZ, 'bronze')
    oe = ox * 0.994
    k.bx(min(oe, oe - sx * 0.035), max(oe, oe - sx * 0.035), -0.04, 0.04, 3.3 if revolve else 0.55, AZ + R, 'bronze')
    for z in (((6.2, 6.26), (AZ - 0.06, AZ)) if revolve else ((2.7, 2.78), (6.2, 6.26), (AZ - 0.06, AZ))):
        ta, tb = srt(fe + sx * 0.07, oe - sx * 0.035)
        k.bx(ta, tb, -0.03, 0.03, z[0], z[1], 'bronze', ink=False)
    # the arch moulding (a band of bronze segments on the glass plane) and two fanlight bars
    for i in range(len(curve) - 1):
        (x0, z0), (x1, z1) = curve[i], curve[i + 1]
        r_in = 0.93
        q0 = (ox + (x0 - ox) * r_in, AZ + (z0 - AZ) * r_in)
        q1 = (ox + (x1 - ox) * r_in, AZ + (z1 - AZ) * r_in)
        k.prism([(x0, z0), (x1, z1), q1, q0] if sx < 0 else [(x0, z0), q0, q1, (x1, z1)], -0.025, 0.025, 'bronze', ink=False)
    for a in ((2.2, 2.75) if sx > 0 else (0.94, 0.39)):
        k.beam((ox + math.cos(a) * 0.16, 0, AZ + math.sin(a) * 0.16), (ox + math.cos(a) * R * 0.93, 0, AZ + math.sin(a) * R * 0.93), 0.03, 'bronze', ink=False)
    # moulded architrave round the arch on the room face, and a deep marble sill
    D.arch_architrave(k, ox, AZ, 0.96, 1.1, a0, a1 + (0.012 if sx > 0 else -0.012), 8)
    if not revolve:
        D.window_sill(k)
    # keystone half and a gilt rosette in the spandrel
    k.bx(min(oe, oe - sx * 0.14), max(oe, oe - sx * 0.14), -0.56, -0.5, AZ + R - 0.12, H - 0.36, 'stone2')
    vdisc(k, far + sx * 0.18, -0.503, AZ + R + 0.05, 0.11, 'gold', n=10)
    # glints on the glass (both faces)
    for s in (-1, 1):
        lo = -0.4 if sx > 0 else -0.25
        for (z0, z1) in ((0.8, 2.6), (2.9, 4.0), (4.6, 6.1)):
            k.poly([(lo, s * 0.006, z0 + 0.3), (lo + 0.05, s * 0.006, z0 + 0.3), (lo + 0.05 + 0.3, s * 0.006, z1 - 0.2), (lo + 0.3, s * 0.006, z1 - 0.2)], 'glint', (0, s, 0))
    # drapes hanging in the reveal on the pier side, a gold tie-back, a pelmet
    dx0, dx1 = srt(far + sx * 0.02, far + sx * 0.3)
    k.bx(dx0, dx1, -0.42, -0.3, 0.56, AZ - 0.34, 'wine')
    for i in range(3):
        fx = dx0 + 0.04 + i * 0.09
        k.qy(fx, fx + 0.03, 0.6, AZ - 0.34, -0.423, -1, 'wine2')
    k.bx(dx0 - 0.01, dx1 + 0.01, -0.44, -0.29, 3.0, 3.1, 'gold', ink=False)
    k.bx(-0.5, 0.5, -0.46, -0.28, AZ - 0.3, AZ - 0.05, 'wine2')
    k.bx(-0.5, 0.5, -0.47, -0.27, AZ - 0.34, AZ - 0.3, 'gold', ink=False)
    if revolve:
        revolving_half(k, sx)
    return k


def revolving_half(k, sx):
    """Half of a revolving door set in the facade (drum centre on the shared edge, on the glass line): a bronze
    canopy drum with a gilt band, the curved glass enclosure on the far side, two of the four wings with push bars,
    the central post and the gilt name band over the doors."""
    ox = 0.5 * sx
    R = 0.95
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.03, 'nero', ink=False)              # threshold
    base = math.pi / 2 if sx > 0 else -math.pi / 2                        # the half of the circle in this cell
    pts = [(ox, 0.0)] + [(ox + math.cos(base + i * math.pi / 8) * R, math.sin(base + i * math.pi / 8) * R) for i in range(9)]
    k.prism_z(pts, 2.5, 2.78, 'bronze')
    pts2 = [(ox - sx * 0.003, 0.0)] + [(ox - sx * 0.003 + math.cos(base + i * math.pi / 8) * (R + 0.012), math.sin(base + i * math.pi / 8) * (R + 0.012)) for i in range(9)]
    k.prism_z(pts2, 2.6, 2.68, 'gold', ink=False)
    # the curved enclosure (bronze rails, glass) round the far side: -/+ 50 degrees about the side axis
    side = math.pi if sx > 0 else 0.0
    for (z0, z1, c) in ((0.03, 0.12, 'bronze'), (2.38, 2.5, 'bronze')):
        k.arc(ox, 0, R - 0.06, R, side - 0.85, side + 0.85, 5, z0, z1, c, ink=False)
    k.arc(ox, 0, R - 0.04, R - 0.02, side - 0.85, side + 0.85, 5, 0.12, 2.38, 'crystal2', ink=False)
    # the central post and two wings (glass in a bronze frame) with brass push bars
    k.bx(min(ox, ox - sx * 0.05), max(ox, ox - sx * 0.05), -0.05, 0.05, 0.03, 2.5, 'brass', ink=False)
    for a in ((math.pi * 0.75, math.pi * 1.25) if sx > 0 else (math.pi * 0.25, -math.pi * 0.25)):
        r0, r1 = 0.07, R - 0.08
        cxw, cyw = ox + math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2
        deg = math.degrees(a)
        k.m.box((cxw, cyw, 1.25), (r1 - r0, 0.035, 2.3), 'bronze', rot=(0, 0, deg), bevel=False)
        k._mark(False)
        k.m.box((cxw, cyw, 1.25), (r1 - r0 - 0.1, 0.045, 2.1), 'crystal2', rot=(0, 0, deg), bevel=False)
        k._mark(False)
        k.beam((ox + math.cos(a) * 0.2, math.sin(a) * 0.2, 1.05), (ox + math.cos(a) * 0.8, math.sin(a) * 0.8, 1.05), 0.035, 'brass', ink=False)
    # the name band over the doors (each half draws its part of the lettering)
    k.bx(-0.494, 0.494, -0.53, -0.5, 2.85, 3.3, 'nero', ink=False)
    txt(k, 'THE AURELIAN', ox, -0.533, 2.98, 0.2, 'gold', clip=(-0.5 - ox, 0.5 - ox), maxw=1.8)


def win_pier(k):
    """Stone pilaster between window pairs: plinth, fluted shaft, a sconce on each storey, a gilt capital."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone', ink=False)
    k.bx(-0.36, 0.36, -0.58, -0.5, 0, 0.7, 'stone2')
    k.bx(-0.38, 0.38, -0.6, -0.496, 0, 0.14, 'nero', ink=False)
    k.bx(-0.3, 0.3, -0.56, -0.497, 0.7, H - 0.95, 'marble')
    for x in (-0.18, -0.06, 0.06, 0.18):
        k.qy(x - 0.02, x + 0.02, 0.8, H - 0.95, -0.563, -1, 'marble2')
    k.bx(-0.38, 0.38, -0.62, -0.5, H - 0.85, H - 0.6, 'gold')
    k.bx(-0.34, 0.34, -0.6, -0.497, H - 0.95, H - 0.85, 'brass', ink=False)
    k.bx(-0.497, 0.497, -0.6, -0.494, DECK - 0.36, DECK - 0.04, 'stone2', ink=False)
    k.bx(-0.497, 0.497, -0.6, -0.494, H - 0.35, H - 0.004, 'stone2')  # 3 mm in: a corner neighbour's band ends on the wall face
    sconce(k, 0, -0.563, 2.9)
    sconce(k, 0, -0.563, 6.8)
    D.pier_detail(k)
    return k


def core(k):
    """Four-sided block (corners, junctions, lone columns): marble with a black plinth and a stone cornice."""
    k.begin()
    k.bx(-0.497, 0.497, -0.497, 0.497, 0.16, H - 0.33, 'stone')
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.16, 'nero', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, H - 0.33, H - 0.012, 'stone2', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, DECK - 0.34, DECK - 0.06, 'stone2', ink=False)
    D.core_bands(k)
    return k


def gate_side(k):
    """Pier beside a gate (room toward -Y): marble with a brass reveal and a lantern sconce."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone', ink=False)
    k.bx(-0.5, 0.5, -0.56, -0.5, 0, 0.14, 'nero', ink=False)
    k.bx(-0.42, 0.42, -0.54, -0.5, 0.14, DECK - 0.4, 'marble')
    k.qy(-0.03, 0.03, 0.2, DECK - 0.5, -0.543, -1, 'brass')
    k.bx(-0.5, 0.5, -0.56, -0.5, DECK - 0.36, DECK - 0.04, 'stone2', ink=False)
    k.bx(-0.5, 0.5, -0.6, -0.5, H - 0.35, H, 'stone2')
    k.bx(-0.42, 0.42, -0.54, -0.5, DECK, H - 0.35, 'marble')
    sconce(k, 0, -0.543, 2.6, arms=1)
    return k


# ================================================================ interior walls (two-sided)
def panel_face(k, kind, v, dz=0.0):
    """One face of an interior wall module (face at y = -0.5, facing -Y): walnut wainscot, a gilt-framed silk panel,
    the belt course at the mezzanine height, a tall upper panel, the cornice. dz lifts the protruding bands (the _V
    modules of N-S runs): where two runs meet in a room corner their bands cross, at heights 6 mm apart."""
    y = -0.497   # 3 mm in from the cell edge: a corner neighbour's bands end on the cell edge
    k.bx(-0.5, 0.5, y - 0.04, y, dz, 1.0 + dz, 'walnut')
    k.bx(-0.5, 0.5, y - 0.05, y, 1.0 + dz, 1.05 + dz, 'gold', ink=False)
    for (x0, x1) in ((-0.42, -0.06), (0.06, 0.42)):
        k.qy(x0, x1, 0.18, 0.86, y - 0.043, -1, 'walnut2')
    k.qy(-0.5, 0.5, 1.05, DECK - 0.4, y - 0.003, -1, 'silk')
    k.bx(-0.5, 0.5, y - 0.06, y, DECK - 0.4 + dz, DECK + dz, 'stone2')
    k.bx(-0.5, 0.5, y - 0.03, y, DECK - 0.55 + dz, DECK - 0.4 + dz, 'stone', ink=False)
    k.qy(-0.5, 0.5, DECK, H - 0.4, y - 0.003, -1, 'silk')
    k.bx(-0.5, 0.5, y - 0.08, y, H - 0.4 + dz, H - 2 * dz, 'stone2')
    k.bx(-0.37, 0.37, y - 0.1, y - 0.08, H - 0.32, H - 0.24, 'gold', ink=False)
    # gilt mouldings framing the panels
    for (z0, z1) in ((1.25, DECK - 0.75), (DECK + 0.3, H - 0.7)):
        for (a, b, c, d) in ((-0.4, 0.4, z0, z0 + 0.03), (-0.4, 0.4, z1 - 0.03, z1), (-0.4, -0.37, z0 + 0.03, z1 - 0.03), (0.37, 0.4, z0 + 0.03, z1 - 0.03)):
            k.qy(a, b, c, d, y - 0.006, -1, 'gold')
    D.wall_face_detail(k, y, dz, kind)
    if kind == 'Sconce':
        sconce(k, 0, y - 0.003, 2.6)
        sconce(k, 0, y - 0.003, 6.7)
    elif kind == 'Art':
        painting(k, 0, y - 0.003, 1.6, 0.66, 0.9 if v % 2 else 1.1, scheme=v % 4)
        painting(k, 0, y - 0.003, 5.3, 0.7, 1.9, scheme=(v + 1) % 4)
    elif kind == 'Mirror':
        k.bx(-0.36, 0.36, y - 0.05, y, 1.3, 3.5, 'gold')
        k.qy(-0.3, 0.3, 1.36, 3.44, y - 0.053, -1, 'crystal2')
        k.poly([(-0.2, y - 0.056, 2.0), (-0.12, y - 0.056, 2.0), (0.05, y - 0.056, 2.9), (-0.03, y - 0.056, 2.9)], 'glint', (0, -1, 0))
        k.bx(-0.08, 0.08, y - 0.07, y, 3.5, 3.62, 'gold', ink=False)
        sconce(k, 0, y - 0.003, 6.7)


def inner_wall(k, kind, v=0, dz=0.0):
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stone', ink=False)
    panel_face(k, kind, v, dz)
    k.push(0, 0, 180)
    panel_face(k, kind, v + 1, dz)
    k.pop()
    return k


def suite_front(k, kind):
    """One-sided corridor wall in front of a suite (the suite piece draws the room side): the panelled face only."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stone', ink=False)
    panel_face(k, kind, 0)
    return k


def lift_half(k, side):
    """One cell of a pair of bronze lift doors (two-sided interior module; the door pair spans two cells, side +1: the
    pair's centre on this cell's +X edge): an etched leaf, the architrave, an arched floor dial above."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, 0, H, 'stone', ink=False)
    sx = side
    cx = 0.5 * sx
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        s_ = sx if f < 0 else -sx
        c_ = 0.5 * s_
        y = -0.497
        k.bx(-0.5, 0.5, y - 0.04, y, 0, 0.12, 'nero', ink=False)
        lo, hi = srt(c_ * 0.994, c_ - s_ * 0.7)
        k.bx(lo, hi, y - 0.025, y + 0.003, 0.0, 2.55, 'bronze')                 # leaf (half of the pair)
        k.qy(lo + 0.08 if s_ > 0 else lo + 0.05, hi - 0.05 if s_ > 0 else hi - 0.08, 0.3, 2.3, y - 0.028, -1, 'brass')
        k.poly([((lo + hi) / 2, y - 0.031, 0.9), ((lo + hi) / 2 + 0.18, y - 0.031, 1.3), ((lo + hi) / 2, y - 0.031, 1.7), ((lo + hi) / 2 - 0.18, y - 0.031, 1.3)], 'bronze', (0, -1, 0))
        ax0, ax1 = srt(c_ - s_ * 0.7, c_ - s_ * 0.86)
        k.bx(ax0, ax1, y - 0.08, y + 0.006, 0, 2.75, 'gold')                     # architrave jamb
        hx0, hx1 = srt(c_, c_ - s_ * 0.7)
        k.bx(hx0, hx1, y - 0.08, y, 2.55, 2.75, 'gold')
        D.lift_fittings(k, y, c_, s_)
        # floor dial: a half sunburst over the doors
        pts = [(c_, y - 0.01, 2.85)] + [(c_ + math.cos(a) * 0.6, y - 0.01, 2.85 + math.sin(a) * 0.6)
                                         for a in ([math.pi / 2 + i * math.pi / 12 for i in range(7)] if s_ > 0 else [math.pi / 2 - i * math.pi / 12 for i in range(7)])]
        k.poly(pts, 'bronze', (0, -1, 0))
        for i in range(3):
            a = math.pi / 2 + s_ * (0.35 + i * 0.4)
            k.qy(min(c_ + math.cos(a) * 0.45, c_ + math.cos(a) * 0.45 + 0.05), max(c_ + math.cos(a) * 0.45, c_ + math.cos(a) * 0.45 + 0.05),
                 2.85 + math.sin(a) * 0.45 - 0.025, 2.85 + math.sin(a) * 0.45 + 0.025, y - 0.013, -1, 'glow')
        if s_ > 0:
            k.beam((c_, y - 0.016, 2.85), (c_ - 0.3, y - 0.016, 3.25), 0.02, 'black', ink=False)
        k.bx(-0.5, 0.5, y - 0.06, y, DECK - 0.4, DECK, 'stone2')
        k.qy(-0.5, 0.5, DECK, H - 0.4, y - 0.003, -1, 'silk')
        k.bx(-0.5, 0.5, y - 0.08, y, H - 0.4, H, 'stone2')
        k.qy(-0.5, 0.5, 3.4, DECK - 0.4, y - 0.003, -1, 'silk')
        k.pop()
    return k


# ================================================================ guest floor (suites) and passages
def suite_window(k):
    """Facade module behind a suite (room toward -Y): a window to the city with sheers and drapes, a deep sill; the
    suite's ceiling is at 3.3 m (stone above it)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.6, 'stone')
    k.bx(-0.497, 0.497, -0.56, -0.497, 0, 0.12, 'walnut2', ink=False)
    k.bx(-0.497, 0.497, -0.58, -0.494, 0.58, 0.64, 'marble')
    k.bx(-0.5, 0.5, -0.5, 0.5, RH - 0.25, H, 'stone')
    k.bx(-0.5, 0.5, -0.05, 0.05, 0.6, 0.68, 'bronze', ink=False)
    k.bx(-0.5, 0.5, -0.05, 0.05, RH - 0.31, RH - 0.25, 'bronze', ink=False)
    k.bx(-0.5, -0.46, -0.05, 0.05, 0.68, RH - 0.31, 'bronze')
    k.bx(0.46, 0.5, -0.05, 0.05, 0.68, RH - 0.31, 'bronze')
    for s in (-1, 1):
        k.poly([(-0.3, s * 0.006, 1.2), (-0.24, s * 0.006, 1.2), (-0.02, s * 0.006, 2.4), (-0.08, s * 0.006, 2.4)], 'glint', (0, s, 0))
    # sheer at the sides, a velvet drape on one side, a pelmet
    k.bx(-0.48, -0.32, -0.36, -0.3, 0.66, RH - 0.32, 'ivory')
    k.bx(0.32, 0.48, -0.36, -0.3, 0.66, RH - 0.32, 'ivory')
    k.bx(-0.497, -0.34, -0.46, -0.37, 0.64, RH - 0.32, 'navy')
    for x in (-0.46, -0.41):
        k.qy(x, x + 0.02, 0.7, RH - 0.36, -0.463, -1, 'navy2')
    k.bx(-0.5, 0.5, -0.48, -0.296, RH - 0.45, RH - 0.25, 'cream')
    return k


def suite_plaque(k, num):
    """A suite's brass number plate (a floor-layer piece in the corridor cell beside the door, its back against the
    wall: the plate stands on the wall face at the cell's back edge, +Y, 1.6 m up)."""
    k.begin()
    y = 0.5 - 0.012
    k.bx(-0.17, 0.17, y - 0.03, y, 1.45, 1.77, 'brass')
    k.qy(-0.14, 0.14, 1.48, 1.74, y - 0.033, -1, 'gold')
    txt(k, str(num), 0, y - 0.036, 1.61, 0.14, 'black', font='display', valign='m', maxw=0.26)
    return k


def doorway(k, part, lintel=2.7):
    """Passage cell (two-sided): open below `lintel`, a gilt architrave on the outer jamb(s), a carved transom
    panel above. part: 'L' (jamb at local -X), 'R' (jamb at +X), 'M' (no jamb)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.497, 0.497, lintel, H, 'stone', ink=False)
    for f in (-1, 1):
        y = f * 0.497
        y0, y1 = srt(y, y + f * 0.08)
        k.bx(-0.497, 0.497, y0, y1, lintel, lintel + 0.18, 'gold')
        ya, yb = srt(y, y + f * 0.003)
        k.poly([(-0.5, y + f * 0.003, lintel + 0.18), (0.5, y + f * 0.003, lintel + 0.18), (0.5, y + f * 0.003, DECK - 0.4), (-0.5, y + f * 0.003, DECK - 0.4)], 'silk', (0, f, 0))
        k.poly([(-0.5, y + f * 0.003, DECK), (0.5, y + f * 0.003, DECK), (0.5, y + f * 0.003, H - 0.4), (-0.5, y + f * 0.003, H - 0.4)], 'silk', (0, f, 0))
        y2a, y2b = srt(y, y + f * 0.06)
        k.bx(-0.5, 0.5, y2a, y2b, DECK - 0.4, DECK, 'stone2')
        y3a, y3b = srt(y, y + f * 0.08)
        k.bx(-0.5, 0.5, y3a, y3b, H - 0.4, H, 'stone2')
        # transom: a carved walnut panel with a gilt fan
        y4a, y4b = srt(y, y + f * 0.03)
        k.bx(-0.48, 0.48, y4a, y4b, lintel + 0.3, lintel + 0.95, 'walnut')
        k.poly([(0.0, y + f * 0.033, lintel + 0.35)] + [(math.cos(a) * 0.4, y + f * 0.033, lintel + 0.35 + math.sin(a) * 0.5) for a in [i * math.pi / 8 for i in range(9)]], 'gold', (0, f, 0))
    for (side, xs) in (('L', -1), ('R', 1)):
        if part in (side,):
            x0, x1 = srt(xs * 0.494, xs * 0.36)
            k.bx(x0, x1, -0.6, 0.6, 0, lintel + 0.24, 'gold')
    D.doorway_fittings(k, part, lintel)
    return k


# ================================================================ sky deck facade
def sky_glass(k, fin=False):
    """Floor-to-ceiling glazing on the top floor (room toward -Y): half a bronze mullion on each edge, a glass
    balustrade with a brass rail at 1.1 m, transoms, a header at the roof line. fin: a bronze fin pier with an uplight."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.12, 'nero')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.5, s * 0.465)
        k.bx(x0, x1, -0.06, 0.06, 0.12, H - 0.42, 'bronze')
    for z in (3.0, 6.0):
        k.bx(-0.465, 0.465, -0.03, 0.03, z, z + 0.05, 'bronze', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, H - 0.42, H, 'bronze')
    k.bx(-0.497, 0.497, -0.52, -0.497, H - 0.36, H - 0.3, 'gold', ink=False)
    k.bx(-0.5, 0.5, -0.38, -0.31, 1.02, 1.08, 'brass')                              # rail of the glass balustrade
    k.bx(-0.03, 0.03, -0.37, -0.32, 0.12, 1.02, 'bronze', ink=False)
    for s in (-1, 1):
        k.poly([(-0.32, s * 0.004, 1.5), (-0.26, s * 0.004, 1.5), (0.04, s * 0.004, 2.7), (-0.02, s * 0.004, 2.7)], 'glint', (0, s, 0))
        k.poly([(0.05, s * 0.004, 6.6), (0.09, s * 0.004, 6.6), (0.3, s * 0.004, 7.6), (0.26, s * 0.004, 7.6)], 'glint', (0, s, 0))
    for s2 in (-1, 1):
        y = -0.345 + s2 * 0.004
        k.poly([(-0.3, y, 0.35), (-0.22, y, 0.35), (-0.08, y, 0.85), (-0.16, y, 0.85)], 'glint', (0, s2, 0))
        k.poly([(0.18, y, 0.3), (0.22, y, 0.3), (0.34, y, 0.7), (0.3, y, 0.7)], 'glint', (0, s2, 0))
    if fin:
        k.bx(-0.09, 0.09, -0.62, -0.06, 0.5, H - 0.4, 'bronze')
        k.bx(-0.13, 0.13, -0.66, -0.38, 0.12, 0.5, 'nero')
        k.qy(-0.07, 0.07, 0.2, 0.42, -0.663, -1, 'glow')
        k.col(-0.13, 0.13, -0.66, -0.5, 0, 0.5)
    return k


# ================================================================ gate, trail, hatch, stand
def gate_frame(k):
    """Portal of the 3 m service-stair doors (both faces alike): walnut and gilt architrave, a pediment with the
    hotel's crest, stone up to the 9 m ceiling. Closes the trail end (|x| <= 2.5)."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.5)
        k.bx(x0, x1, -0.5, 0.5, 0, H, 'stone')
        a0, a1 = srt(s * 1.497, s * 1.78)
        k.bx(a0, a1, -0.6, 0.6, 0, DROP, 'gold')
        b0, b1 = srt(s * 1.494, s * 1.72)
        k.bx(b0, b1, -0.62, 0.62, 0, 0.16, 'nero', ink=False)
    k.bx(-1.78, 1.78, -0.6, 0.6, DROP, DROP + 0.3, 'gold')
    k.bx(-1.5, 1.5, -0.5, 0.5, DROP + 0.3, H, 'stone')
    for f in (-1, 1):
        y = f * 0.6
        ya, yb = srt(y, y + f * 0.003)
        # pediment over the doors with a cartouche and the crest letter
        k.poly([(-1.95, y + f * 0.003, DROP + 0.4), (1.95, y + f * 0.003, DROP + 0.4), (0, y + f * 0.003, DROP + 1.25)], 'stone2', (0, f, 0))
        k.poly([(-1.6, y + f * 0.006, DROP + 0.5), (1.6, y + f * 0.006, DROP + 0.5), (0, y + f * 0.006, DROP + 1.1)], 'stone', (0, f, 0))
        k.poly([(math.cos(a) * 0.3, y + f * 0.009, DROP + 0.78 + math.sin(a) * 0.24) for a in [i * math.pi * 2 / 12 for i in range(12)]], 'gold', (0, f, 0))
        txt(k, 'A', 0, y + f * 0.012, DROP + 0.78, 0.3, 'wine2', face='y-' if f < 0 else 'y+', font='serif', valign='m')
        yb0, yb1 = srt(f * 0.5, f * 0.56)
        k.bx(-2.5, 2.5, yb0, yb1, DECK - 0.36, DECK - 0.04, 'stone2', ink=False)
        k.bx(-2.5, 2.5, srt(f * 0.5, f * 0.6)[0], srt(f * 0.5, f * 0.6)[1], H - 0.35, H, 'stone2')
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        for s in (-1, 1):
            k.bx(s * 2.15 - 0.3, s * 2.15 + 0.3, -0.53, -0.5, 0.14, 0.2, 'nero', ink=False)
            sconce(k, s * 2.15, -0.5, 2.5, arms=1)
        k.pop()
    k.col(-2.5, -1.5, -0.6, 0.6, 0, H)
    k.col(1.5, 2.5, -0.6, 0.6, 0, H)
    return k


def gate_shutter(k):
    """Bronze security grille: horizontal slats with a wine band, a brass bottom bar."""
    k.begin()
    Hs, n = 3.05, 12
    h = (Hs - 0.3) / n
    for i in range(n):
        z0 = 0.3 + i * h
        k.bx(-1.5, 1.5, -0.05, 0.05, z0, z0 + h, 'bronze' if i % 2 else 'brass', ink=False)
        for f in (-1, 1):
            k.qy(-1.5, 1.5, z0 + h - 0.02, z0 + h - 0.008, f * 0.053, f, 'walnut2')
    for f in (-1, 1):
        k.qy(-1.5, 1.5, 1.4, 1.62, f * 0.056, f, 'wine')
    k.bx(-1.5, 1.5, -0.07, 0.07, 0, 0.3, 'brass', ink=False)
    return k


def trail_wall(k, kind=''):
    """Back-of-house service corridor side (1 m along Blender Y, corridor toward +X): painted block wall with a green
    dado, a steel handrail, a conduit run, and half the corridor's drop ceiling at 3.2 m with a strip light."""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, H, 'block')
    k.qx(-0.5, 0.5, 0.0, 1.1, 0.253, 1, 'svc')
    k.qx(-0.5, 0.5, 1.1, 1.16, 0.256, 1, 'block2')
    for z in (0.4, 0.8, 1.6, 2.0, 2.4, 2.8):
        k.qx(-0.5, 0.5, z - 0.008, z + 0.008, 0.256 if z > 1.2 else 0.256, 1, 'block2' if z > 1.2 else 'emerald2')
    k.bx(0.25, 0.31, -0.5, 0.5, 0, 0.1, 'nero', ink=False)                              # skirting
    k.bx(0.25, 2.25, -0.5, 0.5, DROP, DROP + 0.08, 'block')                             # drop ceiling (half)
    k.qz(0.5, 0.7, -0.5, 0.5, DROP - 0.003, -1, 'glow')                                 # strip light
    k.bx(0.25, 0.3, -0.5, 0.5, 2.6, 2.68, 'steel2', ink=False)                          # conduit
    if kind not in ('Lift', 'Hose'):
        k.bx(0.3, 0.36, -0.5, 0.5, 0.9, 0.95, 'steel')                                  # handrail
        k.bx(0.25, 0.3, -0.03, 0.03, 0.88, 0.95, 'steel2', ink=False)
    if kind == 'Pipe':       # riser pipes with valves and labels
        for (y, c) in ((-0.25, 'red'), (0.15, 'svc')):
            k.cyl(0.36, y, 0, 0.07, 0.07, DROP, c, seg=8)
            k.cyl(0.36, y, 1.4, 0.1, 0.1, 0.08, 'steel2', seg=8, ink=False)
            k.qx(y - 0.06, y + 0.06, 1.8, 1.9, 0.432, 1, 'paper')
    elif kind == 'Hose':     # fire hose reel cabinet
        k.bx(0.25, 0.4, -0.42, 0.42, 0.6, 1.7, 'red')
        k.qx(-0.36, 0.36, 0.68, 1.62, 0.403, 1, 'crystal2')
        k.cyl(0.32, 0, 1.15, 0.3, 0.3, 0.06, 'red', seg=12, rot=(0, 90, 0), ink=False)
        k.qx(-0.36, 0.36, 1.72, 1.86, 0.256, 1, 'red')
        txt(k, 'FIRE HOSE', 0.259, 0.0, 1.79, 0.08, 'white', face='x+', font='sans', valign='m')
    elif kind == 'Lift':     # service lift doors with a floor indicator
        k.bx(0.255, 0.32, -0.48, 0.48, 0, 2.4, 'steel')
        k.qx(-0.44, -0.004, 0.05, 2.35, 0.323, 1, 'chrome')
        k.qx(0.004, 0.44, 0.05, 2.35, 0.323, 1, 'chrome')
        k.bx(0.25, 0.34, -0.5, 0.5, 2.4, 2.5, 'steel2')
        k.qx(-0.2, 0.2, 2.74, 2.94, 0.259, 1, 'black')
        k.poly([(0.262, -0.06, 2.78), (0.262, 0.06, 2.78), (0.262, 0.0, 2.9)], 'amber', (1, 0, 0))
    elif kind.startswith('F'):   # stencilled floor sign: the stair climbs to ...
        label = {'F24': '24', 'F56': '56', 'FR': 'ROOF'}[kind]
        k.qx(-0.48, 0.48, 1.25, 2.5, 0.259, 1, 'amber')
        txt(k, label, 0.262, 0.0, 1.8, 0.56 if len(label) < 3 else 0.3, 'black', face='x+', font='display', valign='m', maxw=0.86)
        txt(k, 'STAIR B', 0.262, 0.0, 2.32, 0.13, 'black', face='x+', font='sans', valign='m', maxw=0.8)
        k.poly([(0.262, -0.16, 1.32), (0.262, 0.16, 1.32), (0.262, 0.0, 1.47)], 'black', (1, 0, 0))
    elif kind == 'Linen':    # a housekeeping notice board and linen chute hatch
        k.bx(0.25, 0.29, -0.4, 0.4, 1.3, 1.95, 'steel')
        k.qx(-0.34, 0.34, 1.36, 1.89, 0.293, 1, 'steel2')
        txt(k, 'LINEN', 0.296, 0.0, 1.62, 0.12, 'black', face='x+', font='sans', valign='m')
        k.qx(-0.4, 0.4, 2.05, 2.5, 0.259, 1, 'cream')
        for i, c in enumerate(('wine', 'navy', 'amber')):
            k.qx(-0.3 + i * 0.22, -0.16 + i * 0.22, 2.15, 2.4, 0.262, 1, c)
    return k


def hatch(k):
    """Exit: the private express lift to the roof: a brass car (open to the south) with a mirrored back, a handrail,
    a glowing ceiling and the floor chevrons."""
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
        xa, xb = srt(s * (W - 0.08), s * (W - 0.083))
        k.poly([(s * (W - 0.083), -D + 0.15, 0.9), (s * (W - 0.083), D - 0.2, 0.9), (s * (W - 0.083), D - 0.2, Hc - 0.25), (s * (W - 0.083), -D + 0.15, Hc - 0.25)], 'walnut', (-s, 0, 0))
        k.bx(min(s * (W - 0.12), s * (W - 0.16)), max(s * (W - 0.12), s * (W - 0.16)), -D + 0.2, D - 0.2, 0.92, 0.97, 'brass', ink=False)
    k.bx(-W, W, -D, D, Hc, Hc + 0.12, 'bronze')
    k.qz(-W + 0.2, W - 0.2, -D + 0.2, D - 0.2, Hc - 0.003, -1, 'glow')
    k.bx(-W - 0.1, W + 0.1, -D - 0.1, -D + 0.05, Hc + 0.12, Hc + 0.45, 'bronze')
    k.qy(-0.5, 0.5, Hc + 0.16, Hc + 0.41, -D - 0.103, -1, 'nero')
    txt(k, 'ROOF', 0, -D - 0.106, Hc + 0.285, 0.17, 'amber', font='display', valign='m')
    return k


def stand(k):
    """Weapon stand: a marble console on gilt legs."""
    k.begin()
    k.bx(-0.48, 0.48, -0.3, 0.3, 0.86, 0.94, 'marble')
    k.bx(-0.44, 0.44, -0.26, 0.26, 0.72, 0.86, 'gold')
    for (x, y) in ((-0.4, -0.22), (0.4, -0.22), (-0.4, 0.22), (0.4, 0.22)):
        k.cyl(x, y, 0, 0.035, 0.05, 0.72, 'gold', seg=6, ink=False)
    k.bx(-0.4, 0.4, -0.22, 0.22, 0.12, 0.16, 'gold', ink=False)
    D.stand_detail(k)
    k.col(-0.48, 0.48, -0.3, 0.3, 0, 0.94)
    return k


# ================================================================ circulation
def grand_stair(k):
    """4 x 10 marble stair rising toward +Y to the 4.5 m mezzanine: 14 steps with a wine runner held by brass rods,
    gilt balusters and a walnut handrail on both sides; walkable stair boxes (the Spire's step line)."""
    k.begin()
    n, y0, y1 = 14, -5.0 + 0.9, 5.0 - 1.0
    run, rise = (y1 - y0) / n, DECK / n
    k.bx(-1.8, 1.8, -5.0, y0, 0.0, 0.03, 'marble', ink=False)
    k.qz(-1.0, 1.0, -5.0, y0, 0.033, 1, 'wine')
    k.col(-1.85, 1.85, -5.0, y0, 0, 0.03, True)
    for kk in range(n):
        a, top = y0 + kk * run, (kk + 1) * rise
        k.bx(-1.8, 1.8, a, a + run, 0.0, top, 'marble')
        k.qz(-1.0, 1.0, a, a + run, top + 0.003, 1, 'wine')
        k.qy(-1.0, 1.0, top - rise + 0.01, top, a - 0.003, -1, 'wine2')
        k.bx(-1.05, 1.05, a + 0.02, a + 0.05, top + 0.003, top + 0.03, 'brass', ink=False)
        k.col(-1.85, 1.85, a, a + run, 0, top, True)
    k.bx(-1.8, 1.8, y1, 5.0, DECK - 0.4, DECK, 'marble')
    k.qz(-1.0, 1.0, y1, 5.0, DECK + 0.003, 1, 'wine')
    k.bx(-1.8, 1.8, y1, 4.99, 0.0, DECK - 0.4, 'stone2', ink=False)
    k.col(-1.85, 1.85, y1, 5.0, 0, DECK, True)
    for sx in (-1, 1):
        a, b = srt(sx * 1.8, sx * 2.0)
        prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, DECK + 0.1), (y1, DECK + 0.1), (y0 - 0.05, 0.25), (-5.0, 0.25)]
        k.prism_y(prof, a, b, 'marble2')
        gx = sx * 1.9
        # balusters (gilt) along the rake, a newel post at the foot, the walnut rail
        for j in range(11):
            yy = -4.7 + j * 0.9
            zb = 0.25 if yy < y0 else (DECK + 0.1 if yy > y1 else 0.25 + (yy - y0) / (y1 - y0) * (DECK - 0.15))
            k.cyl(gx, yy, zb, 0.03, 0.03, 0.88, 'gold', seg=6, ink=False)
        hr = [(-4.85, 1.12), (y0, 1.12), (y1 + 0.05, DECK + 0.97), (4.85, DECK + 0.97), (4.85, DECK + 1.07), (y1 + 0.06, DECK + 1.07), (y0 - 0.01, 1.22), (-4.85, 1.22)]
        k.prism_y(hr, gx - 0.06, gx + 0.06, 'walnut')
        k.bx(gx - 0.14, gx + 0.14, -4.98, -4.72, 0, 1.25, 'marble2')
        k.sph(gx, -4.86, 1.36, 0.12, 'gold', seg=(8, 5))
        D.stair_detail(k, gx, y0, y1, DECK)
        for kk in range(n + 2):
            if kk == 0:
                a2, b2, top = -5.0, y0, 0.03
            elif kk == n + 1:
                a2, b2, top = y1, 5.0, DECK
            else:
                a2, b2, top = y0 + (kk - 1) * run, y0 + kk * run, kk * rise
            k.col(sx * 1.92 - 0.1, sx * 1.92 + 0.1, a2, b2, 0, top + 1.1)
    return k


def rail(k, y0, y1):
    """Marble and gilt balustrade on the mezzanine edge (a run along Y): plinth, turned balusters, walnut rail."""
    k.bx(-0.08, 0.08, y0, y1, 0, 0.14, 'marble2')
    n = max(1, int(round((y1 - y0) / 0.16)))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        k.cyl(0, y, 0.14, 0.035, 0.05, 0.4, 'gold', seg=6, ink=False)
        k.cyl(0, y, 0.54, 0.05, 0.03, 0.4, 'gold', seg=6, ink=False)
    k.bx(-0.07, 0.07, y0, y1, 0.94, 1.04, 'walnut')
    D.rail_detail(k, y0, y1)


def rails(k):
    k.begin()
    rail(k, -0.5, -0.07)
    k.col(-0.1, 0.1, -0.5, 0.0, 0, 1.1)
    k.finish('Rail')
    k.begin()
    rail(k, -0.5, 0.5)
    k.col(-0.1, 0.1, -0.5, 0.5, 0, 1.1)
    k.finish('RailFull')
    k.begin()
    k.bx(-0.1, 0.1, -0.1, 0.1, 0.004, 1.0, 'marble')
    k.bx(-0.12, 0.12, -0.12, 0.12, 1.0, 1.08, 'walnut')
    k.sph(0, 0, 1.15, 0.07, 'gold', seg=(6, 4), ink=False)
    D.post_detail(k)
    k.finish('RailPost')


def columns(k):
    """Marble columns with gilt Corinthian-ish capitals: under the mezzanine slab (0 - 4.1) and over it (4.5 - 9)."""
    for name, h in (('Column_Lo', DECK - 0.4), ('Column_Hi', H - DECK)):
        k.begin()
        k.bx(-0.42, 0.42, -0.42, 0.42, 0, 0.3, 'nero')
        k.cyl(0, 0, 0.3, 0.36, 0.3, 0.16, 'gold', seg=12)
        k.cyl(0, 0, 0.46, 0.28, 0.25, h - 0.46 - 0.6, 'marble', seg=12, caps=False)
        for i in range(8):
            a = i / 8 * math.pi * 2
            k.beam((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.5), (math.cos(a) * 0.245, math.sin(a) * 0.245, h - 0.65), 0.02, 'marble2', ink=False)
        k.cyl(0, 0, h - 0.6, 0.25, 0.4, 0.45, 'gold', seg=12)
        k.bx(-0.44, 0.44, -0.44, 0.44, h - 0.15, h - 0.004, 'stone2')
        D.column_detail(k, h)
        k.col(-0.4, 0.4, -0.4, 0.4, 0, h)
        k.finish(name)


# ================================================================ ceilings (hang from the 9 m plane)
def coffer(k):
    """4 x 4 coffered ceiling bay: deep beams with gilt edges, a cream panel with a rosette."""
    k.begin()
    for s in (-1, 1):
        a, b = srt(s * 1.997, s * 1.8)
        k.bx(a, b, -1.997, 1.997, -0.42, -0.004, 'cream', ink=False)
        k.bx(-1.8, 1.8, a, b, -0.42, -0.004, 'cream', ink=False)
        c0, c1 = srt(s * 1.8, s * 1.77)
        k.bx(c0, c1, -1.8, 1.8, -0.42, -0.38, 'gold', ink=False)
        k.bx(-1.77, 1.77, c0, c1, -0.418, -0.38, 'gold', ink=False)
    k.qz(-1.6, 1.6, -1.6, 1.6, -0.006, -1, 'silk')
    disc(k, 0, 0, -0.012, 0.55, 'gold', n=12, up=False)
    disc(k, 0, 0, -0.018, 0.32, 'cream', n=10, up=False)
    k.cyl(0, 0, -0.1, 0.1, 0.06, 0.08, 'gold', seg=8, ink=False)
    return k


def downlight(k):
    k.begin()
    k.cyl(0, 0, -0.035, 0.15, 0.15, 0.031, 'brass', seg=10, ink=False)
    k.cyl(0, 0, -0.041, 0.1, 0.1, 0.006, 'glow', seg=10, ink=False)
    return k


def under_light(k):
    """Gilt flush light under the mezzanine slab (the piece stands on the deck top; the underside is 0.4 m below)."""
    k.begin()
    k.cyl(0, 0, -0.45, 0.2, 0.16, 0.046, 'gold', seg=10, ink=False)
    k.cyl(0, 0, -0.456, 0.14, 0.14, 0.006, 'glow', seg=10, ink=False)
    return k


def chandelier(k, big):
    """Crystal chandelier hung from the ceiling plane: tiers of gilt arms with candle shades, crystal drops and
    swags, a crown and a finial. big: the lobby's 5 x 5 landmark (hangs 3.6 m); else 3 x 3 (2.3 m)."""
    k.begin()
    sc = 1.0 if big else 0.62
    drop = 3.6 if big else 2.3
    k.beam((0, 0, -0.01), (0, 0, -drop * 0.35), 0.04, 'gold', ink=False)
    k.cyl(0, 0, -0.12, 0.3 * sc, 0.3 * sc, 0.1, 'gold', seg=10)
    tiers = ((1.9, -drop + 0.9, 12), (1.25, -drop + 1.45, 9), (0.7, -drop + 1.95, 6)) if big else ((1.25, -drop + 0.7, 9), (0.7, -drop + 1.15, 6))
    for ti, (r, z, nn) in enumerate(tiers):
        ring(k, r, z, nn, 0.07 if big else 0.06, 'gold', ink=(ti == 0))
        for i in range(nn):
            a = (i + 0.5 * (ti % 2)) / nn * math.pi * 2
            x, y = math.cos(a) * r, math.sin(a) * r
            k.cyl(x, y, z + 0.04, 0.045, 0.025, 0.24, 'glow', seg=5, ink=False)
            if i % 2 == 0:
                k.sph(x, y, z - 0.18, 0.06 * (1 if big else 0.8), 'crystal', seg=(4, 2), scale=(1, 1, 1.7), ink=False)
                k.beam((x, y, z), (x * 0.25, y * 0.25, z + 0.35), 0.03, 'gold', ink=False)
        if ti == 0:   # crystal swag ring under the widest tier
            ring(k, r * 0.92, z - 0.12, nn, 0.025, 'crystal2', ink=False)
    # central body: stacked bowls and the finial ball
    zb = tiers[0][1]
    k.cyl(0, 0, zb - 0.4, 0.08 * sc, 0.45 * sc, 0.4, 'gold', seg=12)
    k.cyl(0, 0, zb, 0.45 * sc, 0.2 * sc, 0.3, 'crystal2', seg=12)
    k.cyl(0, 0, zb + 0.3, 0.12 * sc, 0.12 * sc, tiers[-1][1] - zb, 'gold', seg=8, ink=False)
    k.sph(0, 0, zb - 0.55, 0.13 * sc, 'crystal', seg=(6, 4), scale=(1, 1, 1.4))
    k.cyl(0, 0, tiers[-1][1] + 0.1, 0.25 * sc, 0.06, 0.45, 'gold', seg=8)
    return k


def glass_roof(k):
    """6 x 6 glazed pyramid standing on the ceiling plane over the sky deck: bronze edge beams, hip ribs, purlins,
    an apex lantern and glints."""
    k.begin()
    A, E = 1.9, 3.0
    for s in (-1, 1):
        a, b = srt(s * E, s * (E - 0.12))
        k.bx(a, b, -E, E, -0.25, 0.12, 'bronze')
        k.bx(-(E - 0.12), E - 0.12, a, b, -0.25, 0.12, 'bronze')
    for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        k.beam((x * (E - 0.1), y * (E - 0.1), 0.12), (x * 0.22, y * 0.22, A - 0.06), 0.1, 'bronze')
    for f in (0.4, 0.72):
        r, z = E * (1 - f), 0.12 + f * (A - 0.2)
        for i, (x0, y0, x1, y1) in enumerate(((-r, -r, r, -r), (r, -r, r, r), (r, r, -r, r), (-r, r, -r, -r))):
            zz = z + 0.008 * (i % 2)
            k.beam((x0, y0, zz), (x1, y1, zz), 0.05, 'brass', ink=False)
    k.cyl(0, 0, A - 0.12, 0.34, 0.18, 0.34, 'bronze', seg=8)
    k.sph(0, 0, A + 0.3, 0.09, 'gold', seg=(6, 4), ink=False)
    for (ax, ay) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        tx, ty = -ay, ax
        d0, d1 = 2.5, 1.4
        p = lambda d, uu, z: (ax * d + tx * uu, ay * d + ty * uu, z)
        z0 = 0.12 + (E - d0) / E * (A - 0.12) + 0.05
        z1 = 0.12 + (E - d1) / E * (A - 0.12) + 0.05
        k.poly([p(d0, -1.5, z0), p(d0, -1.32, z0), p(d1, -0.82, z1), p(d1, -1.0, z1)], 'glint', (-ax * 0.5, -ay * 0.5, -0.85))
    # gilt pendant lantern under the apex
    k.beam((0, 0, -0.25), (0, 0, -1.55), 0.02, 'bronze', ink=False)
    k.cyl(0, 0, -2.05, 0.16, 0.24, 0.45, 'glow', seg=8)
    k.cyl(0, 0, -1.6, 0.26, 0.1, 0.12, 'brass', seg=8)
    return k


# ================================================================ floors (layer 0)
def medallion(k):
    """7 x 7 marble compass medallion: a black ring, a cream star, a gilt inner star, a wine centre."""
    k.begin()
    disc(k, 0, 0, 0.014, 3.4, 'nero', n=24)
    disc(k, 0, 0, 0.017, 3.2, 'marble2', n=24)

    def star(ro, ri, z, c, n=8, ph=0.0):
        for i in range(n):
            a = i / n * math.pi * 2 + ph
            b0, b1 = a - math.pi / n, a + math.pi / n
            k.poly([(0, 0, z), (math.cos(b0) * ri, math.sin(b0) * ri, z), (math.cos(a) * ro, math.sin(a) * ro, z), (math.cos(b1) * ri, math.sin(b1) * ri, z)], c, (0, 0, 1))
    star(3.1, 1.1, 0.02, 'marble')
    star(2.0, 0.75, 0.023, 'gold', ph=math.pi / 8)
    disc(k, 0, 0, 0.026, 0.62, 'nero', n=14)
    disc(k, 0, 0, 0.029, 0.48, 'wine', n=12)
    txt(k, 'A', 0, 0.0, 0.032, 0.44, 'gold', face='up', font='serif', valign='m')
    return k


def band(k):
    k.begin()
    k.qz(-0.5, 0.5, -0.36, 0.36, 0.014, 1, 'nero')
    k.qz(-0.5, 0.5, -0.04, 0.04, 0.017, 1, 'gold')
    return k


def carpet(k, kind):
    """4 x 4 carpet tile with a pattern that runs on into its neighbours (period 2 m).
    Lobby: wine with a gold trellis; Corridor: navy with gold medallions; Suite: cream with a soft lattice."""
    k.begin()
    field, line, dot = {'Lobby': ('wine', 'cgold', 'wine3'), 'Corridor': ('navy', 'cgold', 'wine'), 'Pent': ('cream', 'silk2', 'gold')}[kind]
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.014, 1, field)
    for i in range(2):
        for j in range(2):
            cx, cy = -1.0 + i * 2.0, -1.0 + j * 2.0
            r = 0.95
            k.poly([(cx, cy - r, 0.017), (cx + r, cy, 0.017), (cx, cy + r, 0.017), (cx - r, cy, 0.017)], line, (0, 0, 1))
            r2 = 0.85
            k.poly([(cx, cy - r2, 0.02), (cx + r2, cy, 0.02), (cx, cy + r2, 0.02), (cx - r2, cy, 0.02)], field, (0, 0, 1))
            if kind == 'Corridor':
                disc(k, cx, cy, 0.023, 0.38, line, n=10)
                disc(k, cx, cy, 0.026, 0.24, dot, n=8)
            else:
                k.poly([(cx, cy - 0.3, 0.023), (cx + 0.3, cy, 0.023), (cx, cy + 0.3, 0.023), (cx - 0.3, cy, 0.023)], dot, (0, 0, 1))
                k.qz(cx - 0.05, cx + 0.05, cy - 0.05, cy + 0.05, 0.026, 1, line)
            for (dx, dy) in ((1, 0), (0, 1)):
                px, py = cx + dx * 1.0, cy + dy * 1.0
                if abs(px) < 2.0 and abs(py) < 2.0:
                    k.qz(px - 0.07, px + 0.07, py - 0.07, py + 0.07, 0.023, 1, dot)
    return k


def runner(k):
    """[3, 1] carpet runner tile (laid in a run from the door): wine with a gold border on both long sides and a
    gold lozenge in the middle."""
    k.begin()
    k.qz(-1.5, 1.5, -0.5, 0.5, 0.014, 1, 'wine')
    for s in (-1, 1):
        a, b = srt(s * 1.4, s * 1.25)
        k.qz(a, b, -0.5, 0.5, 0.017, 1, 'cgold')
    k.poly([(0, -0.38, 0.017), (0.5, 0, 0.017), (0, 0.38, 0.017), (-0.5, 0, 0.017)], 'cgold', (0, 0, 1))
    k.poly([(0, -0.24, 0.02), (0.3, 0, 0.02), (0, 0.24, 0.02), (-0.3, 0, 0.02)], 'wine3', (0, 0, 1))
    return k


def parquet(k):
    """3 x 3 dance-floor tile: a chequer of walnut squares and oak squares laid in strips."""
    k.begin()
    k.bx(-1.496, 1.496, -1.496, 1.496, 0.0, 0.03, 'oak', ink=False)
    for i in range(3):
        for j in range(3):
            if (i + j) % 2:
                k.qz(-1.5 + i, -0.5 + i, -1.5 + j, -0.5 + j, 0.033, 1, 'walnut')
            else:
                for t in range(1, 4):
                    x = -1.5 + i + t * 0.25
                    k.qz(x - 0.006, x + 0.006, -1.5 + j + 0.02, -0.5 + j - 0.02, 0.033, 1, 'teak2')
    return k


def trail_end(k):
    """Back wall of the exit room (the trail module without its half ceiling and handrail): block, dado, a sign."""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, H, 'block')
    k.qx(-0.5, 0.5, 0.0, 1.1, 0.253, 1, 'svc')
    k.qx(-0.5, 0.5, 1.1, 1.16, 0.256, 1, 'block2')
    k.bx(0.25, 0.31, -0.5, 0.5, 0, 0.1, 'nero', ink=False)
    return k


def deck(k):
    """4 x 4 teak pool deck with stainless grout strips."""
    k.begin()
    k.bx(-1.996, 1.996, -1.996, 1.996, 0.0, 0.03, 'teak', ink=False)
    for i in range(1, 16):
        y = -2.0 + i * 0.25
        k.qz(-2.0, 2.0, y - 0.008, y + 0.008, 0.033, 1, 'teak2')
    return k
