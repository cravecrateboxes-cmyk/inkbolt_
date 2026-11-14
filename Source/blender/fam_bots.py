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
import enemy_detail as ED


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
    # detail pass: rolled base bead, hip mounts with pivot pins, lid bolts, hinge and latch, a bezel round the sensor
    # slot, back vent and rivets, pouch flaps and buckles, hazard stencil, serial plate, antenna collar, lamp holder
    rz = lambda z: 0.32 - (z - 0.30) * (0.01 / 0.42)                                   # can radius at height z
    p.cyl((0, 0, 0.318), 0.327, 0.327, 0.022, 'trim', seg=10, caps=False, deco=True)
    for x, y in [(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]:
        a = math.atan2(y, x)
        u, t = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        p.box(tuple(u * 0.3175 + Vector((0, 0, 0.35))), (0.075, 0.07, 0.06), 'trim', rot=(0, 0, math.degrees(a)), deco=True)
        c = u * 0.345 + Vector((0, 0, 0.33))
        p.limb(tuple(c - t * 0.05), tuple(c + t * 0.05), 0.02, 0.02, 'steel', seg=6, deco=True)
    ED.bolt_ring(p, 0, 0, 0.77, 0.30, 10, r=0.012, h=0.007, phase=0.2)
    for x in (-0.07, 0.07):
        p.limb((x - 0.03, 0.352, 0.745), (x + 0.03, 0.352, 0.745), 0.016, 0.016, 'gunmetal', seg=6, deco=True)
    p.box((0, -0.341, 0.735), (0.07, 0.02, 0.04), 'steel', deco=True)
    p.box((0, -0.354, 0.72), (0.03, 0.012, 0.05), 'gunmetal', deco=True)
    for sx in (-1, 1):
        p.box((sx * 0.178, -0.30, 0.60), (0.016, 0.104, 0.086), 'trim', deco=True)
    p.box((0, -0.2995, 0.556), (0.336, 0.099, 0.014), 'trim', deco=True)
    with ED.at(p, ED.facet_frame(2, 10, rz(0.66), 0.66)):
        ED.grille(p, 0, 0, 0.15, 0.07, 4, slat='tin2')
    with ED.at(p, ED.facet_frame(2, 10, rz(0.528), 0.528)):                            # back battery box
        ED.pad(p, 0, 0, 0.16, 0.08, 0.03, 'trim')
        ED.grille(p, 0, 0, 0.12, 0.05, 3, slat='tin2', base=0.03)
    for k in (1, 3, 5):                                                                   # bolted side armour plates
        with ED.at(p, ED.facet_frame(k, 10, rz(0.528), 0.528)):
            ED.pad(p, 0, 0, 0.15, 0.085, 0.006, 'tin3')
            ED.bolts(p, [(sx * 0.06, sy * 0.03) for sx in (-1, 1) for sy in (-1, 1)], r=0.009, top=0.004, color='tin2', seg=4, base=0.006)
    for k in (4, 0):
        p.on_facet(k, 10, 0.335, 0.052, 0.446, (0.142, 0.008, 0.045), 'pouch')
        p.on_facet(k, 10, 0.335, 0.059, 0.42, (0.024, 0.006, 0.09), 'trim')
        p.on_facet(k, 10, 0.335, 0.064, 0.425, (0.032, 0.006, 0.022), 'steel')
    with ED.at(p, ED.facet_frame(6, 10, rz(0.525), 0.525)):
        ED.chevrons(p, 0, 0, 0.10, 0.05, 4)
    with ED.at(p, ED.facet_frame(9, 10, rz(0.53), 0.53)):
        ED.serial_plate(p, 0, 0, 0.08, 0.035)
    p.cyl((0.12, 0.08, 0.765), 0.03, 0.03, 0.03, 'gunmetal', seg=6, deco=True)
    p.cyl((0.12, 0.08, 0.995), 0.028, 0.028, 0.035, 'gunmetal', seg=6, deco=True)
    body = p.build('BOT_CRAWLER_Body')
    socket('BOT_CRAWLER_CORE', body, (0, 0, 0.82))
    for i, (x, y) in enumerate([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]):
        socket('BOT_CRAWLER_HIP%d' % i, body, (x, y, 0.33))
    p = Part(pal)
    for i in range(3):
        p.box(((0.035 if i % 2 else -0.035), 0, -0.05 - i * 0.085), (0.13, 0.06, 0.04), 'spring', deco=True)
    p.box((0, 0, -0.15), (0.03, 0.03, 0.3), 'gunmetal')
    p.cyl((0, 0, -0.355), 0.09, 0.07, 0.05, 'gunmetal', seg=5)
    # detail pass: hip knuckle, hydraulic piston behind the spring, ankle collar, three toe claws
    p.cyl((-0.04, 0, 0), 0.03, 0.03, 0.08, 'trim', seg=6, rot=(0, 90, 0), deco=True)
    ED.piston(p, (0, 0.045, -0.03), (0, 0.045, -0.29), 0.014, 0.008, k=0.5, body='trim', rod='steel')
    p.cyl((0, 0, -0.315), 0.028, 0.028, 0.03, 'trim', seg=6, deco=True)
    for a in (-90, 30, 150):
        r = math.radians(a)
        p.box((0.085 * math.cos(r), 0.085 * math.sin(r), -0.34), (0.05, 0.03, 0.022), 'trim', rot=(0, 0, a), deco=True)
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
    # detail pass: twin lamps on the chest plate, serial plates and rivet rows on the sponsons, exhaust stubs and
    # a grab rail on the power pack, skid bolts, pod rivets, hinge brackets, tow hook, battery cables in the bay
    with ED.at(p, on_edge(P_, 6, 0.5, 0.0)):
        for x in (-0.11, 0.11):
            ED.lamp(p, x, 0.0, 0.02, lens='sticker', w=0.006, base=0.009)
    for sx in (-1, 1):
        p.parent = Matrix.Translation((sx * 0.25, 0, 0.33)) @ Matrix.Rotation(math.radians(7 * sx), 4, 'Y') @ Matrix.Translation((-sx * 0.25, 0, -0.33))
        p.box((sx * 0.3015, 0.12, 0.62), (0.007, 0.10, 0.06), 'sticker', deco=True)
        for z, w in ((0.632, 0.07), (0.608, 0.045)):
            p.box((sx * 0.3055, 0.115, z), (0.006, w, 0.01), 'ink', deco=True)
        for y in (-0.24, -0.14, -0.04, 0.06, 0.16):
            p.cyl((sx * 0.296, y, 0.775), 0.012, 0.012, 0.008, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
    p.parent = Matrix.Identity(4)
    for x in (-0.17, 0.17):
        p.cyl((x, 0.40, 0.92), 0.026, 0.026, 0.05, 'gunmetal', seg=6, deco=True)
        p.cyl((x, 0.40, 0.967), 0.015, 0.015, 0.006, 'ink', seg=6, deco=True)
    for sx in (-1, 1):
        for y in (-0.25, -0.17):
            p.cyl((sx * 0.217, y, 0.03), 0.011, 0.011, 0.008, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
        p.cyl((0.437, -0.20 + 0.10 * (sx + 1), 0.73), 0.009, 0.009, 0.007, 'steel', seg=4, rot=(0, 90, 0), deco=True)
        p.box((sx * 0.20, 0.335, 0.965), (0.05, 0.04, 0.03), 'gunmetal', deco=True)
    p.box((0, 0.355, 0.20), (0.08, 0.03, 0.05), 'gunmetal', deco=True)
    p.box((0, 0.378, 0.195), (0.03, 0.03, 0.03), 'steel', deco=True)
    ED.cable(p, [(0.12, -0.36, 0.905), (0.12, -0.20, 0.968), (0.05, 0.10, 0.968)], 0.018, 'rubber')
    ED.cable(p, [(-0.12, -0.36, 0.905), (-0.12, -0.20, 0.972), (-0.05, 0.10, 0.972)], 0.018, 'red')
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
    # detail pass: panel seams across the cowl, a grab handle on the spine, spine bolts
    for sx in (-1, 1):
        for y in (-0.30, -0.60):
            p.box((sx * 0.245, y, 0.086), (0.12, 0.012, 0.006), 'ink', deco=True)
    for x in (-0.05, 0.05):
        p.box((x, -0.12, 0.125), (0.015, 0.009, 0.025), 'steel', deco=True)
    p.box((0, -0.12, 0.135), (0.14, 0.015, 0.015), 'steel', deco=True)
    for y in (-0.25, -0.40, -0.52):
        for x in (-0.13, 0.13):
            p.cyl((x, y, 0.113), 0.01, 0.01, 0.006, 'steel', seg=4, deco=True)
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
    # detail pass: barrel cooling rings, side ammo drum with a feed chute, receiver bolts and top rail slots
    for sx in (-1, 1):
        for y in (-0.385, -0.415):
            p.cyl((sx * 0.032, y, 0), 0.031, 0.031, 0.012, 'gunmetal', seg=6, rot=(90, 0, 0), caps=False, deco=True)
        for y in (-0.09, -0.19):
            p.cyl((sx * 0.073, y, 0.045), 0.01, 0.01, 0.006, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
    p.cyl((-0.073, -0.14, -0.02), 0.05, 0.05, 0.025, 'bin2', seg=8, rot=(0, -90, 0), deco=True)
    p.cyl((-0.096, -0.14, -0.02), 0.022, 0.022, 0.006, 'steel', seg=6, rot=(0, -90, 0), deco=True)
    p.box((-0.085, -0.145, 0.03), (0.016, 0.04, 0.03), 'gunmetal', deco=True)
    for y in (-0.08, -0.19):
        p.box((0, y, 0.0815), (0.06, 0.012, 0.007), 'ink', deco=True)
    gun = p.build('BOT_GUNNER_Gun', bevel=False)
    socket('BOT_GUNNER_GUN', gun, (0, -0.51, 0))

    # wheel (origin on the axle; axis X; symmetric so the game mirrors it for the other side)
    p = Part(pal)
    w = 0.075
    p.cyl((-w / 2, 0, 0), G_WHEEL_R, G_WHEEL_R, w, 'rubber', seg=8, rot=(0, 90, 0))
    p.cyl((-w / 2 - 0.004, 0, 0), 0.072, 0.072, w + 0.008, 'bin2', seg=6, rot=(0, 90, 0), deco=True)     # armoured hub
    p.cyl((-w / 2 - 0.01, 0, 0), 0.026, 0.026, w + 0.02, 'gunmetal', seg=6, rot=(0, 90, 0), deco=True)   # axle nut
    # detail pass: tread lugs on every tyre facet, five hub bolts on each face
    ap = G_WHEEL_R * math.cos(math.pi / 8)
    for j in range(8):
        b = math.radians(22.5 + 45 * j)
        r = ap + 0.005
        p.box((0, r * math.cos(b), r * math.sin(b)), (0.066, 0.03, 0.014), 'rubber', rot=(math.degrees(b) - 90, 0, 0), deco=True)
    for sx in (-1, 1):
        for j in range(5):
            b = 2 * math.pi * j / 5
            p.cyl((sx * 0.0395, 0.048 * math.cos(b), 0.048 * math.sin(b)), 0.009, 0.009, 0.007, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
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
    # detail pass: roller mudguards, bolted fork plates with a slot, cradle bolts, moulded flutes on the shoulder,
    # neck thread rings, a pressure gauge and a hose from the canister valve to the neck, a second canister clamp,
    # explosive diamonds and a barcode on the label
    for sy in (-1, 1):
        arc = [(sy * r * math.cos(math.radians(a)), B_AXLE[2] + r * math.sin(math.radians(a)))
               for r, angs in ((0.165, range(18, 79, 12)), (0.155, range(78, 17, -12))) for a in angs]
        sprism(p, arc, -0.20, 0.20, 'steel', deco=True)
    for sx in (-1, 1):
        for y in (-0.025, 0.025):
            p.cyl((sx * 0.275, y, 0.285), 0.009, 0.009, 0.008, 'steel', seg=6, rot=(0, sx * 90, 0), deco=True)
        p.box((sx * 0.2785, 0, 0.225), (0.007, 0.04, 0.035), 'ink', deco=True)
    ED.bolt_ring(p, 0, 0, 0.32, 0.222, 8, r=0.01, h=0.007, phase=math.pi / 8, seg=5)
    for k in range(0, SEG, 2):
        p.on_slope(k, SEG, (0.212, 0.665), (0.165, 0.725), 0.5, 0.003, (0.034, 0.006, 0.05), 'glass2')
    for z in (0.848, 0.858):
        p.band(z, z + 0.006, 0.081, 'glass2', seg=8)
    p.cyl((0, cy, 0.525), 0.072, 0.072, 0.02, 'core2', seg=8, caps=False, deco=True)
    p.cyl((0, cy - 0.064, 0.43), 0.026, 0.026, 0.008, 'gunmetal', seg=8, rot=(90, 0, 0), deco=True)
    p.cyl((0, cy - 0.070, 0.43), 0.02, 0.02, 0.005, 'paper', seg=8, rot=(90, 0, 0), deco=True)
    p.box((0.006, cy - 0.0765, 0.435), (0.004, 0.004, 0.018), 'ink', rot=(0, 30, 0), deco=True)
    ED.cable(p, [(0, cy, 0.632), (0, -0.25, 0.70), (0, -0.20, 0.735), (0, -0.12, 0.765)], 0.016, 'rubber')
    for k in (5, 11):
        with ED.at(p, ED.facet_frame(k, SEG, 0.232, 0.51)):
            ED.pad(p, 0, 0, 0.042, 0.042, 0.004, 'red', base=0.0, rot=45)
            ED.pad(p, 0, 0, 0.012, 0.012, 0.003, 'ink', base=0.004)
    with ED.at(p, ED.facet_frame(2, SEG, 0.232, 0.51)):
        for i, w in enumerate((0.004, 0.008, 0.003, 0.006, 0.004, 0.009, 0.003)):
            ED.pad(p, -0.024 + 0.008 * i, 0, w, 0.04, 0.003, 'ink')
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
    # detail pass: tread lugs on every facet (three rows between the steel rings), hub bolts on both ends
    ap = B_ROLLER_R * math.cos(math.pi / 10)
    for j in range(10):
        b = math.radians(36 * j)
        for x, w in ((0.0, 0.18), (-0.172, 0.06), (0.172, 0.06)):
            r = ap + 0.004
            p.box((x, r * math.cos(b), r * math.sin(b)), (w, 0.028, 0.012), 'rubber', rot=(math.degrees(b) - 90, 0, 0), deco=True)
    for sx in (-1, 1):
        for j in range(4):
            b = math.pi / 4 + math.pi / 2 * j
            p.cyl((sx * 0.226, 0.034 * math.cos(b), 0.034 * math.sin(b)), 0.009, 0.009, 0.008, 'steel', seg=5, rot=(0, sx * 90, 0), deco=True)
    p.build('BOT_BOMBER_Roller', bevel=False)

    # crimp cap + fuse wick (origin on the neck top)
    p = Part(pal)
    p.cyl((0, 0, 0.0), 0.088, 0.088, 0.05, 'capred', seg=10)
    pts = [(0, 0, 0.06), (0.02, 0.005, 0.10), (0.006, -0.01, 0.14), (0.022, 0.0, 0.175)]
    for a, b in zip(pts, pts[1:]):
        p.beam(a, b, 0.016, 'wick')
    p.cyl((0, 0, -0.012), 0.095, 0.095, 0.02, 'capred', seg=10, caps=False, deco=True)   # crimp skirt
    p.cyl((0, 0, 0.046), 0.026, 0.02, 0.025, 'alu', seg=6, deco=True)                     # wick holder
    # detail pass: crimp teeth round the skirt, knurled grip ridges, a crimp ring on the wick holder
    for k in range(10):
        p.on_facet(k, 10, 0.095, 0.0, -0.002, (0.014, 0.008, 0.018), 'red')
        p.on_facet(k, 10, 0.088, 0.0, 0.034, (0.012, 0.007, 0.022), 'capred', phase=math.pi / 10)
    p.cyl((0, 0, 0.056), 0.025, 0.025, 0.008, 'gunmetal', seg=6, caps=False, deco=True)
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
    # detail pass: rolled top chime and bottom bead, a seam strip down the back, side vents, a can label with
    # stencil bars, two side cameras over the sensor slot, a gimbal yoke round the gun
    p.band(0.563, 0.572, 0.168, 'alu', seg=SEG)
    p.band(0.075, 0.09, 0.194, 'can2', seg=SEG)
    for z0, z1 in ((0.095, 0.175), (0.295, 0.365), (0.435, 0.495)):
        p.on_facet(2, SEG, 0.19, 0.0, (z0 + z1) / 2, (0.016, 0.007, z1 - z0), 'can2')
    for k in (0, 5):
        with ED.at(p, ED.facet_frame(k, SEG, 0.19, 0.33)):
            ED.grille(p, 0, 0, 0.07, 0.05, 3, slat='can2')
    with ED.at(p, ED.facet_frame(10, SEG, 0.19, 0.13)):
        ED.pad(p, 0, 0, 0.075, 0.07, 0.004, 'paper')
        ED.stencil(p, -0.005, 0.016, 0.05, 0.008, 3, base=0.004)
        ED.pad(p, -0.012, -0.004, 0.04, 0.006, 0.003, 'ink', base=0.004)
        ED.pad(p, -0.006, -0.018, 0.052, 0.006, 0.003, 'ink', base=0.004)
    for k in (11, 6):
        with ED.at(p, ED.facet_frame(k, SEG, 0.19, 0.465)):
            ED.pad(p, 0, 0, 0.04, 0.03, 0.012, 'gunmetal')
            ED.lamp(p, 0, 0, 0.009, lens='teal', w=0.004, base=0.012, seg=6)
    for sx in (-1, 1):
        p.box((sx * 0.048, D_PIVOT[1], -0.01), (0.012, 0.04, 0.06), 'gunmetal', deco=True)
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
    # detail pass: rotor guards (a ring on two struts round each rotor disc), motor housings (cooling fins, bell
    # cap), nav lamps on the pods, bolts where the arms cross the lid, a lamp holder under the light
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = D_ARM * math.cos(a), D_ARM * math.sin(a)
        p.parent = Matrix.Translation((x, y, 0))
        p.lathe([(0.19, 0.084), (0.199, 0.084), (0.199, 0.102), (0.19, 0.102), (0.19, 0.084)], 'gunmetal', seg=12, deco=True)
        for da in (-50, 50):
            b = a + math.radians(180 + da)
            p.beam((0.04 * math.cos(b), 0.04 * math.sin(b), 0.05), (0.192 * math.cos(b), 0.192 * math.sin(b), 0.09), 0.012, 'gunmetal', deco=True)
        for z in (0.018, 0.042):
            p.cyl((0, 0, z), 0.05, 0.05, 0.008, 'gunmetal', seg=6, caps=False, deco=True)
        p.cyl((0, 0, 0.072), 0.032, 0.028, 0.014, 'gunmetal', seg=6, deco=True)
        p.box((0.046 * math.cos(a), 0.046 * math.sin(a), 0.06), (0.014, 0.014, 0.012), 'red' if k in (1, 2) else 'teal', rot=(0, 0, math.degrees(a)), deco=True)
        p.parent = Matrix.Identity(4)
    ED.bolt_ring(p, 0, 0, 0.022, 0.135, 4, r=0.01, h=0.006, phase=0.0)
    p.cyl((0.0, 0.08, 0.145), 0.02, 0.02, 0.025, 'gunmetal', seg=6, deco=True)
    lid = p.build('BOT_DRONE_Lid', bevel=False)
    for k, q in enumerate(pods):
        socket('BOT_DRONE_ROTOR%d' % k, lid, q)
    socket('BOT_DRONE_LIGHT', lid, (0.0, 0.08, 0.205))

    # rotor: one blade bar with amber tips
    p = Part(pal)
    p.box((0, 0, 0.0), (0.30, 0.042, 0.008), 'ink')
    for sx in (-1, 1):
        p.box((sx * 0.168, 0, 0.0), (0.036, 0.042, 0.008), 'amber', deco=True)
        p.box((sx * 0.085, sx * 0.012, 0.0), (0.12, 0.012, 0.014), 'gunmetal', deco=True)   # raised leading edge
    p.cyl((0, 0, -0.008), 0.022, 0.018, 0.02, 'gunmetal', seg=6, deco=True)                # hub cap
    p.build('BOT_DRONE_Rotor', bevel=False, hull=0.008)

    # gun on its gimbal (origin on the pivot, barrel along -Y)
    p = Part(pal)
    p.box((0, 0, 0), (0.08, 0.06, 0.06), 'gunmetal')
    p.cyl((0, -0.01, 0), 0.026, 0.026, 0.19, 'alu', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.17, 0), 0.036, 0.036, 0.04, 'gunmetal', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.06, 0), 0.031, 0.031, 0.03, 'amber', seg=6, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, -0.207, 0), 0.018, 0.018, 0.006, 'ink', seg=6, rot=(90, 0, 0), deco=True)
    # detail pass: cooling rings on the barrel, ported muzzle brake, ammo box under the breech, a sight on top
    for y in (-0.10, -0.125, -0.15):
        p.cyl((0, y, 0), 0.03, 0.03, 0.008, 'gunmetal', seg=6, rot=(90, 0, 0), caps=False, deco=True)
    for sx in (-1, 1):
        p.box((sx * 0.034, -0.19, 0), (0.008, 0.014, 0.016), 'ink', deco=True)
    p.box((0, 0.0, -0.038), (0.05, 0.045, 0.028), 'can2', deco=True)
    p.box((0, 0.0, -0.0545), (0.03, 0.03, 0.006), 'amber', deco=True)
    p.box((0, -0.01, 0.036), (0.012, 0.03, 0.016), 'gunmetal', deco=True)
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
    # detail pass: boot strap with a buckle, knee bolts, a calf piston
    p.box((0, -0.045, -0.385), (0.138, 0.278, 0.02), 'suit2', deco=True)
    p.box((0.072, -0.08, -0.385), (0.008, 0.03, 0.028), 'steel', deco=True)
    for x in (-0.04, 0.04):
        p.cyl((x, -0.102, 0.0), 0.01, 0.01, 0.006, 'gunmetal', seg=4, rot=(90, 0, 0), deco=True)
    ED.piston(p, (0, 0.06, -0.05), (0, 0.06, -0.33), 0.016, 0.009, k=0.5)
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
    for s in (-1, 1):                                                                        # detail: side rails + rivets
        p.box((s * 0.158, 0.0, 0.205), (0.012, 0.18, 0.02), 'gunmetal', deco=True)
        for y in (-0.06, 0.06):
            p.cyl((s * 0.164, y, 0.205), 0.008, 0.008, 0.008, 'steel', seg=4, rot=(0, s * 90, 0), deco=True)
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
    for s in (-1, 1):                                                                        # detail: brow bolts, top vents
        p.cyl((s * 0.11, -0.188, 0.215), 0.01, 0.01, 0.008, 'gunmetal', seg=4, rot=(90, 0, 0), deco=True)
    for x in (-0.06, 0.0, 0.06):
        p.box((x, 0.06, 0.277), (0.03, 0.10, 0.006), 'ink', deco=True)
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
    for s in (-1, 1):                                                                        # detail: cheek guard bolts
        p.cyl((s * 0.14, -0.09, 0.07), 0.01, 0.01, 0.008, 'gunmetal', seg=4, rot=(0, s * 90, 8 * s), deco=True)
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
    e = Vector(_elbow((0, 0, 0), S_HAND_L, 0.33, 0.32, (0.5, 0.2, -1.0)))                  # detail: forearm piston
    h = Vector(S_HAND_L)
    ED.piston(p, tuple(e + (h - e) * 0.15 + Vector((0, 0, -0.075))), tuple(e + (h - e) * 0.75 + Vector((0, 0, -0.07))), 0.014, 0.008)
    al = p.build('BOT_SOLDIER_ArmL', bevel=False)
    socket('BOT_SOLDIER_HANDL', al, (S_HAND_L[0], S_HAND_L[1] - 0.02, S_HAND_L[2] + 0.07))

    # ---- grenade: gunmetal can, red band, amber fuse cap, ink spoon (origin = centre)
    p = Part(pal)
    p.cyl((0, 0, -0.05), 0.045, 0.045, 0.10, 'gunmetal', seg=8)
    p.cyl((0, 0, 0.05), 0.024, 0.024, 0.025, 'amber', seg=6)
    p.cyl((0, 0, -0.012), 0.049, 0.049, 0.026, 'red', seg=8, caps=False, deco=True)
    p.box((0.047, 0, 0.015), (0.008, 0.022, 0.06), 'ink', deco=True)
    # detail pass: grip ribs, a fuse collar and a pull ring
    for z in (-0.04, 0.025):
        p.cyl((0, 0, z), 0.048, 0.048, 0.008, 'ink', seg=8, caps=False, deco=True)
    p.cyl((0, 0, 0.046), 0.03, 0.03, 0.012, 'steel', seg=6, deco=True)
    p.cyl((-0.03, 0, 0.075), 0.014, 0.014, 0.006, 'steel', seg=6, rot=(90, 0, 0), caps=False, deco=True)
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
    # detail pass: a bezel round the sensor slot, rim bolts between the bands, a seam band on the shoulder, bolts on
    # the crown, three thruster nozzles under the saucer, hub post collar and slip rings
    with ED.at(p, ED.facet_frame(8, SEG, 0.49, 0.43, phase=ph)):
        ED.pad(p, 0, 0, 0.25, 0.052, 0.004, 'gunmetal')
    for k in range(SEG):
        if k in (7, 8, 9):
            continue
        with ED.at(p, ED.facet_frame(k, SEG, 0.49, 0.43, phase=ph)):
            ED.bolts(p, [(-0.07, 0), (0.07, 0)], r=0.011, top=0.006, color='violet2', seg=4)
    (r0, z0), (r1, z1) = (0.49, 0.48), (0.42, 0.55)
    n = Vector((z1 - z0, r0 - r1)).normalized() * 0.004
    p.lathe([(r0 + (r1 - r0) * t + n.x, z0 + (z1 - z0) * t + n.y) for t in (0.42, 0.58)], 'violet2', seg=SEG, phase=ph, deco=True)
    for k in range(1, SEG, 2):
        p.on_slope(k, SEG, (0.28, 0.61), (0.17, 0.63), 0.5, 0.0, (0.022, 0.006, 0.022), 'gunmetal', phase=ph)
    for k in range(SEG):                                                                    # crown armour plates + vent slats
        with ED.at(p, ED.slope_frame(k, SEG, (0.42, 0.55), (0.28, 0.61), 0.5, phase=ph)):
            if k in (2, 5, 8, 11):
                for y in (-0.014, 0.0, 0.014):
                    ED.pad(p, 0, y, 0.044, 0.006, 0.003, 'gunmetal', base=0.010)
            else:
                ED.pad(p, 0, 0, 0.12, 0.08, 0.006, 'violet2')
                ED.bolts(p, [(-0.045, 0.025), (0.045, 0.025)], r=0.009, top=0.004, color='gunmetal', seg=4, base=0.006)
    for j in range(3):
        a = math.radians(90 + 120 * j)
        x, y = 0.15 * math.cos(a), 0.15 * math.sin(a)
        p.cyl((x, y, 0.13), 0.04, 0.032, 0.04, 'gunmetal', seg=8, deco=True)
        p.cyl((x, y, 0.124), 0.026, 0.026, 0.008, 'teal', seg=8, deco=True)
    p.cyl((0, 0, 0.66), 0.055, 0.055, 0.03, 'steel', seg=8, deco=True)
    for z in (0.75, 0.80):
        p.cyl((0, 0, z), 0.05, 0.05, 0.012, 'amber', seg=8, caps=False, deco=True)
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
    # detail pass: lightening holes in the arms, a hydraulic piston over the weapon arm, clamp bolts and jaw slit,
    # weight plates on the counterweight, bolts round the hub drum
    for sy in (-1, 1):
        for x in (0.16, 0.25, 0.34, -0.15, -0.24):
            p.box((x, sy * 0.0315, 0), (0.045 if x > 0 else 0.04, 0.005, 0.024), 'ink', deco=True)
        for x in (0.45, 0.49):
            p.cyl((x, sy * 0.045, 0.022), 0.009, 0.009, 0.006, 'steel', seg=4, rot=(sy * -90, 0, 0), deco=True)
    ED.piston(p, (0.10, 0, 0.045), (0.40, 0, 0.045), 0.012, 0.007, k=0.55, body='gunmetal', rod='steel')
    for x in (0.10, 0.40):
        p.box((x, 0, 0.034), (0.022, 0.016, 0.022), 'gunmetal', deco=True)
    p.box((X_GRIP[0] + 0.0, 0, 0.0425), (0.07, 0.012, 0.006), 'ink', deco=True)
    for z in (-0.03, -0.065):
        p.cyl((-0.34, 0, z), 0.074, 0.074, 0.008, 'gunmetal', seg=8, caps=False, deco=True)
    ED.bolt_ring(p, 0, 0, 0.04, 0.095, 8, r=0.01, h=0.006, phase=math.pi / 8, seg=4)
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
    # detail pass: diamond ito wrap on four sides of the handle, seppa washers and a ring on the guard, a fuller
    # (bo-hi) groove line along both flats of the blade near the spine
    for j in range(4):
        b = math.radians(22.5 + 90 * j)
        for i, x in enumerate((-0.12, -0.08, -0.04, 0.0, 0.04, 0.08)):
            p.parent = Matrix.Rotation(b - math.pi / 2, 4, 'X')
            p.box((x, 0, 0.0215), (0.013, 0.013, 0.006), 'paper', rot=(0, 0, 45), deco=True)
            p.parent = Matrix.Identity(4)
    for x in (0.109, 0.142):
        p.cyl((x, 0, 0), 0.034, 0.034, 0.006, 'amber', seg=8, rot=(0, 90, 0), deco=True)
    for x in (0.117, 0.137):
        p.cyl((x, 0, 0), 0.052, 0.052, 0.006, 'ink', seg=12, rot=(0, 90, 0), caps=False, deco=True)
    for sz in (-1, 1):
        for a, b in zip(st[1:], st[2:]):
            if b[0] > 0.86:
                break
            pts = []
            for (x, yb, ye, t), s_ in ((a, 0.14), (b, 0.14), (b, 0.42), (a, 0.42)):
                ys, yh = yb + (ye - yb) * 0.3, yb + (ye - yb) * 0.72
                pts.append(Vector((x, ys + (yh - ys) * s_, sz * (t + (t * 0.5 - t) * s_))))
            o = sum(pts, Vector()) / 4
            u = (pts[1] - pts[0]).normalized()
            nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0]).normalized()
            if nrm.z * sz < 0:
                nrm = -nrm
            w = nrm.cross(u)
            F = Matrix((u, w, nrm)).transposed().to_4x4()
            F.translation = o
            q = [((v - o).dot(u), (v - o).dot(w)) for v in pts]
            if _parea(q) < 0:
                q = list(reversed(q))
            p.parent = F
            p.prism(q, -0.0015, 0.003, 'gunmetal', deco=True)
            p.parent = Matrix.Identity(4)
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
    # detail pass: wrapped grip rings, head bolts and hazard stencils on both faces, a bevel line along the blade
    # inside the glowing edge, a power cable from the battery over the head, a pommel cap
    for x in (0.10, 0.145, 0.19, 0.235, 0.28):
        p.cyl((x, 0, 0), 0.033, 0.033, 0.009, 'gunmetal', seg=8, rot=(0, 90, 0), caps=False, deco=True)
    for sz in (-1, 1):
        for x in (0.655, 0.745):
            for y in (-0.025, 0.025):
                p.cyl((x, y, sz * 0.0355), 0.008, 0.008, 0.008, 'steel', seg=4, rot=(0, 0 if sz > 0 else 180, 0), deco=True)
        p.box((0.70, 0.0, sz * 0.0385), (0.05, 0.03, 0.006), 'amber', deco=True)
        for x in (0.687, 0.70, 0.713):
            p.box((x, 0.0, sz * 0.0435), (0.005, 0.024, 0.004), 'ink', rot=(0, 0, 30), deco=True)
        p.prism([(0.575, 0.205), (0.70, 0.235), (0.825, 0.205), (0.83, 0.217), (0.70, 0.249), (0.57, 0.217)],
                *(sorted((sz * 0.0125, sz * 0.018))), 'gunmetal', deco=True)
    ED.cable(p, [(0.68, -0.09, 0.02), (0.68, -0.05, 0.052), (0.70, 0.03, 0.052), (0.72, 0.06, 0.02)], 0.012, 'ink')
    p.cyl((-0.13, 0, 0), 0.034, 0.03, 0.012, 'amber', seg=8, rot=(0, 90, 0), deco=True)
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
    # detail pass: hip mounts with pivot pins, cap rim bolts, head ring vents, chin grille, back heat sink, rivets on
    # the shell plates, bolted belt armour, serial plate, antenna collar and lamp holder (plates keep the key colours)
    rz = lambda z: 0.32 - (z - 0.30) * (0.01 / 0.30)
    for x, y in [(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]:
        a = math.atan2(y, x)
        u, t = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        p.box(tuple(u * 0.3175 + Vector((0, 0, 0.355))), (0.075, 0.07, 0.06), 'gunmetal', rot=(0, 0, math.degrees(a)), deco=True)
        c = u * 0.345 + Vector((0, 0, 0.33))
        p.limb(tuple(c - t * 0.05), tuple(c + t * 0.05), 0.02, 0.02, 'steel', seg=6, deco=True)
    ED.bolt_ring(p, 0, 0, 0.765, 0.212, 8, r=0.011, h=0.007, color='gunmetal', phase=0.3)
    for k in (1, 2, 3):                                                                   # head ring vents
        with ED.at(p, ED.slope_frame(k, SEG, (0.31, 0.60), (0.25, 0.73), 0.5)):
            ED.grille(p, 0, 0, 0.09, 0.06, 3, color='ink', slat='gunmetal')
    with ED.at(p, ED.facet_frame(7, SEG, rz(0.555), 0.555)):                             # chin grille under the visor
        ED.grille(p, 0, 0, 0.12, 0.05, 3, color='ink', slat='gunmetal', base=0.009)   # over the panel line
    with ED.at(p, ED.facet_frame(2, SEG, rz(0.553), 0.553)):                             # back heat sink
        ED.pad(p, 0, 0, 0.15, 0.07, 0.006, 'gunmetal')
        for i in range(5):
            ED.pad(p, -0.06 + 0.03 * i, 0, 0.008, 0.06, 0.02, 'ink', base=0.006)
    for k in (0, 4, 6, 8):                                                                # rivets on the shell plates
        with ED.at(p, ED.facet_frame(k, SEG, rz(0.555), 0.555)):
            ED.bolts(p, [(sx * 0.07, sy * 0.03) for sx in (-1, 1) for sy in (-1, 1)], r=0.009, top=0.004, color='gunmetal', seg=4)
    for k in (2, 4, 0, 9, 5):                                                             # bolted belt armour
        with ED.at(p, ED.facet_frame(k, SEG, 0.335, 0.405, out=0.052)):
            ED.bolts(p, [(sx * 0.042, 0.035) for sx in (-1, 1)], r=0.01, top=0.005, color='gunmetal', seg=6)
    with ED.at(p, ED.facet_frame(0, SEG, rz(0.535), 0.535)):
        ED.serial_plate(p, 0, 0, 0.07, 0.03, color='paper')
    p.cyl((0.12, 0.08, 0.765), 0.03, 0.03, 0.03, 'gunmetal', seg=6, deco=True)
    p.cyl((0.12, 0.08, 0.995), 0.028, 0.028, 0.035, 'gunmetal', seg=6, deco=True)
    p.build('BOT_CRAWLER_Body2')
    # legs: armoured thigh guard and a wide plated foot, same pivot and length
    p = Part(pal)
    p.box((0, 0, -0.02), (0.11, 0.08, 0.07), 'plate2', bevel=True)
    for i in range(2):
        p.box(((0.03 if i % 2 else -0.03), 0, -0.10 - i * 0.075), (0.11, 0.055, 0.035), 'gunmetal', deco=True)
    p.box((0, 0, -0.17), (0.034, 0.034, 0.30), 'plate')
    p.box((0, -0.022, -0.25), (0.044, 0.01, 0.09), 'plate2', deco=True)
    p.cyl((0, 0, -0.355), 0.095, 0.07, 0.05, 'plate2', seg=6)
    # detail pass: hip knuckle, hydraulic piston, ankle collar, toe claws, knee bolts
    p.cyl((-0.05, 0, 0), 0.026, 0.026, 0.10, 'gunmetal', seg=6, rot=(0, 90, 0), deco=True)
    ED.piston(p, (0, 0.045, -0.06), (0, 0.045, -0.29), 0.014, 0.008, k=0.5, body='gunmetal', rod='steel')
    p.cyl((0, 0, -0.315), 0.029, 0.029, 0.03, 'gunmetal', seg=6, deco=True)
    for a in (-90, 30, 150):
        r = math.radians(a)
        p.box((0.088 * math.cos(r), 0.088 * math.sin(r), -0.34), (0.05, 0.03, 0.022), 'gunmetal', rot=(0, 0, a), deco=True)
    for x in (-0.03, 0.03):
        p.cyl((x, -0.0395, -0.02), 0.009, 0.009, 0.006, 'gunmetal', seg=4, rot=(90, 0, 0), deco=True)
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
    # detail pass: panel seam rings round the fuselage, a sensor bezel round the nose eye, a dorsal sensor turret,
    # intake slats, pylon bolts, a blade antenna under the belly, a collar round the core, cooling rings and nozzle
    # petals on the thruster, serial stencils on the fins
    p.parent = Matrix.Translation((0, 0, H_CEN)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Diagonal(Vector((1, 0.72, 1, 1)))
    rp = lambda z: next(r0 + (r1 - r0) * (z - z0) / (z1 - z0) for (r0, z0), (r1, z1) in zip(prof, prof[1:]) if z0 <= z <= z1)
    for zc in (-0.27, 0.28):
        p.lathe([(rp(zc - 0.005) + 0.0055, zc - 0.005), (rp(zc + 0.005) + 0.0055, zc + 0.005)], 'ink', seg=SEG, phase=ph, deco=True)
    p.parent = Matrix.Identity(4)
    ly = Vector((0, math.cos(math.radians(-28)), math.sin(math.radians(-28))))
    p.box(tuple(Vector((0, -0.385, H_CEN + 0.07)) + ly * 0.012), (0.19, 0.06, 0.06), 'gunmetal', rot=(-28, 0, 0), deco=True)
    p.cyl((0, 0.145, top + 0.0425), 0.03, 0.026, 0.022, 'hawk3', seg=8, deco=True)
    p.box((0, 0.118, top + 0.055), (0.03, 0.012, 0.012), 'lens', deco=True)
    for sx in (-1, 1):
        for z in (H_CEN - 0.055, H_CEN - 0.03, H_CEN - 0.005):
            p.box((sx * 0.222, -0.157, z), (0.020, 0.008, 0.006), 'gunmetal', deco=True)
        for y in (-0.02, 0.06):
            p.cyl((sx * 0.25, y, H_FAN[2] + 0.018), 0.01, 0.01, 0.006, 'steel', seg=4, deco=True)
        p.parent = Matrix.Translation((sx * 0.045, 0, top + 0.03)) @ Matrix.Rotation(math.radians(-30 * sx), 4, 'Y') @ _YZX
        for i in range(3):
            p.box((0.31 + 0.025 * i, 0.07, sx * 0.0135), (0.012, 0.03, 0.005), 'hawk3', deco=True)
        p.parent = Matrix.Identity(4)
    p.box((0, -0.06, H_CEN - 0.155), (0.006, 0.07, 0.035), 'hawk2', rot=(25, 0, 0), deco=True)
    p.parent = Matrix.Translation((0, 0.17, H_CEN - 0.145)) @ Matrix.Diagonal(Vector((1, 1.2, 1, 1)))
    p.cyl((0, 0, 0), 0.082, 0.082, 0.014, 'gunmetal', seg=10, caps=False, deco=True)
    p.parent = Matrix.Identity(4)
    for y in (0.415, 0.445):
        p.cyl((0, y, H_CEN), 0.088, 0.088, 0.01, 'ink', seg=10, rot=(-90, 0, 0), caps=False, deco=True)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        p.box((0.074 * math.cos(a), 0.54, H_CEN + 0.074 * math.sin(a)), (0.03, 0.03, 0.008), 'gunmetal',
              rot=(0, -math.degrees(a) + 90, 0), deco=True)
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
    # detail pass: twelve bolts round the duct lip, four extra stator vanes, cooling bands on the motor housing
    for k in range(12):
        p.on_slope(k, 12, (0.205, -0.01), (0.20, 0.045), 0.82, 0.0, (0.014, 0.007, 0.014), 'gunmetal')
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        p.beam((0.045 * math.cos(a), 0.045 * math.sin(a), -0.02), (0.152 * math.cos(a), 0.152 * math.sin(a), -0.02), 0.012, 'gunmetal', deco=True)
    for z in (-0.045, -0.03):
        p.cyl((0, 0, z), 0.043, 0.043, 0.007, 'gunmetal', seg=8, caps=False, deco=True)
    p.build('BOT_HAWK_Fan', bevel=False, hull=0.01)
    # rotor: three blades
    p = Part(pal)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.box((math.cos(a) * 0.075, math.sin(a) * 0.075, 0.0), (0.12, 0.034, 0.008), 'gunmetal', rot=(18, 0, math.degrees(a)))
    p.cyl((0, 0, -0.012), 0.026, 0.026, 0.024, 'hawk3', seg=8)
    # detail pass: a spinner cone on the hub, dark blade tips
    p.cyl((0, 0, 0.012), 0.02, 0.006, 0.02, 'gunmetal', seg=6, deco=True)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.box((math.cos(a) * 0.131, math.sin(a) * 0.131, 0.0), (0.016, 0.042, 0.016), 'gunmetal', rot=(18, 0, math.degrees(a)), deco=True)
    p.build('BOT_HAWK_Rotor', bevel=False, hull=0.006)
    # chin turret (origin = pivot, barrels along -Y)
    p = Part(pal)
    p.sphere((0, 0, 0), 0.065, 'hawk', seg=(10, 6))
    for sx in (-1, 1):
        p.cyl((sx * 0.025, -0.03, -0.005), 0.016, 0.016, 0.16, 'gunmetal', seg=6, rot=(90, 0, 0))
        p.cyl((sx * 0.025, -0.18, -0.005), 0.021, 0.021, 0.03, 'ink', seg=6, rot=(90, 0, 0))
    p.cyl((0, -0.035, 0), 0.0675, 0.0675, 0.02, 'plate', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    # detail pass: vented barrel jackets, side armour cheeks with a sensor lens, an ammo feed on top
    for sx in (-1, 1):
        p.cyl((sx * 0.025, -0.07, -0.005), 0.021, 0.021, 0.06, 'hawk', seg=6, rot=(90, 0, 0), deco=True)
        for y in (-0.085, -0.105):
            p.box((sx * 0.025, y, 0.0135), (0.008, 0.01, 0.006), 'ink', deco=True)
        p.box((sx * 0.058, 0.0, 0.0), (0.02, 0.07, 0.05), 'hawk2', deco=True)
    p.box((0.069, -0.02, 0.008), (0.004, 0.016, 0.016), 'lens', deco=True)
    p.box((0, 0.01, 0.064), (0.04, 0.05, 0.02), 'gunmetal', deco=True)
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
    """shoulder ball, a tapered upper arm under a curved outer plate, elbow ball, a sculpted gauntlet, wrist ring"""
    import bot_shapes_air as SA
    e = Vector(_elbow((0, 0, 0), hand, la, lb, pole))
    h = Vector(hand)
    out = Vector((side, 0.0, 0.0))
    p.sphere((0, 0, 0), 0.088, 'gunmetal', seg=(8, 4))
    L1, L2 = e.length, (h - e).length
    p.parent = _jframe((0, 0, 0), e, out)
    SA.limb(p, [(0.03, 0.05, 0.05, 0.05), (L1 * 0.45, 0.06, 0.058, 0.064, 0, 0.004), (L1 * 0.95, 0.05, 0.05, 0.05)], 'jet2', n=8, e=2.2)
    SA.shell(p, [(L1 * 0.14, 0.066, 0.07, 0.012), (L1 * 0.2, 0.076, 0.082, 0.02), (L1 * 0.7, 0.07, 0.078, 0.02),
                 (L1 * 0.78, 0.06, 0.068, 0.012)], 15, 165, 'jet', k=4)
    p.parent = Matrix.Identity(4)
    p.sphere(tuple(e), 0.06, 'gunmetal', seg=(8, 4))
    p.parent = _jframe(e, h, out)
    SA.limb(p, [(0.02, 0.046, 0.046, 0.05), (L2 * 0.3, 0.064, 0.058, 0.084, 0, 0.012), (L2 * 0.68, 0.062, 0.056, 0.078, 0, 0.01),
                (L2 * 0.84, 0.048, 0.048, 0.054)], 'jet', n=12, e=2.6)
    SA.sweep(p, [(0.0, 0.0, L2 * z) for z in (0.36, 0.48, 0.6)], [(0, 1, 0)] * 3, 0.03, 0.005, 'jet3', off=0.088)   # raised guard ridge
    SA.limb(p, [(L2 * 0.83, 0.058, 0.058, 0.058), (L2 * 0.84 + 0.04, 0.056, 0.056, 0.056)], 'gunmetal', n=10, e=2.0)   # wrist ring
    p.parent = Matrix.Identity(4)
    return e


def build_jet(pal):
    import bot_shapes_air as SA
    # ---- hips: pelvis core, a rounded belt, a curved codpiece, curved tassets over the hip joints, a rear plate
    p = Part(pal)
    SA.limb(p, [(0.905, 0.10, 0.075, 0.075), (0.95, 0.14, 0.10, 0.10), (1.07, 0.15, 0.11, 0.11)], 'jet2', n=8, e=2.6)
    SA.limb(p, [(1.065, 0.165, 0.122, 0.122), (1.075, 0.175, 0.132, 0.132), (1.125, 0.175, 0.132, 0.132), (1.135, 0.163, 0.12, 0.12)],
            'jet3', n=10, e=3.0)                                                                           # belt
    SA.shell(p, [(0.905, 0.05, 0.125, 0.012), (0.925, 0.07, 0.142, 0.02), (1.03, 0.12, 0.152, 0.022), (1.065, 0.12, 0.146, 0.014)],
             -132, -48, 'jet', k=3)                                                                        # codpiece
    SA.sweep(p, *SA.se_path(0.1, 0.148, (-112, -101, -90, -79, -68), 0.99), 0.008, 0.005, 'ink', off=-0.001)   # panel line
    for s in (-1, 1):
        a0 = -50 if s > 0 else 130
        SA.shell(p, [(0.855, 0.104, 0.122, 0.012, s * 0.13, -0.01), (0.875, 0.118, 0.136, 0.02, s * 0.13, -0.01),
                     (1.02, 0.104, 0.122, 0.02, s * 0.13, -0.01), (1.05, 0.092, 0.11, 0.012, s * 0.13, -0.01)], a0, a0 + 100, 'jet', k=3)   # tassets
    SA.shell(p, [(0.9, 0.11, 0.12, 0.012), (0.92, 0.13, 0.135, 0.02), (1.05, 0.13, 0.142, 0.02)], 52, 128, 'jet', k=3)   # rear plate
    hips = p.build('BOT_JET_Hips', bevel=False)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_JET_HIP%d' % i, hips, (sx * J_HIPX, 0, J_HIP))
    socket('BOT_JET_WAIST', hips, (0, 0, J_WAIST))

    # ---- thigh (origin on the hip joint): servo ball, a tapered thigh under a wrap-around armour shell with a
    # layered front plate, the knee axle
    p = Part(pal)
    p.sphere((0, 0, 0), 0.085, 'gunmetal', seg=(8, 4))
    SA.limb(p, [(-0.45, 0.05, 0.055, 0.055), (-0.2, 0.074, 0.08, 0.084), (-0.04, 0.068, 0.074, 0.078)], 'jet2', n=10, e=2.2)
    SA.shell(p, [(-0.385, 0.072, 0.084, 0.012, 0, -0.008), (-0.36, 0.084, 0.098, 0.022, 0, -0.008), (-0.12, 0.094, 0.106, 0.022, 0, -0.012),
                 (-0.07, 0.086, 0.096, 0.014, 0, -0.012)], -165, -15, 'jet', k=5)
    SA.shell(p, [(-0.27, 0.094, 0.112, 0.016, 0, -0.012), (-0.14, 0.1, 0.12, 0.016, 0, -0.014)], -125, -55, 'jet3', k=3, cham=1.2)   # layered front plate
    p.cyl((-0.05, 0, -0.44), 0.045, 0.045, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0))
    p.build('BOT_JET_Thigh', bevel=False)

    # ---- shin + foot (origin on the knee): knee ball under a domed knee cop, a tapered calf, a curved shin guard,
    # calf piston, ankle, a sculpted boot
    p = Part(pal)
    p.sphere((0, 0, 0), 0.07, 'gunmetal', seg=(8, 4))
    SA.shell(p, [(-0.125, 0.06, 0.10, 0.012), (-0.10, 0.08, 0.128, 0.026), (0.03, 0.082, 0.13, 0.026), (0.07, 0.06, 0.108, 0.012)],
             -150, -30, 'jet3', k=3)                                                                        # knee cop
    SA.limb(p, [(-0.45, 0.042, 0.042, 0.048), (-0.26, 0.056, 0.053, 0.072, 0, 0.008), (-0.05, 0.056, 0.056, 0.06)], 'jet2', n=10, e=2.2)
    SA.shell(p, [(-0.425, 0.06, 0.07, 0.012, 0, -0.004), (-0.40, 0.07, 0.084, 0.022, 0, -0.004), (-0.19, 0.084, 0.1, 0.024, 0, -0.004),
                 (-0.145, 0.078, 0.092, 0.014, 0, -0.004)], -165, -15, 'jet', k=5)                         # shin guard
    SA.sweep(p, *SA.se_path(0.0787, 0.094, (-125, -107, -90, -73, -55), -0.27, cy=-0.004), 0.008, 0.005, 'ink', off=-0.001)
    p.limb((0, 0.06, -0.18), (0, 0.05, -0.40), 0.018, 0.018, 'steel', seg=6)                      # calf piston
    with SA.at_frame(p, SA.frame((0, 0.125, 0), (0, -1, 0))):
        rings = []
        for d, hw, z0, z1, r in ((0.0, 0.055, -0.535, -0.475, 0.02), (0.025, 0.074, -0.54, -0.44, 0.03), (0.17, 0.08, -0.54, -0.445, 0.032),
                                 (0.3, 0.068, -0.54, -0.49, 0.022), (0.335, 0.048, -0.536, -0.508, 0.01)):
            rings.append(SA.ring_rr(hw, (z1 - z0) / 2, r, 1, d, 0, (z0 + z1) / 2))
        SA.loft(p, rings, 'jet2')
    p.build('BOT_JET_Shin', bevel=False)

    # ---- torso (origin on the waist): a core with a curved, segmented abdomen, a sculpted chest with two curved pec
    # plates (the sternum seam glows in the groove between them), the gold reactor (weak point) on a round boss, a
    # collar, domed pauldrons with the element line along their lower edge, the sculpted jet back unit with round
    # nozzles and the pod-arm hinges
    sx_, sy_, sz_ = J_SHOULDER
    p = Part(pal)
    SA.limb(p, [(-0.06, 0.13, 0.12, 0.12), (0.2, 0.15, 0.125, 0.13)], 'jet2', n=10, e=2.3)
    for i, (z0, z1) in enumerate(((-0.025, 0.025), (0.04, 0.09), (0.105, 0.155))):
        a = 0.158 - 0.004 * i
        SA.shell(p, [(z0, a, 0.15, 0.02), (z1, a, 0.15, 0.02)], -155, -25, 'jet3' if i == 1 else 'jet', k=3, cham=1.0)   # abdomen plates
    SA.limb(p, [(0.15, 0.17, 0.15, 0.15), (0.185, 0.205, 0.172, 0.17), (0.30, 0.235, 0.178, 0.18), (0.45, 0.232, 0.176, 0.18),
                (0.53, 0.20, 0.15, 0.16), (0.565, 0.14, 0.10, 0.12)], 'jet', n=14, e=2.6)                 # chest
    for s in (-1, 1):
        a0 = -82 if s > 0 else -158
        SA.shell(p, [(0.30, 0.23, 0.188, 0.014), (0.325, 0.248, 0.208, 0.03), (0.465, 0.245, 0.206, 0.03), (0.51, 0.22, 0.182, 0.014)],
                 a0, a0 + 60, 'jet3', k=3)                                                                  # pec plates
    with SA.at_frame(p, SA.frame((0, -0.15, 0.255), (0, -1, 0))):
        SA.lathe_r(p, [(0.072, 0.0), (0.078, 0.03), (0.066, 0.048)], 'jet2', seg=10)                    # reactor boss
    p.cyl((0, -0.196, 0.255), 0.05, 0.05, 0.03, 'core', seg=12, rot=(90, 0, 0))
    p.cyl((0, -0.194, 0.255), 0.06, 0.06, 0.008, 'gunmetal', seg=12, rot=(90, 0, 0), caps=False, deco=True)
    SA.limb(p, [(0.5, 0.11, 0.11, 0.11), (0.6, 0.10, 0.10, 0.10)], 'jet3', n=10, e=2.0)                   # collar
    p.cyl((0, 0, 0.555), 0.114, 0.114, 0.016, 'gunmetal', seg=12, caps=False, deco=True)
    for s in (-1, 1):
        # pauldron: a domed shell, its lower edge carrying the shoulder line (element colour)
        p.parent = Matrix.Translation((s * sx_, sy_, sz_)) @ Matrix.Rotation(math.radians(-s * 12), 4, 'Y')
        cx = s * 0.012
        st = [(-0.075, 0.115, 0.14, 0.14, cx), (-0.05, 0.13, 0.155, 0.155, cx), (0.06, 0.125, 0.15, 0.15, cx), (0.125, 0.10, 0.12, 0.12, cx * 0.5),
              (0.16, 0.055, 0.07, 0.07, 0)]
        N = 10
        SA.limb(p, st, 'jet', n=N, e=2.5)
        z, a, bf, bb, c = st[1]
        ks = [k for k in range(N) if math.cos(2 * math.pi * k / N) * s > -0.6]
        ks = sorted(ks, key=lambda k: (2 * math.pi * k / N - (math.pi if s < 0 else 0) + math.pi) % (2 * math.pi))
        pts, nrm = [], []
        for k in ks:
            q, n = SA.se_point(a, bf, bb, 2.5, 2 * math.pi * k / N, c, 0)
            pts.append((q.x, q.y, z)); nrm.append((n.x, n.y, 0.0))
        SA.sweep(p, pts, nrm, 0.012, 0.005, 'plate', off=-0.001)                                    # shoulder line
        p.parent = Matrix.Identity(4)
    # back unit: a sculpted pack, a lighter back panel with vents, round nozzles, the pod-arm hinges
    SA.limb(p, [(0.10, 0.14, 0.06, 0.06, 0, 0.255), (0.13, 0.17, 0.074, 0.074, 0, 0.255), (0.40, 0.215, 0.084, 0.084, 0, 0.255),
                (0.48, 0.2, 0.08, 0.08, 0, 0.255), (0.51, 0.168, 0.064, 0.064, 0, 0.255)], 'jet', n=14, e=3.0)
    with SA.at_frame(p, SA.frame((0, 0.325, 0), (0, 1, 0))):
        SA.loft(p, [SA.ring_rr(0.13, 0.11, 0.03, 1, 0.0, 0, 0.33), SA.ring_rr(0.13, 0.11, 0.03, 1, 0.012, 0, 0.33),
                    SA.ring_rr(0.118, 0.098, 0.022, 1, 0.02, 0, 0.33)], 'jet3')
    for z in (0.27, 0.31, 0.35):
        p.box((0, 0.345, z), (0.18, 0.008, 0.012), 'ink', deco=True)                                        # vent slats
    for s in (-1, 1):
        nx, ny, nz = J_NOZ
        with SA.at_frame(p, Matrix.Translation((s * nx, ny, 0))):
            SA.lathe_r(p, [(0.062, 0.03), (0.05, 0.075), (0.066, 0.21)], 'gunmetal', seg=10)                # nozzle
            SA.lathe_r(p, [(0.0575, 0.112), (0.0575, 0.126)], 'jet3', seg=10, deco=True)                      # nozzle band
        ax, ay, az = J_ARM
        p.box((s * ax, 0.25, az + 0.0096), (0.12, 0.10, 0.008), 'ink', deco=True)                           # arm slot
        p.box((s * ax, ay - 0.006, az + 0.012), (0.09, 0.05, 0.02), 'gunmetal')                           # hinge block
    torso = p.build('BOT_JET_Torso', bevel=False)
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
        p.box((0, -0.138, z), (0.10, 0.01, 0.008), 'light')
    p.box((0, -0.19, 0.405), (0.014, 0.012, 0.12), 'light')
    for s in (-1, 1):
        nx, ny, nz = J_NOZ
        p.cyl((s * nx, ny, nz - 0.006), 0.042, 0.042, 0.004, 'light', seg=12)                      # nozzle cores
    strip_hull(p.build('BOT_JET_Seam', bevel=False, hull=0.003))

    # ---- head (origin on the neck): a sculpted helmet, no face: a smooth shell, a low crest, a dark curved visor
    # band carrying the one sensor slit, rounded ear modules, an antenna
    p = Part(pal)
    SA.limb(p, [(-0.05, 0.065, 0.065, 0.065), (0.05, 0.07, 0.07, 0.07)], 'jet3', n=10, e=2.0)
    p.cyl((0, 0, -0.02), 0.075, 0.075, 0.02, 'gunmetal', seg=10, caps=False, deco=True)
    SA.limb(p, [(0.005, 0.078, 0.122, 0.085, 0, 0.0), (0.04, 0.104, 0.148, 0.128), (0.13, 0.118, 0.152, 0.145), (0.205, 0.11, 0.142, 0.138),
                (0.25, 0.08, 0.10, 0.11), (0.275, 0.035, 0.045, 0.055)], 'jet', n=14, e=2.4)
    VA, VB = 0.1225, 0.1595                                                                                  # visor outline (hugs the shell)
    SA.shell(p, [(0.08, VA - 0.008, VB - 0.008, 0.01), (0.09, VA, VB, 0.02), (0.16, VA, VB, 0.02), (0.17, VA - 0.008, VB - 0.008, 0.01)],
             -150, -30, 'jet2', k=6, cham=0.8, e=2.4)                                                       # visor band
    SA.sweep(p, *SA.se_path(VA, VB, range(-120, -59, 10), 0.125, e=2.4), 0.022, 0.0045, 'ink', off=-0.001)   # the sensor slit
    with SA.at_frame(p, SA.frame((0, -0.01, 0.235), (0, 1, 0))):                                           # crest
        SA.loft(p, [SA.ring_rr(0.016, 0.02, 0.012, 1, -0.10, 0, 0.0), SA.ring_rr(0.022, 0.035, 0.016, 1, -0.07, 0, 0.022),
                    SA.ring_rr(0.022, 0.035, 0.016, 1, 0.07, 0, 0.022), SA.ring_rr(0.016, 0.022, 0.012, 1, 0.12, 0, -0.01)], 'jet3')
    for s in (-1, 1):
        with SA.at_frame(p, SA.frame((s * 0.1, -0.01, 0.12), (s, 0, 0))):
            SA.lathe_r(p, [(0.045, 0.0), (0.045, 0.026), (0.032, 0.045)], 'jet3', seg=10)                   # ear modules
    p.cyl((0.075, 0.09, 0.2), 0.008, 0.008, 0.15, 'ink', seg=4)
    p.sphere((0.075, 0.09, 0.355), 0.013, 'gunmetal', seg=(6, 4), deco=True)
    head = p.build('BOT_JET_Head', bevel=False)
    socket('BOT_JET_SLIT', head, (0, -0.168, 0.125))
    # the slit light: a bar curved along the visor, 6 mm proud of the slit (origin = BOT_JET_SLIT)
    p = Part(pal)
    with SA.at_frame(p, Matrix.Translation((0, 0.168, -0.125))):
        SA.sweep(p, *SA.se_path(VA, VB, range(-114, -65, 12), 0.125, e=2.4), 0.012, 0.004, 'light', off=0.0045, deco=False)
    p.build('BOT_JET_Light', bevel=False, hull=0.004)

    # ---- arms (origin on the shoulder); the right one carries the bullet launcher, held low, barrels along -Y
    p = Part(pal)
    _jet_arm(p, J_HAND_R, (0.2, 1.0, -0.3), 0.30, 0.32, -1)
    hx, hy, hz = J_HAND_R
    with SA.at_frame(p, Matrix.Translation((hx, hy, hz - 0.045))):
        SA.slab(p, 0.045, 0.045, 0.09, 0.02, 0.012, 'jet2', nc=1)                                          # fist
    with SA.at_frame(p, SA.frame((hx, hy + 0.10, hz + 0.065), (0, -1, 0))):                                # receiver
        SA.loft(p, [SA.ring_rr(0.042, 0.047, 0.022, 2, 0.0), SA.ring_rr(0.05, 0.055, 0.03, 2, 0.014), SA.ring_rr(0.05, 0.055, 0.03, 2, 0.39),
                    SA.ring_rr(0.044, 0.048, 0.024, 2, 0.40)], 'gunmetal')
    p.box((hx, hy - 0.10, hz + 0.126), (0.036, 0.30, 0.012), 'jet3')                                      # top rail
    for k in range(2):
        p.box((hx, hy - 0.16 + 0.1 * k, hz + 0.1355), (0.046, 0.012, 0.008), 'ink', deco=True)
    with SA.at_frame(p, Matrix.Translation((hx, hy - 0.17, hz - 0.12)) @ Matrix.Rotation(math.radians(-12), 4, 'X')):
        p.box((0, 0, 0.07), (0.06, 0.09, 0.14), 'jet2')                                                     # magazine
    with SA.at_frame(p, SA.frame((hx, hy - 0.29, hz + 0.07), (0, -1, 0))):                                 # barrel shroud
        SA.limb(p, [(0.0, 0.04, 0.04, 0.04), (0.012, 0.046, 0.046, 0.046), (0.205, 0.044, 0.044, 0.044), (0.222, 0.036, 0.036, 0.036)],
                'jet', n=10, e=2.8)
    for k in range(2):
        for s in (-1, 1):
            p.box((hx + s * 0.0455, hy - 0.36 - 0.06 * k, hz + 0.07), (0.008, 0.024, 0.044), 'ink', deco=True)   # vents
    for sx in (-0.022, 0.022):
        p.cyl((hx + sx, hy - 0.50, hz + 0.07), 0.017, 0.017, 0.17, 'steel', seg=8, rot=(90, 0, 0))   # twin barrels
        p.cyl((hx + sx, hy - 0.655, hz + 0.07), 0.022, 0.022, 0.014, 'plate', seg=8, rot=(90, 0, 0), caps=False, deco=True)   # cannon tips
    with SA.at_frame(p, SA.frame((hx, hy - 0.595, hz + 0.07), (0, -1, 0))):                                 # muzzle brake
        SA.limb(p, [(0.0, 0.05, 0.04, 0.04), (0.05, 0.048, 0.038, 0.038)], 'gunmetal', n=10, e=3.0)
    for s in (-1, 1):
        p.box((hx + s * 0.05, hy - 0.62, hz + 0.07), (0.008, 0.026, 0.036), 'ink', deco=True)
    ar = p.build('BOT_JET_ArmR', bevel=False)
    socket('BOT_JET_MUZZLE', ar, (hx, hy - 0.69, hz + 0.07))

    p = Part(pal)
    _jet_arm(p, J_HAND_L, (-0.2, 1.0, -0.3), 0.31, 0.31, 1)
    hx, hy, hz = J_HAND_L
    with SA.at_frame(p, Matrix.Translation((hx, hy, hz - 0.03))):
        SA.slab(p, 0.0425, 0.05, 0.08, 0.02, 0.012, 'jet2', nc=1)                                           # hand
    for x in (-0.025, 0.0, 0.025):
        p.limb((hx + x, hy - 0.042, hz - 0.025), (hx + x, hy - 0.05, hz - 0.095), 0.011, 0.008, 'gunmetal', seg=6)   # claw fingers
    p.limb((hx + 0.04, hy - 0.01, hz - 0.005), (hx + 0.055, hy - 0.02, hz - 0.06), 0.012, 0.009, 'gunmetal', seg=6)   # thumb
    p.build('BOT_JET_ArmL', bevel=False)

    # ---- pod arm (origin = its hinge on the back unit): a telescoping strut that raises the pod (the game stretches
    # it along its length while the pod rises), a piston, a round bracket at the top (socket BOT_JET_PODTOP)
    p = Part(pal)
    p.cyl((-0.035, 0, 0), 0.028, 0.028, 0.07, 'gunmetal', seg=8, rot=(0, 90, 0))
    SA.limb(p, [(0.0, 0.03, 0.026, 0.026), (0.2, 0.024, 0.02, 0.02)], 'jet3', n=8, e=2.4)
    p.cyl((0, 0, 0.19), 0.016, 0.016, 0.06, 'steel', seg=8)
    p.limb((0, 0.03, 0.02), (0, 0.03, 0.20), 0.011, 0.011, 'steel', seg=6)
    p.cyl((-0.04, 0, 0.255), 0.026, 0.026, 0.08, 'gunmetal', seg=8, rot=(0, 90, 0))
    arm = p.build('BOT_JET_PodArm', bevel=False, hull=0.008)
    socket('BOT_JET_PODTOP', arm, (0, 0, J_ARM_LEN))

    # ---- rocket pod (origin = its mount on the arm): a rounded launcher body with chamfered ends, a layered top
    # plate, three round launcher barrels along -Y (element-colour rims, rocket tips inside); the lid hinges on the top
    # front edge
    p = Part(pal)
    with SA.at_frame(p, SA.frame((0, 0.10, 0), (0, -1, 0))):
        SA.loft(p, [SA.ring_rr(0.088, 0.068, 0.04, 3, 0.0, 0, 0.10), SA.ring_rr(0.11, 0.09, 0.058, 3, 0.022, 0, 0.10),
                    SA.ring_rr(0.11, 0.09, 0.058, 3, 0.318, 0, 0.10), SA.ring_rr(0.096, 0.076, 0.046, 3, 0.338, 0, 0.10)], 'jet2')
        SA.loft(p, [SA.ring_rr(0.08, 0.012, 0.01, 1, 0.04, 0, 0.19), SA.ring_rr(0.08, 0.012, 0.01, 1, 0.28, 0, 0.19)], 'jet')   # top plate
    for x in (-0.045, 0.045):
        p.cyl((x, 0.096, 0.10), 0.03, 0.03, 0.01, 'ink', seg=8, rot=(-90, 0, 0), deco=True)                  # rear exhaust ports
    for x in (-0.068, 0.0, 0.068):
        p.cyl((x, -0.235, 0.10), 0.032, 0.032, 0.026, 'jet3', seg=10, rot=(90, 0, 0))                     # launcher barrel
        p.cyl((x, -0.25, 0.10), 0.036, 0.036, 0.016, 'plate', seg=10, rot=(90, 0, 0), caps=False, deco=True)   # rim
        p.cyl((x, -0.2615, 0.10), 0.024, 0.024, 0.004, 'ink', seg=8, rot=(90, 0, 0), deco=True)      # bore
        p.cyl((x, -0.252, 0.10), 0.017, 0.0, 0.02, 'red', seg=8, rot=(90, 0, 0), deco=True)         # rocket tip
    p.box((0, 0.0, 0.0), (0.08, 0.06, 0.03), 'gunmetal')                                         # mount
    pod = p.build('BOT_JET_Pod', bevel=False)
    socket('BOT_JET_LID', pod, (0, -0.28, 0.19))
    for k, x in enumerate((-0.068, 0.0, 0.068)):
        socket('BOT_JET_TUBE%d' % k, pod, (x, -0.30, 0.10))
    # lid (origin = hinge): a rounded plate with a bevelled outer face, a raised centre rib, its inner edge in the
    # element colour
    p = Part(pal)
    with SA.at_frame(p, SA.frame((0, -0.002, 0), (0, -1, 0))):
        SA.loft(p, [SA.ring_rr(0.115, 0.09, 0.038, 2, 0.0, 0, -0.09), SA.ring_rr(0.115, 0.09, 0.038, 2, 0.012, 0, -0.09),
                    SA.ring_rr(0.105, 0.08, 0.03, 2, 0.02, 0, -0.09)], 'jet')
    SA.sweep(p, [(0, -0.022, z) for z in (-0.03, -0.09, -0.15)], [(0, -1, 0)] * 3, 0.03, 0.005, 'jet3', off=-0.001)
    with SA.at_frame(p, SA.frame((0, -0.002, 0), (0, 1, 0))):
        SA.ring_band(p, [(q[0], q[1], 0.0) for q in SA.ring_rr(0.098, 0.074, 0.026, 1, 0.0, 0, -0.09)], lambda q: (0, 0, 1), 0.01, 0.004, 'plate',
                     off=0.0)
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
