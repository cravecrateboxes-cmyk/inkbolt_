"""kit-spire modelled detail (tactical look plan Stage 11): fittings for the pieces seen most in the white, bright
interiors. Each `<piece>(k, ...)` runs on the open piece in fam_kit_spire (after its own shapes, before finish). Every
part is ink=False, at least 3 mm proud, embedded 3 mm, and horizontal runs stop 5 mm short of the piece's sides.
Faces that look toward Blender -Y sit at y = yf in the current frame; `sides` runs a function on all four faces
(k.push rotation 0 / 90 / 180 / 270 puts the +X / +Y / -X faces into that frame)."""
import math

from kit_base import PROUD, EMBED, corner_guard, cap_trim, base_trim, kick_plate, bolt_row, rivet_strip, panel_seams

H = 9.0
DECK = 4.5


def sides(k, hx, hy, fn):
    """fn(k, half_width, yf) on the -Y, +X, +Y, -X faces of a box centred on the origin (yf is always -depth)"""
    for deg, hw, d in ((0, hx, hy), (90, hy, hx), (180, hx, hy), (270, hy, hx)):
        k.push(0, 0, deg)
        fn(k, hw, -d)
        k.pop()


# ------------------------------------------------------------------ curtain wall
def dia_slice(k, j):
    """sill-kick cap, header reveal, floor-beam bead, transom glazing beads, node-plate bolts, balustrade posts,
    splice plates with bolts on the free runs of the diagonals"""
    k.bx(-0.495, 0.495, -0.512, -0.356, 0.137, 0.152, 'steel2', ink=False)               # kick cap
    k.bx(-0.495, 0.495, -0.512, -0.497, 0.004, 0.03, 'steelDark', ink=False)             # kick toe line
    k.bx(-0.495, 0.495, -0.508, -0.497, H - 0.46, H - 0.43, 'graphite2', ink=False)      # header shadow line
    k.bx(-0.495, 0.495, -0.508, -0.497, DECK - 0.17, DECK - 0.14, 'steel2', ink=False)   # beam bead above the brass
    for zt in (2.25, 6.75):                                                               # glazing beads either side
        for y0, y1 in ((0.135, 0.163), (0.187, 0.215)):
            k.bx(-0.495, 0.495, y0, y1, zt - 0.04, zt + 0.04, 'steelDark', ink=False)
    # node plates: bolts
    if j == 0:
        for z in (0.12, 0.38):
            bolt_row(k, -0.45, -0.22, z, -0.17, 2, 'steelDark')
    if j == 5:
        for z in (0.12, 0.38):
            bolt_row(k, 0.22, 0.45, z, -0.17, 2, 'steelDark')
    if j in (2, 3):
        a, b = (0.2, 0.45) if j == 2 else (-0.45, -0.2)
        for z in (4.2, 4.5, 4.8):
            bolt_row(k, a, b, z, -0.17, 2, 'steelDark')
    # balustrade posts (base plate, post) every module, both floors
    for zr, zb in ((0.98, 0.149), (DECK + 0.98, DECK - 0.003)):
        k.bx(-0.02, 0.02, -0.355, -0.315, zb + 0.01, zr + 0.005, 'steelDark', ink=False)
        k.bx(-0.05, 0.05, -0.375, -0.295, zb, zb + 0.018, 'steel2', ink=False)
        for sx in (-0.035, 0.035):
            k.bx(sx - 0.008, sx + 0.008, -0.372, -0.366, zb + 0.015, zb + 0.023, 'steel', ink=False)
    # splice plates on the diagonals (slices 1 and 4 have clear runs of both members)
    if j in (1, 4):
        o, dz = 0.005 * (j % 2), 0.006 * (j % 2)
        for (z0, slope, yface) in ((1.5 * j + dz, 1.5, -0.13 + o), (H - 1.5 * j + dz, -1.5, -0.09 + o)):
            def zc(x):
                return z0 + slope * (x + 0.5)
            hh = 0.2
            yp = yface - 0.012
            k.prism([(-0.18, zc(-0.18) - hh), (0.18, zc(0.18) - hh), (0.18, zc(0.18) + hh), (-0.18, zc(-0.18) + hh)],
                    yp, yface + EMBED, 'steel2', ink=False)
            for x in (-0.1, 0.1):
                for dzz in (-0.1, 0.1):
                    k.bx(x - 0.013, x + 0.013, yp - 0.009, yp + EMBED, zc(x) + dzz - 0.013, zc(x) + dzz + 0.013, 'steelDark', ink=False)


# ------------------------------------------------------------------ interior walls
def wall_trim(k, deck_band=True, skirt=True):
    """brass cap line on the granite skirting, reveal lines under the cornice and the deck band"""
    if skirt:
        k.bx(-0.495, 0.495, -0.522, -0.497, 0.147, 0.158, 'brass', ink=False)
    k.bx(-0.495, 0.495, -0.538, -0.527, 8.636, 8.653, 'graphite2', ink=False)
    if deck_band:
        k.bx(-0.495, 0.495, -0.538, -0.527, DECK - 0.414, DECK - 0.397, 'graphite2', ink=False)


