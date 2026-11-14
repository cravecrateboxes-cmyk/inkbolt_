"""kit-classroom modelled detail (tactical look plan Stage 11): the finish and fittings a real classroom has, added to
the pieces the player sees most. Everything goes through K.bx(..., flat=True) / K.cyl so the part carries no outline
shell and no bevel, stands at least 3 mm proud of its face, starts EMBED inside it and keeps horizontal runs 5 mm
short of the piece sides. Coordinates are in the current m.parent frame (the frame the piece's own shapes use).

Finish and fittings only: skirting grooves and cap, chalk rail bead, wainscot panel moulding, cornice step, socket
plates, edge banding, bolts, ferrules, foot caps, hinges, handles, label holders, tray brackets. No grime."""

EMBED = 0.003
INS = 0.005          # runs stop 5 mm short of a piece's sides


def dbx(m, x0, x1, y0, y1, z0, z1, c):
    """detail box from extents (x0 x1 y0 y1 z0 z1), no outline"""
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    return m.bx(x0, y0, z0, x1, y1, z1, c, flat=True)


def dcy(m, loc, r, h, c, seg=6, rot=(0, 0, 0)):
    """detail cylinder, base at loc, axis along local z turned by rot"""
    m.cyl(loc, r, r, h, c, seg=seg, rot=rot, bevel=False)
    m.flat()


def bolt_y(m, x, z, yf, r=0.05, c='steelDk', d=0.018, sign=-1):
    """hex bolt head on a face looking toward -Y (sign -1) or +Y (sign +1)"""
    if sign < 0:
        dcy(m, (x, yf + EMBED, z), r, d + EMBED, c, rot=(90, 0, 0))
    else:
        dcy(m, (x, yf - EMBED, z), r, d + EMBED, c, rot=(-90, 0, 0))


def bolt_x(m, y, z, xf, r=0.05, c='steelDk', d=0.018, sign=1):
    """hex bolt head on a face looking toward +X (sign +1) or -X (sign -1)"""
    if sign > 0:
        dcy(m, (xf - EMBED, y, z), r, d + EMBED, c, rot=(0, 90, 0))
    else:
        dcy(m, (xf + EMBED, y, z), r, d + EMBED, c, rot=(0, -90, 0))


def frame_lines(m, x0, x1, z0, z1, yf, c, t=0.05, d=0.012):
    """raised rectangle outline on a -Y face (butt joints: no bar overlaps another)"""
    dbx(m, x0, x1, yf - d, yf + EMBED, z1 - t, z1, c)
    dbx(m, x0, x1, yf - d, yf + EMBED, z0, z0 + t, c)
    dbx(m, x0, x0 + t, yf - d, yf + EMBED, z0 + t, z1 - t, c)
    dbx(m, x1 - t, x1, yf - d, yf + EMBED, z0 + t, z1 - t, c)


def label_holder(m, x, z, yf, w=0.5, h=0.26, sign=-1, c='steelDk', card='cream'):
    """a metal card holder with a card in it, on a face looking toward -Y (sign -1) or +Y (sign +1)"""
    if sign < 0:
        dbx(m, x - w / 2, x + w / 2, yf - 0.012, yf + EMBED, z - h / 2, z + h / 2, c)
        dbx(m, x - w / 2 + 0.05, x + w / 2 - 0.05, yf - 0.02, yf - 0.012 + EMBED, z - h / 2 + 0.04, z + h / 2 - 0.04, card)
    else:
        dbx(m, x - w / 2, x + w / 2, yf - EMBED, yf + 0.012, z - h / 2, z + h / 2, c)
        dbx(m, x - w / 2 + 0.05, x + w / 2 - 0.05, yf + 0.012 - EMBED, yf + 0.02, z - h / 2 + 0.04, z + h / 2 - 0.04, card)


