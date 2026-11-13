"""INKBOLT guns: launchers (no mods fit them: src/data/weapons.js noMods). Built by fam_weapons.py (GUNS); shared parts in wpn_core.py."""
from wpn_core import *  # noqa: F401,F403


def grooves(k, y0, y1, r, z, n=3, x=0.0, color='ink', seg=10, fill=0.44, axis='y', c=None):
    """n dark grip rings around a cylinder of radius r (open bands, no inner faces)"""
    pitch = (y1 - y0) / n
    for i in range(n):
        yc = y0 + pitch * (i + 0.5)
        k.lathe([(yc - pitch * fill / 2, r - 0.001), (yc - pitch * fill / 2, r + PR), (yc + pitch * fill / 2, r + PR), (yc + pitch * fill / 2, r - 0.001)],
                color, axis, c or (x, 0, z), seg, hull=False, caps=(False, False))


def band(k, y0, y1, r, t, color, c, seg=16, hull=False):
    """clamp band / sleeve standing t proud of a tube of radius r around the y axis through c (open: no inner faces)"""
    return k.lathe([(y0, r - 0.001), (y0, r + t), (y1, r + t), (y1, r - 0.001)], color, 'y', c, seg, hull=hull, caps=(False, False))


def studs(k, hw, pts, sides=(-1, 1), r=0.0028):
    """dome rivets at side-profile points [(y, z)] on the side faces of a body of half-width hw"""
    for s in sides:
        for y, z in pts:
            bolt(k, (s * hw, y, z), (s, 0, 0), r, 0.0022, socket=False)


def radial(k, ang, c):
    """local frame for a blade in the plane through the barrel axis: local x points outward at `ang` degrees
    (0 = right, 90 = up), y stays along the barrel; use k.ext(prof_yr, color, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -t, t)"""
    return k.at(c, (0, -ang, 0))


