"""kit-academy modelled-detail pass (tactical look plan Stage 11; see docs/tactical-look/KIT-BRIEF.md).

Nothing in ac_struct / ac_rooms / ac_gym changes: install(k) wraps the kit's finish() (a piece's detail is drawn
just before it is finished), chair() and legs4() (rubber feet, bolts). All parts are ink=False, at least 3 mm
proud, 3 mm embedded, horizontal runs 5 mm short of the piece's sides. Bright and tidy: a few fixings per piece.
"""
from ac_base import *  # noqa: F401,F403
import kit_base as KB
from kit_base import PROUD, EMBED, bolt_row, base_trim, cap_trim, drip_edge, panel_seams, sign_plate  # noqa: F401

Y0 = -0.5


def B(k, x0, x1, y0, y1, z0, z1, c):
    k.bx(x0, x1, y0, y1, z0, z1, c, ink=False)


def edge_band(k, x0, x1, y0, y1, z0, z1, c='woodD', t=0.004):
    """a slim edge band round a table top (z0..z1 its thickness): four strips, 4 mm proud, 3 mm embedded"""
    zz0, zz1 = z0 + 0.004, z1 - 0.004
    B(k, x0 + 0.005, x1 - 0.005, y0 - t, y0 + EMBED, zz0, zz1, c)
    B(k, x0 + 0.005, x1 - 0.005, y1 - EMBED, y1 + t, zz0, zz1, c)
    B(k, x0 - t, x0 + EMBED, y0 + 0.005, y1 - 0.005, zz0, zz1, c)
    B(k, x1 - EMBED, x1 + t, y0 + 0.005, y1 - 0.005, zz0, zz1, c)


def pull(k, x, y, z0, z1, c='chrome', w=0.03, d=0.016, face=-1):
    """a vertical bar pull on a face at y (face -1 looks toward -Y)"""
    if face < 0:
        B(k, x - w / 2, x + w / 2, y - d, y + EMBED, z0, z1, c)
    else:
        B(k, x - w / 2, x + w / 2, y - EMBED, y + d, z0, z1, c)


# ---------------------------------------------------------------- walls
def d_I(k):
    # rubber cove base proud with a top bead, a wall-protection rail at hand height
    base_trim(k, -0.5, 0.5, Y0, 'cove', h=0.12, d=0.014)
    B(k, -0.495, 0.495, Y0 - 0.018, Y0 + EMBED, 0.124, 0.138, 'stoneD')
    B(k, -0.495, 0.495, Y0 - 0.03, Y0 + EMBED, 0.86, 0.98, 'cove')
    B(k, -0.485, 0.485, Y0 - 0.034, Y0 - 0.026, 0.9, 0.94, 'steelD')


def d_X(k):
    drip_edge(k, -0.495, 0.495, 0.6 + 0.012, Y0, 'stone', d=0.035, t=0.024)
    drip_edge(k, -0.495, 0.495, 4.1 + 0.012, Y0, 'stone', d=0.035, t=0.024)


def d_lockers(k):
    # plinth, vent slats, pulls, number plates
    B(k, -0.495, 0.495, Y0 - 0.02, Y0 + EMBED, 0.004, 0.15, 'cove')
    for i in range(3):
        a = -0.5 + i / 3 + 0.012
        b = -0.5 + (i + 1) / 3 - 0.012
        for z in (1.74, 1.80, 1.86):
            B(k, a + 0.09, b - 0.09, Y0 - 0.011, Y0 - 0.003, z, z + 0.014, 'black')
        pull(k, b - 0.06, Y0 - 0.003, 0.97, 1.13, 'chrome', w=0.02, d=0.016)
        sign_plate(k, (a + b) / 2, 1.58, Y0 - 0.003, 0.09, 0.05, 'paper', None)
        B(k, (a + b) / 2 - 0.02, (a + b) / 2 + 0.02, Y0 - 0.017, Y0 - 0.008, 1.57, 1.59, 'navy')


def d_cork(k):
    # proper frame round the cork and a pen ledge
    B(k, -0.455, 0.455, Y0 - 0.036, Y0 - 0.017, 1.95, 1.99, 'woodD')
    B(k, -0.455, 0.455, Y0 - 0.036, Y0 - 0.017, 0.96, 1.0, 'woodD')
    B(k, -0.46, -0.42, Y0 - 0.036, Y0 - 0.017, 1.0, 1.95, 'woodD')
    B(k, 0.42, 0.46, Y0 - 0.036, Y0 - 0.017, 1.0, 1.95, 'woodD')
    B(k, -0.4, 0.4, Y0 - 0.05, Y0 + EMBED, 0.935, 0.955, 'wood')
    for x in (-0.28, 0.16):
        B(k, x - 0.008, x + 0.008, Y0 - 0.034, Y0 - 0.026, 1.9, 1.92, 'chD')


