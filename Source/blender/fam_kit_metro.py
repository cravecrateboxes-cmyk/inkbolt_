"""INKBOLT asset family: kit-metro ("Metro Central", an underground station: the vaulted ticket hall with its shops,
ticket office, fare gates and escalator well; the platform hall with an island and two side platforms, stopped
trains, footbridges, passages and the maintenance depot).

The kit is split over mt_base.py (palette, finish schemes, helpers, conventions), mt_struct.py (wall faces and wall
art, through pieces, sunk side faces, doorways, gate, trail, hatch, ceilings, vaults, the mosaic, stairs, the
escalator bank, rails, hanging screens, fascias), mt_hall.py (ticket hall, shop and ticket office furniture, the
departures board) and mt_plat.py (trains, track, platform furniture, the station clock, maintenance gear).
Build: python3 build_assets.py --family kit-metro
"""
from ib_lib import Palette, export
import mt_base as B
import mt_struct as S
import mt_hall as H
import mt_plat as PL


def build_kit_metro(ao):
    pal = Palette(B.FAM)
    k = B.MKit(pal, B.PFX, B.HULL_T)
    S.build_struct(k, ao)
    H.build_hall(k, ao)
    PL.build_plat(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-metro'
BUILD = build_kit_metro
