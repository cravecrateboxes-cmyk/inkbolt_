/* Theme: Grand Hotel Riviera (kit-riviera) -- a made-up Belle Epoque grand hotel on a cliff over the Mediterranean,
   late afternoon, the sea to the west. Two zones; player travel is north.
   1 The ground floor (73 x 63, 9 m rooms under the ceiling): the Grand Lobby in the middle -- the front doors in the
     south with a blue runner to the marble medallion under the great chandelier, the reception under the east arm of
     the gallery, the concierge under the west arm, lounges on carpets, palms, the bell captain's stand and luggage
     carts; the gallery at 4.5 m on three sides; the Imperial Staircase (landmark: a central flight of white marble on
     a blue runner to a landing at 2.16 m, two flights turning back from it to the top landings at 4.5 m, iron and
     gilt balustrades, bronze lamp standards, flower urns, niches with fountain urns in its flanks) and the bridges
     from its top landings to the gallery's arms. The restaurant Le Grand Bleu on the sea side (west): two-tops at the
     arched French windows, four-tops in white linen, the chef's round table, blue velvet banquettes along the wall,
     the wine wall, the pass in front of the kitchen's swing doors, sommeliers' trolleys, Provencal cement tiles; the
     bar Le Phare at its south end (the bar, stools, the grand piano, lounges) behind a row of palms. The conference
     hall Salon Mediterranee in the north-east (the stage with the projection screen and blue drapes, the lectern,
     rows of gilt chairs either side of the aisle, the AV desk with its camera, coffee stations, cocktail tables) and
     its foyer in the south-east (the registration desk and roll-up banner, the cloakroom, coffee stations, cocktail
     tables, lounges). The guest wing in the north-west: a corridor with three walk-in suites (the Salon, King and
     Twin suites of The Aurelian, repainted) on its north side and the closed doors of the others on its south side.
     The palm court in the north: tea tables of rattan round the court fountain, palms in urns, writing desks, a
     piano, the lifts (between the palm court and the lobby), and the doors out to the pool terrace.
   2 The pool terrace (75 x 68, open sky): the infinity pool (landmark: 45 m along the cliff edge, its water running
     out to the vanishing edge over the sea, a bronze wave sculpture at its north end), the spa pool with its
     whirlpool, Le Bar de la Plage under a striped pergola with cafe tables round it, pairs of sun loungers under
     parasols facing the sea, single loungers, outdoor showers, cabanas along the north wing, the towel hut by the
     garden doors, Canary palms, olives, lemon trees, cypresses, urns, lavender planters as low walls, a terrace
     fountain, a fire table; the lawn garden south-east (two pergola lounges, daybeds, olives, a hedge). The spa
     podium in the east (arched windows with blue shutters, the doors of LES BAINS and SPA AZUR, bougainvillea)
     carries the roof garden at 4.5 m (the belvedere over the pool, pergola lounges, daybeds, fire tables, olives,
     planters, hedges, lemon trees, cypresses, lawns, behind a stucco parapet with a band of blue tiles), reached by
     two stairs set into the podium. The hotel's white stucco facades with blue shutters and wrought-iron balconettes
     close the terrace on three sides; the stone balustrade over the cliff on the fourth.
   The trails are the orangery passages (white plaster, a blue and white tiled dado, frosted arched windows,
   lanterns), the exit the hotel's lift down to the private beach (PLAGE). Kit: blender/fam_kit_riviera.py
   (rv_base / rv_walls / rv_inside / rv_pool); zones: tools/riviera_zones.py (src/data/zones/riviera_*.txt). The
   grand-hotel furniture is The Aurelian's (kit-hotel: KH below), lemon trees, cypresses and urns Ca' Doranza's
   (kit-venetian: KV), placed through the option `families`; the hotel pieces are repainted in the Riviera blues
   (symbol option `paint`, hotel palette cells: wine 21 / 22 / 23 -> navy 26 / 27, teal 28).

   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled)
     # wall (wall.height 4.5, taller modules carry their own collision above it: wall.cols)
       zone 1: interior walls (white plaster, sea-glass dado, belt course, cornice; sconces, paintings, mirrors), the
       outer walls' arched French windows in 3 m bays (SW_P pier, SW_A / SW_B the two halves of an arch), doorways
       (n), the suites' corridor fronts and closed doors, the kitchen doors, the lifts, the suites' windows;
       zone 2: the facades (F_ShA / F_Win / F_ShB bays, doors, plain ends with bougainvillea), the podium's front
       (PW_*: windows, doors, plain, bougainvillea, corners, the stair heads under the deck), the sea balustrade and
       the infinity edge (west).
     n doorway (wall.passage: open below the 2.7 m lintel)
     Zone 1: X the Imperial Staircase [13,10] (landmark)   I column (under the gallery's edge)   R reception [6,4] KH
             Q concierge / cloakroom [3,2] KH   F flower table [3,3] KH   L lounge (sofa, armchairs) [4,3]   K piano [3,3] KH
             B the bar Le Phare [8,4] (The Aurelian's bar, relettered)   b bar stool KH   O ottoman [2,1] KH   k console [2,1] KH   w writing desk [2,1] KH
             p palm in an urn   t topiary KH   c luggage cart KH   j bell captain KH   e easel KH   T the chef's table [3,3] KH
             D the stage [9,4] KH (with the projection screen)   y housekeeping cart [2,1] KH   v trolley [2,1] KH
             M / N / W the King / Twin / Salon suite [6,6] KH (front to the doorway)
             d four-top [2,2]   u two-top [2,1]   q banquette [4,2]   V wine wall [3,1]   Z the kitchen pass [4,1]
             z sommelier's trolley   Y row of six chairs [6,1] (facing north)   l lectern   A AV desk [3,2]
             C coffee station [4,1]   o cocktail table   g registration desk [4,2]   s tea table [2,2]
             f fountain [4,4] (the palm court; the terrace)
     Zone 2: % the infinity pool [9,12] (landmark; south end / middle / north end, run north)   & the spa pool [8,6]
             $ the pool bar [8,4]   < two sun loungers and a parasol [3,3] (facing the sea)   > lounger [1,2]
             ( cabana [3,3] KH   ) towel hut [3,2]   [ outdoor shower   ] Canary palm   { lavender planter [3,1]
             } olive [2,2]   ? stair to the roof garden [8,4] (rises along local X)   / pergola lounge [4,6]
             1 the belvedere [5,5]   2 daybed [2,2]   3 fire table [2,2] KH   4 hedge (links) KH
             5 lemon tree KV   6 cypress KV   7 urn KV   s tea table [2,2]   f fountain [4,4]
   Layer symbols: zone 1 "@layer 0": x medallion [7,7] KH   _ runner [3,1] KH   ! carpet [4,4] KH   + corridor carpet
     [4,4] KH   , cement tiles [2,2]; "@layer 4.5" the gallery: m deck (every symbol on that layer stands on it), r
     balustrade (links), i column, L p t O (furniture), S a; "@layer 9" the ceiling: H the great chandelier [5,5]
     KH, ^ chandelier [3,3], ~ coffer [4,4] KH, : downlight KH.
     Zone 2 "@layer 0": 9 lawn [2,2]; "@layer 4.5": = the roof garden's deck; "@layer 4.5": the roof garden's
     furniture (1 / 2 3 4 5 6 } {), 9 lawn, S h.
   Backdrop (backdrop.build, level-wide, so nothing switches between the zones): the sea far below the cliff to the
   horizon (bands of turquoise and deep blue, sun glitter, yachts and sailing boats), the cliff face with rocks and
   surf at its foot, the bay's far shore with a hillside town (white, ochre and rose houses with terracotta roofs, a
   campanile, the harbour with its breakwater and lighthouse) to the north-west and a headland with villas and a
   lighthouse to the south-west, hills behind; on the land side the gardens, the forecourt and the town up the hill
   (seen from the windows); the facades over zone 2's gates. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, KH = 'KIT_HOTEL_', KV = 'KIT_VENETIAN_';
  var SEA = -30;

  // ---------------------------------------------------------------- walls
  function kindOf(g) {   // zone 1 (the ground floor) holds the staircase; zone 2 the infinity pool
    if (g._rK === undefined) { g._rK = 'pool'; for (var r = 0; r < g.h; r++) if (g.rows[r].indexOf('X') >= 0) { g._rK = 'inside'; break; } }
    return g._rK;
  }
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E' || ch === 'n'; }
  function gateDist(g, c, r) {   // cells from a north / south edge cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  // module-local +X in grid steps for a module facing S / N / E / W (the engine's yaw 0, pi, pi/2, -pi/2)
  var LDIR = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };
  var INWARD = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  /* The run of cells along a wall line through (c, r) that share its facing and are open on that side (cached per
     grid and facing): returns { i, n } the cell's index in module-local +X order and the run's length. */
  function runOf(g, c, r, face, ok) {
    var cache = g._rRun || (g._rRun = {}), key = face + c + ',' + r;
    if (cache[key]) return cache[key];
    var L = LDIR[face], F = INWARD[face];
    function good(x, y) { return ok(x, y) && wallish(g.at(x, y)) && !wallish(g.at(x + F[0], y + F[1])); }
    var a = 0, b = 0;
    while (good(c - L[0] * (a + 1), r - L[1] * (a + 1))) a++;
    while (good(c + L[0] * (b + 1), r + L[1] * (b + 1))) b++;
    var res = { i: a, n: a + b + 1 };
    for (var k = -a; k <= b; k++) cache[face + (c + L[0] * k) + ',' + (r + L[1] * k)] = { i: a + k, n: a + b + 1 };
    return res;
  }
  // a panelled interior wall in a rhythm along the run: sconces every 4 m, a painting or a mirror between them
  function panel(a, c, r, V) {
    var k = ((a % 6) + 6) % 6;
    if (k === 0) return 'IW_Sconce' + V;
    if (k === 3) return (hh(c * 5 + 1, r * 11 + 7) < 0.55 ? 'IW_Art' : 'IW_Mirror') + V;
    return 'IW_Plain' + V;
  }
  var SUITES = 'MNW';
  // the outer walls of the ground floor: 3 m bays of a pier and an arched window pair, from each run's start
  function seaBay(g, c, r, face) {
    var R = runOf(g, c, r, face, function (x, y) { return gateDist(g, x, y) >= 2.6 && !((x === 0 || x === g.w - 1) && (y === 0 || y === g.h - 1)); });
    var k = R.i % 3, last = R.n - 1;
    if (k === 0 || (k === 1 && R.i === last)) return 'SW_P';   // a half without its partner stands as a pier
    return k === 1 ? 'SW_A' : 'SW_B';   // SW_A: the arch's centre on the module's +X edge (its partner is the next cell)
  }
  function insideWall(c, r, horiz, corner, g, face) {
    var W = g.w, Hh = g.h, ch = g.at(c, r);
    if (ch === 'n') {   // doorway: the jamb on the end(s) of the run (local -X / +X: +c / -c on E-W runs, +r / -r on N-S runs)
      var along = wallish(g.at(c - 1, r)) || wallish(g.at(c + 1, r));
      var lo = along ? g.at(c - 1, r) !== 'n' : g.at(c, r + 1) !== 'n', hi = along ? g.at(c + 1, r) !== 'n' : g.at(c, r - 1) !== 'n';
      return lo ? 'Door_L' : hi ? 'Door_R' : 'Door_M';
    }
    var west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1;
    if ((west || east) && (north || south)) return null;
    if (face === 'corner' || face === 'none') return 'Core';
    var F = INWARD[face], inward = g.at(c + F[0], r + F[1]);
    // suites: party walls draw nothing (the suites draw their sides), the outer wall behind a suite is its window
    if (SUITES.indexOf(inward) >= 0) {
      if (north) return 'SuiteWin';
      if (west || east || south) return null;   // the suite's own side wall stands 2 cm inside this cell
      var acrossS = g.at(c - F[0], r - F[1]);
      if (SUITES.indexOf(acrossS) >= 0 || face === 'E' || face === 'W') return null;
    }
    if (west || east || north || south) {
      if (gateDist(g, c, r) < 2.6) return null;   // the gate portal's piers stand there
      var lat = LDIR[face];
      if (wallish(g.at(c + lat[0], r + lat[1])) && wallish(g.at(c + lat[0] + F[0], r + lat[1] + F[1]))) return 'Core';
      if (wallish(g.at(c - lat[0], r - lat[1])) && wallish(g.at(c - lat[0] + F[0], r - lat[1] + F[1]))) return 'Core';
      // arched French windows: the sea side of the restaurant and the guest wing, the front of the lobby; panelled
      // one-sided walls elsewhere (the bar's back wall, the hall, the palm court, the foyer)
      if ((west && r >= 8) || (south && c > 21 && c < 51)) return seaBay(g, c, r, face);
      return (((west || east) ? r : c) % 6 === 0) ? 'SF_Sconce' : 'SF_Plain';
    }
    // the suites' corridor: the fronts of the walk-in suites (sconces by the doorways), the closed doors opposite
    var nearDoor = g.at(c - 1, r) === 'n' || g.at(c + 1, r) === 'n';
    if (r === 7 && c < 21) return nearDoor ? 'SF_Sconce' : 'SF_Plain';
    if (r === 12 && c < 21 && face === 'N') {
      if (c === 3 || c === 10 || c === 17) return 'SuiteDoor_' + 'ABC'[c === 3 ? 0 : c === 10 ? 1 : 2];
    }
    // the restaurant's kitchen doors, the palm court's lifts
    if (r === 20 && c < 21 && face === 'S' && (c === 9 || c === 10)) return 'KitDoor';
    if (r === 22 && (c === 32 || c === 33 || c === 39 || c === 40)) return KH + (c % 2 === (c < 36 ? 0 : 1) ? 'Lift_A' : 'Lift_B');   // pairs (32, 33), (39, 40): both faces
    var vert = wallish(g.at(c, r - 1)) || wallish(g.at(c, r + 1));
    if (corner || !(horiz || vert)) return 'Core';
    return panel(horiz ? c : r, c, r, horiz ? '' : '_V');
  }
  // ---- zone 2
  var PX0 = 52, PX1 = 73, PY0 = 1, PY1 = 44;   // the spa podium (tools/riviera_zones.py)
  function facade(g, c, r, face) {
    var R = runOf(g, c, r, face, function (x, y) { return gateDist(g, x, y) >= 2.6 && !((x === 0 || x === g.w - 1) && (y === 0 || y === g.h - 1)); });
    var lead = Math.max(1, Math.floor((R.n % 3) / 2) + 1), i = R.i - lead, n3 = Math.floor((R.n - lead - 1) / 3);
    if (i < 0 || i >= n3 * 3) return hh(c * 3 + 1, r * 5) < 0.15 ? 'F_Bloom' : 'F_Plain';
    var bay = Math.floor(i / 3), k = i % 3, closed = hh(bay * 7 + c * 0 + (face === 'N' || face === 'S' ? r : c), bay + 3) < 0.4 ? '2' : '';
    if (k === 1) return (bay % 4 === 1 && !closed) ? 'F_Door' : 'F_Win' + closed;
    return (k === 0 ? 'F_ShA' : 'F_ShB') + closed;
  }
  function podium(g, c, r, face) {
    var head = (c === 60 && r >= 18 && r <= 21) || (r === 36 && c >= 64 && c <= 67);
    if (head || face === 'none') return 'PW_Gap';
    if (face === 'corner') return 'PW_Corner';
    var F = INWARD[face];
    if (g.at(c + F[0], r + F[1]) === '?') return 'PW_Side';   // the walls either side of a stair
    var pos = face === 'W' ? r : c, k = pos % 5;
    if (face === 'W' && (r === 16 || r === 23)) return 'PW_Bloom';
    if (face === 'W' && r === 9) return 'PW_Door';
    if (face === 'S' && c === 57) return 'PW_DoorB';
    if (face === 'S' && (c === 63 || c === 68)) return 'PW_Bloom';
    return (pos % 15 === 2) ? 'PW_Bloom' : k === 4 || k === 2 ? 'PW_Plain' : 'PW_Win';
  }
  function poolWall(c, r, horiz, corner, g, face) {
    var W = g.w - 1, H = g.h - 1;
    if ((c === 0 || c === W) && (r === 0 || r === H)) return 'F_Corner';
    if (c >= PX0 && c <= PX1 && r >= PY0 && r <= PY1) return podium(g, c, r, face);
    if (c === 0) return g.at(1, r) === '%' ? 'InfEdge' : (r % 6 === 0 ? 'SeaBal_L' : 'SeaBal');
    if (gateDist(g, c, r) < 2.6) return null;   // the gate portal (its facade over it: backdrop.build)
    if (face === 'corner' || face === 'none') return 'F_Corner';
    if ((c === W) && (r === 1 || r === H - 1 || r === PY1 + 1)) return 'F_End';   // its bands cross the N / S fronts' (or the podium's) in the corner
    return facade(g, c, r, face);
  }
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    return kindOf(g) === 'inside' ? insideWall(c, r, horiz, corner, g, face) : poolWall(c, r, horiz, corner, g, face);
  }

  // ---------------------------------------------------------------- symbols
  function pf(size, pieces, extra) { return Object.assign({ size: size, pieces: pieces, kind: 'cover' }, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, kind: 'cover', rotate: rot === undefined ? 'random90' : rot }, extra || {}); }
  function flat(size, pieces, extra) { return Object.assign({ size: size, pieces: pieces, collide: false }, extra || {}); }
  // the hotel kit's palette cells (blender/hotel_base.py): wine 21, wine2 22, wine3 23, navy 26, navy2 27, teal2 28
  var BLUE = { from: [21, 22, 23], to: [[26, 27, 27], [28, 27, 27], [26, 27, 27]] };
  var NAVY = { from: [21, 22, 23], to: [[26, 27, 27]] };
  var TEAL = { from: [21, 23], to: [[28, 27]] };
  var SYMBOLS = {
    // ---- zone 1 (the hotel's pieces: KH)
    'X': pf([13, 10], ['Landmark_Stair'], { face: 0, kind: 'step' }),
    'I': { pieces: ['GCol_Lo'], kind: 'cover' },
    'R': pf([6, 4], [KH + 'Landmark_Reception'], { orient: 'wall' }),
    'Q': pf([3, 2], [KH + 'Concierge'], { orient: 'wall' }),
    'F': pf([3, 3], [KH + 'Landmark_Flowers']),
    'L': pf([4, 3], ['LoungeSet'], { flip: true }),
    'K': pf([3, 3], [KH + 'Piano'], { flip: true }),
    'B': pf([8, 4], ['Bar'], { orient: 'wall' }),
    'b': one([KH + 'Stool'], undefined, { paint: NAVY }),
    'O': pf([2, 1], [KH + 'Ottoman'], { paint: BLUE }),
    'k': pf([2, 1], [KH + 'Console'], { orient: 'wall' }),
    'w': pf([2, 1], [KH + 'WritingDesk'], { orient: 'wall' }),
    'p': one(['PalmPot']),
    't': one([KH + 'Topiary']),
    'c': one([KH + 'LuggageCart']),
    'j': one([KH + 'BellStand'], 0),
    'e': one([KH + 'Easel'], R90),
    'T': pf([3, 3], [KH + 'Banquet'], { paint: NAVY }),
    'D': pf([9, 4], [KH + 'Landmark_Stage'], { orient: 'wall', paint: NAVY, with: {} }),
    'y': pf([2, 1], [KH + 'HKCart'], { flip: true }),
    'v': pf([2, 1], [KH + 'RSTrolley'], { flip: true }),
    'M': pf([6, 6], [KH + 'Suite_King'], { orient: 'open' }),
    'N': pf([6, 6], [KH + 'Suite_Twin'], { orient: 'open' }),
    'W': pf([6, 6], [KH + 'Suite_Salon'], { orient: 'open', paint: NAVY }),
    'd': pf([2, 2], ['DineTable']),
    'u': pf([2, 1], ['DineTwo']),
    'q': pf([4, 2], ['Banquette'], { orient: 'wall' }),
    'V': pf([3, 1], ['WineWall'], { orient: 'wall' }),
    'Z': pf([4, 1], ['KitchenPass'], { orient: 'wall' }),
    'z': one(['WineTrolley']),
    'Y': pf([6, 1], ['ChairRow'], { face: Math.PI }),
    'l': one(['Lectern'], 0),
    'A': pf([3, 2], ['AVDesk'], { face: Math.PI }),
    'C': pf([4, 1], ['CoffeeStation'], { orient: 'wall' }),
    'o': one(['HighTable'], 0),
    'g': pf([4, 2], ['RegDesk'], { face: 0 }),
    's': pf([2, 2], ['TeaSet'], { flip: true }),
    'f': pf([4, 4], ['CourtFountain'], { face: 0 }),
    // ---- zone 2
    '%': pf([9, 12], ['Landmark_Pool_S', 'Landmark_Pool_M', 'Landmark_Pool_N'], { sequence: 'run' }),
    '&': pf([8, 6], ['SpaPool'], { face: 0 }),
    '$': pf([8, 4], ['PoolBar'], { face: 0 }),
    '<': pf([3, 3], ['SunSet'], { face: -R90 }),
    '>': pf([1, 2], ['Lounger'], { face: 0 }),
    '(': pf([3, 3], [KH + 'Cabana'], { orient: 'wall' }),
    ')': pf([3, 2], ['TowelHut'], { face: 0 }),
    '[': one(['Shower'], 0),
    ']': one(['CanaryPalm']),
    '{': pf([3, 1], ['Planter'], { flip: true }),
    '}': pf([2, 2], ['OliveTree'], { flip: true }),
    '?': pf([8, 4], ['RoofStair'], { kind: 'step' }),
    '/': pf([4, 6], ['Pergola'], { flip: true }),
    '1': pf([5, 5], ['Belvedere'], { face: 0 }),
    '2': pf([2, 2], ['Daybed'], { flip: true }),
    '3': pf([2, 2], [KH + 'FireTable']),
    '4': { pieces: [KH + 'Hedge'], rotate: 'run', kind: 'cover' },
    '5': one([KV + 'LemonPot']),
    '6': one([KV + 'Cypress']),
    '7': one([KV + 'Urn']),
    // ---- layers
    'x': flat([7, 7], [KH + 'Inlay_Medallion']),
    '_': flat([3, 1], [KH + 'Runner'], { paint: NAVY }),
    '!': flat([4, 4], [KH + 'Carpet_Lobby'], { paint: TEAL }),
    '+': flat([4, 4], [KH + 'Carpet_Corridor'], { paint: NAVY }),
    ',': flat([2, 2], ['CementTiles']),
    '9': flat([2, 2], ['Lawn']),
    'm': { deck: { thick: 0.3, color: '#EDE6DA', edge: '#D9CEBC', under: '#F2EBDD', with: '*' } },
    '=': { deck: { thick: 0.3, color: '#B35A36', edge: '#D9CEBC', under: '#F2EBDD' } },
    'r': { pieces: ['GRail'], full: 'GRailFull', links: 'ri', post: 'GRailPost', kind: 'wall' },
    'i': { pieces: ['GCol_Hi'], kind: 'cover' },
    'H': flat([5, 5], [KH + 'Landmark_Chandelier']),
    '^': flat([3, 3], ['Lustre']),
    '~': flat([4, 4], [KH + 'Coffer']),
    ':': { pieces: [KH + 'Downlight'], collide: false }
  };
  SYMBOLS.D.with[KH + 'Landmark_Stage'] = ['StageScreen'];

  // ---------------------------------------------------------------- the sea, the coast, the town (backdrop.build)
  /* Level-wide: built once in level.root, so nothing here switches or pops as the player crosses between the zones. */
  function buildCoast(level, api) {
    var G = api.geo, hash = api.hash, Z = level.zones, Z1 = Z[0], Z2 = Z[1] || Z[0], T = THREE;
    var XC = Math.min(Z1.ox, Z2.ox);                       // the cliff edge (the zones' west walls stand on it)
    var zN = Math.min(Z1.oz, Z2.oz) - 260, zS = Z1.oz + Z1.h + 260, XE = Math.max(Z1.ox + Z1.w, Z2.ox + Z2.w);
    var WHITE = ['#F4EFE6', '#EAD7B0', '#E9C29A', '#F1D9CF', '#F6F1E8', '#E3B98F', '#DCC6A6'], ROOF = '#BC5B37', ROOFD = '#9A4A2D';
    // ---- the land: the hotel's plateau (gardens), the cliff, the sea
    G.flat([[XC, zN], [XE + 300, zN], [XE + 300, zS], [XC, zS]], -0.02, '#8EAF62');
    G.flat([[XC - 2600, zN - 2400], [XC - 40, zN - 2400], [XC - 40, zS + 2400], [XC - 2600, zS + 2400]], SEA, '#2C6FA6');
    G.flat([[XC - 40, zN - 2400], [XC, zN - 2400], [XC, zS + 2400], [XC - 40, zS + 2400]], SEA, '#3E9EBF');
    G.flat([[XC - 300, zN - 2400], [XC - 40, zN - 2400], [XC - 40, zS + 2400], [XC - 300, zS + 2400]], SEA + 0.01, '#3486B6');
    // sun glitter on the water toward the low sun (west), light ripple strokes nearer in
    for (var i = 0; i < 90; i++) {
      var gx = XC - 60 - hash(i, 3) * 900, gz = (Z1.oz + Z2.oz) / 2 + (hash(i, 5) - 0.5) * (120 + (XC - gx) * 0.5), L = 3 + hash(i, 7) * 9;
      G.flat([[gx - 0.25, gz - L], [gx + 0.25, gz - L], [gx + 0.25, gz + L], [gx - 0.25, gz + L]], SEA + 0.03, hash(i, 9) < 0.5 ? '#FBE7B6' : '#9ED3E6');
    }
    // the cliff face: jagged rock bands from the plateau down to the sea, rocks and surf at the foot
    var STEP = 9, rock = ['#B7A58C', '#A08F78', '#C7B79E', '#8F7F6B'];
    for (var zz = zN; zz < zS; zz += STEP) {
      var j0 = hash(Math.round(zz), 11) * 3, j1 = hash(Math.round(zz + STEP), 11) * 3, k0 = hash(Math.round(zz), 13) * 5, k1 = hash(Math.round(zz + STEP), 13) * 5;
      // upper face (vertical-ish, facing west) and the lower slope out to the water line
      quadW(XC - 0.3 - j0 * 0.3, XC - 0.3 - j1 * 0.3, -0.02, SEA * 0.45, XC - 4 - j0, XC - 4 - j1, zz, zz + STEP, rock[Math.floor(hash(Math.round(zz), 17) * 4)]);
      quadW(XC - 4 - j0, XC - 4 - j1, SEA * 0.45, SEA, XC - 12 - k0, XC - 12 - k1, zz, zz + STEP, rock[Math.floor(hash(Math.round(zz), 19) * 4)]);
      if (hash(Math.round(zz), 23) < 0.55) G.box(XC - 13 - k0, SEA + 1.0, zz + STEP / 2, 3 + j0, 3.2, 3 + k0 * 0.5, rock[(Math.round(zz) & 3)], { hull: true });
      G.flat([[XC - 15 - k0, zz], [XC - 12 - k0, zz], [XC - 12 - k1, zz + STEP], [XC - 15 - k1, zz + STEP]], SEA + 0.05, '#F2FAFC');
    }
    // a sloped quad facing west: top edge at x0 (z0) / x1 (z1), height yTop, bottom edge at bx0 / bx1, height yBot
    function quadW(x0, x1, yTop, yBot, bx0, bx1, z0, z1, c) {
      var col = new T.Color(c), p = G._vert(x0, yTop, z0, -0.85, 0.5, 0, col);
      G._vert(x1, yTop, z1, -0.85, 0.5, 0, col); G._vert(bx1, yBot, z1, -0.85, 0.5, 0, col); G._vert(bx0, yBot, z0, -0.85, 0.5, 0, col);
      G.idx.push(p, p + 2, p + 1, p, p + 3, p + 2);
    }
    // ---- the bay's far shore: a hillside town to the north-west, a headland with villas to the south-west
    function house(x, z, w, d, h, k, base) {
      var col = WHITE[Math.floor(hash(k, 31) * WHITE.length)];
      G.box(x, base + h / 2, z, w, h, d, col, { hull: false });
      G.box(x, base + h + 0.6, z, w + 0.4, 1.2, d + 0.4, hash(k, 33) < 0.5 ? ROOF : ROOFD, { hull: false });
      G.box(x - w / 2 - 0.01, base + h * 0.55, z, 0.02, h * 0.35, d * 0.6, '#5A6E86', { hull: false });
    }
    function hill(cx, cz, rx, rz, h, c) { var r = (rx + rz) / 2; G.sphere(cx, SEA - 2, cz, r, c, { ws: 12, hs: 6, sy: h / r, hull: false }); }
    var tx = XC - 520, tz = Z2.oz - 380;                    // the town across the bay (north-west)
    hill(tx - 120, tz - 60, 260, 200, 95, '#6E9150');
    hill(tx + 60, tz - 230, 240, 200, 120, '#62844A');
    hill(tx - 300, tz + 120, 200, 180, 70, '#78995A');
    for (var hI = 0; hI < 50; hI++) {
      var ang = hash(hI, 41) * Math.PI * 0.9 - 0.2, rad = 30 + hash(hI, 43) * 180, hx = tx + Math.cos(ang) * rad * 0.9, hz = tz - Math.sin(ang) * rad * 0.7;
      var lift = SEA + 2 + Math.max(0, (rad - 30)) * 0.42 + hash(hI, 45) * 6;
      house(hx, hz, 7 + hash(hI, 47) * 9, 7 + hash(hI, 49) * 7, 6 + hash(hI, 51) * 7, hI, lift);
    }
    G.box(tx - 10, SEA + 42, tz - 80, 6, 50, 6, '#E9C29A', { hull: false });                       // the campanile
    G.box(tx - 10, SEA + 69, tz - 80, 6.6, 4, 6.6, '#F4EFE6', { hull: false });
    G.cyl(tx - 10, SEA + 71, tz - 80, 4.4, 0.2, 7, 4, '#BC5B37', { hull: false });
    // the harbour: a breakwater with a lighthouse, moored boats
    G.box(tx + 70, SEA + 1.4, tz + 70, 120, 2.8, 6, '#CDBFA6', { hull: false });
    G.cyl(tx + 128, SEA + 2.8, tz + 70, 2.2, 1.8, 14, 8, '#F4EFE6', { hull: false });
    G.cyl(tx + 128, SEA + 16.8, tz + 70, 2.4, 2.4, 2, 8, '#C8473A', { hull: false });
    for (var bI = 0; bI < 10; bI++) api.add('Backdrop_Sail', tx + 20 + bI * 9, SEA, tz + 50 - hash(bI, 61) * 20, R90 + (hash(bI, 63) - 0.5) * 0.3, 0.7);
    var hx2 = XC - 430, hz2 = Z1.oz + Z1.h + 330;           // the headland to the south-west
    hill(hx2, hz2 + 80, 220, 180, 75, '#6E9150');
    hill(hx2 + 160, hz2 + 260, 260, 220, 100, '#62844A');
    for (var vI = 0; vI < 26; vI++) {
      var vx = hx2 + (hash(vI, 71) - 0.5) * 220, vz = hz2 + 20 + hash(vI, 73) * 140;
      house(vx, vz, 9 + hash(vI, 75) * 6, 9 + hash(vI, 77) * 6, 6 + hash(vI, 79) * 4, vI + 300, SEA + 20 + (vz - hz2) * 0.45);
    }
    G.cyl(hx2 - 150, SEA, hz2 - 40, 3, 2.4, 26, 8, '#F4EFE6', { hull: false });
    G.cyl(hx2 - 150, SEA + 26, hz2 - 40, 3.2, 3.2, 3, 8, '#2D6EAE', { hull: false });
    // far hills along the coast round the bay, hazed by the fog
    for (var fI = 0; fI < 9; fI++) hill(XC - 1100 + fI * 40, zN - 600 + fI * 520, 380, 300, 70 + hash(fI, 81) * 60, fI % 2 ? '#7F9A66' : '#73905C');
    // ---- boats on the sea
    [[-160, -60, 0.2], [-320, 90, -0.4], [-480, -200, 1.2], [-650, 260, 0.6]].forEach(function (b) {
      api.add('Backdrop_Yacht', XC + b[0], SEA, (Z1.oz + Z2.oz) / 2 + b[1], b[2], 1);
    });
    [[-120, 140, 0.3], [-240, -170, -0.6], [-380, -40, 1.0], [-560, 140, 0.2], [-260, 330, -0.2], [-700, -320, 0.8]].forEach(function (b) {
      api.add('Backdrop_Sail', XC + b[0], SEA, (Z1.oz + Z2.oz) / 2 + b[1], b[2], 1);
    });
    // ---- the land side, seen through the ground floor's windows: the forecourt (south), the gardens (east), the
    // town climbing the hill beyond
    var fz = Z1.oz + Z1.h, fx = Z1.ox + Z1.w / 2;
    G.flat([[Z1.ox, fz], [Z1.ox + Z1.w, fz], [Z1.ox + Z1.w, fz + 26], [Z1.ox, fz + 26]], -0.01, '#E3D6BE');
    G.cyl(fx, 0, fz + 14, 5, 5, 0.6, 16, '#EDE5D5', { hull: true });
    G.flat([[fx - 4.4, fz + 9.6], [fx + 4.4, fz + 9.6], [fx + 4.4, fz + 18.4], [fx - 4.4, fz + 18.4]], 0.5, '#3AA6D4');
    function palmT(x, z, h) {
      G.cyl(x, 0, z, 0.35, 0.28, h, 6, '#9B7650', { hull: true });
      for (var q = 0; q < 7; q++) { var a2 = q / 7 * Math.PI * 2; G.box(x + Math.cos(a2) * 1.6, h + 0.2, z + Math.sin(a2) * 1.6, 3.4, 0.25, 0.9, '#4E8F45', { hull: false }); }
    }
    for (var pI = 0; pI < 8; pI++) palmT(Z1.ox + 6 + pI * 9, fz + 6, 9 + hash(pI, 91) * 2);
    G.box(fx, 1.0, fz + 27, Z1.w + 30, 2, 0.6, '#EDE5D5', { hull: true });
    for (var sI = 0; sI < 12; sI++) house(Z1.ox - 10 + sI * 9, fz + 50 + hash(sI, 95) * 20, 6, 8, 7 + hash(sI, 97) * 5, sI + 500, 0);
    var ex = Z1.ox + Z1.w;
    for (var cI = 0; cI < 18; cI++) G.cyl(ex + 5 + hash(cI, 101) * 10, 0, Z1.oz + 3 + cI * 3.6, 0.9, 0.0, 9 + hash(cI, 103) * 3, 6, '#2F5E3C', { hull: true });
    for (var uI = 0; uI < 14; uI++) house(ex + 30 + hash(uI, 105) * 60, Z1.oz + hash(uI, 107) * Z1.h, 8, 8, 7 + hash(uI, 109) * 6, uI + 700, uI * 0.6);
    // ---- the facades over zone 2's gates (the gates are placed by the engine with their portal frames)
    if (Z[1]) {
      if (Z2.entryGate) api.add('F_GateTop', Z2.entryGate.x, 0, Z2.entryGate.z, Math.PI, 1);
      api.add('F_GateTop', Z2.exitGate.x, 0, Z2.exitGate.z, 0, 1);
    }
  }

  var PIECES = ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Win', 'TrailWall_Lamp', 'TrailWall_Art', 'Hatch',
    'Core', 'SF_Plain', 'SF_Sconce', 'SuiteDoor_A', 'SuiteDoor_B', 'SuiteDoor_C', 'KitDoor', 'Door_L', 'Door_M', 'Door_R',
    'SW_A', 'SW_B', 'SW_P', 'F_Win', 'F_Win2', 'F_ShA', 'F_ShB', 'F_ShA2', 'F_ShB2', 'F_Door', 'F_Plain', 'F_Bloom',
    'F_Corner', 'F_End', 'F_GateTop', 'PW_Win', 'PW_Door', 'PW_DoorB', 'PW_Plain', 'PW_Bloom', 'PW_Gap', 'PW_Side', 'PW_Corner', 'TrailWall_End', 'SeaBal',
    'SeaBal_L', 'InfEdge', 'StageScreen', 'Backdrop_Yacht', 'Backdrop_Sail', 'SuiteWin', KH + 'Lift_A', KH + 'Lift_B', KH + 'Stand'];
  ['Plain', 'Sconce', 'Art', 'Mirror'].forEach(function (k) { PIECES.push('IW_' + k, 'IW_' + k + '_V'); });
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (!d.pieces) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'riviera', name: 'Grand Hotel Riviera', family: 'kit-riviera', prefix: 'KIT_RIVIERA_', families: ['kit-hotel', 'kit-venetian'],
    palette: ['#F5F0E6', '#2D6EAE', '#C8653D', '#2E9FD0'],
    // late afternoon on the Riviera: a clear sky going pale toward the sea's hazy horizon, a warm low sun from the west
    env: { sky: ['#5F9FDF', '#DCE8EE'], fog: { color: '#D8E5EC', near: 150, far: 1300, tierScale: true }, sun: [-0.66, 0.55, 0.12],
      sunColor: '#FFE8C6', far: 1600, clouds: true, ceiling: { height: 9.0, color: '#F7F0E2' } },
    // zone 1: honed white marble with 1 m joints (carpets, the medallion and the restaurant's tiles from "@layer 0");
    // zone 2: travertine (its zone plan floor)
    floor: { color: '#EFE8DC', trail: '#E3D6BE', lines: [{ dir: 'x', every: 1, width: 0.025, color: '#DCD2C2', y: 0.008 }, { dir: 'z', every: 1, width: 0.025, color: '#DCD2C2', y: 0.0105 }],
      trailLines: [{ dir: 'x', every: 0.5, width: 0.02, color: '#CDBFA6', y: 0.008 }] },
    wall: { height: 4.5, roof: '#B35A36', facing: 'open', choose: chooseWall, cols: true, passage: { ch: 'n', solid: [[2.7, 9.0]] } },
    symbols: SYMBOLS,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // the orangery passages between the zones and out to the beach lift (their own ceiling at 4.2 m)
    trail: { wall: 'TrailWall', variants: ['TrailWall_Win', 'TrailWall', 'TrailWall_Lamp', 'TrailWall_Win', 'TrailWall_Art'], height: 4.2, end: 'TrailWall_End' },
    hatch: 'Hatch', stand: KH + 'Stand',
    backdrop: { build: buildCoast },
    budget: { prop: 4400, landmark: 6000, total: 60000 },
    // the kit's own pieces (the unit tests check them on fps-kit-riviera.glb); the borrowed ones (KIT_HOTEL_ /
    // KIT_VENETIAN_) are listed apart and checked on their kits' GLBs
    allPieces: function () { return PIECES.filter(function (n) { return !/^KIT_/.test(n); }); },
    borrowed: function () { return PIECES.filter(function (n) { return /^KIT_/.test(n); }); },
    levels: {
      riviera: {
        name: 'Grand Hotel Riviera',
        intro: 'Robots have taken the Grand Hotel Riviera. Fight through the lobby, the restaurant and the conference hall, then out to the pool terrace and up to the roof garden.',
        zones: [
          // the ground floor: the lobby and its gallery, the restaurant, the hall, the suites; the first wave is light robots only
          { map: 'riviera_1', ceiling: 'plain', label: 'The Grand Lobby', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 6]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 6], ['blader', 5]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 7], ['blader', 5]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 7], ['blader', 4]],
            [['crawler', 17], ['gunner', 10], ['drone', 7], ['soldier', 7], ['blader', 4]]] },
          // the pool terrace: the infinity pool, the spa podium and its roof garden
          { map: 'riviera_2', ceiling: false, label: 'The Pool Terrace', floor: { color: '#E6D9C2', lines: [{ dir: 'x', every: 1, width: 0.03, color: '#D2C3A8', y: 0.008 }, { dir: 'z', every: 2, width: 0.03, color: '#D2C3A8', y: 0.0105 }] }, waves: [
            [['crawler', 18], ['gunner', 11], ['drone', 5], ['soldier', 6], ['blader', 4]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 5], ['blader', 4]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 5], ['blader', 3]],
            [['crawler', 19], ['gunner', 11], ['bomber', 2], ['soldier', 5], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
