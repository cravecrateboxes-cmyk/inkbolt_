"""Per-piece detail passes for kit-mountains (see mtn_detail.py for the shared helpers). Each function takes the
piece's bare Model and adds ink=False detail before the builder calls finish()."""
import math

from mathutils import Matrix

from kit_base import EMBED, PROUD, bolt_row, kick_plate, base_trim, window_frame_depth
from mtn_detail import det, hline, vline, door_leaf, snow_guard, fascia


# ---------------------------------------------------------------------------------------------- log cabin
def cabin(m):
    k = det(m)
    X, Yf, Yb = 2.3, -1.3, 1.9
    fy = Yf - 0.2
    yr, eave, ridge, ov, th = (Yf + Yb) / 2, 2.55, 4.35, 0.45, 0.16
    slope = (ridge - eave) / (yr - Yf)
    ze = eave - slope * ov
    ye_f, ye_b = Yf - ov, Yb + ov
    ang = math.degrees(math.atan(slope))
    # front door: plank joints, strap hinges, kick plate, escutcheon, a lintel board over the frame
    door_leaf(k, -0.43, 0.43, 0.16, 1.93, fy - 0.10, boards=4, kick=0.17)
    k.bx(0.24, 0.32, fy - 0.108, fy - 0.094, 0.92, 1.08, 'gunmetal', ink=False)
    k.bx(-0.66, 0.66, fy - 0.10, fy + 0.05, 2.09, 2.19, 'log2', ink=False)
    # front windows: reveal frame, corbels under the sill, brace bars on the shutters
    for sx in (-1, 1):
        x = sx * 1.35
        window_frame_depth(k, x - 0.36, x + 0.36, 1.12, 1.78, fy - 0.06, 'log2', depth=0.03, t=0.05)
        for dx in (-0.36, 0.36):
            k.bx(x + dx - 0.03, x + dx + 0.03, fy - 0.12, fy + 0.05, 0.88, 0.98, 'log2', ink=False)
        for s2 in (-1, 1):
            cx = x + s2 * 0.6
            for z in (1.2, 1.7):
                k.bx(cx - 0.125, cx + 0.125, fy - 0.045 - 0.011, fy - 0.045 + EMBED, z - 0.025, z + 0.025, 'roof2', ink=False)
    # east window reveal
    k.push(0, 0, 90)
    window_frame_depth(k, 0.04, 0.76, 1.12, 1.78, -(X + 0.26), 'log2', depth=0.03, t=0.05)
    k.pop()
    # roof edges: fascia + drip lip on both eaves, barge boards on both gable ends, snow-guard rails
    fascia(k, -X - 0.38, X + 0.38, ye_f, ze + 0.03, ze + th - 0.01, lip='gunmetal')
    k.push(0, 0, 180)
    fascia(k, -X - 0.38, X + 0.38, -ye_b, ze + 0.03, ze + th - 0.01, lip='gunmetal')
    k.pop()
    zc = (ze + 0.08 + ridge + 0.08) / 2
    L = math.hypot(yr - ye_f, ridge - ze) - 0.1
    for sgn in (-1, 1):
        k.bxr(sgn * (X + 0.38 + 0.012), (ye_f + yr) / 2, zc, 0.03, L, 0.09, 'log2', rot=(ang, 0, 0), ink=False)
        k.bxr(sgn * (X + 0.38 + 0.017), (ye_b + yr) / 2, zc, 0.03, L, 0.09, 'log2', rot=(-ang, 0, 0), ink=False)
    snow_guard(k, ye_f, ze + th + 0.12, slope, -2.45, 2.45)
    snow_guard(k, ye_b, ze + th + 0.12, slope, -2.45, 2.45, back=True)
    # porch deck: board joints and a front edge board
    for i in range(1, 6):
        y = -1.5 - 0.14 * i
        k.bx(-2.345, 2.345, y - 0.006, y + 0.006, 0.135, 0.1445, 'log2', ink=False)
    yd = Yf - 0.62 - 0.42
    k.bx(-2.34, 2.34, yd - 0.02, yd + EMBED, 0.02, 0.125, 'log2', ink=False)
    # chimney: stone courses on the front and west faces of the stack and the shaft above the roof
    cx = -X - 0.42
    for z in (0.55, 1.1, 1.65, 2.2, 2.75):
        hline(k, cx - 0.28, cx + 0.28, z, 0.47, 'stone')
    for z in (3.55, 4.0, 4.45):
        hline(k, cx - 0.22, cx + 0.22, z, 0.6, 'stone2')
    k.push(0, 0, 270)
    for z in (0.55, 1.1, 1.65, 2.2, 2.75):
        hline(k, -1.27, -0.53, z, cx - 0.3, 'stone2')
    for z in (3.55, 4.0, 4.45):
        hline(k, -1.2, -0.6, z, cx - 0.22, 'stone')
    k.pop()


