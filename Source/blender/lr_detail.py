"""kit-livingroom modelled detail (tactical look plan Stage 11): the finish and fittings a real open-plan house has,
added to the pieces the player sees most. Everything goes through the kit's K model with flat=True (no outline shell,
no bevel), stands at least 3 mm proud of its face, starts EMBED inside it and keeps horizontal runs 5 mm short of the
piece sides. Coordinates are in the current m.parent frame (the same frame the piece's own shapes use). D() takes
extents as x0, x1, y0, y1, z0, z1. Faces that look toward Blender -Y are drawn at y = yf.

Detail is finish and fittings only: skirting grooves, rails, dentils, socket and switch plates, hinges, handles,
piping, button tufts, edge banding, joints, ferrules. Nothing is grime. Never touches glow parts (fire, lamps)."""
import math

EMBED = 0.003
INS = 0.005          # runs stop 5 mm short of a piece's sides
WAINS_H = 6.0


def D(m, x0, x1, y0, y1, z0, z1, c):
    """a detail box from extents (flat: no outline shell)"""
    assert x1 > x0 and y1 > y0 and z1 > z0, (c, x0, x1, y0, y1, z0, z1)
    return m.bx(x0, y0, z0, x1, y1, z1, c, flat=True)


def Dy(m, x, z, yf, r, c, d=0.014, seg=8, sign=-1):
    """a round cap / knob plate standing out of a face looking toward -Y (sign -1) or +Y (sign +1)"""
    if sign < 0:
        m.cy(x, yf + EMBED, z, r, r, d + EMBED, c, seg=seg, rot=(90, 0, 0), flat=True)
    else:
        m.cy(x, yf - EMBED, z, r, r, d + EMBED, c, seg=seg, rot=(-90, 0, 0), flat=True)


def Dx(m, y, z, xf, r, c, d=0.014, seg=8, sign=1):
    """a round cap on a face looking toward +X (sign +1) or -X (sign -1)"""
    if sign > 0:
        m.cy(xf - EMBED, y, z, r, r, d + EMBED, c, seg=seg, rot=(0, 90, 0), flat=True)
    else:
        m.cy(xf + EMBED, y, z, r, r, d + EMBED, c, seg=seg, rot=(0, -90, 0), flat=True)


def screw(m, x, z, yf, s=0.05, c='steel2', d=0.01):
    D(m, x - s / 2, x + s / 2, yf - d, yf + EMBED, z - s / 2, z + s / 2, c)


def band(m, x0, x1, z0, z1, yf, c, d=0.014, sign=-1):
    """edge banding on a front (sign -1) or back (+1) face, run inset 5 mm from its ends"""
    if sign < 0:
        D(m, x0 + INS, x1 - INS, yf - d, yf + EMBED, z0, z1, c)
    else:
        D(m, x0 + INS, x1 - INS, yf - EMBED, yf + d, z0, z1, c)


def frame_lines(m, x0, x1, z0, z1, yf, c, t=0.05, d=0.012):
    """a thin raised rectangle outline on a -Y face: a routed door / drawer panel (butt joints, no overlaps)"""
    D(m, x0, x1, yf - d, yf + EMBED, z1 - t, z1, c)
    D(m, x0, x1, yf - d, yf + EMBED, z0, z0 + t, c)
    D(m, x0, x0 + t, yf - d, yf + EMBED, z0 + t, z1 - t, c)
    D(m, x1 - t, x1, yf - d, yf + EMBED, z0 + t, z1 - t, c)


def hinge(m, x, z0, z1, yf, w=0.1, c='steel', d=0.014):
    """a butt-hinge seen from the front: a leaf plate with a pin line down it"""
    D(m, x - w / 2, x + w / 2, yf - d, yf + EMBED, z0, z1, c)
    D(m, x - 0.006, x + 0.006, yf - d - 0.008, yf - d + EMBED, z0 + 0.02, z1 - 0.02, 'steel2')


def pull(m, x, z, yf, c='mustard', long=0.9):
    """a bar pull on two stand-offs"""
    h = long / 2
    D(m, x - h, x + h, yf - 0.1, yf - 0.06, z - 0.035, z + 0.035, c)
    for xx in (x - h + 0.08, x + h - 0.08):
        D(m, xx - 0.04, xx + 0.04, yf - 0.06, yf + EMBED, z - 0.03, z + 0.03, c)


