"""INKBOLT asset family: weapons (hitscan viewmodels and launchers, melee, gloved arms rig + per-weapon actions, pickups).

Layout: wpn_core.py (palette, shape kit, shared gun parts), wpn_<group>.py (the guns), this file (melee, arms, actions,
pickups, the family build), wpn_arms.py (arms mesh and rig), wpn_anim.py (arm actions).
"""
import math
import os

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from wpn_core import *  # noqa: F401,F403
import wpn_core
from wpn_pistols import build_pip, build_handcannon, build_twintap
from wpn_smgs import build_buzz, build_whisk, build_hornet
from wpn_rifles import build_rivet, build_triplet, build_longtom, build_vanguard
from wpn_heavy import build_brick, build_needle, build_railspike
from wpn_shotguns import build_scrapper, build_thunder
from wpn_launchers import build_hothead, build_murmur
from wpn_arms import *  # noqa: F401,F403
from wpn_anim import *  # noqa: F401,F403


# ================================================================ melee (round 3): struck with V; the gun is put away for the swing
# Weapon space for a melee weapon: the handle runs along the grip axis (+Z up), the hand's web at the origin (top of the
# handle, under the guard), the edge faces +Y. rake 0, so the hand frame IS the weapon frame. Two-handed weapons
# (katana, axe) carry a 'hold2' z: the support hand grips the handle that far below the right hand. The nunchucks'
# second stick is the weapon's 'Mag' part, hanging from the chain end (MAG socket) so the Mag bone can swing it.
def blade(k, st, color, edge='steel'):
    """Blade along +Z from stations (z, y_back, y_edge, half_thick, y_bevel): a flat body (spine at the back, flat
    faces to the bevel line) and a separate edge wedge (bevel line to the sharp edge, toward +Y) in its own colour.
    The last station may have y_back == y_edge: the tip apex."""
    body, wedge = [], []
    for z, yb, ye, t, ys in st:
        if abs(ye - yb) < 1e-6:
            body.append([(0.0, ye, z)])
            wedge.append([(0.0, ye, z)])
            continue
        body.append([(t, ys, z), (t, yb + 0.6 * t, z), (0.6 * t, yb, z), (-0.6 * t, yb, z), (-t, yb + 0.6 * t, z), (-t, ys, z)])
        wedge.append([(0.0, ye, z), (t, ys, z), (-t, ys, z)])
    k.loft(body, color, hull=True)
    k.loft(wedge, edge, hull=True)


def wrap_handle(k, z0, z1, rx, ry, color='ink', diamond='paper', n=6):
    """Wrapped handle: oval core, diamond peeks of the under-layer on the edge sides (y), ink binding."""
    k.lathe([(z0, 0), (z0, 1.0), (z1, 1.0), (z1, 0)], color, 'z', (0, 0, 0), 10, sc=(rx, ry))
    step = (z1 - z0) / n
    for i in range(n):
        z = z0 + step * (i + 0.5)
        for s in (-1, 1):
            k.box((0, s * (ry + 0.0010), z), (rx * 0.9, 0.006, step * 0.42), diamond, rot=(0, 45, 0), skip=('-y' if s > 0 else '+y',))


def build_katana(pal):
    """Mk-1 Ronin Blade: katana. Ink-wrapped two-hand handle, round steel guard, brass collar, curved blade with a
    pale temper line along the edge."""
    k = Kit(pal)
    wrap_handle(k, -0.215, 0.010, 0.015, 0.0195, 'ink', 'sleeve', n=7)
    k.lathe([(-0.235, 0), (-0.235, 0.0120), (-0.228, 0.0170), (-0.215, 0.0170), (-0.215, 0)], 'steel2', 'z', (0, 0, 0), 10, sc=(1.0, 1.25))   # end cap
    k.lathe([(0.010, 0), (0.010, 0.0360), (0.022, 0.0360), (0.022, 0)], 'gunmetal', 'z', (0, 0, 0), 16, sc=(0.85, 1.15))      # guard
    k.lathe([(0.022, 0), (0.022, 0.0260), (0.026, 0.0240), (0.026, 0)], 'amber', 'z', (0, 0, 0), 16, hull=False, sc=(0.85, 1.15))   # seppa washer
    k.cbox((0, 0.0, 0.038), (0.016, 0.036, 0.022), 'brass', ch=0.002)                                         # collar
    st = []
    n = 9
    for i in range(n):
        t = i / (n - 1)
        z = 0.046 + 0.600 * t
        sori = -0.030 * t * t                                       # the blade curves back toward the tip
        w = 0.030 - 0.006 * t
        st.append((z, -0.014 + sori, -0.014 + sori + w, 0.0040 - 0.0012 * t, -0.014 + sori + w * 0.62))
    st.append((0.690, -0.050, -0.050, 0, 0))
    blade(k, st, 'steel', 'paper')
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.30), 'muzzle': (0, -0.050, 0.690), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'hold2': -0.098, 'len': 0.69}


