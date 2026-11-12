"""INKBOLT guns: rifles. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_rivet(pal):
    """AR-22 Rivet: modular assault rifle. Forged upper and lower with layered side plates, a free-float cage
    handguard (the barrel, gas block and gas tube show through the slots), three-port brake, skeleton telescoping
    stock on a buffer tube, flip-up irons on a full-length top rail.
    Rarity layers: Rare bolts on a strike plate, an aiming module, a flared magwell and a round counter; Epic adds an
    energy cell under the handguard feeding a coil shroud on the barrel; Legendary (Kingsgold) crowns the handguard
    with a crest of fins, a sun-ray collar behind the brake, a royal seal on the receiver and a gem floating in the
    stock window."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    HU, HL, HM = 0.024, 0.0205, 0.0235           # half widths: upper, lower, magwell
    # ---- upper receiver
    k.ext_y(rrect(0.048, 0.044, ct=0.006, cb=0.002, cy=0.034), -0.112, 0.140, 'gunmetal', ch0=0.004, ch1=0.003)
    plate(k, [(-0.104, 0.017), (-0.012, 0.017), (-0.004, 0.025), (-0.004, 0.047), (-0.104, 0.047)], HU, 'body2', sides=(-1,))      # left data panel
    stencil(k, 'AR-22', HU + PR, -0.058, 0.0285, cap=0.011, sides=(-1,))
    stencil(k, 'IB ARMS  5.56', HU + PR, -0.058, 0.0195, cap=0.0045, sides=(-1,), font='cond')
    plate(k, [(0.006, 0.015), (0.134, 0.015), (0.134, 0.051), (0.018, 0.051), (0.006, 0.039)], HU, 'gunmetal', t=0.003, sides=(-1,), hull=True)   # barrel-extension block
    bolts(k, HU + 0.003, [(0.018, 0.022), (0.124, 0.022), (0.124, 0.045)], sides=(-1,))
    slots(k, HU + 0.003, 0.040, 0.112, 0.036, 4, h=0.012, fill=0.45, sides=(-1,), slant=-28)
    # right side: ejection port with the bolt carrier in it, open dust cover, brass deflector, forward assist
    k.box((HU + PR / 2 - 0.0005, 0.050, 0.041), (PR + 0.001, 0.062, 0.018), 'ink', skip=sk(1))
    k.box((HU + PR, 0.040, 0.0415), (0.0036, 0.034, 0.011), 'steel', skip=sk(1))
    k.box((HU + 0.0035, 0.051, 0.0245), (0.006, 0.058, 0.011), 'gun3', hull=True)
    k.pin(HU + 0.0005, HU + 0.0075, 0.051, 0.0310, 0.0024, color='steel2')
    k.ext_x([(-0.012, 0.030), (0.014, 0.030), (0.014, 0.050), (-0.004, 0.050)], HU - 0.001, HU + 0.008, 'gunmetal', ch=0.0015)
    k.lathe([(0.0, 0), (0.0, 0.0068), (0.018, 0.0068), (0.018, 0.0052), (0.024, 0.0052), (0.024, 0)], 'steel2',
            (V((0.45, -0.89, 0)).normalized(), V((0, 0, 1)), V((0.89, 0.45, 0))), (0.019, -0.050, 0.040), 8, hull=False, bands=[None, None, None, 'ink', 'ink'])
    plate(k, [(-0.104, 0.017), (-0.070, 0.017), (-0.070, 0.047), (-0.104, 0.047)], HU, 'body2', sides=(1,))
    stencil(k, 'RIVET', HU + PR, 0.104, 0.019, cap=0.008, sides=(1,))
    hazard(k, HU, 0.086, 0.132, 0.034, 0.048, n=4, sides=(1,))
    # ---- lower receiver, magwell
    k.ext_y(rrect(0.041, 0.034, c=0.003, cy=-0.004), -0.104, 0.140, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.074, 0.004), (0.138, 0.004), (0.140, -0.040), (0.134, -0.050), (0.072, -0.050), (0.070, -0.040)], -HM, HM, 'gun2', ch=0.003)
    k.ext_x([(0.066, -0.043), (0.144, -0.043), (0.147, -0.055), (0.063, -0.055)], -0.0265, 0.0265, 'frame2', ch=0.002)            # magwell flare
    plate(k, [(0.080, -0.004), (0.132, -0.004), (0.132, -0.038), (0.084, -0.038)], HM, 'frame2')
    slots(k, HM + PR, 0.090, 0.126, -0.021, 3, h=0.022, fill=0.4)
    cross_pin(k, HM, 0.132, 0.000)
    cross_pin(k, HL, -0.094, 0.002)
    plate(k, [(-0.082, -0.016), (-0.010, -0.016), (-0.004, -0.010), (-0.004, 0.008), (-0.082, 0.008)], HL, 'frame2')
    # controls: selector with its marks (left), bolt catch (left), mag release with fence (right)
    k.lathe([(HL - 0.003, 0.0052), (HL + 0.0045, 0.0052), (HL + 0.0045, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, -0.040, -0.001), 8, hull=False, caps=(False, True))
    k.xbar(-HL - 0.0075, -HL - 0.0040, [(-0.058, -0.004), (-0.038, -0.0055), (-0.036, 0.0025), (-0.056, 0.004)], 'gun3', ch=0, hull=False)
    k.box((-HL - PR * 1.5, -0.066, 0.002), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-HL - PR * 1.5, -0.040, 0.0105), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    k.xbar(-HM - 0.0050, -HM + 0.0030, [(0.078, 0.004), (0.098, 0.004), (0.100, 0.020), (0.092, 0.024), (0.080, 0.014)], 'ink', ch=0, hull=False)
    k.box((-HM - 0.0052, 0.089, 0.015), (0.0022, 0.012, 0.009), 'gun3')
    k.lathe([(HL - 0.003, 0.0050), (HL + 0.0040, 0.0050), (HL + 0.0040, 0)], 'steel2', 'x', (0, 0.058, -0.004), 8, hull=False, caps=(False, True))
    k.ext_x([(0.046, -0.012), (0.070, -0.012), (0.070, -0.009), (0.046, -0.009)], HL - 0.001, HL + 0.0045, 'gun2', ch=0, hull=False)
    # charging handle with latch, top rail
    k.cbox((0, -0.118, 0.0535), (0.040, 0.012, 0.011), 'gun3', ch=0.002, axis='x')
    k.box((-0.0185, -0.121, 0.0535), (0.008, 0.014, 0.006), 'steel2')
    k.box((0, -0.1255, 0.0535), (0.012, PR * 2, 0.007), 'ink')
    rail(k, -0.108, 0.136, 0.056, w=0.022, pitch=0.010, clear=[(-0.098, -0.082)])
    # ---- barrel group inside the cage
    k.lathe([(0.134, 0), (0.134, 0.0170), (0.150, 0.0170), (0.150, 0.0100), (0.292, 0.0100), (0.292, 0.0085), (0.452, 0.0085), (0.452, 0)],
            'steel', 'y', (0, 0, bz), 10, bands=['steel2', 'steel2', 'steel2', None, None, None, None])
    gas_block(k, 0.296, bz, r=0.0125, L=0.022, tube_to=0.146, tz=bz + 0.0165)
    ys = cage(k, 0.138, 0.362, bz, 0.054, 0.050, 0.013, n=5, rib=0.010, open=('R', 'UR', 'UL', 'L'), color='gun3')
    for (a, b) in zip(ys[:-1], ys[1:]):                                          # trim line under the side slots
        plate(k, rect(a[1] + 0.004, b[0] - 0.004, bz - 0.0105, bz - 0.0075), 0.027, 'trim', ch=0)
    for s in (-1, 1):
        bolt(k, (s * (0.027 + PR), 0.146, bz + 0.007), (s, 0, 0))
        bolt(k, (s * (0.027 + PR), 0.146, bz - 0.007), (s, 0, 0))
        sling_loop(k, 0.354, bz, s, hw=0.027 + PR, r=0.006)
    rail(k, 0.142, 0.358, 0.059 + PR, w=0.020, pitch=0.010, clear=[(0.322, 0.338)])
    muzzle(k, 0.448, 0.500, 0.0120, bz, rb=0.0055, ports=3, top_ports=3)
    k.ring('y', (0, 0, bz), 0.440, 0.449, 0.0085, 0.0135, 'steel2', seg=10, hull=False)                  # jam nut
    sz = iron_rear(k, -0.090, 0.059)
    iron_front(k, 0.330, 0.062 + PR, post=0.008 - PR)
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.008, ptop=-0.038, grooves=2)
    # ---- stock: buffer tube, castle nut and end plate, skeleton telescoping stock
    k.lathe([(-0.100, 0), (-0.100, 0.014), (-0.270, 0.014), (-0.274, 0.010), (-0.274, 0)], 'steel2', 'y', (0, 0, 0.030), 8)
    k.ring('y', (0, 0, 0.030), -0.133, -0.1215, 0.014, 0.0185, 'steel', seg=8, hull=False)
    k.cbox((0, -0.1155, 0.021), (0.038, 0.006, 0.050), 'steel2', ch=0.002, axis='y')
    for s in (-1, 1):
        sling_loop(k, -0.1155, 0.004, s, hw=0.019, r=0.0026)
    k.ext_x([(-0.160, 0.051), (-0.298, 0.053), (-0.298, 0.009), (-0.170, 0.009), (-0.160, 0.016)], -0.019, 0.019, 'furn', ch=0.004)       # sleeve
    k.ext_x([(-0.276, 0.012), (-0.300, 0.012), (-0.303, -0.044), (-0.282, -0.048), (-0.270, -0.030)], -0.017, 0.017, 'furn', ch=0.003)     # heel
    k.bar((0, -0.180, 0.004), (0, -0.276, -0.036), 0.028, 0.011, 'furn', hull=True, up=(0, 0.4, 1))                                         # brace
    k.ext_x([(-0.298, 0.057), (-0.313, 0.055), (-0.316, -0.049), (-0.300, -0.050)], -0.0225, 0.0225, 'rubber', ch=0.003)                    # butt pad
    for i in range(6):
        for s in (-1, 1):
            k.box((s * (0.0225 + PR / 2 - 0.0005), -0.307, 0.044 - i * 0.017), (PR + 0.001, 0.011, 0.005), 'ink', skip=sk(s))
    plate(k, [(-0.176, 0.018), (-0.262, 0.018), (-0.262, 0.044), (-0.168, 0.044)], 0.019, 'frame2')
    slots(k, 0.019 + PR, -0.250, -0.182, 0.031, 5, h=0.014, fill=0.35)
    k.cbox((0, -0.226, 0.0545), (0.026, 0.094, 0.006), 'rubber', ch=0.002, axis='y')                                                        # cheek pad
    top_slots(k, 0.0575, -0.268, -0.184, 9, w=0.020, fill=0.32)
    for s in (-1, 1):                                                                                                                       # sleeve top rails beside the pad
        k.box((s * 0.0158, -0.226, 0.0532), (0.0030, 0.110, 0.0030), 'frame2')
    k.ext_x([(-0.172, 0.008), (-0.196, 0.008), (-0.204, -0.004), (-0.182, -0.002)], -0.007, 0.007, 'steel2', ch=0.0015)                     # adjust lever
    for s in (-1, 1):
        sling_loop(k, -0.286, 0.032, s, hw=0.019, r=0.006)
        bolt(k, (s * 0.017, -0.288, -0.028), (s, 0, 0))
    # ---- magazine
    mk = Kit(pal)
    mag_box(mk, 4, 0.052, -0.120, 0.052, 0.026, curve=0.040)

    # ---- Rare (and up): strike plate, aiming module with its cable, flared magwell funnel, round counter
    r3 = Kit(pal)
    plate(r3, [(-0.100, 0.049), (-0.020, 0.049), (-0.008, 0.037), (-0.008, 0.021), (-0.100, 0.021)], HU + PR, 'gun3', t=0.0035, sides=(1,), hull=True)
    bolts(r3, HU + PR + 0.0035, [(-0.092, 0.027), (-0.092, 0.043), (-0.020, 0.027)], sides=(1,))
    slots(r3, HU + PR + 0.0035, -0.080, -0.032, 0.035, 4, h=0.010, fill=0.4, sides=(1,), slant=28)
    laser_box(r3, 0.186, bz + 0.004, s=1, hw=0.027 + PR, L=0.052, w=0.018, h=0.024, color='gun2')
    cable(r3, [(0.0375, 0.160, bz + 0.004), (0.0330, 0.148, bz - 0.006), (0.0275, 0.136, bz - 0.014), (0.0262, 0.118, bz - 0.020)], clamps=(2,))
    r3.ext_x([(0.060, -0.046), (0.150, -0.046), (0.156, -0.064), (0.054, -0.064)], -0.0300, 0.0300, 'gun3', ch=0.003)                      # funnel
    bolts(r3, 0.0300, [(0.066, -0.055), (0.144, -0.055)])
    r3.cbox((-HU - 0.004, -0.058, 0.052), (0.010, 0.040, 0.012), 'gun2', ch=0.002, hull=True)                                              # counter housing
    for i in range(4):
        r3.box((-HU - 0.0090 - PR / 2 + 0.0005, -0.070 + i * 0.008, 0.052), (PR + 0.001, 0.005, 0.006), 'emis', skip=sk(-1))
    for s in (-1, 1):                                                                                                                       # stock side saddles
        r3.cbox((s * 0.0225, -0.222, 0.040), (0.007, 0.066, 0.016), 'gun3', ch=0.002, hull=True)
        bolt(r3, (s * 0.026, -0.246, 0.040), (s, 0, 0))
        bolt(r3, (s * 0.026, -0.198, 0.040), (s, 0, 0))

    # ---- Epic (and up): energy cell slung under the handguard, conduit to a coil shroud on the bare barrel
    r4 = Kit(pal)
    r4.cbox((0, 0.196, bz - 0.0305), (0.030, 0.062, 0.011), 'gun2', ch=0.003, axis='y', hull=True)                                         # cradle
    energy_cell(r4, (0, 0.196, bz - 0.0460), L=0.056, r=0.0095, cage_bars=4)
    conduit(r4, [(0.012, 0.228, bz - 0.044), (0.022, 0.250, bz - 0.036), (0.0315, 0.280, bz - 0.022), (0.0315, 0.350, bz - 0.022),
                 (0.022, 0.372, bz - 0.014), (0.016, 0.386, bz - 0.008)], r=0.0028, every=2)
    r4.ring('y', (0, 0, bz), 0.366, 0.438, 0.0090, 0.0165, 'gun2', seg=10)                                                                   # shroud
    for i in range(4):
        r4.ring('y', (0, 0, bz), 0.376 + i * 0.016, 0.384 + i * 0.016, 0.0150, 0.0165 + PR, 'emis', seg=10, hull=False)
    fins(r4, (0, -0.148, 0.030), (0.046, 0.022, 0.046), 3, axis='y', color='gun3', hull=True)                                              # buffer heat sink
    for s in (-1, 1):
        r4.box((s * (0.019 + PR / 2 - 0.0005), -0.230, 0.0135), (PR + 0.001, 0.090, 0.003), 'emis', skip=sk(s))

    # ---- Legendary: handguard crest, sun-ray collar, royal seal, the gem in the stock window
    r5 = Kit(pal)
    for s in (-1, 1):                                                                                                                       # crest fins on the upper diagonals
        with r5.at((s * 0.0215, 0, bz + 0.0195), (0, s * 45, 0)):
            for (a, b) in zip(ys[:-1], ys[1:]):
                y0, y1 = a[1] + 0.002, b[0] - 0.002
                r5.ext_x([(y0, 0.0), (y1, 0.0), (y1 - 0.006, 0.013), (y0 + 0.012, 0.013)], -0.0022, 0.0022, 'gun3', ch=0.0008)
                r5.ext_x([(y0 + 0.006, 0.013), (y1 - 0.008, 0.013), (y1 - 0.011, 0.0165), (y0 + 0.011, 0.0165)], -0.0012, 0.0012, 'trim', ch=0, hull=False)
    for i in range(8):                                                                                                                      # sun rays behind the brake
        a = math.pi * 2 * (i + 0.5) / 8
        with r5.at((0, 0.443, bz), (0, math.degrees(a), 0)):
            r5.ext_x([(-0.010, 0.0170), (0.004, 0.0170), (-0.004, 0.0330), (-0.012, 0.0270)], -0.0018, 0.0018, 'gun3', ch=0.0006)
    r5.ring('y', (0, 0, bz), 0.4385, 0.4470, 0.0130, 0.0190, 'steel', seg=10)
    r5.ring('y', (0, 0, bz), 0.4405, 0.4450, 0.0175, 0.0190 + PR, 'trim', seg=10, hull=False)
    for s in (-1, 1):                                                                                                                       # royal seal on the magwell
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        r5.lathe([(-0.001, 0.0150), (0.0055, 0.0150), (0.0055, 0.0115), (0.0035, 0.0115), (0.0035, 0.0060), (0.0070, 0.0060), (0.0085, 0)],
                 'gun3', n, (s * (HM + PR), 0.108, -0.021), 8, hull=False, bands=[None, None, 'ink', 'ink', 'trim', 'trim'], caps=(False, True), a0=0)
    with r5.at((0, -0.238, -0.003)):                                                                                                        # the gem
        r5.lathe([(-0.008, 0), (-0.002, 0.006), (0.002, 0.006), (0.008, 0)], 'emis', 'z', (0, 0, 0), 6, hull=False)
        for z in (-0.0095, 0.0095):
            r5.lathe([(z - 0.0015, 0), (z - 0.0015, 0.003), (z + 0.0015, 0.003), (z + 0.0015, 0)], 'gun3', 'z', (0, 0, 0), 6, hull=False)
    r5.bar((0, -0.238, 0.0065), (0, -0.238, 0.020), 0.010, 0.004, 'gun3', up=(0, 1, 0))
    for s in (-1, 1):                                                                                                                       # gold inlay bars on the stock sleeve
        r5.box((s * (0.019 + PR + 0.0005), -0.216, 0.0225), (PR + 0.001, 0.070, 0.003), 'trim', skip=sk(s))
        r5.box((s * (0.019 + PR + 0.0005), -0.216, 0.0395), (PR + 0.001, 0.070, 0.003), 'trim', skip=sk(s))
    m5 = Kit(pal)                                                                                                                           # magazine: gold bands
    for t in (0.30, 0.62):
        y, z = g2w(4, 0.040 * t * t, 0.052 + (-0.120 - 0.052) * t)
        m5.cbox((0, y, z), (0.036, 0.060, 0.007), 'trim', ch=0, rot=(-4 - 14 * t, 0, 0))
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.105, -0.052), 'muzzle': (0, 0.502, bz), 'eject': (0.03, 0.050, 0.042),
                   'sight': (0, -0.105, sz), 'cls': 'rifle', 'guard': (0, 0.300, 0.034),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'5': m5}}