# ------------------------------------------------------------------ wall modules
def wall_detail(m, window_open=False, dado=True, panel=True):
    """skirting groove and cap, chalk-rail bead, wainscot panel moulding, cornice step of one 1 m wall module.
    Faces sit on the planes wall_base draws: skirting -0.49, dado -0.497, cap -0.53, cornice -0.497, frieze -0.46,
    wainscot -0.42. Nothing leaves the cell (x +-0.495, y >= -0.53)."""
    a, b = -0.49, 0.49      # 1 cm in: clear of the corner posts (x +-0.493) as well
    # skirting: a routed groove and a cap moulding on its top edge
    dbx(m, a, b, -0.49 - 0.012, -0.49 + EMBED, 0.38, 0.42, 'honey')
    dbx(m, a, b, -0.507, -0.49 + EMBED, 0.78, 0.84, 'honey')
    # wainscot: a panel moulding, one panel a metre
    if panel:
        frame_lines(m, -0.3, 0.3, 1.2, 4.6, -0.42, 'trim', t=0.04, d=0.01)
    if dado and not window_open:
        # chalk rail: a fine bead in the middle of the dado board and a bead under the cap
        dbx(m, a, b, -0.497 - 0.012, -0.497 + EMBED, 5.34, 5.38, 'honey')
        dbx(m, a, b, -0.52, -0.497 + EMBED, 5.205, 5.245, 'honey')
    # cornice: a stepped crown over the bead and a picture-hook rail on the frieze
    dbx(m, a, b, -0.52, -0.497 + EMBED, 15.6, 15.66, 'honey')
    dbx(m, a, b, -0.46 - 0.014, -0.46 + EMBED, 15.9, 15.96, 'honeyDk')


def socket_plate(m, x, z, yf):
    """a double plug socket at a toy's-eye height: faceplate, two round sockets, two screws"""
    dbx(m, x - 0.27, x + 0.27, yf - 0.04, yf + EMBED, z - 0.27, z + 0.27, 'white')
    for sx in (-1, 1):
        dbx(m, x + sx * 0.12 - 0.08, x + sx * 0.12 + 0.08, yf - 0.05, yf - 0.04 + EMBED, z - 0.08, z + 0.08, 'trim')
        dbx(m, x + sx * 0.12 - 0.035, x + sx * 0.12 + 0.035, yf - 0.056, yf - 0.05 + EMBED, z - 0.035, z + 0.035, 'steelDk')
    for sz in (-1, 1):
        bolt_y(m, x, z + sz * 0.215, yf - 0.04, r=0.025, d=0.008, c='steel')


def switch_extras(m):
    """bezel frame and screws round the existing switch plate (x +-0.21, z 6.8..7.55, face y -0.47)"""
    frame_lines(m, -0.2, 0.2, 6.81, 7.54, -0.47, 'trim', t=0.02, d=0.008)


def vent_screws(m):
    for sx in (-1, 1):
        for z in (11.68, 12.82):
            bolt_y(m, sx * 0.425, z, -0.47, r=0.03, d=0.014)


# ------------------------------------------------------------------ student desk
def desk_detail(m):
    """edge banding round the top, a pencil groove, a tray lip and tray bolts, leg ferrules, footrest bolts"""
    # banding (top face flat span: bevel 0.03 -> z 4.18..4.42 on the sides, front)
    dbx(m, -2.865, 2.865, -0.4 - 0.012, -0.4 + EMBED, 4.19, 4.41, 'honeyDk')
    for sx in (-1, 1):
        x0, x1 = (2.9 - EMBED, 2.912) if sx > 0 else (-2.912, -2.9 + EMBED)
        dbx(m, x0, x1, -0.365, 3.365, 4.19, 4.41, 'honeyDk')
    dbx(m, -2.865, 2.865, 3.4 - EMBED, 3.4 + 0.012, 4.19, 4.41, 'honeyDk')
    # pencil groove along the back of the top
    dbx(m, -2.3, 2.3, 3.0, 3.1, 4.447, 4.455, 'honeyDk')
    # tray: front lip along the floor panel, bolts down both side walls
    dbx(m, -2.295, 2.295, 0.15 - 0.012, 0.15 + EMBED, 3.304, 3.376, 'steelDk')
    for y in (0.5, 1.55, 2.6):
        bolt_x(m, y, 3.95, 2.3, r=0.045, d=0.016, sign=1)
        bolt_x(m, y, 3.95, -2.3, r=0.045, d=0.016, sign=-1)
    # steel ferrules where the legs meet the rubber feet
    for x in (-2.55, 2.55):
        for y in (-0.1, 3.1):
            m.cyl((x, y, 0.117), 0.19, 0.19, 0.1, 'steelDk', seg=6, bevel=False)
            m.flat()
    # footrest bolts through the front legs' bar
    for x in (-2.2, 2.2):
        bolt_y(m, x, 0.525, 3.04, r=0.05, d=0.016)


