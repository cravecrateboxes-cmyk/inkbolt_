"""INKBOLT asset family: kit-smallcity (campaign level 2, 'Small City').

A warm late-afternoon downtown: 2-4 storey red / orange / buff brick and cream-stone buildings with painted shop
fronts and striped awnings, concrete sidewalks, grey-blue asphalt with white lane paint and zebra crossings,
parked cars, a city bus, a delivery van, iron lamp posts, street trees, a clock tower and a fountain.

Conventions (shared with every kit family, see ib_lib.py):
  * one ASCII cell = 1 m; a piece's origin is the centre of its cell / footprint at floor level
  * Blender Z-up; the facade of a wall module is its Blender -Y face (= game +Z before the engine turns it to the
    open side with theme.wall.faceOpen)
  * every coplanar pair of faces is avoided by construction (check_zfight fails the build otherwise): details sit
    >= 3 mm proud, full-width facade bands are stacked so their end faces never overlap
  * wall modules strip the outline shell on their +/-X faces ('noside' hull) so a run of modules reads as one
    seamless facade; building boundaries (pilasters) and corners keep the full ink outline.
  * east / west facades use the same modules, placed by the theme's '[' / ']' symbols (the engine only turns '#'
    modules by 0 or 180 degrees); 'Blank' modules give inner corners to the perpendicular facade, 'Fill' caps the
    hidden cells behind '[' / ']'.
  * faces nobody can see are dropped (backs of facade details, tops above 5 m, bottoms below 1 m, slab bottoms) so a
    56 x 50 m downtown zone stays near 90k triangles.
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import smallcity_detail as SD

FAM = 'kit-smallcity'
PRE = 'KIT_SMALLCITY_'
ib_lib.GLB[FAM] = 'fps-kit-smallcity.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # facades
    ('brickR', '#C9614A'), ('brickO', '#DB7E52'), ('brickT', '#D4A170'), ('stoneC', '#F1E4C6'),
    ('stoneS', '#E2C896'), ('stoneB', '#C9B086'), ('roof', '#8E9097'), ('frameW', '#F7F3EA'),
    # shop fronts and awnings (muted)
    ('shopTeal', '#3E9B95'), ('shopMustard', '#D7A93C'), ('shopBurg', '#94434F'), ('shopGreen', '#4F8C61'),
    ('shopNavy', '#45618E'), ('awnCream', '#F6EDD8'), ('glass', '#A9D4E4'), ('glassD', '#6F9DB4'),
    ('glassL', '#E6F5FA'), ('glassW', '#FFE3A3'), ('wood', '#7D5640'), ('woodL', '#B98A5B'),
    # street
    ('asphalt', '#8C95A2'), ('paintW', '#F5F2E9'), ('paintY', '#F0C548'), ('conc', '#D8D3C8'),
    ('concD', '#C2BCAF'), ('iron', '#363941'), ('ironL', '#5A616D'), ('lamp', '#FFF1C4'),
    # nature
    ('leaf', '#6BAA55'), ('leaf2', '#86C166'), ('leafD', '#558F46'), ('trunk', '#7E5C42'),
    ('soil', '#6C4E3A'), ('flowerP', '#F28DB2'), ('planter', '#C77A52'), ('water', '#8ECFE1'),
    ('conc2', '#CDC7BA'),
    # vehicles
    ('taxi', '#F2C232'), ('carRed', '#D65A4C'), ('carBlue', '#5089C8'), ('carMint', '#7DC3A6'),
    ('carCream', '#EEE0BD'), ('tire', '#2C2B30'), ('chrome', '#CDD3DA'), ('waterL', '#C6EAF2'),
    # props / landmark / backdrop
    ('mailbox', '#3E6EA9'), ('bag', '#4B505B'), ('copper', '#78B9A5'), ('gold', '#E0B04C'),
    ('steel', '#AEB7C2'), ('steelD', '#8C96A3'), ('bdA', '#CFB39A'), ('bdB', '#BEB8C8'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64

HT = 0.02            # outline shell thickness (CFG)
CULL_DIRS = [('t', Vector((0, 0, 1))), ('b', Vector((0, 0, -1))), ('f', Vector((0, -1, 0))), ('k', Vector((0, 1, 0))),
             ('l', Vector((-1, 0, 0))), ('r', Vector((1, 0, 0)))]
G_H, U_H = 3.6, 3.0  # ground floor / upper floor heights


def top_of(n):
    """Top of the top storey for an n-storey building (the cornice sits here)."""
    return G_H + (n - 1) * U_H


PARAPET = 0.85


# ================================================================ modelling helpers
class PM(Model):
    """Model with per-shape outline-shell modes: 'full' (default), 'noside' (no shell on faces at x = +/-0.5,
    so neighbouring modules join seamlessly) and 'none' (painted detail, no shell)."""

    def __init__(self, pal):
        super().__init__(pal)
        self.hmode = {}
        self.cur = 'full'

    def _finish(self, verts, color, bevel):
        faces = super()._finish(verts, color, bevel)
        if self.cur != 'full':
            self.hmode[self.nshape] = self.cur
        return faces

    def bx(self, x0, x1, y0, y1, z0, z1, color, hull='full', bevel=False, cull=''):
        """Axis-aligned box from extents. cull: faces never seen, dropped (t b f k l r = +Z -Z -Y +Y -X +X, in the
        box's own frame before the parent transform)."""
        self.cur = hull
        M = mat_trs(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0))
        verts = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)['verts']
        if cull:
            kill = []
            for f in {f for v in verts for f in v.link_faces}:
                f.normal_update()
                if any(ch in cull and f.normal.dot(d) > 0.99 for ch, d in CULL_DIRS):
                    kill.append(f)
            bmesh.ops.delete(self.bm, geom=kill, context='FACES_ONLY')
            loose = [e for e in {e for v in verts for e in v.link_edges} if not e.link_faces]
            if loose:
                bmesh.ops.delete(self.bm, geom=loose, context='EDGES')
            verts = [v for v in verts if v.is_valid]
            lone = [v for v in verts if not v.link_edges]
            if lone:
                bmesh.ops.delete(self.bm, geom=lone, context='VERTS')
                verts = [v for v in verts if v.is_valid]
        bmesh.ops.transform(self.bm, matrix=self.parent, verts=verts)
        f = self._finish(verts, color, bevel)
        self.cur = 'full'
        return f

    def det(self, x0, x1, d, emb, z0, z1, color, hull='none', back=None):
        """Facade detail standing d proud of the facade plane (y = -0.5) and sunk emb into whatever is behind it
        (back face at y = back, default -0.5 + emb). The back face is never seen; the top is dropped above 5 m (no eye
        gets that high) and the bottom below 1 m (no eye gets that low)."""
        cull = 'k' + ('t' if z1 > 5.0 else '') + ('b' if z0 < 1.0 else '')
        return self.bx(x0, x1, F(d), -0.5 + emb if back is None else back, z0, z1, color, hull=hull, cull=cull)

    def cy(self, loc, r1, r2, h, color, seg=12, rot=(0, 0, 0), bevel=False, caps=True, hull='full'):
        self.cur = hull
        f = self.cyl(loc, r1, r2, h, color, seg=seg, rot=rot, bevel=bevel, caps=caps)
        self.cur = 'full'
        return f

    def sp(self, loc, r, color, seg=(8, 5), scale=(1, 1, 1), hull='full'):
        self.cur = hull
        f = self.sphere(loc, r, color, seg=seg, scale=scale)
        self.cur = 'full'
        return f

    def bm_(self, a, b, t, color, hull='full'):
        self.cur = hull
        f = self.beam(a, b, t, color)
        self.cur = 'full'
        return f

    def prism(self, prof, x0, x1, colors, hull='full', bevel=False, mat=None, skip=()):
        """Polygon prof [(y, z), ...] extruded along X from x0 to x1, split into len(colors) segments, one colour
        each (a striped awning, a barrier with tape...). One shape. skip: profile edges (i -> i+1) never seen."""
        bm = self.bm
        n = len(colors)
        M = self.parent @ (mat or Matrix.Identity(4))
        rings = []
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            rings.append([bm.verts.new(M @ Vector((x, y, z))) for (y, z) in prof])
        faces, drop = [], []
        P = len(prof)
        for k in range(n):
            a, b = rings[k], rings[k + 1]
            for i in range(P):
                j = (i + 1) % P
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.material_index = self.pal.index(colors[k])
                (drop if i in skip else faces).append(f)
        for ring, c in ((rings[0], colors[0]), (rings[-1], colors[-1])):
            f = bm.faces.new(ring)
            f.material_index = self.pal.index(c)
            faces.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=faces + drop)
        if drop:
            bmesh.ops.delete(bm, geom=drop, context='FACES_ONLY')
        self.nshape += 1
        for f in faces:
            f[self.shape] = self.nshape
            if bevel:
                for e in f.edges:
                    e[self.bw] = 1.0
        if hull != 'full':
            self.hmode[self.nshape] = hull
        return faces

    def fan(self, center, top, r, seg, colors, rot=0.0, hull='full', base_z=None):
        """Striped cone / pyramid (umbrella, roof): apex at top, base ring radius r at center z; colours alternate."""
        bm = self.bm
        M = self.parent
        cx, cy, cz = center
        ring = [bm.verts.new(M @ Vector((cx + math.cos(rot + i * 2 * math.pi / seg) * r, cy + math.sin(rot + i * 2 * math.pi / seg) * r, cz))) for i in range(seg)]
        apex = bm.verts.new(M @ Vector((cx, cy, top)))
        faces = []
        for i in range(seg):
            f = bm.faces.new((ring[i], ring[(i + 1) % seg], apex))
            f.material_index = self.pal.index(colors[i % len(colors)])
            faces.append(f)
        f = bm.faces.new(list(reversed(ring)))
        f.material_index = self.pal.index(colors[0])
        faces.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        self.nshape += 1
        for f in faces:
            f[self.shape] = self.nshape
        if hull != 'full':
            self.hmode[self.nshape] = hull
        return faces


