"""kit-parking vehicles (front = Blender -Y). Car bodies are side profiles (y, z) extruded across the width with a
greenhouse on top; windows are inset ink / glass slabs and slanted screen strips; body paint is the 'paint' cell
(repainted per placed car by the theme). Each car sits a little skewed / off-centre in its bay (built into the piece);
collision is an axis-aligned body box plus a cabin box around the skewed footprint (low enough to shoot over)."""
import math

from mathutils import Matrix

from parking_base import *  # noqa: F401,F403
from parking_struct import inset


def rz(deg, dx=0.0, dy=0.0, dz=0.0):
    return Matrix.Translation((dx, dy, dz)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


SEDAN = dict(L=4.5, W=1.84, r=0.34, wy=(-1.4, 1.38), cw=0.8, bp=0.2, top=0.92, roof=1.43,
             body=[(-2.25, 0.3), (2.25, 0.3), (2.28, 0.6), (2.2, 0.88), (1.3, 0.92), (-1.2, 0.92), (-2.1, 0.8), (-2.3, 0.55)],
             cab=[(-1.2, 0.92), (-0.42, 1.43), (0.78, 1.43), (1.35, 0.92)],
             hl=(-2.27, 0.6, 0.72), tl=(2.25, 0.64, 0.8), fb=(-2.32, 0.3, 0.47), rb=(2.3, 0.3, 0.48), seams=(-1.05, 0.2, 1.25))
HATCH = dict(L=3.9, W=1.76, r=0.32, wy=(-1.25, 1.2), cw=0.78, bp=0.3, top=0.9, roof=1.47,
             body=[(-1.95, 0.28), (1.95, 0.28), (1.97, 0.62), (1.92, 0.9), (-1.0, 0.9), (-1.85, 0.78), (-2.0, 0.5)],
             cab=[(-1.0, 0.9), (-0.3, 1.45), (1.6, 1.47), (1.9, 0.9)],
             hl=(-1.97, 0.58, 0.7), tl=(1.95, 0.7, 0.86), fb=(-2.02, 0.28, 0.45), rb=(2.0, 0.28, 0.46), seams=(-0.85, 0.3, 1.3))
SUV = dict(L=4.7, W=1.96, r=0.4, wy=(-1.5, 1.45), cw=0.88, bp=0.35, top=1.1, roof=1.8,
           body=[(-2.35, 0.38), (2.35, 0.38), (2.37, 0.8), (2.33, 1.08), (-1.25, 1.1), (-2.25, 0.98), (-2.4, 0.6)],
           cab=[(-1.25, 1.1), (-0.45, 1.78), (2.15, 1.8), (2.3, 1.1)],
           hl=(-2.36, 0.74, 0.88), tl=(2.35, 0.8, 1.02), fb=(-2.44, 0.36, 0.58), rb=(2.42, 0.36, 0.58), seams=(-1.1, 0.35, 1.55))
SPORTS = dict(L=4.4, W=1.92, r=0.35, wy=(-1.35, 1.35), cw=0.72, bp=0.62, top=0.8, roof=1.17,
              body=[(-2.2, 0.25), (2.2, 0.25), (2.25, 0.62), (2.15, 0.78), (0.9, 0.82), (-0.7, 0.8), (-2.15, 0.6), (-2.28, 0.42)],
              cab=[(-0.7, 0.8), (0.0, 1.17), (0.65, 1.17), (1.25, 0.82)],
              hl=(-2.2, 0.5, 0.6), tl=(2.22, 0.6, 0.72), fb=(-2.3, 0.25, 0.4), rb=(2.27, 0.25, 0.4), seams=(-0.55, 0.75))


def car_body(m, S, paint='paint', glass='glass', wheels=True, tire='tire', hub='chrome', lights=True, frame='ink'):
    hw, r, cw = S['W'] / 2, S['r'], S['cw']
    if wheels:
        for sx in (-1, 1):
            for y in S['wy']:
                wheel(m, sx * (hw + 0.03), y, r, 0.24, hub=hub, tire=tire)
    m.prism(S['body'], -hw, hw, [paint], bevel=True)
    for sx in (-1, 1):   # wheel arches
        x = sx * (hw + 0.003)
        for y in S['wy']:
            R = r + 0.07
            poly(m, [(x, y + math.cos(a) * R, r + math.sin(a) * R) for a in [i / 8 * math.pi for i in range(9)]], 'ink', (sx, 0, 0))
    cab = S['cab']
    m.prism(cab, -cw, cw, [paint], bevel=True)
    m.prism(inset(cab, 0.05), -cw - 0.006, cw + 0.006, [frame], hull='none')
    m.prism(inset(cab, 0.085), -cw - 0.012, cw + 0.012, [glass], hull='none')
    for (p0, p1) in ((cab[0], cab[1]), (cab[2], cab[3])):
        m.prism(slant(p0, p1, 0.07, 0.93, -0.01, 0.006), -cw + 0.05, cw - 0.05, [frame], hull='none')
        m.prism(slant(p0, p1, 0.11, 0.89, -0.004, 0.012), -cw + 0.09, cw - 0.09, [glass], hull='none')
        if glass == 'glass':   # a glint on each screen
            a = slant(p0, p1, 0.3, 0.45, 0.013, 0.016)
            m.prism(a, -cw + 0.25, -cw + 0.4, ['glassL'], hull='none')
    bp = S['bp']
    m.bx(-cw - 0.016, cw + 0.016, bp - 0.05, bp + 0.05, S['top'] + 0.07, S['roof'] - 0.04, paint, hull='none')
    if not lights:
        return
    yf, z0, z1 = S['hl']
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.12), sx * (hw - 0.45)))
        m.bx(a, b, yf - 0.025, yf + 0.06, z0, z1, 'light', hull='none')
        m.bx(sx * 0.0 + min(sx * (hw - 0.04), sx * (hw - 0.1)), max(sx * (hw - 0.04), sx * (hw - 0.1)), yf, yf + 0.06, z0, z1, 'cone', hull='none')
    yt, t0, t1 = S['tl']
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.08), sx * (hw - 0.42)))
        m.bx(a, b, yt - 0.06, yt + 0.025, t0, t1, 'red', hull='none')
    m.bx(-0.32, 0.32, yf - 0.012, yf + 0.06, z0 - 0.02, z1, 'ink', hull='none')   # grille
    for (y, c0, c1), sg in ((S['fb'], -1), (S['rb'], 1)):
        m.bx(-hw + 0.03, hw - 0.03, min(y, y - sg * 0.2), max(y, y - sg * 0.2), c0 - 0.03, c1, 'steelD')
        (fq if sg < 0 else bq)(m, -0.2, 0.2, y + sg * 0.003, c0 + 0.03, c1 - 0.03, 'plate')
    y = S['cab'][0][0] + 0.25   # mirrors
    for sx in (-1, 1):
        a, b = sorted((sx * cw, sx * (cw + 0.16)))
        m.bx(a, b, y - 0.05, y + 0.07, S['top'] + 0.08, S['top'] + 0.2, paint)
    for sx in (-1, 1):   # door seams and handles
        x = sx * (hw + 0.007)
        for ys in S['seams']:
            (rq if sx > 0 else lq)(m, x, ys - 0.008, ys + 0.008, S['body'][0][1] + 0.08, S['top'] - 0.03, 'ink')
        for ys in S['seams'][:-1]:
            (rq if sx > 0 else lq)(m, x + sx * 0.003, ys + 0.12, ys + 0.28, S['top'] - 0.17, S['top'] - 0.12, 'chrome')


