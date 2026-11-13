"""kit-bedroom modelled detail (tactical look plan Stage 11): the finish and fittings a real bedroom has, added to the
pieces the player sees most. Everything is drawn through the bedroom Kit's no-outline detail model (k.dbx / k.dcyl:
no outline shell, no bevel), stands at least 3 mm proud of its face, starts EMBED inside it and keeps horizontal runs
5 mm short of the piece sides. All coordinates are in the current k.m.parent frame (the same frame the piece's own
shapes use); faces that look toward Blender -Y are drawn at the plane y = yf.

Detail is finish and fittings only: skirting grooves, dado and picture rails, cornice, plug sockets and switch plates,
hinges, handles, screw and cam caps, edge banding, label holders, foot caps. Nothing is grime."""
import math

EMBED = 0.003
INS = 0.005          # runs stop 5 mm short of a piece's sides


# ------------------------------------------------------------------ small fittings
def screw(k, x, z, yf, s=0.05, c='metal2', d=0.012):
    """a screw head (square, reads as a slotted head at this scale) on a -Y face"""
    k.dbx(x - s / 2, x + s / 2, yf - d, yf + EMBED, z - s / 2, z + s / 2, c)


def disc_y(k, x, z, yf, r, c, d=0.014, seg=8, sign=-1):
    """a round cap / washer standing out of a face that looks toward -Y (sign -1) or +Y (sign +1)"""
    if sign < 0:
        k.dcyl((x, yf + EMBED, z), r, d + EMBED, c, seg=seg, rot=(90, 0, 0))
    else:
        k.dcyl((x, yf - EMBED, z), r, d + EMBED, c, seg=seg, rot=(-90, 0, 0))


def disc_x(k, y, z, xf, r, c, d=0.014, seg=8, sign=1):
    """a round cap on a face looking toward +X (sign +1) or -X (sign -1)"""
    if sign > 0:
        k.dcyl((xf - EMBED, y, z), r, d + EMBED, c, seg=seg, rot=(0, 90, 0))
    else:
        k.dcyl((xf + EMBED, y, z), r, d + EMBED, c, seg=seg, rot=(0, -90, 0))


def edge_band(k, x0, x1, z0, z1, yf, c, d=0.014):
    """edge banding on the front face of a board (run inset 5 mm from its ends)"""
    k.dbx(x0 + INS, x1 - INS, yf - d, yf + EMBED, z0, z1, c)


def frame_lines(k, x0, x1, z0, z1, yf, c, t=0.05, d=0.012):
    """a thin raised rectangle outline: a routed drawer / door panel (butt joints: no shape overlaps another)"""
    k.dbx(x0, x1, yf - d, yf + EMBED, z1 - t, z1, c)
    k.dbx(x0, x1, yf - d, yf + EMBED, z0, z0 + t, c)
    k.dbx(x0, x0 + t, yf - d, yf + EMBED, z0 + t, z1 - t, c)
    k.dbx(x1 - t, x1, yf - d, yf + EMBED, z0 + t, z1 - t, c)


def rosette(k, x, z, yf, r, c='metal', knob_hole=False):
    disc_y(k, x, z, yf, r, c, d=0.02, seg=10)


def label_holder(k, x, z, yf, w=0.8, h=0.13, c='cream', line='tblue'):
    """a card in a drawer-front label slot"""
    k.dbx(x - w / 2, x + w / 2, yf - 0.012, yf + EMBED, z - h / 2, z + h / 2, c)
    k.dbx(x - w * 0.32, x + w * 0.32, yf - 0.019, yf - 0.012 + EMBED, z - h * 0.12, z + h * 0.12, line)


# ------------------------------------------------------------------ wall modules
def socket_plate(k, x, z, y):
    """a 13 A plug socket: faceplate, raised boss, three slots, two screws (y = the wall face plane)"""
    k.dbx(x - 0.25, x + 0.25, y - 0.03, y + EMBED, z - 0.25, z + 0.25, 'white')
    k.dbx(x - 0.17, x + 0.17, y - 0.042, y - 0.03 + EMBED, z - 0.15, z + 0.15, 'trim2')
    k.dbx(x - 0.03, x + 0.03, y - 0.049, y - 0.042 + EMBED, z + 0.05, z + 0.12, 'ink')
    for sx in (-1, 1):
        k.dbx(x + sx * 0.085 - 0.03, x + sx * 0.085 + 0.03, y - 0.049, y - 0.042 + EMBED, z - 0.1, z - 0.02, 'ink')
    for sz in (-1, 1):
        screw(k, x, z + sz * 0.212, y - 0.03 + 0.0, s=0.045, c='metal', d=0.008)


