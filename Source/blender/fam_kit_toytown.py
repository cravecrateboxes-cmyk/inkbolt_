"""INKBOLT asset family: kit-toytown."""
import math
import os
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

ib_lib.PALETTES['kit-toytown'] = BASE + [('tangerine', '#FF8A3D'), ('bubblegum', '#FF7FB0'), ('purple', '#8A6CD8'), ('purple2', '#6A55B8'),
                           ('sky', '#5BC0EB'), ('sand', '#F6D57A'), ('coral', '#F26B5B'), ('trim', '#F4EEE2'),
                           ('window', '#8ED2FF'), ('door', '#3B3550'), ('crate2', '#C8642A'), ('lowwall', '#D8D2C4'),
                           ('lowtop', '#EAE5D8'), ('tank', '#F4EEE2'), ('pad', '#E6DCC6'), ('ground', '#F6D57A'),
                           ('canbody', '#8C93A0'), ('canlid', '#6E7480')]

# ================================================================ KIT: TOY TOWN
WALL_COLORS = ['tangerine', 'bubblegum', 'purple', 'sky', 'sand', 'coral']


def build_kit_toytown(ao):
    pal = Palette('kit-toytown')
    bw, ht = CFG['kit-toytown']
    # 1 m wall modules, 3 m tall, centred on the cell; windows/doors on both faces (+Y and -Y)
    for ci, c in enumerate(WALL_COLORS):
        for kind in ('Plain', 'Window', 'Door'):
            m = Model(pal)
            m.box((0, 0, 1.5), (1.0, 1.0, 3.0), c, bevel=False)
            m.box((0, 0, 3.08), (1.04, 1.04, 0.16), 'trim')
            for fy in (-1, 1):
                if kind == 'Window':
                    m.box((0, fy * 0.515, 1.9), (0.62, 0.05, 0.62), 'window', bevel=False)
                    m.box((0, fy * 0.53, 1.56), (0.72, 0.06, 0.07), 'trim', bevel=False)
                elif kind == 'Door':
                    m.box((0, fy * 0.515, 0.95), (0.7, 0.05, 1.9), 'door', bevel=False)
                    m.box((0.22, fy * 0.54, 0.95), (0.06, 0.04, 0.06), 'amber', bevel=False)
            build_object('KIT_TOYTOWN_Wall%s_%s' % (kind, c), m, 0, ht, ao=ao)
    # crate (1 m) and stacked crate top
    for name, c in (('Crate', 'tangerine'), ('CrateB', 'bubblegum')):
        m = Model(pal)
        m.box((0, 0, 0.5), (0.96, 0.96, 0.96), c)
        # straps: front/back and side straps differ in height and depth so no faces coincide
        for fy in (-1, 1):
            m.box((0, fy * 0.49, 0.5), (0.98, 0.04, 0.12), 'crate2', bevel=False)
            m.box((fy * 0.495, 0, 0.5), (0.04, 0.95, 0.13), 'crate2', bevel=False)
            m.beam((-0.38, fy * 0.497, 0.14), (0.38, fy * 0.497, 0.86), 0.06, 'crate2')
        build_object('KIT_TOYTOWN_' + name, m, bw, ht, ao=ao)
    # container 2 x 2 x 2.5 with ribs
    for c in ('teal', 'tangerine', 'bubblegum', 'sky'):
        m = Model(pal)
        m.box((0, 0, 1.25), (1.96, 1.96, 2.5), c)
        for k in range(4):
            o = -0.7 + k * 1.4 / 3
            for fy in (-1, 1):
                m.box((o, fy * 0.99, 1.25), (0.08, 0.06, 2.3), 'ink', bevel=False)
        m.box((0, 0, 2.52), (1.8, 1.8, 0.06), 'trim', bevel=False)
        build_object('KIT_TOYTOWN_Container_' + c, m, bw, ht, ao=ao)
    # low wall (1 m segment, 1 m tall) with alternating cap colour
    for name, cap in (('LowWall', 'teal'), ('LowWallB', 'ink')):
        m = Model(pal)
        m.box((0, 0, 0.45), (0.96, 0.8, 0.9), 'lowwall')
        m.box((0, 0, 0.95), (0.96, 0.9, 0.1), cap, bevel=False)
        build_object('KIT_TOYTOWN_' + name, m, bw, ht, ao=ao)
    # landmark: water tower on purple lattice legs (3 x 3 footprint)
    m = Model(pal)
    hw, legH = 1.3, 7.5
    legs = [(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]
    for (x, y) in legs:
        m.box((x, y, legH / 2), (0.28, 0.28, legH), 'purple')
    for i in range(4):
        a, b = legs[i], legs[(i + 1) % 4]
        for lv in range(2):
            z0 = 1.2 + lv * 3
            # the two diagonals sit 3 cm either side of the frame plane, like real lattice bracing
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ol = math.hypot(mx, my) or 1
            ox, oy = mx / ol * 0.035, my / ol * 0.035
            m.beam((a[0] + ox, a[1] + oy, z0), (b[0] + ox, b[1] + oy, z0 + 3), 0.12, 'purple')
            m.beam((b[0] - ox, b[1] - oy, z0), (a[0] - ox, a[1] - oy, z0 + 3), 0.12, 'purple')
            hz = z0 + 3 + (0.04 if i % 2 else 0.0)   # neighbouring ring beams at different heights
            m.beam((a[0], a[1], hz), (b[0], b[1], hz), 0.17, 'purple')
    m.box((0, 0, legH + 0.1), (3.2, 3.2, 0.2), 'purple2')
    r = hw + 0.5
    m.cyl((0, 0, legH + 0.2), r, r, 3.0, 'tank', seg=16)
    m.cyl((0, 0, legH + 1.2), r + 0.03, r + 0.03, 0.5, 'bubblegum', seg=16, bevel=False, caps=False)
    m.cyl((0, 0, legH + 3.2), r + 0.1, 0.3, 1.4, 'tangerine', seg=16)
    m.cyl((0, 0, legH + 4.6), 0.06, 0.06, 1.0, 'ink', seg=5, bevel=False)
    build_object('KIT_TOYTOWN_Landmark_WaterTower', m, 0.03, 0.03, ao=False)
    # billboards (decoration, facing -Y = game +Z toward the zone entry)
    for name, c in (('Billboard_A', 'bubblegum'), ('Billboard_B', 'tangerine'), ('Billboard_C', 'teal'), ('Billboard_D', 'purple')):
        m = Model(pal)
        for sx in (-1.2, 1.2):
            m.box((sx, 0, 2.2), (0.16, 0.16, 4.4), 'gunmetal')
        m.box((0, 0, 4.1), (3.6, 0.2, 1.6), 'paper')
        m.box((-0.6, -0.12, 4.1), (2.0, 0.04, 0.8), c, bevel=False)
        m.box((1.15, -0.12, 4.1), (0.7, 0.04, 0.7), 'ink', bevel=False)
        build_object('KIT_TOYTOWN_' + name, m, 0.02, ht)
    # gate frame (3 m opening) and roll-up shutter (theme main colour slats, teal/ink hazard band)
    m = Model(pal)
    for sx in (-1.75, 1.75):
        m.box((sx, 0, 1.8), (0.5, 0.7, 3.6), 'gunmetal')
    m.box((0, 0, 3.35), (4.08, 0.8, 0.6), 'gunmetal')   # header overhangs the posts by 4 cm
    for sx in (-1.2, 1.2):
        for fy in (-1, 1):
            m.box((sx, fy * 0.42, 3.35), (0.34, 0.06, 0.24), 'teal', bevel=False)
    build_object('KIT_TOYTOWN_GateFrame', m, bw, ht)
    m = Model(pal)
    H, slats = 3.05, 9
    for i in range(slats):
        z = 0.55 + i * (H - 0.55) / slats + (H - 0.55) / slats / 2
        m.box((0, 0, z), (3.0, 0.14, (H - 0.55) / slats - 0.05), 'tangerine' if i % 2 else 'coral', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.16, 0.5), 'ink' if k % 2 else 'teal', bevel=False)
    build_object('KIT_TOYTOWN_GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects['KIT_TOYTOWN_GateShutter']
    strip_hull(shutter)
    # one clean box outline for the shutter as a whole (slats would outline individually)
    m = Model(pal)
    m.box((0, 0, H / 2), (3.0, 0.16, H), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    # exit hatch pad
    m = Model(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'gunmetal', seg=20)
    m.cyl((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, bevel=False)
    build_object('KIT_TOYTOWN_Hatch', m, 0.015, ht)
    # trail wall (1 m segment, 2.6 m tall, theme secondary with accent posts)
    m = Model(pal)
    m.box((0, 0, 1.3), (0.5, 1.0, 2.6), 'bubblegum', bevel=False)
    m.box((0, 0, 2.68), (0.62, 1.02, 0.16), 'trim')
    m.box((0, 0, 1.3), (0.56, 0.2, 2.55), 'purple', bevel=False)
    build_object('KIT_TOYTOWN_TrailWall', m, 0, ht, ao=ao)
    # spawn can lives in fps-common; ammo/health pickups in fps-weapons
    export('kit-toytown')