def car_cols(S, skew, dx, dy):
    L, W = S['L'], S['W'] + 0.06
    cab = S['cab']
    cy0, cy1 = min(p[0] for p in cab), max(p[0] for p in cab)
    a = math.radians(skew)
    cyc = (cy0 + cy1) / 2
    cx, cyy = dx - math.sin(a) * cyc, dy + math.cos(a) * cyc
    return [rot_box(L, W, skew, S['top'], dx, dy), rot_box(cy1 - cy0, 2 * S['cw'], skew, S['roof'], cx, cyy)]


def roof_rails(m, S):
    for sx in (-1, 1):
        x = sx * (S['cw'] - 0.1)
        m.bx(x - 0.03, x + 0.03, -0.25, 1.95, S['roof'] + 0.06, S['roof'] + 0.1, 'steelD')
        for y in (-0.2, 1.9):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, S['roof'] - 0.01, S['roof'] + 0.06, 'steelD', hull='none')


def open_door(m, S, side=-1, deg=32, paint='paint'):
    """the front door on one side swung open: dark opening + seat on the body, the door panel on its hinge"""
    hw = S['W'] / 2
    y0, y1 = S['seams'][0], S['seams'][1]
    x = side * (hw + 0.0065)
    (lq if side < 0 else rq)(m, x, y0 + 0.02, y1 - 0.02, S['body'][0][1] + 0.12, S['top'] - 0.04, 'interior')
    m.bx(-0.55 if side < 0 else 0.15, -0.15 if side < 0 else 0.55, y0 + 0.25, y1 - 0.1, S['top'] - 0.25, S['top'] + 0.25, 'seat', hull='none')
    P0 = m.parent
    m.parent = P0 @ Matrix.Translation((side * hw, y0, 0)) @ Matrix.Rotation(math.radians(-side * deg), 4, 'Z')
    L = y1 - y0
    xa, xb = sorted((0.0, side * 0.07))
    m.bx(xa, xb, 0.0, L, S['body'][0][1] + 0.05, S['top'], paint)
    (lq if side < 0 else rq)(m, xa if side < 0 else xb, 0.02, L - 0.02, S['body'][0][1] + 0.12, S['top'] - 0.05, paint) if False else None
    (rq if side < 0 else lq)(m, xb + 0.003 if side < 0 else xa - 0.003, 0.03, L - 0.03, S['body'][0][1] + 0.1, S['top'] - 0.03, 'interior')
    # window frame on the door
    m.bx(xa + 0.01, xb - 0.01, 0.02, 0.07, S['top'], S['roof'] - 0.08, paint, hull='none')
    m.bx(xa + 0.01, xb - 0.01, L - 0.1, L - 0.04, S['top'], S['roof'] - 0.12, paint, hull='none')
    m.bx(xa + 0.01, xb - 0.01, 0.07, L - 0.1, S['roof'] - 0.12, S['roof'] - 0.07, paint, hull='none')
    m.bx(xa + 0.025, xb - 0.025, 0.07, L - 0.1, S['top'], S['roof'] - 0.12, 'glass', hull='none')
    m.parent = P0


