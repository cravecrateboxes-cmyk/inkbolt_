"""kit-factory2 modelled detail (tactical look plan Stage 11): heavy-plant fixings on the pieces the player sees most.
Same rules and style as fac_detail.py: every part is ink=False, at least 3 mm proud, embedded 3 mm, horizontal runs stop
5 mm short of the piece sides. Faces looking toward Blender -Y are drawn at y = yf in the current frame
(k.push(0, 0, 180) for the +Y face, push(x, 0, 90) for +X, push(x, 0, 270) for -X)."""
import math

from kit_base import PROUD, EMBED, bolt_row, panel_seams, base_trim, conduit_run, junction_box, sign_plate
from fac_detail import screw, access_panel, isolator, framed_board

ST, ST2, STD = 'steel', 'steel2', 'steelDark'
RAIL = 9.4


def tray(k, x0, x1, z, yf, d=0.12):
    """Perforated cable tray on stand-off brackets with two cables in it."""
    k.bx(x0, x1, yf - d, yf + 0.006, z, z + 0.008, ST2, ink=False)
    k.bx(x0 + 0.005, x1 - 0.005, yf - d - 0.006, yf - d + 0.006, z + 0.004, z + 0.06, ST2, ink=False)
    for i, (ya, yb) in enumerate(((yf - 0.047, yf - 0.023), (yf - 0.087, yf - 0.063))):
        k.bx(x0 + 0.015, x1 - 0.015, ya, yb, z + 0.012 + 0.004 * i, z + 0.036 + 0.004 * i, 'rubber', ink=False)
    for x in (x0 + 0.12, x1 - 0.12):
        k.bx(x - 0.02, x + 0.02, yf - d + 0.004, yf + 0.009, z - 0.03, z + 0.002, STD, ink=False)


def extinguisher(k, x, z0, yf):
    yc = yf - 0.075
    k.bx(x - 0.06, x + 0.06, yf - 0.012, yf + EMBED, z0 - 0.02, z0 + 0.5, STD, ink=False)
    k.cyl(x, yc, z0, 0.065, 0.065, 0.4, 'red', seg=8, ink=False)
    k.cyl(x, yc, z0 + 0.4, 0.025, 0.025, 0.08, STD, seg=6, ink=False)
    k.bx(x - 0.045, x + 0.045, yc - 0.02, yc + 0.02, z0 + 0.46, z0 + 0.49, STD, ink=False)
    for zz in (z0 + 0.1, z0 + 0.28):
        k.bx(x - 0.07, x + 0.07, yc - 0.07, yc + 0.065, zz, zz + 0.03, STD, ink=False)
    sign_plate(k, x, z0 + 0.82, yf, 0.26, 0.26, 'cream', 'red')


def pipe_collars(k, xs, yc, z, r, face_y):
    """Strap collars on a horizontal pipe (axis along x at y = yc) with a stand-off arm back to the wall face."""
    for x in xs:
        k.bx(x - 0.025, x + 0.025, yc - r - 0.015, yc + r + 0.015, z - r - 0.015, z + r + 0.015, STD, ink=False)
        k.bx(x - 0.012, x + 0.012, yc + r + 0.01, face_y + EMBED, z - 0.02, z + 0.02, STD, ink=False)


