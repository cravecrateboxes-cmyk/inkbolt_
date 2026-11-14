"""INKBOLT asset family: kit-police ("Strike Team HQ", a police / special-forces base).

Rooms with their own wall and floor finish: a lobby (navy wainscot, gold rail, pale blue walls, 1 m two-tone tiles,
star emblem, front desk), a briefing room (oak panelling, cream walls, carpet tiles, projector screen, rows of
seats), armories (slate block walls with hazard dados, rubber floor, steel gun walls, workbenches, gear shelving),
an operations room (console walls with big screens, desk pods), a locker room, a firing range (acoustic panels,
booths, robot-silhouette targets, rubber backstop, baffles), a vehicle garage (block walls with a safety stripe,
roller doors, bay lines, SWAT vans, holding cells, tool chests, drums and tyres).

Conventions (see ib_lib.py / kit_util.py): 1 cell = 1 m; a piece's origin is the centre of its cell / footprint on
the floor; Blender -Y = game +Z (the piece's front); Blender Z = up.
  * wall modules: face at y = -0.5 (the cell edge), nothing proud of it within 6 cm of the module ends, so modules
    meeting in a concave corner never overlap; the theme's chooser picks the room style from the floor layer
  * floor finishes ('Floor_*', 'Emblem') are flat faces without an outline, placed by the zone files' floor layer
    ("@layer 0.008"); ceiling pieces ('Ceil_*', 'Beam*', 'Duct', 'Baffle', 'Lintel') hang from their origin on the
    4 m ceiling plane ("@layer 4")
  * armory mounts (game prefab-local x, height, z) are listed in src/data/themes/police.js: a gun's back rests on the
    rack's mount plane 3.5 cm in front of the board (pegs reach 2.7 cm), a mod / item stands on its surface
Coplanar overlapping faces are avoided by construction (check_zfight fails the build otherwise).
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
from fam_kit_smallcity import PM, post_hull
from kit_util import col_box, tag
import police_detail as pd

FAM = 'kit-police'
PFX = 'KIT_POLICE_'
ib_lib.GLB[FAM] = 'fps-kit-police.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # lobby / office walls
    ('navy', '#2D4F8E'), ('navy2', '#213C6E'), ('gold', '#F0B530'), ('wall', '#D6E2EE'), ('wall2', '#B5C8DD'),
    ('cream', '#EFE5CF'), ('oak', '#B9824F'), ('oak2', '#93613A'),
    # armory / garage / range / cells walls
    ('slate', '#4D5A72'), ('slate2', '#3D485E'), ('block', '#B7C0B4'), ('block2', '#A4AE9F'),
    ('gconc', '#C9C2B2'), ('gconc2', '#A79F8F'), ('acou', '#5F6F93'), ('acou2', '#4A5878'),
    ('tile', '#E8EFEE'), ('mint', '#7DC9B8'),
    # floors
    ('flA', '#B8C8DA'), ('flB', '#A3B6CC'), ('grout', '#8FA2B8'), ('carpet', '#4A6595'), ('carpet2', '#425C8A'),
    ('rubber', '#5C6577'), ('rubber2', '#515A6B'), ('conc', '#AEB0AE'), ('conc2', '#9C9E9C'), ('range', '#6C6F78'),
    ('paleA', '#DCE6E4'), ('paleB', '#C7D5D2'),
    # props
    ('steel', '#93A0B2'), ('steel2', '#6D7A8D'), ('chrome', '#CBD3DD'), ('black', '#2A2B33'), ('rubberK', '#34343C'),
    ('olive', '#6F7B4A'), ('olive2', '#59643B'), ('sand', '#D2BC86'), ('khaki', '#B5A170'), ('peg', '#CDAE7E'),
    ('peg2', '#BE9C6A'), ('glass', '#A6D8F0'), ('screen', '#46C2F2'), ('screen2', '#1F3E66'), ('light', '#FFF4CF'),
    ('yellow', '#F7CF2E'), ('orange', '#F0883A'), ('green', '#4FA86A'), ('leaf', '#3F9358'), ('clay', '#C4704A'),
    ('cork', '#C99A62'), ('blue', '#3B7EEB'), ('target', '#F3EEE2'), ('flC', '#7F96B3'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
TRIS = {}
H = 4.0
HT = 0.02


def new(pal):
    return PM(pal)


def fin(name, m, ao, hull=HT, cols=None, flat=False):
    full = PFX + name
    obj = build_object(full, m, 0.0, 0.0 if flat else hull, ao=ao and not flat)
    if flat:
        strip_hull(obj)
    else:
        post_hull(obj, m.hmode)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, col in enumerate(cols or []):
        c, hlf = col[0], col[1]
        e = bpy.data.objects.new('%s_COL%d' % (full, i), None)
        e.empty_display_type = 'CUBE'
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def quad(m, x0, y0, x1, y1, color, z=0.0):
    """one up-facing flat face (floor finish)"""
    vs = [m.bm.verts.new(m.parent @ Vector(p)) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    return tag(m, [m.bm.faces.new(vs)], color)


def poly(m, pts, color, z=0.0):
    vs = [m.bm.verts.new(m.parent @ Vector((x, y, z))) for x, y in pts]
    return tag(m, [m.bm.faces.new(vs)], color)


def clip(poly_pts, a, b, c):
    """clip a convex polygon to a*x + b*y <= c"""
    out = []
    n = len(poly_pts)
    for i in range(n):
        p, q = poly_pts[i], poly_pts[(i + 1) % n]
        dp, dq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def stripes(m, x0, y0, x1, y1, width, colors, z=0.0):
    """45 degree stripes over a rectangle (hazard paint)"""
    sq = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    s0, s1 = x0 + y0, x1 + y1
    k = 0
    s = s0 - (s0 % width) - width
    while s < s1:
        p = clip(clip(sq, -1, -1, -s), 1, 1, s + width)
        if len(p) >= 3:
            poly(m, p, colors[int(round((s - s0) / width)) % len(colors)], z)
        s += width
        k += 1


# ================================================================ walls (face at y = -0.5, back at +0.5)
# style bands: (z0, z1, colour, face depth: how far in front of the core face at y = -0.42)
STY = {
    'L': [(0.0, 0.1, 'navy2', 0.08), (0.1, 1.02, 'navy', 0.07), (1.02, 1.12, 'gold', 0.08), (1.12, 3.62, 'wall', 0.05),
          (3.62, 3.72, 'navy', 0.07), (3.72, 4.0, 'wall2', 0.06)],
    'O': [(0.0, 0.1, 'oak2', 0.08), (0.1, 0.95, 'oak', 0.065), (0.95, 1.03, 'oak2', 0.08), (1.03, 3.62, 'cream', 0.05),
          (3.62, 3.7, 'oak', 0.065), (3.7, 4.0, 'wall', 0.06)],
    'A': [(0.0, 0.12, 'black', 0.08), (0.12, 1.15, 'slate', 0.07), (1.15, 1.25, 'yellow', 0.08), (1.25, 3.62, 'block', 0.05),
          (3.62, 4.0, 'slate2', 0.065)],
    'G': [(0.0, 0.12, 'black', 0.08), (0.12, 1.0, 'gconc2', 0.07), (1.0, 1.14, 'yellow', 0.08), (1.14, 3.62, 'gconc', 0.05),
          (3.62, 4.0, 'slate2', 0.065)],
    'R': [(0.0, 0.1, 'black', 0.08), (0.1, 0.95, 'acou2', 0.07), (0.95, 1.03, 'steel2', 0.08), (1.03, 3.62, 'acou2', 0.04),
          (3.62, 4.0, 'slate2', 0.065)],
    'C': [(0.0, 0.1, 'mint', 0.08), (0.1, 1.45, 'tile', 0.07), (1.45, 1.55, 'mint', 0.08), (1.55, 3.62, 'wall', 0.05),
          (3.62, 4.0, 'wall2', 0.065)],
}
CORE = -0.42


def face_y(S, z):
    """y of the wall face at height z (band in front of the core)"""
    for z0, z1, c, d in STY[S]:
        if z0 <= z < z1:
            return CORE - d
    return CORE - 0.05


def wall_base(m, S, skip=(), fit=True):
    """the style's bands across the module (fronts, tops and bottoms only: neighbours hide the ends and the back)"""
    if fit:
        pd.wall_fit(m, S, lambda z: face_y(S, z))
    for i, (z0, z1, c, d) in enumerate(STY[S]):
        if i in skip:
            continue
        m.bx(-0.5, 0.5, CORE - d, CORE, z0, z1, c, cull='klr' + ('b' if z0 == 0 else '') + ('t' if z1 >= H else ''))


def band_split(m, S, idx, x0, x1, keep=None):
    """one band drawn only outside x0..x1 (a door / screen goes in the gap)"""
    z0, z1, c, d = STY[S][idx]
    for a, b in ((-0.5, x0), (x1, 0.5)):
        if b - a > 0.001:
            m.bx(a, b, CORE - d, CORE, z0, z1, c, cull='k' + ('l' if a <= -0.5 else '') + ('r' if b >= 0.5 else '') + ('b' if z0 == 0 else '') + ('t' if z1 >= H else ''))


def d(m, S, x0, x1, z0, z1, proud, color, back_in=0.01, hull='full'):
    """wall detail: front `proud` m in front of the face at z0, back sunk 1 cm into the band; ends stay >= 6 cm in"""
    y = face_y(S, z0)
    m.bx(x0, x1, y - proud, y + back_in, z0, z1, color, cull='k', hull=hull)


def corner_piece(pal, ao, S):
    m = new(pal)
    for z0, z1, c, dd in STY[S]:
        h = 0.5 - (0.08 - dd)          # deeper recess for the recessed bands, flush for the proud ones
        m.bx(-h, h, -h, h, z0, z1, c, cull=('b' if z0 == 0 else '') + ('t' if z1 >= H else ''))
    pd.corner_guard_post(m, S, STY)
    fin('Corner' + S, m, ao)


def window(m, S, z0=1.35, z1=3.05, w=0.38, blinds=True):
    y = face_y(S, 2.0)
    m.bx(-w, w, y - 0.012, y + 0.01, z0, z1, 'glass', cull='klrtb')                   # glass
    for a, b in ((-w, -w + 0.05), (w - 0.05, w)):
        m.bx(a, b, y - 0.045, y + 0.01, z0, z1 - 0.06, 'steel2', cull='k')
    m.bx(-w, w, y - 0.045, y + 0.01, z1 - 0.06, z1, 'steel2', cull='k')
    m.bx(-w - 0.03, w + 0.03, y - 0.07, y + 0.01, z0 - 0.06, z0, 'steel', cull='k')   # sill
    m.bx(-0.01, 0.01, y - 0.036, y - 0.011, z0, z1 - 0.06, 'steel2', cull='k')        # mullion
    if blinds:
        for k in range(5):
            zz = z1 - 0.2 - k * 0.12
            m.bx(-w + 0.05, w - 0.05, y - 0.03, y - 0.016, zz - 0.035, zz, 'paper', cull='k', hull='none')


def notice(m, S, x0=-0.36, x1=0.36, z0=1.75, z1=2.65):
    y = face_y(S, z0)
    m.bx(x0, x1, y - 0.03, y + 0.01, z0, z1, 'steel2', cull='k')
    m.bx(x0 + 0.03, x1 - 0.03, y - 0.04, y - 0.03, z0 + 0.03, z1 - 0.03, 'cork', cull='k', hull='none')
    sheets = ((-0.2, 2.42, 0.2, 0.26, 'paper'), (0.08, 2.35, 0.22, 0.3, 'white'), (0.2, 2.0, 0.16, 0.2, 'yellow'),
              (-0.17, 2.0, 0.18, 0.24, 'wall'))
    for k, (x, z, w, h, c) in enumerate(sheets):
        if x - w / 2 < x0 + 0.04 or x + w / 2 > x1 - 0.04:
            continue
        m.bx(x - w / 2, x + w / 2, y - 0.044 - 0.003 * (k % 2), y - 0.04, z - h / 2, z + h / 2, c, cull='k', hull='none')
        m.bx(x - 0.012, x + 0.012, y - 0.054, y - 0.044, z + h / 2 - 0.04, z + h / 2 - 0.016, 'red', cull='k', hull='none')
    for k, (x, z, w) in enumerate(((-0.2, 2.47, 0.12), (0.08, 2.4, 0.14), (-0.17, 2.04, 0.1))):   # text lines
        m.bx(x - w / 2, x + w / 2, y - 0.05 - 0.003 * (k % 2), y - 0.044, z, z + 0.012, 'ink', cull='k', hull='none')


def star_pts(r, inner=0.42, a0=math.pi / 2):
    return [((r if i % 2 == 0 else r * inner) * math.cos(a0 + i * math.pi / 5),
             (r if i % 2 == 0 else r * inner) * math.sin(a0 + i * math.pi / 5)) for i in range(10)]


