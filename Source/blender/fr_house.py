"""INKBOLT kit-frontier: the settlement's buildings -- one generic house builder (log or plank walls with real door and
window openings, a porch, gable or false-front roofs, collision that follows the walls) and the furniture of the
walk-in interiors (the general store with its upstairs, the trading post, the bunkhouse), the closed cabins and
offices, the smithy shed and the stable. See fr_base.py for the conventions.

Building frame (Blender): x in [-W/2, W/2] along the front, y in [-D/2, D/2], the front (porch, street) at -Y.
Walls stand inside the footprint (front wall centre at the porch's back edge + T/2); floors are FLOOR up."""
import math
import random

import fr_detail as FD
from fr_base import (FLOOR, RISE, TREAD, by_normal, wall, window, gable, gable_end, shed_roof, stairs, rail_run,
                     lantern, crate, barrel, sack, post, log_x, log_y, segments)

T = 0.22   # wall thickness


def courses(k, axis, pos, s, u0, u1, v0, v1, every, holes, c, w=0.035):
    """horizontal seams (log courses / clapboards) on a wall face, broken at the holes"""
    n = int(round((v1 - v0) / every))
    for i in range(1, n):
        v = v0 + i * (v1 - v0) / n
        for (a, b) in segments(u0, u1, [h for h in holes if h[2] - 0.02 <= v <= h[3] + 0.02]):
            if b - a < 0.05:
                continue
            if axis == 'x':
                k.qy(a, b, v - w / 2, v + w / 2, pos + s * 0.005, s, c)
            else:
                k.qx(a, b, v - w / 2, v + w / 2, pos + s * 0.005, s, c)


def boards(k, axis, pos, s, u0, u1, v0, v1, every, holes, c, w=0.03):
    """vertical board seams on a wall face, broken at the holes"""
    n = int(round((u1 - u0) / every))
    for i in range(1, n):
        u = u0 + i * (u1 - u0) / n
        spans = [(v0, v1)]
        for (a, b, z0, z1) in holes:
            if a - 0.02 <= u <= b + 0.02:
                nxt = []
                for (p, q) in spans:
                    if z1 <= p or z0 >= q:
                        nxt.append((p, q))
                        continue
                    if z0 > p:
                        nxt.append((p, z0))
                    if z1 < q:
                        nxt.append((z1, q))
                spans = nxt
        for (p, q) in spans:
            if q - p < 0.05:
                continue
            if axis == 'x':
                k.qy(u - w / 2, u + w / 2, p, q, pos + s * 0.005, s, c)
            else:
                k.qx(u - w / 2, u + w / 2, p, q, pos + s * 0.005, s, c)


def floor_lines(k, x0, x1, y0, y1, z, every=0.3, c='plank2', along='y'):
    if along == 'y':
        n = int(round((x1 - x0) / every))
        for i in range(1, n):
            x = x0 + i * (x1 - x0) / n
            k.qz(x - 0.012, x + 0.012, y0 + 0.01, y1 - 0.01, z + 0.004, 1, c)
    else:
        n = int(round((y1 - y0) / every))
        for i in range(1, n):
            y = y0 + i * (y1 - y0) / n
            k.qz(x0 + 0.01, x1 - 0.01, y - 0.012, y + 0.012, z + 0.004, 1, c)


def corner_logs(k, x, y, z0, z1, sx, sy, every=0.42):
    """log-cabin corner: notched log ends sticking out past both walls (a column with end discs per course)"""
    e = 0.16
    xa, xb = sorted((x, x + sx * e))
    ya, yb = sorted((y, y + sy * e))
    k.bx(min(xa, x - sx * 0.3), max(xb, x - sx * 0.3), min(ya, y - sy * 0.3), max(yb, y - sy * 0.3), z0, z1 + 0.06, 'log2')
    n = int(round((z1 - z0) / every))
    for i in range(n):
        zc = z0 + (i + 0.5) * (z1 - z0) / n
        r = (z1 - z0) / n * 0.42
        # end discs on the front / back faces (the side faces show the notched column)
        fy = y + sy * e + sy * 0.004
        k.poly([(x - sx * 0.3 + sx * 0.15 + math.cos(a) * r * 0.9, fy, zc + math.sin(a) * r) for a in [j / 6 * 2 * math.pi for j in range(6)]], 'logEnd', (0, sy, 0))


def door_leaf(k, axis, pos, u0, u1, z0, z1, c='plank2', open_in=None, s=-1):
    """a plank door: closed in the hole (open_in None) or swung open against the inside wall (open_in = +1 / -1: the
    side of the hole its hinge is on)"""
    th = 0.05
    if open_in is None:
        if axis == 'x':
            k.bx(u0 + 0.01, u1 - 0.01, pos - th / 2, pos + th / 2, z0, z1 - 0.01, c)
        else:
            k.bx(pos - th / 2, pos + th / 2, u0 + 0.01, u1 - 0.01, z0, z1 - 0.01, c)
        return
    w = u1 - u0
    hu = u0 if open_in < 0 else u1
    if axis == 'x':
        # hinge at hu on the inside face (s points outside): the leaf lies along -s*Y from the wall
        d0 = pos - s * (T / 2 + 0.02)
        a, b = sorted((d0, d0 - s * w))
        k.bx(hu - th / 2 if open_in < 0 else hu - th / 2, hu + th / 2, a, b, z0 + 0.02, z1 - 0.03, c)
    else:
        d0 = pos - s * (T / 2 + 0.02)
        a, b = sorted((d0, d0 - s * w))
        k.bx(a, b, hu - th / 2, hu + th / 2, z0 + 0.02, z1 - 0.03, c)


def porch_posts(W, front):
    """porch post positions along the front: the two ends and evenly between, none in front of a door"""
    n = max(2, int(round(W / 2.6)) + 1)
    xs = [-W / 2 + 0.25 + (W - 0.5) * i / (n - 1) for i in range(n)]
    doors = [(a, b) for (a, b, z0, z1, kind) in front if kind in ('door', 'shut')]
    return [x for x in xs if not any(a - 0.45 < x < b + 0.45 for (a, b) in doors)]


