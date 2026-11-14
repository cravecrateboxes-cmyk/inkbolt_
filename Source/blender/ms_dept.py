"""kit-megastore sales floor: produce tables, freezer bunkers, electronics demo tables, apparel tables and round
rails, the pharmacy / optical counter, checkout lanes, shopping carts and a cart corral, the entrance vestibule (glass
runs, automatic doors, greeter podium) and the landmark BULKBARN CAFE food-court counter with its tables
(see ms_base.py for conventions)."""
import math
import random

from ms_base import *  # noqa: F401,F403
import ms_base as B
import ms_detail as DT


def rbox(m, loc, size, c, rot=(0, 0, 0), hull='full'):
    m.cur = hull
    f = m.box(loc, size, c, rot=rot, bevel=False)
    m.cur = 'full'
    return f


# ================================================================ produce, frozen, electronics, apparel
def build_produce(pal, ao):
    """[2, 2] produce display: a wooden stand with four tilted crates heaped with fruit (gA - gD, repainted per
    copy) and a chalkboard price sign"""
    m = new(pal)
    m.bx(-0.95, 0.95, -0.95, 0.95, 0.0, 0.5, 'woodD', cull='b')
    for (fx, fy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        for k in range(3):
            z = 0.06 + k * 0.15
            if fy:
                (fq if fy < 0 else bq)(m, -0.95, 0.95, fy * 0.953, z, z + 0.1, 'wood')
            else:
                (lq if fx < 0 else rq)(m, fx * 0.953, -0.95, 0.95, z, z + 0.1, 'wood')
    for i, (cx, cy) in enumerate(((-0.47, -0.47), (0.47, -0.47), (-0.47, 0.47), (0.47, 0.47))):
        c = GOODS[i]
        m.bx(cx - 0.44, cx + 0.44, cy - 0.44, cy + 0.44, 0.5, 0.72, 'wood', cull='b')
        uq(m, cx - 0.4, cx + 0.4, cy - 0.4, cy + 0.4, 0.7, c)
        m.sp((cx, cy, 0.72), 0.4, c, seg=(6, 3), scale=(1.0, 1.0, 0.36))
    m.bx(-0.02, 0.02, -0.02, 0.02, 0.72, 1.25, 'woodD', hull='none', cull='b')
    m.bx(-0.22, 0.22, -0.03, 0.03, 1.05, 1.32, 'black')
    text_front(m, '2.99', 0.12, -0.033, 0.0, 1.13, 'paper', font='script')
    text_back(m, 'FRESH', 0.1, 0.033, 0.0, 1.13, 'paper', font='script')
    make('Produce', m, ao, cols=[cb(-0.95, -0.95, 0.0, 0.95, 0.95, 0.9)])


def build_bunker(pal, ao):
    """[4, 2] chest-freezer island: white body, steel rim, glass lids over frozen packs, a FROZEN band"""
    rnd = random.Random(3)
    m = new(pal)
    m.bx(-1.95, 1.95, -0.95, 0.95, 0.0, 0.86, 'pWhite', cull='b')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -1.95, 1.95, s * 0.953, 0.0, 0.12, 'grey')
        (fq if s < 0 else bq)(m, -1.95, 1.95, s * 0.953, 0.58, 0.7, 'pSky')
        (text_front if s < 0 else text_back)(m, 'FROZEN', 0.1, s * 0.956, -1.2, 0.6, 'navy', font='display')
    for s in (-1, 1):
        (lq if s < 0 else rq)(m, s * 1.953, -0.95, 0.95, 0.0, 0.12, 'grey')
    m.bx(-1.95, 1.95, -0.95, -0.85, 0.86, 0.92, 'chrome', cull='b')
    m.bx(-1.95, 1.95, 0.85, 0.95, 0.86, 0.92, 'chrome', cull='b')
    m.bx(-1.95, -1.85, -0.85, 0.85, 0.86, 0.92, 'chrome', cull='b')
    m.bx(1.85, 1.95, -0.85, 0.85, 0.86, 0.92, 'chrome', cull='b')
    m.bx(-0.04, 0.04, -0.85, 0.85, 0.86, 0.92, 'chrome', cull='b')
    uq(m, -1.85, 1.85, -0.85, 0.85, 0.87, 'pSky')
    for (x0, x1) in ((-1.82, -0.07), (0.07, 1.82)):
        x = x0
        while x < x1 - 0.2:
            w = rnd.uniform(0.22, 0.42)
            for (y0, y1) in ((-0.8, -0.05), (0.05, 0.8)):
                uq(m, x, min(x1, x + w - 0.03), y0 + rnd.uniform(0, 0.1), y1 - rnd.uniform(0, 0.1), 0.874, rnd.choice(GOODS + ['pWhite', 'pBlack']))
            x += w
    for (x0, z) in ((-1.5, 0.878), (0.6, 0.878)):
        poly(m, [(x0, -0.8, z), (x0 + 0.12, -0.8, z), (x0 + 0.6, 0.8, z), (x0 + 0.48, 0.8, z)], 'glassL', (0, 0, 1))
    make('Bunker', m, ao, cols=[cb(-1.95, -0.95, 0.0, 1.95, 0.95, 0.92)])


