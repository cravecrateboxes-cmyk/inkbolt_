"""kit-factory modelled detail (tactical look plan Stage 11): real-plant fixings on the pieces the player sees most.
Built on the kit_base detail helpers; every part is ink=False, at least 3 mm proud, embedded 3 mm, horizontal runs stop
5 mm short of the piece sides. Faces looking toward Blender -Y are drawn at y = yf in the current frame
(k.push(0, 0, 180) for the +Y face, push(x, 0, 90) for +X, push(x, 0, 270) for -X)."""
import math

from kit_base import (PROUD, EMBED, bolt_row, panel_seams, base_trim, conduit_run, junction_box, sign_plate,
                      cable_tray, drip_edge)

ST, ST2, STD = 'steel', 'steel2', 'steelDark'


def screw(k, x, z, yf, c=STD, s=0.02):
    k.bx(x - s / 2, x + s / 2, yf - PROUD - 0.002, yf + EMBED, z - s / 2, z + s / 2, c, ink=False)


def access_panel(k, x0, x1, z0, z1, yf, c='panelG', sc=STD, handle=True, d=0.008, m=0.03):
    """A bolted inspection panel on a -Y face: 8 mm plate, a screw in each corner, a quarter-turn latch."""
    k.bx(x0, x1, yf - d, yf + EMBED, z0, z1, c, ink=False)
    for x in (x0 + m, x1 - m):
        for z in (z0 + m, z1 - m):
            screw(k, x, z, yf - d, sc)
    if handle:
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        k.bx(xm - 0.03, xm + 0.03, yf - d - 0.014, yf - d + EMBED, zm - 0.012, zm + 0.012, sc, ink=False)


def isolator(k, x, z, yf):
    """Wall-mounted isolator switch: yellow enclosure, red rotary handle on a black plate, a lock tab."""
    k.bx(x - 0.08, x + 0.08, yf - 0.085, yf + EMBED, z - 0.1, z + 0.1, 'hazard', ink=False)
    k.bx(x - 0.055, x + 0.055, yf - 0.092, yf - 0.085 + 0.001, z - 0.03, z + 0.08, 'ink', ink=False)
    k.bx(x - 0.012, x + 0.012, yf - 0.112, yf - 0.092 + 0.001, z + 0.012, z + 0.058, 'red', ink=False)
    k.bx(x - 0.03, x + 0.03, yf - 0.092, yf - 0.085 + 0.001, z - 0.075, z - 0.05, ST2, ink=False)


def extinguisher(k, x, z0, yf):
    """Fire extinguisher on a wall hook with its sign plate above."""
    yc = yf - 0.075
    k.bx(x - 0.06, x + 0.06, yf - 0.012, yf + EMBED, z0 - 0.02, z0 + 0.5, STD, ink=False)         # back plate
    k.cyl(x, yc, z0, 0.065, 0.065, 0.4, 'red', seg=8, ink=False)
    k.cyl(x, yc, z0 + 0.4, 0.025, 0.025, 0.08, STD, seg=6, ink=False)
    k.bx(x - 0.045, x + 0.045, yc - 0.02, yc + 0.02, z0 + 0.46, z0 + 0.49, STD, ink=False)         # head lever
    for zz in (z0 + 0.1, z0 + 0.28):
        k.bx(x - 0.07, x + 0.07, yc - 0.07, yc + 0.065, zz, zz + 0.03, STD, ink=False)           # strap
    sign_plate(k, x, z0 + 0.82, yf, 0.26, 0.26, 'label', 'red')


def framed_board(k, x0, x1, z0, z1, yf, c=STD, w=0.022, d=0.02):
    """Angle frame round a flat marked board (flat quads stay inside it), corner screws."""
    k.bx(x0 - 0.017, x1 + 0.017, yf - d, yf + EMBED, z1 - 0.005, z1 + w - 0.005, c, ink=False)
    k.bx(x0 - 0.017, x1 + 0.017, yf - d, yf + EMBED, z0 - w + 0.005, z0 + 0.005, c, ink=False)
    k.bx(x0 - w + 0.005, x0 + 0.005, yf - d, yf + EMBED, z0 + 0.007, z1 - 0.007, c, ink=False)
    k.bx(x1 - 0.005, x1 + w - 0.005, yf - d, yf + EMBED, z0 + 0.007, z1 - 0.007, c, ink=False)
    for x in (x0 - 0.004, x1 + 0.004):
        for z in (z0 - 0.006, z1 + 0.006):
            screw(k, x, z, yf - d, ST, s=0.012)


