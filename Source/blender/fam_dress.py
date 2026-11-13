"""INKBOLT asset family: dress (tactical look, plan Stage 9.3).

Small clutter placed by the game's dressing pass (src/game/dress.js) on top of every map: rubble, bricks, cans,
bottles, cardboard, paper, cable coils, pipe offcuts, broken pallets, leaves, stones, grass tufts, floor cable runs,
wall conduit, junction boxes, vents, extinguishers, sign plates. Every piece is under 300 triangles with its ink
shell (shell no thicker than 8 mm), has no collision boxes (nothing here is solid; the walk tests do not change),
and is named KIT_DRESS_<Piece> (KIT_ names pass through IB.themePiece unchanged).

Floor pieces stand on the origin (Blender Z up). Wall pieces have their back on the wall plane at Y = 0 and stand
out toward -Y (the game's +Z, the open side), with their base at Z = 0 (dress.js lifts them to their height).
"""
import math
import os
import random
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'dress'
ib_lib.GLB[FAM] = 'fps-dress.glb'
ib_lib.CFG[FAM] = (0.0, 0.008)
ib_lib.PALETTES[FAM] = BASE + [
    ('concrete', '#9C978E'), ('concrete2', '#86827B'), ('brick', '#A4573F'), ('brick2', '#8E4A36'),
    ('cardboard', '#B08A5A'), ('cardboard2', '#9A7448'), ('paperw', '#E8E2D4'), ('can', '#B9BEC6'), ('canred', '#C2402F'),
    ('bottle', '#3F7A55'), ('cable', '#24232A'), ('cableY', '#D9A62B'), ('pipe', '#8D9399'), ('pipeRust', '#8A5A3A'),
    ('palletwood', '#A88660'), ('palletwood2', '#8F7051'), ('leaf', '#8A6A2E'), ('leaf2', '#6F7A34'), ('stone', '#8B8780'),
    ('stone2', '#6F6B66'), ('grass', '#5E8A3A'), ('grass2', '#7A9A45'), ('steelbox', '#A3A8A9'), ('ventgrey', '#7D8286'),
    ('extred', '#C8352B'), ('extblack', '#2A282E'), ('signY', '#E8B92A'), ('signW', '#ECE8DE'), ('signG', '#2F8F5B'),
    ('rubber', '#2E2C30'), ('sandbag', '#B5A57E'), ('bucket', '#3E73B8'),
]

HULL = 0.008


def piece(name, m, hull=HULL):
    obj = build_object('KIT_DRESS_' + name, m, 0, hull)
    if hull <= 0:
        strip_hull(obj)
    return obj


def rock(m, loc, r, color, seed, squash=0.6):
    rnd = random.Random(seed)
    m.sphere(loc, r, color, seg=(6, 3), scale=(rnd.uniform(0.8, 1.2), rnd.uniform(0.8, 1.2), squash),
             rot=(rnd.uniform(-15, 15), rnd.uniform(-15, 15), rnd.uniform(0, 180)))