def switch_plate(k, x, z, y):
    """a rocker light switch: faceplate, two-step rocker, two screws"""
    k.dbx(x - 0.25, x + 0.25, y - 0.03, y + EMBED, z - 0.25, z + 0.25, 'white')
    k.dbx(x - 0.13, x + 0.13, y - 0.075, y - 0.03 + EMBED, z + 0.012, z + 0.17, 'cream')
    k.dbx(x - 0.13, x + 0.13, y - 0.05, y - 0.03 + EMBED, z - 0.17, z - 0.012, 'trim2')
    for sz in (-1, 1):
        screw(k, x, z + sz * 0.215, y - 0.03 + 0.0, s=0.04, c='metal', d=0.008)


def wall_detail(k, motif, dz, S, y, skirt_front):
    """skirting grooves, dado and picture rails, border beads, cornice and the socket / switch plates of one wall module.
    dz = the E/W modules' 6 mm trim lift, y = wall face plane, skirt_front = the skirting face plane."""
    ys = skirt_front
    # skirting: a plinth step along the foot, a routed groove and a fine line on the top bead
    k.dbx(-0.5 + INS, 0.5 - INS, ys - 0.03, ys + EMBED, 0.004, 0.2, 'trim2')
    k.dbx(-0.5 + INS, 0.5 - INS, ys - 0.012, ys + EMBED, 0.5 + dz, 0.54 + dz, 'trim2')
    k.dbx(-0.5 + INS, 0.5 - INS, ys - 0.035 - 0.014, ys - 0.035 + EMBED, 0.935 + dz, 0.97 + dz, 'trim')
    # dado rail with a bead beneath it
    k.dbx(-0.5 + INS, 0.5 - INS, y - 0.07, y + EMBED, 2.95 + dz, 3.13 + dz, 'trim')
    k.dbx(-0.5 + INS, 0.5 - INS, y - 0.045, y + EMBED, 2.89 + dz, 2.95 + dz, 'trim2')
    # border band: a bead line along each edge of the paper
    for z in (8.09, 9.31):
        k.dbx(-0.5 + INS, 0.5 - INS, y - 0.05 - 0.014, y - 0.05 + EMBED, z - 0.015 + dz, z + 0.015 + dz, S['star'])
    # picture-hook rail and cornice under the ceiling
    k.dbx(-0.5 + INS, 0.5 - INS, y - 0.05, y + EMBED, 14.6 + dz, 14.74 + dz, 'trim2')
    k.dbx(-0.5 + INS, 0.5 - INS, y - 0.1, y + EMBED, 17.66 + dz, 17.99 - dz, 'trim')
    k.dbx(-0.5 + INS, 0.5 - INS, y - 0.055, y + EMBED, 17.5 + dz, 17.66 - 0.003 + dz, 'trim2')
    if motif == 'Star':
        socket_plate(k, 0.0, 1.95, y)
    elif motif == 'Accent':
        switch_plate(k, 0.0, 6.1, y)


# ------------------------------------------------------------------ bed
def bed_detail(k, posts, leg):
    """bolt covers where the rails join the posts, dowel plugs and battens on the head and foot boards, brass collars"""
    for sx in (-1, 1):
        xf = sx * 5.0
        for (y, z) in ((-6.35, 2.7), (6.35, 2.7), (6.35, 3.05)):
            disc_x(k, y, z, xf, 0.1, 'metal', d=0.02, seg=8, sign=sx)
        k.dbx(min(xf - EMBED * sx, xf + 0.012 * sx), max(xf - EMBED * sx, xf + 0.012 * sx), -6.7, 6.7, 2.53, 2.57, 'wood3')
    # head board back: two cross battens with bolt heads, plank joints
    for (z0, z1) in ((1.5, 1.85), (4.3, 4.65)):
        k.dbx(-4.1, 4.1, 7.35 - EMBED, 7.46, z0, z1, 'wood2')
        for x in (-3.6, -1.2, 1.2, 3.6):
            disc_y(k, x, (z0 + z1) / 2, 7.46, 0.08, 'metal', d=0.02, seg=8, sign=+1)
    for x in (-2.8, -1.4, 0.0, 1.4, 2.8):
        k.dbx(x - 0.015, x + 0.015, 7.35 - 0.01, 7.35 + EMBED, 0.9, 6.4, 'wood3')
    # head board front: dowel plugs down each side
    for sx in (-1, 1):
        for z in (1.6, 3.4, 5.2):
            disc_y(k, sx * 4.0, z, 6.95, 0.11, 'wood3', d=0.02, seg=8, sign=-1)
    # foot board outer face: dowel plugs
    for sx in (-1, 1):
        for z in (2.95, 3.9):
            disc_y(k, sx * 3.9, z, -7.35, 0.11, 'wood3', d=0.02, seg=8, sign=-1)
    # brass collar under each post knob
    for (x, y, top) in posts:
        k.dcyl((x, y, top - EMBED), 0.34, 0.07, 'tyellow', seg=8)