def build_tech(pal, ao):
    """[3, 2] electronics demo table: navy cabinet, white top, three open laptops and two tablets on stands (screens
    glow), a DEMO card"""
    m = new(pal)
    g = new(pal)
    m.bx(-1.42, 1.42, -0.92, 0.92, 0.0, 0.7, 'navy', cull='b')
    m.bx(-1.5, 1.5, -1.0, 1.0, 0.7, 0.78, 'pWhite')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -1.42, 1.42, s * 0.923, 0.3, 0.38, 'scrC')
    for i, x in enumerate((-0.95, 0.0, 0.95)):
        for s in (-1, 1):
            y = s * 0.45
            m.bx(x - 0.3, x + 0.3, y - 0.2, y + 0.2, 0.78, 0.8, 'pBlack' if i != 1 else 'chrome', hull='none', cull='b')
            ys = y + s * 0.2
            a, b = sorted((ys, ys + s * 0.02))
            m.bx(x - 0.3, x + 0.3, a, b, 0.8, 1.17, 'pBlack' if i != 1 else 'chrome', cull='b')
            (fq if s > 0 else bq)(g, x - 0.27, x + 0.27, ys - s * 0.003, 0.83, 1.14, ['scrB', 'scrO', 'scrC'][i])
    for x in (-1.35, 1.35):
        m.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0.78, 1.1, 'grey', hull='none')
        m.bx(x - 0.12, x + 0.12, -0.04, 0.0, 1.0, 1.32, 'pBlack')
        fq(g, x - 0.1, x + 0.1, -0.043, 1.02, 1.3, 'scrC')
        m.bx(x - 0.12, x + 0.12, 0.0, 0.04, 1.0, 1.32, 'pBlack')
        bq(g, x - 0.1, x + 0.1, 0.043, 1.02, 1.3, 'scrB')
    make('TechTable', m, ao, cols=[cb(-1.5, -1.0, 0.0, 1.5, 1.0, 1.0)])
    make_glow('TechTable_LED', g)


