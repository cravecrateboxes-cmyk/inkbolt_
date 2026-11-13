"""kit-metro modelled detail (tactical look plan Stage 11): the real-station fixings, trims and service runs added to the
pieces the player sees most. Built on the kit_base detail helpers (all ink=False, 3 mm proud minimum, embedded 3 mm,
runs inset 5 mm from the piece sides); a few small local helpers where the station wants something the shared ones
do not draw. Everything here draws on the face that looks toward Blender -Y at the plane y = yf in the current frame
(use k.push(0, 0, 90) / k.push(0, 0, 270) for the +X / -X faces: the face plane is then y = -half width)."""
from kit_base import (PROUD, EMBED, bolt_row, rivet_strip, kick_plate, base_trim, cap_trim, drip_edge, corner_guard,
                      junction_box, vent, cable_tray, sign_plate, window_frame_depth)
from mt_base import SCHEMES, Y0


def hseam(k, x0, x1, z, yf, c, t=0.012, d=0.006):
    """a horizontal joint line, d proud, embedded, inset 5 mm"""
    k.bx(x0 + 0.005, x1 - 0.005, yf - d, yf + EMBED, z - t / 2, z + t / 2, c, ink=False)


def vseam(k, x, z0, z1, yf, c, t=0.012, d=0.006):
    k.bx(x - t / 2, x + t / 2, yf - d, yf + EMBED, z0, z1, c, ink=False)


# ------------------------------------------------------------------ wall faces
def wall_face(k, sch):
    """skirting with a cap, a dado rail, a cornice at the frieze top and (stone / tile uppers) coursing"""
    S = SCHEMES[sch]
    yf = Y0
    k.bx(-0.495, 0.495, yf - 0.012, yf + EMBED, 0.004, 0.15, S['skirt'], ink=False)
    k.bx(-0.492, 0.492, yf - 0.018, yf + 0.006, 0.146, 0.17, 'graph', ink=False)
    k.bx(-0.495, 0.495, yf - 0.014, yf + EMBED, 1.09, 1.13, S['line'], ink=False)
    cc = 'stoneD' if S['upper'] == 'stone' else S['frieze']
    k.bx(-0.495, 0.495, yf - 0.04, yf + EMBED, 7.7, 7.78, cc, ink=False)
    k.bx(-0.492, 0.492, yf - 0.025, yf + 0.006, 7.77, 7.84, cc, ink=False)
    if S['upper'] == 'stone':
        for z in (4.6, 5.3, 6.0, 6.7):
            hseam(k, -0.5, 0.5, z, yf, 'stoneD')
    elif S['upper'] == 'tileW':
        for z in (5.0, 6.0, 7.0):
            hseam(k, -0.5, 0.5, z, yf, 'grout')


def tray(k, x0, x1, z, yf, c, cable_c, d=0.1):
    """an open cable tray on the wall (bottom shelf, a front rail, two cables); parts overlap, never share a plane"""
    k.bx(x0, x1, yf - d, yf + EMBED, z, z + 0.01, c, ink=False)
    k.bx(x0 + 0.003, x1 - 0.003, yf - d - 0.004, yf - d + 0.006, z + 0.003, z + 0.06, c, ink=False)
    for i, off in enumerate((0.03, 0.065)):
        k.bx(x0 + 0.015, x1 - 0.015, yf - off - 0.012, yf - off + 0.012, z + 0.008 + i * 0.004, z + 0.036 + i * 0.004, cable_c, ink=False)


# ------------------------------------------------------------------ platform edge
def edge_detail(k, b):
    """tactile warning ribs on the yellow strip and a cable tray on the trackside face"""
    n = max(2, int((b + 0.5) / 0.1))
    for i in range(n):
        x = -0.5 + (b + 0.5) * (i + 0.5) / n
        if x - 0.012 < -0.495 or x + 0.012 > b - 0.005:
            continue
        k.bx(x - 0.012, x + 0.012, Y0 + 0.275, Y0 + 0.345, 0.009, 0.019, 'stoneD', ink=False)
    tray(k, -0.495, 0.495, -0.62, Y0, 'steelD', 'black')


