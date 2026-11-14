/* Theme: BULKBARN Warehouse Club (kit-megastore) -- the inside of a huge warehouse store (made-up BULKBARN brand) under
   a 10 m steel deck roof on open-web joists, with skylights, high-bay lamps and hanging aisle signs. Two zones:
   1 Sales Floor (80 m wide): eight rows of 5.6 m pallet racks (goods on the shelves, shrink-wrapped pallets above)
     in two blocks with a cross aisle, endcaps at every row end; produce and walk-in coolers in the north-west, dairy
     and drink coolers along the back wall, electronics with a TV wall and apparel in the east, the pharmacy / optical
     counter on the west wall, freezer bunkers and pallet drops in the front aisle, a row of checkout lanes, cart
     corrals, the entrance vestibule (the player starts inside) and the landmark BULKBARN CAFE food court.
   2 Stockroom (72 m wide), behind the EMPLOYEES ONLY doors: 9 m racks, forklifts and pallet jacks, seven dock doors
     on the east wall (four with a trailer backed in), a baler with cardboard bales, a stretch wrapper, the break room
     under the mezzanine and the landmark receiving office up on the mezzanine deck (a steel stair: high ground).
   Built by blender/fam_kit_megastore.py (ms_*.py); zone layers by tools/megastore_zones.py. Forklifts, pallet stacks,
   drums and bins are kit-parking pieces (theme option `families`).

   A zone file has a floor plan and three layers: "@layer 0.01" (floor marks; on wall cells, wall-art codes; the
   cell (0, 0) holds ',' in the stockroom), "@layer 3.5" (the mezzanine deck) and "@layer 10" (roof bays and hanging
   signs, from the 10 m roof plane).
   Floor plan:  R sales rack row [3,2] (runs N-S, capped by end frames)   T stockroom rack row [3,2]
     n s endcap [2,1] facing north / south   p floor pallet (water, tissue, TVs, mixed, sacks)   l low pallet
     m empty pallet stack   F freezer bunker [4,2]   V produce stand [2,2]   K electronics demo table [3,2]
     A apparel table [2,2]   Q round clothes rail [2,2]   H pharmacy / optical counter [8,3] (back to the wall)
     L checkout lane [3,5] (exit south)   c shopping cart (some knocked over)   C cart corral [4,1]
     q vestibule glass (runs)   D automatic doors [4,1] (in the glass line)   g greeter podium
     Z BULKBARN CAFE counter [10,4] (back to the wall)   t cafe table [2,2]   O steel column
     j pallet jack   X forklift [2,3] (kit-parking)   x pallet stack [2,2] (kit-parking)   k drums (kit-parking)
     w bins [2,1] (kit-parking)   B baler [2,2]   b cardboard bale   y gaylord   W stretch wrapper [2,2]
     M break table [2,2]   v vending machine (against a wall)   U lockers [2,1]   Y kitchenette [3,1]
     i block partition (runs)   J break-room door [3,1] (in the partition line)   N steel stair [2,7] rising north
     I deck column
   Mezzanine (3.5): u deck   r guard rail (runs)   o receiving office [8,5] (faces south)
   Floor marks (0.01): - yellow aisle line (runs)   z green walkway   / keep-clear hatch   + entrance mat [3,2]
     Wall-art codes (on wall cells; never a symbol): d dairy cooler door  e drinks cooler door  < walk-in cooler door
       f fire point  > fire exit  { sprinkler riser  ( ) banners  8 9 TV wall  ] dock door with a trailer (centre cell; the cells
       either side are '_')  [ closed dock door (centre)  ? notice board  ` electrical panel
       * the BULKBARN logo (a run of exactly eight cells)
   Roof (10): = joist bay [4,4]  ~ bay with a high-bay lamp  : bay with a skylight  ; girder bay  | girder + lamp
     1 - 7 aisle signs   ! produce  @ electronics  $ apparel  % frozen  ^ receiving  & staging (hanging boards) */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var ART = {
    S: { d: 'WC_Dairy', e: 'WC_Drinks', '<': 'WC_WalkIn', f: 'WS_Fire', '>': 'WS_Exit', '{': 'WS_Riser', '(': 'WS_BannerA', ')': 'WS_BannerB', '8': 'WE_TVA', '9': 'WE_TVB' },
    K: { f: 'WK_Fire', ']': 'WK_Dock', '[': 'WK_DockShut', '?': 'WK_Board', '`': 'WK_Panel', '_': null }
  };
  function floorOf(grid) {
    if (grid._msF === undefined) {
      grid._msF = null;
      (grid.layers || []).forEach(function (l) { if (!grid._msF && l.y < 1) grid._msF = l; });
    }
    return grid._msF;
  }
  // the BULKBARN logo: a run of eight '*' wall cells, each module drawing its slice of the word (read from the
  // viewer's left: the module's local -X end)
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = floorOf(grid), S = F && F.at(0, 0) === ',' ? 'K' : 'S';
    if (face === 'corner' || face === 'none') return 'Corner' + S;
    var code = F ? F.at(c, r) : '.', A = ART[S];
    if (code === '*' && LEFT[face]) {
      var L = LEFT[face], k = 0;
      while (k < 8 && F.at(c + L[0] * (k + 1), r + L[1] * (k + 1)) === '*') k++;
      return 'WS_Logo' + Math.min(7, k);
    }
    if (A.hasOwnProperty(code)) return A[code];   // null: a dock door's side cell (the centre module draws the 3 m bay)
    return 'W' + S;
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }

  // goods colours: the kit models stock in four cells (gA - gD, 30 - 33) and the theme deals each placed copy one of
  // these mixes of the product colours (30 - 42: red, blue, yellow, green, orange, purple, white, black, pink, teal,
  // brown, lime, sky)
  var MIX = [[30, 31, 32, 33], [34, 35, 36, 31], [39, 32, 30, 36], [33, 41, 34, 37], [38, 31, 42, 32], [40, 36, 33, 30],
    [31, 34, 39, 35], [32, 37, 38, 41], [36, 30, 42, 40], [35, 33, 34, 36], [30, 39, 41, 31], [42, 38, 32, 37]];
  var GOODS = { from: [30, 31, 32, 33], to: MIX };
  var FRUIT = { from: [30, 31, 32, 33], to: [[30, 34, 32, 33], [35, 30, 41, 32], [34, 33, 30, 32], [32, 41, 35, 34], [30, 32, 33, 35]] };
  var SALES = ['Rack_EndL', 'Rack_A', 'Rack_B', 'Rack_EndR'];
  var TALL = ['Tall_EndL', 'Tall_A', 'Tall_B', 'Tall_EndR'];
  var KP = 'KIT_PARKING_';

  var SYMBOLS = {
    // ---- sales floor
    'R': { size: [3, 2], pieces: SALES, sequence: 'run', kind: 'cover', paint: GOODS },
    'n': { size: [2, 1], pieces: ['Endcap_A', 'Endcap_B'], face: Math.PI, kind: 'cover', paint: GOODS },
    's': { size: [2, 1], pieces: ['Endcap_B', 'Endcap_A'], face: 0, kind: 'cover', paint: GOODS },
    'p': { pieces: ['Pal_Water', 'Pal_Paper', 'Pal_TV', 'Pal_Mixed', 'Pal_Bags', 'Pal_Water', 'Pal_Mixed'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'l': { pieces: ['Pal_Low', 'Pal_Bags', 'Pal_Low'], rotate: 'random90', kind: 'cover', paint: GOODS },
    'm': { pieces: ['Pal_Empty'], rotate: 'random90', kind: 'cover' },
    'F': { size: [4, 2], pieces: ['Bunker'], flip: true, kind: 'cover', paint: GOODS },
    'V': { size: [2, 2], pieces: ['Produce'], flip: true, kind: 'cover', paint: FRUIT },
    'K': { size: [3, 2], pieces: ['TechTable'], flip: true, kind: 'cover' },
    'A': { size: [2, 2], pieces: ['ClothesTable'], flip: true, kind: 'cover', paint: GOODS },
    'Q': { size: [2, 2], pieces: ['ClothesRack'], flip: true, kind: 'cover', paint: GOODS },
    'H': { size: [8, 3], pieces: ['Pharmacy'], orient: 'wall', kind: 'cover' },
    'L': { size: [3, 5], pieces: ['Checkout'], face: 0, kind: 'cover', paint: GOODS },
    'c': { pieces: ['Cart', 'Cart', 'Cart_B'], rotate: 'random90', kind: 'cover' },
    'C': { size: [4, 1], pieces: ['CartCorral'], flip: true, kind: 'cover' },
    'q': { pieces: ['VGlassHalf'], full: 'VGlassFull', links: 'qD#', post: 'VGlassPost', kind: 'wall' },
    'D': { size: [4, 1], pieces: ['VDoor'], orient: 'span', kind: 'wall' },
    'g': { pieces: ['Podium'], rotate: 'edge', kind: 'cover' },
    'Z': { size: [10, 4], pieces: ['Landmark_FoodCourt'], orient: 'wall', kind: 'cover' },
    't': { size: [2, 2], pieces: ['CafeTable'], kind: 'cover' },
    'O': { pieces: ['Column'], kind: 'cover' },
    // ---- stockroom
    'T': { size: [3, 2], pieces: TALL, sequence: 'run', kind: 'cover', paint: GOODS },
    'j': { pieces: ['PalletJack'], rotate: 'random90', kind: 'cover' },
    'X': { size: [2, 3], pieces: [KP + 'Forklift'], flip: true, kind: 'cover' },
    'x': { size: [2, 2], pieces: [KP + 'Pallets'], flip: true, kind: 'cover' },
    'k': { pieces: [KP + 'Drums'], rotate: 'random90', kind: 'cover' },
    'w': { size: [2, 1], pieces: [KP + 'Bins'], flip: true, kind: 'cover' },
    'B': { size: [2, 2], pieces: ['Baler'], orient: 'wall', kind: 'cover' },
    'b': { pieces: ['Bale_1', 'Bale_2', 'Bale_1', 'Bale_2', 'Bale_2'], rotate: 'random90', kind: 'cover' },
    'y': { pieces: ['Gaylord'], rotate: 'random90', kind: 'cover' },
    'W': { size: [2, 2], pieces: ['Wrapper'], flip: true, kind: 'cover' },
    'M': { size: [2, 2], pieces: ['BreakTable'], kind: 'cover' },
    'v': { size: [1, 1], pieces: ['Vending', 'Vending_B'], sequence: true, orient: 'wall', kind: 'cover' },
    'U': { size: [2, 1], pieces: ['Lockers'], orient: 'wall', kind: 'cover' },
    'Y': { size: [3, 1], pieces: ['Kitchen'], orient: 'wall', kind: 'cover' },
    'i': { pieces: ['PartHalf'], full: 'PartFull', links: 'iJ#', post: 'PartPost', kind: 'wall' },
    'J': { size: [3, 1], pieces: ['BreakDoor'], orient: 'span', kind: 'wall' },
    'N': { size: [2, 7], pieces: ['Stair'], face: 0, kind: 'step' },
    'I': { pieces: ['DeckColumn'], kind: 'cover' },
    // ---- mezzanine (layer 3.5)
    'u': { deck: { thick: 0.4, color: '#B9C2CB', edge: '#F7C531', under: '#D6DCE3', with: '*' } },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    'o': { size: [8, 5], pieces: ['Landmark_Office'], face: 0, kind: 'cover' },
    // ---- floor marks (layer 0.01)
    '-': { pieces: ['F_Line'], rotate: 'run', collide: false },
    'z': flat(['F_Walk']), '/': flat(['F_Hatch']), '+': { size: [3, 2], pieces: ['F_Mat'], collide: false },
    // ---- roof (layer 10): bays and hanging signs
    '=': { size: [4, 4], pieces: ['Roof_J'], collide: false }, '~': { size: [4, 4], pieces: ['Roof_L'], collide: false },
    ':': { size: [4, 4], pieces: ['Roof_S'], collide: false }, ';': { size: [4, 4], pieces: ['Roof_G'], collide: false },
    '|': { size: [4, 4], pieces: ['Roof_GL'], collide: false },
    '!': flat(['Dept_Produce']), '@': flat(['Dept_Tech'], R90), '$': flat(['Dept_Apparel'], R90), '%': flat(['Dept_Frozen']),
    '^': flat(['Dept_Receiving'], R90), '&': flat(['Dept_Staging'])
  };
  for (var a = 1; a <= 7; a++) SYMBOLS[String(a)] = flat(['Aisle_' + a]);

  // glow companions (zones.js theme.glow): screens, menu boards, lamp lenses, skylights, the cooler cases' light
  var GLOW = {
    WS_Exit: { piece: 'WS_Exit_LED' }, WC_Dairy: { piece: 'WC_Glow' }, WC_Drinks: { piece: 'WC_Glow' },
    WE_TVA: { piece: 'WE_TVA_LED' }, WE_TVB: { piece: 'WE_TVB_LED' }, GateFrame: { piece: 'GateFrame_LED' },
    Roof_L: { piece: 'Roof_L_LED' }, Roof_GL: { piece: 'Roof_GL_LED' }, Roof_S: { piece: 'Roof_S_LED' },
    TechTable: { piece: 'TechTable_LED' }, Checkout: { piece: 'Checkout_LED' }, Landmark_FoodCourt: { piece: 'Landmark_FoodCourt_LED' },
    Vending: { piece: 'Vending_LED' }, Vending_B: { piece: 'Vending_B_LED' }, Landmark_Office: { piece: 'Landmark_Office_LED' }
  };

  var WALLS = ['WS', 'CornerS', 'WK', 'CornerK'];
  for (var lg = 0; lg < 8; lg++) WALLS.push('WS_Logo' + lg);
  Object.keys(ART).forEach(function (S) { Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (p && WALLS.indexOf(p) < 0) WALLS.push(p); }); });
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch']);
  var BORROWED = [];   // kit-parking pieces (named in full; tests check they exist in fps-kit-parking.glb)
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) {
      if (n.indexOf(KP) === 0) { if (BORROWED.indexOf(n) < 0) BORROWED.push(n); } else if (PIECES.indexOf(n) < 0) PIECES.push(n);
    });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'megastore', name: 'BULKBARN Warehouse Club', family: 'kit-megastore', prefix: 'KIT_MEGASTORE_', families: ['kit-parking'],
    palette: ['#2C63B8', '#D8392F', '#F7C531', '#EEF0EC'],
    env: {
      sky: null, clear: '#B9C0C6', fog: { color: '#C9CDCF', near: 55, far: 150 }, clouds: false,
      sun: [0.32, 0.86, 0.4],
      ceiling: { height: 10.0, color: '#A7AFB6' }   // roof bays and signs come from the zone's "@layer 10" grid
    },
    // polished concrete with saw-cut joints every 4 m
    floor: {
      color: '#CBC8C0', trail: '#C2BFB6', outside: '#CBC8C0',
      lines: [{ dir: 'x', every: 4, width: 0.02, color: '#A9A59C', y: 0.008 }, { dir: 'z', every: 4, width: 0.02, color: '#A9A59C', y: 0.0105 }]
    },
    wall: { height: 10.0, roof: '#A7AFB6', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 10.0 },
    hatch: 'Hatch', stand: 'Pal_Low',
    backdrop: null,
    budget: { prop: 2000, landmark: 2000, total: 45000 },
    allPieces: function () { return PIECES.slice(); },
    borrowed: function () { return BORROWED.slice(); },
    levels: {
      megastore: {
        name: 'BULKBARN Warehouse Club',
        intro: 'Robots have overrun the warehouse club. Clear the sales floor, then push through the EMPLOYEES ONLY doors into the stockroom.',
        zones: [
          // Sales Floor: rack aisles, departments, the front end and the food court
          { map: 'megastore_1', waves: [
            [['crawler', 20], ['gunner', 10], ['drone', 3]],
            [['crawler', 10], ['bomber', 2], ['gunner', 6], ['blader', 6]],
            [['crawler', 12], ['drone', 7], ['gunner', 7], ['soldier', 10]],
            [['crawler', 14], ['drone', 3], ['bomber', 2], ['gunner', 9], ['soldier', 6], ['blader', 5]],
            [['crawler', 8], ['gunner', 6], ['soldier', 5]]] },
          // Stockroom: tall racks, the docks, the mezzanine office
          { map: 'megastore_2', waves: [
            [['crawler', 16], ['gunner', 10], ['soldier', 6]],
            [['crawler', 12], ['drone', 6], ['gunner', 8], ['blader', 6]],
            [['crawler', 12], ['bomber', 2], ['gunner', 9], ['soldier', 8]],
            [['crawler', 14], ['drone', 6], ['gunner', 10], ['soldier', 6], ['blader', 5]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
