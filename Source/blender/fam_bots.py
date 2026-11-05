"""INKBOLT asset family: bots."""
import math
import os
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

ib_lib.PALETTES['bots'] = BASE + [('tin', '#C9CFD6'), ('tin2', '#A9B0BA'), ('rust', '#D9663B'), ('spring', '#8C93A0'),
                    ('core', '#FFC23A'), ('light', '#FFFFFF')]

# ================================================================ BOTS
def build_bots(ao):
    pal = Palette('bots')
    bw, ht = CFG['bots']
    # Crawler: dented tin can on 4 spring legs; one sensor slot, antenna light, gold core dome (weak point)
    m = Model(pal)
    m.cyl((0, 0, 0.30), 0.32, 0.31, 0.42, 'tin', seg=10)
    m.cyl((0, 0, 0.42), 0.335, 0.335, 0.12, 'rust', seg=10, bevel=False, caps=False)
    m.cyl((0, 0, 0.72), 0.35, 0.35, 0.05, 'tin2', seg=10)
    m.box((0, -0.31, 0.60), (0.34, 0.07, 0.07), 'ink', bevel=False)          # sensor slot (front = -Y)
    m.box((0, -0.349, 0.60), (0.22, 0.02, 0.03), 'amber', bevel=False)
    m.sphere((0, 0, 0.77), 0.14, 'core', seg=(8, 4), scale=(1, 1, 0.6))
    m.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=3, bevel=False)
    body = build_object('BOT_CRAWLER_Body', m, bw, ht)
    socket('BOT_CRAWLER_CORE', body, (0, 0, 0.82))
    for i, (x, y) in enumerate([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]):
        socket('BOT_CRAWLER_HIP%d' % i, body, (x, y, 0.33))
    m = Model(pal)
    for i in range(3):
        m.box(((0.035 if i % 2 else -0.035), 0, -0.05 - i * 0.085), (0.13, 0.06, 0.04), 'spring', bevel=False)
    m.box((0, 0, -0.15), (0.03, 0.03, 0.3), 'gunmetal', bevel=False)
    m.cyl((0, 0, -0.355), 0.09, 0.07, 0.05, 'gunmetal', seg=5, bevel=False)
    build_object('BOT_CRAWLER_Leg', m, 0, 0.01)
    m = Model(pal)
    m.box((0, 0, 0), (0.09, 0.09, 0.09), 'light', bevel=False)
    build_object('BOT_CRAWLER_Light', m, 0, 0.008)
    export('bots')


