"""kit-cargoship structure: wall modules (main deck bulwarks, superstructure front, forecastle bulkhead, hold bulkheads
and side shell, engine room plating), corner posts, the watertight-door gate, the stair-trunk corridor walls, the exit
escape hatch, steel stairs, walkway rails, deck / hatch-cover / walkway markings (see cargo_base.py for conventions).

A wall module is 1 m wide, its room face at Blender y = -0.5; whatever stands in front of that face stays inside the
cell, so the cell's collision box always meets something drawn (no invisible walls)."""
import math

from cargo_base import *  # noqa: F401,F403
import cargo_base as B
import ib_text


# ================================================================ main deck: bulwarks (west / east zone walls)
def bulwark(m, plate=True, full=None):
    """bulwark plate on the deck edge: the plate, a wide cap rail at the room edge, a stay, the fire main"""
    if plate:
        m.bx(-0.5, 0.5, -0.3, -0.24, 0.0, 1.0, 'supWD', hull='noside', cull='b')
        bq(m, -0.5, 0.5, -0.237, 0.0, 1.0, 'hullR')
        # stay: a triangular bracket from the deck to the cap
        m.prism([(-0.3, 0.0), (-0.47, 0.0), (-0.47, 0.12), (-0.3, 0.92)], -0.04, 0.04, ['supWD'])
    if plate if full is None else full:   # the cap runs out to the ship's side: a thick gunwale, red on its outer face
        m.bx(-0.5, 0.5, -0.5, 0.5, 1.0, 1.1, 'deckG', hull='noside')
        bq(m, -0.5, 0.5, 0.503, 0.6, 1.1, 'hullR')
    else:       # open railing: the hull's top strake shows outboard of it
        m.bx(-0.5, 0.5, -0.5, -0.2, 1.0, 1.1, 'deckG', hull='noside')
        m.bx(-0.5, 0.5, -0.2, 0.5, 0.0, 0.08, 'hullR', hull='noside', cull='b')
    fq(m, -0.5, 0.5, -0.503, 1.0, 1.1, 'yel')
    # fire main on brackets (red), running the whole bulwark
    m.cy((-0.5, -0.4, 0.42), 0.06, 0.06, 1.0, 'fireR', seg=8, rot=(0, 90, 0), hull='noside', caps=False)
    m.bx(-0.03, 0.03, -0.42, -0.3 if plate else -0.24, 0.3, 0.36, 'steelD', hull='none', cull='k')


def build_bulwarks(pal, ao):
    for v in ('Plain', 'Rail', 'Chock', 'Hose', 'Lash', 'Light'):
        m = new(pal)
        if v == 'Rail':   # open railing: you see the sea through it
            bulwark(m, plate=False)
            for x in (-0.25, 0.25):
                m.bx(x - 0.03, x + 0.03, -0.29, -0.25, 0.0, 1.0, 'supWD', hull='none')
            for z in (0.35, 0.68):
                m.bx(-0.5, 0.5, -0.285, -0.255, z, z + 0.04, 'supWD', hull='noside')
            m.bx(-0.5, 0.5, -0.3, -0.24, 0.0, 0.12, 'supWD', hull='noside', cull='b')
        elif v == 'Chock':   # panama chock: an oval fairlead through the bulwark plate
            m.bx(-0.5, -0.32, -0.3, -0.24, 0.0, 1.0, 'supWD', hull='noside', cull='b')
            m.bx(0.32, 0.5, -0.3, -0.24, 0.0, 1.0, 'supWD', hull='noside', cull='b')
            m.bx(-0.32, 0.32, -0.3, -0.24, 0.0, 0.22, 'supWD', hull='none', cull='b')
            m.bx(-0.32, 0.32, -0.3, -0.24, 0.72, 1.0, 'supWD', hull='none')
            m.parent = Matrix.Translation((0.0, -0.27, 0.47)) @ Matrix.Diagonal((0.32, 1.0, 0.24, 1.0))
            m.cy((0, -0.07, 0), 1.0, 1.0, 0.14, 'steelD', seg=12, rot=(-90, 0, 0))
            for yy in (-0.073, 0.073):
                m.cy((0, yy - (0.004 if yy < 0 else 0), 0), 0.72, 0.72, 0.004, 'ink', seg=12, rot=(-90, 0, 0), hull='none')
            m.parent = Matrix.Identity(4)
            bulwark(m, plate=False, full=True)
        else:
            bulwark(m)
        if v == 'Hose':   # fire hose box and a hydrant on the main
            m.bx(-0.36, 0.06, -0.48, -0.3, 0.15, 0.95, 'fireR', bevel=True, cull='k')
            fq(m, -0.32, 0.02, -0.483, 0.55, 0.9, 'paper')
            text_front(m, 'FIRE', 0.034, -0.486, -0.15, 0.66, 'fireR')
            m.cy((0.28, -0.4, 0.42), 0.05, 0.05, 0.28, 'fireR', seg=8)
            m.cy((0.28, -0.4, 0.7), 0.09, 0.09, 0.03, 'steelD', seg=8)
        elif v == 'Lash':   # lashing rods stored upright in a rack, a twistlock bin
            m.bx(-0.45, 0.2, -0.48, -0.32, 0.0, 0.08, 'steelD', cull='b')
            for k in range(6):
                x = -0.4 + k * 0.1
                m.bm_((x, -0.4, 0.05), (x + 0.04, -0.33, 1.6), 0.025, 'galv', hull='none')
                m.bx(x + 0.01, x + 0.06, -0.37, -0.31, 1.45, 1.6, 'yel', hull='none')
            m.bx(0.24, 0.47, -0.48, -0.31, 0.0, 0.42, 'yelD', bevel=True)
            m.bx(0.26, 0.45, -0.46, -0.33, 0.42, 0.45, 'grime', hull='none')
        elif v == 'Light':   # deck light on a post over the bulwark
            m.cy((0.0, -0.35, 1.1), 0.05, 0.05, 2.6, 'supWD', seg=8)
            m.bx(-0.18, 0.18, -0.6, -0.3, 3.55, 3.8, 'steelD')
            dq(m, -0.15, 0.15, -0.58, -0.32, 3.547, 'light')
        make('Bul_' + v, m, ao)


