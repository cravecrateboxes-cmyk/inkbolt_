"""kit-townhomes site pieces: the gated entrance (zone 1 landmark), the entry sign wall, the clubhouse, the pool and
its deck furniture, the mailbox kiosk, the playground, the park gazebo and the lot under construction (zone 2
landmark) with its skip and building materials. Front = -Y (game +Z, south: the entrance faces the approach road).
"""
import math

from townhomes_base import *  # noqa: F401,F403
import townhomes_detail as TD

EMB = TD.EMB
from townhomes_houses import window, door, clip_rects, frame_front, frame_back, fz, fbox, carriage_lamp  # noqa: F401
from townhomes_rooms import sofa, table, chair, shelf, picture, counter_run, plant, rug, lamp, stool  # noqa: F401


def tube(m, a, b, r, c, hull='none'):
    """a round tube from a to b (scaffold, rails): a 5-sided cylinder"""
    a, b = Vector(a), Vector(b)
    d = b - a
    e = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler('XYZ')
    m.cy(tuple(a), r, r, d.length, c, seg=5, rot=tuple(math.degrees(v) for v in e), hull=hull)


def solid(cols, x0, y0, z0, x1, y1, z1):
    cols.append(box(x0, y0, z0, x1, y1, z1))


def stone_pier(m, cols, x, y, w, h, cap='stoneD', lantern=True):
    """a stone gate pier with a cap stone and a lantern on top"""
    m.bx(x - w / 2, x + w / 2, y - w / 2, y + w / 2, 0.0, h, 'stone', cull='b')
    for k in range(1, int(h / 0.6)):
        z = k * 0.6
        fq(m, x - w / 2, x + w / 2, y - w / 2 - 0.004, z - 0.012, z + 0.012, 'stoneD')
    m.bx(x - w / 2 - 0.08, x + w / 2 + 0.08, y - w / 2 - 0.08, y + w / 2 + 0.08, h, h + 0.16, cap)
    if lantern:
        m.bx(x - 0.12, x + 0.12, y - 0.12, y + 0.12, h + 0.16, h + 0.22, 'iron')
        m.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, h + 0.22, h + 0.6, 'glassL')
        m.fan((x, y, h + 0.6), h + 0.82, 0.24, 4, ['iron'], rot=math.pi / 4)
    solid(cols, x - w / 2 - 0.08, y - w / 2 - 0.08, 0.0, x + w / 2 + 0.08, y + w / 2 + 0.08, h + 0.16)


def iron_leaf(m, x0, x1, y, z0, h, arch=0.25):
    """a wrought-iron gate leaf along X: rails, pickets with spear tips, an arched top rail"""
    m.bx(x0, x1, y - 0.03, y + 0.03, z0 + 0.1, z0 + 0.16, 'iron')
    m.bx(x0, x1, y - 0.03, y + 0.03, z0 + h - 0.3, z0 + h - 0.24, 'iron')
    for x in (x0, x1):
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, z0, z0 + h + arch * 0.4, 'iron')
    n = max(2, int(round((x1 - x0) / 0.22)))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        u = (x - x0) / (x1 - x0)
        top = z0 + h + arch * math.sin(math.pi * u) * 0.6
        m.bx(x - 0.016, x + 0.016, y - 0.016, y + 0.016, z0 + 0.05, top, 'iron', hull='none', cull='b')
    m.cy((((x0 + x1) / 2), y, z0 + 0.55), 0.16, 0.16, 0.04, 'lineY', seg=8, rot=(90, 0, 0), hull='none')
    for zz in (z0 + 0.45,):      # hinge strap on the hanging post
        m.bx(x0 - 0.043, x0 + 0.2, y - 0.047, y + 0.047, zz, zz + 0.05, 'steel', hull='none', cull='blr')
    m.bx(x1 - 0.043, x1 + 0.043, y - 0.047, y + 0.047, z0 + 0.95, z0 + 1.05, 'steel', hull='none', cull='blr')   # latch box


