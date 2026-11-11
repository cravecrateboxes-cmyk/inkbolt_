"""INKBOLT kit-stronghold, inside the mountain (zone 2): carved rock hall faces (12 m, up to the cavern roof), the
terrace face (rock on the terrace side up to 14.2 m) and its doorway lintels, the cavern roof tiles, the vehicle hangar
(armoured truck, blast door, workbench, tool chests, tyres, engine hoist, bay paint, oil stains), the ammo depot
(ammo racks, shell pallets, gun racks, the armory cage), the barracks (bunks, footlockers, lockers, mess tables), the
command centre (the tactical table, consoles, the video wall, radio racks), mezzanine decks (posts, steel stairs) and
the observation terrace (spotting scopes, the twin AA gun, the flagpole). See sh_base.py for the conventions."""
import math
import random

from sh_base import (CLIFF_H, HALL_H, LINTEL, MEZZ, rock_face, rock_pillar, sandbag_row, sandbag_wall, crate, drum,  # noqa: F401
                     pipe_rail, rock_lump, steps)

CAVE = ('cave', 'cave2', 'cave3', 'cave3')
ROCK = ('rock', 'rock2', 'rock3', 'rockL')


# ================================================================ hall faces (face -Y, 12 m)
def build_halls(k, ao):
    def face(name, w, seed, extra=None, bands=4):
        rnd = random.Random(seed)
        k.begin()
        rock_face(k, rnd, -0.5, -0.5 + w, HALL_H, CAVE, split=0.75)
        if extra:
            extra(rnd)
        k.finish(name, ao=ao)

    face('Rock2_A', 2, 61)
    face('Rock2_B', 2, 62)
    face('Rock1', 1, 63)

    def lamp(rnd):   # caged bulkhead lamp on a bracket, conduit down to a junction box
        k.bx(0.3, 0.7, -0.68, -0.48, 3.2, 3.5, 'steelD')
        k.cyl(0.5, -0.6, 0.3, 0.025, 0.025, 2.9, 'steel2', seg=4, ink=False)
        k.bx(0.38, 0.62, -0.62, -0.48, 1.2, 1.5, 'olive2')
    face('Rock2_Lamp', 2, 64, lamp)
    k.begin()
    k.bx(0.34, 0.66, -0.69, -0.68, 3.24, 3.46, 'lamp', ink=False)
    k.finish('Rock2_Lamp_Glow', ao=False)

    def cable(rnd):   # cable tray and a pipe run along the face at 3 m, a stencilled sign
        k.bx(-0.5, 1.5, -0.75, -0.5, 3.0, 3.06, 'steel2', ink=False)
        k.bx(-0.5, 1.5, -0.75, -0.72, 3.06, 3.16, 'steel2', ink=False)
        k.cyl(-0.5, -0.62, 3.45, 0.07, 0.07, 2.0, 'olive', seg=6, rot=(0, 90, 0), caps=False)
        k.bx(0.1, 0.9, -0.62, -0.58, 1.3, 1.9, 'amber', ink=False)
        k.text('SECTOR %d' % rnd.randint(2, 7), 0.5, -0.625, 1.52, 0.18, 'ink', maxw=0.72, font='display')
    face('Rock2_Cable', 2, 65, cable)

    k.begin()   # corner pillar
    rock_pillar(k, random.Random(66), HALL_H, CAVE)
    k.finish('RockC', ao=ao)

    # terrace face modules (column between the halls and the terrace): hall side (-Y) to 12 m in the cave rock, the
    # terrace side (+Y, sunlit rock) up to 14.2 m where the massif's shell starts
    def tface(name, w, seed):
        rnd = random.Random(seed)
        k.begin()
        rock_face(k, rnd, -0.5, -0.5 + w, HALL_H, CAVE, back=0.38, split=0.8)
        rock_face(k, rnd, -0.5, -0.5 + w, CLIFF_H, ROCK, y0=0.5, back=0.38, side=1)
        k.finish(name, ao=ao)
    tface('Face2', 2, 67)
    tface('Face1', 1, 68)
    k.begin()   # terrace face corner: a 14.2 m pillar
    rock_pillar(k, random.Random(69), CLIFF_H, ROCK)
    k.finish('FaceC', ao=ao)
    # doorway lintel (a passage cell of the terrace face): clear up to 4.2 m, a steel beam, rock above both sides
    k.begin()
    rnd = random.Random(70)
    k.bx(-0.5, 0.5, -0.5, 0.5, LINTEL, LINTEL + 0.45, 'conc2')
    k.bx(-0.494, 0.494, -0.56, -0.5, LINTEL - 0.02, LINTEL + 0.3, 'steelD')
    k.bx(-0.494, 0.494, 0.5, 0.56, LINTEL - 0.02, LINTEL + 0.3, 'steelD')
    for i, (a, b) in enumerate(((LINTEL + 0.45, 8.0), (8.0, HALL_H))):
        k.bxr(0, -0.25, (a + b) / 2, 0.988 - 0.012 * i, 0.5, b - a - 0.01, CAVE[i], rot=(rnd.uniform(-2, 2), 0, 0))
    for i, (a, b) in enumerate(((LINTEL + 0.45, 8.3), (8.3, 11.2), (11.2, CLIFF_H))):
        k.bxr(0, 0.25, (a + b) / 2, 0.982 - 0.012 * i, 0.5, b - a - 0.01, ROCK[i + 1], rot=(rnd.uniform(-2, 2), 0, 0))
    k.finish('Lintel', ao=ao)

    # cavern roof [6, 8] (layer 12): a rock slab, its underside at the layer height, hanging lumps; B: a steel arch
    # rib with a hanging lamp; C: a vent duct and a cable tray
    def roof(name, seed, extra=None):
        rnd = random.Random(seed)
        k.begin()
        k.bx(-3.0, 3.0, -4.0, 4.0, 0.0, 0.9, 'cave2')
        for i, (y, w) in enumerate(((-2.6, 0.5), (0.4, 0.7), (2.9, 0.45))):   # blasting scars: shallow rock ribs across the tile
            y += rnd.uniform(-0.4, 0.4)
            k.hullp([(-2.98, y - w, 0.06), (2.98, y - w, 0.06 + 0.02 * i), (-2.98, y + w, 0.06), (2.98, y + w, 0.06 + 0.02 * i),
                     (-2.9, y + rnd.uniform(-0.1, 0.1), -rnd.uniform(0.12, 0.2)), (2.9, y + rnd.uniform(-0.1, 0.1), -rnd.uniform(0.12, 0.2))], 'cave')
        if extra:
            extra(rnd)
        k.finish(name, ao=ao)
    roof('Roof_A', 71)

    def rib(rnd):
        k.bx(-3.0, 3.0, -0.12, 0.12, -0.35, -0.012, 'steelD')
        k.bx(-3.0, 3.0, -0.2, 0.2, -0.4, -0.35, 'steel2', ink=False)
        k.cyl(0.0, 1.8, -1.6, 0.012, 0.012, 1.6, 'steelD', seg=4, ink=False)
        k.cyl(0.0, 1.8, -1.85, 0.28, 0.12, 0.25, 'steelD', seg=8)
    roof('Roof_B', 72, rib)
    k.begin()
    k.cyl(0.0, 1.8, -1.86, 0.24, 0.24, 0.012, 'lampW', seg=8, ink=False)
    k.finish('Roof_B_Glow', ao=False)

    def duct(rnd):
        k.bx(-3.0, 3.0, -1.6, -0.9, -0.75, -0.05, 'steel')
        for x in (-2.0, 0.0, 2.0):
            k.bx(x - 0.04, x + 0.04, -1.64, -0.86, -0.79, -0.09, 'steel2', ink=False)
            k.cyl(x, -1.25, -0.05, 0.02, 0.02, 0.05, 'steelD', seg=4, ink=False)
        k.bx(-3.0, 3.0, 1.0, 1.5, -0.3, -0.24, 'steel2', ink=False)
    roof('Roof_C', 73, duct)


