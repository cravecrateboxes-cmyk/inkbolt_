"""kit-seabase research ring: the glass observation chamber [12, 25] (a half-round glass room bulging from the hull
into the seabed: sill, mullions, a quarter-ellipsoid glass dome, the curved bench, the observation console and the
deep-sea camera; the seabed outside with rocks, a cable and an instrument lander as its own part), the hub's glass
dome [17, 17] (the ceiling plate round the oculus, ribs, rings; glass as a companion), the hub's survey table [9, 9]
(a turning holographic seabed relief over the table, four console desks), sample tanks, tank banks, lab benches,
core racks, sonar desks, comms racks, workstations, chairs and sample fridges (see sb_base.py for conventions)."""
import math
import random

from sb_base import *  # noqa: F401,F403
import sb_base as B
from kit_util import hull_pts
from fam_kit_bedroom import normals_up

# ================================================================ observation chamber [12, 25]
OR = 9.5          # glass radius (the D's centre is on the hull line, local x = 6)
OZ = 3.0          # eave (top of the glass wall)
OH = 4.0          # dome rise over the eave
OCX = 6.0
NA = 19           # mullions every 10 degrees


def oang(i, n=NA):
    return math.radians(-90 + 180 * i / (n - 1))


def opt(a, r, z):
    """a point at angle a (0 = straight out, west; +90 = north along the hull) and radius r from the D's centre"""
    return (OCX - r * math.cos(a), r * math.sin(a), z)


def dome(a, phi, r=OR):
    return opt(a, r * math.cos(phi), OZ + OH * math.sin(phi))


PHIS = [math.radians(d) for d in (0, 28, 54, 76, 90)]


