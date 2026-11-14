"""kit-smallcity modelled detail (tactical look plan Stage 11): the street-level fittings a player sees up close.

Shopfronts (Win / Door / Pier modules): plinths, bulkhead mouldings, glazing bars and frame depth, door kick plates,
pull handles, panel mouldings, thresholds, lintels, buzzer plates, drainpipes on straps, meter boxes with conduit,
vents; brick facades: sills with corbels, keystones, glazing bars, dentils, wall-tie plates, air bricks.
Street props: lamp posts, hydrant, bench, bin, mailbox, news boxes, bus shelter (base plates, bolts, hatches).

Same rules as every detail pass: all parts are hull='none' (no outline shell), stand at least 3 mm proud and sink
3 mm into whatever they sit on, horizontal runs stop 5 mm short of the module sides. Nothing here changes a piece's
origin, footprint, collision boxes or the parts already drawn: it only adds shapes. The facade plane is y = -0.5.
"""
import math

EMB = 0.003
G_H, U_H = 3.6, 3.0
PANEL = 0.025     # shop panel front, proud of the facade plane
FASCIA = 0.1      # fascia sign board front
HX = 0.495        # horizontal runs stop 5 mm short of the module's sides


def F(d):
    return -0.5 - d


def fb(m, x0, x1, d, z0, z1, c, d0=0.0, cull=''):
    """facade fitting: front d proud of the facade plane, back sunk EMB into a surface standing d0 proud"""
    c_ = 'k' + ('b' if z0 < 1.0 else '') + ('t' if z1 > 5.0 else '') + cull
    m.bx(x0, x1, F(d), F(d0) + EMB, z0, z1, c, hull='none', cull=c_)


