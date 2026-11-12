/* Theme: Scoops & Cream (kit-icecream) -- a huge commercial ice cream shop (made-up SCOOPS & CREAM brand) and the
   creamery behind it, under a 7 m ceiling. Two zones:
   1 The Parlour (72 x 60 m): strawberry-pink walls over a mint wainscot with a chocolate-drip band, a pink / cream
     checker floor. Along the north wall the back bar (twin soft-serve machines with swirl signs, back counters, ice
     cream cake freezers) under menu boards and the script SCOOPS & CREAM logo; in front of it three counters with
     gaps between them (the flanking routes): west the sundae / topping bar, a waffle-cone station and a till; in the
     middle the scoop bar of glass-front dipping cabinets (48 tubs in two flavour sets, named tags, enamel repainted
     per copy) with a till and a second sundae bar; east the milkshake bar with diner stools, a waffle-cone station
     and a till. A queue-belt maze in front of the scoop bar, pushcarts, napkin stations, planter-box dividers.
     The landmark GIANT CONE (a 6.8 m waffle cone with strawberry and mint scoops, a chocolate drip and a cherry) on
     a ringed bench plinth in the middle of the floor, under a clear ceiling. Seating: diner booths along the west
     and east walls, a pastel table area of bistro tables with heart-back chairs, the window bar along the shop
     front, the raised TERRACE in the south-west (1.2 m, rails, two flights of steps, lounge sofas and tables: high
     ground over the floor), the kids' corner in the south-east (soft-play tower, crayon tables, bean bags, a mural).
     The player starts in the glass entrance vestibule (automatic doors) at the south.
   2 The Creamery (70 x 58 m), behind the STAFF ONLY door: white tiled walls, a terracotta quarry-tile floor with
     drains and yellow walkway lines (the zone plan's own floor paint). The mix room (mix and ageing tanks, cream
     cans), the churn line (batch freezers facing the aisle), prep tables (mixing, cake decorating), the novelty
     line, two filling lines in the south (tub fillers feeding conveyors of filled tubs), blast freezers along the
     east wall, speed racks, dispatch by the closed DELIVERIES door (pallets of cone / cup / cream-base cartons, wrapped stacks,
     a pallet jack), pallet bays in the south-west, lockers and sinks by the staff entrance. The mezzanine over the
     north-west corner (3.5 m, a steel stair, rails) carries the landmark PARTY ROOM (pink walls, big windows, a
     party table with a giant sundae cake, balloons, bunting) and party tables; under it the walk-in freezer
     (insulated panels, a door with a tied-back strip curtain, frosted shelving) and the dry store.
   Built by blender/fam_kit_icecream.py (ic_*.py); zone layers by tools/icecream_zones.py. No engine changes.

   A zone file has a floor plan and three layers: "@layer 0.01" (floor tiles and marks; on wall cells, wall-art
   codes; the cell (0, 0) holds ',' in the creamery), the raised layer ("@layer 1.2" the terrace, "@layer 3.5" the
   mezzanine) and "@layer 7" (ceiling bays [4, 4], hung from the 7 m ceiling).
   Floor plan, parlour:
     D dipping cabinet [2,2] (front south; two flavour sets in turn, enamel repainted)   k counter end [1,2]
     R till [2,2]   U sundae bar [3,2]   W waffle-cone station [3,2]   Y milkshake bar [3,2] (all front south)
     s diner stool   Q soft-serve machine [2,1]   b back counter [2,1] (three kinds)   F cake freezer [2,1]
       (Q b F back to the wall)   q queue belt (runs)   L GIANT CONE landmark [6,6]   B booth [2,3] (end to the wall)
     t bistro table set [2,2] (four or two heart-back chairs)   f lounge sofa [3,1] (back to the wall)
     n window bar [2,1] (back to the window)   K soft-play tower [4,4]   j kids' crayon table [2,2]   g bean bag
     v planter   c cone bin   x napkin station   < pushcart [2,1]   / planter-box divider [3,1]   O candy-striped column
     e vestibule glass (runs)   d automatic doors [4,1] (in the glass line)   T terrace steps [3,3] rising north
   Terrace (1.2): w deck (solid slab)   l rail (runs)   t f as above
   Floor plan, creamery:
     M batch freezer / churn [2,2] (front south)   V mix / ageing tank [2,2]   X blast freezer [3,2] (back to the wall)
     i insulated panel wall (runs)   J walk-in freezer door [3,1] (in the panel line)   z freezer shelving [2,1]
     H prep table [3,2] (mixing / cake decorating)   A double sink [2,1]   C lockers [2,1]   (z A C back to the wall)
     > tub filler [2,2] (front east, its nozzle over the line)   = filling-line conveyor [3,1]
     p pallet of cartons (cones, cups, cream base)   m empty pallets   Z wrapped carton stack [2,2]   y cream cans
     % pallet jack   | speed rack   N steel stair [2,7] rising north   I deck column   0 kitchen column
   Mezzanine (3.5): u deck   r rail (runs)   o PARTY ROOM landmark [8,5] (faces south)   t party table   4 balloons
   Floor (0.01): : pink checker square   ; chocolate checker square   - walkway line (runs)
     ' floor drain   + entrance mat [3,2]
     Wall-art codes (on wall cells; never a symbol): parlour 1 2 3 menu boards (scoops, cones, sundaes)
       * the SCOOPS & CREAM logo (a run of exactly ten cells)   [ ] shop windows (plain, with a cone decal)
       ( ) posters   { } kids' mural   ! fire point   ^ fire exit;   creamery ! fire point   ^ fire exit
       ? notice board   ` electrical panel   & hand-wash sign   @ extractor louvre   " HAIRNETS ON sign
       ~ wall clock and the churn board   $ DELIVERIES dock door (centre cell; the cells either side are '_')
   Ceiling (7): 5 coffer with a pendant lamp   6 mint coffer   7 sky coffer   8 kitchen T-bar bay   9 ... with a duct */