def inner_wall(k, kind):
    wall_trim(k)
    if kind in ('Stone', 'Wood'):
        # centre panel joint, lower and upper stone fields
        for z0, z1 in ((0.2, DECK - 0.45), (DECK + 0.05, H - 0.4)):
            k.bx(-0.005, 0.005, -0.509, -0.497, z0, z1, 'granite' if kind == 'Stone' else 'walnut2', ink=False)
    if kind == 'Wood':
        for x in (-0.375, -0.125, 0.125, 0.375):
            for z0, z1 in ((DECK - 0.45, DECK - 0.38), (DECK - 0.02, DECK + 0.04), (H - 0.39, H - 0.33)):
                k.bx(x - 0.046, x + 0.046, -0.606, -0.497, z0, z1, 'brass', ink=False)
    if kind == 'Art':
        k.bx(-0.43, 0.43, -0.585, -0.497, 1.385, 1.403, 'brass', ink=False)     # picture ledge
    if kind.startswith('Screen'):
        for z in (0.76, 3.89, 4.58, 8.42):
            k.bx(-0.495, 0.495, -0.568, -0.557, z, z + 0.02, 'graphite2', ink=False)


def gate_side(k):
    wall_trim(k)


# ------------------------------------------------------------------ bridge
def trail_wall(k, kind=''):
    """skirting, glazing gaskets, mullion pressure cap, handrail brackets"""
    k.bx(0.247, 0.262, -0.495, 0.495, 0.004, 0.09, 'steel2', ink=False)                  # skirting on the corridor face
    k.bx(0.247, 0.262, -0.495, 0.495, 0.14, 0.153, 'steelDark', ink=False)                # shadow line under the glazing
    k.bx(-0.05, 0.05, -0.495, 0.495, 0.247, 0.263, 'graphite2', ink=False)                # lower gasket
    k.bx(-0.05, 0.05, -0.495, 0.495, H - 0.416, H - 0.397, 'graphite2', ink=False)        # upper gasket
    k.bx(0.077, 0.092, -0.495, -0.435, 0.27, H - 0.42, 'steel2', ink=False)               # mullion pressure cap
    for y in (0.0, 0.43):                                                                # handrail brackets
        k.bx(0.06, 0.165, y - 0.02, y + 0.02, 0.955, 1.0, 'steelDark', ink=False)
        k.bx(0.1, 0.12, y - 0.03, y + 0.03, 0.94, 0.955 + 0.003, 'steelDark', ink=False)


# ------------------------------------------------------------------ circulation
def rail(k, y0, y1):
    """shoe bolts, glass clamps and handrail brackets"""
    L = y1 - y0
    for t in (0.25, 0.75):
        y = y0 + L * t
        for s in (-1, 1):
            a, b = sorted((s * 0.047, s * 0.056))
            k.bx(a, b, y - 0.012, y + 0.012, 0.04, 0.06, 'steelDark', ink=False)        # shoe bolt
        k.bx(-0.026, 0.026, y - 0.025, y + 0.025, 0.28, 0.36, 'steel2', ink=False)      # glass clamp
        k.bx(-0.02, 0.02, y - 0.012, y + 0.012, 0.93, 0.975, 'steelDark', ink=False)     # handrail bracket
    for s in (-1, 1):
        a, b = sorted((s * 0.047, s * 0.054))
        k.bx(a, b, y0 + 0.005, y1 - 0.005, 0.1 - 0.012, 0.1 + 0.004, 'steel', ink=False)  # shoe cap line


def rail_post(k):
    k.bx(-0.078, 0.078, -0.078, 0.078, 0.004, 0.04, 'steel2', ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * 0.062 - 0.009, sx * 0.062 + 0.009, sy * 0.062 - 0.009, sy * 0.062 + 0.009, 0.037, 0.047, 'steelDark', ink=False)
    k.bx(-0.07, 0.07, -0.07, 0.07, 0.6, 0.62, 'steel2', ink=False)                       # post joint collar


def column(k, h):
    """anchor nuts on the base plate, bolt rows on the head plate, a steel collar at the shaft mid joint, corner guards"""
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * 0.35 - 0.025, sx * 0.35 + 0.025, sy * 0.35 - 0.025, sy * 0.35 + 0.025, 0.117, 0.145, 'steelDark', ink=False)

    def head(k, hw, yf):
        bolt_row(k, -0.34, 0.34, h - 0.04, yf, 4, 'steelDark', s=0.026)
    sides(k, 0.44, 0.44, head)
    k.cyl(0, 0, 0.9, 0.282, 0.282, 0.04, 'steel2', seg=12, ink=False, caps=False)


