"""kit-seabase structure: wall modules in three finishes (service steel, research panels, the outer hull seen from the
observation chambers) with their wall art (portholes, leaking pipes, emergency lights, warning stencils, valve panels,
deck signs, fire points, screens, the station logo), corner posts, the watertight bulkhead door (a sliding door
parked in its pocket, a walkable coaming that holds the flood water back), the glass lab partition and its sliding
door, guard rails, the gallery / mezzanine stair and deck columns, the station gate, the trail tube, the exit hatch,
ceiling tiles and floor marks (see sb_base.py for conventions)."""
import math

from sb_base import *  # noqa: F401,F403
import sb_base as B
import sb_detail as SD
from fam_kit_bedroom import normals_up


def inner(m, faces):
    """turn a tube's faces inward (seen from inside: a porthole's bore)"""
    bmesh.ops.reverse_faces(m.bm, faces=list(faces))
    for f in faces:
        f.normal_update()


# ================================================================ wall finishes
def wall_service(m, rib=True):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'steel')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'steelD')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.18, 'rib')
    fq(m, -0.5, 0.5, -0.506, 0.18, 1.08, 'steelD')
    fq(m, -0.5, 0.5, -0.506, 1.08, 1.17, 'hazY')
    fq(m, -0.5, 0.5, -0.506, 4.3, 4.45, 'rib')
    fq(m, -0.5, 0.5, -0.506, 4.45, H, 'plate')
    # SD.wall_service(m): left out (wall modules repeat thousands of times per level; triangle budget, plan section 6)


def wall_research(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'panel')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'panelG')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.15, 'seam')
    fq(m, -0.5, 0.5, -0.506, 0.95, 1.07, 'tealM')
    fq(m, -0.5, 0.5, -0.506, 1.07, 1.09, 'tealD')
    fq(m, -0.5, 0.5, -0.506, 3.2, 3.24, 'lampC')
    fq(m, -0.5, 0.5, -0.506, 4.5, H, 'panelG')
    # SD.wall_research(m): left out (wall modules repeat thousands of times per level; triangle budget, plan section 6)


def wall_hull(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'hull')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'hullD')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.5, 'hullD')
    fq(m, -0.5, 0.5, -0.506, 0.62, 0.74, 'hazY')
    for z in (1.9, 3.7, 5.5):
        fq(m, -0.5, 0.5, -0.506, z, z + 0.03, 'hullD')
        for x in (-0.36, -0.12, 0.12, 0.36):
            fq(m, x - 0.018, x + 0.018, -0.509, z + 0.07, z + 0.106, 'rivet')
    fq(m, -0.5, -0.484, -0.503, 0.5, H, 'hullD')
    fq(m, -0.5, 0.5, -0.506, 6.9, 7.1, 'hullD')
    # SD.wall_hull(m): left out (wall modules repeat thousands of times per level; triangle budget, plan section 6)


STYLES = {'S': wall_service, 'R': wall_research, 'H': wall_hull}


def port_hole(m, z=1.5, r=0.3, outer=0.47, depth=0.5, body='steel', back='steelD', flange='steelL'):
    """a round porthole through the 1 m wall cell: the wall faces with a square hole, a tube through, a bolted
    flange ring on the front; the glass is the companion piece"""
    a = r
    for (y, c, f) in ((-0.5, body, fq), (0.5, back, bq)):
        f(m, -0.5, 0.5, y, 0.0, z - a, c)
        f(m, -0.5, 0.5, y, z + a, H, c)
        f(m, -0.5, -a, y, z - a, z + a, c)
        f(m, a, 0.5, y, z - a, z + a, c)
    inner(m, m.cy((0, -0.5, z), r, r, 1.0, 'steelD', seg=14, rot=(-90, 0, 0), caps=False, hull='none'))
    m.cy((0, -0.5, z), outer, outer, 0.07, flange, seg=14, rot=(90, 0, 0), caps=False)
    ring(m, 0, -0.573, z, r, outer, flange, seg=14, normal=(0, -1, 0), axis='y')
    for k in range(8):
        ang = (k + 0.5) / 8 * 2 * math.pi
        bx, bz = math.cos(ang) * (r + outer) / 2, z + math.sin(ang) * (r + outer) / 2
        fq(m, bx - 0.02, bx + 0.02, -0.576, bz - 0.02, bz + 0.02, 'rib')
    # glints on the glass (in front of the companion pane)
    poly(m, [(-0.16, -0.3, z + 0.02), (-0.1, -0.3, z + 0.02), (0.06, -0.3, z + 0.2), (0.0, -0.3, z + 0.2)], 'glint', (0, -1, 0))
    poly(m, [(0.06, -0.3, z - 0.2), (0.09, -0.3, z - 0.2), (0.17, -0.3, z - 0.08), (0.14, -0.3, z - 0.08)], 'glint', (0, -1, 0))


def port_glass(name, pal, z=1.5, r=0.3):
    g = new(pal)
    pts = [(math.cos(i / 14 * 2 * math.pi) * r, -0.25, z + math.sin(i / 14 * 2 * math.pi) * r) for i in range(14)]
    poly(g, pts, 'glassT', (0, -1, 0))
    make_glow(name, g)


