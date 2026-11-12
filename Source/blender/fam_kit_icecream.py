"""INKBOLT asset family: kit-icecream ("Scoops & Cream", a huge ice cream shop and its creamery).

The kit is split over ic_base.py (palette, helpers, conventions), ic_struct.py (walls in two finishes and their wall
art: menu boards, the script logo run, shop windows, posters, the kids' mural, fire point / exit, kitchen notices, the
dock door; corners, the STAFF ONLY gate, the staff-corridor trail walls, the hatch, ceiling bays, floor tiles and
marks, columns), ic_parlour.py (the shop floor: dipping cabinets with 48 flavours, counters, the till, sundae /
waffle / shake stations, stools, the back bar, soft-serve machines, the cake freezer, queue belts, the giant cone
landmark, booths, bistro tables, sofas, the window bar, the kids' corner, small props, the vestibule, the terrace)
and ic_kitchen.py (the creamery: churns, tanks, blast freezers, the walk-in freezer, prep tables, sink, lockers,
pallets and cartons, the mezzanine stair and rails, balloons and the PARTY ROOM landmark).
Build: python3 build_assets.py --family kit-icecream
"""
import ib_lib
import ic_base as B
import ic_struct as S
import ic_parlour as P
import ic_kitchen as K


def build_kit_icecream(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    S.build_gate(pal, ao)
    S.build_ceiling(pal, ao)
    S.build_floors(pal, ao)
    S.build_columns(pal, ao)
    P.build_parlour(pal, ao)
    K.build_kitchen(pal, ao)
    T = B.TRIS
    print('kit-icecream: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k]):
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-icecream'
BUILD = build_kit_icecream