def post_hull(obj, hmode, side=0.45):
    """Remove outline-shell faces per shape mode (see PM)."""
    if not hmode:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    sl = bm.faces.layers.int.get('shape_id')
    if hl is None or sl is None:
        print('post_hull: missing layers on', obj.name)
        bm.free()
        return
    bm.normal_update()
    kill = []
    for f in bm.faces:
        if not all(v[hl].length > 0 for v in f.verts):
            continue
        mode = hmode.get(f[sl])
        if mode == 'none':
            kill.append(f)
        elif mode in ('noside', 'noend'):
            c = f.calc_center_median()
            ax = 0 if mode == 'noside' else 1
            if abs(f.normal[ax]) > 0.9 and abs(c[ax]) > side:
                kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(obj.data)
    bm.free()


def make(name, m, bevel=0.0, hull=HT, ao=False):
    obj = build_object(PRE + name, m, bevel, hull, ao=ao)
    post_hull(obj, m.hmode)
    return obj


def col_box(obj, i, x0, x1, y0, y1, z0, z1):
    """Collision box child <Piece>_COL<i> (Blender extents; the engine reads centre + half extents in Y-up)."""
    e = bpy.data.objects.new(obj.name + '_COL%d' % i, None)
    e.empty_display_type = 'CUBE'
    e.parent = obj
    e.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    e.scale = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
    bpy.context.scene.collection.objects.link(e)
    return e


# ================================================================ facades
# y of the front face of a detail standing d proud of the facade plane (y = -0.5)
def F(d):
    return -0.5 - d


MATS = {'R': ('brickR', 'stoneC', 'stoneB'), 'O': ('brickO', 'stoneC', 'stoneS'), 'T': ('brickT', 'stoneC', 'brickR'),
        'C': ('stoneS', 'frameW', 'stoneB')}
# building styles: (facade material, shop colour, storeys). Mirrored by STY in src/data/themes/smallcity.js.
STYLES = [
    ('R', 'shopTeal', 3), ('O', 'shopBurg', 2), ('T', 'shopGreen', 3), ('R', 'shopMustard', 4),
    ('C', 'shopNavy', 3), ('O', 'shopTeal', 3), ('T', 'shopBurg', 2), ('C', 'shopMustard', 4),
]


def facade_common(m, mat, n, upper_windows, glass='glass'):
    """Body, string course, sill courses, upper windows, cornice and coping of one 1 m module."""
    brick, trim, base = MATS[mat]
    T = top_of(n)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PARAPET, brick, hull='noside', cull='bt')
    m.det(-0.5, 0.5, 0.06, 0, 3.5, 3.62, trim, hull='noside')                        # string course over the shops
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        m.det(-0.5, 0.5, 0.05, 0, z0 + 0.62, z0 + 0.72, trim)                         # continuous sill course
        if upper_windows:
            m.det(-0.3, 0.3, 0.02, 0.02, z0 + 0.72, z0 + 2.34, 'ink')                    # inked window frame
            m.det(-0.255, 0.255, 0.03, 0.03, z0 + 0.765, z0 + 2.295, glass)
            m.det(-0.25, 0.25, 0.04, 0.04, z0 + 1.50, z0 + 1.56, 'frameW')               # meeting rail
            m.det(-0.36, 0.36, 0.045, 0.045, z0 + 2.34, z0 + 2.5, trim)                  # lintel
    m.det(-0.5, 0.5, 0.14, 0, T, T + 0.32, trim, hull='noside')                        # cornice
    m.bx(-0.5, 0.5, F(0.03), 0.5, T + PARAPET, T + PARAPET + 0.1, trim, hull='noside', cull='b')  # coping


def shopfront(m, shop, kind):
    """Painted shop front on the ground floor: panel, fascia sign, display window or door, striped awning."""
    m.bx(-0.5, 0.5, F(0.025), -0.5, 0.058, 3.5, shop, hull='noside', cull='ktb')      # panel (clear of the paving)
    m.bx(-0.5, 0.5, F(0.1), F(0.025), 2.86, 3.46, shop, hull='noside', cull='k')       # fascia sign board
    if kind == 'win':
        m.det(-0.45, 0.45, 0.085, 0.06, 0.5, 0.58, 'stoneC')                              # window sill
        m.det(-0.42, 0.42, 0.04, 0.015, 0.58, 2.74, 'ink')                                # window surround
        m.det(-0.385, 0.385, 0.05, 0.025, 0.615, 2.705, 'glassD')                         # display glass
        m.det(-0.33, -0.27, 0.055, 0.03, 1.1, 2.35, 'glassL')                             # comic shine
    elif kind == 'door':
        for x0, x1 in ((-0.3, -0.04), (0.06, 0.3)):                                        # sign lettering
            m.bx(x0, x1, F(0.106), F(0.1) + 0.004, 3.06, 3.26, 'awnCream', hull='none', cull='k')
        m.det(-0.37, 0.37, 0.04, 0.015, 0, 2.62, 'ink')                                   # door surround
        m.det(-0.33, 0.33, 0.05, 0.025, 0, 2.2, 'wood')                                   # door leaf
        m.det(-0.25, 0.25, 0.058, 0.033, 1.0, 2.05, 'glassD')                             # door glass
        m.det(0.2, 0.28, 0.066, 0.041, 0.98, 1.06, 'gold')                                # handle
        m.det(-0.33, 0.33, 0.05, 0.025, 2.24, 2.58, 'glass')                              # transom
        # blade sign hanging off an iron bracket above the awning
        m.bx(-0.02, 0.02, -1.2, -0.49, 4.18, 4.22, 'iron', hull='none', cull='k')
        m.bx(-0.025, 0.025, -1.14, -0.66, 3.62, 4.18, shop, cull='t')
        m.bx(-0.029, 0.029, -1.04, -0.76, 3.78, 4.02, 'awnCream', hull='none', cull='tb')   # sign face (both sides)
    if kind == 'pier':
        return
    # striped awning below the fascia: slope + valance in one folded profile (4 stripes per metre); its back is on the
    # panel. Piers between shop windows have none, so each window / door reads as its own little awning.
    yb, yf = F(0.025), F(0.025) - 0.95
    prof = [(yb, 2.82), (yf, 2.44), (yf, 2.22), (yb, 2.74)]
    m.prism(prof, -0.5, 0.5, [shop, 'awnCream', shop, 'awnCream'], skip=(3,))


def build_walls(pal, ao):
    out = []
    for si, (mat, shop, n) in enumerate(STYLES):
        for kind in ('Win', 'Door', 'Pier'):
            m = PM(pal)
            facade_common(m, mat, n, upper_windows=(kind != 'Pier'))
            shopfront(m, shop, {'Win': 'win', 'Door': 'door', 'Pier': 'pier'}[kind])
            SD.wall_detail(m, kind, MATS[mat][1], n, si)
            out.append(make('Wall%s_%d' % (kind, si), m, ao=ao))
    for mat, n in sorted({(st[0], st[2]) for st in STYLES}):
        out.append(pilaster(pal, mat, n, ao))
        out.append(corner(pal, mat, n, ao))
        # plain brick beside an inner corner: nothing proud, so the perpendicular facade owns the corner
        brick, trim, base = MATS[mat]
        T = top_of(n)
        m = PM(pal)
        m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PARAPET, brick, hull='noside', cull='bt')
        m.bx(-0.5, 0.5, -0.5, 0.5, T + PARAPET, T + PARAPET + 0.1, trim, hull='noside', cull='b')
        out.append(make('Blank_%s%d' % (mat, n), m, ao=ao))
    # hidden block filler behind east/west facades (see themes/smallcity.js): a roof-coloured cap at roof height
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 6.96, 7.04, 'roof', hull='none', cull='b')
    out.append(make('Fill', m, hull=0))
    return out


def pilaster(pal, mat, n, ao):
    """Building boundary: full-height pier with base and cap, full ink outline."""
    brick, trim, base = MATS[mat]
    T = top_of(n)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PARAPET, brick, cull='bt')
    # every band stays inside the cell (two pilasters can stand side by side); the pier is a little narrower
    m.bx(-0.46, 0.46, F(0.11), -0.49, 0.55, T + PARAPET + 0.27, brick, cull='kbt')      # the pier
    m.bx(-0.48, 0.48, F(0.15), -0.49, 0, 0.55, base, cull='kb')                        # base block
    m.bx(-0.5, 0.5, F(0.17), -0.5, T - 0.06, T + 0.38, trim, cull='kt')                # cornice block
    m.bx(-0.5, 0.5, -0.5, 0.5, T + PARAPET, T + PARAPET + 0.25, brick, cull='bt')      # raised parapet
    m.bx(-0.5, 0.5, F(0.14), 0.5, T + PARAPET + 0.25, T + PARAPET + 0.37, trim, cull='b')   # cap
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        m.det(-0.2, 0.2, 0.125, 0.02, z0 + 1.1, z0 + 1.7, trim, back=-0.48)              # stone panel
    m.bx(-0.5, 0.5, F(0.13), -0.5, 3.46, 3.66, trim, cull='k')                         # string block
    return make('Pilaster_%s%d' % (mat, n), m, ao=ao)


