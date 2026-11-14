"""kit-police modelled detail (tactical look plan Stage 11): fittings of a clean but used special-forces base, added
to the pieces the player sees most. Every part is hull='none' (no outline shell), stands >= 3 mm proud of what it sits
on, is embedded 3 mm, and horizontal runs on wall modules stop 6 cm short of the module ends (concave corners).
The kit models are PM (fam_kit_smallcity) instances, so the helpers take the model `m` first."""
from kit_base import PROUD, EMBED


def B(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def bolts(m, xs, z, yf, c='chrome', s=0.022, cull='k'):
    """bolt heads on a -Y facing face at y = yf"""
    for x in xs:
        B(m, x - s / 2, x + s / 2, yf - PROUD - 0.004, yf + EMBED, z - s / 2, z + s / 2, c, cull)


def bolts_z(m, x, zs, yf, c='chrome', s=0.022):
    for z in zs:
        B(m, x - s / 2, x + s / 2, yf - PROUD - 0.004, yf + EMBED, z - s / 2, z + s / 2, c, 'k')


# ------------------------------------------------------------------ wall modules
RAIL = {'A': (0.82, 0.90, 'steel2'), 'G': (0.74, 0.82, 'steel2'), 'C': (0.9, 0.98, 'steel')}
PLATE = {'L': 'white', 'O': 'white', 'A': 'steel', 'G': 'blue', 'C': 'steel'}


def wall_fit(m, S, fy):
    """low fittings on every wall module: double socket + data plate, and a wall-protection rail with a dark insert
    in the armory, garage and cell blocks (fy(z) = y of the wall face at height z)"""
    if S == 'R':
        return
    y = fy(0.3)
    pc = PLATE[S]
    B(m, -0.34, -0.25, y - 0.008, y + EMBED, 0.30, 0.39, pc, 'k')
    for x in (-0.322, -0.278):
        B(m, x - 0.01, x + 0.01, y - 0.012, y - 0.005, 0.325, 0.365, 'black', 'k')
    B(m, 0.25, 0.32, y - 0.008, y + EMBED, 0.30, 0.37, pc, 'k')
    for x in (0.272, 0.298):
        B(m, x - 0.009, x + 0.009, y - 0.012, y - 0.005, 0.318, 0.352, 'black', 'k')
    if S in RAIL:
        z0, z1, c = RAIL[S]
        y = fy(z0)
        B(m, -0.44, 0.44, y - 0.016, y + EMBED, z0, z1, c, 'k')
        B(m, -0.43, 0.43, y - 0.022, y - 0.013, z0 + 0.02, z1 - 0.02, 'black', 'k')


def wall_top(m, S, fy):
    """plain modules only: a conduit run with clips into a junction box under the ceiling band"""
    y = fy(3.3)
    r = 0.02
    m.cy((-0.44, y - r - 0.006, 3.3), r, r, 0.74, 'steel2', seg=6, rot=(0, 90, 0), hull='none')
    for x in (-0.36, -0.02, 0.26):
        B(m, x - 0.015, x + 0.015, y - 2 * r - 0.012, y + EMBED, 3.3 - r - 0.008, 3.3 + r + 0.008, 'steel', 'k')
    B(m, 0.3, 0.42, y - 0.045, y + EMBED, 3.22, 3.38, 'steel2', 'k')
    B(m, 0.32, 0.40, y - 0.05, y - 0.042, 3.24, 3.36, 'steel', 'k')


def call_point(m, S, fy):
    """fire alarm manual call point (red box, white glass, black button)"""
    y = fy(1.4)
    B(m, 0.26, 0.40, y - 0.035, y + EMBED, 1.34, 1.52, 'red', 'k')
    B(m, 0.29, 0.37, y - 0.04, y - 0.033, 1.40, 1.48, 'white', 'k')
    B(m, 0.325, 0.335, y - 0.045, y - 0.038, 1.43, 1.45, 'ink', 'k')


def door_fit(m, y):
    """door leaf at front y: hinges, lock escutcheon, closer, vision-panel bead and a casing cap on the head
    (leaf front is y - 0.005)"""
    for z in (0.35, 1.1, 1.85):
        B(m, -0.384, -0.34, y - 0.012, y - 0.002, z - 0.06, z + 0.06, 'ink', 'k')
    B(m, 0.31, 0.38, y - 0.012, y - 0.002, 0.9, 1.1, 'ink', 'k')
    m.cy((0.345, y - 0.009, 0.97), 0.014, 0.014, 0.008, 'chrome', seg=8, rot=(90, 0, 0), hull='none')
    B(m, 0.08, 0.3, y - 0.02, y - 0.002, 2.1, 2.2, 'ink', 'k')                       # closer body
    B(m, -0.145, -0.127, y - 0.018, y - 0.005, 1.335, 1.865, 'steel', 'k')           # bead round the glass
    B(m, 0.127, 0.145, y - 0.018, y - 0.005, 1.335, 1.865, 'steel', 'k')
    B(m, -0.127, 0.127, y - 0.018, y - 0.005, 1.335, 1.355, 'steel', 'k')
    B(m, -0.127, 0.127, y - 0.018, y - 0.005, 1.845, 1.865, 'steel', 'k')
    B(m, -0.435, 0.435, y - 0.035, y + 0.003, 2.297, 2.35, 'ink', 'k')              # casing cap over the frame


def corner_guard_post(m, S, STY):
    """steel / hazard angle guards on the four vertical edges of a corner post, inside the dado band"""
    z0, z1, c, dd = STY[S][1]
    h = 0.5 - (0.08 - dd)
    g0, g1 = z0 + 0.12, min(z1 - 0.05, 1.4)
    col = 'yellow' if S in 'AG' else 'steel'
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * h, sy * h
            xa = sorted((cx - sx * 0.06, cx + sx * 0.008))
            ya = sorted((cy + sy * 0.008, cy - sy * 0.003))
            B(m, xa[0], xa[1], ya[0], ya[1], g0, g1, col)
            xb = sorted((cx + sx * 0.008, cx - sx * 0.003))
            yb = sorted((cy - sy * 0.003, cy - sy * 0.06))
            B(m, xb[0], xb[1], yb[0], yb[1], g0, g1, col)


# ------------------------------------------------------------------ armory
def cage_fit(m, y):
    """armoury cage: padlock on a hasp, hinge straps, corner bolts (frame front is y - 0.05)"""
    yf = y - 0.05
    B(m, 0.39, 0.43, yf - 0.008, yf + EMBED, 2.0, 2.14, 'steel', 'k')              # hasp plate
    B(m, 0.395, 0.425, yf - 0.026, yf - 0.006, 1.88, 2.0, 'gold', 'k')             # padlock body
    B(m, 0.403, 0.417, yf - 0.022, yf - 0.006, 1.99, 2.05, 'black', 'k')            # shackle
    for z in (1.55, 2.15, 2.75):
        B(m, -0.435, -0.385, yf - 0.01, yf + EMBED, z - 0.05, z + 0.05, 'black', 'k')
    bolts(m, (-0.41, 0.41), 1.33, yf, 'chrome', s=0.02)
    bolts(m, (-0.41, 0.41), 3.02, yf, 'chrome', s=0.02)


def rack_fit(m, slot_x, slot_z):
    """weapon wall: steel border round every slot panel with corner bolts, drawer label cards and padlock hasps,
    bolts down the posts (guns, pegs and the slot panels themselves are untouched)"""
    for x in slot_x:
        for z in slot_z:
            for a, b in ((x - 0.655, x - 0.63), (x + 0.63, x + 0.655)):
                B(m, a, b, 0.440, 0.4505, z - 0.325, z + 0.295, 'steel2', 'k')
            B(m, x - 0.63, x + 0.63, 0.440, 0.4505, z + 0.27, z + 0.295, 'steel2', 'k')
            for bx_ in (x - 0.6425, x + 0.6425):
                for bz in (z - 0.295, z + 0.235):
                    B(m, bx_ - 0.0075, bx_ + 0.0075, 0.432, 0.443, bz - 0.01, bz + 0.01, 'chrome', 'k')
    for x in slot_x:
        for k in range(3):
            z0 = 0.09 + k * 0.175
            B(m, x - 0.60, x - 0.40, 0.012, 0.018, z0 + 0.04, z0 + 0.10, 'paper', 'k')
            B(m, x - 0.575, x - 0.43, 0.009, 0.013, z0 + 0.065, z0 + 0.075, 'ink', 'k')
        z0 = 0.09
        B(m, x + 0.48, x + 0.60, 0.007, 0.018, z0 + 0.09, z0 + 0.13, 'steel', 'k')   # hasp
        B(m, x + 0.51, x + 0.57, -0.012, 0.008, z0 + 0.03, z0 + 0.095, 'gold', 'k')  # padlock
        B(m, x + 0.53, x + 0.55, -0.006, 0.0, z0 + 0.095, z0 + 0.135, 'black', 'k')  # shackle
    for sx in (-1, 1):
        bolts_z(m, sx * 1.46, (0.4, 1.0, 1.6), 0.36, 'chrome', s=0.024)


def locker_fit(m):
    for sx in (-1, 1):
        x = sx * 0.225
        for z in (0.2, 0.26, 0.32):                                                  # low vent slits
            B(m, x - 0.1, x + 0.1, -0.241, -0.232, z, z + 0.02, 'ink', 'k')
        B(m, x - 0.035, x + 0.035, -0.239, -0.232, 1.89, 1.935, 'chrome', 'k')       # number plate
        B(m, x - 0.022, x - 0.006, -0.243, -0.238, 1.9, 1.925, 'ink', 'k')
        B(m, x + 0.006, x + 0.022, -0.243, -0.238, 1.9, 1.925, 'ink', 'k')
        hx = x - sx * 0.16
        B(m, hx - 0.02, hx + 0.02, -0.239, -0.232, 1.19, 1.23, 'black', 'k')         # lock
        ox = sx * 0.418
        for z in (0.3, 1.0, 1.7):                                                    # hinges on the outer edge
            B(m, ox - 0.015, ox + 0.015, -0.238, -0.232, z - 0.04, z + 0.04, 'steel2', 'k')


# ------------------------------------------------------------------ desks, tables, benches
def edge_band(m, x0, x1, y0, y1, z0, z1, c, ends=True):
    """banding round a table top spanning x0..x1, y0..y1, z0..z1 (3 mm proud, inset 5 mm along each side)"""
    B(m, x0 + 0.005, x1 - 0.005, y0 - 0.003, y0 + 0.003, z0 + 0.003, z1 - 0.003, c)
    B(m, x0 + 0.005, x1 - 0.005, y1 - 0.003, y1 + 0.003, z0 + 0.003, z1 - 0.003, c)
    if ends:
        B(m, x0 - 0.003, x0 + 0.003, y0 + 0.006, y1 - 0.006, z0 + 0.003, z1 - 0.003, c)
        B(m, x1 - 0.003, x1 + 0.003, y0 + 0.006, y1 - 0.006, z0 + 0.003, z1 - 0.003, c)


def grommet(m, x, y, z, w=0.06, d=0.06):
    B(m, x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + 0.007, 'black')


def desk_fit(m):
    edge_band(m, -0.9, 0.9, -0.4, 0.4, 0.72, 0.76, 'oak2')
    for y in (-0.285, 0.285):
        grommet(m, 0.04, y, 0.757, 0.05, 0.05)
    for sx in (-0.86, 0.86):
        B(m, sx - 0.035, sx + 0.035, -0.365, 0.365, 0.004, 0.02, 'black')


def ops_fit(m):
    B(m, -1.895, 1.895, -0.058, -0.047, 0.004, 0.08, 'black', 'k')                 # toe kick
    for x in (-1.24, -0.62, 0.0, 0.62, 1.24):
        grommet(m, x, 0.36, 0.77, 0.05, 0.05)
    for sx in (-0.95, 0.95):                                                         # screen brackets
        B(m, sx - 0.6, sx + 0.6, 0.40, 0.49, 1.416, 1.453, 'steel2', 'k')


def brief_fit(m):
    edge_band(m, -1.85, 1.85, 0.1, 0.75, 0.72, 0.77, 'oak2')
    for x in (0.0, 0.9):                                                             # power / data flip covers
        B(m, x - 0.07, x + 0.07, 0.56, 0.68, 0.767, 0.774, 'steel2')
        B(m, x - 0.05, x + 0.05, 0.58, 0.66, 0.771, 0.778, 'black')
    for sx in (-1.75, 1.75):
        B(m, sx - 0.035, sx + 0.035, 0.155, 0.695, 0.004, 0.02, 'black')


def bench_fit(m):
    edge_band(m, -0.95, 0.95, -0.42, 0.42, 0.86, 0.92, 'steel2')
    for sx in (-0.88, 0.88):
        for sy in (-0.36, 0.36):
            B(m, sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.004, 0.02, 'black')
    B(m, 0.35, 0.8, 0.394, 0.403, 1.1, 1.16, 'black', 'k')                           # power strip on the riser board
    for k in range(4):
        B(m, 0.4 + k * 0.1 - 0.02, 0.4 + k * 0.1 + 0.02, 0.39, 0.397, 1.115, 1.145, 'light', 'k')
    # tool silhouettes on the pegboard: hammer, spanner, screwdriver
    B(m, -0.612, -0.588, 0.397, 0.403, 1.0, 1.28, 'ink', 'k')
    B(m, -0.65, -0.55, 0.397, 0.403, 1.28, 1.32, 'ink', 'k')
    B(m, -0.312, -0.288, 0.397, 0.403, 1.0, 1.25, 'ink', 'k')
    B(m, -0.34, -0.26, 0.397, 0.403, 1.25, 1.33, 'ink', 'k')
    B(m, -0.108, -0.092, 0.397, 0.403, 1.0, 1.3, 'ink', 'k')


def shelf_fit(m, tops):
    for top in tops:
        B(m, -0.8, -0.6, -0.029, -0.022, top - 0.045, top - 0.017, 'paper', 'k')    # label card on the shelf lip
        B(m, -0.77, -0.63, -0.032, -0.028, top - 0.035, top - 0.027, 'ink', 'k')
    for sx in (-0.95, 0.95):
        bolts_z(m, sx, (0.47, 0.93, 1.4, 1.88), -0.025, 'chrome', s=0.022)


def frontdesk_fit(m):
    edge_band(m, -2.95, 2.95, -0.65, -0.2, 1.05, 1.1, 'oak2')
    edge_band(m, -2.6, 2.6, 0.35, 0.75, 0.72, 0.76, 'oak', ends=False)
    for x in (-0.8, 0.8):
        grommet(m, x, 0.46, 0.76)
    for x in (-2.4, -0.7, 0.7, 2.4):                                                 # panel seams on the counter front
        B(m, x - 0.006, x + 0.006, -0.554, -0.547, 0.19, 0.84, 'navy2', 'k')


# ------------------------------------------------------------------ vehicles, doors
def van_fit(m):
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.147, sx * 1.163))
        for y0, y1 in ((-0.78, -0.68), (-0.52, -0.42)):                              # door handles
            B(m, x0, x1, y0, y1, 1.3, 1.35, 'chrome')
    B(m, -0.25, 0.25, 2.747, 2.756, 0.48, 0.58, 'white', 'f')                        # rear plate
    B(m, -0.15, 0.15, 2.756, 2.760, 0.51, 0.55, 'ink', 'f')
    for z in (0.78, 0.88, 0.98):                                                     # grille slats
        B(m, -0.5, 0.5, -2.884, -2.877, z, z + 0.04, 'steel2', 'k')
    for y in (0.2, 1.0, 1.8):                                                        # roof rack cross bars
        B(m, -0.885, 0.885, y - 0.03, y + 0.03, 2.457, 2.5, 'black')
    m.cy((0.8, 2.42, 2.4), 0.012, 0.012, 0.5, 'ink', seg=5, hull='none')


def roller_fit(m, part, a, b):
    """roller door: bottom seal bar, guide-rail bolts, header bolts (+ a rating plate on the middle module)"""
    B(m, a + 0.005, b - 0.005, -0.456, -0.447, 0.004, 0.05, 'black', 'k')
    xs = {'L': -0.42, 'R': 0.42}.get(part)
    if xs is not None:
        bolts_z(m, xs, (0.35, 0.95, 1.6, 2.2, 2.8), -0.5, 'steel', s=0.026)
    n = 3 if part != 'M' else 2
    span = (b - a) - 0.2
    for i in range(n):
        x = a + 0.1 + span * (i + 0.5) / n if part != 'M' else (-0.3 if i == 0 else 0.3)
        bolts(m, [x], 3.45, -0.54, 'steel', s=0.026)
    if part == 'M':
        B(m, -0.1, 0.1, -0.546, -0.537, 3.38, 3.52, 'paper', 'k')
        B(m, -0.07, 0.07, -0.549, -0.545, 3.43, 3.46, 'ink', 'k')
