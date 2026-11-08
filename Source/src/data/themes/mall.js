/* Theme: Galleria Mall (kit-mall) -- a two-storey shopping mall under a glazed roof.
   Each zone is an atrium: shopfronts on two storeys (9.5 m walls), a 7 m mezzanine ring at 4.5 m ('u' in the
   "@layer 4.5" grid of the zone file) with baluster railings ('r') and columns ('i' over / 'I' under the slab edge),
   two escalators ('N' rises north, 'V' rises south) and a glass lift ('L' door west, 'J' door east) with sliding doors
   that shuttles between the floors. Robots spawn on both floors and climb the escalators (stair-block collision,
   kind 'step') to reach the player. The floor inlays live in an "@layer 0" grid, the roof (glazed coffers, trusses with
   banners, downlights) in an "@layer 9.5" grid. Built by blender/fam_kit_mall.py; zone layers by tools/mall_zones.py.

   Symbols (floor plan)                        Symbols (mezzanine layer, 4.5)      Floor inlays (layer 0)
     N / V  escalator [2,10] north / south        u  deck   r  railing              x y  diamonds (terracotta, teal)
     L / J  glass lift [3,3], door west / east    i  column (deck - ceiling)        =  border band   +  band knot
     F  fountain [4,4]   Q  Guest Services [4,4]  l  downlight under the deck       M  compass rose [8,8]
     O  palm planter [2,2]  o  flower planter     o B c S a h  props / spawns       k  food-court checker
     B  bench [2,1]  c  bin  d  directory totem                                     w  entrance mat [3,2]
     K  kiosk [3,2]  T  food-court table [2,2]   Roof (layer 9.5)
     D  podium [2,1]  Y  food stall [4,2]          ~  glazed coffers [4,4]   &  coffers + truss [4,4]
     I  column under the deck edge                 %  $  truss tiles with banners [4,4]   :  downlight

   Walk-in shops (both storeys): tools/mall_zones.py adds a 7-cell band behind the west and east walls and opens 5 of
   the 8 bays per side (where the approach is clear) into 5 x 6 m rooms: a room symbol on the plan (A Z C R W U: Atelier,
   SIGNAL, The Coffee House, Northfield Books, Toy Workshop, Aurum) and on the mezzanine layer (g v b m t: Shoe Gallery,
   Lumen Optics, Bakehouse, Hearth & Home, Leatherworks) places the furnished room piece (blender/mall_rooms.py); the
   bay's three middle cells are doorways ('n', wall.passage) and its windows keep a display bed. The other bays stay
   window-only, Field & Court stays shuttered. Spawns stay in the hall; two ground-floor shops per zone hold a pickup.

   Walls: every wall cell stacks two storefront modules (ground 'Lo_', upper 'Up_'), so the chooser returns a list.
   Bays are 6 m: a pilaster, then five modules (window, sign-left, door, sign-right, window) of one brand per storey;
   the shop name (vector lettering, blender/ib_text.py) runs over the middle three. On the N and E faces the modules come mirrored (the
   engine turns them to face the open side), so sign-left / sign-right and the two windows swap there. */
