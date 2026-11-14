"""kit-townhomes houses: 6 x 12 m town-house lots (front = -Y, the street), built as whole pieces.

Lot frame (Blender): x -3 .. 3 along the street, y -6 (porch edge) .. 6 (back wall). The front wall stands at FW = -4.5,
the porch / stoop strip in front of it; a step reaches 0.5 m past the lot edge into the front yard on the walk-in houses.
Styles (each its own silhouette, materials and roof line; the theme repaints siding / stucco / brick / doors / shutters
per house, so a row never shows one colour twice in a row):
  Siding   two storeys of lap siding, a gable roof along the street with a dormer, a covered porch
  Stucco   two storeys of stucco under a clay-tile front gable (ridge to the street), arched door and windows
  Brick    three storeys of brick, a flat roof behind a bracketed cornice, a two-storey bay and an iron-railed stoop
  Garage   modern three-storey: brick base with a front garage, board siding above, a cantilevered box bay
Walk-in houses (Walk_Siding / Walk_Stucco / Walk_Brick): open front and back doors, a ground floor (0.32 m up) with the
living room at the front and the kitchen at the back (furniture: Int_* pieces), a straight stair along the left party
wall up to the upper floor (3.32 m): an open front room with French doors onto the balcony over the porch (the sniper
perch), a back bedroom behind a partition. Every rise is 0.16 / 0.3 m on 0.5 m treads, doorways 1.3 m, so robots follow
the player up (zones.js layered nav).
"""
import math

from townhomes_base import *  # noqa: F401,F403
import townhomes_detail as TD

EMB = TD.EMB

SIDING_STEP = 0.3


# ---------------------------------------------------------------- facade frame helpers
# A facade is painted in a local frame: the wall plane at y = 0 facing -Y, x along the wall, z up; m.parent puts it on
# the house (front, back or a side).
def frame_front():
    return Matrix.Translation((0, FW, 0))


def frame_back():
    return Matrix.Translation((0, BW, 0)) @ Matrix.Rotation(math.pi, 4, 'Z')


def frame_side(sx):
    """side wall at x = sx * HW, facing out; local x runs along +Y for sx > 0, -Y for sx < 0"""
    return Matrix.Translation((sx * HW, 0, 0)) @ Matrix.Rotation(sx * math.pi / 2, 4, 'Z')


def fz(m, x0, x1, z0, z1, d, c):
    """painted quad d proud of the facade plane"""
    fq(m, x0, x1, -d, z0, z1, c)


def fbox(m, x0, x1, z0, z1, d0, d1, c, hull='none', cull='k'):
    """box standing out of the facade from d0 to d1"""
    m.bx(x0, x1, -d1, -d0, z0, z1, c, hull=hull, cull=cull)


def clip_rects(x0, x1, z0, z1, holes):
    """the wall rect minus rectangular holes [(x0, x1, z0, z1)] -> list of rects (vertical bands then rows)"""
    xs = sorted({x0, x1} | {h[0] for h in holes if x0 < h[0] < x1} | {h[1] for h in holes if x0 < h[1] < x1})
    out = []
    for a, b in zip(xs, xs[1:]):
        zs = [(z0, z1)]
        for h in holes:
            if h[0] < b - 1e-6 and h[1] > a + 1e-6:
                nz = []
                for (p, q) in zs:
                    if h[3] <= p or h[2] >= q:
                        nz.append((p, q))
                        continue
                    if h[2] > p:
                        nz.append((p, h[2]))
                    if h[3] < q:
                        nz.append((h[3], q))
                zs = nz
        out += [(a, b, p, q) for (p, q) in zs if q - p > 1e-4]
    return out


def lines_h(m, rects, z0, z1, step, c, d=0.004, w=0.025):
    """horizontal pattern lines (lap siding shadows, brick courses) across the wall rects only"""
    z = z0 + step
    while z < z1 - 0.05:
        for (a, b, p, q) in rects:
            if p <= z - w and z <= q:
                fz(m, a, b, z - w, z, d, c)
        z += step


def lines_v(m, rects, x0, x1, step, c, d=0.004, w=0.022):
    x = x0 + step
    while x < x1 - 0.05:
        for (a, b, p, q) in rects:
            if a <= x - w / 2 and x + w / 2 <= b:
                fz(m, x - w / 2, x + w / 2, p, q, d, c)
        x += step


def window(m, x0, x1, z0, z1, trim='trim', shutters=False, sill=True, grille=True, arch=False, glint=True, box=None):
    """double-hung window: casing, glass, meeting rail, grille, sill, shutters, a glint; arch: a fanlight on top"""
    fz(m, x0 - 0.09, x1 + 0.09, z0 - 0.06, z1 + 0.09, 0.012, trim)
    fz(m, x0, x1, z0, z1, 0.02, 'glass')
    zm = (z0 + z1) / 2
    fz(m, x0, x1, zm - 0.03, zm + 0.03, 0.026, trim)
    if grille:
        xm = (x0 + x1) / 2
        fz(m, xm - 0.018, xm + 0.018, z0, z1, 0.03, trim)
    if glint:
        poly(m, [(x0 + 0.06, -0.034, zm + 0.08), (x0 + 0.14, -0.034, zm + 0.08), (x0 + 0.3, -0.034, z1 - 0.08), (x0 + 0.22, -0.034, z1 - 0.08)], 'glassL', (0, -1, 0))
    if arch:   # semicircular fanlight over the sash
        r = (x1 - x0) / 2 + 0.09
        xc = (x0 + x1) / 2
        n = 7
        pts = [(xc + math.cos(math.pi * i / n) * r, -0.012, z1 + 0.09 + math.sin(math.pi * i / n) * r) for i in range(n + 1)]
        poly(m, pts, trim, (0, -1, 0))
        r2 = r - 0.09
        pts = [(xc + math.cos(math.pi * i / n) * r2, -0.02, z1 + 0.09 + math.sin(math.pi * i / n) * r2) for i in range(n + 1)]
        poly(m, pts, 'glass', (0, -1, 0))
    if sill:
        fbox(m, x0 - 0.13, x1 + 0.13, z0 - 0.12, z0 - 0.05, 0.0, 0.07, trim, cull='kb')
    if box:   # a window box of flowers under the sill
        fbox(m, x0 - 0.05, x1 + 0.05, z0 - 0.38, z0 - 0.14, 0.0, 0.22, box, cull='kb')
        m.sp(((x0 + x1) / 2, -0.12, z0 - 0.1), (x1 - x0) / 2, 'leaf', seg=(7, 3), scale=(1, 0.22, 0.25), hull='none')
        for i in range(4):
            x = x0 + (i + 0.5) * (x1 - x0) / 4
            m.sp((x, -0.2, z0 - 0.05), 0.07, ('flower', 'trim', 'doorY', 'flower')[i], seg=(5, 3), hull='none')
    if shutters:
        w = (x1 - x0) * 0.45
        for (a, b) in ((x0 - 0.12 - w, x0 - 0.12), (x1 + 0.12, x1 + 0.12 + w)):
            fz(m, a, b, z0 - 0.02, z1 + 0.04, 0.016, 'shut')
            zz = (z0 + z1) / 2
            fz(m, a + 0.04, b - 0.04, zz - 0.015, zz + 0.015, 0.02, 'iron')
    TD.window_detail(m, x0, x1, z0, z1, shutters=shutters, sill=sill, arch=arch, flowerbox=bool(box))


