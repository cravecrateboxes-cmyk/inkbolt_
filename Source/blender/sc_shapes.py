"""kit-smallcity remodelled shapes (map asset upgrade pass): the props that read as plain primitives (lollipop street
trees, box cars, ball trash bags, plain cubes) rebuilt with real silhouettes. Works on the kit's PM model (see
fam_kit_smallcity.py): outlined shapes keep the full ink shell, small detail is hull='none' and stands >= 3 mm proud.
Nothing here moves a piece's origin, footprint or collision boxes."""
import math
import random

import bmesh
from mathutils import Vector


# ---------------------------------------------------------------------------------------------- primitives
def hullp(m, pts, color, hull='full'):
    """Convex hull of points (piece frame) as one shape; color: palette name or fn(face) -> name."""
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
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return fs


def blob(m, rnd, c, r, color, n=11, squash=(1.0, 1.0, 0.8), jag=0.18, hull='full'):
    """Irregular faceted lump (a foliage clump, a stuffed bag): points on a jittered sphere, hulled."""
    pts = []
    for i in range(n):
        # golden-angle spiral, each point pushed in or out
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996 + rnd.uniform(-0.3, 0.3)
        k = r * rnd.uniform(1 - jag, 1 + jag * 0.5)
        pts.append((c[0] + math.cos(a) * rr * k * squash[0], c[1] + math.sin(a) * rr * k * squash[1], c[2] + z * k * squash[2]))
    return hullp(m, pts, color, hull)


# ---------------------------------------------------------------------------------------------- street tree
def street_tree(m, rnd):
    """A young plane tree: tapered trunk with a flare, three limbs forking at 1.9 m, and a canopy of eight faceted
    leaf clumps in three greens round the limb ends (lit tops lighter, undersides darker)."""
    m.cy((0, 0, 0.044), 0.13, 0.085, 2.05, 'trunk', seg=7)
    hullp(m, [(math.cos(a) * 0.19, math.sin(a) * 0.19, 0.05) for a in [i * 1.26 for i in range(5)]] +
          [(math.cos(a) * 0.11, math.sin(a) * 0.11, 0.3) for a in [i * 1.26 + 0.6 for i in range(5)]], 'trunk')
    ends = []
    for k, (a, tilt, L) in enumerate(((0.3, 46, 1.45), (2.4, 42, 1.35), (4.3, 50, 1.4))):
        a += rnd.uniform(-0.2, 0.2)
        r = L * math.sin(math.radians(tilt))
        e = (math.cos(a) * r, math.sin(a) * r, 1.95 + L * math.cos(math.radians(tilt)))
        m.bm_((0, 0, 1.85 + k * 0.08), e, 0.09 - k * 0.01, 'trunk')
        ends.append(e)
    m.bm_((0, 0, 2.0), (0.05, -0.04, 3.1), 0.08, 'trunk')            # leader

    def leafc(f):
        return 'leaf2' if f.normal.z > 0.45 else ('leafD' if f.normal.z < -0.25 else 'leaf')
    for i, e in enumerate(ends):
        blob(m, rnd, (e[0], e[1], e[2] + 0.2), rnd.uniform(0.78, 0.92), leafc, n=12, squash=(1.0, 1.0, 0.75))
    for i in range(4):
        a = i * 1.57 + rnd.uniform(-0.3, 0.3) + 0.8
        blob(m, rnd, (math.cos(a) * 0.75, math.sin(a) * 0.75, 3.05 + rnd.uniform(-0.15, 0.25)), rnd.uniform(0.6, 0.72), leafc, n=10)
    blob(m, rnd, (0.0, 0.0, 3.75), 0.85, leafc, n=12, squash=(1.0, 1.0, 0.72))


# ---------------------------------------------------------------------------------------------- vehicles
def arch(yc, r, z0, n=6):
    """Wheel-arch points (y, z) over a wheel centred at y = yc: from the back (+y) side over to the front (-y) side,
    starting and ending at the sill z0."""
    pts = [(yc + r, z0)]
    for i in range(n + 1):
        a = i / n * math.pi
        pts.append((yc + math.cos(a) * r, z0 + 0.04 + math.sin(a) * (r - 0.04)))
    pts.append((yc - r, z0))
    return pts


def body_profile(front, rear, sill, arches, top):
    """Side profile of a vehicle body (y, z), front = -y: the sill line with arches cut over the wheels, then the
    top line (front to back points given as `top`, which starts at the front bumper and ends at the rear)."""
    bottom = [(rear, sill)]
    for yc, r in sorted(arches, reverse=True):
        bottom += arch(yc, r, sill)
    bottom.append((front, sill))
    return bottom + top


