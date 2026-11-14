"""INKBOLT sculpted shape helpers for the ground robots (fam_bots.py: Crawler, Gunner, Bomber, Blade Bot).

The robots were built from boxes, plain prisms and 5..10-sided cylinders; these helpers give them rounded and
chamfered hard-surface forms at a game budget. Every helper draws on a fam_bots.Part (silhouette shapes keep the
ink outline, deco=True shapes have none) and makes ONE closed shape per call, so the strict z-fighting check sees it
as one shape. Rounding is spent on the silhouette: corner fillets of 1..3 segments, chamfers of 1..2 segments.

  loft(p, rings, ...)          rings of points (same count) joined into a closed solid (ngon caps or poles)
  rrect / squircle / fillet    2D sections: rounded rectangle, superellipse, a polygon with filleted corners
  inset(poly, d)               a convex-ish polygon moved inward by d (the chamfer / rounding of the ends)
  cprism(p, poly, z0, z1, c)   a section extruded along local z with chamfered (cseg=1) or rounded (2) end edges
  sprism2(p, poly_yz, x0, x1)  the same on a side profile (y, z), extruded along X (as fam_bots.sprism)
  rbox(p, loc, size, r, c)     rounded box: rounded-rectangle section along local z, chamfered / rounded ends
  slathe(p, prof, ...)         superellipse lathe: a lathe whose section is a squircle (rounded square body)
  sweep(p, prof_rz, a0, a1)    a closed (r, z) profile swept round Z from angle a0 to a1: curved armour plates
  tlimb(p, a, b, r1, r2)       tapered limb with chamfered ends (round, or squircle section)
  blade(p, st, tip, ...)       blade with a chamfered spine, flats, a ridge line and a bevelled (ground) edge
"""
import math

from mathutils import Matrix, Vector

from ib_lib import mat_trs

YZX = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # local (a, b, c) -> world (c, a, b)


# ---------------------------------------------------------------- 2D sections
def parea(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, list(poly[1:]) + list(poly[:1]))) / 2


def ccw(poly):
    poly = [tuple(q) for q in poly]
    return poly if parea(poly) > 0 else list(reversed(poly))


def rrect(w, h, r, n=2, cx=0.0, cy=0.0):
    """Rounded rectangle w x h, corner radius r, n segments per corner (n=1: chamfered corners); CCW."""
    r = max(min(r, w / 2 - 1e-4, h / 2 - 1e-4), 2e-4)
    pts = []
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        ox, oy = cx + sx * (w / 2 - r), cy + sy * (h / 2 - r)
        for j in range(n + 1):
            a = math.pi / 2 * (i + j / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def squircle(rx, ry, seg, e=4.0, cx=0.0, cy=0.0, phase=0.0):
    """Superellipse |x/rx|^e + |y/ry|^e = 1 sampled at seg angles (e=2: ellipse, 4: rounded square); CCW."""
    pts = []
    for k in range(seg):
        a = phase + 2 * math.pi * k / seg
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + rx * math.copysign(abs(c) ** (2 / e), c), cy + ry * math.copysign(abs(s) ** (2 / e), s)))
    return pts


def fillet(poly, r, n=2):
    """Round the corners of a polygon: r is one radius or a list per vertex (0 keeps the corner sharp)."""
    poly = [tuple(q) for q in poly]
    m = len(poly)
    rs = list(r) if isinstance(r, (list, tuple)) else [r] * m
    if parea(poly) < 0:
        poly, rs = poly[::-1], rs[::-1]
    out = []
    for i in range(m):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % m])
        ri = rs[i]
        a, b = p0 - p1, p2 - p1
        la, lb = a.length, b.length
        if ri <= 0 or la < 1e-6 or lb < 1e-6:
            out.append(tuple(p1))
            continue
        a.normalize()
        b.normalize()
        ang = math.acos(max(-1.0, min(1.0, a.dot(b))))          # interior angle between the edges
        if ang > math.pi - 1e-3:
            out.append(tuple(p1))
            continue
        t = ri / math.tan(ang / 2)
        t = min(t, 0.45 * la, 0.45 * lb)
        rr = t * math.tan(ang / 2)
        bis = (a + b).normalized()
        c = p1 + bis * (rr / math.sin(ang / 2))
        t0, t1 = p1 + a * t, p1 + b * t
        a0 = math.atan2(t0.y - c.y, t0.x - c.x)
        a1 = math.atan2(t1.y - c.y, t1.x - c.x)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(n + 1):
            q = a0 + da * j / n
            out.append((c.x + rr * math.cos(q), c.y + rr * math.sin(q)))
    return out


