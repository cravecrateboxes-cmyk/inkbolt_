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
    import bot_shapes_ground as SG
    PH, SEG = -math.pi / 16, 16       # 16-sided shell, facet centres every 22.5 deg (facet 12 = front -Y, 4 = back)
    R = 0.326                         # shell radius on its straight part
    PROF = [(0.0, 0.30), (0.27, 0.30), (0.316, 0.322), (R, 0.375), (0.334, 0.505), (R, 0.63), (0.302, 0.712), (0.0, 0.716)]
    rz = lambda z: next(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]) for a, b in zip(PROF[2:], PROF[3:]) if z <= b[1])
    fr = lambda k, z, r=None: ED.facet_frame(k, SEG, r or rz(z), z, phase=PH)
    p = Part(pal)
    # sculpted can: rounded base, straight corrugated wall, rolled shoulder under a domed rim; gold core dome on top
    p.lathe(PROF, 'tin', seg=SEG, phase=PH)
    p.lathe([(0.0, 0.712), (0.342, 0.716), (0.354, 0.742), (0.33, 0.77), (0.0, 0.79)], 'trim', seg=SEG, phase=PH)
    p.sphere((0, 0, 0.77), 0.14, 'core', seg=(12, 5), scale=(1, 1, 0.6))
    p.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=6)                          # whip antenna (light)
    SG.arc_plate(p, 0.30, 0.352, 0.565, 0.635, 238, 302, 4, 'ink', c=0.012)                # wrap-around sensor visor
    # ---- deco: visor lens, brow and lip, webbing belt + pouches, corrugation ridge, base bead, core seat
    SG.arc_plate(p, 0.345, 0.357, 0.585, 0.615, 246, 294, 4, 'amber', deco=True)
    SG.arc_plate(p, 0.30, 0.37, 0.64, 0.656, 234, 306, 4, 'trim', c=0.006, deco=True)
    p.lathe([(0.338, 0.3725), (0.338, 0.4375)], 'trim', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.337, 0.577), (0.337, 0.593)], 'tin2', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.152, 0.763), (0.152, 0.79)], 'gunmetal', seg=SEG, deco=True)
    for k in (7, 1):                                                                     # rounded pouches on the belt
        with ED.at(p, fr(k, 0.405, 0.338)):
            SG.rbox(p, (0, -0.005, 0.025), (0.13, 0.12, 0.054), 'pouch', r=0.022, n=1, c=0.012, deco=True)
            p.box((0, 0.03, 0.056), (0.136, 0.05, 0.012), 'pouch', deco=True)
            ED.pad(p, 0, 0.012, 0.03, 0.024, 0.004, 'steel', base=0.062)
    # hip mounts with pivot pins, rim bolts, lid hinge and latch
    for k in (10, 14, 2, 6):
        with ED.at(p, fr(k, 0.35, 0.321)):
            SG.rbox(p, (0, 0, 0.02), (0.08, 0.07, 0.05), 'trim', r=0.018, n=1, deco=True)
        a = math.radians(22.5 * k)
        u, t = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        c = u * 0.345 + Vector((0, 0, 0.33))
        p.limb(tuple(c - t * 0.05), tuple(c + t * 0.05), 0.02, 0.02, 'steel', seg=8, caps=False, deco=True)
    ED.bolt_ring(p, 0, 0, 0.772, 0.30, 8, r=0.012, h=0.007, phase=0.2, seg=5)
    for x in (-0.07, 0.07):
        p.limb((x - 0.03, 0.366, 0.745), (x + 0.03, 0.366, 0.745), 0.016, 0.016, 'gunmetal', seg=6, deco=True)
    SG.rbox(p, (0, -0.351, 0.735), (0.07, 0.02, 0.04), 'steel', r=0.008, n=1, deco=True)
    p.box((0, -0.364, 0.72), (0.03, 0.012, 0.05), 'gunmetal', deco=True)
    # back vent and battery box, side armour (curved, bolted), front plate, hazard stencil, serial plate, rivets
    with ED.at(p, ED.slope_frame(4, SEG, (R, 0.63), (0.302, 0.712), 0.43, phase=PH)):
        ED.grille(p, 0, 0, 0.12, 0.06, 3, slat='tin2')
    with ED.at(p, fr(4, 0.528)):
        ED.pad(p, 0, 0, 0.12, 0.08, 0.03, 'trim')
    for a in (45, 135, 180, 270):
        w = 18 if a == 270 else 16
        z0, z1 = (0.47, 0.54) if a == 270 else (0.49, 0.566)
        SG.arc_plate(p, 0.322, 0.346, z0, z1, a - w, a + w, 2, 'tin3', c=0.006, deco=True)
        for da in ((-w / 2, w / 2) if a == 270 else ()):
            q = math.radians(a + da)
            n = Vector((math.cos(q), math.sin(q), 0))
            ap = 0.346 * math.cos(math.radians(w / 2)) - 0.0005
            with ED.at(p, ED.axis_frame(tuple(n * ap + Vector((0, 0, (z0 + z1) / 2))), tuple(n))):
                ED.bolts(p, [(0, -0.022), (0, 0.022)] if a != 270 else [(0, 0)], r=0.009, top=0.004, color='tin2', seg=6)
    with ED.at(p, fr(10, 0.525)):
        ED.chevrons(p, 0, 0, 0.10, 0.05, 4)
    with ED.at(p, fr(15, 0.53)):
        ED.serial_plate(p, 0, 0, 0.08, 0.035)
    p.cyl((0.12, 0.08, 0.765), 0.03, 0.03, 0.03, 'gunmetal', seg=8, deco=True)            # antenna collar, lamp holder
    p.cyl((0.12, 0.08, 0.995), 0.028, 0.028, 0.035, 'gunmetal', seg=8, deco=True)
    p.cyl((-0.15, 0.09, 0.755), 0.014, 0.014, 0.13, 'ink', seg=6, deco=True)             # stub antenna, ball tip
    p.sphere((-0.15, 0.09, 0.895), 0.022, 'trim', seg=(5, 3), deco=True)
    body = p.build('BOT_CRAWLER_Body')
    socket('BOT_CRAWLER_CORE', body, (0, 0, 0.82))
    for i, (x, y) in enumerate([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]):
        socket('BOT_CRAWLER_HIP%d' % i, body, (x, y, 0.33))
    # leg: ball hip joint, tapered strut inside a coil spring, domed foot
    p = Part(pal)
    p.sphere((0, 0, 0), 0.042, 'trim', seg=(6, 4), deco=True)
    SG.tlimb(p, (0, 0, -0.01), (0, 0, -0.315), 0.03, 0.018, 'gunmetal', seg=8)
    for i in range(3):
        with ED.at(p, Matrix.Translation((0, 0, -0.07 - i * 0.075)) @ Matrix.Rotation(math.radians(12 if i % 2 else -12), 4, 'X')):
            p.cyl((0, 0, -0.011), 0.05, 0.05, 0.022, 'spring', seg=8, caps=False, deco=True)
    p.lathe([(0.0, -0.355), (0.088, -0.355), (0.095, -0.34), (0.066, -0.314), (0.0, -0.30)], 'gunmetal', seg=8)
    p.build('BOT_CRAWLER_Leg', bevel=False, hull=0.01)
    p = Part(pal)
    p.sphere((0, 0, 0), 0.05, 'light', seg=(6, 4))
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
    import bot_shapes_ground as SG
    P_ = G_PROF
    p = Part(pal)
    # hull: sculpted core (filleted profile, chamfered sides), side armour sponsons (stepped out), glacis cheek plates
    SG.sprism2(p, P_, -G_HW, G_HW, 'bin', c=0.035, r=[0.0, 0.0, 0.0, 0.06, 0.10, 0.11, 0.05, 0.04], n=1)
    SG.sprism2(p, [(-0.207, 0.068), (0.249, 0.068), (0.354, 0.33), (-0.333, 0.33)], -G_HW - 0.01, G_HW + 0.01, 'gunmetal',
               c=0.02)                                                                    # dark chassis
    spon = [(-0.300, 0.33), (0.190, 0.33), (0.240, 0.42), (0.240, 0.83), (-0.255, 0.86), (-0.320, 0.60)]
    for sx in (-1, 1):                                                                     # flared 7 deg: wider at the shoulder
        p.parent = Matrix.Translation((sx * 0.25, 0, 0.33)) @ Matrix.Rotation(math.radians(7 * sx), 4, 'Y') @ Matrix.Translation((-sx * 0.25, 0, -0.33))
        SG.sprism2(p, spon, sx * 0.225, sx * 0.300, 'bin2', c=(0, 0.016), r=[0.0, 0.04, 0.04, 0.08, 0.08, 0.06], n=1)
        p.box((sx * 0.301, -0.04, 0.47), (0.008, 0.28, 0.03), 'ink', deco=True)          # vision cut + amber tick
        p.box((sx * 0.301, -0.04, 0.52), (0.008, 0.28, 0.015), 'amber', deco=True)
        for y in (-0.20, 0.10):
            p.cyl((sx * 0.296, y, 0.40), 0.016, 0.016, 0.008, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
    p.parent = Matrix.Identity(4)
    # rear power pack (carries the antenna) and the round drive axle housing
    pack = [(0.300, 0.56), (0.470, 0.60), (0.500, 0.70), (0.470, 0.925), (0.300, 0.925)]
    SG.sprism2(p, pack, -0.27, 0.27, 'gunmetal', c=0.025, r=[0.0, 0.04, 0.05, 0.07, 0.0], n=1)
    p.cyl((-0.28, 0.30, 0.125), 0.05, 0.05, 0.56, 'gunmetal', seg=10, rot=(0, 90, 0))
    # core: gold battery lying along X (the gun's trunnion), in an armoured cradle
    px, py, pz = G_PIVOT
    p.cyl((-0.17, py, pz), 0.075, 0.075, 0.34, 'core', seg=12, rot=(0, 90, 0))
    for sx in (-1, 1):
        SG.sprism2(p, [(-0.300, 0.73), (py, 0.745), (py - 0.03, 0.80), (-0.29, 0.86)], sx * 0.185, sx * 0.235, 'gunmetal',
                   r=[0.0, 0.02, 0.02, 0.0], n=1)
        # front claw skids
        SG.sprism2(p, [(-0.30, 0.0), (-0.12, 0.0), (-0.10, 0.06), (-0.22, 0.14), (-0.33, 0.04)], sx * 0.12, sx * 0.22, 'gunmetal',
                   r=[0.0, 0.0, 0.0, 0.03, 0.03], n=1)
    # 4-cell rocket pod on the right shoulder: a rounded launcher box
    pod = [(-0.27, 0.70), (0.13, 0.70), (0.16, 0.78), (0.13, 0.86), (-0.27, 0.86)]
    SG.sprism2(p, pod, 0.315, 0.440, 'gunmetal', c=(0, 0.018), r=[0.0, 0.04, 0.04, 0.04, 0.035], n=1)
    lx, ly, lz = G_LIGHT
    p.cyl((lx, ly, 0.935), 0.012, 0.012, lz - 0.935 - 0.04, 'ink', seg=6)                    # antenna whip
    # ---- deco
    hazard(p, on_edge(P_, 7, 0.55, 0.009), 0.38, 0.15)                                # lower glacis chevrons
    p.parent = on_edge(P_, 6, 0.5, 0.0)                                                   # bolted chest plate + intake slits
    SG.rbox(p, (0, 0, 0.004), (0.36, 0.23, 0.010), 'bin2', r=0.03, n=2, deco=True)
    for x in (-0.06, 0.0, 0.06):
        p.box((x, 0.0, 0.0105), (0.022, 0.15, 0.006), 'ink', deco=True)
    for x in (-0.15, 0.15):
        for y in (-0.085, 0.085):
            p.cyl((x, y, 0.006), 0.014, 0.014, 0.008, 'steel', seg=4, deco=True)
    p.parent = Matrix.Identity(4)
    for sx in (-1, 1):                                                                     # battery clamp bands
        p.cyl((sx * 0.13 - 0.02, py, pz), 0.081, 0.081, 0.04, 'core2', seg=12, rot=(0, 90, 0), caps=False, deco=True)
    p.cyl((0.165, py, pz), 0.03, 0.03, 0.03, 'steel', seg=8, rot=(0, 90, 0), deco=True)   # + terminal
    for i in range(4):                                                                    # rocket pod tubes + red tips
        y0, z0 = -0.27, (0.745, 0.815)[i % 2]
        x0 = (0.407, 0.348)[i // 2]
        p.cyl((x0, y0 + 0.004, z0), 0.024, 0.024, 0.012, 'ink', seg=6, rot=(90, 0, 0), deco=True)
        p.cyl((x0, y0 - 0.004, z0), 0.012, 0.006, 0.014, 'red', seg=4, rot=(90, 0, 0), deco=True)
    p.box((0.443, -0.05, 0.78), (0.008, 0.20, 0.035), 'amber', deco=True)
    for t in (0.2, 0.4, 0.6, 0.8):                                                        # power pack cooling slats
        p.parent = on_edge(pack, 2, t, 0.0)
        p.box((0, 0, 0.0015), (0.40, 0.018, 0.006), 'ink', deco=True)
    p.parent = Matrix.Identity(4)
    p.box((0, 0.347, 0.45), (0.38, 0.008, 0.10), 'ink', deco=True)                       # rear hull vent
    p.cyl((lx, ly, 0.92), 0.03, 0.022, 0.035, 'steel', seg=6, deco=True)                  # antenna base
    p.box((0, -0.02, 0.962), (0.40, 0.44, 0.006), 'ink', deco=True)                       # dark bay (shows when the cowl lifts)
    # detail pass: twin lamps on the chest plate, serial plates and rivet rows on the sponsons, exhaust stubs and
    # a grab rail on the power pack, skid bolts, pod rivets, hinge brackets, tow hook, battery cables in the bay
    with ED.at(p, on_edge(P_, 6, 0.5, 0.0)):
        for x in (-0.11, 0.11):
            ED.lamp(p, x, 0.0, 0.02, lens='sticker', w=0.006, base=0.009, seg=6)
    for sx in (-1, 1):
        p.parent = Matrix.Translation((sx * 0.25, 0, 0.33)) @ Matrix.Rotation(math.radians(7 * sx), 4, 'Y') @ Matrix.Translation((-sx * 0.25, 0, -0.33))
        p.box((sx * 0.3015, 0.12, 0.62), (0.007, 0.10, 0.06), 'sticker', deco=True)
        for z, w in ((0.632, 0.07), (0.608, 0.045)):
            p.box((sx * 0.3055, 0.115, z), (0.006, w, 0.01), 'ink', deco=True)
    p.parent = Matrix.Identity(4)
    for x in (-0.17, 0.17):
        p.cyl((x, 0.40, 0.92), 0.026, 0.026, 0.05, 'gunmetal', seg=6, deco=True)
        p.cyl((x, 0.40, 0.967), 0.015, 0.015, 0.006, 'ink', seg=6, deco=True)
    for sx in (-1, 1):
        for y in (-0.25, -0.17):
            p.cyl((sx * 0.217, y, 0.03), 0.011, 0.011, 0.008, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
        p.cyl((0.437, -0.20 + 0.10 * (sx + 1), 0.73), 0.009, 0.009, 0.007, 'steel', seg=4, rot=(0, 90, 0), deco=True)
        p.box((sx * 0.20, 0.335, 0.965), (0.05, 0.04, 0.03), 'gunmetal', deco=True)
    SG.rbox(p, (0, 0.355, 0.20), (0.08, 0.03, 0.05), 'gunmetal', r=0.012, n=1, deco=True)
    p.box((0, 0.374, 0.195), (0.03, 0.03, 0.03), 'steel', deco=True)
    ED.cable(p, [(0.12, -0.36, 0.905), (0.12, -0.20, 0.968), (0.05, 0.10, 0.968)], 0.018, 'rubber')
    ED.cable(p, [(-0.12, -0.36, 0.905), (-0.12, -0.20, 0.972), (-0.05, 0.10, 0.972)], 0.018, 'red')
    body = p.build('BOT_GUNNER_Body')
    socket('BOT_GUNNER_CORE', body, (0, py, pz))
    socket('BOT_GUNNER_HINGE', body, G_HINGE)
    socket('BOT_GUNNER_GUNPIVOT', body, G_PIVOT)
    socket('BOT_GUNNER_LIGHT', body, G_LIGHT)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_GUNNER_WHEEL%d' % i, body, (sx * G_WHEEL[0], G_WHEEL[1], G_WHEEL[2]))

    # armoured cowl (origin on the hinge axis; extends toward -Y): a rounded wedge with a sloped brow and a hanging lip
    p = Part(pal)
    cowl = [(0.012, -0.020), (0.012, 0.045), (-0.07, 0.085), (-0.58, 0.085), (-0.735, 0.030), (-0.755, -0.035),
            (-0.705, -0.075), (-0.640, -0.020)]
    SG.sprism2(p, cowl, -0.315, 0.315, 'bin', c=0.035, r=[0.0, 0.0, 0.09, 0.07, 0.012, 0.012, 0.02, 0.0], n=1)
    SG.sprism2(p, [(-0.05, 0.07), (-0.56, 0.07), (-0.50, 0.115), (-0.10, 0.115)], -0.17, 0.17, 'bin2', c=0.014,
               r=[0.0, 0.0, 0.03, 0.03], n=1)                                               # raised spine plate
    p.parent = on_edge(cowl, 3, 0.5, 0.0)                                                 # brow: sensor slit
    SG.rbox(p, (0, 0, 0.004), (0.46, 0.05, 0.008), 'ink', r=0.02, n=1, deco=True)
    SG.rbox(p, (0, 0, 0.010), (0.36, 0.018, 0.006), 'amber', r=0.008, n=1, deco=True)
    p.parent = Matrix.Identity(4)
    hazard(p, on_edge(cowl, 4, 0.5, 0.0), 0.48, 0.040, n=5)                                 # lip hazard band
    for sx in (-1, 1):
        p.cyl((sx * 0.30 - 0.05, 0, 0.0), 0.028, 0.028, 0.10, 'gunmetal', seg=8, rot=(0, 90, 0), deco=True)  # knuckles
        for y in (-0.15, -0.45):
            p.cyl((sx * 0.25, y, 0.081), 0.014, 0.014, 0.008, 'steel', seg=5, deco=True)  # bolts
    # detail pass: panel seams across the cowl, a grab handle on the spine, spine bolts
    for sx in (-1, 1):
        for y in (-0.30, -0.60):
            p.box((sx * 0.225, y, 0.086), (0.10, 0.012, 0.006), 'ink', deco=True)
    p.limb((-0.05, -0.12, 0.112), (-0.05, -0.12, 0.137), 0.008, 0.008, 'steel', seg=6, deco=True)
    p.limb((0.05, -0.12, 0.112), (0.05, -0.12, 0.137), 0.008, 0.008, 'steel', seg=6, deco=True)
    p.limb((-0.07, -0.12, 0.137), (0.07, -0.12, 0.137), 0.009, 0.009, 'steel', seg=6, deco=True)
    for y in (-0.25, -0.40):
        for x in (-0.12, 0.12):
            p.cyl((x, y, 0.113), 0.01, 0.01, 0.006, 'steel', seg=5, deco=True)
    p.build('BOT_GUNNER_Lid')

    # twin autocannon (origin on the battery axis; barrels along -Y): round collar, rounded receiver and shroud
    p = Part(pal)
    p.cyl((-0.05, 0, 0), 0.092, 0.092, 0.10, 'gunmetal', seg=12, rot=(0, 90, 0))          # clamp collar
    SG.rbox(p, (0, -0.14, 0.01), (0.15, 0.14, 0.15), 'gunmetal', r=0.03, n=1, c=0.012, rot=(90, 0, 0))   # receiver
    SG.rbox(p, (0, -0.29, 0.0), (0.12, 0.07, 0.17), 'bin2', r=0.03, n=2, rot=(90, 0, 0))        # barrel shroud
    for sx in (-1, 1):
        p.cyl((sx * 0.032, -0.20, 0), 0.025, 0.025, 0.27, 'steel', seg=8, rot=(90, 0, 0), caps=False)  # barrels
        p.cyl((sx * 0.032, -0.445, 0), 0.031, 0.031, 0.06, 'gunmetal', seg=10, rot=(90, 0, 0))   # muzzle brakes
        p.cyl((sx * 0.032, -0.500, 0), 0.016, 0.016, 0.009, 'ink', seg=8, rot=(90, 0, 0), deco=True)  # bores
        p.box((sx * 0.062, -0.29, 0.0), (0.006, 0.11, 0.012), 'ink', deco=True)          # shroud cooling slots
    p.box((0, -0.29, 0.037), (0.05, 0.11, 0.006), 'ink', deco=True)
    p.box((0, -0.14, 0.087), (0.09, 0.05, 0.006), 'amber', deco=True)                     # receiver hazard band
    # detail pass: barrel cooling rings, side ammo drum with a feed chute, receiver bolts and top rail slots
    for sx in (-1, 1):
        for y in (-0.40,):
            p.cyl((sx * 0.032, y, 0), 0.030, 0.030, 0.014, 'gunmetal', seg=8, rot=(90, 0, 0), caps=False, deco=True)
        for y in (-0.085,):
            p.cyl((sx * 0.073, y, 0.035), 0.01, 0.01, 0.006, 'steel', seg=5, rot=(0, sx * 90, 0), deco=True)
    p.cyl((-0.073, -0.14, -0.02), 0.05, 0.05, 0.025, 'bin2', seg=10, rot=(0, -90, 0), deco=True)
    p.box((-0.085, -0.145, 0.034), (0.016, 0.04, 0.03), 'gunmetal', deco=True)
    for y in (-0.10, -0.18):
        p.box((0, y, 0.0865), (0.04, 0.012, 0.007), 'ink', deco=True)
    gun = p.build('BOT_GUNNER_Gun', bevel=False)
    socket('BOT_GUNNER_GUN', gun, (0, -0.51, 0))

    # wheel (origin on the axle; axis X; symmetric so the game mirrors it for the other side): a round tyre with
    # rolled shoulders, tread lugs, an armoured hub with an axle nut
    p = Part(pal)
    w = 0.075
    AX = Matrix.Rotation(math.radians(90), 4, 'Y')                                       # lathe axis Z -> X
    p.parent = AX
    p.lathe([(0.0, -w / 2), (0.108, -w / 2), (G_WHEEL_R, -0.02), (G_WHEEL_R, 0.02), (0.108, w / 2), (0.0, w / 2)], 'rubber', seg=12)
    p.parent = Matrix.Identity(4)
    p.cyl((-w / 2 - 0.005, 0, 0), 0.072, 0.072, w + 0.01, 'bin2', seg=10, rot=(0, 90, 0), deco=True)   # armoured hub
    p.cyl((-w / 2 - 0.012, 0, 0), 0.026, 0.026, w + 0.024, 'gunmetal', seg=8, rot=(0, 90, 0), deco=True)   # axle nut
    ap = G_WHEEL_R * math.cos(math.pi / 12)
    for j in range(6):
        b = math.radians(15 + 60 * j)
        r = ap + 0.005
        p.box((0, r * math.cos(b), r * math.sin(b)), (0.05, 0.03, 0.014), 'rubber', rot=(math.degrees(b) - 90, 0, 0), deco=True)
    for sx in (-1, 1):
        for j in range(3):
            b = math.pi / 2 + 2 * math.pi / 3 * j
            p.cyl((sx * 0.0405, 0.046 * math.cos(b), 0.046 * math.sin(b)), 0.009, 0.009, 0.007, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
    p.build('BOT_GUNNER_Wheel', bevel=False)

    p = Part(pal)
    p.sphere((0, 0, 0), 0.045, 'light', seg=(6, 4))
    p.build('BOT_GUNNER_Light', bevel=False, hull=0.008)


# ================================================================ BOMBER
# Fizzing bottle in a roller fork: blue bottle with a label and a strapped gold pressure canister (core),
# red crimp cap with a fuse wick (the cap pops and the wick sparks during the 0.6 s fuse).
B_AXLE = (0, 0, 0.13)
B_ROLLER_R = 0.13
B_CAP = (0, 0, 0.865)


def build_bomber(pal):
    import bot_shapes_ground as SG
    SEG, PH = 16, -math.pi / 16          # facet centres every 22.5 deg (facet 12 = front -Y)
    AX = Matrix.Translation(B_AXLE) @ Matrix.Rotation(math.radians(90), 4, 'Y')       # local Z -> world X, on the axle
    p = Part(pal)
    for sx in (-1, 1):                                                                  # rounded fork side plates
        SG.sprism2(p, SG.rrect(0.09, 0.21, 0.038, n=2, cy=0.20), sx * 0.247, sx * 0.277, 'gunmetal', c=(0.0, 0.008))
    SG.rbox(p, (0, 0, 0.285), (0.03, 0.11, 0.53), 'gunmetal', r=0.012, n=1, c=0.01, rot=(0, 90, 0))   # cross bar
    p.lathe([(0.0, 0.29), (0.236, 0.29), (0.236, 0.31), (0.226, 0.32), (0.0, 0.32)], 'alu', seg=12)   # cradle disc
    BOT = [(0.0, 0.316), (0.15, 0.316), (0.205, 0.333), (0.223, 0.368), (0.225, 0.62), (0.214, 0.662), (0.188, 0.703),
           (0.148, 0.74), (0.105, 0.771), (0.08, 0.792), (0.074, 0.81), (0.074, 0.87), (0.0, 0.87)]
    p.lathe(BOT, 'glass', seg=SEG, phase=PH)
    cy = -0.307                                                                          # core canister (one rounded can)
    p.parent = Matrix.Translation((0, cy, 0))
    p.lathe([(0.0, 0.36), (0.04, 0.36), (0.066, 0.39), (0.066, 0.58), (0.04, 0.61), (0.0, 0.61)], 'core', seg=10)
    p.parent = Matrix.Identity(4)
    # ---- deco: label, straps, neck ring + sensor strip, glints, hub caps, canister band + valve, roller housing
    p.lathe([(0.232, 0.43), (0.232, 0.55)], 'label', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.236, 0.456), (0.236, 0.47)], 'teal', seg=SEG, phase=PH, deco=True)
    for z in (0.405, 0.555):
        p.lathe([(0.24, z), (0.24, z + 0.022)], 'gunmetal', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.088, 0.795), (0.088, 0.812)], 'ink', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.082, 0.822), (0.082, 0.840)], 'amber', seg=SEG, phase=PH, deco=True)
    # comic highlight: one streak down the left-front of the shoulder and body
    p.on_slope(10, SEG, (0.214, 0.662), (0.188, 0.703), 0.5, 0.004, (0.03, 0.006, 0.042), 'paper', phase=PH)
    p.on_slope(10, SEG, (0.188, 0.703), (0.148, 0.74), 0.45, 0.004, (0.026, 0.006, 0.045), 'paper', phase=PH)
    p.on_facet(10, SEG, 0.225, 0.004, 0.596, (0.03, 0.006, 0.034), 'paper', phase=PH)
    for sx in (-1, 1):
        p.cyl((sx * 0.277, 0, 0.13), 0.045, 0.045, 0.014, 'alu', seg=10, rot=(0, sx * 90, 0), deco=True)
    p.cyl((0, cy, 0.465), 0.072, 0.072, 0.02, 'core2', seg=10, caps=False, deco=True)
    p.cyl((0, cy, 0.60), 0.016, 0.016, 0.04, 'gunmetal', seg=6, deco=True)
    # rounded roller housing over the drum (chamfered steel fender on the fork), fork bolts and slot, cradle bolts,
    # moulded flutes on the shoulder, a neck thread ring, a pressure gauge and a hose from the canister valve to the
    # neck, a second canister clamp, explosive diamonds and a barcode on the label
    SG.arc_plate(p, 0.150, 0.168, -0.20, 0.20, 105, 255, 8, 'steel', c=0.006, deco=True, frame=AX)
    for sx in (-1, 1):
        for y in (-0.025, 0.025):
            p.cyl((sx * 0.275, y, 0.27), 0.009, 0.009, 0.008, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
        p.box((sx * 0.2785, 0, 0.21), (0.007, 0.022, 0.05), 'ink', deco=True)
    ED.bolt_ring(p, 0, 0, 0.32, 0.218, 6, r=0.008, h=0.007, phase=math.pi / 6, seg=4)
    for k in range(1, SEG, 2):
        p.on_slope(k, SEG, (0.214, 0.662), (0.188, 0.703), 0.5, 0.003, (0.03, 0.006, 0.04), 'glass2', phase=PH)
    p.lathe([(0.081, 0.850), (0.081, 0.858)], 'glass2', seg=SEG, phase=PH, deco=True)
    p.cyl((0, cy, 0.525), 0.072, 0.072, 0.02, 'core2', seg=10, caps=False, deco=True)
    p.cyl((0, cy - 0.061, 0.43), 0.026, 0.026, 0.009, 'gunmetal', seg=8, rot=(90, 0, 0), deco=True)
    p.cyl((0, cy - 0.068, 0.43), 0.02, 0.02, 0.005, 'paper', seg=8, rot=(90, 0, 0), deco=True)
    ED.cable(p, [(0, cy, 0.632), (0, -0.25, 0.70), (0, -0.20, 0.735), (0, -0.12, 0.765)], 0.016, 'rubber')
    for k in (7, 15):
        with ED.at(p, ED.facet_frame(k, SEG, 0.232, 0.51, phase=PH)):
            ED.pad(p, 0, 0, 0.042, 0.042, 0.004, 'red', base=0.0, rot=45)
            ED.pad(p, 0, 0, 0.012, 0.012, 0.003, 'ink', base=0.004)
    with ED.at(p, ED.facet_frame(3, SEG, 0.232, 0.51, phase=PH)):
        for i, w in enumerate((0.004, 0.009, 0.005, 0.008)):
            ED.pad(p, -0.021 + 0.014 * i, 0, w, 0.04, 0.003, 'ink')
    body = p.build('BOT_BOMBER_Body', bevel=False)
    socket('BOT_BOMBER_CORE', body, (0, cy, 0.48))
    socket('BOT_BOMBER_AXLE', body, B_AXLE)
    socket('BOT_BOMBER_CAP', body, B_CAP)

    # roller drum (origin on the axle, axis X): rounded rubber drum with rolled ends, steel rings, tread lugs
    p = Part(pal)
    p.parent = Matrix.Rotation(math.radians(90), 4, 'Y')
    p.lathe([(0.0, -0.22), (0.115, -0.22), (B_ROLLER_R, -0.205), (B_ROLLER_R, 0.205), (0.115, 0.22), (0.0, 0.22)], 'rubber', seg=12)
    p.parent = Matrix.Identity(4)
    for x in (-0.12, 0.12):
        p.cyl((x - 0.012, 0, 0), B_ROLLER_R + 0.006, B_ROLLER_R + 0.006, 0.024, 'steel', seg=12, rot=(0, 90, 0),
              caps=False, deco=True)
    p.cyl((-0.228, 0, 0), 0.06, 0.06, 0.456, 'alu', seg=10, rot=(0, 90, 0), deco=True)    # end hubs (one through-rod)
    ap = B_ROLLER_R * math.cos(math.pi / 12)
    for j in range(6):
        b = math.radians(15 + 60 * j)
        for x, w in ((0.0, 0.18), (-0.172, 0.06), (0.172, 0.06)):
            r = ap + 0.004
            p.box((x, r * math.cos(b), r * math.sin(b)), (w, 0.028, 0.012), 'rubber', rot=(math.degrees(b) - 90, 0, 0), deco=True)
    for sx in (-1, 1):
        for j in range(4):
            b = math.pi / 4 + math.pi / 2 * j
            p.cyl((sx * 0.226, 0.034 * math.cos(b), 0.034 * math.sin(b)), 0.009, 0.009, 0.008, 'steel', seg=4, rot=(0, sx * 90, 0), deco=True)
    p.build('BOT_BOMBER_Roller', bevel=False)

    # crimp cap + fuse wick (origin on the neck top): a rounded cap over a crimped skirt, a round fuse cord
    p = Part(pal)
    p.lathe([(0.0, 0.0), (0.08, 0.0), (0.088, 0.008), (0.088, 0.04), (0.078, 0.05), (0.0, 0.052)], 'capred', seg=14)
    pts = [(0, 0, 0.06), (0.02, 0.005, 0.10), (0.006, -0.01, 0.14), (0.022, 0.0, 0.175)]
    for a, b in zip(pts, pts[1:]):
        p.limb(a, b, 0.009, 0.009, 'wick', seg=5)
    p.cyl((0, 0, -0.012), 0.095, 0.095, 0.02, 'capred', seg=14, caps=False, deco=True)   # crimp skirt
    p.cyl((0, 0, 0.046), 0.026, 0.02, 0.025, 'alu', seg=8, deco=True)                     # wick holder
    for k in range(0, 14, 2):
        p.on_facet(k, 14, 0.095, 0.0, -0.002, (0.014, 0.008, 0.018), 'red')                # crimp teeth
    p.cyl((0, 0, 0.056), 0.029, 0.029, 0.008, 'gunmetal', seg=8, caps=False, deco=True)
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
    import bot_shapes_air as SA
    SEG = 16
    p = Part(pal)
    p.lathe([(0.12, 0.02), (0.176, 0.045), (0.19, 0.075), (0.19, 0.50), (0.184, 0.527), (0.17, 0.552), (0.163, 0.575),
             (0.0, 0.575)], 'can', seg=SEG)
    p.lathe([(0.0, 0.02), (0.12, 0.02)], 'can2', seg=SEG)                               # bottom (seat of the dome)
    p.sphere((0, 0, 0.02), 0.11, 'core', seg=(12, 4), scale=(1, 1, 0.62))              # core dome
    p.box((0, D_PIVOT[1] + 0.01, 0.0), (0.05, 0.06, 0.05), 'gunmetal')                    # gun gimbal bracket
    p.band(0.18, 0.29, 0.195, 'paper', seg=SEG)                                           # white ribbon
    p.band(0.37, 0.43, 0.196, 'ink', seg=SEG)                                             # sensor slot (all round)
    p.band(0.388, 0.412, 0.2, 'amber', seg=SEG)                                           # sensor strip
    # detail pass: rolled top chime and bottom bead, a seam strip down the back, side vents, a can label with
    # stencil bars, two side cameras over the sensor slot, a gimbal yoke round the gun
    p.band(0.563, 0.572, 0.17, 'alu', seg=SEG)
    p.band(0.075, 0.09, 0.194, 'can2', seg=SEG)
    for z0, z1 in ((0.095, 0.175), (0.295, 0.365), (0.435, 0.495)):
        p.on_facet(3, SEG, 0.19, 0.0, (z0 + z1) / 2, (0.016, 0.007, z1 - z0), 'can2')
    for k in (0, 7):
        with ED.at(p, ED.facet_frame(k, SEG, 0.19, 0.33)):
            ED.grille(p, 0, 0, 0.06, 0.05, 3, slat='can2')
    with ED.at(p, ED.facet_frame(13, SEG, 0.19, 0.13)):
        ED.pad(p, 0, 0, 0.06, 0.07, 0.004, 'paper')
        ED.stencil(p, -0.004, 0.016, 0.04, 0.008, 3, base=0.004)
        ED.pad(p, -0.01, -0.004, 0.032, 0.006, 0.003, 'ink', base=0.004)
        ED.pad(p, -0.005, -0.018, 0.042, 0.006, 0.003, 'ink', base=0.004)
    for k in (15, 8):
        with ED.at(p, ED.facet_frame(k, SEG, 0.19, 0.465)):
            ED.pad(p, 0, 0, 0.04, 0.03, 0.012, 'gunmetal')
            ED.lamp(p, 0, 0, 0.009, lens='teal', w=0.004, base=0.012, seg=8)
    for sx in (-1, 1):
        p.box((sx * 0.048, D_PIVOT[1], -0.01), (0.012, 0.04, 0.06), 'gunmetal', deco=True)
    body = p.build('BOT_DRONE_Body', bevel=False)
    socket('BOT_DRONE_CORE', body, (0, 0, -0.01))
    socket('BOT_DRONE_LID', body, D_LID)
    socket('BOT_DRONE_GUNPIVOT', body, D_PIVOT)

    # lid (origin on the can top): a rounded disc, round tapered X arms, rounded motor pods inside round rotor
    # guards; deco: pull tab, telescoping post, antenna
    p = Part(pal)
    SA.lathe_r(p, [(0.172, 0.0), (0.172, 0.013), (0.158, 0.022), (0.0, 0.022)], 'alu', seg=12)
    pods = []
    for k in range(2):
        a = math.radians(45 + 90 * k)
        c, s = D_ARM * math.cos(a), D_ARM * math.sin(a)
        z = 0.03 + 0.006 * k                                                               # crossing arms at two heights
        p.limb((-c, -s, z), (c, s, z), 0.016, 0.016, 'gunmetal', seg=8)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = D_ARM * math.cos(a), D_ARM * math.sin(a)
        with SA.at_frame(p, Matrix.Translation((x, y, 0.0))):
            SA.lathe_r(p, [(0.047, 0.0), (0.047, 0.056), (0.03, 0.078)], 'can2', seg=10)                       # motor pod
        pods.append((x, y, 0.092))
    p.cyl((0, 0, -0.16), 0.03, 0.03, 0.16, 'gunmetal', seg=8, caps=False, deco=True)     # post (shows when lifted)
    p.box((0, -0.06, 0.026), (0.05, 0.085, 0.008), 'alu', deco=True)                        # pull tab
    p.cyl((0.0, 0.08, 0.022), 0.009, 0.009, 0.16, 'ink', seg=4, deco=True)               # antenna
    # detail pass: rotor guards (a round ring on two struts round each rotor disc), a cooling band and nav lamp on
    # each pod, bolts where the arms cross the lid, a lamp holder under the light
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = D_ARM * math.cos(a), D_ARM * math.sin(a)
        p.parent = Matrix.Translation((x, y, 0))
        p.lathe([(0.19, 0.093), (0.1955, 0.084), (0.201, 0.093), (0.1955, 0.102), (0.19, 0.093)], 'gunmetal', seg=12, deco=True)
        for da in (-50, 50):
            b = a + math.radians(180 + da)
            p.beam((0.04 * math.cos(b), 0.04 * math.sin(b), 0.05), (0.192 * math.cos(b), 0.192 * math.sin(b), 0.09), 0.012, 'gunmetal', deco=True)
        p.cyl((0, 0, 0.03), 0.0515, 0.0515, 0.01, 'gunmetal', seg=10, caps=False, deco=True)
        p.box((0.05 * math.cos(a), 0.05 * math.sin(a), 0.045), (0.012, 0.014, 0.012), 'red' if k in (1, 2) else 'teal', rot=(0, 0, math.degrees(a)), deco=True)
        p.parent = Matrix.Identity(4)
    ED.bolt_ring(p, 0, 0, 0.022, 0.135, 4, r=0.01, h=0.006, phase=0.0)
    p.cyl((0.0, 0.08, 0.145), 0.02, 0.02, 0.025, 'gunmetal', seg=8, deco=True)
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
    p.cyl((0, 0, -0.008), 0.022, 0.016, 0.022, 'gunmetal', seg=8, deco=True)                # hub cap
    p.build('BOT_DRONE_Rotor', bevel=False, hull=0.008)

    # gun on its gimbal (origin on the pivot, barrel along -Y): a rounded housing, a round barrel and muzzle
    p = Part(pal)
    with SA.at_frame(p, SA.frame((0, 0.03, 0), (0, -1, 0))):
        SA.limb(p, [(0.0, 0.034, 0.025, 0.025), (0.012, 0.04, 0.03, 0.03), (0.072, 0.036, 0.027, 0.027)], 'gunmetal', n=10, e=2.6)
    p.cyl((0, -0.03, 0), 0.026, 0.024, 0.15, 'alu', seg=10, rot=(90, 0, 0))
    with SA.at_frame(p, SA.frame((0, -0.17, 0), (0, -1, 0))):
        SA.limb(p, [(0.0, 0.036, 0.036, 0.036), (0.04, 0.033, 0.033, 0.033)], 'gunmetal', n=10, e=2.0)
    p.cyl((0, -0.06, 0), 0.0305, 0.0305, 0.03, 'amber', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, -0.207, 0), 0.018, 0.018, 0.006, 'ink', seg=8, rot=(90, 0, 0), deco=True)
    # detail pass: cooling rings on the barrel, ported muzzle brake, ammo box under the breech, a sight on top
    for y in (-0.10, -0.125, -0.15):
        p.cyl((0, y, 0), 0.0295, 0.0295, 0.008, 'gunmetal', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    for sx in (-1, 1):
        p.box((sx * 0.035, -0.19, 0), (0.008, 0.014, 0.016), 'ink', deco=True)
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
X_SAU = [(0.0, 0.155), (0.235, 0.158), (0.345, 0.238), (0.45, 0.332), (0.482, 0.372), (0.488, 0.43), (0.482, 0.484),
         (0.452, 0.522), (0.42, 0.55), (0.28, 0.61), (0.17, 0.63), (0.0, 0.635)]      # saucer profile (r, z)


def build_blader(pal):
    import bot_shapes_ground as SG
    SEG, PH = 16, -math.pi / 16          # facet centres every 22.5 deg (facet 12 = front -Y, under the sensor bar)
    CR = ((0.42, 0.55), (0.28, 0.61))                                                     # the crown slope
    p = Part(pal)
    # smooth saucer: rolled rim, rounded underside, a gold core dome on the crown and a round hub post
    p.lathe(X_SAU, 'violet', seg=SEG, phase=PH)
    p.sphere((0, 0, 0.62), 0.17, 'core', seg=(12, 5), scale=(1, 1, 0.68))
    p.cyl((0, 0, 0.70), 0.045, 0.045, 0.16, 'gunmetal', seg=12)                              # hub post
    # ---- deco: rim bands, hazard chevrons, under-thruster glow, crown vents, core seat
    for z0, z1 in ((0.383, 0.40), (0.46, 0.477)):
        p.lathe([(0.496, z0), (0.496, z1)], 'violet2', seg=SEG, phase=PH, deco=True)
    for k in range(0, SEG, 2):
        p.on_slope(k, SEG, (0.345, 0.238), (0.45, 0.332), 0.55, 0.004, (0.07, 0.006, 0.07), 'amber', phase=PH)
    p.cyl((0, 0, 0.150), 0.18, 0.18, 0.008, 'teal', seg=12, deco=True)
    p.cyl((0, 0, 0.140), 0.08, 0.08, 0.008, 'paper', seg=10, deco=True)
    p.lathe([(0.18, 0.62), (0.18, 0.645)], 'gunmetal', seg=SEG, deco=True)
    # detail pass: a curved bezel behind the sensor bar, rim bolts between the bands, curved crown armour plates with
    # vents between them, crown bolts, three thruster nozzles under the saucer, hub post collar and slip rings
    SG.arc_plate(p, 0.466, 0.484, 0.403, 0.457, 254, 286, 2, 'gunmetal', deco=True)
    for k in range(0, SEG, 2):
        if k == 12:
            continue
        with ED.at(p, ED.facet_frame(k, SEG, 0.488, 0.43, phase=PH)):
            ED.bolt(p, 0, 0, r=0.011, top=0.006, color='violet2', seg=4)
    (r0, z0), (r1, z1) = CR
    nrm = Vector((z1 - z0, r0 - r1)).normalized()
    plate = lambda t0, t1, d0, d1: [(r0 + (r1 - r0) * t + nrm.x * d, z0 + (z1 - z0) * t + nrm.y * d) for t, d in
                                    ((t0, d0), (t1, d0), (t1, d1), (t0, d1))]
    for a in (0, 90, 180, 270):                                                           # curved crown armour
        SG.sweep(p, plate(0.12, 0.86, -0.006, 0.008), math.radians(a - 33.75), math.radians(a + 33.75), 3, 'violet2', deco=True)
    for k in (2, 6, 10, 14):                                                              # vents between the plates
        with ED.at(p, ED.slope_frame(k, SEG, CR[0], CR[1], 0.5, phase=PH)):
            for y in (-0.014, 0.0, 0.014):
                ED.pad(p, 0, y, 0.05, 0.006, 0.003, 'gunmetal', base=0.004)
            ED.pad(p, 0, 0, 0.06, 0.042, 0.004, 'ink', base=0.0)
    for k in range(1, SEG, 2):
        p.on_slope(k, SEG, (0.28, 0.61), (0.17, 0.63), 0.5, 0.0, (0.022, 0.006, 0.022), 'gunmetal', phase=PH)
    for j in range(3):
        a = math.radians(90 + 120 * j)
        x, y = 0.15 * math.cos(a), 0.15 * math.sin(a)
        p.cyl((x, y, 0.128), 0.04, 0.032, 0.04, 'gunmetal', seg=8, deco=True)
        p.cyl((x, y, 0.122), 0.026, 0.026, 0.008, 'teal', seg=8, deco=True)
    p.cyl((0, 0, 0.66), 0.055, 0.055, 0.03, 'steel', seg=12, deco=True)
    for z in (0.75, 0.80):
        p.cyl((0, 0, z), 0.05, 0.05, 0.012, 'amber', seg=12, caps=False, deco=True)
    body = p.build('BOT_BLADER_Body')
    socket('BOT_BLADER_CORE', body, (0, 0, 0.67))
    socket('BOT_BLADER_HUB', body, X_HUB)
    socket('BOT_BLADER_LIGHT', body, (0, -0.48, 0.43))

    # hub: a rounded drum on the post, one tapered chamfered arm through it (the weapon clamp on +X, a rounded
    # counterweight on -X)
    p = Part(pal)
    p.lathe([(0.0, -0.04), (0.11, -0.04), (0.12, -0.028), (0.12, 0.028), (0.11, 0.04), (0.0, 0.04)], 'steel', seg=12)
    SG.cprism(p, [(-0.33, -0.028), (-0.06, -0.034), (0.08, -0.034), (0.45, -0.026), (0.45, 0.026), (0.08, 0.034),
                  (-0.06, 0.034), (-0.33, 0.028)], -0.025, 0.025, 'gunmetal', c=0.01)
    p.parent = Matrix.Translation((-0.34, 0, 0))
    p.lathe([(0.0, -0.05), (0.06, -0.05), (0.07, -0.038), (0.07, 0.038), (0.06, 0.05), (0.0, 0.05)], 'amber', seg=10)
    p.parent = Matrix.Identity(4)
    SG.rbox(p, (X_GRIP[0], 0, 0), (0.08, 0.09, 0.08), 'violet2', r=0.022, n=1, c=0.012)
    p.cyl((0, 0, 0.038), 0.06, 0.06, 0.008, 'amber', seg=12, deco=True)
    p.cyl((-0.34, 0, 0.048), 0.04, 0.04, 0.008, 'ink', seg=8, deco=True)
    # detail pass: lightening slots in the arm, a hydraulic piston over the weapon arm, clamp bolts and jaw slit,
    # weight plates on the counterweight, bolts round the hub drum
    for x in (0.17, 0.26, 0.35, -0.16, -0.25):
        p.box((x, 0, 0.026), (0.05, 0.016, 0.006), 'ink', deco=True)
    for sy in (-1, 1):
        for x in (0.458, 0.482):
            p.cyl((x, sy * 0.043, 0.022), 0.009, 0.009, 0.006, 'steel', seg=4, rot=(sy * -90, 0, 0), deco=True)
    ED.piston(p, (0.10, 0, 0.045), (0.40, 0, 0.045), 0.012, 0.007, k=0.55, body='gunmetal', rod='steel', seg=6)
    for x in (0.10, 0.40):
        p.box((x, 0, 0.034), (0.022, 0.016, 0.022), 'gunmetal', deco=True)
    p.box((X_GRIP[0] + 0.0, 0, 0.0425), (0.04, 0.012, 0.006), 'ink', deco=True)
    p.cyl((-0.34, 0, -0.03), 0.074, 0.074, 0.008, 'gunmetal', seg=10, caps=False, deco=True)
    ED.bolt_ring(p, 0, 0, 0.04, 0.09, 6, r=0.01, h=0.006, phase=math.pi / 6, seg=4)
    hub = p.build('BOT_BLADER_Hub', bevel=False)
    socket('BOT_BLADER_GRIP', hub, X_GRIP)

    # katana (origin = clamp centre; the clamp hides the middle of the handle): round wrapped handle, rolled
    # tsuba, habaki, a blade with a chamfered spine, flats, a ridge line and a ground edge (pale temper line)
    p = Part(pal)
    XA = Matrix.Rotation(math.radians(90), 4, 'Y')                                      # lathe axis Z -> X
    p.cyl((-0.15, 0, 0), 0.022, 0.022, 0.27, 'ink', seg=8, rot=(0, 90, 0))
    p.parent = Matrix.Translation((-0.16, 0, 0)) @ XA
    p.lathe([(0.0, -0.012), (0.022, -0.012), (0.028, -0.004), (0.028, 0.012), (0.0, 0.012)], 'steel', seg=8)   # pommel
    p.parent = Matrix.Translation((0.13, 0, 0)) @ XA
    p.lathe([(0.0, -0.01), (0.058, -0.01), (0.066, -0.003), (0.066, 0.003), (0.058, 0.01), (0.0, 0.01)], 'gunmetal', seg=14)  # tsuba
    p.parent = Matrix.Identity(4)
    SG.rbox(p, (0.1525, 0.0, 0), (0.026, 0.05, 0.035), 'amber', r=0.008, n=1, rot=(0, 90, 0))   # habaki
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.165 + 0.825 * t
        sori = -0.07 * t * t
        w = 0.068 - 0.014 * t
        st.append((x, -w / 2 + sori, w / 2 + sori, 0.0095 - 0.0025 * t, 0.66))
    SG.blade(p, st, (1.06, -0.07 - 0.005, 0.0), 'blade', 'paper')
    # detail pass: criss-cross ito wrap rings on the handle, seppa washers and a ring on the guard, a fuller (bo-hi)
    # groove line along both flats of the blade near the spine
    for i, x in enumerate((-0.115, -0.085, -0.055, 0.055, 0.085)):
        p.cyl((x - 0.005, 0, 0), 0.026, 0.026, 0.010, 'paper', seg=8, rot=(0, 90, 22 if i % 2 else -22), caps=False, deco=True)
    for x in (0.111, 0.141):
        p.cyl((x - 0.002, 0, 0), 0.034, 0.034, 0.006, 'amber', seg=10, rot=(0, 90, 0), deco=True)
    p.cyl((0.117, 0, 0), 0.05, 0.05, 0.006, 'ink', seg=14, rot=(0, 90, 0), caps=False, deco=True)
    for sz in (-1, 1):
        for a, b in zip(st[1:], st[2:]):
            if b[0] > 0.86:
                break
            pts = []
            for (x, yb, ye, t, _), f in ((a, 0.16), (b, 0.16), (b, 0.36), (a, 0.36)):
                pts.append(Vector((x, yb + (ye - yb) * f, sz * t)))
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

    # electric axe: round shaft with wrapped grip, rounded head with the battery, chamfered blade with a ground
    # bevel inside the glowing edge
    p = Part(pal)
    p.cyl((-0.10, 0, 0), 0.024, 0.024, 0.90, 'steel', seg=10, rot=(0, 90, 0))
    p.cyl((-0.12, 0, 0), 0.03, 0.03, 0.03, 'gunmetal', seg=10, rot=(0, 90, 0))
    p.cyl((0.08, 0, 0), 0.029, 0.029, 0.22, 'ink', seg=10, rot=(0, 90, 0), caps=False)
    SG.rbox(p, (0.70, 0.0, 0), (0.12, 0.085, 0.075), 'gunmetal', r=0.025, n=1, c=0.012)
    SG.rbox(p, (0.70, -0.065, 0), (0.08, 0.05, 0.055), 'teal', r=0.012, n=1, c=0.008)
    SG.cprism(p, SG.fillet([(0.62, 0.02), (0.78, 0.02), (0.83, 0.13), (0.85, 0.25), (0.70, 0.29), (0.55, 0.25), (0.57, 0.13)],
                           [0.0, 0.0, 0.03, 0.02, 0.0, 0.02, 0.03], n=1), -0.014, 0.014, 'steel', c=0.007)
    p.prism([(0.55, 0.235), (0.70, 0.27), (0.85, 0.235), (0.855, 0.255), (0.70, 0.295), (0.545, 0.255)], -0.019, 0.019, 'lens')
    SG.cprism(p, [(0.67, -0.06), (0.70, -0.17), (0.73, -0.06)], -0.01, 0.01, 'steel', c=0.005)
    for xc in (0.56, 0.60):
        p.cyl((xc, 0, 0), 0.036, 0.036, 0.014, 'teal', seg=10, rot=(0, 90, 0), caps=False, deco=True)
    # detail pass: wrapped grip rings, head bolts and hazard stencils on both faces, a bevel line along the blade
    # inside the glowing edge, a power cable from the battery over the head, a pommel cap
    for x in (0.12, 0.19, 0.26):
        p.cyl((x, 0, 0), 0.033, 0.033, 0.009, 'gunmetal', seg=10, rot=(0, 90, 0), caps=False, deco=True)
    for sz in (-1, 1):
        p.box((0.70, 0.0, sz * 0.0385), (0.05, 0.03, 0.006), 'amber', deco=True)
        for x in (0.69, 0.71):
            p.box((x, 0.0, sz * 0.0435), (0.005, 0.024, 0.004), 'ink', rot=(0, 0, 30), deco=True)
        p.prism([(0.575, 0.205), (0.70, 0.235), (0.825, 0.205), (0.83, 0.217), (0.70, 0.249), (0.57, 0.217)],
                *(sorted((sz * 0.0125, sz * 0.018))), 'gunmetal', deco=True)
    ED.cable(p, [(0.68, -0.09, 0.02), (0.68, -0.05, 0.052), (0.70, 0.03, 0.052), (0.72, 0.06, 0.02)], 0.012, 'ink')
    p.cyl((-0.13, 0, 0), 0.034, 0.03, 0.012, 'amber', seg=10, rot=(0, 90, 0), deco=True)
    p.build('BOT_BLADER_Axe', bevel=False, hull=0.01)

    p = Part(pal)
    SG.rbox(p, (0, 0, 0), (0.20, 0.035, 0.02), 'light', r=0.008, n=1, rot=(90, 0, 0))
    p.build('BOT_BLADER_Light', bevel=False, hull=0.006)
    build_blader2(pal)                                                                   # the levels 30+ skin


# ================================================================ BLADE BOT, ADVANCED SKIN (levels 30+)
# Same saucer, hub, pivots, sockets and hit volumes as the Blade Bot (the parts are swapped in by the game, the sockets
# stay on Body / Hub / Fundo): a tactical refit in the same violet family. Body2: segmented rim armour, a wrap-around
# sensor visor round the lit sensor bar (Light), dark crown plates with cyan sensor lenses between them, a swept sensor
# fin with a glowing leading edge, a cyan ring round the gold core, a few amber hazard tabs kept for fun. Hub2: an
# armoured drum with a sensor ring, plated arms, an armoured counterweight. Sharper weapons with glowing cyan edges:
# Katana2 (straighter blade with a clipped tanto point, octagonal guard, segmented grip), Axe2 (crescent blade with
# horned tips, a longer spike, armoured head), Kusari2 (narrower sickle with a long point, dark handle). The chain
# and the weight (Fundo) are shared with the normal skin.
def build_blader2(pal):
    import bot_shapes_ground as SG
    SEG, PH = 16, -math.pi / 16
    CR = ((0.42, 0.55), (0.28, 0.61))
    p = Part(pal)
    p.lathe(X_SAU, 'violet', seg=SEG, phase=PH)
    p.sphere((0, 0, 0.62), 0.17, 'core', seg=(12, 5), scale=(1, 1, 0.68))
    p.cyl((0, 0, 0.70), 0.045, 0.045, 0.16, 'gunmetal', seg=12)                              # hub post
    # swept sensor fin on the back of the crown (clear of the spinning hub)
    SG.sprism2(p, [(0.20, 0.585), (0.36, 0.555), (0.37, 0.585), (0.27, 0.735), (0.235, 0.735)], -0.012, 0.012, 'gunmetal',
               c=0.004, r=[0.0, 0.0, 0.01, 0.015, 0.01], n=1)
    # sensor visor pods either side of the lit sensor bar (the Light part sits between them, on a bezel)
    for a0, a1 in ((236, 257), (283, 304)):
        SG.arc_plate(p, 0.46, 0.50, 0.398, 0.462, a0, a1, 2, 'ink', c=0.008)
    # ---- deco: visor lenses, rim armour segments, crown plates and sensor lenses, fin edge, core ring, belly
    for a0, a1 in ((240, 253), (287, 300)):
        SG.arc_plate(p, 0.494, 0.506, 0.418, 0.442, a0, a1, 2, 'lens', deco=True)
    SG.arc_plate(p, 0.466, 0.484, 0.403, 0.457, 257, 283, 2, 'gunmetal', deco=True)
    for a in (330, 30, 90, 150, 210):
        SG.arc_plate(p, 0.476, 0.506, 0.386, 0.474, a - 22, a + 22, 2, 'violet2', c=0.009, deco=True)
        for da in (-11, 11):
            q = math.radians(a + da)
            n = Vector((math.cos(q), math.sin(q), 0))
            with ED.at(p, ED.axis_frame(tuple(n * (0.506 * math.cos(math.radians(11)) - 0.0005) + Vector((0, 0, 0.43))), tuple(n))):
                ED.bolt(p, 0, 0, r=0.009, top=0.004, color='steel', seg=4)
    (r0, z0), (r1, z1) = CR
    nrm = Vector((z1 - z0, r0 - r1)).normalized()
    plate = lambda t0, t1, d0, d1: [(r0 + (r1 - r0) * t + nrm.x * d, z0 + (z1 - z0) * t + nrm.y * d) for t, d in
                                    ((t0, d0), (t1, d0), (t1, d1), (t0, d1))]
    for a in (0, 90, 180, 270):                                                           # dark crown armour
        SG.sweep(p, plate(0.08, 0.9, -0.006, 0.01), math.radians(a - 33.75), math.radians(a + 33.75), 3, 'gunmetal', deco=True)
    for k in (2, 6, 10, 14):                                                              # cyan sensor lenses between them
        with ED.at(p, ED.slope_frame(k, SEG, CR[0], CR[1], 0.5, phase=PH)):
            ED.lamp(p, 0, 0, 0.018, lens='lens', rim='gunmetal', w=0.008, seg=6)
    SG.sprism2(p, [(0.268, 0.725), (0.358, 0.58), (0.372, 0.586), (0.282, 0.732)], -0.0155, 0.0155, 'lens', deco=True)
    p.lathe([(0.18, 0.62), (0.18, 0.645)], 'gunmetal', seg=SEG, deco=True)
    p.lathe([(0.188, 0.627), (0.188, 0.638)], 'lens', seg=SEG, deco=True)
    for k in (2, 6, 10, 14):                                                              # amber hazard tabs (the fun)
        p.on_slope(k, SEG, (0.345, 0.238), (0.45, 0.332), 0.55, 0.004, (0.07, 0.006, 0.07), 'amber', phase=PH)
    for k in (0, 4, 8, 12):
        with ED.at(p, ED.slope_frame(k, SEG, (0.345, 0.238), (0.45, 0.332), 0.55, phase=PH)):
            ED.grille(p, 0, 0, 0.08, 0.05, 3, color='ink', slat='gunmetal')
    p.cyl((0, 0, 0.150), 0.18, 0.18, 0.008, 'lens', seg=12, deco=True)
    p.cyl((0, 0, 0.140), 0.08, 0.08, 0.008, 'paper', seg=10, deco=True)
    for j in range(3):
        a = math.radians(90 + 120 * j)
        x, y = 0.15 * math.cos(a), 0.15 * math.sin(a)
        p.cyl((x, y, 0.128), 0.04, 0.032, 0.04, 'gunmetal', seg=8, deco=True)
        p.cyl((x, y, 0.122), 0.026, 0.026, 0.008, 'lens', seg=8, deco=True)
    p.cyl((0, 0, 0.66), 0.055, 0.055, 0.03, 'steel', seg=12, deco=True)
    p.cyl((0, 0, 0.75), 0.05, 0.05, 0.012, 'amber', seg=12, caps=False, deco=True)
    p.cyl((0, 0, 0.80), 0.05, 0.05, 0.012, 'lens', seg=12, caps=False, deco=True)
    p.build('BOT_BLADER_Body2')

    # hub: dark armoured drum with a cyan sensor ring, plated arm, armoured amber counterweight, plated clamp
    p = Part(pal)
    p.lathe([(0.0, -0.04), (0.11, -0.04), (0.12, -0.028), (0.12, 0.028), (0.11, 0.04), (0.0, 0.04)], 'gunmetal', seg=12)
    SG.cprism(p, [(-0.33, -0.028), (-0.06, -0.034), (0.08, -0.034), (0.45, -0.026), (0.45, 0.026), (0.08, 0.034),
                  (-0.06, 0.034), (-0.33, 0.028)], -0.025, 0.025, 'gunmetal', c=0.01)
    p.parent = Matrix.Translation((-0.34, 0, 0))
    p.lathe([(0.0, -0.05), (0.06, -0.05), (0.07, -0.038), (0.07, 0.038), (0.06, 0.05), (0.0, 0.05)], 'amber', seg=10)
    p.parent = Matrix.Identity(4)
    SG.rbox(p, (X_GRIP[0], 0, 0), (0.08, 0.09, 0.08), 'violet2', r=0.022, n=1, c=0.012)
    p.cyl((0, 0, -0.008), 0.124, 0.124, 0.016, 'lens', seg=12, caps=False, deco=True)
    p.cyl((0, 0, 0.038), 0.07, 0.07, 0.008, 'violet2', seg=12, deco=True)
    p.cyl((0, 0, 0.044), 0.03, 0.03, 0.008, 'lens', seg=8, deco=True)
    for x0, x1 in ((0.12, 0.40), (-0.30, -0.10)):                                         # side armour on the arms
        for sy in (-1, 1):
            xm, w = (x0 + x1) / 2, x1 - x0
            ym = sy * (0.034 - (xm - 0.08) / 0.37 * 0.008 if xm > 0 else 0.034 - (-0.06 - xm) / 0.27 * 0.006)
            SG.rbox(p, (xm, ym + sy * 0.004, 0), (w, 0.028, 0.012), 'violet2', r=0.012, n=1, rot=(sy * -90, 0, 0), deco=True)
    p.cyl((-0.34, 0, -0.03), 0.074, 0.074, 0.008, 'gunmetal', seg=10, caps=False, deco=True)
    p.cyl((-0.34, 0, 0.02), 0.074, 0.074, 0.008, 'gunmetal', seg=10, caps=False, deco=True)
    p.cyl((-0.34, 0, 0.048), 0.04, 0.04, 0.008, 'ink', seg=8, deco=True)
    p.box((X_GRIP[0], 0, 0.0425), (0.05, 0.014, 0.006), 'lens', deco=True)
    for sy in (-1, 1):
        for x in (0.458, 0.482):
            p.cyl((x, sy * 0.043, 0.022), 0.009, 0.009, 0.006, 'steel', seg=4, rot=(sy * -90, 0, 0), deco=True)
    ED.piston(p, (0.10, 0, 0.045), (0.40, 0, 0.045), 0.012, 0.007, k=0.55, body='gunmetal', rod='steel', seg=6)
    for x in (0.10, 0.40):
        p.box((x, 0, 0.034), (0.022, 0.016, 0.022), 'gunmetal', deco=True)
    ED.bolt_ring(p, 0, 0, 0.04, 0.095, 6, r=0.01, h=0.006, phase=math.pi / 6, seg=4)
    p.build('BOT_BLADER_Hub2', bevel=False)

    # katana: straighter blade with a clipped (tanto) point and a glowing cyan edge, octagonal guard, segmented grip
    p = Part(pal)
    XA = Matrix.Rotation(math.radians(90), 4, 'Y')
    p.cyl((-0.15, 0, 0), 0.022, 0.022, 0.27, 'ink', seg=8, rot=(0, 90, 0))
    p.parent = Matrix.Translation((-0.16, 0, 0)) @ XA
    p.lathe([(0.0, -0.012), (0.022, -0.012), (0.028, -0.004), (0.028, 0.012), (0.0, 0.012)], 'gunmetal', seg=8)
    p.parent = Matrix.Identity(4)
    SG.sprism2(p, SG.squircle(0.064, 0.064, 8, 2.0, phase=math.pi / 8), 0.12, 0.14, 'gunmetal', c=0.005)   # guard
    SG.rbox(p, (0.1525, 0.0, 0), (0.026, 0.05, 0.035), 'steel', r=0.006, n=1, rot=(0, 90, 0))
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.165 + 0.80 * t
        sori = -0.035 * t * t
        w = 0.066 - 0.024 * t
        st.append((x, -w / 2 + sori, w / 2 + sori, 0.0095 - 0.0025 * t, 0.6))
    SG.blade(p, st, (1.065, -0.052, 0.0), 'blade', 'lens')
    for x in (-0.12, -0.08, 0.06, 0.09):
        p.cyl((x - 0.006, 0, 0), 0.026, 0.026, 0.012, 'gunmetal', seg=8, rot=(0, 90, 0), caps=False, deco=True)
    p.cyl((-0.176, 0, 0), 0.016, 0.016, 0.006, 'lens', seg=8, rot=(0, 90, 0), deco=True)   # pommel light
    p.cyl((0.141, 0, 0), 0.036, 0.036, 0.004, 'violet2', seg=8, rot=(0, 90, 0), deco=True)
    p.build('BOT_BLADER_Katana2', bevel=False, hull=0.01)

    # electric axe: crescent blade with horned tips and a glowing edge, longer spike, armoured head
    p = Part(pal)
    p.cyl((-0.10, 0, 0), 0.024, 0.024, 0.90, 'gunmetal', seg=10, rot=(0, 90, 0))
    p.cyl((-0.12, 0, 0), 0.03, 0.03, 0.03, 'steel', seg=10, rot=(0, 90, 0))
    p.cyl((0.08, 0, 0), 0.029, 0.029, 0.22, 'ink', seg=10, rot=(0, 90, 0), caps=False)
    SG.rbox(p, (0.70, 0.0, 0), (0.12, 0.085, 0.075), 'gunmetal', r=0.025, n=1, c=0.012)
    SG.rbox(p, (0.70, -0.065, 0), (0.08, 0.05, 0.055), 'teal', r=0.012, n=1, c=0.008)
    SG.cprism(p, SG.fillet([(0.62, 0.02), (0.78, 0.02), (0.835, 0.12), (0.876, 0.292), (0.70, 0.262), (0.524, 0.292),
                            (0.565, 0.12)], [0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.03], n=1), -0.014, 0.014, 'steel', c=0.007)
    p.prism([(0.54, 0.272), (0.70, 0.244), (0.86, 0.272), (0.876, 0.296), (0.70, 0.268), (0.524, 0.296)], -0.019, 0.019, 'lens')
    SG.cprism(p, [(0.665, -0.06), (0.70, -0.205), (0.735, -0.06)], -0.011, 0.011, 'steel', c=0.005)
    for xc in (0.56, 0.60):
        p.cyl((xc, 0, 0), 0.036, 0.036, 0.014, 'lens', seg=10, rot=(0, 90, 0), caps=False, deco=True)
    for x in (0.12, 0.19, 0.26):
        p.cyl((x, 0, 0), 0.033, 0.033, 0.009, 'gunmetal', seg=10, rot=(0, 90, 0), caps=False, deco=True)
    for sz in (-1, 1):
        SG.rbox(p, (0.70, 0.0, sz * 0.0395), (0.09, 0.06, 0.008), 'violet2', r=0.012, n=1, deco=True)
        p.box((0.70, 0.0, sz * 0.0455), (0.05, 0.012, 0.006), 'lens', deco=True)
        p.prism([(0.58, 0.215), (0.70, 0.19), (0.82, 0.215), (0.828, 0.228), (0.70, 0.204), (0.572, 0.228)],
                *(sorted((sz * 0.0125, sz * 0.018))), 'gunmetal', deco=True)
    ED.cable(p, [(0.68, -0.09, 0.02), (0.68, -0.05, 0.052), (0.70, 0.03, 0.052), (0.72, 0.06, 0.02)], 0.012, 'ink')
    p.cyl((-0.13, 0, 0), 0.034, 0.03, 0.012, 'lens', seg=10, rot=(0, 90, 0), deco=True)
    p.build('BOT_BLADER_Axe2', bevel=False, hull=0.01)

    # sickle: dark handle with wraps and a cyan ring, a narrower kama blade with a long point and a glowing edge
    p = Part(pal)
    K = Matrix.Diagonal(Vector((1.4, 1.4, 1.4, 1)))
    YA = Matrix.Rotation(math.radians(90), 4, 'X')
    p.parent = K @ Matrix.Rotation(math.radians(90), 4, 'Y')
    _torus(p, 0.018, 0.006, 'chain', seg=6)
    p.parent = K
    p.cyl((0, -0.022, 0), 0.016, 0.021, 0.025, 'steel', seg=10, rot=(90, 0, 0))
    SG.tlimb(p, (0, -0.045, 0), (0, -0.375, 0), 0.021, 0.025, 'gunmetal', seg=10)
    for y in (-0.09, -0.15, -0.21, -0.27):
        p.cyl((0, y, 0), 0.028, 0.028, 0.018, 'ink', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    p.cyl((0, -0.33, 0), 0.029, 0.029, 0.01, 'lens', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    p.parent = K @ Matrix.Translation((0, -0.37, 0)) @ YA
    p.lathe([(0.0, 0.0), (0.026, 0.0), (0.031, 0.007), (0.031, 0.043), (0.026, 0.05), (0.0, 0.05)], 'steel', seg=8)
    p.parent = K @ Matrix.Translation((0, -0.395, 0))
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.012 + 0.32 * t
        curve = 0.14 * t * t
        w = 0.066 - 0.042 * t
        st.append((x, -w / 2 + curve, w / 2 + curve, 0.0085 - 0.003 * t, 0.6))
    SG.blade(p, st, (0.385, 0.205, 0.0), 'blade', 'lens')
    p.parent = K
    SG.cprism(p, [(-0.005, -0.37), (-0.06, -0.395), (-0.005, -0.42)], -0.012, 0.012, 'steel', c=0.005)   # back spike
    p.build('BOT_BLADER_Kusari2', bevel=False, hull=0.009)


# ================================================================ CRAWLER, ADVANCED SKIN (levels 20+)
# Same silhouette, pivots and hit volumes as the tin-can Crawler (same hips, core, light): a faceted armoured shell
# with a sloped head ring and a wrap-around visor, belly and belt armour, panel lines and bolts. The armour is in the
# two KEY colours: 'plate' (about two thirds of the shell) and 'plate2' (the other third); the game paints them black
# and grey per crawler (ai.js keyMat2: 66 % grey / 33 % black or the other way round). Specks: white flecks and a
# stencil chevron drawn over some of them (its own part, so most crawlers draw none).
def build_crawler2(pal):
    import bot_shapes_ground as SG
    PH, SEG = -math.pi / 16, 16       # 16-sided shell, facet centres every 22.5 deg (facet 12 = front -Y, 4 = back)
    R = 0.324
    PROF = [(0.0, 0.30), (0.29, 0.30), (0.318, 0.315), (R, 0.345), (R, 0.59), (0.316, 0.618), (0.292, 0.665),
            (0.262, 0.708), (0.25, 0.73), (0.0, 0.734)]
    rs = lambda z: next(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]) for a, b in zip(PROF[1:], PROF[2:]) if z <= b[1])
    fr = lambda k, z, r=None, out=0.0: ED.facet_frame(k, SEG, r or rs(z), z, phase=PH, out=out)
    p = Part(pal)
    # one sculpted armour shell rolling into the sloped head, a rounded belly bowl and a rolled head cap (plate2)
    p.lathe(PROF, 'plate', seg=SEG, phase=PH)
    p.lathe([(0.0, 0.25), (0.27, 0.25), (0.325, 0.27), (0.336, 0.30), (0.30, 0.318), (0.0, 0.318)], 'plate2', seg=SEG, phase=PH)
    p.lathe([(0.0, 0.724), (0.244, 0.726), (0.27, 0.744), (0.255, 0.764), (0.0, 0.768)], 'plate2', seg=SEG, phase=PH)
    p.sphere((0, 0, 0.77), 0.14, 'core', seg=(12, 5), scale=(1, 1, 0.6))
    p.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=6)                           # whip antenna (light)
    # wrap-around visor on the head slope: ink housing (outlined) with a glowing lens strip
    vis = lambda z0, z1, d0, d1: [(rs(z0) + d0, z0), (rs(z0) + d1, z0), (rs(z1) + d1, z1), (rs(z1) + d0, z1)]
    SG.sweep(p, vis(0.635, 0.692, -0.02, 0.012), math.radians(230), math.radians(310), 6, 'ink')
    # ---- deco: lens, belt band (plate2), panel line, belt armour, panel lines, bolts, core seat
    SG.sweep(p, vis(0.648, 0.678, 0.006, 0.019), math.radians(238), math.radians(302), 6, 'lens', deco=True)
    p.lathe([(0.335, 0.37), (0.335, 0.44)], 'plate2', seg=SEG, phase=PH, deco=True)
    p.lathe([(0.329, 0.494), (0.329, 0.506)], 'ink', seg=SEG, phase=PH, deco=True)
    ARM = (7, 1, 15, 4, 9)
    for k in ARM:                                                                         # rounded belt armour, bolted
        with ED.at(p, fr(k, 0.405, 0.335)):
            SG.rbox(p, (0, 0, 0.024), (0.12, 0.11, 0.052), 'plate2', r=0.022, n=1, c=0.01, deco=True)
            ED.bolts(p, [(sx * 0.04, 0.035) for sx in (-1, 1)], r=0.01, top=0.005, color='gunmetal', seg=6, base=0.05)
    for k in range(1, SEG, 2):
        p.on_facet(k, SEG, R, 0.003, 0.55, (0.012, 0.008, 0.08), 'ink', phase=PH)        # vertical panel lines
    for k in (0, 4, 8):
        p.on_facet(k, SEG, 0.321, 0.003, 0.33, (0.028, 0.008, 0.028), 'gunmetal', phase=PH)   # bolts
    p.cyl((-0.15, 0.09, 0.755), 0.014, 0.014, 0.13, 'ink', seg=6, deco=True)             # stub antenna, ball tip
    p.sphere((-0.15, 0.09, 0.895), 0.022, 'plate2', seg=(5, 3), deco=True)
    p.lathe([(0.152, 0.758), (0.152, 0.785)], 'gunmetal', seg=SEG, deco=True)
    # hip mounts with pivot pins, cap rim bolts, head ring vents, chin grille, back heat sink, rivets, serial plate,
    # antenna collar and lamp holder (plates keep the key colours)
    for k in (10, 14, 2, 6):
        with ED.at(p, fr(k, 0.355, 0.322)):
            SG.rbox(p, (0, 0, 0.02), (0.08, 0.07, 0.05), 'gunmetal', r=0.018, n=1, deco=True)
        a = math.radians(22.5 * k)
        u, t = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        c = u * 0.345 + Vector((0, 0, 0.33))
        p.limb(tuple(c - t * 0.05), tuple(c + t * 0.05), 0.02, 0.02, 'steel', seg=8, caps=False, deco=True)
    ED.bolt_ring(p, 0, 0, 0.766, 0.212, 8, r=0.011, h=0.007, color='gunmetal', phase=0.3, seg=5)
    for k in (3, 4, 5):
        with ED.at(p, ED.slope_frame(k, SEG, (0.316, 0.618), (0.292, 0.665), 0.5, phase=PH)):
            ED.grille(p, 0, 0, 0.09, 0.04, 2, color='ink', slat='gunmetal')
    with ED.at(p, fr(12, 0.555)):                                                          # chin grille under the visor
        ED.grille(p, 0, 0, 0.11, 0.05, 3, color='ink', slat='gunmetal', base=0.009)      # over the panel line
    with ED.at(p, fr(4, 0.553)):                                                           # back heat sink
        ED.pad(p, 0, 0, 0.11, 0.07, 0.006, 'gunmetal')
        for i in range(4):
            ED.pad(p, -0.039 + 0.026 * i, 0, 0.008, 0.06, 0.02, 'ink', base=0.006)
    for k in (2, 7, 10, 14):                                                               # rivets on the shell plates
        with ED.at(p, fr(k, 0.555)):
            ED.bolts(p, [(sx * 0.04, sx * 0.03) for sx in (-1, 1)], r=0.009, top=0.004, color='gunmetal', seg=4)
    with ED.at(p, fr(0, 0.535)):
        ED.serial_plate(p, 0, 0, 0.07, 0.03, color='paper')
    p.cyl((0.12, 0.08, 0.765), 0.03, 0.03, 0.03, 'gunmetal', seg=8, deco=True)
    p.cyl((0.12, 0.08, 0.995), 0.028, 0.028, 0.035, 'gunmetal', seg=8, deco=True)
    p.build('BOT_CRAWLER_Body2')
    # legs: ball hip, rounded thigh guard, armoured tapered strut with a curved shin guard, coil, domed plated foot
    p = Part(pal)
    p.sphere((0, 0, 0), 0.04, 'gunmetal', seg=(6, 4), deco=True)
    SG.rbox(p, (0, 0, -0.02), (0.11, 0.08, 0.07), 'plate2', r=0.024, n=1, c=0.012)
    SG.tlimb(p, (0, 0, -0.05), (0, 0, -0.32), 0.03, 0.02, 'plate', seg=8, e=3.0)
    SG.arc_plate(p, 0.024, 0.036, -0.29, -0.19, 225, 315, 3, 'plate2', deco=True)
    for i in range(2):
        with ED.at(p, Matrix.Translation((0, 0, -0.09 - i * 0.065)) @ Matrix.Rotation(math.radians(12 if i % 2 else -12), 4, 'X')):
            p.cyl((0, 0, -0.01), 0.048, 0.048, 0.02, 'gunmetal', seg=8, caps=False, deco=True)
    p.lathe([(0.0, -0.355), (0.096, -0.355), (0.07, -0.318), (0.0, -0.30)], 'plate2', seg=8)
    p.build('BOT_CRAWLER_Leg2', bevel=False, hull=0.01)
    # specks: white flecks and a stencil chevron, 6 mm off the shell (drawn over Body2, no outline); the flecks keep
    # the old layout (facet of the 10-sided shell, height, angle off the facet centre, size), moved onto the 16 facets
    p = Part(pal)
    rnd = [(0, 0.47, 0.05, 0.03), (1, 0.535, 0.1, 0.022), (2, 0.57, -0.06, 0.036), (3, 0.475, -0.1, 0.02),
           (4, 0.555, 0.04, 0.03), (5, 0.535, -0.1, 0.026), (6, 0.565, 0.08, 0.022), (8, 0.53, -0.05, 0.034),
           (9, 0.47, 0.1, 0.026), (0, 0.575, -0.07, 0.018), (4, 0.47, -0.08, 0.028), (2, 0.53, 0.07, 0.02),
           (6, 0.48, -0.06, 0.028), (8, 0.575, 0.07, 0.018), (1, 0.475, -0.08, 0.024), (9, 0.56, -0.06, 0.03)]
    hw = R * math.sin(math.pi / SEG)
    for k, z, d, sz in rnd:
        a = 2 * math.pi * (k + 0.5) / 10 + d
        k16 = int(round(a / (2 * math.pi / SEG))) % SEG
        da = (a - k16 * 2 * math.pi / SEG + math.pi) % (2 * math.pi) - math.pi
        lim = hw - sz * 0.8 - 0.004
        x = max(-lim, min(lim, da * R))
        with ED.at(p, fr(k16, z, R)):
            p.box((x, 0, 0.009), (sz * 1.6, sz * 1.25, 0.006), 'paper')
    for k, z, w in ((4, 0.39, 0.05), (7, 0.42, 0.035), (15, 0.395, 0.04), (9, 0.385, 0.03)):   # on the belt armour
        with ED.at(p, fr(k, 0.405, 0.335)):
            p.box((0, z - 0.405, 0.0545), (w, w * 0.7, 0.006), 'paper')
    for k in (6, 7):                                                                       # stencil on the head slope
        with ED.at(p, ED.slope_frame(k, SEG, (0.316, 0.618), (0.292, 0.665), 0.35, phase=PH)):
            p.box((0, 0, 0.007), (0.10, 0.03, 0.006), 'paper')
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
    import bot_shapes_air as SA
    SEG = 16
    ph = math.pi / 2                                                                           # a ring vertex on the top line
    FUS = Matrix.Translation((0, 0, H_CEN)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Diagonal(Vector((1, 0.72, 1, 1)))
    p = Part(pal)
    # fuselage: a smooth lathe along the length (lathe z -> -Y), flattened to 72 % of its width
    p.parent = FUS
    prof = [(0.0, -0.46), (0.07, -0.45), (0.14, -0.385), (0.185, -0.26), (0.207, -0.08), (0.205, 0.10), (0.182, 0.26), (0.135, 0.39),
            (0.07, 0.48), (0.0, 0.52)]
    SA.lathe_r(p, prof, 'hawk', seg=SEG, phase=ph)
    p.parent = Matrix.Identity(4)
    rp = lambda z: next(r0 + (r1 - r0) * (z - z0) / (z1 - z0) for (r0, z0), (r1, z1) in zip(prof, prof[1:]) if z0 <= z <= z1)
    ztop = lambda y: H_CEN + rp(-y) * 0.72                                                    # top line height at y
    # dorsal armour spine: a rounded blister along the top line
    spine = [(0.30, 0.04, 0.014, 0.016), (0.24, 0.07, 0.03, 0.034), (-0.15, 0.075, 0.03, 0.036), (-0.23, 0.045, 0.016, 0.018)]
    with SA.at_frame(p, SA.frame((0, 0, 0), (0, -1, 0))):
        SA.loft(p, [SA.ring_se(a, bf, bb, 10, 2.6, -y, 0, ztop(y) - 0.006) for y, a, bf, bb in spine], 'hawk2')
    top = ztop(0.0) - 0.006 + 0.036                                                             # spine crest height mid-body
    for sx in (-1, 1):                                                                         # V-tail fins: tapered lens section
        p.parent = Matrix.Translation((sx * 0.045, 0, ztop(0.3) - 0.004)) @ Matrix.Rotation(math.radians(-30 * sx), 4, 'Y')
        rings = []
        for z, y0, y1, t in ((0.0, 0.20, 0.42, 0.014), (0.205, 0.37, 0.47, 0.008)):
            m = (y0 + y1) / 2
            rings.append([(0, y0, z), (-t, y0 + (y1 - y0) * 0.3, z), (-t * 0.6, y0 + (y1 - y0) * 0.75, z), (0, y1, z),
                          (t * 0.6, y0 + (y1 - y0) * 0.75, z), (t, y0 + (y1 - y0) * 0.3, z)])
        SA.loft(p, rings, 'hawk2')
    p.parent = Matrix.Identity(4)
    for sx in (-1, 1):
        # stub pylon to the fan: a tapered wing section
        with SA.at_frame(p, SA.frame((sx * 0.15, H_FAN[1], H_FAN[2]), (sx, 0, 0))):
            rings = []
            for z, c, t in ((0.0, 0.085, 0.024), (0.17, 0.065, 0.016)):
                rings.append([(0, -c, z), (t * 0.8, -c * 0.4, z), (t, 0.2 * c, z), (t * 0.4, c, z), (-t * 0.4, c, z), (-t, 0.2 * c, z),
                              (-t * 0.8, -c * 0.4, z)])
            SA.loft(p, rings, 'hawk2')
        # intake cheek: a rounded pod along the flank, an oval intake mouth at its front
        with SA.at_frame(p, SA.frame((sx * 0.19, 0.12, H_CEN - 0.03), (0, -1, 0))):
            SA.limb(p, [(0.0, 0.022, 0.035, 0.035), (0.05, 0.032, 0.054, 0.054), (0.21, 0.032, 0.056, 0.056), (0.26, 0.026, 0.046, 0.046)],
                    'hawk', n=10, e=2.4)
            SA.limb(p, [(0.258, 0.017, 0.032, 0.032), (0.264, 0.017, 0.032, 0.032)], 'ink', n=8, e=2.0, deco=True)   # intake mouth
    with SA.at_frame(p, SA.frame((0, 0.33, H_CEN), (0, 1, 0))):
        SA.lathe_r(p, [(0.072, 0.0), (0.09, 0.03), (0.088, 0.12), (0.074, 0.205)], 'gunmetal', seg=12)          # tail thruster
    p.cyl((0, 0.535, H_CEN), 0.06, 0.06, 0.012, 'plate', seg=12, rot=(-90, 0, 0))           # thruster glow
    p.sphere((0, 0.17, H_CEN - 0.13), 0.075, 'core', seg=(12, 6), scale=(1, 1.2, 0.6))       # core (belly)
    with SA.at_frame(p, Matrix.Translation((0, H_PIVOT[1] + 0.01, H_PIVOT[2] + 0.015))):
        SA.slab(p, 0.04, 0.05, 0.05, 0.02, 0.01, 'gunmetal', nc=2)                              # turret mount
    # deco: accent strips along the cheeks and the spine (KEY colours), panel lines, thruster ring, vents
    for sx in (-1, 1):
        p.box((sx * (0.19 + 0.032 + 0.002), 0.03, H_CEN - 0.03), (0.008, 0.15, 0.02), 'plate', deco=True)   # accent strips on the cheeks
        # spine accents: on the blister flanks, one path point per station
        pts, nrm = [], []
        for y, a, bf, bb in spine[1:3]:
            q, n = SA.se_point(a, bf, bb, 2.6, math.radians(55 if sx > 0 else 125))
            pts.append((q.x, y, ztop(y) - 0.006 + q.y)); nrm.append((n.x, 0, n.y))
        SA.sweep(p, pts, nrm, 0.014, 0.004, 'plate', off=-0.001)
    for y in (-0.12, 0.08, 0.2):
        pts, nrm = [], []
        for d in (60, 90, 120):
            q, n = SA.se_point(0.075 if y < 0.2 else 0.0735, 0.03, 0.036 if y < 0.2 else 0.0355, 2.6, math.radians(d))
            pts.append((q.x, y, ztop(y) - 0.006 + q.y)); nrm.append((n.x, 0, n.y))
        SA.sweep(p, pts, nrm, 0.008, 0.004, 'ink', off=-0.001)                                    # spine panel lines
    p.cyl((0, 0.47, H_CEN), 0.0925, 0.0925, 0.03, 'plate2', seg=12, rot=(-90, 0, 0), caps=False, deco=True)
    # detail pass: panel seam rings round the fuselage, a sensor bezel round the nose eye, a dorsal sensor turret,
    # intake slats, a blade antenna under the belly, a collar round the core, cooling rings and nozzle petals
    p.parent = FUS
    for zc in (-0.27, 0.28):
        p.lathe([(rp(zc - 0.005) + 0.0055, zc - 0.005), (rp(zc + 0.005) + 0.0055, zc + 0.005)], 'ink', seg=SEG, phase=ph, deco=True)
    p.parent = Matrix.Identity(4)
    ly = Vector((0, math.cos(math.radians(-28)), math.sin(math.radians(-28))))
    p.box(tuple(Vector((0, -0.385, H_CEN + 0.07)) + ly * 0.012), (0.19, 0.06, 0.06), 'gunmetal', rot=(-28, 0, 0), deco=True)
    p.cyl((0, 0.145, top - 0.006), 0.03, 0.022, 0.024, 'hawk3', seg=10, deco=True)
    p.box((0, 0.118, top + 0.008), (0.03, 0.012, 0.012), 'lens', deco=True)
    p.box((0, -0.06, H_CEN - 0.155), (0.006, 0.07, 0.035), 'hawk2', rot=(25, 0, 0), deco=True)
    p.parent = Matrix.Translation((0, 0.17, H_CEN - 0.145)) @ Matrix.Diagonal(Vector((1, 1.2, 1, 1)))
    p.cyl((0, 0, 0), 0.082, 0.082, 0.014, 'gunmetal', seg=12, caps=False, deco=True)
    p.parent = Matrix.Identity(4)
    for y in (0.415, 0.445):
        p.cyl((0, y, H_CEN), 0.0935, 0.0935, 0.01, 'ink', seg=12, rot=(-90, 0, 0), caps=False, deco=True)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        p.box((0.074 * math.cos(a), 0.54, H_CEN + 0.074 * math.sin(a)), (0.03, 0.03, 0.008), 'gunmetal',
              rot=(0, -math.degrees(a) + 90, 0), deco=True)
    body = p.build('BOT_HAWK_Body', bevel=False)
    socket('BOT_HAWK_CORE', body, (0, 0.17, H_CEN - 0.15))
    for i, sx in enumerate((-1, 1)):
        socket('BOT_HAWK_FAN%d' % i, body, (sx * H_FAN[0], H_FAN[1], H_FAN[2]))
    socket('BOT_HAWK_GUNPIVOT', body, H_PIVOT)
    socket('BOT_HAWK_LIGHT', body, (0, -0.385, H_CEN + 0.07))

    # ducted fan (origin = duct centre): a rounded duct section turned about Z, round stator rods and a domed hub,
    # accent rim
    p = Part(pal)
    duct = [(0.15, -0.045), (0.178, -0.052), (0.2, -0.03), (0.206, 0.0), (0.2, 0.04), (0.172, 0.062), (0.15, 0.05), (0.15, -0.045)]
    p.lathe(duct, 'hawk2', seg=16)
    p.cyl((-0.155, 0, -0.035), 0.011, 0.011, 0.31, 'gunmetal', seg=6, rot=(0, 90, 0))
    p.cyl((0, -0.155, -0.03), 0.011, 0.011, 0.31, 'gunmetal', seg=6, rot=(-90, 0, 0))
    SA.lathe_r(p, [(0.03, -0.062), (0.042, -0.05), (0.04, -0.012), (0.026, 0.0), (0.0, 0.004)], 'hawk', seg=10)
    p.lathe([(0.2075, -0.004), (0.2075, 0.02)], 'plate', seg=16, deco=True)
    p.cyl((0, 0, -0.068), 0.026, 0.026, 0.008, 'plate2', seg=10, deco=True)
    # detail pass: bolts round the duct lip, four extra stator vanes, cooling bands on the motor housing
    for k in range(0, 16, 2):
        p.on_slope(k, 16, (0.206, 0.0), (0.2, 0.04), 0.75, 0.0, (0.014, 0.007, 0.014), 'gunmetal')
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        p.beam((0.045 * math.cos(a), 0.045 * math.sin(a), -0.02), (0.152 * math.cos(a), 0.152 * math.sin(a), -0.02), 0.012, 'gunmetal', deco=True)
    p.cyl((0, 0, -0.04), 0.0445, 0.0445, 0.008, 'gunmetal', seg=10, caps=False, deco=True)
    p.build('BOT_HAWK_Fan', bevel=False, hull=0.01)
    # rotor: three tapered, twisted blades on a round hub
    p = Part(pal)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.parent = Matrix.Rotation(a, 4, 'Z')
        rings = []
        for x, c, t, tw in ((0.02, 0.016, 0.005, 22), (0.135, 0.022, 0.004, 12)):
            R = Matrix.Rotation(math.radians(tw), 3, 'X')
            rings.append([tuple(R @ Vector((x, yy, zz))) for yy, zz in ((-c, 0), (-c * 0.3, t), (c, 0), (-c * 0.3, -t))])
        SA.loft(p, [[(q[0], q[1], q[2]) for q in r] for r in rings], 'gunmetal')
        p.parent = Matrix.Identity(4)
    p.cyl((0, 0, -0.012), 0.026, 0.026, 0.024, 'hawk3', seg=10)
    # detail pass: a spinner cone on the hub, dark blade tips
    p.cyl((0, 0, 0.012), 0.02, 0.006, 0.02, 'gunmetal', seg=8, deco=True)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.box((math.cos(a) * 0.134, math.sin(a) * 0.134, 0.0), (0.016, 0.048, 0.014), 'gunmetal', rot=(14, 0, math.degrees(a)), deco=True)
    p.build('BOT_HAWK_Rotor', bevel=False, hull=0.006)
    # chin turret (origin = pivot, barrels along -Y): a smooth ball, two tapered barrels with vented jackets
    p = Part(pal)
    p.sphere((0, 0, 0), 0.065, 'hawk', seg=(12, 6))
    for sx in (-1, 1):
        p.cyl((sx * 0.025, -0.03, -0.005), 0.018, 0.013, 0.16, 'gunmetal', seg=8, rot=(90, 0, 0))
        p.cyl((sx * 0.025, -0.18, -0.005), 0.02, 0.022, 0.03, 'ink', seg=8, rot=(90, 0, 0))
    p.cyl((0, -0.035, 0), 0.0675, 0.0675, 0.02, 'plate', seg=12, rot=(90, 0, 0), caps=False, deco=True)
    # detail pass: vented barrel jackets, curved side cheeks with a sensor lens, an ammo feed on top
    for sx in (-1, 1):
        p.cyl((sx * 0.025, -0.07, -0.005), 0.0215, 0.0195, 0.06, 'hawk', seg=8, rot=(90, 0, 0), deco=True)
        for y in (-0.085, -0.105):
            p.box((sx * 0.025, y, 0.0135), (0.008, 0.01, 0.006), 'ink', deco=True)
        a0 = -40 if sx > 0 else 140
        with SA.at_frame(p, Matrix.Rotation(math.radians(90), 4, 'X')):
            SA.shell(p, [(-0.035, 0.07, 0.07, 0.01), (0.035, 0.07, 0.07, 0.01)], a0, a0 + 80, 'hawk2', k=3, deco=True, cham=1.0)
    p.box((0.072, -0.02, 0.008), (0.004, 0.016, 0.016), 'lens', deco=True)
    with SA.at_frame(p, Matrix.Translation((0, 0.01, 0.054))):
        SA.slab(p, 0.02, 0.025, 0.02, 0.008, 0.004, 'gunmetal', nc=1, deco=True)
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
    import bot_shapes_ground as SG
    XA = Matrix.Rotation(math.radians(90), 4, 'Y')                                      # lathe axis Z -> X
    # weight in the clamp: grip through the clamp, a smooth bullet-shaped iron weight with an amber band, the chain ring
    p = Part(pal)
    p.cyl((-0.08, 0, 0), 0.021, 0.021, 0.19, 'ink', seg=8, rot=(0, 90, 0))
    p.parent = XA
    p.lathe([(0.0, 0.105), (0.036, 0.105), (0.046, 0.116), (0.048, 0.155), (0.043, 0.19), (0.03, 0.208), (0.016, 0.224),
             (0.0, 0.226)], 'gunmetal', seg=12)
    p.lathe([(0.053, 0.14), (0.053, 0.16)], 'amber', seg=12, deco=True)
    p.parent = Matrix.Identity(4)
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

    # sickle: ring, tapered wrapped wooden handle out along -Y, rounded steel ferrule and collar, curved kama blade
    # along +X (edge toward +Y) with a chamfered spine and a ground edge
    p = Part(pal)
    K = Matrix.Diagonal(Vector((1.4, 1.4, 1.4, 1)))          # drawn 40 % up so it reads at fighting range
    YA = Matrix.Rotation(math.radians(90), 4, 'X')           # lathe axis Z -> -Y
    p.parent = K @ Matrix.Rotation(math.radians(90), 4, 'Y')
    _torus(p, 0.018, 0.006, 'chain', seg=6)
    p.parent = K
    p.cyl((0, -0.022, 0), 0.016, 0.021, 0.025, 'gunmetal', seg=10, rot=(90, 0, 0))
    SG.tlimb(p, (0, -0.045, 0), (0, -0.375, 0), 0.021, 0.025, 'kwood', seg=10)
    for y in (-0.09, -0.15, -0.21, -0.27):
        p.cyl((0, y, 0), 0.028, 0.028, 0.018, 'ink', seg=10, rot=(90, 0, 0), caps=False, deco=True)
    p.parent = K @ Matrix.Translation((0, -0.37, 0)) @ YA
    p.lathe([(0.0, 0.0), (0.026, 0.0), (0.031, 0.007), (0.031, 0.043), (0.026, 0.05), (0.0, 0.05)], 'steel', seg=10)
    p.parent = K @ Matrix.Translation((0, -0.395, 0))
    st = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = 0.012 + 0.31 * t
        curve = 0.13 * t * t
        w = 0.074 - 0.04 * t
        st.append((x, -w / 2 + curve, w / 2 + curve, 0.0085 - 0.003 * t, 0.6))
    SG.blade(p, st, (0.37, 0.19, 0.0), 'blade', 'paper')
    p.parent = K
    SG.rbox(p, (-0.03, -0.395, 0), (0.05, 0.044, 0.03), 'steel', r=0.012, n=1, c=0.006)   # spine knob behind the blade
    p.build('BOT_BLADER_Kusari', bevel=False, hull=0.009)


# ================================================================ JET TROOPER (levels 35+)
# A tall bipedal combat robot on a jet back unit in sleek, angular hard-surface armour (near-black, the black-ops
# soldiers' colours): flat faceted plates with one crisp chamfer on every edge, layered over slimmer faceted cores
# (8-sided where a part must read round), a narrow waist under a broad V-fronted chest, swept angular pauldrons, a slim
# faceted helmet with a V visor carrying the one sensor slit (no face, no eyes), slender segmented limbs, a sleek flight
# pack with swept fins. A bullet launcher fixed to the right hand, held low (receiver, rail, magazine, vented barrel
# shroud, twin barrels with a muzzle brake). On the back unit two glowing thruster nozzles and two telescoping arms
# (PodArm) that raise an angular rocket pod each (Pod): the pod's lid (Lid) flips open on the top front edge to show
# three tubes with rocket tips inside. Element accents are in the KEY colours 'plate' / 'plate2' (painted per robot by
# the game: electric blue, acid green, explosive orange): the shoulder edges, cannon tips, tube rims, the lids' edges;
# the glowing seams (Seam: abdomen gaps, sternum, nozzle cores) and the sensor slit (Light) are drawn in the light
# material. Parts are posed like the Soldier's rigid parts (origins on their joints); sockets give the joints, the pod
# arms, the nozzles, the muzzle and the tube mouths.
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


def _drum(p, c, r, w, color, seg=8):
    """an 8-sided joint drum along X centred on c (shoulder, elbow, hip and knee servos)"""
    p.cyl((c[0] - w / 2, c[1], c[2]), r, r, w, color, seg=seg, rot=(0, 90, 0))


def _mx(poly, s):
    """an outline mirrored across local X for the s = -1 side"""
    return [(x * s, y) for x, y in poly]


def _jet_arm(p, hand, pole, la, lb, side):
    """an 8-sided shoulder drum, a slim faceted upper arm under a flat outer plate, the elbow drum, a faceted gauntlet
    flared at the back with a layered guard plate, a wrist band"""
    import bot_shapes_air as SA
    e = Vector(_elbow((0, 0, 0), hand, la, lb, pole))
    h = Vector(hand)
    out = Vector((side, 0.0, 0.0))
    _drum(p, (0, 0, 0), 0.082, 0.15, 'gunmetal')
    L1, L2 = e.length, (h - e).length
    p.parent = _jframe((0, 0, 0), e, out)
    SA.flimb(p, [(0.03, 0.05, 0.05, 0.05, 0.018), (L1 * 0.45, 0.06, 0.058, 0.064, 0.021, 0, 0.004), (L1 * 0.95, 0.05, 0.05, 0.05, 0.018)], 'jet2')
    SA.plate_at(p, (0, 0.058, L1 * 0.47), (0, 1, 0), (0, 0, 1),
                [(-0.058, -L1 * 0.33), (0.058, -L1 * 0.33), (0.072, 0.0), (0.06, L1 * 0.36), (-0.06, L1 * 0.36), (-0.072, 0.0)], 0.026, 'jet', z0=-0.01)
    p.parent = Matrix.Identity(4)
    _drum(p, tuple(e), 0.058, 0.11, 'gunmetal')
    p.parent = _jframe(e, h, out)
    SA.flimb(p, [(0.02, 0.046, 0.046, 0.05, 0.016), (L2 * 0.3, 0.062, 0.056, 0.08, 0.022, 0, 0.012), (L2 * 0.68, 0.06, 0.054, 0.076, 0.022, 0, 0.01),
                 (L2 * 0.84, 0.048, 0.048, 0.054, 0.018)], 'jet')
    SA.plate_at(p, (0, 0.086, L2 * 0.47), (0, 1, 0), (0, 0, 1),
                [(-0.045, -L2 * 0.3), (0.045, -L2 * 0.3), (0.054, L2 * 0.12), (0.0, L2 * 0.26), (-0.054, L2 * 0.12)], 0.02, 'jet3', z0=-0.01)   # guard plate
    SA.flimb(p, [(L2 * 0.83, 0.058, 0.058, 0.058, 0.02), (L2 * 0.84 + 0.04, 0.056, 0.056, 0.056, 0.02)], 'gunmetal')   # wrist band
    p.parent = Matrix.Identity(4)
    return e


def build_jet(pal):
    import bot_shapes_air as SA
    UP, BACK = (0, 0, 1), (0, 1, 0)
    # ---- hips: a faceted pelvis core, an octagonal belt, an angular codpiece with a layered plate, flat tassets angled
    # out over the hip joints, a rear plate
    p = Part(pal)
    SA.flimb(p, [(0.905, 0.085, 0.07, 0.07, 0.03), (0.95, 0.135, 0.095, 0.095, 0.04), (1.07, 0.145, 0.105, 0.105, 0.045)], 'jet2')
    SA.flimb(p, [(1.062, 0.16, 0.12, 0.12, 0.05), (1.072, 0.172, 0.132, 0.132, 0.055), (1.128, 0.172, 0.132, 0.132, 0.055),
                 (1.138, 0.16, 0.12, 0.12, 0.05)], 'jet3')                                                             # belt
    cod = [(-0.05, -0.085), (0.05, -0.085), (0.095, 0.025), (0.075, 0.075), (-0.075, 0.075), (-0.095, 0.025)]
    SA.plate_at(p, (0, -0.104, 0.985), (0, -1, -0.18), UP, cod, 0.036, 'jet', z0=-0.012)                                  # codpiece
    SA.plate_at(p, (0, -0.124, 0.975), (0, -1, -0.18), UP, [(-0.025, -0.07), (0.025, -0.07), (0.05, 0.0), (0.04, 0.05), (-0.04, 0.05), (-0.05, 0.0)],
                0.012, 'jet3', ch=0.005, z0=-0.001)                                                                    # its layered centre plate
    tas = [(-0.075, -0.095), (0.075, -0.095), (0.092, 0.02), (0.07, 0.078), (-0.07, 0.078), (-0.092, 0.02)]
    for s in (-1, 1):
        SA.plate_at(p, (s * 0.192, 0.0, 0.955), (s, 0, -0.35), UP, tas, 0.028, 'jet', z0=-0.01)                          # tassets
    SA.plate_at(p, (0, 0.122, 0.985), (0, 1, -0.2), UP, [(-0.1, -0.065), (0.1, -0.065), (0.122, 0.035), (0.09, 0.07), (-0.09, 0.07), (-0.122, 0.035)],
                0.03, 'jet', z0=-0.01)                                                                                 # rear plate
    hips = p.build('BOT_JET_Hips', bevel=False)
    for i, sx in enumerate((-1, 1)):
        socket('BOT_JET_HIP%d' % i, hips, (sx * J_HIPX, 0, J_HIP))
    socket('BOT_JET_WAIST', hips, (0, 0, J_WAIST))

    # ---- thigh (origin on the hip joint): the hip drum, a slim faceted thigh, a long front plate with a layered upper
    # plate, flat side plates, the knee axle
    p = Part(pal)
    _drum(p, (0, 0, 0), 0.078, 0.15, 'gunmetal')
    SA.flimb(p, [(-0.45, 0.05, 0.055, 0.055, 0.018), (-0.2, 0.072, 0.08, 0.082, 0.026), (-0.04, 0.066, 0.074, 0.076, 0.024)], 'jet2')
    SA.plate_at(p, (0, -0.1, -0.22), (0, -1, 0.06), UP, [(-0.06, -0.17), (0.06, -0.17), (0.085, -0.06), (0.09, 0.12), (0.06, 0.16), (-0.06, 0.16),
                                                           (-0.09, 0.12), (-0.085, -0.06)], 0.04, 'jet', z0=-0.026)   # front plate
    SA.plate_at(p, (0, -0.112, -0.16), (0, -1, 0.06), UP, [(-0.06, -0.06), (0.06, -0.06), (0.072, 0.03), (0.05, 0.075), (-0.05, 0.075), (-0.072, 0.03)],
                0.016, 'jet3', ch=0.006, z0=-0.004)                                                                     # layered upper plate
    for s in (-1, 1):
        SA.plate_at(p, (s * 0.066, 0.004, -0.23), (s, 0, 0), UP, [(-0.05, -0.13), (0.05, -0.13), (0.06, 0.1), (0.0, 0.14), (-0.06, 0.1)],
                    0.022, 'jet', z0=-0.008)                                                                            # side plates
    _drum(p, (0, 0, -0.45), 0.044, 0.1, 'gunmetal', seg=6)                                                            # knee axle
    p.build('BOT_JET_Thigh', bevel=False)

    # ---- shin + foot (origin on the knee): the knee drum under an angular knee cop, a slim faceted calf, a long flat
    # shin guard with a raised spine, calf piston, ankle, a faceted boot with an angled toe cap
    p = Part(pal)
    _drum(p, (0, 0, 0), 0.066, 0.13, 'gunmetal')
    SA.plate_at(p, (0, -0.075, -0.03), (0, -1, 0.3), UP, [(-0.06, -0.085), (0.06, -0.085), (0.085, -0.01), (0.06, 0.075), (0.0, 0.095), (-0.06, 0.075),
                                                           (-0.085, -0.01)], 0.04, 'jet3', z0=-0.014)                   # knee cop
    SA.flimb(p, [(-0.45, 0.042, 0.042, 0.048, 0.015), (-0.26, 0.056, 0.053, 0.072, 0.02, 0, 0.008), (-0.05, 0.056, 0.056, 0.06, 0.02)], 'jet2')
    SA.plate_at(p, (0, -0.06, -0.285), (0, -1, 0.04), UP, [(-0.045, -0.15), (0.045, -0.15), (0.072, -0.08), (0.075, 0.1), (0.05, 0.14), (-0.05, 0.14),
                                                           (-0.075, 0.1), (-0.072, -0.08)], 0.03, 'jet', z0=-0.01)       # shin guard
    SA.plate_at(p, (0, -0.08, -0.28), (0, -1, 0.04), UP, [(-0.016, -0.12), (0.016, -0.12), (0.022, 0.1), (0.0, 0.125), (-0.022, 0.1)],
                0.012, 'jet3', ch=0.005, z0=-0.001)                                                                     # its spine
    p.limb((0, 0.06, -0.18), (0, 0.05, -0.40), 0.018, 0.018, 'steel', seg=6)                                          # calf piston
    with SA.at_frame(p, SA.frame((0, 0.125, 0), (0, -1, 0))):
        rings = []
        for d, hw, z0, z1, r in ((0.0, 0.055, -0.535, -0.475, 0.016), (0.025, 0.074, -0.54, -0.44, 0.024), (0.17, 0.08, -0.54, -0.445, 0.026),
                                 (0.29, 0.07, -0.54, -0.49, 0.02), (0.335, 0.05, -0.538, -0.512, 0.008)):
            rings.append(SA.ring_rr(hw, (z1 - z0) / 2, r, 1, d, 0, (z0 + z1) / 2))
        SA.loft(p, rings, 'jet2')
    SA.plate_at(p, (0, -0.12, -0.472), (0, -0.5, 1), BACK, [(-0.06, -0.05), (0.06, -0.05), (0.072, 0.02), (0.045, 0.05), (-0.045, 0.05), (-0.072, 0.02)],
                0.018, 'jet', z0=-0.006)                                                                                # toe cap
    p.build('BOT_JET_Shin', bevel=False)

    # ---- torso (origin on the waist): a narrow faceted waist under three octagonal abdomen bands (the seams glow in
    # the gaps), a broad V-fronted chest with two angled pec plates (the sternum seam glows in the groove between
    # them), the gold reactor (weak point) on a hexagonal boss, a faceted collar, swept angular pauldrons (a faceted
    # cap, a swept top plate, a flat outer plate; the element line along their edges), the flight pack with swept
    # fins, 8-sided nozzles and the pod-arm hinges
    sx_, sy_, sz_ = J_SHOULDER
    p = Part(pal)
    SA.flimb(p, [(-0.06, 0.115, 0.125, 0.11, 0.035), (0.06, 0.112, 0.13, 0.11, 0.035), (0.2, 0.145, 0.13, 0.125, 0.04)], 'jet2')
    for i, (z0, z1) in enumerate(((-0.025, 0.025), (0.04, 0.09), (0.105, 0.155))):
        a = 0.138 + 0.004 * i
        SA.flimb(p, [(z0, a - 0.01, 0.138, 0.118, 0.05), (z0 + 0.01, a, 0.148, 0.128, 0.055), (z1 - 0.01, a, 0.148, 0.128, 0.055),
                     (z1, a - 0.01, 0.138, 0.118, 0.05)], 'jet3' if i == 1 else 'jet')                                  # abdomen bands
    SA.flimb(p, [(0.15, 0.15, 0.14, 0.14, 0.05, 0, 0, 0.0, 0.0), (0.19, 0.198, 0.165, 0.165, 0.06, 0, 0, 0.008, 0.0),
                 (0.30, 0.238, 0.172, 0.175, 0.075, 0, 0, 0.02, 0.0), (0.45, 0.236, 0.17, 0.175, 0.075, 0, 0, 0.02, 0.0),
                 (0.53, 0.2, 0.145, 0.155, 0.06, 0, 0, 0.008, 0.0), (0.565, 0.14, 0.1, 0.12, 0.04, 0, 0, 0.004, 0.0)], 'jet')   # chest
    for s in (-1, 1):
        pec = [(-0.095, -0.07), (0.06, -0.085), (0.105, -0.02), (0.1, 0.06), (0.04, 0.085), (-0.095, 0.085)]
        SA.plate_at(p, (s * 0.105, -0.18, 0.41), (s * 0.3, -1, 0.12), UP, _mx(pec, s), 0.032, 'jet3', z0=-0.012)   # pec plates
    with SA.at_frame(p, SA.frame((0, -0.15, 0.255), (0, -1, 0))):
        SA.lathe_r(p, [(0.074, 0.0), (0.08, 0.026), (0.068, 0.042)], 'jet2', seg=6, phase=math.pi / 6)                 # reactor boss
    p.cyl((0, -0.196, 0.255), 0.05, 0.05, 0.03, 'core', seg=12, rot=(90, 0, 0))
    p.cyl((0, -0.194, 0.255), 0.06, 0.06, 0.008, 'gunmetal', seg=12, rot=(90, 0, 0), caps=False, deco=True)
    SA.flimb(p, [(0.5, 0.11, 0.105, 0.105, 0.035), (0.6, 0.1, 0.095, 0.095, 0.03)], 'jet3')                           # collar
    SA.flimb(p, [(0.548, 0.116, 0.112, 0.112, 0.04), (0.562, 0.116, 0.112, 0.112, 0.04)], 'gunmetal', deco=True)       # collar band
    top = [(-0.08, -0.16), (0.07, -0.14), (0.1, -0.04), (0.095, 0.11), (0.035, 0.22), (-0.065, 0.17), (-0.09, 0.0)]
    side = [(-0.13, -0.06), (0.12, -0.06), (0.15, 0.03), (0.11, 0.085), (-0.1, 0.085), (-0.15, 0.025)]
    for s in (-1, 1):
        S = Vector((s * sx_, sy_, sz_))
        # pauldron: a faceted cap over the shoulder drum, a swept top plate angled out, a flat outer plate; the element
        # line along the outer plate's lower edge and the top plate's outer edge
        p.parent = Matrix.Translation(S) @ Matrix.Rotation(math.radians(-s * 12), 4, 'Y')
        cx = s * 0.012
        SA.flimb(p, [(-0.07, 0.112, 0.13, 0.13, 0.04, cx, 0), (-0.045, 0.126, 0.148, 0.15, 0.05, cx, 0), (0.05, 0.12, 0.142, 0.146, 0.05, cx, 0),
                     (0.1, 0.086, 0.104, 0.112, 0.042, cx * 0.5, 0), (0.128, 0.04, 0.05, 0.06, 0.016, 0, 0)], 'jet')
        p.parent = Matrix.Identity(4)
        SA.plate_at(p, S + Vector((s * 0.06, 0.025, 0.1)), (s * 0.6, 0.08, 1), BACK, _mx(top, s), 0.03, 'jet3', z0=-0.014)
        F = SA.frame(S + Vector((s * 0.128, 0.01, -0.005)), (s, 0, -0.3), UP)
        with SA.at_frame(p, F):
            SA.plate(p, _mx(side, s), 0.026, 'jet', z0=-0.01)
            SA.sweep(p, [(-0.11 * s, -0.04, 0.016), (0.0, -0.04, 0.016), (0.11 * s, -0.04, 0.016)], [UP] * 3, 0.014, 0.005, 'plate', off=-0.001)
        with SA.at_frame(p, SA.frame(S + Vector((s * 0.06, 0.025, 0.1)), (s * 0.6, 0.08, 1), BACK)):
            SA.sweep(p, [(s * 0.077, -0.07, 0.016), (s * 0.08, 0.02, 0.016), (s * 0.075, 0.1, 0.016)], [UP] * 3, 0.012, 0.005, 'plate', off=-0.001)
    # flight pack: a faceted pack, a chamfered back panel with vents, swept fins, 8-sided nozzles, the pod-arm hinges
    SA.flimb(p, [(0.10, 0.13, 0.055, 0.055, 0.03, 0, 0.255), (0.13, 0.165, 0.07, 0.07, 0.04, 0, 0.255), (0.40, 0.212, 0.082, 0.082, 0.045, 0, 0.255),
                 (0.48, 0.196, 0.078, 0.078, 0.045, 0, 0.255), (0.51, 0.162, 0.062, 0.062, 0.035, 0, 0.255)], 'jet')
    with SA.at_frame(p, SA.frame((0, 0.325, 0), (0, 1, 0))):
        SA.loft(p, [SA.ring_rr(0.13, 0.11, 0.03, 1, 0.0, 0, 0.33), SA.ring_rr(0.13, 0.11, 0.03, 1, 0.012, 0, 0.33),
                    SA.ring_rr(0.118, 0.098, 0.022, 1, 0.02, 0, 0.33)], 'jet3')
    for z in (0.27, 0.31, 0.35):
        p.box((0, 0.345, z), (0.18, 0.008, 0.012), 'ink', deco=True)                                        # vent slats
    fin = [(-0.08, -0.12), (0.04, -0.09), (0.085, 0.09), (0.05, 0.14), (-0.06, 0.04)]
    for s in (-1, 1):
        SA.plate_at(p, (s * 0.2, 0.275, 0.36), (s, 0.4, 0.0), UP, _mx(fin, s), 0.024, 'jet3', z0=-0.012)          # swept fins
        nx, ny, nz = J_NOZ
        with SA.at_frame(p, Matrix.Translation((s * nx, ny, 0))):
            SA.lathe_r(p, [(0.062, 0.03), (0.05, 0.075), (0.066, 0.21)], 'gunmetal', seg=8, phase=math.pi / 8)    # nozzle
            SA.lathe_r(p, [(0.0585, 0.112), (0.0585, 0.126)], 'jet3', seg=8, phase=math.pi / 8, deco=True)         # nozzle band
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
    p.box((0, -0.196, 0.405), (0.014, 0.012, 0.12), 'light')
    for s in (-1, 1):
        nx, ny, nz = J_NOZ
        p.cyl((s * nx, ny, nz - 0.006), 0.042, 0.042, 0.004, 'light', seg=8, rot=(0, 0, 22.5))                      # nozzle cores
    strip_hull(p.build('BOT_JET_Seam', bevel=False, hull=0.003))

    # ---- head (origin on the neck): a slim faceted helmet, longer than wide, its front a shallow V; a dark V visor band
    # carrying the one sensor slit, a faceted crest, hexagonal ear modules, an antenna
    p = Part(pal)
    SA.flimb(p, [(-0.05, 0.06, 0.06, 0.06, 0.02), (0.05, 0.065, 0.065, 0.065, 0.022)], 'jet3')
    SA.flimb(p, [(-0.03, 0.076, 0.076, 0.076, 0.026), (-0.01, 0.076, 0.076, 0.076, 0.026)], 'gunmetal', deco=True)     # neck band
    SA.flimb(p, [(0.0, 0.066, 0.10, 0.08, 0.03, 0, 0, 0.01, 0.0), (0.04, 0.092, 0.122, 0.115, 0.045, 0, 0, 0.016, 0.004),
                 (0.08, 0.102, 0.132, 0.135, 0.05, 0, 0, 0.018, 0.005), (0.17, 0.102, 0.132, 0.138, 0.05, 0, 0, 0.018, 0.005),
                 (0.22, 0.092, 0.118, 0.128, 0.05, 0, 0, 0.015, 0.004), (0.26, 0.064, 0.08, 0.095, 0.035, 0, 0, 0.01, 0.002),
                 (0.28, 0.03, 0.035, 0.045, 0.012, 0, 0, 0.004, 0.0)], 'jet')
    # the V visor: a band across the two front facets and onto the corner chamfers (the helmet's z 0.08-0.17 ring)
    vpts = [(-0.092, -0.092), (-0.052, -0.132), (0.0, -0.15), (0.052, -0.132), (0.092, -0.092)]

    def vpath():
        nrm = []
        for i, q in enumerate(vpts):
            a, b = Vector(vpts[max(i - 1, 0)]), Vector(vpts[min(i + 1, len(vpts) - 1)])
            d = (b - a).normalized()
            n = Vector((d.y, -d.x))
            if n.y > 0:
                n = -n
            nrm.append((n.x, n.y, 0.0))
        return [(q[0], q[1], 0.125) for q in vpts], nrm
    SA.sweep(p, *vpath(), 0.078, 0.0105, 'jet2', off=-0.001, deco=False)                                             # visor band
    sp, sn = vpath()
    sp = [(q[0] + n[0] * 0.0095, q[1] + n[1] * 0.0095, q[2]) for q, n in zip(sp, sn)]
    SA.sweep(p, sp, sn, 0.022, 0.0045, 'ink', off=-0.001)                                        # the sensor slit
    with SA.at_frame(p, SA.frame((0, -0.01, 0.235), (0, 1, 0))):                                                      # crest
        SA.loft(p, [SA.ring_rr(0.014, 0.02, 0.01, 1, -0.10, 0, 0.0), SA.ring_rr(0.02, 0.035, 0.012, 1, -0.07, 0, 0.022),
                    SA.ring_rr(0.02, 0.035, 0.012, 1, 0.07, 0, 0.022), SA.ring_rr(0.014, 0.022, 0.01, 1, 0.125, 0, -0.01)], 'jet3')
    for s in (-1, 1):
        p.cyl((s * 0.094, -0.012, 0.125), 0.045, 0.045, 0.034, 'jet3', seg=6, rot=(0, s * 90, 0))                     # ear modules
        p.cyl((s * 0.128, -0.012, 0.125), 0.03, 0.026, 0.016, 'gunmetal', seg=6, rot=(0, s * 90, 0))
    p.cyl((0.075, 0.09, 0.2), 0.008, 0.008, 0.15, 'ink', seg=4)
    p.cyl((0.075, 0.09, 0.35), 0.013, 0.004, 0.024, 'gunmetal', seg=4, deco=True)
    head = p.build('BOT_JET_Head', bevel=False)
    socket('BOT_JET_SLIT', head, (0, -0.168, 0.125))
    # the slit light: a bar along the V visor, 6 mm proud of the slit (origin = BOT_JET_SLIT)
    p = Part(pal)
    lp = [(q[0] + n[0] * 0.0095, q[1] + n[1] * 0.0095 + 0.168, 0.0) for q, n in zip(*vpath())][1:4]
    lp = [(lp[0][0] * 0.95, lp[0][1], 0.0), lp[1], (lp[2][0] * 0.95, lp[2][1], 0.0)]
    SA.sweep(p, lp, sn[1:4], 0.012, 0.004, 'light', off=0.0045, deco=False)
    p.build('BOT_JET_Light', bevel=False, hull=0.004)

    # ---- arms (origin on the shoulder); the right one carries the bullet launcher, held low, barrels along -Y
    p = Part(pal)
    _jet_arm(p, J_HAND_R, (0.2, 1.0, -0.3), 0.30, 0.32, -1)
    hx, hy, hz = J_HAND_R
    with SA.at_frame(p, Matrix.Translation((hx, hy, hz - 0.045))):
        SA.slab(p, 0.045, 0.045, 0.09, 0.02, 0.012, 'jet2', nc=1)                                          # fist
    with SA.at_frame(p, SA.frame((hx, hy + 0.10, hz + 0.065), (0, -1, 0))):                                # receiver
        SA.loft(p, [SA.ring_rr(0.042, 0.047, 0.016, 1, 0.0), SA.ring_rr(0.05, 0.055, 0.022, 1, 0.014), SA.ring_rr(0.05, 0.055, 0.022, 1, 0.39),
                    SA.ring_rr(0.044, 0.048, 0.016, 1, 0.40)], 'gunmetal')
    p.box((hx, hy - 0.10, hz + 0.126), (0.036, 0.30, 0.012), 'jet3')                                      # top rail
    for k in range(2):
        p.box((hx, hy - 0.16 + 0.1 * k, hz + 0.1355), (0.046, 0.012, 0.008), 'ink', deco=True)
    with SA.at_frame(p, Matrix.Translation((hx, hy - 0.17, hz - 0.12)) @ Matrix.Rotation(math.radians(-12), 4, 'X')):
        p.box((0, 0, 0.07), (0.06, 0.09, 0.14), 'jet2')                                                     # magazine
    with SA.at_frame(p, SA.frame((hx, hy - 0.29, hz + 0.07), (0, -1, 0))):                                 # barrel shroud
        SA.flimb(p, [(0.0, 0.04, 0.04, 0.04, 0.014), (0.012, 0.046, 0.046, 0.046, 0.017), (0.205, 0.044, 0.044, 0.044, 0.016),
                     (0.222, 0.036, 0.036, 0.036, 0.012)], 'jet')
    for k in range(2):
        for s in (-1, 1):
            p.box((hx + s * 0.0455, hy - 0.36 - 0.06 * k, hz + 0.07), (0.008, 0.024, 0.03), 'ink', deco=True)   # vents
    for sx in (-0.022, 0.022):
        p.cyl((hx + sx, hy - 0.50, hz + 0.07), 0.017, 0.017, 0.17, 'steel', seg=6, rot=(90, 0, 0))   # twin barrels
        p.cyl((hx + sx, hy - 0.655, hz + 0.07), 0.022, 0.022, 0.014, 'plate', seg=6, rot=(90, 0, 0), caps=False, deco=True)   # cannon tips
    with SA.at_frame(p, SA.frame((hx, hy - 0.595, hz + 0.07), (0, -1, 0))):                                 # muzzle brake
        SA.flimb(p, [(0.0, 0.05, 0.04, 0.04, 0.015), (0.05, 0.048, 0.038, 0.038, 0.014)], 'gunmetal')
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
        p.limb((hx + x, hy - 0.042, hz - 0.025), (hx + x, hy - 0.05, hz - 0.095), 0.011, 0.008, 'gunmetal', seg=4)   # claw fingers
    p.limb((hx + 0.04, hy - 0.01, hz - 0.005), (hx + 0.055, hy - 0.02, hz - 0.06), 0.012, 0.009, 'gunmetal', seg=4)   # thumb
    p.build('BOT_JET_ArmL', bevel=False)

    # ---- pod arm (origin = its hinge on the back unit): a telescoping faceted strut that raises the pod (the game
    # stretches it along its length while the pod rises), a piston, a bracket at the top (socket BOT_JET_PODTOP)
    p = Part(pal)
    p.cyl((-0.035, 0, 0), 0.028, 0.028, 0.07, 'gunmetal', seg=6, rot=(0, 90, 0))
    SA.flimb(p, [(0.0, 0.03, 0.026, 0.026, 0.01), (0.2, 0.024, 0.02, 0.02, 0.008)], 'jet3')
    p.cyl((0, 0, 0.19), 0.016, 0.016, 0.06, 'steel', seg=6)
    p.limb((0, 0.03, 0.02), (0, 0.03, 0.20), 0.011, 0.011, 'steel', seg=6)
    p.cyl((-0.04, 0, 0.255), 0.026, 0.026, 0.08, 'gunmetal', seg=6, rot=(0, 90, 0))
    arm = p.build('BOT_JET_PodArm', bevel=False, hull=0.008)
    socket('BOT_JET_PODTOP', arm, (0, 0, J_ARM_LEN))

    # ---- rocket pod (origin = its mount on the arm): a sleek angular launcher, wedged at the tail, chamfered all
    # round, a layered top plate, flat side rails cut back at the front, three 8-sided barrels along -Y (element-colour
    # rims, rocket tips inside); the lid hinges on the top front edge
    p = Part(pal)
    with SA.at_frame(p, SA.frame((0, 0.10, 0), (0, -1, 0))):
        SA.flimb(p, [(0.0, 0.074, 0.054, 0.054, 0.024, 0, 0.10), (0.06, 0.11, 0.09, 0.09, 0.036, 0, 0.10), (0.318, 0.11, 0.09, 0.09, 0.036, 0, 0.10),
                     (0.338, 0.098, 0.078, 0.078, 0.03, 0, 0.10)], 'jet2')
        SA.loft(p, [SA.ring_rr(0.08, 0.012, 0.008, 1, 0.04, 0, 0.19), SA.ring_rr(0.08, 0.012, 0.008, 1, 0.28, 0, 0.19)], 'jet')   # top plate
    rail = [(-0.15, -0.055), (0.1, -0.055), (0.13, 0.0), (0.1, 0.055), (-0.15, 0.055)]
    for s in (-1, 1):
        SA.plate_at(p, (s * 0.11, -0.07, 0.10), (s, 0, 0), UP, _mx(rail, -s), 0.018, 'jet', z0=-0.006)               # side rails
    for x in (-0.045, 0.045):
        p.cyl((x, 0.096, 0.10), 0.03, 0.03, 0.01, 'ink', seg=6, rot=(-90, 0, 0), deco=True)                   # rear exhaust ports
    for x in (-0.068, 0.0, 0.068):
        p.cyl((x, -0.235, 0.10), 0.032, 0.032, 0.026, 'jet3', seg=8, rot=(90, 0, 0))                      # launcher barrel
        p.cyl((x, -0.25, 0.10), 0.036, 0.036, 0.016, 'plate', seg=8, rot=(90, 0, 0), caps=False, deco=True)   # rim
        p.cyl((x, -0.2615, 0.10), 0.024, 0.024, 0.004, 'ink', seg=6, rot=(90, 0, 0), deco=True)      # bore
        p.cyl((x, -0.252, 0.10), 0.017, 0.0, 0.02, 'red', seg=6, rot=(90, 0, 0), deco=True)         # rocket tip
    p.box((0, 0.0, 0.0), (0.08, 0.06, 0.03), 'gunmetal')                                         # mount
    pod = p.build('BOT_JET_Pod', bevel=False)
    socket('BOT_JET_LID', pod, (0, -0.28, 0.19))
    for k, x in enumerate((-0.068, 0.0, 0.068)):
        socket('BOT_JET_TUBE%d' % k, pod, (x, -0.30, 0.10))
    # lid (origin = hinge): a chamfered plate, a raised centre rib, its inner edge in the element colour
    p = Part(pal)
    with SA.at_frame(p, SA.frame((0, -0.002, 0), (0, -1, 0))):
        SA.loft(p, [SA.ring_rr(0.115, 0.09, 0.03, 1, 0.0, 0, -0.09), SA.ring_rr(0.115, 0.09, 0.03, 1, 0.012, 0, -0.09),
                    SA.ring_rr(0.105, 0.08, 0.024, 1, 0.02, 0, -0.09)], 'jet')
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