# ------------------------------------------------------------------ wall modules
def wall_detail(k, kind, endL=False, endR=False):
    """Plinth face y = -0.53 (z 0..3.2, hazard foot to z 0.26), siding y = -0.5 (z 3.3..), girt z 6..6.2 (y -0.62),
    crane runway corbel z 8.9..9.4 (y -1.12), pipe at z 4.5 (y -0.8, r 0.12) on the full modules."""
    x0 = -0.497 + (0.14 if endL else 0.0)
    x1 = 0.497 - (0.14 if endR else 0.0)
    win = kind.startswith('Win')
    base_trim(k, x0, x1, -0.53, STD, h=0.06, d=0.02, z0=0.27)                     # kick rail above the hazard foot
    if x1 - x0 <= 0.5:
        return
    bolt_row(k, x0 + 0.05, x1 - 0.05, 3.25, -0.57, 4, ST, s=0.022)                # plinth cap fixings
    if kind != 'Win_Duct':
        panel_seams(k, x0, x1, 3.35, 5.95, -0.5, 0.5, STD)                        # cladding sheet joints
    if kind not in ('Win_Duct', 'Win_Sign'):
        panel_seams(k, x0, x1, 6.25, 8.85, -0.5, 0.5, STD)
    panel_seams(k, x0, x1, 9.5, 11.25 if win else 15.55, -0.5, 0.5, STD)
    bolt_row(k, x0 + 0.06, x1 - 0.06, 6.1, -0.62, 4, STD, s=0.03)                 # girt bolts
    if kind not in ('Win_Sign', 'Win_Duct'):
        tray(k, x0, x1, 7.0, -0.5)
    full = not (endL or endR)
    if full:                                                                      # the process pipe: strap collars
        pipe_collars(k, (-0.3, 0.3), -0.8, 4.5, 0.12, -0.5)
    # crane runway: bolted corbel, gussets, rail clips
    r0 = max(x0, -0.497 + (0.68 if endL else 0.0)) + 0.005
    r1 = min(x1, 0.497 - (0.68 if endR else 0.0)) - 0.005
    if r1 > r0 + 0.3:
        bolt_row(k, r0 + 0.05, r1 - 0.05, 9.05, -1.12, max(2, int((r1 - r0) / 0.25)), ST, s=0.024)
        for x in (-0.25, 0.25):
            if r0 + 0.03 < x < r1 - 0.03:
                k.bx(x - 0.012, x + 0.012, -1.1, -0.5 + EMBED, 8.6, 8.9 - EMBED, STD, ink=False)      # gusset under the corbel
                k.bx(x - 0.04, x + 0.04, -1.04, -0.88, RAIL - EMBED, RAIL + 0.03, STD, ink=False)     # rail clip
    # plinth furniture (the oxide block face)
    if kind in ('Plain', 'Win_A'):
        extinguisher(k, 0.27, 0.95, -0.53)
        isolator(k, -0.27, 1.55, -0.53)
        junction_box(k, -0.27, 2.12, -0.53, STD, ST2, w=0.2, h=0.2, d=0.08)
        k.cyl(-0.27, -0.558, 2.22, 0.018, 0.018, 0.43, STD, seg=6, ink=False)
        conduit_run(k, x0, x1, 2.65, -0.53, ST2, STD)
    elif kind == 'Win_B':
        junction_box(k, 0.27, 2.1, -0.53, STD, ST2, w=0.22, h=0.26, d=0.09)
        k.cyl(0.27, -0.558, 2.23, 0.018, 0.018, 0.42, STD, seg=6, ink=False)
        isolator(k, -0.27, 1.5, -0.53)
        extinguisher(k, 0.27, 0.65, -0.53)
        conduit_run(k, x0, x1, 2.65, -0.53, ST2, STD)
    elif kind == 'Win_Duct':
        isolator(k, -0.27, 1.5, -0.53)
        junction_box(k, 0.27, 1.6, -0.53, STD, ST2, w=0.22, h=0.26, d=0.09)
        conduit_run(k, x0, x1, 2.65, -0.53, ST2, STD)
        bolt_row(k, -0.34, 0.34, 3.45, -1.1, 4, ST, s=0.024)                      # duct foot flange
    elif kind == 'Win_Sign':
        extinguisher(k, -0.27, 0.9, -0.53)
        junction_box(k, 0.27, 1.9, -0.53, STD, ST2, w=0.2, h=0.2, d=0.08)
        conduit_run(k, x0, x1, 2.65, -0.53, ST2, STD)
    elif kind == 'Win_Hose':
        bolt_row(k, -0.15, 0.15, 1.23, -0.75, 2, STD, s=0.022)
        bolt_row(k, -0.15, 0.15, 1.87, -0.75, 2, STD, s=0.022)
        k.bx(-0.208, -0.19, -0.77, -0.74, 1.25, 1.85, STD, ink=False)           # hinge
        isolator(k, -0.32, 1.55, -0.53)
        conduit_run(k, x0, x1, 2.65, -0.53, ST2, STD)
    elif kind in ('Panel', 'Win_Panel'):
        access_panel(k, -0.3, 0.0, 0.4, 0.85, -0.53, c='panel')                   # low inspection hatch
        k.bx(-0.373, -0.357, -0.79, -0.77, 1.05, 2.15, STD, ink=False)           # hinge strap on the door
        k.bx(0.0, 0.03, -0.8, -0.77, 1.45, 1.7, ST, ink=False)                    # door handle
        for z in (1.1, 1.5, 1.9):
            screw(k, 0.04, z, -0.783, STD, s=0.026)
        junction_box(k, 0.27, 2.2, -0.53, STD, ST2, w=0.2, h=0.2, d=0.08)
        k.cyl(0.27, -0.558, 2.3, 0.018, 0.018, 0.4, STD, seg=6, ink=False)


