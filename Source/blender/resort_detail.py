"""kit-resort modelled detail (tactical look plan Stage 11): thatch eave rolls and hip ties, post collars and base plates,
beam brackets and bolts, brass bar rails and counter edge bands, pool coping joints, ladder and skimmer grilles, lounger
wheels and hinges, umbrella collars, torch bindings, sign fixings, window frames. Every part is ink=False (no outline
shell), >= 3 mm proud, embedded 3 mm, horizontal runs inset 5 mm from the piece sides. Called from the piece builders
in rs_build.py just before their collision boxes; nothing here moves or renames an existing shape and no collision
box is touched."""
import math

from kit_base import EMBED, PROUD, window_frame_depth


def ring(k, x, y, z, r, h, c='rope', seg=6, rot=(0, 0, 0)):
    """open tube (no caps, so nothing lies on the ground or deck it starts at) round a pole of radius < r"""
    k.cyl(x, y, z, r, r, h, c, seg=seg, caps=False, ink=False, rot=rot)


def screw(k, x, z, yf, sgn=-1, c='metal2', s=0.026):
    """a bolt head on a face at y = yf that looks toward -Y (sgn -1) or +Y (sgn +1)"""
    if sgn < 0:
        k.bx(x - s / 2, x + s / 2, yf - PROUD - 0.006, yf + EMBED, z - s / 2, z + s / 2, c, ink=False)
    else:
        k.bx(x - s / 2, x + s / 2, yf - EMBED, yf + PROUD + 0.006, z - s / 2, z + s / 2, c, ink=False)


def plate(k, x0, x1, z0, z1, yf, sgn=-1, c='metal2', d=0.008):
    """a steel strap plate on a face at y = yf with a bolt near each end"""
    if sgn < 0:
        k.bx(x0, x1, yf - d, yf + EMBED, z0, z1, c, ink=False)
    else:
        k.bx(x0, x1, yf - EMBED, yf + d, z0, z1, c, ink=False)
    for x in (x0 + 0.06, x1 - 0.06):
        screw(k, x, (z0 + z1) / 2, yf + sgn * d, sgn, c='metal', s=0.022)


def strip_y(k, x0, x1, z0, z1, yf, sgn, c, d=0.006):
    """a flat strip on a face at y = yf (looks toward -Y for sgn -1)"""
    if sgn < 0:
        k.bx(x0, x1, yf - d, yf + EMBED, z0, z1, c, ink=False)
    else:
        k.bx(x0, x1, yf - EMBED, yf + d, z0, z1, c, ink=False)


# ------------------------------------------------------------------------------------------------ thatch roofs
def eave_roll(k, x0, x1, y0, y1, ze, th, rx=0.0, zr=0.0, col='thatch2'):
    """a rolled thatch edge on the four eaves of a hip roof, hip beams down the corners, rope ties round the ridge"""
    r = min(0.12, th / 2 + 0.03)
    zc = ze - th * 0.45
    for y in (y0, y1):
        k.cyl(x0 + 0.005, y, zc, r, r, x1 - x0 - 0.01, col, seg=6, rot=(0, 90, 0), ink=False)
    for x in (x0, x1):
        k.cyl(x, y0 + 0.03, zc, r, r, y1 - y0 - 0.06, col, seg=6, rot=(-90, 0, 0), ink=False)
    if rx > 0.05:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = (x0 if sx < 0 else x1, y0 if sy < 0 else y1)
                k.beam((a[0] - sx * 0.02, a[1] - sy * 0.02, ze - 0.02), (cx + sx * rx, cy, zr + 0.01), 0.07, col, ink=False)
        if rx > 1.0:
            for f in (-0.75, 0.0, 0.75):
                x = cx + rx * f
                k.bx(x - 0.025, x + 0.025, cy - 0.097, cy + 0.097, zr + 0.02 - 0.097, zr + 0.02 + 0.097, 'rope', ink=False)