def door(m, x0, x1, z0, z1, open_=False, trim='trim', transom=True, arch=False, panels=True):
    """front door: casing, transom light; closed: a panelled leaf with a knob; open: the dark doorway is left as a
    hole in the wall and the leaf stands swung in (drawn by the caller inside)"""
    TD.door_detail(m, x0, x1, z0, z1, open_=open_, arch=arch, transom=transom)
    fz(m, x0 - 0.12, x0, z0, z1 + (0.12 if not arch else 0.0), 0.014, trim)
    fz(m, x1, x1 + 0.12, z0, z1 + (0.12 if not arch else 0.0), 0.014, trim)
    if not arch:
        fz(m, x0 - 0.16, x1 + 0.16, z1, z1 + 0.16, 0.018, trim)
    if open_:
        return
    zt = z1 - (0.4 if transom else 0.0)
    fz(m, x0, x1, z0, zt, 0.01, 'door')
    if transom:
        fz(m, x0, x1, zt + 0.04, z1, 0.01, 'glass')
        fz(m, x0, x1, zt, zt + 0.04, 0.014, trim)
    if panels:
        for (p, q) in ((z0 + 0.15, z0 + 0.85), (z0 + 1.05, zt - 0.15)):
            for (a, b) in ((x0 + 0.1, (x0 + x1) / 2 - 0.05), ((x0 + x1) / 2 + 0.05, x1 - 0.1)):
                fz(m, a, b, p, q, 0.014, 'doorK')
                fz(m, a + 0.03, b - 0.03, p + 0.03, q - 0.03, 0.018, 'door')
    m.sp((x1 - 0.12, -0.04, z0 + 1.0), 0.035, 'lineY', seg=(5, 3), hull='none')


def carriage_lamp(m, x, z):
    fbox(m, x - 0.05, x + 0.05, z - 0.15, z + 0.15, 0.0, 0.04, 'iron')
    fbox(m, x - 0.09, x + 0.09, z - 0.12, z + 0.16, 0.04, 0.22, 'iron', cull='')
    fz(m, x - 0.06, x + 0.06, z - 0.09, z + 0.12, 0.224, 'glassL')
    fbox(m, x - 0.11, x + 0.11, z + 0.16, z + 0.2, 0.03, 0.24, 'iron', cull='')
    TD.lamp_detail(m, x, z)


def house_number(m, x, z, n):
    fz(m, x - 0.16, x + 0.16, z - 0.09, z + 0.09, 0.014, 'trim')
    txt(m, str(n), x, -0.018, z, 0.11, 'iron', font='serif', maxw=0.28)


# ---------------------------------------------------------------- wall masses
def walls(m, cols, x0, x1, y0, y1, z0, z1, c, holes_front=(), holes_back=(), inner=None, solid=True):
    """the house shell. Side walls run the full depth with an outline shell (they carry the corners); the front and
    back walls stand between them as boxes round their openings (no shell: no ink seams across the facade).
    holes: [(x0, x1, z0, z1)] in piece x. inner: a walk-in house (the boxes drop their inside faces, painted quads
    take their place, and collision follows the openings); otherwise one solid box fills the house."""
    ci = x0 + WT, x1 - WT
    for (a, b, p, q) in clip_rects(ci[0], ci[1], z0, z1, list(holes_front)):
        m.bx(a, b, y0, y0 + WT, p, q, c, hull='none', cull=('k' if inner else '') + ('b' if p < 0.01 else ''))
        if inner:
            cols.append(box(a, y0, p, b, y0 + WT, q))
    for (a, b, p, q) in clip_rects(ci[0], ci[1], z0, z1, list(holes_back)):
        m.bx(a, b, y1 - WT, y1, p, q, c, hull='none', cull=('f' if inner else '') + ('b' if p < 0.01 else ''))
        if inner:
            cols.append(box(a, y1 - WT, p, b, y1, q))
    for sx in (-1, 1):
        a, b = (x0, x0 + WT) if sx < 0 else (x1 - WT, x1)
        m.bx(a, b, y0, y1, z0, z1, c, hull='full', cull=(('r' if sx < 0 else 'l') if inner else '') + ('b' if z0 < 0.01 else ''))
        if inner:
            cols.append(box(a, y0, z0, b, y1, z1))
    if not inner and solid:
        cols.append(box(x0, y0, z0, x1, y1, z1))


def roof_gable_x(m, y0, y1, eave, pitch, x0=-HW, x1=HW, over=0.35, c='shingle', body='sid', thick=0.16):
    """gable roof with its ridge along X: the attic mass (gable triangles in the body colour) and the roof slab with
    eave overhangs front and back, a ridge cap; returns the ridge height"""
    yr = (y0 + y1) / 2
    rise = (y1 - y0) / 2 * math.tan(math.radians(pitch))
    R = eave + rise
    m.prism([(y0, eave), (y1, eave), (yr, R - 0.02)], -HW + 0.01, HW - 0.01, [body], hull='full', skip=(0,))
    k = math.tan(math.radians(pitch))
    ya, yb = y0 - over, y1 + over
    za, zb = eave - over * k, eave - over * k
    t = thick / math.cos(math.radians(pitch))
    prof = [(ya, za), (yr, R), (yb, zb), (yb, zb + t), (yr, R + t), (ya, za + t)]
    m.prism(prof, x0, x1, [c], hull='full')
    m.prism([(yr - 0.14, R + t - 0.03), (yr + 0.14, R + t - 0.03), (yr + 0.1, R + t + 0.07), (yr - 0.1, R + t + 0.07)], x0 + 0.01, x1 - 0.01, ['shingleD'], hull='full')
    # fascia boards along the eaves
    for (yy, s) in ((ya, -1), (yb, 1)):
        a, b = srt(yy, yy + s * 0.04)
        m.bx(x0, x1, a, b, za - 0.12, za + t * 0.6, 'trim', hull='none', cull='')
        TD.gutter_run(m, x0, x1, yy, za, s)
    return R, k, t


def roof_gable_y(m, y0, y1, eave, pitch, over=0.45, c='tileR', body='stu', thick=0.16):
    """front gable: ridge along Y at x = 0, the gable triangle facing the street; clay tile slab with tile rows"""
    rise = HW * math.tan(math.radians(pitch))
    R = eave + rise
    rot = Matrix.Rotation(math.pi / 2, 4, 'Z')
    # prism along X of profile (y, z) turned to run along Y: local (x, y) -> (-y, x); profile y -> -x
    m.prism([(-HW, eave), (HW, eave), (0.0, R - 0.02)], y0, y1, [body], hull='full', mat=rot, skip=(0,))
    k = math.tan(math.radians(pitch))
    t = thick / math.cos(math.radians(pitch))
    xa = HW + 0.08
    za = eave - 0.08 * k
    prof = [(-xa, za), (0.0, R), (xa, za), (xa, za + t), (0.0, R + t), (-xa, za + t)]
    m.prism(prof, y0 - over, y1 + 0.06, [c], hull='full', mat=rot)
    m.prism([(-0.14, R + t - 0.03), (0.14, R + t - 0.03), (0.1, R + t + 0.08), (-0.1, R + t + 0.08)], y0 - over - 0.02, y1 + 0.08, ['tileR'], hull='full', mat=rot)
    # tile rows: painted strips along the ridge direction on both slopes
    th = math.atan(k)
    for sx in (-1, 1):
        for i in range(1, 6):
            pts = []
            for (u, yy) in ((i / 6.0, y0 - over), (i / 6.0 + 0.025, y0 - over), (i / 6.0 + 0.025, y1 + 0.06), (i / 6.0, y1 + 0.06)):
                pts.append((sx * xa * u, yy, R + t + 0.006 - (R - za) * u))
            poly(m, pts, 'stuC', (sx * math.sin(th), 0, math.cos(th)))
    return R, k, t


