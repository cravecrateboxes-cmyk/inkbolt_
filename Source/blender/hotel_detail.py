"""INKBOLT kit-hotel: modelled-detail helpers (tactical look, Stage 11). Finish and fittings, not wear: mouldings,
brass bands and plates, piping, ferrules, collars.

Every part is ink=False (no outline shell), stands at least 3 mm proud of whatever it sits on and starts 3 mm inside
it (EM), and horizontal runs stop 5 mm short of a piece's sides, so ib_lib.check_zfight stays clean. Faces are the
wall modules' (looking toward Blender -Y at the plane y, `s` = -1) unless a helper says otherwise.
"""
import math

EM = 0.003
IN = 0.005


def _yy(y, s, d):
    """(y0, y1) of a part standing d proud of the face at y that looks toward s * Y, 3 mm embedded in it."""
    a, b = y - s * EM, y + s * d
    return (a, b) if a < b else (b, a)


def pframe(k, x0, x1, z0, z1, y, c, t=0.016, d=0.012, s=-1):
    """A rectangular picture-frame moulding (outer rect x0..x1 / z0..z1) standing d proud of the face at y."""
    ya, yb = _yy(y, s, d)
    k.bx(x0, x1, ya, yb, z1 - t, z1, c, ink=False)
    k.bx(x0, x1, ya, yb, z0, z0 + t, c, ink=False)
    k.bx(x0, x0 + t, ya, yb, z0 + t + 0.004, z1 - t - 0.004, c, ink=False)
    k.bx(x1 - t, x1, ya, yb, z0 + t + 0.004, z1 - t - 0.004, c, ink=False)


def strip(k, x0, x1, z0, z1, y, c, d=0.012, s=-1):
    """A horizontal moulding run, ends inset 5 mm from the piece's sides."""
    ya, yb = _yy(y, s, d)
    k.bx(x0 + IN, x1 - IN, ya, yb, z0, z1, c, ink=False)


def ferrule(k, x, y, w, c='brass', h=0.026, z0=0.004):
    """A brass sabot on a square leg (w = leg width): 3 mm proud all round."""
    e = w / 2 + 0.003
    k.bx(x - e, x + e, y - e, y + e, z0, z0 + h, c, ink=False)


def ferrule_r(k, x, y, r, c='brass', h=0.03, z0=0.004):
    """A brass sabot on a round leg of radius r at its foot."""
    k.cyl(x, y, z0, r + 0.008, r + 0.006, h, c, seg=6, ink=False)


def collar(k, x, y, z, r, c='brass', h=0.022, seg=6):
    k.cyl(x, y, z, r, r, h, c, seg=seg, ink=False)


def dentils(k, x0, x1, z0, z1, y, c, n, w=0.05, d=0.024, s=-1):
    """A row of n dentil blocks between x0 and x1."""
    ya, yb = _yy(y, s, d)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        k.bx(x - w / 2, x + w / 2, ya, yb, z0, z1, c, ink=False)


def piping_x(k, x0, x1, y, z, c='gold', t=0.014, d=0.014, s=-1):
    """A piping cord along x on a face at y (the seam of a cushion, a trim): section t high, d proud."""
    ya, yb = _yy(y, s, d)
    k.bx(x0, x1, ya, yb, z - t / 2, z + t / 2, c, ink=False)


def piping_y(k, y0, y1, x, z, c='gold', t=0.014, d=0.014, s=1):
    """A piping cord along y on a face at x looking toward s * X."""
    xa, xb = _yy(x, s, d)
    k.bx(xa, xb, y0, y1, z - t / 2, z + t / 2, c, ink=False)


