"""INKBOLT asset family: kit-gemmine (Glimmerdeep Colliery: a coal mine whose No. 3 Seam broke into a cavern of gems).

Zone 1 (gem_seam.py): the working coal seam -- timbered drifts, a wide haulage gallery under steel arch sets, mine-cart
rails with carts, the ore chute and its feed belt, the raised conveyor catwalk, the winch house, the ventilation fan and
its duct, lamp strings, cribs, coal heaps, and the first gem veins glinting in the coal faces.
Zone 2 (gem_cavern.py): the Glimmer Vault -- a vast natural cavern with giant faceted crystals (diamond, ruby, emerald,
sapphire) that glow (theme.glow), the Gem Heart landmark, the mining gallery at 4.8 m, platforms at 2.4 m, ledges with
ramps, the sorting / cutting station, the chasm edge with its railing and the far cliff (backdrop).
Shared: gate portal, shutter, drift trail, lift-cage hatch (the coal mine kit's helpers, repainted in this palette).
Conventions: gem_base.py.
"""
import random

from gem_base import (FAM, PFX, HULL_T, WALL_H, CAVE_H, GK, CM, Palette, export)
from kit_base import shutter_hull
import gem_seam as S
import gem_cavern as C


def gate_frame(k):
    """The coal mine portal (timber posts, cap, plank bulkhead to 9.4 m, level boards, lanterns) with a rock lintel
    above it up to the cavern roof (in zone 1 it stands above the ceiling, out of sight)."""
    CM.gate_frame(k)
    rnd = random.Random(8)
    fn = lambda f: 'cave3' if f.normal.z > 0.5 else ('cave' if abs(f.normal.y) > 0.5 else 'cave2')
    for (z0, z1) in ((WALL_H - 0.1, 14.2), (13.8, CAVE_H + 0.2)):
        pts = []
        for y in (-0.7, 0.7):
            for x in (-2.75, 2.75):
                for z in (z0, z1):
                    pts.append((x + rnd.uniform(-0.05, 0.05), y * rnd.uniform(0.95, 1.1), z))
        pts += [(0.0, -0.95, (z0 + z1) / 2), (0.0, 0.95, (z0 + z1) / 2 + 0.6)]
        k.hullp(pts, fn)
    return k


WALLS_1 = (('Rock_A', 'A', 11), ('Rock_B', 'B', 23), ('Rock_C', 'C', 37), ('Seam_A', 'Seam', 41), ('Seam_B', 'Seam', 52),
           ('Gem_Ruby', 'Gem_Ruby', 43), ('Gem_Emer', 'Gem_Emer', 46), ('Gem_Saph', 'Gem_Saph', 57), ('Gem_Dia', 'Gem_Dia', 58),
           ('Rock_LampS', 'LampS', 61), ('Rock_LampN', 'LampN', 67), ('Rock_LampE', 'LampE', 63), ('Rock_LampW', 'LampW', 69),
           ('Rock_Prop', 'Prop', 73), ('Sign_Seam', 'SignSeam', 79), ('Sign_Haul', 'SignHaul', 83), ('Sign_Gem', 'SignGem', 89))
WALLS_2 = (('Cave_A', 'A', 101), ('Cave_B', 'B', 113), ('Cave_C', 'C', 127), ('Cave_Ruby', 'Ruby', 131), ('Cave_Emer', 'Emer', 137),
           ('Cave_Saph', 'Saph', 139), ('Cave_Dia', 'Dia', 149),
           ('Cave_LampS', 'LampS', 161), ('Cave_LampN', 'LampN', 167), ('Cave_LampE', 'LampE', 163), ('Cave_LampW', 'LampW', 169))


