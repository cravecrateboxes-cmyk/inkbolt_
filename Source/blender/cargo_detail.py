"""kit-cargoship modelled detail (tactical look plan Stage 11): real-ship fixings on the pieces the player sees most.

Everything here draws painted-over-solid detail on a PM model: hull='none' (no outline shell), each part at least 3 mm
proud of what it sits on, starting E (3 mm) inside the face behind it, horizontal runs stopping 5 mm short of the
piece sides, tops of tall strips 5 mm below the piece top. A face looks toward Blender -Y when sy = -1 (the usual wall
module face) or +Y when sy = +1. Only palette names the kit already has are used.
"""
import math

from parking_base import poly

E = 0.003          # a part starts this far inside the face it sits on, so its back never lies on that face
STEEL, STEELD, GALV, STEELL = 'steel', 'steelD', 'galv', 'steelL'


# ------------------------------------------------------------------------------------------------ primitives
def fb(m, x0, x1, z0, z1, yf, sy, d, c, cull='b', emb=E):
    """box standing d proud of the face at y = yf (sy -1: toward -Y, +1: toward +Y), emb inside it"""
    if sy < 0:
        return m.bx(x0, x1, yf - d, yf + emb, z0, z1, c, hull='none', cull=cull + 'k')
    return m.bx(x0, x1, yf - emb, yf + d, z0, z1, c, hull='none', cull=cull + 'f')


def bolt(m, x, z, yf, sy, c=STEELD, s=0.026, d=0.010):
    """a bolt / rivet head: one square face standing 5 mm off the plate (4 vertices), like the kit's painted quads"""
    fb(m, x - s / 2, x + s / 2, z - s / 2, z + s / 2, yf, sy, 0.005, c, cull='btlr')


def bolt_xs(m, xs, z, yf, sy, c=STEELD, s=0.026, d=0.010):
    for x in xs:
        bolt(m, x, z, yf, sy, c, s, d)


def bolt_row(m, x0, x1, z, yf, sy, n, c=STEELD, s=0.026, d=0.010):
    for i in range(n):
        bolt(m, x0 + (x1 - x0) * (i + 0.5) / n, z, yf, sy, c, s, d)


def seam_h(m, x0, x1, z, yf, sy, c, h=0.016, d=0.009):
    """a raised weld bead / plate joint along x, ends 5 mm short of the piece sides"""
    fb(m, x0 + 0.005, x1 - 0.005, z - h / 2, z + h / 2, yf, sy, d, c, cull='blr')


def seam_v(m, x, z0, z1, yf, sy, c, w=0.014, d=0.006):
    """a raised vertical weld seam (its ends open: it runs into trims)"""
    fb(m, x - w / 2, x + w / 2, z0, z1, yf, sy, d, c, cull='btlr')


def kick(m, x0, x1, yf, sy, c, h=0.28, d=0.012, bolts=4):
    """a bolted kick plate along the foot of a face"""
    fb(m, x0 + 0.005, x1 - 0.005, 0.004, h, yf, sy, d, c, cull='blr')
    if bolts:
        bolt_row(m, x0 + 0.06, x1 - 0.06, h * 0.5, yf - (d if sy < 0 else -d), sy, bolts, STEELD, s=0.022, d=0.008)


def gauge(m, x, z, yf, sy, r=0.055, rim=STEELD, face='paper'):
    """a round pressure gauge: hex bezel drum, white dial 3 mm proud of it, red needle. Faces toward sy."""
    sg = float(sy)
    rot = (90, 0, 0) if sy < 0 else (-90, 0, 0)
    m.cy((x, yf - sg * E, z), r, r, 0.03 + E, rim, seg=6, rot=rot, hull='none')
    yd = yf + sg * 0.033
    poly(m, [(x + math.cos(i * math.pi / 3) * r * 0.78, yd, z + math.sin(i * math.pi / 3) * r * 0.78) for i in range(6)], face, (0, sg, 0))
    yn = yf + sg * 0.037
    poly(m, [(x - 0.004, yn, z), (x + 0.004, yn, z), (x + r * 0.5, yn, z + r * 0.45), (x + r * 0.5 - 0.008, yn, z + r * 0.45)], 'fireR', (0, sg, 0))


def flange_y(m, x, y, z, r, c=STEELL, sy=1, t=0.028, seg=8):
    """pipe flange (axis along Y) whose thickness runs from y toward sy"""
    rot = (-90, 0, 0) if sy > 0 else (90, 0, 0)
    m.cy((x, y, z), r, r, t, c, seg=seg, rot=rot, hull='none')


