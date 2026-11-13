"""INKBOLT kit-stronghold, the outer works on the cliff ledge (zone 1) plus the shared gate, trail and hatch pieces:
cliff faces with bunkers, embrasures and vents, parapets and their posts, sandbag walls, jersey barriers, tank traps,
boulders, the bastions flanking the rock gate, pillboxes, gun emplacements, concrete ramps (walkable steps), deck rails,
the helipad and its helicopter, the radome, the comms mast, floodlight towers, supply crates, pallet stacks, drums,
the camouflage-netted supply dump, the jeep, the generator, the fuel bowser, signposts, the windsock.
See sh_base.py for the conventions."""
import math
import random

from sh_base import (SKit, CLIFF_H, T1, TRAIL_H, rock_face, rock_pillar, sandbag_row, sandbag_wall, crate, drum, pipe_rail,  # noqa: F401
                     lattice, rock_lump, steps)
from kit_base import shutter_hull, panel_seams, bolt_row, kick_plate, base_trim, junction_box, rivet_strip  # noqa: F401

ROCK = ('rock', 'rock2', 'rock3', 'rockL')


# ================================================================ cliff faces (wall modules, face -Y, 14.2 m)
def build_cliffs(k, ao):
    def face(name, w, seed, extra=None, z0=0.0):
        rnd = random.Random(seed)
        k.begin()
        rock_face(k, rnd, -0.5, -0.5 + w, CLIFF_H, ROCK, z0=z0)
        if extra:
            extra(rnd)
        k.finish(name, ao=ao)

    face('Cliff2_A', 2, 11)
    face('Cliff2_B', 2, 12)
    face('Cliff1', 1, 13)

    def ledge(rnd):   # a rock shelf with scrub and a fallen block at its foot
        k.bx(-0.3, 1.2, -0.72, -0.4, 6.1, 6.4, 'rock3')
        rock_lump(k, rnd, 0.6, -0.8, 0.45, 0.3, 0.55)
    face('Cliff2_C', 2, 14, ledge)

    def bunker(rnd):   # concrete casemate front: steel door, number, lamp, cable conduit
        k.bx(-0.5, 1.5, -0.62, 0.3, 0.0, 3.3, 'conc')
        k.bx(-0.5, 1.5, -0.68, 0.3, 3.3, 3.55, 'conc3')
        k.bx(0.05, 0.95, -0.66, -0.6, 0.0, 2.15, 'steel2')
        k.bx(0.1, 0.9, -0.675, -0.66, 0.08, 2.08, 'olive2', ink=False)
        k.bx(0.78, 0.86, -0.69, -0.675, 0.95, 1.2, 'steelD', ink=False)
        k.text('B-%d' % rnd.randint(2, 9), 0.5, -0.684, 2.35, 0.32, 'paint', font='display')
        k.bx(1.15, 1.35, -0.75, -0.62, 2.45, 2.65, 'steelD')
        k.bx(1.17, 1.33, -0.756, -0.75, 2.47, 2.63, 'lamp', ink=False)
        k.cyl(-0.3, -0.66, 0.0, 0.05, 0.05, 3.27, 'steel2', seg=6, ink=False)
        # Stage 11 detail: formwork seams, base trim, door kick plate and bolts, a junction box on the conduit
        panel_seams(k, -0.5, 1.5, 0.12, 3.28, -0.62, 1.0, 'concD', horizontal=[1.2, 2.32])
        base_trim(k, -0.5, 0.05, -0.62, 'concD', h=0.11)
        base_trim(k, 0.95, 1.5, -0.62, 'concD', h=0.11)
        kick_plate(k, 0.12, 0.88, -0.675, 'steelD', h=0.24, z0=0.08, bolts='steel')
        bolt_row(k, 0.15, 0.85, 1.96, -0.675, 6, 'steelD')
        junction_box(k, -0.06, 1.55, -0.62, 'steel2', 'steelD', w=0.2, h=0.26)
    face('Cliff2_Bunker', 2, 15, bunker, z0=3.55)

    def slit(rnd):   # gun casemate: a dark embrasure with a machine-gun barrel, sandbags under it
        k.bx(-0.5, 1.5, -0.62, 0.3, 0.0, 2.9, 'conc')
        k.bx(-0.5, 1.5, -0.68, 0.3, 2.9, 3.15, 'conc3')
        k.bx(-0.1, 1.1, -0.64, -0.6, 1.35, 1.7, 'ink', ink=False)
        k.cyl(0.5, -0.62, 1.52, 0.04, 0.035, 0.6, 'steelD', seg=6, rot=(90, 0, 0))
        sandbag_row(k, -0.4, 1.4, -0.85, 0.0, h=0.2, d=0.36)
        sandbag_row(k, -0.3, 1.3, -0.85, 0.2, h=0.2, d=0.32, stagger=True)
        k.text('%d' % rnd.randint(10, 40), 1.25, -0.684, 2.35, 0.3, 'paint', font='display')
        panel_seams(k, -0.5, 1.5, 0.45, 1.3, -0.62, 1.0, 'concD')   # vertical seams stop at the slit
        panel_seams(k, -0.5, 1.5, 1.75, 2.88, -0.62, 1.0, 'concD', horizontal=[2.05])
        bolt_row(k, -0.05, 1.05, 1.82, -0.62, 4, 'concD', s=0.03)   # formwork tie holes over the slit (clear of the seam)
    face('Cliff2_Slit', 2, 16, slit, z0=3.15)

    def vent(rnd):   # ventilation grille and pipes coming out of the rock
        k.bx(0.1, 0.9, -0.6, -0.4, 0.4, 1.4, 'steel2')
        for i in range(5):
            z = 0.52 + i * 0.18
            k.bx(0.16, 0.84, -0.615, -0.6, z, z + 0.06, 'steelD', ink=False)
        k.cyl(1.2, -0.62, 0.0, 0.09, 0.09, 4.6, 'steel', seg=8)
        k.cyl(1.2, -0.62, 4.6, 0.12, 0.12, 0.25, 'steel2', seg=8)
        rivet_strip(k, 0.12, 0.88, 1.36, -0.6, 'steelD', every=0.13)
        rivet_strip(k, 0.12, 0.88, 0.44, -0.6, 'steelD', every=0.13)
    face('Cliff2_Vent', 2, 17, vent)

    k.begin()   # corner / notch pillar: rock on every side
    rock_pillar(k, random.Random(18), CLIFF_H, ROCK)
    k.finish('CliffC', ao=ao)