def build_kit_gemmine(ao):
    pal = Palette(FAM)
    k = GK(pal, PFX, HULL_T)
    # ---- zone 1 walls, ceiling patches, fittings
    for name, kind, seed in WALLS_1:
        S.seam_wall(k, kind, seed).finish(name, ao=ao)
    for name, seed in (('Rock_Corner_A', 5), ('Rock_Corner_B', 17)):
        S.seam_corner(k, seed).finish(name, ao=ao)
    CM.ceil_rock(k).finish('CeilRock')
    S.vent_duct(k).finish('VentDuct')
    S.lamp_string(k, True).finish('LampString_A')
    S.lamp_string(k, False).finish('LampString_B')
    # ---- shared: gate, trail, hatch, stand
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = CM.gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    S.trail_wall(k).finish('TrailWall', ao=ao)
    CM.hatch(k).finish('Hatch', ao=ao)
    CM.stand(k).finish('Stand', ao=ao)
    # ---- zone 1 props
    for kind in ('Powder', 'Tools', 'Plain', 'Lid'):
        CM.crate(k, kind).finish('Crate_' + kind, ao=ao)
    for v in (0, 1):
        CM.coal_heap(k, v).finish('CoalHeap_%s' % 'AB'[v], ao=ao)
        CM.conveyor(k, v).finish('Conveyor_%s' % 'AB'[v], ao=ao)
        CM.puddle(k, v).finish('Puddle_%s' % 'AB'[v])
        CM.dust(k, v).finish('Dust_%s' % 'AB'[v])
    S.lantern_post(k).finish('LanternPost', ao=ao)
    CM.lantern_post(k, 'Work').finish('WorkLight', ao=ao)
    CM.timber_stack(k, 1).finish('Timbers', ao=ao)
    CM.drums(k, 0).finish('Drums', ao=ao)
    CM.sacks(k, 0).finish('Sacks', ao=ao)
    S.crib(k).finish('Crib', ao=ao)
    CM.roof_jack(k).finish('RoofJack', ao=ao)
    S.rail(k).finish('Rail')
    CM.ore_cart(k, 0).finish('OreCart_Full', ao=ao)
    CM.ore_cart(k, 1).finish('OreCart_Empty', ao=ao)
    S.gem_cart(k).finish('OreCart_Gem', ao=ao)
    for v in ('Plain', 'Lamp'):
        S.drift(k, v).finish('Drift_' + v, ao=ao)
    S.steel_arch(k).finish('Arch', ao=ao)
    S.steel_arch(k, lamp=True).finish('Arch_Lamp', ao=ao)
    S.chute(k).finish('Landmark_Chute', ao=ao)
    S.belt_bridge(k).finish('Landmark_BeltBridge', ao=ao)
    S.winch_house(k).finish('Landmark_Winch', ao=ao)
    S.fan_unit(k).finish('FanUnit', ao=ao)
    # ---- zone 2 walls, roof
    for name, kind, seed in WALLS_2:
        C.cave_wall(k, kind, seed).finish(name, ao=ao)
    for name, seed in (('Cave_Corner_A', 7), ('Cave_Corner_B', 19)):
        C.cave_corner(k, seed).finish(name, ao=ao)
    for name, v, seed in (('Chasm', '', 171), ('Chasm_B', '', 173), ('Chasm_Sign', 'Sign', 177), ('Chasm_Lamp', 'Lamp', 179)):
        C.chasm(k, v, seed).finish(name, ao=ao)
    for i, seed in enumerate((211, 223, 227)):
        C.cave_roof(k, seed).finish('CaveRoof_' + 'ABC'[i])
    # ---- zone 2 props and landmarks
    for i, g in enumerate(('Ruby', 'Emer', 'Saph', 'Dia')):
        C.crystal_cluster(k, g.lower() if g != 'Emer' else 'emer', 300 + i).finish('Crystal_' + g, ao=ao)
    for i in range(2):
        C.clump(k, 310 + i).finish('Clump_' + 'AB'[i], ao=ao)
    for i in range(2):
        C.spire(k, 320 + i).finish('Spire_' + 'AB'[i], ao=ao)
        C.stalagmite(k, 330 + i).finish('Stalagmite_' + 'AB'[i], ao=ao)
    C.gem_heart(k).finish('Landmark_GemHeart', ao=ao)
    C.gallery(k).finish('Landmark_Gallery', ao=ao)
    C.platform(k).finish('Platform', ao=ao)
    C.ledge(k).finish('Ledge', ao=ao)
    C.sieve(k).finish('Sieve', ao=ao)
    C.cut_bench(k).finish('CutBench', ao=ao)
    C.work_table(k, 0).finish('WorkTable_A', ao=ao)
    C.work_table(k, 1).finish('WorkTable_B', ao=ao)
    C.gem_crate(k, 0).finish('GemCrate_A', ao=ao)
    C.gem_crate(k, 1).finish('GemCrate_B', ao=ao)
    C.hoist(k).finish('Landmark_Hoist', ao=ao)
    C.planks(k, 0).finish('Planks_A')
    C.planks(k, 1).finish('Planks_B')
    C.backdrop_chasm(k).finish('Backdrop_Chasm')
    print('glow companions:', ' '.join(k.glows))
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_gemmine
