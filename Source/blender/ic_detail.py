"""kit-icecream finish and fittings (tactical look, modelled-detail pass): local helpers on the PM model.
All parts are hull='none' (no outline shell), stand >= 3 mm proud of what they sit on and start 3 mm inside it;
horizontal runs stop 5 mm short of the piece's sides. Palette names are the kit's own."""
import math

EM = 0.003
INSET = 0.005


def _cull(z0, z1, c='k'):
    return c + ('b' if z0 < 1.0 else '') + ('t' if z1 > 5.0 else '')


def fbar(m, x0, x1, z0, z1, yf, d, c, inset=True):
    """a horizontal run on a -Y face at y = yf, d proud"""
    a, b = (x0 + INSET, x1 - INSET) if inset else (x0, x1)
    m.bx(a, b, yf - d, yf + EM, z0, z1, c, hull='none', cull=_cull(z0, z1))


def fpad(m, x0, x1, z0, z1, yf, d, c):
    """a small plate / block on a -Y face (no inset)"""
    m.bx(x0, x1, yf - d, yf + EM, z0, z1, c, hull='none', cull=_cull(z0, z1))


def screw(m, x, z, yf, c='chrome', s=0.016, d=0.006):
    m.bx(x - s / 2, x + s / 2, yf - d, yf + EM, z - s / 2, z + s / 2, c, hull='none', cull='k')


def screws(m, pts, yf, c='chrome', s=0.016, d=0.006):
    for (x, z) in pts:
        screw(m, x, z, yf, c, s, d)


def rect_screws(m, x0, x1, z0, z1, yf, c='chrome', s=0.016, d=0.006):
    screws(m, [(x0, z0), (x1, z0), (x0, z1), (x1, z1)], yf, c, s, d)


def collar(m, x, y, z, r, h, c, seg=8):
    """a collar round a vertical post"""
    m.cy((x, y, z), r, r, h, c, seg=seg, hull='none')


def gauge(m, x, y, z, r=0.055):
    """a round dial on a -Y face at y: bezel, white face, a needle"""
    m.cy((x, y + EM, z), r, r, 0.012, 'steelD', seg=10, rot=(90, 0, 0), hull='none')
    m.cy((x, y - 0.009 + EM, z), r * 0.76, r * 0.76, 0.006, 'white', seg=10, rot=(90, 0, 0), hull='none')
    m.bx(x - 0.003, x + 0.003, y - 0.0185, y - 0.0125, z - 0.002, z + r * 0.6, 'cherry', hull='none', cull='k')


def hinge_pair(m, x, yf, zs, c='steelD', w=0.085, h=0.13, d=0.012):
    """hinge straps across a door edge at x with a chrome knuckle, on a -Y face"""
    for z in zs:
        m.bx(x - w / 2, x + w / 2, yf - d, yf + EM, z - h / 2, z + h / 2, c, hull='none', cull='k')
        m.bx(x - 0.011, x + 0.011, yf - d - 0.006, yf - d + 0.002, z - h / 2 - 0.01, z + h / 2 + 0.01, 'chrome', hull='none', cull='k')


# ---------------------------------------------------------------- walls
def parlour_finish(m, x0=-0.5, x1=0.5, z0=0.0):
    """skirting board with a bead, tile border lines on the wainscot, chair rail, crown moulding (face y = -0.5)"""
    if z0 < 0.12:
        fbar(m, x0, x1, 0.004, 0.115, -0.5, 0.016, 'chocD')
        fbar(m, x0, x1, 0.115, 0.135, -0.5, 0.022, 'wafL')
    if z0 < 1.0:
        lo = max(z0, 0.17)
        fbar(m, x0, x1, lo, lo + 0.014, -0.5, 0.009, 'wallC')
        fbar(m, x0, x1, 0.98, 0.995, -0.5, 0.009, 'wallC')
    if z0 < 1.1:
        fbar(m, x0, x1, 1.205, 1.24, -0.5, 0.034, 'wafL')
        fbar(m, x0, x1, 1.085, 1.1, -0.5, 0.02, 'wafD')
    fbar(m, x0, x1, 6.8, 6.86, -0.5, 0.04, 'wafL')
    fbar(m, x0, x1, 6.93, 6.995, -0.5, 0.03, 'waf')