def build_chamber(pal, ao):
    m = new(pal)
    # floor: a dark plate disc with radial seams and a teal ring near the glass (painted, 1 cm up)
    zf = 0.012
    poly(m, [(OCX, -(OR - 1.3), zf)] + [opt(oang(i), OR - 1.3, zf) for i in range(NA)] + [(OCX, OR - 1.3, zf)], 'plate', (0, 0, 1))
    for i in range(NA - 1):
        a0, a1 = oang(i), oang(i + 1)
        poly(m, [opt(a0, OR - 1.3, zf), opt(a0, OR - 1.05, zf), opt(a1, OR - 1.05, zf), opt(a1, OR - 1.3, zf)], 'tealM', (0, 0, 1))
        poly(m, [opt(a0, OR - 1.05, zf), opt(a0, OR - 0.15, zf), opt(a1, OR - 0.15, zf), opt(a1, OR - 1.05, zf)], 'grate', (0, 0, 1))
    for i in range(1, NA - 1, 3):
        a = oang(i)
        p0, p1 = opt(a, 1.2, zf + 0.003), opt(a, OR - 1.3, zf + 0.003)
        dx, dy = -math.sin(a) * 0.03, -math.cos(a) * 0.03
        poly(m, [(p0[0] - dx, p0[1] - dy, p0[2]), (p1[0] - dx, p1[1] - dy, p1[2]), (p1[0] + dx, p1[1] + dy, p1[2]), (p0[0] + dx, p0[1] + dy, p0[2])], 'rib', (0, 0, 1))
    # the sill: a steel ring 0.35 high under the glass (one swept shape)
    rows = []
    for (r, z) in ((OR - 0.16, 0.0), (OR - 0.16, 0.35), (OR + 0.16, 0.35), (OR + 0.16, 0.0)):
        rows.append([opt(oang(i), r, z) for i in range(NA)])
    m.surf(rows, 'steelD')
    # mullions, the eave ring, the dome ribs and rings
    for i in range(NA):
        a = oang(i)
        m.tube([opt(a, OR, 0.35), opt(a, OR, OZ)], 0.07, 'steelL', seg=4, caps=False)
    m.tube([opt(oang(i), OR, OZ) for i in range(NA)], 0.11, 'steelL', seg=6, caps=True)
    m.tube([opt(oang(i), OR, 0.4) for i in range(NA)], 0.06, 'steelL', seg=4, caps=True, hull='none')
    for i in range(0, NA, 2):
        a = oang(i)
        m.tube([dome(a, p) for p in PHIS], 0.075, 'steelL', seg=4, caps=False)
    for p in PHIS[1:4]:
        m.tube([dome(oang(i), p) for i in range(NA)], 0.06, 'steelL', seg=4, caps=False)
    # the curved bench along the glass (a swept seat with a kick face), the observation console, the camera
    rows = []
    b0, b1 = 2, NA - 3
    for (r, z) in ((OR - 1.75, 0.0), (OR - 1.75, 0.46), (OR - 1.2, 0.46), (OR - 1.2, 0.0)):
        rows.append([opt(oang(i), r, z) for i in range(b0, b1 + 1)])
    m.surf(rows, 'fabric')
    for i in (b0, b1):
        a = oang(i)
        poly(m, [opt(a, OR - 1.75, 0.0), opt(a, OR - 1.75, 0.46), opt(a, OR - 1.2, 0.46), opt(a, OR - 1.2, 0.0)], 'fabric', (math.sin(a) * (1 if i == b1 else -1), math.cos(a) * (1 if i == b1 else -1), 0))
    cx = OCX - 4.2
    m.cy((cx, 0, 0), 1.0, 0.9, 0.9, 'steelB', seg=12)
    m.cy((cx, 0, 0.9), 1.05, 1.05, 0.06, 'steelL', seg=12)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        m.bxr(cx + math.cos(a) * 0.82, math.sin(a) * 0.82, 1.06, 0.4, 0.05, 0.22, 'steelD', rot=(60, 0, math.degrees(a) + 90))
    # deep-sea camera on a tripod looking out of the glass's apex
    tx = OCX - OR + 2.2
    for k in range(3):
        a = k / 3 * 2 * math.pi
        m.bm_((tx + math.cos(a) * 0.45, math.sin(a) * 0.45, 0.0), (tx, 0, 1.35), 0.04, 'rib')
    m.cy((tx + 0.35, 0, 1.45), 0.18, 0.2, 0.75, 'steelD', seg=8, rot=(0, -90, 0))
    m.cy((tx - 0.4, 0, 1.45), 0.2, 0.2, 0.06, 'glassE', seg=8, rot=(0, -90, 0))
    m.bx(tx + 0.15, tx + 0.55, -0.15, 0.15, 1.45 + 0.18, 1.45 + 0.42, 'subY')
    # station lettering on the console skirt
    cols = []
    N = 120
    for k in range(N + 1):
        a = math.radians(-90 + 180 * k / N)
        p = opt(a, OR, 0)
        cols.append(cb(p[0] - 0.15, p[1] - 0.15, 0.0, p[0] + 0.15, p[1] + 0.15, 3.6))
    for i in range(b0, b1, 2):   # the bench: a box per 20 degrees, cut to the swept seat
        a = (oang(i) + oang(i + 2)) / 2
        p = opt(a, OR - 1.475, 0)
        cols.append(cb(p[0] - 0.24, p[1] - 0.24, 0.0, p[0] + 0.24, p[1] + 0.24, 0.46))
    # the seabed outside the glass is solid (behind the ring boxes): nobody stands there, robots never path there
    prev = None
    for k in range(25):
        y0, y1 = -12.5 + k, -11.5 + k
        if y0 >= OR or y1 <= -OR:
            x1 = 6.0
        else:
            yy = 0.0 if y0 < 0 < y1 else min(abs(y0), abs(y1))
            x1 = OCX - math.sqrt(OR * OR - yy * yy) - 0.16
        if x1 <= -5.9:
            prev = None
            continue
        if prev and abs(prev[1] - x1) < 1e-6 and abs(prev[2] - y0) < 1e-6:
            prev[2] = y1
            cols[prev[0]] = cb(-6.0, prev[3], 0.0, x1, y1, 3.6)
        else:
            cols.append(cb(-6.0, y0, 0.0, x1, y1, 3.6))
            prev = [len(cols) - 1, x1, y1, y0]
    cols.append(cb(cx - 0.95, -0.4, 0.0, cx + 0.95, 0.4, 0.96))
    cols.append(cb(cx - 0.4, -0.95, 0.0, cx + 0.4, 0.95, 0.96))
    cols.append(cb(tx - 0.3, -0.3, 0.0, tx + 0.3, 0.3, 1.7))
    make('Landmark_Obs', m, ao, cols=cols)
    # glass (companion, additive): the wall panes and the dome panes; floor lights round the sill; console screens
    g = new(pal)
    for i in range(NA - 1):
        a0, a1 = oang(i), oang(i + 1)
        poly(g, [opt(a0, OR, 0.35), opt(a1, OR, 0.35), opt(a1, OR, OZ), opt(a0, OR, OZ)], 'glassT', (-1, 0, 0))
        for j in range(len(PHIS) - 1):
            P = [dome(a0, PHIS[j]), dome(a1, PHIS[j]), dome(a1, PHIS[j + 1]), dome(a0, PHIS[j + 1])]
            if j == len(PHIS) - 2:
                P = P[:3]
            poly(g, P, 'glassT', (-1, 0, 1))
    make_glow('Landmark_Obs_Glass', g)
    g = new(pal)
    for i in range(1, NA - 1):
        p = opt(oang(i), OR - 0.4, 0.016)
        disc(g, p[0], p[1], 0.016, 0.09, 'lampC', seg=6)
    ring(g, cx, 0, 0.963, 0.4, 0.46, 'scrC', seg=12)
    ring(g, cx, 0, 0.963, 0.62, 0.66, 'scrG', seg=12)
    make_glow('Landmark_Obs_LED', g)

    # ---- the seabed outside the glass (its own part): a sediment field swept from the sill to the footprint's edge,
    # rocks, a cable from the hull, an instrument lander
    m = new(pal)
    rnd = random.Random(21)
    def edge(a):
        dx, dy = -math.cos(a), math.sin(a)
        t = 1e9
        if dx < -1e-6:
            t = min(t, (-6.0 - OCX) / dx)
        if abs(dy) > 1e-6:
            t = min(t, (12.5 * (1 if dy > 0 else -1)) / dy)
        return t
    NS = 25
    ts = (0.0, 0.08, 0.25, 0.5, 0.78, 1.0)
    H0 = {}
    rows = []
    for j, t in enumerate(ts):
        row = []
        for i in range(NS):
            a = math.radians(-90 + 180 * i / (NS - 1))
            r = OR + 0.16 + (edge(a) - OR - 0.16) * t
            h = 0.03 if j == 0 else 0.05 + 0.32 * rnd.random() * (1 if j < len(ts) - 1 else 0.3)
            if j == len(ts) - 1:
                h = 0.03
            row.append(opt(a, r, h))
        rows.append(row)
    faces = m.surf(rows, 'sedim', hull='none')
    for k, f in enumerate(faces):
        if rnd.random() < 0.35:
            f.material_index = pal.index('sedimL')
    for k in range(9):
        a = math.radians(rnd.uniform(-80, 80))
        r = rnd.uniform(OR + 1.0, edge(a) - 0.8)
        p = opt(a, r, 0.0)
        s = rnd.uniform(0.35, 0.8)
        pts = []
        for q in range(7):
            b = q / 7 * 2 * math.pi
            pts.append((p[0] + math.cos(b) * s * rnd.uniform(0.7, 1.0), p[1] + math.sin(b) * s * rnd.uniform(0.6, 1.0), 0.01 + 0.006 * k))
        for q in range(4):
            b = rnd.uniform(0, 2 * math.pi)
            pts.append((p[0] + math.cos(b) * s * 0.5, p[1] + math.sin(b) * s * 0.5, s * rnd.uniform(0.6, 1.1)))
        hull_pts(m, pts, 'rock' if k % 3 else 'rockL')
    m.tube([(OCX - 0.05, -10.6, 0.06), (OCX - 1.5, -10.9, 0.08), (OCX - 4.0, -11.4, 0.1), (OCX - 8.0, -11.1, 0.12), (-6.0, -10.4, 0.08)], 0.08, 'hazY', seg=5, caps=False)
    lx, ly = OCX - 10.4, 9.2
    for k in range(3):
        a = k / 3 * 2 * math.pi + 0.3
        m.bm_((lx + math.cos(a) * 0.8, ly + math.sin(a) * 0.8, 0.1), (lx, ly, 1.3), 0.06, 'steelD')
    m.sp((lx, ly, 1.35), 0.3, 'subY', seg=(8, 4))
    m.cy((lx, ly, 1.6), 0.04, 0.04, 0.9, 'rib', seg=5)
    make('Obs_Seabed', m, ao)
    g = new(pal)
    g.sp((lx, ly, 2.5), 0.07, 'scrO', seg=(6, 3))
    make_glow('Obs_Seabed_LED', g)