def socket_plate(m, x, z, y):
    """a 13 A plug socket: faceplate, raised boss, three slots, two screws (y = the wall face plane)"""
    D(m, x - 0.25, x + 0.25, y - 0.03, y + EMBED, z - 0.25, z + 0.25, 'white')
    D(m, x - 0.17, x + 0.17, y - 0.042, y - 0.03 + EMBED, z - 0.15, z + 0.15, 'trim2')
    D(m, x - 0.03, x + 0.03, y - 0.049, y - 0.042 + EMBED, z + 0.05, z + 0.12, 'black')
    for sx in (-1, 1):
        D(m, x + sx * 0.085 - 0.03, x + sx * 0.085 + 0.03, y - 0.049, y - 0.042 + EMBED, z - 0.1, z - 0.02, 'black')
    for sz in (-1, 1):
        screw(m, x, z + sz * 0.212, y - 0.03, s=0.045, c='steel', d=0.008)


def switch_plate(m, x, z, y):
    """a rocker light switch: faceplate, two-step rocker, two screws"""
    D(m, x - 0.25, x + 0.25, y - 0.03, y + EMBED, z - 0.25, z + 0.25, 'white')
    D(m, x - 0.13, x + 0.13, y - 0.075, y - 0.03 + EMBED, z + 0.012, z + 0.17, 'cream')
    D(m, x - 0.13, x + 0.13, y - 0.05, y - 0.03 + EMBED, z - 0.17, z - 0.012, 'trim2')
    for sz in (-1, 1):
        screw(m, x, z + sz * 0.215, y - 0.03, s=0.04, c='steel', d=0.008)


# ------------------------------------------------------------------ wall modules
def wall_detail(m, idx, dz, y):
    """skirting groove and cap, wainscot panel beading, chair-rail beads, picture-rail lip, dentils under the crown and
    the socket / switch plates of one wall module (idx '1' lounge, '2' dining, '3' kitchen).
    dz = the E/W modules' 6 mm trim lift, y = wall face plane."""
    a, b = -0.5 + INS, 0.5 - INS
    ys = y - 0.16                                     # skirting face
    D(m, a, b, ys - 0.012, ys + EMBED, 0.5 + dz, 0.55 + dz, 'trim2')          # routed groove line
    D(m, a, b, ys - 0.012, ys + EMBED, 0.004, 0.09, 'trim2')                  # plinth foot
    D(m, a, b, y - 0.17, y + EMBED, 1.08 + dz, 1.14 + dz, 'trim')             # cap bead on the skirting
    frame_lines(m, -0.44, 0.44, 1.9 + dz, 4.55 + dz, y, 'trim', t=0.05, d=0.014)      # raised panel moulding
    frame_lines(m, -0.36, 0.36, 1.98 + dz, 4.47 + dz, y, 'trim2', t=0.03, d=0.008)
    D(m, a, b, y - 0.09, y + EMBED, WAINS_H - 0.07 + dz, WAINS_H + dz, 'trim')        # chair rail: cove under, fillet on top
    D(m, a, b, y - 0.1, y + EMBED, WAINS_H + 0.3 + dz, WAINS_H + 0.35 + dz, 'oak')
    D(m, a, b, y - 0.09, y + EMBED, 14.32 + dz, 14.38 + dz, 'oak')                    # picture-rail lip
    for i in range(5):                                                                 # dentils under the crown
        x0 = -0.5 + 0.03 + i * 0.19
        D(m, x0, x0 + 0.1, y - 0.22, y - 0.18 + EMBED, 16.95 + dz, 17.17 + dz, 'trim')
    D(m, a, b, y - 0.2, y + EMBED, 17.6 + dz, 17.68 + dz, 'trim2')                    # fillet on top of the crown
    if idx == '1':
        socket_plate(m, 0.0, 2.45, y)
    elif idx == '2':
        socket_plate(m, 0.0, 2.45, y)
        switch_plate(m, 0.0, 7.6, y)
    else:
        switch_plate(m, 0.0, 7.6, y)