def flange_x(m, x, y, z, r, c=STEELL, t=0.028, seg=8):
    m.cy((x, y, z), r, r, t, c, seg=seg, rot=(0, 90, 0), hull='none')


def pad_eye(m, x, y, z, c=STEELD):
    """a deck tie-down point: base plate and an eye lug with its dark hole"""
    m.bx(x - 0.07, x + 0.07, y - 0.06, y + 0.06, z, z + 0.014, c, hull='none', cull='b')
    m.bx(x - 0.05, x + 0.05, y - 0.012, y + 0.012, z + 0.014 - E, z + 0.085, c, hull='none', cull='b')
    m.bx(x - 0.02, x + 0.02, y - 0.0165, y - 0.0155, z + 0.04, z + 0.07, 'ink', hull='none', cull='btlrk')


def post_foot(m, px, py, z0, x0, x1, hy=0.045):
    """base plate of a guard-rail stanchion; clamped inside the run's ends"""
    a, b = max(px - 0.055, x0 + 0.012), min(px + 0.055, x1 - 0.012)
    if b - a > 0.03:
        m.bx(a, b, py - hy, py + hy, z0, z0 + 0.014, STEELD, hull='none', cull='b')


def ladder_brackets(m, x, y, z0, z1, w, face, emb=E, every=5.5):
    """wall stand-off brackets under each stile of a ladder"""
    yo = y + face * 0.16
    n = max(2, int((z1 - z0) / every) + 1)
    for k in range(n):
        z = z0 + 0.5 + k * (z1 - z0 - 1.0) / (n - 1)
        ya, yb = (yo, y + emb) if face < 0 else (y - emb, yo)
        for sx in (-1, 1):
            xs = x + sx * w / 2
            m.bx(xs - 0.015, xs + 0.015, ya, yb, z, z + 0.05, STEELD, hull='none', cull='bfk')


# ------------------------------------------------------------------------------------------------ containers
CH_, CW_ = 2.6, 2.44


def casting(m, sx, sy, x, y, z, hx, hy, vis, bottom):
    """ISO corner casting, 178 x 162 x 118 mm: only its two outer faces are drawn (the rest is inside the box), with the
    oval aperture on the end face"""
    see_s = ('r' if sx > 0 else 'l') in vis
    see_e = ('n' if sy > 0 else 's') in vis
    if not (see_s or see_e):
        return
    cull = 'bt' + ('l' if sx > 0 else 'r') + ('f' if sy > 0 else 'k')
    if not see_s:
        cull += 'r' if sx > 0 else 'l'
    if not see_e:
        cull += 'k' if sy > 0 else 'f'
    xa, xb = sorted((x + sx * (hx - 0.162), x + sx * (hx + 0.012)))
    ya, yb = sorted((y + sy * (hy - 0.178), y + sy * (hy + 0.012)))
    z0 = z if bottom else z + CH_ - 0.118
    z1 = z + 0.118 if bottom else z + CH_
    m.bx(xa, xb, ya, yb, z0, z1, STEELD, hull='none', cull=cull)
    if see_e:
        xc = x + sx * (hx - 0.081)
        yp = y + sy * (hy + 0.0155)
        zc = (z0 + z1) / 2
        m.bx(xc - 0.045, xc + 0.045, yp - 0.0005, yp + 0.0005, zc - 0.022, zc + 0.022, 'ink', hull='none',
             cull='btlr' + ('f' if sy > 0 else 'k'))


def container_detail(m, x, y, z, L, door, vis, reefer, tier):
    """ground tier of a stack: corner castings at the foot, lever handles on the door's locking rods"""
    if tier:
        return
    hx, hy = CW_ / 2, L / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            casting(m, sx, sy, x, y, z, hx, hy, vis, True)


def flat_rod(m, a, b, sy, w=0.04):
    """a lashing rod seen from the front: one flat ribbon facing outward (the box behind it hides its back)"""
    dx, dz = b[0] - a[0], b[2] - a[2]
    n = math.hypot(dx, dz)
    px, pz = dz / n * w / 2, -dx / n * w / 2
    poly(m, [(a[0] + px, a[1], a[2] + pz), (a[0] - px, a[1], a[2] - pz), (b[0] - px, b[1], b[2] - pz), (b[0] + px, b[1], b[2] + pz)],
         GALV, (0, sy, 0))


