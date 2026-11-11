"""kit-techhq furniture, labs, terrace and landmarks (see fam_kit_techhq.py for the conventions).

Every piece faces Blender -Y (game +Z) and is centred on its footprint; collision boxes follow what is drawn at
player height (no invisible walls), walkable boxes only where people stand on them (the stage).
"""
import math

import fam_kit_office as O
import ib_text
from fam_kit_techhq import BRAND, BRAND_FONT, DECK, glint_x, glint_y, logo_mark, srt

# ---------------------------------------------------------------- small helpers (local frames face -Y)


def laptop(k, x, y, deg, z0, c='alu', ang=110, scr='code', s=1.0):
    """An open laptop: base with a keyboard, lid opened `ang` degrees from the base, a screen with code or UI."""
    k.push(x, y, deg, z0)
    W, D, L, t = 0.33 * s, 0.23 * s, 0.22 * s, 0.009
    k.bx(-W / 2, W / 2, -D / 2, D / 2, 0, 0.016, c)
    k.qz(-W / 2 + 0.02, W / 2 - 0.02, -D / 2 + 0.07 * s, D / 2 - 0.015, 0.019, 1, 'graphite')
    k.qz(-0.05 * s, 0.05 * s, -D / 2 + 0.012, -D / 2 + 0.06 * s, 0.019, 1, 'graphite2')
    a = math.radians(ang)
    dy, dz = -math.cos(a), math.sin(a)          # base points -Y from the hinge; the lid leans back
    yh, zh = D / 2 - 0.004, 0.016
    nx, nz = -dz, dy                            # normal of the lid's screen face (toward the front)
    p = [(yh, zh), (yh + L * dy, zh + L * dz), (yh + L * dy + t * nx, zh + L * dz + t * nz), (yh + t * nx, zh + t * nz)]
    k.prism_y(p, -W / 2, W / 2, c)
    o = t + 0.003
    sp = lambda u, v: (u, yh + (v * L) * dy + o * nx, zh + (v * L) * dz + o * nz)
    m = 0.018 * s
    k.poly([sp(-W / 2 + m, 0.08), sp(W / 2 - m, 0.08), sp(W / 2 - m, 0.94), sp(-W / 2 + m, 0.94)], 'screenD' if scr == 'code' else scr, (0, -dz, -dy))
    if scr == 'code':
        for i in range(3):
            v = 0.8 - i * 0.2
            w0 = -W / 2 + m + 0.02 + 0.03 * (i % 3)
            w1 = w0 + (0.08 + 0.05 * ((i * 7) % 4)) * s
            oo = o + 0.003
            q = lambda u, vv: (u, yh + (vv * L) * dy + oo * nx, zh + (vv * L) * dz + oo * nz)
            k.poly([q(w0, v), q(w1, v), q(w1, v + 0.06), q(w0, v + 0.06)], ('code', 'sky', 'pink', 'code', 'sun')[i], (0, -dz, -dy))
    k.pop()


def monitor(k, x, y, deg, z0, wide=1.0, content='code', arm=False):
    """Slim monitor (black, thin bezel) on a stand or a desk arm; screen faces local -Y."""
    k.push(x, y, deg, z0)
    w = 0.3 * wide
    if arm:
        k.bx(-0.02, 0.02, 0.1, 0.14, 0.0, 0.42, 'steel', ink=False)
        k.bx(-0.015, 0.015, 0.03, 0.1, 0.36, 0.4, 'steel', ink=False)
    else:
        k.bx(-0.018, 0.018, 0.04, 0.07, 0.0, 0.2, 'steel', ink=False)
    k.bx(-w, w, 0.0, 0.025, 0.14, 0.5, 'black')
    k.qy(-w + 0.012, w - 0.012, 0.152, 0.488, -0.003, -1, 'screenD')
    if content == 'code':
        for i in range(4):
            z = 0.44 - i * 0.07
            x0 = -w + 0.04 + 0.03 * ((i * 5) % 4)
            k.qy(x0, x0 + (0.08 + 0.04 * ((i * 3) % 5)) * wide, z, z + 0.018, -0.006, -1, ('code', 'sky', 'code', 'pink', 'sun', 'code', 'sky')[i])
    elif content == 'chart':
        for i in range(6):
            xx = -w + 0.05 + i * (2 * w - 0.1) / 6
            k.qy(xx, xx + 0.03 * wide, 0.18, 0.2 + 0.04 * ((i * 3) % 7), -0.006, -1, ('mint', 'violet', 'sun', 'mint', 'coral', 'sky')[i])
    elif content == 'cad':
        k.qy(-w * 0.6, w * 0.6, 0.22, 0.24, -0.006, -1, 'sky')
        k.qy(-w * 0.5, w * 0.5, 0.24, 0.41, -0.006, -1, 'graphite2')
        k.qy(-w * 0.45, w * 0.45, 0.27, 0.38, -0.009, -1, 'sky')
    else:
        k.qy(-w + 0.03, w - 0.03, 0.42, 0.46, -0.006, -1, content)
        k.qy(-w + 0.03, -w + 0.15, 0.18, 0.4, -0.006, -1, 'graphite2')
    k.pop()


def keyboard(k, x, y, deg, z0):
    k.push(x, y, deg, z0)
    k.bx(-0.21, 0.21, -0.065, 0.065, 0, 0.018, 'graphite2', ink=False)
    k.pop()


def chair(k, x, y, deg, c='violet'):
    """Mesh-back task chair (white base, coloured seat); the sitter faces local -Y."""
    k.push(x, y, deg)
    k.cyl(0, 0, 0.03, 0.27, 0.27, 0.05, 'wallW', seg=5, ink=False)
    k.bx(-0.022, 0.022, -0.022, 0.022, 0.08, 0.42, 'steelD', ink=False)
    k.bx(-0.23, 0.23, -0.24, 0.22, 0.42, 0.5, c)
    k.prism_y([(0.2, 0.52), (0.26, 0.52), (0.3, 1.02), (0.24, 1.02)], -0.21, 0.21, 'graphite')
    k.poly([(-0.17, 0.2335, 0.58), (0.17, 0.2335, 0.58), (0.17, 0.2635, 0.97), (-0.17, 0.2635, 0.97)], c, (0, -1, 0.08))
    k.pop()


def stool(k, x, y, c='oak', h=0.75):
    k.cyl(x, y, 0, 0.2, 0.2, 0.03, 'steelD', seg=8, ink=False)
    k.cyl(x, y, 0.03, 0.025, 0.025, h - 0.06, 'steel', seg=6, ink=False)
    k.cyl(x, y, h - 0.05, 0.19, 0.19, 0.06, c, seg=7)


def desk(k, x0, x1, y0, y1, h, top='wallW', leg='steel'):
    """Sit-stand desk: a top on a T-frame (two lifting columns, feet, a crossbar)."""
    k.bx(x0, x1, y0, y1, h - 0.03, h, top)
    k.qy(x0 + 0.002, x1 - 0.002, h - 0.028, h - 0.004, y0 - 0.003, -1, 'oak' if top == 'wallW' else 'wallW')
    for x in (x0 + 0.15, x1 - 0.15):
        k.bx(x - 0.04, x + 0.04, (y0 + y1) / 2 - 0.05, (y0 + y1) / 2 + 0.05, 0.03, h - 0.03, leg, ink=False)
        k.bx(x - 0.03, x + 0.03, y0 + 0.06, y1 - 0.06, 0, 0.03, leg, ink=False)


def plant_pot(k, x, y, z, s=1.0, kind='monstera', pot='pot'):
    """Floor / desk plant: a white pot with a monstera, a snake plant or a little palm."""
    k.cyl(x, y, z, 0.2 * s, 0.16 * s, 0.4 * s, pot, seg=10)
    k.cyl(x, y, z + 0.4 * s, 0.18 * s, 0.18 * s, 0.004, 'soil', seg=10, ink=False)
    zt = z + 0.4 * s
    if kind == 'monstera':
        for i in range(7):
            a = i / 7 * math.pi * 2 + 0.3
            r = (0.28 + 0.1 * (i % 2)) * s
            k.beam((x, y, zt), (x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6, zt + (0.45 + 0.12 * (i % 3)) * s), 0.015, 'leaf2', ink=False)
            k.sph(x + math.cos(a) * r, y + math.sin(a) * r, zt + (0.5 + 0.12 * (i % 3)) * s, 0.17 * s, 'leaf' if i % 2 else 'leaf2', seg=(6, 3), scale=(1, 1, 0.35))
    elif kind == 'snake':
        for i in range(8):
            a = i / 8 * math.pi * 2
            k.beam((x + math.cos(a) * 0.05 * s, y + math.sin(a) * 0.05 * s, zt), (x + math.cos(a) * 0.12 * s, y + math.sin(a) * 0.12 * s, zt + (0.5 + 0.12 * (i % 3)) * s), 0.05 * s, 'leaf' if i % 2 else 'leafL')
    else:
        for i in range(6):
            a = i / 6 * math.pi * 2
            mid = (x + math.cos(a) * 0.1 * s, y + math.sin(a) * 0.1 * s, zt + 0.55 * s)
            k.beam((x + math.cos(a) * 0.03, y + math.sin(a) * 0.03, zt), mid, 0.02, 'bark', ink=False)
            k.beam(mid, (x + math.cos(a) * 0.45 * s, y + math.sin(a) * 0.45 * s, zt + 0.4 * s), 0.08 * s, 'leaf' if i % 2 else 'leafL')


def glass_run(k, ax, fixed, a0, a1, h, frame='wallW', strip='violet'):
    """A run of glass wall (prefab pods and rooms): shoe and head rails, a manifestation strip, glints and a thin
    collision box. ax 'x': runs along x at y = fixed; 'y': along y at x = fixed."""
    if ax == 'x':
        k.bx(a0, a1, fixed - 0.03, fixed + 0.03, 0, 0.07, frame, ink=False)
        k.bx(a0, a1, fixed - 0.03, fixed + 0.03, h - 0.08, h, frame, ink=False)
        k.bx(a0, a1, fixed - 0.009, fixed + 0.009, 1.0, 1.4, strip, ink=False)
        for s in (-1, 1):
            glint_y(k, (a0 + a1) / 2 - 0.2, fixed + s * 0.012, 1.6, 0.7, s)
        k.col(a0, a1, fixed - 0.05, fixed + 0.05, 0, h)
    else:
        k.bx(fixed - 0.03, fixed + 0.03, a0, a1, 0, 0.07, frame, ink=False)
        k.bx(fixed - 0.03, fixed + 0.03, a0, a1, h - 0.08, h, frame, ink=False)
        k.bx(fixed - 0.009, fixed + 0.009, a0, a1, 1.0, 1.4, strip, ink=False)
        for s in (-1, 1):
            glint_x(k, fixed + s * 0.012, (a0 + a1) / 2 - 0.2, 1.6, 0.7, s)
        k.col(fixed - 0.05, fixed + 0.05, a0, a1, 0, h)


# ================================================================ reception and showroom (zone 1)
def reception(k):
    """Landmark: 6 x 3 reception desk facing -Y: a white solid-surface front with a rounded end, an oak top, a
    violet light line along the plinth, NOVYX lettering; staff side with screens, laptops, chairs and a vase."""
    k.begin()
    k.bx(-2.2, 2.2, -0.6, 0.2, 0, 1.08, 'wallW')
    k.cyl(-2.2, -0.2, 0, 0.4, 0.4, 1.07, 'wallW', seg=14)
    k.bx(-2.4, 2.45, -0.75, 0.25, 1.08, 1.13, 'oak')
    k.cyl(-2.2, -0.2, 1.083, 0.55, 0.55, 0.044, 'oak', seg=14)
    k.bx(-2.2, 2.2, -0.63, -0.6, 0.0, 0.08, 'violet', ink=False)
    ib_text.draw(k, BRAND, 0.35, -0.603, 0.45, 0.3, 'graphite', face='y-', font=BRAND_FONT, maxw=2.6)
    logo_mark(k, -1.75, -0.6, 0.42, 0.34, -1)
    k.bx(-2.0, 2.2, 0.2, 0.7, 0.72, 0.75, 'oak2')
    for x in (-1.85, 2.05):
        k.bx(x - 0.03, x + 0.03, 0.25, 0.65, 0, 0.72, 'steel', ink=False)
    for (x, c) in ((-1.0, 'violet'), (0.6, 'mint')):
        monitor(k, x, 0.38, 180, 0.75, 1.0, 'chart' if x < 0 else 'code')
        keyboard(k, x, 0.58, 180, 0.75)
        chair(k, x + 0.05, 1.1, 4 if x > 0 else -7, c)
    laptop(k, 1.6, 0.45, 165, 0.75, 'alu', 105, 'screen')
    k.cyl(1.9, -0.45, 1.13, 0.07, 0.06, 0.25, 'pot', seg=8)
    for (dx, dz, c) in ((0.0, 0.42, 'pink'), (-0.06, 0.36, 'coral'), (0.07, 0.34, 'sun')):
        k.beam((1.9 + dx * 0.3, -0.45 + dz * 0.02, 1.35), (1.9 + dx, -0.45, 1.13 + dz), 0.008, 'leaf2', ink=False)
        k.sph(1.9 + dx, -0.45, 1.13 + dz + 0.03, 0.05, c, seg=(5, 3), ink=False)
    k.bx(-0.6, -0.2, -0.6, -0.35, 1.13, 1.16, 'paper', ink=False)
    k.col(-2.6, 2.45, -0.75, 0.25, 0, 1.13)
    k.col(-2.0, 2.2, 0.25, 0.7, 0, 0.75)
    return k