# ================================================================ wall modules
def wall_face_detail(k, y, dz, kind):
    """The six-piece wall family's shared face (face at y, looking toward -Y): skirting with a moulded cap, wainscot
    panel mouldings, dado cove and cap, cornice crown with dentils, a sconce backplate. dz lifts the bands of the _V
    modules (see hotel_struct.panel_face)."""
    from hotel_base import H
    # skirting board and its cap moulding (the walnut wainscot front stands 4 cm proud of y)
    k.bx(-0.495, 0.495, y - 0.064, y - 0.037, dz + 0.004, dz + 0.135, 'walnut2', ink=False)
    k.bx(-0.495, 0.495, y - 0.052, y - 0.037, dz + 0.135, dz + 0.152, 'gold', ink=False)
    # wainscot panels: a raised bolection frame round each recessed panel
    for (x0, x1) in ((-0.44, -0.04), (0.04, 0.44)):
        pframe(k, x0, x1, dz + 0.16, dz + 0.88, y - 0.037, 'walnut', t=0.02, d=0.016)
    # dado cove under the rail and a cap moulding over it
    k.bx(-0.495, 0.495, y - 0.047, y - 0.037, dz + 0.97, dz + 1.003, 'walnut2', ink=False)
    k.bx(-0.495, 0.495, y - 0.062, y + EM, dz + 1.047, dz + 1.078, 'walnut', ink=False)
    # cornice: dentils under a projecting crown
    dentils(k, -0.4, 0.4, H - 0.2 - dz, H - 0.115 - dz, y - 0.077, 'stone', 9, w=0.05, d=0.023)
    k.bx(-0.495, 0.495, y - 0.13, y + EM, H - 0.12 - dz, H - 0.01 - dz, 'stone', ink=False)
    k.bx(-0.495, 0.495, y - 0.13 - 0.0, y - 0.1, H - 0.135 - dz, H - 0.12 - dz, 'gold', ink=False)
    if kind == 'Sconce':
        for z in (2.6, 6.7):
            sconce_plate(k, 0, y - 0.003, z)


def sconce_plate(k, x, y, z, s=-1):
    """A bronze backplate with a gilt boss behind a sconce (y = the sconce's own plane)."""
    ya, yb = _yy(y, s, 0.012)
    k.bx(x - 0.11, x + 0.11, ya, yb, z - 0.27, z + 0.2, 'bronze', ink=False)
    ya2, yb2 = _yy(y + s * 0.012, s, 0.006)
    k.bx(x - 0.085, x + 0.085, ya2, yb2, z - 0.24, z - 0.2, 'gold', ink=False)
    k.bx(x - 0.085, x + 0.085, ya2, yb2, z + 0.16, z + 0.17, 'gold', ink=False)


def arch_architrave(k, ox, az, r0, r1, a0, a1, n, y0=-0.55, y1=-0.497, c='stone2', lim=0.495):
    """A moulded band (radii r0..r1) round an arch on the room face, clipped to the cell (|x| <= lim)."""
    def p(r, a):
        return (max(-lim, min(lim, ox + math.cos(a) * r)), az + math.sin(a) * r)
    for i in range(n):
        b0, b1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        pts = [p(r0, b0), p(r0, b1), p(r1, b1), p(r1, b0)]
        k.prism(pts, y0, y1, c, ink=False)


def window_sill(k):
    """A deep marble stool on the plinth of a window cell and a brass nosing along its edge."""
    k.bx(-0.495, 0.495, -0.585, -0.06, 0.547, 0.6, 'marble', ink=False)
    k.bx(-0.49, 0.49, -0.595, -0.58, 0.557, 0.583, 'brass', ink=False)


def pier_detail(k):
    """win_pier: plinth cap, shaft base torus, an astragal bead and abacus under the cornice, capital volutes."""
    from hotel_base import H
    k.bx(-0.375, 0.375, -0.595, -0.49, 0.66, 0.705, 'stone', ink=False)
    k.bx(-0.32, 0.32, -0.575, -0.485, 0.703, 0.76, 'marble2', ink=False)
    k.bx(-0.31, 0.31, -0.585, -0.48, H - 0.985, H - 0.947, 'gold', ink=False)
    k.bx(-0.4, 0.4, -0.635, -0.475, H - 0.603, H - 0.55, 'brass', ink=False)
    for sx in (-1, 1):
        k.sph(sx * 0.33, -0.63, H - 0.72, 0.055, 'gold', seg=(5, 3), ink=False)


def core_bands(k):
    """core: brass fillets round the four-sided block (flush with its plinth and cornice, 3 mm proud of the shaft)."""
    from hotel_base import H
    for (z0, z1) in ((0.2, 0.225), (0.97, 0.995), (H - 0.38, H - 0.35)):
        k.bx(-0.5, 0.5, -0.5, 0.5, z0, z1, 'brass', ink=False)


