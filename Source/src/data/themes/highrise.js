/* Theme: Zenith Command (kit-highrise) -- the headquarters of the Zenith Tactical Response Unit, on the top floors of a
   skyscraper 240 m above the street, and the roofs of the buildings packed round it. The final campaign level.
     highrise_1  Armory Deck: the secure lift lobby (bio-gates, front desk, the unit's star), the briefing theatre
                 (tiered seat rows, a video wall), the long armory hall (lit gun walls, glass gun cases, workbenches,
                 gear shelving, exo-suit stands) and the armoury vault behind its open round door (landmark)
     highrise_2  Operations Deck: the drone bay (drones on their charging cradles), the shooting simulator (booths,
                 holo targets, projection wall), the operations room round the holo table (landmark), the gear room
                 and the server room
     highrise_3  The Roof: out over a sky-bridge onto the roof next door, a block of roofs 3 - 5 m apart at heights
                 from -3 m to +3 m (zones.js decks), with HVAC units and their spinning fans, cooling towers, water
                 tanks, the lift machine room, an antenna mast, skylights, ducts and the window-cleaning gantry
                 (landmark). Robots throw wooden planks across the gaps to reach you (rooftops.js); a fall is a death.
   Armory odds (game.js placeLoot): rack guns mostly green and blue, about one or two purples over the level, orange
   0.3 %; bench mods and shelf gear tilted to rare with a little epic.

   Interior zones: three grids, the floor plan, "@layer 0.008" (floor finishes; on wall cells, wall-art codes) and
   "@layer 4.5" (ceiling fittings hanging from the 4.5 m ceiling).
   Floor plan:  R gun wall [3,1] (turns to face the room)  C lit gun case [2,2] (an island, guns both sides)  b workbench [2,1]
     g gear shelf [2,1] (turns)  H exo-suit stand  l smart locker  x hard cases / ammo crates  D ops console [4,1]
     K ops desk pair [4,2]  T theatre seat row [4,2] (faces north)  U lectern  p plant  B bench [2,1]
     o vending / water cooler  Q front desk [6,2]  t bio-gate (runs)  y simulator booth [3,2] (counter north)
     Y holo target  d drone cradle [2,2]  V vault door [6,2] (in a wall gap; landmark)  O holo table [4,4] (landmark)
     s server rack  I column  c coffee point [2,1]
   Floor layer: 1 lobby stone  8 lobby border  2 theatre carpet  3 armory rubber  4 simulator floor  5 ops floor
     7 entry mat  / hazard stripes  ^ firing line  - | cyan guide line (along X / Z)  0 unit star [4,4]
     Wall-art codes (on wall cells): u door  s sign  e unit logo  v video wall (runs)  m city map screen  k bio lock
   Ceiling layer: i light line  j downlight  = ! + beam (X / Z / crossing)  ~ ; duct (X / Z)  { } cable tray (X / Z)
     [ ] doorway lintel (wall along X / Z)

   The roof zone: the floor plan is the zone's own roof (y = 0) with its equipment, '_' open air, '%' a plank site,
   '$' a plank laid from the start (rooftops.js; never theme symbols, so nothing is built on those cells); "@layer <y>" grids hold the neighbouring roofs (decks 'n' grey
   membrane / 'Z' tan gravel, at their own height) with their own equipment, spawns and pickups; "@layer 0.008"
   walkway pavers ('6').
   Roof symbols: F HVAC unit [3,2] (spinning fan)  N cooling tower [4,4] (big fan)  J water tank [3,3]
     M lift machine room [6,4]  A antenna mast [2,2]  X window-cleaning gantry [4,6] (landmark)  L skylight [3,2]
     W solar array [4,2]  f exhaust vent  r duct (runs)  q plank stack  z roof hatch
   Roof edges are built by rooftops.js: parapets (1.1 m) everywhere but where planks land (a 0.3 m kerb with hazard
   paint, one cell either side). The '#' cells on the roof are the HQ tower's facade (south) and the stair penthouse
   with the exit door (north).
   The wall chooser styles each interior module from the floor finish in front of it (lobby, theatre, armory,
   simulator, ops), turns the art code on the cell into that style's piece and splits video-wall runs into
   left / middle / right parts; edge cells of the interior zones are the curtain wall (glass, a column every 6 m). */