def cone_roll(k, x, y, ze, r, th, seg=8, col='thatch2'):
    """rolled thatch edge round the eave of a cone roof"""
    rr = min(0.11, th / 2 + 0.03)
    zc = ze - th * 0.45
    pts = []
    for i in range(seg):
        a = i / seg * 2 * math.pi + math.pi / seg
        pts.append((x + math.cos(a) * (r - 0.02), y + math.sin(a) * (r - 0.02), zc))
    for i in range(seg):
        q = rr * (1.0 if i % 2 else 0.94)    # neighbouring runs differ in thickness: no coplanar flats
        k.tube(pts[i], pts[(i + 1) % seg], q, q, col, seg=6, ink=False, caps=False)
    for p in pts:
        k.sph(p[0], p[1], p[2], rr * 1.12, col, seg=(5, 3), ink=False)


def finial(k, x, y, z, c='wood2', cb='coral'):
    k.cyl(x, y, z, 0.05, 0.02, 0.22, c, seg=6, ink=False)
    k.sph(x, y, z + 0.24, 0.06, cb, seg=(5, 3), ink=False)


# ------------------------------------------------------------------------------------------------ lobby pavilion
def lobby(k, xs, ys):
    for x in xs:
        for y in ys:   # stone plinth caps, iron collars at the foot and head of every post
            k.bx(x - 0.345, x + 0.345, y - 0.345, y + 0.345, 0.40, 0.455, 'stone2', ink=False)
            ring(k, x, y, 0.452, 0.235, 0.07, 'metal2', seg=8)
            ring(k, x, y, 3.78, 0.228, 0.07, 'metal2', seg=8)
    for y in (ys[0], ys[-1]):   # steel straps and bolts where the posts meet the outer cross beams, both faces
        for sgn in (-1, 1):
            for x in xs:
                plate(k, x - 0.26, x + 0.26, 4.30, 4.55, y + sgn * 0.18, sgn)
    # reception desk: brass inlay along the stone top's front edge, kick plate, brass foot rail on brackets
    k.bx(-5.695, -1.305, 2.42 - 0.004, 2.42 + EMBED, 1.075, 1.095, 'amber', ink=False)
    k.bx(-5.595, -1.405, 2.5 - 0.012, 2.5 + EMBED, 0.07, 0.17, 'metal2', ink=False)
    k.cyl(-5.5, 2.33, 0.3, 0.025, 0.025, 4.0, 'amber', seg=6, rot=(0, 90, 0), ink=False)
    for x in (-5.5, -3.925, -1.5):
        k.bx(x - 0.02, x + 0.02, 2.33, 2.5 + EMBED, 0.27, 0.33, 'amber', ink=False)
    # brass trim round the rug
    for (x0, x1, y0, y1) in ((-2.465, 2.465, -3.065, -3.035), (-2.465, 2.465, -0.765, -0.735),
                             (-2.465, -2.435, -3.035, -0.765), (2.435, 2.465, -3.035, -0.765)):
        k.qz(x0, x1, y0, y1, 0.0735, 1, 'amber')
    # hanging sign: frame strips and corner bolts on its front, eyebolts on the beam
    yf = -4.66
    k.bx(-1.795, 1.795, yf - 0.02, yf + EMBED, 4.145, 4.195, 'wood2', ink=False)
    k.bx(-1.795, 1.795, yf - 0.02, yf + EMBED, 3.454, 3.5, 'wood2', ink=False)
    k.bx(-1.795, -1.75, yf - 0.02, yf + EMBED, 3.5, 4.145, 'wood2', ink=False)
    k.bx(1.75, 1.795, yf - 0.02, yf + EMBED, 3.5, 4.145, 'wood2', ink=False)
    for x in (-1.775, 1.775):
        for z in (3.477, 4.17):
            screw(k, x, z, yf - 0.02, -1, c='metal', s=0.022)


# ------------------------------------------------------------------------------------------------ pool
def edge_y(pts, x, sign):
    """y where the closed outline `pts` crosses the vertical line `x` on the + (sign 1) or - (sign -1) side"""
    best = None
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            y = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
            if y * sign > 0 and (best is None or abs(y) > abs(best)):
                best = y
    return best


