"""INKBOLT collision fit: no invisible walls.

A kit piece's collision is authored as <Piece>_COL<n> box empties (see kit_base.py). A single box over a whole prefab
is cheap to author but often blocks open air where the visual is a thin frame, a legs-only table, a round planter, a
skewed car, an open bike rack, a booth with a walk-in front ... (tests/e2e/collision-audit.spec.js finds those in game).

fit(family) runs just before a family's GLB export (ib_lib.export) and re-cuts the _COL boxes of the pieces listed in
FIT[family] to what the piece actually shows at player height:
  * the piece's evaluated mesh (ink hull included) is rasterised on a 5 cm grid inside each box's height band (from
    the box base, at least 0.2 m above the floor, 1.6 m up) -- a top-down footprint of everything drawn there;
  * the player's capsule (radius R) is flooded in from outside the box through every spot where it touches nothing
    drawn; the solid part is what the capsule can never reach (closed shapes stay solid inside, slots narrower than
    the capsule stay shut, so cover stays cover), grown by TOL so the capsule never sinks into a drawn surface;
  * that region is covered by at most K axis-aligned boxes (largest rectangles first, 10 cm blocks; its outer rim
    of one block may stay uncovered) that keep the
    original box's height. Boxes are never grown; walkable _WCOL boxes are never touched.
"""
import math
import re

import bpy
import numpy as np

R = 0.35       # player capsule radius (src/game/player.js MOVE.radius)
TOL = 0.1      # the solid region grows this much toward the capsule (the audit allows 0.15)
RES = 0.05     # raster cell (m)
BLK = 2        # cells per decomposition block (10 cm)
K = 16         # boxes per fitted box at most
BAND = 1.6     # height band above the box base (or 0.2 m above the floor)

# per family: piece names (without the KIT_<FAMILY>_ prefix) whose _COL boxes are re-cut; a name ending in '*' is a
# prefix match. Only pieces that the in-game audit flagged as blocking open air are listed.
FIT = {
    'kit-parking': ['Landmark_CarWash', 'BikeRack', 'Wreck_Burnt', 'Wreck_Burnt_B', 'Wreck_Smash', 'CarJack', 'CarCovered',
                    'Cage', 'Sedan', 'Sedan_Door', 'Hatchback', 'Hatch_Hazard', 'Hatch_Boot', 'SUV', 'SUV_Boot', 'Sports',
                    'Motorbike', 'Scooter', 'Buggy', 'Forklift'],
    'kit-mountains': ['Landmark_Lookout', 'Landmark_RopeBridge', 'Outcrop_A', 'Outcrop_B'],
    'kit-smallcity': ['Landmark_Fountain'],
    'kit-classroom': ['Backpack_A', 'Backpack_B', 'BeanBag_R', 'BeanBag_Y', 'Bin', 'Landmark_Globe'],
    'kit-bedroom': ['ClothesPile', 'CrayonPile_A', 'CrayonPile_B', 'Landmark_Bed', 'ToyCastle'],
    'kit-coalmine': ['Landmark_DrillRig', 'Landmark_Hopper'],
    'kit-castle': ['Barrels', 'Landmark_Trebuchet', 'Landmark_Well'],
    'kit-city2': ['Landmark_Subway'],
    'kit-downtown': ['TruckOver', 'Bus', 'Landmark_Tram', 'Hedgehog'],
    'kit-factory': ['Arm_A', 'Arm_B', 'Landmark_Booth', 'Landmark_Press', 'TestCage'],
    'kit-livingroom': ['Ball', 'Basket', 'Controller', 'Island', 'Mug', 'Plant_Fig', 'Plant_Snake'],
    'kit-garden': ['Landmark_Fountain', 'Landmark_PlayShip'],
    'kit-factory2': ['ChassisJig_Bruiser', 'ChassisJig_Walker', 'ChassisJig_*', 'Landmark_Titan', 'Machine_Brake'],
    'kit-island': ['Boat_A', 'Boat_B', 'Charger', 'Lagoon', 'Landmark_Lighthouse', 'Outcrop_A', 'Outcrop_B', 'PalmClump_A', 'PalmClump_B'],
    'kit-mall': ['BigPlanter', 'FoodTable', 'FoodTable_B', 'Landmark_Fountain', 'Landmark_GuestDesk'],
    'kit-grove': ['Boulder_A', 'Landmark_Cabin'],
    'kit-spire': ['Landmark_Bolt', 'Landmark_Reception', 'Tree_Cherry', 'Tree_Maple'],
    'kit-hotel': ['Landmark_SkyBar', 'Piano'],
    # not Line_* (the box over the moving line is cover for the robots riding it) nor the Bay decks' stair blocks
    'kit-datacenter': ['Landmark_Chamber', 'Landmark_Quantum', 'TileOpen'],
    'kit-foundry': ['CentipedeRack', 'Jig_Hound', 'Jig_Hover', 'Jig_*', 'Landmark_Bay_Armour', 'Landmark_Bay_Frame', 'Landmark_Bay_Launch',
                    'Landmark_Bay_Strider', 'Landmark_LaunchDoor1', 'Landmark_LaunchDoor2', 'Landmark_Strider_Legs',
                    'Landmark_Titan_Legs', 'LimbRack', 'Pad_Hound', 'Pad_Hover', 'Pad_*', 'WeldCell_Hover', 'WeldCell_Spider', 'WeldCell_*'],
}


