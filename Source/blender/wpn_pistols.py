"""INKBOLT guns: pistols. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_pip(pal):
    """P-12 Warden: chunky striker-fired polymer service pistol. The slide is three sections so the ejection port is
    a real cut with the barrel hood in it; cocking serrations front and rear, dovetailed three-dot sights, an optic-cut
    cover plate, extractor, polymer frame with an accessory rail, slide stop, takedown lever and mag release.
    Rarity layers: Rare bolts on racking wings, slide armour, a weapon light, a magwell funnel and a round counter on
    the slide's rear; Epic swaps the anti-glare rib for a glowing vented rib and adds an energy cell feeding a coil
    around the crown; Legendary (pearl and rose gold) spreads a three-feather wing along each flank, a rose of petals
    around the muzzle, a pearl in a claw at the back of the slide and a scroll tail under it."""
    rake = 16
    k = Kit(pal)
    HS, HF, ZT = 0.0235, 0.0205, 0.052            # half widths: slide, frame; slide top
    # ---- slide
    full = rrect(0.047, 0.046, ct=0.009, cb=0.003, cy=0.029)
    cut = [(0.0205, 0.006), (HS, 0.009), (HS, 0.034), (0.003, 0.034), (0.003, ZT), (-0.0145, ZT), (-HS, 0.043), (-HS, 0.009), (-0.0205, 0.006)]
    k.ext_y(full, -0.086, 0.000, 'gunmetal', ch0=0.004)
    k.ext_y(cut, 0.000, 0.050, 'gunmetal')
    k.ext_y(full, 0.050, 0.150, 'gunmetal', ch1=0.006)
    k.ext_y([(0.0045, 0.0355), (0.0205, 0.0355), (0.0205, 0.0418), (0.0133, 0.049), (0.0045, 0.049)], 0.0015, 0.0485, 'ink', hull=False)      # port
    k.ext_y([(0.006, 0.037), (0.022, 0.037), (0.022, 0.0424), (0.0139, 0.0505), (0.006, 0.0505)], 0.006, 0.0465, 'steel2', hull=False)        # barrel hood
    k.box((0.010, 0.011, 0.0505 + PR / 2 - 0.0005), (0.005, 0.003, PR + 0.001), 'brass', skip=('-z',))                                     # loaded-chamber indicator
    k.box((0.010, 0.019, 0.0505 + PR / 2 - 0.0005), (0.008, 0.0012, PR + 0.001), 'ink', skip=('-z',))
    k.box((HS + PR / 2 - 0.0005, -0.0125, 0.0385), (PR + 0.001, 0.021, 0.005), 'steel', skip=sk(1))                                         # extractor
    plate(k, [(-0.034, 0.017), (0.094, 0.017), (0.097, 0.020), (0.097, 0.040), (-0.031, 0.040), (-0.034, 0.037)], HS, 'body2', sides=(-1,))
    plate(k, [(-0.034, 0.017), (0.094, 0.017), (0.097, 0.020), (0.097, 0.040), (0.056, 0.040), (0.056, 0.030), (-0.026, 0.030), (-0.026, 0.040),
              (-0.031, 0.040), (-0.034, 0.037)], HS, 'body2', sides=(1,))
    plate(k, rect(-0.034, 0.097, 0.0105, 0.0135), HS, 'trim', ch=0)
    slots(k, HS, -0.082, -0.042, 0.027, 6, h=0.028, fill=0.45, slant=-14)                                                                   # cocking serrations
    slots(k, HS, 0.103, 0.139, 0.027, 5, h=0.026, fill=0.45, slant=-14)
    for s in (-1, 1):                                                                                                                       # relief flats on the top bevels
        with k.at((s * 0.019, 0, 0.0475), (0, s * 45, 0)):
            k.box((0, 0.089, PR / 2 - 0.0005), (0.0065, 0.064, PR + 0.001), 'body2', skip=('-z',))
            k.box((0, -0.028, PR / 2 - 0.0005), (0.0065, 0.046, PR + 0.001), 'body2', skip=('-z',))
    # top: optic-cut cover plate, dovetailed three-dot sights
    k.box((0, -0.031, ZT + PR / 2 - 0.0005), (0.024, 0.042, PR + 0.001), 'body2', skip=('-z',))
    for sx in (-1, 1):
        for yy in (-0.046, -0.016):
            bolt(k, (sx * 0.0075, yy, ZT + PR), (0, 0, 1), 0.0024, 0.0018)
    k.cbox((0, -0.068, 0.0525), (0.030, 0.022, 0.005), 'steel2', ch=0.001, hull=False)
    for s in (-1, 1):
        k.ext_x([(-0.077, 0.0535), (-0.058, 0.0535), (-0.064, 0.0645), (-0.077, 0.0645)], min(s * 0.0042, s * 0.014), max(s * 0.0042, s * 0.014), 'body2', ch=0.0008)
        k.box((s * 0.0091, -0.0775, 0.0600), (0.0034, 0.003, 0.0034), 'paper')
    k.cbox((0, 0.134, 0.0525), (0.018, 0.018, 0.005), 'steel2', ch=0.001, hull=False)
    k.ext_x([(0.1275, 0.0535), (0.142, 0.0535), (0.137, 0.0625), (0.1275, 0.0625)], -0.0032, 0.0032, 'body2', ch=0.0006)
    k.box((0, 0.1270, 0.0595), (0.003, 0.003, 0.003), 'red')
    b3 = Kit(pal)                                                                                                                            # anti-glare rib (Epic replaces it)
    top_slots(b3, ZT, 0.056, 0.122, 11, w=0.022, fill=0.4)
    # rear: slide cover plate with the striker indicator
    k.box((0, -0.0865, 0.027), (0.024, 0.004, 0.030), 'gun3', skip=('+y',))
    bolt(k, (0, -0.0885, 0.034), (0, -1, 0), 0.0034, 0.002, color='steel')
    for zz in (0.0165, 0.0205):
        k.box((0, -0.0885 - PR / 2 + 0.0005, zz), (0.014, PR + 0.001, 0.002), 'ink', skip=('+y',))
    # muzzle: barrel crown, recoil-spring guide
    muzzle(k, 0.143, 0.1615, 0.0115, 0.030, rb=0.006, hull=False)
    k.lathe([(0.146, 0.0030), (0.1515, 0.0030), (0.1515, 0.0016), (0.150, 0.0016), (0.150, 0)], 'steel2', 'y', (0, 0, 0.0150), 6, hull=False,
            bands=[None, None, 'ink', 'ink'], caps=(False, True))
    # ---- polymer frame with the accessory rail
    k.ext_y(rrect(0.041, 0.024, c=0.003, cy=-0.001), -0.074, 0.134, 'gun2', ch1=0.008)
    k.ext_x([(-0.072, 0.009), (-0.086, 0.0045), (-0.084, 0.001), (-0.072, -0.006)], -0.014, 0.014, 'gun2', ch=0.002)                               # tang
    k.box((HF + PR / 2 - 0.0005, 0.030, 0.0042), (PR + 0.001, 0.196, 0.0016), 'ink', skip=sk(1))                                              # frame rail line
    k.box((-HF - PR / 2 + 0.0005, 0.093, 0.0042), (PR + 0.001, 0.070, 0.0016), 'ink', skip=sk(-1))
    k.box((-HF - PR / 2 + 0.0005, -0.044, 0.0042), (PR + 0.001, 0.048, 0.0016), 'ink', skip=sk(-1))
    k.box((0, 0.10725, -0.0105), (HF * 2 + PR * 2, 0.0445, 0.008), 'ink')
    for i in range(4):
        k.box((0, 0.090 + i * 0.0115, -0.0105), (HF * 2 + 0.006, 0.006, 0.011), 'frame2')
    plate(k, rect(0.090, 0.124, -0.0035, 0.0018, c=0.0012), HF, 'frame2')
    # controls: slide stop with its thumb shelf, takedown lever, pins, mag release
    k.xbar(-HF - 0.004, -HF + 0.001, [(0.050, -0.002), (0.052, 0.003), (0.012, 0.0055), (-0.012, 0.0075), (-0.015, 0.0025), (0.010, 0.0005)], 'gun3', ch=0, hull=False)
    k.box((-HF - 0.0048, -0.008, 0.0048), (0.0036, 0.011, 0.0058), 'gun3')
    bolt(k, (-HF - 0.004, 0.046, 0.0008), (-1, 0, 0), 0.0024, 0.0016)
    k.xbar(-HF - 0.0035, -HF + 0.001, [(0.058, -0.0065), (0.071, -0.0065), (0.072, -0.0025), (0.059, -0.0015)], 'steel2', ch=0, hull=False)
    bolt(k, (HF, 0.065, -0.004), (1, 0, 0), 0.0034)
    cross_pin(k, HF, 0.040, -0.0075, r=0.0022)
    cross_pin(k, HF, -0.052, -0.001, r=0.0026)
    k.lathe([(HF - 0.002, 0.0052), (HF + 0.0015, 0.0052), (HF + 0.0015, 0.0040), (HF + 0.004, 0.0040), (HF + 0.004, 0)], 'gun3',
            (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.014, -0.008), 8, hull=False, bands=['ink', 'ink', None, None], caps=(False, True))
    bolt(k, (HF, 0.014, -0.008), (1, 0, 0), 0.0030)
    trigger_guard(k, rake, front=0.084, depth=-0.046)
    trigger(k, rake)
    ty, tz = g2w(rake, TRIG[0], TRIG[1])                                                                                                    # trigger safety blade
    k.ext_x([(ty + 0.0075, tz + 0.008), (ty + 0.0098, tz + 0.008), (ty + 0.0082, tz - 0.003), (ty + 0.0005, tz - 0.0135), (ty - 0.001, tz - 0.012),
             (ty + 0.0062, tz - 0.002)], -0.0012, 0.0012, 'ink', hull=False)
    grip(k, rake, 'pistol')
    my, mz = g2w(rake, HAND['cy'], -0.100)
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, 0.0, 0.040, 0.025, plate='gunmetal', plate_h=0.011, plate_w=0.041)

    # ---- Rare (and up): racking wings, slide armour, weapon light, magwell funnel, round counter
    r3 = Kit(pal)
    f, b = HAND['cy'] + HAND['hy'], HAND['cy'] - HAND['hy']
    r3.ext_x(gprof(rake, [(f + 0.003, -0.082), (f + 0.008, -0.0975), (b - 0.010, -0.0975), (b - 0.006, -0.082)]), -0.0235, 0.0235, 'gun3', ch=0.002)
    bolts(r3, 0.0235, [g2w(rake, f - 0.004, -0.090), g2w(rake, b + 0.004, -0.090)])
    for s in (-1, 1):
        r3.ext_y([(s * HS, 0.020), (s * (HS + 0.009), 0.025), (s * (HS + 0.009), 0.035), (s * HS, 0.040)], -0.074, -0.054, 'gun3', ch0=0.004, ch1=0.0015)
    plate(r3, [(0.058, 0.019), (0.091, 0.019), (0.0945, 0.0225), (0.0945, 0.0375), (0.062, 0.0375), (0.058, 0.0335)], HS + PR, 'gun3', t=0.003, hull=True)
    bolts(r3, HS + PR + 0.003, [(0.063, 0.024), (0.090, 0.033)])
    slots(r3, HS + PR + 0.003, 0.068, 0.088, 0.029, 3, h=0.010, fill=0.4, slant=-14)
    laser_box(r3, 0.1065, -0.002, s=1, hw=HF, L=0.036, w=0.012, h=0.014, color='gun2')
    r3.cbox((0, -0.0905, 0.0185), (0.020, 0.005, 0.010), 'gun2', ch=0.001, hull=False)
    for i in range(4):
        r3.box((-0.006 + i * 0.004, -0.093 - PR / 2 + 0.0005, 0.0185), (0.0026, PR + 0.001, 0.006), 'emis', skip=('+y',))

    # ---- Epic (and up): glowing vented rib, energy cell on the dust cover feeding a coil around the crown
    r4 = Kit(pal)
    r4.cbox((0, 0.089, ZT + 0.00075), (0.020, 0.066, 0.0035), 'gun2', ch=0.0012, axis='y', hull=False)
    r4.box((0, 0.089, 0.0545 + PR / 2 - 0.0005), (0.005, 0.058, PR + 0.001), 'emis', skip=('-z',))
    for sx in (-1, 1):
        top_slots(r4, 0.0545, 0.060, 0.118, 8, w=0.005, fill=0.4, x=sx * 0.0062)
    energy_cell(r4, (-(HF + 0.0095), 0.106, -0.004), L=0.034, r=0.0058)
    r4.cbox((-(HF + 0.001), 0.106, 0.0005), (0.006, 0.022, 0.005), 'gun2', ch=0.001, hull=False)
    conduit(r4, [(-(HF + 0.0095), 0.1235, -0.004), (-0.029, 0.133, 0.000), (-0.0235, 0.149, 0.012), (-0.0165, 0.1545, 0.024)], r=0.0024, every=3)
    r4.ring('y', (0, 0, 0.030), 0.1515, 0.1590, 0.0100, 0.0165, 'gun2', seg=10)
    r4.ring('y', (0, 0, 0.030), 0.1535, 0.1570, 0.0150, 0.0165 + PR, 'emis', seg=10, hull=False)
    r4.ring('y', (0, 0, 0.034), -0.0915, -0.0880, 0.0040, 0.0062, 'emis', seg=8, hull=False)
    for s in (-1, 1):
        r4.box((s * (HS + 0.009 + PR / 2 - 0.0005), -0.063, 0.030), (PR + 0.001, 0.008, 0.004), 'emis', skip=sk(s))
        r4.box((s * (HS + PR + 0.003 + PR / 2 - 0.0005), 0.078, 0.0222), (PR + 0.001, 0.020, 0.0016), 'emis', skip=sk(s))
        r4.box((s * (HF + PR / 2 - 0.0005), -0.030, -0.0088), (PR + 0.001, 0.066, 0.0016), 'emis', skip=sk(s))

    # ---- Legendary: feather wings, the rose at the muzzle, the pearl, gold pinstripes, a scroll tail
    r5 = Kit(pal)
    XW = 0.0315
    feathers = [([(0.140, 0.024), (0.140, 0.0135), (0.070, 0.0135), (0.022, 0.0235), (0.074, 0.0220)], (0.130, 0.0188), (0.046, 0.0207)),
                ([(0.140, 0.034), (0.140, 0.0255), (0.084, 0.0250), (0.046, 0.0360), (0.088, 0.0325)], (0.130, 0.0298), (0.066, 0.0322)),
                ([(0.140, 0.044), (0.140, 0.0355), (0.098, 0.0350), (0.066, 0.0465), (0.100, 0.0430)], (0.130, 0.0397), (0.082, 0.0428))]
    for s in (-1, 1):
        r5.cbox((s * (HS + 0.0065), 0.140, 0.029), (0.013, 0.012, 0.034), 'gun3', ch=0.002)
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(-0.001, 0.0042), (0.0018, 0.0042), (0.0040, 0.0026), (0.0050, 0)], 'emis', n, (s * (HS + 0.013), 0.140, 0.029), 8, hull=False, caps=(False, True))
        xs = s * (XW + 0.0025 + PR / 2 - 0.0005)
        for i, (pts, a, c) in enumerate(feathers):
            r5.ext_x(pts, min(s * XW, s * (XW + 0.0025)), max(s * XW, s * (XW + 0.0025)), 'steel' if i == 1 else 'gun3', ch=0.0006)
            r5.bar((xs, a[0], a[1]), (xs, c[0], c[1]), PR + 0.001, 0.0016, 'trim')
    for i in range(8):
        with r5.at((0, 0.1553, 0.030), (0, 360 * (i + 0.5) / 8, 0)):
            r5.ext_x([(-0.0040, 0.0125), (0.0030, 0.0125), (0.0040, 0.0190), (-0.0050, 0.0290), (-0.0080, 0.0275), (-0.0065, 0.0200)], -0.0032, 0.0032, 'gun3', ch=0)
    r5.ring('y', (0, 0, 0.030), 0.1575, 0.1608, 0.0120, 0.0145, 'trim', seg=10, hull=False)
    r5.lathe([(-0.0875, 0.0080), (-0.0930, 0.0080), (-0.0930, 0.0060), (-0.0950, 0.0048), (-0.0965, 0.0026), (-0.0972, 0)], 'gun3', 'y', (0, 0, 0.034), 8,
             hull=False, bands=[None, None, 'emis', 'emis', 'emis'], caps=(False, True), a0=0)
    plate(r5, rect(-0.034, 0.097, 0.0405, 0.0420), HS, 'trim', ch=0, sides=(-1,))
    plate(r5, rect(-0.034, -0.024, 0.0405, 0.0420), HS, 'trim', ch=0, sides=(1,))
    plate(r5, rect(0.056, 0.097, 0.0405, 0.0420), HS, 'trim', ch=0, sides=(1,))
    for r0, r1, col in ((0.0095, 0.0115, 'trim'), (0.0030, 0.0060, 'emis')):
        r5.lathe([(ZT + PR - 0.001, r0), (ZT + PR - 0.001, r1), (ZT + PR * 2, r1), (ZT + PR * 2, r0)], col, 'z', (0, -0.031, 0), 4, hull=False, closed=True, a0=0, sc=(0.62, 1.0))
    r5.ext_x([(-0.070, 0.003), (-0.088, 0.004), (-0.096, -0.002), (-0.095, -0.010), (-0.088, -0.014), (-0.082, -0.010), (-0.086, -0.006), (-0.085, -0.002),
              (-0.070, -0.006)], -0.006, 0.006, 'gun3', ch=0.0015)
    m5 = Kit(pal)
    y, z = g2w(rake, 0.0, -0.0045)
    m5.cbox((0, y, z), (0.047, 0.056, 0.003), 'trim', ch=0, rot=(-rake, 0, 0))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.164, 0.030), 'eject': (0.03, 0.025, 0.048),
                   'sight': (0, -0.090, 0.062), 'cls': 'pistol',
                   'layers': {'123': b3, '345': r3, '45': r4, '5': r5}, 'mag_layers': {'5': m5}}


def build_handcannon(pal):
    """R-50 Ironjaw: big six-shot revolver. Long squared barrel under a ventilated rib, a full underlug with a window
    on the ejector rod, crane and yoke, cylinder latch, side plate with its screws, exposed hammer in its slot, ramp
    front sight with a red insert and an adjustable rear sight on a leaf. The fluted cylinder (stop notches, case rims
    at the back) is the Mag part on the bore axis.
    Rarity layers: Rare bolts strike plates on the barrel, a brake collar, an aiming module on the lug, a six-pip
    counter and a target hammer spur; Epic winds glowing coils on the ejector rod, lights the rib vents, adds an
    energy cell, cooling fins and lit flutes; Legendary (Wyrmforged) turns the barrel into the wyrm: fanged jaws round
    the muzzle with a burning eye, the body coiling back along the barrel."""
    rake = 20
    k = Kit(pal)
    ZA = 0.032                  # cylinder axis = bore axis = barrel centre height
    BE = 0.290                  # barrel end (the muzzle device stands a little past it)
    HFR, HY, HB, HL = 0.0215, 0.017, 0.013, 0.010          # half widths: rear frame, yoke, barrel, underlug
    # ---- frame: rear frame, top strap, front yoke, bottom strap (the sides stay open: the cylinder shows through)
    k.ext_x([(-0.034, -0.008), (0.0, -0.008), (0.0, 0.060), (-0.020, 0.060), (-0.034, 0.040)], -HFR, HFR, 'gunmetal', ch=0.003)
    k.box((0, 0.0245, 0.0562), (0.022, 0.048, 0.0076), 'gunmetal', hull=True)
    k.ext_x([(0.049, -0.008), (0.078, -0.008), (0.078, 0.060), (0.049, 0.060)], -HY, HY, 'gunmetal', ch=0.003)
    k.box((0, 0.025, 0.001), (0.025, 0.046, 0.010), 'gunmetal', hull=True)
    # right: side plate with its screws; left: cylinder latch, pins
    plate(k, [(-0.029, -0.003), (-0.005, -0.003), (-0.005, 0.050), (-0.010, 0.055), (-0.018, 0.055), (-0.0295, 0.038)], HFR, 'body2', sides=(1,))
    bolts(k, HFR + PR, [(-0.025, 0.002), (-0.009, 0.002), (-0.012, 0.049)], sides=(1,), r=0.0028)
    k.cbox((-HFR - 0.0025, -0.016, 0.034), (0.007, 0.015, 0.009), 'gun3', ch=0.0015, hull=False)
    for i in range(3):
        k.box((-HFR - 0.006 - PR / 2 + 0.0005, -0.020 + i * 0.004, 0.034), (PR + 0.001, 0.0018, 0.006), 'ink', skip=sk(-1))
    for (y, z, r) in ((-0.025, 0.045, 0.0030), (-0.024, 0.006, 0.0026), (-0.008, 0.006, 0.0026)):
        bolt(k, (-HFR, y, z), (-1, 0, 0), r)
    # crane on the yoke (left), yoke plates and the crane pin
    plate(k, [(0.052, -0.005), (0.075, -0.005), (0.075, 0.016), (0.064, 0.016), (0.052, 0.004)], HY, 'body2', sides=(-1,))
    bolt(k, (-HY - PR, 0.066, 0.004), (-1, 0, 0), 0.0034)
    bolt(k, (HY, 0.066, 0.004), (1, 0, 0), 0.0030)
    plate(k, rect(0.053, 0.074, 0.024, 0.054, c=0.002), HY, 'body2')
    bolts(k, HY + PR, [(0.0635, 0.048)], r=0.0026)
    # ---- barrel: collar, squared barrel with side panels, ports, ventilated rib
    k.cbox((0, 0.083, ZA), (0.030, 0.014, 0.047), 'body2', ch=0.002, axis='y')
    k.ext_y(rrect(0.026, 0.044, ct=0.005, cb=0.003, cy=ZA, seg=1), 0.074, BE, 'gunmetal', ch1=0.005)
    plate(k, [(0.096, 0.020), (0.268, 0.020), (0.274, 0.026), (0.274, 0.046), (0.096, 0.046)], HB, 'body2')
    hazard(k, HB + PR, 0.104, 0.134, 0.0365, 0.0425, n=4)
    slots(k, HB + PR, 0.236, 0.262, 0.040, 3, h=0.009, fill=0.4, slant=-20)                                  # barrel ports
    k.cbox((0, 0.172, 0.0635), (0.010, 0.186, 0.005), 'gun3', ch=0.001)                                         # rib
    top_slots(k, 0.066, 0.104, 0.254, 22, w=0.007, fill=0.4)
    for i in range(7):
        k.box((0, 0.092 + i * 0.028, 0.0570), (0.006, 0.008, 0.008), 'gun3', hull=False)                         # rib posts (vents between)
    muzzle(k, BE - 0.008, BE + 0.014, 0.0105, ZA, rb=0.0055, hull=False, seg=8)
    # ---- full underlug with the ejector-rod window
    lug = [(0.072, 0.012), (0.094, 0.012), (0.094, -0.009), (0.150, -0.004), (0.150, 0.012), (BE - 0.004, 0.012), (BE - 0.004, 0.002),
           (0.200, -0.004), (0.100, -0.014), (0.072, -0.014)]
    k.ext_x(lug, -HL, HL, 'gun3', ch=0.0015)
    k.lathe([(0.080, 0.0036), (0.136, 0.0036), (0.136, 0.0052), (0.153, 0.0052)], 'steel', 'y', (0, 0, 0.004), 8, hull=False, caps=(False, False))
    knurl(k, 0.137, 0.149, 0.0052, 0.004, n=3, seg=8)
    plate(k, rect(0.208, BE - 0.010, 0.0050, 0.0070), HL, 'trim', ch=0)
    k.lathe([(BE - 0.006, 0.0028), (BE - 0.002, 0.0028), (BE - 0.002, 0)], 'steel', 'y', (0, 0, 0.007), 6, hull=False, caps=(False, True))
    # ---- sights: ramp front with a red insert, adjustable rear on its leaf
    k.cbox((0, 0.272, 0.0595), (0.014, 0.024, 0.017), 'gun3', ch=0.0015)
    k.ext_x([(0.258, 0.0675), (0.282, 0.0675), (0.280, 0.080), (0.270, 0.080), (0.270, 0.074)], -0.003, 0.003, 'body2', ch=0)
    k.box((0, 0.2695, 0.0762), (0.0028, 0.003, 0.0045), 'red')
    k.box((0, 0.0165, 0.0610), (0.012, 0.053, 0.003), 'body2', skip=('-z',))                                     # sight leaf on the top strap
    bolt(k, (0, 0.036, 0.0625), (0, 0, 1), 0.0028)
    k.cbox((0, -0.012, 0.0640), (0.026, 0.016, 0.009), 'gun3', ch=0.0015)
    for s in (-1, 1):
        k.box((s * 0.0085, -0.017, 0.0745), (0.009, 0.004, 0.012), 'body2', hull=True)
        k.box((s * 0.0075, -0.0195, 0.0765), (0.003, 0.003, 0.003), 'paper')
    k.box((0, -0.017, 0.0705), (0.008, 0.004, 0.004), 'body2')
    bolt(k, (0, -0.009, 0.0685), (0, 0, 1), 0.0030, color='steel')                                               # elevation, windage
    bolt(k, (0.013, -0.012, 0.064), (1, 0, 0), 0.0032, color='steel')
    bolt(k, (-0.013, -0.012, 0.064), (-1, 0, 0), 0.0022)
    # ---- hammer in its slot, chequered spur
    k.box((0, -0.027, 0.050), (0.0115, 0.006, 0.022), 'ink', rot=(-35, 0, 0))
    k.xbar(-0.0045, 0.0045, [(-0.022, 0.040), (-0.030, 0.058), (-0.040, 0.064), (-0.050, 0.060), (-0.060, 0.050), (-0.064, 0.043),
                             (-0.052, 0.046), (-0.040, 0.044), (-0.028, 0.034)], 'steel2', ch=0)
    for j in range(3):
        k.box((0, -0.0523 - j * 0.003, 0.0583 - j * 0.003), (0.012, 0.0022, 0.0024), 'ink', rot=(45, 0, 0))
    k.box((0, -0.034 - PR / 2 + 0.0005, 0.017), (0.016, PR + 0.001, 0.034), 'body2', skip=('+y',))                                # back-strap plate
    for j in range(5):
        k.box((0, -0.034 - PR * 1.5 + 0.0005, 0.005 + j * 0.006), (0.011, PR + 0.001, 0.002), 'ink', skip=('+y',))
    trigger_guard(k, rake, front=0.060, depth=-0.046, hook=False, top=-0.006)
    trigger(k, rake, ext=0.006)
    grip(k, rake, 'flare', w=0.036, top=-0.004, ptop=-0.026, grooves=3, chequer=3)
    my, mz = g2w(rake, -0.004, -0.015)                                                                           # grip medallion
    for s in (-1, 1):
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        k.lathe([(-0.001, 0.0058), (0.0032, 0.0058), (0.0032, 0.0042), (0.0018, 0.0042), (0.0018, 0)], 'gun3', n, (s * 0.018, my, mz), 8, hull=False,
                bands=[None, None, 'ink', 'trim'], caps=(False, True))
    # ---- cylinder (the Mag): full rear band with the stop notches, six flutes, case rims, chamber mouths
    mk = Kit(pal)
    R = 0.0215
    flute, band = [], []
    for i in range(6):
        for da, rr in ((-18, R), (18, R), (30, R - 0.008)):
            a = D(60 * i + da)
            flute.append((rr * math.cos(a), rr * math.sin(a)))
            band.append((R * math.cos(a), R * math.sin(a)))
    mk.ext_y(band, -0.022, -0.006, 'steel2')
    mk.ext_y(flute, -0.006, 0.022, 'steel2')
    RL = R * math.cos(D(18))
    for i in range(6):
        with mk.at((0, 0, 0), (0, -60 * i, 0)):
            mk.box((RL + PR / 2 - 0.0005, -0.016, 0.004), (PR + 0.001, 0.006, 0.004), 'ink', skip=('-x',))
        a = D(60 * i)
        c = (0.0125 * math.cos(a), 0, 0.0125 * math.sin(a))
        mk.lathe([(-0.0245, 0), (-0.0245, 0.0052), (-0.0215, 0.0052)], 'brass', 'y', c, 6, hull=False, caps=(False, False))
        mk.lathe([(0.0215, 0.0045), (0.0235, 0.0045), (0.0235, 0)], 'ink', 'y', c, 6, hull=False, caps=(False, True))
    mk.lathe([(-0.0245, 0), (-0.0245, 0.0055), (-0.0215, 0.0055)], 'steel', 'y', (0, 0, 0), 6, hull=False, caps=(False, False))

    # ---- Rare (and up): barrel strike plates, brake collar, aiming module with its cable, six-pip counter, target spur
    r3 = Kit(pal)
    plate(r3, [(0.100, 0.024), (0.136, 0.024), (0.140, 0.028), (0.140, 0.044), (0.100, 0.044)], HB + PR, 'gun3', t=0.003, hull=True)
    bolts(r3, HB + PR + 0.003, [(0.105, 0.029), (0.105, 0.039), (0.134, 0.039)])
    slots(r3, HB + PR + 0.003, 0.112, 0.130, 0.034, 3, h=0.011, fill=0.4, slant=20)
    r3.ring('y', (0, 0, ZA), BE + 0.0015, BE + 0.0105, 0.0095, 0.0150, 'gun3', seg=10)
    for s in (-1, 1):
        r3.box((s * 0.0148, BE + 0.006, ZA), (0.004, 0.004, 0.009), 'ink', skip=sk(s))
    laser_box(r3, 0.178, 0.003, s=1, hw=HL, L=0.044, w=0.014, h=0.016, color='gun2')
    cable(r3, [(0.0165, 0.157, 0.003), (0.0125, 0.150, -0.004), (0.0118, 0.126, -0.0085), (0.0118, 0.098, -0.0115), (0.0118, 0.084, -0.0115)], r=0.0022, clamps=(3,))
    r3.cbox((-HFR - 0.002, -0.0115, 0.0495), (0.006, 0.018, 0.009), 'gun2', ch=0.001, hull=False)
    for i in range(6):
        r3.box((-HFR - 0.005 - PR / 2 + 0.0005, -0.0178 + i * 0.0025, 0.0495), (PR + 0.001, 0.0015, 0.005), 'emis', skip=sk(-1))
    r3.cbox((0, -0.0557, 0.0557), (0.016, 0.016, 0.007), 'gun3', ch=0.0015, rot=(45, 0, 0))
    plate(r3, rect(0.054, 0.073, 0.000, 0.018, c=0.002), HY, 'gun3', t=0.0045, sides=(1,), hull=True)

    # ---- Epic (and up): coils on the ejector rod, lit rib vents, energy cell and conduits, cooling fins, lit flutes
    r4 = Kit(pal)
    for i in range(4):
        r4.ring('y', (0, 0, 0.004), 0.098 + i * 0.010, 0.103 + i * 0.010, 0.0036, 0.0062, 'emis', seg=8, hull=False)
    r4.lathe([(0.092, 0), (0.092, 0.002), (0.262, 0.002), (0.262, 0)], 'emis', 'y', (0, 0, 0.0572), 6, hull=False)
    for s in (-1, 1):
        fins(r4, (s * (HB + PR + 0.002), 0.247, 0.027), (0.006, 0.032, 0.010), 6, axis='y', color='steel2')
    r4.ring('y', (0, 0, ZA), BE + 0.0095, BE + 0.0120, 0.0112, 0.0136, 'emis', seg=10, hull=False)
    energy_cell(r4, (-(HL + 0.0085), 0.178, 0.001), L=0.040, r=0.006)
    conduit(r4, [(-0.0185, 0.158, 0.001), (-0.0165, 0.150, 0.002), (-0.011, 0.144, 0.004), (-0.0055, 0.141, 0.004)], r=0.0022, every=3)
    conduit(r4, [(-0.0185, 0.198, 0.001), (-0.0158, 0.210, 0.0145), (-0.0158, 0.246, 0.0145), (-0.0158, 0.280, 0.0145), (-0.0125, 0.293, 0.0245)], r=0.0022, every=2)
    m4 = Kit(pal)
    for i in range(6):
        with m4.at((0, 0, 0), (0, -(60 * i + 30), 0)):
            m4.box((R - 0.0072, 0.008, 0), (0.002, 0.022, 0.0026), 'emis')

    # ---- Legendary: the wyrm. Eye at the muzzle, the body along the barrel
    r5 = Kit(pal)
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.0095, s * (HB + 0.005)))
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(-0.001, 0.0048), (0.0018, 0.0048), (0.0018, 0.0034), (0.0030, 0.0022), (0.0036, 0)], 'steel', n, (s * (HB + 0.005), 0.254, 0.0455), 6, hull=False,
                 bands=[None, None, 'emis', 'emis'], caps=(False, True))
        xb =s * (HB + PR + 0.0035)                                                                                  # body
        body = [(0.240, 0.046, 0.0075), (0.224, 0.0405, 0.0075), (0.206, 0.0310, 0.0072), (0.188, 0.0265, 0.0068), (0.170, 0.0310, 0.0062),
                (0.156, 0.0385, 0.0052), (0.148, 0.0415, 0.0036), (0.143, 0.0400, 0.0)]
        r5.tube([((xb, y, z), w, w) for (y, z, w) in body], 'gun3', sides=6)
        for j in range(1, 6):                                                                                        # dorsal scales
            (y, z, w), (y2, z2, _) = body[j], body[j - 1]
            r5.bar((xb + s * 0.0045, y, z), (xb + s * 0.0045, (y + y2) / 2, (z + z2) / 2), 0.004, 0.0022, 'trim')
        r5.lathe([(-0.001, 0.0070), (PR, 0.0070), (PR, 0.0052), (PR * 2, 0.0040), (PR * 2 + 0.0008, 0)], 'gun3', n, (s * (HY + PR), 0.0635, 0.036), 4, hull=False,
                 bands=[None, None, 'emis', 'emis'], caps=(False, True), a0=0, sc=(0.5, 1.0))
    m5 = Kit(pal)
    for i in range(6):
        with m5.at((0, 0, 0), (0, -60 * i, 0)):
            m5.box((RL + PR / 2 - 0.0005, 0.008, 0), (PR + 0.001, 0.020, 0.003), 'trim', skip=('-x',))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.025, ZA), 'muzzle': (0, BE + 0.016, ZA), 'eject': (-0.03, 0.025, ZA),
                   'sight': (0, -0.012, 0.078), 'cls': 'pistol', 'pivot': (-0.024, 0.050, ZA),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}


def build_twintap(pal):
    """P-16 Twinfire: stacked twin-bore burst pistol built like a race gun. The slide is a frame of rails and slanted
    pillars: both barrels show through the lightening cuts on the sides and the top slot; a real ejection port with the
    barrel hood; a three-baffle compensator with open ports; optic plate under the mini reflex; ring hammer over an
    upswept beavertail, ambi safeties, thumb rest, flared magwell, extended magazine with a sleeve.
    Rarity layers: Rare adds a slide racker, a weapon light, an ambi thumb rest, compensator clamps, magwell weights and
    a round counter; Epic rings both barrels with glowing bands, fills the compensator ports with plasma and runs
    conduits to it; Legendary (oil-slick chrome) adds compensator fins and a gem in the hammer ring."""
    rake = 18
    k = Kit(pal)
    HS, HF, ZT = 0.023, 0.020, 0.064              # half widths: slide, frame; slide top
    ZB = (0.020, 0.048)                           # the two bores
    Y0, Y1 = 0.022, 0.106                         # the skeleton section of the slide
    # ---- slide: rear block, port section, skeleton section, front block
    full = rrect(0.046, 0.060, ct=0.011, cb=0.003, cy=0.034)
    cut = [(0.020, 0.004), (HS, 0.007), (HS, 0.040), (0.003, 0.040), (0.003, ZT), (-0.012, ZT), (-HS, 0.053), (-HS, 0.007), (-0.020, 0.004)]
    k.ext_y(full, -0.084, -0.030, 'gunmetal', ch0=0.004)
    k.ext_y(cut, -0.030, 0.016, 'gunmetal')
    k.ext_y(full, 0.016, Y0, 'gunmetal')
    k.ext_y([(0.020, 0.004), (HS, 0.007), (HS, 0.0115), (-HS, 0.0115), (-HS, 0.007), (-0.020, 0.004)], Y0, Y1, 'gunmetal')              # floor
    for s in (-1, 1):
        k.ext_y([(s * 0.006, 0.052), (s * HS, 0.052), (s * HS, 0.053), (s * 0.012, ZT), (s * 0.006, ZT)], Y0, Y1, 'gunmetal')           # roof rails
    k.box((0, (Y0 + Y1) / 2, 0.034), (0.043, Y1 - Y0, 0.011), 'body2')                                                                   # spine between the barrels
    for y0 in (0.050, 0.078):
        k.ext_x([(y0 + 0.005, 0.0115), (y0 + 0.011, 0.0115), (y0 + 0.001, 0.052), (y0 - 0.005, 0.052)], -HS, HS, 'gunmetal')             # slanted pillars
    k.ext_y(full, Y1, 0.124, 'gunmetal', ch1=0.003)
    for zz in ZB:
        k.lathe([(0.018, 0.009), (0.112, 0.009)], 'steel', 'y', (0, 0, zz), 10, hull=False, caps=(False, False))                       # barrels
    plate(k, rect(0.024, 0.120, 0.0325, 0.0355), 0.0215, 'trim', t=0.003, ch=0)
    k.ext_y([(0.0045, 0.0415), (0.020, 0.0415), (0.020, 0.0518), (0.0108, 0.061), (0.0045, 0.061)], -0.0285, 0.0145, 'ink', hull=False)   # port
    k.ext_y([(0.006, 0.043), (0.0215, 0.043), (0.0215, 0.0524), (0.0114, 0.0625), (0.006, 0.0625)], -0.024, 0.0125, 'steel2', hull=False)  # barrel hood
    k.box((0.009, -0.019, 0.0625 + PR / 2 - 0.0005), (0.006, 0.0012, PR + 0.001), 'ink', skip=('-z',))
    k.box((HS + PR / 2 - 0.0005, -0.040, 0.046), (PR + 0.001, 0.016, 0.005), 'steel', skip=sk(1))                                      # extractor
    slots(k, HS, -0.080, -0.052, 0.029, 4, h=0.040, fill=0.45, slant=-12)                                                                # cocking serrations
    plate(k, rect(-0.046, 0.018, 0.010, 0.050, c=0.003), HS, 'body2', sides=(-1,))
    plate(k, rect(-0.046, 0.018, 0.010, 0.0375, c=0.002), HS, 'body2', sides=(1,))
    # top: optic plate with its screws under the mini reflex, backup post
    top_slots(k, ZT, -0.026, 0.012, 6, w=0.009, fill=0.4, x=-0.006)
    k.box((0, -0.0555, ZT + PR / 2 - 0.0005), (0.022, 0.047, PR + 0.001), 'body2', skip=('-z',))
    for sx in (-1, 1):
        for yy in (-0.076, -0.0345):
            bolt(k, (sx * 0.006, yy, ZT + PR), (0, 0, 1), 0.0022, 0.0018)
    hz = hood_sight(k, -0.070, -0.040, 0.064, w=0.030, h=0.022, t=0.0045)
    bolt(k, (0.013, -0.055, 0.068), (1, 0, 0), 0.0026, color='steel')
    k.cbox((0, 0.114, 0.0645), (0.016, 0.012, 0.004), 'steel2', ch=0.001, hull=False)
    k.ext_x([(0.1095, 0.0655), (0.1185, 0.0655), (0.116, 0.0725), (0.1095, 0.0725)], -0.003, 0.003, 'body2', ch=0)
    # rear: firing-pin stop plate with both pins, ring hammer
    k.box((0, -0.0845, 0.036), (0.020, 0.004, 0.044), 'gun3', skip=('+y',))
    for zz in (0.019, 0.048):
        bolt(k, (0, -0.0865, zz), (0, -1, 0), 0.0030, 0.002, color='steel')
    k.ring('x', (0, -0.0935, 0.019), -0.004, 0.004, 0.0040, 0.0085, 'steel2', seg=8)
    # ---- compensator: three baffles on a bottom bar, both muzzles run through the open ports
    for (a, b, c) in ((0.123, 0.1335, 'y'), (0.1375, 0.1475, 'y'), (0.1515, 0.163, None)):
        k.cbox((0, (a + b) / 2, 0.034), (0.050, b - a, 0.058), 'gun3', ch=0.004, axis=c)
    k.box((0, 0.143, 0.0105), (0.044, 0.034, 0.006), 'acc2')
    for zz in ZB:
        muzzle(k, 0.116, 0.176, 0.0085, zz, rb=0.0048, hull=False, seg=8)
    bolts(k, 0.025, [(0.128, 0.020), (0.128, 0.048)], r=0.0024)
    # ---- frame: dust cover with the rail, controls, beavertail, magwell
    k.ext_y(rrect(0.040, 0.024, c=0.003, cy=-0.004), -0.070, 0.118, 'gun2', ch1=0.010)
    k.box((0, 0.099, -0.0135), (HF * 2 + PR * 2, 0.034, 0.008), 'ink')
    for i in range(3):
        k.box((0, 0.088 + i * 0.011, -0.0135), (HF * 2 + 0.006, 0.006, 0.011), 'frame2')
    plate(k, rect(0.030, 0.112, -0.006, 0.002, c=0.0015), HF, 'frame2', sides=(1,))
    plate(k, rect(0.074, 0.112, -0.006, 0.002, c=0.0015), HF, 'frame2', sides=(-1,))
    k.xbar(-HF - 0.004, -HF + 0.001, [(0.000, -0.006), (0.038, -0.006), (0.042, -0.001), (0.004, 0.001)], 'gun3', ch=0, hull=False)     # slide stop
    bolt(k, (-HF - 0.004, 0.036, -0.0035), (-1, 0, 0), 0.0022, 0.0016)
    bolt(k, (HF, 0.036, -0.004), (1, 0, 0), 0.0030)
    bolt(k, (HF, 0.050, -0.009), (1, 0, 0), 0.0024)
    k.ext_y([(-0.019, -0.012), (-0.019, 0.0005), (-0.031, 0.0005), (-0.031, -0.002), (-0.022, -0.012)], 0.047, 0.069, 'gun3', ch0=0.0015, ch1=0.0015)   # thumb rest
    top_slots(k, 0.0005, 0.049, 0.067, 4, w=0.007, fill=0.4, x=-0.0265)
    for s in (-1, 1):                                                                                                                  # ambi safeties, pins
        x0, x1 = sorted((s * (HF - 0.001), s * (HF + 0.0035)))
        k.ext_x([(-0.062, 0.000), (-0.034, -0.002), (-0.030, 0.003), (-0.036, 0.006), (-0.060, 0.006)], x0, x1, 'gun3', ch=0.0008, hull=False)
        bolt(k, (s * (HF + 0.0035), -0.056, 0.003), (s, 0, 0), 0.0022, 0.0016)
    cross_pin(k, HF, -0.046, -0.009, r=0.0022)
    cross_pin(k, HF, -0.058, -0.009, r=0.0022)
    k.lathe([(HF - 0.002, 0.0050), (HF + 0.0015, 0.0050), (HF + 0.0015, 0.0038), (HF + 0.004, 0.0038), (HF + 0.004, 0)], 'gun3',
            (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.012, -0.010), 8, hull=False, bands=['ink', 'ink', None, None], caps=(False, True))
    k.ext_x([(-0.062, 0.006), (-0.062, -0.008), (-0.076, -0.004), (-0.092, 0.006), (-0.096, 0.013), (-0.088, 0.0115), (-0.078, 0.006)], -0.011, 0.011, 'gun2', ch=0.002)
    trigger_guard(k, rake, front=0.080, depth=-0.048, hook=True, top=-0.010)
    trigger(k, rake, color='gun3')
    grip(k, rake, 'pistol', w=0.034, top=0.004, ptop=-0.026, grooves=3)
    f, b = HAND['cy'] + HAND['hy'], HAND['cy'] - HAND['hy']
    k.ext_x(gprof(rake, [(f + 0.003, -0.084), (f + 0.009, -0.0985), (b - 0.011, -0.0985), (b - 0.006, -0.084)]), -0.0235, 0.0235, 'gun3', ch=0.002)   # magwell
    bolts(k, 0.0235, [g2w(rake, f - 0.004, -0.091), g2w(rake, b + 0.004, -0.091)])
    my, mz = g2w(rake, HAND['cy'], -0.100)
    # ---- extended magazine: sleeve blocks, grooved base pad
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, -0.030, 0.040, 0.025, plate='gun3', plate_h=0.012, plate_w=0.041, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.0, -0.016)
        mk.box((s * 0.0125, y, z), (0.008, 0.026, 0.020), 'gun2', skip=sk(s))
        bolt(mk, (s * 0.0165, y, z + 0.004), (s, 0, 0), 0.0024)
        for j in range(3):
            y, z = g2w(rake, -0.012 + j * 0.012, -0.036)
            mk.box((s * (0.0205 + PR / 2 - 0.0005), y, z), (PR + 0.001, 0.0035, 0.007), 'ink', skip=sk(s))

    # ---- Rare (and up): slide racker, weapon light, ambi thumb rest, compensator clamps, magwell weights, counter
    r3 = Kit(pal)
    r3.cbox((HS + 0.007, -0.078, 0.046), (0.016, 0.008, 0.010), 'gun3', ch=0.002)
    laser_box(r3, 0.099, -0.00175, s=1, hw=HF, L=0.025, w=0.012, h=0.0135, color='gun2')
    r3.ext_y([(0.019, -0.012), (0.019, 0.0005), (0.029, 0.0005), (0.029, -0.002), (0.022, -0.012)], 0.049, 0.067, 'gun3', ch0=0.0015, ch1=0.0015)
    wy, wz = g2w(rake, HAND['cy'], -0.091)
    for s in (-1, 1):
        r3.cbox((s * 0.026, 0.1355, 0.034), (0.005, 0.020, 0.016), 'gun2', ch=0.0012)
        bolt(r3, (s * 0.0285, 0.1295, 0.034), (s, 0, 0), 0.0024)
        bolt(r3, (s * 0.0285, 0.1415, 0.034), (s, 0, 0), 0.0024)
        r3.cbox((s * 0.0245, wy, wz), (0.006, 0.028, 0.010), 'steel2', ch=0.0015, rot=(-rake, 0, 0))
    r3.cbox((-HS - 0.002, -0.026, 0.0445), (0.006, 0.026, 0.008), 'gun2', ch=0.001, hull=False)
    for i in range(4):
        r3.box((-HS - 0.005 - PR / 2 + 0.0005, -0.0335 + i * 0.005, 0.0445), (PR + 0.001, 0.003, 0.005), 'emis', skip=sk(-1))

    # ---- Epic (and up): glowing bands on both barrels, plasma in the compensator ports, conduits, lit magazine
    r4 = Kit(pal)
    for zz in ZB:
        for yc in (0.034, 0.064, 0.094):
            r4.lathe([(yc - 0.005, 0.0090), (yc - 0.005, 0.0108), (yc + 0.005, 0.0108), (yc + 0.005, 0.0090)], 'emis', 'y', (0, 0, zz), 8, hull=False, closed=True, a0=0)
    for yc in (0.1355, 0.1495):
        r4.box((0, yc, 0.036), (0.040, 0.0015, 0.044), 'emis')
    for s in (-1, 1):
        conduit(r4, [(s * 0.0252, 0.028, 0.0088), (s * 0.0252, 0.066, 0.0088), (s * 0.0252, 0.112, 0.0088), (s * 0.0272, 0.127, 0.0125)], r=0.0022)
    m4 = Kit(pal)
    for s in (-1, 1):
        y, z = g2w(rake, 0.0, -0.016)
        m4.box((s * (0.0165 + PR / 2 - 0.0005), y, z - 0.004), (PR + 0.001, 0.018, 0.003), 'emis', skip=sk(s))

    # ---- Legendary: compensator fins, the hammer gem, gold trim
    r5 = Kit(pal)
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.0150, s * 0.0180))                                                                                      # compensator fins
        r5.ext_x([(0.125, 0.061), (0.162, 0.061), (0.151, 0.0735), (0.133, 0.0690)], x0, x1, 'gun3', ch=0.0008)
        r5.bar((s * 0.0165, 0.134, 0.0705), (s * 0.0165, 0.150, 0.0745), 0.0045, 0.0016, 'trim')
        with r5.at((s * 0.0175, 0, 0.0585), (0, s * 45, 0)):
            r5.box((0, 0.064, PR / 2 - 0.0005), (0.003, 0.080, PR + 0.001), 'trim', skip=('-z',))
    r5.lathe([(-0.0034, 0), (0, 0.0034), (0.0034, 0)], 'emis', 'z', (0, -0.0935, 0.019), 4, hull=False)
    m5 = Kit(pal)
    y, z = g2w(rake, 0.0, -0.0345)
    m5.cbox((0, y, z), (0.047, 0.056, 0.003), 'trim', ch=0, rot=(-rake, 0, 0))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.178, 0.034), 'eject': (0.03, -0.005, 0.060),
                   'sight': (0, -0.090, hz), 'cls': 'pistol',
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}