def house(k, W, D, pd, eave, style='log', out='log', inside='plank', holes=None, roof='gable_x', ridge=None,
          ff_top=None, sign=None, sign_c=('plankW', 'ink'), porch_c='plank', walkin=True, roof_c=('shingle', 'shingle2'),
          chimney=None, glazed=(), open_win=(), shutters=None, upper=None, cols=True):
    """A one- or two-storey frontier building. holes: {'f'|'b'|'l'|'r': [(u0, u1, z0, z1, kind)]} with kind 'door'
    (an opening), 'win' (glazed window), 'open' (unglazed window: sight and shots pass), 'shut' (closed door leaf).
    Returns the frame dict (wall lines, floor) for the interior builder."""
    holes = holes or {}
    x0, x1 = -W / 2, W / 2
    yf = -D / 2 + pd + T / 2          # front wall centre line
    yb = D / 2 - T / 2               # back wall centre line
    xl, xr = x0 + T / 2, x1 - T / 2  # side wall centre lines
    ztop = eave
    F = {'x0': x0, 'x1': x1, 'yf': yf, 'yb': yb, 'xl': xl, 'xr': xr, 'ix0': x0 + T, 'ix1': x1 - T,
         'iy0': yf + T / 2, 'iy1': yb - T / 2, 'z': FLOOR if walkin else 0.0}
    sides = {
        'f': ('x', yf, x0, x1, -1),
        'b': ('x', yb, x0, x1, 1),
        'l': ('y', xl, yf + T / 2, yb - T / 2, -1),
        'r': ('y', xr, yf + T / 2, yb - T / 2, 1),
    }
    wall_top = {'f': ff_top or ztop, 'b': ztop, 'l': ztop, 'r': ztop}
    seam_c = 'logD' if style == 'log' else 'plank2'
    for key, (axis, pos, u0, u1, s) in sides.items():
        hl = holes.get(key, [])
        cut = [(a, b, z0, z1) for (a, b, z0, z1, kind) in hl if kind in ('door', 'open', 'win')] if walkin else \
              [(a, b, z0, z1) for (a, b, z0, z1, kind) in hl if kind == 'door']
        zt = wall_top[key]
        wall(k, axis, pos, u0, u1, 0.0, zt, T, cut, out, inside if walkin else out, top=('log2' if style == 'log' else 'plank2'),
             cols=cols)
        fu0, fu1 = (u0, u1) if axis == 'x' else (u0 - T / 2, u1 + T / 2)
        face = pos + s * T / 2
        if style == 'log':
            courses(k, axis, face, s, fu0 + (0.02 if axis == 'y' else 0.0), fu1 - (0.02 if axis == 'y' else 0.0), 0.0, zt, 0.42, [(a, b, z0, z1) for (a, b, z0, z1, kd) in hl], seam_c)
        else:
            boards(k, axis, face, s, fu0 + 0.02, fu1 - 0.02, 0.0, zt, 0.5, [(a, b, z0, z1) for (a, b, z0, z1, kd) in hl], seam_c)
        for (a, b, z0, z1, kind) in hl:
            if kind == 'win':
                window(k, axis, pos, s, a, b, z0, z1, T, frame='plankW' if style == 'plank' else 'plank', shutters=shutters,
                       gd=0.01 if walkin else T / 2 + 0.008)
                if walkin and cols:   # glazed: solid to shots and to anyone jumping at it
                    if axis == 'x':
                        k.col(a, b, pos - T / 2, pos + T / 2, z0, z1)
                    else:
                        k.col(pos - T / 2, pos + T / 2, a, b, z0, z1)
            elif kind == 'open':
                window(k, axis, pos, s, a, b, z0, z1, T, frame='plankW' if style == 'plank' else 'plank', open_=True, shutters=shutters)
            elif kind == 'door':
                window(k, axis, pos, s, a, b, z0, z1, T, frame='plank2' if style == 'log' else 'plankW', open_=True, sill=False)
            elif kind == 'shut':
                window(k, axis, pos, s, a, b, z0, z1, T, frame='plank2' if style == 'log' else 'plankW', open_=True, sill=False)
                if axis == 'x':
                    k.bx(a, b, pos + s * T / 2 + s * 0.004 - (0.04 if s > 0 else 0), pos + s * T / 2 + s * 0.004 + (0.04 if s < 0 else 0), z0, z1, 'plank2')
                else:
                    k.bx(pos + s * T / 2 + s * 0.004 - (0.04 if s > 0 else 0), pos + s * T / 2 + s * 0.004 + (0.04 if s < 0 else 0), a, b, z0, z1, 'plank2')
    if style == 'log':
        for (cx, cy, sx, sy) in ((x0, yf - T / 2, -1, -1), (x1, yf - T / 2, 1, -1), (x0, yb + T / 2, -1, 1), (x1, yb + T / 2, 1, 1)):
            corner_logs(k, cx, cy, 0.0, ztop, sx, sy)
    # floor inside (walk-in) and the porch
    if walkin:
        k.bx(F['ix0'], F['ix1'], F['iy0'], F['iy1'], 0.0, FLOOR, 'plank2')
        floor_lines(k, F['ix0'], F['ix1'], F['iy0'], F['iy1'], FLOOR, 0.6, 'logD')
        if cols:
            k.wcol(F['ix0'], F['ix1'], F['iy0'], F['iy1'], 0.0, FLOOR)
    if pd > 0.1:
        py0, py1 = -D / 2, yf - T / 2
        k.bx(x0 + 0.05, x1 - 0.05, py0, py1, 0.0, FLOOR, porch_c)
        floor_lines(k, x0 + 0.05, x1 - 0.05, py0, py1, FLOOR, 0.5, 'plank2', along='x')
        if cols:
            k.wcol(x0 + 0.05, x1 - 0.05, py0, py1, 0.0, FLOOR)
        # porch posts and roof
        ptop = 2.75
        for x in porch_posts(W, holes.get('f', [])):
            k.bx(x - 0.08, x + 0.08, py0 + 0.12, py0 + 0.28, FLOOR, ptop, 'log2' if style == 'log' else 'plankW')
            if cols:
                k.col(x - 0.09, x + 0.09, py0 + 0.11, py0 + 0.29, FLOOR, ptop)
        k.bx(x0 + 0.1, x1 - 0.1, py0 + 0.1, py0 + 0.3, ptop, ptop + 0.18, 'log2' if style == 'log' else 'plankW')
        zr_wall = min(ptop + 0.75, (ff_top or ztop) - 0.2) if roof != 'gable_x' else min(ptop + 0.75, ztop - 0.15)
        shed_roof(k, x0 - 0.05, x1 + 0.05, py0 - 0.25, py1 - 0.02, ptop + 0.17, zr_wall, 0.1, roof_c[0], roof_c[1])
    # roof
    if roof == 'gable_x':
        zr = ridge or (ztop + (yb - yf) * 0.5)
        gable(k, x0, x1, yf - T / 2, yb + T / 2, ztop, zr, 0.16, roof_c[0], roof_c[1], over=0.35, ridge_along='x')
        for xx in (xl, xr):
            gable_end(k, 'y', xx, yf - T / 2, yb + T / 2, ztop, zr - 0.16, T, out, inside if walkin else out)
    elif roof == 'gable_y':
        zr = ridge or (ztop + (x1 - x0) * 0.32)
        gable(k, x0, x1, (yf + 0.3) if ff_top else (yf - T / 2), yb + T / 2, ztop, zr, 0.16, roof_c[0], roof_c[1], over=0.3, ridge_along='y')
        gable_end(k, 'x', yb, x0, x1, ztop, zr - 0.16, T, out, inside if walkin else out)
        if not ff_top:
            gable_end(k, 'x', yf, x0, x1, ztop, zr - 0.16, T, out, inside if walkin else out)
    if ff_top:
        # false front: a cornice and a sign board on the upper facade
        k.bx(x0 - 0.12, x1 + 0.12, yf - T / 2 - 0.16, yf + T / 2 + 0.02, ff_top, ff_top + 0.16, 'plank2')
        k.bx(x0 - 0.06, x1 + 0.06, yf - T / 2 - 0.1, yf - T / 2 - 0.001, ff_top - 0.28, ff_top - 0.001, 'plankW' if out != 'plankW' else 'plankR', ink=False)
    if sign:
        word, sz0, sz1 = sign
        sy = yf - T / 2
        k.bx(x0 + 0.5, x1 - 0.5, sy - 0.06, sy - 0.004, sz0, sz1, sign_c[0])
        k.text(word, 0.0, sy - 0.064, sz0 + (sz1 - sz0) * 0.18, (sz1 - sz0) * 0.66, sign_c[1], maxw=W - 1.6, font='display')
    if chimney:
        cx, cy, ch = chimney
        k.bx(cx - 0.4, cx + 0.4, cy - 0.4, cy + 0.4, 0.0, ch, 'stone')
        k.bx(cx - 0.45, cx + 0.45, cy - 0.45, cy + 0.45, ch, ch + 0.12, 'stone2')
        if cols:
            k.col(cx - 0.4, cx + 0.4, cy - 0.4, cy + 0.4, 0.0, ch)
    FD.house_detail(k, W, D, pd, T, FLOOR, style, out, holes, ztop, ff_top, roof, roof_c, walkin, sign, chimney, shutters,
                   yf, yb, porch_posts(W, holes.get('f', [])), ridge)
    return F