def cornice(m, x0, x1, z, d=0.32, c='trim', brackets=6):
    """flat-roof cornice on the facade frame: a projecting crown over a frieze with brackets"""
    fbox(m, x0, x1, z, z + 0.14, 0.0, d, c, hull='full', cull='k')
    fbox(m, x0, x1, z + 0.14, z + 0.22, 0.0, d + 0.06, c, hull='full', cull='k')
    fz(m, x0, x1, z - 0.42, z, 0.01, 'trimD')
    for i in range(brackets):
        x = x0 + 0.2 + i * (x1 - x0 - 0.4) / max(1, brackets - 1)
        fbox(m, x - 0.06, x + 0.06, z - 0.36, z, 0.006, d - 0.04, c, cull='kt')


def chimney(m, x, y, z0, z1, c='brk'):
    m.bx(x - 0.32, x + 0.32, y - 0.3, y + 0.3, z0, z1, c)
    m.bx(x - 0.38, x + 0.38, y - 0.36, y + 0.36, z1, z1 + 0.12, 'stoneD')
    for dx in (-0.14, 0.14):
        m.cy((x + dx, y, z1 + 0.12), 0.08, 0.08, 0.22, 'tileR', seg=6)


# ---------------------------------------------------------------- porches and stoops (piece frame)
def porch_balcony(m, cols, body):
    """walk-in houses: a 1 m porch at the floor level behind a full-width step, two columns carrying the balcony
    (the upper floor's sniper perch) with a turned-baluster rail"""
    m.bx(-HW + 0.05, HW - 0.05, -5.5, FW, 0.0, GF, 'stone', cull='b')
    uq(m, -HW + 0.05, HW - 0.05, -5.5, FW, GF + 0.004, 'woodD')
    m.bx(-HW + 0.05, HW - 0.05, -6.0, -5.5, 0.0, GF / 2, 'stone', cull='b')
    cols += [wbox(-HW + 0.05, -5.5, 0, HW - 0.05, FW, GF), wbox(-HW + 0.05, -6.0, 0, HW - 0.05, -5.5, GF / 2)]
    TD.nosing(m, -HW + 0.05, HW - 0.05, -5.5, GF)
    TD.nosing(m, -HW + 0.05, HW - 0.05, -6.0, GF / 2)
    for sx in (-1, 1):
        x = sx * 2.72
        m.bx(x - 0.13, x + 0.13, -5.95, -5.69, GF / 2, GF / 2 + 0.25, 'trim')
        post(m, x, -5.82, GF / 2 + 0.25, UF - SLAB - 0.2, 0.1, 'trim', seg=8)
        m.bx(x - 0.13, x + 0.13, -5.95, -5.69, UF - SLAB - 0.2, UF - SLAB, 'trim')
        m.cy((x, -5.82, GF / 2 + 0.25 - EMB), 0.125, 0.125, 0.045, 'trim', seg=8, hull='none')
        m.cy((x, -5.82, UF - SLAB - 0.2 - 0.042), 0.125, 0.125, 0.045, 'trim', seg=8, hull='none')
        cols.append(box(x - 0.13, -5.95, GF / 2, x + 0.13, -5.69, UF - SLAB))
    # the balcony slab (porch ceiling under it), fascia, rail
    m.bx(-HW + 0.04, HW - 0.04, -6.05, FW, UF - SLAB, UF, 'trim')
    uq(m, -HW + 0.06, HW - 0.06, -6.0, FW, UF + 0.004, 'wood')
    dq(m, -HW + 0.1, HW - 0.1, -5.98, FW - 0.02, UF - SLAB - 0.004, 'trimD')
    cols.append(wbox(-HW + 0.04, -6.05, UF - SLAB, HW - 0.04, FW, UF))
    z0, z1 = UF, UF + 1.0
    m.bx(-HW + 0.04, HW - 0.04, -6.05, -5.95, z1 - 0.07, z1, 'trim')
    m.bx(-HW + 0.04, HW - 0.04, -6.05, -5.95, z0, z0 + 0.08, 'trim', cull='b')
    pickets_x(m, -HW + 0.12, HW - 0.12, -6.0, z0 + 0.08, z1 - 0.07, 0.2, 0.05, 'trim')
    cols.append(box(-HW + 0.04, -6.05, z0, HW - 0.04, -5.95, z1))
    TD.rail_cap(m, -HW + 0.04, HW - 0.04, -6.0, z1)
    for sx in (-1, 1):
        a, b = srt(sx * (HW - 0.04), sx * (HW - 0.14))
        m.bx(a, b, -5.95, FW, z1 - 0.07, z1, 'trim')
        m.bx(a, b, -5.95, FW, z0, z0 + 0.08, 'trim', cull='b')
        pickets_y(m, -5.85, FW - 0.08, (a + b) / 2, z0 + 0.08, z1 - 0.07, 0.2, 0.05, 'trim')
        cols.append(box(a, -5.95, z0, b, FW, z1))
    # planters on the balcony corners and porch
    for x in (-2.45, 2.45):
        m.bx(x - 0.18, x + 0.18, -5.85, -5.5, UF, UF + 0.32, 'tileR')
        shrub(m, x, -5.67, 0.24, z=UF + 0.3)
        cols.append(box(x - 0.18, -5.85, UF, x + 0.18, -5.5, UF + 0.6))
    m.bx(1.95, 2.45, -5.4, -4.9, GF, GF + 0.42, 'stoneD')
    shrub(m, 2.2, -5.15, 0.3, z=GF + 0.4)
    cols.append(box(1.95, -5.4, GF, 2.45, -4.9, GF + 0.42))


def stoop_iron(m, cols):
    """brick houses: a two-step stone stoop up to the door with iron railings"""
    x0, x1 = DOOR[0] - 0.2, DOOR[1] + 0.2
    m.bx(x0, x1, -5.4, FW, 0.0, GF, 'stone', cull='b')
    m.bx(x0, x1, -5.95, -5.4, 0.0, GF / 2, 'stone', cull='b')
    cols += [wbox(x0, -5.4, 0, x1, FW, GF), wbox(x0, -5.95, 0, x1, -5.4, GF / 2)]
    TD.nosing(m, x0, x1, -5.4, GF)
    TD.nosing(m, x0, x1, -5.95, GF / 2)
    for x in (x0 + 0.04, x1 - 0.04):
        m.bm_((x, -5.9, 0.95), (x, -5.4, GF + 0.95), 0.045, 'iron')
        m.bm_((x, -5.38, GF + 0.95), (x, FW, GF + 0.95), 0.036, 'iron')
        for y in (-5.85, -5.55, -5.25, -4.95, -4.65):
            zb = GF / 2 if y < -5.4 else GF
            m.bx(x - 0.016, x + 0.016, y - 0.016, y + 0.016, zb, GF + 0.92 + (0 if y > -5.4 else -0.2), 'iron', hull='none', cull='tb')
        m.cy((x, -5.9, 0.0), 0.05, 0.05, 1.05, 'iron', seg=6)
        cols.append(box(x - 0.05, -5.95, 0, x + 0.05, FW, GF + 0.98))


def porch_bench(m, cols, x0, x1, yb, z):
    """a slatted bench against the front wall (back toward +Y)"""
    for x in (x0 + 0.05, x1 - 0.05):
        m.bx(x - 0.04, x + 0.04, yb - 0.45, yb, z, z + 0.62, 'woodD', hull='full', cull='b')
    for k in range(3):
        m.bx(x0, x1, yb - 0.44 + k * 0.14, yb - 0.32 + k * 0.14, z + 0.4, z + 0.45, 'woodL', hull='none')
    m.bx(x0, x1, yb - 0.08, yb - 0.02, z + 0.5, z + 0.85, 'woodL', hull='full')
    cols.append(box(x0, yb - 0.45, z, x1, yb, z + 0.85))


