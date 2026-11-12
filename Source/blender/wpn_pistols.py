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
    stencil(k, 'P-12', HS + PR, 0.012, 0.0255, cap=0.011, sides=(-1,))
    stencil(k, 'WARDEN  9X19', HS + PR, 0.012, 0.0195, cap=0.004, sides=(-1,), font='cond')
    stencil(k, 'WARDEN', HS + PR, 0.014, 0.0205, cap=0.007, sides=(1,))
    stencil(k, 'IB ARMS', HS + PR, 0.076, 0.0215, cap=0.0045, sides=(1,), font='cond')
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
    stencil(k, 'WX-4471', HF + PR, 0.107, -0.0024, cap=0.003, sides=(1,), font='cond')
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
    """R-50 Ironjaw: classic six-shot revolver. Long barrel with a slotted vent rib, ejector-rod shroud on a long underlug,
    open cylinder window (the fluted six-chamber cylinder is the Mag, on the bore axis), exposed hammer with spur,
    two sight rings, grip frame and trigger guard. Palette cells are the ones the gun always used."""
    rake = 20
    k = Kit(pal)
    ZA = 0.032                  # cylinder axis = bore axis = barrel centre height
    BE = 0.290                  # barrel end (the muzzle device stands a little past it)
    # frame: rear frame (hammer block, grip frame), front yoke at the breech, top and bottom straps; the sides between
    # them stay open so the cylinder shows through the window
    k.ext_x([(-0.034, -0.008), (0.0, -0.008), (0.0, 0.060), (-0.020, 0.060), (-0.034, 0.040)], -0.0215, 0.0215, 'gunmetal', ch=0.003)
    k.box((0, 0.0245, 0.0562), (0.022, 0.048, 0.0076), 'gunmetal', hull=True)                # top strap over the cylinder
    k.ext_x([(0.049, -0.008), (0.078, -0.008), (0.078, 0.060), (0.049, 0.060)], -0.017, 0.017, 'gunmetal', ch=0.003)
    k.box((0, 0.025, 0.001), (0.025, 0.046, 0.010), 'gunmetal', hull=True)                   # bottom strap under the cylinder
    # barrel: long squared hand-cannon barrel, raised vent rib on posts, ported muzzle device
    k.ext_y(rrect(0.026, 0.044, ct=0.005, cb=0.003, cy=ZA, seg=1), 0.074, BE, 'gunmetal', ch1=0.005)
    k.box((0, 0.172, 0.0635), (0.010, 0.186, 0.005), 'gun3')                                   # top rib
    for i in range(5):
        k.box((0, 0.094 + i * 0.039, 0.0570), (0.006, 0.010, 0.008), 'gun3', hull=False)        # rib posts (vents between)
    muzzle(k, BE - 0.008, BE + 0.014, 0.0105, ZA, rb=0.0055, hull=False, seg=8)
    # full underlug (amber), deep at the frame and tapering toward the muzzle; ejector rod rides in it
    k.ext_x([(0.077, 0.012), (BE - 0.004, 0.012), (BE - 0.004, 0.002), (0.200, -0.004), (0.100, -0.014), (0.077, -0.014)],
            -0.010, 0.010, 'trim', ch=0.002)
    k.lathe([(0.080, 0), (0.080, 0.0045), (BE - 0.003, 0.0045), (BE + 0.001, 0.0032), (BE + 0.001, 0)], 'steel', 'y', (0, 0, 0.004), 8, hull=False)
    # sights: tall front blade with a red insert, tall notched rear blade on the top strap
    k.ext_x([(BE - 0.030, 0.066), (BE - 0.010, 0.066), (BE - 0.012, 0.080), (BE - 0.020, 0.080)], -0.003, 0.003, 'ink', ch=0)
    k.box((0, BE - 0.018, 0.0735), (0.012, 0.005, 0.004), 'red')
    for sd in (-1, 1):
        k.box((sd * 0.0065, -0.012, 0.0715), (0.006, 0.008, 0.017), 'ink')
    k.box((0, -0.012, 0.0625), (0.025, 0.016, 0.006), 'gun3')
    # hammer: exposed, rounded cock at the back of the frame with a spur, plus the hammer pin screw
    k.xbar(-0.0045, 0.0045, [(-0.022, 0.040), (-0.030, 0.058), (-0.040, 0.064), (-0.050, 0.060), (-0.060, 0.050), (-0.064, 0.043),
                             (-0.052, 0.046), (-0.040, 0.044), (-0.028, 0.034)], 'steel2', ch=0)
    k.cbox((-0.0245, -0.016, 0.034), (0.006, 0.014, 0.008), 'gun3', ch=0.0015, hull=False)
    k.screw((-0.0215, -0.012, 0.004), (-1, 0, 0))
    k.pin(-0.020, 0.020, 0.066, 0.004, 0.003)
    trigger_guard(k, rake, front=0.060, depth=-0.046, hook=False, top=-0.006)
    trigger(k, rake, ext=0.006)
    grip(k, rake, 'flare', w=0.036, top=-0.004, ptop=-0.026, grooves=3, chequer=3)
    # cylinder (the Mag): six flutes, six chambers on the flats (ink rims 4 mm proud, visible through the window)
    mk = Kit(pal)
    R = 0.0215
    prof = []
    for i in range(6):
        a = 60 * i
        prof += [(R * math.cos(D(a - 18)), R * math.sin(D(a - 18))), (R * math.cos(D(a + 18)), R * math.sin(D(a + 18))),
                 ((R - 0.008) * math.cos(D(a + 30)), (R - 0.008) * math.sin(D(a + 30)))]
    mk.ext_y(prof, -0.022, 0.022, 'steel2')
    for i in range(6):         # chamber bosses: ink discs on the flats, 3 mm proud of the cylinder
        a = D(60 * i)
        d = V((math.cos(a), 0.0, math.sin(a)))
        u = V((-math.sin(a), 0.0, math.cos(a)))
        mk.lathe([(R + 0.003, 0), (R + 0.003, 0.0080), (R - 0.004, 0.0080), (R - 0.004, 0)], 'ink', (d, u, d.cross(u)), (0, 0, 0), 6, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.025, ZA), 'muzzle': (0, BE + 0.016, ZA), 'eject': (-0.03, 0.025, ZA),
                   'sight': (0, -0.012, 0.078), 'cls': 'pistol', 'pivot': (-0.024, 0.050, ZA)}