(function (IB) {
  'use strict';
  var BRANDS = ['rose', 'sky', 'orange', 'mint', 'gold', 'violet'];
  var POS = ['WinA', 'SignL', 'Door', 'SignR', 'WinB'];
  /* Walk-in shops (tools/mall_zones.py): a 7-cell band behind the west and east walls holds 5 x 6 m shop rooms behind
     some bays, on both storeys. The plan cell of a room names the ground-storey shop, its "@layer 4.5" cell the upper
     one; the bay's three middle wall cells are doorways ('n', wall.passage: solid only above each storey's opening),
     the two windows keep their glass with a display bed behind. The room piece draws the floor, walls, ceiling and
     fittings; the band's own wall cells get no module. */
  var LO_ROOM = { A: 'rose', Z: 'sky', C: 'orange', R: 'mint', W: 'gold', U: 'violet' };
  var UP_ROOM = { g: 'rose', v: 'sky', b: 'orange', m: 'mint', t: 'violet' };
  var ROOM_PIECE = { A: 'Room_Atelier', Z: 'Room_Signal', C: 'Room_Coffee', R: 'Room_Books', W: 'Room_Toys', U: 'Room_Aurum',
    g: 'Room_Shoes', v: 'Room_Optics', b: 'Room_Bakery', m: 'Room_Home', t: 'Room_Leather' };
  var POS_W = ['WinAW', 'OpenL', 'OpenC', 'OpenR', 'WinBW'];
  // shop band depth: the cells left of the hall in the zone's first open row (0 without walk-in shops)
  function band(grid) {
    if (grid._mallBand === undefined) { var row = grid.rows[1] || '', i = 0; while (row[i] === '#') i++; grid._mallBand = Math.max(0, i - 1); }
    return grid._mallBand;
  }
  function layerAt(grid, y) { return (grid.layers || []).filter(function (L) { return L.y === y; })[0] || null; }
  // a shop front with its room behind it is open on both sides: it faces the hall
  function faceOf(c, r, grid, face) {
    if (face === 'none' || face === 'corner') return null;
    var B = band(grid);
    return c === B ? 'E' : c === grid.w - 1 - B ? 'W' : null;
  }
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  // centre of the gate opening (G / E cells) in row r, or null
  function gateC(grid, r) {
    var cache = grid._mallGate || (grid._mallGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows[r] || '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  /* Bays run from each zone corner (and, on the N / S walls, from both corners toward the gate): a pilaster on the
     cell next to the corner, then 5 shop modules and a pilaster, repeating. The cell next to a corner is always a
     pilaster (nothing of it reaches the corner square, where the two walls' frames would otherwise meet). Cells too
     close to a gate or to the far end for a whole bay get blank (directory / poster) modules; E / W walls end on a
     pilaster beside the far corner too. */
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var B = band(grid);
    if (c < B || c > grid.w - 1 - B) return null;   // a shop room's walls: drawn by the room piece
    if (face === 'corner' || face === 'none') return 'Corner_' + (r < grid.h / 2 ? 'N' : 'S') + (c < grid.w / 2 ? 'W' : 'E');
    var cA = c;   // absolute column (neighbour lookups); c is counted from the hall's west wall below
    c -= B;
    var ns = face === 'S' || face === 'N', line = ns ? r : c + 100, k, bay, ok;
    if (ns ? (c === 1 || c === grid.w - 2 * B - 2) : (r === 1 || r === grid.h - 2)) return 'Pilaster_C';
    if (ns) {   // beside a gate: the trail corridor runs behind these cells, so no shop interior there
      var g = gateC(grid, r), W = grid.w - 2 * B;
      if (g !== null) g -= B;
      if (g !== null) { var d = Math.abs(c + 0.5 - g); if (d < 2.6) return 'GateSide'; if (d < 3.6) return 'Blank_Map'; }
      if (g === null) g = W;
      if (c + 0.5 < g) { k = (c - 1) % 6; bay = Math.floor((c - 1) / 6); ok = c - k + 5 + 0.5 < g - 3.6; }
      else { var k2 = (W - 2 - c) % 6; k = k2 ? 6 - k2 : 0; bay = 20 + Math.floor((W - 2 - c) / 6); ok = c - k + 1 + 0.5 > g + 3.6; }
    } else {
      var Hh = grid.h;
      k = (r - 1) % 6; bay = Math.floor((r - 1) / 6); ok = r - k + 5 <= Hh - 3;
    }
    if (k === 0) return 'Pilaster';
    // a walk-in bay: the room behind names both shops
    var bc = cA + (face === 'E' ? -1 : face === 'W' ? 1 : 0), br = r + (face === 'S' ? -1 : face === 'N' ? 1 : 0);
    var lb = LO_ROOM[grid.at(bc, br)], L45 = layerAt(grid, 4.5), ub = L45 && UP_ROOM[L45.at(bc, br)];
    if (lb && ub) { var pw = POS_W[(face === 'N' || face === 'E') ? 5 - k : k - 1]; return ['Lo_' + lb + '_' + pw, 'Up_' + ub + '_' + pw]; }
    // a food stall stands against this cell (it fills the ground storey): a plain wall below, the shop above
    var stall = grid.at(cA + (face === 'E' ? 1 : face === 'W' ? -1 : 0), r + (face === 'S' ? 1 : face === 'N' ? -1 : 0)) === 'Y';
    if (!stall && !ok) return k % 2 ? 'Blank_Ad' : 'Blank_Map';
    if (!stall && (k === 1 || k === 5) && !ns && hh(bay * 3 + k, line) < 0.2) return k === 1 ? 'Blank_Ad' : 'Blank_Map';
    var b0 = Math.floor(hh(line, 3) * 6), lo = BRANDS[(bay * 5 + b0) % 6], up = BRANDS[(bay * 5 + b0 + 3 + (hh(line, 9) < 0.5 ? 0 : 1)) % 6];
    var p = POS[(face === 'N' || face === 'E') ? 5 - k : k - 1];
    return [stall ? 'Lo_Plain' : 'Lo_' + lo + '_' + p, 'Up_' + up + '_' + p];
  }
  var WALLS = ['Pilaster', 'Pilaster_C', 'Lo_Plain', 'Blank_Map', 'Blank_Ad', 'GateSide', 'Corner_NW', 'Corner_NE', 'Corner_SW', 'Corner_SE'];
  BRANDS.forEach(function (b) { POS.forEach(function (p) { WALLS.push('Lo_' + b + '_' + p, 'Up_' + b + '_' + p); }); });
  Object.keys(LO_ROOM).forEach(function (k) { POS_W.forEach(function (p) { WALLS.push('Lo_' + LO_ROOM[k] + '_' + p); }); });
  Object.keys(UP_ROOM).forEach(function (k) { POS_W.forEach(function (p) { WALLS.push('Up_' + UP_ROOM[k] + '_' + p); }); });
  var ROOMS = Object.keys(ROOM_PIECE).map(function (k) { return ROOM_PIECE[k]; });
  var OTHER = ['Rail', 'RailFull', 'RailPost', 'Column_Lo', 'Column_Hi', 'Escalator', 'Landmark_ElevatorShaft', 'Elevator_Cab',
    'Elevator_CabDoor', 'Elevator_LandDoor', 'Planter', 'Planter_B', 'BigPlanter', 'Bench', 'Bin', 'AdPillar', 'Kiosk_A', 'Kiosk_B', 'Kiosk_C',
    'FoodTable', 'FoodTable_B', 'Stall_Pizza', 'Stall_Noodle', 'Stall_Burger', 'Display', 'Landmark_Fountain', 'Landmark_GuestDesk',
    'Inlay_A', 'Inlay_B', 'Inlay_Band', 'Inlay_Knot', 'Inlay_Rose', 'Inlay_ChkA', 'Inlay_ChkB', 'Mat',
    'Skylight', 'SkylightLamp', 'SkyTruss', 'SkyTrussBanA', 'SkyTrussBanB', 'CeilLight', 'UnderLight',
    'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Ad', 'Hatch'];
  // the glass lift: a 2.5 m cab between 0 and 4.5 m; centre-parting doors on the cab and on each landing (1.3 m
  // doorway), held open while anyone stands in the doorway; a walkable sill bridges the cab and the upper landing
  function room(ch) { return { size: [5, 6], pieces: [ROOM_PIECE[ch]], orient: 'open', kind: 'cover' }; }
  var LIFT = { top: 4.5, wait: 4.0, speed: 1.4, cab: 'Elevator_Cab', inner: [2.5, 2.5], floor: 0.06, wall: 2.4,
    doors: { cab: 'Elevator_CabDoor', landing: 'Elevator_LandDoor', width: 1.3, slide: 0.6, time: 0.8, cabZ: 1.29, landZ: [1.39, 1.45], half: 1.42 } };

  IB.registerTheme({
    id: 'mall', name: 'Galleria Mall', family: 'kit-mall', prefix: 'KIT_MALL_',
    palette: ['#EE6F8C', '#2E9E95', '#F0B840', '#EADFCB'],
    env: {
      sky: null, clear: '#EFE3CF', fog: { color: '#EFE3CF', near: 50, far: 135 }, clouds: false,
      // low southern light (like the office): floors and south faces lit, the ceiling in the light 0.9 band
      sun: [0.3, 0.45, 0.84],
      ceiling: { height: 9.5, color: '#F7F1E6' }   // fittings are placed by the zone's roof layer
    },
    // warm marble, 1 m tiles with sand grout (inlays on top come from the zone's "@layer 0" grid)
    floor: {
      color: '#ECE1CC', trail: '#E6D9C1', outside: '#ECE1CC',
      lines: [{ dir: 'x', every: 1, width: 0.025, color: '#DCCCB0', y: 0.008 }, { dir: 'z', every: 1, width: 0.025, color: '#DCCCB0', y: 0.0105 }]
    },
    // doorway cells ('n'): open below 3.0 m (ground) and from the deck at 4.5 m to 7.3 m (upper); lintels between
    wall: { height: 9.5, roof: '#E9E0D2', facing: 'open', choose: chooseWall, faceOf: faceOf, passage: { ch: 'n', solid: [[3.0, 4.1], [7.3, 9.5]] } },
    symbols: {
      'N': { size: [2, 10], pieces: ['Escalator'], face: 0, kind: 'step' },
      'V': { size: [2, 10], pieces: ['Escalator'], face: Math.PI, kind: 'step' },
      'L': { size: [3, 3], pieces: ['Landmark_ElevatorShaft'], face: -Math.PI / 2, kind: 'wall', elevator: LIFT },
      'J': { size: [3, 3], pieces: ['Landmark_ElevatorShaft'], face: Math.PI / 2, kind: 'wall', elevator: LIFT },
      'F': { size: [4, 4], pieces: ['Landmark_Fountain'], kind: 'cover' },
      'Q': { size: [4, 4], pieces: ['Landmark_GuestDesk'], kind: 'cover' },
      'O': { size: [2, 2], pieces: ['BigPlanter'], kind: 'cover' },
      'o': { pieces: ['Planter', 'Planter_B'], rotate: 'random90', kind: 'cover' },
      'B': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      'c': { pieces: ['Bin'], rotate: 'random90', kind: 'cover' },
      'd': { pieces: ['AdPillar'], rotate: 'random90', kind: 'cover' },
      'K': { size: [3, 2], pieces: ['Kiosk_A', 'Kiosk_B', 'Kiosk_C'], sequence: true, flip: true, kind: 'cover' },
      'T': { size: [2, 2], pieces: ['FoodTable', 'FoodTable_B'], kind: 'cover' },
      'D': { size: [2, 1], pieces: ['Display'], flip: true, kind: 'cover' },
      'Y': { size: [4, 2], pieces: ['Stall_Pizza', 'Stall_Noodle', 'Stall_Burger'], sequence: true, orient: 'wall', kind: 'cover' },
      'I': { pieces: ['Column_Lo'], kind: 'cover' },
      // walk-in shop rooms [5 x 6] (ground storey on the plan, upper storey on the mezzanine layer): front toward the doorways
      'A': room('A'), 'Z': room('Z'), 'C': room('C'), 'R': room('R'), 'W': room('W'), 'U': room('U'),
      'g': room('g'), 'v': room('v'), 'b': room('b'), 'm': room('m'), 't': room('t'),
      // mezzanine
      'u': { deck: { thick: 0.4, color: '#E9DCC4', edge: '#2E9E95', under: '#F6F0E6', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'ri', post: 'RailPost', kind: 'wall' },
      'i': { pieces: ['Column_Hi'], kind: 'cover' },
      'l': { pieces: ['UnderLight'], collide: false },
      // floor inlays (layer 0)
      'x': { pieces: ['Inlay_A'], collide: false },
      'y': { pieces: ['Inlay_B'], collide: false },
      '=': { pieces: ['Inlay_Band'], rotate: 'run', collide: false },
      '+': { pieces: ['Inlay_Knot'], collide: false },
      'M': { size: [8, 8], pieces: ['Inlay_Rose'], collide: false },
      'k': { pieces: ['Inlay_ChkA', 'Inlay_ChkB'], alternate: true, collide: false },
      'w': { size: [3, 2], pieces: ['Mat'], collide: false },
      // roof (layer 9.5): pieces hang from the ceiling plane
      '~': { size: [4, 4], pieces: ['Skylight', 'SkylightLamp', 'Skylight', 'Skylight'], sequence: true, collide: false },
      '&': { size: [4, 4], pieces: ['SkyTruss'], collide: false },
      '%': { size: [4, 4], pieces: ['SkyTrussBanA'], collide: false },
      '$': { size: [4, 4], pieces: ['SkyTrussBanB'], collide: false },
      ':': { pieces: ['CeilLight'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 9.5, variants: ['TrailWall_Ad'] },
    hatch: 'Hatch', stand: 'Planter',
    backdrop: null,
    budget: { prop: 3200, landmark: 4000, total: 90000 },   // total: + eleven walk-in shop rooms and their open fronts
    allPieces: function () { return WALLS.concat(OTHER, ROOMS); },
    levels: {
      mall: {
        name: 'Galleria Mall',
        intro: 'Robots have taken both floors. The escalators and the glass lift go up to the mezzanine.',
        zones: [
          // Grand Atrium: fountain court; Gunners hold the mezzanine rails from the second wave
          { map: 'mall_1', waves: [[['crawler', 19], ['gunner', 4]], [['crawler', 4], ['bomber', 4], ['gunner', 4], ['blader', 5]], [['crawler', 4], ['drone', 4], ['gunner', 3], ['soldier', 5]], [['crawler', 4], ['bomber', 4], ['gunner', 4], ['soldier', 5]]] },
          // Food Court: tables for cover, food stalls under the east mezzanine, Drones over the atrium
          { map: 'mall_2', waves: [[['crawler', 19], ['gunner', 4], ['drone', 3]], [['crawler', 5], ['bomber', 5], ['gunner', 4], ['blader', 5]], [['crawler', 5], ['drone', 5], ['gunner', 4], ['soldier', 5]], [['crawler', 4], ['bomber', 4], ['gunner', 4], ['blader', 5]]] },
          // Department Store: displays, the lift on the east side, a heavy last wave
          { map: 'mall_3', waves: [[['crawler', 19], ['gunner', 7]], [['crawler', 5], ['bomber', 5], ['drone', 4], ['soldier', 6]], [['crawler', 7], ['gunner', 7], ['drone', 4], ['blader', 5]], [['crawler', 7], ['gunner', 7], ['bomber', 7], ['drone', 3], ['soldier', 10]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
