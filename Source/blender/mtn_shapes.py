"""kit-mountains organic shapes (map asset upgrade pass): layered conifers built from drooping branch fronds instead of
stacked star cones, ragged far-forest silhouettes, and faceted boulder clusters. Shapes are outlined (ink=True) like
the forms they replace; the caller passes the kit's `hull` and `star` so palette tagging stays in one place."""
import math

from mathutils import Vector


def frond_tree(m, hull, top_z, rnd, x, y, h, r, trunk_h, tiers, trunk_r=0.16, lean=(0.0, 0.0), snow=True, fronds=7,
               cols=('pine2', 'pine', 'pine', 'pine3', 'pine3'), stub=False, flare=True):
    """A conifer: tapered trunk with a root flare, `tiers` whorls of drooping fronds (each its own faceted wedge,
    lengths and droops varied, the whorls twisted against each other), a dark core cone so no daylight shows through,
    snow loaded on the upper side of the fronds and a crooked leader at the top. lean = top offset (m) at full height.
    Returns nothing; every part lands in m as an outlined shape."""
    lx, ly = lean

    def at(z):
        k = z / h
        return x + lx * k, y + ly * k
    # trunk: two tapered sections (the upper one leans with the crown) and a root flare
    tx, ty = at(trunk_h + 1.0)
    pts = []
    for i in range(7):
        a = i / 7 * 2 * math.pi
        pts.append((x + math.cos(a) * trunk_r, y + math.sin(a) * trunk_r, 0.0))
        pts.append((tx + math.cos(a) * trunk_r * 0.62, ty + math.sin(a) * trunk_r * 0.62, trunk_h + 1.0))
    hull(m, pts, 'trunk')
    if flare:
        fp = []
        for i in range(5):
            a = (i + rnd.uniform(-0.2, 0.2)) / 5 * 2 * math.pi + 0.3
            rr = trunk_r * rnd.uniform(1.7, 2.1)
            fp.append((x + math.cos(a) * rr, y + math.sin(a) * rr, 0.0))
            fp.append((x + math.cos(a + 0.3) * trunk_r * 0.9, y + math.sin(a + 0.3) * trunk_r * 0.9, rnd.uniform(0.28, 0.4)))
        fp.append((x, y, 0.45))
        hull(m, fp, 'trunk')
    if stub:      # a dead branch stub below the crown
        a = rnd.uniform(0, 2 * math.pi)
        z = trunk_h * 0.62
        cx, cy = at(z)
        hull(m, [(cx + math.cos(a) * 0.05, cy + math.sin(a) * 0.05, z - 0.04), (cx + math.cos(a) * 0.05, cy + math.sin(a) * 0.05, z + 0.06),
                 (cx - math.cos(a) * 0.04, cy - math.sin(a) * 0.04, z), (cx + math.cos(a) * 0.62, cy + math.sin(a) * 0.62, z + 0.22),
                 (cx + math.cos(a) * 0.6, cy + math.sin(a) * 0.6, z + 0.17)], 'trunk')
    span = h - trunk_h
    tw = rnd.uniform(0, 2 * math.pi)
    for t in range(tiers):
        f = t / tiers
        zb = trunk_h + span * f * 0.8
        rr = r * (1.0 - f * 0.66)
        th = span * (0.5 - f * 0.1) if t < tiers - 1 else (h - zb) * 0.8
        cx, cy = at(zb)
        col = cols[min(t, len(cols) - 1)]
        # core: a plain dark cone the fronds grow from (fills the gaps between them)
        core = [(cx + math.cos(i / 6 * 6.283 + tw) * rr * 0.42, cy + math.sin(i / 6 * 6.283 + tw) * rr * 0.42, zb + th * 0.05) for i in range(6)]
        ax, ay = at(zb + th * 0.95)
        hull(m, core + [(ax, ay, zb + th * 0.95)], 'pine2')
        n = fronds - (1 if t >= tiers - 1 else 0)
        tw += math.pi / n * rnd.uniform(0.8, 1.2)
        for i in range(n):
            a = tw + (i + rnd.uniform(-0.22, 0.22)) / n * 2 * math.pi
            L = rr * rnd.uniform(0.82, 1.08)
            droop = L * rnd.uniform(0.18, 0.32)
            half = math.pi / n * rnd.uniform(0.7, 0.95)
            ca, sa = math.cos(a), math.sin(a)
            z0 = zb + th * 0.42
            # wedge: root at the trunk (two heights), broad shoulders a third out, a drooping tip
            P = [(cx + ca * 0.06, cy + sa * 0.06, z0), (cx + ca * 0.06, cy + sa * 0.06, zb - 0.02),
                 (cx + math.cos(a - half) * L * 0.55, cy + math.sin(a - half) * L * 0.55, zb + th * 0.08),
                 (cx + math.cos(a + half) * L * 0.55, cy + math.sin(a + half) * L * 0.55, zb + th * 0.08),
                 (cx + math.cos(a - half * 0.6) * L * 0.5, cy + math.sin(a - half * 0.6) * L * 0.5, zb + th * 0.2),
                 (cx + math.cos(a + half * 0.6) * L * 0.5, cy + math.sin(a + half * 0.6) * L * 0.5, zb + th * 0.2),
                 (cx + ca * L, cy + sa * L, zb - droop), (cx + ca * L * 0.9, cy + sa * L * 0.9, zb - droop + 0.09)]
            frond = hull(m, P, col)
            if snow and (t >= 1 or rnd.random() < 0.6):
                # snow laid along the frond's back: a flat pad sunk into the wedge, standing 4-6 cm proud of it
                s0, s1 = 0.3, 0.82
                lift = rnd.uniform(0.04, 0.06)
                w = half * 0.45
                spots = [(a, s0, lift), (a, s1, lift * 0.7), (a - w, s0 + 0.12, -0.015), (a + w, s0 + 0.12, -0.015),
                         (a, (s0 + s1) / 2, -0.12)]
                S = []
                for (aa, ss, dz) in spots:
                    px, py = cx + math.cos(aa) * L * ss, cy + math.sin(aa) * L * ss
                    wp = m.parent @ Vector((px, py, 0.0))      # faces are stored in the piece frame
                    zz = top_z(frond, wp.x, wp.y)
                    if zz is None:
                        break
                    S.append((px, py, zz - m.parent.translation.z + dz))
                if len(S) == 5:
                    hull(m, S, 'snow')
    # leader: a slim crooked spike above the last whorl, a snow tuft on it
    zt = zb + th * 0.55          # from inside the last whorl
    bx, by = at(zt)
    tx, ty = at(h)
    tx += rnd.uniform(-0.06, 0.06)
    hull(m, [(bx + math.cos(i * 2.1) * 0.16, by + math.sin(i * 2.1) * 0.16, zt) for i in range(3)] + [(tx, ty, h)], 'pine3')
    if snow:
        hull(m, [(bx + math.cos(i * 2.1 + 1) * 0.13, by + math.sin(i * 2.1 + 1) * 0.13, zt + 0.12) for i in range(3)] +
             [((bx + tx) / 2, (by + ty) / 2, (zt + h) / 2 + 0.05), (bx, by, zt + 0.02)], 'snow')