# ------------------------------------------------------------------ wall modules
def tray(k, x0, x1, z, yf, d=0.12):
    """Perforated cable tray on stand-off brackets with two cables in it (own version: kit_base's helper overlaps itself)."""
    k.bx(x0, x1, yf - d, yf + 0.006, z, z + 0.008, 'grate', ink=False)
    k.bx(x0 + 0.005, x1 - 0.005, yf - d - 0.006, yf - d + 0.006, z + 0.004, z + 0.06, 'grate', ink=False)
    for i, (ya, yb) in enumerate(((yf - 0.047, yf - 0.023), (yf - 0.087, yf - 0.063))):
        k.bx(x0 + 0.015, x1 - 0.015, ya, yb, z + 0.012 + 0.004 * i, z + 0.036 + 0.004 * i, 'rubber', ink=False)
    for x in (x0 + 0.12, x1 - 0.12):
        k.bx(x - 0.02, x + 0.02, yf - d + 0.004, yf + 0.009, z - 0.03, z + 0.002, STD, ink=False)


def wall_detail(k, kind, x0=-0.495, x1=0.495):
    """Dado kick rail, a conduit run with drops, cladding seams, cable tray, extinguisher / isolator / junction box.
    Dado face y = -0.53 (z 0..3), siding face y = -0.5 (z 3.08..5.95)."""
    base_trim(k, x0, x1, -0.53, STD, h=0.07, d=0.02, z0=0.25)                    # kick rail above the hazard base
    if kind in ('Sign', 'Win_Sign'):
        framed_board(k, -0.46, 0.46, 3.3, 5.6, -0.506)
        return
    if x1 - x0 <= 0.5:
        return
    panel_seams(k, x0, x1, 5.0, 5.92, -0.5, 0.5, STD)
    if kind not in ('Vent', 'Win_Vent', 'Panel', 'Win_Panel'):
        panel_seams(k, x0, x1, 3.12, 4.15, -0.5, 0.5, STD)
    tray(k, x0, x1, 5.35, -0.5)
    if kind != 'End':
        conduit_run(k, x0, x1, 2.65, -0.53, 'tin2', STD)
    if kind in ('Plain', 'Win_A'):
        extinguisher(k, 0.27, 0.95, -0.53)
        isolator(k, -0.27, 1.55, -0.53)
        junction_box(k, -0.27, 2.12, -0.53, STD, ST2, w=0.2, h=0.2, d=0.08)
        k.cyl(-0.27, -0.558, 2.22, 0.018, 0.018, 0.43, 'tin2', seg=6, ink=False)
    elif kind == 'Win_B':
        junction_box(k, 0.27, 2.1, -0.53, STD, ST2, w=0.22, h=0.26, d=0.09)
        k.cyl(0.27, -0.558, 2.23, 0.018, 0.018, 0.42, 'tin2', seg=6, ink=False)
        isolator(k, -0.27, 1.5, -0.53)
        extinguisher(k, 0.27, 0.65, -0.53)
    elif kind in ('Panel', 'Win_Panel'):
        bolt_row(k, -0.34, 0.04, 1.06, -0.78, 2, STD, s=0.026)
        bolt_row(k, -0.34, 0.04, 2.04, -0.78, 2, STD, s=0.026)
        k.bx(-0.373, -0.357, -0.79, -0.77, 1.05, 2.05, STD, ink=False)           # hinge
        k.bx(0.0, 0.03, -0.8, -0.77, 1.45, 1.7, ST, ink=False)                    # handle
        junction_box(k, -0.27, 2.45, -0.53, STD, ST2, w=0.16, h=0.18, d=0.08)
    elif kind in ('Vent', 'Win_Vent'):
        bolt_row(k, -0.38, 0.38, 3.29, -0.66, 4, STD, s=0.02)
        bolt_row(k, -0.38, 0.38, 4.06, -0.66, 4, STD, s=0.02)
        drip_edge(k, -0.43, 0.43, 4.1, -0.66, ST2, d=0.05, t=0.03)
    elif kind in ('Hose', 'Win_Hose'):
        bolt_row(k, -0.15, 0.15, 1.23, -0.75, 2, STD, s=0.022)
        bolt_row(k, -0.15, 0.15, 1.87, -0.75, 2, STD, s=0.022)
        k.bx(-0.208, -0.19, -0.77, -0.74, 1.25, 1.85, STD, ink=False)            # hinge
        sign_plate(k, 0.0, 2.5, -0.53, 0.3, 0.18, 'label', 'red')