# ================================================================ lifts, doors
def lift_fittings(k, y, c_, s_):
    """One face of a lift cell: plinth blocks and a brass cap on the architrave, a brass threshold and (on the
    right-hand side only) a call-button plate with two buttons."""
    ax_in, ax_out = c_ - s_ * 0.7, c_ - s_ * 0.86
    lo, hi = sorted((ax_in + s_ * 0.012, ax_out - s_ * 0.012))
    k.bx(lo, hi, y - 0.1, y + 0.012, 0.004, 0.16, 'nero2', ink=False)
    k.bx(lo, hi, y - 0.092, y + 0.018, 0.16, 0.19, 'brass', ink=False)
    h0, h1 = sorted((c_ * 0.98, ax_out - s_ * 0.015))
    k.bx(h0, h1, y - 0.096, y + 0.012, 2.747, 2.79, 'brass', ink=False)
    t0, t1 = sorted((c_ * 0.98, c_ - s_ * 0.66))
    k.bx(t0, t1, y - 0.07, y + 0.012, 0.004, 0.016, 'brass', ink=False)
    if s_ > 0:
        px = -0.435 * s_
        k.bx(px - 0.045, px + 0.045, y - 0.013, y + 0.012, 0.95, 1.25, 'brass', ink=False)
        for z in (1.08, 1.14):
            k.bx(px - 0.015, px + 0.015, y - 0.023, y - 0.01, z - 0.015, z + 0.015, 'lamp', ink=False)


def doorway_fittings(k, part, lintel):
    """doorway: a brass bead capping the head architrave, plinth blocks with brass caps on a jamb, rosettes."""
    for f in (-1, 1):
        yh = f * 0.497
        h0, h1 = sorted((yh + f * 0.077, yh + f * 0.095))
        k.bx(-0.48, 0.48, h0, h1, lintel + 0.17, lintel + 0.2, 'brass', ink=False)
    for (side, xs) in (('L', -1), ('R', 1)):
        if part == side:
            x0, x1 = sorted((xs * 0.49, xs * 0.345))
            k.bx(x0, x1, -0.597, 0.597, 0.004, 0.2, 'nero2', ink=False)
            k.bx(x0, x1, -0.597, 0.597, 0.2, 0.23, 'brass', ink=False)
            for f in (-1, 1):
                _rosette(k, xs * 0.427, f * 0.6, lintel + 0.1, 0.05, f)


def _rosette(k, x, y, z, r, f, n=8):
    k.poly([(x + math.cos(i / n * math.tau) * r, y + f * 0.003, z + math.sin(i / n * math.tau) * r) for i in range(n)],
           'brass', (0, f, 0))


# ================================================================ columns, balustrades, stair
def column_detail(k, h):
    """Column_Lo / Hi: plinth cap, brass torus over the base cone, brass bands at the foot and neck of the shaft,
    a brass ring on the capital and a gilt ring under the abacus (everything inside the existing plan)."""
    k.bx(-0.428, 0.428, -0.428, 0.428, 0.262, 0.305, 'nero2', ink=False)
    k.cyl(0, 0, 0.309, 0.375, 0.37, 0.034, 'brass', seg=12, ink=False)
    k.cyl(0, 0, 0.455, 0.292, 0.292, 0.034, 'brass', seg=12, ink=False)
    k.cyl(0, 0, h - 0.665, 0.262, 0.262, 0.04, 'brass', seg=12, ink=False)
    k.cyl(0, 0, h - 0.36, 0.348, 0.346, 0.04, 'brass', seg=12, ink=False)
    k.cyl(0, 0, h - 0.19, 0.412, 0.41, 0.043, 'gold', seg=12, ink=False)


def post_detail(k):
    """RailPost: base moulding, raised panels on the shaft, a brass band and a collar under the gilt ball."""
    k.bx(-0.108, 0.108, -0.108, 0.108, 0.008, 0.09, 'marble2', ink=False)
    for s in (-1, 1):
        k.bx(min(s * 0.097, s * 0.106), max(s * 0.097, s * 0.106), -0.05, 0.05, 0.24, 0.84, 'marble2', ink=False)
        k.bx(-0.05, 0.05, min(s * 0.097, s * 0.106), max(s * 0.097, s * 0.106), 0.24, 0.84, 'marble2', ink=False)
    k.bx(-0.108, 0.108, -0.108, 0.108, 0.9, 0.93, 'brass', ink=False)
    k.cyl(0, 0, 1.074, 0.085, 0.07, 0.03, 'brass', seg=8, ink=False)


def rail_detail(k, y0, y1):
    """Balustrade run: brass collars on every baluster at its foot, waist and head, a brass inlay on the rail."""
    n = max(1, int(round((y1 - y0) / 0.16)))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        collar(k, 0, y, 0.145, 0.05, h=0.02)
        collar(k, 0, y, 0.52, 0.062, h=0.03)
        collar(k, 0, y, 0.9, 0.046, h=0.037)
    k.bx(-0.02, 0.02, y0 + IN, y1 - IN, 1.037, 1.043, 'brass', ink=False)
    k.bx(-0.088, 0.088, y0 + IN, y1 - IN, 0.004, 0.03, 'marble', ink=False)


