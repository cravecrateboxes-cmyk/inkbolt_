"""INKBOLT asset family: kit-techhq (NOVYX HQ: a laptop and software maker's headquarters on floors 27 - 33 of a
mid-rise glass tower; campaign level 21).

A modern tech campus, not the corporate office of kit-office: light oak and white, the brand's bold violet / coral /
sunflower / mint, glass meeting pods, a living green wall, sit-stand desks with several screens, beanbags and a
bleacher stair, a micro-kitchen, whiteboards full of diagrams, a hardware lab and a roof terrace. The Kit class comes
from kit-office (outlined + flat shapes, the z-fight check, collision empties) with walkable boxes and extruded
polygons added; every model is new.

Files: this one (palette, kit class, walls, gate, lift lobbies, stairs, rails, ceiling and floor finishes, build),
techhq_props.py (furniture, labs, terrace, landmarks), techhq_city.py (the skyline rows).

Conventions (src/data/themes.js, src/game/zones.js):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z, the room). Wall modules are 8 m tall (double-height floors); the
    mezzanine deck stands at 4 m (slab 3.6 - 4.0); ceiling pieces hang from their origin (the 8 m ceiling plane);
    the lab's roof tiles stand on it.
  * Curtain wall: a slim black mullion every 3 m (Win_M, the bay's middle cell: symmetric, so the engine's turns
    never mirror a pattern), a white aluminium fin outside it, the slab line at 4 m, glints on open glazing.
  * Lift-lobby trail modules carry half of the corridor's roof and floor slabs and a glass outside face down to the
    set-back block 4 m below, so a lobby reads as a glazed link between the wings from the other floors.
  * Collision: <Piece>_COL<n> empties; <Piece>_WCOL<n> for boxes robots may walk on (stairs, the bleacher, the stage).
"""
import math
import os

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
import fam_kit_office as O

FAM = 'kit-techhq'
PFX = 'KIT_TECHHQ_'
ib_lib.GLB[FAM] = 'fps-kit-techhq.glb'
ib_lib.CFG[FAM] = (0.012, 0.013)
HULL_T = ib_lib.CFG[FAM][1]
H = 8.0          # wall / ceiling height
DECK = 4.0       # mezzanine floor (slab 3.6 - 4.0)
HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = 'NOVYX'
BRAND_FONT = 'sans'     # Inter Bold: the logotype (Bebas Neue's Y loses its stem at this curve resolution)