# ------------------------------------------------------------------ toy chest
def chest_detail(k):
    # lid corners: strap plates over the front / back faces and the ends
    for sx in (-1, 1):
        a, b = sorted((sx * 1.85, sx * 2.465))
        for sy in (-1, 1):
            yf = sy * 1.47
            y0, y1 = (yf - 0.014, yf + EMBED) if sy < 0 else (yf - EMBED, yf + 0.014)
            k.dbx(a, b, y0, y1, 2.88, 3.19, 'metal')
            if sy < 0:
                screw(k, sx * 2.1, 3.035, yf - 0.014, s=0.05, c='metal2', d=0.01)
            else:
                k.dbx(sx * 2.1 - 0.025, sx * 2.1 + 0.025, yf + 0.014 - EMBED, yf + 0.024, 3.01, 3.06, 'metal2')
            xe = sx * 2.47
            x0, x1 = (xe - EMBED, xe + 0.014) if sx > 0 else (xe - 0.014, xe + EMBED)
            ya, yb = sorted((sy * 1.465, sy * 1.15))
            k.dbx(x0, x1, ya, yb, 2.88, 3.19, 'metal')
    # clasp: plate on the lid, hasp plate and a toy padlock on the body
    k.dbx(-0.3, 0.3, -1.47 - 0.014, -1.47 + EMBED, 2.9, 3.18, 'metal')
    k.dbx(-0.3, 0.3, -1.35 - 0.016, -1.35 + EMBED, 2.2, 2.8, 'metal')
    k.dbx(-0.19, 0.19, -1.35 - 0.07, -1.35 - 0.016 + EMBED, 2.25, 2.62, 'tyellow')
    k.dbx(-0.025, 0.025, -1.35 - 0.075, -1.35 - 0.07 + EMBED, 2.36, 2.5, 'ink')
    for sx in (-1, 1):
        screw(k, sx * 0.22, 2.7, -1.35 - 0.016, s=0.05, c='metal2', d=0.01)
        screw(k, sx * 0.22, 3.04, -1.47 - 0.014, s=0.05, c='metal2', d=0.01)
    # back hinges: a leaf on the lid, a leaf on the body, a barrel behind the lid overhang
    for x in (-1.2, 1.2):
        k.dbx(x - 0.3, x + 0.3, 1.47 - EMBED, 1.47 + 0.016, 2.9, 3.18, 'metal')
        k.dbx(x - 0.3, x + 0.3, 1.35 - EMBED, 1.35 + 0.016, 2.3, 2.8, 'metal')
        k.dcyl((x - 0.3, 1.42, 2.83), 0.07, 0.6, 'metal2', seg=6, rot=(0, 90, 0))
        for dx in (-0.2, 0.2):
            k.dbx(x + dx - 0.025, x + dx + 0.025, 1.47 + 0.016 - EMBED, 1.47 + 0.026, 3.02, 3.07, 'metal2')
            k.dbx(x + dx - 0.025, x + dx + 0.025, 1.35 + 0.016 - EMBED, 1.35 + 0.026, 2.5, 2.55, 'metal2')


# ------------------------------------------------------------------ desk
def desk_detail(k, top):
    yf = -1.95
    edge_band(k, -3.95, 3.95, top - 0.3 + 0.07, top - 0.07, yf, 'wood3')       # banding on the front edge of the top
    # drawer fronts: routed panel lines, knob rosettes, label holders
    for (z0, z1) in ((0.3, 1.55), (1.68, 2.88), (3.0, 4.06)):
        yd = -1.82
        frame_lines(k, -3.46, -1.84, z0 + 0.14, z1 - 0.14, yd, 'white')
        zm = (z0 + z1) / 2
        disc_y(k, -2.65, zm, yd, 0.18, 'metal', d=0.02, seg=6)
    # screws holding the pedestal legs under the top, grommet in the top
    k.dcyl((3.3, 1.52, top - 0.003), 0.22, 0.018, 'ink', seg=6)       # cable grommet


