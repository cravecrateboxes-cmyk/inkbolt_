"""kit-frontier modelled detail (tactical look plan Stage 11): window casings with sills, drip caps and muntins, door
casings with ledges, braces, strap hinges and latches, shutter straps, corner boards, stone footings, porch post
plinths, caps and knee braces, porch fascia and plank nails, false-front corbels, crown and sign trim, chimney
courses, standing-seam tin ribs, palisade lashings and iron spike caps, gate straps, tower collars, bolts and rafter
tails, barrel hoops, crate corner posts, wagon tyres and hubs, forge brick courses, anvil stump bands, and more.
Every part is ink=False (no outline shell), >= 3 mm proud of what it sits on, embedded 3 mm, horizontal runs inset
5 mm from the piece sides. Colours are palette names the kit already has. Never touches a _COL / _WCOL box."""
import math

from kit_base import EMBED

IRON = 'iron2'
INSET = 0.005


# ------------------------------------------------------------------------------------------------ face helpers
def fb(k, axis, u0, u1, z0, z1, fp, s, d, c, emb=EMBED):
    """a box on a wall face: axis 'x' = the wall runs along X (face plane y = fp), 'y' = along Y (x = fp); s = the
    outward side; the box starts `emb` inside the face and stands `d` proud; u0..u1 runs along the wall"""
    lo, hi = sorted((fp - s * emb, fp + s * d))
    if axis == 'x':
        k.bx(u0, u1, lo, hi, z0, z1, c, ink=False)
    else:
        k.bx(lo, hi, u0, u1, z0, z1, c, ink=False)


def fq(k, axis, u0, u1, z0, z1, fp, s, off, c):
    if axis == 'x':
        k.qy(u0, u1, z0, z1, fp + s * off, s, c)
    else:
        k.qx(u0, u1, z0, z1, fp + s * off, s, c)


def nail(k, axis, u, z, fp, s, c=IRON, w=0.024, d=0.007):
    fb(k, axis, u - w / 2, u + w / 2, z - w / 2, z + w / 2, fp, s, d, c)


def bolt(k, x, y, z, face, c=IRON, s=0.035, p=0.006):
    """a bolt head on a face; `face` = '-y' '+y' '-x' '+x' names the way the face looks; (x, y, z) is on the face"""
    e, h = EMBED, s / 2
    if face == '-y':
        k.bx(x - h, x + h, y - p, y + e, z - h, z + h, c, ink=False)
    elif face == '+y':
        k.bx(x - h, x + h, y - e, y + p, z - h, z + h, c, ink=False)
    elif face == '-x':
        k.bx(x - p, x + e, y - h, y + h, z - h, z + h, c, ink=False)
    else:
        k.bx(x - e, x + p, y - h, y + h, z - h, z + h, c, ink=False)


def collar(k, x, y, z, r, c=IRON, h=0.05, seg=6):
    """an iron band round a post (r = the band's radius, already clear of the post)"""
    k.cyl(x, y, z, r, r, h, c, seg=seg, caps=False, ink=False)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ------------------------------------------------------------------------------------------------ windows and doors
def window_detail(k, axis, pos, s, a, b, z0, z1, T, kind, gd, style, shutters):
    fp = pos + s * T / 2
    cas = 'plankW' if style == 'plank' else 'plank'
    fb(k, axis, a - 0.12, b + 0.12, z0 - 0.07, z0 + 0.004, fp, s, 0.07, 'plank2')                 # sill
    fb(k, axis, a - 0.08, a + 0.004, z0 + 0.004, z1 + 0.074, fp, s, 0.03, cas)                      # casing
    fb(k, axis, b - 0.004, b + 0.08, z0 + 0.004, z1 + 0.074, fp, s, 0.03, cas)
    fb(k, axis, a - 0.11, b + 0.11, z1 + 0.07, z1 + 0.15, fp, s, 0.05, cas, emb=0.006)              # lintel
    if kind == 'win':
        g = pos + s * gd
        for f in (0.25, 0.75):                                                                       # muntins
            u = a + (b - a) * f
            fb(k, axis, u - 0.011, u + 0.011, z0 + 0.004, z1 - 0.004, g, s, 0.018, cas, emb=(0.03 if gd < T / 2 else EMBED))
    if shutters:
        w = (b - a) / 2
        for (ua, ub) in ((a - 0.14 - w, a - 0.14), (b + 0.14, b + 0.14 + w)):
            lo, hi = (ub - 0.34, ub) if ua < a else (ua, ua + 0.34)
            for zc in (z0 + 0.17, z1 - 0.17):
                fb(k, axis, lo, hi, zc - 0.035, zc + 0.035, fp + s * 0.012, s, 0.016, IRON, emb=0.015)