# ------------------------------------------------------------------ chair
def chair_detail(m):
    """seat banding, backrest bolts and top banding, foot caps and under-seat brackets"""
    z0, z1 = 2.485, 2.585
    dbx(m, -1.215, 1.215, 1.15 - EMBED, 1.15 + 0.012, z0, z1, 'honeyDk')
    dbx(m, -1.215, 1.215, -1.15 - 0.012, -1.15 + EMBED, z0, z1, 'honeyDk')
    for sx in (-1, 1):
        x0, x1 = (1.25 - EMBED, 1.262) if sx > 0 else (-1.262, -1.25 + EMBED)
        dbx(m, x0, x1, -1.115, 1.115, z0, z1, 'honeyDk')
    # backrest: top edge banding and four bolts through to the back legs
    dbx(m, -1.195, 1.195, -1.115, -0.985, 4.75 - EMBED, 4.762, 'honeyDk')
    for x in (-1.05, 1.05):
        for z in (3.95, 4.5):
            bolt_y(m, x, z, -1.12, r=0.055, d=0.018)
    # rubber caps on the four feet; steel brackets under the seat corners
    for x in (-1.05, 1.05):
        for y in (-0.95, 0.95):
            m.cyl((x, y, -EMBED), 0.145, 0.145, 0.1 + EMBED, 'rubber', seg=6, bevel=False)
            m.flat()
            dbx(m, x - 0.17, x + 0.17, y - 0.17, y + 0.17, 2.41, 2.45 + EMBED, 'steelDk')


# ------------------------------------------------------------------ teacher's desk
def teacher_desk_detail(m):
    z = 4.75
    # banding round the top
    dbx(m, -4.815, 4.815, -2.35 - 0.014, -2.35 + EMBED, 4.485, 4.715, 'honeyDk')
    dbx(m, -4.815, 4.815, 2.35 - EMBED, 2.35 + 0.014, 4.485, 4.715, 'honeyDk')
    for sx in (-1, 1):
        x0, x1 = (4.85 - EMBED, 4.864) if sx > 0 else (-4.864, -4.85 + EMBED)
        dbx(m, x0, x1, -2.315, 2.315, 4.485, 4.715, 'honeyDk')
    # panel mouldings on the three raised panels of the class-facing front (face y -2.13)
    for (x0, x1, z0, z1) in ((-3.95, -1.45, 1.3, 4.05), (-1.15, 1.45, 1.3, 4.05), (2.2, 4.2, 0.6, 4.05)):
        frame_lines(m, x0 + 0.2, x1 - 0.2, z0 + 0.2, z1 - 0.2, -2.13, 'honeyDk', t=0.07, d=0.014)
    # drawer fronts (face y 2.16, looking +Y): moulding, label holders, a lock on the top drawer
    for (z0, z1) in ((0.45, 1.75), (1.85, 3.05), (3.15, 4.3)):
        zc = (z0 + z1) / 2
        d = 0.012
        yf = 2.16
        t = 0.05
        x0, x1, a, b = 2.1, 4.3, z0 + 0.15, z1 - 0.15
        dbx(m, x0, x1, yf - EMBED, yf + d, b - t, b, 'honeyDk')
        dbx(m, x0, x1, yf - EMBED, yf + d, a, a + t, 'honeyDk')
        dbx(m, x0, x0 + t, yf - EMBED, yf + d, a + t, b - t, 'honeyDk')
        dbx(m, x1 - t, x1, yf - EMBED, yf + d, a + t, b - t, 'honeyDk')
        label_holder(m, 3.2, zc + 0.22, yf, w=0.7, h=0.2, sign=1)
    # cable grommet in the top: steel ring and a rubber plug
    dcy(m, (-3.9, -1.4, z - EMBED), 0.27, 0.008 + EMBED, 'steelDk', seg=10)
    dcy(m, (-3.9, -1.4, z - 2 * EMBED), 0.2, 0.016 + 2 * EMBED, 'rubber', seg=10)


# ------------------------------------------------------------------ blackboard
def chalkboard_detail(m):
    yb = 0.46
    # screws along the top and side bars of the frame (front face y 0.25)
    for i in range(-4, 5):
        bolt_y(m, i * 2.4, 12.6, 0.25, r=0.07, d=0.02)
    for sx in (-1, 1):
        for z in (6.5, 8.3, 10.1, 11.7):
            bolt_y(m, sx * 10.75, z, 0.25, r=0.07, d=0.02)
    # board seams: three panels
    for x in (-3.5, 3.5):
        dbx(m, x - 0.012, x + 0.012, 0.31 - 0.006, 0.31 + EMBED, 5.72, 12.38, 'boardDk')
    # tray: end caps and brackets
    for sx in (-1, 1):
        x0, x1 = (10.6 - EMBED, 10.614) if sx > 0 else (-10.614, -10.6 + EMBED)
        dbx(m, x0, x1, -0.345, 0.245, 5.304, 5.616, 'honey')
    for x in (-9.0, -4.5, 0.0, 4.5, 9.0):
        dbx(m, x - 0.15, x + 0.15, -0.25, 0.24, 5.18, 5.303, 'honeyDk')