# ------------------------------------------------------------------ column
def column_detail(k):
    """Wall_Col: base plate anchor bolts and gussets, web stiffener plates, splice plates with screws, nameplate."""
    for sx in (-1, 1):
        for y in (-1.22, -0.58):
            k.bx(sx * 0.4 - 0.025, sx * 0.4 + 0.025, y - 0.025, y + 0.025, 0.077, 0.115, ST, ink=False)   # anchor nuts
        xa, xb = sorted((sx * 0.047, sx * 0.3))
        k.bx(xa, xb, -0.885, -0.855, 0.077, 0.55, 'orange2', ink=False)                                    # base gussets
    for z in (0.7, 4.0, 8.4, 12.0):                                              # web stiffeners between the flanges
        for sx in (-1, 1):
            xa, xb = sorted((sx * 0.047, sx * 0.335))
            k.bx(xa, xb, -1.083, -0.657, z, z + 0.02, 'orange2', ink=False)
    for z0, z1 in ((4.4, 5.1), (12.4, 13.1)):                                    # bolted splice plates on the front flange
        k.bx(-0.26, 0.26, -1.192, -1.177, z0, z1, ST2, ink=False)
        for x in (-0.18, 0.0, 0.18):
            for z in (z0 + 0.08, z1 - 0.08):
                screw(k, x, z, -1.192, STD, s=0.026)
    sign_plate(k, 0.0, 3.6, -1.18, 0.26, 0.3, 'cream', 'red')                    # column number plate
    for sx in (-1, 1):                                                            # flange tip guards at foot height
        xa, xb = sorted((sx * 0.343, sx * 0.358))
        k.bx(xa, xb, -1.17, -1.09, 0.1, 1.5, STD, ink=False)


# ------------------------------------------------------------------ gate
def gate_frame_detail(k):
    for s in (-1, 1):
        xa, xb = sorted((s * 1.47, s * 2.18))
        k.bx(xa, xb, -0.7, 0.7, 0.004, 0.05, STD, ink=False)                      # post base plates
        for f in (-1, 1):
            for x in (s * 1.57, s * 2.08):
                k.bx(x - 0.02, x + 0.02, f * 0.66 - 0.02, f * 0.66 + 0.02, 0.047, 0.09, ST, ink=False)
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        bolt_row(k, -0.6, 2.25, 3.74, -0.72, 6, STD, s=0.03)                      # header face fixings
        junction_box(k, -1.9, 3.7, -0.72, STD, ST2, w=0.4, h=0.3, d=0.1)          # roll-up motor box
        conduit_run(k, -1.65, -0.95, 3.7, -0.72, ST2, STD, every=0.35)             # to the photo-eye
        junction_box(k, -0.88, 3.7, -0.72, STD, ST2, w=0.12, h=0.12, d=0.06)
        k.pop()


def gate_shutter_detail(k):
    for s in (-1, 1):                                                             # guide rails with bolts
        xa, xb = sorted((s * 1.497, s * 1.43))
        k.bx(xa, xb, -0.075, 0.075, 0.008, 3.0, STD, ink=False)
        for z in (0.5, 1.0, 1.5, 2.0, 2.5):
            x = s * 1.463
            k.bx(x - 0.012, x + 0.012, -0.081, -0.072, z - 0.012, z + 0.012, ST, ink=False)
            k.bx(x - 0.012, x + 0.012, 0.072, 0.081, z - 0.012, z + 0.012, ST, ink=False)
    k.bx(-1.49, 1.49, -0.082, 0.082, 0.004, 0.05, 'rubber', ink=False)           # bottom seal
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        for x in (-0.16, 0.16):
            k.bx(x - 0.012, x + 0.012, -0.115, -0.07 + EMBED, 0.176, 0.194, STD, ink=False)
        k.bx(-0.18, 0.18, -0.12, -0.1, 0.17, 0.2, ST, ink=False)                  # pull handle
        k.pop()


# ------------------------------------------------------------------ weld cell
def arm_base_detail_at(k, x, y, deg):
    """Anchor bolts round a robot arm's base flange and a connector box (arm placed at x, y turned deg)."""
    k.push(x, y, deg)
    for a in (45, 135, 225, 315):
        bx, by = 0.37 * math.cos(math.radians(a)), 0.37 * math.sin(math.radians(a))
        k.bx(bx - 0.015, bx + 0.015, by - 0.015, by + 0.015, 0.177, 0.21, ST, ink=False)
    k.bx(-0.06, 0.06, 0.37, 0.47, 0.04, 0.14, STD, ink=False)
    k.pop()