# ================================================================ main deck: superstructure front (north wall)
DECKS = (3.0, 6.0, 9.0, 12.0)


def sup_face(m, kind):
    """white deckhouse front: deck ledges, a grey coaming, windows per deck (kind: Win, Blank, Door, Vent, Top)"""
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'supW')
    fq(m, -0.5, 0.5, -0.503, 0.0, 0.3, 'supG')
    for z in DECKS:
        m.bx(-0.5, 0.5, -0.56, -0.5, z - 0.08, z, 'supWD', hull='noside', cull='k')
    m.bx(-0.5, 0.5, -0.62, -0.5, H - 0.25, H, 'supWD', hull='noside', cull='kt')
    rows = [] if kind == 'Blank' else [1.0 + d for d in DECKS[:3]]
    if kind == 'Top':
        rows = rows[:2]
    for z in rows:
        fq(m, -0.32, 0.32, -0.503, z + 0.7, z + 1.85, 'supWD')
        fq(m, -0.27, 0.27, -0.506, z + 0.75, z + 1.8, 'glassD')
        fq(m, -0.27, 0.0, -0.509, z + 1.45, z + 1.8, 'glass')
    if kind == 'Door':   # weathertight door with a sill, a lamp over it
        fq(m, -0.42, 0.42, -0.503, 0.3, 2.35, 'supWD')
        m.bx(-0.36, 0.36, -0.56, -0.5, 0.3, 2.25, 'supW', cull='k')
        fq(m, -0.3, 0.3, -0.563, 1.85, 2.15, 'supWD')
        for z in (0.65, 1.95):
            m.bx(0.22, 0.3, -0.62, -0.56, z, z + 0.06, 'steelD', hull='none')
        m.bx(-0.3, -0.12, -0.62, -0.56, 1.05, 1.11, 'steelD', hull='none')
        m.bx(-0.12, 0.12, -0.7, -0.5, 2.55, 2.75, 'steelD')
        dq(m, -0.1, 0.1, -0.68, -0.52, 2.547, 'light')
    elif kind == 'Vent':   # louvred vent grille at main-deck level
        fq(m, -0.4, 0.4, -0.503, 0.6, 2.2, 'supG')
        for k in range(7):
            fq(m, -0.37, 0.37, -0.506, 0.7 + k * 0.21, 0.78 + k * 0.21, 'steelD')
    elif kind != 'Blank':   # main-deck portholes
        porthole(m, 0.0, -0.5, 1.7, r=0.2)


def build_superstructure(pal, ao):
    for v in ('Win', 'Blank', 'Door', 'Vent', 'Top'):
        m = new(pal)
        sup_face(m, v)
        make('Sup_' + v, m, ao)
    # the line's name across the upper decks, split over modules (stacked on Sup_Top by the theme): HALCYON / LINES
    for word, n in (('HALCYON', 10), ('LINES', 7)):
        for k in range(n):
            m = new(pal)
            u0 = k - n / 2.0
            ib_text.draw(m, word, -(u0 + 0.5), -0.512, 9.2, 2.6, 'cTel', face='y-', font='display', clip=(u0, u0 + 1.0),
                         maxw=n - 0.6, shadow='ink', shadow_off=(0.03, -0.04))
            make('Sup_%s_%d' % (word, k), m, ao)


# ================================================================ main deck: forecastle bulkhead (south wall)
def fc_face(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, FC, 'supW')
    fq(m, -0.5, 0.5, -0.503, 0.0, 0.3, 'supG')
    fq(m, -0.5, 0.5, -0.503, 1.6, 1.64, 'supWD')
    # the forecastle deck edge and its guard rail
    m.bx(-0.5, 0.5, -0.6, -0.5, FC - 0.05, FC + 0.12, 'deckGD', hull='noside', cull='k')
    m.bx(-0.5, 0.5, -0.5, 0.5, FC, FC + 0.12, 'deckG', hull='none', cull='bf')
    rail_run(m, -0.5, 0.5, -0.4, FC + 0.12, h=1.05, c='supW')


