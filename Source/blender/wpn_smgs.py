"""INKBOLT guns: SMGs. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_buzz(pal):
    """KV-9 Buzzsaw: boxy all-round SMG. Polymer upper in three sections (the ejection port is a real cut with the bolt
    in it) with cladding plates and assembly bolts, a charging-handle channel with its folded handle on the left, a
    lower with selector, bolt release and paddle mag catch, a short cage handguard (the barrel shows through), front
    sight, birdcage flash hider, vertical foregrip on a lug and a folding skeleton stock on a two-knuckle hinge.
    Rarity layers: Rare bolts on a strike plate, an aiming module with its cable, a magwell funnel, a round counter and
    stock saddles; Epic slings an energy cell in the stock, runs a conduit to coils on the barrel and adds a radiator;
    Legendary (gold) is the saw: a toothed blade round the barrel, a saw-back on the stock, saw emblems on the magwell."""
    rake = 14
    k = Kit(pal)
    bz = 0.040
    HU, HL, HM, HG = 0.024, 0.020, 0.0225, 0.022                 # half widths: upper, lower, magwell, handguard
    # ---- upper receiver
    full = rrect(0.048, 0.060, ct=0.009, cb=0.004, cy=0.038)
    cut = [(0.020, 0.008), (HU, 0.012), (HU, 0.041), (0.010, 0.041), (0.010, 0.057), (HU, 0.057), (HU, 0.059), (0.015, 0.068), (-0.015, 0.068),
           (-HU, 0.059), (-HU, 0.012), (-0.020, 0.008)]
    k.ext_y(full, -0.096, 0.016, 'gunmetal', ch0=0.005)
    k.ext_y(cut, 0.016, 0.066, 'gunmetal')
    k.ext_y(full, 0.066, 0.140, 'gunmetal', ch1=0.004)
    k.box((0.01625, 0.041, 0.049), (0.0095, 0.047, 0.013), 'ink')                                                    # port, bolt
    k.box((0.01775, 0.037, 0.049), (0.0095, 0.030, 0.010), 'steel2')
    k.box((0.0225 + PR / 2 - 0.0005, 0.047, 0.049), (PR + 0.001, 0.0035, 0.0045), 'steel', skip=sk(1))
    k.ext_y([(HU - 0.001, 0.043), (HU + 0.004, 0.046), (HU + 0.004, 0.054), (HU - 0.001, 0.057)], 0.003, 0.0135, 'gunmetal', ch0=0.003)   # brass deflector
    rail(k, -0.090, 0.132, 0.068, w=0.022, clear=[(-0.078, -0.036)])
    hz = hood_sight(k, -0.076, -0.038, 0.071)
    bolt(k, (0.015, -0.057, 0.075), (1, 0, 0), 0.0030)
    turret(k, (-0.017, -0.057, 0.091), '-x', r=0.0050, h=0.005)
    # charging-handle channel (left) with the folded handle
    k.cbox((-HU - 0.0015, 0.078, 0.056), (0.007, 0.116, 0.012), 'body2', ch=0.002, axis='y')
    k.box((-HU - 0.005 - PR / 2 + 0.0005, 0.072, 0.056), (PR + 0.001, 0.088, 0.0036), 'ink', skip=sk(-1))
    k.cbox((-HU - 0.011, 0.122, 0.056), (0.014, 0.009, 0.008), 'gun3', ch=0.002)
    k.box((-HU - 0.018 - PR / 2 + 0.0005, 0.122, 0.056), (PR + 0.001, 0.0045, 0.004), 'ink', skip=sk(-1))
    # cladding, markings, assembly bolts
    for s in (-1, 1):
        plate(k, [(-0.082, 0.028), (-0.030, 0.028), (-0.026, 0.032), (-0.026, 0.052), (-0.082, 0.052)], HU, 'body2', sides=(s,))
    stencil(k, 'KV-9', HU + PR, -0.054, 0.0355, cap=0.012, sides=(-1,))
    stencil(k, 'BUZZSAW  9MM', HU + PR, -0.054, 0.0300, cap=0.004, sides=(-1,), font='cond')
    stencil(k, 'BUZZSAW', HU + PR, -0.054, 0.0375, cap=0.009, sides=(1,))
    stencil(k, 'IB ARMS', HU + PR, -0.054, 0.0310, cap=0.004, sides=(1,), font='cond')
    slots(k, HU, -0.020, 0.012, 0.040, 4, h=0.016, fill=0.45, sides=(-1,), slant=-25)
    slots(k, HU, -0.022, 0.002, 0.036, 3, h=0.014, fill=0.45, sides=(1,), slant=-25)
    plate(k, [(0.024, 0.028), (0.134, 0.028), (0.134, 0.046), (0.030, 0.046), (0.024, 0.040)], HU, 'gunmetal', t=0.003, sides=(-1,), hull=True)
    bolts(k, HU + 0.003, [(0.030, 0.032), (0.128, 0.032), (0.128, 0.042)], sides=(-1,))
    stencil(k, 'CAL 9X19', HU + 0.003, 0.080, 0.034, cap=0.006, sides=(-1,))
    plate(k, rect(0.072, 0.134, 0.028, 0.055, c=0.003), HU, 'body2', sides=(1,))
    hazard(k, HU + PR, 0.084, 0.126, 0.043, 0.051, n=4, sides=(1,))
    stencil(k, 'KV-9', HU + PR, 0.104, 0.031, cap=0.008, sides=(1,))
    plate(k, rect(-0.090, 0.134, 0.0215, 0.0245), HU, 'trim', ch=0)
    bolts(k, HU, [(-0.086, 0.0555), (-0.050, 0.0555), (-0.0245, 0.0555)], r=0.0026)
    # ---- lower: trigger housing, controls, magwell
    k.ext_y(rrect(0.040, 0.026, c=0.003, cy=0.005), -0.070, 0.124, 'gun2', ch0=0.004, ch1=0.004)
    k.lathe([(HL - 0.003, 0.0050), (HL + 0.004, 0.0050), (HL + 0.004, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, -0.040, 0.002), 8, hull=False, caps=(False, True))
    k.xbar(-HL - 0.0070, -HL - 0.0035, [(-0.058, -0.001), (-0.038, -0.002), (-0.036, 0.005), (-0.056, 0.007)], 'gun3', ch=0, hull=False)     # selector
    k.box((-HL - PR / 2 + 0.0005, -0.065, 0.004), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-HL - PR / 2 + 0.0005, -0.063, -0.003), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    bolt(k, (HL, -0.040, 0.002), (1, 0, 0), 0.0034)
    k.xbar(-HL - 0.004, -HL + 0.001, [(0.014, -0.002), (0.030, -0.002), (0.032, 0.007), (0.024, 0.009), (0.014, 0.004)], 'gun3', ch=0, hull=False)   # bolt release
    cross_pin(k, HL, -0.014, 0.004, r=0.0030)
    cross_pin(k, HL, 0.050, 0.004, r=0.0030)
    k.ext_x([(0.066, 0.010), (0.118, 0.010), (0.120, -0.030), (0.114, -0.038), (0.066, -0.038), (0.062, -0.026)], -HM, HM, 'gun2', ch=0.003)
    plate(k, [(0.072, 0.004), (0.114, 0.004), (0.115, -0.026), (0.111, -0.031), (0.072, -0.031)], HM, 'frame2')
    slots(k, HM + PR, 0.078, 0.108, -0.014, 3, h=0.022, fill=0.4)
    k.ext_x([(0.064, -0.0335), (0.117, -0.0335), (0.120, -0.0415), (0.062, -0.0415)], -0.0245, 0.0245, 'frame2', ch=0.0015)                 # well lip
    for s in (-1, 1):                                                                                                                       # paddle mag catch
        x0, x1 = sorted((s * (HM - 0.001), s * (HM + 0.003)))
        k.ext_x([(0.064, -0.012), (0.076, -0.012), (0.076, -0.018), (0.064, -0.026), (0.060, -0.022)], x0, x1, 'gun3', ch=0, hull=False)
    # ---- cage handguard, barrel, flash hider, front sight
    k.lathe([(0.136, 0.0090), (0.246, 0.0090)], 'steel', 'y', (0, 0, bz), 10, caps=(False, False))
    ys = cage(k, 0.138, 0.214, 0.030, 0.044, 0.044, 0.009, n=3, rib=0.008, open=('R', 'UR', 'UL', 'L'), color='gun2', end=0.012, th=0.0025)
    for (a, b) in list(zip(ys[:-1], ys[1:]))[:2]:
        top_slots(k, 0.052, a[1] + 0.002, b[0] - 0.002, 1, w=0.012, fill=0.5)
    for s in (-1, 1):
        bolt(k, (s * (HG + PR), 0.144, 0.036), (s, 0, 0))
        bolt(k, (s * (HG + PR), 0.144, 0.024), (s, 0, 0))
        sling_loop(k, 0.208, 0.030, s, hw=HG + PR, r=0.0050)
    iron_front(k, 0.195, 0.052, w=0.026, h=0.012, post=0.010)
    muzzle(k, 0.246, 0.280, 0.0115, bz, ports=3, top_ports=3, rb=0.0055, seg=8)
    k.ring('y', (0, 0, bz), 0.238, 0.247, 0.0090, 0.0128, 'steel2', seg=10, hull=False)
    k.cbox((0, 0.180, 0.0055), (0.036, 0.047, 0.007), 'gun2', ch=0.002, axis='y')                                                           # foregrip lug
    vgrip(k, 0.180, 0.010, seg=8)
    trigger_guard(k, rake, front=0.062, depth=-0.046, hook=False, top=0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=0.010, ptop=-0.028, grooves=2)
    # ---- folding skeleton stock: two hinge knuckles on one pin, latch, top bar, strut, butt with a ribbed pad
    k.cbox((0, -0.104, 0.044), (0.034, 0.018, 0.034), 'steel2', ch=0.003)
    k.cbox((0, -0.104, 0.008), (0.034, 0.018, 0.016), 'steel2', ch=0.003)
    k.lathe([(-0.002, 0), (-0.002, 0.0042), (0.064, 0.0042), (0.064, 0)], 'steel', 'z', (0.0165, -0.1125, 0), 8, hull=False)
    k.lathe([(-0.001, 0.0055), (0.003, 0.0055), (0.003, 0.0040), (0.0045, 0.0040), (0.0045, 0)], 'gun3', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))),
            (-0.017, -0.104, 0.044), 8, hull=False, bands=[None, 'ink', None, None], caps=(False, True))
    k.cbox((0, -0.180, 0.050), (0.016, 0.140, 0.014), 'furn', ch=0.003, axis='y')
    slots(k, 0.008, -0.232, -0.130, 0.050, 6, h=0.006, fill=0.55)
    top_slots(k, 0.057, -0.236, -0.130, 8, w=0.010, fill=0.35)
    k.bar((0, -0.100, 0.004), (0, -0.240, -0.030), 0.014, 0.012, 'furn', hull=True)
    k.ext_x([(-0.232, 0.060), (-0.246, 0.060), (-0.247, -0.040), (-0.234, -0.036)], -0.017, 0.017, 'furn', ch=0.003)
    k.ext_x([(-0.246, 0.062), (-0.257, 0.060), (-0.259, -0.042), (-0.247, -0.044)], -0.019, 0.019, 'rubber', ch=0.003)
    for s in (-1, 1):
        for i in range(4):
            k.box((s * (0.019 + PR / 2 - 0.0005), -0.2525, 0.047 - i * 0.025), (PR + 0.001, 0.007, 0.005), 'ink', skip=sk(s))
        bolt(k, (s * 0.017, -0.240, 0.046), (s, 0, 0))
        bolt(k, (s * 0.017, -0.240, -0.026), (s, 0, 0))
        sling_loop(k, -0.240, 0.010, s, hw=0.017, r=0.006)
    mk = Kit(pal)
    mag_box(mk, 2, 0.034, -0.150, 0.040, 0.026, plate='gun3')

    # ---- Rare (and up): strike plate, aiming module with its cable, magwell funnel, round counter, stock saddles
    r3 = Kit(pal)
    plate(r3, [(-0.078, 0.031), (-0.034, 0.031), (-0.030, 0.035), (-0.030, 0.049), (-0.078, 0.049)], HU + PR, 'gun3', t=0.0035, sides=(1,), hull=True)
    bolts(r3, HU + PR + 0.0035, [(-0.073, 0.035), (-0.073, 0.045), (-0.036, 0.045)], sides=(1,))
    slots(r3, HU + PR + 0.0035, -0.064, -0.042, 0.040, 3, h=0.009, fill=0.4, sides=(1,), slant=25)
    laser_box(r3, 0.176, 0.030, s=1, hw=HG + PR, L=0.046, w=0.016, h=0.020, color='gun2')
    cable(r3, [(0.0320, 0.153, 0.030), (0.0285, 0.142, 0.022), (0.0268, 0.128, 0.0165), (0.0268, 0.102, 0.0165), (0.0268, 0.088, 0.0165)], clamps=(3,))
    r3.ext_x([(0.058, -0.030), (0.124, -0.030), (0.128, -0.048), (0.056, -0.048)], -0.0285, 0.0285, 'gun3', ch=0.003)
    bolts(r3, 0.0285, [(0.066, -0.039), (0.118, -0.039)])
    r3.cbox((-HU - 0.002, -0.004, 0.0545), (0.006, 0.030, 0.008), 'gun2', ch=0.001, hull=False)
    for i in range(4):
        r3.box((-HU - 0.005 - PR / 2 + 0.0005, -0.013 + i * 0.006, 0.0545), (PR + 0.001, 0.0036, 0.005), 'emis', skip=sk(-1))
    for s in (-1, 1):
        r3.cbox((s * 0.0105, -0.181, 0.050), (0.007, 0.068, 0.018), 'gun3', ch=0.002)
        bolt(r3, (s * 0.014, -0.207, 0.050), (s, 0, 0))
        bolt(r3, (s * 0.014, -0.155, 0.050), (s, 0, 0))

    # ---- Epic (and up): energy cell slung in the stock, conduit along the receiver to coils on the barrel, radiator
    r4 = Kit(pal)
    r4.cbox((0, -0.176, 0.0405), (0.020, 0.044, 0.007), 'gun2', ch=0.002, axis='y')
    energy_cell(r4, (0, -0.176, 0.027), L=0.056, r=0.0095, cage_bars=4)
    conduit(r4, [(0, -0.146, 0.027), (-0.012, -0.128, 0.024), (-0.0215, -0.114, 0.019), (-0.0268, -0.094, 0.0165), (-0.0268, 0.030, 0.0165),
                 (-0.0268, 0.128, 0.0165), (-0.0215, 0.146, 0.026), (-0.012, 0.155, 0.034)], r=0.0028, every=2)
    for yc in (0.1547, 0.1720, 0.1933):
        r4.lathe([(yc - 0.004, 0.0090), (yc - 0.004, 0.0105), (yc + 0.004, 0.0105), (yc + 0.004, 0.0090)], 'emis', 'y', (0, 0, bz), 8, hull=False, closed=True, a0=0)
    fins(r4, (0, 0.2265, bz), (0.030, 0.0195, 0.030), 3, axis='y', color='gun3', hull=True)
    for y0 in (0.2225, 0.2290):
        r4.ring('y', (0, 0, bz), y0, y0 + 0.0015, 0.0090, 0.0125, 'emis', seg=8, hull=False)
    for s in (-1, 1):
        r4.box((s * (0.014 + PR / 2 - 0.0005), -0.181, 0.050), (PR + 0.001, 0.038, 0.003), 'emis', skip=sk(s))

    # ---- Legendary: the saw. Toothed blade round the barrel, saw-back on the stock, saw emblems on the magwell
    r5 = Kit(pal)

    def saw(n, ro, ri, cx, cz, a0=0.0, lead=8.0):
        pts = []
        for i in range(n):
            a = D(a0 + 360.0 * i / n)
            b = D(a0 + 360.0 * i / n + lead)
            pts += [(cx + ro * math.cos(a), cz + ro * math.sin(a)), (cx + ri * math.cos(b), cz + ri * math.sin(b))]
        return pts
    r5.ext_y(saw(12, 0.0300, 0.0215, 0.0, bz, a0=15), 0.2330, 0.2366, 'gun3', ch0=0.0008, ch1=0.0008)
    r5.ring('y', (0, 0, bz), 0.2355, 0.2425, 0.0145, 0.0168, 'trim', seg=10, hull=False)
    for s in (-1, 1):
        x0, x1 = sorted((s * (HM + PR - 0.0005), s * (HM + PR + 0.0035)))
        r5.ext_x(saw(8, 0.0150, 0.0105, 0.093, -0.013, a0=22.5 if s > 0 else 0, lead=10 * s), x0, x1, 'gun3', ch=0.0006)
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(0.0035, 0.0055), (0.0050, 0.0055), (0.0050, 0.0036), (0.0062, 0.0024), (0.0068, 0)], 'trim', n, (s * (HM + PR), 0.093, -0.013), 8, hull=False,
                 bands=[None, None, 'emis', 'emis'], caps=(False, True))
    back = [(-0.118, 0.0555), (-0.240, 0.0555)]
    for j in range(10):
        y0 = -0.240 + j * 0.012
        back += [(y0 + 0.001, 0.0660), (y0 + 0.012, 0.0595)]
    r5.ext_x(back, -0.0025, 0.0025, 'gun3', ch=0.0006)
    r5.lathe([(-0.001, 0.0048), (0.004, 0.0048), (0.008, 0)], 'gun3', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (-HU - 0.018, 0.122, 0.056), 6, hull=False, caps=(False, True))
    r5.lathe([(0.0045, 0.0030), (0.0060, 0.0030), (0.0075, 0)], 'emis', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (-0.017, -0.104, 0.044), 6, hull=False, caps=(False, True))
    m5 = Kit(pal)
    for t in (0.35, 0.65):
        y, z = g2w(2, 0.0, 0.034 + (-0.150 - 0.034) * t)
        m5.cbox((0, y, z), (0.036, 0.050, 0.006), 'trim', ch=0, rot=(-2, 0, 0))
    return k, mk, {'rake': rake, 'mrake': 2, 'mag': (0, 0.092, -0.038), 'muzzle': (0, 0.282, bz), 'eject': (0.03, 0.040, 0.050),
                   'sight': (0, -0.100, hz), 'cls': 'smg', 'fore': (0.180, 0.010),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'5': m5}}


def build_whisk(pal):
    """KV-4 Whiplash: compact machine pistol, magazine in the grip. Receiver in three sections (the ejection port is a
    real cut with the bolt in it), T cocking handle on its stem, selector with its marks, takedown pins; a long
    suppressor on a hex mount nut with a wrench collar, twin accent rings, a knurled grip band, sight clamp and a
    ported endcap; folding foregrip on a hinge block; sliding wire stock in bushings with its latch and a ribbed pad.
    Rarity layers: Rare adds an aiming module, a suppressor wrap, a magwell funnel, a round counter and butt plates;
    Epic slings an energy cell between the stock rods, runs a conduit to the can and adds cooling discs and glow
    rings; Legendary (aurora) winds two ribbons of light round the suppressor under a crown of crystals, with star
    emblems on the receiver and crystals on the butt."""
    rake = 8
    k = Kit(pal)
    bz = 0.032
    HU = 0.022
    # ---- receiver
    full = rrect(0.044, 0.064, ct=0.010, cb=0.004, cy=0.026)
    cut = [(0.018, -0.006), (HU, -0.002), (HU, 0.038), (0.008, 0.038), (0.008, 0.054), (0.016, 0.054), (0.012, 0.058), (-0.012, 0.058), (-HU, 0.048),
           (-HU, -0.002), (-0.018, -0.006)]
    k.ext_y(full, -0.078, 0.000, 'gunmetal', ch0=0.005)
    k.ext_y(cut, 0.000, 0.040, 'gunmetal')
    k.ext_y(full, 0.040, 0.110, 'gunmetal', ch1=0.012)
    k.ext_y([(0.0095, 0.0395), (0.019, 0.0395), (0.019, 0.0468), (0.0133, 0.0525), (0.0095, 0.0525)], 0.0015, 0.0385, 'ink', hull=False)      # port
    k.ext_y([(0.011, 0.041), (0.0205, 0.041), (0.0205, 0.0474), (0.0169, 0.051), (0.011, 0.051)], 0.006, 0.030, 'steel2', hull=False)        # bolt
    rail(k, -0.075, 0.096, 0.058, w=0.022, clear=[(-0.070, -0.050)])
    sz = iron_rear(k, -0.060, 0.058, w=0.026, h=0.011)
    plate(k, rect(-0.066, 0.094, 0.018, 0.036, c=0.003), HU, 'body2')
    stencil(k, 'KV-4', HU + PR, 0.012, 0.0215, cap=0.011, sides=(-1,))
    stencil(k, 'WHIPLASH  4.6MM', HU + PR, 0.066, 0.0250, cap=0.004, sides=(-1,), font='cond')
    stencil(k, 'WHIPLASH', HU + PR, 0.014, 0.0230, cap=0.008, sides=(1,))
    hazard(k, HU, 0.052, 0.088, 0.039, 0.046, n=4, sides=(1,))
    slots(k, HU, 0.006, 0.062, 0.008, 5, h=0.008, fill=0.5, slant=-20)
    bolts(k, HU, [(-0.070, 0.043), (-0.070, 0.003), (0.0945, 0.004)], r=0.0026)
    bolt(k, (-HU, 0.0945, 0.043), (-1, 0, 0), 0.0026)
    # controls: selector with its marks, takedown pins, mag release
    k.lathe([(HU - 0.003, 0.0048), (HU + 0.004, 0.0048), (HU + 0.004, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, -0.032, 0.008), 8, hull=False, caps=(False, True))
    k.xbar(-HU - 0.0070, -HU - 0.0035, [(-0.034, 0.004), (-0.014, 0.005), (-0.012, 0.011), (-0.032, 0.012)], 'gun3', ch=0, hull=False)
    k.box((-HU - PR / 2 + 0.0005, -0.043, 0.0095), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-HU - PR / 2 + 0.0005, -0.043, 0.0030), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    bolt(k, (HU, -0.032, 0.008), (1, 0, 0), 0.0034)
    cross_pin(k, HU, 0.080, 0.006, r=0.0030)
    cross_pin(k, HU, -0.062, 0.006, r=0.0030)
    k.lathe([(HU - 0.002, 0.0046), (HU + 0.0015, 0.0046), (HU + 0.0015, 0.0034), (HU + 0.0035, 0.0034), (HU + 0.0035, 0)], 'gun3',
            (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.068, 0.004), 8, hull=False, bands=['ink', 'ink', None, None], caps=(False, True))
    # T cocking handle on its stem
    k.box((0, -0.080, 0.050), (0.012, 0.010, 0.008), 'steel2')
    k.cbox((0, -0.087, 0.050), (0.042, 0.008, 0.011), 'gun3', ch=0.002, axis='x')
    for s in (-1, 1):
        for j in range(3):
            k.box((s * (0.011 + j * 0.0035), -0.091 - PR / 2 + 0.0005, 0.050), (0.0018, PR + 0.001, 0.007), 'ink', skip=('+y',))
    # ---- suppressor: mount nut, wrench collar, can with a stepped endcap, accent rings, knurling, ports, sight clamp
    L1, r = 0.270, 0.0205
    k.lathe([(0.102, 0), (0.102, 0.0228), (0.118, 0.0228), (0.118, 0)], 'steel2', 'y', (0, 0, bz), 6)
    k.lathe([(0.117, 0), (0.117, r - 0.003), (0.120, r), (0.250, r), (0.250, r + 0.0015), (L1 - 0.004, r + 0.0015), (L1, r - 0.003), (L1, 0.006), (L1 - 0.010, 0.006),
             (L1 - 0.010, 0)], 'gun3', 'y', (0, 0, bz), 12, bands=[None, None, None, 'acc2', 'acc2', 'acc2', 'acc2', 'ink', 'ink'])
    k.lathe([(0.1215, r - 0.001), (0.1215, 0.0255), (0.134, 0.0255), (0.134, r - 0.001)], 'acc2', 'y', (0, 0, bz), 6, closed=True, a0=0)
    for y0 in (0.180, 0.198):
        k.ring('y', (0, 0, bz), y0, y0 + 0.004, r - 0.001, r + PR, 'trim', seg=12, hull=False)
    knurl(k, 0.228, 0.246, r, bz, n=4, seg=12)
    RF = (r + 0.0015) * math.cos(D(15))
    for i in range(6):
        with k.at((0, 0, bz), (0, 60 * i, 0)):
            k.box((0, 0.259, RF + PR / 2 - 0.0005), (0.006, 0.008, PR + 0.001), 'ink', skip=('-z',))
    for i in range(6):                                                                         # vent flutes
        with k.at((0, 0, bz), (0, 60 * i + 30, 0)):
            k.box((0, 0.165, r * math.cos(D(15)) + PR / 2 - 0.0005), (0.005, 0.016, PR + 0.001), 'ink', skip=('-z',))
    k.ring('y', (0, 0, bz), 0.209, 0.223, r - 0.001, r + 0.0025, 'steel2', seg=12)
    k.box((0, 0.216, 0.06025), (0.005, 0.008, 0.0285), 'ink', hull=True)                 # front post on the can (on the sight line)
    # ---- folding foregrip on its hinge block, guard, grip
    k.cbox((0, 0.088, -0.008), (0.034, 0.036, 0.008), 'gun2', ch=0.002, axis='y')
    k.pin(-0.0185, 0.0185, 0.088, -0.008, 0.003, color='steel2')
    vgrip(k, 0.088, -0.006, length=0.060, r=0.014)
    trigger_guard(k, rake, front=0.064, depth=-0.046, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.036, top=0.000, bottom=-0.096, ptop=-0.024)
    # ---- wire stock (collapsed): rods in their bushings, latch, butt frame with a ribbed pad
    for s in (-1, 1):
        k.lathe([(-0.150, 0), (-0.150, 0.004), (-0.074, 0.004), (-0.074, 0)], 'steel', 'y', (s * 0.016, 0, 0.012), 6, hull=True)
        k.ring('y', (s * 0.016, 0, 0.012), -0.0845, -0.0755, 0.0040, 0.0068, 'steel2', seg=8, hull=False)
        k.ring('y', (s * 0.016, 0, 0.012), -0.1465, -0.1400, 0.0040, 0.0065, 'steel2', seg=8, hull=False)
        for i in range(4):
            k.box((s * (0.0235 + PR / 2 - 0.0005), -0.1575, 0.028 - i * 0.017), (PR + 0.001, 0.006, 0.005), 'ink', skip=sk(s))
        bolt(k, (s * 0.0215, -0.149, 0.030), (s, 0, 0))
        bolt(k, (s * 0.0215, -0.149, -0.020), (s, 0, 0))
    k.ext_x([(-0.076, 0.004), (-0.090, 0.006), (-0.092, 0.000), (-0.078, -0.004)], -0.006, 0.006, 'gun3', ch=0.001)
    k.ext_x([(-0.144, 0.039), (-0.152, 0.039), (-0.153, -0.031), (-0.146, -0.028)], -0.0215, 0.0215, 'furn', ch=0.002)
    k.ext_x([(-0.152, 0.041), (-0.161, 0.040), (-0.163, -0.035), (-0.153, -0.033)], -0.0235, 0.0235, 'rubber', ch=0.003)
    my, mz = g2w(rake, HAND['cy'], -0.096)
    mk = Kit(pal)
    mag_box(mk, rake, 0.080, -0.062, 0.040, 0.025, plate='gun3', plate_w=0.043, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.004, -0.030)
        mk.box((s * 0.0125, y, z), (0.008, 0.020, 0.036), 'gun3', skip=sk(s))
        bolt(mk, (s * 0.0165, y, z + 0.012), (s, 0, 0), 0.0024)
        bolt(mk, (s * 0.0165, y, z - 0.012), (s, 0, 0), 0.0024)

    # ---- Rare (and up): aiming module, suppressor wrap, magwell funnel, round counter, butt plates
    r3 = Kit(pal)
    laser_box(r3, 0.068, 0.041, s=1, hw=HU, L=0.044, w=0.014, h=0.016, color='gun2')
    r3.ring('y', (0, 0, bz), 0.154, 0.176, r - 0.001, r + 0.003, 'gun2', seg=12)
    RW = (r + 0.003) * math.cos(D(15))
    for i in range(6):
        with r3.at((0, 0, bz), (0, 60 * i + 30, 0)):
            r3.box((0, 0.165, RW + PR / 2 - 0.0005), (0.005, 0.014, PR + 0.001), 'ink', skip=('-z',))
    f, b = HAND['cy'] + HAND['hy'], HAND['cy'] - HAND['hy']
    r3.ext_x(gprof(rake, [(f + 0.003, -0.080), (f + 0.008, -0.0945), (b - 0.008, -0.0945), (b - 0.004, -0.080)]), -0.0245, 0.0245, 'gun3', ch=0.002)
    bolts(r3, 0.0245, [g2w(rake, f - 0.004, -0.088), g2w(rake, b + 0.004, -0.088)])
    r3.cbox((-HU - 0.002, -0.050, 0.043), (0.006, 0.026, 0.008), 'gun2', ch=0.001, hull=False)
    for i in range(4):
        r3.box((-HU - 0.005 - PR / 2 + 0.0005, -0.0575 + i * 0.005, 0.043), (PR + 0.001, 0.003, 0.005), 'emis', skip=sk(-1))
    for s in (-1, 1):
        r3.cbox((s * 0.0235, -0.1485, 0.005), (0.005, 0.010, 0.038), 'gun3', ch=0.0015)

    # ---- Epic (and up): energy cell between the stock rods, conduit to the can, cooling discs, glow rings
    r4 = Kit(pal)
    energy_cell(r4, (0, -0.117, 0.012), L=0.044, r=0.0075)
    r4.cbox((0, -0.117, 0.012), (0.043, 0.008, 0.018), 'gun2', ch=0.002, hull=False)
    conduit(r4, [(0, -0.093, 0.012), (-0.012, -0.085, 0.014), (-0.0215, -0.076, 0.015), (-0.0245, -0.064, 0.015), (-0.0245, 0.020, 0.015), (-0.0245, 0.094, 0.015),
                 (-0.0215, 0.108, 0.024)], r=0.0024, every=2)
    for y0 in (0.139, 0.1445, 0.150):
        r4.ring('y', (0, 0, bz), y0, y0 + 0.0024, r - 0.001, 0.0260, 'steel2', seg=12)
    r4.ring('y', (0, 0, bz), 0.1865, 0.1955, r - 0.001, r + PR, 'emis', seg=12, hull=False)
    r4.ring('y', (0, 0, bz), 0.2515, 0.2545, 0.0210, 0.0220 + PR, 'emis', seg=12, hull=False)
    m4 = Kit(pal)
    for s in (-1, 1):
        y, z = g2w(rake, 0.004, -0.030)
        m4.box((s * (0.0165 + PR / 2 - 0.0005), y, z), (PR + 0.001, 0.004, 0.014), 'emis', skip=sk(s))

    # ---- Legendary: aurora ribbons round the suppressor, crystal crown, star emblems, crystals on the butt
    r5 = Kit(pal)
    for ph, col in ((90, 'emis'), (270, 'trim')):
        pts, ups = [], []
        for i in range(25):
            t = i / 24.0
            a = D(ph) + 2 * math.pi * 1.75 * t
            d = V((math.sin(a), 0.0, math.cos(a)))
            pts.append(((d.x * 0.027, 0.156 + 0.104 * t, bz + d.z * 0.027), 0.009, 0.0028))
            ups.append(tuple(d))
        r5.tube(pts, col, sides=4, up=ups, hull=False, a0=45)

    def shard(p, d, L, rr, col='steel'):
        d = V(d).normalized()
        u = d.orthogonal().normalized()
        r5.lathe([(-0.004, rr), (L * 0.35, rr), (L * 0.7, rr * 0.75), (L, 0)], col, (d, u, d.cross(u)), p, 6, bands=[None, 'emis', None], caps=(False, True))
    for s in (-1, 1):
        for ang, L in ((35, 0.036), (75, 0.029), (115, 0.022)):
            a = D(ang)
            shard((s * math.sin(a) * 0.018, 0.114, bz + math.cos(a) * 0.018), (s * math.sin(a) * 0.86, -0.5, math.cos(a) * 0.86), L, 0.0056)
        shard((s * 0.014, -0.150, 0.036), (s * 0.30, -0.40, 0.86), 0.024, 0.0042)
        shard((s * 0.007, -0.153, 0.036), (s * 0.10, -0.55, 0.83), 0.016, 0.0034)
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(0.0, 0.0030), (0.0030, 0.0030), (0.0055, 0)], 'emis', n, (s * 0.021, -0.087, 0.050), 6, hull=False, caps=(False, True))
    star = []
    for i in range(8):
        a = D(45 * i + 90)
        rr = 0.0105 if i % 2 == 0 else 0.0030
        star.append((-0.044 + rr * math.cos(a), 0.027 + rr * math.sin(a)))
    plate(r5, star, HU + PR, 'trim', t=0.002, ch=0)
    for s in (-1, 1):
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(0.0015, 0.0026), (0.0035, 0.0018), (0.0042, 0)], 'emis', n, (s * (HU + PR), -0.044, 0.027), 6, hull=False, caps=(False, True))
    m5 = Kit(pal)
    y, z = g2w(rake, 0.0, -0.067)
    m5.cbox((0, y, z), (0.046, 0.056, 0.003), 'trim', ch=0, rot=(-rake, 0, 0))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.272, bz), 'eject': (0.03, 0.020, 0.046),
                   'sight': (0, -0.072, sz), 'cls': 'smg', 'fore': (0.088, -0.006),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}


def build_hornet(pal):
    """KV-7 Hornet: precision SMG, round tubular receiver, curved mag, tube red-dot, retractable stock."""
    rake = 16
    k = Kit(pal)
    bz = 0.040
    k.lathe([(-0.096, 0), (-0.096, 0.021), (-0.090, 0.025), (0.126, 0.025), (0.130, 0.021), (0.130, 0)], 'gunmetal', 'y', (0, 0, bz), 10, a0=18)
    k.ext_y(rrect(0.040, 0.034, c=0.004, cy=0.006), -0.080, 0.064, 'gun2', ch0=0.004, ch1=0.004)                     # trigger housing
    k.box((0.0190, 0.030, 0.050), (0.016, 0.050, 0.016), 'ink')                                                   # port
    rail(k, -0.070, 0.070, 0.0625, w=0.022, clear=[(-0.040, 0.020)])
    rz = red_dot(k, -0.010, 0.0625, L=0.056)
    stripe(k, 0.140, 0.212, 0.016, 0.022, 0.0285)
    # cocking tube above the handguard, handle out to the left
    k.lathe([(0.126, 0), (0.126, 0.0075), (0.236, 0.0075), (0.236, 0)], 'gun3', 'y', (0, 0, 0.066), 8, hull=False)
    k.bar((-0.004, 0.214, 0.066), (-0.034, 0.206, 0.072), 0.008, 0.008, 'ink')
    # handguard: wide rounded, vents
    k.ext_y(rrect(0.051, 0.044, ct=0.013, cb=0.010, cy=0.034), 0.124, 0.228, 'gun2', ch0=0.003, ch1=0.005)
    for s in (-1, 1):
        for i in range(3):
            k.box((s * 0.0255, 0.146 + i * 0.026, 0.040), (0.006, 0.016, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    barrel(k, 0.220, 0.258, 0.0085, bz)
    muzzle(k, 0.258, 0.292, 0.0120, bz, ports=1, top_ports=1, rb=0.0055, seg=8)
    k.box((0, 0.250, bz + 0.018), (0.006, 0.010, 0.012), 'ink', hull=True)
    k.ext_x([(0.060, 0.016), (0.104, 0.016), (0.104, -0.020), (0.098, -0.026), (0.062, -0.026), (0.058, -0.016)], -0.0235, 0.0235, 'gun2', ch=0.003)
    trigger_guard(k, rake, front=0.052, depth=-0.046, hook=False, top=-0.006)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=-0.006, ptop=-0.030, grooves=2)
    k.xbar(-0.0235, -0.0200, [(-0.060, -0.002), (-0.040, -0.004), (-0.038, 0.004), (-0.058, 0.006)], 'gun3', ch=0, hull=False)
    # retractable stock: two rails, butt with cheek rest
    for s in (-1, 1):
        k.box((s * 0.015, -0.150, 0.036), (0.008, 0.130, 0.010), 'steel2', hull=True)
    k.ext_x([(-0.206, 0.060), (-0.224, 0.060), (-0.226, -0.030), (-0.208, -0.026)], -0.0225, 0.0225, 'furn', ch=0.003)
    k.box((0, -0.215, -0.024), (0.052, 0.010, 0.010), 'ink')
    k.box((0, -0.190, 0.058), (0.026, 0.040, 0.010), 'gun3')
    mk = Kit(pal)
    mag_box(mk, 0, 0.036, -0.120, 0.040, 0.024, curve=0.036, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.081, -0.026), 'muzzle': (0, 0.294, bz), 'eject': (0.03, 0.030, 0.050),
                   'sight': (0, -0.050, rz), 'cls': 'smg', 'guard': (0, 0.215, 0.034)}
