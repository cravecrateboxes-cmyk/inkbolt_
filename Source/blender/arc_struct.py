"""kit-arctic wall modules: firn strata (the trench), the entry ramp buried by a snow slide, the station facade with the
name board, station interiors (corridor / bunks / comms and the mess hall), glacier ice (the deep caves), the lab
modules' outer shell, lab interiors, the generator hall plating, and a corner post per finish (see arc_base.py).
Every module fills its cell; its face is the plane y = -0.5 (game +Z, the open side). The face functions take an
x range and a height range so door frames and the gate paint the same finish round their openings."""
import math

from arc_base import *  # noqa: F401,F403
import arc_base as B

# ---------------------------------------------------------------- strata: (bottom of band, colour, line under it)
FIRN = [(0.0, 'iceM', None), (1.6, 'ice', 'iceD'), (3.0, 'firn', 'line'), (4.2, 'iceL', 'snowD'), (5.9, 'ice', None),
        (7.0, 'firn', 'line'), (8.8, 'snowL', 'snowD'), (10.2, 'snowW', 'line')]
FIRN_LEDGE = (3.0, 7.0)                # ledges stand proud where the firn turns (straight boundaries)
CAVE = [(0.0, 'iceD', None), (1.4, 'iceK', 'iceN'), (2.6, 'iceD', None), (4.1, 'iceM', 'iceK'), (5.6, 'iceD', None),
        (7.4, 'iceM', 'iceN'), (9.6, 'ice', 'iceD'), (11.0, 'iceM', None)]
CAVE_LEDGE = (2.6, 7.4)
BULGE = {'A': (0.0, 0.12, -0.1, 0.0, 0.14, 0.0, -0.12, 0.1), 'B': (0.0, -0.1, 0.14, 0.0, -0.08, 0.0, 0.12, -0.06),
         'C': (0.0, 0.06, 0.04, 0.0, -0.14, 0.0, 0.08, 0.14), '0': (0.0,) * 8}


def P(plane, at, u, v):
    return (u, at, v) if plane == 'y' else (at, u, v)


def paint(m, plane, at, s, pts, c):
    """a flat polygon on the plane y = at (plane 'y', facing s * Y) or x = at (plane 'x', facing s * X); pts (u, z)"""
    poly(m, [P(plane, at, u, v) for (u, v) in pts], c, (0, s, 0) if plane == 'y' else (s, 0, 0))


def strata(m, bands, bul, plane='y', at=-0.5, s=-1, u0=-0.5, u1=0.5, zmin=0.0, zmax=H, mids=None):
    """paint layered bands between u0 and u1 (boundaries bulge by bul[i] at the middle, straight at the ends so modules
    run on); old snow lines a little proud of the bands"""
    um = (u0 + u1) / 2 if mids is None else mids

    def bz(i):
        if i >= len(bands):
            return (H, H, H)
        b = bands[i][0]
        k = bul[i] if i < len(bul) else 0.0
        return (b, b + k, b)
    for i, (z0, c, line) in enumerate(bands):
        lo, hi = bz(i), bz(i + 1)
        if hi[0] <= zmin or lo[0] >= zmax:
            continue
        lo = [min(max(v, zmin), zmax) for v in lo]
        hi = [min(max(v, zmin), zmax) for v in hi]
        if max(h - l for h, l in zip(hi, lo)) < 0.01:
            continue
        paint(m, plane, at, s, [(u0, lo[0]), (um, lo[1]), (u1, lo[2]), (u1, hi[2]), (um, hi[1]), (u0, hi[0])], c)
        if line and zmin < lo[1] < zmax - 0.05:
            a2 = at + s * 0.003
            paint(m, plane, a2, s, [(u0, lo[0]), (um, lo[1]), (u1, lo[2]), (u1, lo[2] + 0.06), (um, lo[1] + 0.075), (u0, lo[0] + 0.06)], line)


def ledge(m, x0, x1, z, c='snowW', d=0.09, under='firn', hull='noside'):
    """a proud strip where the strata turn, snow on top; no level faces (two modules meeting in an inside corner
    overlap here, and level faces of theirs would share a plane)"""
    m.prism([(-0.5, z - 0.14), (-0.5 - d, z - 0.07), (-0.5 - d - 0.01, z), (-0.5, z + 0.03)], x0, x1, [under], hull=hull, skip=(3,))
    m.prism([(-0.5, z + 0.03), (-0.5 - d - 0.01, z + 0.002), (-0.5 - d - 0.03, z + 0.03), (-0.5, z + 0.08)], x0, x1, [c], hull=hull, skip=(3,))


def drift_skirt(m, x0=-0.5, x1=0.5, d=0.38, h=0.55, c='snowL'):
    m.prism([(-0.5, 0.0), (-0.5 - d, 0.0), (-0.5 - d * 0.35, h * 0.6), (-0.5, h)], x0, x1, [c], hull='noside', skip=(0, 3))