def pool_joints(k, outer, inner):
    """coping joints: a thin raised grout line across every coping stone at its seam"""
    n = len(outer)
    for i in range(n):
        a, d = outer[i], inner[i]
        L = math.hypot(d[0] - a[0], d[1] - a[1])
        ux, uy = (d[0] - a[0]) / L, (d[1] - a[1]) / L
        px, py = -uy * 0.007, ux * 0.007
        p0 = (a[0] + ux * 0.02, a[1] + uy * 0.02)
        p1 = (d[0] - ux * 0.02, d[1] - uy * 0.02)
        k.poly([(p0[0] - px, p0[1] - py, 0.1335), (p1[0] - px, p1[1] - py, 0.1335),
                (p1[0] + px, p1[1] + py, 0.1335), (p0[0] + px, p0[1] + py, 0.1335)], 'stone2', (0, 0, 1))


def pool_ladder(k, outer, inner, x, sign):
    """a steel pool ladder: flanges on the coping, handrails arching over the edge, rungs down to the water"""
    yo, yi = edge_y(outer, x, sign), edge_y(inner, x, sign)
    ym = (yo + yi) / 2
    d = -sign                                  # toward the pool centre
    yin = yi + d * 0.22
    for xx in (x - 0.22, x + 0.22):
        k.cyl(xx, ym, 0.127, 0.06, 0.06, 0.016, 'metal', seg=6, ink=False)      # flange
        k.cyl(xx, ym, 0.14, 0.03, 0.03, 0.03, 'metal2', seg=6, ink=False)       # escutcheon
        k.cyl(xx, ym, 0.17, 0.022, 0.022, 0.66, 'metal', seg=5, ink=False)
        k.tube((xx, ym, 0.82), (xx, ym + d * 0.12, 0.93), 0.03, 0.03, 'metal', seg=5, ink=False, caps=False)
        k.tube((xx, ym + d * 0.12, 0.93), (xx, yin - d * 0.12, 0.93), 0.022, 0.022, 'metal', seg=5, ink=False, caps=False)
        k.tube((xx, yin - d * 0.12, 0.93), (xx, yin, 0.82), 0.03, 0.03, 'metal', seg=5, ink=False, caps=False)
        k.cyl(xx, yin, 0.08, 0.022, 0.022, 0.74, 'metal', seg=5, ink=False)
    for z in (0.3, 0.5, 0.7):
        k.bx(x - 0.22, x + 0.22, yin - 0.025, yin + 0.025, z - 0.014, z + 0.014, 'metal2', ink=False)


def grille(k, x, y, w=0.4, d=0.16, z=0.13):
    """a skimmer / drain grille set in the coping: frame plate and slats"""
    k.bx(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z - EMBED, z + 0.006, 'metal2', ink=False)
    n = 6
    for i in range(n):
        xx = x - w / 2 + 0.035 + (w - 0.07) * (i + 0.5) / n
        k.bx(xx - 0.01, xx + 0.01, y - d / 2 + 0.025, y + d / 2 - 0.025, z + 0.003, z + 0.011, 'metal', ink=False)


