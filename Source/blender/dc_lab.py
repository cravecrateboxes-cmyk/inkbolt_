"""kit-datacenter R&D wing: holographic design tables with turning hologram companions (a mech, a rail rifle), robot chassis on assembly gantries (a biped mech, a quadruped walker), weapon prototype pods in containment
fields (breakable: the field is the leaf), cryo cylinders, lab benches, a fabricator, a cobot arm, a parts shelf, the
energy test chamber and the Forge (zone 3 landmark) (see dc_base.py for conventions)."""
import math
import random

from dc_base import *  # noqa: F401,F403
import dc_base as B


def wire_box(g, x0, x1, y0, y1, z0, z1, c='holo', t=0.016, fill='field'):
    """a hologram box (additive): faint faces and four glowing vertical edges"""
    for (x, y) in ((x0, y0), (x1, y1)):
        g.beam((x, y, z0), (x, y, z1), t, c)
    if fill:
        g.bx(x0 + 0.012, x1 - 0.012, y0 + 0.012, y1 - 0.012, z0 + 0.004, z1 - 0.004, fill, hull='none')


def wire_line(g, a, b, c='holo', t=0.016):
    g.beam(a, b, t, c)


# ================================================================ holo tables and holograms
def build_holo(pal, ao):
    for name, top in (('HoloTable', 'graph'), ('HoloTable_B', 'wallW')):
        m, g = new(pal), new(pal)
        m.cy((0, 0, 0.0), 0.55, 0.65, 0.12, 'graph', seg=10)
        m.cy((0, 0, 0.12), 0.32, 0.4, 0.7, 'graphL', seg=10)
        m.bx(-1.4, 1.4, -0.9, 0.9, 0.82, 0.95, top)
        m.bx(-1.43, 1.43, -0.93, 0.93, 0.8, 0.84, 'graphD', hull='none')
        m.cy((0, 0, 0.95), 0.62, 0.62, 0.02, 'black', seg=16, hull='none')
        for s in (-1, 1):
            m.bx(-1.1, 1.1, s * 0.92 - 0.04, s * 0.92 + 0.04, 0.95, 1.0, 'graph', hull='none')
            m.bxr(s * 1.05, -0.55, 1.08, 0.36, 0.02, 0.24, 'graphD', rot=(-55, 0, s * 15))
        # glow: projector ring, edge light, two floating UI panels
        ring(g, 0, 0, 0.975, 0.5, 0.6, 'cyan', seg=16)
        ring(g, 0, 0, 0.975, 0.2, 0.26, 'cyanL', seg=12)
        for s in (-1, 1):
            g.bx(-1.4, 1.4, s * 0.903 - (0.002 if s < 0 else 0), s * 0.903 + (0.002 if s > 0 else 0), 0.86, 0.9, 'cyan', hull='none')
            g.bxr(s * 1.05, -0.553, 1.09, 0.3, 0.004, 0.18, 'scrB', rot=(-55, 0, s * 15), hull='none')
        make(name, m, ao, cols=[cb(-1.43, -0.93, 0.0, 1.43, 0.93, 1.0)])
        make_glow(name + '_LED', g)
    # a mech in wireframe (z 1.05 - 2.45 over the table centre)
    g = new(pal)
    s = 0.42
    z = 1.05
    for sx in (-1, 1):
        wire_box(g, sx * 0.1 * s * 2 - 0.05, sx * 0.1 * s * 2 + 0.05, -0.06, 0.06, z, z + 0.35)
        wire_box(g, sx * 0.09 - 0.045, sx * 0.09 + 0.045, -0.05, 0.05, z + 0.35, z + 0.66)
        wire_box(g, sx * 0.28 - 0.04, sx * 0.28 + 0.04, -0.04, 0.04, z + 0.72, z + 1.08)
    wire_box(g, -0.16, 0.16, -0.1, 0.1, z + 0.62, z + 0.75)
    wire_box(g, -0.22, 0.22, -0.13, 0.13, z + 0.75, z + 1.15)
    wire_box(g, -0.08, 0.08, -0.09, 0.07, z + 1.18, z + 1.36)
    g.sp((0, -0.13, z + 0.95), 0.05, 'cyanL', seg=(6, 4), hull='none')
    for k in range(5):
        wire_line(g, (-0.45, -0.3, z + 0.1 + k * 0.3), (-0.3, -0.3, z + 0.1 + k * 0.3), 'cyanL', 0.01)
    ring(g, 0, 0, z, 0.35, 0.37, 'holo', seg=16)
    make_glow('Holo_Mech', g)
    # a rail rifle prototype, exploded view
    g = new(pal)
    z = 1.55
    wire_box(g, -0.55, 0.25, -0.05, 0.05, z - 0.06, z + 0.08)
    wire_box(g, 0.27, 0.75, -0.025, 0.025, z - 0.02, z + 0.03)
    for k in range(4):
        x = 0.32 + k * 0.12
        ring(g, x, 0.0, z + 0.005, 0.04, 0.055, 'cyanL', seg=8, normal=(1, 0, 0), axis='x')
    wire_box(g, -0.75, -0.57, -0.04, 0.04, z - 0.18, z + 0.04)
    wire_box(g, -0.3, -0.18, -0.03, 0.03, z - 0.32, z - 0.08)
    wire_box(g, -0.1, 0.12, -0.035, 0.035, z + 0.12, z + 0.22)
    for k in range(3):
        wire_line(g, (-0.1 + k * 0.1, 0.0, z + 0.08), (-0.1 + k * 0.1, 0.0, z + 0.12), 'cyanL', 0.008)
    ring(g, 0, 0, 1.05, 0.5, 0.52, 'holo', seg=16)
    make_glow('Holo_Gun', g)


