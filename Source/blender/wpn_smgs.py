"""INKBOLT guns: SMGs. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_buzz(pal):
    """KV-9 Buzzsaw: boxy all-round SMG, reflex sight, vertical foregrip, skeleton stock, straight mag."""
    rake = 14
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.048, 0.060, ct=0.009, cb=0.004, cy=0.038), -0.096, 0.140, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    rail(k, -0.090, 0.132, 0.068, w=0.022, clear=[(-0.078, -0.036)])
    hz = hood_sight(k, -0.076, -0.038, 0.071)
    k.box((0.0155, 0.040, 0.050), (0.023, 0.050, 0.016), 'ink')                     # port
    k.box((0.0285, 0.036, 0.050), (0.005, 0.030, 0.010), 'steel')                   # bolt face in the port
    k.ext_y(rrect(0.040, 0.026, c=0.003, cy=0.005), -0.070, 0.124, 'gun2', ch0=0.004, ch1=0.004)                 # trigger housing
    stripe(k, -0.070, 0.110, 0.022, 0.028, 0.0270)
    # charging tube (left, HK style) with knob
    k.lathe([(0.020, 0), (0.020, 0.0065), (0.170, 0.0065), (0.170, 0)], 'gun3', 'y', (-0.025, 0, 0.060), 8, hull=False)
    k.cbox((-0.036, 0.150, 0.060), (0.016, 0.010, 0.010), 'ink', ch=0.002, hull=False)
    # shroud with vents, barrel, birdcage
    k.ext_y(rrect(0.044, 0.044, ct=0.006, cb=0.010, cy=0.030), 0.136, 0.214, 'gun2', ch1=0.006)
    for s in (-1, 1):
        for i in range(3):
            k.box((s * 0.0225, 0.152 + i * 0.020, 0.030), (0.006, 0.010, 0.018), 'ink', skip=('-x' if s > 0 else '+x',))
    barrel(k, 0.205, 0.246, 0.0090, bz)
    muzzle(k, 0.246, 0.280, 0.0115, bz, ports=2, rb=0.0055, seg=8)
    k.box((0, 0.200, 0.064), (0.006, 0.008, 0.016), 'ink', hull=True)               # front post
    # magwell, vertical foregrip, trigger group, grip
    k.ext_x([(0.066, 0.010), (0.118, 0.010), (0.120, -0.030), (0.114, -0.038), (0.066, -0.038), (0.062, -0.026)], -0.0225, 0.0225, 'gun2', ch=0.003)
    vgrip(k, 0.180, 0.010, seg=8)
    trigger_guard(k, rake, front=0.062, depth=-0.046, hook=False, top=0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=0.010, ptop=-0.028, grooves=2)
    k.xbar(-0.0275, -0.0240, [(-0.052, 0.010), (-0.032, 0.008), (-0.030, 0.016), (-0.050, 0.018)], 'gun3', ch=0, hull=False)   # selector
    k.pin(-0.0270, 0.0270, -0.080, 0.012, 0.003)
    # skeleton stock (extended): top bar, sloped lower strut, butt plate
    k.box((0, -0.170, 0.050), (0.016, 0.160, 0.014), 'furn', hull=True)
    k.bar((0, -0.100, 0.004), (0, -0.240, -0.030), 0.014, 0.012, 'furn', hull=True)
    k.ext_x([(-0.236, 0.062), (-0.256, 0.062), (-0.258, -0.044), (-0.238, -0.044)], -0.019, 0.019, 'ink', ch=0.003)
    k.box((0, -0.244, 0.010), (0.044, 0.008, 0.050), 'gun3')
    mk = Kit(pal)
    mag_box(mk, 2, 0.034, -0.150, 0.040, 0.026, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 2, 'mag': (0, 0.092, -0.038), 'muzzle': (0, 0.282, bz), 'eject': (0.03, 0.040, 0.050),
                   'sight': (0, -0.100, hz), 'cls': 'smg', 'fore': (0.180, 0.010)}


def build_whisk(pal):
    """KV-4 Whiplash: compact machine pistol, mag in the grip, long suppressor can, wire stock."""
    rake = 8
    k = Kit(pal)
    bz = 0.032
    k.ext_y(rrect(0.044, 0.064, ct=0.010, cb=0.004, cy=0.026), -0.078, 0.110, 'gunmetal', ch0=0.005, ch1=0.012)   # receiver
    rail(k, -0.075, 0.096, 0.058, w=0.022, clear=[(-0.070, -0.050)])
    k.cbox((0, -0.060, 0.064), (0.024, 0.016, 0.012), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, 0.0755), -0.063, -0.057, 0.003, 0.0065, 'gunmetal', seg=8, hull=False)
    k.box((0.0135, 0.020, 0.046), (0.0225, 0.040, 0.014), 'ink')                       # port
    k.cbox((0, -0.086, 0.050), (0.040, 0.010, 0.010), 'gun3', ch=0.002, axis='x')     # T charging handle
    for s in (-1, 1):
        k.box((s * 0.0235, 0.040, 0.010), (0.006, 0.050, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    # suppressor can: gun3 with one amber band (the accent stripe), recessed bore
    L0, L1, r = 0.106, 0.270, 0.0205
    k.lathe([(L0, 0), (L0, r - 0.004), (L0 + 0.006, r), (0.180, r), (0.180, r + 0.003), (0.202, r + 0.003), (0.202, r), (L1 - 0.004, r),
             (L1, r - 0.004), (L1, 0.006), (L1 - 0.010, 0.006), (L1 - 0.010, 0)], 'gun3', 'y', (0, 0, bz), 12,
            bands=[None, None, None, 'trim', 'trim', 'trim', None, None, None, 'ink', 'ink'])
    for i in range(3):
        k.box((0, 0.230 + i * 0.012, bz + r - 0.0005), (0.010, 0.004, 0.007), 'ink', skip=('-z',))
    k.box((0, 0.216, bz + r + 0.010), (0.005, 0.008, 0.024), 'ink', hull=True)       # front post on the can (on the sight line)
    # folding vertical foregrip, grip (mag well), guard
    vgrip(k, 0.088, -0.006, length=0.060, r=0.014)
    trigger_guard(k, rake, front=0.064, depth=-0.046, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.036, top=0.000, bottom=-0.096, ptop=-0.024)
    # wire stock (collapsed): two rods + butt plate
    for s in (-1, 1):
        k.lathe([(-0.150, 0), (-0.150, 0.004), (-0.074, 0.004), (-0.074, 0)], 'steel', 'y', (s * 0.016, 0, 0.012), 6, hull=True)
    k.ext_x([(-0.146, 0.040), (-0.160, 0.040), (-0.162, -0.034), (-0.148, -0.030)], -0.022, 0.022, 'furn', ch=0.003)
    k.box((0, -0.153, -0.022), (0.050, 0.008, 0.010), 'ink')
    my, mz = g2w(rake, HAND['cy'], -0.096)
    mk = Kit(pal)
    mag_box(mk, rake, 0.080, -0.062, 0.040, 0.025, plate='gun3', plate_w=0.043, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.004, -0.030)
        mk.box((s * 0.0125, y, z), (0.008, 0.020, 0.036), 'gun3', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.272, bz), 'eject': (0.03, 0.020, 0.046),
                   'sight': (0, -0.072, 0.0755), 'cls': 'smg', 'fore': (0.088, -0.006)}


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
