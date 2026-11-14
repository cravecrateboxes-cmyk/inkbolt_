"""kit-garden modelled detail (tactical look plan Stage 11): the fixings a park's furniture and playground really have.

Fences: post caps, rail brackets, nail heads; benches and picnic tables: bolt heads, end-grain caps, foot plates;
lamp posts: base plate, hand-hole door, collars, finial; bins: base ring, sign plate; the roller gate: handle brackets,
hasp and padlock, bottom-rail bolts; play equipment: base plates, clamps, chain links, deck rail bolts, pivot bolts;
the gazebo: post plinths and capitals, rafter tails, hip rolls; the shed: hinges, handle, corner boards, fascia, butt
bands. Same rules as every detail pass: every part is ink=False (no outline shell), stands >= 3 mm proud, is embedded
3 mm, and horizontal runs stop 5 mm short of the piece sides. Only shapes are added: nothing here changes a piece's
origin, footprint, collision boxes or the parts already drawn.
"""
import math

OUT = 0.009     # how far a bolt head stands out of its face
EMB = 0.003     # how far it sinks into it


def bolt(k, x, y, z, face, c='metal2', s=0.024, out=OUT):
    """A square bolt head / screw on a face of a part. face: '+x' '-x' '+y' '-y' '+z' (the face's outward direction)."""
    h = s / 2
    x0, x1, y0, y1, z0, z1 = x - h, x + h, y - h, y + h, z - h, z + h
    if face == '+x':
        x0, x1 = x - EMB, x + out
    elif face == '-x':
        x0, x1 = x - out, x + EMB
    elif face == '+y':
        y0, y1 = y - EMB, y + out
    elif face == '-y':
        y0, y1 = y - out, y + EMB
    else:
        z0, z1 = z - EMB, z + out
    k.bx(x0, x1, y0, y1, z0, z1, c, ink=False)


def cap_end(k, x, y0, y1, z0, z1, side, c='woodD', t=0.006):
    """An end-grain cap on a board end at x (side +1: the +x end)."""
    if side > 0:
        k.bx(x - EMB, x + t - EMB, y0, y1, z0, z1, c, ink=False)
    else:
        k.bx(x - t + EMB, x + EMB, y0, y1, z0, z1, c, ink=False)


def base_plate(k, x, y, r, c='metal', t=0.018, bolts=None, bc='metal2'):
    """A square foot plate (floats 4 mm off the ground: the bottom is never seen) with corner bolts."""
    k.bx(x - r, x + r, y - r, y + r, 0.004, 0.004 + t, c, ink=False)
    if bolts:
        for sx in (-1, 1):
            for sy in (-1, 1):
                bolt(k, x + sx * (r - 0.03), y + sy * (r - 0.03), 0.004 + t, '+z', bc, s=0.026)


# ---------------------------------------------------------------- fences
def picket_detail(k):
    # cap on the post (post x -0.55..-0.45, y +-0.05, top 1.12)
    k.bx(-0.56, -0.44, -0.06, 0.06, 1.117, 1.14, 'paintW', ink=False)
    k.bx(-0.535, -0.465, -0.035, 0.035, 1.14, 1.165, 'metal', ink=False)
    # galvanised rail brackets on the post's front face (y = -0.05), screws in them
    for z in (0.34, 0.79):
        k.bx(-0.54, -0.46, -0.058, -0.047, z - 0.05, z + 0.05, 'metal', ink=False)
        for dz in (-0.03, 0.03):
            bolt(k, -0.5, -0.058, z + dz, '-y', 'metal2', s=0.02, out=0.005)
    # nail heads through the pickets into the rails
    for i in range(4):
        x = -0.32 + i * 0.23
        for z in (0.34, 0.79):
            bolt(k, x, -0.02, z, '-y', 'metal2', s=0.02, out=0.007)
    # ground-spike shoe at the post foot
    k.bx(-0.575, -0.425, -0.075, 0.075, 0.004, 0.06, 'metal2', ink=False)


def bench_detail(k):
    for i in range(3):
        y = -0.24 + i * 0.15
        for s in (-1, 1):
            bolt(k, s * 0.8, y, 0.47, '+z', 'metal2', s=0.026)         # carriage bolts through slats into the end frames
            cap_end(k, s * 0.95, y - 0.05, y + 0.05, 0.425, 0.465, s)  # end-grain caps
    # foot plates under the legs
    for s in (-1, 1):
        x = s * 0.8
        k.bx(x - 0.07, x + 0.07, -0.31, -0.19, 0.004, 0.016, 'metal', ink=False)
        k.bx(x - 0.07, x + 0.07, 0.13, 0.25, 0.004, 0.016, 'metal', ink=False)