def build_cars(pal, ao):
    out = {}
    specs = [
        ('Sedan', SEDAN, 3.0, 0.08, 0.1, None),
        ('Sedan_Door', SEDAN, -2.0, -0.05, -0.1, 'door'),
        ('Hatch', HATCH, -4.0, 0.1, 0.2, None),
        ('Hatch_Hazard', HATCH, 2.0, -0.05, 0.15, None),
        ('Hatch_Boot', HATCH, 1.0, 0.05, -0.2, 'boot'),
        ('SUV', SUV, -2.5, -0.08, 0.0, 'rails'),
        ('SUV_Boot', SUV, 3.5, 0.06, -0.05, 'boot'),
        ('Sports', SPORTS, 1.5, 0.0, 0.1, 'spoiler'),
    ]
    for name, S, skew, dx, dy, extra in specs:
        m = new(pal)
        m.parent = rz(skew, dx, dy)
        car_body(m, S)
        if extra == 'rails':
            roof_rails(m, S)
        elif extra == 'spoiler':
            m.bx(-0.85, 0.85, 1.85, 2.15, 0.98, 1.03, 'paint')
            for sx in (-1, 1):
                m.bx(sx * 0.6 - 0.03, sx * 0.6 + 0.03, 1.95, 2.05, 0.8, 0.98, 'ink')
            uq(m, -0.12, 0.12, -2.0, -1.0, 0.783, 'paper') if False else None
            for sx in (-1, 1):   # racing stripes over the bonnet
                poly(m, [(sx * 0.1, -2.1, 0.645), (sx * 0.25, -2.1, 0.645), (sx * 0.25, -0.75, 0.805), (sx * 0.1, -0.75, 0.805)], 'paper', (0, -0.16, 1.0))
        elif extra == 'door':
            open_door(m, S, -1)
        elif extra == 'boot':   # tailgate up, luggage inside
            yb = S['cab'][3][0]
            hw = S['W'] / 2
            bq(m, -hw + 0.12, hw - 0.12, S['L'] / 2 + 0.006, S['body'][0][1] + 0.3, S['top'] - 0.02, 'interior')
            for i, (x0, x1, c) in enumerate(((-0.6, -0.1, 'cardb'), (0.0, 0.5, 'pBlue'))):
                m.bx(x0, x1, yb - 0.4, yb + 0.15, S['top'] - 0.05, S['top'] + 0.3 + 0.08 * i, c)
            P0 = m.parent
            ry, rzz = S['cab'][2][0], S['roof']
            m.parent = P0 @ Matrix.Translation((0, ry, rzz)) @ Matrix.Rotation(math.radians(-70), 4, 'X')
            Lg = math.hypot(S['cab'][3][0] - ry, S['cab'][3][1] - rzz) + (S['top'] - S['body'][0][1]) * 0.6
            m.bx(-S['cw'] + 0.03, S['cw'] - 0.03, -0.06, 0.02, -Lg, 0.0, 'paint')
            dq(m, -S['cw'] + 0.15, S['cw'] - 0.15, -0.05, 0.0, -Lg * 0.55 if False else 0.0, 'glass') if False else None
            fq(m, -S['cw'] + 0.12, S['cw'] - 0.12, -0.063, -Lg * 0.55, -0.08, 'glass')
            m.parent = P0
        cols = car_cols(S, skew, dx, dy)
        make(name, m, ao, bevel=0.02, cols=cols)
    # the hazard lights' glow (an overlay the theme blinks): placed with Hatch_Hazard's transform
    m = new(pal)
    m.parent = rz(2.0, -0.05, 0.15)
    S = HATCH
    hw = S['W'] / 2
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.03), sx * (hw - 0.13)))
        m.bx(a - 0.015, b + 0.015, S['hl'][0] - 0.02, S['hl'][0] + 0.09, S['hl'][1] - 0.03, S['hl'][2] + 0.03, 'litA', hull='none')
        m.bx(a - 0.015, b + 0.015, S['tl'][0] - 0.09, S['tl'][0] + 0.04, S['tl'][1] - 0.03, S['tl'][2] + 0.03, 'litA', hull='none')
        for y in (-1.0, 1.4):
            x = sx * (hw + 0.008)
            (rq if sx > 0 else lq)(m, x, y - 0.06, y + 0.06, S['top'] - 0.08, S['top'] - 0.02, 'litA')
    make('HazardGlow', m, ao)
    return out