# ------------------------------------------------------------------ doors
def door_leaf_detail(k, yl, sign=True):
    """hinges, a kick plate over the chrome strip, a door closer and a threshold strip; yl = the leaf plane"""
    for z in (0.35, 1.1, 1.85):
        k.bx(-0.45, -0.405, yl - 0.012, yl + EMBED, z - 0.05, z + 0.05, 'steelD', ink=False)
    kick_plate(k, -0.4, 0.4, yl, 'steelD', h=0.3, z0=0.0, bolts='chrome')
    k.bx(-0.2, 0.2, yl - 0.02, yl + EMBED, 2.14, 2.2, 'steelD', ink=False)      # door closer body
    k.bx(-0.46, 0.46, yl - 0.04, yl + 0.007, 0.0, 0.008, 'steelD', ink=False)   # threshold strip


def lift_detail(k, part):
    y = Y0 - 0.01
    if part == 'L':
        kick_plate(k, -0.4, 0.465, y, 'steelD', h=0.22, bolts='chrome')
    else:
        kick_plate(k, -0.465, 0.4, y, 'steelD', h=0.22, bolts='chrome')
        window_frame_depth(k, 0.22, 0.38, 1.0, 1.3, y, 'steelD', depth=0.018, t=0.02)
        window_frame_depth(k, -0.299, 0.299, 2.381, 2.579, Y0, 'steelD', depth=0.045, t=0.03)


def doorway(k, H):
    """sliding-door head cover with sensor, kick plates and a floor track"""
    k.bx(-0.915, 0.915, -0.112, -0.097, H - 0.1, H - 0.02, 'steelD', ink=False)
    k.bx(-0.12, 0.12, -0.134, -0.109, H - 0.085, H - 0.035, 'black', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * 0.52, s * 0.9))
        kick_plate(k, a, b, -0.12, 'steelD', h=0.2, z0=0.02)
    k.bx(-0.915, 0.915, -0.05, 0.05, 0.0, 0.012, 'steelD', ink=False)


def kiosk_front(k, H):
    rivet_strip(k, -1.44, 1.44, H + 0.225, -0.35, 'steelD', every=0.3, s=0.02)
    k.bx(-1.495, -1.44, -0.4, -0.35 + EMBED, H + 0.003, H + 0.247, 'steelD', ink=False)   # box end plates
    k.bx(1.44, 1.495, -0.4, -0.35 + EMBED, H + 0.003, H + 0.247, 'steelD', ink=False)


# ------------------------------------------------------------------ fixtures
def fare_gate(k, L):
    for sx in (-1, 1):
        k.push(0, 0, 90 if sx > 0 else 270)
        kick_plate(k, -L + 0.06, L - 0.06, -0.16, 'steelD', h=0.18, bolts='chrome')
        k.pop()
    k.bx(-0.09, 0.09, -0.19, -0.1, 1.117, 1.15, 'graph', ink=False)           # card reader pad on top


def tvm_front(k, x, yf):
    """one machine: screen frame, kick plate with bolts, a louvred vent; yf = the machine's front plane"""
    window_frame_depth(k, x - 0.32, x + 0.32, 1.12, 1.6, yf, 'steelD', depth=0.026, t=0.03)
    kick_plate(k, x - 0.425, x + 0.425, yf, 'steelD', h=0.2, bolts='chrome')
    vent(k, x, 0.38, yf, 0.4, 0.16, 'steelD', 'black', n=3)


def tvm_wall_bank(k):
    for x in (-0.95, 0.0, 0.95):
        tvm_front(k, x, 0.0)


def tvm_island(k):
    for s in (0, 180):
        k.push(0, 0, s)
        for x in (-0.95, 0.0, 0.95):
            tvm_front(k, x, -0.45)
        k.pop()
    for e in (-1, 1):                  # kick plates on the end panels (their faces at x = +-1.9)
        k.push(0, 0, 90 if e > 0 else 270)
        kick_plate(k, -0.44, 0.44, -1.9, 'steelD', h=0.2, bolts='chrome')
        k.pop()


