"""INKBOLT guns: LMG, sniper and rail rifle. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def _poff(pts, d):
    """offset an open polyline section [(x, z)] by d along its left normals (miter joins)"""
    P = [V(p) for p in pts]
    out = []
    for i, p in enumerate(P):
        ns = []
        if i > 0:
            e = (p - P[i - 1]).normalized()
            ns.append(V((-e.y, e.x)))
        if i < len(P) - 1:
            e = (P[i + 1] - p).normalized()
            ns.append(V((-e.y, e.x)))
        m = sum(ns, V((0, 0))).normalized()
        q = p + m * (d / max(m.dot(ns[0]), 0.35))
        out.append((q.x, q.y))
    return out


def vent_shield(k, y0, y1, pts, th=0.0035, n=6, rib=0.008, open=None, color='gun2', rib_color=None, edge=0.27, end=0.012, hull=True, strip_hull=False):
    """Open heat shield over a barrel: `pts` is an open section [(x, z)] running clockwise seen from behind (left foot,
    over the top, right foot). Thin wall strips with a real slot in every face listed in `open` (all by default)
    between raised hoops; you see the barrel through the slots. Returns the hoops' (y0, y1)."""
    I = _poff(pts, -th)
    nf = len(pts) - 1
    for i in range(nf):
        p0, p1, q0, q1 = V(pts[i]), V(pts[i + 1]), V(I[i]), V(I[i + 1])
        if open is None or i in open:
            for (a, b) in ((0.0, edge), (1.0 - edge, 1.0)):
                quad = [p0.lerp(p1, a), p0.lerp(p1, b), q0.lerp(q1, b), q0.lerp(q1, a)]
                k.ext_y([tuple(v) for v in quad], y0 + 0.003, y1 - 0.003, color, hull=strip_hull)
        else:
            k.ext_y([tuple(p0), tuple(p1), tuple(q1), tuple(q0)], y0 + 0.003, y1 - 0.003, color, hull=strip_hull)
    O2, I2 = _poff(pts, PR), _poff(pts, -th - 0.002)
    O2[0], O2[-1] = (O2[0][0], O2[0][1] - 0.002), (O2[-1][0], O2[-1][1] - 0.002)
    I2[0], I2[-1] = (I2[0][0], O2[0][1]), (I2[-1][0], O2[-1][1])
    span = (y1 - y0 - 2 * end) / n
    ys = [(y0, y0 + end)] + [(y0 + end + span * i - rib / 2, y0 + end + span * i + rib / 2) for i in range(1, n)] + [(y1 - end, y1)]
    for (a, b) in ys:
        k.ext_y(O2 + list(reversed(I2)), a, b, rib_color or color, hull=hull)
    return ys


def belt_round(k, c, tip='steel2', seg=6):
    """one cartridge lying along +y at c (case head 15 mm behind c)"""
    k.lathe([(-0.015, 0), (-0.015, 0.0050), (0.004, 0.0050), (0.008, 0.0032), (0.018, 0)], 'brass', 'y', c, seg, hull=False,
            bands=[None, None, None, tip], a0=0)


def grooves(k, y0, y1, r, z, n=3, x=0.0, color='ink', seg=10, fill=0.44, axis='y', c=None):
    """n dark grip rings around a cylinder of radius r (cheaper than knurl: open bands, no inner faces)"""
    pitch = (y1 - y0) / n
    for i in range(n):
        yc = y0 + pitch * (i + 0.5)
        k.lathe([(yc - pitch * fill / 2, r - 0.001), (yc - pitch * fill / 2, r + PR), (yc + pitch * fill / 2, r + PR), (yc + pitch * fill / 2, r - 0.001)],
                color, axis, c or (x, 0, z), seg, hull=False, caps=(False, False))