def box(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def frame(m, x0, x1, z0, z1, d, t, c, d0=0.0):
    """four bars round an opening, non-overlapping (sides full height, top and bottom between them)"""
    fb(m, x0, x0 + t, d, z0, z1, c, d0)
    fb(m, x1 - t, x1, d, z0, z1, c, d0)
    fb(m, x0 + t, x1 - t, d, z0, z0 + t, c, d0)
    fb(m, x0 + t, x1 - t, d, z1 - t, z1, c, d0)


# ================================================================ facade modules
def upper_floors(m, kind, n, trim):
    if kind == 'Pier':
        return
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        fb(m, -0.34, 0.34, 0.085, z0 + 0.69, z0 + 0.735, trim)                   # projecting stone sill
        for sx in (-1, 1):                                                         # corbels under it
            fb(m, sx * 0.30 - 0.02, sx * 0.30 + 0.02, 0.07, z0 + 0.60, z0 + 0.69, trim)
        fb(m, -0.008, 0.008, 0.047, z0 + 0.772, z0 + 2.288, 'frameW', 0.03)      # centre glazing bar
        fb(m, -0.05, 0.05, 0.07, z0 + 2.33, z0 + 2.58, trim)                      # keystone over the lintel


def dentils(m, T, trim):
    for i in range(6):
        x = -0.4167 + i * 0.1667
        fb(m, x - 0.04, x + 0.04, 0.07, T - 0.06, T + EMB, trim, cull='t')


def drainpipe(m, x, T, strap_c, pipe_c):
    r = 0.035
    m.cy((x, F(0.09), 0.062), r, r, T - 0.1 - 0.062, pipe_c, seg=8, hull='none')
    for z, d0 in ((0.6, PANEL), (1.8, PANEL), (2.5, PANEL), (3.15, FASCIA)):
        fb(m, x - r - 0.012, x + r + 0.012, 0.135, z - 0.016, z + 0.016, strap_c, d0)
    z = G_H + 1.5
    while z < T - 0.4:
        fb(m, x - r - 0.012, x + r + 0.012, 0.135, z - 0.016, z + 0.016, strap_c)
        z += U_H
    fb(m, x - r - 0.01, x + r + 0.01, 0.165, 0.062, 0.17, strap_c, PANEL)      # shoe at the foot
    fb(m, x - 0.06, x + 0.06, 0.15, T - 0.3, T - 0.04, strap_c)                 # hopper head under the cornice


def win_detail(m, trim, n, si):
    fb(m, -HX, HX, 0.05, 0.06, 0.22, 'concD', PANEL)                             # stone plinth
    frame(m, -0.4, 0.4, 0.27, 0.44, 0.04, 0.02, 'frameW', PANEL)                 # bulkhead panel moulding
    for sx in (-1, 1):                                                           # corbels under the window sill
        fb(m, sx * 0.335 - 0.025, sx * 0.335 + 0.025, 0.07, 0.40, 0.5, 'stoneC', PANEL)
    frame(m, -0.405, 0.405, 0.585, 2.735, 0.062, 0.025, 'frameW', 0.04)          # window frame standing proud of the surround
    fb(m, -0.38, 0.38, 0.062, 1.99, 2.03, 'frameW', 0.05)                        # transom bar
    fb(m, -0.01, 0.01, 0.066, 0.61, 1.99, 'frameW', 0.05)                        # mullion
    fb(m, -0.01, 0.01, 0.066, 2.03, 2.71, 'frameW', 0.05)
    fb(m, -0.22, 0.22, 0.056, 1.5, 1.57, 'awnCream', 0.05)                       # gold-leaf lettering on the glass
    for x0, x1 in ((-0.34, -0.06), (0.0, 0.34)):                                  # fascia lettering
        fb(m, x0, x1, 0.106, 3.1, 3.24, 'awnCream', FASCIA)
    fb(m, -0.3, 0.3, 0.106, 2.96, 3.0, 'awnCream', FASCIA)


def door_detail(m, trim, n, si):
    for sx in (-1, 1):
        fb(m, min(sx * 0.375, sx * HX), max(sx * 0.375, sx * HX), 0.05, 0.06, 0.22, 'concD', PANEL)   # plinth beside the door
    fb(m, -0.3, 0.3, 0.058, 0.02, 0.25, 'gold', 0.05)                            # brass kick plate
    frame(m, -0.26, 0.26, 0.34, 0.9, 0.058, 0.02, 'woodL', 0.05)                 # raised lower panel
    fb(m, -0.008, 0.008, 0.066, 1.008, 2.042, 'wood', 0.058)                        # door glass: mullion and rail
    fb(m, -0.242, 0.242, 0.062, 1.5, 1.53, 'wood', 0.058)
    fb(m, 0.278, 0.292, 0.066, 0.89, 0.91, 'gold', 0.05)                          # pull handle on two stand-offs
    fb(m, 0.278, 0.292, 0.066, 1.29, 1.31, 'gold', 0.05)
    fb(m, 0.275, 0.295, 0.075, 0.88, 1.32, 'gold', 0.06)
    fb(m, -0.34, 0.34, 0.08, 0.0, 0.055, 'steelD', 0.05)                          # threshold plate
    for sx in (-1, 1):                                                           # transom bars
        fb(m, sx * 0.11 - 0.008, sx * 0.11 + 0.008, 0.058, 2.248, 2.572, 'frameW', 0.05)
    fb(m, -0.43, 0.43, 0.07, 2.62, 2.72, 'stoneC', PANEL)                        # stone lintel over the surround
    fb(m, 0.405, 0.47, 0.04, 1.1, 1.34, 'steelD', PANEL)                          # buzzer plate
    fb(m, 0.425, 0.45, 0.048, 1.2, 1.24, 'lamp', 0.04)
    fb(m, 0.425, 0.45, 0.048, 1.12, 1.16, 'ink', 0.04)


def pier_detail(m, trim, n, si):
    T = G_H + (n - 1) * U_H
    sx = 1 if si % 2 == 0 else -1
    fb(m, -HX, HX, 0.05, 0.06, 0.22, 'concD', PANEL)
    drainpipe(m, sx * 0.42, T, 'ironL', 'iron')
    bx = -sx * 0.3                                                                 # meter box with lid, handle, conduit
    fb(m, bx - 0.12, bx + 0.12, 0.1, 0.95, 1.25, 'steelD', PANEL)
    fb(m, bx - 0.1, bx + 0.1, 0.106, 0.97, 1.23, 'steel', 0.099)
    fb(m, bx + 0.07, bx + 0.09, 0.116, 1.05, 1.15, 'chrome', 0.105)
    m.cy((bx, F(0.035), 1.25), 0.014, 0.014, 0.8, 'ironL', seg=5, hull='none')
    for z in (1.45, 1.85):
        fb(m, bx - 0.024, bx + 0.024, 0.056, z - 0.012, z + 0.012, 'iron', PANEL)
    fb(m, bx - 0.05, bx + 0.05, 0.07, 2.05, 2.15, 'steelD', PANEL)                # elbow box where it enters the wall
    vx = 0.02                                                                      # louvred vent low on the panel
    fb(m, vx - 0.145, vx + 0.145, 0.036, 0.503, 0.697, 'ink', PANEL)
    fb(m, vx - 0.15, vx + 0.15, 0.05, 0.5, 0.525, 'iron', PANEL)
    fb(m, vx - 0.15, vx + 0.15, 0.05, 0.675, 0.7, 'iron', PANEL)
    for i in range(3):
        z = 0.555 + i * 0.045
        fb(m, vx - 0.13, vx + 0.13, 0.045, z, z + 0.014, 'ironL', 0.03)
    fb(m, -0.07 + vx, 0.07 + vx, 0.034, 1.8, 1.96, 'shopNavy', PANEL)             # house number plate
    fb(m, -0.04 + vx, 0.04 + vx, 0.04, 1.85, 1.91, 'paintW', 0.03)
    for k in range(1, n):                                                          # wall-tie plates on the upper brick
        z = G_H + 1.1 + (k - 1) * U_H
        for x in (-0.28, 0.28):
            if abs(x - sx * 0.42) > 0.15:
                fb(m, x - 0.045, x + 0.045, 0.025, z - 0.045, z + 0.045, 'iron')
    fb(m, -0.15 + vx, 0.15 + vx, 0.02, G_H + 1.7, G_H + 1.9, 'ink')              # air brick
    for i in range(3):
        z = G_H + 1.73 + i * 0.055
        fb(m, -0.13 + vx, 0.13 + vx, 0.032, z, z + 0.022, 'stoneB', 0.015)


def wall_detail(m, kind, trim, n, si):
    T = G_H + (n - 1) * U_H
    upper_floors(m, kind, n, trim)
    dentils(m, T, trim)
    {'Win': win_detail, 'Door': door_detail, 'Pier': pier_detail}[kind](m, trim, n, si)


# ================================================================ street props
def lamp_detail(m):
    m.cy((0, 0, 0.047), 0.26, 0.26, 0.03, 'ironL', seg=6, hull='none')            # base flange with four nuts
    for a in range(4):
        x, y = math.cos(a * 1.5708 + 0.7854) * 0.2, math.sin(a * 1.5708 + 0.7854) * 0.2
        m.cy((x, y, 0.074), 0.022, 0.018, 0.03, 'iron', seg=6, hull='none')
    box(m, -0.05, 0.05, -0.165, -0.105, 0.14, 0.36, 'ironL')                       # hand-hole door
    box(m, -0.035, 0.035, -0.171, -0.162, 0.17, 0.33, 'iron')
    box(m, -0.012, 0.012, -0.18, -0.168, 0.24, 0.27, 'chrome')
    for z in (1.3, 3.2):
        m.cy((0, 0, z), 0.075, 0.075, 0.05, 'ironL', seg=6, hull='none')
    box(m, -0.2, 0.2, -0.075, -0.062, 3.3, 3.46, 'shopNavy')                       # street-name blade on two clamps
    box(m, -0.14, 0.14, -0.0785, -0.0715, 3.36, 3.4, 'paintW')
    for z in (3.31, 3.41):
        box(m, -0.012, 0.012, -0.07, -0.03, z, z + 0.04, 'ironL')


def hydrant_detail(m):
    for a in range(4):                                                              # bolts on the base flange
        x, y = math.cos(a * 1.5708 + 0.7854) * 0.14, math.sin(a * 1.5708 + 0.7854) * 0.14
        m.cy((x, y, 0.117), 0.014, 0.012, 0.025, 'ironL', seg=6, hull='none')
    m.cy((0, 0, 0.24), 0.123, 0.123, 0.02, 'paintY', seg=10, hull='none')           # painted band
    for x in (0.197, -0.227):                                                       # outlet caps with nuts
        m.cy((x, 0, 0.42), 0.062, 0.062, 0.03, 'ironL', seg=8, rot=(0, 90, 0), hull='none')
    m.cy((0.227, 0, 0.42), 0.02, 0.02, 0.025, 'iron', seg=6, rot=(0, 90, 0), hull='none')
    m.cy((-0.252, 0, 0.42), 0.02, 0.02, 0.025, 'iron', seg=6, rot=(0, 90, 0), hull='none')
    m.cy((0, -0.22, 0.38), 0.035, 0.035, 0.02, 'ironL', seg=6, rot=(90, 0, 0), hull='none')   # pumper cap nut


def bench_detail(m):
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.76, sx * 0.92))
        box(m, x0, x1, -0.30, 0.27, 0.047, 0.062, 'iron', 'b')                      # floor plate under each end
        for bxc in (sx * 0.785, sx * 0.895):
            for byc in (-0.283, 0.247):
                box(m, bxc - 0.013, bxc + 0.013, byc - 0.013, byc + 0.013, 0.059, 0.075, 'ironL', 'b')
        for y in (-0.2, -0.06, 0.08):                                               # bolts on the seat slats
            box(m, sx * 0.84 - 0.013, sx * 0.84 + 0.013, y - 0.013, y + 0.013, 0.467, 0.482, 'ironL', 'b')
        for z in (0.66, 0.84):                                                      # and on the backrest slats
            box(m, sx * 0.84 - 0.013, sx * 0.84 + 0.013, 0.109, 0.123, z - 0.013, z + 0.013, 'ironL', 'k')
    box(m, -0.803, 0.803, -0.1, -0.06, 0.27, 0.31, 'iron')                           # cross brace under the seat
    box(m, -0.1, 0.1, 0.109, 0.123, 0.83, 0.85, 'gold', 'k')                         # memorial plaque
    for sx in (-1, 1):
        box(m, sx * 0.11 - 0.006, sx * 0.11 + 0.006, 0.105, 0.123, 0.835, 0.845, 'gold', 'k')