# ------------------------------------------------------------------ lobby
def reception(k):
    k.bx(-2.2, 2.2, -0.558, -0.547, 0.004, 0.096, 'steelDark', ink=False)               # kick plate under the fins
    bolt_row(k, -2.15, 2.15, 0.07, -0.558, 12, 'brass', s=0.02)
    k.bx(-2.2, 2.2, -0.558, -0.547, 1.012, 1.04, 'graphite2', ink=False)                # reveal under the marble
    for x in (-1.2, 0.0, 1.2):                                                          # marble joints
        k.bx(x - 0.005, x + 0.005, -0.665, 0.2, 1.107, 1.114, 'vein', ink=False)
    k.bx(-2.4, 2.4, -0.69, -0.676, 1.107, 1.114, 'brass', ink=False)                    # brass inlay along the front edge
    k.push(0, 0, 180)
    kick_plate(k, -2.0, 2.0, -0.15, 'steelDark', h=0.12)
    k.pop()
    k.bx(-2.195, 2.195, 0.617, 0.627, 0.73, 0.752, 'brass', ink=False)                 # shelf edge


def stand(k):
    def f(k, hw, yf):
        base_trim(k, -hw, hw, yf, 'steelDark', h=0.03, d=0.01, z0=0.1)
        corner_guard(k, hw - 0.005, yf, 0.14, 0.88, 'steel2', w=0.05, t=0.008)
    sides(k, 0.45, 0.42, f)


def totem(k):
    k.bx(-0.285, 0.285, -0.125, 0.125, 0.128, 0.16, 'steelDark', ink=False)
    k.bx(-0.285, 0.285, -0.125, 0.125, 2.04, 2.07, 'steelDark', ink=False)


def turnstile(k):
    for s in (-1, 1):
        a, b = sorted((s * 0.107, s * 0.118))
        k.bx(a, b, -0.415, 0.415, 0.004, 0.12, 'steelDark', ink=False)                  # kick plate
        k.bx(a, b, -0.007, 0.007, 0.12, 0.99, 'graphite2', ink=False)                   # panel seam
        for y0, y1 in ((-0.3, -0.02), (0.02, 0.3)):
            k.bx(a, b, y0, y1, 0.5, 0.52, 'graphite2', ink=False)


def planter_a(k):
    def f(k, hw, yf):
        base_trim(k, -hw, hw, yf, 'granite', h=0.08, d=0.006)
        k.bx(-hw + 0.005, hw - 0.005, yf - 0.004, yf + EMBED, 0.35 - 0.005, 0.35 + 0.005, 'vein', ink=False)
    sides(k, 0.4, 0.4, f)


def planter_b(k):
    k.cyl(0, 0, 0.004, 0.364, 0.364, 0.05, 'granite', seg=12, ink=False)
    k.cyl(0, 0, 0.78, 0.316, 0.316, 0.035, 'brass', seg=12, ink=False, caps=False)


def olive_planter(k):
    def f(k, hw, yf):
        base_trim(k, -hw, hw, yf, 'granite', h=0.09, d=0.008)
        panel_seams(k, -hw + 0.005, hw - 0.005, 0.1, 0.59, yf, 0.6, 'vein', t=0.012)
        corner_guard(k, hw - 0.005, yf, 0.1, 0.59, 'steel2', w=0.05, t=0.008)
        corner_guard(k, -hw + 0.005, yf, 0.1, 0.59, 'steel2', w=0.05, t=0.008, side=-1)
    sides(k, 0.9, 0.9, f)


def bench(k):
    for s in (-1, 1):
        a, b = sorted((s * 0.695, s * 0.865))
        k.bx(a, b, -0.245, 0.245, 0.004, 0.04, 'brass', ink=False)                      # feet pads
    for y0, y1 in ((-0.265, -0.257), (0.257, 0.265)):
        k.bx(-0.94, 0.94, y0, y1, 0.372, 0.408, 'brass', ink=False)
    for x0, x1 in ((-0.957, -0.947), (0.947, 0.957)):
        k.bx(x0, x1, -0.25, 0.25, 0.372, 0.408, 'brass', ink=False)


def trade_desk(k):
    for y0, y1 in ((-0.806, -0.797), (0.797, 0.806)):
        k.bx(-1.945, 1.945, y0, y1, 0.724, 0.756, 'steel2', ink=False)
    for x0, x1 in ((-1.953, -1.947), (1.947, 1.953)):
        k.bx(x0, x1, -0.795, 0.795, 0.724, 0.756, 'steel2', ink=False)
    for x in (-1.85, 0.0, 1.85):
        k.bx(x - 0.045, x + 0.045, -0.705, 0.705, 0.004, 0.03, 'black', ink=False)
    for x in (-1.4, -0.5, 0.5, 1.4):
        k.bx(x - 0.03, x + 0.03, 0.63, 0.67, 0.757, 0.766, 'black', ink=False)
        k.bx(x - 0.03, x + 0.03, -0.67, -0.63, 0.757, 0.766, 'black', ink=False)