def build_brick(pal):
    """LMG-26 Bricklayer: belt-fed heavy LMG. Riveted receiver with a hinged feed cover (latch, rail, tangent rear
    sight), feed tray on the left with the belt coming up from the brick ammo box through a chute, ejection port,
    cocking slot and handle on the right, quick-change barrel in a vented heat shield (real slots: the barrel shows),
    carry handle, gas block with regulator, folded bipod on a yoke, windowed stock with the hydraulic buffer in it,
    flip-up shoulder rest."""
    rake = 20
    k = Kit(pal)
    bz = 0.044
    HR, HC, HT, HF = 0.029, 0.025, 0.023, 0.023          # half widths: receiver, feed cover, trigger housing, forend

    def rivets(kk, hw, pts, sides=(-1, 1), r=0.0026):
        for s in sides:
            for y, z in pts:
                bolt(kk, (s * hw, y, z), (s, 0, 0), r, 0.0022, socket=False)

    # ---- receiver
    k.ext_y(rrect(0.058, 0.082, ct=0.010, cb=0.004, cy=0.040), -0.130, 0.155, 'gunmetal', ch0=0.005, ch1=0.004)
    plate(k, rect(-0.100, 0.064, 0.0075, 0.0115), HR, 'trim', ch=0)                                               # accent line
    plate(k, [(0.072, 0.006), (0.148, 0.006), (0.148, 0.036), (0.140, 0.044), (0.072, 0.044)], HR, 'gunmetal', t=0.003, hull=True)   # trunnion block
    bolts(k, HR + 0.003, [(0.079, 0.012), (0.079, 0.038), (0.141, 0.012)], sides=(1,))
    rivets(k, HR + 0.003, [(0.141, 0.012), (0.079, 0.038)], sides=(-1,), r=0.0030)
    # left: data panel, riveted rails, slanted vents, barrel latch, feed port and tray
    plate(k, [(-0.120, 0.020), (-0.034, 0.020), (-0.026, 0.028), (-0.026, 0.066), (-0.120, 0.066)], HR, 'body2', sides=(-1,))
    stencil(k, 'LMG-26', HR + PR, -0.073, 0.043, cap=0.013, sides=(-1,))
    stencil(k, 'CAL 7.62', HR + PR, -0.073, 0.030, cap=0.0055, sides=(-1,), font='cond')
    rivets(k, HR + PR, [(-0.114, 0.026), (-0.114, 0.060), (-0.032, 0.060)], sides=(-1,))
    plate(k, [(-0.018, 0.048), (0.150, 0.048), (0.150, 0.057), (-0.012, 0.057)], HR, 'gunmetal', t=0.003, sides=(-1,), hull=True)
    rivets(k, HR + 0.003, [(-0.006 + i * 0.030, 0.0525) for i in range(3)] + [(0.144, 0.0525)], sides=(-1,))
    plate(k, rect(-0.018, 0.066, 0.020, 0.028), HR, 'gunmetal', t=0.003, sides=(-1,), hull=True)
    rivets(k, HR + 0.003, [(-0.010 + i * 0.034, 0.024) for i in range(3)], sides=(-1,))
    slots(k, HR, -0.012, 0.060, 0.038, 4, h=0.012, fill=0.4, sides=(-1,), slant=-28)
    k.xbar(-HR - 0.0070, -HR - 0.0030, [(0.136, 0.022), (0.144, 0.022), (0.144, 0.030), (0.134, 0.042), (0.128, 0.040)], 'gun3', ch=0.0008, hull=False)   # barrel latch
    bolt(k, (-HR - 0.0070, 0.140, 0.026), (-1, 0, 0), 0.0026)
    k.box((-(HR + PR / 2 - 0.0005), 0.105, 0.0665), (PR + 0.001, 0.052, 0.009), 'ink', skip=sk(-1))               # feed port
    k.box((-(HR + 0.0055), 0.105, 0.0598), (0.013, 0.058, 0.003), 'steel', hull=True)                             # feed tray
    sling_loop(k, -0.112, 0.012, -1, hw=HR, r=0.0050)
    # right: ejection port with the bolt in it, open dust cover, brass deflector, link port, cocking slot and handle
    k.box((HR + PR / 2 - 0.0005, 0.020, 0.048), (PR + 0.001, 0.060, 0.018), 'ink', skip=sk(1))
    k.box((HR + PR, 0.010, 0.049), (0.0036, 0.036, 0.011), 'steel', skip=sk(1))
    k.box((HR + 0.003, 0.020, 0.0335), (0.006, 0.058, 0.007), 'gun3', hull=True)
    k.ext_x([(-0.030, 0.038), (-0.012, 0.038), (-0.012, 0.058), (-0.022, 0.058)], HR - 0.001, HR + 0.007, 'gunmetal', ch=0.0015)
    k.box((HR + PR / 2 - 0.0005, 0.110, 0.0650), (PR + 0.001, 0.034, 0.008), 'ink', skip=sk(1))
    hazard(k, HR, 0.062, 0.142, 0.047, 0.057, n=6, sides=(1,))
    k.box((HR + PR / 2 - 0.0005, -0.006, 0.0205), (PR + 0.001, 0.140, 0.006), 'ink', skip=sk(1))
    k.box((HR + 0.0025, 0.036, 0.0205), (0.003, 0.026, 0.003), 'steel2')
    k.cbox((HR + 0.006, 0.054, 0.0205), (0.016, 0.012, 0.011), 'gun3', ch=0.002, axis='x')
    plate(k, rect(-0.120, -0.040, 0.028, 0.066), HR, 'body2', sides=(1,))
    stencil(k, 'BRICKLAYER', HR + PR, -0.080, 0.043, cap=0.008, sides=(1,))
    rivets(k, HR + PR, [(-0.114, 0.060), (-0.046, 0.060)], sides=(1,))
    # ---- feed cover: hinge at the front, latch at the rear, rail, stamped ribs; tangent rear sight
    k.ext_y(rrect(0.050, 0.012, ct=0.004, cb=0.0, cy=0.0855), -0.110, 0.130, 'gun3', ch0=0.004, ch1=0.004)
    k.pin(-0.0285, 0.0285, 0.137, 0.0845, 0.0030, color='steel2')
    for x in (-0.017, 0.017):
        k.cbox((x, 0.137, 0.0845), (0.012, 0.012, 0.012), 'gun3', ch=0.003, axis='x', hull=False)
    k.cbox((0, 0.139, 0.0835), (0.018, 0.012, 0.009), 'gunmetal', ch=0.003, axis='x', hull=False)
    k.cbox((0, -0.118, 0.0845), (0.038, 0.012, 0.009), 'body2', ch=0.002, axis='x')
    for s in (-1, 1):
        k.box((s * 0.0195, -0.118, 0.0845), (0.006, 0.007, 0.005), 'steel2')
        for i in range(4):
            k.box((s * 0.0150, -0.036 + i * 0.044, 0.0915 + PR / 2 - 0.0005), (0.006, 0.026, PR + 0.001), 'acc2', skip=('-z',))
    slots(k, HC, -0.096, 0.114, 0.0838, 6, h=0.0035, fill=0.5)
    rail(k, -0.056, 0.116, 0.0915, w=0.018, pitch=0.010)
    k.cbox((0, -0.084, 0.0935), (0.030, 0.036, 0.006), 'gunmetal', ch=0.0015, axis='y')
    k.ext_x([(-0.100, 0.096), (-0.068, 0.096), (-0.068, 0.099), (-0.078, 0.107), (-0.100, 0.103)], -0.0055, 0.0055, 'gunmetal', ch=0.001)
    for s in (-1, 1):
        k.ext_x([(-0.097, 0.102), (-0.089, 0.104), (-0.089, 0.114), (-0.095, 0.114)], min(s * 0.002, s * 0.0075), max(s * 0.002, s * 0.0075), 'gunmetal', ch=0.0006, hull=False)
        k.ext_x([(-0.102, 0.096), (-0.084, 0.096), (-0.088, 0.110), (-0.100, 0.110)], min(s * 0.0105, s * 0.0135), max(s * 0.0105, s * 0.0135), 'gunmetal', ch=0.0008, hull=False)
    k.pin(-0.017, 0.017, -0.074, 0.1005, 0.0042, color='steel2')
    # ---- trigger housing, safety, ammo box rail
    k.ext_y(rrect(0.046, 0.030, c=0.003, cy=-0.006), -0.090, 0.090, 'gun2', ch0=0.004, ch1=0.004)
    cross_pin(k, HT, -0.074, -0.0095, r=0.0030)
    rivets(k, HT, [(0.046, -0.0095)], r=0.0034)
    k.lathe([(HT - 0.003, 0.0046), (HT + 0.0050, 0.0046), (HT + 0.0050, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.020, -0.0095), 8,
            hull=False, caps=(False, True), bands=['red', None])
    k.lathe([(HT - 0.003, 0.0046), (HT + 0.0040, 0.0046), (HT + 0.0040, 0)], 'steel2', 'x', (0, 0.020, -0.0095), 8, hull=False, caps=(False, True))
    k.cbox((0, 0.105, -0.0045), (0.039, 0.072, 0.008), 'body2', ch=0.002, axis='x')
    # ---- barrel group: socket collar, barrel, vented heat shield, carry handle
    k.lathe([(0.118, 0), (0.118, 0.0120), (0.404, 0.0120), (0.404, 0.0105), (0.470, 0.0105), (0.470, 0)], 'steel', 'y', (0, 0, bz), 10)
    k.lathe([(0.150, 0), (0.150, 0.0185), (0.170, 0.0185), (0.174, 0.0150), (0.178, 0.0150), (0.178, 0)], 'steel2', 'y', (0, 0, bz), 10)
    grooves(k, 0.154, 0.170, 0.0185, bz, n=2, seg=10)
    sh = [(-0.022, bz - 0.004), (-0.022, bz + 0.011), (-0.011, bz + 0.022), (0.011, bz + 0.022), (0.022, bz + 0.011), (0.022, bz - 0.004)]
    hy = vent_shield(k, 0.182, 0.376, sh, n=5, rib=0.008, color='gun2')
    hz = bz + 0.052
    k.tube([((0, 0.190, bz + 0.010), 0.012, 0.010), ((0, 0.200, hz), 0.012, 0.010), ((0, 0.280, hz), 0.012, 0.010),
            ((0, 0.290, bz + 0.010), 0.012, 0.010)], 'gun3', sides=6, up=(1, 0, 0))
    for y in (0.1970, 0.2875):
        k.cbox((0, y, bz + 0.0245), (0.022, 0.018, 0.008), 'steel2', ch=0.002, axis='y', hull=False)
    k.lathe([(0.212, 0), (0.212, 0.0085), (0.268, 0.0085), (0.268, 0)], 'furn', 'y', (0, 0, hz), 8)
    grooves(k, 0.218, 0.262, 0.0085, hz, n=2, seg=8)
    # ---- gas system, forend, bipod on its yoke
    k.lathe([(0.156, 0), (0.156, 0.008), (0.384, 0.008), (0.384, 0)], 'steel2', 'y', (0, 0, 0.012), 8, hull=True)
    k.ext_y(octa(0.030, 0.056, 0.008, 0.0, 0.029), 0.380, 0.402, 'steel2', ch0=0.002, ch1=0.002)
    k.lathe([(0.400, 0), (0.400, 0.0095), (0.412, 0.0095), (0.412, 0.0065), (0.420, 0.0065), (0.420, 0)], 'steel', 'y', (0, 0, 0.012), 8, hull=False)
    k.ext_y(rrect(0.046, 0.034, ct=0.006, cb=0.010, cy=0.012), 0.152, 0.300, 'gun2', ch1=0.006)
    for s in (-1, 1):
        for z in (0.009, 0.014, 0.019):
            k.box((s * (HF + PR / 2 - 0.0005), 0.228, z), (PR + 0.001, 0.108, 0.0022), 'ink', skip=sk(s))
        rivets(k, HF, [(0.162, 0.014), (0.288, 0.014)], sides=(s,), r=0.0030)
        k.cbox((s * 0.016, 0.3835, 0.008), (0.009, 0.091, 0.009), 'steel2', ch=0.002, axis='y')
        k.cbox((s * 0.016, 0.322, 0.008), (0.006, 0.040, 0.006), 'steel', ch=0.0015, axis='y', hull=False)
        k.box((s * 0.016, 0.302, 0.006), (0.011, 0.014, 0.013), 'rubber', hull=True)
        rivets(k, 0.023, [(0.428, 0.012)], sides=(s,), r=0.0034)
    k.ring('y', (0, 0, bz), 0.420, 0.434, 0.0100, 0.0160, 'steel2', seg=10, hull=False)
    k.cbox((0, 0.428, 0.018), (0.046, 0.010, 0.022), 'steel2', ch=0.003, axis='y')
    # ---- front sight tower, flash hider
    k.ring('y', (0, 0, bz), 0.442, 0.456, 0.0100, 0.0150, 'gunmetal', seg=8, hull=False)
    k.ext_x([(0.4435, bz + 0.012), (0.4545, bz + 0.012), (0.4525, 0.100), (0.4455, 0.100)], -0.0045, 0.0045, 'gunmetal', ch=0.001)
    k.box((0, 0.449, 0.1045), (0.0030, 0.004, 0.013), 'ink')
    for s in (-1, 1):
        k.ext_x([(0.443, 0.096), (0.455, 0.096), (0.453, 0.113), (0.445, 0.113)], min(s * 0.0045, s * 0.0075), max(s * 0.0045, s * 0.0075), 'gunmetal', ch=0.0006, hull=False)
    k.lathe([(0.466, 0), (0.466, 0.0140), (0.500, 0.0175), (0.512, 0.0175), (0.512, 0.0080), (0.500, 0.0080), (0.500, 0)], 'steel', 'y', (0, 0, bz), 12,
            bands=[None, None, None, None, 'ink', 'ink'])
    for i in range(6):
        a = D(30 + 60 * i)
        k.box((0.0160 * math.cos(a), 0.497, bz + 0.0160 * math.sin(a)), (0.006, 0.018, 0.0045), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    trigger_guard(k, rake, front=0.056, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    # ---- stock: socket block, top beam with cheek pad, lower strut, butt block; the buffer shows in the window
    k.ext_x([(-0.126, 0.072), (-0.172, 0.0701), (-0.172, -0.0025), (-0.126, 0.006)], -0.022, 0.022, 'furn', ch=0.004)
    k.ext_x([(-0.290, 0.0652), (-0.320, 0.064), (-0.322, -0.046), (-0.296, -0.050), (-0.290, -0.0476)], -0.022, 0.022, 'furn', ch=0.004)
    k.ext_x([(-0.166, 0.068), (-0.296, 0.0627), (-0.296, 0.046), (-0.166, 0.046)], -0.0195, 0.0195, 'furn', ch=0.003)
    k.ext_x([(-0.166, 0.0196), (-0.296, -0.032), (-0.296, -0.0475), (-0.166, 0.004)], -0.0195, 0.0195, 'furn', ch=0.003)
    k.lathe([(-0.168, 0), (-0.168, 0.0105), (-0.236, 0.0105), (-0.236, 0.0060), (-0.294, 0.0060), (-0.294, 0)], 'steel2', 'y', (0, 0, 0.031), 10,
            bands=[None, None, None, 'steel', 'steel'])
    grooves(k, -0.286, -0.244, 0.0060, 0.031, n=3, color='rubber', seg=10, fill=0.5)
    cross_pin(k, 0.022, -0.148, 0.036, r=0.0045)
    with k.at((0, -0.229, 0.0654), (2.33, 0, 0)):
        k.cbox((0, 0, 0.0012), (0.030, 0.082, 0.0055), 'rubber', ch=0.002, axis='y')
        top_slots(k, 0.00395, -0.036, 0.036, 6, w=0.022, fill=0.3)
    k.cbox((0, -0.296, 0.0688), (0.032, 0.040, 0.0036), 'steel2', ch=0.0012, axis='z')                           # shoulder rest, folded
    top_slots(k, 0.0706, -0.310, -0.284, 3, w=0.020, fill=0.4)
    k.pin(-0.019, 0.019, -0.3145, 0.0672, 0.0036, color='steel')
    k.ext_x([(-0.318, 0.070), (-0.336, 0.070), (-0.338, -0.050), (-0.320, -0.054)], -0.0265, 0.0265, 'rubber', ch=0.003)
    for i in range(5):
        z = 0.056 - i * 0.024
        yf = -0.336 - (0.070 - z) / 0.120 * 0.002 - PR
        k.box((0, (yf - 0.323) / 2, z), (0.053 + 2 * PR, -0.323 - yf, 0.005), 'ink')
    for s in (-1, 1):
        sling_loop(k, -0.306, 0.046, s, hw=0.022, r=0.006)
    # ---- brick ammo box (the Mag): lid with hinge and latch, ribs, stencils, the chute and the belt up to the feed tray
    mk = Kit(pal)
    HB = 0.032
    mk.cbox((0, 0, -0.050), (0.064, 0.090, 0.088), 'gun3', ch=0.005, axis='z')
    mk.cbox((0, 0, -0.098), (0.070, 0.096, 0.010), 'gun2', ch=0.003, axis='z')
    mk.cbox((0, 0, -0.0045), (0.068, 0.094, 0.008), 'gun2', ch=0.002, axis='z')
    for y in (-0.024, 0.024):
        mk.lathe([(y - 0.009, 0), (y - 0.009, 0.0032), (y + 0.009, 0.0032), (y + 0.009, 0)], 'steel2', 'y', (0.0355, 0, -0.009), 6, hull=False)
    mk.box((0, 0.048, -0.010), (0.016, 0.004, 0.014), 'steel2')
    for s in (-1, 1):
        for y in (-0.033, 0.033):
            mk.box((s * (HB + 0.001), y, -0.052), (0.004, 0.006, 0.070), 'gun2', skip=sk(s))
        mk.box((0, s * 0.0455, -0.052), (0.024, 0.004, 0.076), 'gun2', skip=('-y' if s > 0 else '+y',))
    plate(mk, rect(-0.026, 0.026, -0.086, -0.038, 0.004), HB, 'acc2')
    stencil(mk, '200', HB + PR, 0.0, -0.070, cap=0.018)
    hazard(mk, HB, -0.026, 0.020, -0.033, -0.025, n=4)
    mk.ext_y([(-0.028, -0.022), (-0.028, -0.006), (-0.044, -0.004), (-0.044, 0.040), (-0.063, 0.040), (-0.063, -0.010), (-0.052, -0.024)], -0.021, 0.021,
             'gun2', ch0=0.002, ch1=0.002)
    mk.box((-0.0535, 0, 0.040 + PR / 2 - 0.0005), (0.016, 0.036, PR + 0.001), 'ink', skip=('-z',))
    belt = [(-0.0305, 0.0785), (-0.0415, 0.0780), (-0.0505, 0.0715), (-0.0535, 0.0605), (-0.0535, 0.0490)]
    for i, (x, z) in enumerate(belt):
        belt_round(mk, (x, 0, z), tip='red' if i == 2 else 'steel2')
    mk.tube([((x, -0.004, z), 0.0175, 0.0113) for x, z in belt + [(-0.0535, 0.0390)]], 'steel2', sides=4, up=(0, 1, 0), hull=False)

    # ---- Rare (and up): bolted strike plate, rail saddle on the shield with an aiming module, its cable and pressure
    # switch, round counter beside the feed cover, hook under the butt, armoured chute
    r3 = Kit(pal)
    plate(r3, [(-0.014, 0.0305), (0.062, 0.0305), (0.062, 0.0455), (-0.008, 0.0455), (-0.014, 0.0395)], HR, 'gun3', t=0.0035, sides=(-1,), hull=True)
    bolts(r3, HR + 0.0035, [(-0.008, 0.034), (0.056, 0.034), (0.056, 0.042)], sides=(-1,))
    slots(r3, HR + 0.0035, 0.002, 0.047, 0.038, 3, h=0.008, fill=0.4, sides=(-1,), slant=-28)
    r3.cbox((0, 0.337, bz + 0.0245), (0.020, 0.070, 0.005), 'gun3', ch=0.0015, axis='y')
    rail(r3, 0.304, 0.370, bz + 0.027, w=0.018, pitch=0.010)
    laser_box(r3, 0.347, bz + 0.003, s=1, hw=0.0235, L=0.044, w=0.018, h=0.022, color='gun2')
    cable(r3, [(0.0305, 0.326, 0.046), (0.0265, 0.306, 0.039), (0.0265, 0.190, 0.039), (0.0270, 0.168, 0.036), (0.0345, 0.152, 0.031), (0.0350, 0.132, 0.030)], clamps=(2,))
    r3.cbox((HR + 0.005, 0.118, 0.030), (0.006, 0.030, 0.012), 'rubber', ch=0.0015, hull=False)
    r3.cbox((-(HC + 0.004), -0.070, 0.08575), (0.010, 0.044, 0.0125), 'gun2', ch=0.002, hull=True)
    for i in range(4):
        r3.box((-(HC + 0.009) - PR / 2 + 0.0005, -0.082 + i * 0.008, 0.0865), (PR + 0.001, 0.005, 0.006), 'emis', skip=sk(-1))
    top_slots(r3, 0.092, -0.086, -0.054, 4, w=0.005, fill=0.6, color='emis', x=-(HC + 0.004))
    r3.ext_x([(-0.256, -0.028), (-0.292, -0.042), (-0.292, -0.068), (-0.281, -0.068), (-0.277, -0.056), (-0.252, -0.046)], -0.009, 0.009, 'gun3', ch=0.0015)
    rivets(r3, 0.009, [(-0.285, -0.058)], r=0.0030)
    m3 = Kit(pal)
    m3.cbox((-0.0535, 0, 0.010), (0.0235, 0.047, 0.026), 'gun3', ch=0.002, axis='z')
    for y in (-0.014, 0.014):
        bolt(m3, (-0.06525, y, 0.010), (-1, 0, 0))

    # ---- Epic (and up): the barrel glows through the shield vents, cooling fins on the barrel socket, a conduit from
    # the stock along the receiver to the barrel, a glow ring behind the flash hider; Epic alone carries the energy cell
    # in the stock window (Legendary swaps it for the prism)
    r4 = Kit(pal)
    r4.lathe([(0.187, 0), (0.187, 0.0150), (0.371, 0.0150), (0.371, 0)], 'emis', 'y', (0, 0, bz), 10, hull=False)
    r4.ring('y', (0, 0, bz), 0.1545, 0.1695, 0.0170, 0.0225, 'gun2', seg=10)
    grooves(r4, 0.1560, 0.1680, 0.0225, bz, n=2, color='emis', seg=10, fill=0.5)
    conduit(r4, [(0.006, -0.246, 0.002), (0.0225, -0.232, -0.012), (0.0225, -0.176, 0.008), (0.0252, -0.164, 0.008), (0.0262, -0.132, 0.000),
                 (0.0275, -0.120, -0.002), (0.0275, 0.146, -0.002), (0.0275, 0.156, 0.008), (0.0185, 0.168, 0.037)], r=0.0028, every=2)
    r4.ring('y', (0, 0, bz), 0.4575, 0.4650, 0.0105, 0.0150, 'emis', seg=8, hull=False)
    m4 = Kit(pal)
    m4.box((-0.063 - PR / 2 + 0.0005, 0, 0.031), (PR + 0.001, 0.010, 0.012), 'emis', skip=sk(-1))
    for s in (-1, 1):
        m4.box((0, s * (0.0475 + PR / 2 - 0.0005), -0.052), (0.008, PR + 0.001, 0.044), 'emis', skip=('-y' if s > 0 else '+y',))
    r4o = Kit(pal)
    energy_cell(r4o, (0, -0.266, 0.004), L=0.052, r=0.0085, cage_bars=3)

    # ---- Legendary (oil-slick chrome): swept chrome exhaust stacks with glowing throats along the heat shield, a
    # prism core floating in the stock window, glowing feed cover ribs, a halo on the flash hider, chrome-bound ammo box
    r5 = Kit(pal)
    gaps = [(a[1] + b[0]) / 2 for a, b in zip(hy[:-1], hy[1:])]
    for s in (-1, 1):
        ax = V((s * 0.62, -0.45, 0.64)).normalized()
        u = ax.orthogonal().normalized()
        for yc in gaps[:4]:
            r5.lathe([(-0.006, 0.0064), (0.036, 0.0064), (0.041, 0.0080), (0.041, 0.0052), (0.032, 0.0052), (0.032, 0)], 'steel', (ax, u, ax.cross(u)),
                     (s * 0.0165, yc + 0.006, bz + 0.0165), 6, bands=[None, None, 'trim', 'emis', 'emis'], caps=(False, True))
        for i in range(4):
            r5.box((s * 0.0150, -0.036 + i * 0.044, 0.0915 + PR * 1.5), (0.004, 0.022, PR), 'trim')
        r5.box((s * (0.0195 + PR / 2 - 0.0005), -0.230, 0.0510), (PR + 0.001, 0.100, 0.0028), 'trim', skip=sk(s))
        r5.bar((s * 0.0198, -0.184, 0.0040), (s * 0.0198, -0.284, -0.0357), PR * 2, 0.0028, 'trim')
    with r5.at((0, -0.262, 0.004)):
        r5.lathe([(-0.027, 0), (-0.009, 0.012), (0.009, 0.012), (0.027, 0)], 'emis', 'y', (0, 0, 0), 6, hull=False)
        r5.ring('y', (0, 0, 0), -0.0015, 0.0015, 0.0145, 0.0165, 'trim', seg=8, hull=False)
        r5.lathe([(-0.030, 0), (-0.030, 0.0060), (-0.017, 0.0095), (-0.017, 0)], 'steel', 'y', (0, 0, 0), 6, hull=False, a0=0)
    for i in range(6):
        with r5.at((0, 0, bz), (0, 60 * i, 0)):
            r5.ext([(0.469, 0.0150), (0.509, 0.0180), (0.505, 0.0270), (0.490, 0.0235)], 'steel', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0015, 0.0015)
    r5.ring('y', (0, 0, bz), 0.5045, 0.5085, 0.0165, 0.0215, 'trim', seg=12, hull=False)
    m5 = Kit(pal)
    for (sx, sy, a) in ((1, 1, 45), (-1, 1, 135), (-1, -1, 225), (1, -1, 315)):
        m5.box((sx * 0.0299, sy * 0.0429, -0.052), (0.004, 0.010, 0.072), 'steel', rot=(0, 0, a), hull=True)
    for z in (-0.0200, -0.0830):
        m5.box((0, 0, z), (0.073, 0.099, 0.003), 'trim')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.010), 'muzzle': (0, 0.514, bz), 'eject': (0.03, 0.020, 0.048),
                   'sight': (0, -0.095, 0.110), 'cls': 'rifle', 'guard': (0, 0.292, 0.012),
                   'layers': {'345': r3, '45': r4, '4': r4o, '5': r5}, 'mag_layers': {'345': m3, '45': m4, '5': m5}}


def build_needle(pal):
    """SR-160 Needle: bolt-action sniper on a folding chassis. Round action with an open port (the bolt shows), bolt
    shroud, handle and knob; fluted heavy barrel on a barrel nut; tank brake with open ports (you see through it);
    chassis with a magwell, paddle release and a slotted forend; long scope on bolted rings with a turret saddle,
    throw lever and bubble level; skeleton stock on a hinge with a cheek piece and butt pad on rods with thumb wheels,
    and a monopod.
    Rarity layers: Rare bolts on a rangefinder with its cable, an offset reflex, a ballistic computer, an ammo cuff
    and a magwell funnel; Epic adds accelerator coils fed by a conduit, plasma in the brake ports and (Epic alone) an
    energy cell in the stock; Legendary (damascus and ivory) crowns the brake with leaf blades, rings the barrel in
    gold, sets ivory medallions with a gold star in the chassis, feathers the forend and hangs an armillary in the
    stock."""
    rake = 22
    k = Kit(pal)
    bz = 0.032
    HCH = 0.0225

    def rivets(kk, hw, pts, sides=(-1, 1), r=0.0028):
        for s in sides:
            for y, z in pts:
                bolt(kk, (s * hw, y, z), (s, 0, 0), r, 0.0022, socket=False)

    # ---- action: port with the bolt in it, shroud with cocking indicator, bolt handle and knob, safety, barrel nut
    k.lathe([(-0.112, 0), (-0.112, 0.016), (-0.106, 0.020), (0.100, 0.020), (0.106, 0.016), (0.106, 0)], 'gunmetal', 'y', (0, 0, bz), 12, a0=0)
    apo = 0.020 * math.cos(D(15))
    with k.at((0, 0.010, bz), (0, -15, 0)):
        k.box((apo + PR / 2 - 0.0005, 0, 0), (PR + 0.001, 0.056, 0.0085), 'ink', skip=('-x',))
        k.box((apo + PR, -0.008, 0), (0.0036, 0.034, 0.0055), 'steel', skip=('-x',))
    k.tube([((0.016, -0.074, bz + 0.004), 0.008, 0.008), ((0.034, -0.078, bz - 0.006), 0.007, 0.007), ((0.046, -0.082, bz - 0.020), 0.007, 0.007)], 'steel', sides=6, up=(0, 1, 0))
    k.lathe([(0.0, 0), (0.0, 0.006), (0.006, 0.010), (0.016, 0.010), (0.020, 0.005), (0.020, 0)], 'steel2', (V((0.5, -0.1, -0.86)).normalized(), V((0, 1, 0)), V((0.86, 0, 0.5))), (0.042, -0.081, bz - 0.014), 8)
    k.lathe([(-0.136, 0), (-0.136, 0.0100), (-0.130, 0.0135), (-0.106, 0.0135), (-0.106, 0)], 'gun3', 'y', (0, 0, bz), 8)
    k.lathe([(-0.140, 0), (-0.140, 0.0034), (-0.134, 0.0034), (-0.134, 0)], 'red', 'y', (0, 0, bz), 6, hull=False)
    k.cbox((0.0125, -0.121, bz + 0.0075), (0.008, 0.014, 0.0045), 'steel2', ch=0.001, rot=(0, -30, 0), hull=False)
    k.lathe([(0.098, 0), (0.098, 0.0170), (0.116, 0.0170), (0.116, 0)], 'steel2', 'y', (0, 0, bz), 8)
    k.box((-0.0200, -0.010, bz), (0.004, 0.110, 0.011), 'body2')                                                   # machined flat, proof marks, gas vents
    stencil(k, 'IB-338 LONG ACTION', 0.022, -0.020, bz - 0.002, cap=0.0042, sides=(-1,), font='cond', t=0.0)
    for y in (0.028, 0.037):
        k.box((-0.022 - PR / 2 + 0.0005, y, bz), (PR + 0.001, 0.005, 0.005), 'ink', skip=sk(-1))
    # ---- chassis: side plates with stencils, magwell, paddle release, forend slots, trim line
    k.ext_x([(-0.100, 0.020), (0.320, 0.020), (0.330, 0.010), (0.330, -0.016), (0.120, -0.024), (0.080, -0.030), (-0.100, -0.030)], -HCH, HCH, 'gun3', ch=0.004)
    plate(k, [(-0.094, -0.014), (0.086, -0.014), (0.098, -0.002), (0.098, 0.014), (-0.094, 0.014)], HCH, 'acc2')
    stencil(k, 'SR-160', HCH + PR, -0.034, -0.002, cap=0.011, sides=(-1,))
    stencil(k, '.338 IB ARMS', HCH + PR, -0.034, -0.010, cap=0.0045, sides=(-1,), font='cond')
    stencil(k, 'NEEDLE', HCH + PR, -0.034, -0.005, cap=0.009, sides=(1,))
    bolts(k, HCH + PR, [(-0.084, 0.006), (0.088, 0.004)])
    k.xbar(-HCH - 0.0040, -HCH + 0.0010, [(-0.092, 0.011), (-0.076, 0.011), (-0.078, 0.019), (-0.090, 0.019)], 'steel2', ch=0.0008, hull=False)   # bolt release
    k.ext_x([(0.012, -0.026), (0.090, -0.026), (0.088, -0.041), (0.014, -0.041)], -0.0255, 0.0255, 'acc2', ch=0.002)
    slots(k, 0.0255, 0.026, 0.078, -0.0335, 3, h=0.007, fill=0.4)
    k.xbar(-0.006, 0.006, [(0.092, -0.024), (0.100, -0.024), (0.104, -0.044), (0.098, -0.046), (0.094, -0.036)], 'steel2', ch=0.001)
    slots(k, HCH, 0.139, 0.309, 0.005, 5, h=0.011, fill=0.65)
    plate(k, rect(0.140, 0.320, -0.0115, -0.0085), HCH, 'trim', ch=0)
    rivets(k, HCH, [(0.120, 0.006), (0.321, -0.002)])
    for s in (-1, 1):
        top_slots(k, 0.020, 0.140, 0.310, 5, w=0.004, fill=0.6, x=s * 0.0155)
    # ---- bipod, folded under the forend on its mount
    k.cbox((0, 0.318, -0.0225), (0.040, 0.016, 0.019), 'steel2', ch=0.003, axis='y')
    rivets(k, 0.020, [(0.318, -0.024)], r=0.0034)
    for s in (-1, 1):
        k.cbox((s * 0.012, 0.262, -0.026), (0.008, 0.116, 0.008), 'steel2', ch=0.002, axis='y')
        k.box((s * 0.012, 0.207, -0.0265), (0.011, 0.014, 0.013), 'rubber', hull=True)
    rail(k, -0.104, 0.098, bz + 0.0195, w=0.020, pitch=0.014, clear=[(-0.074, -0.054), (0.044, 0.064)])
    # ---- fluted barrel, tank brake with open ports
    k.lathe([(0.100, 0), (0.100, 0.0125), (0.150, 0.0125), (0.156, 0.0110), (0.600, 0.0090), (0.600, 0)], 'steel', 'y', (0, 0, bz), 12)
    for i in range(6):
        a = D(30 + 60 * i)
        r0, r1 = 0.01094 * math.cos(D(15)) + 0.0005, 0.00918 * math.cos(D(15)) + 0.0005
        k.bar((r0 * math.cos(a), 0.170, bz + r0 * math.sin(a)), (r1 * math.cos(a), 0.560, bz + r1 * math.sin(a)), 0.0030, 0.0024, 'ink', up=(math.cos(a), 0, math.sin(a)))
    k.cbox((0, 0.606, bz), (0.030, 0.016, 0.032), 'steel2', ch=0.003, axis='y')
    rivets(k, 0.015, [(0.606, bz - 0.008), (0.606, bz + 0.008)], r=0.0026)
    for s in (-1, 1):
        k.cbox((0, 0.637, bz + s * 0.0115), (0.036, 0.058, 0.005), 'steel2', ch=0.0015, axis='y')
    for y in (0.632, 0.650, 0.6655):
        k.box((0, y, bz), (0.040, 0.005, 0.020), 'steel2', hull=True)
    top_slots(k, bz + 0.014, 0.616, 0.661, 3, w=0.012, fill=0.5)
    muzzle(k, 0.6665, 0.672, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # ---- scope: turret saddle, turrets, bolted rings, throw lever, bubble level
    sz = bz + 0.062
    scope(k, -0.150, 0.180, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    for yy in (-0.064, 0.054):
        k.cbox((0, yy, bz + 0.033), (0.024, 0.016, 0.022), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
        for s in (-1, 1):
            bolt(k, (s * 0.0117, yy, sz + 0.0117), (s * 0.707, 0, 0.707), 0.0024, 0.0026, socket=False)
        k.lathe([(0.011, 0.0048), (0.0175, 0.0048), (0.0175, 0)], 'steel2', 'x', (0, yy, bz + 0.027), 6, hull=False, caps=(False, True))
    k.cbox((0, -0.004, sz), (0.029, 0.024, 0.029), 'gunmetal', ch=0.005, axis='y')
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    turret(k, (-0.010, -0.010, sz), '-x', r=0.008, h=0.009, cap='gun3')
    grooves(k, 0.007, 0.015, 0.010, 0, n=2, seg=8, axis='z', c=(0, -0.004, sz + 0.010), color='mark')
    with k.at((0, -0.106, sz), (0, 40, 0)):
        k.cbox((-0.0255, 0, 0), (0.009, 0.006, 0.005), 'gun3', ch=0.001, hull=False)                                # throw lever
    k.lathe([(-0.027, 0), (-0.027, 0.0036), (-0.011, 0.0036), (-0.011, 0)], 'lens', 'x', (0, -0.064, bz + 0.041), 6, hull=False,
            bands=['steel2', None, 'steel2'])                                                                        # bubble level
    grooves(k, 0.150, 0.176, 0.024, sz, n=2, seg=12)
    grooves(k, -0.147, -0.139, 0.019, sz, n=1, seg=12, fill=0.6)
    trigger_guard(k, rake, front=0.068, depth=-0.054, w=0.012, top=-0.024, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.022, ptop=-0.040)
    # ---- skeleton stock: hinge, top bar, cheek piece and butt pad on rods with thumb wheels, lower strut, monopod
    k.cbox((0, -0.108, -0.004), (0.036, 0.020, 0.060), 'steel2', ch=0.003, axis='z')
    k.lathe([(-0.039, 0), (-0.039, 0.0050), (0.031, 0.0050), (0.031, 0)], 'steel', 'z', (0.0165, -0.1165, 0), 6, hull=False)
    k.cbox((0, -0.2015, 0.020), (0.020, 0.185, 0.020), 'gun3', ch=0.004, axis='y')
    slots(k, 0.010, -0.172, -0.124, 0.020, 3, h=0.008, fill=0.5)
    rivets(k, 0.0125, [(-0.289, 0.024), (-0.289, -0.056)], r=0.0030)
    for s in (-1, 1):
        sling_loop(k, -0.108, -0.022, s, hw=0.018, r=0.006)
    for y in (-0.250, -0.200):
        k.lathe([(0.028, 0), (0.028, 0.0030), (0.038, 0.0030), (0.038, 0)], 'steel', 'z', (0, y, 0), 6, hull=False)
    k.cbox((0, -0.225, 0.043), (0.026, 0.090, 0.014), 'furn', ch=0.004, axis='y')
    top_slots(k, 0.050, -0.262, -0.188, 6, w=0.016, fill=0.3)
    k.lathe([(0.008, 0.0075), (0.017, 0.0075), (0.017, 0.0030), (0.019, 0.0030), (0.019, 0)], 'steel2', 'x', (0, -0.225, 0.020), 8, caps=(False, True),
            bands=[None, 'ink', None, None])
    k.bar((0, -0.100, -0.024), (0, -0.290, -0.056), 0.020, 0.016, 'gun3', hull=True)
    k.ext_x([(-0.280, 0.034), (-0.297, 0.036), (-0.299, -0.068), (-0.280, -0.066)], -0.0125, 0.0125, 'gun3', ch=0.002)
    for z in (0.016, -0.046):
        k.lathe([(-0.306, 0), (-0.306, 0.0035), (-0.297, 0.0035), (-0.297, 0)], 'steel', 'y', (0, 0, z), 6, hull=False)
    k.lathe([(-0.3035, 0), (-0.3035, 0.0090), (-0.2995, 0.0090), (-0.2995, 0)], 'steel2', 'y', (0, 0, -0.014), 8, hull=False)
    k.ext_x([(-0.304, 0.042), (-0.318, 0.040), (-0.320, -0.076), (-0.304, -0.076)], -0.0215, 0.0215, 'rubber', ch=0.003)
    for i in range(5):
        z = 0.028 - i * 0.023
        yf = -0.318 - (0.040 - z) / 0.116 * 0.002 - PR
        k.box((0, (yf - 0.3085) / 2, z), (0.043 + 2 * PR, -0.3085 - yf, 0.005), 'ink')
    k.lathe([(0, 0), (0, 0.0085), (-0.030, 0.0085), (-0.030, 0.0110), (-0.036, 0.0110), (-0.036, 0.0055), (-0.056, 0.0055), (-0.056, 0.0090), (-0.060, 0.0090),
             (-0.060, 0)], 'steel2', 'z', (0, -0.262, -0.050), 8, bands=[None, None, 'gun3', 'gun3', 'gun3', 'steel', 'rubber', 'rubber', 'rubber'])
    mk = Kit(pal)
    mag_box(mk, 4, 0.034, -0.040, 0.060, 0.026, plate='gun2', ribs=True, wt=0.62)

    # ---- Rare (and up)
    r3 = Kit(pal)
    laser_box(r3, 0.176, 0.004, s=-1, hw=HCH, L=0.046, w=0.016, h=0.020, color='gun2')
    cable(r3, [(-0.0300, 0.154, 0.006), (-0.0270, 0.140, 0.018), (-0.0200, 0.120, 0.040), (-0.0150, 0.086, 0.056), (-0.0130, 0.060, 0.060)], clamps=(2,))
    with r3.at((0, 0.054, sz), (0, 45, 0)):
        hood_sight(r3, -0.012, 0.012, 0.0160, w=0.022, h=0.018, t=0.004, color='gun2')
    r3.cbox((-0.0235, -0.064, sz), (0.012, 0.030, 0.020), 'gun2', ch=0.002, hull=True)
    for i in range(3):
        r3.box((-0.0235, -0.079 - PR / 2 + 0.0005, sz + 0.005 - i * 0.005), (0.007, PR + 0.001, 0.003), 'emis', skip=('+y',))
    top_slots(r3, sz + 0.010, -0.074, -0.054, 2, w=0.006, fill=0.5, color='emis', x=-0.0235)
    r3.cbox((0.0125, -0.150, 0.019), (0.006, 0.050, 0.020), 'rubber', ch=0.0015, hull=True)
    for i in range(4):
        r3.lathe([(0.008, 0), (0.008, 0.0042), (0.030, 0.0042), (0.034, 0.0028), (0.040, 0)], 'brass', 'z', (0.0185, -0.168 + i * 0.012, 0), 6, hull=False)
    r3.ext_x([(0.006, -0.036), (0.096, -0.036), (0.100, -0.050), (0.002, -0.050)], -0.0285, 0.0285, 'gun3', ch=0.002)
    rivets(r3, 0.0285, [(0.014, -0.043), (0.088, -0.043)])

    # ---- Epic (and up)
    r4 = Kit(pal)
    for y in (0.400, 0.460, 0.520):
        r4.ring('y', (0, 0, bz), y, y + 0.026, 0.0090, 0.0175, 'gun2', seg=10, hull=False)
        grooves(r4, y + 0.003, y + 0.023, 0.0175, bz, n=2, color='emis', seg=10, fill=0.5)
    conduit(r4, [(0.012, -0.160, -0.004), (0.0210, -0.122, -0.012), (0.0255, -0.096, -0.020), (0.0255, 0.004, -0.020), (0.0285, 0.016, -0.020),
                 (0.0285, 0.092, -0.020), (0.0255, 0.110, -0.016), (0.0250, 0.128, 0.012), (0.0165, 0.140, 0.032), (0.0165, 0.398, 0.032)], r=0.0028, every=3)
    r4.lathe([(0.612, 0), (0.612, 0.0045), (0.661, 0.0045), (0.661, 0)], 'emis', 'y', (0, 0, bz), 6, hull=False)
    grooves(r4, 0.1605, 0.1655, 0.024, sz, n=1, color='emis', seg=12, fill=0.6)
    r4o = Kit(pal)
    energy_cell(r4o, (0, -0.190, -0.004), L=0.052, r=0.0085, cage_bars=3)
    r4o.cbox((0, -0.190, 0.008), (0.012, 0.030, 0.008), 'gun2', ch=0.002, axis='y', hull=False)
    m4 = Kit(pal)
    a, b = g2w(4, 0.0305, -0.014), g2w(4, 0.0305, -0.038)
    m4.bar((0, a[0], a[1]), (0, b[0], b[1]), 0.008, PR * 2, 'emis', up=(0, 1, 0))

    # ---- Legendary (damascus and ivory)
    r5 = Kit(pal)
    for s in (-1, 1):
        with r5.at((0, 0, bz), (0, 0 if s > 0 else 180, 0)):
            r5.ext_x([(0.588, 0.0150), (0.666, 0.0150), (0.656, 0.0240), (0.628, 0.0340), (0.598, 0.0300), (0.584, 0.0200)], -0.0020, 0.0020, 'gun3', ch=0)
            r5.ext_x([(0.600, 0.0290), (0.628, 0.0340), (0.654, 0.0245), (0.628, 0.0305)], -0.0035, 0.0035, 'trim', ch=0, hull=False)
        with r5.at((0, 0, bz), (0, 90 * s, 0)):
            r5.ext_x([(0.590, 0.0140), (0.616, 0.0140), (0.612, 0.0250), (0.596, 0.0300)], -0.0018, 0.0018, 'gun3', ch=0)
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(-0.001, 0.0125), (0.0040, 0.0125), (0.0040, 0.0100), (0.0028, 0.0100), (0.0028, 0)], 'gun3', n, (s * (HCH + PR), 0.060, 0.000), 10,
                 hull=False, bands=[None, None, 'furn', 'furn'], caps=(False, True))
        for rot in (0, 90):
            with r5.at((s * (HCH + PR + 0.0028), 0.060, 0.000), (rot, 0, 0)):
                plate(r5, [(-0.0085, 0), (0, 0.0022), (0.0085, 0), (0, -0.0022)], 0.0, 'trim', t=PR * (1 + rot / 90), ch=0, sides=(s,), sink=0.0)
        r5.box((s * (0.013 + PR / 2 - 0.0005), -0.225, 0.043), (PR + 0.001, 0.070, 0.0022), 'trim', skip=sk(s))
        plate(r5, rect(-0.276, -0.182, 0.0150, 0.0250, 0.003), 0.010, 'furn', sides=(s,))
        r5.box((s * (0.010 + PR * 1.5), -0.229, 0.020), (PR + 0.001, 0.080, 0.0020), 'trim', skip=sk(s))
        plate(r5, rect(-0.2955, -0.2835, -0.050, 0.018, 0.002), 0.0125, 'furn', sides=(s,))
        for y0 in (0.130, 0.184):
            r5.ext_x([(y0, 0.012), (y0 + 0.046, 0.012), (y0 + 0.056, 0.034), (y0 + 0.016, 0.027)], min(s * 0.0200, s * 0.0240), max(s * 0.0200, s * 0.0240), 'gun3', ch=0)
    for y in (0.200, 0.300, 0.580):
        r5.lathe([(y, 0), (y, 0.0160), (y + 0.012, 0.0160), (y + 0.012, 0)], 'gun3', 'y', (0, 0, bz), 12, hull=False)
        grooves(r5, y + 0.003, y + 0.009, 0.0160, bz, n=1, color='trim', seg=12, fill=0.7)
    for (a, b) in ((0.215, 0.297), (0.315, 0.392), (0.396, 0.478), (0.482, 0.572)):
        r5.ext_x([(a, bz + 0.008), (b, bz + 0.008), (b, bz + 0.0145), (b - 0.014, bz + 0.0215), (a + 0.030, bz + 0.0175), (a + 0.006, bz + 0.0215), (a, bz + 0.0160)],
                 -0.0030, 0.0030, 'gun3', ch=0)
    r5.lathe([(0.0135, 0.0105), (0.0185, 0.0105), (0.0185, 0)], 'furn', 'x', (0.010, -0.004, sz), 8, hull=False, caps=(False, True), bands=[None, 'trim'])
    r5.lathe([(0.0105, 0.0095), (0.0150, 0.0095), (0.0150, 0)], 'furn', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))), (-0.010, -0.010, sz), 8, hull=False,
             caps=(False, True), bands=[None, 'trim'])
    r5.lathe([(-0.002, 0), (-0.002, 0.0070), (0.005, 0.0125), (0.017, 0.0125), (0.0225, 0.0060), (0.0225, 0)], 'furn',
             (V((0.5, -0.1, -0.86)).normalized(), V((0, 1, 0)), V((0.86, 0, 0.5))), (0.042, -0.081, bz - 0.014), 8, bands=[None, None, 'trim', None, None])
    with r5.at((0, -0.196, -0.012)):
        r5.lathe([(-0.0075, 0), (-0.004, 0.0062), (0.004, 0.0062), (0.0075, 0)], 'emis', 'z', (0, 0, 0), 6, hull=False)
        r5.ring('x', (0, 0, 0), -0.0012, 0.0012, 0.0140, 0.0162, 'trim', seg=10, hull=False)
        r5.ring('z', (0, 0, 0), -0.0012, 0.0012, 0.0100, 0.0120, 'gun3', seg=10, hull=False)
        r5.bar((0, 0, 0.0150), (0, 0, 0.0230), 0.004, 0.004, 'gun3', up=(0, 1, 0))
    m5 = Kit(pal)
    for gz in (-0.020, -0.032):
        y, z = g2w(4, 0.0, gz)
        m5.cbox((0, y, z), (0.036, 0.070, 0.005), 'trim', ch=0, rot=(-4, 0, 0), hull=False)
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.050, -0.030), 'muzzle': (0, 0.674, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.165, sz), 'scope': (0, -0.150, sz), 'cls': 'sniper', 'guard': (0, 0.300, 0.000),
                   'bolt': (0.046, -0.082, bz - 0.020),
                   'layers': {'345': r3, '45': r4, '4': r4o, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}


