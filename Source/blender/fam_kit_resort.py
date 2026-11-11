"""INKBOLT asset family: kit-resort ("Palmyra Cove Resort": a luxury tropical resort whose treehouse villas stand on
long, wide platforms in enormous palms; you climb up on broken limbs and fallen fronds leaning against the trunks).

The kit is split over rs_base.py (palette, helpers, conventions), rs_nature.py (palms, the giant treehouse palms,
the limb / frond ramps, hedges, shore rocks, ground cover, backdrop greenery) and rs_build.py (lobby pavilion, lagoon
pool with the swim-up bar, cabanas, loungers, torches, furniture, golf cart, plank decals, rails, rope bridges, deck
posts, villas, gate, hatch, overwater bungalows).
Build: python3 build_assets.py --family kit-resort
"""
from ib_lib import Palette, export
import rs_base as B
import rs_nature as N
import rs_build as K


def build_kit_resort(ao):
    pal = Palette(B.FAM)
    k = B.RKit(pal, B.PFX, B.HULL_T)
    N.build_nature(k, ao)
    K.build_built(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-resort'
BUILD = build_kit_resort
