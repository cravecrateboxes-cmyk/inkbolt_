"""INKBOLT asset family: kit-academy ("Chalkstone Academy", a school: the main building with its classrooms, labs,
cafeteria and library mezzanine; the gymnasium and the courtyard).

The kit is split over ac_base.py (palette, helpers, conventions), ac_struct.py (wall faces and wall art, doorways,
the gate, trail walls, the hatch, ceiling tiles, roof bays, floor finishes, the court lines, stairs, rails),
ac_rooms.py (classroom, computer lab, art room, science labs, robotics lab, office, lounge, corridor, cafeteria and
library furniture) and ac_gym.py (bleachers, the stage, hoops, gym gear, the snack bar; the courtyard's big tree,
planters, picnic tables, bike racks, covered walkway, flagpole, lamps, tiers, street trees, backdrop trees).
Build: python3 build_assets.py --family kit-academy
"""
from ib_lib import Palette, export
import ac_base as B
import ac_struct as S
import ac_rooms as R
import ac_gym as G
import ac_detail as D


def build_kit_academy(ao):
    pal = Palette(B.FAM)
    k = B.AKit(pal, B.PFX, B.HULL_T)
    D.install(k)
    S.build_struct(k, ao)
    R.build_rooms(k, ao)
    G.build_gym_yard(k, ao)
    k.report(B.FAM)
    export(B.FAM)


FAMILY = 'kit-academy'
BUILD = build_kit_academy