def inset(poly, d):
    """Move each edge of a CCW polygon inward by d (vertices along the corner bisector)."""
    m = len(poly)
    out = []
    for i in range(m):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % m])
        e0, e1 = p1 - p0, p2 - p1
        if e0.length < 1e-9 or e1.length < 1e-9:
            out.append(tuple(p1))
            continue
        e0.normalize()
        e1.normalize()
        n0, n1 = Vector((-e0.y, e0.x)), Vector((-e1.y, e1.x))
        k = 1 + n0.dot(n1)
        mv = (n0 + n1) * (d / k) if k > 0.15 else n0 * d
        out.append(tuple(p1 + mv))
    return out


# ---------------------------------------------------------------- solids
def _fix_orientation(bm, faces, verts):
    """Make a closed shape face outward (signed volume > 0)."""
    vol = 0.0
    for f in faces:
        vs = [v.co for v in f.verts]
        for k in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[k].cross(vs[k + 1]))
    if vol < 0:
        for f in faces:
            f.normal_flip()


def loft(p, rings, color, closed=True, caps=(True, True), deco=False):
    """Join rings of local points (same count; a ring of one point is a pole) into one shape on Part p."""
    for mm in p._each(deco):
        bm = mm.bm
        vr = [[bm.verts.new(mm.parent @ Vector(v)) for v in ring] for ring in rings]
        faces = []
        for a, b in zip(vr, vr[1:]):
            if len(a) == 1:
                n = len(b)
                for k in range(n if closed else n - 1):
                    faces.append(bm.faces.new((a[0], b[(k + 1) % n], b[k])))
            elif len(b) == 1:
                n = len(a)
                for k in range(n if closed else n - 1):
                    faces.append(bm.faces.new((a[k], a[(k + 1) % n], b[0])))
            else:
                n = len(a)
                for k in range(n if closed else n - 1):
                    k2 = (k + 1) % n
                    faces.append(bm.faces.new((a[k], a[k2], b[k2], b[k])))
        if caps[0] and len(vr[0]) > 2:
            faces.append(bm.faces.new(list(reversed(vr[0]))))
        if caps[1] and len(vr[-1]) > 2:
            faces.append(bm.faces.new(vr[-1]))
        if closed and (caps[0] or len(vr[0]) == 1) and (caps[1] or len(vr[-1]) == 1):
            _fix_orientation(bm, faces, None)
        mm._finish([v for r in vr for v in r], color, False)


def _ends(poly, z0, z1, c, cseg):
    """Rings of a section between z0 and z1 with its ends chamfered (cseg=1) or rounded (cseg>=2) by c; c may be a
    pair (c at z0, c at z1), 0 leaving that end square."""
    c0, c1 = c if isinstance(c, (list, tuple)) else (c, c)
    lim = (z1 - z0) / (2 if c0 > 0 and c1 > 0 else 1) - 1e-4
    c0, c1 = min(c0, lim), min(c1, lim)
    prof = [(1 - math.sin(math.pi / 2 * j / cseg), 1 - math.cos(math.pi / 2 * j / cseg)) for j in range(cseg + 1)]
    lo = [[(x, y, z0 + c0 * h) for x, y in inset(poly, c0 * d)] for d, h in prof] if c0 > 0 else [[(x, y, z0) for x, y in poly]]
    hi = [[(x, y, z1 - c1 * h) for x, y in inset(poly, c1 * d)] for d, h in reversed(prof)] if c1 > 0 else [[(x, y, z1) for x, y in poly]]
    if abs(lo[-1][0][2] - hi[0][0][2]) < 1e-4:
        hi = hi[1:]
    return lo + hi