# ================================================================ parapets, sandbags, barriers
def build_barriers(k, ao):
    for name, extra in (('Parapet_A', None), ('Parapet_B', 'bags'), ('Parapet_C', 'drain')):
        k.begin()
        k.bx(-0.5, 0.5, -0.2, 0.2, 0.0, 1.04, 'conc', ink=False)
        k.bx(-0.5, 0.5, -0.25, 0.25, 1.04, 1.16, 'conc3')
        k.bx(-0.494, 0.494, -0.215, 0.215, 0.0, 0.12, 'concD', ink=False)
        if extra == 'bags':
            sandbag_row(k, -0.48, 0.48, 0.0, 1.16, n=2, h=0.18, d=0.34)
        if extra == 'drain':
            for s in (-1, 1):
                k.bx(-0.16, 0.16, s * 0.2 - 0.004, s * 0.2 + 0.004, 0.13, 0.3, 'ink', ink=False)
        for turn in (0, 180):   # formwork tie holes on both faces
            k.push(0, 0, turn)
            bolt_row(k, -0.42, 0.42, 0.62 if extra != 'drain' else 0.7, -0.2, 3, 'concD', s=0.03)
            k.pop()
        k.col(-0.5, 0.5, -0.25, 0.25, 0.0, 1.16)
        k.finish(name, ao=ao)
    k.begin()
    k.bx(-0.33, 0.33, -0.33, 0.33, 0.0, 1.3, 'conc2')
    k.bx(-0.38, 0.38, -0.38, 0.38, 1.3, 1.42, 'conc3')
    k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 1.42)
    k.finish('ParapetPost', ao=ao)
    # sandbag wall (1 m along X, 5 courses: 1 m cover)
    for name, seed in (('Sandbags_A', 1), ('Sandbags_B', 2)):
        k.begin()
        sandbag_wall(k, -0.5, 0.5, 0.0, courses=5, h=0.2, d=0.5 if seed == 1 else 0.46)
        k.col(-0.5, 0.5, -0.25, 0.25, 0.0, 1.0)
        k.finish(name, ao=ao)
    # concrete jersey barrier (1 m segment along X)
    k.begin()
    prof = [(-0.3, 0.0), (-0.3, 0.08), (-0.14, 0.3), (-0.1, 0.84), (0.1, 0.84), (0.14, 0.3), (0.3, 0.08), (0.3, 0.0)]
    pts = [(x, y, z) for x in (-0.49, 0.49) for (y, z) in prof]
    k.hullp(pts, lambda f: 'conc3' if f.normal.z > 0.9 else 'conc')
    k.bx(-0.3, 0.3, -0.302, -0.296, 0.42, 0.5, 'amber', ink=False)
    k.col(-0.5, 0.5, -0.3, 0.3, 0.0, 0.84)
    k.finish('Jersey', ao=ao)
    # Czech hedgehog tank trap (three crossed steel angles)
    k.begin()
    for (a, b) in (((-0.6, -0.6, 0.0), (0.6, 0.6, 1.2)), ((0.6, -0.6, 0.0), (-0.6, 0.6, 1.2)), ((0.0, -0.75, 0.6), (0.0, 0.75, 0.6))):
        k.beam(a, b, 0.11, 'steelD' if a[2] == 0 else 'rust')
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 1.0)
    k.finish('Hedgehog', ao=ao)
    # fallen boulders
    for name, seed, s in (('Boulder_A', 31, 0.42), ('Boulder_B', 32, 0.38)):
        k.begin()
        rnd = random.Random(seed)
        rock_lump(k, rnd, 0, 0, s, s * 0.9, s * 1.8)
        rock_lump(k, rnd, 0.22, -0.18, s * 0.45, s * 0.4, s * 0.8)
        k.col(-s * 0.8, s * 0.8, -s * 0.75, s * 0.75, 0.0, s * 1.6)
        k.finish(name, ao=ao)
    k.begin()
    rnd = random.Random(33)
    rock_lump(k, rnd, 0, 0, 0.92, 0.8, 1.7)
    rock_lump(k, rnd, -0.55, 0.45, 0.4, 0.38, 0.7)
    k.col(-0.75, 0.75, -0.65, 0.65, 0.0, 1.55)
    k.finish('BoulderBig', ao=ao)


# ================================================================ fortifications
def embrasure(k, x, y, z, w, h, facing='y-'):
    """dark gun slit set 2 mm proud of a concrete face (y- / y+ / x- / x+)"""
    d = 0.006
    if facing in ('y-', 'y+'):
        s = -1 if facing == 'y-' else 1
        k.bx(x - w / 2, x + w / 2, y + s * d - 0.002, y + s * d + 0.002, z, z + h, 'ink', ink=False)
    else:
        s = -1 if facing == 'x-' else 1
        k.bx(x + s * d - 0.002, x + s * d + 0.002, y - w / 2, y + w / 2, z, z + h, 'ink', ink=False)