def bar_trim(k, bx, H):
    """swim-up bar: brass strips along the counter tops' outer edge, brass foot rails on brackets, kick plates"""
    zt = 1.13
    k.bx(bx - 1.3, bx + 1.3, -H - 0.04, -H - 0.01, zt - EMBED, zt + 0.006, 'amber', ink=False)
    k.bx(bx - 1.3, bx + 1.3, H + 0.01, H + 0.04, zt - EMBED, zt + 0.006, 'amber', ink=False)
    k.bx(bx - H - 0.04, bx - H - 0.01, -0.85, 0.85, zt - EMBED, zt + 0.006, 'amber', ink=False)
    k.cyl(bx - 1.3, -H - 0.12, 0.26, 0.025, 0.025, 2.6, 'amber', seg=6, rot=(0, 90, 0), ink=False)
    k.cyl(bx - 1.3, H + 0.12, 0.26, 0.025, 0.025, 2.6, 'amber', seg=6, rot=(0, 90, 0), ink=False)
    k.cyl(bx - H - 0.12, -0.8, 0.26, 0.025, 0.025, 1.6, 'amber', seg=6, rot=(-90, 0, 0), ink=False)
    for x in (bx - 1.3, bx + 1.3):
        k.bx(x - 0.02, x + 0.02, -H - 0.12, -H + EMBED, 0.22, 0.26, 'amber', ink=False)
        k.bx(x - 0.02, x + 0.02, H - EMBED, H + 0.12, 0.22, 0.26, 'amber', ink=False)
    for y in (-0.8, 0.8):
        k.bx(bx - H - 0.12, bx - H + EMBED, y - 0.02, y + 0.02, 0.22, 0.26, 'amber', ink=False)
    k.bx(bx - H + 0.005, bx + H - 0.005, -H - 0.012, -H + EMBED, 0.004, 0.14, 'metal2', ink=False)
    k.bx(bx - H + 0.005, bx + H - 0.005, H - EMBED, H + 0.012, 0.004, 0.14, 'metal2', ink=False)
    k.bx(bx - H - 0.012, bx - H + EMBED, -0.995, 0.995, 0.004, 0.14, 'metal2', ink=False)
    for sx in (-1, 1):   # sign board corner bolts
        for z in (2.79, 3.11):
            screw(k, bx + sx * 1.44, z, -H - 0.12, -1, c='metal', s=0.022)


def bamboo_post_fit(k, x, y, z0, h, r):
    """base plate and bindings on a bamboo post"""
    k.cyl(x, y, z0 - EMBED, r + 0.06, r + 0.06, 0.02, 'metal2', seg=8, ink=False)
    ring(k, x, y, z0 + 0.02, r + 0.015, 0.05, 'rope')
    ring(k, x, y, z0 + h - 0.45, r + 0.015, 0.06, 'rope')
    ring(k, x, y, z0 + h - 0.38, r + 0.012, 0.02, 'amber')


# ------------------------------------------------------------------------------------------------ cabana
def cabana(k):
    # deck fascia boards on all four edges, collars on the posts, finial on the canopy
    k.bx(-1.845, 1.845, -1.862, -1.85 + EMBED, 0.02, 0.14, 'wood2', ink=False)
    k.bx(-1.845, 1.845, 1.85 - EMBED, 1.862, 0.02, 0.14, 'wood2', ink=False)
    k.bx(1.85 - EMBED, 1.862, -1.843, 1.843, 0.02, 0.14, 'wood2', ink=False)
    k.bx(-1.862, -1.85 + EMBED, -1.843, 1.843, 0.02, 0.14, 'wood2', ink=False)
    for x in (-1.68, 1.68):
        for y in (-1.68, 1.68):
            ring(k, x, y, 0.147, 0.1, 0.05, 'metal2', seg=6)
            ring(k, x, y, 2.5, 0.095, 0.06, 'metal2', seg=6)
    finial(k, 0, 0, 3.73)


# ------------------------------------------------------------------------------------------------ loungers, umbrella, torch
def lounger(k):
    for sx in (-1, 1):
        # wheels at the foot end, rubber feet at the head end
        x0 = 0.345 if sx > 0 else -0.375
        k.cyl(x0, -0.8, 0.055, 0.055, 0.055, 0.03, 'tire', seg=8, rot=(0, 90, 0), ink=False)
        ring(k, sx * 0.32, 0.5, 0.0, 0.055, 0.04, 'tire', seg=6)
        # frame bolts along the side rail and the backrest hinge
        for y in (-0.75, -0.25, 0.4):
            xf = sx * 0.34
            k.bx(min(xf - sx * 0.003, xf + sx * 0.0065), max(xf - sx * 0.003, xf + sx * 0.0065), y - 0.011, y + 0.011, 0.319, 0.341, 'metal2', ink=False)
        xf = sx * 0.34
        k.bx(min(xf - sx * 0.003, xf + sx * 0.012), max(xf - sx * 0.003, xf + sx * 0.012), 0.46, 0.6, 0.31, 0.4, 'metal2', ink=False)