# ---------------------------------------------------------------- wrecks, covered, on a jack
def build_wrecks(pal, ao):
    S = SEDAN
    hw = S['W'] / 2
    # burnt-out shell: sits on its rims, scorched paint, empty window frames, ash and soot on the floor
    for name, skew, cave in (('Wreck_Burnt', 6.0, False), ('Wreck_Burnt_B', -3.0, True)):
        m = new(pal)
        m.parent = rz(skew, 0.05)
        for sx in (-1, 1):
            for y in S['wy']:
                m.cy((sx * (hw - 0.1) - (0.2 if sx > 0 else 0), y, 0.24), 0.24, 0.24, 0.2, 'steelD', seg=8, rot=(0, 90, 0))
        disc(m, 0.0, 0.0, 0.058, 2.6, 'ash', seg=14, sx=0.62, jag=[1.0, 0.86, 1.08, 0.92, 1.04, 0.8, 1.1])
        disc(m, 0.1, -0.2, 0.064, 1.9, 'ink', seg=12, sx=0.55, jag=[0.9, 1.06, 0.84, 1.0, 0.95])
        body = [(p[0], p[1] - 0.12) for p in S['body']]
        m.prism(body, -hw, hw, ['burnt'], bevel=True)
        cab = S['cab']
        cab = [(cab[0][0], cab[0][1] - 0.12), (cab[1][0], cab[1][1] - (0.3 if cave else 0.14)), (cab[2][0], cab[2][1] - (0.26 if cave else 0.14)), (cab[3][0], cab[3][1] - 0.12)]
        m.prism(cab, -S['cw'], S['cw'], ['burnt'], bevel=True)
        m.prism(inset(cab, 0.06), -S['cw'] - 0.008, S['cw'] + 0.008, ['ink'], hull='none')
        for (p0, p1) in ((cab[0], cab[1]), (cab[2], cab[3])):
            m.prism(slant(p0, p1, 0.08, 0.92, -0.01, 0.008), -S['cw'] + 0.06, S['cw'] - 0.06, ['ink'], hull='none')
        for sx in (-1, 1):   # scorched / rusty patches on the sides
            x = sx * (hw + 0.004)
            for (y0, y1, z0, z1, c) in ((-1.9, -0.9, 0.3, 0.7, 'rust'), (-0.4, 0.7, 0.22, 0.6, 'burntL'), (1.1, 1.9, 0.35, 0.72, 'rust')):
                (rq if sx > 0 else lq)(m, x, y0, y1, z0, z1, c)
        uq(m, -0.6, 0.5, -2.0, -1.4, S['body'][-3][1] - 0.12 + 0.01, 'rust') if False else None
        m.bx(-0.7, 0.7, -2.0, -1.3, 0.72, 0.76, 'rust', hull='none')
        m.bx(-0.3, 0.2, 1.6, 2.0, 0.72, 0.8, 'burntL', hull='none')
        make(name, m, ao, bevel=0.02, cols=[rot_box(S['L'], S['W'], skew, 0.8, 0.05), rot_box(2.3, 1.6, skew, 1.25, 0.05)])
    # smashed: front crumpled, bonnet buckled up, windscreen crazed, a door gone
    m = new(pal)
    skew = -7.0
    m.parent = rz(skew, -0.1, 0.1)
    for sx in (-1, 1):
        for y in S['wy']:
            wheel(m, sx * (hw + 0.03), y, S['r'], 0.24)
    body = [(-1.75, 0.3), (2.25, 0.3), (2.28, 0.6), (2.2, 0.88), (1.3, 0.92), (-1.2, 0.92), (-1.6, 0.72), (-1.85, 0.55)]
    m.prism(body, -hw, hw, ['paint'], bevel=True)
    cab = S['cab']
    m.prism(cab, -S['cw'], S['cw'], ['paint'], bevel=True)
    m.prism(inset(cab, 0.05), -S['cw'] - 0.006, S['cw'] + 0.006, ['ink'], hull='none')
    m.prism(inset(cab, 0.085), -S['cw'] - 0.012, S['cw'] + 0.012, ['glass'], hull='none')
    for (p0, p1) in ((cab[0], cab[1]), (cab[2], cab[3])):
        m.prism(slant(p0, p1, 0.07, 0.93, -0.01, 0.006), -S['cw'] + 0.05, S['cw'] - 0.05, ['ink'], hull='none')
        m.prism(slant(p0, p1, 0.11, 0.89, -0.004, 0.012), -S['cw'] + 0.09, S['cw'] - 0.09, ['glassL'], hull='none')
    m.bx(-hw + 0.1, hw - 0.1, -1.7, -0.95, 0.9, 1.05, 'paint')   # buckled bonnet peak
    m.bm_((-hw + 0.1, -1.85, 0.6), (hw - 0.3, -1.95, 0.4), 0.12, 'steelD')   # bumper hanging off
    for sx in (-1, 1):
        x = sx * (hw + 0.004)
        (rq if sx > 0 else lq)(m, x, -1.7, -1.1, 0.4, 0.82, 'rust')
    lq(m, -hw - 0.004, -1.05, 0.2, 0.42, 0.88, 'interior')
    m.bx(-0.6, -0.15, -0.8, 0.0, 0.7, 1.2, 'seat', hull='none')
    m.bx(-0.8, 0.8, -1.4, -1.1, 0.0, 0.02, 'glassL', hull='none') if False else None
    disc(m, -0.2, -2.6, 0.058, 0.35, 'glassL', seg=7, jag=[1.0, 0.6, 1.1, 0.7, 0.9, 0.5, 1.0])
    make('Wreck_Smash', m, ao, bevel=0.02, cols=[rot_box(4.1, S['W'], skew, 1.0, -0.1, 0.3), rot_box(2.5, 1.6, skew, 1.43, -0.1, 0.1)])
    # covered car: a fitted tarp over a sedan shape, tie straps, the tyres peeking out
    m = new(pal)
    skew = 2.0
    m.parent = rz(skew)
    for sx in (-1, 1):
        for y in S['wy']:
            wheel(m, sx * (hw + 0.03), y, S['r'], 0.24, hub='steelD')
    tarp = [(-2.32, 0.42), (2.32, 0.42), (2.34, 0.78), (2.2, 0.98), (1.3, 1.0), (0.82, 1.5), (-0.46, 1.5), (-1.25, 1.0), (-2.15, 0.88), (-2.36, 0.62)]
    m.prism(tarp, -hw - 0.08, hw + 0.08, ['tarp'], bevel=True)
    for y in (-1.6, 0.2, 1.7):   # straps
        m.bx(-hw - 0.095, hw + 0.095, y - 0.04, y + 0.04, 0.42, 0.98 if abs(y) > 1 else 1.0, 'ink', hull='none', cull='b')
    for sx in (-1, 1):   # sagging folds
        x = sx * (hw + 0.084)
        (rq if sx > 0 else lq)(m, x, -0.9, -0.84, 0.48, 0.95, 'steelD')
        (rq if sx > 0 else lq)(m, x, 0.9, 0.96, 0.48, 0.95, 'steelD')
    make('CarCovered', m, ao, bevel=0.03, cols=[rot_box(4.7, 2.0, skew, 1.0), rot_box(2.2, 1.6, skew, 1.5)])
    # on a jack: nose lifted, front-left wheel off and leaning on the body, trolley jack, toolbox
    m = new(pal)
    skew = -3.0
    base = rz(skew, 0.05, 0.1)
    m.parent = base @ Matrix.Translation((0, 1.38, 0)) @ Matrix.Rotation(math.radians(-3.5), 4, 'X') @ Matrix.Translation((0, -1.38, 0))
    for sx in (-1, 1):
        for y in S['wy']:
            if sx < 0 and y < 0:
                m.cy((-hw - 0.03, y, S['r']), 0.12, 0.12, 0.14, 'steelD', seg=8, rot=(0, 90, 0))   # bare hub
                continue
            wheel(m, sx * (hw + 0.03), y, S['r'], 0.24)
    car_body(m, S, wheels=False)
    m.parent = base
    m.cy((-hw - 0.55, -1.3, 0.0), 0.34, 0.34, 0.22, 'tire', seg=10)   # the wheel, lying flat
    m.cy((-hw - 0.55, -1.3, 0.22), 0.19, 0.19, 0.02, 'chrome', seg=6, hull='none')
    m.bx(-hw - 0.2, -hw + 0.3, -1.75, -1.15, 0.0, 0.16, 'pipeR')   # trolley jack
    m.bm_((-hw + 0.1, -1.45, 0.14), (-hw + 0.3, -1.45, 0.4), 0.08, 'pipeR')
    m.bm_((-hw - 0.15, -1.15, 0.12), (-hw - 0.75, -0.6, 0.85), 0.04, 'steelD')
    m.bx(-hw - 0.75, -hw - 0.3, 0.1, 0.5, 0.0, 0.3, 'pipeR')   # toolbox
    m.bx(-hw - 0.77, -hw - 0.28, 0.08, 0.52, 0.3, 0.34, 'steelD')
    m.bx(-hw - 0.6, -hw - 0.45, 0.25, 0.35, 0.34, 0.42, 'ink', hull='none')
    make('CarJack', m, ao, bevel=0.02, cols=[rot_box(4.5, 1.9, skew, 1.0, 0.05, 0.1), rot_box(2.6, 1.6, skew, 1.5, 0.05, 0.2), cb(-hw - 0.9, -1.8, 0, -hw - 0.15, 0.6, 0.4)])