ib_lib.PALETTES[FAM] = BASE + [
    # structure and fit-out
    ('wallW', '#F4F2EE'), ('oak', '#E2C496'), ('oak2', '#C9A36E'), ('oakD', '#A87E4E'), ('mullion', '#23262D'),
    ('alu', '#DCE0E5'), ('concrete', '#C9C6C0'), ('glass', '#BFE3F0'), ('glint', '#F4FBFF'), ('glow', '#FFF6DE'),
    ('steel', '#C8CDD4'), ('steelD', '#7D848F'), ('graphite', '#33363E'), ('graphite2', '#575C67'), ('black', '#1C1E24'),
    # brand
    ('violet', '#6C4BFF'), ('violetD', '#4B32C7'), ('coral', '#FF5A4E'), ('sun', '#FFC23C'), ('mint', '#2ED3A6'),
    ('sky', '#3AA0FF'), ('pink', '#FF8FB8'),
    # screens, fabrics
    ('screen', '#8FD8FF'), ('screenD', '#1B2433'), ('code', '#7CF0A8'), ('felt', '#8E9AA8'), ('sofa', '#3E4A5C'),
    ('cushion', '#EDE6D8'), ('board', '#FBFBF8'),
    # nature
    ('leaf', '#5DB55E'), ('leaf2', '#2F8A4E'), ('leafL', '#9BD36A'), ('soil', '#5E4535'), ('bark', '#6B4A36'),
    ('pot', '#F2EFE9'), ('terra', '#D27D57'),
    # lab and terrace
    ('esd', '#4E8C86'), ('pcb', '#2F7A4A'), ('copper', '#D08A4E'), ('foam', '#3C3F46'), ('foamB', '#5A5F69'),
    ('deck', '#B98A5E'), ('paver', '#BDB8AE'), ('fire', '#FF9A3C'),
    # skyline
    ('twGlass', '#9DBFD8'), ('twDark', '#5B6E84'), ('twSand', '#D8C3A0'), ('twBrick', '#C9876A'), ('twWhite', '#E6E2DA'),
    ('twWin', '#4E5F73'), ('solar', '#2E4A78'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
HEX2NAME = {h.upper(): n for (n, h) in ib_lib.PALETTES[FAM]}


class TKit(O.Kit):
    """The office Kit with this family's prefix, walkable collision boxes and extruded polygons."""

    def col(self, x0, x1, y0, y1, z0, z1, walk=False):
        self.cols.append((x0, x1, y0, y1, z0, z1, walk))

    def prism(self, pts, y0, y1, c, ink=True):
        """Polygon in the XZ plane, extruded along Y from y0 to y1."""
        P, bm = self.m.parent, self.m.bm
        a = [bm.verts.new(P @ Vector((x, y0, z))) for (x, z) in pts]
        b = [bm.verts.new(P @ Vector((x, y1, z))) for (x, z) in pts]
        fs = [bm.faces.new(a), bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.m._finish(a + b, c, False)
        self._mark(ink)

    def prism_y(self, pts, x0, x1, c, ink=True):
        """Polygon in the YZ plane, extruded along X."""
        P, bm = self.m.parent, self.m.bm
        a = [bm.verts.new(P @ Vector((x0, y, z))) for (y, z) in pts]
        b = [bm.verts.new(P @ Vector((x1, y, z))) for (y, z) in pts]
        fs = [bm.faces.new(a), bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.m._finish(a + b, c, False)
        self._mark(ink)

    def txt(self, text, x, y, z, cap, color, face='y-', font='sans', **kw):
        return ib_text.draw(self, text, x, y, z, cap, color, face=face, font=font, **kw)

    def finish(self, name, bevel=0.0, ao=False):
        full = PFX + name
        m = self.m
        check_zfight(full, m.bm, m.shape)
        flat = self.flat
        fb = m.bm.copy()
        bmesh.ops.delete(m.bm, geom=[f for f in m.bm.faces if f[m.shape] in flat], context='FACES')
        fm = Model(self.pal)
        fm.bm.free()
        fm.bm = fb
        fm.bw = fb.edges.layers.float['bevel_weight_edge']
        fm.shape = fb.faces.layers.int['shape_id']
        bmesh.ops.delete(fb, geom=[f for f in fb.faces if f[fm.shape] not in flat], context='FACES')
        obj = None
        if len(m.bm.faces):
            obj = build_object(full, m, bevel, HULL_T, ao=ao)
        else:
            m.bm.free()
        if len(fb.faces):
            o2 = build_object(full + '_flat', fm, 0, 0.0)
            strip_hull(o2)
            if obj is None:
                obj = o2
                obj.name = full
                obj.data.name = full
            else:
                join_into(obj, o2)
        else:
            fb.free()
        P = self.base.to_3x3()
        for i, (x0, x1, y0, y1, z0, z1, walk) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_%sCOL%d' % (full, 'W' if walk else '', i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj


srt = O.srt


def glint_y(k, x, y, z0, h, s=-1, w=0.07):
    """Two slanted highlight streaks on a glass plane at y (facing s * Y)."""
    for (dx, ww) in ((0.0, w), (0.16, w * 0.45)):
        a = x + dx
        k.poly([(a, y, z0), (a + ww, y, z0), (a + ww + h * 0.45, y, z0 + h), (a + h * 0.45, y, z0 + h)], 'glint', (0, s, 0))


def glint_x(k, x, y, z0, h, s=1, w=0.07):
    for (dy, ww) in ((0.0, w), (0.16, w * 0.45)):
        a = y + dy
        k.poly([(x, a, z0), (x, a + ww, z0), (x, a + ww + h * 0.45, z0 + h), (x, a + h * 0.45, z0 + h)], 'glint', (s, 0, 0))


def logo_mark(k, x, y, z, s, face=-1, d=0.003):
    """The NOVYX mark painted d in front of a -Y (face -1) or +Y (face 1) plane at y: four bars leaning right in the
    brand colours, s = its height, 1.5 s wide; (x, z) = its bottom-left corner as seen."""
    X = lambda u: x - face * u
    yy = y + face * d
    for i, c in enumerate(('violet', 'coral', 'sun', 'mint')):
        u0, w, sl = i * 0.3 * s, 0.2 * s, 0.4 * s
        k.poly([(X(u0), yy, z), (X(u0 + w), yy, z), (X(u0 + w + sl), yy, z + s), (X(u0 + sl), yy, z + s)], c, (0, face, 0))


# ================================================================ curtain wall (room toward -Y, outside +Y)
def window(k, kind):
    """1 m of the double-height curtain wall: open glazing (glints), the slab band at 4 m, head and sill, a slim
    black frame; Win_M adds the bay's mullion and an aluminium fin outside, Win_B an oak window bench."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.2, 0.0, 0.1, 'wallW', ink=False)                         # floor upstand
    k.bx(-0.5, 0.5, -0.515, -0.5, 0.0, 0.1, 'black', ink=False)                      # skirting line
    k.bx(-0.5, 0.5, -0.5, 0.2, DECK - 0.42, DECK + 0.08, 'wallW')                     # slab band (the floor line)
    k.bx(-0.5, 0.5, 0.2, 0.26, DECK - 0.5, DECK + 0.14, 'mullion', ink=False)        # dark spandrel glass outside
    k.bx(-0.5, 0.5, -0.5, 0.2, H - 0.5, H, 'wallW')                                   # head / ceiling bulkhead
    k.qz(-0.5, 0.5, -0.42, -0.3, H - 0.503, -1, 'glow')                              # light cove
    for (z0, z1) in ((0.1, 0.16), (DECK - 0.48, DECK - 0.42), (DECK + 0.08, DECK + 0.14), (H - 0.56, H - 0.5)):
        k.bx(-0.5, 0.5, 0.06, 0.14, z0, z1, 'mullion', ink=False)                    # frame rails at the glass line
    for zr in (0.95, DECK + 0.95):                                                   # safety rail on stand-offs, both storeys
        k.bx(-0.5, 0.5, -0.44, -0.38, zr, zr + 0.06, 'oak', ink=False)
        k.bx(-0.015, 0.015, -0.38, 0.06, zr + 0.015, zr + 0.045, 'steelD', ink=False)
    gx = {'A': -0.3, 'B': 0.1, 'M': -0.25}[kind]
    glint_y(k, gx, 0.059, 1.0, 0.9)
    glint_y(k, gx - 0.15, 0.059, DECK + 1.0, 0.85)
    k.bx(-0.5, 0.5, 0.2, 0.5, -0.6, 0.1, 'concrete')                                  # slab edge outside
    if kind == 'M':
        k.bx(-0.035, 0.035, 0.04, 0.19, 0.16, H - 0.56, 'mullion')
        k.bx(-0.05, 0.05, 0.26, 0.72, 0.1, H + 0.2, 'alu')                            # the fin outside
        k.bx(-0.06, 0.06, -0.53, -0.47, 0.1, H - 0.5, 'wallW', ink=False)             # a slim reveal inside
    elif kind == 'B':
        k.bx(-0.5, 0.5, -0.5, 0.05, 0.1, 0.42, 'oak2')
        k.bx(-0.5, 0.5, -0.5, 0.05, 0.42, 0.46, 'oak')
        k.bx(-0.48, 0.48, -0.46, 0.0, 0.46, 0.53, 'cushion', ink=False)
        k.bx(-0.5, 0.5, -0.52, -0.5, 0.12, 0.36, 'black', ink=False)                  # toe recess shadow
    return k


def win_corner(k):
    """Corner column (four-sided white, a slab ledge round it outside)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'wallW')
    for z in (DECK - 0.42, H - 0.5):
        k.qy(-0.5, 0.5, z - 0.006, z + 0.006, -0.503, -1, 'concrete')
        k.qy(-0.5, 0.5, z - 0.006, z + 0.006, 0.503, 1, 'concrete')
        k.qx(-0.5, 0.5, z - 0.006, z + 0.006, -0.503, -1, 'concrete')
        k.qx(-0.5, 0.5, z - 0.006, z + 0.006, 0.503, 1, 'concrete')
    return k


def screen(k):
    """Roof-terrace windscreen: frameless glass 1.9 m tall in a steel shoe, a top cap and an oak handrail; the
    parapet runs down outside. Nothing above it (the zone is open to the sky there)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, -0.3, 0.0, 0.16, 'steelD')                                 # glass on the inner edge of the cell
    k.bx(-0.5, 0.5, -0.42, -0.38, 0.16, 1.08, 'glass', ink=False)
    k.bx(-0.5, 0.5, -0.45, -0.35, 1.08, 1.14, 'oak')
    for s in (-1, 1):
        glint_y(k, -0.32, -0.4 + s * 0.023, 0.35, 0.6, s)
    k.bx(-0.5, 0.5, -0.3, 0.5, -0.7, 0.25, 'concrete')                                # the parapet beyond it
    k.bx(-0.5, 0.5, -0.3, 0.5, 0.25, 0.3, 'steel', ink=False)
    return k


def screen_corner(k):
    """Terrace corner: a concrete planter of grasses where the two windscreens meet (symmetric: it needs no turn)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, -0.7, 0.75, 'concrete')
    k.qz(-0.44, 0.44, -0.44, 0.44, 0.753, 1, 'soil')
    for i in range(7):
        a = i / 7 * math.pi * 2
        k.beam((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.75), (math.cos(a) * 0.4, math.sin(a) * 0.4, 1.35 + 0.1 * (i % 3)), 0.05, 'leafL' if i % 2 else 'sun')
    return k


def gate_side(k):
    """Lift-core cladding beside a gate (one-sided): oak lower storey with a slot light, white above."""
    k.begin()
    E = 0.496     # 4 mm short of the cell edges: the gate frame's posts stand on the gate's side of them
    k.bx(-E, E, -0.5, 0.5, 0, H, 'wallW')
    k.bx(-E, E, -0.56, -0.5, 0.08, 3.6, 'oak')
    for x in (-0.3, -0.1, 0.1, 0.3):
        k.qy(x - 0.006, x + 0.006, 0.13, 3.55, -0.563, -1, 'oak2')
    k.bx(-E, E, -0.57, -0.5, 0.0, 0.08, 'black', ink=False)
    k.qy(-0.03, 0.03, 3.7, H - 0.6, -0.503, -1, 'violet')
    return k


def core(k):
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'wallW')
    return k


def inner_wall(k, kind):
    """One-sided inner wall (room toward -Y): white plaster with a black skirting and a reveal at the deck line, and
    oak battens, a living green wall, a whiteboard full of diagrams or the brand supergraphic on it."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'wallW')
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.1, 'black', ink=False)
    if kind == 'Oak':
        k.bx(-0.5, 0.5, -0.53, -0.5, 0.1, H - 0.3, 'oak2', ink=False)
        for x in (-0.4, -0.2, 0.0, 0.2, 0.4):
            k.bx(x - 0.055, x + 0.055, -0.6, -0.53, 0.1, H - 0.3, 'oak')
    elif kind == 'Plant':
        k.bx(-0.5, 0.5, -0.56, -0.5, 0.4, H - 0.4, 'leaf2', ink=False)
        k.bx(-0.5, 0.5, -0.64, -0.5, 0.1, 0.4, 'oak')                                # planter trough at the foot
        k.qz(-0.5, 0.5, -0.63, -0.51, 0.403, 1, 'soil')
        rows = [(0.9 + i * 1.32) for i in range(5)]
        for i, z in enumerate(rows):
            for j, x in enumerate((-0.25, 0.25)):
                xx = x + 0.12 * math.sin(i * 1.7 + j * 2.3)
                c = ('leaf', 'leafL', 'leaf2', 'leaf')[(i + j * 2) % 4]
                r = 0.36 + 0.05 * ((i * 3 + j) % 3)
                jit = math.sin(i * 12.9898 + j * 78.233) * 43758.5453
                jit -= math.floor(jit)
                k.sph(xx + 0.03 * jit, -0.6 - 0.04 * jit, z + 0.1 * math.cos(i + j) + 0.02 * jit, r + 0.03 * jit, c, seg=(5 + (i + j) % 3, 4), scale=(1.0, 0.42 + 0.06 * jit, 0.8 + 0.1 * jit))
        for (x, z, c) in ((-0.2, 1.6, 'pink'), (0.25, 3.3, 'sun'), (-0.3, 5.1, 'pink'), (0.15, 6.4, 'coral')):
            k.sph(x, -0.75, z, 0.06, c, seg=(4, 3), ink=False)
    elif kind in ('BoardA', 'BoardB'):
        k.bx(-0.5, 0.5, -0.53, -0.5, 0.85, 2.35, 'steel', ink=False)                  # board frame
        k.qy(-0.5, 0.5, 0.88, 2.32, -0.533, -1, 'board')
        k.bx(-0.5, 0.5, -0.6, -0.53, 0.84, 0.88, 'steel', ink=False)                   # marker tray
        diagram(k, kind[-1], -0.536)
        k.bx(-0.5, 0.5, -0.55, -0.5, 2.9, 3.5, 'felt', ink=False)                       # acoustic felt band
        k.qy(-0.5, 0.5, 3.1, 3.2, -0.553, -1, 'violet' if kind == 'BoardA' else 'mint')
    else:   # Graphic: diagonal stripes at 45 deg (period 1 m: the modules run on seamlessly), a band, the mark
        cols = ('violet', 'coral', 'sun', 'mint')
        for i in range(-8, 9):
            c = cols[i % 4]
            z0 = 1.0 + i * 0.5
            pts = []
            for (x, z) in ((-0.5, z0), (-0.5, z0 + 0.22), (0.5, z0 + 1.22), (0.5, z0 + 1.0)):
                pts.append((x, z))
            pts = clip_poly(pts, 0.6, 6.4)
            if len(pts) >= 3:
                k.poly([(x, -0.503 - 0.0005 * (i % 2), z) for (x, z) in pts], c, (0, -1, 0))
        k.qy(-0.5, 0.5, 6.6, 6.7, -0.503, -1, 'black')
    return k


def clip_poly(poly, lo, hi):
    """Clip a polygon in (x, z) to lo <= z <= hi."""
    def cut(P, keep, zc):
        out = []
        for i in range(len(P)):
            p, q = P[i], P[(i + 1) % len(P)]
            ip, iq = keep(p[1]), keep(q[1])
            if ip:
                out.append(p)
            if ip != iq:
                t = (zc - p[1]) / (q[1] - p[1])
                out.append((p[0] + (q[0] - p[0]) * t, zc))
        return out
    P = cut(poly, lambda z: z >= lo, lo)
    return cut(P, lambda z: z <= hi, hi) if len(P) >= 3 else P


def diagram(k, v, y):
    """Marker drawings on a whiteboard plane at y (facing -Y), 1 m wide, 0.9 - 2.3 m: architecture boxes and
    arrows (A) or a sprint chart with sticky notes (B)."""
    n = [0]

    def line(x0, z0, x1, z1, c, w=0.012):
        # horizontal / vertical / sloping strokes on three depths (3 mm apart), sloping ones alternating, so no two
        # crossing strokes share a plane
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L * w, dx / L * w
        if abs(dz) < 1e-6:
            yy = y - 0.001
        elif abs(dx) < 1e-6:
            yy = y - 0.004
        else:
            n[0] += 1
            yy = y - 0.007 - 0.003 * (n[0] % 2)
        k.poly([(x0 + nx, yy, z0 + nz), (x1 + nx, yy, z1 + nz), (x1 - nx, yy, z1 - nz), (x0 - nx, yy, z0 - nz)], c, (0, -1, 0))

    def rect(x0, z0, x1, z1, c):
        line(x0, z0, x1, z0, c)
        line(x1, z0, x1, z1, c)
        line(x1, z1, x0, z1, c)
        line(x0, z1, x0, z0, c)
    if v == 'A':
        rect(-0.42, 1.85, -0.1, 2.15, 'ink')
        rect(0.08, 1.85, 0.4, 2.15, 'sky')
        rect(-0.3, 1.2, 0.25, 1.5, 'ink')
        line(-0.26, 1.85, -0.1, 1.5, 'ink')
        line(0.24, 1.85, 0.1, 1.5, 'sky')
        line(-0.1, 2.0, 0.08, 2.0, 'red')
        line(-0.35, 1.05, 0.3, 1.05, 'mint')
        for x in (-0.25, -0.05, 0.15):
            line(x, 1.3, x + 0.12, 1.3, 'ink', 0.008)
            line(x, 1.4, x + 0.08, 1.4, 'ink', 0.008)
        k.qy(0.28, 0.42, 1.1, 1.24, y - 0.014, -1, 'sun')
    else:
        for i, x in enumerate((-0.48, -0.16, 0.16)):
            line(x + 0.3, 0.95, x + 0.3, 2.25, 'ink', 0.006)
            for j in range(3 - (i % 2)):
                c = ('sun', 'pink', 'mint', 'sky')[(i + j) % 4]
                xx, zz = x + 0.04 + 0.12 * (j % 2), 2.05 - j * 0.3
                k.qy(xx, xx + 0.14, zz, zz + 0.14, y - 0.014, -1, c)
        line(-0.45, 2.27, 0.45, 2.27, 'ink', 0.01)
        line(-0.4, 1.0, -0.1, 1.25, 'red')
        line(-0.1, 1.25, 0.2, 1.12, 'red')
        line(0.2, 1.12, 0.44, 1.4, 'red')


def glass_wall(k, door=False):
    """The lab's full-height glass wall onto the terrace (both faces alike, 'open' glazing): half mullions on both
    module edges, the slab band at 4 m, head, a violet manifestation strip; door: a sliding doorway (open below
    2.6 m, header with a sensor, floor track)."""
    k.begin()
    for s in (-1, 1):
        a, b = srt(s * 0.4965, s * 0.472)
        k.bx(a, b, -0.06, 0.06, 0 if not door else 2.78, H - 0.4, 'mullion')
    k.bx(-0.5, 0.5, -0.5, 0.5, DECK - 0.42, DECK + 0.04, 'wallW')                    # slab edge (the deck abuts it)
    k.bx(-0.5, 0.5, -0.12, 0.12, H - 0.4, H, 'wallW')
    if door:
        k.bx(-0.5, 0.5, -0.1, 0.1, 2.6, 2.78, 'graphite')
        k.bx(-0.06, 0.06, -0.14, -0.1, 2.5, 2.6, 'black', ink=False)
        k.qz(-0.5, 0.5, -0.03, 0.03, 0.003, 1, 'steelD')
    else:
        k.bx(-0.469, 0.469, -0.03, 0.03, 0.0, 0.08, 'mullion', ink=False)
        k.bx(-0.469, 0.469, -0.01, 0.01, 1.2, 1.32, 'violet', ink=False)              # manifestation strip
        for s in (-1, 1):                                                              # floor tracks and grab rails on both faces
            a, b = srt(s * 0.5, s * 0.44)
            k.bx(-0.469, 0.469, a, b, 0.0, 0.06, 'steelD', ink=False)
            k.bx(-0.469, 0.469, a, b, 0.92, 0.97, 'oak', ink=False)
            k.bx(-0.012, 0.012, srt(s * 0.44, s * 0.03)[0], srt(s * 0.44, s * 0.03)[1], 0.93, 0.96, 'steelD', ink=False)
    for s in (-1, 1):
        glint_y(k, -0.25, s * 0.012 if door else s * 0.032, 4.6, 0.8, s)
        if not door:
            glint_y(k, 0.05, s * 0.032, 1.5, 0.75, s)
    return k


# ================================================================ gate, lift lobby, hatch, stand
def gate_frame(k):
    """Portal of the 3 m gates (both faces alike): white posts with oak liners, a black lintel with a violet light
    line, a white panel up to the 8 m head with the NOVYX mark and a stair / lift pictogram."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.1)
        k.bx(x0, x1, -0.6, 0.6, 0, 3.4, 'wallW')
        lx0, lx1 = srt(s * 1.47, s * 1.53)
        k.bx(lx0, lx1, -0.5, 0.5, 0.05, 3.35, 'oak', ink=False)
        k.bx(x0 + 0.01, x1 - 0.01, -0.61, 0.61, 0, 0.08, 'black', ink=False)
    k.bx(-2.1, 2.1, -0.6, 0.6, 3.4, 3.9, 'graphite')
    k.bx(-2.1, 2.1, -0.47, 0.47, 3.9, H - 0.005, 'wallW')
    for f in (-1, 1):
        y = f * 0.603
        k.qy(-2.0, 2.0, 3.6, 3.66, y, f, 'violet')
        logo_mark(k, f * 0.825, f * 0.47, 5.0, 1.1, f)
        k.txt(BRAND, 0.0, f * 0.473, 4.25, 0.36, 'graphite', face='y-' if f < 0 else 'y+', font=BRAND_FONT)
    return k


def gate_shutter(k):
    k.begin()
    Hs, n = 3.05, 10
    h = (Hs - 0.4) / n
    for i in range(n):
        z0 = 0.4 + i * h
        k.bx(-1.5, 1.5, -0.06, 0.06, z0, z0 + h, 'alu' if i % 2 else 'steel', ink=False)
        for f in (-1, 1):
            k.qy(-1.5, 1.5, z0 + h - 0.015, z0 + h - 0.005, f * 0.063, f, 'steelD')
    for j in range(6):
        x0 = -1.5 + j * 0.5
        k.bx(x0, x0 + 0.5, -0.07, 0.07, 0, 0.4, 'violet' if j % 2 else 'graphite', ink=False)
    return k


def trail_wall(k, kind=''):
    """Lift-lobby side, 1 m along Blender Y, corridor toward +X: white wall with an oak lower storey, a gallery
    ledge at 4 m (glass rail), white above; outside (-X) the link's glass face down to the set-back roof 4 m below;
    half the corridor's floor and roof slabs. kind: Lift (lift doors, indicator, call buttons), Plant (green wall),
    Stair (stair door and the floor directory), End (the hatch room's back wall: the logo)."""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, H, 'wallW')
    k.bx(0.25, 0.27, -0.5, 0.5, 0, 0.1, 'black', ink=False)
    # gallery ledge at 4 m with a glass rail
    k.bx(0.25, 0.95, -0.5, 0.5, DECK - 0.3, DECK, 'wallW')
    k.bx(0.9, 0.93, -0.5, 0.5, DECK, DECK + 0.95, 'glass', ink=False)
    k.bx(0.88, 0.95, -0.5, 0.5, DECK + 0.95, DECK + 1.0, 'oak')
    k.qz(0.3, 0.88, -0.5, 0.5, DECK + 0.003, 1, 'oak')
    if kind == 'Lift':
        k.bx(0.25, 0.3, -0.5, 0.5, 0.1, 3.0, 'steel')                                  # door surround
        k.bx(0.3, 0.33, -0.42, 0.42, 0.1, 2.5, 'alu', ink=False)                       # two leaves
        k.qx(-0.006, 0.006, 0.12, 2.48, 0.333, 1, 'steelD')
        k.bx(0.3, 0.34, -0.3, 0.3, 2.62, 2.86, 'screenD', ink=False)                   # floor indicator
        k.poly([(0.343, -0.2, 2.68), (0.343, -0.08, 2.68), (0.343, -0.14, 2.8)], 'mint', (1, 0, 0))
        k.poly([(0.343, 0.08, 2.8), (0.343, 0.2, 2.8), (0.343, 0.14, 2.68)], 'coral', (1, 0, 0))
        k.bx(0.3, 0.32, 0.44, 0.5, 1.0, 1.3, 'steelD', ink=False)                      # call buttons (half on each module edge)
    elif kind == 'Plant':
        k.bx(0.25, 0.31, -0.5, 0.5, 0.35, 3.3, 'leaf2', ink=False)
        k.bx(0.25, 0.45, -0.5, 0.5, 0.1, 0.35, 'oak')
        for i in range(4):
            for j, y in enumerate((-0.22, 0.24)):
                c = ('leaf', 'leafL', 'leaf2')[(i + j) % 3]
                k.sph(0.36 + 0.01 * j, y + 0.06 * math.sin(i * 2 + j), 0.7 + i * 0.75 + 0.05 * j, 0.27 + 0.02 * j, c, seg=(5 + j, 4), scale=(0.45, 1, 0.85))
    elif kind == 'Stair':
        k.bx(0.25, 0.3, -0.48, 0.48, 0.1, 2.3, 'oakD')                                 # door frame
        k.bx(0.3, 0.33, -0.42, 0.42, 0.1, 2.25, 'oak', ink=False)
        k.qx(-0.25, 0.25, 1.3, 1.9, 0.333, 1, 'glass')                                 # vision panel
        k.bx(0.33, 0.38, 0.28, 0.36, 1.0, 1.1, 'steelD', ink=False)
        k.bx(0.27, 0.32, -0.25, 0.25, 2.45, 2.7, 'mint', ink=False)                    # exit sign
        ib_text.draw(k, 'STAIR B', 0.323, 0.0, 2.51, 0.11, 'white', face='x+', font='cond', maxw=0.42)
        # the floor directory on the wall above the ledge
        k.bx(0.25, 0.29, -0.45, 0.45, 5.2, 6.9, 'graphite')
        for i, (fl, label, c) in enumerate((('33', 'LAB / TERRACE', 'mint'), ('29', 'ENGINEERING', 'sun'), ('27', 'RECEPTION', 'violet'))):
            z = 6.45 - i * 0.5
            k.qx(-0.4, -0.26, z, z + 0.28, 0.293, 1, c)
            ib_text.draw(k, fl, 0.296, -0.33, z + 0.05, 0.18, 'graphite', face='x+', font='display')
            ib_text.draw(k, label, 0.293, 0.06, z + 0.07, 0.12, 'white', face='x+', font='cond', maxw=0.56)
    elif kind == 'End':
        k.bx(0.25, 0.29, -0.5, 0.5, 4.6, 7.2, 'violet')
        k.bx(0.25, 0.3, -0.5, 0.5, 0.1, 3.4, 'oak2', ink=False)
        for y in (-0.3, -0.1, 0.1, 0.3):
            k.bx(0.3, 0.36, y - 0.05, y + 0.05, 0.1, 3.4, 'oak')
    else:
        k.bx(0.25, 0.28, -0.5, 0.5, 0.1, 3.5, 'oak2', ink=False)
        for y in (-0.375, -0.125, 0.125, 0.375):
            k.bx(0.28, 0.34, y - 0.05, y + 0.05, 0.1, 3.5, 'oak')
        k.bx(0.25, 0.27, -0.5, 0.5, 5.6, 5.7, 'violet', ink=False)
    # outside: the glass face of the link (spandrels at the floor lines), down to the set-back roof
    k.bx(-0.32, -0.25, -0.5, 0.5, -4.2, H + 0.36, 'twWin')
    for z in (-0.6, DECK - 0.35, H - 0.3):
        k.bx(-0.36, -0.32, -0.5, 0.5, z, z + 0.5, 'wallW', ink=False)
    k.bx(-0.375, -0.355, -0.03, 0.03, -4.2, H + 0.36, 'alu', ink=False)
    # slabs: floor (half, under the floor), roof (half)
    k.bx(-0.25, 2.25, -0.5, 0.5, -0.5, -0.004, 'concrete')
    k.bx(-0.25, 2.25, -0.5, 0.5, H + 0.02, H + 0.36, 'concrete')
    k.bx(-0.38, -0.25, -0.5, 0.5, H + 0.36, H + 0.6, 'wallW')
    return k