def ragged_tree(m, star_fn, rnd, x, y, h, under='pine2', mid='pine', top='snow'):
    """A far-forest conifer for the backdrop: three twisted tiers whose tips vary in reach, so the skyline is ragged
    instead of a row of identical cones (one-sided tiers: fan=False, like the old ones)."""
    r = h * rnd.uniform(0.19, 0.25)
    m.cyl((x, y, 0), 0.25, 0.2, 2.2, 'trunk', seg=4, bevel=False)
    zs = [1.0, 1.0 + h * 0.3, 1.0 + h * 0.55]
    for k, (z, rr, th, c) in enumerate(((zs[0], r, h * 0.45, under), (zs[1], r * 0.74, h * 0.4, mid), (zs[2], r * 0.46, h * 0.42, mid))):
        star_fn(m, (x + rnd.uniform(-0.15, 0.15), y, z), rr * rnd.uniform(0.9, 1.1), th, c, pts=rnd.choice((5, 6, 7)),
                inner=rnd.uniform(0.5, 0.62), droop=0.22 * rr, phase=rnd.uniform(0, 60), fan=False)
    star_fn(m, (x, y, zs[2] + h * 0.22), r * 0.24, h * 0.24, top, pts=5, inner=0.7, droop=0.05, phase=rnd.uniform(0, 30), fan=False)


def boulder(m, hull, rock_pts, clamp_pts, rock_col, rnd, h, rx, ry, lim=0.48):
    """A faceted boulder cluster: the main block split by a cleft into two leaning slabs, a chunk broken off at the
    foot, two loose stones and a snow pad on the top facets (rock_col paints the up-facing faces snow)."""
    hull(m, clamp_pts(rock_pts(rnd, (-0.06, 0.03), rx * 0.82, ry * 0.95, h, n=8, top=4, waist=(0.35, 0.6)), lim), rock_col(0, h))
    hull(m, clamp_pts(rock_pts(rnd, (0.17, -0.04), rx * 0.62, ry * 0.8, h * 0.78, n=7, top=3, waist=(0.4, 0.65)), lim), rock_col(0, h * 0.78))
    sx, sy = rnd.choice([(-0.28, -0.3), (0.3, -0.28), (-0.3, 0.28), (0.29, 0.3)])
    hull(m, clamp_pts(rock_pts(rnd, (sx, sy), 0.2, 0.17, h * 0.4, n=6, top=2), lim + 0.01), rock_col(0, h * 0.4))
    for k in range(2):
        a = rnd.uniform(0, 2 * math.pi)
        hull(m, clamp_pts(rock_pts(rnd, (math.cos(a) * 0.36, math.sin(a) * 0.36), 0.08, 0.07, rnd.uniform(0.1, 0.16), n=5, top=1),
                          lim + 0.01), rock_col(0, 0.2))