def door_hood(m, x0, x1, z, c='trim', roofc='shingle'):
    """a little pediment hood on brackets over a door (facade frame)"""
    a = max(x0 - 0.3, -HW + 0.06)
    fbox(m, a, x1 + 0.3, z, z + 0.08, 0.0, 0.6, c, hull='full', cull='k')
    m.prism([(-0.62, z + 0.08), (0.0, z + 0.08), (0.0, z + 0.3)], a - 0.02, x1 + 0.32, [roofc], hull='full', skip=(1,))
    for x in (a + 0.1, x1 + 0.18):
        fbox(m, x - 0.04, x + 0.04, z - 0.35, z, 0.0, 0.45, c, cull='k')


# ---------------------------------------------------------------- the inside of a walk-in house (shell part)
def interior_shell(m, cols, inner='plaster', floor='wood', ceil='plaster'):
    """floors, ceilings, the stair, the stairwell balustrades and the upper partition; collision for all of it"""
    sx0, sx1, sy0, sy1 = STAIR
    # ground floor slab (walkable) and its boards
    uq(m, -IX, IX, IY0, IY1, GF, floor)
    for k in range(1, 12):
        x = -IX + k * (2 * IX) / 12
        uq(m, x - 0.008, x + 0.008, IY0, IY1, GF + 0.004, 'woodD')
    cols.append(wbox(-IX, IY0, 0.0, IX, IY1, GF))
    for (y0, y1) in ((FW, IY0), (IY1, BW)):      # door thresholds through the wall
        m.bx(DOOR[0], DOOR[1], y0, y1, 0.0, GF, 'stone', hull='none', cull='b' + ('f' if y0 == FW else 'k'))
        cols.append(wbox(DOOR[0], y0, 0.0, DOOR[1], y1, GF))
    # upper slab round the stairwell: undersides (ground floor ceiling), tops, the well's edges
    U0 = UF - SLAB
    slabs = [(sx1, IX, IY0, IY1), (-IX, sx1, IY0, sy0), (-IX, sx1, sy1, IY1)]
    for (a, b, c0, c1) in slabs:
        m.bx(a, b, c0, c1, U0, UF, 'trimD', hull='none', cull='tb')
        uq(m, a, b, c0, c1, UF, floor)
        dq(m, a, b, c0, c1, U0, ceil)
        cols.append(wbox(a, c0, U0, b, c1, UF))
    for k in range(1, 9):
        x = sx1 + k * (IX - sx1) / 9
        uq(m, x - 0.008, x + 0.008, IY0, IY1, UF + 0.004, 'woodD')
    # stair: ten risers of 0.3 on 0.5 treads, walkable boxes solid to the floor
    n = 10
    run = (sy1 - sy0) / n
    for k in range(n):
        a = sy0 + k * run
        top = GF + (k + 1) * 0.3
        m.bx(sx0, sx1, a, a + run, top - 0.3 if k else 0.0, top, 'trim', cull='b' if k == 0 else 'b')
        uq(m, sx0, sx1, a, a + run, top + 0.004, 'wood')
        cols.append(wbox(sx0, a, 0.0, sx1, a + run, top))
    # the closet under the stair (its side panel), so the steps read as a solid flight
    for k in range(1, n):
        a = sy0 + k * run
        rq(m, sx1 + 0.002, a, a + run, GF, GF + k * 0.3, 'trimD')
    # balustrade up the flight (stepped collision under the slanted rail)
    hr0, hr1 = GF + 0.92, UF + 0.92
    xr = sx1 - 0.06
    m.bm_((xr, sy0 + 0.05, hr0 + 0.3), (xr, sy1, hr1), 0.07, 'woodD')
    m.cy((xr, sy0 + 0.08, GF + 0.3), 0.06, 0.06, 1.0, 'woodD', seg=6)
    for k in range(n):
        y = sy0 + 0.25 + k * run
        tread = GF + (int((y - sy0) / run) + 1) * 0.3
        rail = hr0 + 0.3 + (hr1 - hr0 - 0.3) * (y - sy0 - 0.05) / (sy1 - sy0 - 0.05)
        if rail - tread > 0.1:
            m.bx(xr - 0.018, xr + 0.018, y - 0.018, y + 0.018, tread, rail - 0.03, 'trim', hull='none', cull='tb')
    for k in range(5):
        y0 = sy0 + k * (sy1 - sy0) / 5
        y1 = y0 + (sy1 - sy0) / 5
        rail = hr0 + 0.3 + (hr1 - hr0 - 0.3) * (y1 - sy0) / (sy1 - sy0)
        cols.append(box(xr - 0.05, y0, GF, xr + 0.05, y1, rail + 0.04))
    # upper balustrades round the well (along x = sx1 and across its front end)
    z0, z1 = UF, UF + 1.0
    xu = sx1 + 0.05
    m.bx(xu - 0.04, xu + 0.04, sy0 - 0.14, sy1, z1 - 0.06, z1, 'woodD')
    pickets_y(m, sy0, sy1 - 0.05, xu, z0, z1 - 0.06, 0.4, 0.04, 'trim')
    m.bx(sx0, xu - 0.04, sy0 - 0.14, sy0 - 0.06, z1 - 0.06, z1, 'woodD')
    pickets_x(m, sx0 + 0.05, xu - 0.05, sy0 - 0.1, z0, z1 - 0.06, 0.25, 0.036, 'trim')
    cols += [box(xu - 0.05, sy0 - 0.14, z0, xu + 0.05, sy1, z1), box(sx0, sy0 - 0.15, z0, xu - 0.04, sy0 - 0.05, z1)]
    # upper partition with the back bedroom door (behind the landing)
    for (a, b) in ((-IX, DOOR[0]), (DOOR[1], IX)):
        m.bx(a, b, PART_Y, PART_Y + 0.14, UF, UC, 'plaster', hull='none', cull='tb')
        cols.append(box(a, PART_Y, UF, b, PART_Y + 0.14, UC))
    m.bx(DOOR[0], DOOR[1], PART_Y, PART_Y + 0.14, UF + DOOR_H - 0.3, UC, 'plaster', hull='none', cull='t')
    for (a, b, p, q) in ((DOOR[0] - 0.08, DOOR[0], UF, UF + DOOR_H - 0.3), (DOOR[1], DOOR[1] + 0.08, UF, UF + DOOR_H - 0.3), (DOOR[0] - 0.08, DOOR[1] + 0.08, UF + DOOR_H - 0.3, UF + DOOR_H - 0.22)):
        fq(m, a, b, PART_Y - 0.004, p, q, 'trim')
        bq(m, a, b, PART_Y + 0.144, p, q, 'trim')
    # upper ceiling
    dq(m, -IX, IX, IY0, IY1, UC, ceil)
    # the inside faces of the shell: plaster on both storeys, skirting
    for (z0_, z1_) in ((GF, U0), (UF, UC)):
        rq(m, -IX, IY0, IY1, z0_, z1_, inner)
        lq(m, IX, IY0, IY1, z0_, z1_, inner)
        m.bx(-IX, -IX + 0.02, IY0, IY1, z0_, z0_ + 0.1, 'trim', hull='none', cull='lbfk')
        m.bx(IX - 0.02, IX, IY0, IY1, z0_, z0_ + 0.1, 'trim', hull='none', cull='rbfk')


def inner_front_back(m, holes_front, holes_back, inner='plaster'):
    """plaster on the inside of the front and back walls round their openings (both storeys)"""
    for (a, b, p, q) in clip_rects(-IX, IX, GF, UC, list(holes_front) + [(-IX, IX, UF - SLAB, UF)]):
        bq(m, a, b, IY0, p, q, inner)
    for (a, b, p, q) in clip_rects(-IX, IX, GF, UC, list(holes_back) + [(-IX, IX, UF - SLAB, UF)]):
        fq(m, a, b, IY1, p, q, inner)


