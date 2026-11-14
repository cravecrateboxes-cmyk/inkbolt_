"""kit-gemmine modelled detail (tactical look plan Stage 11): real-mine fixings on the pieces the player sees most,
in the style of cm_detail.py (whose collars, plates and sign frames are reused). Every part is ink=False, at least 3 mm
proud, embedded 3 mm, horizontal runs stop 5 mm short of the piece sides. Crystals and glow parts are never touched; the
pieces col_fit.py re-cuts collision for (Landmark_Chute, Landmark_GemHeart ...) only get detail outside the band the fit
reads (below 0.2 m, above 1.6 m)."""
from kit_base import PROUD, EMBED, bolt_row, junction_box, sign_plate, panel_seams
from cm_detail import (STEEL, STEEL_D, BOLT, face_plate, collar, sign_frame, lamp_bracket, prop_detail,
                       lamp_post_detail, crib_detail, trail_post)
import fam_kit_coalmine as CM

__all__ = ['cable_hook', 'lamp_bracket', 'prop_detail', 'lamp_post_detail', 'crib_detail', 'trail_post']


def cable_hook(k, z, y):
    """Clamp round the sagging power cable (wider than the lamp bulb under it) and a rock-bolt plate behind it."""
    k.bx(-0.036, 0.036, y - 0.026, y + 0.04, z - 0.125, z - 0.062, STEEL_D, ink=False)
    k.bx(-0.05, 0.05, y + 0.215, y + 0.235, z - 0.16, z - 0.03, STEEL, ink=False)


def nut(k, x, y, z, s=0.03, h=0.012):
    """A bolt head on an upward face whose top is at z."""
    k.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z - EMBED, z + h, BOLT, ink=False)


def foot_plate(k, cx, cy, zbase, hx, hy, bolts=4, c=STEEL_D):
    """A base plate 12 mm proud of a floor / deck at zbase (a post stands on it), with bolt heads at its corners."""
    k.bx(cx - hx, cx + hx, cy - hy, cy + hy, zbase - EMBED, zbase + 0.012, c, ink=False)
    if bolts:
        for sx in (-1, 1):
            for sy in ((-1, 1) if bolts == 4 else (0,)):
                nut(k, cx + sx * (hx - 0.03), cy + sy * (hy - 0.03), zbase + 0.012, s=0.026, h=0.01)


def rail_feet(k, x0, x1, y, z, post=1.5, axis='x'):
    """Plate + two bolts under every post of foundry_common.guard_rail (same post spacing). Rails along y use a
    slightly taller plate, so plates of two rails meeting at a corner never share a top plane."""
    n = max(1, int(round((x1 - x0) / post)))
    lift = 0.012 if axis == 'x' else 0.025
    for i in range(n + 1):
        u = x0 + (x1 - x0) * i / n
        cx, cy = (u, y) if axis == 'x' else (y, u)
        k.bx(cx - 0.08, cx + 0.08, cy - 0.08, cy + 0.08, z - (EMBED if axis == 'x' else 0.007), z + lift, STEEL_D, ink=False)
        for s in (-1, 1):   # across x on both axes: the bolt's y faces (+-20 mm) stay clear of the kick plates (+-15 / 21 mm)
            bx_ = cx + s * 0.055
            k.bx(bx_ - 0.013, bx_ + 0.013, cy - 0.02, cy + 0.02, z + lift - EMBED, z + lift + 0.009, BOLT, ink=False)


# ------------------------------------------------------------------ zone 1
def arch_detail(k, W, LEG, TOP, lamp):
    """Steel arch set: bolts on the foot plates, bolts on both faces of the fishplate joints, washers and nuts on the
    tie rod ends, a hanger clamp on the lamp crown."""
    for s in (-1, 1):
        cx = s * (W + 0.06)
        for sx in (-1, 1):
            for sy in (-1, 1):
                nut(k, cx + sx * 0.27, sy * 0.22, 0.08, s=0.04, h=0.014)
    for deg in (0, 180):
        k.push(0, 0, deg)
        for s in (-1, 1):
            bolt_row(k, s * W - 0.14, s * W + 0.14, LEG - 0.12, -0.2, 2, BOLT, s=0.034)
            bolt_row(k, s * W - 0.14, s * W + 0.14, LEG + 0.08, -0.2, 2, BOLT, s=0.034)
        k.pop()
    import math
    for x in (-2.6, 0.0, 2.6):
        a = math.acos(max(-1, min(1, x / W)))
        z = LEG + math.sin(a) * (TOP - LEG) - 0.1
        for sy in (-1, 1):
            k.bx(x - 0.045, x + 0.045, *sorted((sy * 0.495, sy * 0.512)), z - 0.045, z + 0.045, STEEL, ink=False)
            k.bx(x - 0.03, x + 0.03, *sorted((sy * 0.509, sy * 0.535)), z - 0.03, z + 0.03, STEEL_D, ink=False)
    if lamp:
        k.bx(-0.05, 0.05, -0.1, 0.1, TOP - 0.135, TOP - 0.112, STEEL_D, ink=False)   # hanger plate under the crown
        k.bx(-0.03, 0.03, -0.03, 0.03, TOP - 0.9, TOP - 0.84, STEEL_D, ink=False)    # clamp over the lamp's hook