# ================================================================ robot chassis on gantries [4, 4] (landmarks)
def cobot(m, x, y, deg, reach=1.0, lift=0.0, base=True):
    """a white six-axis arm on a pedestal at (x, y), reaching toward local +X"""
    m.push(x, y, deg)
    if base:
        m.cy((0, 0, 0.0), 0.22, 0.25, 0.5, 'graph', seg=8)
    m.cy((0, 0, 0.5), 0.16, 0.16, 0.18, 'mech', seg=8)
    m.cy((0, 0, 0.66), 0.17, 0.17, 0.04, 'teal', seg=8, hull='none')
    a = (0.0, 0.0, 0.75)
    b = (reach * 0.35, 0.0, 1.45 + lift)
    c = (reach * 0.9, 0.0, 1.25 + lift)
    m.beam(a, b, 0.17, 'mech')
    L = math.hypot(c[0] - b[0], c[2] - b[2])
    m.beam((b[0] + (c[0] - b[0]) * 0.06 / L, 0.0, b[2] + (c[2] - b[2]) * 0.06 / L), c, 0.13, 'mech')
    m.cy((b[0], -0.12, b[2]), 0.12, 0.12, 0.24, 'graph', seg=8, rot=(-90, 0, 0))
    m.cy((b[0], -0.126, b[2]), 0.132, 0.132, 0.03, 'teal', seg=8, rot=(-90, 0, 0), hull='none')
    m.beam((c[0] + 0.03, 0.0, c[2] - 0.024), (c[0] + 0.15, 0.0, c[2] - 0.12), 0.09, 'graphD')
    for s in (-1, 1):
        m.beam((c[0] + 0.15, s * 0.03, c[2] - 0.12), (c[0] + 0.28, s * 0.06, c[2] - 0.2), 0.03, 'steelL')
    m.pop()


def gantry(m, w=1.85, d=1.6, h=4.6):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * w, sy * d
            m.bx(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.0, h, 'graph')
            for k in range(2):
                m.bx(x - 0.133, x + 0.133, y - 0.133, y + 0.133, 0.15 + k * 0.3, 0.3 + k * 0.3, 'hazY', hull='none', cull='tb')
            m.bx(x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0.0, 0.06, 'steelD', hull='none', cull='b')
    for sy in (-1, 1):
        m.bx(-w - 0.1, w + 0.1, sy * d - 0.12, sy * d + 0.12, h - 0.3, h - 0.004, 'tealD')
    m.bx(-0.25, 0.25, -d - 0.12, d + 0.12, h - 0.42, h - 0.3, 'graphD')
    m.bx(-0.35, 0.35, -0.3, 0.3, h - 0.7, h - 0.42, 'hazY')
    # the painted bay on the floor
    for (x0, x1, y0, y1) in ((-w + 0.2, w - 0.2, -d + 0.15, -d + 0.25), (-w + 0.2, w - 0.2, d - 0.25, d - 0.15)):
        uq(m, x0, x1, y0, y1, 0.009, 'hazY')


