"""INKBOLT asset family: kit-parking ("Deep Park", a multi-level underground car park).

The kit is split over parking_base.py (palette, helpers, conventions), parking_struct.py (walls per level and storey,
columns, rails, ramps, stairs, gate), parking_cars.py (every vehicle) and parking_props.py (markings, ceiling
fittings, props, dock, car wash). Build: python3 build_assets.py --family kit-parking
"""
import ib_lib
import parking_base as B
import parking_cars as C
import parking_props as PR
import parking_struct as S


def build_kit_parking(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    S.build_columns(pal, ao)
    S.build_rails(pal, ao)
    S.build_circulation(pal, ao)
    S.build_gate(pal, ao)
    C.build_cars(pal, ao)
    C.build_wrecks(pal, ao)
    C.build_vans(pal, ao)
    C.build_trucks(pal, ao)
    C.build_small(pal, ao)
    PR.build_markings(pal, ao)
    PR.build_ceiling(pal, ao)
    PR.build_props(pal, ao)
    PR.build_dock(pal, ao)
    T = B.TRIS
    print('kit-parking: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:24]:
        print('  %-40s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-parking'
BUILD = build_kit_parking