def lashing_detail(m, x, y, z, sy):
    """a pad eye on the box foot under each lashing rod"""
    for sx in (-1, 1):
        a = x + sx * 1.0
        yb = y + sy * 0.07
        m.bx(a - 0.07, a + 0.07, min(y, yb + sy * 0.045), max(y, yb + sy * 0.045), z, z + 0.03, STEELD, hull='none', cull='b')


def seam_marking(m):
    """hatch-cover panel joint: a raised bead and a cleat"""
    m.bx(-0.495, 0.495, -0.022, 0.022, 0.0, 0.013, 'deckGD', hull='none', cull='b')
    m.bx(-0.07, 0.07, -0.1, 0.1, 0.0, 0.02, STEELD, hull='none', cull='b')


def sockets_marking(m):
    """twistlock sockets standing a little proud of the hatch cover"""
    for x in (-0.25, 0.25):
        m.bx(x - 0.09, x + 0.09, -0.06, 0.06, 0.0, 0.016, STEELD, hull='none', cull='b')


# ------------------------------------------------------------------------------------------------ bulwarks and decks
def bulwark_detail(m, v):
    """riveted rows and a stiffener bar on the plate (face y = -0.3), a tie-down eye on the deck"""
    if v != 'Rail':
        for z in (0.1, 0.9):
            bolt_xs(m, (-0.44, -0.28, -0.12, 0.12, 0.28, 0.44), z, -0.3, -1, STEELL, s=0.02)
        if v != 'Chock':
            fb(m, -0.495, -0.06, 0.5, 0.54, -0.3, -1, 0.012, 'supW', cull='blr')
            fb(m, 0.06, 0.495, 0.5, 0.54, -0.3, -1, 0.012, 'supW', cull='blr')
    if v == 'Plain':
        pad_eye(m, 0.3, -0.43, 0.0)


# ------------------------------------------------------------------------------------------------ superstructure
def porthole_collar(m, x, y, z, r, face=-1, seg=8):
    """a raised collar and lip round a round window at y: the glass sits recessed inside it"""
    rot = (90, 0, 0) if face < 0 else (-90, 0, 0)
    rr = r + 0.035
    m.cy((x, y - face * E, z), rr, rr, 0.035 + E, 'steelL', seg=seg, rot=rot, hull='none', caps=False)
    for i in range(seg):
        a0, a1 = i / seg * 2 * math.pi, (i + 1) / seg * 2 * math.pi
        poly(m, [(x + math.cos(a0) * r * 0.97, y + face * 0.0345, z + math.sin(a0) * r * 0.97),
                 (x + math.cos(a0) * rr, y + face * 0.0345, z + math.sin(a0) * rr),
                 (x + math.cos(a1) * rr, y + face * 0.0345, z + math.sin(a1) * rr),
                 (x + math.cos(a1) * r * 0.97, y + face * 0.0345, z + math.sin(a1) * r * 0.97)], 'steelL', (0, face, 0))


def sup_detail(m, kind, DECKS, H):
    """weld seams, riveted plate joints, window sills and hoods, door dogs and hinges on the deckhouse front (y = -0.5)"""
    yf = -0.5
    for x in (-0.455, 0.455):
        seam_v(m, x, 0.34, 12.72, yf, -1, 'supWD')
    for z in (3.6, 6.6, 9.6):
        seam_h(m, -0.5, 0.5, z, yf, -1, 'supWD', d=0.009)
    if kind != 'Blank':
        rows = [1.0 + d for d in DECKS[:3]]
        if kind == 'Top':
            rows = rows[:2]
        for z in rows:   # a sill under each window and a hood over it
            fb(m, -0.37, 0.37, z + 0.64, z + 0.69, yf, -1, 0.075, 'supW', cull='blr')
    if kind == 'Door':
        for z in (0.55, 0.85, 1.45, 1.75):
            fb(m, -0.35, -0.27, z, z + 0.07, -0.56, -1, 0.03, STEELD, cull='blr')
        for z in (0.5, 1.9):
            fb(m, 0.31, 0.36, z, z + 0.12, -0.56, -1, 0.03, STEELD, cull='blr')
        fb(m, -0.34, 0.34, 0.31, 0.5, -0.56, -1, 0.02, STEELD, cull='blr')
    elif kind == 'Vent':
        fb(m, -0.4, 0.4, 0.6, 0.66, yf, -1, 0.026, 'supWD', cull='blr')
        fb(m, -0.4, 0.4, 2.14, 2.2, yf, -1, 0.026, 'supWD', cull='blr')
    elif kind != 'Blank':
        porthole_collar(m, 0.0, -0.5, 1.7, 0.2, seg=8)


