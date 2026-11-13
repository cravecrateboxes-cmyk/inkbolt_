"""INKBOLT guns: shotguns. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def heat_shield(k, y0, y1, cz, w, h, c, n=8, color='gun3', th=0.0025, edge=0.27, rib=0.007, end=0.012, skirt=0.004, open=(1, 2, 3)):
    """Ventilated heat shield over the top half of a barrel at height cz: a half-octagon sheet (two short skirts,
    the two upper diagonals and the top) built from thin strips with open slots between raised ribs, so the barrel
    shows through. `open`: which of the five faces (0 right skirt .. 4 left skirt) get slots. Returns the ribs' y spans."""
    def half(w_, h_, c_, sk_):
        a_, b_ = w_ / 2, h_ / 2
        return [V((a_, cz - sk_)), V((a_, cz + b_ - c_)), V((a_ - c_, cz + b_)), V((-a_ + c_, cz + b_)), V((-a_, cz + b_ - c_)), V((-a_, cz - sk_))]
    O, I = half(w, h, c, skirt), half(w - 2 * th, h - 2 * th, c - th * 0.42, skirt)
    for i in range(5):
        p0, p1, q0, q1 = O[i], O[i + 1], I[i], I[i + 1]
        if i in open:
            for (s, e) in ((0.0, edge), (1.0 - edge, 1.0)):
                k.ext_y([tuple(p0.lerp(p1, s)), tuple(p0.lerp(p1, e)), tuple(q0.lerp(q1, e)), tuple(q0.lerp(q1, s))], y0 + 0.003, y1 - 0.003, color)
        else:
            k.ext_y([tuple(p0), tuple(p1), tuple(q1), tuple(q0)], y0 + 0.003, y1 - 0.003, color)
    Or, Ir = half(w + 2 * PR, h + 2 * PR, c + PR * 0.42, skirt + 0.002), half(w - 2 * th - 0.003, h - 2 * th - 0.003, c - th * 0.42, skirt + 0.002)
    span = (y1 - y0 - 2 * end) / n
    ys = [(y0, y0 + end)] + [(y0 + end + span * i - rib / 2, y0 + end + span * i + rib / 2) for i in range(1, n)] + [(y1 - end, y1)]
    for (ya, yb) in ys:
        k.ext_y([tuple(p) for p in Or] + [tuple(p) for p in reversed(Ir)], ya, yb, color)
    return ys


def shell(k, c, z0, L=0.048, r=0.0080, axis='z'):
    """12-gauge shell standing at c (base at z0 along axis): brass head with its rim, red hull, crimped mouth."""
    k.lathe([(z0, 0), (z0, r + 0.0010), (z0 + 0.0025, r + 0.0010), (z0 + 0.0025, r), (z0 + 0.011, r), (z0 + L - 0.003, r), (z0 + L, r - 0.002), (z0 + L, 0)],
            'brass', axis, c, 8, hull=False, bands=[None, None, None, None, 'red', 'red', 'red'])