def door_detail(k, axis, pos, s, a, b, z0, z1, T, kind, style):
    fp = pos + s * T / 2
    cas = 'plank2' if style == 'log' else 'plankW'
    fb(k, axis, a - 0.1, a + 0.004, z0 + 0.004, z1 + 0.004, fp, s, 0.04, cas)                               # casing
    fb(k, axis, b - 0.004, b + 0.1, z0 + 0.004, z1 + 0.004, fp, s, 0.04, cas)
    fb(k, axis, a - 0.12, b + 0.12, z1 + 0.004, z1 + 0.13, fp, s, 0.043, cas, emb=0.006)            # lintel
    fb(k, axis, a - 0.15, b + 0.15, z1 + 0.13, z1 + 0.16, fp, s, 0.075, 'plank2', emb=0.009)       # drip cap
    if kind != 'shut':
        return
    fl = fp + s * 0.004                       # the leaf's face
    ledges = (z0 + 0.2, (z0 + z1) / 2, z1 - 0.26)
    for zc in ledges:
        fb(k, axis, a + 0.05, b - 0.05, zc - 0.06, zc + 0.06, fl, s, 0.018, 'plank')
    # diagonal brace between the ledges
    p0, p1 = (a + 0.14, ledges[0]), (b - 0.14, ledges[2])
    d = fl + s * 0.016
    if axis == 'x':
        k.beam((p0[0], d, p0[1]), (p1[0], d, p1[1]), 0.06, 'plank', ink=False)
    else:
        k.beam((d, p0[0], p0[1]), (d, p1[0], p1[1]), 0.06, 'plank', ink=False)
    for zc in (ledges[0], ledges[2]):                                                                # strap hinges
        fb(k, axis, a + 0.03, a + 0.5, zc - 0.035, zc + 0.035, fl, s, 0.034, IRON, emb=0.0065)
        for u in (a + 0.13, a + 0.36):
            nail(k, axis, u, zc, fl + s * 0.034, s, 'iron', w=0.034, d=0.008)
    zh = z0 + 1.0                                                                                    # latch
    fb(k, axis, b - 0.17, b - 0.1, zh - 0.12, zh + 0.12, fl, s, 0.03, IRON, emb=0.0095)
    fb(k, axis, b - 0.155, b - 0.115, zh - 0.02, zh + 0.04, fl + s * 0.03, s, 0.05, 'iron')