def corner(pal, mat, n, ao):
    """Block corner: brick pier with stone quoins on all four edges and wrap-around courses (4-way symmetric)."""
    brick, trim, base = MATS[mat]
    T = top_of(n)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PARAPET, brick, cull='bt')
    q = 0.535
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(min(sx * 0.37, sx * q), max(sx * 0.37, sx * q), min(sy * 0.37, sy * q), max(sy * 0.37, sy * q), 0.5, T, trim, cull='bt')
    m.bx(-0.55, 0.55, -0.55, 0.55, 0, 0.5, base, cull='b')                            # plinth
    m.bx(-0.58, 0.58, -0.58, 0.58, 3.48, 3.64, trim)                                  # string course wrap
    m.bx(-0.66, 0.66, -0.66, 0.66, T - 0.04, T + 0.36, trim, cull='t')                # cornice wrap
    m.bx(-0.535, 0.535, -0.535, 0.535, T + PARAPET - 0.02, T + PARAPET + 0.12, trim)   # coping
    return make('Corner_%s%d' % (mat, n), m, ao=ao)


# ================================================================ street surface
def build_floor_marks(pal):
    """Flat paint and paving. No outline shell: joints would turn to ink at grazing angles."""
    # sidewalk paving slab (1 m), raised 5 cm: the side faces read as the curb
    # 1 m paving slabs, 5 cm proud (the sides read as the curb); the theme lays two tones as a checker
    for name, c, j in (('Walk', 'conc', 'concD'), ('WalkB', 'conc2', 'concD'), ('Plaza', 'stoneC', 'stoneS'), ('PlazaB', 'stoneS', 'stoneB')):
        m = PM(pal)
        tile(m, 0, 0, c, j)
        make(name, m, hull=0)
    # zebra bar (one 0.5 m bar per metre; bars join along X)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.25, 0.25, 0.006, 0.014, 'paintW', hull='none')
    make('Zebra', m, hull=0)
    # lane line, 1 m of paint along X (a run of cells = a solid line, alternate cells = dashes)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.06, 0.06, 0.006, 0.013, 'paintW', hull='none')
    make('LaneW', m, hull=0)
    m = PM(pal)
    for sy in (-1, 1):
        m.bx(-0.5, 0.5, sy * 0.13 - 0.05, sy * 0.13 + 0.05, 0.006, 0.013, 'paintY', hull='none')
    make('LaneY', m, hull=0)
    # manhole cover
    m = PM(pal)
    m.cy((0, 0, 0.006), 0.36, 0.36, 0.012, 'ironL', seg=14, hull='none')
    for k in range(3):
        m.bx(-0.24 + k * 0.16, -0.2 + k * 0.16, -0.22, 0.22, 0.01, 0.0215, 'iron', hull='none')
    make('Manhole', m, hull=0)


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    """Brick gatehouse arch over the 3 m roll-up shutter; symmetric front/back (entry and exit gates)."""
    m = PM(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.485, sx * 2.12))
        m.bx(x0, x1, -0.66, 0.66, 0, 7.6, 'brickR')                                    # piers
        m.bx(x0 - 0.04, x1 + 0.04, -0.72, 0.72, 0, 0.6, 'stoneB')                      # pier base
        m.bx(x0 - 0.03, x1 + 0.03, -0.7, 0.7, 3.95, 4.15, 'stoneC')                    # impost band
    m.bx(-1.49, 1.49, -0.58, 0.58, 3.12, 7.62, 'brickR')                               # bridge over the opening
    m.bx(-2.24, 2.24, -0.74, 0.74, 7.6, 7.95, 'stoneC')                                # cornice
    m.bx(-2.16, 2.16, -0.66, 0.66, 7.95, 8.5, 'brickR')                                # parapet
    m.bx(-2.22, 2.22, -0.7, 0.7, 8.5, 8.62, 'stoneC')                                  # coping
    m.bx(-1.62, 1.62, -0.72, 0.72, 3.07, 3.6, 'steelD')                                # shutter box (drum housing)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.72, sy * 0.745))
        m.bx(-1.55, 1.55, y0, y1, 3.25, 3.42, 'amber', hull='none')                    # hazard band on the housing
        y0, y1 = sorted((sy * 0.58, sy * 0.64))
        m.bx(-0.9, 0.9, y0, y1, 4.6, 6.9, 'stoneC')                                    # plaque frame
        y0, y1 = sorted((sy * 0.64, sy * 0.66))
        m.bx(-0.75, 0.75, y0, y1, 4.75, 6.75, 'shopTeal', hull='none')                # plaque
        y0, y1 = sorted((sy * 0.66, sy * 0.675))
        m.bx(-0.5, 0.5, y0, y1, 5.45, 6.05, 'paper', hull='none')                      # emblem bar
        for k, x in enumerate((-0.3, 0.0, 0.3)):
            y0, y1 = sorted((sy * 0.675, sy * 0.69))
            m.bx(x - 0.07, x + 0.07, y0, y1, 5.55, 5.95, 'ink' if k != 1 else 'amber', hull='none')
        # gate lamps on the piers
        for sx in (-1, 1):
            y0, y1 = sorted((sy * 0.66, sy * 0.8))
            m.bx(sx * 1.81 - 0.05, sx * 1.81 + 0.05, y0, y1, 2.9, 3.0, 'iron', hull='none')
            y0, y1 = sorted((sy * 0.8, sy * 0.98))
            m.bx(sx * 1.81 - 0.09, sx * 1.81 + 0.09, y0, y1, 2.55, 2.95, 'lamp')
    make('GateFrame', m, ao=ao)
    # roll-up shutter: corrugated steel slats, ink/amber hazard band at the foot
    m = PM(pal)
    H, slats = 3.05, 12
    for i in range(slats):
        z0 = 0.42 + i * (H - 0.42) / slats
        m.bx(-1.5, 1.5, -0.07, 0.07, z0, z0 + (H - 0.42) / slats - 0.03, 'steel' if i % 2 else 'steelD', hull='none')
    for k in range(10):
        m.bx(-1.5 + k * 0.3, -1.2 + k * 0.3, -0.08, 0.08, 0.0, 0.4, 'ink' if k % 2 else 'amber', hull='none')
    sh = make('GateShutter', m, hull=0)
    m = PM(pal)
    m.bx(-1.5, 1.5, -0.08, 0.08, 0, H, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(sh, tmp)


def build_trail(pal, ao):
    """Trail walls: 1 m of brick garden wall, 2.6 m, detailed on its +X face (the trail side). TrailWall has the inset
    panel; the variants (mixed in per module by zones.js through theme.trail.variants) carry pasted gig posters, a
    blue garden door, a planter box with flowers and a creeper over the coping, so the alley never repeats."""
    def base(m, band=True):
        m.bx(-0.2, 0.2, -0.5, 0.5, 0, 2.5, 'brickO', hull='noend')
        m.bx(-0.26, 0.26, -0.5, 0.5, 2.5, 2.64, 'stoneC', hull='noend')                 # coping
        m.bx(0.2, 0.25, -0.5, 0.5, 0, 0.42, 'stoneS', hull='noend')                      # plinth (trail side)
        if band:
            m.bx(0.2, 0.23, -0.5, 0.5, 1.9, 2.0, 'stoneC', hull='noend')                 # band
    m = PM(pal)
    base(m)
    m.bx(0.2, 0.22, -0.32, 0.32, 0.9, 1.7, 'brickR', hull='none')                         # inset panel
    make('TrailWall', m, ao=ao)
    # posters pasted over the bricks (overlapping sheets, each 4 mm prouder), a torn corner
    m = PM(pal)
    base(m)
    for i, (y0, y1, z0, z1, c, c2) in enumerate(((-0.42, 0.02, 0.62, 1.62, 'shopMustard', 'iron'), (-0.05, 0.4, 0.75, 1.82, 'shopTeal', 'paintW'),
                                                  (-0.3, 0.12, 1.25, 1.84, 'awnCream', 'carRed'))):
        x = 0.205 + i * 0.01
        m.bx(x - 0.004, x, y0, y1, z0, z1, c, hull='none')
        m.bx(x, x + 0.004, y0 + 0.06, y1 - 0.06, z1 - 0.3, z1 - 0.12, c2, hull='none')
        m.bx(x, x + 0.004, y0 + 0.06, y0 + 0.06 + (y1 - y0) * 0.45, z0 + 0.1, z0 + 0.16, c2, hull='none')
    make('TrailWall_Posters', m, ao=ao)
    # a blue garden door with a brick arch and an iron ring
    m = PM(pal)
    base(m, band=False)
    m.bx(0.2, 0.235, -0.44, 0.44, 0.42, 2.12, 'stoneC', hull='full')                     # surround
    m.bx(0.235, 0.26, -0.36, 0.36, 0.42, 2.04, 'shopNavy', hull='full')                  # door
    for z in (0.75, 1.35, 1.85):
        m.bx(0.26, 0.265, -0.33, 0.33, z, z + 0.05, 'ironL', hull='none')                # planks / straps
    m.cyl((0.27, 0.2, 1.2), 0.05, 0.05, 0.03, 'iron', seg=8, rot=(0, 90, 0), bevel=False)
    make('TrailWall_Door', m, ao=ao)
    # a planter box with flowers on a bracket, a creeper spilling over the coping
    m = PM(pal)
    base(m)
    m.bx(0.25, 0.55, -0.4, 0.4, 0.9, 1.2, 'planter', hull='full')
    m.bx(0.29, 0.51, -0.36, 0.36, 1.2, 1.22, 'soil', hull='none')
    for j, (y, c) in enumerate(((-0.28, 'flowerP'), (-0.1, 'leaf2'), (0.08, 'flowerP'), (0.26, 'paintY'))):
        m.sphere((0.4, y, 1.32 + 0.03 * (j % 2)), 0.11, c, seg=(6, 4))
    for j, (y, z, r) in enumerate(((-0.3, 2.66, 0.2), (0.05, 2.7, 0.24), (0.32, 2.64, 0.18), (0.22, 2.38, 0.14))):
        m.sphere((0.2, y, z), r, 'leaf' if j % 2 else 'leafD', seg=(7, 5), rot=(0, 0, j * 31))
    make('TrailWall_Planter', m, ao=ao)


def build_hatch(pal, ao):
    """Exit pad: a big iron service hatch (metro maintenance cover) ringed by teal lights and amber studs."""
    m = PM(pal)
    m.cy((0, 0, 0), 1.3, 1.24, 0.1, 'stoneB', seg=20, bevel=True)
    m.cy((0, 0, 0.1), 1.06, 1.06, 0.03, 'teal', seg=20, hull='none')
    m.cy((0, 0, 0.13), 0.98, 0.98, 0.03, 'iron', seg=20, hull='none')
    for k in range(5):
        y = -0.6 + k * 0.3
        m.bx(-0.75 + abs(y) * 0.4, 0.75 - abs(y) * 0.4, y - 0.05, y + 0.05, 0.16, 0.18, 'ironL', hull='none')
    m.bx(-0.05, 0.05, -0.75, 0.75, 0.163, 0.177, 'ironL', hull='none')
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        m.cy((math.cos(a) * 1.17, math.sin(a) * 1.17, 0.1), 0.06, 0.05, 0.06, 'amber', seg=6, hull='none')
    make('Hatch', m, bevel=0.015, ao=ao)


# ================================================================ props: helpers
def slab(m, cells, kind='walk'):
    """Paving under a prop, cell for cell identical to the Walk / Plaza tiles so it joins the pavement seamlessly."""
    c, j = ('conc', 'concD') if kind == 'walk' else ('stoneC', 'stoneS')
    for (cx, cy) in cells:
        tile(m, cx, cy, c, j)


def tile(m, cx, cy, c, j, h=0.05):
    """One 1 m paving slab as a single 10-triangle mesh: top in the slab colour, four sides in the curb colour, no
    bottom."""
    bm = m.bm
    M = m.parent
    t = [bm.verts.new(M @ Vector((cx + x, cy + y, h))) for (x, y) in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))]
    b = [bm.verts.new(M @ Vector((cx + x, cy + y, 0))) for (x, y) in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))]
    faces = []
    f = bm.faces.new(t)
    f.material_index = m.pal.index(c)
    faces.append(f)
    for i in range(4):
        k = (i + 1) % 4
        f = bm.faces.new((b[i], b[k], t[k], t[i]))
        f.material_index = m.pal.index(j)
        faces.append(f)
    bottom = bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=faces + [bottom])
    bmesh.ops.delete(bm, geom=[bottom], context='FACES_ONLY')
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
    m.hmode[m.nshape] = 'none'