# per family: pieces that had no _COL box (the theme fell back to a full-cell box: boxCols in zones.js); that box is
# authored here (Blender frame: x0, x1, y0, y1, z0, z1) and then fitted like the listed ones
ADD = {
    'kit-coalmine': {'Drums_A': (-0.5, 0.5, -0.5, 0.5, 0, 1.0), 'Drums_B': (-0.5, 0.5, -0.5, 0.5, 0, 1.0),
                     'CoalHeap_A': (-1, 1, -1, 1, 0, 1.0), 'CoalHeap_B': (-1, 1, -1, 1, 0, 1.0),
                     'Sacks_A': (-0.5, 0.5, -0.5, 0.5, 0, 1.0), 'Sacks_B': (-0.5, 0.5, -0.5, 0.5, 0, 1.0)},
    'kit-foundry': {'Drums_A': (-0.5, 0.5, -0.5, 0.5, 0, 1.0), 'Drums_B': (-0.5, 0.5, -0.5, 0.5, 0, 1.0),
                    'Cart_Gas': (-0.5, 0.5, -0.5, 0.5, 0, 1.2), 'Cart_Chest': (-0.5, 0.5, -0.5, 0.5, 0, 1.2),
                    'Cart_Screen': (-0.5, 0.5, -0.5, 0.5, 0, 1.2), 'Console': (-0.5, 0.5, -0.5, 0.5, 0, 1.2)},
    'kit-factory': {'Drums_A': (-0.5, 0.5, -0.5, 0.5, 0, 1.0), 'Drums_B': (-0.5, 0.5, -0.5, 0.5, 0, 1.0)},
    'kit-factory2': {'Drums_A': (-0.5, 0.5, -0.5, 0.5, 0, 1.0), 'Drums_B': (-0.5, 0.5, -0.5, 0.5, 0, 1.0)},
    'kit-island': {'Barrel_A': (-0.5, 0.5, -0.5, 0.5, 0, 0.9), 'Barrel_B': (-0.5, 0.5, -0.5, 0.5, 0, 0.9)},
}


def _match(family, piece):
    if piece in ADD.get(family, {}):
        return True
    for n in FIT.get(family, ()):
        if n.endswith('*') and piece.startswith(n[:-1]) or piece == n:
            return True
    return False