# ================================================================ the gated entrance (zone 1 landmark) [16, 6]
def gate_landmark(pal, ao):
    """Landmark_Gate: the stone-and-iron entrance across the boulevard. A planted island down the middle carries the
    gatehouse (stone base, windows all round, a hip roof with a lantern); a boom barrier on each side of it (the
    residents' lane to the east standing open, the exit lane closed); the keypad call post at the visitors' stop line;
    stone piers with lanterns at both lane edges carrying wrought-iron gates swung open; a pedestrian gate to the east.
    The approach (south, -Y) reads LARKSPUR GLEN on the gatehouse fascia; STOP is painted at both barriers."""
    m = new(pal)
    cols = []
    # the island: curb, lawn, flowers
    m.bx(-1.5, 1.5, -3.0, 3.0, 0.0, 0.15, 'curb', cull='b')
    uq(m, -1.42, 1.42, -2.92, 2.92, 0.154, 'grass')
    cols.append(wbox(-1.5, -3.0, 0.0, 1.5, 3.0, 0.15))
    flowers(m, -1.3, 1.3, -2.85, -1.9, 0.158, n=10)
    shrub(m, -0.9, 2.3, 0.4, z=0.15)
    shrub(m, 0.9, 2.4, 0.36, z=0.15)
    solid(cols, -1.3, 1.95, 0.15, 1.3, 2.75, 0.75)
    # the gatehouse booth
    bx0, bx1, by0, by1, H = -1.15, 1.15, -1.55, 1.55, 2.9
    m.bx(bx0, bx1, by0, by1, 0.15, 0.95, 'stone')
    m.bx(bx0, bx1, by0, by1, 0.95, H, 'trim')
    for (f, yy) in ((fq, by0 - 0.006), (bq, by1 + 0.006)):
        f(m, bx0 + 0.15, bx1 - 0.15, yy, 1.1, 2.45, 'iron')
        f(m, bx0 + 0.2, bx1 - 0.2, yy - 0.004 if f is fq else yy + 0.004, 1.15, 2.4, 'glass')
    for (f, xx) in ((rq, bx1 + 0.006), (lq, bx0 - 0.006)):
        f(m, xx, by0 + 0.15, by1 - 0.15, 1.1, 2.45, 'iron')
        f(m, xx + (0.004 if f is rq else -0.004), by0 + 0.2, by1 - 0.2, 1.15, 2.4, 'glass')
    # the door on the east (residents') side, a sliding service window
    rq(m, bx1 + 0.016, -0.95, -0.25, 0.95, 2.45, 'door')
    # the guard's desk and monitor seen through the south window (painted on the glass)
    fq(m, -0.75, 0.75, by0 - 0.014, 1.15, 1.35, 'woodD')
    fq(m, -0.25, 0.25, by0 - 0.018, 1.35, 1.7, 'iron')
    fq(m, -0.21, 0.21, by0 - 0.022, 1.39, 1.66, 'glassD')
    # belt course, corner boards, window sills and muntins
    TD.bx(m, bx0 - 0.035, bx1 + 0.035, by0 - 0.035, by1 + 0.035, 0.93, 0.975, 'stoneD', cull='b')
    for (cx, cy_) in ((bx0, by0), (bx1, by1), (bx0, by1), (bx1, by0)):
        sx_, sy_ = (1 if cx < 0 else -1), (1 if cy_ < 0 else -1)
        xa, xb = sorted((cx - sx_ * 0.02, cx + sx_ * 0.1))
        ya, yb = sorted((cy_ - sy_ * 0.02, cy_ + sy_ * 0.1))
    for (yy, sg) in ((by0, -1), (by1, 1)):
        a, b = sorted((yy + sg * 0.05, yy - sg * EMB))
        TD.bx(m, bx0 + 0.13, bx1 - 0.13, a, b, 1.04, 1.1, 'stoneD', cull='blr' + ('k' if sg < 0 else 'f'))
        for xx in (0.0,):
            a2, b2 = sorted((yy + sg * 0.007, yy + sg * 0.026))
            TD.bx(m, xx - 0.012, xx + 0.012, a2, b2, 1.15, 2.4, 'iron', cull='tblr' + ('k' if sg < 0 else 'f'))
            a3, b3 = sorted((yy + sg * 0.007, yy + sg * 0.02))
            TD.bx(m, bx0 + 0.2, xx - 0.012, a3, b3, 1.765, 1.79, 'iron', cull='tblr' + ('k' if sg < 0 else 'f'))
            TD.bx(m, xx + 0.012, bx1 - 0.2, a3, b3, 1.765, 1.79, 'iron', cull='tblr' + ('k' if sg < 0 else 'f'))
    # roof: a hip roof with a lantern
    m.bx(bx0 - 0.3, bx1 + 0.3, by0 - 0.3, by1 + 0.3, H, H + 0.3, 'trim')
    txt(m, 'LARKSPUR GLEN', 0.0, by0 - 0.305, H + 0.15, 0.17, 'iron', font='serif', maxw=2.4)
    txt(m, 'RESIDENTS & GUESTS', 0.0, by1 + 0.305, H + 0.15, 0.15, 'iron', face='y+', font='display', maxw=2.4)
    m.fan((0, 0, H + 0.3), H + 1.4, 1.85 * 1.41, 4, ['shingle'], rot=math.pi / 4)
    for (hx, hy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):     # hip rolls
        m.bm_((hx * 0.06, hy * 0.06, H + 1.36), (hx * 1.78, hy * 1.78, H + 0.36), 0.08, 'shingleD', hull='none')
    m.bx(-0.28, 0.28, -0.28, 0.28, H + 0.95, H + 1.5, 'trim')
    m.fan((0, 0, H + 1.5), H + 1.9, 0.45, 4, ['doorT'], rot=math.pi / 4)
    m.cy((0, 0, H + 1.9), 0.02, 0.02, 0.4, 'iron', seg=4, hull='none')
    m.bx(-0.02, 0.22, -0.02, 0.02, H + 2.15, H + 2.2, 'iron', hull='none')       # weathervane arrow
    solid(cols, bx0 - 0.3, by0 - 0.3, 0.15, bx1 + 0.3, by1 + 0.3, H + 0.3)
    # boom barriers: housings on the island ends, arms over the lanes (east lane open: arm up)
    for sx in (-1, 1):
        x = sx * 1.75
        y = -2.4
        m.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0.0, 1.05, 'lineY')
        fq(m, x - 0.18, x + 0.18, y - 0.224, 0.75, 0.95, 'iron')
        solid(cols, x - 0.22, y - 0.22, 0.0, x + 0.22, y + 0.22, 1.05)
        TD.bx(m, x - 0.27, x + 0.27, y - 0.27, y + 0.27, 0.0, 0.035, 'steel', cull='b')       # base plate
        for (bx_, by_) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            TD.bolt_plate(m, x + bx_ * 0.245, y + by_ * 0.245, 0.035, '+z', 'chrome', s=0.03, out=0.012, cull='bfklr')
        TD.bx(m, x - 0.235, x + 0.235, y - 0.235, y + 0.235, 1.047, 1.085, 'iron', cull='b')   # lid
        TD.bx(m, x - 0.04, x + 0.04, y - 0.236, y - 0.217, 0.5, 0.58, 'chrome', cull='tblrk')  # lock
        if sx < 0:   # exit lane: arm down across the lane, red and white bands, a rest post at the far side
            for k in range(8):
                a = x - 0.2 - k * 0.48
                m.bx(a - 0.48, a, y - 0.05, y + 0.05, 0.9, 1.0, 'red' if k % 2 else 'trim', hull='full')
            m.bx(-5.55, -5.35, y - 0.1, y + 0.1, 0.0, 0.9, 'iron')
            solid(cols, -5.55, y - 0.1, 0.0, -5.35, y + 0.1, 0.9)
            solid(cols, x - 0.2 - 3.84, y - 0.06, 0.88, x - 0.2, y + 0.06, 1.02)
        else:        # residents' lane: the arm stands up
            for k in range(8):
                z = 1.05 + k * 0.48
                m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, z, z + 0.48, 'red' if k % 2 else 'trim', hull='full')
            solid(cols, x - 0.06, y - 0.06, 1.05, x + 0.06, y + 0.06, 4.9)
        txt(m, 'STOP', x + sx * 2.0, y - 0.75, 0.006, 0.55, 'lineW', face='up', font='display', maxw=2.2)
        uq(m, x + sx * 0.25, x + sx * 3.85, y - 0.35, y - 0.25, 0.006, 'lineW')
    # keypad call post at the visitors' (east) lane, facing the driver (+X side)
    m.cy((1.95, -0.6, 0.0), 0.06, 0.06, 1.2, 'iron', seg=6)
    m.bm_((1.95, -0.6, 1.2), (2.25, -0.6, 1.35), 0.07, 'iron')
    m.bx(2.22, 2.42, -0.78, -0.42, 1.12, 1.55, 'iron')
    rq(m, 2.424, -0.74, -0.46, 1.16, 1.51, 'steel')
    for r in range(3):
        for c in range(3):
            rq(m, 2.428, -0.72 + c * 0.09, -0.66 + c * 0.09, 1.2 + r * 0.07, 1.25 + r * 0.07, 'trim')
    rq(m, 2.428, -0.72, -0.48, 1.43, 1.49, 'glassL')
    solid(cols, 1.88, -0.82, 0.0, 2.45, -0.38, 1.55)
    # stone piers at the lane edges and on the island's north end, iron gate leaves swung open along the lanes
    for sx in (-1, 1):
        stone_pier(m, cols, sx * 5.9, 2.4, 0.8, 2.5)
        stone_pier(m, cols, sx * 1.1, 2.5, 0.7, 1.9, lantern=False)
        for (xh, xd) in ((sx * 5.45, sx * 5.45), (sx * 1.5, sx * 1.5)):
            m.parent = Matrix.Translation((xh, 2.55, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
            iron_leaf(m, 0.05, 1.95, 0.0, 0.05, 1.9)
            m.parent = Matrix.Identity(4)
            solid(cols, xh - 0.05, 2.55, 0.0, xh + 0.05, 4.55, 2.0)
    # the pedestrian gate (east): a pier pair with an iron arch, the leaf open
    stone_pier(m, cols, 7.65, 2.4, 0.6, 2.1, lantern=True)
    m.parent = Matrix.Translation((7.3, 2.55, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    iron_leaf(m, 0.05, 1.1, 0.0, 0.05, 1.6, arch=0.1)
    m.parent = Matrix.Identity(4)
    solid(cols, 7.25, 2.55, 0.0, 7.35, 3.65, 1.8)
    for k in range(9):
        a0, a1 = math.pi * k / 9, math.pi * (k + 1) / 9
        r = 0.88
        m.bm_((6.78 + r * math.cos(a0), 2.4, 2.2 + r * 0.5 * math.sin(a0)), (6.78 + r * math.cos(a1), 2.4, 2.2 + r * 0.5 * math.sin(a1)), 0.05 if k % 2 else 0.038, 'iron', hull='none')
    m.bx(6.0, 7.56, 2.37, 2.43, 2.15, 2.2, 'iron', hull='none')
    # wing walls: stone base with iron railing, each side of the outer piers to the footprint edge
    for (x0, x1) in ((-8.0, -6.3), (7.95, 8.0)):
        if x1 - x0 < 0.2:
            continue
        m.bx(x0, x1, 2.2, 2.6, 0.0, 0.9, 'stone', cull='b')
        m.bx(x0, x1, 2.15, 2.65, 0.9, 1.02, 'stoneD')
        m.bx(x0, x1, 2.37, 2.43, 2.05, 2.1, 'iron')
        pickets_x(m, x0 + 0.05, x1 - 0.05, 2.4, 1.02, 2.2, 0.14, 0.028, 'iron')
        solid(cols, x0, 2.15, 0.0, x1, 2.65, 2.2)
    # lane signs on the island's south end
    for (sx, word) in ((1, 'RESIDENTS'), (-1, 'EXIT')):
        x = sx * 1.0
        m.cy((x, -2.75, 0.15), 0.03, 0.03, 1.5, 'iron', seg=4, hull='none')
        m.bx(x - 0.42, x + 0.42, -2.79, -2.71, 1.4, 1.75, 'doorG')
        txt(m, word, x, -2.794, 1.575, 0.14, 'trim', font='display', maxw=0.74)
    make('Landmark_Gate', m, ao, cols=cols)


def entry_sign(pal, ao):
    """EntrySign [8, 2]: the community's name on a low curved stone wall in a flower bed, lanterns at both ends"""
    m = new(pal)
    cols = []
    n = 5
    pts = []
    for i in range(n + 1):
        x = -3.4 + 6.8 * i / n
        pts.append((x, 0.25 - 0.22 * (1 - (x / 3.4) ** 2)))
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        h = 1.25 + 0.35 * math.sin(math.pi * (i + 0.5) / n)
        m.bx(xa, xb, ya - 0.2, ya + 0.2, 0.0, h, 'stone', cull='b')
        m.bx(xa, xb, ya - 0.24, ya + 0.24, h, h + 0.08, 'stoneD')
    m.bx(-2.3, 2.3, -0.26, -0.2, 0.62, 1.32, 'trim', cull='k')
    txt(m, 'LARKSPUR GLEN', 0.0, -0.264, 1.05, 0.32, 'iron', font='serif', maxw=4.3)
    txt(m, 'EST. 2019', 0.0, -0.264, 0.76, 0.12, 'doorG', font='display', maxw=3.5)
    for x in (-3.55, 3.55):
        stone_pier(m, cols, x, 0.25, 0.5, 1.7)
    m.bx(-3.8, 3.8, -0.95, -0.27, 0.0, 0.18, 'stoneD', cull='b')
    uq(m, -3.75, 3.75, -0.9, -0.27, 0.184, 'woodD')
    flowers(m, -3.6, 3.6, -0.85, -0.35, 0.188, n=10, s=0.07)
    for x in (-2.4, 2.4):
        shrub(m, x, -0.6, 0.24, z=0.18)
    solid(cols, -3.4, -0.27, 0.0, 3.4, 0.45, 1.6)
    cols.append(wbox(-3.8, -0.95, 0.0, 3.8, -0.27, 0.18))
    make('EntrySign', m, ao, cols=cols)


# ================================================================ the clubhouse [14, 11] (walk-in)
CX, CY0, CY1, CH = 7.0, -4.3, 5.5, 3.6


def clubhouse(pal, ao):
    """Clubhouse: one storey of white clapboard under a hip roof with a cupola; a portico with double doors to the
    parking (front), French doors onto the pool terrace (back). Inside: the residents' lounge (sofas round a
    fireplace on the west wall), a billiards table in the middle, a kitchenette on the east wall, the front desk."""
    m = new(pal)
    cols = []
    T = 0.25
    fd = (-0.8, 0.8)
    bd = [(-3.6, -2.0), (2.0, 3.6)]
    hf = [(fd[0], fd[1], 0.0, 2.6)]
    hb = [(a, b, 0.0, 2.6) for (a, b) in bd]
    # walls round the openings (no shell on the faces with openings, outlined side walls)
    for (a, b, p, q) in clip_rects(-CX + T, CX - T, 0.0, CH, hf):
        m.bx(a, b, CY0, CY0 + T, p, q, 'sidC', hull='none', cull='k' + ('b' if p < 0.01 else ''))
        solid(cols, a, CY0, p, b, CY0 + T, q)
    for (a, b, p, q) in clip_rects(-CX + T, CX - T, 0.0, CH, hb):
        m.bx(a, b, CY1 - T, CY1, p, q, 'sidC', hull='none', cull='f' + ('b' if p < 0.01 else ''))
        solid(cols, a, CY1 - T, p, b, CY1, q)
    for sx in (-1, 1):
        a, b = (-CX, -CX + T) if sx < 0 else (CX - T, CX)
        m.bx(a, b, CY0, CY1, 0.0, CH, 'sidC', cull=('r' if sx < 0 else 'l') + 'b')
        solid(cols, a, CY0, 0.0, b, CY1, CH)
    # clapboard lines and corner boards outside; windows all round
    for (fr, holes, L) in ((frame_front(), hf, None), (frame_back(), [(-b, -a, p, q) for (a, b, p, q) in hb], None)):
        m.parent = Matrix.Translation((0, CY0, 0)) if fr is None else (Matrix.Translation((0, CY0 - FW, 0)) @ fr if holes is hf else Matrix.Translation((0, CY1 - BW, 0)) @ fr)
        for (a, b, p, q) in clip_rects(-CX, CX, 0.35, CH, holes):
            z = p + 0.3
            while z < q - 0.05:
                fz(m, a, b, z - 0.03, z, 0.004, 'trimD')
                z += 0.3
        fz(m, -CX, CX, 0.0, 0.35, 0.006, 'stone')
        m.parent = Matrix.Identity(4)
    m.parent = Matrix.Translation((0, CY0 - FW, 0)) @ frame_front()
    for x in (-5.4, -2.8, 2.8, 5.4):
        window(m, x - 0.55, x + 0.55, 0.9, 2.6, shutters=True)
    door(m, fd[0], fd[1], 0.0, 2.6, open_=True)
    m.parent = Matrix.Translation((0, CY1 - BW, 0)) @ frame_back()
    for x in (-5.4, 0.0, 5.4):
        window(m, x - 0.55, x + 0.55, 0.9, 2.6, shutters=True)
    for (a, b) in bd:
        door(m, -b, -a, 0.0, 2.6, open_=True, transom=False)
    for sx in (-1, 1):
        m.parent = Matrix.Translation((sx * CX, 0.6, 0)) @ Matrix.Rotation(sx * math.pi / 2, 4, 'Z')
        for x in (-3.0, 3.0):
            window(m, x - 0.55, x + 0.55, 0.9, 2.6, shutters=False)
        fz(m, -4.9, 4.9, 0.0, 0.35, 0.006, 'stone')
    m.parent = Matrix.Identity(4)
    # hip roof with a cupola and its weathervane
    m.bx(-CX - 0.3, CX + 0.3, CY0 - 0.3, CY1 + 0.3, CH, CH + 0.22, 'trim')
    h = 2.4
    yc = (CY0 + CY1) / 2
    hw, hd = CX + 0.3, (CY1 - CY0) / 2 + 0.3
    rv = [(-hw, yc - hd, CH + 0.22), (hw, yc - hd, CH + 0.22), (hw, yc + hd, CH + 0.22), (-hw, yc + hd, CH + 0.22)]
    ra, rb = (-hw + hd, yc, CH + 0.22 + h), (hw - hd, yc, CH + 0.22 + h)
    for tri in ((rv[0], rv[1], rb, ra), (rv[2], rv[3], ra, rb)):
        poly(m, list(tri), 'shingle', (0, -1 if tri[0] is rv[0] else 1, 1))
    for tri in ((rv[3], rv[0], ra), (rv[1], rv[2], rb)):
        poly(m, list(tri), 'shingle', (-1 if tri[0] is rv[3] else 1, 0, 1))
    m.bx(ra[0], rb[0], yc - 0.08, yc + 0.08, CH + 0.22 + h - 0.06, CH + 0.22 + h + 0.06, 'shingleD')
    m.bx(-0.55, 0.55, yc - 0.55, yc + 0.55, CH + 0.22 + h - 0.6, CH + 0.22 + h + 0.7, 'trim')
    for (f, yy) in ((fq, yc - 0.556), (bq, yc + 0.556)):
        f(m, -0.35, 0.35, yy, CH + h + 0.0, CH + h + 0.75, 'glassD')
    m.fan((0, yc, CH + 0.22 + h + 0.7), CH + 0.22 + h + 1.3, 0.8, 4, ['doorG'], rot=math.pi / 4)
    m.cy((0, yc, CH + h + 1.52), 0.02, 0.02, 0.5, 'iron', seg=4, hull='none')
    m.bx(-0.3, 0.3, yc - 0.015, yc + 0.015, CH + h + 1.85, CH + h + 1.9, 'iron', hull='none')
    m.bx(-0.015, 0.015, yc - 0.2, yc + 0.2, CH + h + 1.75, CH + h + 1.78, 'iron', hull='none')
    # portico: columns and a pediment over the front doors, the sign
    py0 = -5.5
    for x in (-1.6, 1.6):
        post(m, x, py0 + 0.3, 0.12, 3.0, 0.13, 'trim', seg=8)
        solid(cols, x - 0.14, py0 + 0.16, 0.0, x + 0.14, py0 + 0.44, 3.0)
    m.bx(-1.9, 1.9, py0, CY0, 0.0, 0.12, 'stone', cull='b')
    cols.append(wbox(-1.9, py0, 0.0, 1.9, CY0, 0.12))
    m.bx(-1.95, 1.95, py0 - 0.05, CY0, 3.0, 3.3, 'trim')
    m.prism([(py0 - 0.05, 3.3), (CY0, 3.3), (CY0, 4.3)], -1.95, 1.95, ['shingle'], hull='full', skip=(1,))
    m.parent = Matrix.Translation((0, py0 - 0.05 - FW, 0)) @ frame_front()
    poly(m, [(-1.7, -0.004, 3.35), (1.7, -0.004, 3.35), (0.0, -0.004, 3.95)], 'trim', (0, -1, 0))
    m.parent = Matrix.Identity(4)
    txt(m, 'CLUBHOUSE', 0.0, py0 - 0.056, 3.15, 0.2, 'iron', font='cond', maxw=3.2)
    # inside: floor, ceiling with beams, the lounge, billiards, kitchenette, the front desk
    IXc, IY0c, IY1c = CX - T, CY0 + T, CY1 - T
    uq(m, -IXc, IXc, IY0c, IY1c, 0.012, 'wood')
    for k in range(1, 14):
        x = -IXc + k * 2 * IXc / 14
        uq(m, x - 0.01, x + 0.01, IY0c, IY1c, 0.016, 'woodD')
    dq(m, -IXc, IXc, IY0c, IY1c, CH - 0.01, 'plaster')
    for k in range(1, 5):
        y = IY0c + k * (IY1c - IY0c) / 5
        m.bx(-IXc, IXc, y - 0.1, y + 0.1, CH - 0.3, CH - 0.01, 'woodD', hull='none', cull='t')
    for (z0, z1) in ((0.0, CH),):
        rq(m, -IXc, IY0c, IY1c, z0, z1, 'sidY')
        lq(m, IXc, IY0c, IY1c, z0, z1, 'sidY')
    for (a, b, p, q) in clip_rects(-IXc, IXc, 0.0, CH, hf):
        bq(m, a, b, IY0c, p, q, 'sidY')
    for (a, b, p, q) in clip_rects(-IXc, IXc, 0.0, CH, hb):
        fq(m, a, b, IY1c, p, q, 'sidY')
    for x in (-5.4, -2.8, 2.8, 5.4):
        bq(m, x - 0.55, x + 0.55, IY0c + 0.006, 0.9, 2.6, 'glass')
    for x in (-5.4, 0.0, 5.4):
        fq(m, x - 0.55, x + 0.55, IY1c - 0.006, 0.9, 2.6, 'glass')
    # fireplace on the west wall, sofas round it
    m.bx(-IXc, -IXc + 0.5, -0.9, 0.9, 0.0, 1.4, 'stone')
    m.bx(-IXc, -IXc + 0.6, -1.0, 1.0, 1.4, 1.52, 'woodD')
    m.bx(-IXc, -IXc + 0.35, -0.7, 0.7, 1.52, CH - 0.3, 'stone', hull='none')
    rq(m, -IXc + 0.504, -0.5, 0.5, 0.15, 0.95, 'iron')
    rq(m, -IXc + 0.508, -0.35, 0.35, 0.2, 0.55, 'orange')
    solid(cols, -IXc, -1.0, 0.0, -IXc + 0.6, 1.0, 1.52)
    rug(m, -5.6, -2.6, -1.6, 1.6, 0.012, 'fabricR', 'stuP')
    sofa(m, cols, -5.7, -3.5, -2.25, -1.4, 0.0, 'fabric', back='-y')
    sofa(m, cols, -5.7, -3.5, 1.4, 2.25, 0.0, 'fabric', back='+y')
    table(m, cols, -5.0, -4.0, -0.5, 0.5, 0.0, h=0.42, top='woodD')
    # billiards table
    m.bx(-1.1, 1.1, -0.65, 0.65, 0.62, 0.82, 'woodD')
    uq(m, -0.98, 0.98, -0.53, 0.53, 0.824, 'doorG')
    for (x, y) in ((-0.95, -0.5), (0.95, -0.5), (-0.95, 0.5), (0.95, 0.5)):
        m.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 0.62, 'woodD', hull='none', cull='tb')
    for (x, y, c) in ((0.3, 0.1, 'trim'), (-0.4, -0.2, 'red'), (-0.5, 0.15, 'doorY'), (-0.3, 0.05, 'fabric')):
        m.sp((x, y, 0.86), 0.035, c, seg=(5, 3), hull='none')
    solid(cols, -1.1, -0.65, 0.5, 1.1, 0.65, 0.82)
    for (x, y) in ((-0.95, -0.5), (0.95, -0.5), (-0.95, 0.5), (0.95, 0.5)):
        solid(cols, x - 0.07, y - 0.07, 0.0, x + 0.07, y + 0.07, 0.5)
    # kitchenette on the east wall, a bar with stools; the front desk; a notice board
    m.bx(IXc - 0.6, IXc, -1.5, 3.4, 0.0, 0.86, 'doorT')
    m.bx(IXc - 0.63, IXc, -1.53, 3.43, 0.86, 0.92, 'stone')
    m.bx(IXc - 0.35, IXc, -1.5, 3.4, 1.45, 2.2, 'doorT')
    for k in range(1, 8):
        y = -1.5 + k * 0.6125
        lq(m, IXc - 0.604, y - 0.008, y + 0.008, 0.08, 0.8, 'iron')
        lq(m, IXc - 0.354, y - 0.008, y + 0.008, 1.5, 2.15, 'iron')
    uq(m, IXc - 0.5, IXc - 0.1, 0.1, 0.7, 0.924, 'steel')
    m.bx(IXc - 0.5, IXc - 0.15, 2.4, 2.9, 0.92, 1.2, 'iron')         # coffee machine
    solid(cols, IXc - 0.63, -1.53, 0.0, IXc, 3.43, 0.92)
    solid(cols, IXc - 0.35, -1.5, 1.45, IXc, 3.4, 2.2)
    m.bx(3.2, 3.7, -1.2, 2.6, 0.0, 1.0, 'woodD')
    m.bx(3.15, 3.75, -1.25, 2.65, 1.0, 1.06, 'stone')
    solid(cols, 3.15, -1.25, 0.0, 3.75, 2.65, 1.06)
    for y in (-0.6, 0.4, 1.4, 2.2):
        stool(m, cols, 2.75, y, 0.0)
    m.bx(-2.6, -1.2, -3.85, -3.35, 0.0, 1.05, 'woodD')
    m.bx(-2.65, -1.15, -3.9, -3.3, 1.05, 1.1, 'stone')
    m.bx(-2.2, -1.8, -3.55, -3.45, 1.1, 1.4, 'iron', hull='none')
    solid(cols, -2.65, -3.9, 0.0, -1.15, -3.3, 1.1)
    bq(m, 1.0, 2.1, IY0c + 0.006, 1.2, 2.2, 'woodL')
    for (x, z, c) in ((1.25, 1.9, 'trim'), (1.6, 1.55, 'sidY'), (1.85, 1.95, 'trim')):
        bq(m, x - 0.15, x + 0.15, IY0c + 0.01, z - 0.2, z + 0.15, c)
    picture(m, -IXc, -3.2, 2.0, 1.2, 0.8, 'leaf', face='+x')
    picture(m, -IXc, 3.4, 2.0, 1.0, 0.7, 'water', face='+x')
    plant(m, cols, -6.3, -3.6, 0.0, h=1.4)
    plant(m, cols, 6.3, -3.6, 0.0, h=1.4)
    # the open door leaves
    for x in fd:
        a, b = srt(x, x + (0.05 if x < 0 else -0.05))
        m.bx(a, b, IY0c + 0.02, IY0c + 0.8, 0.0, 2.55, 'door')
        solid(cols, a, IY0c + 0.02, 0.0, b, IY0c + 0.8, 2.55)
    for (a0, b0) in bd:
        for x in (a0, b0):
            a, b = srt(x, x + (0.05 if x == a0 else -0.05))
            m.bx(a, b, IY1c - 0.8, IY1c - 0.02, 0.0, 2.55, 'trim')
            solid(cols, a, IY1c - 0.8, 0.0, b, IY1c - 0.02, 2.55)
    # back terrace step
    m.bx(-4.2, 4.2, CY1, CY1 + 0.5, 0.0, 0.12, 'stone', cull='bf')
    cols.append(wbox(-4.2, CY1, 0.0, 4.2, CY1 + 0.5, 0.12))
    make('Clubhouse', m, ao, cols=cols)


# ================================================================ pool and deck furniture
def pool(pal, ao):
    """Pool [12, 6]: an in-ground pool with a stone coping, a tiled waterline band, lane lines and depth marks, a
    ladder and a handrail. Its one box is a movement-only bound over the water (theme kind 'bound'): nobody walks on
    the water, shots and sight lines pass."""
    m = new(pal)
    X, Y = 5.6, 2.6
    for (a, b, p, q) in ((-6.0, 6.0, -3.0, -Y), (-6.0, 6.0, Y, 3.0), (-6.0, -X, -Y, Y), (X, 6.0, -Y, Y)):
        m.bx(a, b, p, q, 0.0, 0.07, 'trim', hull='none', cull='b')
    uq(m, -X, X, -Y, Y, 0.02, 'water')
    for (a, b, p, q) in ((-X, X, -Y, -Y + 0.25), (-X, X, Y - 0.25, Y), (-X, -X + 0.25, -Y + 0.25, Y - 0.25), (X - 0.25, X, -Y + 0.25, Y - 0.25)):
        uq(m, a, b, p, q, 0.024, 'waterL')
    for y in (-1.3, 0.0, 1.3):
        uq(m, -X + 1.0, X - 1.0, y - 0.07, y + 0.07, 0.024, 'glassD')
    for (x, word) in ((-4.6, '3 FT'), (0.0, '4 FT'), (4.6, '6 FT')):
        txt(m, word, x, -2.8, 0.074, 0.16, 'glassD', face='up', font='display', maxw=0.8)
    txt(m, 'NO DIVING', -1.8, 2.8, 0.074, 0.16, 'red', face='up', font='display', maxw=1.4)
    for x in (-4.0, -3.5):
        m.cy((x, -2.75, 0.07), 0.025, 0.025, 0.8, 'chrome', seg=5, hull='none')
        m.bm_((x, -2.75, 0.87), (x, -2.45, 0.87), 0.05, 'chrome', hull='none')
        m.cy((x, -2.45, 0.02), 0.025, 0.025, 0.85, 'chrome', seg=5, hull='none')
    make('Pool', m, ao, cols=[box(-X, -Y, 0.0, X, Y, 1.2)])


def lounger(pal, ao):
    """Lounger [1, 2]: a white resin sun lounger with a raised back and a striped towel"""
    m = new(pal)
    m.bx(-0.33, 0.33, -0.95, 0.55, 0.28, 0.36, 'trim')
    for (x, y) in ((-0.28, -0.88), (0.28, -0.88), (-0.28, 0.48), (0.28, 0.48)):
        m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.28, 'trimD', hull='none', cull='tb')
    m.box((0, 0.72, 0.56), (0.66, 0.5, 0.06), 'trim', rot=(48, 0, 0), bevel=False)
    m.bx(-0.26, 0.26, -0.7, 0.3, 0.36, 0.38, 'doorT', hull='none')
    m.bx(-0.26, 0.26, -0.45, -0.3, 0.38, 0.385, 'trim', hull='none', cull='b')
    make('Lounger', m, ao, cols=[box(-0.33, -0.95, 0, 0.33, 0.55, 0.38), box(-0.33, 0.55, 0, 0.33, 0.9, 0.78)])


def umbrella_table(pal, ao):
    """PatioTable [2, 2]: a round patio table under a striped market umbrella, two chairs"""
    m = new(pal)
    cols = []
    m.cy((0, 0, 0.0), 0.3, 0.3, 0.03, 'iron', seg=8, hull='none')
    m.cy((0, 0, 0.03), 0.04, 0.04, 0.68, 'iron', seg=5, hull='none')
    m.cy((0, 0, 0.71), 0.48, 0.48, 0.04, 'trim', seg=12)
    m.cy((0, 0, 0.75), 0.025, 0.025, 1.65, 'trim', seg=4, hull='none')
    m.fan((0, 0, 2.15), 2.55, 1.15, 8, ['doorT', 'trim'], rot=math.pi / 8)
    solid(cols, -0.48, -0.48, 0.45, 0.48, 0.48, 0.75)
    solid(cols, -0.06, -0.06, 0.0, 0.06, 0.06, 0.45)
    for (x, y, f) in ((-0.62, -0.38, '+x'), (0.62, 0.38, '-x')):
        chair(m, cols, x, y, 0.0, c='trim', face=f)
    make('PatioTable', m, ao, cols=cols)


def pool_fence(pal, ao):
    """pool fence (theme `links`, run along Blender Y = game Z): black aluminium pickets, 1.25 m; PoolFence (half
    module from the cell centre toward -Y), PoolFenceFull, PoolPost; PoolGate (a gate leaf standing open, along X)"""
    for (name, y0, y1) in (('PoolFence', -0.5, -0.05), ('PoolFenceFull', -0.5, 0.5)):
        m = new(pal)
        for z in (0.1, 1.15):
            m.bx(-0.025, 0.025, y0, y1, z, z + 0.05, 'iron')
        pickets_y(m, y0, y1, 0.0, 0.15, 1.15, 0.12, 0.022, 'iron')
        make(name, m, ao, cols=[box(-0.05, y0, 0.0, 0.05, y1, 1.25)])
    m = new(pal)
    m.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 1.32, 'iron')
    m.bx(-0.07, 0.07, -0.07, 0.07, 1.32, 1.36, 'iron')
    make('PoolFencePost', m, ao, cols=[box(-0.06, -0.06, 0.0, 0.06, 0.06, 1.36)])
    m = new(pal)
    for x in (-0.5, 0.5):
        m.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.0, 1.36, 'iron')
    m.parent = rz(-80, -0.45, 0.0)
    for z in (0.1, 1.15):
        m.bx(0.0, 0.9, -0.025, 0.025, z, z + 0.05, 'iron')
    pickets_x(m, 0.0, 0.9, 0.0, 0.15, 1.15, 0.12, 0.022, 'iron')
    m.bx(-0.01, 0.2, -0.03, 0.03, 0.65, 0.7, 'steel', hull='none', cull='blr')      # hinge strap along the leaf
    m.parent = Matrix.Identity(4)
    m.bx(0.434, 0.452, -0.03, 0.03, 0.95, 1.05, 'steel', hull='none', cull='tblr')      # latch box on the strike post
    make('PoolGate', m, ao, cols=[box(-0.56, -0.06, 0.0, -0.44, 0.06, 1.36), box(0.44, -0.06, 0.0, 0.56, 0.06, 1.36),
                                    box(-0.5, -0.92, 0.0, -0.22, 0.0, 1.25)])