def umbrella(k):
    k.cyl(0, 0, 0.003, 0.2, 0.2, 0.03, 'metal2', seg=8, ink=False)            # base plate
    for x in (-0.14, 0.14):
        for y in (-0.14, 0.14):
            k.bx(x - 0.011, x + 0.011, y - 0.011, y + 0.011, 0.03, 0.04, 'metal', ink=False)
    ring(k, 0, 0, 0.033, 0.062, 0.12, 'metal2')                                 # pole socket
    ring(k, 0, 0, 1.45, 0.056, 0.2, 'amber')                                     # height sleeve
    ring(k, 0, 0, 1.43, 0.062, 0.02, 'metal2')
    ring(k, 0, 0, 2.02, 0.062, 0.08, 'metal2')                                   # collar under the canopy
    ring(k, 0.35, -0.3, 0.505, 0.25, 0.03, 'wood2', seg=8)                       # side table rim
    k.cyl(0.35, -0.3, 0.003, 0.09, 0.09, 0.02, 'wood2', seg=8, ink=False)       # and foot pad


def torch(k):
    ring(k, 0, 0, 0.0, 0.068, 0.14, 'metal2')                                    # ground ferrule
    ring(k, 0, 0, 0.14, 0.066, 0.025, 'amber')
    for z in (1.69, 1.74):                                                       # rope lashing under the cup
        ring(k, 0, 0, z, 0.058, 0.03, 'rope')
    ring(k, 0, 0, 1.86, 0.118, 0.035, 'rope')
    ring(k, 0, 0, 2.045, 0.162, 0.03, 'metal2')                                  # cup rim band


def signpost(k):
    ring(k, 0, 0, 0.0, 0.1, 0.12, 'metal2')
    ring(k, 0, 0, 0.12, 0.098, 0.025, 'amber')
    k.cyl(0, 0, 2.397, 0.085, 0.03, 0.08, 'amber', seg=6, ink=False)


def board_screws(k, z):
    """bolts through a signpost board into the pole, both faces (called inside the board's push frame)"""
    for x in (0.16, 1.02):
        screw(k, x, z + 0.035, -0.04, -1, c='metal', s=0.022)
        screw(k, x, z + 0.035, 0.04, 1, c='metal', s=0.022)


# ------------------------------------------------------------------------------------------------ villas
def villa_window(k, sx, hx):
    """frame with depth round the side window, with a sill; drawn on the outside of the +/-X wall"""
    k.push(sx * hx, 0, 90 * sx)
    xc, zc, hw, hh = 0.1 * sx, 1.65, 0.7, 0.55
    yf = -0.004
    yb = yf + 0.009
    window_frame_depth(k, xc - hw, xc + hw, zc - hh, zc + hh, yb, 'wood2', depth=0.059, t=0.05)
    k.bx(xc - hw - 0.08, xc + hw + 0.08, yf - 0.09, yb + 0.007, zc - hh - 0.075, zc - hh - 0.04, 'wood2', ink=False)
    k.pop()


def villa_front(k, hx, hy, fl, wh):
    for sx in (-1, 1):
        x0, x1 = (hx - 0.55, hx - 0.05) if sx > 0 else (-hx + 0.05, -hx + 0.55)
        plate(k, x0, x1, wh + 0.04, wh + 0.26, -hy, -1)       # strap on the front beam
        a, b = (hx - 0.215, hx - 0.005) if sx > 0 else (-hx + 0.005, -hx + 0.215)
        plate(k, a, b, fl + 0.004, fl + 0.3, -hy, -1)         # kick plate at the post foot


# ------------------------------------------------------------------------------------------------ small things
def towelhut(k):
    k.bx(-1.495, 1.495, -1.006, -1.0 + EMBED, 1.065, 1.085, 'amber', ink=False)
    k.bx(-1.445, 1.445, -0.962, -0.95 + EMBED, 0.004, 0.13, 'metal2', ink=False)
    for sx in (-1, 1):
        ring(k, sx * 1.35, -0.85, 1.117, 0.075, 0.05, 'metal2')
        ring(k, sx * 1.35, -0.85, 2.15, 0.072, 0.05, 'metal2')