def cornice(m, rnd, x0=-0.5, x1=0.5, icy=0):
    m.prism([(-0.5, 11.35), (-0.62, 11.42), (-0.8, 11.7), (-0.74, 12.0), (-0.5, 12.0)], x0, x1, ['snowW'], hull='noside', skip=(3, 4))
    if icy:
        icicles(m, rnd, x0 + 0.05, x1 - 0.05, -0.68, 11.43, icy, 0.9, 'iceL')


def firn_face(m, x0=-0.5, x1=0.5, zmin=0.0, v='A', rnd=None, skirt=True, top=True):
    strata(m, FIRN, BULGE[v], u0=x0, u1=x1, zmin=zmin)
    for i, z in enumerate(FIRN_LEDGE):   # one proud ledge (with its ink line), the other painted
        if z > zmin + 0.2:
            ledge(m, x0, x1, z) if i == 0 else fq(m, x0, x1, -0.506, z - 0.02, z + 0.05, 'snowW')
    if skirt and zmin < 0.1:
        drift_skirt(m, x0, x1)
    if top:
        cornice(m, rnd or RND(1), x0, x1, icy=(3 if v == 'C' else 0))


def cave_face(m, x0=-0.5, x1=0.5, zmin=0.0, v='A', rnd=None, skirt=True):
    strata(m, CAVE, BULGE[v], u0=x0, u1=x1, zmin=zmin)
    for i, z in enumerate(CAVE_LEDGE):
        if z > zmin + 0.2:
            ledge(m, x0, x1, z, c='iceL', d=0.07, under='iceD') if i == 0 else fq(m, x0, x1, -0.506, z - 0.02, z + 0.04, 'iceL')
    rnd = rnd or RND(7)
    for _ in range(2 if v != '0' else 0):   # trapped air bubbles
        x, z = rnd.uniform(x0 + 0.08, x1 - 0.08), rnd.uniform(max(zmin, 0.6), 10.5)
        fq(m, x - 0.025, x + 0.025, -0.506, z, z + 0.05, 'iceL')
    if skirt and zmin < 0.1:
        drift_skirt(m, x0, x1, 0.3, 0.35, 'snowS')


# ---------------------------------------------------------------- station / lab finishes (front face only up to the ceiling)
def st_face(m, x0=-0.5, x1=0.5, z1=CS, y=-0.5, s=-1, seam=True):
    f = fq if s < 0 else bq
    f(m, x0, x1, y, 0.0, z1, 'panelW')
    f(m, x0, x1, y + s * 0.003, 0.0, 0.14, 'vinylD')
    f(m, x0, x1, y + s * 0.003, 0.14, 1.0, 'panelB')
    f(m, x0, x1, y + s * 0.006, 1.0, 1.06, 'panelK')
    f(m, x0, x1, y + s * 0.003, z1 - 0.12, z1, 'panelG')
    if seam and x0 <= -0.49:
        f(m, x0, x0 + 0.012, y + s * 0.003, 1.06, z1 - 0.12, 'panelG')


def mess_face(m, x0=-0.5, x1=0.5, z1=CS, y=-0.5, s=-1, seam=True):
    f = fq if s < 0 else bq
    f(m, x0, x1, y, 0.0, z1, 'panelW')
    f(m, x0, x1, y + s * 0.003, 0.0, 0.12, 'woodD')
    f(m, x0, x1, y + s * 0.003, 0.12, 1.1, 'wood')
    f(m, x0, x1, y + s * 0.006, 1.1, 1.16, 'woodD')
    f(m, x0, x1, y + s * 0.003, 2.4, 2.46, 'orange')
    f(m, x0, x1, y + s * 0.003, z1 - 0.12, z1, 'panelG')
    if seam and x0 <= -0.49:
        f(m, x0, x0 + 0.012, y + s * 0.006, 0.14, 1.08, 'woodD')


def lab_face(m, x0=-0.5, x1=0.5, z1=CL, y=-0.5, s=-1, seam=True):
    f = fq if s < 0 else bq
    f(m, x0, x1, y, 0.0, z1, 'panelW')
    f(m, x0, x1, y + s * 0.003, 0.0, 0.12, 'steelK')
    f(m, x0, x1, y + s * 0.003, 1.18, 1.26, 'blueP')
    f(m, x0, x1, y + s * 0.003, z1 - 0.3, z1, 'panelG')
    if seam and x0 <= -0.49:
        f(m, x0, x0 + 0.012, y + s * 0.003, 0.12, 1.18, 'panelG')
        f(m, x0, x0 + 0.012, y + s * 0.003, 1.26, z1 - 0.3, 'panelG')


