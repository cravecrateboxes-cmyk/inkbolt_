"""kit-scrapyard modelled detail (tactical look plan Stage 11): real-yard fixings on the pieces seen most.

Built on the kit_base detail helpers: every part is ink=False (no outline shell), at least 3 mm proud, embedded 3 mm,
horizontal runs stop 5 mm short of the piece sides. A face looking toward Blender -Y is drawn at y = yf in the current
frame (k.push(0, 0, 180) for the +Y face, push(x, y, 90) for +X, push(x, y, 270) for -X). Only palette names the kit
already has are used. Collision (k.col / colw) is never touched here.
"""
from kit_base import PROUD, EMBED, bolt_row, rivet_strip, vent, pipe_run, conduit_run, junction_box

ST, ST2, STD, GUN2, RUST2, HZ = 'steel', 'steel2', 'steelDark', 'gun2', 'rust2', 'hazard'


def nut(k, x, y, z0, s=0.05, h=0.04, c=STD):
    """A hex-nut stand-in (a small box) standing on a horizontal surface at z0."""
    k.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z0 - EMBED, z0 + h, c, ink=False)


def base_plate(k, x, y, w, d, t=0.03, nuts=0.05, inset=0.045):
    """A plate on the ground (centre x, y; w by d) with four anchor nuts."""
    k.bx(x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0.004, 0.004 + t, STD, ink=False)
    if nuts:
        for sx in (-1, 1):
            for sy in (-1, 1):
                nut(k, x + sx * (w / 2 - inset), y + sy * (d / 2 - inset), 0.004 + t, s=nuts, h=nuts * 0.8, c=ST2)


def window_frame(k, x0, x1, z0, z1, yf, depth=0.05, t=0.05, sill=True):
    """Frame standing out round an opening (the glass quads sit inside it); a drip sill below."""
    k.bx(x0 - t, x1 + t, yf - depth, yf + EMBED, z1, z1 + t, STD, ink=False)
    k.bx(x0 - t, x1 + t, yf - depth, yf + EMBED, z0 - t, z0, STD, ink=False)
    k.bx(x0 - t, x0, yf - depth, yf + EMBED, z0 + 0.004, z1 - 0.004, STD, ink=False)
    k.bx(x1, x1 + t, yf - depth, yf + EMBED, z0 + 0.004, z1 - 0.004, STD, ink=False)
    if sill:
        k.bx(x0 - t - 0.04, x1 + t + 0.04, yf - depth - 0.04, yf + EMBED, z0 - t - 0.03, z0 - t, ST2, ink=False)


