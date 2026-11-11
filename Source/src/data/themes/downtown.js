/* Theme: Downtown Standoff (kit-downtown) -- a wide downtown district at midday, braced for a battle. Not Small City's
   two-storey main street nor Downtown at Dusk's brownstones under neon: five to eight storey commercial blocks in
   limestone, tan brick, glass curtain wall, teal terracotta deco and 60s concrete over street-level shops, a clear
   blue sky. The street is full of vehicles (parked, crashed and abandoned: sedans, hatchbacks, SUVs, taxis, police
   cruisers, pickups, vans, box trucks, a city bus, motorbikes, scooters, bikes at racks) and staged for a fight:
   jersey barriers, sandbag walls and nests, czech hedgehogs, wire, police tape, a checkpoint, an overturned truck
   across the avenue, burnt-out wrecks, sniper nests on low balconies, taped and boarded windows.
   Ten walk-in shops (two to four per zone) open off the sidewalks: furnished 7 x 8 m rooms with a counter, shelving
   and a back room behind a staff door, that the player and the robots fight through.
   Built by blender/fam_kit_downtown.py (downtown_*.py); zone layouts by tools/downtown_zones.py.
   The everyday vehicles and some street props are kit-parking pieces (theme option `families` loads that kit too;
   they are named in full, KIT_PARKING_*), repainted per car from the parking palette (paint jobs, CAR).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] cells; built-ins # P S a h G E):
     #  building (the zone edge and the shop bands; facades face the open side)   n  shop doorway (wall.passage)
     ,  sidewalk    ;  plaza paving    -  |  lane dash along X / Z    ~  !  double yellow along X / Z
     z  Z  zebra bars along X / Z    _  :  stop line along X / Z    o  manhole    x  scorch mark    *  rubble and brass
     =  tram rails (along Z)                                           (all of these: no collision)
     i  l  e  w  street lamp, arm over the road to the S / N / E / W   1 2 3 4  traffic signal, mast arm S / N / E / W
     t  street tree in a grate   f  hydrant   m  mailbox / news boxes / litter basket / parking meters   b  bench [2,1]
     u  U  bus shelter [4,2], open to the E / W    k  newsstand [2,3], front to the E (block 3 x 2)
     Y  I  market stall [3,2], front to the E / W (blocks 2 x 3)
     C  parked / abandoned car [3,5]  H  car with its hazard lights blinking [3,5]  W  wreck [3,5] (burnt, smashed)
     A  taxi [3,5]  Q  police cruiser [3,5]  T  pickup / van [3,6]  X  box truck [3,8]  B  city bus [3,12]
     O  box truck on its side, a roadblock [4,8]   v  motorbike / scooter [1,2]   K  bike rack [2,4]
     s  sandbag wall (runs)   N  sandbag nest [3,3] (gun to the S)   g  czech hedgehog   r  barbed wire (runs, no collision)
     p  police tape (runs, no collision)   c  ammo crates [2,1]   F  burn barrel   d  rubble heap   j  jersey barrier [2,1]
     q  cones   D  drums   L  pallets [2,2]   y  wheelie bins [2,1]
     R  police checkpoint [6,4] (zone 1 landmark)   M  Founders monument [8,8] (zone 2)   V  stalled tram [3,14] (zone 3)
   Walk-in shops [7, 8] (a room symbol fills the room's cells; the room's front turns to its doorway line, orient 'open'):
     5 Hollis Pharmacy   6 Lula's Diner   7 Voltaic Electronics   8 Corner Mart 24   9 Inkwell Books
     0 Sal's Barber Shop   & Fieldhouse Sports   $ Kessler Hardware   % Lucky 7 Pawn   @ Bubbles Laundromat
   A shop sits in a band of building cells behind a facade line: two window cells, three doorway cells 'n', two window
   cells. The facade modules there are ShopWin / ShopOpen of the building's style; the room piece draws the sign, the
   awning and the inside. Pickups inside shops lie in an "@layer 0" grid (the plan cell holds the room symbol).

   The wall uses facing 'open'. The chooser cuts every facade run into buildings: each shop frontage is a building of
   its own, the runs between them are split into buildings 3-7 m wide, each with a style (STY) and height; pilasters
   frame the shops and mark boundaries on the taller side, corner piers wrap where facades meet, a lobby door in each
   building, closed shops with half-down shutters, plywood boards and sniper-nest balconies on some styles. */