def build_scrapper(pal):
    """SG-9 Scrapper: pump shotgun. Steel receiver with a five-shell side saddle on the left, ejection port with the
    bolt, ghost-ring rear sight and a ramped bead, loading port and lifter underneath, ventilated heat shield over the
    barrel (the barrel shows through the slots), tube magazine with its cap, barrel clamp with sling sockets, walnut
    stock with a ribbed recoil pad and a sling stud. The walnut pump forend is the 'Mag' part: it slides on the tube
    with its twin action bars when the gun is worked.
    Rarity layers: Rare adds shell loops on the stock, a weapon light on the shield, a breacher collar, a shell
    counter and toe armour; Epic winds glowing coils round the barrel under the shield, fed from a cell on the stock,
    fins the muzzle and lights the pump; Legendary (Oni crimson) raises a dorsal row of spines on the shield, fangs
    round the muzzle, a browed eye on each side of the receiver and flame inlays in the walnut."""
    rake = 20
    k = Kit(pal)
    bz = 0.040
    BZ, TZ = bz + 0.004, bz - 0.024            # barrel axis, magazine-tube axis
    HR, HS = 0.023, 0.021                      # half widths: receiver, stock
    # ---- receiver
    k.ext_y(rrect(0.046, 0.058, ct=0.010, cb=0.004, cy=0.036), -0.110, 0.120, 'gunmetal', ch0=0.005, ch1=0.004)
    # right: ejection port with the bolt and extractor, name plate, accent line
    k.box((HR + PR / 2 - 0.0005, 0.020, 0.044), (PR + 0.001, 0.070, 0.022), 'ink', skip=sk(1))
    k.box((HR + PR, 0.030, 0.0445), (0.0036, 0.044, 0.015), 'steel', skip=sk(1))
    k.box((HR + PR + 0.0022, 0.047, 0.0445), (0.0036, 0.005, 0.009), 'steel2', skip=sk(1))
    plate(k, [(-0.104, 0.021), (-0.030, 0.021), (-0.022, 0.029), (-0.022, 0.050), (-0.104, 0.050)], HR, 'body2', sides=(1,))
    stencil(k, 'SG-9', HR + PR, -0.064, 0.0340, cap=0.011, sides=(1,))
    stencil(k, 'IB ARMS  12 GA', HR + PR, -0.064, 0.0255, cap=0.0045, sides=(1,), font='cond')
    plate(k, rect(-0.016, 0.112, 0.0225, 0.0255), HR, 'trim', ch=0, sides=(1,))
    stencil(k, 'SCRAPPER', HR, 0.074, 0.0385, cap=0.0075, sides=(1,))
    # left: side saddle (backing plate, carrier block, five shells), accent line
    plate(k, rect(-0.070, 0.070, 0.022, 0.052, c=0.003), HR, 'steel2', t=0.003, sides=(-1,), hull=True)
    bolts(k, HR + 0.003, [(-0.065, 0.047), (0.065, 0.047), (-0.065, 0.027), (0.065, 0.027)], r=0.0026, sides=(-1,))
    k.cbox((-HR - 0.0115, 0.0, 0.037), (0.019, 0.116, 0.015), 'frame2', ch=0.002)
    for i in range(5):
        shell(k, (-HR - 0.0115, -0.044 + i * 0.022, 0), 0.013)
    plate(k, rect(-0.050, 0.080, 0.0145, 0.0175), HR, 'trim', ch=0, sides=(-1,))
    cross_pin(k, HR, -0.060, 0.0135)
    cross_pin(k, HR, 0.090, 0.0135)
    # top: sight base, ghost-ring rear sight, tang safety, scope-base screws
    rail(k, -0.094, -0.050, 0.065, w=0.022, pitch=0.010, clear=[(-0.078, -0.062)])
    sz = iron_rear(k, -0.070, 0.066, w=0.026, h=0.010)
    k.cbox((0, -0.1005, 0.0660), (0.010, 0.009, 0.004), 'steel2', ch=0.001, hull=False)
    for y in (-0.030, 0.006, 0.042, 0.078):
        bolt(k, (0, y, 0.065), (0, 0, 1), 0.0028)
    # underneath: loading port, lifter, follower; trigger plate with the cross-bolt safety
    k.box((0.0, 0.052, 0.0045), (0.024, 0.080, 0.006), 'ink')
    k.box((0, 0.052, -0.0005), (0.016, 0.056, 0.006), 'steel2')
    k.box((0, 0.085, 0.0005), (0.012, 0.009, 0.006), 'red')
    k.ext_y(rrect(0.040, 0.020, c=0.003, cy=-0.004), -0.080, 0.002, 'gunmetal', ch0=0.004, ch1=0.004)
    k.pin(-0.0235, 0.0235, -0.064, -0.004, 0.0040, color='steel2')
    k.box((-0.020 - PR / 2 + 0.0005, -0.054, -0.004), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    # ---- barrel, magazine tube with its cap, ventilated heat shield, clamp with sling sockets, ramped bead
    barrel(k, 0.118, 0.560, 0.0125, BZ, seg=12)
    k.lathe([(0.118, 0), (0.118, 0.0100), (0.500, 0.0100), (0.500, 0)], 'steel2', 'y', (0, 0, TZ), 10)
    k.ring('y', (0, 0, BZ), 0.116, 0.134, 0.0125, 0.0165, 'steel2', seg=12, hull=False)
    ys = heat_shield(k, 0.142, 0.440, BZ, 0.037, 0.037, 0.011, n=8, color='gun3')
    for s in (-1, 1):
        bolt(k, (s * 0.020, 0.148, BZ + 0.002), (s, 0, 0), 0.0026)
        bolt(k, (s * 0.020, 0.434, BZ + 0.002), (s, 0, 0), 0.0026)
    k.cbox((0, 0.506, bz - 0.012), (0.034, 0.016, 0.048), 'gunmetal', ch=0.004, axis='y')
    bolts(k, 0.017, [(0.506, 0.034)], r=0.0030)
    for s in (-1, 1):
        sling_loop(k, 0.506, 0.016, s, hw=0.017, r=0.0055)
    k.lathe([(0.502, 0), (0.502, 0.0118), (0.522, 0.0118), (0.527, 0.0085), (0.527, 0)], 'steel', 'y', (0, 0, TZ), 10)
    knurl(k, 0.5155, 0.5215, 0.0118, TZ, n=2, seg=10)
    muzzle(k, 0.556, 0.574, 0.0162, BZ, rb=0.0095, seg=12)
    k.ext_x([(0.522, 0.054), (0.552, 0.054), (0.550, 0.066), (0.541, 0.0815), (0.534, 0.0815)], -0.0035, 0.0035, 'gunmetal', ch=0.001)
    k.cbox((0, 0.5345, 0.0775), (0.0045, 0.004, 0.0045), 'red', ch=0.001, hull=False)
    trigger_guard(k, rake, front=0.066, depth=-0.048, w=0.012, top=-0.010, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=-0.006, ptop=-0.036, grooves=2)
    # ---- walnut stock: ferrule, chequered wrist, stock bolt, accent line, sling stud, spacer and ribbed recoil pad
    k.cbox((0, -0.111, 0.036), (0.045, 0.008, 0.056), 'steel2', ch=0.002, axis='y')
    k.ext_x([(-0.103, 0.062), (-0.326, 0.050), (-0.328, -0.050), (-0.300, -0.056), (-0.160, -0.004), (-0.103, 0.010)], -HS, HS, 'furn', ch=0.005)
    slots(k, HS, -0.152, -0.120, 0.031, 5, h=0.022, fill=0.24, slant=30)
    cross_pin(k, HS, -0.262, 0.006, r=0.0055)
    plate(k, [(-0.170, 0.0020), (-0.292, -0.0435), (-0.292, -0.0405), (-0.170, 0.0050)], HS, 'trim', ch=0)
    for s in (-1, 1):
        sling_loop(k, -0.300, 0.026, s, hw=HS, r=0.0060)
    k.lathe([(-0.053, 0), (-0.053, 0.0028), (-0.040, 0.0028), (-0.040, 0)], 'steel', 'z', (0, -0.262, 0), 6, hull=False)
    k.ring('x', (0, -0.262, -0.0555), -0.0012, 0.0012, 0.0034, 0.0058, 'steel', seg=8, hull=False)
    k.ext_x(rect(-0.3335, -0.3235, -0.0545, 0.0530), -0.0230, 0.0230, 'frame2', ch=0.0015)
    k.ext_x([(-0.331, 0.056), (-0.348, 0.056), (-0.350, -0.056), (-0.333, -0.060)], -0.0250, 0.0250, 'rubber', ch=0.003)
    for i in range(5):
        z = 0.040 - i * 0.020
        for s in (-1, 1):
            k.box((s * (0.0250 + PR / 2 - 0.0005), -0.3405, z), (PR + 0.001, 0.009, 0.006), 'ink', skip=sk(s))
        k.box((0, -0.3495 - PR / 2, z), (0.034, PR + 0.002, 0.005), 'ink', skip=('+y',))
    # ---- the pump (Mag part): walnut forend round the tube, origin = its rear end on the tube axis; steel collars
    #      and the twin action bars that run back into the receiver
    mk = Kit(pal)
    mk.ext_y(rrect(0.046, 0.038, c=0.010, cy=0.001), 0.0, 0.130, 'furn', ch0=0.006, ch1=0.006)
    slots(mk, 0.023, 0.016, 0.114, 0.0025, 8, h=0.011, fill=0.3, slant=-20)
    for i in range(6):
        mk.box((0, 0.020 + i * 0.018, -0.018 - PR / 2 + 0.0005), (0.022, 0.007, PR + 0.001), 'ink', skip=('+z',))
    for y in (0.0, 0.130):
        mk.cbox((0, y, 0.0), (0.040, 0.008, 0.030), 'steel2', ch=0.003, axis='y')
    for s in (-1, 1):
        mk.box((s * 0.0125, -0.091, 0.004), (0.003, 0.186, 0.007), 'steel', hull=True)

    # ---- Rare (and up): shell loops on the stock, weapon light on the shield, breacher collar, shell counter, toe armour
    r3 = Kit(pal)
    r3.cbox((HS + 0.0050, -0.232, 0.014), (0.011, 0.074, 0.014), 'rubber', ch=0.002)
    for i in range(4):
        shell(r3, (HS + 0.0095, -0.259 + i * 0.018, 0), -0.012, L=0.046, r=0.0076)
    r3.cbox((0.0215, 0.412, 0.050), (0.008, 0.019, 0.014), 'steel2', ch=0.002)
    r3.lathe([(0.384, 0), (0.384, 0.0075), (0.418, 0.0075), (0.422, 0.0100), (0.438, 0.0100), (0.438, 0.0080), (0.434, 0.0080), (0.434, 0)], 'gun2', 'y',
             (0.0295, 0, 0.050), 8, bands=[None, None, None, None, None, 'emis', 'emis'])
    r3.ring('y', (0.0295, 0, 0.050), 0.3825, 0.3890, 0.0055, 0.0092, 'steel2', seg=8, hull=False)
    r3.ring('y', (0, 0, BZ), 0.5580, 0.5725, 0.0140, 0.0210, 'gun3', seg=12)
    for i in range(6):
        a = D(60 * i + 30)
        bolt(r3, (0.0210 * math.cos(a) * math.cos(math.pi / 12), 0.5652, BZ + 0.0210 * math.sin(a) * math.cos(math.pi / 12)), (math.cos(a), 0, math.sin(a)), 0.0026)
    r3.cbox((-HR - 0.0040, -0.089, 0.038), (0.010, 0.026, 0.022), 'gun2', ch=0.002)
    for i in range(3):
        r3.box((-HR - 0.0090 - PR / 2 + 0.0005, -0.089, 0.0315 + i * 0.0065), (PR + 0.001, 0.016, 0.004), 'emis', skip=sk(-1))
    plate(r3, [(-0.320, -0.046), (-0.292, -0.050), (-0.262, -0.036), (-0.262, -0.022), (-0.320, -0.022)], HS + PR, 'gun3', t=0.003, hull=True)
    bolts(r3, HS + PR + 0.003, [(-0.312, -0.030), (-0.312, -0.042), (-0.270, -0.030)])

    # ---- Epic (and up): coils round the barrel under the shield, cell on the stock with its conduit, muzzle fins
    r4 = Kit(pal)
    r4.lathe([(0.148, 0), (0.148, 0.0024), (0.434, 0.0024), (0.434, 0)], 'emis', 'y', (0, 0, BZ + 0.0132), 6, hull=False)
    for (a, b) in list(zip(ys[:-1], ys[1:]))[::2]:
        ym = (a[1] + b[0]) / 2
        r4.ring('y', (0, 0, BZ), ym - 0.0045, ym + 0.0045, 0.0125, 0.0150, 'emis', seg=8, hull=False)
    r4.cbox((HS + 0.0030, -0.158, 0.034), (0.008, 0.044, 0.020), 'gun2', ch=0.002)
    energy_cell(r4, (HS + 0.0125, -0.158, 0.034), L=0.058, r=0.0068, cage_bars=3)
    conduit(r4, [(HS + 0.0100, -0.128, 0.036), (0.0265, -0.116, 0.050), (0.0201, -0.100, 0.0621), (0.0201, 0.108, 0.0621), (0.0165, 0.128, 0.0605), (0.0120, 0.146, 0.0590)],
            r=0.0026, every=1)
    fins(r4, (0, 0.537, BZ), (0.040, 0.026, 0.040), 3, axis='y', color='gun2', hull=True)
    m4 = Kit(pal)
    for s in (-1, 1):
        m4.box((s * (0.023 + PR / 2 - 0.0005), 0.065, -0.0060), (PR + 0.001, 0.100, 0.002), 'emis', skip=sk(s))

    # ---- Legendary: dorsal spines on the shield, fangs round the muzzle, browed eyes on the receiver, flame inlays
    r5 = Kit(pal)
    for i, (a, b) in enumerate(ys[1:-1]):
        hgt = 0.0125 if i % 2 == 0 else 0.0095
        with r5.at((0, (a + b) / 2, BZ + 0.0195)):
            r5.ext_x([(0.008, -0.002), (0.003, 0.0045), (-0.016, hgt), (-0.007, -0.002)], -0.0017, 0.0017, 'gun3', ch=0.0008)
            r5.ext_x([(0.0005, 0.0040), (-0.0115, hgt - 0.0030), (-0.006, 0.0025)], -0.0030, 0.0030, 'trim', ch=0, hull=False)
    for ang in (38, -38, 104, -104):
        with r5.at((0, 0, BZ), (0, ang, 0)):
            r5.ext_x([(0.518, 0.010), (0.540, 0.010), (0.556, 0.0185), (0.5735, 0.0200), (0.563, 0.0290), (0.542, 0.0330), (0.522, 0.0260)], -0.0018, 0.0018, 'steel', ch=0.0012)
            r5.ext_x([(0.528, 0.0240), (0.543, 0.0295), (0.562, 0.0260), (0.5705, 0.0212), (0.558, 0.0222), (0.542, 0.0240)], -0.0032, 0.0032, 'trim', ch=0, hull=False)
    plate(r5, [(0.074, 0.047), (0.114, 0.0390), (0.114, 0.0450), (0.080, 0.0550)], HR, 'gun3', t=0.003, hull=True)
    plate(r5, [(0.080, 0.0365), (0.110, 0.0305), (0.110, 0.0350), (0.084, 0.0425)], HR, 'emis', ch=0)
    plate(r5, [(0.094, 0.0325), (0.098, 0.0315), (0.098, 0.0385), (0.094, 0.0400)], HR + PR, 'ink', ch=0)
    plate(r5, [(-0.190, 0.040), (-0.240, 0.022), (-0.306, 0.034), (-0.250, 0.029), (-0.212, 0.038)], HS, 'trim', ch=0)
    plate(r5, [(-0.176, 0.018), (-0.226, 0.000), (-0.250, -0.012), (-0.232, 0.008), (-0.196, 0.022)], HS, 'trim', ch=0)
    m5 = Kit(pal)
    for (y0, y1) in ((0.0060, 0.0098), (0.1202, 0.1240)):
        m5.ext_y(rrect(0.0495, 0.0415, c=0.0107, cy=0.001), y0, y1, 'trim', hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.300, bz - 0.024), 'muzzle': (0, 0.576, bz + 0.004), 'eject': (0.03, 0.020, 0.050),
                   'sight': (0, -0.070, sz), 'cls': 'shotgun', 'guard': (0, 0.365, bz - 0.022), 'port': (0, 0.052, -0.004),   # pump: palm under the forend
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}