def column_detail(k):
    """Wall_Col: base plate anchor bolts, web stiffeners, flange tip guards, a bolted splice plate, bracket gussets."""
    for sx in (-1, 1):
        for y in (-0.97, -0.6):
            k.bx(sx * 0.32 - 0.02, sx * 0.32 + 0.02, y - 0.02, y + 0.02, 0.057, 0.1, ST, ink=False)
    for z in (0.5, 3.0, 7.0):                                                    # web stiffeners between the flanges
        k.bx(-0.27, 0.27, -0.863, -0.637, z, z + 0.025, 'beam2', ink=False)
    for sx in (-1, 1):                                                           # tip guards on the flange edges
        xa, xb = sorted((sx * 0.277, sx * 0.292))
        k.bx(xa, xb, -0.95, -0.85, 0.1, 1.3, STD, ink=False)
    k.bx(-0.2, 0.2, -0.953, -0.937, 4.9, 5.5, ST2, ink=False)                  # splice plate
    for x in (-0.14, 0.14):
        for z in (4.97, 5.2, 5.43):
            screw(k, x, z, -0.953, STD, s=0.026)
    for sx in (-1, 1):                                                           # bracket gussets and cleats
        k.bx(sx * 0.2 - 0.015, sx * 0.2 + 0.015, -1.4, -0.94 + EMBED, 6.9, 7.2, 'beam2', ink=False)
    for x in (-0.2, 0.2):
        k.bx(x - 0.02, x + 0.02, -1.4 - PROUD, -1.4 + EMBED, 7.25, 7.55, STD, ink=False)