def pool_sign(pal, ao):
    """PoolSign [1, 1]: POOL RULES board on two posts and a life ring on a hook"""
    m = new(pal)
    for x in (-0.35, 0.35):
        m.bx(x - 0.04, x + 0.04, -0.04, 0.04, 0.0, 1.9, 'trim')
    m.bx(-0.45, 0.45, -0.06, -0.02, 1.0, 1.85, 'trim')
    txt(m, 'POOL RULES', 0.0, -0.064, 1.72, 0.1, 'doorN', font='display', maxw=0.8)
    for k in range(5):
        fq(m, -0.36, 0.2 - 0.06 * (k % 2), -0.064, 1.15 + k * 0.1, 1.18 + k * 0.1, 'shingle')
    m.cy((0.0, 0.06, 0.55), 0.26, 0.26, 0.08, 'red', seg=10, rot=(90, 0, 0))
    make('PoolSign', m, ao, cols=[box(-0.45, -0.08, 0.0, 0.45, 0.14, 1.9)])


# ================================================================ mailbox kiosk [4, 3]
def mail_kiosk(pal, ao):
    """MailKiosk: a cluster mailbox kiosk under a little hip-roofed shelter: two cluster box units back to back
    (rows of small numbered doors, parcel lockers), four posts, a lamp, a bin for flyers"""
    m = new(pal)
    cols = []
    for (x, y) in ((-1.75, -1.25), (1.75, -1.25), (-1.75, 1.25), (1.75, 1.25)):
        m.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.0, 2.55, 'trim')
        solid(cols, x - 0.08, y - 0.08, 0.0, x + 0.08, y + 0.08, 2.55)
    m.bx(-1.95, 1.95, -1.45, 1.45, 2.55, 2.75, 'trim')
    for sg in (-1, 1):       # drip flange along the beam's foot
        a, b = sorted((sg * 1.45 - sg * EMB, sg * 1.485))
        TD.bx(m, -1.945, 1.945, a, b, 2.535, 2.57, 'trimD', cull='blr' + ('k' if sg < 0 else 'f'))
        a, b = sorted((sg * 1.95 - sg * EMB, sg * 1.987))
        TD.bx(m, a, b, -1.44, 1.44, 2.535, 2.57, 'trimD', cull='bfk' + ('r' if sg < 0 else 'l'))
    m.fan((0, 0, 2.75), 3.45, 2.6, 4, ['shingle'], rot=math.pi / 4)
    m.bx(-1.9, 1.9, -1.4, 1.4, 0.0, 0.1, 'stone', hull='none', cull='b')
    m.bx(-1.3, 1.3, -0.42, 0.42, 0.1, 0.35, 'stoneD')
    m.bx(-1.25, 1.25, -0.38, 0.38, 0.35, 1.85, 'doorN')
    m.bx(-1.3, 1.3, -0.42, 0.42, 1.85, 1.95, 'doorN')
    for (f, yy, s) in ((fq, -0.384, -1), (bq, 0.384, 1)):
        for c in range(6):
            x0 = -1.15 + c * 0.32
            for r in range(5):
                z0 = 0.9 + r * 0.18
                f(m, x0, x0 + 0.28, yy + s * 0.0, z0, z0 + 0.15, 'steel')
                f(m, x0 + 0.2, x0 + 0.25, yy + s * 0.004, z0 + 0.06, z0 + 0.09, 'iron')
        for c in range(3):
            x0 = -1.15 + c * 0.64
            f(m, x0, x0 + 0.6, yy, 0.42, 0.85, 'sidG')
        f(m, -1.0, 1.0, yy + s * 0.004, 1.76, 1.81, 'trim')
        a, b = sorted((yy + s * 0.012 + s * 0.003, yy - s * 0.003))
        for c in range(3):
            TD.bx(m, -1.15 + c * 0.64 + 0.26, -1.15 + c * 0.64 + 0.34, a, b, 0.6, 0.64, 'chrome', cull='tblr' + ('k' if s < 0 else 'f'))   # parcel locker pulls
        a, b = sorted((s * 0.455 - s * EMB, s * 0.417))
        TD.bx(m, -1.295, 1.295, a, b, 1.947, 1.98, 'steel', cull='blr' + ('k' if s < 0 else 'f'))   # drip hood
    txt(m, 'LARKSPUR GLEN', 0.0, -1.454, 2.65, 0.12, 'iron', font='display', maxw=2.2)
    solid(cols, -1.3, -0.42, 0.0, 1.3, 0.42, 1.95)
    m.bx(1.35, 1.65, -0.2, 0.2, 0.0, 0.75, 'doorG')
    TD.bx(m, 1.34, 1.66, -0.21, 0.21, 0.745, 0.79, 'steel', cull='b')
    solid(cols, 1.35, -0.2, 0.0, 1.65, 0.2, 0.75)
    make('MailKiosk', m, ao, cols=cols)