def car_body(m, body, half=0.89):
    """Shaped lower body for a 2 x 4 car: a nose and tail that step down from the waist, a sloped hood, rounded wheel
    arches over the wheels (dark liners behind them) and a black sill."""
    top = [(-1.92, 0.78), (-1.86, 0.84), (-1.66, 0.89), (-0.78, 0.9), (1.0, 0.9), (1.74, 0.89), (1.9, 0.84), (1.92, 0.8)]
    prof = body_profile(-1.92, 1.92, 0.3, [(-1.22, 0.42), (1.22, 0.42)], top)
    m.prism(prof, -half, half, [body], bevel=True)
    for yc in (-1.22, 1.22):                                                  # arch liners (between the tyres)
        m.bx(-0.62, 0.62, yc - 0.4, yc + 0.4, 0.33, 0.72, 'iron', hull='none', cull='b')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (half - 0.003), sx * (half + 0.011)))
        m.bx(x0, x1, -0.78, 0.78, 0.31, 0.38, 'iron', hull='none')             # sill strip between the arches
        x0, x1 = sorted((sx * (half - 0.003), sx * (half + 0.014)))
        for y in (-0.42, 0.42):
            m.bx(x0, x1, y - 0.07, y + 0.01, 0.74, 0.77, 'chrome', hull='none')   # door handles


def van_body(m):
    """Delivery van: cab lower with a short sloped nose and a front arch, cargo box with a rear arch."""
    prof = body_profile(-2.42, -1.12, 0.34, [(-1.62, 0.46)], [(-2.42, 0.95), (-2.36, 1.12), (-2.25, 1.25), (-1.12, 1.25)])
    m.prism(prof, -0.95, 0.95, ['paper'])
    m.bx(-0.7, 0.7, -2.06, -1.18, 0.37, 0.8, 'iron', hull='none', cull='b')
    prof = body_profile(-1.12, 2.45, 0.4, [(1.55, 0.46)], [(-1.12, 2.62), (-1.06, 2.7), (2.37, 2.7), (2.45, 2.62)])
    m.prism(prof, -0.98, 0.98, ['paper'], bevel=True)
    m.bx(-0.68, 0.68, 1.11, 1.99, 0.43, 0.86, 'iron', hull='none', cull='b')


def bus_body(m):
    """Bus: one long body with rounded front and rear caps (profile) and arches over both axles."""
    top = [(-4.42, 2.85), (-4.36, 2.98), (-4.24, 3.05), (4.26, 3.05), (4.38, 2.98), (4.42, 2.85)]
    prof = body_profile(-4.42, 4.42, 0.35, [(-2.9, 0.62), (2.75, 0.62)], top)
    m.prism(prof, -1.27, 1.27, ['carCream'], bevel=True)
    for yc in (-2.9, 2.75):
        m.bx(-0.95, 0.95, yc - 0.58, yc + 0.58, 0.38, 1.1, 'iron', hull='none', cull='b')


# ---------------------------------------------------------------------------------------------- street clutter
def trash_bags(m, rnd):
    """Four stuffed bin bags: lumpy faceted bodies, each gathered into a twisted neck and a tied tuft."""
    for (x, y, z, r, c) in ((-0.2, -0.12, 0.26, 0.3, 'bag'), (0.22, -0.05, 0.25, 0.28, 'leafD'), (0.0, 0.2, 0.24, 0.27, 'bag'),
                            (0.02, -0.02, 0.6, 0.24, 'bag')):
        blob(m, rnd, (x, y, z), r, c, n=13, squash=(1.0, 0.9, 0.92), jag=0.14)
        zt = z + r * 0.85
        hullp(m, [(x + math.cos(a) * 0.07, y + math.sin(a) * 0.07, zt - 0.04) for a in (0, 2.1, 4.2)] +
              [(x + math.cos(a) * 0.035, y + math.sin(a) * 0.035, zt + 0.08) for a in (1, 3.1, 5.2)], c)
        for k in range(3):                                                     # the tied ends
            a = k * 2.1 + rnd.uniform(-0.3, 0.3)
            hullp(m, [(x + math.cos(a) * 0.02, y + math.sin(a) * 0.02, zt + 0.07), (x - math.sin(a) * 0.02, y + math.cos(a) * 0.02, zt + 0.07),
                      (x + math.cos(a) * 0.1, y + math.sin(a) * 0.1, zt + 0.15), (x + math.cos(a) * 0.09, y + math.sin(a) * 0.09, zt + 0.12)],
                  c, hull='none')


