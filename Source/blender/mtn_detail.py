"""kit-mountains modelled detail (tactical look plan Stage 11): timber battens, iron fixings, door hardware, window
reveals, fascias, snow-guard rails and sign plates on the pieces the player sees most. Every part is ink=False (no
outline shell), >= 3 mm proud, embedded 3 mm, runs inset 5 mm from the piece sides. The mountains builders use a bare
Model, so `det(m)` wraps it in a Kit whose flat set `finish` splits off into a hull-less mesh.
Faces facing Blender -Y use the kit_base helpers at plane y = yf; for other faces `k.push(x, y, deg)` first."""
import math

from kit_base import (PROUD, EMBED, Kit, bolt_row, kick_plate, base_trim, drip_edge, sign_plate, window_frame_depth)


def det(m):
    """a Kit view over the bare Model m (its detail shapes land in m.flat)"""
    k = Kit(m.pal, '', 0.02)
    k.m = m
    m.flat = k.flat = getattr(m, 'flat', set())
    k.stack = []
    return k


def hline(k, x0, x1, z, yf, c, t=0.012, d=0.006):
    k.bx(x0 + 0.005, x1 - 0.005, yf - d, yf + EMBED, z - t / 2, z + t / 2, c, ink=False)


def vline(k, x, z0, z1, yf, c, t=0.012, d=0.006):
    k.bx(x - t / 2, x + t / 2, yf - d, yf + EMBED, z0, z1, c, ink=False)


def door_leaf(k, x0, x1, z0, z1, yf, c='gunmetal', plank='log2', boards=4, kick=0.16, straps=(0.28, 0.7)):
    """a plank door: board joints, two strap hinges with bolts, a kick plate; yf = the leaf's -Y face"""
    n = boards
    for i in range(1, n):
        x = x0 + (x1 - x0) * i / n
        k.bx(x - 0.007, x + 0.007, yf - 0.005, yf + 0.006, z0 + kick + 0.01, z1 - 0.05, plank, ink=False)
    for f in straps:
        z = z0 + (z1 - z0) * f
        k.bx(x0 + 0.005, x1 - 0.12, yf - 0.011, yf + EMBED, z - 0.04, z + 0.04, c, ink=False)
        bolt_row(k, x0 + 0.05, x1 - 0.14, z, yf - 0.011, 3, c, s=0.03)
    kick_plate(k, x0 + 0.01, x1 - 0.01, yf, c, h=kick, z0=z0)


def sill(k, x0, x1, z, yf, c='log2', d=0.07, t=0.035):
    k.bx(x0, x1, yf - d, yf + EMBED, z - t, z, c, ink=False)


def snow_guard(k, yedge, zsnow, slope, x0, x1, back=False, rows=(0.35, 0.8), c='gunmetal', post_every=0.85):
    """pipe-style snow-guard rails on a roof slope; (yedge, zsnow) = the snow top at the eave line"""
    th = math.atan(slope)
    sg = -1 if back else 1                 # the front slope rises toward +y, the back one toward -y
    s, cth = math.sin(th), math.cos(th)
    rot = (sg * math.degrees(th), 0, 0)
    for r in rows:
        y = yedge + sg * r * cth
        z = zsnow + r * s
        k.bxr(0.5 * (x0 + x1), y - sg * s * 0.005, z + cth * 0.005, x1 - x0, 0.032, 0.05, c, rot=rot, ink=False)
        cnt = max(2, int((x1 - x0) / post_every) + 1)
        for i in range(cnt):
            x = x0 + 0.05 + (x1 - x0 - 0.1) * i / (cnt - 1)
            k.bxr(x, y + sg * s * 0.07, z - cth * 0.07, 0.03, 0.022, 0.13, c, rot=rot, ink=False)


def fascia(k, x0, x1, yf, z0, z1, c="log2", lip=None, d=0.028):
    """a fascia board over a roof-edge face at plane yf (+ an optional dark drip lip under it)"""
    k.bx(x0 + 0.005, x1 - 0.005, yf - d, yf + EMBED, z0, z1, c, ink=False)
    if lip:
        k.bx(x0 + 0.012, x1 - 0.012, yf - d - 0.012, yf + EMBED + 0.004, z0 - 0.03, z0 + 0.004, lip, ink=False)
