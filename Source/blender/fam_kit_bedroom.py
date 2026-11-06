"""INKBOLT asset family: kit-bedroom (Big Bedroom, a "tiny" theme: the player is toy-sized, the furniture is giant).

Scale: about x6 around the player (1 m in game = ~17 cm in the real room). Walls run 18.4 m up to an 18 m ceiling.
Blender is Z-up; game +Z (south) = Blender -Y. A piece's origin is the centre of its cell / footprint at floor level.

Pieces (prefix KIT_BEDROOM_):
  Wall<s>_<Motif>_<D>    1 m wall modules, scheme s = 1 sky blue / 2 lilac / 3 pink (one per zone); motif Plain / Star /
                         Accent (cloud, moon, rainbow); D = side the painted face looks at as authored (S = Blender -Y,
                         E = +X, W = -X). Front face only (never seen from behind), skirting + wallpaper border.
                         E/W modules carry their horizontal trims 6 mm higher than S modules so inner corners never fight.
  Wall_Corner            hidden corner filler
  Landmark_Bed           10 x 15 m bed: run under it (frame bottom 2.4 m), legs are pillars. Origin = centre of a
                         10 x 1 anchor strip along the headboard; the bed reaches 14.5 m south of it.
  CeilingTile            1 m ceiling tile (env.ceiling.light, every 1 m) with custom normals facing up, so the ceiling
                         shades light instead of falling in the darkest toon band.
  ToyChest_A/B, Block_A..E, BookStack_A/B, Desk, Chair, Bookcase(_R), CubeShelf, Nightstand, ToyCastle, Ball,
  ToyCar_A/B, TrainEngine, TrainCar_A/B, CrayonPile_A/B, Pencil, ClothesPile, BrickTower,
  Rug_Round, Rug_Stripe, TrackLoop  (floor patches, no collision)
  Window, Poster_A..D(_R), WallShelf(_R), Door   (wall overlays: placed in the row in front of a wall module)
  CeilingLamp, CeilingStars_A/B, Mobile           (hung from the ceiling: placed at y = 18)
  GateFrame, GateShutter, TrailWall, Hatch
Collision boxes are <Piece>_COL<n> cube empties (location = box centre, scale = half extents).
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'kit-bedroom'
PFX = 'KIT_BEDROOM_'
ib_lib.GLB[FAM] = 'fps-kit-bedroom.glb'
ib_lib.CFG[FAM] = (0.03, 0.008)   # bevel (m), baked outline shell (m); the game widens outlines with distance

ib_lib.PALETTES[FAM] = BASE + [
    # wall paint per zone scheme (lower wall, upper wall, wallpaper border band)
    ('wall1', '#8ED2FF'), ('wall1u', '#CDEBFF'), ('band1', '#FFD45E'),
    ('wall2', '#C2B0F2'), ('wall2u', '#E5DCFB'), ('band2', '#4A4E9C'),
    ('wall3', '#FFB4CF'), ('wall3u', '#FFDFEA'), ('band3', '#FFF7EC'),
    ('trim', '#FFF9F0'), ('trim2', '#E9E0D2'),
    # woods
    ('wood', '#E2B077'), ('wood2', '#C79A6B'), ('wood3', '#A2724A'), ('birch', '#F3D9AE'),
    # toy primaries and pastels
    ('tblue', '#3F8CF0'), ('tyellow', '#FFC93C'), ('tgreen', '#5BCF4A'), ('torange', '#FF8A3D'),
    ('tpink', '#FF7FB0'), ('tpurple', '#8A6CD8'), ('tsky', '#8ED2FF'), ('tmint', '#7FDCC8'),
    ('pink', '#FFB4CF'), ('butter', '#FFE38A'), ('cream', '#FFF3DA'), ('lilac', '#C9B8F5'),
    ('navy', '#33377A'), ('glass', '#BCE5FF'), ('glint', '#F1FAFF'), ('metal', '#C9CFD6'), ('metal2', '#8F96A3'),
    ('lampshade', '#FFF0B8'), ('ticking', '#C4DCF2'), ('rubber', '#3A3644'), ('peach', '#FFC7A8'),
    ('rugpink', '#FFC9DA'), ('rugblue', '#C2E6FF'), ('rugyellow', '#FFF0B0'), ('rugmint', '#C9F0DE'),
    ('ceil', '#F6F2FF'),
]

CEIL = 18.0       # ceiling height (theme env.ceiling.height)
WALL_H = 18.4     # wall modules poke 0.4 m above the ceiling so the ceiling always meets them
TRAIL_H = 18.3    # trail bookcases
FRAME_H = 18.5    # gate built-in
FACE = 0.5        # wall face plane (|y| from the wall cell centre)
SKIRT_H, SKIRT_D = 0.9, 0.14
BAND_Z0, BAND_Z1, BAND_D = 8.0, 9.4, 0.05

SCHEMES = {
    '1': dict(lo='wall1', up='wall1u', band='band1', star='tblue', accent='cloud', acc='white'),
    '2': dict(lo='wall2', up='wall2u', band='band2', star='butter', accent='moon', acc='tyellow'),
    '3': dict(lo='wall3', up='wall3u', band='band3', star='tpink', accent='rainbow', acc='tsky'),
}
ROT = {'S': 0.0, 'E': 90.0, 'N': 180.0, 'W': -90.0}   # Blender Z rotation that turns an S-authored face (-Y) to D


# ================================================================ helpers
def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z):
    return Matrix.Translation(Vector((x, y, z)))


# local frame for shapes drawn on a wall facing -Y: local x = Blender x, local y = Blender z (up), extrude toward -Y
WALLF = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # local (x, y, z) -> (x, -z, y)


class Kit:
    """Model wrapper with prism/strip/grid builders on top of ib_lib.Model."""

    def __init__(self, pal):
        self.m = Model(pal)
        self.cols = []

    # ---- passthroughs (Model works in its own parent space)
    def box(self, loc, size, color, rot=(0, 0, 0), bevel=True):
        return self.m.box(loc, size, color, rot=rot, bevel=bevel)

    def bx(self, x0, x1, y0, y1, z0, z1, color, bevel=True, rot=(0, 0, 0)):
        """Box from extents."""
        return self.m.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), color, rot=rot, bevel=bevel)

    def cyl(self, loc, r1, r2, h, color, seg=12, rot=(0, 0, 0), bevel=True, caps=True):
        return self.m.cyl(loc, r1, r2, h, color, seg=seg, rot=rot, bevel=bevel, caps=caps)

    def sphere(self, loc, r, color, seg=(10, 6), scale=(1, 1, 1), rot=(0, 0, 0)):
        return self.m.sphere(loc, r, color, seg=seg, scale=scale, rot=rot)

    def beam(self, a, b, thick, color, bevel=False):
        return self.m.beam(a, b, thick, color, bevel=bevel)

    def col(self, x0, x1, y0, y1, z0, z1):
        """Collision box from Blender extents."""
        self.cols.append(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2))

    # ---- custom shapes
    def _mat(self, mat):
        return self.m.parent @ (mat if mat is not None else Matrix.Identity(4))

    def prism(self, pts, z0, z1, color, mat=None, bevel=False, fan=False, top=True, bottom=True):
        """Extrude a CCW 2D polygon (local x, y) from local z0 to z1, then transform by mat. fan=True for concave outlines."""
        M = self._mat(mat)
        bm = self.m.bm
        n = len(pts)
        if sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) < 0:
            pts = list(reversed(pts))      # outlines may come in either winding
        b = [bm.verts.new(M @ Vector((x, y, z0))) for x, y in pts]
        t = [bm.verts.new(M @ Vector((x, y, z1))) for x, y in pts]
        allv = b + t
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((b[i], b[j], t[j], t[i]))
        if fan:
            cx = sum(p[0] for p in pts) / n
            cy = sum(p[1] for p in pts) / n
            if top:
                ct = bm.verts.new(M @ Vector((cx, cy, z1)))
                allv.append(ct)
                for i in range(n):
                    bm.faces.new((ct, t[i], t[(i + 1) % n]))
            if bottom:
                cb = bm.verts.new(M @ Vector((cx, cy, z0)))
                allv.append(cb)
                for i in range(n):
                    bm.faces.new((cb, b[(i + 1) % n], b[i]))
        else:
            if top:
                bm.faces.new(t)
            if bottom:
                bm.faces.new(list(reversed(b)))
        return self.m._finish(allv, color, bevel)

    def strip(self, outer, inner, z0, z1, color, mat=None, bevel=False, bottom=False):
        """Band between two polylines of equal length, extruded z0..z1 (arcs, crescents). The back (z0) face is
        left out unless bottom=True; winding is fixed from the outline so normals face out."""
        n = len(outer)
        ring = list(outer) + list(reversed(inner))
        if sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring))) < 0:
            outer, inner = list(reversed(outer)), list(reversed(inner))
        M = self._mat(mat)
        bm = self.m.bm
        ob = [bm.verts.new(M @ Vector((x, y, z0))) for x, y in outer]
        ot = [bm.verts.new(M @ Vector((x, y, z1))) for x, y in outer]
        ib = [bm.verts.new(M @ Vector((x, y, z0))) for x, y in inner]
        it = [bm.verts.new(M @ Vector((x, y, z1))) for x, y in inner]
        for i in range(n - 1):
            bm.faces.new((ot[i], ot[i + 1], it[i + 1], it[i]))      # top
            if bottom:
                bm.faces.new((ob[i], ib[i], ib[i + 1], ob[i + 1]))
            bm.faces.new((ob[i + 1], ot[i + 1], ot[i], ob[i]))      # outer wall
            bm.faces.new((ib[i], it[i], it[i + 1], ib[i + 1]))      # inner wall
        bm.faces.new((ob[0], ot[0], it[0], ib[0]))                  # end caps
        bm.faces.new((ib[n - 1], it[n - 1], ot[n - 1], ob[n - 1]))
        return self.m._finish(ob + ot + ib + it, color, bevel)

    def grid_box(self, xs, ys, zs, color_fn, bevel=False, mat=None, skip=()):
        """Box with a lattice of quads (xs, ys, zs split lists); color_fn(normal_key, centre) -> palette name per quad."""
        M = self._mat(mat)
        bm = self.m.bm
        V = {}
        nx, ny, nz = len(xs) - 1, len(ys) - 1, len(zs) - 1

        def v(i, j, k):
            key = (i, j, k)
            if key not in V:
                V[key] = bm.verts.new(M @ Vector((xs[i], ys[j], zs[k])))
            return V[key]
        made = []

        def add(key, vs):
            if key not in skip:
                made.append((key, bm.faces.new(vs)))
        for i in range(nx):
            for j in range(ny):
                add('+z', (v(i, j, nz), v(i + 1, j, nz), v(i + 1, j + 1, nz), v(i, j + 1, nz)))
                add('-z', (v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0), v(i, j, 0)))
        for j in range(ny):
            for k in range(nz):
                add('+x', (v(nx, j, k), v(nx, j + 1, k), v(nx, j + 1, k + 1), v(nx, j, k + 1)))
                add('-x', (v(0, j, k + 1), v(0, j + 1, k + 1), v(0, j + 1, k), v(0, j, k)))
        for i in range(nx):
            for k in range(nz):
                add('+y', (v(i, ny, k), v(i, ny, k + 1), v(i + 1, ny, k + 1), v(i + 1, ny, k)))
                add('-y', (v(i + 1, 0, k), v(i + 1, 0, k + 1), v(i, 0, k + 1), v(i, 0, k)))
        self.m._finish(list(V.values()), color_fn('+z', Vector((0, 0, 0))), bevel)
        pal = self.m.pal
        for key, f in made:
            f.material_index = pal.index(color_fn(key, f.calc_center_median()))
        return [f for _, f in made]

    def obox(self, x0, x1, y0, y1, z0, z1, color, faces=('-y', '+z', '-x', '+x')):
        """Box with only the listed faces (the rest are never seen); corners shared so the outline shell stays closed."""
        M = self.m.parent
        bm = self.m.bm
        xs, ys, zs = (min(x0, x1), max(x0, x1)), (min(y0, y1), max(y0, y1)), (min(z0, z1), max(z0, z1))
        V = {}

        def v(i, j, kk):
            if (i, j, kk) not in V:
                V[(i, j, kk)] = bm.verts.new(M @ Vector((xs[i], ys[j], zs[kk])))
            return V[(i, j, kk)]
        quads = {'+z': ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), '-z': ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)),
                 '+x': ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), '-x': ((0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)),
                 '+y': ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)), '-y': ((1, 0, 0), (1, 0, 1), (0, 0, 1), (0, 0, 0))}
        for f in faces:
            bm.faces.new([v(*c) for c in quads[f]])
        return self.m._finish(list(V.values()), color, False)

    def recolor(self, faces, fn):
        pal = self.m.pal
        for f in faces:
            f.material_index = pal.index(fn(f))

    def quad(self, p0, p1, p2, p3, color):
        """Single one-sided quad (no hull needed behind it); points in parent space, CCW seen from the front."""
        bm = self.m.bm
        M = self.m.parent
        vs = [bm.verts.new(M @ Vector(p)) for p in (p0, p1, p2, p3)]
        bm.faces.new(vs)
        return self.m._finish(vs, color, False)

    def disc(self, cx, cy, z0, z1, r, color, seg=24, bottom=False):
        """Upright cylinder with a fan top (and optionally a bottom): rugs, coins, lids."""
        pts = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        return self.prism(pts, z0, z1, color, fan=True, bottom=bottom)

    # ---- output
    def build(self, name, bw=None, ht=None, ao=False, hull=True):
        dbw, dht = CFG[FAM]
        obj = build_object(PFX + name, self.m, dbw if bw is None else bw, dht if ht is None else ht, ao=ao)
        if not hull:
            strip_hull(obj)
        for i, (x, y, z, hx, hy, hz) in enumerate(self.cols):
            e = socket('%s%s_COL%d' % (PFX, name, i), obj, (x, y, z))
            e.scale = (hx, hy, hz)
            e.empty_display_type = 'CUBE'
            e.empty_display_size = 1.0
        return obj


def star_pts(R, cx=0.0, cy=0.0, n=5, inner=0.46, rot=90.0):
    out = []
    for i in range(n * 2):
        a = math.radians(rot) + i * math.pi / n
        r = R if i % 2 == 0 else R * inner
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def circle_pts(r, cx=0.0, cy=0.0, seg=12, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / seg), cy + r * math.sin(a0 + 2 * math.pi * i / seg)) for i in range(seg)]


def arc_pts(r, cx, cy, a0, a1, seg):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / seg)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / seg))) for i in range(seg + 1)]


def wall_mat(x, z, y_front, depth):
    """Matrix for a shape drawn in local (x, y=up) on a wall facing -Y: local z 0..depth extrudes from y_front + depth to y_front."""
    return T(x, y_front + depth, z) @ WALLF


def crescent_pts(R, seg=8):
    """Crescent as (outer, inner) arcs for Kit.strip, opening to the right."""
    return arc_pts(R, 0, 0, 60, 300, seg), arc_pts(R * 0.78, R * 0.34, 0, 78, 282, seg)


# ================================================================ walls
def build_walls(pal, ao):
    for s, S in SCHEMES.items():
        for motif in ('Plain', 'Star', 'Accent'):
            for d in ('S', 'E', 'W'):
                k = Kit(pal)
                k.m.parent = rz(ROT[d])
                dz = 0.0 if d == 'S' else 0.006       # E/W trims sit 6 mm higher: inner corners never share a plane
                y = -FACE
                # painted wall: one-sided quads (lower wall, upper wall); the trims cover the seam
                k.quad((-0.5, y, 0.0), (0.5, y, 0.0), (0.5, y, BAND_Z0 + 0.1), (-0.5, y, BAND_Z0 + 0.1), S['lo'])
                k.quad((-0.5, y, BAND_Z1 - 0.1), (0.5, y, BAND_Z1 - 0.1), (0.5, y, WALL_H), (-0.5, y, WALL_H), S['up'])
                # skirting board and its proud top bead (open profiles: only the faces the room can see)
                k.obox(-0.5, 0.5, y - SKIRT_D, y + 0.05, 0.0, SKIRT_H + dz, 'trim', faces=('-y', '+z'))
                k.obox(-0.5, 0.5, y - SKIRT_D - 0.035, y + 0.05, SKIRT_H + dz, SKIRT_H + 0.09 + dz, 'trim2', faces=('-y', '+z', '-z'))
                # wallpaper border band between two white strips
                k.obox(-0.5, 0.5, y - BAND_D, y + 0.05, BAND_Z0 + dz, BAND_Z1 + dz, S['band'], faces=('-y',))
                k.obox(-0.5, 0.5, y - BAND_D - 0.03, y + 0.05, BAND_Z0 - 0.12 + dz, BAND_Z0 + dz, 'trim', faces=('-y', '+z', '-z'))
                k.obox(-0.5, 0.5, y - BAND_D - 0.03, y + 0.05, BAND_Z1 + dz, BAND_Z1 + 0.12 + dz, 'trim', faces=('-y', '+z', '-z'))
                yb = y - BAND_D + 0.01            # motifs sink 1 cm into the band (their backs are never drawn)
                zc = (BAND_Z0 + BAND_Z1) / 2 + dz
                if motif == 'Star':
                    k.prism(star_pts(0.46), 0.0, 0.05, S['star'], mat=wall_mat(0.0, zc - 0.04, yb - 0.05, 0.05), fan=True, bottom=False)
                elif motif == 'Accent':
                    if S['accent'] == 'cloud':
                        for i, (px, pz, r) in enumerate([(-0.38, -0.05, 0.36), (0.36, -0.08, 0.32), (0.0, 0.12, 0.44)]):
                            dd = 0.05 + 0.006 * i
                            k.prism(circle_pts(r, seg=10), 0.0, dd, S['acc'], mat=wall_mat(px, zc + pz, yb - dd, dd), bottom=False)
                    elif S['accent'] == 'moon':
                        o, i = crescent_pts(0.5, seg=7)
                        k.strip(o, i, 0.0, 0.05, S['acc'], mat=wall_mat(0.05, zc, yb - 0.05, 0.05))
                        k.prism(star_pts(0.15), 0.0, 0.044, 'white', mat=wall_mat(0.44, zc + 0.38, yb - 0.04, 0.044), fan=True, bottom=False)
                        k.prism(star_pts(0.12), 0.0, 0.044, 'white', mat=wall_mat(-0.46, zc - 0.42, yb - 0.04, 0.044), fan=True, bottom=False)
                    else:   # rainbow: three arcs, each 6 mm prouder than the one outside it
                        for ri, (c, r0, r1) in enumerate((('red', 0.62, 0.78), ('tyellow', 0.46, 0.62), ('tsky', 0.30, 0.46))):
                            dd = 0.04 + ri * 0.006
                            k.strip(list(reversed(arc_pts(r1, 0, 0, 0, 180, 6))), list(reversed(arc_pts(r0, 0, 0, 0, 180, 6))),
                                    0.0, dd, c, mat=wall_mat(0.0, zc - 0.38, yb - dd, dd))
                k.build('Wall%s_%s_%s' % (s, motif, d), bw=0.0)
    k = Kit(pal)
    k.obox(-0.5, 0.5, -0.5, 0.5, 0.0, WALL_H, 'trim2', faces=('-y', '+y', '-x', '+x'))
    k.build('Wall_Corner', bw=0.0, hull=False)


# ================================================================ gate, shutter, trail, hatch
BOOK_COLORS = ['red', 'tblue', 'tyellow', 'tgreen', 'torange', 'tpink', 'tpurple', 'tmint', 'navy', 'tsky']


def books_row(k, x0, x1, z0, y_front, depth, seed, maxh, colors=BOOK_COLORS, spine=True):
    """Books standing in a row along local x (x0..x1) on a shelf at z0, spines facing -Y at y_front, in k.m.parent space.
    Each book is 1 cm narrower than its slot so neighbours never share a face; a few get a pale spine band."""
    import random
    rnd = random.Random(seed)
    x, n = x0, 0
    while x < x1 - 0.12:
        w = rnd.choice((0.14, 0.18, 0.22, 0.26, 0.3))
        if x + w > x1:
            w = x1 - x
            if w < 0.12:
                break
        h = maxh * rnd.uniform(0.7, 1.0)
        c = colors[rnd.randrange(len(colors))]
        d = depth * rnd.uniform(0.86, 1.0)
        k.obox(x + 0.005, x + w - 0.005, y_front, y_front + d, z0, z0 + h, c)
        if spine and w >= 0.18 and rnd.random() < 0.45:
            k.obox(x + 0.0005, x + w - 0.0005, y_front - 0.006, y_front + 0.04, z0 + h - 0.34, z0 + h - 0.22, 'cream', faces=('-y', '+z', '-z', '-x', '+x'))
        x += w + rnd.choice((0.0, 0.0, 0.02, 0.05))
        n += 1
    return n


TRAIL_VARIANTS = (('TrailWall', 101), ('TrailWall_B', 212), ('TrailWall_C', 323), ('TrailWall_D', 434), ('TrailWall_E', 545))


def shelf_mix(k, x0, x1, z0, zt, y_front, depth, rnd):
    """One bookcase bay (local x0..x1 on a shelf at z0 under zt, front at y_front facing -Y, in k.m.parent space):
    upright books of mixed width, height, depth and colour with spine bands or star stickers, a book leaning on its
    neighbour, a lying stack with its page block, bookends, and a toy now and then (alphabet block, ball, little car).
    Neighbours keep 1 cm gaps; marks sit 6 mm proud; no two shapes share a face."""
    hmax = zt - z0 - 0.1
    x, prev, toy, stack = x0 + rnd.uniform(0.0, 0.05), None, False, False
    while x1 - x > 0.12:
        room, r = x1 - x, rnd.random()
        if not stack and room > 0.66 and r < 0.13:                       # a stack lying flat
            w = min(room - 0.04, rnd.uniform(0.6, 0.86))
            z = z0
            for i in range(rnd.randint(2, 4)):
                t = rnd.uniform(0.14, 0.24)
                book(k, x + w / 2 + rnd.uniform(-0.02, 0.02), y_front + depth / 2, z + 0.004, w * rnd.uniform(0.86, 0.98), depth * 0.92, t,
                     rnd.uniform(-4, 4), rnd.choice(BOOK_COLORS), parent=k.m.parent)
                z += t + 0.004
            if not toy and rnd.random() < 0.5 and z + 0.5 < z0 + hmax:
                k.sphere((x + w / 2, y_front + depth / 2, z + 0.2), 0.2, rnd.choice(('red', 'tyellow', 'tblue')), seg=(8, 5))
                toy = True
            x += w + 0.06
            stack, prev = True, None
            continue
        if not toy and room > 0.5 and r < 0.24:                           # a toy
            kind = rnd.choice(('block', 'ball', 'car'))
            cx = x + 0.24
            if kind == 'block':
                s = rnd.uniform(0.36, 0.44)
                c, c2 = rnd.choice((('red', 'white'), ('tblue', 'butter'), ('tgreen', 'white'), ('tyellow', 'red')))
                k.obox(cx - s / 2, cx + s / 2, y_front, y_front + s, z0, z0 + s, c, faces=('-y', '+z', '-x', '+x'))
                k.obox(cx - s * 0.3, cx + s * 0.3, y_front - 0.006, y_front + 0.02, z0 + s * 0.2, z0 + s * 0.8, c2, faces=('-y', '+z', '-z', '-x', '+x'))
            elif kind == 'ball':
                k.sphere((cx, y_front + 0.1, z0 + 0.24), 0.24, rnd.choice(('red', 'tsky', 'tpink')), seg=(10, 6))
            else:
                c = rnd.choice(('red', 'tblue', 'tyellow'))
                k.obox(cx - 0.22, cx + 0.22, y_front + 0.02, y_front + 0.18, z0 + 0.08, z0 + 0.24, c, faces=('-y', '+z', '-x', '+x'))
                k.obox(cx - 0.12, cx + 0.1, y_front + 0.03, y_front + 0.17, z0 + 0.24, z0 + 0.38, 'glass', faces=('-y', '+z', '-x', '+x'))
                for wx in (-0.13, 0.13):
                    k.m.cyl((cx + wx, y_front + 0.012, z0 + 0.085), 0.085, 0.085, 0.04, 'rubber', seg=8, rot=(90, 0, 0), bevel=False)
            x += 0.5
            toy, prev = True, None
            continue
        if prev is None and room > 0.5 and r < 0.3:                        # a bookend
            c = rnd.choice(('metal', 'tpink', 'tmint'))
            k.obox(x, x + 0.2, y_front + 0.02, y_front + depth - 0.02, z0 + 0.006, z0 + 0.04, c, faces=('-y', '+z', '-x', '+x'))
            k.obox(x + 0.2, x + 0.24, y_front + 0.02, y_front + depth - 0.02, z0 + 0.006, z0 + 0.95, c, faces=('-y', '+z', '-x', '+x'))
            x += 0.252
            prev = ('end', x, 0.95)
            continue
        if prev is not None and prev[0] == 'book' and r < 0.45:            # a book leaning on its neighbour
            t = rnd.uniform(0.13, 0.2)
            h = min(hmax, prev[2] * rnd.uniform(0.88, 1.08))
            a = math.radians(rnd.uniform(12, 24))
            if h * math.cos(a) < prev[2] - 0.05 and room > h * math.sin(a) + t + 0.06:
                px = prev[1] + h * math.sin(a) + 0.014
                cx = px + t / 2 * math.cos(a) - h / 2 * math.sin(a)
                cz = z0 + t / 2 * math.sin(a) + h / 2 * math.cos(a) + 0.002
                k.box((cx, y_front + depth * 0.46, cz), (t - 0.006, depth * 0.9, h), rnd.choice(BOOK_COLORS), rot=(0, -math.degrees(a), 0), bevel=False)
                x = px + t * math.cos(a) + 0.04
                prev = None
                continue
        w = rnd.choice((0.13, 0.16, 0.2, 0.24, 0.28, 0.32))
        if w > room - 0.01:
            w = room - 0.01
            if w < 0.11:
                break
        h = hmax * rnd.uniform(0.6, 0.98)
        d = depth * rnd.uniform(0.8, 1.0)
        c = rnd.choice(BOOK_COLORS)
        yo = y_front + rnd.uniform(0.0, depth - d)
        k.obox(x, x + w - 0.01, yo, yo + d, z0, z0 + h, c)
        mark = rnd.choice((0, 1, 1, 2, 3))
        if w >= 0.16 and mark == 1:
            k.obox(x - 0.004, x + w - 0.006, yo - 0.006, yo + 0.04, z0 + h - 0.34, z0 + h - 0.22, 'cream', faces=('-y', '+z', '-z', '-x', '+x'))
        elif w >= 0.16 and mark == 2:
            for (a0, a1) in ((0.1, 0.14), (0.84, 0.88)):
                k.obox(x - 0.004, x + w - 0.006, yo - 0.006, yo + 0.04, z0 + h * a0, z0 + h * a1, 'navy' if c not in ('navy', 'tpurple') else 'butter', faces=('-y', '+z', '-z', '-x', '+x'))
        elif w >= 0.2 and mark == 3:   # a square sticker
            k.obox(x + w * 0.3, x + w * 0.7 - 0.01, yo - 0.006, yo + 0.04, z0 + h * 0.64, z0 + h * 0.64 + w * 0.4, 'butter' if c != 'tyellow' else 'white', faces=('-y', '+z', '-z', '-x', '+x'))
        prev = ('book', x + w - 0.01, h)
        x += w + rnd.choice((0.0, 0.0, 0.0, 0.012, 0.03))


def build_gate(pal, ao):
    # GateFrame: a white built-in around a 3 m opening, decorated the same on both faces (the entry gate shows its
    # back to the room). Half width 3.55 / depth 0.70 so no face lands on a wall-cell boundary or wall-module plane.
    k = Kit(pal)
    HW, HD, OW, OH = 3.55, 0.70, 1.5, 3.45
    k.obox(-HW, -OW, -HD, HD, 0.0, FRAME_H, 'trim', faces=('-y', '+y', '+x'))      # left tower (outer side hides in the wall)
    k.obox(OW, HW, -HD, HD, 0.0, FRAME_H, 'trim', faces=('-y', '+y', '-x'))        # right tower
    k.obox(-OW, OW, -HD, HD, OH, FRAME_H, 'trim', faces=('-y', '+y', '-z'))        # header over the opening
    for side in (0, 1):
        R = rz(180 * side)
        k.m.parent = R
        y = -HD
        # toy-garage surround: teal posts with hazard stripes, Pop Teal lights, butter lintel, red gable with a star
        for sx in (-1, 1):
            k.obox(sx * 1.47, sx * 2.12, y - 0.08, y + 0.05, 0.0, 3.9, 'teal', faces=('-y', '-x', '+x'))
            for i in range(3):
                z0 = 0.3 + i * 0.8
                pts = [(-0.28, 0.0), (0.28, 0.3), (0.28, 0.62), (-0.28, 0.32)] if sx < 0 else [(-0.28, 0.3), (0.28, 0.0), (0.28, 0.32), (-0.28, 0.62)]
                k.prism(pts, 0.0, 0.035, 'tyellow' if i % 2 == 0 else 'ink', mat=wall_mat(sx * 1.8, z0, y - 0.11, 0.035), bottom=False)
            k.obox(sx * 1.66, sx * 1.94, y - 0.2, y - 0.06, 3.0, 3.45, 'ink', faces=('-y', '+z', '-z', '-x', '+x'))
            k.obox(sx * 1.70, sx * 1.90, y - 0.24, y - 0.15, 3.06, 3.39, 'teal', faces=('-y', '+z', '-z', '-x', '+x'))
        k.obox(-2.2, 2.2, y - 0.12, y + 0.05, 3.9, 4.4, 'butter', faces=('-y', '-z', '-x', '+x'))
        k.prism([(-2.6, 0.0), (2.6, 0.0), (0.0, 1.6)], 0.0, 0.2, 'red', mat=wall_mat(0.0, 4.4, y - 0.18, 0.2), bottom=False)
        k.prism([(-1.9, 0.0), (1.9, 0.0), (0.0, 1.15)], 0.0, 0.06, 'tyellow', mat=wall_mat(0.0, 4.55, y - 0.23, 0.06), bottom=False)
        k.prism(star_pts(0.34), 0.0, 0.05, 'white', mat=wall_mat(0.0, 4.98, y - 0.27, 0.05), fan=True, bottom=False)
        # wall-hung shelves on the built-in: picture books over the door, a ball and a toy drum on the towers
        for sx in (-1, 1):
            lo, hi = (1.68, 3.42) if sx > 0 else (-3.42, -1.68)
            k.obox(lo - 0.06, hi + 0.06, y - 0.5, y + 0.03, 7.82, 8.0, 'trim2', faces=('-y', '+z', '-z', '-x', '+x'))
        k.obox(-3.1, -2.1, y - 0.46, y - 0.06, 8.0, 9.0, 'tsky', faces=('-y', '+z', '-x', '+x'))
        k.prism(star_pts(0.32), 0.0, 0.03, 'white', mat=wall_mat(-2.6, 8.5, y - 0.49, 0.035), fan=True, bottom=False)
        book(k, 2.55, y - 0.25, 8.0, 1.2, 0.42, 0.2, 4, 'red', parent=k.m.parent)
        book(k, 2.5, y - 0.25, 8.2, 1.05, 0.4, 0.18, -6, 'tmint', parent=k.m.parent)
        k.obox(-1.42, 1.42, y - 0.5, y + 0.03, 9.32, 9.5, 'trim2', faces=('-y', '+z', '-z', '-x', '+x'))
        books_row(k, -1.3, 1.3, 9.5, y - 0.44, 0.38, 41 + 3 * side, 2.5, spine=False)
        # the upper built-in is a wardrobe: two butter doors with raised panels and knobs, a cornice at the top
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.06, sx * 3.25))
            k.obox(x0, x1, y - 0.05, y + 0.02, 12.7, 17.25, 'butter', faces=('-y', '+z', '-z', '-x', '+x'))
            k.obox(x0 + 0.4, x1 - 0.4, y - 0.09, y + 0.0, 13.3, 16.65, 'butter', faces=('-y', '+z', '-z', '-x', '+x'))
            k.obox(sx * 0.32, sx * 0.44, y - 0.2, y - 0.05, 13.9, 15.9, 'tpink', faces=('-y', '+z', '-z', '-x', '+x'))   # bar handles
        k.obox(-3.6, 3.6, y - 0.16, y + 0.03, 17.45, 17.8, 'trim2', faces=('-y', '+z', '-z', '-x', '+x'))
        k.m.parent = Matrix.Identity(4)
    k.build('GateFrame', bw=0.03, ao=ao)

    # GateShutter: toy garage roll door, slats in the theme colours, hazard band at the foot
    k = Kit(pal)
    H, n = 3.05, 9
    for i in range(n):
        z = 0.55 + i * (H - 0.55) / n + (H - 0.55) / n / 2
        k.box((0, 0, z), (3.0, 0.14, (H - 0.55) / n - 0.05), ('pink', 'butter', 'tsky')[i % 3], bevel=False)
    for j in range(8):
        k.box((-1.5 + (j + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.16, 0.5), 'ink' if j % 2 else 'tyellow', bevel=False)
    k.box((0, 0, 0.66), (0.9, 0.2, 0.12), 'teal', bevel=False)
    obj = k.build('GateShutter', bw=0.0, ht=0.0)
    strip_hull(obj)
    k = Kit(pal)
    k.box((0, 0, H / 2), (3.0, 0.16, H), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', k.m, 0, 0.02)
    hull_only(tmp)
    join_into(obj, tmp)

    # TrailWall (+ _B.._E): 1 m of floor-to-ceiling bookcase, 0.5 m thick; books face +X (the trail), a plain wall
    # behind (-X). Open profiles only: the run is continuous, so module ends and backs are never seen. Five fills
    # (zones.js mixes them per module via theme.trail.variants) so the aisle never repeats one slice.
    import random
    for name, seed in TRAIL_VARIANTS:
        rnd = random.Random(seed)
        k = Kit(pal)
        k.quad((0.04, -0.5, 0.0), (0.04, 0.5, 0.0), (0.04, 0.5, TRAIL_H), (0.04, -0.5, TRAIL_H), 'trim2')       # case back (+X)
        k.quad((-0.25, 0.5, 0.0), (-0.25, -0.5, 0.0), (-0.25, -0.5, TRAIL_H), (-0.25, 0.5, TRAIL_H), 'wall1u')  # plain side (-X)
        k.obox(-0.39, -0.24, -0.5, 0.5, 0.0, SKIRT_H, 'trim', faces=('-x', '+z'))
        k.obox(-0.262, -0.249, 0.46, 0.54, SKIRT_H, TRAIL_H, 'trim', faces=('-x', '-y', '+y'))                   # batten over the seam
        k.obox(0.04, 0.25, -0.5, 0.5, 0.0, 0.7, 'trim', faces=('+x', '+z'))                                       # plinth
        shelves = [0.7, 3.6, 6.5, 9.4, 12.3, 15.2]
        for zs in shelves[1:]:
            k.obox(0.04, 0.25, -0.5, 0.5, zs - 0.16, zs, 'trim', faces=('+x', '+z', '-z'))
        k.obox(0.04, 0.27, -0.5, 0.5, TRAIL_H - 0.6, TRAIL_H, 'trim', faces=('+x', '-z'))
        k.m.parent = rz(90)   # rows authored along local x facing -Y, turned to run along Blender y facing +X
        for si, zs in enumerate(shelves[:-1]):
            shelf_mix(k, -0.48, 0.48, zs, shelves[si + 1] - 0.16, -0.23, 0.2, rnd)
        k.m.parent = Matrix.Identity(4)
        k.build(name, bw=0.0, ao=ao)

    # Hatch: a floor heating vent with a dark slot below the grille and teal corner lights
    k = Kit(pal)
    k.obox(-1.45, 1.45, -1.0, 1.0, 0.0, 0.1, 'trim', faces=('+z', '-x', '+x', '-y', '+y'))
    k.obox(-1.2, 1.2, -0.78, 0.78, 0.0, 0.104, 'gunmetal', faces=('+z',))
    for i in range(9):
        x = -1.08 + i * 0.27
        k.obox(x - 0.06, x + 0.06, -0.75, 0.75, 0.0, 0.13, 'metal', faces=('+z', '-x', '+x', '-y', '+y'))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.disc(sx * 1.3, sy * 0.86, 0.0, 0.14, 0.08, 'teal', seg=8)
    k.build('Hatch', bw=0.02)


# ================================================================ furniture
PATCH = ['pink', 'butter', 'tmint', 'cream', 'tsky', 'lilac']


def build_bed(pal, ao):
    """Landmark_Bed: 10 x 15 m bed, headboard at +Y (game north). Frame bottom 2.4 m: run under it.
    The origin is the centre of a 10 x 1 m anchor strip along the headboard (the map's 'T' cells), so the cells under
    the bed stay free for spawns and lost toys; the bed extends 14.5 m south of the anchor row."""
    k = Kit(pal)
    k.m.parent = T(0.0, -7.0, 0.0)
    LEG = 2.4
    # legs / posts (square, tapered toward the floor) with knobs on the posts
    posts = [(-4.65, 7.15, 8.2), (4.65, 7.15, 8.2), (-4.65, -7.15, 5.2), (4.65, -7.15, 5.2)]
    for (x, y, top) in posts:
        k.cyl((x, y, 0.0), 0.36, 0.44, LEG, 'wood', seg=4, rot=(0, 0, 45))
        k.obox(x - 0.33, x + 0.33, y - 0.33, y + 0.33, LEG, top, 'wood', faces=('+z', '-y', '+y', '-x', '+x'))
        k.obox(x - 0.37, x + 0.37, y - 0.37, y + 0.37, top - 0.5, top - 0.3, 'tpink', faces=('+z', '-z', '-y', '+y', '-x', '+x'))
        k.sphere((x, y, top + 0.32), 0.42, 'tpink', seg=(8, 4))
        k.col(x - 0.34, x + 0.34, y - 0.34, y + 0.34, 0.0, top + 0.7)
    for (x, y) in ((-4.65, 0.0), (4.65, 0.0)):
        k.cyl((x, y, 0.0), 0.34, 0.42, LEG, 'wood', seg=4, rot=(0, 0, 45))
        k.col(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0.0, LEG)
    for y in (-3.6, 3.6):    # centre supports under the slats
        k.cyl((0.0, y, 0.0), 0.26, 0.3, 2.45, 'wood3', seg=4, rot=(0, 0, 45), bevel=False)
        k.col(-0.24, 0.24, y - 0.24, y + 0.24, 0.0, 2.45)
    # side rails, slat ledges, centre beam, slats (what you see from under the bed)
    for sx in (-1, 1):
        k.obox(sx * 4.3, sx * 5.0, -6.82, 6.82, LEG, 3.25, 'wood', faces=('-z', '-x', '+x'))
        k.obox(sx * 4.08, sx * 4.3, -6.82, 6.82, 2.52, 2.68, 'wood3', faces=('-z', '-x' if sx > 0 else '+x'))
    k.obox(-0.3, 0.3, -6.82, 6.82, 2.45, 2.68, 'wood3', faces=('-z', '-x', '+x'))
    for i in range(11):
        y = -6.3 + i * 1.26
        k.obox(-4.3, 4.3, y - 0.27, y + 0.27, 2.68, 2.82, 'birch', faces=('-z', '-y', '+y'))
    # mattress: white sheet on top, ticking underneath (seen between the slats)
    k.grid_box([-4.3, 4.3], [-6.82, 6.82], [2.82, 4.1], lambda key, c: 'ticking' if key == '-z' else 'white')
    # patchwork duvet folded back at the head end, hanging over the rails
    xs = [-5.25 + i * 1.75 for i in range(7)]
    ys = [-7.0 + j * (10.6 / 6) for j in range(7)]
    zs = [2.95, 3.7, 4.45]

    def patch(key, c):
        i = int((c.x + 5.25) / 1.75)
        j = int((c.y + 7.0) / (10.6 / 6))
        kz = int((c.z - 2.95) / 0.75)
        if key in ('+z', '-z'):
            return PATCH[(i * 2 + j * 3 + (i * j) % 2) % len(PATCH)]
        if key in ('+x', '-x'):
            return PATCH[(j * 2 + kz * 3 + (1 if key == '+x' else 4)) % len(PATCH)]
        return PATCH[(i * 2 + kz * 3 + 2) % len(PATCH)]
    k.grid_box(xs, ys, zs, patch, bevel=True, skip=('-z',))
    for sx in (-1, 1):   # the duvet's hem seen from below, outside the rails
        k.obox(sx * 5.0, sx * 5.25, -7.0, 3.6, 2.95, 2.96, 'pink', faces=('-z',))
    k.obox(-5.0, 5.0, -7.0, -6.82, 2.95, 2.96, 'pink', faces=('-z',))
    k.cyl((-5.3, 3.6, 4.2), 0.42, 0.42, 10.6, 'cream', seg=10, rot=(0, 90, 0), bevel=False)     # folded-back edge
    # pillows
    for sx, c in ((-1, 'white'), (1, 'butter')):
        k.sphere((sx * 2.15, 5.6, 4.52), 1.0, c, seg=(10, 5), scale=(1.85, 1.05, 0.48))
    # headboard: arched panel down to 0.6 m (the head end under the bed is closed), sky inset, three stars
    arch = [(-4.32, 0.0), (4.32, 0.0)] + [(4.32 * math.cos(math.pi * i / 8), 6.6 + 1.0 * math.sin(math.pi * i / 8)) for i in range(9)]
    k.prism(arch, 0.0, 0.4, 'wood', mat=wall_mat(0.0, 0.6, 6.95, 0.4), bottom=True)
    inset = [(-3.7, 0.0), (3.7, 0.0)] + [(3.7 * math.cos(math.pi * i / 8), 5.0 + 0.8 * math.sin(math.pi * i / 8)) for i in range(9)]
    k.prism(inset, 0.0, 0.05, 'tsky', mat=wall_mat(0.0, 1.2, 6.91, 0.05), bottom=False)
    for (x, z, r) in ((-2.5, 5.75, 0.55), (0.0, 6.35, 0.72), (2.5, 5.75, 0.55)):
        k.prism(star_pts(r), 0.0, 0.06, 'tyellow', mat=wall_mat(x, z, 6.86, 0.06), fan=True, bottom=False)
    k.col(-4.32, 4.32, 6.95, 7.35, 0.0, 7.6)
    # footboard on the foot legs (bottom 2.4 m), rainbow on its outer face
    foot = [(-4.32, 0.0), (4.32, 0.0)] + [(4.32 * math.cos(math.pi * i / 8), 1.9 + 0.35 * math.sin(math.pi * i / 8)) for i in range(9)]
    k.prism(foot, 0.0, 0.4, 'wood', mat=wall_mat(0.0, LEG, -7.35, 0.4), bottom=True)
    for ri, (c, r0, r1) in enumerate((('red', 1.1, 1.4), ('tyellow', 0.8, 1.1), ('tsky', 0.5, 0.8))):
        dd = 0.05 + ri * 0.006
        k.strip(arc_pts(r1, 0, 0, 0, 180, 8), arc_pts(r0, 0, 0, 0, 180, 8), 0.0, dd, c, mat=wall_mat(0.0, LEG + 0.35, -7.35 - dd, dd))
    k.col(-4.32, 4.32, -7.35, -6.95, LEG, 4.3)
    # body collision: rails + duvet sides, slat level inside, centre beam
    for sx in (-1, 1):
        k.col(sx * 4.3, sx * 5.25, -7.0, 6.82, LEG, 4.45)
    k.col(-4.3, 4.3, -6.95, 6.95, 2.68, 4.45)
    k.col(-0.3, 0.3, -6.82, 6.82, 2.45, 2.68)
    k.m.parent = Matrix.Identity(4)
    k.cols = [(x, y - 7.0, z, hx, hy, hz) for (x, y, z, hx, hy, hz) in k.cols]
    k.build('Landmark_Bed', bw=0.06, ao=ao)


def build_toychest(pal, ao):
    for name, body, lid, shapes in (('ToyChest_A', 'tmint', 'butter', ('tpink', 'tblue', 'torange')),
                                    ('ToyChest_B', 'pink', 'tsky', ('tyellow', 'white', 'tpurple'))):
        k = Kit(pal)
        k.obox(-2.42, 2.42, -1.42, 1.42, 0.0, 0.3, 'wood3', faces=('-y', '+y', '-x', '+x'))
        k.bx(-2.35, 2.35, -1.35, 1.35, 0.3, 2.85, body)
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.obox(sx * 2.2, sx * 2.41, sy * 1.2, sy * 1.41, 0.3, 2.85, 'birch', faces=('-y', '+y', '-x', '+x'))
        k.bx(-2.47, 2.47, -1.47, 1.47, 2.85, 3.22, lid)
        k.obox(-2.25, 2.25, -1.25, 1.25, 3.22, 3.36, lid, faces=('+z', '-y', '+y', '-x', '+x'))
        # raised shapes on the front, rope handles on the ends
        k.prism(star_pts(0.62), 0.0, 0.07, shapes[0], mat=wall_mat(-1.35, 1.6, -1.42, 0.08), fan=True, bottom=False)
        k.prism(circle_pts(0.55, seg=14), 0.0, 0.07, shapes[1], mat=wall_mat(0.0, 1.6, -1.42, 0.08), bottom=False)
        k.prism([(-0.6, -0.45), (0.6, -0.45), (0.0, 0.6)], 0.0, 0.07, shapes[2], mat=wall_mat(1.35, 1.55, -1.42, 0.08), bottom=False)
        for sx in (-1, 1):
            x = sx * 2.35
            k.obox(x, x + sx * 0.05, -0.55, 0.55, 2.0, 2.35, 'wood3', faces=('-y', '+y', '+z', '-z', '+x' if sx > 0 else '-x'))
            for (a, b) in (((x + sx * 0.05, -0.45, 2.2), (x + sx * 0.3, -0.45, 1.8)), ((x + sx * 0.3, -0.45, 1.8), (x + sx * 0.3, 0.45, 1.8)),
                           ((x + sx * 0.3, 0.45, 1.8), (x + sx * 0.05, 0.45, 2.2))):
                k.beam(a, b, 0.11, 'cream')
        # a block left on the lid
        k.m.parent = T(1.2, 0.25, 3.36) @ rz(22)
        k.obox(-0.45, 0.45, -0.45, 0.45, 0.0, 0.9, 'red', faces=('+z', '-y', '+y', '-x', '+x'))
        k.prism(star_pts(0.3), 0.0, 0.03, 'white', mat=wall_mat(0.0, 0.45, -0.48, 0.035), fan=True, bottom=False)
        k.m.parent = Matrix.Identity(4)
        k.col(-2.47, 2.47, -1.47, 1.47, 0.0, 3.36)
        k.col(0.6, 1.8, -0.35, 0.85, 3.36, 4.26)
        k.build(name, bw=0.05, ao=ao)


LETTERS = {
    # strokes as (x0, z0, x1, z1, width) in a 0.6 x 0.6 cell centred on 0
    'A': [(-0.24, -0.27, 0.0, 0.27, 0.12), (0.24, -0.27, 0.0, 0.27, 0.12), (-0.13, -0.04, 0.13, -0.04, 0.09)],
    'E': [(-0.2, -0.27, -0.2, 0.27, 0.12), (-0.14, 0.24, 0.22, 0.24, 0.09), (-0.14, 0.0, 0.16, 0.0, 0.09), (-0.14, -0.24, 0.22, -0.24, 0.09)],
    'K': [(-0.2, -0.27, -0.2, 0.27, 0.12), (-0.12, 0.0, 0.22, 0.27, 0.1), (-0.06, 0.06, 0.22, -0.27, 0.1)],
    'M': [(-0.24, -0.27, -0.24, 0.27, 0.1), (0.24, -0.27, 0.24, 0.27, 0.1), (-0.2, 0.25, 0.0, 0.0, 0.09), (0.2, 0.25, 0.0, 0.0, 0.09)],
    'T': [(-0.25, 0.24, 0.25, 0.24, 0.11), (0.0, -0.27, 0.0, 0.18, 0.12)],
}


def stroke_pts(x0, z0, x1, z1, w):
    dx, dz = x1 - x0, z1 - z0
    L = math.hypot(dx, dz) or 1.0
    nx, nz = -dz / L * w / 2, dx / L * w / 2
    return [(x0 + nx, z0 + nz), (x0 - nx, z0 - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)]


def letter(k, ch, x, z, y_back, color, scale=1.0, mat=None):
    base = mat if mat is not None else Matrix.Identity(4)
    for i, (x0, z0, x1, z1, w) in enumerate(LETTERS[ch]):
        d = 0.03 + 0.004 * i               # every stroke a different depth: crossings never share a plane
        pts = [(px * scale, pz * scale) for px, pz in stroke_pts(x0, z0, x1, z1, w)]
        k.prism(pts, 0.0, d, color, mat=base @ wall_mat(x, z, y_back - d, d), bottom=False)


def shape(k, kind, x, z, y_back, color, size=0.3, mat=None):
    base = mat if mat is not None else Matrix.Identity(4)
    M = base @ wall_mat(x, z, y_back - 0.03, 0.03)
    if kind == 'star':
        k.prism(star_pts(size), 0.0, 0.03, color, mat=M, fan=True, bottom=False)
    elif kind == 'circle':
        k.prism(circle_pts(size * 0.85, seg=12), 0.0, 0.03, color, mat=M, bottom=False)
    elif kind == 'tri':
        k.prism([(-size, -size * 0.8), (size, -size * 0.8), (0.0, size * 0.9)], 0.0, 0.03, color, mat=M, bottom=False)
    else:
        k.prism([(0.0, -size), (size, 0.0), (0.0, size), (-size, 0.0)], 0.0, 0.03, color, mat=M, bottom=False)


BLOCKS = [('Block_A', 'red', 'A', 'white', 'star', 'butter'), ('Block_B', 'tblue', 'E', 'white', 'circle', 'tyellow'),
          ('Block_C', 'tyellow', 'K', 'tblue', 'tri', 'red'), ('Block_D', 'tgreen', 'M', 'white', 'star', 'butter'),
          ('Block_E', 'torange', 'T', 'white', 'diamond', 'tblue')]


def build_blocks(pal, ao):
    """1 m alphabet blocks: birch cube, painted panels on four sides and the top, raised letters and shapes."""
    for name, panel, ch, lc, kind, sc in BLOCKS:
        k = Kit(pal)
        h, e = 0.9, 0.44
        k.obox(-e, e, -e, e, 0.0, h, 'birch', faces=('+z', '-y', '+y', '-x', '+x'))
        for d in ('S', 'N', 'E', 'W'):
            k.m.parent = rz(ROT[d])
            k.obox(-0.355, 0.355, -e - 0.012, -e + 0.03, 0.09, 0.81, panel, faces=('-y', '+z', '-z', '-x', '+x'))
            if d in ('S', 'N'):
                letter(k, ch, 0.0, 0.45, -e - 0.012, lc, scale=0.98)
            else:
                shape(k, kind, 0.0, 0.45, -e - 0.012, sc, size=0.25)
        k.m.parent = Matrix.Identity(4)
        k.obox(-0.34, 0.34, -0.34, 0.34, h - 0.1, h + 0.012, panel, faces=('+z', '-y', '+y', '-x', '+x'))
        k.col(-0.47, 0.47, -0.47, 0.47, 0.0, h + 0.012)
        k.build(name, bw=0.0, ao=ao)


def book(k, x, y, z, w, d, t, yaw, cover, pages='white', parent=None):
    """A book lying flat: coloured cover with the page block showing on three sides (4 mm proud)."""
    base = parent if parent is not None else Matrix.Identity(4)
    k.m.parent = base @ T(x, y, z) @ rz(yaw)
    k.obox(-w / 2, w / 2, -d / 2, d / 2, 0.0, t, cover, faces=('+z', '-z', '-y', '+y', '-x', '+x'))
    k.obox(-w / 2 + 0.05, w / 2 + 0.004, -d / 2 - 0.004, d / 2 + 0.004, 0.035, t - 0.035, pages, faces=('-y', '+y', '+x'))
    k.m.parent = base


def build_bookstacks(pal, ao):
    for name, seq in (('BookStack_A', [('tblue', 0.92, 0.7, 0.2, -4), ('pink', 0.86, 0.66, 0.18, 6), ('tyellow', 0.9, 0.62, 0.22, -2),
                                       ('tgreen', 0.8, 0.6, 0.17, 9), ('red', 0.76, 0.56, 0.2, -7)]),
                      ('BookStack_B', [('navy', 0.94, 0.72, 0.22, 3), ('torange', 0.84, 0.64, 0.19, -8), ('tmint', 0.88, 0.62, 0.2, 5),
                                       ('tpurple', 0.78, 0.58, 0.18, -3), ('butter', 0.74, 0.54, 0.16, 10)])):
        k = Kit(pal)
        z = 0.0
        for c, w, d, t, yaw in seq:
            book(k, 0.0, 0.0, z, w, d, t, yaw, c)
            z += t
        k.col(-0.48, 0.48, -0.48, 0.48, 0.0, z)
        k.build(name, bw=0.0, ao=ao)


def build_desk(pal, ao):
    """Desk 8 x 4 m, top at 4.5 m: run under it. Front (chair side) at -Y. Lamp, pencil cup, globe, drawing on top."""
    k = Kit(pal)
    TOP = 4.5
    k.bx(-3.95, 3.95, -1.95, 1.95, TOP - 0.3, TOP, 'wood')
    k.obox(-3.75, -1.55, -1.75, 1.75, 0.0, TOP - 0.3, 'trim', faces=('-y', '+y', '-x', '+x'))
    for (z0, z1, c) in ((0.3, 1.55, 'tsky'), (1.68, 2.88, 'pink'), (3.0, 4.06, 'butter')):
        k.obox(-3.6, -1.7, -1.82, -1.75, z0, z1, c, faces=('-y', '+z', '-z', '-x', '+x'))
        k.cyl((-2.65, -1.82, (z0 + z1) / 2), 0.13, 0.13, 0.14, 'tyellow', seg=8, rot=(90, 0, 0), bevel=False)
    for sy in (-1, 1):
        k.obox(3.2, 3.7, sy * 1.2, sy * 1.7, 0.0, TOP - 0.3, 'trim', faces=('-y', '+y', '-x', '+x'))
    k.obox(-1.55, 3.2, 1.55, 1.72, 3.55, TOP - 0.3, 'trim', faces=('-y', '+y', '-z'))
    # desk lamp (hinged arms, cone shade aimed at the desk)
    k.disc(-2.7, 0.9, TOP, TOP + 0.14, 0.55, 'tpink', seg=12)
    k.beam((-2.7, 0.9, TOP + 0.1), (-2.25, 0.9, TOP + 2.0), 0.14, 'tpink')
    k.sphere((-2.25, 0.9, TOP + 2.0), 0.13, 'ink', seg=(6, 4))
    k.beam((-2.25, 0.9, TOP + 2.0), (-1.25, 0.9, TOP + 2.55), 0.115, 'tpink')
    k.cyl((-1.25, 0.9, TOP + 2.55), 0.18, 0.7, 0.85, 'tpink', seg=12, rot=(0, 145, 0))
    # pencil cup with pencils
    k.cyl((2.5, 1.0, TOP), 0.42, 0.45, 1.0, 'tblue', seg=12, caps=True)
    for (dx, dy, tilt, c) in ((-0.1, 0.05, (8, -6, 0), 'tyellow'), (0.12, -0.08, (-10, 4, 0), 'red'), (0.02, 0.15, (4, 12, 0), 'tgreen')):
        k.cyl((2.5 + dx, 1.0 + dy, TOP + 0.3), 0.075, 0.075, 1.6, c, seg=6, rot=tilt, bevel=False)
    # two books, a drawing on a sheet of paper, a globe
    book(k, 0.5, 1.05, TOP, 1.5, 1.1, 0.22, 8, 'tpurple')
    book(k, 0.55, 1.0, TOP + 0.22, 1.3, 1.0, 0.2, -5, 'torange')
    k.obox(0.9, 2.7, -1.5, -0.1, TOP, TOP + 0.02, 'white', faces=('+z', '-y', '+y', '-x', '+x'))
    k.disc(1.3, -0.55, TOP + 0.02, TOP + 0.035, 0.28, 'tyellow', seg=10)
    k.obox(1.75, 2.35, -1.2, -0.65, TOP + 0.02, TOP + 0.035, 'red', faces=('+z',))
    k.prism([(1.65, -0.65), (2.45, -0.65), (2.05, -0.3)], TOP + 0.02, TOP + 0.04, 'tblue', bottom=False)
    k.disc(-0.9, 1.0, TOP, TOP + 0.1, 0.4, 'tyellow', seg=10)
    k.cyl((-0.9, 1.0, TOP + 0.1), 0.06, 0.06, 0.5, 'tyellow', seg=6, bevel=False)
    g = k.sphere((-0.9, 1.0, TOP + 1.3), 0.75, 'tsky', seg=(12, 7))
    k.recolor(g, lambda f: 'tgreen' if (math.sin(f.calc_center_median().x * 6.1) + math.cos(f.calc_center_median().y * 5.3 + f.calc_center_median().z * 4.0)) > 0.9 else 'tsky')
    k.col(-3.75, -1.55, -1.75, 1.75, 0.0, TOP - 0.3)
    for sy in (-1, 1):
        k.col(3.2, 3.7, sy * 1.2, sy * 1.7, 0.0, TOP - 0.3)
    k.col(-1.55, 3.2, 1.55, 1.72, 3.55, TOP - 0.3)
    k.col(-3.95, 3.95, -1.95, 1.95, TOP - 0.3, TOP)
    k.build('Desk', bw=0.04, ao=ao)


def build_chair(pal, ao):
    """Kid's chair 3 x 3 m, seat at 2.75 m: run under it. Backrest at -Y (it faces +Y, toward a desk to its north)."""
    k = Kit(pal)
    SEAT = 2.75
    for sx in (-1, 1):
        for sy in (-1, 1):
            top = 5.5 if sy < 0 else SEAT - 0.3
            k.obox(sx * 1.05 - 0.17, sx * 1.05 + 0.17, sy * 1.05 - 0.17, sy * 1.05 + 0.17, 0.0, top, 'tmint', faces=('+z', '-y', '+y', '-x', '+x'))
            k.col(sx * 1.05 - 0.18, sx * 1.05 + 0.18, sy * 1.05 - 0.18, sy * 1.05 + 0.18, 0.0, top)
    for sy in (-1, 1):
        k.obox(-0.88, 0.88, sy * 1.05 - 0.08, sy * 1.05 + 0.08, 0.8, 0.98, 'tmint', faces=('-y', '+y', '+z', '-z'))
    k.bx(-1.32, 1.32, -1.32, 1.32, SEAT - 0.3, SEAT, 'butter')
    k.obox(-1.25, 1.25, -1.14, -0.96, 4.7, 5.35, 'pink', faces=('+z', '-z', '-y', '+y', '-x', '+x'))
    for x in (-0.55, 0.0, 0.55):
        k.obox(x - 0.09, x + 0.09, -1.1, -1.0, SEAT, 4.7, 'pink', faces=('-y', '+y', '-x', '+x'))
    k.col(-1.32, 1.32, -1.32, 1.32, SEAT - 0.3, SEAT)
    k.col(-1.25, 1.25, -1.2, -0.9, SEAT, 5.5)
    k.build('Chair', bw=0.04, ao=ao)


def build_bookcase(pal, ao):
    """Freestanding bookcase 5 x 2 m, 11 m tall, open front at -Y. _R: the same turned to face +Y."""
    for name, rot in (('Bookcase', 0), ('Bookcase_R', 180)):
        k = Kit(pal)
        R = rz(rot)
        k.m.parent = R
        H = 11.0
        for sx in (-1, 1):
            k.obox(sx * 2.28, sx * 2.45, -0.95, 0.95, 0.0, H - 0.3, 'trim', faces=('-y', '+y', '-x', '+x'))
        k.obox(-2.52, 2.52, -1.0, 1.0, H - 0.3, H, 'trim', faces=('+z', '-z', '-y', '+y', '-x', '+x'))
        k.obox(-2.28, 2.28, -0.85, 0.95, 0.0, 0.55, 'trim2', faces=('-y', '+z'))
        k.quad((2.28, 0.88, 0.55), (-2.28, 0.88, 0.55), (-2.28, 0.88, H - 0.3), (2.28, 0.88, H - 0.3), 'tsky')
        for zs in (3.1, 5.75, 8.35):
            k.obox(-2.28, 2.28, -0.95, 0.88, zs - 0.16, zs, 'trim', faces=('-y', '+z', '-z'))
        for ri, (z0, mh) in enumerate(((0.55, 2.3), (3.1, 2.4), (5.75, 2.3))):
            books_row(k, -2.2, 2.2, z0, -0.82, 0.75, 301 + ri * 13 + rot, mh)
        # top shelf: a ball, a block and a lying book
        k.sphere((-1.3, -0.1, 8.35 + 0.8), 0.8, 'red', seg=(10, 6))
        k.m.parent = R @ T(0.4, -0.15, 8.35) @ rz(18)
        k.obox(-0.5, 0.5, -0.5, 0.5, 0.0, 1.0, 'tyellow', faces=('+z', '-y', '+y', '-x', '+x'))
        k.m.parent = R
        book(k, 1.55, -0.05, 8.35, 1.1, 1.3, 0.25, -6, 'tgreen', parent=R)
        k.m.parent = Matrix.Identity(4)
        k.col(-2.52, 2.52, -1.0, 1.0, 0.0, H)
        k.build(name, bw=0.03, ao=ao)


def build_storage(pal, ao):
    # CubeShelf: 6 x 2 m cube organiser, open both ways (a room divider), fabric bins and books in the cubbies
    k = Kit(pal)
    H = 4.3
    for x in (-2.95, -1.0, 1.0, 2.95):
        w = 0.1 if abs(x) < 2 else 0.12
        k.obox(x - w, x + w, -0.9, 0.9, 0.0, H, 'trim', faces=('-y', '+y', '-x', '+x'))
    for z in (0.0, 2.1, H - 0.14):
        z0 = max(0.0, z)
        k.obox(-2.83, 2.83, -0.88, 0.88, z0, z0 + 0.14 if z > 0 else 0.25, 'trim', faces=('-y', '+y', '+z', '-z') if z > 0 else ('-y', '+y', '+z'))
    k.obox(-3.07, 3.07, -0.95, 0.95, H, H + 0.12, 'trim2', faces=('-y', '+y', '-x', '+x', '+z', '-z'))
    bins = [(-2.0, 0.25, 'pink'), (0.0, 2.24, 'tsky'), (2.0, 0.25, 'butter'), (-2.0, 2.24, 'tmint')]
    for (cx, z0, c) in bins:
        k.obox(cx - 0.8, cx + 0.8, -0.82, 0.82, z0, z0 + 1.62, c, faces=('-y', '+y', '-x', '+x', '+z'))
        for sy in (-1, 1):
            k.obox(cx - 0.32, cx + 0.32, sy * 0.82, sy * 0.825, z0 + 1.15, z0 + 1.38, 'ink', faces=('-y' if sy < 0 else '+y',))
    k.m.parent = Matrix.Identity(4)
    books_row(k, -0.86, 0.86, 0.25, -0.86, 1.7, 501, 1.75)
    k.sphere((2.0, 0.0, 2.24 + 0.78), 0.78, 'red', seg=(10, 6))
    k.col(-3.07, 3.07, -0.95, 0.95, 0.0, H + 0.12)
    k.build('CubeShelf', bw=0.03, ao=ao)

    # Nightstand: 3 x 3 m, drawer, open cubby, lamp with a drum shade, a book and a cup
    k = Kit(pal)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.cyl((sx * 1.05, sy * 0.95, 0.0), 0.12, 0.17, 0.4, 'wood', seg=6, bevel=False)
    k.bx(-1.3, 1.3, -1.2, 1.2, 0.4, 3.0, 'trim')
    k.obox(-1.15, 1.15, -1.25, -1.2, 2.1, 2.85, 'lilac', faces=('-y', '+z', '-z', '-x', '+x'))
    k.sphere((0.0, -1.32, 2.48), 0.14, 'tyellow', seg=(8, 4))
    k.obox(-1.1, 1.1, -1.205, -1.2, 0.6, 1.9, 'trim2', faces=('-y',))
    book(k, 0.0, -0.75, 0.6, 1.5, 0.9, 0.22, 4, 'tsky')
    k.m.parent = Matrix.Identity(4)
    k.sphere((-0.45, 0.25, 3.0 + 0.4), 0.45, 'tsky', seg=(8, 5))
    k.cyl((-0.45, 0.25, 3.7), 0.07, 0.07, 1.4, 'white', seg=6, bevel=False)
    k.cyl((-0.45, 0.25, 4.9), 0.95, 0.72, 1.15, 'lampshade', seg=12, bevel=False)
    book(k, 0.55, -0.35, 3.0, 0.9, 1.2, 0.18, -12, 'tpink')
    k.m.parent = Matrix.Identity(4)
    k.cyl((0.85, 0.5, 3.0), 0.22, 0.25, 0.55, 'glass', seg=8, bevel=False)
    k.col(-1.3, 1.3, -1.25, 1.2, 0.0, 3.0)
    k.build('Nightstand', bw=0.03, ao=ao)

    # ClothesPile: folded tees, a rolled scarf and a striped sock
    k = Kit(pal)
    for i, (c, w, d, t, yaw, dx, dy) in enumerate((('tsky', 2.3, 1.9, 0.38, 6, 0.0, 0.0), ('pink', 2.1, 1.7, 0.36, -9, 0.1, -0.1),
                                                  ('butter', 1.9, 1.6, 0.34, 14, -0.1, 0.1))):
        z = 0.38 * i
        k.m.parent = T(dx, dy, z) @ rz(yaw)
        k.bx(-w / 2, w / 2, -d / 2, d / 2, 0.0, t - 0.004, c)
        k.obox(-w / 2 + 0.25, w / 2 - 0.25, -d / 2 - 0.004, -d / 2 + 0.3, t - 0.004, t + 0.02, c, faces=('+z', '-y', '-x', '+x'))
    k.m.parent = T(-0.4, 0.2, 1.1) @ rz(-30)
    k.cyl((-1.1, 0.0, 0.3), 0.3, 0.3, 2.2, 'tmint', seg=10, rot=(0, 90, 0), bevel=False)
    for x in (-0.6, 0.1, 0.8):
        k.cyl((x, 0.0, 0.3), 0.31, 0.31, 0.22, 'white', seg=10, rot=(0, 90, 0), bevel=False, caps=False)
    k.m.parent = T(0.3, -1.05, 0.0) @ rz(15)
    for i, c in enumerate(('red', 'white', 'red', 'white', 'red')):
        k.cyl((-1.3 + i * 0.42, 0.0, 0.22), 0.22, 0.22, 0.42 - 0.004, c, seg=8, rot=(0, 90, 0), bevel=False)
    k.sphere((0.85, 0.12, 0.22), 0.24, 'red', seg=(8, 5), scale=(1.3, 1.0, 1.0))
    k.m.parent = Matrix.Identity(4)
    k.col(-1.3, 1.3, -1.35, 1.2, 0.0, 1.4)
    k.build('ClothesPile', bw=0.05, ao=ao)


def build_toys(pal, ao):
    # Ball: a striped play ball (beach-ball gores, white caps)
    k = Kit(pal)
    f = k.sphere((0.0, 0.0, 1.3), 1.3, 'white', seg=(16, 10))
    gores = ['red', 'tyellow', 'tblue', 'tgreen', 'torange', 'tpink']

    def gore(face):
        c = face.calc_center_median()
        if abs(c.z - 1.3) > 1.05:
            return 'white'
        a = (math.atan2(c.y, c.x) + math.pi) / (2 * math.pi)
        return gores[int(a * 6) % 6]
    k.recolor(f, gore)
    k.col(-1.05, 1.05, -1.05, 1.05, 0.15, 2.45)
    k.build('Ball', bw=0.0, ao=ao)

    # ToyCar_A/B: chunky toy car pointing +X
    for name, body in (('ToyCar_A', 'red'), ('ToyCar_B', 'tblue')):
        k = Kit(pal)
        k.bx(-1.45, 1.45, -0.78, 0.78, 0.35, 1.05, body)
        k.bx(-0.8, 0.55, -0.66, 0.66, 1.05, 1.72, body)
        k.obox(-0.68, -0.2, -0.672, 0.672, 1.15, 1.6, 'glass', faces=('-y', '+y', '+z', '-z', '-x', '+x'))
        k.obox(-0.08, 0.38, -0.672, 0.672, 1.15, 1.6, 'glass', faces=('-y', '+y', '+z', '-z', '-x', '+x'))
        k.obox(0.55, 0.567, -0.5, 0.5, 1.12, 1.58, 'glass', faces=('+x', '+z', '-z', '-y', '+y'))
        for sx in (-1, 1):
            k.obox(sx * 1.45, sx * 1.55, -0.7, 0.7, 0.45, 0.68, 'metal', faces=('+x' if sx > 0 else '-x', '+z', '-z', '-y', '+y'))
            for sy in (-1, 1):
                k.cyl((sx * 0.92, sy * 0.92, 0.36), 0.36, 0.36, 0.26, 'rubber', seg=8, rot=(90 if sy > 0 else -90, 0, 0), bevel=False)
                k.cyl((sx * 0.92, sy * 0.945, 0.36), 0.17, 0.17, 0.025, 'white', seg=8, rot=(90 if sy > 0 else -90, 0, 0), bevel=False)
        # one wide light bar front and back (no pair of round lamps: nothing on the toys reads as a face)
        k.obox(1.45, 1.49, -0.55, 0.55, 0.74, 0.9, 'tyellow', faces=('+x', '+z', '-z', '-y', '+y'))
        k.obox(-1.49, -1.45, -0.55, 0.55, 0.74, 0.9, 'torange', faces=('-x', '+z', '-z', '-y', '+y'))
        k.col(-1.55, 1.55, -0.95, 0.95, 0.0, 1.72)
        k.build(name, bw=0.06, ao=ao)

    # TrainEngine: wooden toy engine (no face), chimney toward -X
    k = Kit(pal)
    k.obox(-1.95, 1.95, -0.7, 0.7, 0.3, 0.62, 'wood3', faces=('+z', '-z', '-y', '+y', '-x', '+x'))
    k.cyl((-1.9, 0.0, 1.27), 0.64, 0.64, 2.25, 'red', seg=12, rot=(0, 90, 0), bevel=False)
    k.cyl((-1.94, 0.0, 1.27), 0.5, 0.5, 0.04, 'ink', seg=12, rot=(0, 90, 0), bevel=False)
    k.cyl((-1.35, 0.0, 1.8), 0.24, 0.34, 0.85, 'rubber', seg=10, bevel=False)
    k.sphere((-0.5, 0.0, 1.88), 0.32, 'tyellow', seg=(8, 4))
    k.bx(0.35, 1.9, -0.7, 0.7, 0.62, 2.2, 'tblue')
    k.bx(0.25, 2.0, -0.85, 0.85, 2.2, 2.4, 'tyellow')
    for sy in (-1, 1):
        k.obox(0.75, 1.5, sy * 0.7, sy * 0.71, 1.3, 1.95, 'butter', faces=('-y' if sy < 0 else '+y', '+z', '-z', '-x', '+x'))
        for x in (-1.3, -0.3, 0.95):
            k.cyl((x, sy * 0.92, 0.38), 0.38, 0.38, 0.2, 'tyellow', seg=10, rot=(90 if sy > 0 else -90, 0, 0), bevel=False)
            k.cyl((x, sy * 0.95, 0.38), 0.14, 0.14, 0.03, 'red', seg=8, rot=(90 if sy > 0 else -90, 0, 0), bevel=False)
    k.cyl((1.95, 0.0, 0.46), 0.14, 0.14, 0.3, 'rubber', seg=8, rot=(0, 90, 0), bevel=False)
    k.col(-2.0, 2.0, -0.95, 0.95, 0.0, 2.65)
    k.build('TrainEngine', bw=0.05, ao=ao)

    # TrainCar_A/B: open wagons with cargo
    for name, c, cargo in (('TrainCar_A', 'tyellow', 'blocks'), ('TrainCar_B', 'tgreen', 'ball')):
        k = Kit(pal)
        k.bx(-1.45, 1.45, -0.7, 0.7, 0.3, 0.6, 'wood3')
        k.obox(-1.4, 1.4, -0.68, 0.68, 0.6, 1.6, c, faces=('-y', '+y', '-x', '+x'))
        k.quad((-1.28, -0.56, 1.3), (1.28, -0.56, 1.3), (1.28, 0.56, 1.3), (-1.28, 0.56, 1.3), 'wood2')
        for sy in (-1, 1):
            k.obox(-1.4, 1.4, sy * 0.56, sy * 0.68, 1.3, 1.6, c, faces=('+z', '+y' if sy < 0 else '-y'))
        for sx in (-1, 1):
            k.obox(sx * 1.28, sx * 1.4, -0.56, 0.56, 1.3, 1.6, c, faces=('+z', '+x' if sx < 0 else '-x'))
        for sy in (-1, 1):
            for x in (-0.85, 0.85):
                k.cyl((x, sy * 0.91, 0.38), 0.36, 0.36, 0.2, 'red', seg=10, rot=(90 if sy > 0 else -90, 0, 0), bevel=False)
        if cargo == 'blocks':
            for (x, z, yaw, bc) in ((-0.6, 1.3, 12, 'tblue'), (0.55, 1.3, -18, 'red'), (0.0, 2.15, 30, 'tgreen')):
                k.m.parent = T(x, 0.0, z) @ rz(yaw)
                k.obox(-0.42, 0.42, -0.42, 0.42, 0.0, 0.84, bc, faces=('+z', '-y', '+y', '-x', '+x'))
                k.m.parent = Matrix.Identity(4)
        else:
            k.sphere((0.0, 0.0, 1.95), 0.85, 'tpink', seg=(12, 6))
        k.col(-1.5, 1.5, -0.95, 0.95, 0.0, 2.4)
        k.build(name, bw=0.04, ao=ao)

    # CrayonPile_A/B: three jumbo crayons, two on the floor, one on top
    for name, cols in (('CrayonPile_A', ('red', 'tblue', 'tyellow')), ('CrayonPile_B', ('tgreen', 'torange', 'tpurple'))):
        k = Kit(pal)
        for (dy, z, yaw, dx), c in zip(((-0.3, 0.27, 4, 0.0), (0.32, 0.27, -3, -0.15), (0.0, 0.79, 14, 0.2)), cols):
            k.m.parent = T(dx, dy, z) @ rz(yaw)
            k.cyl((-1.25, 0.0, 0.0), 0.26, 0.26, 2.15, c, seg=10, rot=(0, 90, 0), bevel=False)
            k.cyl((0.9, 0.0, 0.0), 0.26, 0.07, 0.45, c, seg=10, rot=(0, 90, 0), bevel=False)
            k.cyl((-1.05, 0.0, 0.0), 0.276, 0.276, 1.55, c, seg=10, rot=(0, 90, 0), bevel=False, caps=False)
            for x0 in (-0.98, 0.32):
                k.cyl((x0, 0.0, 0.0), 0.29, 0.29, 0.08, 'ink', seg=10, rot=(0, 90, 0), bevel=False, caps=False)
            k.cyl((-0.55, 0.0, 0.0), 0.284, 0.284, 0.62, 'cream', seg=10, rot=(0, 90, 0), bevel=False, caps=False)
            k.m.parent = Matrix.Identity(4)
        k.col(-1.45, 1.45, -0.62, 0.62, 0.0, 1.05)
        k.build(name, bw=0.0, ao=ao)

    # Pencil: hexagonal pencil lying along X
    k = Kit(pal)
    R = 0.3
    k.cyl((-2.0, 0.0, R), R, R, 3.6, 'tyellow', seg=6, rot=(0, 90, 0), bevel=False)
    k.cyl((1.6, 0.0, R), R, 0.09, 0.65, 'birch', seg=6, rot=(0, 90, 0), bevel=False)
    k.cyl((2.25, 0.0, R), 0.09, 0.0, 0.22, 'gunmetal', seg=6, rot=(0, 90, 0), bevel=False)
    k.cyl((-2.28, 0.0, R), R + 0.015, R + 0.015, 0.3, 'metal', seg=6, rot=(0, 90, 0), bevel=False)
    k.cyl((-2.5, 0.0, R), R - 0.01, R - 0.01, 0.22, 'tpink', seg=6, rot=(0, 90, 0), bevel=False)
    k.col(-2.5, 2.45, -0.32, 0.32, 0.0, 0.6)
    k.build('Pencil', bw=0.0, ao=ao)

    # BrickTower: interlocking building bricks (no brand), studs on the top layer
    k = Kit(pal)
    cols = ['red', 'tblue', 'tyellow', 'tgreen', 'red', 'tyellow', 'tblue']
    BH = 0.6
    for L in range(6):
        for b in range(2):
            c = cols[(L * 2 + b) % len(cols)]
            if L % 2 == 0:
                x0, x1, y0, y1 = -0.94, 0.94, (-0.94 if b == 0 else 0.01), (-0.01 if b == 0 else 0.94)
            else:
                x0, x1, y0, y1 = (-0.94 if b == 0 else 0.01), (-0.01 if b == 0 else 0.94), -0.94, 0.94
            k.obox(x0, x1, y0, y1, L * BH, (L + 1) * BH, c, faces=('+z', '-y', '+y', '-x', '+x'))
    for i in range(2):
        for j in range(4):
            x = -0.47 + i * 0.94
            y = -0.705 + j * 0.47
            k.cyl((x, y, 6 * BH), 0.15, 0.15, 0.12, cols[(10 + i) % len(cols)], seg=8, bevel=False)
    k.col(-0.95, 0.95, -0.95, 0.95, 0.0, 6 * BH + 0.12)
    k.build('BrickTower', bw=0.0, ao=ao)

    # ToyCastle: wooden castle on a solid base, four towers, two cone roofs with flags
    k = Kit(pal)
    k.bx(-2.6, 2.6, -2.6, 2.6, 0.0, 2.1, 'birch')
    for (x, y) in ((-1.1, -2.62), (1.1, -2.62), (-1.1, 2.62), (1.1, 2.62), (-2.62, -1.1), (-2.62, 1.1), (2.62, -1.1), (2.62, 1.1), (0.0, -2.62), (0.0, 2.62), (-2.62, 0.0), (2.62, 0.0)):
        k.obox(x - 0.3, x + 0.3, y - 0.18, y + 0.18, 2.1, 2.6, 'birch', faces=('+z', '-y', '+y', '-x', '+x'))
    k.obox(-0.75, 0.75, -2.63, -2.6, 0.0, 1.5, 'wood3', faces=('-y',))
    k.prism(arc_pts(0.75, 0, 0, 0, 180, 6), 0.0, 0.03, 'wood3', mat=wall_mat(0.0, 1.5, -2.63, 0.03), bottom=False)
    for i, (x, y) in enumerate(((-2.55, -2.55), (2.55, -2.55), (-2.55, 2.55), (2.55, 2.55))):
        top = 4.2 if i < 2 else 3.6
        k.cyl((x, y, 0.0), 0.95, 0.95, top, 'tsky' if i % 2 == 0 else 'pink', seg=10, bevel=False)
        for a in range(5):
            ang = a / 5 * 2 * math.pi + 0.3
            k.obox(x + math.cos(ang) * 0.8 - 0.17, x + math.cos(ang) * 0.8 + 0.17, y + math.sin(ang) * 0.8 - 0.17, y + math.sin(ang) * 0.8 + 0.17,
                   top, top + 0.4, 'tsky' if i % 2 == 0 else 'pink', faces=('+z', '-y', '+y', '-x', '+x'))
        if i >= 2:
            continue
        k.cyl((x, y, top + 0.4), 1.1, 0.0, 1.9, 'red' if i == 0 else 'tblue', seg=10, bevel=False)
        k.cyl((x, y, top + 2.2), 0.04, 0.04, 1.0, 'ink', seg=4, bevel=False)
        k.prism([(0.0, 0.0), (0.7, 0.22), (0.0, 0.45)], -0.02, 0.02, 'tyellow', mat=T(x, y, top + 2.75) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
        k.obox(x - 0.25, x + 0.25, y - 0.96, y - 0.94, top - 1.7, top - 1.0, 'ink', faces=('-y',))
    k.col(-2.6, 2.6, -2.6, 2.6, 0.0, 2.6)
    for (x, y) in ((-2.55, -2.55), (2.55, -2.55), (-2.55, 2.55), (2.55, 2.55)):
        k.col(x - 0.95, x + 0.95, y - 0.95, y + 0.95, 0.0, 4.2)
    k.build('ToyCastle', bw=0.04, ao=ao)


def build_floor(pal, ao):
    """Floor patches (no collision): tops at least 3 cm above the painted floor and its board lines."""
    k = Kit(pal)
    rings = [(6.2, 'rugpink'), (5.0, 'cream'), (3.8, 'rugblue'), (2.6, 'rugyellow'), (1.4, 'white')]
    for i, (r, c) in enumerate(rings):
        k.disc(0.0, 0.0, 0.0, 0.03 + 0.006 * i, r, c, seg=28 if i < 2 else 20)
    k.build('Rug_Round', bw=0.0, ao=False)

    k = Kit(pal)
    stripes = ['rugmint', 'cream', 'rugpink', 'rugyellow', 'rugblue', 'cream', 'rugmint', 'rugpink']
    for i, c in enumerate(stripes):
        x0 = -8.0 + i * 2.0
        k.obox(x0, x0 + 2.0, -5.0, 5.0, 0.0, 0.035, c, faces=('+z', '-y', '+y') + (('-x',) if i == 0 else ()) + (('+x',) if i == 7 else ()))
    for sx in (-1, 1):
        for j in range(9):
            y = -4.4 + j * 1.1
            k.obox(sx * 8.0, sx * 8.45, y - 0.08, y + 0.08, 0.0, 0.022, 'cream', faces=('+z', '-y', '+y', '+x' if sx > 0 else '-x'))
    k.build('Rug_Stripe', bw=0.0, ao=False)

    # TrackLoop: wooden train track oval (straights along X, curves at the ends); grooves 8 mm proud of the board
    k = Kit(pal)
    RC, HW, SX = 5.0, 0.66, 5.5
    for sy in (-1, 1):
        y = sy * RC
        k.obox(-SX, SX, y - HW, y + HW, 0.0, 0.05, 'birch', faces=('+z', '-y', '+y'))
        for g in (-0.3, 0.3):
            k.obox(-SX, SX, y + g - 0.07, y + g + 0.07, 0.05, 0.058, 'wood2', faces=('+z',))
    for sx in (-1, 1):
        a0, a1 = (-90, 90) if sx > 0 else (90, 270)
        k.strip(arc_pts(RC + HW, sx * SX, 0, a0, a1, 12), arc_pts(RC - HW, sx * SX, 0, a0, a1, 12), 0.0, 0.05, 'birch')
        for g in (-0.3, 0.3):
            k.strip(arc_pts(RC + g + 0.07, sx * SX, 0, a0, a1, 12), arc_pts(RC + g - 0.07, sx * SX, 0, a0, a1, 12), 0.05, 0.058, 'wood2')
    k.build('TrackLoop', bw=0.0, ao=False)


def build_overlays(pal, ao):
    """Wall overlays: footprint is the floor row in front of a wall; the wall face is the plane y = +0.5."""
    WF = 0.5
    # Window: white frame, daylight panes with glints and cloud stickers, sill, pink pelmet, striped floor-length curtains
    k = Kit(pal)
    yf = WF - 0.25
    k.obox(-3.0, 3.0, WF - 0.13, WF - 0.03, 3.95, 12.65, 'glass', faces=('-y',))
    for (x0, x1, z0, z1) in ((-3.35, -3.0, 3.6, 13.0), (3.0, 3.35, 3.6, 13.0), (-3.0, 3.0, 3.6, 3.95), (-3.0, 3.0, 12.65, 13.0),
                             (-0.15, 0.15, 3.95, 9.85), (-0.15, 0.15, 10.15, 12.65), (-3.0, -0.15, 9.85, 10.15), (0.15, 3.0, 9.85, 10.15)):
        k.obox(x0, x1, yf, WF - 0.03, z0, z1, 'trim', faces=('-y', '-x', '+x', '+z', '-z'))
    for (x, z) in ((-1.6, 5.5), (1.4, 6.6), (-1.5, 11.0), (1.6, 11.3)):
        k.prism([(-0.55, -0.7), (-0.25, -0.7), (0.55, 0.7), (0.25, 0.7)], 0.0, 0.012, 'glint', mat=wall_mat(x, z, WF - 0.138, 0.012), bottom=False)
    for (x, z, sz) in ((-2.1, 7.6, 0.9), (2.0, 8.6, 0.75)):
        for i, (px, pz, r) in enumerate([(-0.38, -0.05, 0.36), (0.36, -0.08, 0.32), (0.0, 0.12, 0.44)]):
            dd = 0.01 + 0.006 * i
            k.prism(circle_pts(r * sz, seg=10), 0.0, dd, 'white', mat=wall_mat(x + px * sz, z + pz * sz, WF - 0.13 - dd + 0.004, dd), bottom=False)
    k.obox(-3.7, 3.7, -0.25, WF - 0.02, 3.28, 3.6, 'trim', faces=('-y', '+z', '-z', '-x', '+x'))
    scal = [(4.5, 0.0), (4.5, 1.2), (-4.5, 1.2), (-4.5, 0.0)]
    pts = [(-4.5, 1.2), (-4.5, 0.0)]
    for i in range(6):
        xa = -4.5 + i * 1.5
        pts += [(xa + 0.75, -0.35), (xa + 1.5, 0.0)]
    k.prism(pts + [(4.5, 1.2)], 0.0, 0.85, 'pink', mat=wall_mat(0.0, 13.55, WF - 0.87, 0.85), fan=True, bottom=False)
    k.cyl((-4.3, WF - 0.55, 13.4), 0.1, 0.1, 8.6, 'wood', seg=8, rot=(0, 90, 0), bevel=False)
    for sx in (-1, 1):
        x0 = sx * 2.62
        for i in range(4):
            x = x0 + sx * (0.22 + i * 0.46)
            k.cyl((x, 0.08, 0.3 + 0.03 * (i % 2)), 0.226, 0.226, 13.1, 'butter' if i % 2 == 0 else 'white', seg=8, bevel=False)
        lo, hi = sorted((x0, x0 + sx * 1.86))
        k.quad((lo, 0.27, 0.3) if sx < 0 else (hi, 0.27, 0.3), (hi, 0.27, 0.3) if sx < 0 else (lo, 0.27, 0.3),
               (hi, 0.27, 13.4) if sx < 0 else (lo, 0.27, 13.4), (lo, 0.27, 13.4) if sx < 0 else (hi, 0.27, 13.4), 'butter')
        k.obox(lo - 0.03, hi + 0.03, -0.22, 0.33, 4.6, 5.0, 'tpink', faces=('-y', '+z', '-z', '-x', '+x'))
        k.col(lo, hi, -0.2, 0.34, 0.0, 13.4)
    k.build('Window', bw=0.02, ao=ao)

    # Posters (no faces: rocket, rainbow, shapes chart, planets); _R variants for the south and east walls
    def poster(name, bg, draw, rot):
        k = Kit(pal)
        k.m.parent = rz(rot)
        z0, z1 = 10.3, 14.9
        yfp = WF - 0.035
        k.obox(-1.7, 1.7, yfp, WF - 0.005, z0, z1, 'white', faces=('-y', '+z', '-z', '-x', '+x'))
        k.obox(-1.5, 1.5, yfp - 0.006, WF - 0.02, z0 + 0.2, z1 - 0.2, bg, faces=('-y',))
        draw(k, yfp - 0.006, (z0 + z1) / 2)
        for sx in (-1, 1):
            k.prism([(-0.35, -0.12), (0.35, -0.12), (0.35, 0.12), (-0.35, 0.12)], 0.0, 0.012, 'cream',
                    mat=wall_mat(sx * 1.55, z1 - 0.1, yfp - 0.012, 0.012) @ Matrix.Rotation(math.radians(-35 * sx), 4, 'Z'), bottom=False)
        k.m.parent = Matrix.Identity(4)
        k.build(name, bw=0.0, ao=False)

    def flat(k, pts, x, z, yb, c, i=0, fan=False):
        d = 0.012 + 0.004 * i
        k.prism(pts, 0.0, d, c, mat=wall_mat(x, z, yb - d, d), fan=fan, bottom=False)

    def rocket(k, yb, zc):
        flat(k, [(-0.42, -1.1), (0.42, -1.1), (0.42, 0.7), (-0.42, 0.7)], 0.0, zc, yb, 'white', 0)
        flat(k, [(-0.42, 0.0), (0.42, 0.0), (0.0, 0.85)], 0.0, zc + 0.7, yb, 'red', 1)
        flat(k, [(-0.42, 0.0), (-0.95, -0.6), (-0.42, 0.5)], 0.0, zc - 1.0, yb, 'red', 1)
        flat(k, [(0.42, 0.0), (0.42, 0.5), (0.95, -0.6)], 0.0, zc - 1.0, yb, 'red', 1)
        flat(k, [(-0.36, -0.05), (0.36, -0.05), (0.36, 0.18), (-0.36, 0.18)], 0.0, zc - 0.1, yb, 'tsky', 1)
        flat(k, [(-0.3, 0.0), (0.3, 0.0), (0.0, -0.75)], 0.0, zc - 1.1, yb, 'torange', 1)
        flat(k, [(-0.15, -0.03), (0.15, -0.03), (0.0, -0.4)], 0.0, zc - 1.1, yb, 'tyellow', 2)
        for (x, z, r) in ((-1.05, 1.4, 0.2), (1.0, 0.9, 0.16), (-0.95, -0.4, 0.13), (1.1, -1.5, 0.2)):
            flat(k, star_pts(r), x, zc + z, yb, 'butter', 0, fan=True)

    def rainbow(k, yb, zc):
        for ri, (c, r0, r1) in enumerate((('red', 1.05, 1.3), ('torange', 0.8, 1.05), ('tyellow', 0.55, 0.8), ('tblue', 0.3, 0.55))):
            d = 0.012 + 0.004 * ri
            k.strip(arc_pts(r1, 0, 0, 0, 180, 10), arc_pts(r0, 0, 0, 0, 180, 10), 0.0, d, c, mat=wall_mat(0.0, zc - 0.6, yb - d, d))
        for sx in (-1, 1):
            for i, (px, pz, r) in enumerate([(-0.3, -0.05, 0.28), (0.28, -0.07, 0.25), (0.0, 0.1, 0.34)]):
                flat(k, circle_pts(r, seg=10), sx * 1.0 + px, zc - 0.7 + pz, yb, 'white', 5 + i)

    def shapes(k, yb, zc):
        flat(k, circle_pts(0.55, seg=14), -0.75, zc + 0.85, yb, 'red')
        flat(k, [(-0.6, -0.5), (0.6, -0.5), (0.0, 0.55)], 0.75, zc + 0.8, yb, 'tblue')
        flat(k, [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)], -0.75, zc - 0.55, yb, 'tyellow')
        flat(k, star_pts(0.6), 0.75, zc - 0.5, yb, 'tgreen', fan=True)
        for i in range(5):
            flat(k, circle_pts(0.12, seg=8), -1.0 + i * 0.5, zc - 1.65, yb, ('red', 'torange', 'tyellow', 'tgreen', 'tblue')[i])

    def planets(k, yb, zc):
        flat(k, circle_pts(0.62, seg=16), -0.3, zc + 0.4, yb, 'torange', 1)
        k.strip([(x * 1.0, y * 0.32) for x, y in arc_pts(1.15, 0, 0, 0, 180, 10)], [(x * 1.0, y * 0.22) for x, y in arc_pts(0.95, 0, 0, 0, 180, 10)],
                0.0, 0.024, 'butter', mat=wall_mat(-0.3, zc + 0.4, yb - 0.024, 0.024) @ Matrix.Rotation(math.radians(180 + 12), 4, 'Z'))
        flat(k, circle_pts(0.3, seg=12), 0.85, zc - 0.85, yb, 'tpink')
        flat(k, circle_pts(0.2, seg=10), -0.95, zc - 1.25, yb, 'tmint')
        for (x, z, r) in ((0.9, 1.5, 0.16), (-1.1, 1.6, 0.12), (1.15, 0.3, 0.12), (0.1, -1.5, 0.14)):
            flat(k, star_pts(r), x, zc + z, yb, 'white', 0, fan=True)

    for nm, bg, fn in (('Poster_A', 'navy', rocket), ('Poster_B', 'cream', rainbow), ('Poster_C', 'white', shapes), ('Poster_D', 'navy', planets)):
        poster(nm, bg, fn, 0)
        poster(nm + '_R', bg, fn, 180)

    # WallShelf: floating shelf with brackets, books held by a block, a toy sailboat and a ball
    for name, rot in (('WallShelf', 0), ('WallShelf_R', 180)):
        k = Kit(pal)
        R = rz(rot)
        k.m.parent = R
        k.obox(-2.3, 2.3, -0.42, WF - 0.004, 10.6, 10.84, 'trim', faces=('-y', '+z', '-z', '-x', '+x'))
        for x in (-1.6, 1.6):
            k.prism([(0.0, 0.0), (-0.6, 0.0), (0.0, -0.8)], -0.06, 0.06, 'trim2', mat=T(x, WF - 0.004, 10.6) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
        books_row(k, -2.1, -0.6, 10.84, -0.36, 0.7, 777 + rot, 1.6)
        k.obox(-0.55, 0.15, -0.3, 0.4, 10.84, 11.54, 'tblue', faces=('+z', '-y', '+y', '-x', '+x'))
        k.obox(0.5, 1.5, -0.25, 0.25, 10.84, 11.14, 'red', faces=('+z', '-y', '+y', '-x', '+x'))
        k.cyl((1.0, 0.0, 11.14), 0.03, 0.03, 1.1, 'wood3', seg=4, bevel=False)
        k.prism([(0.0, 0.0), (0.0, 0.95), (0.5, 0.0)], -0.015, 0.015, 'white', mat=T(1.05, 0.0, 11.2) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
        k.sphere((1.85, 0.05, 11.24), 0.4, 'tyellow', seg=(10, 6))
        k.m.parent = Matrix.Identity(4)
        k.build(name, bw=0.02, ao=False)

    # Door: a kid's room door (closed) with panels, a knob and a cloud door hanger
    k = Kit(pal)
    k.obox(-2.45, 2.45, WF - 0.2, WF - 0.004, 0.0, 12.4, 'cream', faces=('-y', '-x', '+x', '+z'))
    for (x0, x1, z0, z1) in ((-2.95, -2.45, 0.0, 12.9), (2.45, 2.95, 0.0, 12.9), (-2.45, 2.45, 12.4, 12.9)):
        k.obox(x0, x1, WF - 0.26, WF - 0.004, z0, z1, 'trim', faces=('-y', '-x', '+x', '+z', '-z'))
    for (x, z0, z1) in ((-1.15, 1.0, 5.4), (1.15, 1.0, 5.4), (-1.15, 6.6, 11.4), (1.15, 6.6, 11.4)):
        k.obox(x - 0.9, x + 0.9, WF - 0.235, WF - 0.19, z0, z1, 'lilac', faces=('-y', '-x', '+x', '+z', '-z'))
    k.sphere((1.85, WF - 0.42, 6.0), 0.24, 'tyellow', seg=(10, 6))
    k.cyl((1.85, WF - 0.2, 6.0), 0.16, 0.16, 0.2, 'tyellow', seg=8, rot=(90, 0, 0), bevel=False)
    k.beam((1.85, WF - 0.44, 6.1), (1.6, WF - 0.44, 7.1), 0.03, 'ink')
    k.beam((1.85, WF - 0.448, 6.1), (2.1, WF - 0.448, 7.1), 0.026, 'ink')
    for i, (px, pz, r) in enumerate([(-0.38, -0.05, 0.36), (0.36, -0.08, 0.32), (0.0, 0.12, 0.44)]):
        dd = 0.04 + 0.008 * i
        k.prism(circle_pts(r, seg=10), 0.0, dd, 'tsky', mat=wall_mat(1.85 + px, 6.75 + pz, WF - 0.48 - dd + 0.005 * i, dd), bottom=True)
    k.col(-2.95, 2.95, WF - 0.26, WF, 0.0, 12.9)
    k.build('Door', bw=0.02, ao=ao)


def normals_up(obj, only_down=True):
    """Shade downward faces as if they faced up (custom normals): the toon light has no ambient term, so a ceiling
    would otherwise always fall in the darkest band. Outline-shell faces keep their normals."""
    me = obj.data
    hull = me.attributes.get('_HULL')
    corner = [tuple(n.vector) for n in me.corner_normals]
    out = []
    for poly in me.polygons:
        shell = hull is not None and any(Vector(hull.data[v].vector).length > 0 for v in poly.vertices)
        lift = not shell and (not only_down or poly.normal.z < -0.5)
        for li in poly.loop_indices:
            out.append((0.0, 0.0, 1.0) if lift else corner[li])
    me.normals_split_custom_set(out)
    return obj


def build_ceiling(pal, ao):
    """Hung from the ceiling: these pieces are placed at y = CEIL (18 m); everything stays >= 4 cm below it except the
    ceiling tiles, which sit 6-10 mm under the engine's ceiling plane and hide it."""
    # CeilingTile: 1 m grid (theme env.ceiling.light, every = 1), 1.02 m tiles so neighbours overlap by 2 cm everywhere
    # (zones, trails, the hatch). A slight tilt (3 mm / 7 mm per metre) puts every tile on its own plane: overlapping
    # neighbours are >= 3 mm apart and the cross-piece z-check stays linear.
    k = Kit(pal)
    corners = [(-0.51, -0.51), (0.51, -0.51), (0.51, 0.51), (-0.51, 0.51)]
    pts = [(x, y, -0.006 - 0.003 * (x + 0.51) - 0.007 * (y + 0.51)) for x, y in corners]
    k.quad(pts[3], pts[2], pts[1], pts[0], 'ceil')
    normals_up(k.build('CeilingTile', bw=0.0, hull=False))

    # CeilingLamp: flying-saucer pendant
    k = Kit(pal)
    k.cyl((0.0, 0.0, -0.24), 0.7, 0.55, 0.2, 'trim', seg=10, bevel=False)
    k.cyl((0.0, 0.0, -1.7), 0.06, 0.06, 1.52, 'ink', seg=6, bevel=False)
    k.cyl((0.0, 0.0, -3.1), 2.3, 0.85, 1.4, 'white', seg=16, bevel=False)
    k.cyl((0.0, 0.0, -3.0), 2.31, 2.2, 0.32, 'tyellow', seg=16, bevel=False, caps=False)
    k.disc(0.0, 0.0, -3.13, -3.1, 2.05, 'lampshade', seg=16, bottom=True)
    normals_up(k.build('CeilingLamp', bw=0.03, ao=False))

    # CeilingStars_A/B: glow-in-the-dark star stickers with a moon (only their undersides are seen)
    for name, stars in (('CeilingStars_A', [(-2.4, 1.6, 1.15), (1.3, 2.6, 0.75), (2.6, -0.9, 1.35), (-0.7, -2.6, 0.85), (-2.9, -1.5, 0.55)]),
                        ('CeilingStars_B', [(2.3, 2.0, 1.0), (-1.5, 2.6, 0.7), (-2.5, -0.6, 1.3), (1.5, -2.5, 0.9), (2.9, 0.3, 0.55)])):
        k = Kit(pal)
        for i, (x, y, r) in enumerate(stars):
            k.prism(star_pts(r, x, y, rot=90 + i * 23), -0.1 - 0.004 * i, -0.045, 'butter', fan=True, top=False, bottom=True)
        o, i_ = crescent_pts(1.25, seg=8)
        mx, my = (0.3, 0.2) if name.endswith('A') else (-0.2, -0.1)
        k.strip([(x + mx, y + my) for x, y in o], [(x + mx, y + my) for x, y in i_], -0.13, -0.045, 'butter', bottom=True)
        normals_up(k.build(name, bw=0.0, ao=False), only_down=False)

    # Mobile: planets, a star, a moon and a cloud on a wooden cross
    k = Kit(pal)
    k.disc(0.0, 0.0, -0.14, -0.045, 0.35, 'trim', seg=10, bottom=True)
    k.beam((0.0, 0.0, -0.12), (0.0, 0.0, -3.5), 0.05, 'ink')
    k.beam((-3.2, 0.0, -3.5), (3.2, 0.0, -3.5), 0.12, 'wood', bevel=False)
    k.beam((0.0, -3.2, -3.62), (0.0, 3.2, -3.62), 0.12, 'wood', bevel=False)
    hangs = [((-3.0, 0.0), 2.6), ((3.0, 0.0), 3.4), ((0.0, -3.0), 2.2), ((0.0, 3.0), 3.0)]
    for (x, y), L in hangs:
        z0 = -3.5 if y == 0 else -3.62
        k.beam((x, y, z0), (x, y, z0 - L), 0.035, 'ink')
    (x, y), L = hangs[0]
    k.sphere((x, y, -3.5 - L - 0.6), 0.6, 'torange', seg=(10, 6))
    k.strip(circle_pts(1.05, x, y, seg=16) + [circle_pts(1.05, x, y, seg=16)[0]], circle_pts(0.8, x, y, seg=16) + [circle_pts(0.8, x, y, seg=16)[0]],
            -3.5 - L - 0.63, -3.5 - L - 0.57, 'butter', mat=None, bottom=True)
    (x, y), L = hangs[1]
    k.prism(star_pts(0.75), -0.06, 0.06, 'tyellow', fan=True, mat=T(x, y, -3.5 - L - 0.75) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    (x, y), L = hangs[2]
    o, i_ = crescent_pts(0.7, seg=8)
    k.strip(o, i_, -0.06, 0.06, 'butter', mat=T(x, y, -3.62 - L - 0.7) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))), bottom=True)
    (x, y), L = hangs[3]
    k.sphere((x, y, -3.62 - L - 0.45), 0.45, 'tpink', seg=(10, 6))
    k.sphere((x + 0.0, y, -3.62 - L - 1.2), 0.3, 'tmint', seg=(8, 5))
    k.beam((x, y, -3.62 - L - 0.9), (x, y, -3.62 - L - 0.95), 0.03, 'ink')
    k.build('Mobile', bw=0.0, ao=False)


def build_kit_bedroom(ao):
    pal = Palette(FAM)
    build_walls(pal, ao)
    build_gate(pal, ao)
    build_bed(pal, ao)
    build_toychest(pal, ao)
    build_blocks(pal, ao)
    build_bookstacks(pal, ao)
    build_desk(pal, ao)
    build_chair(pal, ao)
    build_bookcase(pal, ao)
    build_storage(pal, ao)
    build_toys(pal, ao)
    build_floor(pal, ao)
    build_overlays(pal, ao)
    build_ceiling(pal, ao)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_bedroom
