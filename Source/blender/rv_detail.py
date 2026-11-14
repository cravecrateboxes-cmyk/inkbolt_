"""INKBOLT kit-riviera: modelled-detail helpers (tactical look, Stage 11). Finish and fittings, not wear: skirting and
cornice mouldings, panel frames, architraves, plinths, collars, brass fittings.

Every part is ink=False (no outline shell), stands at least 3 mm proud of whatever it sits on and starts 3 mm inside it,
and horizontal runs stop 5 mm short of a piece's sides, so ib_lib.check_zfight stays clean. Faces are the wall modules'
(looking toward Blender -Y at the plane y) unless a helper says otherwise. Nothing here touches a _COL box.
"""
import math

import hotel_detail as D
from rv_base import H, DECK

IN = 0.005
EM = 0.003


def iw_face_detail(k, y, dz, kind):
    """Interior wall face (plane y, facing -Y): skirting with a moulded cap, raised frames round the sea-glass dado
    panels, a cap and bead on the blue rail, dentils under the cornice, a bead under the belt course; a frame round
    the sconce plate, a bead frame on the mirror, a plaque under the painting."""
    k.bx(-0.495, 0.495, y - 0.03, y + EM, dz + 0.004, dz + 0.118, 'marble', ink=False)
    k.bx(-0.492, 0.492, y - 0.018, y + 0.008, dz + 0.116, dz + 0.165, 'stone2', ink=False)
    for (x0, x1) in ((-0.44, -0.02), (0.02, 0.44)):
        D.pframe(k, x0, x1, dz + 0.285, dz + 0.915, y - 0.006, 'ivory', t=0.018, d=0.012)
    k.bx(-0.495, 0.495, y - 0.03, y + EM, dz + 1.098, dz + 1.135, 'ivory', ink=False)
    k.bx(-0.495, 0.495, y - 0.014, y + EM, dz + 0.992, dz + 1.02, 'stone2', ink=False)
    k.bx(-0.495, 0.495, y - 0.022, y + EM, DECK - 0.43 + dz, DECK - 0.397 + dz, 'gold', ink=False)
    D.dentils(k, -0.42, 0.42, H - 0.5 + dz, H - 0.418 + dz, y, 'stone', 9, w=0.05, d=0.024)
    if kind == 'Sconce':
        D.pframe(k, -0.095, 0.095, 2.52, 2.82, y, 'gold', t=0.016, d=0.014)
        k.bx(-0.03, 0.03, y - 0.012, y + EM, 2.84, 2.9, 'gold', ink=False)
    elif kind == 'Art':
        k.bx(-0.07, 0.07, y - 0.013, y + EM, 1.56, 1.6, 'brass', ink=False)
    elif kind == 'Mirror':
        D.pframe(k, -0.3, 0.3, 1.41, 3.54, y - 0.05, 'gold', t=0.016, d=0.012)


def suite_door_detail(k, y):
    """Suite door: plinth blocks under the architrave, raised fillets in the leaf panels, a brass kick plate, three
    hinges on the jamb side, skirting and dentils."""
    k.bx(-0.489, 0.489, y - 0.045, y + EM, 0.004, 0.118, 'marble', ink=False)
    for sx in (-1, 1):
        a, b = sorted((sx * 0.405, sx * 0.497))
        k.bx(a, b, y - 0.095, y + 0.007, 0.0, 0.163, 'stone2', ink=False)
        a, b = sorted((sx * 0.395, sx * 0.378))
        for z in (0.3, 1.25, 2.2):
            k.bx(a, b, y - 0.052, y - 0.03, z, z + 0.13, 'brass', ink=False)
    k.bx(-0.37, 0.37, y - 0.052, y - 0.03, 0.012, 0.17, 'brass', ink=False)
    D.pframe(k, -0.3, -0.05, 0.24, 1.06, y - 0.043, 'ivory', t=0.012, d=0.008)
    D.pframe(k, -0.3, -0.13, 1.34, 2.26, y - 0.043, 'ivory', t=0.012, d=0.008)
    D.pframe(k, 0.13, 0.3, 1.34, 2.26, y - 0.043, 'ivory', t=0.012, d=0.008)
    D.dentils(k, -0.4, 0.4, H - 0.5, H - 0.418, y, 'stone', 9, w=0.05, d=0.024)