def ceil_light(k):
    """Lift-lobby ceiling light: a ring pendant 1.2 m across on three cables."""
    k.begin()
    k.cyl(0, 0, -1.58, 0.62, 0.62, 0.1, 'wallW', seg=14, caps=False)
    k.cyl(0, 0, -1.56, 0.6, 0.6, 0.006, 'glow', seg=14, ink=False)
    for i in range(3):
        a = i / 3 * math.pi * 2
        k.bx(math.cos(a) * 0.6 - 0.005, math.cos(a) * 0.6 + 0.005, math.sin(a) * 0.6 - 0.005, math.sin(a) * 0.6 + 0.005, -1.46, -0.01, 'steelD', ink=False)
    k.cyl(0, 0, -0.02, 0.08, 0.08, 0.016, 'wallW', seg=8, ink=False)
    return k


def hatch(k):
    """Exit: a glass lift car (open toward the approach, -Y): oak floor with brand chevrons, white frame, glass
    sides and back with glints, a canopy with a light ring and the floor display."""
    k.begin()
    k.bx(-1.3, 1.3, -1.3, 1.3, 0, 0.06, 'wallW')
    k.bx(-1.15, 1.15, -1.15, 1.15, 0.06, 0.07, 'oak', ink=False)
    for i in range(3):
        y = -0.7 + i * 0.45
        k.poly([(-0.55, y, 0.074), (0, y + 0.32, 0.074), (0, y + 0.46, 0.074), (-0.55, y + 0.14, 0.074)], ('violet', 'coral', 'mint')[i], (0, 0, 1))
        k.poly([(0, y + 0.32, 0.075), (0.55, y, 0.075), (0.55, y + 0.14, 0.075), (0, y + 0.46, 0.075)], ('violet', 'coral', 'mint')[i], (0, 0, 1))
    for (x, y) in ((-1.25, -1.25), (1.25, -1.25), (-1.25, 1.25), (1.25, 1.25)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.06, 2.9, 'wallW')
    for s in (-1, 1):
        k.bx(s * 1.25 - 0.012, s * 1.25 + 0.012, -1.2, 1.2, 0.06, 2.9, 'glass', ink=False)
        glint_x(k, s * 1.266, -0.4, 0.9, 1.0, s)
        k.bx(s * 1.25 - 0.03, s * 1.25 + 0.03, -1.19, 1.19, 1.0, 1.05, 'oak', ink=False)
    k.bx(-1.2, 1.2, 1.238, 1.262, 0.06, 2.9, 'glass', ink=False)
    glint_y(k, 0.2, 1.266, 0.9, 1.0, 1)
    k.bx(-1.35, 1.35, -1.35, 1.35, 2.9, 3.15, 'wallW')
    k.cyl(0, 0, 2.885, 0.7, 0.7, 0.012, 'glow', seg=16, ink=False)
    k.bx(-0.45, 0.45, -1.37, -1.35, 2.94, 3.11, 'screenD', ink=False)
    ib_text.draw(k, 'UP', 0.0, -1.373, 2.97, 0.11, 'mint', face='y-', font='display')
    k.cyl(0, 0, 3.15, 0.25, 0.25, 0.9, 'steelD', seg=8)                                   # the hoist (cables up)
    return k