# ================================================================ hangar
def wheel(k, x, y, z, r, w, c='tire'):
    k.cyl(x - w / 2, y, z, r, r, w, c, seg=10, rot=(0, 90, 0))
    k.cyl(x + (w / 2 + 0.003 if x > 0 else -w / 2 - 0.013), y, z, r * 0.52, r * 0.52, 0.01, 'olive2', seg=8, rot=(0, 90, 0), ink=False)


def build_hangar(k, ao):
    # armoured 6x6 truck [3, 7] (made-up BRUTE 6x6), nose toward -Y
    k.begin()

    def tc(f):
        return 'oliveL' if f.normal.z > 0.6 else ('olive2' if f.normal.z < -0.3 else 'olive')
    k.bx(-1.15, 1.15, -3.3, 3.2, 0.62, 0.92, 'steelD')
    # armoured cab: sloped bonnet and windscreen, slit windows
    k.hullp([(-1.25, -3.35, 0.9), (1.25, -3.35, 0.9), (-1.25, -1.0, 0.9), (1.25, -1.0, 0.9), (-1.2, -3.35, 1.7), (1.2, -3.35, 1.7),
             (-1.2, -2.5, 2.0), (1.2, -2.5, 2.0), (-1.15, -2.0, 2.9), (1.15, -2.0, 2.9), (-1.2, -1.0, 2.95), (1.2, -1.0, 2.95)], tc)
    k.hullp([(-1.0, -2.47, 2.06), (1.0, -2.47, 2.06), (-0.95, -2.06, 2.75), (0.95, -2.06, 2.75), (-1.0, -2.5, 2.04), (0.95, -2.03, 2.79)], 'glassD')
    for s in (-1, 1):
        k.bx(s * 1.227 - 0.005, s * 1.227 + 0.005, -1.9, -1.2, 2.2, 2.55, 'glassD', ink=False)
        k.bx(s * 1.24 - 0.004, s * 1.24 + 0.004, -1.95, -1.1, 1.0, 2.1, 'olive2', ink=False)   # door
    # troop compartment
    k.hullp([(-1.3, -0.95, 0.9), (1.3, -0.95, 0.9), (-1.3, 3.25, 0.9), (1.3, 3.25, 0.9), (-1.3, -0.95, 2.6), (1.3, -0.95, 2.6),
             (-1.3, 3.25, 2.6), (1.3, 3.25, 2.6), (-1.1, -0.95, 3.0), (1.1, -0.95, 3.0), (-1.1, 3.25, 3.0), (1.1, 3.25, 3.0)], tc)
    for s in (-1, 1):
        for y in (0.2, 1.4, 2.5):
            k.bx(s * 1.302 - 0.004, s * 1.302 + 0.004, y - 0.25, y + 0.25, 1.9, 2.1, 'ink', ink=False)
        k.bx(s * 1.31 - 0.004, s * 1.31 + 0.004, -0.6, 3.0, 1.0, 1.08, 'olive2', ink=False)
        k.text('BRUTE', s * 1.312, 1.6, 1.2, 0.36, 'paint', face='x+' if s > 0 else 'x-', font='display')
    k.bx(-0.6, 0.6, 3.25, 3.31, 1.0, 2.5, 'olive2')   # rear door
    k.bx(-0.08, 0.08, 3.31, 3.36, 1.6, 1.75, 'steelD', ink=False)
    # roof ring with a machine gun, jerry cans, spare tyre, bull bar, winch, lamps
    k.cyl(0, 1.0, 3.0, 0.62, 0.62, 0.18, 'olive2', seg=10)
    k.bx(-0.12, 0.12, 0.5, 1.0, 3.18, 3.45, 'gunmetal')
    k.cyl(0, 0.5, 3.33, 0.045, 0.04, 1.0, 'steelD', seg=6, rot=(90, 0, 0))
    k.bxr(0, 1.25, 3.42, 0.9, 0.06, 0.4, 'olive2', rot=(-12, 0, 0))
    for x in (-0.95, -0.6):
        k.bx(x - 0.15, x + 0.15, 3.0, 3.24, 2.6, 2.95, 'olive')
    k.cyl(0.65, 3.27, 1.85, 0.48, 0.48, 0.28, 'tire', seg=10, rot=(-90, 0, 0))
    k.bx(-1.2, 1.2, -3.55, -3.35, 0.6, 0.85, 'steelD')
    for x in (-1.05, 1.05):
        k.beam((x, -3.5, 0.75), (x * 0.95, -3.4, 1.55), 0.09, 'steelD', ink=False)
    k.bx(-0.35, 0.35, -3.5, -3.35, 0.88, 1.15, 'steel2')
    for x in (-0.85, 0.85):
        k.bx(x - 0.16, x + 0.16, -3.37, -3.35, 1.25, 1.45, 'lamp', ink=False)
    for y in (-2.1, 0.4, 2.0):
        for s in (-1, 1):
            wheel(k, s * 1.12, y, 0.6, 0.6, 0.42)
    k.col(-1.32, 1.32, -3.55, 3.32, 0.0, 3.0)
    k.finish('Landmark_Truck', ao=ao)

    # blast door [8, 1] set into the hangar wall (front -Y, back against the rock): two leaves, frame, stripes
    k.begin()
    k.bx(-4.0, 4.0, -0.2, 0.5, 6.0, 6.8, 'conc')
    for s in (-1, 1):
        x0, x1 = (s * 3.4, s * 4.0) if s > 0 else (s * 4.0, s * 3.4)
        k.bx(x0, x1, -0.2, 0.5, 0.0, 6.0, 'conc')
        k.stripes(x0 + 0.05, x1 - 0.05, 0.2, 2.0, -0.204, -1, 2)
    k.bx(-3.4, 3.4, 0.1, 0.4, 0.0, 6.0, 'steel2')
    for x in (-1.7, 1.7):
        for z in (1.0, 2.5, 4.0, 5.3):
            k.bx(x - 1.6, x + 1.6, 0.06, 0.1, z, z + 0.12, 'steelD', ink=False)
    k.bx(-0.04, 0.04, 0.05, 0.1, 0.0, 6.0, 'ink', ink=False)
    k.text('HANGAR 2', 0.0, -0.205, 6.15, 0.45, 'paint', maxw=4.0, font='display')
    k.col(-4.0, -3.4, -0.2, 0.5, 0.0, 6.0)
    k.col(3.4, 4.0, -0.2, 0.5, 0.0, 6.0)
    k.col(-3.4, 3.4, 0.08, 0.5, 0.0, 6.0)
    k.col(-4.0, 4.0, -0.2, 0.5, 6.0, 6.8)
    k.finish('BlastDoor', ao=ao)

    k.begin()   # workbench [2, 1] (front -Y): steel bench, vice, tools on a pegboard, drawers
    k.bx(-0.95, 0.95, -0.4, 0.35, 0.86, 0.94, 'wood')
    for x in (-0.88, 0.88):
        k.bx(x - 0.04, x + 0.04, -0.36, 0.3, 0.0, 0.86, 'steel2')
    k.bx(0.2, 0.84, -0.34, 0.28, 0.1, 0.8, 'olive2')
    for z in (0.3, 0.55):
        k.bx(0.24, 0.81, -0.345, -0.34, z, z + 0.04, 'steelD', ink=False)
    k.bx(-0.95, 0.95, 0.35, 0.45, 0.94, 2.0, 'olive')
    for (x, z, w, h) in ((-0.7, 1.2, 0.08, 0.5), (-0.5, 1.4, 0.3, 0.06), (-0.1, 1.15, 0.06, 0.6), (0.3, 1.5, 0.4, 0.3), (0.65, 1.2, 0.1, 0.45)):
        k.bx(x - w / 2, x + w / 2, 0.33, 0.35, z, z + h, 'steelD', ink=False)
    k.bx(-0.6, -0.35, -0.38, -0.18, 0.94, 1.1, 'steelD')
    k.col(-0.95, 0.95, -0.4, 0.45, 0.0, 0.94)
    k.col(-0.95, 0.95, 0.35, 0.45, 0.94, 2.0)
    k.finish('Workbench', ao=ao)

    k.begin()   # rolling tool chest [1, 1] (front -Y)
    k.bx(-0.36, 0.36, -0.25, 0.25, 0.12, 1.05, 'red')
    for i in range(5):
        z = 0.22 + i * 0.16
        k.bx(-0.33, 0.33, -0.255, -0.25, z, z + 0.12, 'rust', ink=False)
        k.bx(-0.12, 0.12, -0.262, -0.255, z + 0.08, z + 0.1, 'steel', ink=False)
    for x in (-0.28, 0.28):
        k.cyl(x - 0.03, -0.15, 0.06, 0.06, 0.06, 0.06, 'tire', seg=6, rot=(0, 90, 0), ink=False)
        k.cyl(x - 0.03, 0.15, 0.06, 0.06, 0.06, 0.06, 'tire', seg=6, rot=(0, 90, 0), ink=False)
    k.col(-0.36, 0.36, -0.26, 0.26, 0.0, 1.05)
    k.finish('ToolChest', ao=ao)

    k.begin()   # tyre stack [1, 1]
    for i in range(4):
        k.cyl(0.03 * (i % 2), 0.0, i * 0.24, 0.42, 0.42, 0.23, 'tire', seg=10)
        k.cyl(0.03 * (i % 2), 0.0, i * 0.24 + 0.231, 0.22, 0.22, 0.004, 'steelD', seg=8, ink=False)
    k.col(-0.42, 0.42, -0.42, 0.42, 0.0, 0.95)
    k.finish('Tyres', ao=ao)

    k.begin()   # engine hoist [1, 1] (front -Y): A-frame legs, boom, chain and hook, an engine block hanging
    k.bx(-0.35, 0.35, -0.4, 0.4, 0.0, 0.08, 'red')
    k.cyl(0, 0.3, 0.08, 0.05, 0.05, 1.9, 'red', seg=6)
    k.beam((0, 0.3, 1.9), (0, -0.4, 2.1), 0.08, 'red')
    k.cyl(0, -0.4, 1.35, 0.01, 0.01, 0.7, 'steelD', seg=4, ink=False)
    k.bx(-0.2, 0.2, -0.6, -0.2, 0.95, 1.35, 'steel2')
    k.col(-0.35, 0.35, -0.42, 0.42, 0.0, 1.4)
    k.finish('Hoist', ao=ao)

    k.begin()   # parking bay paint [4, 8] (no collision): yellow side lines, hatched end, a number
    for x in (-1.9, 1.9):
        k.qz(x - 0.06, x + 0.06, -3.9, 3.9, 0.012, 1, 'amber')
    k.qz(-1.84, 1.84, 3.78, 3.9, 0.012, 1, 'amber')
    for i in range(5):
        x = -1.6 + i * 0.6
        k.poly([(x, 3.2, 0.016), (x + 0.22, 3.2, 0.016), (x + 0.52, 3.72, 0.016), (x + 0.3, 3.72, 0.016)], 'amber', (0, 0, 1))
    k.text('BAY 3', 0.0, 2.2, 0.02, 0.5, 'paint', face='up', font='display')
    k.finish('BayPaint', ao=False)

    k.begin()   # oil stain decal [2, 2]
    rnd = random.Random(81)
    k.disc(0.1, 0.0, 0.01, 0.7, 'asph2', n=9, rnd=rnd, jag=0.25)
    k.disc(-0.4, 0.35, 0.014, 0.3, 'asph2', n=7, rnd=rnd, jag=0.3)
    k.finish('Stain', ao=False)