def d_fireext(k):
    # fire alarm point (call point) and a double socket plate
    B(k, -0.42, -0.32, Y0 - 0.04, Y0 + EMBED, 1.28, 1.44, 'chD')
    B(k, -0.395, -0.345, Y0 - 0.05, Y0 - 0.037, 1.33, 1.39, 'paper')
    B(k, -0.385, -0.355, Y0 - 0.056, Y0 - 0.047, 1.35, 1.37, 'chD')
    B(k, 0.30, 0.42, Y0 - 0.012, Y0 + EMBED, 0.32, 0.40, 'trimW')
    for x in (0.335, 0.385):
        B(k, x - 0.012, x + 0.012, Y0 - 0.02, Y0 - 0.009, 0.345, 0.375, 'steelD')


def d_pad(k):
    # wall pad: vertical seams, a cross seam, hanging cleat
    for x in (-0.165, 0.165):
        B(k, x - 0.006, x + 0.006, Y0 - 0.066, Y0 - 0.057, 0.305, 1.88, 'navy')
        B(k, x - 0.006, x + 0.006, Y0 - 0.066, Y0 - 0.057, 1.99, 2.195, 'navy')
    for z in (0.7, 1.18):
        for x0, x1 in ((-0.485, -0.171), (-0.159, 0.159), (0.171, 0.485)):
            B(k, x0, x1, Y0 - 0.066, Y0 - 0.057, z, z + 0.02, 'navy')
    for x in (-0.4, 0.4):
        B(k, x - 0.02, x + 0.02, Y0 - 0.07, Y0 - 0.057, 2.12, 2.16, 'steelD')


def d_closed_door(k):
    # closer, kick-plate screws, a door stop strip
    B(k, 0.04, 0.3, Y0 - 0.016, Y0 + 0.013, 2.06, 2.14, 'steel')
    B(k, -0.1, 0.04, Y0 - 0.012, Y0 + 0.013, 2.09, 2.11, 'steel')
    for x in (-0.3, -0.1, 0.1, 0.3):
        B(k, x - 0.008, x + 0.008, Y0 - 0.002, Y0 + 0.010, 0.21, 0.226, 'steelD')
    for z in (0.35, 1.0, 1.75):
        B(k, -0.455, -0.435, Y0 - 0.036, Y0 - 0.026, z, z + 0.12, 'black')


# ---------------------------------------------------------------- doors
def casing(k, W, H):
    for side in (0, 180):
        k.push(0, 0, side)
        h = W / 2
        B(k, -h + 0.005, h - 0.005, Y0 - 0.02, Y0 + 0.045, H - 0.004, H + 0.06, 'steelD')
        for s in (-1, 1):
            a, b = sorted((s * h, s * (h - 0.065)))
            B(k, a, b, Y0 - 0.02, Y0 + 0.045, 0.004, H - 0.004, 'steelD')
        k.pop()


def d_door2(k):
    casing(k, 2.0, DOOR_H)
    # leaves lie against the back face (y 0.512 - 0.557): vision-panel frames, push bars
    for x0, x1 in ((1.0, 1.96), (-1.96, -1.0)):
        xm, w = (x0 + x1) / 2, x1 - x0
        a, b = xm - w * 0.22, xm + w * 0.22
        yf = 0.557
        for (xa, xb, za, zb) in ((a - 0.04, b + 0.04, 2.0, 2.04), (a - 0.04, b + 0.04, 1.21, 1.25), (a - 0.04, a, 1.25, 2.0), (b, b + 0.04, 1.25, 2.0)):
            B(k, xa, xb, yf - EMBED, yf + 0.012, za, zb, 'steelD')
        B(k, xm - 0.18, xm + 0.18, yf - EMBED, yf + 0.028, 1.0, 1.04, 'chrome')


def d_door3(k):
    casing(k, 3.0, DOOR_H)
    for s in (-1, 1):
        a = s * 1.5
        xa, xb = sorted((a + s * 0.15, a + s * 0.6))
        yf = 0.5 + 0.05 + 0.046
        for (x0, x1, z0, z1) in ((xa - 0.04, xb + 0.04, 2.2, 2.24), (xa - 0.04, xb + 0.04, 0.86, 0.9), (xa - 0.04, xa, 0.9, 2.2), (xb, xb + 0.04, 0.9, 2.2)):
            B(k, x0, x1, yf - EMBED, yf + 0.012, z0, z1, 'steelD')
        xm = (xa + xb) / 2
        B(k, xm - 0.2, xm + 0.2, yf - EMBED, yf + 0.032, 1.0, 1.04, 'chrome')


