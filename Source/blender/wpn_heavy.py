"""INKBOLT guns: LMG, sniper and rail rifle. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_brick(pal):
    """LMG-26 Bricklayer: heavy LMG, feed cover, carry handle, perforated heat shield, folded bipod, brick ammo box."""
    rake = 20
    k = Kit(pal)
    bz = 0.044
    k.ext_y(rrect(0.058, 0.082, ct=0.010, cb=0.004, cy=0.040), -0.130, 0.155, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.ext_y(rrect(0.050, 0.012, ct=0.004, cb=0.0, cy=0.0855), -0.110, 0.130, 'gun3', ch0=0.004, ch1=0.004)       # feed cover
    k.pin(-0.028, 0.028, 0.124, 0.086, 0.004, color='steel2')
    k.ext_y(rrect(0.046, 0.030, c=0.003, cy=-0.006), -0.090, 0.090, 'gun2', ch0=0.004, ch1=0.004)                  # trigger housing
    k.cbox((0, -0.118, 0.090), (0.034, 0.010, 0.010), 'ink', ch=0.002, axis='x', hull=False)                       # cover latch
    for i in range(4):
        k.box((0, -0.080 + i * 0.044, 0.0935), (0.040, 0.010, 0.004), 'ink', skip=('-z',))
    k.ext_x([(-0.090, 0.090), (-0.070, 0.090), (-0.070, 0.112), (-0.078, 0.114), (-0.090, 0.100)], -0.012, 0.012, 'gunmetal')  # leaf sight
    k.box((0, -0.080, 0.111), (0.004, 0.012, 0.006), 'ink')
    stripe(k, -0.110, 0.100, 0.010, 0.017, 0.0320)
    for s in (-1, 1):
        k.screw((s * 0.029, -0.100, 0.060), (s, 0, 0))
    k.box((0.021, 0.020, 0.048), (0.022, 0.060, 0.018), 'ink')                                       # port
    k.cbox((0.036, -0.010, 0.030), (0.012, 0.014, 0.012), 'gun3', ch=0.002, hull=False)               # charging handle
    # barrel, heat shield with holes, gas tube, forend, carry handle, flash hider, front post
    barrel(k, 0.118, 0.466, 0.0120, bz, seg=12)
    hs = [(-0.022, bz - 0.002), (-0.020, bz + 0.012), (-0.010, bz + 0.022), (0.010, bz + 0.022), (0.020, bz + 0.012), (0.022, bz - 0.002),
          (0.017, bz - 0.002), (0.015, bz + 0.009), (0.007, bz + 0.016), (-0.007, bz + 0.016), (-0.015, bz + 0.009), (-0.017, bz - 0.002)]
    k.ext_y(hs, 0.180, 0.400, 'gun2', ch0=0.0, ch1=0.0)
    for i in range(5):
        k.box((0, 0.196 + i * 0.044, bz + 0.0235), (0.012, 0.014, 0.006), 'ink', skip=('-z',))
    k.lathe([(0.156, 0), (0.156, 0.008), (0.380, 0.008), (0.380, 0)], 'steel2', 'y', (0, 0, 0.012), 8, hull=True)    # gas tube
    k.ext_y(rrect(0.046, 0.034, ct=0.006, cb=0.010, cy=0.012), 0.152, 0.300, 'gun2', ch1=0.006)                      # forend
    for s in (-1, 1):
        for i in range(2):
            k.box((s * 0.0235, 0.180 + i * 0.056, 0.010), (0.006, 0.024, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    k.tube([((0, 0.190, bz + 0.010), 0.012, 0.010), ((0, 0.200, bz + 0.052), 0.012, 0.010), ((0, 0.280, bz + 0.052), 0.012, 0.010),
            ((0, 0.290, bz + 0.010), 0.012, 0.010)], 'gun3', sides=6, up=(1, 0, 0))
    k.lathe([(0.466, 0), (0.466, 0.0140), (0.500, 0.0175), (0.512, 0.0175), (0.512, 0.0080), (0.500, 0.0080), (0.500, 0)], 'steel', 'y', (0, 0, bz), 12,
            bands=[None, None, None, None, 'ink', 'ink'])
    for i in range(4):
        a = D(45 + 90 * i)
        k.box((0.0185 * math.cos(a), 0.496, bz + 0.0185 * math.sin(a)), (0.006, 0.020, 0.006), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    k.box((0, 0.452, bz + 0.040), (0.006, 0.010, 0.056), 'ink', hull=True)       # tall front post, level with the leaf
    bipod_folded(k, 0.290, 0.440, 0.008, x=0.016)
    k.ring('y', (0, 0, bz), 0.420, 0.432, 0.010, 0.0165, 'steel2', seg=10, hull=False)
    trigger_guard(k, rake, front=0.056, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    # stock: solid with butt plate, buffer ridge
    k.ext_x([(-0.126, 0.072), (-0.320, 0.064), (-0.322, -0.046), (-0.296, -0.050), (-0.180, -0.004), (-0.126, 0.006)], -0.022, 0.022, 'furn', ch=0.005)
    k.ext_x([(-0.318, 0.070), (-0.336, 0.070), (-0.338, -0.050), (-0.320, -0.054)], -0.0265, 0.0265, 'ink', ch=0.003)
    k.box((0, -0.220, 0.040), (0.050, 0.120, 0.006), 'gun3')
    # brick ammo box (the Mag): ribs, lid, feed chute with rounds
    mk = Kit(pal)
    mk.cbox((0, 0, -0.050), (0.064, 0.090, 0.088), 'gun3', ch=0.005, axis='z')
    mk.cbox((0, 0, -0.098), (0.070, 0.096, 0.010), 'gun2', ch=0.003, axis='z')
    mk.box((0, 0, -0.003), (0.054, 0.076, 0.008), 'gun2')
    for s in (-1, 1):
        for j in range(2):
            mk.box((s * 0.0335, -0.018 + j * 0.036, -0.052), (0.006, 0.008, 0.070), 'gun2', skip=('-x' if s > 0 else '+x',))
        mk.box((s * 0.0360, 0, -0.010), (0.006, 0.030, 0.010), 'ink', skip=('-x' if s > 0 else '+x',))
    mk.cbox((-0.046, 0.0, 0.004), (0.020, 0.040, 0.034), 'gun2', ch=0.003, rot=(0, -25, 0))
    for i in range(2):
        mk.lathe([(-0.012, 0), (-0.012, 0.0055), (0.010, 0.0055), (0.018, 0.0030), (0.018, 0)], 'brass', 'y', (-0.020 + i * 0.010, 0.0, 0.009 + i * 0.002), 6, hull=False)
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