def shell_face(m, x0=-0.5, x1=0.5, rnd=None, v='A', top=True):
    """the lab module's outer skin seen from the cave: ribbed steel to 4.6 m, a roof flashing, glacier ice above"""
    fq(m, x0, x1, -0.5, 0.0, 4.6, 'panelG')
    n = max(1, int(round((x1 - x0) / 0.25)))
    for k in range(n):
        a = x0 + (k + 0.4) * (x1 - x0) / n
        fq(m, a, a + 0.05, -0.503, 0.25, 4.3, 'panelB')
    fq(m, x0, x1, -0.503, 0.0, 0.25, 'steelK')
    fq(m, x0, x1, -0.506, 2.0, 2.16, 'orange')
    m.prism([(-0.5, 4.43), (-0.62, 4.47), (-0.62, 4.6), (-0.5, 4.64)], x0, x1, ['steelD'], hull='noside', skip=(3,))
    if top:
        strata(m, CAVE, BULGE[v], u0=x0, u1=x1, zmin=4.62)
        fq(m, x0, x1, -0.506, 7.38, 7.44, 'iceL')
    frost_spots(m, rnd or RND(3), x0 + 0.02, x1 - 0.02, 3.6, 4.4, -0.506, 3)


def fac_face(m, x0=-0.5, x1=0.5, rnd=None, v='A', top=True):
    """the station's front seen from the trench: insulated panels to 3.9 m under an eave, the overburden of firn above"""
    fq(m, x0, x1, -0.5, 0.0, 3.9, 'panelW')
    fq(m, x0, x1, -0.503, 0.0, 0.3, 'panelK')
    fq(m, x0, x1, -0.503, 0.86, 0.98, 'orange')
    if x0 <= -0.49:
        fq(m, x0, x0 + 0.02, -0.503, 0.3, 0.86, 'panelG')
        fq(m, x0, x0 + 0.02, -0.503, 0.98, 3.7, 'panelG')
    m.prism([(-0.5, 3.84), (-0.78, 3.88), (-0.78, 4.1), (-0.5, 4.14)], x0, x1, ['orangeD'], hull='noside', skip=(3,))
    m.prism([(-0.5, 4.14), (-0.8, 4.1), (-0.82, 4.17), (-0.5, 4.24)], x0, x1, ['snowW'], hull='noside', skip=(3,))
    if top:
        strata(m, FIRN, BULGE[v], u0=x0, u1=x1, zmin=4.22)
        fq(m, x0, x1, -0.506, 6.98, 7.05, 'snowW')
        cornice(m, rnd or RND(2), x0, x1)
    frost_spots(m, rnd or RND(4), x0 + 0.02, x1 - 0.02, 2.9, 3.8, -0.506, 3)
    drift_skirt(m, x0, x1, 0.32, 0.42)


def plant_face(m, x0=-0.5, x1=0.5, rnd=None, v='A', top=True):
    """generator hall: grey plated lower wall with a hazard foot, a crane-rail band, ice above 6 m"""
    fq(m, x0, x1, -0.5, 0.0, 6.0, 'steel')
    for z in (1.5, 3.0, 4.5):
        fq(m, x0, x1, -0.503, z, z + 0.03, 'steelD')
    if x0 <= -0.49:
        fq(m, x0, x0 + 0.02, -0.506, 0.3, 6.0, 'steelD')
    chevrons(m, x0, x1, -0.503, 0.0, 0.3, 4, ca='yel', cb_='black')
    m.prism([(-0.5, 5.78), (-0.66, 5.82), (-0.66, 6.08), (-0.5, 6.12)], x0, x1, ['steelK'], hull='noside', skip=(3,))
    if top:
        strata(m, CAVE, BULGE[v], u0=x0, u1=x1, zmin=6.1)
    frost_spots(m, rnd or RND(5), x0 + 0.02, x1 - 0.02, 4.8, 5.8, -0.509, 2)


# ---------------------------------------------------------------- art
def window_in(m, rnd, z0=1.1, z1=2.5, w=0.36, y=-0.5):
    """a station window seen from inside: frosted, packed snow pressed against the glass"""
    m.bx(-w - 0.06, w + 0.06, y - 0.06, y, z0 - 0.06, z1 + 0.06, 'panelG', cull='k')
    fq(m, -w, w, y - 0.063, z0, z1, 'snowS')
    poly(m, [(-w, y - 0.066, z0), (w, y - 0.066, z0), (w, y - 0.066, z0 + 0.5), (0.1, y - 0.066, z0 + 0.75), (-w, y - 0.066, z0 + 0.55)], 'snowL', (0, -1, 0))
    fq(m, -0.015, 0.015, y - 0.069, z0, z1, 'panelG')
    frost_spots(m, rnd, -w + 0.02, w - 0.02, z0 + 0.6, z1 - 0.02, y - 0.072, 4)


def heater(m, y=-0.5):
    m.bx(-0.3, 0.3, y - 0.12, y - 0.02, 0.18, 0.75, 'panelW', cull='k')
    for k in range(5):
        x = -0.22 + k * 0.11
        fq(m, x - 0.02, x + 0.02, y - 0.123, 0.22, 0.7, 'panelG')
    m.cy((0.32, y - 0.08, 0.2), 0.02, 0.02, 0.5, 'steelD', seg=6, hull='none')


