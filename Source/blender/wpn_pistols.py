"""INKBOLT guns: pistols. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_pip(pal):
    """P-12 Warden: chunky service pistol."""
    rake = 16
    k = Kit(pal)
    k.ext_y(rrect(0.047, 0.046, ct=0.009, cb=0.003, cy=0.029), -0.086, 0.150, 'gunmetal', ch0=0.004, ch1=0.010)   # slide
    for side in (-1, 1):
        sk = ('-x' if side > 0 else '+x',)
        for i in range(4):
            k.box((side * 0.0245, -0.076 + i * 0.0085, 0.028), (0.006, 0.004, 0.026), 'ink', skip=sk)     # rear serrations
        for i in range(2):
            k.box((side * 0.0245, 0.108 + i * 0.0085, 0.030), (0.006, 0.004, 0.020), 'ink', skip=sk)      # front serrations
    k.box((0.01525, 0.024, 0.0455), (0.0225, 0.050, 0.019), 'ink')             # ejection port (right top)
    k.box((0.012, 0.022, 0.0555), (0.010, 0.040, 0.006), 'steel')              # barrel hood in the port
    muzzle(k, 0.143, 0.1615, 0.0115, 0.030, rb=0.006, hull=False)              # barrel crown
    stripe(k, -0.040, 0.094, 0.010, 0.016, 0.0265)
    for s in (-1, 1):                                                          # rear sight ears, white dots
        k.box((s * 0.0095, -0.066, 0.056), (0.010, 0.013, 0.016), 'ink', hull=True)
        k.box((s * 0.0095, -0.0735, 0.0595), (0.004, 0.004, 0.004), 'paper')
    k.box((0, 0.134, 0.054), (0.0075, 0.012, 0.014), 'ink', hull=True)          # front post + red fibre
    k.box((0, 0.1265, 0.0585), (0.004, 0.004, 0.004), 'red')
    k.ext_y(rrect(0.041, 0.024, c=0.003, cy=-0.001), -0.074, 0.134, 'gun2', ch1=0.008)   # polymer frame
    for i in range(3):
        k.box((0, 0.088 + i * 0.012, -0.0105), (0.047, 0.005, 0.013), 'ink')    # dust-cover rail slots
    k.xbar(-0.005, 0.005, [(-0.084, 0.006), (-0.093, 0.020), (-0.097, 0.034), (-0.090, 0.037), (-0.080, 0.016)], 'steel2', ch=0)  # hammer
    k.xbar(-0.0265, -0.0225, [(0.002, 0.000), (0.042, 0.000), (0.046, 0.006), (0.040, 0.009), (0.004, 0.006)], 'gun3', ch=0, hull=False)  # slide stop
    k.pin(-0.0235, 0.0235, 0.060, -0.004, 0.0028)
    k.pin(-0.0235, 0.0235, -0.050, 0.000, 0.0026)
    for i in range(2):                                                         # lightening cuts on the slide top
        k.box((0, 0.070 + i * 0.024, 0.052), (0.016, 0.016, 0.006), 'ink', skip=('-z',))
    k.box((0, -0.0865, 0.028), (0.024, 0.005, 0.024), 'gun3')                  # slide rear plate
    k.box((0.02375, 0.003, 0.030), (0.0055, 0.014, 0.006), 'steel')            # extractor
    k.box((-0.0225, 0.012, -0.006), (0.006, 0.008, 0.008), 'gun3')             # mag release
    k.box((-0.0235, 0.052, -0.0015), (0.004, 0.008, 0.009), 'gun3')            # takedown lever
    trigger_guard(k, rake, front=0.084, depth=-0.046)
    trigger(k, rake)
    grip(k, rake, 'pistol')
    my, mz = g2w(rake, HAND['cy'], -0.100)
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, 0.0, 0.040, 0.025, plate='gunmetal', plate_h=0.011, plate_w=0.041, ribs=False)
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.164, 0.030), 'eject': (0.03, 0.025, 0.048),
                   'sight': (0, -0.090, 0.062), 'cls': 'pistol'}


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