def kitchen_finish(m, x0=-0.5, x1=0.5, z0=0.0):
    """cove skirting in quarry tile with a steel cap, rails above and below the mint band, high rail"""
    if z0 < 0.15:
        fbar(m, x0, x1, 0.004, 0.14, -0.5, 0.016, 'quarry')
        fbar(m, x0, x1, 0.14, 0.158, -0.5, 0.022, 'steel')
    if z0 < 1.42:
        fbar(m, x0, x1, 1.41, 1.425, -0.5, 0.009, 'steel')
        fbar(m, x0, x1, 1.575, 1.59, -0.5, 0.009, 'steel')
    fbar(m, x0, x1, 2.38, 2.5, -0.5, 0.03, 'steel')
    fbar(m, x0, x1, 6.38, 6.395, -0.5, 0.012, 'white')


def socket_plate(m, x, z, c='white', hole='black'):
    """a double socket plate on a -Y wall face"""
    fpad(m, x - 0.04, x + 0.04, z - 0.045, z + 0.045, -0.5, 0.012, c)
    for dx in (-0.017, 0.017):
        fpad(m, x + dx - 0.008, x + dx + 0.008, z - 0.012, z + 0.012, -0.512, 0.004, hole)
    screws(m, [(x, z - 0.034), (x, z + 0.034)], -0.512, 'steel', 0.008, 0.004)


def light_switch(m, x, z, c='white'):
    fpad(m, x - 0.03, x + 0.03, z - 0.045, z + 0.045, -0.5, 0.01, c)
    fpad(m, x - 0.01, x + 0.01, z - 0.02, z + 0.02, -0.51, 0.005, 'steel')


def menu_frame_detail(m, z0, z1):
    """a bead round the board, corner screws, a chalk tray under it (board front y = -0.56)"""
    yf = -0.56
    b = 0.012
    m.bx(-0.475, 0.475, yf - b, yf + EM, z1 - 0.034, z1 - 0.004, 'waf', hull='none', cull='k')
    m.bx(-0.475, 0.475, yf - b, yf + EM, z0 + 0.004, z0 + 0.034, 'waf', hull='none', cull='k')
    m.bx(-0.475, -0.445, yf - b, yf + EM, z0 + 0.034, z1 - 0.034, 'waf', hull='none', cull='k')
    m.bx(0.445, 0.475, yf - b, yf + EM, z0 + 0.034, z1 - 0.034, 'waf', hull='none', cull='k')
    rect_screws(m, -0.46, 0.46, z0 + 0.019, z1 - 0.019, yf - b, 'chrome', 0.014, 0.006)
    m.bx(-0.4, 0.4, -0.62, -0.497, z0 - 0.045, z0 + 0.003, 'chrome', hull='none', cull='b')


# ---------------------------------------------------------------- counters, cabinets, seating
def counter_finish(m, x0, x1, zt, front=-1.0):
    """chrome nosing on the top's front edge and a steel kick plate in the recessed plinth"""
    fbar(m, x0, x1, zt - 0.046, zt - 0.012, front, 0.011, 'chrome')
    fbar(m, x0 + 0.05, x1 - 0.05, 0.012, 0.105, -0.9, 0.013, 'steel')
    screws(m, [(x0 + 0.1, 0.058), (x1 - 0.1, 0.058)], -0.913, 'steelD', 0.012, 0.004)


def stool_finish(m):
    """collars on the post, piping and a chrome band round the seat, rubber feet"""
    collar(m, 0, 0, 0.04, 0.075, 0.025, 'steel')
    collar(m, 0, 0, 0.62, 0.07, 0.05, 'steel')
    collar(m, 0, 0, 0.26, 0.05, 0.035, 'steel')
    m.cy((0, 0, 0.744), 0.2, 0.2, 0.016, 'wallC', seg=8, caps=False, hull='none')
    m.cy((0, 0, 0.705), 0.2, 0.2, 0.012, 'chrome', seg=8, caps=False, hull='none')
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 8
        x, y = math.cos(a) * 0.19, math.sin(a) * 0.19
        m.bx(x - 0.012, x + 0.012, y - 0.012, y + 0.012, 0.0, 0.006, 'black', hull='none')