def inside_window(m, x0, x1, z0, z1, y, face):
    """a window seen from inside (face +1: on the front wall looking in +Y; -1 on the back wall)"""
    f = bq if face > 0 else fq
    s = face
    f(m, x0 - 0.08, x1 + 0.08, y + s * 0.006, z0 - 0.06, z1 + 0.08, 'trim')
    f(m, x0, x1, y + s * 0.012, z0, z1, 'glass')
    f(m, x0, x1, y + s * 0.016, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03, 'trim')
    a, b = srt(y, y + s * 0.18)
    m.bx(x0 - 0.12, x1 + 0.12, a, b, z0 - 0.08, z0 - 0.02, 'trim', hull='none', cull='b' + ('f' if face > 0 else 'k'))


def open_leaf(m, x_hinge, y_wall, z0, h, w, face, swing=1):
    """an open door leaf standing swung 90 degrees into the room at its hinge (face +1: front wall, opens toward +Y)"""
    a, b = srt(x_hinge, x_hinge + swing * 0.05)
    c0, c1 = srt(y_wall + face * 0.02, y_wall + face * (0.02 + w))
    m.bx(a, b, c0, c1, z0, z0 + h, 'door', hull='full')
    return box(a, c0, z0, b, c1, z0 + h)


# ---------------------------------------------------------------- styles
def siding_face(m, rects, eave, z0=GF):
    lines_h(m, rects, z0, eave, SIDING_STEP, 'trimD', d=0.004, w=0.03)


def brick_face(m, rects, top, z0=GF, d=0.004):
    lines_h(m, rects, z0, top, 0.3, 'mortar', d=d, w=0.02)


def foundation(m, x0, x1, h=GF, c='stone'):
    fz(m, x0, x1, 0.0, h, 0.006, c)
    fz(m, x0, x1, h, h + 0.05, 0.006, 'stoneD')


def house_siding(pal, name, walk, ao, num=12):
    m = new(pal)
    cols = []
    eave = EAVE2
    hf = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H), (FRENCH[0], FRENCH[1], UF, UF + FR_H)] if walk else []
    hb = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H)] if walk else []
    walls(m, cols, -HW, HW, FW, BW, 0.0, eave, 'sid', hf, hb, inner='plaster' if walk else None)
    R, k, t = roof_gable_x(m, FW, BW, eave, 28, body='sid')
    # front facade
    m.parent = frame_front()
    rects = clip_rects(-HW, HW, GF, eave, hf)
    siding_face(m, rects, eave)
    foundation(m, -HW, HW)
    fz(m, -HW, -HW + 0.14, GF, eave, 0.01, 'trim')
    fz(m, HW - 0.14, HW, GF, eave, 0.01, 'trim')
    TD.siding_trim(m, -HW, HW, eave, GF, UF, [(DOOR[0] - 0.17, DOOR[1] + 0.17)])
    if walk:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H, open_=True)
        window(m, -0.3, 2.3, 1.15, 2.55, shutters=False, grille=True)
        door(m, FRENCH[0], FRENCH[1], UF, UF + FR_H, open_=True, transom=False)
        window(m, -2.4, -1.6, UF + 0.55, UF + 2.0, shutters=True)
        window(m, 1.6, 2.4, UF + 0.55, UF + 2.0, shutters=True)
        house_number(m, -2.1, GF + DOOR_H + 0.38, num)
        carriage_lamp(m, -1.15, GF + 1.75)
    else:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H)
        window(m, -0.45, 0.35, 1.0, 2.6, shutters=True)
        window(m, 1.45, 2.25, 1.0, 2.6, shutters=True)
        for x in (-1.95, 0.0, 1.95):
            window(m, x - 0.4, x + 0.4, UF + 0.5, UF + 2.0, shutters=True)
        house_number(m, -2.1, GF + DOOR_H + 0.38, num)
        carriage_lamp(m, -1.15, GF + 1.75)
    m.parent = Matrix.Identity(4)
    # dormer on the front slope
    yd0 = FW + 1.0
    zb = eave + (yd0 - FW) * k + t * 0.5
    m.bx(-0.75, 0.75, yd0, yd0 + 1.6, zb - 0.6, zb + 1.2, 'sid')
    m.prism([(yd0 - 0.12, zb + 1.2), (yd0 + 1.7, zb + 1.2), (yd0 + 0.79, zb + 1.75)], -0.88, 0.88, ['shingle'], hull='full')
    m.parent = Matrix.Translation((0, yd0, 0))
    window(m, -0.42, 0.42, zb + 0.05, zb + 1.0, grille=True, sill=False)
    m.parent = Matrix.Identity(4)
    chimney(m, 2.1, 2.6, eave + 1.5, R + 1.0, c='brk')
    # porch
    if walk:
        porch_balcony(m, cols, 'sid')
    else:
        m.bx(-HW + 0.05, HW - 0.05, -5.6, FW, 0.0, GF, 'stone', cull='b')
        uq(m, -HW + 0.05, HW - 0.05, -5.6, FW, GF + 0.004, 'woodD')
        m.bx(DOOR[0] - 0.1, DOOR[1] + 0.1, -6.0, -5.6, 0.0, GF / 2, 'stone', cull='b')
        cols += [wbox(-HW + 0.05, -5.6, 0, HW - 0.05, FW, GF), wbox(DOOR[0] - 0.1, -6.0, 0, DOOR[1] + 0.1, -5.6, GF / 2)]
        for x in (-2.8, -0.7, 2.8):
            post(m, x, -5.45, GF, 2.95, 0.08, 'trim', seg=6)
            TD.porch_post(m, x, -5.45, 2.95, GF)
            cols.append(box(x - 0.09, -5.54, GF, x + 0.09, -5.36, 2.95))
        m.prism([(-5.75, 2.9), (FW + 0.01, 2.9), (FW + 0.01, 3.45), (-5.75, 3.08)], -HW + 0.02, HW - 0.02, ['shingle'], hull='full')
        dq(m, -HW + 0.05, HW - 0.05, -5.7, FW - 0.01, 2.895, 'trimD')
        for (x0, x1) in ((-0.62, 2.72),):
            m.bx(x0, x1, -5.5, -5.4, GF + 0.85, GF + 0.92, 'trim')
            pickets_x(m, x0 + 0.05, x1 - 0.05, -5.45, GF + 0.06, GF + 0.85, 0.15, 0.04, 'trim')
            m.bx(x0, x1, -5.5, -5.4, GF, GF + 0.06, 'trim', hull='none', cull='b')
            cols.append(box(x0, -5.5, GF, x1, -5.4, GF + 0.92))
            TD.rail_cap(m, x0, x1, -5.45, GF + 0.92)
        porch_bench(m, cols, 0.9, 2.5, -4.6, GF)
        TD.nosing(m, -HW + 0.05, HW - 0.05, -5.6, GF)
        TD.nosing(m, DOOR[0] - 0.1, DOOR[1] + 0.1, -6.0, GF / 2)
        TD.bx(m, -HW + 0.025, HW - 0.025, -5.82, -5.747, 2.875, 3.06, 'trimD', cull='blrk')     # porch-roof gutter
    back_facade(m, cols, 'sid', eave, walk, siding=True, gutter=True)
    side_faces(m, 'sid', eave, siding=True)
    if walk:
        interior_shell(m, cols)
        inner_front_back(m, hf, hb)
        inside_window(m, -0.3, 2.3, 1.15, 2.55, IY0, 1)
        inside_window(m, -2.4, -1.6, UF + 0.55, UF + 2.0, IY0, 1)
        inside_window(m, 1.6, 2.4, UF + 0.55, UF + 2.0, IY0, 1)
        walk_extras(m, cols)
    make(name, m, ao, cols=cols)