def build_walls(pal, ao):
    for S, fn in STYLES.items():
        m = new(pal)
        fn(m)
        # SD.service_run / SD.research_run (pipe and tray runs) left out: these modules repeat hundreds of times
        # per level and the runs took the map from 258,000 to 1.09 million triangles at the entry
        make('W' + S, m, ao)
        m = new(pal)
        body, trim, acc = {'S': ('steel', 'rib', ('hazY', 1.08, 1.17)), 'R': ('panel', 'seam', ('tealM', 0.95, 1.07)),
                           'H': ('hull', 'hullD', ('hazY', 0.62, 0.74))}[S]
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, body, cull='b')
        for (c, z0, z1) in ((trim, 0.0, 0.18), acc):
            fq(m, -0.5, 0.5, -0.503, z0, z1, c)
            bq(m, -0.5, 0.5, 0.503, z0, z1, c)
            lq(m, -0.503, -0.5, 0.5, z0, z1, c)
            rq(m, 0.503, -0.5, 0.5, z0, z1, c)
        make('Corner' + S, m, ao)
    # ---- portholes (service, research, the trail tube uses its own)
    m = new(pal)
    port_hole(m)
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.18, 'rib')
    fq(m, -0.5, 0.5, -0.506, 0.18, 1.08, 'steelD')
    fq(m, -0.5, 0.5, -0.506, 1.08, 1.17, 'hazY')
    fq(m, -0.5, 0.5, -0.506, 4.3, 4.45, 'rib')
    fq(m, -0.5, 0.5, -0.506, 4.45, H, 'plate')
    SD.wall_service(m)
    SD.port_rim(m, 1.5, 0.3)
    make('WS_Port', m, ao)
    port_glass('WS_Port_Glass', pal)
    m = new(pal)
    port_hole(m, z=1.75, r=0.34, outer=0.49, body='panel', back='panelG', flange='chrome')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.15, 'seam')
    fq(m, -0.5, 0.5, -0.506, 0.95, 1.07, 'tealM')
    fq(m, -0.5, 0.5, -0.506, 4.5, H, 'panelG')
    SD.wall_research(m)
    SD.port_rim(m, 1.75, 0.34)
    make('WR_Port', m, ao)
    port_glass('WR_Port_Glass', pal, z=1.75, r=0.34)

    for S in ('S', 'R'):
        base = STYLES[S]
        # ---- leaking pipe: a riser with a cracked flange, spray (companion, blinking) and a drip line
        m = new(pal)
        base(m)
        m.cy((-0.18, -0.64, 0.0), 0.08, 0.08, 4.3, 'steelL' if S == 'S' else 'chrome', seg=8, caps=False)
        for z in (0.9, 2.3, 3.7):
            m.bx(-0.3, -0.06, -0.72, -0.5, z, z + 0.05, 'steelD', hull='none')
        m.cy((-0.18, -0.64, 2.05), 0.115, 0.115, 0.1, 'rib', seg=8)
        m.cy((-0.18, -0.64, 0.6), 0.06, 0.06, 0.6, 'tealD', seg=6, rot=(0, 90, 0), caps=False)
        m.cy((0.42, -0.64, 0.6), 0.075, 0.075, 0.08, 'tealD', seg=6, rot=(0, 90, 0))
        wheel(m, 0.18, -0.74, 1.35, 0.13, 'fireR')
        m.bx(-0.02, 0.02, -0.74, -0.64, 1.35, 1.38, 'steelD', hull='none')
        fq(m, 0.0, 0.42, -0.509, 2.7, 3.05, 'hazY')
        text_front(m, 'LEAK', 0.18, -0.512, 0.21, 2.78, 'hazK')
        make('W%s_Leak' % S, m, ao)
        for k in range(2):
            g = new(pal)
            for j in range(4):
                a = math.radians(-50 + j * 33 + k * 15)
                L = 0.55 + 0.15 * ((j + k) % 2)
                x0, z0 = -0.18 + 0.12 * math.cos(a), 2.1
                pts = [(x0, -0.66, z0), (x0, -0.62, z0 + 0.02), (x0 + math.cos(a) * L, -0.95, z0 + math.sin(a) * L * 0.6 + 0.04), (x0 + math.cos(a) * L, -1.0, z0 + math.sin(a) * L * 0.6)]
                poly(g, pts, 'lampC', (0, -1, 0))
            for j in range(3):   # the drip line down the pipe
                zz = 1.9 - j * 0.55 - k * 0.27
                fq(g, -0.205, -0.155, -0.725, zz - 0.18, zz, 'tealL')
            make_glow('W%s_Leak_Spray%d' % (S, k), g)
        # ---- emergency light: a caged beacon on a bracket (the lens and the rays are companions)
        m = new(pal)
        base(m)
        m.bx(-0.14, 0.14, -0.6, -0.5, 3.0, 3.18, 'steelD')
        m.cy((0.0, -0.72, 3.18), 0.14, 0.14, 0.06, 'rib', seg=10)
        for k in range(4):
            ang = k / 4 * 2 * math.pi + 0.4
            m.bm_((math.cos(ang) * 0.15, -0.72 + math.sin(ang) * 0.15, 3.24), (math.cos(ang) * 0.06, -0.72 + math.sin(ang) * 0.06, 3.52), 0.02, 'rib', hull='none')
        fq(m, -0.3, 0.3, -0.509, 3.65, 3.9, 'hazK')
        text_front(m, 'ALARM', 0.15, -0.512, 0.0, 3.7, 'orange')
        make('W%s_Beacon' % S, m, ao)
        if S == 'S':
            g = new(pal)
            g.sp((0.0, -0.72, 3.24), 0.12, 'orange', seg=(8, 4), scale=(1, 1, 1.5))
            make_glow('Beacon_Lamp', g)
            g = new(pal)
            for k in range(3):
                ang = k / 3 * math.pi
                c, s = math.cos(ang), math.sin(ang)
                pts = [(c * 0.1, -0.72 + s * 0.1, 3.3), (c * 1.4, -0.72 + s * 1.4, 3.6), (c * 1.4, -0.72 + s * 1.4, 3.0)]
                pts2 = [(-c * 0.1, -0.72 - s * 0.1, 3.3), (-c * 1.4, -0.72 - s * 1.4, 3.6), (-c * 1.4, -0.72 - s * 1.4, 3.0)]
                for P_ in (pts, pts2):
                    if P_[1][1] < -0.5:
                        poly(g, P_, 'orange', (s, -c, 0))
            make_glow('Beacon_Ray', g)
        # ---- fire point: red panel, extinguisher, hose reel
        m = new(pal)
        base(m)
        m.bx(-0.42, 0.42, -0.56, -0.5, 1.3, 2.3, 'fireR', cull='k')
        fq(m, -0.38, 0.38, -0.563, 2.05, 2.25, 'paper')
        text_front(m, 'FIRE POINT', 0.12, -0.566, 0.0, 2.08, 'fireR', maxw=0.7)
        m.cy((0.0, -0.6, 1.62), 0.26, 0.26, 0.16, 'fireR', seg=12, rot=(90, 0, 0))
        m.cy((0.0, -0.76, 1.62), 0.12, 0.12, 0.03, 'chrome', seg=10, rot=(90, 0, 0))
        m.cy((-0.3, -0.7, 0.3), 0.1, 0.1, 0.55, 'fireR', seg=8)
        m.cy((-0.3, -0.7, 0.85), 0.04, 0.03, 0.08, 'rubber', seg=6, hull='none')
        make('W%s_Fire' % S, m, ao)
        # ---- flood stencil: FLOOD ZONE with depth marks
        m = new(pal)
        base(m)
        fq(m, -0.46, 0.46, -0.509, 2.0, 2.5, 'hazY')
        text_front(m, 'FLOOD', 0.3, -0.512, 0.0, 2.08, 'hazK', maxw=0.8)
        for k in range(6):
            z = 0.25 + k * 0.25
            fq(m, -0.4, -0.4 + (0.2 if k % 2 else 0.12), -0.509, z, z + 0.025, 'hazK' if S == 'R' else 'paper')
        text_front(m, 'KEEP DOORS SHUT', 0.075, -0.512, 0.12, 1.75, 'hazK' if S == 'R' else 'paper', font='sans', maxw=0.6)
        make('W%s_Flood' % S, m, ao)

    # ---- service-only art
    m = new(pal)
    wall_service(m)
    m.bx(-0.44, 0.44, -0.535, -0.5, 1.9, 2.8, 'hazY', cull='k')
    hazard(m, -0.44, 0.44, -0.538, 2.62, 2.78, 6)
    text_front(m, 'DANGER', 0.2, -0.539, 0.0, 2.28, 'hazK', maxw=0.8)
    text_front(m, 'HIGH PRESSURE', 0.09, -0.539, 0.0, 2.0, 'hazK', font='sans', maxw=0.8)
    make('WS_Warn', m, ao)
    m = new(pal)                                        # valve panel: two handwheels on a header, gauges
    wall_service(m)
    m.cy((-0.5, -0.66, 1.6), 0.1, 0.1, 1.0, 'tealD', seg=8, rot=(0, 90, 0), caps=False, hull='noside')
    for x in (-0.22, 0.22):
        m.cy((x, -0.66, 1.6), 0.13, 0.13, 0.22, 'steelD', seg=8, rot=(90, 0, 0))
        wheel(m, x, -0.9, 1.6, 0.16, 'fireR' if x < 0 else 'hazY')
    m.bx(-0.3, 0.3, -0.54, -0.5, 2.1, 2.5, 'steelL', cull='k')
    gauge(m, -0.14, -0.54, 2.3)
    gauge(m, 0.14, -0.54, 2.3)
    SD.valve_panel(m)
    make('WS_Valve', m, ao)
    for name, top, sub in (('WS_SignDock', 'DOCK B', 'MOON POOL'), ('WS_SignPump', 'PUMPS', 'BALLAST')):
        m = new(pal)
        wall_service(m)
        m.bx(-0.48, 0.48, -0.56, -0.5, 2.9, 3.7, 'orange', cull='k')
        fq(m, -0.46, 0.46, -0.563, 2.92, 3.1, 'hazK')
        text_front(m, top, 0.4, -0.566, 0.0, 3.17, 'hazK', maxw=0.86)
        text_front(m, sub, 0.12, -0.566, 0.0, 2.95, 'paper', font='sans', maxw=0.8)
        make(name, m, ao)
    # ---- research-only art: the seabed sonar screen (companion), the station logo, ring signs
    m = new(pal)
    wall_research(m)
    m.bx(-0.48, 0.48, -0.58, -0.5, 1.45, 2.55, 'hazK', cull='k')
    make('WR_Screen', m, ao)
    g = new(pal)
    fq(g, -0.44, 0.44, -0.583, 1.49, 2.51, 'screen')
    for k in range(5):                                   # seabed contour lines
        z = 1.6 + k * 0.17
        pts = [(-0.4 + i * 0.08, z + 0.05 * math.sin(i * 0.9 + k)) for i in range(11)]
        for i in range(10):
            (x0, z0), (x1, z1) = pts[i], pts[i + 1]
            poly(g, [(x0, -0.586, z0), (x1, -0.586, z1), (x1, -0.586, z1 + 0.018), (x0, -0.586, z0 + 0.018)], 'scrC' if k % 2 else 'scrG', (0, -1, 0))
    fq(g, -0.44, 0.44, -0.586, 2.38, 2.48, 'tealD')
    make_glow('WR_Screen_LED', g)
    m = new(pal)
    wall_research(m)
    m.bx(-0.5, 0.5, -0.54, -0.5, 2.6, 3.0, 'tealD', hull='noside', cull='k')
    text_front(m, 'THALASSA', 0.24, -0.543, 0.0, 2.68, 'panelL', maxw=0.94)
    ring(m, 0.0, -0.506, 3.75, 0.28, 0.34, 'tealM', seg=16, normal=(0, -1, 0), axis='y')
    for k in range(3):
        z = 3.62 + k * 0.1
        poly(m, [(-0.2, -0.506, z), (0.2, -0.506, z), (0.2, -0.506, z + 0.03), (-0.2, -0.506, z + 0.03)], 'tealD', (0, -1, 0))
    make('WR_Logo', m, ao)
    for name, top, sub in (('WR_SignHub', 'HUB', 'OBSERVATION'), ('WR_SignObs', 'VIEW', 'CHAMBER')):
        m = new(pal)
        wall_research(m)
        m.bx(-0.48, 0.48, -0.56, -0.5, 2.6, 3.1, 'tealD', cull='k')
        text_front(m, top, 0.28, -0.563, 0.0, 2.78, 'panelL', maxw=0.86)
        text_front(m, sub, 0.1, -0.563, 0.0, 2.64, 'tealL', font='sans', maxw=0.86)
        make(name, m, ao)
    # ---- hull floodlight: a lamp on a bracket aiming down into the notch (the beam cone is an additive companion)
    m = new(pal)
    wall_hull(m)
    m.bx(-0.12, 0.12, -0.75, -0.5, 4.6, 4.75, 'hullD')
    m.cy((0.0, -0.85, 4.45), 0.17, 0.2, 0.3, 'rivet', seg=10, rot=(-30, 0, 0))
    make('WH_Lamp', m, ao)
    g = new(pal)
    fq(g, -0.1, 0.1, -1.03, 4.38, 4.56, 'lamp')
    make_glow('WH_Lamp_LED', g)
    g = new(pal)
    n = 10
    apex = (0.0, -1.0, 4.4)
    for i in range(n):
        a0, a1 = i / n * 2 * math.pi, (i + 1) / n * 2 * math.pi
        cx, cy, cz = 0.0, -3.0, 0.4
        R = 1.2
        p0 = (cx + math.cos(a0) * R, cy + math.sin(a0) * R * 0.6, cz)
        p1 = (cx + math.cos(a1) * R, cy + math.sin(a1) * R * 0.6, cz)
        poly(g, [apex, p0, p1], 'beamG', (0, -1, 0))
    make_glow('WH_Lamp_Beam', g)


