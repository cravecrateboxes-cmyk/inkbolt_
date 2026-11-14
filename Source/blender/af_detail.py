"""kit-airfield7 modelled detail (tactical look plan Stage 11): the fixings a real air base shows up close.

Hangar door guide rails, panel laps, personnel doors with frames and hinges; control tower window frames, rail feet,
service ladder, antenna base plates; transport panel lines, hatches, hubs, cowl rings; vehicle hubs, handles, mirrors,
hazard bands, fuel caps; barracks door hardware and window frames; runway light and sign base plates; T-wall sockets;
gate and barrier plates. Built on the PK model of af_base (boxes with hull='none': no outline shell).

Rules kept: every part is hull='none', stands at least 3 mm proud of what it sits on and starts 3 mm inside it,
horizontal runs stop 5 mm short of a piece's sides. Nothing here touches a collision box, a glow part, an origin or
a footprint.
"""
import math

from mathutils import Vector
from mathutils.bvhtree import BVHTree

from af_base import hazard, cyl_x, cyl_y, xdisc, vdisc, TOWER_DECK, GALLERY, HOLD

PROUD = 0.004
EMBED = 0.003


# ------------------------------------------------------------------------------------------------ primitives
def fbox(m, face, p, u0, u1, z0, z1, out, c, emb=EMBED, cull=''):
    """A box standing `out` proud of a face at plane p (face 'y-' looks toward -Y, 'y+', 'x+', 'x-'; u runs along the
    face), sunk `emb` into the wall; the face turned to the wall is never seen and is dropped."""
    u0, u1 = min(u0, u1), max(u0, u1)
    if z0 < 0.02:
        cull += 'b'
    if face == 'y-':
        return m.bx(u0, u1, p - out, p + emb, z0, z1, c, hull='none', cull='k' + cull)
    if face == 'y+':
        return m.bx(u0, u1, p - emb, p + out, z0, z1, c, hull='none', cull='f' + cull)
    if face == 'x+':
        return m.bx(p - emb, p + out, u0, u1, z0, z1, c, hull='none', cull='l' + cull)
    return m.bx(p - out, p + emb, u0, u1, z0, z1, c, hull='none', cull='r' + cull)


def rivets(m, face, p, u0, u1, z, every, c, s=0.022, out=0.01):
    n = max(2, int((u1 - u0) / every))
    for i in range(n):
        u = u0 + (u1 - u0) * (i + 0.5) / n
        fbox(m, face, p, u - s / 2, u + s / 2, z - s / 2, z + s / 2, out, c)


def rivets_v(m, face, p, u, z0, z1, every, c, s=0.022, out=0.01):
    n = max(2, int((z1 - z0) / every))
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        fbox(m, face, p, u - s / 2, u + s / 2, z - s / 2, z + s / 2, out, c)


def bolt4(m, face, p, u0, u1, z0, z1, c, inset=0.035, s=0.022, out=0.01):
    for u in (u0 + inset, u1 - inset):
        for z in (z0 + inset, z1 - inset):
            fbox(m, face, p, u - s / 2, u + s / 2, z - s / 2, z + s / 2, out, c)


def wframe(m, face, p, u0, u1, z0, z1, c='steelD', t=0.04, out=0.04, sill=None):
    """A frame standing out round a window: head, two jambs (4 mm gap under the head), an optional sill ledge."""
    fbox(m, face, p, u0 - t, u1 + t, z1, z1 + t, out, c)
    for u in ((u0 - t, u0), (u1, u1 + t)):
        fbox(m, face, p, u[0], u[1], z0 - 0.003, z1 - 0.004, out, c)
    if sill:
        fbox(m, face, p, u0 - 0.06, u1 + 0.06, z0 - 0.07, z0, out + 0.07, sill)


def dframe(m, face, p, u0, u1, z0, z1, c='steelD', t=0.06, out=0.04):
    """A door frame: two jambs and a head round a door leaf of u0..u1 x z0..z1."""
    fbox(m, face, p, u0 - t, u1 + t, z1, z1 + t, out, c)
    for u in ((u0 - t, u0), (u1, u1 + t)):
        fbox(m, face, p, u[0], u[1], z0, z1 - 0.004, out, c)


def hinges(m, face, p, u, zs, c='steelD', w=0.04, h=0.1, out=0.03):
    for z in zs:
        fbox(m, face, p, u - w / 2, u + w / 2, z - h / 2, z + h / 2, out, c)


def lever(m, face, p, u, z, c='steel', plate_c='steelD', length=0.16, out=0.05):
    """A door lever handle on a back plate."""
    fbox(m, face, p, u - 0.03, u + 0.03, z - 0.1, z + 0.1, 0.02, plate_c)
    fbox(m, face, p, u - length / 2, u + length / 2, z - 0.015, z + 0.015, out, c)


def hub(m, x, y, z, r, w, c='steelD', cap_c='steel', nuts=5):
    """Lug nuts and a centre cap on the outer face of a wheel turning about X (ap_base.wheel's hub disc)."""
    s = 1 if x >= 0 else -1
    xf = x + s * (w / 2 + 0.003)
    nr, ns = r * 0.32, max(0.022, r * 0.06)
    for i in range(nuts):
        a = 2 * math.pi * (i + 0.25) / nuts
        yy, zz = y + math.cos(a) * nr, z + math.sin(a) * nr
        a0, a1 = (xf - 0.003, xf + 0.014) if s > 0 else (xf - 0.014, xf + 0.003)
        m.bx(a0, a1, yy - ns / 2, yy + ns / 2, zz - ns / 2, zz + ns / 2, c, hull='none', cull='l' if s > 0 else 'r')
    a0, a1 = (xf - 0.006, xf + 0.02) if s > 0 else (xf - 0.02, xf + 0.006)
    cyl_x(m, a0, a1, y, z, r * 0.15, cap_c, seg=6, hull='none')