def bin_detail(m):
    m.cy((0, 0, 0.047), 0.28, 0.28, 0.045, 'ironL', seg=12, hull='none')            # base ring
    for z in (0.22, 0.66):                                                          # rivets on the bands
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)):
            x, y = sx * 0.27, sy * 0.27
            box(m, x - 0.012, x + 0.012, y - 0.012, y + 0.012, z - 0.012, z + 0.012, 'iron')
    box(m, -0.1, 0.1, -0.282, -0.24, 0.3, 0.5, 'ironL')                              # service hatch
    box(m, -0.05, 0.05, -0.287, -0.28, 0.38, 0.42, 'ink')
    box(m, -0.018, 0.018, -0.292, -0.285, 0.455, 0.485, 'chrome')
    m.cy((0.17, 0, 0.947), 0.055, 0.055, 0.03, 'ironL', seg=8, hull='none')         # ash tray on the lid
    m.cy((-0.17, 0, 0.947), 0.04, 0.04, 0.02, 'ironL', seg=6, hull='none')


def mailbox_detail(m):
    for sx in (-1, 1):
        for y0, y1 in ((-0.28, -0.18), (0.18, 0.28)):
            x0, x1 = sorted((sx * 0.16, sx * 0.28))
            box(m, x0, x1, y0, y1, 0.047, 0.062, 'iron', 'b')
            xb = sx * 0.255
            yb = (y0 + y1) / 2
            box(m, xb - 0.013, xb + 0.013, yb - 0.013, yb + 0.013, 0.059, 0.075, 'ironL', 'b')
    box(m, -0.2, -0.185, -0.268, -0.257, 0.34, 0.76, 'ironL', 'k')                   # pull-down door outline
    box(m, 0.185, 0.2, -0.268, -0.257, 0.34, 0.76, 'ironL', 'k')
    box(m, -0.185, 0.185, -0.268, -0.257, 0.34, 0.355, 'ironL', 'k')
    box(m, -0.185, 0.185, -0.268, -0.257, 0.745, 0.76, 'ironL', 'k')
    box(m, -0.16, 0.16, -0.285, -0.25, 0.915, 0.94, 'ironL', 'k')                    # rain hood over the slot