def build_forts(k, ao):
    # bastion [5, 4]: concrete casemate against the rock beside the gate (front -Y), slits on the front and both ends
    k.begin()
    H = 3.4
    # the back stops 0.28 m short of the rock face (the cliff's relief and the gate portal's pylon sit there)
    k.hullp([(-2.35, -1.75, 0), (2.35, -1.75, 0), (2.35, 1.7, 0), (-2.35, 1.7, 0),
             (-2.15, -1.55, H), (2.15, -1.55, H), (2.15, 1.7, H), (-2.15, 1.7, H)], lambda f: 'conc3' if f.normal.z > 0.9 else 'conc')
    k.bx(-2.25, 2.25, -1.65, 1.7, H, H + 0.22, 'conc2')
    for x in (-1.2, 1.2):
        embrasure(k, x, -1.6, 1.55, 1.0, 0.28, 'y-')
    for s in (-1, 1):
        k.push(s * 2.25, 0.2, 0)
        embrasure(k, 0.0, 0.0, 1.55, 0.9, 0.28, 'x-' if s < 0 else 'x+')
        k.pop()
    sandbag_row(k, -2.1, 2.1, -1.42, H + 0.22, h=0.2, d=0.4)
    sandbag_row(k, -1.9, 1.9, -1.42, H + 0.42, h=0.2, d=0.36, stagger=True)
    k.bx(-2.42, 2.42, -1.82, -1.72, 0.0, 0.28, 'concD', ink=False)
    k.bx(-0.2, 0.2, -1.66, -1.5, 2.5, 2.8, 'steelD')
    k.bx(-0.16, 0.16, -1.668, -1.66, 2.54, 2.76, 'lamp', ink=False)
    k.text('HIGHWATCH', 0.0, -1.62, 2.05, 0.34, 'paint', maxw=2.0, font='display')
    k.col(-2.35, 2.35, -1.75, 1.7, 0.0, H + 0.22)
    k.finish('Bastion', ao=ao)

    # pillbox [4, 4]: octagonal concrete, slits on the four main faces, steel door at the back, sandbag apron
    k.begin()
    r, H = 1.85, 2.45
    k.cyl(0, 0, 0, r, r * 0.97, H, 'conc', seg=8, rot=(0, 0, 22.5))
    k.cyl(0, 0, H, r + 0.14, r + 0.08, 0.3, 'conc3', seg=8, rot=(0, 0, 22.5))
    k.cyl(0, 0, H + 0.3, 0.55, 0.45, 0.25, 'conc2', seg=8, rot=(0, 0, 22.5))
    ap = r * math.cos(math.radians(22.5))
    for (x, y, f) in ((0, -ap, 'y-'), (-ap, 0, 'x-'), (ap, 0, 'x+')):
        embrasure(k, x, y, 1.3, 0.9 if f[0] == 'y' else 0.9, 0.26, f)
    k.bx(-0.45, 0.45, ap - 0.02, ap + 0.04, 0.0, 1.95, 'steel2')
    k.bx(-0.4, 0.4, ap + 0.04, ap + 0.05, 0.05, 1.9, 'olive2', ink=False)
    for a in range(8):
        ang = math.radians(a * 45 + 22.5)
        cx, cy = math.cos(ang) * (r + 0.05), math.sin(ang) * (r + 0.05)
        if a in (1, 2):   # leave the door side clear
            continue
        k.push(cx, cy, a * 45 + 22.5 + 90)
        sandbag_row(k, -0.55, 0.55, -0.05, 0.0, n=2, h=0.24, d=0.34)
        k.pop()
    k.cyl(0.0, 0.0, H + 0.55, 0.05, 0.04, 1.1, 'steelD', seg=5)
    k.col(-ap, ap, -0.7, 0.7, 0.0, H + 0.3)
    k.col(-0.7, 0.7, -ap, ap, 0.0, H + 0.3)
    k.col(-1.21, 1.21, -1.21, 1.21, 0.0, H + 0.3)
    k.finish('Pillbox', ao=ao)

    # gun emplacement [3, 3]: sandbag U open at the back (+Y), a machine gun on a tripod firing over the front (-Y)
    k.begin()
    for i in range(3):
        sandbag_row(k, -1.48, 1.48, -1.22, i * 0.34, n=3, h=0.325, d=0.52 - 0.05 * i, stagger=bool(i % 2))
    for s in (-1, 1):
        k.push(s * 1.22, 0.0, 90)
        for i in range(3):
            sandbag_row(k, -0.94, 0.95, 0.0, i * 0.27, n=3, h=0.255, d=0.5 - 0.04 * i, stagger=bool(i % 2))
        k.pop()
    k.cyl(0, -0.55, 0.0, 0.05, 0.05, 0.95, 'steelD', seg=6)
    for a in (0, 120, 240):
        ang = math.radians(a + 90)
        k.beam((0, -0.55, 0.9), (math.cos(ang) * 0.5, -0.55 + math.sin(ang) * 0.5, 0.0), 0.04, 'steelD', ink=False)
    k.bx(-0.12, 0.12, -0.75, 0.05, 0.95, 1.17, 'gunmetal')
    k.cyl(0, -0.75, 1.07, 0.045, 0.04, 0.9, 'steelD', seg=6, rot=(90, 0, 0))
    k.bx(-0.04, 0.04, -0.15, 0.1, 1.17, 1.32, 'gunmetal', ink=False)
    k.bx(0.12, 0.32, -0.5, -0.3, 0.95, 1.15, 'olive2')
    for (x, y) in ((-0.7, 0.75), (-0.35, 0.8), (0.55, 0.7)):
        crate(k, x, y, 0.0, 0.3, 0.22, 0.2, 'olive', 'olive2')
    k.col(-1.48, 1.48, -1.48, -0.96, 0.0, 1.0)
    for s in (-1, 1):
        k.col(s * 1.22 - 0.25, s * 1.22 + 0.25, -0.96, 0.95, 0.0, 0.8)
    k.col(-0.3, 0.3, -0.95, 0.15, 0.0, 1.2)
    k.finish('Emplacement', ao=ao)


# ================================================================ ramps (rise toward +Y) and rails
def ramp(k, L, z0, z1, ao, name):
    """concrete ramp [2, L]: a solid wedge from z0 at -Y to z1 at +Y over a plinth, anti-slip ribs, kerbs, pipe rails
    on both sides; walkable steps every 0.5 m (the nav cell; rise 0.15 m)"""
    k.begin()
    h0, h1, Y = z0, z1, L / 2
    if z0 > 0:
        k.bx(-0.99, 0.99, -Y, Y, 0.0, z0, 'conc2')
    k.hullp([(-0.99, -Y, z0), (0.99, -Y, z0), (-0.99, Y, z0), (0.99, Y, z0), (-0.99, Y, z1), (0.99, Y, z1)] +
            ([(-0.99, -Y, z0 + 0.01), (0.99, -Y, z0 + 0.01)] if z0 > 0 else []), lambda f: 'conc3' if f.normal.z > 0.3 else 'conc')
    sl = (h1 - h0) / L
    n = int(L / 0.5)
    for i in range(1, n):
        y = -Y + i * 0.5
        z = h0 + (y + Y) * sl
        k.bxr(0, y, z + 0.008, 1.7, 0.06, 0.02, 'concD', rot=(math.degrees(math.atan(sl)), 0, 0), ink=False)
    for s in (-1, 1):
        x = s * 0.925
        ya, yb = -Y + 0.012, Y - 0.012
        za, zb = h0 + 0.012 * sl, h1 - 0.012 * sl
        k.hullp([(x - 0.07, ya, za), (x + 0.07, ya, za), (x - 0.07, yb, zb), (x + 0.07, yb, zb),
                 (x - 0.07, ya, za + 0.16), (x + 0.07, ya, za + 0.16), (x - 0.07, yb, zb + 0.16), (x + 0.07, yb, zb + 0.16)], 'conc2')
        k.beam((x, -Y + 0.05, h0 + 1.05), (x, Y - 0.05, h1 + 1.05), 0.06, 'amber')
        k.beam((x, -Y + 0.05, h0 + 0.58), (x, Y - 0.05, h1 + 0.58), 0.04, 'amber', ink=False)
        for j in range(int(L / 1.5) + 1):
            y = -Y + 0.1 + j * (L - 0.2) / int(L / 1.5)
            z = h0 + (y + Y) * sl
            k.cyl(x, y, z + 0.14, 0.035, 0.035, 0.93, 'steel2', seg=5, ink=False)
        # side guard: three boxes up to the rail top along each side
        seg = 3
        for j in range(seg):
            ya, yb = -Y + j * L / seg, -Y + (j + 1) * L / seg
            k.col(x - 0.08, x + 0.08, ya, yb, 0.0, h0 + (yb + Y) * sl + 1.1)
    steps(k, -0.84, 0.84, -Y, Y, h0, h1, int(round(L / 0.5)))
    k.finish(name, ao=ao)


