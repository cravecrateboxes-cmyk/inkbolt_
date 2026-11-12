"""INKBOLT guns: shotguns. Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def build_scrapper(pal):
    """SG-9 Scrapper: pump shotgun. Tube magazine under the barrel; the pump forend is the 'Mag' part (it slides on
    the tube when the gun is worked); shells go in through the loading port under the receiver."""
    rake = 20
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.046, 0.058, ct=0.010, cb=0.004, cy=0.036), -0.110, 0.120, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.box((0.0225, 0.020, 0.044), (0.008, 0.070, 0.022), 'ink', skip=('-x',))                                   # ejection port
    k.box((0.0, 0.052, 0.0045), (0.024, 0.080, 0.006), 'ink')                                                 # loading port
    k.box((0, 0.052, -0.0005), (0.016, 0.056, 0.006), 'red')                                                  # shell lifter
    stripe(k, -0.100, 0.100, 0.012, 0.019, 0.0265)
    k.ext_y(rrect(0.040, 0.020, c=0.003, cy=-0.004), -0.080, 0.002, 'gunmetal', ch0=0.004, ch1=0.004)        # trigger plate: body colour, so it flows into the receiver
    barrel(k, 0.118, 0.560, 0.0125, bz + 0.004, seg=12)
    k.lathe([(0.118, 0), (0.118, 0.0100), (0.500, 0.0100), (0.500, 0)], 'steel2', 'y', (0, 0, bz - 0.024), 10)    # magazine tube
    k.cbox((0, 0.506, bz - 0.012), (0.034, 0.016, 0.048), 'gunmetal', ch=0.004, axis='y')                     # tube cap / barrel clamp
    muzzle(k, 0.556, 0.574, 0.0162, bz + 0.004, rb=0.0095, seg=12)
    k.ext_y(rrect(0.010, 0.006, c=0.002, cy=bz + 0.019), 0.130, 0.546, 'ink')                                # vent rib
    k.cbox((0, 0.548, bz + 0.026), (0.006, 0.006, 0.008), 'red', ch=0.0015)                                   # bead sight
    sz = iron_rear(k, -0.070, 0.066, w=0.026, h=0.010)
    trigger_guard(k, rake, front=0.066, depth=-0.048, w=0.012, top=-0.010, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=-0.006, ptop=-0.036, grooves=2)
    k.pin(-0.0295, 0.0295, -0.060, 0.012, 0.003)
    k.pin(-0.0295, 0.0295, 0.090, 0.012, 0.003)
    # stock: wood-tone polymer with a recoil pad
    k.ext_x([(-0.106, 0.064), (-0.330, 0.050), (-0.332, -0.050), (-0.300, -0.056), (-0.160, -0.004), (-0.106, 0.010)], -0.021, 0.021, 'furn', ch=0.005)
    k.ext_x([(-0.328, 0.056), (-0.348, 0.056), (-0.350, -0.056), (-0.330, -0.060)], -0.025, 0.025, 'ink', ch=0.003)
    for i in range(3):
        k.box((0, -0.200 - i * 0.030, 0.0560 - i * 0.002), (0.050, 0.010, 0.006), 'gun3')
    # the pump (Mag part): ribbed forend round the tube, origin = its rear end on the tube axis
    mk = Kit(pal)
    mk.ext_y(rrect(0.046, 0.040, c=0.010, cy=0.002), 0.0, 0.130, 'gun2', ch0=0.006, ch1=0.006)
    for i in range(6):
        mk.box((0, 0.020 + i * 0.018, -0.0185), (0.050, 0.008, 0.006), 'ink')
    for s in (-1, 1):
        mk.box((s * 0.0235, 0.065, 0.006), (0.006, 0.090, 0.008), 'gun3', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.300, bz - 0.024), 'muzzle': (0, 0.576, bz + 0.004), 'eject': (0.03, 0.020, 0.050),
                   'sight': (0, -0.070, sz), 'cls': 'shotgun', 'guard': (0, 0.365, bz - 0.022), 'port': (0, 0.052, -0.004)}   # pump: palm under the forend


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