# ================================================================ ammo depot
def build_depot(k, ao):
    # ammo rack [4, 1] along X: steel shelving (three shelves) packed with ammo crates and shell cases, open both sides
    for name, seed in (('AmmoRack_A', 91), ('AmmoRack_B', 92)):
        rnd = random.Random(seed)
        k.begin()
        for x in (-1.95, -0.65, 0.65, 1.95):
            for y in (-0.42, 0.42):
                k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 2.4, 'steel2')
        for z in (0.08, 0.86, 1.64):
            k.bx(-2.0, 2.0, -0.45, 0.45, z, z + 0.05, 'amber' if z < 0.1 else 'steel', ink=z < 0.1)
            k.bx(-2.0, 2.0, -0.47, -0.43, z + 0.05, z + 0.12, 'amber', ink=False)
            k.bx(-2.0, 2.0, 0.43, 0.47, z + 0.05, z + 0.12, 'amber', ink=False)
            x = -1.9
            while x < 1.8:
                w = rnd.choice((0.55, 0.7, 0.9))
                if x + w > 1.92:
                    w = 1.92 - x
                if w < 0.3:
                    break
                kind = rnd.random()
                h = 0.62 if z < 1.6 else rnd.uniform(0.45, 0.6)
                if kind < 0.65:
                    k.bx(x + 0.025, x + w - 0.025, -0.41, 0.41, z + 0.05, z + 0.05 + h, rnd.choice(('olive', 'oliveL', 'olive2')))
                else:   # an open shell box: brass cases with olive tips showing over the rim
                    k.bx(x + 0.03, x + w - 0.03, -0.4, 0.4, z + 0.05, z + 0.45, 'olive2')
                    n = int((w - 0.05) / 0.2)
                    for i in range(n):
                        cx = x + 0.13 + i * 0.2
                        k.cyl(cx, 0.0, z + 0.45, 0.07, 0.02, 0.16, 'oliveL', seg=5, ink=False)
                x += w
        k.bx(-2.0, 2.0, -0.45, 0.45, 2.4, 2.44, 'steel2')
        k.col(-2.0, 2.0, -0.47, 0.47, 0.0, 2.44)
        k.finish(name, ao=ao)

    k.begin()   # artillery shells on a pallet [1, 1]: brass cases in an open crate, olive tips showing
    k.bx(-0.45, 0.45, -0.45, 0.45, 0.0, 0.13, 'wood')
    k.bx(-0.42, 0.42, -0.42, 0.42, 0.13, 0.62, 'olive2')
    for i in range(3):
        for j in range(3):
            x, y = -0.27 + i * 0.27, -0.27 + j * 0.27
            k.cyl(x, y, 0.62, 0.1, 0.02, 0.24, 'olive', seg=5, ink=False)
    k.text('HE 155', 0.0, -0.424, 0.3, 0.12, 'paint', font='display')
    k.col(-0.45, 0.45, -0.45, 0.45, 0.0, 0.9)
    k.finish('Shells', ao=ao)

    k.begin()   # wall gun rack [2, 1] (front -Y, back to the wall): rifles in a steel rack, ammo boxes below
    k.bx(-0.95, 0.95, 0.2, 0.42, 0.0, 1.95, 'steel2')
    k.bx(-0.94, 0.94, -0.25, 0.19, 0.0, 0.55, 'olive2')
    k.bx(-0.94, 0.94, -0.27, 0.19, 0.55, 0.6, 'steel')
    for i in range(7):
        x = -0.78 + i * 0.26
        k.bx(x - 0.03, x + 0.03, -0.05, 0.19, 0.6, 1.62, 'gunmetal')
        k.bx(x - 0.045, x + 0.045, -0.1, 0.18, 0.62, 0.9, 'wood')
        k.bx(x - 0.02, x + 0.02, 0.0, 0.17, 1.62, 1.75, 'steelD', ink=False)
    k.bx(-0.94, 0.94, -0.08, 0.16, 1.5, 1.56, 'steel', ink=False)
    for x in (-0.6, 0.0, 0.6):
        k.bx(x - 0.24, x + 0.24, -0.255, -0.25, 0.15, 0.42, 'olive', ink=False)
    k.col(-0.95, 0.95, -0.27, 0.42, 0.0, 1.95)
    k.finish('GunRack', ao=ao)

    # armory cage fence (link runs along Blender Y): square tube frame, bars every 0.25 m, 2.4 m tall
    def fence(y0, y1, post):
        k.bx(-0.03, 0.03, y0, y1, 2.34, 2.4, 'steel2')
        k.bx(-0.025, 0.025, y0, y1, 0.08, 0.13, 'steel2', ink=False)
        k.bx(-0.02, 0.02, y0, y1, 1.2, 1.24, 'steel2', ink=False)
        n = max(1, int(round((y1 - y0) / 0.25)))
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            k.bx(-0.012, 0.012, y - 0.012, y + 0.012, 0.13, 2.34, 'steelD', ink=False)
        if post:
            k.bx(-0.04, 0.04, -0.04, 0.04, 0.0, 2.45, 'steel2')
    k.begin(); fence(-0.5, 0.5, True); k.col(-0.05, 0.05, -0.5, 0.5, 0.0, 2.4); k.finish('FenceFull', ao=ao)
    k.begin(); fence(-0.5, -0.04, False); k.col(-0.05, 0.05, -0.5, 0.0, 0.0, 2.4); k.finish('FenceHalf', ao=ao)
    k.begin()
    k.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 2.48, 'steel2')
    k.finish('FencePost', ao=ao)