# ================================================================ playground and park
def play_structure(pal, ao):
    """Playground [8, 6]: two play towers (decks at 1.2 m under canopy roofs) joined by a chain bridge, stairs up the
    west tower, a wavy slide down the east one, a climbing wall, a steering wheel and a telescope panel. Decks, bridge
    and stairs are walkable (robots climb after you); a rubber-mulch pad under it all."""
    m = new(pal)
    cols = []
    D = 1.2
    uq(m, -4.0, 4.0, -3.0, 3.0, 0.012, 'woodD')
    for k in range(9):
        x = -3.6 + k * 0.9
        uq(m, x - 0.2, x + 0.2, -2.8 + (k % 3) * 0.4, -2.6 + (k % 3) * 0.4, 0.016, 'shingleD')
    for (cx, roofc) in ((-2.2, 'doorY'), (2.2, 'doorT')):
        x0, x1, y0, y1 = cx - 1.0, cx + 1.0, -0.6, 1.4
        m.bx(x0, x1, y0, y1, D - 0.12, D, 'woodL')
        cols.append(wbox(x0, y0, D - 0.12, x1, y1, D))
        for (x, y) in ((x0 + 0.06, y0 + 0.06), (x1 - 0.06, y0 + 0.06), (x0 + 0.06, y1 - 0.06), (x1 - 0.06, y1 - 0.06)):
            m.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, D + 1.7, 'red')
            solid(cols, x - 0.07, y - 0.07, 0.0, x + 0.07, y + 0.07, D + 1.7)
        m.fan((cx, (y0 + y1) / 2, D + 1.7), D + 2.5, 1.55, 4, [roofc, 'trim'], rot=math.pi / 4)
        # rails round the deck except the openings (bridge side, stair / slide side)
        for (a, b, yy) in ((x0, x1, y1 - 0.05),):
            m.bx(a, b, yy - 0.04, yy + 0.04, D + 0.8, D + 0.88, 'doorG')
            pickets_x(m, a + 0.15, b - 0.15, yy, D, D + 0.8, 0.14, 0.04, 'doorG')
            solid(cols, a, yy - 0.05, D, b, yy + 0.05, D + 0.88)
    # chain bridge between the towers (walkable planks with rope rails)
    for k in range(10):
        x = -1.2 + 0.12 + k * 0.24
        m.bx(x - 0.1, x + 0.1, -0.1, 0.9, D - 0.1, D - 0.04, 'woodL', hull='full')
    cols.append(wbox(-1.2, -0.1, D - 0.12, 1.2, 0.9, D - 0.04))
    for y in (-0.12, 0.92):
        m.bx(-1.2, 1.2, y - 0.025, y + 0.025, D + 0.75, D + 0.8, 'iron')
        for k in range(6):
            x = -1.0 + k * 0.4
            m.bx(x - 0.012, x + 0.012, y - 0.012, y + 0.012, D - 0.05, D + 0.75, 'iron', hull='none', cull='tb')
        solid(cols, -1.2, y - 0.04, D - 0.04, 1.2, y + 0.04, D + 0.8)
    # stairs up the west tower (from the south, 4 risers of 0.3 on 0.5 treads)
    for k in range(4):
        y = -0.6 - (4 - k) * 0.5
        top = (k + 1) * 0.3
        m.bx(-2.9, -1.5, y, y + 0.5, top - 0.06, top, 'woodL')
        m.bx(-2.9, -1.5, y + 0.44, y + 0.5, 0.0, top - 0.06, 'woodD', hull='none', cull='b')
        cols.append(wbox(-2.9, y, 0.0, -1.5, y + 0.5, top))
    for x in (-2.95, -1.45):
        m.bm_((x, -2.65, 0.9), (x, -0.6, D + 0.85), 0.06, 'doorG')
        m.cy((x, -2.65, 0.0), 0.04, 0.04, 0.9, 'doorG', seg=5)
        for k in range(4):
            y = -2.4 + k * 0.5
            solid(cols, x - 0.04, y - 0.25, 0.0, x + 0.04, y + 0.25, 0.3 * (k + 1) + 0.9)
    # wavy slide down the east tower to the south
    top = [(-0.6, D), (-1.4, 0.9), (-2.1, 0.75), (-2.7, 0.35), (-2.95, 0.33)]
    prof = top + [(y, z - 0.08) for (y, z) in reversed(top)]
    m.prism(prof, 1.92, 2.48, ['doorY'], hull='full')
    for (a0, a1) in ((1.86, 1.92), (2.48, 2.54)):
        m.prism([(y, z + 0.16) for (y, z) in top] + [(y, z - 0.08) for (y, z) in reversed(top)], a0, a1, ['doorY'], hull='full')
    for (a, b) in zip(top, top[1:]):
        lo, hi = srt(a[0], b[0])
        solid(cols, 1.86, lo, 0.0, 2.54, hi, max(a[1], b[1]) + 0.16)
    # climbing wall on the east tower's east face, a steering wheel on the west tower rail
    m.bx(3.2, 3.3, -0.6, 1.4, 0.0, D, 'doorT')
    for (y, z, c) in ((-0.3, 0.3, 'red'), (0.5, 0.55, 'doorY'), (0.1, 0.85, 'trim'), (0.9, 0.3, 'doorG'), (-0.1, 1.0, 'red')):
        m.sp((3.34, y, z), 0.06, c, seg=(5, 3), hull='none')
    solid(cols, 3.2, -0.6, 0.0, 3.3, 1.4, D)
    m.cy((-2.2, 1.42, D + 0.65), 0.2, 0.2, 0.04, 'red', seg=8, rot=(90, 0, 0))
    make('Playground', m, ao, cols=cols)


