"""kit-foundry modelled detail (tactical look plan Stage 11): the fixings a real heavy-plant hall carries on the pieces
the player sees most. The kit sits right under its theme triangle ceiling (100,000, hard-asserted by
theme_foundry.test.js) and the wall modules repeat hundreds of times, so every part here is a flat quad drawn from the
visible side only (rivet / bolt heads 2 tris, plates and seams 2 tris, not the 12 of a box), 4 - 8 mm proud of the
face it sits on, never coplanar with a neighbour, and horizontal runs stop 5 mm short of the piece sides (so they pass
ib_lib.check_zfight). Nothing here touches a glow part, a collision box, an origin or a footprint."""
from foundry_common import rivet_row

E = 0.005        # horizontal runs stop this far short of a piece side
BOLT = 'steel2'
DARK = 'steelDark'


def bolts(k, xs, z, y, s, c=BOLT, r=0.017):
    """Bolt heads at the given x positions (flat 3.4 cm squares)."""
    for x in xs:
        k.qy(x - r, x + r, z - r, z + r, y, s, c)


def wall_extra(k, a, b, plinth_y, seam):
    """Wall module, room face at y = -0.5: a conduit run with a clip on the concrete plinth (a, b = the run's x span),
    and on the plain modules a lapped cladding seam down the middle of the plate courses with bolt pairs on it."""
    yc = plinth_y - 0.004
    k.qy(a + E, b - E, 3.28, 3.35, yc, -1, DARK)                       # conduit along the plinth head
    k.qy(a + E, b - E, 3.355, 3.365, yc, -1, 'steel2')                 # its lit upper edge
    if a < 0.0 < b:
        k.qy(-0.03, 0.03, 3.24, 3.39, yc - 0.003, -1, 'gun')              # one saddle clip per module
    if seam and a < -0.03 and b > 0.03:
        k.qy(-0.015, 0.015, 4.3, 23.8, -0.507, -1, 'slate2')           # lapped seam (the horizontal seams sit at -0.503)
        for z in (6.0, 10.0, 14.0, 18.0, 22.0):
            bolts(k, (-0.045, 0.045), z, -0.509, -1, c='slateL', r=0.015)


def num_plate(k):
    """Wall_Num: corner bolts on the stencilled number plate (plate x +-0.42, z 11.2 - 15.3 at y = -0.506)."""
    bolts(k, (-0.38, 0.38), 11.38, -0.511, -1, r=0.02)
    bolts(k, (-0.38, 0.38), 15.12, -0.511, -1, r=0.02)


def pilaster_extra(k):
    """Pilaster: anchor bolts on the foot of the concrete pier, web stiffener ribs up the steel column."""
    for x in (-0.34, -0.12, 0.12, 0.34):
        k.qy(x - 0.03, x + 0.03, 0.04, 0.1, -1.756, -1, DARK)           # nut and washer under the chevron field
        k.qy(x - 0.014, x + 0.014, 0.052, 0.088, -1.76, -1, BOLT)
    for x in (-0.34, 0.34):
        k.qy(x - 0.018, x + 0.018, 5.5, 22.4, -1.41, -1, 'gun2')        # stiffener ribs on the column web (y = -1.4)
    for z in (5.9, 22.0):
        bolts(k, (-0.34, 0.34), z, -1.414, -1, r=0.02)


def gate_extra(k, hd, side):
    """GateFrame (side f = -1 / +1 faces): a rivet row down the crimson header and anchor bolts on the post feet."""
    f = side
    yb = f * 0.853
    rivet_row(k, -2.3, 2.3, hd + 0.7, yb + f * 0.004, f, 8, c=DARK, r=0.025)
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.5, s * 2.2))
        bolts(k, (x0 + 0.18, x1 - 0.18), 0.045, f * 0.753 + f * 0.004, f, r=0.022)


def fence_plate(k, x, y):
    """Line fence post: a base plate on the floor round the post (post 0.12 square at x, y)."""
    k.qz(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.022, 1, DARK)


def tunnel_rivets(k, x0, x1, yo, f):
    """Fitting tunnel wall: a rivet row down the crimson band (z 2.6 - 3.1 at yo)."""
    rivet_row(k, x0 + 0.2, x1 - 0.2, 2.85, yo + f * 0.007, f, 6, c=DARK, r=0.022)


def port_rivets(k, x0, x1, z, yo, f):
    """Monorail port: a rivet row along its crimson band."""
    rivet_row(k, x0 + 0.3, x1 - 0.3, z, yo + f * 0.004, f, 8, c=DARK, r=0.022)


def ammo_crate(k):
    """Ammo crate: steel latches on the long faces (the hazard band and stencil sit on y = +-0.383)."""
    for f in (-1, 1):
        for x in (-0.4, 0.4):
            k.qy(x - 0.035, x + 0.035, 0.63, 0.76, f * 0.389, f, 'steel2')
            k.qy(x - 0.014, x + 0.014, 0.65, 0.68, f * 0.392, f, DARK)


def flood_base(k):
    """FloodTower: a flange and four bolts where the mast meets the generator, bolts on its panel."""
    k.qz(-0.24, 0.24, -0.24, 0.24, 1.203, 1, DARK)
    for x in (-0.19, 0.19):
        for y in (-0.19, 0.19):
            k.qz(x - 0.025, x + 0.025, y - 0.025, y + 0.025, 1.207, 1, BOLT)
    bolts(k, (-0.57, -0.13), 0.78, -0.606, -1, r=0.02)
    bolts(k, (-0.57, -0.13), 1.02, -0.606, -1, r=0.02)


def door_header(k, h):
    """Launch door header: a rivet row along the lower edge of the slate header (y = -1.1)."""
    rivet_row(k, -8.7, 8.7, h + 0.18, -1.104, -1, 22, c=DARK, r=0.04)