def build_forecastle(pal, ao):
    for v in ('Plain', 'Door', 'Ladder', 'Vent', 'Sign'):
        m = new(pal)
        fc_face(m)
        if v == 'Door':
            fq(m, -0.44, 0.44, -0.506, 0.3, 2.3, 'supWD')
            m.bx(-0.38, 0.38, -0.56, -0.5, 0.35, 2.2, 'supW', cull='k')
            for z in (0.6, 1.25, 1.9):
                m.bx(-0.34, -0.24, -0.62, -0.56, z, z + 0.06, 'steelD', hull='none')
            sign(m, 0.0, -0.563, 1.55, 0.6, 0.22, 'BOSUN', bg='signB')
            m.bx(-0.12, 0.12, -0.7, -0.5, 2.6, 2.8, 'steelD')
            dq(m, -0.1, 0.1, -0.68, -0.52, 2.597, 'light')
        elif v == 'Ladder':
            ladder(m, 0.0, -0.5, 0.0, FC + 1.05, c='yel')
        elif v == 'Vent':
            fq(m, -0.36, 0.36, -0.503, 0.7, 1.5, 'supG')
            for k in range(4):
                fq(m, -0.33, 0.33, -0.506, 0.78 + k * 0.18, 0.86 + k * 0.18, 'steelD')
        elif v == 'Sign':
            sign(m, 0.0, -0.503, 1.9, 0.86, 0.5, 'MUSTER', bg='exitG')
        make('Fc_' + v, m, ao)


# ================================================================ hold: transverse bulkheads (N / S) and side shell (W / E)
def corrugation(m, z0=0.0, z1=H, c='hold', cd='holdD'):
    """one vertical corrugation per module: a flange at the room face, webs back to the recessed plate"""
    m.bx(-0.5, 0.5, -0.38, -0.3, z0, z1, c, hull='noside', cull='k')
    m.bx(-0.2, 0.2, -0.5, -0.38, z0, z1, c, cull='k')
    for sx in (-1, 1):
        a, b = sorted((sx * 0.2, sx * 0.32))
        poly(m, [(sx * 0.2, -0.5, z0), (sx * 0.32, -0.383, z0), (sx * 0.32, -0.383, z1), (sx * 0.2, -0.5, z1)], cd, (sx, -1, 0))


def build_hold_walls(pal, ao):
    for v in ('Plain', 'Ladder', 'Lamp', 'Rust', 'Vent'):
        m = new(pal)
        corrugation(m)
        fq(m, -0.2, 0.2, -0.503, 0.0, 0.25, 'holdD')
        if v == 'Ladder':
            ladder(m, 0.0, -0.5, 0.0, H - 0.4, c='yel', cage=True)
        elif v == 'Lamp':   # floodlight under the coaming, a junction box low down
            m.bx(-0.25, 0.25, -0.85, -0.5, 11.2, 11.6, 'steelD')
            poly(m, [(-0.22, -0.853, 11.23), (0.22, -0.853, 11.23), (0.22, -0.853, 11.57), (-0.22, -0.853, 11.57)], 'light', (0, -1, 0))
            m.bx(-0.12, 0.12, -0.6, -0.5, 1.6, 1.9, 'steelD')
        elif v == 'Rust':
            for x, z0, z1 in ((-0.12, 5.4, 8.8), (0.05, 2.0, 4.6), (0.14, 9.5, 11.9)):
                fq(m, x - 0.025, x + 0.025, -0.503, z0, z1, 'rust')
        elif v == 'Vent':   # ventilation trunk opening near the deckhead
            m.bx(-0.45, 0.45, -0.75, -0.5, 9.8, 11.4, 'holdD', cull='k')
            for k in range(6):
                fq(m, -0.42, 0.42, -0.753, 9.95 + k * 0.24, 10.05 + k * 0.24, 'steelD')
        make('Hb_' + v, m, ao)
    # the hold number painted big across the bulkhead (stacked on Hb_Plain by the theme)
    n = 5
    for k in range(n):
        m = new(pal)
        u0 = k - n / 2.0
        ib_text.draw(m, 'NO.7 HOLD', -(u0 + 0.5), -0.506, 2.2, 1.0, 'paper', face='y-', font='display', clip=(u0, u0 + 1.0), maxw=n - 0.5)
        make('Hb_Num_%d' % k, m, ao)
    # side shell: plating with a frame per module, web frames, ladders, sounding pipes
    for v in ('Plain', 'Web', 'Pipe', 'Ladder', 'Lamp'):
        m = new(pal)
        fq(m, -0.5, 0.5, -0.4, 0.0, H, 'hold')
        m.bx(-0.04, 0.04, -0.5, -0.4, 0.0, H, 'holdD', cull='kt')
        fq(m, -0.5, 0.5, -0.403, 0.0, 0.3, 'holdD')
        for z in (4.0, 8.4):   # side stringers
            m.bx(-0.5, 0.5, -0.49, -0.4, z, z + 0.12, 'hold', hull='noside', cull='k')
        if v == 'Web':
            m.bx(-0.16, 0.16, -0.53, -0.4, 0.0, H, 'hold', cull='kt')
            fq(m, -0.1, 0.1, -0.533, 0.0, H, 'holdD')
        elif v == 'Pipe':
            m.cy((0.3, -0.455, 0.0), 0.04, 0.04, H, 'steelD', seg=8, caps=False)
            m.cy((0.3, -0.455, 0.7), 0.06, 0.06, 0.12, 'yel', seg=8)
            fq(m, -0.3, 0.0, -0.403, 1.2, 1.5, 'paper')
            text_front(m, 'BILGE', 0.025, -0.406, -0.15, 1.29, 'ink')
        elif v == 'Ladder':
            ladder(m, 0.0, -0.4, 0.0, H - 0.4, c='yel', cage=True)
        elif v == 'Lamp':
            m.bx(-0.25, 0.25, -0.8, -0.5, 11.2, 11.6, 'steelD')
            poly(m, [(-0.22, -0.803, 11.23), (0.22, -0.803, 11.23), (0.22, -0.803, 11.57), (-0.22, -0.803, 11.57)], 'light', (0, -1, 0))
        make('Hs_' + v, m, ao)