# ------------------------------------------------------------------------------------------------ whole buildings
def house_detail(k, W, D, pd, T, FLOOR, style, out, holes, ztop, ff_top, roof, roof_c, walkin, sign, chimney, shutters,
                 yf, yb, porch_xs, ridge):
    x0, x1 = -W / 2, W / 2
    sides = {'f': ('x', yf, x0, x1, -1), 'b': ('x', yb, x0, x1, 1),
             'l': ('y', x0 + T / 2, yf + T / 2, yb - T / 2, -1), 'r': ('y', x1 - T / 2, yf + T / 2, yb - T / 2, 1)}
    trim = 'plankW' if out != 'plankW' else 'plank'
    for key, (axis, pos, u0, u1, s) in sides.items():
        hl = holes.get(key, [])
        for (a, b, z0, z1, kind) in hl:
            if kind in ('win', 'open'):
                window_detail(k, axis, pos, s, a, b, z0, z1, T, kind, 0.01 if walkin else T / 2 + 0.008, style, shutters)
            else:
                door_detail(k, axis, pos, s, a, b, z0, z1, T, kind, style)
        fp = pos + s * T / 2
        fu0, fu1 = (u0, u1) if axis == 'x' else (u0 - T / 2, u1 + T / 2)
        if key != 'f' or pd <= 0.1:                                                                  # stone footing
            fb(k, axis, fu0 + INSET, fu1 - INSET, 0.0, 0.17, fp, s, 0.03, 'stone2', emb=0.0065)
        if style == 'plank':                                                                         # corner boards
            zb = (FLOOR if (key == 'f' and pd > 0.1) else 0.17) + 0.004
            zt = ((ff_top - 0.3) if (key == 'f' and ff_top) else ztop) - 0.006
            if key in ('f', 'b'):
                fb(k, axis, fu0 + INSET, fu0 + 0.125, zb, zt, fp, s, 0.03, trim)
                fb(k, axis, fu1 - 0.125, fu1 - INSET, zb, zt, fp, s, 0.03, trim)
            else:
                fb(k, axis, fu0 + INSET, fu0 + 0.125, zb, zt, fp, s, 0.03, trim)
                fb(k, axis, fu1 - 0.125, fu1 - INSET, zb, zt, fp, s, 0.03, trim)
    py0 = -D / 2
    if pd > 0.1:
        ptop = 2.75
        # porch: front rim board, plank nails, plinths, caps, knee braces, beam bolts, roof fascia
        fb(k, 'x', x0 + 0.05 + INSET, x1 - 0.05 - INSET, 0.03, FLOOR + 0.01, py0, -1, 0.014, 'plank2')
        py1 = yf - T / 2
        n = max(1, int(round((py1 - py0) / 0.5)))
        for i in range(n):
            yc = py0 + (py1 - py0) * (i + 0.5) / n
            for j in range(int((W - 0.6) / 1.5) + 1):
                xn = x0 + 0.3 + j * 1.5
                k.qz(xn - 0.012, xn + 0.012, yc - 0.012, yc + 0.012, FLOOR + 0.007, 1, IRON)
        for x in porch_xs:
            yc = py0 + 0.2
            k.bx(x - 0.13, x + 0.13, py0 + 0.07, py0 + 0.33, FLOOR - 0.003, FLOOR + 0.12, 'stone2', ink=False)
            k.bx(x - 0.13, x + 0.13, py0 + 0.07, py0 + 0.33, ptop - 0.1, ptop + 0.003, 'log2' if style == 'log' else 'plank2', ink=False)
            for sg in (-1, 1):
                xe = x + sg * 0.55
                if x0 + 0.2 < xe < x1 - 0.2:
                    k.beam((x + sg * 0.08, yc, ptop - 0.6), (xe, yc, ptop - 0.005), 0.07, 'plank2' if style == 'plank' else 'log2', ink=False)
            bolt(k, x, py0 + 0.1, ptop + 0.09, '-y', s=0.04)
        fb(k, 'x', x0 - 0.05 + INSET, x1 + 0.05 - INSET, ptop + 0.04, ptop + 0.2, py0 - 0.25, -1, 0.012, 'plank2', emb=-0.003)
    # false front: corbels, crown, belt board, sign trim
    if ff_top:
        fp = yf - T / 2
        xs = [x0 + 0.5 + i * (W - 1.0) / max(1, int(round((W - 1.0) / 1.0))) for i in range(int(round((W - 1.0) / 1.0)) + 1)]
        for x in xs:
            k.bx(x - 0.06, x + 0.06, fp - 0.14, fp - 0.09, ff_top - 0.2, ff_top + 0.003, 'plank2', ink=False)
        k.bx(x0 - 0.12 + INSET, x1 + 0.12 - INSET, fp - 0.185, fp - 0.02, ff_top + 0.157, ff_top + 0.2, 'plank', ink=False)
        zbelt = min(2.75 + 0.75, ff_top - 0.2) + 0.12
        fb(k, 'x', x0 + 0.012, x1 - 0.012, zbelt, zbelt + 0.13, fp, -1, 0.035, trim, emb=0.006)
    if sign:
        word, sz0, sz1 = sign
        sy = yf - T / 2
        ux0, ux1 = x0 + 0.5, x1 - 0.5
        pl = 'plank2'
        k.bx(ux0 + INSET, ux1 - INSET, sy - 0.082, sy - 0.057, sz1 - 0.07, sz1 - 0.003, pl, ink=False)
        k.bx(ux0 + INSET, ux1 - INSET, sy - 0.082, sy - 0.057, sz0 + 0.003, sz0 + 0.07, pl, ink=False)
        k.bx(ux0 + INSET, ux0 + 0.08, sy - 0.082, sy - 0.057, sz0 + 0.07, sz1 - 0.07, pl, ink=False)
        k.bx(ux1 - 0.08, ux1 - INSET, sy - 0.082, sy - 0.057, sz0 + 0.07, sz1 - 0.07, pl, ink=False)
        for x in (ux0 + 0.04, ux1 - 0.04):
            for z in (sz0 + 0.035, sz1 - 0.035):
                bolt(k, x, sy - 0.082, z, '-y', s=0.03)
    # chimney courses
    if chimney:
        cx, cy, ch = chimney
        zlo = FLOOR + 0.1 if walkin else ztop + 0.3
        n = int((ch - zlo) / 0.34)
        for i in range(n):
            z = zlo + 0.17 + i * 0.34
            if not walkin or z > FLOOR + 0.85:
                k.qy(cx - 0.4, cx + 0.4, z - 0.007, z + 0.007, cy - 0.4 - 0.007, -1, 'stone2')
            k.qx(cy - 0.4, cy + 0.4, z - 0.007, z + 0.007, cx - 0.4 - 0.007, -1, 'stone2')
            k.qx(cy - 0.4, cy + 0.4, z - 0.007, z + 0.007, cx + 0.4 + 0.007, 1, 'stone2')
            if not walkin or z > ztop:
                k.qy(cx - 0.4, cx + 0.4, z - 0.007, z + 0.007, cy + 0.4 + 0.007, 1, 'stone2')
        for dx in (-0.2, 0.2):
            k.cyl(cx + dx, cy, ch + 0.12 - 0.003, 0.13, 0.11, 0.26, 'rock2', seg=6, ink=False)
    # standing-seam ribs on tin roofs
    if roof == 'gable_x' and roof_c[0] == 'tin':
        zr = ridge or (ztop + (yb - yf) * 0.5)
        y0, y1 = yf - T / 2, yb + T / 2
        over = 0.35
        cy = (y0 + y1) / 2
        dz = (zr - ztop) / ((y1 - y0) / 2) * over
        ya = y0 - over
        zeave = ztop - dz
        nrib = int((W + 2 * over - 0.6) / 0.9)
        for i in range(nrib + 1):
            x = x0 - over + 0.3 + i * (W + 2 * over - 0.6) / nrib
            for sg in (-1, 1):
                yy0 = (ya if sg < 0 else y1 + over)
                ya_, yb_ = yy0 - sg * 0.03, cy + sg * 0.12
                z_a = zeave + (zr - zeave) * abs(ya_ - yy0) / abs(cy - yy0) + 0.009
                z_b = zeave + (zr - zeave) * abs(yb_ - yy0) / abs(cy - yy0) + 0.009
                k.beam((x, ya_, z_a), (x, yb_, z_b), 0.02, 'tin2', ink=False)