# ================================================================ watertight bulkhead door [3, 2]
def build_doors(pal, ao):
    m = new(pal)
    # jambs and the heavy frame with rounded corners on both faces
    for sx in (-1, 1):
        a, b = sorted((sx * 1.2, sx * 1.5))
        m.bx(a, b, -1.0, 1.0, 0.0, DH, 'steelD', cull='b' + ('l' if sx < 0 else 'r'))
    m.bx(-1.5, 1.5, -1.0, 1.0, DH, H, 'steel', hull='noside', cull='t')
    dq(m, -1.2, 1.2, -1.0, 1.0, DH - 0.003, 'rib')
    for sy in (-1, 1):
        c0, c1 = sorted((sy * 1.0, sy * 1.12))
        for sx in (-1, 1):
            a, b = sorted((sx * 1.2, sx * 1.42))
            m.bx(a, b, c0, c1, 0.25, DH - 0.25, 'hazY')
        m.bx(-0.95, 0.95, c0, c1, DH - 0.02, DH + 0.2, 'hazY')
        for sx in (-1, 1):          # rounded top corners: a mitred block in each upper corner of the opening
            m.bxr(sx * 1.13, sy * 1.06, DH - 0.12, 0.42, 0.1, 0.2, 'hazY', rot=(0, sx * 45, 0), hull='none')
        yy = sy * 1.12
        (fq if sy < 0 else bq)(m, -0.9, 0.9, yy + sy * 0.003, DH + 0.05, DH + 0.15, 'hazK')
        # the hydraulic ram housing over the opening and the status lamp box
        c2, c3 = sorted((sy * 1.0, sy * 1.16))
        m.bx(-1.3, 0.9, c2, c3, 3.05, 3.3, 'steelD', hull='none')
        m.bx(1.25, 1.45, c2, c3, 2.85, 3.05, 'rib', hull='none')
    # the leaf, slid into its pocket: its striped edge shows in the left jamb
    m.bx(-1.24, -1.12, -0.12, 0.12, SILL, DH - 0.05, 'steelL', cull='l')
    for k in range(3):
        z0 = SILL + 0.15 + k * 0.76
        rq(m, -1.117, -0.11, 0.11, z0, z0 + 0.38, 'hazK')
    # the coaming: a raised steel sill across the opening (walkable), hazard-striped, with a rubber seal groove
    m.bx(-1.2, 1.2, -1.0, 1.0, 0.0, SILL, 'steelD', cull='b')
    hazard_up(m, -1.2, 1.2, -1.0, -0.6, SILL + 0.003, 5)
    hazard_up(m, -1.2, 1.2, 0.6, 1.0, SILL + 0.003, 5)
    uq(m, -1.2, 1.2, -0.06, 0.06, SILL + 0.003, 'rubber')
    SD.bulkhead(m)
    make('Bulkhead', m, ao, cols=[cb(-1.5, -1.0, 0.0, -1.12, 1.0, DH), cb(1.2, -1.0, 0.0, 1.5, 1.0, DH),
                                  cb(-1.2, -1.0, 0.0, 1.2, 1.0, SILL, True)])
    g = new(pal)
    for sy in (-1, 1):
        (fq if sy < 0 else bq)(g, 1.29, 1.41, sy * 1.163, 2.89, 3.01, 'scrG')
    make_glow('Bulkhead_LED', g)


