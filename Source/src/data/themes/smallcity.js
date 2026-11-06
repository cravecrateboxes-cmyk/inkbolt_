/* Theme: Small City (kit-smallcity). Campaign level 2: a warm late-afternoon downtown of 2-4 storey brick and
   cream-stone buildings with painted shop fronts and striped awnings, concrete sidewalks, grey-blue asphalt with lane
   paint and zebra crossings, parked cars, a city bus, iron lamp posts, street trees, a clock tower and a fountain.

   ASCII legend (1 cell = 1 m; built-ins: # building, S spawn can, P entry, E entry gate, G exit gate, a ammo, h health):
     .  asphalt (the floor colour)          ,  sidewalk paving        ;  plaza paving (cream stone)
     -  white lane paint along X            |  white lane paint along Z
     ~  double yellow line along X          !  double yellow line along Z
     z  zebra bars along X (crossing an E-W street)    Z  zebra bars along Z (crossing a N-S street)
     o  manhole cover    i  iron lamp post on sidewalk paving    I  the same on plaza paving    t  street tree in an iron grate
     m  sidewalk furniture: newspaper box, mailbox, hydrant, litter bin (on paving)
     c  street junk cover: fruit crates, trash bags, boxes  =  red/white water barriers   j  concrete jersey barrier
     +  planter box with shrubs (on paving)                 b  park bench 2x1 (on plaza paving)
     C  parked car 2x4                      V  delivery van 2x5        B  city bus 3x9
     k  bus shelter 2x4 (on paving)         n  food cart 2x2 (on paving)
     T  clock tower 4x4 (landmark)          F  fountain 6x6 (landmark)
     ]  building facade facing east         [  building facade facing west   (use these, not '#', on east / west faces)
   Buildings ('#') are 2-4 storeys: the chooser cuts every facade run into buildings 4-7 m wide, each with its own
   brick, shop colour and height; pilasters mark building boundaries on the taller side, corners wrap the taller.
   Any '#' cell whose only open sides are east or west must be ']' / '[' (tests/unit/theme_smallcity.test.js checks). */
