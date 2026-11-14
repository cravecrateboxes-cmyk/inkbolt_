"""kit-venetian modelled detail (tactical look plan Stage 11): window lintels, aprons and sill corbels, shutter hinge
straps, cornice dentils and a cornice bead, string-course drip lips, plinth caps, drainpipes with straps and rain
heads, door studs / knockers / keystones, arch voussoir joints, balcony nosings and corbels, coping joints on the quay and
the bridge, cloister column bases / astragals / abacus lips and arch imposts, stair nosings, stall post pegs and cloth
ties, lamp-post collars, bucket hoops. Every part is ink=False (no outline shell), at least 3 mm proud, sunk 3 mm into
what it sits on, and horizontal runs stop 5 mm short of a module's sides. Nothing here changes a piece's origin,
footprint, collision boxes or the parts already drawn; it only adds shapes. Facade faces look toward Blender -Y
(plane y = -0.5)."""
import math

Y = -0.5
E = 0.003     # sink into the face
I = 0.005     # horizontal runs stop this far short of a piece's sides


def bx(k, x0, x1, y0, y1, z0, z1, c, cull=''):
    k.bxc(x0, x1, y0, y1, z0, z1, c, cull=cull, ink=False)


# ================================================================ facade
def window_dress(k, x0, x1, z0, z1, box=False, y=Y):
    """a projecting lintel cap over the frame, and under the sill an apron panel on two tapered corbels"""
    bx(k, x0 - 0.1, x1 + 0.1, y - 0.045, y + E, z1 + 0.084, z1 + 0.13, 'stone', cull='k')
    bx(k, x0 - 0.115, x1 + 0.115, y - 0.06, y + E, z1 + 0.13 - E, z1 + 0.15, 'stone', cull='k')
    if box:
        return
    bx(k, x0 + 0.02, x1 - 0.02, y - 0.014, y + E, z0 - 0.19, z0 - 0.07 + E, 'stoneD', cull='kt')
    for xc in (x0 - 0.04, x1 + 0.04):
        k.prism_xz([(xc - 0.035, z0 - 0.07 + E), (xc + 0.035, z0 - 0.07 + E), (xc + 0.02, z0 - 0.2), (xc - 0.02, z0 - 0.2)],
                   y - 0.055, y + E, 'stone', ink=False, cull='k')


def shutter_hinges(k, leaf, z0, z1, hinge_left, yb):
    """two iron strap hinges on a shutter leaf (a, b), hinge side given"""
    a, b = leaf
    w = (b - a) * 0.62
    for z in (z0 + 0.1, z1 - 0.16):
        if hinge_left:
            xa, xb = a + I, a + I + w
        else:
            xa, xb = b - I - w, b - I
        bx(k, xa, xb, yb - 0.035 - 0.007, yb - 0.035 + E, z, z + 0.045, 'iron', cull='k')
        pin = xa + 0.022 if hinge_left else xb - 0.022
        bx(k, pin - 0.012, pin + 0.012, yb - 0.035 - 0.014, yb - 0.035 - 0.007 + E, z - 0.005, z + 0.05, 'iron', cull='k')


def dentils(k, x0, x1, H, y=Y):
    """tooth blocks hanging under the cornice lip"""
    n = max(2, int(round((x1 - x0) / 0.125)))
    pw = (x1 - x0) / n
    for i in range(n):
        xa = x0 + pw * i + pw * 0.22
        xb = x0 + pw * (i + 1) - pw * 0.22
        if xa < x0 + I or xb > x1 - I:
            continue
        bx(k, xa, xb, y - 0.22, y - 0.1 + E, H - 0.26 - 0.055, H - 0.26 + E, 'stone', cull='kt')


def cornice_bead(k, x0, x1, H, y=Y):
    bx(k, x0 + I, x1 - I, y - 0.295, y - 0.28 + E, H - 0.14, H - 0.1, 'stoneD', cull='k')