def hall_detail(m, x):
    """the hallway wall slice, trail face at +X: the same fittings in the +X direction (y runs along the slice)"""
    a, b = -0.5 + INS, 0.5 - INS
    D(m, x + 0.16 - EMBED, x + 0.16 + 0.012, a, b, 0.5, 0.55, 'trim2')
    D(m, x + 0.16 - EMBED, x + 0.16 + 0.012, a, b, 0.004, 0.09, 'trim2')
    D(m, x + 0.17 - EMBED, x + 0.17 + 0.05, a, b, 1.08, 1.14, 'trim')
    D(m, x + 0.14 - EMBED, x + 0.14 + 0.012, a, b, WAINS_H - 0.07, WAINS_H, 'trim')
    D(m, x + 0.14 - EMBED, x + 0.14 + 0.05, a, b, WAINS_H + 0.3, WAINS_H + 0.35, 'oak')
    D(m, x + 0.07 - EMBED, x + 0.07 + 0.05, a, b, 14.32, 14.38, 'oak')
    for i in range(5):
        y0 = -0.5 + 0.03 + i * 0.19
        D(m, x + 0.18 - EMBED, x + 0.22, y0, y0 + 0.1, 16.95, 17.17, 'trim')
    for (y0, y1, z0, z1) in ((-0.44, -0.39, 1.95, 4.5), (0.39, 0.44, 1.95, 4.5), (-0.44, 0.44, 1.9, 1.95), (-0.44, 0.44, 4.5, 4.55)):
        D(m, x - EMBED, x + 0.014, y0, y1, z0, z1, 'trim')                              # panel moulding


def radiator_detail(m, x):
    """thermostatic valve and lockshield valve with their risers, top grille slots"""
    for (yy, head) in ((-0.34, 'cream'), (0.34, 'trim2')):
        m.cy(x + 0.1, yy, 0.0, 0.04, 0.04, 1.62, 'steel', seg=6, flat=True)                 # riser pipe
        m.cy(x + 0.1, yy, 1.1, 0.075, 0.075, 0.3, 'mustard', seg=6, flat=True)             # brass valve body
        m.cy(x + 0.1, yy, 1.4, 0.1, 0.1, 0.14, head, seg=8, flat=True)                     # valve head
    for i in range(6):
        yy = -0.375 + i * 0.15
        D(m, x + 0.03, x + 0.17, yy - 0.012, yy + 0.012, 4.4 - EMBED, 4.407, 'trim2')


# ------------------------------------------------------------------ sofa
def sofa_detail(m):
    """piping on the seat cushions and the base, button tufts on the back cushions and arm sides, seams down the back,
    brass collars and toe caps on the walnut feet"""
    for i in range(3):                                              # seat cushions: welts along the front edge
        x0 = -5.7 + i * 3.8
        D(m, x0 + 0.14, x0 + 3.66, -2.55 - 0.016, -2.55 + EMBED, 2.58, 2.64, 'sofaD')
        D(m, x0 + 0.14, x0 + 3.66, -2.55 - 0.016, -2.55 + EMBED, 1.82, 1.88, 'sofaD')
    for sx in (-1, 1):
        a, b = sorted((sx * 5.75, sx * 6.95))
        D(m, a + 0.1, b - 0.1, -2.65 - 0.014, -2.65 + EMBED, 1.8, 1.86, 'sofa2')       # arm foot welt
        # rolled arm end: a gathered cap ring and a button
        m.cy(sx * 6.35, -2.66 + EMBED, 3.4, 0.4, 0.4, 0.016, 'sofa2', seg=10, rot=(90, 0, 0), flat=True)
        m.cy(sx * 6.35, -2.673, 3.4, 0.14, 0.14, 0.03, 'sofaD', seg=6, rot=(90, 0, 0), flat=True)
        xo = sx * 6.95                                                                  # arm outer side
        for yy in (-2.0, 2.0):
            for zz in (2.0, 2.5):
                Dx(m, yy, zz, xo, 0.09, 'sofaD', d=0.03, seg=6, sign=sx)
        for yy in (-2.45, 2.45):
            if sx > 0:
                D(m, xo - EMBED, xo + 0.012, yy - 0.012, yy + 0.012, 1.8, 2.7, 'sofaD')
            else:
                D(m, xo - 0.012, xo + EMBED, yy - 0.012, yy + 0.012, 1.8, 2.7, 'sofaD')
    D(m, -5.6, 5.6, -2.6 - 0.014, -2.6 + EMBED, 0.72, 0.78, 'sofa')                    # base welts
    D(m, -5.6, 5.6, -2.6 - 0.014, -2.6 + EMBED, 1.6, 1.66, 'sofa')
    th = math.radians(-8)                                                                # button tufts on the back cushions
    for i in range(3):
        cx = -5.7 + i * 3.8 + 1.9
        for lx in (-1.0, 0.0, 1.0):
            x = cx + lx
            if -5.5 < x < -3.1 or 3.3 < x < 5.6:
                continue                                                                  # behind a pillow
            for lz in (-0.55, 0.55):
                yy = 1.075 + (-0.475 + EMBED) * math.cos(th) - lz * math.sin(th)
                zz = 4.025 + (-0.475 + EMBED) * math.sin(th) + lz * math.cos(th)
                m.cy(x, yy, zz, 0.09, 0.09, 0.035, 'sofaD', seg=6, rot=(82, 0, 0), flat=True)
    for x in (-4.6, -2.3, 0.0, 2.3, 4.6):                                                # back: seams and a top welt
        D(m, x - 0.012, x + 0.012, 2.95 - EMBED, 2.95 + 0.014, 1.8, 5.45, 'sofaD')
    D(m, -6.8, 6.8, 2.95 - EMBED, 2.95 + 0.014, 5.45, 5.52, 'sofa2')
    for sx in (-1, 1):                                                                   # feet: brass collar and toe cap
        for sy in (-1, 1):
            m.cy(sx * 6.4, sy * 2.3, 0.5, 0.2, 0.2, 0.1, 'mustard', seg=6, flat=True)
            m.cy(sx * 6.4, sy * 2.3, 0.0, 0.235, 0.235, 0.06, 'mustard', seg=6, flat=True)


