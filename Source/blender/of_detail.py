"""kit-office modelled detail (tactical look plan Stage 11): the finish and fittings of a clean office floor, added to
the pieces the player sees most. Built on the kit_base detail helpers; every part is ink=False, at least 3 mm proud,
embedded 3 mm, and horizontal runs stop 5 mm short of the piece's sides. Faces that look toward Blender -Y sit at the
plane y = yf in the current frame (k.push(0, 0, 180) for the back face, 90 / 270 for the +X / -X faces)."""
from kit_base import PROUD, EMBED, corner_guard, cap_trim, base_trim, kick_plate


# ------------------------------------------------------------------ walls
def wall_fittings(k, yf, rail_x=(-0.495, 0.495), sockets=True):
    """skirting cap, a wall-protection rail with a steel insert, a double socket plate and a data plate"""
    k.bx(-0.485, 0.485, yf - 0.016, yf + 0.012, 0.098, 0.112, 'graphite2', ink=False)
    a, b = rail_x
    k.bx(a, b, yf - 0.018, yf + EMBED, 0.88, 0.95, 'graphite2', ink=False)
    k.bx(a + 0.01, b - 0.01, yf - 0.024, yf - 0.015, 0.905, 0.925, 'steel2', ink=False)
    if sockets:
        k.bx(-0.345, -0.255, yf - 0.008, yf + EMBED, 0.30, 0.39, 'white', ink=False)
        for x in (-0.322, -0.278):
            k.bx(x - 0.01, x + 0.01, yf - 0.012, yf - 0.005, 0.325, 0.365, 'black', ink=False)
        k.bx(0.265, 0.335, yf - 0.008, yf + EMBED, 0.30, 0.37, 'white', ink=False)
        for x in (0.287, 0.313):
            k.bx(x - 0.008, x + 0.008, yf - 0.012, yf - 0.005, 0.318, 0.352, 'black', ink=False)


def dry_fittings(k, kind):
    """both faces of a 1 m partition (the decor stays on the -Y face; the Ext cabinet leaves the rail short)"""
    if kind == 'Door':
        return door_fittings(k)
    wall_fittings(k, -0.5, rail_x=(-0.495, 0.08) if kind == 'Ext' else (-0.495, 0.495))
    k.push(0, 0, 180)
    wall_fittings(k, -0.5)
    k.pop()


def door_fittings(k):
    """office door: kick plate, hinges, backplate, closer and a head casing on both leaves"""
    for s in (-1, 1):
        k.push(0, 0, 0 if s < 0 else 180)
        yl = -0.512
        kick_plate(k, -0.4, 0.4, yl, 'steel', h=0.25)
        hx = (-0.43, -0.405) if s < 0 else (0.405, 0.43)
        for z in (0.35, 1.1, 1.85):
            k.bx(hx[0], hx[1], yl - 0.01, yl + EMBED, z - 0.05, z + 0.05, 'steelDark', ink=False)
        px = (0.29, 0.39) if s < 0 else (-0.39, -0.29)
        k.bx(px[0], px[1], yl - 0.007, yl + EMBED, 0.9, 1.1, 'steelDark', ink=False)
        k.bx(-0.2, 0.2, yl - 0.02, yl + EMBED, 2.13, 2.18, 'graphite', ink=False)
        k.bx(-0.485, 0.485, -0.533, -0.517, 2.19, 2.26, 'walnut2', ink=False)
        k.pop()


def trail_fittings(k, faces):
    """corridor slab (0.5 m, faces at x = +-0.258): faces = the signs (+1 / -1) that get the fittings"""
    for s in faces:
        k.push(0, 0, 90 if s > 0 else 270)
        wall_fittings(k, -0.258)
        k.pop()


# ------------------------------------------------------------------ curtain wall
def window_fittings(k):
    """pressure cap on the interior mullion, glazing bead, stool cap on the sill kick, head lip under the shade pocket"""
    k.bx(-0.485, -0.455, -0.512, -0.497, 0.124, 3.546, 'steelDark', ink=False)
    k.bx(-0.443, -0.428, -0.49, -0.38, 0.13, 3.545, 'graphite2', ink=False)
    k.bx(-0.435, 0.495, -0.512, -0.352, 0.117, 0.127, 'steelDark', ink=False)
    k.bx(-0.435, 0.495, -0.514, -0.497, 3.51, 3.57, 'steel2', ink=False)