def string_lip(k, x0, x1, gf, y=Y):
    bx(k, x0 + I, x1 - I, y - 0.082, y - 0.06 + E, gf + 0.06 - E, gf + 0.088, 'stone', cull='k')


def plinth_lip(k, a, b, y=Y):
    bx(k, a + I, b - I, y - 0.05, y - 0.035 + E, 0.49, 0.53, 'stone', cull='kb')


def drainpipe(k, x, H, gf, y=Y):
    """a round iron downpipe from a bronze rain head under the cornice to the ground, held on strap clips"""
    r = 0.034
    ztop = H - 0.72
    k.cyl(x, y - 0.031, 0.0, r, r, ztop, 'iron', seg=8, ink=False)
    k.cyl(x, y - 0.031, 0.0, r + 0.014, r + 0.014, 0.1, 'iron', seg=8, ink=False)      # shoe
    z = 0.9
    while z < ztop - 0.3:
        if abs(z - gf) > 0.25:
            bx(k, x - 0.05, x + 0.05, y - 0.075, y + E, z - 0.02, z + 0.02, 'iron', cull='k')
        z += 1.25
    bx(k, x - 0.085, x + 0.085, y - 0.115, y + E, ztop - 0.004, ztop + 0.24, 'bronze', cull='k')
    bx(k, x - 0.1, x + 0.1, y - 0.13, y - 0.1 + E, ztop + 0.2, ztop + 0.25, 'bronze', cull='k')


def voussoirs(k, xc, zs, a, w, y, f=-1, n=8, c='stoneD', t=0.012, skip_mid=True):
    """radial joint lines across an arch's stone band (intrados radius a, band width w) as painted strips on the plane y"""
    for i in range(1, n):
        if skip_mid and 2 * i == n:
            continue
        ang = math.pi * i / n
        ca, sa = math.cos(ang), math.sin(ang)
        pa = (xc + ca * (a + 0.004), zs + sa * (a + 0.004))
        pb = (xc + ca * (a + w - 0.004), zs + sa * (a + w - 0.004))
        dx, dz = -sa * t / 2, ca * t / 2
        k.poly([(pa[0] - dx, y, pa[1] - dz), (pb[0] - dx, y, pb[1] - dz), (pb[0] + dx, y, pb[1] + dz), (pa[0] + dx, y, pa[1] + dz)], c, (0, f, 0))


def keystone(k, xc, zcrown, w, y=Y, f=-1, h=0.14, d=0.032):
    """a tapering keystone standing d out of the facade plane at the crown of an arch's band"""
    yo = y + f * d
    y0, y1 = (yo, y + E) if f < 0 else (y - E, yo)
    k.prism_xz([(xc - w * 0.55, zcrown + 0.005), (xc + w * 0.55, zcrown + 0.005), (xc + w * 0.8, zcrown + h), (xc - w * 0.8, zcrown + h)],
               y0, y1, 'stone', ink=False, cull='b')


def door_detail(k, x0, x1, top, yd, cr, round_arch=True):
    """voussoir joints and a keystone over the arch, studs on the leaf panels, a knocker ring on a boss"""
    xm = (x0 + x1) / 2
    a = (x1 - x0) / 2
    fw = 0.08
    voussoirs(k, xm, top, a, fw, Y - 0.010, n=8)
    keystone(k, xm, cr + 0.0, 0.07, h=fw + 0.06, d=0.034)
    ys = yd - 0.003     # the inner panels' plane
    for (pa, pb) in ((x0 + 0.07, xm - 0.06), (xm + 0.06, x1 - 0.07)):
        for (c0, c1) in ((0.25, 1.15), (1.35, top - 0.15)):
            for xs in (pa + 0.07, pb - 0.07):
                for zs in (c0 + 0.07, c1 - 0.07):
                    if abs(xs - (xm + 0.12)) < 0.1 and abs(zs - 1.06) < 0.1:
                        continue
                    bx(k, xs - 0.014, xs + 0.014, ys - 0.007, ys + E, zs - 0.014, zs + 0.014, 'iron', cull='k')
    # knocker: a hanger on the boss, a bronze ring (a dark centre makes it read as a ring)
    kx = xm + 0.12
    bx(k, kx - 0.008, kx + 0.008, yd - 0.03, yd - 0.012, 1.11, 1.22, 'bronze', cull='k')
    k.cyl(kx, yd - 0.03, 1.06, 0.05, 0.05, 0.012, 'bronze', seg=6, ink=False, rot=(90, 0, 0))
    k.cyl(kx, yd - 0.03 - 0.012 + 0.0, 1.06, 0.03, 0.03, 0.004, 'woodD', seg=6, ink=False, rot=(90, 0, 0))