def logo_wall(k):
    """Landmark: 14 x 2 freestanding feature wall 6.5 m tall. Front (-Y, the arrival): oak slats with the giant NOVYX
    letters and the mark, a tagline. Back (+Y, the stage): a 12 x 4.6 m LED wall showing the keynote slide of the
    NOVYX Air 14 (laptop silhouette, name, colour bars)."""
    k.begin()
    Hw = 6.5
    k.bx(-7.0, 7.0, -0.35, 0.35, 0.0, 0.25, 'graphite')
    k.bx(-6.9, 6.9, -0.3, 0.3, 0.25, Hw, 'wallW')
    k.bx(-6.9, 6.9, -0.36, -0.3, 0.25, Hw - 0.2, 'oak2', ink=False)
    for i in range(31):
        x = -6.75 + i * 0.45
        k.bx(x - 0.1, x + 0.1, -0.42, -0.36, 0.3, Hw - 0.25, 'oak', ink=False)
    k.bx(-6.9, 6.9, -0.38, 0.38, Hw, Hw + 0.12, 'graphite')
    k.bx(-5.6, 5.6, -0.48, -0.42, 2.0, 4.9, 'wallW', ink=False)
    cap = 2.05
    tw = min(ib_text.width(BRAND, BRAND_FONT, cap), 10.6 - 1.9 * cap)
    x0 = -(1.5 * cap + 0.4 * cap + tw) / 2
    logo_mark(k, x0, -0.48, 2.4, cap, -1, 0.006)
    ib_text.draw(k, BRAND, x0 + 1.9 * cap, -0.483, 2.4, cap, 'graphite', face='y-', font=BRAND_FONT, align='l', maxw=tw,
                 shadow='violet', shadow_off=(0.03, -0.035))
    ib_text.draw(k, 'THINK LIGHTER.', 0.0, -0.423, 1.15, 0.32, 'graphite', face='y-', font='cond', maxw=5.0)
    # back: the LED wall of the demo stage
    k.bx(-6.2, 6.2, 0.3, 0.36, 1.2, 5.8, 'black')
    k.qy(-6.05, 6.05, 1.32, 5.68, 0.363, 1, 'screenD')
    for i, c in enumerate(('violet', 'coral', 'sun', 'mint', 'sky')):
        k.qy(3.4 - i * 0.5, 3.2 - i * 0.5 + 0.6, 1.6, 1.75, 0.366, 1, c)
    # laptop silhouette (seen from +Y: x runs to the left)
    k.poly([(2.6, 0.366, 3.0), (-2.6, 0.366, 3.0), (-2.2, 0.366, 3.15), (2.2, 0.366, 3.15)], 'steel', (0, 1, 0))
    k.qy(-2.0, 2.0, 3.15, 5.2, 0.366, 1, 'steel')
    k.qy(-1.85, 1.85, 3.3, 5.05, 0.369, 1, 'violet')
    k.qy(-1.85, 0.2, 3.3, 5.05, 0.372, 1, 'violetD')
    ib_text.draw(k, BRAND + ' AIR 14', 0.0, 0.366, 2.1, 0.45, 'white', face='y+', font=BRAND_FONT, maxw=5.0)
    ib_text.draw(k, '980 g  /  22 h  /  NyxOS 9', 0.0, 0.366, 1.95 - 0.38, 0.2, 'screen', face='y+', font='cond', maxw=5.5)
    k.col(-7.0, 7.0, -0.42, 0.36, 0, Hw + 0.12)
    return k


def stage(k):
    """8 x 3 demo stage (front -Y): a 0.3 m oak platform with a black skirt and a violet light line, a lectern, the
    product on a turntable, two lights on stands, a confidence monitor on the floor. Its top is walkable."""
    k.begin()
    k.bx(-4.0, 4.0, -1.5, 1.5, 0.0, 0.27, 'graphite')
    k.bx(-4.0, 4.0, -1.5, 1.5, 0.27, 0.3, 'oak')
    k.bx(-3.95, 3.95, -1.52, -1.5, 0.06, 0.1, 'violet', ink=False)
    k.col(-4.0, 4.0, -1.5, 1.5, 0, 0.3, True)
    # lectern
    k.prism([(-0.3, 0.3), (0.3, 0.3), (0.26, 1.1), (-0.32, 1.12)], -0.85, -0.45, 'wallW')
    k.bx(-0.36, 0.34, -0.9, -0.42, 1.1, 1.15, 'oak')
    logo_mark(k, -0.15, -0.9, 0.6, 0.2, -1, 0.004)
    laptop(k, 0.0, -0.66, 0, 1.15, 'graphite2', 108, 'code', 0.8)
    k.col(-0.36, 0.34, -0.9, -0.42, 0.3, 1.15)
    # the turntable with the Air 14
    k.cyl(2.1, 0.0, 0.3, 0.45, 0.45, 0.55, 'wallW', seg=14)
    k.cyl(2.1, 0.0, 0.85, 0.5, 0.5, 0.04, 'violet', seg=14)
    laptop(k, 2.1, 0.0, -25, 0.89, 'alu', 115, 'violet', 1.4)
    k.col(1.65, 2.55, -0.45, 0.45, 0.3, 0.89)
    # stage lights on stands and the confidence monitor
    for sx in (-3.5, 3.5):
        k.cyl(sx, 1.0, 0.3, 0.18, 0.18, 0.03, 'black', seg=8, ink=False)
        k.cyl(sx, 1.0, 0.33, 0.025, 0.025, 1.9, 'black', seg=6, ink=False)
        k.push(sx, 1.0, 35 if sx < 0 else -35, 2.2)
        k.bx(-0.12, 0.12, -0.18, 0.12, 0, 0.22, 'black')
        k.qy(-0.09, 0.09, 0.03, 0.19, -0.183, -1, 'glow')
        k.pop()
        k.col(sx - 0.15, sx + 0.15, 0.85, 1.15, 0.3, 2.4)
    k.push(-1.6, -1.1, 0, 0.3)
    k.prism_y([(-0.15, 0.0), (0.15, 0.0), (0.0, 0.32)], -0.3, 0.3, 'black')
    k.poly([(-0.27, -0.06, 0.06), (0.27, -0.06, 0.06), (0.27, 0.07, 0.29), (-0.27, 0.07, 0.29)], 'screenD', (0, -1, 0.5))
    k.pop()
    return k


def display_table(k, v):
    """4 x 2 product table: an oak top on white trestles, laptops open at angles (A: the Air range in four colours,
    B: the Pro with a tablet on a stand and headphones), product cards."""
    k.begin()
    k.bx(-1.9, 1.9, -0.75, 0.75, 0.86, 0.9, 'oak')
    for x in (-1.5, 1.5):
        k.bx(x - 0.04, x + 0.04, -0.6, 0.6, 0, 0.86, 'wallW')
    k.bx(-1.46, 1.46, -0.03, 0.03, 0.3, 0.36, 'wallW', ink=False)
    if v == 'A':
        for (x, y, d, c) in ((-1.4, -0.3, 20, 'alu'), (-0.5, 0.25, -10, 'violet'), (0.45, -0.25, 15, 'coral'), (1.35, 0.3, -20, 'mint')):
            laptop(k, x, y, d, 0.9, c, 110, 'code' if c == 'alu' else 'screen')
        for x in (-1.0, 0.95):
            k.qz(x - 0.08, x + 0.08, -0.6, -0.5, 0.903, 1, 'paper')
    else:
        laptop(k, -1.2, -0.2, 15, 0.9, 'graphite2', 105, 'code', 1.15)
        laptop(k, 0.9, 0.2, -12, 0.9, 'graphite2', 112, 'screen', 1.15)
        k.push(-0.1, 0.25, 0, 0.9)
        k.bx(-0.08, 0.08, -0.06, 0.06, 0, 0.02, 'steel', ink=False)
        k.poly([(-0.14, 0.02, 0.05), (0.14, 0.02, 0.05), (0.14, 0.08, 0.27), (-0.14, 0.08, 0.27)], 'black', (0, -1, 0.3))
        k.poly([(-0.125, 0.017, 0.062), (0.125, 0.017, 0.062), (0.125, 0.071, 0.26), (-0.125, 0.071, 0.26)], 'sky', (0, -1, 0.3))
        k.pop()
        k.cyl(1.6, -0.45, 0.9, 0.06, 0.06, 0.25, 'wallW', seg=6, ink=False)
        k.sph(1.6, -0.45, 1.2, 0.09, 'coral', seg=(6, 4), scale=(1.2, 0.5, 1))
        k.qz(-0.6, -0.4, -0.65, -0.55, 0.903, 1, 'paper')
    k.col(-1.9, 1.9, -0.75, 0.75, 0, 0.9)
    return k


def plinth(k, v):
    """1 x 1 white plinth (1 m) with a product under a light: A an open laptop, B a stack of laptops in the range
    colours, C the 27-inch display."""
    k.begin()
    k.bx(-0.35, 0.35, -0.35, 0.35, 0, 1.0, 'wallW')
    k.bx(-0.37, 0.37, -0.37, 0.37, 1.0, 1.03, 'oak')
    k.bx(-0.36, 0.36, -0.36, 0.36, 0, 0.05, 'black', ink=False)
    k.qy(-0.3, 0.3, 0.12, 0.15, -0.353, -1, 'violet')
    if v == 'A':
        laptop(k, 0, 0, 15, 1.03, 'alu', 112, 'code')
        k.qz(-0.3, -0.1, -0.33, -0.25, 1.033, 1, 'paper')
    elif v == 'B':
        for i, c in enumerate(('alu', 'violet', 'coral', 'mint')):
            k.push(0, 0, -10 + i * 9, 1.03 + i * 0.02)
            k.bx(-0.16, 0.16, -0.11, 0.11, 0, 0.018, c)
            k.pop()
    else:
        monitor(k, 0, 0.05, 0, 1.03, 1.45, 'cad')
    k.col(-0.37, 0.37, -0.37, 0.37, 0, 1.03)
    return k


def shelf_acc(k):
    """3 x 1 accessory wall shelving (back to +Y): white frame, oak shelves, boxed products in the brand colours,
    headphones, chargers, sleeves."""
    k.begin()
    for x in (-1.45, -0.5, 0.5, 1.45):
        k.bx(x - 0.03, x + 0.03, -0.25, 0.25, 0, 2.2, 'wallW')
    k.bx(-1.48, 1.48, 0.25, 0.3, 0, 2.2, 'wallW')
    for z in (0.1, 0.6, 1.1, 1.6, 2.1):
        k.bx(-1.42, 1.42, -0.24, 0.24, z, z + 0.04, 'oak')
    cols = ('violet', 'coral', 'sun', 'mint', 'sky', 'wallW', 'graphite2')
    for si, z in enumerate((0.14, 0.64, 1.14, 1.64)):
        for bay in range(3):
            x0 = -1.42 + bay * 0.95
            for j in range(2):
                c = cols[(si * 3 + bay * 2 + j) % len(cols)]
                xx = x0 + 0.12 + j * 0.42
                h = 0.22 + 0.08 * ((si + j + bay) % 3)
                k.bx(xx, xx + 0.2, -0.18, 0.12, z, z + h, c, ink=False)
                k.qy(xx + 0.03, xx + 0.17, z + h - 0.08, z + h - 0.04, -0.183, -1, 'wallW' if c != 'wallW' else 'violet')
    k.col(-1.48, 1.48, -0.25, 0.3, 0, 2.2)
    return k


def lockers(k):
    """3 x 1 order-pickup lockers (back to +Y): a white grid of doors with violet number tabs, a touch screen in
    the middle column, an oak plinth."""
    k.begin()
    k.bx(-1.48, 1.48, -0.3, 0.3, 0.1, 2.0, 'wallW')
    k.bx(-1.48, 1.48, -0.28, 0.3, 0.0, 0.1, 'oak2')
    for col in range(5):
        x0 = -1.42 + col * 0.57
        for row in range(4):
            z0 = 0.16 + row * 0.46
            if col == 2 and row in (1, 2):
                continue
            k.qy(x0 + 0.02, x0 + 0.53, z0, z0 + 0.42, -0.303, -1, 'cushion')
            k.qy(x0 + 0.06, x0 + 0.14, z0 + 0.32, z0 + 0.38, -0.306, -1, 'violet' if (col + row) % 3 else 'mint')
    k.bx(-0.24, 0.24, -0.34, -0.3, 0.7, 1.5, 'black')
    k.qy(-0.21, 0.21, 0.74, 1.46, -0.343, -1, 'screenD')
    logo_mark(k, -0.1, -0.343, 1.25, 0.12, -1, 0.003)
    k.qy(-0.15, 0.15, 0.9, 0.98, -0.346, -1, 'mint')
    k.col(-1.48, 1.48, -0.34, 0.3, 0, 2.0)
    return k


