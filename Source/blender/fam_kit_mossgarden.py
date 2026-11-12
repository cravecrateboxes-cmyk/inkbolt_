"""INKBOLT asset family: kit-mossgarden ("Mosswood Gardens": a landscaped garden -- formal parterres round a tiered
fountain, a raised terrace with balustrades, a glasshouse, then a wild garden with a stream and stone bridges, a hedge
maze, a gazebo, a nursery yard and a ruined folly on a mound; a few huge trees).

The kit is split over mg_base.py (palette, helpers, conventions), mg_plants.py (giant trees, hedges, topiary, flower
beds, roses, ferns, lumenbell pods, rocks, logs, bank stones, backdrop trees) and mg_built.py (walls, gate, terrace,
fountains, pools, grotto, culvert, bridge, glasshouse, gazebo, folly, pergola, benches, lamps, urns, signs, the maze
arch, the potting shed and nursery props, hatch, backdrop manor).
Build: python3 build_assets.py --family kit-mossgarden
"""
from ib_lib import Palette, export
import mg_base as B
import mg_plants as N
import mg_built as K


def build_kit_mossgarden(ao):
    pal = Palette(B.FAM)
    k = B.MKit(pal, B.PFX, B.HULL_T)
    N.build_plants(k, ao)
    K.build_built(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-mossgarden'
BUILD = build_kit_mossgarden
