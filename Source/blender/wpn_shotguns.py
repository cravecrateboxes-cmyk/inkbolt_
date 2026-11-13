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


def crystal(k, p, d, L, r, color='emis', sides=5, hull=True):
    """Faceted crystal shard growing from p along d: a short root, the girdle, a point."""
    d = V(d).normalized()
    u = d.orthogonal().normalized()
    k.lathe([(-0.003, r * 0.55), (L * 0.5, r), (L, 0)], color, (d, u, d.cross(u)), p, sides, hull=hull, caps=(False, True))


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
    for i in range(3):
        a = D(120 * i + 90)
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
            r5.ext_x([(0.520, 0.010), (0.540, 0.010), (0.554, 0.0185), (0.5735, 0.0195), (0.562, 0.0255), (0.543, 0.0290), (0.526, 0.0235)], -0.0018, 0.0018, 'steel', ch=0.0012)
            r5.ext_x([(0.531, 0.0222), (0.543, 0.0262), (0.561, 0.0232), (0.5700, 0.0204), (0.558, 0.0208), (0.543, 0.0222)], -0.0032, 0.0032, 'trim', ch=0, hull=False)
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
    """SG-12 Thunderclap: drum-fed automatic shotgun. Slab receiver with the ejection port and bolt, a carry handle
    on two pillars (open underneath) whose top is the sight channel with the aperture between two ears, the charging
    handle in its slot under the handle, a square heat shroud built as a cage (vent rows on both sides and the top:
    the barrel, gas tube and gas block show through), ported compensator, tall front sight, foregrip.
    The drum (Mag part) has rim ribs, spokes, a winder key on the left face and a witness window with shell heads on
    the right.
    Rarity layers: Rare adds an aiming module with its cable, a shell counter behind the handle, butt armour and
    armour rings on the drum; Epic lays a cell under the carry handle, coils the barrel inside the shroud, fins the
    muzzle and lights the drum; Legendary (Aurora) grows crystal shards along the shroud's shoulders and round the
    compensator, draws constellations on the receiver and sets a starburst on each drum face."""
    rake = 18
    k = Kit(pal)
    bz = 0.040
    HR, HL, HM, HC, HS = 0.027, 0.023, 0.0265, 0.029, 0.023       # half widths: receiver, lower, magwell, shroud, stock
    # ---- receiver
    k.ext_y(rrect(0.054, 0.072, ct=0.010, cb=0.004, cy=0.036), -0.120, 0.150, 'gunmetal', ch0=0.005, ch1=0.004)
    plate(k, rect(-0.112, 0.142, 0.0165, 0.0190), HR, 'trim', ch=0)
    cross_pin(k, HR, -0.100, 0.0085)
    cross_pin(k, HR, 0.130, 0.0085)
    # right: ejection port with the bolt and extractor, case deflector, name plate, trunnion plate
    k.box((HR + PR / 2 - 0.0005, 0.030, 0.048), (PR + 0.001, 0.060, 0.020), 'ink', skip=sk(1))
    k.box((HR + PR, 0.038, 0.0485), (0.0036, 0.040, 0.014), 'steel', skip=sk(1))
    k.box((HR + PR + 0.0022, 0.054, 0.0485), (0.0036, 0.005, 0.009), 'steel2', skip=sk(1))
    k.ext_x([(-0.016, 0.038), (-0.004, 0.038), (-0.004, 0.058), (-0.011, 0.058)], HR - 0.001, HR + 0.0090, 'gunmetal', ch=0.0015)
    plate(k, [(-0.110, 0.024), (-0.030, 0.024), (-0.022, 0.032), (-0.022, 0.058), (-0.110, 0.058)], HR, 'body2', sides=(1,))
    stencil(k, 'THUNDERCLAP', HR + PR, -0.066, 0.0290, cap=0.0068, sides=(1,))
    slots(k, HR + PR, -0.102, -0.034, 0.047, 4, h=0.012, fill=0.36, sides=(1,), slant=28)
    plate(k, [(0.070, 0.024), (0.144, 0.024), (0.144, 0.058), (0.070, 0.058)], HR, 'gunmetal', t=0.003, sides=(1,), hull=True)
    bolts(k, HR + 0.003, [(0.078, 0.030), (0.136, 0.030), (0.078, 0.052), (0.136, 0.052)], sides=(1,))
    stencil(k, '12 GA', HR + 0.003, 0.107, 0.0370, cap=0.0085, sides=(1,))
    # left: data panel, trunnion plate with a hazard band
    plate(k, [(-0.110, 0.024), (0.040, 0.024), (0.052, 0.036), (0.052, 0.058), (-0.110, 0.058)], HR, 'body2', sides=(-1,))
    stencil(k, 'SG-12', HR + PR, -0.050, 0.0370, cap=0.013, sides=(-1,))
    stencil(k, 'IB ARMS  12 GA  AUTO', HR + PR, -0.050, 0.0280, cap=0.0048, sides=(-1,), font='cond')
    plate(k, [(0.062, 0.024), (0.144, 0.024), (0.144, 0.058), (0.072, 0.058), (0.062, 0.048)], HR, 'gunmetal', t=0.003, sides=(-1,), hull=True)
    bolts(k, HR + 0.003, [(0.070, 0.030), (0.136, 0.030), (0.136, 0.052)], sides=(-1,))
    hazard(k, HR + 0.003, 0.080, 0.128, 0.036, 0.048, n=4, sides=(-1,))
    # top: charging slot and handle under the carry handle
    k.box((0, 0.026, 0.072 + PR / 2 - 0.0005), (0.008, 0.112, PR + 0.001), 'ink', skip=('-z',))
    k.cbox((0, 0.066, 0.0765), (0.022, 0.012, 0.010), 'steel2', ch=0.002)
    for s in (-1, 1):
        bolt(k, (s * 0.011, -0.104, 0.072), (0, 0, 1), 0.0028)
        bolt(k, (s * 0.011, 0.134, 0.072), (0, 0, 1), 0.0028)
    # ---- carry handle: two pillars, the sight channel between two walls, aperture between the rear ears
    k.ext_x([(-0.070, 0.070), (-0.044, 0.070), (-0.050, 0.094), (-0.066, 0.094)], -0.009, 0.009, 'gunmetal', ch=0.002)
    k.ext_x([(0.090, 0.070), (0.118, 0.070), (0.112, 0.094), (0.096, 0.094)], -0.009, 0.009, 'gunmetal', ch=0.002)
    k.cbox((0, 0.024, 0.0945), (0.025, 0.196, 0.007), 'gunmetal', ch=0.002, axis='y')
    for s in (-1, 1):
        k.ext_x([(-0.0725, 0.096), (0.1205, 0.096), (0.113, 0.105), (-0.048, 0.105), (-0.056, 0.120), (-0.070, 0.120)], min(s * 0.0075, s * 0.0110), max(s * 0.0075, s * 0.0110),
                'gunmetal', ch=0.0008)
        bolt(k, (s * 0.009, -0.057, 0.082), (s, 0, 0), 0.0028)
        bolt(k, (s * 0.009, 0.104, 0.082), (s, 0, 0), 0.0028)
    k.box((0, 0.036, 0.098 + PR / 2 - 0.0005), (0.009, 0.150, PR + 0.001), 'ink', skip=('-z',))
    k.ring('y', (0, 0, 0.112), -0.064, -0.054, 0.0040, 0.0072, 'ink', seg=8, hull=False)
    turret(k, (0.0110, -0.062, 0.110), 'x', r=0.0055, h=0.004, color='steel2')
    # ---- lower receiver, magwell with its collar, controls
    k.ext_y(rrect(0.046, 0.026, c=0.003, cy=-0.002), -0.090, 0.140, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.070, 0.006), (0.140, 0.006), (0.142, -0.030), (0.134, -0.040), (0.070, -0.040), (0.066, -0.028)], -HM, HM, 'gun2', ch=0.003)
    k.ext_x([(0.062, -0.032), (0.146, -0.032), (0.150, -0.044), (0.058, -0.044)], -0.0295, 0.0295, 'frame2', ch=0.002)
    plate(k, rect(0.088, 0.134, -0.029, -0.002, c=0.003), HM, 'frame2')
    stencil(k, 'DRUM 20', HM + PR, 0.111, -0.0195, cap=0.0065)
    for s in (-1, 1):
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        k.lathe([(HM - 0.003, 0.0050), (HM + 0.0040, 0.0050), (HM + 0.0040, 0)], 'steel2', n, (0, 0.078, -0.014), 8, hull=False, caps=(False, True))
    k.lathe([(HL - 0.003, 0.0050), (HL + 0.0045, 0.0050), (HL + 0.0045, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, -0.040, -0.0075), 8, hull=False, caps=(False, True))
    k.xbar(-HL - 0.0075, -HL - 0.0040, [(-0.058, -0.0105), (-0.038, -0.012), (-0.036, -0.0045), (-0.056, -0.003)], 'gun3', ch=0, hull=False)
    k.box((-HL - PR / 2 + 0.0005, -0.068, -0.0065), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-HL - PR / 2 + 0.0005, -0.076, -0.0065), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    # ---- barrel group in the square shroud (a cage: vent rows on both sides and the top)
    k.lathe([(0.146, 0), (0.146, 0.0190), (0.160, 0.0190), (0.160, 0.0140), (0.450, 0.0140), (0.450, 0)], 'steel', 'y', (0, 0, bz), 12,
            bands=['steel2', 'steel2', 'steel2', None, None])
    k.lathe([(0.150, 0), (0.150, 0.0045), (0.392, 0.0045), (0.392, 0)], 'steel2', 'y', (0, 0, bz + 0.0195), 6, hull=False)
    k.cbox((0, 0.374, bz + 0.010), (0.024, 0.020, 0.030), 'steel2', ch=0.003, axis='y', hull=False)
    ys = cage(k, 0.150, 0.402, bz, 0.058, 0.060, 0.008, n=6, rib=0.010, open=('R', 'L', 'T'), color='gun3', edge=0.30, th=0.0055)
    for i, (a, b) in enumerate(zip(ys[:-1], ys[1:])):
        if i < 3:
            k.box((0, (a[1] + b[0]) / 2, bz - 0.0273), (0.055, b[0] - a[1] - 0.006, 0.0022), 'trim')
    for s in (-1, 1):
        bolt(k, (s * (HC + PR), 0.158, bz + 0.012), (s, 0, 0))
        bolt(k, (s * (HC + PR), 0.158, bz - 0.012), (s, 0, 0))
        sling_loop(k, 0.394, bz, s, hw=HC + PR, r=0.006)
    # tall front sight on the shroud's nose
    k.ext_x([(0.378, 0.068), (0.400, 0.068), (0.395, 0.100), (0.385, 0.100)], -0.0080, 0.0080, 'gunmetal', ch=0.0015)
    plate(k, [(0.384, 0.076), (0.395, 0.076), (0.3925, 0.092), (0.3865, 0.092)], 0.0080, 'ink', ch=0)
    for s in (-1, 1):
        k.ext_x([(0.383, 0.098), (0.397, 0.098), (0.394, 0.119), (0.386, 0.119)], min(s * 0.0045, s * 0.0098), max(s * 0.0045, s * 0.0098), 'gunmetal', ch=0.0008)
    k.box((0, 0.390, 0.1045), (0.0036, 0.005, 0.015), 'ink')
    # big compensator: side, top and diagonal ports
    k.ring('y', (0, 0, bz), 0.4360, 0.4445, 0.0140, 0.0185, 'steel', seg=8, hull=False)
    muzzle(k, 0.446, 0.488, 0.0215, bz, color='steel2', ports=3, top_ports=3, rb=0.0115, seg=8, slot=0.007)
    for i in range(4):
        a = D(45 + 90 * i)
        k.box((0.0195 * math.cos(a), 0.467, bz + 0.0195 * math.sin(a)), (0.008, 0.024, 0.007), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    trigger_guard(k, rake, front=0.062, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    vgrip(k, 0.300, bz - 0.030, length=0.070, seg=8)
    # ---- stock: polymer body with a recessed panel, accent line, ribbed recoil pad
    k.ext_x([(-0.114, 0.070), (-0.298, 0.060), (-0.300, -0.048), (-0.276, -0.054), (-0.170, -0.004), (-0.114, 0.006)], -HS, HS, 'gun2', ch=0.005)
    plate(k, [(-0.130, 0.012), (-0.170, 0.012), (-0.286, -0.036), (-0.286, 0.046), (-0.130, 0.055)], HS, 'frame2')
    slots(k, HS + PR, -0.274, -0.202, 0.020, 4, h=0.020, fill=0.34, slant=-26)
    stencil(k, '12', HS + PR, -0.158, 0.026, cap=0.016)
    bolts(k, HS + PR, [(-0.136, 0.018), (-0.136, 0.046)])
    plate(k, [(-0.126, 0.0605), (-0.290, 0.0515), (-0.290, 0.0540), (-0.126, 0.0630)], HS, 'trim', ch=0)
    for s in (-1, 1):
        sling_loop(k, -0.186, 0.000, s, hw=HS, r=0.0055)
    k.cbox((0, -0.215, 0.0652), (0.030, 0.104, 0.005), 'rubber', ch=0.0015, axis='y', rot=(3.1, 0, 0))
    for i in range(5):
        k.box((0, -0.251 + i * 0.018, 0.0660 + i * 0.00098), (0.020, 0.005, 0.0052), 'ink', rot=(3.1, 0, 0))
    k.ext_x([(-0.296, 0.066), (-0.316, 0.066), (-0.318, -0.054), (-0.298, -0.058)], -0.027, 0.027, 'rubber', ch=0.003)
    for i in range(5):
        z = 0.050 - i * 0.022
        for s in (-1, 1):
            k.box((s * (0.027 + PR / 2 - 0.0005), -0.308, z), (PR + 0.001, 0.010, 0.006), 'ink', skip=sk(s))
        k.box((0, -0.3175 - PR / 2, z), (0.038, PR + 0.002, 0.005), 'ink', skip=('+y',))
    # ---- drum magazine (Mag): feed neck, drum with rim ribs and spokes, winder key (left), witness window (right)
    mk = Kit(pal)
    C = (0, 0.010, -0.080)
    mk.cbox((0, 0.0, -0.012), (0.040, 0.050, 0.030), 'gun2', ch=0.004, axis='x')
    mk.lathe([(-0.034, 0), (-0.034, 0.060), (-0.026, 0.064), (0.026, 0.064), (0.034, 0.060), (0.034, 0)], 'gun3', 'x', C, 14)
    for ad in (0, 30, 150, 180, 210, 240, 300, 330):
        a = D(ad)
        mk.box((0, C[1] + 0.0650 * math.cos(a), C[2] + 0.0650 * math.sin(a)), (0.050, 0.005, 0.006), 'acc2', rot=(ad - 90, 0, 0))
    for s in (-1, 1):
        mk.ring('x', C, min(s * 0.0330, s * 0.0372), max(s * 0.0330, s * 0.0372), 0.0178, 0.0238, 'red', seg=12, hull=False)
        for ad in ((0, 60, 120, 180, 240, 300) if s < 0 else (0, 60, 120, 180)):
            a = D(ad)
            mk.box((s * 0.0352, C[1] + 0.041 * math.cos(a), C[2] + 0.041 * math.sin(a)), (0.0036, 0.005, 0.028), 'acc2', rot=(ad - 90, 0, 0))
    mk.lathe([(0.033, 0.0150), (0.0395, 0.0150), (0.0395, 0.0100), (0.0375, 0.0100), (0.0375, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), C, 10,
             hull=False, caps=(False, True))
    mk.cbox((-0.0430, C[1], C[2]), (0.008, 0.008, 0.034), 'steel', ch=0.002, rot=(28, 0, 0))
    mk.box((0.034 + PR / 2 - 0.0005, C[1], C[2] - 0.040), (PR + 0.001, 0.046, 0.014), 'ink', skip=sk(1))
    for dy in (-0.015, 0.0, 0.015):
        bolt(mk, (0.034 + PR, C[1] + dy, C[2] - 0.040), (1, 0, 0), r=0.0055, h=0.0034, color='brass', seg=8)

    # ---- Rare (and up): aiming module with its cable, shell counter behind the handle, butt armour; drum armour rings
    r3 = Kit(pal)
    laser_box(r3, 0.352, bz + 0.004, s=-1, hw=HC + PR, L=0.046, w=0.016, h=0.022, color='gun2')
    cable(r3, [(-0.0380, 0.330, bz + 0.004), (-0.0345, 0.316, bz + 0.016), (-0.0318, 0.300, bz + 0.0255), (-0.0318, 0.166, bz + 0.0255), (-0.0270, 0.146, bz + 0.0240)], clamps=(2, 3))
    r3.cbox((0, -0.096, 0.0780), (0.030, 0.030, 0.012), 'gun2', ch=0.002)
    for i in range(4):
        r3.box((-0.0090 + i * 0.0060, -0.096, 0.084 + PR / 2 - 0.0005), (0.0040, 0.016, PR + 0.001), 'emis', skip=('-z',))
        r3.box((-0.0090 + i * 0.0060, -0.111 - PR / 2 + 0.0005, 0.0780), (0.0040, PR + 0.001, 0.0060), 'emis', skip=('+y',))
    plate(r3, [(-0.296, -0.050), (-0.276, -0.050), (-0.246, -0.034), (-0.246, -0.020), (-0.296, -0.020)], HS + PR, 'gun3', t=0.003, hull=True)
    bolts(r3, HS + PR + 0.003, [(-0.290, -0.026), (-0.290, -0.042), (-0.254, -0.027)])
    plate(r3, [(-0.296, 0.050), (-0.246, 0.052), (-0.246, 0.040), (-0.296, 0.040)], HS + PR, 'gun3', t=0.003, hull=True)
    m3 = Kit(pal)
    for s in (-1, 1):
        m3.ring('x', C, min(s * 0.0310, s * 0.0386), max(s * 0.0310, s * 0.0386), 0.0505, 0.0592, 'steel2', seg=14, hull=False)

    # ---- Epic (and up): cell under the carry handle, conduit into the shroud, coils round the barrel, muzzle fins
    r4 = Kit(pal)
    energy_cell(r4, (0, -0.008, 0.0810), L=0.056, r=0.0064, cage_bars=4)
    conduit(r4, [(0.0080, 0.020, 0.0800), (0.0140, 0.034, 0.0747), (0.0140, 0.140, 0.0747), (0.0125, 0.158, 0.0705)], r=0.0026, every=1)
    for (a, b) in zip(ys[:-1], ys[1:]):
        ym = (a[1] + b[0]) / 2
        if abs(ym - 0.374) < 0.016:
            continue
        r4.ring('y', (0, 0, bz), ym - 0.006, ym + 0.006, 0.0140, 0.0178, 'emis', seg=8, hull=False)
    fins(r4, (0, 0.420, bz), (0.046, 0.026, 0.046), 3, axis='y', color='gun2', hull=True)
    slots(r4, HS + 2 * PR, -0.274, -0.202, 0.020, 4, h=0.012, fill=0.12, color='emis', slant=-26)
    m4 = Kit(pal)
    for s in (-1, 1):
        m4.ring('x', C, min(s * 0.0310, s * 0.0390), max(s * 0.0310, s * 0.0390), 0.0290, 0.0325, 'emis', seg=14, hull=False)

    # ---- Legendary: crystal shards on the shroud's shoulders and round the compensator, constellations, drum starbursts
    r5 = Kit(pal)
    for s in (-1, 1):
        for i, (a, b) in enumerate(zip(ys[:-1], ys[1:])):
            ym = (a[1] + b[0]) / 2
            L = (0.042, 0.028, 0.046, 0.026, 0.038, 0.024)[i % 6]
            crystal(r5, (s * 0.0250, ym + 0.004, bz + 0.0260), (s * 0.78, -0.30 + 0.12 * (i % 3), 0.62), L, 0.0066)
            crystal(r5, (s * 0.0250, ym - 0.010, bz + 0.0260), (s * 0.60, 0.25, 0.75), L * 0.55, 0.0046, color='gun3')
    for i in range(5):
        a = D(72 * i + 18)
        crystal(r5, (0.0150 * math.cos(a), 0.444, bz + 0.0150 * math.sin(a)), (math.cos(a) * 0.80, -0.52, math.sin(a) * 0.80), 0.040 if i % 2 == 0 else 0.028, 0.0062)
    stars = [(-0.096, 0.050), (-0.070, 0.036), (-0.040, 0.052), (-0.012, 0.040), (0.016, 0.052)]
    for s in (-1, 1):
        for (y, z) in (stars if s < 0 else stars[:2]):
            plate(r5, [(y - 0.0045, z), (y, z - 0.0045), (y + 0.0045, z), (y, z + 0.0045)], HR + PR, 'emis', t=0.0030, ch=0.0012, sides=(s,))
    r5.ext_x([(-0.096, 0.0495), (-0.070, 0.0355), (-0.070, 0.0367), (-0.096, 0.0507)], -HR - 2 * PR, -HR - PR + 0.0005, 'trim', hull=False)
    r5.ext_x([(-0.070, 0.0355), (-0.040, 0.0515), (-0.040, 0.0527), (-0.070, 0.0367)], -HR - 2 * PR, -HR - PR + 0.0005, 'trim', hull=False)
    r5.ext_x([(-0.040, 0.0520), (-0.012, 0.0400), (-0.012, 0.0412), (-0.040, 0.0532)], -HR - 2 * PR, -HR - PR + 0.0005, 'trim', hull=False)
    crystal(r5, (0, -0.210, 0.060), (0, -0.35, 0.94), 0.040, 0.0078)
    crystal(r5, (0.006, -0.238, 0.058), (0.2, -0.50, 0.87), 0.027, 0.0058, color='gun3')
    crystal(r5, (-0.006, -0.184, 0.062), (-0.2, -0.20, 0.98), 0.024, 0.0054, color='gun3')
    m5 = Kit(pal)
    for s in (-1, 1):
        for j in range(8):
            ad = 45 * j + 22.5
            a = D(ad)
            Lr = 0.022 if j % 2 == 0 else 0.013
            with m5.at((s * 0.0340, C[1], C[2]), (ad - 90, 0, 0)):
                m5.ext_x([(-0.0035, 0.0300), (0.0035, 0.0300), (0.0, 0.0300 + Lr)], min(s * 0.0040, s * 0.0073), max(s * 0.0040, s * 0.0073), 'trim', hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.040), 'muzzle': (0, 0.490, bz), 'eject': (0.03, 0.030, 0.050),
                   'sight': (0, -0.090, 0.112), 'cls': 'shotgun', 'fore': (0.300, bz - 0.030),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'345': m3, '45': m4, '5': m5}}
