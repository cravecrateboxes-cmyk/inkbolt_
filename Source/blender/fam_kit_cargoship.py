"""INKBOLT asset family: kit-cargoship ("Halcyon Vega", a big container ship at sea, no land in sight).

The kit is split over cargo_base.py (palette, helpers, conventions), cargo_struct.py (walls per zone kind, corners,
the watertight-door gate, stair-trunk walls, the escape hatch, steel stairs, rails, markings, deckhead fittings),
cargo_cargo.py (containers, hold cells with cell guides, lashing bridges, project cargo), cargo_deck.py (deck crane,
mooring gear, vents, davits), cargo_engine.py (main engine, generators, auxiliaries, control room, shaft line) and
cargo_backdrop.py (deckhouse tower, funnel, forecastle and bow, a feeder ship, gulls, sea glints and foam).
Build: python3 build_assets.py --family kit-cargoship
"""
import ib_lib
import cargo_base as B
import cargo_backdrop as BD
import cargo_cargo as CG
import cargo_deck as DK
import cargo_engine as EN
import cargo_struct as S


def build_kit_cargoship(ao):
    pal = ib_lib.Palette(B.FAM)
    S.build_bulwarks(pal, ao)
    S.build_superstructure(pal, ao)
    S.build_forecastle(pal, ao)
    S.build_hold_walls(pal, ao)
    S.build_er_walls(pal, ao)
    S.build_corners(pal, ao)
    S.build_gate(pal, ao)
    S.build_stairs(pal, ao)
    S.build_rails(pal, ao)
    S.build_markings(pal, ao)
    S.build_deckhead(pal, ao)
    CG.build_stacks(pal, ao)
    CG.build_cells(pal, ao)
    CG.build_lashing_bridges(pal, ao)
    CG.build_project(pal, ao)
    DK.build_crane(pal, ao)
    DK.build_mooring(pal, ao)
    DK.build_davits(pal, ao)
    EN.build_main_engine(pal, ao)
    EN.build_generators(pal, ao)
    EN.build_aux(pal, ao)
    EN.build_control_room(pal, ao)
    EN.build_shaft(pal, ao)
    BD.build_deckhouse(pal, ao)
    BD.build_funnel(pal, ao)
    BD.build_forecastle(pal, ao)
    BD.build_small(pal, ao)
    T = B.TRIS
    print('kit-cargoship: %d pieces, %d triangles' % (len(T), sum(T.values())))
    for n in sorted(T, key=lambda k: -T[k])[:40]:
        print('  %-40s %6d' % (n, T[n]))
    ib_lib.export(B.FAM)


FAMILY = 'kit-cargoship'
BUILD = build_kit_cargoship
