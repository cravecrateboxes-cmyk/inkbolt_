"""INKBOLT asset family: gear (loot). Weapon attachments that ride the first-person guns, the shield cell, and the
world loot drop (a capsule pedestal; the game adds the rarity beam).

  GEAR_Grip         vertical foregrip; origin = top of the rail clamp (hangs down -Z)
  GEAR_Scope        tube scope on a cantilever riser; origin = optical axis at the eyepiece (socket GEAR_Scope_EYE);
                    the tube is open (lens rings + a duplex ink reticle) so aiming looks through it
  GEAR_Acid         acid muzzle: silencer can with a green glass window and a side vial; origin = rear face on the
                    bore axis (rides the gun's MUZZLE socket, extends +Y); GEAR_Acid_TIP = the new muzzle point;
                    GEAR_Acid_Glow = the glass core (no outline; the game pulses it unlit)
  GEAR_ShieldCell   hex shield battery (pickup look)
  LOOT_Capsule      drop pod pedestal (world size); LOOT_Glow = its light ring + emitter (recoloured per rarity in game)

Same conventions as fps-weapons: +Y forward, +Z up, origin where the part mounts; exact primitives with chamfers;
small inner details carry no outline shell; ib_lib.check_zfight runs strict on every object.
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

V = Vector
D = math.radians
FAM = 'gear'
ib_lib.GLB[FAM] = 'fps-gear.glb'
ib_lib.CFG[FAM] = (0.004, 0.0035)          # attachments use the viewmodel shell; world pieces pass their own
HULL_VM = 0.0035
HULL_WORLD = 0.012

_LIFT = {'gunmetal': '#5A586D'}
ib_lib.PALETTES[FAM] = [(n, _LIFT.get(n, h)) for n, h in BASE] + [
    ('gun2', '#48475A'), ('gun3', '#6E6B85'), ('steel', '#B7BDC9'), ('steel2', '#8C92A3'),
    ('rubber', '#3B3A4A'), ('lens', '#86EAF2'), ('lens2', '#4FC3D6'),
    ('acid', '#7BE34A'), ('acid2', '#3FAE2A'), ('acid3', '#C8FF8A'),
    ('cell', '#5FD0FF'), ('cell2', '#2F8FD8'), ('cell3', '#BDF0FF'),
    ('pod', '#5A586D'), ('pod2', '#48475A'), ('pod3', '#6E6B85'), ('glow', '#FFFDF7')]


# ================================================================ geometry kit (same primitives as fam_weapons)
def ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return list(poly) if s > 0 else list(reversed(poly))


def inset2d(poly, d):
    P = [V((p[0], p[1])) for p in ccw(poly)]
    n = len(P)
    out = P
    for _ in range(8):
        out = []
        for i in range(n):
            p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % n]
            e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
            n1, n2 = V((-e1.y, e1.x)), V((-e2.y, e2.x))
            m = n1 + n2
            m = n1 if m.length < 1e-6 else m.normalized()
            out.append(p1 + m * (d / max(m.dot(n1), 0.35)))
        if all((out[(i + 1) % n] - out[i]).dot(P[(i + 1) % n] - P[i]) > 0 for i in range(n)):
            break
        d *= 0.6
    return [(p.x, p.y) for p in out]


def ngon(r, n, a0=0.0, sx=1.0, sy=1.0):
    return [(r * sx * math.cos(D(a0) + 2 * math.pi * i / n), r * sy * math.sin(D(a0) + 2 * math.pi * i / n)) for i in range(n)]


AXES = {'x': (V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))),
        'y': (V((0, 1, 0)), V((1, 0, 0)), V((0, 0, 1))),
        'z': (V((0, 0, 1)), V((1, 0, 0)), V((0, 1, 0)))}


class Kit:
    def __init__(self, pal):
        self.pal = pal
        self.m = Model(pal)
        self.bm = self.m.bm
        self.sl = self.m.shape
        self.nohull = set()
        self.xf = Matrix.Identity(4)

    def _reg(self, before, color, hull, fcol=None):
        new = [f for f in self.bm.faces if f not in before]
        self.m.nshape += 1
        sid = self.m.nshape
        mi = self.pal.index(color)
        for f in new:
            f[self.sl] = sid
            f.material_index = self.pal.index(fcol[f]) if fcol and f in fcol else mi
        if not hull:
            self.nohull.add(sid)
        return sid

    class _At:
        def __init__(self, kit, m):
            self.kit, self.m = kit, m

        def __enter__(self):
            self.old = self.kit.xf
            self.kit.xf = self.old @ self.m

        def __exit__(self, *a):
            self.kit.xf = self.old

    def at(self, loc=(0, 0, 0), rot=(0, 0, 0)):
        return Kit._At(self, mat_trs(loc, rot))

    def loft(self, rings, color, hull=True, caps=(True, True), closed=False, bands=None):
        bm = self.bm
        before = set(bm.faces)
        vr = [[bm.verts.new(self.xf @ V(p)) for p in r] for r in rings]
        fcol = {}
        nb = len(vr) if closed else len(vr) - 1
        for i in range(nb):
            a, b = vr[i], vr[(i + 1) % len(vr)]
            n = max(len(a), len(b))
            for j in range(n):
                j2 = (j + 1) % n
                if len(a) == 1:
                    q = (a[0], b[j], b[j2])
                elif len(b) == 1:
                    q = (a[j], a[j2], b[0])
                else:
                    q = (a[j], a[j2], b[j2], b[j])
                f = bm.faces.new(q)
                if bands and i < len(bands) and bands[i]:
                    fcol[f] = bands[i]
        if not closed:
            if caps[0] and len(vr[0]) >= 3:
                bm.faces.new(vr[0])
            if caps[1] and len(vr[-1]) >= 3:
                bm.faces.new(list(reversed(vr[-1])))
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        return self._reg(before, color, hull, fcol)

    def cbox(self, loc, size, color, ch=0.003, rot=(0, 0, 0), hull=True, axis=None):
        bm = self.bm
        before = set(bm.faces)
        M = self.xf @ mat_trs(loc, rot, size)
        verts = bmesh.ops.create_cube(bm, size=1.0, matrix=M)['verts']
        if ch > 0:
            edges = list({e for v in verts for e in v.link_edges})
            if axis:
                R = (self.xf @ mat_trs(loc, rot)).to_3x3().inverted()
                ai = 'xyz'.index(axis)
                edges = [e for e in edges if abs((R @ (e.verts[1].co - e.verts[0].co)).normalized()[ai]) > 0.9]
            bmesh.ops.bevel(bm, geom=edges, offset=ch, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in before])
        return self._reg(before, color, hull)

    def box(self, loc, size, color, rot=(0, 0, 0), hull=False):
        return self.cbox(loc, size, color, ch=0, rot=rot, hull=hull)

    def ext(self, prof, color, o, u, v, w, d0, d1, ch0=0.0, ch1=0.0, hull=True):
        o, u, v, w = V(o), V(u), V(v), V(w)
        P = ccw(prof)

        def ring(p2, d):
            return [o + u * p[0] + v * p[1] + w * d for p in p2]
        st = []
        if ch0 > 0:
            st.append((d0, ch0))
        st.append((d0 + ch0, 0.0))
        st.append((d1 - ch1, 0.0))
        if ch1 > 0:
            st.append((d1, ch1))
        return self.loft([ring(inset2d(P, s) if s > 0 else P, d) for d, s in st], color, hull)

    def ext_x(self, prof, x0, x1, color, ch=0.0, hull=True):
        """profile in (y, z), extruded across x"""
        return self.ext(prof, color, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), x0, x1, ch, ch, hull)

    def ext_y(self, prof, y0, y1, color, ch0=0.0, ch1=0.0, hull=True, x=0.0, z=0.0):
        """profile in (x, z), extruded along y"""
        return self.ext(prof, color, (x, 0, z), (1, 0, 0), (0, 0, 1), (0, 1, 0), y0, y1, ch0, ch1, hull)

    def ext_z(self, prof, z0, z1, color, ch0=0.0, ch1=0.0, hull=True):
        """profile in (x, y), extruded along z"""
        return self.ext(prof, color, (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), z0, z1, ch0, ch1, hull)

    def lathe(self, prof, color, axis='y', c=(0, 0, 0), seg=12, hull=True, bands=None, a0=None, closed=False, sc=(1.0, 1.0)):
        """Revolve [(t, r)] around an axis through c; r == 0 is an apex."""
        ax, u, v = AXES[axis] if isinstance(axis, str) else axis
        c = V(c)
        a0 = (math.pi / seg) if a0 is None else D(a0)
        rings = []
        for t, r in prof:
            if r < 1e-7:
                rings.append([c + ax * t])
            else:
                rings.append([c + ax * t + u * (r * sc[0] * math.cos(a0 + 2 * math.pi * k / seg)) + v * (r * sc[1] * math.sin(a0 + 2 * math.pi * k / seg)) for k in range(seg)])
        return self.loft(rings, color, hull, bands=bands, closed=closed)

    def ring(self, axis, c, t0, t1, r0, r1, color, seg=12, hull=True, a0=None, sc=(1.0, 1.0)):
        """Washer / tube with a real hole."""
        return self.lathe([(t0, r0), (t0, r1), (t1, r1), (t1, r0)], color, axis, c, seg, hull, closed=True, a0=a0, sc=sc)

    def sphere(self, loc, r, color, seg=(8, 5), hull=False):
        bm = self.bm
        before = set(bm.faces)
        bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=r, matrix=self.xf @ Matrix.Translation(loc))
        return self._reg(before, color, hull)


def finish(name, kit, ht=HULL_VM):
    bm = kit.bm
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
    obj = build_object(name, kit.m, 0, ht)
    if kit.nohull:
        b2 = bmesh.new()
        b2.from_mesh(obj.data)
        hl = b2.verts.layers.float_vector.get('_HULL')
        sl = b2.faces.layers.int.get('shape_id')
        kill = [f for f in b2.faces if f[sl] in kit.nohull and all(v[hl].length > 0 for v in f.verts)]
        bmesh.ops.delete(b2, geom=kill, context='FACES')
        b2.to_mesh(obj.data)
        b2.free()
    return obj


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ================================================================ attachments (viewmodel scale)
def build_grip(pal):
    """Vertical foregrip: rail clamp with a thumb screw, oval rubber body with finger ridges, flared foot + amber band."""
    k = Kit(pal)
    # rail clamp: slotted block straddling a rail, chamfered along Y
    k.ext_y([(-0.015, 0.0), (0.015, 0.0), (0.015, -0.008), (0.010, -0.014), (-0.010, -0.014), (-0.015, -0.008)],
            -0.022, 0.022, 'gunmetal', ch0=0.002, ch1=0.002)
    k.box((0, 0.0, 0.0015), (0.022, 0.050, 0.003), 'ink')                        # clamp jaw slot (top, 1.5 mm proud)
    k.lathe([(0, 0), (0, 0.0055), (0.006, 0.0055), (0.008, 0.004), (0.008, 0)], 'steel', 'x', (0.015, 0.006, -0.007), 8, hull=False)
    k.box((0.0245, 0.006, -0.007), (0.003, 0.0022, 0.009), 'ink')              # screw slot
    # body: oval lathe hanging down, slight forward rake
    with k.at((0, 0.002, -0.012), (-6, 0, 0)):
        prof = [(0.002, 0), (0.002, 0.0115), (-0.004, 0.0132), (-0.060, 0.0128), (-0.066, 0.0150), (-0.074, 0.0172),
                (-0.080, 0.0172), (-0.083, 0.0145), (-0.083, 0)]
        k.lathe(prof, 'rubber', 'z', (0, 0, 0), 12, sc=(1.0, 1.22),
                bands=[None, 'gun2', None, 'gun2', 'gun2', 'gun2', 'gun2', 'gun2'])
        # finger ridges: three ink rings standing 3 mm proud on the front half
        for j in range(3):
            z = -0.018 - j * 0.0135
            k.ring('z', (0, 0, 0), z - 0.0022, z + 0.0022, 0.010, 0.0163, 'ink', seg=12, hull=False, sc=(1.0, 1.22))
        k.ring('z', (0, 0, 0), -0.0655, -0.0605, 0.012, 0.0164, 'amber', seg=12, hull=False, sc=(1.0, 1.22))   # amber band above the foot
        # foot cap bolt
        k.lathe([(-0.0828, 0), (-0.0828, 0.006), (-0.0858, 0.006), (-0.0858, 0)], 'steel2', 'z', (0, 0, 0), 6, hull=False)
    return finish('GEAR_Grip', k)


def build_scope(pal):
    """Open tube scope: eyepiece bell, tube, objective bell; lens rings and a duplex reticle; cantilever riser."""
    k = Kit(pal)
    ye, yo = 0.0, 0.108              # eyepiece / objective faces (origin = eye point on the optical axis)
    re, rt, ro, wall = 0.0175, 0.0118, 0.0195, 0.0028
    outer = [(ye, re), (ye + 0.030, re), (ye + 0.040, rt), (yo - 0.032, rt), (yo - 0.022, ro), (yo, ro)]
    inner = [(yo, ro - wall), (yo - 0.022, ro - wall), (yo - 0.032, rt - wall), (ye + 0.040, rt - wall), (ye + 0.030, re - wall), (ye, re - wall)]
    k.lathe(outer + inner, 'gunmetal', 'y', (0, 0, 0), 12, closed=True,
            bands=[None, None, None, None, None, 'ink', 'ink', 'ink', 'ink', 'ink', 'ink', 'gun3'])
    # lens rings inside both ends (glass tint, no disc: the view stays open)
    k.ring('y', (0, 0, 0), ye + 0.006, ye + 0.010, re - wall - 0.0035, re - 0.0026, 'lens', seg=12, hull=False)
    k.ring('y', (0, 0, 0), yo - 0.012, yo - 0.008, ro - wall - 0.0040, ro - 0.0026, 'lens2', seg=12, hull=False)
    # duplex reticle near the objective: thick outer posts, thin centre with a gap
    yr = yo - 0.016
    rr = ro - wall + 0.0005
    for (ax, s) in (('x', 1), ('x', -1), ('z', 1), ('z', -1)):
        a0, a1 = 0.0060, rr
        c = (a0 + a1) / 2
        p = (s * c, yr, 0) if ax == 'x' else (0, yr, s * c)
        sz = (a1 - a0, 0.0012, 0.0016) if ax == 'x' else (0.0016, 0.0012, a1 - a0)
        k.box(p, sz, 'ink')
        b0, b1 = 0.0014, 0.0060
        c = (b0 + b1) / 2
        p = (s * c, yr + 0.0005, 0) if ax == 'x' else (0, yr + 0.0005, s * c)
        sz = (b1 - b0, 0.0008, 0.0008) if ax == 'x' else (0.0008, 0.0008, b1 - b0)
        k.box(p, sz, 'ink')
    # amber stripe ring and the bell rings (3 mm proud)
    k.ring('y', (0, 0, 0), 0.058, 0.062, rt - 0.0001, rt + 0.0032, 'amber', seg=12, hull=False)
    k.ring('y', (0, 0, 0), ye + 0.003, ye + 0.012, re - 0.0001, re + 0.0032, 'gun3', seg=12, hull=False)
    k.ring('y', (0, 0, 0), yo - 0.010, yo - 0.002, ro - 0.0001, ro + 0.0032, 'gun3', seg=12, hull=False)
    # turrets: elevation on top, windage on the right (caps ink)
    k.lathe([(0, 0), (0, 0.0082), (0.011, 0.0082), (0.0135, 0.0058), (0.0135, 0)], 'gun3', 'z', (0, 0.048, rt - 0.0001), 8, hull=True,
            bands=[None, None, None, 'ink'])
    k.lathe([(0, 0), (0, 0.0072), (0.009, 0.0072), (0.0112, 0.0050), (0.0112, 0)], 'gun3', 'x', (rt - 0.0001, 0.048, 0), 8, hull=True,
            bands=[None, None, None, 'ink'])
    # rings + cantilever riser down to the base clamp (the base sinks into the receiver deck)
    for yy in (0.022, 0.070):
        r1 = (re if yy < 0.04 else rt) + 0.0032
        k.ring('y', (0, 0, 0), yy - 0.0065, yy + 0.0065, r1 - 0.0032, r1 + 0.0015, 'gun2', seg=12, hull=True)
        k.cbox((0, yy, -r1 - 0.006), (0.016, 0.007, 0.014), 'gun2', ch=0.002, axis='y')
    k.cbox((0, 0.046, -0.031), (0.024, 0.062, 0.012), 'gunmetal', ch=0.003, axis='y')    # riser beam
    k.cbox((0, 0.046, -0.041), (0.020, 0.056, 0.014), 'gun2', ch=0.003, axis='y')        # clamp (sinks into the deck)
    k.lathe([(0, 0), (0, 0.0042), (0.005, 0.0042), (0.005, 0)], 'steel', 'x', (0.012, 0.028, -0.031), 6, hull=False)
    k.lathe([(0, 0), (0, 0.0042), (0.005, 0.0042), (0.005, 0)], 'steel', 'x', (0.012, 0.064, -0.031), 6, hull=False)
    o = finish('GEAR_Scope', k)
    socket('GEAR_Scope_EYE', o, (0, 0, 0))
    return o


def build_acid(pal):
    """Acid muzzle: silencer can (collar, front cap with an ink bore), green glass window in a 4-bar cage,
    a side vial feeding the can, warning stripe."""
    k = Kit(pal)
    L, R = 0.112, 0.0172
    w0, w1 = 0.034, 0.078            # glass window
    # collar + rear can + front can, one closed lathe each side of the window; front face recessed bore
    k.lathe([(-0.014, 0), (-0.014, 0.0105), (0.0, 0.0105), (0.0, R - 0.002), (0.004, R), (w0, R), (w0, 0)], 'gun2', 'y', (0, 0, 0), 14,
            bands=['steel2', 'steel2', None, None, None, None])
    k.lathe([(w1, 0), (w1, R), (L - 0.006, R), (L, R - 0.004), (L, 0.0058), (L - 0.010, 0.0058), (L - 0.010, 0)], 'gun2', 'y', (0, 0, 0), 14,
            bands=[None, None, None, None, 'ink', 'ink'])
    # cage bars over the glass (45 degrees), and two cage rings
    for i in range(4):
        a = D(90 * i)
        rc = R + 0.0009
        k.cbox((rc * math.cos(a), (w0 + w1) / 2, rc * math.sin(a)), (0.0048, w1 - w0 + 0.002, 0.0048), 'gunmetal', ch=0.001,
               rot=(0, -(90 * i), 0), axis='y')
    # warning stripes: ink + amber rings on the front can
    k.ring('y', (0, 0, 0), 0.084, 0.090, R - 0.001, R + 0.0032, 'amber', seg=14, hull=False)
    k.ring('y', (0, 0, 0), 0.094, 0.098, R - 0.001, R + 0.0032, 'ink', seg=14, hull=False)
    # side vial on top-right: glass cylinder in a clip, steel caps, feed tube into the can
    vx, vz, vy0, vy1, vr = 0.0145, 0.0165, 0.010, 0.060, 0.0062
    k.lathe([(vy0, 0), (vy0, vr + 0.0016), (vy0 + 0.007, vr + 0.0016), (vy0 + 0.007, 0)], 'steel', 'y', (vx, 0, vz), 8, hull=True)
    k.lathe([(vy1 - 0.007, 0), (vy1 - 0.007, vr + 0.0016), (vy1, vr + 0.0016), (vy1 + 0.004, 0.003), (vy1 + 0.004, 0)], 'steel', 'y', (vx, 0, vz), 8, hull=True)
    k.lathe([(vy0 + 0.007, vr), (vy1 - 0.007, vr)], 'acid', 'y', (vx, 0, vz), 8, hull=True)    # glass wall (open tube, caps close it)
    va = math.atan2(vz, vx)
    k.cbox((vx + math.cos(va) * (vr - 0.0005), (vy0 + vy1) / 2 - 0.004, vz + math.sin(va) * (vr - 0.0005)), (0.0042, 0.022, 0.0022), 'acid3',
           ch=0.0, rot=(0, -math.degrees(va), 0))                                        # glass highlight
    for yy in (vy0 + 0.016, vy1 - 0.016):                                               # clip bands around the vial
        k.ring('y', (vx, 0, vz), yy - 0.0025, yy + 0.0025, vr - 0.001, vr + 0.0032, 'gun3', seg=8, hull=False)
    o = finish('GEAR_Acid', k)
    socket('GEAR_Acid_TIP', o, (0, L + 0.002, 0))
    # glass core: separate unlit piece (fills the window between the cans)
    g = Kit(pal)
    g.lathe([(w0, 0), (w0, R - 0.0012), (w1, R - 0.0012), (w1, 0)], 'acid', 'y', (0, 0, 0), 14, hull=False)
    for (yy, aa, rr) in ((0.042, 20, 0.0035), (0.052, 140, 0.0028), (0.063, 260, 0.0033), (0.070, 70, 0.0024), (0.047, 300, 0.0022)):
        a = D(aa)
        g.sphere((math.cos(a) * (R - 0.0012), yy, math.sin(a) * (R - 0.0012)), rr, 'acid3', seg=(6, 4))
    gl = finish('GEAR_Acid_Glow', g)
    strip_hull(gl)
    return o


def build_shield_cell(pal):
    """Hex shield battery: blue energy core seen between six ribs, gunmetal end caps, amber terminal, bolt emblem."""
    k = Kit(pal)
    H, R = 0.105, 0.040
    hexp = ngon(R, 6, 30)
    # end caps (chamfered hex prisms)
    k.ext_z(hexp, 0.0, 0.020, 'gunmetal', ch0=0.004, ch1=0.002)
    k.ext_z(hexp, H - 0.020, H, 'gunmetal', ch0=0.002, ch1=0.004)
    # core: glowing hex prism, slightly smaller
    k.ext_z(ngon(R * 0.80, 6, 30), 0.020, H - 0.020, 'cell', hull=True)
    # six ribs on the hex corners
    for i in range(6):
        a = D(30 + 60 * i)
        k.cbox((math.cos(a) * R * 0.86, math.sin(a) * R * 0.86, H / 2), (0.011, 0.011, H - 0.031), 'gun2', ch=0.002, rot=(0, 0, 30 + 60 * i), axis='z')
    # energy bands on the core faces
    for z in (0.034, H - 0.034):
        k.ring('z', (0, 0, 0), z - 0.003, z + 0.003, R * 0.60, R * 0.80 + 0.0032, 'cell3', seg=6, hull=False, a0=30)
    # terminal on top + amber cap, bottom foot ring
    k.lathe([(H, 0), (H, 0.012), (H + 0.010, 0.012), (H + 0.014, 0.008), (H + 0.014, 0)], 'amber', 'z', (0, 0, 0), 8, bands=[None, None, None, 'ink'])
    k.ring('z', (0, 0, 0), -0.004, 0.0, R * 0.55, R * 0.82, 'ink', seg=6, hull=False, a0=30)
    # bolt emblem on the front face (paper, 3 mm proud of the core)
    bolt = [(0.004, 0.030), (-0.010, 0.002), (0.0, 0.002), (-0.005, -0.030), (0.011, 0.006), (0.001, 0.006)]
    fx = R * 0.80 * math.cos(D(30))
    k.ext(bolt, 'paper', (fx, 0, H / 2), (0, 1, 0), (0, 0, 1), (1, 0, 0), -0.0005, 0.0065, hull=False)
    k.ext(bolt, 'paper', (-fx, 0, H / 2), (0, -1, 0), (0, 0, 1), (-1, 0, 0), -0.0005, 0.0065, hull=False)
    return finish('GEAR_ShieldCell', k)


# ================================================================ world loot drop
def build_capsule(pal):
    """Drop pod pedestal: stepped hex base with feet, a light ring band (LOOT_Glow), top collar with the emitter."""
    k = Kit(pal)
    k.ext_z(ngon(0.30, 6, 0), 0.0, 0.055, 'pod2', ch0=0.0, ch1=0.012)                 # base slab
    for i in range(6):                                                                  # feet with hazard tabs
        a = D(60 * i)
        k.cbox((math.cos(a) * 0.29, math.sin(a) * 0.29, 0.034), (0.07, 0.10, 0.068), 'pod', ch=0.012, rot=(0, 0, 60 * i + 90), axis='z')
        k.box((math.cos(a) * 0.3425, math.sin(a) * 0.3425, 0.036), (0.008, 0.044, 0.020), 'amber', rot=(0, 0, 60 * i))
    k.ext_z(ngon(0.24, 6, 30), 0.055, 0.105, 'pod', ch0=0.0, ch1=0.0)                # body under the light band
    k.ext_z(ngon(0.24, 6, 30), 0.155, 0.205, 'pod3', ch0=0.0, ch1=0.014)             # top collar
    k.lathe([(0.205, 0), (0.205, 0.150), (0.222, 0.140), (0.222, 0.0)], 'pod2', 'z', (0, 0, 0), 12, bands=[None, None, 'ink'])   # emitter rim
    for i in range(3):                                                                  # rivets on the collar
        a = D(30 + 120 * i)
        d = 0.24 * math.cos(D(30)) + 0.001
        k.lathe([(0, 0), (0, 0.012), (0.006, 0.012), (0.006, 0)], 'steel2', (V((math.cos(a), math.sin(a), 0)), V((0, 0, 1)), V((-math.sin(a), math.cos(a), 0))),
                (d * math.cos(a), d * math.sin(a), 0.180), 6, hull=False)
    o = finish('LOOT_Capsule', k, ht=HULL_WORLD)
    g = Kit(pal)
    g.ext_z(ngon(0.236, 6, 30), 0.105, 0.155, 'glow', hull=False)                    # light band
    g.lathe([(0.226, 0.0), (0.226, 0.128), (0.2245, 0.128), (0.2245, 0.0)], 'glow', 'z', (0, 0, 0), 12, hull=False)   # emitter disc
    gl = finish('LOOT_Glow', g, ht=HULL_WORLD)
    strip_hull(gl)
    return o


def build_gear(ao):
    pal = Palette(FAM)
    objs = [build_grip(pal), build_scope(pal), build_acid(pal), build_shield_cell(pal), build_capsule(pal)]
    for o in objs:
        print('%-16s %5d tris (incl. outline)' % (o.name, tris(o)))
    export(FAM)


FAMILY = FAM
BUILD = build_gear