def build_triplet(pal):
    """AR-3 Tribolt: bullpup burst rifle. A steel receiver sits in a one-piece stock shell with an angular cut (panel
    step), rear magwell with a collar and a big paddle catch behind it, integrated optic on two pillars (you see
    through under the tube), quick-change barrel collar, gas regulator, an open three-port brake, foregrip.
    Rarity layers: Rare bolts on heel armour, a magwell funnel, an aiming module with its cable, a round counter and
    cheek rails; Epic slots an energy cell into the optic bridge, feeds the gas block through a conduit, lights the
    three brake ports and the stock vents; Legendary (crimson lacquer) fans three forward-swept blades round the
    barrel over a tsuba, a heel blade under the butt, lacquer slashes and a diamond mon on the stock."""
    rake = 18
    k = Kit(pal)
    bz = 0.034
    HB, HR, HG = 0.025, 0.0225, 0.023            # half widths: stock shell, receiver, handguard
    # ---- receiver inside the stock shell (grip forward, mag behind the grip, butt at the rear)
    k.ext_x([(0.1178, 0.062), (-0.192, 0.062), (-0.192, 0.006), (0.1178, 0.006)], -HR, HR, 'body2', ch=0.002)
    shell = [(0.122, 0.016), (0.122, -0.012), (-0.020, -0.012), (-0.040, -0.030), (-0.140, -0.030), (-0.170, -0.058), (-0.290, -0.074),
             (-0.318, -0.070), (-0.318, 0.050), (-0.300, 0.064), (-0.204, 0.064), (-0.174, 0.032), (-0.056, 0.032), (-0.040, 0.016)]
    k.ext_x(shell, -HB, HB, 'gunmetal', ch=0.003)
    # right: ejection port with the bolt, case deflector; front plate with the name and a hazard band
    k.box((HR + PR / 2 - 0.0005, -0.120, 0.046), (PR + 0.001, 0.062, 0.018), 'ink', skip=sk(1))
    k.box((HR + PR, -0.110, 0.0465), (0.0036, 0.036, 0.011), 'steel', skip=sk(1))
    k.box((HR + PR + 0.0022, -0.098, 0.0465), (0.0036, 0.004, 0.0075), 'steel2', skip=sk(1))                        # extractor
    k.ext_x([(-0.166, 0.036), (-0.153, 0.036), (-0.153, 0.057), (-0.161, 0.057)], HR - 0.001, HR + 0.0090, 'gun3', ch=0.0015)   # deflector
    plate(k, [(-0.030, 0.021), (0.112, 0.021), (0.112, 0.037), (-0.022, 0.037)], HR, 'gunmetal', sides=(1,))
    stencil(k, 'TRIBOLT', HR + PR, 0.040, 0.0255, cap=0.008, sides=(1,))
    hazard(k, HR, 0.064, 0.112, 0.042, 0.056, n=4, sides=(1,))
    bolts(k, HR, [(-0.026, 0.050), (0.040, 0.050)], sides=(1,))
    # left: port cover, data panel, burst selector with its marks
    plate(k, rect(-0.152, -0.088, 0.037, 0.057, c=0.003), HR, 'gunmetal', sides=(-1,))
    bolts(k, HR + PR, [(-0.146, 0.042), (-0.094, 0.042), (-0.146, 0.052), (-0.094, 0.052)], r=0.0024, sides=(-1,))
    plate(k, [(-0.030, 0.021), (0.052, 0.021), (0.060, 0.029), (0.060, 0.046), (-0.022, 0.046)], HR, 'gunmetal', sides=(-1,))
    stencil(k, 'AR-3', HR + PR, 0.016, 0.0315, cap=0.010, sides=(-1,))
    stencil(k, 'IB ARMS  5.56  3RB', HR + PR, 0.016, 0.0245, cap=0.0042, sides=(-1,), font='cond')
    k.lathe([(HR - 0.002, 0.0055), (HR + 0.0040, 0.0055), (HR + 0.0040, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.092, 0.031), 8, hull=False, caps=(False, True))
    k.xbar(-HR - 0.0075, -HR - 0.0035, [(0.074, 0.028), (0.094, 0.0265), (0.096, 0.0345), (0.076, 0.036)], 'gun3', ch=0, hull=False)
    for (y, z, c) in ((0.078, 0.045, 'mark'), (0.090, 0.048, 'mark'), (0.102, 0.045, 'red')):
        k.box((-HR - PR / 2 + 0.0005, y, z), (PR + 0.001, 0.004, 0.004), c, skip=sk(-1))
    bolts(k, HR, [(-0.026, 0.054), (0.112, 0.054)], sides=(-1,))
    # ---- shell: moulded butt panel with rib cuts, magwell panel, accent lines, pins, cross-bolt safety, swivels
    plate(k, [(-0.300, -0.062), (-0.190, -0.050), (-0.166, -0.026), (-0.166, 0.020), (-0.300, 0.020)], HB, 'body2')
    slots(k, HB + PR, -0.292, -0.180, -0.014, 5, h=0.022, fill=0.34, slant=-24)
    bolts(k, HB + PR, [(-0.294, 0.014), (-0.172, 0.014)])
    plate(k, [(-0.150, -0.024), (-0.058, -0.024), (-0.050, -0.016), (-0.050, 0.020), (-0.150, 0.020)], HB, 'body2')
    for z in (-0.016, -0.008, 0.000):
        slots(k, HB + PR, -0.142, -0.062, z, 1, h=0.003, fill=0.9)
    cross_pin(k, HB + PR, -0.100, 0.011)
    plate(k, rect(-0.304, -0.062, 0.0255, 0.0285), HB, 'trim', ch=0)
    plate(k, rect(-0.036, 0.116, 0.0090, 0.0118), HB, 'trim', ch=0)
    k.pin(-HB - 0.0035, HB + 0.0035, -0.006, 0.001, 0.0040, color='steel2')                                         # cross-bolt safety
    k.box((-HB - PR / 2 + 0.0005, 0.004, 0.001), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    k.box((HB + PR / 2 - 0.0005, 0.004, 0.001), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(1))
    cross_pin(k, HB, -0.226, 0.047)
    cross_pin(k, HB, 0.096, -0.001)
    for s in (-1, 1):
        sling_loop(k, -0.288, 0.045, s, hw=HB, r=0.0065)
    # magwell collar and the big paddle catch behind it
    k.ext_x([(-0.126, -0.022), (-0.054, -0.022), (-0.052, -0.036), (-0.056, -0.042), (-0.124, -0.042), (-0.128, -0.036)], -0.0275, 0.0275, 'gun2', ch=0.002)
    k.ext_x([(-0.130, -0.026), (-0.142, -0.026), (-0.156, -0.050), (-0.148, -0.055), (-0.134, -0.040)], -0.012, 0.012, 'gun3', ch=0.0015)
    # ---- rubber butt plate: side ribs and grooves across the back
    k.ext_x([(-0.300, 0.058), (-0.326, 0.058), (-0.328, -0.072), (-0.302, -0.076)], -0.0285, 0.0285, 'rubber', ch=0.003)
    for i in range(6):
        z = 0.044 - i * 0.021
        for s in (-1, 1):
            k.box((s * (0.0285 + PR / 2 - 0.0005), -0.315, z), (PR + 0.001, 0.012, 0.006), 'ink', skip=sk(s))
        k.box((0, -0.3275 - PR / 2, z), (0.040, PR + 0.002, 0.005), 'ink', skip=('+y',))
    # cheek pad
    k.cbox((0, -0.250, 0.066), (0.034, 0.092, 0.005), 'rubber', ch=0.002, axis='y')
    top_slots(k, 0.0685, -0.290, -0.210, 8, w=0.022, fill=0.32)
    # ---- integrated optic: base, two pillars (open under the tube), tube, lens hood, adjustment caps
    k.ext_x([(-0.172, 0.060), (0.046, 0.060), (0.038, 0.068), (-0.164, 0.068)], -0.013, 0.013, 'gun3', ch=0.002)
    k.ext_x([(-0.134, 0.066), (-0.096, 0.066), (-0.102, 0.090), (-0.128, 0.090)], -0.008, 0.008, 'gun3', ch=0.0015)
    k.ext_x([(-0.012, 0.066), (0.028, 0.066), (0.022, 0.090), (-0.006, 0.090)], -0.008, 0.008, 'gun3', ch=0.0015)
    bolts(k, 0.013, [(-0.150, 0.064), (-0.054, 0.064), (0.030, 0.064)], r=0.0024)
    scope(k, -0.150, 0.052, 0.096, rt=0.012, ro=0.018, re=0.016, lo=0.030, le=0.028, seg=12)
    k.ring('y', (0, 0, 0.096), 0.046, 0.064, 0.0160, 0.0202, 'rubber', seg=12)                                      # lens hood
    turret(k, (0, -0.034, 0.106), 'z', r=0.0070, h=0.007)
    turret(k, (0.010, -0.034, 0.096), 'x', r=0.0070, h=0.007)
    turret(k, (-0.010, -0.070, 0.096), '-x', r=0.0055, h=0.005, color='steel2')
    # ---- handguard shroud: lower cladding, vents (right), cocking slot and handle (left), top rail, folded sight
    k.ext_y(rrect(0.046, 0.046, ct=0.010, cb=0.008, cy=0.031), 0.118, 0.300, 'gun2', ch1=0.006)
    plate(k, rect(0.128, 0.290, 0.017, 0.029, c=0.003), HG, 'frame2')
    bolts(k, HG + PR, [(0.136, 0.023), (0.206, 0.023)])
    for s in (-1, 1):
        sling_loop(k, 0.276, 0.023, s, hw=HG + PR, r=0.0050)
    slots(k, HG, 0.134, 0.284, 0.038, 6, h=0.008, fill=0.5, sides=(1,), slant=28)
    k.box((-HG - PR / 2 + 0.0005, 0.200, 0.038), (PR + 0.001, 0.144, 0.006), 'ink', skip=sk(-1))
    k.cbox((-HG - 0.0065, 0.254, 0.038), (0.017, 0.012, 0.010), 'gun3', ch=0.002)
    rail(k, 0.126, 0.292, 0.054, w=0.020, pitch=0.010, clear=[(0.270, 0.282)])
    k.cbox((0, 0.276, 0.0615), (0.014, 0.022, 0.009), 'gunmetal', ch=0.002, axis='x')
    # ---- quick-change collar, gas block and regulator, barrel, open three-port brake
    barrel(k, 0.290, 0.400, 0.0090, bz)
    k.lathe([(0.294, 0), (0.294, 0.0175), (0.310, 0.0175), (0.316, 0.0125), (0.316, 0)], 'steel2', 'y', (0, 0, bz), 8)
    knurl(k, 0.3015, 0.3105, 0.0175, bz, n=3, seg=8)
    k.cbox((0, 0.332, bz + 0.006), (0.022, 0.020, 0.034), 'steel2', ch=0.003, axis='y')
    k.lathe([(0.296, 0), (0.296, 0.0048), (0.344, 0.0048), (0.344, 0.0072), (0.356, 0.0072), (0.356, 0.0040), (0.361, 0.0040), (0.361, 0)], 'steel', 'y',
            (0, 0, bz + 0.0160), 8, hull=False, bands=[None, None, None, 'gun3', 'ink', None, None])
    k.ring('y', (0, 0, bz), 0.389, 0.398, 0.0090, 0.0135, 'steel2', seg=10, hull=False)
    for sz_ in (-1, 1):
        k.cbox((0, 0.422, bz + sz_ * 0.0115), (0.030, 0.050, 0.006), 'steel', ch=0.002, axis='y')
    for y in (0.4005, 0.414, 0.428, 0.442):
        k.box((0, y, bz), (0.026, 0.004, 0.019), 'steel', hull=True)
    top_slots(k, bz + 0.0145, 0.404, 0.440, 3, w=0.012, fill=0.5)
    muzzle(k, 0.4425, 0.450, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # ---- full-hand trigger guard, trigger, grip, foregrip
    hy, cy = HAND['hy'], HAND['cy']
    gb = g2w(rake, cy + hy + 0.022, -0.100)
    k.ext_x([(0.070, -0.010), (0.078, -0.024), (gb[0] + 0.004, gb[1]), (gb[0] - 0.010, gb[1] - 0.008),
             (gb[0] - 0.010, gb[1] + 0.002), (0.064, -0.024), (0.060, -0.010)], -0.006, 0.006, 'gun2')
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=-0.010, ptop=-0.034)
    vgrip(k, 0.200, 0.008, length=0.070)
    mk = Kit(pal)
    mag_box(mk, 4, 0.030, -0.110, 0.050, 0.026, curve=0.030, plate='gun3')

    # ---- Rare (and up): heel armour, magwell funnel, aiming module with its cable, round counter, cheek rails
    r3 = Kit(pal)
    plate(r3, [(-0.298, -0.066), (-0.244, -0.058), (-0.232, -0.036), (-0.298, -0.036)], HB + PR, 'gun3', t=0.003, hull=True)
    bolts(r3, HB + PR + 0.003, [(-0.290, -0.058), (-0.290, -0.042), (-0.244, -0.047)])
    r3.ext_x([(-0.126, -0.036), (-0.052, -0.036), (-0.046, -0.050), (-0.130, -0.050)], -0.0300, 0.0300, 'gun3', ch=0.003)
    bolts(r3, 0.0300, [(-0.120, -0.043), (-0.058, -0.043)])
    laser_box(r3, 0.250, 0.037, s=1, hw=HG + PR, L=0.050, w=0.018, h=0.020, color='gun2')
    cable(r3, [(0.0335, 0.224, 0.040), (0.0270, 0.212, 0.047), (0.0205, 0.196, 0.0515), (0.0205, 0.136, 0.0515), (0.0195, 0.112, 0.050)], clamps=(2,))
    r3.cbox((-HR - 0.0035, -0.120, 0.047), (0.011, 0.050, 0.016), 'gun2', ch=0.002)
    for i in range(4):
        r3.box((-HR - 0.0090 - PR / 2 + 0.0005, -0.135 + i * 0.010, 0.047), (PR + 0.001, 0.006, 0.007), 'emis', skip=sk(-1))
    for s in (-1, 1):
        r3.cbox((s * 0.0205, -0.250, 0.0665), (0.007, 0.104, 0.008), 'gun3', ch=0.002)
        bolt(r3, (s * 0.0205, -0.290, 0.0705), (0, 0, 1), 0.0024)
        bolt(r3, (s * 0.0205, -0.210, 0.0705), (0, 0, 1), 0.0024)

    # ---- Epic (and up): energy cell in the optic bridge, conduit to the gas block, lit brake ports, glowing vents, barrel fins
    r4 = Kit(pal)
    energy_cell(r4, (0, -0.054, 0.076), L=0.070, r=0.0058, cage_bars=4)
    conduit(r4, [(-0.009, -0.024, 0.074), (-0.018, -0.008, 0.0655), (-0.018, 0.108, 0.0655), (-0.0205, 0.132, 0.0515), (-0.0205, 0.288, 0.0515),
                 (-0.013, 0.306, 0.053), (-0.006, 0.324, 0.056)], r=0.0026, every=2)
    for i in range(3):
        r4.ring('y', (0, 0, bz), 0.4035 + i * 0.014, 0.4105 + i * 0.014, 0.0035, 0.0078, 'emis', seg=8, hull=False)
    fins(r4, (0, 0.3765, bz), (0.030, 0.024, 0.030), 3, axis='y', color='gun3', hull=True)
    slots(r4, HB + 2 * PR, -0.292, -0.180, -0.014, 5, h=0.014, fill=0.12, color='emis', slant=-24)

    # ---- Legendary: three forward-swept blades over a tsuba, the heel blade, lacquer slashes, diamond mon
    r5 = Kit(pal)
    for ang in (0, 90, -90):
        with r5.at((0, 0, bz), (0, ang, 0)):
            r5.ext_x([(0.322, 0.006), (0.350, 0.006), (0.368, 0.0185), (0.422, 0.0185), (0.449, 0.041), (0.412, 0.029), (0.356, 0.032), (0.324, 0.041), (0.330, 0.026)], -0.0016, 0.0016, 'steel', ch=0.0012)
            r5.ext_x([(0.340, 0.0275), (0.356, 0.0245), (0.414, 0.0225), (0.438, 0.0320), (0.412, 0.0255), (0.358, 0.0280)], -0.0031, 0.0031, 'trim', ch=0, hull=False)
    r5.ring("y", (0, 0, bz), 0.3165, 0.3215, 0.0100, 0.0245, 'gun3', seg=8)
    r5.ring('y', (0, 0, bz), 0.3178, 0.3202, 0.0225, 0.0262, 'trim', seg=8, hull=False)
    r5.ext_x([(-0.186, -0.058), (-0.288, -0.071), (-0.322, -0.110), (-0.262, -0.091), (-0.212, -0.079)], -0.0020, 0.0020, 'steel', ch=0.0015)
    r5.ext_x([(-0.178, -0.055), (-0.294, -0.070), (-0.296, -0.080), (-0.180, -0.066)], -0.0080, 0.0080, 'gun3', ch=0.002)
    bolts(r5, 0.0080, [(-0.200, -0.064), (-0.240, -0.069), (-0.280, -0.074)], r=0.0022, color='trim')
    plate(r5, [(-0.170, 0.0075), (-0.296, 0.0030), (-0.296, 0.0050), (-0.170, 0.0115)], HB + PR, 'trim', ch=0)
    plate(r5, [(0.146, 0.0205), (0.268, 0.0225), (0.268, 0.0245), (0.146, 0.0255)], HG + PR, 'trim', ch=0)
    plate(r5, [(-0.271, 0.046), (-0.258, 0.034), (-0.245, 0.046), (-0.258, 0.058)], HB, 'gun3', t=0.003, hull=True)
    plate(r5, [(-0.265, 0.046), (-0.258, 0.0395), (-0.251, 0.046), (-0.258, 0.0525)], HB + 0.003, 'emis', ch=0)
    m5 = Kit(pal)
    for t in (0.42, 0.72):
        y, z = g2w(4, 0.030 * t * t, 0.030 + (-0.110 - 0.030) * t)
        m5.cbox((0, y, z), (0.036, 0.058, 0.006), 'trim', ch=0, rot=(-4 - 14 * t, 0, 0))
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, -0.090, -0.030), 'muzzle': (0, 0.452, bz), 'eject': (0.03, -0.120, 0.040),
                   'sight': (0, -0.170, 0.096), 'cls': 'rifle', 'fore': (0.200, 0.008),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'5': m5}}