def newsbox_detail(m):
    for cx in (-0.23, 0.23):
        box(m, cx - 0.1, cx + 0.1, -0.1, 0.1, 0.047, 0.062, 'iron', 'b')
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(m, cx + sx * 0.08 - 0.012, cx + sx * 0.08 + 0.012, sy * 0.08 - 0.012, sy * 0.08 + 0.012, 0.059, 0.074, 'ironL', 'b')
        box(m, cx - 0.16, cx - 0.04, -0.2155, -0.187, 0.5, 0.53, 'chrome', 'k')       # pull handle
        box(m, cx - 0.12, cx + 0.12, -0.196, -0.187, 0.405, 0.45, 'paintW', 'k')      # price label


def shelter_detail(m):
    for y in (-1.86, 1.86):
        for x in (0.86, -0.3):
            box(m, x - 0.085, x + 0.085, y - 0.085, y + 0.085, 0.047, 0.061, 'iron', 'b')   # post base plates
            for sx in (-1, 1):
                for sy in (-1, 1):
                    xb, yb = x + sx * 0.065, y + sy * 0.065
                    box(m, xb - 0.011, xb + 0.011, yb - 0.011, yb + 0.011, 0.058, 0.073, 'steel', 'b')
    for y in (-1.2, -0.4, 0.4, 1.2):                                                # spider clamps on the back glass
        for z in (0.45, 2.05):
            box(m, 0.797, 0.833, y - 0.035, y + 0.035, z - 0.035, z + 0.035, 'steel')
    for x0, x1, z0, z1 in ((-0.24, -0.2, 0.26, 2.24), (0.76, 0.8, 0.26, 2.24), (-0.2, 0.76, 2.18, 2.23), (-0.2, 0.76, 0.27, 0.32)):
        box(m, x0, x1, 1.752, 1.783, z0, z1, 'ironL', 'k')                           # poster frame
    for y in (-1.86, 1.86):                                                         # downspouts and clips on the back posts
        m.cy((0.915, y, 0.2), 0.015, 0.015, 2.15, 'ironL', seg=6, hull='none')
        for z in (0.5, 1.4, 2.2):
            box(m, 0.895, 0.935, y - 0.022, y + 0.022, z - 0.012, z + 0.012, 'iron')