# ================================================================ engine room plating
def build_er_walls(pal, ao):
    for v in ('Plain', 'Pipes', 'Panel', 'Tray', 'Ladder', 'Lamp', 'Sign'):
        m = new(pal)
        fq(m, -0.5, 0.5, -0.42, 0.0, H, 'supG')
        m.bx(-0.04, 0.04, -0.47, -0.42, 0.0, H, 'supWD', cull='kt')
        fq(m, -0.5, 0.5, -0.423, 0.0, 0.25, 'steelD')
        fq(m, -0.5, 0.5, -0.423, 9.6, 9.7, 'supWD')
        if v == 'Pipes':   # colour-coded vertical pipes: sea water, fuel, fresh water
            for x, r, c in ((-0.28, 0.07, 'deckG'), (0.0, 0.05, 'rust'), (0.24, 0.06, 'signB')):
                m.cy((x, -0.43 - r, 0.0), r, r, H, c, seg=8, caps=False)
                for z in (1.2, 5.0, 9.0):
                    m.cy((x, -0.43 - r, z), r + 0.012, r + 0.012, 0.12, 'paper', seg=8, caps=False, hull='none')
            for z in (2.0, 6.5, 11.0):
                m.bx(-0.45, 0.45, -0.5, -0.42, z, z + 0.05, 'steelD', hull='noside')
        elif v == 'Panel':   # local starter panel: grey cabinet, lamps, a switch
            m.bx(-0.42, 0.42, -0.5, -0.42, 0.3, 2.1, 'supWD', bevel=True)
            fq(m, -0.36, 0.36, -0.503, 1.2, 1.9, 'steelL')
            for k, c in enumerate(('exitG', 'fireR', 'amber')):
                m.cy((-0.2 + k * 0.2, -0.503, 1.55), 0.04, 0.04, 0.02, c, seg=6, rot=(90, 0, 0), hull='none')
            m.bx(-0.06, 0.06, -0.56, -0.5, 0.8, 0.95, 'ink', hull='none')
        elif v == 'Tray':   # vertical cable tray with cable bundles
            m.bx(-0.25, 0.25, -0.5, -0.42, 0.0, H, 'galv', cull='kt')
            for x, c in ((-0.15, 'ink'), (-0.03, 'gunmetal'), (0.1, 'ink')):
                m.bx(x - 0.04, x + 0.04, -0.54, -0.5, 0.0, H, c, hull='none', cull='kt')
        elif v == 'Ladder':
            ladder(m, 0.0, -0.42, 0.0, H - 0.4, c='yel')
        elif v == 'Lamp':
            for z in (3.6, 9.2):
                m.bx(-0.3, 0.3, -0.62, -0.5, z, z + 0.16, 'steelL')
                dq(m, -0.27, 0.27, -0.6, -0.52, z - 0.003, 'light')
        elif v == 'Sign':   # ear defenders must be worn: blue mandatory sign
            m.cy((0.0, -0.423, 2.0), 0.24, 0.24, 0.01, 'signB', seg=14, rot=(90, 0, 0), hull='none')
            fq(m, -0.12, 0.12, -0.437, 1.9, 2.1, 'paper')
            fq(m, -0.2, -0.12, -0.437, 1.85, 2.15, 'paper')
            fq(m, 0.12, 0.2, -0.437, 1.85, 2.15, 'paper')
        make('Er_' + v, m, ao)