def build_hothead(pal):
    """RL-3 Hothead: shoulder-fired rocket tube on a pistol-grip frame. Banded and clamped tube with a ribbed heat
    guard, a finned venturi and a flared muzzle bell, hazard bands, flip-up ring sights either side of an optic rail,
    a carrying handle, a shoulder rest, the firing mechanism with its safety on the frame, a caged element canister on
    the left with its valve and hose (the game lights its core in the element's colour at the ELEM socket) and a
    3-rocket cassette (the Mag) under the tube.
    Rarity layers: Rare bolts on a bell guard, a rangefinder, a sling and a rocket counter; Epic lights the venturi
    and bell throats, wraps a coil in front of the clamp and runs a conduit from an energy cell; Legendary (obsidian)
    crowns the bell with shards, opens a row of molten vents along the tube and cracks it with lava."""
    rake = 18
    k = Kit(pal)
    bz, R = 0.074, 0.046
    C = (0, 0, bz)
    AP = R * math.cos(math.pi / 16)                 # the 16-sided tube has flat facets at the sides (x = +-AP) and on top
    # ---- tube, venturi with fins, muzzle bell
    k.lathe([(-0.262, 0), (-0.262, R - 0.006), (-0.254, R), (0.296, R), (0.296, 0)], 'gun3', 'y', C, 16)
    k.lathe([(-0.240, 0), (-0.240, 0.034), (-0.300, 0.040), (-0.336, 0.054), (-0.344, 0.054), (-0.344, 0.045), (-0.304, 0.030), (-0.304, 0)],
            'gunmetal', 'y', C, 14, bands=[None, None, None, None, 'ink', 'ink', 'ink'])
    for i in range(4):
        with radial(k, 45 + 90 * i, C):
            k.ext([(-0.262, 0.0370), (-0.300, 0.0385), (-0.334, 0.0520), (-0.334, 0.0610), (-0.300, 0.0500), (-0.264, 0.0475)], 'gunmetal',
                  (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0020, 0.0020)
    k.lathe([(0.286, 0), (0.286, 0.051), (0.326, 0.055), (0.366, 0.063), (0.378, 0.063), (0.378, 0.051), (0.334, 0.040), (0.334, 0)],
            'red', 'y', C, 16, bands=[None, None, None, None, 'ink', 'ink', 'ink'])
    for i in range(4):
        with radial(k, 90 * i, C):
            k.ext([(0.290, 0.0500), (0.326, 0.0545), (0.364, 0.0625), (0.364, 0.0655), (0.326, 0.0580), (0.290, 0.0540)], 'gunmetal',
                  (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0020, 0.0020, hull=False)
    # ---- clamps, hazard bands, heat guard
    band(k, 0.262, 0.284, R, 0.0045, 'gunmetal', C, hull=True)
    band(k, 0.150, 0.166, R, 0.0045, 'gunmetal', C, hull=True)
    for y in (0.273, 0.158):
        studs(k, (R + 0.0045) * math.cos(math.pi / 16), [(y, bz)], r=0.0034)
    band(k, 0.190, 0.242, R, 0.0030, 'body2', C)
    band(k, 0.1975, 0.2025, R, 0.0045, 'trim', C)
    band(k, 0.2295, 0.2345, R, 0.0045, 'trim', C)
    hazard(k, (R + 0.0030) * math.cos(math.pi / 16), 0.206, 0.224, bz - 0.0075, bz + 0.0075, n=3)
    band(k, -0.2170, -0.1985, R, 0.0030, 'body2', C)
    band(k, -0.2100, -0.2055, R, 0.0045, 'trim', C)
    band(k, -0.192, -0.062, R, 0.0055, 'furn', C, hull=True)
    grooves(k, -0.192, -0.066, R + 0.0055, bz, n=3, seg=16)
    stencil(k, 'DANGER', (R + 0.0055) * math.cos(math.pi / 16), -0.149, bz - 0.003, cap=0.006, font='cond')
    with k.at(C, (0, -22.5, 0)):                                                                                  # optical sight bracket and its thumb screw
        k.cbox((0, 0.020, AP + 0.0030), (0.012, 0.060, 0.008), 'steel2', ch=0.002, axis='y')
        for y in (0.000, 0.040):
            bolt(k, (0, y, AP + 0.0070), (0, 0, 1), 0.0026, 0.0022, socket=False)
        k.lathe([(0.004, 0.0050), (0.012, 0.0050), (0.012, 0)], 'gun3', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))), (0, 0.020, AP + 0.0030), 6, hull=False,
                caps=(False, True))
    # ---- optic rail, ring sights, carrying handle
    rail(k, -0.056, 0.104, bz + AP, w=0.016, pitch=0.012)
    zs = bz + R + 0.028
    k.cbox((0, -0.150, 0.12825), (0.022, 0.032, 0.0245), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.156, -0.148, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.pin(-0.0150, 0.0150, -0.140, 0.1330, 0.0030, color='steel2')
    k.cbox((0, 0.120, 0.1278), (0.012, 0.018, 0.0235), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.116, 0.124, 0.0120, 0.0165, 'trim', seg=12, hull=True)
    k.pin(-0.0100, 0.0100, 0.120, 0.1270, 0.0026, color='steel2')
    with k.at(C, (0, 45, 0)):
        for y in (0.010, 0.100):
            k.cbox((0, y, R + 0.0040), (0.016, 0.014, 0.012), 'steel2', ch=0.002, axis='y', hull=False)
        k.tube([((0, 0.010, R + 0.006), 0.010, 0.009), ((0, 0.022, R + 0.030), 0.010, 0.009), ((0, 0.088, R + 0.030), 0.010, 0.009),
                ((0, 0.100, R + 0.006), 0.010, 0.009)], 'gun2', sides=6, up=(1, 0, 0))
        k.lathe([(0.030, 0), (0.030, 0.0072), (0.080, 0.0072), (0.080, 0)], 'rubber', 'y', (0, 0, R + 0.030), 8)
    # ---- stencils: model name and backblast chevrons (right), model code (left)
    stencil(k, 'RL-3 HOTHEAD', AP, 0.058, bz - 0.0050, cap=0.010, sides=(1,))
    stencil(k, 'RL-3', AP, 0.122, bz - 0.0055, cap=0.011, sides=(-1,))
    for i in range(3):
        y = -0.056 + i * 0.014
        plate(k, [(y, bz), (y + 0.007, bz + 0.0070), (y + 0.011, bz + 0.0070), (y + 0.004, bz), (y + 0.011, bz - 0.0070), (y + 0.007, bz - 0.0070)], AP, 'mark',
              ch=0, sides=(1,))
    # ---- caged element canister (left): caps with strap bands, bars, valve and hose; ELEM socket at its centre
    cx, cz = -(R + 0.010), bz - 0.004
    k.lathe([(-0.082, 0), (-0.082, 0.023), (-0.066, 0.023), (-0.066, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(0.066, 0), (0.066, 0.023), (0.082, 0.023), (0.082, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(-0.068, 0), (-0.068, 0.008), (0.068, 0.008), (0.068, 0)], 'ink', 'y', (cx, 0, cz), 8, hull=False)
    for a in (100, 180, 260):
        aa = D(a)
        k.cbox((cx + 0.0168 * math.cos(aa), 0.0, cz + 0.0168 * math.sin(aa)), (0.004, 0.134, 0.004), 'steel2', ch=0, hull=True)
    k.cbox((cx + 0.010, 0.0, cz), (0.014, 0.120, 0.014), 'gunmetal', ch=0.002, axis='y', hull=False)
    for y in (-0.074, 0.074):
        band(k, y - 0.0035, y + 0.0035, 0.023, PR, 'steel2', (cx, 0, cz), seg=10)
    k.lathe([(0.080, 0), (0.080, 0.0070), (0.092, 0.0070), (0.092, 0.0110), (0.095, 0.0110), (0.095, 0)], 'steel2', 'y', (cx, 0, cz), 8, hull=False,
            bands=[None, None, 'red', 'red', 'red'])
    cable(k, [(cx, 0.089, cz + 0.006), (cx + 0.002, 0.100, cz + 0.016), (cx + 0.010, 0.110, cz + 0.022), (cx + 0.019, 0.114, cz + 0.022)], r=0.0030, clamps=(1,))
    # ---- cocking lever, shoulder rest with its pad
    k.cbox((-0.034, -0.110, bz - 0.040), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    bolt(k, (-0.040, -0.098, bz - 0.040), (-1, 0, 0), 0.0030)
    k.ext_x([(-0.146, 0.032), (-0.238, 0.032), (-0.242, 0.006), (-0.232, -0.002), (-0.222, 0.014), (-0.146, 0.016)], -0.017, 0.017, 'gun2', ch=0.003)
    k.cbox((0, -0.2425, 0.012), (0.038, 0.008, 0.030), 'rubber', ch=0.002, axis='x')
    for z in (0.004, 0.012, 0.020):
        k.box((0, -0.2445, z), (0.030, 0.007, 0.0025), 'ink')
    studs(k, 0.017, [(-0.160, 0.024), (-0.226, 0.022)], r=0.0032)
    # ---- frame: firing mechanism plates, safety with its marks, cassette guide and catch
    launcher_frame(k, rake, 0.205, 0.024)
    plate(k, [(-0.048, 0.002), (0.060, 0.002), (0.066, 0.008), (0.066, 0.027), (-0.048, 0.027)], 0.020, 'frame2')
    plate(k, rect(-0.046, 0.068, -0.0055, -0.0030), 0.020, 'trim', ch=0)
    studs(k, 0.020 + PR, [(-0.042, 0.022), (0.060, 0.022)])
    stencil(k, 'RL-3', 0.020 + PR, 0.028, 0.008, cap=0.011, sides=(1,))
    k.lathe([(0.017, 0.0050), (0.0255, 0.0050), (0.0255, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.016, 0.017), 8, hull=False, caps=(False, True))
    k.xbar(-0.0285, -0.0255, [(-0.004, 0.0125), (0.018, 0.0125), (0.020, 0.0215), (-0.002, 0.0200)], 'gun3', ch=0, hull=False)
    k.box((-0.0215 - PR / 2 + 0.0005, -0.014, 0.022), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-0.0215 - PR / 2 + 0.0005, 0.036, 0.022), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    k.cbox((0, 0.160, 0.0275), (0.022, 0.060, 0.009), 'gun2', ch=0.002, axis='y', hull=False)
    k.xbar(-0.005, 0.005, [(0.132, 0.004), (0.142, 0.004), (0.146, -0.016), (0.140, -0.018), (0.136, -0.006)], 'steel2', ch=0.001)
    studs(k, 0.020, [(0.192, 0.0275), (0.218, 0.0275)])
    # ---- 3-rocket cassette: launch cells with red warheads at the nose, exhaust ports at the back
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.026), (0.046, 0.074, 0.070), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.012), (0.046 + 2 * PR, 0.052, 0.004), 'trim')
    mk.cbox((0, 0.0, -0.064), (0.052, 0.082, 0.010), 'gun3', ch=0.003, axis='z')
    mk.box((0, 0.037 + PR / 2 - 0.0005, -0.044), (0.042, PR + 0.001, 0.017), 'ink', skip=('-y',))
    mk.box((0, -0.037 - PR / 2 + 0.0005, -0.044), (0.042, PR + 0.001, 0.017), 'ink', skip=('+y',))
    for i in (-1, 0, 1):
        mk.lathe([(0.030, 0), (0.030, 0.0062), (0.044, 0.0058), (0.052, 0)], 'red', 'y', (i * 0.0140, 0, -0.044), 8, hull=False)
        mk.lathe([(-0.0420, 0.0048), (-0.0420, 0.0030), (-0.0360, 0.0030)], 'steel2', 'y', (i * 0.0140, 0, -0.044), 6, hull=False, caps=(False, False))
    for s in (-1, 1):
        for y in (-0.024, 0.024):
            mk.box((s * (0.023 + PR / 2 - 0.0005), y, -0.036), (PR + 0.001, 0.005, 0.040), 'frame2', skip=sk(s))
    stencil(mk, 'HE-3', 0.023, 0.0, -0.036, cap=0.009)
    hazard(mk, 0.023, -0.018, 0.014, -0.054, -0.048, n=4)

    # ---- Rare (and up): bell guard, rangefinder with its cable, sling, rocket counter
    r3 = Kit(pal)
    r3.ring('y', C, 0.364, 0.374, 0.0640, 0.0700, 'gunmetal', seg=16)
    for i in range(4):
        with radial(r3, 45 + 90 * i, C):
            r3.ext([(0.286, 0.0500), (0.296, 0.0500), (0.370, 0.0650), (0.370, 0.0690), (0.290, 0.0545)], 'gunmetal', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                   -0.0025, 0.0025)
    laser_box(r3, 0.128, bz, s=1, hw=AP, L=0.036, w=0.016, h=0.020, color='gun2')
    cable(r3, [(AP + 0.008, 0.109, bz), (0.0420, 0.100, 0.0480), (0.0300, 0.094, 0.0340), (0.0225, 0.088, 0.0260)], clamps=(1,))
    r3.tube([((0.0500, 0.270, 0.0520), 0.005, 0.028), ((0.0580, 0.180, 0.0300), 0.005, 0.028), ((0.0600, 0.030, 0.0220), 0.005, 0.028),
             ((0.0570, -0.110, 0.0300), 0.005, 0.028), ((0.0500, -0.226, 0.0520), 0.005, 0.028)], 'rubber', sides=4, up=(0, 0, 1), a0=45)
    for y in (0.270, -0.226):
        r3.cbox((0.0460, y, 0.0540), (0.012, 0.012, 0.010), 'steel2', ch=0.002, hull=False)
    r3.cbox((-0.0255, -0.034, 0.016), (0.009, 0.026, 0.018), 'gun2', ch=0.002, hull=True)
    for i in range(3):
        r3.box((-0.0300 - PR / 2 + 0.0005, -0.042 + i * 0.008, 0.016), (PR + 0.001, 0.005, 0.010), 'emis', skip=sk(-1))

    # ---- Epic (and up): glowing throats, a coil ahead of the clamp, energy cell and conduit, cassette charge strips
    r4 = Kit(pal)
    r4.ring('y', C, -0.338, -0.326, 0.0300, 0.0445, 'emis', seg=14, hull=False)
    r4.ring('y', C, 0.352, 0.362, 0.0380, 0.0500, 'emis', seg=16, hull=False)
    grooves(r4, 0.168, 0.188, R, bz, n=2, color='emis', seg=16)
    energy_cell(r4, (0.0300, -0.096, bz - 0.0420), L=0.050, r=0.0085, cage_bars=3)
    conduit(r4, [(0.0320, -0.072, 0.0340), (0.0375, -0.058, 0.0425), (0.0375, 0.060, 0.0425), (0.0375, 0.148, 0.0425)], r=0.0028, every=1)
    m4 = Kit(pal)
    for s in (-1, 1):
        m4.box((0, s * (0.037 + PR * 1.5 - 0.0005), -0.026), (0.030, PR + 0.001, 0.003), 'emis', skip=('-y' if s > 0 else '+y',))

    # ---- Legendary (obsidian): shard crown on the bell, molten vents along the tube, lava cracks
    r5 = Kit(pal)
    for i in range(8):
        h = 0.016 if i in (1, 2) else 0.028                                                                       # the two beside the sight line stay low
        with radial(r5, 22.5 + 45 * i, C):
            r5.ext([(0.300, 0.0530), (0.372, 0.0630), (0.383, 0.0630 + h), (0.352, 0.0640 + h * 0.5), (0.318, 0.0640)], 'gun3', (0, 0, 0), (0, 1, 0), (1, 0, 0),
                   (0, 0, 1), -0.0035, 0.0035)
            r5.ext([(0.330, 0.0600), (0.368, 0.0660), (0.380, 0.0610 + h), (0.356, 0.0650 + h * 0.4)], 'emis', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                   -0.0050, 0.0050, hull=False)
    for a in (0, 180):
        with radial(r5, a, C):
            r5.ext([(-0.262, 0.0440), (-0.334, 0.0540), (-0.350, 0.0840), (-0.318, 0.0660), (-0.286, 0.0560)], 'gun3', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                   -0.0035, 0.0035)
    with radial(r5, 135, C):
        for i in range(5):
            r5.lathe([(R - 0.003, 0.0125), (R + 0.016, 0.0085), (R + 0.016, 0.0058), (R + 0.006, 0.0058), (R + 0.006, 0)], 'gun3', 'x', (0, -0.040 + i * 0.044, 0), 6,
                     bands=[None, 'trim', 'emis', 'emis'], caps=(False, True))
        r5.box((R + PR / 2 - 0.0005, 0.048, 0), (PR + 0.001, 0.180, 0.0030), 'emis', skip=('-x',))
    r5.tube([((AP + 0.0010, -0.058, bz - 0.020), 0.004, 0.004), ((AP + 0.0018, -0.020, bz - 0.012), 0.004, 0.004), ((AP + 0.0010, 0.010, bz - 0.019), 0.004, 0.004),
             ((AP + 0.0018, 0.060, bz - 0.011), 0.005, 0.004), ((AP + 0.0010, 0.100, bz - 0.018), 0.004, 0.004), ((AP + 0.0010, 0.146, bz - 0.014), 0.004, 0.004)],
            'emis', sides=4, up=(1, 0, 0), hull=False)
    for i in range(4):
        with radial(r5, 45 + 90 * i, C):
            r5.ext([(-0.270, 0.0490), (-0.300, 0.0515), (-0.332, 0.0625), (-0.300, 0.0535)], 'emis', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0032, 0.0032, hull=False)
    m5 = Kit(pal)
    m5.box((0, 0, -0.020), (0.046 + 2 * PR + 0.003, 0.058, 0.003), 'gun3')
    for i in (-1, 0, 1):
        m5.lathe([(0.046, 0.0066), (0.050, 0.0066), (0.050, 0.0040)], 'emis', 'y', (i * 0.0140, 0, -0.044), 8, hull=False, caps=(False, False))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.384, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.165, zs), 'elem': (cx, 0.0, cz), 'cls': 'rocket', 'fore': (0.205, 0.024),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}


