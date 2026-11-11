"""INKBOLT asset family: kit-frontier ("Cinder Ridge Outpost", the last campaign map): a remote frontier settlement in
a log stockade among mountains and endless forest, and the edge of the wild beyond its back gate.

The kit is split over fr_base.py (palette, helpers, conventions), fr_house.py (the generic house builder, the
walk-in interiors, cabins, the smithy and the stable), fr_town.py (palisade, gate, trail, hatch, watchtowers, the
water tower, the well, the street arch, corrals, wagons, small props, the supply depot's modern gear) and fr_wild.py
(trees, forest-edge and cliff walls, ravine banks, the rope bridge, the lookout, the sawmill and its water wheel, the
creek, the logging camp, the mine, the relay, the backdrop conifers).
Build: python3 build_assets.py --family kit-frontier
"""
from ib_lib import Palette, export
import fr_base as B
import fr_house as H
import fr_town as T
import fr_wild as W


def build_kit_frontier(ao):
    pal = Palette(B.FAM)
    k = B.FKit(pal, B.PFX, B.HULL_T)
    T.build_town(k, ao)
    H.build_houses(k, ao)
    W.build_wild(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-frontier'
BUILD = build_kit_frontier
