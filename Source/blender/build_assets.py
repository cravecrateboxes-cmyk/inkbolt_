"""INKBOLT procedural asset build (Blender as a Python module: `pip install bpy`).

    python3 build_assets.py                 # every family
    python3 build_assets.py --family bots   # one family: common | weapons | bots | kit-toytown
    python3 build_assets.py --no-ao         # skip the Cycles AO bake (faster)

Each family is one GLB in Source/assets/ (fps-common.glb, fps-weapons.glb, fps-bots.glb, fps-kit-toytown.glb):
  * one 64x64 palette texture per family (8x8 cells, nearest filtering); UVs point at palette cells
  * chunky bevels (bevel modifier, 2 segments) on silhouette shapes, sharp edges above 40 degrees
  * baked ink outline (brief 3.3): an inverted shell offset along even-thickness normals, reversed winding,
    mapped to the palette's HULL cell, joined into the same mesh -> one mesh, one material, one draw call.
    The shell's offset direction is exported as the custom attribute _HULL so the game can widen
    outlines with distance.
  * static kit props get a Cycles AO bake into the vertex colour, posterised to 2 steps
  * sockets are empties parented to their part (MUZZLE, MAG, EJECT, CORE, HIP0..3 ...)
  * the arms are one skinned mesh on a 22-bone rig with per-weapon actions (<WEAPON>_Idle, _Draw, ...)
Blender is Z-up; the exporter converts to glTF Y-up. Game forward (-Z) is Blender +Y for the viewmodel,
robots face game +Z (Blender -Y).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ib_lib  # noqa: E402
import fam_bots  # noqa: E402
import fam_common  # noqa: E402
import fam_kit_toytown  # noqa: E402
import fam_weapons  # noqa: E402

BUILDERS = {'common': fam_common.build_common, 'bots': fam_bots.build_bots,
            'kit-toytown': fam_kit_toytown.build_kit_toytown, 'weapons': fam_weapons.build_weapons}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--family', default='all', choices=['all'] + list(BUILDERS))
    ap.add_argument('--no-ao', action='store_true')
    a = ap.parse_args(argv)
    fams = list(BUILDERS) if a.family == 'all' else [a.family]
    for f in fams:
        ib_lib.fresh_scene()
        BUILDERS[f](not a.no_ao)


if __name__ == '__main__':
    main(sys.argv[1:])