def stand(k):
    """Weapon stand: a white product plinth with an oak top and a violet light line."""
    k.begin()
    k.bx(-0.45, 0.45, -0.42, 0.42, 0, 0.9, 'wallW')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0.9, 0.95, 'oak')
    k.qy(-0.4, 0.4, 0.12, 0.16, -0.423, -1, 'violet')
    k.bx(-0.46, 0.46, -0.43, 0.43, 0, 0.06, 'black', ink=False)
    k.col(-0.47, 0.47, -0.44, 0.44, 0, 0.95)
    return k


# ================================================================ circulation
def rail(k, y0, y1):
    """Glass balustrade on a white shoe with an oak handrail; one-cell module pieces."""
    k.bx(-0.05, 0.05, y0, y1, 0, 0.1, 'wallW', ink=False)
    k.bx(-0.012, 0.012, y0, y1, 0.1, 0.98, 'glass', ink=False)
    k.bx(-0.04, 0.04, y0, y1, 0.98, 1.05, 'oak', ink=False)
    for s in (-1, 1):
        x = s * 0.015
        ym = (y0 + y1) / 2
        k.poly([(x, ym - 0.12, 0.35), (x, ym - 0.07, 0.35), (x, ym + 0.08, 0.75), (x, ym + 0.03, 0.75)], 'glint', (s, 0, 0))