# ---------------------------------------------------------------- pickups, vans
def build_vans(pal, ao):
    # pickup (3 x 6): cab + open bed with a toolbox and sacks
    for name, skew, load in (('Pickup', 2.0, True), ('Pickup_B', -2.5, False)):
        m = new(pal)
        m.parent = rz(skew, 0.05)
        hw = 0.98
        for sx in (-1, 1):
            for y in (-1.75, 1.6):
                wheel(m, sx * (hw + 0.04), y, 0.42, 0.28)
        m.prism([(-2.65, 0.42), (2.65, 0.42), (2.67, 1.0), (-1.0, 1.08), (-2.55, 1.0), (-2.7, 0.7)], -hw, hw, ['paint'], bevel=True)
        cab = [(-1.0, 1.08), (-0.55, 1.85), (0.55, 1.86), (0.62, 1.08)]
        m.prism(cab, -0.9, 0.9, ['paint'], bevel=True)
        m.prism(inset(cab, 0.05), -0.906, 0.906, ['ink'], hull='none')
        m.prism(inset(cab, 0.085), -0.912, 0.912, ['glass'], hull='none')
        m.prism(slant(cab[0], cab[1], 0.07, 0.93, -0.01, 0.006), -0.85, 0.85, ['ink'], hull='none')
        m.prism(slant(cab[0], cab[1], 0.11, 0.89, -0.004, 0.012), -0.81, 0.81, ['glass'], hull='none')
        m.bx(-0.916, 0.916, -0.02, 0.06, 1.12, 1.8, 'paint', hull='none')
        # bed: floor, side walls, tailgate
        uq(m, -0.9, 0.9, 0.7, 2.58, 1.003, 'steelD')
        for sx in (-1, 1):
            a, b = sorted((sx * 0.9, sx * (hw - 0.004)))
            m.bx(a, b, 0.62, 2.66, 1.0, 1.45, 'paint')
        m.bx(-0.9, 0.9, 0.62, 0.7, 1.0, 1.5, 'paint')
        m.bx(-0.9, 0.9, 2.58, 2.66, 1.0, 1.42, 'paint')
        bq(m, -0.3, 0.3, 2.663, 1.15, 1.3, 'ink')
        for sx in (-1, 1):
            a, b = sorted((sx * (hw - 0.1), sx * (hw - 0.4)))
            m.bx(a, b, -2.72, -2.64, 0.78, 0.92, 'light', hull='none')
            m.bx(a, b, 2.64, 2.7, 1.1, 1.35, 'red', hull='none')
        m.bx(-hw + 0.03, hw - 0.03, -2.78, -2.6, 0.38, 0.62, 'chrome')
        m.bx(-hw + 0.03, hw - 0.03, 2.62, 2.78, 0.38, 0.6, 'steelD')
        m.bx(-0.4, 0.4, -2.73, -2.69, 0.64, 0.9, 'ink', hull='none')
        if load:
            m.bx(-0.85, 0.85, 0.75, 1.15, 1.0, 1.42, 'steel')
            m.bx(-0.86, 0.86, 0.74, 1.16, 1.42, 1.46, 'steelD')
            for i, x in enumerate((-0.45, 0.25)):
                m.sp((x, 1.9 + 0.2 * i, 1.18), 0.32, 'cardb', seg=(7, 4), scale=(1.0, 0.75, 0.45))
        else:   # tarp over a load
            m.prism([(0.75, 1.0), (2.55, 1.0), (2.4, 1.65), (0.95, 1.7)], -0.86, 0.86, ['tarp'], bevel=True)
        make(name, m, ao, bevel=0.02, cols=[rot_box(5.4, 2.0, skew, 1.45, 0.05), rot_box(1.7, 1.8, skew, 1.86, 0.05 - math.sin(math.radians(skew)) * -0.2, -0.2)])
    # van (3 x 6): one box, sliding side door (Van_Door: slid open, parcels inside)
    for name, skew, door in (('Van', -1.5, False), ('Van_Door', 2.5, True)):
        m = new(pal)
        m.parent = rz(skew, -0.05)
        hw = 0.98
        for sx in (-1, 1):
            for y in (-1.6, 1.65):
                wheel(m, sx * (hw + 0.03), y, 0.38, 0.26)
        prof = [(-2.5, 0.36), (2.5, 0.36), (2.5, 2.15), (-1.2, 2.2), (-2.05, 1.25), (-2.55, 1.05), (-2.58, 0.6)]
        m.prism(prof, -hw, hw, ['paint'], bevel=True)
        for sx in (-1, 1):
            x = sx * (hw + 0.003)
            for y in (-1.6, 1.65):
                poly(m, [(x, y + math.cos(a) * 0.45, 0.38 + math.sin(a) * 0.45) for a in [i / 8 * math.pi for i in range(9)]], 'ink', (sx, 0, 0))
        m.prism(slant(prof[3], prof[4], 0.07, 0.93, -0.01, 0.006), -0.9, 0.9, ['ink'], hull='none')
        m.prism(slant(prof[3], prof[4], 0.11, 0.89, -0.004, 0.012), -0.86, 0.86, ['glass'], hull='none')
        win = [(-1.95, 1.33), (-1.2, 2.06), (-0.75, 2.06), (-0.75, 1.33)]
        m.prism(win, -hw - 0.006, hw + 0.006, ['ink'], hull='none')
        m.prism(inset(win, 0.035), -hw - 0.012, hw + 0.012, ['glass'], hull='none')
        for sx in (-1, 1):
            x = sx * (hw + 0.003)
            f = rq if sx > 0 else lq
            f(m, x, -0.66, -0.64, 0.45, 2.05, 'ink')
            f(m, x, 0.95, 0.97, 0.45, 2.05, 'ink')
            f(m, x + sx * 0.003, -0.55, 2.4, 1.0, 1.1, 'paper')
        bq(m, -0.006, 0.006, 2.503, 0.45, 2.05, 'ink')
        for sx in (-1, 1):
            a, b = sorted((sx * (hw - 0.1), sx * (hw - 0.4)))
            m.bx(a, b, -2.6, -2.5, 0.75, 0.9, 'light', hull='none')
            m.bx(a, b, 2.48, 2.55, 0.8, 1.25, 'red', hull='none')
        m.bx(-hw + 0.03, hw - 0.03, -2.66, -2.5, 0.32, 0.58, 'steelD')
        m.bx(-hw + 0.03, hw - 0.03, 2.5, 2.64, 0.32, 0.56, 'steelD')
        fq(m, -0.2, 0.2, -2.663, 0.4, 0.54, 'plate')
        if door:   # right side door slid back, the dark load space with parcels
            rq(m, hw + 0.009, -0.62, 0.92, 0.45, 2.0, 'interior')
            for i, (y0, z0) in enumerate(((-0.4, 0.45), (0.2, 0.45), (-0.2, 0.95))):
                m.bx(0.35, 0.9, y0, y0 + 0.5, z0, z0 + 0.45, 'cardb')
            m.bx(hw + 0.02, hw + 0.08, 0.95, 2.45, 0.45, 2.02, 'paint')
        make(name, m, ao, bevel=0.02, cols=[rot_box(5.2, 2.0, skew, 2.2, -0.05)])