# ------------------------------------------------------------------ coffee table
def coffee_detail(m):
    for s in (-1, 1):                                               # edge banding round the top
        band(m, -3.9, 3.9, 2.38, 2.54, s * 1.9, 'oak2', sign=s)
        xe = s * 3.9
        if s > 0:
            D(m, xe - EMBED, xe + 0.014, -1.85, 1.85, 2.38, 2.54, 'oak2')
        else:
            D(m, xe - 0.014, xe + EMBED, -1.85, 1.85, 2.38, 2.54, 'oak2')
    yf = -1.7                                                        # a drawer front in the apron
    frame_lines(m, -2.5, 2.5, 2.05, 2.27, yf, 'oak', t=0.035)
    pull(m, 0.0, 2.16, yf, long=0.9)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 3.4, sy * 1.5, 0.0, 0.14, 0.14, 0.14, 'mustard', seg=6, flat=True)   # brass ferrules


# ------------------------------------------------------------------ TV unit
def tvstand_detail(m):
    yf = -1.5
    band(m, -6.0, 6.0, 3.1, 3.18, yf, 'oak')                         # banding along top and foot
    band(m, -6.0, 6.0, 0.64, 0.72, yf, 'oak')
    for x0, kx, hx, (xa, xb) in ((-5.8, 3.2, -5.6, (-5.42, -2.9)), (2.0, 0.5, 5.52, (2.9, 5.35))):
        yd = -1.52                                                    # shaker panel, hinges, knob plate on each door
        frame_lines(m, xa, xb, 1.15, 2.7, yd, 'oak', t=0.07, d=0.014)
        for z in (1.0, 2.7):
            hinge(m, hx, z - 0.2, z + 0.2, yd, w=0.1)
        Dy(m, x0 + kx, 1.9, yd, 0.16, 'steel', d=0.014, seg=8)
    m.cy(-0.9, 1.25, 3.2 - EMBED, 0.2, 0.2, 0.02, 'black', seg=8, flat=True)   # cable grommet and the cable to the TV
    D(m, -0.95, -0.85, 1.2, 1.3, 3.2, 4.35, 'white')
    D(m, -0.98, -0.82, 0.755, 1.32, 4.3, 4.4, 'white')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 5.5, sy * 1.1, 0.0, 0.17, 0.17, 0.08, 'mustard', seg=6, flat=True)