def shop_detail(k, x0, x1, top):
    xm = (x0 + x1) / 2
    a = (x1 - x0) / 2
    voussoirs(k, xm, top, a, 0.08, Y - 0.010, n=8)
    keystone(k, xm, top + a, 0.07, h=0.14, d=0.034)


def balcony_detail(k, x0, x1, z, depth, y=Y):
    """a drip nosing under the slab's front edge, and a corbel row"""
    yf = y - depth
    bx(k, x0 + I, x1 - I, yf - 0.03, yf + 0.05, z - 0.14 - 0.035, z - 0.14 + E, 'stone', cull='k')
    L = x1 - x0
    n = max(3, int(round(L / 0.8)) + 1)
    cx = (x0 + x1) / 2
    for i in range(n):
        c = x0 + 0.12 + (L - 0.24) * i / (n - 1)
        if abs(c - cx) < 0.14:
            continue
        k.prism_xz([(c - 0.05, z - 0.14 + E), (c + 0.05, z - 0.14 + E), (c + 0.03, z - 0.36), (c - 0.03, z - 0.36)],
                   y - depth * 0.62, y + E, 'stone', ink=False, cull='k')


# ================================================================ quay, bridge, walls
def coping_joint(k, x, y0, y1, z, c='paveD'):
    """a joint line across a coping stone's top face at height z (3 mm proud)"""
    bx(k, x - 0.006, x + 0.006, y0 + I, y1 - I, z - E, z + 0.003, c)


def quay_joints(k):
    """kerb stone joints, ashlar courses and perpends on the quay face, the coping joint on the rail"""
    for x in (-0.17, 0.17):
        coping_joint(k, x, 0.25, 0.5, 0.1)
    for z in (-0.15, -0.55, -0.85):
        bx(k, -0.495, 0.495, 0.497, 0.507, z, z + 0.012, 'paveD', cull='k')
    for (x, z0, z1) in ((0.2, -0.15, -0.3), (-0.25, -0.55, -0.3), (0.1, -0.55, -0.85)):
        bx(k, x - 0.006, x + 0.006, 0.497, 0.507, min(z0, z1) + 0.012, max(z0, z1), 'paveD', cull='k')


def mooring_ring(k, y=0.525):
    """an iron ring hanging on the plate (the plate stays as built)"""
    cz = -0.5 - 0.065
    pts = [(0.075 * math.cos(i * math.pi / 4), cz + 0.075 * math.sin(i * math.pi / 4)) for i in range(8)]
    for i in range(8):
        a = pts[i]
        b = pts[(i + 1) % 8]
        yy = y + 0.008 + (0.006 if i % 2 else 0.0)
        k.beam((a[0], yy, a[1]), (b[0], yy, b[1]), 0.02, 'iron', ink=False)


def pier_panel(k, y=-0.52):
    bx(k, -0.14, 0.14, y - 0.005, y + E, 0.28, 1.05, 'stoneD', cull='k')


def lamp_collars(k, x, y, zs):
    for z, r in zs:
        k.cyl(x, y, z, r, r, 0.04, 'bronze', seg=6, ink=False)


def bridge_detail(k, lamp):
    """coping joint on the balustrade cap, a drip course on the fascia (frame: the bridge model, along X)"""
    if lamp:
        lamp_collars(k, 0, 0, ((1.52, 0.062), (1.95, 0.058)))
        return
    bx(k, -0.006, 0.006, -0.125, 0.125, 1.097, 1.103, 'paveD')
    bx(k, -0.495, 0.495, 0.28, 0.345, -0.16, -0.06, 'stone', cull='')