def tin_ribs_shed(k, x0, x1, ylo, yhi, zlo, zhi, every=0.8):
    """standing-seam ribs on a mono-pitch roof slab from ylo (top at zlo) to yhi (top at zhi)"""
    n = int((x1 - x0 - 0.4) / every)
    for i in range(n + 1):
        x = x0 + 0.2 + i * (x1 - x0 - 0.4) / n
        k.beam((x, ylo + 0.03, zlo + 0.009 + (zhi - zlo) * 0.03 / (yhi - ylo)), (x, yhi - 0.03, zhi - (zhi - zlo) * 0.03 / (yhi - ylo) + 0.009), 0.02, 'tin2', ink=False)


def mortar_courses(k, x0, x1, y, z0, z1, s, every=0.17, c='rock2', joints=0.4, stag=True):
    """brick / stone courses on a face looking toward -Y (s -1) or +Y (s +1) at plane y: mortar lines + staggered joints"""
    n = max(1, int((z1 - z0) / every))
    h = (z1 - z0) / n
    for i in range(1, n):
        z = z0 + i * h
        k.qy(x0 + INSET, x1 - INSET, z - 0.006, z + 0.006, y + s * 0.006, s, c)
    for i in range(n):
        off = (joints / 2) if (stag and i % 2) else 0.0
        u = x0 + joints / 2 + off
        while u < x1 - 0.1:
            k.qy(u - 0.006, u + 0.006, z0 + i * h + 0.006, z0 + (i + 1) * h - 0.006, y + s * 0.006, s, c)
            u += joints


def mortar_courses_x(k, y0, y1, x, z0, z1, s, every=0.17, c='rock2', joints=0.4):
    n = max(1, int((z1 - z0) / every))
    h = (z1 - z0) / n
    for i in range(1, n):
        z = z0 + i * h
        k.qx(y0 + INSET, y1 - INSET, z - 0.006, z + 0.006, x + s * 0.006, s, c)
    for i in range(n):
        off = (joints / 2) if (i % 2) else 0.0
        u = y0 + joints / 2 + off
        while u < y1 - 0.1:
            k.qx(u - 0.006, u + 0.006, z0 + i * h + 0.006, z0 + (i + 1) * h - 0.006, x + s * 0.006, s, c)
            u += joints


# ------------------------------------------------------------------------------------------------ palisade, gate, tower
def spike_cap(k, x, y, h, r, seg=5):
    """iron ferrule ring and tip cap on a sharpened stockade log whose shaft ends at h (the cone is 1.6 r tall)"""
    ch = r * 1.6
    def rad(z):
        return r * 0.96 + (0.02 - r * 0.96) * (z - h) / ch
    zr = h + ch * 0.38
    collar(k, x, y, zr, rad(zr) + 0.014, h=0.045, seg=seg)
    zt = h + ch * 0.76
    k.cyl(x, y, zt, rad(zt) + 0.012, 0.012, h + ch + 0.012 - zt, 'iron', seg=seg, ink=False)