def rail_detail(k, xs, y, gauge, x0, x1):
    """Single-bar rails: tie plates and two spikes per rail on each sleeper, fishplates on the bar ends."""
    top = CM.SLEEPER_TOP
    for x in xs:
        for s in (-1, 1):
            yc = y + s * gauge / 2
            k.bx(x - 0.05, x + 0.05, yc - 0.05, yc + 0.05, top - EMBED, top + 0.005, STEEL_D, ink=False)
            for d in (-1, 1):
                ys = yc + d * 0.034
                k.bx(x - 0.007, x + 0.007, ys - 0.007, ys + 0.007, top + 0.003, top + 0.026, BOLT, ink=False)
    for s in (-1, 1):
        yc = y + s * gauge / 2
        for xa, xb in ((x0 + 0.005, x0 + 0.14), (x1 - 0.14, x1 - 0.005)):
            for d in (-1, 1):
                ya, yb = sorted((yc + d * 0.027, yc + d * 0.036))
                k.bx(xa, xb, ya, yb, top + 0.018, top + 0.062, STEEL, ink=False)


def sign_wall(k, xh, z0, z1, yf=-0.6):
    """Wall signs: angle frame with corner bolts round the board (face at y = yf)."""
    sign_frame(k, xh, z0, z1, yf)