def build_thunder(pal):
    """SG-12 Thunderclap: box-fed auto shotgun, square shroud, carry handle sight, big drum."""
    rake = 18
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.054, 0.072, ct=0.010, cb=0.004, cy=0.036), -0.120, 0.150, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.box((0.0265, 0.030, 0.048), (0.008, 0.060, 0.020), 'ink', skip=('-x',))
    k.ext_y(rrect(0.046, 0.026, c=0.003, cy=-0.002), -0.090, 0.140, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.070, 0.006), (0.140, 0.006), (0.142, -0.030), (0.134, -0.040), (0.070, -0.040), (0.066, -0.028)], -0.0265, 0.0265, 'gun2', ch=0.003)
    k.ext_y(rrect(0.058, 0.060, c=0.008, cy=bz), 0.148, 0.400, 'gun3', ch0=0.003, ch1=0.006)                    # square shroud
    for s in (-1, 1):
        for i in range(4):
            k.box((s * 0.0290, 0.180 + i * 0.052, bz + 0.004), (0.006, 0.030, 0.026), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.214, bz - 0.0305), (0.062, 0.100, 0.006), 'trim')
    barrel(k, 0.390, 0.450, 0.0140, bz, seg=12)
    k.lathe([(0.446, 0), (0.446, 0.0200), (0.488, 0.0200), (0.488, 0.0110), (0.478, 0.0110), (0.478, 0)], 'steel2', 'y', (0, 0, bz), 12)   # brake
    for i in range(4):
        a = D(45 + 90 * i)
        k.box((0.0205 * math.cos(a), 0.470, bz + 0.0205 * math.sin(a)), (0.006, 0.020, 0.008), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    # carry handle with a peep sight
    k.tube([((0, -0.060, 0.072), 0.014, 0.010), ((0, -0.050, 0.098), 0.014, 0.010), ((0, 0.100, 0.098), 0.014, 0.010), ((0, 0.110, 0.072), 0.014, 0.010)],
           'gunmetal', sides=6, up=(1, 0, 0))
    k.ring('y', (0, 0, 0.112), -0.064, -0.054, 0.004, 0.009, 'ink', seg=8, hull=False)
    k.box((0, 0.380, bz + 0.046), (0.006, 0.010, 0.040), 'ink', hull=True)
    trigger_guard(k, rake, front=0.062, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    vgrip(k, 0.300, bz - 0.030, length=0.070, seg=8)
    k.ext_x([(-0.116, 0.074), (-0.300, 0.060), (-0.302, -0.048), (-0.276, -0.054), (-0.170, -0.004), (-0.116, 0.006)], -0.023, 0.023, 'gun2', ch=0.005)
    k.ext_x([(-0.298, 0.066), (-0.318, 0.066), (-0.320, -0.054), (-0.300, -0.058)], -0.027, 0.027, 'ink', ch=0.003)
    # drum magazine (Mag): round drum with a feed neck
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.012), (0.040, 0.050, 0.030), 'gun2', ch=0.004, axis='x')
    mk.lathe([(-0.034, 0), (-0.034, 0.060), (-0.026, 0.064), (0.026, 0.064), (0.034, 0.060), (0.034, 0)], 'gun3', 'x', (0, 0.010, -0.080), 14)
    mk.ring('x', (0, 0.010, -0.080), 0.034, 0.040, 0.018, 0.030, 'red', seg=12, hull=False)
    mk.ring('x', (0, 0.010, -0.080), -0.040, -0.034, 0.018, 0.030, 'red', seg=12, hull=False)
    for i in range(6):
        a = D(60 * i)
        mk.box((0, 0.010 + 0.0665 * math.cos(a), -0.080 + 0.0665 * math.sin(a)), (0.050, 0.006, 0.006), 'ink', rot=(-math.degrees(a), 0, 0))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.040), 'muzzle': (0, 0.490, bz), 'eject': (0.03, 0.030, 0.050),
                   'sight': (0, -0.090, 0.112), 'cls': 'shotgun', 'fore': (0.300, bz - 0.030)}
