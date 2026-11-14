"""INKBOLT sculpted shape helpers for the air robots of fam_bots.py (Jet Trooper, Hawk, Drone).

Rounded, chamfered and tapered forms built as lofts (rings of points joined by quads), drawn into a fam_bots Part
(silhouette shapes keep the ink outline, deco=True shapes do not). Every helper works in the Part's current frame
(`p.parent`), so frames from fam_bots (_jframe, Matrix.Translation ...) place them.

  ring_se    superellipse ring (rounded square at e ~ 3-4, ellipse at e = 2), separate front (-y) and back depths
  ring_rr    rounded / chamfered rectangle ring (nc = 1: chamfer, 2-3: round corners)
  loft       join rings (a ring of one point is a pole) with caps
  slab       rounded-rectangle block with chamfered top and bottom (plates, blocks, boxes)
  pod        superellipse block with chamfered ends along any axis (helper over slab for se rings)
  limb       tapered limb along local Z from superellipse stations (thighs, shins, arms, fuselages)
  shell      curved armour plate: an elliptical arc band of a given thickness, swept along Z by stations, with
             slanted (chamfered) side edges and inset ends
  sweep      a thin strip of rectangular section along a path on a surface (accent lines, slits, seams)
  lathe_r    a smooth surface of revolution about Z (bells, nozzles, domes) with optional poles
  ring_ch    chamfered rectangle ring (8 points: one flat 45 degree facet per corner), optional front / back keel
  flimb      faceted limb / block along local Z from ring_ch stations (hard-surface armour: flat planes, crisp edges)
  plate      flat armour plate from a convex outline, its top rim chamfered once (layered angular plates)

Edges between faces under 40 degrees shade smooth (ib_lib.build_object), so a ring of 12-16 points reads round in
the toon bands; a single 45 degree chamfer step stays a crisp chamfer.
"""
import math

import bmesh
from mathutils import Matrix, Vector


def _orient(bm, faces):
    """make a closed shape's faces point outward (signed volume test: sum of n . x over the faces = 3 V)"""
    faces = [f for f in faces if f.is_valid]
    for f in faces:
        f.normal_update()
    if sum(f.normal.dot(f.calc_center_median()) * f.calc_area() for f in faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=faces)


def _sp(c, e):
    return math.copysign(abs(c) ** (2.0 / e), c)


def ring_se(a, bf, bb=None, n=16, e=2.5, z=0.0, cx=0.0, cy=0.0, phase=0.0):
    """Superellipse ring in the XY plane at height z, counter-clockwise from +Z: half width a, half depth bf to the
    front (-y) and bb to the back (+y)."""
    bb = bf if bb is None else bb
    out = []
    for k in range(n):
        t = phase + 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        out.append((cx + a * _sp(c, e), cy + (bb if s > 0 else bf) * _sp(s, e), z))
    return out


def ring_rr(hw, hd, r, nc=2, z=0.0, cx=0.0, cy=0.0):
    """Rounded rectangle ring (half sizes hw, hd, corner radius r, nc steps per corner), counter-clockwise."""
    r = max(1e-4, min(r, hw - 1e-4, hd - 1e-4))
    out = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (hw - r), cy + qy * (hd - r)
        for k in range(nc + 1):
            a = math.radians(a0 + 90.0 * k / nc)
            out.append((ox + r * math.cos(a), oy + r * math.sin(a), z))
    return out


