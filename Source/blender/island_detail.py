"""kit-island modelled detail (tactical look plan Stage 11): bamboo lashings, thatch eave rolls, door and shutter
hardware, stilt-post footings, deck nail heads, post bands, mooring cleats, crate battens, barrel chimes, torch
bindings and sign bolts on the pieces the player sees most. Every part is ink=False (no outline shell), >= 3 mm
proud, embedded 3 mm, horizontal runs inset 5 mm from the piece sides. Called from the piece builders in
fam_kit_island.py just before their collision boxes; nothing here moves or renames an existing shape."""
import math

from kit_base import EMBED, bolt_row, window_frame_depth


def band(k, x, y, z, r, h, c='rope', seg=6, n=1, gap=0.0):
    """n stacked ring wraps (open tubes, no caps) round a vertical pole of radius < r"""
    for i in range(n):
        k.cyl(x, y, z + i * (h + gap), r, r, h, c, seg=seg, caps=False, ink=False)


def nail(k, x, y, z, c='metal2', s=0.022):
    """nail head on an upward face at height z (6.5 mm proud, 3 mm embedded)"""
    k.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z - EMBED, z + 0.0065, c, ink=False)


def torch_bind(k, x, y, zc, rp=0.062, rings=2, z_first=None):
    """rope lashing on a torch pole just under its cup (cup base at zc)"""
    z = z_first if z_first is not None else zc - 0.03 - rings * 0.05
    for i in range(rings):
        k.cyl(x, y, z + i * 0.05, rp, rp, 0.03, 'rope', seg=6, caps=False, ink=False)


def cup_band(k, x, y, zc, r_base, r_top, hc, c='rope'):
    """a rope band round the lower third of a thatch cup (zc..zc+hc, radius r_base -> r_top)"""
    z0 = zc + hc * 0.18
    r = r_base + (r_top - r_base) * 0.36 + 0.016
    k.cyl(x, y, z0, r, r, 0.035, c, seg=6, caps=False, ink=False)


def window_bamboo(k, xc, zc, hw, hh, yf, c='wood2', mullions=1):
    """bamboo window frame (on a -Y facing plane yf) with vertical mullions in the opening and a sill"""
    yb = yf + 0.009                       # backs 12 mm inside the wall: clear of the flat window / strip quads
    window_frame_depth(k, xc - hw, xc + hw, zc - hh, zc + hh, yb, c, depth=0.059, t=0.045)
    for i in range(mullions):
        x = xc - hw + 2 * hw * (i + 1) / (mullions + 1)
        k.bx(x - 0.015, x + 0.015, yf - 0.03, yb + EMBED, zc - hh + 0.004, zc + hh - 0.004, c, ink=False)
    k.bx(xc - hw - 0.08, xc + hw + 0.08, yf - 0.09, yb + 0.007, zc - hh - 0.075, zc - hh - 0.04, c, ink=False)


def strap_hinge(k, x0, x1, z, yf, c='metal2'):
    """flat strap hinge across a door leaf from the hinge edge x0 to x1, two bolts"""
    k.bx(x0, x1, yf - 0.012, yf + EMBED, z - 0.03, z + 0.03, c, ink=False)
    bolt_row(k, x0 + 0.06, x1 - 0.06, z, yf - 0.012, 2, c, s=0.026)


