"""INKBOLT kit-hotel ("The Aurelian", a grand hotel tower; campaign level 20): palette, kit class and the furniture
helpers shared by hotel_struct.py (walls, gates, trail, stairs, ceilings, floors), hotel_props.py (lobby, ballroom,
sky deck, street) and hotel_rooms.py (the open suites).

Conventions (src/data/themes.js, src/game/zones.js):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z, the room). Wall modules are 9 m tall (double-height floors); the
    lobby mezzanine stands at 4.5 m (slab 4.1 - 4.5); ceiling pieces hang from their origin (the 9 m ceiling plane).
  * Interior wall modules are two-sided (the same panelling on both faces): a one-cell partition shows a finished
    face to both rooms whichever way the engine turns it.
  * Collision: <Piece>_COL<n> empties; <Piece>_WCOL<n> for boxes robots may walk on (stairs, the bandstand).
  * Shapes marked ink=False get no outline shell (trims, painted quads, small detail).
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
import fam_kit_spire as S
import hotel_detail as D

FAM = 'kit-hotel'
PFX = 'KIT_HOTEL_'
ib_lib.GLB[FAM] = 'fps-kit-hotel.glb'
ib_lib.CFG[FAM] = (0.012, 0.014)
HULL_T = ib_lib.CFG[FAM][1]
H = 9.0          # wall / ceiling height
DECK = 4.5       # lobby mezzanine floor (slab 4.1 - 4.5)
RH = 3.3         # suite ceiling
DROP = 3.2       # service corridor (trail) drop ceiling = the gate opening

ib_lib.PALETTES[FAM] = BASE + [
    ('marble', '#F3ECDF'), ('marble2', '#E3D7C3'), ('vein', '#C8B9A2'), ('nero', '#2B2630'), ('nero2', '#4B4350'),
    ('stone', '#E8DBC3'), ('stone2', '#CDBB9C'), ('gold', '#F0C24E'), ('brass', '#CF9F43'), ('bronze', '#8C6430'),
    ('walnut', '#7C4A2D'), ('walnut2', '#57321E'), ('oak', '#C9955F'),
    ('wine', '#922A3C'), ('wine2', '#6B1B2B'), ('wine3', '#4C1220'), ('emerald', '#2F7F60'), ('emerald2', '#1F5A45'),
    ('navy', '#2A4570'), ('navy2', '#1C2E4E'), ('teal2', '#2E7E86'),
    ('cream', '#F7EEDB'), ('ivory', '#FCF7EC'), ('silk', '#EAD7B2'), ('silk2', '#D8BE8E'), ('cgold', '#D9A84C'),
    ('glow', '#FFF2CC'), ('lamp', '#FFE3A3'), ('shade', '#F5DFB0'), ('crystal', '#F3FAFF'), ('crystal2', '#CFE3EE'),
    ('glint', '#FAFDFF'), ('glassT', '#A9CCDC'),
    ('leaf', '#4E9F58'), ('leaf2', '#2E7446'), ('rose', '#E05470'), ('blush', '#F3AFBD'), ('pot', '#EEE6D6'),
    ('soil', '#5A4232'), ('steel', '#C9CDD3'), ('steel2', '#979DA7'), ('chrome', '#E6EAF0'),
    ('block', '#DAD3C3'), ('block2', '#C2BAA8'), ('svc', '#5C8A70'),
    ('water', '#3AA6D4'), ('waterL', '#A4E0F2'), ('tile', '#5FBBD3'), ('teak', '#B57D49'), ('teak2', '#8C5A33'),
    ('screen', '#283849'), ('black', '#1D1A21'), ('fire', '#FF8B2B'), ('sky', '#9FD0EC'), ('canvas', '#E9DDC4'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]
# upholstery cells the theme repaints per placed copy (symbol option paint): wine, emerald, navy, teal2
FABRIC = ['wine', 'emerald', 'navy', 'teal2']

srt = S.srt
TRIS = {}


class HKit(S.SKit):
    """The Spire's kit (office Kit + walkable collision boxes + prisms) under this family's prefix."""

    def prism_z(self, pts, z0, z1, c, ink=True):
        """Polygon in the XY plane (convex or a simple outline), extruded along Z from z0 to z1."""
        P, bm = self.m.parent, self.m.bm
        a = [bm.verts.new(P @ Vector((x, y, z0))) for (x, y) in pts]
        b = [bm.verts.new(P @ Vector((x, y, z1))) for (x, y) in pts]
        fs = [bm.faces.new(a), bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.m._finish(a + b, c, False)
        self._mark(ink)

    def arc(self, cx, cy, r0, r1, a0, a1, n, z0, z1, c, ink=True):
        """A curved band (annulus sector) from angle a0 to a1 in n segments, extruded z0..z1."""
        for i in range(n):
            b0, b1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
            self.prism_z([(cx + math.cos(b0) * r0, cy + math.sin(b0) * r0), (cx + math.cos(b1) * r0, cy + math.sin(b1) * r0),
                          (cx + math.cos(b1) * r1, cy + math.sin(b1) * r1), (cx + math.cos(b0) * r1, cy + math.sin(b0) * r1)], z0, z1, c, ink)

    def finish(self, name, bevel=0.0, ao=False):
        full = PFX + name
        m = self.m
        check_zfight(full, m.bm, m.shape)
        flat = self.flat
        fb = m.bm.copy()
        bmesh.ops.delete(m.bm, geom=[f for f in m.bm.faces if f[m.shape] in flat], context='FACES')
        fm = Model(self.pal)
        fm.bm.free()
        fm.bm = fb
        fm.bw = fb.edges.layers.float['bevel_weight_edge']
        fm.shape = fb.faces.layers.int['shape_id']
        bmesh.ops.delete(fb, geom=[f for f in fb.faces if f[fm.shape] not in flat], context='FACES')
        obj = None
        if len(m.bm.faces):
            obj = build_object(full, m, bevel, HULL_T, ao=ao)
        else:
            m.bm.free()
        if len(fb.faces):
            # flat detail (lettering, painted quads) comes as loose triangles: weld coincident corners so the export
            # shares them (same plane, colour and normal), a third of the vertices for a line of text
            bmesh.ops.remove_doubles(fb, verts=fb.verts[:], dist=1e-5)
            o2 = build_object(full + '_flat', fm, 0, 0.0)
            strip_hull(o2)
            if obj is None:
                obj = o2
                obj.name = full
                obj.data.name = full
            else:
                join_into(obj, o2)
        else:
            fb.free()
        P = self.base.to_3x3()
        for i, (x0, x1, y0, y1, z0, z1, walk) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_%sCOL%d' % (full, 'W' if walk else '', i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj


def txt(k, s, x, y, z, cap, c, face='y-', font='serif', align='c', valign='b', maxw=None, clip=None, shadow=None):
    return ib_text.draw(k, s, x, y, z, cap, c, face=face, font=font, align=align, valign=valign, maxw=maxw, clip=clip,
                        shadow=shadow)


def disc(k, x, y, z, r, c, n=12, up=True):
    k.poly([(x + math.cos(i / n * math.pi * 2) * r, y + math.sin(i / n * math.pi * 2) * r, z) for i in range(n)], c,
           (0, 0, 1 if up else -1))


def vdisc(k, x, y, z, r, c, n=12, s=-1):
    """Disc on a plane facing s * Y (a clock face, a dial)."""
    k.poly([(x + math.cos(i / n * math.pi * 2) * r, y, z + math.sin(i / n * math.pi * 2) * r) for i in range(n)], c, (0, s, 0))


def frame_y(k, x0, x1, z0, z1, y, s, c, t=0.03):
    """A rectangular moulding (four strips, no overlaps at the corners) on a plane at y facing s * Y."""
    k.qy(x0, x1, z0, z0 + t, y, s, c)
    k.qy(x0, x1, z1 - t, z1, y, s, c)
    k.qy(x0, x0 + t, z0 + t, z1 - t, y, s, c)
    k.qy(x1 - t, x1, z0 + t, z1 - t, y, s, c)


def ring(k, r, z, n, t, c, ink=True, cx=0.0, cy=0.0):
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        k.beam((cx + math.cos(a0) * r, cy + math.sin(a0) * r, z), (cx + math.cos(a1) * r, cy + math.sin(a1) * r, z), t, c, ink=ink)


# ================================================================ furniture (local frames face -Y)
def legs4(k, x0, x1, y0, y1, h, c='walnut2', t=0.04):
    for x in (x0, x1 - t):
        for y in (y0, y1 - t):
            k.bx(x, x + t, y, y + t, 0, h, c, ink=False)


def dining_chair(k, x, y, deg, fab='wine', frame='walnut'):
    """Upholstered dining / side chair; the sitter faces local -Y (back at +Y)."""
    k.push(x, y, deg)
    legs4(k, -0.21, 0.21, -0.21, 0.21, 0.42, frame, 0.04)
    k.bx(-0.23, 0.23, -0.23, 0.22, 0.42, 0.5, fab)
    k.bx(-0.21, 0.21, 0.17, 0.22, 0.5, 1.0, frame)
    k.qy(-0.16, 0.16, 0.58, 0.92, 0.167, -1, fab)
    k.pop()


def gold_chair(k, x, y, deg, seat='ivory'):
    """Gilt chiavari banquet chair (slim rails), the sitter faces local -Y."""
    k.push(x, y, deg)
    for sx in (-0.18, 0.15):
        for sy in (-0.19, 0.16):
            k.bx(sx, sx + 0.03, sy, sy + 0.03, 0, 0.45, 'gold', ink=False)
    k.bx(-0.2, 0.2, -0.21, 0.2, 0.43, 0.5, seat)
    for sx in (-0.18, 0.15):
        k.bx(sx, sx + 0.03, 0.16, 0.19, 0.5, 0.98, 'gold', ink=False)
    for z in (0.66, 0.88):
        k.bx(-0.15, 0.15, 0.165, 0.185, z, z + 0.025, 'gold', ink=False)
    k.pop()


def armchair(k, x, y, deg, fab='wine', leg='walnut2', wing=False):
    """Club armchair; the sitter faces local -Y."""
    k.push(x, y, deg)
    k.bx(-0.42, 0.42, -0.4, 0.4, 0.1, 0.42, fab)
    k.bx(-0.42, 0.42, 0.2, 0.4, 0.42, 0.95 if wing else 0.82, fab)
    for t in (-1, 1):
        x0, x1 = srt(t * 0.28, t * 0.42)
        k.bx(x0, x1, -0.4, 0.2, 0.42, 0.64, fab)
        if wing:
            k.bx(x0, x1, 0.05, 0.2, 0.64, 0.95, fab)
        for yy in (-0.35, 0.35):
            k.bx(t * 0.36 - 0.025, t * 0.36 + 0.025, yy - 0.025, yy + 0.025, 0, 0.1, leg, ink=False)
    k.bx(-0.28, 0.28, -0.4, 0.2, 0.42, 0.52, fab, ink=False)
    k.qz(-0.25, 0.25, -0.37, 0.17, 0.523, 1, 'cream' if fab != 'cream' else 'silk')
    D.armchair_detail(k)
    k.pop()


def sofa(k, x, y, deg, w=2.0, fab='wine', leg='walnut2', tufts=True):
    """Chesterfield-style sofa w wide; the sitters face local -Y (back at +Y)."""
    k.push(x, y, deg)
    hw = w / 2
    k.bx(-hw, hw, -0.42, 0.42, 0.1, 0.42, fab)
    k.bx(-hw, hw, 0.18, 0.42, 0.42, 0.84, fab)
    for t in (-1, 1):
        x0, x1 = srt(t * (hw - 0.18), t * hw)
        k.bx(x0, x1, -0.42, 0.18, 0.42, 0.7, fab)
        k.cyl(t * (hw - 0.09), -0.44, 0.7, 0.1, 0.1, 0.6, fab, seg=8, rot=(-90, 0, 0), ink=False)
        for yy in (-0.37, 0.37):
            k.bx(t * (hw - 0.08) - 0.03, t * (hw - 0.08) + 0.03, yy - 0.03, yy + 0.03, 0, 0.1, leg, ink=False)
    n = max(2, int(round((w - 0.36) / 0.6)))
    cw = (w - 0.36) / n
    for i in range(n):
        x0 = -hw + 0.18 + i * cw
        k.bx(x0 + 0.004, x0 + cw - 0.004, -0.42, 0.18, 0.42, 0.53, fab)
    if tufts:
        for i in range(int(w / 0.25)):
            xx = -hw + 0.3 + i * 0.25
            if xx > hw - 0.3:
                break
            for zz in (0.62, 0.74):
                k.qy(xx - 0.012, xx + 0.012, zz - 0.012, zz + 0.012, 0.177, -1, 'black')
    D.sofa_detail(k, hw, w)
    k.pop()


def side_table(k, x, y, h=0.55, top='marble', r=0.25):
    k.cyl(x, y, 0, 0.16, 0.16, 0.03, 'brass', seg=10, ink=False)
    k.cyl(x, y, 0.03, 0.03, 0.03, h - 0.06, 'brass', seg=6, ink=False)
    k.cyl(x, y, h - 0.04, r, r, 0.04, top, seg=8)


def table_lamp(k, x, y, z, s=1.0, base='brass'):
    k.cyl(x, y, z, 0.08 * s, 0.08 * s, 0.03 * s, base, seg=6, ink=False)
    k.cyl(x, y, z + 0.03 * s, 0.05 * s, 0.03 * s, 0.25 * s, base, seg=6)
    k.cyl(x, y, z + 0.28 * s, 0.012, 0.012, 0.1 * s, base, seg=4, ink=False)
    k.cyl(x, y, z + 0.32 * s, 0.17 * s, 0.11 * s, 0.2 * s, 'shade', seg=8)
    disc(k, x, y, z + 0.32 * s - 0.004, 0.15 * s, 'glow', n=8, up=False)


def floor_lamp(k, x, y, s=1.0):
    k.cyl(x, y, 0, 0.16, 0.16, 0.03, 'bronze', seg=10, ink=False)
    k.cyl(x, y, 0.03, 0.018, 0.018, 1.3 * s, 'brass', seg=5, ink=False)
    k.cyl(x, y, 1.3 * s, 0.24, 0.16, 0.3, 'shade', seg=10)
    disc(k, x, y, 1.3 * s - 0.004, 0.22, 'glow', n=10, up=False)


def flowers(k, x, y, z, s=1.0, kind='rose', vase='crystal2', tall=False):
    """A vase with a dome of blooms and a few leaves; base at z."""
    h = (0.34 if tall else 0.2) * s
    k.cyl(x, y, z, 0.07 * s, 0.1 * s, h, vase, seg=6)
    cols = {'rose': ('rose', 'blush', 'ivory'), 'white': ('ivory', 'white', 'blush'), 'gold': ('gold', 'ivory', 'amber'),
            'red': ('rose', 'wine', 'rose')}[kind]
    top = z + h
    k.sph(x, y, top + 0.1 * s, 0.17 * s, 'leaf2', seg=(6, 3), scale=(1, 1, 0.7))
    for i in range(6):
        a = i / 6 * math.pi * 2
        r = 0.12 * s
        k.sph(x + math.cos(a) * r, y + math.sin(a) * r, top + 0.14 * s + 0.03 * s * (i % 2), 0.06 * s, cols[i % 3], seg=(4, 2), ink=False)
    k.sph(x, y, top + 0.21 * s, 0.065 * s, cols[0], seg=(4, 2), ink=False)
    for i in range(3):
        a = i / 3 * math.pi * 2 + 0.4
        k.beam((x, y, top + 0.05 * s), (x + math.cos(a) * 0.26 * s, y + math.sin(a) * 0.26 * s, top - 0.02 * s), 0.04 * s, 'leaf', ink=False)


def palm(k, x, y, s=1.0, urn='stone'):
    """Potted kentia palm in a classical urn (base at the floor)."""
    k.cyl(x, y, 0, 0.2 * s, 0.2 * s, 0.08 * s, urn, seg=10)
    k.cyl(x, y, 0.08 * s, 0.1 * s, 0.14 * s, 0.18 * s, urn, seg=10, ink=False)
    k.cyl(x, y, 0.26 * s, 0.2 * s, 0.32 * s, 0.4 * s, urn, seg=12)
    k.cyl(x, y, 0.62 * s, 0.33 * s, 0.33 * s, 0.05 * s, 'brass', seg=12, ink=False)
    k.cyl(x, y, 0.66 * s, 0.29 * s, 0.29 * s, 0.006, 'soil', seg=10, ink=False)
    for i in range(7):
        a = i / 7 * math.pi * 2 + 0.2
        ca, sa = math.cos(a), math.sin(a)
        mid = (x + ca * 0.25 * s, y + sa * 0.25 * s, (1.55 + 0.18 * (i % 3)) * s)
        k.beam((x + ca * 0.04, y + sa * 0.04, 0.66 * s), mid, 0.03 * s, 'oak', ink=False)
        k.beam(mid, (x + ca * 0.85 * s, y + sa * 0.85 * s, (1.2 + 0.15 * (i % 2)) * s), 0.12 * s, 'leaf' if i % 2 else 'leaf2')


def topiary(k, x, y, s=1.0, pot='nero'):
    """Boxwood ball on a stem in a square planter."""
    k.bx(x - 0.26 * s, x + 0.26 * s, y - 0.26 * s, y + 0.26 * s, 0, 0.55 * s, pot)
    k.bx(x - 0.29 * s, x + 0.29 * s, y - 0.29 * s, y + 0.29 * s, 0.55 * s, 0.6 * s, 'brass', ink=False)
    k.qz(x - 0.24 * s, x + 0.24 * s, y - 0.24 * s, y + 0.24 * s, 0.604 * s, 1, 'soil')
    k.cyl(x, y, 0.6 * s, 0.025, 0.025, 0.5 * s, 'walnut2', seg=5, ink=False)
    k.sph(x, y, 1.35 * s, 0.36 * s, 'leaf2', seg=(8, 6))


def painting(k, x, y, z0, w, h, scheme=0, s=-1, frame='gold'):
    """Framed oil painting on a plane at y facing s * Y: gilt frame, canvas and a simple picture (each paint layer
    3 mm proud of the one under it)."""
    d = 0.06
    y0, y1 = srt(y, y + s * d)
    k.bx(x - w / 2, x + w / 2, y0, y1, z0, z0 + h, frame)
    fw = 0.09
    a0, a1, b0, b1 = x - w / 2 + fw, x + w / 2 - fw, z0 + fw, z0 + h - fw
    W, Hh = a1 - a0, b1 - b0

    def L(n, pts, c):
        yy = y + s * (d + 0.003 * (n + 1))
        k.poly([(a0 + u * W, yy, b0 + v * Hh) for (u, v) in pts], c, (0, s, 0))
    if scheme == 0:      # landscape: sky, distant hills, meadow, a lake, a tree, the sun
        L(0, [(0, 0), (1, 0), (1, 1), (0, 1)], 'sky')
        L(1, [(0, 0), (1, 0), (1, 0.6), (0.75, 0.5), (0.45, 0.62), (0, 0.3)], 'emerald')
        L(2, [(0, 0), (1, 0), (1, 0.3), (0, 0.3)], 'leaf2')
        L(3, [(0.15, 0.08), (0.7, 0.08), (0.62, 0.22), (0.25, 0.22)], 'waterL')
        L(3, [(0.78, 0.25), (0.84, 0.25), (0.84, 0.55), (0.78, 0.55)], 'walnut2')
        L(4, [(0.68, 0.5), (0.94, 0.5), (0.81, 0.85)], 'leaf')
        L(1, [(0.12, 0.78), (0.2, 0.78), (0.2, 0.86), (0.12, 0.86)], 'gold')
    elif scheme == 1:    # portrait: a dark ground, a figure in a wine coat
        L(0, [(0, 0), (1, 0), (1, 1), (0, 1)], 'nero2')
        L(1, [(0.2, 0), (0.8, 0), (0.72, 0.5), (0.5, 0.58), (0.28, 0.5)], 'wine')
        L(2, [(0.4, 0.55), (0.6, 0.55), (0.62, 0.78), (0.5, 0.86), (0.38, 0.78)], 'blush')
        L(3, [(0.37, 0.76), (0.63, 0.76), (0.6, 0.9), (0.4, 0.9)], 'walnut2')
        L(2, [(0.44, 0.3), (0.56, 0.3), (0.5, 0.48)], 'ivory')
    elif scheme == 2:    # still life: a vase of flowers on a table
        L(0, [(0, 0), (1, 0), (1, 1), (0, 1)], 'emerald2')
        L(1, [(0, 0), (1, 0), (1, 0.25), (0, 0.25)], 'walnut')
        L(2, [(0.4, 0.25), (0.6, 0.25), (0.64, 0.5), (0.36, 0.5)], 'crystal2')
        for i, (u, v, c) in enumerate(((0.5, 0.68, 'rose'), (0.36, 0.6, 'ivory'), (0.64, 0.62, 'gold'), (0.45, 0.78, 'blush'), (0.58, 0.8, 'rose'))):
            L(3 + i, [(u - 0.08, v - 0.06), (u + 0.08, v - 0.06), (u + 0.08, v + 0.06), (u - 0.08, v + 0.06)], c)
    else:                # seascape at dusk: sky and sea, the sun, a sail
        L(0, [(0, 0), (1, 0), (1, 1), (0, 1)], 'blush')
        L(1, [(0, 0), (1, 0), (1, 0.5), (0, 0.5)], 'navy')
        L(1, [(0.62, 0.62), (0.74, 0.62), (0.74, 0.74), (0.62, 0.74)], 'amber')
        L(2, [(0.25, 0.3), (0.45, 0.3), (0.38, 0.75)], 'ivory')
        L(2, [(0.2, 0.25), (0.5, 0.25), (0.46, 0.3), (0.24, 0.3)], 'walnut2')
    return y + s * (d + 0.03)


def sconce(k, x, y, z, s=-1, arms=2):
    """Brass wall sconce on a plane at y facing s * Y: a backplate, curved arms, pleated shades with a glow."""
    y0, y1 = srt(y, y + s * 0.03)
    k.bx(x - 0.07, x + 0.07, y0, y1, z - 0.18, z + 0.12, 'brass')
    offs = (-0.17, 0.17) if arms == 2 else (0.0,)
    for dx in offs:
        tip = (x + dx, y + s * 0.2, z + 0.05)
        if dx:
            k.beam((x, y + s * 0.03, z - 0.08), (x + dx * 0.6, y + s * 0.14, z - 0.1), 0.025, 'brass', ink=False)
            k.beam((x + dx * 0.6, y + s * 0.14, z - 0.1), tip, 0.025, 'brass', ink=False)
        else:
            k.beam((x, y + s * 0.03, z - 0.08), tip, 0.025, 'brass', ink=False)
        k.cyl(tip[0], tip[1], tip[2], 0.075, 0.05, 0.13, 'shade', seg=6)
        disc(k, tip[0], tip[1], tip[2] - 0.004, 0.065, 'glow', n=6, up=False)


def rug(k, x0, x1, y0, y1, z=0.036, field='wine', border='cgold', inner='navy', medal=True):
    k.qz(x0, x1, y0, y1, z, 1, border)
    b = min(0.18, (x1 - x0) * 0.08)
    k.qz(x0 + b, x1 - b, y0 + b, y1 - b, z + 0.003, 1, field)
    if medal:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) * 0.22, (y1 - y0) * 0.22
        k.poly([(cx, cy - ry, z + 0.006), (cx + rx, cy, z + 0.006), (cx, cy + ry, z + 0.006), (cx - rx, cy, z + 0.006)], inner, (0, 0, 1))
        k.poly([(cx, cy - ry * 0.5, z + 0.009), (cx + rx * 0.5, cy, z + 0.009), (cx, cy + ry * 0.5, z + 0.009), (cx - rx * 0.5, cy, z + 0.009)], border, (0, 0, 1))
        for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            px, py = cx + sx * (x1 - x0) * 0.36, cy + sy * (y1 - y0) * 0.33
            k.qz(px - 0.06, px + 0.06, py - 0.06, py + 0.06, z + 0.006, 1, border)


def coffee_table(k, x, y, w, d, h=0.42, top='marble', base='brass'):
    k.bx(x - w / 2, x + w / 2, y - d / 2, y + d / 2, h - 0.05, h, top)
    k.bx(x - w / 2 + 0.1, x + w / 2 - 0.1, y - d / 2 + 0.1, y + d / 2 - 0.1, 0.04, 0.07, base, ink=False)
    for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px, py = x + sx * (w / 2 - 0.08), y + sy * (d / 2 - 0.08)
        k.bx(px - 0.02, px + 0.02, py - 0.02, py + 0.02, 0, h - 0.05, base, ink=False)


def books(k, x, y, z, n=3, deg=0):
    cols = ('wine', 'navy', 'emerald', 'cream', 'cgold')
    k.push(x, y, deg, z)
    zz = 0.0
    for i in range(n):
        w, d, t = 0.28 - 0.03 * (i % 2), 0.2, 0.035
        k.bx(-w / 2, w / 2, -d / 2, d / 2, zz, zz + t, cols[(i + n) % 5], ink=False)
        zz += t
    k.pop()


def suitcase(k, x, y, z, w, d, h, c, deg=0):
    k.push(x, y, deg, z)
    k.bx(-w / 2, w / 2, -d / 2, d / 2, 0, h, c)
    k.bx(-w / 2 - 0.004, w / 2 + 0.004, -0.02, 0.02, 0.02, h - 0.02, 'walnut2', ink=False)
    k.bx(-0.08, 0.08, -0.025, 0.025, h - 0.01, h + 0.04, 'black', ink=False)
    k.pop()