def beam(m, a, b, t, c):
    return m.bm_(a, b, t, c, hull='none')


def hazard_strip(m, x0, x1, y, z0, z1, n, face=-1):
    hazard(m, x0, x1, y, z0, z1, n, face=face)


# ================================================================ the maintenance hangar
def hangar(m, W, D, E, t):
    """Door guide rails (a top track under the header with trolleys, a floor rail in the opening), stiffeners, rivet
    rows and handles on the door leaves, corner guards, cladding laps with fixings, a plinth, personnel doors with
    frames and hinges, downpipes."""
    yf0 = -D
    # top track under the header, across the opening, with the hanger trolleys
    m.bx(-9.0 + 0.005, 9.0 - 0.005, yf0 + 0.04, yf0 + 0.17, E - 1.2 - 0.14, E - 1.2 + EMBED, 'steelD', hull='none', cull='t')
    for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
        m.bx(x - 0.12, x + 0.12, yf0 + 0.02, yf0 + 0.19, E - 1.2 - 0.2, E - 1.2 - 0.14 + EMBED, 'steel', hull='none', cull='t')
    # floor guide rail in the opening with its end stops
    m.bx(-9.0 + 0.005, 9.0 - 0.005, yf0 + 0.1, yf0 + 0.19, 0.0, 0.035, 'steelD', hull='none', cull='b')
    for s in (-1, 1):
        m.bx(*sorted((s * 8.9, s * 8.65)), yf0 + 0.08, yf0 + 0.21, 0.0, 0.08, 'steel', hull='none', cull='b')
    # door leaves: stiffeners, stile, rivets, handle (the leaf fronts are at y = ya)
    for s in (-1, 1):
        for k in range(2):
            xa, xb = sorted((s * (9.0 + 2.35 * k), s * (11.4 + 2.35 * k)))
            ya = yf0 + 0.05 + k * 0.32
            ux0, ux1 = (xa, xb) if k == 0 else ((xa + 0.05, xb) if s > 0 else (xa, xb - 0.05))
            for z in (2.2, 4.6):
                fbox(m, 'y-', ya, ux0 + 0.1, ux1 - 0.1, z - 0.05, z + 0.05, 0.014, 'steelD')
            rivets(m, 'y-', ya, ux0 + 0.15, ux1 - 0.15, 6.62, 0.6, 'steelD', s=0.02)
            rivets(m, 'y-', ya, ux0 + 0.15, ux1 - 0.15, 2.38, 0.8, 'steelD', s=0.02)
            if k == 0:
                u_in = xa if s > 0 else xb          # the leading edge toward the opening
                su = 1 if s > 0 else -1
                fbox(m, 'y-', ya, u_in + su * 0.02, u_in + su * 0.14, 0.45, 6.7, 0.019, 'steelD')
                lever(m, 'y-', ya, u_in + su * 0.3, 1.1, length=0.2)
    # header: a bolt row under the lettering, corner guards on the front corners
    rivets(m, 'y-', yf0, -W + 0.4, W - 0.4, E - 1.14, 0.9, 'steelD', s=0.022)
    for s in (-1, 1):
        a, b = sorted((s * (W - 0.08), s * (W - 0.005)))
        fbox(m, 'y-', yf0, a, b, 0.0, E - 0.01, 0.008, 'steelD')
    # side walls (exterior faces x = +-W): two cladding laps with fixings, a plinth, downpipes, personnel door
    for s in (-1, 1):
        face = 'x+' if s > 0 else 'x-'
        p = s * W
        for z in (2.7, 5.3):
            fbox(m, face, p, -D + 0.2, D - 0.25, z - 0.03, z + 0.03, 0.014, 'corrD')
            rivets(m, face, p, -D + 0.6, D - 0.6, z, 2.0, 'steelD', s=0.02, out=0.02)
        fbox(m, face, p, -D + 0.3, D - 0.3, 0.0, 0.3, 0.02, 'concD')
        for yy in (-D + 0.35, D - 0.35):
            cyl_x_pipe(m, s * (W + 0.07), yy, 0.1, E - 0.3, 0.045)
            for z in (1.2, 3.6, 6.0):
                fbox(m, face, p, yy - 0.035, yy + 0.035, z - 0.02, z + 0.02, 0.045, 'steel')
        # personnel door at y = -s * 6.5
        yc = -s * 6.5
        dframe(m, face, p, yc - 0.45, yc + 0.45, 0.0, 2.1, 'steelD', t=0.08, out=0.05)
        fbox(m, face, p, yc - 0.45, yc + 0.45, 0.0, 2.1, 0.03, 'od')
        for z in (0.9, 1.7):
            fbox(m, face, p, yc - 0.33, yc + 0.33, z - 0.28, z + 0.28, 0.04, 'odD')
        fbox(m, face, p, yc - 0.4, yc + 0.4, 0.02, 0.28, 0.045, 'steelD')
        hinges(m, face, p, yc - 0.42, (0.3, 1.0, 1.8), w=0.034, out=0.05)
        lever(m, face, p, yc + 0.33, 1.0, out=0.08)
        fbox(m, face, p, yc - 0.55, yc + 0.55, 0.0, 0.14, 0.5, 'concD')            # a step
        fbox(m, face, p, yc - 0.6, yc + 0.6, 2.2, 2.26, 0.65, 'steelD')            # a canopy
        for y in (yc - 0.5, yc + 0.5):
            beam(m, (p + s * 0.55, y, 2.22), (p - s * 0.01, y, 1.85), 0.04, 'steelD')
        fbox(m, face, p, yc - 0.12, yc + 0.12, 2.5, 2.74, 0.12, 'dark')            # a wall-pack lamp
        fbox(m, face, p, yc - 0.09, yc + 0.09, 2.53, 2.71, 0.13, 'lamp')