# ------------------------------------------------------------------ chair
def chair_detail(k, seat):
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 1.05, sy * 1.05
            k.dbx(cx - 0.175, cx + 0.175, cy - 0.175, cy + 0.175, 0.0, 0.22, 'tyellow')     # foot cap
    for x in (-0.55, 0.0, 0.55):
        disc_y(k, x, 5.02, -1.14, 0.07, 'metal', d=0.02, seg=8)
    for sx in (-1, 1):
        disc_y(k, sx * 1.05, 5.02, -1.22, 0.07, 'metal', d=0.02, seg=8)
    # piping round the seat
    z0, z1 = seat - 0.19, seat - 0.12
    k.dbx(-1.27, 1.27, -1.32 - 0.012, -1.32 + EMBED, z0, z1, 'white')
    k.dbx(-1.27, 1.27, 1.32 - EMBED, 1.32 + 0.012, z0, z1, 'white')
    k.dbx(-1.32 - 0.012, -1.32 + EMBED, -1.27, 1.27, z0, z1, 'white')
    k.dbx(1.32 - EMBED, 1.32 + 0.012, -1.27, 1.27, z0, z1, 'white')


# ------------------------------------------------------------------ bookcase
def bookcase_detail(k, H):
    yf = -0.95
    for zs in (3.1, 5.75, 8.35):
        edge_band(k, -2.28, 2.28, zs - 0.14, zs - 0.02, yf, 'wood')
        disc_y(k, 2.365, zs - 0.08, yf, 0.055, 'trim2', d=0.018, seg=8)            # cam-lock caps on the right post
    k.dbx(-2.28 + INS, 2.28 - INS, -0.85 - 0.012, -0.85 + EMBED, 0.2, 0.24, 'wood3')   # plinth groove
    k.dbx(-2.515, 2.515, -1.0 - 0.05, -1.0 + EMBED, H - 0.24, H - 0.17, 'trim2')       # crown bead
    k.dbx(-2.515, 2.515, -1.0 - 0.022, -1.0 + EMBED, H - 0.08, H - 0.02, 'wood')
    # growth chart ticks up the left post
    for i in range(1, 11):
        z = i * 1.0
        long = (i % 3 == 0)
        k.dbx(-2.43, -2.30 if long else -2.37, yf - 0.012, yf + EMBED, z - 0.02, z + 0.02, 'tblue')


# ------------------------------------------------------------------ cube shelf
def cubeshelf_detail(k, H, bins):
    for ys, sg in ((-0.88, -1), (0.88, 1)):
        for (z0, z1) in ((2.12, 2.22), (0.03, 0.22), (H - 0.12, H - 0.02)):
            if sg < 0:
                k.dbx(-2.83 + INS, 2.83 - INS, ys - 0.014 - 0.0, ys + EMBED, z0, z1, 'wood')
            else:
                k.dbx(-2.83 + INS, 2.83 - INS, ys - EMBED, ys + 0.014, z0, z1, 'wood')
    for sg in (-1, 1):
        yf = sg * 0.9
        for x in (-2.95, -1.0, 1.0, 2.95):
            for z in (2.17, H - 0.07):
                disc_y(k, x, z, yf, 0.05, 'metal2', d=0.016, seg=6, sign=sg)
    # label holder on every bin, both sides
    for (cx, z0, c) in bins:
        for sg in (-1, 1):
            yf = sg * 0.82
            if sg < 0:
                k.dbx(cx - 0.4, cx + 0.4, yf - 0.012, yf + EMBED, z0 + 0.4, z0 + 0.7, 'white')
                k.dbx(cx - 0.28, cx + 0.28, yf - 0.019, yf - 0.012 + EMBED, z0 + 0.5, z0 + 0.6, 'tblue')
            else:
                k.dbx(cx - 0.4, cx + 0.4, yf - EMBED, yf + 0.012, z0 + 0.4, z0 + 0.7, 'white')
                k.dbx(cx - 0.28, cx + 0.28, yf + 0.012 - EMBED, yf + 0.019, z0 + 0.5, z0 + 0.6, 'tblue')