def grille(k, x0, x1, z0, z1, yf, every=0.28, t=0.018):
    """Security bars over a window, tied into the frame at top and bottom."""
    n = max(2, int(round((x1 - x0) / every)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        k.bx(x - t / 2, x + t / 2, yf - 0.04, yf - 0.026, z0 - 0.004, z1 + 0.004, STD, ink=False)


# ------------------------------------------------------------------------------------------------ walls and gate
def trail_wall_detail(k, lamp=False):
    """Corrugated alley fence: sheet laps, rail bolts, a centre post on a base plate, a razor-wire coil on brackets."""
    yf = -0.05
    for z in (2.2, 4.3):   # sheet laps
        k.bx(-0.495, 0.495, yf - 0.014, yf + EMBED, z - 0.025, z + 0.025, STD, ink=False)
        bolt_row(k, -0.45, 0.45, z, yf - 0.014, 6, ST2, s=0.022)
    for z in (1.1, 3.4):   # bolt heads on the rails
        bolt_row(k, -0.44, 0.44, z + 0.06, -0.13, 5, ST2, s=0.026)
    k.bx(-0.035, 0.035, yf - 0.05, yf + 0.02, 0.3, 5.55, STD, ink=False)   # centre post channel
    k.bx(-0.07, 0.07, yf - 0.065, yf + 0.025, 0.27, 0.34, ST2, ink=False)     # its base plate
    for x in (-0.38, 0.38):   # razor-wire outriggers
        k.bx(x - 0.018, x + 0.018, -0.34, -0.05, 5.46, 5.5, STD, ink=False)
        k.bx(x - 0.018, x + 0.018, -0.34, -0.31, 5.5, 5.9, STD, ink=False)
    k.cyl(-0.495, -0.325, 5.78, 0.07, 0.07, 0.99, ST, seg=6, ink=False, rot=(0, 90, 0))
    if lamp:   # lamp bracket: a diagonal brace
        k.beam((0.0, -0.09, 4.0), (0.0, -0.4, 4.22), 0.03, STD, ink=False)


def gate_frame_detail(k):
    for s in (-1, 1):
        x0, x1 = (s * 1.5, s * 2.3) if s > 0 else (s * 2.3, s * 1.5)
        base_plate(k, (x0 + x1) / 2, 0.0, x1 - x0 + 0.34, 1.0, t=0.04, nuts=0.07)
        for f in (-1, 1):
            k.push(0, 0, 0 if f < 0 else 180)
            xa, xb = (x0, x1) if f < 0 else (-x1, -x0)
            yf = -0.42
            for zc in (5.0,):   # flange splice plates with bolts
                k.bx(xa + 0.04, xb - 0.04, yf - 0.012, yf + EMBED, zc, zc + 0.6, ST2, ink=False)
                bolt_row(k, xa + 0.1, xb - 0.1, zc + 0.1, yf - 0.012, 4, STD, s=0.04)
                bolt_row(k, xa + 0.1, xb - 0.1, zc + 0.5, yf - 0.012, 4, STD, s=0.04)
            k.pop()
    for f in (-1, 1):   # header rivets
        k.push(0, 0, 0 if f < 0 else 180)
        rivet_strip(k, -2.4, 2.4, 3.28, -0.5, STD, every=0.6, s=0.024)
        rivet_strip(k, -2.4, 2.4, 3.72, -0.5, STD, every=0.6, s=0.024)
        k.pop()


def gate_shutter_detail(k):
    for f in (-1, 1):
        k.push(0, 0, 0 if f < 0 else 180)
        yf = -0.06
        for z in (1.25, 2.2):   # stiffener rails
            k.bx(-1.4, 1.4, yf - 0.016, yf + EMBED, z - 0.04, z + 0.04, STD, ink=False)
            rivet_strip(k, -1.35, 1.35, z, yf - 0.016, ST2, every=0.3, s=0.02)
        for z in (0.8, 2.6):   # strap hinges at the leaf edge with their pins
            k.bx(-1.4, -0.75, yf - 0.02, yf + EMBED, z - 0.05, z + 0.05, ST2, ink=False)
            k.cyl(-1.4, yf - 0.03, z - 0.07, 0.04, 0.04, 0.14, STD, seg=6, ink=False)
        k.bx(1.1, 1.36, yf - 0.02, yf + EMBED, 1.5, 1.7, ST2, ink=False)    # hasp
        k.bx(1.2, 1.28, yf - 0.065, yf - 0.02 + EMBED, 1.3, 1.45, ST, ink=False)   # padlock body
        for i in range(5):   # chain hanging from the hasp, links alternately edge-on
            z = 1.28 - i * 0.075
            k.bx(1.21, 1.25, yf - 0.045 - (i % 2) * 0.012, yf - 0.025, z - 0.07, z, STD, ink=False)
        k.pop()


# ------------------------------------------------------------------------------------------------ office
def office_detail(k):
    X0, X1, Y0, Y1, ZB, ZT = -3.1, 3.1, -1.5, 1.5, 0.3, 3.1
    for sx in (-1, 1):   # corner castings and corner posts
        for sy in (-1, 1):
            cx, cy = (X0, X1)[sx > 0], (Y0, Y1)[sy > 0]
            xa, xb = (cx - 0.02, cx + 0.16) if sx < 0 else (cx - 0.16, cx + 0.02)
            ya, yb = (cy - 0.02, cy + 0.16) if sy < 0 else (cy - 0.16, cy + 0.02)
            k.bx(xa, xb, ya, yb, ZB + 0.004, ZB + 0.2, STD, ink=False)
            k.bx(xa, xb, ya, yb, ZT - 0.25, ZT - 0.05, STD, ink=False)
            xa2, xb2 = (cx - 0.012, cx + 0.06) if sx < 0 else (cx - 0.06, cx + 0.012)
            ya2, yb2 = (cy - 0.012, cy + 0.06) if sy < 0 else (cy - 0.06, cy + 0.012)
            k.bx(xa2, xb2, ya2, yb2, ZB + 0.2 - 0.003, ZT - 0.25 + 0.003, ST2, ink=False)
    bolt_row(k, -3.0, 3.0, ZT + 0.003, Y0 - 0.06, 12, STD, s=0.03)   # roof edge trim bolts
    # south face: the door with its frame, lock bars and handle
    yd = Y0 - 0.006
    k.bx(-2.66, -1.64, Y0 - 0.034, Y0 + EMBED, 2.35, 2.41, STD, ink=False)
    k.bx(-2.66, -2.6, Y0 - 0.034, Y0 + EMBED, 0.305, 2.35, STD, ink=False)
    k.bx(-1.7, -1.64, Y0 - 0.034, Y0 + EMBED, 0.305, 2.35, STD, ink=False)
    for x in (-2.4, -2.05):
        k.bx(x - 0.016, x + 0.016, yd - 0.02, yd + EMBED, 0.42, 2.3, ST2, ink=False)
        k.bx(x - 0.04, x + 0.04, yd - 0.032, yd + 0.006, 2.2, 2.26, STD, ink=False)
        k.bx(x - 0.04, x + 0.04, yd - 0.032, yd + 0.006, 0.46, 0.52, STD, ink=False)
    k.bx(-2.24, -2.2, yd - 0.05, yd + EMBED, 1.2, 1.34, 'chrome', ink=False)   # handle
    window_frame(k, -0.9, 1.9, 1.15, 2.35, Y0)
    grille(k, -0.9, 1.9, 1.15, 2.35, Y0)
    vent(k, -1.3, 1.85, Y0, 0.5, 0.5, STD, ST2)
    junction_box(k, 2.55, 1.65, Y0, GUN2, ST2)
    conduit_run(k, -2.9, 2.9, 2.75, Y0, STD, ST2, r=0.022, every=0.9)
    # steps: hazard nosing and a handrail on the west side
    k.bx(-2.84, -1.46, Y0 - 0.77, Y0 - 0.6, 0.27 - EMBED, 0.28, HZ, ink=False)
    for y in (Y0 - 0.72, Y0 - 0.1):
        k.bx(-2.81, -2.77, y - 0.02, y + 0.02, 0.262, 1.12, STD, ink=False)
    k.bx(-2.815, -2.765, Y0 - 0.73, Y0 - 0.09, 1.06, 1.1, STD, ink=False)
    k.bx(-2.815, -2.765, Y0 - 0.73, Y0 - 0.09, 0.66, 0.7, STD, ink=False)
    k.push(X1, 0, 90)   # east end window
    window_frame(k, -1.2, 1.2, 1.15, 2.4, 0.0)
    k.pop()
    vent(k, X0 - 0.31, 1.35, -0.5, 0.4, 0.5, STD, ST2)   # AC unit louvres


# ------------------------------------------------------------------------------------------------ baler and crane
def baler_detail(k):
    Y0, Y1 = 2.0, 5.2
    for i in range(1, 4):   # crushed-car panel seams (backs sunk 6 mm so they never meet the rivet heads' backs)
        x = -6.6 + 1.35 * i
        k.bx(x - 0.007, x + 0.007, Y0 - PROUD, Y0 + 0.006, 0.98, 2.28, RUST2, ink=False)
    rivet_strip(k, -6.5, -1.3, 1.3, Y0, STD, every=0.4, s=0.026)
    rivet_strip(k, -6.5, -1.3, 2.1, Y0, STD, every=0.4, s=0.026)
    yp = Y0 - 0.2   # press housing front
    for x in (-1.0, 2.8):
        k.bx(x - 0.007, x + 0.007, yp - PROUD, yp + 0.006, 1.0, 3.3, STD, ink=False)
    rivet_strip(k, -1.1, 2.9, 0.88, yp, STD, every=0.4, s=0.026)
    rivet_strip(k, -1.1, 2.9, 3.05, yp, STD, every=0.4, s=0.026)
    pipe_run(k, -1.1, 2.7, 0.66, yp, 0.04, 'cable', ST2, every=1.0)   # hydraulic line on stand-offs
    for x in (-0.6, 0.6, 1.8, 2.6):   # hose clamps
        k.bx(x - 0.03, x + 0.03, yp - 0.15, yp - 0.036, 0.66 - 0.055, 0.66 + 0.055, STD, ink=False)
    for (x, y) in ((-1.1, 0.5), (2.9, 0.5), (2.9, 1.7)):   # operator platform post base plates
        base_plate(k, x, y, 0.3, 0.3, t=0.025, nuts=0.04, inset=0.035)
    rivet_strip(k, 3.95, 6.85, 0.45, Y0 + 0.3, STD, every=0.45, s=0.024)   # roller table side
    rivet_strip(k, 3.1, 3.7, 1.1, Y0 + 0.4, STD, every=0.2, s=0.022)       # chute side


def crane_detail(k):
    cx, cy = 1.6, -3.4
    yc = cy - 2.7   # counterweight face
    rivet_strip(k, cx - 1.42, cx + 1.42, 1.72, yc, STD, every=0.3, s=0.026)
    rivet_strip(k, cx - 1.42, cx + 1.42, 2.47, yc, STD, every=0.3, s=0.026)
    for (x, deg) in ((cx - 1.75, 270), (cx - 0.35, 90)):   # cab window frames on both glass faces
        k.push(x, cy, deg)
        a, b = (-1.45, -0.15) if deg == 270 else (0.15, 1.45)
        window_frame(k, a, b, 5.0, 6.05, 0.0, depth=0.03, t=0.04, sill=False)
        k.pop()


# ------------------------------------------------------------------------------------------------ tower, hatch, post
def flood_tower_detail(k):
    k.bx(-0.62, 0.62, -0.62, 0.62, 0.5 - EMBED, 0.54, STD, ink=False)   # mast base plate on the footing
    for sx in (-1, 1):
        for sy in (-1, 1):
            nut(k, sx * 0.54, sy * 0.54, 0.54, s=0.07, h=0.06, c=ST2)
    for z in (2.5, 5.0, 7.5, 10.0, 12.2):   # ladder stand-offs
        for x in (-0.18, 0.18):
            k.bx(x - 0.02, x + 0.02, -0.5, -0.42, z, z + 0.05, STD, ink=False)
    vent(k, 0.7, 1.15, -0.35, 0.34, 0.24, STD, ST2)   # cabinet: vent, latch, door seam, bolts
    k.bx(0.88, 0.92, -0.38, -0.35 + EMBED, 0.8, 0.95, ST2, ink=False)
    k.bx(0.46, 0.94, -0.355, -0.35 + EMBED, 0.66, 0.672, STD, ink=False)
    bolt_row(k, 0.5, 0.9, 1.33, -0.35, 4, STD, s=0.026)
    bolt_row(k, -1.05, 1.05, 12.68, -1.1, 8, STD, s=0.034)   # head frame edge bolts


def hatch_detail(k):
    C0, C1, W, H = 1.05, 2.6, 1.3, 4.4
    for x in (-W, W):
        base_plate(k, x, C0, 0.4, 0.4, t=0.03, nuts=0.05)
    rivet_strip(k, -W - 0.05, W + 0.05, H + 0.12, C0 - 0.1, STD, every=0.3, s=0.026)
    yd = C1 - 0.083 - 0.003   # cross rails over the corrugated leaf
    for z in (0.9, 2.2):
        k.bx(-W + 0.1, W - 0.1, yd - 0.016, yd + EMBED, z, z + 0.08, STD, ink=False)
        rivet_strip(k, -W + 0.15, W - 0.15, z + 0.04, yd - 0.016, ST2, every=0.3, s=0.02)


def beacon_post_detail(k):
    k.bx(-0.14, 0.14, -0.14, 0.14, 0.25 - EMBED, 0.28, STD, ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            nut(k, sx * 0.1, sy * 0.1, 0.28, s=0.04, h=0.03, c=ST2)


# ------------------------------------------------------------------------------------------------ wrecks, skips
def _skip_y(z):
    return 0.85 + (0.92 - 0.85) * z / 1.45


def skip_detail(k, seed):
    for sy in (-1, 1):
        for z0 in (0.28, 1.2):   # welded stiffener bands that follow the slope of the skip side
            z1 = z0 + 0.08
            ya, yb = _skip_y(z0), _skip_y(z1)
            pts = []
            for x in (-1.5, 1.5):
                for (y, z) in ((ya - 0.004, z0), (ya + 0.014, z0), (yb - 0.004, z1), (yb + 0.014, z1)):
                    pts.append((x, sy * y, z))
            k.hullp(pts, STD, ink=False)
    # a patch plate peeling off the -Y side (broken, not tidy)
    k.bxr(0.55 + 0.4 * (seed % 2), -0.945, 0.8, 0.6, 0.03, 0.34, RUST2 if seed % 2 else GUN2, rot=(-9, 0, 2), ink=False)


def barrier_detail(k):
    for x in (-0.3, 0.3):   # steel lifting pins on top
        k.bx(x - 0.03, x + 0.03, -0.012, 0.012, 0.8 - EMBED, 0.85, STD, ink=False)
        k.bx(x - 0.04, x + 0.04, -0.02, 0.02, 0.84, 0.86, STD, ink=False)


def scaffold_detail(k):
    Ya, Yb, Yc = -1.95, -0.65, 0.65
    posts = ((-5.8, Ya + 0.1, 3.0), (-5.8, Yb - 0.1, 3.0), (0.8, Ya + 0.1, 3.0), (0.8, Yb - 0.1, 3.0), (-5.8, 1.85, 3.0),
             (0.55, Yc - 0.5, 6.0), (0.55, 1.86, 6.0), (5.8, Yc - 0.5, 6.0), (5.8, 1.86, 6.0))
    for (x, y, top) in posts:
        base_plate(k, x, y, 0.26, 0.26, t=0.02, nuts=0)
        for z in (1.4,):   # couplers
            k.bx(x - 0.075, x + 0.075, y - 0.075, y + 0.075, z, z + 0.05, STD, ink=False)


def reactor_detail(k):
    for (x, y) in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)):   # base plates under the hazard posts
        k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.4 - EMBED, 0.43, STD, ink=False)
        for sx in (-1, 1):
            for sy in (-1, 1):
                nut(k, x + sx * 0.155, y + sy * 0.155, 0.43, s=0.045, h=0.035, c=ST2)


def arm_detail(k):
    yf = -0.95
    for x in (1.2, 2.3):   # seams above the hazard band
        k.bx(x - 0.007, x + 0.007, yf - PROUD, yf + 0.006, 0.85, 1.85, STD, ink=False)
    rivet_strip(k, 0.65, 2.75, 1.7, yf, ST2, every=0.3, s=0.024)
    k.bxr(1.75, yf - 0.02, 1.2, 0.8, 0.03, 0.55, RUST2, rot=(-8, 0, 0), ink=False)   # a panel hanging loose
    for x in (3.2, 5.4):   # elbow clamp plates
        bolt_row(k, x - 0.1, x + 0.1, 1.55, -0.85, 3, STD, s=0.03)
        bolt_row(k, x - 0.1, x + 0.1, 0.4, -0.85, 3, STD, s=0.03)