def picnic_detail(k):
    # carriage bolts through the table planks into the leg frames, and through the bench boards
    for s in (-1, 1):
        x = s * 0.7
        for i in range(4):
            y = -0.33 + i * 0.22
            bolt(k, x, y, 0.78, '+z', 'metal2', s=0.028, out=0.01)
        for b in (-1, 1):
            for dy in (-0.05, 0.05):
                bolt(k, x, b * 0.62 + dy, 0.47, '+z', 'metal2', s=0.026)
    # end-grain caps on table planks and bench boards
    for s in (-1, 1):
        for i in range(4):
            y = -0.33 + i * 0.22
            cap_end(k, s * 0.95, y - 0.09, y + 0.09, 0.725, 0.775, s)
        for b in (-1, 1):
            cap_end(k, s * 0.95, b * 0.62 - 0.12, b * 0.62 + 0.12, 0.425, 0.465, s)
    # foot pads at the leg ends
    for s in (-1, 1):
        for f in (-1, 1):
            k.bx(s * 0.7 - 0.07, s * 0.7 + 0.07, f * 0.62 - 0.07, f * 0.62 + 0.07, 0.004, 0.02, 'woodD', ink=False)
    # nuts on the brace ends
    for s in (-1, 1):
        for f in (-1, 1):
            bolt(k, s * 0.7 + s * 0.04, f * 0.7, 0.4, '+x' if s > 0 else '-x', 'metal2', s=0.026)


# ---------------------------------------------------------------- lamp posts, bins
def lamp_detail(k):
    base_plate(k, 0, 0, 0.19, 'metal2', bolts=True)
    # hand-hole door in the base (front, -y): works whichever way the 8-sided base is turned
    k.bx(-0.05, 0.05, -0.152, -0.12, 0.08, 0.24, 'metal2', ink=False)
    for dz in (0.1, 0.22):
        bolt(k, 0, -0.152, dz, '-y', 'metal', s=0.02, out=0.006)
    # collars on the pole, a cap ring under the lantern and a finial
    k.cyl(0, 0, 0.296, 0.1, 0.1, 0.05, 'metal2', seg=8, ink=False)
    k.cyl(0, 0, 0.8, 0.085, 0.085, 0.04, 'paintG2', seg=6, ink=False)
    k.cyl(0, 0, 2.25, 0.08, 0.08, 0.04, 'paintG2', seg=6, ink=False)
    k.cyl(0, 0, 2.8, 0.08, 0.08, 0.05, 'metal2', seg=6, ink=False)
    k.sph(0, 0, 3.52, 0.04, 'metal2', seg=(6, 4), ink=False)
    # bolts on the cross-arm
    for s in (-1, 1):
        bolt(k, s * 0.15, -0.03, 2.53, '-y', 'metal2', s=0.02, out=0.006)