def cyl_x_pipe(m, x, y, z0, z1, r):
    m.cy((x, y, z0), r, r, z1 - z0, 'steelD', seg=6, hull='none')


# ================================================================ the control tower
def _rail_posts(x0, x1, posts=1.2, ends=True):
    n = max(1, int(round((x1 - x0) / posts)))
    rng = range(n + 1) if ends else range(1, n)
    return [x0 + (x1 - x0) * i / n for i in rng]


def tower(m):
    T = TOWER_DECK
    # window frames with depth (the sills of the window_y bands are already there)
    for (u0, u1, z0, z1) in ((-3.8, -0.4, 1.0, 2.5), (2.4, 5.6, 1.0, 2.5)):
        wframe(m, 'y-', -6.0, u0, u1, z0, z1)
    wframe(m, 'y+', 6.0, -3.6, 0.0, 1.1, 2.5)
    for (face, p, u0, u1) in (('x-', -4.2, -5.6, -0.4), ('x+', 6.0, -5.6, -1.0)):
        wframe(m, face, p, u0, u1, 1.1, 2.5, sill='concL')
    for z in (6.3, 8.3):
        wframe(m, 'y-', 0.4, 1.4, 4.8, z, z + 1.2)
        wframe(m, 'y+', 5.4, 1.4, 4.8, z, z + 1.2)
        wframe(m, 'x+', 5.6, 1.2, 4.6, z, z + 1.2, sill='concL')
        wframe(m, 'x-', 0.6, 1.2, 4.6, z, z + 1.2, sill='concL')
    # the ops door: frame, kick plates, push bars, hinges, bracketed canopy, a lamp
    dframe(m, 'y-', -6.0, 0.4, 1.8, 0.0, 2.3, 'steelD', t=0.08, out=0.05)
    for (a, b) in ((0.46, 1.04), (1.16, 1.74)):
        fbox(m, 'y-', -6.0, a, b, 0.02, 0.3, 0.025, 'steelD')
        fbox(m, 'y-', -6.0, a + 0.05, b - 0.05, 1.0, 1.04, 0.07, 'steel')
    hinges(m, 'y-', -6.0, 0.43, (0.3, 1.1, 1.9), out=0.04)
    hinges(m, 'y-', -6.0, 1.77, (0.3, 1.1, 1.9), out=0.04)
    for x in (0.2, 2.0):
        beam(m, (x, -5.99, 2.0), (x, -6.85, 2.48), 0.05, 'steelD')
    fbox(m, 'y-', -6.0, 2.0, 2.22, 2.1, 2.3, 0.12, 'dark')
    fbox(m, 'y-', -6.0, 2.03, 2.19, 2.13, 2.27, 0.13, 'lamp')
    # terrace rail feet
    def feet(x, y):
        m.bx(x - 0.045, x + 0.045, y - 0.045, y + 0.045, T - EMBED, T + 0.013, 'steelD', hull='none', cull='b')
    for x in _rail_posts(-4.15, 5.95):
        feet(x, -5.9)
    for y in _rail_posts(-5.9, 3.5, ends=False):
        feet(-4.1, y)
    for y in _rail_posts(-5.9, 0.35, ends=False):
        feet(5.9, y)
    for y in _rail_posts(3.6, 5.9, ends=False):
        feet(-5.9, y)
    for x in _rail_posts(-5.9, 0.55):
        feet(x, 5.9)
    # terrace AC units: louvres on the south faces, feet
    for (x0, x1, y, z1) in ((-3.4, -2.0, -2.0, T + 0.9), (3.0, 4.6, -4.6, T + 0.95)):
        for i in range(5):
            z = T + 0.2 + i * 0.12
            fbox(m, 'y-', y, x0 + 0.1, x1 - 0.1, z, z + 0.04, 0.014, 'steelD')
        fbox(m, 'y-', y, x0 + 0.04, x1 - 0.04, T, T + 0.08, 0.016, 'steelD')
    # the service ladder up the shaft's east face, with stand-offs
    px = 5.6
    for y in (4.78, 5.22):
        fbox(m, 'x+', px, y - 0.02, y + 0.02, T + 0.15, 9.7, 0.07, 'yellow')
    n = int((9.6 - (T + 0.3)) / 0.4)
    for i in range(n + 1):
        z = T + 0.3 + i * 0.4
        m.bx(px + 0.04, px + 0.06, 4.79, 5.21, z - 0.015, z + 0.015, 'steel', hull='none')
    for z in (6.0, 8.2, 9.4):
        for y in (4.78, 5.22):
            fbox(m, 'x+', px, y - 0.015, y + 0.015, z - 0.03, z + 0.03, 0.09, 'steelD')
    # antenna base plate with gussets and the radar pedestal ring
    z0 = 13.5
    cx, cy = 3.9, 3.7
    m.bx(cx - 0.2, cx + 0.2, cy - 0.2, cy + 0.2, z0 - EMBED, z0 + 0.025, 'steelD', hull='none', cull='b')
    for dx in (-1, 1):
        for dy in (-1, 1):
            m.bx(cx + dx * 0.15 - 0.018, cx + dx * 0.15 + 0.018, cy + dy * 0.15 - 0.018, cy + dy * 0.15 + 0.018, z0 + 0.02, z0 + 0.055, 'steel', hull='none', cull='b')
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        beam(m, (cx + dx * 0.19, cy + dy * 0.19, z0 + 0.03), (cx + dx * 0.07, cy + dy * 0.07, z0 + 0.5), 0.03, 'steelD')
    px_, py_ = 2.2, 2.3
    m.bx(px_ - 0.32, px_ + 0.32, py_ - 0.32, py_ + 0.32, z0 - EMBED, z0 + 0.03, 'steelD', hull='none', cull='b')
    for dx in (-1, 1):
        for dy in (-1, 1):
            m.bx(px_ + dx * 0.27 - 0.02, px_ + dx * 0.27 + 0.02, py_ + dy * 0.27 - 0.02, py_ + dy * 0.27 + 0.02, z0 + 0.025, z0 + 0.065, 'steel', hull='none', cull='b')


