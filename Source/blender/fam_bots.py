"""INKBOLT asset family: bots (brief 3.2, 4.6, 5.7).

Every robot is split into rigid parts for instancing; each part is modelled around its own pivot so the game
can pose it with one matrix (wheels spin about their axle, lids hinge, guns pitch about their trunnion).
Blender is Z-up and robots face -Y (game +Z). Sockets (empties) give the game every pivot and weak point:
  BOT_<T>_CORE   weak point centre (gold)          BOT_<T>_GUN    muzzle (child of the Gun part)
  BOT_<T>_*      part pivots (HIP0..3, HINGE, GUNPIVOT, WHEEL0/1, AXLE, CAP, WICK, LID, ROTOR0..3, LIGHT)
No faces, no eyes: sensors are single slots, wrap-around strips and antenna lights.

Triangle budgets include the outline hull, so each part is built from two shape sets (class Part):
  * silhouette shapes -> get the inverted-hull ink outline (brief 3.3)
  * deco shapes (stripes, straps, stickers, bolts, rings) -> sit >= 3 mm proud on a silhouette shape and are joined
    without a shell of their own, so detail costs half
One strict z-fighting check covers both sets together (nothing coplanar may overlap, inside a part or between sets).
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib


def _lighten(hx, k=0.12):
    """Mix a colour toward white by k (the bots read a touch lighter than the brief's base swatches)."""
    r, g, b = hex2rgb(hx)
    return '#%02X%02X%02X' % tuple(int(round((c + (1 - c) * k) * 255)) for c in (r, g, b))


ib_lib.ZFIGHT_STRICT['bots'] = True
ib_lib.PALETTES['bots'] = BASE + [
    # Crawler: dented tin can
    ('tin', _lighten('#C9CFD6')), ('tin2', _lighten('#A9B0BA')), ('rust', _lighten('#D9663B')), ('spring', _lighten('#8C93A0')),
    ('core', '#FFC23A'), ('light', '#FFFFFF'),
    # Gunner: wheelie bin
    ('bin', _lighten('#4FA36A')), ('bin2', _lighten('#3F8A57')), ('rubber', _lighten('#3A3844', 0.06)), ('steel', _lighten('#9AA6B4')),
    ('core2', '#E9A21F'), ('sticker', '#FFF1D6'),
    # Bomber: fizzing bottle on a roller
    ('glass', _lighten('#3E86D8')), ('glass2', _lighten('#2F6DB8')), ('capred', _lighten('#F0443A', 0.06)), ('label', '#FFF7E6'),
    ('wick', '#7A5638'),
    # Drone: soda can
    ('can', _lighten('#E2483D')), ('can2', _lighten('#B93A31')), ('alu', _lighten('#C4CBD3')),
    ('tin3', _lighten('#7E8794')),
]


# ---------------------------------------------------------------- helpers
def lathe(m, prof, color, seg=12, phase=0.0):
    """Surface of revolution about Z: prof = [(r, z), ...] bottom to top; r == 0 makes a pole (closed end).
    One shape with shared rings, so the profile has no seams."""
    bm = m.bm
    rings = []
    for r, z in prof:
        if r <= 1e-6:
            rings.append([bm.verts.new(m.parent @ Vector((0, 0, z)))])
            continue
        rings.append([bm.verts.new(m.parent @ Vector((r * math.cos(phase + 2 * math.pi * k / seg),
                                                      r * math.sin(phase + 2 * math.pi * k / seg), z))) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            k2 = (k + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[k2], b[k]))
            elif len(b) == 1:
                bm.faces.new((a[k], a[k2], b[0]))
            else:
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    return m._finish([v for ring in rings for v in ring], color, False)


class Part:
    """A part = silhouette shapes (outlined) + deco shapes (no own outline); see the module docstring."""

    def __init__(self, pal):
        self.pal = pal
        self.main, self.deco, self.all = Model(pal), Model(pal), Model(pal)
        self.parent = Matrix.Identity(4)
        self.ndeco = 0

    def _each(self, deco):
        for mm in (self.deco if deco else self.main, self.all):
            mm.parent = self.parent
            yield mm
        if deco:
            self.ndeco += 1

    def box(self, loc, size, color, rot=(0, 0, 0), bevel=False, deco=False):
        for mm in self._each(deco):
            mm.box(loc, size, color, rot=rot, bevel=bevel and not deco)

    def cyl(self, loc, r1, r2, h, color, seg=12, rot=(0, 0, 0), bevel=False, caps=True, deco=False):
        for mm in self._each(deco):
            mm.cyl(loc, r1, r2, h, color, seg=seg, rot=rot, bevel=bevel and not deco, caps=caps)

    def sphere(self, loc, r, color, seg=(10, 6), scale=(1, 1, 1), rot=(0, 0, 0), deco=False):
        for mm in self._each(deco):
            mm.sphere(loc, r, color, seg=seg, scale=scale, rot=rot)

    def beam(self, a, b, thick, color, deco=False):
        for mm in self._each(deco):
            mm.beam(a, b, thick, color)

    def lathe(self, prof, color, seg=12, phase=0.0, deco=False):
        for mm in self._each(deco):
            lathe(mm, prof, color, seg, phase)

    def band(self, z0, z1, r, color, seg=12, phase=0.0, deco=True):
        """Open ring band around Z (a painted stripe / strap standing proud of a round body)."""
        self.lathe([(r, z0), (r, z1)], color, seg, phase, deco=deco)

    def on_facet(self, k, seg, r_body, out, z, size, color, phase=0.0, deco=True):
        """Flat box lying on facet k of a seg-sided round body (r_body = its vertex radius), `out` m off the facet."""
        a = phase + 2 * math.pi * (k + 0.5) / seg
        d = r_body * math.cos(math.pi / seg) + out + size[1] / 2
        self.box((d * math.cos(a), d * math.sin(a), z), size, color, rot=(0, 0, math.degrees(a) - 90), deco=deco)

    def on_slope(self, k, seg, a, b, t, out, size, color, phase=0.0, deco=True):
        """Flat box on facet k of the lathe band between profile points a=(r0, z0) and b=(r1, z1), at t along it,
        tilted to lie on the sloped facet; size = (width, thickness, length along the slope)."""
        (r0, z0), (r1, z1) = a, b
        phi = math.atan2(r0 - r1, z1 - z0)
        r, z = r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
        ang = phase + 2 * math.pi * (k + 0.5) / seg
        o = out + size[1] / 2
        d = r * math.cos(math.pi / seg) + o * math.cos(phi)
        self.box((d * math.cos(ang), d * math.sin(ang), z + o * math.sin(phi)), size, color,
                 rot=(math.degrees(phi), 0, math.degrees(ang) - 90), deco=deco)

    def build(self, name, bevel=True, hull=None):
        bw, ht = CFG['bots']
        ht = hull or ht
        check_zfight(name, self.all.bm, self.all.shape)
        self.all.bm.free()
        obj = build_object(name, self.main, bw if bevel else 0, ht)
        if self.ndeco:
            d = build_object(name + '_deco', self.deco, 0, ht)
            strip_hull(d)
            join_into(obj, d)
        else:
            self.deco.bm.free()
        return obj


# ================================================================ CRAWLER
# Dented tin can on 4 spring legs: corrugated tin with a rust band and a torn paper label scrap, rolled top rim,
# one sensor slot, antenna light, gold core dome (weak point) where the lid used to be.
def build_crawler(pal):
    p = Part(pal)
    p.cyl((0, 0, 0.30), 0.32, 0.31, 0.42, 'tin', seg=10, bevel=True)
    p.cyl((0, 0, 0.72), 0.35, 0.35, 0.05, 'tin2', seg=10, bevel=True)                 # rolled top rim
    p.box((0, -0.31, 0.60), (0.34, 0.07, 0.07), 'ink')                                  # sensor slot (front = -Y)
    p.box((0, -0.349, 0.60), (0.22, 0.02, 0.03), 'amber')
    p.sphere((0, 0, 0.77), 0.14, 'core', seg=(8, 4), scale=(1, 1, 0.6))
    p.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=3)
    # deco: rust band, corrugation ridges, torn label scrap, dent creases, seam rivets, core seat ring
    p.cyl((0, 0, 0.42), 0.335, 0.335, 0.12, 'rust', seg=10, caps=False, deco=True)
    for z in (0.335, 0.375, 0.585):
        p.cyl((0, 0, z), 0.326, 0.326, 0.016, 'tin2', seg=10, caps=False, deco=True)
    for k, (z, w, h) in enumerate(((0.47, 0.17, 0.10), (0.50, 0.07, 0.06))):
        p.on_facet(3, 10, 0.335, 0.004 + 0.004 * k, z, (w, 0.006, h), 'paper' if k == 0 else 'sticker')
    p.on_facet(4, 10, 0.32, 0.004, 0.62, (0.012, 0.006, 0.12), 'ink')                   # dent crease
    for z in (0.34, 0.44, 0.54, 0.64):
        p.on_facet(8, 10, 0.32, 0.003, z, (0.022, 0.008, 0.022), 'tin2')                # seam rivets
    p.cyl((0, 0, 0.77), 0.152, 0.152, 0.02, 'gunmetal', seg=10, caps=False, deco=True)
    body = p.build('BOT_CRAWLER_Body')
    socket('BOT_CRAWLER_CORE', body, (0, 0, 0.82))
    for i, (x, y) in enumerate([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]):
        socket('BOT_CRAWLER_HIP%d' % i, body, (x, y, 0.33))
    p = Part(pal)
    for i in range(3):
        p.box(((0.035 if i % 2 else -0.035), 0, -0.05 - i * 0.085), (0.13, 0.06, 0.04), 'spring', deco=True)
    p.box((0, 0, -0.15), (0.03, 0.03, 0.3), 'gunmetal')
    p.cyl((0, 0, -0.355), 0.09, 0.07, 0.05, 'gunmetal', seg=5)
    p.build('BOT_CRAWLER_Leg', bevel=False, hull=0.01)
    p = Part(pal)
    p.box((0, 0, 0), (0.09, 0.09, 0.09), 'light')
    p.build('BOT_CRAWLER_Light', bevel=False, hull=0.008)


# ================================================================ GUNNER
# Wheelie bin (tapered tub, rim lip, hinged lid, push handle, two back wheels, front feet) with a pipe gun
# clamped on a gold battery (the core) under the lid's front lip. The gun pitches about the battery axis.
G_Z0, G_Z1 = 0.07, 0.985            # tub bottom / top
G_HW0, G_HW1 = 0.25, 0.30           # tub half width (x) at bottom / top
G_DEPTH = 1.1                       # depth (y) / width
G_HINGE = (0, 0.372, 1.0)
G_PIVOT = (0, -0.405, 0.835)        # battery axis centre = gun trunnion
G_WHEEL = (0.318, 0.30, 0.125)
G_WHEEL_R = 0.125
G_LIGHT = (0.24, 0.47, 1.43)


def g_hw(z):
    return G_HW0 + (G_HW1 - G_HW0) * (z - G_Z0) / (G_Z1 - G_Z0)


def build_gunner(pal):
    slope_y = math.degrees(math.atan(G_DEPTH * (G_HW1 - G_HW0) / (G_Z1 - G_Z0)))  # front/back wall lean

    def front(z, out):
        return -(G_DEPTH * g_hw(z) + out)

    p = Part(pal)
    # tub (square frustum stretched in depth) and the rim lip the lid rests on
    p.parent = Matrix.Diagonal(Vector((1, G_DEPTH, 1, 1)))
    p.cyl((0, 0, G_Z0), G_HW0 * math.sqrt(2), G_HW1 * math.sqrt(2), G_Z1 - G_Z0, 'bin', seg=4, rot=(0, 0, 45), bevel=True)
    p.cyl((0, 0, 0.925), 0.322 * math.sqrt(2), 0.322 * math.sqrt(2), 0.07, 'bin2', seg=4, rot=(0, 0, 45), bevel=True)
    p.parent = Matrix.Identity(4)
    # core: gold battery lying along X (the gun's trunnion)
    px, py, pz = G_PIVOT
    p.cyl((-0.17, py, pz), 0.075, 0.075, 0.34, 'core', seg=10, rot=(0, 90, 0))
    # back: axle housing, push handle with grips
    p.box((0, 0.30, 0.125), (0.56, 0.08, 0.08), 'gunmetal')
    p.cyl((-0.30, 0.445, 0.95), 0.03, 0.03, 0.60, 'gunmetal', seg=8, rot=(0, 90, 0))
    for sx in (-1, 1):
        p.cyl((sx * 0.295 - 0.025, 0.445, 0.95), 0.037, 0.037, 0.05, 'rubber', seg=8, rot=(0, 90, 0))
        p.box((sx * 0.17, -0.235, 0.035), (0.11, 0.10, 0.07), 'rubber')                  # front feet
    # antenna on the right handle bracket (the light sits on top)
    lx, ly, lz = G_LIGHT
    p.cyl((lx, ly, 0.97), 0.012, 0.012, lz - 0.97 - 0.04, 'ink', seg=4)
    # ---- deco
    for sx in (-1, 1):                                                                   # side ribs, leaning with the wall
        for y in (-0.15, 0.13):
            za, zb = 0.16, 0.86
            p.beam((sx * (g_hw(za) + 0.006), y, za), (sx * (g_hw(zb) + 0.006), y, zb), 0.03, 'bin2', deco=True)
    p.box((0, front(0.20, 0.012), 0.20), (0.40, 0.03, 0.07), 'bin2', rot=(slope_y, 0, 0), deco=True)   # kick rib
    zs = 0.52                                                                           # "collection day" sticker
    p.box((0, front(zs, 0.006), zs), (0.30, 0.008, 0.24), 'sticker', rot=(slope_y, 0, 0), deco=True)
    p.box((0, front(zs + 0.07, 0.0135), zs + 0.07), (0.27, 0.008, 0.05), 'teal', rot=(slope_y, 0, 0), deco=True)
    for i, w in enumerate((0.20, 0.14, 0.17)):
        z = zs - 0.005 - i * 0.045
        p.box((-0.12 + w / 2, front(z, 0.0135), z), (w, 0.008, 0.016), 'ink', rot=(slope_y, 0, 0), deco=True)
    for sx in (-1, 1):                                                                   # battery brackets + bolts
        x = sx * 0.218
        y0 = front(pz, -0.02)
        p.box((x, (y0 + py) / 2, pz), (0.04, abs(py - y0), 0.10), 'gunmetal', deco=True)
        p.cyl((x + sx * 0.02, py, pz), 0.022, 0.022, 0.012, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
        p.cyl((sx * 0.17 - 0.02, py, pz), 0.081, 0.081, 0.04, 'core2', seg=10, rot=(0, 90, 0), caps=False, deco=True)
        p.box((sx * 0.235, 0.40, 0.95), (0.05, 0.10, 0.06), 'bin2', deco=True)           # handle brackets
    p.cyl((0.165, py, pz), 0.03, 0.03, 0.03, 'steel', seg=6, rot=(0, 90, 0), deco=True)   # + terminal
    p.cyl((lx, ly, 0.965), 0.03, 0.022, 0.035, 'gunmetal', seg=6, deco=True)             # antenna base
    p.box((0, 0, 0.996), (0.56, 0.62, 0.006), 'ink', deco=True)                          # dark opening (shows when the lid lifts)
    body = p.build('BOT_GUNNER_Body')
    socket('BOT_GUNNER_CORE', body, (0, py, pz))
    socket('BOT_GUNNER_HINGE', body, G_HINGE)
    socket('BOT_GUNNER_GUNPIVOT', body, G_PIVOT)
    socket('BOT_GUNNER_LIGHT', body, G_LIGHT)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_GUNNER_WHEEL%d' % i, body, (sx * G_WHEEL[0], G_WHEEL[1], G_WHEEL[2]))

    # lid (origin on the hinge axis; extends toward -Y)
    p = Part(pal)
    L = 0.75
    p.box((0, -L / 2 + 0.005, 0.024), (0.69, L, 0.048), 'bin', bevel=True)
    p.box((0, -L + 0.012, -0.012), (0.70, 0.026, 0.10), 'bin2')                         # front lip
    p.box((0, -L / 2 - 0.02, 0.054), (0.50, 0.50, 0.014), 'bin2', deco=True)           # raised panel
    p.box((0, -L - 0.004, -0.004), (0.42, 0.012, 0.04), 'ink', deco=True)               # sensor slot
    p.box((0, -L - 0.0125, -0.004), (0.34, 0.01, 0.018), 'amber', deco=True)            # sensor strip
    for sx in (-1, 1):
        p.cyl((sx * 0.30 - 0.05, 0, 0.0), 0.028, 0.028, 0.10, 'gunmetal', seg=6, rot=(0, 90, 0), deco=True)  # knuckles
    p.build('BOT_GUNNER_Lid')

    # pipe gun (origin on the battery axis; barrel along -Y)
    p = Part(pal)
    p.cyl((-0.05, 0, 0), 0.092, 0.092, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0))          # clamp collar
    p.box((0, -0.10, 0), (0.07, 0.10, 0.11), 'gunmetal')                                  # breech block
    p.cyl((0, -0.12, 0), 0.044, 0.044, 0.36, 'steel', seg=8, rot=(90, 0, 0))              # barrel
    p.cyl((0, -0.44, 0), 0.06, 0.06, 0.06, 'gunmetal', seg=8, rot=(90, 0, 0))             # muzzle cap
    p.cyl((0, -0.17, 0), 0.049, 0.049, 0.05, 'amber', seg=8, rot=(90, 0, 0), caps=False, deco=True)   # tape wrap
    p.cyl((0, -0.29, 0), 0.056, 0.056, 0.05, 'gunmetal', seg=8, rot=(90, 0, 0), caps=False, deco=True)  # coupling
    p.cyl((0, -0.496, 0), 0.032, 0.032, 0.008, 'ink', seg=8, rot=(90, 0, 0), deco=True)   # bore
    p.box((0, -0.468, 0.068), (0.018, 0.03, 0.024), 'gunmetal', deco=True)                 # sight
    gun = p.build('BOT_GUNNER_Gun', bevel=False)
    socket('BOT_GUNNER_GUN', gun, (0, -0.51, 0))

    # wheel (origin on the axle; axis X; symmetric so the game mirrors it for the other side)
    p = Part(pal)
    w = 0.075
    p.cyl((-w / 2, 0, 0), G_WHEEL_R, G_WHEEL_R, w, 'rubber', seg=10, rot=(0, 90, 0))
    p.cyl((-w / 2 - 0.004, 0, 0), 0.072, 0.072, w + 0.008, 'steel', seg=8, rot=(0, 90, 0), deco=True)     # hub
    p.cyl((-w / 2 - 0.01, 0, 0), 0.026, 0.026, w + 0.02, 'gunmetal', seg=6, rot=(0, 90, 0), deco=True)   # axle nut
    p.build('BOT_GUNNER_Wheel', bevel=False)

    p = Part(pal)
    p.box((0, 0, 0), (0.08, 0.08, 0.08), 'light')
    p.build('BOT_GUNNER_Light', bevel=False, hull=0.008)


# ================================================================ BOMBER
# Fizzing bottle in a roller fork: blue bottle with a label and a strapped gold pressure canister (core),
# red crimp cap with a fuse wick (the cap pops and the wick sparks during the 0.6 s fuse).
B_AXLE = (0, 0, 0.13)
B_ROLLER_R = 0.13
B_CAP = (0, 0, 0.865)


def build_bomber(pal):
    SEG = 12
    p = Part(pal)
    for sx in (-1, 1):                                                                  # fork side plates
        p.box((sx * 0.262, 0, 0.21), (0.03, 0.09, 0.20), 'gunmetal')
    p.box((0, 0, 0.285), (0.53, 0.11, 0.03), 'gunmetal')                                 # cross bar
    p.cyl((0, 0, 0.29), 0.235, 0.235, 0.03, 'alu', seg=SEG)                              # cradle disc
    p.lathe([(0.0, 0.316), (0.15, 0.316), (0.205, 0.335), (0.223, 0.37), (0.225, 0.62), (0.212, 0.665),
             (0.165, 0.725), (0.105, 0.775), (0.076, 0.80), (0.074, 0.87), (0.0, 0.87)], 'glass', seg=SEG)
    cy = -0.307                                                                          # core canister
    p.cyl((0, cy, 0.39), 0.066, 0.066, 0.19, 'core', seg=8)
    p.cyl((0, cy, 0.58), 0.066, 0.04, 0.03, 'core', seg=8)
    p.cyl((0, cy, 0.36), 0.04, 0.066, 0.03, 'core', seg=8)
    # ---- deco: label, straps, neck ring + sensor strip, glints, hub caps, canister band + valve
    p.band(0.43, 0.55, 0.232, 'label', seg=SEG)
    p.band(0.456, 0.47, 0.236, 'teal', seg=SEG)
    for z in (0.405, 0.555):
        p.band(z, z + 0.022, 0.24, 'gunmetal', seg=SEG)
    p.band(0.795, 0.812, 0.088, 'ink', seg=8)
    p.band(0.822, 0.840, 0.082, 'amber', seg=8)
    # comic highlight: one streak down the left-front of the shoulder and body
    p.on_slope(7, SEG, (0.212, 0.665), (0.165, 0.725), 0.5, 0.004, (0.03, 0.006, 0.058), 'paper')
    p.on_slope(7, SEG, (0.165, 0.725), (0.105, 0.775), 0.45, 0.004, (0.024, 0.006, 0.04), 'paper')
    p.on_facet(7, SEG, 0.225, 0.004, 0.604, (0.03, 0.006, 0.034), 'paper')
    for sx in (-1, 1):
        p.cyl((sx * 0.277, 0, 0.13), 0.045, 0.045, 0.014, 'alu', seg=6, rot=(0, sx * 90, 0), deco=True)
    p.cyl((0, cy, 0.465), 0.072, 0.072, 0.02, 'core2', seg=8, caps=False, deco=True)
    p.cyl((0, cy, 0.61), 0.016, 0.016, 0.03, 'gunmetal', seg=6, deco=True)
    body = p.build('BOT_BOMBER_Body', bevel=False)
    socket('BOT_BOMBER_CORE', body, (0, cy, 0.48))
    socket('BOT_BOMBER_AXLE', body, B_AXLE)
    socket('BOT_BOMBER_CAP', body, B_CAP)

    # roller drum (origin on the axle, axis X)
    p = Part(pal)
    p.cyl((-0.22, 0, 0), B_ROLLER_R, B_ROLLER_R, 0.44, 'rubber', seg=10, rot=(0, 90, 0))
    for x in (-0.12, 0.12):
        p.cyl((x - 0.012, 0, 0), B_ROLLER_R + 0.006, B_ROLLER_R + 0.006, 0.024, 'steel', seg=10, rot=(0, 90, 0),
              caps=False, deco=True)
    p.cyl((-0.228, 0, 0), 0.06, 0.06, 0.456, 'alu', seg=6, rot=(0, 90, 0), deco=True)    # end hubs (one through-rod)
    p.build('BOT_BOMBER_Roller', bevel=False)

    # crimp cap + fuse wick (origin on the neck top)
    p = Part(pal)
    p.cyl((0, 0, 0.0), 0.088, 0.088, 0.05, 'capred', seg=10)
    pts = [(0, 0, 0.06), (0.02, 0.005, 0.10), (0.006, -0.01, 0.14), (0.022, 0.0, 0.175)]
    for a, b in zip(pts, pts[1:]):
        p.beam(a, b, 0.016, 'wick')
    p.cyl((0, 0, -0.012), 0.095, 0.095, 0.02, 'capred', seg=10, caps=False, deco=True)   # crimp skirt
    p.cyl((0, 0, 0.046), 0.026, 0.02, 0.025, 'alu', seg=6, deco=True)                     # wick holder
    cap = p.build('BOT_BOMBER_Cap', bevel=False)
    socket('BOT_BOMBER_WICK', cap, (0.022, 0.0, 0.185))

    # spark: three crossed bars, coloured per instance by the game
    p = Part(pal)
    p.box((0, 0, 0), (0.11, 0.02, 0.02), 'light')
    p.box((0, 0, 0), (0.028, 0.11, 0.028), 'light')
    p.box((0, 0, 0), (0.036, 0.036, 0.11), 'light')
    p.build('BOT_BOMBER_Light', bevel=False, hull=0.008)


# ================================================================ DRONE
# Soda can (red, white ribbon, wrap-around sensor strip, gold core dome underneath) with a 4-rotor lid that
# lifts on a telescoping post during the windup, and a small pipe gun on a gimbal under the front edge.
D_LID = (0, 0, 0.575)
D_PIVOT = (0, -0.135, -0.035)
D_ARM = 0.30


def build_drone(pal):
    SEG = 12
    p = Part(pal)
    p.lathe([(0.12, 0.02), (0.188, 0.07), (0.19, 0.09), (0.19, 0.50), (0.182, 0.53), (0.163, 0.56), (0.163, 0.575),
             (0.0, 0.575)], 'can', seg=SEG)
    p.lathe([(0.0, 0.02), (0.12, 0.02)], 'can2', seg=SEG)                               # bottom (seat of the dome)
    p.sphere((0, 0, 0.02), 0.11, 'core', seg=(8, 4), scale=(1, 1, 0.62))               # core dome
    p.box((0, D_PIVOT[1] + 0.01, 0.0), (0.05, 0.06, 0.05), 'gunmetal')                    # gun gimbal bracket
    p.band(0.18, 0.29, 0.195, 'paper', seg=SEG)                                           # white ribbon
    p.band(0.37, 0.43, 0.196, 'ink', seg=SEG)                                             # sensor slot (all round)
    p.band(0.388, 0.412, 0.2, 'amber', seg=SEG)                                           # sensor strip
    body = p.build('BOT_DRONE_Body', bevel=False)
    socket('BOT_DRONE_CORE', body, (0, 0, -0.01))
    socket('BOT_DRONE_LID', body, D_LID)
    socket('BOT_DRONE_GUNPIVOT', body, D_PIVOT)

    # lid (origin on the can top): disc, X arms, motor pods; deco: pull tab, telescoping post, antenna
    p = Part(pal)
    p.cyl((0, 0, 0.0), 0.172, 0.172, 0.022, 'alu', seg=10)
    pods = []
    for k in range(2):
        a = math.radians(45 + 90 * k)
        c, s = D_ARM * math.cos(a), D_ARM * math.sin(a)
        z = 0.03 + 0.006 * k                                                               # crossing beams at two heights
        p.beam((-c, -s, z), (c, s, z), 0.03, 'gunmetal')
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = D_ARM * math.cos(a), D_ARM * math.sin(a)
        p.cyl((x, y, 0.0), 0.046, 0.046, 0.075, 'can2', seg=6)
        pods.append((x, y, 0.092))
    p.cyl((0, 0, -0.16), 0.03, 0.03, 0.16, 'gunmetal', seg=6, caps=False, deco=True)     # post (shows when lifted)
    p.box((0, -0.06, 0.026), (0.05, 0.085, 0.008), 'alu', deco=True)                       # pull tab
    p.cyl((0.0, 0.08, 0.022), 0.009, 0.009, 0.16, 'ink', seg=4, deco=True)               # antenna
    lid = p.build('BOT_DRONE_Lid', bevel=False)
    for k, q in enumerate(pods):
        socket('BOT_DRONE_ROTOR%d' % k, lid, q)
    socket('BOT_DRONE_LIGHT', lid, (0.0, 0.08, 0.205))

    # rotor: one blade bar with amber tips
    p = Part(pal)
    p.box((0, 0, 0.0), (0.30, 0.042, 0.008), 'ink')
    for sx in (-1, 1):
        p.box((sx * 0.168, 0, 0.0), (0.036, 0.042, 0.008), 'amber', deco=True)
    p.build('BOT_DRONE_Rotor', bevel=False, hull=0.008)

    # gun on its gimbal (origin on the pivot, barrel along -Y)
    p = Part(pal)
    p.box((0, 0, 0), (0.08, 0.06, 0.06), 'gunmetal')
    p.cyl((0, -0.01, 0), 0.026, 0.026, 0.19, 'alu', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.17, 0), 0.036, 0.036, 0.04, 'gunmetal', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.06, 0), 0.031, 0.031, 0.03, 'amber', seg=6, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, -0.207, 0), 0.018, 0.018, 0.006, 'ink', seg=6, rot=(90, 0, 0), deco=True)
    gun = p.build('BOT_DRONE_Gun', bevel=False)
    socket('BOT_DRONE_GUN', gun, (0, -0.22, 0))

    p = Part(pal)
    p.box((0, 0, 0), (0.06, 0.06, 0.06), 'light')
    p.build('BOT_DRONE_Light', bevel=False, hull=0.008)


# ================================================================ BOTS
def build_bots(ao):
    pal = Palette('bots')
    build_crawler(pal)
    build_gunner(pal)
    build_bomber(pal)
    build_drone(pal)
    export('bots')