def grid_cells(w, d):
    return [(-w / 2 + 0.5 + i, -d / 2 + 0.5 + k) for i in range(w) for k in range(d)]


def ring(m, r0, r1, z0, z1, seg, color, hull='full'):
    """Annulus prism (fountain rim): one shape."""
    bm = m.bm
    M = m.parent
    vs = []
    for (r, z) in ((r1, z0), (r1, z1), (r0, z1), (r0, z0)):
        vs.append([bm.verts.new(M @ Vector((math.cos(i * 2 * math.pi / seg) * r, math.sin(i * 2 * math.pi / seg) * r, z))) for i in range(seg)])
    faces = []
    for k in range(4):
        a, b = vs[k], vs[(k + 1) % 4]
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.material_index = m.pal.index(color)
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull


def slant(p0, p1, t0, t1, o0, o1):
    """Parallelogram profile lying on the segment p0->p1 (y, z), from t0..t1 along it, o0..o1 off it (outward = left normal)."""
    dy, dz = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dy, dz)
    uy, uz = dy / L, dz / L
    ny, nz = -uz, uy
    a = (p0[0] + uy * t0 * L, p0[1] + uz * t0 * L)
    b = (p0[0] + uy * t1 * L, p0[1] + uz * t1 * L)
    return [(a[0] + ny * o0, a[1] + nz * o0), (b[0] + ny * o0, b[1] + nz * o0), (b[0] + ny * o1, b[1] + nz * o1), (a[0] + ny * o1, a[1] + nz * o1)]


def wheel(m, x_out, y, r, w, hub='chrome', seg=10):
    """Wheel on the X axis whose outer face is at x_out (its sign gives the side)."""
    if x_out > 0:
        m.cy((x_out - w, y, r), r, r, w, 'tire', seg=seg, rot=(0, 90, 0))
        m.cy((x_out, y, r), r * 0.5, r * 0.5, 0.025, hub, seg=6, rot=(0, 90, 0), hull='none')
    else:
        m.cy((x_out, y, r), r, r, w, 'tire', seg=seg, rot=(0, 90, 0))
        m.cy((x_out - 0.025, y, r), r * 0.5, r * 0.5, 0.025, hub, seg=6, rot=(0, 90, 0), hull='none')


# ================================================================ vehicles (front = Blender -Y = game +Z)
def build_car(pal, name, body, taxi=False, ao=False):
    m = PM(pal)
    for sx in (-1, 1):
        for y in (-1.22, 1.22):
            wheel(m, sx * 0.9, y, 0.34, 0.24, seg=8)
    m.bx(-0.89, 0.89, -1.92, 1.92, 0.3, 0.9, body, bevel=True)                      # lower body
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 1.84, sy * 1.96))
        m.bx(-0.86, 0.86, y0, y1, 0.28, 0.46, 'chrome')                              # bumpers
        y0, y1 = sorted((sy * 1.95, sy * 1.975))
        m.bx(-0.22, 0.22, y0, y1, 0.3, 0.42, 'paper', hull='none')                  # plates (blank)
    cab = [(-0.78, 0.9), (-0.36, 1.42), (0.62, 1.42), (1.0, 0.9)]
    m.prism(cab, -0.74, 0.74, [body])                                                 # cabin
    m.prism([(-0.73, 0.93), (-0.35, 1.39), (0.6, 1.39), (0.96, 0.93)], -0.746, 0.746, ['ink'], hull='none')
    m.prism([(-0.70, 0.95), (-0.34, 1.37), (0.58, 1.37), (0.93, 0.95)], -0.752, 0.752, ['glass'], hull='none')
    m.bx(-0.758, 0.758, 0.08, 0.2, 0.935, 1.4, body, hull='none')                      # B pillar
    for (p0, p1) in ((cab[0], cab[1]), (cab[2], cab[3])):
        m.prism(slant(p0, p1, 0.06, 0.94, -0.01, 0.006), -0.69, 0.69, ['ink'], hull='none')
        m.prism(slant(p0, p1, 0.12, 0.88, -0.004, 0.014), -0.64, 0.64, ['glass'], hull='none')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.5, sx * 0.79))
        m.bx(x0, x1, -1.935, -1.9, 0.62, 0.78, 'lamp', hull='none', cull='k')         # headlights
        m.bx(x0, x1, 1.9, 1.935, 0.64, 0.8, 'red', hull='none', cull='f')             # tail lights
        x0, x1 = sorted((sx * 0.886, sx * 0.894))
        for y in (-0.62, 0.18):
            m.bx(x0, x1, y - 0.009, y + 0.009, 0.36, 0.86, 'ink', hull='none', cull='l' if sx > 0 else 'r')   # door seams
        x0, x1 = sorted((sx * 0.74, sx * 0.95))
        m.bx(x0, x1, -0.62, -0.5, 1.0, 1.12, body)                                     # mirrors
    m.bx(-0.38, 0.38, -1.932, -1.9, 0.56, 0.74, 'iron', hull='none', cull='k')        # grille
    if taxi:
        m.bx(-0.26, 0.26, 0.05, 0.25, 1.42, 1.62, 'paper')                             # roof sign
        m.bx(-0.265, 0.265, 0.045, 0.255, 1.5, 1.55, 'ink', hull='none')
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.8915, sx * 0.899))
            m.bx(x0, x1, -0.85, 0.85, 0.6, 0.66, 'ink', hull='none')                  # side band
    obj = make(name, m, bevel=0.025, ao=ao)
    col_box(obj, 0, -0.9, 0.9, -1.95, 1.95, 0, 0.9)
    col_box(obj, 1, -0.75, 0.75, -0.78, 1.0, 0.9, 1.42)