def build_longtom(pal):
    """DMR-60 Longtom: semi-auto marksman rifle, 1.5x prism optic, long free-float guard, fixed precision stock."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    k.ext_y(rrect(0.048, 0.044, ct=0.006, cb=0.002, cy=0.034), -0.114, 0.140, 'gunmetal', ch0=0.004, ch1=0.003)   # upper
    k.box((0.01675, 0.050, 0.042), (0.0205, 0.058, 0.016), 'ink')
    k.box((0.0265, 0.052, 0.0255), (0.006, 0.050, 0.011), 'gun3')
    k.ext_y(rrect(0.041, 0.034, c=0.003, cy=-0.004), -0.106, 0.140, 'gun2', ch0=0.004, ch1=0.004)                  # lower
    k.ext_x([(0.074, 0.004), (0.138, 0.004), (0.140, -0.040), (0.134, -0.050), (0.072, -0.050), (0.070, -0.040)], -0.0235, 0.0235, 'gun2', ch=0.003)
    k.pin(-0.0265, 0.0265, 0.134, 0.000, 0.003)
    k.pin(-0.0235, 0.0235, -0.096, 0.000, 0.003)
    k.xbar(-0.0240, -0.0205, [(-0.050, -0.004), (-0.030, -0.006), (-0.028, 0.002), (-0.048, 0.004)], 'gun3', ch=0, hull=False)
    k.cbox((0, -0.120, 0.0535), (0.036, 0.012, 0.011), 'gun3', ch=0.002, axis='x')
    rail(k, -0.110, 0.136, 0.056, w=0.022, clear=[(-0.092, 0.066)])
    # 1.5x prism optic: trapezoid housing, recessed lenses in two bells, windage cap, fibre strip
    oz = 0.059
    k.ext_y([(-0.018, oz), (0.018, oz), (0.018, oz + 0.022), (0.012, oz + 0.036), (-0.012, oz + 0.036), (-0.018, oz + 0.022)], -0.060, 0.032, 'gunmetal', ch0=0.003, ch1=0.003)
    lz = oz + 0.020
    k.lathe([(0.052, 0), (0.052, 0.013), (0.060, 0.013), (0.060, 0.017), (0.032, 0.017), (0.032, 0)], 'gunmetal', 'y', (0, 0, lz), 10, bands=['lens', 'ink', None, None, None])
    k.lathe([(-0.078, 0), (-0.078, 0.010), (-0.086, 0.010), (-0.086, 0.014), (-0.060, 0.014), (-0.060, 0)], 'gunmetal', 'y', (0, 0, lz), 10, bands=['lens', 'ink', None, None, None])
    turret(k, (0.018, -0.014, oz + 0.016), 'x', r=0.008, h=0.006)
    k.cbox((0, -0.020, oz + 0.040), (0.010, 0.040, 0.008), 'gun3', ch=0.002, axis='y', hull=False)
    # long octagonal guard with slots, fluted barrel, compensator
    k.ext_y(rrect(0.048, 0.048, c=0.014, cy=bz), 0.138, 0.420, 'gun3', ch0=0.003, ch1=0.006)
    for s in (-1, 1):
        for i in range(6):
            k.box((s * 0.0240, 0.165 + i * 0.040, bz), (0.006, 0.024, 0.008), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.290, bz - 0.0145), (0.0540, 0.220, 0.006), 'trim')
    rail(k, 0.141, 0.250, 0.058, w=0.020, pitch=0.018)
    barrel(k, 0.410, 0.536, 0.0100, bz)
    for s in (-1, 1):
        k.box((s * 0.0105, 0.475, bz), (0.006, 0.100, 0.004), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.475, bz + 0.0105), (0.004, 0.100, 0.006), 'ink', skip=('-z',))
    muzzle(k, 0.536, 0.600, 0.0130, bz, ports=3, top_ports=2, rb=0.0060, seg=8)
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.008, ptop=-0.038, grooves=2)
    # fixed precision stock: cheek riser, butt pad, sling stud
    k.ext_x([(-0.110, 0.050), (-0.180, 0.050), (-0.330, 0.054), (-0.334, -0.060), (-0.300, -0.064), (-0.200, -0.016), (-0.110, -0.016)], -0.020, 0.020, 'furn', ch=0.005)
    k.ext_x([(-0.190, 0.049), (-0.300, 0.053), (-0.300, 0.064), (-0.196, 0.062)], -0.0155, 0.0155, 'gun3', ch=0.003)
    k.ext_x([(-0.330, 0.058), (-0.346, 0.058), (-0.348, -0.064), (-0.332, -0.066)], -0.0235, 0.0235, 'ink', ch=0.003)
    for s in (-1, 1):
        k.box((s * 0.0215, -0.260, -0.004), (0.006, 0.070, 0.004), 'ink', skip=('-x' if s > 0 else '+x',))
    k.ring('x', (0, -0.250, -0.046), -0.023, 0.023, 0.004, 0.0075, 'steel2', seg=8, hull=False)
    mk = Kit(pal)
    mag_box(mk, 4, 0.040, -0.084, 0.056, 0.028, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.105, -0.050), 'muzzle': (0, 0.602, bz), 'eject': (0.03, 0.050, 0.042),
                   'sight': (0, -0.100, lz), 'scope': (0, -0.086, lz), 'cls': 'rifle', 'guard': (0, 0.320, 0.034)}


def build_vanguard(pal):
    """AR-40 Vanguard: heavy battle rifle, long free-float rail, red-dot over a tall riser, straight 20-round box."""
    rake = 20
    k = Kit(pal)
    bz = 0.036
    k.ext_y(rrect(0.050, 0.050, ct=0.006, cb=0.002, cy=0.036), -0.118, 0.150, 'gunmetal', ch0=0.004, ch1=0.003)
    k.box((0.0195, 0.052, 0.044), (0.020, 0.064, 0.018), 'ink')
    k.cbox((-0.032, 0.090, 0.046), (0.016, 0.012, 0.012), 'gun3', ch=0.002, hull=False)                    # side charging handle
    k.ext_y(rrect(0.044, 0.036, c=0.003, cy=-0.004), -0.110, 0.150, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.074, 0.004), (0.146, 0.004), (0.148, -0.044), (0.140, -0.054), (0.072, -0.054), (0.070, -0.040)], -0.025, 0.025, 'gun2', ch=0.003)
    rail(k, -0.112, 0.146, 0.0625, w=0.022, pitch=0.016, clear=[(-0.060, -0.020)])
    k.ext_y(rrect(0.052, 0.054, c=0.006, cy=bz), 0.146, 0.420, 'gun3', ch0=0.003, ch1=0.006)                 # rail handguard
    for s in (-1, 1):
        for i in range(6):
            k.box((s * 0.0260, 0.170 + i * 0.040, bz), (0.006, 0.026, 0.014), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.280, bz - 0.0285), (0.056, 0.240, 0.006), 'red')
    rail(k, 0.150, 0.412, bz + 0.0285, w=0.020, pitch=0.018, clear=[(0.380, 0.396)])
    barrel(k, 0.410, 0.520, 0.0100, bz)
    k.cbox((0, 0.540, bz), (0.030, 0.048, 0.030), 'steel2', ch=0.005, axis='y')                              # brake
    for i in range(2):
        k.box((0, 0.530 + i * 0.020, bz), (0.036, 0.010, 0.014), 'ink')
    muzzle(k, 0.566, 0.578, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # red dot on a tall riser
    k.cbox((0, -0.040, 0.074), (0.026, 0.040, 0.020), 'gunmetal', ch=0.003, axis='y')
    sz = red_dot(k, -0.040, 0.094, L=0.056, r=0.018)
    iron_front(k, 0.392, bz + 0.056, post=0.016)
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=-0.008, ptop=-0.038, grooves=2)
    k.lathe([(-0.116, 0), (-0.116, 0.015), (-0.260, 0.015), (-0.264, 0.011), (-0.264, 0)], 'steel2', 'y', (0, 0, 0.030), 8)
    k.ext_x([(-0.170, 0.056), (-0.300, 0.058), (-0.304, -0.046), (-0.282, -0.052), (-0.240, -0.014), (-0.180, 0.012)], -0.020, 0.020, 'furn', ch=0.004)
    k.ext_x([(-0.300, 0.062), (-0.316, 0.062), (-0.318, -0.050), (-0.302, -0.054)], -0.024, 0.024, 'ink')
    k.cbox((0, -0.236, 0.066), (0.030, 0.080, 0.014), 'gun3', ch=0.003, axis='y')                         # cheek riser
    mk = Kit(pal)
    mag_box(mk, 2, 0.052, -0.110, 0.058, 0.028, curve=0.010)
    return k, mk, {'rake': rake, 'mrake': 2, 'mag': (0, 0.110, -0.054), 'muzzle': (0, 0.580, bz), 'eject': (0.03, 0.052, 0.044),
                   'sight': (0, -0.040, sz), 'cls': 'rifle', 'guard': (0, 0.330, bz)}
