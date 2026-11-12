/* Theme: Metro Central (kit-metro) -- a deep-level underground station taken over by robots. Glazed cream tiles with a
   deep teal dado and a mustard line in the ticket hall, white tiles banded in the line colours on the platforms
   (Crimson Line red, Harbour Line blue), green-banded passages, buff stone under ribbed barrel vaults, terrazzo and
   granite. Two zones:
   1 The ticket hall (72 x 70): the street entrance in the south (WAY OUT signs, ticket machines along the wall), the
     unpaid hall under a 44 m vault with the DEPARTURES BOARD on its granite seat plinth (landmark), the station roundel
     in the floor, ticket machine islands, the ticket office's counter windows with queue barriers, a photo booth and
     the toilets; four walk-in shops along the west side (SNACKBOX kiosk with its open front, COGWHEEL COFFEE, PAPERCLIP
     NEWS, NIGHTJAR MART); the fare gate line (gates, the wide gates, glass screens); the paid concourse with the
     ESCALATOR WELL (4.5 m down: four escalators and two fixed stairs to the lower landing, whose passage to platforms
     3 - 4 is shuttered), balconies round it with benches, a coffee cart, light boxes and vending machines; the
     platform passage to the exit (PLATFORMS 1 - 2).
   2 The platforms (72 x 66): the entry hall from the connecting tunnel (lift, help point), the maintenance depot
     (workbenches, tool cages, cable drums, track trolleys, lockers) and the cross passage; under one 32 m vault side
     platform A (Crimson Line), track 1 with a stopped three-car train, the island platform with info pylons, the staff
     booth and the STATION CLOCK (landmark), track 2 with a stopped two-car Harbour Line train, side platform B; two
     footbridges over the tracks (4.5 m, a stair down to each platform); platform-end steps down into each trackbed
     (the trackbeds are walkable, 0.9 m down); tunnel mouths at both ends; the north passage with maintenance alcoves
     and the exit.
   Built by blender/fam_kit_metro.py (mt_*.py); zone layouts by tools/metro_zones.py (src/data/zones/metro_*.txt).
   Engine: theme.sunk (zones.js: sunk floors -- the trackbeds and the escalator well).

   A zone file has the floor plan and layers: "@layer 0.006" (finishes), "@layer 0.02" / "@layer 0.03" (data: wall art
   codes for the south / east and the north / west face of wall cells), "@layer 0.04" (data: sunk cells and the art on
   the sunk side faces round them), "@layer 0.05" (data: the finish scheme of each open cell), "@layer 2.9" (shop
   fascias), "@layer 3.2" (hanging screens), "@layer 4" (ceiling tiles), "@layer 4.5" (the footbridges), "@layer 8"
   (the vaults and their end walls).
   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled, front = +Z unless turned):
     # wall (8 m; the chooser faces every open side with its cell's finish, art overlays from the data layers)
     D d glass shop / office doorway [2,1] (in the wall line; front toward east / south resp. west / north)
     O kiosk open front [3,1]   n archway header (open floor)
     V ticket machines [3,1] (wall)   I ticket machine island [4,2]   Z the departures board [10,2] (landmark)
     F fare gate [2,1]   W wide gate [2,1]   | glass screen / balustrade (runs)   B bench [3,1]   b bin
     H help point   M map totem   Q queue barrier [3,1]   j planter   k vending machine   K coffee cart [2,1]
     L light box [2,1]   p photo booth [2,1] (wall)   X escalator bank [10,9] (top to the south)
     N fixed stair [5,9] (top to the south)   c shop counter [3,1] (wall)   C cafe bar [4,2] (wall)
     t cafe table [2,2]   g gondola [3,1]   f drinks cooler [2,1] (wall)   r magazine rack [2,1] (wall)
     R magazine island [3,1]   z freezer [2,1]   y stock shelf [2,1] (wall)   o office desk [2,1] (wall)
     s safe   l lockers [2,1] (wall)   T staff table [2,2]
     e x train [18,3] (cab cars at the run's ends; e Crimson, x Harbour line)   ~ track [2,3]
     1 2 trackbed steps [3,2] (rising south / north)   < > footbridge stair [8,2] (rising west / east)
     Y info pylon   @ the station clock [6,4] (landmark)   J staff booth [2,2] (front north)
     w tool cage [2,1] (wall)   q cable drum   m track trolley [2,1]   i cones   $ electrical cabinets [2,1] (wall)
     % workbench [3,1] (wall)
   Layers: ^ the floor mosaic [8,8] (0.006)   3 4 5 6 shop fascias [7,1] (2.9: kiosk, cafe, news, mart)
     7 8 hanging departure screen (facing north-south / east-west)   9 hanging TRAINS sign (3.2)
     - * = + ceiling tiles [2,2] / lit [2,2] / tile / light (4)   u footbridge deck   ] its rail (runs) (4.5)
     ( ) the hall vault bay [44,2] / with pendants   { } its north / south end wall [44,1]
     : ; the platform vault bay [2,32] / with light fittings   ! ? its west / east end wall [1,32] (8)
   Wall art codes (0.02: the S / E face, 0.03: the N / W face; data, never symbols):
     a poster  A billboard (3)  m network map (2)  x WAY OUT  X WAY OUT (2)  P platforms sign (2) / platform sign
     n station name panel CENTRAL (3)  f fire point  k clock  u menu board  g G women / men toilets (2)
     S staff door  b notice board  L lift (2)  U tunnel mouth (3)  Y platform end sign
     w shop window (run, through the wall)  T ticket windows (run, through the wall)
   Sunk cells (0.04): t trackbed (0.9 m)  w escalator well (4.5 m); side art on the cells round the well: U the
     closed shutter (3+)  n name panel (3)  a poster  m PLATFORMS 3 - 4 CLOSED sign
   Schemes (0.05): h hall  p passage  e entry hall  o office / depot  k f n m the shops  r b i platforms */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, PI = Math.PI;

  // ---------------------------------------------------------------- walls
  var DOORS = 'DOd', WALLISH = '#GE' + DOORS;
  var SIDES = ['S', 'N', 'E', 'W'];
  var STEP = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var FYAW = { S: 0, N: PI, E: R90, W: -R90 };
  var RIGHT = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };   // the viewer's right along a face
  var SCHEME = { h: 'IH', p: 'IP', e: 'IE', o: 'IO', k: 'IK', f: 'IF', n: 'IN', m: 'IM', r: 'IR', b: 'IB', i: 'II' };
  function wl(g, c, r) { return WALLISH.indexOf(g.at(c, r)) >= 0; }
  function data(g, y) {
    var key = '_mt' + y;
    if (g[key] === undefined) { g[key] = null; (g.layers || []).forEach(function (l) { if (Math.abs(l.y - y) < 1e-4) g[key] = l; }); }
    return g[key];
  }
  function codeAt(g, c, r, side) { var L = data(g, side === 'S' || side === 'E' ? 0.02 : 0.03); return L ? L.at(c, r) : '.'; }
  function schemeAt(g, c, r) { var L = data(g, 0.05); return L ? L.at(c, r) : '.'; }
  function gateCell(g, c, r) {   // the gate frame covers the gate and one wall cell either side of it
    if (r !== 0 && r !== g.h - 1) return false;
    var ch = r === 0 ? 'G' : 'E';
    for (var dc = -1; dc <= 1; dc++) if (g.at(c + dc, r) === ch) return true;
    return false;
  }
  // a run of one code along the wall: [index from the viewer's left, length, first cell c, r]
  function runOf(g, c, r, side, code) {
    var R = RIGHT[side], k = 0;
    while (k < 40 && codeAt(g, c - R[0] * (k + 1), r - R[1] * (k + 1), side) === code && wl(g, c - R[0] * (k + 1), r - R[1] * (k + 1))) k++;
    var m = 0; while (m < 40 && codeAt(g, c + R[0] * (m + 1), r + R[1] * (m + 1), side) === code && wl(g, c + R[0] * (m + 1), r + R[1] * (m + 1))) m++;
    return [k, k + 1 + m, c - R[0] * k, r - R[1] * k];
  }
  function ends(k, n, L, M, R) { return n === 1 ? M : k === 0 ? L : k === n - 1 ? R : M; }
  function pair(k, n, L, R) { return k % 2 === 0 ? L : R; }
  // the art overlay for a face (or a through piece: shop windows, ticket windows)
  function artPiece(g, c, r, side, code, hash) {
    var run, h = hash(c * 7 + 3, r * 11 + 5);
    switch (code) {
      case 'a': return 'Ad' + (1 + Math.floor(h * 4) % 4);
      case 'A': run = runOf(g, c, r, side, code); return (hash(run[2] * 5 + 1, run[3] * 9 + 2) < 0.5 ? 'BigA_' : 'BigB_') + ends(run[0], run[1], 'L', 'M', 'R');
      case 'm': run = runOf(g, c, r, side, code); return pair(run[0], run[1], 'Map_L', 'Map_R');
      case 'x': return 'WayOut';
      case 'X': run = runOf(g, c, r, side, code); return pair(run[0], run[1], 'Exit_L', 'Exit_R');
      case 'P':
        run = runOf(g, c, r, side, code);
        if (run[1] > 1) return pair(run[0], run[1], 'Plat_L', 'Plat_R');
        return schemeAt(g, c + STEP[side][0], r + STEP[side][1]) === 'b' ? 'PlatB' : 'PlatR';
      case 'n': run = runOf(g, c, r, side, code); return 'Name_' + ends(run[0], run[1], 'L', 'M', 'R');
      case 'f': return 'FirePt';
      case 'k': return 'Clock';
      case 'u': return 'Menu';
      case 'g': run = runOf(g, c, r, side, code); return pair(run[0], run[1], 'WCW_L', 'WCW_R');
      case 'G': run = runOf(g, c, r, side, code); return pair(run[0], run[1], 'WCM_L', 'WCM_R');
      case 'S': return 'StaffDoor';
      case 'b': return 'Notice';
      case 'L': run = runOf(g, c, r, side, code); return pair(run[0], run[1], 'Lift_L', 'Lift_R');
      case 'U': run = runOf(g, c, r, side, code); return 'Tun_' + ends(run[0], run[1], 'L', 'M', 'R');
      case 'Y': return 'EndSign';
      case 'w': run = runOf(g, c, r, side, code); return 'SW_' + ends(run[0], run[1], 'L', 'M', 'R');
      case 'T': run = runOf(g, c, r, side, code); return 'TW_' + ends(run[0], run[1], 'L', 'M', 'R');
    }
    return null;
  }
  /* One finish face (modelled on a cell's front face) per open side of the cell, turned to that side (the engine
     turns the cell by its own rule, the chooser hands each piece the extra turn), in the scheme of the cell it looks
     onto; an art code stacks its overlay on it; a through piece (a shop window, the ticket windows) fills the cell. */
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    if (face === 'none' || gateCell(g, c, r) || DOORS.indexOf(g.at(c, r)) >= 0) return null;   // door pieces draw their own wall
    var open = SIDES.filter(function (s) { return !wl(g, c + STEP[s][0], r + STEP[s][1]); });
    if (!open.length) return null;
    var yaw = face === 'corner' ? (!horiz && (wl(g, c, r - 1) || wl(g, c, r + 1)) ? R90 : 0) : FYAW[face];
    var plainOnly = face === 'corner', out = [];
    for (var i = 0; i < open.length; i++) {
      var s = open[i], nc = c + STEP[s][0], nr = r + STEP[s][1], t = FYAW[s] - yaw;
      var code = plainOnly ? '.' : codeAt(g, c, r, s), art = code !== '.' ? artPiece(g, c, r, s, code, hash) : null;
      if (art && /^(SW|TW)_/.test(art)) return [{ piece: art, turn: t }];   // through the wall: it is the whole cell
      var plain = SCHEME[schemeAt(g, nc, nr)] || 'IH';
      out.push(t ? { piece: plain, turn: t } : plain);
      if (art) out.push(t ? { piece: art, turn: t } : art);
    }
    return out;
  }

  // ---------------------------------------------------------------- sunk floors: the trackbeds, the escalator well
  function sunkCode(g, c, r) { var L = data(g, 0.04); return L ? L.at(c, r) : '.'; }
  function isSunk(g, c, r) { var k = sunkCode(g, c, r); return k === 't' || k === 'w'; }
  /* the face down from a higher cell (c, r) into the sunk cell (c + dc, r + dr): platform edges (trimmed at their
     right end where the cell also drops away on that side, so two coping bands never overlap), the trackbed's end
     walls (dark under a tunnel mouth), the escalator well's tiled walls with their art (the codes on the rim cells) */
  function sunkSide(c, r, dc, dr, code, g, hash) {
    var right = [dr, -dc];   // the viewer's right, standing in the sunk cell facing the side
    if (code === 't') {
      if (g.at(c, r) === '#') {
        var side = dc > 0 ? 'E' : dc < 0 ? 'W' : dr > 0 ? 'S' : 'N';
        return codeAt(g, c, r, side) === 'U' ? 'TunBase' : 'WallBase';
      }
      var st = g.at(c + dc, r + dr);
      if (st === '1' || st === '2') return 'EdgeP';   // beside the trackbed steps: a plain face, the steps land flush
      return isSunk(g, c + right[0], r + right[1]) ? 'EdgeR' : 'Edge';
    }
    var a = sunkCode(g, c, r);
    if (a === 'U' || a === 'n') {
      var k = 0, n = 1;
      while (k < 20 && sunkCode(g, c - right[0] * (k + 1), r - right[1] * (k + 1)) === a) k++;
      while (n + k < 40 && sunkCode(g, c + right[0] * n, r + right[1] * n) === a) n++;
      n += k;
      var p = n === 1 ? 'M' : k === 0 ? 'L' : k === n - 1 ? 'R' : 'M';
      return (a === 'U' ? 'WellSh_' : 'WellN_') + p;
    }
    if (a === 'a') return hash(c * 3 + 1, r * 7 + 2) < 0.5 ? 'WellAd' : 'WellAd2';
    if (a === 'm') return 'WellMap';
    return 'WellWall';
  }

  // ---------------------------------------------------------------- symbols
  // palette cells (blender/mt_base.py): crim 14, crimD 15, blue 16, blueD 17
  var HARBOUR = { from: [14, 15], to: [[16, 17]] };
  function pf(size, pieces, extra) { return Object.assign({ size: size, pieces: pieces, kind: 'cover' }, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, rotate: rot, kind: 'cover' }, extra || {}); }
  function flat(pieces, extra) { return Object.assign({ pieces: pieces, collide: false, rotate: 0 }, extra || {}); }
  var SYMBOLS = {
    // ---- doorways (wall.passage cells: the lintel collides, the door piece does not)
    'D': pf([2, 1], ['Door2'], { orient: 'span', kind: 'wall', collide: false }),
    'd': pf([2, 1], ['Door2'], { orient: 'span', kind: 'wall', collide: false, turn: PI }),
    'O': pf([3, 1], ['Front3'], { orient: 'span', kind: 'wall', collide: false }),
    'n': { pieces: ['Header'], rotate: 'run', collide: false },
    // ---- the ticket hall
    'V': pf([3, 1], ['TVM3'], { orient: 'wall' }),
    'I': pf([4, 2], ['TVMIsland'], { face: 0 }),
    'Z': pf([10, 2], ['Landmark_Board'], { face: 0 }),
    'F': pf([2, 1], ['FareGate'], { face: 0 }),
    'W': pf([2, 1], ['FareWide'], { face: 0 }),
    '|': { pieces: ['GRailHalf'], full: 'GRailFull', links: '|', post: 'GRailPost', kind: 'wall' },
    'B': pf([3, 1], ['Bench'], { orient: 'wall', flip: true }),
    'b': one(['Bin'], 'random90'),
    'H': one(['HelpPt'], 'edge'),
    'M': one(['MapTotem'], 'edge'),
    'Q': pf([3, 1], ['QueueBar']),
    'j': one(['Plant'], 'random90'),
    'k': one(['Vend'], 'edge'),
    'K': pf([2, 1], ['CoffeeCart'], { flip: true }),
    'L': pf([2, 1], ['LightBox'], { face: 0 }),
    'p': pf([2, 1], ['PhotoBooth'], { orient: 'wall' }),
    'X': pf([10, 9], ['EscBank'], { face: 0, kind: 'step' }),
    'N': pf([5, 9], ['Stair'], { face: 0, kind: 'step' }),
    // ---- shops, the ticket office
    'c': pf([3, 1], ['Counter'], { orient: 'wall' }),
    'C': pf([4, 2], ['CafeBar'], { orient: 'wall' }),
    't': pf([2, 2], ['CafeTable'], { flip: true }),
    'g': pf([3, 1], ['Gondola'], { flip: true }),
    'f': pf([2, 1], ['Cooler'], { orient: 'wall' }),
    'r': pf([2, 1], ['MagRack'], { orient: 'wall' }),
    'R': pf([3, 1], ['MagIsland'], { flip: true }),
    'z': pf([2, 1], ['Freezer'], { flip: true }),
    'y': pf([2, 1], ['Shelf'], { orient: 'wall' }),
    'o': pf([2, 1], ['OfficeDesk'], { orient: 'wall' }),
    's': one(['Safe'], 'edge'),
    'l': pf([2, 1], ['Lockers'], { orient: 'wall' }),
    'T': pf([2, 2], ['StaffTable'], { flip: true }),
    // ---- the platforms
    'e': pf([18, 3], ['CarTail', 'CarMid', 'CarHead'], { sequence: 'run', face: 0, kind: 'step' }),
    'x': pf([18, 3], ['CarTail', 'CarMid', 'CarHead'], { sequence: 'run', face: 0, kind: 'step', paint: HARBOUR }),
    '~': pf([2, 3], ['Track'], { face: 0, collide: false }),
    '1': pf([3, 2], ['Steps'], { face: 0, kind: 'step' }),
    '2': pf([3, 2], ['Steps'], { face: PI, kind: 'step' }),
    '<': pf([8, 2], ['BStair'], { face: PI, kind: 'step' }),
    '>': pf([8, 2], ['BStair'], { face: 0, kind: 'step' }),
    'Y': one(['Column'], 0),
    '@': pf([6, 4], ['Landmark_Clock'], { face: 0 }),
    'J': pf([2, 2], ['Booth'], { face: PI }),
    'w': pf([2, 1], ['ToolCage'], { orient: 'wall' }),
    'q': one(['Drum'], 'random90'),
    'm': pf([2, 1], ['Trolley'], { flip: true }),
    'i': one(['Cones'], 'random90'),
    '$': pf([2, 1], ['ElecCab'], { orient: 'wall' }),
    '%': pf([3, 1], ['Workbench'], { orient: 'wall' }),
    // ---- layers: the mosaic (0.006), fascias (2.9), hanging screens (3.2), ceilings (4), footbridges (4.5), vaults (8)
    '^': pf([8, 8], ['F_Mosaic'], { collide: false, face: 0 }),
    '3': pf([7, 1], ['SignK'], { collide: false, face: R90 }), '4': pf([7, 1], ['SignF'], { collide: false, face: R90 }),
    '5': pf([7, 1], ['SignN'], { collide: false, face: R90 }), '6': pf([7, 1], ['SignM'], { collide: false, face: R90 }),
    '7': flat(['PID']), '8': flat(['PID'], { rotate: R90 }), '9': flat(['HangSign']),
    '=': flat(['C_Tile']), '+': flat(['C_Light']), '-': pf([2, 2], ['C_Tile2'], { collide: false, face: 0 }),
    '*': pf([2, 2], ['C_Light2'], { collide: false, face: 0 }),
    'u': { deck: { thick: 0.4, color: '#B2A895', edge: '#5D6671', under: '#8D8A84', with: ']' } },
    ']': { pieces: ['BRailHalf'], full: 'BRailFull', links: ']', post: 'BRailPost', kind: 'wall' },
    '(': pf([44, 2], ['VaultH'], { collide: false, face: 0 }), ')': pf([44, 2], ['VaultHL'], { collide: false, face: 0 }),
    '{': pf([44, 1], ['VEndN'], { collide: false, face: 0 }), '}': pf([44, 1], ['VEndS'], { collide: false, face: PI }),
    ':': pf([2, 32], ['VaultP'], { collide: false, face: 0 }), ';': pf([2, 32], ['VaultPL'], { collide: false, face: 0 }),
    '!': pf([1, 32], ['PEnd'], { collide: false, face: 0 }), '?': pf([1, 32], ['PEnd'], { collide: false, face: PI })
  };

  // glow companions (zones.js theme.glow): screens, lit signs and fittings drawn unlit, glass additive
  var ADD = 'add';
  var GLOW = {
    Door2: { piece: 'Door2_Glow', blend: ADD },
    SW_L: { piece: 'SW_Glass', blend: ADD }, SW_M: { piece: 'SW_Glass', blend: ADD }, SW_R: { piece: 'SW_Glass', blend: ADD },
    TW_L: { piece: 'TW_Glass', blend: ADD }, TW_M: { piece: 'TW_Glass', blend: ADD }, TW_R: { piece: 'TW_Glass', blend: ADD },
    TVM3: { piece: 'TVM3_Glow' }, TVMIsland: { piece: 'TVMIsland_Glow' }, FareGate: { piece: 'FareGate_Glow' }, FareWide: { piece: 'FareGate_Glow' },
    HelpPt: { piece: 'HelpPt_Glow' }, Vend: { piece: 'Vend_Glow' }, LightBox: { piece: 'LightBox_Glow' },
    CafeBar: { piece: 'CafeBar_Glow' }, Cooler: { piece: 'Cooler_Glow' }, OfficeDesk: { piece: 'OfficeDesk_Glow' },
    Landmark_Board: { piece: 'Landmark_Board_Glow' }, Landmark_Clock: { piece: 'Landmark_Clock_Glow' },
    Booth: { piece: 'Booth_Glow', blend: ADD }, ElecCab: { piece: 'ElecCab_Glow' }, PID: { piece: 'PID_Glow' },
    CarHead: { piece: 'CarHead_Glow' }, CarMid: { piece: 'CarMid_Glow' }, CarTail: { piece: 'CarTail_Glow' },
    VaultHL: { piece: 'VaultHL_Glow' }, VaultPL: { piece: 'VaultPL_Glow' },
    C_Light: { piece: 'C_Light_Glow' }, C_Light2: { piece: 'C_Light2_Glow' }, GateFrame: { piece: 'GateFrame_Glow' }
  };

  var ART = ['Ad1', 'Ad2', 'Ad3', 'Ad4', 'Map_L', 'Map_R', 'WayOut', 'Exit_L', 'Exit_R', 'Plat_L', 'Plat_R', 'PlatR', 'PlatB',
    'Name_L', 'Name_M', 'Name_R', 'FirePt', 'Clock', 'Menu', 'WCW_L', 'WCW_R', 'WCM_L', 'WCM_R', 'StaffDoor', 'Notice',
    'Lift_L', 'Lift_R', 'Tun_L', 'Tun_M', 'Tun_R', 'EndSign', 'SW_L', 'SW_M', 'SW_R', 'TW_L', 'TW_M', 'TW_R'];
  ['A', 'B'].forEach(function (v) { ['L', 'M', 'R'].forEach(function (p) { ART.push('Big' + v + '_' + p); }); });
  var SUNK = ['Edge', 'EdgeR', 'EdgeP', 'TunBase', 'WallBase', 'WellWall', 'WellAd', 'WellAd2', 'WellMap', 'WellN_L', 'WellN_M', 'WellN_R',
    'WellSh_L', 'WellSh_M', 'WellSh_R'];
  var PIECES = Object.keys(SCHEME).map(function (k) { return SCHEME[k]; }).concat(ART, SUNK,
    ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Stand', 'C_TrailLight']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'metro', name: 'Metro Central', family: 'kit-metro', prefix: 'KIT_METRO_',
    palette: ['#1E6B67', '#E2A62E', '#C9353D', '#EADFC4'],
    env: {
      sky: null, clear: '#1B1F27', fog: { color: '#2B303A', near: 55, far: 150 }, clouds: false,
      sun: [0.3, 0.88, 0.36],
      ceiling: { height: 3.6, color: '#E3E6DE', light: 'C_TrailLight', every: 3 }   // the trails and the hatch room only (zones: false)
    },
    // terrazzo with 1 m joints (the platforms' granite paving is zone 2's own floor)
    floor: {
      color: '#D8D0BF', trail: '#CFC7B5',
      lines: [{ dir: 'x', every: 1, width: 0.015, color: '#C4BBA8', y: 0.008 }, { dir: 'z', every: 1, width: 0.015, color: '#C4BBA8', y: 0.0105 }]
    },
    wall: { height: 8.0, roof: '#3A3D45', facing: 'open', choose: chooseWall, passage: { ch: DOORS, solid: [[2.6, 8.0]] } },
    dataLayers: [0.02, 0.03, 0.04, 0.05],
    sunk: { layer: 0.04, depth: { t: 0.9, w: 4.5 }, side: sunkSide,
      floor: { t: '#57524C', w: { color: '#D8D0BF', lines: [{ dir: 'x', every: 1, width: 0.015, color: '#C4BBA8', y: 0.008 }, { dir: 'z', every: 1, width: 0.015, color: '#C4BBA8', y: 0.0105 }] } } },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 3.6 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: null,   // underground: no ground plane round the level (it would cover the trackbeds and the well)
    budget: { prop: 2500, landmark: 4500, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    chooser: { codeAt: codeAt, schemeAt: schemeAt, runOf: runOf, artPiece: artPiece, sunkSide: sunkSide, isSunk: isSunk },
    levels: {
      metro: {
        name: 'Metro Central',
        intro: 'Robots have taken over Metro Central at rush hour. Fight through the ticket hall and down past the escalators, then cross the platforms -- through the stopped trains, over the footbridges or along the tracks -- to the far passage.',
        zones: [
          // the ticket hall, the shops, the fare gates, the escalator well
          { map: 'metro_1', ceiling: false, label: 'The ticket hall', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 5]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 8], ['blader', 5]],
            [['crawler', 15], ['drone', 6], ['gunner', 10], ['soldier', 7], ['blader', 5]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['gunner', 9], ['drone', 5], ['soldier', 5], ['blader', 3]]] },
          // the platforms, the trains, the footbridges, the passages
          { map: 'metro_2', ceiling: false, label: 'The platforms',
            floor: { color: '#A9A49B', trail: '#CFC7B5', lines: [{ dir: 'x', every: 1, width: 0.02, color: '#97928A', y: 0.008 }, { dir: 'z', every: 1, width: 0.02, color: '#97928A', y: 0.0105 }] },
            waves: [
              [['crawler', 18], ['gunner', 10], ['drone', 5], ['soldier', 6]],
              [['crawler', 15], ['drone', 7], ['gunner', 10], ['soldier', 7], ['blader', 5]],
              [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 6], ['blader', 5]],
              [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 3]],
              [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 1], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