(function (IB) {
  'use strict';
  // must mirror STYLES in blender/fam_kit_smallcity.py: [material, storeys]
  var STY = [['R', 3], ['O', 2], ['T', 3], ['R', 4], ['C', 3], ['O', 3], ['T', 2], ['C', 4]];
  var NSTY = STY.length;
  var WIDTHS = [5, 6, 4, 7, 5, 4, 6], WSUM = 37;
  var CARS = ['Car_Taxi', 'Car_Red', 'Car_Blue', 'Car_Mint', 'Car_Cream'];
  var FURNITURE = ['NewsBoxes', 'Mailbox', 'Hydrant', 'Bin'], JUNK = ['Crates', 'TrashBags', 'Boxes'];

  // The kit bakes a 2 cm outline shell (blender CFG). IB.Assets.BAKED (src/game/assets.js) only lists the original
  // families, and without an entry the shader adds its full distance outline on top of the baked one. Until the engine
  // lists kit-smallcity (or defaults kit-* families to 0.02), fill the entry in before the game boots (scripts run while
  // the document is still loading, so this listener runs ahead of game.js's boot listener).
  if (typeof document !== 'undefined' && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      if (IB.Assets && IB.Assets.BAKED && IB.Assets.BAKED['kit-smallcity'] === undefined) IB.Assets.BAKED['kit-smallcity'] = 0.02;
    });
  }

  // building segment for a north/south facade cell: pos along the run (column), line = row
  function segment(pos, line, hash) {
    var p = pos + Math.floor(hash(line * 7 + 3, 11) * WSUM), cyc = Math.floor(p / WSUM), q = p - cyc * WSUM, k = 0;
    while (q >= WIDTHS[k]) { q -= WIDTHS[k]; k++; }
    return { b: cyc * WIDTHS.length + k, i: q, w: WIDTHS[k] };
  }
  // neighbouring buildings never share a style (steps of 3-4 around the style ring)
  function styleOf(b, line, hash) { var s = (Math.floor(hash(line * 5 + 1, 17) * NSTY) + b * 3 + Math.floor(hash(b + 50, line + 99) * 2)) % NSTY; return s < 0 ? s + NSTY : s; }
  function moduleFor(st, n, i, w, nPrev, nNext, door) {
    if ((i === 0 && n >= nPrev) || (i === w - 1 && n > nNext)) return 'Pilaster_' + STY[st][0] + n;   // boundary: taller side
    if (i === door) return 'WallDoor_' + st;
    return (Math.abs(i - door) % 2 === 1 ? 'WallWin_' : 'WallPier_') + st;
  }

  /* East / west facades. The engine turns '#' modules only by 0 or 180 degrees (every cell of a thick block's side
     face counts as a corner), so facades that face east or west are separate symbols ']' (faces east) and '['
     (faces west) placed with a fixed rotation. Their modules come from one long building sequence indexed by
     (column + row) % length ('alternate'), so walking down a run reads building after building. */
  var SEQ_W = [5, 6, 4, 7, 5, 4, 6, 5, 7, 4, 6, 5], SEQ = [], SEQN = [];
  (function () {
    var st = [], s = 2, L = SEQ_W.length;
    SEQ_W.forEach(function (w, b) { st.push(s); s = (s + 3 + (b % 3 === 1 ? 1 : 0)) % NSTY; });
    SEQ_W.forEach(function (w, b) {
      var n = STY[st[b]][1], nPrev = STY[st[(b + L - 1) % L]][1], nNext = STY[st[(b + 1) % L]][1], door = 1 + ((b * 5 + 2) % (w - 2));
      for (var i = 0; i < w; i++) { SEQ.push(moduleFor(st[b], n, i, w, nPrev, nNext, door)); SEQN.push(st[b]); }
    });
  })();
  var SIDE = '[]';
  function solidAt(grid, c, r) { return '#GE[]'.indexOf(grid.at(c, r)) >= 0; }

  function chooseWall(c, r, horiz, corner, hash, grid) {
    var oN = !solidAt(grid, c, r - 1), oS = !solidAt(grid, c, r + 1), oE = !solidAt(grid, c + 1, r), oW = !solidAt(grid, c - 1, r);
    var ns = oN || oS, ew = oE || oW;
    if (!ns && !ew) {
      var diag = !solidAt(grid, c - 1, r - 1) || !solidAt(grid, c + 1, r - 1) || !solidAt(grid, c - 1, r + 1) || !solidAt(grid, c + 1, r + 1);
      if (!diag) return 'Fill';   // only touches a '[' / ']' facade cell: hidden behind it
    }
    if (!ns || ew) {
      // corner: belongs to the taller of the facades that meet here
      var best = STY[styleOf(segment(c, r, hash).b, r, hash)];
      [[c, r - 1], [c, r + 1]].forEach(function (q) {
        if (SIDE.indexOf(grid.at(q[0], q[1])) >= 0) { var o = STY[SEQN[(q[0] + q[1]) % SEQ.length]]; if (o[1] > best[1]) best = o; }
      });
      return 'Corner_' + best[0] + best[1];
    }
    var g = segment(c, r, hash), s = styleOf(g.b, r, hash), n = STY[s][1], dr = oN ? -1 : 1;
    // beside an inner corner (an east/west facade diagonally across the street cell): plain brick, nothing proud
    if (SIDE.indexOf(grid.at(c - 1, r + dr)) >= 0 || SIDE.indexOf(grid.at(c + 1, r + dr)) >= 0) return 'Blank_' + STY[s][0] + n;
    // next to a gate: a pilaster (an awning would poke out of the gate pier)
    if ('GE'.indexOf(grid.at(c - 1, r)) >= 0 || 'GE'.indexOf(grid.at(c + 1, r)) >= 0) return 'Pilaster_' + STY[s][0] + n;
    var nPrev = STY[styleOf(g.b - 1, r, hash)][1], nNext = STY[styleOf(g.b + 1, r, hash)][1];
    return moduleFor(s, n, g.i, g.w, nPrev, nNext, 1 + Math.floor(hash(g.b + 7, r) * (g.w - 2)));
  }

  function allWalls() {
    var out = ['Fill'], seen = {};
    for (var s = 0; s < NSTY; s++) out.push('WallWin_' + s, 'WallDoor_' + s, 'WallPier_' + s);
    STY.forEach(function (t) { var k = t[0] + t[1]; if (!seen[k]) { seen[k] = 1; out.push('Pilaster_' + k, 'Corner_' + k, 'Blank_' + k); } });
    return out;
  }

  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }

  IB.registerTheme({
    id: 'smallcity', name: 'Small City', family: 'kit-smallcity', prefix: 'KIT_SMALLCITY_',
    palette: ['#C9614A', '#3E9B95', '#D7A93C', '#8C95A2'],
    env: { sky: ['#86BDE6', '#FFE0B8'], fog: { color: '#F2D9BF', near: 55, far: 150 }, sun: [-0.55, 0.62, 0.42], clouds: true, ceiling: null },
    floor: { color: '#8C95A2', trail: '#C9C3B6', outside: '#9AA2AD' },
    wall: { height: 7, roof: '#8E9097', faceOpen: true, choose: chooseWall },
    symbols: {
      ',': { pieces: ['Walk', 'WalkB'], alternate: true, collide: false },
      ';': { pieces: ['Plaza', 'PlazaB'], alternate: true, collide: false },
      '-': flat(['LaneW'], 0), '|': flat(['LaneW'], Math.PI / 2),
      '~': flat(['LaneY'], 0), '!': flat(['LaneY'], Math.PI / 2),
      'z': flat(['Zebra'], 0), 'Z': flat(['Zebra'], Math.PI / 2),
      'o': flat(['Manhole']),
      ']': { pieces: SEQ, alternate: true, rotate: Math.PI / 2, h: 7, kind: 'wall' },
      '[': { pieces: SEQ, alternate: true, rotate: -Math.PI / 2, h: 7, kind: 'wall' },
      // street furniture (collision from the pieces' _COL boxes)
      'i': { pieces: ['Lamp'], kind: 'prop' },
      'I': { pieces: ['LampP'], kind: 'prop' },
      't': { pieces: ['StreetTree'], rotate: 'random90', kind: 'prop' },
      'm': { pieces: FURNITURE, rotate: 'random90', kind: 'cover' },
      'c': { pieces: JUNK, rotate: 'random90', kind: 'cover' },
      '=': { pieces: ['BarrierR', 'BarrierW'], rotate: 'run', alternate: true, kind: 'cover' },
      'j': { pieces: ['Jersey'], rotate: 'run', kind: 'cover' },
      '+': { pieces: ['Planter'], rotate: 'run', kind: 'cover' },
      'b': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      // vehicles and big pieces
      'C': { size: [2, 4], pieces: CARS, flip: true, kind: 'cover' },
      'V': { size: [2, 5], pieces: ['Van'], flip: true, kind: 'cover' },
      'B': { size: [3, 9], pieces: ['Bus'], flip: true, kind: 'cover' },
      'k': { size: [2, 4], pieces: ['Shelter'], kind: 'cover' },
      'n': { size: [2, 2], pieces: ['Cart'], kind: 'cover' },
      'T': { size: [4, 4], pieces: ['Landmark_ClockTower'], kind: 'wall' },
      'F': { size: [6, 6], pieces: ['Landmark_Fountain'], kind: 'wall' }   // not cover: the basin inside is unreachable
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 2.64 },
    hatch: 'Hatch', stand: 'Crates',
    // a skyline of taller brick / stone towers, a steeple and rooftop water tanks beyond the zone walls
    backdrop: { ring: [
      { piece: 'Backdrop_Row', count: 14, radius: [16, 26], scale: [0.9, 1.2], face: true, squeezeX: 0.75 },
      { piece: 'Backdrop_Tower', count: 9, radius: [30, 42], scale: [0.9, 1.3], face: true, squeezeX: 0.8 },
      { piece: 'Backdrop_Office', count: 5, radius: [48, 60], scale: [1.0, 1.3], face: true, squeezeX: 0.85 },
      { piece: 'Backdrop_Church', count: 2, radius: [36, 40], scale: [1.0, 1.1], face: true, squeezeX: 0.8 }
    ] },
    budget: { prop: 1200, landmark: 4000, total: 60000 },
    allPieces: function () {
      return allWalls().concat(['Walk', 'WalkB', 'Plaza', 'PlazaB', 'LaneW', 'LaneY', 'Zebra', 'Manhole', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch',
        'Lamp', 'LampP', 'StreetTree', 'BarrierR', 'BarrierW', 'Jersey', 'Planter', 'Bench', 'Van', 'Bus', 'Shelter', 'Cart',
        'Landmark_ClockTower', 'Landmark_Fountain', 'Backdrop_Row', 'Backdrop_Tower', 'Backdrop_Office', 'Backdrop_Church'], FURNITURE, JUNK, CARS);
    },
    levels: {
      smallcity: {
        name: 'Small City', intro: 'Downtown is overrun. Use the parked cars for cover.',
        zones: [
          // Main Street: crawler packs down the avenue, then gunners behind the parked cars
          { map: 'smallcity_1', waves: [[['crawler', 7]], [['crawler', 5], ['gunner', 2]], [['crawler', 5], ['gunner', 3]], [['crawler', 3], ['gunner', 1]]] },
          // Clock Square: gunners hold the ring road, the first bombers roll across the square, a drone over the tower
          { map: 'smallcity_2', waves: [[['crawler', 7], ['gunner', 2]], [['crawler', 5], ['bomber', 2], ['drone', 1]], [['gunner', 3], ['crawler', 4]], [['bomber', 2], ['crawler', 4]]] },
          // Market Lot: rows of cars for the gunners, bombers in the aisles, two drones over the lot
          { map: 'smallcity_3', waves: [[['crawler', 7], ['gunner', 2]], [['crawler', 5], ['bomber', 3]], [['gunner', 3], ['drone', 2], ['crawler', 3]], [['crawler', 5], ['bomber', 2], ['gunner', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