def column_fittings(k):
    corner_guard(k, -0.498, -0.5, 0.124, 1.5, 'steel', w=0.06, t=0.008, side=-1)
    corner_guard(k, 0.498, -0.5, 0.124, 1.5, 'steel', w=0.06, t=0.008, side=1)
    k.bx(-0.49, 0.49, -0.52, -0.497, 3.946, 3.996, 'graphite2', ink=False)


# ------------------------------------------------------------------ cubicle pod
def cubicle_feet(k):
    """panel feet / glides along the spine and cross panels"""
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.032, s * 0.047))
        k.bx(-1.97, 1.97, y0, y1, 0.004, 0.07, 'graphite', ink=False)
        for sy in (-1, 1):
            a, b = sorted((sy * 0.06, sy * 1.97))
            k.bx(y0, y1, a, b, 0.004, 0.07, 'graphite', ink=False)


def cubicle_quad(B):
    """one cubicle in quadrant space (u along the spine, v away from it): edge banding, grommet and cable drop,
    modesty-panel seams, pedestal plinth and lock"""
    B(0.74, 1.925, 0.732, 0.744, 0.725, 0.745, 'oak2', False)          # spine desk front edge
    B(0.732, 0.744, 0.748, 1.595, 0.725, 0.745, 'oak2', False)         # return desk free edge
    B(1.35, 1.41, 0.2, 0.26, 0.747, 0.757, 'black', False)             # grommet
    B(1.37, 1.39, 0.22, 0.24, 0.56, 0.745, 'black', False)              # cable drop
    for v0, v1 in ((1.552, 1.558), (1.582, 1.588)):                    # modesty panel seams, both faces
        B(0.385, 0.395, v0, v1, 0.03, 0.7, 'graphite2', False)
        B(0.085, 0.38, v0, v1, 0.355, 0.365, 'graphite2', False)
        B(0.4, 0.695, v0, v1, 0.355, 0.365, 'graphite2', False)
    B(1.455, 1.895, 0.672, 0.69, 0.004, 0.045, 'graphite', False)      # pedestal plinth
    B(1.755, 1.775, 0.678, 0.692, 0.64, 0.66, 'brass', False)          # pedestal lock


# ------------------------------------------------------------------ bench
def bench_fittings(k):
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.697, s * 0.708))
        k.bx(-1.945, 1.945, y0, y1, 0.727, 0.744, 'oak2', ink=False)    # edge banding
        y0, y1 = sorted((s * 0.022, s * 0.031))
        k.bx(-0.006, 0.006, y0, y1, 0.78, 1.1, 'cap', ink=False)         # divider seam
        x0, x1 = sorted((s * 1.947, s * 1.958))
        k.bx(x0, x1, -0.695, 0.695, 0.727, 0.744, 'oak2', ink=False)
    k.bx(-1.75, 1.75, -0.09, 0.09, 0.58, 0.62, 'graphite', ink=False)  # cable trough under the top
    for x in (-1.6, -0.55, 0.55, 1.6):
        k.bx(x - 0.015, x + 0.015, -0.04, 0.04, 0.615, 0.725, 'graphite', ink=False)
    for x in (-0.95, 0.95):
        for sy in (-1, 1):
            a, b = sorted((sy * 0.27, sy * 0.33))
            k.bx(x + 0.3, x + 0.36, a, b, 0.747, 0.757, 'black', ink=False)   # grommets


# ------------------------------------------------------------------ meeting room
def meeting_fittings(k, tab_band, apron, GY, xs, doors):
    for side, sy in (('S', -1), ('N', 1)):
        for x in xs[side]:
            for f in (-1, 1):
                y0, y1 = sorted((sy * GY + f * 0.037, sy * GY + f * 0.048))
                k.bx(x - 0.012, x + 0.012, y0, y1, 0.08, 3.8, 'steelDark', ink=False)
        d0, d1 = doors[side]
        k.bx(d0 + 0.03, d1 - 0.03, sy * GY - 0.05, sy * GY + 0.05, 3.84, 3.99, 'graphite', ink=False)  # door head
    k.bx(-1.95, 1.95, -0.55, 0.55, 0.69, 0.725, apron, ink=False)       # table apron
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.597, s * 0.608))
        k.bx(-1.995, 1.995, y0, y1, 0.725, 0.755, tab_band, ink=False)
        x0, x1 = sorted((s * 1.997, s * 2.008))
        k.bx(x0, x1, -0.595, 0.595, 0.725, 0.755, tab_band, ink=False)
    for x in (-1.45, 1.45):                                            # power / data flip covers
        k.bx(x - 0.07, x + 0.07, -0.08, 0.08, 0.757, 0.768, 'steelDark', ink=False)
        k.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.765, 0.772, 'black', ink=False)
    for y in (-0.317, 0.317):                                          # credenza door seams, pulls, plinth
        k.bx(-3.353, -3.347, y - 0.004, y + 0.004, 0.06, 0.68, 'graphite', ink=False)
    for y in (-0.38, -0.25, 0.25, 0.38):
        k.bx(-3.362, -3.347, y - 0.008, y + 0.008, 0.42, 0.6, 'steel', ink=False)
    k.bx(-3.362, -3.347, -0.945, 0.945, 0.004, 0.05, 'graphite', ink=False)