def service_door_detail(k, y):
    """Kitchen swing doors: stainless kick plates, push plates and a hinge strip on each leaf."""
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.05, s * 0.4))
        k.bx(x0, x1, y - 0.078, y - 0.06, 0.06, 0.3, 'chrome', ink=False)
        k.bx(x0 + 0.1, x1 - 0.1, y - 0.075, y - 0.06, 0.95, 1.2, 'chrome', ink=False)
        a, b = sorted((s * 0.455, s * 0.425))
        for z in (0.35, 1.2, 2.05):
            k.bx(a, b, y - 0.075, y - 0.06, z, z + 0.14, 'steel2', ink=False)
    k.bx(-0.47, 0.47, y - 0.072, y - 0.058, 0.004, 0.02, 'steel2', ink=False)
    D.dentils(k, -0.4, 0.4, H - 0.5, H - 0.418, y, 'stone', 9, w=0.05, d=0.024)


def doorway_detail(k, part, lintel):
    """Doorway: a brass bead on the head architrave, jamb plinths with brass caps."""
    for f in (-1, 1):
        a, b = sorted((f * 0.5, f * 0.606))
        k.bx(-0.485, 0.485, a, b, lintel + 0.157, lintel + 0.19, 'brass', ink=False)
    for (side, xs) in (('L', -1), ('R', 1)):
        if part == side:
            x0, x1 = sorted((xs * 0.347, xs * 0.484))
            k.bx(x0, x1, -0.616, 0.616, 0.004, 0.2, 'stone2', ink=False)
            k.bx(*sorted((xs * 0.343, xs * 0.489)), -0.622, 0.622, 0.197, 0.23, 'brass', ink=False)


def sea_win_detail(k, sx, AZ, R):
    """Arched window cell: a moulded architrave round the arch and down the jamb, a panelled apron and skirting
    under the sill, a brass nosing on the sill, dentils under the cornice."""
    ox, far = 0.5 * sx, -0.5 * sx
    a0, a1 = (math.pi, math.pi / 2) if sx > 0 else (0.0, math.pi / 2)
    D.arch_architrave(k, ox, AZ, R + 0.015, R + 0.14, a0, a1, 6, y0=-0.53, y1=-0.497, c='stone2', lim=0.489)
    xa, xb = sorted((far * 0.99, far * 0.99 + sx * 0.13))
    k.bx(xa, xb, -0.53, -0.497, 0.5, AZ, 'stone2', ink=False)
    k.bx(-0.495, 0.495, -0.575, -0.553, 0.5, 0.512, 'brass', ink=False)
    D.pframe(k, -0.38, 0.38, 0.1, 0.38, -0.5, 'stone2', t=0.03, d=0.016)
    k.bx(-0.495, 0.495, -0.53, -0.497, 0.004, 0.08, 'marble', ink=False)
    xa, xb = (-0.46, 0.3) if sx > 0 else (-0.3, 0.46)
    D.dentils(k, xa, xb, H - 0.5, H - 0.418, -0.5, 'stone', 7, w=0.05, d=0.024)


def pier_detail(k):
    """Pilaster between windows: a plinth cap, a base bead, an astragal under the capital, flutes of white marble."""
    k.bx(-0.375, 0.375, -0.595, -0.49, 0.66, 0.705, 'stone', ink=False)
    k.bx(-0.325, 0.325, -0.575, -0.484, 0.703, 0.748, 'marble2', ink=False)
    k.bx(-0.315, 0.315, -0.575, -0.49, H - 1.0, H - 0.96, 'gold', ink=False)
    for fx in (-0.18, -0.06, 0.06, 0.18):
        k.bx(fx - 0.012, fx + 0.012, -0.575, -0.49, 0.9, H - 1.05, 'marble2', ink=False)
    k.bx(-0.4, 0.4, -0.635, -0.49, H - 0.605, H - 0.55, 'brass', ink=False)