# ================================================================ hub glass dome [17, 17] (hangs from the 7 m ceiling plane)
HR = 7.6
HD = 4.2


def build_hubdome(pal, ao):
    m = new(pal)
    n = 24
    E = 8.5

    def sq(a):
        c, s = math.cos(a), math.sin(a)
        t = E / max(abs(c), abs(s))
        return (c * t, s * t)
    for i in range(n):
        a0, a1 = i / n * 2 * math.pi, (i + 1) / n * 2 * math.pi
        s0, s1 = sq(a0), sq(a1)
        poly(m, [(math.cos(a0) * HR, math.sin(a0) * HR, -0.004), (math.cos(a1) * HR, math.sin(a1) * HR, -0.004), (s1[0], s1[1], -0.004), (s0[0], s0[1], -0.004)], 'panelG', (0, 0, -1))
    # the oculus fascia (seen from below: inward faces) and its ink-dark rim
    rows = [[(math.cos(i / n * 2 * math.pi) * HR, math.sin(i / n * 2 * math.pi) * HR, z) for i in range(n)] for z in (-0.45, 0.0)]
    f = m.surf(rows, 'tealD', hull='none', closed_u=True)
    bmesh.ops.recalc_face_normals(m.bm, faces=f)
    bmesh.ops.reverse_faces(m.bm, faces=f)
    m.tube([(math.cos(i / n * 2 * math.pi) * (HR + 0.05), math.sin(i / n * 2 * math.pi) * (HR + 0.05), -0.45) for i in range(n + 1)], 0.07, 'steelL', seg=4, caps=False)
    # ribs and rings
    phis = [math.radians(d) for d in (0, 30, 58, 80)]
    for k in range(12):
        a = k / 12 * 2 * math.pi
        m.tube([(math.cos(a) * HR * math.cos(p), math.sin(a) * HR * math.cos(p), HD * math.sin(p)) for p in phis], 0.08, 'steelL', seg=4, caps=False)
    for p in phis[1:]:
        r = HR * math.cos(p)
        m.tube([(math.cos(i / n * 2 * math.pi) * r, math.sin(i / n * 2 * math.pi) * r, HD * math.sin(p)) for i in range(n + 1)], 0.06, 'steelL', seg=4, caps=False)
    rt = HR * math.cos(phis[-1])
    m.cy((0, 0, HD * math.sin(phis[-1]) - 0.05), rt + 0.08, rt + 0.08, 0.2, 'steelD', seg=12)
    # downlights round the plate
    for k in range(8):
        a = (k + 0.5) / 8 * 2 * math.pi
        x, y = math.cos(a) * 8.05, math.sin(a) * 8.05
        m.cy((x, y, -0.16), 0.14, 0.14, 0.156, 'steelD', seg=8, caps=True)
    normals_up(make('HubDome', m, ao))
    g = new(pal)
    for k in range(12):
        a0, a1 = k / 12 * 2 * math.pi, (k + 1) / 12 * 2 * math.pi
        for j in range(len(phis) - 1):
            p0, p1 = phis[j], phis[j + 1]
            poly(g, [(math.cos(a0) * HR * math.cos(p0), math.sin(a0) * HR * math.cos(p0), HD * math.sin(p0)),
                     (math.cos(a1) * HR * math.cos(p0), math.sin(a1) * HR * math.cos(p0), HD * math.sin(p0)),
                     (math.cos(a1) * HR * math.cos(p1), math.sin(a1) * HR * math.cos(p1), HD * math.sin(p1)),
                     (math.cos(a0) * HR * math.cos(p1), math.sin(a0) * HR * math.cos(p1), HD * math.sin(p1))], 'glassT', (0, 0, -1))
    make_glow('HubDome_Glass', g)
    g = new(pal)
    for k in range(8):
        a = (k + 0.5) / 8 * 2 * math.pi
        disc(g, math.cos(a) * 8.05, math.sin(a) * 8.05, -0.163, 0.1, 'lamp', seg=8)
    make_glow('HubDome_LED', g)