def weld_cell_detail(k, kind):
    """Frame posts on base plates with anchor bolts, screen frames (bottom rails, rail fixings), jig table panels, clamps,
    gas bottle chain and regulators."""
    for (x, y) in ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9), (0, 1.9), (-1.9, 0), (1.9, 0)):
        k.bx(x - 0.09, x + 0.09, y - 0.09, y + 0.09, 0.004, 0.07, STD, ink=False)           # base plate
        for sx, sy in ((-1, -1), (1, 1)):
            k.bx(x + sx * 0.07 - 0.011, x + sx * 0.07 + 0.011, y + sy * 0.07 - 0.011, y + sy * 0.07 + 0.011, 0.067, 0.095, ST, ink=False)
    for (xa, xb, ya, yb) in ((-1.88, 1.88, 1.865, 1.935), (-1.935, -1.865, -1.86, 1.86), (1.865, 1.935, -1.86, 1.86)):
        k.bx(xa, xb, ya, yb, 0.09, 0.145, STD, ink=False)                                   # bottom rail of each screen
    # top-rail fixings (rail faces: back y = 1.86 looking -Y, sides x = -+1.86 looking inward)
    bolt_row(k, -1.7, -0.1, 2.406, 1.86, 4, ST, s=0.02)
    bolt_row(k, 0.1, 1.7, 2.406, 1.86, 4, ST, s=0.02)
    for sx, deg in ((-1.86, 90), (1.86, 270)):
        k.push(sx, 0, deg)
        bolt_row(k, -1.7, -0.1, 2.412, 0.0, 4, ST, s=0.02)
        bolt_row(k, 0.1, 1.7, 2.412, 0.0, 4, ST, s=0.02)
        k.pop()
    # jig table: front access panels, clamps, toe trim
    access_panel(k, -0.85, -0.25, 0.14, 0.62, -0.5, c='panel')
    access_panel(k, 0.0, 0.5, 0.14, 0.62, -0.5, c='panel')
    for x in (-0.9, 0.5):
        k.bx(x - 0.04, x + 0.04, -0.47, -0.39, 0.9 - EMBED, 0.98, STD, ink=False)           # toggle clamp base
        k.bx(x - 0.012, x + 0.012, -0.45, -0.37, 0.98, 1.02, ST, ink=False)
    arm_base_detail_at(k, 1.1, 1.0, 40)
    for x in (-1.55, -1.25):                                                                # gas bottles: regulator, valve
        k.cyl(x, 1.5, 1.3, 0.05, 0.05, 0.1, ST, seg=6, ink=False)
        k.bx(x - 0.04, x + 0.04, 1.455, 1.545, 1.4 - EMBED, 1.43, 'red', ink=False)
    k.bx(-1.69, -1.11, 1.36, 1.64, 0.85, 0.88, STD, ink=False)                              # safety chain strap


# ------------------------------------------------------------------ machines
def brake_detail(k):
    for x0, x1 in ((-1.35, -0.45), (0.45, 1.35)):
        access_panel(k, x0, x1, 0.12, 0.8, -0.35, c='panel')                                  # base cabinet doors
        access_panel(k, x0, x1 - 0.1, 1.95, 2.6, -0.25, c='panel')                            # ram covers
    for x in (-0.9, 0.9):                                                                     # hydraulic cylinders on the cap
        k.cyl(x, 0.0, 3.25 - EMBED, 0.15, 0.15, 0.3, STD, seg=8, ink=False)
        k.cyl(x, 0.0, 3.55 - EMBED, 0.1, 0.1, 0.05, ST2, seg=8, ink=False)
    k.cyl(-0.9, 0.0, 3.4, 0.022, 0.022, 1.8, 'hose', seg=6, ink=False, rot=(0, 90, 0))     # feed line between them
    for x in (-0.3, 0.3):
        k.bx(x - 0.025, x + 0.025, -0.045, 0.045, 3.25 - EMBED, 3.455, STD, ink=False)
    bolt_row(k, -1.85, 1.85, 3.12, -0.72, 9, ST, s=0.03)                                     # cap fixings
    for s in (-1, 1):                                                                         # hose runs up the posts
        x = s * 1.62
        k.cyl(x, -0.72, 0.92, 0.02, 0.02, 1.98, 'hose', seg=6, ink=False)
        for z in (1.3, 1.9, 2.5):
            k.bx(x - 0.03, x + 0.03, -0.76, -0.697, z, z + 0.04, STD, ink=False)
    framed_board(k, 1.45, 1.7, 1.35, 1.52, -1.0)                                              # control panel bezel
    for x in (1.45, 1.67):
        screw(k, x, 1.68, -1.0, STD, s=0.02)
        screw(k, x, 1.05, -1.0, STD, s=0.02)
    k.cyl(1.52, -1.0, 1.15, 0.028, 0.028, 0.02, STD, seg=8, ink=False, rot=(90, 0, 0))      # e-stop stem and mushroom
    k.cyl(1.52, -1.02, 1.15, 0.036, 0.036, 0.02, 'red', seg=8, ink=False, rot=(90, 0, 0))
    k.cyl(1.6, -0.9, 1.6, 0.02, 0.02, 0.06, STD, seg=6, ink=False)                          # cable gland on the panel top


