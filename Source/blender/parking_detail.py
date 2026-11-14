"""kit-parking modelled detail (tactical look plan Stage 11): what a real car park shows up close.

Walls: formwork seams and tie holes, conduit runs with clips, cable trays on brackets, louvred vents, pipe flanges,
pier corner guards, fire-door hinges / kick plates / closers, shutter guide rails. Columns: hazard-banded corner
guards with caps, base plinth, a formwork joint, screwed number plates and P signs. Ticket barriers and the pay
station: kick plates, access panels, bezels, anchor bolts, kerb joints. Rails, ramps, stairs: anchor plates and
bolts, kerb expansion joints, handrail brackets. Bollard: base bolts and a reflective band.

Rules (KIT-BRIEF): every part is hull='none' (no outline shell), stands >= 3 mm proud of what it sits on and
sinks 3 mm into the face behind it; horizontal runs stop 5 mm short of a module's sides. Nothing here changes a
piece's origin, footprint, collision boxes or the parts already drawn: it only adds shapes.
"""
import math

from mathutils import Matrix

from parking_base import *  # noqa: F401,F403

E = 0.003          # sink into the face behind
HOLD = 0.495       # horizontal runs stop 5 mm short of a module side


def P(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def fx(m, x0, x1, z0, z1, yf, d, c, cull='k'):
    """a box d proud of the face-toward--Y plane at y = yf, sunk E into it"""
    if z0 < 0.01:
        cull += 'b'
    return P(m, x0, x1, yf - d, yf + E, z0, z1, c, cull)


def span(trim):
    """x extent of a module's proud details (same rule as parking_struct.span)"""
    return (-0.18, 0.5) if trim == 'L' else (-0.5, 0.18) if trim == 'R' else (-0.5, 0.5)


def clampx(x0, x1, span=(-HOLD, HOLD)):
    return max(x0, span[0]), min(x1, span[1])


# ------------------------------------------------------------------------------------------------ wall fittings
def tie_holes(m, xs, zs, yf, span=(-HOLD, HOLD), s=0.04):
    """formwork tie holes: a dark plug with a darker centre"""
    for x in xs:
        if x - s / 2 < span[0] or x + s / 2 > span[1]:
            continue
        for z in zs:
            fx(m, x - s / 2, x + s / 2, z - s / 2, z + s / 2, yf, 0.005, 'concD')
            fx(m, x - 0.009, x + 0.009, z - 0.009, z + 0.009, yf, 0.009, 'ink')


def form_seam(m, x, z0, z1, yf, span=(-HOLD, HOLD), w=0.016):
    if x - w / 2 < span[0] or x + w / 2 > span[1]:
        return
    fx(m, x - w / 2, x + w / 2, z0, z1, yf, 0.012, 'concD')


def conduit(m, x0, x1, z, yf, span=(-HOLD, HOLD), r=0.02, every=0.8, c='steelD', clip='galv'):
    x0, x1 = clampx(x0, x1, span)
    if x1 - x0 < 0.1:
        return
    m.cy((x0, yf - r - 0.006, z), r, r, x1 - x0, c, seg=6, rot=(0, 90, 0), hull='none')
    n = max(1, int((x1 - x0) / every))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        P(m, x - 0.015, x + 0.015, yf - 2 * r - 0.012, yf + E, z - r - 0.008, z + r + 0.008, clip, 'k')


def drop_conduit(m, x, z0, z1, yf, r=0.02, c='steelD'):
    m.cy((x, yf - r - 0.006, z0), r, r, z1 - z0, c, seg=6, hull='none')


def junction_box(m, x, z, yf, w=0.2, h=0.26, d=0.09, c='steelD', lid='galv'):
    fx(m, x - w / 2, x + w / 2, z - h / 2, z + h / 2, yf, d, c)
    fx(m, x - w / 2 + 0.02, x + w / 2 - 0.02, z - h / 2 + 0.02, z + h / 2 - 0.02, yf, d + 0.005, lid)
    for sx in (-1, 1):   # lid screws
        for sz in (-1, 1):
            fx(m, x + sx * (w / 2 - 0.035) - 0.008, x + sx * (w / 2 - 0.035) + 0.008,
               z + sz * (h / 2 - 0.035) - 0.008, z + sz * (h / 2 - 0.035) + 0.008, yf, d + 0.012, 'chrome')


def cable_tray(m, x0, x1, z, yf, span=(-HOLD, HOLD), d=0.11, c='galv', cable='ink', cable2='pipeR'):
    """a tray on brackets with two cables: shelf, outer lip, brackets under it"""
    x0, x1 = clampx(x0, x1, span)
    fx(m, x0, x1, z, z + 0.012, yf, d - 0.012, c)               # shelf
    P(m, x0, x1, yf - d, yf - d + 0.012, z, z + 0.07, c, 'k')   # outer lip
    n = max(2, int((x1 - x0) / 0.45) + 1)
    for i in range(n):
        x = x0 + 0.06 + (x1 - x0 - 0.12) * i / (n - 1)
        P(m, x - 0.01, x + 0.01, yf - d + 0.012, yf + E, z - 0.07, z, 'steelD', 'kt')   # bracket under the shelf
    P(m, x0 + 0.01, x1 - 0.01, yf - 0.065, yf - 0.03, z + 0.012, z + 0.045, cable, 'k')
    P(m, x0 + 0.01, x1 - 0.01, yf - 0.095, yf - 0.065, z + 0.012, z + 0.04, cable2, 'k')


def vent(m, x, z, w, h, yf, frame='steelD', slat='galv'):
    """louvred vent: frame 12 mm proud, a dark void and slats sunk into it"""
    t = 0.03
    fx(m, x - w / 2, x + w / 2, z - h / 2, z - h / 2 + t, yf, 0.012, frame)
    fx(m, x - w / 2, x + w / 2, z + h / 2 - t, z + h / 2, yf, 0.012, frame)
    fx(m, x - w / 2, x - w / 2 + t, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, yf, 0.012, frame)
    fx(m, x + w / 2 - t, x + w / 2, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, yf, 0.012, frame)
    fx(m, x - w / 2 + t, x + w / 2 - t, z - h / 2 + t, z + h / 2 - t, yf, 0.004, 'ink')
    n = max(3, int(h / 0.06))
    for i in range(n):
        zz = z - h / 2 + t + (h - 2 * t) * (i + 0.5) / n
        P(m, x - w / 2 + t + 0.004, x + w / 2 - t - 0.004, yf - 0.011, yf - 0.001, zz - 0.007, zz + 0.007, slat, 'k')


def pipe_flange(m, x, y, z, r, c='steelD'):
    m.cy((x, y, z), r + 0.016, r + 0.016, 0.03, c, seg=8, hull='none')
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        m.cy((x + math.cos(a) * (r + 0.008), y + math.sin(a) * (r + 0.008), z + 0.03), 0.007, 0.007, 0.01, 'chrome', seg=4, hull='none')


def corner_guard_pier(m, z0, z1, yf=-0.78, x=0.36):
    """a hazard-banded angle on each front corner of a wall pier"""
    for sx in (-1, 1):
        xa, xb = sorted((sx * (x - 0.07), sx * (x + 0.012)))
        P(m, xa, xb, yf - 0.012, yf + 0.06, z0, z1, 'lineY', 'tbk')
        h = z1 - z0
        nb = max(2, int(h / 0.3))
        for k in range(nb):
            za = z0 + 0.1 + k * (h - 0.2) / nb
            P(m, xa - 0.003, xb + 0.003, yf - 0.015, yf + 0.06, za, za + (h - 0.2) / nb * 0.5, 'ink', 'tbk')


# ------------------------------------------------------------------------------------------------ wall modules
def lo_detail(m, v, trim=None):
    """lower storey (0 - 3.6) wall module of variant v, face plane y = -0.5"""
    x0, x1 = span(trim) if trim else (-0.5, 0.5)
    sp = (max(x0, -HOLD), min(x1, HOLD))
    yf = -0.5
    if v in ('Plain', 'End'):
        form_seam(m, 0.0, 1.62, 3.2, yf, sp)
        tie_holes(m, (-0.25, 0.25), (1.95, 2.25), yf, sp)
        conduit(m, -HOLD, HOLD, 3.05, yf, sp)
    elif v == 'Num':
        cable_tray(m, -HOLD, HOLD, 2.7, yf, sp)
    elif v == 'Arrow':
        vent(m, 0.0, 2.75, 0.5, 0.3, yf)
        tie_holes(m, (-0.35, 0.35), (2.2,), yf, sp)
    elif v == 'Pipe':
        pipe_flange(m, 0.32, -0.64, 0.5, 0.07)
        pipe_flange(m, 0.32, -0.64, 2.55, 0.07)
        # nozzle on its holder, beside the hose reel
        m.cy((0.14, -0.55, 0.95), 0.016, 0.016, 0.4, 'chrome', seg=6, hull='none')
        P(m, 0.1, 0.18, -0.58, -0.497, 1.3, 1.34, 'steelD', 'k')
        P(m, 0.1, 0.18, -0.58, -0.497, 0.93, 0.97, 'steelD', 'k')
    elif v == 'Pier':
        corner_guard_pier(m, 0.0, 1.1)
        # extinguisher sign above it
        fx(m, -0.09, 0.09, 1.7, 1.98, -0.78, 0.012, 'pipeR')
        fx(m, -0.04, 0.04, 1.78, 1.9, -0.78, 0.016, 'paper')
    elif v == 'Door':
        fx(m, -0.40, 0.40, 0.0, 0.22, -0.5, 0.012, 'galv')                     # kick plate
        for z in (0.3, 1.1, 1.9):                                              # hinge leaves
            fx(m, -0.42, -0.37, z, z + 0.14, -0.5, 0.012, 'steelD')
            fx(m, -0.405, -0.385, z + 0.02, z + 0.12, -0.5, 0.02, 'galv')
        for t0, t1, a, b in ((1.9, 1.93, -0.18, 0.18), (1.32, 1.35, -0.18, 0.18)):   # glass frame
            fx(m, a, b, t0, t1, -0.5, 0.016, 'steelD')
        fx(m, -0.18, -0.15, 1.35, 1.9, -0.5, 0.016, 'steelD')
        fx(m, 0.15, 0.18, 1.35, 1.9, -0.5, 0.016, 'steelD')
        fx(m, 0.28, 0.40, 2.05, 2.2, -0.5, 0.03, 'steelD')                     # door closer body and arm
        fx(m, 0.0, 0.3, 2.1, 2.14, -0.5, 0.022, 'galv')
        fx(m, 0.36, 0.41, 0.95, 1.1, -0.5, 0.012, 'steelD')                    # lock plate
        for sx in (-1, 1):                                                     # pads behind the push bar ends
            fx(m, sx * 0.30 if sx > 0 else -0.36, 0.36 if sx > 0 else -0.30, 0.98, 1.09, -0.5, 0.02, 'steelD')
    elif v == 'Lift':
        fx(m, -0.43, 0.43, 0.0, 0.03, -0.5, 0.06, 'galv')                       # sill
        for z in (0.5, 1.5):                                                   # door guide pads
            fx(m, -0.43, -0.41, z, z + 0.12, -0.5, 0.012, 'steelD')
            fx(m, 0.41, 0.43, z, z + 0.12, -0.5, 0.012, 'steelD')
    elif v == 'Dock':
        for sx in (-1, 1):   # guide rails
            a, b = sorted((sx * 0.488, sx * 0.448))
            P(m, a, b, -0.525, -0.497, 1.62, 3.2, 'steelD', 'kt')
        P(m, -0.25, 0.25, -0.52, -0.497, 1.63, 1.69, 'steelD', 'k')           # bottom bar
        P(m, -0.03, 0.03, -0.535, -0.497, 1.64, 1.68, 'chrome', 'k')          # pull
        for x in (-0.42, -0.14, 0.14, 0.42):                                    # hood rivets
            P(m, x - 0.01, x + 0.01, -0.786, -0.777, 3.33, 3.35, 'steel', 'k')


def up_detail(m, v, trim=None):
    """upper storey (3.6 - 7.0) wall module of variant v"""
    x0, x1 = span(trim) if trim else (-0.5, 0.5)
    sp = (max(x0, -HOLD), min(x1, HOLD))
    yf = -0.5
    if v in ('Plain', 'End'):
        form_seam(m, 0.0, 5.25, 6.65, yf, sp)
        tie_holes(m, (-0.25, 0.25), (5.5, 5.82), yf, sp)
        conduit(m, -HOLD, HOLD, 6.42, yf, sp)
    elif v == 'Num':
        cable_tray(m, -HOLD, HOLD, 6.2, yf, sp)
    elif v == 'Arrow':
        vent(m, 0.0, 6.3, 0.5, 0.3, yf)
        tie_holes(m, (-0.35, 0.35), (5.9,), yf, sp)
    elif v == 'Pipe':
        pipe_flange(m, 0.32, -0.64, 6.1, 0.07)
        pipe_flange(m, -0.25, -0.64, 6.1, 0.06)
    elif v == 'Pier':
        corner_guard_pier(m, DECK + 0.18, DECK + 1.28)


def trail_detail(m, name):
    """corridor wall: inner face +X at x = 0.25 (a -Y facing frame turned 90 degrees)"""
    m.parent = Matrix.Rotation(math.radians(90), 4, 'Z')
    yf = -0.25
    tie_holes(m, (-0.25, 0.25), (1.95, 2.3), yf)
    conduit(m, -HOLD, HOLD, 3.5, yf)
    if name != 'TrailWall_B':
        form_seam(m, 0.0, 3.0, 3.4, yf)
    m.parent = Matrix.Identity(4)


# ------------------------------------------------------------------------------------------------ columns
def column_detail(m, h):
    for sx in (-1, 1):   # hazard bands, cap on the yellow corner guards
        for sy in (-1, 1):
            xa, xb = sorted((sx * 0.255, sx * 0.319))
            ya, yb = sorted((sy * 0.255, sy * 0.319))
            for z0 in (0.12, 0.36, 0.60):
                P(m, xa, xb, ya, yb, z0, z0 + 0.12, 'ink', 'tb')
            P(m, xa, xb, ya, yb, 0.897, 0.912, 'steelD', 'b')
    P(m, -0.322, 0.322, -0.322, 0.322, 0.0, 0.1, 'concD', 'b')       # base plinth
    P(m, -0.304, 0.304, -0.304, 0.304, 2.72, 2.735, 'concD', 'tb')   # formwork joint
    for sx in (-1, 1):   # screws on the number plates (front and back)
        for z in (1.645, 1.995):
            for yf, d in ((-0.32, -1), (0.32, 1)):
                a, b = sorted((yf - d * 0.003, yf + d * 0.006))
                P(m, sx * 0.17 - 0.011, sx * 0.17 + 0.011, a, b, z - 0.011, z + 0.011, 'steelD', '')
    for z in (2.225, 2.495):   # and on the P signs (sides)
        for sy in (-1, 1):
            for xf, d in ((0.32, 1), (-0.32, -1)):
                a, b = sorted((xf - d * 0.003, xf + d * 0.006))
                P(m, a, b, sy * 0.135 - 0.011, sy * 0.135 + 0.011, z - 0.011, z + 0.011, 'steelD', '')


# ------------------------------------------------------------------------------------------------ props
def barrier_detail(m):
    """ticket barrier island: kerb joints, anchor collars, cabinet kick plates / panels / bezel, arm-cabinet door"""
    for y in (-0.4, 0.4):                                              # kerb expansion joints
        P(m, -0.44, 0.44, y - 0.007, y + 0.007, 0.175, 0.186, 'concD', 'b')
    for y0, y1, hx in ((-1.44, -0.86, 0.29), (0.91, 1.59, 0.32)):      # anchor collars + bolts
        P(m, -hx, hx, y0, y1, 0.175, 0.206, 'steelD', 'b')
        for sx in (-1, 1):
            for y in (y0 + 0.03, y1 - 0.03):
                P(m, sx * (hx - 0.03) - 0.016, sx * (hx - 0.03) + 0.016, y - 0.016, y + 0.016, 0.203, 0.221, 'steel', 'bk')
    for s in (1, -1):   # ticket machine faces: kick plate, bolts, access panel
        xf = s * 0.25
        cl = 'l' if s > 0 else 'r'
        def sx(d0, d1):
            return tuple(sorted((xf + s * d0, xf + s * d1)))
        a, b = sx(-E, 0.008)
        P(m, a, b, -1.37, -0.93, 0.21, 0.32, 'steelD', cl)
        for y in (-1.31, -1.15, -0.99):
            a, b = sx(-E, 0.014)
            P(m, a, b, y - 0.012, y + 0.012, 0.29, 0.314, 'steel', cl)
        for (y0, y1, z0, z1) in ((-1.37, -1.36, 0.34, 0.5), (-0.94, -0.93, 0.34, 0.5),
                                 (-1.36, -0.94, 0.34, 0.35), (-1.36, -0.94, 0.49, 0.5)):
            a, b = sx(-E, 0.006)
            P(m, a, b, y0, y1, z0, z1, 'ink', cl)
    xf = 0.25
    cl = 'l'
    # button surround, slot bezel, intercom slits on the lane side
    P(m, xf - E, xf + 0.014, -1.17, -0.97, 0.5, 0.52, 'steelD', cl)
    P(m, xf - E, xf + 0.014, -1.17, -0.97, 0.64, 0.66, 'steelD', cl)
    P(m, xf - E, xf + 0.014, -1.17, -1.15, 0.52, 0.64, 'steelD', cl)
    P(m, xf - E, xf + 0.014, -0.99, -0.97, 0.52, 0.64, 'steelD', cl)
    P(m, xf - E, xf + 0.012, -1.33, -0.97, 0.815, 0.83, 'chrome', cl)
    P(m, xf - E, xf + 0.012, -1.33, -0.97, 0.67, 0.685, 'chrome', cl)
    P(m, xf - E, xf + 0.012, -1.33, -1.315, 0.685, 0.815, 'chrome', cl)
    P(m, xf - E, xf + 0.012, -0.985, -0.97, 0.685, 0.815, 'chrome', cl)
    for z in (1.35, 1.39, 1.43):
        P(m, xf - E, xf + 0.008, -1.28, -1.02, z, z + 0.012, 'ink', cl)
    # barrier arm cabinet: door outline, hinges, lock (both faces)
    for s in (1, -1):
        xf = s * 0.28
        cl = 'l' if s > 0 else 'r'
        def sx2(d0, d1):
            return tuple(sorted((xf + s * d0, xf + s * d1)))
        a, b = sx2(-E, 0.006)
        for (y0, y1, z0, z1) in ((1.02, 1.03, 0.3, 0.8), (1.47, 1.48, 0.3, 0.8), (1.03, 1.47, 0.3, 0.31), (1.03, 1.47, 0.79, 0.8)):
            P(m, a, b, y0, y1, z0, z1, 'ink', cl)
        a, b = sx2(-E, 0.012)
        for z in (0.34, 0.68):
            P(m, a, b, 1.035, 1.065, z, z + 0.08, 'steelD', cl)
        a, b = sx2(-E, 0.016)
        P(m, a, b, 1.40, 1.44, 0.52, 0.58, 'chrome', cl)


def paystation_detail(m):
    yf = -0.22
    fx(m, -0.31, 0.31, 0.124, 0.35, yf, 0.012, 'steelD')                      # kick plate
    for x in (-0.25, 0.0, 0.25):
        fx(m, x - 0.011, x + 0.011, 0.31, 0.331, yf, 0.02, 'steel')
    for z0, z1, a, b in ((1.5, 1.54, -0.28, 0.28), (1.11, 1.15, -0.28, 0.28)):    # screen bezel
        fx(m, a, b, z0, z1, yf, 0.012, 'steelD')
    fx(m, -0.28, -0.24, 1.15, 1.5, yf, 0.012, 'steelD')
    fx(m, 0.24, 0.28, 1.15, 1.5, yf, 0.012, 'steelD')
    for z0, z1 in ((0.665, 0.69), (0.57, 0.595)):                             # card slot bezel
        fx(m, -0.14, 0.14, z0, z1, yf, 0.012, 'chrome')
    fx(m, -0.14, -0.12, 0.595, 0.665, yf, 0.012, 'chrome')
    fx(m, 0.12, 0.14, 0.595, 0.665, yf, 0.012, 'chrome')
    fx(m, -0.16, 0.16, 0.38, 0.5, yf, 0.045, 'steelD')                        # receipt tray
    fx(m, -0.12, 0.12, 0.4, 0.44, yf, 0.052, 'ink')
    for x in (-0.28, 0.28):                                                    # fascia screws
        for z in (0.55, 1.65):
            fx(m, x - 0.011, x + 0.011, z - 0.011, z + 0.011, yf, 0.012, 'chrome')
    for sx in (-1, 1):                                                         # anchor bolts on the plinth
        for sy in (-1, 1):
            P(m, sx * 0.35 - 0.016, sx * 0.35 + 0.016, sy * 0.26 - 0.016, sy * 0.26 + 0.016, 0.115, 0.135, 'steel', 'bk')


def bollard_detail(m):
    m.cy((0, 0, 0.4), 0.1235, 0.1235, 0.07, 'paper', seg=10, hull='none', caps=False)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 0.145, math.sin(a) * 0.145
        P(m, x - 0.014, x + 0.014, y - 0.014, y + 0.014, 0.036, 0.054, 'steel', 'b')


# ------------------------------------------------------------------------------------------------ rails, ramps, stairs
def rail_detail(m, y0, y1, post_at=None):
    """kerb expansion joint across the upstand top (and an anchor plate with bolts round a post)"""
    ymid = (y0 + y1) / 2
    for y in ((ymid,) if post_at is None else (y0 + 0.2 * (y1 - y0), y1 - 0.2 * (y1 - y0))):
        P(m, -0.09, 0.09, y - 0.007, y + 0.007, 0.345, 0.358, 'concD', 'b')
    if post_at is not None:
        plate(m, post_at[0], post_at[1], 0.35, 0.09)


def plate(m, x, y, z, hw, c='steelD', h=0.016):
    """anchor plate on a surface at height z with four bolt heads"""
    P(m, x - hw, x + hw, y - hw, y + hw, z - 0.003, z + h, c, 'b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = x + sx * (hw - 0.02), y + sy * (hw - 0.02)
            P(m, cx - 0.01, cx + 0.01, cy - 0.01, cy + 0.01, z + h - 0.003, z + h + 0.012, 'steel', 'bk')


def ramp_post_plate(m, xc, y, zs):
    """base plate for a guard-rail post standing on a sloping kerb (zs = kerb top at the post)"""
    P(m, xc - 0.065, xc + 0.065, y - 0.065, y + 0.065, zs - 0.02, zs + 0.04, 'steelD', 'b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = xc + sx * 0.05, y + sy * 0.05
            P(m, cx - 0.01, cx + 0.01, cy - 0.01, cy + 0.01, zs + 0.037, zs + 0.052, 'steel', 'bk')


def stair_brackets(m, xi, ya, za, yb, zb, wall_x, count):
    """handrail brackets: short arms from the rail to the parapet's inner face"""
    for i in range(count):
        t = (i + 0.5) / count
        y = ya + (yb - ya) * t
        z = za + (zb - za) * t
        a, b = sorted((xi, wall_x + (0.003 if wall_x > xi else -0.003)))
        P(m, a, b, y - 0.02, y + 0.02, z - 0.03, z + 0.012, 'galv', '')


def kerb_joint(m, xa, xb, y, s):
    """a thin expansion joint across a sloping kerb top (kerb top = s(y) + 0.22)"""
    prof = [(y - 0.012, s(y - 0.012) + 0.214), (y + 0.012, s(y + 0.012) + 0.214),
            (y + 0.012, s(y + 0.012) + 0.234), (y - 0.012, s(y - 0.012) + 0.234)]
    m.prism(prof, xa, xb, ['concD'], hull='none', skip=(0,))
