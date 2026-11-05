"""INKBOLT asset family: common."""
import math
import os
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

ib_lib.PALETTES['common'] = BASE + [('cloud', '#FFFDF7'), ('cloudshade', '#EDE6F2'), ('hill', '#93D08E'), ('hill2', '#A9DC9A'),
                      ('pine', '#4FA27B'), ('trunk', '#8A5A3B'), ('canbody', '#A0A7B3'), ('canlid', '#838995'),
                      ('canband', '#737986'), ('dull', '#E9DFC8')]

# ================================================================ COMMON
def build_common(ao):
    pal = Palette('common')
    bw, ht = CFG['common']
    # clouds: three puff shapes
    for name, puffs in (('Cloud_A', [(0, 0, 0, 2.2), (2.2, 0.2, -0.3, 1.6), (-2.1, 0, -0.4, 1.5)]),
                        ('Cloud_B', [(0, 0, 0, 1.8), (1.7, 0.3, -0.2, 1.3), (-1.5, -0.2, -0.3, 1.2)]),
                        ('Cloud_C', [(0, 0, 0, 2.6), (2.7, 0, -0.5, 1.7), (-2.5, 0.2, -0.4, 1.9)])):
        m = Model(pal)
        for (x, y, z, r) in puffs:
            m.sphere((x, y, z), r, 'cloud', seg=(8, 4), scale=(1, 1, 0.7))
        build_object(name, m, 0, 0.06)
    m = Model(pal)
    m.sphere((0, 0, 0), 16.0, 'hill', seg=(12, 6), scale=(1, 1, 0.55))
    build_object('Hill', m, 0, 0.15)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.18, 0.14, 0.9, 'trunk', seg=5, bevel=False)
    m.cyl((0, 0, 0.8), 1.3, 0.0, 2.2, 'pine', seg=7, bevel=False)
    m.cyl((0, 0, 2.2), 0.95, 0.0, 1.9, 'pine', seg=7, bevel=False)
    build_object('Tree', m, 0, 0.05)
    # trail arrow (painted chevron, flat, no outline)
    m = Model(pal)
    bm = m.bm
    for sgn in (1, -1):
        pts = [(0, 0.5), (sgn * 0.7, -0.2), (sgn * 0.7, -0.55), (0, 0.15)]
        vs = [bm.verts.new((x, y, 0.0)) for x, y in pts]
        f = bm.faces.new(vs if sgn < 0 else list(reversed(vs)))
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        f.material_index = pal.index('dull')
    obj = build_object('TrailArrow', m, 0, 0.0)
    strip_hull(obj)
    # spawn can (robots hop out of these)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.42, 0.48, 0.95, 'canbody', seg=10, bevel=False)
    for z in (0.18, 0.62):
        m.cyl((0, 0, z), 0.445 + z * 0.06, 0.455 + z * 0.06, 0.06, 'canband', seg=10, bevel=False, caps=False)
    m.cyl((0, 0, 0.95), 0.52, 0.5, 0.1, 'canlid', seg=10, bevel=False)
    m.box((0, 0, 1.08), (0.3, 0.08, 0.08), 'ink', bevel=False)
    build_object('SpawnCan', m, 0, ht, ao=ao)
    # ink chunk set (6 pieces): cans and bolts
    for i in range(6):
        m = Model(pal)
        if i < 3:
            m.cyl((0, 0, -0.08), 0.06 + i * 0.01, 0.06 + i * 0.01, 0.16, 'ink', seg=7, bevel=False)
        else:
            m.cyl((0, 0, -0.03), 0.05, 0.05, 0.03, 'ink', seg=6, bevel=False)
            m.cyl((0, 0, -0.08), 0.02, 0.02, 0.1, 'ink', seg=5, bevel=False)
        obj = build_object('InkChunk_%d' % i, m, 0, 0.0)
        strip_hull(obj)
    export('common')


FAMILY = 'common'
BUILD = build_common
