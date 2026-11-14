"""kit-grove modelled detail (tactical look plan Stage 11): bolts through deck fascias and stringers, iron straps and
collars on braces and posts, rope lashings, rail-post caps, plank nails, log end grain, door and window hardware,
fascia / barge boards, chimney courses, lamp cages and sign bolts on the pieces the player sees most. Every part is
ink=False (no outline shell), >= 3 mm proud, embedded 3 mm, horizontal runs inset 5 mm from the piece sides. Colours
are palette names the kit already has (gunmetal, woodd, rope, heart, roof2, rockd ...)."""
import math

from kit_base import EMBED

IRON = 'gunmetal'


def bolt(k, x, y, z, face, c=IRON, s=0.035, p=0.006):
    """a bolt head (box) on a face; `face` = '-y' '+y' '-x' '+x' names the way the face looks; (x, y, z) is on the face"""
    e, h = EMBED, s / 2
    if face == '-y':
        k.bx(x - h, x + h, y - p, y + e, z - h, z + h, c, ink=False)
    elif face == '+y':
        k.bx(x - h, x + h, y - e, y + p, z - h, z + h, c, ink=False)
    elif face == '-x':
        k.bx(x - p, x + e, y - h, y + h, z - h, z + h, c, ink=False)
    else:
        k.bx(x - e, x + p, y - h, y + h, z - h, z + h, c, ink=False)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def collar(k, x, y, z, r, c=IRON, h=0.05, seg=6):
    k.cyl(x, y, z, r, r, h, c, seg=seg, ink=False)


def cage(k, x0, x1, y0, y1, z0, z1, c=IRON, w=0.014):
    """corner bars on a lantern box: 3 mm proud of both faces at each vertical edge, ends 3 mm inside the plates"""
    for x, sx in ((x0, -1), (x1, 1)):
        for y, sy in ((y0, -1), (y1, 1)):
            xa, xb = (x - 0.003, x - 0.003 + w) if sx < 0 else (x + 0.003 - w, x + 0.003)
            ya, yb = (y - 0.003, y - 0.003 + w) if sy < 0 else (y + 0.003 - w, y + 0.003)
            k.bx(xa, xb, ya, yb, z0 + 0.003, z1 - 0.003, c, ink=False)


# ------------------------------------------------------------------------------------------------ climbable redwood
def redwood(k, deck, foot, e2, posts, stringers, braces, rail_posts, lantern):
    """posts = [(x, y, tz)] ground log posts; stringers = [(a, b, face)]; braces = [(a, b)]; rail_posts =
    [(x, y, top, face)] stair rail posts (outer face); lantern = (x0, x1, y0, y1, z0, z1)"""
    zb = deck - 0.2
    for jx in (-3.5, -2.5, -0.6, 0.6, 2.6, 3.5):                     # bolts through the fascias at the joist lines
        bolt(k, jx, -foot, zb, '-y')
    for y in (-3.0, -1.5, 0.0, 1.5, 3.0):
        bolt(k, -foot, y, zb, '-x')
    for y in (-3.0, -1.5, 0.0):
        bolt(k, foot, y, zb, '+x')
    for x in (-3.0, -1.5):
        bolt(k, x, foot, zb, '+y')
    for i in range(20):                                              # plank nails on the joist lines
        yc = -foot + i * 0.4 + 0.012 + 0.188
        if i % 2 == 0:
            for nx in (-3.5, -2.5):
                k.bx(nx - 0.014, nx + 0.014, yc - 0.014, yc + 0.014, deck - EMBED, deck + 0.004, IRON, ink=False)
        elif yc < e2 - 0.1:
            k.bx(3.5 - 0.014, 3.5 + 0.014, yc - 0.014, yc + 0.014, deck - EMBED, deck + 0.004, IRON, ink=False)
    for (a, b) in braces:                                            # iron straps round the knee braces
        for t0 in (0.2, 0.82):
            k.beam(lerp3(a, b, t0), lerp3(a, b, t0 + 0.04), 0.19, IRON, ink=False)
    for (px, py, tz) in posts:                                       # collars on the ground log posts
        collar(k, px, py, 0.55, 0.15)
        collar(k, px, py, tz - 0.5, 0.15)
    for (a, b, face) in stringers:                                   # bolts on the stringers' outer faces
        for t in (0.2, 0.5, 0.8):
            p = lerp3(a, b, t)
            if face == '-y':
                bolt(k, p[0], p[1] - 0.07, p[2], '-y', s=0.04)
            elif face == '+x':
                bolt(k, p[0] + 0.07, p[1], p[2], '+x', s=0.04)
            else:
                bolt(k, p[0], p[1] + 0.07, p[2], '+y', s=0.04)
    for (px, py, top, face) in rail_posts:                           # lag bolts on the rail posts
        z = top + 0.7
        if face == '-y':
            bolt(k, px, py - 0.05, z, '-y', s=0.03)
        elif face == '+x':
            bolt(k, px + 0.05, py, z, '+x', s=0.03)
        else:
            bolt(k, px, py + 0.05, z, '+y', s=0.03)
    cage(k, *lantern)