# ------------------------------------------------------------------ sideboard
def sideboard_detail(m):
    yf = -1.5
    band(m, -5.0, 5.0, 4.78, 4.86, yf, 'oak')
    band(m, -5.0, 5.0, 0.84, 0.92, yf, 'oak')
    for i in range(4):
        x0 = -4.85 + i * 2.43
        yp = -1.535
        frame_lines(m, x0 + 0.62, x0 + 1.8, 1.5, 4.2, yp, 'oak', t=0.06, d=0.012)
        hx = x0 + (0.18 if i % 2 == 0 else 2.18)
        for z0 in (1.55, 3.95):
            hinge(m, hx, z0, z0 + 0.4, yp, w=0.12)
        Dy(m, x0 + (2.0 if i % 2 == 0 else 0.33), 2.9, yp, 0.15, 'steel', d=0.014, seg=8)
    m.cy(-3.0, 0.3, 4.89, 0.55, 0.55, 0.09, 'mustard', seg=10, flat=True)    # lamp: foot ring, neck collar, cord
    m.cy(-3.0, 0.3, 6.88, 0.42, 0.42, 0.2, 'mustard', seg=10, flat=True)
    D(m, -3.04, -2.96, 0.75, 1.45, 4.9 - EMBED, 4.94, 'cream')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 4.6, sy * 1.1, 0.0, 0.165, 0.165, 0.08, 'mustard', seg=6, flat=True)


# ------------------------------------------------------------------ bookshelf
def bookshelf_detail(m):
    yf = -0.95
    for zs in (3.0, 5.4, 7.8, 10.2):
        band(m, -2.7, 2.7, zs - 0.12, zs - 0.02, -0.9, 'walnut2')
    for sx in (-1, 1):                                              # cam-lock caps on the posts
        for z in (3.4, 8.8):
            screw(m, sx * 2.91, z, yf, s=0.11, c='steel', d=0.016)
    D(m, -3.1 + INS, 3.1 - INS, -1.05 - 0.02, -1.05 + EMBED, 12.5, 12.58, 'walnut2')   # top edge bead
    D(m, -2.82 + INS, 2.82 - INS, -0.95 - 0.012, -0.95 + EMBED, 0.3, 0.36, 'walnut')   # plinth groove


# ------------------------------------------------------------------ fireplace
def fireplace_detail(m):
    for x in (-2.5, 0.0, 2.5):                                      # hearth slab joints on the front and on top
        D(m, x - 0.012, x + 0.012, -0.6 - 0.008, -0.6 + 0.006, 0.03, 0.32, 'oak2')
        D(m, x - 0.012, x + 0.012, -0.58, -0.22, 0.35 - EMBED, 0.357, 'oak2')
    D(m, -5.0 + INS, 5.0 - INS, -0.6 - 0.04, -0.6 + EMBED, 0.27, 0.31, 'trim2')     # hearth nosing
    for sx in (-1, 1):
        a, b = sorted((sx * 2.6, sx * 4.6))
        D(m, a + INS, b - INS, -0.2 - 0.05, -0.2 + EMBED, 0.36, 0.9, 'trim2')        # pillar plinth
        D(m, a + INS, b - INS, -0.2 - 0.04, -0.2 + EMBED, 6.55, 6.9, 'trim2')        # pillar capital
        for z in (1.45, 2.55, 3.65, 4.75, 5.85):                                      # stone courses
            D(m, a + INS, b - INS, -0.2 - 0.008, -0.2 + EMBED, z - 0.012, z + 0.012, 'oak2')
    D(m, -0.5, 0.5, -0.2 - 0.07, -0.2 + EMBED, 5.7, 7.1, 'trim2')                    # keystone
    for r, (z0, z1) in enumerate(((0.36, 1.4), (1.4, 2.6), (2.6, 3.8), (3.8, 5.0), (5.0, 5.6))):   # brick joints
        x = -2.08 + (0.0 if r % 2 == 0 else 0.52)
        while x < 2.55:
            D(m, x - 0.02, x + 0.02, 0.185, 0.2 + EMBED, z0 + 0.06, z1 - 0.06, 'brick')
            x += 1.04
    for i in range(9):                                              # fire-basket bars in front of the logs
        x = -1.6 + i * 0.4
        D(m, x - 0.035, x + 0.035, -0.16, -0.1 + EMBED, 0.4, 1.0, 'steel2')
    D(m, -1.8 + INS, 1.8 - INS, -0.17, -0.1 + 0.006, 1.0, 1.07, 'steel2')
    D(m, -1.8 + INS, 1.8 - INS, -0.17, -0.1 + 0.006, 0.52, 0.58, 'steel2')
    D(m, -4.6 + INS, 4.6 - INS, -0.5, -0.2 + 0.006, 6.9, 7.2 - 0.004, 'walnut2')    # mantel moulding underneath
    D(m, -5.3 + INS, 5.3 - INS, -0.7 - 0.016, -0.7 + EMBED, 7.25, 7.34, 'walnut2')   # bead on the mantel front
    frame_lines(m, -4.08, 4.08, 9.72, 14.88, 0.85, 'trim', t=0.06, d=0.012)           # bead ring in the mirror frame