# ================================================================ glass partitions and the lab door
GH = 4.5    # partitions run up to the 4.5 m ceiling


def glass_run(m, y0, y1, mullion=True):
    m.bx(-0.07, 0.07, y0, y1, 0.0, 0.12, 'steelD', hull='noend', cull='b')
    m.bx(-0.05, 0.05, y0, y1, GH - 0.14, GH, 'steelL', hull='noend', cull='t')
    m.bx(-0.035, 0.035, y0, y1, 2.68, 2.74, 'steelL', hull='noend')
    if mullion:
        m.bx(-0.04, 0.04, -0.03, 0.03, 0.12, GH - 0.14, 'steelL', hull='none')
    for s in (-1, 1):
        x = s * 0.006
        a = y0 + (y1 - y0) * 0.2
        poly(m, [(x, a, 0.6), (x, a + 0.08, 0.6), (x, a + 0.28, 1.4), (x, a + 0.2, 1.4)], 'glint', (s, 0, 0))
        poly(m, [(x, a + 0.3, 1.0), (x, a + 0.34, 1.0), (x, a + 0.44, 1.35), (x, a + 0.4, 1.35)], 'glint', (s, 0, 0))


def glass_pane(name, pal, y0, y1):
    g = new(pal)
    for (z0, z1) in ((0.12, 2.68), (2.74, GH - 0.14)):
        poly(g, [(0.0, y0, z0), (0.0, y1, z0), (0.0, y1, z1), (0.0, y0, z1)], 'glassT', (1, 0, 0))
    make_glow(name, g)