def notice(m, rnd, y=-0.5):
    m.bx(-0.42, 0.42, y - 0.04, y, 1.3, 2.1, 'woodD', cull='k')
    fq(m, -0.39, 0.39, y - 0.043, 1.33, 2.07, 'cardb')
    for i in range(6):
        x, z = rnd.uniform(-0.3, 0.3), rnd.uniform(1.42, 1.95)
        w, h = rnd.uniform(0.07, 0.12), rnd.uniform(0.09, 0.14)
        fq(m, x - w, x + w, y - 0.047 - i * 0.004, z - h, z + h, rnd.choice(['paperY', 'paper', 'paperY', 'frost']))
        fq(m, x - 0.01, x + 0.01, y - 0.072, z + h - 0.03, z + h - 0.01, 'redE')


def pipes_v(m, xs=(-0.25, 0.05), c=('steelL', 'orange'), z1=CS, y=-0.5):
    for x, cc in zip(xs, c):
        m.cy((x, y - 0.1, 0.12), 0.05, 0.05, z1 - 0.12, cc, seg=8, caps=False)
        for z in (0.9, 2.4):
            m.bx(x - 0.07, x + 0.07, y - 0.16, y, z, z + 0.05, 'steelD', hull='none')


def sign_board(m, word, x=0.0, z=2.2, w=0.8, h=0.26, bg='tileB', fg='paper', y=-0.5, cap=None):
    m.bx(x - w / 2, x + w / 2, y - 0.03, y, z, z + h, bg, cull='k')
    text_front(m, word, cap or h * 0.55, y - 0.033, x, z + h * 0.22, fg, maxw=w * 0.9)


def ice_breach(m, rnd, y=-0.5, reach=0.75):
    """wall panels burst inward by the ice: bent panel shards round a bulge of glacier ice (its own collision)"""
    for (x, z, sx, sz, rx) in ((-0.3, 1.5, 0.35, 0.9, 18), (0.32, 2.2, 0.3, 0.7, -24), (0.05, 0.6, 0.5, 0.35, 10)):
        m.bxr(x, y - 0.06, z, sx, 0.03, sz, 'panelB' if z < 1 else 'panelW', rot=(rx, 0, rx * 0.5))
    lump(m, rnd, 0.0, y - reach * 0.45, 0.48, reach * 0.5, 2.6, 0.0, 'iceM', n=7, top=3)
    lump(m, rnd, 0.15, y - reach * 0.5, 0.3, reach * 0.4, 1.4, 0.0, 'ice', n=6, top=2)
    lump(m, rnd, -0.2, y - reach * 0.2, 0.32, 0.3, 3.4, 0.2, 'iceL', n=6, top=2)


def lamp_bracket(m, z=3.2, glow=None, y=-0.5, c='steelD'):
    m.bx(-0.04, 0.04, y - 0.35, y, z - 0.04, z + 0.04, c, cull='k')
    m.bx(-0.16, 0.16, y - 0.46, y - 0.3, z - 0.2, z, 'steelK')
    fq(m, -0.13, 0.13, y - 0.463, z - 0.17, z - 0.03, 'lampC')
    if glow is not None:
        fq(glow, -0.13, 0.13, y - 0.466, z - 0.17, z - 0.03, 'lamp')


# ---------------------------------------------------------------- builders
SIGNS = {'S': ['BUNK A', 'BUNK B', 'BUNK C', 'BUNK D', 'COMMS', 'SHAFT K-7', 'SCIENCE', 'BOOT ROOM'],
         'M': ['MESS'], 'L': ['CORE ARCHIVE', 'CRYO LAB', 'VAULT 3'], 'P': ['POWER HALL']}


def sname(w):
    return w.replace(' ', '').replace('-', '')


def mk(name, m, ao, **kw):
    """station / mess modules: the back gets the same finish (their partitions are one cell thick)"""
    if name[:2] in ('S_', 'M_'):
        (st_face if name[0] == 'S' else mess_face)(m, y=0.5, s=1, seam=False)
    make(name, m, ao, **kw)