def side_faces(m, body, eave, siding=False, brick=False):
    """pattern lines and trim on both side walls (the end of a row shows them)"""
    for sx in (-1, 1):
        m.parent = frame_side(sx)
        L0, L1 = FW, BW   # local x runs along the wall
        a, b = (FW, BW) if sx > 0 else (-BW, -FW)
        rects = [(a, b, GF, eave)]
        if siding:
            lines_h(m, rects, GF, eave, 0.5, 'trimD', d=0.004, w=0.03)
        if brick:
            lines_h(m, rects, GF, eave, 0.6, 'mortar', d=0.004, w=0.02)
        fz(m, a, b, 0.0, GF, 0.008, 'stone')
        if sx > 0:
            TD.meter(m, 3.4, 1.55)
        else:
            TD.hose_bib(m, -3.6, 0.75)
    m.parent = Matrix.Identity(4)


def back_services(m, top, walk, siding, gutter, gaps):
    """lane-side trims and services (back frame): siding trims, a downpipe at the corner with its gutter elbow or a
    scupper"""
    if siding:
        TD.siding_trim(m, -HW, HW, top, GF, UF, gaps)
    x = -2.8 if walk else 2.75
    if gutter:
        zg = top - 0.35 * math.tan(math.radians(28)) - 0.04
        TD.downpipe(m, x, 0.15, zg, jog=0.46)
    else:
        TD.downpipe(m, x, 0.15, top - 0.34)


def back_facade(m, cols, body, top, walk, siding=False, brick=False, garage=True, gutter=False):
    """the lane side: a garage door (closed houses), a back door, windows, a deck light"""
    m.parent = frame_back()
    # back frame: local x = -piece x
    hb = [(-DOOR[1], -DOOR[0], 0.0, GF + DOOR_H)] if walk else []
    rects = clip_rects(-HW, HW, GF, top, hb)
    if siding:
        siding_face(m, rects, top)
    if brick:
        brick_face(m, rects, top)
    if walk:
        foundation(m, -HW, HW)
    else:
        foundation(m, -HW, -2.7)
        foundation(m, 0.7, HW)
    if walk:
        door(m, -DOOR[1], -DOOR[0], GF, GF + DOOR_H, open_=True, transom=False)
        window(m, -1.6, 0.6, 1.25, 2.35, grille=False)          # over the sink
        window(m, -1.9, -0.9, UF + 0.6, UF + 1.9)
        window(m, 0.9, 1.9, UF + 0.6, UF + 1.9)
        carriage_lamp(m, 2.95 - 0.95 - 0.2, GF + 1.8)
        back_services(m, top, walk, siding, gutter, [(-DOOR[1] - 0.17, -DOOR[0] + 0.17)])
    else:
        # garage door: raised panels in four rows
        g0, g1 = -2.6, 0.6
        fz(m, g0 - 0.1, g1 + 0.1, 0.0, 2.45, 0.012, 'trim')
        fz(m, g0, g1, 0.0, 2.3, 0.018, 'trimD')
        for r in range(4):
            for c in range(4):
                x = g0 + 0.1 + c * (g1 - g0 - 0.2) / 4
                z = 0.12 + r * 0.55
                fz(m, x + 0.03, x + (g1 - g0 - 0.2) / 4 - 0.03, z, z + 0.42, 0.022, 'trim')
        for c in range(4):
            x = g0 + 0.1 + c * (g1 - g0 - 0.2) / 4
            fz(m, x + 0.03, x + (g1 - g0 - 0.2) / 4 - 0.03, 0.12 + 3 * 0.55 + 0.1, 0.12 + 3 * 0.55 + 0.3, 0.026, 'glass')
        door(m, 1.3, 2.3, GF, GF + 2.2, transom=False, panels=False)
        carriage_lamp(m, 0.95, 1.9)
        TD.garage_door_detail(m, g0, g1, [0.605, 1.155, 1.705], -1.375, 2.3)
        gaps = [(-2.8, 0.75), (1.1, 2.5)]
        for x in (-1.9, 0.0, 1.9):
            if top > 7.0 or x != 0.0:
                window(m, x - 0.45, x + 0.45, UF + 0.6, UF + 1.9)
        if top > 7.0:
            for x in (-1.9, 1.9):
                window(m, x - 0.45, x + 0.45, 6.6, 8.0)
        back_services(m, top, walk, siding, gutter, gaps)
        m.parent = Matrix.Identity(4)
        # the door step at the lane, collision for nothing proud of the wall here
        m.bx(-2.3, -1.3, BW, BW + 0.4, 0.0, GF / 2, 'stone', cull='bf')
        cols.append(wbox(-2.3, BW, 0.0, -1.3, BW + 0.4, GF / 2))
    m.parent = Matrix.Identity(4)
    if walk:
        m.bx(DOOR[0] - 0.15, DOOR[1] + 0.15, BW, BW + 0.5, 0.0, GF / 2, 'stone', cull='bf')
        cols.append(wbox(DOOR[0] - 0.15, BW, 0.0, DOOR[1] + 0.15, BW + 0.5, GF / 2))


def walk_extras(m, cols):
    """the swung-in leaves of the open front / back / balcony doors and the bedroom door"""
    cols.append(open_leaf(m, DOOR[0], IY0, GF, DOOR_H - 0.05, 0.9, 1, swing=1))
    cols.append(open_leaf(m, DOOR[0], IY1, GF, DOOR_H - 0.05, 0.9, -1, swing=1))
    for x in FRENCH:
        cols.append(open_leaf(m, x, IY0, UF, FR_H - 0.05, 0.6, 1, swing=1 if x < 0 else -1))
    cols.append(open_leaf(m, DOOR[1], PART_Y + 0.14, UF, DOOR_H - 0.3, 0.8, 1, swing=-1))