def fc_detail(m, v, FC):
    """forecastle bulkhead (y = -0.5): seams and rivets, door dogs"""
    yf = -0.5
    for x in (-0.455, 0.455):
        seam_v(m, x, 0.34, FC - 0.1, yf, -1, 'supWD')
    seam_h(m, -0.5, 0.5, 1.1, yf, -1, 'supWD', d=0.009)
    bolt_row(m, -0.4, 0.4, 2.7, yf, -1, 6, STEELD, s=0.018)
    if v == 'Door':
        for z in (0.75, 1.2, 1.65, 2.0):
            fb(m, 0.26, 0.34, z, z + 0.07, -0.56, -1, 0.03, STEELD, cull='blr')
        fb(m, -0.36, 0.36, 0.36, 0.52, -0.56, -1, 0.02, STEELD, cull='blr')


# ------------------------------------------------------------------------------------------------ hold and engine room walls
def hb_detail(m, v):
    """hold transverse bulkhead (web face y = -0.5, |x| < 0.2): bolted kick plate and weld seams"""
    yf = -0.5
    if v in ('Plain', 'Ladder', 'Lamp', 'Vent'):
        fb(m, -0.19, 0.19, 0.004, 0.27, yf, -1, 0.008, 'holdD', cull='blr')
        bolt_row(m, -0.15, 0.15, 0.14, yf - 0.008, -1, 4, STEELD, s=0.02)
        for z in (2.6, 5.4, 8.2):
            seam_h(m, -0.2, 0.2, z, yf, -1, 'holdD', h=0.014, d=0.006)


def hs_detail(m, v):
    """hold side shell: rivets along the stringers, kick plate, pipe clips, tie-down eyes"""
    if v == 'Web':
        return
    for z in (4.0, 8.4):
        bolt_xs(m, (-0.44, -0.32, -0.2, 0.2, 0.32, 0.44), z + 0.06, -0.49, -1, STEELL, s=0.02)
    fb(m, -0.495, 0.495, 0.004, 0.27, -0.4, -1, 0.012, 'holdD', cull='blr')
    if v == 'Plain':
        pad_eye(m, 0.25, -0.435, 0.0)
    elif v == 'Pipe':
        for z in (2.6, 8.4):
            fb(m, 0.255, 0.345, z, z + 0.05, -0.4, -1, 0.1, STEELD, cull='b')


H_ = 13.0


def er_detail(m, v):
    """engine room plating (face y = -0.42): weld seams, rivets down the stiffener, kick plate; per variant fittings"""
    yf = -0.42
    if v in ('Plain', 'Pipes', 'Panel', 'Tray'):
        seam_v(m, -0.465, 0.3, H_ - 0.3, yf, -1, 'supWD')
        seam_v(m, 0.465, 0.3, H_ - 0.3, yf, -1, 'supWD')
        for z in (3.2, 6.4):
            seam_h(m, -0.5, 0.5, z, yf, -1, 'supWD', d=0.009)
        for z in [1.0 + k * 1.8 for k in range(7)]:
            bolt(m, 0.0, z, -0.47, -1, STEELL, s=0.022)
    fb(m, -0.495, 0.495, 0.004, 0.27, yf, -1, 0.012, 'steelD', cull='blr')
    if v == 'Pipes':   # a gate valve on the fuel line: body, stem, handwheel
        m.bx(-0.07, 0.07, -0.56, -0.46, 3.0, 3.2, 'steelD', hull='none', cull='bk')
        m.cy((0.0, -0.56 + E, 3.1), 0.014, 0.014, 0.09, STEELL, seg=6, rot=(90, 0, 0), hull='none')
        fb(m, -0.06, 0.06, 3.04, 3.16, -0.65, -1, 0.012, 'fireR', cull='btlr', emb=0.0)
    elif v == 'Panel':   # starter panel: hinges, latch, nameplate
        for z in (0.55, 1.9):
            fb(m, -0.44, -0.4, z, z + 0.14, -0.5, -1, 0.03, STEELD, cull='blr')
        fb(m, 0.3, 0.38, 1.05, 1.12, -0.5, -1, 0.04, STEELD, cull='blr')
        fb(m, -0.12, 0.12, 2.0, 2.06, -0.5, -1, 0.012, STEELL, cull='blr')
        bolt_row(m, -0.3, 0.3, 0.34, -0.5, -1, 4, STEELL, s=0.02)
    elif v == 'Tray':   # tray side rails and cable clamps
        for sx in (-1, 1):
            xa, xb = sorted((sx * 0.224, sx * 0.238))
            fb(m, xa, xb, 0.3, H_ - 0.3, -0.5, -1, 0.062, GALV, cull='btlr')