def bench(k):
    """foot plates on the cast legs, a bolt row on the back rail, a top rail"""
    for x in (-1.2, 1.2):
        k.bx(x - 0.09, x + 0.09, -0.24, 0.24, 0.0, 0.016, 'steelD', ink=False)
    bolt_row(k, -1.35, 1.35, 0.76, 0.18, 6, 'steelD', s=0.024)
    bolt_row(k, -1.35, 1.35, 0.54, 0.18, 6, 'steelD', s=0.024)
    k.bx(-1.445, 1.445, 0.17, 0.25, 0.846, 0.872, 'steelD', ink=False)           # top rail of the back
    for x in (-1.0, 1.0):
        vseam(k, x, 0.48, 0.846, 0.18, 'steelD', t=0.016, d=0.01)               # back-rest stiffeners


def help_point(k):
    kick_plate(k, -0.175, 0.175, -0.12, 'steelD', h=0.16, bolts='chrome')
    for z in (0.9, 1.6):
        bolt_row(k, -0.12, 0.12, z, -0.12, 2, 'steelD', s=0.02)
    cap_trim(k, -0.18, 0.18, -0.12, 1.9, 'steelD', h=0.05, d=0.02)
    # back face
    k.push(0, 0, 180)
    kick_plate(k, -0.175, 0.175, -0.12, 'steelD', h=0.16)
    k.pop()


def map_totem(k):
    for s in (0, 180):
        k.push(0, 0, s)
        window_frame_depth(k, -0.36, 0.36, 0.7, 1.95, -0.12, 'steelD', depth=0.03, t=0.03)
        kick_plate(k, -0.415, 0.415, -0.12, 'steelD', h=0.2, bolts='chrome')
        k.pop()


def column(k):
    for s in (0, 180):
        k.push(0, 0, s)
        yf = -0.18
        for e in (-1, 1):             # steel angle round each vertical corner
            a, b = sorted((e * 0.453, e * 0.40))
            k.bx(a, b, yf - 0.01, yf + EMBED, 0.34, 2.56, 'steel', ink=False)
        drip_edge(k, -0.44, 0.44, 2.58, yf, 'steelD', d=0.03, t=0.03)
        bolt_row(k, -0.34, 0.34, 0.5, yf, 4, 'steelD', s=0.022)
        bolt_row(k, -0.34, 0.34, 2.46, yf, 4, 'steelD', s=0.022)
        k.pop()
    # service box on the side of the shaft
    k.push(0, 0, 90)
    junction_box(k, 0.0, 0.5, -0.45, 'graph', 'steelD', w=0.2, h=0.26, d=0.07)
    k.pop()


def vend(k):
    yf = -0.38
    window_frame_depth(k, -0.38, 0.12, 0.75, 1.8, yf, 'steelD', depth=0.03, t=0.03)
    window_frame_depth(k, 0.18, 0.38, 1.2, 1.5, yf, 'steelD', depth=0.025, t=0.02)
    kick_plate(k, -0.44, 0.44, yf, 'steelD', h=0.12, bolts='chrome')


def elec_cab(k, x0):
    yf = -0.3
    kick_plate(k, x0 + 0.01, x0 + 0.92, yf, 'steelD', h=0.09)
    vent(k, x0 + 0.465, 0.4, yf, 0.44, 0.2, 'steelD', 'black', n=3)
    cap_trim(k, x0 + 0.005, x0 + 0.925, yf, 2.0, 'steelD', h=0.07, d=0.03)


def lockers(k):
    yf = -0.2
    kick_plate(k, -0.94, 0.94, yf, 'graph', h=0.08)
    cap_trim(k, -0.94, 0.94, yf, 1.95, 'graph', h=0.07, d=0.025)


def sign_fascia(k):
    cap_trim(k, -3.45, 3.45, -0.68, 0.55, 'steelD', h=0.045, d=0.03)
    k.bx(-3.453, -3.40, -0.7, -0.68 + EMBED, 0.004, 0.496, 'steelD', ink=False)
    k.bx(3.40, 3.453, -0.7, -0.68 + EMBED, 0.004, 0.496, 'steelD', ink=False)


def shop_plinth(k, xa, xb):
    base_trim(k, xa, xb, Y0, 'steelD', h=0.1, d=0.02)


def counter(k):
    base_trim(k, -1.4, 1.4, -0.35, 'graph', h=0.1, d=0.02)


def cafe_bar(k):
    base_trim(k, -1.95, 1.95, -0.6, 'graph', h=0.1, d=0.02)