def booth_finish(m):
    """piping round the seat and back cushions, a chrome edge band round the table, pedestal collar and flange"""
    for s in (-1, 1):
        y0, y1 = sorted((s * 1.45, s * 0.95))
        yf = y1 if s < 0 else y0   # the seat's front edge toward the table
        a, b = (yf - EM, yf + 0.007) if s < 0 else (yf - 0.007, yf + EM)
        m.bx(-0.975, 0.975, a, b, 0.455, 0.468, 'wallC', hull='none', cull='b')
        yb = s * 1.3   # the backrest's face toward the table
        a, b = (yb - EM, yb + 0.007) if s < 0 else (yb - 0.007, yb + EM)
        m.bx(-0.975, 0.975, a, b, 1.17, 1.183, 'wallC', hull='none')
        m.bx(-0.975, 0.975, a, b, 0.512, 0.525, 'wallC', hull='none')
    m.bx(-0.895, 0.895, -0.412, -0.397, 0.716, 0.742, 'chrome', hull='none', cull='b')
    m.bx(-0.895, 0.895, 0.397, 0.412, 0.716, 0.742, 'chrome', hull='none', cull='b')
    m.bx(0.897, 0.912, -0.395, 0.395, 0.716, 0.742, 'chrome', hull='none', cull='b')
    m.bx(-0.912, -0.897, -0.395, 0.395, 0.716, 0.742, 'chrome', hull='none', cull='b')
    collar(m, 0, 0, 0.036, 0.07, 0.03, 'steel')
    collar(m, 0, 0, 0.66, 0.1, 0.02, 'steel')


def bistro_finish(m, r):
    """round top: a chrome edge band and pedestal collars"""
    m.cy((0, 0, 0.72), r + 0.008, r + 0.008, 0.016, 'chrome', seg=10, caps=False, hull='none')
    collar(m, 0, 0, 0.04, 0.08, 0.025, 'steel')
    collar(m, 0, 0, 0.67, 0.09, 0.025, 'steel')


def sq_table_finish(m):
    """square top: chrome corner caps on the legs' tops"""
    for (lx, ly) in ((-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)):
        m.bx(lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0.0, 0.012, 'black', hull='none')
        collar(m, lx, ly, 0.3, 0.03, 0.02, 'steel', seg=6)


def dip_finish(m):
    """steel kick plate, staff-side door pulls, hood hinges"""
    fbar(m, -1.0, 1.0, 0.012, 0.105, -0.9, 0.013, 'steel')
    screws(m, [(-0.9, 0.058), (0.9, 0.058)], -0.913, 'steelD', 0.012, 0.004)
    for x in (-0.1, 0.1):   # staff side doors (face y = +0.553): vertical pulls
        m.bx(x - 0.011, x + 0.011, 0.55, 0.57, 0.3, 0.66, 'chrome', hull='none', cull='f')
    for x in (-0.62, 0.62):   # hood hinges at the rear top
        m.bx(x - 0.07, x + 0.07, 0.034, 0.08, 1.33, 1.4, 'steelD', hull='none')
        m.bx(x - 0.055, x + 0.055, 0.026, 0.037, 1.35, 1.38, 'chrome', hull='none')


