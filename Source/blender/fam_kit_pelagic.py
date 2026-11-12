"""INKBOLT asset family: kit-pelagic ("Pelagic Airbase", a made-up offshore military air platform far out at sea).

The kit is split over pel_base.py (palette, helpers, conventions), pel_struct.py (deck-edge railings and safety nets,
blast fences, the runway barricade, the flight-operations block front, gate, trail, hatch, deck posts, rails and
stairs, the island control tower, the second tower, the hangar shells), pel_craft.py (the light aircraft at the
spawn, the naval fighters, the helicopter, deck tractors, ordnance carts, the crash tender, the escort warships) and
pel_props.py (blast deflectors, arresting wires, deck gear, maintenance stands, cargo lifts, fuel tanks and lines,
containers, floodlights).
Build: python3 build_assets.py --family kit-pelagic
"""
import ib_lib
import pel_base as B
import pel_struct as S
import pel_craft as C
import pel_props as P


def build_kit_pelagic(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_struct(pal, ao)
    C.build_craft(pal, ao)
    P.build_props(pal, ao)
    T_ = B.TRIS
    print('kit-pelagic: %d pieces, %d triangles' % (len(T_), sum(T_.values())))
    for n in sorted(T_, key=lambda k: -T_[k]):
        print('  %-44s %6d' % (n, T_[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-pelagic'
BUILD = build_kit_pelagic