def fruit_crate(m, cx, cy, z, w, d, fruit, rnd):
    """Slatted fruit crate: corner posts, three side slats a side with gaps, end boards with hand holes, fruit
    heaped in it."""
    h = 0.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(cx + sx * w / 2 - (0.04 if sx > 0 else 0), cx + sx * w / 2 + (0.04 if sx < 0 else 0),
                 cy + sy * d / 2 - (0.04 if sy > 0 else 0), cy + sy * d / 2 + (0.04 if sy < 0 else 0), z, z + h, 'wood')
    m.bx(cx - w / 2 + 0.01, cx + w / 2 - 0.01, cy - d / 2 + 0.01, cy + d / 2 - 0.01, z + 0.005, z + 0.025, 'woodL', hull='none')   # floor
    for sy in (-1, 1):                                                         # long sides: slats with gaps
        y0, y1 = sorted((cy + sy * (d / 2 - 0.03), cy + sy * (d / 2 - 0.005)))
        for k in range(3):
            za = z + 0.02 + k * 0.095
            m.bx(cx - w / 2 + 0.04, cx + w / 2 - 0.04, y0, y1, za, za + 0.07, 'woodL')
    for sx in (-1, 1):                                                         # ends: a board with a hand hole
        x0, x1 = sorted((cx + sx * (w / 2 - 0.03), cx + sx * (w / 2 - 0.005)))
        m.bx(x0, x1, cy - d / 2 + 0.04, cy + d / 2 - 0.04, z + 0.02, z + h - 0.01, 'woodL')
        x0, x1 = sorted((cx + sx * (w / 2 - 0.008), cx + sx * (w / 2 + 0.002)))
        m.bx(x0, x1, cy - 0.07, cy + 0.07, z + h - 0.09, z + h - 0.05, 'ink', hull='none')
    for i in range(5):                                                         # fruit
        fx = cx + rnd.uniform(-w / 2 + 0.1, w / 2 - 0.1)
        fy = cy + rnd.uniform(-d / 2 + 0.1, d / 2 - 0.1)
        blob(m, rnd, (fx, fy, z + h - 0.03 + rnd.uniform(0, 0.03)), 0.075, fruit, n=8, squash=(1, 1, 0.9), jag=0.08, hull='none')


def card_box(m, x0, x1, y0, y1, z0, z1, rnd):
    """Cardboard box: body, a seam of tape over the lid with tape tabs down the ends, one top flap lifted."""
    m.bx(x0, x1, y0, y1, z0, z1, 'stoneS')
    cx = (x0 + x1) / 2
    m.bx(cx - 0.035, cx + 0.035, y0 - 0.004, y1 + 0.004, z1 - 0.004, z1 + 0.004, 'stoneB', hull='none')     # tape over the lid
    for y in (y0, y1):
        ya, yb = (y - 0.009, y + 0.003) if y == y0 else (y - 0.003, y + 0.009)
        m.bx(cx - 0.029, cx + 0.029, ya, yb, z1 - 0.1, z1 - 0.003, 'stoneB', hull='none')
    m.bx(cx - 0.002, cx + 0.002, y0 - 0.005, y0 + 0.003, z0 + 0.02, z1 - 0.12, 'stoneB', hull='none')       # flap seam down the front
    # a lifted flap on one side of the lid
    xa = x1 if rnd.random() < 0.5 else x0
    s = 1 if xa == x1 else -1
    hullp(m, [(xa - s * 0.005, y0 + 0.03, z1 + 0.003), (xa - s * 0.005, y1 - 0.03, z1 + 0.003), (xa - s * 0.005, y0 + 0.03, z1 + 0.015),
              (xa - s * 0.005, y1 - 0.03, z1 + 0.015), (xa + s * 0.12, y0 + 0.04, z1 + 0.12), (xa + s * 0.12, y1 - 0.04, z1 + 0.12),
              (xa + s * 0.11, y0 + 0.04, z1 + 0.13), (xa + s * 0.11, y1 - 0.04, z1 + 0.13)], 'stoneS')


def shrub(m, rnd, c, r, cols=('leaf', 'leafD', 'leaf2')):
    """Bush in a planter: three overlapping faceted clumps, lighter on top."""
    def leafc(f):
        return cols[2] if f.normal.z > 0.5 else (cols[1] if f.normal.z < -0.1 else cols[0])
    for i in range(3):
        a = i * 2.1 + rnd.uniform(-0.4, 0.4)
        blob(m, rnd, (c[0] + math.cos(a) * r * 0.45, c[1] + math.sin(a) * r * 0.4, c[2] + rnd.uniform(-0.03, 0.05)),
             r * rnd.uniform(0.6, 0.75), leafc, n=10, squash=(1, 0.9, 0.78))
