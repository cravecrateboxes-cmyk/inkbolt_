"""INKBOLT kit-airfield7 structures: the T-wall blast barriers (zone walls), the runway closure barriers, the gate, the
trail's HESCO screens, the hatch, the control tower (zone 1 landmark), the fighter revetment, the hardened aircraft
shelter (zone 2 landmark), the maintenance hangar, the barracks block, the ordnance igloo, the engine test stand and
the tool crib. Conventions: af_base.py."""
import math

from mathutils import Matrix

from af_base import *  # noqa: F401,F403
from af_base import new, make, text, hazard, plate, box_lines, stair_x, stair_y, rail_x, rail_y, window_y, window_x, arch_pts, vault, tyre_stack
from kit_base import shutter_hull


# ================================================================ T-wall blast barriers (zone walls, 3.6 m)
TW_T = 0.3          # panel thickness (the inside face is the cell edge y = -0.5)
TW_COL = [cb(-0.5, -0.5, 0.0, 0.5, -0.5 + TW_T, WALL_H)]


def twall(m, seam=True, cap=True, end=False):
    y0, y1 = -0.5, -0.5 + TW_T
    m.bx(-0.5, 0.5, y0, y1, 0.0, WALL_H - 0.12, 'conc', hull='full' if end else 'noside', cull='b')
    # the chamfered top: a narrower cap course
    m.bx(-0.5, 0.5, y0 + 0.04, y1 - 0.04, WALL_H - 0.12, WALL_H, 'concL', hull='full' if end else 'noside', cull='b')
    # the T foot outboard (and its upper face)
    m.bx(-0.5, 0.5, y1, 0.85, 0.0, 0.42, 'concD', hull='full' if end else 'noside', cull='b')
    if seam:   # the joint to the next panel and the lifting loops on top
        fq(m, 0.47, 0.5, y0 - 0.003, 0.0, WALL_H - 0.12, 'concS')
    if cap:
        for x in (-0.25, 0.25):
            m.bx(x - 0.06, x + 0.06, -0.37, -0.33, WALL_H, WALL_H + 0.12, 'steelD', hull='none', cull='b')
    # weathering: the sand-blown foot of the inside face
    fq(m, -0.5, 0.47, y0 - 0.003, 0.0, 0.22, 'sandD')


def build_twalls(pal, ao):
    m = new(pal); twall(m); make('TWall_A', m, ao, cols=TW_COL)
    m = new(pal); twall(m)
    poly(m, [(-0.3, -0.504, 3.3), (-0.12, -0.504, 3.3), (-0.16, -0.504, 1.2), (-0.26, -0.504, 0.9)], 'concS', (0, -1, 0))
    text(m, '07', 0.15, -0.505, 2.55, 0.32, 'black', font='cond')
    make('TWall_B', m, ao, cols=TW_COL)
    m = new(pal); twall(m)
    text(m, 'AF7', 0.0, -0.505, 1.9, 0.42, 'black', font='cond')
    fq(m, -0.4, 0.4, -0.504, 1.72, 1.78, 'yellow')
    make('TWall_Num', m, ao, cols=TW_COL)
    # the wing crest: a made-up shield with a lightning bolt and a 7
    m = new(pal); twall(m)
    poly(m, [(-0.32, -0.504, 2.9), (0.32, -0.504, 2.9), (0.32, -0.504, 2.1), (0.0, -0.504, 1.7), (-0.32, -0.504, 2.1)], 'blueD', (0, -1, 0))
    poly(m, [(-0.27, -0.508, 2.85), (0.27, -0.508, 2.85), (0.27, -0.508, 2.12), (0.0, -0.508, 1.77), (-0.27, -0.508, 2.12)], 'yellow', (0, -1, 0))
    poly(m, [(-0.05, -0.512, 2.78), (0.14, -0.512, 2.78), (0.02, -0.512, 2.35), (0.13, -0.512, 2.35), (-0.1, -0.512, 1.9), (-0.02, -0.512, 2.25), (-0.13, -0.512, 2.25)], 'redD', (0, -1, 0))
    text(m, '7TH AIR WING', 0.0, -0.505, 1.3, 0.13, 'black', font='cond', maxw=0.9)
    make('TWall_Crest', m, ao, cols=TW_COL)
    # a floodlight on a bracket over the top, aimed into the base
    m = new(pal); twall(m, cap=False)
    m.bx(-0.05, 0.05, -0.36, -0.28, WALL_H, WALL_H + 0.7, 'steelD', cull='b')
    m.bx(-0.04, 0.04, -0.62, -0.33, WALL_H + 0.6, WALL_H + 0.68, 'steelD', cull='')
    m.bx(-0.22, 0.22, -0.78, -0.56, WALL_H + 0.42, WALL_H + 0.66, 'dark', cull='')
    fq(m, -0.18, 0.18, -0.783, WALL_H + 0.46, WALL_H + 0.62, 'lamp')
    m.cy((0.0, -0.535, 1.5), 0.02, 0.02, WALL_H - 1.6, 'black', seg=5, hull='none')
    m.bx(-0.09, 0.09, -0.535, -0.5, 1.2, 1.5, 'steelD', cull='k')
    make('TWall_Light', m, ao, cols=TW_COL)
    # a warning board
    m = new(pal); twall(m)
    m.bx(-0.42, 0.42, -0.53, -0.505, 1.35, 2.25, 'white2', cull='k')
    fq(m, -0.42, 0.42, -0.533, 2.02, 2.25, 'redD')
    text(m, 'RESTRICTED AREA', 0.0, -0.536, 2.07, 0.13, 'white', font='cond', maxw=0.78)
    text(m, 'NO ENTRY WITHOUT', 0.0, -0.536, 1.78, 0.1, 'black', font='cond', maxw=0.76)
    text(m, 'AUTHORISATION', 0.0, -0.536, 1.6, 0.1, 'black', font='cond', maxw=0.76)
    text(m, 'AIRFIELD 7', 0.0, -0.536, 1.42, 0.1, 'redD', font='cond', maxw=0.76)
    make('TWall_Sign', m, ao, cols=TW_COL)
    # concertina wire coils along the top
    m = new(pal); twall(m, cap=False)
    for k in range(3):
        xc = -0.33 + k * 0.33
        pts = [(xc + 0.06 * math.sin(a), -0.35 + 0.22 * math.cos(a), WALL_H + 0.24 + 0.22 * math.sin(a + 1.2)) for a in [i * math.pi / 3 for i in range(7)]]
        for i in range(6):
            m.bm_(pts[i], pts[i + 1], 0.018, 'steel', hull='none')
    m.bx(-0.5, 0.5, -0.36, -0.34, WALL_H, WALL_H + 0.08, 'steelD', hull='none', cull='b')
    make('TWall_Wire', m, ao, cols=TW_COL)
    # the end panel next to a barrier run (full outline, hazard band on its end edge)
    m = new(pal); twall(m, seam=False, end=True)
    hazard(m, -0.5, 0.5, -0.504, 0.25, 0.85, 5)
    make('TWall_End', m, ao, cols=TW_COL)
    # corner pillar: fills its cell (both inside faces lie on the cell edges)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, WALL_H + 0.2, 'concD', cull='b')
    m.bx(-0.56, 0.56, -0.56, 0.56, WALL_H + 0.2, WALL_H + 0.36, 'concL', cull='')
    m.cy((0.0, 0.0, WALL_H + 0.36), 0.1, 0.1, 0.5, 'steelD', seg=6)
    m.cy((0.0, 0.0, WALL_H + 0.86), 0.12, 0.12, 0.14, 'lampR', seg=8)
    make('TWall_Corner', m, ao, cols=[cb(-0.5, -0.5, 0.0, 0.5, 0.5, WALL_H + 0.36)])