# ================================================================ corners
def build_corners(pal, ao):
    """corner posts in each zone kind; NW..SE name the corner of the zone they stand in"""
    for kind, c, h in (('DeckN', 'supW', H), ('DeckS', 'supW', FC + 1.17), ('Hold', 'holdD', H), ('Er', 'supWD', H)):
        for name, sx, sy in (('NW', 1, -1), ('NE', -1, -1), ('SW', 1, 1), ('SE', -1, 1)):
            m = new(pal)
            x0, x1 = sorted((sx * 0.496, sx * 0.78))
            y0, y1 = sorted((sy * 0.496, sy * 0.78))
            if kind == 'DeckS' or (kind == 'DeckN' and name[0] == 'S'):
                h2 = 1.1 if kind == 'DeckN' else h
            else:
                h2 = h
            m.bx(x0, x1, y0, y1, 0.0, h2, c, cull='b')
            m.bx(x0 - 0.004, x1 + 0.004, y0 - 0.004, y1 + 0.004, 0.0, 0.3, 'steelD' if kind != 'DeckN' else 'supG', hull='none', cull='tb')
            make('Corner_%s_%s' % (kind, name), m, ao)


# ================================================================ gate (watertight door), corridor (stair trunk), hatch
def gate_face(m, fy):
    """details of one face (fy -1: front -Y, +1: back) of the door portal"""
    f = fq if fy < 0 else bq
    y = fy * 0.6
    for sx in (-1, 1):   # jamb faces: hazard stripes
        a, b = sorted((sx * 1.5, sx * 2.5))
        for k in range(5):
            f(m, a + 0.12, b - 0.12, y + fy * 0.003, 0.25 + k * 0.5, 0.5 + k * 0.5, 'yel' if k % 2 == 0 else 'ink')
    # heavy door frame with dog handles round the opening
    for sx in (-1, 1):
        m.bx(min(sx * 1.5, sx * 1.66), max(sx * 1.5, sx * 1.66), min(y, y + fy * 0.12), max(y, y + fy * 0.12), 0.0, 3.28, 'steelD', cull='b')
        for z in (0.9, 2.3):
            m.bx(min(sx * 1.68, sx * 1.86), max(sx * 1.68, sx * 1.86), min(y, y + fy * 0.18), max(y, y + fy * 0.18), z, z + 0.08, 'steelD', hull='none', cull='k' if fy < 0 else 'f')
    m.bx(-1.66, 1.66, min(y, y + fy * 0.12), max(y, y + fy * 0.12), 3.28, 3.44, 'steelD')
    for sx in (-1, 1):   # rounded top corners of the opening
        poly(m, [(sx * 1.5, y + fy * 0.123, 3.28), (sx * 1.5, y + fy * 0.123, 2.98), (sx * 1.2, y + fy * 0.123, 3.28)], 'steelD', (0, fy, 0))
    # plaque, status lights
    zt = 4.2
    f(m, -1.2, 1.2, y + fy * 0.003, zt, zt + 0.7, 'paper')
    (text_front if fy < 0 else text_back)(m, 'WATERTIGHT DOOR', 0.04, y + fy * 0.006, 0.0, zt + 0.22, 'fireR', font='display')
    for sx, c in ((-1, 'exitG'), (1, 'fireR')):
        m.cy((sx * 2.0, y, 3.75), 0.11, 0.11, 0.08, c, seg=8, rot=(fy * -90, 0, 0))
    # a down arrow and the deck the door leads to
    f(m, -0.6, 0.6, y + fy * 0.003, 6.2, 8.4, 'yel')
    poly(m, [(-0.45, y + fy * 0.006, 7.6), (0.45, y + fy * 0.006, 7.6), (0.0, y + fy * 0.006, 6.5)], 'ink', (0, fy, 0))
    f(m, -0.15, 0.15, y + fy * 0.006, 7.6, 8.2, 'ink')