def build_apparel(pal, ao):
    rnd = random.Random(8)
    # folding table [2, 2]: stacks of folded clothes in three colours a stack (repainted per copy)
    m = new(pal)
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.7, 'pWhite', cull='b')
    m.bx(-0.95, 0.95, -0.95, 0.95, 0.7, 0.76, 'woodL')
    for i, cx in enumerate((-0.6, 0.0, 0.6)):
        for j, cy in enumerate((-0.5, 0.0, 0.5)):
            hgt = rnd.uniform(0.14, 0.34)
            c = GOODS[(i + j * 2) % 4] if (i + j) % 3 else rnd.choice(['navy', 'pPink', 'pWhite'])
            m.bx(cx - 0.24, cx + 0.24, cy - 0.19, cy + 0.19, 0.76, 0.76 + hgt, c, cull='b')
            for k in range(1, int(hgt / 0.06)):
                z = 0.76 + k * 0.06
                fq(m, cx - 0.24, cx + 0.24, cy - 0.193, z - 0.006, z, 'black') if j == 0 else None
    make('ClothesTable', m, ao, cols=[cb(-0.95, -0.95, 0.0, 0.95, 0.95, 1.05)])
    # round rail [2, 2]: base, pole, ring, garments on hangers all round
    m = new(pal)
    m.cy((0, 0, 0), 0.45, 0.45, 0.05, 'chrome', seg=8)
    m.cy((0, 0, 0.05), 0.03, 0.03, 1.32, 'chrome', seg=6, hull='none')
    m.cy((0, 0, 1.36), 0.62, 0.62, 0.03, 'chrome', seg=12, caps=False)
    n = 22
    for k in range(n):
        a = (k + 0.5) * 2 * math.pi / n
        r = 0.6
        c = GOODS[(k // 2) % 4] if (k // 2) % 3 else ['navy', 'pPink', 'pWhite', 'pBlack'][(k // 2) % 4]
        L = rnd.uniform(0.62, 0.9)
        rbox(m, (math.cos(a) * r, math.sin(a) * r, 1.34 - L), (0.4, 0.05, L), c, rot=(0, 0, a))
    make('ClothesRack', m, ao, cols=[cb(-0.72, -0.72, 0.0, 0.72, 0.72, 1.4)])


# ================================================================ pharmacy / optical counter [8, 3] (back to the wall)
def build_pharmacy(pal, ao):
    rnd = random.Random(12)
    m = new(pal)
    # back shelving (pharmacy bins left, optical frame boards right), a staff door between
    m.bx(-3.95, 0.3, 0.95, 1.45, 0.0, 2.3, 'pWhite', cull='b')
    for z in (0.15, 0.7, 1.25, 1.8):
        m.bx(-3.9, 0.25, 0.85, 0.95, z, z + 0.03, 'chrome', hull='none', cull='b')
        shelf_row(m, rnd, -3.88, 0.23, 0.6, 0.95, z + 0.03, z + 0.45, ['pWhite', 'pSky', 'pWhite', 'gB', 'mint'], face=-1, nb=4, col_w=(0.15, 0.25))
    m.bx(1.6, 3.95, 0.95, 1.45, 0.0, 2.3, 'brand', cull='b')
    fq(m, 1.7, 3.85, 0.947, 0.3, 2.15, 'pWhite')
    for r in range(5):
        for k in range(7):
            x = 1.85 + k * 0.29
            z = 0.55 + r * 0.32
            c = ['black', 'navy', 'brandR', 'pBrown', 'black'][(r + k) % 5]
            fq(m, x - 0.1, x - 0.01, 0.944, z, z + 0.05, c)
            fq(m, x + 0.01, x + 0.1, 0.944, z, z + 0.05, c)
    # staff door (closed) in the gap
    fq(m, 0.3, 1.6, 1.45, 0.0, 2.3, 'wallL')
    m.bx(0.45, 1.45, 1.38, 1.45, 0.0, 2.1, 'steel', cull='bk')
    m.bx(1.25, 1.32, 1.3, 1.38, 0.95, 1.05, 'chrome')
    # header boards over the back (above the hanging counter boards)
    m.bx(-3.95, 0.3, 1.2, 1.45, 2.3, 3.7, 'brandR', cull='')
    text_front(m, 'PHARMACY', 0.52, 1.197, -1.82, 3.02, 'paper', maxw=3.9)
    m.bx(1.6, 3.95, 1.2, 1.45, 2.3, 3.7, 'brand', cull='')
    text_front(m, 'OPTICAL', 0.5, 1.197, 2.77, 3.02, 'paper', maxw=2.2)
    # front counter (two serving windows) with registers and pick-up / drop-off boards on rods
    m.bx(-3.4, 3.4, -1.45, -0.85, 0.0, 1.0, 'pWhite', cull='b')
    m.bx(-3.45, 3.45, -1.5, -0.8, 1.0, 1.06, 'woodL')
    fq(m, -3.4, 3.4, -1.453, 0.6, 0.72, 'brandR')
    fq(m, -3.4, 3.4, -1.453, 0.0, 0.1, 'grey')
    for x, word in ((-2.0, 'DROP OFF'), (0.9, 'PICK UP'), (2.8, 'EYE EXAMS')):
        m.bx(x - 0.18, x + 0.18, -1.2, -0.95, 1.06, 1.16, 'pBlack')
        m.bx(x - 0.16, x + 0.16, -1.08, -1.02, 1.16, 1.42, 'pBlack')
        fq(m, x - 0.14, x + 0.14, -1.083, 1.19, 1.4, 'scrB')
        m.bx(x - 0.01, x + 0.01, -1.16, -1.14, 2.2, H - 0.02, 'steelD', hull='none', cull='bt')
        m.bx(x - 0.55, x + 0.55, -1.2, -1.1, 1.9, 2.2, 'paper')
        text_front(m, word, 0.17, -1.203, x, 1.97, 'brandR' if x < 2 else 'brand', maxw=1.0)
    make('Pharmacy', m, ao, cols=[cb(-3.95, 0.85, 0.0, 0.3, 1.45, 2.3), cb(1.6, 0.85, 0.0, 3.95, 1.45, 2.3),
                                  cb(-3.45, -1.5, 0.0, 3.45, -0.8, 1.06), cb(0.3, 1.38, 0.0, 1.6, 1.45, 2.3)])


# ================================================================ checkout lane [3, 5] (front -Y = the exit side)
def build_checkout(pal, ao):
    """cashier strip (x -1.5..-0.95), counter with the belt (-0.95..-0.05), customer aisle (-0.05..1.1), a low impulse
    rack of candy (1.1..1.5); the register and the bagging shelf at the south end, the lane light at the north end"""
    rnd = random.Random(20)
    m = new(pal)
    g = new(pal)
    # counter body
    m.bx(-0.95, -0.05, -1.6, 2.3, 0.0, 0.86, 'pWhite', cull='b')
    for s in (-1, 1):
        x = -0.5 + s * 0.453
        (lq if s < 0 else rq)(m, x, -1.6, 2.3, 0.4, 0.5, 'brand')
        (lq if s < 0 else rq)(m, x, -1.6, 2.3, 0.0, 0.08, 'grey')
    uq(m, -0.95, -0.05, -1.6, 2.3, 0.863, 'grey')
    uq(m, -0.86, -0.14, -0.2, 2.2, 0.866, 'black')     # the belt
    for k in range(11):
        y = -0.1 + k * 0.21
        uq(m, -0.86, -0.14, y, y + 0.025, 0.869, 'grey')
    m.bx(-0.95, -0.05, -0.32, -0.26, 0.866, 0.92, 'steel', hull='none', cull='b')   # divider bar slot
    # register (pole screen, drawer, keypad) on the cashier side, the card reader on the customer side
    m.bx(-1.2, -0.96, -1.1, -0.7, 0.0, 0.95, 'grey', cull='b')
    m.bx(-1.18, -0.98, -1.05, -0.75, 0.95, 1.05, 'pBlack')
    m.bx(-1.12, -1.06, -0.93, -0.87, 1.05, 1.3, 'steelD', hull='none', cull='b')
    m.bx(-1.22, -1.0, -0.98, -0.82, 1.3, 1.48, 'pBlack')
    rq(g, -0.997, -0.96, -0.84, 1.32, 1.46, 'scrC')
    m.bx(-0.03, 0.05, -0.65, -0.57, 0.0, 1.05, 'steelD', hull='none', cull='b')
    m.bx(-0.06, 0.08, -0.7, -0.52, 1.05, 1.2, 'pBlack')
    lq(g, -0.063, -0.67, -0.55, 1.08, 1.17, 'scrB')
    # bagging shelf at the south end
    m.bx(-0.95, -0.05, -2.45, -1.6, 0.0, 0.7, 'grey', cull='b')
    uq(m, -0.92, -0.08, -2.42, -1.63, 0.703, 'steel')
    # impulse rack (candy, gum, batteries) along the customer aisle
    m.bx(1.1, 1.48, -1.6, 2.3, 0.0, 0.2, 'grey', cull='b')
    m.bx(1.38, 1.48, -1.6, 2.3, 0.2, 1.35, 'pWhite', cull='b')
    for z in (0.2, 0.75):
        m.bx(1.1, 1.38, -1.6, 2.3, z, z + 0.025, 'chrome', hull='none', cull='b' if z < 0.3 else '')
        x0 = -1.55
        y = -1.55
        while y < 2.2:
            w = rnd.uniform(0.45, 0.8)
            hgt = rnd.uniform(0.25, 0.45)
            c = rnd.choice(GOODS + ['pPink', 'pPurple', 'pOrange'])
            y1 = min(2.25, y + w - 0.02)
            if y1 - y > 0.14:
                m.bx(1.14, 1.37, y, y1, z + 0.025, z + 0.025 + hgt, c, hull='none', cull='br')
                lq(m, 1.137, y + 0.04, y1 - 0.04, z + 0.06, z + hgt - 0.04, rnd.choice(['paper', 'pWhite', 'gC']))
            y += w
    # lane light at the north end of the counter: pole and a lit box
    m.bx(-0.53, -0.47, 2.17, 2.23, 0.86, 2.3, 'steelD', hull='none', cull='b')
    m.bx(-0.68, -0.32, 2.12, 2.28, 2.3, 2.62, 'pBlack')
    for s in (-1, 1):
        yy = 2.2 + s * 0.083
        (fq if s < 0 else bq)(g, -0.65, -0.35, yy, 2.33, 2.59, 'exitG')
        (text_front if s < 0 else text_back)(g, 'OPEN', 0.14, yy + s * 0.003, -0.5, 2.39, 'paper')
    DT.checkout_detail(m)
    make('Checkout', m, ao, cols=[cb(-0.95, -2.45, 0.0, -0.05, 2.3, 0.92), cb(-1.22, -1.1, 0.0, -0.96, -0.7, 1.48),
                                  cb(1.1, -1.6, 0.0, 1.48, 2.3, 1.35)])
    make_glow('Checkout_LED', g)


# ================================================================ carts
def cart(m, x, y, yaw=0.0, n=1, gap=0.32):
    """a shopping cart (n nested carts in a row along its axis): wire basket, red handle, chassis, wheels;
    the basket runs along local X (handle at -X)"""
    c, s = math.cos(yaw), math.sin(yaw)

    def P(px, py, pz):
        return (x + px * c - py * s, y + px * s + py * c, pz)
    L = 0.85 + (n - 1) * gap
    rot = (0, 0, yaw)
    # basket: rim, two long sides, front, floor tray (thin, outline-free sides read as wire)
    def bx2(x0, x1, y0, y1, z0, z1, col, hull='full'):
        rbox(m, P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), col, rot=rot, hull=hull)
    bx2(-0.42, L - 0.42, -0.28, 0.28, 0.9625, 0.9975, 'chrome')
    for sy in (-1, 1):
        bx2(-0.41, L - 0.43, sy * 0.265 - 0.006, sy * 0.265 + 0.006, 0.54, 0.95, 'rackG', hull='none')
    bx2(L - 0.45, L - 0.438, -0.25, 0.25, 0.54, 0.95, 'rackG', hull='none')
    bx2(-0.40, L - 0.46, -0.25, 0.25, 0.515, 0.535, 'steel', hull='none')
    # chassis rails, lower tray, wheels
    for sy in (-1, 1):
        bx2(-0.40, L - 0.47, sy * 0.2 - 0.015, sy * 0.2 + 0.015, 0.125, 0.155, 'steelD', hull='none')
    for k in range(n):
        hx = -0.45 + k * gap
        rbox(m, P(hx, 0, 1.06), (0.05, 0.6, 0.05), 'brandR', rot=rot)
        for sy in (-1, 1):
            rbox(m, P(hx + 0.04, sy * 0.27, 1.0), (0.03, 0.03, 0.12), 'steelD', rot=rot, hull='none')
    for wx in (-0.36, L - 0.5):
        for sy in (-1, 1):
            rbox(m, P(wx, sy * 0.2, 0.05), (0.09, 0.04, 0.1), 'black', rot=rot)


def build_carts(pal, ao):
    m = new(pal)
    cart(m, 0.0, 0.0, 0.25)
    make('Cart', m, ao, cols=[cb(-0.45, -0.42, 0.0, 0.45, 0.42, 1.08)])
    m = new(pal)   # knocked over on its side (a battle has been through)
    m.parent = Matrix.Translation((0.0, 0.55, 0.31)) @ Matrix.Rotation(math.radians(90), 4, 'X')
    cart(m, 0.02, 0.0, 0.0)
    m.parent = Matrix.Identity(4)
    make('Cart_B', m, ao, cols=[cb(-0.47, -0.55, 0.0, 0.45, 0.55, 0.62)])
    # cart corral [4, 1]: a steel pen with five nested carts, a sign at the end
    m = new(pal)
    for sy in (-1, 1):
        y = sy * 0.42
        m.bx(-1.9, 1.9, y - 0.025, y + 0.025, 0.85, 0.9, 'hazY', hull='full', cull='')
        m.bx(-1.9, 1.9, y - 0.02, y + 0.02, 0.4, 0.44, 'steel', hull='none', cull='')
        for x in (-1.9, 0.0, 1.9):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.94, 'steelD', cull='b')
    m.bx(1.885, 1.915, -0.395, 0.395, 0.86, 0.89, 'hazY', cull='')
    m.bx(1.885, 1.915, -0.015, 0.015, 0.9, 1.6, 'steelD', hull='none', cull='b')
    m.bx(1.72, 1.98, -0.04, 0.04, 1.3, 1.65, 'brand')
    text_front(m, 'CARTS', 0.1, -0.043, 1.85, 1.43, 'paper', maxw=0.24)
    cart(m, -1.25, 0.0, 0.0, n=5)
    DT.corral_detail(m)
    make('CartCorral', m, ao, cols=[cb(-1.95, -0.45, 0.0, 1.96, 0.45, 1.1)])