def build_ramps(k, ao):
    ramp(k, 6.0, 0.0, 1.8, ao, 'RampLo')
    ramp(k, 6.0, 1.8, T1, ao, 'RampHi')
    ramp(k, 12.0, 0.0, T1, ao, 'RampLong')
    # deck-edge railing along Blender Y (link runs): olive posts, steel rails, a kick plate
    def rail(y0, y1, post):
        k.cyl(0, y0, 1.05, 0.04, 0.04, y1 - y0, 'amber', seg=6, rot=(-90, 0, 0), caps=False)
        k.cyl(0, y0, 0.55, 0.028, 0.028, y1 - y0, 'amber', seg=6, rot=(-90, 0, 0), caps=False, ink=False)
        k.bx(-0.02, 0.02, y0, y1, 0.01, 0.12, 'olive2', ink=False)
        if post:
            k.cyl(0, 0, 0.0, 0.03, 0.03, 1.02, 'olive2', seg=5, ink=False)
    k.begin(); rail(-0.5, 0.5, True); k.col(-0.07, 0.07, -0.5, 0.5, 0.0, 1.1); k.finish('RailFull', ao=ao)
    k.begin(); rail(-0.5, -0.04, False); k.col(-0.07, 0.07, -0.5, 0.0, 0.0, 1.1); k.finish('RailHalf', ao=ao)
    k.begin()
    k.cyl(0, 0, 0.0, 0.055, 0.055, 1.1, 'olive2', seg=6)
    k.cyl(0, 0, 1.1, 0.07, 0.04, 0.05, 'olive', seg=6)
    k.finish('RailPost', ao=ao)


# ================================================================ helipad and helicopter
def build_heli(k, ao):
    # pad [14, 14]: dark asphalt square, white border, yellow touchdown ring, a big H, edge lights (glow)
    k.begin()
    k.qz(-6.8, 6.8, -6.8, 6.8, 0.012, 1, 'asph')
    for (x0, x1, y0, y1) in ((-6.6, 6.6, -6.6, -6.35), (-6.6, 6.6, 6.35, 6.6), (-6.6, -6.35, -6.35, 6.35), (6.35, 6.6, -6.35, 6.35)):
        k.qz(x0, x1, y0, y1, 0.016, 1, 'paint')
    N = 28
    for i in range(N):
        a0, a1 = i / N * 2 * math.pi, (i + 1) / N * 2 * math.pi
        if i % 2:
            continue
        pts = [(math.cos(a) * r, math.sin(a) * r, 0.018) for (a, r) in ((a0, 4.6), (a1, 4.6), (a1, 5.1), (a0, 5.1))]
        k.poly(pts, 'amber', (0, 0, 1))
    for (x0, x1, y0, y1) in ((-1.9, -1.1, -2.6, 2.6), (1.1, 1.9, -2.6, 2.6), (-1.1, 1.1, -0.38, 0.38)):
        k.qz(x0, x1, y0, y1, 0.02, 1, 'paint')
    for i in range(16):
        t = i / 16 * 4
        side, f = int(t), t - int(t)
        x, y = [(-6.0 + 12 * f, -6.0), (6.0, -6.0 + 12 * f), (6.0 - 12 * f, 6.0), (-6.0, 6.0 - 12 * f)][side]
        k.cyl(x, y, 0.0, 0.11, 0.1, 0.12, 'steelD', seg=6)
    k.finish('Landmark_Helipad', ao=False)
    k.begin()   # the pad lights' lenses (drawn unlit)
    for i in range(16):
        t = i / 16 * 4
        side, f = int(t), t - int(t)
        x, y = [(-6.0 + 12 * f, -6.0), (6.0, -6.0 + 12 * f), (6.0 - 12 * f, 6.0), (-6.0, 6.0 - 12 * f)][side]
        k.cyl(x, y, 0.12, 0.08, 0.05, 0.06, 'lamp' if i % 4 else 'beacon', seg=6, ink=False)
    k.finish('Landmark_Helipad_Glow', ao=False)

    # utility helicopter (made-up HW-7 Kestrel), nose toward -Y; modelled with the rotor mast at y = -0.6 and shifted
    # 2 m toward -Y so nose to tail (-6.6 .. 6.75) stays on the 14 m pad
    k.begin()
    k.push(0, -2.0, 0)

    def hc(f):
        n = f.normal
        return 'oliveL' if n.z > 0.55 else ('olive2' if n.z < -0.4 else 'olive')
    # cabin and nose
    sec = [(-4.6, 0.55, 0.75, 1.15, 0.3), (-3.6, 1.0, 0.55, 2.35, 0.6), (-2.2, 1.2, 0.5, 2.7, 0.75), (0.8, 1.2, 0.55, 2.75, 0.78),
           (2.2, 0.9, 0.8, 2.55, 0.6)]
    pts = []
    for (y, hw, z0, z1, tw) in sec:
        pts += [(-hw, y, z0), (hw, y, z0), (-tw, y, z1), (tw, y, z1), (-hw * 1.02, y, (z0 + z1) * 0.5), (hw * 1.02, y, (z0 + z1) * 0.5)]
    k.hullp(pts, hc)
    # cockpit glazing (two side windows and the windscreen), slightly proud
    k.hullp([(-0.62, -4.25, 1.05), (0.62, -4.25, 1.05), (-0.95, -3.35, 1.25), (0.95, -3.35, 1.25), (-0.55, -3.3, 2.3), (0.55, -3.3, 2.3),
             (-0.4, -4.05, 1.4), (0.4, -4.05, 1.4)], 'glass')
    for s in (-1, 1):
        k.bx(s * 1.205 - 0.005, s * 1.205 + 0.005, -3.1, -2.2, 1.45, 2.2, 'glassD', ink=False)
        k.bx(s * 1.205 - 0.005, s * 1.205 + 0.005, -1.6, 0.4, 0.75, 2.25, 'olive2', ink=False)   # sliding door
        k.bx(s * 1.212 - 0.004, s * 1.212 + 0.004, -1.25, -0.25, 1.65, 2.05, 'glassD', ink=False)
        k.text('HW-07', s * 1.215, 1.4, 1.4, 0.32, 'paint', face='x+' if s > 0 else 'x-', font='display')
    # engine housing, exhausts, rotor mast, hub, four blades
    k.hullp([(-0.75, -1.9, 2.7), (0.75, -1.9, 2.7), (-0.8, 1.8, 2.7), (0.8, 1.8, 2.7), (-0.55, -1.4, 3.25), (0.55, -1.4, 3.25),
             (-0.5, 1.4, 3.2), (0.5, 1.4, 3.2)], hc)
    for s in (-1, 1):
        k.cyl(s * 0.55, 1.6, 2.95, 0.16, 0.18, 0.4, 'steelD', seg=6, rot=(-90, 0, 0))
    k.cyl(0, -0.6, 3.2, 0.13, 0.11, 0.55, 'steel2', seg=8)
    k.cyl(0, -0.6, 3.72, 0.32, 0.26, 0.2, 'steelD', seg=8)
    for i in range(4):
        a = math.radians(i * 90 + 25)
        r0, r1 = 0.28, 6.7
        m = (r0 + r1) / 2
        k.bxr(math.cos(a) * m, -0.6 + math.sin(a) * m, 3.83 + 0.01 * (i % 2), r1 - r0, 0.36, 0.06, 'steelD', rot=(0, 0, math.degrees(a)))
    # tail boom, fin, stabiliser, tail rotor
    k.hullp([(-0.55, 2.0, 1.7), (0.55, 2.0, 1.7), (-0.5, 2.0, 2.55), (0.5, 2.0, 2.55), (-0.16, 8.0, 2.05), (0.16, 8.0, 2.05),
             (-0.14, 8.0, 2.4), (0.14, 8.0, 2.4)], hc)
    k.hullp([(-0.07, 7.3, 2.3), (0.07, 7.3, 2.3), (-0.07, 8.4, 2.3), (0.07, 8.4, 2.3), (-0.05, 8.3, 3.7), (0.05, 8.3, 3.7),
             (-0.05, 8.75, 3.75), (0.05, 8.75, 3.75)], 'olive')
    k.bx(-1.1, 1.1, 6.6, 7.0, 2.1, 2.2, 'olive2')
    k.cyl(0.1, 8.45, 3.25, 0.1, 0.1, 0.12, 'steelD', seg=6, rot=(0, 90, 0))
    for i, a in enumerate((20, 110)):
        k.bxr(0.235 + 0.05 * i, 8.45, 3.25, 0.04, 0.12, 1.5, 'steelD', rot=(a, 0, 0))
    # skids
    for s in (-1, 1):
        k.cyl(s * 1.25, -3.9, 0.1, 0.06, 0.06, 6.0, 'steel2', seg=6, rot=(-90, 0, 0))
        for y in (-2.9, 0.7):
            k.beam((s * 1.25, y, 0.1), (s * 0.85, y, 0.85), 0.07, 'steel2', ink=False)
    # insignia (made up): white star in a dark disc on both sides of the boom
    for s in (-1, 1):
        x = s * 0.47
        k.text('*', s * 0.535, 3.3, 1.86, 0.5, 'paint', face='x+' if s > 0 else 'x-', font='sans')
    k.pop()
    S = -2.0
    k.col(-1.0, 1.0, -4.35 + S, -3.6 + S, 0.0, 2.3)
    k.col(-1.25, 1.25, -3.6 + S, 2.2 + S, 0.0, 2.9)
    k.col(-0.5, 0.5, 2.2 + S, 5.0 + S, 1.6, 2.6)
    k.col(-0.3, 0.3, 5.0 + S, 8.0 + S, 1.9, 2.5)
    k.finish('Landmark_Helicopter', ao=ao)