# ------------------------------------------------------------------ rug
def rug_detail(m):
    for s in (-1, 1):                                                # binding along the edges
        y0, y1 = (5.88, 6.0 - INS) if s > 0 else (-6.0 + INS, -5.88)
        D(m, -8.0 + INS, 8.0 - INS, y0, y1, 0.055, 0.066, 'rugB')
        x0, x1 = (7.88, 8.0 - INS) if s > 0 else (-8.0 + INS, -7.88)
        D(m, x0, x1, -5.88, 5.88, 0.055, 0.066, 'rugB')
        for i in range(10):                                           # woven dashes in the cream border
            x = -7.2 + i * 1.6
            D(m, x - 0.3, x + 0.3, s * 5.72 - 0.05, s * 5.72 + 0.05, 0.055, 0.066, 'mustard')


# ------------------------------------------------------------------ window overlays
def window_detail(m, wy, W, Z0, Z1):
    D(m, -W - 0.35 + INS, W + 0.35 - INS, wy - 0.46, wy - 0.42 + EMBED, Z0 - 0.2, Z0 + 0.004, 'trim')   # sill nosing
    frame_lines(m, -W + 0.4, W - 0.4, Z0 - 1.05, Z0 - 0.65, wy - 0.3, 'trim', t=0.05, d=0.014)        # apron panel
    for sx in (-1, 1):                                               # inner beads on the jambs, hinges on the outside
        xi = sx * (W - 0.17)
        a, b = sorted((xi, xi - sx * 0.06))
        D(m, a, b, wy - 0.34 - 0.014, wy - 0.34 + EMBED, Z0 + 0.02, Z1 - 0.02, 'trim2')
        for z in (Z0 + 1.6, Z1 - 2.2):
            hinge(m, sx * (W + 0.11), z, z + 0.6, wy - 0.34, w=0.16)
    D(m, -W - 0.3 + INS, W + 0.3 - INS, wy - 0.36 - 0.07, wy - 0.36 + EMBED, Z1 + 0.46, Z1 + 0.54, 'trim2')   # head cap
    for x in (-W / 3, W / 3):                                        # glazing bar fillets
        D(m, x - 0.03, x + 0.03, wy - 0.25 - 0.012, wy - 0.25 + EMBED, Z0 + 0.02, Z1 - 0.02, 'trim2')
    yb = wy - 0.245                                                  # sash catch on the cross bar
    D(m, -0.2, 0.2, yb - 0.014, yb + EMBED, Z0 + 3.3, Z0 + 3.5, 'steel')
    D(m, -0.7, 0.12, yb - 0.07, yb - 0.014 + EMBED, Z0 + 3.38, Z0 + 3.46, 'steel2')
    for sx in (-1, 1):                                               # curtain rod brackets over the glass
        D(m, sx * (W - 0.8) - 0.05, sx * (W - 0.8) + 0.05, wy - 0.45, wy + EMBED, Z1 + 0.88, Z1 + 1.12, 'mustard')