# ================================================================ entrance vestibule
def build_vestibule(pal, ao):
    """glass runs (modelled along Blender Y: the run placer lines them up with their cells), the automatic doors
    [4, 1] (orient 'span'), a greeter podium"""
    H3 = 3.0

    def glass(m, y0, y1):
        m.bx(-0.05, 0.05, y0, y1, 0.0, 0.1, 'steelD', hull='noend', cull='b')
        m.bx(-0.04, 0.04, y0, y1, H3 - 0.08, H3, 'steelD', hull='noend', cull='')
        for s in (-1, 1):
            x = s * 0.02
            (lq if s < 0 else rq)(m, x, y0, y1, 1.15, 1.35, 'glassL')
            (lq if s < 0 else rq)(m, x, y0, y1, 1.42, 1.46, 'brand')
            if y1 - y0 > 0.6:
                pts = [(x, -0.25, 1.8), (x, -0.1, 1.8), (x, 0.25, 2.4), (x, 0.1, 2.4)]
                poly(m, pts, 'glassL', (s, 0, 0))
    m = new(pal); glass(m, -0.5, 0.5); make('VGlassFull', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.5, H3)])
    m = new(pal); glass(m, -0.5, -0.07); make('VGlassHalf', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.0, H3)])
    m = new(pal)
    m.bx(-0.07, 0.07, -0.07, 0.07, 0.0, H3 + 0.02, 'steelD', cull='b')
    make('VGlassPost', m, ao, cols=[cb(-0.07, -0.07, 0.0, 0.07, 0.07, H3)])
    # automatic sliding doors: 2.2 m opening, the leaves parked behind the fixed side panes, a header with the
    # motor box and sensor; WELCOME on the vestibule side (front), THANK YOU on the store side (back)
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.1, sx * 1.95))
        m.bx(a, b, -0.05, 0.05, 0.0, 0.1, 'steelD', cull='b')
        m.bx(sx * 1.1 - 0.04, sx * 1.1 + 0.04, -0.06, 0.06, 0.0, 2.4, 'steelD', cull='b')
        m.bx(sx * 1.96 - 0.04, sx * 1.96 + 0.04, -0.06, 0.06, 0.0, 2.4, 'steelD', cull='b')
        for s in (-1, 1):
            y = s * 0.03
            (fq if s < 0 else bq)(m, a + 0.06, b - 0.06, y, 1.15, 1.35, 'glassL')
            (fq if s < 0 else bq)(m, a + 0.06, b - 0.06, y, 1.42, 1.46, 'brand')
        # parked leaf (behind the pane, a frame line shows)
        m.bx(sx * 1.25 - 0.03, sx * 1.25 + 0.03, 0.06, 0.12, 0.05, 2.35, 'steel', hull='none', cull='b')
    m.bx(-2.0, 2.0, -0.18, 0.18, 2.4, H3, 'steelD', cull='')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -1.9, 1.9, s * 0.183, 2.48, 2.92, 'brand')
    text_front(m, 'WELCOME TO BULKBARN', 0.26, -0.186, 0.0, 2.57, 'paper', maxw=3.6)
    text_back(m, 'THANK YOU', 0.3, 0.186, 0.0, 2.55, 'paper', maxw=3.0)
    m.bx(-0.12, 0.12, -0.24, -0.18, 2.3, 2.4, 'pBlack')
    make('VDoor', m, ao, cols=[cb(-2.0, -0.08, 0.0, -1.06, 0.12, H3), cb(1.06, -0.08, 0.0, 2.0, 0.12, H3)])
    # greeter podium
    m = new(pal)
    m.bx(-0.3, 0.3, -0.22, 0.22, 0.0, 1.05, 'brand', cull='b')
    m.bx(-0.34, 0.34, -0.28, 0.24, 1.05, 1.12, 'woodL')
    fq(m, -0.24, 0.24, -0.223, 0.5, 0.85, 'paper')
    text_front(m, 'MEMBERS', 0.08, -0.226, 0.0, 0.62, 'brand', font='display', maxw=0.4)
    m.bx(0.1, 0.24, -0.1, 0.1, 1.12, 1.2, 'pBlack')
    make('Podium', m, ao, cols=[cb(-0.34, -0.28, 0.0, 0.34, 0.24, 1.12)])