# ================================================================ runway closure barriers (wall cells over the runway)
def build_barriers(pal, ao):
    for name, lamp in (('Barrier_A', False), ('Barrier_B', True)):
        m = new(pal)
        m.bx(-0.5, 0.5, -0.5, 0.05, 0.0, BAR_H, 'concL', hull='noside', cull='b')
        m.bx(-0.5, 0.5, 0.05, 0.5, 0.0, 0.3, 'concD', hull='noside', cull='b')
        fq(m, -0.47, 0.47, -0.503, 0.05, 0.12, 'concS')
        # red / white boards on two posts above the block
        for x in (-0.35, 0.35):
            m.bx(x - 0.03, x + 0.03, -0.25, -0.2, BAR_H, BAR_H + 0.42, 'steelD', hull='none', cull='b')
        m.bx(-0.48, 0.48, -0.3, -0.25, BAR_H + 0.12, BAR_H + 0.4, 'white2', cull='')
        for i in range(4):
            if i % 2 == 0:
                x0 = -0.48 + i * 0.24
                fq(m, x0, x0 + 0.24, -0.303, BAR_H + 0.12, BAR_H + 0.4, 'redD')
                bq(m, x0, x0 + 0.24, -0.247, BAR_H + 0.12, BAR_H + 0.4, 'redD')
        hazard(m, -0.5, 0.5, -0.504, 0.55, 0.85, 5)
        if lamp:
            m.cy((0.0, -0.22, BAR_H + 0.4), 0.025, 0.025, 0.12, 'black', seg=5, hull='none')
            m.cy((0.0, -0.22, BAR_H + 0.52), 0.07, 0.07, 0.1, 'lampR', seg=8)
        make(name, m, ao, cols=[cb(-0.5, -0.5, 0.0, 0.5, 0.05, BAR_H)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.55, s * 2.5))
        m.bx(x0, x1, -0.5, 0.5, 0.0, 4.6, 'conc', cull='b')
        for k in range(3):   # red / white bands on the pylons
            z = 0.5 + k * 0.7
            fq(m, x0 + 0.02, x1 - 0.02, -0.503, z, z + 0.35, 'redD')
            bq(m, x0 + 0.02, x1 - 0.02, 0.503, z, z + 0.35, 'redD')
        m.bx(x0 - 0.05, x1 + 0.05, -0.56, 0.56, 4.6, 4.75, 'concL', cull='')
        m.cy((s * 2.0, 0.0, 4.75), 0.12, 0.12, 0.2, 'lampR', seg=8)
    m.bx(-1.55, 1.55, -0.38, 0.38, 3.35, 4.25, 'od', cull='')
    fq(m, -1.5, 1.5, -0.383, 3.38, 3.43, 'yellow')
    bq(m, -1.5, 1.5, 0.383, 3.38, 3.43, 'yellow')
    for face, y in (('y-', -0.386), ('y+', 0.386)):
        text(m, 'AIRFIELD 7', 0.0, y, 3.62, 0.42, 'white', face=face, maxw=2.8)
        text(m, '7TH AIR WING', 0.0, y, 3.47, 0.11, 'sandL', face=face, font='cond', maxw=1.5)
    make('GateFrame', m, ao, cols=[cb(-2.5, -0.5, 0.0, -1.55, 0.5, 4.6), cb(1.55, -0.5, 0.0, 2.5, 0.5, 4.6)])
    m = new(pal)
    Hs = 3.05
    m.bx(-1.5, 1.5, -0.06, 0.06, 0.0, Hs, 'steel', hull='none', cull='')
    for i in range(1, 16):
        z = i * Hs / 16
        fq(m, -1.48, 1.48, -0.063, z - 0.02, z + 0.02, 'steelD')
        bq(m, -1.48, 1.48, 0.063, z - 0.02, z + 0.02, 'steelD')
    hazard(m, -1.48, 1.48, -0.066, 0.0, 0.3, 10)
    hazard(m, -1.48, 1.48, 0.066, 0.0, 0.3, 10, face=1)
    obj = make('GateShutter', m, False)
    shutter_hull(pal, obj)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)


def hesco(m, x0, x1, y0, y1, z0, z1):
    """a sand-filled wire-mesh basket: the geotextile block, the mesh lines on the trail face (+X), sand on top"""
    m.bx(x0, x1, y0, y1, z0, z1, 'canvas', hull='noend', cull='b')
    for i in range(1, 4):
        y = y0 + (y1 - y0) * i / 4
        m.bx(x1 + 0.002, x1 + 0.005, y - 0.012, y + 0.012, z0, z1, 'steelD', hull='none', cull='tbfkl')
    for i in range(1, 4):
        z = z0 + (z1 - z0) * i / 4
        m.bx(x1 + 0.005, x1 + 0.008, y0, y1, z - 0.012, z + 0.012, 'steelD', hull='none', cull='tbfkl')
    uq(m, x0 + 0.04, x1 - 0.04, y0 + 0.02, y1 - 0.02, z1 + 0.004, 'sand')


def build_trail(pal, ao):
    """1 m trail screen along Blender Y, its trail face +X, 2.6 m: two courses of HESCO baskets; variants with a lamp,
    a direction sign, sandbags on top"""
    for name, extra in (('TrailWall', None), ('TrailWall_B', 'lamp'), ('TrailWall_C', 'sign'), ('TrailWall_D', 'bags')):
        m = new(pal)
        hesco(m, -1.0, 0.06, -0.5, 0.5, 0.0, 1.3)
        hesco(m, -0.9, 0.0, -0.5, 0.5, 1.3, TRAIL_H)
        if extra == 'lamp':
            m.bx(0.0, 0.08, -0.06, 0.06, 1.6, 2.5, 'steelD', cull='')
            m.bx(0.012, 0.3, -0.15, 0.15, 2.3, 2.48, 'dark', cull='')
            m.bx(0.1, 0.28, -0.12, 0.12, 2.295, 2.297, 'lamp', hull='none', cull='tfklr')
        elif extra == 'sign':
            m.bx(0.006, 0.04, -0.42, 0.42, 1.5, 2.1, 'black', cull='l')
            text(m, 'HANGARS', 0.043, 0.0, 1.85, 0.17, 'yellow', face='x+', font='cond', maxw=0.72)
            text(m, 'AREA 2', 0.043, 0.0, 1.6, 0.14, 'yellow', face='x+', font='cond', maxw=0.72)
        elif extra == 'bags':
            for k, (y, z) in enumerate(((-0.25, 0.0), (0.25, 0.0), (0.0, 0.16))):
                m.bx(-0.8, -0.1, y - 0.24, y + 0.24, TRAIL_H + z + 0.004, TRAIL_H + z + 0.16, 'khaki' if k % 2 else 'khakiD', bevel=True)
        make(name, m, ao)
    # the exit hatch: a blast hatch in the apron in a hazard border
    m = new(pal)
    m.bx(-1.3, 1.3, -1.3, 1.3, 0.0, 0.06, 'concD', cull='b')
    for (a, b, c, d) in ((-1.25, 1.25, -1.25, -1.0), (-1.25, 1.25, 1.0, 1.25), (-1.25, -1.0, -1.0, 1.0), (1.0, 1.25, -1.0, 1.0)):
        uq(m, a, b, c, d, 0.063, 'yellow')
    for i in range(5):
        x = -1.2 + i * 0.5
        poly(m, [(x, -1.25, 0.066), (x + 0.22, -1.25, 0.066), (x + 0.37, -1.0, 0.066), (x + 0.15, -1.0, 0.066)], 'black', (0, 0, 1))
        poly(m, [(x, 1.0, 0.066), (x + 0.22, 1.0, 0.066), (x + 0.37, 1.25, 0.066), (x + 0.15, 1.25, 0.066)], 'black', (0, 0, 1))
    m.bx(-0.85, 0.85, -0.85, 0.85, 0.06, 0.18, 'od', cull='b')
    for y in (-0.5, 0.5):
        m.bx(-0.8, 0.8, y - 0.04, y + 0.04, 0.18, 0.2, 'steelD', hull='none', cull='b')
    m.cy((0, 0, 0.18), 0.28, 0.28, 0.04, 'yellow', seg=12)
    m.cy((0, 0, 0.22), 0.05, 0.05, 0.1, 'steelD', seg=6)
    make('Hatch', m, ao)