# ------------------------------------------------------------------ gate (the giant interior door)
def gate_detail(m, s, ys):
    """hinges and kick plates on the door slab (ys = the slab's front plane in the current frame)"""
    hx = 2.8 * s
    for z in (2.0, 6.6, 11.2):
        D(m, hx - 0.22, hx + 0.22, ys - 0.016, ys + EMBED, z - 0.5, z + 0.5, 'steel')
        m.cy(hx, ys - 0.016, z - 0.46, 0.05, 0.05, 0.92, 'steel2', seg=6, flat=True)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.65, sx * 2.85))
        D(m, a, b, ys - 0.02, ys + EMBED, 0.06, 0.95, 'steel2')
        for (xx, zz) in ((a + 0.12, 0.2), (b - 0.12, 0.2), (a + 0.12, 0.8), (b - 0.12, 0.8)):
            screw(m, xx, zz, ys - 0.02, s=0.06, c='steel', d=0.01)


# ------------------------------------------------------------------ kitchen units
def counter_detail(m, kind):
    D(m, -1.5 + INS, 1.5 - INS, -1.7 - 0.012, -1.7 + EMBED, 0.4, 0.46, 'steel2')           # kick plinth line
    D(m, -1.53 + INS, 1.53 - INS, -2.05 - 0.012, -2.05 + EMBED, 5.3, 5.34, 'oak2')          # worktop grain line
    for sx in (-1, 1):                                                                      # upper doors: shaker lines, hinges
        a, b = sorted((sx * 0.34, sx * 1.26))
        frame_lines(m, a, b, 9.9, 14.1, 0.58, 'trim2', t=0.05, d=0.012)
        for z in (9.8, 14.0):
            hinge(m, sx * 1.34, z, z + 0.3, 0.58, w=0.1)
    for x in (-1.0, -0.5, 0.0, 0.5, 1.0):                                                   # backsplash grout lines
        D(m, x - 0.02, x + 0.02, 1.975, 1.99 + 0.006, 5.54, 9.38, 'tile2')
    if kind != 'stove':
        D(m, -1.5 + INS, 1.5 - INS, 0.56, 0.6 + EMBED, 9.36, 9.403, 'trim2')               # light rail under the uppers
        yd = -1.88
        for sx in (-1, 1):
            for z in (1.0, 3.2):
                hinge(m, sx * 1.35, z, z + 0.4, yd, w=0.1)
            Dy(m, sx * 0.3, 3.4, -1.9, 0.15, 'steel', d=0.012, seg=8)
        frame_lines(m, -1.3, 1.3, 4.12, 4.93, yd, 'trim2', t=0.035, d=0.012)
    if kind == 'plain':
        socket_plate(m, -1.1, 7.0, 1.99)
    if kind == 'sink':
        m.cy(0.0, -0.45, 5.53 - EMBED, 0.2, 0.2, 0.02, 'steel2', seg=8, flat=True)         # drain
        D(m, 0.08, 0.55, 1.14, 1.26, 6.3, 6.4, 'steel2')                                     # tap lever
    if kind == 'stove':
        for sx in (-1, 1):                                                                   # handle stand-offs
            D(m, sx * 0.9 - 0.05, sx * 0.9 + 0.05, -1.9, -1.88 + EMBED, 3.82, 3.93, 'steel2')
        for i in range(4):                                                                   # knob pointers
            x = -1.05 + i * 0.7
            D(m, x - 0.015, x + 0.015, -2.0 - 0.006, -2.0 + EMBED, 4.65, 4.76, 'cream')
        for (x, y_) in ((0.7, -0.8), (-0.7, 0.4), (0.7, 0.4)):                              # burner centres
            m.cy(x, y_, 5.617, 0.17, 0.17, 0.016, 'black', seg=8, flat=True)


def fridge_detail(m):
    for z in (0.75, 6.85, 7.9, 10.7):                                    # door hinges on the left
        hinge(m, -2.28, z, z + 0.5, -1.9, w=0.2)
    D(m, -1.0, 1.0, -1.9 - 0.014, -1.9 + EMBED, 10.3, 10.6, 'steel')       # chrome badge
    D(m, -0.7, 0.7, -1.9 - 0.02, -1.9 - 0.014 + EMBED, 10.38, 10.52, 'mint2')
    for z in (0.1, 0.22, 0.34):                                           # grille slots in the plinth
        D(m, -1.8, 1.8, -1.8 - 0.012, -1.8 + EMBED, z, z + 0.05, 'black')