# ---------------------------------------------------------------------------------------------- A-frame chalet
def chalet(m):
    k = det(m)
    y0, ridge = -2.55, 6.3
    fy = y0 + 0.17
    # front door and lintel
    door_leaf(k, -0.41, 0.41, 0.2, 1.96, fy - 0.07, boards=4, kick=0.17)
    k.bx(-0.52, 0.52, fy - 0.07, fy + 0.04, 2.10, 2.17, 'log2', ink=False)
    # glass: reveal frame and a vertical muntin per pane
    for (x, z, w, h) in ((-0.95, 1.1, 0.5, 1.2), (0.95, 1.1, 0.5, 1.2), (-0.4, 3.1, 0.5, 0.9), (0.4, 3.1, 0.5, 0.9), (0.0, 4.35, 0.45, 0.6)):
        window_frame_depth(k, x - w / 2, x + w / 2, z - h / 2, z + h / 2, fy - 0.03, 'log2', depth=0.03, t=0.05)
        k.bx(x - 0.015, x + 0.015, fy - 0.07 - 0.006, fy - 0.07 + EMBED, z - h / 2 + 0.03, z + h / 2 - 0.03, 'log2', ink=False)
    # barge boards along the front roof edge (the second one a few mm forward: they share the apex)
    L = 6.3
    a = math.degrees(math.atan(2.47 / 6.0))
    k.bxr(1.235, y0 - 0.0105, 3.4, 0.14, 0.03, L, 'log2', rot=(0, -a, 0), ink=False)
    k.bxr(-1.235, y0 - 0.0145, 3.4, 0.14, 0.03, L, 'log2', rot=(0, a, 0), ink=False)
    # balcony: edge board and balusters between the mid and top rails
    bz, by, ry = 2.45, -2.55, -2.88
    k.bx(-1.44, 1.44, by - 0.4 - 0.026, by - 0.4 + EMBED, bz - 0.05, bz + 0.05, 'log2', ink=False)
    for lo, hi in ((-1.34, -0.5), (-0.42, 0.42), (0.5, 1.34)):
        for i in range(1, 6):
            x = lo + (hi - lo) * i / 6
            k.bx(x - 0.015, x + 0.015, ry - 0.012, ry + 0.012, bz + 0.5, bz + 0.91, 'log2', ink=False)
    # lantern hoods got no change; ski bindings neither


# ---------------------------------------------------------------------------------------------- fire lookout
def lookout(m):
    k = det(m)
    top = 9.0
    C, zc0, zc1 = 1.18, top + 0.23, top + 2.55
    D = 1.7
    # cab corner boards and plank-course joints on the timber lower wall
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * C - 0.07, sx * C + 0.07, sy * C - 0.07, sy * C + 0.07, zc0 + 0.01, zc1 + 0.01, 'log2', ink=False)
    for ang in (0, 90, 180, 270):
        k.push(0, 0, ang)
        for z in (zc0 + 0.28, zc0 + 0.56):
            hline(k, -C + 0.07, C - 0.07, z, -C, 'log2')
        k.pop()
    # deck rim boards
    for ang in (0, 90, 180, 270):
        k.push(0, 0, ang)
        k.bx(-D + 0.01, D - 0.01, -D - 0.022, -D + EMBED, top + 0.03, top + 0.18, 'log2', ink=False)
        k.pop()
    # stair handrails on the outer side of each flight
    flights = [((-0.95, -0.62, 0.0), (0.85, -0.62, 3.3)), ((0.85, 0.62, 3.3), (-0.95, 0.62, 6.2)), ((-0.95, -0.62, 6.2), (0.7, -0.62, 8.85))]
    for (p0, p1) in flights:
        yo = p0[1] + (-0.365 if p0[1] < 0 else 0.365)
        k.beam((p0[0], yo, p0[2] + 0.98), (p1[0], yo, p1[2] + 0.98), 0.05, 'log2', ink=False)
        for f in (0.12, 0.5, 0.9):
            x = p0[0] + (p1[0] - p0[0]) * f
            z = p0[2] + (p1[2] - p0[2]) * f
            k.bx(x - 0.03, x + 0.03, yo - 0.02, yo + 0.02, z + 0.03, z + 0.99, 'log2', ink=False)


# ---------------------------------------------------------------------------------------------- rope bridge
def ropebridge(m, cat, half, zend, sag):
    k = det(m)
    # two timber stringers under the planks, following the catenary
    xs = [-half + 0.05 + i * (2 * half - 0.1) / 8 for i in range(9)]
    for y in (-0.42, 0.42):
        for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
            yo = y + 0.004 * (i % 2)       # neighbouring segments in planes 4 mm apart
            k.beam((a, yo, cat(a, half, zend, sag) - 0.075), (b, yo, cat(b, half, zend, sag) - 0.075), 0.1, 'log2', ink=False)


