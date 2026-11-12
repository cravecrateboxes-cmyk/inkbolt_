/* Theme: Chalkstone Academy (kit-academy) -- a well-kept public school overrun by robots on a bright school day. Warm
   cream block walls with the school colours (a slate-blue and gold band), recessed lockers along every corridor,
   cream vinyl tile floors, white acoustic tile ceilings at 4 m, double-height rooms under 8 m roofs; outside, red
   brick with stone bands and two storeys of windows round a planted courtyard. Two zones:
   1 The main building (72 x 70): the entrance hall (double height) with recessed trophy cases, the honour rolls, the
     school crest in the floor and the main office behind its glass counter window; the main corridor and the west /
     east corridors and the spine hall, lockers on both sides; classroom 101 (maths), the computer lab, the art room,
     classrooms 107 (English: group tables), 109 (history: maps, a timeline), 108, 110, 113 and 115, the robotics lab
     (workbenches with half-built robot arms), the chemistry and biology labs (epoxy benches with sinks and gas
     taps, fume hoods, chemical cabinets, demo benches, eyewash stations, the skeleton model, periodic tables), the
     teachers' lounge, the restrooms and the custodian's closet; the landmark CAFETERIA (double height: the serving
     line with its sneeze guard, the kitchen pass and menu boards behind it, long tables, vending machines, the tray
     return) with the LIBRARY on a mezzanine along its west side (book stacks, reading tables, the checkout desk, two
     stairs: high ground over the whole hall). Exit: the cafeteria's north doors.
   2 The gymnasium and the courtyard (72 x 72): the gym lobby (the SNACK SHACK, the ticket table, the trophy wall),
     the locker room and the equipment room; the GYMNASIUM (double height: maple floor and court lines, two banks of
     pulled-out bleachers you climb, hoops hung from the roof, the stage with its curtains at the west end, mats,
     ball carts, the scoreboard, championship banners); three doors north into the open-air COURTYARD: the big oak
     (landmark) in its raised seat-wall bed in the lawn quad, the covered walkway from the gym to the north wing,
     the flagpole, planters and the school garden beds, benches, picnic tables, bike racks, the outdoor classroom's
     concrete tiers, street trees in grates, lamp posts; exit: the north wing's doors.
   Built by blender/fam_kit_academy.py (ac_*.py); zone layouts by tools/academy_zones.py (src/data/zones/academy_*.txt).

   A zone file has the floor plan and layers: "@layer 0.006" (floor finishes), "@layer 0.012" (the court lines),
   "@layer 0.02" and "@layer 0.03" (data, theme.dataLayers: wall art codes for the south / east and the north / west
   face of wall cells; 'o' on 0.02 marks the outdoor cells), "@layer 4" (ceiling tiles; in zone 1 a second "@layer 4":
   the library mezzanine) and "@layer 8" (roof bays over the double-height rooms).
   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled, front = +Z unless turned):
     # wall (8 m; the chooser faces every open side: interior paint, or brick toward the outdoor cells; art codes)
     D 7 classroom double door [2,1] (in the wall line; leaves folded open on the north / west resp. south / east side)
     O wide glass doors [3,1]   Q courtyard doors [3,1] (brick on the north face)   n archway header (open floor)
     d q student desk and chair (facing north / south)   T t teacher desk [2,1] (facing south / north)
     K bookcase [2,1] (back to a wall)   g group table for four [2,2]   A art table [2,2]   e easel
     k sink counter [3,1] (wall)   c computer desk [2,1] (wall)   C computer island [2,2]
     L lab bench [4,2]   F fume hood [2,1] (wall)   x skeleton model   X chemical cabinet [2,1] (wall)
     M m demo bench [4,1] (facing south / north)   w robotics workbench [3,2]   R reception counter [6,2] (front west)
     o office desk [2,1]   f file cabinet   p copier   s sofa [2,1] (wall)   y kitchenette [3,1] (wall)
     Y lounge table [2,2]   i bins   B bench [2,1]   j potted plant   b banner stand
     Z the serving line [10,3] (landmark, back to the wall)   l cafeteria table [6,2]   v vending machine
     z tray return [3,1] (wall)   W milk cooler   N stair [2,7] rising north   U stair [2,7] rising west   I deck column
     { } bleachers [8,5] (front south / north; walkable tiers)   > < hoop [2,1] hung from the roof (facing east / west)
     & stage [14,6] (front east)   % mats [2,1]   $ ball cart   ) gear shelf [2,1] (wall)   9 snack bar [6,2] (wall)
     0 ticket table [2,1]   @ the big tree [9,9] (landmark)   r planter / garden bed [4,2]   1 picnic table [2,2]
     2 bike rack [4,1] (wall)   3 covered walkway [2,4] (a run north from the gym door)   4 flagpole [2,2]
     5 lamp post   6 outdoor classroom tiers [10,4] (front south; walkable)   8 street tree in a grate [2,2]
   Library mezzanine (4): u deck   | rail (runs)   H book stack [3,1]   J reading table [2,2]   V checkout desk [4,2]
   Finishes (0.006): _ lab epoxy   ^ the crest [6,6]   [ gym maple [2,2]   , lawn      Court (0.012): ] court [28,16]
   Ceiling (4): - acoustic tiles [2,2]   * tiles with a light panel [2,2]   = tile   + light panel (1 cell, where a
     [2,2] does not fit)     Roofs (8): : coffer  ; coffer + pendant  ! skylight  / gym joist  ~ gym deck between joists
     ? joist + high-bay lamp
   Wall art codes (0.02: the S / E face, 0.03: the N / W face of a wall cell; data, never symbols):
     l lockers (a colour per run)  w whiteboard (run)  b cork board  p posters  k clock  y window  m maths poster
     q code poster  n cell poster  T periodic table (run)  e eyewash  x fire extinguisher  u kitchen pass / menu boards
     c clerestory windows  C 'CHALKSTONE CAFE' (8)  R 'ROBOTICS CLUB' (8)  L 'LIBRARY' (5)  h honour roll
     t trophy case (run)  O office window (run, through the wall)  M world map (run)  i timeline  r student art
     B / g / J restroom and custodian doors  f drinking fountain  P wall pads  s scoreboard (2)  V banners  F flags
     outdoors: W windows  d downspout  D doors (2)  N 'CHALKSTONE ACADEMY' (13)  G 'GO COMETS' (8) */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, PI = Math.PI;

  // ---------------------------------------------------------------- walls
  var DOORS = 'D7OQ', WALLISH = '#GE' + DOORS;
  var SIDES = ['S', 'N', 'E', 'W'];
  var STEP = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var FYAW = { S: 0, N: PI, E: R90, W: -R90 };
  var RIGHT = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };   // the viewer's right along a face
  function wl(g, c, r) { return WALLISH.indexOf(g.at(c, r)) >= 0; }
  function data(g, y) {
    var key = '_ac' + y;
    if (g[key] === undefined) { g[key] = null; (g.layers || []).forEach(function (l) { if (Math.abs(l.y - y) < 1e-4) g[key] = l; }); }
    return g[key];
  }
  function codeAt(g, c, r, side) { var L = data(g, side === 'S' || side === 'E' ? 0.02 : 0.03); return L ? L.at(c, r) : '.'; }
  function outdoor(g, c, r) { var L = data(g, 0.02); return !!L && L.at(c, r) === 'o'; }
  function gateCell(g, c, r) {   // the gate frame covers the gate and one wall cell either side of it
    if (r !== 0 && r !== g.h - 1) return false;
    var ch = r === 0 ? 'G' : 'E';
    for (var dc = -1; dc <= 1; dc++) if (g.at(c + dc, r) === ch) return true;
    return false;
  }
  // a run of one code along the wall: [index from the viewer's left, length]
  function runOf(g, c, r, side, code) {
    var R = RIGHT[side], k = 0, n = 1;
    while (k < 40 && codeAt(g, c - R[0] * (k + 1), r - R[1] * (k + 1), side) === code && wl(g, c - R[0] * (k + 1), r - R[1] * (k + 1))) k++;
    var m = 0; while (m < 40 && codeAt(g, c + R[0] * (m + 1), r + R[1] * (m + 1), side) === code && wl(g, c + R[0] * (m + 1), r + R[1] * (m + 1))) m++;
    n = k + 1 + m;
    return [k, n, c - R[0] * k, r - R[1] * k];
  }
  function ends(k, n, L, M, R) { return n === 1 ? M : k === 0 ? L : k === n - 1 ? R : M; }
  var SLICES = { C: ['SignCafe', 8], R: ['SignRobo', 8], L: ['SignLib', 5], N: ['XSign', 13], G: ['XBanner', 8] };
  function artPiece(g, c, r, side, code, hash) {
    var run, h = hash(c * 7 + 3, r * 11 + 5);
    switch (code) {
      case 'l': run = runOf(g, c, r, side, code); return ['LkA', 'LkB', 'LkC'][Math.floor(hash(run[2] * 5 + 1, run[3] * 9 + 2) * 3) % 3];
      case 'w': run = runOf(g, c, r, side, code); return run[0] === 1 && run[1] > 3 ? 'WB_T' : ends(run[0], run[1], 'WB_L', 'WB_M', 'WB_R');
      case 'T': run = runOf(g, c, r, side, code); return ends(run[0], run[1], 'PT_L', 'PT_M', 'PT_R');
      case 't': run = runOf(g, c, r, side, code); return ends(run[0], run[1], 'TC_L', 'TC_M', 'TC_R');
      case 'M': run = runOf(g, c, r, side, code); return ends(run[0], run[1], 'Map_L', 'Map_M', 'Map_R');
      case 'O': run = runOf(g, c, r, side, code); return ends(run[0], run[1], 'OW_L', 'OW_M', 'OW_R');
      case 's': run = runOf(g, c, r, side, code); return run[0] === 0 ? 'SB_L' : 'SB_R';
      case 'D': run = runOf(g, c, r, side, code); return run[0] === 0 ? 'XDoor_L' : 'XDoor_R';
      case 'u': run = runOf(g, c, r, side, code); return run[0] % 3 === 1 ? 'Menu' : 'KitPass';
      case 'V': run = runOf(g, c, r, side, code); return 'Banner' + [0, 1, 0, 2, 0, 3][run[0] % 6];
      case 'F': run = runOf(g, c, r, side, code); return 'Flag' + (run[0] % 4);
      case 'b': return 'Cork';
      case 'p': return ['PosterA', 'PosterB', 'PosterC'][Math.floor(h * 3) % 3];
      case 'r': return h < 0.5 ? 'ArtA' : 'ArtB';
      case 'k': return 'Clock'; case 'y': return 'Win'; case 'm': return 'PosterMath'; case 'q': return 'PosterCode';
      case 'n': return 'PosterCell'; case 'e': return 'EyeWash'; case 'x': return 'FireExt'; case 'c': return 'Clere';
      case 'h': return 'Honor'; case 'i': return 'Timeline'; case 'B': return 'DoorBoys'; case 'g': return 'DoorGirls';
      case 'J': return 'DoorJan'; case 'f': return 'Fountain'; case 'P': return 'Pad';
      case 'W': return 'XWin'; case 'd': return 'XPipe';
    }
    if (SLICES[code]) { run = runOf(g, c, r, side, code); return SLICES[code][0] + Math.min(SLICES[code][1] - 1, run[0]); }
    return null;
  }
  /* One face piece (modelled on a cell's front face) per open side of the cell, turned to that side: the engine
     turns the cell by its own rule (zones.js buildWalls: facing 'open', corners by their run), the chooser hands
     each piece the extra turn ({ piece, turn }). Plain faces are interior paint, or brick where the face looks onto
     an outdoor cell; art codes (the data layers) pick wall art; a through piece (the office window) fills the cell. */
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    if (face === 'none' || gateCell(g, c, r) || DOORS.indexOf(g.at(c, r)) >= 0) return null;   // door pieces draw their own wall
    var open = SIDES.filter(function (s) { return !wl(g, c + STEP[s][0], r + STEP[s][1]); });
    if (!open.length) return null;
    var yaw = face === 'corner' ? (!horiz && (wl(g, c, r - 1) || wl(g, c, r + 1)) ? R90 : 0) : FYAW[face];
    var plainOnly = face === 'corner', out = [];
    for (var i = 0; i < open.length; i++) {
      var s = open[i], nc = c + STEP[s][0], nr = r + STEP[s][1];
      var code = plainOnly ? '.' : codeAt(g, c, r, s), piece = code !== '.' ? artPiece(g, c, r, s, code, hash) : null;
      if (!piece) piece = outdoor(g, nc, nr) ? 'X' : 'I';
      var t = FYAW[s] - yaw;
      if (piece.indexOf('OW_') === 0) return [{ piece: piece, turn: t }];   // the office window runs through the wall
      out.push(t ? { piece: piece, turn: t } : piece);
    }
    return out;
  }

  // ---------------------------------------------------------------- symbols
  // palette cells (blender/ac_base.py): chairs chA - chF 32 - 37
  var CHAIRS = { from: [32], to: [[32], [33], [34], [35], [36], [37], [32], [35]] };
  var DESKS = { from: [32, 33], to: [[32, 33], [35, 34], [36, 32], [34, 37], [37, 35], [33, 36], [32, 35], [36, 34]] };
  var CAFE = { from: [32], to: [[32], [35], [34], [32]] };
  function pf(size, pieces, extra) { return Object.assign({ size: size, pieces: pieces, kind: 'cover' }, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, rotate: rot, kind: 'cover' }, extra || {}); }
  function flat(pieces, extra) { return Object.assign({ pieces: pieces, collide: false, rotate: 0 }, extra || {}); }
  var SYMBOLS = {
    // ---- doorways (wall.passage cells: the lintel collides, the door piece does not)
    'D': pf([2, 1], ['Door2'], { orient: 'span', kind: 'wall', collide: false }),
    '7': pf([2, 1], ['Door2'], { orient: 'span', kind: 'wall', collide: false, turn: PI }),
    'O': pf([3, 1], ['Door3'], { orient: 'span', kind: 'wall', collide: false }),
    'Q': pf([3, 1], ['Door3X'], { orient: 'span', kind: 'wall', collide: false }),
    'n': { pieces: ['Header'], rotate: 'run', collide: false },
    // ---- classrooms, labs, offices
    'd': one(['Desk'], 0, { paint: DESKS }), 'q': one(['Desk'], PI, { paint: DESKS }),
    'T': pf([2, 1], ['TeacherDesk'], { face: 0 }), 't': pf([2, 1], ['TeacherDesk'], { face: PI }),
    'K': pf([2, 1], ['Bookcase'], { orient: 'wall' }),
    'g': pf([2, 2], ['GroupTable'], { paint: CHAIRS, flip: true }),
    'A': pf([2, 2], ['ArtTable'], { flip: true }),
    'e': one(['Easel'], 'random90'),
    'k': pf([3, 1], ['SinkCounter'], { orient: 'wall' }),
    'c': pf([2, 1], ['CompDesk'], { orient: 'wall', paint: CHAIRS }),
    'C': pf([2, 2], ['CompIsland'], { paint: CHAIRS, flip: true }),
    'L': pf([4, 2], ['LabBench'], { flip: true }),
    'F': pf([2, 1], ['FumeHood'], { orient: 'wall' }),
    'x': one(['Skeleton'], 'edge'),
    'X': pf([2, 1], ['ChemCab'], { orient: 'wall' }),
    'M': pf([4, 1], ['DemoBench'], { face: 0 }), 'm': pf([4, 1], ['DemoBench'], { face: PI }),
    'w': pf([3, 2], ['RoboBench'], { flip: true }),
    'R': pf([6, 2], ['Reception'], { face: -R90 }),
    'o': pf([2, 1], ['OfficeDesk'], { flip: true }),
    'f': one(['FileCab'], 'edge'), 'p': one(['Copier'], 'edge'),
    's': pf([2, 1], ['Sofa'], { orient: 'wall' }),
    'y': pf([3, 1], ['Kitchenette'], { orient: 'wall' }),
    'Y': pf([2, 2], ['LoungeTable'], { paint: CHAIRS }),
    'i': one(['Bins'], 'random90'),
    'B': pf([2, 1], ['Bench'], { flip: true }),
    'j': one(['Plant'], 'random90'),
    'b': one(['BannerStand'], 'edge'),
    // ---- cafeteria and the library mezzanine
    'Z': pf([10, 3], ['Landmark_Serving'], { orient: 'wall' }),
    'l': pf([6, 2], ['CafTable'], { flip: true, paint: CAFE }),
    'v': one(['Vend_A', 'Vend_B'], 'edge', { alternate: true }),
    'z': pf([3, 1], ['TrayReturn'], { orient: 'wall' }),
    'W': one(['MilkCooler'], 'edge'),
    'N': pf([2, 7], ['Stair'], { face: 0, kind: 'step' }),
    'U': pf([2, 7], ['Stair'], { face: R90, kind: 'step' }),
    'I': one(['DeckColumn'], 0),
    'u': { deck: { thick: 0.4, color: '#5B6FA3', edge: '#F2EADA', under: '#F5EEDC', with: '|HJVja' } },
    '|': { pieces: ['RailHalf'], full: 'RailFull', links: '|', post: 'RailPost', kind: 'wall' },
    'H': pf([3, 1], ['Shelf'], { flip: true }),
    'J': pf([2, 2], ['ReadTable'], { paint: CHAIRS }),
    'V': pf([4, 2], ['LibDesk'], { face: 0 }),
    // ---- gym, lobby, locker and equipment rooms
    '{': pf([8, 5], ['Bleacher'], { face: 0, kind: 'step' }), '}': pf([8, 5], ['Bleacher'], { face: PI, kind: 'step' }),
    '>': pf([2, 1], ['Hoop'], { face: R90, collide: false }), '<': pf([2, 1], ['Hoop'], { face: -R90, collide: false }),
    '&': pf([14, 6], ['Stage'], { face: R90, kind: 'step' }),
    '%': pf([2, 1], ['Mats'], { flip: true }),
    '$': one(['BallCart'], 'random90'),
    ')': pf([2, 1], ['GearShelf'], { orient: 'wall' }),
    '9': pf([6, 2], ['SnackBar'], { orient: 'wall' }),
    '0': pf([2, 1], ['TicketTable'], { face: 0 }),
    // ---- courtyard
    '@': pf([9, 9], ['Landmark_Tree'], { face: 0 }),
    'r': pf([4, 2], ['PlanterA', 'PlanterB'], { flip: true }),
    '1': pf([2, 2], ['Picnic'], { flip: true }),
    '2': pf([4, 1], ['BikeRack'], { orient: 'wall' }),
    '3': pf([2, 4], ['Canopy_S', 'Canopy_M', 'Canopy_N'], { sequence: 'run' }),
    '4': pf([2, 2], ['Flagpole'], { face: 0 }),
    '5': one(['LampPost'], 0),
    '6': pf([10, 4], ['Tiers'], { face: 0, kind: 'step' }),
    '8': pf([2, 2], ['TreeGrate'], { flip: true }),
    // ---- floor finishes (0.006), the court (0.012), ceilings (4), roofs (8)
    '_': flat(['F_Epoxy']), '^': pf([6, 6], ['F_Crest'], { collide: false, face: 0 }),
    '[': pf([2, 2], ['F_Maple'], { collide: false, face: 0 }), ',': flat(['F_LawnA', 'F_LawnB'], { alternate: true }),
    ']': pf([28, 16], ['F_Court'], { collide: false, face: 0 }),
    '=': flat(['C_Tile']), '+': flat(['C_Light']), '-': pf([2, 2], ['C_Tile2'], { collide: false, face: 0 }),
    '*': pf([2, 2], ['C_Light2'], { collide: false, face: 0 }),
    ':': pf([2, 2], ['R_Coffer'], { collide: false, face: 0 }), ';': pf([2, 2], ['R_Pendant'], { collide: false, face: 0 }),
    '!': pf([2, 2], ['R_Sky'], { collide: false, face: 0 }), '/': pf([2, 2], ['R_Joist'], { collide: false, face: 0 }),
    '~': pf([2, 2], ['R_Deck'], { collide: false, face: 0 }),
    '?': pf([2, 2], ['R_JoistLamp'], { collide: false, face: 0 })
  };

  // glow companions (zones.js theme.glow): screens, lit cases and panels drawn unlit, glass additive
  var ADD = 'add';
  var GLOW = {
    Win: { piece: 'Win_Glow' }, Clere: { piece: 'Clere_Glow' }, Menu: { piece: 'Menu_Glow' },
    TC_L: { piece: 'TC_L_Glow', blend: ADD }, TC_M: { piece: 'TC_M_Glow', blend: ADD }, TC_R: { piece: 'TC_R_Glow', blend: ADD },
    OW_L: { piece: 'OW_Glass', blend: ADD }, OW_M: { piece: 'OW_Glass', blend: ADD }, OW_R: { piece: 'OW_Glass', blend: ADD },
    SB_L: { piece: 'SB_L_Glow' }, SB_R: { piece: 'SB_R_Glow' },
    C_Light: { piece: 'C_Light_Glow' }, C_Light2: { piece: 'C_Light2_Glow' }, R_Pendant: { piece: 'R_Pendant_Glow' }, R_Sky: { piece: 'R_Sky_Glow' },
    R_JoistLamp: { piece: 'R_JoistLamp_Glow' },
    CompDesk: { piece: 'CompDesk_Glow' }, CompIsland: { piece: 'CompIsland_Glow' }, OfficeDesk: { piece: 'OfficeDesk_Glow' },
    Reception: { piece: 'Reception_Glow' }, LibDesk: { piece: 'LibDesk_Glow' }, RoboBench: { piece: 'RoboBench_Glow' },
    FumeHood: { piece: 'FumeHood_Glass', blend: ADD }, ChemCab: { piece: 'ChemCab_Glass', blend: ADD },
    Landmark_Serving: { piece: 'Landmark_Serving_Glow', blend: ADD },
    Vend_A: { piece: 'Vend_A_Glow' }, Vend_B: { piece: 'Vend_B_Glow' }, SnackBar: { piece: 'SnackBar_Glow' },
    Canopy_S: { piece: 'Canopy_Glow' }, Canopy_M: { piece: 'Canopy_Glow' }, Canopy_N: { piece: 'Canopy_Glow' },
    LampPost: { piece: 'LampPost_Glow' }, GateFrame: { piece: 'GateFrame_Glow' }
  };

  var ART = ['LkA', 'LkB', 'LkC', 'WB_L', 'WB_M', 'WB_R', 'WB_T', 'Cork', 'PosterA', 'PosterB', 'PosterC', 'PosterMath', 'PosterCode',
    'PosterCell', 'Clock', 'Win', 'PT_L', 'PT_M', 'PT_R', 'EyeWash', 'FireExt', 'KitPass', 'Menu', 'Clere', 'Honor',
    'TC_L', 'TC_M', 'TC_R', 'Map_L', 'Map_M', 'Map_R', 'OW_L', 'OW_M', 'OW_R', 'Timeline', 'ArtA', 'ArtB', 'DoorBoys',
    'DoorGirls', 'DoorJan', 'Fountain', 'Pad', 'SB_L', 'SB_R', 'Banner0', 'Banner1', 'Banner2', 'Banner3', 'Flag0', 'Flag1',
    'Flag2', 'Flag3', 'XWin', 'XPipe', 'XDoor_L', 'XDoor_R'];
  Object.keys(SLICES).forEach(function (k) { for (var i = 0; i < SLICES[k][1]; i++) ART.push(SLICES[k][0] + i); });
  var PIECES = ['I', 'X'].concat(ART, ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Stand', 'C_TrailLight',
    'Backdrop_TreesA', 'Backdrop_TreesB']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  // ---------------------------------------------------------------- the trees round the courtyard (backdrop.build)
  /* Level-wide (nothing here belongs to a zone, so nothing switches or pops at the zone boundary): clusters of big
     trees beyond the courtyard's west, east and north wings, seen over the 8 m roofline from the courtyard only (zone 1
     and the gym are roofed). One merged mesh. */
  function buildTrees(level, api) {
    var Z = level.zones[1]; if (!Z) return;
    var hx = level.hatch ? level.hatch.x : Z.ox + Z.w / 2, hash = api.hash, k = 0;
    function put(x, z) {
      var h = hash(Math.round(x * 3), Math.round(z * 3));
      api.add(h < 0.5 ? 'Backdrop_TreesA' : 'Backdrop_TreesB', x, 0, z, h * 6.28, 0.9 + hash(k++, 7) * 0.5);
    }
    for (var z = Z.oz - 6; z < Z.oz + 46; z += 11) { put(Z.ox - 16 - hash(z, 1) * 12, z + hash(z, 2) * 4); put(Z.ox + Z.w + 16 + hash(z, 3) * 12, z + hash(z, 4) * 4); }
    for (var x = Z.ox - 14; x < Z.ox + Z.w + 16; x += 13) { if (Math.abs(x - hx) < 14) continue; put(x + hash(x, 5) * 5, Z.oz - 22 - hash(x, 6) * 12); }
  }

  IB.registerTheme({
    id: 'academy', name: 'Chalkstone Academy', family: 'kit-academy', prefix: 'KIT_ACADEMY_',
    palette: ['#3E5C86', '#E9B23B', '#B5583F', '#EFE5CD'],
    env: {
      sky: ['#5FA8E6', '#DCEEF8'], clear: '#BFD9EA', fog: { color: '#D8E3E8', near: 60, far: 170 }, clouds: true,
      sun: [-0.3, 0.86, 0.42],
      ceiling: { height: 4.0, color: '#F7F4EC', light: 'C_TrailLight', every: 3 }   // the trails and the hatch room only (zones: false)
    },
    // cream vinyl composition tile with 1 m joints (labs, the gym, the lawn and the crest come from "@layer 0.006")
    floor: {
      color: '#E4DAC3', trail: '#DDD2BA', outside: '#7CAB4D',
      lines: [{ dir: 'x', every: 1, width: 0.015, color: '#CFC3A8', y: 0.008 }, { dir: 'z', every: 1, width: 0.015, color: '#CFC3A8', y: 0.0105 }]
    },
    wall: { height: 8.0, roof: '#8D8A86', facing: 'open', choose: chooseWall, passage: { ch: DOORS, solid: [[2.5, 8.0]] } },
    dataLayers: [0.02, 0.03],
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 4.0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: buildTrees },
    budget: { prop: 2400, landmark: 4500, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    chooser: { codeAt: codeAt, outdoor: outdoor, runOf: runOf, artPiece: artPiece },
    levels: {
      academy: {
        name: 'Chalkstone Academy',
        intro: 'Robots have taken Chalkstone Academy in the middle of a school day. Clear the main building corridor by corridor, then fight through the gym and out across the courtyard.',
        zones: [
          // the main building: the entrance hall, corridors, classrooms, labs, the cafeteria and the library
          { map: 'academy_1', ceiling: false, label: 'The main building', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 5]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 7], ['blader', 4]],
            [['crawler', 15], ['drone', 6], ['gunner', 10], ['soldier', 6], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['gunner', 9], ['drone', 5], ['soldier', 5], ['blader', 3]]] },
          // the gymnasium and the courtyard
          { map: 'academy_2', ceiling: false, label: 'The gym and the courtyard',
            floor: { color: '#C8C2B6', lines: [{ dir: 'x', every: 2, width: 0.025, color: '#ACA598', y: 0.008 }, { dir: 'z', every: 2, width: 0.025, color: '#ACA598', y: 0.0105 }] },
            waves: [
              [['crawler', 18], ['gunner', 10], ['drone', 5], ['soldier', 6]],
              [['crawler', 15], ['drone', 7], ['gunner', 10], ['soldier', 6], ['blader', 4]],
              [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 5], ['blader', 4]],
              [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 4]],
              [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 2], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