# ------------------------------------------------------------------------------------------------ bridge, rails, pier
def bridge(k):
    for i in range(3):                                               # plank nails
        x = -1 / 3 + i / 3
        for y in (-0.25, 0.4):
            k.bx(x - 0.013, x + 0.013, y - 0.013, y + 0.013, -EMBED, 0.004, IRON, ink=False)
    k.bx(-0.058, 0.058, -0.494, -0.396, 0.8, 0.88, 'rope', ink=False)    # lashing round the post
    for z in (0.12, 0.62):
        bolt(k, 0.0, -0.49, z, '-y', s=0.03)
    for x in (-0.3, 0.3):
        bolt(k, x, -0.45, -0.19, '-y', s=0.035)
    k.bx(-0.065, 0.065, -0.486, -0.41, 1.047, 1.085, 'woodd', ink=False)  # newel cap above the handrail


def rail(k, corner):
    k.bx(-0.065, 0.065, 0.41, 0.486, 1.047, 1.085, 'woodd', ink=False)    # newel cap
    k.bx(-0.058, 0.058, 0.394, 0.494, 0.8, 0.88, 'rope', ink=False)        # lashing round the post
    bolt(k, 0.0, 0.4, 0.3, '-y', s=0.03)
    if corner:
        k.bx(-0.486, -0.41, -0.065, 0.065, 1.047, 1.085, 'woodd', ink=False)
        k.bx(-0.494, -0.394, -0.058, 0.058, 0.8, 0.88, 'rope', ink=False)
        bolt(k, -0.5, 0.0, 0.3, '-x', s=0.03)


def pier(k, top, posts_y, r=0.17):
    for y in posts_y:
        for z in (0.82, 0.9, 4.45, 4.53):                            # rope lashings where the braces meet the posts
            rr = r - 0.03 * (z + 0.15) / (top + 0.15 - 0.16) + 0.026
            k.cyl(0.0, y, z, rr, rr, 0.05, 'rope', seg=8, ink=False)
        for sx in (-1, 1):                                           # through-bolts on the cap beam ends
            bolt(k, sx * 0.13, y, top - 0.08, '-x' if sx < 0 else '+x', s=0.04)


# ------------------------------------------------------------------------------------------------ cabin
def window_detail(k, x, yw, z, w, h, s):
    """muntin, shutter hinges and board joints, sill corbels: same geometry as fam_kit_grove.window"""
    y = yw + 0.004 * s
    d = 0.006 * s

    def yy(front, back):
        a, b = y + front * d, y - back * s
        return min(a, b), max(a, b)
    y0, y1 = yy(7.5, 0.045)
    k.bx(x - w / 2, x + w / 2, y0, y1, z + h / 2 - 0.015, z + h / 2 + 0.015, 'woodd', ink=False)
    for sx in (-1, 1):
        xs = x + sx * (w / 2 + 0.11 + 0.22)
        for zz in (z + 0.12, z + h - 0.125):                          # strap hinges from the outer edge
            xa = xs + sx * 0.205
            ya, yb = yy(10, 0.047)
            k.bx(min(xa, xa - sx * 0.3), max(xa, xa - sx * 0.3), ya, yb, zz - 0.02, zz + 0.02, IRON, ink=False)
        for off in (-0.07, 0.07):                                    # board joints
            ya, yb = yy(8.5, 0.043)
            k.bx(xs + off - 0.006, xs + off + 0.006, ya, yb, z + 0.03, z + h - 0.03, 'roof2', ink=False)
        xc = x + sx * (w / 2 - 0.02)
        ya, yb = yy(11, 0.046)
        k.bx(xc - 0.03, xc + 0.03, ya, yb, z - 0.17, z - 0.097, 'woodd', ink=False)