(function (IB) {
  'use strict';
  var ART = {
    P: { '1': 'WP_MenuA', '2': 'WP_MenuB', '3': 'WP_MenuC', '[': 'WP_WinA', ']': 'WP_WinB', '(': 'WP_PosterA', ')': 'WP_PosterB',
      '{': 'WP_MuralA', '}': 'WP_MuralB', '!': 'WP_Fire', '^': 'WP_Exit' },
    K: { '!': 'WK_Fire', '^': 'WK_Exit', '?': 'WK_Board', '`': 'WK_Panel', '&': 'WK_Wash', '@': 'WK_Vent', '$': 'WK_Dock', '"': 'WK_Safety', '~': 'WK_Clock', '_': null }
  };
  var LOGO = 10;
  function floorOf(grid) {
    if (grid._icF === undefined) {
      grid._icF = null;
      (grid.layers || []).forEach(function (l) { if (!grid._icF && l.y < 1) grid._icF = l; });
    }
    return grid._icF;
  }
  // the SCOOPS & CREAM logo: a run of ten '*' wall cells, each module drawing its slice of the word (read from the
  // viewer's left: the module's local -X end)
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = floorOf(grid), S = F && F.at(0, 0) === ',' ? 'K' : 'P';
    if (face === 'corner' || face === 'none') return 'Corner' + S;
    var code = F ? F.at(c, r) : '.', A = ART[S];
    if (S === 'P' && code === '*' && LEFT[face]) {
      var L = LEFT[face], k = 0;
      while (k < LOGO && F.at(c + L[0] * (k + 1), r + L[1] * (k + 1)) === '*') k++;
      return 'WP_Logo' + Math.min(LOGO - 1, k);
    }
    if (A.hasOwnProperty(code)) return A[code];   // null: a dock door's side cell (the centre module draws the 3 m bay)
    return 'W' + S;
  }
  function flat(pieces, extra) { var d = { pieces: pieces, collide: false }; for (var k in extra || {}) d[k] = extra[k]; return d; }

  // paint jobs (palette cells, blender/ic_base.py order): cabinet enamel, upholstery (+ piping), chair / stool seats,
  // sofas. 8 wallP 9 wallC 10 wallM 11 pinkD 12 mintD 18 cherry 19 lemon 20 sky 21 lilac 22 orange 28 glassL 44 peach
  var ENAMEL = { from: [8], to: [[8], [10], [19], [20], [21], [44]] };
  var UPH = { from: [11, 8], to: [[11, 8], [12, 10], [20, 28], [21, 9], [22, 19], [18, 9]] };
  var SEAT = { from: [21], to: [[21], [20], [19], [10], [8], [22], [12]] };
  var SOFA = { from: [12, 10], to: [[12, 10], [11, 8], [20, 28], [21, 9]] };

  // the creamery's own floor paint (zone plan `floor`): terracotta quarry tiles, 0.5 m, cream grout
  var QUARRY = { color: '#C55E3E', lines: [{ dir: 'x', every: 0.5, width: 0.025, color: '#E9D8C2', y: 0.008 },
    { dir: 'z', every: 0.5, width: 0.025, color: '#E9D8C2', y: 0.0105 }] };

  var SYMBOLS = {
    // ---- the parlour: counters
    'D': { size: [2, 2], pieces: ['Dip_A', 'Dip_B'], sequence: true, face: 0, kind: 'cover', paint: ENAMEL },
    'k': { size: [1, 2], pieces: ['Ctr_End'], face: 0, kind: 'cover' },
    'R': { size: [2, 2], pieces: ['Till'], face: 0, kind: 'cover' },
    'U': { size: [3, 2], pieces: ['Sundae'], face: 0, kind: 'cover' },
    'W': { size: [3, 2], pieces: ['Waffle'], face: 0, kind: 'cover' },
    'Y': { size: [3, 2], pieces: ['ShakeBar'], face: 0, kind: 'cover' },
    's': { pieces: ['Stool'], kind: 'cover', paint: SEAT },
    'Q': { size: [2, 1], pieces: ['SoftServe'], orient: 'wall', kind: 'cover' },
    'b': { size: [2, 1], pieces: ['BackBar_A', 'BackBar_B', 'BackBar_C'], orient: 'wall', kind: 'cover' },
    'F': { size: [2, 1], pieces: ['CakeFreezer'], orient: 'wall', kind: 'cover' },
    'q': { pieces: ['BeltHalf'], full: 'BeltFull', links: 'q', post: 'BeltPost', kind: 'cover' },
    'L': { size: [6, 6], pieces: ['Landmark_Cone'], kind: 'cover' },
    // ---- seating, kids, small props
    'B': { size: [2, 3], pieces: ['Booth'], face: 0, kind: 'cover', paint: UPH },
    't': { size: [2, 2], pieces: ['Table4', 'Table2', 'Table4'], kind: 'cover', paint: SEAT },
    'f': { size: [3, 1], pieces: ['Sofa'], orient: 'wall', kind: 'cover', paint: SOFA },
    'n': { size: [2, 1], pieces: ['WindowBar'], orient: 'wall', kind: 'cover', paint: SEAT },
    'K': { size: [4, 4], pieces: ['Play'], flip: true, kind: 'cover' },
    'j': { size: [2, 2], pieces: ['KidTable'], kind: 'cover' },
    'g': { pieces: ['BeanBag'], rotate: 'random90', kind: 'cover', paint: SEAT },
    'v': { pieces: ['Planter'], kind: 'cover' },
    'c': { pieces: ['Bin'], rotate: 'edge', kind: 'cover' },
    'x': { pieces: ['Napkins'], rotate: 'edge', kind: 'cover' },
    '<': { size: [2, 1], pieces: ['Cart'], flip: true, kind: 'cover' },
    '/': { size: [3, 1], pieces: ['PlanterBox'], kind: 'cover' },
    'O': { pieces: ['Column'], kind: 'cover' },
    'e': { pieces: ['VGlassHalf'], full: 'VGlassFull', links: 'ed#', post: 'VGlassPost', kind: 'wall' },
    'd': { size: [4, 1], pieces: ['VDoor'], orient: 'span', kind: 'wall' },
    'T': { size: [3, 3], pieces: ['Steps'], face: 0, kind: 'step' },
    // ---- the terrace (layer 1.2): a solid slab under every terrace cell
    'w': { deck: { thick: 1.2, color: '#E2BB86', edge: '#EA5C93', under: '#E2BB86', with: '*' } },
    'l': { pieces: ['TRailHalf'], full: 'TRailFull', links: 'l', post: 'TRailPost', kind: 'wall' },
    // ---- the creamery
    'M': { size: [2, 2], pieces: ['Churn'], face: 0, kind: 'cover' },
    'V': { size: [2, 2], pieces: ['MixTank', 'AgeTank'], flip: true, kind: 'cover' },
    'X': { size: [3, 2], pieces: ['BlastFreezer'], orient: 'wall', kind: 'cover' },
    'i': { pieces: ['PanHalf'], full: 'PanFull', links: 'iJ#', post: 'PanPost', kind: 'wall' },
    'J': { size: [3, 1], pieces: ['FreezerDoor'], orient: 'span', kind: 'wall' },
    'z': { size: [2, 1], pieces: ['FreezerShelf'], orient: 'wall', kind: 'cover' },
    'H': { size: [3, 2], pieces: ['PrepTable_A', 'PrepTable_B'], flip: true, kind: 'cover' },
    'A': { size: [2, 1], pieces: ['Sink'], orient: 'wall', kind: 'cover' },
    'C': { size: [2, 1], pieces: ['Lockers'], orient: 'wall', kind: 'cover' },
    'p': { pieces: ['Pal_Cones', 'Pal_Cups', 'Pal_Mix', 'Pal_Cones'], rotate: 'random90', kind: 'cover' },
    'm': { pieces: ['Pal_Empty'], rotate: 'random90', kind: 'cover' },
    'Z': { size: [2, 2], pieces: ['BoxStack'], flip: true, kind: 'cover' },
    '>': { size: [2, 2], pieces: ['Filler'], face: Math.PI / 2, kind: 'cover' },
    '=': { size: [3, 1], pieces: ['Line_A', 'Line_B'], sequence: true, kind: 'cover' },
    'y': { pieces: ['Cans'], rotate: 'random90', kind: 'cover' },
    '%': { pieces: ['PalletJack'], rotate: 'random90', kind: 'cover' },
    '|': { pieces: ['SpeedRack'], rotate: 'random90', kind: 'cover' },
    'N': { size: [2, 7], pieces: ['Stair'], face: 0, kind: 'step' },
    'I': { pieces: ['DeckColumn'], kind: 'cover' },
    '0': { pieces: ['ColumnK'], kind: 'cover' },
    // ---- the mezzanine (layer 3.5)
    'u': { deck: { thick: 0.4, color: '#E9D3DA', edge: '#EA5C93', under: '#DDE3E8', with: '*' } },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    'o': { size: [8, 5], pieces: ['Landmark_Party'], face: 0, kind: 'cover' },
    '4': { pieces: ['Balloons'], kind: 'cover' },
    // ---- floor tiles and marks (layer 0.01)
    ':': flat(['F_Chk']), ';': flat(['F_ChkD']),
    '-': flat(['F_Line'], { rotate: 'run' }), "'": flat(['F_Drain']), '+': flat(['F_Mat'], { size: [3, 2] }),
    // ---- ceiling bays (layer 7)
    '5': flat(['Ceil_A'], { size: [4, 4] }), '6': flat(['Ceil_B'], { size: [4, 4] }), '7': flat(['Ceil_D'], { size: [4, 4] }),
    '8': flat(['Ceil_K'], { size: [4, 4] }), '9': flat(['Ceil_KD'], { size: [4, 4] })
  };

  // glow companions (zones.js theme.glow): glass drawn additive over what is behind it; lamps, screens, the cone's
  // lettering, the windows' daylight drawn unlit
  var GLASS = function (p) { return { piece: p, blend: 'add' }; };
  var GLOW = {
    Dip_A: GLASS('Dip_Glass'), Dip_B: GLASS('Dip_Glass'), Sundae: GLASS('Sundae_Glass'), CakeFreezer: GLASS('CakeFreezer_Glass'),
    VGlassFull: GLASS('VGlassFull_G'), VGlassHalf: GLASS('VGlassHalf_G'), VDoor: GLASS('VDoor_G'), Landmark_Party: GLASS('Landmark_Party_Glass'),
    WP_WinA: { piece: 'WP_Win_LED' }, WP_WinB: { piece: 'WP_Win_LED' }, WP_Exit: { piece: 'W_Exit_LED' }, WK_Exit: { piece: 'W_Exit_LED' },
    GateFrame: { piece: 'GateFrame_LED' }, Ceil_A: { piece: 'Ceil_A_LED' }, Ceil_K: { piece: 'Ceil_K_LED' }, Ceil_KD: { piece: 'Ceil_KD_LED' },
    Till: { piece: 'Till_LED' }, SoftServe: { piece: 'SoftServe_LED' }, Landmark_Cone: { piece: 'Landmark_Cone_LED' },
    Churn: { piece: 'Churn_LED' }, Filler: { piece: 'Filler_LED' }, BlastFreezer: { piece: 'BlastFreezer_LED' }, FreezerDoor: { piece: 'FreezerDoor_LED' }
  };

  var WALLS = ['WP', 'CornerP', 'WK', 'CornerK'];
  for (var lg = 0; lg < LOGO; lg++) WALLS.push('WP_Logo' + lg);
  Object.keys(ART).forEach(function (S) { Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (p && WALLS.indexOf(p) < 0) WALLS.push(p); }); });
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'icecream', name: 'Scoops & Cream', family: 'kit-icecream', prefix: 'KIT_ICECREAM_',
    palette: ['#EA5C93', '#3DBE9A', '#FFE36A', '#FFF3DE'],
    env: {
      sky: null, clear: '#F4E2E8', fog: { color: '#F6E6EA', near: 55, far: 150 }, clouds: false,
      sun: [0.32, 0.86, 0.4],
      ceiling: { height: 7.0, color: '#FFF3DE' }   // coffers, lamps and kitchen bays come from the zone's "@layer 7" grid
    },
    // cream floor tiles with a grout grid every metre (the checker / quarry tiles are floor-layer pieces over it)
    floor: {
      color: '#FBF5EA', trail: '#F1E8DA', outside: '#FBF5EA',
      lines: [{ dir: 'x', every: 1, width: 0.02, color: '#E4D9C7', y: 0.008 }, { dir: 'z', every: 1, width: 0.02, color: '#E4D9C7', y: 0.0105 }]
    },
    wall: { height: 7.0, roof: '#FFF3DE', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 7.0 },
    hatch: 'Hatch', stand: 'Napkins',
    backdrop: null,
    budget: { prop: 1800, landmark: 3000, total: 45000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      icecream: {
        name: 'Scoops & Cream',
        intro: 'Robots have overrun the biggest ice cream shop in town. Clear the parlour from the front doors to the counters, then push through the STAFF ONLY door into the creamery.',
        zones: [
          // the parlour: the seating, the giant cone, the queue and the counters; the first wave is light robots only
          { map: 'icecream_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 5]],
            [['crawler', 14], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['drone', 8], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 4], ['soldier', 7], ['blader', 4]],
            [['crawler', 15], ['gunner', 9], ['drone', 6], ['soldier', 7], ['blader', 4]]] },
          // the creamery: the churn line, the freezers, dispatch and the party room up on the mezzanine
          { map: 'icecream_2', floor: QUARRY, waves: [
            [['crawler', 16], ['gunner', 10], ['drone', 5], ['soldier', 4]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 5], ['blader', 4]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 4]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
