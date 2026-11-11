"""INKBOLT asset family: kit-arctic ("Kolvane Station K-7", an abandoned polar research station buried under ice).

The kit is split over arc_base.py (palette, helpers, conventions), arc_struct.py (wall modules: firn strata, the buried
entry ramp, the station facade and its name board, station / mess interiors, glacier ice, the lab modules' shell, lab
interiors, generator-hall plating, corner posts), arc_doors.py (door frames, breaches, the breakable vault door, gate,
shaft trail, hatch, stairs, rails, ceiling tiles and the cave ceiling's ice, floor finishes), arc_surface.py (the
trench and the upper station: snowcat, fuel, sleds, masts, buried huts, the collapsed radar dome, mess, bunks, comms)
and arc_labs.py (the deep labs: core archive, cryo lab, generator hall, vault, the ice cavern and the frozen relic).
Build: python3 build_assets.py --family kit-arctic
"""
import ib_lib
import arc_base as B
import arc_struct as S
import arc_doors as D
import arc_surface as SU
import arc_labs as LB


def build_kit_arctic(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_walls(pal, ao)
    D.build_doors(pal, ao)
    D.build_gate(pal, ao)
    D.build_stairs(pal, ao)
    D.build_rails(pal, ao)
    D.build_ceiling(pal, ao)
    D.build_floors(pal, ao)
    SU.build(pal, ao)
    LB.build(pal, ao)
    T = B.TRIS
    print('kit-arctic: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:30]:
        print('  %-44s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-arctic'
BUILD = build_kit_arctic