def build_twintap(pal):
    """P-16 Twinfire: stacked twin-bore burst pistol, compensator, mini reflex, extended mag."""
    rake = 18
    k = Kit(pal)
    k.ext_y(rrect(0.046, 0.060, ct=0.011, cb=0.003, cy=0.034), -0.084, 0.124, 'gunmetal', ch0=0.004, ch1=0.003)   # tall slide
    for s in (-1, 1):
        sk = ('-x' if s > 0 else '+x',)
        for zz in (0.020, 0.048):            # twin barrel flutes along the slide
            k.box((s * 0.0235, 0.040, zz), (0.006, 0.120, 0.005), 'ink', skip=sk)
        for i in range(2):
            k.box((s * 0.0235, -0.074 + i * 0.010, 0.034), (0.006, 0.0045, 0.040), 'ink', skip=sk)
    k.box((0, 0.045, 0.034), (0.0525, 0.080, 0.006), 'trim')
    k.box((0.015, -0.005, 0.0605), (0.023, 0.046, 0.016), 'ink')                # port
    # compensator with top + side ports, twin crowns
    k.cbox((0, 0.143, 0.034), (0.050, 0.040, 0.058), 'gun3', ch=0.004, axis='y')
    for i in range(3):
        k.box((0, 0.131 + i * 0.011, 0.0635), (0.024, 0.005, 0.008), 'ink', skip=('-z',))
    for s in (-1, 1):
        for i in range(2):
            k.box((s * 0.0255, 0.134 + i * 0.016, 0.034), (0.008, 0.008, 0.030), 'ink', skip=('-x' if s > 0 else '+x',))
    for zz in (0.020, 0.048):
        muzzle(k, 0.156, 0.176, 0.0085, zz, rb=0.0048, hull=False, seg=8)
    # mini reflex on the slide + backup notch
    hz = hood_sight(k, -0.070, -0.040, 0.064, w=0.030, h=0.022, t=0.0045)
    k.box((0, 0.112, 0.0675), (0.007, 0.010, 0.010), 'ink', hull=True)
    # frame with rail slots, squared hooked guard
    k.ext_y(rrect(0.040, 0.024, c=0.003, cy=-0.004), -0.070, 0.118, 'gun2', ch1=0.010)
    for i in range(3):
        k.box((0, 0.086 + i * 0.012, -0.0135), (0.047, 0.005, 0.013), 'ink')
    k.xbar(-0.005, 0.005, [(-0.084, 0.008), (-0.091, 0.024), (-0.087, 0.032), (-0.080, 0.018)], 'steel2', ch=0)
    k.xbar(-0.0255, -0.0215, [(0.000, -0.004), (0.036, -0.004), (0.040, 0.002), (0.004, 0.004)], 'gun3', ch=0, hull=False)
    k.pin(-0.0225, 0.0225, 0.050, -0.008, 0.0028)
    trigger_guard(k, rake, front=0.080, depth=-0.048, hook=True, top=-0.010)
    trigger(k, rake, color='gun3')
    grip(k, rake, 'pistol', w=0.034, top=0.004, ptop=-0.026, grooves=3)
    my, mz = g2w(rake, HAND['cy'], -0.100)
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, -0.030, 0.040, 0.025, plate='gun3', plate_h=0.012, plate_w=0.041, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.0, -0.016)
        mk.box((s * 0.0125, y, z), (0.008, 0.026, 0.020), 'gun2', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.178, 0.034), 'eject': (0.03, -0.005, 0.060),
                   'sight': (0, -0.090, hz), 'cls': 'pistol'}