# ------------------------------------------------------------------ bookcase (open to -Y; the caller turns the frame)
def bookcase_detail(m):
    # edge banding on the shelf boards and the plinth; label holders on the shelf fronts
    for z in (2.0, 3.7):
        dbx(m, -2.795, 2.795, -0.8 - 0.012, -0.8 + EMBED, z - 0.115, z - 0.005, 'honeyDk')
        label_holder(m, 0.0, z - 0.06, -0.8 - 0.012, w=0.9, h=0.1, sign=-1)
    dbx(m, -2.795, 2.795, -0.8 - 0.012, -0.8 + EMBED, 0.12, 0.16, 'honey')
    # crown step on the top board and vertical banding on the post fronts
    dbx(m, -2.945, 2.945, -0.85 - 0.03, -0.85 + EMBED, 5.5, 5.58, 'honeyDk')
    for sx in (-1, 1):
        x0, x1 = (2.805, 2.945) if sx > 0 else (-2.945, -2.805)
        dbx(m, x0, x1, -0.85 - 0.012, -0.85 + EMBED, 0.2, 5.4, 'honeyDk')
        # cam-lock caps on the outside of the posts
        for z in (2.0, 3.7, 1.0):
            for y in (-0.5, 0.5):
                bolt_x(m, y, z - 0.06, sx * 2.95, r=0.07, d=0.016, c='steelDk', sign=sx)


# ------------------------------------------------------------------ cork noticeboard
def cork_detail(m):
    # a bead down the middle of the frame, and a pin ledge under the board
    dbx(m, -4.395, 4.395, -0.56 - 0.014, -0.56 + EMBED, 12.22, 12.33, 'honey')
    dbx(m, -4.395, 4.395, -0.56 - 0.014, -0.56 + EMBED, 6.47, 6.58, 'honey')
    for sx in (-1, 1):
        a, b = sorted((sx * 4.15, sx * 4.3))
        dbx(m, a, b, -0.56 - 0.014, -0.56 + EMBED, 6.75, 12.05, 'honey')
    dbx(m, -4.395, 4.395, -0.7, -0.56 + EMBED, 6.2, 6.353, 'honeyDk')


# ------------------------------------------------------------------ window bay
def window_detail(m):
    # sill: front groove and a lip on its top edge, corbels under it
    dbx(m, -2.555, 2.555, -0.8 - 0.012, -0.8 + EMBED, 5.3, 5.34, 'honeyDk')
    dbx(m, -2.555, 2.555, -0.806, -0.77, 5.617, 5.665, 'honey')
    for x in (-2.2, -0.75, 0.75, 2.2):
        dbx(m, x - 0.12, x + 0.12, -0.78, -0.42 + EMBED, 5.0, 5.163, 'honey')
        dbx(m, x - 0.08, x + 0.08, -0.62, -0.42 + 2 * EMBED, 4.7, 5.0 + EMBED, 'honey')
    # head casing: a cap moulding on top
    dbx(m, -2.66, 2.66, -0.56, -0.417, 14.297, 14.4, 'honey')
    # hinges on the side casings (face y -0.5)
    for sx in (-1, 1):
        a, b = sorted((sx * 2.47, sx * 2.59))
        for z in (6.4, 9.6, 12.8):
            dbx(m, a, b, -0.5 - 0.012, -0.5 + EMBED, z - 0.3, z + 0.3, 'steelDk')
            bolt_y(m, sx * 2.53, z - 0.18, -0.512, r=0.025, d=0.008, c='steel')
            bolt_y(m, sx * 2.53, z + 0.18, -0.512, r=0.025, d=0.008, c='steel')
    # lever handles on the mullions (front face y -0.33)
    for x in (-1.22, 0.0, 1.22):
        dbx(m, x - 0.05, x + 0.05, -0.342, -0.33 + EMBED, 7.2, 7.9, 'steelDk')
        dbx(m, x - 0.03, x + 0.3, -0.375, -0.342 + EMBED, 7.5, 7.6, 'steel')