def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.5, sx * 2.5))
        m.bx(a, b, -0.6, 0.6, 0.0, 3.44, 'supWD', cull='b')
    m.bx(-2.5, 2.5, -0.6, 0.6, 3.44, H, 'supWD', cull='t')
    for fy in (-1, 1):
        gate_face(m, fy)
        for z in (5.6, 9.2, 11.6):   # stiffeners on the trunk plating
            m.bx(-2.5, 2.5, min(fy * 0.6, fy * 0.66), max(fy * 0.6, fy * 0.66), z, z + 0.1, 'supG', hull='noside', cull='')
    make('GateFrame', m, ao, cols=[cb(-2.5, -0.6, 0, -1.5, 0.6, 3.44), cb(1.5, -0.6, 0, 2.5, 0.6, 3.44)], side=2.45)
    # sliding watertight door leaf
    m = new(pal)
    Hs = 3.05
    m.box((0, 0, Hs / 2), (3.0, 0.12, Hs), 'steel', bevel=False)
    for fy in (-1, 1):
        f = fq if fy < 0 else bq
        for z in (0.45, 1.15, 2.65):
            m.box((0, fy * 0.075, z), (2.9, 0.03, 0.08), 'steelD', bevel=False)
        for k in range(10):
            f(m, -1.5 + k * 0.3, -1.2 + k * 0.3, fy * 0.063, 0.02, 0.22, 'yel' if k % 2 else 'ink')
        m.cy((0.0, fy * 0.06, 1.95), 0.26, 0.26, 0.004, 'steelL', seg=12, rot=(-fy * 90, 0, 0))
        m.cy((0.0, fy * 0.064, 1.95), 0.2, 0.2, 0.004, 'glassD', seg=12, rot=(-fy * 90, 0, 0))
        m.box((1.1, fy * 0.1, 1.1), (0.08, 0.06, 0.4), 'yel', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.14, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)

    # stair trunk walls (13 m): 1 m along Blender Y, inner face +X; landings at 4.4 and 8.8 m on every module
    for v in ('TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_End'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'supWD', hull='noend', cull='t')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.25, 'steelD')
        rq(m, 0.253, -0.5, 0.5, 0.25, 1.3, 'supG')
        m.bx(0.25, 0.31, -0.5, 0.5, 1.3, 1.36, 'supG', hull='noend')
        for z in ((4.4, 8.8) if v != 'TrailWall_End' else ()):   # landing: grating with a toe plate and a rail
            m.bx(0.25, 1.0, -0.5, 0.5, z - 0.08, z, 'galv', hull='noend')
            rq(m, 1.003, -0.5, 0.5, z - 0.08, z, 'yel')
            m.bx(0.96, 1.0, -0.5, 0.5, z + 0.95, z + 1.0, 'yel', hull='noend')
            m.bx(0.97, 0.99, -0.5, 0.5, z + 0.5, z + 0.53, 'yel', hull='none')
            m.bx(0.96, 1.0, -0.03, 0.03, z, z + 0.95, 'yel', hull='none')
        if v == 'TrailWall_B':   # ladder between the floor and the landings
            m.parent = Matrix.Rotation(math.radians(90), 4, 'Z')
            ladder(m, 0.0, -0.25, 0.0, 9.75, c='yel', face=-1)
            m.parent = Matrix.Identity(4)
        elif v == 'TrailWall_C':   # deck doors off each landing, deck names
            for z, word in ((4.4, 'C DECK'), (8.8, 'B DECK')):
                rq(m, 0.253, -0.4, 0.4, z, z + 2.0, 'steelL')
                rq(m, 0.256, -0.34, 0.34, z + 0.05, z + 1.9, 'supG')
                text_side(m, word, 0.03, 0.259, 0.0, z + 2.25, 'ink', 'x+')
        elif v == 'TrailWall_End':   # the escape trunk's end bulkhead: plating, a lamp, stencilled exit arrow
            m.bx(0.25, 0.4, -0.18, 0.18, 2.6, 2.95, 'steelD')
            rq(m, 0.403, -0.15, 0.15, 2.64, 2.91, 'light')
            for z in (4.4, 8.8):
                rq(m, 0.253, -0.5, 0.5, z - 0.05, z, 'supG')
        elif v == 'TrailWall_D':   # bulkhead lamp, vertical pipes
            m.bx(0.25, 0.4, -0.18, 0.18, 2.6, 2.95, 'steelD')
            rq(m, 0.403, -0.15, 0.15, 2.64, 2.91, 'light')
            for yy, c in ((-0.3, 'deckG'), (0.32, 'fireR')):
                m.cy((0.33, yy, 0.0), 0.05, 0.05, H, c, seg=8, caps=False)
        make(v, m, ao, side=0.45)
    # escape hatch in the floor: round lid on a coaming, hinge, yellow ring, stencil
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.12, 'steelD', seg=16)
    m.cy((0, 0, 0.12), 0.95, 0.95, 0.06, 'steel', seg=16)
    for i in range(16):
        a0, a1 = i / 16 * 2 * math.pi, (i + 1) / 16 * 2 * math.pi
        poly(m, [(math.cos(a0) * 0.98, math.sin(a0) * 0.98, 0.123), (math.cos(a0) * 1.15, math.sin(a0) * 1.15, 0.123),
                 (math.cos(a1) * 1.15, math.sin(a1) * 1.15, 0.123), (math.cos(a1) * 0.98, math.sin(a1) * 0.98, 0.123)], 'yel' if i % 2 else 'ink', (0, 0, 1))
    m.bx(-0.3, 0.3, 0.9, 1.1, 0.0, 0.26, 'steelD')
    text_up(m, 'ESCAPE', 0.05, 0.183, 0.0, 0.0, 'paper')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ steel stairs, walkway rails
