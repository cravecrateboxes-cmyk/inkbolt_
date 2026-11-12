"""INKBOLT asset family: kit-airfield7 ("Airfield 7", a made-up remote military air base on the arid steppe).

The kit is split over af_base.py (palette, helpers, conventions), af_struct.py (T-wall blast barriers, runway closure
barriers, gate, trail, hatch, the control tower, the revetment, the hardened aircraft shelter, the maintenance hangar,
the barracks block, the ordnance igloo, the engine test stand, the tool crib), af_craft.py (the fighter, the transport
with its ramp down, the fuel bowser, the crash tender, the runway caravan, the tug, the munitions trailer) and
af_props.py (runway / taxiway lights and signs, the windsock, ground equipment, workshop and ordnance props, scrub).
Build: python3 build_assets.py --family kit-airfield7
"""
import ib_lib
import af_base as B
import af_struct as S
import af_craft as C
import af_props as P


def build_kit_airfield7(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_struct(pal, ao)
    C.build_craft(pal, ao)
    P.build_props(pal, ao)
    T_ = B.TRIS
    print('kit-airfield7: %d pieces, %d triangles' % (len(T_), sum(T_.values())))
    for n in sorted(T_, key=lambda k: -T_[k]):
        print('  %-44s %6d' % (n, T_[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-airfield7'
BUILD = build_kit_airfield7