# ================================================================ the transport
def _probe(bvh, s, y, z):
    hit = bvh.ray_cast(Vector((s * 3.0, y, z)), Vector((-s, 0.0, 0.0)))
    if hit[0] is None or not 1.5 < abs(hit[0].x) < 2.2:
        return None
    return hit[0].x


def _surf_beam(m, bvh, s, pts, t=0.022, c='odD', lift=0.007):
    """A beam following the fuselage surface through the (y, z) points, 7 mm off it; neighbouring segments overlap a
    little and alternate 4 mm in height, so their faces never share a plane."""
    q = []
    for (y, z) in pts:
        x = _probe(bvh, s, y, z)
        if x is None:
            return
        q.append((x, y, z))
    for k, (a, b) in enumerate(zip(q, q[1:])):
        lf = lift + (0.002 if k % 2 else 0.0)
        va, vb = Vector((a[0] + s * lf, a[1], a[2])), Vector((b[0] + s * lf, b[1], b[2]))
        d = (vb - va).normalized() * 0.011
        beam(m, tuple(va - d), tuple(vb + d), t + (0.01 if k % 2 else 0.0), c)


def transport(m, TA, HOLD0, HOLD1):
    bvh = BVHTree.FromBMesh(m.bm)
    for s in (-1, 1):
        # frame lines on the fuselage side (clear of the portholes, roundel and lettering)
        for y in (-4.2, -2.2, 0.2, 2.6, 5.0):
            _surf_beam(m, bvh, s, [(y, 2.3 + 0.6 * i) for i in range(4)], c='odD')
        # long skin laps
        lines = (-4.2, -2.2, 0.2, 2.6, 5.0)
        edges = [-4.6] + [v for y in lines for v in (y - 0.03, y + 0.03)] + [8.0]
        for z in (2.3, 3.95):
            for a, b in zip(edges[0::2], edges[1::2]):
                _surf_beam(m, bvh, s, [(a, z), (b, z)], t=0.02, c='odD')
        # access hatch on the forward fuselage side and the cargo door frame behind
        zs = [(1.9, -8.6), (3.05, -8.6)]
        # (a hatch frame: four beams on the surface)
        hz0, hz1, hy0, hy1 = 1.95, 2.55, -4.9 + 0.0, -4.4
        _surf_beam(m, bvh, s, [(hy0, hz0), (hy0, hz1)], t=0.018, c='steelD')
        _surf_beam(m, bvh, s, [(hy1, hz0), (hy1, hz1)], t=0.018, c='steelD')
        _surf_beam(m, bvh, s, [(hy0 + 0.02, hz0), (hy1 - 0.02, hz0)], t=0.026, c='steelD')
        _surf_beam(m, bvh, s, [(hy0 + 0.02, hz1), (hy1 - 0.02, hz1)], t=0.026, c='steelD')
        del zs
        # sponson wheels: hubs; nose wheels too
        for y in (-1.2, 1.8):
            hub(m, s * 2.25, y, 0.55, 0.55, 0.35)
        hub(m, s * 0.22, -10.0, 0.4, 0.4, 0.22, nuts=4)
    # nacelle cowl rings with a row of fasteners, front gear brace
    for s in (-1, 1):
        for xe in (5.0, 9.8):
            x = s * xe
            cyl_y(m, x, -4.46, -4.4, 4.1, 0.7, 'steelD', seg=8, hull='none', caps=True)
            cyl_y(m, x, -2.04, -1.98, 4.15, 0.76, 'steelD', seg=8, hull='none', caps=True)
    # wing underside: chord seams and flap lines (the underside plate is at z = 4.55)
    for s in (-1, 1):
        for xe in (3.0, 7.4, 12.0, 14.0):
            x = s * xe
            yle = -2.4 + 1.6 * xe / 15.0 + 0.15
            yte = 1.8 - 0.8 * xe / 15.0 - 0.15
            m.bx(x - 0.015, x + 0.015, yle, yte, 4.538, 4.553, 'steelD', hull='none', cull='t')
        for (xa, xb) in ((2.45, 4.2), (5.8, 9.0), (10.6, 14.6)):
            m.bx(*sorted((s * xa, s * xb)), 0.82, 0.86, 4.533, 4.553, 'steelD', hull='none', cull='t')
    # cargo floor tie-down fittings along the roller tracks
    for x in (-0.9, 0.9):
        for i in range(6):
            y = HOLD0 + 0.6 + i * 1.5
            m.bx(x - 0.045, x + 0.045, y - 0.05, y + 0.05, HOLD + 0.0, HOLD + 0.03, 'steel', hull='none', cull='b')
    # ramp hinge plates and lip
    m.bx(-1.42 + 0.005, 1.42 - 0.005, HOLD1 - 0.02, HOLD1 + 0.12, HOLD - 0.01, HOLD + 0.012, 'steelD', hull='none', cull='b')