def build_murmur(pal):
    """ML-6 Murmur: shoulder-fired six-tube homing launcher. Two rows of three numbered launch tubes held by a front
    and a rear frame with latches, a bulkhead strap and hazard lines; seeker-tipped warheads at the front rims,
    venturis at the back, the front cover folded back on top, data panels on both sides; a command launch unit up
    top-left (lens hood, eyepiece, battery pack with its cable, lock lights, whip antenna), ring sights on the centre
    line, a shoulder rest, the pistol-grip frame with its safety and forward handle, and a missile cassette (the Mag).
    Rarity layers: Rare bolts on a seeker bumper, an illuminator with its cable, a missile counter, a CLU sun shield
    and a sling; Epic rings every tube mouth and venturi in light and beds two energy cells in the valleys between
    the tubes; Legendary (pearl and rose gold) spreads feather wings from the front frame, bands the tubes in gold,
    sets a pearl on the cover and another on the antenna."""
    rake = 18
    k = Kit(pal)
    bz, R, dx, dz = 0.076, 0.018, 0.042, 0.021
    C = (0, 0, bz)
    RA = R * math.cos(D(30))                         # hex tubes: flats on top and bottom, RA from the tube axis
    ZT = bz + dz + RA                                # top flats of the upper row
    tubes = [(x, bz + z) for z in (-dz, dz) for x in (-dx, 0.0, dx)]
    ring3 = lambda p, y: [(q[0], y, q[1]) for q in p]
    for x, z in tubes:
        k.lathe([(-0.150, 0), (-0.150, R), (0.252, R), (0.256, R + 0.0028), (0.274, R + 0.0028), (0.274, 0.0150),
                 (0.262, 0.0150), (0.262, 0)], 'gun3', 'y', (x, 0, z), 6, a0=0,
                bands=[None, None, 'gunmetal', 'gunmetal', 'gunmetal', 'ink', 'ink'])
        k.lathe([(0.250, 0.0140), (0.279, 0.0128), (0.292, 0.0058), (0.298, 0)], 'red', 'y', (x, 0, z), 6, hull=False, a0=0, bands=[None, None, 'lens'])
        for y in (0.140, 0.000):
            k.lathe([(y - 0.003, R - 0.001), (y - 0.003, R + 0.0022), (y + 0.003, R + 0.0022), (y + 0.003, R - 0.001)], 'acc2', 'y', (x, 0, z), 6, hull=False, a0=0,
                    caps=(False, False))
        k.lathe([(-0.140, 0.0150), (-0.176, R + 0.0028), (-0.176, 0.0110), (-0.160, 0)],
                'steel2', 'y', (x, 0, z), 6, bands=[None, None, 'ink'], hull=False, a0=0)
    # ---- frames with latches and bolts, bulkhead strap, hazard lines, tube numbers
    FW, FH = 2 * (dx + R) + 0.012, 2 * (dz + R) + 0.012
    for y in (0.230, -0.132):
        k.cbox((0, y, bz), (FW, 0.020, FH), 'gunmetal', ch=0.004, axis='y')
        for s in (-1, 1):
            k.cbox((s * 0.036, y, bz + FH / 2 + 0.0015), (0.014, 0.012, 0.005), 'steel2', ch=0.001, axis='x', hull=False)
            for zz in (-0.024, 0.024):
                bolt(k, (s * FW / 2, y, bz + zz), (s, 0, 0), 0.0032, 0.0024, socket=False)
    k.cbox((0, 0.040, bz), (FW - 0.006, 0.008, FH - 0.006), 'steel2', ch=0.003, axis='y')
    for y in (0.176, -0.090):
        k.box((0, y, bz), (FW - 0.006, 0.004, FH - 0.010), 'trim')
    for i, x in enumerate((-dx, 0.0, dx)):
        top_stencil(k, str(i + 1), ZT, -0.064, cap=0.012, x=x)
    # ---- front cover folded back on top, side data panels
    k.cbox((0, 0.187, ZT + 0.0024), (0.112, 0.062, 0.005), 'gun2', ch=0.002, axis='z')
    k.pin(-0.050, 0.050, 0.2185, ZT + 0.0050, 0.0028, color='steel2')
    top_slots(k, ZT + 0.0049, 0.192, 0.214, 2, w=0.070, fill=0.3)
    top_stencil(k, 'COVER', ZT + 0.0049, 0.160, cap=0.007)
    for s in (-1, 1):
        k.cbox((s * (dx + R - 0.0015), 0.086, bz), (0.005, 0.078, 0.026), 'body2', ch=0.001, axis='y')
        for (y, zz) in ((0.052, 0.009), (0.120, 0.009), (0.052, -0.009), (0.120, -0.009)):
            bolt(k, (s * (dx + R + 0.001), y, bz + zz), (s, 0, 0), 0.0022, 0.0020, socket=False)
        k.cbox((s * (dx + R - 0.0015), -0.042, bz), (0.005, 0.050, 0.022), 'body2', ch=0.001, axis='y')
    hazard(k, dx + R + 0.001, -0.062, -0.028, bz - 0.0070, bz + 0.0070, n=4)
    stencil(k, 'MURMUR', dx + R + 0.001, 0.086, bz - 0.0045, cap=0.010, sides=(1,))
    stencil(k, 'ML-6', dx + R + 0.001, 0.086, bz - 0.0050, cap=0.011, sides=(-1,))
    with k.at((dx, 0, ZT)):                                                                                       # carrying handle on the right-hand tube
        for y in (-0.036, 0.030):
            k.cbox((0, y, 0.0035), (0.014, 0.012, 0.009), 'steel2', ch=0.002, axis='y', hull=False)
        k.tube([((0, -0.036, 0.004), 0.009, 0.008), ((0, -0.026, 0.020), 0.009, 0.008), ((0, 0.020, 0.020), 0.009, 0.008), ((0, 0.030, 0.004), 0.009, 0.008)],
               'gun2', sides=6, up=(1, 0, 0))
        k.lathe([(-0.020, 0), (-0.020, 0.0066), (0.014, 0.0066), (0.014, 0)], 'rubber', 'y', (0, 0, 0.020), 8)
    # ---- cradle onto the frame
    k.cbox((0, 0.040, 0.034), (0.100, 0.300, 0.012), 'gun2', ch=0.003, axis='y')
    slots(k, 0.050, -0.094, 0.174, 0.034, 7, h=0.004, fill=0.5)
    # ---- command launch unit (top left): hood and seeker lens, eyepiece, battery pack and cable, lock lights, antenna
    tx, ty, tz = -0.054, 0.080, 0.140
    k.cbox((tx + 0.006, ty, 0.118), (0.020, 0.050, 0.012), 'gun2', ch=0.002, axis='y')
    k.cbox((tx, ty, tz), (0.034, 0.096, 0.036), 'gun2', ch=0.004, axis='y')
    k.ring('y', (tx, 0, tz), ty + 0.046, ty + 0.066, 0.0105, 0.0150, 'gunmetal', seg=8)
    k.lathe([(ty + 0.046, 0), (ty + 0.046, 0.0107), (ty + 0.052, 0.0080), (ty + 0.055, 0)], 'lens', 'y', (tx, 0, tz), 8, hull=False)
    k.lathe([(ty - 0.046, 0.0090), (ty - 0.056, 0.0090), (ty - 0.066, 0.0125), (ty - 0.066, 0.0080), (ty - 0.058, 0.0060), (ty - 0.058, 0)], 'rubber', 'y',
            (tx + 0.002, 0, tz + 0.002), 8, bands=[None, None, None, None, 'lens'], caps=(False, True))
    k.lathe([(ty - 0.034, 0), (ty - 0.034, 0.0095), (ty + 0.030, 0.0095), (ty + 0.030, 0.0070), (ty + 0.036, 0.0070), (ty + 0.036, 0)], 'gun3', 'y',
            (tx - 0.0160, 0, tz - 0.0160), 8, bands=[None, None, 'steel2', 'steel2', 'steel2'])
    cable(k, [(tx - 0.0160, ty + 0.036, tz - 0.0160), (tx - 0.0200, ty + 0.046, tz - 0.0100), (tx - 0.0190, ty + 0.054, tz), (tx - 0.0140, ty + 0.056, tz + 0.004)], r=0.0026)
    plate(k, rect(ty - 0.040, ty + 0.040, tz + 0.008, tz + 0.011), -tx + 0.017, 'trim', ch=0, sides=(-1,))
    stencil(k, 'CLU', -tx + 0.017, ty, tz - 0.006, cap=0.008, sides=(-1,))
    k.cbox((tx + 0.004, ty - 0.020, tz + 0.020), (0.010, 0.010, 0.008), 'red', ch=0.002)
    for i in range(2):
        k.box((tx - 0.004 + i * 0.010, ty + 0.012, tz + 0.018 + PR / 2 - 0.0005), (0.006, 0.010, PR + 0.001), 'rubber', skip=('-z',))
    for i in range(3):
        k.box((tx - 0.009 + i * 0.008, ty - 0.048 - PR / 2 + 0.0005, tz - 0.011), (0.005, PR + 0.001, 0.004), 'emis', skip=('+y',))
    k.lathe([(0.016, 0), (0.016, 0.0036), (0.024, 0.0036), (0.024, 0.0014), (0.064, 0.0014), (0.064, 0)], 'ink', 'z', (tx - 0.008, ty - 0.036, tz), 6, hull=False,
            bands=[None, 'steel2', 'steel2', None, None])
    # ---- sights on the centre line (rear aperture, front ring)
    zs = 0.120 + 0.024
    k.cbox((0, -0.120, 0.12575), (0.022, 0.028, 0.0235), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.126, -0.118, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.pin(-0.0150, 0.0150, -0.111, 0.1300, 0.0028, color='steel2')
    k.cbox((0, 0.240, 0.12625), (0.012, 0.016, 0.0205), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.236, 0.244, 0.0110, 0.0155, 'trim', seg=12, hull=True)
    # ---- arming lever, shoulder rest with its pad
    k.cbox((-0.034, -0.110, 0.030), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    k.ext_x([(-0.112, 0.036), (-0.238, 0.036), (-0.242, 0.006), (-0.232, -0.002), (-0.222, 0.016), (-0.150, 0.020), (-0.112, 0.024)], -0.017, 0.017, 'gun2', ch=0.003)
    k.cbox((0, -0.2425, 0.012), (0.038, 0.008, 0.030), 'rubber', ch=0.002, axis='x')
    for z in (0.004, 0.012, 0.020):
        k.box((0, -0.2445, z), (0.030, 0.007, 0.0025), 'ink')
    studs(k, 0.017, [(-0.160, 0.027), (-0.226, 0.024)], r=0.0032)
    # ---- frame: plates, safety with its marks, cassette catch
    launcher_frame(k, rake, 0.200, 0.026)
    plate(k, [(-0.048, 0.002), (0.056, 0.002), (0.066, 0.012), (0.066, 0.027), (-0.048, 0.027)], 0.020, 'frame2')
    plate(k, rect(-0.046, 0.068, -0.0055, -0.0030), 0.020, 'trim', ch=0)
    studs(k, 0.020 + PR, [(-0.042, 0.022), (0.060, 0.022)])
    stencil(k, 'ML-6', 0.020 + PR, 0.028, 0.008, cap=0.011, sides=(1,))
    k.lathe([(0.017, 0.0050), (0.0255, 0.0050), (0.0255, 0)], 'steel2', (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, -1))), (0, 0.016, 0.017), 8, hull=False, caps=(False, True))
    k.xbar(-0.0285, -0.0255, [(-0.004, 0.0125), (0.018, 0.0125), (0.020, 0.0215), (-0.002, 0.0200)], 'gun3', ch=0, hull=False)
    k.box((-0.0215 - PR / 2 + 0.0005, -0.014, 0.022), (PR + 0.001, 0.004, 0.004), 'mark', skip=sk(-1))
    k.box((-0.0215 - PR / 2 + 0.0005, 0.036, 0.022), (PR + 0.001, 0.004, 0.004), 'red', skip=sk(-1))
    k.xbar(-0.005, 0.005, [(0.132, 0.004), (0.142, 0.004), (0.146, -0.016), (0.140, -0.018), (0.136, -0.006)], 'steel2', ch=0.001)
    studs(k, 0.020, [(0.187, 0.0295), (0.213, 0.0295)])
    # ---- missile cassette: three seeker-tipped warheads at the nose, exhaust ports at the back
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.022), (0.050, 0.080, 0.064), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.010), (0.050 + 2 * PR, 0.056, 0.004), 'trim')
    mk.cbox((0, 0.0, -0.058), (0.056, 0.086, 0.010), 'gun3', ch=0.003, axis='z')
    mk.box((0, 0.040 + PR / 2 - 0.0005, -0.040), (0.046, PR + 0.001, 0.017), 'ink', skip=('-y',))
    mk.box((0, -0.040 - PR / 2 + 0.0005, -0.040), (0.046, PR + 0.001, 0.017), 'ink', skip=('+y',))
    for i in (-1, 0, 1):
        mk.lathe([(0.034, 0), (0.034, 0.0062), (0.046, 0.0054), (0.054, 0)], 'red', 'y', (i * 0.0150, 0, -0.040), 6, hull=False, bands=[None, None, 'lens'])
        mk.lathe([(-0.0450, 0.0048), (-0.0450, 0.0030), (-0.0390, 0.0030)], 'steel2', 'y', (i * 0.0150, 0, -0.040), 6, hull=False, caps=(False, False))
    for s in (-1, 1):
        for y in (-0.027, 0.027):
            mk.box((s * (0.025 + PR / 2 - 0.0005), y, -0.032), (PR + 0.001, 0.005, 0.036), 'frame2', skip=sk(s))
    stencil(mk, 'HM-6', 0.025, 0.0, -0.034, cap=0.009)
    hazard(mk, 0.025, -0.018, 0.014, -0.049, -0.044, n=4)

    # ---- Rare (and up): seeker bumper, illuminator and cable, missile counter, CLU sun shield, sling
    r3 = Kit(pal)
    r3.loft([ring3(rrect(FW - 0.010, FH - 0.010, c=0.006, cy=bz), 0.280), ring3(rrect(FW, FH, c=0.008, cy=bz), 0.280),
             ring3(rrect(FW, FH, c=0.008, cy=bz), 0.288), ring3(rrect(FW - 0.010, FH - 0.010, c=0.006, cy=bz), 0.288)], 'gunmetal', closed=True)
    for sx in (-1, 1):
        for s in (-1, 1):
            r3.bar((sx * (FW / 2 - 0.004), 0.238, bz + s * (FH / 2 - 0.004)), (sx * (FW / 2 - 0.004), 0.284, bz + s * (FH / 2 - 0.004)), 0.005, 0.005, 'gunmetal', hull=True)
    r3.cbox((0.036, 0.186, ZT + 0.0120), (0.022, 0.044, 0.015), 'gun2', ch=0.003, hull=True)
    r3.lathe([(0.206, 0), (0.206, 0.0062), (0.214, 0.0062), (0.214, 0.0042), (0.211, 0.0042), (0.211, 0)], 'steel2', 'y', (0.036, 0, ZT + 0.0125), 8, hull=False,
             bands=[None, None, None, 'emis', 'emis'])
    cable(r3, [(0.0260, 0.168, ZT + 0.0090), (0.0100, 0.150, ZT + 0.0040), (-0.0200, 0.136, ZT + 0.0040), (-0.0340, 0.122, ZT + 0.0120)], clamps=(1,))
    r3.cbox((0.036, -0.132, bz + FH / 2 + 0.00325), (0.040, 0.016, 0.0135), 'gun2', ch=0.002, hull=True)
    for i in range(6):
        top_slots(r3, bz + FH / 2 + 0.0100, -0.132 - 0.005, -0.132 + 0.005, 1, w=0.0036, fill=0.8, color='emis', x=0.022 + i * 0.0056)
    r3.cbox((tx, ty + 0.024, tz + 0.0215), (0.040, 0.076, 0.004), 'gun3', ch=0.0015, axis='z', hull=True)
    studs(r3, -tx + 0.020, [(ty + 0.000, tz + 0.0215), (ty + 0.050, tz + 0.0215)], sides=(-1,), r=0.0022)
    r3.tube([((0.0640, 0.228, 0.0600), 0.005, 0.028), ((0.0700, 0.140, 0.0380), 0.005, 0.028), ((0.0710, 0.040, 0.0300), 0.005, 0.028),
             ((0.0690, -0.060, 0.0380), 0.005, 0.028), ((0.0640, -0.130, 0.0600), 0.005, 0.028)], 'rubber', sides=4, up=(0, 0, 1), a0=45)

    # ---- Epic (and up): light in every tube mouth and venturi, energy cells in the valleys with their conduits
    r4 = Kit(pal)
    for x, z in tubes:
        r4.lathe([(0.2735, 0.0190), (0.2755, 0.0190), (0.2755, 0.0168), (0.2735, 0.0168)], 'emis', 'y', (x, 0, z), 6, hull=False, a0=0,
                 caps=(False, False))
        r4.lathe([(-0.166, 0.0125), (-0.162, 0)], 'emis', 'y', (x, 0, z), 6, hull=False, a0=0)
    for s in (-1, 1):
        energy_cell(r4, (s * 0.021, -0.020, bz + dz + 0.0110), L=0.050, r=0.0075, cage_bars=3)
        conduit(r4, [(s * 0.021, 0.006, bz + dz + 0.0110), (s * 0.021, 0.034, bz + dz + 0.0080), (s * 0.021, 0.048, bz + dz + 0.0080), (s * 0.021, 0.148, bz + dz + 0.0080)],
                r=0.0028, every=1)
    grooves(r4, ty + 0.050, ty + 0.062, 0.0150, 0, n=1, color='emis', seg=8, fill=0.5, c=(tx, 0, tz))
    for y in (0.230, -0.132):
        for s in (-1, 1):
            r4.box((s * (FW / 2 + PR / 2 - 0.0005), y, bz), (PR + 0.001, 0.008, 0.032), 'emis', skip=sk(s))
    m4 = Kit(pal)
    for s in (-1, 1):
        m4.box((0, s * (0.040 + PR * 1.5 - 0.0005), -0.024), (0.032, PR + 0.001, 0.003), 'emis', skip=('-y' if s > 0 else '+y',))

    # ---- Legendary (pearl and rose gold): feather wings off the front frame, gold bands, pearls on the cover and antenna
    r5 = Kit(pal)
    for s in (-1, 1):
        for j, ang in enumerate((30, 10, -10)):
            with radial(r5, ang if s > 0 else 180 - ang, C):
                dy, dr = 0.020 * j, 0.012 * j
                r5.ext([(0.238, 0.0560), (0.222, 0.0560), (0.150 + dy, 0.1180 - dr), (0.178 + dy, 0.1000 - dr), (0.214, 0.0820)], 'gun3', (0, 0, 0), (0, 1, 0), (1, 0, 0),
                       (0, 0, 1), -0.0018, 0.0018)
                r5.ext([(0.226, 0.0660), (0.158 + dy, 0.1120 - dr), (0.182 + dy, 0.0960 - dr)], 'trim', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), -0.0033, 0.0033,
                       hull=False)
        for sz in (-1, 1):
            r5.ext_x([(0.218, bz + sz * 0.016), (0.218, bz + sz * 0.040), (0.150, bz + sz * 0.044), (0.060, bz + sz * 0.052), (0.110, bz + sz * 0.030), (0.160, bz + sz * 0.020)],
                     min(s * 0.0590, s * 0.0655), max(s * 0.0590, s * 0.0655), 'gun3', ch=0)
            r5.ext_x([(0.212, bz + sz * 0.028), (0.150, bz + sz * 0.036), (0.072, bz + sz * 0.049), (0.150, bz + sz * 0.032)], min(s * 0.0605, s * 0.0670),
                     max(s * 0.0605, s * 0.0670), 'trim', ch=0, hull=False)
        r5.box((s * (dx + R + 0.001 + PR / 2 - 0.0005), 0.086, bz + 0.0105), (PR + 0.001, 0.070, 0.0018), 'trim', skip=sk(s))
        r5.box((s * (dx + R + 0.001 + PR / 2 - 0.0005), 0.086, bz - 0.0105), (PR + 0.001, 0.070, 0.0018), 'trim', skip=sk(s))
    for x, z in tubes:
        r5.lathe([(0.2430, R - 0.001), (0.2430, R + 0.0025), (0.2500, R + 0.0025), (0.2500, R - 0.001)], 'trim', 'y', (x, 0, z), 6, hull=False, a0=0, caps=(False, False))
        r5.lathe([(-0.1190, R - 0.001), (-0.1190, R + 0.0025), (-0.1130, R + 0.0025), (-0.1130, R - 0.001)], 'trim', 'y', (x, 0, z), 6, hull=False, a0=0,
                 caps=(False, False))
    with r5.at((0, 0.187, ZT + 0.0049)):
        for j, a in enumerate((35, -35)):
            r5.box((0, 0, 0.0020 + 0.0016 * j), (0.0030, 0.064, 0.0020), 'trim', rot=(0, 0, a))
        r5.lathe([(0.0005, 0.0120), (0.0065, 0.0120), (0.0065, 0.0090), (0.0080, 0.0090), (0.0120, 0.0055), (0.0135, 0)], 'gun3', 'z', (0, 0, 0), 8, hull=False,
                 bands=[None, None, 'emis', 'emis', 'emis'], caps=(False, True), a0=0)
    r5.lathe([(0.062, 0), (0.064, 0.0050), (0.071, 0.0078), (0.078, 0.0050), (0.080, 0)], 'emis', 'z', (tx - 0.008, ty - 0.036, tz), 6, hull=False)
    r5.lathe([(0.056, 0.0030), (0.056, 0.0056), (0.062, 0.0056), (0.062, 0.0030)], 'trim', 'z', (tx - 0.008, ty - 0.036, tz), 6, hull=False, caps=(False, False))
    for i in range(6):
        with radial(r5, 60 * i, (tx, 0, tz)):
            r5.ext([(ty + 0.052, 0.0140), (ty + 0.064, 0.0140), (ty + 0.070, 0.0230), (ty + 0.058, 0.0190)], 'trim', (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                   -0.0015, 0.0015, hull=False)
    m5 = Kit(pal)
    for z in (-0.018, -0.040):
        m5.box((0, 0, z), (0.050 + 2 * PR + 0.003, 0.062, 0.003), 'trim')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.300, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.135, zs), 'cls': 'rocket', 'fore': (0.200, 0.026),
                   'layers': {'345': r3, '45': r4, '5': r5}, 'mag_layers': {'45': m4, '5': m5}}