# ---------------------------------------------------------------- stairs, columns
def d_stair(k):
    Wd, L, n = 1.7, 7.0, 25
    y0 = -L / 2
    for i in range(n):
        top = (i + 1) * RISE
        a = y0 + i * TREAD
        B(k, -Wd / 2 + 0.03, Wd / 2 - 0.03, a - 0.004, a + 0.052, top - 0.02, top + 0.008, 'gold')


def d_column(k):
    k.cyl(0, 0, 0.12, 0.153, 0.153, 1.1, 'cove', seg=10, caps=False, ink=False)
    k.cyl(0, 0, 1.22, 0.162, 0.162, 0.04, 'gold', seg=10, ink=False)


# ---------------------------------------------------------------- furniture
def d_bench(k):
    B(k, -0.723, 0.723, -0.02, 0.02, 0.3, 0.34, 'steelD')
    for x in (-0.75, 0.75):
        for i in range(3):
            y = -0.18 + i * 0.13 + 0.05
            B(k, x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0.457, 0.466, 'chrome')


def d_bins(k):
    for x in (-0.2, 0.2):
        for z in (0.13, 0.66):
            k.cyl(x, 0, z, 0.197, 0.197, 0.03, 'steelD', seg=8, ink=False)
        k.cyl(x, 0, 0.827, 0.03, 0.03, 0.023, 'black', seg=6, ink=False)


def d_desk(k):
    edge_band(k, -0.31, 0.31, -0.04, 0.38, 0.69, 0.72, 'woodD')
    B(k, -0.262, 0.262, 0.31, 0.34, 0.3, 0.33, 'steelD')


def d_teacher(k):
    edge_band(k, -0.8, 0.8, -0.38, 0.38, 0.73, 0.76, 'woodD')
    for z in (0.12, 0.34, 0.56):
        pull(k, -0.54, 0.363, z + 0.07, z + 0.1, 'chrome', w=0.1, d=0.014, face=1)
    k.cyl(0.62, 0.2, 0.757, 0.025, 0.025, 0.008, 'black', seg=8, ink=False)


def d_book(k):
    # open bookcase: plinth, cap
    B(k, -0.88, 0.88, -0.176, -0.167, 0.004, 0.075, 'woodD')


def d_group(k):
    edge_band(k, -0.58, 0.58, -0.58, 0.58, 0.70, 0.73, 'woodD')


def d_compdesk(k):
    edge_band(k, -0.92, 0.92, -0.35, 0.35, 0.71, 0.74, 'steelD')


def d_island(k):
    edge_band(k, -0.88, 0.88, -0.4, 0.4, 0.71, 0.74, 'steelD')


def d_read(k):
    edge_band(k, -0.8, 0.8, -0.5, 0.5, 0.73, 0.76, 'woodD')


def d_art(k):
    edge_band(k, -0.8, 0.8, -0.52, 0.52, 0.75, 0.78, 'wood')


def d_caf(k):
    edge_band(k, -2.6, 2.6, -0.4, 0.4, 0.71, 0.75, 'steelD')
    for x in (-1.8, 0.0, 1.8):
        B(k, x - 0.043, x + 0.043, 0.797, 0.808, 0.004, 0.056, 'black')
        B(k, x - 0.043, x + 0.043, -0.808, -0.797, 0.004, 0.056, 'black')
        for sg in (-1, 1):
            for dy in (-0.07, 0.07):
                B(k, x - 0.01, x + 0.01, sg * 0.66 + dy - 0.01, sg * 0.66 + dy + 0.01, 0.457, 0.466, 'chrome')


def d_shelf(k):
    # double-sided stack: plinths, shelf-edge label strips, cam bolts on the end panels
    for sg in (-1, 1):
        lo, hi = sorted((sg * 0.297, sg * 0.306))
        B(k, -1.35, 1.35, lo, hi, 0.004, 0.075, 'woodD')
        for z0 in (0.46, 0.88, 1.30):
            B(k, 0.3, 0.7, lo, hi, z0 + 0.006, z0 + 0.034, 'trimW')
    for sx in (-1, 1):
        lo, hi = sorted((sx * 1.447, sx * 1.454))
        for z in (0.5, 1.2):
            for y in (-0.2, 0.2):
                B(k, lo, hi, y - 0.012, y + 0.012, z - 0.012, z + 0.012, 'steelD')


def d_sink(k):
    B(k, -1.44, 1.44, -0.309, -0.298, 0.004, 0.09, 'black')
    edge_band(k, -1.48, 1.48, -0.34, 0.3, 0.86, 0.9, 'steel')
    for i in range(5):
        x = -1.4 + i * 0.57
        pull(k, x + 0.43, -0.306, 0.58, 0.72, 'chrome', w=0.02, d=0.016)


