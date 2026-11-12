"""INKBOLT asset family: kit-riviera ("Grand Hotel Riviera", a made-up Belle Epoque grand hotel on a cliff over the
Mediterranean; campaign level 44).

The kit is split over rv_base.py (palette, kit class, helpers, conventions), rv_walls.py (the zone walls and
facades, gate, trail, hatch), rv_inside.py (zone 1: the imperial staircase, the restaurant, the conference hall, the
palm court) and rv_pool.py (zone 2: the infinity pool, the spa pool, the pool bar, loungers, the roof garden, boats
for the backdrop). The grand-hotel furniture (reception, bar, lounges, piano, suites, stage, gallery balustrades,
columns, chandeliers, coffers, carpets, lifts, cabanas) is The Aurelian's (kit-hotel), placed by the theme through
its option `families` and repainted in the Riviera blues (symbol option `paint`).
Build: python3 build_assets.py --family kit-riviera
"""
import ib_lib
import col_fit
import rv_base as B
import rv_walls as W
import rv_inside as I
import rv_pool as P


def build_kit_riviera(ao):
    pal = ib_lib.Palette(B.FAM)
    k = B.RKit(pal)
    # ---- zone 1 walls
    for i, kind in enumerate(('Plain', 'Sconce', 'Art', 'Mirror')):
        W.inner_wall(k, kind, i).finish('IW_' + kind, ao=ao)
        W.inner_wall(k, kind, i + 1, 0.006).finish('IW_' + kind + '_V', ao=ao)
    for kind in ('Plain', 'Sconce'):
        W.suite_front(k, kind).finish('SF_' + kind, ao=ao)
    W.core(k).finish('Core', ao=ao)
    for i, n in enumerate((2, 4, 6)):
        W.suite_door(k, n).finish('SuiteDoor_' + 'ABC'[i], ao=ao)
    W.service_door(k).finish('KitDoor', ao=ao)
    for part in ('L', 'M', 'R'):
        W.doorway(k, part).finish('Door_' + part, ao=ao)
    W.sea_win(k, 1).finish('SW_A', ao=ao)
    W.sea_win(k, -1).finish('SW_B', ao=ao)
    W.sea_pier(k).finish('SW_P', ao=ao)
    W.suite_win(k).finish('SuiteWin', ao=ao)
    # ---- gate, trail, hatch, stand
    W.gate_frame(k).finish('GateFrame', ao=ao)
    shutter = W.gate_shutter(k).finish('GateShutter')
    m = ib_lib.Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.12, 3.05), 'HULL', bevel=False)
    tmp = ib_lib.build_object('tmp_shutter_hull', m, 0, 0.02)
    ib_lib.hull_only(tmp)
    ib_lib.join_into(shutter, tmp)
    for kind in ('', 'Win', 'Lamp', 'Art', 'End'):
        W.trail_wall(k, kind).finish('TrailWall' + ('_' + kind if kind else ''), ao=ao)
    W.hatch(k).finish('Hatch', ao=ao)
    # ---- zone 2 facades, the podium, the cliff edge
    W.f_win(k).finish('F_Win', ao=ao)
    W.f_win(k, True).finish('F_Win2', ao=ao)
    W.f_shut(k, 1).finish('F_ShA', ao=ao)
    W.f_shut(k, -1).finish('F_ShB', ao=ao)
    W.f_shut(k, 1, True).finish('F_ShA2', ao=ao)
    W.f_shut(k, -1, True).finish('F_ShB2', ao=ao)
    W.f_door(k).finish('F_Door', ao=ao)
    W.f_plain(k).finish('F_Plain', ao=ao)
    W.f_plain(k, True, 3).finish('F_Bloom', ao=ao)
    W.f_plain(k, dz=0.012).finish('F_End', ao=ao)
    W.f_corner(k).finish('F_Corner', ao=ao)
    W.f_gate_top(k).finish('F_GateTop', ao=ao)
    W.p_win(k).finish('PW_Win', ao=ao)
    W.p_door(k, 'LES BAINS').finish('PW_Door', ao=ao)
    W.p_door(k, 'SPA AZUR').finish('PW_DoorB', ao=ao)
    W.p_plain(k).finish('PW_Plain', ao=ao)
    W.p_plain(k, True, 5).finish('PW_Bloom', ao=ao)
    W.p_gap(k).finish('PW_Gap', ao=ao)
    W.p_side(k).finish('PW_Side', ao=ao)
    W.p_corner(k).finish('PW_Corner', ao=ao)
    W.sea_bal(k).finish('SeaBal', ao=ao)
    W.sea_bal(k, True).finish('SeaBal_L', ao=ao)
    W.inf_edge(k).finish('InfEdge', ao=ao)
    # ---- zone 1: the imperial staircase
    I.imperial_stair(k).finish('Landmark_Stair', ao=ao)
    I.g_rails(k)
    I.lounge_set(k).finish('LoungeSet', ao=ao)
    I.lustre(k).finish('Lustre')
    I.palm_pot(k).finish('PalmPot', ao=ao)
    I.g_columns(k)
    I.dine_table(k).finish('DineTable', ao=ao)
    I.dine_two(k).finish('DineTwo', ao=ao)
    I.banquette(k).finish('Banquette', ao=ao)
    I.wine_wall(k).finish('WineWall', ao=ao)
    I.kitchen_pass(k).finish('KitchenPass', ao=ao)
    I.wine_trolley(k).finish('WineTrolley', ao=ao)
    I.cement_tiles(k).finish('CementTiles')
    # ---- the conference hall and its foyer
    I.chair_row(k).finish('ChairRow', ao=ao)
    I.lectern(k).finish('Lectern', ao=ao)
    I.stage_screen(k).finish('StageScreen', ao=ao)
    I.av_desk(k).finish('AVDesk', ao=ao)
    I.coffee_station(k).finish('CoffeeStation', ao=ao)
    I.high_table(k).finish('HighTable', ao=ao)
    I.reg_desk(k).finish('RegDesk', ao=ao)
    # ---- the palm court, the suites
    I.tea_set(k).finish('TeaSet', ao=ao)
    I.court_fountain(k).finish('CourtFountain', ao=ao)
    for end in ('S', 'M', 'N'):
        P.pool_seg(k, end).finish('Landmark_Pool_' + end, ao=ao)
    P.spa_pool(k).finish('SpaPool', ao=ao)
    P.sun_set(k).finish('SunSet', ao=ao)
    P.lounger(k).finish('Lounger', ao=ao)
    P.pool_bar(k).finish('PoolBar', ao=ao)
    P.towel_hut(k).finish('TowelHut', ao=ao)
    P.shower(k).finish('Shower', ao=ao)
    P.canary_palm(k).finish('CanaryPalm', ao=ao)
    P.planter(k).finish('Planter', ao=ao)
    P.olive_tree(k).finish('OliveTree', ao=ao)
    P.pergola(k).finish('Pergola', ao=ao)
    P.belvedere(k).finish('Belvedere', ao=ao)
    P.daybed(k).finish('Daybed', ao=ao)
    P.roof_stair(k).finish('RoofStair', ao=ao)
    P.roof_tile(k).finish('RoofTile')
    P.lawn(k).finish('Lawn')
    P.terrace_tile(k).finish('TerraceTile')
    P.yacht(k).finish('Backdrop_Yacht')
    P.sailboat(k).finish('Backdrop_Sail')
    T_ = B.TRIS
    print('kit-riviera: %d pieces, %d triangles' % (len(T_), sum(T_.values())))
    for n in sorted(T_, key=lambda q: -T_[q]):
        print('  %-40s %6d' % (n, T_[n]))
    ib_lib.export(B.FAM)


# pieces whose box collision is re-cut to the drawn shape on export
col_fit.FIT['kit-riviera'] = []

FAMILY = 'kit-riviera'
BUILD = build_kit_riviera