def build_van(pal, ao):
    """Box delivery van, 2 x 5: white with a teal wave livery (no lettering)."""
    m = PM(pal)
    for sx in (-1, 1):
        for y in (-1.62, 1.55):
            wheel(m, sx * 0.97, y, 0.38, 0.26)
    m.bx(-0.95, 0.95, -2.42, -1.12, 0.34, 1.25, 'paper', cull='b')                     # cab lower
    cab = [(-2.42, 1.25), (-2.02, 2.08), (-1.12, 2.08), (-1.12, 1.25)]
    m.prism(cab, -0.92, 0.92, ['paper'])
    m.prism(slant(cab[0], cab[1], 0.1, 0.92, -0.01, 0.006), -0.84, 0.84, ['ink'], hull='none')
    m.prism(slant(cab[0], cab[1], 0.15, 0.87, -0.004, 0.014), -0.78, 0.78, ['glass'], hull='none')
    m.prism([(-2.18, 1.3), (-1.97, 1.98), (-1.3, 1.98), (-1.3, 1.3)], -0.926, 0.926, ['ink'], hull='none')
    m.prism([(-2.14, 1.34), (-1.95, 1.94), (-1.34, 1.94), (-1.34, 1.34)], -0.932, 0.932, ['glass'], hull='none')
    m.bx(-0.98, 0.98, -1.12, 2.45, 0.4, 2.7, 'paper', bevel=True)                      # cargo box
    for sx in (-1, 1):
        inner = 'l' if sx > 0 else 'r'
        x0, x1 = sorted((sx * 0.982, sx * 0.989))
        m.bx(x0, x1, -1.0, 2.33, 0.55, 1.3, 'shopTeal', hull='none', cull=inner)       # two-tone livery: teal skirt
        x0, x1 = sorted((sx * 0.982, sx * 0.992))
        m.bx(x0, x1, -1.0, 2.33, 1.3, 1.38, 'shopMustard', hull='none', cull=inner)    # mustard pinstripe
        if sx > 0:                                                                       # sun-disc emblem (no lettering)
            m.cy((0.982, 0.75, 1.95), 0.36, 0.36, 0.012, 'shopMustard', seg=10, rot=(0, 90, 0), hull='none')
            m.cy((0.986, 0.75, 1.95), 0.22, 0.22, 0.012, 'shopTeal', seg=8, rot=(0, 90, 0), hull='none')
        else:
            m.cy((-0.994, 0.75, 1.95), 0.36, 0.36, 0.012, 'shopMustard', seg=10, rot=(0, 90, 0), hull='none')
            m.cy((-0.998, 0.75, 1.95), 0.22, 0.22, 0.012, 'shopTeal', seg=8, rot=(0, 90, 0), hull='none')
        x0, x1 = sorted((sx * 0.5, sx * 0.8))
        m.bx(x0, x1, -2.435, -2.4, 0.75, 0.92, 'lamp', hull='none')
        m.bx(x0, x1, 2.45, 2.48, 0.6, 0.9, 'red', hull='none')
        x0, x1 = sorted((sx * 0.8, sx * 1.0))
        m.bx(x0, x1, -1.9, -1.78, 1.55, 1.85, 'iron')                                  # mirrors
    m.bx(-0.008, 0.008, 2.45, 2.47, 0.45, 2.62, 'ink', hull='none')                    # rear door split
    for sx in (-1, 1):
        m.bx(sx * 0.09 - 0.04, sx * 0.09 + 0.04, 2.45, 2.475, 1.3, 1.5, 'chrome', hull='none')
    m.bx(-0.92, 0.92, -2.5, -2.38, 0.3, 0.5, 'chrome')                                 # bumpers
    m.bx(-0.92, 0.92, 2.4, 2.5, 0.3, 0.46, 'iron')
    m.bx(-0.4, 0.4, -2.437, -2.4, 0.6, 0.95, 'iron', hull='none')                      # grille
    obj = make('Van', m, bevel=0.025, ao=ao)
    col_box(obj, 0, -0.96, 0.96, -2.48, -1.12, 0, 2.08)
    col_box(obj, 1, -0.99, 0.99, -1.12, 2.48, 0, 2.7)


def build_bus(pal, ao):
    """City bus 3 x 9: cream with a teal band, burgundy skirt, window band, two doors on its right (-X) side."""
    m = PM(pal)
    for sx in (-1, 1):
        for y in (-2.9, 2.75):
            wheel(m, sx * 1.285, y, 0.5, 0.3, seg=12)
    m.bx(-1.27, 1.27, -4.42, 4.42, 0.35, 3.05, 'carCream', bevel=True)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.2, sx * 1.278))
        m.bx(x0, x1, -3.9, 3.95, 1.6, 2.45, 'glassD', hull='none')                   # window band
        x0, x1 = sorted((sx * 1.22, sx * 1.276))
        m.bx(x0, x1, -4.3, 4.3, 1.25, 1.45, 'shopTeal', hull='none')                 # livery band
        x0, x1 = sorted((sx * 1.225, sx * 1.276))
        m.bx(x0, x1, -4.3, 4.3, 0.42, 0.68, 'shopBurg', hull='none')                 # skirt
        x0, x1 = sorted((sx * 1.205, sx * 1.284))
        for y in (-2.4, -0.9, 0.6, 2.1):
            m.bx(x0, x1, y - 0.06, y + 0.06, 1.58, 2.47, 'ink', hull='none')        # pillars
    for (y0, y1) in ((-3.75, -2.75), (0.45, 1.45)):                                    # doors (right side)
        m.bx(-1.29, -1.19, y0, y1, 0.4, 2.52, 'ink', hull='none')
        m.bx(-1.296, -1.235, y0 + 0.06, y1 - 0.06, 0.5, 2.44, 'glass', hull='none')
        m.bx(-1.302, -1.24, (y0 + y1) / 2 - 0.012, (y0 + y1) / 2 + 0.012, 0.52, 2.42, 'ink', hull='none')
    m.bx(-1.12, 1.12, -4.437, -4.4, 1.25, 2.6, 'ink', hull='none')                   # windshield
    m.bx(-1.06, 1.06, -4.445, -4.41, 1.3, 2.55, 'glass', hull='none')
    m.bx(-0.95, 0.95, -4.447, -4.41, 2.66, 2.95, 'ink', hull='none')                 # destination sign
    for x0, x1 in ((-0.8, -0.3), (-0.15, 0.6)):
        m.bx(x0, x1, -4.453, -4.42, 2.74, 2.87, 'amber', hull='none')
    m.bx(-1.0, 1.0, 4.4, 4.437, 1.9, 2.6, 'glassD', hull='none')                    # rear window
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.75, sx * 1.1))
        m.bx(x0, x1, -4.437, -4.4, 0.75, 0.95, 'lamp', hull='none')
        m.bx(x0, x1, 4.4, 4.437, 0.75, 1.05, 'red', hull='none')
        m.bm_((sx * 1.27, -4.3, 2.55), (sx * 1.45, -4.55, 2.45), 0.05, 'iron')
        x0, x1 = sorted((sx * 1.4, sx * 1.48))
        m.bx(x0, x1, -4.62, -4.48, 2.0, 2.45, 'iron')                                 # mirrors
    m.bx(-1.24, 1.24, -4.5, -4.36, 0.3, 0.6, 'iron')                                  # bumpers
    m.bx(-1.24, 1.24, 4.36, 4.5, 0.3, 0.6, 'iron')
    m.bx(-0.7, 0.7, 0.4, 2.3, 3.05, 3.38, 'steel')                                    # roof unit
    obj = make('Bus', m, bevel=0.03, ao=ao)
    col_box(obj, 0, -1.29, 1.29, -4.45, 4.45, 0, 3.05)


# ================================================================ street furniture
def build_lamp(pal, name, kind, ao):
    """Iron lamp post with a lantern and a city banner, on its own paving slab."""
    m = PM(pal)
    slab(m, [(0, 0)], kind)
    m.cy((0, 0, 0.05), 0.17, 0.12, 0.45, 'iron', seg=6)
    m.cy((0, 0, 0.5), 0.09, 0.09, 0.08, 'iron', seg=6)
    m.cy((0, 0, 0.58), 0.055, 0.05, 3.37, 'iron', seg=6)
    m.cy((0, 0, 3.95), 0.09, 0.12, 0.14, 'iron', seg=6)
    m.cy((0, 0, 4.09), 0.15, 0.2, 0.4, 'lamp', seg=6)
    m.cy((0, 0, 4.49), 0.25, 0.04, 0.28, 'iron', seg=6)
    m.cy((0, 0, 4.77), 0.03, 0.01, 0.16, 'iron', seg=5, hull='none')
    for z in (2.55, 3.55):
        m.bx(0.05, 0.42, -0.02, 0.02, z, z + 0.05, 'iron', hull='none')                # banner arms
    m.bx(0.08, 0.4, -0.012, 0.012, 2.62, 3.53, 'shopBurg')                             # banner
    m.bx(0.075, 0.405, -0.016, 0.016, 3.24, 3.36, 'shopMustard', hull='none')
    m.bx(0.075, 0.405, -0.016, 0.016, 2.74, 2.8, 'awnCream', hull='none')
    SD.lamp_detail(m)
    obj = make(name, m, ao=ao)
    col_box(obj, 0, -0.14, 0.14, -0.14, 0.14, 0, 4.6)


def build_tree(pal, ao):
    """Street tree in a square iron grate (the grate fills the cell, so it sits in any pavement)."""
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.054, 'iron', hull='none', cull='b')
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.04, 0.058, 'soil', hull='none', cull='b')
    for y in (-0.15, 0.15):
        m.bx(-0.31, 0.31, y - 0.02, y + 0.02, 0.05, 0.062, 'ironL', hull='none', cull='b')
    m.cy((0, 0, 0.044), 0.12, 0.09, 2.6, 'trunk', seg=7)
    m.bm_((0, 0, 1.9), (0.45, 0.18, 2.75), 0.08, 'trunk')
    m.sp((0, 0, 3.4), 1.2, 'leaf', seg=(8, 5), scale=(1, 1, 0.9))
    m.sp((0.62, 0.3, 2.95), 0.8, 'leaf2', seg=(7, 4))
    m.sp((-0.5, -0.38, 3.15), 0.85, 'leafD', seg=(7, 4))
    obj = make('StreetTree', m, ao=ao)
    col_box(obj, 0, -0.15, 0.15, -0.15, 0.15, 0, 2.5)