# ================================================================ barracks
def build_barracks(k, ao):
    k.begin()   # double bunk [1, 2] along Y, head at +Y (against the wall), ladder at the foot
    for (x, y) in ((-0.43, -0.95), (0.43, -0.95), (-0.43, 0.95), (0.43, 0.95)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 1.85, 'olive2')
    for z in (0.3, 1.25):
        k.bx(-0.45, 0.45, -0.97, 0.97, z, z + 0.06, 'olive2')
        k.bx(-0.42, 0.42, -0.94, 0.94, z + 0.06, z + 0.2, 'linen')
        k.bx(-0.43, 0.43, -0.95, 0.5, z + 0.2, z + 0.25, 'blanket')
        k.bx(-0.3, 0.3, 0.6, 0.88, z + 0.2, z + 0.32, 'paint')
    for z in (0.5, 0.8, 1.05):
        k.bx(0.3, 0.42, -0.99, -0.95, z, z + 0.03, 'steel2', ink=False)
    k.col(-0.47, 0.47, -0.99, 0.99, 0.0, 1.85)
    k.finish('Bunk', ao=ao)
    k.begin()   # footlocker [1, 1] (front -Y)
    k.bx(-0.4, 0.4, -0.24, 0.24, 0.0, 0.45, 'olive')
    k.bx(-0.42, 0.42, -0.26, 0.26, 0.45, 0.5, 'olive2')
    k.bx(-0.06, 0.06, -0.265, -0.24, 0.3, 0.42, 'brass', ink=False)
    k.text('%d' % 17, 0.25, -0.243, 0.12, 0.1, 'paint', font='display')
    k.col(-0.42, 0.42, -0.26, 0.26, 0.0, 0.5)
    k.finish('Footlocker', ao=ao)
    k.begin()   # steel locker pair [1, 1] (front -Y)
    for x in (-0.23, 0.23):
        k.bx(x - 0.22, x + 0.22, -0.25, 0.25, 0.0, 1.95, 'olive')
        k.bx(x - 0.2, x + 0.2, -0.255, -0.25, 0.05, 1.9, 'olive2', ink=False)
        for z in (1.6, 1.68, 1.76):
            k.bx(x - 0.12, x + 0.12, -0.262, -0.255, z, z + 0.035, 'ink', ink=False)
        k.bx(x + 0.13, x + 0.16, -0.262, -0.255, 0.95, 1.1, 'steel', ink=False)
    k.col(-0.46, 0.46, -0.26, 0.26, 0.0, 1.95)
    k.finish('Locker', ao=ao)
    k.begin()   # mess table [3, 2] along X with two benches, mugs and trays
    k.bx(-1.4, 1.4, -0.42, 0.42, 0.72, 0.78, 'olive2')
    for x in (-1.2, 1.2):
        k.bx(x - 0.04, x + 0.04, -0.35, 0.35, 0.0, 0.72, 'steel2')
    for y in (-0.82, 0.82):
        k.bx(-1.4, 1.4, y - 0.15, y + 0.15, 0.42, 0.47, 'wood')
        for x in (-1.2, 1.2):
            k.bx(x - 0.03, x + 0.03, y - 0.12, y + 0.12, 0.0, 0.42, 'steel2', ink=False)
    for (x, y) in ((-0.9, -0.2), (-0.1, 0.2), (0.7, -0.2)):
        k.bx(x - 0.2, x + 0.2, y - 0.15, y + 0.15, 0.78, 0.8, 'steel', ink=False)
        k.cyl(x + 0.28, y, 0.78, 0.05, 0.05, 0.1, 'paint', seg=6, ink=False)
    k.col(-1.4, 1.4, -0.97, 0.97, 0.0, 0.78)
    k.finish('MessTable', ao=ao)


