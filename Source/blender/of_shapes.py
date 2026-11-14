"""kit-office remodelled shapes (map asset upgrade pass): office plants with real foliage instead of balls and planks,
archive boxes with lids. Works on fam_kit_office's Kit (k.m is the bmesh Model, k._mark(ink) files small detail into
the hull-less mesh). Nothing here moves a piece's origin, footprint or collision boxes."""
import math

import bmesh
from mathutils import Vector


def hullp(k, pts, color, ink=True):
    """Convex hull of points (current k.push frame) as one shape; color: palette name or fn(face) -> name."""
    m = k.m
    P = m.parent
    vs = [m.bm.verts.new(P @ Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(m.bm, input=vs)
    junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(m.bm, geom=junk, context='VERTS')
    fs = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    m.nshape += 1
    for f in fs:
        f[m.shape] = m.nshape
        f.normal_update()
        f.material_index = m.pal.index(color(f) if callable(color) else color)
    k._mark(ink)
    return fs


def blob(k, rnd, c, r, color, n=10, squash=(1.0, 1.0, 0.8), jag=0.16, ink=True):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996 + rnd.uniform(-0.3, 0.3)
        q = r * rnd.uniform(1 - jag, 1 + jag * 0.5)
        pts.append((c[0] + math.cos(a) * rr * q * squash[0], c[1] + math.sin(a) * rr * q * squash[1], c[2] + z * q * squash[2]))
    return hullp(k, pts, color, ink)


def leafc(f):
    return 'leaf2' if f.normal.z > 0.45 else 'leaf'


def blade(k, base, tip, w, color, bend=(0.0, 0.0), ink=True):
    """A tapered leaf blade from base to tip: a flat-ish wedge, widest a third of the way up, bent by `bend` (x, y)
    at mid height (one convex hull)."""
    bx, by, bz = base
    tx, ty, tz = tip
    mx, my, mz = (bx + tx) / 2 + bend[0], (by + ty) / 2 + bend[1], (bz + tz) / 2
    dx, dy = tx - bx, ty - by
    L = math.hypot(dx, dy) or 1.0
    # sideways direction across the blade (horizontal, perpendicular to its run; if upright, across x)
    sx, sy = (-dy / L, dx / L) if L > 1e-3 else (1.0, 0.0)
    t = w * 0.25
    hullp(k, [(bx + sx * w * 0.4, by + sy * w * 0.4, bz), (bx - sx * w * 0.4, by - sy * w * 0.4, bz), (bx, by, bz + t),
              (mx + sx * w * 0.5, my + sy * w * 0.5, mz), (mx - sx * w * 0.5, my - sy * w * 0.5, mz), (mx, my, mz + t),
              (tx, ty, tz)], color, ink)


def pot(k, x, y, s, r0, r1, h, c='pot'):
    """Planter: tapered body, a rolled rim, soil sunk below the rim."""
    k.cyl(x, y, 0, r0 * s, r1 * s, h * s, c, seg=12)
    k.cyl(x, y, (h - 0.06) * s, r1 * s + 0.018, r1 * s + 0.018, 0.06 * s + 0.012, c, seg=12)
    k.cyl(x, y, (h - 0.05) * s, r1 * s - 0.03, r1 * s - 0.03, 0.03 * s, 'soil', seg=12, ink=False)


def fig(k, x, y, s, rnd):
    """Weeping fig: a slim trunk that forks into three, a crown of faceted leaf clumps round the branch ends."""
    pot(k, x, y, s, 0.22, 0.27, 0.55)
    z0 = 0.53 * s
    k.cyl(x, y, z0, 0.035 * s, 0.028 * s, 0.5 * s, 'trunk', seg=6)
    ends = []
    for i, (a, L, up) in enumerate(((0.4, 0.3, 0.75), (2.5, 0.28, 0.62), (4.4, 0.26, 0.85))):
        e = (x + math.cos(a) * L * s, y + math.sin(a) * L * s, z0 + (0.5 + up) * s)
        k.beam((x, y, z0 + 0.45 * s), e, 0.03 * s, 'trunk')
        ends.append(e)
    ends.append((x, y, z0 + 1.35 * s))
    k.beam((x, y, z0 + 0.45 * s), ends[-1], 0.03 * s, 'trunk')
    for e in ends:
        blob(k, rnd, (e[0], e[1], e[2] + 0.05 * s), rnd.uniform(0.25, 0.31) * s, leafc, n=11, squash=(1, 1, 0.85))
    for i in range(3):
        a = i * 2.1 + 1.0
        blob(k, rnd, (x + math.cos(a) * 0.22 * s, y + math.sin(a) * 0.22 * s, z0 + rnd.uniform(0.75, 1.05) * s),
             rnd.uniform(0.19, 0.24) * s, leafc, n=9)


def snake(k, x, y, s, rnd):
    """Snake plant: a square pot with a rim, upright pointed blades fanning out a little, two-tone."""
    h = 0.45 * s
    k.bx(x - 0.22 * s, x + 0.22 * s, y - 0.22 * s, y + 0.22 * s, 0, h, 'graphite2')
    k.bx(x - 0.235 * s, x + 0.235 * s, y - 0.235 * s, y + 0.235 * s, h - 0.04 * s, h + 0.012, 'graphite2')
    k.qz(x - 0.19 * s, x + 0.19 * s, y - 0.19 * s, y + 0.19 * s, h - 0.02 * s, 1, 'soil')
    blades = ((0, 0, 1.3), (0.1, 0.06, 1.15), (-0.11, 0.04, 1.2), (0.05, -0.1, 1.05), (-0.06, -0.09, 1.25),
              (0.12, -0.04, 0.95), (-0.13, -0.02, 1.0), (0.0, 0.12, 1.1))
    for i, (dx, dy, top) in enumerate(blades):
        base = (x + dx * s, y + dy * s, h - 0.03 * s)
        tip = (x + dx * 2.1 * s, y + dy * 2.1 * s, top * s)
        blade(k, base, tip, 0.1 * s, 'leaf' if i % 2 else 'leaf2', bend=(dx * 0.3 * s, dy * 0.3 * s))


def palm(k, x, y, s, rnd):
    """Areca palm: a clump of cane stems, each arching out into a frond of paired leaflets."""
    pot(k, x, y, s, 0.24, 0.2, 0.5)
    z0 = 0.47 * s
    for i in range(6):
        a = i / 6 * math.pi * 2 + rnd.uniform(-0.2, 0.2)
        ca, sa = math.cos(a), math.sin(a)
        top = (x + ca * 0.16 * s, y + sa * 0.16 * s, (0.85 + 0.12 * (i % 3)) * s)
        k.beam((x + ca * 0.04 * s, y + sa * 0.04 * s, z0), top, 0.03 * s, 'leaf', ink=False)
        # the frond's rib arcs out and down; leaflets in pairs along it
        tip = (x + ca * 0.85 * s, y + sa * 0.85 * s, (0.8 + 0.1 * (i % 2)) * s)
        mid = (x + ca * 0.48 * s, y + sa * 0.48 * s, top[2] + 0.12 * s)
        k.beam(top, mid, 0.024 * s, 'leaf', ink=False)
        k.beam(mid, tip, 0.013 * s, 'leaf', ink=False)
        for j in range(6):
            f = (j + 0.5) / 6
            if f < 0.5:
                p = [top[q] + (mid[q] - top[q]) * f * 2 for q in range(3)]
            else:
                p = [mid[q] + (tip[q] - mid[q]) * (f - 0.5) * 2 for q in range(3)]
            Lf = (0.3 - 0.12 * f) * s
            for side in (-1, 1):
                b = a + side * 1.1
                end = (p[0] + math.cos(b) * Lf, p[1] + math.sin(b) * Lf, p[2] - rnd.uniform(0.06, 0.1) * s)
                blade(k, (p[0] + math.cos(b) * 0.012, p[1] + math.sin(b) * 0.012, p[2] + rnd.uniform(-0.01, 0.01)), end, rnd.uniform(0.06, 0.075) * s, 'leaf2' if (i + j) % 2 else 'leaf')


def small_plant(k, rnd, x, y, z):
    """Desk plant: a small pot with a rim and two leaf clumps."""
    k.cyl(x, y, z, 0.07, 0.09, 0.14, 'pot', seg=8, ink=False)
    k.cyl(x, y, z + 0.12, 0.1, 0.1, 0.03, 'pot', seg=8, ink=False)
    blob(k, rnd, (x - 0.03, y, z + 0.24), 0.11, leafc, n=9)
    blob(k, rnd, (x + 0.05, y + 0.02, z + 0.3), 0.09, leafc, n=8)


def archive_box(k, x0, x1, y0, y1, z0, z1):
    """Archive box: body, a lid 6 mm wider all round, a hand hole and a label on the front."""
    lid = 0.07
    k.bx(x0, x1, y0, y1, z0, z1 - lid + 0.01, 'cardboard')
    k.bx(x0 - 0.006, x1 + 0.006, y0 - 0.006, y1 + 0.006, z1 - lid, z1, 'cardboard')
    k.qy(x0 + 0.02, x1 - 0.02, z1 - lid + 0.012, z1 - 0.012, y0 - 0.009, -1, 'oak2')                # lid band
    cx = (x0 + x1) / 2
    k.qy(cx - 0.06, cx + 0.06, z0 + 0.1, z0 + 0.15, y0 - 0.003, -1, 'white')                          # label
    k.qy(cx - 0.035, cx + 0.035, z0 + 0.04, z0 + 0.07, y0 - 0.003, -1, 'graphite')                    # hand hole


def soft_box(k, x0, x1, y0, y1, z0, z1, color, c=0.035):
    """Upholstered block: a box with every edge chamfered (convex hull of the corners pulled in along each axis)."""
    c = min(c, (x1 - x0) / 3, (y1 - y0) / 3, (z1 - z0) / 3)
    pts = []
    for x, sx in ((x0, 1), (x1, -1)):
        for y, sy in ((y0, 1), (y1, -1)):
            for z, sz in ((z0, 1), (z1, -1)):
                pts += [(x + sx * c, y, z + sz * c), (x, y + sy * c, z + sz * c), (x + sx * c, y + sy * c, z)]
    return hullp(k, pts, color)
