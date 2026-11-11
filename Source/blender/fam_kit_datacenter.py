"""INKBOLT asset family: kit-datacenter ("Helix Vault", a hyperscale data center and the HELIXA R&D wing).

The kit is split over dc_base.py (palette, helpers, conventions), dc_struct.py (walls in four finishes and their wall
art, corners, the breakable doors with their damage stages, glass and cage partitions, gate, corridor, hatch, ceiling
fittings, floor finishes), dc_hall.py (rack rows, cooling, fire suppression, power, NOC, meeting room, armory and
gear, small props, the quantum core) and dc_lab.py (holo tables and holograms, robot chassis gantries, weapon pods in
containment fields, cryo cylinders, lab benches, fabricator, cobot, parts shelf, test chamber, the Forge).
Build: python3 build_assets.py --family kit-datacenter
"""
import ib_lib
import dc_base as B
import dc_hall as HL
import dc_lab as LB
import dc_struct as S


def build_kit_datacenter(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    S.build_doors(pal, ao)
    S.build_partitions(pal, ao)
    S.build_gate(pal, ao)
    S.build_ceiling(pal, ao)
    S.build_floors(pal, ao)
    HL.build_racks(pal, ao)
    HL.build_plant(pal, ao)
    HL.build_rooms(pal, ao)
    HL.build_loot(pal, ao)
    HL.build_props(pal, ao)
    HL.build_quantum(pal, ao)
    LB.build_holo(pal, ao)
    LB.build_gantries(pal, ao)
    LB.build_pods(pal, ao)
    LB.build_cryo(pal, ao)
    LB.build_benches(pal, ao)
    LB.build_landmarks(pal, ao)
    T = B.TRIS
    print('kit-datacenter: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:24]:
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-datacenter'
BUILD = build_kit_datacenter