# ---------------------------------------------------------------- trucks
def truck_cab(m, y0, y1, hw, top, paint='paint'):
    """flat-fronted truck cab from y0 (front) to y1, roof at top"""
    prof = [(y0, 0.5), (y1, 0.5), (y1, top), (y0 + 0.25, top), (y0, top - 0.5)]
    m.prism(prof, -hw, hw, [paint], bevel=True)
    ws = [(y0 + 0.02, top - 1.15), (y0 + 0.02, top - 0.55), (y0 + 0.26, top - 0.08), (y0 + 0.3, top - 1.15)]
    m.prism(ws, -hw + 0.1, hw - 0.1, ['ink'], hull='none')
    poly(m, [(-hw + 0.16, y0 - 0.006, top - 1.1), (hw - 0.16, y0 - 0.006, top - 1.1), (hw - 0.16, y0 - 0.006, top - 0.58), (-hw + 0.16, y0 - 0.006, top - 0.58)], 'glass', (0, -1, 0))
    for sx in (-1, 1):
        x = sx * (hw + 0.004)
        f = rq if sx > 0 else lq
        f(m, x, y0 + 0.35, y1 - 0.25, top - 1.05, top - 0.3, 'ink')
        f(m, x + sx * 0.003, y0 + 0.4, y1 - 0.3, top - 1.0, top - 0.35, 'glass')
        a, b = sorted((sx * hw, sx * (hw + 0.25)))
        m.bx(a, b, y0 + 0.1, y0 + 0.2, top - 1.0, top - 0.5, 'steelD')
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.12), sx * (hw - 0.45)))
        fq(m, a, b, y0 - 0.006, 0.75, 0.92, 'light')
    fq(m, -0.5, 0.5, y0 - 0.006, 1.0, 1.35, 'ink')
    m.bx(-hw - 0.02, hw + 0.02, y0 - 0.15, y0 + 0.05, 0.42, 0.68, 'steelD')


def build_trucks(pal, ao):
    # box truck (3 x 8): paint cab, white box with a paint stripe, rear roller door
    m = new(pal)
    hw = 1.12
    for sx in (-1, 1):
        for y in (-2.55, 1.9, 2.95):
            wheel(m, sx * (hw + 0.02), y, 0.48, 0.3)
    m.bx(-0.7, 0.7, -3.5, 3.6, 0.45, 0.75, 'steelD', hull='none')
    truck_cab(m, -3.7, -1.75, 1.08, 2.85)
    m.bx(-hw, hw, -1.65, 3.7, 0.75, 3.3, 'pWhite', bevel=True)
    for sx in (-1, 1):
        x = sx * (hw + 0.003)
        f = rq if sx > 0 else lq
        f(m, x, -1.5, 3.55, 1.2, 1.65, 'paint')
        f(m, x, -1.5, 3.55, 1.72, 1.8, 'paint')
        x2 = sx * (hw + 0.006)
        for k in range(3):
            (rq if sx > 0 else lq)(m, x2, -1.2 + k * 0.5, -0.95 + k * 0.5, 2.3, 2.9, ['lineY', 'pipeB', 'exitG'][k])
    for k in range(9):
        bq(m, -hw + 0.08, hw - 0.08, 3.703, 0.85 + k * 0.27, 0.95 + k * 0.27, 'galv')
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.05), sx * (hw - 0.3)))
        bq(m, a, b, 3.706, 0.85, 1.1, 'red')
    make('BoxTruck', m, ao, bevel=0.02, cols=[cb(-1.15, -3.85, 0, 1.15, -1.7, 2.85), cb(-1.15, -1.7, 0, 1.15, 3.75, 3.3)])
    # tow truck (3 x 8): cab with a light bar, boom, cable and hook, wheel-lift and tool boxes
    m = new(pal)
    hw = 1.08
    for sx in (-1, 1):
        for y in (-2.5, 1.45, 2.45):
            wheel(m, sx * (hw + 0.02), y, 0.46, 0.3)
    truck_cab(m, -3.6, -1.6, hw, 2.6)
    m.bx(-0.75, 0.75, -2.2, -1.9, 2.6, 2.75, 'ink')
    for k, c in enumerate(('litA', 'cone', 'litA', 'cone')):
        m.bx(-0.7 + k * 0.35, -0.4 + k * 0.35, -2.18, -1.92, 2.75, 2.9, c)
    m.bx(-hw, hw, -1.5, 3.3, 0.5, 1.15, 'steelD')
    for sx in (-1, 1):
        a, b = sorted((sx * hw, sx * (hw - 0.55)))
        m.bx(a, b, -1.4, 0.4, 1.15, 1.85, 'paint', bevel=True)
        x = sx * (hw + 0.003)
        (rq if sx > 0 else lq)(m, x, -1.3, 0.3, 1.25, 1.75, 'lineY') if False else None
        for k in range(4):
            (rq if sx > 0 else lq)(m, x, -1.3 + k * 0.42, -1.1 + k * 0.42, 1.2, 1.32, 'lineY')
    m.bm_((0, 0.3, 1.2), (0, 2.9, 3.0), 0.28, 'lineY')
    m.bm_((0, 0.2, 1.2), (0, 0.9, 1.9), 0.2, 'steel')
    m.bm_((0, 2.95, 2.95), (0, 3.15, 1.4), 0.03, 'ink')
    m.cy((0, 3.15, 1.15), 0.09, 0.09, 0.25, 'steelD', seg=6)
    m.bm_((0, 3.1, 1.2), (0, 3.3, 1.05), 0.05, 'pipeR')
    m.bx(-0.9, 0.9, 3.3, 3.75, 0.35, 0.5, 'lineY')
    for sx in (-1, 1):
        m.bx(sx * 0.6 - 0.12, sx * 0.6 + 0.12, 3.4, 3.75, 0.5, 0.62, 'ink')
    make('TowTruck', m, ao, bevel=0.02, cols=[cb(-1.15, -3.75, 0, 1.15, -1.55, 2.6), cb(-1.15, -1.55, 0, 1.15, 3.8, 1.85)])
    # delivery truck (4 x 10) at the dock: tall cab, long box open at the back (roller door up), parcels inside
    m = new(pal)
    hw = 1.25
    for sx in (-1, 1):
        for y in (-3.3, 2.4, 3.45):
            wheel(m, sx * (hw + 0.02), y, 0.5, 0.32)
    m.bx(-0.8, 0.8, -4.4, 4.5, 0.48, 0.95, 'steelD', hull='none')
    truck_cab(m, -4.6, -2.45, 1.2, 3.25)
    m.bx(-hw, hw, -2.35, 4.55, 0.95, 1.05, 'pWhite')                       # floor
    m.bx(-hw, hw, -2.35, 4.55, 3.6, 3.72, 'pWhite')                        # roof
    m.bx(-hw + 0.08, hw - 0.08, -2.35, -2.25, 1.05, 3.6, 'pWhite', hull='none')   # front wall
    for sx in (-1, 1):
        a, b = sorted((sx * hw, sx * (hw - 0.08)))
        m.bx(a, b, -2.35, 4.55, 1.05, 3.6, 'pWhite')
        x = sx * (hw + 0.003)
        f = rq if sx > 0 else lq
        f(m, x, -2.1, 4.35, 1.5, 2.05, 'signB')
        f(m, x, -2.1, 4.35, 2.12, 2.22, 'lineY')
        xi = sx * (hw - 0.083)
        (lq if sx > 0 else rq)(m, xi, -2.25, 4.55, 1.05, 3.6, 'interior')
    dq(m, -hw + 0.08, hw - 0.08, -2.25, 4.55, 3.597, 'interior')
    bq(m, -hw + 0.08, hw - 0.08, -2.247, 1.05, 3.6, 'interior')
    uq(m, -hw + 0.08, hw - 0.08, -2.25, 4.55, 1.053, 'steelD')
    m.cy((-hw + 0.08, 4.4, 3.42), 0.15, 0.15, 2 * hw - 0.16, 'galv', seg=8, rot=(0, 90, 0))   # rolled-up door
    for i, (x0, y0, z0, h) in enumerate(((-1.0, 2.6, 1.05, 0.7), (-0.2, 2.9, 1.05, 0.55), (0.45, 2.4, 1.05, 0.8), (-0.9, 2.7, 1.75, 0.5), (0.5, 2.5, 1.85, 0.45), (-0.4, 0.8, 1.05, 0.9))):
        m.bx(x0, x0 + 0.6, y0, y0 + 0.6, z0, z0 + h, 'cardb')
        uq(m, x0 + 0.26, x0 + 0.34, y0 + 0.02, y0 + 0.58, z0 + h + 0.003, 'wood')
    for sx in (-1, 1):
        a, b = sorted((sx * (hw - 0.02), sx * (hw - 0.3)))
        m.bx(a, b, 4.55, 4.6, 0.6, 0.85, 'red', hull='none')
    m.bx(-hw, hw, 4.5, 4.62, 0.48, 0.6, 'lineY')
    make('DeliveryTruck', m, ao, bevel=0.02, cols=[cb(-1.3, -4.75, 0, 1.3, -2.4, 3.25), cb(-1.3, -2.4, 0, 1.3, 4.6, 1.05),
                                                    cb(-1.3, -2.4, 1.05, -1.17, 4.6, 3.72), cb(1.17, -2.4, 1.05, 1.3, 4.6, 3.72),
                                                    cb(-1.3, -2.4, 3.6, 1.3, 4.6, 3.72), cb(-1.3, -2.4, 1.05, 1.3, -2.25, 3.6)])