def build_gantries(pal, ao):
    # biped mech chassis, half armoured, hanging from the hoist
    m, g = new(pal), new(pal)
    gantry(m)
    for sx in (-1, 1):
        x = sx * 0.3
        m.cy((x - 0.15, 0.0, 1.62), 0.13, 0.13, 0.3, 'graph', seg=10, rot=(0, 90, 0))
        m.bxr(x, 0.0, 1.22, 0.26, 0.32, 0.72, 'mech', rot=(sx * 3, 0, 0))
        m.bxr(x, -0.17, 1.25, 0.2, 0.04, 0.5, 'mechD', rot=(sx * 3, 0, 0))
        m.cy((x - 0.15, 0.0, 0.85), 0.11, 0.11, 0.3, 'graph', seg=10, rot=(0, 90, 0))
        m.bx(x - 0.11, x + 0.11, -0.12, 0.14, 0.32, 0.85, 'mechD')
        m.cy((x, 0.15, 0.4), 0.04, 0.04, 0.42, 'chrome', seg=6)
        m.bx(x - 0.18, x + 0.18, -0.32, 0.22, 0.17, 0.32, 'graph')
    m.bx(-0.38, 0.38, -0.2, 0.2, 1.5, 1.78, 'graphL')                       # pelvis
    m.bx(-0.09, 0.09, -0.09, 0.09, 1.78, 2.7, 'graphD')                     # spine
    for (x0, x1, y0, y1, z0, z1) in ((-0.36, 0.36, -0.26, -0.2, 2.0, 2.06), (-0.36, 0.36, -0.26, -0.2, 2.6, 2.66),
                                     (-0.42, -0.36, -0.26, 0.22, 2.0, 2.66), (0.36, 0.42, -0.26, 0.22, 2.0, 2.66),
                                     (-0.36, 0.36, 0.16, 0.22, 2.0, 2.66)):
        m.bx(x0, x1, y0, y1, z0, z1, 'mechD')
    m.bxr(0.2, -0.28, 2.35, 0.42, 0.06, 0.6, 'mech', rot=(0, 0, -6))          # one chest plate on
    m.sp((-0.12, -0.05, 2.3), 0.14, 'cyan', seg=(8, 5))
    g.sp((-0.12, -0.05, 2.3), 0.16, 'cyanL', seg=(8, 5), hull='none')
    for sx in (-1, 1):
        m.cy((sx * 0.48, 0.0, 2.55), 0.13, 0.13, 0.16, 'graph', seg=10, rot=(0, 90, 0))
    m.bxr(0.62, 0.0, 2.15, 0.16, 0.18, 0.6, 'mech', rot=(0, -8, 0))           # right arm
    m.bxr(0.72, -0.12, 1.65, 0.14, 0.16, 0.5, 'mechD', rot=(28, -8, 0))
    m.bx(0.62, 0.84, -0.42, -0.24, 1.32, 1.48, 'graph')
    m.bx(-0.14, 0.14, -0.16, 0.12, 2.75, 3.0, 'mech')                         # head
    fq(m, -0.11, 0.11, -0.163, 2.85, 2.92, 'black')
    g.bx(-0.1, 0.1, -0.167, -0.163, 2.86, 2.91, 'cyan', hull='none')
    for sx in (-1, 1):   # hoist chains to the shoulders
        m.beam((sx * 0.25, 0.0, 3.9), (sx * 0.45, 0.0, 2.7), 0.04, 'steelD')
    m.beam((0, 0, 3.9), (0, 0, 3.02), 0.04, 'steelD')
    # the left arm waits on a stand; two cobots work on the legs; sparks glow at the weld point
    m.bx(-1.45, -1.05, 0.6, 1.0, 0.0, 0.9, 'graph')
    m.bxr(-1.25, 0.8, 1.2, 0.16, 0.18, 0.62, 'mech', rot=(0, 75, 0))
    cobot(m, -1.25, -0.85, 15, reach=1.0, lift=-0.4)
    g.sp((-0.33, -0.18, 1.1), 0.05, 'glow', seg=(6, 4), hull='none')
    cols = [cb(sx * 1.85 - 0.13, sy * 1.6 - 0.13, 0.0, sx * 1.85 + 0.13, sy * 1.6 + 0.13, 4.6) for sx in (-1, 1) for sy in (-1, 1)]
    cols += [cb(-0.5, -0.34, 0.0, 0.5, 0.26, 3.0), cb(-1.47, -1.07, 0.0, -1.03, -0.63, 0.75), cb(-1.45, 0.6, 0.0, -1.05, 1.0, 0.9)]
    make('Landmark_GantryMech', m, ao, cols=cols)
    make_glow('Landmark_GantryMech_LED', g)
    # quadruped walker on jack stands, one leg off
    m, g = new(pal), new(pal)
    gantry(m)
    m.bx(-0.85, 0.85, -0.5, 0.5, 1.25, 1.75, 'mech')
    m.bx(-0.87, 0.87, -0.52, 0.52, 1.45, 1.5, 'tealD', hull='none', cull='tb')
    m.bx(-0.4, 0.4, -0.3, 0.3, 1.75, 1.95, 'graphL')
    m.bx(0.85, 1.15, -0.25, 0.25, 1.35, 1.7, 'mechD')
    g.bx(1.152, 1.156, -0.15, 0.15, 1.48, 1.58, 'cyan', hull='none')
    for x in (-0.5, 0.5):
        m.bx(x - 0.18, x + 0.18, -0.18, 0.18, 0.0, 1.25, 'steelD')
        m.bx(x - 0.25, x + 0.25, -0.25, 0.25, 0.0, 0.08, 'hazY', hull='none', cull='b')
    for (x, y, k) in ((-0.7, -0.5, 1), (0.7, -0.5, 1), (-0.7, 0.5, 1)):
        sy = -1 if y < 0 else 1
        m.cy((x, y + sy * 0.08, 1.5), 0.13, 0.13, 0.16, 'graph', seg=10, rot=(90, 0, 0))
        m.beam((x, y + sy * 0.15, 1.5), (x, y + sy * 0.55, 1.0), 0.16, 'mechD')
        m.beam((x, y + sy * 0.55, 1.0), (x, y + sy * 0.62, 0.12), 0.13, 'mech')
        m.cy((x, y + sy * 0.62, 0.0), 0.14, 0.12, 0.12, 'graph', seg=8)
    m.cy((0.7, 0.58, 1.5), 0.13, 0.13, 0.16, 'graph', seg=10, rot=(90, 0, 0))
    m.cy((0.7, 0.6, 1.5), 0.06, 0.06, 0.3, 'cabR', seg=5, rot=(90, 0, 0), hull='none')
    m.bxr(1.25, 1.05, 0.12, 0.9, 0.16, 0.16, 'mechD', rot=(0, 0, 20))           # the loose leg on the floor
    m.bxr(0.55, 1.2, 0.1, 0.7, 0.13, 0.13, 'mech', rot=(0, 0, -35))
    g.sp((-0.7, 0.3, 1.45), 0.05, 'glow', seg=(6, 4), hull='none')
    cols = [cb(sx * 1.85 - 0.13, sy * 1.6 - 0.13, 0.0, sx * 1.85 + 0.13, sy * 1.6 + 0.13, 4.6) for sx in (-1, 1) for sy in (-1, 1)]
    cols += [cb(-0.9, -1.15, 0.0, 1.15, 1.15, 1.95), cb(0.7, 0.85, 0.0, 1.75, 1.3, 0.3)]
    make('Landmark_GantryWalker', m, ao, cols=cols)
    make_glow('Landmark_GantryWalker_LED', g)


