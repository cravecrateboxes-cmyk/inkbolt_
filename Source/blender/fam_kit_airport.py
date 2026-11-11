"""INKBOLT asset family: kit-airport ("Meridian International", a made-up airport and the hangar of its MRO).

The kit is split over ap_base.py (palette, helpers, conventions), ap_struct.py (walls, gate, corridor, roofs, decks,
stairs, escalator, floor marks, columns), ap_term.py (check-in islands, kiosks, the departures board, the automated
security checkpoint, gate seating, duty free, the lounge, the cafe deck), ap_hangar.py (the airliner under
maintenance, work platforms, the engine stand, ground support vehicles, tool cribs) and ap_back.py (the parked
airliner and its jet bridge, distant aircraft, the control tower, apron masts).
Build: python3 build_assets.py --family kit-airport
"""
import ib_lib
import ap_base as B
import ap_struct as S
import ap_term as T
import ap_hangar as K
import ap_back as A


def build_kit_airport(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    S.build_hangar_walls(pal, ao)
    S.build_gate(pal, ao)
    S.build_roof(pal, ao)
    S.build_decks(pal, ao)
    S.build_floors(pal, ao)
    T.build_term(pal, ao)
    K.build_hangar(pal, ao)
    A.build_back(pal, ao)
    T_ = B.TRIS
    print('kit-airport: %d pieces, %d triangles' % (len(T_), sum(T_.values())))
    for n in sorted(T_, key=lambda k: -T_[k]):
        print('  %-44s %6d' % (n, T_[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-airport'
BUILD = build_kit_airport