def rails(k):
    k.begin()
    rail(k, -0.5, -0.06)
    k.col(-0.09, 0.09, -0.5, 0.0, 0, 1.1)
    k.finish('Rail')
    k.begin()
    rail(k, -0.5, 0.5)
    k.col(-0.09, 0.09, -0.5, 0.5, 0, 1.1)
    k.finish('RailFull')
    k.begin()
    k.bx(-0.05, 0.05, -0.05, 0.05, 0, 1.0, 'wallW')
    k.bx(-0.065, 0.065, -0.065, 0.065, 1.0, 1.06, 'oak', ink=False)
    k.finish('RailPost')


def columns(k):
    """Round white columns on the deck edge: under the slab (0 - 3.6) and over it (deck - ceiling)."""
    for name, h in (('Column_Lo', DECK - 0.4), ('Column_Hi', H - DECK)):
        k.begin()
        k.cyl(0, 0, 0, 0.3, 0.3, h, 'wallW', seg=12)
        k.cyl(0, 0, 0, 0.312, 0.312, 0.1, 'black', seg=12, ink=False, caps=False)
        if name == 'Column_Lo':
            k.cyl(0, 0, 1.3, 0.306, 0.306, 0.08, 'violet', seg=12, ink=False, caps=False)
        k.col(-0.3, 0.3, -0.3, 0.3, 0, h)
        k.finish(name)