# ================================================================ vehicles
def bowser(m):
    for x in (-1.12, 1.12):
        for y in (-3.0, 1.0, 2.4):
            hub(m, x, y, 0.55, 0.55, 0.32)
    for s in (-1, 1):
        face = 'x+' if s > 0 else 'x-'
        p = s * 1.25
        # cab door outline, handle, mirror
        fbox(m, face, p, -3.74, -3.72, 1.1, 2.76, 0.016, 'odD')
        fbox(m, face, p, -2.58, -2.56, 1.1, 2.76, 0.016, 'odD')
        fbox(m, face, p, -3.72, -2.58, 2.74, 2.76, 0.016, 'odD')
        fbox(m, face, p, -3.72, -2.58, 1.1, 1.12, 0.016, 'odD')
        lever(m, face, p, -2.75, 1.85, out=0.04, length=0.14)
        a0, a1 = (p - 0.003, p + 0.3) if s > 0 else (p - 0.3, p + 0.003)
        m.bx(a0, a1, -3.9, -3.86, 2.5, 2.54, 'dark', hull='none', cull='l' if s > 0 else 'r')
        c0, c1 = (p + 0.27, p + 0.36) if s > 0 else (p - 0.36, p - 0.27)
        m.bx(c0, c1, -3.95, -3.79, 2.36, 2.7, 'black', hull='none')
        # chassis: a fuel cap on its side
        cyl_x(m, *sorted((s * 1.1 - s * 0.006, s * 1.1 + s * 0.045)), -1.5, 0.78, 0.085, 'steel', seg=8, hull='none')
        cyl_x(m, *sorted((s * 1.1 - s * 0.009, s * 1.1 + s * 0.02)), -1.5, 0.78, 0.115, 'redD', seg=8, hull='none')
    # manhole lids: bolts, hinge lugs
    for y in (-0.6, 1.6):
        for i in range(6):
            a = 2 * math.pi * (i + 0.5) / 6
            bx_, by_ = math.cos(a) * 0.2, y + math.sin(a) * 0.2
            m.bx(bx_ - 0.018, bx_ + 0.018, by_ - 0.018, by_ + 0.018, 3.045, 3.07, 'steel', hull='none', cull='b')
        m.bx(-0.1, 0.1, y + 0.27, y + 0.35, 2.9, 2.99, 'steelD', hull='none', cull='b')
    # bumper hazard bands, rear bumper bar
    hazard_strip(m, -1.25, 1.25, -4.056, 0.73, 1.0, 7)
    m.bx(-1.15, 1.15, 3.93, 4.04, 0.62, 0.86, 'steelD', hull='none', cull='f' + 'b')
    hazard_strip(m, -1.1, 1.1, 4.044, 0.64, 0.84, 8, face=1)
    for x in (-0.6, 0.6):
        m.bx(x - 0.05, x + 0.05, 4.044, 4.07, 0.9, 0.96, 'lampR', hull='none', cull='f' + 'b')


def tender(m):
    for x in (-1.2, 1.2):
        for y in (-3.4, 1.6, 3.3):
            hub(m, x, y, 0.6, 0.6, 0.36, nuts=6)
    for s in (-1, 1):
        face = 'x+' if s > 0 else 'x-'
        p = s * 1.4
        # locker shutters: frames, bottom pull bars
        for (ya, yb) in ((-2.3, -0.4), (-0.2, 1.7), (1.9, 3.8)):
            fbox(m, face, p, ya, yb, 1.73, 1.77, 0.016, 'steelD')
            fbox(m, face, p, ya, yb, 2.7, 2.74, 0.016, 'steelD')
            fbox(m, face, p, ya - 0.02, ya + 0.02, 1.774, 2.696, 0.016, 'steelD')
            fbox(m, face, p, yb - 0.02, yb + 0.02, 1.774, 2.696, 0.016, 'steelD')
            fbox(m, face, p, (ya + yb) / 2 - 0.12, (ya + yb) / 2 + 0.12, 1.79, 1.83, 0.04, 'steel')
        # cab door outline and handle, mirror
        fbox(m, face, p, -4.62, -4.6, 1.1, 2.9, 0.018, 'black')
        fbox(m, face, p, -2.92, -2.9, 1.1, 2.9, 0.018, 'black')
        lever(m, face, p, -3.1, 1.8, out=0.04, length=0.14)
        a0, a1 = (p - 0.003, p + 0.32) if s > 0 else (p - 0.32, p + 0.003)
        m.bx(a0, a1, -4.7, -4.66, 2.45, 2.49, 'dark', hull='none', cull='l' if s > 0 else 'r')
        c0, c1 = (p + 0.29, p + 0.38) if s > 0 else (p - 0.38, p - 0.29)
        m.bx(c0, c1, -4.75, -4.59, 2.3, 2.66, 'black', hull='none')
        # a fuel cap behind the cab
        cyl_x(m, *sorted((p - s * 0.006, p + s * 0.05)), -2.45, 1.15, 0.085, 'steel', seg=8, hull='none')
        cyl_x(m, *sorted((p - s * 0.009, p + s * 0.02)), -2.45, 1.15, 0.115, 'redD', seg=8, hull='none')
    hazard_strip(m, -1.45, 1.45, -5.006, 0.6, 0.95, 8)
    # rear: a step and grab handles
    for x in (-0.6, 0.6):
        m.bx(x - 0.02, x + 0.02, 4.85, 4.95, 1.2, 2.5, 'yellow', hull='none', cull='f')
    m.bx(-0.7, 0.7, 4.85, 5.0, 0.58, 0.64, 'steelD', hull='none', cull='f' + 'b')