def fan_detail(k, YB, CEIL):
    """FanUnit: anchor bolts on the skid, lid screws on the motor terminal box, collars and bolts on the riser strut,
    hinges and a latch on the starter box."""
    bolt_row(k, -1.5, 0.9, 0.09, YB - 0.55, 4, BOLT, s=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            nut(k, -0.05 + sx * 0.2, YB + sy * 0.2, 1.9, s=0.026, h=0.011)
    for z in (1.5, 3.5, 5.5, 7.5):
        collar(k, 1.44, 1.56, 0.02, 0.14, z, z + 0.07)
        bolt_row(k, 1.47, 1.53, z + 0.035, 0.017, 1, BOLT, s=0.022)
    for z in (1.97, 2.45):
        k.bx(-1.49, -1.4, 0.35 - 0.008, 0.35 + EMBED, z, z + 0.06, STEEL_D, ink=False)
    k.bx(-0.97, -0.94, 0.35 - 0.012, 0.35 + EMBED, 2.1, 2.3, STEEL, ink=False)


def lamp_post_extra(k):
    """LanternPost: hanger plate on the arm over the lantern's hook already comes from the coal mine set."""
    lamp_post_detail(k)


def winch_detail(k, X0, X1, Y0, Y1, H):
    """Winch house: bolt rings on the drum flanges, anchor bolts in the bed, bolts in the bearing blocks, ribs and a
    plate on the motor, header plates and post shoes at the front, bolted girts inside the back wall."""
    import math
    for x, sg in ((-1.3, 1), (0.9, -1)):    # inner faces of the two flanges (-1.3 faces +x, 0.9 faces -x)
        for i in range(6):
            a = i * math.pi / 3 + 0.3
            y, z = 0.65 + math.cos(a) * 0.68, 1.15 + math.sin(a) * 0.68
            xa, xb = (x - EMBED, x + 0.012) if sg > 0 else (x - 0.012, x + EMBED)
            k.bx(xa, xb, y - 0.022, y + 0.022, z - 0.022, z + 0.022, BOLT, ink=False)
    for x in (-1.9, -0.6, 0.7, 2.0):    # anchor bolts with washers along the bed's front edge
        k.bx(x - 0.05, x + 0.05, -0.3, -0.2, 0.35 - EMBED, 0.362, STEEL_D, ink=False)
        nut(k, x, -0.25, 0.362, s=0.04, h=0.014)
    for (x0, x1) in ((-1.6, -1.4), (1.0, 1.2)):
        bolt_row(k, x0 + 0.03, x1 - 0.03, 0.5, 0.15, 1, BOLT, s=0.04)
    panel_seams(k, 1.34, 2.2, 0.4, 1.2, 0.2, 0.215, 'mach2')      # cooling ribs on the motor
    sign_plate(k, 1.6625, 0.62, 0.2, 0.17, 0.1, 'chalk', 'ink', bar=0.3)
    for sx, (a, b) in ((-1, (-2.95, -2.45)), (1, (2.45, 2.95))):
        face_plate(k, a, b, H - 0.38, H - 0.17, Y0 - 0.12, nx=2, m=0.04, s=0.026)
    for s in (-1, 1):
        k.bx(s * 2.7 - 0.12, s * 2.7 + 0.12, Y0 - 0.1, Y0 + 0.2, 0.0, 0.07, STEEL_D, ink=False)
        collar(k, s * 2.7 - 0.08, s * 2.7 + 0.08, Y0 - 0.05, Y0 + 0.15, 1.2, 1.27)
        bolt_row(k, s * 2.7 - 0.04, s * 2.7 + 0.04, 1.235, Y0 - 0.053, 2, BOLT, s=0.024)
    yg = Y1 - 0.12
    for z in (1.1, 2.3):    # girts across the back wall, bolted through
        k.bx(X0 + 0.12 + 0.005, X1 - 0.12 - 0.005, yg - 0.04, yg + EMBED, z, z + 0.1, 'timber2', ink=False)
        bolt_row(k, X0 + 0.4, X1 - 0.4, z + 0.05, yg - 0.04, 6, BOLT, s=0.03)


# ------------------------------------------------------------------ landmarks
def chute_detail(k, TX):
    """Ore bin: bolts along the timber rim on all four sides, bolts on the steel shoes of the legs (kept outside the
    0.2 - 1.6 m band the collision fit reads)."""
    for (x, y, deg, xr, yf) in ((0, 0, 0, (TX - 1.7, TX + 1.7), -2.38), (0, 0, 180, (-TX - 1.7, -TX + 1.7), -2.38)):
        k.push(x, y, deg)
        bolt_row(k, xr[0], xr[1], 5.37, yf, 6, BOLT, s=0.034)
        k.pop()
    for deg in (90, 270):
        k.push(TX, 0, deg)
        bolt_row(k, -2.3, 2.3, 5.37, -1.78, 5, BOLT, s=0.034)
        k.pop()
    for x in (TX - 1.15, TX + 1.15):
        for y in (-1.9, 1.9):
            for sx in (-1, 1):
                for sy in (-1, 1):
                    nut(k, x + sx * 0.175, y + sy * 0.175, 0.18, s=0.03, h=0.012)


def belt_bridge_detail(k, Z, trestles, BY):
    """Belt bridge: plate + bolts under every rail post, collars on the trestle legs and the deck posts, bolted straps
    on the lamp posts."""
    rail_feet(k, -5.5, 5.5, -1.36, Z, post=2.75)
    rail_feet(k, -5.5, 5.5, 0.25, Z, post=2.75)
    for x in trestles:
        for yy in (BY - 0.45, BY + 0.45):
            collar(k, x - 0.07, x + 0.07, yy - 0.07, yy + 0.07, 1.3, 1.36)
    for x in (-5.4, -1.8, 1.8, 5.4):
        for y in (-1.3, 0.1):
            collar(k, x - 0.06, x + 0.06, y - 0.06, y + 0.06, Z - 0.5, Z - 0.44)
    for x in (-4.6, 4.6):
        for z in (Z + 0.6, Z + 1.5):
            collar(k, x - 0.04, x + 0.04, 0.21, 0.29, z, z + 0.05)


def gallery_detail(k, Z):
    """Mining gallery: plate + bolts under every rail post, strap collars on the deck posts."""
    rail_feet(k, -8.0, -1.0, 0.0, Z, post=2.4)
    rail_feet(k, 1.0, 8.0, 0.0, Z, post=2.4)
    rail_feet(k, -1.0, 1.0, -2.05, Z, post=1.0)
    rail_feet(k, -8.0, 8.0, 1.9, Z, post=3.2)
    for s in (-1, 1):
        rail_feet(k, 0.05, 1.85, s * 8.05, Z, post=1.0, axis='y')
    for x in (-7.8, -3.9, 0.0, 3.9, 7.8):
        for y in ((0.2, 1.7) if x in (-7.8, 0.0, 7.8) else (1.7,)):
            collar(k, x - 0.12, x + 0.12, y - 0.12, y + 0.12, Z - 0.55, Z - 0.48)
    for y in (-1.85, -0.2):
        for x in (-1.0 + 0.12, 1.0 - 0.12):
            collar(k, x - 0.1, x + 0.1, y - 0.1, y + 0.1, Z - 0.55, Z - 0.48)


def platform_detail(k, Z):
    """Timber platform: plate + bolts under every rail post, collars on the deck posts, bolts on the winch cheeks."""
    rail_feet(k, -3.0, 0.5, -0.32, Z, post=3.5)
    rail_feet(k, 0.5, 3.0, -2.0, Z, post=2.5)
    rail_feet(k, -3.0, 3.0, 1.95, Z, post=3.0)
    rail_feet(k, -0.35, 1.9, -3.05, Z, post=2.25, axis='y')
    rail_feet(k, -1.95, 1.9, 3.05, Z, post=1.9, axis='y')
    for (x, y) in ((-2.85, -0.2), (-2.85, 1.75), (0.0, 1.75), (2.85, 1.75), (2.85, -1.8), (0.65, -1.8), (0.0, -0.2)):
        collar(k, x - 0.11, x + 0.11, y - 0.11, y + 0.11, Z - 0.5, Z - 0.44)
    for x in (-2.1, -1.3):
        k.bx(x - 0.044, x + 0.044, 0.9 - 0.008, 0.9 + EMBED, Z + 0.3, Z + 0.7, STEEL_D, ink=False)


def ledge_detail(k, Z):
    """Rock ledge: strap collars where the ramp hand rail meets its posts, a strap on the lantern post."""
    for y in (-0.95, 0.95):
        for x in (3.6, 1.8, 0.1):
            zz = Z * (4.0 - x) / 4.0
            collar(k, x - 0.04, x + 0.04, y - 0.04, y + 0.04, zz + 0.3, zz + 0.36)
    collar(k, -3.5, -3.4, -1.55, -1.45, Z + 0.7, Z + 0.76)
    collar(k, -3.5, -3.4, -1.55, -1.45, Z + 1.5, Z + 1.56)
    foot_plate(k, -3.45, -1.5, Z, 0.11, 0.11, bolts=4)


def hoist_detail(k):
    """Hoist: bolts on the A-frame foot plates, bolted straps on the apex timber, bolts on the winch skid."""
    for s in (-1, 1):
        for (y0, y1) in ((-1.0, -0.6), (1.6, 1.95)):
            yc = (y0 + y1) / 2
            for sx in (-1, 1):
                for sy in (-1, 1):
                    nut(k, s * 1.5 + sx * 0.14, yc + sy * (y1 - y0) / 2 * 0.65, 0.09, s=0.034, h=0.014)
    for a, b in ((-0.55, -0.2), (0.2, 0.55)):
        face_plate(k, a, b, 4.45, 4.65, 0.85, nx=2, m=0.04, s=0.024)
    bolt_row(k, -0.9, 0.9, 0.075, -1.7, 4, BOLT, s=0.03)


def table_detail(k, top_z=0.88, y_face=0.42, hx=0.85, hy=0.33):
    """Sorting table: strap collars at the leg tops, bolts along the front edge of the top."""
    for x in (-hx, hx):
        for y in (-hy, hy):
            collar(k, x - 0.045, x + 0.045, y - 0.045, y + 0.045, 0.6, 0.65)
    bolt_row(k, -0.8, 0.8, 0.84, -y_face, 6, BOLT, s=0.024)


def cut_bench_detail(k):
    """Lapidary bench: strap collars on the legs, bolts along the bench edge and the saw bed."""
    for x in (-0.85, 0.85):
        for y in (-0.35, 0.35):
            collar(k, x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.6, 0.65)
    bolt_row(k, -0.85, 0.85, 0.87, -0.45, 5, BOLT, s=0.026)


def sieve_detail(k):
    """Sieve: strap collars on the four legs."""
    for x in (-0.8, 0.8):
        for y in (-0.7, 0.7):
            collar(k, x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.5, 0.56)


# ------------------------------------------------------------------ chasm edge
def chasm_detail(k, variant):
    """Chasm railing: a bolted base plate under the post, bolts in the rails, a cap on the post; the lamp mast gets a
    base plate, strap collars and a junction box."""
    foot_plate(k, 0.0, -0.42, 0.0, 0.09, 0.07, bolts=4)
    for z in (0.555, 1.045):
        bolt_row(k, -0.03, 0.03, z, -0.47, 2, BOLT, s=0.026)
    k.bx(-0.06, 0.06, -0.48, -0.36, 1.15 - EMBED, 1.162, STEEL_D, ink=False)
    if variant == 'Lamp':
        k.bx(-0.11, 0.11, -0.335, -0.2, -EMBED, 0.02, STEEL_D, ink=False)
        for z in (0.6, 1.8):
            collar(k, -0.06, 0.06, -0.36, -0.24, z, z + 0.07)
        junction_box(k, 0.0, 1.45, -0.36, STEEL_D, STEEL, w=0.1, h=0.16, d=0.05)