def core_detail(k):
    """Core block: a plinth moulding at the foot and a gilt fillet under the cornice, all four sides."""
    k.bx(-0.5, 0.5, -0.5, 0.5, 0.004, 0.14, 'marble', ink=False)
    k.bx(-0.504, 0.504, -0.504, 0.504, H - 0.46, H - 0.42 + EM, 'gold', ink=False)


def door_hardware(k, y, ztop):
    """Terrace doors: stone jamb architraves, a stone threshold, a brass kick plate on the leaves, a stone head."""
    for sx in (-1, 1):
        a, b = sorted((sx * 0.45, sx * 0.495))
        k.bx(a, b, y - 0.04, y + 0.007, 0.004, ztop, 'stone2', ink=False)
    k.bx(-0.4, 0.4, y - 0.05, y + 0.007, 0.004, 0.035, 'stone', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * 0.04, s * 0.4))
        k.bx(a, b, y - 0.026, y - 0.003, 0.06, 0.28, 'brass', ink=False)
    k.bx(-0.485, 0.485, y - 0.04, y + 0.007, ztop, ztop + 0.04, 'stone2', ink=False)


def sea_bal_detail(k, lamp):
    """Cliff balustrade: base moulding, plinth cap, baluster collars, rail underbead and cap."""
    k.bx(-0.495, 0.495, -0.325, 0.325, 0.004, 0.065, 'stone2', ink=False)
    k.bx(-0.495, 0.495, -0.305, 0.305, 0.205, 0.245, 'marble', ink=False)
    for i in range(3):
        x = -0.333 + i * 0.333
        k.cyl(x, 0, 0.53, 0.112, 0.112, 0.03, 'marble2', seg=6, ink=False)
        k.cyl(x, 0, 0.9, 0.078, 0.078, 0.04, 'marble2', seg=6, ink=False)
    k.bx(-0.495, 0.495, -0.325, 0.325, 0.935, 0.953, 'stone2', ink=False)
    k.bx(-0.495, 0.495, -0.3, 0.3, 1.097, 1.125, 'marble', ink=False)
    if lamp:
        k.bx(-0.19, 0.19, -0.385, 0.385, 0.0, 0.08, 'stone2', ink=False)
        k.bx(-0.19, 0.19, -0.385, 0.385, 1.1, 1.14, 'marble', ink=False)
        k.cyl(0, 0, 1.55, 0.075, 0.075, 0.06, 'brass', seg=6, ink=False)
        k.cyl(0, 0, 3.0, 0.065, 0.065, 0.05, 'brass', seg=6, ink=False)


def gcol_detail(k, h):
    """Gallery column: a stone foot, a torus on the plinth, an astragal under the capital and a fillet over it."""
    k.bx(-0.415, 0.415, -0.415, 0.415, 0.004, 0.07, 'stone2', ink=False)
    k.cyl(0, 0, 0.297, 0.335, 0.31, 0.055, 'marble2', seg=8, ink=False)
    k.cyl(0, 0, h - 0.545, 0.27, 0.27, 0.065, 'brass', seg=8, ink=False)
    k.cyl(0, 0, h - 0.18, 0.39, 0.385, 0.033, 'brass', seg=8, ink=False)


def grail_detail(k, y0, y1):
    """Gallery balustrade run: plinth foot and cap, gilt collars on the bars, a gilt cap on the rail."""
    k.bx(-0.092, 0.092, y0 + IN, y1 - IN, 0.004, 0.05, 'stone2', ink=False)
    k.bx(-0.095, 0.095, y0 + IN, y1 - IN, 0.12, 0.158, 'marble', ink=False)
    n = max(1, int(round((y1 - y0) / 0.2)))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        k.bx(-0.02, 0.02, y - 0.02, y + 0.02, 0.5, 0.53, 'gold', ink=False)
    k.bx(-0.07, 0.07, y0 + IN, y1 - IN, 1.027, 1.05, 'gold', ink=False)


def gpost_detail(k):
    k.bx(-0.114, 0.114, -0.114, 0.114, 0.0, 0.07, 'marble2', ink=False)
    k.bx(-0.108, 0.108, -0.108, 0.108, 0.92, 0.955, 'stone2', ink=False)
    k.sph(0, 0, 1.115, 0.05, 'gold', seg=(6, 4), ink=False)


