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
    grooves(k, 0.216, 0.264, 0.0085, hz, n=3, seg=8)
    # ---- gas system, forend, bipod on its yoke
    k.lathe([(0.156, 0), (0.156, 0.008), (0.384, 0.008), (0.384, 0)], 'steel2', 'y', (0, 0, 0.012), 8, hull=True)
    k.ext_y(octa(0.030, 0.056, 0.008, 0.0, 0.029), 0.380, 0.402, 'steel2', ch0=0.002, ch1=0.002)
    k.lathe([(0.400, 0), (0.400, 0.0095), (0.412, 0.0095), (0.412, 0.0065), (0.420, 0.0065), (0.420, 0)], 'steel', 'y', (0, 0, 0.012), 8, hull=False)
    grooves(k, 0.403, 0.410, 0.0095, 0.012, n=1, seg=8, fill=0.6)
    k.ext_y(rrect(0.046, 0.034, ct=0.006, cb=0.010, cy=0.012), 0.152, 0.300, 'gun2', ch1=0.006)
    for s in (-1, 1):
        for z in (0.009, 0.014, 0.019):
            k.box((s * (HF + PR / 2 - 0.0005), 0.228, z), (PR + 0.001, 0.108, 0.0022), 'ink', skip=sk(s))
        rivets(k, HF, [(0.162, 0.014), (0.288, 0.014)], sides=(s,), r=0.0030)
        k.cbox((s * 0.016, 0.3835, 0.008), (0.009, 0.091, 0.009), 'steel2', ch=0.002, axis='y')
        k.cbox((s * 0.016, 0.322, 0.008), (0.006, 0.040, 0.006), 'steel', ch=0.0015, axis='y', hull=False)
        k.box((s * 0.016, 0.302, 0.006), (0.011, 0.014, 0.013), 'rubber', hull=True)
        k.box((s * 0.016, 0.350, 0.008), (0.012, 0.006, 0.012), 'steel')
        rivets(k, 0.023, [(0.428, 0.012)], sides=(s,), r=0.0034)
    k.ring('y', (0, 0, bz), 0.420, 0.434, 0.0100, 0.0160, 'steel2', seg=10, hull=False)
    k.cbox((0, 0.428, 0.018), (0.046, 0.010, 0.022), 'steel2', ch=0.003, axis='y')
    # ---- front sight tower, flash hider
    k.ring('y', (0, 0, bz), 0.442, 0.456, 0.0100, 0.0150, 'gunmetal', seg=8, hull=False)
    k.ext_x([(0.4435, bz + 0.012), (0.4545, bz + 0.012), (0.4525, 0.100), (0.4455, 0.100)], -0.0045, 0.0045, 'gunmetal', ch=0.001)
    k.box((0, 0.449, 0.1045), (0.0030, 0.004, 0.013), 'ink')
    for s in (-1, 1):
        k.ext_x([(0.443, 0.096), (0.455, 0.096), (0.453, 0.113), (0.445, 0.113)], min(s * 0.0045, s * 0.0075), max(s * 0.0045, s * 0.0075), 'gunmetal', ch=0.0006, hull=False)
    k.ring('y', (0, 0, bz), 0.4575, 0.4655, 0.0100, 0.0150, 'steel2', seg=8, hull=False)
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
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.010), 'muzzle': (0, 0.514, bz), 'eject': (0.03, 0.020, 0.048),
                   'sight': (0, -0.095, 0.110), 'cls': 'rifle', 'guard': (0, 0.292, 0.012)}


