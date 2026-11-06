"""INKBOLT asset family: kit-classroom (campaign level 3, a TINY theme).

The player and the trash robots are toy-sized, so the classroom is built at about x6 (brief 5.12): student desks
with 4.45 m tops on steel tube legs (run underneath them), 2.6 m chair seats, 16.6 m walls with giant daylight
windows, a 21 m chalkboard, a floor globe you can walk under and the teacher's desk.

Conventions (ib_lib, fam_kit_toytown): Blender Z-up; a piece's origin is the centre of its cell / footprint at floor
level; Blender -Y is game +Z (south). Wall modules are 1 m wide, decorated on Blender -Y (theme.wall.faceOpen turns
that face toward the room) and stop exactly at their cell edges. Their plaster bodies and rails carry no outline
shell -- a shell on every 1 m module would draw a seam each metre -- so the ink on the walls comes from the decor
(cards, boards, window frames, posters), which is outlined. Big decor (cork board, map, window bays, clock) is one
piece that reaches over its plain neighbours. Collision boxes are <Piece>_COL<n> cube empties (centre, half extents).
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'kit-classroom'
PRE = 'KIT_CLASSROOM_'
ib_lib.GLB[FAM] = 'fps-kit-classroom.glb'
ib_lib.CFG[FAM] = (0.03, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # walls
    ('mint', '#BFE6D3'), ('cream', '#FFF6E3'), ('trim', '#FFFCF4'), ('honey', '#EDBB68'), ('honeyDk', '#CF9150'),
    ('wood3', '#A9713E'), ('steel', '#B4BDC8'), ('steelDk', '#7C8794'),
    # glass and the view outside
    ('glass', '#B4E2FF'), ('glassHi', '#F6FDFF'), ('hedge', '#A6DD8A'), ('tree', '#7CC66B'), ('tree2', '#5DB35E'),
    # boards and paper
    ('board', '#2F6B4F'), ('boardDk', '#245A42'), ('chalk', '#F4F4EA'), ('chalkY', '#FFE9A6'), ('cork', '#D7A266'),
    ('noteY', '#FFF07A'), ('notePk', '#FFA9C9'), ('noteBl', '#A6DBFF'), ('noteGr', '#B6EBA0'), ('lineBl', '#79AEEA'),
    # crayon primaries
    ('crayR', '#EC4B3F'), ('crayB', '#2F7BEA'), ('crayY', '#FFC928'), ('crayG', '#3DBA5C'), ('crayO', '#FF8A3D'),
    ('crayP', '#8A6CD8'), ('navy', '#2F4A8A'), ('pink', '#FF8FB0'),
    # misc props
    ('rubber', '#3B3F4B'), ('terra', '#DA7A4B'), ('leaf', '#3E9C4E'), ('ocean', '#5DB4EE'), ('land', '#8FD068'),
    ('sand', '#F2D58C'), ('pencilWood', '#F6D3A1'), ('felt', '#8A8F9A'), ('ruler', '#F6D88E'), ('tbar', '#E8E3D8'),
    ('lamp', '#FFFFFF'), ('cardboard', '#D6AC74'), ('teal2', '#5CCFC2'), ('paperDk', '#EDE6D6')]

pal = None
HT = 0.02          # baked outline shell (m)
BW = 0.03          # bevel width for props (m)
WH = 16.6          # wall module height; the ceiling (theme env.ceiling.height 16.5) sits just under its top
STATS = {}


# ================================================================ helpers
def tris_of(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def strip_shapes(obj, ids):
    """Remove the outline shell of the given shapes only (plaster bodies, rails, flat paint)."""
    if not ids:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    sl = bm.faces.layers.int.get('shape_id')
    kill = [f for f in bm.faces if f[sl] in ids and all(v[hl].length > 0 for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


class K(Model):
    """Model that remembers which shapes get no outline shell (nh) and the piece's collision boxes."""

    def __init__(self):
        super().__init__(pal)
        self.nh = set()
        self.cols = []
        self.wall = False        # built on wall_base: cull faces nobody can see (see cull_hidden)

    def flat(self):          # the last shape gets no outline
        self.nh.add(self.nshape)

    def col(self, c, h):     # collision box: centre and half extents (Blender axes)
        self.cols.append((tuple(c), tuple(h)))

    def colbox(self, x0, y0, z0, x1, y1, z1):
        self.col(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))

    # axis-aligned box from min/max corners
    def bx(self, x0, y0, z0, x1, y1, z1, color, bevel=False, flat=False, rot=(0, 0, 0)):
        f = self.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), color, rot=rot, bevel=bevel)
        if flat:
            self.flat()
        return f