def cprism(p, poly, z0, z1, color, c=0.0, cseg=1, deco=False, frame=None):
    """Section `poly` (x, y) extruded from z0 to z1 with chamfered / rounded end edges (c deep, cseg segments)."""
    poly = ccw(poly)
    old = p.parent
    if frame is not None:
        p.parent = old @ frame
    loft(p, _ends(poly, min(z0, z1), max(z0, z1), c, cseg), color, deco=deco)
    p.parent = old


def sprism2(p, poly_yz, x0, x1, color, c=0.0, cseg=1, r=0.0, n=2, deco=False):
    """Side profile (y, z) extruded along X from x0 to x1: corners filleted by r (per vertex list allowed), the
    two side faces chamfered (cseg=1) or rounded by c (a pair: c at x0, c at x1)."""
    poly = fillet(poly_yz, r, n) if (isinstance(r, (list, tuple)) or r > 0) else ccw(poly_yz)
    if x0 > x1:
        x0, x1 = x1, x0
        c = tuple(reversed(c)) if isinstance(c, (list, tuple)) else c
    cprism(p, poly, x0, x1, color, c, cseg, deco, frame=YZX)


def rbox(p, loc, size, color, r=0.02, c=0.0, n=2, cseg=1, rot=(0, 0, 0), deco=False):
    """Box with rounded vertical edges (radius r, n segments) and chamfered / rounded top and bottom edges (c)."""
    w, d, h = size
    cprism(p, rrect(w, d, r, n), -h / 2, h / 2, color, c, cseg, deco, frame=mat_trs(loc, rot))


def slathe(p, prof, color, seg=16, e=4.0, phase=0.0, deco=False, sx=1.0, sy=1.0):
    """Superellipse lathe about Z: prof = [(r, z), ...] bottom to top (r=0: a pole); section exponent e."""
    rings = []
    for r, z in prof:
        if r <= 1e-6:
            rings.append([(0, 0, z)])
        else:
            rings.append([(x, y, z) for x, y in squircle(r * sx, r * sy, seg, e, phase=phase)])
    loft(p, rings, color, deco=deco)


def sweep(p, prof_rz, a0, a1, seg, color, deco=False, frame=None):
    """Closed (r, z) profile swept round Z from angle a0 to a1 (radians) in seg steps: a curved plate / band."""
    old = p.parent
    if frame is not None:
        p.parent = old @ frame
    rings = []
    for k in range(seg + 1):
        a = a0 + (a1 - a0) * k / seg
        ca, sa = math.cos(a), math.sin(a)
        rings.append([(r * ca, r * sa, z) for r, z in prof_rz])
    # rings run along the sweep; each ring is the profile: loft them with ngon caps at the two ends
    loft(p, rings, color, deco=deco)
    p.parent = old


def arc_plate(p, r0, r1, z0, z1, a0, a1, seg, color, c=0.0, deco=False, frame=None):
    """Curved plate between radii r0 < r1, heights z0..z1, angles a0..a1 (degrees); outer edges chamfered by c."""
    if c > 0:
        prof = [(r0, z0), (r1 - c, z0), (r1, z0 + c), (r1, z1 - c), (r1 - c, z1), (r0, z1)]
    else:
        prof = [(r0, z0), (r1, z0), (r1, z1), (r0, z1)]
    sweep(p, prof, math.radians(a0), math.radians(a1), seg, color, deco, frame)