# ================================================================ weapon prototype pod in a containment field [2, 2]
POD_R = 0.74


def build_pods(pal, ao):
    m = new(pal)
    m.cy((0, 0, 0.0), 0.88, 0.88, 0.2, 'graph', seg=16)
    ring(m, 0, 0, 0.203, 0.62, 0.7, 'cyan', seg=16)
    m.cy((0, 0, 0.2), 0.22, 0.28, 0.75, 'graphL', seg=10)
    m.bx(-0.36, 0.36, -0.12, 0.12, 0.95, 1.0, 'graphD')
    for s in (-1, 1):
        m.bx(s * 0.32 - 0.03, s * 0.32 + 0.03, -0.1, 0.1, 1.0, 1.12, 'chrome', hull='none')
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = math.cos(a) * 0.8, math.sin(a) * 0.8
        m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.2, 2.62, 'steelL')
    m.cy((0, 0, 2.6), 0.88, 0.85, 0.16, 'graph', seg=16)
    ring(m, 0, 0, 2.596, 0.6, 0.72, 'cyan', seg=16, normal=(0, 0, -1))
    m.cy((0, 0, 2.76), 0.3, 0.2, 0.12, 'graphD', seg=10)
    make('FieldPod', m, ao, cols=[cb(-0.88, -0.88, 0.0, 0.88, 0.88, 0.2)] +
         [cb(math.cos(math.pi / 4 + k * math.pi / 2) * 0.8 - 0.05, math.sin(math.pi / 4 + k * math.pi / 2) * 0.8 - 0.05, 0.2,
             math.cos(math.pi / 4 + k * math.pi / 2) * 0.8 + 0.05, math.sin(math.pi / 4 + k * math.pi / 2) * 0.8 + 0.05, 2.62) for k in range(4)])

    def field(g, keep, col, hexc):
        n = 8
        for k in range(n):
            if k not in keep:
                continue
            a0, a1 = k / n * 2 * math.pi + math.pi / 8, (k + 1) / n * 2 * math.pi + math.pi / 8
            p0 = (math.cos(a0) * POD_R, math.sin(a0) * POD_R)
            p1 = (math.cos(a1) * POD_R, math.sin(a1) * POD_R)
            nrm = (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0)
            for sgn in (1, -1):
                poly(g, [(p0[0], p0[1], 0.22), (p1[0], p1[1], 0.22), (p1[0], p1[1], 2.58), (p0[0], p0[1], 2.58)], col, (nrm[0] * sgn, nrm[1] * sgn, 0))
            for z in (0.5, 1.0, 1.5, 2.0):   # hex rows: short bright dashes on the panel
                q = 0.98
                a, b = (p0[0] * q + p1[0] * (1 - q), p0[1] * q + p1[1] * (1 - q)), (p0[0] * (1 - q) + p1[0] * q, p0[1] * (1 - q) + p1[1] * q)
                g.beam((a[0] * 1.04, a[1] * 1.04, z + (k % 2) * 0.25), (b[0] * 1.04, b[1] * 1.04, z + (k % 2) * 0.25), 0.012, hexc)
    for st, keep, col in (('_Leaf', range(8), 'scrB'), ('_Leaf_D1', (0, 1, 2, 4, 5, 6, 7), 'scrB'), ('_Leaf_D2', (0, 2, 3, 5, 7), 'field')):
        g = new(pal)
        field(g, list(keep), col, 'cyanL')
        obj = make_glow('FieldPod' + st, g)
        if st == '_Leaf':
            e = bpy.data.objects.new(PFX + 'FieldPod_Leaf_COL0', None)
            e.empty_display_type = 'CUBE'
            bpy.context.scene.collection.objects.link(e)
            e.parent = obj
            e.location = (0, 0, 1.4)
            e.scale = (0.8, 0.8, 1.2)
    m = new(pal)                     # after it blows: scorch on the base, a dead emitter segment fallen on the base
    rnd = random.Random(61)
    for k in range(6):
        a = k / 6 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(0.38, 0.55)
        cx, cy = math.cos(a) * r, math.sin(a) * r
        poly(m, [(cx + math.cos(a + j * 2.1) * 0.12, cy + math.sin(a + j * 2.1) * 0.08, 0.207 + (k % 2) * 0.003) for j in range(3)], 'black', (0, 0, 1))
    torus(m, 0.2, 0.0, 0.25, 0.42, 0.03, 'steelD', seg=6, sides=4, axis='z', a0=0.3, a1=1.6)
    make('FieldPod_Broken', m, ao)