# ================================================================ radome, comms mast, floodlights, windsock
def build_masts(k, ao):
    # radome [4, 4]: concrete plinth, steel drum with a door, white faceted dome, a small antenna mast
    k.begin()
    k.bx(-1.85, 1.85, -1.85, 1.85, 0.0, 0.55, 'conc')
    k.bx(-1.9, 1.9, -1.9, 1.9, 0.55, 0.65, 'conc3')
    k.cyl(0, 0, 0.65, 1.5, 1.5, 1.4, 'steel', seg=12)
    k.bx(-0.4, 0.4, -1.52, -1.4, 0.66, 2.0, 'steel2')
    k.cyl(0, 0, 2.05, 1.62, 1.62, 0.1, 'steel2', seg=12, ink=False)
    k.sph(0, 0, 2.15, 1.75, 'paint', seg=(12, 7), scale=(1, 1, 0.95))
    k.cyl(1.4, 1.4, 0.65, 0.06, 0.05, 4.6, 'steelD', seg=6)
    k.bx(1.15, 1.65, 1.47, 1.55, 4.6, 5.0, 'steel2')
    k.col(-1.9, 1.9, -1.9, 1.9, 0.0, 0.65)
    k.col(-1.5, 1.5, -1.5, 1.5, 0.65, 3.9)
    k.finish('Landmark_Radar', ao=ao)
    # comms mast [2, 2]: concrete plinth, 15 m lattice mast, two dishes, panel antennas, red beacon (glow)
    k.begin()
    k.bx(-0.8, 0.8, -0.8, 0.8, 0.0, 1.2, 'conc')
    k.bx(-0.85, 0.85, -0.85, 0.85, 1.2, 1.3, 'conc3')
    lattice(k, 0, 0, 1.3, 15.0, 1.1, 0.42, 'steel', every=1.9)
    for (z, a, r) in ((8.2, -90, 0.55), (11.0, 0, 0.45)):
        ang = math.radians(a)
        dx, dy = math.cos(ang), math.sin(ang)
        k.push(dx * 0.5, dy * 0.5, a + 90, z=z)
        k.cyl(0, -0.05, 0, r, 0.12, 0.28, 'paint', seg=10, rot=(90, 0, 0))
        k.cyl(0, -0.28, 0, 0.03, 0.03, 0.35, 'steelD', seg=4, rot=(90, 0, 0), ink=False)
        k.pop()
    for a in (0, 120, 240):
        ang = math.radians(a)
        k.bx(math.cos(ang) * 0.28 - 0.08, math.cos(ang) * 0.28 + 0.08, math.sin(ang) * 0.28 - 0.04, math.sin(ang) * 0.28 + 0.04, 13.2, 14.6, 'paint')
    k.cyl(0, 0, 15.2, 0.03, 0.02, 2.0, 'steelD', seg=4)
    k.cyl(0, 0, 15.0, 0.12, 0.12, 0.2, 'steelD', seg=6)
    k.col(-0.85, 0.85, -0.85, 0.85, 0.0, 1.3)
    k.finish('Mast', ao=ao)
    k.begin()
    k.cyl(0, 0, 15.2, 0.1, 0.07, 0.16, 'beacon', seg=6, ink=False)
    k.finish('Mast_Glow', ao=False)
    # floodlight tower [1, 1]: steel pole, cross bar with four lamps facing -Y
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.3, 'conc')
    k.cyl(0, 0, 0.3, 0.1, 0.08, 6.6, 'steel2', seg=6)
    k.bx(-0.8, 0.8, -0.06, 0.06, 6.6, 6.72, 'steelD')
    for x in (-0.6, -0.2, 0.2, 0.6):
        k.bxr(x, -0.15, 6.95, 0.32, 0.22, 0.26, 'steelD', rot=(-20, 0, 0))
    for z in range(1, 6):
        k.bx(0.09, 0.12, -0.12, 0.12, z * 1.1, z * 1.1 + 0.04, 'steel', ink=False)
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 6.6)
    k.finish('Flood', ao=ao)
    k.begin()
    for x in (-0.6, -0.2, 0.2, 0.6):
        k.bxr(x, -0.265, 6.91, 0.26, 0.012, 0.2, 'lampW', rot=(-20, 0, 0), ink=False)
    k.finish('Flood_Glow', ao=False)
    # windsock [1, 1]
    k.begin()
    k.bx(-0.25, 0.25, -0.25, 0.25, 0.0, 0.2, 'conc')
    k.cyl(0, 0, 0.2, 0.05, 0.04, 4.4, 'steel', seg=6)
    k.cyl(0, 0, 4.4, 0.04, 0.04, 0.3, 'steelD', seg=4, rot=(0, 90, 0))
    for i in range(5):
        x0 = 0.3 + i * 0.36
        r0, r1 = 0.3 - i * 0.04, 0.3 - (i + 1) * 0.04
        k.cyl(x0, 0, 4.4 - i * 0.07, r0, r1, 0.35, 'amber' if i % 2 == 0 else 'paint', seg=8, rot=(0, 95, 0))
    k.col(-0.25, 0.25, -0.25, 0.25, 0.0, 4.4)
    k.finish('Windsock', ao=ao)