# ================================================================ hub survey table [9, 9]
def build_hub(pal, ao):
    m = new(pal)
    m.cy((0, 0, 0), 1.7, 1.7, 0.25, 'steelD', seg=16)
    ring(m, 0, 0, 0.253, 1.35, 1.65, 'hazY', seg=16)
    m.cy((0, 0, 0.25), 1.25, 1.05, 0.65, 'steelB', seg=16)
    m.cy((0, 0, 0.9), 1.3, 1.3, 0.08, 'steelL', seg=16)
    # four console desks facing the table, gaps on the diagonals
    for k in range(4):
        m.push(0, 0, k * 90)
        m.bx(-1.2, 1.2, -3.6, -3.0, 0.0, 0.8, 'steelB')
        m.bxr(0.0, -3.3, 0.86, 2.3, 0.62, 0.06, 'rib', rot=(-15, 0, 0))
        m.bx(-1.0, 1.0, -3.68, -3.6, 0.85, 1.35, 'hazK')
        fq(m, -1.15, 1.15, -3.603, 0.1, 0.16, 'tealM')
        m.pop()
    for k in range(4):   # the floor ring between the desks
        a0 = math.radians(k * 90 + 25)
        a1 = math.radians(k * 90 + 65)
        for j in range(3):
            b0 = a0 + (a1 - a0) * j / 3
            b1 = a0 + (a1 - a0) * (j + 1) / 3
            poly(m, [(math.cos(b0) * 3.9, math.sin(b0) * 3.9, 0.012), (math.cos(b1) * 3.9, math.sin(b1) * 3.9, 0.012),
                     (math.cos(b1) * 4.2, math.sin(b1) * 4.2, 0.012), (math.cos(b0) * 4.2, math.sin(b0) * 4.2, 0.012)], 'tealM', (0, 0, 1))
    cols = [cb(-1.7, -0.75, 0.0, 1.7, 0.75, 0.98), cb(-0.75, -1.7, 0.0, 0.75, 1.7, 0.98), cb(-1.25, -1.25, 0.0, 1.25, 1.25, 0.98)]
    for (x0, y0, x1, y1) in ((-1.2, -3.7, 1.2, -3.0), (-1.2, 3.0, 1.2, 3.7), (-3.7, -1.2, -3.0, 1.2), (3.0, -1.2, 3.7, 1.2)):
        cols.append(cb(x0, y0, 0.0, x1, y1, 1.35))
    make('Landmark_Hub', m, ao, cols=cols)
    g = new(pal)
    disc(g, 0, 0, 0.985, 1.2, 'screen', seg=16)
    for k in range(4):
        g.push(0, 0, k * 90)
        g.bxr(0.0, -3.312, 0.9, 2.1, 0.5, 0.004, 'scrC' if k % 2 else 'scrG', rot=(-15, 0, 0))
        fq(g, -0.9, 0.9, -3.683, 0.92, 1.28, 'screen')
        for j in range(4):
            z = 0.98 + j * 0.07
            fq(g, -0.8, -0.8 + 0.3 * (1 + (j + k) % 4), -3.686, z, z + 0.03, 'scrC')
        g.pop()
    make_glow('Landmark_Hub_LED', g)
    # the hologram: a seabed relief (a ridge and a trench) as a wire grid over the table, and a ring
    g = new(pal)
    rnd = random.Random(5)
    N, S = 9, 1.1
    hts = [[0.25 * math.sin(i * 0.9) * math.cos(j * 0.7) + 0.2 * math.exp(-((i - 4) ** 2) / 4.0) - 0.15 * math.exp(-((j - 6) ** 2) / 2.0) for j in range(N)] for i in range(N)]
    def P(i, j):
        return (-S + 2 * S * i / (N - 1), -S + 2 * S * j / (N - 1), 1.45 + hts[i][j])
    for i in range(N):
        for j in range(N - 1):
            a, b = P(i, j), P(i, j + 1)
            poly(g, [a, b, (b[0], b[1], b[2] + 0.025), (a[0], a[1], a[2] + 0.025)], 'scrC', (1, 0, 0))
            a, b = P(j, i), P(j + 1, i)
            poly(g, [a, b, (b[0], b[1], b[2] + 0.025), (a[0], a[1], a[2] + 0.025)], 'tealL', (0, 1, 0))
    ring(g, 0, 0, 1.1, 1.45, 1.5, 'scrC', seg=16)
    make_glow('Hub_Holo', g)