def build_glass(pal, ao):
    m = new(pal)
    glass_run(m, -0.5, 0.5)
    make('GlassFull', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.5, GH)])
    glass_pane('GlassFull_Glass', pal, -0.5, 0.5)
    m = new(pal)
    glass_run(m, -0.5, -0.04, mullion=False)
    make('GlassHalf', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.0, GH)])
    glass_pane('GlassHalf_Glass', pal, -0.5, -0.04)
    m = new(pal)
    m.bx(-0.06, 0.06, -0.06, 0.06, 0.0, GH, 'steelL', cull='bt')
    make('GlassPost', m, ao, cols=[cb(-0.06, -0.06, 0.0, 0.06, 0.06, GH)])
    # sliding lab door [3, 1] (in a glass run, local X along the run): two leaves parked over the side lights
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.05, sx * 1.5))
        m.bx(a, b, -0.07, 0.07, 0.0, 0.12, 'steelD', cull='b')
        e0, e1 = sorted((sx * 1.05, sx * 1.11))
        m.bx(e0, e1, -0.06, 0.06, 0.12, 2.74, 'steelL')
        f0, f1 = sorted((sx * 1.44, sx * 1.5))
        m.bx(f0, f1, -0.06, 0.06, 0.12, 2.74, 'steelL', hull='none')
        for sy in (-1, 1):   # leaf frames parked in front of / behind the side lights
            yy = sy * 0.1
            c0, c1 = sorted((yy, yy + sy * 0.03))
            m.bx(a, b, c0, c1, 0.08, 0.16, 'steelL')
            m.bx(a, b, c0, c1, 2.6, 2.68, 'steelL')
            m.bx(e0, e1, c0, c1, 0.16, 2.6, 'steelL', hull='none')
            if sy < 0:
                m.bx(sx * 1.2 - 0.02, sx * 1.2 + 0.02, c0 - 0.03, c0, 0.9, 1.5, 'chrome', hull='none')
    m.bx(-1.5, 1.5, -0.08, 0.08, 2.74, 2.98, 'steelD')
    for sy in (-1, 1):
        (fq if sy < 0 else bq)(m, -0.9, 0.9, sy * 0.083, 2.78, 2.94, 'tealD')
        (text_front if sy < 0 else text_back)(m, 'LAB', 0.12, sy * 0.086, 0.0, 2.8, 'panelL')
    m.bx(-1.5, 1.5, -0.05, 0.05, GH - 0.14, GH, 'steelL', cull='t')
    for sx in (-1, 1):
        a, b = sorted((sx * 1.44, sx * 1.5))
        m.bx(a, b, -0.05, 0.05, 2.98, GH - 0.14, 'steelL', hull='none')
    make('GlassDoor', m, ao, cols=[cb(-1.5, -0.13, 0.0, -1.05, 0.13, 2.74), cb(1.05, -0.13, 0.0, 1.5, 0.13, 2.74),
                                   cb(-1.5, -0.08, 2.74, 1.5, 0.08, GH)])
    g = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.11, sx * 1.44))
        poly(g, [(a, 0.0, 0.12), (b, 0.0, 0.12), (b, 0.0, 2.74), (a, 0.0, 2.74)], 'glassT', (0, -1, 0))
        for sy in (-1, 1):
            yy = sy * 0.115
            poly(g, [(a, yy, 0.16), (b, yy, 0.16), (b, yy, 2.6), (a, yy, 2.6)], 'glassT', (0, -1, 0))
    poly(g, [(-1.44, 0.0, 2.98), (1.44, 0.0, 2.98), (1.44, 0.0, GH - 0.14), (-1.44, 0.0, GH - 0.14)], 'glassT', (0, -1, 0))
    make_glow('GlassDoor_Glass', g)