def swings(pal, ao):
    """Swings [4, 2]: an A-frame swing set with two belt seats and a toddler bucket"""
    m = new(pal)
    cols = []
    H = 2.4
    for x in (-1.85, 1.85):
        for sy in (-1, 1):
            m.bm_((x + sy * 0.045, sy * 0.75, 0.0), (x + sy * 0.045, 0.0, H), 0.08, 'doorN')
        solid(cols, x - 0.06, -0.8, 0.0, x + 0.06, 0.8, H)
    m.bx(-1.95, 1.95, -0.05, 0.05, H - 0.05, H + 0.05, 'doorN')
    for (x, c) in ((-1.0, 'iron'), (0.0, 'red'), (1.0, 'iron')):
        for dx in (-0.2, 0.2):
            m.cy((x + dx, 0.0, 0.45), 0.012, 0.012, H - 0.48, 'chrome', seg=3, hull='none')
        if c == 'red':
            m.bx(x - 0.22, x + 0.22, -0.18, 0.18, 0.32, 0.55, 'red')
        else:
            m.bx(x - 0.23, x + 0.23, -0.08, 0.08, 0.42, 0.47, c)
        solid(cols, x - 0.23, -0.18, 0.3, x + 0.23, 0.18, 0.56)
    uq(m, -1.7, 1.7, -0.9, 0.9, 0.012, 'woodD')
    make('Swings', m, ao, cols=cols)