def d_lab(k):
    edge_band(k, -1.8, 1.8, -0.68, 0.68, 0.85, 0.9, 'steelD')
    for s in (-1, 1):
        for i in range(4):
            x = -1.7 + i * 0.86
            B(k, x + 0.7, x + 0.73, min(s * 0.6, s * 0.618), max(s * 0.6, s * 0.618), 0.5, 0.7, 'chrome')


def d_hoop(k):
    yB = -1.2
    for x in (-0.6, 0.6):
        B(k, x - 0.035, x + 0.035, yB + 0.027, yB + 0.083, 3.72, 3.97, 'steelD')
    for x in (-0.885, 0.885):
        for z in (3.0, 3.84):
            B(k, x - 0.012, x + 0.012, yB - 0.04, yB - 0.027, z - 0.012, z + 0.012, 'chrome')


def d_bleacher(k):
    for j in range(0, 15, 2):
        top = (j + 1) * STEP_R_
        a = -2.45 + j * STEP_D_
        for x in (-2.6, 0.0, 2.6):
            B(k, x - 0.05, x + 0.05, a + 0.02, a + STEP_D_ - 0.02, top - 0.003, top + 0.006, 'steelD')


STEP_R_, STEP_D_ = 0.16, 0.28


def d_picnic(k):
    for i in range(4):
        y = -0.36 + i * 0.18 + 0.01 + 0.08
        for x in (-0.7, 0.7):
            B(k, x - 0.008, x + 0.008, y - 0.008, y + 0.008, 0.757, 0.766, 'steel')


def d_planter(k):
    for s in (-1, 1):
        for x in (-1.3, -0.65, 0.0, 0.65, 1.3):
            a, b = sorted((s * 0.95 - 0.003 * s, s * 0.95 + 0.004 * s))
            B(k, x - 0.006, x + 0.006, a, b, 0.525, 0.595, 'stoneD')
        for z in (0.17, 0.35):
            a, b = sorted((s * 0.9 - 0.003 * s, s * 0.9 + 0.004 * s))
            B(k, -1.895, 1.895, a, b, z, z + 0.012, 'mortar')


DETAIL = {
    'I': d_I, 'X': d_X, 'LkA': d_lockers, 'LkB': d_lockers, 'LkC': d_lockers, 'Cork': d_cork, 'FireExt': d_fireext,
    'Pad': d_pad, 'DoorBoys': d_closed_door, 'DoorGirls': d_closed_door, 'DoorJan': d_closed_door,
    'Door2': d_door2, 'Door3': d_door3, 'Door3X': d_door3, 'Stair': d_stair, 'DeckColumn': d_column,
    'Bench': d_bench, 'Bins': d_bins, 'Desk': d_desk, 'TeacherDesk': d_teacher, 'Bookcase': d_book,
    'GroupTable': d_group, 'CompDesk': d_compdesk, 'CompIsland': d_island, 'ReadTable': d_read, 'ArtTable': d_art,
    'CafTable': d_caf, 'Shelf': d_shelf, 'SinkCounter': d_sink, 'LabBench': d_lab, 'Hoop': d_hoop,
    'Bleacher': d_bleacher, 'Picnic': d_picnic, 'PlanterA': d_planter, 'PlanterB': d_planter,
}


def install(k):
    fin, chair, legs4 = k.finish, k.chair, k.legs4

    def finish(name, *a, **kw):
        fn = DETAIL.get(name)
        if fn:
            fn(k)
        return fin(name, *a, **kw)

    def chair_(x, y, deg, c='chA', seat=0.45):
        chair(x, y, deg, c, seat)
        k.push(x, y, deg)
        for sx in (-0.19, 0.17):
            B(k, sx - 0.004, sx + 0.024, -0.194, -0.15, 0.0, 0.03, 'black')
            B(k, sx - 0.004, sx + 0.024, 0.15, 0.194, 0.0, 0.03, 'black')
        for bx_ in (-0.12, 0.12):
            B(k, bx_ - 0.012, bx_ + 0.012, 0.19 - 0.012, 0.19 + EMBED, seat + 0.3, seat + 0.324, 'chrome')
        k.pop()

    def legs4_(x0, x1, y0, y1, z1, c, t=0.04, ink=True):
        legs4(x0, x1, y0, y1, z1, c, t, ink)
        for x in (x0, x1 - t):
            for y in (y0, y1 - t):
                B(k, x - 0.004, x + t + 0.004, y - 0.004, y + t + 0.004, 0.0, 0.02, 'black')

    k.finish, k.chair, k.legs4 = finish, chair_, legs4_