def caravan(m, X, Y0, Y1, Z0, Z1):
    for x in (-1.0, 1.0):
        for y in (-0.9, 0.9):
            hub(m, x, y, 0.4, 0.4, 0.24, nuts=5)
    # door on the west face: frame, hinges, handle, kick plate, grab rails
    p = -X
    dframe(m, 'x-', p, -0.4, 0.4, Z0 + 0.05, Z1 - 0.25, 'steelD', t=0.05, out=0.04)
    hinges(m, 'x-', p, -0.37, (Z0 + 0.3, Z0 + 1.0, Z0 + 1.7), h=0.09, out=0.035)
    lever(m, 'x-', p, 0.27, Z0 + 0.95, out=0.06, length=0.14)
    fbox(m, 'x-', p, -0.38, 0.38, Z0 + 0.06, Z0 + 0.28, 0.02, 'steelD')
    for y in (-0.62, 0.62):
        fbox(m, 'x-', p, y - 0.02, y + 0.02, Z0 + 0.3, Z0 + 1.3, 0.09, 'steel')
    # corner guards, roof edge trim
    for (xc, sx) in ((-X, 1), (X, -1)):
        for (yc, sy) in ((Y0, 1), (Y1, -1)):
            a, b = sorted((xc + sx * 0.005, xc + sx * 0.07))
            m.bx(a, b, yc - 0.012 if yc == Y0 else yc - 0.005, yc + 0.005 if yc == Y0 else yc + 0.012, Z0 + 0.02, Z1 - 0.01, 'steelD', hull='none')
    # drawbar coupler with a safety chain lug
    cyl_y(m, 0.0, Y0 - 0.58, Y0 - 0.44, 0.47, 0.085, 'steel', seg=8, hull='none')
    m.bx(-0.03, 0.03, Y0 - 0.62, Y0 - 0.44, 0.58, 0.62, 'steelD', hull='none', cull='b')


def tug(m):
    for x in (-0.72, 0.72):
        for y in (-0.85, 0.85):
            hub(m, x, y, 0.33, 0.33, 0.24, nuts=5)
    # fuel cap on the bonnet, beacon base plate, hitch pin, rear lamps, hazard bar
    m.cy((0.4, -0.9, 0.85 - EMBED), 0.065, 0.065, 0.03, 'steel', seg=8, hull='none')
    m.cy((0.4, -0.9, 0.85 - 0.006), 0.09, 0.09, 0.012 + 0.003, 'redD', seg=8, hull='none')
    m.bx(-0.6 - 0.07, -0.6 + 0.07, 1.1 - 0.07, 1.1 + 0.07, 0.85 - EMBED, 0.865, 'steelD', hull='none', cull='b')
    m.cy((0.0, 1.45, 0.45 - EMBED), 0.03, 0.03, 0.12, 'steel', seg=6, hull='none')
    for x in (-0.55, 0.55):
        m.bx(x - 0.07, x + 0.07, 1.35 - EMBED, 1.38, 0.62, 0.74, 'lampR', hull='none', cull='f' + 'b' if False else 'k')
    m.bx(-0.75, 0.75, 1.35 - EMBED, 1.39, 0.31, 0.5, 'black', hull='none', cull='k')
    hazard_strip(m, -0.7, 0.7, 1.394, 0.32, 0.48, 6, face=1)
    # side rubbing strips and a grab handle
    for s in (-1, 1):
        face = 'x+' if s > 0 else 'x-'
        fbox(m, face, s * 0.8, -1.2, 1.2, 0.78, 0.83, 0.014, 'black')
        fbox(m, face, s * 0.8, -0.95, -0.9, 0.5, 0.8, 0.05, 'steelD')