# ------------------------------------------------------------------------------------------------ hut
def hut(k):
    yf = -1.2
    # stilt posts: stone footing pad, lashing bands, cross ties lashed at every post
    for x in (-1.9, 1.9):
        for y in (-1.6, 1.9):
            k.cyl(x, y, 0.004, 0.2, 0.2, 0.066, 'rock2', seg=6, ink=False)
            band(k, x, y, 0.7, 0.13, 0.05, n=2, gap=0.025)
    for y in (-1.6, 1.9):
        k.bx(-1.9 + 0.05, 1.9 - 0.05, y - 0.03, y + 0.03, 0.36, 0.42, 'wood', ink=False)
    for x in (-1.9, 1.9):
        sx = 1 if x > 0 else -1
        k.bx(x + sx * 0.1 - 0.03, x + sx * 0.1 + 0.03, -1.6 + 0.05, 1.9 - 0.05, 0.36, 0.42, 'wood', ink=False)
        for y in (-1.6, 1.9):
            band(k, x, y, 0.34, 0.135, 0.04, n=1)
    # floor edge board and nail heads along the porch deck
    k.bx(-2.145, 2.145, -2.328, -2.297, 0.87, 1.03, 'wood2', ink=False)
    for i in range(8):
        x = -2.15 + 4.3 * (i + 0.5) / 8
        for y in (-2.2, -1.4):
            nail(k, x, y, 1.05)
    # threshold, door frame and strap hinges, latch knob
    k.bx(-0.45, 0.45, yf - 0.06, yf + 0.012, 1.038, 1.085, 'wood', ink=False)
    k.bx(-0.52, -0.42, yf - 0.03, yf + EMBED, 1.045, 2.47, 'wood2', ink=False)
    k.bx(0.42, 0.52, yf - 0.03, yf + EMBED, 1.045, 2.47, 'wood2', ink=False)
    k.bx(-0.42, 0.42, yf - 0.03, yf + EMBED, 2.4, 2.47, 'wood2', ink=False)
    for z in (1.4, 2.05):
        strap_hinge(k, -0.42, -0.1, z, yf - 0.006)
    k.sph(0.3, yf - 0.03, 1.72, 0.035, 'metal2', seg=(6, 4), ink=False)
    # bamboo windows: frames, mullions, sills; side windows on the +/-X walls
    for sx in (-1, 1):
        window_bamboo(k, sx * 1.25, 2.1, 0.3, 0.3, yf - 0.006)
    for sx in (-1, 1):
        k.push(sx * 1.8, 0, 90 * sx)
        window_bamboo(k, 0.15 * sx, 2.1, 0.45, 0.3, -0.003, mullions=2)
        k.pop()
    # lashed bamboo rails, corner poles and a wall plate on the front wall
    for z, spans in ((1.5, ((-1.795, -0.53), (0.53, 1.795))), (2.62, ((-1.795, 1.795),))):
        for a, b in spans:
            k.bx(a, b, yf - 0.024, yf + EMBED, z, z + 0.05, 'rope', ink=False)
    for sx in (-1, 1):
        k.cyl(sx * 1.8, yf, 1.044, 0.05, 0.05, 1.93, 'wood', seg=5, ink=False)
        band(k, sx * 1.8, yf, 1.5, 0.06, 0.05)
        band(k, sx * 1.8, yf, 2.6, 0.06, 0.05)
    k.bx(-1.795, 1.795, yf - 0.035, yf + EMBED, 2.9, 2.97, 'wood2', ink=False)
    # porch posts: bamboo mid rail, lashings, caps
    k.bx(-1.94, 1.94, -2.178, -2.122, 1.45, 1.5, 'wood', ink=False)
    for x in (-2.0, 2.0):
        band(k, x, -2.15, 1.88, 0.082, 0.05)
        band(k, x, -2.15, 1.43, 0.082, 0.05)
        k.cyl(x, -2.15, 2.045, 0.08, 0.06, 0.04, 'wood', seg=5, ink=False)
    # ladder: lashings where the rungs meet the rails
    for sx in (-1, 1):
        for i in range(4):
            z = 0.225 + i * 0.22
            y = -2.55 + 0.2126 * (z + 0.025 - 0.5)
            xa, xb = (0.505, 0.525) if sx > 0 else (-0.525, -0.505)
            k.bx(xa, xb, y - 0.045, y + 0.045, z - 0.005, z + 0.055, 'rope', ink=False)
    # thatch: eave rolls on all four sides, hip ridges and a ridge cap
    cy = 0.35
    for s in (-1, 1):
        k.cyl(-2.2, cy + s * 1.93, 3.03, 0.07, 0.07, 4.4, 'thatch2', seg=6, rot=(0, 90, 0), ink=False)
        k.cyl(s * 2.28, cy - 2.1, 3.03, 0.07, 0.07, 4.2, 'thatch2', seg=6, rot=(-90, 0, 0), ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.beam((sx * 2.2, cy + sy * 2.2, 3.05), (sx * 0.16, cy + sy * 0.16, 4.85), 0.07, 'thatch2', ink=False)
    k.cyl(0, cy, 4.86, 0.09, 0.07, 0.07, 'thatch2', seg=6, ink=False)


# ------------------------------------------------------------------------------------------------ jetty
def jetty(k):
    for sx in (-1, 1):
        xa, xb = (0.997, 1.03) if sx > 0 else (-1.03, -0.997)
        k.bx(xa, xb, -3.895, 3.895, 0.06, 0.15, 'wood2', ink=False)              # rim boards
    for y in (-3.6, -1.2, 1.2, 3.6):
        k.bx(-1.14, 1.14, y - 0.06, y + 0.06, 0.04, 0.103, 'wood2', ink=False)   # bearers under the deck
    for i in range(16):                                                           # nail heads, both ends of each plank
        y = -3.9 + 7.8 * (i + 0.5) / 16
        for x in (-0.88, 0.88):
            nail(k, x, y, 0.16)
    for y in (1.2, 3.6):                                                          # post bands and caps
        for x in (-1.08, 1.08):
            band(k, x, y, 0.66, 0.108, 0.04, n=2, gap=0.03)
            k.cyl(x, y, 0.94, 0.108, 0.09, 0.04, 'wood', seg=6, ink=False)
    for x in (-0.93, 0.93):                                                       # mooring cleats
        for y in (-2.6, 2.4):
            k.bx(x - 0.03, x + 0.03, y - 0.1, y + 0.1, 0.157, 0.185, 'metal2', ink=False)
            for dy in (-0.07, 0.07):
                k.bx(x - 0.02, x + 0.02, y + dy - 0.025, y + dy + 0.025, 0.185 - EMBED, 0.22, 'metal2', ink=False)
    for z in (0.2, 0.32):                                                         # barrel hoops
        k.cyl(0.6, 3.4, z, 0.19, 0.19, 0.03, 'metal2', seg=8, caps=False, ink=False)


# ------------------------------------------------------------------------------------------------ fence
def fence(k, rails):
    """lashings where each rail meets each post; rails = rail centre heights after jitter"""
    for x in (-0.35, 0.35):
        for z in rails:
            k.bx(x - 0.03, x + 0.03, -0.13, 0.085, z - 0.06, z + 0.06, 'rope', ink=False)


# ------------------------------------------------------------------------------------------------ sea wall
def seawall(k, kind):
    k.bx(-0.495, 0.495, -0.15, -0.117, 0.004, 0.09, 'rockd', ink=False)             # plinth strip
    for x in (-0.17, 0.17):
        k.bx(x - 0.008, x + 0.008, -0.16, 0.46, 0.957, 0.963, 'rock2', ink=False)    # cap expansion joints
    k.bx(-0.495, 0.495, -0.19, -0.167, 0.88, 0.915, 'rock2', ink=False)             # cap drip lip
    if kind == 'B':
        band(k, 0.0, -0.32, 1.0, 0.122, 0.035, n=3, gap=0.02)                          # mooring rope wraps
        k.cyl(0.0, -0.32, 0.2, 0.125, 0.125, 0.04, 'metal2', seg=6, caps=False, ink=False)
        k.cyl(0.0, -0.32, 1.3, 0.12, 0.12, 0.04, 'metal2', seg=6, caps=False, ink=False)
    elif kind == 'C':
        k.bx(0.09, 0.31, -0.4, -0.2, 0.0, 0.03, 'metal2', ink=False)                  # base plate and bolts
        for x in (0.11, 0.29):
            for y in (-0.38, -0.22):
                k.bx(x - 0.013, x + 0.013, y - 0.013, y + 0.013, 0.027, 0.038, 'metal', ink=False)
        for x in (0.08, 0.32):                                                        # lamp cage corner bars
            for y in (-0.42, -0.18):
                xs = x + (0.028 if x > 0.2 else -0.028)
                ys = y + (0.028 if y > -0.3 else -0.028)
                k.bx(min(x, xs) - (0.0 if x > 0.2 else 0.0), max(x, xs), min(y, ys), max(y, ys), 1.9, 2.16, 'metal2', ink=False)
        k.cyl(0.2, -0.3, 1.2, 0.07, 0.07, 0.05, 'metal2', seg=6, caps=False, ink=False)


# ------------------------------------------------------------------------------------------------ crates and barrels
def crate(k, h, hz, kind):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = (h - 0.05, h + 0.012) if sx > 0 else (-h - 0.012, -h + 0.05)
            y0, y1 = (h - 0.05, h + 0.012) if sy > 0 else (-h - 0.012, -h + 0.05)
            k.bx(x0, x1, y0, y1, 0.006, hz - 0.006, 'wood2', ink=False)
    if kind != 'Small':
        dx, dz = 2 * h - 0.2, hz - 0.2
        ang = math.degrees(math.atan2(dz, dx))
        k.bxr(0, -h - 0.003, hz / 2, math.hypot(dx, dz), 0.018, 0.06, 'wood2', rot=(0, -ang, 0), ink=False)
        for sx in (-1, 1):
            x, z = sx * (h - 0.1), hz / 2 + sx * (hz / 2 - 0.1)
            k.bx(x - 0.013, x + 0.013, -h - 0.017, -h - 0.007, z - 0.013, z + 0.013, 'metal2', ink=False)


def barrel_hoops(k, x, y, lying=None):
    if lying is None:
        k.cyl(x, y, 0.004, 0.31, 0.31, 0.036, 'metal2', seg=10, caps=False, ink=False)
        k.cyl(x, y, 0.862, 0.31, 0.31, 0.036, 'metal2', seg=10, caps=False, ink=False)
        k.cyl(x, y - 0.2753, 0.5, 0.032, 0.032, 0.022, 'metal', seg=6, rot=(90, 0, 0), ink=False)    # bung
    else:
        a = math.radians(lying)
        for t in (0.108, 0.702):
            k.cyl(x + math.cos(a) * t, y + math.sin(a) * t, 0.3, 0.312, 0.312, 0.07, 'metal2', seg=10, rot=(0, 90, lying), caps=False, ink=False)


# ------------------------------------------------------------------------------------------------ torches, signs, umbrella
def torch(k):
    torch_bind(k, 0, 0, 1.85, rp=0.068, rings=3)
    cup_band(k, 0, 0, 1.85, 0.08, 0.17, 0.28)
    k.cyl(0, 0, 0.004, 0.09, 0.07, 0.07, 'rock2', seg=6, ink=False)                  # foot collar


def signpost(k):
    for z in (1.55, 1.18):
        k.cyl(0, -0.0535 + 0.012, z, 0.017, 0.017, 0.024, 'metal2', seg=6, rot=(90, 0, 0), ink=False)
    for (x, z) in ((0.579, 1.529), (-0.539, 1.154)):
        k.cyl(x, -0.025 + 0.012, z, 0.014, 0.014, 0.024, 'metal2', seg=6, rot=(90, 0, 0), ink=False)
    k.cyl(0, 0, 1.9, 0.08, 0.05, 0.045, 'wood2', seg=6, ink=False)                  # pole cap
    k.cyl(0, 0, 0.004, 0.105, 0.075, 0.09, 'drift', seg=6, ink=False)                # sand collar


def umbrella(k):
    k.cyl(0, -0.126, 1.2, 0.05, 0.05, 0.08, 'metal', seg=6, rot=(6, 0, 0), ink=False)
    k.sph(0, -0.2, 2.4, 0.045, 'metal', seg=(6, 4), ink=False)
    for x in (-0.15, 0.15):
        k.bx(x - 0.006, x + 0.006, -0.945, -0.355, 0.327, 0.336, 'ink', ink=False)  # seat slats
    k.bx(-0.315, 0.315, -0.372, -0.34, 0.5, 0.508, 'ink', ink=False)               # back rest slat


# ------------------------------------------------------------------------------------------------ gate, trail walls, hatch
def gate(k):
    for s in (-1, 1):
        x0, x1 = (1.52, 2.0) if s > 0 else (-2.0, -1.52)
        k.bx(x0 - 0.03, x1 + 0.03, -0.56, 0.56, 0.004, 0.12, 'rock2', ink=False)
        cx = 0.5 * (x0 + x1)
        for z in (0.6, 1.5, 2.4):                                                   # lashing knots on the rope bands
            k.bx(cx - 0.035, cx + 0.035, -0.555, -0.515, z + 0.02, z + 0.1, 'wood2', ink=False)
        for f in (-1, 1):
            torch_bind(k, s * 1.76, f * 0.66, 3.55, rp=0.066, rings=2, z_first=3.41)


def trail_wall(k, kind):
    for z in (0.9, 0.52):
        k.bx(-0.07, 0.07, -0.37, -0.255, z - 0.04, z + 0.04, 'wood2', ink=False)    # rope knots at the post
    k.cyl(0.0, -0.3, 0.99, 0.07, 0.05, 0.04, 'wood', seg=5, ink=False)               # post cap
    k.cyl(0.0, -0.3, 0.004, 0.09, 0.07, 0.06, 'rock2', seg=5, ink=False)             # sand footing
    if kind == 'Torch':
        torch_bind(k, 0.3, -0.12, 2.15, rp=0.066, rings=2)
        cup_band(k, 0.3, -0.12, 2.15, 0.07, 0.14, 0.24)


def hatch(k):
    k.cyl(0, 0, 0.03, 1.325, 1.325, 0.05, 'metal2', seg=16, caps=False, ink=False)   # edge hoop
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 16
        k.bxr(math.cos(a) * 1.33, math.sin(a) * 1.33, 0.055, 0.03, 0.05, 0.03, 'metal', rot=(0, 0, math.degrees(a)), ink=False)