# ------------------------------------------------------------------ executive set
def exec_fittings(k, srt):
    for f in (-1, 1):
        y0, y1 = srt(f * 0.417, f * 0.428)
        k.bx(-0.895, 0.895, y0, y1, 0.725, 0.765, 'walnut2', ink=False)  # desk edge banding
    k.bx(0.4, 0.8, -0.28, 0.38, 0.04, 0.70, 'walnut2', ink=False)        # drawer pedestal under the top
    for z0, z1 in ((0.07, 0.25), (0.27, 0.45), (0.47, 0.67)):
        k.qy(0.42, 0.78, z0, z1, 0.383, 1, 'walnut')
        k.bx(0.55, 0.65, 0.377, 0.392, z1 - 0.08, z1 - 0.055, 'brass', ink=False)
    for i in range(4):                                                   # credenza pulls
        x0 = -1.27 + i * 0.64
        k.bx(x0 + 0.24, x0 + 0.36, 1.083, 1.103, 0.6, 0.625, 'brass', ink=False)
    kick_plate(k, -1.29, 1.29, 1.1, 'graphite', h=0.05)


# ------------------------------------------------------------------ reception
def reception_fittings(k):
    k.bx(-2.395, 2.395, -0.612, -0.597, 1.05, 1.085, 'brass', ink=False)       # brass band under the ledge
    k.bx(-2.595, 2.595, -0.727, -0.717, 1.12, 1.14, 'brass', ink=False)       # stone ledge inlay
    base_trim(k, -2.8, 2.8, 1.2, 'graphite', h=0.09, d=0.018)                  # feature wall skirting
    for x in (-0.5, 0.5):                                                      # staff desk grommets
        k.bx(x - 0.03, x + 0.03, -0.23, -0.17, 0.747, 0.757, 'black', ink=False)


# ------------------------------------------------------------------ lift doors
def lift_fittings(k):
    for f in (-1, 1):
        y0, y1 = sorted((f * 2.997, f * 3.009))
        for cx in (-3.5, 0.0, 3.5):
            for xa, xb in ((cx - 0.73, cx - 0.02), (cx + 0.02, cx + 0.73)):
                for za, zb in ((0.9, 0.94), (1.95, 1.99)):
                    k.bx(xa, xb, y0, y1, za, zb, 'steelDark', ink=False)


# ------------------------------------------------------------------ cabinets, counters
def file_fittings(k):
    for i in range(3):
        z0 = 0.07 + i * 0.31
        for xa, xb in ((-0.335, -0.325), (-0.215, -0.205)):
            k.bx(xa, xb, -0.292, -0.277, z0 + 0.175, z0 + 0.265, 'steel', ink=False)
        k.bx(-0.325, -0.215, -0.292, -0.277, z0 + 0.175, z0 + 0.185, 'steel', ink=False)
        k.bx(-0.325, -0.215, -0.292, -0.277, z0 + 0.255, z0 + 0.265, 'steel', ink=False)
    k.bx(0.27, 0.33, -0.292, -0.277, 0.07 + 0.62 + 0.2, 0.07 + 0.62 + 0.26, 'steelDark', ink=False)  # lock


def tall_fittings(k):
    kick_plate(k, -0.46, 0.46, -0.27, 'graphite', h=0.055)
    for sx in (-1, 1):
        a, b = sorted((sx * 0.45, sx * 0.47))
        for z in (0.25, 0.9, 1.6):
            k.bx(a, b, -0.282, -0.267, z - 0.05, z + 0.05, 'steelDark', ink=False)


def counter_fittings(k):
    k.bx(-0.495, 0.495, -0.328, -0.317, 0.91, 0.93, 'steel2', ink=False)      # bullnose edge trim
    for sx in (-1, 1):
        a, b = sorted((sx * 0.455, sx * 0.475))
        for z in (0.3, 0.7):
            k.bx(a, b, -0.282, -0.267, z - 0.04, z + 0.04, 'steelDark', ink=False)