def seesaw(pal, ao):
    """SeeSaw [3, 1]: a teeter-totter on a red pivot, one end down"""
    m = new(pal)
    m.bx(-0.15, 0.15, -0.2, 0.2, 0.0, 0.45, 'red')
    m.box((0, 0, 0.5), (2.8, 0.26, 0.07), 'doorY', rot=(0, 9, 0), bevel=False)
    for sx in (-1, 1):
        x = sx * 1.25
        z = 0.5 - sx * 1.25 * math.tan(math.radians(9))
        m.bx(x - 0.04, x + 0.04, -0.2, 0.2, z + 0.15, z + 0.2, 'iron', hull='none')
    make('SeeSaw', m, ao, cols=[box(-1.4, -0.15, 0.0, 1.4, 0.15, 0.75)])


def spring_rider(pal, ao):
    """SpringRider [1, 1]: a little red race car on a spring"""
    m = new(pal)
    m.cy((0, 0, 0.0), 0.2, 0.2, 0.05, 'iron', seg=8, hull='none')
    for k in range(4):
        m.cy((0, 0, 0.05 + k * 0.06), 0.09, 0.09, 0.03, 'steel', seg=6, hull='none')
    m.bx(-0.18, 0.18, -0.4, 0.4, 0.28, 0.5, 'red')
    m.bx(-0.14, 0.14, -0.1, 0.18, 0.5, 0.62, 'red')
    m.cy((0, -0.3, 0.6), 0.1, 0.1, 0.03, 'iron', seg=8, rot=(60, 0, 0), hull='none')
    for (x, y) in ((-0.2, -0.28), (0.2, -0.28), (-0.2, 0.28), (0.2, 0.28)):
        m.cy((x, y, 0.32), 0.08, 0.08, 0.05, 'iron', seg=8, rot=(0, 90, 0), hull='none')
    make('SpringRider', m, ao, cols=[box(-0.2, -0.4, 0.0, 0.2, 0.4, 0.65)])


def sandbox(pal, ao):
    """Sandbox [3, 3]: a timber-edged sand pit with a bucket and spade"""
    m = new(pal)
    for (a, b, p, q) in ((-1.4, 1.4, -1.4, -1.2), (-1.4, 1.4, 1.2, 1.4), (-1.4, -1.2, -1.2, 1.2), (1.2, 1.4, -1.2, 1.2)):
        m.bx(a, b, p, q, 0.0, 0.25, 'wood')
    uq(m, -1.2, 1.2, -1.2, 1.2, 0.15, 'stuP')
    m.cy((0.4, 0.3, 0.15), 0.1, 0.12, 0.16, 'doorT', seg=6)
    m.bx(-0.5, -0.1, -0.4, -0.3, 0.15, 0.18, 'red', hull='none')
    m.sp((-0.3, 0.4, 0.15), 0.3, 'stuP', seg=(6, 3), scale=(1, 1, 0.35), hull='none')
    make('Sandbox', m, ao, cols=[wbox(-1.4, -1.4, 0.0, 1.4, 1.4, 0.25)])


def gazebo(pal, ao):
    """Gazebo [6, 6]: the park's octagonal white gazebo on a raised deck: eight posts, a rail with an opening on
    two sides, benches round the inside, a two-tier roof with a finial"""
    m = new(pal)
    cols = []
    R, D = 2.6, 0.3
    pts = [(math.cos(math.pi / 8 + i * math.pi / 4) * R, math.sin(math.pi / 8 + i * math.pi / 4) * R) for i in range(8)]
    vs = [(x, y, D) for (x, y) in pts]
    poly(m, vs, 'woodL', (0, 0, 1))
    for i in range(8):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % 8]
        poly(m, [(xa, ya, 0.0), (xb, yb, 0.0), (xb, yb, D), (xa, ya, D)], 'trim', ((xa + xb), (ya + yb), 0))
    cols += [wbox(-R * 0.92, -R * 0.38, 0.0, R * 0.92, R * 0.38, D), wbox(-R * 0.38, -R * 0.92, 0.0, R * 0.38, R * 0.92, D)]
    cols += [wbox(-R * 0.66, -R * 0.66, 0.0, R * 0.66, R * 0.66, D)]
    for i in range(8):
        x, y = pts[i]
        m.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, D, D + 2.5, 'trim')
        solid(cols, x - 0.08, y - 0.08, 0.0, x + 0.08, y + 0.08, D + 2.5)
    # rails between posts, open on the south (-Y) and north (+Y) faces
    for i in range(8):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % 8]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        if abs(mx) < 0.5:
            continue
        m.bm_((xa, ya, D + 0.85), (xb, yb, D + 0.85), 0.07, 'trim')
        m.bm_((xa, ya, D + 0.1), (xb, yb, D + 0.1), 0.05, 'trim', hull='none')
        for k in range(1, 4):
            u = k / 4
            x, y = xa + (xb - xa) * u, ya + (yb - ya) * u
            m.bx(x - 0.017, x + 0.017, y - 0.017, y + 0.017, D + 0.12, D + 0.82, 'trim', hull='none', cull='tb')
        # benches on the inside of the railed sides
        ix, iy = mx * 0.8, my * 0.8
        ang = math.degrees(math.atan2(my, mx)) - 90
        m.box((ix, iy, D + 0.45), (1.2, 0.36, 0.06), 'wood', rot=(0, 0, ang), bevel=False)
        m.box((ix, iy, D + 0.21), (1.0, 0.24, 0.42), 'woodD', rot=(0, 0, ang), bevel=False)
        tx, ty = -my / math.hypot(mx, my), mx / math.hypot(mx, my)
        for u in (-0.4, 0.0, 0.4):
            bx_, by_ = ix + tx * u, iy + ty * u
            solid(cols, bx_ - 0.2, by_ - 0.2, D, bx_ + 0.2, by_ + 0.2, D + 0.48)
        for k in range(5):   # the rail (diagonal sides: a chain of small boxes along it)
            u0, u1 = k / 5, (k + 1) / 5
            lo, hi = srt(xa + (xb - xa) * u0, xa + (xb - xa) * u1)
            lo2, hi2 = srt(ya + (yb - ya) * u0, ya + (yb - ya) * u1)
            solid(cols, lo - 0.05, lo2 - 0.05, D, hi + 0.05, hi2 + 0.05, D + 0.9)
    # steps at the two openings
    for sy in (-1, 1):
        a, b = srt(sy * R * 0.92, sy * (R * 0.92 + 0.5))
        m.bx(-0.9, 0.9, a, b, 0.0, D / 2, 'woodL', cull='b')
        cols.append(wbox(-0.9, a, 0.0, 0.9, b, D / 2))
    # roof: octagonal two-tier, a cupola and a finial
    z0 = D + 2.5
    m.cy((0, 0, z0), R + 0.25, R + 0.25, 0.18, 'trim', seg=8, rot=(0, 0, 22.5))
    m.fan((0, 0, z0 + 0.18), z0 + 1.5, R + 0.4, 8, ['shingle', 'shingleD'], rot=math.pi / 8)
    m.cy((0, 0, z0 + 1.2), 0.5, 0.5, 0.4, 'trim', seg=8, rot=(0, 0, 22.5))
    m.fan((0, 0, z0 + 1.6), z0 + 2.2, 0.75, 8, ['shingle'], rot=math.pi / 8)
    m.cy((0, 0, z0 + 2.2), 0.03, 0.01, 0.5, 'lineY', seg=4, hull='none')
    m.sp((0, 0, z0 + 2.3), 0.07, 'lineY', seg=(5, 3), hull='none')
    make('Gazebo', m, ao, cols=cols)