def _tris(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('vertices', tri)
    out = co.reshape(-1, 3)[tri.reshape(-1, 3)].copy()
    ev.to_mesh_clear()
    return out


_BARY = {}


def _bary(n):
    if n not in _BARY:
        uv = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
        _BARY[n] = np.array(uv)
    return _BARY[n]


def _raster(T, X0, Y0, nx, ny, za, zb):
    """mark[ny, nx]: cells holding a drawn surface between za and zb"""
    mark = np.zeros((ny, nx), dtype=bool)
    X1, Y1 = X0 + nx * RES, Y0 + ny * RES
    lo, hi = T.min(axis=1), T.max(axis=1)
    keep = (hi[:, 0] >= X0) & (lo[:, 0] <= X1) & (hi[:, 1] >= Y0) & (lo[:, 1] <= Y1) & (hi[:, 2] >= za) & (lo[:, 2] <= zb)
    stack = list(T[keep])
    while stack:
        t = stack.pop()
        lo, hi = t.min(axis=0), t.max(axis=0)
        if hi[0] < X0 or lo[0] > X1 or hi[1] < Y0 or lo[1] > Y1 or hi[2] < za or lo[2] > zb:
            continue
        e = max(np.linalg.norm(t[0] - t[1]), np.linalg.norm(t[1] - t[2]), np.linalg.norm(t[2] - t[0]))
        if e > 0.6:
            a, b, c = t
            ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
            stack.extend([np.array([a, ab, ca]), np.array([ab, b, bc]), np.array([ca, bc, c]), np.array([ab, bc, ca])])
            continue
        n = max(1, int(math.ceil(e / (RES * 0.7))))
        uv = _bary(n)
        p = t[0] * (1 - uv[:, :1] - uv[:, 1:]) + t[1] * uv[:, :1] + t[2] * uv[:, 1:]
        p = p[(p[:, 2] >= za) & (p[:, 2] <= zb)]
        i = np.floor((p[:, 0] - X0) / RES).astype(int)
        j = np.floor((p[:, 1] - Y0) / RES).astype(int)
        ok = (i >= 0) & (j >= 0) & (i < nx) & (j < ny)
        mark[j[ok], i[ok]] = True
    return mark


def _edt1(f):
    n = len(f)
    INF = 1e18
    v = [0] * n
    z = [0.0] * (n + 1)
    k = 0
    z[0], z[1] = -INF, INF
    for q in range(1, n):
        s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        while s <= z[k]:
            k -= 1
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        k += 1
        v[k] = q
        z[k] = s
        z[k + 1] = INF
    d = [0.0] * n
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def _edt(mask):
    """metres from each cell to the nearest True cell"""
    INF = 1e12
    ny, nx = mask.shape
    d = np.where(mask, 0.0, INF)
    for j in range(ny):
        d[j, :] = _edt1(list(d[j, :]))
    for i in range(nx):
        d[:, i] = _edt1(list(d[:, i]))
    return np.sqrt(d) * RES


def _flood(free):
    ny, nx = free.shape
    reach = np.zeros_like(free)
    st = [(j, i) for i in range(nx) for j in (0, ny - 1)] + [(j, i) for j in range(ny) for i in (0, nx - 1)]
    while st:
        j, i = st.pop()
        if j < 0 or i < 0 or j >= ny or i >= nx or reach[j, i] or not free[j, i]:
            continue
        reach[j, i] = True
        st.extend(((j + 1, i), (j - 1, i), (j, i + 1), (j, i - 1)))
    return reach


def _rects(solid):
    """cover the True blocks of solid[ny, nx] with at most K rectangles of all-True blocks, largest new area first"""
    ny, nx = solid.shape
    # must cover: the solid blocks one block in from its open edges (the outer rim may stay uncovered: the solid
    # region is TOL wider than the drawn one anyway); rectangles may reach over the whole solid region
    pad = np.pad(solid, 1, constant_values=True)
    need = solid & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    if not need.any():
        need = solid.copy()
    out = []
    while need.any() and len(out) < K:
        P = np.zeros((ny + 1, nx + 1), dtype=int)
        P[1:, 1:] = np.cumsum(np.cumsum(need, 0), 1)
        best, bi = 0, None
        h = [0] * nx
        for j in range(ny):
            for i in range(nx):
                h[i] = h[i] + 1 if solid[j, i] else 0
            st = []
            for i in range(nx + 1):
                cur = h[i] if i < nx else 0
                start = i
                while st and st[-1][1] >= cur:
                    s0, hh = st.pop()
                    if hh > 0:
                        j0, j1, i0, i1 = j - hh + 1, j + 1, s0, i
                        gain = P[j1, i1] - P[j0, i1] - P[j1, i0] + P[j0, i0]
                        if gain > best:
                            best, bi = gain, (j0, j1, i0, i1)
                    start = s0
                st.append((start, cur))
        if not bi:
            break
        j0, j1, i0, i1 = bi
        need[j0:j1, i0:i1] = False
        out.append(bi)
    return None if need.any() else out   # too ragged for K boxes: keep the authored box


def fit_box(T, c, h):
    """new boxes [(cx, cy, cz, hx, hy, hz)] for the box (centre c, half extents h) or None to keep it"""
    x0, x1, y0, y1, z0, z1 = c[0] - h[0], c[0] + h[0], c[1] - h[1], c[1] + h[1], c[2] - h[2], c[2] + h[2]
    za = max(z0, 0.2)
    zb = min(z1, za + BAND)
    if zb <= za:
        return None
    M = 2 * R + TOL + 0.15
    X0, Y0 = x0 - M, y0 - M
    nx, ny = int(math.ceil((x1 - x0 + 2 * M) / RES)), int(math.ceil((y1 - y0 + 2 * M) / RES))
    mark = _raster(T, X0, Y0, nx, ny, za - 0.05, zb + 0.05)
    reach = _flood(_edt(mark) > R)
    ds = _edt(reach)
    xs = X0 + (np.arange(nx) + 0.5) * RES
    ys = Y0 + (np.arange(ny) + 0.5) * RES
    inside = ((xs[None, :] >= x0) & (xs[None, :] <= x1)) & ((ys[:, None] >= y0) & (ys[:, None] <= y1))
    solid = (ds >= R - TOL) & inside
    # 10 cm blocks aligned to the box corner (a block is solid if any of its cells is); 20 cm if 10 cm needs > K boxes
    for blk in (BLK, 2 * BLK):
        bs = RES * blk
        bx, by = int(math.ceil((x1 - x0) / bs - 1e-6)), int(math.ceil((y1 - y0) / bs - 1e-6))
        blocks = np.zeros((by, bx), dtype=bool)
        jj, ii = np.nonzero(solid)
        if len(jj):
            bi = np.clip(((xs[ii] - x0) / bs).astype(int), 0, bx - 1)
            bj = np.clip(((ys[jj] - y0) / bs).astype(int), 0, by - 1)
            blocks[bj, bi] = True
        if blocks.all():
            return None
        rects = _rects(blocks)
        if rects is not None:
            break
    if rects is None:
        print('col_fit: too ragged, box kept', c, h)
        return None
    out = []
    for j0, j1, i0, i1 in rects:
        a, b = x0 + i0 * bs, min(x1, x0 + i1 * bs)
        e, f = y0 + j0 * bs, min(y1, y0 + j1 * bs)
        out.append(((a + b) / 2, (e + f) / 2, (z0 + z1) / 2, (b - a) / 2, (f - e) / 2, (z1 - z0) / 2))
    return out


def fit(family):
    if family not in FIT and family not in ADD:
        return
    pat = re.compile(r'^(.*)_COL(\d+)$')
    for short, (x0, x1, y0, y1, z0, z1) in ADD.get(family, {}).items():
        parent = next((o for o in bpy.data.objects if o.type == 'MESH' and re.sub(r'^KIT_[A-Z0-9]+_', '', o.name) == short), None)
        if parent is None or any(re.search(r'_W?COL\d+$', ch.name) for ch in parent.children):
            print('col_fit: ADD %s skipped (no such piece, or it has collision)' % short)
            continue
        e = bpy.data.objects.new('%s_COL0' % parent.name, None)
        e.empty_display_type = 'CUBE'
        e.parent = parent
        e.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        e.scale = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
        bpy.context.scene.collection.objects.link(e)
    by_piece = {}
    for o in list(bpy.data.objects):
        m = pat.match(o.name)
        if o.type == 'EMPTY' and m and o.parent is not None and o.parent.type == 'MESH':
            by_piece.setdefault(o.parent.name, []).append(o)
    for pname, cols in sorted(by_piece.items()):
        short = re.sub(r'^KIT_[A-Z0-9]+_', '', pname)
        if not _match(family, short):
            continue
        parent = cols[0].parent
        T = _tris(parent)
        top = 1 + max(int(re.search(r'(\d+)$', o.name).group(1)) for o in parent.children if re.search(r'_W?COL\d+$', o.name))
        n0, n1 = len(cols), 0
        for o in sorted(cols, key=lambda o: o.name):
            new = fit_box(T, tuple(o.location), tuple(abs(s) for s in o.scale))
            if new is None:
                n1 += 1
                continue
            for (cx, cy, cz, hx, hy, hz) in new:
                e = bpy.data.objects.new('%s_COL%d' % (pname, top), None)
                top += 1
                e.empty_display_size = 0.02
                e.empty_display_type = 'CUBE'
                e.parent = parent
                e.location = (cx, cy, cz)
                e.scale = (hx, hy, hz)
                bpy.context.scene.collection.objects.link(e)
                n1 += 1
            bpy.data.objects.remove(o, do_unlink=True)
        print('col_fit %-40s %d -> %d boxes' % (pname, n0, n1))