def build_dress(ao):
    pal = Palette(FAM)
    R = random.Random(4242)

    # ---- rubble: irregular concrete chunks
    for k, n in (('RubbleA', 6), ('RubbleB', 4)):
        m = Model(pal)
        for i in range(n):
            s = R.uniform(0.08, 0.2)
            m.box((R.uniform(-0.35, 0.35), R.uniform(-0.3, 0.3), s * 0.35 + i * 0.002), (s, s * R.uniform(0.6, 1.0), s * 0.6),
                  'concrete' if i % 2 else 'concrete2', rot=(R.uniform(-12, 12), R.uniform(-12, 12), R.uniform(0, 90)), bevel=False)
        piece(k, m)

    # ---- bricks
    m = Model(pal)
    m.box((0, 0, 0.033), (0.22, 0.1, 0.065), 'brick', rot=(0, 0, 18), bevel=False)
    piece('Brick', m)
    m = Model(pal)
    m.box((0, 0, 0.033), (0.22, 0.1, 0.065), 'brick', bevel=False)
    m.box((0.02, 0.11, 0.038), (0.22, 0.1, 0.066), 'brick2', rot=(0, 0, 8), bevel=False)
    m.box((0.01, 0.05, 0.1), (0.22, 0.1, 0.065), 'brick', rot=(0, 0, -12), bevel=False)
    m.box((0.2, -0.08, 0.029), (0.11, 0.1, 0.058), 'brick2', rot=(0, 0, 40), bevel=False)
    piece('BrickPile', m)

    # ---- cans, bottle
    m = Model(pal)
    m.cyl((0, 0, 0), 0.033, 0.033, 0.12, 'can', seg=8, bevel=False)
    m.cyl((0, 0, 0.04), 0.0365, 0.0365, 0.05, 'canred', seg=8, bevel=False, caps=False)
    piece('Can', m)
    m = Model(pal)
    m.cyl((-0.06, 0, 0.033), 0.033, 0.033, 0.12, 'can', seg=8, rot=(0, 90, 20), bevel=False)
    piece('CanLying', m)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.035, 0.035, 0.17, 'bottle', seg=8, bevel=False)
    m.cyl((0, 0, 0.166), 0.035, 0.013, 0.064, 'bottle', seg=8, bevel=False)
    m.cyl((0, 0, 0.226), 0.0125, 0.0125, 0.044, 'bottle', seg=6, bevel=False)
    piece('Bottle', m)

    # ---- cardboard, paper
    m = Model(pal)
    m.box((0, 0, 0.15), (0.42, 0.32, 0.3), 'cardboard', rot=(0, 0, 12), bevel=False)
    m.box((0, 0, 0.3045), (0.43, 0.06, 0.003), 'cardboard2', rot=(0, 0, 12), bevel=False)
    piece('Carton', m)
    m = Model(pal)
    m.box((0, 0, 0.006), (0.7, 0.45, 0.012), 'cardboard', rot=(0, 0, -20), bevel=False)
    m.box((0.12, 0.05, 0.0195), (0.32, 0.4, 0.008), 'cardboard2', rot=(0, 0, 5), bevel=False)
    piece('CartonFlat', m)
    m = Model(pal)
    for i in range(5):
        m.box((R.uniform(-0.01, 0.01), R.uniform(-0.01, 0.01), 0.012 + i * 0.026), (0.3, 0.22, 0.022), 'paperw' if i % 2 else 'signW',
              rot=(0, 0, R.uniform(-8, 8)), bevel=False)
    piece('PaperStack', m)

    # ---- cable coil: a ring of short beams; pipe offcut
    m = Model(pal)
    for ring, (rr, z) in enumerate(((0.2, 0.02), (0.17, 0.05))):
        n = 6
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            m.beam((math.cos(a0) * rr, math.sin(a0) * rr, z), (math.cos(a1) * rr, math.sin(a1) * rr, z + 0.004), 0.035,
                   'cable' if ring == 0 else 'cableY')
    piece('CableCoil', m)
    m = Model(pal)
    m.cyl((-0.4, 0, 0.06), 0.06, 0.06, 0.8, 'pipeRust', seg=8, rot=(0, 90, 0), bevel=False)
    m.cyl((-0.2, 0.18, 0.04), 0.04, 0.04, 0.5, 'pipe', seg=7, rot=(0, 90, 25), bevel=False)
    piece('PipeOffcut', m)

    # ---- broken pallet, laid flat
    m = Model(pal)
    for i in range(5):
        if i == 3:
            continue
        m.box((-0.4 + i * 0.2, 0, 0.11), (0.14, 1.0 - (0.3 if i == 4 else 0), 0.022), 'palletwood', rot=(0, 0, 2 if i == 4 else 0), bevel=False)
    for y in (-0.42, 0, 0.42):
        m.box((0, y, 0.048), (1.0, 0.09, 0.094), 'palletwood2', bevel=False)
    piece('PalletBroken', m)

    # ---- leaves, stones, grass
    m = Model(pal)
    for i in range(6):
        rock(m, (R.uniform(-0.3, 0.3), R.uniform(-0.3, 0.3), 0.0), R.uniform(0.07, 0.14), 'leaf' if i % 2 else 'leaf2', 100 + i, squash=0.3)
    piece('LeafPile', m)
    for k, n in (('StonesA', 3), ('StonesB', 5)):
        m = Model(pal)
        for i in range(n):
            rock(m, (R.uniform(-0.25, 0.25), R.uniform(-0.25, 0.25), 0.02), R.uniform(0.05, 0.12), 'stone' if i % 2 else 'stone2', 200 + i + n * 10)
        piece(k, m)
    for k, n in (('GrassTuft', 7), ('GrassTuft2', 9)):
        m = Model(pal)
        bm = m.bm
        for i in range(n):
            a = R.uniform(0, 2 * math.pi)
            h = R.uniform(0.18, 0.32)
            bx, by = R.uniform(-0.08, 0.08), R.uniform(-0.08, 0.08)
            lean = R.uniform(0.04, 0.1)
            w = 0.025
            v = [bm.verts.new((bx - math.sin(a) * w, by + math.cos(a) * w, 0)), bm.verts.new((bx + math.sin(a) * w, by - math.cos(a) * w, 0)),
                 bm.verts.new((bx + math.cos(a) * lean, by + math.sin(a) * lean, h))]
            for vv in v:
                vv.co.z += i * 0.0003
            f = bm.faces.new(v)
            f.material_index = pal.index('grass' if i % 2 else 'grass2')
            f2 = bm.faces.new(list(reversed([bm.verts.new(vv.co + Vector((0, 0, 0.0001))) for vv in v])))
            f2.material_index = f.material_index
        piece(k, m, hull=0)

    # ---- small litter: scraps of paper and a wrapper (flat, no shell)
    m = Model(pal)
    for i in range(5):
        m.box((R.uniform(-0.3, 0.3), R.uniform(-0.3, 0.3), 0.003 + i * 0.004), (R.uniform(0.06, 0.14), R.uniform(0.05, 0.1), 0.004),
              'paperw' if i % 2 else 'canred', rot=(0, 0, R.uniform(0, 180)), bevel=False)
    piece('Litter', m, hull=0)

    # ---- floor cable run (1 m along X), clips every 0.5 m
    m = Model(pal)
    m.box((0, 0.03, 0.012), (1.0, 0.024, 0.024), 'cable', bevel=False)
    m.box((0, -0.03, 0.01), (1.0, 0.02, 0.02), 'cableY', bevel=False)
    for x in (-0.25, 0.25):
        m.box((x, 0, 0.026), (0.04, 0.11, 0.008), 'steelbox', bevel=False)
    piece('CableRun', m)

    # ---- wall pieces (back on the wall plane Y = 0, standing out toward -Y)
    m = Model(pal)
    m.cyl((-0.5, -0.03, 0), 0.025, 0.025, 1.0, 'pipe', seg=8, rot=(0, 90, 0), bevel=False)
    for x in (-0.3, 0.3):
        m.box((x, -0.02, 0), (0.03, 0.04, 0.07), 'steelbox', bevel=False)
    piece('Conduit', m)
    m = Model(pal)
    m.box((0, -0.05, 0.15), (0.24, 0.1, 0.3), 'steelbox', bevel=False)
    m.box((0, -0.105, 0.15), (0.2, 0.004, 0.26), 'ventgrey', bevel=False)
    m.cyl((0, -0.03, -0.25), 0.025, 0.025, 0.25, 'pipe', seg=8, bevel=False)
    piece('JunctionBox', m)
    m = Model(pal)
    m.box((0, -0.02, 0.2), (0.4, 0.04, 0.4), 'ventgrey', bevel=False)
    for i in range(5):
        m.box((0, -0.042, 0.06 + i * 0.07), (0.34, 0.012, 0.03), 'extblack', rot=(30, 0, 0), bevel=False)
    piece('Vent', m)
    m = Model(pal)
    m.cyl((0, -0.1, 0.02), 0.075, 0.075, 0.45, 'extred', seg=10, bevel=False)
    m.cyl((0, -0.1, 0.466), 0.072, 0.03, 0.06, 'extred', seg=10, bevel=False)
    m.box((0, -0.1, 0.56), (0.03, 0.03, 0.06), 'extblack', bevel=False)
    m.box((0.05, -0.1, 0.57), (0.1, 0.02, 0.015), 'extblack', bevel=False)
    m.box((0, -0.01, 0.3), (0.12, 0.02, 0.4), 'extblack', bevel=False)
    piece('Extinguisher', m)
    for k, col, mark in (('SignWarn', 'signY', 'extblack'), ('SignExit', 'signG', 'signW'), ('SignPlate', 'signW', 'extblack')):
        m = Model(pal)
        m.box((0, -0.006, 0.15), (0.36, 0.012, 0.3) if k != 'SignExit' else (0.4, 0.012, 0.2), col, bevel=False)
        if k == 'SignWarn':
            m.box((0, -0.0145, 0.15), (0.05, 0.002, 0.14), mark, bevel=False)
        else:
            m.box((0, -0.0145, 0.15), (0.26 if k == 'SignExit' else 0.22, 0.002, 0.04), mark, bevel=False)
        piece(k, m)

    # ---- bigger floor props (still low, under 0.6 m)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.13, 0.16, 0.3, 'bucket', seg=10, bevel=False)
    m.cyl((0, 0, 0.3), 0.165, 0.165, 0.015, 'bucket', seg=10, bevel=False, caps=False)
    piece('Bucket', m)
    m = Model(pal)
    m.cyl((0, 0, 0.11), 0.32, 0.32, 0.22, 'rubber', seg=12, rot=(0, 0, 0), bevel=False)
    m.cyl((0, 0, 0.113), 0.17, 0.17, 0.214, 'extblack', seg=10, bevel=False, caps=True)
    piece('TyreOld', m)
    m = Model(pal)
    for i, (x, y, z, r) in enumerate(((-0.25, 0, 0.08, 4), (0.25, 0.02, 0.08, -3), (0, 0.01, 0.235, 6))):
        m.sphere((x, y, z), 0.3, 'sandbag', seg=(8, 4), scale=(1.0, 0.55, 0.27), rot=(0, 0, r))
    piece('Sandbags', m)

    export(FAM)


FAMILY = FAM
BUILD = build_dress
