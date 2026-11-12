"""INKBOLT guns: launchers (no mods fit them: src/data/weapons.js noMods). Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_hothead(pal):
    """RL-3 Hothead: a fat comic rocket tube on a pistol-grip frame. Flared red muzzle bell, venturi exhaust, hazard
    rings, flip-up ring sights, a caged element canister on the left (the game lights its core in the element's
    colour at the ELEM socket) and a 3-rocket cassette (the Mag) under the tube."""
    rake = 18
    k = Kit(pal)
    bz, R = 0.074, 0.046
    k.lathe([(-0.262, 0), (-0.262, R - 0.006), (-0.254, R), (0.296, R), (0.296, 0)], 'gun3', 'y', (0, 0, bz), 16)        # tube
    k.lathe([(-0.240, 0), (-0.240, 0.034), (-0.300, 0.040), (-0.336, 0.054), (-0.344, 0.054), (-0.344, 0.045), (-0.304, 0.030), (-0.304, 0)],
            'gunmetal', 'y', (0, 0, bz), 14, bands=[None, None, None, None, 'ink', 'ink', 'ink'])                            # venturi
    k.lathe([(0.286, 0), (0.286, 0.051), (0.326, 0.055), (0.366, 0.063), (0.378, 0.063), (0.378, 0.051), (0.334, 0.040), (0.334, 0)],
            'red', 'y', (0, 0, bz), 16, bands=[None, None, None, None, 'ink', 'ink', 'ink'])                                 # muzzle bell
    for y in (0.196, 0.226, -0.214):
        k.ring('y', (0, 0, bz), y, y + 0.016, R - 0.010, R + 0.0045, 'trim', seg=16, hull=False)
    k.ring('y', (0, 0, bz), 0.150, 0.162, R - 0.010, R + 0.0040, 'ink', seg=16, hull=False)
    # caged element canister (left side): dark core, three bars, two end caps; ELEM socket at its centre
    cx, cz = -(R + 0.010), bz - 0.004
    k.lathe([(-0.082, 0), (-0.082, 0.023), (-0.066, 0.023), (-0.066, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(0.066, 0), (0.066, 0.023), (0.082, 0.023), (0.082, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(-0.068, 0), (-0.068, 0.008), (0.068, 0.008), (0.068, 0)], 'ink', 'y', (cx, 0, cz), 8, hull=False)
    for a in (100, 180, 260):
        aa = D(a)
        k.cbox((cx + 0.0168 * math.cos(aa), 0.0, cz + 0.0168 * math.sin(aa)), (0.004, 0.134, 0.004), 'steel2', ch=0, hull=True)
    k.cbox((cx + 0.010, 0.0, cz), (0.014, 0.120, 0.014), 'gunmetal', ch=0.002, axis='y', hull=False)                    # saddle onto the tube
    # sights: rear aperture, front ring on posts
    zs = bz + R + 0.028
    k.cbox((0, -0.150, 0.12825), (0.022, 0.032, 0.0245), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.156, -0.148, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.cbox((0, 0.120, 0.1278), (0.012, 0.018, 0.0235), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.116, 0.124, 0.0120, 0.0165, 'trim', seg=12, hull=True)
    # arming lever (rear left) and a shoulder pad under the rear of the tube
    k.cbox((-0.034, -0.110, bz - 0.040), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    k.cbox((0, -0.190, 0.025), (0.034, 0.090, 0.020), 'gun2', ch=0.005, axis='y')
    launcher_frame(k, rake, 0.205, 0.024)
    stripe(k, -0.020, 0.090, 0.012, 0.018, 0.023)
    # 3-rocket cassette: box with three red warheads peeking out of its nose
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.026), (0.046, 0.074, 0.070), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.022), (0.052, 0.056, 0.012), 'trim')
    mk.cbox((0, 0.0, -0.064), (0.052, 0.082, 0.010), 'gun3', ch=0.003, axis='z')
    for i in (-1, 0, 1):
        mk.lathe([(0.030, 0), (0.030, 0.0062), (0.044, 0.0058), (0.052, 0)], 'red', 'y', (i * 0.0140, 0, -0.044), 8, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.384, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.165, zs), 'elem': (cx, 0.0, cz), 'cls': 'rocket', 'fore': (0.205, 0.024)}


def build_murmur(pal):
    """ML-6 Murmur: a shoulder-fired six-pack homing launcher. Two rows of three launch tubes bundled by steel straps,
    red warhead noses poking out of the front rims, flared venturis at the back (rear blast venting), a lock-on
    targeting unit with a seeker lens and whip antenna up top-left, ring sights on the centre line, the Hothead's
    pistol-grip frame + foregrip, and a missile cassette (the Mag) under the bundle with its warheads showing."""
    rake = 18
    k = Kit(pal)
    bz, R, dx, dz = 0.076, 0.018, 0.042, 0.021
    tubes = [(x, bz + z) for z in (-dz, dz) for x in (-dx, 0.0, dx)]
    for x, z in tubes:
        k.lathe([(-0.150, 0), (-0.150, R), (0.252, R), (0.256, R + 0.0028), (0.274, R + 0.0028), (0.274, 0.0150),
                 (0.262, 0.0150), (0.262, 0)], 'gun3', 'y', (x, 0, z), 6,
                bands=[None, None, 'gunmetal', 'gunmetal', 'gunmetal', 'ink', 'ink'])                                  # tube + front rim
        k.lathe([(0.250, 0.0140), (0.280, 0.0128), (0.300, 0)], 'red', 'y', (x, 0, z), 6, hull=False)       # warhead nose
        k.lathe([(-0.140, 0.0150), (-0.176, R + 0.0028), (-0.176, 0.0110), (-0.160, 0)],
                'steel2', 'y', (x, 0, z), 6, bands=[None, None, 'ink'], hull=False)                              # venturi
    for y, w in ((0.230, 0.020), (-0.132, 0.020)):                                                             # bundle straps
        k.cbox((0, y, bz), (2 * (dx + R) + 0.012, w, 2 * (dz + R) + 0.012), 'gunmetal', ch=0.004, axis='y')
    for y in (0.176, -0.090):                                                                                                  # hazard bands
        k.box((0, y, bz), (2 * (dx + R) + 0.006, 0.012, 2 * (dz + R) + 0.006), 'trim')
    k.cbox((0, 0.040, 0.034), (0.100, 0.300, 0.012), 'gun2', ch=0.003, axis='y')                                              # saddle onto the frame
    # lock-on targeting unit (top left): housing on a mount, seeker lens + ring, lock LED, whip antenna
    tx, ty, tz = -0.054, 0.080, 0.140
    k.cbox((tx + 0.006, ty, 0.118), (0.020, 0.050, 0.012), 'gun2', ch=0.002, axis='y')
    k.cbox((tx, ty, tz), (0.034, 0.096, 0.036), 'gun2', ch=0.004, axis='y')
    k.ring('y', (tx, 0, tz), ty + 0.046, ty + 0.058, 0.0100, 0.0150, 'gunmetal', seg=6)
    k.lathe([(ty + 0.046, 0), (ty + 0.046, 0.0102), (ty + 0.052, 0.0080), (ty + 0.055, 0)], 'lens', 'y', (tx, 0, tz), 6, hull=False)
    k.box((tx - 0.0185, ty - 0.010, tz + 0.006), (0.004, 0.030, 0.008), 'trim')
    k.cbox((tx + 0.004, ty - 0.020, tz + 0.020), (0.010, 0.010, 0.008), 'red', ch=0.002)
    k.bar((tx - 0.008, ty - 0.040, tz + 0.016), (tx - 0.008, ty - 0.040, tz + 0.062), 0.004, 0.004, 'ink', hull=False)
    # sights on the centre line (rear aperture, front ring)
    zs = 0.120 + 0.024
    k.cbox((0, -0.120, 0.12575), (0.022, 0.028, 0.0235), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.126, -0.118, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.cbox((0, 0.240, 0.12625), (0.012, 0.016, 0.0205), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.236, 0.244, 0.0110, 0.0155, 'trim', seg=12, hull=True)
    # arming lever (rear left, under the bundle) and a shoulder pad
    k.cbox((-0.034, -0.110, 0.030), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    k.cbox((0, -0.190, 0.025), (0.034, 0.090, 0.020), 'gun2', ch=0.005, axis='y')
    launcher_frame(k, rake, 0.200, 0.026)
    stripe(k, -0.020, 0.090, 0.012, 0.018, 0.023)
    # missile cassette: a flat box with an amber label band, three warheads peeking out of its nose
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.022), (0.050, 0.080, 0.064), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.024), (0.056, 0.060, 0.014), 'trim')
    for i in (-1, 1):
        mk.box((0, i * 0.018, -0.024), (0.062, 0.006, 0.020), 'ink')
    mk.cbox((0, 0.0, -0.058), (0.056, 0.086, 0.010), 'gun3', ch=0.003, axis='z')
    for i in (-1, 0, 1):
        mk.lathe([(0.034, 0), (0.034, 0.0062), (0.054, 0)], 'red', 'y', (i * 0.0150, 0, -0.042), 6, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.300, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.135, zs), 'cls': 'rocket', 'fore': (0.200, 0.026)}