def cull_hidden(obj, ids):
    """Wall modules: drop faces of the plaster/rail shapes that can never be seen from the room -- faces turned
    into the wall or outside (+Y), tops above the ceiling, bottoms on the floor, the mint/cream seam at 5.5 m."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sl = bm.faces.layers.int.get('shape_id')
    kill = []
    for f in bm.faces:
        if f[sl] not in ids:
            continue
        n, c = f.normal, f.calc_center_median()
        if n.y > 0.99 or (n.z > 0.99 and c.z >= WH - 0.02) or (n.z < -0.99 and c.z <= 0.002) or \
                (abs(n.z) > 0.99 and abs(c.z - 5.5) < 0.001 and c.y > -0.42):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


def finish(name, m, bevel=0.0, hull=HT, ao=False, strip=False):
    full = PRE + name
    obj = build_object(full, m, bevel, hull, ao=ao)
    if strip:
        strip_hull(obj)
    else:
        strip_shapes(obj, m.nh)
    if m.wall:
        cull_hidden(obj, m.nh)
    for i, (c, h) in enumerate(m.cols):
        e = socket('%s_COL%d' % (full, i), obj, c)
        e.scale = h
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
    STATS[full] = tris_of(obj)
    return obj


def rotz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def roty(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def rotx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def disc(m, x, y, z, r, h, color, seg, spin=0.0):
    """Flat polygon on a wall: back cap at y, extruded h toward -Y (the room); first vertex at angle spin
    (degrees from +X toward +Z). No outline."""
    m.parent = T(x, y, z) @ rotx(90) @ rotz(spin)
    m.cyl((0, 0, 0), r, r, h, color, seg=seg, bevel=False)
    m.flat()
    m.parent = Matrix.Identity(4)


# 5 x 5 pixel font (chalk, letter cards, blocks, posters)
FONT = {
    'A': ['.###.', '#...#', '#####', '#...#', '#...#'], 'B': ['####.', '#...#', '####.', '#...#', '####.'],
    'C': ['.####', '#....', '#....', '#....', '.####'], 'D': ['####.', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '####.', '#....', '#####'], 'F': ['#####', '#....', '####.', '#....', '#....'],
    'G': ['.####', '#....', '#..##', '#...#', '.###.'], 'H': ['#...#', '#...#', '#####', '#...#', '#...#'],
    'I': ['#####', '..#..', '..#..', '..#..', '#####'], 'J': ['#####', '...#.', '...#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '###..', '#..#.', '#...#'], 'L': ['#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#'], 'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '.###.'], 'P': ['####.', '#...#', '####.', '#....', '#....'],
    'Q': ['.###.', '#...#', '#.#.#', '#..#.', '.##.#'], 'R': ['####.', '#...#', '####.', '#..#.', '#...#'],
    'S': ['.####', '#....', '.###.', '....#', '####.'], 'T': ['#####', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '.###.'], 'V': ['#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#.#.#', '##.##', '#...#'], 'X': ['#...#', '.#.#.', '..#..', '.#.#.', '#...#'],
    'Y': ['#...#', '.#.#.', '..#..', '..#..', '..#..'], 'Z': ['#####', '...#.', '..#..', '.#...', '#####'],
    '1': ['..#..', '.##..', '..#..', '..#..', '.###.'], '2': ['.###.', '#...#', '..##.', '.#...', '#####'],
    '3': ['####.', '....#', '.###.', '....#', '####.'], '+': ['.....', '..#..', '.###.', '..#..', '.....'],
    '=': ['.....', '#####', '.....', '#####', '.....'],
}


def glyph_rects(ch):
    """Disjoint rectangles (col, row, w, h) covering a 5x5 glyph (greedy merge)."""
    rows = FONT[ch]
    used = [[False] * 5 for _ in range(5)]
    out = []
    for r in range(5):
        for c in range(5):
            if rows[r][c] != '#' or used[r][c]:
                continue
            w = 1
            while c + w < 5 and rows[r][c + w] == '#' and not used[r][c + w]:
                w += 1
            h = 1
            while r + h < 5 and all(rows[r + h][c + k] == '#' and not used[r + h][c + k] for k in range(w)):
                h += 1
            for y in range(h):
                for x in range(w):
                    used[r + y][c + x] = True
            out.append((c, r, w, h))
    return out


def glyph_wall(m, ch, cx, ztop, px, pz, y0, y1, color, flat=True):
    """Glyph on a wall plane (faces -Y): pixel px wide, pz tall, top edge at ztop, spanning y0..y1."""
    for (c, r, w, h) in glyph_rects(ch):
        x0 = cx - 2.5 * px + c * px
        z1 = ztop - r * pz
        m.bx(x0, y0, z1 - h * pz, x0 + w * px, y1, z1, color, flat=flat)


def glyph_top(m, ch, cx, cy, px, z0, z1, color):
    """Glyph lying on a horizontal surface (read from the south: rows run toward -Y)."""
    for (c, r, w, h) in glyph_rects(ch):
        x0 = cx - 2.5 * px + c * px
        ya = cy + 2.5 * px - r * px
        m.bx(x0, ya - h * px, z0, x0 + w * px, ya, z1, color, flat=True)


# ---------------------------------------------------------------- continents (globe + wall map share them)
LAND = [  # lat, lon, radius (deg), kind
    (48, -100, 22, 'land'), (62, -112, 16, 'land'), (66, -150, 9, 'land'), (34, -94, 13, 'land'), (20, -101, 8, 'land'),
    (73, -40, 9, 'white'), (-8, -60, 15, 'land'), (-28, -64, 10, 'land'), (6, -70, 8, 'land'),
    (50, 14, 10, 'land'), (61, 22, 8, 'land'), (8, 18, 15, 'land'), (-12, 26, 12, 'land'), (-26, 24, 8, 'land'),
    (22, 12, 13, 'sand'), (24, 45, 8, 'sand'), (56, 92, 22, 'land'), (45, 62, 14, 'land'), (34, 104, 14, 'land'),
    (22, 79, 8, 'land'), (62, 130, 15, 'land'), (14, 103, 7, 'land'), (-25, 134, 11, 'land'), (-24, 131, 5, 'sand'),
    (42, 75, 7, 'sand')]


def land_at(lat, lon):
    if lat < -68 or lat > 80:
        return 'white'
    v = Vector((math.cos(math.radians(lat)) * math.cos(math.radians(lon)), math.cos(math.radians(lat)) * math.sin(math.radians(lon)), math.sin(math.radians(lat))))
    kind = None
    for (la, lo, rad, k) in LAND:
        w = Vector((math.cos(math.radians(la)) * math.cos(math.radians(lo)), math.cos(math.radians(la)) * math.sin(math.radians(lo)), math.sin(math.radians(la))))
        if v.angle(w) < math.radians(rad):
            if k != 'land':
                return k
            kind = 'land'
    return kind


# ================================================================ walls
def wall_base(m, window_open=False, dado=True):
    """The 1 m plaster module (room side -Y): skirting, mint wainscot, dado rail, cream upper wall, cornice.
    Front face of the body at y -0.42; everything stays inside the cell (x +-0.5, y >= -0.53). No outline."""
    m.wall = True
    m.bx(-0.5, -0.42, 0, 0.5, 0.5, 5.5, 'mint', flat=True)
    if window_open:   # window bays fill z 5.62..13.8 with glass (Win_Bay)
        m.bx(-0.5, -0.42, 5.5, 0.5, 0.5, 5.62, 'honey', flat=True)        # inner sill
        m.bx(-0.5, -0.42, 13.8, 0.5, 0.5, WH, 'cream', flat=True)         # head wall
    else:
        m.bx(-0.5, -0.42, 5.5, 0.5, 0.5, WH, 'cream', flat=True)
    m.bx(-0.5, -0.49, 0, 0.5, -0.42, 0.8, 'honeyDk', flat=True)           # skirting
    m.bx(-0.5, -0.47, 5.12, 0.5, -0.42, 5.2, 'ink', flat=True)            # shadow line under the rail
    if dado and not window_open:
        m.bx(-0.5, -0.497, 5.2, 0.5, -0.42, 5.55, 'honeyDk', flat=True)   # dado rail (front off the cell edge plane)
        m.bx(-0.5, -0.53, 5.55, 0.5, -0.42, 5.63, 'honey', flat=True)     # rail cap
    m.bx(-0.5, -0.45, 15.45, 0.5, -0.42, 15.52, 'ink', flat=True)         # line under the cornice
    m.bx(-0.5, -0.497, 15.52, 0.5, -0.42, 15.68, 'honeyDk', flat=True)    # cornice bead
    m.bx(-0.5, -0.46, 15.68, 0.5, -0.42, WH, 'trim', flat=True)           # frieze


def build_walls():
    m = K()
    wall_base(m)
    finish('Wall_Plain', m)
    # room corner: four ink posts on the cell corners hide the inside-corner seam (only the room-side one shows)
    m = K()
    wall_base(m)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.438 - 0.055, sy * 0.438 - 0.055, 0, sx * 0.438 + 0.055, sy * 0.438 + 0.055, 16.4, 'ink', flat=True)
    finish('Wall_Corner', m)
    # light switch at a toy's-eye 7 m (a real 1.2 m)
    m = K()
    wall_base(m)
    m.bx(-0.21, -0.47, 6.8, 0.21, -0.42, 7.55, 'white')
    m.bx(-0.06, -0.52, 7.08, 0.06, -0.47, 7.3, 'trim', rot=(14, 0, 0))
    for z in (6.9, 7.45):
        m.cyl((0, -0.47, z), 0.025, 0.025, 0.006, 'steelDk', seg=6, rot=(90, 0, 0), bevel=False)
        m.flat()
    finish('Wall_Switch', m)
    # return-air vent high on the wall
    m = K()
    wall_base(m)
    m.bx(-0.46, -0.47, 11.6, 0.46, -0.42, 12.9, 'steel')
    m.bx(-0.38, -0.475, 11.7, 0.38, -0.47, 12.8, 'steelDk', flat=True)
    for i in range(5):
        z = 11.82 + i * 0.22
        m.bx(-0.37, -0.53, z - 0.03, 0.37, -0.476, z + 0.03, "steel", rot=(28, 0, 0), flat=True)
    finish('Wall_Vent', m)
    # window wall without its own glass (a Win_Bay piece on the bay's centre cell glazes the whole 5 m bay)
    m = K()
    wall_base(m, window_open=True)
    finish('Win_Open', m)
    build_window_bays()
    build_alphabet()
    build_cork()
    build_map()
    build_clock()
    build_posters()


def tree_crowns(m, xs, seed):
    """Round tree tops behind the hedge band on the glass (flat discs, three depths so neighbours never coincide)."""
    for i, (x, z, r) in enumerate(xs):
        lv = (i + seed) % 3
        disc(m, x, -0.247 + 0.003 * lv, z, r, 0.011 + 0.0065 * lv, 'tree' if (i + seed) % 2 else 'tree2', 14)


def build_window_bays():
    """5 m window bay (5 wall cells: Win_Open on the outer four): glass, sill, casing, mullions, a view of trees."""
    for v in 'ABC':
        m = K()
        wall_base(m, window_open=True)
        m.bx(-2.5, -0.25, 5.62, 2.5, 0.5, 13.8, 'glass', flat=True)
        m.bx(-2.56, -0.8, 5.16, 2.56, -0.425, 5.62, 'honey')                   # deep sill
        m.bx(-2.62, -0.5, 13.72, 2.62, -0.42, 14.3, 'honeyDk')                 # head casing
        for sx in (-1, 1):
            m.bx(min(sx * 2.44, sx * 2.62), -0.5, 5.62, max(sx * 2.44, sx * 2.62), -0.42, 13.72, 'honeyDk')
        for x in (-1.22, 0.0, 1.22):
            m.bx(x - 0.07, -0.33, 5.62, x + 0.07, -0.254, 13.72, 'honeyDk')     # mullions
        m.bx(-2.44, -0.35, 10.2, 2.44, -0.25, 10.45, 'honeyDk')                # transom
        # latch on the transom
        m.bx(-0.25, -0.4, 10.0, 0.25, -0.35, 10.2, 'steelDk')
        # the view: hedge, tree tops, clouds, glare
        m.bx(-2.44, -0.254, 5.62, 2.44, -0.25, 6.45, 'hedge', flat=True)
        crowns = {'A': [(-1.9, 6.5, 0.55), (-1.0, 6.7, 0.8), (0.3, 6.45, 0.5), (1.4, 6.8, 0.9), (2.1, 6.4, 0.3)],
                  'B': [(-2.0, 6.75, 0.4), (-1.2, 6.5, 0.6), (-0.2, 6.9, 0.95), (1.0, 6.5, 0.55), (1.9, 6.7, 0.5)],
                  'C': [(-1.7, 6.9, 0.75), (-0.6, 6.45, 0.45), (0.6, 6.7, 0.7), (1.8, 6.5, 0.6)]}[v]
        tree_crowns(m, crowns, 'ABC'.index(v))
        clouds = {'A': [(-1.6, 12.3), (1.0, 11.6)], 'B': [(0.6, 12.4)], 'C': [(-0.8, 11.9), (1.7, 12.6)]}[v]
        for (cx, cz) in clouds:
            for k, (dx, dz, r) in enumerate(((-0.32, -0.05, 0.28), (0.0, 0.12, 0.38), (0.34, -0.04, 0.3))):
                disc(m, cx + dx, -0.247 + 0.003 * k, cz + dz, r, 0.007 + 0.0065 * k, 'white', 12)
        for k, (gx, gz, w) in enumerate(((-1.6, 9.1, 0.16), (-1.25, 9.35, 0.07), (0.7, 9.0, 0.12)) if v != 'B' else ((0.9, 9.1, 0.16), (1.25, 9.35, 0.07))):
            m.box((gx, -0.253 - 0.0015 * k, gz), (w, 0.006 + 0.003 * k, 1.5), 'glassHi', rot=(0, -32, 0), bevel=False)
            m.flat()
        # sill things
        if v == 'A':
            plant(m, -1.6, -0.55, 5.62)
            plant(m, 1.7, -0.56, 5.62, tall=True)
        elif v == 'B':
            # two books lying on the sill and a jar of crayons
            m.bx(-1.9, -0.75, 5.62, -0.7, -0.36, 5.8, 'crayB')
            m.bx(-1.8, -0.72, 5.8, -0.85, -0.39, 5.95, 'crayY')
            m.cyl((1.2, -0.55, 5.62), 0.2, 0.2, 0.45, 'glassHi', seg=12)
            for k, c in enumerate(('crayR', 'crayG', 'crayP')):
                m.cyl((1.12 + k * 0.08, -0.55 + (k - 1) * 0.06, 5.9), 0.04, 0.04, 0.42, c, seg=6, rot=((k - 1) * 9, (k - 1) * 7, 0), bevel=False)
        else:
            plant(m, 0.6, -0.55, 5.62)
        finish('Win_Bay_' + v, m, bevel=0.015, ao=False)


def plant(m, x, y, z, tall=False):
    m.cyl((x, y, z), 0.2, 0.27, 0.5, 'terra', seg=8, bevel=False)
    m.cyl((x, y, z + 0.44), 0.29, 0.29, 0.12, 'terra', seg=8, bevel=False)
    leaves = [(0, 0, 0.45, 0, 0.2), (-0.16, 0.0, 0.32, 28, 0.17), (0.17, 0.02, 0.36, -30, 0.18)]
    for (dx, dy, h, tilt, r) in leaves:
        m.sphere((x + dx * 1.6, y + dy, z + 0.62 + h * (1.3 if tall else 1.0)), r, 'leaf', seg=(6, 4), scale=(1.0, 0.7, 2.4 if not tall else 2.9), rot=(0, tilt, 0))


CARD = ['crayR', 'crayB', 'crayY', 'crayG', 'crayO', 'crayP']


def build_alphabet():
    for i, L in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        m = K()
        wall_base(m)
        c = CARD[i % 6]
        m.bx(-0.42, -0.47, 13.75, 0.42, -0.42, 15.15, c)
        ink = 'ink' if c in ('crayY', 'crayO') else 'white'
        glyph_wall(m, L, 0.0, 14.95, 0.12, 0.2, -0.475, -0.468, ink)
        m.bx(-0.06, -0.48, 15.0, 0.06, -0.47, 15.22, 'paperDk', flat=True)   # tape strip
        finish('Alpha_' + L, m)


def build_cork():
    """9 m cork board with pinned work (centred on one cell, reaching over four plain cells each side)."""
    m = K()
    wall_base(m)
    m.bx(-4.4, -0.56, 12.1, 4.4, -0.42, 12.45, 'honeyDk')
    m.bx(-4.4, -0.56, 6.35, 4.4, -0.42, 6.7, 'honeyDk')
    for sx in (-1, 1):
        m.bx(min(sx * 4.05, sx * 4.4), -0.56, 6.7, max(sx * 4.05, sx * 4.4), -0.42, 12.1, 'honeyDk')
    m.bx(-4.05, -0.5, 6.7, 4.05, -0.4235, 12.1, 'cork', flat=True)
    k = [0]

    def L(i):        # decal layer i on a sheet: (front, back), 3.5 mm apart so overlapping decals never coincide
        b = -0.006 - 0.0035 * i
        return b - 0.003, b

    def sheet(cx, cz, w, h, col, ang, lines=0, margin=False, pin='crayR'):
        y = -0.501 - 0.016 * k[0]
        k[0] += 1
        M = T(cx, y, cz) @ roty(ang)
        m.parent = M
        m.bx(-w / 2, -0.006, -h / 2, w / 2, 0, h / 2, col)
        f, b = L(0)
        for i in range(lines):
            z = h / 2 - 0.3 - i * 0.18
            m.bx(-w / 2 + 0.06, f, z - 0.012, w / 2 - 0.06, b, z + 0.012, 'lineBl', flat=True)
        if margin:
            f, b = L(1)
            m.bx(-w / 2 + 0.2, f, -h / 2 + 0.04, -w / 2 + 0.23, b, h / 2 - 0.04, 'crayR', flat=True)
        if pin:
            f, b = L(3)
            m.cyl((0, b, h / 2 - 0.1), 0.055, 0.055, 0.06, pin, seg=8, rot=(90, 0, 0), bevel=False)
        return M

    def sdisc(M, x, z, r, layer, col, seg, spin=0.0):
        f, b = L(layer)
        m.parent = M @ T(x, b, z) @ rotx(90) @ rotz(spin)
        m.cyl((0, 0, 0), r, r, 0.003, col, seg=seg, bevel=False)
        m.flat()
        m.parent = M

    def sbox(M, cx, cz, w, h, layer, col, ang=0.0):
        f, b = L(layer)
        m.parent = M
        m.box((cx, (f + b) / 2, cz), (w, b - f, h), col, rot=(0, ang, 0), bevel=False)
        m.flat()

    # lined writing
    sheet(-3.1, 9.95, 1.15, 1.6, 'paper', 3, lines=7, margin=True)
    # sticky notes
    for (x, z, c, a) in ((-1.75, 11.35, 'noteY', -6), (-1.05, 11.5, 'notePk', 5), (-1.6, 10.6, 'noteBl', 3)):
        sheet(x, z, 0.62, 0.62, c, a, pin=None)
    # a kid's drawing: sun, house with a door and a roof, grass
    M = sheet(0.15, 9.9, 1.6, 1.2, 'paper', -3, pin='crayB')
    sdisc(M, 0.5, 0.3, 0.16, 0, 'crayY', 10)
    sbox(M, -0.225, -0.175, 0.55, 0.45, 0, 'crayR')
    sbox(M, -0.25, -0.3, 0.14, 0.2, 1, 'crayB')
    sbox(M, -0.33, 0.13, 0.42, 0.07, 1, 'crayO', -40)
    sbox(M, -0.12, 0.13, 0.42, 0.07, 2, 'crayO', 40)
    sbox(M, 0.0, -0.5, 1.5, 0.12, 0, 'crayG')
    # A+ test
    M = sheet(1.75, 10.55, 1.05, 1.45, 'paper', 4, lines=5, pin='crayY')
    f, b = L(1)
    glyph_wall(m, 'A', -0.14, 0.62, 0.05, 0.05, f, b, 'crayR')
    glyph_wall(m, '+', 0.2, 0.62, 0.05, 0.05, f, b, 'crayR')
    # star chart
    M = sheet(-2.45, 7.8, 1.6, 1.0, 'noteBl', -2, pin='crayG')
    for r in range(3):
        for c in range(5 - r % 2):
            sdisc(M, -0.56 + c * 0.28 + (r % 2) * 0.14, 0.26 - r * 0.25, 0.075, 0, 'crayY', 5, 90)
    # calendar grid
    M = sheet(0.2, 7.75, 1.7, 1.25, 'paper', 1, pin='crayB')
    sbox(M, 0.0, 0.5, 1.7, 0.24, 0, 'crayR')
    for i in range(1, 4):
        sbox(M, 0.0, 0.38 - i * 0.24, 1.6, 0.02, 1, 'ink')
    for i in range(1, 5):
        sbox(M, -0.85 + i * 0.34, -0.1, 0.02, 0.94, 2, 'ink')
    sdisc(M, 0.0, 0.02, 0.08, 3, 'crayG', 8)
    # weather chart
    M = sheet(2.75, 8.25, 1.15, 1.15, 'noteGr', -4, pin='crayR')
    sdisc(M, 0.0, 0.05, 0.24, 0, 'crayY', 12)
    for i in range(8):
        a = math.radians(i * 45)
        sbox(M, math.sin(a) * 0.36, 0.05 + math.cos(a) * 0.36, 0.05, 0.16, 1, 'crayO', -i * 45)
    m.parent = Matrix.Identity(4)
    # name banner across the top of the board (a ribbon of coloured flags)
    for i in range(14):
        x = -3.6 + i * 0.555
        m.parent = T(x, -0.62, 12.7) @ rotx(90) @ rotz(-90)
        m.cyl((0, 0, 0), 0.2, 0.2, 0.02, CARD[i % 6], seg=3, bevel=False)
    m.parent = Matrix.Identity(4)
    m.bx(-3.9, -0.6, 12.82, 3.9, -0.57, 12.86, 'ink', flat=True)
    finish('Wall_Cork', m)


def build_map():
    """7 m pull-down world map on a roller (same continents as the globe)."""
    m = K()
    wall_base(m)
    m.cyl((-3.35, -0.6, 13.25), 0.16, 0.16, 6.7, 'steelDk', seg=10, rot=(0, 90, 0))
    for sx in (-3.45, 3.35):
        m.cyl((sx, -0.6, 13.25), 0.2, 0.2, 0.1, 'amber', seg=10, rot=(0, 90, 0), bevel=False)
    m.bx(-3.1, -0.49, 8.45, 3.1, -0.47, 13.1, 'paper')
    m.bx(-2.9, -0.494, 8.7, 2.9, -0.49, 12.85, 'ocean', flat=True)
    # raster of land / sand / ice, merged per colour into disjoint rectangles
    NX, NZ = 36, 18
    grid = [[land_at(90 - (j + 0.5) * 180 / NZ, -180 + (i + 0.5) * 360 / NX) for i in range(NX)] for j in range(NZ)]
    used = [[False] * NX for _ in range(NZ)]
    cw, ch = 5.8 / NX, 4.15 / NZ
    for j in range(NZ):
        for i in range(NX):
            k = grid[j][i]
            if not k or used[j][i]:
                continue
            w = 1
            while i + w < NX and grid[j][i + w] == k and not used[j][i + w]:
                w += 1
            h = 1
            while j + h < NZ and all(grid[j + h][i + q] == k and not used[j + h][i + q] for q in range(w)):
                h += 1
            for y in range(h):
                for x in range(w):
                    used[j + y][i + x] = True
            x0 = -2.9 + i * cw
            z1 = 12.85 - j * ch
            m.bx(x0, -0.498, z1 - h * ch, x0 + w * cw, -0.494, z1, k, flat=True)
    m.cyl((-3.15, -0.55, 8.35), 0.1, 0.1, 6.3, 'honeyDk', seg=8, rot=(0, 90, 0))
    m.bx(-0.1, -0.56, 7.7, 0.1, -0.5, 8.3, 'ink')
    m.cyl((0, -0.53, 7.55), 0.17, 0.17, 0.05, 'amber', seg=10, rot=(90, 0, 0), bevel=False)
    finish('Wall_Map', m)


def build_clock():
    m = K()
    wall_base(m)
    cz = 13.1
    m.cyl((0, -0.42, cz), 1.15, 1.15, 0.16, 'crayR', seg=24, rot=(90, 0, 0), bevel=False)
    m.cyl((0, -0.43, cz), 0.98, 0.98, 0.18, 'white', seg=24, rot=(90, 0, 0), bevel=False)
    for i in range(12):
        a = math.radians(i * 30)
        big = i % 3 == 0
        m.box((math.sin(a) * 0.8, -0.613, cz + math.cos(a) * 0.8), (0.07 if big else 0.04, 0.008, 0.2 if big else 0.12), 'ink', rot=(0, -i * 30, 0), bevel=False)
        m.flat()
    # hands at ten past two
    m.parent = T(0, -0.62, cz) @ roty(-70)
    m.bx(-0.045, -0.006, -0.08, 0.045, 0, 0.5, 'ink')
    m.parent = T(0, -0.632, cz) @ roty(-60 * 0 - 12)
    m.bx(-0.03, -0.006, -0.1, 0.03, 0, 0.78, 'ink')
    m.parent = Matrix.Identity(4)
    m.cyl((0, -0.64, cz), 0.07, 0.07, 0.03, 'crayR', seg=8, rot=(90, 0, 0), bevel=False)
    finish('Wall_Clock', m)


def build_posters():
    # A: shapes chart
    m = K()
    wall_base(m)
    m.bx(-1.35, -0.47, 7.2, 1.35, -0.45, 10.6, 'paper')
    m.bx(-1.2, -0.474, 10.05, 1.2, -0.47, 10.45, 'crayP', flat=True)
    m.cyl((-0.6, -0.47, 9.3), 0.42, 0.42, 0.005, 'crayR', seg=16, rot=(90, 0, 0), bevel=False)
    m.flat()
    m.bx(0.22, -0.475, 8.92, 1.0, -0.47, 9.7, 'crayB', flat=True)
    disc(m, -0.6, -0.47, 7.9, 0.5, 0.005, 'crayY', 3, 90)
    disc(m, 0.6, -0.47, 7.95, 0.45, 0.005, 'crayG', 5, 90)
    m.cyl((0, -0.5, 10.5), 0.06, 0.06, 0.04, 'crayR', seg=6, rot=(90, 0, 0), bevel=False)
    finish('Wall_Poster_A', m)
    # B: colour chart (crayon swatches)
    m = K()
    wall_base(m)
    m.bx(-1.35, -0.47, 7.0, 1.35, -0.45, 10.6, 'paper')
    for i, c in enumerate(CARD + ['navy', 'pink']):
        col, row = i % 2, i // 2
        x = -0.6 + col * 1.2
        z = 10.0 - row * 0.78
        m.cyl((x - 0.38, -0.47, z), 0.24, 0.24, 0.005, c, seg=12, rot=(90, 0, 0), bevel=False)
        m.flat()
        m.bx(x - 0.05, -0.474, z - 0.06, x + 0.45, -0.47, z + 0.06, 'paperDk', flat=True)
    m.cyl((0, -0.5, 10.5), 0.06, 0.06, 0.04, 'crayB', seg=6, rot=(90, 0, 0), bevel=False)
    finish('Wall_Poster_B', m)
    # C: counting poster 1 2 3 with dots
    m = K()
    wall_base(m)
    m.bx(-1.4, -0.47, 7.4, 1.4, -0.45, 10.3, 'noteY')
    for i, ch in enumerate('123'):
        x = -0.85 + i * 0.85
        glyph_wall(m, ch, x, 10.0, 0.13, 0.2, -0.475, -0.47, CARD[i * 2])
        for d in range(i + 1):
            m.cyl((x - 0.2 + d * 0.2, -0.47, 8.3), 0.08, 0.08, 0.005, 'ink', seg=8, rot=(90, 0, 0), bevel=False)
            m.flat()
    m.cyl((0, -0.5, 10.2), 0.06, 0.06, 0.04, 'crayG', seg=6, rot=(90, 0, 0), bevel=False)
    finish('Wall_Poster_C', m)


# ================================================================ gate, shutter, trail, hatch, stand, light
def build_gate():
    """Doorway in a 16.6 m wall: casing both faces (the room sees -Y on a north wall and +Y on a south wall),
    wall above the door with the same rails on both faces, jamb liners covering the neighbours' reveals."""
    m = K()
    m.bx(-1.5, -0.42, 3.1, 1.5, 0.42, WH, 'cream', flat=True)
    for s in (-1, 1):   # both faces
        def Y(a, b):
            return (min(s * a, s * b), max(s * a, s * b))
        # stacked rails alternate their back plane (-0.42 / -0.425): touching coplanar faces on a 3 m piece
        # would overlap by float error
        for (z0, z1, fy, by, col) in ((5.12, 5.2, 0.47, 0.42, 'ink'), (5.2, 5.55, 0.5, 0.425, 'honeyDk'), (5.55, 5.63, 0.53, 0.42, 'honey'),
                                      (15.45, 15.52, 0.45, 0.42, 'ink'), (15.52, 15.68, 0.5, 0.425, 'honeyDk'), (15.68, WH, 0.46, 0.42, 'trim')):
            y0, y1 = Y(fy, by)
            m.bx(-1.5, y0, z0, 1.5, y1, z1, col, flat=True)
        # casing: jambs + head, chunky honey wood
        y0, y1 = Y(0.6, 0.42)
        for sx in (-1, 1):
            m.bx(min(sx * 1.488, sx * 1.98), y0, 0, max(sx * 1.488, sx * 1.98), y1, 3.75, 'honeyDk')
        y0, y1 = Y(0.6, 0.425)
        m.bx(-2.06, y0, 3.75, 2.06, y1, 4.2, 'honeyDk')
        # teal gate lights and a green exit plate with an arrow (no text)
        y0, y1 = Y(0.64, 0.6)
        for sx in (-1, 1):
            m.bx(sx * 1.25 - 0.22, y0, 3.86, sx * 1.25 + 0.22, y1, 4.1, 'teal', flat=True)
        y0, y1 = Y(0.5, 0.42)
        m.bx(-0.75, y0, 4.5, 0.75, y1, 5.05, 'crayG')
        ya, yb = Y(0.504, 0.501)
        m.bx(-0.06, ya, 4.56, 0.06, yb, 4.8, 'white', flat=True)
        m.parent = T(0, s * 0.497, 4.86) @ (rotx(90) @ rotz(90) if s < 0 else rotx(-90) @ rotz(-90))
        m.cyl((0, 0, 0), 0.17, 0.17, 0.011, 'white', seg=3, bevel=False)
        m.flat()
        m.parent = Matrix.Identity(4)
    # jamb liners and head soffit (cover the reveal faces of the neighbouring wall modules)
    for sx in (-1, 1):
        m.bx(min(sx * 1.494, sx * 1.6), -0.495, 0, max(sx * 1.494, sx * 1.6), 0.495, 3.1, 'honey', flat=True)
    m.bx(-1.58, -0.415, 3.044, 1.58, 0.415, 3.15, 'honey', flat=True)
    finish('GateFrame', m, bevel=0.0)
    # shutter: wooden rulers as slats (3 m wide, 3.05 m tall); ticks pass through so both faces show them
    m = K()
    H, n = 3.05, 6
    sh = (H - 0.5) / n
    for i in range(n):
        z0 = 0.5 + i * sh
        col = 'ruler' if i % 2 == 0 else 'noteBl'
        m.bx(-1.5, -0.06, z0 + 0.02, 1.5, 0.06, z0 + sh - 0.02, col)
        for t in range(1, 10):
            x = -1.5 + t * 0.3
            long = t % 3 == 0
            m.bx(x - 0.012, -0.065, z0 + sh - 0.05 - (0.18 if long else 0.1), x + 0.012, 0.065, z0 + sh - 0.05, 'ink')
    for k in range(8):
        m.bx(-1.5 + k * 0.375, -0.08, 0, -1.5 + (k + 1) * 0.375, 0.08, 0.5, 'ink' if k % 2 else 'teal')
    finish('GateShutter', m, hull=0.0, strip=True)
    shutter = bpy.data.objects[PRE + 'GateShutter']
    m = K()
    m.bx(-1.5, -0.08, 0, 1.5, 0.08, H, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    STATS[PRE + 'GateShutter'] = tris_of(shutter)


def build_trail():
    """Trail wall: a 1 m slice of a double-sided library bookcase up to the ceiling, exactly the 0.5 m collision slab
    deep (x -0.25..0.25), so it reads from both faces (the hatch room turns some modules round). Books run through
    the thin central divider and show their spines on both sides; shelves are continuous (no outline)."""
    m = K()
    m.bx(-0.25, -0.5, 0, 0.25, 0.5, 0.45, 'honeyDk', flat=True)               # plinth
    levels = [0.45, 3.75, 7.05, 10.35, 13.65]
    for z in levels[1:]:
        m.bx(-0.25, -0.5, z - 0.2, 0.25, 0.5, z, 'honey', flat=True)
        for sx in (-1, 1):
            m.bx(min(sx * 0.2, sx * 0.255), -0.5, z - 0.26, max(sx * 0.2, sx * 0.255), 0.5, z - 0.2, 'ink', flat=True)
    m.bx(-0.25, -0.5, 16.0, 0.25, 0.5, WH, 'honey', flat=True)
    for z0, z1 in zip(levels, [l - 0.2 for l in levels[1:]] + [16.0]):    # central divider, one panel per shelf bay
        m.bx(-0.012, -0.5, z0 + 0.004, 0.012, 0.5, z1 - 0.004, 'wood3', flat=True)
    books = [  # per shelf: (thickness, height, colour, pull-out toward +X)
        [(0.22, 2.3, 'crayR', 0.0), (0.18, 2.6, 'navy', 0.03), (0.26, 2.1, 'crayY', -0.02), (0.16, 2.45, 'crayG', 0.04)],
        [(0.28, 2.0, 'crayB', 0.0), (0.2, 2.5, 'crayO', 0.03), (0.24, 2.2, 'crayP', -0.03), (0.18, 1.8, 'teal2', 0.0)],
        [(0.18, 2.55, 'teal2', 0.02), (0.24, 2.3, 'crayR', 0.0), (0.2, 1.9, 'noteY', -0.03), (0.18, 2.4, 'navy', 0.0)],
        [(0.26, 2.2, 'crayG', 0.0), (0.22, 2.6, 'pink', 0.03), (0.2, 2.0, 'crayB', -0.02), (0.2, 2.35, 'crayO', 0.0)],
        [(0.24, 1.9, 'crayP', 0.0), (0.2, 2.1, 'crayY', 0.03), (0.26, 1.7, 'crayR', -0.02)],
    ]
    for li, row in enumerate(books):
        z = levels[li]
        y = -0.48
        for (t, h, c, out) in row:
            m.bx(-0.21 + out, y, z, 0.21 + out, y + t - 0.012, z + h, c, flat=True)   # no shell: a long run of outlined spines reads as a dark tunnel
            if (li + int(y * 100)) % 2 == 0:
                m.bx(-0.214 + out, y + 0.025, z + h * 0.64, 0.214 + out, y + t - 0.037, z + h * 0.72, 'amber' if c not in ('crayY', 'noteY') else 'ink', flat=True)
            y += t
    finish('TrailWall', m, ao=False)


ROTATED = {90: ['Wall_Plain', 'Win_Open', 'Win_Bay_A', 'Win_Bay_B', 'Win_Bay_C'],
           270: ['Wall_Plain', 'Wall_Cork', 'Wall_Poster_A', 'Wall_Map', 'Wall_Vent']}


def build_rotated():
    """Wall modules pre-turned about the cell centre (<Piece>_R90 / _R270). zones.js counts cells outside the grid
    as wall, so it lays the west and east perimeter runs out like horizontal runs (yaw 0); the theme's chooser
    works out the yaw the engine will use and asks for the turned module that makes the decor face the room."""
    for deg, names in ROTATED.items():
        R = rotz(deg)
        R3 = R.to_3x3()
        for n in names:
            src = bpy.data.objects[PRE + n]
            me = src.data.copy()
            me.transform(R)
            # rails 4 mm higher than on north/south modules: at an inside corner the two walls' rails cross in a
            # 3 cm square and their tops must not coincide
            for v in me.vertices:
                if 0.3 < v.co.z < WH - 0.01:
                    v.co.z += 0.004
            hl = me.attributes.get('_HULL')
            if hl:
                for d in hl.data:
                    d.vector = R3 @ Vector(d.vector)
            obj = bpy.data.objects.new(PRE + n + '_R%d' % deg, me)
            me.name = obj.name
            bpy.context.scene.collection.objects.link(obj)
            STATS[obj.name] = tris_of(obj)


def build_hatch(ao):
    """Exit pad: a floor vent grate with a teal ring and amber bolts."""
    m = K()
    m.cyl((0, 0, 0), 1.3, 1.25, 0.1, 'steelDk', seg=20, bevel=False)
    m.cyl((0, 0, 0.1), 1.0, 1.0, 0.02, 'teal', seg=20, bevel=False)
    m.flat()
    m.cyl((0, 0, 0.12), 0.85, 0.85, 0.01, 'rubber', seg=20, bevel=False)
    m.flat()
    for i in range(5):
        x = -0.6 + i * 0.3
        hw = math.sqrt(max(0.0, 0.85 ** 2 - x * x)) - 0.05
        m.bx(x - 0.06, -hw, 0.13, x + 0.06, hw, 0.17, 'steel')
    for i in range(8):
        a = i / 8 * math.pi * 2
        m.cyl((math.cos(a) * 1.13, math.sin(a) * 1.13, 0.1), 0.06, 0.06, 0.05, 'amber', seg=6, bevel=False)
    finish('Hatch', m, bevel=0.015, ao=ao)


def build_eraser(ao):
    """Weapon stand / cover: a jumbo pink eraser with a cardboard sleeve."""
    m = K()
    m.bx(-0.47, -0.34, 0, 0.47, 0.34, 0.86, 'pink', bevel=True)
    m.bx(-0.16, -0.353, 0.004, 0.3, 0.353, 0.866, 'crayB')
    m.bx(-0.1, -0.357, 0.36, 0.24, -0.353, 0.5, 'white', flat=True)
    m.bx(-0.1, 0.353, 0.36, 0.24, 0.357, 0.5, 'white', flat=True)
    m.colbox(-0.47, -0.34, 0, 0.47, 0.34, 0.86)
    finish('Eraser', m, bevel=0.05, ao=ao)


def build_light():
    """Ceiling light (theme env.ceiling.light, origin on the ceiling plane): a 4 x 4 m louvred troffer and the
    T-bar grid of its 12 x 12 m ceiling cell: lines at -5.5, -1.5, +2.5 (cell centres of the 1 m zone grid, so a
    strip never lands on a wall module's face); the troffer fills the tile between -1.5 and +2.5."""
    m = K()
    o = 0.5
    m.bx(o - 2.0, o - 2.0, -0.3, o + 2.0, o + 2.0, -0.008, 'trim')
    m.bx(o - 1.78, o - 1.78, -0.36, o + 1.78, o + 1.78, -0.25, 'lamp', flat=True)
    for i in (-1, 0, 1):
        m.bx(o - 1.74, o + i * 0.89 - 0.03, -0.44, o + 1.74, o + i * 0.89 + 0.03, -0.3, 'trim', flat=True)
        m.bx(o + i * 0.89 - 0.03, o - 1.74, -0.435, o + i * 0.89 + 0.03, o + 1.74, -0.305, 'trim', flat=True)
    for v in (-5.5, -1.5, 2.5):
        m.bx(-5.996, v - 0.04, -0.034, 5.996, v + 0.04, -0.004, 'tbar', flat=True)
        m.bx(v - 0.04, -5.996, -0.03, v + 0.04, 5.996, -0.012, 'tbar', flat=True)
    finish('LightPanel', m, ao=False)


# ================================================================ furniture
def desk(m, items):
    """Student desk, north part of a DeskSet (y -0.4 .. 3.4), top at 4.45 m on steel tube legs."""
    m.bx(-2.9, -0.4, 4.15, 2.9, 3.4, 4.45, 'honey', bevel=True)
    for x in (-2.55, 2.55):
        for y in (-0.1, 3.1):
            m.cyl((x, y, 0.12), 0.16, 0.16, 4.03, 'steel', seg=6, bevel=False)
            m.cyl((x, y, 0), 0.2, 0.18, 0.12, 'rubber', seg=6, bevel=False)
            m.col((x, y, 2.15), (0.18, 0.18, 2.15))
    for y in (-0.1, 3.1):
        m.bx(-2.55, y - 0.06, 3.95, 2.55, y + 0.06, 4.145, 'steel', flat=True)
    for x in (-2.55, 2.55):
        m.bx(x - 0.055, -0.1, 3.96, x + 0.055, 3.1, 4.14, 'steel', flat=True)
    # book box under the top, open toward the student (-Y)
    m.bx(-2.3, 0.15, 3.3, 2.3, 2.95, 3.38, 'steel')
    m.bx(-2.3, 2.87, 3.38, 2.3, 2.95, 4.15, 'steel')
    for sx in (-1, 1):
        m.bx(min(sx * 2.22, sx * 2.3), 0.15, 3.38, max(sx * 2.22, sx * 2.3), 2.87, 4.15, 'steel')
    m.bx(-1.9, 0.9, 3.38, -0.3, 2.3, 3.58, 'crayB')
    m.bx(-1.75, 1.0, 3.58, -0.45, 2.2, 3.72, 'crayG')
    m.bx(0.2, -0.25, 3.38, 1.4, 1.55, 3.4, 'paper', flat=True)   # homework sheet poking out
    m.bx(0.4, 0.95, 3.4, 1.9, 2.4, 3.62, 'crayR')
    # foot bar on the front legs (jumpable)
    m.bx(-2.55, 3.04, 0.45, 2.55, 3.16, 0.6, 'steel')
    m.colbox(-2.6, 3.0, 0, 2.6, 3.2, 0.6)
    m.colbox(-2.9, -0.4, 4.15, 2.9, 3.4, 4.45)
    m.colbox(-2.3, 0.15, 3.3, 2.3, 2.95, 4.15)
    z = 4.45
    if 'cup' in items:      # pencil cup with pencils
        m.cyl((1.6, 2.4, z), 0.34, 0.36, 0.85, 'crayB', seg=10)
        for k, (dx, dy, a, b, c) in enumerate(((-0.1, 0.05, 8, 0, 'crayY'), (0.1, -0.08, -6, 10, 'crayR'), (0.0, 0.12, 0, -9, 'crayG'))):
            m.cyl((1.6 + dx, 2.4 + dy, z + 0.3), 0.07, 0.07, 1.25, c, seg=6, rot=(a, b, 0), bevel=False)
    if 'books' in items:
        m.bx(-2.4, 1.6, z, -0.6, 2.95, z + 0.26, 'crayP')
        m.bx(-2.3, 1.7, z + 0.26, -0.75, 2.85, z + 0.5, 'crayO')
    if 'crayons' in items:  # upright crayon box with tips
        m.bx(-1.9, 2.3, z, -0.9, 2.75, z + 1.05, 'crayY')
        m.bx(-1.904, 2.296, z + 0.35, -0.896, 2.754, z + 0.6, 'crayG')
        for k, c in enumerate(('crayR', 'crayB', 'crayG', 'crayO', 'crayP')):
            m.cyl((-1.8 + k * 0.2, 2.52, z + 1.05), 0.07, 0.07, 0.18, c, seg=6, bevel=False)
            m.cyl((-1.8 + k * 0.2, 2.52, z + 1.23), 0.07, 0.01, 0.14, c, seg=6, bevel=False)
    if 'bottle' in items:
        m.cyl((2.0, 1.2, z), 0.3, 0.3, 1.3, 'teal2', seg=10)
        m.cyl((2.0, 1.2, z + 1.3), 0.2, 0.2, 0.25, 'crayB', seg=10)
    if 'lunch' in items:
        m.bx(-2.3, 1.4, z, -0.8, 2.6, z + 0.8, 'crayR', bevel=True)
        m.bx(-1.85, 1.95, z + 0.8, -1.25, 2.05, z + 1.05, 'rubber')
    if 'ruler' in items:
        m.bx(-1.0, 0.0, z, 1.8, 0.28, z + 0.04, 'ruler')


def chair(m, M):
    """School chair: wooden seat at 2.6 m, steel legs; backrest on -Y. M places it."""
    m.parent = M
    m.bx(-1.25, -1.15, 2.45, 1.25, 1.15, 2.62, 'honey', bevel=True)
    for x in (-1.05, 1.05):
        m.cyl((x, 0.95, 0), 0.12, 0.12, 2.45, 'steel', seg=6, bevel=False)
        m.cyl((x, -0.95, 0), 0.12, 0.12, 4.85, 'steel', seg=6, bevel=False)
        m.bx(x - 0.045, -0.95, 0.85, x + 0.045, 0.95, 0.97, 'steel')
    m.bx(-1.2, -1.12, 3.7, 1.2, -0.98, 4.75, 'honey')
    m.parent = Matrix.Identity(4)


def chair_cols(m, cx, cy, yaw):
    """Collision for an upright chair at (cx, cy) turned by yaw (deg, multiples of 90 keep it exact)."""
    R = rotz(yaw)
    for (x, y, h) in ((-1.05, 0.95, 2.45), (1.05, 0.95, 2.45), (-1.05, -0.95, 4.85), (1.05, -0.95, 4.85)):
        p = R @ Vector((x, y, 0))
        m.col((cx + p.x, cy + p.y, h / 2), (0.14, 0.14, h / 2))
    hx, hy = (1.25, 1.15) if yaw % 180 == 0 else (1.15, 1.25)
    m.col((cx, cy, 2.535), (hx, hy, 0.085))


def fallen_chair_M(cx, cy):
    return T(cx, cy, 0) @ rotz(90) @ T(0, 0, 1.17) @ rotx(90)


def build_desks(ao):
    sets = {'A': ('up', ('cup', 'books')), 'B': ('turned', ('crayons', 'ruler')),
            'C': ('fallen', ('bottle',)), 'D': ('none', ('lunch',))}
    for v, (ch, items) in sets.items():
        m = K()
        desk(m, items)
        if ch == 'up':
            chair(m, T(0, -1.95, 0))
            chair_cols(m, 0, -1.95, 0)
        elif ch == 'turned':
            chair(m, T(0.35, -2.05, 0) @ rotz(90))
            chair_cols(m, 0.35, -2.05, 90)
        elif ch == 'fallen':
            chair(m, fallen_chair_M(-2.5, -2.0))
            m.colbox(-0.06, -3.25, 0, 0.13, -0.75, 2.33)       # the seat, now a 2.3 m wall
            m.colbox(1.2, -3.2, 0, 2.25, -0.8, 0.2)            # backrest flat on the floor (step on it)
        else:
            for i, (L, W, Tk, c, a) in enumerate(((1.75, 1.3, 0.3, 'crayO', 4), (1.6, 1.2, 0.26, 'navy', -6), (1.5, 1.12, 0.24, 'crayY', 9))):
                book_lying(m, L, W, Tk, c, T(0.4, -2.0, (0, 0.3, 0.56)[i]) @ rotz(a + 90 * (i % 2)))
            m.colbox(-0.5, -2.9, 0, 1.3, -1.1, 0.8)
        finish('DeskSet_' + v, m, bevel=BW, ao=ao)


def build_chairs(ao):
    m = K()
    chair(m, Matrix.Identity(4))
    chair_cols(m, 0, 0, 0)
    finish('Chair', m, bevel=BW, ao=ao)
    m = K()
    chair(m, fallen_chair_M(-2.5, 0))           # lies along X (x -2.4..2.4): seat stands up as a 2.3 m wall
    m.colbox(-0.06, -1.25, 0, 0.13, 1.25, 2.33)
    m.colbox(1.2, -1.2, 0, 2.25, 1.2, 0.2)
    finish('Chair_Fallen', m, bevel=BW, ao=ao)


def backpack(m, M, body, accent, scale=1.0):
    m.parent = M @ Matrix.Diagonal((scale, scale, scale, 1.0))
    m.bx(-1.05, -0.6, 0, 1.05, 0.6, 2.55, body, bevel=True)
    m.bx(-0.8, -0.85, 0.25, 0.8, -0.6, 1.45, accent, bevel=True)              # front pocket
    m.bx(-0.7, -0.865, 1.38, 0.7, -0.845, 1.42, 'ink', flat=True)             # pocket zip
    m.bx(-0.98, -0.615, 2.3, 0.98, -0.6, 2.34, 'ink', flat=True)              # main zip
    m.bx(0.4, -0.895, 1.12, 0.5, -0.855, 1.36, 'steelDk')
    m.beam((-0.35, 0, 2.55), (-0.25, 0, 2.95), 0.1, 'rubber')                  # top handle
    m.beam((0.25, 0, 2.95), (0.35, 0, 2.55), 0.1, 'rubber')
    m.beam((-0.25, 0, 2.95), (0.25, 0, 2.95), 0.12, 'rubber')
    for sx in (-0.55, 0.55):                                                  # shoulder straps on the back
        m.bx(sx - 0.17, 0.6, 0.4, sx + 0.17, 0.75, 2.3, accent)
    m.cyl((1.05, -0.2, 0.2), 0.28, 0.28, 0.9, 'teal2', seg=10, rot=(0, 0, 0))  # bottle in the side pocket
    m.bx(1.0, -0.5, 0.15, 1.12, 0.1, 0.8, accent)
    m.bx(-0.5, -0.625, 1.75, -0.1, -0.6, 2.05, 'white', flat=True)           # name tag
    m.parent = Matrix.Identity(4)


def build_backpacks(ao):
    for v, (b, a) in (('A', ('crayR', 'navy')), ('B', ('crayB', 'crayY'))):
        m = K()
        backpack(m, rotz(0), b, a)
        m.colbox(-1.1, -0.9, 0, 1.4, 0.8, 2.6)
        finish('Backpack_' + v, m, bevel=0.08, ao=ao)


def book_lying(m, L, W, Tk, col, M):
    """Hardcover lying flat: boards + spine in colour, a recessed paper page block. Spine on -X."""
    m.parent = M
    b = 0.04
    m.bx(-L / 2, -W / 2, Tk - b, L / 2, W / 2, Tk, col)
    m.bx(-L / 2, -W / 2, 0, L / 2, W / 2, b, col)
    m.bx(-L / 2, -W / 2, b, -L / 2 + 0.07, W / 2, Tk - b, col)
    m.bx(-L / 2 + 0.07, -W / 2 + 0.025, b, L / 2 - 0.025, W / 2 - 0.025, Tk - b, 'paper', flat=True)
    m.parent = Matrix.Identity(4)


def build_books(ao):
    # '=' run: books standing upright on the floor, spines out on both sides
    rows = {'BooksA': [(0.2, 1.42, 'crayR'), (0.16, 1.25, 'navy'), (0.24, 1.55, 'crayY'), (0.14, 1.3, 'crayG'), (0.18, 1.48, 'crayP')],
            'BooksB': [(0.22, 1.5, 'crayB'), (0.18, 1.36, 'crayO'), (0.2, 1.58, 'teal2'), (0.16, 1.28, 'pink'), (0.16, 1.44, 'crayR')]}
    for name, books in rows.items():
        m = K()
        x = -0.48
        for (t, h, c) in books:
            m.bx(x, -0.45, 0, x + t - 0.012, 0.45, h, c)
            for s in (-1, 1):
                m.bx(x + 0.025, min(s * 0.45, s * 0.454), h * 0.66, x + t - 0.037, max(s * 0.45, s * 0.454), h * 0.74, 'amber' if c not in ('crayY',) else 'ink', flat=True)
            x += t
        m.colbox(-0.5, -0.46, 0, 0.5, 0.46, 1.3)
        finish(name, m, bevel=0.0, ao=ao)
    # stacks of textbooks lying on the floor (2x2 cells)
    stacks = {'BookStack_A': [(1.75, 1.3, 0.26, 'crayB', 3), (1.6, 1.2, 0.22, 'crayR', -5), (1.7, 1.25, 0.3, 'crayY', 8)],
              'BookStack_B': [(1.8, 1.32, 0.28, 'crayG', -4), (1.7, 1.26, 0.24, 'navy', 6), (1.6, 1.2, 0.26, 'crayO', -2), (1.5, 1.1, 0.22, 'pink', 10), (1.65, 1.2, 0.28, 'crayP', -7)],
              'BookStack_C': [(1.78, 1.3, 0.3, 'crayP', 6), (1.72, 1.28, 0.26, 'crayY', -3), (1.62, 1.16, 0.24, 'crayB', 4), (1.55, 1.1, 0.28, 'crayR', -9)]}
    for name, books in stacks.items():
        m = K()
        z = 0.0
        for i, (L, W, Tk, c, a) in enumerate(books):
            book_lying(m, L, W, Tk, c, T(0.03 * (i % 2) - 0.015, 0.02 * ((i + 1) % 2), z) @ rotz(a + (180 if i % 2 else 0)))
            z += Tk
        m.colbox(-0.92, -0.85, 0, 0.92, 0.85, z)
        finish(name, m, bevel=0.0, ao=ao)


def build_blocks(ao):
    """Foam alphabet blocks (1 m): bevelled cube, raised letter on two faces, a shape on the other two."""
    for name, (col, ch, ink) in (('Block_R', ('crayR', 'A', 'white')), ('Block_B', ('crayB', 'B', 'white')),
                                  ('Block_Y', ('crayY', 'C', 'crayR')), ('Block_G', ('crayG', 'D', 'white')),
                                  ('Block_S', ('crayO', 'E', 'navy'))):
        m = K()
        m.bx(-0.48, -0.48, 0, 0.48, 0.48, 0.96, col, bevel=True)
        for s in (-1, 1):
            m.parent = rotz(0 if s < 0 else 180)
            glyph_wall(m, ch, 0, 0.83, 0.13, 0.13, -0.486, -0.478, ink)
            m.parent = rotz(90 if s < 0 else 270)
            m.cyl((0, -0.478, 0.48), 0.27, 0.27, 0.008, ink, seg=5 if s < 0 else 10, rot=(90, 0, 0), bevel=False)
            m.flat()
        m.parent = Matrix.Identity(4)
        finish(name, m, bevel=0.05, ao=ao)


def build_bin(ao):
    m = K()
    m.cyl((0, 0, 0), 0.75, 0.9, 2.1, 'crayB', seg=14, bevel=False)
    m.cyl((0, 0, 2.02), 0.94, 0.94, 0.12, 'navy', seg=14, bevel=False)
    for (x, y, z, r) in ((-0.3, 0.15, 2.2, 0.36), (0.3, -0.2, 2.25, 0.32), (0.05, 0.4, 2.35, 0.3), (0.15, 0.0, 2.5, 0.28)):
        m.sphere((x, y, z), r, 'paper', seg=(6, 4), rot=(x * 90, y * 60, z * 40))
    m.sphere((0.75, -0.62, 0.26), 0.26, 'paper', seg=(6, 4), rot=(20, 40, 10))
    m.colbox(-0.92, -0.92, 0, 0.92, 0.92, 2.14)
    finish('Bin', m, bevel=0.03, ao=ao)


def bookcase(m, flip):
    """Low bookcase 6 x 1.7 x 5.6 m, open to -Y (flip: open to +Y)."""
    m.parent = rotz(180) if flip else Matrix.Identity(4)
    m.bx(-2.85, 0.72, 0.3, 2.85, 0.82, 5.44, 'wood3', flat=True)
    for sx in (-1, 1):
        m.bx(min(sx * 2.8, sx * 2.95), -0.85, 0, max(sx * 2.8, sx * 2.95), 0.85, 5.45, 'honey')
    m.bx(-2.95, -0.85, 5.45, 2.95, 0.85, 5.62, 'honey')
    m.bx(-2.8, -0.8, 0, 2.8, 0.72, 0.3, 'honeyDk')
    shelves = [0.3, 2.0, 3.7]
    for z in shelves[1:]:
        m.bx(-2.8, -0.8, z - 0.12, 2.8, 0.72, z, 'honey')
    cols = ['crayR', 'navy', 'crayY', 'crayG', 'crayB', 'crayO', 'crayP', 'teal2', 'pink', 'crayR', 'crayB']
    for si, z in enumerate(shelves):
        x = -2.72
        i = si * 3
        top = (shelves[si + 1] - 0.12) if si + 1 < len(shelves) else 5.45
        while x < 2.0:
            t = (0.22, 0.3, 0.24, 0.34, 0.2, 0.28)[i % 6]
            h = min(top - z - 0.12, (1.2, 1.38, 1.05, 1.3, 1.15, 1.42)[(i + si) % 6])
            d = (0.0, 0.06, 0.02, 0.1, 0.04)[i % 5]
            c = cols[(i * 3 + si) % len(cols)]
            m.bx(x, -0.68 - d, z, x + t - 0.015, 0.68 - d, z + h, c)
            if i % 2 == 0:
                m.bx(x + 0.025, -0.684 - d, z + h * 0.7, x + t - 0.04, -0.68 - d, z + h * 0.78, 'amber' if c != 'crayY' else 'ink', flat=True)
            x += t
            i += 1
        # a couple of books leaning at the end of the row
        m.box((2.55, -0.05, z + 0.62), (0.2, 1.3, 1.25), cols[(si + 4) % len(cols)], rot=(0, -14, 0), bevel=False)
    m.parent = Matrix.Identity(4)
    m.colbox(-2.95, -0.85, 0, 2.95, 0.85, 5.62)


def build_bookcases(ao):
    for name, flip in (('Bookcase', False), ('BookcaseB', True)):
        m = K()
        bookcase(m, flip)
        finish(name, m, bevel=0.02, ao=ao)


def build_beanbags(ao):
    for v, c in (('R', 'crayR'), ('B', 'crayB'), ('Y', 'crayY')):
        m = K()
        m.sphere((0, 0, 0.58), 1.0, c, seg=(14, 8), scale=(1.35, 1.25, 0.62))
        m.sphere((0, 0.5, 1.02), 0.8, c, seg=(12, 7), scale=(1.12, 0.62, 0.78), rot=(-12, 0, 0))
        m.cyl((0.0, -1.2, 0.5), 0.08, 0.08, 0.02, 'white', seg=6, rot=(90, 0, 0), bevel=False)
        m.colbox(-1.3, -1.2, 0, 1.3, 1.2, 1.55)
        finish('BeanBag_' + v, m, bevel=0.0, ao=ao)


def build_rug():
    """Reading rug 11.6 x 9.6 m: navy border, 4 x 3 coloured seat squares with shapes (floor patch, no collision)."""
    m = K()
    m.bx(-5.8, -4.8, 0.016, 5.8, 4.8, 0.05, 'navy')
    cols = ['crayR', 'crayY', 'crayB', 'crayG', 'crayO', 'crayP', 'teal2', 'pink', 'crayY', 'crayB', 'crayR', 'crayG']
    shapes = [16, 3, 4, 5, 16, 3, 5, 4, 3, 16, 4, 5]
    for j in range(3):
        for i in range(4):
            x = -4.05 + i * 2.7
            y = 2.9 - j * 2.9
            k = j * 4 + i
            m.bx(x - 1.2, y - 1.25, 0.046, x + 1.2, y + 1.25, 0.056, cols[k], flat=True)
            m.cyl((x, y, 0.05), 0.55, 0.55, 0.012, 'white', seg=shapes[k], rot=(0, 0, 45 if shapes[k] == 4 else 90), bevel=False)
            m.flat()
    finish('Rug', m, bevel=0.0)


def build_papers():
    """Sheets of paper on the floor (inside a 2 x 2 footprint, no collision): lined, drawing, maths."""
    specs = (('Paper_A', 12, 'lined'), ('Paper_B', -9, 'drawing'), ('Paper_C', 5, 'sums'))
    for name, ang, kind in specs:
        m = K()
        m.parent = rotz(ang)
        m.bx(-0.55, -0.78, 0.016, 0.55, 0.78, 0.026, 'paper')
        if kind == 'lined' or kind == 'sums':
            for i in range(7):
                y = 0.55 - i * 0.18
                m.bx(-0.5, y - 0.012, 0.022, 0.5, y + 0.012, 0.03, 'lineBl', flat=True)
            m.bx(-0.36, -0.74, 0.025, -0.33, 0.74, 0.034, 'crayR', flat=True)
        if kind == 'sums':
            for i, ch in enumerate('1+2'):
                glyph_top(m, ch, -0.15 + i * 0.25, 0.2, 0.045, 0.034, 0.04, 'ink')
            glyph_top(m, '3', 0.25, -0.25, 0.06, 0.034, 0.04, 'crayR')
        if kind == 'drawing':
            m.cyl((0.28, 0.45, 0.026), 0.17, 0.17, 0.006, 'crayY', seg=10, bevel=False)
            m.flat()
            m.bx(-0.35, -0.35, 0.026, 0.15, 0.1, 0.032, 'crayB', flat=True)
            m.bx(-0.5, -0.7, 0.026, 0.5, -0.56, 0.032, 'crayG', flat=True)
            m.bx(-0.18, -0.35, 0.032, -0.04, -0.12, 0.038, 'crayY', flat=True)
        m.parent = Matrix.Identity(4)
        finish(name, m, bevel=0.0)


def build_pencils(ao):
    """Jumbo pencil and crayons lying on the floor (3 x 1 cells; a low step-over collision)."""
    m = K()
    m.parent = T(0, 0, 0.11) @ rotz(6) @ roty(90) @ rotz(30)
    m.cyl((0, 0, -1.2), 0.11, 0.11, 1.95, 'crayY', seg=6, bevel=False)
    m.cyl((0, 0, 0.75), 0.11, 0.025, 0.36, 'pencilWood', seg=6, bevel=False)
    m.cyl((0, 0, 1.11), 0.025, 0.0, 0.08, 'ink', seg=6, bevel=False)
    m.cyl((0, 0, -1.42), 0.115, 0.115, 0.22, 'steel', seg=8, bevel=False)
    m.cyl((0, 0, -1.58), 0.11, 0.11, 0.16, 'pink', seg=8, bevel=False)
    m.parent = Matrix.Identity(4)
    m.colbox(-1.45, -0.2, 0, 1.45, 0.2, 0.2)
    finish('Pencil', m, bevel=0.0, ao=ao)
    for name, cols in (('Crayons_A', ('crayR', 'crayB')), ('Crayons_B', ('crayG', 'crayO', 'crayP'))):
        m = K()
        for i, c in enumerate(cols):
            x = -0.9 + i * 0.95
            y = (-0.2, 0.18, -0.05)[i]
            m.parent = T(x, y, 0.13) @ rotz((-12, 9, 20)[i]) @ roty(90)
            m.cyl((0, 0, -0.62), 0.13, 0.13, 0.95, c, seg=10, bevel=False)
            m.cyl((0, 0, -0.42), 0.136, 0.136, 0.5, 'paperDk', seg=10, bevel=False)
            m.cyl((0, 0, 0.33), 0.13, 0.05, 0.22, c, seg=10, bevel=False)
        m.parent = Matrix.Identity(4)
        m.colbox(-1.5, -0.42, 0, 1.5, 0.42, 0.24)
        finish(name, m, bevel=0.0, ao=ao)


# ================================================================ landmarks
def build_teacher_desk(ao):
    """Teacher's desk 10 x 5: drawer pedestal (east), panel leg (west), modesty panel facing the class (-Y);
    the kneehole opens north (+Y). Desk globe, books, papers, mug and bell on top."""
    m = K()
    m.bx(-4.85, -2.35, 4.45, 4.85, 2.35, 4.75, 'honey', bevel=True)
    m.bx(1.8, -2.1, 0.25, 4.6, 2.1, 4.45, 'honeyDk')
    m.bx(1.9, -2.0, 0, 4.5, 2.0, 0.25, 'wood3', flat=True)
    for (z0, z1) in ((0.45, 1.75), (1.85, 3.05), (3.15, 4.3)):
        m.bx(1.95, 2.1, z0, 4.45, 2.16, z1, 'honey')
        m.bx(2.85, 2.16, (z0 + z1) / 2 - 0.06, 3.55, 2.26, (z0 + z1) / 2 + 0.06, 'steelDk')
    m.bx(-4.6, -2.1, 0, -4.3, 2.1, 4.45, 'honeyDk')
    m.bx(-4.3, -2.095, 0.9, 1.8, -1.9, 4.45, 'honeyDk')
    for (x0, x1) in ((-3.95, -1.45), (-1.15, 1.45)):
        m.bx(x0, -2.13, 1.3, x1, -2.095, 4.05, 'honey')
    m.bx(2.2, -2.13, 0.6, 4.2, -2.1, 4.05, 'honey')
    m.cyl((0.15, -2.13, 3.4), 0.3, 0.3, 0.01, 'crayY', seg=5, rot=(90, 0, 0), bevel=False)   # gold star sticker
    m.flat()
    z = 4.75
    # desk globe
    m.cyl((-3.3, 0.9, z), 0.4, 0.3, 0.12, 'honeyDk', seg=10)
    m.cyl((-3.3, 0.9, z + 0.12), 0.06, 0.06, 0.45, 'amber', seg=6, bevel=False)
    m.sphere((-3.3, 0.9, z + 1.05), 0.5, 'ocean', seg=(12, 8))
    m.sphere((-3.22, 0.84, z + 1.12), 0.47, 'land', seg=(9, 6), scale=(1.07, 1.07, 0.6), rot=(20, 0, 30))
    # papers and books
    m.bx(-1.9, 0.2, z, -0.3, 1.9, z + 0.18, 'paper')
    m.bx(-1.8, 0.3, z + 0.18, -0.4, 1.8, z + 0.2, 'paperDk', rot=(0, 0, 6))
    book_lying(m, 1.7, 1.25, 0.26, 'crayR', T(0.9, 1.2, z) @ rotz(-8))
    book_lying(m, 1.6, 1.15, 0.24, 'navy', T(0.9, 1.2, z + 0.26) @ rotz(5))
    book_lying(m, 1.5, 1.1, 0.22, 'crayG', T(0.9, 1.2, z + 0.5) @ rotz(-3))
    # mug of pencils and a desk bell
    m.cyl((3.2, 1.4, z), 0.36, 0.36, 0.75, 'crayB', seg=12)
    m.beam((3.56, 1.4, z + 0.18), (3.56, 1.4, z + 0.58), 0.1, 'crayB')
    for k, c in enumerate(('crayY', 'crayR', 'crayY')):
        m.cyl((3.1 + k * 0.1, 1.4 + (k - 1) * 0.1, z + 0.3), 0.06, 0.06, 1.15, c, seg=6, rot=((k - 1) * 10, (k - 1) * 6, 0), bevel=False)
    m.cyl((2.3, -1.2, z), 0.32, 0.32, 0.08, 'rubber', seg=10, bevel=False)
    m.sphere((2.3, -1.2, z + 0.12), 0.27, 'amber', seg=(10, 5), scale=(1, 1, 0.9))
    m.cyl((2.3, -1.2, z + 0.36), 0.05, 0.05, 0.12, 'amber', seg=6, bevel=False)
    m.colbox(1.8, -2.1, 0, 4.6, 2.1, 4.45)
    m.colbox(-4.6, -2.1, 0, -4.3, 2.1, 4.45)
    m.colbox(-4.3, -2.13, 0.9, 1.8, -1.9, 4.45)
    m.colbox(-4.85, -2.35, 4.45, 4.85, 2.35, 4.75)
    finish('Landmark_TeacherDesk', m, bevel=BW, ao=ao)


def build_globe(ao):
    """Floor globe on a wooden tripod: walk under it. Continents from LAND, axis tilted 23.5 degrees."""
    m = K()
    C = Vector((0, 0, 4.5))
    R = 1.62
    tilt = rotx(-23.5)
    # tripod
    for i in range(3):
        a = math.radians(90 + i * 120)
        foot = Vector((math.cos(a) * 1.65, math.sin(a) * 1.65, 0.12))
        m.beam((0, 0, 2.05), foot, 0.16, 'honeyDk')
        m.cyl((foot.x, foot.y, 0), 0.2, 0.17, 0.12, 'rubber', seg=8, bevel=False)
        m.col((foot.x, foot.y, 0.3), (0.22, 0.22, 0.3))
    m.cyl((0, 0, 1.85), 0.2, 0.2, 0.55, 'honeyDk', seg=10)
    # meridian half ring (brass) in the plane of the tilted axis and X, joined to the stand at the south pole
    ax = tilt @ Vector((0, 0, 1))
    xs = Vector((1, 0, 0))
    Rr = R + 0.2
    pts = [C + Rr * (math.cos(t) * ax + math.sin(t) * xs) for t in [i / 12 * math.pi for i in range(13)]]
    for i in range(12):
        m.beam(pts[i], pts[i + 1], 0.13, 'amber')
    m.beam((0, 0, 2.4), pts[12], 0.14, 'amber')
    for p in (C + R * ax, C - R * ax):
        m.beam(p - 0.05 * ax.normalized() * (1 if p.z > C.z else -1), p + 0.22 * (p - C).normalized(), 0.1, 'amber')
    # the globe: one sphere, faces coloured by the continent map
    bm = m.bm
    before = set(bm.faces)
    m.sphere((0, 0, 0), R, 'ocean', seg=(26, 15))
    new = [f for f in bm.faces if f not in before]
    Mx = T(*C) @ tilt
    for v in {v for f in new for v in f.verts}:
        v.co = Mx @ v.co
    inv = tilt.inverted()
    for f in new:
        c = inv @ (f.calc_center_median() - C)
        c.normalize()
        lat = math.degrees(math.asin(max(-1, min(1, c.z))))
        lon = math.degrees(math.atan2(c.y, c.x))
        k = land_at(lat, lon)
        if k:
            f.material_index = pal.index(k)
    m.col((0, 0, 1.2), (0.25, 0.25, 1.2))
    m.col((0, 0, 4.5), (1.7, 1.7, 1.75))
    finish('Landmark_Globe', m, bevel=0.02, ao=ao)


def build_chalkboard(ao):
    """21.9 m chalkboard on the north wall (prefab row next to the wall; back 1 cm off the wall's rails)."""
    m = K()
    yb = 0.46
    m.bx(-10.95, 0.25, 12.4, 10.95, yb, 12.8, 'honeyDk')
    m.bx(-10.95, 0.25, 5.3, 10.95, yb, 5.7, 'honeyDk')
    for sx in (-1, 1):
        m.bx(min(sx * 10.55, sx * 10.95), 0.25, 5.7, max(sx * 10.55, sx * 10.95), yb, 12.4, 'honeyDk')
    m.bx(-10.55, 0.31, 5.7, 10.55, yb - 0.005, 12.4, 'board', flat=True)
    m.bx(-10.6, -0.35, 5.3, 10.6, 0.25, 5.48, 'honeyDk')
    m.bx(-10.6, -0.35, 5.48, 10.6, -0.28, 5.62, 'honey')
    # chalk and the duster on the tray
    for (x, c, a) in ((-6.2, 'chalk', 4), (-5.6, 'chalkY', -8), (-5.1, 'notePk', 12), (4.4, 'chalk', -3), (6.8, 'noteBl', 7)):
        m.parent = T(x, -0.05, 5.55) @ rotz(a) @ roty(90)
        m.cyl((0, 0, -0.35), 0.07, 0.07, 0.7, c, seg=8, bevel=False)
    m.parent = Matrix.Identity(4)
    m.bx(-1.2, -0.2, 5.48, 0.2, 0.15, 5.6, 'felt')
    m.bx(-1.2, -0.2, 5.6, 0.2, 0.15, 5.8, 'honeyDk')
    # chalk work (strokes 5 mm proud of the board)
    yf, yk = 0.305, 0.31

    def word(s, x0, ztop, px, pz, col, gap=1.4):
        for i, ch in enumerate(s):
            if ch != ' ':
                glyph_wall(m, ch, x0 + i * px * 5 * gap, ztop, px, pz, yf, yk, col)

    word('ABC', -8.6, 11.6, 0.3, 0.34, 'chalk')
    word('1+2=3', 2.6, 11.6, 0.22, 0.26, 'chalkY')
    # underline squiggle
    for i in range(7):
        m.box((-8.3 + i * 0.72, 0.3065 - 0.003 * (i % 2), 9.35 + (0.12 if i % 2 else -0.12)), (0.78, 0.007, 0.09), 'chalk', rot=(0, 18 if i % 2 else -18, 0), bevel=False)
        m.flat()
    # a drawn sun: ring of strokes and rays
    cx, cz = -1.0, 8.4
    for i in range(12):
        a = i * 30
        r = math.radians(a)
        m.box((cx + math.sin(r) * 0.95, 0.307 - 0.003 * (i % 2), cz + math.cos(r) * 0.95), (0.52, 0.006, 0.1), 'chalkY', rot=(0, -a - 90, 0), bevel=False)
        m.flat()
        if i % 2 == 0:
            m.box((cx + math.sin(r) * 1.55, 0.3075, cz + math.cos(r) * 1.55), (0.07, 0.005, 0.5), 'chalkY', rot=(0, -a, 0), bevel=False)
            m.flat()
    # a little house and a tic-tac-toe
    m.bx(5.0, yf, 6.6, 7.2, yk, 6.7, 'chalk', flat=True)
    for x in (5.0, 7.1):
        m.bx(x, 0.3045, 6.7, x + 0.1, yk, 8.2, 'chalk', flat=True)
    m.box((5.6, 0.3065, 8.75), (1.5, 0.007, 0.1), 'chalk', rot=(0, -38, 0), bevel=False)
    m.flat()
    m.box((6.6, 0.3035, 8.75), (1.5, 0.007, 0.1), 'chalk', rot=(0, 38, 0), bevel=False)
    m.flat()
    for i in (1, 2):
        m.bx(-8.6, yf, 6.5 + i * 0.7, -6.5, yk, 6.58 + i * 0.7, 'chalk', flat=True)
        m.bx(-8.6 + i * 0.7, 0.3, 6.4, -8.52 + i * 0.7, 0.307, 8.6, 'chalk', flat=True)
    m.colbox(-10.95, 0.25, 5.3, 10.95, yb, 12.8)
    m.colbox(-10.6, -0.35, 5.3, 10.6, 0.25, 5.62)
    finish('Landmark_Chalkboard', m, bevel=0.03, ao=False)


# ================================================================ build
def build_kit_classroom(ao):
    global pal
    pal = Palette(FAM)
    STATS.clear()
    build_walls()
    build_rotated()
    build_gate()
    build_trail()
    build_hatch(ao)
    build_eraser(ao)
    build_light()
    build_desks(ao)
    build_chairs(ao)
    build_backpacks(ao)
    build_books(ao)
    build_blocks(ao)
    build_bin(ao)
    build_bookcases(ao)
    build_beanbags(ao)
    build_rug()
    build_papers()
    build_pencils(ao)
    build_teacher_desk(ao)
    build_globe(ao)
    build_chalkboard(ao)
    total = 0
    for k in sorted(STATS):
        print('%-40s %6d tris' % (k, STATS[k]))
        total += STATS[k]
    print('kit-classroom pieces: %d, total %d tris' % (len(STATS), total))
    export(FAM)


FAMILY = FAM
BUILD = build_kit_classroom