def rope_band(k, x, y, z, r, seg=5):
    k.cyl(x, y, z, r + 0.015, r + 0.015, 0.06, 'rope', seg=seg, caps=False, ink=False)


def palisade_rail_bolts(k, a, b, yf, z):
    n = 2 if b - a > 0.5 else 1
    for i in range(n):
        x = a + (b - a) * (i + 0.5) / n
        bolt(k, x, yf, z, '-y', s=0.04)


def gate_frame_detail(k):
    for sx in (-1, 1):
        x = sx * 1.82
        for z in (1.0, 2.35):
            collar(k, x, 0, z, 0.314, h=0.07, seg=8)
        for z in (1.0, 2.35):
            r = 0.314
            bolt(k, x, -r + 0.0, z + 0.035, '-y', s=0.035, p=0.012)
        collar(k, sx * 1.3, 0, 3.62, 0.24 + 0.014, h=0.08, seg=6)
        collar(k, sx * 2.1, 0, 3.62, 0.24 + 0.014, h=0.08, seg=6)
        # stone footing courses
        k.qy(x - 0.36 + INSET, x + 0.36 - INSET, 0.168, 0.182, -0.36 - 0.006, -1, 'stone2')
        k.qx(-0.36 + INSET, 0.36 - INSET, 0.168, 0.182, x - 0.36 - 0.006 if sx < 0 else x + 0.36 + 0.006, sx, 'stone2')
    for y in (-0.7, 0.7):
        k.bx(-2.45 + INSET, 2.45 - INSET, y - 0.014 if y < 0 else y - 0.003, y + 0.003 if y < 0 else y + 0.014, 4.28, 4.45, 'plank2', ink=False)


def gate_shutter_detail(k):
    Hs = 3.05
    for sx in (-1, 1):
        for z in (0.5, 2.6):
            for xb in (0.5, 0.9, 1.3):
                x = sx * xb
                k.bx(x - 0.018, x + 0.018, -0.16 - 0.006, -0.157 + 0.0, z + 0.07, z + 0.11, 'iron', ink=False)
            # hinge eye at the outer edge
            k.cyl(sx * 1.46, -0.15, z, 0.034, 0.034, 0.17, 'iron', seg=6, ink=False)
    # centre bar: brackets
    for z in (0.9, 1.6, 2.3):
        k.bx(-0.09, 0.09, -0.19, -0.172, z - 0.05, z + 0.05, 'iron', ink=False)


def tower_detail(k, Z, py0, py1, y0, legs, ztop_leg):
    for (x, y) in legs:
        for z in (1.95, Z - 0.4):
            collar(k, x, y, z, 0.186, h=0.07, seg=6)
    # bolts through the deck joists' ends, nails into them
    for yj in (py0 + 0.2, py1 - 0.2):
        for sx in (-1, 1):
            bolt(k, sx * 1.5, yj, Z - 0.23, '-x' if sx < 0 else '+x', s=0.04)
        for i in range(10):
            xn = -1.5 + (i + 0.5) * 0.3
            k.qz(xn - 0.013, xn + 0.013, yj - 0.013, yj + 0.013, Z + 0.007, 1, IRON)
    # stringer bolts on the inner faces, handrail post straps
    yE = py0
    for t in (0.22, 0.45, 0.68, 0.88):
        yy = y0 + (yE - y0) * t
        zz = Z * t - 0.13
        bolt(k, -0.62, yy, zz, '+x', s=0.04)
        bolt(k, 0.62, yy, zz, '-x', s=0.04)
    for sx in (-0.7, 0.7):
        for t in (0.15, 0.55, 0.92):
            yy = y0 + (yE - y0) * t
            k.bx(sx - 0.052, sx + 0.052, yy - 0.052, yy + 0.052, Z * t + 0.62, Z * t + 0.69, IRON, ink=False)
    # rafter tails under the eaves (roof ridge along Y, eave edge at x = +-1.8)
    for sx in (-1, 1):
        for i in range(5):
            yy = py0 - 0.1 + i * (py1 - py0 + 0.2) / 4
            xa, xb = sorted((sx * 1.78, sx * 1.62))
            k.bx(xa, xb, yy - 0.05, yy + 0.05, Z + 1.88, Z + 2.04, 'log2', ink=False)