(function (IB) {
  'use strict';
  // must mirror STYLES in blender/downtown_facades.py: [material, storeys]
  var STY = [['L', 5], ['T', 6], ['G', 8], ['D', 7], ['C', 5]];
  var NSTY = STY.length, NEST = 'LTC', BOARD = 'LTC';
  var WIDTHS = [5, 6, 4, 7, 5, 3, 6];
  var ROOM = { '5': 'Shop_Pharmacy', '6': 'Shop_Diner', '7': 'Shop_Electronics', '8': 'Shop_Mart', '9': 'Shop_Books',
    '0': 'Shop_Barber', '&': 'Shop_Sports', '$': 'Shop_Hardware', '%': 'Shop_Pawn', '@': 'Shop_Laundry' };
  var ROOMS = Object.keys(ROOM).join('');
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  function isRoom(ch) { return ROOMS.indexOf(ch) >= 0; }
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E' || ch === 'n'; }
  function open(ch) { return !wallish(ch) && !isRoom(ch); }
  var DIR = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var OPP = { S: 'N', N: 'S', E: 'W', W: 'E' };

  // a shop front is open on both sides (the street and its own room): it faces the street
  function faceOf(c, r, grid) {
    for (var f in DIR) {
      var d = DIR[f];
      if (isRoom(grid.at(c + d[0], r + d[1])) && open(grid.at(c - d[0], r - d[1]))) return OPP[f];
    }
    return null;
  }

  /* Buildings along one facade line (cached per grid): the cells of a straight run with the same open side, shop
     frontages (the cell behind is a room) as buildings of their own, the rest split by WIDTHS; neighbours never share
     a style. Returns pos -> { i, w, s, prev, next, shop }. */
  function lineOf(grid, c, r, face) {
    var cache = grid._dtLines || (grid._dtLines = {});
    var ns = face === 'S' || face === 'N', d = DIR[face], key = face + (ns ? r : c);
    if (!cache[key]) {
      var len = ns ? grid.w : grid.h, cells = [];
      for (var p = 0; p < len; p++) {
        var cc = ns ? p : c, rr = ns ? r : p, ch = grid.at(cc, rr);
        var on = (ch === '#' || ch === 'n') && open(grid.at(cc + d[0], rr + d[1]));
        cells.push(on ? (isRoom(grid.at(cc - d[0], rr - d[1])) ? grid.at(cc - d[0], rr - d[1]) : '.') : null);
      }
      var B = [], k = 0;
      while (k < len) {
        if (cells[k] === null) { k++; continue; }
        var k1 = k; while (k1 + 1 < len && cells[k1 + 1] !== null) k1++;
        // split the run [k, k1]: shop spans, then the gaps by WIDTHS
        var q = k;
        while (q <= k1) {
          if (cells[q] !== '.') { var q1 = q; while (q1 + 1 <= k1 && cells[q1 + 1] === cells[q]) q1++; B.push({ a: q, b: q1, shop: true }); q = q1 + 1; continue; }
          var g1 = q; while (g1 + 1 <= k1 && cells[g1 + 1] === '.') g1++;
          var wi = Math.floor(hh(q * 7 + 3, (ns ? r : c) + 11) * WIDTHS.length), x = q;
          while (x <= g1) {
            var w = WIDTHS[wi++ % WIDTHS.length];
            if (g1 - (x + w - 1) < 3) w = g1 - x + 1;   // no building narrower than 3 at the end of a gap
            B.push({ a: x, b: Math.min(g1, x + w - 1), shop: false }); x += w;
          }
          q = g1 + 1;
        }
        k = k1 + 1;
      }
      var line = ns ? r : c + 997, map = {};
      B.forEach(function (b, bi) {
        var s = Math.floor(hh(bi * 5 + 1, line) * NSTY);
        if (bi > 0 && s === B[bi - 1].s) s = (s + 1 + Math.floor(hh(bi, line + 3) * (NSTY - 1))) % NSTY;
        b.s = s;
      });
      B.forEach(function (b, bi) {
        for (var p2 = b.a; p2 <= b.b; p2++) map[p2] = { i: p2 - b.a, w: b.b - b.a + 1, s: b.s, shop: b.shop, prev: B[bi - 1] || null, next: B[bi + 1] || null, a: b.a };
      });
      cache[key] = map;
    }
    return cache[key][ns ? c : r] || null;
  }
  function height(s) { return STY[s][1]; }
  function faceAt(grid, c, r) {
    var ch = grid.at(c, r); if (ch !== '#' && ch !== 'n') return null;
    var f0 = faceOf(c, r, grid); if (f0) return f0;
    var hit = []; for (var f in DIR) if (open(grid.at(c + DIR[f][0], r + DIR[f][1]))) hit.push(f);
    return hit.length === 1 ? hit[0] : null;
  }
  // a corner pier takes the taller of the facades meeting at it
  function cornerStyle(grid, c, r) {
    var best = -1;
    [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(function (d) {
      var f = faceAt(grid, c + d[0], r + d[1]); if (!f) return;
      var b = lineOf(grid, c + d[0], r + d[1], f); if (b && (best < 0 || height(b.s) > height(best))) best = b.s;
    });
    return best < 0 ? 0 : best;
  }

  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none' || !DIR[face]) return 'Corner_' + cornerStyle(grid, c, r);
    var d = DIR[face];
    if (isRoom(grid.at(c + d[0], r + d[1]))) return null;   // a shop room's own walls: drawn by the room piece
    var b = lineOf(grid, c, r, face);
    if (!b) return 'Corner_' + cornerStyle(grid, c, r);
    var s = b.s, ns = face === 'S' || face === 'N', dc = ns ? 1 : 0, dr = ns ? 0 : 1;
    if (b.shop) return (b.i >= 2 && b.i <= 4 ? 'ShopOpen_' : 'ShopWin_') + s;
    for (var k = -2; k <= 2; k++) { var q = grid.at(c + k * dc, r + k * dr); if (q === 'G' || q === 'E') return 'Pilaster_' + s; }
    var fc = c + d[0], fr = r + d[1];
    if (wallish(grid.at(fc - dc, fr - dr)) || wallish(grid.at(fc + dc, fr + dr))) return 'Blank_' + s;   // inner corner
    if (b.w <= 1) return 'Pilaster_' + (b.prev && b.next ? (height(b.prev.s) >= height(b.next.s) ? b.prev.s : b.next.s) : s);
    var P = b.prev, N = b.next;
    if (b.i === 0 && P && (P.shop || height(s) >= height(P.s))) return 'Pilaster_' + s;
    if (b.i === b.w - 1 && N && (N.shop || height(s) > height(N.s))) return 'Pilaster_' + s;
    var line = ns ? r : c + 997, door = 1 + Math.floor(hh(b.a + 7, line) * Math.max(1, b.w - 2));
    if (b.i === door) return 'Lobby_' + s;
    if (Math.abs(b.i - door) % 3 === 0) return 'Pier_' + s;
    var mat = STY[s][0], h = hh(c * 3 + 1, r * 7 + 2);
    if (NEST.indexOf(mat) >= 0 && h < 0.1) return 'Nest_' + s;
    if (BOARD.indexOf(mat) >= 0 && h > 0.68) return 'Board_' + s;
    return 'Win_' + s;
  }

  function wallPieces() {
    var out = [];
    STY.forEach(function (t, s) {
      ['Win', 'Lobby', 'Pier', 'ShopWin', 'ShopOpen', 'Pilaster', 'Corner', 'Blank'].forEach(function (k) { out.push(k + '_' + s); });
      if (NEST.indexOf(t[0]) >= 0) out.push('Nest_' + s);
      if (BOARD.indexOf(t[0]) >= 0) out.push('Board_' + s);
    });
    return out;
  }

  // kit-parking pieces, named in full (the theme loads that family too); paint jobs from the parking palette
  var KP = 'KIT_PARKING_';
  function kp(list) { return list.map(function (n) { return KP + n; }); }
  var PAINT = 48;   // parking_base.py: 'paint' cell; 49 blue 50 yellow 51 green 52 white 53 black 54 silver 55 orange 56 teal 57 purple 58 mint 59 brown
  var CAR = { from: [PAINT], to: [[48], [49], [51], [52], [53], [54], [55], [56], [57], [58], [59], [52], [54], [53], [49]] };
  var TAXI = { from: [PAINT], to: [[50]] }, POLICE = { from: [PAINT], to: [[52]] };
  var CARS = kp(['Sedan', 'Sedan', 'Sedan_Door', 'Hatchback', 'Hatchback', 'Hatch_Boot', 'SUV', 'SUV', 'SUV_Boot', 'Sports', 'Sedan', 'Wreck_Smash']);
  var R90 = Math.PI / 2;
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }
  function shop(ch) { return { size: [7, 8], pieces: [ROOM[ch]], orient: 'open', kind: 'cover' }; }
  var withTaxi = {}, withPolice = {};
  withTaxi[KP + 'Sedan'] = ['TaxiTop']; withPolice[KP + 'Sedan'] = ['PoliceKit'];

  /* the hazard lights of the 'H' cars: kit-parking's HazardGlow overlay placed on each car, blinked by the theme */
  function buildOverlays(level, api) {
    var A = IB.Assets, list = [];
    level.zones.forEach(function (Z) {
      var g = Z.grid;
      for (var r = 0; r < g.h; r++) for (var c = 0; c < g.w; c++) {
        if (g.rows[r][c] !== 'H' || (c > 0 && g.rows[r][c - 1] === 'H') || (r > 0 && g.rows[r - 1][c] === 'H')) continue;
        var m = new THREE.Matrix4().makeTranslation(Z.ox + c + 1.5, 0, Z.oz + r + 2.5);   // 'H' blocks are 3 x 5 (face 0)
        list.push(A.placed(KP + 'HazardGlow', m));
      }
    });
    if (!list.length || !A.mat['kit-parking']) return;
    var mesh = new THREE.Mesh(A.merge(list), A.mat['kit-parking']);
    level.root.add(mesh);
    api.tick(function (dt, t) { mesh.visible = (t % 0.9) < 0.45; });
  }

  var SYMBOLS = {
    ',': flat(['Walk', 'WalkB'], 0, true),
    ';': flat(['Plaza', 'PlazaB'], 0, true),
    '-': flat(['LaneW'], 0), '|': flat(['LaneW'], R90),
    '~': flat(['LaneY'], 0), '!': flat(['LaneY'], R90),
    'z': flat(['Zebra'], 0), 'Z': flat(['Zebra'], R90),
    '_': flat(['StopLine'], 0), ':': flat(['StopLine'], R90),
    'o': flat(['Manhole']),
    'x': { pieces: ['Scorch'], rotate: 'random90', collide: false },
    '*': { pieces: ['Rubble'], rotate: 'random90', collide: false },
    '=': flat(['Rails'], 0),
    // street furniture
    'i': { pieces: ['Lamp'], rotate: 0, kind: 'prop' }, 'l': { pieces: ['Lamp'], rotate: Math.PI, kind: 'prop' },
    'e': { pieces: ['Lamp'], rotate: R90, kind: 'prop' }, 'w': { pieces: ['Lamp'], rotate: -R90, kind: 'prop' },
    '1': { pieces: ['Signal'], rotate: 0, kind: 'prop' }, '2': { pieces: ['Signal'], rotate: Math.PI, kind: 'prop' },
    '3': { pieces: ['Signal'], rotate: R90, kind: 'prop' }, '4': { pieces: ['Signal'], rotate: -R90, kind: 'prop' },
    't': { pieces: ['Tree'], rotate: 'random90', kind: 'prop' },
    'f': { pieces: ['Hydrant'], rotate: 'random90', kind: 'cover' },
    'm': { pieces: ['Mailbox', 'NewsBoxes', 'Basket', 'Meters'], rotate: 'random90', kind: 'cover' },
    'b': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
    'u': { size: [4, 2], pieces: ['BusStop'], face: R90, kind: 'cover' },
    'U': { size: [4, 2], pieces: ['BusStop'], face: -R90, kind: 'cover' },
    'k': { size: [2, 3], pieces: ['Newsstand'], face: R90, kind: 'cover' },
    'Y': { size: [3, 2], pieces: ['Stall_Fruit', 'Stall_Flowers'], sequence: true, face: R90, kind: 'cover' },
    'I': { size: [3, 2], pieces: ['Stall_Flowers', 'Stall_Fruit'], sequence: true, face: -R90, kind: 'cover' },
    // vehicles (kit-parking unless named here)
    'C': { size: [3, 5], pieces: CARS, flip: true, kind: 'cover', paint: CAR },
    'H': { size: [3, 5], pieces: kp(['Hatch_Hazard']), face: 0, kind: 'cover', paint: CAR },
    'W': { size: [3, 5], pieces: kp(['Wreck_Burnt', 'Wreck_Burnt_B', 'Wreck_Smash', 'Wreck_Burnt']), flip: true, kind: 'cover', paint: CAR },
    'A': { size: [3, 5], pieces: kp(['Sedan']), with: withTaxi, flip: true, kind: 'cover', paint: TAXI },
    'Q': { size: [3, 5], pieces: kp(['Sedan']), with: withPolice, flip: true, kind: 'cover', paint: POLICE },
    'T': { size: [3, 6], pieces: kp(['Pickup', 'Van', 'Pickup_B', 'Van_Door']), flip: true, kind: 'cover', paint: CAR },
    'X': { size: [3, 8], pieces: kp(['BoxTruck']), flip: true, kind: 'cover', paint: CAR },
    'B': { size: [3, 12], pieces: ['Bus'], flip: true, kind: 'cover' },
    'O': { size: [4, 8], pieces: ['TruckOver'], flip: true, kind: 'cover' },
    'v': { size: [1, 2], pieces: kp(['Motorbike', 'Scooter']), flip: true, kind: 'cover', paint: CAR },
    'K': { size: [2, 4], pieces: kp(['BikeRack']), flip: true, kind: 'cover', paint: CAR },
    // battle staging
    's': { pieces: ['Sandbags'], rotate: 'run', kind: 'cover' },
    'N': { size: [3, 3], pieces: ['Nest'], face: 0, kind: 'cover' },
    'g': { pieces: ['Hedgehog'], rotate: 'random90', kind: 'cover' },
    'r': { pieces: ['Wire'], rotate: 'run', collide: false },
    'p': { pieces: ['Tape'], rotate: 'run', collide: false },
    'c': { size: [2, 1], pieces: ['Crates'], flip: true, kind: 'cover' },
    'F': { pieces: ['BurnBarrel'], kind: 'cover' },
    'd': { pieces: ['RubbleHeap'], rotate: 'random90', kind: 'cover' },
    'j': { size: [2, 1], pieces: kp(['Jersey_C', 'Jersey_P']), flip: true, kind: 'cover' },
    'q': { pieces: kp(['Cone', 'Cones']), rotate: 'random90', kind: 'cover' },
    'D': { pieces: kp(['Drums']), rotate: 'random90', kind: 'cover' },
    'L': { size: [2, 2], pieces: kp(['Pallets']), flip: true, kind: 'cover' },
    'y': { size: [2, 1], pieces: kp(['Bins']), flip: true, kind: 'cover' },
    // landmarks
    'R': { size: [6, 4], pieces: ['Landmark_Checkpoint'], face: 0, kind: 'cover' },
    'M': { size: [8, 8], pieces: ['Landmark_Monument'], face: 0, kind: 'wall' },
    'V': { size: [3, 14], pieces: ['Landmark_Tram'], face: 0, kind: 'cover' }
  };
  Object.keys(ROOM).forEach(function (ch) { SYMBOLS[ch] = shop(ch); });

  IB.registerTheme({
    id: 'downtown', name: 'Downtown Standoff', family: 'kit-downtown', prefix: 'KIT_DOWNTOWN_', families: ['kit-parking'],
    palette: ['#C98455', '#63B5A8', '#E6DCC6', '#2B3A67'],
    // midday: a deep blue zenith to a pale horizon, light haze, the sun high in the south-west
    env: { sky: ['#4F9FE6', '#D9EDF9'], fog: { color: '#CFE0EC', near: 62, far: 175 }, sun: [-0.35, 0.86, 0.38], clouds: true, ceiling: null },
    floor: { color: '#5F626C', trail: '#6B6862', outside: '#55585F' },
    // shop doorways ('n'): open below the 3.4 m lintel
    wall: { height: 10, roof: '#6E6A74', facing: 'open', choose: chooseWall, faceOf: faceOf, passage: { ch: 'n', solid: [[3.4, 10]] } },
    symbols: SYMBOLS,
    // the gates are checkpoint buildings over the street; the passages between zones are 16 m brick alleys
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C'], height: 16 },
    hatch: 'Hatch', stand: 'Crates',
    backdrop: {
      ring: [
        { piece: 'Backdrop_Block', count: 14, radius: [22, 32], scale: [0.95, 1.2], face: true, squeezeX: 0.75 },
        { piece: 'Backdrop_Tower', count: 8, radius: [38, 50], scale: [0.9, 1.25], face: true, squeezeX: 0.8 },
        { piece: 'Backdrop_Spire', count: 2, radius: [52, 58], scale: [1.0, 1.1], face: true, squeezeX: 0.85 }
      ],
      build: buildOverlays
    },
    budget: { prop: 2600, landmark: 3000, total: 45000 },
    allPieces: function () {
      var out = wallPieces().concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Backdrop_Block',
        'Backdrop_Tower', 'Backdrop_Spire', 'TaxiTop', 'PoliceKit']);
      Object.keys(SYMBOLS).forEach(function (ch) { SYMBOLS[ch].pieces.forEach(function (n) { if (n.indexOf(KP) !== 0 && out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    // the kit-parking pieces this theme places (tests check they exist in fps-kit-parking.glb)
    parkingPieces: function () {
      var out = [KP + 'HazardGlow'];
      Object.keys(SYMBOLS).forEach(function (ch) { SYMBOLS[ch].pieces.forEach(function (n) { if (n.indexOf(KP) === 0 && out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    levels: {
      downtown: {
        name: 'Downtown Standoff',
        intro: 'The city held the line downtown and lost it. Fight up Commerce Avenue, across Liberty Square and down Market Street, through the shops if you have to.',
        zones: [
          // Commerce Avenue: the checkpoint and the overturned truck across the avenue, gunners behind the barriers
          { map: 'downtown_1', waves: [[['crawler', 22], ['gunner', 6]], [['crawler', 8], ['bomber', 2], ['gunner', 6], ['blader', 8]], [['crawler', 8], ['drone', 5], ['gunner', 5], ['soldier', 9]], [['crawler', 9], ['bomber', 2], ['gunner', 6], ['soldier', 10]]] },
          // Liberty Square: nests round the monument, drones over the open plaza, blade bots through the shops
          { map: 'downtown_2', waves: [[['crawler', 22], ['gunner', 6], ['drone', 3]], [['crawler', 10], ['bomber', 2], ['gunner', 6], ['blader', 10]], [['crawler', 8], ['drone', 6], ['gunner', 6], ['soldier', 8]], [['crawler', 8], ['bomber', 2], ['gunner', 6], ['blader', 8], ['soldier', 5]]] },
          // Market Street: the stalled tram, the stalls and the back lane, a heavy last wave
          { map: 'downtown_3', waves: [[['crawler', 23], ['gunner', 9]], [['crawler', 10], ['bomber', 2], ['drone', 6], ['soldier', 9]], [['crawler', 11], ['gunner', 9], ['drone', 5], ['blader', 10]], [['crawler', 10], ['gunner', 10], ['bomber', 2], ['drone', 5], ['soldier', 13], ['blader', 6]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