def build_railspike(pal):
    """SR-9 Railspike: semi-auto rail rifle. Twin rails with copper bus strips in an open frame, held by five coil
    clamps (bolted saddles, tie rods, cooling fins between them); a ribbed breech insulator, capacitor banks strapped
    to both sides of the receiver, a charge ladder, a hollow emitter head, a battery magazine and a long scope on a
    one-piece mount.
    Rarity layers: Rare bolts on an aiming module, vented rail covers, a charge gauge, a magwell funnel and a spare
    cell in the stock; Epic lights a plasma column down the bore, energy cells on the stock and conduits along the
    receiver; Legendary (oil-slick chrome) fans prism wings off every clamp, raises a spine of spikes along the top
    rail, floats prisms between the rails and crowns the emitter."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    HU, HL, HM, HB = 0.026, 0.022, 0.0255, 0.022           # half widths: upper, lower, magwell, breech insulator
    ring3 = lambda p, y: [(q[0], y, q[1]) for q in p]

    def rivets(kk, hw, pts, sides=(-1, 1), r=0.0028):
        for s in sides:
            for y, z in pts:
                bolt(kk, (s * hw, y, z), (s, 0, 0), r, 0.0022, socket=False)

    # ---- receiver: data panels, charge ladder, capacitor banks under a strap, vent port, readout block
    k.ext_y(rrect(0.052, 0.060, ct=0.010, cb=0.004, cy=0.030), -0.120, 0.140, 'gunmetal', ch0=0.005, ch1=0.004)
    plate(k, rect(-0.100, 0.120, 0.0055, 0.0085), HU, 'trim', ch=0)
    plate(k, [(-0.112, 0.018), (-0.040, 0.018), (-0.032, 0.026), (-0.032, 0.048), (-0.112, 0.048)], HU, 'body2')
    stencil(k, 'SR-9', HU + PR, -0.074, 0.030, cap=0.012, sides=(-1,))
    stencil(k, 'RAIL RIFLE 40KV', HU + PR, -0.074, 0.021, cap=0.0045, sides=(-1,), font='cond')
    stencil(k, 'RAILSPIKE', HU + PR, -0.074, 0.029, cap=0.008, sides=(1,))
    rivets(k, HU + PR, [(-0.107, 0.043), (-0.037, 0.043)])
    k.box((-(HU + PR / 2 - 0.0005), -0.016, 0.031), (PR + 0.001, 0.014, 0.034), 'ink', skip=sk(-1))
    for i in range(5):
        k.box((-(HU + PR * 1.5 - 0.0005), -0.016, 0.019 + i * 0.006), (PR + 0.001, 0.010, 0.0036), 'emis', skip=sk(-1))
    k.box((HU + PR / 2 - 0.0005, -0.012, 0.040), (PR + 0.001, 0.026, 0.013), 'ink', skip=sk(1))
    k.box((HU + PR, -0.016, 0.040), (0.0036, 0.014, 0.008), 'steel', skip=sk(1))
    for s in (-1, 1):
        for i in range(4):
            k.lathe([(0.014, 0), (0.014, 0.0085), (0.045, 0.0085), (0.045, 0)], 'steel2', 'z', (s * (HU - 0.003), 0.026 + i * 0.028, 0), 6, hull=False,
                    bands=[None, None, 'brass'])
        k.box((s * (HU + 0.0035), 0.068, 0.030), (0.008, 0.112, 0.006), 'gunmetal', hull=True)
        rivets(k, HU + 0.0075, [(0.016, 0.030), (0.120, 0.030)], sides=(s,))
    hazard(k, HU, 0.014, 0.118, 0.0105, 0.0135, n=10, lean=0.8)
    k.cbox((0, -0.100, 0.0625), (0.024, 0.026, 0.009), 'body2', ch=0.002, axis='x')
    top_slots(k, 0.067, -0.110, -0.090, 3, w=0.014, fill=0.5, color='emis')
    # ---- lower: pins, selector, magwell with plate and slots, cable up to the capacitor bank
    k.ext_y(rrect(0.044, 0.024, c=0.003, cy=-0.004), -0.100, 0.130, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.060, 0.002), (0.130, 0.002), (0.132, -0.034), (0.124, -0.044), (0.060, -0.044), (0.056, -0.032)], -HM, HM, 'gun2', ch=0.003)
    plate(k, [(0.066, -0.004), (0.126, -0.004), (0.126, -0.032), (0.070, -0.032)], HM, 'frame2')
    slots(k, HM + PR, 0.076, 0.120, -0.018, 3, h=0.018, fill=0.4)
    cross_pin(k, HL, -0.088, -0.004, r=0.0030)
    rivets(k, HL, [(0.044, -0.004)], r=0.0034)
    k.lathe([(HL - 0.003, 0.0050), (HL + 0.0045, 0.0050), (HL + 0.0045, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, -0.036, -0.003), 8,
            hull=False, caps=(False, True))
    k.xbar(-HL - 0.0070, -HL - 0.0040, [(-0.054, -0.006), (-0.034, -0.0075), (-0.032, 0.0005), (-0.052, 0.002)], 'gun3', ch=0, hull=False)
    k.box((-HL - PR / 2 + 0.0005, -0.062, 0.000), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    cable(k, [(-0.0285, 0.066, -0.026), (-0.0310, 0.052, -0.010), (-0.0300, 0.036, 0.004), (-0.0300, 0.026, 0.016)], clamps=(1,))
    # ---- breech insulator, rails with copper strips, bore core, coil clamps with bolted saddles, tie rods, fins
    k.cbox((0, 0.153, bz), (HB * 2, 0.034, 0.066), 'gun2', ch=0.005, axis='y')
    slots(k, HB, 0.141, 0.165, bz, 3, h=0.046, fill=0.34)
    top_slots(k, bz + 0.033, 0.141, 0.165, 3, w=0.026, fill=0.34)
    for zz in (bz + 0.020, bz - 0.020):
        k.cbox((0, 0.392, zz), (0.020, 0.496, 0.012), 'steel2', ch=0.003, axis='y')
        plate(k, rect(0.172, 0.628, zz - 0.0025, zz + 0.0025), 0.010, 'brass', ch=0)
    for s in (-1, 1):
        k.box((0, 0.401, bz + s * (0.014 - PR / 2 + 0.0005)), (0.008, 0.454, PR + 0.001), 'trim', skip=('+z' if s > 0 else '-z',))
        k.lathe([(0.170, 0), (0.170, 0.0028), (0.634, 0.0028), (0.634, 0)], 'steel', 'y', (s * 0.0205, 0, bz + 0.0205), 6, hull=False)
    k.lathe([(0.140, 0), (0.140, 0.0060), (0.640, 0.0060), (0.640, 0)], 'ink', 'y', (0, 0, bz), 8, hull=False)
    rings = [0.180 + i * 0.090 for i in range(5)]
    for i, y in enumerate(rings):
        k.ring('y', (0, 0, bz), y, y + 0.022, 0.024, 0.034, 'gun3', seg=12)
        k.lathe([(y + 0.004, 0.0330), (y + 0.004, 0.0375), (y + 0.018, 0.0375), (y + 0.018, 0.0330)], 'lens', 'y', (0, 0, bz), 12, hull=False, caps=(False, False))
        k.cbox((0, y + 0.011, bz + 0.0360), (0.016, 0.018, 0.006), 'steel2', ch=0.0015, axis='y', hull=False)
        for s in (-1, 1):
            bolt(k, (s * 0.0042, y + 0.011, bz + 0.039), (0, 0, 1), 0.0024, 0.0020, socket=False)
        if i < 4:
            fins(k, (0, y + 0.056, bz + 0.0285), (0.016, 0.050, 0.006), 4, axis='y', color='steel2')
    # ---- hollow emitter head (you see the bore through it)
    k.loft([ring3(rrect(0.014, 0.022, c=0.003, cy=bz), 0.630), ring3(rrect(0.040, 0.064, c=0.005, cy=bz), 0.630),
            ring3(rrect(0.040, 0.064, c=0.005, cy=bz), 0.650), ring3(rrect(0.014, 0.022, c=0.003, cy=bz), 0.650)], 'gunmetal', closed=True,
           bands=[None, None, None, 'ink'])
    k.lathe([(0.640, 0), (0.640, 0.0048), (0.647, 0.0048), (0.647, 0)], 'lens', 'y', (0, 0, bz), 6, hull=False)
    rivets(k, 0.020, [(0.640, bz + 0.020), (0.640, bz - 0.020)], r=0.0030)
    stencil(k, '40KV', 0.020, 0.640, bz - 0.004, cap=0.007, font='cond', t=PR)
    # ---- scope on a one-piece mount: saddle, turrets, battery cap, bolted rings
    sz = bz + 0.066
    scope(k, -0.160, 0.170, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    k.cbox((0, -0.002, 0.0635), (0.022, 0.150, 0.009), 'gunmetal', ch=0.002, axis='y')
    rivets(k, 0.011, [(-0.030, 0.0640), (0.000, 0.0640), (0.030, 0.0640)], r=0.0024)
    for yy in (-0.064, 0.060):
        k.cbox((0, yy, 0.0760), (0.025, 0.020, 0.020), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
        for s in (-1, 1):
            bolt(k, (s * 0.0117, yy, sz + 0.0117), (s * 0.707, 0, 0.707), 0.0024, 0.0026, socket=False)
    k.cbox((0, -0.004, sz), (0.029, 0.024, 0.029), 'gunmetal', ch=0.005, axis='y')
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    k.lathe([(0.012, 0.0070), (0.024, 0.0070), (0.024, 0.0045), (0.026, 0.0045), (0.026, 0)], 'gun3', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))), (0, -0.004, sz), 8,
            hull=False, caps=(False, True), bands=[None, None, 'ink', 'ink'])
    grooves(k, 0.140, 0.166, 0.024, sz, n=2, seg=12)
    trigger_guard(k, rake, front=0.066, depth=-0.052, w=0.012, top=-0.016, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.016, ptop=-0.040)
    # ---- stock: top bar with slots, cheek rest, lower strut and brace, butt pad
    k.cbox((0, -0.205, 0.024), (0.022, 0.180, 0.022), 'gun3', ch=0.004, axis='y')
    slots(k, 0.011, -0.176, -0.124, 0.024, 3, h=0.008, fill=0.5)
    k.bar((0, -0.110, -0.022), (0, -0.290, -0.052), 0.020, 0.016, 'gun3', hull=True)
    k.bar((0, -0.262, 0.016), (0, -0.236, -0.040), 0.012, 0.010, 'gun3', hull=True, up=(0, 1, 0))
    k.cbox((0, -0.226, 0.044), (0.026, 0.090, 0.016), 'furn', ch=0.004, axis='y')
    top_slots(k, 0.052, -0.262, -0.190, 6, w=0.016, fill=0.3)
    k.cbox((0, -0.123, 0.016), (0.040, 0.008, 0.058), 'body2', ch=0.002, axis='y')
    for s in (-1, 1):
        rivets(k, 0.020, [(-0.123, -0.004), (-0.123, 0.036)], sides=(s,), r=0.0028)
        rivets(k, 0.011, [(-0.282, 0.024)], sides=(s,), r=0.0034)
    k.ext_x([(-0.290, 0.044), (-0.300, 0.044), (-0.302, -0.072), (-0.292, -0.072)], -0.018, 0.018, 'gun3', ch=0.002)
    k.ext_x([(-0.299, 0.046), (-0.312, 0.044), (-0.314, -0.074), (-0.3005, -0.074)], -0.022, 0.022, 'rubber', ch=0.003)
    for i in range(5):
        z = 0.030 - i * 0.024
        yf = -0.312 - (0.044 - z) / 0.118 * 0.002 - PR
        k.box((0, (yf - 0.3035) / 2, z), (0.044 + 2 * PR, -0.3035 - yf, 0.005), 'ink')
    # ---- battery magazine: cell windows, ribs, hazard band, stencil
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.036), (0.030, 0.056, 0.072), 'gun2', ch=0.004, axis='x')
    for i in range(3):
        mk.box((0, 0.0, -0.020 - i * 0.012), (0.030 + 2 * PR, 0.028, 0.008), 'lens')
    mk.cbox((0, 0.0, -0.076), (0.036, 0.062, 0.010), 'gun3', ch=0.003, axis='z')
    for s in (-1, 1):
        for y in (-0.020, 0.020):
            mk.box((s * (0.015 + PR / 2 - 0.0005), y, -0.034), (PR + 0.001, 0.005, 0.050), 'frame2', skip=sk(s))
        mk.box((0, s * (0.028 + PR / 2 - 0.0005), -0.034), (0.018, PR + 0.001, 0.044), 'frame2', skip=('-y' if s > 0 else '+y',))
    hazard(mk, 0.015, -0.016, 0.012, -0.066, -0.060, n=4)
    stencil(mk, 'CELL', 0.015, 0.0, -0.057, cap=0.0065, font='cond')

    # ---- Rare (and up)
    r3 = Kit(pal)
    laser_box(r3, 0.150, bz + 0.012, s=1, hw=HB, L=0.040, w=0.016, h=0.022, color='gun2')
    cable(r3, [(0.0290, 0.132, bz + 0.012), (0.0300, 0.124, bz + 0.016), (0.0300, 0.110, bz + 0.016)], clamps=(1,))
    for y in (rings[2], rings[3]):
        r3.cbox((0, y + 0.056, bz + 0.0345), (0.026, 0.062, 0.003), 'gun3', ch=0.001, axis='y', hull=True)
        top_slots(r3, bz + 0.036, y + 0.030, y + 0.082, 4, w=0.016, fill=0.45)
    r3.cbox((-0.016, -0.034, 0.0660), (0.010, 0.040, 0.012), 'gun2', ch=0.002, hull=True)
    for i in range(4):
        r3.box((-0.021 - PR / 2 + 0.0005, -0.046 + i * 0.008, 0.0660), (PR + 0.001, 0.005, 0.006), 'emis', skip=sk(-1))
    top_slots(r3, 0.072, -0.050, -0.018, 4, w=0.005, fill=0.6, color='emis', x=-0.016)
    r3.ext_x([(0.052, -0.040), (0.136, -0.040), (0.140, -0.056), (0.048, -0.056)], -0.0290, 0.0290, 'gun3', ch=0.003)
    rivets(r3, 0.0290, [(0.058, -0.048), (0.130, -0.048)])
    r3.cbox((0, -0.186, 0.003), (0.020, 0.050, 0.024), 'gun2', ch=0.003, axis='x')
    for i in range(2):
        r3.box((0, -0.196 + i * 0.020, 0.001), (0.020 + 2 * PR, 0.012, 0.012), 'lens')
    r3.box((0, -0.186, 0.004), (0.026, 0.006, 0.030), 'rubber')

    # ---- Epic (and up)
    r4 = Kit(pal)
    r4.lathe([(0.172, 0), (0.172, 0.0085), (0.644, 0.0085), (0.644, 0)], 'emis', 'y', (0, 0, bz), 6, hull=False, a0=0)
    for s in (-1, 1):
        energy_cell(r4, (s * 0.0195, -0.152, 0.024), L=0.050, r=0.0075, cage_bars=3)
        conduit(r4, [(s * 0.0195, -0.126, 0.024), (s * 0.0240, -0.118, 0.018), (s * 0.0290, -0.108, 0.0125), (s * 0.0290, 0.006, 0.0125),
                     (s * 0.0290, 0.012, 0.020)], r=0.0026, every=2)
    for y in rings:
        r4.box((0, y + 0.011, bz + 0.039 + PR / 2 - 0.0005), (0.004, 0.012, PR + 0.001), 'emis', skip=('-z',))
    m4 = Kit(pal)
    for s in (-1, 1):
        m4.box((0, s * (0.028 + PR * 1.5 - 0.0005), -0.034), (0.006, PR + 0.001, 0.036), 'emis', skip=('-y' if s > 0 else '+y',))

    # ---- Legendary (oil-slick chrome)
    r5 = Kit(pal)
    for i, y in enumerate(rings):
        for s in (-1, 1):
            with r5.at((0, 0, bz), (0, -90 + s * 58, 0)):
                r5.ext([(y + 0.002, 0.0320), (y + 0.020, 0.0320), (y + 0.016, 0.0480), (y - 0.004, 0.0640), (y - 0.022, 0.0720), (y - 0.006, 0.0520)], 'steel',
                       (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0016, 0.0016)
                r5.ext([(y + 0.008, 0.0400), (y - 0.004, 0.0560), (y - 0.018, 0.0685), (y - 0.002, 0.0500)], 'trim', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                       -0.0031, 0.0031, hull=False)
        if i < 4:
            g0 = y + 0.022
            r5.ext_x([(g0 + 0.006, bz + 0.029), (g0 + 0.060, bz + 0.029), (g0 + 0.064, bz + 0.040), (g0 + 0.022, bz + 0.0345)], -0.0022, 0.0022, 'steel', ch=0)
            r5.ext_x([(g0 + 0.026, bz + 0.0350), (g0 + 0.062, bz + 0.0395), (g0 + 0.064, bz + 0.0400), (g0 + 0.060, bz + 0.0372)], -0.0037, 0.0037, 'trim', ch=0, hull=False)
        if i < 4:
            with r5.at((0, y + 0.056, bz)):
                r5.lathe([(-0.024, 0), (-0.008, 0.0115), (0.008, 0.0115), (0.024, 0)], 'emis', 'y', (0, 0, 0), 6, hull=False)
                r5.lathe([(-0.0012, 0.0110), (-0.0012, 0.0136), (0.0012, 0.0136), (0.0012, 0.0110)], 'trim', 'y', (0, 0, 0), 8, hull=False, caps=(False, False), a0=0)
    for sx in (-1, 1):
        for s in (-1, 1):
            r5.lathe([(0.634, 0.0042), (0.646, 0.0042), (0.6555, 0)], 'steel', 'y', (sx * 0.0135, 0, bz + s * 0.0275), 6, caps=(False, True))
        r5.box((sx * (0.011 + PR / 2 - 0.0005), -0.236, 0.0180), (PR + 0.001, 0.090, 0.0024), 'trim', skip=sk(sx))
        r5.ext_x([(0.126, 0.037), (0.126, 0.051), (0.030, 0.054), (0.002, 0.044), (0.034, 0.041)], min(sx * (HU + 0.0090), sx * (HU + 0.0112)),
                 max(sx * (HU + 0.0090), sx * (HU + 0.0112)), 'steel', ch=0)
        r5.ext_x([(0.122, 0.0465), (0.034, 0.0490), (0.008, 0.0440), (0.034, 0.0465)], min(sx * (HU + 0.0104), sx * (HU + 0.0127)),
                 max(sx * (HU + 0.0104), sx * (HU + 0.0127)), 'trim', ch=0, hull=False)
    r5.ext_x([(-0.292, -0.066), (-0.312, -0.072), (-0.320, -0.096), (-0.302, -0.080)], -0.0030, 0.0030, 'steel', ch=0)
    m5 = Kit(pal)
    for z in (-0.008, -0.052):
        m5.box((0, 0, z), (0.036, 0.068, 0.003), 'trim')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.096, -0.044), 'muzzle': (0, 0.656, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.175, sz), 'scope': (0, -0.160, sz), 'cls': 'sniper', 'guard': (0, 0.300, bz - 0.020),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}