def build_stair(pal, ao, name, W, L, rise, n, landing):
    """steel stair rising toward +Y: grating treads with yellow nosings, side stringers, handrails. Collision: walkable
    step blocks (solid to the floor for the nav grid) and the handrails along both sides"""
    m = new(pal)
    run = (L - landing) / n
    cols = []
    for k in range(n):
        y0 = -L / 2 + k * run
        y1 = y0 + run if k < n - 1 else L / 2
        top = (k + 1) * rise / n
        m.bx(-W / 2 + 0.08, W / 2 - 0.08, y0, y1 if k == n - 1 else y0 + run + 0.02, top - 0.05, top, 'galv', hull='none', cull='blr')
        uq(m, -W / 2 + 0.1, W / 2 - 0.1, y0 + 0.01, y0 + 0.07, top + 0.003, 'yel')
        cols.append(cb(-W / 2, y0, 0.0, W / 2, y1, top, True))
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (W / 2 - 0.08), sx * W / 2))
        prof = [(-L / 2, 0.0), (L / 2, 0.0), (L / 2, rise + 0.02), (L / 2 - landing, rise + 0.02), (-L / 2, 0.3)]
        m.prism(prof, x0, x1, ['steelL'], skip=(0,))
        # stringer band painted along the flight on the outer face
        xo = sx * (W / 2 + 0.003)
        poly(m, [(xo, -L / 2, 0.02), (xo, L / 2 - landing, rise - 0.28), (xo, L / 2 - landing, rise), (xo, -L / 2, 0.3)], 'steelD', (sx, 0, 0))
        xr = sx * (W / 2 - 0.04)
        yt = L / 2 - landing
        m.bm_((xr, -L / 2 + 0.1, rise / n + 0.95), (xr, yt, rise + 0.95), 0.05, 'yel')
        m.bm_((xr, yt + 0.04, rise + 0.95), (xr, L / 2 - 0.03, rise + 0.95), 0.05, 'yel')
        m.bm_((xr, -L / 2 + 0.2, rise / n + 0.5), (xr, yt, rise + 0.5), 0.03, 'yel')
        for k in range(0, n + 1, 3):
            y = min(-L / 2 + (k + 0.5) * run, yt)
            z = min(rise, (k + 1) * rise / n)
            m.bx(xr - 0.018, xr + 0.018, y - 0.018, y + 0.018, z, z + 0.92, 'yel', hull='none', cull='bt')
        m.bx(xr - 0.018, xr + 0.018, L / 2 - 0.07, L / 2 - 0.035, rise, rise + 0.92, 'yel', hull='none', cull='bt')
    m.bx(-W / 2 + 0.08, W / 2 - 0.08, L / 2 - 0.04, L / 2, 0.0, rise - 0.05, 'steelL', cull='b')
    make(name, m, ao, cols=cols)


def build_stairs(pal, ao):
    build_stair(pal, ao, 'StairH', 2.6, 4.0, HATCH, 6, 0.5)
    build_stair(pal, ao, 'StairW', 2.6, 10.0, WALK, 18, 1.0)