def build_eaxe(pal):
    """VX-7 Voltaxe: electric axe. Long steel shaft with a rubber grip, a heavy head with a battery and teal coils, a
    back spike, glowing edge."""
    k = Kit(pal)
    k.lathe([(-0.300, 0), (-0.300, 0.0150), (0.300, 0.0150), (0.300, 0)], 'steel2', 'z', (0, 0, 0), 10, sc=(1.0, 1.2))     # shaft
    for z0, z1 in ((-0.290, -0.110), (-0.080, 0.016)):
        k.lathe([(z0, 0), (z0, 0.0178), (z1, 0.0178), (z1, 0)], 'gun2', 'z', (0, 0, 0), 10, sc=(1.0, 1.2))                    # rubber grips
        for z in [z0 + 0.012 + j * 0.022 for j in range(int((z1 - z0 - 0.012) / 0.022))]:
            k.ring('z', (0, 0, 0), z, z + 0.006, 0.0172, 0.0210, 'gun3', seg=10, hull=False)
    k.lathe([(-0.316, 0), (-0.316, 0.0200), (-0.300, 0.0220), (-0.292, 0.0160), (-0.292, 0)], 'gunmetal', 'z', (0, 0, 0), 10)  # pommel
    # head (z 0.20 .. 0.32): core block, battery on the back, axe blade forward with a glowing edge, back spike
    k.cbox((0, 0.000, 0.262), (0.044, 0.056, 0.090), 'gunmetal', ch=0.006)
    k.cbox((0, -0.040, 0.262), (0.036, 0.030, 0.060), 'gun3', ch=0.004)
    k.box((0, -0.0565, 0.262), (0.024, 0.006, 0.036), 'lens')
    k.ext_x([(0.026, 0.226), (0.090, 0.180), (0.120, 0.196), (0.130, 0.262), (0.120, 0.330), (0.090, 0.346), (0.026, 0.298)], -0.006, 0.006, 'steel', ch=0.002)
    k.ext_x([(0.116, 0.198), (0.126, 0.192), (0.137, 0.262), (0.126, 0.332), (0.116, 0.326), (0.125, 0.262)], -0.0095, 0.0095, 'lens', hull=False)  # glowing edge
    k.ext_x([(-0.020, 0.248), (-0.090, 0.262), (-0.020, 0.278)], -0.008, 0.008, 'steel2', ch=0.002)   # back spike (through the battery)
    for z in (0.236, 0.262, 0.288):
        k.ring('y', (0, 0, z), 0.031, 0.048, 0.009, 0.0135, 'lens', seg=8, hull=False)                   # coils on the neck
    k.lathe([(0.300, 0), (0.300, 0.012), (0.318, 0.008), (0.326, 0)], 'amber', 'z', (0, 0, 0), 8)
    for s in (-1, 1):
        k.box((s * 0.0255, 0.0, 0.262), (0.006, 0.030, 0.050), 'amber', skip=('-x' if s > 0 else '+x',))   # warning plates
        k.box((s * 0.0255, 0.0, 0.262), (0.013, 0.010, 0.010), 'ink', skip=('-x' if s > 0 else '+x',))
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.40), 'muzzle': (0, 0.130, 0.262), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'hold2': -0.200, 'len': 0.33}