def corner_detail(k):
    """Corner pier: four steel angle guards (L in plan) on the vertical edges."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa = sorted((sx * 0.497, sx * 0.513))
            ya = sorted((sy * 0.44, sy * 0.513))
            k.bx(xa[0], xa[1], ya[0], ya[1], 0.1, 1.3, STD, ink=False)
            xb = sorted((sx * 0.44, sx * 0.497))
            yb = sorted((sy * 0.497, sy * 0.513))
            k.bx(xb[0], xb[1], yb[0], yb[1], 0.1, 1.3, STD, ink=False)


# ------------------------------------------------------------------ roller door
def gate_frame_detail(k):
    for s in (-1, 1):                                                            # post base plates and anchor bolts
        xa, xb = sorted((s * 1.5, s * 2.103))
        k.bx(xa, xb, -0.65, 0.65, 0.004, 0.05, STD, ink=False)
        for f in (-1, 1):
            for x in (s * 1.6, s * 2.0):
                k.bx(x - 0.02, x + 0.02, f * 0.635 - 0.012, f * 0.635 + 0.012, 0.047, 0.085, ST, ink=False)
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        k.bx(-2.395, 2.395, -0.62, -0.25 + EMBED, 5.95, 6.15, 'beam2', ink=False)      # girt across the infill
        junction_box(k, -1.9, 3.7, -0.7, STD, ST2, w=0.5, h=0.4, d=0.1)                # roll-up motor box
        bolt_row(k, -2.1, -1.7, 3.57, -0.805, 3, STD, s=0.02)
        conduit_run(k, -1.65, -0.95, 3.7, -0.7, 'tin2', STD, every=0.35)                # to the photo-eye
        junction_box(k, -0.88, 3.7, -0.7, STD, ST2, w=0.12, h=0.12, d=0.06)
        k.pop()


def gate_shutter_detail(k):
    for s in (-1, 1):                                                            # guide rails with bolts
        xa, xb = sorted((s * 1.497, s * 1.43))
        k.bx(xa, xb, -0.075, 0.075, 0.008, 3.0, STD, ink=False)
        for z in (0.5, 1.0, 1.5, 2.0, 2.5):
            x = s * 1.463
            k.bx(x - 0.012, x + 0.012, -0.081, -0.072, z - 0.012, z + 0.012, ST, ink=False)
            k.bx(x - 0.012, x + 0.012, 0.072, 0.081, z - 0.012, z + 0.012, ST, ink=False)
    k.bx(-1.49, 1.49, -0.082, 0.082, 0.004, 0.05, 'rubber', ink=False)         # bottom seal
    for f in (-1, 1):                                                            # pull handle
        k.push(0, 0, 0 if f < 0 else 180)
        for x in (-0.16, 0.16):
            k.bx(x - 0.012, x + 0.012, -0.115, -0.07 + EMBED, 0.176, 0.194, STD, ink=False)
        k.bx(-0.18, 0.18, -0.12, -0.1, 0.17, 0.2, ST, ink=False)
        k.pop()


# ------------------------------------------------------------------ conveyors
def conveyor_detail(k):
    for x in (-0.3, 0.3):
        for s in (-1, 1):                                                        # leg feet with anchor bolts
            ya, yb = sorted((s * 0.31, s * 0.47))
            k.bx(x - 0.07, x + 0.07, ya, yb, 0.004, 0.02, STD, ink=False)
            for y in (s * 0.335, s * 0.445):
                k.bx(x - 0.0125, x + 0.0125, y - 0.0125, y + 0.0125, 0.017, 0.045, ST, ink=False)
    for s in (-1, 1):
        ya, yb = sorted((s * 0.39, s * 0.45))
        k.bx(-0.495, 0.495, ya, yb, 0.62, 0.723, STD, ink=False)               # stringer under the rail
        ya, yb = sorted((s * 0.467, s * 0.478))
        k.bx(-0.495, 0.495, ya, yb, 0.724, 0.77, STD, ink=False)               # side guard lip
        ya, yb = sorted((s * 0.467, s * 0.476))
        for x in (-0.2, 0.2):
            k.bx(x - 0.016, x + 0.016, ya, yb, 0.81, 0.842, ST, ink=False)     # splice bolts


def hood_detail(k, kind, L, W, H, rail, base):
    sx = -1 if kind == 'Feed' else 1
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        if f < 0:
            access_panel(k, 0.22 if L < 0.55 else 0.24, L - 0.07, rail + 0.3, H - 0.14, -W)
        else:
            access_panel(k, -0.3, 0.3, rail + 0.3, H - 0.14, -W)
        bolt_row(k, -L + 0.1, L - 0.1, H + 0.04, -(W + 0.03), 3, STD, s=0.02)    # roof fixing screws
        if base is not None:
            base_trim(k, -L, L, -W, STD, h=0.14, d=0.014)                        # toe kick
        k.pop()
    xm = sx * (L + 0.07)                                                         # motor: cable gland and flex conduit
    k.cyl(xm, 0, rail + 0.397, 0.03, 0.03, 0.05, STD, seg=6, ink=False)
    k.cyl(xm, 0, rail + 0.44, 0.018, 0.018, 0.22, 'rubber', seg=6, ink=False)
    xa, xb = sorted((sx * (L + 0.02), sx * (L + 0.12)))
    for s2 in (-1, 1):                                                           # motor cooling fins
        ya, yb = sorted((s2 * 0.217, s2 * 0.232))
        for z in (rail - 0.2, rail - 0.1, rail, rail + 0.1, rail + 0.2):
            k.bx(xa, xb, ya, yb, z - 0.015, z + 0.015, ST2, ink=False)


# ------------------------------------------------------------------ machine tools and robot cells
def mill_detail(k):
    access_panel(k, -1.27, -1.07, 0.35, 1.6, -0.8)
    access_panel(k, -0.75, 0.25, 0.27, 0.5, -0.8)
    access_panel(k, 0.72, 1.18, 0.3, 0.9, -0.8)
    bolt_row(k, -1.25, 1.25, 2.275, -0.82, 6, STD, s=0.024)
    k.push(1.3, 0, 90)                                                           # +X face: service entry
    junction_box(k, -0.3, 1.0, 0.0, STD, ST2, w=0.3, h=0.36, d=0.12)
    isolator(k, 0.3, 1.3, 0.0)
    k.cyl(-0.3, -0.032, 1.18, 0.02, 0.02, 1.0, 'tin2', seg=6, ink=False)
    for z in (1.5, 1.9):
        k.bx(-0.325, -0.275, -0.056, 0.003, z, z + 0.03, STD, ink=False)
    k.pop()


def lathe_detail(k):
    for x0, x1 in ((-1.3, -0.5), (-0.4, 0.4), (0.5, 1.3)):
        access_panel(k, x0, x1, 0.14, 0.8, -0.5)
    base_trim(k, -1.4, 1.4, -0.5, STD, h=0.1, d=0.012, z0=0.0)
    bolt_row(k, -1.25, -0.65, 1.04, -0.45, 3, STD, s=0.022)
    bolt_row(k, -1.25, -0.65, 1.65, -0.45, 3, STD, s=0.022)
    k.push(-1.4, 0, 270)                                                         # -X face: junction box
    junction_box(k, 0.0, 0.5, 0.0, STD, ST2, w=0.26, h=0.3, d=0.08)
    k.pop()


def arm_cell_detail(k):
    for sx in (-1, 1):                                                           # plinth: anchor bolts, edge angle
        for sy in (-1, 1):
            k.bx(sx * 0.82 - 0.03, sx * 0.82 + 0.03, sy * 0.82 - 0.03, sy * 0.82 + 0.03, 0.12 - EMBED, 0.15, ST, ink=False)
    for s in (-1, 1):
        ya, yb = sorted((s * 0.894, s * 0.906))
        k.bx(-0.906, 0.906, ya, yb, 0.004, 0.13, STD, ink=False)
        k.bx(ya, yb, -0.894, 0.894, 0.004, 0.13, STD, ink=False)
    k.bx(0.6, 0.894, 0.42, 0.48, 0.126 - EMBED, 0.16, STD, ink=False)           # cable duct into the robot base


def arm_base_detail(k):
    """Called inside robot_arm's frame: anchor bolts round the base flange and a connector box."""
    for a in (45, 135, 225, 315):
        x, y = 0.37 * math.cos(math.radians(a)), 0.37 * math.sin(math.radians(a))
        k.bx(x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.177, 0.21, ST, ink=False)
    k.bx(-0.06, 0.06, 0.37, 0.47, 0.04, 0.14, STD, ink=False)