def stair_detail(k, gx, y0, y1, DECK, n_bal=11):
    """Grand stair side: collars at the foot of the gilt balusters, a brass inlay along the handrail and a brass
    collar under the newel ball."""
    for j in range(n_bal):
        yy = -4.7 + j * 0.9
        zb = 0.25 if yy < y0 else (DECK + 0.1 if yy > y1 else 0.25 + (yy - y0) / (y1 - y0) * (DECK - 0.15))
        k.cyl(gx, yy, zb + 0.003, 0.045, 0.045, 0.026, 'brass', seg=5, ink=False)
    pts = [(-4.84, 1.22), (y0 - 0.01, 1.22), (y1 + 0.06, DECK + 1.07), (4.84, DECK + 1.07)]
    k.prism_y([(y, z - 0.003) for y, z in pts] + [(y, z + 0.004) for y, z in reversed(pts)], gx - 0.015, gx + 0.015, 'brass', ink=False)
    k.cyl(gx, -4.86, 1.247, 0.125, 0.115, 0.028, 'brass', seg=8, ink=False)


# ================================================================ desks, bars, furniture
def counter_detail(k, L, yf, yb0, yb1, top_z0, top_z1, n_panels, panel_x, pw, pz0, pz1, edge_x, kick_h=0.12):
    """A front desk / bar counter (front face at y = yf looking toward -Y, marble top yb0..yb1 over x +-edge_x):
    a brass kick plate above the plinth, a brass band round the top edge, a fillet frame inside every gilt-framed
    panel."""
    k.bx(-L + IN, L - IN, yf - 0.012, yf + 0.006, kick_h + 0.004, kick_h + 0.09, 'brass', ink=False)
    xa = edge_x - IN
    k.bx(-xa, xa, yb0 - 0.006, yb0 + 0.006, top_z0 + 0.015, top_z1 - 0.015, 'brass', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * (edge_x - 0.003), s * (edge_x + 0.006)))
        k.bx(a, b, yb0 + IN, yb1 - IN, top_z0 + 0.015, top_z1 - 0.015, 'brass', ink=False)
    for x in panel_x:
        pframe(k, x - pw + 0.07, x + pw - 0.07, pz0 + 0.07, pz1 - 0.07, yf, 'gold', t=0.012, d=0.014)


def backdrop_detail(k, y, xa, xb, panels, z0, z1, cz, dent_z):
    """Reception back wall (face at y): gilt frames round the panels and a dentil row under the cornice."""
    for x, w in panels:
        pframe(k, x - w - 0.03, x + w + 0.03, z0 - 0.03, z1 + 0.03, y, 'gold', t=0.03, d=0.014)
    dentils(k, xa + 0.2, xb - 0.2, dent_z - 0.09, dent_z + 0.003, y - 0.001, 'cream', 19, w=0.07, d=0.03)


def sofa_detail(k, hw, w):
    """Chesterfield sofa (sitters face -Y): piping along the seat cushions, the back and the arms, brass sabots."""
    n = max(2, int(round((w - 0.36) / 0.6)))
    cw = (w - 0.36) / n
    for i in range(n):
        x0 = -hw + 0.18 + i * cw
        piping_x(k, x0 + 0.02, x0 + cw - 0.02, -0.42, 0.515, c='gold', t=0.014, d=0.014)
    piping_x(k, -hw + 0.2, hw - 0.2, 0.18, 0.825, c='gold', t=0.014, d=0.014)
    for t in (-1, 1):
        for yy in (-0.37, 0.37):
            ferrule(k, t * (hw - 0.08), yy, 0.06)


def armchair_detail(k):
    """Club armchair: piping along the seat cushion and the back, brass sabots."""
    piping_x(k, -0.26, 0.26, -0.4, 0.505, c='gold', t=0.014, d=0.014)
    piping_x(k, -0.38, 0.38, 0.2, 0.805, c='gold', t=0.014, d=0.014)
    for t in (-1, 1):
        ferrule(k, t * 0.36, -0.35, 0.05)
        ferrule(k, t * 0.36, 0.35, 0.05)