def along(a, b):
    """Frame with local +z from point a toward b (origin at a); returns (matrix, length)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return Matrix.Translation(a) @ q.to_matrix().to_4x4(), d.length


def tlimb(p, a, b, r1, r2, color, seg=8, c=(0.0, 0.0), e=2.0, deco=False, sxy=(1.0, 1.0)):
    """Tapered limb from a (radius r1) to b (r2); ends chamfered by c = (c_a, c_b) (an end of c=0 is flat);
    e > 2 gives a squircle (armoured, rounded-square) section."""
    m, L = along(a, b)
    old = p.parent
    p.parent = old @ m
    sec = lambda r, z: [(x, y, z) for x, y in squircle(r * sxy[0], r * sxy[1], seg, e, phase=math.pi / seg)]
    rings = []
    if c[0] > 0:
        rings.append(sec(r1 * 0.55, 0.0))
        rings.append(sec(r1, c[0]))
    else:
        rings.append(sec(r1, 0.0))
    if c[1] > 0:
        rings.append(sec(r2, L - c[1]))
        rings.append(sec(r2 * 0.55, L))
    else:
        rings.append(sec(r2, L))
    loft(p, rings, color, deco=deco)
    p.parent = old


def ball(p, loc, r, color, seg=(10, 6), scale=(1, 1, 1), deco=False):
    p.sphere(loc, r, color, seg=seg, scale=scale, deco=deco)


def torus(p, R, rr, color, seg=8, rs=4, phase=0.0, deco=False, frame=None):
    """Ring about local Z (major radius R, tube radius rr)."""
    old = p.parent
    if frame is not None:
        p.parent = old @ frame
    rings = []
    for k in range(rs):
        a = 2 * math.pi * k / rs + math.pi / rs
        r, z = R + rr * math.cos(a), rr * math.sin(a)
        rings.append([(r * math.cos(phase + 2 * math.pi * j / seg), r * math.sin(phase + 2 * math.pi * j / seg), z) for j in range(seg)])
    for mm in p._each(deco):
        bm = mm.bm
        vr = [[bm.verts.new(mm.parent @ Vector(v)) for v in ring] for ring in rings]
        faces = []
        for i in range(rs):
            A, B = vr[i], vr[(i + 1) % rs]
            for j in range(seg):
                j2 = (j + 1) % seg
                faces.append(bm.faces.new((A[j], A[j2], B[j2], B[j])))
        _fix_orientation(bm, faces, None)
        mm._finish([v for r in vr for v in r], color, False)
    p.parent = old


def blade(p, st, tip, color, edge_color, spine=0.35, deco=False):
    """Blade along +X, edge on +Y: stations (x, y_back, y_edge, half_thickness, ridge) with ridge = where the flat
    turns into the ground bevel (0..1 from back to edge). Section: chamfered spine, flats, ridge, bevel to the edge;
    the bevel faces take edge_color; ends in the tip point."""
    for mm in p._each(deco):
        bm = mm.bm
        rings = []
        for s in st:
            x, yb, ye, t = s[:4]
            rg = s[4] if len(s) > 4 else 0.62
            yr = yb + (ye - yb) * rg
            ys = yb + (ye - yb) * 0.08
            pts = ((x, yb, t * spine), (x, ys, t), (x, yr, t), (x, ye, 0.0), (x, yr, -t), (x, ys, -t), (x, yb, -t * spine))
            rings.append([bm.verts.new(mm.parent @ Vector(q)) for q in pts])
        tv = bm.verts.new(mm.parent @ Vector(tip))
        faces = [bm.faces.new(list(reversed(rings[0])))]
        edge = []
        for a, b in zip(rings, rings[1:]):
            for k in range(7):
                k2 = (k + 1) % 7
                f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
                faces.append(f)
                if k in (2, 3):
                    edge.append(f)
        r = rings[-1]
        for k in range(7):
            f = bm.faces.new((r[k], r[(k + 1) % 7], tv))
            faces.append(f)
            if k in (2, 3):
                edge.append(f)
        _fix_orientation(bm, faces, None)
        mm._finish([v for ring in rings for v in ring] + [tv], color, False)
        ei = mm.pal.index(edge_color)
        for f in edge:
            f.material_index = ei