def build_furniture(pal, ao):
    """Sidewalk furniture, each on a paving slab: newspaper boxes, mailbox, hydrant, litter bin."""
    m = PM(pal)
    slab(m, [(0, 0)])
    for cx, c in ((-0.23, 'shopGreen'), (0.23, 'shopBurg')):
        m.bx(cx - 0.05, cx + 0.05, -0.05, 0.05, 0.05, 0.38, 'iron')
        m.bx(cx - 0.21, cx + 0.21, -0.19, 0.19, 0.38, 1.0, c, cull='t')
        m.bx(cx - 0.215, cx + 0.215, -0.195, 0.195, 1.0, 1.06, c)
        m.bx(cx - 0.17, cx + 0.17, -0.203, -0.177, 0.6, 0.92, 'ink', hull='none')       # window frame
        m.bx(cx - 0.15, cx + 0.15, -0.21, -0.17, 0.62, 0.9, 'paper', hull='none')        # today's paper
        m.bx(cx - 0.12, cx + 0.12, -0.215, -0.165, 0.81, 0.85, 'ink', hull='none')       # headline bar
        m.bx(cx - 0.11, cx + 0.03, -0.215, -0.165, 0.66, 0.76, 'glassD', hull='none')    # photo
        m.bx(cx + 0.06, cx + 0.14, -0.21, -0.17, 0.44, 0.54, 'iron', hull='none')        # coin box
    SD.newsbox_detail(m)
    obj = make('NewsBoxes', m, bevel=0.012, ao=ao)
    col_box(obj, 0, -0.45, 0.45, -0.21, 0.21, 0, 1.06)
    m = PM(pal)
    slab(m, [(0, 0)])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.2, sx * 0.24))
        m.bx(x0, x1, -0.24, 0.24, 0.05, 0.3, 'iron')
    m.bx(-0.24, 0.24, -0.26, 0.26, 0.3, 1.0, 'mailbox', bevel=True)
    m.cy((0, 0.255, 1.0), 0.24, 0.24, 0.51, 'mailbox', seg=12, rot=(90, 0, 0))
    m.bx(-0.13, 0.13, -0.272, -0.25, 0.86, 0.91, 'ink', hull='none')
    m.bx(-0.1, 0.1, -0.268, -0.25, 0.5, 0.68, 'paper', hull='none')
    m.bx(-0.04, 0.04, -0.29, -0.25, 1.12, 1.18, 'ironL', hull='none')
    SD.mailbox_detail(m)
    obj = make('Mailbox', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.25, 0.25, -0.27, 0.27, 0, 1.24)
    m = PM(pal)
    slab(m, [(0, 0)])
    m.cy((0, 0, 0.05), 0.17, 0.16, 0.07, 'red', seg=10)
    m.cy((0, 0, 0.12), 0.12, 0.12, 0.46, 'red', seg=10)
    m.cy((0, 0, 0.56), 0.15, 0.15, 0.06, 'red', seg=10)
    m.cy((0, 0, 0.62), 0.14, 0.06, 0.15, 'red', seg=10)
    m.cy((0, 0, 0.77), 0.035, 0.035, 0.05, 'ironL', seg=5)
    m.cy((0.11, 0, 0.42), 0.055, 0.055, 0.09, 'red', seg=8, rot=(0, 90, 0))
    m.cy((-0.2, 0, 0.42), 0.055, 0.055, 0.09, 'red', seg=8, rot=(0, 90, 0))
    m.cy((0, -0.1, 0.38), 0.07, 0.07, 0.1, 'red', seg=8, rot=(90, 0, 0))
    m.cy((0, -0.2, 0.38), 0.05, 0.05, 0.02, 'paper', seg=6, rot=(90, 0, 0), hull='none')
    SD.hydrant_detail(m)
    obj = make('Hydrant', m, ao=ao)
    col_box(obj, 0, -0.18, 0.18, -0.18, 0.18, 0, 0.8)
    m = PM(pal)
    slab(m, [(0, 0)])
    m.cy((0, 0, 0.05), 0.25, 0.27, 0.85, 'shopGreen', seg=12)
    for z in (0.22, 0.66):
        m.cy((0, 0, z), 0.265, 0.27, 0.05, 'ironL', seg=12, hull='none')
    m.cy((0, 0, 0.9), 0.29, 0.29, 0.05, 'iron', seg=12)
    m.cy((0, 0, 0.95), 0.22, 0.22, 0.01, 'ink', seg=12, hull='none')
    SD.bin_detail(m)
    obj = make('Bin', m, ao=ao)
    col_box(obj, 0, -0.29, 0.29, -0.29, 0.29, 0, 0.96)


def build_junk(pal, ao):
    """Alley / street clutter 1 x 1 (no paving): fruit crates, trash bags, cardboard boxes."""
    m = PM(pal)

    def crate(cx, cy, z, w, d, fruit):
        m.bx(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z, z + 0.3, 'woodL')
        for sy in (-1, 1):
            y0, y1 = sorted((cy + sy * d / 2, cy + sy * (d / 2 + 0.004)))
            m.bx(cx - w / 2 + 0.03, cx + w / 2 - 0.03, y0, y1, z + 0.13, z + 0.16, 'wood', hull='none')
        for i in range(2):
            fx = cx - w / 6 + i * w / 3
            m.sp((fx, cy + (0.07 if i % 2 else -0.07), z + 0.3), 0.085, fruit, seg=(5, 3), hull='none')
    crate(-0.22, 0, 0, 0.42, 0.56, 'brickO')
    crate(0.22, 0, 0, 0.42, 0.56, 'leaf2')
    m.parent = Matrix.Rotation(math.pi / 2, 4, 'Z')
    crate(0, 0, 0.3, 0.42, 0.56, 'red')
    m.parent = Matrix.Identity(4)
    obj = make('Crates', m, bevel=0.012, ao=ao)
    col_box(obj, 0, -0.44, 0.44, -0.29, 0.29, 0, 0.9)
    m = PM(pal)
    for (x, y, z, r, c) in ((-0.2, -0.12, 0.26, 0.3, 'bag'), (0.22, -0.05, 0.25, 0.28, 'leafD'), (0.0, 0.2, 0.24, 0.27, 'bag'), (0.02, -0.02, 0.6, 0.24, 'bag')):
        m.sp((x, y, z), r, c, seg=(7, 4), scale=(1.0, 0.9, 0.95))
        m.cy((x, y, z + r * 0.9), 0.05, 0.02, 0.12, c, seg=5, hull='none')
    obj = make('TrashBags', m, ao=ao)
    col_box(obj, 0, -0.46, 0.46, -0.4, 0.45, 0, 0.85)
    m = PM(pal)
    for (x0, x1, y0, y1, z0, z1) in ((-0.44, 0.06, -0.38, 0.12, 0, 0.45), (0.1, 0.44, -0.3, 0.32, 0, 0.38), (-0.36, 0.02, -0.3, 0.08, 0.45, 0.78), (0.12, 0.4, -0.22, 0.2, 0.38, 0.6)):
        m.bx(x0, x1, y0, y1, z0, z1, 'stoneS')
        m.bx((x0 + x1) / 2 - 0.04, (x0 + x1) / 2 + 0.04, y0 - 0.004, y1 + 0.004, z1 - 0.06, z1 + 0.004, 'stoneB', hull='none')
    obj = make('Boxes', m, bevel=0.01, ao=ao)
    col_box(obj, 0, -0.44, 0.44, -0.38, 0.32, 0, 0.78)


def build_barriers(pal, ao):
    """'=' red / white water-filled barriers (alternating along a run); 'j' concrete jersey barrier with tape."""
    prof = [(-0.25, 0), (0.25, 0), (0.25, 0.12), (0.18, 0.2), (0.18, 0.85), (0.12, 1.0), (-0.12, 1.0), (-0.18, 0.85), (-0.18, 0.2), (-0.25, 0.12)]
    for name, c in (('BarrierR', 'red'), ('BarrierW', 'paintW')):
        m = PM(pal)
        m.prism(prof, -0.48, 0.48, [c])
        for sy in (-1, 1):
            y0, y1 = sorted((sy * 0.18, sy * 0.186))
            m.bx(-0.3, 0.3, y0, y1, 0.5, 0.58, 'ink' if c == 'paintW' else 'paintW', hull='none')
        m.cy((-0.25, 0, 1.0), 0.06, 0.06, 0.03, 'iron', seg=6, hull='none')
        obj = make(name, m, bevel=0.02, ao=ao)
        col_box(obj, 0, -0.5, 0.5, -0.25, 0.25, 0, 1.0)
    m = PM(pal)
    jp = [(-0.3, 0), (0.3, 0), (0.3, 0.08), (0.12, 0.34), (0.08, 0.9), (-0.08, 0.9), (-0.12, 0.34), (-0.3, 0.08)]
    m.prism(jp, -0.49, 0.49, ['conc'])
    m.prism([(-0.103, 0.62), (0.103, 0.62), (0.0944, 0.74), (-0.0944, 0.74)], -0.495, 0.495, ['red', 'paintW', 'red', 'paintW'], hull='none')
    obj = make('Jersey', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.5, 0.5, -0.3, 0.3, 0, 0.9)


def build_planter(pal, ao):
    m = PM(pal)
    slab(m, [(0, 0)])
    m.bx(-0.46, 0.46, -0.36, 0.36, 0.05, 0.62, 'planter', cull='bt')
    m.bx(-0.48, 0.48, -0.38, 0.38, 0.62, 0.68, 'stoneC', cull='b')
    m.bx(-0.42, 0.42, -0.32, 0.32, 0.6, 0.7, 'soil', hull='none', cull='b')
    m.sp((-0.2, 0.0, 0.86), 0.3, 'leafD', seg=(7, 4), scale=(1, 0.9, 0.8))
    m.sp((0.22, 0.02, 0.84), 0.28, 'leaf', seg=(7, 4), scale=(1, 0.9, 0.8))
    for (x, y, z, c) in ((-0.32, -0.16, 0.92, 'flowerP'), (0.05, 0.14, 1.0, 'paintY'), (0.36, -0.12, 0.9, 'flowerP')):
        m.sp((x, y, z), 0.075, c, seg=(5, 3), hull='none')
    obj = make('Planter', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.48, 0.48, -0.38, 0.38, 0, 0.95)


def build_bench(pal, ao):
    """2 x 1 park bench on plaza paving, facing -Y."""
    m = PM(pal)
    slab(m, [(-0.5, 0), (0.5, 0)], 'plaza')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.8, sx * 0.88))
        m.bx(x0, x1, -0.26, 0.2, 0.05, 0.42, 'iron')                                  # legs
        m.bx(x0, x1, 0.17, 0.25, 0.42, 0.95, 'iron')                                   # back support
        x0, x1 = sorted((sx * 0.79, sx * 0.89))
        m.bx(x0, x1, -0.28, 0.15, 0.62, 0.67, 'iron')                                  # arm rest
        m.bx(x0 + 0.02, x1 - 0.02, -0.26, -0.2, 0.44, 0.62, 'iron', hull='none')
    for y in (-0.2, -0.06, 0.08):
        m.bx(-0.95, 0.95, y - 0.055, y + 0.055, 0.42, 0.47, 'woodL')
    for z in (0.6, 0.78):
        m.bx(-0.95, 0.95, 0.12, 0.17, z, z + 0.12, 'woodL')
    SD.bench_detail(m)
    obj = make('Bench', m, ao=ao)
    col_box(obj, 0, -0.95, 0.95, -0.28, 0.26, 0, 0.95)