def lounge(k, v):
    """4 x 3 modular sofa (an L of cushioned blocks in the brand fabric), an oak coffee table with laptops and cups,
    a pouf; A violet, B mint."""
    k.begin()
    c = 'violet' if v == 'A' else 'mint'
    k.bx(-1.8, 1.2, 0.55, 1.4, 0.0, 0.42, 'sofa')
    k.bx(-1.8, 1.2, 1.12, 1.45, 0.42, 0.85, 'sofa')
    for x in (-1.3, -0.3, 0.7):
        k.bx(x - 0.48, x + 0.48, 0.58, 1.1, 0.42, 0.52, c)
    k.bx(1.2, 1.9, -0.6, 1.45, 0.0, 0.42, 'sofa')
    k.bx(1.57, 1.92, -0.6, 1.12, 0.42, 0.85, 'sofa')
    k.bx(1.22, 1.55, -0.55, 1.08, 0.42, 0.52, c)
    for (x, y) in ((-1.0, 1.25), (0.4, 1.28), (1.72, 0.2)):
        k.bx(x - 0.22, x + 0.22, y - 0.08, y + 0.08, 0.52, 0.82, 'cushion' if v == 'A' else 'sun')
    k.cyl(-0.3, -0.35, 0, 0.55, 0.55, 0.36, 'oak', seg=14)
    k.cyl(-0.3, -0.35, 0.36, 0.58, 0.58, 0.03, 'oak2', seg=14)
    laptop(k, -0.45, -0.3, 160, 0.39, 'alu', 108, 'code', 0.9)
    O.mug(k, -0.05, -0.55, 0.39, 'white')
    k.cyl(-1.5, -0.9, 0, 0.3, 0.28, 0.38, 'sun' if v == 'A' else 'coral', seg=10)
    k.col(-1.8, 1.9, 0.55, 1.45, 0, 0.85)
    k.col(1.2, 1.92, -0.6, 0.55, 0, 0.85)
    k.col(-0.8, 0.2, -0.85, 0.15, 0, 0.39)
    k.col(-1.75, -1.25, -1.15, -0.65, 0, 0.38)
    return k


def beanbag(k, c):
    k.begin()
    k.sph(0, 0, 0.26, 0.42, c, seg=(9, 6), scale=(1.0, 1.0, 0.62))
    k.sph(0.05, 0.1, 0.5, 0.3, c, seg=(8, 5), scale=(1.0, 0.8, 0.6))
    k.cyl(0, 0, 0.0, 0.3, 0.3, 0.01, c, seg=9, ink=False)
    k.col(-0.36, 0.36, -0.36, 0.36, 0, 0.55)
    return k


def planter(k, v):
    """A: a white drum with a fiddle-leaf fig; B: a terracotta box of grasses."""
    k.begin()
    if v == 'A':
        k.cyl(0, 0, 0, 0.34, 0.3, 0.7, 'pot', seg=12)
        k.cyl(0, 0, 0.7, 0.31, 0.31, 0.004, 'soil', seg=12, ink=False)
        k.cyl(0, 0, 0.704, 0.035, 0.03, 1.0, 'bark', seg=5, ink=False)
        for (x, y, z, r) in ((0.0, 0.0, 1.85, 0.32), (0.2, -0.1, 1.55, 0.26), (-0.18, 0.12, 1.45, 0.27), (0.06, 0.2, 1.25, 0.22)):
            k.sph(x, y, z, r, 'leaf' if r > 0.25 else 'leaf2', seg=(6, 4))
        k.col(-0.3, 0.3, -0.3, 0.3, 0, 0.7)
    else:
        k.bx(-0.38, 0.38, -0.38, 0.38, 0, 0.6, 'terra')
        k.qz(-0.34, 0.34, -0.34, 0.34, 0.603, 1, 'soil')
        for i in range(10):
            a = i / 10 * math.pi * 2
            k.beam((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.6), (math.cos(a) * 0.42, math.sin(a) * 0.42, 1.25 + 0.1 * (i % 3)), 0.045, 'leafL' if i % 2 else 'leaf')
        k.col(-0.38, 0.38, -0.38, 0.38, 0, 0.6)
    return k


def planter_tree(k):
    """2 x 2 oak-clad planter box with a small multi-stem tree."""
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.55, 'oak')
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):
        k.qy(x - 0.005, x + 0.005, 0.03, 0.52, -0.903, -1, 'oak2')
        k.qx(x - 0.005, x + 0.005, 0.03, 0.52, 0.903, 1, 'oak2')
    k.bx(-0.93, 0.93, -0.93, 0.93, 0.55, 0.6, 'wallW')
    k.qz(-0.85, 0.85, -0.85, 0.85, 0.603, 1, 'soil')
    for (dx, dy, tx, ty) in ((0.0, 0.0, 0.1, 0.0), (0.15, 0.1, 0.5, 0.35), (-0.1, 0.1, -0.45, 0.3)):
        k.beam((dx, dy, 0.6), (tx, ty, 2.2), 0.08, 'bark')
    for i, (x, y, z, r, c) in enumerate(((0.0, 0.0, 2.75, 0.75, 'leaf'), (0.55, 0.35, 2.4, 0.5, 'leafL'), (-0.5, 0.3, 2.45, 0.52, 'leaf2'),
                                         (0.2, -0.45, 2.4, 0.45, 'leafL'), (-0.3, -0.35, 2.85, 0.47, 'leaf'))):
        k.sph(x, y, z, r, c, seg=(7, 4), scale=(1, 1, 0.78 + 0.03 * i))
    k.col(-0.93, 0.93, -0.93, 0.93, 0, 0.6)
    k.col(-0.2, 0.25, -0.15, 0.2, 0.6, 2.0)
    return k


def plant(k, v):
    k.begin()
    kind = {'A': 'monstera', 'B': 'snake', 'C': 'palm'}[v]
    plant_pot(k, 0, 0, 0, 1.25, kind, 'pot' if v != 'B' else 'terra')
    k.col(-0.25, 0.25, -0.25, 0.25, 0, 0.5)
    return k


def pod(k, v):
    """4 x 4 glass meeting pod (doorway in the front, -Y): white frame, glass with a manifestation strip, a felt roof
    with an oak fascia; A: round table, four chairs, a screen; B: a whiteboard wall and a high table with stools."""
    k.begin()
    G, Hp = 1.9, 2.7
    for (x, y) in ((-G, -G), (G, -G), (-G, G), (G, G), (-0.5, -G), (0.45, -G)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, Hp, 'wallW')
    glass_run(k, 'x', -G, -G + 0.05, -0.55, Hp)
    glass_run(k, 'x', -G, 0.5, G - 0.05, Hp)
    glass_run(k, 'x', G, -G + 0.05, G - 0.05, Hp)
    glass_run(k, 'y', -G, -G + 0.05, G - 0.05, Hp)
    glass_run(k, 'y', G, -G + 0.05, G - 0.05, Hp)
    k.bx(-0.45, 0.4, -G - 0.03, -G + 0.03, Hp - 0.25, Hp, 'wallW', ink=False)       # door head
    k.bx(-G - 0.1, G + 0.1, -G - 0.1, G + 0.1, Hp, Hp + 0.18, 'oak')
    k.qz(-G + 0.05, G - 0.05, -G + 0.05, G - 0.05, Hp - 0.003, -1, 'felt')
    k.cyl(0, 0, Hp - 0.25, 0.4, 0.4, 0.2, 'violet' if v == 'A' else 'mint', seg=8)
    k.cyl(0, 0, Hp - 0.254, 0.32, 0.32, 0.004, 'glow', seg=8, ink=False)
    if v == 'A':
        k.cyl(0, 0.2, 0, 0.25, 0.25, 0.04, 'steel', seg=10, ink=False)
        k.cyl(0, 0.2, 0.04, 0.05, 0.05, 0.68, 'steel', seg=6, ink=False)
        k.cyl(0, 0.2, 0.72, 0.6, 0.6, 0.04, 'oak', seg=14)
        laptop(k, 0.15, 0.1, 200, 0.76, 'alu', 110, 'code', 0.9)
        for i, a in enumerate((20, 110, 200, 290)):
            r = math.radians(a)
            chair(k, math.cos(r) * 0.95, 0.2 + math.sin(r) * 0.95, a + 90, ('coral', 'violet', 'sun', 'mint')[i])
        k.bx(-0.7, 0.7, G - 0.12, G - 0.06, 1.0, 1.85, 'black')
        k.qy(-0.66, 0.66, 1.04, 1.81, G - 0.123, -1, 'screenD')
        k.qy(-0.5, 0.2, 1.5, 1.7, G - 0.126, -1, 'sky')
        k.qy(-0.5, 0.5, 1.15, 1.4, G - 0.126, -1, 'violet')
        k.col(-0.62, 0.62, -0.42, 0.82, 0, 0.76)
    else:
        k.bx(-1.5, 1.5, G - 0.1, G - 0.06, 0.8, 2.1, 'steel', ink=False)
        k.qy(-1.47, 1.47, 0.83, 2.07, G - 0.103, -1, 'board')
        for i, (x, z, c) in enumerate(((-1.2, 1.7, 'sun'), (-0.9, 1.7, 'pink'), (-1.2, 1.4, 'mint'), (0.4, 1.8, 'sky'), (0.7, 1.5, 'sun'))):
            k.qy(x, x + 0.18, z, z + 0.18, G - 0.109, -1, c)
        k.qy(-0.4, 0.2, 1.3, 1.32, G - 0.106, -1, 'ink')
        k.qy(-0.4, -0.38, 1.0, 1.8, G - 0.112, -1, 'ink')
        k.bx(-0.8, 0.8, -0.35, 0.35, 1.0, 1.05, 'oak')
        k.bx(-0.05, 0.05, -0.25, 0.25, 0, 1.0, 'steel', ink=False)
        for x in (-0.55, 0.0, 0.55):
            stool(k, x, -0.75, ('coral', 'oak', 'violet')[int(x * 2 + 1.1)], 0.72)
        k.col(-0.8, 0.8, -0.35, 0.35, 0, 1.05)
    return k


def booth(k):
    """2 x 2 phone booth (door in the front, -Y, closed): felt-lined box in white with an oak frame, a glass door,
    a stool and a shelf with a laptop inside, a vent and a light on top."""
    k.begin()
    G = 0.92
    k.bx(-G, G, G - 0.08, G, 0, 2.3, 'wallW')
    for s in (-1, 1):
        a, b = srt(s * G, s * (G - 0.08))
        k.bx(a, b, -G, G - 0.08, 0, 2.3, 'wallW')
    k.bx(-G, G, -G, G, 2.3, 2.42, 'oak')
    k.bx(-G + 0.08, G - 0.08, -G + 0.02, -G + 0.06, 0, 0.12, 'oak2', ink=False)
    k.bx(-G + 0.08, G - 0.08, -G + 0.02, -G + 0.06, 2.12, 2.3, 'oak2', ink=False)
    k.bx(-G + 0.08, G - 0.08, -G + 0.03, -G + 0.05, 0.12, 2.12, 'glass', ink=False)
    k.bx(0.55, 0.6, -G - 0.04, -G + 0.02, 0.9, 1.4, 'steelD', ink=False)
    glint_y(k, -0.4, -G + 0.027, 1.2, 0.7, -1)
    k.qx(-G + 0.12, G - 0.12, 0.2, 2.2, -G + 0.077, 1, 'felt')
    k.qx(-G + 0.12, G - 0.12, 0.2, 2.2, G - 0.077, -1, 'felt')
    k.qy(-G + 0.1, G - 0.1, 0.2, 2.2, G - 0.083, -1, 'violet')
    k.bx(-0.6, 0.6, 0.45, 0.83, 0.95, 0.99, 'oak')
    laptop(k, 0.0, 0.62, 180, 0.99, 'alu', 110, 'code', 0.85)
    stool(k, 0.0, -0.05, 'coral', 0.72)
    k.bx(-0.3, 0.3, -0.3, 0.3, 2.42, 2.55, 'steel')
    k.col(-G, G, -G, G, 0, 2.42)
    return k