def house_stucco(pal, name, walk, ao, num=14):
    m = new(pal)
    cols = []
    eave = EAVE2
    hf = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H), (FRENCH[0], FRENCH[1], UF, UF + FR_H)] if walk else []
    hb = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H)] if walk else []
    walls(m, cols, -HW, HW, FW, BW, 0.0, eave, 'stu', hf, hb, inner='plaster' if walk else None)
    R, k, t = roof_gable_y(m, FW, BW, eave, 38, body='stu')
    m.parent = frame_front()
    foundation(m, -HW, HW, c='stoneD')
    fz(m, -HW, HW, eave - 0.3, eave - 0.22, 0.01, 'trimD')
    # gable: a round attic vent with clay tiles round it
    m.cy((0.0, -0.01, eave + 0.95), 0.42, 0.42, 0.02, 'tileR', seg=12, rot=(90, 0, 0), hull='none')
    m.cy((0.0, -0.025, eave + 0.95), 0.32, 0.32, 0.02, 'glassD', seg=12, rot=(90, 0, 0), hull='none')
    for i in range(4):
        fz(m, -0.3, 0.3, eave + 0.72 + i * 0.13, eave + 0.76 + i * 0.13, 0.04, 'stuC')
    if walk:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H, open_=True, trim='trimD')
        window(m, -0.2, 0.9, 0.95, 2.45, trim='trimD', arch=True, grille=False, box='tileR')
        window(m, 1.45, 2.45, 0.95, 2.45, trim='trimD', arch=True, grille=False)
        door(m, FRENCH[0], FRENCH[1], UF, UF + FR_H, open_=True, transom=False, trim='trimD')
        window(m, -2.4, -1.6, UF + 0.6, UF + 1.9, trim='trimD', shutters=True, grille=False)
        window(m, 1.6, 2.4, UF + 0.6, UF + 1.9, trim='trimD', shutters=True, grille=False)
    else:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H - 0.2, trim='trimD', transom=False, arch=True)
        r = (DOOR[1] - DOOR[0]) / 2 + 0.12
        xc = (DOOR[0] + DOOR[1]) / 2
        zc = GF + DOOR_H - 0.2
        pts = [(xc + math.cos(math.pi * i / 8) * r, -0.016, zc + math.sin(math.pi * i / 8) * r) for i in range(9)]
        poly(m, pts, 'trimD', (0, -1, 0))
        pts = [(xc + math.cos(math.pi * i / 8) * (r - 0.12), -0.02, zc + math.sin(math.pi * i / 8) * (r - 0.12)) for i in range(9)]
        poly(m, pts, 'door', (0, -1, 0))
        window(m, -0.4, 0.8, 0.95, 2.45, trim='trimD', arch=True, grille=False, box='tileR')
        window(m, 1.4, 2.5, 0.95, 2.45, trim='trimD', arch=True, grille=False, box='tileR')
        # Juliet balcony upstairs
        window(m, -0.55, 0.55, UF + 0.25, UF + 2.0, trim='trimD', grille=True)
        fbox(m, -0.85, 0.85, UF + 0.15, UF + 0.25, 0.0, 0.4, 'iron', cull='k')
        fbox(m, -0.85, 0.85, UF + 0.92, UF + 0.97, 0.36, 0.4, 'iron', cull='k')
        for i in range(9):
            x = -0.78 + i * 0.195
            fbox(m, x - 0.015, x + 0.015, UF + 0.25, UF + 0.92, 0.37, 0.39, 'iron', cull='tbk')
        window(m, -2.4, -1.6, UF + 0.6, UF + 1.9, trim='trimD', shutters=True, grille=False)
        window(m, 1.6, 2.4, UF + 0.6, UF + 1.9, trim='trimD', shutters=True, grille=False)
        door_hood(m, DOOR[0], DOOR[1], GF + DOOR_H + 0.12, c='stuC', roofc='tileR')
    carriage_lamp(m, DOOR[1] + 0.35, GF + 1.8)
    house_number(m, DOOR[1] + 0.35, GF + 2.35, num)
    m.parent = Matrix.Identity(4)
    if walk:
        porch_balcony(m, cols, 'stu')
    else:
        m.bx(DOOR[0] - 0.2, DOOR[1] + 0.2, -5.3, FW, 0.0, GF, 'tileR', cull='b')
        m.bx(DOOR[0] - 0.2, DOOR[1] + 0.2, -5.9, -5.3, 0.0, GF / 2, 'tileR', cull='b')
        cols += [wbox(DOOR[0] - 0.2, -5.3, 0, DOOR[1] + 0.2, FW, GF), wbox(DOOR[0] - 0.2, -5.9, 0, DOOR[1] + 0.2, -5.3, GF / 2)]
        TD.nosing(m, DOOR[0] - 0.2, DOOR[1] + 0.2, -5.3, GF)
        TD.nosing(m, DOOR[0] - 0.2, DOOR[1] + 0.2, -5.9, GF / 2)
        for x in (-0.2, 2.2):
            m.bx(x - 0.32, x + 0.32, -5.2, -4.6, 0.0, 0.55, 'tileR')
            shrub(m, x, -4.9, 0.36, z=0.52, c='leafD', c2='leaf')
            cols.append(box(x - 0.32, -5.2, 0, x + 0.32, -4.6, 0.55))
    back_facade(m, cols, 'stu', eave, walk)
    side_faces(m, 'stu', eave)
    if walk:
        interior_shell(m, cols, inner='stuW', floor='woodL')
        inner_front_back(m, hf, hb, inner='stuW')
        inside_window(m, -0.2, 0.9, 0.95, 2.45, IY0, 1)
        inside_window(m, 1.45, 2.45, 0.95, 2.45, IY0, 1)
        inside_window(m, -2.4, -1.6, UF + 0.6, UF + 1.9, IY0, 1)
        inside_window(m, 1.6, 2.4, UF + 0.6, UF + 1.9, IY0, 1)
        walk_extras(m, cols)
    make(name, m, ao, cols=cols)


def house_brick(pal, name, walk, ao, num=16):
    m = new(pal)
    cols = []
    top = EAVE3
    hf = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H), (FRENCH[0], FRENCH[1], UF, UF + FR_H)] if walk else []
    hb = [(DOOR[0], DOOR[1], 0.0, GF + DOOR_H)] if walk else []
    walls(m, cols, -HW, HW, FW, BW, 0.0, top, 'brk', hf, hb, inner='sidC' if walk else None)
    # flat roof: parapet cap and a roof hatch box behind
    m.bx(-HW, HW, FW, BW, top, top + 0.05, 'shingleD', hull='none', cull='b')
    m.bx(1.0, 2.2, 1.0, 2.4, top + 0.05, top + 0.7, 'steel')
    m.parent = frame_front()
    rects = clip_rects(-HW, HW, GF, top, hf)
    brick_face(m, rects, top - 0.4)
    foundation(m, -HW, HW, c='stoneD')
    cornice(m, -HW, HW, top - 0.22, brackets=7)
    TD.brick_trim(m, -HW, HW, GF, [(DOOR[0] - 0.17, DOOR[1] + 0.17)])
    # third storey windows (both styles)
    for x in (-1.9, 0.0, 1.9):
        window(m, x - 0.42, x + 0.42, 6.75, 8.3, grille=True)
        fz(m, x - 0.55, x + 0.55, 8.3, 8.48, 0.016, 'stone')
    if walk:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H, open_=True)
        window(m, -0.3, 2.3, 1.1, 2.6, grille=True)
        fz(m, -0.45, 2.45, 2.69, 2.86, 0.016, 'stone')
        door(m, FRENCH[0], FRENCH[1], UF, UF + FR_H, open_=True, transom=False)
        for x in (-1.9, 1.9):
            window(m, x - 0.42, x + 0.42, UF + 0.5, UF + 2.0)
            fz(m, x - 0.55, x + 0.55, UF + 2.09, UF + 2.27, 0.016, 'stone')
    else:
        door(m, DOOR[0], DOOR[1], GF, GF + DOOR_H)
        fz(m, DOOR[0] - 0.2, DOOR[1] + 0.2, GF + DOOR_H + 0.16, GF + DOOR_H + 0.36, 0.02, 'stone')
        for x in (-0.15,):
            window(m, x - 0.42, x + 0.42, UF + 0.5, UF + 2.0)
            fz(m, x - 0.55, x + 0.55, UF + 2.09, UF + 2.27, 0.016, 'stone')
        window(m, -2.5, -1.7, UF + 0.5, UF + 2.0)
        fz(m, -2.62, -1.58, UF + 2.09, UF + 2.27, 0.016, 'stone')
    house_number(m, DOOR[0] - 0.0 + 0.65, GF + DOOR_H + 0.5, num) if not walk else house_number(m, -1.0, GF + 2.25, num)
    m.parent = Matrix.Identity(4)
    if not walk:
        # two-storey bay window on the right, copper-coloured cap
        bx0, bx1, bd = 0.75, 2.75, 0.62
        m.bx(bx0, bx1, FW - bd, FW, 0.0, UF + 2.45, 'brk')
        m.bx(bx0 - 0.06, bx1 + 0.06, FW - bd - 0.06, FW, UF + 2.45, UF + 2.6, 'trim')
        m.prism([(FW - bd - 0.06, UF + 2.6), (FW, UF + 2.6), (FW, UF + 2.95)], bx0 - 0.06, bx1 + 0.06, ['doorT'], hull='full', skip=(1,))
        cols.append(box(bx0, FW - bd, 0.0, bx1, FW, UF + 2.95))
        m.parent = Matrix.Translation((0, FW - bd, 0))
        brick_face(m, [(bx0, bx1, GF, UF + 2.45)], UF + 2.45)
        foundation(m, bx0, bx1, c='stoneD')
        for z0 in (1.0, UF + 0.5):
            window(m, bx0 + 0.3, bx1 - 0.3, z0, z0 + 1.5, grille=True)
            fz(m, bx0 + 0.1, bx1 - 0.1, z0 + 1.6, z0 + 1.76, 0.016, 'stone')
        m.parent = Matrix.Identity(4)
        for sx in (-1, 1):
            xx = bx0 if sx < 0 else bx1
            m.parent = Matrix.Translation((xx, FW - bd / 2, 0)) @ Matrix.Rotation(sx * math.pi / 2, 4, 'Z')
            for z0 in (1.0, UF + 0.5):
                window(m, -0.16, 0.16, z0, z0 + 1.5, grille=False, sill=False, glint=False)
            m.parent = Matrix.Identity(4)
        stoop_iron(m, cols)
        m.parent = frame_front()
        fbox(m, DOOR[0] - 0.2, DOOR[1] + 0.32, GF + DOOR_H + 0.4, GF + DOOR_H + 0.5, 0.0, 0.7, 'iron', hull='full', cull='k')
        for x in (DOOR[0] - 0.12, DOOR[1] + 0.25):
            m.bm_((x, -0.02, GF + DOOR_H - 0.1), (x, -0.66, GF + DOOR_H + 0.42), 0.03, 'iron', hull='none')
        m.parent = Matrix.Identity(4)
    else:
        porch_balcony(m, cols, 'brk')
    back_facade(m, cols, 'brk', top, walk, brick=True)
    side_faces(m, 'brk', top - 0.4, brick=True)
    if walk:
        interior_shell(m, cols, inner='sidC', floor='wood')
        inner_front_back(m, hf, hb, inner='sidC')
        inside_window(m, -0.3, 2.3, 1.1, 2.6, IY0, 1)
        for x in (-1.9, 1.9):
            inside_window(m, x - 0.42, x + 0.42, UF + 0.5, UF + 2.0, IY0, 1)
        walk_extras(m, cols)
    make(name, m, ao, cols=cols)