# ================================================================ cryo cylinders [1, 1]
def build_cryo(pal, ao):
    for name, figure in (('CryoPod_A', 'android'), ('CryoPod_B', 'robot')):
        m, g = new(pal), new(pal)
        m.cy((0, 0, 0.0), 0.46, 0.46, 0.28, 'graph', seg=12)
        m.cy((0, 0, 2.3), 0.46, 0.46, 0.28, 'graph', seg=12)
        m.cy((0, 0, 2.58), 0.28, 0.2, 0.2, 'graphD', seg=10)
        for k in range(2):
            m.cy((-0.12 + k * 0.24, 0.12, 2.78), 0.05, 0.05, H - 2.78, 'cabK', seg=5, caps=False, hull='none')
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            x, y = math.cos(a) * 0.41, math.sin(a) * 0.41
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.28, 2.3, 'steelL')
        # glass: frost banks at the foot, a few streaks (the rest reads as clear)
        for k in range(12):
            a0, a1 = k / 12 * 2 * math.pi, (k + 1) / 12 * 2 * math.pi
            p0, p1 = (math.cos(a0) * 0.4, math.sin(a0) * 0.4), (math.cos(a1) * 0.4, math.sin(a1) * 0.4)
            nrm = (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0)
            top = 0.55 + 0.15 * math.sin(k * 1.7) ** 2
            poly(m, [(p0[0], p0[1], 0.28), (p1[0], p1[1], 0.28), (p1[0], p1[1], top), (p0[0], p0[1], top)], 'frost', nrm)
            if k in (7, 8):
                poly(m, [(p0[0] * 1.002, p0[1] * 1.002, 1.2), (p1[0] * 1.002, p1[1] * 1.002, 1.5), (p1[0] * 1.002, p1[1] * 1.002, 1.62), (p0[0] * 1.002, p0[1] * 1.002, 1.32)], 'glassL', nrm)
        ring(g, 0, 0, 0.283, 0.3, 0.38, 'cyanL', seg=12)
        ring(g, 0, 0, 2.297, 0.3, 0.38, 'cyanL', seg=12, normal=(0, 0, -1))
        fq(m, -0.12, 0.12, -0.463, 0.08, 0.2, 'screen')
        fq(g, -0.1, 0.1, -0.466, 0.1, 0.18, 'scrC')
        if figure == 'android':
            for sx in (-1, 1):
                m.bx(sx * 0.09 - 0.05, sx * 0.09 + 0.05, -0.05, 0.05, 0.36, 1.18, 'mechD')
                m.bx(sx * 0.2 - 0.04, sx * 0.2 + 0.04, -0.04, 0.04, 1.2, 1.78, 'mech')
            m.bx(-0.16, 0.16, -0.08, 0.08, 1.15, 1.85, 'mech')
            m.bx(-0.165, 0.165, -0.085, 0.085, 1.4, 1.45, 'tealD', hull='none', cull='tb')
            m.sp((0, 0, 2.0), 0.11, 'mech', seg=(8, 5), scale=(1, 1, 1.15))
            fq(m, -0.06, 0.06, -0.105, 1.98, 2.02, 'graphD')
            m.cy((0.0, 0.0, 2.1), 0.015, 0.015, 0.2, 'cabK', seg=4, hull='none', caps=False)
        else:
            m.bx(-0.06, 0.06, -0.06, 0.06, 0.28, 1.2, 'graphD')
            m.bx(-0.2, 0.2, -0.13, 0.13, 1.2, 1.7, 'mechD')
            m.bx(-0.205, 0.205, -0.135, 0.135, 1.42, 1.48, 'teal', hull='none', cull='tb')
            m.bx(-0.13, 0.13, -0.12, 0.1, 1.75, 2.0, 'mech')
            fq(m, -0.1, 0.1, -0.123, 1.84, 1.9, 'black')
            g.bx(-0.08, 0.08, -0.127, -0.124, 1.85, 1.89, 'cyan', hull='none')
            for sx in (-1, 1):
                m.beam((sx * 0.2, 0.0, 1.62), (sx * 0.3, -0.05, 1.25), 0.06, 'mech')
        make(name, m, ao, cols=[cb(-0.46, -0.46, 0.0, 0.46, 0.46, 2.6)])
        make_glow(name + '_LED', g)