STEPS = 14
Y0S, Y1S = -5.0 + 0.9, 5.0 - 1.0
RUN, RISE = (Y1S - Y0S) / STEPS, DECK / STEPS


def stair(k):
    """3 x 10 open oak stair rising toward +Y (game north) to the 4 m deck: 14 floating oak treads on white
    stringers, glass balustrades with oak handrails; walkable stair boxes."""
    k.begin()
    k.bx(-1.3, 1.3, -5.0, Y0S, 0.0, 0.03, 'oak2', ink=False)
    k.col(-1.35, 1.35, -5.0, Y0S, 0, 0.03, True)
    for i in range(STEPS):
        a, top = Y0S + i * RUN, (i + 1) * RISE
        if i < STEPS - 1:      # the last tread is the landing's edge
            k.bx(-1.3, 1.3, a - 0.02, a + RUN + 0.02, top - 0.07, top, 'oak')
            k.qy(-1.25, 1.25, top - 0.06, top - 0.01, a - 0.023, -1, 'oakD')
        k.col(-1.35, 1.35, a, a + RUN, 0, top, True)
    k.bx(-1.3, 1.3, Y1S, 5.0, DECK - 0.4, DECK, 'oak')
    k.col(-1.35, 1.35, Y1S, 5.0, 0, DECK, True)
    for sx in (-1, 1):
        a, b = srt(sx * 1.3, sx * 1.45)
        prof = [(Y0S - 0.3, 0.0), (Y0S + 0.3, 0.0), (Y1S + 0.4, DECK - 0.55), (5.0, DECK - 0.55), (5.0, DECK + 0.05), (Y1S, DECK + 0.05), (Y0S - 0.3, 0.3)]
        k.prism_y(prof, a, b, 'wallW')
        gx = sx * 1.375
        gl = [(Y0S - 0.2, 0.3), (Y1S, DECK + 0.05), (4.8, DECK + 0.05), (4.8, DECK + 1.0), (Y1S + 0.05, DECK + 1.0), (Y0S, 1.25), (Y0S - 0.2, 1.25)]
        k.prism_y(gl, gx - 0.012, gx + 0.012, 'glass', ink=False)
        hr = [(Y0S - 0.25, 1.2), (Y1S + 0.05, DECK + 0.97), (4.85, DECK + 0.97), (4.85, DECK + 1.05), (Y1S + 0.06, DECK + 1.05), (Y0S - 0.26, 1.28)]
        k.prism_y(hr, gx - 0.04, gx + 0.04, 'oak')
        for t in (0.25, 0.6):
            yy = Y0S + (Y1S - Y0S) * t
            zz = 0.5 + DECK * t
            xg = sx * 1.393
            k.poly([(xg, yy, zz + 0.1), (xg, yy + 0.3, zz + 0.1 + 0.3 * DECK / (Y1S - Y0S)), (xg, yy + 0.5, zz + 0.65), (xg, yy + 0.2, zz + 0.5)], 'glint', (sx, 0, 0))
        for i in range(STEPS + 2):
            if i == 0:
                a2, b2, top = Y0S - 0.25, Y0S, 0.03
            elif i == STEPS + 1:
                a2, b2, top = Y1S, 4.8, DECK
            else:
                a2, b2, top = Y0S + (i - 1) * RUN, Y0S + i * RUN, i * RISE
            k.col(sx * 1.4 - 0.08, sx * 1.4 + 0.08, a2, b2, 0, top + 1.05)
    return k


