"""INKBOLT kit-venetian ("Ca' Doranza", a made-up Venetian mansion compound): palette and modelling helpers shared by
ven_facade.py (the zone walls: the campo's house fronts in four stucco colours and two heights, the mansion's courtyard
and canal facades, the quay balustrade, corners, the gate portal and the facades over the gates, the trail's bridge
balustrades and the exit lane's walls, the hatch), ven_campo.py (zone 1, the campo: the Fountain of the Four Winds,
the two walk-in cafes, the merchants' loggia, cafe tables, parasols, planters, the kiosk, the flower stall, market
stalls, the well-head, lamp posts, benches, crates and barrels, paving) and ven_court.py (zone 2, the courtyard: the
cloister columns and arches, the balustrades of its upper walk, the grand staircase, the service stairs, the garden
fountain, parterres and hedges, the roof loggia, citrus pots, cypresses, urns, the boat under repair).
The family module is fam_kit_venetian.py.

Look: warm stucco (ochre, terracotta, rose, cream) over white Istrian stone trims, green louvred shutters, terracotta
roofs and funnel chimneys, grey trachyte paving with white stone bands, canal water in green-teal, red and pink
geraniums trailing from every balcony, comic ink outlines throughout.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = game north, Blender +X = game east.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (stair treads, terraces).
  * Wall modules face Blender -Y (the theme turns their -Y face toward the open side: wall.facing 'open'); the cell
    spans y -0.5..0.5 and the face the player meets is the plane y = -0.5. The stucco cells (stucco / stuccoL /
    stuccoD) are repainted per building by the theme (wall.paint).
  * Run pieces placed with `links` (balustrades, hedges) are modelled along Blender Y (the half module runs from the
    origin toward -Y); spans (the cloister arches) along Blender X.
  * Stairs rise RISE (0.18 m) per TREAD (0.25 m): 0.36 m per 0.5 m nav cell, under the robots' 0.4 m step.
  * Flat detail (paint, lettering, glints) is a single face without an outline shell, >= 3 mm proud of its surface.
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fr_base import FKit, wall_parts  # noqa: F401
from kit_base import srt  # noqa: F401

FAM = 'kit-venetian'
PFX = 'KIT_VENETIAN_'
ib_lib.GLB[FAM] = 'fps-kit-venetian.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    # stucco (8 - 19): the modelled colour (ochre) and the theme's repaints (terracotta, rose, cream); base / lit / shade
    ('stucco', '#E0A659'), ('stuccoL', '#EDBE78'), ('stuccoD', '#B9813F'),
    ('terra', '#CF6E45'), ('terraL', '#DF8A60'), ('terraD', '#A9532F'),
    ('rose', '#DE9A8B'), ('roseL', '#ECB5A8'), ('roseD', '#B97467'),
    ('cream', '#EAD7B0'), ('creamL', '#F4E6C8'), ('creamD', '#C7B288'),
    # stone, marble, brick, roof tiles (20 - 27)
    ('stone', '#EFE9DC'), ('stoneD', '#CBC2AE'), ('marbleR', '#C27A6A'), ('brick', '#B0563B'),
    ('roof', '#C0603A'), ('roofD', '#93452A'), ('plaster', '#F1E3C6'), ('verd', '#5FA592'),
    # shutters, wood, iron, metal (28 - 36)
    ('shut', '#3E7556'), ('shutD', '#2B5540'), ('wood', '#8C5B38'), ('woodD', '#5E3B24'), ('iron', '#2B2D33'),
    ('gold', '#E3B24A'), ('bronze', '#A07A3A'), ('chrome', '#C8CFD6'), ('boat', '#1F1F26'),
    # glass, light (37 - 40)
    ('glass', '#34495C'), ('glassL', '#9CC3D6'), ('lamp', '#FFD47A'), ('lampW', '#FFF2C9'),
    # flowers, greens (41 - 48)
    ('fRed', '#E0423A'), ('fPink', '#F283AE'), ('fPurp', '#9A5CC8'), ('fOrange', '#F29A36'),
    ('leaf', '#4E9442'), ('leafD', '#376E30'), ('leafL', '#7DBA58'), ('cypress', '#2D5A3A'),
    # water, awnings (49 - 53)
    ('water', '#3F8F93'), ('waterL', '#86C8C2'), ('awnR', '#B5302E'), ('awnG', '#2F6D50'), ('canvas', '#F2E8D0'),
    # paving, cafe, garden (54 - 62)
    ('pave', '#A39A8F'), ('paveD', '#8E867D'), ('cobble', '#B0A699'), ('marble', '#ECE7DE'), ('rattan', '#C9A066'),
    ('bottle', '#3B7A4C'), ('gravel', '#DCCDA6'), ('soil', '#7A5A40'), ('lemon', '#F2D23A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# ---------------------------------------------------------------- dimensions
RISE = 0.18          # stair rise per tread
TREAD = 0.25
GF = 4.0             # ground floor top (string course)
PN = 7.2             # piano nobile top
H3 = 10.4            # three-storey house: cornice top
H2 = 7.6             # two-storey house
HP = 12.2            # the mansion (zone 2): ground 0-4.4, piano nobile 4.4-8.4, second floor 8.4-11.6, cornice
PGF, PPN = 4.4, 8.4
QUAY_H = 1.1         # quay / bridge balustrade (theme wall.height)
TERR = 3.6           # cafe roof terrace and the loggia roof (20 treads)
DECK = 4.32          # the cloister's upper walk (24 treads)
WATER = -1.25        # canal surface (game y)
CALLE_H = 3.4        # the exit lane's walls

TRIS = {}


class VKit(FKit):
    """FKit with face culling on boxes, profile prisms (arches), lathes (balusters, urns, columns) and tubes."""

    def bxc(self, x0, x1, y0, y1, z0, z1, c, cull='', ink=True, bevel=False):
        """box with faces dropped: t b f k l r = +Z -Z -Y +Y -X +X (piece frame)"""
        x0, x1 = srt(x0, x1)
        y0, y1 = srt(y0, y1)
        z0, z1 = srt(z0, z1)
        m = self.m
        M = m.parent @ mat_trs(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0))
        verts = bmesh.ops.create_cube(m.bm, size=1.0, matrix=M)['verts']
        if cull:
            R = m.parent.to_3x3()
            dirs = {'t': (0, 0, 1), 'b': (0, 0, -1), 'f': (0, -1, 0), 'k': (0, 1, 0), 'l': (-1, 0, 0), 'r': (1, 0, 0)}
            kill = []
            for f in {f for v in verts for f in v.link_faces}:
                f.normal_update()
                for ch in cull:
                    d = (R @ Vector(dirs[ch])).normalized()
                    if f.normal.dot(d) > 0.99:
                        kill.append(f)
                        break
            bmesh.ops.delete(m.bm, geom=kill, context='FACES_ONLY')
            loose = [e for e in {e for v in verts if v.is_valid for e in v.link_edges} if not e.link_faces]
            if loose:
                bmesh.ops.delete(m.bm, geom=loose, context='EDGES')
            verts = [v for v in verts if v.is_valid]
            lone = [v for v in verts if not v.link_edges]
            if lone:
                bmesh.ops.delete(m.bm, geom=lone, context='VERTS')
                verts = [v for v in verts if v.is_valid]
        m._finish(verts, c, bevel)
        self._mark(ink)

    def prism_xz(self, pts, y0, y1, c, ink=True, cull='', colors=None):
        """polygon [(x, z), ...] (a simple outline, any winding) extruded along Y from y0 to y1; cull drops faces by
        their local normal: 'f' the -Y cap, 'k' the +Y cap, l r t b the -X +X +Z -Z sides; colors: fn(local face
        normal) -> colour name (else c)"""
        m = self.m
        P, bm = m.parent, m.bm
        y0, y1 = srt(y0, y1)
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        if area < 0:
            pts = list(reversed(pts))
        # counter-clockwise in (x, z): the y0 cap faces -Y as listed, the y1 cap reversed, sides (a_i, b_i, b_j, a_j)
        a = [bm.verts.new(P @ Vector((x, y0, z))) for (x, z) in pts]
        b = [bm.verts.new(P @ Vector((x, y1, z))) for (x, z) in pts]
        fs = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((a[i], b[i], b[j], a[j])))
        R = P.to_3x3()
        kill = []
        for f in fs:
            f.normal_update()
            ln = R.inverted() @ f.normal
            if (('f' in cull and ln.y < -0.99) or ('k' in cull and ln.y > 0.99) or ('l' in cull and ln.x < -0.99) or ('r' in cull and ln.x > 0.99)
                    or ('t' in cull and ln.z > 0.99) or ('b' in cull and ln.z < -0.99)):
                kill.append(f)
        if kill:
            bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
            fs = [f for f in fs if f.is_valid]
        m.nshape += 1
        for f in fs:
            f[m.shape] = m.nshape
            ln = R.inverted() @ f.normal
            f.material_index = m.pal.index(colors(ln) if colors else c)
        self._mark(ink)

    def lathe(self, x, y, z0, prof, c, seg=8, ink=True, colors=None, closed=False, a0=0.0, caps=True):
        """solid of revolution about the vertical axis at (x, y): prof [(r, dz), ...] bottom to top, counter-clockwise
        in (r, z) (round the outside from the bottom) so the faces face out (the winding is built, not recalculated);
        caps close the ends where r > 0 (caps=False leaves them open); closed=True: the profile is a loop (a ring, a
        basin wall: no caps); a0 turns the rings; colors: a list (one per profile band) instead of c"""
        m = self.m
        P, bm = m.parent, m.bm
        if closed:
            prof = list(prof) + [prof[0]]
        rings = []
        if closed:
            rings_ = []
            for (r, dz) in prof[:-1]:
                rings_.append([bm.verts.new(P @ Vector((x + math.cos(a0 + i * 2 * math.pi / seg) * r, y + math.sin(a0 + i * 2 * math.pi / seg) * r, z0 + dz))) for i in range(seg)])
            rings_.append(rings_[0])
            fs, fc = [], []
            for kk in range(len(rings_) - 1):
                A, B = rings_[kk], rings_[kk + 1]
                for i in range(seg):
                    j = (i + 1) % seg
                    fs.append(bm.faces.new((A[i], A[j], B[j], B[i])))
                    fc.append(colors[kk] if colors else c)
            m.nshape += 1
            for f, col in zip(fs, fc):
                f[m.shape] = m.nshape
                f.material_index = m.pal.index(col)
            self._mark(ink)
            return
        rings = []
        for (r, dz) in prof:
            if r < 1e-4:
                rings.append([bm.verts.new(P @ Vector((x, y, z0 + dz)))])
            else:
                rings.append([bm.verts.new(P @ Vector((x + math.cos(a0 + i * 2 * math.pi / seg) * r, y + math.sin(a0 + i * 2 * math.pi / seg) * r, z0 + dz))) for i in range(seg)])
        fs, fc = [], []
        for k in range(len(rings) - 1):
            A, B = rings[k], rings[k + 1]
            col = colors[k] if colors else c
            if len(A) == 1 and len(B) == 1:
                continue
            for i in range(seg):
                j = (i + 1) % seg
                if len(A) == 1:
                    f = bm.faces.new((A[0], B[j], B[i]))
                elif len(B) == 1:
                    f = bm.faces.new((A[i], A[j], B[0]))
                else:
                    f = bm.faces.new((A[i], A[j], B[j], B[i]))
                fs.append(f)
                fc.append(col)
        if len(rings[0]) > 1 and caps:
            fs.append(bm.faces.new(list(reversed(rings[0]))))
            fc.append(colors[0] if colors else c)
        if len(rings[-1]) > 1 and caps:
            fs.append(bm.faces.new(rings[-1]))
            fc.append(colors[-1] if colors else c)
        for f in fs:
            f.normal_update()
        m.nshape += 1
        for f, col in zip(fs, fc):
            f[m.shape] = m.nshape
            f.material_index = m.pal.index(col)
        self._mark(ink)


def kit(pal):
    return VKit(pal, PFX, HULL_T)


def done(k, name, ao, bevel=0.0, recolor=None):
    """finish a piece; recolor: {colour: colour} remaps faces before the build (a piece placed without the theme's
    paint, e.g. the mansion's portal facades, keeps the mansion's rose)"""
    if recolor:
        pal = k.pal
        rm = {pal.index(a): pal.index(b) for a, b in recolor.items()}
        for f in k.m.bm.faces:
            if f.material_index in rm:
                f.material_index = rm[f.material_index]
    obj = k.finish(name, bevel=bevel, ao=ao)
    TRIS[PFX + name] = k.tris[PFX + name]
    return obj


# ---------------------------------------------------------------- shapes
def arch_curve(x0, x1, zs, kind='round', n=4, rise=None):
    """points of an arch's intrados from the left spring (x0, zs) over the crown to the right spring (x1, zs);
    kind 'round' (semicircle), 'seg' (segmental: rise given), 'ogee' (Venetian Gothic: convex then concave to a
    point); n segments per half"""
    a = (x1 - x0) / 2
    xc = (x0 + x1) / 2
    pts = []
    if kind == 'round':
        for i in range(2 * n + 1):
            t = math.pi - math.pi * i / (2 * n)
            pts.append((xc + math.cos(t) * a, zs + math.sin(t) * a))
    elif kind == 'seg':
        h = rise or a * 0.4
        R = (a * a + h * h) / (2 * h)
        zc = zs + h - R
        t0 = math.atan2(zs - zc, -a)
        t1 = math.atan2(zs - zc, a)
        for i in range(2 * n + 1):
            t = t0 + (t1 - t0) * i / (2 * n)
            pts.append((xc + math.cos(t) * R, zc + math.sin(t) * R))
    else:   # ogee
        h = rise or a * 1.25
        half = []
        for i in range(n + 1):
            u = i / n
            if u <= 0.55:
                f = 0.62 * math.sin(math.pi / 2 * u / 0.55)
            else:
                f = 0.62 + 0.38 * ((u - 0.55) / 0.45) ** 2.2
            half.append((x0 + a * u, zs + h * f))
        pts = half + [(2 * xc - px, pz) for (px, pz) in reversed(half[:-1])]
    return pts


def arched_opening(k, x0, x1, z0, zs, kind, depth, back, frame='stone', fw=0.06, y=-0.5, n=4, rise=None,
                   reveal='stuccoD', sill=None):
    """an arched opening in a facade plane at y (facing -Y) whose front strips the caller leaves open over the hole
    (x0..x1, z0..crown): the spandrel fill between the arch and the hole's top corners, the reveal round it (depth),
    the back fill (glass / door colour, or None), a stone frame band round the arch and the jambs; returns the crown"""
    cur = arch_curve(x0, x1, zs, kind, n, rise)
    top = max(pz for _, pz in cur)
    # spandrels (flat on the facade plane, filling the hole's top corners)
    left = [(x0, zs)] + [p for p in cur if p[0] <= (x0 + x1) / 2 + 1e-6]
    right = [p for p in cur if p[0] >= (x0 + x1) / 2 - 1e-6] + [(x1, zs)]
    k.poly([(px, y, pz) for (px, pz) in left] + [(x0, y, top)], 'stucco', (0, -1, 0))
    k.poly([(x1, y, top)] + [(px, y, pz) for (px, pz) in right], 'stucco', (0, -1, 0))
    # reveal: jambs and the soffit along the curve
    yd = y + depth
    k.poly([(x0, y, z0), (x0, yd, z0), (x0, yd, zs), (x0, y, zs)], reveal, (1, 0, 0))
    k.poly([(x1, y, z0), (x1, y, zs), (x1, yd, zs), (x1, yd, z0)], reveal, (-1, 0, 0))
    for (pa, pb) in zip(cur, cur[1:]):
        mx, mz = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        nx, nz = (x0 + x1) / 2 - mx, (zs - 2.0) - mz
        L = math.hypot(nx, nz) or 1.0
        k.poly([(pa[0], y, pa[1]), (pb[0], y, pb[1]), (pb[0], yd, pb[1]), (pa[0], yd, pa[1])], reveal, (nx / L, 0, nz / L))
    if sill is None:
        k.poly([(x0, y, z0), (x1, y, z0), (x1, yd, z0), (x0, yd, z0)], reveal, (0, 0, 1))
    if back:
        k.poly([(x0, yd, z0), (x1, yd, z0)] + [(px, yd, pz) for (px, pz) in reversed(cur)][1:-1] + [(x0, yd, zs)], back, (0, -1, 0))
    if frame:
        # the stone band round the arch, 6 mm proud of the facade (segments outward along the curve)
        yf = y - 0.006
        for (pa, pb) in zip(cur, cur[1:]):
            def out(p):
                dx, dz = p[0] - (x0 + x1) / 2, p[1] - zs + (0.0 if kind == 'round' else 0.3)
                L = math.hypot(dx, dz) or 1.0
                return (p[0] + dx / L * fw, p[1] + max(0.0, dz / L) * fw)
            qa, qb = out(pa), out(pb)
            k.poly([(pa[0], yf, pa[1]), (qa[0], yf, qa[1]), (qb[0], yf, qb[1]), (pb[0], yf, pb[1])], frame, (0, -1, 0))
        k.poly([(x0 - fw, yf, z0), (x0, yf, z0), (x0, yf, zs), (x0 - fw, yf, zs)], frame, (0, -1, 0))
        k.poly([(x1, yf, z0), (x1 + fw, yf, z0), (x1 + fw, yf, zs), (x1, yf, zs)], frame, (0, -1, 0))
    return top


def rect_opening(k, x0, x1, z0, z1, depth, back, y=-0.5, reveal='stuccoD', frame='stone', fw=0.06, sill=True):
    """a rectangular opening (window / door) at plane y facing -Y: reveal, back fill, stone frame, a sill"""
    yd = y + depth
    k.poly([(x0, y, z0), (x0, yd, z0), (x0, yd, z1), (x0, y, z1)], reveal, (1, 0, 0))
    k.poly([(x1, y, z0), (x1, y, z1), (x1, yd, z1), (x1, yd, z0)], reveal, (-1, 0, 0))
    k.poly([(x0, y, z1), (x0, yd, z1), (x1, yd, z1), (x1, y, z1)], reveal, (0, 0, -1))
    k.poly([(x0, y, z0), (x1, y, z0), (x1, yd, z0), (x0, yd, z0)], reveal, (0, 0, 1))
    if back:
        k.qy(x0, x1, z0, z1, yd, -1, back)
    if frame:
        yf = y - 0.006
        k.qy(x0 - fw, x1 + fw, z1, z1 + fw * 1.4, yf, -1, frame)
        k.qy(x0 - fw, x0, z0, z1, yf, -1, frame)
        k.qy(x1, x1 + fw, z0, z1, yf, -1, frame)
    if sill:
        k.bxc(x0 - fw - 0.02, x1 + fw + 0.02, y - 0.07, y, z0 - 0.07, z0, 'stone', cull='kb', ink=False)


def glints(k, x0, x1, z0, z1, y, s=-1):
    """a slanted streak on a glass plane (facing s * Y)"""
    w = x1 - x0
    h = (z1 - z0) * 0.32
    zz = z0 + (z1 - z0) * 0.3
    a, ww = x0 + w * 0.2, w * 0.1
    k.poly([(a, y, zz), (a + ww, y, zz), (a + ww + h * 0.4, y, zz + h), (a + h * 0.4, y, zz + h)], 'glassL', (0, s, 0))


def flowers(k, rnd, x0, x1, y0, y1, z, n, cols=('fRed', 'fPink', 'fRed', 'white'), s=0.07, trail=0.0, yt=None):
    """geranium heads in a box (x0..x1, y0..y1) at height z: leafy mound and blooms; trail: vines hanging down
    from the box's front edge (at y = yt) this long"""
    L = x1 - x0
    k.hullp([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
             (x0 + 0.04, y0 + 0.02, z + 0.12), (x1 - 0.04, y0 + 0.02, z + 0.12), (x1 - 0.04, y1 - 0.02, z + 0.1),
             (x0 + 0.04, y1 - 0.02, z + 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.17)], 'leaf', ink=False)
    for i in range(n):
        fx = x0 + L * (i + 0.5) / n + rnd.uniform(-0.03, 0.03)
        fy = (y0 + y1) / 2 + rnd.uniform(-0.04, 0.03)
        k.hullp([(fx + math.cos(a) * s, fy + math.sin(a) * s * 0.8, z + 0.12 + rnd.uniform(0.0, 0.04)) for a in (0, 2.1, 4.2)] +
                [(fx, fy, z + 0.2 + rnd.uniform(0.0, 0.05))], cols[i % len(cols)], ink=False)
    if trail > 0:
        yy = yt if yt is not None else y0
        nt = max(2, int(L / 0.18))
        for i in range(nt):
            tx = x0 + 0.05 + (L - 0.1) * i / max(1, nt - 1) + rnd.uniform(-0.02, 0.02)
            ln = trail * rnd.uniform(0.45, 1.0)
            k.hullp([(tx - 0.035, yy - 0.004, z + 0.06), (tx + 0.035, yy - 0.004, z + 0.06), (tx, yy - 0.05, z + 0.02),
                     (tx + rnd.uniform(-0.03, 0.03), yy - 0.03, z - ln)], 'leafD' if i % 2 else 'leaf', ink=False)
            if i % 2 == 0:
                bz = z - ln * rnd.uniform(0.3, 0.8)
                k.hullp([(tx - 0.03, yy - 0.05, bz), (tx + 0.03, yy - 0.05, bz), (tx, yy - 0.07, bz + 0.05), (tx, yy - 0.02, bz - 0.04)],
                        cols[(i // 2) % len(cols)], ink=False)


def flower_box(k, rnd, x0, x1, y, z, trail=0.45, cols=('fRed', 'fPink', 'fRed', 'white'), d=0.2, c='terra'):
    """a window box standing out from a facade plane at y (facing -Y), its bottom at z, full of geraniums"""
    k.bxc(x0, x1, y - d, y, z, z + 0.16, c, cull='k')
    flowers(k, rnd, x0 + 0.02, x1 - 0.02, y - d + 0.02, y - 0.02, z + 0.16, max(2, int((x1 - x0) / 0.16)), cols, trail=trail, yt=y - d - 0.01)


def wall_lantern(k, x, y, z, arm=0.38):
    """an iron bracket lantern on a facade plane at y (facing -Y): z = the lantern's bottom; returns the glass centre"""
    k.bxc(x - 0.06, x + 0.06, y - 0.02, y, z + 0.35, z + 0.6, 'iron', cull='k')
    k.beam((x, y - 0.01, z + 0.55), (x, y - arm, z + 0.62), 0.03, 'iron')
    k.beam((x, y - 0.01, z + 0.38), (x, y - arm * 0.7, z + 0.58), 0.018, 'iron')
    cy = y - arm
    k.cyl(x, cy, z + 0.04, 0.07, 0.11, 0.3, 'lamp', seg=6, ink=False)
    k.cyl(x, cy, z, 0.06, 0.06, 0.05, 'iron', seg=6)
    k.cyl(x, cy, z + 0.34, 0.13, 0.03, 0.12, 'iron', seg=6)
    k.cyl(x, cy, z + 0.46, 0.015, 0.015, 0.14, 'iron', seg=4, ink=False)
    return (x, cy, z + 0.2)


def lantern_glow(k, x, y, z, r=0.13, h=0.36):
    """the unlit glow companion of a lantern: a slightly larger glass"""
    k.cyl(x, y, z - h / 2, r * 0.8, r, h, 'lamp', seg=6, ink=False)


def baluster(k, x, y, z0, h, c='stone', seg=4, r=0.055):
    """a turned stone baluster (square-turned: 4 sides)"""
    k.lathe(x, y, z0, [(r * 0.7, 0.0), (r * 1.3, h * 0.45), (r * 0.75, h)], c, seg=seg, ink=False, caps=False, a0=math.pi / 4)


def balustrade_x(k, x0, x1, y, z0, h=1.0, every=0.25, c='stone', plinth=True, w=0.22, ends=(True, True), cull_ends=False):
    """a stone balustrade along X at y: plinth, balusters every `every`, handrail; ends: closed end faces"""
    cl = ('l' if not ends[0] else '') + ('r' if not ends[1] else '')
    if plinth:
        k.bxc(x0, x1, y - w / 2, y + w / 2, z0, z0 + 0.12, c, cull='b' + cl)
    k.bxc(x0, x1, y - w / 2 - 0.02, y + w / 2 + 0.02, z0 + h - 0.1, z0 + h, c, cull=cl, bevel=False)
    n = max(1, int(round((x1 - x0) / every)))
    for i in range(n):
        bx = x0 + (x1 - x0) * (i + 0.5) / n
        baluster(k, bx, y, z0 + 0.12, h - 0.22, 'stoneD' if c == 'stone' else c)


def text(k, word, x, y, z, cap, c, face='y-', font='serif', maxw=None, align='c', valign='b'):
    k.text(word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)


def steps(k, x0, x1, y0, n, z0=0.0, dir_=1, c='stone', nose='stoneD', cols=True, visual=True, sides='', ink=False):
    """straight stair: n treads of TREAD rising RISE from z0, from y0 toward +Y (dir_ 1) or -Y; each tread a walkable
    box solid down to z0 (robot nav) and drawn as a solid block (sides: 'l' / 'r' drop its -X / +X face, against a
    wall) with a darker nose line on its riser; returns the end y"""
    for i in range(n):
        ya = y0 + dir_ * i * TREAD
        yb = ya + dir_ * TREAD
        za = z0 + (i + 1) * RISE
        lo, hi = srt(ya, yb)
        if visual:
            k.bxc(x0, x1, lo, hi, z0, za, c, cull='b' + ('k' if dir_ > 0 else 'f') + sides, ink=ink)
            yr = lo - 0.004 if dir_ > 0 else hi + 0.004
            k.poly([(x0 + 0.01, yr, za - 0.05), (x1 - 0.01, yr, za - 0.05), (x1 - 0.01, yr, za - 0.012), (x0 + 0.01, yr, za - 0.012)], nose, (0, -dir_, 0))
        if cols:
            k.wcol(x0, x1, lo, hi, z0, za)
    return y0 + dir_ * n * TREAD