# ================================================================ command centre
def build_command(k, ao):
    # the tactical table [6, 4]: steel base, a sand-table relief of the massif and the valley, a river, markers,
    # a model helicopter, a glowing grid rim (glow companion)
    k.begin()
    rnd = random.Random(101)
    k.bx(-2.8, 2.8, -1.8, 1.8, 0.0, 0.85, 'steelD')
    k.bx(-2.9, 2.9, -1.9, 1.9, 0.85, 0.95, 'steel2')
    k.bx(-2.7, 2.7, -1.7, 1.7, 0.95, 1.0, 'map2')
    for s in (-1, 1):
        k.bx(-2.6, 2.6, s * 1.81 - 0.004, s * 1.81 + 0.004, 0.25, 0.7, 'gunmetal', ink=False)
    # the massif along the east edge, the opposite range along the west, the valley floor between
    for i in range(7):
        y = -1.45 + i * 0.48
        h = rnd.uniform(0.32, 0.55)
        zb = 1.002 + 0.005 * (i % 2)
        k.hullp([(1.2, y - 0.3, zb), (2.6, y - 0.3, zb), (1.2, y + 0.3, zb), (2.6, y + 0.3, zb), (2.0 + rnd.uniform(-0.2, 0.2), y, 1.0 + h)],
                lambda f: 'snow' if f.normal.z > 0.8 else ('map' if f.normal.z > 0.3 else 'rock'))
        h = rnd.uniform(0.18, 0.34)
        k.hullp([(-2.6, y - 0.28, zb), (-1.4, y - 0.28, zb), (-2.6, y + 0.28, zb), (-1.4, y + 0.28, zb), (-2.1 + rnd.uniform(-0.2, 0.2), y, 1.0 + h)],
                lambda f: 'map' if f.normal.z > 0.3 else 'rock')
    pts = [(-0.3, -1.7), (0.1, -0.9), (-0.25, 0.0), (0.2, 0.8), (-0.1, 1.7)]
    for (a, b) in zip(pts, pts[1:]):
        k.beam((a[0], a[1], 1.006), (b[0], b[1], 1.006), 0.12, 'mapW', ink=False)
    for (x, y, c) in ((1.0, -0.6, 'red'), (0.6, 0.9, 'red'), (-0.9, 0.3, 'mapW'), (-1.1, -1.0, 'mapW'), (0.3, -1.3, 'amber')):
        k.cyl(x, y, 1.0, 0.012, 0.012, 0.24, 'steelD', seg=4, ink=False)
        k.bx(x, x + 0.12, y - 0.005, y + 0.005, 1.14, 1.22, c, ink=False)
    k.bx(0.55, 0.95, -0.15, -0.05, 1.12, 1.2, 'olive')
    k.cyl(0.75, -0.1, 1.2, 0.01, 0.01, 0.04, 'steelD', seg=4, ink=False)
    k.bx(0.5, 1.0, -0.115, -0.085, 1.24, 1.245, 'steelD', ink=False)
    k.col(-2.9, 2.9, -1.9, 1.9, 0.0, 1.0)
    k.finish('Landmark_Table', ao=ao)
    k.begin()   # rim glow + the valley's grid lines
    for s in (-1, 1):
        y0, y1 = sorted((s * 1.902, s * 1.906))
        k.bx(-2.9, 2.9, y0, y1, 0.88, 0.92, 'screen', ink=False)
        x0, x1 = sorted((s * 2.902, s * 2.906))
        k.bx(x0, x1, -1.9, 1.9, 0.88, 0.92, 'screen', ink=False)
    for i in range(1, 6):
        x = -1.2 + i * 0.4
        k.bx(x - 0.008, x + 0.008, -1.7, 1.7, 1.003, 1.004, 'screen', ink=False)
    k.finish('Landmark_Table_Glow', ao=False)

    # operator console [2, 1]: a steel desk with screens back to back (operators on both sides)
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.4, 0.0, 0.74, 'steel2')
    k.bx(-0.98, 0.98, -0.45, 0.45, 0.74, 0.8, 'steelD')
    for s in (-1, 1):
        for x in (-0.48, 0.48):
            k.bxr(x, s * 0.08, 1.1, 0.78, 0.07, 0.5, 'gunmetal', rot=(s * -8, 0, 0))
        k.bx(-0.6, 0.6, s * 0.33 - 0.12, s * 0.33 + 0.12, 0.8, 0.83, 'steelD', ink=False)
        k.bx(-0.9, 0.9, s * 0.4 - 0.004, s * 0.4 + 0.004, 0.08, 0.7, 'steelD', ink=False)
    k.col(-0.98, 0.98, -0.45, 0.45, 0.0, 1.4)
    k.finish('Console', ao=ao)
    k.begin()
    for s in (-1, 1):
        for x in (-0.48, 0.48):
            k.bxr(x, s * 0.08 + s * 0.042, 1.1, 0.7, 0.004, 0.42, 'screen' if x < 0 else 'mapW', rot=(s * -8, 0, 0), ink=False)
    k.finish('Console_Glow', ao=False)

    # video wall [6, 1] against the wall (front -Y): steel frame, 3 x 2 screens (glow), a clock strip
    k.begin()
    k.bx(-2.95, 2.95, 0.05, 0.45, 0.0, 0.9, 'steel2')
    k.bx(-2.95, 2.95, 0.1, 0.4, 0.9, 4.2, 'steelD')
    k.bx(-2.95, 2.95, 0.05, 0.45, 4.2, 4.6, 'steel2')
    k.bx(-1.0, 1.0, 0.045, 0.05, 4.28, 4.52, 'ink', ink=False)
    k.text('OPS 24', 2.3, 0.04, 4.3, 0.2, 'amber', font='display')
    k.col(-2.95, 2.95, 0.05, 0.45, 0.0, 4.6)
    k.finish('VideoWall', ao=ao)
    k.begin()
    for i in range(3):
        for j in range(2):
            x0 = -2.85 + i * 1.92
            z0 = 1.0 + j * 1.6
            k.qy(x0 + 0.04, x0 + 1.84, z0, z0 + 1.52, 0.095, -1, ('screen', 'mapW', 'screenD', 'mapW', 'screen', 'screenD')[i * 2 + j])
    for (x, z) in ((-2.0, 1.6), (-1.4, 2.0), (0.2, 3.1), (1.6, 1.4), (2.0, 3.6)):
        k.qy(x - 0.08, x + 0.08, z - 0.08, z + 0.08, 0.09, -1, 'beacon')
    k.text('0742', 0.0, 0.044, 4.31, 0.18, 'beacon', font='display')
    k.finish('VideoWall_Glow', ao=False)

    k.begin()   # radio rack [1, 1] (front -Y)
    k.bx(-0.4, 0.4, -0.3, 0.3, 0.0, 1.8, 'steelD')
    for i in range(5):
        z = 0.2 + i * 0.32
        k.bx(-0.36, 0.36, -0.305, -0.3, z, z + 0.26, 'gunmetal', ink=False)
        for x in (-0.25, -0.1, 0.05):
            k.bx(x, x + 0.06, -0.312, -0.305, z + 0.1, z + 0.16, 'steel', ink=False)
    k.cyl(0.25, 0.1, 1.8, 0.012, 0.01, 0.9, 'steelD', seg=4, ink=False)
    k.col(-0.4, 0.4, -0.3, 0.3, 0.0, 1.8)
    k.finish('RadioRack', ao=ao)


