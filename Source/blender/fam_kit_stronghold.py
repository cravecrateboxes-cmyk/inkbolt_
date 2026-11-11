"""INKBOLT asset family: kit-stronghold ("Fort Highwatch": a remote military stronghold built and carved into the
side of a huge mountain, late afternoon turning to sunset). The kit is split over sh_base.py (palette, helpers,
conventions), sh_outer.py (the outer works on the cliff ledge, the gate, trail and hatch) and sh_inner.py (the carved
rock halls inside the mountain and the observation terrace). The vista (massif, valley, waterfalls, sky dressing) is
built in code by the theme's backdrop.
Build: python3 build_assets.py --family kit-stronghold
"""
from ib_lib import Palette, export
import sh_base as B
import sh_outer as O
import sh_inner as I


def build_kit_stronghold(ao):
    pal = Palette(B.FAM)
    k = B.SKit(pal, B.PFX, B.HULL_T)
    O.build_outer(k, ao)
    I.build_inner(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-stronghold'
BUILD = build_kit_stronghold