# ------------------------------------------------------------------------------------------------ gate, stairs, rails
def gate_detail(m):
    """watertight door frame: more dogs, bolt columns, a bolted header"""
    for fy in (-1, 1):
        y = fy * 0.72
        for sx in (-1, 1):
            for z in (0.42, 1.2, 1.98, 2.76):
                bolt(m, sx * 1.58, z, y, fy, STEELL, s=0.024)
        bolt_row(m, -1.55, 1.55, 3.36, y, fy, 7, STEELL, s=0.024)


def stair_detail(m, W, L, rise, n, landing):
    """a grating bar across each tread"""
    run = (L - landing) / n
    for k in range(n):
        y0 = -L / 2 + k * run
        top = (k + 1) * rise / n
        m.bx(-W / 2 + 0.12, W / 2 - 0.12, y0 + 0.22, y0 + 0.25, top - 0.003, top + 0.004, STEELD, hull='none', cull='bflrfk')


def rail_detail(m, kind):
    """walkway rail module: stanchion base plate"""
    h = 0.06 if kind == 'full' else 0.07
    m.bx(-h, h, -h, h, 0.0, 0.014, STEELD, hull='none', cull='b')


# ------------------------------------------------------------------------------------------------ deck gear and machinery
def winch_detail(m):
    """hold-down nuts on the bed frame, gearbox cover plate with bolts"""
    for x in (-1.75, -0.4, 0.9, 1.75):
        for sy in (-1, 1):
            m.bx(x - 0.04, x + 0.04, sy * 1.08 - 0.04, sy * 1.08 + 0.04, 0.305, 0.3055, STEELL, hull='none', cull='bfkrl')
    fb(m, 0.78, 1.32, 0.45, 1.3, -0.55, -1, 0.012, 'engG', cull='blr')
    for x in (0.82, 1.28):
        for z in (0.49, 1.26):
            bolt(m, x, z, -0.562, -1, STEELD, s=0.024)


def bitts_detail(m):
    for x in (-0.8, 0.0, 0.8):
        for sy in (-1, 1):
            m.bx(x - 0.03, x + 0.03, sy * 0.28 - 0.03, sy * 0.28 + 0.03, 0.085, 0.0855, STEELL, hull='none', cull='bfkrl')


def pumps_detail(m):
    for x in (-0.45, 0.45):
        gauge(m, x, 1.1, -0.245, -1, r=0.05)


def manifold_detail(m):
    m.cy((0.11, 0.0, 0.96), 0.014, 0.014, 0.24, STEELD, seg=6, hull='none')
    gauge(m, 0.11, 1.26, 0.0, -1, r=0.06)


def airbottles_detail(m):
    m.cy((0.0, 0.0, 3.5 - E), 0.014, 0.014, 0.22, STEELD, seg=6, hull='none')
    gauge(m, 0.0, 3.82, 0.0, -1, r=0.06)


def tank_detail(m):
    """settling tank: manhole bolt ring, gauge, raised stiffener ribs"""
    gauge(m, -1.55, 3.0, -1.3, -1, r=0.07)
    for x in (-1.0, 1.0):
        fb(m, x - 0.05, x + 0.05, 0.004, 3.39, -1.3, -1, 0.026, 'supG', cull='btlr')


def boiler_detail(m):
    """burner door: perimeter bolts, hinge leaves, a latch"""
    yf = -1.5
    bolt_row(m, -0.5, 0.5, 1.5, yf, -1, 6, STEELL, s=0.03)
    bolt_row(m, -0.5, 0.5, 0.4, yf, -1, 6, STEELL, s=0.03)
    for z in (0.5, 1.2):
        fb(m, -0.58, -0.52, z, z + 0.16, yf, -1, 0.03, STEELD, cull='blr')
    fb(m, 0.4, 0.55, 0.9, 1.0, yf, -1, 0.06, STEELD, cull='blr')