def build_needle(pal):
    """SR-160 Needle: bolt-action sniper, chassis stock, long scope with turrets and lens rings, big brake."""
    rake = 22
    k = Kit(pal)
    bz = 0.032
    k.lathe([(-0.112, 0), (-0.112, 0.016), (-0.106, 0.020), (0.100, 0.020), (0.106, 0.016), (0.106, 0)], 'gunmetal', 'y', (0, 0, bz), 12, a0=0)   # action
    k.box((0.0175, 0.010, bz + 0.006), (0.010, 0.050, 0.014), 'ink')                       # port
    # bolt handle + knob (right side, rear)
    k.tube([((0.016, -0.074, bz + 0.004), 0.008, 0.008), ((0.034, -0.078, bz - 0.006), 0.007, 0.007), ((0.046, -0.082, bz - 0.020), 0.007, 0.007)], 'steel', sides=6, up=(0, 1, 0))
    k.lathe([(0.0, 0), (0.0, 0.006), (0.006, 0.010), (0.016, 0.010), (0.020, 0.005), (0.020, 0)], 'steel2', (V((0.5, -0.1, -0.86)).normalized(), V((0, 1, 0)), V((0.86, 0, 0.5))), (0.042, -0.081, bz - 0.014), 8)
    k.cbox((0, -0.120, bz), (0.026, 0.016, 0.026), 'gun3', ch=0.004, axis='y', hull=False)   # bolt shroud
    # chassis (lighter), forend with slots, amber stripe, folded bipod
    k.ext_x([(-0.100, 0.020), (0.320, 0.020), (0.330, 0.010), (0.330, -0.016), (0.120, -0.024), (0.080, -0.030), (-0.100, -0.030)], -0.0225, 0.0225, 'gun3', ch=0.004)
    for s in (-1, 1):
        for i in range(5):
            k.box((s * 0.0225, 0.150 + i * 0.034, 0.004), (0.006, 0.022, 0.012), 'ink', skip=('-x' if s > 0 else '+x',))
        k.screw((s * 0.0225, 0.060, 0.008), (s, 0, 0))
    k.box((0, 0.230, -0.010), (0.0510, 0.180, 0.005), 'trim')
    bipod_folded(k, 0.200, 0.320, -0.026, x=0.012)
    rail(k, -0.104, 0.098, bz + 0.0195, w=0.020, pitch=0.014, clear=[(-0.074, -0.054), (0.044, 0.064)])
    # barrel (taper) and two-chamber brake
    k.lathe([(0.100, 0), (0.100, 0.0110), (0.600, 0.0090), (0.600, 0)], 'steel', 'y', (0, 0, bz), 10)
    k.cbox((0, 0.634, bz), (0.034, 0.068, 0.026), 'steel2', ch=0.005, axis='y')
    for i in range(2):
        k.box((0, 0.616 + i * 0.030, bz), (0.040, 0.016, 0.016), 'ink')
    muzzle(k, 0.664, 0.672, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # scope with mounts, turrets, parallax knob
    sz = bz + 0.062
    scope(k, -0.150, 0.180, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    for yy in (-0.064, 0.054):
        k.cbox((0, yy, bz + 0.033), (0.024, 0.016, 0.022), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    turret(k, (-0.010, -0.010, sz), '-x', r=0.008, h=0.009, cap='gun3')
    trigger_guard(k, rake, front=0.068, depth=-0.054, w=0.012, top=-0.024, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.022, ptop=-0.040)
    # skeleton chassis stock: top bar with cheek riser, lower strut, butt pad, monopod
    k.cbox((0, -0.2045, 0.020), (0.020, 0.191, 0.020), 'gun3', ch=0.004, axis='y')
    k.cbox((0, -0.225, 0.040), (0.026, 0.090, 0.016), 'furn', ch=0.004, axis='y')
    k.bar((0, -0.100, -0.024), (0, -0.290, -0.056), 0.020, 0.016, 'gun3', hull=True)
    k.ext_x([(-0.296, 0.040), (-0.318, 0.040), (-0.320, -0.074), (-0.298, -0.074)], -0.0215, 0.0215, 'ink', ch=0.003)
    k.lathe([(-0.060, 0), (-0.060, 0.007), (0.0, 0.007), (0.0, 0)], 'steel2', 'z', (0, -0.262, -0.050), 8, hull=False)
    mk = Kit(pal)
    mag_box(mk, 4, 0.034, -0.040, 0.060, 0.026, plate='gun2', ribs=True, wt=0.62)
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.050, -0.030), 'muzzle': (0, 0.674, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.165, sz), 'scope': (0, -0.150, sz), 'cls': 'sniper', 'guard': (0, 0.300, 0.000),
                   'bolt': (0.046, -0.082, bz - 0.020)}


def build_railspike(pal):
    """SR-9 Railspike: semi-auto rail rifle. Twin copper rails in an open frame, glowing coil rings, a battery
    magazine, long scope."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    k.ext_y(rrect(0.052, 0.060, ct=0.010, cb=0.004, cy=0.030), -0.120, 0.140, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.ext_y(rrect(0.044, 0.024, c=0.003, cy=-0.004), -0.100, 0.130, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.060, 0.002), (0.130, 0.002), (0.132, -0.034), (0.124, -0.044), (0.060, -0.044), (0.056, -0.032)], -0.0255, 0.0255, 'gun2', ch=0.003)
    # open rail frame: two rails (top / bottom) with coil rings between, an ink core
    for zz in (bz + 0.020, bz - 0.020):
        k.cbox((0, 0.392, zz), (0.020, 0.496, 0.012), 'trim', ch=0.003, axis='y')
    k.lathe([(0.140, 0), (0.140, 0.0060), (0.640, 0.0060), (0.640, 0)], 'ink', 'y', (0, 0, bz), 8, hull=False)
    for i in range(5):
        y = 0.180 + i * 0.090
        k.ring('y', (0, 0, bz), y, y + 0.022, 0.024, 0.034, 'gun3', seg=12)
        k.ring('y', (0, 0, bz), y + 0.004, y + 0.018, 0.0335, 0.0375, 'lens', seg=12, hull=False)
    k.cbox((0, 0.640, bz), (0.040, 0.020, 0.064), 'gunmetal', ch=0.005, axis='y')                         # muzzle block
    k.box((0, 0.6515, bz), (0.012, 0.006, 0.012), 'lens')
    stripe(k, -0.100, 0.120, 0.010, 0.016, 0.0290)
    for s in (-1, 1):
        k.screw((s * 0.026, -0.090, 0.050), (s, 0, 0))
    sz = bz + 0.066
    scope(k, -0.160, 0.170, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    for yy in (-0.064, 0.060):
        k.cbox((0, yy, bz + 0.0375), (0.024, 0.016, 0.022), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    trigger_guard(k, rake, front=0.066, depth=-0.052, w=0.012, top=-0.016, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.016, ptop=-0.040)
    k.cbox((0, -0.205, 0.024), (0.022, 0.180, 0.022), 'gun3', ch=0.004, axis='y')
    k.bar((0, -0.110, -0.022), (0, -0.290, -0.052), 0.020, 0.016, 'gun3', hull=True)
    k.ext_x([(-0.290, 0.044), (-0.312, 0.044), (-0.314, -0.072), (-0.292, -0.072)], -0.022, 0.022, 'ink', ch=0.003)
    k.cbox((0, -0.226, 0.044), (0.026, 0.090, 0.016), 'furn', ch=0.004, axis='y')
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.036), (0.030, 0.056, 0.072), 'gun2', ch=0.004, axis='x')                            # battery pack
    mk.box((0, 0.0, -0.036), (0.037, 0.030, 0.040), 'lens')
    mk.cbox((0, 0.0, -0.076), (0.036, 0.062, 0.010), 'gun3', ch=0.003, axis='z')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.096, -0.044), 'muzzle': (0, 0.656, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.175, sz), 'scope': (0, -0.160, sz), 'cls': 'sniper', 'guard': (0, 0.300, bz - 0.020)}
