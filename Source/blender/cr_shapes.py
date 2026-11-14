"""kit-classroom remodelled shapes (map asset upgrade pass): sill plants with real leaves instead of stretched balls,
and the trees in the window view as lobed crowns on trunks instead of plain round discs. Works on the classroom's K
model (m.flat() marks the last shape as outline-free). Nothing here moves a piece's origin, footprint or collision."""
import math

import bmesh
from mathutils import Matrix, Vector


def hullp(m, pts, color):
    """Convex hull of points (m.parent frame) as one shape."""
    P = m.parent
    vs = [m.bm.verts.new(P @ Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(m.bm, input=vs)
    junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(m.bm, geom=junk, context='VERTS')
    fs = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    m.nshape += 1
    ci = m.pal.index(color)
    for f in fs:
        f[m.shape] = m.nshape
        f.material_index = ci
    return fs


def leaf(m, base, tip, w, color, lift=0.0):
    """A pointed leaf: base at the stem, widest 40 % along, a raised midrib, tip drooping by `lift`."""
    bx, by, bz = base
    tx, ty, tz = tip
    dx, dy, dz = tx - bx, ty - by, tz - bz
    L = math.hypot(dx, dy)
    sx, sy = (-dy / L, dx / L) if L > 1e-3 else (1.0, 0.0)
    px, py, pz = bx + dx * 0.4, by + dy * 0.4, bz + dz * 0.4 + lift
    hullp(m, [(bx, by, bz), (px + sx * w / 2, py + sy * w / 2, pz), (px - sx * w / 2, py - sy * w / 2, pz),
              (px, py, pz + w * 0.18), (tx, ty, tz)], color)


def sill_plant(m, x, y, z, tall=False, cols=('leaf', 'leaf')):
    """Potted plant on the sill: terracotta pot with a rolled rim and soil, a fan of pointed leaves arching out of it
    (taller and more upright for `tall`)."""
    m.cyl((x, y, z), 0.2, 0.27, 0.5, 'terra', seg=8, bevel=False)
    m.cyl((x, y, z + 0.44), 0.29, 0.29, 0.12, 'terra', seg=8, bevel=False)
    n = 9 if tall else 8
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        up = (1.25 if tall else 0.85) * (0.75 + 0.25 * ((i * 7) % 3) / 2)
        reach = (0.32 if tall else 0.42) * (0.85 + 0.15 * ((i * 5) % 3) / 2)
        base = (x + math.cos(a) * 0.05, y + math.sin(a) * 0.05, z + 0.53)
        tip = (x + math.cos(a) * reach, y + math.sin(a) * reach, z + 0.53 + up)
        leaf(m, base, tip, 0.13 if tall else 0.16, cols[i % len(cols)], lift=0.05)


def quad_y(m, x0, x1, z0, z1, y, color):
    """One flat quad facing -Y at plane y (painted line); its own shape, the caller marks it flat."""
    P = m.parent
    vs = [m.bm.verts.new(P @ Vector(p)) for p in ((x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0))]
    f = m.bm.faces.new(vs)
    f.normal_update()
    if f.normal.dot(P.to_3x3() @ Vector((0, -1, 0))) < 0:
        f.normal_flip()
    m.nshape += 1
    f[m.shape] = m.nshape
    f.material_index = m.pal.index(color)


def block_coursing(m, z0=5.63, z1=15.45, yf=-0.42, course=1.2, color='paperDk'):
    """Painted block wall on the cream upper wall of a 1 m module: a mortar line every course, running bond (a joint
    in the middle of the module on odd courses, half joints at both module edges on even courses, so neighbouring
    modules complete each other). Flat quads 6 mm proud; joints stop where the lines start (no overlap)."""
    y = yf - 0.006
    zs = [z0]
    while zs[-1] + course < z1 - 0.3:
        zs.append(zs[-1] + course)
    for z in zs[1:]:
        quad_y(m, -0.495, 0.495, z - 0.012, z + 0.012, y, color)
        m.flat()
    for k, (za, zb) in enumerate(zip(zs[:-1], zs[1:])):
        lo, hi = za + (0.012 if k else 0.0), zb - 0.012
        if k % 2:
            quad_y(m, -0.012, 0.012, lo, hi, y, color)
            m.flat()
        else:
            for (xa, xb) in ((-0.497, -0.488), (0.488, 0.497)):
                quad_y(m, xa, xb, lo, hi, y, color)
                m.flat()


def eraser(m):
    """Jumbo eraser (weapon stand / cover, footprint 0.94 x 0.68 x 0.86): a chamfered block with one end rubbed down
    into a rounded slope, a printed card sleeve with lips, labels and a stripe, and a few rubbed-off crumbs."""
    prof = [(-0.47, 0.0), (0.47, 0.0), (0.47, 0.5), (0.455, 0.65), (0.41, 0.76), (0.33, 0.835), (0.22, 0.86), (-0.47, 0.86)]
    c = 0.05
    cx, cz = 0.0, 0.43
    pts = []
    for (x, z) in prof:
        for y in (-0.34 + c, 0.34 - c):
            pts.append((x, y, z))
        xi = cx + (x - cx) * (0.47 - c) / 0.47
        zi = cz + (z - cz) * (0.43 - c) / 0.43
        for y in (-0.34, 0.34):
            pts.append((xi, y, zi))
    hullp(m, pts, 'pink')
    # sleeve: the card band, lips at both edges, labels both sides, a yellow stripe
    m.bx(-0.2, -0.353, 0.004, 0.2, 0.353, 0.866, 'crayB')
    for x in (-0.2, 0.2):
        m.bx(x - 0.012, -0.358, 0.012, x + 0.012, 0.358, 0.872, 'crayB')
        m.flat()
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.358, s * 0.362))
        m.bx(-0.13, y0, 0.36, 0.13, y1, 0.5, 'white', flat=True)
        m.bx(-0.17, y0, 0.62, 0.17, y1, 0.67, 'crayY', flat=True)
        y0, y1 = sorted((s * 0.362, s * 0.366))
        m.bx(-0.1, y0, 0.41, 0.06, y1, 0.43, 'ink', flat=True)
    # crumbs by the rubbed end
    for (x, y, r) in ((0.46, -0.41, 0.035), (0.43, 0.42, 0.03), (0.4, -0.45, 0.022)):
        hullp(m, [(x - r, y - r * 0.8, 0), (x + r, y - r * 0.6, 0), (x + r * 0.7, y + r, 0), (x - r * 0.8, y + r * 0.7, 0),
                  (x, y, r * 1.3)], 'pink')
        m.flat()