def stool_detail(k):
    """Bar stool: gilt piping round the seat and back, brass collars on the pedestal."""
    k.cyl(0, 0, 0.745, 0.226, 0.226, 0.014, 'gold', seg=10, ink=False)
    k.cyl(0, 0, 0.792, 0.208, 0.208, 0.014, 'gold', seg=10, ink=False)
    collar(k, 0, 0, 0.09, 0.05, h=0.03)
    collar(k, 0, 0, 0.64, 0.05, h=0.03)
    k.bx(-0.165, 0.165, 0.114, 0.186, 0.998, 1.024, 'gold', ink=False)


def ottoman_detail(k):
    """Ottoman: piping round the top edge, brass sabots on the gilt feet."""
    piping_x(k, -0.84, 0.84, -0.32, 0.40, c='gold', t=0.016, d=0.016)
    piping_x(k, -0.84, 0.84, 0.32, 0.40, c='gold', t=0.016, d=0.016, s=1)
    piping_y(k, -0.3, 0.3, -0.85, 0.40, c='gold', t=0.016, d=0.016, s=-1)
    piping_y(k, -0.3, 0.3, 0.85, 0.40, c='gold', t=0.016, d=0.016, s=1)
    for (x, y) in ((-0.78, -0.25), (0.78, -0.25), (-0.78, 0.25), (0.78, 0.25)):
        ferrule_r(k, x, y, 0.03, h=0.026)


def console_detail(k):
    """Console: brass sabots, beading on the apron and the marble top, a bead frame round the mirror glass."""
    for x in (-0.75, 0.75):
        for y in (-0.1, 0.17):
            ferrule_r(k, x, y, 0.03, h=0.04)
    piping_x(k, -0.78, 0.78, -0.16, 0.695, c='brass', t=0.016, d=0.014)
    piping_x(k, -0.78, 0.78, -0.16, 0.76, c='brass', t=0.012, d=0.012)
    piping_x(k, -0.84, 0.84, -0.2, 0.81, c='brass', t=0.024, d=0.012)
    pframe(k, -0.64, 0.64, 1.16, 2.54, 0.4, 'brass', t=0.04, d=0.014)


def stand_detail(k):
    """Weapon stand: brass sabots, a brass bead on the apron, an inlay line on the marble top."""
    for (x, y) in ((-0.4, -0.22), (0.4, -0.22), (-0.4, 0.22), (0.4, 0.22)):
        ferrule_r(k, x, y, 0.035, h=0.04)
    piping_x(k, -0.43, 0.43, -0.26, 0.79, c='brass', t=0.016, d=0.014)
    k.bx(-0.44, 0.44, -0.27, -0.25, 0.937, 0.943, 'brass', ink=False)
    k.bx(-0.44, 0.44, 0.25, 0.27, 0.937, 0.943, 'brass', ink=False)


def concierge_detail(k):
    """Concierge desk: a brass edge band round the top, brass pulls on the pedestals and kick plates."""
    k.bx(-1.095, 1.095, -0.456, -0.444, 0.735, 0.785, 'brass', ink=False)
    for xs in ((-1.05, -0.55), (0.55, 1.05)):
        k.bx(xs[0] + 0.05, xs[1] - 0.05, -0.412, -0.397, 0.02, 0.1, 'brass', ink=False)
        c = (xs[0] + xs[1]) / 2
        k.bx(c - 0.07, c + 0.07, -0.415, -0.397, 0.58, 0.6, 'brass', ink=False)


def planter_detail(k):
    """Topiary planter: brass kick band, corner angles, a brass rim moulding and raised panels on every face."""
    k.bx(-0.268, 0.268, -0.268, 0.268, 0.004, 0.07, 'brass', ink=False)
    k.bx(-0.268, 0.268, -0.268, 0.268, 0.49, 0.52, 'brass', ink=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(min(sx * 0.2, sx * 0.268), max(sx * 0.2, sx * 0.268), min(sy * 0.2, sy * 0.268), max(sy * 0.2, sy * 0.268), 0.074, 0.486, 'nero2', ink=False)
    for s in (-1, 1):
        a, b = sorted((s * 0.257, s * 0.266))
        k.bx(a, b, -0.14, 0.14, 0.14, 0.44, 'nero2', ink=False)
        k.bx(-0.14, 0.14, a, b, 0.14, 0.44, 'nero2', ink=False)


def urn_detail(k):
    """Palm urn: a stone plinth with a brass-edged cap, a brass band round the belly."""
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.06, 'stone2', ink=False)
    k.bx(-0.26, 0.26, -0.26, 0.26, 0.057, 0.09, 'brass', ink=False)
    k.cyl(0, 0, 0.42, 0.262, 0.262, 0.03, 'brass', seg=12, ink=False)