# ================================================================ rails, stair, deck columns
def build_mezzanine(pal, ao):
    def rail(m, y0, y1):
        m.bx(-0.03, 0.03, y0, y1, 1.02, 1.08, 'hazY', hull='noend', cull='')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'steelL', hull='noend', cull='')
        m.bx(-0.012, 0.012, y0, y1, 0.0, 0.12, 'hazY', hull='none', cull='b')
    m = new(pal); rail(m, -0.5, 0.5)
    m.bx(-0.025, 0.025, -0.025, 0.025, 0.0, 1.02, 'steelL', hull='none', cull='b')
    make('RailFull', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.5, 1.08)])
    m = new(pal); rail(m, -0.5, -0.035); make('RailHalf', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.0, 1.08)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.1, 'hazY', cull='b')
    make('RailPost', m, ao)
    under = DECK - 0.4
    m = new(pal)
    m.bx(-0.11, 0.11, -0.11, 0.11, 0.0, under, 'steelD', cull='bt')
    m.bx(-0.17, 0.17, -0.17, 0.17, under - 0.05, under, 'steelD', hull='none', cull='t')
    for (c, z0, z1) in (('hazY', 0.0, 0.35), ('hazK', 0.35, 0.5), ('hazY', 0.5, 0.85)):
        fq(m, -0.11, 0.11, -0.113, z0, z1, c)
        bq(m, -0.11, 0.11, 0.113, z0, z1, c)
        lq(m, -0.113, -0.11, 0.11, z0, z1, c)
        rq(m, 0.113, -0.11, 0.11, z0, z1, c)
    make('DeckColumn', m, ao, cols=[cb(-0.11, -0.11, 0.0, 0.11, 0.11, under)])
    # steel stair [2, 7] rising toward Blender +Y (game north) to the deck: 12 steps and a landing
    m = new(pal)
    W, L, n, landing = 1.6, 7.0, 12, 0.6
    run = (L - landing) / n
    cols = []
    for k in range(n):
        y0 = -L / 2 + k * run
        y1 = y0 + run if k < n - 1 else L / 2
        top = (k + 1) * DECK / n
        m.bx(-W / 2, W / 2, y0, y1, top - 0.06, top, 'grate', cull='')
        uq(m, -W / 2 + 0.03, W / 2 - 0.03, y0 + 0.005, y0 + 0.06, top + 0.003, 'hazY')
        cols.append(cb(-W / 2, y0, 0.0, W / 2, y1, top, True))
    for sx in (-1, 1):
        a, b = sorted((sx * W / 2, sx * (W / 2 + 0.08)))
        prof = [(-L / 2, 0.0), (-L / 2 + 0.25, 0.0), (L / 2 - landing, DECK - 0.35), (L / 2, DECK - 0.35), (L / 2, DECK), (L / 2 - landing - 0.1, DECK), (-L / 2, 0.3)]
        m.prism(prof, a, b, ['steelD'])
        xr = sx * (W / 2 + 0.04)
        m.bm_((xr, -L / 2 + 0.1, 1.0), (xr, L / 2 - landing, DECK + 1.0), 0.05, 'hazY')
        m.bm_((xr, L / 2 - landing, DECK + 1.0), (xr, L / 2 - 0.05, DECK + 1.0), 0.042, 'hazY')
        for k in range(4):
            t = (k + 0.5) / 4
            yy = -L / 2 + 0.1 + t * (L - landing - 0.1)
            zz = 0.3 + t * (DECK - 0.3)
            m.bx(xr - 0.015, xr + 0.015, yy - 0.015, yy + 0.015, zz, zz + 0.95, 'hazY', hull='none', cull='b')
        for k in range(n + 1):
            y0 = -L / 2 + k * run
            y1 = L / 2 if k == n else y0 + run
            top = min(DECK, (k + 1) * DECK / n) + 1.0
            cols.append(cb(a, y0, 0.0, b, y1, top))
    SD.stair(m, W, L, n, landing, DECK)
    make('Stair', m, ao, cols=cols)