def hitch_detail(k):
    for x in (-1.25, 1.25):
        k.bx(x - 0.13, x + 0.13, -0.13, 0.13, 0.0, 0.09, 'stone2', ink=False)
        k.cyl(x, 0, 1.05 - 0.003, 0.085, 0.05, 0.05, 'logEnd', seg=6, ink=False)
        collar(k, x, 0, 0.93 - 0.0, 0.08 + 0.015, h=0.04, seg=6)
        collar(k, x * 0.84, 0, 1.0 - 0.025, 0.07 + 0.014, h=0.05, seg=6, c='iron')
    for x in (-0.5, 0.4):
        collar(k, x, 0, 1.0 - 0.02, 0.07 + 0.016, h=0.04, seg=6, c='rope')


def fence_detail(k, full=True):
    if full:
        for z in (0.5, 1.15):
            collar(k, 0, 0, z - 0.03, 0.075 * 0.97 + 0.012, h=0.07, seg=6, c='rope')
        k.cyl(0, 0, 1.35 - 0.003, 0.085, 0.04, 0.06, 'logEnd', seg=6, ink=False)


def post_detail(k):
    for z in (0.35, 1.05):
        collar(k, 0, 0, z, 0.085 + 0.012, h=0.06, seg=6, c='rope')
    k.bx(-0.12, 0.12, -0.12, 0.12, 0.0, 0.08, 'stone2', ink=False)


def trough_detail(k):
    for x in (-0.55, 0.55):
        for sg in (-1, 1):
            lo, hi = sorted((sg * 0.347, sg * 0.362))
            k.bx(x - 0.04, x + 0.04, lo, hi, 0.162, 0.688, IRON, ink=False)
    for z in (0.34, 0.52):
        k.qy(-0.9 + INSET, 0.9 - INSET, z - 0.007, z + 0.007, -0.35 - 0.007, -1, 'logD')
        k.qy(-0.9 + INSET, 0.9 - INSET, z - 0.007, z + 0.007, 0.35 + 0.007, 1, 'logD')
        k.qx(-0.35 + INSET, 0.35 - INSET, z - 0.007, z + 0.007, -0.9 - 0.007, -1, 'logD')
        k.qx(-0.35 + INSET, 0.35 - INSET, z - 0.007, z + 0.007, 0.9 + 0.007, 1, 'logD')
    # rim boards round the opening
    k.bx(-0.9 + INSET, 0.9 - INSET, -0.366, -0.27, 0.69, 0.724, 'plank', ink=False)
    k.bx(-0.9 + INSET, 0.9 - INSET, 0.27, 0.366, 0.69, 0.724, 'plank', ink=False)
    k.bx(-0.912, -0.82, -0.27 + INSET, 0.27 - INSET, 0.69, 0.724, 'plank', ink=False)
    k.bx(0.82, 0.912, -0.27 + INSET, 0.27 - INSET, 0.69, 0.724, 'plank', ink=False)


def lamp_detail(k):
    k.bx(-0.15, 0.15, -0.15, 0.15, 0.0, 0.16, 'stone2', ink=False)
    k.bx(-0.16, 0.16, -0.16, 0.16, 2.7 - 0.003, 2.77, 'log', ink=False)
    k.beam((0.0, -0.14, 2.12), (0.0, -0.52, 2.55), 0.045, IRON, ink=False)
    for z in (0.7, 1.5):
        k.bx(-0.132, 0.132, -0.132, 0.132, z, z + 0.05, IRON, ink=False)


def sign_detail(k):
    k.bx(-0.1, 0.1, -0.1, 0.1, 2.5 - 0.003, 2.56, 'log', ink=False)
    k.bx(-0.13, 0.13, -0.13, 0.13, 0.0, 0.14, 'stone2', ink=False)
    for z in (2.15, 1.8, 1.45):
        k.bx(-0.092, 0.092, -0.092, 0.092, z - 0.05, z - 0.02, IRON, ink=False)
        k.bx(-0.092, 0.092, -0.092, 0.092, z + 0.26, z + 0.29, IRON, ink=False)


def sign_board_nails(k):
    for x in (0.115, 1.02):
        k.bx(x - 0.015, x + 0.015, -0.036, -0.027, 0.105, 0.135, IRON, ink=False)
        k.bx(x - 0.015, x + 0.015, 0.027, 0.036, 0.105, 0.135, IRON, ink=False)