def tarp_bundle(m, hull, rnd):
    """Supply bundle: a canvas tarp pulled tight over a load (bulged sides, sagging top, uneven corners), two rope
    bands round it and a cross rope over the top, a pad of snow on the top. Same footprint as the old box."""
    def ring(sx, sy, z, j=0.02):
        return [(x * sx + rnd.uniform(-j, j), y * sy + rnd.uniform(-j, j), z + rnd.uniform(-j, j) * 0.5)
                for x, y in ((-1, -1), (0, -1.06), (1, -1), (1.05, 0), (1, 1), (0, 1.06), (-1, 1), (-1.05, 0))]
    body = ring(0.37, 0.31, 0.0, 0) + ring(0.395, 0.335, 0.24) + ring(0.36, 0.3, 0.5) + ring(0.24, 0.18, 0.585, 0.01)
    hull(m, body, 'canvas')

    def band(x, lo=0.0, hi=0.6):
        pts = []
        for xx in (x - 0.03, x + 0.03):
            for (y, z) in ((-0.32, 0.0), (-0.345, 0.24), (-0.31, 0.5), (-0.19, 0.6), (0.19, 0.6), (0.31, 0.5), (0.345, 0.24), (0.32, 0.0)):
                pts.append((xx, y * 1.04, z + (0.012 if z > 0.55 else 0.0)))
        hull(m, pts, 'rope')
    band(-0.21)
    band(0.2)
    # cross rope over the top, and the knot where it is tied off
    hull(m, [(-0.25, -0.025, 0.592), (0.25, -0.025, 0.592), (-0.25, 0.025, 0.592), (0.25, 0.025, 0.592),
             (-0.25, -0.025, 0.624), (0.25, -0.025, 0.624), (-0.25, 0.025, 0.624), (0.25, 0.025, 0.624)], 'rope')
    hull(m, [(0.2 + math.cos(a) * 0.05, math.sin(a) * 0.05 - 0.36, 0.3 + math.sin(a * 2) * 0.04) for a in [i * 1.05 for i in range(6)]] +
         [(0.2, -0.32, 0.3)], 'rope')
    # snow pad on the top, lying between the rope bands
    hull(m, [(-0.13, -0.15, 0.585), (0.12, -0.16, 0.585), (0.13, 0.15, 0.585), (-0.12, 0.14, 0.585),
             (-0.08, -0.08, 0.63), (0.07, 0.06, 0.635), (0.0, 0.1, 0.62)], 'snow')


def logpile_detail(m, r):
    """Bark strips along the three logs (ink-free detail)."""
    from mtn_detail import det
    k = det(m)
    for (y, z, a0) in ((-0.26, r, 30), (0.26, r, 160), (0.0, r + 0.44, 100)):
        for j, (x0, x1, da) in enumerate(((-0.42, -0.05, 0), (0.08, 0.38, 72), (-0.2, 0.18, 216))):
            a = math.radians(a0 + da)
            rr = r * math.cos(math.radians(22.5)) + 0.004
            k.bxr((x0 + x1) / 2, y + math.cos(a) * rr, z + math.sin(a) * rr, x1 - x0, 0.05, 0.022, 'log2',
                  rot=(math.degrees(a) - 90, 0, 0), ink=False)


def stone_courses(m, hull, rnd, fy, yface, x0, x1, courses, cols=('stone', 'rock3', 'stone2', 'stone')):
    """Dry-stone facing on the plane y = fy * yface: per course, stones of random length with a 1-2 cm joint, each a
    chamfered block (front face smaller than its bed) standing 2-5 cm proud and sunk 3 cm into the core."""
    for ci, (z0, z1) in enumerate(courses):
        x = x0 + rnd.uniform(0.0, 0.12) * (ci % 2)
        while x < x1 - 0.1:
            w = min(rnd.uniform(0.18, 0.36), x1 - x)
            if x1 - (x + w) < 0.1:
                w = x1 - x
            j = 0.012 + rnd.uniform(0, 0.008)
            a, b = x + j / 2, x + w - j / 2
            za, zb = z0 + j / 2 + rnd.uniform(0, 0.015), z1 - j / 2 - rnd.uniform(0, 0.015)
            d = rnd.uniform(0.02, 0.05)
            c = min(0.03, (b - a) * 0.2, (zb - za) * 0.2)
            yb, yf = fy * (yface - 0.03), fy * (yface + d)
            ym = fy * (yface + d * 0.6)
            P = [(a, yb, za), (b, yb, za), (a, yb, zb), (b, yb, zb),
                 (a, ym, za), (b, ym, za), (a, ym, zb), (b, ym, zb),
                 (a + c, yf, za + c), (b - c, yf, za + c * rnd.uniform(0.6, 1.4)), (a + c, yf, zb - c), (b - c * rnd.uniform(0.6, 1.4), yf, zb - c)]
            hull(m, P, rnd.choice(cols))
            x += w