def counter(k, kind):
    """1 m of micro-kitchen counter (back to +Y): white fronts, an oak top, a white splashback with an oak shelf;
    Plain (fruit bowl), Espresso (a twin-group machine, cups), Sink (tap, drainer), Fridge (glass-door drinks
    fridge in the run), Snack (jars of snacks on the shelf, the granola dispensers)."""
    k.begin()
    if kind == 'Fridge':
        k.bx(-0.48, 0.48, -0.32, 0.3, 0, 2.0, 'steel')
        k.bx(-0.44, 0.44, -0.34, -0.32, 0.12, 1.88, 'graphite', ink=False)
        k.qy(-0.4, 0.4, 0.16, 1.84, -0.343, -1, 'screenD')
        for z in (0.5, 0.9, 1.3, 1.7):
            for i in range(6):
                x = -0.34 + i * 0.13
                c = ('coral', 'sun', 'mint', 'sky', 'pink', 'white')[(i + int(z * 10)) % 6]
                k.qy(x, x + 0.08, z - 0.3, z - 0.06, -0.346, -1, c)
        k.bx(0.36, 0.4, -0.38, -0.34, 0.8, 1.4, 'steel', ink=False)
        glint_y(k, -0.2, -0.349, 0.8, 0.6, -1)
        k.col(-0.48, 0.48, -0.38, 0.3, 0, 2.0)
        return k
    k.bx(-0.5, 0.5, -0.27, 0.3, 0.1, 0.88, 'wallW')
    k.bx(-0.5, 0.5, -0.24, 0.3, 0, 0.1, 'graphite', ink=False)
    k.bx(-0.5, 0.5, -0.32, 0.3, 0.88, 0.92, 'oak')
    k.qy(-0.48, 0.48, 0.15, 0.85, -0.273, -1, 'cushion')
    k.qy(-0.06, 0.06, 0.78, 0.8, -0.276, -1, 'steelD')
    k.bx(-0.5, 0.5, 0.26, 0.3, 0.92, 2.2, 'wallW')
    k.bx(-0.5, 0.5, 0.0, 0.26, 1.55, 1.59, 'oak')
    if kind == 'Plain':
        k.cyl(-0.1, -0.05, 0.92, 0.15, 0.12, 0.08, 'wallW', seg=10)
        for (x, y, c) in ((-0.15, -0.05, 'red'), (-0.05, -0.08, 'sun'), (-0.1, 0.02, 'leafL')):
            k.sph(x, y, 1.04, 0.045, c, seg=(5, 3), ink=False)
        O.small_plant(k, 0.3, 0.13, 1.59)
    elif kind == 'Espresso':
        k.bx(-0.35, 0.3, -0.12, 0.22, 0.92, 1.38, 'steel')
        k.bx(-0.33, 0.28, -0.14, -0.12, 1.25, 1.36, 'black', ink=False)
        for x in (-0.18, 0.12):
            k.cyl(x, -0.16, 1.1, 0.04, 0.035, 0.08, 'black', seg=6, ink=False)
            k.cyl(x, -0.16, 0.94, 0.035, 0.03, 0.07, 'white', seg=6, ink=False)
        k.bx(-0.36, 0.31, -0.2, -0.125, 0.92, 0.94, 'graphite2', ink=False)
        k.bx(0.33, 0.47, -0.1, 0.15, 0.92, 1.25, 'graphite')
        for i in range(4):
            O.mug(k, -0.3 + i * 0.16, 0.12, 1.59, ('white', 'violet', 'white', 'coral')[i])
    elif kind == 'Sink':
        k.qz(-0.3, 0.3, -0.22, 0.15, 0.923, 1, 'steelD')
        k.bx(-0.03, 0.03, 0.15, 0.2, 0.92, 1.25, 'steel', ink=False)
        k.bx(-0.025, 0.025, 0.0, 0.195, 1.22, 1.26, 'steel', ink=False)
        k.bx(0.33, 0.47, -0.2, 0.15, 0.92, 0.95, 'steel', ink=False)
        for i in range(3):
            k.qy(0.36 + i * 0.035, 0.38 + i * 0.035, 0.95, 1.12, -0.05, -1, 'white')
    else:   # Snack
        for i, c in enumerate(('sun', 'coral', 'leafL', 'pink')):
            x = -0.36 + i * 0.24
            k.cyl(x, 0.12, 1.59, 0.08, 0.08, 0.26, 'glass', seg=8, ink=False)
            k.cyl(x, 0.12, 1.594, 0.075, 0.075, 0.16, c, seg=8, ink=False)
            k.cyl(x, 0.12, 1.85, 0.085, 0.085, 0.03, 'oak', seg=8, ink=False)
        for x in (-0.25, 0.05):
            k.bx(x - 0.1, x + 0.1, 0.0, 0.2, 0.92, 1.3, 'glass', ink=False)
            k.bx(x - 0.09, x + 0.09, 0.01, 0.19, 0.924, 1.12, 'oak2', ink=False)
        k.bx(0.2, 0.46, -0.15, 0.15, 0.92, 1.0, 'wallW')
        for (x, c) in ((0.27, 'red'), (0.35, 'sun'), (0.42, 'leafL')):
            k.sph(x, 0.0, 1.04, 0.04, c, seg=(5, 3), ink=False)
    k.col(-0.5, 0.5, -0.32, 0.3, 0, 0.92)
    return k


def coffee_bar(k):
    """4 x 2 coffee-bar island: an oak-clad counter with a white top and an overhang, stools both sides, cups and
    a laptop, a pendant pair above."""
    k.begin()
    k.bx(-1.8, 1.8, -0.35, 0.35, 0, 1.0, 'oak')
    for x in (-1.4, -0.7, 0.0, 0.7, 1.4):
        k.qy(x - 0.005, x + 0.005, 0.05, 0.95, -0.353, -1, 'oak2')
        k.qy(x - 0.005, x + 0.005, 0.05, 0.95, 0.353, 1, 'oak2')
    k.bx(-1.9, 1.9, -0.55, 0.55, 1.0, 1.05, 'wallW')
    for i, x in enumerate((-0.8, 0.8)):
        stool(k, x, -0.8, ('violet', 'coral')[i])
        stool(k, x + 0.1, 0.8, ('mint', 'sun')[i])
    laptop(k, -0.6, -0.25, 10, 1.05, 'graphite2', 110, 'code')
    for (x, y, c) in ((0.3, -0.3, 'white'), (0.55, 0.25, 'coral'), (1.4, -0.2, 'white')):
        O.mug(k, x, y, 1.05, c)
    O.small_plant(k, -1.5, 0.2, 1.05)
    k.col(-1.9, 1.9, -0.55, 0.55, 0, 1.05)
    return k


# ================================================================ engineering floor (zone 2)
def dev_desk(k, v):
    """4 x 2 pair of sit-stand desks facing each other across a low divider (two seats a side). A: one side
    raised to standing height with a laptop on a riser, the other sitting with two screens; B: four sitting seats,
    curved ultra-wide and portrait screens; C: both standing, laptops and one big screen each, a balance board."""
    k.begin()
    hs = {'A': ((0.74, 1.08), (0.74, 0.74)), 'B': ((0.74, 0.74), (0.74, 0.74)), 'C': ((1.08, 1.08), (1.08, 1.08))}[v]
    k.bx(-1.95, 1.95, -0.02, 0.02, 0, 1.25, 'wallW')
    k.bx(-1.94, 1.94, -0.035, 0.035, 0.9, 1.24, 'felt', ink=False)
    k.qy(-1.9, 1.9, 1.15, 1.2, -0.038, -1, 'violet' if v != 'B' else 'mint')
    for f, deg in ((-1, 0), (1, 180)):
        for si, sx in enumerate((-0.98, 0.98)):
            h = hs[0 if f < 0 else 1][si]
            y0, y1 = srt(f * 0.06, f * 0.8)
            k.push(sx, 0, 0)
            desk(k, -0.92, 0.92, y0, y1, h)
            k.pop()
            yf = f * 0.25
            seat = 'chair' if h < 1.0 else None
            mug = (sx + 0.7, f * 0.6)
            if v == 'A' and f < 0:
                k.bx(sx - 0.2, sx + 0.2, f * 0.32 - 0.12, f * 0.32 + 0.12, h, h + 0.12, 'steel', ink=False)
                laptop(k, sx, f * 0.36, deg, h + 0.12, 'alu', 110, 'code')
                monitor(k, sx + 0.5, f * 0.2, deg - 15, h, 1.0, 'chart', True)
                keyboard(k, sx - 0.05, f * 0.6, deg, h)
            elif v == 'B':
                monitor(k, sx - 0.15, f * 0.18, deg + 8, h, 1.7, 'code')
                k.push(sx + 0.62, f * 0.2, deg - 25, h)
                k.bx(-0.16, 0.16, 0, 0.025, 0.1, 0.62, 'black')
                k.qy(-0.15, 0.15, 0.11, 0.61, -0.003, -1, 'screenD')
                for i in range(6):
                    k.qy(-0.12, -0.12 + 0.06 + 0.03 * (i % 4), 0.55 - i * 0.07, 0.57 - i * 0.07, -0.006, -1, 'code' if i % 2 else 'sky')
                k.pop()
                keyboard(k, sx - 0.05, f * 0.55, deg, h)
            elif v == 'C':
                monitor(k, sx - 0.25, f * 0.18, deg + 10, h, 1.0, 'code', True)
                monitor(k, sx + 0.35, f * 0.18, deg - 10, h, 1.0, 'cad' if (si + f) % 2 else 'chart', True)
                laptop(k, sx + 0.05, f * 0.5, deg, h, 'alu', 108, 'code', 0.9)
            else:
                monitor(k, sx - 0.25, f * 0.18, deg + 10, h, 1.0, 'code', True)
                monitor(k, sx + 0.35, f * 0.18, deg - 10, h, 1.0, 'cad' if (si + f) % 2 else 'chart', True)
                keyboard(k, sx - 0.05, f * 0.55, deg, h)
                laptop(k, sx + 0.62, f * 0.48, deg - 25, h, 'alu', 108, 'code', 0.85)
                mug = (sx - 0.68, f * 0.6)
            O.mug(k, mug[0], mug[1], h, ('white', 'coral', 'violet', 'mint')[si + (1 if f > 0 else 0)])
            if seat:
                chair(k, sx + 0.08 * f, f * 1.05, deg + 180 + (10 if sx > 0 else -8), ('violet', 'coral', 'mint', 'sun')[(si * 2 + (f > 0)) % 4])
            elif v == 'C' and si == 0:
                k.bx(sx - 0.3, sx + 0.3, f * 0.95 - 0.15, f * 0.95 + 0.15, 0.03, 0.08, 'oak')
                k.cyl(sx, f * 0.95, 0.0, 0.08, 0.08, 0.03, 'black', seg=6, ink=False)
    for fi, f in enumerate((-1, 1)):
        y0, y1 = srt(f * 0.06, f * 0.8)
        for si, sx in enumerate((-0.98, 0.98)):
            k.col(sx - 0.94, sx + 0.94, y0, y1, 0, hs[fi][si])       # each desk up to its own top (sit or stand)
    k.col(-1.95, 1.95, -0.06, 0.06, 0, 1.25)
    return k


def scrum(k, v):
    """2 x 1 mobile whiteboard on castors, double-sided: a kanban (TODO / DOING / DONE with sticky notes) on the
    front, a burndown and an architecture sketch on the back."""
    k.begin()
    for x in (-0.95, 0.95):
        k.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0.1, 1.95, 'steel')
        k.bx(x - 0.04, x + 0.04, -0.3, 0.3, 0.06, 0.1, 'steel', ink=False)
        for y in (-0.27, 0.27):
            k.cyl(x, y, 0, 0.04, 0.04, 0.08, 'black', seg=6, ink=False)
    k.bx(-0.92, 0.92, -0.025, 0.025, 0.75, 1.9, 'board')
    k.bx(-0.92, 0.92, -0.04, 0.04, 0.7, 0.75, 'steel', ink=False)
    for f in (-1, 1):
        y = f * 0.028
        face = 'y-' if f < 0 else 'y+'
        if f < 0:
            for i, lab in enumerate(('TODO', 'DOING', 'DONE')):
                x0 = -0.88 + i * 0.6
                ib_text.draw(k, lab, x0 + 0.28, y, 1.76, 0.07, 'ink', face=face, font='cond')
                k.qy(x0 + 0.58, x0 + 0.59, 0.8, 1.85, y, f, 'ink') if i < 2 else None
                for j in range(4 - i + (1 if v == 'B' else 0)):
                    c = ('sun', 'pink', 'mint', 'sky', 'sun')[(i + j * 2 + (v == 'B')) % 5]
                    xx = x0 + 0.06 + (j % 2) * 0.24
                    zz = 1.55 - (j // 2) * 0.24 - (0.02 if j % 2 else 0)
                    k.qy(xx, xx + 0.18, zz, zz + 0.18, y - 0.003, f, c)
        else:
            pts = [(-0.7, 1.7), (-0.4, 1.55), (-0.1, 1.45), (0.2, 1.2), (0.5, 1.05), (0.75, 0.9)]
            for si, (a, b) in enumerate(zip(pts, pts[1:])):
                dx, dz = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dz)
                nx, nz = -dz / L * 0.01, dx / L * 0.01
                yy = y + 0.003 * (1 + si % 2)
                k.poly([(-(a[0] + nx), yy, a[1] + nz), (-(b[0] + nx), yy, b[1] + nz), (-(b[0] - nx), yy, b[1] - nz), (-(a[0] - nx), yy, a[1] - nz)], 'red', (0, 1, 0))
            k.qy(-0.8, 0.8, 0.84, 0.86, y, f, 'ink')
            k.qy(0.78, 0.8, 0.87, 1.8, y, f, 'ink')
            k.qy(-0.2, 0.2, 1.62, 1.8, y + 0.012, f, 'sun')
    k.col(-0.98, 0.98, -0.06, 0.06, 0.1, 1.95)
    return k


def server_room(k):
    """6 x 4 server closet (front -Y, back to the wall): a glass front with a locked door, three racks with
    blinking LEDs and cable trays inside, a cooling unit, an access reader; walls white elsewhere."""
    k.begin()
    W, D, Hr = 3.0, 2.0, 3.2
    k.bx(-W, W, D - 0.1, D, 0, Hr, 'wallW')
    for s in (-1, 1):
        a, b = srt(s * W, s * (W - 0.1))
        k.bx(a, b, -D, D - 0.1, 0, Hr, 'wallW')
    k.bx(-W, W, -D, D, Hr, Hr + 0.15, 'concrete')
    glass_run(k, 'x', -D + 0.05, -W + 0.1, 1.2, Hr, 'graphite', 'sky')
    glass_run(k, 'x', -D + 0.05, 2.25, W - 0.1, Hr, 'graphite', 'sky')
    k.bx(1.2, 2.25, -D + 0.02, -D + 0.08, 0, 2.3, 'graphite')                          # the locked door
    k.qy(1.3, 2.15, 1.1, 2.1, -D + 0.017, -1, 'screenD')
    k.bx(1.21, 2.24, -D + 0.02, -D + 0.08, 2.3, Hr, 'graphite', ink=False)
    k.bx(2.35, 2.5, -D - 0.02, -D + 0.02, 1.1, 1.35, 'black', ink=False)
    k.qy(2.38, 2.47, 1.25, 1.31, -D - 0.023, -1, 'mint')
    ib_text.draw(k, 'SRV-01', 1.725, -D + 0.017, 2.15, 0.09, 'mint', face='y-', font='cond')
    k.col(1.15, 2.3, -D, -D + 0.1, 0, Hr)
    for i, x in enumerate((-2.2, -1.2, -0.2)):
        k.bx(x - 0.4, x + 0.4, -0.6, 0.6, 0, 2.2, 'black')
        k.qy(x - 0.36, x + 0.36, 0.08, 2.12, -0.603, -1, 'graphite')
        for j in range(10):
            z = 0.2 + j * 0.19
            k.qy(x - 0.33, x + 0.33, z, z + 0.09, -0.606, -1, 'graphite2')
            for q in range(2):
                c = ('mint', 'sky', 'mint', 'amber', 'mint')[(i * 5 + j * 3 + q) % 5]
                xx = x - 0.28 + q * 0.07
                k.qy(xx, xx + 0.03, z + 0.03, z + 0.06, -0.609, -1, c)
        k.col(x - 0.4, x + 0.4, -0.6, 0.6, 0, 2.2)
    k.bx(-2.7, 0.3, -0.3, 0.3, 2.5, 2.6, 'steel', ink=False)
    for x in (-2.5, -1.5, -0.5):
        k.bx(x - 0.02, x + 0.02, -0.02, 0.02, 2.2, 2.5, 'sky', ink=False)
    k.bx(1.0, 2.7, 0.8, 1.85, 0, 1.9, 'alu')
    for z in (0.4, 0.8, 1.2, 1.6):
        k.qy(1.1, 2.6, z, z + 0.04, 0.797, -1, 'steelD')
    k.col(1.0, 2.7, 0.8, 1.85, 0, 1.9)
    k.col(-W, W, D - 0.1, D, 0, Hr)
    for s in (-1, 1):
        a, b = srt(s * W, s * (W - 0.1))
        k.col(a, b, -D, D - 0.1, 0, Hr)
    return k


