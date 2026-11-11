"""INKBOLT asset family: kit-seabase ("Abyssal Station Thalassa", an underwater research station on the deep seabed).

The kit is split over sb_base.py (palette, helpers, conventions), sb_struct.py (walls in three finishes and their wall
art, corners, the watertight bulkhead door, glass partitions and the lab door, rails, stair, deck columns, gate,
shutter, trail tube, exit hatch, ceiling tiles, floor marks), sb_dock.py (the docking and service level: the moon pool
landmark with the submersible in its cradle and the gantry, winches, umbilical spools, the ROV, dive lockers, tank
racks, suit racks, benches, pumps, manifolds, pressure and ballast tanks, compressors, battery racks, cabinets, flood
barriers, pipe runs, crates, carts, gas cylinders, the decompression chamber, the dock control cabin), sb_lab.py (the
research ring: the glass observation chambers bulging into the seabed, the hub's glass dome and survey table, sample
tanks, tank banks, lab benches, core racks, sonar desks, comms racks, workstations, chairs, sample fridges) and
sb_back.py (the deep-sea backdrop: rocks, rock spires, distant station pods on legs, pylons, cable spools).
Build: python3 build_assets.py --family kit-seabase
"""
import ib_lib
import sb_base as B
import sb_struct as S
import sb_dock as D
import sb_lab as L
import sb_back as K


def build_kit_seabase(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_struct(pal, ao)
    D.build_dock(pal, ao)
    L.build_lab(pal, ao)
    K.build_back(pal, ao)
    T = B.TRIS
    print('kit-seabase: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k]):
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-seabase'
BUILD = build_kit_seabase
