"""INKBOLT asset family: kit-toyfactory ("Topsy Toyworks", a bright toy factory and its warehouse).

The kit is split over tf_base.py (palette, helpers, conventions, the toy models), tf_struct.py (walls in two finishes
and their art: fire point, exit, panel, safety board, logo, banners, carton chute, dock doors; corners, gate, trail
walls, hatch, stand, roof bays, hanging boards, floor marks, columns), tf_lines.py (the production floor: belts and
rollers with the toys and cartons riding them, robot arms, benches, tote racks, moulding machines, the pellet loft,
paint booths, packaging machines, pack benches, andons, carts, the stuffing machine, QC benches, finished-goods
pallets, wrapper, pallet jack), tf_giants.py (the showpiece workshop's oversized toys: the ROBO-PAL MAX landmark, the
rocking horse, the spinning top, giant bricks, alphabet blocks, scaffold, paint pots) and tf_store.py (the warehouse:
tall racks, the mezzanine, the dispatch office landmark with the mascot bear, pack stations, chargers, the returns
cage, the showpiece crate).
Build: python3 build_assets.py --family kit-toyfactory
"""
import ib_lib
import tf_base as B
import tf_struct as S
import tf_lines as L
import tf_giants as G
import tf_store as W


def build_kit_toyfactory(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_struct(pal, ao)
    L.build_lines(pal, ao)
    G.build_giants(pal, ao)
    W.build_store(pal, ao)
    T = B.TRIS
    print('kit-toyfactory: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:40]:
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-toyfactory'
BUILD = build_kit_toyfactory