# ================================================================ landmark: BULKBARN CAFE food court [10, 4]
def build_foodcourt(pal, ao):
    """the counter against the wall (front -Y): order counter with registers and a sneeze guard, behind it ovens,
    the hot-dog roller, a soda fountain and a churro warmer; three lit menu boards and the big CAFE sign on top"""
    rnd = random.Random(31)
    m = new(pal)
    g = new(pal)
    # back wall cladding and the kitchen line
    m.bx(-5.0, 5.0, 1.75, 2.0, 0.0, 5.2, 'cream', cull='b')
    for k in range(10):
        x = -4.5 + k
        fq(m, x - 0.45, x + 0.45, 1.747, 1.0, 2.2, 'paper' if k % 2 else 'cream')
    m.bx(-4.68, 4.68, 1.0, 1.75, 0.0, 0.92, 'steel', cull='bk')
    uq(m, -4.68, 4.68, 1.0, 1.75, 0.923, 'chrome')
    for x in (-3.6, -2.2):   # pizza ovens (stacked deck ovens)
        for z in (0.92, 1.5):
            m.bx(x - 0.6, x + 0.6, 1.1, 1.72, z, z + 0.55, 'steelD')
            fq(m, x - 0.45, x + 0.45, 1.097, z + 0.12, z + 0.4, 'black')
            fq(m, x - 0.4, x + 0.4, 1.094, z + 0.2, z + 0.32, 'scrO')
    m.bx(-0.9, 0.5, 1.15, 1.6, 0.92, 1.12, 'chrome')   # hot-dog roller
    for k in range(6):
        y = 1.2 + k * 0.07
        uq(m, -0.85, 0.45, y, y + 0.04, 1.123, 'pBrown')
    m.bx(1.1, 2.4, 1.2, 1.72, 0.92, 1.7, 'brandR')       # soda fountain
    for k in range(6):
        x = 1.25 + k * 0.2
        fq(m, x - 0.07, x + 0.07, 1.197, 1.35, 1.6, ['brandR', 'pBlack', 'pOrange', 'pLime', 'brand', 'pPurple'][k])
        m.bx(x - 0.02, x + 0.02, 1.15, 1.2, 1.2, 1.3, 'chrome', hull='none')
    m.bx(3.0, 4.4, 1.2, 1.7, 0.92, 1.55, 'glassL')       # warmer cabinet
    fq(m, 3.1, 4.3, 1.197, 1.0, 1.45, 'cardL')
    for k in range(5):
        fq(m, 3.15 + k * 0.23, 3.3 + k * 0.23, 1.194, 1.08, 1.35, 'pBrown')
    # order counter with the sneeze guard and three registers
    m.bx(-3.5, 4.6, -1.9, -1.2, 0.0, 1.0, 'brandR', cull='b')
    m.bx(-3.55, 4.65, -1.95, -1.15, 1.0, 1.07, 'pWhite')
    fq(m, -3.5, 4.6, -1.903, 0.0, 0.12, 'black')
    fq(m, -3.5, 4.6, -1.903, 0.62, 0.7, 'hazY')
    for x in (-2.4, 0.4, 3.2):
        m.bx(x - 0.2, x + 0.2, -1.5, -1.25, 1.07, 1.17, 'pBlack')
        m.bx(x - 0.18, x + 0.18, -1.4, -1.34, 1.17, 1.45, 'pBlack')
        bq(g, x - 0.15, x + 0.15, -1.337, 1.2, 1.42, 'scrC')
    for x in (-3.3, -1.0, 1.8, 4.2):
        m.bx(x - 0.02, x + 0.02, -1.62, -1.58, 1.07, 1.55, 'chrome', hull='none', cull='b')
    m.bx(-3.4, 4.3, -1.63, -1.57, 1.55, 1.58, 'chrome', hull='none')
    # menu boards (lit) and the CAFE sign
    for i, (x, items) in enumerate(((-3.2, ('HOT DOG + SODA', '1.50')), (0.0, ('PIZZA SLICE', '1.99')), (3.2, ('CHURRO', '1.00')))):
        m.bx(x - 1.45, x + 1.45, 1.5, 1.75, 2.6, 3.7, 'pBlack')
        fq(g, x - 1.38, x + 1.38, 1.497, 2.66, 3.64, 'navy')
        text_front(g, items[0], 0.28, 1.494, x, 3.25, 'paper', maxw=2.6)
        text_front(g, items[1], 0.36, 1.494, x, 2.78, 'gC')
        poly(g, [(x - 1.2 + math.cos(a / 5 * math.pi) * 0.14, 1.494, 2.95 + math.sin(a / 5 * math.pi) * 0.14) for a in range(10)], ['brandR', 'gC', 'leaf'][i], (0, -1, 0))
    m.bx(-4.2, 4.2, 1.45, 1.75, 4.0, 5.0, 'brandR')
    fq(m, -4.1, 4.1, 1.447, 4.06, 4.14, 'hazY')
    text_front(m, 'BULKBARN CAFE', 0.62, 1.444, 0.0, 4.25, 'gC', maxw=7.8)
    for sx in (-1, 1):   # side pillars with the brand stripe
        a, b = sorted((sx * 4.7, sx * 5.0))
        m.bx(a, b, -2.0, 1.75, 0.0, 5.2, 'cream', cull='b')
        (lq if sx > 0 else rq)(m, sx * 4.7 - sx * 0.003, -2.0, 1.75, 3.6, 4.0, 'brandR')
    make('Landmark_FoodCourt', m, ao, cols=[cb(-3.55, -1.95, 0.0, 4.65, -1.15, 1.07), cb(-4.68, 1.0, 0.0, 4.68, 1.75, 0.92),
                                            cb(-5.0, 1.75, 0.0, 5.0, 2.0, 5.2), cb(-4.2, 1.1, 0.92, -1.6, 1.72, 2.05), cb(-0.9, 1.15, 0.92, 0.5, 1.6, 1.12),
                                            cb(1.1, 1.2, 0.92, 2.4, 1.72, 1.7), cb(3.0, 1.2, 0.92, 4.4, 1.7, 1.55),
                                            cb(-5.0, -2.0, 0.0, -4.7, 1.75, 5.2), cb(4.7, -2.0, 0.0, 5.0, 1.75, 5.2)])
    make_glow('Landmark_FoodCourt_LED', g)
    # food-court table [2, 2]: a red top on a pedestal with two fixed benches, a napkin box and a tray
    m = new(pal)
    m.bx(-0.75, 0.75, -0.4, 0.4, 0.72, 0.77, 'brandR')
    m.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 0.72, 'steelD', hull='none', cull='b')
    m.bx(-0.5, 0.5, -0.04, 0.04, 0.0, 0.06, 'steelD', hull='none', cull='b')
    for s in (-1, 1):
        y = s * 0.75
        m.bx(-0.75, 0.75, y - 0.17, y + 0.17, 0.42, 0.47, 'gC')
        m.bx(-0.5, 0.5, y - 0.03, y + 0.03, 0.0, 0.42, 'steelD', hull='none', cull='b')
    m.bx(0.3, 0.45, -0.08, 0.08, 0.77, 0.9, 'paper')
    m.bx(-0.4, 0.0, -0.25, 0.05, 0.77, 0.79, 'brand', hull='none', cull='b')
    make('CafeTable', m, ao, cols=[cb(-0.75, -0.92, 0.0, 0.75, 0.92, 0.77)])


def build_dept(pal, ao):
    build_produce(pal, ao)
    build_bunker(pal, ao)
    build_tech(pal, ao)
    build_apparel(pal, ao)
    build_pharmacy(pal, ao)
    build_checkout(pal, ao)
    build_carts(pal, ao)
    build_vestibule(pal, ao)
    build_foodcourt(pal, ao)