# ================================================================ supplies and vehicles
def build_supplies(k, ao):
    k.begin()   # crate stack A: a long rifle crate on a big ammo crate
    crate(k, 0.0, 0.0, 0.0, 0.86, 0.66, 0.62, 'olive', 'olive2', 'AMMO')
    crate(k, -0.05, 0.02, 0.62, 0.8, 0.36, 0.3, 'oliveL', 'olive2')
    k.col(-0.43, 0.43, -0.33, 0.33, 0.0, 0.92)
    k.finish('Crate_A', ao=ao)
    k.begin()   # B: two wooden supply crates stacked
    crate(k, 0.0, 0.0, 0.0, 0.88, 0.82, 0.7, 'crate', 'crate2', 'MRE')
    crate(k, 0.04, -0.02, 0.7, 0.7, 0.66, 0.55, 'crate', 'crate2')
    k.col(-0.44, 0.44, -0.41, 0.41, 0.0, 1.25)
    k.finish('Crate_B', ao=ao)
    k.begin()   # C: ammo cans, two layers
    for i in range(4):
        x = -0.33 + i * 0.22
        k.bx(x - 0.09, x + 0.09, -0.3, 0.0, 0.0, 0.28, 'olive2')
        k.bx(x - 0.09, x + 0.09, 0.05, 0.35, 0.0, 0.28, 'olive')
    for i in range(3):
        x = -0.22 + i * 0.22
        k.bx(x - 0.09, x + 0.09, -0.15, 0.15, 0.28, 0.56, 'olive')
        k.bx(x - 0.03, x + 0.03, -0.1, 0.1, 0.56, 0.6, 'steelD', ink=False)
    k.col(-0.42, 0.42, -0.3, 0.35, 0.0, 0.56)
    k.finish('AmmoCans', ao=ao)
    k.begin()   # pallet stack [2, 2]: crates on a pallet under a strapped tarp
    k.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.14, 'wood')
    k.hullp([(-0.85, -0.85, 0.14), (0.85, -0.85, 0.14), (0.85, 0.85, 0.14), (-0.85, 0.85, 0.14),
             (-0.8, -0.8, 1.35), (0.8, -0.8, 1.35), (0.8, 0.8, 1.35), (-0.8, 0.8, 1.35), (0, 0, 1.5)], lambda f: 'tarp' if f.normal.z < 0.95 else 'olive')
    for x in (-0.45, 0.45):
        k.bx(x - 0.04, x + 0.04, -0.86, 0.86, 1.36, 1.38, 'olive2', ink=False)
    k.col(-0.9, 0.9, -0.9, 0.9, 0.0, 1.4)
    k.finish('Stack', ao=ao)
    k.begin()   # three drums (fuel / water)
    drum(k, -0.255, -0.15, r=0.245, c='olive')
    drum(k, 0.255, -0.15, r=0.245, h=0.84, c='red', ring='rust')
    drum(k, 0.0, 0.29, r=0.245, h=0.9, c='olive')
    k.col(-0.48, 0.48, -0.4, 0.48, 0.0, 0.88)
    k.finish('Drums', ao=ao)
    # camouflage net over a supply dump [4, 4]: four poles, a draped net, crates under it
    k.begin()
    rnd = random.Random(41)
    for (x, y) in ((-1.7, -1.7), (1.7, -1.7), (1.7, 1.7), (-1.7, 1.7)):
        k.cyl(x, y, 0.0, 0.05, 0.05, 2.45, 'wood', seg=5)
    net = []
    for i in range(5):
        for j in range(5):
            x, y = -1.95 + i * 0.975, -1.95 + j * 0.975
            edge = i in (0, 4) or j in (0, 4)
            z = 2.45 if (i, j) in ((0, 0), (4, 0), (4, 4), (0, 4)) else (2.0 + rnd.uniform(-0.15, 0.1) if edge else 2.65 + rnd.uniform(-0.1, 0.1))
            net.append((x, y, z))
    cols = ('olive', 'olive2', 'tarp', 'oliveL')
    for i in range(4):
        for j in range(4):
            a, b, c, d = net[i * 5 + j], net[(i + 1) * 5 + j], net[(i + 1) * 5 + j + 1], net[i * 5 + j + 1]
            col = cols[(i * 3 + j * 5) % 4]
            k.poly([a, b, c], col, (0, 0, 1))
            k.poly([a, c, d], col, (0, 0, 1))
            k.poly([a, c, b], col, (0, 0, -1))
            k.poly([a, d, c], col, (0, 0, -1))
    crate(k, -0.8, -0.6, 0.0, 0.9, 0.7, 0.7, 'olive', 'olive2', 'AMMO')
    crate(k, 0.35, -0.65, 0.0, 0.9, 0.7, 0.7, 'crate', 'crate2')
    crate(k, -0.2, 0.55, 0.0, 1.2, 0.8, 0.8, 'olive', 'olive2', 'MED')
    crate(k, -0.25, 0.55, 0.8, 0.8, 0.6, 0.5, 'oliveL', 'olive2')
    k.col(-1.25, 0.8, -1.0, -0.25, 0.0, 0.7)
    k.col(-0.8, 0.4, 0.15, 0.95, 0.0, 1.3)
    for (x, y) in ((-1.7, -1.7), (1.7, -1.7), (1.7, 1.7), (-1.7, 1.7)):
        k.col(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 2.4)
    k.finish('CamoNet', ao=ao)

    # generator [2, 1]: genset on skids (along X), exhaust stack, control panel, cable reel
    k.begin()
    k.bx(-0.95, 0.95, -0.45, 0.45, 0.0, 0.12, 'steelD')
    k.bx(-0.85, 0.85, -0.4, 0.4, 0.12, 1.15, 'olive')
    k.bx(-0.88, 0.88, -0.43, 0.43, 1.15, 1.22, 'olive2')
    for i in range(6):
        x = -0.7 + i * 0.16
        k.bx(x, x + 0.08, -0.405, -0.4, 0.4, 0.95, 'olive2', ink=False)
    k.bx(0.35, 0.75, -0.405, -0.4, 0.55, 0.95, 'steelD', ink=False)
    k.bx(0.42, 0.5, -0.41, -0.405, 0.8, 0.88, 'lamp', ink=False)
    k.cyl(-0.6, 0.15, 1.22, 0.07, 0.07, 0.55, 'steelD', seg=6)
    k.text('POWER 60KW', 0.0, 0.405, 0.7, 0.13, 'paint', face='y+', font='display')
    k.col(-0.95, 0.95, -0.45, 0.45, 0.0, 1.22)
    k.finish('Generator', ao=ao)

    # fuel bowser [2, 4]: a tank trailer along Y (towbar -Y), four wheels, hose reel, stencil
    k.begin()
    k.bx(-0.75, 0.75, -1.6, 1.7, 0.42, 0.55, 'steelD')
    k.cyl(0, -1.45, 1.15, 0.72, 0.72, 3.0, 'olive', seg=12, rot=(-90, 0, 0))
    for y in (-1.45, 1.55):
        k.cyl(0, y, 1.15, 0.74, 0.74, 0.06, 'olive2', seg=12, rot=(-90, 0, 0), caps=False, ink=False)
    k.cyl(0, 0.0, 1.85, 0.2, 0.2, 0.12, 'olive2', seg=8)
    for (x, y) in ((-0.82, -0.6), (0.82, -0.6), (-0.82, 0.6), (0.82, 0.6)):
        k.cyl(x - 0.12 if x < 0 else x - 0.12, y, 0.38, 0.38, 0.38, 0.24, 'tire', seg=10, rot=(0, 90, 0))
    k.beam((0, -1.6, 0.5), (0, -2.0, 0.42), 0.08, 'steelD')
    k.cyl(0, 1.75, 0.6, 0.22, 0.22, 0.25, 'steelD', seg=8, rot=(-90, 0, 0))
    for s in (-1, 1):
        k.text('JET FUEL', s * 0.725, 0.05, 0.98, 0.26, 'paint', face='x+' if s > 0 else 'x-', font='display')
    k.col(-0.95, 0.95, -1.8, 1.85, 0.0, 1.9)
    k.finish('Bowser', ao=ao)

    # signpost [1, 1]: arrow boards (front -Y)
    k.begin()
    k.cyl(0, 0, 0, 0.05, 0.05, 2.6, 'steel2', seg=6)
    for (z, txt, d) in ((2.2, 'HELIPAD', -1), (1.75, 'COMMAND', 1), (1.3, 'ARMORY', 1)):
        x0, x1 = (-1.0, 0.05) if d < 0 else (-0.05, 1.0)
        k.bx(x0, x1, -0.06, -0.02, z - 0.18, z + 0.18, 'olive2')
        tip = x0 - 0.2 if d < 0 else x1 + 0.2
        base = x0 if d < 0 else x1
        k.poly([(base, -0.04, z - 0.18), (tip, -0.04, z), (base, -0.04, z + 0.18)], 'olive2', (0, -1, 0))
        k.text(txt, (x0 + x1) / 2, -0.064, z - 0.1, 0.2, 'paint', maxw=0.9, font='display')
    k.col(-0.1, 0.1, -0.1, 0.1, 0.0, 2.4)
    k.finish('Signpost', ao=ao)