def build_walls(pal, ao):
    # ---- firn (the trench)
    for v in ('A', 'B', 'C'):
        m = new(pal); firn_face(m, v=v, rnd=RND(ord(v))); make('Firn_' + v, m, ao)
    m = new(pal); firn_face(m, v='B', rnd=RND(11))   # a work lamp on a stake, its cable down the wall
    g = new(pal)
    lamp_bracket(m, 3.4, g)
    m.bx(-0.012, 0.012, -0.52, -0.5, 0.5, 3.2, 'black', hull='none', cull='k')
    make('Firn_Lamp', m, ao); make_glow('Firn_Lamp_LED', g)
    m = new(pal); firn_face(m, v='A', rnd=RND(12))   # a buried service pipe breaking out of the wall
    tube(m, (-0.2, -0.3, 2.2), (-0.2, -0.95, 2.05), 0.16, 'orangeD', seg=8)
    m.cy((-0.2, -0.95, 2.05), 0.2, 0.2, 0.06, 'steelD', seg=8, rot=(90, 0, 0))
    icicles(m, RND(5), -0.35, -0.05, -0.9, 1.88, 3, 0.35)
    make('Firn_Pipe', m, ao)
    m = new(pal); firn_face(m, v='C', rnd=RND(13))   # survey depth board
    m.bx(-0.05, 0.05, -0.56, -0.5, 0.4, 9.6, 'steelK', cull='k')
    for k in range(1, 10):
        fq(m, 0.05, 0.22 if k % 2 else 0.12, -0.51, k - 0.02, k + 0.02, 'black')
        if k % 3 == 0:
            text_front(m, '%d' % (12 - k), 0.16, -0.513, -0.2, k - 0.08, 'orange')
    make('Firn_Mark', m, ao)
    # ---- the entry ramp: a snow road up to the surface, buried at its foot by a fresh snow slide
    for v in ('L', 'M', 'N', 'R'):
        m = new(pal)
        rnd = RND({'L': 21, 'M': 22, 'N': 23, 'R': 24}[v])
        L = 32.0
        pts = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, L, H), (-0.5, L, H)]
        poly(m, pts, 'snowL', (0, -0.5, 1))
        for x in (-0.3, 0.3):   # vehicle ruts up the road
            poly(m, [(x - 0.08, -0.4, 0.004), (x + 0.08, -0.4, 0.004), (x + 0.08, L, H + 0.004), (x - 0.08, L, H + 0.004)], 'snowS', (0, -0.5, 1))
        dz = 0.03 * 'LMNR'.index(v)   # neighbouring modules' lumps never share a level face
        for i in range(3):   # the snow slide: big lumps over the road foot
            lump(m, rnd, rnd.uniform(-0.3, 0.3), -0.05 + i * 0.9, 0.75, 0.6, 2.4 - i * 0.4 + rnd.uniform(0, 0.4), i * 0.35 + dz, 'snowW' if i else 'snowL', n=7)
        lump(m, rnd, 0.0, 2.6, 0.7, 1.0, 1.4, 1.0 + dz, 'snowS', n=6)
        if v in ('L', 'R'):
            sx = -1 if v == 'L' else 1
            x = sx * 0.5
            # the cut's side wall, the strata running on, its top falling with the road
            for (y0, y1) in ((-0.5, 8.0), (8.0, 16.0), (16.0, 24.0), (24.0, L)):
                z0, z1 = H * (y0 + 0.5) / (L + 0.5), H * (y1 + 0.5) / (L + 0.5)
                poly(m, [(x, y0, z0), (x, y1, z1), (x, y1, H), (x, y0, H)], 'firn', (-sx, 0, 0))
                for zz, c in ((7.0, 'line'), (8.8, 'snowD'), (10.2, 'line')):
                    if zz > z1:
                        poly(m, [(x - sx * 0.003, y0, max(zz, z0)), (x - sx * 0.003, y1, max(zz, z1)), (x - sx * 0.003, y1, max(zz, z1) + 0.04), (x - sx * 0.003, y0, max(zz, z0) + 0.04)], c, (-sx, 0, 0))
            for k in range(4):   # route flags along the road
                y = 4 + k * 7.0
                z = H * (y + 0.5) / (L + 0.5)
                m.cy((-sx * 0.15 + x * 0.6, y, z), 0.02, 0.02, 1.6, 'black', seg=5, hull='none')
                m.bx(x * 0.6 - sx * 0.15, x * 0.6 - sx * 0.15 + 0.32, y - 0.01, y + 0.01, z + 1.25, z + 1.55, 'orange', hull='none')
        if v == 'M':   # the road sign at the top, half buried
            m.cy((0.0, L - 3, H - 0.6), 0.04, 0.04, 2.6, 'steelD', seg=6)
            m.bx(-0.9, 0.9, L - 3.06, L - 3.0, H + 1.2, H + 1.9, 'orange')
            text_front(m, 'K-7', 0.4, L - 3.065, 0.0, H + 1.33, 'black', maxw=1.4)
        make('Ramp_' + v, m, ao)
    m = new(pal)   # corner post: strata round all four sides
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'firn', cull='b')
    corner_bands(m, FIRN, 'snowW')
    make('CornerF', m, ao)
    # ---- the station facade (trench side)
    for v, k in (('A', 1), ('B', 2)):
        m = new(pal); fac_face(m, v=v, rnd=RND(30 + k)); make('Fac_' + v, m, ao)
    m = new(pal); fac_face(m, v='A', rnd=RND(33))   # window, frosted, dark inside
    m.bx(-0.42, 0.42, -0.58, -0.5, 1.0, 2.7, 'steelD', cull='k')
    fq(m, -0.36, 0.36, -0.583, 1.06, 2.64, 'glassD')
    poly(m, [(-0.36, -0.586, 1.06), (0.36, -0.586, 1.06), (0.36, -0.586, 1.5), (-0.36, -0.586, 1.8)], 'snowS', (0, -1, 0))
    frost_spots(m, RND(34), -0.34, 0.34, 1.9, 2.6, -0.589, 5)
    icicles(m, RND(35), -0.4, 0.4, -0.6, 0.99, 4, 0.25)
    make('Fac_Window', m, ao)
    m = new(pal); fac_face(m, v='B', rnd=RND(36))   # broken window, ice bursting out
    m.bx(-0.42, 0.42, -0.58, -0.5, 1.0, 2.7, 'steelD', cull='k')
    fq(m, -0.36, 0.36, -0.583, 1.06, 2.64, 'black')
    lump(m, RND(37), 0.0, -0.62, 0.34, 0.16, 1.3, 1.1, 'iceM', n=6)
    for (a, b) in ((-0.36, -0.18), (0.2, 0.36)):
        poly(m, [(a, -0.587, 2.64), (b, -0.587, 2.64), ((a + b) / 2, -0.587, 2.3)], 'glass', (0, -1, 0))
    make('Fac_Broken', m, ao)
    m = new(pal); fac_face(m, v='A', rnd=RND(38))   # louvred vent with a frost beard
    m.bx(-0.36, 0.36, -0.6, -0.5, 2.6, 3.3, 'steelL', cull='k')
    for k in range(5):
        fq(m, -0.32, 0.32, -0.603, 2.66 + k * 0.12, 2.72 + k * 0.12, 'steelD')
    icicles(m, RND(39), -0.34, 0.34, -0.62, 2.6, 4, 0.3)
    make('Fac_Vent', m, ao)
    m = new(pal); fac_face(m, v='B', rnd=RND(40))   # bulkhead light (dead) and a hose box
    m.cy((0.0, -0.5, 3.3), 0.13, 0.13, 0.1, 'steelK', seg=8, rot=(90, 0, 0))
    m.cy((0.0, -0.6, 3.3), 0.1, 0.1, 0.02, 'lampC', seg=8, rot=(90, 0, 0), hull='none')
    m.bx(-0.3, 0.3, -0.7, -0.5, 1.1, 1.7, 'redE', cull='k')
    text_front(m, 'FIRE HOSE', 0.07, -0.703, 0.0, 1.5, 'paper', maxw=0.5)
    make('Fac_Light', m, ao)
    # the name board over the windows: one piece 12 m long, stacked on the westmost of its facade modules
    m = new(pal)
    m.bx(-0.5, 11.5, -0.6, -0.5, 2.85, 3.6, 'tileB', cull='k')
    text_front(m, 'KOLVANE STATION K-7', 0.58, -0.603, 5.5, 2.98, 'paper', maxw=11.0)
    for x in (-0.3, 11.3):
        m.bx(x - 0.05, x + 0.05, -0.64, -0.6, 2.8, 3.65, 'orange')
    make('NameBoard', m, ao)
    # door signs: a board stacked on any wall module beside a door
    for S_, words in SIGNS.items():
        for w in words:
            m = new(pal)
            sign_board(m, w, bg={'S': 'tileB', 'M': 'orangeD', 'L': 'blueP', 'P': 'yel'}[S_], fg='black' if S_ == 'P' else 'paper')
            make('Sign_' + sname(w), m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'panelW', cull='b')
    corner_bands(m, FIRN, 'snowW', z0=4.22)
    make('CornerX', m, ao)
    # ---- station interior (S) and the mess hall (M)
    for S, fn in (('S', st_face), ('M', mess_face)):
        for v in ('A', 'B'):
            m = new(pal); fn(m)
            rnd = RND(60 + ord(S) + ord(v))
            frost_spots(m, rnd, -0.48, 0.48, 2.8 if v == 'A' else 1.6, CS - 0.14, -0.506, 3 if v == 'A' else 7)
            if v == 'B':   # rime along the ceiling line, icicles off it
                m.prism([(-0.5, CS - 0.2), (-0.58, CS - 0.1), (-0.58, CS - 0.04), (-0.5, CS - 0.01)], -0.42, 0.42, ['frost'], hull='noside', skip=(3,))
                icicles(m, rnd, -0.38, 0.38, -0.55, CS - 0.18, 4, 0.35)
            mk(S + '_' + v, m, ao)
        m = new(pal); fn(m); window_in(m, RND(70 + ord(S))); mk(S + '_Window', m, ao)
        m = new(pal); fn(m); heater(m); mk(S + '_Heater', m, ao)
        m = new(pal); m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, CS, 'panelW', cull='b'); corner_trim(m, S); make('Corner' + S, m, ao)
    m = new(pal); st_face(m); notice(m, RND(81)); mk('S_Notice', m, ao)
    m = new(pal); st_face(m); pipes_v(m); mk('S_Pipe', m, ao)
    m = new(pal); st_face(m); ice_breach(m, RND(82)); mk('S_Breach', m, ao, cols=[cb(-0.48, -0.5 - 0.6, 0.0, 0.48, -0.5, 2.6)])
    m = new(pal); mess_face(m); ice_breach(m, RND(83)); mk('M_Breach', m, ao, cols=[cb(-0.48, -0.5 - 0.6, 0.0, 0.48, -0.5, 2.6)])
    m = new(pal); st_face(m)   # station map
    m.bx(-0.45, 0.45, -0.53, -0.5, 1.25, 2.25, 'paper', cull='k')
    for (a, b, c0, c1, c) in ((-0.38, -0.05, 1.35, 1.75, 'panelB'), (0.0, 0.38, 1.35, 1.75, 'panelB'), (-0.38, 0.38, 1.8, 1.9, 'orange'),
                              (-0.12, 0.12, 1.95, 2.15, 'iceM'), (-0.02, 0.02, 1.9, 1.95, 'black')):
        fq(m, a, b, -0.533, c0, c1, c)
    text_front(m, 'YOU ARE HERE', 0.04, -0.536, 0.0, 1.28, 'redE')
    mk('S_Map', m, ao)
    m = new(pal); mess_face(m)   # menu board, a stopped clock
    m.bx(-0.42, 0.42, -0.54, -0.5, 1.4, 2.2, 'black', cull='k')
    for k, w in enumerate(('MON  STEW', 'TUE  PASTA', 'WED  SOUP')):
        text_front(m, w, 0.06, -0.543, 0.0, 2.0 - k * 0.16, 'paper', maxw=0.7)
    m.cy((0.0, -0.5, 2.9), 0.16, 0.16, 0.05, 'paper', seg=12, rot=(90, 0, 0))
    m.bx(-0.008, 0.008, -0.556, -0.552, 2.9, 3.02, 'black', hull='none')
    m.bx(0.0, 0.08, -0.562, -0.558, 2.893, 2.907, 'black', hull='none')
    mk('M_Menu', m, ao)
    # ---- the deep labs: interior (L), the modules' outer shell (seen from the caves), plant hall (P), glacier ice (C)
    for v in ('A', 'B'):
        m = new(pal); lab_face(m); frost_spots(m, RND(90 + ord(v)), -0.48, 0.48, 3.0 if v == 'A' else 1.4, CL - 0.32, -0.506, 3 if v == 'A' else 8)
        if v == 'B':
            m.prism([(-0.5, CL - 0.32), (-0.58, CL - 0.22), (-0.58, CL - 0.15), (-0.5, CL - 0.12)], -0.42, 0.42, ['frost'], hull='noside', skip=(3,))
            icicles(m, RND(93), -0.38, 0.38, -0.55, CL - 0.3, 4, 0.4)
        make('L_' + v, m, ao)
    m = new(pal); lab_face(m)   # a dead wall monitor
    m.bx(-0.42, 0.42, -0.57, -0.5, 1.6, 2.2, 'black', cull='k'); fq(m, -0.38, 0.38, -0.573, 1.64, 2.16, 'scrDead')
    poly(m, [(-0.38, -0.576, 2.16), (-0.2, -0.576, 2.16), (-0.38, -0.576, 1.94)], 'frost', (0, -1, 0))
    make('L_Screen', m, ao)
    m = new(pal); lab_face(m)   # gauge / valve panel
    m.bx(-0.4, 0.4, -0.6, -0.5, 1.1, 2.0, 'steelL', cull='k')
    for k, x in enumerate((-0.22, 0.0, 0.22)):
        m.cy((x, -0.6, 1.75), 0.08, 0.08, 0.02, 'paper', seg=10, rot=(90, 0, 0), hull='none')
        fq(m, x - 0.005, x + 0.005, -0.623, 1.75, 1.81, 'redE')
        m.cy((x, -0.6, 1.3), 0.05, 0.05, 0.06, 'blueP', seg=8, rot=(90, 0, 0))
    make('L_Panel', m, ao)
    m = new(pal); lab_face(m); window_in(m, RND(94), 1.1, 2.6, 0.4); make('L_Window', m, ao)
    m = new(pal); m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, CL, 'panelW', cull='b'); corner_trim(m, 'L'); make('CornerL', m, ao)
    for v in ('A', 'B'):
        m = new(pal); shell_face(m, rnd=RND(100 + ord(v)), v=v); make('Shell_' + v, m, ao)
    m = new(pal); shell_face(m, rnd=RND(104), v='A')
    m.bx(-0.4, 0.4, -0.58, -0.5, 1.2, 2.4, 'steelD', cull='k'); fq(m, -0.34, 0.34, -0.583, 1.26, 2.34, 'glassD')
    frost_spots(m, RND(105), -0.32, 0.32, 1.3, 2.3, -0.586, 5)
    make('Shell_Window', m, ao)
    m = new(pal); shell_face(m, rnd=RND(106), v='B'); g = new(pal); lamp_bracket(m, 3.9, g); make('Shell_Lamp', m, ao); make_glow('Shell_Lamp_LED', g)
    for v in ('A', 'B'):
        m = new(pal); plant_face(m, rnd=RND(110 + ord(v)), v=v); make('P_' + v, m, ao)
    m = new(pal); plant_face(m, rnd=RND(113), v='B'); pipes_v(m, (-0.3, -0.05, 0.22), ('steelL', 'orange', 'blueP'), 5.8); make('P_Pipes', m, ao)
    m = new(pal); plant_face(m, rnd=RND(114), v='A')
    m.bx(-0.44, 0.44, -0.75, -0.5, 0.0, 2.2, 'steelL', cull='kb')
    fq(m, -0.4, 0.4, -0.753, 1.6, 2.1, 'steelD')
    for x in (-0.25, 0.0, 0.25):
        m.cy((x, -0.75, 1.85), 0.06, 0.06, 0.02, 'paper', seg=8, rot=(90, 0, 0), hull='none')
    m.bx(-0.1, 0.1, -0.8, -0.75, 1.0, 1.3, 'black')
    chevrons(m, -0.4, 0.4, -0.753, 0.2, 0.4, 6, ca='yel')
    make('P_Panel', m, ao, cols=[cb(-0.44, -0.75, 0.0, 0.44, -0.5, 2.2)])
    m = new(pal); plant_face(m, rnd=RND(115), v='A'); g = new(pal); lamp_bracket(m, 4.6, g); make('P_Lamp', m, ao); make_glow('P_Lamp_LED', g)
    m = new(pal); m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'steel', cull='b'); corner_bands(m, CAVE, 'iceL', z0=6.1); corner_trim(m, 'P'); make('CornerP', m, ao)
    for v in ('A', 'B', 'C'):
        m = new(pal); cave_face(m, v=v, rnd=RND(120 + ord(v)))
        if v == 'B':   # a vertical meltwater rib
            lump(m, RND(124), 0.1, -0.56, 0.2, 0.12, 9.0, 0.0, 'iceM', n=5, top=1, hull='noside')
        if v == 'C':   # stones frozen in the ice
            for (x, z) in ((-0.25, 1.9), (0.2, 5.1), (-0.1, 8.3)):
                fq(m, x - 0.08, x + 0.07, -0.506, z, z + 0.1, 'steelD')
        make('Cave_' + v, m, ao)
    m = new(pal); cave_face(m, v='B', rnd=RND(125)); g = new(pal); lamp_bracket(m, 3.6, g)
    m.bx(-0.012, 0.012, -0.52, -0.5, 0.4, 3.4, 'black', hull='none', cull='k')
    make('Cave_Lamp', m, ao); make_glow('Cave_Lamp_LED', g)
    m = new(pal); cave_face(m, v='A', rnd=RND(126))   # cable tray on brackets
    m.prism([(-0.5, 2.98), (-0.72, 3.0), (-0.72, 3.06), (-0.5, 3.1)], -0.5, 0.5, ['galv'], hull='noside', skip=(3,))
    for (zz, c) in ((3.09, 'black'), (3.13, 'orange')):
        m.cy((-0.5, -0.62, zz), 0.025, 0.025, 1.0, c, seg=6, rot=(0, 90, 0), caps=False, hull='none')
    m.bx(-0.03, 0.03, -0.72, -0.5, 2.8, 3.0, 'galv', hull='none')
    make('Cave_Cable', m, ao)
    m = new(pal); cave_face(m, v='C', rnd=RND(127))   # level marker sprayed on the ice
    fq(m, -0.4, 0.4, -0.506, 1.8, 2.5, 'orange')
    text_front(m, 'L-2', 0.36, -0.509, 0.0, 1.95, 'black', maxw=0.7)
    make('Cave_Mark', m, ao)
    m = new(pal); m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'iceD', cull='b'); corner_bands(m, CAVE, 'iceL'); make('CornerC', m, ao)