def test_cage_detail(k):
    posts = ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9), (0, 1.9), (-1.9, 0), (1.9, 0))
    for (x, y) in posts:
        k.bx(x - 0.09, x + 0.09, y - 0.09, y + 0.09, 0.004, 0.06, STD, ink=False)   # base plate (above the floor decals)
        for dx in (-0.07, 0.07):
            for dy in (-0.07, 0.07):
                k.bx(x + dx - 0.011, x + dx + 0.011, y + dy - 0.011, y + dy + 0.011, 0.057, 0.085, ST, ink=False)
    for (a, b) in ((-1.853, -0.047), (0.047, 1.853)):                            # mid rails between the posts
        k.bx(a, b, 1.87, 1.93, 1.1, 1.15, STD, ink=False)
        k.bx(-1.93, -1.87, a, b, 1.1, 1.15, STD, ink=False)
        k.bx(1.87, 1.93, a, b, 1.1, 1.15, STD, ink=False)
    k.bx(-1.853, -0.603, -1.93, -1.87, 1.1, 1.15, STD, ink=False)
    k.bx(0.603, 1.853, -1.93, -1.87, 1.1, 1.15, STD, ink=False)
    for x in (-0.45, 0.45):                                                      # warning sign screws
        for z in (1.43, 1.87):
            screw(k, x, z, -1.95, STD, s=0.022)


# ------------------------------------------------------------------ catwalk
def catwalk_detail(k):
    D = 4.0
    for s in (-1, 1):
        xa, xb = sorted((s * 0.875, s * 0.935))
        xo0, xo1 = sorted((s * 0.932, s * 0.944))
        for y in (-3.5, -1.5, 0.5, 2.5):
            k.bx(xa, xb, y - 0.05, y + 0.05, D + 0.147, D + 0.19, STD, ink=False)         # stanchion base plate
            k.bx(xa, xb, y - 0.04, y + 0.04, D + 0.535, D + 0.605, STD, ink=False)        # mid-rail clamp
            k.bx(xa, xb, y - 0.04, y + 0.04, D + 0.994, D + 1.066, STD, ink=False)        # top-rail clamp
            k.bx(xo0, xo1, y - 0.012, y + 0.012, D + 0.158, D + 0.182, ST, ink=False)     # plate bolt
