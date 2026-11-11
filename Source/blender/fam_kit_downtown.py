"""INKBOLT asset family: kit-downtown ("Downtown Standoff", campaign level 24): a wide daylight downtown braced for
a battle -- five building styles over walk-in shops, street furniture, battle staging and the vehicles the parking
kit does not have (taxi, police cruiser, city bus, an overturned truck, a stalled tram, fallen bikes).

The kit is split over downtown_base.py (palette, helpers), downtown_facades.py (facade modules, street surface, gate,
trail, hatch, backdrop), downtown_shops.py (ten furnished walk-in shop rooms) and downtown_props.py (vehicles, battle
staging, street furniture, market stalls, landmarks). Build: python3 build_assets.py --family kit-downtown
"""
import os

import ib_lib
import downtown_base as B
import downtown_facades as FA
import downtown_props as PR
import downtown_shops as SH


def build_kit_downtown(ao):
    pal = ib_lib.Palette(B.FAM)
    only = os.environ.get('DT_ONLY', '')   # iterate on one part: DT_ONLY=facades|shops|props
    if not only or only == 'facades':
        FA.build_facades(pal, ao)
        FA.build_floor(pal, ao)
        FA.build_gate(pal, ao)
        FA.build_trail(pal, ao)
        FA.build_hatch(pal, ao)
        FA.build_backdrop(pal, ao)
    if not only or only == 'shops':
        SH.build_shops(pal, ao)
    if not only or only == 'props':
        PR.build_props(pal, ao)
    T = B.TRIS
    print('kit-downtown: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:30]:
        print('  %-40s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-downtown'
BUILD = build_kit_downtown