# ================================================================ the lot under construction (zone 2 landmark) [6, 12]
def construction(pal, ao):
    """Landmark_Build: a town house going up between two finished ones. A concrete slab at the floor level, timber
    stud walls with headers on the ground floor, joists and a part-laid subfloor upstairs over the stair (a rough
    site stair, walkable), a few studs and trusses above, house-wrap on the back wall, and a steel scaffold across
    the front with plank decks at the upper floor (a perch reached from the subfloor through the open front)."""
    m = new(pal)
    cols = []
    U0 = UF - SLAB
    m.bx(-HW + 0.02, HW - 0.02, FW, BW, 0.0, GF, 'curb', cull='b')
    uq(m, -HW + 0.04, HW - 0.04, FW + 0.02, BW - 0.02, GF + 0.004, 'walkB')
    cols.append(wbox(-HW + 0.02, FW, 0.0, HW - 0.02, BW, GF))
    # stud walls: front (open in the middle, the door and window headers), back (wrapped), the side walls are the
    # neighbours'; plates and studs every 0.6 m
    def stud_wall_x(y, x0, x1, z0, z1, gaps=()):
        m.bx(x0, x1, y - 0.07, y + 0.07, z0, z0 + 0.05, 'woodL', hull='none', cull='b')
        m.bx(x0, x1, y - 0.07, y + 0.07, z1 - 0.1, z1, 'woodL')
        x = x0 + 0.03
        while x < x1:
            if not any(g0 - 0.08 < x < g1 + 0.08 for (g0, g1) in gaps):
                m.bx(x - 0.025, x + 0.025, y - 0.07, y + 0.07, z0 + 0.05, z1 - 0.1, 'woodL', hull='none', cull='tb')
            x += 0.6
        for (g0, g1) in gaps:
            m.bx(g0 - 0.05, g1 + 0.05, y - 0.07, y + 0.07, z1 - 0.45, z1 - 0.1, 'wood')
            for xx in (g0 - 0.025, g1 + 0.025):
                m.bx(xx - 0.025, xx + 0.025, y - 0.07, y + 0.07, z0 + 0.05, z1 - 0.45, 'wood', hull='none', cull='tb')
    stud_wall_x(FW + 0.08, -2.9, 2.9, GF, U0, gaps=((-2.6, -1.3), (-0.4, 2.4)))
    for (a, b) in ((-2.9, -2.6), (-1.3, -0.4), (2.4, 2.9)):
        solid(cols, a, FW + 0.01, GF, b, FW + 0.15, U0)
    stud_wall_x(BW - 0.08, -2.9, 2.9, GF, U0, gaps=((-2.6, -1.3),))
    for (a, b) in ((-2.9, -2.6), (-1.3, 2.9)):
        solid(cols, a, BW - 0.15, GF, b, BW - 0.01, U0)
    m.bx(-1.3, 2.9, BW - 0.005, BW, GF + 0.1, U0 - 0.1, 'trim', hull='none', cull='ftblr')
    for k in range(2):
        txt(m, 'WRAPLINE', 0.2 + k * 1.6 - 0.8, BW + 0.004, GF + 0.9 + k * 1.0, 0.16, 'doorN', face='y+', font='display', maxw=1.2)
    # joists and the part-laid subfloor (walkable over the front room and round the stair head)
    for k in range(10):
        x = -2.7 + k * 0.6
        if STAIR[0] < x < STAIR[1] + 0.05:
            continue
        m.bx(x - 0.03, x + 0.03, FW + 0.25, BW - 0.25, U0, UF - 0.03, 'woodL', hull='none', cull='')
    m.bx(-2.9, 2.9, FW + 0.15, FW + 0.25, U0, UF - 0.03, 'wood')
    m.bx(-2.9, 2.9, BW - 0.25, BW - 0.15, U0, UF - 0.03, 'wood')
    sx0, sx1, sy0, sy1 = STAIR
    for (a, b, c0, c1) in ((sx1, 2.9, FW + 0.15, 2.6), (-2.9, sx1, FW + 0.15, sy0), (-2.9, sx1, sy1, 2.6)):
        m.bx(a, b, c0, c1, UF - 0.03, UF, 'woodL', hull='full')
        k = 0
        y = c0 + 1.2
        while y < c1 - 0.05:
            uq(m, a, b, y - 0.006, y + 0.006, UF + 0.004, 'wood')
            y += 1.2
        cols.append(wbox(a, c0, UF - 0.2, b, c1, UF))
    # a stack of sheets waiting on the subfloor
    m.bx(1.0, 2.2, -2.6, -1.4, UF, UF + 0.3, 'woodL')
    solid(cols, 1.0, -2.6, UF, 2.2, -1.4, UF + 0.3)
    # the rough site stair (walkable) with a 2x4 handrail
    n = 10
    run = (sy1 - sy0) / n
    for k in range(n):
        a = sy0 + k * run
        top = GF + (k + 1) * 0.3
        m.bx(sx0 + 0.05, sx1 - 0.05, a, a + run, top - 0.05, top, 'woodL')
        cols.append(wbox(sx0, a, 0.0, sx1, a + run, top))
    for x in (sx0 + 0.05, sx1 - 0.05):
        m.bm_((x, sy0, GF), (x, sy1, UF), 0.08, 'wood')
    m.bm_((sx1 - 0.04, sy0, GF + 1.0), (sx1 - 0.04, sy1, UF + 1.0), 0.06, 'wood', hull='none')
    for k in range(5):
        y0 = sy0 + k * (sy1 - sy0) / 5
        y1 = y0 + (sy1 - sy0) / 5
        solid(cols, sx1 - 0.08, y0, GF, sx1, y1, GF + 1.0 + 3.0 * (y1 - sy0) / (sy1 - sy0))
    # upper studs (the front half of the walls) and roof trusses on the back half
    for x in (-2.85, -2.25, 2.25, 2.85):
        m.bx(x - 0.025, x + 0.025, FW + 0.01, FW + 0.15, UF, UF + 2.6, 'woodL', hull='none', cull='tb')
        solid(cols, x - 0.03, FW + 0.01, UF, x + 0.03, FW + 0.15, UF + 2.6)
    m.bx(-2.9, 2.9, FW + 0.01, FW + 0.15, UF + 2.6, UF + 2.7, 'woodL')
    for k in range(3):
        y = 2.6 + k * 1.3
        m.bm_((-2.9, y, UF + 2.7), (0.0, y, UF + 4.4), 0.1, 'woodL')
        m.bm_((2.9, y, UF + 2.7), (0.0, y, UF + 4.4), 0.09, 'woodL')
        m.bx(-2.9, 2.9, y - 0.04, y + 0.04, UF + 2.6, UF + 2.7, 'woodL', hull='none')
        m.bm_((0.0, y, UF + 2.7), (0.0, y, UF + 4.3), 0.07, 'woodL', hull='none')
    for x in (-2.85, 2.85):
        m.bx(x - 0.05, x + 0.05, 0.6, BW - 0.15, UF, UF + 2.6, 'woodL', hull='none', cull='b')
        solid(cols, x - 0.05, 0.6, UF, x + 0.05, BW - 0.15, UF + 2.6)
    # the scaffold across the front: two frames, a plank deck at the upper floor with a toe board and rails, a ladder
    ys0, ys1 = -6.0, FW - 0.05
    for x in (-2.8, 0.0, 2.8):
        for y in (ys0 + 0.05, ys1 - 0.05):
            m.cy((x, y, 0.0), 0.03, 0.03, UF + 1.1, 'steel', seg=5, hull='none')
            m.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.0, 0.055, 'iron', hull='none', cull='b')
            solid(cols, x - 0.04, y - 0.04, 0.0, x + 0.04, y + 0.04, UF + 1.1)
        tube(m, (x + 0.035, ys0 + 0.05, 1.6), (x + 0.035, ys1 - 0.05, 1.6), 0.024, 'steel')
        tube(m, (x - 0.035, ys0 + 0.05, 0.3), (x - 0.035, ys1 - 0.05, UF - 0.2), 0.02, 'steel')
    for z in (UF + 0.5, UF + 1.05):
        tube(m, (-2.8, ys0 + 0.0, z), (2.8, ys0 + 0.0, z), 0.024, 'orange' if z > UF + 0.6 else 'steel')
    solid(cols, -2.85, ys0, UF, 2.85, ys0 + 0.1, UF + 1.1)
    tube(m, (-2.8, ys0 + 0.1, 0.4), (2.8, ys0 + 0.1, UF - 0.4), 0.018, 'steel')
    for k in range(5):
        y = ys0 + 0.12 + k * 0.27
        m.bx(-2.9, 2.9, y, y + 0.25, UF - 0.06, UF, 'woodL', hull='full')
    cols.append(wbox(-2.9, ys0, UF - 0.25, 2.9, ys1, UF))
    m.bx(-2.9, 2.9, ys0 + 0.06, ys0 + 0.1, UF, UF + 0.15, 'woodL', hull='none')
    # sheet of debris netting on the scaffold's east bay, a site light
    m.bx(1.45, 2.75, ys0 - 0.02, ys0, 0.4, UF - 0.2, 'leafD', hull='none', cull='k')
    m.bx(1.45, 2.75, ys0 + 0.0, ys0 + 0.02, 0.4, UF - 0.2, 'leafD', hull='none', cull='f')
    make('Landmark_Build', m, ao, cols=cols)