# ================================================================ decks, stairs, terrace
def build_decks(k, ao):
    k.begin()   # mezzanine deck post (floor to the slab underside)
    k.bx(-0.16, 0.16, -0.16, 0.16, 0.0, 0.08, 'steelD')
    k.bx(-0.1, 0.1, -0.1, 0.1, 0.08, MEZZ - 0.3, 'steel2')
    k.col(-0.1, 0.1, -0.1, 0.1, 0.0, MEZZ - 0.3)
    k.finish('DeckPost', ao=ao)
    k.begin()   # steel stair [2, 6] rising toward +Y to the deck top (2.4 m), stringers, hand rails, treads
    Y = 3.0
    n = 24
    for i in range(n):
        y0 = -Y + i * 6.0 / n
        top = (i + 1) * MEZZ / n
        k.bx(-0.85, 0.85, y0 + 0.01, y0 + 0.24, top - 0.04, top, 'steel' if i % 2 else 'steel2', ink=False)
    for s in (-1, 1):
        x = s * 0.9
        k.hullp([(x - 0.05, -Y, 0.0), (x + 0.05, -Y, 0.0), (x - 0.05, Y, MEZZ - 0.3), (x + 0.05, Y, MEZZ - 0.3),
                 (x - 0.05, -Y, 0.25), (x + 0.05, -Y, 0.25), (x - 0.05, Y, MEZZ), (x + 0.05, Y, MEZZ)], 'olive2')
        k.beam((x, -Y + 0.05, 1.0), (x, Y - 0.05, MEZZ + 1.0), 0.05, 'amber')
        for j in range(4):
            y = -Y + 0.2 + j * (2 * Y - 0.4) / 3
            z = (y + Y) * MEZZ / (2 * Y)
            k.cyl(x, y, z + 0.12, 0.025, 0.025, 0.88, 'steel2', seg=5, ink=False)
        for j in range(3):
            ya, yb = -Y + j * 2.0, -Y + (j + 1) * 2.0
            k.col(x - 0.07, x + 0.07, ya, yb, 0.0, (yb + Y) * MEZZ / (2 * Y) + 1.05)
    steps(k, -0.84, 0.84, -Y, Y, 0.0, MEZZ, n // 2)   # walkable: 0.5 m treads (the nav cell), 0.2 m rise
    k.finish('Stair', ao=ao)


def build_terrace(k, ao):
    k.begin()   # spotting scope on a pedestal [1, 1], looking out toward -Y
    k.bx(-0.25, 0.25, -0.25, 0.25, 0.0, 0.12, 'conc2')
    k.cyl(0, 0, 0.12, 0.06, 0.05, 1.05, 'steel2', seg=6)
    k.bx(-0.12, 0.12, -0.1, 0.1, 1.15, 1.25, 'steelD')
    for x in (-0.085, 0.085):
        k.cyl(x, 0.15, 1.36, 0.055, 0.075, 0.62, 'olive', seg=8, rot=(90, 0, 0))
    k.bx(-0.12, 0.12, -0.12, 0.12, 1.28, 1.44, 'olive2')
    k.col(-0.25, 0.25, -0.25, 0.25, 0.0, 1.3)
    k.finish('Scope', ao=ao)
    k.begin()   # twin AA gun [3, 3] in a sandbag ring (barrels toward -Y)
    for a in range(10):
        if a in (4, 5):
            continue
        ang = math.radians(a * 36 + 90)
        dz = 0.008 * (a % 2)
        k.push(math.cos(ang) * 1.25, math.sin(ang) * 1.25, a * 36 + 180)
        sandbag_row(k, -0.36, 0.36, 0.0, dz, n=2, h=0.24, d=0.36)
        sandbag_row(k, -0.3, 0.3, 0.0, 0.25 + dz, n=1, h=0.21, d=0.32)
        k.pop()
    k.cyl(0, 0, 0, 0.55, 0.6, 0.35, 'olive2', seg=10)
    k.cyl(0, 0, 0.35, 0.45, 0.4, 0.4, 'olive', seg=10)
    k.bx(-0.55, 0.55, -0.3, 0.3, 0.75, 1.25, 'olive')
    for x in (-0.38, 0.38):
        k.cyl(x, -0.2, 1.05, 0.06, 0.05, 1.7, 'steelD', seg=6, rot=(80, 0, 0))
    k.bx(-0.06, 0.06, 0.2, 0.75, 0.76, 0.82, 'steelD', ink=False)
    k.bx(-0.3, 0.3, 0.31, 0.43, 0.77, 1.05, 'steelD')
    k.col(-0.62, 0.62, -0.62, 0.62, 0.0, 1.3)
    for a in range(10):
        if a in (4, 5):
            continue
        ang = math.radians(a * 36 + 90)
        cx, cy = math.cos(ang) * 1.25, math.sin(ang) * 1.25
        k.col(cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, 0.0, 0.46)
    k.finish('AAGun', ao=ao)
    k.begin()   # flagpole [1, 1] with a made-up emblem flag
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.25, 'conc')
    k.cyl(0, 0, 0.25, 0.06, 0.04, 8.0, 'steel', seg=6)
    k.sph(0, 0, 8.3, 0.09, 'brass', seg=(6, 4))
    k.bx(0.05, 2.1, -0.015, 0.015, 6.9, 8.1, 'flag')
    k.bx(0.06, 2.09, -0.02, 0.02, 7.38, 7.62, 'paint', ink=False)
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 2.0)
    k.finish('Flagpole', ao=ao)


def build_inner(k, ao):
    build_halls(k, ao)
    build_hangar(k, ao)
    build_depot(k, ao)
    build_barracks(k, ao)
    build_command(k, ao)
    build_decks(k, ao)
    build_terrace(k, ao)