def arcade(k, v):
    """1 x 1 arcade cabinet (front -Y): A violet 'NYX RACER', B coral 'BIT BLASTER'; marquee, screen, controls."""
    k.begin()
    c, c2, name = ('violet', 'mint', 'NYX RACER') if v == 'A' else ('coral', 'sun', 'BIT BLASTER')
    k.prism_y([(-0.35, 0.0), (0.38, 0.0), (0.38, 1.9), (0.0, 1.9), (-0.08, 1.6), (-0.2, 1.05), (-0.35, 0.95)], -0.34, 0.34, c)
    k.bx(-0.32, 0.32, -0.12, 0.0, 1.62, 1.85, 'black', ink=False)
    ib_text.draw(k, name, 0.0, -0.123, 1.68, 0.1, c2, face='y-', font='cond', maxw=0.56)
    k.poly([(-0.27, -0.17, 1.08), (0.27, -0.17, 1.08), (0.27, -0.065, 1.56), (-0.27, -0.065, 1.56)], 'screenD', (0, -1, 0.25))
    k.poly([(-0.2, -0.155, 1.18), (0.2, -0.155, 1.18), (0.2, -0.085, 1.47), (-0.2, -0.085, 1.47)], c2 if v == 'A' else 'sky', (0, -1, 0.25))
    k.poly([(-0.3, -0.36, 0.955), (0.3, -0.36, 0.955), (0.3, -0.2, 1.06), (-0.3, -0.2, 1.06)], 'graphite', (0, -0.55, 1))
    for (x, cc) in ((-0.15, 'red'), (0.08, 'sun'), (0.18, 'sky')):
        k.cyl(x, -0.29, 1.0, 0.03, 0.03, 0.04, cc, seg=6, ink=False)
    k.qy(-0.25, 0.25, 0.3, 0.5, -0.353, -1, 'black')
    k.col(-0.34, 0.34, -0.35, 0.38, 0, 1.9)
    return k


def ping_pong(k):
    """3 x 2 ping-pong table (2.74 x 1.525): violet top, white lines, the net, paddles and a ball."""
    k.begin()
    k.bx(-1.37, 1.37, -0.76, 0.76, 0.72, 0.76, 'violetD')
    k.qz(-1.35, 1.35, -0.015, 0.015, 0.763, 1, 'white')
    k.qz(-1.35, 1.35, -0.76, -0.74, 0.763, 1, 'white')
    k.qz(-1.35, 1.35, 0.74, 0.76, 0.763, 1, 'white')
    for x in (-1.0, 1.0):
        k.bx(x - 0.05, x + 0.05, -0.6, 0.6, 0, 0.72, 'graphite', ink=False)
    k.bx(-0.02, 0.02, -0.82, 0.82, 0.76, 0.91, 'black', ink=False)
    for (x, y, c) in ((-0.9, 0.3, 'red'), (0.8, -0.35, 'black')):
        k.cyl(x, y, 0.76, 0.08, 0.08, 0.012, c, seg=8, ink=False)
        k.bx(x + 0.07, x + 0.17, y - 0.015, y + 0.015, 0.764, 0.776, 'oak', ink=False)
    k.sph(0.3, 0.1, 0.79, 0.02, 'white', seg=(5, 3), ink=False)
    k.col(-1.37, 1.37, -0.76, 0.76, 0, 0.91)
    return k


def foosball(k):
    """2 x 1 foosball table: an oak cabinet on legs, a green pitch, eight rods with players in two colours."""
    k.begin()
    k.bx(-0.6, 0.6, -0.36, 0.36, 0.55, 0.9, 'oak')
    k.qz(-0.55, 0.55, -0.31, 0.31, 0.903, 1, 'leaf2')
    k.qz(-0.005, 0.005, -0.31, 0.31, 0.906, 1, 'white')
    for x in (-0.55, 0.55):
        for y in (-0.3, 0.3):
            k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0, 0.55, 'graphite', ink=False)
    for i in range(8):
        x = -0.5 + i * 0.143
        k.bx(x - 0.008, x + 0.008, -0.55, 0.55, 0.96, 0.976, 'steel', ink=False)
        c = 'violet' if i % 2 else 'coral'
        for j in range((1, 2, 3, 2)[(i if i < 4 else 7 - i)]):
            n = (1, 2, 3, 2)[(i if i < 4 else 7 - i)]
            y = (j - (n - 1) / 2) * 0.18
            k.bx(x - 0.02, x + 0.02, y - 0.03, y + 0.03, 0.91, 1.02, c, ink=False)
        k.bx(x - 0.02, x + 0.02, -0.66, -0.55, 0.95, 0.99, 'black', ink=False)
    k.col(-0.6, 0.6, -0.36, 0.36, 0, 1.0)
    return k


def game_lounge(k):
    """4 x 3 console corner (back to +Y): a big screen on an oak media unit with consoles and controllers, a low
    charcoal sofa facing it with coral cushions, a side table with snacks."""
    k.begin()
    k.bx(-1.6, 1.6, 1.05, 1.45, 0, 0.45, 'oak')
    for x in (-1.0, 0.0, 1.0):
        k.qy(x - 0.4, x + 0.4, 0.06, 0.39, 1.047, -1, 'oak2')
    k.bx(-0.7, -0.3, 1.1, 1.35, 0.45, 0.53, 'black')
    k.bx(0.3, 0.55, 1.15, 1.35, 0.45, 0.75, 'wallW')
    k.bx(-1.3, 1.3, 1.28, 1.36, 0.65, 2.05, 'black')
    k.qy(-1.26, 1.26, 0.69, 2.01, 1.277, -1, 'screenD')
    k.qy(-1.1, 1.1, 0.8, 1.15, 1.274, -1, 'leaf2')
    k.qy(-0.6, 0.2, 1.15, 1.6, 1.274, -1, 'sky')
    k.qy(0.5, 1.0, 1.2, 1.5, 1.271, -1, 'coral')
    ib_text.draw(k, 'PLAYER 1', -0.7, 1.271, 1.75, 0.12, 'sun', face='y-', font='cond')
    k.bx(-1.7, 1.7, -1.45, -0.7, 0, 0.4, 'sofa')
    k.bx(-1.7, 1.7, -1.48, -1.18, 0.4, 0.8, 'sofa')
    for s in (-1, 1):
        a, b = srt(s * 1.69, s * 1.45)
        k.bx(a, b, -1.17, -0.7, 0.4, 0.62, 'sofa')
    for x in (-0.8, 0.0, 0.8):
        k.bx(x - 0.38, x + 0.38, -1.15, -0.72, 0.4, 0.48, 'graphite2')
    for x in (-0.6, 0.7):
        k.bx(x - 0.2, x + 0.2, -1.17, -1.05, 0.48, 0.78, 'coral')
    for (x, y, a) in ((-0.4, -0.95, 10), (0.4, -0.9, -15)):
        k.push(x, y, a, 0.48)
        k.bx(-0.08, 0.08, -0.04, 0.04, 0, 0.03, 'black', ink=False)
        k.pop()
    k.cyl(1.0, 0.0, 0, 0.25, 0.25, 0.5, 'wallW', seg=10)
    k.cyl(1.0, 0.0, 0.5, 0.15, 0.12, 0.08, 'sun', seg=8, ink=False)
    k.col(-1.6, 1.6, 1.05, 1.45, 0, 0.75)
    k.col(-1.3, 1.3, 1.25, 1.4, 0.75, 2.05)
    k.col(-1.7, 1.7, -1.48, -0.7, 0, 0.8)
    k.col(0.75, 1.25, -0.25, 0.25, 0, 0.58)
    return k