def star(m, cx, z, y, r, color, t=0.006, hull='full'):
    """five-point star prism in the wall plane: back face at y (dropped), front face t further toward -Y"""
    bm = m.bm
    P = star_pts(r)
    fr = [bm.verts.new(m.parent @ Vector((cx + px, y - t, z + pz))) for px, pz in P]
    bk = [bm.verts.new(m.parent @ Vector((cx + px, y, z + pz))) for px, pz in P]
    faces = [bm.faces.new(list(reversed(fr)))]
    for i in range(10):
        j = (i + 1) % 10
        faces.append(bm.faces.new((fr[i], fr[j], bk[j], bk[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    tag(m, faces, color)
    if hull != 'full':
        m.hmode[m.nshape] = hull


def star_flat(m, r, color, z):
    """flat five-point star facing up (floor emblem)"""
    return poly(m, star_pts(r), color, z)


def badge(m, S, z=2.45, r=0.3):
    y = face_y(S, z)
    m.cy((0, y + 0.01, z), r, r, 0.04, 'gold', seg=12, rot=(90, 0, 0))                # cylinder grows toward -Y
    m.cy((0, y - 0.03, z), r * 0.8, r * 0.8, 0.012, 'navy', seg=12, rot=(90, 0, 0), hull='none')
    star(m, 0, z, y - 0.042, r * 0.75, 'gold', t=0.004)


def build_walls(pal, ao):
    for S in STY:
        if S != 'R':   # the range's plain module is the padded one (acoustic)
            m = new(pal); wall_base(m, S); pd.wall_top(m, S, lambda z: face_y(S, z)); fin('W' + S, m, ao)
        corner_piece(pal, ao, S)

    # ---- lobby
    m = new(pal); wall_base(m, 'L'); window(m, 'L'); fin('WL_Window', m, ao)
    m = new(pal); wall_base(m, 'L'); badge(m, 'L'); fin('WL_Badge', m, ao)
    m = new(pal); wall_base(m, 'L'); notice(m, 'L'); fin('WL_Board', m, ao)
    m = new(pal); wall_base(m, 'L'); clock(m, 'L'); fin('WL_Clock', m, ao)
    m = new(pal); wall_base(m, 'L'); banner(m, 'L'); fin('WL_Flag', m, ao)
    m = new(pal); door(m, 'L', 'navy2', 'gold'); fin('WL_Door', m, ao)
    m = new(pal); wall_base(m, 'L'); sign(m, 'L', 'navy2', 'gold', 'paper'); fin('WL_Sign', m, ao)
    m = new(pal); wall_base(m, 'L'); photos(m, 'L'); fin('WL_Photos', m, ao)
    m = new(pal); wall_base(m, 'O'); photos(m, 'O'); fin('WO_Photos', m, ao)
    # ---- briefing / office
    m = new(pal); wall_base(m, 'O'); window(m, 'O'); fin('WO_Window', m, ao)
    m = new(pal); wall_base(m, 'O'); whiteboard(m, 'O'); fin('WO_White', m, ao)
    m = new(pal); wall_base(m, 'O'); mapboard(m, 'O'); fin('WO_Map', m, ao)
    m = new(pal); wall_base(m, 'O'); clock(m, 'O'); fin('WO_Clock', m, ao)
    m = new(pal); wall_base(m, 'O'); banner(m, 'O'); fin('WO_Flag', m, ao)
    m = new(pal); wall_base(m, 'O'); notice(m, 'O'); fin('WO_Board', m, ao)
    m = new(pal); door(m, 'O', 'oak', 'oak2'); fin('WO_Door', m, ao)
    for part in 'LMR':
        m = new(pal); wall_base(m, 'O'); screen(m, 'O', part); fin('WO_Screen' + part, m, ao)
    # ---- armory
    m = new(pal); wall_base(m, 'A'); sign(m, 'A', 'yellow', 'ink', 'ink', 'rifle'); fin('WA_Sign', m, ao)
    m = new(pal); wall_base(m, 'A'); cage(m, 'A'); fin('WA_Cage', m, ao)
    m = new(pal); wall_base(m, 'A'); firstaid(m, 'A'); fin('WA_Aid', m, ao)
    m = new(pal); wall_base(m, 'A'); extinguisher(m, 'A'); fin('WA_Ext', m, ao)
    m = new(pal); door(m, 'A', 'steel2', 'yellow'); fin('WA_Door', m, ao)
    m = new(pal); wall_base(m, 'A'); notice(m, 'A'); fin('WA_Board', m, ao)
    # ---- garage
    for part in 'LMR':
        m = new(pal); roller(m, 'G', part); fin('WG_Roller' + part, m, ao)
    m = new(pal); wall_base(m, 'G'); toolboard(m, 'G'); fin('WG_Tools', m, ao)
    m = new(pal); wall_base(m, 'G'); panel(m, 'G'); fin('WG_Panel', m, ao)
    m = new(pal); wall_base(m, 'G'); extinguisher(m, 'G'); fin('WG_Ext', m, ao)
    m = new(pal); wall_base(m, 'G'); window(m, 'G', z0=2.2, z1=3.3, blinds=False); fin('WG_Window', m, ao)
    m = new(pal); wall_base(m, 'G'); sign(m, 'G', 'blue', 'white', 'white', 'parking'); fin('WG_Sign', m, ao)
    m = new(pal); wall_base(m, 'G'); notice(m, 'G'); fin('WG_Board', m, ao)
    # ---- range
    m = new(pal); acoustic(m); fin('WR', m, ao)          # replaces the plain band module: padded squares
    m = new(pal); backstop(m); fin('WR_Back', m, ao)
    m = new(pal); acoustic(m); sign(m, 'R', 'white', 'red', 'ink', 'rules'); fin('WR_Sign', m, ao)
    m = new(pal); acoustic(m); beacon(m, 'R'); fin('WR_Light', m, ao)
    m = new(pal); wall_base(m, 'R'); window(m, 'R', z0=1.15, z1=2.4, blinds=False); fin('WR_Window', m, ao)
    # ---- cells / lockers
    m = new(pal); wall_base(m, 'C'); sign(m, 'C', 'mint', 'ink', 'white', 'cell'); fin('WC_Sign', m, ao)
    m = new(pal); wall_base(m, 'C'); notice(m, 'C'); fin('WC_Board', m, ao)
    m = new(pal); wall_base(m, 'C'); clock(m, 'C'); fin('WC_Clock', m, ao)
    for S in 'LOAGC':
        m = new(pal); wall_base(m, S); lamp(m, S); fin('W%s_Lamp' % S, m, ao)
    m = new(pal); door(m, 'C', 'steel', 'mint'); fin('WC_Door', m, ao)


def clock(m, S, z=2.85):
    y = face_y(S, z)
    m.cy((0, y + 0.01, z), 0.2, 0.2, 0.05, 'ink', seg=14, rot=(90, 0, 0))
    m.cy((0, y - 0.04, z), 0.17, 0.17, 0.008, 'white', seg=14, rot=(90, 0, 0), hull='none')
    m.box((0.0, y - 0.052, z + 0.05), (0.018, 0.004, 0.11), 'ink', bevel=False)
    m.box((0.045, y - 0.056, z), (0.1, 0.004, 0.016), 'ink', bevel=False)
    m.box((0.0, y - 0.06, z - 0.06), (0.006, 0.004, 0.11), 'red', bevel=False)


def banner(m, S):
    y = face_y(S, 2.0)
    m.bx(-0.33, 0.33, y - 0.04, y + 0.01, 3.2, 3.26, 'gold', cull='k')                 # hanging rod
    m.bx(-0.28, 0.28, y - 0.025, y + 0.01, 1.7, 3.2, 'navy', cull='k')
    m.bx(-0.28, -0.22, y - 0.03, y - 0.025, 1.7, 3.2, 'gold', cull='k', hull='none')
    m.bx(0.22, 0.28, y - 0.03, y - 0.025, 1.7, 3.2, 'gold', cull='k', hull='none')
    m.bx(-0.22, 0.22, y - 0.03, y - 0.025, 2.0, 2.06, 'white', cull='k', hull='none')
    star(m, 0, 2.6, y - 0.03, 0.22, 'gold', t=0.004)
    for sx in (-0.2, 0.0, 0.2):                                                        # tassels
        m.bx(sx - 0.03, sx + 0.03, y - 0.022, y - 0.005, 1.6, 1.7, 'gold', cull='k')


def door(m, S, leaf, trim):
    """a closed door: bands split around a 1.0 x 2.25 opening, frame, leaf with a vision panel and push bar"""
    for i, (z0, z1, c, dd) in enumerate(STY[S]):
        if z0 < 2.3:
            band_split(m, S, i, -0.44, 0.44)
            if z1 > 2.3:
                m.bx(-0.44, 0.44, CORE - dd, CORE, 2.3, z1, c, cull='kb' + ('t' if z1 >= H else ''))
        else:
            m.bx(-0.5, 0.5, CORE - dd, CORE, z0, z1, c, cull='klr' + ('t' if z1 >= H else ''))
    y = CORE - 0.05
    m.bx(-0.44, 0.44, y + 0.01, CORE + 0.0, 0.0, 2.3, 'black', cull='klrtb')            # reveal back
    for a, b in ((-0.44, -0.39), (0.39, 0.44)):
        m.bx(a, b, y - 0.03, y + 0.01, 0, 2.25, 'steel2', cull='kb')
    m.bx(-0.44, 0.44, y - 0.03, y + 0.01, 2.25, 2.3, 'steel2', cull='k')
    m.bx(-0.39, 0.39, y - 0.005, y + 0.02, 0.0, 2.25, leaf, cull='kb')
    m.bx(-0.13, 0.13, y - 0.012, y - 0.005, 1.35, 1.85, 'glass', cull='k', hull='none')
    m.bx(-0.3, 0.3, y - 0.06, y - 0.005, 1.0, 1.05, 'chrome', cull='k')
    m.bx(-0.16, 0.16, y - 0.012, y - 0.005, 1.95, 2.05, trim, cull='k', hull='none')    # door sign
    m.bx(-0.39, 0.39, y - 0.012, y - 0.005, 0.0, 0.18, 'steel', cull='kb', hull='none')  # kick plate
    pd.door_fit(m, y)


def sign(m, S, plate, ink, edge, icon='text'):
    """wall sign: framed plate with a pictogram (rifle, parking P, rules list, cell door) or a line of block letters"""
    z = 2.75
    y = face_y(S, z)
    m.bx(-0.42, 0.42, y - 0.035, y + 0.01, z - 0.2, z + 0.2, edge, cull='k')
    m.bx(-0.39, 0.39, y - 0.045, y - 0.035, z - 0.17, z + 0.17, plate, cull='k', hull='none')
    f, f2 = y - 0.0485, y - 0.052          # pictogram layers, each >= 3 mm in front of the last

    def mark(x0, x1, z0, z1, c=ink, front=f):
        m.bx(x0, x1, front, y - 0.045, z + z0, z + z1, c, cull='k', hull='none')
    if icon == 'rifle':                    # side view of a rifle over a stencil bar
        mark(-0.3, 0.3, 0.02, 0.07)                      # receiver + barrel
        mark(-0.34, -0.18, -0.03, 0.06, front=f2)        # stock
        mark(-0.06, 0.02, -0.1, 0.02)                    # magazine
        mark(-0.14, -0.09, -0.08, 0.02)                  # grip
        mark(-0.1, 0.12, 0.07, 0.1, front=f2)            # scope
        mark(-0.33, 0.33, -0.15, -0.13)
    elif icon == 'parking':                # white P on blue
        mark(-0.09, -0.04, -0.12, 0.12)
        mark(-0.04, 0.08, 0.07, 0.12)
        mark(-0.04, 0.08, -0.02, 0.03)
        mark(0.05, 0.1, 0.03, 0.07, front=f2)
    elif icon == 'rules':                  # red header and rule lines
        mark(-0.36, 0.36, 0.08, 0.15)
        for k in range(4):
            mark(-0.32, 0.12 + 0.05 * (k % 2), -0.13 + k * 0.05, -0.11 + k * 0.05, 'ink')
    elif icon == 'cell':                   # barred door
        mark(-0.12, 0.12, -0.14, 0.13)
        for k in range(4):
            x = -0.08 + k * 0.055
            mark(x - 0.01, x + 0.01, -0.12, 0.11, 'white', front=f2)
        mark(0.2, 0.32, -0.02, 0.02)
    else:                                  # lettered plate (vector glyphs, ib_text) + underline
        ib_text.draw(m, 'RECEPTION', 0.0, f, z - 0.06, 0.14, ink, face='y-', font='cond', maxw=0.62)
        mark(-0.3, 0.3, -0.13, -0.11)


def photos(m, S):
    """honour wall: three framed portraits and a plaque"""
    y = face_y(S, 2.2)
    for k, x in enumerate((-0.28, 0.0, 0.28)):
        zc = 2.3 + (0.06 if k == 1 else 0.0)
        m.bx(x - 0.11, x + 0.11, y - 0.025, y + 0.01, zc - 0.15, zc + 0.15, 'oak2' if S != 'L' else 'gold', cull='k')
        m.bx(x - 0.08, x + 0.08, y - 0.029, y - 0.025, zc - 0.12, zc + 0.12, 'flA', cull='k', hull='none')
        m.bx(x - 0.04, x + 0.04, y - 0.033, y - 0.029, zc - 0.02, zc + 0.06, 'clay', cull='k', hull='none')
        m.bx(x - 0.06, x + 0.06, y - 0.033, y - 0.029, zc - 0.12, zc - 0.03, 'navy', cull='k', hull='none')
    m.bx(-0.2, 0.2, y - 0.02, y + 0.01, 1.85, 2.0, 'oak', cull='k')
    m.bx(-0.16, 0.16, y - 0.024, y - 0.02, 1.88, 1.97, 'gold', cull='k', hull='none')


def whiteboard(m, S):
    y = face_y(S, 1.8)
    m.bx(-0.44, 0.44, y - 0.03, y + 0.01, 1.3, 2.45, 'chrome', cull='k')
    m.bx(-0.41, 0.41, y - 0.036, y - 0.03, 1.33, 2.42, 'white', cull='k', hull='none')
    m.bx(-0.4, 0.4, y - 0.08, y + 0.01, 1.26, 1.3, 'chrome', cull='k')                 # marker tray
    for k, (x0, x1, z, c) in enumerate(((-0.33, -0.05, 2.25, 'blue'), (-0.33, 0.12, 2.12, 'ink'), (-0.33, 0.02, 2.0, 'ink'),
                                         (0.05, 0.32, 1.72, 'red'), (-0.3, -0.12, 1.62, 'green'))):
        m.bx(x0, x1, y - 0.04 - 0.003 * (k % 2), y - 0.036, z, z + 0.018, c, cull='k', hull='none')
    m.cy((0.2, y - 0.039, 1.95), 0.08, 0.08, 0.004, 'red', seg=10, rot=(90, 0, 0), hull='none')
    m.cy((0.2, y - 0.043, 1.95), 0.06, 0.06, 0.003, 'white', seg=10, rot=(90, 0, 0), hull='none')


def mapboard(m, S):
    y = face_y(S, 1.8)
    m.bx(-0.44, 0.44, y - 0.03, y + 0.01, 1.4, 2.6, 'oak2', cull='k')
    m.bx(-0.4, 0.4, y - 0.036, y - 0.03, 1.44, 2.56, 'paleA', cull='k', hull='none')
    for k, (x0, x1, z0, z1, c) in enumerate(((-0.36, -0.1, 2.1, 2.5, 'paleB'), (0.0, 0.36, 2.15, 2.5, 'leaf'),
                                             (-0.36, 0.05, 1.5, 1.95, 'paleB'), (0.12, 0.36, 1.5, 2.0, 'flA'),
                                             (-0.4, 0.4, 2.0, 2.06, 'yellow'), (-0.06, 0.0, 1.44, 2.56, 'yellow'))):
        m.bx(x0, x1, y - 0.04 - 0.003 * k, y - 0.036, z0, z1, c, cull='k', hull='none')
    for x, z in ((-0.2, 2.3), (0.2, 1.7), (-0.25, 1.65), (0.15, 2.35)):
        m.cy((x, y - 0.05, z), 0.025, 0.025, 0.03, 'red', seg=6, rot=(90, 0, 0))


def screen(m, S, part):
    """projector screen across several modules: L / M / R (left end, middle, right end as seen from the room)"""
    y = face_y(S, 2.5)
    a = -0.5 if part != 'L' else -0.42
    b = 0.5 if part != 'R' else 0.42
    m.bx(a, b, y - 0.02, y + 0.01, 1.35, 3.25, 'white', cull='k' + ('l' if part != 'L' else '') + ('r' if part != 'R' else ''))
    m.bx(a, b, y - 0.026, y - 0.02, 1.35, 1.43, 'ink', cull='k' + ('l' if part != 'L' else '') + ('r' if part != 'R' else ''), hull='none')
    m.bx(a, b, y - 0.026, y - 0.02, 3.17, 3.25, 'ink', cull='k' + ('l' if part != 'L' else '') + ('r' if part != 'R' else ''), hull='none')
    m.cy((a, y - 0.1, 3.33), 0.08, 0.08, b - a, 'steel2', seg=8, rot=(0, 90, 0), caps=part != 'M',
         hull='noside' if part == 'M' else 'full')
    if part == 'L':
        m.bx(a, a + 0.06, y - 0.026, y - 0.02, 1.43, 3.17, 'ink', cull='k', hull='none')
    if part == 'R':
        m.bx(b - 0.06, b, y - 0.026, y - 0.02, 1.43, 3.17, 'ink', cull='k', hull='none')
    if part == 'M':   # the projected slide: a badge and title bars
        m.bx(-0.3, 0.3, y - 0.024, y - 0.02, 2.75, 2.9, 'navy', cull='k', hull='none')
        m.bx(-0.3, 0.1, y - 0.024, y - 0.02, 2.4, 2.48, 'screen2', cull='k', hull='none')
        m.bx(-0.3, 0.2, y - 0.024, y - 0.02, 2.2, 2.28, 'screen2', cull='k', hull='none')
        m.bx(-0.3, 0.0, y - 0.024, y - 0.02, 2.0, 2.08, 'screen2', cull='k', hull='none')


def cage(m, S):
    y = face_y(S, 2.0)
    m.bx(-0.43, 0.43, y - 0.005, y + 0.01, 1.36, 2.99, 'slate2', cull='klrtb', hull='none')
    m.bx(-0.44, 0.44, y - 0.05, y + 0.01, 1.3, 1.36, 'steel2', cull='k')
    m.bx(-0.44, 0.44, y - 0.05, y + 0.01, 2.99, 3.05, 'steel2', cull='k')
    for sx in (-1, 1):
        m.bx(-0.44 if sx < 0 else 0.38, -0.38 if sx < 0 else 0.44, y - 0.05, y + 0.01, 1.36, 2.99, 'steel2', cull='k')
    for k in range(5):
        x = -0.28 + k * 0.14
        m.bx(x - 0.008, x + 0.008, y - 0.03, y - 0.015, 1.36, 2.99, 'steel', cull='k', hull='none')
    for k in range(7):
        z = 1.55 + k * 0.2
        m.bx(-0.38, 0.38, y - 0.045, y - 0.03, z - 0.008, z + 0.008, 'steel', cull='k', hull='none')
    pd.cage_fit(m, y)


def firstaid(m, S):
    y = face_y(S, 1.6)
    m.bx(-0.22, 0.22, y - 0.14, y + 0.01, 1.45, 1.95, 'white', cull='k')
    m.bx(-0.04, 0.04, y - 0.146, y - 0.14, 1.58, 1.82, 'red', cull='k', hull='none')
    m.bx(-0.12, -0.04, y - 0.146, y - 0.14, 1.66, 1.74, 'red', cull='k', hull='none')
    m.bx(0.04, 0.12, y - 0.146, y - 0.14, 1.66, 1.74, 'red', cull='k', hull='none')
    m.bx(-0.16, 0.16, y - 0.012, y + 0.01, 2.1, 2.3, 'green', cull='k')
    m.bx(-0.1, 0.1, y - 0.018, y - 0.012, 2.17, 2.23, 'white', cull='k', hull='none')


def extinguisher(m, S):
    y = face_y(S, 1.3)
    m.bx(-0.06, 0.06, y - 0.05, y + 0.01, 1.1, 1.18, 'black', cull='k')                # bracket
    m.cy((0, y - 0.13, 0.55), 0.09, 0.09, 0.6, 'red', seg=10)
    m.cy((0, y - 0.13, 1.15), 0.09, 0.03, 0.08, 'red', seg=10)
    m.cy((0, y - 0.13, 1.23), 0.025, 0.025, 0.06, 'black', seg=6)
    m.bx(-0.014, 0.014, y - 0.24, y - 0.14, 1.24, 1.27, 'black')
    m.bx(-0.06, 0.06, y - 0.225, y - 0.215, 0.75, 0.95, 'white', hull='none')          # label (on the tank front)
    m.bx(-0.15, 0.15, y - 0.012, y + 0.01, 1.85, 2.15, 'red', cull='k')                # sign above
    m.bx(-0.05, 0.05, y - 0.018, y - 0.012, 1.9, 2.1, 'white', cull='k', hull='none')
    pd.call_point(m, S, lambda z: face_y(S, z))


def toolboard(m, S):
    y = face_y(S, 2.0)
    m.bx(-0.45, 0.45, y - 0.025, y + 0.01, 1.4, 2.6, 'peg', cull='k')
    for k, (x, z0, z1, c) in enumerate(((-0.33, 1.6, 2.35, 'red'), (-0.2, 1.7, 2.4, 'steel2'), (-0.08, 1.75, 2.4, 'steel2'),
                                         (0.05, 1.65, 2.35, 'orange'), (0.2, 1.8, 2.45, 'steel2'), (0.33, 1.6, 2.3, 'blue'))):
        m.bx(x - 0.025, x + 0.025, y - 0.05, y - 0.025, z0, z1, c, cull='k')
        m.bx(x - 0.05, x + 0.05, y - 0.055, y - 0.025, z1 - 0.1, z1 + 0.01, c if k % 2 else 'steel', cull='k')
    m.bx(-0.4, 0.4, y - 0.03, y - 0.025, 1.45, 1.52, 'ink', cull='k', hull='none')


def panel(m, S):
    y = face_y(S, 1.8)
    m.bx(-0.3, 0.3, y - 0.18, y + 0.01, 1.3, 2.3, 'steel', cull='k')
    m.bx(-0.26, 0.26, y - 0.186, y - 0.18, 1.34, 2.26, 'steel2', cull='k', hull='none')
    m.bx(-0.1, 0.1, y - 0.192, y - 0.186, 2.05, 2.18, 'yellow', cull='k', hull='none')
    m.bx(0.18, 0.22, y - 0.21, y - 0.186, 1.7, 1.85, 'black', cull='k')
    m.bx(-0.05, 0.05, y - 0.08, y + 0.01, 2.3, 3.98, 'steel2', cull='k')                # conduit
    m.bx(-0.05, 0.05, y - 0.08, y + 0.01, 0.12, 1.3, 'steel2', cull='kb')


def roller(m, S, part):
    """roller door over several modules (L / M / R): slats, guide rails at the ends, a box header"""
    for i, (z0, z1, c, dd) in enumerate(STY[S]):
        if z1 <= 3.35:
            continue
        m.bx(-0.5, 0.5, CORE - dd, CORE, max(z0, 3.35), z1, c, cull='klr' + ('t' if z1 >= H else ''))
    a = -0.5 if part != 'L' else -0.34
    b = 0.5 if part != 'R' else 0.34
    y = CORE - 0.03
    side = ('l' if part != 'L' else '') + ('r' if part != 'R' else '')
    for k in range(11):
        z0 = k * 0.3
        m.bx(a, b, y - 0.02 * (k % 2), CORE, z0, z0 + 0.3, 'steel' if k % 2 else 'chrome', cull='k' + side + ('b' if k == 0 else ''),
             hull='noside' if side else 'full')
    if part == 'L':
        m.bx(-0.5, -0.34, CORE - 0.08, CORE, 0, 3.35, 'black', cull='kb')
        m.bx(-0.5, -0.34, CORE - 0.085, CORE - 0.08, 0.0, 1.2, 'yellow', cull='kb', hull='none')
    if part == 'R':
        m.bx(0.34, 0.5, CORE - 0.08, CORE, 0, 3.35, 'black', cull='kb')
        m.bx(0.34, 0.5, CORE - 0.085, CORE - 0.08, 0.0, 1.2, 'yellow', cull='kb', hull='none')
    m.bx(a, b, CORE - 0.12, CORE, 3.3, 3.6, 'slate', cull='k' + side, hull='noside' if side else 'full')
    for k in range(4):   # hazard chevrons along the bottom slat
        x = a + 0.08 + k * (b - a - 0.16) / 3.0
        m.bx(x - 0.05, x + 0.05, y - 0.006, y + 0.003, 0.05, 0.25, 'yellow' if k % 2 else 'ink', cull='k', hull='none')
    pd.roller_fit(m, part, a, b)


def acoustic(m):
    """range wall: padded squares over a dark frame"""
    for i, (z0, z1, c, dd) in enumerate(STY['R']):
        if i == 3:
            continue
        m.bx(-0.5, 0.5, CORE - dd, CORE, z0, z1, c, cull='klr' + ('b' if z0 == 0 else '') + ('t' if z1 >= H else ''))
    z0, z1, c, dd = STY['R'][3]
    m.bx(-0.5, 0.5, CORE - dd, CORE, z0, z1, 'acou2', cull='klr')
    for row in range(2):
        for col in range(2):
            x = -0.235 + col * 0.47
            zc = 1.7 + row * 1.25
            m.bx(x - 0.215, x + 0.215, CORE - dd - 0.04, CORE - dd + 0.01, zc - 0.58, zc + 0.58, 'acou' if (row + col) % 2 else 'navy', cull='k')


def backstop(m):
    """bullet trap: dark rubber slope over a steel apron in front of the range wall"""
    wall_base(m, 'R')
    y = CORE - 0.04
    for k in range(5):   # louvred rubber blocks, each a little higher and further back
        z = 0.15 + k * 0.5
        m.bx(-0.5, 0.5, y - 0.32 + k * 0.06, y + 0.0, z, z + 0.44, 'rubberK' if k % 2 else 'black', cull='klr' + ('b' if k == 0 else ''))
    m.bx(-0.5, 0.5, y - 0.36, y - 0.32 + 0.0, 0.0, 0.15, 'yellow', cull='klrb')
    m.bx(-0.5, 0.5, y - 0.02, y + 0.0, 2.65, 2.9, 'steel2', cull='klr')


def lamp(m, S):
    """wall light at 2.8 m: an up-light sconce in the lobby / office / cells, a caged bulkhead lamp elsewhere"""
    y = face_y(S, 2.8)
    if S in 'LOC':
        m.bx(-0.07, 0.07, y - 0.02, y + 0.01, 2.62, 2.88, 'navy2' if S != 'O' else 'oak2', cull='k')
        m.cy((0, y - 0.13, 2.7), 0.08, 0.15, 0.2, 'gold' if S == 'L' else 'chrome', seg=10, caps=True)
        m.cy((0, y - 0.13, 2.9), 0.13, 0.13, 0.004, 'light', seg=10, hull='none')
        m.bx(-0.015, 0.015, y - 0.06, y - 0.02, 2.72, 2.76, 'navy2', cull='k')
    else:
        m.bx(-0.16, 0.16, y - 0.03, y + 0.01, 2.62, 2.9, 'black', cull='k')
        m.bx(-0.13, 0.13, y - 0.11, y - 0.03, 2.65, 2.87, 'light')
        for k in range(3):
            x = -0.09 + k * 0.09
            m.bx(x - 0.008, x + 0.008, y - 0.125, y - 0.11, 2.64, 2.88, 'black', cull='k')


def beacon(m, S):
    y = face_y(S, 2.6)
    m.bx(-0.08, 0.08, y - 0.08, y + 0.01, 2.5, 2.58, 'black', cull='k')
    m.cy((0, y - 0.12, 2.58), 0.07, 0.07, 0.04, 'black', seg=10)
    m.cy((0, y - 0.12, 2.62), 0.06, 0.05, 0.14, 'red', seg=10)
    m.bx(-0.26, 0.26, y - 0.012, y + 0.01, 2.0, 2.3, 'red', cull='k')
    m.bx(-0.2, 0.2, y - 0.018, y - 0.012, 2.08, 2.22, 'white', cull='k', hull='none')


# ================================================================ floor finishes (flat, no outline, at the layer height)
def floor_tiles(pal):
    def tile(name, c, g='grout', gw=0.03, extra=None):
        m = new(pal)
        quad(m, -0.5 + gw, -0.5 + gw, 0.5, 0.5, c)
        quad(m, -0.5, -0.5, -0.5 + gw, 0.5, g)
        quad(m, -0.5 + gw, -0.5, 0.5, -0.5 + gw, g)
        fin(name, m, False, flat=True)
    tile('Floor_LobbyA', 'flA')
    tile('Floor_LobbyB', 'flB')
    tile('Floor_Rubber', 'rubber', 'rubber2', 0.025)
    tile('Floor_PaleA', 'paleA', 'paleB', 0.02)
    tile('Floor_Border', 'flC', 'grout')
    m = new(pal)   # carpet tiles: quarter-turned pile shows as two tones per alternate cell
    quad(m, -0.5, -0.5, 0.5, 0.5, 'carpet'); fin('Floor_CarpetA', m, False, flat=True)
    m = new(pal)
    quad(m, -0.5, -0.5, 0.5, 0.5, 'carpet2'); fin('Floor_CarpetB', m, False, flat=True)
    m = new(pal)
    quad(m, -0.5, -0.5, 0.5, 0.5, 'conc'); fin('Floor_Conc', m, False, flat=True)
    m = new(pal)   # concrete with an expansion joint on its west edge
    quad(m, -0.48, -0.5, 0.5, 0.5, 'conc'); quad(m, -0.5, -0.5, -0.48, 0.5, 'conc2'); fin('Floor_ConcJ', m, False, flat=True)
    m = new(pal)   # concrete with joints on its west and south edges
    quad(m, -0.48, -0.48, 0.5, 0.5, 'conc'); quad(m, -0.5, -0.5, -0.48, 0.5, 'conc2'); quad(m, -0.48, -0.5, 0.5, -0.48, 'conc2')
    fin('Floor_ConcJ2', m, False, flat=True)
    m = new(pal)   # concrete with an oil stain
    pts = [(math.cos(a / 8 * 2 * math.pi) * 0.3 * (1 + 0.25 * math.sin(a * 2.3)), math.sin(a / 8 * 2 * math.pi) * 0.22) for a in range(8)]
    sq = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    poly(m, pts, 'conc2')
    for i in range(8):   # fan the square around the stain (8 quads from the stain edge to the square)
        p, q = pts[i], pts[(i + 1) % 8]
        a0, a1 = math.atan2(p[1], p[0]), math.atan2(q[1], q[0])
        def onsq(a):
            c, s = math.cos(a), math.sin(a)
            k = 0.5 / max(abs(c), abs(s))
            return (c * k, s * k)
        P, Q = onsq(a0), onsq(a1)
        ring = [p, q, Q]
        # include a square corner between P and Q if the edge crosses one
        for cx, cy in sq:
            ac = math.atan2(cy, cx)
            lo, hi = a0, a1 if a1 > a0 else a1 + 2 * math.pi
            acc = ac if ac >= lo else ac + 2 * math.pi
            if lo < acc < hi:
                ring.append((cx, cy))
        ring.append(P)
        poly(m, ring, 'conc')
    fin('Floor_ConcStain', m, False, flat=True)
    m = new(pal)   # garage line along X through the cell centre
    quad(m, -0.5, -0.5, 0.5, -0.06, 'conc'); quad(m, -0.5, -0.06, 0.5, 0.06, 'yellow'); quad(m, -0.5, 0.06, 0.5, 0.5, 'conc')
    fin('Floor_ConcLine', m, False, flat=True)
    m = new(pal)   # armory rubber with a yellow keep-clear line along X
    quad(m, -0.475, -0.5, 0.5, -0.05, 'rubber'); quad(m, -0.475, -0.05, 0.5, 0.05, 'yellow'); quad(m, -0.475, 0.05, 0.5, 0.475, 'rubber')
    quad(m, -0.475, 0.475, 0.5, 0.5, 'rubber2'); quad(m, -0.5, -0.5, -0.475, 0.5, 'rubber2')
    fin('Floor_RubberLine', m, False, flat=True)
    m = new(pal)
    quad(m, -0.5, -0.5, 0.5, 0.5, 'range'); fin('Floor_Range', m, False, flat=True)
    m = new(pal)   # red firing line along X
    quad(m, -0.5, -0.5, 0.5, -0.08, 'range'); quad(m, -0.5, -0.08, 0.5, 0.08, 'red'); quad(m, -0.5, 0.08, 0.5, 0.5, 'range')
    fin('Floor_RangeLine', m, False, flat=True)
    m = new(pal)   # lane line along Z on the cell's west edge
    quad(m, -0.5, -0.5, -0.45, 0.5, 'white'); quad(m, -0.45, -0.5, 0.5, 0.5, 'range'); fin('Floor_RangeLane', m, False, flat=True)
    m = new(pal)
    stripes(m, -0.5, -0.5, 0.5, 0.5, 0.25, ['yellow', 'ink']); fin('Floor_Hazard', m, False, flat=True)
    m = new(pal)   # entry mat: ribbed rubber with a navy border band on the cell's north edge
    for k in range(4):
        quad(m, -0.5, -0.5 + k * 0.25, 0.5, -0.5 + (k + 1) * 0.25, 'rubberK' if k % 2 else 'black')
    fin('Floor_Mat', m, False, flat=True)
    # floor emblem 4 x 4: lobby tiles (checker matching (c + r) % 2 with the NW cell 'A'), navy disc, gold ring, star
    m = new(pal)
    for i in range(4):
        for j in range(4):
            x0, y1 = -2 + i, 2 - j
            c = 'flA' if (i + j) % 2 == 0 else 'flB'
            quad(m, x0 + 0.03, y1 - 1, x0 + 1, y1 - 0.03, c)
            quad(m, x0, y1 - 1, x0 + 0.03, y1, 'grout')
            quad(m, x0 + 0.03, y1 - 0.03, x0 + 1, y1, 'grout')
    m.cy((0, 0, 0), 1.75, 1.75, 0.004, 'gold', seg=28)
    m.cy((0, 0, 0.004), 1.6, 1.6, 0.004, 'navy', seg=28)
    m.cy((0, 0, 0.008), 1.32, 1.32, 0.004, 'gold', seg=28)
    m.cy((0, 0, 0.012), 1.24, 1.24, 0.004, 'navy2', seg=28)
    star_flat(m, 1.12, 'gold', 0.019)
    m.cy((0, 0, 0.0225), 0.2, 0.2, 0.004, 'navy', seg=12)
    fin('Emblem', m, False, flat=True)


# ================================================================ ceiling (origin on the ceiling plane, hanging down)
def build_ceiling(pal, ao):
    m = new(pal)   # recessed light panel
    m.bx(-0.45, 0.45, -0.3, 0.3, -0.06, -0.005, 'steel', cull='t')
    m.bx(-0.4, 0.4, -0.25, 0.25, -0.07, -0.06, 'light', cull='t', hull='none')
    fin('Ceil_Panel', m, ao)
    m = new(pal)   # high-bay lamp on a stem
    m.cy((0, 0, -0.62), 0.025, 0.025, 0.615, 'black', seg=6, caps=False)
    m.bx(-0.09, 0.09, -0.09, 0.09, -0.05, -0.005, 'black', cull='t')
    m.cy((0, 0, -0.9), 0.38, 0.12, 0.28, 'navy2', seg=12)
    m.cy((0, 0, -0.91), 0.32, 0.32, 0.01, 'light', seg=12, hull='none', caps=True)
    fin('Ceil_HighBay', m, ao)
    m = new(pal)   # steel beam module along X (web + bottom flange)
    m.bx(-0.5, 0.5, -0.07, 0.07, -0.36, -0.005, 'navy2', cull='lrt', hull='noside')
    m.bx(-0.5, 0.5, -0.13, 0.13, -0.42, -0.36, 'navy2', cull='lr', hull='noside')
    fin('Beam', m, ao)
    m = new(pal)   # pale bulkhead beam (lobby, offices) along X
    m.bx(-0.5, 0.5, -0.12, 0.12, -0.34, -0.005, 'wall2', cull='lrt', hull='noside')
    m.bx(-0.5, 0.5, -0.14, 0.14, -0.4, -0.34, 'navy', cull='lr', hull='noside')
    fin('BeamL', m, ao)
    m = new(pal)   # crossing: X beam plus a Z beam stopping at its web
    m.bx(-0.5, 0.5, -0.07, 0.07, -0.36, -0.005, 'navy2', cull='lrt', hull='noside')
    m.bx(-0.5, 0.5, -0.13, 0.13, -0.42, -0.36, 'navy2', cull='lr', hull='noside')
    for sy in (-1, 1):
        y0, y1 = (0.07, 0.5) if sy > 0 else (-0.5, -0.07)
        m.bx(-0.07, 0.07, y0, y1, -0.36, -0.005, 'navy2', cull='t' + ('k' if sy > 0 else 'f'))
        y0, y1 = (0.13, 0.5) if sy > 0 else (-0.5, -0.13)
        m.bx(-0.13, 0.13, y0, y1, -0.417, -0.36, 'navy2', cull=('k' if sy > 0 else 'f'))
    fin('BeamX', m, ao)
    m = new(pal)   # rectangular duct along X with a flange joint
    m.bx(-0.5, 0.5, -0.3, 0.3, -0.5, -0.12, 'chrome', cull='lr', hull='noside')
    m.bx(0.42, 0.5, -0.32, 0.32, -0.52, -0.1, 'steel', cull='r', hull='noside')
    m.bx(-0.03, 0.03, -0.32, 0.32, -0.12, -0.005, 'steel2', cull='t')                  # hanger
    fin('Duct', m, ao)
    m = new(pal)   # cable tray module along X: side rails, a mesh floor, a bundle of cables, a hanger
    for sy in (-0.16, 0.16):
        m.bx(-0.5, 0.5, sy - 0.012, sy + 0.012, -0.62, -0.54, 'steel', cull='lr', hull='noside')
    m.bx(-0.5, 0.5, -0.148, 0.148, -0.62, -0.61, 'steel2', cull='lr', hull='noside')
    for k, (y, z, r, c) in enumerate(((-0.09, -0.57, 0.035, 'black'), (-0.01, -0.575, 0.03, 'blue'), (0.07, -0.57, 0.035, 'black'),
                                       (0.03, -0.52, 0.025, 'orange'), (-0.06, -0.515, 0.025, 'red'))):
        m.cy((-0.5, y, z), r, r, 1.0, c, seg=6, rot=(0, 90, 0), caps=False, hull='noside')
    m.bx(-0.008, 0.008, 0.162, 0.178, -0.6, -0.005, 'black', cull='t', hull='none')    # hanger
    m.bx(-0.02, 0.02, -0.19, 0.19, -0.64, -0.62, 'black')
    fin('Ceil_Tray', m, ao)
    m = new(pal)   # target carrier rail module (along X; the range turns it along the lanes) with a hanger
    m.bx(-0.5, 0.5, -0.035, 0.035, -0.7, -0.62, 'steel2', cull='lr', hull='noside')
    m.bx(-0.012, 0.012, -0.012, 0.012, -0.62, -0.005, 'black', cull='t', hull='none')
    fin('Ceil_Rail', m, ao)
    m = new(pal)   # doorway lintel (bulkhead) over a two-cell wall: 0.85 m deep
    m.bx(-0.5, 0.5, -0.5, 0.5, -0.85, -0.12, 'wall', cull='lrt', hull='noside')
    m.bx(-0.5, 0.5, -0.5, 0.5, -0.12, 0.0, 'navy', cull='lrt', hull='noside')
    m.bx(-0.5, 0.5, -0.5, 0.5, -0.9, -0.85, 'navy2', cull='lrt', hull='noside')
    fin('Lintel', m, ao)
    m = new(pal)   # env ceiling light for the corridors (origin on the ceiling plane)
    m.box((0, 0, -0.045), (1.2, 0.5, 0.08), 'steel', bevel=False)
    m.box((0, 0, -0.09), (1.1, 0.4, 0.01), 'light', bevel=False)
    fin('CeilLight', m, ao)


# ================================================================ small furniture helpers (local frame: front -Y)
def at(m, x, y, yaw=0.0, z=0.0):
    """push a local frame; returns the previous parent (restore with m.parent = prev)"""
    prev = m.parent
    m.parent = prev @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
    return prev


def chair(m, x, y, yaw=0.0, seat='navy'):
    """office chair, sitter facing -Y (backrest on +Y)"""
    P = at(m, x, y, yaw)
    m.bx(-0.23, 0.23, -0.21, 0.21, 0.42, 0.5, seat)
    m.bx(-0.21, 0.21, 0.2, 0.27, 0.55, 0.98, seat)
    m.bx(-0.03, 0.03, 0.21, 0.25, 0.5, 0.55, 'black')
    m.cy((0, 0, 0.065), 0.028, 0.028, 0.36, 'black', seg=6, caps=False)
    m.bx(-0.26, 0.26, -0.03, 0.03, 0.02, 0.06, 'black')
    m.bx(-0.03, 0.03, -0.26, 0.26, 0.025, 0.066, 'black')
    m.parent = P


def monitor(m, x, y, z, yaw=0.0, w=0.52, h=0.32, ui='screen'):
    """flat screen on a stand, screen facing -Y"""
    P = at(m, x, y, yaw, z)
    m.bx(-0.1, 0.1, -0.06, 0.08, 0.0, 0.015, 'black')
    m.bx(-0.025, 0.025, 0.03, 0.06, 0.015, 0.2, 'black')
    m.bx(-w / 2, w / 2, -0.01, 0.03, 0.14, 0.14 + h, 'black')
    m.bx(-w / 2 + 0.025, w / 2 - 0.025, -0.014, -0.01, 0.165, 0.115 + h, 'screen2', cull='k', hull='none')
    for k, (x0, x1, z0, z1) in enumerate(((-0.6, 0.6, 0.78, 0.9), (-0.6, -0.05, 0.5, 0.7), (0.05, 0.6, 0.3, 0.7), (-0.6, -0.05, 0.25, 0.42))):
        m.bx(x0 * (w / 2 - 0.04), x1 * (w / 2 - 0.04), -0.018, -0.014, 0.14 + h * z0, 0.14 + h * z1,
             ui if k != 1 else 'green', cull='k', hull='none')
    m.parent = P


def keyboard(m, x, y, z, yaw=0.0):
    P = at(m, x, y, yaw, z)
    m.bx(-0.22, 0.22, -0.07, 0.07, 0.0, 0.025, 'black')
    m.bx(-0.2, 0.2, -0.05, 0.05, 0.025, 0.03, 'steel2', hull='none')
    m.parent = P


def mug(m, x, y, z, c='white'):
    m.cy((x, y, z), 0.04, 0.04, 0.1, c, seg=8)
    m.cy((x, y, z + 0.1), 0.03, 0.03, 0.004, 'oak2', seg=8, hull='none')


def papers(m, x, y, z, yaw=0.0, c='paper'):
    P = at(m, x, y, yaw, z)
    m.bx(-0.11, 0.11, -0.15, 0.15, 0.0, 0.01, c)
    m.bx(-0.08, 0.05, -0.1, -0.09, 0.01, 0.014, 'ink', hull='none')
    m.bx(-0.08, 0.08, -0.06, -0.05, 0.01, 0.014, 'ink', hull='none')
    m.parent = P


def helmet(m, x, y, z, c='navy', s=1.0):
    m.sp((x, y, z), 0.15 * s, c, seg=(8, 4), scale=(1, 1.1, 0.85))
    m.bx(x - 0.15 * s, x + 0.15 * s, y - 0.17 * s, y + 0.17 * s, z - 0.03 * s, z, c if c != 'navy' else 'navy2')


# ================================================================ armory furniture (mount pieces; see police.js)
SLOT_X = (-0.72, 0.72)
SLOT_Z = (1.05, 1.75)


def build_rack(pal, ao):
    """3 x 1 gun wall: steel frame, pegboard with four framed slots (2 x 2), labels, a drawer cabinet underneath and
    a header with the badge. Board face y = 0.45; slot panels 0.447; labels 0.444; pegs reach 0.42; guns hang with
    their backs at y = 0.415 (game z = -0.415)."""
    m = new(pal)
    for sx in (-1, 1):
        px = (1.42, 1.5) if sx > 0 else (-1.5, -1.42)
        m.bx(px[0], px[1], 0.36, 0.5, 0.0, 2.2, 'steel2', cull='kt')
    m.bx(-0.03, 0.03, 0.36, 0.45, 0.62, 2.2, 'steel2', cull='k')
    m.bx(-1.42, 1.42, 0.45, 0.49, 0.62, 2.2, 'peg', cull='klr')
    for x in SLOT_X:
        for z in SLOT_Z:
            m.bx(x - 0.66, x + 0.66, 0.447, 0.45, z - 0.33, z + 0.3, 'peg2', cull='k', hull='none')
            m.bx(x - 0.22, x + 0.22, 0.444, 0.447, z - 0.31, z - 0.21, 'paper', cull='k', hull='none')
            m.bx(x - 0.18, x - 0.02, 0.4405, 0.444, z - 0.305, z - 0.29, 'ink', cull='k', hull='none')
            for px in (-0.3, 0.3):
                m.bx(x + px - 0.012, x + px + 0.012, 0.42, 0.447, z - 0.072, z - 0.048, 'black', cull='k')
                m.bx(x + px - 0.012, x + px + 0.012, 0.42, 0.432, z - 0.048, z - 0.02, 'black', cull='k')
    # header: navy box, gold stripe, badge, label plates
    m.bx(-1.5, 1.5, 0.36, 0.5, 2.2, 2.45, 'navy', cull='k')
    m.bx(-1.42, 1.42, 0.355, 0.36, 2.22, 2.25, 'gold', cull='k', hull='none')
    m.cy((0, 0.36, 2.33), 0.1, 0.1, 0.02, 'gold', seg=10, rot=(90, 0, 0))
    m.cy((0, 0.34, 2.33), 0.065, 0.065, 0.006, 'navy2', seg=10, rot=(90, 0, 0), hull='none')
    for x in SLOT_X:
        m.bx(x - 0.3, x + 0.3, 0.355, 0.36, 2.28, 2.4, 'paper', cull='k', hull='none')
        m.bx(x - 0.24, x + 0.1, 0.352, 0.355, 2.32, 2.36, 'ink', cull='k', hull='none')
    # base cabinet with drawers
    m.bx(-1.415, 1.415, 0.03, 0.45, 0.06, 0.62, 'steel', cull='k')
    m.bx(-1.4, 1.4, 0.06, 0.45, 0.0, 0.06, 'black', cull='kb')
    for x in SLOT_X:
        for k in range(3):
            z0 = 0.09 + k * 0.175
            m.bx(x - 0.64, x + 0.64, 0.015, 0.03, z0, z0 + 0.155, 'steel2', cull='k')
            m.bx(x - 0.18, x + 0.18, 0.0, 0.015, z0 + 0.1, z0 + 0.125, 'chrome', cull='k')
    for k, x in enumerate((-0.9, 0.0, 0.9)):      # helmets on the header
        helmet(m, x, 0.43, 2.45 + 0.03, 'navy' if k != 1 else 'olive', s=0.9)
    pd.rack_fit(m, SLOT_X, SLOT_Z)
    fin('WeaponRack', m, ao, cols=[col_box(-1.5, 0.0, 0, 1.5, 0.5, 2.6)])


def build_bench(pal, ao):
    """2 x 1 workbench island: oak top at 0.92, green gun mats (top 0.926) under the two mod mounts at x = +-0.48,
    blender y = -0.18; tool riser on the back half"""
    m = new(pal)
    m.bx(-0.95, 0.95, -0.42, 0.42, 0.86, 0.92, 'oak')
    for sx in (-0.88, 0.88):
        for sy in (-0.36, 0.36):
            m.bx(sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.86, 'steel2', cull='t')
    m.bx(-0.85, 0.85, -0.39, -0.33, 0.74, 0.86, 'steel2', cull='t')
    m.bx(-0.85, 0.85, 0.33, 0.39, 0.74, 0.86, 'steel2', cull='t')
    m.bx(-0.85, 0.85, -0.33, 0.33, 0.18, 0.22, 'steel')
    m.bx(0.3, 0.85, -0.3, 0.3, 0.45, 0.74, 'navy', cull='t')                           # drawer unit
    for k in range(2):
        m.bx(0.34, 0.81, -0.315, -0.3, 0.48 + k * 0.13, 0.6 + k * 0.13, 'navy2')
        m.bx(0.5, 0.65, -0.33, -0.315, 0.53 + k * 0.13, 0.55 + k * 0.13, 'chrome')
    for sx in (-1, 1):   # ammo cans on the lower shelf
        m.bx(sx * 0.45 - 0.14, sx * 0.45 + 0.14, -0.1, 0.1, 0.22, 0.4, 'olive')
        m.bx(sx * 0.45 - 0.05, sx * 0.45 + 0.05, -0.02, 0.02, 0.4, 0.43, 'black')
    for x in (-0.48, 0.48):
        m.bx(x - 0.26, x + 0.26, -0.38, 0.02, 0.92, 0.926, 'leaf', hull='none')
    # riser: two posts and a shelf with spray cans, a parts box and a lamp
    for sx in (-0.82, 0.82):
        m.bx(sx - 0.02, sx + 0.02, 0.36, 0.4, 0.92, 1.42, 'steel2', cull='b')
    m.bx(-0.85, 0.85, 0.2, 0.42, 1.38, 1.41, 'steel')
    m.bx(-0.85, 0.85, 0.4, 0.42, 0.92, 1.38, 'peg', cull='b')
    for k, (x, c) in enumerate(((-0.6, 'red'), (-0.5, 'blue'), (-0.4, 'yellow'))):
        m.cy((x, 0.3, 1.41), 0.03, 0.03, 0.17, c, seg=8)
    m.bx(0.15, 0.55, 0.22, 0.38, 1.41, 1.5, 'orange')
    m.bx(-0.2, 0.0, 0.22, 0.38, 1.41, 1.47, 'olive')
    m.bx(-0.07, 0.07, 0.22, 0.38, 0.926, 1.0, 'blue')                                  # vice
    m.bx(-0.09, 0.09, 0.14, 0.22, 0.95, 1.06, 'steel2')
    m.cy((0.0, 0.18, 1.0), 0.012, 0.012, 0.2, 'chrome', seg=6, rot=(0, 90, 0))
    pd.bench_fit(m)
    fin('Workbench', m, ao, cols=[col_box(-0.97, -0.44, 0, 0.97, 0.44, 0.926), col_box(-0.86, 0.18, 0.926, 0.86, 0.43, 1.5)])


SHELF_TOP = 1.16


def build_shelf(pal, ao):
    """2 x 1 gear shelf (back to the wall): items stand on the 1.16 shelf at x = +-0.5, blender y = 0.22"""
    m = new(pal)
    for sx in (-0.95, 0.95):
        for sy in (0.0, 0.46):
            m.bx(sx - 0.025, sx + 0.025, sy - 0.025, sy + 0.025, 0.0, 2.15, 'steel2')
    for top in (0.24, 0.7, SHELF_TOP, 1.64, 2.12):
        m.bx(-0.925, 0.925, -0.02, 0.48, top - 0.05, top, 'steel', cull='lr')
        m.bx(-0.925, 0.925, -0.025, -0.02, top - 0.05, top - 0.01, 'navy' if top == SHELF_TOP else 'steel2', cull='klr', hull='none')
    m.bx(-0.925, 0.925, 0.48, 0.49, 0.24, 2.07, 'steel2', cull='lr')
    # bottom: two crates; second: helmets and a box; top: boxes
    for k, x in enumerate((-0.45, 0.45)):
        m.bx(x - 0.36, x + 0.36, 0.04, 0.44, 0.24, 0.56, 'olive' if k else 'olive2')
        m.bx(x - 0.12, x + 0.12, 0.035, 0.04, 0.33, 0.45, 'yellow', cull='k', hull='none')
    for k, x in enumerate((-0.62, -0.25, 0.12)):
        helmet(m, x, 0.22, 0.7 + 0.03, ('navy', 'olive', 'black')[k])
    m.bx(0.42, 0.86, 0.06, 0.42, 0.7, 0.98, 'sand')
    for k, (x, w, h, c) in enumerate(((-0.6, 0.5, 0.3, 'sand'), (-0.02, 0.44, 0.24, 'navy'), (0.5, 0.56, 0.36, 'olive'))):
        m.bx(x - w / 2, x + w / 2, 0.06, 0.42, 1.64, 1.64 + h, c)
    m.bx(-0.88, -0.6, 0.1, 0.4, 1.94, 2.07, 'khaki')
    pd.shelf_fit(m, (0.24, 0.7, SHELF_TOP, 1.64, 2.12))
    fin('GearShelf', m, ao, cols=[col_box(-1.0, -0.03, 0, 1.0, 0.5, 2.15)])


# ================================================================ other props
def build_props(pal, ao):
    for name, doors in (('Locker', 'navy'), ('Locker_B', 'steel2')):   # double locker, front -Y, back 2 cm off the wall
        m = new(pal)
        m.bx(-0.46, 0.46, -0.22, 0.48, 0.08, 2.0, 'steel', cull='k')
        m.bx(-0.44, 0.44, -0.2, 0.46, 0.0, 0.08, 'black', cull='kb')
        for sx in (-1, 1):
            x = sx * 0.225
            m.bx(x - 0.215, x + 0.215, -0.235, -0.22, 0.12, 1.96, doors, cull='k')
            for k in range(4):
                z = 1.66 + k * 0.06
                m.bx(x - 0.12, x + 0.12, -0.24, -0.235, z, z + 0.025, 'ink', cull='k', hull='none')
            m.bx(x - 0.08, x + 0.08, -0.24, -0.235, 1.42, 1.5, 'paper', cull='k', hull='none')
            hx = x - sx * 0.16
            m.bx(hx - 0.015, hx + 0.015, -0.26, -0.235, 0.95, 1.15, 'chrome', cull='k')
        if name == 'Locker_B':
            m.bx(-0.3, 0.1, -0.15, 0.35, 2.0, 2.24, 'sand')
            m.bx(-0.3, 0.1, -0.155, -0.15, 2.08, 2.14, 'ink', cull='k', hull='none')
        else:
            helmet(m, 0.18, 0.15, 2.03, 'navy')
        pd.locker_fit(m)
        fin(name, m, ao, cols=[col_box(-0.46, -0.24, 0, 0.46, 0.48, 2.0)])

    m = new(pal)   # sandbags, one run module along X: four courses of rounded bags
    for row in range(4):
        z = 0.1 + row * 0.2
        xs = (-0.25, 0.25) if row % 2 == 0 else (0.0,)
        for k, x in enumerate(xs):
            L = 0.52 if len(xs) == 2 else 0.98
            m.sp((x, 0.0, z), 1.0, 'sand' if (row + k) % 2 else 'khaki', seg=(8, 4), scale=(L / 2, 0.21 - row * 0.012, 0.115))
    fin('Sandbags', m, ao, cols=[col_box(-0.5, -0.21, 0, 0.5, 0.21, 0.85)])

    for name in ('Crate', 'Crate_W', 'AmmoCans'):
        m = new(pal)
        if name == 'Crate':   # olive ammo crate with rope handles and a stencil plate
            m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.68, 'olive', cull='b')
            m.bx(-0.46, 0.46, -0.36, 0.36, 0.68, 0.74, 'olive2')
            for sx in (-1, 1):
                hx = (0.43, 0.47) if sx > 0 else (-0.47, -0.43)
                m.bx(hx[0], hx[1], -0.12, 0.12, 0.42, 0.46, 'black')
                for sy in (-1, 1):
                    m.bx(sx * 0.4 - 0.025, sx * 0.4 + 0.025, -0.355 if sy < 0 else 0.345, -0.345 if sy < 0 else 0.355, 0.0, 0.675, 'olive2', cull='b')
            m.bx(-0.24, 0.24, -0.354, -0.35, 0.3, 0.5, 'yellow', cull='k', hull='none')
            m.bx(-0.18, 0.12, -0.358, -0.354, 0.37, 0.43, 'ink', cull='k', hull='none')
        elif name == 'Crate_W':   # wooden crate: planks and battens
            m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.74, 'oak', cull='b')
            for k in range(3):
                z = 0.12 + k * 0.25
                m.bx(-0.46, 0.46, -0.36, 0.36, z, z + 0.035, 'oak2')
            for sx in (-1, 1):
                m.bx(sx * 0.43 - 0.03, sx * 0.43 + 0.03, -0.365, -0.36, 0.0, 0.74, 'oak2', cull='kb', hull='none')
            m.bx(-0.2, 0.2, -0.364, -0.36, 0.42, 0.56, 'ink', cull='k', hull='none')
            m.bx(-0.16, 0.16, -0.368, -0.364, 0.45, 0.53, 'oak', cull='k', hull='none')
        else:   # four ammo cans on a low pallet
            m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.1, 'oak2', cull='b')
            for i, (x, y) in enumerate(((-0.22, -0.17), (0.22, -0.17), (-0.22, 0.17), (0.22, 0.17))):
                hgt = 0.62 if i < 2 else 0.74
                m.bx(x - 0.2, x + 0.2, y - 0.14, y + 0.14, 0.1, hgt - 0.03, 'olive' if i % 3 else 'olive2')
                m.bx(x - 0.18, x + 0.18, y - 0.12, y + 0.12, hgt - 0.03, hgt, 'olive2')
                if i >= 2:
                    m.bx(x - 0.06, x + 0.06, y - 0.02, y + 0.02, hgt, hgt + 0.02, 'black')
                m.bx(x - 0.1, x + 0.1, y - 0.145, y - 0.14, 0.3, 0.38, 'yellow', cull='k', hull='none')
        fin(name, m, ao, cols=[col_box(-0.46, -0.36, 0, 0.46, 0.36, 0.75)])

    # desk pod [2,2]: a double desk with a divider, monitors, keyboards and chairs both sides
    m = new(pal)
    m.bx(-0.9, 0.9, -0.4, 0.4, 0.72, 0.76, 'oak')
    for sx in (-0.86, 0.86):
        m.bx(sx - 0.03, sx + 0.03, -0.36, 0.36, 0.0, 0.72, 'steel2', cull='t')
    m.bx(-0.84, 0.84, -0.015, 0.015, 0.2, 0.72, 'steel', cull='t')
    m.bx(-0.88, 0.88, -0.02, 0.02, 0.76, 1.12, 'navy')
    m.bx(-0.88, 0.88, -0.025, 0.025, 1.12, 1.15, 'gold')
    for side in (0, 1):
        P = at(m, 0, 0, 180 * side)
        monitor(m, -0.3, -0.15, 0.76, 0, ui='screen' if side else 'blue')
        monitor(m, 0.32, -0.16, 0.76, 12, w=0.44, h=0.28)
        keyboard(m, -0.25, -0.31, 0.76)
        papers(m, 0.6, -0.24, 0.76, 15)
        mug(m, -0.72, -0.15, 0.76, 'red' if side else 'white')
        chair(m, -0.15 + 0.1 * side, -0.72, 180 + (8 if side else -6), 'navy' if side else 'slate')
        m.parent = P
    pd.desk_fit(m)
    fin('DeskPod', m, ao, cols=[col_box(-0.92, -0.42, 0, 0.92, 0.42, 1.15), col_box(-0.45, -0.98, 0, 0.15, -0.42, 0.55),
                                col_box(-0.25, 0.42, 0, 0.35, 0.98, 0.55)])

    # ops console [4,1] against the wall: desk, six monitors, two big wall screens, two chairs
    m = new(pal)
    m.bx(-1.9, 1.9, -0.05, 0.5, 0.0, 0.72, 'navy2', cull='k')
    m.bx(-1.92, 1.92, -0.1, 0.5, 0.72, 0.77, 'slate')
    m.bx(-1.92, 1.92, -0.105, -0.1, 0.72, 0.77, 'gold', cull='k', hull='none')
    for k in range(4):
        m.bx(-1.8 + k * 0.95, -1.05 + k * 0.95, -0.055, -0.05, 0.1, 0.6, 'navy', cull='k', hull='none')
    for k in range(6):
        x = -1.55 + k * 0.62
        monitor(m, x, 0.22, 0.77, 0, w=0.5, h=0.3, ui='screen' if k % 2 else 'green')
    for k in range(3):
        keyboard(m, -1.25 + k * 1.25, 0.0, 0.77)
    for sx in (-0.95, 0.95):   # big screens on the wall above
        m.bx(sx - 0.88, sx + 0.88, 0.42, 0.49, 1.45, 2.65, 'black', cull='k')
        m.bx(sx - 0.82, sx + 0.82, 0.415, 0.42, 1.51, 2.59, 'screen2', cull='k', hull='none')
    # left screen: a city map with markers; right screen: a dashboard
    for k, (x0, x1, z0, z1, c) in enumerate(((-1.7, -1.2, 1.6, 2.1, 'navy'), (-1.1, -0.3, 1.6, 1.95, 'navy'), (-1.7, -0.9, 2.2, 2.5, 'navy'),
                                             (-0.8, -0.3, 2.05, 2.5, 'navy'), (-1.75, -0.2, 2.13, 2.17, 'screen'), (-1.15, -1.11, 1.55, 2.55, 'screen'))):
        m.bx(x0, x1, 0.41 - 0.003 * (k % 2), 0.415, z0, z1, c, cull='k', hull='none')
    for x, z, c in ((-1.4, 1.85, 'red'), (-0.6, 2.3, 'red'), (-1.3, 2.35, 'yellow'), (-0.5, 1.75, 'green')):
        m.cy((x, 0.405, z), 0.04, 0.04, 0.002, c, seg=8, rot=(90, 0, 0), hull='none')
    for k in range(5):
        hgt = (0.25, 0.5, 0.38, 0.7, 0.55)[k]
        m.bx(0.3 + k * 0.22, 0.45 + k * 0.22, 0.41, 0.415, 1.6, 1.6 + hgt * 0.75, ('screen', 'green', 'screen', 'yellow', 'screen')[k], cull='k', hull='none')
    m.bx(0.3, 1.7, 0.41, 0.415, 2.3, 2.38, 'white', cull='k', hull='none')
    m.bx(-0.1, 0.1, 0.4, 0.49, 2.7, 3.0, 'steel2', cull='k')                           # camera dome
    m.sp((0, 0.33, 2.85), 0.08, 'black', seg=(8, 4))
    for sx in (-0.95, 0.95):
        chair(m, sx, -0.42, 180 + 0, 'navy')
    pd.ops_fit(m)
    fin('OpsConsole', m, ao, cols=[col_box(-1.95, -0.12, 0, 1.95, 0.5, 1.1), col_box(-1.22, -0.68, 0, -0.68, -0.12, 0.55),
                                   col_box(0.68, -0.68, 0, 1.22, -0.12, 0.55)])

    # briefing row [4,2]: a long table on the north half, four chairs facing it
    m = new(pal)
    m.bx(-1.85, 1.85, 0.1, 0.75, 0.72, 0.77, 'oak')
    m.bx(-1.8, 1.8, 0.68, 0.71, 0.3, 0.72, 'oak2', cull='t')
    for sx in (-1.75, 1.75):
        m.bx(sx - 0.04, sx + 0.04, 0.15, 0.7, 0.0, 0.72, 'steel2', cull='t')
    for k in range(4):
        x = -1.35 + k * 0.9
        chair(m, x, -0.45, 180 + (-6, 4, -3, 7)[k], 'navy')
        papers(m, x - 0.05, 0.35, 0.77, (5, -8, 12, -4)[k], 'paper' if k % 2 else 'white')
        if k in (1, 3):
            m.cy((x + 0.25, 0.55, 0.77), 0.03, 0.03, 0.2, 'blue', seg=8)
    P = at(m, -0.95, 0.45, 8, 0.77)   # a laptop
    m.bx(-0.17, 0.17, -0.12, 0.12, 0.0, 0.02, 'steel2')
    m.box((0, 0.12, 0.13), (0.33, 0.015, 0.24), 'steel2', rot=(-12, 0, 0), bevel=False)
    m.parent = P
    pd.brief_fit(m)
    fin('BriefRow', m, ao, cols=[col_box(-1.85, 0.1, 0, 1.85, 0.75, 0.77), col_box(-1.8, -0.75, 0, 1.8, -0.18, 0.5)])

    m = new(pal)   # lectern
    m.bx(-0.32, 0.32, -0.22, 0.22, 0.0, 0.08, 'oak2')
    m.bx(-0.26, 0.26, -0.18, 0.2, 0.08, 1.0, 'oak')
    m.box((0, -0.02, 1.07), (0.6, 0.48, 0.05), 'oak2', rot=(-14, 0, 0), bevel=False)
    m.bx(-0.24, 0.24, -0.185, -0.18, 0.2, 0.92, 'navy', cull='k', hull='none')
    m.cy((0, -0.19, 0.62), 0.14, 0.14, 0.02, 'gold', seg=10, rot=(90, 0, 0))
    star(m, 0, 0.62, -0.21, 0.13, 'navy', t=0.003)
    m.cy((0.18, 0.05, 1.08), 0.008, 0.008, 0.28, 'black', seg=5, rot=(-25, 0, 0))
    m.sp((0.18, -0.07, 1.33), 0.025, 'black', seg=(6, 4))
    fin('Lectern', m, ao, cols=[col_box(-0.32, -0.22, 0, 0.32, 0.24, 1.12)])

    m = new(pal)   # potted fig
    m.cy((0, 0, 0), 0.26, 0.21, 0.5, 'clay', seg=10)
    m.cy((0, 0, 0.5), 0.27, 0.27, 0.06, 'clay', seg=10)
    m.cy((0, 0, 0.56), 0.22, 0.22, 0.004, 'oak2', seg=10, hull='none')
    m.cy((0, 0, 0.56), 0.035, 0.03, 0.55, 'oak2', seg=6, caps=False)
    for x, y, z, r, c in ((0.0, 0.0, 1.32, 0.34, 'leaf'), (0.2, -0.1, 1.08, 0.24, 'green'), (-0.2, 0.1, 1.12, 0.25, 'green'), (0.05, 0.18, 1.55, 0.22, 'green')):
        m.sp((x, y, z), r, c, seg=(8, 5))
    fin('Plant', m, ao, cols=[col_box(-0.3, -0.3, 0, 0.3, 0.3, 1.7)])
    m = new(pal)   # snake plant in a square planter
    m.bx(-0.24, 0.24, -0.24, 0.24, 0.0, 0.42, 'slate')
    m.bx(-0.2, 0.2, -0.2, 0.2, 0.42, 0.424, 'oak2', hull='none')
    for k in range(7):
        a = k * 2.4
        r = 0.08 + 0.05 * (k % 3)
        m.box((math.cos(a) * r, math.sin(a) * r, 0.42 + 0.35 + 0.08 * (k % 2)), (0.07, 0.025, 0.7 + 0.16 * (k % 2)),
              'leaf' if k % 2 else 'green', rot=(math.cos(a) * 12, math.sin(a) * 12, math.degrees(a)), bevel=False)
    fin('Plant_B', m, ao, cols=[col_box(-0.25, -0.25, 0, 0.25, 0.25, 1.3)])

    m = new(pal)   # filing cabinet with a box on top
    m.bx(-0.28, 0.28, -0.2, 0.45, 0.0, 1.36, 'steel')
    for k in range(4):
        z = 0.06 + k * 0.325
        m.bx(-0.25, 0.25, -0.212, -0.2, z, z + 0.29, 'steel2', cull='k')
        m.bx(-0.08, 0.08, -0.232, -0.212, z + 0.2, z + 0.225, 'chrome', cull='k')
        m.bx(-0.06, 0.06, -0.216, -0.212, z + 0.08, z + 0.14, 'paper', cull='k', hull='none')
    m.bx(-0.22, 0.2, -0.12, 0.35, 1.36, 1.6, 'sand')
    fin('Cabinet', m, ao, cols=[col_box(-0.28, -0.22, 0, 0.28, 0.45, 1.6)])

    m = new(pal)   # waiting bench [2,1]: three seats on a beam
    m.bx(-0.9, 0.9, -0.05, 0.05, 0.3, 0.38, 'steel2')
    for sx in (-0.75, 0.75):
        m.bx(sx - 0.03, sx + 0.03, -0.25, 0.25, 0.0, 0.04, 'steel2')
        m.bx(sx - 0.03, sx + 0.03, -0.03, 0.03, 0.04, 0.3, 'steel2')
    for k in range(3):
        x = -0.6 + k * 0.6
        m.bx(x - 0.27, x + 0.27, -0.24, 0.16, 0.38, 0.46, 'navy')
        m.box((x, 0.2, 0.72), (0.52, 0.06, 0.48), 'navy', rot=(-10, 0, 0), bevel=False)
    fin('WaitBench', m, ao, cols=[col_box(-0.9, -0.26, 0, 0.9, 0.26, 0.5)])

    m = new(pal)   # snack machine
    m.bx(-0.42, 0.42, -0.35, 0.45, 0.0, 1.9, 'navy', cull='k')
    m.bx(-0.36, 0.14, -0.36, -0.35, 0.6, 1.8, 'glass', cull='k', hull='none')
    for r in range(4):
        for k in range(3):
            m.bx(-0.32 + k * 0.15, -0.22 + k * 0.15, -0.37, -0.36, 0.7 + r * 0.27, 0.86 + r * 0.27, ('red', 'yellow', 'orange', 'green')[(r + k) % 4], cull='k', hull='none')
    m.bx(0.2, 0.36, -0.37, -0.35, 1.2, 1.5, 'black', cull='k')
    m.bx(-0.36, 0.14, -0.37, -0.35, 0.18, 0.4, 'black', cull='k')
    m.bx(-0.42, 0.42, -0.36, -0.35, 1.8, 1.9, 'gold', cull='k', hull='none')
    fin('Vending', m, ao, cols=[col_box(-0.42, -0.36, 0, 0.42, 0.45, 1.9)])
    m = new(pal)   # water cooler and a recycling bin
    m.bx(-0.18, 0.18, -0.16, 0.2, 0.0, 1.0, 'white')
    m.bx(-0.06, 0.06, -0.19, -0.16, 0.75, 0.85, 'blue', cull='k')
    m.cy((0, 0.02, 1.0), 0.15, 0.15, 0.35, 'glass', seg=10)
    m.cy((0, 0.02, 1.35), 0.15, 0.05, 0.08, 'glass', seg=10)
    m.cy((0.32, 0.05, 0.0), 0.15, 0.17, 0.6, 'blue', seg=10)
    fin('Cooler', m, ao, cols=[col_box(-0.2, -0.2, 0, 0.5, 0.25, 1.45)])

    m = new(pal)   # SWAT gear stand: base, post, vest, helmet, shield leaning
    m.cy((0, 0, 0), 0.25, 0.25, 0.04, 'black', seg=10)
    m.cy((0, 0, 0.04), 0.025, 0.025, 1.2, 'steel2', seg=6, caps=False)
    m.bx(-0.24, 0.24, -0.13, 0.13, 0.95, 1.5, 'navy')
    m.bx(-0.25, 0.25, -0.135, -0.13, 1.2, 1.3, 'paper', cull='k', hull='none')
    m.bx(-0.18, 0.18, -0.138, -0.135, 1.23, 1.27, 'ink', cull='k', hull='none')
    for k in range(3):
        m.bx(-0.2 + k * 0.14, -0.1 + k * 0.14, -0.18, -0.13, 0.98, 1.12, 'navy2', cull='k')
    for sx in (-0.17, 0.17):
        m.bx(sx - 0.05, sx + 0.05, -0.11, 0.11, 1.5, 1.56, 'navy2')
    m.cy((0, 0, 1.5), 0.06, 0.06, 0.1, 'black', seg=8)
    helmet(m, 0, 0, 1.68, 'black', s=1.05)
    m.bx(-0.04, 0.04, -0.17, -0.155, 1.66, 1.73, 'gold', cull='k')
    m.box((0.3, 0.12, 0.55), (0.06, 0.5, 1.0), 'black', rot=(0, 0, 0), bevel=False)
    m.bx(0.265, 0.27, -0.06, 0.3, 0.75, 0.85, 'white', hull='none')
    fin('GearStand', m, ao, cols=[col_box(-0.28, -0.28, 0, 0.36, 0.38, 1.8)])

    m = new(pal)   # red tool chest on castors
    m.bx(-0.4, 0.4, -0.25, 0.3, 0.1, 1.0, 'red')
    for k in range(5):
        z = 0.16 + k * 0.165
        m.bx(-0.37, 0.37, -0.262, -0.25, z, z + 0.14, 'red', cull='k')
        m.bx(-0.25, 0.25, -0.28, -0.262, z + 0.1, z + 0.12, 'chrome', cull='k')
    m.bx(-0.4, 0.4, -0.25, 0.3, 1.0, 1.04, 'black')
    for sx in (-0.33, 0.33):
        for sy in (-0.18, 0.23):
            m.cy((sx, sy, 0.0), 0.05, 0.05, 0.1, 'black', seg=6)
    m.bx(-0.3, 0.1, -0.1, 0.2, 1.04, 1.12, 'steel2')
    fin('ToolChest', m, ao, cols=[col_box(-0.4, -0.28, 0, 0.4, 0.3, 1.12)])

    m = new(pal)   # two oil drums
    for k, (x, y, c) in enumerate(((-0.22, -0.18, 'blue'), (0.22, 0.18, 'red'))):
        m.cy((x, y, 0.0), 0.26, 0.26, 0.88, c, seg=12)
        for z in (0.28, 0.58):
            m.cy((x, y, z), 0.27, 0.27, 0.04, 'steel2' if c == 'blue' else 'black', seg=12)
        m.cy((x + 0.1, y, 0.88), 0.05, 0.05, 0.02, 'black', seg=6)
    fin('Drums', m, ao, cols=[col_box(-0.48, -0.42, 0, 0.5, 0.43, 0.9)])
    m = new(pal)   # stack of tyres
    for k in range(4):
        m.cy((0.02 * (k % 2), 0, k * 0.22), 0.36, 0.36, 0.22, 'rubberK', seg=12)
        if k == 3:
            m.cy((0.02 * (k % 2), 0, k * 0.22 + 0.22), 0.2, 0.2, 0.004, 'black', seg=10, hull='none')
    fin('Tyres', m, ao, cols=[col_box(-0.38, -0.36, 0, 0.4, 0.36, 0.9)])

    m = new(pal)   # pallet of wrapped boxes [2,2]
    m.bx(-0.85, 0.85, -0.85, 0.85, 0.0, 0.15, 'oak2', cull='b')
    for i in range(2):
        for j in range(2):
            x, y = -0.42 + i * 0.84, -0.42 + j * 0.84
            m.bx(x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0.15, 0.75, 'sand' if (i + j) % 2 else 'khaki')
    m.bx(-0.4, 0.4, -0.4, 0.4, 0.75, 1.25, 'sand')
    m.bx(-0.06, 0.06, -0.86, 0.86, 0.15, 0.755, 'black', cull='b')
    m.bx(-0.2, 0.2, -0.405, -0.4, 0.9, 1.1, 'ink', cull='k', hull='none')
    fin('Pallet', m, ao, cols=[col_box(-0.86, -0.86, 0, 0.86, 0.86, 0.76), col_box(-0.4, -0.4, 0.76, 0.4, 0.4, 1.25)])

    m = new(pal)   # range booth [3,2]: two partitions, a counter on the downrange (north, +Y) end, lane plate
    for sx in (-1, 1):
        x = sx * 1.44
        m.bx(x - 0.03, x + 0.03, -0.9, 0.95, 0.0, 1.85, 'acou')
        m.bx(x - 0.04, x + 0.04, -0.92, 0.97, 1.85, 1.9, 'black')
        m.bx(x - 0.035, x + 0.035, -0.93, -0.9, 0.0, 1.85, 'navy', cull='k')
    m.bx(-1.41, 1.41, 0.55, 0.95, 0.98, 1.04, 'oak')
    m.bx(-1.41, 1.41, 0.9, 0.95, 0.0, 0.98, 'acou2')
    m.bx(-0.12, 0.12, 0.62, 0.8, 1.04, 1.12, 'black')
    m.bx(-0.05, 0.05, 0.6, 0.62, 1.07, 1.1, 'green', cull='k', hull='none')
    m.bx(-0.7, -0.4, 0.65, 0.85, 1.04, 1.1, 'olive')
    m.bx(0.5, 0.8, 0.6, 0.85, 1.04, 1.05, 'paper', hull='none')
    fin('Booth', m, ao, cols=[col_box(-1.48, -0.93, 0, -1.4, 0.97, 1.9), col_box(1.4, -0.93, 0, 1.48, 0.97, 1.9),
                              col_box(-1.41, 0.55, 0, 1.41, 0.95, 1.04)])

    m = new(pal)   # target stand: robot silhouette on a paper board, front -Y
    for sx in (-0.3, 0.3):
        m.bx(sx - 0.025, sx + 0.025, -0.025, 0.025, 0.0, 1.8, 'oak2')
        m.bx(sx - 0.03, sx + 0.03, -0.2, 0.2, 0.0, 0.04, 'oak2')
    m.bx(-0.32, 0.32, -0.01, 0.01, 0.9, 1.85, 'target')
    m.bx(-0.09, 0.09, -0.016, -0.01, 1.58, 1.76, 'ink', cull='k', hull='none')        # head
    m.bx(-0.16, 0.16, -0.016, -0.01, 1.06, 1.52, 'ink', cull='k', hull='none')        # body
    m.bx(-0.26, 0.26, -0.0195, -0.01, 1.42, 1.5, 'ink', cull='k', hull='none')        # shoulders
    m.bx(-0.06, -0.02, -0.02, -0.016, 1.64, 1.68, 'amber', cull='k', hull='none')     # eye slot
    m.cy((0, -0.016, 1.3), 0.1, 0.1, 0.004, 'target', seg=12, rot=(90, 0, 0), hull='none')
    m.cy((0, -0.02, 1.3), 0.06, 0.06, 0.004, 'red', seg=10, rot=(90, 0, 0), hull='none')
    for x, z in ((0.04, 1.36), (-0.07, 1.22), (0.1, 1.15)):
        m.cy((x, -0.0275, z), 0.012, 0.012, 0.002, 'black', seg=6, rot=(90, 0, 0), hull='none')
    fin('Target', m, ao, cols=[col_box(-0.34, -0.2, 0, 0.34, 0.2, 1.85)])

    m = new(pal)   # steel bollard: yellow with black bands
    m.cy((0, 0, 0.0), 0.11, 0.11, 0.95, 'yellow', seg=10)
    for z in (0.55, 0.75):
        m.cy((0, 0, z), 0.114, 0.114, 0.08, 'ink', seg=10)
    m.sp((0, 0, 0.95), 0.11, 'yellow', seg=(10, 3), scale=(1, 1, 0.45))
    m.cy((0, 0, 0), 0.16, 0.16, 0.03, 'steel2', seg=10)
    fin('Bollard', m, ao, cols=[col_box(-0.16, -0.16, 0, 0.16, 0.16, 1.0)])
    m = new(pal)   # traffic cones
    for k, (x, y, s2) in enumerate(((-0.18, -0.12, 1.0), (0.2, 0.1, 0.85), (-0.1, 0.25, 0.7))):
        m.bx(x - 0.17 * s2, x + 0.17 * s2, y - 0.17 * s2, y + 0.17 * s2, 0.0, 0.035, 'black')
        m.cy((x, y, 0.035), 0.12 * s2, 0.025 * s2, 0.62 * s2, 'orange', seg=8)
        m.cy((x, y, 0.035 + 0.3 * s2), 0.075 * s2 + 0.008, 0.06 * s2 + 0.008, 0.1 * s2, 'white', seg=8, caps=False)
    fin('Cones', m, ao, cols=[col_box(-0.36, -0.3, 0, 0.36, 0.42, 0.66)])


# ================================================================ landmarks
def wheel_x(m, x, y, r=0.42, w=0.3, outward=1):
    """wheel on an axle along X; outward = +1 for the right side (+X), -1 for the left"""
    x0 = x if outward > 0 else x - w
    m.cy((x0, y, r), r, r, w, 'rubberK', seg=12, rot=(0, 90, 0))
    hx = x0 + w if outward > 0 else x0 - 0.006
    m.cy((hx, y, r), r * 0.55, r * 0.55, 0.006, 'chrome', seg=10, rot=(0, 90, 0), hull='none')
    m.cy((hx + (0.006 if outward > 0 else -0.012), y, r), r * 0.2, r * 0.2, 0.012, 'black', seg=6, rot=(0, 90, 0), hull='none')


def build_landmarks(pal, ao):
    m = new(pal)   # SWAT van 3 x 6, nose toward -Y
    m.bx(-1.15, 1.15, -1.6, 2.65, 0.55, 2.4, 'navy')                                   # box body
    m.bx(-1.1, 1.1, -2.85, -1.6, 0.55, 1.45, 'navy')                                   # bonnet
    m.box((0, -1.85, 1.92), (2.1, 0.6, 0.06), 'glass', rot=(-38, 0, 0), bevel=False)   # windscreen
    m.bx(-1.1, 1.1, -2.1, -1.6, 1.45, 1.5, 'navy2')
    for sx in (-1, 1):
        x = sx * 1.15
        side = (x, x + 0.006) if sx > 0 else (x - 0.006, x)
        m.bx(side[0], side[1], -1.5, -0.65, 1.5, 2.1, 'glass', hull='none')            # cab window
        m.bx(side[0], side[1], -0.3, 2.4, 1.15, 1.55, 'white', hull='none')            # SWAT band
        s2 = (x + 0.006, x + 0.01) if sx > 0 else (x - 0.01, x - 0.006)
        for k, (y0, y1) in enumerate(((-0.1, 0.25), (0.35, 0.7), (0.8, 1.15), (1.25, 1.6))):   # block letters
            m.bx(s2[0], s2[1], y0, y1, 1.22, 1.48, 'ink', hull='none')
        m.bx(side[0], side[1], 0.2, 2.2, 1.7, 2.1, 'glass', hull='none')                # rear side window
        m.bx(side[0], side[1], -0.6, -0.56, 0.6, 2.35, 'navy2', hull='none')           # door seam
        mx = (1.15, 1.3) if sx > 0 else (-1.3, -1.15)
        m.bx(mx[0], mx[1], -1.75, -1.6, 1.55, 1.8, 'black')                             # mirror
        m.bx(mx[0], mx[1], -1.3, 2.3, 0.42, 0.5, 'black')                               # step
    m.bx(-1.1, 1.1, -2.88, -2.85, 0.75, 1.3, 'black', cull='k')                         # grille
    for sx in (-0.75, 0.75):
        m.bx(sx - 0.2, sx + 0.2, -2.885, -2.88, 1.1, 1.25, 'light', cull='k', hull='none')
    m.bx(-1.15, 1.15, -3.05, -2.88, 0.45, 0.62, 'black')                               # bull bar
    for sx in (-0.5, 0.5):
        m.bx(sx - 0.05, sx + 0.05, -3.05, -2.88, 0.62, 1.2, 'black')
    m.bx(-1.15, 1.15, 2.65, 2.75, 0.45, 0.62, 'black')
    m.bx(-0.02, 0.02, 2.65, 2.67, 0.65, 2.3, 'navy2')                                  # rear door seam
    for sx in (-0.55, 0.55):
        m.bx(sx - 0.35, sx + 0.35, 2.65, 2.66, 1.6, 2.1, 'glass', hull='none')
        m.bx(sx - 0.15, sx + 0.15, 2.65, 2.66, 0.7, 0.85, 'red', hull='none')
    m.bx(-1.15, 1.15, -1.6, 2.65, 0.4, 0.55, 'black')                                   # skirt
    m.bx(-1.1, 1.1, -2.85, -1.6, 0.4, 0.55, 'black')
    m.bx(-0.9, 0.9, -0.2, 2.2, 2.4, 2.46, 'steel2')                                    # roof rack
    m.bx(-0.7, 0.7, -1.45, -1.25, 2.4, 2.52, 'black')                                  # light bar
    m.bx(-0.65, -0.05, -1.43, -1.27, 2.52, 2.62, 'blue')
    m.bx(0.05, 0.65, -1.43, -1.27, 2.52, 2.62, 'red')
    for sx in (-1, 1):
        for y in (-2.0, 1.7):
            wheel_x(m, sx * 1.02 if sx > 0 else -1.02, y, outward=sx)
    pd.van_fit(m)
    fin('Landmark_Van', m, ao, cols=[col_box(-1.3, -3.05, 0, 1.3, 2.75, 2.5)])

    m = new(pal)   # holding cell 4 x 3: bars along the front (-Y), solid back and sides, bench, toilet, number plate
    m.bx(-2.0, 2.0, 1.4, 1.5, 0.0, 2.9, 'tile', cull='bt')
    for sx in (-1, 1):
        m.bx(sx * 1.95 - 0.05, sx * 1.95 + 0.05, -1.45, 1.4, 0.0, 2.9, 'tile', cull='bt')
        mx = (1.895, 1.997) if sx > 0 else (-1.997, -1.895)
        m.bx(mx[0], mx[1], -1.455, 1.395, 0.0, 1.0, 'mint', cull='b')
    m.bx(-1.996, 1.996, -1.47, 1.495, 2.9, 3.0, 'wall2')
    m.bx(-1.9, 1.9, -1.45, -1.35, 2.75, 2.9, 'steel2')
    for k in range(15):
        x = -1.75 + k * 0.25
        m.cy((x, -1.4, 0.0), 0.022, 0.022, 2.75, 'steel2', seg=6, caps=False)
    for z in (0.12, 1.1):
        m.bx(-1.9, 1.9, -1.43, -1.37, z, z + 0.05, 'steel2')
    m.bx(0.35, 0.55, -1.47, -1.33, 0.95, 1.25, 'black')                                # lock box
    m.bx(-1.6, 1.6, 0.95, 1.4, 0.42, 0.5, 'oak')
    for sx in (-1.4, 1.4):
        m.bx(sx - 0.03, sx + 0.03, 1.0, 1.35, 0.0, 0.42, 'steel2')
    m.bx(1.3, 1.75, -0.2, 0.25, 0.0, 0.42, 'chrome')
    m.bx(1.3, 1.75, 0.25, 0.4, 0.0, 0.75, 'chrome')
    m.bx(-1.6, -0.9, 0.98, 1.38, 0.5, 0.58, 'navy')
    m.bx(-0.35, 0.35, -1.5, -1.47, 2.78, 2.88, 'gold', hull='none')
    m.bx(-0.25, 0.25, -1.505, -1.5, 2.8, 2.86, 'ink', hull='none')
    fin('Landmark_Cells', m, ao, cols=[col_box(-2.0, -1.45, 0, 2.0, 1.5, 3.0)])

    m = new(pal)   # front desk 6 x 2: raised counter facing -Y, badge front, work desk with monitors behind
    m.bx(-2.9, 2.9, -0.55, -0.25, 0.0, 1.05, 'navy', cull='b')
    for sx in (-1, 1):
        ex = (2.6, 2.9) if sx > 0 else (-2.9, -2.6)
        m.bx(ex[0], ex[1], -0.25, 0.75, 0.0, 1.05, 'navy', cull='b')
    m.bx(-2.95, 2.95, -0.65, -0.2, 1.05, 1.1, 'oak')
    m.bx(-2.9, 2.9, -0.56, -0.55, 0.1, 0.18, 'gold', cull='k', hull='none')
    m.bx(-2.9, 2.9, -0.56, -0.55, 0.85, 0.9, 'gold', cull='k', hull='none')
    m.bx(-2.9, 2.9, -0.57, -0.55, 0.0, 0.08, 'black', cull='kb')
    m.cy((0, -0.55, 0.52), 0.3, 0.3, 0.03, 'gold', seg=14, rot=(90, 0, 0))
    m.cy((0, -0.58, 0.52), 0.24, 0.24, 0.006, 'navy2', seg=14, rot=(90, 0, 0), hull='none')
    star(m, 0, 0.52, -0.59, 0.22, 'gold', t=0.003)
    for sx in (-1.6, 1.6):   # "FRONT DESK" letter blocks
        for k in range(4):
            m.bx(sx - 0.5 + k * 0.26, sx - 0.32 + k * 0.26, -0.565 - 0.003 * (k % 2), -0.55, 0.42, 0.62, 'white', cull='k', hull='none')
    m.bx(-2.6, 2.6, 0.35, 0.75, 0.72, 0.76, 'oak2')
    m.bx(-2.6, 2.6, 0.7, 0.75, 0.0, 0.72, 'navy2', cull='t')
    for k, x in enumerate((-1.6, 0.0, 1.6)):
        monitor(m, x, 0.55, 0.76, 180, w=0.5, h=0.3, ui='screen' if k != 1 else 'blue')
        chair(m, x, 0.0, (k - 1) * 10, 'navy')
    for x in (-2.2, 2.2):
        papers(m, x, -0.42, 1.1, 20 if x > 0 else -15, 'white')
    m.cy((1.0, -0.42, 1.1), 0.08, 0.08, 0.02, 'black', seg=8)
    m.bx(0.96, 1.04, -0.44, -0.4, 1.12, 1.3, 'black')                                  # desk bell / mic
    pd.frontdesk_fit(m)
    fin('Landmark_FrontDesk', m, ao, cols=[col_box(-2.95, -0.65, 0, 2.95, 0.75, 1.1)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        m.box((sx * 1.72, 0, 1.75), (0.56, 0.99, 3.5), 'navy2', bevel=False)    # faces 5 mm inside the cell
        m.box((sx * 1.72, 0, 0.6), (0.6, 1.016, 1.2), 'slate2', bevel=False)       # 8 mm proud of the cell edge
    m.box((0, 0, 3.745), (4.0, 0.99, 0.49), 'black', bevel=False)
    for fy in (-1, 1):
        for k in range(10):
            m.box((-1.5 + (k + 0.5) * 0.3, fy * 0.5, 3.745), (0.3, 0.02 + 0.004 * (k % 2), 0.3), 'yellow' if k % 2 else 'ink', bevel=False)
    fin('GateFrame', m, ao)
    m = new(pal)
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.55 + (i + 0.5) * (Hs - 0.55) / n
        m.box((0, 0, z), (3.0, 0.12, (Hs - 0.55) / n - 0.06), 'steel' if i % 2 else 'steel2', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.14, 0.5), 'ink' if k % 2 else 'yellow', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.16, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor walls: 1 m along Y, inner face +X at x = 0.25 (lobby style), with art variants
    for name in ('TrailWall', 'TrailWall_Board', 'TrailWall_Badge', 'TrailWall_Window'):
        m = new(pal)
        P = at(m, 0, 0, 90)          # a wall module facing -Y, turned so its face looks +X, face at x = 0.25
        m.parent = m.parent @ Matrix.Translation((0, 0.25, 0))
        wall_base(m, 'L')
        m.bx(-0.5, 0.5, CORE, 0.0, 0, H, 'wall', cull='flrt')
        if name == 'TrailWall_Board':
            notice(m, 'L')
        elif name == 'TrailWall_Badge':
            badge(m, 'L')
        elif name == 'TrailWall_Window':
            window(m, 'L')
        m.parent = P
        fin(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.12, 'steel2', seg=20)
    m.cy((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, hull='none')
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cy((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6)
    fin('Hatch', m, ao)


def build_kit_police(ao):
    pal = Palette(FAM)
    build_walls(pal, ao)
    floor_tiles(pal)
    build_ceiling(pal, ao)
    build_rack(pal, ao)
    build_bench(pal, ao)
    build_shelf(pal, ao)
    build_props(pal, ao)
    build_landmarks(pal, ao)
    build_gate(pal, ao)
    print('kit-police: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:16]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-police'
BUILD = build_kit_police