def coping_detail(k, X, Y, C, end):
    """Pool coping: expansion joints and a plinth shadow band on the terrace face, a skimmer grille in the top."""
    for i in range(int(2 * X / 1.5)):
        x = -X + 0.5 + 1.5 * i
        if -X + IN < x < X - IN:
            k.bx(x - 0.006, x + 0.006, -Y - 0.004, -Y + EM, 0.06, 0.285, 'vein', ink=False)
    k.bx(-X + IN, X - IN, -Y - 0.012, -Y + 0.007, 0.004, 0.05, 'stone2', ink=False)
    g0, g1 = (-1.2, 1.2) if end == 'M' else (-3.6, -0.8)
    k.bx(g0, g1, -Y + 0.25, -Y + 0.34, 0.296, 0.304, 'steel2', ink=False)
    n = int((g1 - g0) / 0.2)
    for i in range(n):
        x = g0 + (g1 - g0) * (i + 0.5) / n
        k.bx(x - 0.03, x + 0.03, -Y + 0.265, -Y + 0.325, 0.301, 0.307, 'black', ink=False)


def ladder_flange(k, x, y, z):
    k.cyl(x, y, z - 0.003, 0.052, 0.052, 0.012, 'chrome', seg=8, ink=False)


def planter_detail(k):
    """Terrace planter: plinth, fillets framing the tile band, corner pilasters, a drip under the rim."""
    k.bx(-1.47, 1.47, -0.42, 0.42, 0.004, 0.09, 'stone2', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * 0.397, s * 0.412))
        for (z0, z1) in ((0.165, 0.185), (0.435, 0.455)):
            k.bx(-1.43, 1.43, a, b, z0, z1, 'stone', ink=False)
        a, b = sorted((s * 0.395, s * 0.41))
        k.bx(-1.43, 1.43, a, b, 0.58, 0.605, 'stone2', ink=False)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.4, sx * 1.456))
        k.bx(a, b, -0.425, 0.425, 0.09, 0.6, 'stone2', ink=False)
        a, b = sorted((sx * 1.447, sx * 1.462))
        k.bx(a, b, -0.3, 0.3, 0.17, 0.46, 'stone2', ink=False)


def regdesk_detail(k):
    """Registration table: gilt piping round the cloth's top edge, a hem band, a cap on the banner stand."""
    D.piping_x(k, -1.885, 1.885, -0.6, 0.748, 'gold', t=0.014, d=0.014)
    D.piping_y(k, -0.585, 0.085, -1.9, 0.748, 'gold', t=0.014, d=0.014, s=-1)
    D.piping_y(k, -0.585, 0.085, 1.9, 0.748, 'gold', t=0.014, d=0.014, s=1)
    k.bx(-1.885, 1.885, -0.614, -0.597, 0.004, 0.035, 'wine3', ink=False)
    k.bx(0.895, 1.705, 0.545, 0.625, 2.097, 2.135, 'steel2', ink=False)


def banquette_detail(k):
    """Banquette: brass kick plate, gilt piping on the seat and back cushions, a rail cap, walnut arm ends."""
    k.bx(-1.965, 1.965, 0.438, 0.453, 0.01, 0.12, 'brass', ink=False)
    D.piping_x(k, -1.945, 1.945, 0.47, 0.505, 'gold', t=0.014, d=0.014)
    D.piping_x(k, -1.95, 1.95, 0.8, 1.235, 'gold', t=0.014, d=0.014)
    k.bx(-1.985, 1.985, 0.775, 0.99, 1.3, 1.335, 'brass', ink=False)


def lounger_detail(k):
    """Sun lounger: rubber feet, a blue band round the cushion's front and sides, chrome hinge pins."""
    for (lx, ly) in ((-0.28, -0.85), (0.28, -0.85), (-0.28, 0.85), (0.28, 0.85)):
        k.bx(lx - 0.036, lx + 0.036, ly - 0.036, ly + 0.036, 0.004, 0.035, 'black', ink=False)
    k.bx(-0.318, 0.318, -0.935, -0.917, 0.318, 0.362, 'tile', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * 0.298, s * 0.322))
        k.bx(a, b, -0.9, 0.28, 0.318, 0.362, 'tile', ink=False)