# ================================================================ hardware lab and design studio (zone 3)
def lab_bench(k, v):
    """4 x 2 double-sided prototype bench: ESD mat tops on steel frames, an overhead shelf with a light bar and
    power strips; A: laptop prototypes opened up, a soldering station, an oscilloscope, a magnifier lamp;
    B: motherboards on fixtures, a hinge tester, battery packs, a bin of keycaps."""
    k.begin()
    for f in (-1, 1):
        y0, y1 = srt(f * 0.05, f * 0.8)
        k.bx(-1.95, 1.95, y0, y1, 0.86, 0.9, 'steel')
        k.qz(-1.9, 1.9, y0 + 0.03, y1 - 0.03, 0.903, 1, 'esd')
        for x in (-1.85, 1.85):
            k.bx(x - 0.03, x + 0.03, y0 + 0.05, y1 - 0.05, 0, 0.86, 'steelD', ink=False)
        k.bx(-1.85, 1.85, (y0 + y1) / 2 - 0.02, (y0 + y1) / 2 + 0.02, 0.15, 0.19, 'steelD', ink=False)
    k.bx(-1.9, 1.9, -0.05, 0.05, 0.9, 1.75, 'steel')
    k.bx(-1.9, 1.9, -0.25, 0.25, 1.75, 1.8, 'steel')
    k.qz(-1.85, 1.85, -0.2, 0.2, 1.747, -1, 'glow')
    for f in (-1, 1):
        k.qy(-1.8, 1.8, 1.2, 1.26, f * 0.053, f, 'graphite')
        for i in range(8):
            k.qy(-1.7 + i * 0.45, -1.62 + i * 0.45, 1.215, 1.245, f * 0.056, f, 'sun' if i % 3 else 'mint')
    for f, deg in ((-1, 0), (1, 180)):
        y = f * 0.45
        if v == 'A':
            laptop(k, -1.2, y, deg + 10, 0.9, 'alu', 120, 'screenD')
            k.push(-0.2, y, deg, 0.9)                                          # an opened chassis (lid off)
            k.bx(-0.17, 0.17, -0.12, 0.12, 0, 0.012, 'alu')
            k.qz(-0.15, 0.15, -0.1, 0.1, 0.015, 1, 'pcb')
            for (x, yy, w) in ((-0.08, 0.0, 0.04), (0.05, 0.03, 0.03), (0.1, -0.05, 0.025)):
                k.bx(x - w, x + w, yy - w, yy + w, 0.015, 0.025, 'black', ink=False)
            k.qz(-0.15, -0.02, 0.05, 0.09, 0.018, 1, 'copper')
            k.pop()
            k.bx(0.5, 0.8, y - 0.12, y + 0.12, 0.9, 1.0, 'graphite')            # soldering station
            k.qy(0.55, 0.7, 0.93, 0.97, y - f * 0.123, -f, 'red')
            k.beam((0.9, y, 0.9), (1.0, y - f * 0.1, 1.05), 0.012, 'steelD', ink=False)
            k.bx(1.15, 1.6, y - 0.05, y + 0.18, 0.9, 1.15, 'graphite2')        # oscilloscope
            k.qy(1.2, 1.42, 0.95, 1.11, y - f * 0.053 if f < 0 else y - 0.053, -1 if f < 0 else -1, 'screenD') if f < 0 else None
            k.qy(1.22, 1.4, 1.0, 1.02, y - 0.056, -1, 'code') if f < 0 else None
            k.beam((1.75, y + f * 0.2, 0.9), (1.6, y, 1.3), 0.02, 'steelD', ink=False)   # magnifier lamp
            k.cyl(1.6, y, 1.24, 0.1, 0.1, 0.05, 'wallW', seg=10)
        else:
            for x in (-1.3, -0.5):
                k.bx(x - 0.2, x + 0.2, y - 0.14, y + 0.14, 0.9, 0.95, 'graphite', ink=False)
                k.qz(x - 0.17, x + 0.17, y - 0.11, y + 0.11, 0.953, 1, 'pcb')
                k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.953, 0.97, 'black', ink=False)
            k.push(0.5, y, deg, 0.9)                                            # a bench hinge tester
            k.bx(-0.25, 0.25, -0.15, 0.15, 0, 0.06, 'steelD')
            k.bx(-0.17, 0.17, -0.12, 0.1, 0.06, 0.075, 'violet')
            k.bx(-0.17, 0.17, 0.1, 0.11, 0.075, 0.3, 'violet', ink=False)
            k.bx(0.2, 0.24, -0.1, 0.13, 0.06, 0.4, 'steel', ink=False)
            k.beam((0.22, 0.12, 0.38), (0.0, 0.11, 0.3), 0.015, 'steel', ink=False)
            k.pop()
            for i in range(3):
                k.bx(1.0 + i * 0.16, 1.12 + i * 0.16, y - 0.1, y + 0.1, 0.9, 0.93, 'graphite2', ink=False)
            k.bx(1.55, 1.8, y - 0.12, y + 0.12, 0.9, 1.0, 'wallW')
            for i in range(6):
                k.qz(1.58 + (i % 3) * 0.07, 1.63 + (i % 3) * 0.07, y - 0.08 + (i // 3) * 0.08, y - 0.04 + (i // 3) * 0.08, 1.003, 1, ('violet', 'coral', 'sun', 'mint', 'sky', 'white')[i])
        chair(k, -0.5 if v == 'A' else 0.2, f * 1.0, deg + 180 + 8, 'esd' if f < 0 else 'graphite2')
    k.col(-1.95, 1.95, -0.8, 0.8, 0, 0.9)
    k.col(-1.9, 1.9, -0.06, 0.06, 0.9, 1.8)
    return k


def printer3d(k):
    """1 x 1 enclosed 3D printer on a steel cart (front -Y): a frame with a glass door, the print head over a
    half-printed violet laptop hinge, a filament spool, a touch screen; a bin of prints below."""
    k.begin()
    k.bx(-0.4, 0.4, -0.35, 0.35, 0.68, 0.72, 'steel')
    for (x, y) in ((-0.36, -0.31), (0.36, -0.31), (-0.36, 0.31), (0.36, 0.31)):
        k.bx(x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0.06, 0.68, 'steelD', ink=False)
        k.cyl(x, y, 0, 0.03, 0.03, 0.06, 'black', seg=6, ink=False)
    k.bx(-0.36, 0.36, -0.31, 0.31, 0.2, 0.24, 'steel', ink=False)
    k.bx(-0.25, 0.25, -0.2, 0.2, 0.24, 0.45, 'violet', ink=False)
    k.bx(-0.32, 0.32, 0.22, 0.3, 0.72, 1.4, 'graphite')
    for s in (-1, 1):
        a, b = srt(s * 0.32, s * 0.28)
        k.bx(a, b, -0.3, 0.22, 0.72, 1.4, 'graphite')
    k.bx(-0.32, 0.32, -0.3, 0.3, 1.4, 1.46, 'graphite')
    k.bx(-0.28, 0.28, -0.3, -0.28, 0.76, 1.38, 'glass', ink=False)
    glint_y(k, -0.15, -0.303, 0.9, 0.35, -1)
    k.bx(-0.26, 0.26, -0.02, 0.02, 1.25, 1.28, 'steel', ink=False)
    k.bx(-0.06, 0.04, -0.06, 0.06, 1.15, 1.25, 'black', ink=False)
    k.bx(-0.2, 0.2, -0.15, 0.15, 0.76, 0.78, 'black', ink=False)
    k.bx(-0.12, 0.12, -0.05, 0.05, 0.78, 0.86, 'violet', ink=False)
    k.cyl(0.0, 0.34, 1.0, 0.13, 0.13, 0.08, 'coral', seg=10, rot=(90, 0, 0))
    k.qy(0.12, 0.27, 0.6, 0.66, -0.353, -1, 'mint')
    k.col(-0.4, 0.4, -0.35, 0.42, 0, 1.46)
    return k


def hinge_rig(k):
    """2 x 2 hinge-cycle machine: a steel frame on a table, a laptop clamped by its base, a servo arm opening and
    closing its lid, a cycle counter, a safety cage of steel tube (open front)."""
    k.begin()
    k.bx(-0.9, 0.9, -0.7, 0.7, 0.8, 0.85, 'steel')
    for (x, y) in ((-0.82, -0.62), (0.82, -0.62), (-0.82, 0.62), (0.82, 0.62)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0, 0.8, 'steelD', ink=False)
        k.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.85, 1.88, 'sun', ink=False)
    for y in (-0.62, 0.62):
        k.bx(-0.82, 0.82, y - 0.02, y + 0.02, 1.88, 1.92, 'sun', ink=False)
    for x in (-0.82, 0.82):
        k.bx(x - 0.02, x + 0.02, -0.62, 0.62, 1.9, 1.94, 'sun', ink=False)
    k.bx(-0.3, 0.3, -0.25, 0.1, 0.85, 0.9, 'graphite')
    laptop(k, 0.0, -0.05, 0, 0.9, 'alu', 95, 'screenD', 1.2)
    k.bx(0.42, 0.6, 0.05, 0.3, 0.85, 1.25, 'black')
    k.beam((0.5, 0.15, 1.22), (0.12, 0.17, 1.15), 0.03, 'steel')
    k.bx(-0.7, -0.4, 0.3, 0.55, 0.85, 1.05, 'graphite2')
    k.qy(-0.67, -0.43, 0.9, 1.0, 0.297, -1, 'screenD')
    ib_text.draw(k, '48 211', -0.55, 0.294, 0.925, 0.05, 'code', face='y-', font='display')
    k.col(-0.9, 0.9, -0.7, 0.7, 0, 0.85)
    k.col(-0.86, -0.78, -0.66, 0.66, 0.85, 1.9)
    k.col(0.78, 0.86, -0.66, 0.66, 0.85, 1.9)
    return k


def drop_tower(k):
    """2 x 2 drop-test tower: a 3.6 m twin-column frame, a release carriage with a laptop hanging in it, the foam
    landing pad in a tray, a height scale and a hazard rail."""
    k.begin()
    k.bx(-0.95, 0.95, -0.95, 0.95, 0, 0.08, 'graphite')
    k.bx(-0.7, 0.7, -0.7, 0.7, 0.08, 0.22, 'steelD', ink=False)
    k.bx(-0.65, 0.65, -0.65, 0.65, 0.22, 0.38, 'foamB')
    for x in (-0.78, 0.78):
        k.bx(x - 0.07, x + 0.07, 0.6, 0.74, 0.08, 3.6, 'sun')
    k.bx(-0.85, 0.85, 0.6, 0.74, 3.6, 3.75, 'sun')
    for i in range(10):
        z = 0.5 + i * 0.3
        k.qy(0.7, 0.72 + (0.08 if i % 2 else 0.04), z, z + 0.02, 0.597, -1, 'ink')
    k.bx(-0.72, 0.72, 0.45, 0.6, 2.6, 2.75, 'steelD')
    k.bx(-0.05, 0.05, 0.1, 0.45, 2.6, 2.7, 'steelD', ink=False)
    k.push(0, 0.0, 0, 2.2)
    k.prism_y([(-0.11, 0.0), (0.11, 0.0), (0.11, 0.33), (-0.11, 0.33)], -0.17, 0.17, 'alu')
    k.qx(-0.08, 0.08, 0.05, 0.3, 0.173, 1, 'graphite')
    k.pop()
    k.bx(-0.01, 0.01, -0.01, 0.01, 2.53, 2.6, 'steel', ink=False)
    for (x, y) in ((-0.9, -0.9), (0.9, -0.9)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.08, 1.0, 'graphite', ink=False)
    k.bx(-0.87, 0.87, -0.92, -0.88, 0.95, 1.0, 'sun', ink=False)
    k.col(-0.95, 0.95, -0.95, 0.95, 0, 0.08)
    k.col(-0.7, 0.7, -0.7, 0.7, 0.08, 0.38)
    k.col(-0.85, 0.85, 0.6, 0.74, 0.08, 3.75)
    k.col(-0.93, 0.93, -0.93, -0.87, 0.38, 1.0)
    return k


def test_chamber(k):
    """1 x 1 thermal / humidity chamber (front -Y): a white cabinet with a round window door, a control panel."""
    k.begin()
    k.bx(-0.42, 0.42, -0.38, 0.4, 0, 1.75, 'wallW')
    k.bx(-0.36, 0.3, -0.42, -0.38, 0.25, 1.55, 'steel')
    k.cyl(-0.03, -0.42, 0.95, 0.2, 0.2, 0.012, 'screenD', seg=12, rot=(90, 0, 0), ink=False)
    k.bx(0.24, 0.27, -0.46, -0.42, 0.8, 1.1, 'steelD', ink=False)
    k.bx(0.32, 0.41, -0.41, -0.38, 1.2, 1.5, 'black', ink=False)
    k.qy(0.33, 0.4, 1.38, 1.46, -0.413, -1, 'coral')
    ib_text.draw(k, '-20 C', 0.365, -0.413, 1.27, 0.035, 'sky', face='y-', font='display')
    k.bx(-0.4, 0.4, -0.36, 0.38, 1.75, 1.85, 'steelD')
    k.col(-0.42, 0.42, -0.46, 0.4, 0, 1.85)
    return k


def anechoic(k):
    """6 x 6 anechoic chamber (door -Y): a box of grey acoustic panelling on isolation feet, a heavy door with a
    porthole and a red QUIET light, a foam-wedge interior seen through the porthole, cable ports, a warning sign."""
    k.begin()
    W, Ha = 2.9, 3.4
    k.bx(-W, W, -W, W, 0.12, Ha, 'foamB')
    for x in (-W + 0.3, W - 0.3):
        for y in (-W + 0.3, W - 0.3):
            k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 0.12, 'black', ink=False)
    for i in range(1, 8):
        t = -W + i * 2 * W / 8
        k.qy(t - 0.01, t + 0.01, 0.15, Ha - 0.05, -W - 0.003, -1, 'foam')
        k.qy(t - 0.01, t + 0.01, 0.15, Ha - 0.05, W + 0.003, 1, 'foam')
        k.qx(t - 0.01, t + 0.01, 0.15, Ha - 0.05, -W - 0.003, -1, 'foam')
        k.qx(t - 0.01, t + 0.01, 0.15, Ha - 0.05, W + 0.003, 1, 'foam')
    k.bx(-W - 0.04, W + 0.04, -W - 0.04, W + 0.04, Ha, Ha + 0.1, 'steelD')
    k.bx(-0.65, 0.65, -W - 0.12, -W, 0.12, 2.5, 'steel')
    k.cyl(0, -W - 0.12, 1.55, 0.22, 0.22, 0.02, 'black', seg=12, rot=(90, 0, 0))
    k.cyl(0, -W - 0.14, 1.55, 0.17, 0.17, 0.004, 'foam', seg=12, rot=(90, 0, 0), ink=False)
    for i in range(3):
        k.poly([(-0.12 + i * 0.09, -W - 0.148, 1.43), (-0.08 + i * 0.09, -W - 0.148, 1.43), (-0.1 + i * 0.09, -W - 0.148, 1.6)], 'foamB', (0, -1, 0))
    for z in (0.6, 2.1):
        k.bx(0.4, 0.62, -W - 0.2, -W - 0.12, z, z + 0.14, 'steelD')
    k.bx(-0.3, 0.3, -W - 0.06, -W, 2.7, 2.95, 'black')
    k.qy(-0.27, 0.27, 2.73, 2.92, -W - 0.063, -1, 'red')
    ib_text.draw(k, 'QUIET', 0.0, -W - 0.066, 2.77, 0.12, 'white', face='y-', font='display')
    k.bx(-1.6, -0.9, -W - 0.03, -W, 1.3, 1.8, 'sun')
    ib_text.draw(k, 'ANECHOIC TEST', -1.25, -W - 0.033, 1.62, 0.07, 'ink', face='y-', font='cond', maxw=0.62)
    ib_text.draw(k, 'NO ENTRY DURING RUNS', -1.25, -W - 0.033, 1.42, 0.05, 'ink', face='y-', font='cond', maxw=0.62)
    for (x, z) in ((1.6, 0.5), (1.9, 0.5), (2.2, 0.5)):
        k.cyl(x, -W - 0.06, z, 0.06, 0.06, 0.06, 'graphite', seg=8, rot=(90, 0, 0), ink=False)
    k.col(-W, W, -W, W, 0, Ha + 0.1)
    k.col(-0.65, 0.65, -W - 0.12, -W, 0, 2.5)
    return k


