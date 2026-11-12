"""INKBOLT kit-observatory ("Vesper Peak Observatory", the last campaign map: a mountaintop observatory at late dusk):
palette, modelling helpers and conventions shared by ob_struct.py (wall faces and wall art, doorways, the gate, trail,
hatch, weapon stand, parapets, fences, rails, stairs, deck posts, ceilings, floor finishes), ob_summit.py (zone 1, the
summit compound: the funicular station and dome annex fronts' signs, the 12 m dish antennas, the VSAT dishes, the
radio mast array, equipment shelters, the ground station building with its roof deck, the 1931 Halden Dome, the
snowcat, fuel tanks, the generator house, weather mast, all-sky camera, lamps, rocks, benches, cable bridges) and
ob_dome.py (zone 2, inside the Great Dome: the dome shell with its slit open, the Vesper 12 m telescope on its mount,
the catwalk ring, the laboratories, the control room, the lobby, the glass viewing rooms and the service hall).
The family module is fam_kit_observatory.py.

Look: a well-kept high-altitude observatory -- white and silver insulated panels with a deep observatory blue band,
safety yellow steel, timber and stone at the funicular station, snow on every ledge; inside the dome deep blue-grey
steel under the white ribbed dome, white labs, a warm timber lobby, charcoal viewing rooms with full-height glass.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +X = game +X.
  * Wall faces are flat painted quads on a cell's front face (y = -0.5, facing -Y), WALL_H (10 m) tall; the theme's
    chooser turns one face piece onto each open side of a wall cell and stacks an art overlay (6 mm proud) on it.
  * Run pieces placed with rotate 'run' (parapets, cable bridges) are modelled along Blender X; link pieces (fences,
    rails) along Blender Y (the half module runs from the origin toward -Y); [n, 1] prefabs along Blender X.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: walkable (stair treads, roof decks, the catwalk ring).
  * Stairs rise at most 0.16 m per 0.25 m tread: at most 0.32 m between neighbouring 0.5 m nav cells (robots: 0.4 m).
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text  # noqa: F401
from ac_base import AKit

FAM = 'kit-observatory'
PFX = 'KIT_OBSERVATORY_'
ib_lib.GLB[FAM] = 'fps-kit-observatory.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    # snow, rock (8 - 14)
    ('snow', '#EEF1F7'), ('snowS', '#C9CFDD'), ('ice', '#B9D3E6'), ('rock', '#7D7884'), ('rockD', '#5C5866'),
    ('rockL', '#A29DA8'), ('gravel', '#77737C'),
    # concrete, stone (15 - 20)
    ('conc', '#B9B5AE'), ('concD', '#8E8A85'), ('concL', '#D6D2CB'), ('stone', '#B8A88E'), ('stoneD', '#8E7F68'),
    ('stoneL', '#D3C6AE'),
    # domes (21 - 26)
    ('copper', '#5FA08C'), ('copperD', '#3F7566'), ('domeW', '#E4E7EC'), ('domeS', '#B9BEC8'), ('domeIn', '#3E4766'),
    ('domeInD', '#2B3250'),
    # metals (27 - 31)
    ('steel', '#9AA3AD'), ('steelD', '#5B6470'), ('chrome', '#D7DDE3'), ('black', '#25262C'), ('graph', '#3A3D46'),
    # livery (32 - 36)
    ('yellow', '#F2C230'), ('orange', '#E8742A'), ('blueS', '#2F5EA8'), ('blueD', '#1F3F75'), ('navy', '#1B2440'),
    # timber (37 - 39)
    ('wood', '#B9874F'), ('woodD', '#7A5233'), ('woodL', '#D8B37E'),
    # glass, screens, light (40 - 47)
    ('glass', '#7FA9C9'), ('glassD', '#3F5F7F'), ('glassL', '#C6E2F0'), ('screen', '#152238'), ('scrB', '#46A6EE'),
    ('scrG', '#3FD18A'), ('lightW', '#FFF4D2'), ('redL', '#FF4A3D'),
    # interiors (48 - 55)
    ('panelW', '#EDEFF0'), ('panelG', '#C9CED3'), ('hallP', '#4A5270'), ('fabric', '#5D6FA8'), ('fabricD', '#3F4E80'),
    ('leaf', '#4E9A45'), ('pot', '#C46A3F'), ('chart', '#121C3C'),
    # optics, misc (56 - 61)
    ('starW', '#F6F3DE'), ('mirror', '#C9D6E8'), ('mirrorD', '#8FA3BF'), ('rubber', '#3B3D44'), ('brass', '#C9A24E'),
    ('amberL', '#FFB43A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]

WALL_H = 10.0     # walls (the dome springs from the hall walls' top)
DOOR_H = 3.0      # doorway head (wall.passage is solid above)
RISE_MAX = 0.16
Y0 = -0.5         # a front face
YA = Y0 - 0.006   # art overlay plane (6 mm proud of the wall face)
TERR = 3.0        # zone 1: the east terrace, the gantry, the ground station roof
PAD = 1.5         # zone 1: the mast pad
DECK = 4.8        # zone 2: the catwalk ring, the gallery, the star deck


def cell(name):
    return NAMES.index(name)


class OKit(AKit):
    """AKit (culled boxes, painted quads, text, chairs) plus observatory shapes."""

    def plate(self, x0, x1, z0, z1, c, y=Y0, d=0.03, rim=None):
        """a flat sign plate on the front face (d thick), optionally with a rim colour round its top and bottom"""
        self.bx(x0, x1, y - d, y, z0, z1, c, cull='k')
        if rim:
            self.fq(x0 + 0.02, x1 - 0.02, y - d - 0.003, z0 + 0.02, z0 + 0.05, rim)
            self.fq(x0 + 0.02, x1 - 0.02, y - d - 0.003, z1 - 0.05, z1 - 0.02, rim)

    def pole(self, x, y, z0, z1, r, c, seg=6, ink=True):
        self.cyl(x, y, z0, r, r, z1 - z0, c, seg=seg, ink=ink, caps=False)

    def snowcap(self, x0, x1, y0, y1, z, t=0.06, c='snow'):
        """a snow layer lying on a ledge (slightly rounded look from a chamfered upper box)"""
        self.bx(x0, x1, y0, y1, z, z + t, c, cull='b')

    def arc_pts(self, cx, cy, r, a0, a1, n):
        return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]

    def ring_wall(self, cx, cy, r0, r1, z0, z1, c, seg=24, a0=0.0, a1=2 * math.pi, ink=True, top=None, inner=None):
        """a thick cylindrical wall (r0 inner, r1 outer) between angles a0..a1: outer face, top, inner face (inner
        colour optional) as one outlined shape per segment run"""
        pts = self.arc_pts(cx, cy, 1.0, a0, a1, seg)
        m = self.m
        P = m.parent
        vs = []
        for (ux, uy) in pts:
            dx, dy = ux - cx, uy - cy
            vs.append([P @ Vector((cx + dx * r1, cy + dy * r1, z0)), P @ Vector((cx + dx * r1, cy + dy * r1, z1)),
                       P @ Vector((cx + dx * r0, cy + dy * r0, z1)), P @ Vector((cx + dx * r0, cy + dy * r0, z0))])
        bv = [[m.bm.verts.new(v) for v in row] for row in vs]
        fs = []
        for a, b in zip(bv, bv[1:]):
            fs.append(m.bm.faces.new((a[0], b[0], b[1], a[1])))   # outer
            fs.append(m.bm.faces.new((a[1], b[1], b[2], a[2])))   # top
            fs.append(m.bm.faces.new((a[2], b[2], b[3], a[3])))   # inner
        if abs((a1 - a0) - 2 * math.pi) > 1e-6:   # end caps
            fs.append(m.bm.faces.new((bv[0][0], bv[0][1], bv[0][2], bv[0][3])))
            fs.append(m.bm.faces.new((bv[-1][3], bv[-1][2], bv[-1][1], bv[-1][0])))
        bmesh.ops.recalc_face_normals(m.bm, faces=fs)
        cols = {}

        def colour(f):
            n = f.normal
            if n.z > 0.7:
                return top or c
            if inner:
                cen = f.calc_center_median()
                lc = P.inverted() @ cen
                rr = math.hypot(lc.x - cx, lc.y - cy)
                if rr < (r0 + r1) / 2:
                    return inner
            return c
        self._tag(fs, colour)
        self._mark(ink)
        return fs


    def mesh(self, verts, faces, color, ink=True, recalc=False):
        """raw vertices (piece frame) and faces (index tuples, counter-clockwise seen from outside) as one shape;
        color: a palette name or fn(face) -> name"""
        m = self.m
        P = m.parent
        vs = [m.bm.verts.new(P @ Vector(p)) for p in verts]
        fs = []
        for f in faces:
            try:
                fs.append(m.bm.faces.new([vs[i] for i in f]))
            except ValueError:
                pass
        for f in fs:
            f.normal_update()
        if recalc:
            bmesh.ops.recalc_face_normals(m.bm, faces=fs)
        self._tag(fs, color)
        self._mark(ink)
        return fs

    def sweep(self, rings, color, ink=True, closed=True, cap0=False, cap1=False, recalc=False):
        """a surface through rings of points (each ring the same count, closed loops when `closed`): quads between
        consecutive rings; caps fan-close the first / last ring"""
        verts, faces = [], []
        n = len(rings[0])
        for R in rings:
            verts.extend(R)
        for j in range(len(rings) - 1):
            for i in range(n if closed else n - 1):
                i2 = (i + 1) % n
                a, b, c, d = j * n + i, j * n + i2, (j + 1) * n + i2, (j + 1) * n + i
                faces.append((a, b, c, d))
        if cap0:
            faces.append(tuple(reversed(range(n))))
        if cap1:
            faces.append(tuple((len(rings) - 1) * n + i for i in range(n)))
        return self.mesh(verts, faces, color, ink, recalc)


# ---------------------------------------------------------------- collision helpers for round shapes
def disc_cols(k, cx, cy, r, z0, z1, step=0.4, inset=0.04, walk=False):
    """axis-aligned boxes filling a disc of radius r (inscribed: never past the drawn rim), one per strip of `step`
    along Blender X, solid from z0 to z1"""
    n = max(1, int(math.ceil(2 * r / step)))
    w = 2 * r / n
    for i in range(n):
        x0, x1 = cx - r + i * w, cx - r + (i + 1) * w
        xo = max(abs(x0 - cx), abs(x1 - cx))
        if xo >= r - 1e-6:
            xo = r - 1e-3
        h = math.sqrt(max(0.0, (r - inset) ** 2 - xo ** 2))
        if h < 0.05:
            continue
        (k.wcol if walk else k.col)(x0, x1, cy - h, cy + h, z0, z1)


def band_cols(k, cx, cy, r0, r1, z0, z1, step=0.3, walk=False, skip=None):
    """boxes covering the annulus r0..r1 (a rail band, a ring deck), cut in strips of `step` along Blender Y: in each
    strip the x-intervals where the annulus crosses it. skip(angle) -> True leaves that part open (a stair landing)."""
    n = int(math.ceil(2 * r1 / step))
    for i in range(n):
        y0 = cy - r1 + i * step
        y1 = min(cy + r1, y0 + step)
        ylo = min(abs(y0 - cy), abs(y1 - cy)) if (y0 - cy) * (y1 - cy) > 0 else 0.0
        yhi = max(abs(y0 - cy), abs(y1 - cy))
        if ylo >= r1:
            continue
        xo = math.sqrt(max(0.0, r1 * r1 - ylo * ylo))          # outer reach in this strip
        xi = math.sqrt(r0 * r0 - yhi * yhi) if yhi < r0 else 0.0  # inner hole in this strip
        for s in (-1, 1):
            a, b = sorted((cx + s * xi, cx + s * xo))
            if b - a < 0.02:
                continue
            if xi == 0.0 and s > 0:
                break   # one interval across the whole strip (counted once below)
            if xi == 0.0:
                a, b = cx - xo, cx + xo
            ym = (y0 + y1) / 2
            ang = math.atan2(ym - cy, ((a + b) / 2) - cx)
            if skip and skip(ang, a, b, y0, y1):
                # cut the interval round the open part: keep the pieces whose ends are not open
                pieces = []
                m = 12
                seg = [(a + (b - a) * j / m, a + (b - a) * (j + 1) / m) for j in range(m)]
                cur = None
                for (p, q) in seg:
                    angp = math.atan2(ym - cy, (p + q) / 2 - cx)
                    if skip(angp, p, q, y0, y1):
                        if cur:
                            pieces.append(cur)
                        cur = None
                    else:
                        cur = (cur[0], q) if cur else (p, q)
                if cur:
                    pieces.append(cur)
                for (p, q) in pieces:
                    (k.wcol if walk else k.col)(p, q, y0, y1, z0, z1)
                continue
            (k.wcol if walk else k.col)(a, b, y0, y1, z0, z1)


def arc_rail_cols(k, cx, cy, r, half, z0, z1, a0=0.0, a1=2 * math.pi, tol=0.12):
    """a thin round rail (radius r, half thickness `half`) from angle a0 to a1 as small axis-aligned boxes: each box
    covers the arc stretch whose bounding box stays within `tol` of the rail's band"""
    a = a0
    while a < a1 - 1e-6:
        # grow the stretch while its bounding box stays thin in the direction across the rail
        da = 0.01
        while True:
            b = min(a1, a + da * 1.25)
            xs = [cx + math.cos(a + (b - a) * t / 8) * r for t in range(9)]
            ys = [cy + math.sin(a + (b - a) * t / 8) * r for t in range(9)]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if min(w, h) > tol or b >= a1 or b - a > 0.5:
                break
            da = b - a
        b = min(a1, a + da)
        xs = [cx + math.cos(a + (b - a) * t / 8) * r for t in range(9)]
        ys = [cy + math.sin(a + (b - a) * t / 8) * r for t in range(9)]
        k.col(min(xs) - half, max(xs) + half, min(ys) - half, max(ys) + half, z0, z1)
        a = b