def corner_bands(m, bands, cap, z0=0.0):
    """strata painted round a corner post, a snow / rime cap on top"""
    bands = bands[::2]   # every other band on a post (corners are many in the caves)
    for i, (zb, c, line) in enumerate(bands):
        zt = bands[i + 1][0] if i + 1 < len(bands) else H
        if zt <= z0:
            continue
        a = max(zb, z0)
        for (pl, at, s) in (('y', -0.5, -1), ('y', 0.5, 1), ('x', -0.5, -1), ('x', 0.5, 1)):
            paint(m, pl, at + s * 0.003, s, [(-0.5, a), (0.5, a), (0.5, zt), (-0.5, zt)], c)
    m.bx(-0.5, 0.5, -0.5, 0.5, H - 0.0, H + 0.04, cap, cull='b')


def corner_trim(m, S):
    c = {'S': 'panelB', 'M': 'wood', 'L': 'steelK', 'P': 'steelK'}[S]
    z1 = {'S': 1.0, 'M': 1.1, 'L': 0.12, 'P': 0.3}[S]
    for (pl, at, s) in (('y', -0.5, -1), ('y', 0.5, 1), ('x', -0.5, -1), ('x', 0.5, 1)):
        paint(m, pl, at + s * 0.006, s, [(-0.5, 0.0), (0.5, 0.0), (0.5, z1), (-0.5, z1)], c)