def vdoor_finish(m):
    """vestibule doors: pull bars on the leading stiles, kick plates, a sensor strip in the header"""
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.85, s * 0.85))
        xs = x0 + 0.025 if s > 0 else x1 - 0.025
        m.bx(xs - 0.011, xs + 0.011, 0.105, 0.132, 0.95, 1.55, 'chrome', hull='none', cull='b')
        for z in (0.99, 1.51):
            m.bx(xs - 0.007, xs + 0.007, 0.12, 0.135, z - 0.012, z + 0.012, 'steelD', hull='none')
        m.bx(x0 + 0.056, x1 - 0.056, 0.148, 0.163, 0.1, 0.32, 'steel', hull='none', cull='b')
        for xx in (x0 + 0.09, x1 - 0.09):
            for z in (0.14, 0.28):
                m.bx(xx - 0.007, xx + 0.007, 0.143, 0.152, z - 0.007, z + 0.007, 'chrome', hull='none', cull='b')
    m.bx(-0.5, 0.5, -0.215, -0.197, 2.64, 2.69, 'black', hull='none', cull='b')
    m.bx(-0.06, 0.06, -0.222, -0.212, 2.655, 2.675, 'sky', hull='none', cull='b')


def window_finish(m):
    """sill drip and corbels"""
    m.bx(-0.495, 0.495, -0.636, -0.612, 0.772, 0.8, 'wafL', hull='none', cull='b')
    for x in (-0.34, 0.34):
        m.bx(x - 0.02, x + 0.02, -0.6, -0.497, 0.7, 0.803, 'wafD', hull='none', cull='b')


def exit_door_finish(m):
    """fire exit door: hinges, kick plate, door closer"""
    hinge_pair(m, -0.46, -0.56, (0.35, 1.15, 1.95), 'chrome', w=0.07, h=0.12, d=0.01)
    m.bx(-0.36, 0.36, -0.578, -0.559, 0.05, 0.3, 'steel', hull='none', cull='b')
    rect_screws(m, -0.33, 0.33, 0.08, 0.27, -0.578, 'steelD', 0.012, 0.004)
    m.bx(0.08, 0.38, -0.592, -0.56, 2.12, 2.2, 'steelD', hull='none')
    m.bx(-0.3, 0.1, -0.58, -0.568, 2.15, 2.17, 'steel', hull='none')


# ---------------------------------------------------------------- creamery
def churn_finish(m):
    """barrel door bolts, control panel screws, pressure gauges, flange and clamp bands on the hopper"""
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        m.cy((math.cos(a) * 0.3, -0.607, 1.15 + math.sin(a) * 0.3), 0.016, 0.016, 0.012, 'steelD', seg=6, rot=(90, 0, 0), hull='none')
    rect_screws(m, -0.585, -0.165, 1.465, 1.635, -0.6, 'steel', 0.014, 0.006)
    gauge(m, 0.5, -0.55, 1.5)
    gauge(m, 0.5, -0.55, 1.2, 0.045)
    m.cy((0.3, 0.2, 1.72), 0.17, 0.17, 0.025, 'steelD', seg=8, hull='none')
    m.cy((0.3, 0.2, 1.84), 0.19, 0.19, 0.022, 'steel', seg=8, caps=False, hull='none')
    for dx in (-1, 1):
        m.bx(0.3 + dx * 0.2 - 0.02, 0.3 + dx * 0.2 + 0.02, 0.18, 0.22, 1.82, 1.87, 'steelD', hull='none')
    fbar(m, -0.68, 0.68, 0.38, 0.4, -0.55, 0.012, 'steelD')
    fbar(m, -0.68, 0.68, 1.62, 1.64, -0.55, 0.012, 'steelD')


def tank_finish(m, r, z0, z1, tall):
    """outlet valve flanges and clamp, jacket band with lugs, lid details"""
    yv = -r - 0.17
    for z in (0.2, 0.27):
        m.cy((0.0, yv, z), 0.095, 0.095, 0.02, 'steel', seg=8, hull='none')
    zm = (z0 + z1) / 2
    m.cy((0, 0, zm), r + 0.02, r + 0.02, 0.05, 'steel', seg=10, caps=False, hull='none')
    a = (r + 0.02) * math.cos(math.pi / 10)
    for z in (z0 + 0.2, zm, z1 - 0.2):
        m.bx(-0.035, 0.035, -(a + 0.045), -(a - 0.01), z - 0.005, z + 0.045, 'steelD', hull='none', cull='b')
    if not tall:
        m.cy((0, 0, z1 + 0.18), r * 0.3, r * 0.3, 0.025, 'steel', seg=10, hull='none')


