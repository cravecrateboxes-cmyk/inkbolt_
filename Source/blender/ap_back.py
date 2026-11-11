"""kit-airport outside pieces (placed by the theme's backdrop.build, not by zone symbols): the jet bridge in parts
(the rotunda on its column, a tunnel section of unit length along Blender X that the theme stretches and pitches
from the rotunda to the cab, the drive column, the cab with its bellows canopy facing +X), the control tower, a
fuel-farm tank and a low cargo shed. The aircraft outside reuse the hangar's Jet_Body and Engine pieces."""
import math

from ap_base import *  # noqa: F401,F403
import ap_base as B

GY = -4.5        # the apron outside the terminal lies 4.5 m under the departures floor


def build_back(pal, ao):
    # rotunda: a round room at the terminal face (floor at 0) on a concrete column down to the apron
    m = new(pal)
    m.cy((1.6, 0.0, -0.15), 1.6, 1.6, 3.0, 'steelD', seg=10)
    m.cy((1.6, 0.0, 2.85), 1.7, 1.5, 0.25, 'wallL', seg=10)
    m.cy((1.6, 0.0, GY), 0.5, 0.5, -0.15 - GY, 'conc', seg=8, caps=False)
    make('Bk_Rotunda', m, ao)
    # tunnel section: 1 m long along X (stretched by the theme), 2.8 wide, 2.7 tall, a window band each side
    m = new(pal)
    m.bx(0.0, 1.0, -1.4, 1.4, 0.0, 2.7, 'steelD', hull='noside')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, 0.0, 1.0, s * 1.403, 1.0, 1.7, 'glass')
        (fq if s < 0 else bq)(m, 0.0, 1.0, s * 1.406, 0.3, 0.4, 'sky')
    uq(m, 0.0, 1.0, -1.3, 1.3, 2.703, 'wallL')
    make('Bk_Tunnel', m, ao)
    # drive column: two telescopic legs on a wheel bogie (from the apron up to 1.3 m under the departures floor,
    # under the tunnel where it hangs lowest)
    m = new(pal)
    for y in (-0.6, 0.6):
        m.bx(-0.15, 0.15, y - 0.15, y + 0.15, GY + 0.6, -1.3, 'steel', cull='t')
    m.bx(-0.5, 0.5, -1.2, 1.2, GY + 0.35, GY + 0.8, 'steelD')
    for y in (-0.9, 0.9):
        m.cy((-0.22, y, GY + 0.35), 0.35, 0.35, 0.44, 'tire', seg=8, rot=(0, 90, 0))
    make('Bk_Drive', m, ao)
    # cab: a short box with a window, the black bellows canopy at +X (it meets the fuselage), a yellow bumper
    m = new(pal)
    m.bx(-1.2, 1.0, -1.6, 1.6, 0.0, 2.8, 'steelD')
    fq(m, -1.0, 0.6, -1.603, 1.0, 1.9, 'glass')
    bq(m, -1.0, 0.6, 1.603, 1.0, 1.9, 'glass')
    m.bx(1.0, 1.7, -1.5, 1.5, 0.0, 2.75, 'black')
    for k in range(4):
        fq(m, 1.05 + k * 0.17, 1.12 + k * 0.17, -1.503, 0.05, 2.7, 'rubber')
    m.bx(1.0, 1.75, -1.5, 1.5, -0.12, 0.0, 'sun')
    make('Bk_Cab', m, ao)
    # control tower (~46 m): a tapered shaft on a base block, the glass cab (an inverted octagonal frustum), the roof
    # with a radar dome and masts
    m = new(pal)
    m.bx(-6.0, 6.0, -5.0, 5.0, 0.0, 8.0, 'wallL')
    fq(m, -6.0, 6.0, -5.003, 2.0, 6.0, 'screen')
    m.cy((0, 0, 8.0), 3.2, 2.4, 28.0, 'wallW', seg=8, caps=False)
    m.cy((0, 0, 36.0), 2.6, 5.0, 2.0, 'wallL', seg=8)
    m.cy((0, 0, 38.0), 4.6, 5.6, 4.0, 'screen', seg=8, caps=False)
    m.cy((0, 0, 42.0), 5.8, 5.6, 0.6, 'wallW', seg=8)
    m.sp((0, 0, 43.0), 1.4, 'wallW', seg=(8, 4))
    for x in (-3.0, 3.0):
        m.cy((x, 0.0, 42.6), 0.06, 0.06, 4.0, 'red', seg=4, hull='none', caps=False)
    make('Bk_Tower', m, ao)
    # fuel-farm tank and a cargo shed (low boxes far out)
    m = new(pal)
    m.cy((0, 0, 0), 7.0, 7.0, 9.0, 'wallW', seg=12)
    m.cy((0, 0, 9.0), 7.0, 0.5, 1.2, 'wallL', seg=12)
    m.cy((0, 0, 3.0), 7.03, 7.03, 0.6, 'red', seg=12, caps=False, hull='none')
    make('Bk_Tank', m, ao)
    m = new(pal)
    m.bx(-20.0, 20.0, -9.0, 9.0, 0.0, 9.0, 'corr')
    for k in range(5):
        x = -16.0 + k * 8.0
        fq(m, x - 3.0, x + 3.0, -9.003, 0.0, 6.0, 'corrD')
    fq(m, -20.0, 20.0, -9.006, 7.5, 9.0, 'navy')
    text_front(m, 'MERIDIAN CARGO', 1.2, -9.009, 0.0, 7.7, 'paper', maxw=24.0)
    make('Bk_Shed', m, ao)