def bleacher(k):
    """Landmark: 10 x 10 bleacher stair rising toward +Y to the deck. A 2.2 m walking lane of 14 steps on the east
    side; to the west, 7 seating tiers (two steps each) in oak with cushions in the brand colours, laptops and cups
    left on them, a planter; white sloped side walls with glass balustrades. Every tread and tier is a walkable box
    (the tiers are a jump up from the lane, robots step across where the heights meet)."""
    k.begin()
    LX0, LX1 = 2.5, 4.8      # walking lane
    SX0, SX1 = -4.8, 2.5     # seating
    k.bx(-4.8, 4.8, -5.0, Y0S, 0.0, 0.03, 'oak2', ink=False)
    k.col(-4.85, 4.85, -5.0, Y0S, 0, 0.03, True)
    for i in range(STEPS):
        a, top = Y0S + i * RUN, (i + 1) * RISE
        k.bx(LX0, LX1, a, a + RUN, 0.0 if i == 0 else top - RISE - 0.01, top, 'oak' if i % 2 else 'oak2')
        k.qz(LX0 + 0.05, LX1 - 0.05, a + 0.004, a + 0.04, top + 0.003, 1, 'black')
        k.col(LX0, LX1 + 0.05, a, a + RUN, 0, top, True)
    for t in range(STEPS // 2):
        a, top = Y0S + 2 * t * RUN, (2 * t + 2) * RISE
        k.bx(SX0, SX1, a, a + 2 * RUN, 0.0 if t == 0 else top - 2 * RISE - 0.01, top, 'oak')
        k.qy(SX0 + 0.02, SX1 - 0.02, top - 2 * RISE + 0.02, top - 0.04, a - 0.003, -1, 'oak2')
        k.col(SX0 - 0.05, SX1, a, a + 2 * RUN, 0, top, True)
        # cushions: runs of seat pads in the brand colours, a gap here and there
        x = SX0 + 0.15
        j = 0
        xm = SX1 - 0.15 if t != 2 else 1.4      # the planter stands at the end of the third tier
        while x < xm - 0.75:
            w = 1.1 + 0.3 * ((t + j) % 3)
            if (t * 3 + j) % 5 != 2:
                c = ('violet', 'coral', 'sun', 'mint', 'cushion')[(t + j * 2) % 5]
                k.bx(x, min(x + w, xm), a + 0.12, a + 2 * RUN - 0.15, top, top + 0.09, c, ink=False)
            x += w + 0.25
            j += 1
    k.bx(-4.8, 4.8, Y1S, 5.0, DECK - 0.4, DECK, 'oak')
    k.col(-4.85, 4.85, Y1S, 5.0, 0, DECK, True)
    # left on the tiers: laptops, cups, a book; a planter on the third tier
    for (x, t, ang, c) in ((-3.6, 1, 10, 'alu'), (-0.8, 3, -15, 'violet')):
        a, top = Y0S + 2 * t * RUN, (2 * t + 2) * RISE
        k.push(x, a + 0.45, ang, top + 0.09)
        k.bx(-0.17, 0.17, -0.12, 0.12, 0, 0.018, c)
        k.push(0, 0.12, 0, 0.018)
        k.beam((-0.16, 0, 0), (0.16, 0, 0), 0.01, c, ink=False)
        k.pop()
        k.poly([(-0.16, 0.12, 0.02), (0.16, 0.12, 0.02), (0.16, 0.2, 0.24), (-0.16, 0.2, 0.24)], c, (0, -1, 0.3))
        k.poly([(-0.14, 0.117, 0.035), (0.14, 0.117, 0.035), (0.14, 0.186, 0.222), (-0.14, 0.186, 0.222)], 'screen', (0, -1, 0.3))
        k.pop()
    for (x, t, c) in ((-2.9, 1, 'white'), (0.2, 3, 'coral'), (-1.5, 5, 'white')):
        a, top = Y0S + 2 * t * RUN, (2 * t + 2) * RISE
        k.cyl(x, a + 0.9, top + 0.09, 0.045, 0.04, 0.1, c, seg=6, ink=False)
    a, top = Y0S + 4 * RUN, 6 * RISE
    k.bx(1.55, 2.35, a + 0.25, a + 1.0, top, top + 0.45, 'wallW')
    k.sph(1.95, a + 0.62, top + 0.85, 0.45, 'leaf', seg=(7, 5))
    k.sph(1.8, a + 0.5, top + 1.15, 0.3, 'leafL', seg=(6, 4))
    k.col(1.55, 2.35, a + 0.25, a + 1.0, top, top + 0.45)
    # side walls (white, sloped), glass balustrades, oak handrails
    for sx in (-1, 1):
        a, b = srt(sx * 4.8, sx * 4.98)
        prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, DECK + 0.08), (Y1S, DECK + 0.08), (Y0S - 0.1, 0.25), (-5.0, 0.25)]
        k.prism_y(prof, a, b, 'wallW')
        gx = sx * 4.89
        gl = [(-4.8, 0.25), (Y0S - 0.1, 0.25), (Y1S, DECK + 0.08), (4.8, DECK + 0.08), (4.8, DECK + 1.0), (Y1S + 0.05, DECK + 1.0), (Y0S - 0.05, 1.15), (-4.8, 1.15)]
        k.prism_y(gl, gx - 0.012, gx + 0.012, 'glass', ink=False)
        hr = [(-4.85, 1.12), (Y0S - 0.05, 1.12), (Y1S + 0.05, DECK + 0.97), (4.85, DECK + 0.97), (4.85, DECK + 1.05), (Y1S + 0.06, DECK + 1.05), (Y0S - 0.06, 1.2), (-4.85, 1.2)]
        k.prism_y(hr, gx - 0.04, gx + 0.04, 'oak')
        k.prism_y([(-5.0, 0.12), (5.0, 0.12), (5.0, 0.2), (-5.0, 0.2)], (a if sx < 0 else b) - 0.004 if sx < 0 else b, (a if sx < 0 else b) if sx < 0 else b + 0.004, 'violet', ink=False)
        for t in (0.3, 0.7):
            yy = Y0S + (Y1S - Y0S) * t
            zz = 0.4 + DECK * t
            xg = sx * 4.905
            k.poly([(xg, yy, zz + 0.1), (xg, yy + 0.35, zz + 0.1 + 0.35 * DECK / (Y1S - Y0S)), (xg, yy + 0.55, zz + 0.7), (xg, yy + 0.2, zz + 0.55)], 'glint', (sx, 0, 0))
        for i in range(STEPS + 2):
            if i == 0:
                a2, b2, top = -5.0, Y0S, 0.03
            elif i == STEPS + 1:
                a2, b2, top = Y1S, 5.0, DECK
            else:
                a2, b2, top = Y0S + (i - 1) * RUN, Y0S + i * RUN, (i if sx > 0 else 2 * ((i + 1) // 2)) * RISE
            k.col(sx * 4.92 - 0.08, sx * 4.92 + 0.08, a2, b2, 0, top + 1.1)
    return k


# ================================================================ ceiling (layer 8) and under the deck
def baffles(k, v):
    """4 x 4 tile of hanging acoustic felt baffles (east-west), on cables from the ceiling plane, with a linear
    light between; A grey and violet, B grey with mint and sunflower."""
    k.begin()
    cols = ('felt', 'felt', 'violet', 'felt', 'felt') if v == 'A' else ('felt', 'felt', 'mint', 'felt', 'felt')
    for i, c in enumerate(cols):
        y = -1.6 + i * 0.8
        k.bx(-1.9, 1.9, y - 0.03, y + 0.03, -1.05, -0.6, c)
        for x in (-1.5, 1.5):
            k.bx(x - 0.005, x + 0.005, y - 0.005, y + 0.005, -0.6, -0.005, 'steelD', ink=False)
    for y in (-0.4, 0.4):
        k.bx(-1.8, 1.8, y - 0.05, y + 0.05, -0.86, -0.8, 'wallW', ink=False)
        k.qz(-1.78, 1.78, y - 0.035, y + 0.035, -0.863, -1, 'glow')
    return k


def pendant(k):
    """Linear LED pendant (1.6 m, black) hung 2.5 m below the ceiling."""
    k.begin()
    k.bx(-0.8, 0.8, -0.04, 0.04, -2.55, -2.47, 'black')
    k.qz(-0.78, 0.78, -0.025, 0.025, -2.553, -1, 'glow')
    for x in (-0.6, 0.6):
        k.bx(x - 0.004, x + 0.004, -0.004, 0.004, -2.47, -0.005, 'steelD', ink=False)
    return k


def under_light(k):
    """Downlight under the deck slab (the piece stands on the deck top; the slab underside is 0.4 m below)."""
    k.begin()
    k.cyl(0, 0, -0.43, 0.12, 0.12, 0.026, 'wallW', seg=10, ink=False)
    k.cyl(0, 0, -0.436, 0.085, 0.085, 0.006, 'glow', seg=10, ink=False)
    return k


def roof_tile(k, light):
    """4 x 4 roof slab over the lab (standing on the 8 m plane): white soffit with linear lights or a round
    acoustic raft with a downlight ring; the slab top and a parapet edge read from the terrace."""
    k.begin()
    k.bx(-2.0, 2.0, -2.0, 2.0, 0.0, 0.32, 'concrete', ink=False)
    k.qz(-2.0, 2.0, -2.0, 2.0, -0.003, -1, 'wallW')
    if light:
        k.cyl(0, 0, -0.35, 1.3, 1.3, 0.08, 'felt', seg=16)
        k.cyl(0, 0, -0.354, 1.1, 1.1, 0.004, 'glow', seg=16, ink=False)
        k.cyl(0, 0, -0.358, 0.9, 0.9, 0.004, 'felt', seg=16, ink=False)
        for a in (0.4, 2.5, 4.6):
            k.bx(math.cos(a) * 1.1 - 0.005, math.cos(a) * 1.1 + 0.005, math.sin(a) * 1.1 - 0.005, math.sin(a) * 1.1 + 0.005, -0.27, -0.005, 'steelD', ink=False)
    else:
        for y in (-1.0, 1.0):
            k.bx(-1.8, 1.8, y - 0.05, y + 0.05, -0.1, -0.006, 'wallW', ink=False)
            k.qz(-1.78, 1.78, y - 0.035, y + 0.035, -0.103, -1, 'glow')
    return k


# ================================================================ floor finishes (layer 0)
def carpet(k, v):
    """4 x 4 carpet tiles (0.5 m, two greys in a quarter-turn pattern), a brand stripe on B."""
    k.begin()
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.014, 1, 'felt')
    for t in (-1.0, 0.0, 1.0):                                   # 1 m tile joints, a little darker
        k.qz(-2.0, 2.0, t - 0.012, t + 0.012, 0.017, 1, 'graphite2')
        k.qz(t - 0.012, t + 0.012, -2.0, 2.0, 0.02, 1, 'graphite2')
    if v == 'B':
        k.qz(-2.0, 2.0, 1.55, 1.75, 0.023, 1, 'violet')
    return k


def epoxy(k):
    k.begin()
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.014, 1, 'esd')
    for t in (-1.0, 0.0, 1.0):
        k.qz(-2.0, 2.0, t - 0.006, t + 0.006, 0.017, 1, 'concrete')
        k.qz(t - 0.006, t + 0.006, -2.0, 2.0, 0.02, 1, 'concrete')
    return k