def build_dagger(pal):
    """KN-3 Stinger: combat dagger. Ribbed grip, cross guard, a dark clip-point blade with a bright edge."""
    k = Kit(pal)
    k.lathe([(-0.100, 0), (-0.100, 0.0150), (-0.090, 0.0175), (0.006, 0.0175), (0.006, 0)], 'gun2', 'z', (0, 0, 0), 10, sc=(1.0, 1.25))
    for i in range(4):
        z = -0.078 + i * 0.022
        k.ring('z', (0, 0, 0), z, z + 0.007, 0.0170, 0.0205, 'gun3', seg=10, hull=False)
    k.lathe([(-0.112, 0), (-0.112, 0.012), (-0.100, 0.016), (-0.100, 0)], 'steel2', 'z', (0, 0, 0), 8)          # pommel
    k.cbox((0, 0.0, 0.013), (0.020, 0.090, 0.012), 'gunmetal', ch=0.003)                                      # cross guard
    k.box((0, 0.0, 0.013), (0.027, 0.012, 0.006), 'amber')
    st = []
    n = 5
    for i in range(n):
        t = i / (n - 1)
        z = 0.020 + 0.150 * t
        st.append((z, -0.016 + 0.004 * t, 0.018 - 0.006 * t * t, 0.0042 - 0.0012 * t, 0.006 - 0.004 * t))
    st.append((0.205, -0.004, -0.004, 0, 0))
    blade(k, st, 'gun3', 'steel')
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.30), 'muzzle': (0, -0.004, 0.205), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'len': 0.205}


def stick(k, z0, z1, color):
    """Nunchuck stick along Z: octagonal hardwood with ink end bands and an amber grip wrap."""
    k.lathe([(z0, 0), (z0, 0.0145), (z1, 0.0145), (z1, 0)], color, 'z', (0, 0, 0), 8)
    for z in (z0 + 0.004, z1 - 0.012):
        k.ring('z', (0, 0, 0), z, z + 0.008, 0.0090, 0.0180, 'ink', seg=8, hull=False)
    for i in range(3):
        z = z0 + 0.050 + i * 0.030
        k.ring('z', (0, 0, 0), z, z + 0.012, 0.0090, 0.0176, 'amber', seg=8, hull=False)


def build_nunchucks(pal):
    """NC-2 Twin Strikers: nunchucks. The held stick (top cap and swivel at the hand's web side), a short chain; the
    second stick (the 'Mag' part) hangs from the chain's far end, which is its origin."""
    k = Kit(pal)
    stick(k, -0.205, 0.075, 'amber')
    k.lathe([(0.075, 0), (0.075, 0.0120), (0.088, 0.0060), (0.094, 0)], 'steel', 'z', (0, 0, 0), 8)          # swivel cap
    for i in range(2):                                                                                       # chain links (held half)
        z = 0.104 + i * 0.020
        k.ring('x' if i % 2 else 'y', (0, 0, z), -0.003, 0.003, 0.004, 0.0090, 'steel2', seg=6, hull=True)
    mk = Kit(pal)
    for i in range(2):                                                                                       # chain links (far half)
        z = -0.010 - i * 0.020
        mk.ring('y' if i % 2 else 'x', (0, 0, z), -0.003, 0.003, 0.004, 0.0090, 'steel2', seg=6, hull=True)
    mk.lathe([(-0.060, 0), (-0.060, 0.0060), (-0.054, 0.0120), (-0.046, 0)], 'steel', 'z', (0, 0, 0), 8)
    with mk.at((0, 0, -0.046)):
        stick(mk, -0.280, 0.0, 'amber')
    return k, mk, {'rake': 0, 'mrake': 0, 'mag': (0.042, 0, 0.150), 'muzzle': (0, 0, -0.33), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                   'cls': 'melee', 'len': 0.33}


def build_held(pal):
    """Things the support hand holds (ride the HOLD_L socket on the left hand bone): the frag can and a shotgun shell."""
    k = Kit(pal)                                                    # M-15 Frag Can: tin can grenade, red band, lever, pin ring
    k.lathe([(-0.044, 0), (-0.044, 0.028), (-0.040, 0.032), (0.036, 0.032), (0.040, 0.028), (0.040, 0)], 'gun3', 'z', (0, 0, 0), 12)
    k.ring('z', (0, 0, 0), -0.012, 0.012, 0.030, 0.0350, 'red', seg=12, hull=False)
    k.lathe([(0.040, 0), (0.040, 0.014), (0.054, 0.012), (0.058, 0)], 'gunmetal', 'z', (0, 0, 0), 10)        # fuse head
    k.bar((0.0, 0.010, 0.050), (0.0, 0.036, -0.020), 0.010, 0.004, 'steel2', up=(1, 0, 0))                   # spoon lever
    k.ring('x', (0.012, -0.010, 0.054), -0.0015, 0.0015, 0.007, 0.0105, 'amber', seg=8, hull=False)          # pin ring
    for z in (-0.036, 0.018):
        k.ring('z', (0, 0, 0), z, z + 0.004, 0.0315, 0.0350, 'ink', seg=12, hull=False)
    finish('HELD_Frag', k)
    s = Kit(pal)                                                    # 12-gauge shell: red hull, brass head
    s.lathe([(-0.036, 0), (-0.036, 0.0110), (-0.032, 0.0110), (-0.032, 0.0098), (0.034, 0.0098), (0.036, 0.0080), (0.036, 0)], 'red', 'z', (0, 0, 0), 10,
            bands=[None, 'brass', 'brass', None, None, None])
    s.ring('z', (0, 0, 0), -0.030, -0.018, 0.0050, 0.0128, 'brass', seg=10, hull=False)
    finish('HELD_Shell', s)


