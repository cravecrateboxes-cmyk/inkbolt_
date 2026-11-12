/* Theme: Topsy Toyworks (kit-toyfactory) -- a bright toy factory (made-up TOPSY brand: BLOKKO bricks, QUACKERS
   ducks, ROBO-PAL wind-up robots) under a 12 m steel deck roof on open-web joists, skylights and high-bay lamps, a
   ribbon of translucent clerestory panels round the walls. Two zones:
   1 Production Floor (76 x 66 m): three assembly lines run west to east (moving belts carry building bricks and
     alphabet blocks on line A, rubber ducks on line B, wind-up robots and faceless plush bears on line C), split by
     the main aisle, with robot arms, assembly benches, andon lights and tote racks along them; each line ends in its
     packaging machine (case packer, shrink-wrap tunnel, labeller). Moulding machines stand along the west wall under
     the overhead pellet pipes, fed from the pellet loft (a 3.5 m deck in the north-west with dryers, pellets and
     sacks; two stairs). The packing strip in the north-east: a carton roller line runs north through the TO
     WAREHOUSE chute, pack benches, pallets of boxed toys, a wrapper. The paint shop (two booths, drying racks) in the
     south-west, the plush stuffing machine at line C's head, and the showpiece workshop in the south: the landmark
     ROBO-PAL MAX (a 9 m wind-up robot on its plinth), a giant rocking horse with its scaffold, a giant spinning top
     (it spins), giant bricks, alphabet blocks and paint pots on a play mat.
   2 Warehouse (76 x 64 m): four rows of 9.6 m pallet racks full of printed toy cartons in the west block (a cross
     aisle, aisle boards), block-stacked pallets and the returns cage in the north-west, forklifts (kit-parking) and
     pallet stacks in the main aisle, the sortation line bringing cartons in from production through the south wall,
     seven dock doors on the east wall (four with a TOPSY trailer backed in) with staging lanes, the forklift
     chargers on the south wall, and the landmark dispatch office on the 3.5 m mezzanine (pick + pack stations under
     it, two stairs) with the giant TOPSY mascot bear sitting on its roof.
   Built by blender/fam_kit_toyfactory.py (tf_*.py); zone layers by tools/toyfactory_zones.py. Forklifts, pallet
   stacks, drums and bins are kit-parking pieces (theme option `families`).

   A zone file has a floor plan and six layers: "@layer 0.01" (floor marks), "@layer 0.02" (wall-art codes on the
   wall cells: a data layer, theme.dataLayers; cell (0, 0) holds ',' in the warehouse), "@layer 3.5" (the decks),
   "@layer 4.2" (overhead pipes), "@layer 12" (roof bays) and a second "@layer 12" (hanging boards).
   Floor plan:  = ~ -  belts of lines A / B / C (runs, moving; feed and exit hoods at the run ends)
     r carton roller line to the north chute (zone 1)   z sortation line from the south chute (zone 2)
     y robot arm facing south   Y facing north   k assembly bench [2,1] facing south   K facing north
     t tote flow rack [2,1]   A andon light   c parts cart   u tote stack   O steel column
     M moulding machine [5,2] (back to the wall; three colourways)   g gaylord of parts   p pellet gaylord
     q pellet sacks   i deck column   s stair [2,7] rising north   l stair [7,2] rising west
     B paint booth [4,4] (back to the wall)   R drying rack [2,1]   n paint drums
     U case packer   V shrink-wrap tunnel   L labeller [6,3] (line enters at the west end)
     b pack bench [1,2] facing east   o pallet of boxed toys   f flat cartons   W stretch wrapper [2,2]   j pallet jack
     Z plush stuffing machine [3,3]   H ROBO-PAL MAX [6,6] (landmark)   Q giant rocking horse [6,3]   F scaffold [2,2]
     T giant spinning top [3,3] (the top spins: a conveyor path)   I giant brick [2,2]   J giant 2x4 brick [4,2]
     e alphabet blocks   w giant paint pot
     N tall rack row [3,2] (runs N-S)   C returns cage [2,2]   m pick + pack station [2,2]   $ forklift chargers [2,1]
     X forklift [2,3]   x pallet stack [2,2]   ` drums   v bins [2,1] (kit-parking)
   Deck (3.5): d deck   + guard rail (runs)   @ dispatch office [8,5] (landmark)   D pellet dryer [2,2] (and p q o)
   Pipes (4.2): | pellet pipes (runs)
   Floor marks (0.01): ^ yellow aisle line (runs)   % green walkway   / keep-clear hatch   & play mat
   Wall art (0.02, data): f fire point  > fire exit  ` electrical panel  ? safety board  ( ) toy banners  c chute
     ] dock door with a trailer (centre cell; the cells either side are '_')  [ closed dock door  * the TOPSY TOYWORKS
     logo (a run of exactly eight cells)
   Roof (12): 1 joist bay [4,4]  2 bay with a high-bay lamp  3 skylight  4 girder bay  5 girder + lamp
     6 7 8 line boards A / B / C   9 ( ) [ ] { } < department boards   0 ! ? : ; , aisle boards 1 - 6 */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var ART = {
    P: { f: 'WP_Fire', '>': 'WP_Exit', '`': 'WP_Panel', '?': 'WP_Board', '(': 'WP_BanA', ')': 'WP_BanB', c: 'WP_Chute' },
    K: { f: 'WK_Fire', '>': 'WK_Exit', '`': 'WK_Panel', '?': 'WK_Board', ']': 'WK_Dock', '[': 'WK_DockShut', '_': null, c: 'WK_Chute' }
  };
  function artOf(grid) {
    if (grid._tfA === undefined) {
      grid._tfA = null;
      (grid.layers || []).forEach(function (l) { if (Math.abs(l.y - 0.02) < 1e-6) grid._tfA = l; });
    }
    return grid._tfA;
  }
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };
  var FRONT = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  // a pilaster (steel column standing 0.86 m out of the wall) every 6 m along the zone edge, only where the floor in
  // front of it and either side is open and the wall runs on straight either side (never by a gate or a corner)
  function pilasterOK(grid, c, r, face) {
    var F = FRONT[face], L = LEFT[face];
    if (!F) return false;
    for (var k = -1; k <= 1; k++) {
      if (grid.at(c + L[0] * k, r + L[1] * k) !== '#') return false;
      if (grid.at(c + L[0] * k + F[0], r + L[1] * k + F[1]) !== '.') return false;
    }
    for (k = -3; k <= 3; k++) if ('GE'.indexOf(grid.at(c + L[0] * k, r + L[1] * k)) >= 0) return false;
    return true;
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var A = artOf(grid), S = A && A.at(0, 0) === ',' ? 'K' : 'P';
    if (face === 'corner' || face === 'none') return 'Corner' + S;
    var code = A ? A.at(c, r) : '.', T = ART[S];
    if (code === '*' && LEFT[face] && S === 'P') {
      var L = LEFT[face], k = 0;
      while (k < 8 && A.at(c + L[0] * (k + 1), r + L[1] * (k + 1)) === '*') k++;
      return 'WP_Logo' + Math.min(7, k);
    }
    if (T.hasOwnProperty(code)) return T[code];   // null: a dock door's side cell (the centre module draws the 3 m bay)
    var edge = c === 0 || r === 0 || c === grid.w - 1 || r === grid.h - 1, u = (face === 'S' || face === 'N') ? c : r;
    if (edge && u % 6 === 3 && pilasterOK(grid, c, r, face)) return 'W' + S + '_Col';
    return 'W' + S;
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }

  // toy and carton colours: the kit models goods in four cells (gA - gD, 30 - 33) and the theme deals each placed copy
  // one of these mixes of the toy colours (30 - 42: red, blue, yellow, green, orange, purple, white, black, pink, teal,
  // brown, lime, sky)
  var MIX = [[30, 31, 32, 33], [34, 35, 36, 31], [38, 32, 30, 39], [33, 41, 34, 31], [38, 31, 42, 32], [39, 36, 33, 30],
    [31, 34, 38, 35], [32, 30, 38, 41], [36, 30, 42, 39], [35, 33, 34, 36], [30, 39, 41, 31], [42, 38, 32, 35]];
  var GOODS = { from: [30, 31, 32, 33], to: MIX };
  // giant bricks and pots: one bright colour each (never black, white or brown)
  var BRIGHT = { from: [30, 31, 32, 33], to: [[30, 31, 32, 33], [31, 32, 33, 30], [32, 33, 30, 31], [33, 30, 31, 32], [34, 31, 32, 30], [35, 32, 30, 33], [38, 33, 31, 32], [39, 30, 32, 31]] };
  var MACHINE = { from: [56], to: [[56], [57], [35]] };   // moulding machines in Topsy blue, teal or purple
  var RACK = ['Tall_EndL', 'Tall_A', 'Tall_EndR'];
  var KP = 'KIT_PARKING_';
  var BT = 0.86;   // belt top (tf_base.BELT)

  function belt(items, speed) {
    return { pieces: ['Belt'], rotate: 'run', kind: 'cover',
      conveyor: { speed: speed, dir: 1, y: BT + 0.014, spacing: 2.0, inset: 0.1, ends: { start: 'Belt_Feed', end: 'Belt_Exit', at: 0.5 },
        items: items, cleat: 'Belt_Cleat', cleatEvery: 1.0, cleatY: BT + 0.002, carry: { top: 0.98, width: 0.9 } } };
  }
  // the spinning top: one top runs round a 12 cm circle at the plinth's centre, facing along it -- it spins about
  // 1.5 turns a second and wobbles
  var SPIN = []; for (var sp = 0; sp < 12; sp++) SPIN.push([Math.cos(-sp / 12 * 2 * Math.PI) * 0.12, Math.sin(-sp / 12 * 2 * Math.PI) * 0.12]);

  var SYMBOLS = {
    // ---- production floor: the lines
    '=': belt(['Toy_Bricks', 'Toy_ABC'], 0.55),
    '~': belt(['Toy_Duck'], 0.5),
    '-': belt(['Toy_Robot', 'Toy_Bear'], 0.45),
    'r': { pieces: ['Rollers'], rotate: 'run', kind: 'cover',
           conveyor: { speed: 0.5, dir: 1, y: BT, spacing: 1.8, inset: 0, ends: { start: 'Belt_Feed', at: 0.5 }, items: ['Box_A', 'Box_B', 'Box_C'] } },
    'y': { pieces: ['Arm'], rotate: 0, kind: 'cover' },
    'Y': { pieces: ['Arm'], rotate: Math.PI, kind: 'cover' },
    'k': { size: [2, 1], pieces: ['Bench_A'], face: 0, kind: 'cover' },
    'K': { size: [2, 1], pieces: ['Bench_A'], face: Math.PI, kind: 'cover' },
    't': { size: [2, 1], pieces: ['Totes'], flip: true, kind: 'cover' },
    'A': { pieces: ['Andon'], kind: 'cover' },
    'c': { pieces: ['Cart_A'], rotate: 'random90', kind: 'cover' },
    'u': { pieces: ['ToteStack'], rotate: 'random90', kind: 'cover' },
    'O': { pieces: ['Column'], kind: 'cover' },
    // moulding and the pellet loft
    'M': { size: [5, 2], pieces: ['Mould'], orient: 'wall', kind: 'cover', paint: MACHINE },
    'g': { pieces: ['Gay_Parts'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'p': { pieces: ['Pellets'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'q': { pieces: ['Sacks'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'D': { size: [2, 2], pieces: ['Dryer'], face: 0, kind: 'cover' },
    'i': { pieces: ['DeckColumn'], kind: 'cover' },
    's': { size: [2, 7], pieces: ['Stair'], face: 0, kind: 'step' },
    'l': { size: [2, 7], pieces: ['Stair'], face: R90, kind: 'step' },
    // paint shop, packing, plush
    'B': { size: [4, 4], pieces: ['Booth'], orient: 'wall', kind: 'cover' },
    'R': { size: [2, 1], pieces: ['DryRack'], flip: true, kind: 'cover', paint: BRIGHT },
    'n': { pieces: ['PaintCans'], rotate: 'random90', kind: 'cover', paint: BRIGHT },
    'U': { size: [6, 3], pieces: ['Boxer'], face: 0, kind: 'cover' },
    'V': { size: [6, 3], pieces: ['Shrink'], face: 0, kind: 'cover' },
    'L': { size: [6, 3], pieces: ['Labeller'], face: 0, kind: 'cover' },
    'b': { size: [2, 1], pieces: ['PackBench'], face: R90, kind: 'cover' },
    'o': { pieces: ['PalToys_A', 'PalToys_B', 'PalToys_C'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'f': { pieces: ['PalFlat'], rotate: 'random90', kind: 'cover' },
    'W': { size: [2, 2], pieces: ['Wrapper'], flip: true, kind: 'cover', paint: GOODS },
    'j': { pieces: ['PalletJack'], rotate: 'random90', kind: 'cover' },
    'Z': { size: [3, 3], pieces: ['Stuffer'], face: 0, kind: 'cover' },
    // the showpiece workshop
    'H': { size: [6, 6], pieces: ['Landmark_Robot'], face: 0, kind: 'cover' },
    'Q': { size: [6, 3], pieces: ['Horse'], flip: true, kind: 'cover' },
    'F': { size: [2, 2], pieces: ['Scaffold'], kind: 'cover' },
    'T': { size: [3, 3], pieces: ['TopBase'], kind: 'cover', conveyor: { path: SPIN, speed: 1.13, n: 1, y: 0.163, items: ['Top_Spin'] } },
    'I': { size: [2, 2], pieces: ['Brick_A'], rotate: 0, kind: 'cover', paint: BRIGHT },
    'J': { size: [4, 2], pieces: ['Brick_Long'], flip: true, kind: 'cover', paint: BRIGHT },
    'e': { pieces: ['ABC_1', 'ABC_2', 'ABC_1'], rotate: 'random90', kind: 'cover' },
    'w': { pieces: ['PaintPot'], rotate: 'random90', kind: 'cover', paint: BRIGHT },
    // ---- warehouse
    'N': { size: [3, 2], pieces: RACK, sequence: 'run', kind: 'cover', paint: GOODS },
    'z': { pieces: ['Rollers'], rotate: 'run', kind: 'cover',
           conveyor: { speed: 0.5, dir: 1, y: BT, spacing: 1.8, inset: 0, ends: { end: 'Belt_Exit', at: 0.5 }, items: ['Box_B', 'Box_C', 'Box_A'] } },
    'C': { size: [2, 2], pieces: ['Cage'], flip: true, kind: 'cover', paint: GOODS },
    'm': { size: [2, 2], pieces: ['PackStation_A'], face: 0, kind: 'cover' },
    '$': { size: [2, 1], pieces: ['Charger'], orient: 'wall', kind: 'cover' },
    'X': { size: [2, 3], pieces: [KP + 'Forklift'], flip: true, kind: 'cover' },
    'x': { size: [2, 2], pieces: [KP + 'Pallets'], flip: true, kind: 'cover' },
    '`': { pieces: [KP + 'Drums'], rotate: 'random90', kind: 'cover' },
    'v': { size: [2, 1], pieces: [KP + 'Bins'], flip: true, kind: 'cover' },
    // ---- decks (layer 3.5)
    'd': { deck: { thick: 0.4, color: '#B9C2CB', edge: '#F7C531', under: '#D6DCE3', with: '*' } },
    '+': { pieces: ['RailHalf'], full: 'RailFull', links: '+', post: 'RailPost', kind: 'wall' },
    '@': { size: [8, 5], pieces: ['Landmark_Office'], face: 0, kind: 'cover' },
    // ---- overhead pipes (layer 4.2)
    '|': { pieces: ['Pipe'], rotate: 'run', collide: false },
    // ---- floor marks (layer 0.01)
    '^': { pieces: ['F_Line'], rotate: 'run', collide: false },
    '%': flat(['F_Walk']), '/': flat(['F_Hatch']), '&': flat(['F_Mat']),
    // ---- roof (layer 12): bays and hanging boards
    '1': { size: [4, 4], pieces: ['Roof_J'], collide: false }, '2': { size: [4, 4], pieces: ['Roof_L'], collide: false },
    '3': { size: [4, 4], pieces: ['Roof_S'], collide: false }, '4': { size: [4, 4], pieces: ['Roof_G'], collide: false },
    '5': { size: [4, 4], pieces: ['Roof_GL'], collide: false },
    '6': flat(['Line_A']), '7': flat(['Line_B']), '8': flat(['Line_C']),
    '9': flat(['Dept_Moulding'], R90), '(': flat(['Dept_Paint'], R90), ')': flat(['Dept_Packing'], R90), '[': flat(['Dept_Workshop']),
    ']': flat(['Dept_Loft']), '{': flat(['Dept_Shipping'], R90), '}': flat(['Dept_Pick']), '<': flat(['Dept_Plush']),
    '0': flat(['Aisle_1']), '!': flat(['Aisle_2']), '?': flat(['Aisle_3']), ':': flat(['Aisle_4']), ';': flat(['Aisle_5']), ',': flat(['Aisle_6'])
  };

  // glow companions (zones.js theme.glow): clerestory panes, lamp lenses, skylights, screens, andon lamps
  var GLOW = {
    GateFrame: { piece: 'GateFrame_LED' }, Roof_L: { piece: 'Roof_L_LED' }, Roof_GL: { piece: 'Roof_GL_LED' }, Roof_S: { piece: 'Roof_S_LED' },
    Bench_A: { piece: 'Bench_A_LED' }, Andon: { piece: 'Andon_LED' }, Mould: { piece: 'Mould_LED' }, Dryer: { piece: 'Dryer_LED' },
    Booth: { piece: 'Booth_LED' }, Boxer: { piece: 'Boxer_LED' }, Shrink: { piece: 'Shrink_LED' }, Labeller: { piece: 'Labeller_LED' },
    PackBench: { piece: 'PackBench_LED' }, Stuffer: { piece: 'Stuffer_LED' }, Landmark_Robot: { piece: 'Landmark_Robot_LED' },
    Landmark_Office: { piece: 'Landmark_Office_LED' }, PackStation_A: { piece: 'PackStation_A_LED' }, Charger: { piece: 'Charger_LED' },
    WK_Dock: { piece: 'WinK3' }, WK_DockShut: { piece: 'WinK3' }
  };

  var WALLS = ['WP', 'WP_Col', 'CornerP', 'WK', 'WK_Col', 'CornerK'];
  for (var lg = 0; lg < 8; lg++) WALLS.push('WP_Logo' + lg);
  Object.keys(ART).forEach(function (S) { Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (p && WALLS.indexOf(p) < 0) WALLS.push(p); }); });
  // every wall module but the corners and the docks carries the clerestory / daylight band
  WALLS.forEach(function (w) { if (!GLOW[w] && !/^Corner/.test(w)) GLOW[w] = { piece: w.charAt(1) === 'P' ? 'WinP' : 'WinK' }; });
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Stand']);
  var BORROWED = [];   // kit-parking pieces (named in full; tests check they exist in fps-kit-parking.glb)
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : [], IB.conveyorPieces ? IB.conveyorPieces(d.conveyor) : []).forEach(function (n) {
      if (n.indexOf(KP) === 0) { if (BORROWED.indexOf(n) < 0) BORROWED.push(n); } else if (PIECES.indexOf(n) < 0) PIECES.push(n);
    });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'toyfactory', name: 'Topsy Toyworks', family: 'kit-toyfactory', prefix: 'KIT_TOYFACTORY_', families: ['kit-parking'],
    palette: ['#E5392F', '#2D64D8', '#F7C531', '#F3EBD8'],
    env: {
      sky: null, clear: '#C9D2DA', fog: { color: '#D7DEE4', near: 55, far: 150 }, clouds: false,
      sun: [0.3, 0.86, 0.42],
      ceiling: { height: 12.0, color: '#AEB6BE' }   // roof bays and boards come from the zone's "@layer 12" grids
    },
    // pale epoxy with saw-cut joints every 4 m (the warehouse: bare concrete, its own zone floor)
    floor: {
      color: '#DADBD4', trail: '#D0D0C8', outside: '#DADBD4',
      lines: [{ dir: 'x', every: 4, width: 0.02, color: '#BDBDB4', y: 0.008 }, { dir: 'z', every: 4, width: 0.02, color: '#BDBDB4', y: 0.0105 }]
    },
    wall: { height: 12.0, roof: '#AEB6BE', facing: 'open', choose: chooseWall, cols: true },
    dataLayers: [0.02],
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 12.0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: null,
    budget: { prop: 2500, landmark: 2600, total: 46000 },
    allPieces: function () { return PIECES.slice(); },
    borrowed: function () { return BORROWED.slice(); },
    levels: {
      toyfactory: {
        name: 'Topsy Toyworks',
        intro: 'Robots have taken over the Topsy toy factory. Clear the production floor between the running lines, then fight through the warehouse racks to the docks.',
        zones: [
          // Production Floor: the lines, moulding, the pellet loft, packing, the paint shop and the showpiece workshop
          { map: 'toyfactory_1', label: 'The production floor', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 5]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 6], ['blader', 5]],
            [['crawler', 15], ['drone', 6], ['gunner', 10], ['soldier', 6], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['drone', 4], ['soldier', 7], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['drone', 6], ['soldier', 8], ['blader', 4]]] },
          // Warehouse: the racks, the main aisle, the docks and the dispatch mezzanine
          { map: 'toyfactory_2', label: 'The warehouse',
            floor: { color: '#CBC8C0', trail: '#C2BFB6', lines: [{ dir: 'x', every: 4, width: 0.02, color: '#A9A59C', y: 0.008 }, { dir: 'z', every: 4, width: 0.02, color: '#A9A59C', y: 0.0105 }] },
            waves: [
              [['crawler', 18], ['gunner', 10], ['drone', 5], ['soldier', 6]],
              [['crawler', 16], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 5]],
              [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 7], ['blader', 4]],
              [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 4]],
              [['crawler', 17], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 2], ['blader', 4]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