def build_rails(pal, ao):
    """walkway edge rail: toe plate, posts, knee and top rail (half module from the cell centre toward -Y, a full
    module, a post)"""
    def rail(m, y0, y1):
        m.bx(-0.02, 0.02, y0, y1, 0.0, 0.14, 'yel', hull='noend', cull='b')
        m.bx(-0.03, 0.03, y0, y1, 1.0, 1.06, 'yel', hull='noend')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'yel', hull='none')
    m = new(pal)
    rail(m, -0.5, -0.03)
    make('Rail', m, ao, cols=[cb(-0.06, -0.5, 0, 0.06, 0.0, 1.06)])
    m = new(pal)
    rail(m, -0.5, 0.5)
    m.bx(-0.025, 0.025, -0.025, 0.025, 0.14, 1.0, 'yel', hull='none')
    make('RailFull', m, ao, cols=[cb(-0.06, -0.5, 0, 0.06, 0.5, 1.06)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.08, 'yel', cull='b')
    make('RailPost', m, ao)


# ================================================================ markings (flat, no outline)
def build_markings(pal, ao):
    # main deck (@layer 0.01): safe-walkway lines, hazard hatching, rust and oil
    m = new(pal)
    uq(m, -0.06, 0.06, -0.5, -0.05, 0.003, 'yel')
    uq(m, -0.06, 0.06, 0.15, 0.5, 0.003, 'yel')
    make('WalkLine', m, ao)
    m = new(pal)
    for k in range(4):
        poly(m, [(-0.5 + k * 0.25, -0.5, 0.003), (-0.375 + k * 0.25, -0.5, 0.003), (-0.375 + k * 0.25, 0.5, 0.003), (-0.5 + k * 0.25, 0.5, 0.003)], 'yel' if k % 2 else 'ink', (0, 0, 1))
    make('Hatching', m, ao)
    for name, c, pts in (('Rust', 'rust', [1.0, 0.8, 1.1, 0.7, 0.95, 0.85, 1.05, 0.75]), ('Oil', 'oil', [0.9, 1.1, 0.8, 1.0, 1.15, 0.85, 0.95, 1.05])):
        m = new(pal)
        disc(m, 0.05, -0.03, 0.003, 0.38, c, seg=8, jag=pts)
        disc(m, -0.22, 0.24, 0.006, 0.14, c, seg=6)
        make(name, m, ao)
    # hatch cover tops (@layer 1.81): weld seams with cleats, twistlock sockets, hatch numbers
    m = new(pal)
    uq(m, -0.5, 0.5, -0.03, 0.03, 0.003, 'deckGD')
    uq(m, -0.08, 0.08, -0.12, 0.12, 0.006, 'steelD')
    make('Seam', m, ao)
    m = new(pal)
    for x in (-0.25, 0.25):
        uq(m, x - 0.09, x + 0.09, -0.06, 0.06, 0.003, 'steelD')
        uq(m, x - 0.05, x + 0.05, -0.025, 0.025, 0.006, 'ink')
    make('Sockets', m, ao)
    for k in (1, 2, 3):
        m = new(pal)
        text_up(m, 'NO.%d' % k, 0.16, 0.009, 0.0, 0.0, 'paper', font='display')
        make('HatchNo_%d' % k, m, ao)
    # walkway grating (@layer 5.21), bilge well grating (@layer 0.01)
    m = new(pal)
    for k in range(5):
        uq(m, -0.5, 0.5, -0.42 + k * 0.2, -0.38 + k * 0.2, 0.003, 'steelD')
    make('Grate', m, ao)
    m = new(pal)
    uq(m, -0.45, 0.45, -0.45, 0.45, 0.003, 'steelD')
    for k in range(6):
        uq(m, -0.42, 0.42, -0.4 + k * 0.15, -0.34 + k * 0.15, 0.006, 'ink')
    make('Bilge', m, ao)


# ================================================================ deckhead fittings (hold, engine room)
def build_deckhead(pal, ao):
    """hang from their origin at the deckhead (13 m): z <= 0"""
    # hold: hatch-cover girder (run), daylight slot between hatch panels (run), floodlight
    m = new(pal)
    m.bx(-0.5, 0.5, -0.06, 0.06, -0.9, -0.004, 'hold', hull='noside', cull='t')
    m.bx(-0.5, 0.5, -0.22, 0.22, -0.98, -0.9, 'holdD', hull='noside')
    make('Girder', m, ao)
    m = new(pal)
    dq(m, -0.5, 0.5, -0.09, 0.09, -0.004, 'day')
    m.bx(-0.5, 0.5, -0.2, -0.09, -0.12, -0.004, 'holdD', hull='noside', cull='t')
    m.bx(-0.5, 0.5, 0.09, 0.2, -0.12, -0.004, 'holdD', hull='noside', cull='t')
    make('Slot', m, ao)
    m = new(pal)
    m.cy((0, 0, -0.6), 0.03, 0.03, 0.596, 'steelD', seg=6)
    m.cy((0, 0, -0.95), 0.28, 0.12, 0.35, 'steelD', seg=10)
    dq(m, -0.18, 0.18, -0.18, 0.18, -0.953, 'light')
    make('Lamp', m, ao)
    # engine room: crane rail (run), pipe rack (run), duct (run), crane bridge girder (run)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.05, 0.05, -0.6, -0.004, 'steelD', hull='noside', cull='t')
    m.bx(-0.5, 0.5, -0.2, 0.2, -0.68, -0.6, 'steelD', hull='noside')
    m.bx(-0.5, 0.5, -0.04, 0.04, -0.72, -0.68, 'galv', hull='noside')
    make('CraneRail', m, ao)
    m = new(pal)
    for y, r, c in ((-0.3, 0.09, 'deckG'), (0.0, 0.07, 'rust'), (0.28, 0.1, 'galv')):
        m.cy((-0.5, y, -0.7), r, r, 1.0, c, seg=8, rot=(0, 90, 0), hull='noside', caps=False)
    m.bx(-0.04, 0.04, -0.45, 0.45, -0.88, -0.82, 'steelD')
    for y in (-0.42, 0.42):
        m.bx(-0.02, 0.02, y - 0.02, y + 0.02, -0.82, -0.004, 'steelD', hull='none')
    make('PipeRack', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.4, 0.4, -0.85, -0.25, 'galv', hull='noside')
    for y in (-0.403, 0.403):
        f = fq if y < 0 else bq
        f(m, -0.5, 0.5, y, -0.58, -0.52, 'steelL')
    m.bx(-0.03, 0.03, -0.42, 0.42, -0.25, -0.004, 'steelD', hull='none')
    make('Duct', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.35, 0.35, -1.5, -0.8, 'yel', hull='noside')
    for y in (-0.353, 0.353):
        f = fq if y < 0 else bq
        for k in range(2):
            f(m, -0.5 + k * 0.5, -0.25 + k * 0.5, y, -1.5, -0.8, 'ink')
    make('CraneBridge', m, ao)
    m = new(pal)
    for z in range(10):
        m.bx(-0.03, 0.03, -0.06, 0.06, -0.3 - z * 0.25, -0.12 - z * 0.25, 'steelD' if z % 2 else 'galv', hull='none')
    m.bx(-0.2, 0.2, -0.12, 0.12, -0.12, -0.004, 'yel')
    m.bx(-0.1, 0.1, -0.08, 0.08, -2.75, -2.5, 'yel')
    m.cy((0, 0, -3.05), 0.16, 0.12, 0.3, 'steelD', seg=8)
    make('ChainHook', m, ao)