GUNS = {'PIP': build_pip, 'HANDCANNON': build_handcannon, 'TWINTAP': build_twintap, 'BUZZ': build_buzz, 'WHISK': build_whisk,
        'HORNET': build_hornet, 'RIVET': build_rivet, 'TRIPLET': build_triplet, 'LONGTOM': build_longtom, 'BRICK': build_brick,
        'NEEDLE': build_needle, 'SCRAPPER': build_scrapper, 'THUNDER': build_thunder, 'VANGUARD': build_vanguard,
        'RAILSPIKE': build_railspike, 'HOTHEAD': build_hothead, 'MURMUR': build_murmur, 'KATANA': build_katana, 'EAXE': build_eaxe, 'DAGGER': build_dagger, 'NUNCHUCKS': build_nunchucks}
MELEE = [w for w in ('KATANA', 'EAXE', 'DAGGER', 'NUNCHUCKS')]


def build_weapon_meshes(pal):
    for wid, fn in GUNS.items():
        build_weapon(wid, fn, pal, gun=wid not in MELEE)


# ================================================================ pickups
def build_pickups(pal):
    # gem: brilliant-cut, 8 sides, two-tone facets (tinted per gem type by instance colour)
    k = Kit(pal)
    n = 8
    rings = [[(0.09 * math.cos(2 * math.pi * i / n), 0.09 * math.sin(2 * math.pi * i / n), 0.17) for i in range(n)],
             [(0.16 * math.cos(2 * math.pi * (i + 0.5) / n), 0.16 * math.sin(2 * math.pi * (i + 0.5) / n), 0.10) for i in range(n)], [(0, 0, -0.18)]]
    k.loft(rings, 'chip', hull=True, caps=(True, False))
    for i, f in enumerate([f for f in k.bm.faces if len(f.verts) == 4]):
        if i % 2:
            f.material_index = pal.index('chip2')
    finish('PICKUP_Gem', k, ht=0.02)
    # ammo box: steel can with lid, handle, latch, label with three rounds
    k = Kit(pal)
    k.cbox((0, 0, 0.21), (0.60, 0.38, 0.42), 'ammo', ch=0.03, axis='z')
    k.cbox((0, 0, 0.445), (0.64, 0.42, 0.07), 'ammo2', ch=0.02, axis='z')
    k.box((0, 0, 0.495), (0.24, 0.06, 0.03), 'ink')
    k.cbox((0, 0, 0.52), (0.30, 0.08, 0.04), 'ammo3', ch=0.012, axis='y')
    k.box((0.30, 0, 0.345), (0.08, 0.16, 0.12), 'ammo3')
    k.box((0, -0.205, 0.21), (0.36, 0.06, 0.20), 'paper')
    for i in (-1, 0, 1):
        k.lathe([(0, 0), (0, 0.03), (0.09, 0.03), (0.13, 0.0)], 'brass', 'z', (i * 0.1, -0.24, 0.145), 6, hull=False)
    k.box((0, 0, 0.12), (0.66, 0.44, 0.04), 'ammo2')
    finish('PICKUP_Ammo', k, ht=0.018)
    # health can: canister with rim bands, cap and a white heart (no cross or plus sign anywhere in the game world)
    k = Kit(pal)
    k.lathe([(0, 0), (0, 0.19), (0.46, 0.19), (0.50, 0.15), (0.50, 0)], 'health', 'z', (0, 0, 0), 8, a0=0)
    k.ring('z', (0, 0, 0), 0.06, 0.12, 0.17, 0.215, 'health2', seg=10, hull=False)
    k.lathe([(0.49, 0), (0.49, 0.10), (0.58, 0.10), (0.58, 0)], 'health3', 'z', (0, 0, 0), 8, hull=False)
    heart = [(0, -0.10), (0.085, -0.02), (0.105, 0.03), (0.095, 0.075), (0.06, 0.10), (0.025, 0.09), (0, 0.06),
             (-0.025, 0.09), (-0.06, 0.10), (-0.095, 0.075), (-0.105, 0.03), (-0.085, -0.02)]
    k.ext_y(heart, -0.20, -0.17, 'paper', z=0.25, hull=False)
    finish('PICKUP_Health', k, ht=0.018)
    # rocket ammo crate (launchers only; soldiers drop it): olive crate, rope handles, a stencilled rocket on the
    # front, two red-tipped rockets strapped on the lid
    k = Kit(pal)
    k.cbox((0, 0, 0.17), (0.66, 0.40, 0.34), 'olive', ch=0.03, axis='z')
    k.cbox((0, 0, 0.355), (0.70, 0.44, 0.06), 'olive2', ch=0.02, axis='z')
    k.box((0, 0, 0.10), (0.72, 0.46, 0.05), 'olive2')
    for x in (-0.24, 0.24):
        k.box((x, 0, 0.21), (0.05, 0.47, 0.25), 'olive2')
    k.box((0, -0.205, 0.21), (0.30, 0.03, 0.16), 'paper', hull=False)
    k.box((-0.02, -0.225, 0.21), (0.16, 0.02, 0.04), 'red', hull=False)          # stencil: rocket body
    k.box((0.075, -0.225, 0.21), (0.04, 0.03, 0.025), 'ink', hull=False)         # nose
    k.box((-0.11, -0.225, 0.21), (0.03, 0.026, 0.08), 'ink', hull=False)         # fins
    for y in (-0.08, 0.08):
        k.lathe([(-0.26, 0), (-0.26, 0.042), (0.16, 0.042), (0.21, 0.030), (0.25, 0)], 'paper', 'x', (0, y, 0.425), 8,
                bands=[None, None, 'red', 'red'])
        k.ring('x', (0, y, 0.425), -0.20, -0.17, 0.038, 0.048, 'amber', seg=8, hull=False)
    k.box((0, 0, 0.425), (0.06, 0.32, 0.10), 'ink')                                 # strap
    finish('PICKUP_Rockets', k, ht=0.018)
    # launcher round in flight (game/launchers.js scales it per launcher): paper body, red warhead, ink fins, amber band
    k = Kit(pal)
    k.lathe([(-0.22, 0), (-0.22, 0.050), (0.14, 0.055), (0.20, 0.050), (0.29, 0)], 'paper', 'y', (0, 0, 0), 8,
            bands=[None, None, 'red', 'red'])
    k.ring('y', (0, 0, 0), -0.06, -0.02, 0.040, 0.056, 'amber', seg=8, hull=False)
    for a in (45, 135, 225, 315):
        with k.at((0, 0, 0), (0, a, 0)):
            k.box((0.055, -0.16, 0), (0.07, 0.10, 0.012), 'ink', hull=True)
    k.lathe([(-0.26, 0), (-0.26, 0.032), (-0.21, 0.036), (-0.21, 0)], 'gunmetal', 'y', (0, 0, 0), 8, bands=['ink', None, None])
    finish('PROJ_Rocket', k, ht=0.012)