def wheel(k, x, y, z, r, w, c='tire', hub='olive2', axis='x'):
    rot = (0, 90, 0) if axis == 'x' else (90, 0, 0)
    k.cyl(x - w / 2, y, z, r, r, w, c, seg=10, rot=rot) if axis == 'x' else k.cyl(x, y - w / 2, z, r, r, w, c, seg=10, rot=rot)
    k.cyl(x + (w / 2 + 0.005 if x > 0 else -w / 2 - 0.015), y, z, r * 0.5, r * 0.5, 0.01, hub, seg=8, rot=rot, ink=False)


def build_jeep(k, ao):
    # military 4x4 utility vehicle [2, 4] (made-up HAWK 4x4), nose toward -Y
    k.begin()

    def jc(f):
        return 'oliveL' if f.normal.z > 0.6 else ('olive2' if f.normal.z < -0.3 else 'olive')
    k.hullp([(-0.9, -1.95, 0.45), (0.9, -1.95, 0.45), (-0.9, 1.9, 0.45), (0.9, 1.9, 0.45), (-0.88, -1.95, 1.0), (0.88, -1.95, 1.0),
             (-0.9, -0.6, 1.15), (0.9, -0.6, 1.15), (-0.9, 1.9, 1.15), (0.9, 1.9, 1.15)], jc)
    k.bx(-0.7, 0.7, -0.25, 1.75, 1.15, 1.2, 'steelD', ink=False)
    k.bx(-0.75, 0.75, -0.1, 0.4, 1.2, 1.55, 'olive2')     # seats back
    k.bx(-0.85, 0.85, -0.68, -0.62, 1.15, 1.75, 'steelD')   # windscreen frame
    k.bx(-0.78, 0.78, -0.69, -0.67, 1.22, 1.68, 'glass', ink=False)
    for x in (-0.85, 0.85):
        for y in (0.6, 1.6):
            k.cyl(x, y, 1.15, 0.04, 0.04, 0.86, 'steelD', seg=6, ink=False)
        k.cyl(x, 0.6, 1.98, 0.03, 0.03, 1.0, 'steelD', seg=6, rot=(-90, 0, 0), ink=False)
    k.cyl(-0.85, 0.6, 1.95, 0.026, 0.026, 1.7, 'steelD', seg=6, rot=(0, 90, 0), ink=False)
    k.bx(-0.95, 0.95, -2.05, -1.92, 0.4, 0.62, 'steelD')
    for x in (-0.6, 0.6):
        k.bx(x - 0.12, x + 0.12, -1.97, -1.95, 0.75, 0.88, 'lamp', ink=False)
    k.cyl(0, 1.92, 0.95, 0.36, 0.36, 0.22, 'tire', seg=10, rot=(-90, 0, 0))
    for (x, y) in ((-0.82, -1.25), (0.82, -1.25), (-0.82, 1.2), (0.82, 1.2)):
        wheel(k, x, y, 0.42, 0.42, 0.3)
    k.col(-0.98, 0.98, -2.05, 1.95, 0.0, 1.2)
    k.col(-0.9, 0.9, -0.7, 1.7, 1.2, 1.75)
    k.finish('Jeep', ao=ao)