def arch_detail(k):
    for sx in (-1, 1):
        x = sx * 5.6
        for z in (4.5, 5.5):
            collar(k, x, 0, z, 0.216, h=0.08, seg=6)
        k.qy(x - 0.3 + INSET, x + 0.3 - INSET, 0.118, 0.132, -0.3 - 0.006, -1, 'stone2')
    # sign board trim and bolts
    k.bx(-3.6 + INSET, 3.6 - INSET, -0.085, -0.057, 3.953, 4.03, 'plank', ink=False)
    k.bx(-3.6 + INSET, 3.6 - INSET, -0.085, -0.057, 4.80, 4.877, 'plank', ink=False)
    k.bx(-3.6 + INSET, -3.51, -0.085, -0.057, 4.03, 4.80, 'plank', ink=False)
    k.bx(3.51, 3.6 - INSET, -0.085, -0.057, 4.03, 4.80, 'plank', ink=False)
    for x in (-3.4, 3.4):
        bolt(k, x, -0.085, 3.99, '-y', s=0.03)
        bolt(k, x, -0.085, 4.84, '-y', s=0.03)


def well_detail(k):
    for z in (0.27, 0.54):
        r = 0.85 - 0.03 * z / 0.8 + 0.012
        k.cyl(0, 0, z - 0.01, r, r, 0.02, 'stone2', seg=10, caps=False, ink=False)
    for sx in (-1, 1):
        k.beam((sx * 0.8, 0, 1.62), (sx * 0.4, 0, 2.2), 0.07, 'log2', ink=False)
        for z in (1.17, 1.8):
            k.bx(sx * 0.8 - 0.082, sx * 0.8 + 0.082, -0.082, 0.082, z, z + 0.05, IRON, ink=False)
    k.cyl(0, 0, 0.93, 0.147 + 0.012, 0.147 + 0.012, 0.04, 'iron', seg=8, caps=False, ink=False)


# ------------------------------------------------------------------------------------------------ props
def barrel_hoops(k, x, y, z, r, h, hoop):
    """two bilge hoops and a lid (rim ring, boards) on a barrel"""
    for f in (0.34, 0.66):
        t = f / 0.5 if f <= 0.5 else (1 - f) / 0.5
        rb = r * (0.88 + 0.12 * t)
        k.cyl(x, y, z + h * f - 0.02, rb + 0.012, rb + 0.012, 0.04, hoop, seg=8, caps=False, ink=False)
    zt = z + h
    k.cyl(x, y, zt - 0.003, r * 0.74, r * 0.74, 0.012, 'plank', seg=8, ink=False)
    k.cyl(x + r * 0.28, y, zt + 0.002, 0.035, 0.035, 0.02, 'logD', seg=5, ink=False)


def crate_detail(k, x, y, z, sx, sy, sz, c2):
    p = 0.05
    for xx, sgx in ((x - sx / 2, -1), (x + sx / 2, 1)):
        for yy, sgy in ((y - sy / 2, -1), (y + sy / 2, 1)):
            xa, xb = sorted((xx - sgx * (p - 0.012), xx + sgx * 0.012))
            ya, yb = sorted((yy - sgy * (p - 0.012), yy + sgy * 0.012))
            k.bx(xa, xb, ya, yb, z + 0.004, z + sz - 0.004, c2, ink=False)
    # lid board seams on top
    for f in (1 / 3, 2 / 3):
        xl = x - sx / 2 + sx * f
        k.qz(xl - 0.006, xl + 0.006, y - sy / 2 + INSET, y + sy / 2 - INSET, z + sz + 0.005, 1, 'logD')


def wheel_extra(k, x, y, z, r, outward):
    """iron tyre (a capless tube round the rim), hub bands and the axle nut"""
    k.cyl(x - 0.055, y, z, r + 0.06, r + 0.06, 0.11, 'iron2', seg=8, rot=(0, 90, 0), caps=False, ink=False)
    k.cyl(x - 0.085, y, z, 0.125, 0.125, 0.03, 'iron', seg=6, rot=(0, 90, 0), caps=False, ink=False)
    k.cyl(x + 0.055, y, z, 0.125, 0.125, 0.03, 'iron', seg=6, rot=(0, 90, 0), caps=False, ink=False)
    k.cyl(x + 0.087 if outward > 0 else x - 0.127, y, z, 0.05, 0.05, 0.04, 'iron', seg=6, rot=(0, 90, 0), ink=False)


def wagon_straps(k):
    for sx in (-1, 1):
        for y in (-1.5, -0.4, 0.7, 1.55):
            xa, xb = sorted((sx * 0.79 - sx * 0.003, sx * 0.79 + sx * 0.012))
            k.bx(xa, xb, y - 0.035, y + 0.035, 1.004, 1.416, 'iron2', ink=False)
    # doubletree end caps and tongue ferrule
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.4 - sx * 0.003, sx * 0.4 + sx * 0.03))
        k.bx(xa, xb, -2.9 - 0.004, -2.82 + 0.004, 0.397, 0.503, 'iron2', ink=False)