def crate_nails(k, s):
    for x in (-s * 0.75, 0.0, s * 0.75):
        screw(k, x, s, -(s + 0.004), -1, s=0.024)
        screw(k, x, s, s + 0.004, 1, s=0.024)


def cart(k):
    k.bx(-0.5, 0.5, -1.42, -1.3 + EMBED, 0.34, 0.42, 'metal', ink=False)     # front bumper
    k.bx(-0.5, 0.5, 1.25 - EMBED, 1.31, 0.34, 0.42, 'metal', ink=False)      # rear bumper


def gate(k):
    for sx in (-1, 1):
        x = sx * 1.85
        k.bx(x - 0.345, x + 0.345, -0.345, 0.345, 0.46, 0.505, 'stone2', ink=False)
        ring(k, x, 0, 0.502, 0.255, 0.07, 'metal2', seg=8)
        ring(k, x, 0, 3.9, 0.225, 0.07, 'metal2', seg=8)
        x0, x1 = (1.55, 2.15) if sx > 0 else (-2.15, -1.55)
        plate(k, x0, x1, 4.12, 4.38, -0.25, -1)
        plate(k, x0, x1, 4.12, 4.38, 0.25, 1)
        k.bx(x - 0.03, x + 0.03, -0.30, -0.19, 2.72, 2.78, 'metal2', ink=False)   # lamp arm
        ring(k, x, -0.38, 2.57, 0.13, 0.05, 'metal2')
        k.cyl(x, -0.38, 2.877, 0.115, 0.03, 0.09, 'metal2', seg=6, ink=False)
    for sx in (-1, 1):   # sign board corner screws, both faces
        for z in (3.5, 4.0):
            screw(k, sx * 1.5, z, -0.33, -1, c='metal', s=0.022)
            screw(k, sx * 1.5, z, 0.33, 1, c='metal', s=0.022)


def hatch(k):
    ring(k, 0, 0, 0.12, 0.97, 0.035, 'metal2', seg=16)
    k.bx(-0.9, 0.9, -0.05, 0.05, 0.137, 0.155, 'metal2', ink=False)
    k.bx(-0.05, 0.05, -0.9, 0.9, 0.134, 0.16, 'metal2', ink=False)
    k.cyl(0, 0, 0.131, 0.14, 0.14, 0.047, 'amber', seg=8, ink=False)


def deckpost(k):
    k.bx(-0.17, 0.17, -0.17, 0.17, 0.3 - EMBED, 0.312, 'metal2', ink=False)
    k.bx(-0.162, 0.162, -0.162, 0.162, 0.312, 0.55, 'metal2', ink=False)
    k.bx(-0.162, 0.162, -0.162, 0.162, 6.85, 7.1, 'metal2', ink=False)
    for z in (0.43, 6.975):
        screw(k, -0.07, z, -0.162, -1)
        screw(k, 0.07, z, -0.162, -1)


def rail(k, post, ends=True):
    """bamboo rail: lashings at the ends and at the post, iron foot ring"""
    if ends:
        for y in ((-0.495, 0.455) if post else (-0.495,)):
            k.cyl(0, y, 1.0, 0.068, 0.068, 0.04, 'rope', seg=5, rot=(-90, 0, 0), caps=False, ink=False)
    if post:
        k.cyl(0, -0.03, 1.0, 0.068, 0.068, 0.06, 'rope', seg=5, rot=(-90, 0, 0), caps=False, ink=False)
        ring(k, 0, 0, 0.0, 0.06, 0.07, 'metal2', seg=4)


def bridge_nails(k):
    for i in range(6):
        x0 = -1.5 + i * 0.5 + 0.015
        for x in (x0 + 0.07, x0 + 0.40):
            for y in (-0.78, 0.78):
                k.bx(x - 0.011, x + 0.011, y - 0.011, y + 0.011, -EMBED, 0.0065, 'metal2', ink=False)