def island_detail(m):
    band(m, -6.0, 6.0, 5.2, 5.4, -2.45, 'oak2')                           # worktop edge band
    for x in (-4.4, -2.4, -0.4, 1.5, 3.5, 5.3):                            # corbels under the overhang
        D(m, x - 0.15, x + 0.15, -2.4, -1.9 + EMBED, 4.55, 5.15 - 0.004, 'walnut')
    for i in range(4):                                                     # hinges on the back doors
        x0 = -5.6 + i * 2.85
        for (z0, z1) in ((1.0, 1.4), (4.4, 4.8)):
            D(m, x0 + 0.04, x0 + 0.24, 2.88 - EMBED, 2.88 + 0.014, z0, z1, 'steel')
            D(m, x0 + 0.134, x0 + 0.146, 2.88 + 0.014 - EMBED, 2.88 + 0.022, z0 + 0.02, z1 - 0.02, 'steel2')


def stool_detail(m):
    m.cy(0, 0, 4.3, 0.89, 0.89, 0.06, 'coral', seg=12, caps=False, flat=True)     # seat piping
    m.cy(0, 0, 4.45 - EMBED, 0.12, 0.12, 0.02, 'coral', seg=6, flat=True)         # tuft button
    for i in range(4):
        a = math.radians(45 + 90 * i)
        m.cy(math.cos(a) * 0.78, math.sin(a) * 0.78, 0.0, 0.12, 0.12, 0.1, 'black', seg=6, flat=True)


def dining_table_detail(m):
    for s in (-1, 1):
        band(m, -5.0, 5.0, 4.27, 4.46, s * 3.0, 'oak2', sign=s)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 4.4, sy * 2.4, 0.0, 0.26, 0.26, 0.08, 'mustard', seg=6, flat=True)
    m.cy(0, 0, 17.8, 0.5, 0.5, 0.04, 'steel', seg=8, flat=True)                     # ceiling rose
    m.cy(0, 0, 12.85, 0.14, 0.14, 0.35, 'steel', seg=6, flat=True)                  # cord grip on the shade
    m.cy(0, 0, 11.5, 2.05, 1.95, 0.1, 'tyellow', seg=12, caps=False, flat=True)     # rolled hem on the shade


def dining_chair_detail(m):
    D(m, -0.97, 0.97, -1.0 - 0.014, -1.0 + EMBED, 2.93, 2.97, 'coral')              # seat pad piping
    D(m, 1.0 - EMBED, 1.014, -0.97, 0.87, 2.93, 2.97, 'coral')
    D(m, -1.014, -1.0 + EMBED, -0.97, 0.87, 2.93, 2.97, 'coral')
    m.cy(0, -0.05, 3.0 - EMBED, 0.07, 0.07, 0.02, 'coral', seg=6, flat=True)        # centre tuft
    D(m, -0.98, 0.98, 0.8 - 0.012, 0.8 + EMBED, 5.48, 5.53, 'oak2')                 # back-rail grooves
    D(m, -0.98, 0.98, 0.8 - 0.012, 0.8 + EMBED, 5.87, 5.92, 'oak2')
    D(m, -1.2 + INS, 1.2 - INS, -1.2 - 0.012, -1.2 + EMBED, 2.6, 2.64, 'oak2')      # seat rail groove
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 1.0, sy * 1.0, 0.0, 0.15, 0.15, 0.1, 'mustard', seg=6, flat=True)


def lamp_detail(m):
    m.cy(0, 0, 0.18, 0.2, 0.12, 0.37, 'steel', seg=8, flat=True)            # collar above the base
    m.cy(0, 0, 7.5, 0.2, 0.14, 0.4, 'steel', seg=8, flat=True)             # collar under the shade
    D(m, -0.04, 0.04, 0.72, 0.99, 0.0, 0.04, 'cream')                        # cord out across the floor


def plant_detail(m, saucer_r):
    m.cy(0, 0, 0.0, saucer_r, saucer_r, 0.1, 'oak2', seg=10, flat=True)    # drip saucer


def hatch_detail(m):
    for sy in (-1, 1):
        for x in (-1.0, 0.0, 1.0):
            D(m, x - 0.05, x + 0.05, sy * 0.89 - 0.05, sy * 0.89 + 0.05, 0.097, 0.106, 'steel2')
    for sx in (-1, 1):
        D(m, sx * 1.325 - 0.05, sx * 1.325 + 0.05, -0.05, 0.05, 0.097, 0.106, 'steel2')