def lobed_crown(m, x, y, z, r, h, color, lobes, seg=20):
    """A flat tree crown on the window glass: the outline of a union of round lobes (centre lobe r plus `lobes`
    [(dx, dz, rr)]), extruded h toward -Y like disc(); one shape, no outline (the caller marks it flat)."""
    circles = [(0.0, 0.0, r)] + list(lobes)
    pts = []
    for i in range(seg):
        t = i / seg * 2 * math.pi
        ux, uz = math.cos(t), math.sin(t)
        best = 0.0
        for (cx, cz, rr) in circles:
            # far intersection of the ray from the origin with this circle
            b = ux * cx + uz * cz
            c = cx * cx + cz * cz - rr * rr
            disc_ = b * b - c
            if disc_ >= 0:
                best = max(best, b + math.sqrt(disc_))
        pts.append((ux * best, uz * best))
    bm = m.bm
    P = m.parent @ Matrix.Translation((x, y, z))
    back = [bm.verts.new(P @ Vector((px, 0.0, pz))) for (px, pz) in pts]
    front = [bm.verts.new(P @ Vector((px, -h, pz))) for (px, pz) in pts]
    fs = [bm.faces.new(back), bm.faces.new(front[::-1])]
    for i in range(seg):
        j = (i + 1) % seg
        fs.append(bm.faces.new((back[i], back[j], front[j], front[i])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    m.nshape += 1
    ci = m.pal.index(color)
    for f in fs:
        f[m.shape] = m.nshape
        f.material_index = ci
    return fs