def gpu(m):
    for (x, y) in ((-0.55, -0.6), (0.55, -0.6), (-0.55, 0.6), (0.55, 0.6)):
        hub(m, x, y, 0.22, 0.22, 0.12, nuts=4)
    # front panel frame, screws, gauges
    p = -0.85
    for (u0, u1, z0, z1) in ((-0.52, 0.52, 1.1, 1.13), (-0.52, 0.52, 0.57, 0.6), (-0.52, -0.5, 0.604, 1.096), (0.5, 0.52, 0.604, 1.096)):
        fbox(m, 'y-', p, u0, u1, z0, z1, 0.014, 'steelD')
    for x in (-0.28, 0.28):
        vdisc(m, x, p - 0.012, 1.0, 0.065, 'white2', seg=10)
    # lifting eye on top, louvre frames on the +X side
    m.bx(-0.2, 0.2, -0.04, 0.04, 1.3 - EMBED, 1.345, 'steelD', hull='none', cull='b')
    m.bx(-0.04, 0.04, -0.04, 0.04, 1.345, 1.42, 'steel', hull='none', cull='b')
    fbox(m, 'x+', 0.65, -0.66, -0.62, 0.55, 1.15, 0.016, 'steelD')
    fbox(m, 'x+', 0.65, 0.58, 0.62, 0.55, 1.15, 0.016, 'steelD')


def trailer(m):
    for x in (-0.78, 0.78):
        for y in (-1.0, 1.0):
            hub(m, x, y, 0.32, 0.32, 0.2, nuts=4)
    # webbing straps with ratchets over the bombs, bed edge cleats and reflectors
    for (x, z, r) in ((-0.5, 1.07, 0.27), (0.5, 1.07, 0.27), (0.0, 1.55, 0.25)):
        for y in (-0.2, 0.7):
            cyl_y(m, x, y, y + 0.05, z, r + 0.012, 'webbing', seg=8, hull='none')
            m.bx(x - 0.03, x + 0.03, y - 0.005, y + 0.055, z + r + 0.003, z + r + 0.04, 'steel', hull='none', cull='b')
    for y in (-1.4, -0.5, 0.5, 1.4):
        for s in (-1, 1):
            fbox(m, 'x+' if s > 0 else 'x-', s * 0.85, y - 0.05, y + 0.05, 0.58, 0.66, 0.03, 'steelD')
    for x in (-0.7, 0.7):
        fbox(m, 'y-', -1.7, x - 0.07, x + 0.07, 0.57, 0.64, 0.014, 'orange')
        fbox(m, 'y+', 1.7, x - 0.07, x + 0.07, 0.57, 0.64, 0.014, 'lampR')
    cyl_y(m, 0.0, -2.56, -2.42, 0.47, 0.08, 'steel', seg=8, hull='none')


# ================================================================ barracks
def barracks(m, G):
    for k in range(5):
        x = -8.8 + k * 4.4
        for z0 in (0.0, G):
            p = -1.5
            wframe(m, 'y-', p, x + 0.2, x + 1.6, z0 + 0.95, z0 + 2.1)
            dframe(m, 'y-', p, x - 1.25, x - 0.35, z0, z0 + 2.15, 'steelD', t=0.06, out=0.04)
            hinges(m, 'y-', p, x - 1.22, (z0 + 0.3, z0 + 1.8), h=0.09, out=0.03)
            lever(m, 'y-', p, x - 0.5, z0 + 1.0, out=0.06, length=0.14)
    # roof coping on the parapet front, downpipes at the front corners
    for xx in (-10.9, 10.9):
        m.cy((xx, -1.58, 0.1), 0.04, 0.04, 6.1, 'steelD', seg=6, hull='none')
        for z in (1.0, 3.2, 5.4):
            m.bx(xx - 0.03, xx + 0.03, -1.6, -1.5 + EMBED, z - 0.02, z + 0.02, 'steel', hull='none', cull='k')


# ================================================================ T-walls, barriers, gate
def twall(m, W_H, cap):
    # lifting sockets on the inside face, tie-down plates, loop base plates on the cap
    for x in (-0.33, 0.33):
        fbox(m, 'y-', -0.5, x - 0.06, x + 0.06, 3.25, 3.33, 0.012, 'dark')
    for x in (-0.3, 0.3):
        fbox(m, 'y-', -0.5, x - 0.08, x + 0.08, 0.28, 0.34, 0.012, 'steelD')
    if cap:
        for x in (-0.25, 0.25):
            m.bx(x - 0.1, x + 0.1, -0.4, -0.3, W_H - EMBED, W_H + 0.012, 'steel', hull='none', cull='b')


def twall_sign(m):
    for (u0, u1, z0, z1) in ((-0.415, 0.415, 2.225, 2.245), (-0.415, 0.415, 1.355, 1.375)):
        fbox(m, 'y-', -0.53, u0, u1, z0, z1, 0.008, 'steelD')
    for x in (-0.38, 0.38):
        for z in (1.41, 2.19):
            fbox(m, 'y-', -0.53, x - 0.012, x + 0.012, z - 0.012, z + 0.012, 0.012, 'steel')


def twall_light(m):
    for z in (1.6, 2.4, 3.2):
        fbox(m, 'y-', -0.535, -0.04, 0.04, z - 0.02, z + 0.02, 0.03, 'steel')


def barriers(m, BAR_H):
    for x in (-0.35, 0.35):
        m.bx(x - 0.09, x + 0.09, -0.32, -0.13, BAR_H - EMBED, BAR_H + 0.012, 'steel', hull='none', cull='b')
        for dx in (-1, 1):
            for dy in (-0.27, -0.18):
                m.bx(x + dx * 0.06 - 0.012, x + dx * 0.06 + 0.012, dy - 0.012, dy + 0.012, BAR_H + 0.01, BAR_H + 0.03, 'steelD', hull='none', cull='b')
    for x in (-0.3, 0.3):
        fbox(m, 'y-', -0.5, x - 0.07, x + 0.07, 0.24, 0.3, 0.012, 'dark')
        fbox(m, 'y-', -0.5, x - 0.06, x + 0.06, 0.95, 0.99, 0.012, 'steelD')
    for x in (-0.12, 0.12):
        fbox(m, 'y-', -0.3, x - 0.03, x + 0.03, BAR_H + 0.18, BAR_H + 0.24, 0.016, 'white2')