def trail_lamp_detail(k):
    k.bx(-0.12, 0.12, -0.52, -0.28, 0.004, 0.024, 'paintG2', ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bolt(k, sx * 0.09, -0.4 + sy * 0.09, 0.024, '+z', 'metal2', s=0.024)
    k.cyl(0, -0.4, 0.4, 0.09, 0.09, 0.05, 'metal2', seg=6, ink=False)
    k.cyl(0, -0.4, 2.3, 0.08, 0.08, 0.04, 'metal2', seg=6, ink=False)


def bin_detail(k):
    k.cyl(0, 0, 0.0, 0.3, 0.3, 0.05, 'metal2', seg=8, ink=False)            # base ring
    k.cyl(0, 0, 0.931, 0.12, 0.12, 0.009, 'ink', seg=8, ink=False)             # the lid's mouth
    k.cyl(0, 0, 0.927, 0.2, 0.2, 0.007, 'metal', seg=8, ink=False)
    # sign plate on the body (front, -y) with two screws and a mark
    k.bx(-0.075, 0.075, -0.275, -0.222, 0.6, 0.76, 'paintW', ink=False)
    k.bx(-0.04, 0.04, -0.281, -0.274, 0.66, 0.70, 'paintG', ink=False)
    for x in (-0.055, 0.055):
        bolt(k, x, -0.275, 0.73, '-y', 'metal2', s=0.016, out=0.005)


# ---------------------------------------------------------------- the roller gate
def gate_detail(k):
    # stone plinths and quoins on the brick piers
    for s in (-1, 1):
        x0, x1 = (1.5, 2.5) if s > 0 else (-2.5, -1.5)
        xo0, xo1 = (x0 + 0.012, x1 + 0.04) if s > 0 else (x0 - 0.04, x1 - 0.012)
        k.bx(xo0, xo1, -0.59, 0.59, 0.004, 0.26, 'stone2', ink=False)
        for cx in (x0, x1):
            ox = 1 if cx == x1 else -1
            for cy in (-0.55, 0.55):
                oy = 1 if cy > 0 else -1
                for i in range(4):
                    z0 = 0.4 + i * 0.8
                    ln = 0.22 if i % 2 == 0 else 0.14
                    # a block wrapping the corner: along y (on the pier's x face) and along x
                    xa, xb = min(cx - ox * ln, cx + ox * 0.012), max(cx - ox * ln, cx + ox * 0.012)
                    ya, yb = (min(cy - oy * 0.1, cy + oy * 0.012), max(cy - oy * 0.1, cy + oy * 0.012))
                    k.bx(xa, xb, ya, yb, z0, z0 + 0.34, 'stone', ink=False)


def shutter_detail(k):
    # pull handle on both faces, on brackets
    for f in (-1, 1):
        yb0, yb1 = (-0.1, -0.067) if f < 0 else (0.067, 0.1)
        for x in (-0.45, 0.45):
            k.bx(x - 0.02, x + 0.02, yb0, yb1, 0.98, 1.08, 'metal2', ink=False)
        k.bx(-0.47, 0.47, (-0.112 if f < 0 else 0.1), (-0.1 if f < 0 else 0.112), 1.01, 1.05, 'metal', ink=False)
    # hasp and padlock on the south face
    k.bx(1.25, 1.35, -0.098, -0.067, 0.55, 0.75, 'metal2', ink=False)
    k.bx(1.26, 1.34, -0.118, -0.098, 0.48, 0.58, 'amber', ink=False)
    # bolts along the bottom rail
    for i in range(5):
        x = -1.2 + i * 0.6
        bolt(k, x, -0.07, 0.1, '-y', 'metal2', s=0.03, out=0.01)
        bolt(k, x, 0.07, 0.1, '+y', 'metal2', s=0.03, out=0.01)


# ---------------------------------------------------------------- gazebo
def gazebo_detail(k, F, posts, eo):
    for x, y in posts:
        k.cyl(x, y, F - 0.003, 0.13, 0.13, 0.12, 'paintW', seg=6, ink=False)          # plinth
        k.cyl(x, y, F + 0.12, 0.105, 0.105, 0.03, 'metal', seg=6, ink=False)          # a collar above it
        k.cyl(x, y, F + 2.3, 0.125, 0.125, 0.1, 'paintW', seg=6, ink=False)           # capital under the eave
    # rafter tails: one at every roof corner, one mid-face
    for i in range(8):
        a = (i + 0.5) / 8 * 2 * math.pi
        ca, sa = math.cos(a), math.sin(a)
        r = 2.76
        k.bxr(ca * r, sa * r, F + 2.466, 0.38, 0.07, 0.074, 'paintW', rot=(0, 0, math.degrees(a)), ink=False)
        b = i / 8 * 2 * math.pi
        rm = 2.56
        k.bxr(math.cos(b) * rm, math.sin(b) * rm, F + 2.466, 0.32, 0.06, 0.074, 'woodD', rot=(0, 0, math.degrees(b)), ink=False)
    # hip rolls along the roof edges
    for x, y in eo:
        k.beam((x * 0.98, y * 0.98, F + 2.53), (x * 0.03, y * 0.03, F + 4.07), 0.06, 'paintW', ink=False)
    k.cyl(0, 0, F + 3.94, 0.17, 0.17, 0.07, 'metal', seg=8, ink=False)               # finial collar


# ---------------------------------------------------------------- shed
def shed_detail(k):
    # corner boards
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 1.55, sy * 1.2
            xa, xb = (cx - 0.07, cx + 0.035) if sx > 0 else (cx - 0.035, cx + 0.07)
            ya, yb = (cy - 0.07, cy + 0.035) if sy > 0 else (cy - 0.035, cy + 0.07)
            k.bx(xa, xb, ya, yb, 0.004, 2.15, 'paintW', ink=False)
    # strap hinges and a handle on the door (front y = -1.2; the door's panels stand 6-12 mm proud)
    for z in (0.35, 1.55):
        k.bx(-1.07, -0.78, -1.222, -1.203, z - 0.035, z + 0.035, 'gunmetal', ink=False)
        for x in (-1.0, -0.88):
            bolt(k, x, -1.222, z, '-y', 'metal', s=0.026, out=0.007)
    k.bx(-0.5, -0.44, -1.232, -1.203, 0.92, 1.12, 'gunmetal', ink=False)
    k.bx(-0.5, -0.44, -1.252, -1.232, 0.9, 1.0, 'metal', ink=False)
    # window head, fascia board on the roof edge, water-butt bands and tap
    k.bx(0.15, 1.25, -1.236, -1.203, 1.82, 1.86, 'paintW', ink=False)
    k.bx(-1.795, 1.795, -1.47, -1.448, 2.135, 2.257, 'paintW', ink=False)
    k.cyl(1.85, 0.6, 0.2, 0.33, 0.33, 0.035, 'metal2', seg=8, ink=False)
    k.cyl(1.85, 0.6, 0.68, 0.33, 0.33, 0.035, 'metal2', seg=8, ink=False)
    k.bx(1.83, 1.87, 0.255, 0.31, 0.24, 0.3, 'metal', ink=False)


# ---------------------------------------------------------------- playground equipment
def swings_detail(k):
    for s in (-1, 1):
        x = s * 1.8
        for f in (-1, 1):
            base_plate(k, x, f * 0.9, 0.11, 'metal', bolts=False)
        for yb in (-0.42, 0.42):
            for side in (-1, 1):
                bolt(k, x + side * 0.055, yb, 0.94, '+x' if side > 0 else '-x', 'metal2', s=0.03)
        # apex clamp over the top bar
        k.bx(x - 0.07, x + 0.07, -0.09, 0.09, 2.36, 2.54, 'metal', ink=False)
        for side in (-1, 1):
            bolt(k, x, side * 0.09, 2.45, '+y' if side > 0 else '-y', 'metal2', s=0.026)
    for x, c in ((-0.7, 'plR'), (0.7, 'plB')):
        for dx in (-0.22, 0.22):
            cx = x + dx
            k.bx(cx - 0.035, cx + 0.035, -0.085, 0.085, 2.36, 2.52, 'metal', ink=False)       # hanger shackle
            for j in range(15):
                z = 2.27 - j * 0.12
                if j % 2:
                    k.bx(cx - 0.0225, cx + 0.0225, -0.009, 0.009, z - 0.05, z + 0.05, 'metal', ink=False)
                else:
                    k.bx(cx - 0.009, cx + 0.009, -0.0225, 0.0225, z - 0.05, z + 0.05, 'metal', ink=False)
            k.bx(cx - 0.035, cx + 0.035, -0.05, 0.05, 0.515, 0.54, 'metal2', ink=False)       # eye plate on the seat


def seesaw_detail(k):
    k.bx(-0.28, 0.28, -0.325, 0.325, 0.004, 0.02, 'metal', ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bolt(k, sx * 0.2, sy * 0.27, 0.02, '+z', 'metal2', s=0.026)
    ang = math.degrees(math.atan2(0.5, 3.6))
    t = math.tan(math.radians(ang))
    for x in (-1.2, -0.7, 0.7, 1.2):
        for y in (-0.11, 0.11):
            z = 0.6 + x * t
            k.bxr(x, y, z + 0.035, 0.03, 0.03, 0.02, 'metal2', rot=(0, -ang, 0), ink=False)


def monkey_detail(k):
    H = 2.2
    for s in (-1, 1):
        x = s * 2.6
        for f in (-1, 1):
            base_plate(k, x, f * 0.38, 0.1, 'metal', bolts=False)
            for i in range(5):
                z = 0.375 + i * 0.38
                bolt(k, x, f * 0.43, z, '+y' if f > 0 else '-y', 'metal2', s=0.026)
    for f in (-1, 1):
        for i in range(0, 12, 2):
            x = -2.2 + i * 0.4
            bolt(k, x, f * 0.425, H + 0.05, '+y' if f > 0 else '-y', 'metal2', s=0.026)
        for s in (-1, 1):
            bolt(k, s * 2.55 - s * 0.03, f * 0.425, H + 0.05, '+y' if f > 0 else '-y', 'metal2', s=0.026)


def sandpit_detail(k):
    for s in (-1, 1):
        for i in range(4):
            t = -1.35 + i * 0.9
            bolt(k, t, s * 1.825, 0.25, '+z', 'metal2', s=0.03, out=0.01)
            bolt(k, s * 1.825, t, 0.25, '+z', 'metal2', s=0.03, out=0.01)
        for f in (-1, 1):
            cap_end(k, s * 1.95, f * 1.825 - 0.1, f * 1.825 + 0.1, 0.02, 0.23, s)


# ---------------------------------------------------------------- plan-coordinate helpers for the play structures
def pbolt(p, x, z, y, face, c='metal2', s=0.026, out=OUT):
    """bolt in plan coordinates. face: '+x' '-x' '+z' '-z' (plan axes) or '+y' (up)."""
    h = s / 2
    x0, x1, z0, z1, y0, y1 = x - h, x + h, z - h, z + h, y - h, y + h
    if face == '+x':
        x0, x1 = x - EMB, x + out
    elif face == '-x':
        x0, x1 = x - out, x + EMB
    elif face == '+z':
        z0, z1 = z - EMB, z + out
    elif face == '-z':
        z0, z1 = z - out, z + EMB
    else:
        y0, y1 = y - EMB, y + out
    p.bx(x0, x1, z0, z1, y0, y1, c, ink=False)


def deck_posts(p, x0, x1, z0, z1):
    """base plates and anchor bolts under the four corner posts of a play deck"""
    for (px, pz) in ((x0 - 0.08, z0 - 0.08), (x1 + 0.08, z0 - 0.08), (x0 - 0.08, z1 + 0.08), (x1 + 0.08, z1 + 0.08)):
        p.bx(px - 0.13, px + 0.13, pz - 0.13, pz + 0.13, 0.004, 0.022, 'metal', ink=False)
        for sx in (-1, 1):
            for sz in (-1, 1):
                pbolt(p, px + sx * 0.1, pz + sz * 0.1, 0.022, '+y', s=0.026)


def rail_bolts(p, side, a, b, pos, y):
    """two bolts through the top bar of a rail panel, on its outer face (N: -z, S: +z, E: +x, W: -x)"""
    if b - a < 0.5:
        return
    for m in (a + 0.12, b - 0.12):
        if side == 'N':
            pbolt(p, m, pos - 0.005, y, '-z')
        elif side == 'S':
            pbolt(p, m, pos + 0.065, y, '+z')
        elif side == 'E':
            pbolt(p, pos + 0.065, m, y, '+x')
        else:
            pbolt(p, pos - 0.005, m, y, '-x')


def pole_detail(p, x, z):
    p.bx(x - 0.1, x + 0.1, z - 0.1, z + 0.1, 0.004, 0.02, 'metal2', ink=False)
    for sx in (-1, 1):
        pbolt(p, x + sx * 0.075, z + sx * 0.075, 0.02, '+y', s=0.022)


def ship_detail(p, D1, D2):
    # cannon wheels and muzzle rings
    for x in (3.75, 4.25):
        p.cyl(x, 0.497, D1 + 0.15, 0.15, 0.15, 0.06, 'woodD', seg=8, rot=(90, 0, 0), ink=False)
        p.cyl(x, -0.557, D1 + 0.15, 0.15, 0.15, 0.06, 'woodD', seg=8, rot=(90, 0, 0), ink=False)
    p.cyl(4.55, 0.0, D1 + 0.45, 0.2, 0.2, 0.06, 'metal2', seg=8, rot=(0, 90, 0), ink=False)
    p.cyl(3.65, 0.0, D1 + 0.45, 0.23, 0.23, 0.06, 'metal2', seg=8, rot=(0, 90, 0), ink=False)
    # mast collar and straps round the crow's nest
    p.cyl(1.0, 0.0, D1 - 0.003, 0.22, 0.22, 0.25, 'metal2', seg=8, ink=False)
    for i in range(10):
        a = i * 36.0
        r = 0.75
        p.k.bxr(1.0 + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 5.9, 0.04, 0.08, 0.54, 'metal2',
                rot=(0, 0, a), ink=False)