# ---------------------------------------------------------------- two wheels, buggy
def build_small(pal, ao):
    # motorbike (1 x 2), leaning on its side stand
    m = new(pal)
    m.parent = Matrix.Rotation(math.radians(9), 4, 'Y')
    for y in (-0.72, 0.7):
        m.cy((-0.065, y, 0.31), 0.31, 0.31, 0.13, 'tire', seg=10, rot=(0, 90, 0))
        for sx in (-1, 1):
            m.cy((sx * 0.068 - (0.012 if sx < 0 else 0), y, 0.31), 0.16, 0.16, 0.012, 'chrome', seg=8, rot=(0, 90, 0), hull='none')
    m.bx(-0.13, 0.13, -0.25, 0.3, 0.3, 0.62, 'steelD')                    # engine
    m.bm_((0, 0.7, 0.31), (0, 0.15, 0.75), 0.05, 'steelD')
    m.bm_((0.0, 0.55, 0.29), (0, -0.2, 0.42), 0.042, 'steelD')
    m.bm_((0, -0.72, 0.31), (0, -0.48, 1.0), 0.05, 'chrome')
    m.bx(-0.16, 0.16, -0.42, 0.1, 0.72, 0.95, 'paint', bevel=True)       # tank
    m.bx(-0.13, 0.13, 0.1, 0.7, 0.78, 0.88, 'seat')
    m.bx(-0.11, 0.11, 0.6, 0.95, 0.72, 0.82, 'paint')                    # tail
    m.bx(-0.06, 0.06, 0.92, 0.97, 0.68, 0.76, 'red', hull='none')
    m.bm_((-0.36, -0.46, 1.06), (0.36, -0.46, 1.06), 0.035, 'steelD')
    for sx in (-1, 1):
        m.bx(sx * 0.34 - 0.04, sx * 0.34 + 0.04, -0.5, -0.42, 1.02, 1.1, 'ink')
    m.cy((0, -0.62, 0.98), 0.1, 0.1, 0.08, 'steelD', seg=8, rot=(90, 0, 0))
    m.cy((0, -0.7, 0.98), 0.08, 0.08, 0.004, 'light', seg=8, rot=(90, 0, 0), hull='none')
    m.cy((0.17, -0.1, 0.32), 0.05, 0.05, 0.85, 'chrome', seg=6, rot=(-90, 0, 0))   # exhaust
    m.bx(-0.14, 0.14, -0.85, -0.6, 0.55, 0.62, 'paint')                  # front fender
    m.parent = Matrix.Identity(4)
    m.bm_((0.0, -0.1, 0.35), (-0.28, -0.05, 0.0), 0.025, 'steelD')       # side stand
    make('Motorbike', m, ao, bevel=0.015, cols=[cb(-0.35, -1.0, 0, 0.35, 1.0, 1.1)])
    # scooter (1 x 2): step-through body, small wheels, front shield
    m = new(pal)
    m.parent = Matrix.Rotation(math.radians(-7), 4, 'Y')
    for y in (-0.62, 0.6):
        m.cy((-0.055, y, 0.22), 0.22, 0.22, 0.11, 'tire', seg=10, rot=(0, 90, 0))
        m.cy((0.055, y, 0.22), 0.11, 0.11, 0.01, 'chrome', seg=8, rot=(0, 90, 0), hull='none')
    m.prism([(-0.55, 0.3), (-0.4, 0.3), (-0.36, 1.0), (-0.5, 1.02), (-0.62, 0.55)], -0.17, 0.17, ['paint'], bevel=True)
    m.bx(-0.15, 0.15, -0.4, 0.2, 0.26, 0.34, 'ink')
    m.prism([(0.1, 0.3), (0.85, 0.35), (0.8, 0.7), (0.35, 0.78), (0.1, 0.6)], -0.18, 0.18, ['paint'], bevel=True)
    m.bx(-0.14, 0.14, 0.15, 0.7, 0.78, 0.86, 'seat')
    m.bm_((0, -0.45, 1.0), (0, -0.48, 1.12), 0.05, 'steelD')
    m.bm_((-0.3, -0.48, 1.12), (0.3, -0.48, 1.12), 0.035, 'steelD')
    m.cy((0, -0.53, 1.08), 0.07, 0.07, 0.04, 'light', seg=8, rot=(90, 0, 0), hull='none')
    m.bx(-0.05, 0.05, 0.84, 0.87, 0.5, 0.58, 'red', hull='none')
    m.parent = Matrix.Identity(4)
    make('Scooter', m, ao, bevel=0.015, cols=[cb(-0.3, -0.85, 0, 0.3, 0.88, 1.05)])
    # bike rack (2 x 4): galvanised hoops on a rail, three bicycles
    m = new(pal)
    m.bx(-0.04, 0.04, -1.9, 1.9, 0.0, 0.06, 'steelD', cull='b')
    for y in (-1.8, -0.6, 0.6, 1.8):
        m.bm_((-0.25, y, 0.0), (-0.25, y, 0.75), 0.05, 'galv')
        m.bm_((0.25, y, 0.0), (0.25, y, 0.75), 0.05, 'galv')
        m.bm_((-0.21, y + 0.008, 0.73), (0.21, y + 0.008, 0.73), 0.04, 'galv')
    for y, c in ((-1.2, 'paint'), (0.0, 'pTeal'), (1.2, 'pYellow')):
        for wx in (-0.52, 0.52):
            m.cy((wx, y - 0.025, 0.35), 0.33, 0.33, 0.05, 'tire', seg=12, rot=(-90, 0, 0))
            for sy in (-1, 1):
                m.cy((wx, y + sy * 0.025 - (0.004 if sy < 0 else 0), 0.35), 0.26, 0.26, 0.004, 'galv', seg=12, rot=(-90, 0, 0), hull='none')
                m.cy((wx, y + sy * 0.029 - (0.004 if sy < 0 else 0), 0.35), 0.05, 0.05, 0.004, 'steelD', seg=6, rot=(-90, 0, 0), hull='none')
        for i, (a, b) in enumerate((((-0.52, 0.35), (-0.05, 0.38)), ((-0.05, 0.38), (0.32, 0.78)), ((-0.05, 0.38), (-0.12, 0.82)), ((-0.12, 0.82), (0.32, 0.78)),
                                    ((-0.52, 0.35), (-0.12, 0.82)), ((0.32, 0.78), (0.52, 0.35)))):
            dy = (i % 3 - 1) * 0.007
            m.bm_((a[0], y + dy, a[1]), (b[0], y + dy, b[1]), 0.03, c)
        m.bx(-0.2, -0.04, y - 0.05, y + 0.05, 0.86, 0.9, 'seat')
        m.bm_((0.3, y - 0.22, 0.92), (0.3, y + 0.22, 0.92), 0.03, 'steelD')
    make('BikeRack', m, ao, cols=[cb(-0.9, -1.9, 0, 0.9, 1.9, 0.95)])
    # maintenance buggy (2 x 3): white tub with yellow stripes, canopy, beacon, tool tray
    m = new(pal)
    m.parent = rz(4.0)
    for sx in (-1, 1):
        for y in (-0.85, 0.85):
            wheel(m, sx * 0.66, y, 0.22, 0.16, hub='steelD')
    m.prism([(-1.25, 0.25), (1.25, 0.25), (1.25, 0.62), (-0.7, 0.62), (-1.2, 0.72), (-1.3, 0.45)], -0.6, 0.6, ['pWhite'], bevel=True)
    for sx in (-1, 1):
        (rq if sx > 0 else lq)(m, sx * 0.603, -1.2, 1.2, 0.36, 0.46, 'lineY')
    m.bx(-0.55, 0.55, -0.2, 0.35, 0.62, 0.85, 'seat')
    m.bx(-0.55, 0.55, 0.3, 0.42, 0.85, 1.35, 'seat')
    for sx in (-1, 1):
        for y in (-0.6, 0.45):
            m.bx(sx * 0.52 - 0.025, sx * 0.52 + 0.025, y - 0.025, y + 0.025, 0.62, 1.85, 'steelD')
    m.bx(-0.65, 0.65, -0.75, 0.6, 1.85, 1.93, 'pWhite')
    m.cy((0, -0.1, 1.93), 0.09, 0.07, 0.14, 'litA', seg=8)
    m.bx(-0.55, 0.55, 0.55, 1.2, 0.62, 0.95, 'steelD')
    uq(m, -0.52, 0.52, 0.58, 1.17, 0.953, 'steel')
    m.bx(-0.4, 0.0, 0.7, 0.95, 0.95, 1.15, 'pipeR')
    m.cy((0.25, 0.95, 0.95), 0.12, 0.03, 0.4, 'cone', seg=8)
    m.bm_((-0.3, -0.75, 0.75), (-0.3, -0.55, 1.15), 0.04, 'ink')
    m.parent = Matrix.Identity(4)
    make('Buggy', m, ao, bevel=0.015, cols=[rot_box(2.6, 1.35, 4.0, 1.0)])