def wall_coping_joint(k, top):
    bx(k, -0.006, 0.006, Y - 0.055, Y + 0.055, top - E, top + 0.003, 'paveD')


# ================================================================ cloister
def column_detail(k):
    k.lathe(0, 0, 0.157, [(0.19, 0.0), (0.21, 0.03), (0.2, 0.07), (0.17, 0.11)], 'stone', seg=6, ink=False, caps=True)
    k.lathe(0, 0, 1.95, [(0.165, 0.0), (0.195, 0.02), (0.165, 0.04)], 'stone', seg=6, ink=False)
    bx(k, -0.31, 0.31, -0.31, 0.31, 2.49, 2.55, 'stone', cull='t')


def arch_detail(k, cur, spring, top):
    for f in (-1, 1):
        yf = f * 0.208
        voussoirs(k, 0.0, spring, 1.22, 0.14, yf, f=f, n=12)
        yo = f * 0.235
        y0, y1 = (yo, f * 0.197) if f < 0 else (f * 0.197, yo)
        bx(k, -0.09, 0.09, y0, y1, spring + 1.22 + 0.005, spring + 1.22 + 0.165, 'stone', cull='b')
    for s in (-1, 1):
        xa, xb = (s * 1.23, s * 1.495) if s > 0 else (s * 1.495, s * 1.23)
        bx(k, xa, xb, -0.235, 0.235, spring + 0.014, spring + 0.15, 'stone', cull='')


# ================================================================ stairs, stalls, lamps, buckets
def nosing(k, x0, x1, lo, hi, za, dir_):
    """a tread's nosing: a 4 mm raised lip standing 25 mm out over the riser"""
    if dir_ > 0:
        ya, yb = lo - 0.025, lo + 0.04
    else:
        ya, yb = hi - 0.04, hi + 0.025
    bx(k, x0 + I, x1 - I, ya, yb, za - 0.035, za + 0.008, 'stoneD', cull='b')


def post_pegs(k, x, y, zs, hw=0.03, hd=0.03, c='wood'):
    for z in zs:
        bx(k, x - hw - 0.016, x + hw + 0.016, y - 0.01, y + 0.01, z - 0.012, z + 0.012, c, cull='')


def rope_wrap(k, x, y, z, r=0.05, c='rattan'):
    """a rope tie round a vertical post"""
    k.cyl(x, y, z, r, r, 0.03, c, seg=6, ink=False)


def beam_tie(k, x, y, z, r=0.03, c='rattan'):
    """a rope tie round a horizontal arm running along y"""
    k.cyl(x, y, z, r, r, 0.03, c, seg=6, ink=False, rot=(90, 0, 0))


def bucket_hoops(k, x, y, z):
    """two iron hoops on a flower bucket (a tapering 6-sided pail standing at z)"""
    for dz in (0.08, 0.2):
        r = 0.16 + 0.04 * (dz + 0.015) / 0.3 + 0.006
        k.lathe(x, y, z + dz, [(r, 0.0), (r, 0.03)], 'iron', seg=6, ink=False, caps=False)


def lamp_post_detail(k):
    lamp_collars(k, 0, 0, ((0.5, 0.088), (1.5, 0.078), (2.58, 0.07)))
    k.cyl(0, 0, 0.0, 0.2, 0.2, 0.03, 'iron', seg=6, ink=False)
    k.cyl(0, 0, 3.447, 0.03, 0.0, 0.1, 'bronze', seg=6, ink=False)


def well_joints(k):
    """coping joints round the basin's rim (the rim top is at z 1.08)"""
    for i in range(8):
        a = i * math.pi / 4
        k.beam((math.cos(a) * 0.45, math.sin(a) * 0.45, 1.082), (math.cos(a) * 0.66, math.sin(a) * 0.66, 1.082), 0.012, 'paveD', ink=False)