# ================================================================ lab props
def build_labprops(pal, ao):
    # sample tank [2, 2]: a glass cylinder of murky water with sediment and a rock sample on a stand
    m = new(pal)
    m.cy((0, 0, 0), 0.85, 0.85, 0.35, 'steelB', seg=12)
    m.cy((0, 0, 0.35), 0.7, 0.7, 1.3, 'murk', seg=12, caps=False, hull='none')
    disc(m, 0, 0, 1.65, 0.7, 'murkD', seg=12)
    m.cy((0, 0, 0.35), 0.704, 0.704, 0.25, 'sedim', seg=12, caps=False, hull='none')
    m.cy((0, 0, 1.95), 0.85, 0.85, 0.2, 'steelB', seg=12)
    for k in range(4):
        a = k / 4 * 2 * math.pi + 0.4
        m.bx(math.cos(a) * 0.77 - 0.04, math.cos(a) * 0.77 + 0.04, math.sin(a) * 0.77 - 0.04, math.sin(a) * 0.77 + 0.04, 0.35, 1.95, 'steelL', hull='none')
    m.tube([(0.5, 0.0, 2.15), (0.5, 0.0, 2.6), (0.0, 0.0, 2.9), (0.0, 0.0, 4.5)], 0.06, 'tealD', seg=5, caps=False)
    make('SampleTank', m, ao, cols=[cb(-0.85, -0.6, 0.0, 0.85, 0.6, 2.15), cb(-0.6, -0.85, 0.0, 0.6, 0.85, 2.15)])
    g = new(pal)
    g.cy((0, 0, 0.35), 0.74, 0.74, 1.6, 'glassT', seg=12, caps=False)
    make_glow('SampleTank_Glass', g)
    # tank bank [4, 1] (back to the wall): three square sample tanks on a cabinet
    m = new(pal)
    m.bx(-1.95, 1.95, -0.4, 0.45, 0.0, 0.9, 'steelB', cull='b')
    for k in range(3):
        x = -1.3 + k * 1.3
        fq(m, x - 0.55, x + 0.55, -0.403, 0.1, 0.8, 'steel')
        m.bx(x - 0.58, x + 0.58, -0.35, 0.38, 0.9, 1.0, 'steelD')
        m.bx(x - 0.55, x + 0.55, -0.3, 0.35, 1.0, 1.55, 'murk', hull='none', cull='b')
        fq(m, x - 0.55, x + 0.55, -0.303, 1.0, 1.12, 'sedim')
        m.bx(x - 0.58, x + 0.58, -0.35, 0.38, 1.75, 1.82, 'steelD')
        for sx in (-1, 1):
            m.bx(x + sx * 0.56 - 0.025, x + sx * 0.56 + 0.025, -0.34, -0.29, 1.0, 1.75, 'steelD', hull='none', cull='bt')
        fq(m, x - 0.2, x + 0.2, -0.353, 0.92, 0.98, 'paper')
    make('TankBank', m, ao, cols=[cb(-1.95, -0.4, 0.0, 1.95, 0.45, 1.82)])
    g = new(pal)
    for k in range(3):
        x = -1.3 + k * 1.3
        fq(g, x - 0.53, x + 0.53, -0.33, 1.0, 1.75, 'glassT')
    make_glow('TankBank_Glass', g)
    # lab benches [2, 1]: microscope + sample jars; split sediment cores + a laptop
    for name in ('LabBench_A', 'LabBench_B'):
        m = new(pal)
        m.bx(-0.95, 0.95, -0.42, 0.42, 0.0, 0.86, 'panelG', cull='b')
        for x0 in (-0.9, 0.0):
            fq(m, x0 + 0.03, x0 + 0.87, -0.423, 0.08, 0.78, 'panel')
        m.bx(-0.97, 0.97, -0.45, 0.45, 0.86, 0.92, 'rubber')
        if name == 'LabBench_A':
            m.bx(-0.65, -0.25, -0.15, 0.15, 0.92, 0.98, 'panelL')
            m.bm_((-0.45, 0.08, 0.98), (-0.45, 0.08, 1.4), 0.07, 'panelL')
            m.bm_((-0.45, 0.08, 1.35), (-0.45, -0.12, 1.25), 0.08, 'rib')
            m.cy((-0.45, -0.18, 1.08), 0.03, 0.03, 0.14, 'rib', seg=5)
            for k in range(5):
                x = 0.15 + k * 0.15
                m.cy((x, -0.1 + (k % 2) * 0.2, 0.92), 0.05, 0.05, 0.16, 'murk' if k % 2 else 'glassE', seg=6)
                m.cy((x, -0.1 + (k % 2) * 0.2, 1.08), 0.052, 0.052, 0.03, 'fireR' if k % 3 else 'hazY', seg=6, hull='none')
        else:
            for k in range(2):
                y = -0.2 + k * 0.28
                m.bx(-0.85, 0.35, y - 0.09, y + 0.09, 0.92, 0.97, 'panelL')
                m.bx(-0.82, 0.32, y - 0.07, y + 0.07, 0.97, 1.02, 'core', hull='none')
                for j in range(4):
                    x = -0.7 + j * 0.27
                    uq(m, x, x + 0.03, y - 0.07, y + 0.07, 1.023, 'sedimL')
            m.bx(0.45, 0.85, -0.25, 0.1, 0.92, 0.94, 'rib')
            m.bxr(0.65, 0.12, 1.06, 0.38, 0.02, 0.26, 'rib', rot=(-15, 0, 0))
        make(name, m, ao, cols=[cb(-0.97, -0.45, 0.0, 0.97, 0.45, 0.95)])
    # core rack [2, 1] (back to the wall): sediment cores in tubes on four shelves
    m = new(pal)
    for sx in (-1, 1):
        m.bx(sx * 0.92 - 0.04, sx * 0.92 + 0.04, -0.3, 0.4, 0.0, 2.1, 'steelD')
    m.bx(-0.88, 0.88, 0.32, 0.4, 0.0, 2.1, 'steelB', hull='none')
    for k in range(4):
        z = 0.25 + k * 0.5
        m.bx(-0.88, 0.88, -0.3, 0.32, z, z + 0.04, 'steelL', hull='none')
        for j in range(4):
            y = -0.2 + j * 0.15
            m.cy((-0.85, y, z + 0.12), 0.06, 0.06, 1.7, 'glassE' if (j + k) % 3 else 'core', seg=6, rot=(0, 90, 0), hull='none')
        fq(m, -0.3, 0.3, -0.303, z, z + 0.04, 'paper')
    make('CoreRack', m, ao, cols=[cb(-0.96, -0.3, 0.0, 0.96, 0.4, 2.1)])
    # sonar desk [3, 2]: a console with three round sonar scopes and a keyboard shelf, faces -Y
    m = new(pal)
    m.bx(-1.45, 1.45, -0.2, 0.85, 0.0, 0.85, 'steelB', cull='b')
    m.bxr(0.0, -0.45, 0.82, 2.8, 0.55, 0.05, 'rib', rot=(-10, 0, 0))
    m.bx(-1.45, 1.45, 0.45, 0.85, 0.85, 1.75, 'steelB')
    for k in range(3):
        x = -0.95 + k * 0.95
        m.cy((x, 0.45, 1.3), 0.36, 0.36, 0.06, 'hazK', seg=12, rot=(90, 0, 0))
    m.bx(-1.45, 1.45, 0.4, 0.85, 1.75, 1.85, 'rib')
    fq(m, -1.2, 1.2, -0.203, 0.55, 0.65, 'tealM')
    text_front(m, 'SONAR', 0.12, -0.206, 0.0, 0.3, 'tealL')
    make('SonarDesk', m, ao, cols=[cb(-1.45, -0.72, 0.0, 1.45, 0.85, 0.88), cb(-1.45, 0.4, 0.88, 1.45, 0.85, 1.85)])
    g = new(pal)
    for k in range(3):
        x = -0.95 + k * 0.95
        pts = [(x + math.cos(i / 12 * 2 * math.pi) * 0.3, 0.385, 1.3 + math.sin(i / 12 * 2 * math.pi) * 0.3) for i in range(12)]
        poly(g, pts, 'screen', (0, -1, 0))
        for j in range(3):
            r = 0.08 + j * 0.09
            ring(g, x, 0.382, 1.3, r, r + 0.012, 'scrG', seg=12, normal=(0, -1, 0), axis='y')
        a = 0.6 + k
        poly(g, [(x, 0.379, 1.3), (x + math.cos(a) * 0.29, 0.379, 1.3 + math.sin(a) * 0.29), (x + math.cos(a + 0.35) * 0.29, 0.379, 1.3 + math.sin(a + 0.35) * 0.29)], 'scrG', (0, -1, 0))
    make_glow('SonarDesk_LED', g)
    # comms rack [2, 1] (back to the wall): two server cabinets with LED strips
    m = new(pal)
    m.bx(-0.95, 0.95, -0.4, 0.45, 0.0, 2.2, 'hazK', cull='b')
    for x in (-0.48, 0.48):
        fq(m, x - 0.44, x + 0.44, -0.403, 0.1, 2.1, 'rib')
        for k in range(10):
            z = 0.25 + k * 0.18
            fq(m, x - 0.38, x + 0.38, -0.406, z, z + 0.1, 'steelD')
    make('CommsRack', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.45, 2.2)])
    g = new(pal)
    for x in (-0.48, 0.48):
        for k in range(10):
            z = 0.25 + k * 0.18 + 0.035
            fq(g, x - 0.3, x - 0.3 + 0.05 * (1 + (k * 7 + int(x * 10)) % 5), -0.409, z, z + 0.025, 'scrG' if (k + int(x * 10)) % 4 else 'scrB')
    make_glow('CommsRack_LED', g)
    # workstation [2, 1]: a desk with a monitor and a keyboard (faces -Y)
    m = new(pal)
    for sx in (-1, 1):
        m.bx(sx * 0.88 - 0.04, sx * 0.88 + 0.04, -0.35, 0.35, 0.0, 0.74, 'steelD', hull='none')
    m.bx(-0.95, 0.95, -0.4, 0.4, 0.74, 0.79, 'panelG')
    m.bx(-0.45, 0.45, 0.05, 0.12, 0.85, 1.4, 'hazK')
    m.bx(-0.05, 0.05, 0.1, 0.2, 0.79, 0.9, 'rib', hull='none')
    m.bx(-0.3, 0.3, -0.3, -0.1, 0.79, 0.81, 'rib', hull='none')
    make('Workstation', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.4, 0.79)])
    g = new(pal)
    fq(g, -0.41, 0.41, 0.047, 0.89, 1.36, 'screen')
    for k in range(4):
        z = 0.95 + k * 0.1
        fq(g, -0.36, -0.36 + 0.15 * (1 + k % 3), 0.044, z, z + 0.04, 'scrC')
    make_glow('Workstation_LED', g)
    # chair (1 cell)
    m = new(pal)
    for k in range(5):
        a = k / 5 * 2 * math.pi
        m.bm_((0, 0, 0.08), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.04), 0.04, 'rib', hull='none')
    m.cy((0, 0, 0.08), 0.03, 0.03, 0.36, 'chrome', seg=5, hull='none')
    m.bx(-0.24, 0.24, -0.24, 0.24, 0.44, 0.52, 'fabric')
    m.bx(-0.22, 0.22, 0.2, 0.27, 0.55, 1.0, 'fabric')
    make('Chair', m, ao, cols=[cb(-0.26, -0.26, 0.0, 0.26, 0.28, 1.0)])
    # sample fridge (1 cell): white with a glass door, racks of vials (companion light inside)
    m = new(pal)
    m.bx(-0.4, 0.4, -0.35, 0.4, 0.0, 1.9, 'panelL', cull='b')
    fq(m, -0.36, 0.36, -0.353, 0.12, 1.75, 'rib')
    for k in range(4):
        z = 0.3 + k * 0.38
        fq(m, -0.33, 0.33, -0.356, z, z + 0.03, 'steelL')
        for j in range(6):
            x = -0.28 + j * 0.11
            fq(m, x, x + 0.05, -0.356, z + 0.04, z + 0.16, ('murk', 'fireR', 'glassE', 'hazY')[(j + k) % 4])
    m.bx(0.3, 0.34, -0.39, -0.35, 0.8, 1.2, 'chrome', hull='none')
    fq(m, -0.36, 0.0, -0.353, 1.79, 1.86, 'tealM')
    make('LabFridge', m, ao, cols=[cb(-0.4, -0.39, 0.0, 0.4, 0.4, 1.9)])
    g = new(pal)
    fq(g, -0.35, 0.35, -0.362, 0.13, 1.74, 'glassT')
    make_glow('LabFridge_Glass', g)


def build_lab(pal, ao):
    build_chamber(pal, ao)
    build_hubdome(pal, ao)
    build_hub(pal, ao)
    build_labprops(pal, ao)