def eave_boards(k, ya, za, yr, zr, ang, sgn, half=3.0):
    """a fascia on the low edge and barge boards on both gable edges of a roof slab (as build_cabin lays it out)"""
    L = math.hypot(yr - ya, zr - za)
    uy, uz = (yr - ya) / L, (zr - za) / L                            # unit vector low edge -> ridge
    cy, cz = (ya + yr) / 2, (za + zr) / 2 + 0.1
    hl = (L + 0.06) / 2 + 0.017
    k.bxr(0, cy - uy * hl, cz - uz * hl, 2 * half - 0.02, 0.034, 0.26, 'cabin2', rot=(sgn * ang, 0, 0), ink=False)
    for sx in (-1, 1):
        k.bxr(sx * (half + 0.017), cy, cz, 0.046, L + 0.1, 0.22, 'cabin2', rot=(sgn * ang, 0, 0), ink=False)


def cabin(k, corners, Y0, yr, zr, roofs):
    for (cx, cy) in corners:                                         # end grain on the outer end of each corner log
        for i in range(8):
            z = 0.45 + i * 0.3
            c = 'heart' if i % 4 < 2 else 'wood3'
            if i % 2:
                xb = cx - 0.226 if cx < 0 else cx + 0.217
                k.cyl(xb, cy, z, 0.085, 0.085, 0.009, c, seg=6, rot=(0, 90, 0), ink=False)
            else:
                yb = cy - 0.226 if cy < 0.6 else cy + 0.217
                k.cyl(cx, yb, z, 0.085, 0.085, 0.009, c, seg=6, rot=(-90, 0, 0), ink=False)
    for i in range(7):                                               # porch: joist ends and plank nails
        x = -2.445 + i * 0.81
        k.bx(x - 0.07, x + 0.07, -2.956, -2.947, 0.04, 0.2, 'woodd', ink=False)
        for nx in (-0.22, 0.22):
            k.bx(x + nx - 0.012, x + nx + 0.012, -2.87, -2.846, 0.297, 0.304, IRON, ink=False)
    for px in (-2.65, 2.65):                                         # post bases, knee braces, beam bolts
        k.bx(px - 0.15, px + 0.15, -2.93, -2.63, 0.285, 0.4, 'woodd', ink=False)
        s = 1 if px < 0 else -1
        k.beam((px + s * 0.1, -2.78, 1.75), (px + s * 0.62, -2.78, 2.307), 0.09, 'woodd', ink=False)
        for x in (px, px + s * 0.4):
            bolt(k, x, -2.9, 2.4, '-y', s=0.04)
    for x in (-1.38, 1.38):                                          # sign board bolts
        for z in (2.93, 2.59):
            k.bx(x - 0.02, x + 0.02, -2.987, -2.977, z - 0.02, z + 0.02, IRON, ink=False)
    for (a, b) in ((0.09, 0.145), (1.055, 1.11)):                    # door jambs, strap hinges, latch
        k.bx(a, b, Y0 - 0.075, Y0 + EMBED, 0.303, 2.305, 'woodd', ink=False)
    for z in (0.62, 1.95):
        k.bx(0.155, 0.86, Y0 - 0.069, Y0 - 0.045, z - 0.04, z + 0.04, IRON, ink=False)
        for x in (0.3, 0.55, 0.8):
            k.bx(x - 0.018, x + 0.018, Y0 - 0.077, Y0 - 0.066, z - 0.018, z + 0.018, IRON, ink=False)
    k.bx(0.93, 0.97, Y0 - 0.084, Y0 - 0.044, 1.0, 1.26, IRON, ink=False)
    k.bx(0.915, 0.985, Y0 - 0.078, Y0 - 0.047, 1.2, 1.3, IRON, ink=False)
    for i in range(1, 9):                                            # chimney: mortar bands, flue collar and opening
        z = i * 0.6
        for (ya, yb) in ((0.25 - 0.007, 0.25 + 0.003), (1.15 - 0.003, 1.15 + 0.007)):
            k.bx(2.78, 3.36, ya, yb, z - 0.012, z + 0.012, 'rockd', ink=False)
    k.bx(2.84, 3.30, 0.45, 0.95, 5.547, 5.72, 'rock3', ink=False)
    k.bx(2.93, 3.21, 0.56, 0.84, 5.714, 5.726, 'ink', ink=False)
    for (ya, za, ang, sgn) in roofs:
        eave_boards(k, ya, za, yr, zr, ang, sgn)


