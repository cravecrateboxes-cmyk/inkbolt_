"""INKBOLT asset family: kit-venetian ("Ca' Doranza", a made-up Venetian mansion compound: the campo before it and
its inner courtyard).

The kit is split over ven_base.py (palette, helpers, conventions), ven_facade.py (house fronts, the mansion's fronts,
corners, the quay balustrade, gate, gate facades, trail walls, hatch), ven_campo.py (zone 1: the Fountain of the Four
Winds, the walk-in cafes, the merchants' loggia, cafe furniture, stalls, the well-head, lamps, benches, paving) and
ven_court.py (zone 2: cloister columns and arches, balustrades, the grand staircase, service stairs, the garden
fountain, parterres, hedges, the roof loggia, garden pieces, the boat under repair, backdrop pieces).
Build: python3 build_assets.py --family kit-venetian
"""
import ib_lib
import col_fit
import ven_base as B
import ven_facade as F
import ven_walls as W
import ven_campo as C
import ven_campo2 as C2
import ven_court as K


def build_kit_venetian(ao):
    pal = ib_lib.Palette(B.FAM)
    F.build_houses(pal, ao)
    W.build_walls(pal, ao)
    C.build_cafe_a(pal, ao)
    C.build_cafe_b(pal, ao)
    C2.build_loggia(pal, ao)
    C2.build_fountain(pal, ao)
    C2.build_small(pal, ao)
    K.build_court(pal, ao)
    T_ = B.TRIS
    print('kit-venetian: %d pieces, %d triangles' % (len(T_), sum(T_.values())))
    for n in sorted(T_, key=lambda k: -T_[k]):
        print('  %-44s %6d' % (n, T_[n]))
    ib_lib.export(B.FAM)


# pieces whose box collision is re-cut to the drawn shape on export (round basins, the boat's tapering hull)
col_fit.FIT['kit-venetian'] = ['Landmark_Fountain', 'Fountain2', 'Gondola', 'Well', 'LemonPot', 'Urn', 'Barrels', 'Cypress']

FAMILY = 'kit-venetian'
BUILD = build_kit_venetian