(function (IB) {
  'use strict';
  var FSTYLE = { '1': 'L', '7': 'L', '8': 'L', '0': 'L', '2': 'B', '3': 'A', '/': 'A', '4': 'S', '^': 'S', '5': 'O', '-': 'O', '|': 'O' };
  var ART = {
    L: { u: 'WL_Door', s: 'WL_Sign', e: 'WL_Logo', v: 'WL_Screen', k: 'WL_Lock' },
    B: { u: 'WB_Door', v: 'WB_Screen', s: 'WB_Sign' },
    A: { u: 'WA_Door', s: 'WA_Sign', k: 'WA_Lock', e: 'WA_Logo' },
    S: { u: 'WS_Door', v: 'WS_Screen', s: 'WS_Sign' },
    O: { u: 'WO_Door', v: 'WO_Screen', m: 'WO_Map', s: 'WO_Sign' }
  };
  var RUNS = { WB_Screen: 1, WS_Screen: 1, WO_Screen: 1 };
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };
  var NB = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]];
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  function floorOf(grid) {
    if (grid._hrF === undefined) {
      grid._hrF = null;
      (grid.layers || []).forEach(function (l) { if (!grid._hrF && l.y < 0.5 && l.y > 0) grid._hrF = l; });
    }
    return grid._hrF;
  }
  function isRoof(grid) {
    if (grid._hrRoof === undefined) { grid._hrRoof = false; for (var r = 0; r < grid.h; r++) if (grid.rows[r].indexOf('_') >= 0) { grid._hrRoof = true; break; } }
    return grid._hrRoof;
  }
  function gateC(grid, r) {
    var cache = grid._hrGate || (grid._hrGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows[r] || '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  var WIN = ['Win_A', 'Win_A', 'Win_B', 'Win_A', 'Win_C', 'Win_A'];
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var W = grid.w, Hh = grid.h, west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1;
    if (isRoof(grid)) {
      // the roof: the HQ tower's glass facade on the south edge, the stair penthouse round the exit door on the north
      if (face === 'corner' || face === 'none') return south ? 'Tower_Pier' : 'Bulk_Corner';
      var g0 = gateC(grid, r), d0 = g0 === null ? 99 : Math.abs(c + 0.5 - g0);
      if (south) return d0 < 2.6 ? 'Tower_Pier' : (c % 6 === 3 ? 'Tower_Pier' : 'Tower_Glass');
      if (d0 < 2.6) return 'Bulk_Door';
      var gr = gateC(grid, 0); if (gr !== null && r <= 3 && Math.abs(c + 0.5 - gr) < 2.6) return 'Bulk_Corner';   // the door recess: plain, clear of the gate frame
      return (c % 4 === 1) ? 'Bulk_Louvre' : 'Bulk_Plain';
    }
    if ((west || east) && (north || south)) return 'WinCorner_' + (north ? 'N' : 'S') + (west ? 'W' : 'E');
    if (west || east || north || south) {
      var inward = west ? grid.at(1, r) : east ? grid.at(W - 2, r) : north ? grid.at(c, 1) : grid.at(c, Hh - 2);
      if (wallish(inward) || face === 'corner' || face === 'none') return 'Core';   // an inner wall meets the facade
      if (north || south) { var g = gateC(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return 'GateSide'; }
      var k = (north || south) ? c : r;
      if (k % 6 === 3) return 'WinCol';
      return WIN[Math.floor(hash(c * 7 + 3, r * 13 + 1) * WIN.length) % WIN.length];
    }
    var F = floorOf(grid), S = '', i;
    if (face === 'corner' || face === 'none' || !FACE[face]) {
      for (i = 0; F && i < NB.length && !S; i++) S = FSTYLE[F.at(c + NB[i][0], r + NB[i][1])] || '';
      return 'Corner' + (S || 'L');
    }
    if (!F) return 'WL';
    var d = FACE[face];
    for (i = 1; i <= 4 && !S; i++) S = FSTYLE[F.at(c + d[0] * i, r + d[1] * i)] || '';
    S = S || 'L';
    var code = F.at(c, r), piece = ART[S][code];
    if (!piece) return 'W' + S + ((c * 3 + r * 5) % 7 === 0 && grid.at(c + d[0], r + d[1]) === '.' ? '_Lamp' : '');   // no lamp behind a rack or shelf
    if (RUNS[piece]) {
      var L = LEFT[face], nl = 0, nr = 0;
      while (F.at(c + L[0] * (nl + 1), r + L[1] * (nl + 1)) === code) nl++;
      while (F.at(c - L[0] * (nr + 1), r - L[1] * (nr + 1)) === code) nr++;
      return piece + (!nl ? 'L' : !nr ? 'R' : (nl === nr || nl === nr + 1) ? 'C' : 'M');
    }
    return piece;
  }
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }

  // armory mounts in prefab-local game coordinates: [x, height, z (toward the room = +), yaw offset, kind, options]
  // (the same contract as the Strike Team HQ kit: a gun's back rests 3.5 cm in front of the rack board)
  var GUN = { back: true, len: 1.0, h: 0.34, tag: [0, -0.26, -0.008] };   // the plate clear of the slot label
  var RACK = [[-0.72, 1.05, -0.415, 0, 'gun', GUN], [0.72, 1.05, -0.415, 0, 'gun', GUN],
    [-0.72, 1.75, -0.415, 0, 'gun', GUN], [0.72, 1.75, -0.415, 0, 'gun', GUN]];
  var CGUN = { back: true, len: 1.05, h: 0.36, tag: [0, -0.25, -0.012] };
  // the island case: two slots a side on its central board (faces at z = +-0.04, guns' backs 3.5 cm off them)
  var CASE = [[0, 1.0, 0.075, 0, 'gun', CGUN], [0, 1.66, 0.075, 0, 'gun', CGUN],
    [0, 1.0, -0.075, Math.PI, 'gun', CGUN], [0, 1.66, -0.075, Math.PI, 'gun', CGUN]];
  var BENCH = [[-0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }], [0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }]];
  var SHELF = [[-0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }], [0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }]];
  function deck(color, edge) { return { deck: { thick: 0.6, color: color, edge: edge, under: edge, with: '*' } }; }
  var SYMBOLS = {
    // ---- interior floor plan
    'R': { size: [3, 1], pieces: ['WeaponRack'], orient: 'wall', kind: 'cover', mounts: RACK, fill: 0.55 },
    'C': { size: [2, 2], pieces: ['GunCase'], kind: 'cover', mounts: CASE, fill: 0.6 },
    'b': { size: [2, 1], pieces: ['Workbench'], flip: true, kind: 'cover', mounts: BENCH },
    'g': { size: [2, 1], pieces: ['GearShelf'], orient: 'wall', kind: 'cover', mounts: SHELF },
    'H': { pieces: ['ExoStand'], rotate: 'edge', kind: 'cover' },
    'l': { pieces: ['Locker', 'Locker', 'Locker_B'], rotate: 'edge', kind: 'cover' },
    'x': { pieces: ['Cases', 'Cases_B', 'AmmoCrate'], rotate: 'random90', h: 0.7, stack: { piece: 'Cases', chance: 0.3, h: 0.7 }, kind: 'cover' },
    'D': { size: [4, 1], pieces: ['OpsConsole'], orient: 'wall', kind: 'cover' },
    'K': { size: [4, 2], pieces: ['OpsDesk'], flip: true, kind: 'cover' },
    'T': { size: [4, 2], pieces: ['SeatRow'], kind: 'cover' },
    'U': { pieces: ['Lectern'], rotate: 0, kind: 'cover' },
    'p': { pieces: ['Plant', 'Plant_B'], rotate: 'random90', kind: 'cover' },
    'B': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
    'o': { pieces: ['Vending', 'Cooler'], rotate: 'edge', kind: 'cover' },
    'Q': { size: [6, 2], pieces: ['FrontDesk'], kind: 'cover' },
    't': { pieces: ['BioGate'], h: 1.05, rotate: 'run', kind: 'cover' },
    'y': { size: [3, 2], pieces: ['SimBooth'], kind: 'cover' },
    'Y': { pieces: ['HoloTarget'], rotate: 0, kind: 'cover' },
    'd': { size: [2, 2], pieces: ['DroneCradle', 'DroneCradle_B'], flip: true, kind: 'cover' },
    'V': { size: [6, 2], pieces: ['Landmark_Vault'], orient: 'wall', kind: 'wall' },
    'O': { size: [4, 4], pieces: ['Landmark_Holo'], kind: 'cover' },
    's': { pieces: ['ServerRack'], rotate: 'edge', kind: 'cover' },
    'I': { pieces: ['Column'], kind: 'cover' },
    'c': { size: [2, 1], pieces: ['Coffee'], orient: 'wall', kind: 'cover' },
    // ---- interior floor layer (flat, no collision)
    '1': flat(['Floor_StoneA', 'Floor_StoneB'], 0, true),
    '8': flat(['Floor_Border']),
    '2': flat(['Floor_Carpet']),
    '3': flat(['Floor_Rubber']),
    '4': flat(['Floor_Sim']),
    '5': flat(['Floor_Ops']),
    '7': flat(['Floor_Mat']),
    '/': flat(['Floor_Hazard']),
    '^': flat(['Floor_FireLine']),
    '-': flat(['Floor_Guide'], 0), '|': flat(['Floor_Guide'], Math.PI / 2),
    '0': { size: [4, 4], pieces: ['Emblem'], collide: false },
    // ---- ceiling layer (hanging from y = 4.5)
    'i': flat(['Ceil_Line'], 0), 'j': flat(['Ceil_Down']),
    '=': flat(['Beam'], 0), '!': flat(['Beam'], Math.PI / 2), '+': flat(['BeamX']),
    '~': flat(['Duct'], 0), ';': flat(['Duct'], Math.PI / 2),
    '{': flat(['Ceil_Tray'], 0), '}': flat(['Ceil_Tray'], Math.PI / 2),
    '[': flat(['Lintel'], 0), ']': flat(['Lintel'], Math.PI / 2),
    // ---- the roof
    'n': deck('#8C9198', '#6E737B'),
    'Z': deck('#A99C86', '#7E7466'),
    'F': { size: [3, 2], pieces: ['HVAC'], flip: true, kind: 'cover' },
    'N': { size: [4, 4], pieces: ['CoolingTower'], kind: 'cover' },
    'J': { size: [3, 3], pieces: ['WaterTank'], kind: 'cover' },
    'M': { size: [6, 4], pieces: ['MachineRoom'], flip: true, kind: 'wall' },
    'A': { size: [2, 2], pieces: ['Mast'], kind: 'cover' },
    'X': { size: [4, 6], pieces: ['Landmark_Gantry'], face: 0, kind: 'cover' },   // the jib reaches out west, over the edge
    'L': { size: [3, 2], pieces: ['Skylight'], flip: true, kind: 'cover' },
    'W': { size: [4, 2], pieces: ['Solar'], flip: true, kind: 'cover' },
    'f': { pieces: ['Vent', 'Vent_B'], rotate: 'random90', kind: 'cover' },
    'r': { pieces: ['RoofDuct'], rotate: 'run', kind: 'cover' },
    'q': { pieces: ['PlankStack'], rotate: 'edge', kind: 'cover' },
    'z': { pieces: ['RoofHatch'], rotate: 'random90', kind: 'cover' },
    '6': flat(['Floor_Paver'])
  };
  // fans: overlay meshes spun by the theme (HVAC 'F', cooling tower 'N'); each block's fan stands at its centre
  var FANS = { F: { piece: 'Fan_HVAC', y: 1.62, speed: 9 }, N: { piece: 'Fan_Tower', y: 3.32, speed: 3.2 } };
  function buildFans(level, api) {
    var A = IB.Assets, list = [];
    level.zones.forEach(function (Z) {
      [Z.grid].concat(Z.grid.layers || []).forEach(function (g) {
        Object.keys(FANS).forEach(function (ch) {
          var F = FANS[ch], used = {};
          for (var r = 0; r < g.h; r++) for (var c = 0; c < g.w; c++) {
            if (g.rows[r][c] !== ch || used[c + ',' + r]) continue;
            var d = SYMBOLS[ch].size, w = 1, h = 1;
            while (g.rows[r][c + w] === ch) w++;
            while (g.rows[r + h] && g.rows[r + h][c] === ch) h++;
            // one fan per prefab footprint (blocks of several tile by the footprint)
            var fw = w % d[0] === 0 && h % d[1] === 0 ? d[0] : d[1], fh = fw === d[0] ? d[1] : d[0];
            for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) used[(c + x) + ',' + (r + y)] = 1;
            for (var by = 0; by < h; by += fh) for (var bx = 0; bx < w; bx += fw) {
              var name = IB.themePiece(level.theme, F.piece);
              if (!A.geo[name]) continue;
              var m = new THREE.Mesh(A.get(name), A.material(name));
              m.position.set(Z.ox + c + bx + fw / 2, (g.y || 0) + F.y, Z.oz + r + by + fh / 2);
              m.rotation.y = api.hash(c + bx, r + by) * 6.28;
              Z.group.add(m);
              list.push({ m: m, s: F.speed * (0.85 + 0.3 * api.hash(r, c)) });
            }
          }
        });
      });
    });
    api.tick(function (dt) { for (var i = 0; i < list.length; i++) list[i].m.rotation.y += list[i].s * dt; });
  }

  var ALL = '.#SPEGah_%$' + Object.keys(SYMBOLS).join('');
  var WALLS = ['Core', 'GateSide', 'WinCol', 'Win_A', 'Win_B', 'Win_C', 'WinCorner_NW', 'WinCorner_NE', 'WinCorner_SW', 'WinCorner_SE',
    'Tower_Glass', 'Tower_Pier', 'Bulk_Plain', 'Bulk_Louvre', 'Bulk_Door', 'Bulk_Corner'];
  Object.keys(ART).forEach(function (S) {
    WALLS.push('W' + S, 'W' + S + '_Lamp', 'Corner' + S);
    Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (RUNS[p]) WALLS.push(p + 'L', p + 'M', p + 'C', p + 'R'); else WALLS.push(p); });
  });
  var ROOF = ['Tower_GateHead', 'Parapet', 'ParapetL', 'ParapetR', 'ParapetLR', 'Kerb', 'KerbL', 'KerbR', 'KerbLR', 'Plank_6', 'Plank_8', 'Fan_HVAC', 'Fan_Tower'];
  var PIECES = WALLS.concat(ROOF, ['CeilLight', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Sign', 'TrailWall_Plant', 'Hatch', 'Stand', 'Backdrop_RowA', 'Backdrop_RowB']);
  Object.keys(SYMBOLS).forEach(function (ch) { (SYMBOLS[ch].pieces || []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); }); });

  // the skyline round the level, one list per row piece (the Blender kit reads this block; zones.js carries each
  // tower down to the street): [x along the row, front depth, width, depth, colour, window colour, top (m above
  // our floor), style]
  var SKY = /*SKYLINE-BEGIN*/{
    Backdrop_RowA: [
      [-110, 10, 24, 22, '#D8C4A2', '#5A6E86', -40, 'deco'],
      [-74, 30, 22, 20, '#8FB3D1', '#5A6E86', 46, 'needle'],
      [-40, 8, 26, 22, '#E7E4DE', '#5A6E86', -22, 'helipad'],
      [-4, 40, 24, 24, '#4D6178', '#8FB3D1', 34, 'twist'],
      [32, 12, 22, 18, '#9CC7BE', '#5A6E86', 10, 'prism'],
      [68, 34, 24, 22, '#D8C4A2', '#5A6E86', 40, 'deco'],
      [104, 8, 22, 20, '#8FB3D1', '#5A6E86', -52, 'slab'],
      [127, 52, 14, 14, '#E7E4DE', '#5A6E86', 22, 'obelisk']
    ],
    Backdrop_RowB: [
      [-112, 20, 24, 22, '#8FB3D1', '#5A6E86', 26, 'prism'],
      [-74, 6, 26, 20, '#D8C4A2', '#5A6E86', -30, 'helipad'],
      [-38, 36, 22, 22, '#E7E4DE', '#5A6E86', 58, 'obelisk'],
      [0, 8, 26, 22, '#4D6178', '#8FB3D1', -8, 'slab'],
      [38, 30, 24, 24, '#9CC7BE', '#5A6E86', 30, 'twist'],
      [74, 6, 22, 18, '#D8C4A2', '#5A6E86', 18, 'deco'],
      [112, 28, 24, 22, '#8FB3D1', '#5A6E86', 44, 'needle']
    ]
  }/*SKYLINE-END*/;
  var BASE = -110;

  IB.registerTheme({
    id: 'highrise', name: 'Zenith Command', family: 'kit-highrise', prefix: 'KIT_HIGHRISE_',
    palette: ['#2E3540', '#36D1E0', '#3F7BEA', '#C7D3DF'],
    env: {
      // a clear, cold late morning 240 m up: deep blue overhead, a pale blue-grey haze at the horizon and in the city
      sky: ['#3F79C9', '#CBD8E4'], fog: { color: '#CBD8E4', near: 70, far: 720, tierScale: true },
      sun: [0.36, 0.5, 0.79],
      far: 1500,
      clouds: { y: [-80, -40], count: 6, scale: [2.2, 3.4], lanes: [52, 78], span: 300, speed: 0.8, axis: 'z' },
      ceiling: { height: 4.5, color: '#C4CBD4', light: 'CeilLight', every: 4, clear: ALL, clearR: 0 }
    },
    floor: {
      color: '#8F9499', trail: '#B9C2CC', outside: '#CBD8E4',
      trailLines: [{ dir: 'x', every: 1, width: 0.03, color: '#9AA6B3', y: 0.008 }, { dir: 'z', every: 1, width: 0.03, color: '#9AA6B3', y: 0.0105 }]
    },
    wall: { height: 4.5, roof: '#5A6270', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    // rack guns by weapon tier (src/game/wdrops.js TIERS): ~90 filled slots over the level (24 gun walls at 55 %, 16
    // gun cases at 60 %) -> about 1.2 purples a level; orange 0.3 % a gun
    armory: { tiers: { gray: 4, green: 52, blue: 42.4, purple: 1.3, orange: 0.3 }, gear: { common: 25, rare: 60, epic: 15, legendary: 0 } },
    // the roof zone (src/game/rooftops.js)
    rooftop: {
      void: '_', site: '%', laid: '$', depth: 240, drop: 7, flyFloor: 2.2, killer: 'The Long Drop',
      gateHead: 'Tower_GateHead',   // the HQ facade over the roof's entry door (the gate frame stops at 4.5 m)
      parapet: { piece: 'Parapet', h: 1.1, t: 0.3 }, kerb: { piece: 'Kerb', h: 0.3, t: 0.25, reach: 1 },
      plank: { width: 1.5, thick: 0.08, overhang: 0.55, pieces: { 6: 'Plank_6', 8: 'Plank_8' } },
      crew: ['soldier', 'gunner', 'blader', 'crawler'], reach: 4.6, delay: [1.2, 3.2], gap: 3.5,
      // facades of the buildings under the roofs: [wall, window, floor height]
      facades: [['#7F8C9C', '#3E5168', 4.2], ['#B9A890', '#4D5C70', 3.4], ['#5E6B7C', '#9FC3DF', 3.8], ['#C9C3B8', '#56677B', 3.3],
        ['#8E7C6C', '#465569', 3.6], ['#A3B4C2', '#3C4E66', 4.0]]
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    // the sky-bridges between the wings and onto the roof: glass on white steel, a girder under the deck
    trail: { wall: 'TrailWall', height: 4.5, variants: ['TrailWall', 'TrailWall_Sign', 'TrailWall', 'TrailWall_Plant'], end: 'TrailWall' },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: buildFans, ring: [
      { piece: 'Backdrop_RowA', pieces: ['Backdrop_RowA', 'Backdrop_RowB', 'Backdrop_RowA', 'Backdrop_RowB'], count: 4, radius: [112, 112], scale: [1, 1], squeezeX: 0.72, face: true }
    ] },
    skyline: SKY, skylineBase: BASE,
    below: {
      depth: 240, haze: '#CBD8E4', hazeTop: 0.05, hazeBottom: 0.3, hazeDist: [150, 700, 0.92], hazeMax: 1,
      glass: '#41597A', facade: '#3A4250', roof: '#8A8F96', street: '#5E6066',
      blocks: ['#B9A890', '#8E7C6C', '#9FB2C4', '#C9C3B8', '#7F8C9C', '#A3B4C2', '#C4A88E', '#99A89A'],
      extent: 600, detail: 230, horizon: 1400,
      towerTop: [5.2, 5.2, 0, 6.0],               // the HQ's two wings top out just over their ceilings; the roof zone draws its own
      bridges: true, bridgeHole: [2.6, -1.15, 4.95],
      shaftTop: BASE + 1,
      skyline: SKY,
      far: { count: 30, radius: [850, 1300], height: [-150, 30], width: [24, 50] }
    },
    budget: { prop: 3200, landmark: 6000, total: 95000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      highrise: {
        name: 'Zenith Command',
        intro: 'The last stand, 240 m up. Arm up on the armory deck, take the ops deck, then the roofs. Robots throw planks across the gaps: do not fall.',
        zones: [
          // Armory Deck: the lobby, the briefing theatre, the armory hall and the vault
          { map: 'highrise_1', ceiling: 'plain', waves: [
            [['crawler', 18], ['gunner', 12]],
            [['crawler', 8], ['bomber', 2], ['gunner', 7], ['blader', 10]],
            [['crawler', 6], ['drone', 6], ['gunner', 6], ['soldier', 8]],
            [['crawler', 6], ['bomber', 2], ['gunner', 8], ['soldier', 8], ['blader', 4]]] },
          // Operations Deck: drone bay, simulator, the holo-table room
          { map: 'highrise_2', ceiling: 'plain', waves: [
            [['crawler', 18], ['gunner', 8], ['drone', 5]],
            [['crawler', 8], ['bomber', 2], ['gunner', 8], ['blader', 11]],
            [['crawler', 6], ['drone', 8], ['gunner', 7], ['soldier', 9]],
            [['crawler', 6], ['bomber', 2], ['gunner', 8], ['blader', 6], ['soldier', 7]]] },
          // The Roof: troopers and soldiers on every roof, planks across the gaps, a last stand
          { map: 'highrise_3', ceiling: false, waves: [
            [['crawler', 12], ['gunner', 12], ['soldier', 6]],
            [['crawler', 6], ['drone', 6], ['gunner', 10], ['soldier', 8]],
            [['crawler', 6], ['bomber', 2], ['gunner', 10], ['blader', 9]],
            [['crawler', 6], ['drone', 8], ['gunner', 12], ['soldier', 8]],
            [['crawler', 8], ['bomber', 2], ['gunner', 14], ['drone', 6], ['soldier', 9], ['blader', 6]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
