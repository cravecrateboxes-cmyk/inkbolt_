"""INKBOLT asset family: kit-observatory ("Vesper Peak Observatory", the last campaign map: a mountaintop observatory at
late dusk -- the summit compound with its dish antennas, radio masts, the 1931 Halden Dome and the funicular station;
inside the Great Dome the Vesper 12 m telescope, the catwalk ring, the labs, the control room and the glass viewing
rooms over the sea of clouds).

The kit is split over ob_base.py (palette, helpers, conventions), ob_struct.py (wall faces and art, glazing, doorways,
gate, trail, hatch, stand, parapets, fences, rails, stairs, posts, ceilings, floor finishes), ob_summit.py (zone 1
props) and ob_dome.py (zone 2: the dome, the telescope, the ring, the interiors).
Build: python3 build_assets.py --family kit-observatory
"""
from ib_lib import Palette, export
import ob_base as B
import ob_struct as S
import ob_summit as SU
import ob_dome as D
import col_fit
from ob_detail import DKit

# pieces whose single collision boxes the fit re-cuts to what they show (blender/col_fit.py)
col_fit.FIT[B.FAM] = ['Vsat_*', 'Snowcat', 'Cylinders', 'Drum', 'Cairn', 'Outcrop', 'Rock_*', 'Spectro_*', 'OpticTable',
                      'Console', 'OpsDesk', 'PlateTable', 'Reception', 'Coater', 'MirrorCart', 'Lift', 'Sofa', 'LowTable',
                      'Plant', 'Viewer', 'SkyCam', 'VisitorScope', 'WeatherMast', 'GenHouse', 'FuelTank', 'Panorama']


def build_kit_observatory(ao):
    pal = Palette(B.FAM)
    k = DKit(pal, B.PFX, B.HULL_T)
    S.build_faces(k, ao)
    S.build_art(k, ao)
    S.build_doors(k, ao)
    S.build_gate(k, ao)
    S.build_runs(k, ao)
    S.build_stairs(k, ao)
    S.build_ceilings(k, ao)
    SU.build_summit(k, ao)
    D.build_dome_kit(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-observatory'
BUILD = build_kit_observatory