def design_table(k, v):
    """4 x 2 design table: a white top on oak trestles, a pen display with a sketch, foam / clay concept models,
    swatch fans, sketches pinned; A also a lamp, B a CMF tray of colour chips."""
    k.begin()
    k.bx(-1.9, 1.9, -0.8, 0.8, 0.86, 0.9, 'wallW')
    for x in (-1.5, 1.5):
        k.prism_y([(-0.65, 0.0), (-0.55, 0.0), (0.0, 0.86), (0.55, 0.0), (0.65, 0.0), (0.06, 0.86), (-0.06, 0.86)], x - 0.04, x + 0.04, 'oak')
    k.push(-0.9, 0.0, 10, 0.9)
    k.prism_y([(-0.2, 0.0), (0.2, 0.0), (0.2, 0.03), (-0.2, 0.12)], -0.3, 0.3, 'black')
    k.poly([(-0.27, -0.18, 0.115), (0.27, -0.18, 0.115), (0.27, 0.18, 0.04), (-0.27, 0.18, 0.04)], 'board', (0, 0.2, 1))
    k.poly([(-0.15, -0.05, 0.1), (0.1, -0.08, 0.103), (0.15, 0.06, 0.075), (-0.12, 0.08, 0.072)], 'sky', (0, 0.2, 1))
    k.pop()
    for (x, y, d, c) in ((0.3, 0.3, 20, 'cushion'), (1.0, -0.2, -15, 'alu'), (0.4, -0.4, 40, 'cushion')):
        k.push(x, y, d, 0.9)
        k.bx(-0.17, 0.17, -0.12, 0.12, 0, 0.02, c)
        k.prism_y([(0.11, 0.02), (0.13, 0.02), (0.18, 0.22), (0.16, 0.22)], -0.16, 0.16, c)
        k.pop()
    for i, c in enumerate(('violet', 'coral', 'sun', 'mint', 'sky')):
        k.push(1.55, 0.45, -30 + i * 14, 0.9 + i * 0.004)
        k.bx(-0.02, 0.18, -0.025, 0.025, 0, 0.004, c, ink=False)
        k.pop()
    if v == 'A':
        k.cyl(-1.7, 0.6, 0.9, 0.08, 0.08, 0.02, 'black', seg=8, ink=False)
        k.beam((-1.7, 0.6, 0.92), (-1.5, 0.5, 1.4), 0.02, 'black', ink=False)
        k.beam((-1.5, 0.5, 1.4), (-1.25, 0.35, 1.25), 0.02, 'black', ink=False)
        k.cyl(-1.25, 0.35, 1.18, 0.09, 0.05, 0.1, 'coral', seg=8)
    else:
        k.bx(-1.75, -1.25, 0.2, 0.6, 0.9, 0.94, 'graphite')
        for i in range(12):
            k.qz(-1.72 + (i % 4) * 0.12, -1.64 + (i % 4) * 0.12, 0.25 + (i // 4) * 0.12, 0.33 + (i // 4) * 0.12, 0.943, 1, ('violet', 'coral', 'sun', 'mint', 'sky', 'pink', 'oak', 'alu', 'graphite2', 'cushion', 'leafL', 'terra')[i])
    for (x, y, d) in ((0.0, 0.62, 5), (-0.4, 0.55, -8)):
        k.push(x, y, d, 0.9)
        k.qz(-0.15, 0.15, -0.1, 0.1, 0.003, 1, 'paper')
        k.qz(-0.1, 0.08, -0.04, 0.0, 0.006, 1, 'graphite2')
        k.pop()
    chair(k, -0.9, -1.15, 175, 'coral' if v == 'A' else 'violet')
    k.col(-1.9, 1.9, -0.8, 0.8, 0, 0.9)
    return k


def material_board(k):
    """2 x 1 freestanding CMF (colour, material, finish) board, double-sided: swatches of anodised aluminium, fabric,
    oak, felt and paint chips pinned in a grid, labels; on oak feet."""
    k.begin()
    k.bx(-0.95, 0.95, -0.03, 0.03, 0.3, 2.1, 'wallW')
    for x in (-0.85, 0.85):
        k.bx(x - 0.04, x + 0.04, -0.25, 0.25, 0, 0.08, 'oak')
        k.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0.08, 0.3, 'oak', ink=False)
    cols = ('alu', 'violet', 'coral', 'sun', 'mint', 'sky', 'oak', 'felt', 'graphite2', 'pink', 'cushion', 'oakD')
    for f in (-1, 1):
        y = f * 0.033
        for i in range(4):
            for j in range(4):
                c = cols[(i * 4 + j + (3 if f > 0 else 0)) % len(cols)]
                x0, z0 = -0.8 + i * 0.4, 0.55 + j * 0.38
                k.qy(x0, x0 + 0.3, z0, z0 + 0.26, y, f, c)
                k.qy(x0, x0 + 0.18, z0 - 0.06, z0 - 0.03, y, f, 'graphite')
        ib_text.draw(k, 'CMF  AIR 14 / 2027', 0.0, y, 1.95, 0.07, 'graphite', face='y-' if f < 0 else 'y+', font='cond')
    k.col(-0.95, 0.95, -0.06, 0.06, 0, 2.1)
    return k


def turntable(k):
    """Landmark: 3 x 3 concept display: a white drum with a slowly lit violet ring, the next laptop prototype on a
    turntable under a hanging light ring, a slim sign; a velvet rope stanchion on two sides."""
    k.begin()
    k.cyl(0, 0, 0, 1.0, 1.0, 0.75, 'wallW', seg=18)
    k.cyl(0, 0, 0.3, 1.01, 1.01, 0.06, 'violet', seg=18, ink=False, caps=False)
    k.cyl(0, 0, 0.75, 0.85, 0.85, 0.05, 'graphite', seg=18)
    laptop(k, 0.0, 0.0, 30, 0.8, 'violet', 118, 'screen', 1.8)
    k.cyl(0, 0, 2.84, 0.82, 0.82, 0.12, 'wallW', seg=12, caps=False)
    k.cyl(0, 0, 2.86, 0.8, 0.8, 0.006, 'glow', seg=12, ink=False)
    for i in range(3):
        a = i / 3 * math.pi * 2
        k.bx(math.cos(a) * 0.8 - 0.005, math.cos(a) * 0.8 + 0.005, math.sin(a) * 0.8 - 0.005, math.sin(a) * 0.8 + 0.005, 2.93, 5.0, 'steelD', ink=False)
    for (x, y) in ((-1.35, -1.35), (1.35, -1.35), (-1.35, 1.35)):
        k.cyl(x, y, 0, 0.12, 0.12, 0.03, 'steel', seg=8, ink=False)
        k.cyl(x, y, 0.03, 0.025, 0.025, 0.9, 'steel', seg=6, ink=False)
    k.beam((-1.35, -1.35, 0.85), (1.35, -1.35, 0.85), 0.03, 'violetD', ink=False)
    k.beam((-1.35, -1.35, 0.83), (-1.35, 1.35, 0.83), 0.03, 'violetD', ink=False)
    k.bx(0.95, 1.25, 1.1, 1.14, 0, 1.2, 'graphite')
    ib_text.draw(k, 'PROJECT', 1.1, 1.097, 1.0, 0.045, 'white', face='y-', font='cond')
    ib_text.draw(k, 'HALO', 1.1, 1.097, 0.88, 0.08, 'violet', face='y-', font='display')
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 0.8)
    k.col(-1.4, 1.4, -1.4, -1.3, 0, 0.95)
    k.col(-1.4, -1.3, -1.3, 1.4, 0, 0.95)
    return k


def exploded(k):
    """Landmark: 8 x 8 roof section with a square skylight and, hung under it on cables, the exploded NOVYX Air 14
    three metres across: bottom case, battery cells, the logic board, the keyboard deck, the display panel and the
    lid with its logo, each a few tens of centimetres apart (layer 8: the piece stands on the roof plane)."""
    k.begin()
    k.bx(-4.0, 4.0, -4.0, 4.0, 0.0, 0.32, 'concrete', ink=False)
    k.qz(-4.0, 4.0, -4.0, -1.6, -0.003, -1, 'wallW')
    k.qz(-4.0, 4.0, 1.6, 4.0, -0.003, -1, 'wallW')
    k.qz(-4.0, -1.6, -1.6, 1.6, -0.003, -1, 'wallW')
    k.qz(1.6, 4.0, -1.6, 1.6, -0.003, -1, 'wallW')
    k.qz(-1.6, 1.6, -1.6, 1.6, -0.006, -1, 'sky')                                      # the skylight glass
    for s in (-1, 1):
        a, b = srt(s * 1.6, s * 1.75)
        k.bx(a, b, -1.75, 1.75, -0.3, 0.0, 'wallW')
        k.bx(-1.6, 1.6, a, b, -0.3, 0.0, 'wallW')
    W, D = 1.5, 1.0
    layers = (-4.35, -3.95, -3.6, -3.25, -2.75, -2.35)
    # bottom case
    z = layers[0]
    k.bx(-W, W, -D, D, z, z + 0.08, 'alu')
    for (x, y) in ((-1.2, -0.8), (1.2, -0.8), (-1.2, 0.8), (1.2, 0.8)):
        k.cyl(x, y, z - 0.02, 0.06, 0.06, 0.02, 'black', seg=6, ink=False)
    # battery cells
    z = layers[1]
    for i in range(6):
        x = -1.25 + i * 0.5
        k.bx(x - 0.22, x + 0.22, -0.85, -0.05, z, z + 0.08, 'graphite2')
        k.qz(x - 0.18, x + 0.18, -0.8, -0.1, z + 0.083, 1, 'sun' if i % 2 else 'coral')
    # logic board
    z = layers[2]
    k.bx(-1.1, 1.1, -0.2, 0.9, z, z + 0.04, 'pcb')
    for (x, y, w, c) in ((-0.5, 0.35, 0.2, 'black'), (0.2, 0.4, 0.14, 'graphite'), (0.6, 0.6, 0.1, 'black'), (-0.1, 0.7, 0.08, 'steel'), (0.8, 0.1, 0.12, 'graphite')):
        k.bx(x - w, x + w, y - w, y + w, z + 0.04, z + 0.07, c, ink=False)
    k.cyl(-0.9, 0.0, z + 0.04, 0.22, 0.22, 0.05, 'graphite', seg=12)
    k.qz(-0.3, 0.9, -0.12, -0.08, z + 0.043, 1, 'copper')
    # keyboard deck
    z = layers[3]
    k.bx(-W, W, -D, D, z, z + 0.05, 'alu')
    for r in range(4):
        for c in range(10):
            x = -1.3 + c * 0.265
            y = 0.75 - r * 0.25
            k.qz(x, x + 0.21, y - 0.2, y, z + 0.053, 1, 'graphite')
    k.qz(-0.4, 0.4, -0.9, -0.35, z + 0.053, 1, 'steel')
    # display panel and lid
    z = layers[4]
    k.bx(-W, W, -D, D, z, z + 0.04, 'black')
    k.qz(-1.4, 1.4, -0.9, 0.9, z - 0.003, -1, 'screen')
    k.qz(-1.2, 0.2, -0.7, -0.1, z - 0.006, -1, 'violet')
    z = layers[5]
    k.bx(-W, W, -D, D, z, z + 0.06, 'alu')
    k.poly([(-0.25, -0.15, z - 0.003), (0.25, -0.15, z - 0.003), (0.35, 0.2, z - 0.003), (-0.15, 0.2, z - 0.003)], 'violet', (0, 0, -1))
    # cables from the roof
    for (x, y) in ((-1.4, -0.9), (1.4, -0.9), (-1.4, 0.9), (1.4, 0.9)):
        k.bx(x - 0.006, x + 0.006, y - 0.006, y + 0.006, layers[0] + 0.08, -0.3, 'steelD', ink=False)
    return k


# ================================================================ executive deck and terrace (zone 3)
def exec_desk(k):
    """4 x 3 executive desk (the seat behind, +Y, looking -Y): a thick oak top on a white pedestal and a steel leg,
    a monitor and a laptop, a lamp, two guest chairs in front, a credenza with awards and a plant behind."""
    k.begin()
    k.bx(-1.1, 1.1, -0.45, 0.45, 0.7, 0.76, 'oak')
    k.bx(0.5, 1.05, -0.4, 0.4, 0, 0.7, 'wallW')
    k.bx(-1.05, -0.95, -0.4, 0.4, 0, 0.7, 'steel', ink=False)
    monitor(k, -0.2, 0.15, 180, 0.76, 1.3, 'chart')
    laptop(k, 0.5, 0.05, 195, 0.76, 'alu', 110, 'code', 0.9)
    k.cyl(-0.85, 0.25, 0.76, 0.07, 0.07, 0.02, 'black', seg=8, ink=False)
    k.beam((-0.85, 0.25, 0.78), (-0.75, 0.15, 1.15), 0.015, 'black', ink=False)
    k.cyl(-0.72, 0.12, 1.08, 0.09, 0.06, 0.09, 'sun', seg=8)
    chair(k, 0.0, 0.85, 185, 'graphite')
    for x in (-0.55, 0.55):
        k.push(x, -1.05, 10 if x < 0 else -10)
        k.bx(-0.28, 0.28, -0.26, 0.26, 0.0, 0.42, 'cushion')
        k.bx(-0.28, 0.28, 0.16, 0.28, 0.42, 0.75, 'cushion')
        k.pop()
    k.bx(-1.6, 1.6, 1.15, 1.45, 0, 0.7, 'oak2')
    for i, (x, c) in enumerate(((-1.2, 'sun'), (-0.9, 'violet'), (0.9, 'mint'))):
        k.cyl(x, 1.3, 0.7, 0.06, 0.04, 0.2 + 0.05 * i, c, seg=6)
    k.cyl(1.3, 1.3, 0.7, 0.13, 0.1, 0.25, 'terra', seg=8)
    k.sph(1.3, 1.3, 1.15, 0.24, 'leaf', seg=(6, 4))
    k.col(-1.1, 1.1, -0.45, 0.45, 0, 0.76)
    k.col(-1.6, 1.6, 1.15, 1.45, 0, 0.7)
    k.col(-0.85, 0.85, -1.33, -0.78, 0, 0.75)
    return k