def gate_frame(m):
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.55, s * 2.5))
        a, b = x0 + 0.03, x1 - 0.03
        for (face, p) in (('y-', -0.5), ('y+', 0.5)):
            fbox(m, face, p, a, b, 0.0, 0.3, 0.014, 'steelD')
            for xx in (a + 0.06, b - 0.06):
                for z in (0.08, 0.22):
                    fbox(m, face, p, xx - 0.016, xx + 0.016, z - 0.016, z + 0.016, 0.024, 'steel')
            # vertical corner guards on the pylon corners
            ce = x0 + 0.005 if s > 0 else x1 - 0.005
        # beacon collar
        m.cy((s * 2.0, 0.0, 4.75 - EMBED), 0.16, 0.16, 0.03, 'steelD', seg=8, hull='none')
    # beam: rivet rows, end gussets
    for (face, p) in (('y-', -0.38), ('y+', 0.38)):
        rivets(m, face, p, -1.4, 1.4, 4.17, 0.3, 'steelD', s=0.022, out=0.01)
        for s in (-1, 1):
            u0, u1 = sorted((s * 1.2, s * 1.495))
            fbox(m, face, p, u0, u1, 3.55, 4.1, 0.012, 'steelD')
            bolt4(m, face, p, u0, u1, 3.55, 4.1, 'steel', inset=0.05, s=0.024, out=0.022)


# ================================================================ lights, signs, mast, windsock
def light_base(m):
    for dx in (-1, 1):
        for dy in (-1, 1):
            m.bx(dx * 0.12 - 0.018, dx * 0.12 + 0.018, dy * 0.12 - 0.018, dy * 0.12 + 0.018, 0.03 - EMBED, 0.058, 'steelD', hull='none', cull='b')
    m.cy((0.0, 0.0, 0.1), 0.098, 0.098, 0.022, 'steel', seg=6, hull='none')      # the frangible coupling
    m.bx(0.07, 0.15, -0.035, 0.035, 0.03 - EMBED, 0.085, 'dark', hull='none', cull='b')   # cable gland box


def sign_detail(m):
    # aluminium rim over the dark margin, mounting bolts, frangible couplings, base bolts
    for (y, face) in ((-0.18, -1), (0.18, 1)):
        yy = y + face * 0.0
        for (x0, x1, z0, z1) in ((-0.945, 0.945, 1.1, 1.145), (-0.945, 0.945, 0.355, 0.4), (-0.945, -0.9, 0.4, 1.1), (0.9, 0.945, 0.4, 1.1)):
            if face < 0:
                m.bx(x0, x1, yy - 0.01, yy + EMBED, z0, z1, 'steel', hull='none', cull='k' + ('' if z0 > 0.02 else 'b'))
            else:
                m.bx(x0, x1, yy - EMBED, yy + 0.01, z0, z1, 'steel', hull='none', cull='f')
    for x in (-0.7, 0.7):
        m.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.2, 0.235, 'steel', hull='none')
        for dx in (-1, 1):
            for dy in (-1, 1):
                m.bx(x + dx * 0.09 - 0.014, x + dx * 0.09 + 0.014, dy * 0.09 - 0.014, dy * 0.09 + 0.014, 0.05 - EMBED, 0.075, 'steel', hull='none', cull='b')


def mast_detail(m):
    # base plate with anchor nuts, climbing steps up the mast on the +Y side, visors and lens frames
    m.bx(-0.26, 0.26, -0.26, 0.26, 0.25 - EMBED, 0.265, 'steelD', hull='none', cull='b')
    for dx in (-1, 1):
        for dy in (-1, 1):
            m.bx(dx * 0.21 - 0.022, dx * 0.21 + 0.022, dy * 0.21 - 0.022, dy * 0.21 + 0.022, 0.26, 0.31, 'steel', hull='none', cull='b')
    n = 17
    for i in range(n):
        z = 1.9 + i * 0.33
        r = 0.12 - (z - 0.25) / 7.75 * 0.04
        m.bx(-0.07, 0.07, r * 0.8, r + 0.1, z - 0.014, z + 0.014, 'steel', hull='none')
    for x in (-0.45, 0.45):
        m.bx(x - 0.26, x + 0.26, -0.46, -0.105, 7.95 - EMBED, 7.985, 'steelD', hull='none', cull='b')
        for (a, b, z0, z1) in ((-0.22, 0.22, 7.9, 7.92), (-0.22, 0.22, 7.48, 7.5)):
            fbox(m, 'y-', -0.42, x + a, x + b, z0, z1, 0.012, 'steelD')


def windsock_base(m):
    for dx in (-1, 1):
        for dy in (-1, 1):
            m.bx(dx * 0.27 - 0.025, dx * 0.27 + 0.025, dy * 0.27 - 0.025, dy * 0.27 + 0.025, 0.15 - EMBED, 0.2, 'steel', hull='none', cull='b')
    m.cy((0.0, 0.0, 0.15 - EMBED), 0.11, 0.11, 0.05, 'steelD', seg=6, hull='none')