def plasma_detail(k):
    for x0, x1 in ((-1.7, -0.95), (-0.55, 0.3), (0.75, 1.7)):
        access_panel(k, x0, x1, 0.12, 0.66, -0.9, c='panel')
    bolt_row(k, -1.85, 1.85, 0.9, -1.0, 12, STD, s=0.026)                                     # rail fixings
    k.push(1.9, 0, 90)                                                                        # +X end: service entry
    junction_box(k, -0.3, 0.45, 0.0, STD, ST2, w=0.3, h=0.36, d=0.12)
    isolator(k, 0.3, 0.45, 0.0)
    k.pop()
    for sy in (-1, 1):                                                                        # cable chain beside the gantry
        ya, yb = sorted((sy * 0.2, sy * 0.95))
        k.bx(0.547, 0.6, ya, yb, 1.4, 1.6, STD, ink=False)
        for i in range(6):
            y = sy * (0.27 + i * 0.12)
            k.bx(0.597, 0.606, y - 0.01, y + 0.01, 1.405, 1.595, ST2, ink=False)


# ------------------------------------------------------------------ chassis jigs, jig tiles, hatch, trail wall
def jig_scaffold_detail(k):
    for (x, y) in ((1.9, -1.6), (2.8, -1.6), (1.9, 1.6), (2.8, 1.6)):
        k.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.004, 0.04, STD, ink=False)                 # base plate
        for sx, sy in ((-1, -1), (1, 1)):
            k.bx(x + sx * 0.075 - 0.011, x + sx * 0.075 + 0.011, y + sy * 0.075 - 0.011, y + sy * 0.075 + 0.011, 0.037, 0.065, ST, ink=False)
    for z in (1.58, 3.08, 4.6):                                                                # toe boards round the decks
        for y in (-1.66, 1.66):
            k.bx(1.86, 2.84, y - 0.015, y + 0.015, z - EMBED, z + 0.1, 'hazard', ink=False)
        k.bx(2.84, 2.86, -1.64, 1.64, z - EMBED, z + 0.1, 'hazard', ink=False)
    for x in (1.9, 2.8):                                                                       # handrail on the top deck
        for y in (-1.62, 1.62):
            k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 4.59, 5.6, 'hazard', ink=False)
    for y in (-1.62, 1.62):
        for z in (5.1, 5.55):
            k.bx(1.9 + 0.03, 2.8 - 0.03, y - 0.02, y + 0.02, z, z + 0.05, 'hazard', ink=False)


def line_fence_detail(k, bolts=True):
    for f in (-1, 1):
        for x in (-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0):
            ya, yb = sorted((f * (3.62 - 0.1), f * (3.62 + 0.1)))
            k.bx(x - 0.1, x + 0.1, ya, yb, 0.004, 0.05, STD, ink=False)
            if bolts:
                for dx in (-0.075, 0.075):
                    k.bx(x + dx - 0.011, x + dx + 0.011, f * 3.62 - 0.011, f * 3.62 + 0.011, 0.047, 0.085, ST, ink=False)


def hatch_detail(k):
    for x in (-1.3, 1.3):
        for y in (1.05, 2.61):
            k.bx(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.137, 0.17, STD, ink=False)
            for sx, sy in ((-1, -1), (1, 1)):
                k.bx(x + sx * 0.09 - 0.011, x + sx * 0.09 + 0.011, y + sy * 0.09 - 0.011, y + sy * 0.09 + 0.011, 0.167, 0.2, ST, ink=False)


def trail_detail(k):
    """TrailWall, in its own local frame (corridor face looks -Y): kick rail, cap fixings, pipe collars, isolator."""
    base_trim(k, -0.5, 0.5, -0.283, STD, h=0.06, d=0.02, z0=0.27)
    bolt_row(k, -0.45, 0.45, 2.64, -0.31, 4, ST, s=0.022)
    for zz, r, yc in ((3.25, 0.1, -0.55), (3.62, 0.07, -0.52), (3.9, 0.05, -0.5)):
        pipe_collars(k, (-0.3, 0.3), yc, zz, r, -0.253)
    isolator(k, -0.27, 1.3, -0.283)
    junction_box(k, 0.27, 1.3, -0.283, STD, ST2, w=0.2, h=0.2, d=0.08)