# ================================================================ gate, trail, hatch
def build_gate(k, ao):
    k.begin()   # concrete blast portal: pylons, lintel, steel frame, hazard stripes, name, warning lamps
    for s in (-1, 1):
        x0, x1 = (s * 1.5, s * 2.5) if s > 0 else (s * 2.5, s * 1.5)
        k.bx(x0, x1, -0.75, 0.75, 0.0, 3.45, 'conc')
        k.bx(x0 - 0.04, x1 + 0.04, -0.8, 0.8, 0.0, 0.3, 'concD')
        xi = s * 1.5
        k.bx(min(xi, xi - s * 0.12), max(xi, xi - s * 0.12), -0.6, 0.6, 0.0, 3.33, 'steel2')
        for (y, f) in ((-0.754, -1), (0.754, 1)):
            a, b = (s * 1.6, s * 2.4) if s > 0 else (s * 2.4, s * 1.6)
            k.stripes(a, b, 0.35, 1.6, y, f, 4)
        for y in (-0.8, 0.8):
            k.bx(s * 2.0 - 0.14, s * 2.0 + 0.14, y - 0.06 if y < 0 else y, y if y < 0 else y + 0.06, 4.1, 4.38, 'steelD')
    k.bx(-2.55, 2.55, -0.8, 0.8, 3.45, 5.6, 'conc')
    k.bx(-2.6, 2.6, -0.85, 0.85, 5.6, 5.78, 'conc3')
    k.bx(-1.5, 1.5, -0.62, 0.62, 3.33, 3.44, 'steelD')
    for (y, face) in ((-0.802, 'y-'), (0.802, 'y+')):
        k.bx(-1.75, 1.75, y - 0.004, y + 0.004, 4.05, 5.0, 'olive2', ink=False)
        k.text('HIGHWATCH', 0.0, y - 0.009 if y < 0 else y + 0.009, 4.2, 0.62, 'paint', face=face, maxw=3.3, font='display')
    k.col(1.5, 2.5, -0.75, 0.75, 0.0, 5.6)
    k.col(-2.5, -1.5, -0.75, 0.75, 0.0, 5.6)
    k.finish('GateFrame', ao=ao)
    k.begin()
    for s in (-1, 1):
        for y in (-0.87, 0.87):
            k.bx(s * 2.0 - 0.1, s * 2.0 + 0.1, y - 0.01 if y < 0 else y, y if y < 0 else y + 0.01, 4.14, 4.34, 'beacon', ink=False)
    k.finish('GateFrame_Glow', ao=False)
    k.begin()   # the rock face over the portal (dress), up to the cliff top, both sides
    rnd = random.Random(51)
    rock_face(k, rnd, -2.5, 2.5, CLIFF_H, ROCK, z0=5.75, over=0.05)
    rock_face(k, rnd, -2.5, 2.5, CLIFF_H, ROCK, z0=5.75, over=0.05, y0=0.5, side=1)
    k.finish('GateRock', ao=ao)
    k.begin()   # blast door: steel slab panels, rivet bands, hazard chevrons at the foot
    Hs = 3.05
    k.bx(-1.5, 1.5, -0.1, 0.1, 0.0, Hs, 'steel2', ink=False)
    for z in (0.75, 1.55, 2.35):
        k.bx(-1.5, 1.5, -0.12, -0.1, z, z + 0.08, 'steelD', ink=False)
        k.bx(-1.5, 1.5, 0.1, 0.12, z, z + 0.08, 'steelD', ink=False)
    k.bx(-0.04, 0.04, -0.125, 0.125, 0.0, Hs - 0.02, 'steelD', ink=False)
    for y, s in ((-0.13, -1), (0.13, 1)):
        k.stripes(-1.5, 1.5, 0.05, 0.42, y, s, 10)
    obj = k.finish('GateShutter', ao=False)
    shutter_hull(k.pal, obj)
    k.tris[k.prefix + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    k.begin()   # exit hatch: round steel blast hatch in a concrete collar
    k.cyl(0, 0, 0, 1.3, 1.25, 0.14, 'conc', seg=16)
    k.cyl(0, 0, 0.14, 1.0, 1.0, 0.04, 'steel2', seg=16)
    k.cyl(0, 0, 0.18, 0.95, 0.95, 0.008, 'amber', seg=16, ink=False)
    k.cyl(0, 0, 0.188, 0.75, 0.75, 0.01, 'steel2', seg=16, ink=False)
    for i in range(4):
        a = i * 90 + 45
        k.bxr(math.cos(math.radians(a)) * 0.35, math.sin(math.radians(a)) * 0.35, 0.24, 0.5, 0.08, 0.06, 'steelD', rot=(0, 0, a))
    k.finish('Hatch', ao=ao)


def build_trail(k, ao):
    """tunnel lining modules (1 m along Blender Y, face +X at x = 0.25): concrete wainscot, shotcrete above, a cable
    tray, lamps / pipes / signs per variant; the theme ceiling (5 m) closes the top"""
    def wall(name, extra=None, seed=0):
        rnd = random.Random(seed)
        k.begin()
        k.bx(-0.25, 0.25, -0.5, 0.5, 0.18, 2.6, 'conc')
        k.bx(-0.25, 0.28, -0.5, 0.5, 0.0, 0.18, 'concD')
        k.bx(-0.25, 0.22, -0.5, 0.5, 2.6, TRAIL_H + 0.04, 'cave3')
        k.bxr(0.21, 0.0, 3.8 + rnd.uniform(-0.3, 0.3), 0.06, 0.96, 0.9, 'cave', rot=(0, rnd.uniform(-2, 2), 0))
        k.bx(0.25, 0.42, -0.5, 0.5, 3.1, 3.16, 'steel2', ink=False)
        k.bx(0.38, 0.42, -0.5, 0.5, 3.16, 3.24, 'steel2', ink=False)
        k.bx(0.27, 0.36, -0.5, 0.5, 3.17, 3.22, 'olive2', ink=False)
        if extra:
            extra()
        k.finish(name, ao=ao)

    wall('TrailWall', seed=1)

    def lamp():
        k.bx(0.25, 0.4, -0.18, 0.18, 2.75, 2.95, 'steelD')
        k.bx(0.4, 0.41, -0.15, 0.15, 2.78, 2.92, 'lamp', ink=False)
    wall('TrailWall_Lamp', lamp, 2)

    def pipe():
        k.cyl(0.36, -0.5, 1.9, 0.09, 0.09, 1.0, 'steel', seg=8, rot=(-90, 0, 0), caps=False)
        k.cyl(0.34, -0.5, 2.25, 0.06, 0.06, 1.0, 'olive', seg=6, rot=(-90, 0, 0), caps=False, ink=False)
    wall('TrailWall_Pipe', pipe, 3)

    def sign():
        k.bx(0.25, 0.27, -0.42, 0.42, 1.2, 1.9, 'amber', ink=False)
        k.text('NO SMOKING', 0.275, 0.0, 1.45, 0.16, 'ink', face='x+', maxw=0.78, font='display')
    wall('TrailWall_Sign', sign, 4)
    k.begin()   # ceiling lamp over the tunnel (hangs below the ceiling plane)
    k.bx(-0.2, 0.2, -0.6, 0.6, -0.18, 0.0, 'steelD')
    k.bx(-0.16, 0.16, -0.55, 0.55, -0.188, -0.18, 'lampW', ink=False)
    k.finish('TunnelLamp', ao=False)


def build_outer(k, ao):
    build_cliffs(k, ao)
    build_barriers(k, ao)
    build_forts(k, ao)
    build_ramps(k, ao)
    build_heli(k, ao)
    build_masts(k, ao)
    build_supplies(k, ao)
    build_jeep(k, ao)
    build_gate(k, ao)
    build_trail(k, ao)