# ================================================================ the control tower (zone 1 landmark) [12, 12]
def build_tower(pal, ao):
    """Footprint x -6..6, y -6..6, the apron (-Y, south) in front, the runway behind (+Y). A one-storey operations
    annex (x -4.2..6) whose roof is the terrace at 3.6 m (parapet rails, the stair top on the north-west landing),
    the steel stair up the west side rising north, the tower shaft on the north-east (x 0.6..5.6, y 0.4..5.4) with
    the cab of slanted glass at 10.2 - 12.8 m, its roof, mast, beacon and the radar."""
    m = new(pal)
    cols = []
    T = TOWER_DECK
    # ---- the annex block and the landing block under the stair top
    m.bx(-4.2, 6.0, -6.0, 6.0, 0.0, T - 0.25, 'stucco', cull='b')
    m.bx(-6.0, -4.2, 3.5, 6.0, 0.0, T - 0.25, 'stucco', cull='b')
    m.bx(-4.25, 6.05, -6.05, 6.05, T - 0.25, T, 'concL', cull='')
    m.bx(-6.05, -4.25, 3.5, 6.05, T - 0.25, T, 'concL', cull='')
    uq(m, -4.15, 0.55, -5.95, 5.95, T + 0.004, 'concD')
    uq(m, 0.55, 5.95, -5.95, 0.35, T + 0.004, 'concD')
    uq(m, -5.95, -4.15, 3.55, 5.95, T + 0.004, 'concD')
    cols.append(cb(-4.2, -6.0, 0.0, 6.0, 6.0, T, True))
    cols.append(cb(-6.0, 3.5, 0.0, -4.2, 6.0, T, True))
    # south front: windows, the ops door with its canopy and sign, a fire hose box
    window_y(m, -3.8, -0.4, -6.0, 1.0, 2.5, every=0.85)
    window_y(m, 2.4, 5.6, -6.0, 1.0, 2.5, every=0.8)
    fq(m, 0.4, 1.8, -6.003, 0.0, 2.3, 'woodD')
    fq(m, 1.08, 1.12, -6.006, 0.0, 2.3, 'dark')
    m.bx(0.0, 2.2, -6.9, -6.0, 2.5, 2.65, 'concL', cull='')
    text(m, 'FLIGHT OPS', 1.1, -6.004, 2.85, 0.42, 'blueD', maxw=4.0)
    m.bx(-1.3, -0.7, -6.15, -6.0, 1.0, 1.7, 'fire', cull='k')
    # west face: windows; east face: windows and AC units; north face: windows toward the runway
    window_x(m, -5.6, -0.4, -4.2, 1.1, 2.5, every=0.9, face=-1)
    window_x(m, -5.6, -1.0, 6.0, 1.1, 2.5, every=0.9, face=1)
    for y in (-4.0, -1.8):
        m.bx(6.0, 6.55, y - 0.4, y + 0.4, 0.4, 1.0, 'concL', cull='l')
        rq(m, 6.553, y - 0.3, y + 0.3, 0.48, 0.92, 'steelD')
    window_y(m, -3.6, 0.0, 6.0, 1.1, 2.5, every=0.9, face=1)
    # ---- the terrace parapet rails (open at the stair top, x -6..-4.2 on the landing's south edge)
    rail_x(cols, m, -4.15, 5.95, -5.9, T)
    rail_y(cols, m, -5.9, 3.5, -4.1, T)
    rail_y(cols, m, -5.9, 0.35, 5.9, T)
    rail_y(cols, m, 3.6, 5.9, -5.9, T)
    rail_x(cols, m, -5.9, 0.55, 5.9, T)
    # the stair up the west side (x -5.9..-4.3), rising north from y -5.5 to the landing at y 3.5
    stair_y(cols, m, -5.9, -4.3, -5.5, 18, z0=0.0, sign=1, tread='steel', stringer='steelD', rail='yellow', rails=(True, False))
    # ---- the tower shaft (x 0.6..5.6, y 0.4..5.4) up to the cab
    SH0, SH1, CAB0, CAB1 = T, 10.2, 10.2, 12.8
    m.bx(0.6, 5.6, 0.4, 5.4, SH0, SH1 - 0.3, 'stucco', cull='b')
    for z in (6.3, 8.3):
        window_y(m, 1.4, 4.8, 0.4, z, z + 1.2, every=0.85)
        window_x(m, 1.2, 4.6, 5.6, z, z + 1.2, every=0.85, face=1)
        window_x(m, 1.2, 4.6, 0.6, z, z + 1.2, every=0.85, face=-1)
        window_y(m, 1.4, 4.8, 5.4, z, z + 1.2, every=0.85, face=1)
    fq(m, 2.4, 3.6, 0.397, T, T + 2.2, 'woodD')
    m.bx(2.2, 3.8, -0.3, 0.4, T + 2.35, T + 2.45, 'concL', cull='')
    for k in range(4):   # a vertical band of ops stencil on the shaft
        fq(m, 0.75 + k * 0.03, 0.77 + k * 0.03, 0.396, SH0 + 0.4, SH1 - 0.4, 'stuccoD') if k == 9 else None
    m.bx(0.4, 5.8, 0.2, 5.6, SH1 - 0.3, SH1, 'concL', cull='')     # the cab floor slab
    # the cab: slanted glass all round (wider at the top), mullions, the roof slab with a deep overhang
    cx, cy, r0, r1 = 3.1, 2.9, 2.6, 3.05
    z0, z1 = CAB0, CAB1
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    lo = [(cx + sx * r0, cy + sy * r0, z0) for sx, sy in corners]
    hi = [(cx + sx * r1, cy + sy * r1, z1) for sx, sy in corners]
    for i in range(4):
        a, b, c, d = lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]
        nrm = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy, 0.0)
        poly(m, [a, b, c, d], 'glassD', nrm)
        for k in range(1, 4):   # mullions
            t = k / 4.0
            p0 = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, z0)
            p1 = (d[0] + (c[0] - d[0]) * t, d[1] + (c[1] - d[1]) * t, z1)
            m.bm_(p0, p1, 0.06, 'dark', hull='none')
        m.bm_(a, d, 0.1, 'dark')
        g0 = (a[0] + (b[0] - a[0]) * 0.15, a[1] + (b[1] - a[1]) * 0.15, z0 + 0.4)
        g1 = (a[0] + (b[0] - a[0]) * 0.2, a[1] + (b[1] - a[1]) * 0.2, z0 + 0.4)
        n2 = (nrm[0] * 1.02, nrm[1] * 1.02, 0.0)
        off = 0.012 / max(0.01, math.hypot(nrm[0], nrm[1]))
        g0 = (g0[0] + nrm[0] * off, g0[1] + nrm[1] * off, g0[2])
        g1 = (g1[0] + nrm[0] * off, g1[1] + nrm[1] * off, g1[2])
        poly(m, [g0, g1, (g1[0], g1[1], g1[2] + 1.4), (g0[0], g0[1], g0[2] + 1.4)], 'glassL', n2)
    # the cab's inside: a console ring, a dark ceiling, so the glass reads as glass
    m.bx(cx - r0 + 0.1, cx + r0 - 0.1, cy - r0 + 0.1, cy + r0 - 0.1, z0, z0 + 0.95, 'dark', hull='none', cull='b')
    m.bx(cx - r1 - 0.4, cx + r1 + 0.4, cy - r1 - 0.4, cy + r1 + 0.4, z1, z1 + 0.35, 'concL', cull='')
    dq(m, cx - r1 + 0.05, cx + r1 - 0.05, cy - r1 + 0.05, cy + r1 - 0.05, z1 - 0.003, 'dark')
    m.bx(cx - 1.6, cx + 1.6, cy - 1.6, cy + 1.6, z1 + 0.35, z1 + 0.7, 'stucco', cull='b')
    text(m, 'AF7 TOWER', cx, cy - r1 - 0.404, z1 + 0.05, 0.24, 'blueD', maxw=4.6)
    # the mast with the beacon, the radar on its pedestal
    m.cy((cx + 0.8, cy + 0.8, z1 + 0.7), 0.07, 0.05, 3.6, 'steelD', seg=6)
    m.cy((cx + 0.8, cy + 0.8, z1 + 4.3), 0.16, 0.16, 0.2, 'lampR', seg=8)
    for k in range(3):
        z = z1 + 1.4 + k * 0.9
        m.bm_((cx + 0.8, cy + 0.8, z), (cx + 0.8 - 0.6, cy + 0.8, z + 0.4), 0.035, 'steelD', hull='none')
    m.cy((cx - 0.9, cy - 0.6, z1 + 0.7), 0.25, 0.2, 0.5, 'steelD', seg=8)
    m.bx(cx - 1.9, cx + 0.1, cy - 0.75, cy - 0.45, z1 + 1.2, z1 + 1.65, 'white2', cull='')
    m.bx(cx - 0.95, cx - 0.85, cy - 0.65, cy - 0.5, z1 + 1.0, z1 + 1.25, 'steelD', hull='none', cull='')
    # ---- on the terrace: AC units, a signal-lamp stand, crates for cover, a wind vane
    m.bx(-3.4, -2.0, -2.0, -0.8, T, T + 0.9, 'concL', cull='b')
    uq(m, -3.3, -2.1, -1.9, -0.9, T + 0.904, 'steelD')
    cols.append(cb(-3.4, -2.0, T, -2.0, -0.8, T + 0.9))
    m.bx(3.0, 4.6, -4.6, -3.4, T, T + 0.95, 'od', cull='b')
    m.bx(3.15, 4.45, -4.45, -3.55, T + 0.95, T + 1.25, 'odD', cull='b')
    cols.append(cb(3.0, -4.6, T, 4.6, -3.4, T + 1.25))
    m.cy((-1.0, -4.6, T), 0.04, 0.04, 1.3, 'steelD', seg=5)
    m.cy((-1.0, -4.6, T + 1.3), 0.14, 0.14, 0.32, 'dark', seg=8)
    vdisc(m, -1.0, -4.744, T + 1.46, 0.1, 'lampG', seg=8)
    make('Landmark_Tower', m, ao, cols=cols)


# ================================================================ fighter revetment [18, 18] (open toward -Y)
REV_IN, REV_OUT, REV_H, REV_TOP = 6.0, 9.0, 3.6, 0.6