def hold_socket(rig):
    """HOLD_L: an empty on the left hand bone where held things sit (the frag can, a shotgun shell): on the support
    glove's grip axis, in the closed fist, upright along the grip axis."""
    e = bpy.data.objects.new('HOLD_L', None)
    e.empty_display_size = 0.02
    bpy.context.scene.collection.objects.link(e)
    e.parent = rig
    e.parent_type = 'BONE'
    e.parent_bone = 'HAND_L'
    bpy.context.view_layer.update()
    e.matrix_world = rig.matrix_world @ RIG['F0']['L'] @ T((0.0, HAND['cy'], -0.046))


def build_scene():
    """Everything in the weapons GLB, in the current (fresh) scene; returns (palette, rig, arms)."""
    pal = Palette('weapons')
    build_weapon_meshes(pal)
    build_pickups(pal)
    build_held(pal)
    rig, arms = build_arms(pal)
    hold_socket(rig)
    fit_support()
    for wid, info in WEAPONS.items():
        if 'curl_L' in info:
            print('support hold %-10s offset %s curl %+.0f' % (wid, tuple(round(c, 3) for c in info['hold_L'].translation), info['curl_L']))
    build_actions(rig)
    return pal, rig, arms


def build_weapons(ao):
    build_scene()
    export('weapons')


FAMILY = 'weapons'
BUILD = build_weapons