# ------------------------------------------------------------------------------------------------ camp props
def signpost(k, bands):
    """iron straps on the post between the boards, a cap, bolts on the boards (inside k.push frames made by the caller)"""
    for z in bands:
        collar(k, 0, 0, z, 0.08, h=0.04)
    k.cyl(0, 0, 2.197, 0.08, 0.03, 0.08, 'woodd', seg=6, ink=False)


def sign_bolt(k, L):
    for y in (-0.03, 0.03):
        bolt(k, 0.11, y, 0.0, '-y' if y < 0 else '+y', s=0.026, p=0.006)


def lantern_post(k):
    k.beam((0.0, 0.0, 1.7), (0.36, 0.0, 1.975), 0.03, 'woodd', ink=False)
    k.cyl(0.42, 0.0, 1.917, 0.12, 0.02, 0.06, IRON, seg=4, ink=False)
    cage(k, 0.34, 0.5, -0.08, 0.08, 1.48, 1.84)


def crate(k):
    for (x, z) in ((-0.415, 0.08), (-0.415, 0.44), (0.415, 0.08), (0.415, 0.44), (-0.3, 0.25), (0.3, 0.25)):
        k.bx(x - 0.012, x + 0.012, -0.326, -0.317, z - 0.012, z + 0.012, IRON, ink=False)
    for y in (-0.1, 0.1):                                            # plank joints on the lid
        k.bx(-0.35, 0.35, y - 0.006, y + 0.006, 0.497, 0.504, 'woodd', ink=False)


def barrel(k):
    k.cyl(0.14, 0.05, 0.907, 0.035, 0.035, 0.009, 'woodd', seg=6, ink=False)
    k.cyl(0, 0, 0.42, 0.312, 0.312, 0.05, IRON, seg=10, ink=False)


def woodpile(k):
    for y in (-0.3, -0.15, 0.0, 0.15, 0.3):                          # roof boards
        k.bx(-0.99, 0.99, y - 0.012, y + 0.012, 1.307, 1.316, 'roof2', ink=False)
    for x in (-0.98, 0.98):
        for z in (0.4, 0.9):
            bolt(k, x, -0.06, z, '-y', s=0.03)


# ------------------------------------------------------------------------------------------------ gate and hatch
def gate_frame(k, lintel_r):
    """rope wraps on the lintel beside the posts, end grain on the lintel, lamp cages and brackets"""
    for sx in (-1, 1):
        for off in (0.47, 0.58):
            x = sx * 1.82 + sx * off
            r = lintel_r(x) + 0.02
            k.cyl(x - 0.025, 0, 4.0, r, r, 0.05, 'rope', seg=9, ink=False, rot=(0, 90, 0))
        xe = 2.45 * sx
        k.cyl(xe - 0.006 if sx < 0 else xe - 0.003, 0, 4.0, 0.2, 0.2, 0.009, 'heart', seg=9, ink=False, rot=(0, 90, 0))
        c = sx * 1.82
        k.bx(c - 0.14, c + 0.14, -0.44, -0.28, 2.34, 2.403, IRON, ink=False)
        cage(k, c - 0.12, c + 0.12, -0.42, -0.3, 2.4, 2.75)


def shutter(k):
    for i in range(0, 10, 2):
        x = -1.5 + (i + 0.5) * 0.3
        for z in (1.28, 2.58):
            bolt(k, x, -0.2, z, '-y', s=0.04)


def hatch(k):
    for y in (-0.4, 0.0, 0.4):                                       # plank joints and a pull handle
        hx = math.sqrt(0.9 ** 2 - y ** 2)
        k.bx(-hx, hx, y - 0.01, y + 0.01, 0.137, 0.146, IRON, ink=False)
    k.bx(-0.18, 0.18, -0.025, 0.025, 0.17, 0.2, IRON, ink=False)
    for x in (-0.15, 0.15):
        k.bx(x - 0.02, x + 0.02, -0.02, 0.02, 0.132, 0.173, IRON, ink=False)
