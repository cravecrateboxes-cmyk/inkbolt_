"""INKBOLT asset family: kit-hotel ("The Aurelian": a grand hotel tower, from the street-level lobby to the sky
deck on the roof; campaign level 20).

The kit is split over hotel_base.py (palette, kit class, furniture helpers, conventions), hotel_struct.py (walls,
gate, service-stair trail, hatch, stand, grand stair, balustrades, columns, ceilings, floors), hotel_props.py
(lobby, ballroom floor, sky deck, penthouse and street props, landmarks) and hotel_rooms.py (the open suites).
Build: python3 build_assets.py --family kit-hotel
"""
import ib_lib
import hotel_base as B
import hotel_props as PR
import hotel_rooms as RM
import hotel_struct as S


def build_kit_hotel(ao):
    pal = ib_lib.Palette(B.FAM)
    k = B.HKit(pal)
    # walls
    S.win_half(k, 1).finish('Win_A', ao=ao)
    S.win_half(k, -1).finish('Win_B', ao=ao)
    S.win_half(k, 1, revolve=True).finish('Revolve_A', ao=ao)
    S.win_half(k, -1, revolve=True).finish('Revolve_B', ao=ao)
    S.win_pier(k).finish('Pier', ao=ao)
    S.core(k).finish('Core', ao=ao)
    for i, kind in enumerate(('Plain', 'Sconce', 'Art', 'Mirror')):
        S.inner_wall(k, kind, i).finish('Wall_' + kind, ao=ao)
    S.lift_half(k, 1).finish('Lift_A', ao=ao)
    S.lift_half(k, -1).finish('Lift_B', ao=ao)
    S.suite_window(k).finish('SuiteWin', ao=ao)
    for n in range(1, 7):
        S.suite_plaque(k, 2400 + n).finish('Plaque_%d' % n, ao=ao)
    for part in ('L', 'M', 'R'):
        S.doorway(k, part).finish('Door_' + part, ao=ao)
    S.sky_glass(k).finish('SkyGlass', ao=ao)
    S.sky_glass(k, fin=True).finish('SkyFin', ao=ao)
    # gate, trail, hatch, stand
    S.gate_frame(k).finish('GateFrame', ao=ao)
    shutter = S.gate_shutter(k).finish('GateShutter')
    m = ib_lib.Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.12, 3.05), 'HULL', bevel=False)
    tmp = ib_lib.build_object('tmp_shutter_hull', m, 0, 0.02)
    ib_lib.hull_only(tmp)
    ib_lib.join_into(shutter, tmp)
    for kind in ('', 'Pipe', 'Hose', 'Lift', 'F24', 'F56', 'FR'):
        S.trail_wall(k, kind).finish('TrailWall' + ('_' + kind if kind else ''), ao=ao)
    S.trail_end(k).finish('TrailEnd', ao=ao)
    S.hatch(k).finish('Hatch', ao=ao)
    S.stand(k).finish('Stand', ao=ao)
    # circulation
    S.grand_stair(k).finish('GrandStair', ao=ao)
    S.rails(k)
    S.columns(k)
    # ceilings and floors
    S.coffer(k).finish('Coffer')
    S.downlight(k).finish('Downlight')
    S.under_light(k).finish('UnderLight')
    S.chandelier(k, True).finish('Landmark_Chandelier')
    S.chandelier(k, False).finish('Chandelier')
    S.glass_roof(k).finish('GlassRoof')
    S.medallion(k).finish('Inlay_Medallion')
    S.band(k).finish('Inlay_Band')
    for kind in ('Lobby', 'Corridor', 'Pent'):
        S.carpet(k, kind).finish('Carpet_' + kind)
    S.runner(k).finish('Runner')
    S.parquet(k).finish('Parquet')
    S.deck(k).finish('Deck')
    # lobby
    PR.reception(k).finish('Landmark_Reception', ao=ao)
    PR.concierge(k).finish('Concierge', ao=ao)
    PR.bar(k).finish('Landmark_Bar', ao=ao)
    PR.stool(k).finish('Stool', ao=ao)
    PR.lounge(k, 'A').finish('Lounge_A', ao=ao)
    PR.lounge(k, 'B').finish('Lounge_B', ao=ao)
    PR.piano(k).finish('Piano', ao=ao)
    PR.flower_table(k).finish('Landmark_Flowers', ao=ao)
    PR.luggage_cart(k).finish('LuggageCart', ao=ao)
    PR.bell_stand(k).finish('BellStand', ao=ao)
    PR.palm_piece(k).finish('Palm', ao=ao)
    PR.topiary_piece(k).finish('Topiary', ao=ao)
    PR.ottoman(k).finish('Ottoman', ao=ao)
    PR.console(k).finish('Console', ao=ao)
    PR.writing_desk(k).finish('WritingDesk', ao=ao)
    # ballroom floor
    PR.banquet(k).finish('Banquet', ao=ao)
    PR.stage(k).finish('Landmark_Stage', ao=ao)
    PR.easel(k).finish('Easel', ao=ao)
    PR.hk_cart(k).finish('HKCart', ao=ao)
    PR.rs_trolley(k).finish('RSTrolley', ao=ao)
    for kind in ('King', 'Twin', 'Salon'):
        RM.suite(k, kind).finish('Suite_' + kind, ao=ao)
    # sky deck and penthouse
    PR.pool(k).finish('Landmark_Pool', ao=ao)
    PR.lounger(k).finish('Lounger', ao=ao)
    PR.umbrella(k).finish('Umbrella', ao=ao)
    PR.cabana(k).finish('Cabana', ao=ao)
    PR.sky_bar(k).finish('Landmark_SkyBar', ao=ao)
    PR.fire_table(k).finish('FireTable', ao=ao)
    PR.olive(k).finish('Olive', ao=ao)
    PR.hedge(k).finish('Hedge', ao=ao)
    PR.pent_living(k).finish('PentLiving', ao=ao)
    PR.pent_dining(k).finish('PentDining', ao=ao)
    PR.pent_bed(k).finish('PentBed', ao=ao)
    PR.telescope(k).finish('Telescope', ao=ao)
    PR.fireplace(k).finish('Fireplace', ao=ao)
    # the street outside the lobby (placed by the theme's backdrop)
    PR.street_canopy(k).finish('Street_Canopy')
    PR.street_taxi(k).finish('Street_Taxi')
    PR.street_lamp(k).finish('Street_Lamp')
    T = B.TRIS
    print('kit-hotel: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda q: -T[q])[:30]:
        print('  %-34s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-hotel'
BUILD = build_kit_hotel