def boardroom(k):
    """8 x 6 glass boardroom (doors on the -Y side): a long oak table with ten chairs, a video wall on the +X end, a
    credenza, felt ceiling panel with a light ring above (a roof at 3 m)."""
    k.begin()
    GX, GY, Hb = 3.9, 2.9, 3.0
    for (x, y) in ((-GX, -GY), (GX, -GY), (-GX, GY), (GX, GY)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, Hb, 'wallW')
    for x in (-2.2, -1.2, 1.2, 2.2):
        k.bx(x - 0.03, x + 0.03, -GY - 0.03, -GY + 0.03, 0, Hb, 'wallW')
    glass_run(k, 'x', -GY, -GX + 0.05, -2.23, Hb)
    glass_run(k, 'x', -GY, -1.17, 1.17, Hb)
    glass_run(k, 'x', -GY, 2.23, GX - 0.05, Hb)
    glass_run(k, 'x', GY, -GX + 0.05, GX - 0.05, Hb)
    glass_run(k, 'y', -GX, -GY + 0.05, GY - 0.05, Hb)
    for x in ((-2.17, -1.23), (1.23, 2.17)):
        k.bx(x[0], x[1], -GY - 0.03, -GY + 0.03, Hb - 0.3, Hb, 'wallW', ink=False)
    k.bx(GX - 0.15, GX, -GY + 0.05, GY - 0.05, 0, Hb, 'wallW')
    k.bx(GX - 0.2, GX - 0.15, -1.6, 1.6, 0.9, 2.5, 'black')
    k.qx(-1.55, 1.55, 0.95, 2.45, GX - 0.203, -1, 'screenD')
    k.qx(-1.4, 0.4, 1.9, 2.3, GX - 0.206, -1, 'violet')
    ib_text.draw(k, 'Q3 REVIEW', GX - 0.209, 0.6, 2.0, 0.12, 'white', face='x-', font='display', maxw=0.8)
    for i in range(5):
        k.qx(-1.3 + i * 0.5, -1.0 + i * 0.5, 1.1, 1.2 + 0.12 * ((i * 3) % 5), GX - 0.206, -1, ('mint', 'sun', 'coral', 'sky', 'mint')[i])
    k.col(GX - 0.2, GX, -GY, GY, 0, Hb)
    k.bx(-GX - 0.1, GX + 0.1, -GY - 0.1, GY + 0.1, Hb, Hb + 0.15, 'oak')
    k.qz(-GX + 0.05, GX - 0.05, -GY + 0.05, GY - 0.05, Hb - 0.003, -1, 'felt')
    k.bx(-2.6, 2.6, -0.65, 0.65, 0.72, 0.78, 'oak')
    for x in (-1.9, 1.9):
        k.bx(x - 0.3, x + 0.3, -0.2, 0.2, 0, 0.72, 'wallW')
    for i in range(3):
        x = -1.6 + i * 1.6
        chair(k, x, -1.05, 180 + (5 if i % 2 else -4), 'cushion')
        chair(k, x + 0.05, 1.05, (6 if i % 2 else -5), 'cushion')
    chair(k, -3.0, 0.0, -90, 'violet')
    for (x, y) in ((-1.0, -0.3), (0.8, 0.25)):
        laptop(k, x, y, 180 if y < 0 else 0, 0.78, 'alu', 110, 'code', 0.85)
    k.bx(-3.75, -3.35, -1.2, 1.2, 0, 0.7, 'oakD')
    k.col(-2.6, 2.6, -0.65, 0.65, 0, 0.78)
    k.col(-3.75, -3.35, -1.2, 1.2, 0, 0.7)
    return k


def terrace_sofas(k):
    """4 x 3 outdoor lounge: a teak-frame sofa and two armchairs in cream cushions round a low concrete table with
    a lantern; a parasol in mint."""
    k.begin()
    k.bx(-1.6, 1.6, 0.7, 1.45, 0, 0.38, 'deck')
    k.bx(-1.6, 1.6, 1.2, 1.45, 0.38, 0.78, 'deck')
    k.bx(-1.55, 1.55, 0.72, 1.18, 0.38, 0.5, 'cushion')
    for x in (-1.0, 0.0, 1.0):
        k.bx(x - 0.45, x + 0.45, 1.05, 1.2, 0.5, 0.78, 'cushion')
    for (x, y, d) in ((-1.4, -0.6, 70), (1.4, -0.6, -70)):
        k.push(x, y, d)
        k.bx(-0.4, 0.4, -0.38, 0.38, 0, 0.38, 'deck')
        k.bx(-0.38, 0.38, -0.36, 0.27, 0.38, 0.5, 'cushion')
        k.bx(-0.4, 0.4, 0.28, 0.4, 0.38, 0.78, 'deck')
        k.pop()
    k.bx(-0.6, 0.6, -0.65, 0.15, 0, 0.35, 'concrete')
    k.cyl(0.3, -0.25, 0.35, 0.09, 0.09, 0.28, 'graphite', seg=6)
    k.cyl(0.3, -0.25, 0.4, 0.06, 0.06, 0.15, 'fire', seg=6, ink=False)
    k.bx(-0.3, -0.05, -0.35, -0.15, 0.35, 0.38, 'paper', ink=False)
    k.cyl(-1.75, -1.25, 0, 0.18, 0.18, 0.08, 'concrete', seg=8)
    k.cyl(-1.75, -1.25, 0.08, 0.025, 0.025, 2.3, 'oakD', seg=6, ink=False)
    k.cyl(-1.75, -1.25, 2.1, 1.2, 0.05, 0.45, 'mint', seg=8)
    k.col(-1.6, 1.6, 0.7, 1.45, 0, 0.78)
    k.col(-0.6, 0.6, -0.65, 0.15, 0, 0.35)
    for x in (-1.4, 1.4):
        k.col(x - 0.38, x + 0.38, -0.98, -0.22, 0, 0.6)
    k.col(-1.83, -1.67, -1.33, -1.17, 0, 2.1)
    return k


def fire_table(k):
    """2 x 2 gas fire table: concrete with a glass wind guard round the flames, four low stools of oak."""
    k.begin()
    k.bx(-0.55, 0.55, -0.55, 0.55, 0, 0.45, 'concrete')
    k.qz(-0.35, 0.35, -0.35, 0.35, 0.453, 1, 'black')
    for (x, y) in ((-0.15, -0.1), (0.12, 0.05), (0.0, 0.18), (-0.05, -0.2)):
        k.poly([(x - 0.08, y, 0.456), (x + 0.08, y, 0.456), (x, y, 0.75)], 'fire', (0, -1, 0))
        k.poly([(x - 0.04, y - 0.004, 0.456), (x + 0.04, y - 0.004, 0.456), (x, y - 0.004, 0.62)], 'sun', (0, -1, 0))
    for s in (-1, 1):
        k.bx(-0.38, 0.38, s * 0.38 - 0.006, s * 0.38 + 0.006, 0.45, 0.62, 'glass', ink=False)
        k.bx(s * 0.38 - 0.006, s * 0.38 + 0.006, -0.37, 0.37, 0.45, 0.62, 'glass', ink=False)
    for (x, y) in ((-0.82, 0.0), (0.82, 0.0), (0.0, -0.82), (0.0, 0.82)):
        k.bx(x - 0.16, x + 0.16, y - 0.16, y + 0.16, 0, 0.42, 'deck')
    k.col(-0.55, 0.55, -0.55, 0.55, 0, 0.62)
    return k


def pergola(k):
    """6 x 4 steel pergola with oak louvres, festoon lights, a long dining table with benches and climbing jasmine."""
    k.begin()
    for x in (-2.8, 2.8):
        for y in (-1.8, 1.8):
            k.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0, 2.9, 'graphite')
            k.col(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, 2.9)
    for y in (-1.8, 1.8):
        k.bx(-3.0, 3.0, y - 0.07, y + 0.07, 2.9, 3.1, 'graphite')
    for x in (-2.8, 2.8):
        k.bx(x - 0.07, x + 0.07, -1.9, 1.9, 2.92, 3.08, 'graphite')
    for i in range(10):
        x = -2.5 + i * 0.555
        k.bx(x - 0.05, x + 0.05, -1.75, 1.75, 3.0, 3.18, 'oak')
    for y in (-1.0, 0.0, 1.0):
        for i in range(6):
            x = -2.4 + i * 0.96
            zz = 2.7 + 0.08 * math.cos(i * 0.9)
            k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, zz - 0.05, zz + 0.05, 'glow', ink=False)
        k.bx(-2.7, 2.7, y - 0.005, y + 0.005, 2.78, 2.79, 'black', ink=False)
    for (x, y, z, r) in ((-2.75, -1.75, 2.5, 0.38), (2.6, 1.7, 3.15, 0.4), (-1.6, 1.75, 3.2, 0.34)):
        k.sph(x, y, z, r, 'leaf' if r > 0.32 else 'leaf2', seg=(6, 4))
        k.sph(x + 0.15, y - 0.15, z + 0.1, 0.05, 'white', seg=(4, 3), ink=False)
    k.bx(-1.8, 1.8, -0.45, 0.45, 0.72, 0.78, 'oak')
    for x in (-1.5, 1.5):
        k.bx(x - 0.04, x + 0.04, -0.35, 0.35, 0, 0.72, 'graphite', ink=False)
    for y in (-0.85, 0.85):
        k.bx(-1.7, 1.7, y - 0.17, y + 0.17, 0.4, 0.45, 'oak')
        for x in (-1.4, 1.4):
            k.bx(x - 0.03, x + 0.03, y - 0.12, y + 0.12, 0, 0.4, 'graphite', ink=False)
    for (x, c) in ((-1.0, 'white'), (0.2, 'coral'), (1.1, 'white')):
        k.cyl(x, 0.1, 0.78, 0.12, 0.12, 0.012, c, seg=10, ink=False)
    k.cyl(0.6, -0.1, 0.78, 0.05, 0.04, 0.22, 'glass', seg=6, ink=False)
    k.col(-1.8, 1.8, -0.45, 0.45, 0, 0.78)
    for y in (-0.85, 0.85):
        k.col(-1.7, 1.7, y - 0.17, y + 0.17, 0, 0.45)
    return k


def grass_planter(k, v):
    """1 m of a long corten-steel planter with ornamental grasses (A) or lavender and a little olive (B)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.4, 0.4, 0, 0.7, 'terra')
    k.qz(-0.46, 0.46, -0.36, 0.36, 0.703, 1, 'soil')
    if v == 'A':
        for i in range(9):
            x = -0.36 + (i % 3) * 0.36
            y = -0.22 + (i // 3) * 0.22
            for j in range(3):
                a = j * 2.1 + i
                k.beam((x, y, 0.7), (x + math.cos(a) * 0.15, y + math.sin(a) * 0.15, 1.3 + 0.12 * ((i + j) % 3)), 0.035, 'leafL' if (i + j) % 2 else 'sun', ink=False)
    else:
        for i in range(3):
            x = -0.3 + i * 0.3
            y = 0.1 * (1 if i % 2 else -1)
            k.sph(x, y, 0.88, 0.24, 'leaf2', seg=(6, 4), scale=(1, 1, 0.8))
            k.sph(x, y, 1.08, 0.13, 'violet', seg=(5, 3), ink=False)
    k.col(-0.5, 0.5, -0.4, 0.4, 0, 0.7)
    return k


def lamp_post(k):
    """A slim black terrace lamp (3.2 m) with a lantern head and a festoon hook."""
    k.begin()
    k.bx(-0.15, 0.15, -0.15, 0.15, 0, 0.12, 'graphite')
    k.cyl(0, 0, 0.12, 0.04, 0.035, 3.0, 'black', seg=6, ink=False)
    k.bx(-0.13, 0.13, -0.13, 0.13, 3.0, 3.3, 'glow')
    k.bx(-0.16, 0.16, -0.16, 0.16, 3.3, 3.36, 'black')
    k.bx(-0.03, 0.03, -0.03, 0.4, 2.9, 2.94, 'black', ink=False)
    k.col(-0.15, 0.15, -0.15, 0.15, 0, 3.3)
    return k


# ================================================================ build
def build(k, ao):
    reception(k).finish('Landmark_Reception', ao=ao)
    logo_wall(k).finish('Landmark_LogoWall', ao=ao)
    stage(k).finish('Stage', ao=ao)
    for v in ('A', 'B'):
        display_table(k, v).finish('DisplayTable_' + v, ao=ao)
    for v in ('A', 'B', 'C'):
        plinth(k, v).finish('Plinth_' + v, ao=ao)
    shelf_acc(k).finish('Shelf_Acc', ao=ao)
    lockers(k).finish('Lockers', ao=ao)
    lounge(k, 'A').finish('Lounge', ao=ao)            # the theme repaints its violet fabric (symbol option paint)
    beanbag(k, 'violet').finish('BeanBag', ao=ao)
    for v in ('A', 'B'):
        planter(k, v).finish('Planter_' + v, ao=ao)
    planter_tree(k).finish('Planter_Tree', ao=ao)
    for v in ('A', 'B'):
        plant(k, v).finish('Plant_' + v, ao=ao)
    for v in ('A', 'B'):
        pod(k, v).finish('Pod_' + v, ao=ao)
    booth(k).finish('Booth', ao=ao)
    for kind in ('Plain', 'Espresso', 'Sink', 'Fridge', 'Snack'):
        counter(k, kind).finish('Counter_' + kind, ao=ao)
    coffee_bar(k).finish('CoffeeBar', ao=ao)
    for v in ('A', 'B', 'C'):
        dev_desk(k, v).finish('DevDesk_' + v, ao=ao)
    scrum(k, 'A').finish('Scrum', ao=ao)
    server_room(k).finish('ServerRoom', ao=ao)
    for v in ('A', 'B'):
        arcade(k, v).finish('Arcade_' + v, ao=ao)
    ping_pong(k).finish('PingPong', ao=ao)
    foosball(k).finish('Foosball', ao=ao)
    game_lounge(k).finish('GameLounge', ao=ao)
    for v in ('A', 'B'):
        lab_bench(k, v).finish('LabBench_' + v, ao=ao)
    printer3d(k).finish('Printer3D', ao=ao)
    hinge_rig(k).finish('HingeRig', ao=ao)
    drop_tower(k).finish('DropTower', ao=ao)
    test_chamber(k).finish('TestChamber', ao=ao)
    anechoic(k).finish('Anechoic', ao=ao)
    for v in ('A', 'B'):
        design_table(k, v).finish('DesignTable_' + v, ao=ao)
    material_board(k).finish('MaterialBoard', ao=ao)
    turntable(k).finish('Landmark_Turntable', ao=ao)
    exploded(k).finish('Landmark_Exploded')
    exec_desk(k).finish('ExecDesk', ao=ao)
    boardroom(k).finish('Boardroom', ao=ao)
    terrace_sofas(k).finish('Terrace_Sofas', ao=ao)
    fire_table(k).finish('FireTable', ao=ao)
    pergola(k).finish('Pergola', ao=ao)
    for v in ('A', 'B'):
        grass_planter(k, v).finish('GrassPlanter_' + v, ao=ao)
    lamp_post(k).finish('LampPost', ao=ao)
