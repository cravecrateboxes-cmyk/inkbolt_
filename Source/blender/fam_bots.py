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
    ('core', '#FFC23A'), ('light', '#FFFFFF'), ('trim', '#4B515E'), ('pouch', '#6E7262'),
    # Gunner: armoured gun sentry (keeps its green so the type reads at a glance)
    ('bin', _lighten('#44975E')), ('bin2', _lighten('#2F6B45', 0.06)), ('rubber', _lighten('#3A3844', 0.06)), ('steel', _lighten('#9AA6B4')),
    ('core2', '#E9A21F'), ('sticker', '#FFF1D6'),
    # Bomber: fizzing bottle on a roller
    ('glass', _lighten('#3E86D8')), ('glass2', _lighten('#2F6DB8')), ('capred', _lighten('#F0443A', 0.06)), ('label', '#FFF7E6'),
    ('wick', '#7A5638'),
    # Drone: soda can
    ('can', _lighten('#E2483D')), ('can2', _lighten('#B93A31')), ('alu', _lighten('#C4CBD3')),
    ('tin3', _lighten('#7E8794')),
    # Soldier: armour plates in two KEY colours the game recolours per instance (white / grey / blue / purple /
    # black ...: ai troops.js matches these exact texels), an undersuit, a gold chest core
    ('plate', '#F4F6F9'), ('plate2', '#B8BEC7'), ('suit', '#3A3F4B'), ('suit2', '#5A606D'),
    # Blade bot: violet saucer with hazard chevrons, bright steel blades, a glowing Voltaxe edge
    ('violet', _lighten('#6A55A8')), ('violet2', _lighten('#4E3F82', 0.06)), ('blade', '#E8EEF4'), ('lens', '#7FF4FF'),
    # Hawk (levels 20+): graphite armoured fuselage, lighter dorsal plates, steel; its accents are drawn in the KEY
    # colours 'plate' / 'plate2' and take the colour of its round type in the game
    ('hawk', '#363B47'), ('hawk2', '#59606F'), ('hawk3', '#8C95A4'),
    # Jet Trooper (levels 35+): near-black armour like the black-ops soldiers (jet / jet2 / jet3); its element accents
    # (shoulder line, hex panels, pod tubes) are drawn in the KEY colours 'plate' / 'plate2' and painted by the game
    ('jet', '#2A2D34'), ('jet2', '#1D1F24'), ('jet3', '#40454F'), ('jetglow', '#FFE2A8'),
    # Blade Bot kusarigama: oiled wooden handle, dark iron chain and weight
    ('kwood', '#7A5233'), ('chain', '#6C7480'),
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

    def limb(self, a, b, r1, r2, color, seg=8, deco=False, caps=True):
        """Round segment (frustum) from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        old = self.parent
        self.parent = old @ Matrix.Translation(a) @ q.to_matrix().to_4x4()
        self.cyl((0, 0, 0), r1, r2, d.length, color, seg=seg, caps=caps, deco=deco)
        self.parent = old

    def prism(self, poly, z0, z1, color, deco=False, bevel=False):
        """Polygon (x, y) extruded from z0 to z1 (counter-clockwise polygon seen from +Z)."""
        for mm in self._each(deco):
            bm = mm.bm
            lo = [bm.verts.new(mm.parent @ Vector((x, y, z0))) for x, y in poly]
            hi = [bm.verts.new(mm.parent @ Vector((x, y, z1))) for x, y in poly]
            n = len(poly)
            bm.faces.new(list(reversed(lo)))
            bm.faces.new(hi)
            for k in range(n):
                k2 = (k + 1) % n
                bm.faces.new((lo[k], lo[k2], hi[k2], hi[k]))
            mm._finish(lo + hi, color, bevel and not deco)

    def blade(self, st, tip, color, edge_color):
        """Lens-section blade along +X: stations (x, y_back, y_edge, half_thickness); the faces next to the edge
        (+Y side) take edge_color (temper line / glowing edge); ends in the tip point."""
        for mm in self._each(False):
            bm = mm.bm
            rings = []
            for x, yb, ye, t in st:
                ys, yh = yb + (ye - yb) * 0.3, yb + (ye - yb) * 0.72
                pts = ((x, yb, 0), (x, ys, t), (x, yh, t * 0.5), (x, ye, 0), (x, yh, -t * 0.5), (x, ys, -t))
                rings.append([bm.verts.new(mm.parent @ Vector(p)) for p in pts])
            tv = bm.verts.new(mm.parent @ Vector(tip))
            faces = [bm.faces.new(rings[0])]
            edge = []
            for a, b in zip(rings, rings[1:]):
                for k in range(6):
                    k2 = (k + 1) % 6
                    f = bm.faces.new((a[k], b[k], b[k2], a[k2]))
                    faces.append(f)
                    if k in (2, 3):
                        edge.append(f)
            r = rings[-1]
            for k in range(6):
                f = bm.faces.new((r[k], tv, r[(k + 1) % 6]))
                if k in (2, 3):
                    edge.append(f)
            mm._finish([v for ring in rings for v in ring] + [tv], color, False)
            ei = mm.pal.index(edge_color)
            for f in edge:
                f.material_index = ei

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
# Tin can on 4 spring legs, kitted out a touch tactical: corrugated tin, dark gunmetal rim and webbing belt with two
# drab pouches, a bolted front plate under a hooded visor slot, whip + stub antennas (light), gold core dome (weak point).
def build_crawler(pal):
    p = Part(pal)
    p.cyl((0, 0, 0.30), 0.32, 0.31, 0.42, 'tin', seg=10, bevel=True)
    p.cyl((0, 0, 0.72), 0.35, 0.35, 0.05, 'trim', seg=10, bevel=True)                 # rolled top rim
    p.box((0, -0.31, 0.60), (0.34, 0.07, 0.07), 'ink')                                  # sensor slot (front = -Y)
    p.box((0, -0.349, 0.60), (0.22, 0.02, 0.03), 'amber')
    p.sphere((0, 0, 0.77), 0.14, 'core', seg=(8, 4), scale=(1, 1, 0.6))
    p.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=3)
    # deco: webbing belt + pouches, corrugation ridges, front plate, visor hood, seam rivets, stub antenna, core seat ring
    p.cyl((0, 0, 0.405), 0.335, 0.335, 0.065, 'trim', seg=10, caps=False, deco=True)
    p.cyl((0, 0, 0.585), 0.326, 0.326, 0.016, 'tin2', seg=10, caps=False, deco=True)
    for k in (4, 0):                                                                     # pouches hung on the belt
        p.on_facet(k, 10, 0.335, 0.002, 0.405, (0.13, 0.055, 0.12), 'pouch')
    p.on_facet(7, 10, 0.32, 0.003, 0.505, (0.22, 0.012, 0.09), 'tin3')                 # bolted front plate
    for x in (-0.085, 0.085):
        p.box((x, -0.3225, 0.505), (0.022, 0.012, 0.022), 'trim', deco=True)
    p.box((0, -0.322, 0.649), (0.38, 0.10, 0.024), 'trim', rot=(-8, 0, 0), deco=True)   # visor hood over the slot
    p.cyl((-0.15, 0.09, 0.755), 0.014, 0.014, 0.13, 'ink', seg=4, deco=True)            # stub antenna
    p.box((-0.15, 0.09, 0.895), (0.04, 0.04, 0.03), 'trim', deco=True)
    for z in (0.47, 0.54):
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
# Armoured gun sentry (green = the Gunner): an angular hull on two rear drive wheels and front claw skids, sloped glacis
# with hazard chevrons, side armour sponsons, a 4-cell rocket pod on the right shoulder, a rear power pack carrying the
# antenna, and an armoured dorsal cowl (the Lid, sensor slit in its brow) that lifts during the windup to bare a twin
# autocannon clamped on a gold battery (the core) at the front. The gun pitches about the battery axis.
# Socket positions are unchanged from the bin version, so ai.js poses and hit volumes stay identical.
G_HINGE = (0, 0.372, 1.0)
G_PIVOT = (0, -0.405, 0.835)        # battery axis centre = gun trunnion
G_WHEEL = (0.318, 0.30, 0.125)
G_WHEEL_R = 0.125
G_LIGHT = (0.24, 0.47, 1.43)
G_HW = 0.255                        # hull half width (x)
G_PROF = [(-0.215, 0.075), (0.255, 0.075), (0.345, 0.30), (0.345, 0.63), (0.325, 0.955), (-0.255, 0.955),
          (-0.300, 0.715), (-0.355, 0.40)]      # hull side profile (y, z), front = -y
_YZX = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # local (a, b, c) -> world (c, a, b)


def _parea(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))


def sprism(p, poly, x0, x1, color, deco=False, bevel=False):
    """Side-profile prism: polygon in (y, z) extruded along X from x0 to x1."""
    if _parea(poly) < 0:
        poly = list(reversed(poly))
    x0, x1 = min(x0, x1), max(x0, x1)
    old = p.parent
    p.parent = old @ _YZX
    p.prism(poly, x0, x1, color, deco=deco, bevel=bevel)
    p.parent = old


def on_edge(prof, i, t, out, x=0.0):
    """Frame on edge i of a side profile at t along it (x = across, y = along the edge, z = outward normal), `out` m proud."""
    a, b = Vector(prof[i]), Vector(prof[(i + 1) % len(prof)])
    u = (b - a).normalized()
    n = Vector((u.y, -u.x))
    c = Vector((sum(q[0] for q in prof) / len(prof), sum(q[1] for q in prof) / len(prof)))
    pt = a + (b - a) * t
    if n.dot(pt - c) < 0:
        n = -n
    ey = Vector((0, u.x, u.y))
    ez = Vector((0, n.x, n.y))
    if Vector((1, 0, 0)).cross(ey).dot(ez) < 0:
        ey = -ey
    o = Vector((x, pt.x, pt.y)) + ez * out
    m = Matrix.Identity(4)
    for r in range(3):
        m[r][0], m[r][1], m[r][2], m[r][3] = (1, 0, 0)[r], ey[r], ez[r], o[r]
    return m


def hazard(p, frame, w, h, color='amber', n=5, t=0.004):
    """Hazard panel on a frame: amber plate with ink chevron bars (all deco)."""
    old = p.parent
    p.parent = old @ frame
    p.box((0, 0, t / 2 - 0.0005), (w, h, t + 0.001), color, deco=True)
    s = w / n
    for k in range(n):
        x = -w / 2 + s * (k + 0.25)
        poly = [(x, -h / 2), (x + s * 0.45, -h / 2), (x + s * 0.45 + h * 0.35, h / 2), (x + h * 0.35, h / 2)]
        poly = [(min(max(px, -w / 2), w / 2), py) for px, py in poly]
        if abs(_parea(poly)) > 1e-6:
            p.prism(poly, t + 0.0025, t + 0.0075, 'ink', deco=True)
    p.parent = old


def build_gunner(pal):
    P_ = G_PROF
    p = Part(pal)
    # hull: angular core prism, side armour sponsons (stepped out), glacis cheek plates
    sprism(p, P_, -G_HW, G_HW, 'bin')
    sprism(p, [(-0.207, 0.068), (0.249, 0.068), (0.354, 0.33), (-0.333, 0.33)], -G_HW - 0.01, G_HW + 0.01, 'gunmetal')  # dark chassis
    spon = [(-0.300, 0.33), (0.190, 0.33), (0.240, 0.42), (0.240, 0.83), (-0.255, 0.86), (-0.320, 0.60)]
    for sx in (-1, 1):                                                                     # flared 7 deg: wider at the shoulder
        p.parent = Matrix.Translation((sx * 0.25, 0, 0.33)) @ Matrix.Rotation(math.radians(7 * sx), 4, 'Y') @ Matrix.Translation((-sx * 0.25, 0, -0.33))
        sprism(p, spon, sx * 0.225, sx * 0.300, 'bin2')
        p.box((sx * 0.301, -0.04, 0.47), (0.008, 0.30, 0.03), 'ink', deco=True)          # vision cut + amber tick
        p.box((sx * 0.301, -0.04, 0.52), (0.008, 0.30, 0.015), 'amber', deco=True)
        for y in (-0.20, 0.10):
            p.cyl((sx * 0.296, y, 0.40), 0.016, 0.016, 0.008, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
    p.parent = Matrix.Identity(4)
    # rear power pack (carries the antenna) and the drive axle housing
    pack = [(0.300, 0.56), (0.470, 0.60), (0.500, 0.70), (0.470, 0.925), (0.300, 0.925)]
    sprism(p, pack, -0.27, 0.27, 'gunmetal')
    p.box((0, 0.30, 0.125), (0.56, 0.09, 0.09), 'gunmetal')
    # core: gold battery lying along X (the gun's trunnion), in an armoured cradle
    px, py, pz = G_PIVOT
    p.cyl((-0.17, py, pz), 0.075, 0.075, 0.34, 'core', seg=10, rot=(0, 90, 0))
    for sx in (-1, 1):
        sprism(p, [(-0.300, 0.73), (py, 0.745), (py - 0.03, 0.80), (-0.29, 0.86)], sx * 0.185, sx * 0.235, 'gunmetal')
        # front claw skids
        sprism(p, [(-0.30, 0.0), (-0.12, 0.0), (-0.10, 0.06), (-0.22, 0.14), (-0.33, 0.04)], sx * 0.12, sx * 0.22, 'gunmetal', bevel=False)
    # 4-cell rocket pod on the right shoulder
    pod = [(-0.27, 0.70), (0.13, 0.70), (0.16, 0.78), (0.13, 0.86), (-0.27, 0.86)]
    sprism(p, pod, 0.315, 0.440, 'gunmetal')
    lx, ly, lz = G_LIGHT
    p.cyl((lx, ly, 0.935), 0.012, 0.012, lz - 0.935 - 0.04, 'ink', seg=4)                    # antenna whip
    # ---- deco
    hazard(p, on_edge(P_, 7, 0.55, 0.009), 0.40, 0.15)                                # lower glacis chevrons
    p.parent = on_edge(P_, 6, 0.5, 0.0)                                                   # bolted chest plate + intake slits
    p.box((0, 0, 0.004), (0.36, 0.25, 0.010), 'bin2', deco=True)
    for x in (-0.06, 0.0, 0.06):
        p.box((x, 0.0, 0.0105), (0.022, 0.15, 0.006), 'ink', deco=True)
    for x in (-0.15, 0.15):
        for y in (-0.095, 0.095):
            p.cyl((x, y, 0.006), 0.014, 0.014, 0.008, 'steel', seg=6, deco=True)
    p.parent = Matrix.Identity(4)
    for sx in (-1, 1):                                                                     # sponson bolts + vision cut
        p.cyl((sx * 0.13 - 0.02, py, pz), 0.081, 0.081, 0.04, 'core2', seg=10, rot=(0, 90, 0), caps=False, deco=True)
    p.cyl((0.165, py, pz), 0.03, 0.03, 0.03, 'steel', seg=6, rot=(0, 90, 0), deco=True)   # + terminal
    for i in range(4):                                                                    # rocket pod tubes + red tips
        y0, z0 = -0.27, (0.745, 0.815)[i % 2]
        x0 = (0.407, 0.348)[i // 2]
        p.cyl((x0, y0 + 0.004, z0), 0.024, 0.024, 0.012, 'ink', seg=6, rot=(90, 0, 0), deco=True)
        p.cyl((x0, y0 - 0.004, z0), 0.012, 0.006, 0.014, 'red', seg=6, rot=(90, 0, 0), deco=True)
    p.box((0.443, -0.05, 0.78), (0.008, 0.20, 0.035), 'amber', deco=True)
    for t in (0.2, 0.4, 0.6, 0.8):                                                        # power pack cooling slats
        p.parent = on_edge(pack, 2, t, 0.0)
        p.box((0, 0, 0.0015), (0.40, 0.018, 0.006), 'ink', deco=True)
    p.parent = Matrix.Identity(4)
    p.box((0, 0.347, 0.45), (0.40, 0.008, 0.10), 'ink', deco=True)                       # rear hull vent
    p.cyl((lx, ly, 0.92), 0.03, 0.022, 0.035, 'steel', seg=6, deco=True)                  # antenna base
    p.box((0, -0.02, 0.962), (0.44, 0.52, 0.006), 'ink', deco=True)                       # dark bay (shows when the cowl lifts)
    body = p.build('BOT_GUNNER_Body')
    socket('BOT_GUNNER_CORE', body, (0, py, pz))
    socket('BOT_GUNNER_HINGE', body, G_HINGE)
    socket('BOT_GUNNER_GUNPIVOT', body, G_PIVOT)
    socket('BOT_GUNNER_LIGHT', body, G_LIGHT)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_GUNNER_WHEEL%d' % i, body, (sx * G_WHEEL[0], G_WHEEL[1], G_WHEEL[2]))

    # armoured cowl (origin on the hinge axis; extends toward -Y): a wedge with a sloped brow and a hanging front lip
    p = Part(pal)
    cowl = [(0.012, -0.020), (0.012, 0.045), (-0.07, 0.085), (-0.58, 0.085), (-0.735, 0.030), (-0.755, -0.035),
            (-0.705, -0.075), (-0.640, -0.020)]
    sprism(p, cowl, -0.315, 0.315, 'bin')
    sprism(p, [(-0.05, 0.07), (-0.56, 0.07), (-0.50, 0.115), (-0.10, 0.115)], -0.17, 0.17, 'bin2')   # raised spine plate
    p.parent = on_edge(cowl, 3, 0.5, 0.0)                                                 # brow: sensor slit
    p.box((0, 0, 0.004), (0.46, 0.05, 0.008), 'ink', deco=True)
    p.box((0, 0, 0.010), (0.36, 0.018, 0.006), 'amber', deco=True)
    p.parent = Matrix.Identity(4)
    hazard(p, on_edge(cowl, 4, 0.5, 0.0), 0.50, 0.045, n=5)                                 # lip hazard band
    for sx in (-1, 1):
        p.cyl((sx * 0.30 - 0.05, 0, 0.0), 0.028, 0.028, 0.10, 'gunmetal', seg=6, rot=(0, 90, 0), deco=True)  # knuckles
        for y in (-0.15, -0.45):
            p.cyl((sx * 0.25, y, 0.081), 0.014, 0.014, 0.008, 'steel', seg=6, deco=True)  # bolts
    p.build('BOT_GUNNER_Lid')

    # twin autocannon (origin on the battery axis; barrels along -Y)
    p = Part(pal)
    p.cyl((-0.05, 0, 0), 0.092, 0.092, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0))           # clamp collar
    p.box((0, -0.14, 0.01), (0.15, 0.15, 0.14), 'gunmetal', bevel=True)                   # receiver
    p.box((0, -0.29, 0.0), (0.12, 0.17, 0.07), 'bin2', bevel=True)                         # barrel shroud
    for sx in (-1, 1):
        p.cyl((sx * 0.032, -0.20, 0), 0.025, 0.025, 0.27, 'steel', seg=6, rot=(90, 0, 0))  # barrels
        p.cyl((sx * 0.032, -0.445, 0), 0.036, 0.036, 0.06, 'gunmetal', seg=6, rot=(90, 0, 0))   # muzzle brakes
        p.cyl((sx * 0.032, -0.500, 0), 0.016, 0.016, 0.009, 'ink', seg=6, rot=(90, 0, 0), deco=True)  # bores
        p.box((sx * 0.062, -0.29, 0.0), (0.006, 0.12, 0.016), 'ink', deco=True)          # shroud cooling slots
    p.box((0, -0.29, 0.037), (0.10, 0.12, 0.006), 'ink', deco=True)
    p.box((0, -0.12, 0.082), (0.11, 0.05, 0.006), 'amber', deco=True)                     # receiver hazard band
    gun = p.build('BOT_GUNNER_Gun', bevel=False)
    socket('BOT_GUNNER_GUN', gun, (0, -0.51, 0))

    # wheel (origin on the axle; axis X; symmetric so the game mirrors it for the other side)
    p = Part(pal)
    w = 0.075
    p.cyl((-w / 2, 0, 0), G_WHEEL_R, G_WHEEL_R, w, 'rubber', seg=8, rot=(0, 90, 0))
    p.cyl((-w / 2 - 0.004, 0, 0), 0.072, 0.072, w + 0.008, 'bin2', seg=6, rot=(0, 90, 0), deco=True)     # armoured hub
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


# ================================================================ SOLDIER
# Armoured robot trooper, human proportions (1.88 m), armour from helmet to boots. Rigid parts on pivots:
#   Hips (origin = feet; legs and hips face the way it walks), Thigh / Shin x2 (hip / knee pivots),
#   Torso A (trooper: round pauldrons) / B (heavy: chest slab, stacked pauldrons) on the waist pivot (it turns to aim),
#   Helm A (crest) / B (flat top, brow, antenna) / C (tall, cheek guards, red mohawk) on the neck pivot,
#   ArmR (holds the rifle: aims as one with ArmL about the shoulder line), ArmL (foregrip hand; throws the grenades),
#   Visor (glowing sensor bar in the helmet slit, coloured by the game), Nade (its grenade).
# No face, no eyes: the helmet has one visor slit. Armour is drawn in the two key colours 'plate' / 'plate2' that
# the game recolours per instance (white, grey, blue, purple, gunmetal black ...); the suit, rifle and core keep theirs.
S_HIP = 0.93            # hip joint height
S_HIPX = 0.115
S_THIGH = 0.43          # hip -> knee; knee -> sole 0.50
S_WAIST = 1.0
S_SHOULDER = (0.255, 0.0, 0.44)   # torso local (left = +x; the right arm is -x)
S_NECK = (0, 0.0, 0.53)
S_GRIP_R = (0.135, -0.24, -0.24)  # right hand (rifle grip) in right-shoulder space
S_HAND_L = (-0.375, -0.45, -0.19)  # left hand (foregrip) in left-shoulder space
S_RIFLE_X, S_RIFLE_Z = 0.135, -0.135
S_SLIT = (0, -0.170, 0.135)       # visor slit centre on the face plate (helmet space); plate front y = -0.170


def _elbow(a, b, la, lb, pole):
    a, b, pole = Vector(a), Vector(b), Vector(pole)
    d = b - a
    L = d.length
    u = d / L
    x = (la * la - lb * lb + L * L) / (2 * L)
    h = math.sqrt(max(0.0, la * la - x * x))
    w = pole - u * pole.dot(u)
    w.normalize()
    return tuple(a + u * x + w * h)


def _slit(p):
    """Face plate front at y = -0.170 (z 0.03..0.17 at least): the ink visor slit, 5 mm proud."""
    x, y, z = S_SLIT
    p.box((x, y, z), (0.17, 0.010, 0.032), 'ink', deco=True)


def build_soldier(pal):
    # ---- hips: pelvis, belt, codpiece, tassets, grenade cans on the belt
    p = Part(pal)
    p.box((0, 0, 0.92), (0.32, 0.22, 0.16), 'plate2', bevel=True)
    p.box((0, 0, 0.995), (0.34, 0.24, 0.05), 'suit')
    p.box((0, -0.125, 0.885), (0.14, 0.03, 0.14), 'plate', rot=(8, 0, 0), bevel=True)
    for sx in (-1, 1):
        p.box((sx * 0.165, -0.04, 0.865), (0.10, 0.17, 0.16), 'plate', rot=(0, sx * 12, 0), bevel=True)
    for x in (-0.07, 0.07):
        p.box((x, 0.135, 0.985), (0.08, 0.04, 0.05), 'suit2', deco=True)                  # back pouches
    for x in (-0.115, 0.115):
        p.cyl((x, -0.135, 0.955), 0.03, 0.03, 0.075, 'gunmetal', seg=8)                     # grenade cans
        p.cyl((x, -0.135, 0.985), 0.034, 0.034, 0.018, 'red', seg=8, caps=False, deco=True)
    p.box((0, -0.122, 0.995), (0.07, 0.008, 0.035), 'amber', deco=True)                 # buckle
    hips = p.build('BOT_SOLDIER_Hips', bevel=False)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_SOLDIER_HIP%d' % i, hips, (sx * S_HIPX, 0, S_HIP))
    socket('BOT_SOLDIER_WAIST', hips, (0, 0, S_WAIST))

    # ---- thigh (origin on the hip joint) and shin + boot (origin on the knee)
    p = Part(pal)
    p.sphere((0, 0, 0), 0.075, 'suit2', seg=(8, 5))
    p.limb((0, 0, -0.02), (0, 0, -0.41), 0.08, 0.066, 'suit')
    p.box((0, -0.065, -0.19), (0.13, 0.05, 0.27), 'plate', bevel=True)
    p.box((0, -0.0925, -0.13), (0.06, 0.008, 0.10), 'plate2', deco=True)
    p.build('BOT_SOLDIER_Thigh', bevel=False)
    p = Part(pal)
    p.sphere((0, 0, 0), 0.062, 'gunmetal', seg=(8, 5))
    p.box((0, -0.072, 0.0), (0.115, 0.06, 0.12), 'plate', bevel=True)
    p.limb((0, 0, -0.02), (0, 0, -0.40), 0.063, 0.056, 'suit')
    p.box((0, -0.052, -0.21), (0.12, 0.05, 0.25), 'plate', bevel=True)
    p.box((0, -0.045, -0.445), (0.13, 0.27, 0.11), 'plate2', bevel=True)
    p.box((0, -0.16, -0.462), (0.115, 0.06, 0.07), 'suit2')
    p.box((0, -0.045, -0.50), (0.10, 0.25, 0.008), 'ink', deco=True)                     # sole
    p.box((0, -0.0785, -0.16), (0.05, 0.008, 0.08), 'amber', deco=True)                  # shin stripe
    p.build('BOT_SOLDIER_Shin', bevel=False)

    # ---- torso A (trooper) and B (heavy); origin on the waist; gold core on the chest
    sx_, sy_, sz_ = S_SHOULDER
    for v in 'AB':
        p = Part(pal)
        p.cyl((0, 0, -0.04), 0.15, 0.16, 0.22, 'suit', seg=8)
        p.box((0, -0.155, 0.09), (0.22, 0.03, 0.12), 'plate2')                 # ab plate
        if v == 'A':
            p.box((0, -0.01, 0.31), (0.46, 0.30, 0.30), 'plate', bevel=True)
            p.cyl((0, 0, 0.45), 0.12, 0.12, 0.08, 'plate2', seg=10)                          # collar
            for s in (-1, 1):
                p.sphere((s * 0.27, 0, 0.445), 0.13, 'plate', seg=(8, 5), scale=(1, 1.05, 0.75))   # round pauldrons
            p.box((0, 0.2, 0.30), (0.34, 0.12, 0.30), 'plate2')                 # backpack
            cy = -0.16
            p.box((0, cy - 0.002, 0.215), (0.40, 0.012, 0.012), 'ink', deco=True)          # plate seam
            p.box((-0.15, cy - 0.002, 0.405), (0.08, 0.012, 0.025), 'amber', deco=True)    # unit stripe
            p.box((0.27, 0, 0.545), (0.06, 0.05, 0.012), 'amber', deco=True)               # pauldron chevron
        else:
            p.box((0, 0.0, 0.31), (0.50, 0.32, 0.32), 'plate2', bevel=True)
            p.box((0, -0.17, 0.30), (0.40, 0.06, 0.26), 'plate', bevel=True)                 # chest slab
            p.cyl((0, 0, 0.455), 0.13, 0.125, 0.10, 'plate', seg=10)                        # tall collar
            for s in (-1, 1):
                p.box((s * 0.285, 0, 0.475), (0.21, 0.25, 0.07), 'plate', rot=(0, s * 18, 0), bevel=True)
                p.box((s * 0.315, 0, 0.405), (0.18, 0.23, 0.06), 'plate2', rot=(0, s * 28, 0))
            p.box((0, 0.215, 0.29), (0.38, 0.13, 0.32), 'plate2')               # backpack
            for x in (-0.11, 0.0, 0.11):                                                    # spare grenades on the back
                p.cyl((x, 0.27, 0.36), 0.032, 0.032, 0.07, 'gunmetal', seg=8, rot=(-90, 0, 0))
            cy = -0.20
            for s in (-1, 1):
                p.box((s * 0.13, cy - 0.002, 0.20), (0.07, 0.012, 0.07), 'suit2', deco=True)   # slab pouches
            p.box((0.13, cy - 0.002, 0.405), (0.09, 0.012, 0.022), 'amber', deco=True)
        # core: gold reactor puck in the chest (weak point), gunmetal frame
        p.cyl((0, cy + 0.01, 0.315), 0.072, 0.072, 0.045, 'core', seg=10, rot=(90, 0, 0))
        p.cyl((0, cy + 0.006, 0.315), 0.088, 0.088, 0.022, 'gunmetal', seg=10, rot=(90, 0, 0), caps=False, deco=True)
        # backpack vents + antenna
        by = 0.26 if v == 'A' else 0.28
        for x in (-0.09, 0.09):
            p.cyl((x, by - 0.01, 0.20), 0.032, 0.032, 0.05, 'gunmetal', seg=8, rot=(-90, 0, 0))
        p.cyl((0.12, by - 0.06, 0.44), 0.011, 0.011, 0.22, 'ink', seg=4)
        t = p.build('BOT_SOLDIER_Torso' + v)
        if v == 'A':
            socket('BOT_SOLDIER_CORE', t, (0, -0.17, 0.315))
            socket('BOT_SOLDIER_NECK', t, S_NECK)
            socket('BOT_SOLDIER_SHOULDER0', t, (-sx_, sy_, sz_))
            socket('BOT_SOLDIER_SHOULDER1', t, (sx_, sy_, sz_))

    # ---- helmets (origin on the neck pivot); every one has the face plate + slit at the same spot
    def neck(p):
        p.cyl((0, 0, -0.03), 0.07, 0.075, 0.08, 'suit', seg=8)

    p = Part(pal)                                                                            # A: crest
    neck(p)
    p.sphere((0, 0.0, 0.16), 0.155, 'plate', seg=(12, 7), scale=(1, 1.08, 1.0))
    p.box((0, -0.12, 0.10), (0.20, 0.10, 0.14), 'plate2', bevel=True)
    p.box((0, -0.095, 0.03), (0.16, 0.08, 0.06), 'plate')
    p.box((0, 0.02, 0.31), (0.035, 0.26, 0.07), 'plate2')
    for s in (-1, 1):
        p.cyl((s * 0.13, 0, 0.14), 0.05, 0.05, 0.05, 'gunmetal', seg=8, rot=(0, s * 90, 0))
        p.box((s * 0.0195, 0.02, 0.315), (0.008, 0.20, 0.02), 'red', deco=True)
    _slit(p)
    hA = p.build('BOT_SOLDIER_HelmA')
    socket('BOT_SOLDIER_VISOR', hA, (S_SLIT[0], S_SLIT[1] - 0.004, S_SLIT[2]))

    p = Part(pal)                                                                            # B: flat top, brow, antenna
    neck(p)
    p.box((0, 0.005, 0.15), (0.29, 0.31, 0.25), 'plate', bevel=True)
    p.box((0, -0.15, 0.215), (0.30, 0.07, 0.05), 'plate2', rot=(-10, 0, 0), bevel=True)
    p.box((0, -0.13, 0.105), (0.20, 0.08, 0.15), 'plate2', bevel=True)
    p.cyl((0.12, 0.08, 0.27), 0.012, 0.012, 0.18, 'ink', seg=4)
    p.sphere((0.12, 0.08, 0.455), 0.022, 'red', seg=(6, 4))
    for s in (-1, 1):
        for z in (0.12, 0.165):
            p.box((s * 0.145, 0.04, z), (0.008, 0.12, 0.02), 'ink', deco=True)
    _slit(p)
    p.build('BOT_SOLDIER_HelmB')

    p = Part(pal)                                                                            # C: tall, cheek guards, mohawk
    neck(p)
    p.sphere((0, 0.01, 0.17), 0.15, 'plate', seg=(12, 7), scale=(1, 1.1, 1.18))
    p.box((0, -0.125, 0.09), (0.19, 0.09, 0.17), 'plate2', bevel=True)
    for s in (-1, 1):
        p.box((s * 0.115, -0.085, 0.07), (0.05, 0.13, 0.15), 'plate', rot=(0, 0, s * 8), bevel=True)
    for y, z in ((-0.07, 0.33), (0.02, 0.36), (0.11, 0.33)):
        p.box((0, y, z), (0.03, 0.08, 0.09), 'red')
    _slit(p)
    p.build('BOT_SOLDIER_HelmC')

    p = Part(pal)
    p.box((0, 0, 0), (0.15, 0.010, 0.018), 'light')
    p.build('BOT_SOLDIER_Visor', bevel=False, hull=0.004)

    # ---- arms (origin on the shoulder); the right one carries the rifle (barrel along -Y, the game's forward)
    def arm(p, hand, pole, la, lb):
        e = _elbow((0, 0, 0), hand, la, lb, pole)
        p.sphere((0, 0, 0), 0.085, 'suit2', seg=(6, 4))
        p.limb((0, 0, 0), e, 0.058, 0.052, 'suit')
        a, b = Vector((0, 0, 0)), Vector(e)
        p.limb(tuple(a + (b - a) * 0.22), tuple(a + (b - a) * 0.78), 0.071, 0.066, 'plate')
        p.sphere(e, 0.056, 'gunmetal', seg=(6, 4))
        h = Vector(hand)
        p.limb(e, tuple(Vector(e) + (h - Vector(e)) * 0.84), 0.066, 0.058, 'plate')
        p.box(hand, (0.075, 0.085, 0.075), 'plate2', bevel=True)
        return e

    p = Part(pal)
    arm(p, S_GRIP_R, (-0.6, 0.5, -1.0), 0.30, 0.27)
    x, z = S_RIFLE_X, S_RIFLE_Z
    p.box((x, -0.25, z), (0.07, 0.30, 0.11), 'gunmetal', bevel=True)                         # receiver
    p.box((x, -0.025, z - 0.015), (0.055, 0.17, 0.09), 'suit2', bevel=True)                  # stock
    p.box((x, -0.30, z - 0.11), (0.045, 0.07, 0.14), 'suit2', rot=(-8, 0, 0))               # magazine
    p.cyl((x, -0.40, z + 0.005), 0.04, 0.04, 0.22, 'plate2', seg=8, rot=(90, 0, 0))          # handguard
    p.cyl((x, -0.62, z + 0.005), 0.022, 0.022, 0.20, 'steel', seg=8, rot=(90, 0, 0))         # barrel
    p.cyl((x, -0.80, z + 0.005), 0.032, 0.032, 0.06, 'gunmetal', seg=8, rot=(90, 0, 0))      # muzzle brake
    p.box((x, -0.47, z - 0.075), (0.035, 0.04, 0.09), 'ink')                                  # foregrip
    p.box((x, -0.22, z + 0.075), (0.03, 0.09, 0.04), 'gunmetal')                              # sight
    p.box((x, -0.268, z + 0.075), (0.02, 0.008, 0.022), 'amber', deco=True)                  # sight lens
    p.box((x + 0.039, -0.25, z + 0.01), (0.008, 0.20, 0.022), 'amber', deco=True)            # receiver stripe
    p.cyl((x, -0.858, z + 0.005), 0.016, 0.016, 0.01, 'ink', seg=6, rot=(90, 0, 0), deco=True)   # bore
    ar = p.build('BOT_SOLDIER_ArmR', bevel=False)
    socket('BOT_SOLDIER_MUZZLE', ar, (x, -0.875, z + 0.005))

    p = Part(pal)
    arm(p, S_HAND_L, (0.5, 0.2, -1.0), 0.33, 0.32)
    p.box((S_HAND_L[0] + 0.0, S_HAND_L[1], S_HAND_L[2] + 0.042), (0.06, 0.07, 0.008), 'suit2', deco=True)   # knuckle plate
    al = p.build('BOT_SOLDIER_ArmL', bevel=False)
    socket('BOT_SOLDIER_HANDL', al, (S_HAND_L[0], S_HAND_L[1] - 0.02, S_HAND_L[2] + 0.07))

    # ---- grenade: gunmetal can, red band, amber fuse cap, ink spoon (origin = centre)
    p = Part(pal)
    p.cyl((0, 0, -0.05), 0.045, 0.045, 0.10, 'gunmetal', seg=8)
    p.cyl((0, 0, 0.05), 0.024, 0.024, 0.025, 'amber', seg=6)
    p.cyl((0, 0, -0.012), 0.049, 0.049, 0.026, 'red', seg=8, caps=False, deco=True)
    p.box((0.047, 0, 0.015), (0.008, 0.022, 0.06), 'ink', deco=True)
    p.build('BOT_SOLDIER_Nade', bevel=False, hull=0.008)


# ================================================================ BLADE BOT
# Squat violet hover saucer with hazard chevrons on the rim, a front sensor slit (Light), a gold gyro core dome on
# top and a hub on a short post. The Hub spins about the post: one arm ends in a clamp holding the weapon (+X), a
# short counter arm carries an amber weight. Weapons (origin = the clamp, along +X, edge leading on +Y as it spins):
#   Katana: ink-wrapped handle, round guard, brass collar, long curved steel blade with a pale temper line.
#   Axe (Voltaxe): steel shaft with grips, gunmetal head, battery, teal coils, wide blade with a glowing edge.
X_HUB = (0, 0, 0.84)
X_GRIP = (0.47, 0, 0)


def build_blader(pal):
    SEG = 12
    ph = math.radians(15)
    p = Part(pal)
    p.lathe([(0.0, 0.16), (0.24, 0.16), (0.34, 0.24), (0.49, 0.38), (0.49, 0.48), (0.42, 0.55), (0.28, 0.61),
             (0.17, 0.63), (0.0, 0.63)], 'violet', seg=SEG, phase=ph)
    p.sphere((0, 0, 0.62), 0.17, 'core', seg=(10, 5), scale=(1, 1, 0.68))
    p.cyl((0, 0, 0.70), 0.045, 0.045, 0.16, 'gunmetal', seg=8)                                # hub post
    # ---- deco: rim band, hazard chevrons, under-thruster glow, vents, core seat
    p.band(0.383, 0.40, 0.497, 'violet2', seg=SEG, phase=ph)
    p.band(0.46, 0.477, 0.497, 'violet2', seg=SEG, phase=ph)
    for k in range(SEG):
        if k % 2 == 0:
            p.on_slope(k, SEG, (0.34, 0.24), (0.49, 0.38), 0.55, 0.004, (0.07, 0.006, 0.08), 'amber', phase=ph)
    p.cyl((0, 0, 0.152), 0.18, 0.18, 0.008, 'teal', seg=10, deco=True)
    p.cyl((0, 0, 0.142), 0.08, 0.08, 0.008, 'paper', seg=8, deco=True)
    for k in (2, 5, 8, 11):
        p.on_slope(k, SEG, (0.42, 0.55), (0.28, 0.61), 0.5, 0.004, (0.05, 0.006, 0.05), 'ink', phase=ph)
    p.cyl((0, 0, 0.625), 0.18, 0.18, 0.02, 'gunmetal', seg=10, caps=False, deco=True)
    body = p.build('BOT_BLADER_Body')
    socket('BOT_BLADER_CORE', body, (0, 0, 0.67))
    socket('BOT_BLADER_HUB', body, X_HUB)
    socket('BOT_BLADER_LIGHT', body, (0, -0.48, 0.43))

    p = Part(pal)
    p.cyl((0, 0, -0.04), 0.12, 0.12, 0.08, 'steel', seg=10)
    p.box((0.27, 0, 0), (0.38, 0.06, 0.05), 'gunmetal')
    p.box((-0.20, 0, 0), (0.26, 0.06, 0.05), 'gunmetal')
    p.cyl((-0.34, 0, -0.05), 0.07, 0.07, 0.10, 'amber', seg=8)
    p.box((X_GRIP[0], 0, 0), (0.08, 0.09, 0.08), 'violet2', bevel=True)
    p.cyl((0, 0, 0.04), 0.06, 0.06, 0.008, 'amber', seg=8, deco=True)
    p.cyl((-0.34, 0, 0.05), 0.04, 0.04, 0.008, 'ink', seg=6, deco=True)
    hub = p.build('BOT_BLADER_Hub', bevel=False)
    socket('BOT_BLADER_GRIP', hub, X_GRIP)

    # katana (origin = clamp centre; the clamp hides the middle of the handle)
    p = Part(pal)
    p.cyl((-0.14, 0, 0), 0.022, 0.022, 0.26, 'ink', seg=8, rot=(0, 90, 0))
    for xb in (-0.10, -0.06, 0.06):
        p.cyl((xb, 0, 0), 0.026, 0.026, 0.012, 'paper', seg=8, rot=(0, 90, 0), caps=False, deco=True)
    p.cyl((-0.16, 0, 0), 0.027, 0.027, 0.022, 'steel', seg=8, rot=(0, 90, 0))
    p.cyl((0.12, 0, 0), 0.065, 0.065, 0.02, 'gunmetal', seg=12, rot=(0, 90, 0))
    p.box((0.155, 0.0, 0), (0.035, 0.05, 0.026), 'amber')
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.17 + 0.82 * t
        sori = -0.07 * t * t
        w = 0.068 - 0.014 * t
        st.append((x, -w / 2 + sori, w / 2 + sori, 0.009 - 0.002 * t))
    p.blade(st, (1.06, -0.07 - 0.005, 0.0), 'blade', 'paper')
    p.build('BOT_BLADER_Katana', bevel=False, hull=0.01)

    # electric axe
    p = Part(pal)
    p.cyl((-0.10, 0, 0), 0.024, 0.024, 0.90, 'steel', seg=8, rot=(0, 90, 0))
    p.cyl((-0.12, 0, 0), 0.03, 0.03, 0.03, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.cyl((0.08, 0, 0), 0.029, 0.029, 0.22, 'ink', seg=8, rot=(0, 90, 0), caps=False)
    p.box((0.70, 0.0, 0), (0.12, 0.085, 0.075), 'gunmetal', bevel=True)
    p.box((0.70, -0.065, 0), (0.08, 0.05, 0.055), 'teal')
    p.prism([(0.62, 0.02), (0.78, 0.02), (0.83, 0.13), (0.85, 0.25), (0.70, 0.29), (0.55, 0.25), (0.57, 0.13)], -0.014, 0.014, 'steel')
    p.prism([(0.55, 0.235), (0.70, 0.27), (0.85, 0.235), (0.855, 0.255), (0.70, 0.295), (0.545, 0.255)], -0.019, 0.019, 'lens')
    p.prism([(0.67, -0.06), (0.70, -0.17), (0.73, -0.06)], -0.01, 0.01, 'steel')
    for xc in (0.56, 0.60):
        p.cyl((xc, 0, 0), 0.036, 0.036, 0.014, 'teal', seg=8, rot=(0, 90, 0), caps=False, deco=True)
    p.build('BOT_BLADER_Axe', bevel=False, hull=0.01)

    p = Part(pal)
    p.box((0, 0, 0), (0.20, 0.02, 0.035), 'light')
    p.build('BOT_BLADER_Light', bevel=False, hull=0.006)


# ================================================================ CRAWLER, ADVANCED SKIN (levels 20+)
# Same silhouette, pivots and hit volumes as the tin-can Crawler (same hips, core, light): a faceted armoured shell
# with a sloped head ring and a wrap-around visor, belly and belt armour, panel lines and bolts. The armour is in the
# two KEY colours: 'plate' (about two thirds of the shell) and 'plate2' (the other third); the game paints them black
# and grey per crawler (ai.js keyMat2: 66 % grey / 33 % black or the other way round). Specks: white flecks and a
# stencil chevron drawn over some of them (its own part, so most crawlers draw none).
def build_crawler2(pal):
    SEG = 10
    p = Part(pal)
    p.cyl((0, 0, 0.30), 0.32, 0.31, 0.30, 'plate', seg=SEG, bevel=True)                  # lower shell
    p.cyl((0, 0, 0.60), 0.31, 0.25, 0.13, 'plate', seg=SEG, bevel=True)                  # sloped head ring
    p.cyl((0, 0, 0.73), 0.255, 0.255, 0.035, 'plate2', seg=SEG, bevel=True)              # head cap rim
    p.sphere((0, 0, 0.77), 0.14, 'core', seg=(8, 4), scale=(1, 1, 0.6))
    p.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=3)                           # whip antenna (light)
    p.cyl((0, 0, 0.255), 0.30, 0.32, 0.05, 'plate2', seg=SEG, bevel=True)                # belly armour skirt
    # deco: belt band (plate2), visor band + glowing strip, panel lines, side armour, bolts, core seat
    p.cyl((0, 0, 0.405), 0.33, 0.33, 0.07, 'plate2', seg=SEG, caps=False, deco=True)
    p.cyl((0, 0, 0.50), 0.317, 0.317, 0.012, 'ink', seg=SEG, caps=False, deco=True)         # panel line
    p.on_slope(7, SEG, (0.31, 0.60), (0.25, 0.73), 0.45, 0.004, (0.30, 0.012, 0.075), 'ink')      # visor slot
    for k in (6, 8):
        p.on_slope(k, SEG, (0.31, 0.60), (0.25, 0.73), 0.45, 0.004, (0.16, 0.012, 0.05), 'ink')
    p.on_slope(7, SEG, (0.31, 0.60), (0.25, 0.73), 0.45, 0.017, (0.22, 0.008, 0.028), 'lens')    # visor strip
    for k in (6, 8):
        p.on_slope(k, SEG, (0.31, 0.60), (0.25, 0.73), 0.45, 0.017, (0.10, 0.008, 0.022), 'lens')
    for k in (2, 4, 0, 9, 5):
        p.on_facet(k, SEG, 0.335, 0.002, 0.405, (0.12, 0.05, 0.11), 'plate2')             # side armour on the belt
    for k in range(SEG):
        if k % 2:
            p.on_facet(k, SEG, 0.31, 0.003, 0.55, (0.012, 0.008, 0.08), 'ink')           # vertical panel lines
    for k in (1, 3, 7):
        p.on_facet(k, SEG, 0.31, 0.003, 0.335, (0.028, 0.008, 0.028), 'gunmetal')       # bolts
    p.cyl((-0.15, 0.09, 0.755), 0.014, 0.014, 0.13, 'ink', seg=4, deco=True)            # stub antenna
    p.box((-0.15, 0.09, 0.895), (0.04, 0.04, 0.03), 'plate2', deco=True)
    p.cyl((0, 0, 0.765), 0.152, 0.152, 0.02, 'gunmetal', seg=10, caps=False, deco=True)
    p.build('BOT_CRAWLER_Body2')
    # legs: armoured thigh guard and a wide plated foot, same pivot and length
    p = Part(pal)
    p.box((0, 0, -0.02), (0.11, 0.08, 0.07), 'plate2', bevel=True)
    for i in range(2):
        p.box(((0.03 if i % 2 else -0.03), 0, -0.10 - i * 0.075), (0.11, 0.055, 0.035), 'gunmetal', deco=True)
    p.box((0, 0, -0.17), (0.034, 0.034, 0.30), 'plate')
    p.box((0, -0.022, -0.25), (0.044, 0.01, 0.09), 'plate2', deco=True)
    p.cyl((0, 0, -0.355), 0.095, 0.07, 0.05, 'plate2', seg=6)
    p.build('BOT_CRAWLER_Leg2', bevel=False, hull=0.01)
    # specks: white flecks and a stencil chevron, 4 mm proud of the shell (drawn over Body2, no outline)
    p = Part(pal)
    # flecks on the shell (facet k, height z, angle off the facet centre, size); white chips on the belt armour;
    # a stencil chevron on the head ring
    rnd = [(0, 0.47, 0.05, 0.03), (1, 0.535, 0.1, 0.022), (2, 0.57, -0.06, 0.036), (3, 0.475, -0.1, 0.02),
           (4, 0.555, 0.04, 0.03), (5, 0.535, -0.1, 0.026), (6, 0.565, 0.08, 0.022), (8, 0.53, -0.05, 0.034),
           (9, 0.47, 0.1, 0.026), (0, 0.575, -0.07, 0.018), (4, 0.47, -0.08, 0.028), (2, 0.53, 0.07, 0.02),
           (6, 0.48, -0.06, 0.028), (8, 0.575, 0.07, 0.018), (1, 0.475, -0.08, 0.024), (9, 0.56, -0.06, 0.03)]
    for k, z, d, sz in rnd:
        p.on_facet(k, SEG, 0.312, 0.006, z, (sz * 1.6, 0.006, sz * 1.25), 'paper', phase=d, deco=False)
    for k, z, w in ((2, 0.39, 0.05), (4, 0.42, 0.035), (9, 0.395, 0.04), (5, 0.385, 0.03)):
        p.on_facet(k, SEG, 0.335, 0.056, z, (w, 0.006, w * 0.7), 'paper', deco=False)    # on the belt armour
    for k in (3, 4):
        p.on_slope(k, SEG, (0.31, 0.60), (0.25, 0.73), 0.3, 0.004, (0.10, 0.006, 0.03), 'paper', deco=False)
    strip_hull(p.build('BOT_CRAWLER_Specks', bevel=False, hull=0.001))


# ================================================================ HAWK (levels 20+)
# Advanced aerial robot: a sleek octagonal armoured fuselage (nose = -Y), a dorsal armour spine with panel lines,
# stub pylons carrying two ducted fans (Fan: duct + stator, vectored by the game; Rotor: the blades), a vectored tail
# thruster, a ball chin turret with twin barrels (Gun) and a sensor eye in the nose (Light). Accent strips, the duct
# rims, the thruster ring and the turret band are in the KEY colours: the game paints them in its round type's colour
# (normal: steel white, shock: blue, acid: green, explosive: orange). Gold core under the tail (weak point).
H_CEN = 0.30
H_FAN = (0.47, 0.02, 0.32)
H_PIVOT = (0, -0.20, 0.135)


def build_hawk(pal):
    SEG = 8
    ph = math.pi / SEG
    p = Part(pal)
    # fuselage: lathe along the length (lathe z -> -Y), flattened to 72 % of its width
    p.parent = Matrix.Translation((0, 0, H_CEN)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Diagonal(Vector((1, 0.72, 1, 1)))
    prof = [(0.0, -0.46), (0.08, -0.45), (0.15, -0.36), (0.20, -0.18), (0.21, 0.02), (0.19, 0.20), (0.14, 0.36), (0.07, 0.47), (0.0, 0.52)]
    p.lathe(prof, 'hawk', seg=SEG, phase=ph)
    p.parent = Matrix.Identity(4)
    top = H_CEN + 0.21 * 0.72 * math.cos(ph)                                                 # flat top face height
    p.box((0, 0.04, top + 0.022), (0.15, 0.52, 0.045), 'hawk2', bevel=True)                    # dorsal armour spine
    for sx in (-1, 1):                                                                         # V-tail fins
        p.parent = Matrix.Translation((sx * 0.045, 0, top + 0.03)) @ Matrix.Rotation(math.radians(-30 * sx), 4, 'Y') @ _YZX
        p.prism([(0.20, 0.0), (0.40, 0.0), (0.46, 0.16), (0.37, 0.16)], -0.011, 0.011, 'hawk2')
    p.parent = Matrix.Identity(4)
    for sx in (-1, 1):                                                                         # stub pylons to the fans
        p.box((sx * 0.235, H_FAN[1], H_FAN[2]), (0.13, 0.15, 0.04), 'hawk2', bevel=True)
        p.box((sx * 0.19, -0.01, H_CEN - 0.03), (0.06, 0.26, 0.11), 'hawk', bevel=True)      # intake cheeks
        p.box((sx * 0.222, -0.13, H_CEN - 0.03), (0.012, 0.05, 0.07), 'ink')                 # intake mouth
    p.cyl((0, 0.40, H_CEN), 0.085, 0.07, 0.14, 'gunmetal', seg=10, rot=(-90, 0, 0))         # tail thruster
    p.cyl((0, 0.535, H_CEN), 0.06, 0.06, 0.012, 'plate', seg=10, rot=(-90, 0, 0))           # thruster glow
    p.sphere((0, 0.17, H_CEN - 0.13), 0.075, 'core', seg=(10, 5), scale=(1, 1.2, 0.6))       # core (belly)
    p.box((0, H_PIVOT[1] + 0.01, H_PIVOT[2] + 0.04), (0.08, 0.10, 0.05), 'gunmetal')         # turret mount
    # deco: accent strips along the flanks, panel lines on the spine, thruster ring, vents
    for sx in (-1, 1):
        p.box((sx * 0.224, 0.03, H_CEN - 0.03), (0.008, 0.15, 0.02), 'plate', deco=True)       # accent strips on the cheeks
        p.box((sx * 0.072, -0.08, top + 0.0475), (0.012, 0.30, 0.006), 'plate', deco=True)     # accent strips along the spine
    for y in (-0.12, 0.08, 0.22):
        p.box((0, y, top + 0.0475), (0.12, 0.008, 0.006), 'ink', deco=True)
    p.box((0, -0.04, top + 0.0475), (0.03, 0.10, 0.006), 'hawk3', deco=True)
    p.cyl((0, 0.47, H_CEN), 0.084, 0.084, 0.03, 'plate2', seg=10, rot=(-90, 0, 0), caps=False, deco=True)
    body = p.build('BOT_HAWK_Body')
    socket('BOT_HAWK_CORE', body, (0, 0.17, H_CEN - 0.15))
    for i, sx in enumerate((-1, 1)):
        socket('BOT_HAWK_FAN%d' % i, body, (sx * H_FAN[0], H_FAN[1], H_FAN[2]))
    socket('BOT_HAWK_GUNPIVOT', body, H_PIVOT)
    socket('BOT_HAWK_LIGHT', body, (0, -0.385, H_CEN + 0.07))

    # ducted fan (origin = duct centre): a closed duct section turned about Z, stator cross and hub, accent rim
    p = Part(pal)
    duct = [(0.15, -0.045), (0.185, -0.05), (0.205, -0.01), (0.20, 0.045), (0.17, 0.062), (0.15, 0.05), (0.15, -0.045)]
    p.lathe(duct, 'hawk2', seg=12)
    p.beam((-0.155, 0, -0.035), (0.155, 0, -0.035), 0.02, 'gunmetal')
    p.beam((0, -0.155, -0.03), (0, 0.155, -0.03), 0.02, 'gunmetal')
    p.cyl((0, 0, -0.05), 0.04, 0.03, 0.05, 'hawk', seg=8)
    p.lathe([(0.206, 0.0), (0.206, 0.024)], 'plate', seg=12, deco=True)
    p.cyl((0, 0, -0.056), 0.03, 0.03, 0.008, 'plate2', seg=8, deco=True)
    p.build('BOT_HAWK_Fan', bevel=False, hull=0.01)
    # rotor: three blades
    p = Part(pal)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.box((math.cos(a) * 0.075, math.sin(a) * 0.075, 0.0), (0.12, 0.034, 0.008), 'gunmetal', rot=(18, 0, math.degrees(a)))
    p.cyl((0, 0, -0.012), 0.026, 0.026, 0.024, 'hawk3', seg=8)
    p.build('BOT_HAWK_Rotor', bevel=False, hull=0.006)
    # chin turret (origin = pivot, barrels along -Y)
    p = Part(pal)
    p.sphere((0, 0, 0), 0.065, 'hawk', seg=(10, 6))
    for sx in (-1, 1):
        p.cyl((sx * 0.025, -0.03, -0.005), 0.016, 0.016, 0.16, 'gunmetal', seg=6, rot=(90, 0, 0))
        p.cyl((sx * 0.025, -0.18, -0.005), 0.021, 0.021, 0.03, 'ink', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.035, 0), 0.0675, 0.0675, 0.02, 'plate', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    gun = p.build('BOT_HAWK_Gun', bevel=False)
    socket('BOT_HAWK_GUN', gun, (0, -0.21, -0.005))
    # sensor eye (coloured by the game)
    p = Part(pal)
    p.box((0, 0, 0), (0.17, 0.07, 0.05), 'light', rot=(-28, 0, 0))
    p.build('BOT_HAWK_Light', bevel=False, hull=0.006)


# ================================================================ BLADE BOT: KUSARIGAMA (third weapon)
# The hub's clamp holds the iron weight (Fundo, along +X like the other weapons; socket BOT_BLADER_CHAIN where the chain
# leaves it). The chain is drawn by the game as a run of Chain segments (two interlocking links, 0.2 m along game +Z,
# stretched to fit) out to the sickle (Kusari: origin = its chain ring, the handle runs out along game +Z, the curved
# kama blade at the far end with its edge turned back toward the chain).
def _torus(p, R, rr, color, seg=8, rs=4, deco=False):
    prof = [(R + rr * math.cos(2 * math.pi * k / rs), rr * math.sin(2 * math.pi * k / rs)) for k in range(rs + 1)]
    p.lathe(prof, color, seg=seg, deco=deco)


def build_kusari(pal):
    # weight in the clamp: grip through the clamp, an octagonal iron weight with an amber band, the chain ring
    p = Part(pal)
    p.cyl((-0.08, 0, 0), 0.021, 0.021, 0.19, 'ink', seg=8, rot=(0, 90, 0))
    p.cyl((0.105, 0, 0), 0.046, 0.046, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.cyl((0.205, 0, 0), 0.03, 0.018, 0.02, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.cyl((0.14, 0, 0), 0.05, 0.05, 0.02, 'amber', seg=8, rot=(0, 90, 0), caps=False, deco=True)
    p.parent = Matrix.Translation((0.238, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, 'X')
    _torus(p, 0.016, 0.006, 'chain', seg=6)
    p.parent = Matrix.Identity(4)
    fundo = p.build('BOT_BLADER_Fundo', bevel=False, hull=0.008)
    socket('BOT_BLADER_CHAIN', fundo, (0.25, 0, 0))

    # chain segment: two interlocking oval links, 0.2 m along Blender -Y (game +Z)
    p = Part(pal)
    p.parent = Matrix.Translation((0, -0.05, 0)) @ Matrix.Diagonal(Vector((1, 1.7, 1, 1)))
    _torus(p, 0.03, 0.009, 'chain', seg=6)
    p.parent = Matrix.Translation((0, -0.15, 0)) @ Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Diagonal(Vector((1, 1.7, 1, 1)))
    _torus(p, 0.03, 0.009, 'chain', seg=6)
    p.parent = Matrix.Identity(4)
    p.build('BOT_BLADER_Chain', bevel=False, hull=0.005)

    # sickle: ring, wrapped wooden handle out along -Y, steel ferrule, curved kama blade along +X (edge toward +Y)
    p = Part(pal)
    K = Matrix.Diagonal(Vector((1.4, 1.4, 1.4, 1)))          # drawn 40 % up so it reads at fighting range
    p.parent = K @ Matrix.Rotation(math.radians(90), 4, 'Y')
    _torus(p, 0.018, 0.006, 'chain', seg=6)
    p.parent = K
    p.cyl((0, -0.022, 0), 0.016, 0.02, 0.025, 'gunmetal', seg=8, rot=(90, 0, 0))
    p.cyl((0, -0.045, 0), 0.021, 0.024, 0.33, 'kwood', seg=8, rot=(90, 0, 0))
    for y in (-0.09, -0.15, -0.21, -0.27):
        p.cyl((0, y, 0), 0.026, 0.026, 0.018, 'ink', seg=8, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, -0.37, 0), 0.03, 0.03, 0.05, 'steel', seg=8, rot=(90, 0, 0))
    p.parent = K @ Matrix.Translation((0, -0.395, 0))
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.012 + 0.31 * t
        curve = 0.13 * t * t
        w = 0.074 - 0.04 * t
        st.append((x, -w / 2 + curve, w / 2 + curve, 0.008 - 0.003 * t))
    p.blade(st, (0.37, 0.19, 0.0), 'blade', 'paper')
    p.parent = K
    p.box((-0.03, -0.395, 0), (0.05, 0.044, 0.03), 'steel')                                 # spine knob behind the blade
    p.build('BOT_BLADER_Kusari', bevel=False, hull=0.009)


# ================================================================ JET TROOPER (levels 35+)
# A tall bipedal combat robot on a jet back unit, built from layered angular plates in near-black armour (the black-ops
# soldiers' colours): segmented abdomen, layered chest and pauldrons, thigh / shin / knee plates, forearm guards, panel
# lines and bolts. A sensor-slit helmet (no face, no eyes: one glowing slit). A bullet launcher fixed to the right hand,
# held low (receiver, rail, magazine, vented barrel shroud, twin barrels with a muzzle brake). On the back unit two
# glowing thruster nozzles and two telescoping arms (PodArm) that raise a box rocket pod each (Pod): the pod's lid (Lid)
# flips open on the top front edge to show three tubes with rocket tips inside. Element accents are in the KEY colours
# 'plate' / 'plate2' (painted per robot by the game: electric blue, acid green, explosive orange): the shoulder line, hex
# panels, cannon tips, tube rims, the lids' inner faces, nozzle rings; the glowing seams (Seam: abdomen gaps, sternum,
# nozzle cores) and the sensor slit (Light) are drawn in the light material. Parts are posed like the Soldier's rigid
# parts (origins on their joints); sockets give the joints, the pod arms, the nozzles, the muzzle and the tube mouths.
J_HIP = 1.02            # hip joint height
J_HIPX = 0.13
J_THIGH = 0.48          # hip -> knee; knee -> sole 0.54
J_WAIST = 1.10
J_SHOULDER = (0.33, 0.02, 0.47)    # torso local (left = +x; the right arm is -x)
J_NECK = (0, 0.0, 0.60)
J_ARM = (0.135, 0.29, 0.50)        # pod arm hinge on top of the back unit (torso space), left one +x
J_ARM_LEN = 0.27                   # hinge -> pod pivot, fully raised
J_NOZ = (0.105, 0.32, 0.03)        # nozzle exits in torso space
J_HAND_R = (-0.03, -0.24, -0.46)   # right hand in right-shoulder space (gun held low, pointing forward)
J_HAND_L = (0.05, -0.12, -0.54)


def _hexp(p, centre, nrm, r, t, color, rot=0.0):
    """a flat hexagonal accent panel (deco, t thick) standing 3 mm proud of a surface facing nrm ('-y', '+x', ...)"""
    c = Vector(centre)
    R = {'-y': Matrix.Rotation(math.radians(90), 4, 'X'), '+y': Matrix.Rotation(math.radians(-90), 4, 'X'),
         '+x': Matrix.Rotation(math.radians(90), 4, 'Y'), '-x': Matrix.Rotation(math.radians(-90), 4, 'Y'),
         '+z': Matrix.Identity(4)}[nrm]
    old = p.parent
    p.parent = old @ Matrix.Translation(c) @ R @ Matrix.Rotation(rot, 4, 'Z')
    poly = [(r * math.cos(math.pi / 6 + k * math.pi / 3), r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    p.prism(poly, 0.003, 0.003 + t, color, deco=True)
    p.parent = old


def _jframe(a, b, out):
    """a frame at a: local Z runs to b, local Y leans toward `out` (the outer side of a limb)"""
    a, b, out = Vector(a), Vector(b), Vector(out)
    z = (b - a).normalized()
    y = (out - z * out.dot(z)).normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = a
    return M


def _bolt(p, loc, axis, r=0.009):
    """a small bolt head (deco) whose base sits at loc on a face pointing along axis ('+x', '-x', '-y', '+y', '+z')"""
    rot = {'+x': (0, 90, 0), '-x': (0, -90, 0), '-y': (90, 0, 0), '+y': (-90, 0, 0), '+z': (0, 0, 0)}[axis]
    p.cyl(loc, r, r * 0.8, 0.008, 'gunmetal', seg=6, rot=rot, deco=True)


def _jet_arm(p, hand, pole, la, lb, side):
    """shoulder ball, upper arm with a layered outer plate, elbow, forearm with a layered guard and a wrist ring"""
    e = Vector(_elbow((0, 0, 0), hand, la, lb, pole))
    h = Vector(hand)
    out = Vector((side, 0.0, 0.0))
    p.sphere((0, 0, 0), 0.088, 'gunmetal', seg=(8, 5))
    p.limb((0, 0, 0), tuple(e), 0.058, 0.052, 'jet3')
    L1, L2 = e.length, (h - e).length
    p.parent = _jframe((0, 0, 0), e, out)
    p.box((0, 0.025, L1 * 0.47), (0.13, 0.08, L1 * 0.6), 'jet', bevel=True)
    p.box((0, 0.069, L1 * 0.42), (0.09, 0.02, L1 * 0.38), 'jet2')
    p.box((0, 0.0825, L1 * 0.42), (0.045, 0.008, L1 * 0.22), 'plate', deco=True)
    p.parent = Matrix.Identity(4)
    p.sphere(tuple(e), 0.06, 'gunmetal', seg=(8, 5))
    p.limb(tuple(e), tuple(e + (h - e) * 0.9), 0.05, 0.046, 'jet3')
    p.parent = _jframe(e, h, out)
    p.box((0, 0.03, L2 * 0.5), (0.135, 0.08, L2 * 0.66), 'jet', bevel=True)                      # forearm guard
    p.box((0, 0.075, L2 * 0.46), (0.095, 0.02, L2 * 0.44), 'jet2')
    p.box((0, 0.0885, L2 * 0.46), (0.022, 0.008, L2 * 0.34), 'plate', deco=True)
    p.box((0, -0.0135, L2 * 0.32), (0.10, 0.008, 0.012), 'ink', deco=True)                      # panel line
    p.cyl((0, 0, L2 * 0.86), 0.06, 0.06, 0.04, 'gunmetal', seg=8)                                  # wrist ring
    p.parent = Matrix.Identity(4)
    return e


def build_jet(pal):
    # ---- hips: pelvis core, bolted belt, layered codpiece, two-layer tassets, rear plate
    p = Part(pal)
    p.box((0, 0, J_HIP + 0.01), (0.30, 0.22, 0.16), 'jet3')
    p.box((0, 0, J_HIP + 0.09), (0.34, 0.25, 0.05), 'jet2', bevel=True)
    for x in (-0.12, -0.04, 0.04, 0.12):
        _bolt(p, (x, -0.122, J_HIP + 0.09), '-y', 0.011)
    sprism(p, [(-0.14, 0.93), (-0.13, 1.08), (-0.02, 1.08), (-0.05, 0.90)], -0.085, 0.085, 'jet', bevel=True)
    sprism(p, [(-0.165, 0.96), (-0.155, 1.05), (-0.12, 1.05), (-0.13, 0.95)], -0.05, 0.05, 'jet2')
    p.box((0, -0.166, 1.0), (0.04, 0.008, 0.04), 'plate', deco=True)
    for s in (-1, 1):
        p.box((s * 0.19, -0.016, J_HIP - 0.03), (0.07, 0.22, 0.20), 'jet', rot=(0, s * 14, 0), bevel=True)
        p.box((s * 0.228, -0.02, J_HIP - 0.07), (0.035, 0.17, 0.13), 'jet2', rot=(0, s * 20, 0))
    p.box((0, 0.125, J_HIP - 0.02), (0.24, 0.04, 0.16), 'jet', bevel=True)
    p.box((0, 0.1485, J_HIP - 0.02), (0.18, 0.008, 0.012), 'ink', deco=True)
    hips = p.build('BOT_JET_Hips', bevel=False)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_JET_HIP%d' % i, hips, (sx * J_HIPX, 0, J_HIP))
    socket('BOT_JET_WAIST', hips, (0, 0, J_WAIST))

    # ---- thigh (origin on the hip joint): servo ball, strut, layered front plate, side plates with hex + bolts
    p = Part(pal)
    p.sphere((0, 0, 0), 0.085, 'gunmetal', seg=(10, 6))
    p.limb((0, 0, -0.02), (0, 0, -J_THIGH + 0.02), 0.066, 0.056, 'jet3')
    sprism(p, [(-0.135, -0.06), (-0.115, -0.37), (-0.05, -0.41), (-0.02, -0.36), (-0.03, -0.08)], -0.07, 0.07, 'jet', bevel=True)
    sprism(p, [(-0.155, -0.10), (-0.14, -0.26), (-0.11, -0.27), (-0.12, -0.10)], -0.045, 0.045, 'jet2')
    p.box((0, 0.065, -0.22), (0.10, 0.05, 0.26), 'jet2')
    p.cyl((-0.05, 0, -0.44), 0.045, 0.045, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.box((0, -0.131, -0.32), (0.12, 0.008, 0.008), 'ink', deco=True)
    for s in (-1, 1):
        p.box((s * 0.079, -0.02, -0.22), (0.022, 0.16, 0.26), 'jet2', bevel=True)
        _hexp(p, (s * 0.09, -0.02, -0.17), '+x' if s > 0 else '-x', 0.028, 0.005, 'plate')
        _bolt(p, (s * 0.087, -0.08, -0.31), '+x' if s > 0 else '-x')
        _bolt(p, (s * 0.087, 0.04, -0.31), '+x' if s > 0 else '-x')
    p.build('BOT_JET_Thigh', bevel=False)

    # ---- shin + foot (origin on the knee): layered knee cap, shin guard, side plates, calf piston, armoured boot
    p = Part(pal)
    p.sphere((0, 0, 0), 0.07, 'gunmetal', seg=(10, 6))
    sprism(p, [(-0.115, 0.07), (-0.13, -0.07), (-0.075, -0.13), (-0.01, -0.06), (-0.01, 0.07)], -0.075, 0.075, 'jet', bevel=True)
    sprism(p, [(-0.14, 0.03), (-0.145, -0.05), (-0.11, -0.08), (-0.10, 0.03)], -0.045, 0.045, 'jet2')
    p.box((0, -0.147, -0.01), (0.04, 0.008, 0.04), 'plate', deco=True)
    p.limb((0, 0, -0.05), (0, 0, -0.43), 0.056, 0.048, 'jet3')
    p.box((0, 0.07, -0.13), (0.08, 0.06, 0.10), 'jet2')
    p.limb((0, 0.06, -0.18), (0, 0.05, -0.40), 0.018, 0.018, 'steel', seg=6)                      # calf piston
    sprism(p, [(-0.09, -0.13), (-0.075, -0.41), (0.0, -0.43), (0.0, -0.14)], -0.068, 0.068, 'jet', bevel=True)
    p.box((0, -0.088, -0.20), (0.11, 0.008, 0.008), 'ink', deco=True)
    p.box((0, -0.0825, -0.335), (0.11, 0.008, 0.008), 'ink', deco=True)
    p.box((0, -0.0855, -0.27), (0.03, 0.008, 0.09), 'plate2', deco=True)
    for s in (-1, 1):
        p.box((s * 0.079, -0.01, -0.27), (0.022, 0.13, 0.22), 'jet2')
        _bolt(p, (s * 0.087, -0.05, -0.18), '+x' if s > 0 else '-x')
        _hexp(p, (s * 0.09, 0.0, -0.32), '+x' if s > 0 else '-x', 0.024, 0.005, 'plate')
    p.sphere((0, 0, -0.46), 0.05, 'gunmetal', seg=(8, 5))
    sprism(p, [(-0.21, -0.54), (-0.18, -0.46), (-0.05, -0.44), (0.10, -0.47), (0.12, -0.54)], -0.08, 0.08, 'jet2', bevel=True)
    sprism(p, [(-0.225, -0.53), (-0.20, -0.475), (-0.12, -0.465), (-0.11, -0.53)], -0.065, 0.065, 'jet')
    p.box((0, 0.11, -0.50), (0.10, 0.05, 0.07), 'gunmetal')
    p.box((0, -0.045, -0.545), (0.15, 0.31, 0.008), 'ink', deco=True)
    p.build('BOT_JET_Shin', bevel=False)

    # ---- torso (origin on the waist): segmented abdomen, a broad chest with layered pecs and a sternum plate, the gold
    # reactor (weak point), layered pauldrons with the shoulder line, the jet back unit (tanks, vents, nozzles, arm hinges)
    sx_, sy_, sz_ = J_SHOULDER
    p = Part(pal)
    p.cyl((0, 0, -0.06), 0.13, 0.15, 0.26, 'jet3', seg=8)
    for i, z in enumerate((0.0, 0.065, 0.13)):
        p.box((0, -0.115, z), (0.22 - 0.012 * i, 0.06, 0.05), 'jet2')                 # abdomen segments
    sprism(p, [(-0.17, 0.16), (-0.19, 0.44), (-0.09, 0.56), (0.15, 0.56), (0.16, 0.18)], -0.235, 0.235, 'jet', bevel=True)
    for s in (-1, 1):
        sprism(p, [(-0.205, 0.29), (-0.215, 0.46), (-0.15, 0.52), (-0.12, 0.42), (-0.15, 0.28)], s * 0.025, s * 0.20, 'jet2')
        _bolt(p, (s * 0.17, -0.2105, 0.42), '-y')
    sprism(p, [(-0.193, 0.20), (-0.20, 0.30), (-0.15, 0.31), (-0.15, 0.19)], -0.07, 0.07, 'jet3')
    p.cyl((0, -0.196, 0.255), 0.05, 0.05, 0.03, 'core', seg=10, rot=(90, 0, 0))
    p.cyl((0, -0.192, 0.255), 0.064, 0.064, 0.022, 'gunmetal', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, 0, 0.52), 0.11, 0.10, 0.08, 'jet3', seg=8)                                          # collar
    p.cyl((0, 0, 0.555), 0.115, 0.115, 0.016, 'gunmetal', seg=8, caps=False, deco=True)
    p.box((0, -0.176, 0.185), (0.30, 0.008, 0.012), 'ink', deco=True)
    for s in (-1, 1):
        _hexp(p, (s * 0.165, -0.178, 0.235), '-y', 0.03, 0.006, 'plate')
        # pauldron: main block, top layer with the shoulder line, a lower lip, bolts, a hex on the front
        p.parent = Matrix.Translation((s * sx_, sy_, sz_)) @ Matrix.Rotation(math.radians(-s * 12), 4, 'Y')
        p.box((0, 0, 0.05), (0.22, 0.28, 0.15), 'jet')
        p.box((0, 0, 0.135), (0.18, 0.24, 0.03), 'jet2')
        p.box((s * 0.02, 0, -0.045), (0.20, 0.26, 0.05), 'jet2')
        p.box((0, 0, 0.1535), (0.15, 0.22, 0.008), 'plate', deco=True)                           # shoulder line
        p.box((s * 0.1135, 0.0, 0.06), (0.008, 0.24, 0.025), 'plate', deco=True)
        for y in (-0.09, 0.09):
            _bolt(p, (s * 0.107, y, 0.0), '+x' if s > 0 else '-x')
        _hexp(p, (0, -0.14, 0.05), '-y', 0.034, 0.006, 'plate2')
        p.parent = Matrix.Identity(4)
    # back unit
    p.box((0, 0.25, 0.31), (0.40, 0.16, 0.38), 'jet2')
    p.box((0, 0.335, 0.30), (0.30, 0.03, 0.26), 'jet3')
    for z in (0.22, 0.255, 0.29, 0.325):
        p.box((0, 0.3535, z), (0.22, 0.008, 0.012), 'ink', deco=True)                               # vent slats
    p.box((0, 0.3535, 0.40), (0.20, 0.008, 0.02), 'plate', deco=True)
    for s in (-1, 1):
        p.cyl((s * 0.215, 0.25, 0.16), 0.045, 0.045, 0.30, 'jet3', seg=8)                          # side tanks
        p.cyl((s * 0.215, 0.25, 0.30), 0.05, 0.05, 0.02, 'plate2', seg=8, caps=False, deco=True)
        nx, ny, nz = J_NOZ
        p.cyl((s * nx, ny, nz + 0.05), 0.05, 0.065, 0.14, 'gunmetal', seg=10)                      # nozzle
        p.cyl((s * nx, ny, nz), 0.06, 0.052, 0.06, 'jet3', seg=10)                                  # bell
        p.cyl((s * nx, ny, nz + 0.11), 0.07, 0.07, 0.03, 'plate', seg=10, caps=False, deco=True)  # nozzle ring
        ax, ay, az = J_ARM
        p.box((s * ax, 0.25, az), (0.14, 0.13, 0.008), 'ink', deco=True)                           # arm slot
        p.box((s * ax, ay - 0.006, az + 0.012), (0.09, 0.05, 0.02), 'gunmetal')                           # hinge block
    torso = p.build('BOT_JET_Torso', bevel=True)
    socket('BOT_JET_CORE', torso, (0, -0.215, 0.255))
    socket('BOT_JET_NECK', torso, J_NECK)
    socket('BOT_JET_SHOULDER0', torso, (-sx_, sy_, sz_))
    socket('BOT_JET_SHOULDER1', torso, (sx_, sy_, sz_))
    for i, s in enumerate((-1, 1)):
        socket('BOT_JET_ARM%d' % i, torso, (s * J_ARM[0], J_ARM[1], J_ARM[2] + 0.02))
        socket('BOT_JET_NOZ%d' % i, torso, (s * J_NOZ[0], J_NOZ[1], J_NOZ[2] - 0.01))

    # ---- glowing seams (light material, element colour; origin on the waist like the torso)
    p = Part(pal)
    for z in (0.0325, 0.0975):
        p.box((0, -0.138, z), (0.17, 0.01, 0.008), 'light')
    p.box((0, -0.19, 0.405), (0.014, 0.012, 0.12), 'light')
    for s in (-1, 1):
        nx, ny, nz = J_NOZ
        p.cyl((s * nx, ny, nz - 0.006), 0.042, 0.042, 0.004, 'light', seg=10)                      # nozzle cores
    strip_hull(p.build('BOT_JET_Seam', bevel=False, hull=0.003))

    # ---- head (origin on the neck): a sensor-slit helmet, no face: helmet shell, crest, faceplate with one slit,
    # ear modules, chin guard, antenna, panel lines
    p = Part(pal)
    p.cyl((0, 0, -0.05), 0.065, 0.07, 0.10, 'jet3', seg=8)
    p.cyl((0, 0, -0.02), 0.076, 0.076, 0.02, 'gunmetal', seg=8, caps=False, deco=True)
    sprism(p, [(-0.15, 0.04), (-0.135, 0.20), (-0.05, 0.26), (0.10, 0.25), (0.14, 0.16), (0.12, 0.03)], -0.115, 0.115, 'jet', bevel=True)
    sprism(p, [(-0.10, 0.24), (-0.04, 0.285), (0.11, 0.27), (0.12, 0.22)], -0.025, 0.025, 'jet2')
    sprism(p, [(-0.165, 0.06), (-0.155, 0.16), (-0.12, 0.17), (-0.13, 0.05)], -0.09, 0.09, 'jet2', bevel=True)
    sprism(p, [(-0.14, 0.02), (-0.13, 0.07), (-0.06, 0.07), (-0.07, 0.0)], -0.075, 0.075, 'jet3')
    p.box((0, -0.162, 0.125), (0.15, 0.008, 0.022), 'ink', deco=True)                               # the sensor slit
    for s in (-1, 1):
        p.cyl((s * 0.112, -0.01, 0.12), 0.045, 0.045, 0.033, 'gunmetal', seg=8, rot=(0, s * 90, 0))   # ear modules
        p.cyl((s * 0.142, -0.01, 0.12), 0.03, 0.03, 0.008, 'plate', seg=8, rot=(0, s * 90, 0), deco=True)
        p.box((s * 0.1185, 0.03, 0.205), (0.008, 0.16, 0.008), 'ink', deco=True)
    p.cyl((0.075, 0.09, 0.2), 0.008, 0.008, 0.15, 'ink', seg=4)
    p.sphere((0.075, 0.09, 0.355), 0.013, 'plate', seg=(6, 4))
    head = p.build('BOT_JET_Head', bevel=True)
    socket('BOT_JET_SLIT', head, (0, -0.168, 0.125))
    p = Part(pal)
    p.box((0, 0, 0), (0.13, 0.006, 0.012), 'light')
    p.build('BOT_JET_Light', bevel=False, hull=0.004)

    # ---- arms (origin on the shoulder); the right one carries the bullet launcher, held low, barrels along -Y
    p = Part(pal)
    _jet_arm(p, J_HAND_R, (0.2, 1.0, -0.3), 0.30, 0.32, -1)
    hx, hy, hz = J_HAND_R
    p.box((hx, hy, hz), (0.09, 0.09, 0.09), 'jet2', bevel=True)                                   # fist
    p.box((hx, hy - 0.10, hz + 0.065), (0.10, 0.40, 0.11), 'gunmetal', bevel=True)               # receiver
    p.box((hx, hy - 0.10, hz + 0.126), (0.04, 0.30, 0.012), 'jet3')                               # top rail
    for k in range(5):
        p.box((hx, hy - 0.22 + 0.06 * k, hz + 0.1355), (0.05, 0.012, 0.008), 'ink', deco=True)
    p.box((hx, hy - 0.17, hz - 0.055), (0.06, 0.09, 0.15), 'jet2', rot=(-12, 0, 0))             # magazine
    p.box((hx + 0.0335, hy - 0.17, hz - 0.06), (0.008, 0.05, 0.09), 'plate', rot=(-12, 0, 0), deco=True)
    p.box((hx, hy - 0.40, hz + 0.07), (0.09, 0.22, 0.09), 'jet', bevel=True)                      # barrel shroud
    for k in range(4):
        for s in (-1, 1):
            p.box((hx + s * 0.0485, hy - 0.33 - 0.045 * k, hz + 0.07), (0.008, 0.02, 0.05), 'ink', deco=True)   # vents
        p.box((hx, hy - 0.34 - 0.05 * k, hz + 0.1185), (0.06, 0.016, 0.008), 'ink', deco=True)
    for sx in (-0.022, 0.022):
        p.cyl((hx + sx, hy - 0.50, hz + 0.07), 0.017, 0.017, 0.17, 'steel', seg=6, rot=(90, 0, 0))   # twin barrels
        p.cyl((hx + sx, hy - 0.655, hz + 0.07), 0.022, 0.022, 0.014, 'plate', seg=8, rot=(90, 0, 0), caps=False, deco=True)   # cannon tips
    p.box((hx, hy - 0.62, hz + 0.07), (0.10, 0.05, 0.075), 'gunmetal')                           # muzzle brake
    for s in (-1, 1):
        p.box((hx + s * 0.0535, hy - 0.62, hz + 0.07), (0.008, 0.03, 0.04), 'ink', deco=True)
        p.box((hx + s * 0.0545, hy - 0.10, hz + 0.075), (0.008, 0.26, 0.02), 'plate', deco=True)   # element stripes
    ar = p.build('BOT_JET_ArmR', bevel=False)
    socket('BOT_JET_MUZZLE', ar, (hx, hy - 0.69, hz + 0.07))

    p = Part(pal)
    _jet_arm(p, J_HAND_L, (-0.2, 1.0, -0.3), 0.31, 0.31, 1)
    hx, hy, hz = J_HAND_L
    p.box((hx, hy, hz + 0.01), (0.085, 0.10, 0.08), 'jet2', bevel=True)                           # hand
    for x in (-0.025, 0.0, 0.025):
        p.box((hx + x, hy - 0.042, hz - 0.06), (0.018, 0.03, 0.07), 'gunmetal')                     # claw fingers
    p.box((hx + 0.05, hy - 0.01, hz - 0.03), (0.02, 0.03, 0.06), 'gunmetal')                        # thumb
    p.box((hx, hy, hz + 0.0555), (0.05, 0.06, 0.008), 'plate', deco=True)
    p.build('BOT_JET_ArmL', bevel=False)

    # ---- pod arm (origin = its hinge on the back unit): a telescoping strut that raises the pod (the game stretches
    # it along its length while the pod rises), a piston, a bracket at the top (socket BOT_JET_PODTOP)
    p = Part(pal)
    p.cyl((-0.035, 0, 0), 0.028, 0.028, 0.07, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.box((0, 0, 0.12), (0.05, 0.04, 0.22), 'jet3')
    p.box((0, 0, 0.175), (0.034, 0.054, 0.12), 'steel')
    p.limb((0, 0.03, 0.02), (0, 0.03, 0.20), 0.011, 0.011, 'steel', seg=6)
    p.box((0, 0, 0.255), (0.07, 0.06, 0.03), 'gunmetal')
    p.box((0, -0.0245, 0.07), (0.02, 0.008, 0.08), 'plate2', deco=True)
    arm = p.build('BOT_JET_PodArm', bevel=False, hull=0.008)
    socket('BOT_JET_PODTOP', arm, (0, 0, J_ARM_LEN))

    # ---- rocket pod (origin = its mount on the arm): a box with layered top armour, side rails, three tubes along -Y
    # with accent rims and rocket tips inside; the lid hinges on the top front edge
    p = Part(pal)
    p.box((0, -0.07, 0.10), (0.22, 0.34, 0.18), 'jet2', bevel=True)
    p.box((0, -0.05, 0.198), (0.18, 0.26, 0.02), 'jet')
    _hexp(p, (0, -0.13, 0.208), '+z', 0.028, 0.005, 'plate')
    for x in (-0.07, 0.07):
        _bolt(p, (x, 0.04, 0.205), '+z')
    for s in (-1, 1):
        p.box((s * 0.115, -0.07, 0.10), (0.012, 0.30, 0.05), 'jet3')
        p.box((s * 0.125, -0.07, 0.10), (0.008, 0.20, 0.02), 'plate', deco=True)
    p.box((0, 0.105, 0.10), (0.16, 0.012, 0.12), 'ink', deco=True)                                # rear exhaust grille
    for x in (-0.068, 0.0, 0.068):
        p.cyl((x, -0.24, 0.10), 0.032, 0.032, 0.02, 'jet3', seg=8, rot=(90, 0, 0))                # tube mouth
        p.cyl((x, -0.25, 0.10), 0.036, 0.036, 0.014, 'plate', seg=8, rot=(90, 0, 0), caps=False, deco=True)   # rim
        p.cyl((x, -0.2615, 0.10), 0.024, 0.024, 0.004, 'ink', seg=8, rot=(90, 0, 0), deco=True)     # bore
        p.cyl((x, -0.252, 0.10), 0.017, 0.0, 0.02, 'red', seg=8, rot=(90, 0, 0), deco=True)         # rocket tip
    p.box((0, 0.0, 0.0), (0.08, 0.06, 0.03), 'gunmetal')                                         # mount
    pod = p.build('BOT_JET_Pod', bevel=False)
    socket('BOT_JET_LID', pod, (0, -0.28, 0.19))
    for k, x in enumerate((-0.068, 0.0, 0.068)):
        socket('BOT_JET_TUBE%d' % k, pod, (x, -0.30, 0.10))
    # lid (origin = hinge): outer plate with a stripe and bolts, the inner face in the accent colour
    p = Part(pal)
    p.box((0, -0.012, -0.09), (0.23, 0.02, 0.18), 'jet')
    p.box((0, -0.0255, -0.09), (0.13, 0.008, 0.022), 'plate', deco=True)
    p.box((0, 0.0015, -0.09), (0.19, 0.008, 0.15), 'plate', deco=True)
    for x in (-0.09, 0.09):
        _bolt(p, (x, -0.019, -0.03), '-y', 0.008)
    p.build('BOT_JET_Lid', bevel=False)

    # ---- jet flame (origin = nozzle exit, pointing down): drawn in the light material, scaled by the thrust
    p = Part(pal)
    p.cyl((0, 0, -0.42), 0.0, 0.055, 0.42, 'jetglow', seg=8)
    p.build('BOT_JET_Flame', bevel=False, hull=0.004)


# ================================================================ BOTS
def build_bots(ao):
    pal = Palette('bots')
    build_crawler(pal)
    build_gunner(pal)
    build_bomber(pal)
    build_drone(pal)
    build_soldier(pal)
    build_blader(pal)
    build_crawler2(pal)
    build_hawk(pal)
    build_kusari(pal)
    build_jet(pal)
    export('bots')


FAMILY = 'bots'
BUILD = build_bots