# ---------------------------------------------------------------------------------------------- ski lift
def liftline(m, cable_x):
    k = det(m)
    # steel clamp bands on the tapering pole, gusset plates with bolts on the cross-arm
    for z in (1.6, 3.4, 5.2):
        r = 0.3 - 0.1 * (z - 0.24) / 6.31 + 0.02
        k.cyl(0, 0, z - 0.05, r, r, 0.1, 'steel', seg=8, ink=False)
    for sx in (-1, 1):
        x = sx * 0.55
        k.bx(x - 0.22, x + 0.22, -0.13 - 0.01, -0.13 + EMBED, 6.51, 6.69, "steel", ink=False)
        bolt_row(k, x - 0.22, x + 0.22, 6.61, -0.14, 3, 'gunmetal', s=0.04)
    k.push(0, 0, 180)
    for sx in (-1, 1):
        x = sx * 0.55
        k.bx(x - 0.22, x + 0.22, -0.13 - 0.01, -0.13 + EMBED, 6.51, 6.69, "steel", ink=False)
    k.pop()


def liftstation(m):
    k = det(m)
    hx, hy = 0.0, 1.05
    yf = hy - 0.65
    # operator hut: window reveal, skirting, log-course joints, drip-edge fascia round the roof
    window_frame_depth(k, -0.45, 0.45, 1.2, 1.9, yf, 'log2', depth=0.035, t=0.06)
    base_trim(k, -0.7, 0.7, yf, 'log2', h=0.1, d=0.02, z0=0.12)
    for z in (0.45, 0.78, 1.0):
        hline(k, -0.695, 0.695, z, yf, 'log2', t=0.014, d=0.005)
    fascia(k, -0.8, 0.8, hy - 0.75, 2.43, 2.57, c='gunmetal', d=0.02)
    for ang, sw in ((90, 0.75), (270, 0.75)):
        k.push(0, hy, ang)
        fascia(k, -sw, sw, -0.8, 2.43, 2.57, c='gunmetal', d=0.02)
        k.pop()
    # west door: frame, leaf, plank joints, straps, kick plate, knob
    k.bx(-0.735, -0.697, 0.70, 1.40, 0.13, 2.2, 'log2', ink=False)
    k.bx(-0.755, -0.732, 0.76, 1.34, 0.145, 2.14, 'door', ink=False)
    k.push(0, 0, 270)
    door_leaf(k, -1.34, -0.76, 0.145, 2.14, -0.755, boards=3, kick=0.14)
    k.bx(-0.84, -0.78, -0.755 - 0.03, -0.755 + EMBED, 1.0, 1.06, 'steel', ink=False)
    k.pop()
    # loading ramp board joints
    for i in range(1, 7):
        x = 0.4 + 0.2 * i
        k.bx(x - 0.006, x + 0.006, -1.595, -0.405, 0.1375, 0.144, 'log2', ink=False)
    # base plates and bolts under the A-frame legs
    for (x, y) in ((-1.95, 1.6), (1.95, 1.6), (-1.95, -1.45), (1.95, -1.45)):
        k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.117, 0.145, 'steel', ink=False)
        for dx in (-0.16, 0.16):
            for dy in (-0.16, 0.16):
                k.bx(x + dx - 0.02, x + dx + 0.02, y + dy - 0.02, y + dy + 0.02, 0.14, 0.165, 'gunmetal', ink=False)


# ---------------------------------------------------------------------------------------------- gate
def gateframe(m):
    k = det(m)
    for sx in (-1, 1):
        x = sx * 1.72
        for z in (0.62, 1.55, 2.4):
            k.bx(x - 0.27, x + 0.27, -0.25 - 0.01, 0.25 + 0.01, z - 0.035, z + 0.035, 'gunmetal', ink=False)
            bolt_row(k, x - 0.2, x + 0.2, z, -0.26, 2, 'steel', s=0.04)
        k.push(0, 0, 180)
        for z in (0.62, 1.55, 2.4):
            bolt_row(k, x - 0.2, x + 0.2, z, -0.26, 2, 'steel', s=0.04)
        k.pop()
        # mortar courses on the stone plinth, both faces
        for face in (0, 180):
            k.push(0, 0, face)
            hline(k, x - 0.33, x + 0.33, 0.25, -0.31, 'stone2')
            vline(k, x - 0.1, 0.012, 0.238, -0.31, 'stone2', d=0.004)
            vline(k, x + 0.12, 0.262, 0.488, -0.31, 'stone2', d=0.004)
            k.pop()
    # iron collars where the header log crosses the posts
    for x in (-2.2, -1.25, 1.25, 2.2):
        k.cyl(x - 0.04, 0, 3.92, 0.29, 0.29, 0.08, 'gunmetal', seg=8, ink=False, rot=(0, 90, 0))