def berm_side(m, sign, y0, y1):
    """one side berm: the gabion inner face (vertical, x = +/-6), a walkway top, the earth slope down to x = +/-9"""
    xi, xo = sign * REV_IN, sign * REV_OUT
    xt = sign * (REV_IN + REV_TOP)
    prof = [(xi, 0.0), (xo, 0.0), (xt, REV_H), (xi, REV_H)]
    verts = [(x, y0, z) for (x, z) in prof] + [(x, y1, z) for (x, z) in prof]
    fs = skin(m, (verts, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'sandD')
    gi = m.pal.index('concD')
    for f in fs:   # the inner (gabion) face and the walkway top in concrete grey
        f.normal_update()
        if abs(f.normal.x) > 0.99 and abs(f.calc_center_median().x - xi) < 0.01:
            f.material_index = gi
    # gabion basket lines on the inner face and scrub on the slope
    face = -sign
    for k in range(1, int(abs(y1 - y0) / 1.5) + 1):
        y = y0 + (y1 - y0) * k / (int(abs(y1 - y0) / 1.5) + 1)
        if sign > 0:
            lq(m, xi - 0.003, y - 0.015, y + 0.015, 0.0, REV_H, 'concS')
        else:
            rq(m, xi + 0.003, y - 0.015, y + 0.015, 0.0, REV_H, 'concS')
    for z in (1.2, 2.4):
        if sign > 0:
            lq(m, xi - 0.006, y0, y1, z - 0.015, z + 0.015, 'concS')
        else:
            rq(m, xi + 0.006, y0, y1, z - 0.015, z + 0.015, 'concS')
    del face


def build_revetment(pal, ao):
    m = new(pal)
    cols = []
    # side berms from the front (y -9) to the back berm (y 6), the back berm across x -9..9 at y 6..9
    for s in (-1, 1):
        berm_side(m, s, -9.0, 9.0)
        xi = s * REV_IN
        a, b = sorted((xi, s * 7.8))
        cols.append(cb(a, -9.0, 0.0, b, 9.0, 1.8))
        a, b = sorted((xi, s * (REV_IN + REV_TOP + 0.4)))
        cols.append(cb(a, -9.0, 1.8, b, 9.0, REV_H))
        # the front end of each berm: a concrete end wall with hazard stripes
        a, b = sorted((s * (REV_IN - 0.05), s * REV_OUT))
        m.bx(a, b, -9.05, -8.6, 0.0, REV_H + 0.15, 'conc', cull='b')
        hazard(m, a, b, -9.054, 0.2, 1.0, 6)
        text(m, 'R%d' % (1 if s < 0 else 2), (a + b) / 2, -9.054, 1.5, 0.8, 'black', font='cond', maxw=2.4)
        cols.append(cb(a, -9.0, 0.0, b, -8.6, REV_H + 0.15))
    prof = [(6.0, 0.0), (9.0, 0.0), (6.0 + REV_TOP, REV_H), (6.0, REV_H)]
    verts = [(-REV_IN, y, z) for (y, z) in prof] + [(REV_IN, y, z) for (y, z) in prof]
    fs = skin(m, (verts, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'sandD')
    for f in fs:
        f.normal_update()
        if f.normal.y < -0.99:
            f.material_index = m.pal.index('concD')
    for k in range(1, 8):
        x = -REV_IN + k * 1.5
        fq(m, x - 0.015, x + 0.015, 5.997, 0.0, REV_H, 'concS')
    for z in (1.2, 2.4):
        fq(m, -REV_IN, REV_IN, 5.993, z - 0.015, z + 0.015, 'concS')
    cols.append(cb(-REV_IN, 6.0, 0.0, REV_IN, 7.8, 1.8))
    cols.append(cb(-REV_IN, 6.0, 1.8, REV_IN, 7.0, REV_H))
    # the bay: a painted stand box and lead-in line, a tie-down ring, the bay number, an earthing point, a fire bottle
    box_lines(m, -5.6, 5.6, -8.5, 5.52, 0.12, 0.008, 'yellow')
    uq(m, -0.08, 0.08, -8.38, 5.4, 0.008, 'yellow')
    text(m, 'BAY 7', 0.0, 4.4, 0.012, 0.7, 'yellow', face='up', maxw=3.0)
    m.cy((3.5, 3.0, 0.0), 0.12, 0.12, 0.05, 'steelD', seg=8)
    m.cy((3.5, 3.0, 0.05), 0.04, 0.04, 0.35, 'green', seg=5)
    # scrub tufts on the berm tops
    for (x, y) in ((-6.3, -6.0), (-6.3, -1.0), (-6.3, 3.5), (6.3, -4.5), (6.3, 1.0), (6.3, 4.8), (-3.0, 6.3), (2.5, 6.3)):
        m.cy((x, y, REV_H - 0.02), 0.28, 0.05, 0.4, 'scrub', seg=6)
    make('Revetment', m, ao, cols=cols)


# ================================================================ the hardened aircraft shelter (zone 2 landmark)
HA_AO, HA_BO, HA_AI, HA_BI = 11.5, 9.2, 10.3, 8.0     # the vault's outer / inner half width and height
HA_Y0, HA_Y1 = -13.3, 15.0                            # the vault from the headwall to the back wall
HA_DOOR = 7.2                                         # the door opening height


def xin(z):
    return HA_AI * math.sqrt(max(0.0, 1 - (z / HA_BI) ** 2))


def xout(z):
    return HA_AO * math.sqrt(max(0.0, 1 - (z / HA_BO) ** 2))


def end_wall(m, y0, y1, c, door=None, n=16):
    """a vertical wall under the vault's outer curve (the headwall / back wall) built of strips, with an optional
    rectangular opening (half width, height)"""
    for i in range(n):
        xa, xb = -HA_AO + 2 * HA_AO * i / n, -HA_AO + 2 * HA_AO * (i + 1) / n
        za, zb = xout_z(xa), xout_z(xb)
        zb0 = 0.0
        if door and max(abs(xa), abs(xb)) <= door[0] + 1e-6:
            zb0 = door[1]
        elif door and min(abs(xa), abs(xb)) < door[0] - 1e-6:
            # the strip straddles the jamb: split it there
            xj = math.copysign(door[0], xa + xb)
            for (p, q, lo) in ((xa, xj, door[1] if abs(xa) < door[0] else 0.0), (xj, xb, door[1] if abs(xb) < door[0] else 0.0)):
                strip(m, p, q, y0, y1, lo, xout_z(p), xout_z(q), c)
            continue
        if min(za, zb) > zb0 + 0.01:
            strip(m, xa, xb, y0, y1, zb0, za, zb, c)


def xout_z(x):
    return HA_BO * math.sqrt(max(0.0, 1 - (x / HA_AO) ** 2))


def strip(m, xa, xb, y0, y1, z0, za, zb, c):
    xa, xb = sorted((xa, xb))
    v = [(xa, y0, z0), (xb, y0, z0), (xb, y1, z0), (xa, y1, z0), (xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)]
    skin(m, (v, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), c, hull='noside')


def build_has(pal, ao):
    """Footprint x -14..14, y -15..15, door south (-Y). A barrel vault of camouflage-painted concrete (outer half width
    11.5, height 9.2; inside 10.3 x 8.0) from the headwall (y -13.3) to the back wall, the door opening 20.6 x 7.2 in
    the headwall, the sliding door leaves telescoped into their piers at both sides (in front of the headwall), the
    door track across the opening, the jet-blast exhaust port in the back wall; inside: lamps, the fire main, the
    lead-in line, the shelter number."""
    m = new(pal)
    cols = []
    n = 16
    # ---- the vault in three lengths of disruptive paint (alternate faces sand / grey per length)
    pal_a = ['conc', 'concD', 'sandD', 'conc']
    lens = [(HA_Y0 + 1.2, -3.0), (-3.0, 6.5), (6.5, HA_Y1 - 1.2)]
    for k, (ya, yb) in enumerate(lens):
        fs = vault(m, ya, yb, HA_AO, HA_BO, HA_AI, HA_BI, n, 'conc', c_in='concL')
        for i in range(n):
            f = fs[4 * i]
            f.material_index = m.pal.index(pal_a[(i + k * 3) % 4] if (i + k) % 3 else 'concD')
    # ---- the headwall with the door opening; the back wall with the exhaust port
    end_wall(m, HA_Y0, HA_Y0 + 1.2, 'conc', door=(HA_AI, HA_DOOR))
    end_wall(m, HA_Y1 - 1.2, HA_Y1, 'concD')
    # the headwall's lintel face lettering and the shelter number
    text(m, 'HAS 03', 0.0, HA_Y0 - 0.004, 7.55, 0.7, 'black', font='cond', maxw=6.0)
    hazard(m, -HA_AI, HA_AI, HA_Y0 - 0.004, HA_DOOR - 0.0, HA_DOOR + 0.25, 40)
    # the exhaust port: a dark opening framed in steel with a grille, seen from inside (y = HA_Y1 - 1.2)
    yb = HA_Y1 - 1.2
    fq(m, -2.2, 2.2, yb - 0.004, 2.4, 5.2, 'dark')
    for i in range(9):
        x = -2.2 + i * 0.55
        fq(m, x - 0.03, x + 0.03, yb - 0.008, 2.4, 5.2, 'steelD')
    for z in (2.4, 5.2):
        m.bx(-2.35, 2.35, yb - 0.15, yb, z - 0.08, z + 0.08, 'steelD', cull='k')
    text(m, 'SHELTER 7-03', 0.0, yb - 0.004, 6.0, 0.55, 'black', font='cond', maxw=5.0)
    text(m, 'NO SMOKING', 0.0, yb - 0.004, 1.2, 0.35, 'redD', font='cond', maxw=3.0)
    # ---- the door leaves: three per side telescoped into the piers, the track beam over them
    for s in (-1, 1):
        for k in range(3):
            xa, xb = sorted((s * (HA_AI + 0.1 * k), s * (HA_AI + 3.3 + 0.1 * k)))
            ya = -15.0 + k * 0.55
            m.bx(xa, xb, ya, ya + 0.45, 0.05, HA_DOOR + 0.2, 'steelD' if k != 1 else 'grey', cull='')
            cols.append(cb(xa, ya, 0.0, xb, ya + 0.45, HA_DOOR + 0.2))
            hazard(m, xa, xb, ya - 0.004, 0.05, 0.55, 8)
            for z in (2.4, 4.8):
                fq(m, xa + 0.1, xb - 0.1, ya - 0.004, z - 0.04, z + 0.04, 'dark')
        xa, xb = sorted((s * (HA_AI + 3.5), s * 14.0))
        m.bx(xa, xb, -15.0, HA_Y0, 0.0, HA_DOOR + 0.9, 'conc', cull='b')
        cols.append(cb(xa, -15.0, 0.0, xb, HA_Y0, HA_DOOR + 0.9))
    fq(m, HA_AI + 0.2, HA_AI + 3.2, -15.004, 3.0, 4.6, 'white2')
    text(m, '03', HA_AI + 1.7, -15.008, 3.15, 1.3, 'black', font='cond', maxw=2.6)
    m.bx(-14.05, 14.05, -15.05, HA_Y0, HA_DOOR + 0.9, HA_DOOR + 1.5, 'concD', cull='')
    text(m, 'AIRFIELD 7', 0.0, -15.054, HA_DOOR + 0.98, 0.42, 'white', maxw=6.0)
    # the door tracks across the opening (painted steel strips) and the lead-in line into the shelter
    for y in (-14.75, -14.2, -13.65):
        uq(m, -HA_AI, HA_AI, y - 0.06, y + 0.06, 0.008, 'steelD')
    uq(m, -0.1, 0.1, HA_Y0, HA_Y1 - 2.5, 0.01, 'yellow')
    uq(m, -1.5, 1.5, HA_Y1 - 2.7, HA_Y1 - 2.5, 0.013, 'yellow')
    for (x, y) in ((-5.0, -6.0), (5.0, -6.0), (-5.0, 6.0), (5.0, 6.0)):
        m.cy((x, y, 0.0), 0.16, 0.16, 0.03, 'steelD', seg=8)
    # ---- inside: the fire main along both walls at 3 m, hose boxes, lamps hanging from the vault
    for s in (-1, 1):
        x = s * (xin(3.0) - 0.15)
        cyl_y(m, x, HA_Y0 + 1.2, HA_Y1 - 1.2, 3.0, 0.09, 'fire', seg=6, caps=False)
        for y in (-8.0, 2.0, 11.0):
            xa, xb = sorted((s * (xin(1.6) - 0.02), s * (xin(1.6) - 0.3)))
            m.bx(xa, xb, y - 0.4, y + 0.4, 0.9, 1.8, 'fire', cull='')
    for y in (-8.0, -1.0, 6.0, 12.0):
        for x in (-4.0, 4.0):
            zt = HA_BI * math.sqrt(1 - (x / HA_AI) ** 2)
            m.cy((x, y, 6.2), 0.02, 0.02, zt - 6.2 + 0.05, 'black', seg=4, hull='none')
            m.cy((x, y, 5.9), 0.42, 0.18, 0.3, 'steelD', seg=8)
            m.cy((x, y, 5.894), 0.36, 0.36, 0.004, 'lamp', seg=8, hull='none')
    # ---- collision: the vault sides in two height bands, the lintel, the back wall
    # (each band's box runs from the inner surface at the band's foot to the outer surface at its top: inside the
    # concrete at every height of the band)
    for s in (-1, 1):
        for (z0, z1) in ((0.0, 1.8), (1.8, 3.6), (3.6, 5.2)):
            a, b = sorted((s * xin(z0), s * xout(z1)))
            cols.append(cb(a, HA_Y0 + 1.2, z0, b, HA_Y1 - 1.2, z1))
        for (z0, z1) in ((0.0, 1.8), (1.8, 3.6)):   # the headwall's jambs beside the door
            a, b = sorted((s * HA_AI, s * xout(z1)))
            cols.append(cb(a, HA_Y0, z0, b, HA_Y0 + 1.2, z1))
    cols.append(cb(-xout(HA_DOOR + 1.6), HA_Y0, HA_DOOR, xout(HA_DOOR + 1.6), HA_Y0 + 1.2, HA_DOOR + 1.6))
    for (z0, z1) in ((0.0, 3.6), (3.6, 6.0), (6.0, 8.4)):   # the back wall (its strips run a little under the curve)
        cols.append(cb(-xout(z1 + 0.8), HA_Y1 - 1.2, z0, xout(z1 + 0.8), HA_Y1, z1))
    make('Landmark_HAS', m, ao, cols=cols)


# ================================================================ the maintenance hangar [28, 22] (doors -Y)
MH_W, MH_D, MH_E, MH_R = 14.0, 11.0, 8.0, 10.0      # half width, half depth, eaves, ridge


def build_hangar(pal, ao):
    """Footprint x -14..14, y -11..11. A steel portal-frame hangar in tan corrugated cladding: side walls and the back
    wall, a gable roof on trusses, the door leaves pushed back to both sides of the 18 m opening, the gable over the
    door with the MAINTENANCE lettering; inside: the travelling crane beam with its hoist, lamps, the bay lines, tool
    boards on the back wall."""
    m = new(pal)
    cols = []
    W, D, E, R = MH_W, MH_D, MH_E, MH_R
    t = 0.2
    # walls (closed boxes: seen from inside and out)
    for s in (-1, 1):
        a, b = sorted((s * (W - t), s * W))
        m.bx(a, b, -D, D - t, 0.0, E, 'corr', cull='b')
        cols.append(cb(a, -D, 0.0, b, D, E))
        # cladding ribs outside and inside, a dado band inside
        for k in range(1, 22):
            y = -D + k * 1.0
            (rq if s > 0 else lq)(m, s * W + s * 0.003, y - 0.03, y + 0.03, 0.0, E, 'corrD')
        (lq if s > 0 else rq)(m, s * (W - t) - s * 0.003, -D + 0.2, D - 0.2, 0.0, 1.2, 'od')
    m.bx(-W, W, D - t, D, 0.0, E, 'corr', cull='b')
    cols.append(cb(-W, D - t, 0.0, W, D, E))
    fq(m, -W + t, W - t, D - t - 0.003, 0.0, 1.2, 'od')
    # gables (front over the door and back), as wedge strips under the roof line
    for (y0, y1, c) in ((-D, -D + t, 'corr'), (D - t, D, 'corr')):
        for s in (-1, 1):
            a, b = sorted((0.0, s * W))
            za, zb = (R, E) if s > 0 else (E, R)
            strip(m, a, b, y0, y1, E, za, zb, c)
    # the front header (over the door opening) and the jambs with the door leaves pushed back
    m.bx(-W + t, W - t, -D, -D + t, E - 1.2, E, 'od', cull='')
    text(m, 'MAINTENANCE', 0.0, -D - 0.004, E + 0.25, 0.95, 'odD', maxw=13.0)
    text(m, '7TH AIR WING - HANGAR 2', 0.0, -D - 0.004, E - 0.95, 0.42, 'white', font='cond', maxw=10.0)
    for s in (-1, 1):
        for k in range(2):
            xa, xb = sorted((s * (9.0 + 2.35 * k), s * (11.4 + 2.35 * k)))
            ya = -D + 0.05 + k * 0.32
            m.bx(xa, xb, ya, ya + 0.25, 0.0, E - 1.2, 'corr' if k else 'corrD', cull='b')
            for j in range(1, 5):
                x = xa + (xb - xa) * j / 5
                fq(m, x - 0.03, x + 0.03, ya - 0.004, 0.45, E - 1.2, 'corrD' if k else 'corr')
            hazard(m, xa, xb, ya - 0.006, 0.0, 0.4, 6)
            a, b = sorted((xa, xb))
            cols.append(cb(a, ya, 0.0, b, ya + 0.25, E - 1.2))
    # the roof: two pitched plates (seen from inside and out), the ridge cap, skylight strips
    plate(m, [(-W - 0.3, -D - 0.3, E - 0.05), (-W - 0.3, D + 0.3, E - 0.05), (0.0, D + 0.3, R), (0.0, -D - 0.3, R)], (0, 0, 0.15), 'corrD')
    plate(m, [(0.0, -D - 0.3, R), (0.0, D + 0.3, R), (W + 0.3, D + 0.3, E - 0.05), (W + 0.3, -D - 0.3, E - 0.05)], (0, 0, 0.15), 'corrD')
    m.bx(-0.3, 0.3, -D - 0.35, D + 0.35, R + 0.08, R + 0.3, 'corr', cull='')
    # trusses inside (bottom chord, raked top chords, a king post) every 5.5 m
    for y in (-8.0, -2.5, 3.0, 8.5):
        m.bm_((-W + t, y, E - 0.25), (W - t, y, E - 0.25), 0.14, 'steelD')
        m.bm_((-W + t, y, E - 0.1), (0.0, y, R - 0.15), 0.12, 'steelD')
        m.bm_((0.0, y, R - 0.15), (W - t, y, E - 0.1), 0.11, 'steelD')
        m.bm_((0.0, y, E - 0.25), (0.0, y, R - 0.15), 0.1, 'steelD')
        for s in (-1, 1):
            m.bm_((s * 4.0, y, E - 0.25), (s * 2.0, y, R - 0.15 - (R - E) * (2.0 / W)), 0.08, 'steelD')
    # the travelling crane beam along X with its hoist; lamps
    m.bx(-W + t, W - t, 1.8, 2.3, E - 0.75, E - 0.35, 'yellow', cull='')
    m.bx(2.6, 3.6, 1.6, 2.5, E - 1.2, E - 0.75, 'yellowD', cull='')
    m.cy((3.1, 2.05, 4.2), 0.02, 0.02, E - 1.2 - 4.2, 'black', seg=4, hull='none')
    m.bx(2.9, 3.3, 1.85, 2.25, 3.9, 4.2, 'steelD', cull='')
    for y in (-6.0, 0.0, 6.0):
        for x in (-7.0, 0.0, 7.0):
            m.cy((x, y, E - 1.1), 0.5, 0.2, 0.35, 'steelD', seg=8)
            m.cy((x, y, E - 1.106), 0.42, 0.42, 0.004, 'lamp', seg=8, hull='none')
            m.cy((x, y, E - 0.75), 0.015, 0.015, 0.5, 'black', seg=4, hull='none')
    # bay lines on the floor, the FOD walk line at the door
    box_lines(m, -8.5, 8.5, -6.0, 9.5, 0.12, 0.008, 'yellow', sides='sew')
    uq(m, -W + 0.4, W - 0.4, -D + 1.0, -D + 1.15, 0.008, 'white2')
    text(m, 'FOD CHECK', 0.0, -D + 1.6, 0.011, 0.4, 'white2', face='up', maxw=3.0)
    # tool boards on the back wall (pegboard panels with tool silhouettes)
    for x0 in (-12.5, -3.0):
        fq(m, x0, x0 + 2.4, D - t - 0.004, 1.5, 2.7, 'woodD')
        for k in range(6):
            x = x0 + 0.25 + k * 0.38
            fq(m, x, x + 0.06, D - t - 0.008, 1.8, 2.45, 'black')
    text(m, 'SAFETY FIRST', 6.0, D - t - 0.004, 4.2, 0.5, 'redD', font='cond', maxw=6.0)
    # the roof collision for shots (players never get up there)
    make('Hangar', m, ao, cols=cols)


# ================================================================ the barracks block [26, 10] (gallery front -Y)
def build_barracks(pal, ao):
    """Footprint x -13..13, y -5..5. Two storeys of rendered block (x -11..11, y -1.5..5, 3.2 + 3.0 m, parapet), the
    upper gallery (a concrete slab at 3.2 m, y -4..-1.5, on columns, rails) and a concrete stair at each end rising
    from the back (y 5) to a landing (y -5..-3) at the gallery's height."""
    m = new(pal)
    cols = []
    G = GALLERY
    m.bx(-11.0, 11.0, -1.5, 5.0, 0.0, 6.2, 'stucco', cull='b')
    m.bx(-11.1, 11.1, -1.6, 5.1, 6.2, 6.75, 'stuccoD', cull='')
    uq(m, -10.8, 10.8, -1.3, 4.8, 6.754, 'concS')
    cols.append(cb(-11.0, -1.5, 0.0, 11.0, 5.0, 6.75))
    fq(m, -11.0, 11.0, -1.503, 0.0, 0.45, 'stuccoD')
    # doors and windows, both storeys (rooms 101-105, 201-205); AC units under the windows
    for k in range(5):
        x = -8.8 + k * 4.4
        for (z0, base) in ((0.0, 100), (G, 200)):
            fq(m, x - 1.25, x - 0.35, -1.507, z0, z0 + 2.15, 'woodD')
            fq(m, x - 1.22, x - 0.38, -1.511, z0 + 1.6, z0 + 1.95, 'glassD')
            text(m, str(base + k + 1), x - 0.8, -1.511, z0 + 2.2, 0.16, 'black', font='cond')
            window_y(m, x + 0.2, x + 1.6, -1.5, z0 + 0.95, z0 + 2.1, every=0.7, sill='concL')
            m.bx(x + 0.5, x + 1.3, -1.9, -1.5, z0 + 0.25, z0 + 0.75, 'concL', cull='k')
            fq(m, x + 0.6, x + 1.2, -1.903, z0 + 0.33, z0 + 0.67, 'steelD')
    text(m, 'BARRACKS 4', 0.0, -1.604, 6.28, 0.36, 'blueD', maxw=6.0)
    # back and ends: windows
    for z0 in (0.0, G):
        for k in range(6):
            x = -9.5 + k * 3.8
            window_y(m, x - 0.6, x + 0.6, 5.0, z0 + 1.0, z0 + 2.1, every=0.6, face=1, sill=None)
    # the gallery slab, its columns, the rail along its front (gaps at both ends to the stair landings)
    m.bx(-11.1, 11.1, -5.0, -1.5, G - 0.25, G, 'concL', cull='')
    cols.append(cb(-11.1, -5.0, G - 0.25, 11.1, -1.5, G, True))
    for s in (-1, 1):   # the landings at the stair tops
        xa, xb = sorted((s * 11.1, s * 13.0))
        m.bx(xa, xb, -5.0, -3.0, G - 0.25, G, 'concL', cull='')
        cols.append(cb(xa, -5.0, G - 0.25, xb, -3.0, G, True))
    uq(m, -12.9, 12.9, -4.9, -3.05, G + 0.004, 'conc')
    uq(m, -11.1, 11.1, -3.05, -1.55, G + 0.004, 'conc')
    for x in (-11.0, -6.6, -2.2, 2.2, 6.6, 11.0):
        m.bx(x - 0.18, x + 0.18, -4.0, -3.64, 0.0, G - 0.25, 'concL', cull='b')
        cols.append(cb(x - 0.18, -4.0, 0.0, x + 0.18, -3.64, G - 0.25))
    rail_x(cols, m, -12.95, 12.95, -4.9, G, c='steelD', posts=1.1)
    # the stairs at each end (x -12.9..-11.2 and 11.2..12.9), rising from y 5 toward -Y to the landing (y -5..-3)
    for s in (-1, 1):
        x0, x1 = sorted((s * 11.15, s * 12.95))
        top = stair_y(cols, m, x0, x1, 5.0, 16, z0=0.0, sign=-1, tread='concL', stringer='stuccoD', rail='steelD', rails=(s < 0, s > 0))
        del top
        # the solid stair base under the treads (a masonry stair), and the landing's outer rail
        for i in range(16):
            ya, yb = 5.0 - (i + 1) * 0.5, 5.0 - i * 0.5
            m.bx(x0 + 0.06, x1 - 0.06, ya, yb, 0.0, (i + 1) * RISE - 0.06, 'stuccoD', hull='noend', cull='bt')
        xr = s * 12.97
        rail_y(cols, m, -4.9, -3.0, xr, G, c='steelD')
    text(m, 'NO LOITERING ON GALLERY', 0.0, -4.95, G - 0.22, 0.13, 'black', font='cond', maxw=3.5)
    # roof: a water tank, an AC plant, a mast
    m.cy((-7.0, 2.5, 6.75), 1.0, 1.0, 1.6, 'white2', seg=10)
    m.bx(3.0, 5.0, 1.0, 3.0, 6.75, 7.75, 'concL', cull='b')
    m.cy((8.5, 3.5, 6.75), 0.05, 0.05, 3.0, 'steelD', seg=5)
    make('Barracks', m, ao, cols=cols)


# ================================================================ the ordnance igloo [12, 16] (door -Y)
IG_AO, IG_BO, IG_AI, IG_BI = 6.0, 4.6, 3.4, 3.4
IG_Y0, IG_Y1 = -7.2, 7.0


def build_igloo(pal, ao):
    """Footprint x -6..6, y -8..8: an earth-covered steel arch store; the concrete headwall (x -5.4..5.4, 4.2 m) with
    the door opening (3.2 x 2.8) and the two steel leaves swung open against it; inside: bomb racks along both walls,
    a crate stack, lamps."""
    m = new(pal)
    cols = []
    fs = vault(m, IG_Y0, IG_Y1, IG_AO, IG_BO, IG_AI, IG_BI, 12, 'sandD', c_in='steel')
    del fs
    # the back cap of the mound: a sloped end down to the ground at y 8
    O = arch_pts(IG_AO, IG_BO, 12)
    verts = [(x, IG_Y1, z) for (x, z) in O] + [(x, 8.0, 0.0) for (x, z) in O]
    K = len(O)
    faces = [tuple(range(K))] + [(i, i + 1, K + i + 1, K + i) for i in range(K - 1)] + [(0, K, 2 * K - 1, K - 1)]
    skin(m, (verts, faces), 'sandD')
    # the inner back wall (concrete) closing the arch
    O2 = arch_pts(IG_AI, IG_BI, 12)
    poly(m, [(x, IG_Y1 - 0.004, z) for (x, z) in O2], 'concD', (0, -1, 0))
    # the headwall: a slab with the door opening; the wing walls
    HW0, HW1 = -8.0, IG_Y0
    for (xa, xb) in ((-5.4, -1.6), (1.6, 5.4)):
        m.bx(xa, xb, HW0, HW1, 0.0, 4.2, 'conc', cull='b')
        cols.append(cb(xa, HW0, 0.0, xb, HW1, 4.2))
    m.bx(-1.6, 1.6, HW0, HW1, 2.8, 4.2, 'conc', cull='')
    m.bx(-5.5, 5.5, HW0 - 0.05, HW1, 4.2, 4.4, 'concL', cull='')
    cols.append(cb(-1.6, HW0, 2.8, 1.6, HW1, 4.4))
    text(m, 'IGLOO 7', 0.0, HW0 - 0.004, 3.15, 0.55, 'black', font='cond', maxw=3.0)
    fq(m, -4.9, -2.3, HW0 - 0.004, 2.2, 3.4, 'orange')
    text(m, '1.1', -3.6, HW0 - 0.008, 2.35, 0.75, 'black', font='cond')
    fq(m, 2.3, 4.9, HW0 - 0.004, 2.0, 3.4, 'white2')
    text(m, 'EXPLOSIVES', 3.6, HW0 - 0.008, 3.0, 0.24, 'redD', font='cond', maxw=2.4)
    text(m, 'NO NAKED', 3.6, HW0 - 0.008, 2.6, 0.2, 'black', font='cond', maxw=2.4)
    text(m, 'FLAMES', 3.6, HW0 - 0.008, 2.3, 0.2, 'black', font='cond', maxw=2.4)
    # the door leaves swung open flat against the headwall face
    for s in (-1, 1):
        xa, xb = sorted((s * 1.65, s * 3.25))
        m.bx(xa, xb, HW0 - 0.2, HW0 - 0.03, 0.02, 2.75, 'od', cull='')
        for z in (0.7, 2.0):
            fq(m, xa + 0.08, xb - 0.08, HW0 - 0.203, z - 0.03, z + 0.03, 'odD')
        cols.append(cb(xa, HW0 - 0.2, 0.0, xb, HW0, 2.75))
    # inside: the floor's door threshold, lamps, bomb racks along both walls, a crate stack at the back
    uq(m, -1.6, 1.6, HW0, HW1, 0.02, 'concD')
    uq(m, -3.3, 3.3, HW1, IG_Y1, 0.02, 'concD')   # the store's concrete floor (over the yard's sand paint)
    for y in (-3.0, 2.5):
        m.cy((0.0, y, 2.8), 0.3, 0.12, 0.25, 'steelD', seg=8)
        m.cy((0.0, y, 2.794), 0.25, 0.25, 0.004, 'lamp', seg=8, hull='none')
        m.cy((0.0, y, 3.05), 0.015, 0.015, 0.36, 'black', seg=4, hull='none')
    for s in (-1, 1):
        xa, xb = sorted((s * 1.9, s * 2.85))
        for (ya, yb) in ((-6.4, -2.0), (-1.0, 3.8)):
            for z in (0.15, 0.85):
                m.bx(xa, xb, ya, yb, z, z + 0.06, 'yellowD', cull='')
            for y in (ya + 0.05, yb - 0.11):
                m.bx(xa - 0.03, xa + 0.03, y, y + 0.06, 0.0, 1.35, 'yellowD', cull='b')
                m.bx(xb - 0.03, xb + 0.03, y, y + 0.06, 0.0, 1.35, 'yellowD', cull='b')
            for z in (0.47, 1.17):
                cyl_y(m, (xa + xb) / 2, ya + 0.15, yb - 0.15, z, 0.26, 'od', seg=8, r1=0.26)
                m.cy(((xa + xb) / 2, yb - 0.15, z), 0.26, 0.0, 0.5, 'od', seg=8, rot=(-90, 0, 0))
                ya2 = ya + 0.8
                m.bx((xa + xb) / 2 - 0.27, (xa + xb) / 2 + 0.27, ya2, ya2 + 0.1, z - 0.27, z + 0.27, 'yellow', hull='none', cull='')
            cols.append(cb(xa, ya, 0.0, xb, yb, 1.45))
    for (x, y, z, w) in ((-1.0, 5.6, 0.0, 0.9), (0.0, 5.7, 0.0, 0.9), (-0.5, 5.65, 0.7, 0.8)):
        m.bx(x - w / 2, x + w / 2, y - 0.45, y + 0.45, z, z + 0.7, 'od' if z == 0 else 'khaki', cull='b' if z == 0 else '')
    cols.append(cb(-1.45, 5.2, 0.0, 0.45, 6.15, 1.4))
    # scrub on the mound, a vent stack
    for (x, y) in ((-3.5, -4.0), (2.8, -1.0), (-2.0, 3.0), (3.8, 4.5), (0.5, 6.0)):
        z = IG_BO * math.sqrt(max(0.0, 1 - (x / IG_AO) ** 2)) - 0.12
        m.cy((x, y, z), 0.4, 0.05, 0.45, 'scrub', seg=6)
    m.cy((0.0, 4.0, IG_BO - 0.2), 0.18, 0.18, 1.3, 'steelD', seg=8)
    m.cy((0.0, 4.0, IG_BO + 1.1), 0.28, 0.28, 0.12, 'steelD', seg=8)
    # collision: the arch sides in bands, the back
    def ix(z):
        return IG_AI * math.sqrt(max(0.0, 1 - (z / IG_BI) ** 2))

    def ox(z):
        return IG_AO * math.sqrt(max(0.0, 1 - (z / IG_BO) ** 2))
    for s in (-1, 1):
        for (z0, z1) in ((0.0, 1.8), (1.8, 3.2)):
            a, b = sorted((s * ix(z1), s * ox(z1)))
            cols.append(cb(a, IG_Y0, z0, b, IG_Y1, z1))
    cols.append(cb(-IG_AI, IG_Y1, 0.0, IG_AI, 8.0, 3.2))
    make('Igloo', m, ao, cols=cols)


# ================================================================ the engine test stand [10, 14] (intake -Y)
def build_teststand(pal, ao):
    """Footprint x -5..5, y -7..7: a jet engine on its thrust cradle (intake to the south, bellmouth and screen), the
    exhaust into the blast deflector (an angled steel scoop with side cheeks) at the back, the test cabin with its
    window to the engine on the east side, cable trays, hazard paint on the pad."""
    m = new(pal)
    cols = []
    # pad paint
    box_lines(m, -4.0, 1.4, -6.6, 3.55, 0.15, 0.008, 'yellow')
    text(m, 'JET BLAST', -1.3, -5.8, 0.011, 0.55, 'redD', face='up', maxw=4.0)
    # the cradle: two A-frames and longitudinal beams, a thrust beam on top holding the engine
    ex, ez = -1.3, 1.9
    for y in (-2.4, 1.2):
        for s in (-1, 1):
            m.bm_((ex + s * 1.4, y, 0.0), (ex + s * 0.35, y, ez + 0.7), 0.14, 'yellowD')
        m.bm_((ex - 1.0, y, 0.7), (ex + 1.0, y, 0.7), 0.1, 'yellowD')
    for s in (-1, 1):
        m.bm_((ex + s * 1.4, -2.4, 0.06), (ex + s * 1.4, 1.2, 0.06), 0.12, 'steelD')
    m.bx(ex - 0.45, ex + 0.45, -2.8, 1.6, ez + 0.65, ez + 0.85, 'steelD', cull='')
    # the engine: a long cylinder with fan case, the bellmouth and its screen, the nozzle
    cyl_y(m, ex, -2.6, 1.8, ez, 0.62, 'steel', seg=12)
    cyl_y(m, ex, -3.3, -2.6, ez, 0.72, 'steelD', seg=12, r1=0.66)
    cyl_y(m, ex, -4.0, -3.3, ez, 1.05, 'white2', seg=12, r1=0.74)
    vdisc(m, ex, -4.004, ez, 0.95, 'dark', seg=12)
    for k in range(5):
        a = k * math.pi / 5
        yk = -4.03 - 0.03 * k
        m.bm_((ex - 0.9 * math.cos(a), yk, ez - 0.9 * math.sin(a)), (ex + 0.9 * math.cos(a), yk, ez + 0.9 * math.sin(a)), 0.022, 'steel', hull='none')
    cyl_y(m, ex, 1.8, 3.0, ez, 0.58, 'rust', seg=12, r1=0.46)
    vdisc(m, ex, 3.004, ez, 0.4, 'black', seg=12, face=1)
    for y in (-1.6, -0.2, 1.0):   # dress: pipes and boxes on the case
        m.bx(ex + 0.45, ex + 0.75, y - 0.3, y + 0.3, ez - 0.2, ez + 0.2, 'od', cull='')
    cols.append(cb(ex - 0.6, -3.3, ez - 0.6, ex + 0.6, 3.0, ez + 0.6))
    cols.append(cb(ex - 0.9, -4.0, ez - 0.9, ex + 0.9, -3.3, ez + 0.9))
    for y in (-2.4, 1.2):
        cols.append(cb(ex - 1.3, y - 0.08, 0.0, ex + 1.3, y + 0.08, 1.6))
    # the blast deflector: an angled scoop rising toward +Y, side cheeks
    m.bx(-4.3, 1.7, 3.6, 4.0, 0.0, 0.5, 'concD', cull='b')
    plate(m, [(-3.8, 3.8, 0.4), (1.2, 3.8, 0.4), (1.2, 6.4, 4.2), (-3.8, 6.4, 4.2)], (0, 0.25, -0.18), 'steelD')
    for x in (-4.05, 1.2):
        verts = [(x, 3.7, 0.0), (x, 6.7, 0.0), (x, 6.7, 4.4), (x + 0.25, 3.7, 0.0), (x + 0.25, 6.7, 0.0), (x + 0.25, 6.7, 4.4)]
        skin(m, (verts, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]), 'rust')
    for k in range(4):
        y = 4.2 + k * 0.55
        z = 0.4 + (y - 3.8) / 2.6 * 3.8
        m.bm_((-3.7, y, z + 0.02), (1.1, y, z + 0.02), 0.06, 'rust', hull='none')
    cols.append(cb(-4.3, 3.6, 0.0, 1.7, 6.7, 2.5))
    # the test cabin (x 2.2..4.9, y -6..-1.4), window to the engine (-X), door on the south, AC unit, sign
    m.bx(2.2, 4.9, -6.0, -1.4, 0.0, 2.6, 'corr', cull='b')
    m.bx(2.1, 5.0, -6.1, -1.3, 2.6, 2.8, 'corrD', cull='')
    window_x(m, -5.4, -2.0, 2.2, 1.0, 1.9, every=0.85, face=-1)
    fq(m, 3.0, 3.9, -6.003, 0.0, 2.1, 'odD')
    m.bx(4.9, 5.0, -3.4, -2.4, 1.6, 2.2, 'concL', cull='')
    text(m, 'TEST CELL 2', 3.55, -6.004, 2.2, 0.22, 'black', font='cond', maxw=2.3)
    m.bx(2.6, 4.4, -6.5, -6.0, 0.0, 0.18, 'concD', cull='b')
    cols.append(cb(2.2, -6.0, 0.0, 4.9, -1.4, 2.8))
    # cable trays from the cabin to the cradle, a fuel cart by it
    m.bx(1.4, 2.2, -3.0, -2.7, 0.0, 0.2, 'steelD', cull='b')
    m.bx(-0.2, 1.4, -3.0, -2.7, 0.0, 0.2, 'steelD', cull='b')
    m.bx(2.4, 4.0, -0.4, 1.2, 0.3, 1.4, 'yellow', cull='')
    for (x, y) in ((2.6, -0.2), (3.8, -0.2), (2.6, 1.0), (3.8, 1.0)):
        m.cy((x, y, 0.0), 0.08, 0.08, 0.3, 'steelD', seg=5)
    text(m, 'AVTUR', 3.2, -0.404, 0.75, 0.25, 'black', font='cond', maxw=1.4)
    cols.append(cb(2.4, -0.4, 0.0, 4.0, 1.2, 1.4))
    make('TestStand', m, ao, cols=cols)


# ================================================================ the tool crib [8, 5] (counter -Y)
def build_crib(pal, ao):
    """Footprint x -4..4, y -2.5..2.5: a steel-mesh cage room (posts, frame, bars) with the counter window and its
    half-open shutter in the front, shelving with tool bins inside, the TOOL CRIB sign."""
    m = new(pal)
    cols = []
    H = 2.7
    for (x, y) in ((-3.9, -2.4), (3.9, -2.4), (-3.9, 2.4), (3.9, 2.4)):
        m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, H, 'steelD', cull='b')
    for x in (-1.0, 1.0):
        m.bx(x - 0.05, x + 0.05, -2.47, -2.33, 0.0, H - 0.01, 'steelD', cull='b')
    for (x0, x1, y0, y1) in ((-3.85, 3.85, -2.45, -2.35), (-3.85, 3.85, 2.35, 2.45)):
        m.bx(x0, x1, y0, y1, H - 0.08, H - 0.005, 'steelD', cull='')
        m.bx(x0, x1, y0, y1, 0.0, 0.12, 'steelD', cull='b')
    for x in (-3.95, 3.85):
        m.bx(x, x + 0.1, -2.35, 2.35, H - 0.08, H - 0.005, 'steelD', cull='')
        m.bx(x, x + 0.1, -2.35, 2.35, 0.0, 0.12, 'steelD', cull='b')
    # bars: front (skipping the counter window), both sides
    def bars_x(x0, x1, y, z0=0.12, z1=H - 0.08):
        n = int((x1 - x0) / 0.24)
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            m.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, z0, z1, 'steel', hull='none', cull='tb')
    def bars_y(y0, y1, x):
        n = int((y1 - y0) / 0.24)
        for i in range(1, n):
            y = y0 + (y1 - y0) * i / n
            m.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0.12, H - 0.08, 'steel', hull='none', cull='tb')
    bars_x(-3.9, -1.0, -2.4)
    bars_x(1.0, 3.9, -2.4)
    bars_x(-1.0, 1.0, -2.4, z0=1.95)
    bars_y(-2.4, 2.4, -3.9)
    bars_y(-2.4, 2.4, 3.9)
    for z in (0.9, 1.8):
        m.bx(-3.9, 3.9, -2.42, -2.38, z - 0.02, z + 0.02, 'steelD', hull='none', cull='')
    # the counter and the shutter
    m.bx(-1.1, 1.1, -2.75, -2.05, 1.0, 1.08, 'steelD', cull='')
    m.bx(-0.95, 0.95, -2.3, -2.05, 0.0, 1.0, 'od', cull='b')
    m.bx(-0.95, 0.95, -2.455, -2.345, 1.45, 1.95, 'steel', cull='')
    for k in range(1, 5):
        fq(m, -0.93, 0.93, -2.459, 1.45 + k * 0.1 - 0.01, 1.45 + k * 0.1 + 0.01, 'steelD')
    m.bx(-1.3, 1.3, -2.5, -2.43, H + 0.05, H + 0.5, 'yellow', cull='')
    text(m, 'TOOL CRIB', 0.0, -2.503, H + 0.13, 0.26, 'black', font='cond', maxw=2.4)
    text(m, 'SIGN OUT - SIGN IN', 0.0, -2.754, 1.083, 0.06, 'yellow', face='up', maxw=1.8)
    # shelving inside along the back and the sides, bins in colours
    for (x0, x1, y0, y1) in ((-3.7, 3.7, 1.8, 2.3), (-3.7, -3.2, -1.6, 1.6), (3.2, 3.7, -1.6, 1.6)):
        for z in (0.5, 1.1, 1.7, 2.3):
            m.bx(x0, x1, y0, y1, z - 0.04, z, 'steelD', cull='')
            L = max(x1 - x0, y1 - y0)
            nb = int(L / 0.45)
            for k in range(nb):
                c = ('blue', 'redD', 'yellow', 'green')[(k + int(z * 10)) % 4]
                if x1 - x0 > y1 - y0:
                    xa = x0 + 0.05 + k * 0.45
                    m.bx(xa, xa + 0.36, y0 + 0.05, y1 - 0.05, z, z + 0.24, c, cull='b')
                else:
                    ya = y0 + 0.05 + k * 0.45
                    m.bx(x0 + 0.05, x1 - 0.05, ya, ya + 0.36, z, z + 0.24, c, cull='b')
        for (x, y) in ((x0, y0), (x1, y1)):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 2.35, 'steelD', hull='none', cull='b')
    cols += [cb(-4.0, -2.5, 0.0, 4.0, -2.3, H), cb(-4.0, 2.3, 0.0, 4.0, 2.5, H), cb(-4.0, -2.5, 0.0, -3.8, 2.5, H), cb(3.8, -2.5, 0.0, 4.0, 2.5, H),
             cb(-1.1, -2.75, 0.0, 1.1, -2.3, 1.08)]
    make('ToolCrib', m, ao, cols=cols)


def build_struct(pal, ao):
    build_twalls(pal, ao)
    build_barriers(pal, ao)
    build_gate(pal, ao)
    build_trail(pal, ao)
    build_tower(pal, ao)
    build_revetment(pal, ao)
    build_has(pal, ao)
    build_hangar(pal, ao)
    build_barracks(pal, ao)
    build_igloo(pal, ao)
    build_teststand(pal, ao)
    build_crib(pal, ao)