def skip(pal, ao):
    """Skip [2, 4]: a steel dumpster skip full of offcuts, drywall and a broken pallet"""
    m = new(pal)
    m.prism([(-1.6, 0.0), (1.6, 0.0), (1.9, 1.3), (-1.9, 1.3)], -0.9, 0.9, ['doorY'], hull='full', mat=Matrix.Rotation(math.pi / 2, 4, 'Z'))
    for y in (-1.95, 1.95):
        m.bx(-0.95, 0.95, y - 0.06 if y < 0 else y, y if y < 0 else y + 0.06, 1.2, 1.32, 'doorY')
    uq(m, -0.85, 0.85, -1.8, 1.8, 1.0, 'shingle')
    for (x, y, z, c, s) in ((-0.3, -0.8, 1.0, 'woodL', (0.9, 0.3, 0.25)), (0.3, 0.2, 1.0, 'trim', (0.8, 1.0, 0.18)),
                            (-0.2, 1.1, 1.0, 'wood', (1.1, 0.5, 0.4)), (0.4, -1.3, 1.0, 'orange', (0.3, 0.3, 0.35))):
        m.bx(x - s[0] / 2, x + s[0] / 2, y - s[1] / 2, y + s[1] / 2, z, z + s[2], c, hull='full')
    for sx in (-1, 1):
        x = sx * 0.905
    make('Skip', m, ao, cols=[box(-1.0, -2.0, 0.0, 1.0, 2.0, 1.32)])


def materials(pal, ao):
    """site materials: Lumber [2, 1] (a strapped stack of studs on bearers), Bricks [1, 1] (a shrink-wrapped pallet),
    Mixer [1, 1] (a cement mixer), SiteToilet [1, 1], SiteSign [2, 1], SiteFence (links run along Blender Y)"""
    m = new(pal)
    for x in (-0.7, 0.0, 0.7):
        m.bx(x - 0.05, x + 0.05, -0.35, 0.35, 0.0, 0.1, 'woodD', hull='none', cull='b')
    for r in range(4):
        m.bx(-0.95, 0.95, -0.32, 0.32, 0.1 + r * 0.12, 0.21 + r * 0.12, 'woodL' if r % 2 else 'wood')
    for x in (-0.5, 0.5):
        m.bx(x - 0.02, x + 0.02, -0.34, 0.34, 0.1, 0.6, 'iron', hull='none', cull='b')
    make('Lumber', m, ao, cols=[box(-0.95, -0.35, 0.0, 0.95, 0.35, 0.6)])
    m = new(pal)
    m.bx(-0.45, 0.45, -0.45, 0.45, 0.0, 0.14, 'wood')
    m.bx(-0.42, 0.42, -0.42, 0.42, 0.14, 0.95, 'brk')
    for k in range(1, 7):
        z = 0.14 + k * 0.115
        fq(m, -0.42, 0.42, -0.424, z - 0.01, z, 'mortar')
        rq(m, 0.424, -0.42, 0.42, z - 0.01, z, 'mortar')
        lq(m, -0.424, -0.42, 0.42, z - 0.01, z, 'mortar')
        bq(m, -0.42, 0.42, 0.424, z - 0.01, z, 'mortar')
    m.bx(-0.44, 0.44, -0.44, 0.44, 0.9, 0.96, 'glassL', hull='none', cull='b')
    make('Bricks', m, ao, cols=[box(-0.45, -0.45, 0.0, 0.45, 0.45, 0.96)])
    m = new(pal)
    for (x, y) in ((-0.4, -0.25), (0.32, -0.25)):
        m.cy((x, y, 0.15), 0.15, 0.15, 0.08, 'iron', seg=8, rot=(0, 90, 0))
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.15, 0.25, 'orange')
    m.bm_((0.0, 0.0, 0.25), (0.0, 0.0, 0.7), 0.1, 'orange')
    m.cy((0.0, 0.05, 0.6), 0.32, 0.18, 0.55, 'orange', seg=10, rot=(-55, 0, 0))
    m.cy((0.0, -0.33, 0.95), 0.17, 0.17, 0.03, 'iron', seg=10, rot=(-55, 0, 0), hull='none')
    m.bm_((0.0, 0.3, 0.3), (0.0, 0.75, 0.75), 0.04, 'steel')
    make('Mixer', m, ao, cols=[box(-0.38, -0.45, 0.0, 0.38, 0.45, 1.05)])
    m = new(pal)
    m.bx(-0.55, 0.55, -0.55, 0.55, 0.0, 0.12, 'trim')
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.12, 2.2, 'fabric')
    m.cy((0, 0, 2.2), 0.62, 0.55, 0.15, 'trim', seg=8)
    fq(m, -0.4, 0.4, -0.504, 0.15, 2.0, 'doorN')
    txt(m, 'TIDY-CAN', 0.0, -0.508, 1.75, 0.09, 'trim', font='display', maxw=0.7)
    fq(m, 0.2, 0.3, -0.508, 1.0, 1.1, 'red')
    make('SiteToilet', m, ao, cols=[box(-0.55, -0.55, 0.0, 0.55, 0.55, 2.35)])
    m = new(pal)
    for x in (-0.8, 0.8):
        m.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.0, 2.1, 'woodD')
    m.bx(-0.95, 0.95, -0.09, -0.05, 1.0, 2.15, 'trim')
    fq(m, -0.95, 0.95, -0.094, 1.85, 2.15, 'doorG')
    txt(m, 'PHASE 3', 0.0, -0.098, 2.0, 0.17, 'trim', font='display', maxw=1.6)
    txt(m, 'COMING SOON', 0.0, -0.098, 1.6, 0.18, 'doorG', font='display', maxw=1.7)
    fq(m, -0.9, 0.9, -0.094, 1.08, 1.14, 'orange')
    make('SiteSign', m, ao, cols=[box(-0.95, -0.1, 0.0, 0.95, 0.06, 2.15)])
    for (name, y0, y1) in (('SiteFence', -0.5, -0.03), ('SiteFenceFull', -0.5, 0.5)):
        m = new(pal)
        for z in (0.12, 1.85):
            m.bx(-0.02, 0.02, y0, y1, z, z + 0.04, 'steel', hull='none')
        y = y0 + 0.1
        while y < y1:
            m.bx(-0.005, 0.005, y - 0.005, y + 0.005, 0.12, 1.89, 'steel', hull='none', cull='tb')
            y += 0.2
        for (f, xx) in ((rq, 0.01), (lq, -0.01)):
            f(m, xx, y0, y1, 0.2, 1.8, 'leafD')
        make(name, m, ao, cols=[box(-0.05, y0, 0.0, 0.05, y1, 1.9)])
    m = new(pal)
    m.bx(-0.3, 0.3, -0.12, 0.12, 0.0, 0.12, 'curb')
    m.bx(-0.025, 0.025, -0.025, 0.025, 0.12, 1.95, 'steel')
    make('SiteFencePost', m, ao, cols=[box(-0.3, -0.12, 0.0, 0.3, 0.12, 0.12), box(-0.03, -0.03, 0.12, 0.03, 0.03, 1.95)])


def build_site(pal, ao):
    gate_landmark(pal, ao)
    entry_sign(pal, ao)
    clubhouse(pal, ao)
    pool(pal, ao)
    lounger(pal, ao)
    umbrella_table(pal, ao)
    pool_fence(pal, ao)
    pool_sign(pal, ao)
    mail_kiosk(pal, ao)
    play_structure(pal, ao)
    swings(pal, ao)
    seesaw(pal, ao)
    spring_rider(pal, ao)
    sandbox(pal, ao)
    gazebo(pal, ao)
    construction(pal, ao)
    skip(pal, ao)
    materials(pal, ao)