def house_garage(pal, name, ao, num=18):
    """modern three-storey with a front garage: brick base, board siding above, a box bay on the first floor"""
    m = new(pal)
    cols = []
    top = EAVE3
    walls(m, cols, -HW, HW, FW, BW, 0.0, top, 'sid', (), (), inner=None)
    m.parent = frame_front()
    fz(m, -HW, HW, 0.0, 3.05, 0.006, 'brk')
    brick_face(m, clip_rects(-HW, HW, 0.0, 3.05, [(-2.6, -1.4, 0.0, GF + 2.3), (-0.45, 2.8, 0.0, 2.45)]), 3.0, z0=0.0, d=0.0105)
    fz(m, -HW, HW, 3.05, 3.2, 0.014, 'trimD')
    lines_v(m, [(-HW, HW, 3.2, top)], -HW, HW, 0.25, 'trimD', d=0.004, w=0.02)
    # garage door (horizontal ribs, a glass top row), entry door with a flat canopy
    g0, g1 = -0.35, 2.7
    fz(m, g0 - 0.1, g1 + 0.1, 0.0, 2.45, 0.014, 'trimD')
    fz(m, g0, g1, 0.0, 2.35, 0.02, 'steel')
    for r in range(6):
        fz(m, g0 + 0.04, g1 - 0.04, 0.3 + r * 0.33, 0.33 + r * 0.33, 0.024, 'chrome')
    fz(m, g0 + 0.1, g1 - 0.1, 2.0, 2.25, 0.026, 'glassD')
    TD.garage_door_detail(m, g0, g1, [], 1.2, 2.35)
    door(m, -2.6, -1.4, GF, GF + 2.3, transom=False, panels=False, trim='trimD')
    fz(m, -2.45, -2.35, GF + 0.3, GF + 2.0, 0.016, 'chrome')
    fbox(m, -2.85, -1.15, GF + 2.45, GF + 2.55, 0.0, 0.9, 'shingleD', hull='full', cull='k')
    house_number(m, -1.0, 1.6, num)
    # first floor: the box bay (dark frame round a wide window), second floor: a ribbon of windows
    fbox(m, -1.0, 2.6, 3.55, 5.85, 0.0, 0.55, 'shingleD', hull='full', cull='k')
    m.parent = frame_front() @ Matrix.Translation((0, -0.55, 0))
    fz(m, -0.85, 2.45, 3.75, 5.6, 0.012, 'iron')
    fz(m, -0.78, 2.38, 3.82, 5.53, 0.02, 'glass')
    for x in (0.38, 1.54):
        fz(m, x - 0.02, x + 0.02, 3.82, 5.53, 0.026, 'iron')
    poly(m, [(-0.6, -0.03, 4.0), (-0.45, -0.03, 4.0), (-0.1, -0.03, 5.3), (-0.25, -0.03, 5.3)], 'glassL', (0, -1, 0))
    m.parent = frame_front()
    window(m, -2.55, -1.6, 3.9, 5.5, grille=False, trim='iron')
    for x in (-2.0, 0.0, 2.0):
        window(m, x - 0.7, x + 0.7, 6.7, 8.2, grille=False, trim='iron', sill=False)
    fbox(m, -HW, HW, top - 0.15, top + 0.1, 0.0, 0.08, 'shingleD', hull='full', cull='k')
    m.parent = Matrix.Identity(4)
    cols.append(box(-1.0, FW - 0.55, 3.55, 2.6, FW, 5.85))
    # roof: a mono-pitch clerestory over the back half, coping
    m.bx(-HW, HW, FW, BW, top, top + 0.06, 'shingleD', hull='none', cull='b')
    m.prism([(0.6, top + 0.06), (BW + 0.2, top + 0.06), (BW + 0.2, top + 1.3), (0.6, top + 0.21)], -HW, HW, ['steel'], hull='full', skip=(0,))
    # entry step, a planter by the garage
    m.bx(-2.75, -1.25, -5.0, FW, 0.0, GF, 'stone', cull='b')
    m.bx(-2.75, -1.25, -5.5, -5.0, 0.0, GF / 2, 'stone', cull='b')
    cols += [wbox(-2.75, -5.0, 0, -1.25, FW, GF), wbox(-2.75, -5.5, 0, -1.25, -5.0, GF / 2)]
    m.bx(-1.15, -0.55, -5.1, -4.6, 0.0, 0.5, 'shingleD')
    shrub(m, -0.85, -4.85, 0.32, z=0.48, c='leafD', c2='leaf')
    cols.append(box(-1.15, -5.1, 0, -0.55, -4.6, 0.5))
    back_facade(m, cols, 'sid', top, False)
    side_faces(m, 'sid', top)
    make(name, m, ao, cols=cols)


def build_houses(pal, ao):
    house_siding(pal, 'House_Siding', False, ao, num=12)
    house_stucco(pal, 'House_Stucco', False, ao, num=14)
    house_brick(pal, 'House_Brick', False, ao, num=16)
    house_garage(pal, 'House_Garage', ao, num=18)
    house_siding(pal, 'Walk_Siding', True, ao, num=21)
    house_stucco(pal, 'Walk_Stucco', True, ao, num=23)
    house_brick(pal, 'Walk_Brick', True, ao, num=25)