# ---------------------------------------------------------------- furniture (z = the floor it stands on)
def table(k, x0, x1, y0, y1, z, h=0.78, c='plank', cols=True):
    k.bx(x0, x1, y0, y1, z + h - 0.06, z + h, c)
    for (x, y) in ((x0 + 0.08, y0 + 0.08), (x1 - 0.08, y0 + 0.08), (x0 + 0.08, y1 - 0.08), (x1 - 0.08, y1 - 0.08)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, z, z + h - 0.06, 'plank2', ink=False)
    if cols:
        k.col(x0, x1, y0, y1, z, z + h)


def bench(k, x0, x1, y0, y1, z, h=0.45, c='plank2', cols=True):
    k.bx(x0, x1, y0, y1, z + h - 0.05, z + h, c)
    for x in (x0 + 0.1, x1 - 0.1):
        k.bx(x - 0.03, x + 0.03, y0 + 0.03, y1 - 0.03, z, z + h - 0.05, 'plank2', ink=False)
    if cols:
        k.col(x0, x1, y0, y1, z, z + h)


def chair(k, x, y, z, face=0, c='plank2'):
    """simple ladder-back chair facing `face` degrees (0 = toward -Y)"""
    a = math.radians(face)
    ca, sa = math.cos(a), math.sin(a)
    def P(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    k.push(x, y, face, z)
    k.bx(-0.2, 0.2, -0.2, 0.2, 0.42, 0.46, c)
    for (u, v) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
        k.bx(u - 0.02, u + 0.02, v - 0.02, v + 0.02, 0.0, 0.42, 'plank2', ink=False)
    k.bx(-0.2, 0.2, 0.16, 0.2, 0.46, 0.95, c)
    k.pop()


def shelf(k, x0, x1, y0, y1, z, h, n, goods, rnd, c='plank2', cols=True, back='+y'):
    """open shelving unit with goods on each board; back: the wall side ('+y', '-y', '+x', '-x')"""
    th = 0.035
    along_x = back in ('+y', '-y')
    if along_x:
        for xa, xb in ((x0, x0 + 0.04), (x1 - 0.04, x1)):
            k.bx(xa, xb, y0, y1, z, z + h, c)
        by0, by1 = (y1 - 0.02, y1) if back == '+y' else (y0, y0 + 0.02)
        k.bx(x0 + 0.04, x1 - 0.04, by0, by1, z, z + h, 'plank', ink=False)
        bx0, bx1, cy0, cy1 = x0 + 0.04, x1 - 0.04, (y0 if back == '+y' else y0 + 0.02), (y1 - 0.02 if back == '+y' else y1)
    else:
        for ya, yb in ((y0, y0 + 0.04), (y1 - 0.04, y1)):
            k.bx(x0, x1, ya, yb, z, z + h, c)
        bxa, bxb = (x1 - 0.02, x1) if back == '+x' else (x0, x0 + 0.02)
        k.bx(bxa, bxb, y0 + 0.04, y1 - 0.04, z, z + h, 'plank', ink=False)
        bx0, bx1, cy0, cy1 = (x0 if back == '+x' else x0 + 0.02), (x1 - 0.02 if back == '+x' else x1), y0 + 0.04, y1 - 0.04
    gap = (h - 0.16) / max(1, n - 1)
    for i in range(n):
        zz = z + 0.12 + i * gap
        k.bx(bx0, bx1, cy0, cy1, zz - th, zz, c, ink=False)
        if i == n - 1:
            continue
        span = (bx1 - bx0 - 0.08) if along_x else (cy1 - cy0 - 0.08)
        depth = (cy1 - cy0) if along_x else (bx1 - bx0)
        m = max(1, int(span / 0.55))
        for j in range(m):
            if rnd.random() < 0.2:
                continue
            gc = goods[rnd.randrange(len(goods))]
            hh = rnd.uniform(0.12, max(0.13, min(0.3, gap - 0.06)))
            ww = rnd.uniform(0.1, 0.17)
            dd = rnd.uniform(0.14, max(0.15, depth - 0.1))
            u = (bx0 + 0.04 if along_x else cy0 + 0.04) + (j + 0.5) * span / m
            if along_x:
                fy = (cy0 + 0.03) if back == '+y' else (cy1 - 0.03)
                sg = -1 if back == '+y' else 1
                ty0, ty1 = sorted((fy, fy - sg * dd))
                k.qy(u - ww / 2, u + ww / 2, zz + 0.004, zz + hh, fy, sg, gc)
                k.qz(u - ww / 2, u + ww / 2, ty0, ty1, zz + hh, 1, gc)
            else:
                fx = (bx0 + 0.03) if back == '+x' else (bx1 - 0.03)
                sg = -1 if back == '+x' else 1
                tx0, tx1 = sorted((fx, fx - sg * dd))
                k.qx(u - ww / 2, u + ww / 2, zz + 0.004, zz + hh, fx, sg, gc)
                k.qz(tx0, tx1, u - ww / 2, u + ww / 2, zz + hh, 1, gc)
    if cols:
        k.col(x0, x1, y0, y1, z, z + h)


def counter(k, x0, x1, y0, y1, z, h=1.0, c='plank', top='plank2', cols=True):
    k.bx(x0 + 0.04, x1 - 0.04, y0 + 0.04, y1 - 0.04, z, z + h - 0.06, c)
    k.bx(x0, x1, y0, y1, z + h - 0.06, z + h, top)
    if cols:
        k.col(x0, x1, y0, y1, z, z + h)


def stove(k, x, y, z, cols=True, pipe_to=None):
    """pot-belly stove on a hearth plate with its stovepipe"""
    k.bx(x - 0.5, x + 0.5, y - 0.5, y + 0.5, z, z + 0.04, 'stone2', ink=False)
    k.cyl(x, y, z + 0.04, 0.26, 0.3, 0.3, 'iron2', seg=8)
    k.cyl(x, y, z + 0.34, 0.3, 0.24, 0.4, 'iron2', seg=8)
    k.cyl(x, y, z + 0.74, 0.25, 0.25, 0.08, 'iron', seg=8)
    k.bx(x - 0.1, x + 0.1, y - 0.32, y - 0.25, z + 0.3, z + 0.48, 'fire', ink=False)
    top = pipe_to or (z + 2.6)
    k.cyl(x, y, z + 0.82, 0.07, 0.07, top - z - 0.82, 'iron', seg=6)
    if cols:
        k.col(x - 0.32, x + 0.32, y - 0.32, y + 0.32, z, z + 0.85)


def bunk(k, x0, x1, y0, y1, z, rnd, blanket='cloth', cols=True):
    """double-deck bunk bed (posts, two frames, mattresses, blankets, pillows)"""
    for (x, y) in ((x0 + 0.04, y0 + 0.04), (x1 - 0.04, y0 + 0.04), (x0 + 0.04, y1 - 0.04), (x1 - 0.04, y1 - 0.04)):
        k.bx(x - 0.045, x + 0.045, y - 0.045, y + 0.045, z, z + 1.75, 'log2', ink=False)
    for zz in (0.3, 1.25):
        k.bx(x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, z + zz, z + zz + 0.1, 'plank2')
        k.bx(x0 + 0.06, x1 - 0.06, y0 + 0.06, y1 - 0.06, z + zz + 0.1, z + zz + 0.2, 'canvas', ink=False)
        bc = blanket if rnd.random() < 0.6 else 'cloth2'
        along_y = (y1 - y0) > (x1 - x0)
        if along_y:
            k.bx(x0 + 0.05, x1 - 0.05, y0 + 0.5, y1 - 0.05, z + zz + 0.2, z + zz + 0.26, bc, ink=False)
            k.bx(x0 + 0.15, x1 - 0.15, y0 + 0.1, y0 + 0.42, z + zz + 0.2, z + zz + 0.3, 'canvas', ink=False)
        else:
            k.bx(x0 + 0.5, x1 - 0.05, y0 + 0.05, y1 - 0.05, z + zz + 0.2, z + zz + 0.26, bc, ink=False)
            k.bx(x0 + 0.1, x0 + 0.42, y0 + 0.15, y1 - 0.15, z + zz + 0.2, z + zz + 0.3, 'canvas', ink=False)
    if cols:
        k.col(x0, x1, y0, y1, z, z + 1.75)


def trunk_box(k, x, y, z, face=0, c='plankR'):
    k.push(x, y, face, z)
    k.bx(-0.4, 0.4, -0.25, 0.25, 0.0, 0.42, c)
    k.bx(-0.42, 0.42, -0.27, 0.27, 0.42, 0.48, 'plank2')
    for u in (-0.3, 0.3):
        k.bx(u - 0.03, u + 0.03, -0.28, 0.28, 0.004, 0.5, 'iron', ink=False)
    k.pop()


def radio_desk(k, x0, x1, y0, y1, z, cols=True):
    """a field radio set on a desk: transceiver with dials, a headset, a battery box, a laptop"""
    table(k, x0, x1, y0, y1, z, 0.76, 'plank', cols=cols)
    t = z + 0.76
    cx = (x0 + x1) / 2
    k.bx(cx - 0.35, cx + 0.15, y1 - 0.38, y1 - 0.06, t, t + 0.3, 'olive')
    k.qy(cx - 0.3, cx + 0.1, t + 0.05, t + 0.25, y1 - 0.384, -1, 'iron2')
    for i in range(3):
        k.cyl(cx - 0.24 + i * 0.12, y1 - 0.39, t + 0.16, 0.025, 0.025, 0.02, 'fire2', seg=6, rot=(90, 0, 0), ink=False)
    k.bx(cx + 0.22, cx + 0.5, y1 - 0.34, y1 - 0.1, t, t + 0.2, 'iron')
    k.bx(cx - 0.1, cx + 0.25, y0 + 0.05, y0 + 0.27, t + 0.004, t + 0.024, 'iron2', ink=False)
    k.bxr(cx + 0.075, y0 + 0.3, t + 0.13, 0.35, 0.02, 0.22, 'iron2', rot=(-20, 0, 0), ink=False)
    k.bxr(cx + 0.075, y0 + 0.288, t + 0.135, 0.3, 0.004, 0.17, 'solar2', rot=(-20, 0, 0), ink=False)


# ---------------------------------------------------------------- the buildings
def build_store(k, ao):
    """HOLLIS GENERAL STORE [10, 10]: plank false front, walk-in on two floors (the upstairs at 3.55 m: storeroom and
    the storekeeper's room, open front windows over the street, 3.59 m), stair along the back wall, back door."""
    rnd = random.Random(501)
    W, D, pd = 10.0, 10.0, 2.0
    UF = FLOOR + 18 * RISE            # upper floor top 3.59
    k.begin()
    holes = {
        'f': [(-0.8, 0.8, FLOOR, 2.65, 'door'), (-4.0, -1.7, 1.0, 2.55, 'win'), (1.7, 4.0, 1.0, 2.55, 'win'),
              (-3.3, -1.7, UF + 0.85, UF + 1.95, 'open'), (1.7, 3.3, UF + 0.85, UF + 1.95, 'open')],
        'b': [(2.4, 3.8, FLOOR, 2.55, 'door'), (-2.2, -0.8, UF + 0.9, UF + 1.9, 'win')],
        'l': [(-1.0, 0.6, 1.1, 2.3, 'win')],
        'r': [(1.8, 3.2, 1.1, 2.3, 'win'), (-0.6, 0.8, UF + 0.9, UF + 1.9, 'win')],
    }
    F = house(k, W, D, pd, 6.3, style='plank', out='plankW', inside='plank', holes=holes, roof='gable_y', ridge=7.5,
              ff_top=8.0, sign=('HOLLIS GENERAL STORE', 6.45, 7.55), sign_c=('plankR', 'plankW'), roof_c=('shingle', 'shingle2'))
    ix0, ix1, iy0, iy1, z = F['ix0'], F['ix1'], F['iy0'], F['iy1'], FLOOR
    # lettering under the porch roof: GROCERIES / HARDWARE / FEED
    k.text('DRY GOODS', -2.85, F['yf'] - T / 2 - 0.012, 2.68, 0.17, 'plankR', maxw=2.0, font='display')
    k.text('HARDWARE', 2.85, F['yf'] - T / 2 - 0.012, 2.68, 0.17, 'plankR', maxw=2.0, font='display')
    # ---- upper floor slab with the stairwell (the stair runs along the back wall toward -X)
    sy0, sy1 = iy1 - 1.25, iy1
    sx_top = -3.5                      # the top tread ends here; the landing is x < -3.5
    hole = (sx_top, 1.15, sy0 - 0.05, iy1)
    for (a, b, c0, c1) in ((ix0, ix1, iy0, hole[2]), (ix0, hole[0], hole[2], iy1), (hole[1], ix1, hole[2], iy1)):
        k.bx(a, b, c0, c1, UF - 0.25, UF, 'plank2')
        k.wcol(a, b, c0, c1, UF - 0.25, UF)
        floor_lines(k, a, b, c0, c1, UF, 0.6, 'logD')
    # stair: 18 treads from x = 1.0 down to -3.5, rising toward -X
    for i in range(18):
        xa = 1.0 - i * TREAD
        xb = xa - TREAD
        za = z + (i + 1) * RISE
        k.bx(xb, xa, sy0 + 0.02, sy1 - 0.02, za - 0.06, za, 'plank' if i % 2 else 'plank2', ink=False)
        k.wcol(xb, xa, sy0 + 0.02, sy1 - 0.02, z, za)
    pts = [(x, y, zz) for y in (sy0 - 0.02, sy0 + 0.02) for (x, zz) in ((1.0, z), (sx_top, UF), (sx_top, UF - 0.3), (0.7, z))]
    k.hullp(pts, 'plank2')
    # stairwell rail on the upper floor (along the hole's front edge and its east end)
    rail_run(k, 'x', hole[0] + 0.3, hole[1], hole[2] - 0.05, UF, 1.0, 'plank2', posts=1.0, r=0.04)
    rail_run(k, 'y', hole[2] - 0.05, iy1 - 0.05, hole[1], UF, 1.0, 'plank2', posts=1.2, r=0.04)
    k.col(hole[0] + 0.25, hole[1] + 0.1, hole[2] - 0.1, hole[2], UF, UF + 1.0)
    k.col(hole[1] - 0.05, hole[1] + 0.05, hole[2] - 0.1, iy1, UF, UF + 1.0)
    # ---- ground floor: shelves of stock on the left wall, the counter on the right, the stove, barrels and sacks
    goods = ['plankR', 'cloth2', 'fuel', 'olive', 'canvas', 'steel', 'glassL', 'cloth']
    shelf(k, ix0, ix0 + 0.45, iy0 + 1.4, iy0 + 4.6, z, 2.3, 5, goods, rnd, back='-x')
    counter(k, 1.7, 2.3, iy0 + 1.2, iy0 + 4.4, z, 1.0)
    shelf(k, ix1 - 0.42, ix1, iy0 + 2.2, iy0 + 4.3, z, 2.3, 5, goods, rnd, back='+x')
    # scale and a cash box on the counter, a lantern above
    k.bx(1.85, 2.15, iy0 + 1.5, iy0 + 1.8, z + 1.0, z + 1.18, 'iron')
    k.cyl(2.0, iy0 + 1.65, z + 1.18, 0.12, 0.14, 0.03, 'fuel', seg=8, ink=False)
    k.bx(1.8, 2.2, iy0 + 3.4, iy0 + 3.75, z + 1.0, z + 1.2, 'iron2')
    stove(k, -0.9, iy0 + 3.0, z, pipe_to=UF - 0.25)
    table(k, -1.9, -0.9, iy0 + 0.9, iy0 + 1.7, z, 0.75, 'plank')
    chair(k, -2.3, iy0 + 1.3, z, -90)
    chair(k, -0.5, iy0 + 1.3, z, 90)
    barrel(k, -3.3, iy0 + 0.6, z, 0.3, 0.85, 'plank2')
    barrel(k, -2.6, iy0 + 0.45, z, 0.28, 0.8, 'plank')
    k.col(-3.62, -2.3, iy0 + 0.15, iy0 + 0.92, z, z + 0.85)
    for (x, y) in ((4.2, iy1 - 0.45), (4.25, iy1 - 0.95)):
        sack(k, rnd, x, y, z, 1.0, 'canvas2')
    k.col(3.94, ix1 - 0.02, iy1 - 1.2, iy1 - 0.2, z, z + 0.5)
    crate(k, ix1 - 0.45, iy0 + 0.6, z, 0.7, 0.7, 0.6, 'plank', 'plank2')
    k.col(ix1 - 0.82, ix1 - 0.08, iy0 + 0.23, iy0 + 0.97, z, z + 0.6)
    lantern(k, 0.0, iy0 + 2.0, UF - 0.3)
    # ---- upstairs: the storeroom (crates, sacks, a spare stove) at the front, the storekeeper's room at the back right
    crate(k, -3.9, iy0 + 0.8, UF, 0.9, 0.8, 0.7, 'olive', 'olive2')
    crate(k, -3.9, iy0 + 0.8, UF + 0.7, 0.7, 0.6, 0.5, 'plank', 'plank2')
    k.col(-4.35, -3.45, iy0 + 0.4, iy0 + 1.2, UF, UF + 1.2)
    crate(k, 3.9, iy0 + 0.7, UF, 0.9, 0.8, 0.7, 'plank', 'plank2')
    k.col(3.45, 4.35, iy0 + 0.3, iy0 + 1.1, UF, UF + 0.7)
    for (x, y) in ((-1.6, iy0 + 3.2), (-1.1, iy0 + 3.25), (-1.35, iy0 + 2.8)):
        sack(k, rnd, x, y, UF, 0.95, 'canvas2')
    k.col(-1.9, -0.8, iy0 + 2.55, iy0 + 3.5, UF, UF + 0.5)
    # bed, washstand and trunk in the back-right room (open to the loft)
    k.bx(2.2, 4.2, iy1 - 2.6, iy1 - 1.6, UF, UF + 0.42, 'plank2')
    k.bx(2.25, 4.15, iy1 - 2.55, iy1 - 1.65, UF + 0.42, UF + 0.55, 'canvas')
    k.bx(2.6, 4.15, iy1 - 2.58, iy1 - 1.62, UF + 0.55, UF + 0.6, 'cloth2', ink=False)
    k.bx(ix1 - 0.08, ix1, iy1 - 2.6, iy1 - 1.6, UF, UF + 0.95, 'plank2', ink=False)
    k.col(2.2, 4.2, iy1 - 2.6, iy1 - 1.6, UF, UF + 0.6)
    trunk_box(k, 1.4, iy1 - 2.1, UF, 90)
    k.col(1.12, 1.68, iy1 - 2.52, iy1 - 1.68, UF, UF + 0.5)
    table(k, 3.2, 4.1, iy0 + 2.3, iy0 + 3.1, UF, 0.75)
    chair(k, 2.8, iy0 + 2.7, UF, -90)
    lantern(k, 0.5, iy0 + 1.5, 6.0)
    k.finish('Store', ao=ao)


def build_trading_post(k, ao):
    """CINDER RIDGE TRADING POST [10, 9]: a log building with a sign board on the porch roof, walk-in: the trade
    counter on the right, goods tables, the radio desk at the back, a side door on the west wall."""
    rnd = random.Random(502)
    W, D, pd = 10.0, 9.0, 2.0
    k.begin()
    holes = {
        'f': [(-0.8, 0.8, FLOOR, 2.5, 'door'), (-3.9, -2.3, 1.15, 2.25, 'win'), (2.3, 3.9, 1.15, 2.25, 'win')],
        'b': [(-3.6, -2.4, 1.2, 2.2, 'win'), (1.0, 2.2, 1.2, 2.2, 'win')],
        'l': [(1.3, 2.9, FLOOR, 2.45, 'door')],
        'r': [(-0.4, 1.0, 1.2, 2.2, 'win')],
    }
    F = house(k, W, D, pd, 3.3, style='log', out='log', inside='plank', holes=holes, roof='gable_x', ridge=5.2,
              shutters='plankGr', roof_c=('shingle', 'shingle2'), chimney=(-1.2, 4.05, 6.0))
    ix0, ix1, iy0, iy1, z = F['ix0'], F['ix1'], F['iy0'], F['iy1'], FLOOR
    # sign board on the porch roof
    sy = F['yf'] - T / 2 - 1.1
    k.bx(-3.8, 3.8, sy - 0.05, sy + 0.05, 3.35, 4.25, 'plank2')
    for x in (-3.4, 3.4):
        k.bx(x - 0.05, x + 0.05, sy + 0.05, sy + 0.4, 3.0, 4.2, 'log2', ink=False)
    k.text('CINDER RIDGE TRADING POST', 0.0, sy - 0.054, 3.55, 0.5, 'plankW', maxw=7.2, font='display')
    goods = ['cloth', 'cloth2', 'rope', 'canvas', 'fuel', 'olive', 'steel', 'plankR']
    counter(k, 2.1, 2.7, iy0 + 0.9, iy0 + 4.6, z, 1.0, 'plank2', 'plank')
    shelf(k, ix1 - 0.42, ix1, iy0 + 1.0, iy0 + 3.4, z, 2.2, 5, goods, rnd, back='+x')
    # goods tables: folded blankets, rope coils, lanterns, a set of scales
    table(k, -3.6, -1.9, iy0 + 1.3, iy0 + 2.3, z, 0.8)
    for i, c in enumerate(('cloth', 'cloth2', 'canvas2', 'cloth')):
        k.bx(-3.5 + i * 0.4, -3.15 + i * 0.4, iy0 + 1.45, iy0 + 2.1, z + 0.8, z + 0.8 + 0.12 + 0.05 * (i % 2), c, ink=False)
    table(k, -0.8, 0.8, iy0 + 3.2, iy0 + 4.1, z, 0.8)
    for x in (-0.5, 0.0, 0.5):
        k.cyl(x, iy0 + 3.65, z + 0.8, 0.17, 0.17, 0.1, 'rope', seg=8, ink=False)
        k.cyl(x, iy0 + 3.65, z + 0.9, 0.08, 0.08, 0.004, 'plank2', seg=8, ink=False)
    for x in (-3.4, -2.6):
        lantern(k, x, iy0 + 1.8, 3.1, 1.0)
    radio_desk(k, -4.4, -2.9, iy1 - 0.75, iy1 - 0.05, z)
    chair(k, -3.65, iy1 - 1.05, z, 180)
    barrel(k, 1.2, iy0 + 0.55, z, 0.3, 0.85)
    barrel(k, 0.55, iy0 + 0.5, z, 0.28, 0.8, 'plank')
    k.col(0.22, 1.52, iy0 + 0.2, iy0 + 0.87, z, z + 0.85)
    crate(k, ix1 - 0.55, iy0 + 0.47, z, 0.75, 0.75, 0.65, 'olive', 'olive2')
    crate(k, ix1 - 0.55, iy0 + 0.47, z + 0.65, 0.6, 0.6, 0.45)
    k.col(ix1 - 0.95, ix1 - 0.15, iy0 + 0.07, iy0 + 0.87, z, z + 1.1)
    # the fireplace in the chimney breast
    k.qy(-1.45, -0.95, FLOOR + 0.1, FLOOR + 0.7, 3.65 - 0.006, -1, 'coal')
    k.qy(-1.38, -1.02, FLOOR + 0.12, FLOOR + 0.4, 3.65 - 0.01, -1, 'fire')
    for x, y in ((-1.2, iy0 + 0.5), (-0.7, iy0 + 0.6)):
        sack(k, rnd, x, y, z, 0.9, 'canvas2')
    k.col(-1.45, -0.45, iy0 + 0.28, iy0 + 0.8, z, z + 0.45)
    k.finish('TradingPost', ao=ao)


def build_bunkhouse(k, ao):
    """BUNKHOUSE [12, 8]: a long log bunkhouse, walk-in: four bunk beds, footlockers, the mess table with benches,
    the stove, a battery bank with chargers; front and back doors."""
    rnd = random.Random(503)
    W, D, pd = 12.0, 8.0, 1.5
    k.begin()
    holes = {
        'f': [(-0.8, 0.8, FLOOR, 2.5, 'door'), (-4.6, -3.2, 1.2, 2.2, 'win'), (3.2, 4.6, 1.2, 2.2, 'win')],
        'b': [(-0.2, 1.4, FLOOR, 2.45, 'door'), (-3.4, -2.2, 1.2, 2.2, 'win'), (2.6, 3.4, 1.2, 2.2, 'win')],
        'l': [(0.3, 1.5, 1.2, 2.2, 'win')],
        'r': [],
    }
    F = house(k, W, D, pd, 3.2, style='log', out='log2', inside='plank', holes=holes, roof='gable_x', ridge=4.9,
              shutters='plankR', roof_c=('tin', 'tin2'))
    ix0, ix1, iy0, iy1, z = F['ix0'], F['ix1'], F['iy0'], F['iy1'], FLOOR
    sy = F['yf'] - T / 2
    k.bx(-1.3, 1.3, sy - 0.05, sy - 0.003, 2.62, 3.05, 'plank2')
    k.text('BUNKHOUSE', 0.0, sy - 0.054, 2.7, 0.27, 'plankW', maxw=2.3, font='display')
    # bunks: two on each end wall, heads to the wall
    for (x0, x1) in ((ix0 + 0.05, ix0 + 2.05), (ix1 - 2.05, ix1 - 0.05)):
        for (y0, y1) in ((iy0 + 0.6, iy0 + 1.5), (iy1 - 1.4, iy1 - 0.5)):
            bunk(k, x0, x1, y0, y1, z, rnd)
            fx = x1 + 0.1 if x0 < 0 else x0 - 0.6
            trunk_box(k, fx + 0.25, (y0 + y1) / 2, z, 90)
            k.col(fx, fx + 0.5, (y0 + y1) / 2 - 0.42, (y0 + y1) / 2 + 0.42, z, z + 0.5)
    # mess table with two benches in the middle; the stove by the back wall
    table(k, -1.3, 1.3, iy0 + 2.1, iy0 + 3.0, z, 0.78)
    bench(k, -1.2, 1.2, iy0 + 1.55, iy0 + 1.85, z)
    bench(k, -1.2, 1.2, iy0 + 3.25, iy0 + 3.55, z)
    for x in (-0.7, 0.4):
        k.cyl(x, iy0 + 2.5, z + 0.78, 0.08, 0.07, 0.12, 'steel', seg=6, ink=False)
    lantern(k, 0.0, iy0 + 2.55, 3.4)
    stove(k, -1.0, iy1 - 0.65, z, pipe_to=4.6)
    # battery bank with chargers (modern), coat pegs with coats
    k.bx(1.6, 2.6, iy1 - 0.55, iy1 - 0.05, z, z + 0.7, 'olive')
    k.bx(1.7, 2.5, iy1 - 0.56, iy1 - 0.55, z + 0.4, z + 0.62, 'iron2', ink=False)
    for x in (1.85, 2.05, 2.25):
        k.bx(x - 0.04, x + 0.04, iy1 - 0.4, iy1 - 0.2, z + 0.7, z + 0.82, 'fire2', ink=False)
    k.col(1.6, 2.6, iy1 - 0.55, iy1 - 0.05, z, z + 0.7)
    k.bx(-2.75, -1.25, iy0 + 0.02, iy0 + 0.08, z + 1.7, z + 1.78, 'plank2', ink=False)
    for i, c in enumerate(('cloth', 'olive', 'cloth2')):
        x = -2.5 + i * 0.5
        k.bx(x - 0.18, x + 0.18, iy0 + 0.08, iy0 + 0.2, z + 0.85, z + 1.72, c, ink=False)
    k.finish('Bunkhouse', ao=ao)


def build_cabins(k, ao):
    """closed buildings along the street: two log cabins and a plank house (repainted per copy by the theme), the
    CLAIMS & RADIO office (false front, an antenna on the roof)"""
    rnd = random.Random(504)
    for name, style, out in (('Cabin', 'log', 'log'), ('House', 'plank', 'plankW')):
        k.begin()
        holes = {'f': [(-0.65, 0.65, FLOOR, 2.35, 'shut'), (-3.0, -1.8, 1.15, 2.1, 'win'), (1.8, 3.0, 1.15, 2.1, 'win')],
                 'l': [(-0.2, 1.0, 1.15, 2.1, 'win')], 'r': [(0.2, 1.4, 1.15, 2.1, 'win')], 'b': [(-1.0, 0.2, 1.15, 2.1, 'win')]}
        F = house(k, 8.0, 7.0, 1.7, 3.0, style=style, out=out, holes=holes, roof='gable_x', ridge=4.7, walkin=False,
                  shutters=('plankGr' if name == 'Cabin' else 'plankB'),
                  roof_c=('shingle', 'shingle2') if name == 'Cabin' else ('tin', 'tin2'),
                  chimney=(3.3, 2.6, 5.4), cols=False)
        k.col(F['x0'], F['x1'], F['yf'] - T / 2, F['yb'] + T / 2, 0.0, 3.0)
        py0 = -3.5
        k.wcol(F['x0'] + 0.05, F['x1'] - 0.05, py0, F['yf'] - T / 2, 0.0, FLOOR)
        for x in porch_posts(8.0, holes['f']):
            k.col(x - 0.09, x + 0.09, py0 + 0.11, py0 + 0.29, FLOOR, 2.75)
        k.col(2.9, 3.7, 2.2, 3.0, 3.0, 5.4)
        # porch furniture: a bench, a rocking chair, a lantern by the door
        bench(k, -3.6, -2.2, py0 + 0.9, py0 + 1.25, FLOOR)
        chair(k, 2.6, py0 + 0.9, FLOOR, 20)
        k.col(2.3, 2.9, py0 + 0.62, py0 + 1.2, FLOOR, FLOOR + 0.95)
        lantern(k, 1.0, F['yf'] - T / 2 - 0.12, 2.5)
        k.finish(name, ao=ao)
    # CLAIMS & RADIO office: false front, an antenna mast and a dish on the roof
    k.begin()
    holes = {'f': [(-0.65, 0.65, FLOOR, 2.4, 'shut'), (-3.2, -1.6, 1.05, 2.35, 'win'), (1.6, 3.2, 1.05, 2.35, 'win')],
             'l': [(0.0, 1.3, 1.15, 2.1, 'win')], 'r': [(-0.6, 0.7, 1.15, 2.1, 'win')], 'b': []}
    F = house(k, 8.0, 8.0, 1.8, 3.6, style='plank', out='plankB', holes=holes, roof='gable_y', ridge=4.9, ff_top=5.6,
              sign=('CLAIMS & RADIO', 4.0, 5.0), sign_c=('plankW', 'ink'), walkin=False, shutters=None, cols=False)
    k.col(F['x0'], F['x1'], F['yf'] - T / 2, F['yb'] + T / 2, 0.0, 3.6)
    k.wcol(F['x0'] + 0.05, F['x1'] - 0.05, -4.0, F['yf'] - T / 2, 0.0, FLOOR)
    for x in porch_posts(8.0, holes['f']):
        k.col(x - 0.09, x + 0.09, -3.89, -3.71, FLOOR, 2.75)
    # antenna mast at the back gable and a small dish
    k.cyl(2.2, 3.0, 3.6, 0.06, 0.05, 5.0, 'steel', seg=5)
    for zz in (5.0, 6.4, 7.6):
        k.bx(1.6, 2.8, 2.98, 3.02, zz, zz + 0.04, 'steel', ink=False)
    k.cyl(2.2, 3.0, 8.6, 0.06, 0.06, 0.12, 'red', seg=6, ink=False)
    k.push(-2.2, 2.4, 0, 4.15)
    k.cyl(0, 0, 0, 0.05, 0.05, 0.5, 'steel', seg=5)
    k.cyl(0, -0.1, 0.5, 0.45, 0.12, 0.18, 'white', seg=10, rot=(-60, 0, 0))
    k.pop()
    bench(k, 2.0, 3.4, -3.1, -2.75, FLOOR)
    lantern(k, -1.0, F['yf'] - T / 2 - 0.12, 2.55)
    k.finish('Office', ao=ao)


def build_smithy(k, ao):
    """SMITHY [8, 7]: an open-sided timber shed (plank back and west walls), the stone forge with its glowing coals,
    hood and chimney, the bellows, the anvil on its stump, the quench tub, the tool rack, the grindstone, iron stock."""
    rnd = random.Random(505)
    k.begin()
    x0, x1, y0, y1 = -4.0, 4.0, -3.5, 3.5
    H = 3.4
    # plank back wall (+Y) and west wall (-X), posts elsewhere
    wall(k, 'x', y1 - 0.1, x0, x1, 0.0, 4.55, 0.2, [], 'plankG', 'plank', top='plank2')
    wall(k, 'y', x0 + 0.1, y0 + 0.3, y1 - 0.2, 0.0, H, 0.2, [(-1.0, 0.6, 1.2, 2.2)], 'plankG', 'plank', top='plank2')
    boards(k, 'x', y1, 1, x0 + 0.02, x1 - 0.02, 0.0, 4.55, 0.5, [], 'plank2')
    boards(k, 'y', x0, -1, y0 + 0.3, y1 - 0.2, 0.0, H, 0.5, [(-1.0, 0.6, 1.2, 2.2)], 'plank2')
    for (x, y) in ((x0 + 0.15, y0 + 0.15), (0.0, y0 + 0.15), (x1 - 0.15, y0 + 0.15), (x1 - 0.15, 0.0), (x1 - 0.15, y1 - 0.35)):
        k.bx(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.0, H, 'log2')
        k.col(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.0, H)
    k.bx(x0, x1, y0 + 0.02, y0 + 0.28, H, H + 0.22, 'log2')
    k.bx(x1 - 0.28, x1 - 0.02, y0 + 0.28, y1 - 0.2, H, H + 0.22, 'log2')
    shed_roof(k, x0 - 0.3, x1 + 0.3, y0 - 0.45, y1 + 0.3, H + 0.2, H + 1.4, 0.14, 'tin', 'tin2')
    # forge: stone hearth against the back wall (west half), coals, a hood and a chimney through the roof
    fx0, fx1, fy0, fy1 = -3.7, -1.4, 1.5, 3.3
    k.bx(fx0, fx1, fy0, fy1, 0.0, 0.85, 'stone')
    k.bx(fx0 + 0.25, fx1 - 0.25, fy0 + 0.2, fy1 - 0.3, 0.85, 0.9, 'coal', ink=False)
    k.col(fx0, fx1, fy0, fy1, 0.0, 0.9)
    k.hullp([(x, y, z) for (x, y) in ((fx0 + 0.1, fy0 + 0.1), (fx1 - 0.1, fy0 + 0.1), (fx0 + 0.1, fy1), (fx1 - 0.1, fy1)) for z in (1.75,)] +
            [(x, y, 2.5) for (x, y) in ((-2.95, 2.6), (-2.15, 2.6), (-2.95, 3.3), (-2.15, 3.3))], 'stone2')
    k.bx(-2.95, -2.15, 2.6, 3.3, 2.5, H + 2.2, 'stone2')
    k.bx(-3.0, -2.1, 2.55, 3.35, H + 2.2, H + 2.32, 'stone')
    k.col(-2.95, -2.15, 2.6, 3.3, 1.75, H + 2.2)
    # bellows: two boards and a leather bag, on a frame by the forge
    k.push(-0.9, 2.5, 0, 0)
    k.bx(-0.06, 0.06, -0.45, 0.45, 0.0, 0.7, 'plank2')
    k.hullp([(-0.3, -0.5, 0.8), (0.3, -0.5, 0.8), (-0.3, 0.5, 0.85), (0.3, 0.5, 0.85), (0.0, -0.2, 1.05), (0.0, 0.3, 1.1)], 'dirt2')
    k.beam((0.0, -0.6, 0.95), (-0.45, -0.8, 0.9), 0.05, 'plank2')
    k.pop()
    k.col(-1.25, -0.55, 1.95, 3.05, 0.0, 1.1)
    # the anvil on its stump
    k.cyl(0.6, 0.2, 0.0, 0.32, 0.3, 0.55, 'log', seg=8)
    k.bx(0.38, 0.82, 0.08, 0.32, 0.55, 0.62, 'iron2')
    k.bx(0.42, 0.78, 0.1, 0.3, 0.62, 0.75, 'iron2')
    k.bx(0.15, 1.05, 0.04, 0.36, 0.75, 0.9, 'iron')
    k.hullp([(1.05, 0.04, 0.75), (1.05, 0.36, 0.75), (1.05, 0.04, 0.9), (1.05, 0.36, 0.9), (1.4, 0.2, 0.86)], 'iron')
    k.bx(0.3, 0.75, 0.16, 0.24, 0.9, 0.93, 'steel', ink=False)
    k.col(0.25, 0.95, -0.12, 0.52, 0.0, 0.9)
    # quench tub (half barrel of water) and a hammer, tongs on the anvil
    k.cyl(1.9, 1.6, 0.0, 0.42, 0.46, 0.62, 'plank2', seg=8)
    k.disc(1.9, 1.6, 0.624, 0.38, 'water2', n=8)
    k.col(1.45, 2.35, 1.15, 2.05, 0.0, 0.62)
    k.beam((0.35, 0.2, 0.94), (0.75, 0.15, 0.94), 0.04, 'log2')
    k.bx(0.3, 0.42, 0.13, 0.27, 0.93, 1.0, 'iron2')
    # tool rack on the back wall: hammers and tongs
    k.bx(-0.6, 2.8, y1 - 0.24, y1 - 0.2, 1.9, 1.98, 'plank2')
    for i in range(7):
        x = -0.4 + i * 0.48
        k.bx(x - 0.02, x + 0.02, y1 - 0.26, y1 - 0.22, 1.25, 1.95, 'iron2', ink=False)
        k.bx(x - 0.07, x + 0.07, y1 - 0.28, y1 - 0.2, 1.2, 1.32 if i % 2 else 1.28, 'iron', ink=False)
    # grindstone on its frame and iron stock leaning on the wall
    k.push(2.6, -1.6, 0, 0)
    for x in (-0.25, 0.25):
        k.bx(x - 0.04, x + 0.04, -0.4, 0.4, 0.0, 0.7, 'plank2')
    k.cyl(-0.15, 0.0, 0.85, 0.42, 0.42, 0.3, 'stone', seg=10, rot=(0, 90, 0))
    k.cyl(-0.3, 0.0, 0.85, 0.05, 0.05, 0.6, 'iron', seg=5, rot=(0, 90, 0))
    k.pop()
    k.col(2.25, 2.95, -2.05, -1.15, 0.0, 1.28)
    for i in range(6):
        k.beam((-3.75 + i * 0.09, -1.5, 0.0), (-3.82 + i * 0.09, -1.45, 1.6 + 0.08 * (i % 3)), 0.035, 'iron', ink=False)
    # wagon wheel leaning on the west wall
    k.push(-3.55, -2.2, 0, 0.0)
    k.cyl(0.05, 0.0, 0.62, 0.62, 0.62, 0.07, 'plank2', seg=12, rot=(0, 90 - 12, 0), caps=False)
    k.pop()
    sb = y0 + 0.02 - 0.04          # the name board hangs on the front beam's face
    k.bx(-1.1, 1.1, sb, sb + 0.04, H - 0.55, H + 0.2, 'plank2')
    k.text('SMITHY', 0.0, sb - 0.004, H - 0.42, 0.34, 'plankW', maxw=1.9, font='display')
    FD.smithy_detail(k, fx0, fx1, fy0, fy1, H, x0, x1, y0, y1)
    k.finish('Smithy', ao=ao)


def build_stable(k, ao):
    """STABLE [10, 6]: open-fronted timber shed with four empty stalls (plank partitions, hay, feed bins, a saddle
    rack), a shed roof sloping to the back."""
    rnd = random.Random(506)
    k.begin()
    x0, x1, y0, y1 = -5.0, 5.0, -3.0, 3.0
    H = 3.2
    wall(k, 'x', y1 - 0.1, x0, x1, 0.0, 2.6, 0.2, [], 'plankR', 'plank', top='plank2')
    for xx in (x0 + 0.1, x1 - 0.1):
        wall(k, 'y', xx, y0 + 0.3, y1 - 0.2, 0.0, 2.6, 0.2, [], 'plankR', 'plank', top='plank2')
    boards(k, 'x', y1, 1, x0 + 0.02, x1 - 0.02, 0.0, 2.6, 0.5, [], 'plank2')
    for (xx, s) in ((x0, -1), (x1, 1)):
        boards(k, 'y', xx, s, y0 + 0.3, y1 - 0.2, 0.0, 2.6, 0.5, [], 'plank2')
    for x in (-4.85, -2.5, 0.0, 2.5, 4.85):
        k.bx(x - 0.12, x + 0.12, y0 + 0.05, y0 + 0.29, 0.0, H, 'log2')
        k.col(x - 0.12, x + 0.12, y0 + 0.05, y0 + 0.29, 0.0, H)
    k.bx(x0, x1, y0 + 0.05, y0 + 0.29, H, H + 0.2, 'log2')
    shed_roof(k, x0 - 0.3, x1 + 0.3, y0 - 0.5, y1 + 0.35, H + 0.2, 2.75, 0.12, 'shingle', 'shingle2')
    # stall partitions (1.4 m), hay on the floor, feed bins and a saddle rack
    for x in (-2.5, 0.0, 2.5):
        k.bx(x - 0.04, x + 0.04, y0 + 1.0, y1 - 0.2, 0.0, 1.4, 'plank2')
        k.col(x - 0.05, x + 0.05, y0 + 1.0, y1 - 0.2, 0.0, 1.4)
    for i, x in enumerate((-3.75, -1.25, 1.25, 3.75)):
        k.disc(x, 0.9, 0.006, 0.9, 'hay', n=8, rnd=rnd, jag=0.18)
        k.bx(x - 0.5, x + 0.5, y1 - 0.75, y1 - 0.2, 0.0, 0.75, 'plank2')
        k.bx(x - 0.42, x + 0.42, y1 - 0.68, y1 - 0.27, 0.75, 0.78, 'hay', ink=False)
        k.col(x - 0.5, x + 0.5, y1 - 0.75, y1 - 0.2, 0.0, 0.78)
    FD.stable_detail(k, x0, x1, y0, y1, H)
    k.finish('Stable', ao=ao)


def build_houses(k, ao):
    build_store(k, ao)
    build_trading_post(k, ao)
    build_bunkhouse(k, ao)
    build_cabins(k, ao)
    build_smithy(k, ao)
    build_stable(k, ao)