def blast_finish(m):
    """door hinges, embossed panel rims, kick plate, compressor vent frame"""
    for k in range(3):
        x = -1.0 + k * 1.0
        for z in (0.55, 1.2, 1.85):
            m.bx(x - 0.488, x - 0.43, -0.875, -0.857, z - 0.06, z + 0.06, 'steelD', hull='none', cull='k')
        m.bx(x - 0.43, x + 0.43, -0.87, -0.857, 0.31, 0.33, 'steel', hull='none', cull='kb')
        m.bx(x - 0.43, x + 0.43, -0.87, -0.857, 2.07, 2.09, 'steel', hull='none', cull='k')
        m.bx(x + 0.15, x + 0.17, -0.87, -0.857, 0.33, 2.07, 'steel', hull='none', cull='k')
    fbar(m, -1.4, 1.4, 0.012, 0.105, -0.75, 0.013, 'steel')
    fv = -0.6
    m.bx(-0.64, 0.68, fv - 0.012, fv + EM, 2.69, 2.71, 'chrome', hull='none', cull='k')
    m.bx(-0.64, 0.68, fv - 0.012, fv + EM, 2.35, 2.37, 'chrome', hull='none', cull='k')
    m.bx(-0.645, -0.625, fv - 0.012, fv + EM, 2.37, 2.69, 'chrome', hull='none', cull='k')
    m.bx(0.655, 0.675, fv - 0.012, fv + EM, 2.37, 2.69, 'chrome', hull='none', cull='k')


def coldroom_finish(m):
    """heavy leaf hinges, a grab bar on standoffs, door seals, sign screws"""
    for z in (0.35, 1.15, 1.95):
        m.bx(0.617, 0.636, 0.15, 0.42, z - 0.07, z + 0.07, 'steelD', hull='none')
        m.cy((0.627, 0.13, z - 0.09), 0.02, 0.02, 0.18, 'chrome', seg=6, hull='none')
    m.bx(0.438, 0.462, 1.04, 1.1, 0.9, 1.5, 'chrome', hull='none')
    for z in (0.93, 1.47):
        m.bx(0.46, 0.503, 1.05, 1.09, z - 0.02, z + 0.02, 'steelD', hull='none')
    m.bx(0.553, 0.572, -0.118, 0.118, 0.02, 2.22, 'black', hull='none', cull='b')
    m.bx(-0.572, -0.553, -0.118, 0.118, 0.02, 2.22, 'black', hull='none', cull='b')
    m.bx(-0.55, 0.55, -0.118, 0.118, 2.2, 2.27 - 0.001, 'black', hull='none', cull='b')
    rect_screws(m, -0.71, 0.71, 2.6, 2.9, -0.143, 'chrome', 0.022, 0.006)


def prep_finish(m):
    """rolled steel nosing along the front and back, adjustable feet"""
    m.bx(-1.445, 1.445, -0.918, -0.897, 0.864, 0.916, 'steel', hull='none', cull='b')
    m.bx(-1.445, 1.445, 0.897, 0.918, 0.864, 0.916, 'steel', hull='none', cull='b')
    for (x, y) in ((-1.4, -0.85), (1.4, -0.85), (-1.4, 0.85), (1.4, 0.85)):
        m.cy((x, y, 0.0), 0.06, 0.05, 0.03, 'steelD', seg=8, hull='none')


def cakefreezer_finish(m):
    """door hinges, kick plate, header band"""
    for x in (-0.935, 0.935):
        for z in (0.35, 1.0, 1.65):
            m.bx(x - 0.02, x + 0.02, -0.472, -0.457, z - 0.05, z + 0.05, 'steelD', hull='none', cull='k')
    fbar(m, -0.98, 0.98, 0.012, 0.138, -0.423, 0.013, 'steel')
    fbar(m, -0.98, 0.98, 1.9, 1.915, -0.423, 0.013, 'chrome')