# ================================================================ gate, shutter, trail tube, exit hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.5, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'steelD', cull='b')
        for fy in (-1, 1):
            (fq if fy < 0 else bq)(m, a + 0.06, b - 0.06, fy * 0.623, 0.0, 0.5, 'hazY')
            (fq if fy < 0 else bq)(m, a + 0.06, b - 0.06, fy * 0.623, 0.6, 2.9, 'steel')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.8, 'rib')
    for fy in (-1, 1):
        hazard(m, -1.8, 1.8, fy * 0.623, 3.4, 3.7, 14, face=fy)
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.8, H, 'steel', cull='t')
    for fy in (-1, 1):
        c0, c1 = sorted((fy * 0.45, fy * 0.53))
        m.bx(-1.4, 1.4, c0, c1, 4.05, 4.85, 'tealD')
        (text_front if fy < 0 else text_back)(m, 'THALASSA', 0.38, fy * 0.533, 0.0, 4.25, 'panelL', maxw=2.5)
        (fq if fy < 0 else bq)(m, -2.48, 2.48, fy * 0.453, 5.4, 5.48, 'hazY')
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    m = new(pal)
    Hs, n = 3.05, 8
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.03), 'steelL' if i % 2 else 'steel', bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'hazK' if k % 2 else 'hazY', bevel=False)
    m.box((0, -0.06, 1.7), (2.9, 0.02, 0.06), 'tealL', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # the connecting tube between the zones (1 m along Blender Y, inner face +X): ribbed steel, portholes, lamps
    TH = 4.6
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        if name == 'TrailWall_B':
            for (x, c, f) in ((0.25, 'steel', rq), (-0.25, 'steelD', lq)):
                f(m, x, -0.5, 0.5, 0.0, 1.2, c)
                f(m, x, -0.5, 0.5, 1.8, TH, c)
                f(m, x, -0.5, -0.3, 1.2, 1.8, c)
                f(m, x, 0.3, 0.5, 1.2, 1.8, c)
            inner(m, m.cy((0.25, 0.0, 1.5), 0.3, 0.3, 0.5, 'steelD', seg=12, rot=(0, -90, 0), caps=False, hull='none'))
            m.cy((0.25, 0.0, 1.5), 0.43, 0.43, 0.03, 'steelL', seg=12, rot=(0, 90, 0), caps=False, hull='none')
            ring(m, 0.283, 0.0, 1.5, 0.3, 0.43, 'steelL', seg=12, normal=(1, 0, 0), axis='x')
            for k in range(6):
                ang = (k + 0.5) / 6 * 2 * math.pi
                rq(m, 0.286, math.cos(ang) * 0.365 - 0.018, math.cos(ang) * 0.365 + 0.018, 1.5 + math.sin(ang) * 0.365 - 0.018, 1.5 + math.sin(ang) * 0.365 + 0.018, 'rib')
            poly(m, [(0.1, -0.15, 1.52), (0.1, -0.09, 1.52), (0.1, 0.07, 1.72), (0.1, 0.01, 1.72)], 'glint', (1, 0, 0))
        else:
            rq(m, 0.25, -0.5, 0.5, 0.0, TH, 'steel')
            lq(m, -0.25, -0.5, 0.5, 0.0, TH, 'steelD')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.18, 'rib')
        rq(m, 0.253, -0.5, 0.5, 0.95, 1.04, 'hazY')
        m.bx(0.25, 0.32, -0.5, 0.5, 3.4, 3.55, 'rib', hull='noend')
        if name == 'TrailWall_C':
            m.bx(0.25, 0.32, -0.3, 0.3, 2.6, 2.72, 'steelD')
            rq(m, 0.323, -0.26, 0.26, 2.62, 2.7, 'lampC')
            for k in range(2):
                y0 = -0.35 + k * 0.4
                pts = [(y0, 1.3), (y0 + 0.14, 1.3), (y0 + 0.3, 1.5), (y0 + 0.14, 1.7), (y0, 1.7), (y0 + 0.16, 1.5)]
                poly(m, [(0.256, p[0], p[1]) for p in pts[:3] + [pts[5]]], 'tealL', (1, 0, 0))
                poly(m, [(0.256, p[0], p[1]) for p in [pts[5], pts[2], pts[3], pts[4]]], 'tealL', (1, 0, 0))
        make(name, m, ao)
    g = new(pal)
    poly(g, [(0.0, -0.3 * math.cos(i / 12 * 2 * math.pi), 1.5 + 0.3 * math.sin(i / 12 * 2 * math.pi)) for i in range(12)], 'glassT', (1, 0, 0))
    make_glow('TrailWall_B_Glass', g)
    # exit hatch: a round docking hatch in the floor
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=20)
    ring(m, 0, 0, 0.103, 0.98, 1.15, 'hazY', seg=20)
    m.cy((0, 0, 0.1), 0.9, 0.86, 0.06, 'steel', seg=20)
    wheel(m, 0.0, 0.0, 0.22, 0.42, 'hazY', axis='z')
    SD.hatch(m)
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ ceiling tiles (hang from z = 0) and floor marks
def build_ceiling(pal, ao):
    # ceiling tiles shade as if they faced up (custom normals, fam_kit_bedroom.normals_up): the toon light has no
    # ambient term, so a down-facing ceiling would otherwise fall in the darkest band
    m = new(pal)
    dq(m, -0.5, 0.5, -0.5, 0.5, -0.004, 'deck')
    normals_up(make('C_Deck', m, ao))
    m = new(pal)
    dq(m, -0.5, 0.5, -0.5, 0.5, -0.004, 'deck')
    m.bx(-0.24, 0.24, -0.15, 0.15, -0.16, -0.004, 'steelD', cull='t')
    normals_up(make('C_DeckLamp', m, ao))
    g = new(pal)
    dq(g, -0.2, 0.2, -0.11, 0.11, -0.165, 'lamp')
    make_glow('C_DeckLamp_LED', g)
    m = new(pal)
    dq(m, -0.5, 0.5, -0.5, 0.5, -0.004, 'deck')
    for (y, r, c) in ((-0.2, 0.08, 'hazY'), (0.18, 0.11, 'tealD')):
        m.cy((-0.5, y, -0.42), r, r, 1.0, c, seg=6, rot=(0, 90, 0), caps=False, hull='noside')
    m.bx(-0.03, 0.03, -0.38, 0.38, -0.55, -0.5, 'rib', hull='none')
    for y in (-0.38, 0.38):
        m.bx(-0.024, 0.024, y - 0.015, y + 0.015, -0.5, -0.004, 'rib', hull='none', cull='t')
    normals_up(make('C_DeckPipe', m, ao))
    m = new(pal)
    dq(m, -0.5, 0.5, -0.5, 0.5, -0.004, 'panelG')
    normals_up(make('C_Panel', m, ao))
    m = new(pal)
    dq(m, -0.5, 0.5, -0.5, 0.5, -0.004, 'panelG')
    m.bx(-0.36, 0.36, -0.36, 0.36, -0.05, -0.004, 'seam', hull='none', cull='t')
    normals_up(make('C_PanelLight', m, ao))
    g = new(pal)
    dq(g, -0.32, 0.32, -0.32, 0.32, -0.054, 'lampC')
    make_glow('C_PanelLight_LED', g)


def build_floors(pal, ao):
    z = 0.006
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, z, 'hazY')
    for k in (1, 3):
        uq(m, -0.5 + k * 0.2, -0.3 + k * 0.2, -0.5, 0.5, z + 0.003, 'hazK')
    make('F_Hazard', m, ao)
    m = new(pal)
    uq(m, -1.45, 1.45, -0.42, 0.42, z, 'hazY')
    uq(m, -1.39, 1.39, -0.36, 0.36, z + 0.003, 'hazK')
    text_up(m, 'FLOOD ZONE', 0.4, z + 0.006, 0.0, 0.0, 'hazY', maxw=2.6)
    make('F_Flood', m, ao)
    m = new(pal)
    uq(m, -0.32, 0.32, -0.32, 0.32, z, 'rib')
    for k in range(5):
        y = -0.24 + k * 0.12
        uq(m, -0.26, 0.26, y - 0.025, y + 0.025, z + 0.003, 'grate')
    make('F_Drain', m, ao)


def build_struct(pal, ao):
    build_walls(pal, ao)
    build_doors(pal, ao)
    build_glass(pal, ao)
    build_mezzanine(pal, ao)
    build_gate(pal, ao)
    build_ceiling(pal, ao)
    build_floors(pal, ao)