def cart_straps(k):
    for sx in (-1, 1):
        for y in (-0.6, 0.0, 0.6):
            xa, xb = sorted((sx * 0.64 - sx * 0.003, sx * 0.64 + sx * 0.012))
            k.bx(xa, xb, y - 0.03, y + 0.03, 0.724, 1.046, 'iron2', ink=False)


def smithy_detail(k, fx0, fx1, fy0, fy1, H, x0, x1, y0, y1):
    # forge brick courses on the front (-Y) and east (+X) faces and the hood stack
    mortar_courses(k, fx0, fx1, fy0, 0.04, 0.85, -1, every=0.16, c='stone2', joints=0.36)
    mortar_courses_x(k, fy0, fy1, fx1, 0.04, 0.85, 1, every=0.16, c='stone2', joints=0.36)
    mortar_courses(k, -2.95, -2.15, 2.6, 2.5, H + 2.2, -1, every=0.22, c='rock2', joints=0.4)
    mortar_courses_x(k, 2.6, 3.3, -2.15, 2.5, H + 2.2, 1, every=0.22, c='rock2', joints=0.35)
    # iron rim round the coal bed and a tuyere pipe into the fire
    k.bx(fx0 + 0.2, fx1 - 0.2, fy0 + 0.15, fy0 + 0.23, 0.9 - 0.003, 0.93, 'iron2', ink=False)
    k.cyl(-2.55, fy0 - 0.1, 0.62, 0.04, 0.04, 0.2, 'iron', seg=6, rot=(-90, 0, 0), ink=False)
    # anvil stump bands and the hardy / pritchel holes
    for z in (0.1, 0.43):
        r = 0.334
        k.cyl(0.6, 0.2, z, r, r, 0.05, 'iron', seg=8, caps=False, ink=False)
    k.qz(0.9, 0.96, 0.17, 0.23, 0.906, 1, 'coal')
    k.qz(0.2, 0.25, 0.17, 0.23, 0.906, 1, 'coal')
    # quench tub hoops
    for z in (0.12, 0.45):
        r = 0.474
        k.cyl(1.9, 1.6, z, r, r, 0.045, 'iron', seg=8, caps=False, ink=False)
    # front beam bolts and post straps
    for i in range(8):
        xb = x0 + 0.5 + i * (x1 - x0 - 1.0) / 7
        if abs(xb) > 1.2:
            bolt(k, xb, y0 + 0.02, H + 0.11, '-y', s=0.04)
    for (x, y) in ((x0 + 0.15, y0 + 0.15), (0.0, y0 + 0.15), (x1 - 0.15, y0 + 0.15), (x1 - 0.15, 0.0), (x1 - 0.15, y1 - 0.35)):
        k.bx(x - 0.146, x + 0.146, y - 0.146, y + 0.146, H - 0.26, H - 0.2, 'iron2', ink=False)
    # name board trim
    sb = y0 + 0.02 - 0.04
    k.bx(-1.1 + INSET, 1.1 - INSET, sb - 0.02, sb + 0.003, H + 0.15, H + 0.2 - 0.003, 'plank', ink=False)
    k.bx(-1.1 + INSET, 1.1 - INSET, sb - 0.02, sb + 0.003, H - 0.55 + 0.003, H - 0.5, 'plank', ink=False)
    # corrugation-free standing seams on the tin roof
    tin_ribs_shed(k, x0 - 0.3, x1 + 0.3, y0 - 0.45, y1 + 0.3, H + 0.2, H + 1.4)


def stable_detail(k, x0, x1, y0, y1, H):
    for x in (-4.85, -2.5, 0.0, 2.5, 4.85):
        k.bx(x - 0.145, x + 0.145, y0 + 0.02, y0 + 0.32, 0.0, 0.1, 'stone2', ink=False)
        k.bx(x - 0.145, x + 0.145, y0 + 0.025, y0 + 0.325, H - 0.26, H - 0.2, 'iron2', ink=False)
    for x in (-2.5, 0.0, 2.5):
        k.bx(x - 0.06, x + 0.06, y0 + 1.0 + INSET, y1 - 0.2 - INSET, 1.4 - 0.003, 1.44, 'log2', ink=False)
        for y in (y0 + 1.5, y0 + 2.2):
            bolt(k, x - 0.04, y, 1.12, '-x', s=0.03)
            bolt(k, x + 0.04, y, 1.12, '+x', s=0.03)
    for i in range(8):
        bolt(k, x0 + 0.5 + i * (x1 - x0 - 1.0) / 7, y0 + 0.05, H + 0.1, '-y', s=0.04)