def _emit(p, rings, color, cap0, cap1, deco, closed=True):
    for mm in p._each(deco):
        bm = mm.bm
        vr = [[bm.verts.new(mm.parent @ Vector(q)) for q in ring] for ring in rings]
        nf = len(bm.faces)
        for a, b in zip(vr, vr[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            n = max(len(a), len(b))
            rng = range(n) if closed else range(n - 1)
            for k in rng:
                k2 = (k + 1) % n
                if len(a) == 1:
                    bm.faces.new((a[0], b[k], b[k2]))
                elif len(b) == 1:
                    bm.faces.new((a[k], a[k2], b[0]))
                else:
                    bm.faces.new((a[k], a[k2], b[k2], b[k]))
        if cap0 and len(vr[0]) > 2:
            bm.faces.new(list(reversed(vr[0])))
        if cap1 and len(vr[-1]) > 2:
            bm.faces.new(vr[-1])
        bm.faces.ensure_lookup_table()
        _orient(bm, [bm.faces[i] for i in range(nf, len(bm.faces))])
        mm._finish([v for ring in vr for v in ring], color, False)


def loft(p, rings, color, caps=True, deco=False):
    """Rings bottom to top (counter-clockwise seen from the top end, all of one point count; a one-point ring is a
    pole), joined by quads; flat caps on the open ends."""
    _emit(p, rings, color, caps, caps, deco)


def slab(p, hw, hd, h, r, ch, color, nc=2, z0=0.0, cx=0.0, cy=0.0, top=None, deco=False):
    """Rounded-rectangle block from z0 to z0 + h with ch chamfers on the top and bottom rims; `top` = (hw, hd) of
    the top face to taper it."""
    tw, td = top or (hw, hd)
    rings = []
    for z, w, d, k in ((z0, hw, hd, ch), (z0 + ch, hw, hd, 0), (z0 + h - ch, tw, td, 0), (z0 + h, tw, td, ch)):
        rings.append(ring_rr(w - k, d - k, r - k * 0.6, nc, z, cx, cy))
    loft(p, rings, color, deco=deco)


def frame(origin, axis, up=(0, 0, 1)):
    """A frame at origin whose local +Z runs along axis (local +Y leans to `up`)."""
    z = Vector(axis).normalized()
    u = Vector(up)
    if abs(u.normalized().dot(z)) > 0.98:
        u = Vector((0, 1, 0)) if abs(z.y) < 0.9 else Vector((1, 0, 0))
    y = (u - z * u.dot(z)).normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


class at_frame:
    """with at_frame(p, M): draw in frame M (relative to the Part's current frame)."""

    def __init__(self, p, M):
        self.p, self.M = p, M

    def __enter__(self):
        self.old = self.p.parent
        self.p.parent = self.old @ self.M
        return self.p

    def __exit__(self, *a):
        self.p.parent = self.old


def limb(p, st, color, n=12, e=2.4, deco=False, pole0=None, pole1=None):
    """Tapered limb along local Z: stations (z, a, bf, bb, cx, cy) give superellipse rings; pole0 / pole1 close an
    end with a point (a rounded end) instead of a flat cap."""
    rings = []
    for s in st:
        z, a, bf, bb = s[:4]
        cx, cy = (s[4] if len(s) > 4 else 0.0), (s[5] if len(s) > 5 else 0.0)
        rings.append(ring_se(a, bf, bb, n, e, z, cx, cy))
    if pole0 is not None:
        rings.insert(0, [(st[0][4] if len(st[0]) > 4 else 0.0, st[0][5] if len(st[0]) > 5 else 0.0, pole0)])
    if pole1 is not None:
        rings.append([(st[-1][4] if len(st[-1]) > 4 else 0.0, st[-1][5] if len(st[-1]) > 5 else 0.0, pole1)])
    loft(p, rings, color, deco=deco)


def capsule(p, a, b, color, r, n=10, e=2.0, rr=None, deco=False):
    """Round rod from point a to point b (radius r, or r..rr tapered), ends domed with one chamfer step."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    rr = r if rr is None else rr
    with at_frame(p, frame(a, b - a)):
        limb(p, [(0.0, r * 0.62, r * 0.62, r * 0.62), (r * 0.35, r, r, r), (L - rr * 0.35, rr, rr, rr), (L, rr * 0.62, rr * 0.62, rr * 0.62)],
             color, n=n, e=e, deco=deco)


def shell(p, st, phi0, phi1, color, k=6, cham=0.5, deco=False, e=2.0):
    """Curved armour plate around local Z: stations (z, a, b, t, cx, cy) give the outer ellipse (a, b) and the
    thickness t at height z; the plate spans angles phi0..phi1 (degrees, 0 = +x, -90 = front / -y) with k steps.
    The outer arc is trimmed by `cham` x t at both side edges (slanted, chamfered sides); the end stations are
    the user's to inset (smaller a / b / t) for chamfered ends. Caps are quad strips (no concave n-gons).
    e > 2 follows a superellipse (as ring_se) instead of the ellipse, to hug a ring_se body."""
    rings = []
    for s in st:
        z, a, b, t = s[:4]
        cx, cy = (s[4] if len(s) > 4 else 0.0), (s[5] if len(s) > 5 else 0.0)
        ro = (a + b) / 2
        d = math.degrees(cham * t / max(ro, 1e-3))
        out = []
        for i in range(k + 1):
            f = math.radians(phi0 + d + (phi1 - phi0 - 2 * d) * i / k)
            out.append((cx + a * _sp(math.cos(f), e), cy + b * _sp(math.sin(f), e), z))
        inn = []
        for i in range(k, -1, -1):
            f = math.radians(phi0 + (phi1 - phi0) * i / k)
            inn.append((cx + (a - t) * _sp(math.cos(f), e), cy + (b - t) * _sp(math.sin(f), e), z))
        rings.append(out + inn)
    for mm in p._each(deco):
        bm = mm.bm
        vr = [[bm.verts.new(mm.parent @ Vector(q)) for q in ring] for ring in rings]
        nf = len(bm.faces)
        m = len(vr[0])
        for ra, rb in zip(vr, vr[1:]):
            for i in range(m):
                i2 = (i + 1) % m
                bm.faces.new((ra[i], ra[i2], rb[i2], rb[i]))
        for ring, flip in ((vr[0], True), (vr[-1], False)):
            for i in range(k):
                q = (ring[i], ring[i + 1], ring[m - 2 - i], ring[m - 1 - i])
                bm.faces.new(tuple(reversed(q)) if flip else q)
        bm.faces.ensure_lookup_table()
        _orient(bm, [bm.faces[i] for i in range(nf, len(bm.faces))])
        mm._finish([v for ring in vr for v in ring], color, False)


def sweep(p, pts, normals, w, t, color, off=0.0, deco=True, closed=False):
    """A strip of section w x t along the path pts (each with the outward surface normal), standing from `off`
    to off + t over the surface (deco details: off <= 0 starts inside, off + t >= 3 mm proud)."""
    P = [Vector(q) for q in pts]
    N = [Vector(q).normalized() for q in normals]
    rings = []
    m = len(P)
    for i in range(m):
        if closed:
            d = P[(i + 1) % m] - P[i - 1]
        else:
            d = P[min(i + 1, m - 1)] - P[max(i - 1, 0)]
        d.normalize()
        u = N[i].cross(d).normalized()
        n = d.cross(u).normalized()
        if n.dot(N[i]) < 0:
            n = -n
        c0, c1 = P[i] + n * off, P[i] + n * (off + t)
        rings.append([tuple(c0 - u * w / 2), tuple(c0 + u * w / 2), tuple(c1 + u * w / 2), tuple(c1 - u * w / 2)])
    if closed:
        rings.append(rings[0])
        for mm in p._each(deco):
            bm = mm.bm
            vr = [[bm.verts.new(mm.parent @ Vector(q)) for q in ring] for ring in rings[:-1]]
            vr.append(vr[0])
            nf = len(bm.faces)
            for a, b in zip(vr, vr[1:]):
                for k in range(4):
                    k2 = (k + 1) % 4
                    bm.faces.new((a[k], a[k2], b[k2], b[k]))
            bm.faces.ensure_lookup_table()
            _orient(bm, [bm.faces[i] for i in range(nf, len(bm.faces))])
            mm._finish([v for ring in vr[:-1] for v in ring], color, False)
        return
    loft(p, rings, color, deco=deco)


def ring_band(p, ring, nrm_fn, w, t, color, off=0.0, deco=True):
    """A closed accent band following a ring of points (outward normals from nrm_fn(point))."""
    sweep(p, ring, [nrm_fn(q) for q in ring], w, t, color, off=off, deco=deco, closed=True)


def lathe_r(p, prof, color, seg=12, phase=0.0, deco=False):
    """Surface of revolution about Z from profile [(r, z)] bottom to top; r = 0 is a pole; flat caps elsewhere."""
    rings = []
    for r, z in prof:
        if r <= 1e-6:
            rings.append([(0.0, 0.0, z)])
        else:
            rings.append([(r * math.cos(phase + 2 * math.pi * k / seg), r * math.sin(phase + 2 * math.pi * k / seg), z) for k in range(seg)])
    loft(p, rings, color, deco=deco)


def se_point(a, bf, bb, e, t, cx=0.0, cy=0.0):
    """point at parameter angle t on a ring_se outline, with its outward normal (2D)"""
    c, s = math.cos(t), math.sin(t)
    b = bb if s > 0 else bf
    x, y = cx + a * _sp(c, e), cy + b * _sp(s, e)
    # normal of |x/a|^e + |y/b|^e: grad = (sgn x |x/a|^(e-1) / a, sgn y |y/b|^(e-1) / b)
    gx = math.copysign(abs(_sp(c, e)) ** (e - 1), c) / a
    gy = math.copysign(abs(_sp(s, e)) ** (e - 1), s) / b
    g = Vector((gx, gy, 0.0))
    if g.length < 1e-9:
        g = Vector((c, s, 0.0))
    return Vector((x, y, 0.0)), g.normalized()


def se_path(a, b, degs, z, e=2.0, cx=0.0, cy=0.0, out=0.0):
    """points (and outward normals) on a superellipse outline (ellipse at e = 2) at parameter angles `degs`, height
    z, pushed `out` along the normal: a path for sweep() across a curved plate"""
    pts, nrm = [], []
    for d in degs:
        q, n = se_point(a, b, b, e, math.radians(d), cx, cy)
        q = q + n * out
        pts.append((q.x, q.y, z))
        nrm.append((n.x, n.y, 0.0))
    return pts, nrm


# ---------------------------------------------------------------- faceted hard-surface shapes (Jet Trooper)
def ring_ch(hw, hdf, hdb=None, ch=0.02, z=0.0, cx=0.0, cy=0.0, kf=None, kb=None):
    """Chamfered rectangle ring at height z, counter-clockwise from +Z: half width hw, half depth hdf to the front (-y)
    and hdb to the back (+y), one flat 45 degree chamfer of ch on each corner: 8 points. With kf / kb (even 0) it gets
    a keel point in the middle of the front / back face, kf / kb proud of it: 10 points (a V-shaped front reads sleek)."""
    hdb = hdf if hdb is None else hdb
    c = max(1e-4, min(ch, hw - 1e-4, hdf - 1e-4, hdb - 1e-4))
    out = [(cx + hw, cy - hdf + c, z), (cx + hw, cy + hdb - c, z), (cx + hw - c, cy + hdb, z)]
    if kb is not None:
        out.append((cx, cy + hdb + kb, z))
    out += [(cx - hw + c, cy + hdb, z), (cx - hw, cy + hdb - c, z), (cx - hw, cy - hdf + c, z), (cx - hw + c, cy - hdf, z)]
    if kf is not None:
        out.append((cx, cy - hdf - kf, z))
    out.append((cx + hw - c, cy - hdf, z))
    return out


def flimb(p, st, color, deco=False, caps=True):
    """Faceted limb / block along local Z: stations (z, hw, hdf, hdb, ch[, cx, cy[, kf, kb]]) give ring_ch rings
    (all stations of one call with or without the keel numbers, so the rings match)."""
    rings = []
    for s in st:
        z, hw, hdf, hdb, ch = s[:5]
        cx, cy = (s[5], s[6]) if len(s) > 6 else (0.0, 0.0)
        kf, kb = (s[7], s[8]) if len(s) > 8 else (None, None)
        rings.append(ring_ch(hw, hdf, hdb, ch, z, cx, cy, kf, kb))
    loft(p, rings, color, caps=caps, deco=deco)


def _inset(poly, d):
    """a convex counter-clockwise polygon moved in by d on every edge (same vertex count)"""
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey) or 1.0
        nx, ny = -ey / L, ex / L                     # left of the edge = inside for a counter-clockwise polygon
        lines.append((ax + nx * d, ay + ny * d, ex, ey))
    out = []
    for i in range(n):
        px, py, ux, uy = lines[i - 1]
        qx, qy, vx, vy = lines[i]
        den = ux * vy - uy * vx
        if abs(den) < 1e-12:
            out.append((qx, qy))
            continue
        t = ((qx - px) * vy - (qy - py) * vx) / den
        out.append((px + ux * t, py + uy * t))
    return out


def plate(p, poly, t, color, ch=None, z0=0.0, deco=False):
    """Flat armour plate in the current frame: the convex outline poly (local XY) from z0 up to z0 + t along local +Z,
    the top rim chamfered once by ch (45 degrees): flat planes, crisp edges that catch the light."""
    if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) < 0:
        poly = list(reversed(poly))
    ch = t * 0.4 if ch is None else ch
    top = _inset(poly, ch)
    rings = [[(x, y, z0) for x, y in poly], [(x, y, z0 + t - ch) for x, y in poly], [(x, y, z0 + t) for x, y in top]]
    loft(p, rings, color, deco=deco)


def plate_at(p, origin, normal, up, poly, t, color, ch=None, z0=0.0, deco=False):
    """plate() in a frame at origin whose local +Z is normal (local +Y leans to up)"""
    with at_frame(p, frame(origin, normal, up)):
        plate(p, poly, t, color, ch=ch, z0=z0, deco=deco)