def decking(k):
    """4 x 4 timber decking, boards east-west with dark gaps."""
    k.begin()
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.016, 1, 'deck')
    for i in range(1, 27):
        y = -2.0 + i * 4.0 / 27
        k.qz(-2.0, 2.0, y - 0.008, y + 0.008, 0.019, 1, 'oakD')
    for x in (-1.0, 1.0):
        k.qz(x - 0.01, x + 0.01, -2.0, 2.0, 0.022, 1, 'oakD')
    return k


def pavers(k):
    """4 x 3 large-format pavers (0.75 m) with joints."""
    k.begin()
    k.qz(-2.0, 2.0, -1.5, 1.5, 0.016, 1, 'paver')
    for i in range(1, 6):
        x = -2.0 + i * 0.8
        k.qz(x - 0.01, x + 0.01, -1.5, 1.5, 0.019, 1, 'concrete')
    for y in (-0.75, 0.0, 0.75):
        k.qz(-2.0, 2.0, y - 0.01, y + 0.01, 0.022, 1, 'concrete')
    return k


# ================================================================ build
def build_kit_techhq(ao):
    import techhq_props as PR
    import techhq_city as CT
    pal = Palette(FAM)
    k = TKit(pal)
    # walls
    for kind in ('A', 'B', 'M'):
        window(k, kind).finish('Win_' + kind)
    win_corner(k).finish('WinCorner')
    screen(k).finish('Screen')
    screen_corner(k).finish('ScreenCorner')
    gate_side(k).finish('GateSide', ao=ao)
    core(k).finish('Core', ao=ao)
    for kind in ('Oak', 'Plant', 'BoardA', 'BoardB', 'Graphic'):
        inner_wall(k, kind).finish('Wall_' + kind, ao=ao)
    glass_wall(k).finish('GlassWall')
    glass_wall(k, True).finish('GlassDoor')
    # gate, lift lobbies, hatch, stand
    gate_frame(k).finish('GateFrame', ao=ao)
    shutter = gate_shutter(k).finish('GateShutter')
    m = Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    trail_wall(k).finish('TrailWall', ao=ao)
    for kind in ('Lift', 'Plant', 'Stair'):
        trail_wall(k, kind).finish('TrailWall_' + kind, ao=ao)
    ceil_light(k).finish('CeilLight')
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    # circulation
    rails(k)
    columns(k)
    stair(k).finish('Stair', ao=ao)
    bleacher(k).finish('Landmark_Bleacher', ao=ao)
    # ceiling, under the deck, roof tiles
    baffles(k, 'A').finish('Baffles_A')
    baffles(k, 'B').finish('Baffles_B')
    pendant(k).finish('Pendant')
    under_light(k).finish('UnderLight')
    roof_tile(k, False).finish('RoofTile')
    roof_tile(k, True).finish('RoofTile_Light')
    # floor finishes
    carpet(k, 'A').finish('Carpet_A')
    carpet(k, 'B').finish('Carpet_B')
    epoxy(k).finish('Epoxy')
    decking(k).finish('Decking')
    pavers(k).finish('Pavers')
    # furniture, labs, terrace, landmarks; the skyline
    PR.build(k, ao)
    CT.build(k)
    total = 0
    for n in sorted(k.tris):
        total += k.tris[n]
        print('%-34s %6d tris' % (n, k.tris[n]))
    print('kit-techhq: %d pieces, %d tris (one of each)' % (len(k.tris), total))
    export(FAM)


FAMILY = 'kit-techhq'
BUILD = build_kit_techhq