# ================================================================ benches, fabricator, cobot, parts shelf
def bench_base(m):
    m.bx(-0.98, 0.98, -0.45, 0.45, 0.86, 0.92, 'wallW')
    fq(m, -0.98, 0.98, -0.453, 0.87, 0.91, 'cyan')
    for sx in (-1, 1):
        m.bx(sx * 0.9 - 0.04, sx * 0.9 + 0.04, -0.4, 0.4, 0.0, 0.86, 'graph')
    m.bx(-0.86, 0.86, -0.38, 0.38, 0.15, 0.2, 'graph', hull='none')
    m.bx(-0.86, 0.86, 0.3, 0.38, 0.2, 0.86, 'graphL', hull='none')


def build_benches(pal, ao):
    m = new(pal); bench_base(m)                                        # a robot forearm in a jig, calipers, tablet
    m.bx(-0.7, -0.5, -0.15, 0.15, 0.92, 1.05, 'graphD')
    m.beam((-0.6, 0.0, 1.08), (0.25, 0.05, 1.12), 0.14, 'mech')
    m.cy((-0.62, -0.09, 1.08), 0.1, 0.1, 0.18, 'graph', seg=8, rot=(-90, 0, 0))
    for k in range(3):
        m.beam((0.25, 0.05, 1.12), (0.42 + k * 0.03, -0.08 + k * 0.08, 1.06), 0.035, 'steelL')
    m.bx(0.45, 0.8, -0.3, -0.05, 0.92, 0.94, 'black', hull='none')
    m.bx(0.48, 0.77, -0.28, -0.07, 0.94, 0.945, 'scrB', hull='none')
    make('LabBench_Arm', m, ao, cols=[cb(-0.98, -0.45, 0.0, 0.98, 0.45, 0.92)])
    m = new(pal); bench_base(m)                                        # microscope and circuit boards
    m.bx(-0.55, -0.25, -0.15, 0.15, 0.92, 0.97, 'graph')
    m.bx(-0.45, -0.35, 0.05, 0.15, 0.97, 1.45, 'graph')
    m.bxr(-0.4, -0.02, 1.42, 0.09, 0.32, 0.09, 'graphL', rot=(30, 0, 0))
    m.cy((-0.4, -0.04, 1.06), 0.04, 0.03, 0.25, 'black', seg=6)
    for k in range(4):
        x = 0.05 + k * 0.2
        m.bx(x - 0.08, x + 0.08, -0.25 + (k % 2) * 0.2, -0.05 + (k % 2) * 0.2, 0.92, 0.935, 'cabG')
        uq(m, x - 0.04, x + 0.02, -0.2 + (k % 2) * 0.2, -0.14 + (k % 2) * 0.2, 0.938, 'black')
        uq(m, x + 0.03, x + 0.06, -0.12 + (k % 2) * 0.2, -0.08 + (k % 2) * 0.2, 0.938, 'gold')
    make('LabBench_Chip', m, ao, cols=[cb(-0.98, -0.45, 0.0, 0.98, 0.45, 0.92)])
    m = new(pal); bench_base(m)                                        # servos, a robot hand, a sensor head
    for k in range(3):
        x = -0.7 + k * 0.18
        m.cy((x, -0.15, 0.92), 0.06, 0.06, 0.12, 'graphD', seg=8)
        m.cy((x, -0.15, 1.04), 0.03, 0.03, 0.03, 'chrome', seg=6, hull='none')
    m.bx(-0.1, 0.18, -0.12, 0.1, 0.92, 1.0, 'mech')
    for k in range(4):
        m.beam((-0.06 + k * 0.07, -0.12, 0.97), (-0.06 + k * 0.07, -0.3, 0.95), 0.03, 'mechD')
    m.bx(0.4, 0.75, -0.15, 0.2, 0.92, 1.16, 'mech')
    fq(m, 0.45, 0.7, -0.153, 1.0, 1.08, 'black')
    make('LabBench_Parts', m, ao, cols=[cb(-0.98, -0.45, 0.0, 0.98, 0.45, 0.92)])
    # fabricator [2, 2]: a closed base cabinet, an open frame print chamber, a glowing bed, a half-printed receiver
    m, g = new(pal), new(pal)
    m.bx(-0.95, 0.95, -0.95, 0.95, 0.0, 0.85, 'wallW')
    fq(m, -0.9, 0.9, -0.953, 0.1, 0.75, 'wallL')
    fq(m, -0.9, 0.9, -0.956, 0.62, 0.66, 'cyan')
    text_front(m, 'HX-FAB 9', 0.06, -0.956, -0.5, 0.45, 'graph')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.9 - 0.05, sx * 0.9 + 0.05, sy * 0.9 - 0.05, sy * 0.9 + 0.05, 0.85, 2.3, 'graph')
    m.bx(-0.95, 0.95, -0.95, 0.95, 2.3, 2.5, 'graph')
    for sy in (-1, 1):
        m.bx(-0.85, 0.85, sy * 0.6 - 0.03, sy * 0.6 + 0.03, 1.95, 2.0, 'chrome', hull='none')
    m.bx(-0.85, 0.85, -0.06, 0.06, 1.9, 1.96, 'steelL')
    m.bx(-0.15, 0.15, -0.12, 0.12, 1.72, 1.9, 'graphD')
    m.bx(-0.7, 0.7, -0.7, 0.7, 0.85, 0.92, 'graphD')
    for k in range(6):
        z = 0.92 + k * 0.06
        w = 0.42 - k * 0.02
        m.bx(-w, w, -0.12, 0.12, z, z + 0.055, 'mechD' if k % 2 else 'mech', hull='full' if k == 5 else 'none')
    uq(g, -0.68, 0.68, -0.68, 0.68, 0.923, 'scrB')
    g.bx(-0.02, 0.02, -0.02, 0.02, 1.3, 1.72, 'cyanL', hull='none')
    make('Fabricator', m, ao, cols=[cb(-0.95, -0.95, 0.0, 0.95, 0.95, 2.5)])
    make_glow('Fabricator_LED', g)
    m = new(pal)
    cobot(m, 0.0, 0.0, 0, reach=0.8)
    make('Cobot', m, ao, cols=[cb(-0.25, -0.25, 0.0, 0.25, 0.25, 0.75)])
    # parts shelf [2, 1] against a wall: robot heads, arms, servos and labelled bins
    m = new(pal)
    rnd = random.Random(71)
    m.bx(-0.93, 0.93, 0.4, 0.5, 0.0, 2.3, 'graph')
    for sx in (-1, 1):
        m.bx(sx * 0.96 - 0.03, sx * 0.96 + 0.03, -0.1, 0.5, 0.0, 2.3, 'graph')
    for k, z in enumerate((0.1, 0.85, 1.6, 2.25)):
        m.bx(-0.93, 0.93, -0.1, 0.4, z, z + 0.05, 'steelL')
        if k == 3:
            break
        x = -0.75
        while x < 0.7:
            kind = rnd.choice(['head', 'bin', 'servo', 'bin', 'arm'])
            if kind == 'head':
                m.bx(x - 0.12, x + 0.12, 0.0, 0.25, z + 0.05, z + 0.3, 'mech')
                fq(m, x - 0.09, x + 0.09, -0.003, z + 0.15, z + 0.2, 'black')
                x += 0.32
            elif kind == 'bin':
                c = rnd.choice(['cabO', 'teal', 'blue'])
                m.bx(x - 0.13, x + 0.13, -0.05, 0.35, z + 0.05, z + 0.25, c)
                fq(m, x - 0.06, x + 0.06, -0.053, z + 0.12, z + 0.18, 'paper')
                x += 0.31
            elif kind == 'servo':
                m.cy((x, 0.1, z + 0.05), 0.05, 0.05, 0.11, 'graphD', seg=8)
                x += 0.2
            else:
                m.beam((x - 0.1, 0.1, z + 0.1), (x + 0.25, 0.1, z + 0.12), 0.09, 'mechD')
                x += 0.42
    make('PartsShelf', m, ao, cols=[cb(-0.98, -0.1, 0.0, 0.98, 0.5, 2.3)])