def gateshutter(m):
    # the shutter is a hull-less flat piece already: bolts on both faces of the two iron straps
    for x in (-0.9, 0.9):
        for i in range(8):
            z = 0.55 + (i + 0.5) * (3.05 - 0.55) / 8
            for s in (-1, 1):
                m.box((x, s * 0.1, z), (0.032, 0.02, 0.032), 'steel', bevel=False)


# ---------------------------------------------------------------------------------------------- trail wall
def palisade(m, blocks=True, bolts=True):
    k = det(m)
    k.push(0, 0, 90)
    if blocks:
        for (x0, x1) in ((-0.49, -0.17), (-0.13, 0.22), (0.26, 0.49)):
            k.bx(x0, x1, -0.25 - 0.012, -0.25 + EMBED, 0.025, 0.17, 'stone', ink=False)
        for (x0, x1) in ((-0.49, -0.09), (-0.05, 0.19), (0.23, 0.49)):
            k.bx(x0, x1, -0.25 - 0.012, -0.25 + EMBED, 0.2, 0.35, 'stone', ink=False)
    if bolts:
        bolt_row(k, -0.5, 0.5, 1.25, -0.23, 3, 'gunmetal', s=0.035)
    k.pop()


# ---------------------------------------------------------------------------------------------- props
def signpost(m):
    k = det(m)
    for z, ang, col, L in ((1.85, 20, 'tangerine', 0.9), (1.5, -35, 'plank', 0.8), (1.15, 160, 'teal', 0.75)):
        mark = 'ink' if col == 'plank' else 'paper'
        m.parent = Matrix.Translation((0, 0, z)) @ Matrix.Rotation(math.radians(ang), 4, 'Z')
        for s in (-1, 1):
            yf = s * 0.025
            for zz, e in ((0.045, L - 0.08), (-0.04, L - 0.28)):
                lo, hi = (yf - 0.004, yf + 0.007) if s > 0 else (yf - 0.007, yf + 0.004)
                k.bx(0.2, e, lo, hi, zz - 0.014, zz + 0.014, mark, ink=False)
            for bx in (0.14,):
                lo, hi = (yf - 0.004, yf + 0.009) if s > 0 else (yf - 0.009, yf + 0.004)
                k.bx(bx - 0.016, bx + 0.016, lo, hi, 0.07 - 0.016, 0.07 + 0.016, 'gunmetal', ink=False)
                k.bx(bx - 0.016, bx + 0.016, lo, hi, -0.07 - 0.016, -0.07 + 0.016, 'gunmetal', ink=False)
        m.parent = Matrix.Identity(4)


def lanternpost(m):
    k = det(m)
    # diagonal brace under the arm, a collar on the post, corner bars and a bottom plate on the lantern
    k.beam((0.05, 0, 1.9), (0.33, 0, 2.26), 0.05, 'log2', ink=False)
    k.bx(-0.09, 0.09, -0.09, 0.09, 1.86, 1.91, 'gunmetal', ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(0.55 + sx * 0.13 - 0.012, 0.55 + sx * 0.13 + 0.012, sy * 0.13 - 0.012, sy * 0.13 + 0.012, 1.64, 1.92, 'gunmetal', ink=False)
    k.bx(0.55 - 0.15, 0.55 + 0.15, -0.15, 0.15, 1.6, 1.635, 'gunmetal', ink=False)


def fence(m):
    k = det(m)
    # rope lashings where the rails meet the post, stones heaped at the post foot
    for z, d in ((0.45, 0.05), (0.88, -0.05)):
        k.bx(-0.38 - 0.09, -0.38 + 0.09, -0.095, 0.095, z - 0.025, z + 0.025, 'rope', ink=False)
    for (x, y, w) in ((-0.38 - 0.14, 0.0, 0.1), (-0.38 + 0.13, -0.06, 0.08), (-0.38 + 0.05, 0.12, 0.09)):
        k.bx(x - w / 2, x + w / 2, y - w / 2, y + w / 2, 0.0, 0.07, 'stone', ink=False)


def crate(m):
    k = det(m)
    for fy in (-1, 1):
        k.push(0, 0, 0 if fy < 0 else 180)
        bolt_row(k, -0.4, 0.4, 0.46, -0.48, 4, 'gunmetal', s=0.026)
        k.pop()
    k.push(0, 0, 90)
    for z in (0.2, 0.72):
        hline(k, -0.44, 0.44, z, -0.46, 'log2', t=0.014, d=0.006)
    k.pop()
    k.push(0, 0, 270)
    for z in (0.2, 0.72):
        hline(k, -0.44, 0.44, z, -0.46, 'log2', t=0.014, d=0.006)
    k.pop()