# ------------------------------------------------------------------ nightstand
def nightstand_detail(k):
    yd = -1.25
    frame_lines(k, -1.03, 1.03, 2.2, 2.75, yd, 'white', t=0.045)
    rosette(k, 0.0, 2.48, yd, 0.2, 'metal')
    edge_band(k, -1.3, 1.3, 2.88, 2.96, -1.2, 'wood')                                # banding under the top
    edge_band(k, -1.3, 1.3, 0.46, 0.53, -1.2, 'wood')
    # frame round the open cubby
    frame_lines(k, -1.17, 1.17, 0.53, 1.97, -1.2, 'wood', t=0.07, d=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.dcyl((sx * 1.05, sy * 0.95, 0.0), 0.125, 0.05, 'tyellow', seg=6)     # foot glide


# ------------------------------------------------------------------ door
def door_detail(k, WF):
    yl = WF - 0.2        # leaf plane (0.3)
    ya = WF - 0.26       # architrave plane (0.24)
    for z in (1.8, 6.2, 10.6):
        k.dbx(-2.43, -2.11, yl - 0.014, yl + EMBED, z - 0.55, z + 0.55, 'metal')
        k.dcyl((-2.45, ya - 0.0, z - 0.6), 0.06, 1.2, 'metal2', seg=6)
        for dz in (-0.35, 0.35):
            screw(k, -2.27, z + dz, yl - 0.014, s=0.06, c='metal2', d=0.01)
    # lock plate behind the knob, a keyhole and a kick plate
    k.dbx(1.62, 2.08, yl - 0.016, yl + EMBED, 5.5, 6.5, 'metal')
    k.dbx(1.82, 1.88, yl - 0.022, yl - 0.016 + EMBED, 5.62, 5.78, 'ink')
    k.dbx(-2.0, 2.0, yl - 0.02, yl + EMBED, 0.05, 0.8, 'metal2')
    for x in (-1.7, -0.6, 0.6, 1.7):
        screw(k, x, 0.425, yl - 0.02, s=0.06, c='metal', d=0.01)
    # architrave: plinth blocks at the foot and rosettes at the head corners
    for (a, b) in ((-2.95, -2.45), (2.45, 2.95)):
        k.dbx(a + INS, b - INS, ya - 0.035, ya + EMBED, 0.004, 0.95, 'trim2')
        k.dbx(a + INS, b - INS, ya - 0.035, ya + EMBED, 12.4, 12.9 - 0.005, 'trim2')
        k.dcyl(((a + b) / 2, ya - 0.005, 12.65), 0.17, 0.05, 'tyellow', seg=10, rot=(90, 0, 0))


# ------------------------------------------------------------------ window
def window_detail(k, WF):
    yf = WF - 0.25
    yg = WF - 0.13       # glass plane
    # glazing beads round the four panes
    for (z0, z1) in ((3.95, 9.85), (10.15, 12.65)):
        for (x0, x1) in ((-3.0, -0.15), (0.15, 3.0)):
            t = 0.05
            xa, xb, za, zb = x0 + 0.01, x1 - 0.01, z0 + 0.01, z1 - 0.01
            k.dbx(xa, xb, yg - 0.02, yg + EMBED, zb - t, zb, 'trim2')
            k.dbx(xa, xb, yg - 0.02, yg + EMBED, za, za + t, 'trim2')
            k.dbx(xa, xa + t, yg - 0.02, yg + EMBED, za + t, zb - t, 'trim2')
            k.dbx(xb - t, xb, yg - 0.02, yg + EMBED, za + t, zb - t, 'trim2')
    # casement handles on the centre mullion, catches on the cross bar
    for zc in (7.0, 11.4):
        k.dbx(-0.12, 0.12, yf - 0.014, yf + EMBED, zc - 0.5, zc + 0.5, 'metal')
        k.dbx(0.0, 0.55, yf - 0.06, yf - 0.014 + EMBED, zc - 0.12, zc + 0.04, 'metal2')
        screw(k, 0.0, zc + 0.36, yf - 0.014, s=0.05, c='metal2', d=0.01)
        screw(k, 0.0, zc - 0.36, yf - 0.014, s=0.05, c='metal2', d=0.01)
    for sx in (-1, 1):
        k.dbx(sx * 1.9 - 0.2, sx * 1.9 + 0.2, yf - 0.014, yf + EMBED, 9.9, 10.1, 'metal')
    # sill nosing
    k.dbx(-3.69, 3.69, -0.25 - 0.035, -0.25 + EMBED, 3.3, 3.4, 'trim2')


# ------------------------------------------------------------------ wall shelf
def wallshelf_detail(k, WF):
    yf = -0.42
    edge_band(k, -2.3, 2.3, 10.62, 10.82, yf, 'wood')
    for x in (-1.6, 1.6):
        sx = 1 if x > 0 else -1
        disc_x(k, WF - 0.004 - 0.12, 10.6 - 0.15, x + sx * 0.06, 0.05, 'metal', d=0.014, seg=6, sign=sx)