# ================================================================ energy test chamber [6, 6] and the Forge [8, 4]
def build_landmarks(pal, ao):
    m, g = new(pal), new(pal)
    # octagonal plinth, 0.45 m
    m.cy((0, 0, 0.0), 2.95, 2.95, 0.45, 'graph', seg=8, rot=(0, 0, 22.5))
    ring(m, 0, 0, 0.453, 2.35, 2.55, 'hazY', seg=8, a0=math.pi / 8)
    ring(m, 0, 0, 0.453, 2.0, 2.08, 'cyan', seg=16)
    # the standing ring with eight magnet blocks
    zc = 2.55
    torus(m, 0, 0, zc, 2.0, 0.22, 'steelL', seg=16, sides=5, axis='y')
    for k in range(8):
        a = k / 8 * 2 * math.pi + math.pi / 8
        x, z = math.cos(a) * 2.0, zc + math.sin(a) * 2.0
        if z < 0.7:
            continue
        m.push(x, 0, 0, 0)
        m.bxr(0.0, 0.0, z, 0.5, 0.62, 0.5, 'graphD', rot=(0, -math.degrees(a), 0))
        m.bxr(0.0, 0.0, z, 0.36, 0.66, 0.36, 'copper', rot=(0, -math.degrees(a), 0), hull='none')
        m.pop()
    for sx in (-1, 1):   # A-frame feet
        m.beam((sx * 1.4, -0.6, 0.45), (sx * 1.8, 0.0, 1.4), 0.22, 'graph')
        m.beam((sx * 1.4, 0.6, 0.45), (sx * 1.8, 0.0, 1.4), 0.22, 'graph')
    # containment rings round the core, the core itself (and its glow), cable trunks out to the edge
    torus(m, 0, 0, zc, 0.75, 0.025, 'chrome', seg=12, sides=3, axis='y')
    torus(m, 0, 0, zc, 0.7, 0.025, 'chrome', seg=12, sides=3, axis='x')
    torus(m, 0, 0, zc, 0.65, 0.025, 'chrome', seg=12, sides=3, axis='z')
    m.sp((0, 0, zc), 0.36, 'cyanL', seg=(8, 5))
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        m.beam((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.5), (math.cos(a) * 2.7, math.sin(a) * 2.7, 0.5), 0.16, 'black')
    # control console on the south edge
    m.bx(-0.7, 0.7, -2.9, -2.55, 0.45, 1.25, 'graphD')
    m.bxr(0.0, -2.68, 1.3, 1.36, 0.36, 0.06, 'graph', rot=(-25, 0, 0))
    text_front(m, 'TEST CHAMBER 2', 0.1, -2.903, 0.0, 0.62, 'cyanL', maxw=1.2)
    make('Landmark_Chamber', m, ao, cols=[cb(-2.95, -2.95, 0.0, 2.95, 2.95, 0.45), cb(-2.25, -0.25, 0.45, 2.25, 0.25, 4.8)])
    g.sp((0, 0, zc), 0.6, 'field', seg=(10, 6), hull='none')
    g.sp((0, 0, zc), 0.42, 'cyan', seg=(10, 6), hull='none')
    make_glow('Chamber_Core', g)
    g = new(pal)
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        g.beam((math.cos(a) * 1.0, math.sin(a) * 1.0, 0.6), (math.cos(a) * 2.6, math.sin(a) * 2.6, 0.6), 0.04, 'cyan')
    g.bxr(0.0, -2.72, 1.335, 1.2, 0.004, 0.05, 'scrC', rot=(-25, 0, 0), hull='none')
    make_glow('Landmark_Chamber_LED', g)
    # the Forge: a giant standing fabrication ring on a heavy base, arms holding a half-built railgun in its eye,
    # capacitor towers either side
    m, g = new(pal), new(pal)
    m.bx(-3.0, 3.0, -1.4, 1.4, 0.0, 0.8, 'graph')
    m.bx(-3.02, 3.02, -1.42, 1.42, 0.62, 0.68, 'cyan', hull='none', cull='tb')
    fq(m, -2.9, 2.9, -1.423, 0.12, 0.5, 'graphD')
    chevrons(m, -2.9, 2.9, -1.426, 0.15, 0.45, 16)
    zc = 3.0
    torus(m, 0, 0, zc, 2.15, 0.28, 'mech', seg=20, sides=5, axis='y')
    for k in range(14):
        a = k / 14 * 2 * math.pi
        g.bxr(math.cos(a) * 2.15, -0.31, zc + math.sin(a) * 2.15, 0.36, 0.01, 0.12, 'cyan', rot=(0, -math.degrees(a) + 90, 0), hull='none')
    for sx in (-1, 1):
        m.bx(sx * 1.55 - 0.3, sx * 1.55 + 0.3, -0.4, 0.4, 0.8, 1.6, 'graphD')
    # the prototype in its eye: a long rail barrel with coil rings, a receiver block, two clamps
    m.bx(-0.9, 0.5, -0.16, 0.16, zc - 0.15, zc + 0.15, 'graphL')
    m.bx(0.5, 1.5, -0.07, 0.07, zc - 0.05, zc + 0.05, 'steelL')
    for k in range(5):
        torus(m, 0.62 + k * 0.18, 0, zc, 0.11, 0.03, 'copper', seg=8, sides=4, axis='x')
    m.bx(-1.3, -0.9, -0.1, 0.1, zc - 0.35, zc + 0.05, 'mechD')
    for sx in (-1, 1):
        m.beam((sx * 0.5, 0.0, zc + 0.15), (sx * 1.3, 0.0, zc + 1.6), 0.12, 'graph')
    g.sp((-0.2, 0.0, zc + 0.17), 0.06, 'glow', seg=(6, 4), hull='none')
    # capacitor towers
    for sx in (-1, 1):
        x = sx * 3.45
        m.cy((x, 0.0, 0.0), 0.5, 0.5, 0.3, 'graph', seg=10)
        m.cy((x, 0.0, 0.3), 0.36, 0.36, 4.0, 'graphL', seg=8)
        for k in range(3):
            m.cy((x, 0.0, 1.0 + k * 1.2), 0.42, 0.42, 0.18, 'copper', seg=8)
        for k in range(3):
            g.cy((x, 0.0, 1.6 + k * 1.2), 0.365, 0.365, 0.06, 'cyan', seg=8, caps=False, hull='none')
        m.cy((x, 0.0, 4.3), 0.28, 0.1, 0.4, 'graphD', seg=8)
        m.beam((x, 0.0, 4.5), (sx * 2.2, 0.0, zc + 1.6), 0.08, 'black')
    make('Landmark_Forge', m, ao, cols=[cb(-3.0, -1.4, 0.0, 3.0, 1.4, 0.8), cb(-2.45, -0.4, 0.8, 2.45, 0.4, 5.3),
                                        cb(-3.95, -0.5, 0.0, -2.95, 0.5, 4.3), cb(2.95, -0.5, 0.0, 3.95, 0.5, 4.3)])
    make_glow('Landmark_Forge_LED', g)
