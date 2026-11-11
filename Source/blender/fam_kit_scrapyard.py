"""INKBOLT asset family: kit-scrapyard (Rustmoor Salvage: a massive scrapyard at night, among the remains of enormous
abandoned war machines).

Zone 1, the Stacks (sy_stacks.py): canyons of crushed-car bales and flattened car stacks between scrap mountains, the
baler line under the material-handling crane and its electromagnet, the weighbridge and its office, floodlight towers
casting pools of sodium light, wrecked giant limbs and broken giant guns lying as cover, piles of dead tech.
Zone 2, the Titan Graveyard (sy_titans.py): the kneeling dead titan, a fallen torso you walk through, an enormous
head with dead eye lenses, a ribcage frame with plating ramps up to two decks, a colossal broken cannon, dead reactor
cores faintly glowing, the salvage scaffold, the far backdrop.
Shared: scrap bank walls, the yard gate, the trail fence, the exit hoist, the weapon stand.
Conventions: sy_base.py.
"""
from sy_base import FAM, PFX, HULL_T, Palette, SK, PAL_NAMES, export
from kit_base import shutter_hull
import sy_stacks as S
import sy_titans as T

WALLS = (('Bank_A', 'A', 11), ('Bank_B', 'B', 23), ('Bank_C', 'C', 37), ('Bank_Tyres', 'Tyres', 41), ('Bank_Car', 'Car', 52),
         ('Bank_LampS', 'LampS', 61), ('Bank_LampN', 'LampN', 67), ('Bank_LampE', 'LampE', 63), ('Bank_LampW', 'LampW', 69),
         ('Bank_Sign1', 'Sign1', 81), ('Bank_Sign2', 'Sign2', 83),
         ('Grave_A', 'GA', 101), ('Grave_B', 'GB', 113), ('Grave_Plate', 'GPlate', 127), ('Grave_Finger', 'GFinger', 131),
         ('Grave_Tyres', 'GTyres', 137), ('Grave_LampS', 'GLampS', 161), ('Grave_LampN', 'GLampN', 167),
         ('Grave_LampE', 'GLampE', 163), ('Grave_LampW', 'GLampW', 169), ('Grave_Sign', 'GSign', 171), ('Grave_Leak', 'GLeak', 173))


def build_kit_scrapyard(ao):
    pal = Palette(FAM)
    print('palette cells:', ' '.join('%d=%s' % (i, n) for i, n in enumerate(PAL_NAMES)))
    k = SK(pal, PFX, HULL_T)
    # ---- walls
    for name, kind, seed in WALLS:
        S.bank_wall(k, kind, seed).finish(name, ao=ao)
    for name, seed, grave in (('Bank_Corner_A', 5, False), ('Bank_Corner_B', 17, False), ('Grave_Corner_A', 7, True), ('Grave_Corner_B', 19, True)):
        S.bank_corner(k, seed, grave).finish(name, ao=ao)
    # ---- shared: gate, trail, hatch, stand
    S.gate_frame(k).finish('GateFrame', ao=ao)
    shutter_hull(pal, S.gate_shutter(k).finish('GateShutter'))
    S.trail_wall(k, False, 1).finish('TrailWall', ao=ao)
    S.trail_wall(k, False, 2).finish('TrailWall_B', ao=ao)
    S.trail_wall(k, True, 3).finish('TrailWall_Lamp', ao=ao)
    S.hatch(k).finish('Hatch', ao=ao)
    S.stand(k).finish('Stand', ao=ao)
    # ---- zone 1: the Stacks
    for n in (1, 2, 3, 4):
        S.bales(k, n, 200 + n).finish('Bales_%d' % n, ao=ao)
    S.pancakes(k, 4, 211).finish('Pancakes_A', ao=ao)
    S.pancakes(k, 7, 213).finish('Pancakes_B', ao=ao)
    S.scrap_heap(k, 221).finish('Heap_A', ao=ao)
    S.scrap_heap(k, 227, R=4.5, H=5.4).finish('Heap_B', ao=ao)
    S.mound(k, 231).finish('Mound_A', ao=ao)
    S.mound(k, 233).finish('Mound_B', ao=ao)
    S.flood_tower(k).finish('FloodTower', ao=ao)
    S.weighbridge(k).finish('Weighbridge')
    S.office(k).finish('Landmark_Office', ao=ao)
    S.baler(k).finish('Landmark_Baler', ao=ao)
    S.crane(k).finish('Landmark_Crane', ao=ao)
    S.giant_hand(k, 3, 'bone').finish('Hand', ao=ao)
    S.giant_foot(k).finish('Foot', ao=ao)
    S.giant_leg(k).finish('Leg', ao=ao)
    S.giant_forearm(k).finish('Forearm', ao=ao)
    S.giant_rifle(k).finish('Rifle', ao=ao)
    S.giant_minigun(k).finish('Minigun', ao=ao)
    S.monitor_pile(k, 241).finish('Monitors_A', ao=ao)
    S.monitor_pile(k, 243).finish('Monitors_B', ao=ao)
    S.server_racks(k, 251).finish('Racks', ao=ao)
    S.cable_drum(k, False, 1).finish('CableDrum', ao=ao)
    S.cable_drum(k, True, 2).finish('Spool_A', ao=ao)
    S.cable_drum(k, True, 3).finish('Spool_B', ao=ao)
    S.ewaste(k, 261).finish('Ewaste', ao=ao)
    S.tyre_stack(k, 271).finish('Tyres', ao=ao)
    S.skip(k, 0).finish('Skip_A', ao=ao)
    S.skip(k, 1).finish('Skip_B', ao=ao)
    S.barrier(k, 0).finish('Barrier_A', ao=ao)
    S.barrier(k, 1).finish('Barrier_B', ao=ao)
    S.oil(k, 281).finish('Oil_A')
    S.oil(k, 283).finish('Oil_B')
    # ---- zone 2: the Titan Graveyard
    T.titan_lower(k).finish('Landmark_Titan', ao=ao)
    T.titan_upper(k).finish('Landmark_TitanUpper', ao=ao)
    T.torso(k).finish('Landmark_Torso', ao=ao)
    T.head(k).finish('Landmark_Head', ao=ao)
    T.ribs(k).finish('Landmark_Ribs', ao=ao)
    T.cannon(k).finish('Landmark_Cannon', ao=ao)
    T.reactor(k, False).finish('Reactor_A', ao=ao)
    T.reactor(k, True).finish('Reactor_B', ao=ao)
    T.scaffold(k).finish('Scaffold', ao=ao)
    T.arm(k).finish('Arm', ao=ao)
    T.plates(k, 1).finish('Plates_A', ao=ao)
    T.plates(k, 2).finish('Plates_B', ao=ao)
    T.beacon_post(k).finish('BeaconPost', ao=ao)
    # ---- the far backdrop
    T.bd_heap(k, 301).finish('Backdrop_Heap_A')
    T.bd_heap(k, 307).finish('Backdrop_Heap_B')
    T.bd_titan(k).finish('Backdrop_Titan')
    T.bd_crane(k).finish('Backdrop_Crane')
    print('glow companions:', ' '.join(k.glows))
    print('blink companions:', ' '.join(k.blinks))
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_scrapyard