def build_shelter(pal, ao):
    """Bus shelter 2 x 4: glass back on +X (game east, or north when turned), a poster light box, a bench."""
    m = PM(pal)
    slab(m, grid_cells(2, 4))
    for y in (-1.86, 1.86):
        for x in (0.86, -0.3):
            m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.05, 2.35, 'iron')            # posts
    m.bx(0.83, 0.86, -1.82, 1.82, 0.3, 2.2, 'glass', hull='none')                      # back glass
    m.bx(0.82, 0.9, -1.82, 1.82, 2.2, 2.28, 'iron', hull='none')
    m.bx(0.82, 0.9, -1.82, 1.82, 0.22, 0.3, 'iron', hull='none')
    m.bx(-0.26, 0.82, -1.85, -1.82, 0.3, 2.2, 'glass', hull='none')                    # side glass
    m.bx(-0.26, 0.82, 1.78, 1.9, 0.25, 2.25, 'iron')                                   # poster box
    m.bx(-0.2, 0.76, 1.76, 1.78, 0.32, 2.18, 'shopTeal', hull='none')
    m.bx(-0.05, 0.6, 1.755, 1.765, 1.1, 1.75, 'shopMustard', hull='none')
    m.bx(-0.12, 0.7, 1.755, 1.765, 0.55, 0.75, 'paper', hull='none')
    m.bx(-0.98, 0.98, -1.98, 1.98, 2.35, 2.45, 'iron')                                 # roof
    m.bx(-0.95, 0.95, -1.95, 1.95, 2.45, 2.48, 'glass', hull='none')
    m.bx(-0.99, -0.94, -1.99, 1.99, 2.2, 2.35, 'shopTeal')                             # roof fascia
    m.bx(0.3, 0.75, -1.2, 1.2, 0.45, 0.5, 'woodL')                                     # bench
    for y in (-1.0, 1.0):
        m.bx(0.45, 0.6, y - 0.04, y + 0.04, 0.05, 0.45, 'iron', hull='none')
    SD.shelter_detail(m)
    obj = make('Shelter', m, ao=ao)
    col_box(obj, 0, 0.8, 0.92, -1.92, 1.92, 0, 2.3)
    col_box(obj, 1, -0.32, 0.8, -1.92, -1.78, 0, 2.3)
    col_box(obj, 2, -0.32, 0.8, 1.76, 1.92, 0, 2.3)


def build_cart(pal, ao):
    """Food cart 2 x 2 under a striped umbrella, on plaza paving."""
    m = PM(pal)
    slab(m, grid_cells(2, 2), 'plaza')
    m.bx(-0.62, 0.62, -0.34, 0.34, 0.38, 1.05, 'steel', bevel=True)
    m.bx(-0.66, 0.66, -0.38, 0.38, 1.05, 1.1, 'stoneC')
    m.bx(-0.56, 0.56, -0.355, -0.34, 0.45, 0.98, 'shopTeal', hull='none')
    m.bx(-0.4, 0.4, -0.362, -0.35, 0.72, 0.86, 'paper', hull='none')
    m.bx(-0.3, 0.3, -0.368, -0.355, 0.77, 0.81, 'ink', hull='none')
    m.cy((-0.32, 0.44, 0.32), 0.3, 0.3, 0.06, 'iron', seg=10, rot=(90, 0, 0))
    m.cy((-0.32, -0.38, 0.32), 0.3, 0.3, 0.06, 'iron', seg=10, rot=(90, 0, 0))
    m.bx(0.5, 0.56, -0.05, 0.05, 0.05, 0.38, 'iron')
    m.bm_((0.62, -0.3, 0.95), (0.95, -0.3, 1.05), 0.04, 'iron')
    m.bm_((0.62, 0.3, 0.95), (0.95, 0.3, 1.05), 0.04, 'iron')
    m.bm_((0.95, -0.345, 1.05), (0.95, 0.345, 1.05), 0.045, 'iron')
    m.cy((0, 0, 1.1), 0.03, 0.03, 1.4, 'iron', seg=6)
    m.fan((0, 0, 2.18), 2.62, 1.05, 8, ['shopMustard', 'awnCream'])
    m.cy((0, 0, 2.62), 0.04, 0.02, 0.1, 'iron', seg=5, hull='none')
    for (x, c) in ((0.3, 'red'), (0.42, 'paintY')):
        m.cy((x, 0.15, 1.1), 0.04, 0.035, 0.18, c, seg=6)
    obj = make('Cart', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.68, 0.98, -0.42, 0.42, 0, 1.1)


# ================================================================ landmarks
def build_clocktower(pal, ao):
    """Clock tower 4 x 4: stone base with arched doors, brick shaft, four clock faces, open belfry, copper spire."""
    m = PM(pal)
    m.bx(-2.0, 2.0, -2.0, 2.0, 0, 0.45, 'stoneB', bevel=True)
    m.bx(-1.85, 1.85, -1.85, 1.85, 0.45, 0.62, 'stoneC', bevel=True)
    m.bx(-1.6, 1.6, -1.6, 1.6, 0.62, 4.6, 'stoneS')
    m.bx(-1.7, 1.7, -1.7, 1.7, 4.6, 4.85, 'stoneC')
    m.bx(-1.4, 1.4, -1.4, 1.4, 4.85, 11.2, 'brickR')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(min(sx * 1.25, sx * 1.45), max(sx * 1.25, sx * 1.45), min(sy * 1.25, sy * 1.45), max(sy * 1.25, sy * 1.45), 4.87, 11.22, 'stoneC')
    m.bx(-1.55, 1.55, -1.55, 1.55, 11.2, 11.45, 'stoneC')
    m.bx(-1.5, 1.5, -1.5, 1.5, 11.45, 14.2, 'stoneC')
    m.bx(-1.68, 1.68, -1.68, 1.68, 14.2, 14.5, 'stoneS')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(min(sx * 1.1, sx * 1.5), max(sx * 1.1, sx * 1.5), min(sy * 1.1, sy * 1.5), max(sy * 1.1, sy * 1.5), 14.5, 16.3, 'stoneC')
    m.bx(-1.05, 1.05, -1.05, 1.05, 14.5, 16.3, 'iron')                                  # shadowed belfry core
    m.cy((0, 0, 15.05), 0.55, 0.25, 0.75, 'gold', seg=10)                               # bell
    m.bx(-1.55, 1.55, -1.55, 1.55, 16.3, 16.6, 'stoneC')
    m.bx(-1.66, 1.66, -1.66, 1.66, 16.6, 16.8, 'stoneS')
    m.cy((0, 0, 16.8), 1.62 * math.sqrt(2), 0.0, 3.6, 'copper', seg=4, rot=(0, 0, 45))
    m.sp((0, 0, 20.45), 0.13, 'gold', seg=(6, 4))
    m.cy((0, 0, 20.55), 0.03, 0.02, 1.0, 'iron', seg=5, hull='none')
    m.bx(-0.32, 0.32, -0.02, 0.02, 21.2, 21.26, 'iron', hull='none')
    for k in range(4):   # the same detail on all four faces (written for the -Y face, turned)
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        m.bx(-0.48, 0.48, -1.62, -1.58, 0.6, 2.9, 'stoneC')                              # arched door
        m.cy((0, -1.584, 2.9), 0.48, 0.48, 0.032, 'stoneC', seg=12, rot=(90, 0, 0))
        m.bx(-0.4, 0.4, -1.632, -1.6, 0.606, 2.88, 'ink', hull='none')
        m.cy((0, -1.604, 2.9), 0.4, 0.4, 0.024, 'ink', seg=12, rot=(90, 0, 0), hull='none')
        m.cy((0, -1.608, 2.9), 0.34, 0.34, 0.03, 'glassW', seg=12, rot=(90, 0, 0), hull='none')
        m.bx(-0.34, 0.34, -1.645, -1.615, 0.612, 2.86, 'wood', hull='none')
        m.bx(-0.008, 0.008, -1.652, -1.62, 0.7, 2.8, 'ink', hull='none')
        m.bx(-0.3, 0.3, -1.42, -1.38, 6.2, 9.4, 'ink', hull='none')                      # shaft window
        m.cy((0, -1.384, 9.4), 0.3, 0.3, 0.032, 'ink', seg=10, rot=(90, 0, 0), hull='none')
        m.bx(-0.24, 0.24, -1.432, -1.39, 6.26, 9.38, 'glass', hull='none')
        m.cy((0, -1.394, 9.4), 0.24, 0.24, 0.034, 'glass', seg=10, rot=(90, 0, 0), hull='none')
        m.bx(-0.38, 0.38, -1.48, -1.38, 6.1, 6.2, 'stoneC')
        cz = 12.85                                                                         # clock
        m.cy((0, -1.49, cz), 1.1, 1.1, 0.04, 'ink', seg=16, rot=(90, 0, 0), hull='none')
        m.cy((0, -1.5, cz), 1.0, 1.0, 0.05, 'paper', seg=16, rot=(90, 0, 0))
        for (dx, dz, w, h) in ((0, 0.82, 0.07, 0.18), (0, -0.82, 0.07, 0.18), (0.82, 0, 0.18, 0.07), (-0.82, 0, 0.18, 0.07)):
            m.bx(dx - w / 2, dx + w / 2, -1.56, -1.53, cz + dz - h / 2, cz + dz + h / 2, 'ink', hull='none')
        for (ang, L, w, y0) in ((-60, 0.62, 0.07, -1.565), (145, 0.44, 0.09, -1.575)):
            a = math.radians(ang)
            m.cur = 'none'
            m.box((math.sin(a) * L / 2, y0 - 0.012, cz + math.cos(a) * L / 2), (w, 0.024, L), 'ink', rot=(0, ang, 0), bevel=False)
            m.cur = 'full'
        m.cy((0, -1.55, cz), 0.07, 0.07, 0.06, 'gold', seg=8, rot=(90, 0, 0), hull='none')
        m.bx(-0.55, 0.55, -1.08, -1.05, 14.5, 16.0, 'ink', hull='none')                  # belfry opening shadow
    m.parent = Matrix.Identity(4)
    obj = make('Landmark_ClockTower', m, bevel=0.02, ao=ao)
    col_box(obj, 0, -2.0, 2.0, -2.0, 2.0, 0, 0.62)
    col_box(obj, 1, -1.72, 1.72, -1.72, 1.72, 0.62, 16.8)


