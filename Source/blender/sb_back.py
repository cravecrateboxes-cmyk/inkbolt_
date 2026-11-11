"""kit-seabase deep-sea backdrop (placed by the theme's backdrop.build, far out in the dark water): boulders, a rock
spire, distant station pods on legs with lit window bands, a lattice pylon with a beacon, a pipeline segment on its
supports. Low-poly faceted shapes (see sb_base.py for conventions)."""
import math
import random

from sb_base import *  # noqa: F401,F403
import sb_base as B
from kit_util import hull_pts


def boulder(m, rnd, cx, cy, rx, ry, h, z0=0.0, c='rock'):
    pts = []
    for q in range(8):
        b = (q + rnd.uniform(-0.3, 0.3)) / 8 * 2 * math.pi
        pts.append((cx + math.cos(b) * rx * rnd.uniform(0.8, 1.0), cy + math.sin(b) * ry * rnd.uniform(0.8, 1.0), z0))
    for q in range(6):
        b = rnd.uniform(0, 2 * math.pi)
        k = rnd.uniform(0.3, 0.85)
        pts.append((cx + math.cos(b) * rx * k, cy + math.sin(b) * ry * k, z0 + h * rnd.uniform(0.55, 1.0)))
    hull_pts(m, pts, lambda f: c if f.normal.z < 0.6 else ('rockL' if c == 'rock' else 'rock'))


def build_back(pal, ao):
    for name, seed, s in (('BD_Rock_A', 3, 1.0), ('BD_Rock_B', 7, 1.4)):
        rnd = random.Random(seed)
        m = new(pal)
        boulder(m, rnd, 0, 0, 3.2 * s, 2.4 * s, 2.6 * s)
        boulder(m, rnd, 2.6 * s, 1.2 * s, 1.4 * s, 1.2 * s, 1.5 * s, c='rockD')
        boulder(m, rnd, -2.2 * s, -1.6 * s, 1.1 * s, 0.9 * s, 1.0 * s)
        make(name, m, ao)
    rnd = random.Random(11)
    m = new(pal)
    boulder(m, rnd, 0, 0, 3.0, 2.6, 5.5)
    boulder(m, rnd, 0.3, -0.2, 2.0, 1.8, 6.0, z0=4.5, c='rockD')
    boulder(m, rnd, -0.2, 0.3, 1.2, 1.0, 5.0, z0=9.5)
    boulder(m, rnd, 2.8, 1.5, 1.6, 1.3, 2.2)
    make('BD_Spire', m, ao)
    # a station pod on legs: hull cylinder, end domes, a lit window band, a mast with a beacon
    m = new(pal)
    m.cy((-4.0, 0, 3.6), 2.1, 2.1, 8.0, 'hull', seg=10, rot=(0, 90, 0), caps=False)
    for sx in (-1, 1):
        m.sp((sx * 4.0, 0, 3.6), 2.1, 'hull', seg=(10, 4), scale=(0.45, 1, 1))
        for sy in (-1, 1):
            m.bm_((sx * 2.8, sy * 1.2, 2.0), (sx * 3.4, sy * 2.6, 0.0), 0.3, 'hullD')
    for sy in (-1, 1):
        (fq if sy < 0 else bq)(m, -3.4, 3.4, sy * 2.07, 3.7, 4.2, 'lamp')
        for k in range(8):
            x = -3.2 + k * 0.85
            (fq if sy < 0 else bq)(m, x, x + 0.12, sy * 2.075, 3.7, 4.2, 'hullD')
        (fq if sy < 0 else bq)(m, -3.8, 3.8, sy * 2.07, 2.6, 2.75, 'hazY')
    m.cy((1.5, 0, 5.6), 0.08, 0.08, 2.4, 'rib', seg=5)
    m.sp((1.5, 0, 8.0), 0.22, 'orange', seg=(6, 3))
    m.sp((-1.0, 0, 5.4), 1.0, 'glassE', seg=(8, 3), scale=(1, 1, 0.6))
    make('BD_Pod', m, ao)
    # lattice pylon with a beacon
    m = new(pal)
    Hp = 11.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bm_((sx * 1.4, sy * 1.4, 0.0), (sx * 0.35, sy * 0.35, Hp), 0.16, 'hazY')
    for k in range(4):
        z0, z1 = k * Hp / 4, (k + 1) * Hp / 4
        w0, w1 = 1.4 - 1.05 * k / 4, 1.4 - 1.05 * (k + 1) / 4
        for s in (-1, 1):
            m.bm_((-w0, s * w0, z0), (w1, s * w1, z1), 0.07, 'steelD')
            m.bm_((s * w0, -w0, z0), (s * w1, w1, z1), 0.07, 'steelD')
    m.cy((0, 0, Hp), 0.5, 0.5, 0.3, 'hazY', seg=8)
    m.sp((0, 0, Hp + 0.55), 0.3, 'fireR', seg=(6, 3))
    make('BD_Pylon', m, ao)
    # pipeline segment on supports (10 m along X)
    m = new(pal)
    m.cy((-5.0, 0, 1.2), 0.55, 0.55, 10.0, 'tealD', seg=8, rot=(0, 90, 0), caps=False, hull='noside')
    for x in (-3.5, 0.0, 3.5):
        m.bx(x - 0.3, x + 0.3, -0.8, 0.8, 0.0, 0.75, 'steelD')
        m.cy((x - 0.15, 0, 1.2), 0.6, 0.6, 0.3, 'hazY', seg=8, rot=(0, 90, 0), caps=False, hull='none')
    make('BD_Pipe', m, ao)
