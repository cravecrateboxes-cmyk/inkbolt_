"""INKBOLT asset family: kit-megastore ("BULKBARN Warehouse Club", the inside of a huge warehouse store).

The kit is split over ms_base.py (palette, helpers, conventions), ms_struct.py (walls in two finishes and their wall
art: cooler doors, TV wall, dock doors with a trailer; corners, gate, back corridor, hatch, roof bays with open-web
joists, girders, lamps and skylights, hanging aisle / department signs, floor marks, columns), ms_racks.py (sales and
stockroom pallet racks, endcaps, floor pallets, bales), ms_dept.py (the sales floor: produce, freezer bunkers, TV and
tech tables, apparel, pharmacy / optical counter, checkout lanes, carts and corrals, the entrance vestibule, the food
court) and ms_back.py (the stockroom: pallet jack, baler, stretch wrapper, break room, mezzanine office, stairs, rails).
Build: python3 build_assets.py --family kit-megastore
"""
import ib_lib
import ms_base as B
import ms_struct as S
import ms_racks as R
import ms_dept as D
import ms_back as K


def build_kit_megastore(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    S.build_gate(pal, ao)
    S.build_roof(pal, ao)
    S.build_signs(pal, ao)
    S.build_floors(pal, ao)
    R.build_racks(pal, ao)
    R.build_endcaps(pal, ao)
    R.build_pallets(pal, ao)
    R.build_bales(pal, ao)
    D.build_dept(pal, ao)
    K.build_back(pal, ao)
    T = B.TRIS
    print('kit-megastore: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k]):
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-megastore'
BUILD = build_kit_megastore
