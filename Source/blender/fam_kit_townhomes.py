"""INKBOLT asset family: kit-townhomes ("Larkspur Glen", campaign level 28): a gated town-house community at midday --
the stone-and-iron entrance with its gatehouse, boom barriers and keypad post, the entry boulevard with a planted
median, the clubhouse and its fenced pool deck, the mailbox kiosk, rows of two- and three-storey town houses in brick,
lap siding and stucco (walk-in houses with furnished ground floors, stairs and balcony perches), cul-de-sacs, rear
garage lanes, a playground, a park with a gazebo and a lot under construction.

Split over townhomes_base.py (palette, dimensions, helpers), townhomes_houses.py (the town houses), townhomes_rooms.py
(their furniture), townhomes_site.py (gate, clubhouse, pool, playground, park, construction lot) and
townhomes_street.py (street surface, fences, lamps, trees, small props, the zone gate, trail, hatch and backdrop).
The parked cars and wheelie bins are kit-parking pieces (theme option `families`).
Build: python3 build_assets.py --family kit-townhomes   (TH_ONLY=houses|rooms|site|street to iterate on one part)
"""
import os

import ib_lib
import townhomes_base as B


def build_kit_townhomes(ao):
    pal = ib_lib.Palette(B.FAM)
    only = os.environ.get('TH_ONLY', '')
    import townhomes_houses as HO
    if not only or only == 'houses':
        HO.build_houses(pal, ao)
    if not only or only == 'rooms':
        import townhomes_rooms as RO
        RO.build_rooms(pal, ao)
    if not only or only == 'site':
        import townhomes_site as SI
        SI.build_site(pal, ao)
    if not only or only == 'street':
        import townhomes_street as ST
        ST.build_street(pal, ao)
    T = B.TRIS
    print('kit-townhomes: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:40]:
        print('  %-40s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-townhomes'
BUILD = build_kit_townhomes