def build_fountain(pal, ao):
    """Fountain 6 x 6: round stone basin on a square terrace, two-tier centre piece with falling water."""
    m = PM(pal)
    m.bx(-3.0, 3.0, -3.0, 3.0, 0, 0.05, 'stoneS', hull='none')                          # terrace
    for sx in (-1, 1):                                                                     # border stripes
        x0, x1 = sorted((sx * 2.86, sx * 2.94))
        m.bx(x0, x1, -2.94, 2.94, 0.05, 0.054, 'brickR', hull='none')
        m.bx(-2.86, 2.86, x0, x1, 0.05, 0.054, 'brickR', hull='none')
    m.cy((0, 0, 0.05), 2.75, 2.75, 0.4, 'stoneS', seg=20)                               # basin
    ring(m, 2.5, 2.9, 0.45, 0.7, 20, 'stoneC')                                          # rim
    m.cy((0, 0, 0.455), 2.62, 2.62, 0.08, 'water', seg=20, hull='none')
    m.cy((0, 0, 0.45), 0.5, 0.42, 0.95, 'stoneC', seg=10)                               # pedestal
    m.cy((0, 0, 1.4), 0.3, 1.3, 0.38, 'stoneS', seg=14)                                 # lower bowl
    m.cy((0, 0, 1.78), 1.32, 1.32, 0.08, 'stoneC', seg=14)
    m.cy((0, 0, 1.8), 1.18, 1.18, 0.07, 'water', seg=14, hull='none')
    m.cy((0, 0, 1.86), 0.18, 0.14, 0.7, 'stoneC', seg=8)
    m.cy((0, 0, 2.56), 0.15, 0.7, 0.24, 'stoneS', seg=12)                               # upper bowl
    m.cy((0, 0, 2.8), 0.72, 0.72, 0.06, 'stoneC', seg=12)
    m.cy((0, 0, 2.82), 0.6, 0.6, 0.05, 'water', seg=12, hull='none')
    m.sp((0, 0, 3.02), 0.14, 'gold', seg=(8, 5))
    m.cy((0, 0, 3.14), 0.05, 0.03, 0.5, 'waterL', seg=6, hull='none')                  # jet
    m.sp((0, 0, 3.66), 0.1, 'waterL', seg=(6, 4), hull='none')
    m.cy((0, 0, 0.54), 1.36, 1.3, 1.24, 'waterL', seg=16, caps=False, hull='none')    # falling sheets
    m.cy((0, 0, 1.87), 0.76, 0.72, 0.93, 'waterL', seg=12, caps=False, hull='none')
    for k in range(4):                                                                    # spouts on the rim
        a = k * math.pi / 2 + math.pi / 4
        m.bm_((math.cos(a) * 2.7, math.sin(a) * 2.7, 0.62), (math.cos(a) * 2.25, math.sin(a) * 2.25, 0.95), 0.12, 'stoneC')
    obj = make('Landmark_Fountain', m, bevel=0.02, ao=ao)
    for i, (x0, x1, y0, y1) in enumerate(((-2.9, -2.4, -1.3, 1.3), (2.4, 2.9, -1.3, 1.3), (-1.3, 1.3, -2.9, -2.4), (-1.3, 1.3, 2.4, 2.9),
                                          (-2.45, -1.3, -2.45, -1.3), (1.3, 2.45, -2.45, -1.3), (-2.45, -1.3, 1.3, 2.45), (1.3, 2.45, 1.3, 2.45))):
        col_box(obj, i, x0, x1, y0, y1, 0, 0.7)
    col_box(obj, 8, -0.55, 0.55, -0.55, 0.55, 0, 3.1)


# ================================================================ backdrop (beyond the zone walls, fogged)
def build_backdrop(pal):
    m = PM(pal)                                                    # brick apartment tower with a rooftop water tank
    m.bx(-7, 7, -6, 6, 0, 30, 'bdA')
    m.bx(-7.3, 7.3, -6.3, 6.3, 30, 30.8, 'stoneS')
    for f in range(9):
        z = 3.5 + f * 2.9
        m.bx(-6.2, 6.2, -6.04, -5.9, z, z + 1.3, 'glassD', hull='none')
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 6.9, sx * 7.04))
            m.bx(x0, x1, -5.2, 5.2, z, z + 1.3, 'glassD', hull='none')
    for x in (-1.6, 1.6):
        for y in (-1.6, 1.6):
            m.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 30.8, 33.2, 'iron', hull='none')
    m.cy((0, 0, 33.2), 2.0, 2.0, 2.8, 'wood', seg=10)
    m.cy((0, 0, 36.0), 2.15, 0.2, 1.3, 'iron', seg=10)
    make('Backdrop_Tower', m)
    m = PM(pal)                                                    # cream office tower with setbacks
    for (h, z0, z1) in ((8, 0, 24), (6, 24.5, 36), (4, 36.5, 42)):
        m.bx(-h, h, -h, h, z0, z1, 'bdB' if h != 6 else 'stoneS')
        m.bx(-h - 0.3, h + 0.3, -h - 0.3, h + 0.3, z1, z1 + 0.5, 'stoneC')
        for k in range(h):
            x = -h + 1 + k * 2
            if x + 0.5 > h:
                break
            m.bx(x - 0.45, x + 0.45, -h - 0.06, -h + 0.06, z0 + 1.5, z1 - 1.0, 'glass', hull='none')
            for sx in (-1, 1):
                x0, x1 = sorted((sx * (h - 0.06), sx * (h + 0.06)))
                m.bx(x0, x1, x - 0.45, x + 0.45, z0 + 1.5, z1 - 1.0, 'glass', hull='none')
    m.cy((0, 0, 42.5), 0.15, 0.08, 6.0, 'iron', seg=5, hull='none')
    make('Backdrop_Office', m)
    m = PM(pal)                                                    # row of three townhouses
    for i, (c, h) in enumerate((('brickO', 12), ('bdA', 14), ('brickT', 11))):
        x0 = -12 + i * 8
        m.bx(x0, x0 + 8, -5, 5, 0, h, c)
        m.bx(x0 - 0.2 if i == 0 else x0 + 0.01, x0 + 8.2 if i == 2 else x0 + 7.99, -5.3, 5, h, h + 0.5 + i * 0.05, 'stoneC')
        for f in range(int((h - 2) / 3)):
            z = 2.5 + f * 3
            for k in range(3):
                x = x0 + 1.4 + k * 2.6
                m.bx(x - 0.55, x + 0.55, -5.08, -4.95, z, z + 1.6, 'glassD', hull='none')
    make('Backdrop_Row', m)
    m = PM(pal)                                                    # church tower and steeple
    m.bx(-3.5, 3.5, -3.5, 3.5, 0, 24, 'stoneS')
    m.bx(-3.8, 3.8, -3.8, 3.8, 24, 24.6, 'stoneC')
    m.bx(-3.0, 3.0, -3.0, 3.0, 24.6, 29, 'stoneC')
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        m.bx(-0.9, 0.9, -3.08, -2.96, 25.4, 28.2, 'iron', hull='none')
        if k % 2 == 0:
            m.cy((0, -3.5, 20.5), 1.4, 1.4, 0.1, 'paper', seg=12, rot=(90, 0, 0), hull='none')
        m.bx(-0.7, 0.7, -3.58, -3.46, 6, 16, 'glassD', hull='none')
    m.parent = Matrix.Identity(4)
    m.cy((0, 0, 29), 3.0 * math.sqrt(2), 0.0, 14.0, 'copper', seg=4, rot=(0, 0, 45))
    m.cy((0, 0, 43), 0.08, 0.04, 2.5, 'iron', seg=5, hull='none')
    make('Backdrop_Church', m)


# ================================================================ build
def build_kit_smallcity(ao):
    pal = Palette(FAM)
    build_walls(pal, False)
    build_floor_marks(pal)
    build_gate(pal, ao)
    build_trail(pal, ao)
    build_hatch(pal, ao)
    for name, c, taxi in (('Car_Taxi', 'taxi', True), ('Car_Red', 'carRed', False), ('Car_Blue', 'carBlue', False),
                          ('Car_Mint', 'carMint', False), ('Car_Cream', 'carCream', False)):
        build_car(pal, name, c, taxi, ao)
    build_van(pal, ao)
    build_bus(pal, ao)
    build_lamp(pal, 'Lamp', 'walk', ao)
    build_lamp(pal, 'LampP', 'plaza', ao)
    build_tree(pal, ao)
    build_furniture(pal, ao)
    build_junk(pal, ao)
    build_barriers(pal, ao)
    build_planter(pal, ao)
    build_bench(pal, ao)
    build_shelter(pal, ao)
    build_cart(pal, ao)
    build_clocktower(pal, ao)
    build_fountain(pal, ao)
    build_backdrop(pal)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_smallcity
