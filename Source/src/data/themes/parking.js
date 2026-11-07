/* Theme: Deep Park (kit-parking) -- an extensive underground car park, three split-level zones going down B1 to B4.
   Every zone is two storeys under a 7 m ceiling: the floor plan (the deeper level) and a deck ("@layer 3.6", slab
   3.2 - 3.6) over part of it, joined by 16 m car ramps and stair flights (walkable stair blocks: robots path up and
   down them, the player walks them like a slope). Zone 2 adds a solid split-level platform at 1.8 m ("@layer 1.8")
   with half ramps up from the floor and on to the deck; zone 3 a loading dock at 1.2 m ("@layer 1.2") with delivery
   trucks backed up to it. Each level has its own colour, number and wall graphics: B1 blue, B2 green, B3 orange,
   B4 purple (zone 1 deck B1 / floor B2, zone 2 deck B2 / floor B3, zone 3 deck B3 / floor B4).
   Built by blender/fam_kit_parking.py (parking_*.py); zone layers by tools/parking_zones.py.

   A zone file holds the floor plan, then layers: "@layer 0.01" floor markings, "@layer 3.2" fittings hanging under
   the deck, "@layer 3.6" the deck, "@layer 3.61" deck markings, "@layer 7" ceiling fittings, and per zone
   "@layer 1.8" (platform, zone 2), "@layer 1.81" (its markings), "@layer 1.2" (dock, zone 3).
   Floor plan / deck / platform / dock symbols:
     V car [3,5] (sedans, hatchbacks, SUVs, a sports car, doors / boot open, a smashed one)  H car with its hazard
     lights blinking [3,5]  W wreck [3,5] (burnt-out shells, a covered car, a car on a jack)  T pickup / van [3,6]
     X box truck / tow truck [3,8]  Y delivery truck at the dock [4,10] (rear north)  m motorbike / scooter [1,2]
     k bike rack [2,4]  g maintenance buggy [2,3]  A car wash [6,9]
     N ramp rising north [5,16]  U ramp rising south  R half ramp rising north [5,8]  Z stair rising north [3,8]
     z stair rising west  q stair rising east  O dock ramp [3,6]  Q dock steps [2,3]
     I column under the deck  i column over it  C full-height column  B ticket barrier island [1,4] (arm over the
     lane to the east)  p pay station  o cones  b bollard  J jersey barrier [2,1]  K maintenance cage [3,2]
     D drums  L pallets [2,2]  w wheelie bins [2,1]  F forklift [2,3]
     u deck (slab)  t split-level platform (solid, 1.8 m)  d dock (solid, 1.2 m)  r deck-edge rail  e dock edge
   Markings: [ ] ( ) parking bay [3,5] with its back north / south / west / east  v ^ < > lane arrow  : dashed lane
     line  | crossing stripe  % yellow hatching  ! oil stain  ? puddle  & drain  $ speed bump
   Fittings (hang from the deck underside or the ceiling): = beam  + beam crossing  - duct  ~ sprinkler and water
     pipes  l strip light  f flickering strip light  x exit sign  c CCTV  _ height bar  1 2 3 4 level sign B1 - B4
   Paint (zones.js symbol option `paint`): every car, van, truck and bike gets a paint job from CAR; columns, ramps
   and stairs carry the colour of their level (LEVEL). Flickering strips and hazard lights are overlay meshes the
   theme blinks (backdrop.build). */
(function (IB) {
  'use strict';
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  var LV = ['B1', 'B2', 'B3', 'B4'];
  // palette cells (blender/parking_base.py: index = position in the palette list)
  var PAINT = 48, LVB = 40;
  var CAR = { from: [PAINT], to: [[48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [52], [54], [53], [49]] };
  // per level: zone i has its floor on level i + 2 and its deck one level up
  function levelOf(zi, y) { return Math.max(1, Math.min(4, zi + 2 - (y >= 3 ? 1 : 0))); }
  var LEVEL = { from: [LVB, LVB + 1], to: function (zi, y) { var L = levelOf(zi, y); return [LVB + 2 * (L - 1), LVB + 2 * (L - 1) + 1]; } };

  // the floor's level number of a zone grid: the deepest level sign hung in it (1 - 4)
  function floorLevel(grid) {
    if (grid._pkL === undefined) {
      var best = 0;
      [grid].concat(grid.layers || []).forEach(function (g) {
        (g.rows || []).forEach(function (row) { for (var i = 0; i < row.length; i++) { var d = row.charCodeAt(i) - 48; if (d >= 1 && d <= 4 && d > best) best = d; } });
      });
      grid._pkL = best || 2;
    }
    return grid._pkL;
  }
  function layerNear(grid, y) {
    var L = null; (grid.layers || []).forEach(function (l) { if (Math.abs(l.y - y) < 0.05) L = l; }); return L;
  }
  function gateC(grid, r) {
    var cache = grid._pkGate || (grid._pkGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows[r] || '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  var FRONT = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  /* Wall cells stack a lower (0 - 3.6) and an upper (3.6 - 7) module in the colours of the zone's two levels: a pier
     every 6 m, the level code every 12 m, arrows and pipes / hose reels scattered, lift doors and a stair door by the
     entry on the west wall (a stair door on the east), dock shutters behind the loading dock. */
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none') return 'Corner_' + (r < grid.h / 2 ? 'N' : 'S') + (c < grid.w / 2 ? 'W' : 'E');
    var ns = face === 'S' || face === 'N';
    if (ns) { var g = gateC(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return 'GateSide'; }
    var fl = floorLevel(grid), lo = LV[fl - 1], up = LV[fl - 2] || LV[0], k = ns ? c : r, line = ns ? r : c + 100, H = grid.h;
    var vl, vu;
    if (k % 6 === 3) vl = vu = 'Pier';
    else if (k % 12 === 6) vl = vu = 'Num';
    else {
      var a = hh(k, line), b = hh(k + 31, line + 7);
      vl = a < 0.13 ? 'Arrow' : a < 0.27 ? 'Pipe' : 'Plain';
      vu = b < 0.13 ? 'Arrow' : b < 0.27 ? 'Pipe' : 'Plain';
    }
    // where a beam lands on the wall (under the deck / at the ceiling) it gets a pier; ducts and pipes meet plain wall
    var fr = FRONT[face], U = layerNear(grid, 3.2), C7 = layerNear(grid, 7);
    var fu = U ? U.at(c + fr[0], r + fr[1]) : '.', fc = C7 ? C7.at(c + fr[0], r + fr[1]) : '.';
    if ('=+'.indexOf(fu) >= 0) vl = 'Pier'; else if ('-~'.indexOf(fu) >= 0 && (vl === 'Pipe' || vl === 'Pier')) vl = 'Plain';
    if ('=+'.indexOf(fc) >= 0) vu = 'Pier'; else if ('-~'.indexOf(fc) >= 0 && (vu === 'Pipe' || vu === 'Pier')) vu = 'Plain';
    if (face === 'E' && (r === H - 10 || r === H - 9)) vl = 'Lift';
    if (face === 'E' && r === H - 7) vl = 'Door';
    if (face === 'W' && r === H - 10) vl = 'Door';
    var dock = layerNear(grid, 1.2), f = FRONT[face];
    if (dock && dock.at(c + f[0], r + f[1]) !== '.') vl = 'Dock';
    // beside a zone corner: plain modules whose details stop short of the corner post (on the module's -X / +X end)
    var end = endSide(c, r, face, grid);
    if (end) vl = vu = 'End' + end;
    return ['Lo_' + lo + '_' + vl, 'Up_' + up + '_' + vu];
  }
  function endSide(c, r, face, grid) {
    var lo = face === 'S' || face === 'N' ? c === 1 : r === 1, hi = face === 'S' || face === 'N' ? c === grid.w - 2 : r === grid.h - 2;
    if (!lo && !hi) return null;
    // the module's local -X points west (S face), east (N), south (E face, the west wall) or north (W face)
    return { S: lo ? 'L' : 'R', N: lo ? 'R' : 'L', E: lo ? 'R' : 'L', W: lo ? 'L' : 'R' }[face];
  }

  /* overlays the theme animates: flickering strip lights ('f' fittings) and blinking hazard lights (cars 'H').
     Each is a separate mesh of kit pieces placed like the zone's own pieces (one cell / one [3,5] block, yaw 0). */
  function buildOverlays(level, api) {
    var A = IB.Assets, fam = 'kit-parking', strips = [[], [], []], haz = [];
    function place(list, name, x, y, z) { var m = new THREE.Matrix4().makeTranslation(x, y, z); list.push(A.placed('KIT_PARKING_' + name, m)); }
    level.zones.forEach(function (Z) {
      var grids = [Z.grid].concat(Z.grid.layers || []);
      grids.forEach(function (g) {
        var y = g.y || 0;
        for (var r = 0; r < g.h; r++) for (var c = 0; c < g.w; c++) {
          var ch = g.rows[r] ? g.rows[r][c] : '.';
          if (ch === 'f') place(strips[Math.floor(hh(c, r * 3) * 3)], 'StripGlow', Z.ox + c + 0.5, y, Z.oz + r + 0.5);
          else if (ch === 'H' && (c === 0 || g.rows[r][c - 1] !== 'H') && (r === 0 || g.rows[r - 1][c] !== 'H')) place(haz, 'HazardGlow', Z.ox + c + 1.5, y, Z.oz + r + 2.5);
        }
      });
    });
    var meshes = [];
    strips.concat([haz]).forEach(function (list, i) {
      if (!list.length) { meshes.push(null); return; }
      var mesh = new THREE.Mesh(A.merge(list), A.mat[fam]);
      level.root.add(mesh); meshes.push(mesh);
    });
    api.tick(function (dt, t) {
      for (var i = 0; i < 3; i++) {   // mostly lit; every few seconds a burst of sputtering
        var M = meshes[i]; if (!M) continue;
        var per = 3.1 + i * 1.7, ph = (t + i * 1.3) % per, burst = ph < 0.7;
        M.visible = !(burst && (Math.sin(t * (37 + i * 11)) > -0.2 || ph < 0.12));
      }
      if (meshes[3]) meshes[3].visible = (t % 0.9) < 0.45;
    });
  }

  var R90 = Math.PI / 2;
  var COLS = function (n) { return [0, 1, 2, 3].map(function (k) { return n + '_' + k; }); };
  var CARS = ['Sedan', 'Sedan', 'Sedan_Door', 'Hatch', 'Hatch', 'Hatch_Boot', 'SUV', 'SUV', 'SUV_Boot', 'Sports', 'Sedan', 'Wreck_Smash'];
  var BAYS = ['Bay_A', 'Bay_B', 'Bay_C', 'Bay_D', 'Bay_A', 'Bay_C', 'Bay_B', 'Bay_EV', 'Bay_D', 'Bay_H'];
  var WALLS = ['Corner_NW', 'Corner_NE', 'Corner_SW', 'Corner_SE', 'GateSide'];
  LV.forEach(function (L) {
    ['Plain', 'Num', 'Arrow', 'Pipe', 'Pier', 'Door', 'Lift', 'Dock', 'EndL', 'EndR'].forEach(function (v) { WALLS.push('Lo_' + L + '_' + v); });
    ['Plain', 'Num', 'Arrow', 'Pipe', 'Pier', 'EndL', 'EndR'].forEach(function (v) { WALLS.push('Up_' + L + '_' + v); });
  });
  var OTHER = ['Sedan', 'Sedan_Door', 'Hatch', 'Hatch_Hazard', 'Hatch_Boot', 'SUV', 'SUV_Boot', 'Sports', 'HazardGlow', 'Wreck_Burnt',
    'Wreck_Burnt_B', 'Wreck_Smash', 'CarCovered', 'CarJack', 'Pickup', 'Pickup_B', 'Van', 'Van_Door', 'BoxTruck', 'TowTruck',
    'DeliveryTruck', 'Motorbike', 'Scooter', 'BikeRack', 'Buggy', 'Rail', 'RailFull', 'RailPost', 'Ramp', 'RampHalf', 'DockRamp',
    'Stair', 'DockStep', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Bay_A', 'Bay_B', 'Bay_C',
    'Bay_D', 'Bay_EV', 'Bay_H', 'Arrow', 'LaneDash', 'Zebra', 'Hatching', 'Oil_A', 'Oil_B', 'Puddle', 'Drain', 'SpeedBump', 'Beam',
    'BeamX', 'Duct', 'Pipes', 'Strip', 'StripOff', 'StripGlow', 'ExitSign', 'LevelSign_B1', 'LevelSign_B2', 'LevelSign_B3',
    'LevelSign_B4', 'HeightBar', 'CCTV', 'Barrier_Down', 'Barrier_Up', 'PayStation', 'Cone', 'Cones', 'Bollard', 'Jersey_C',
    'Jersey_P', 'Cage', 'Drums', 'Pallets', 'Bins', 'Forklift', 'DockEdge', 'DockEdge_L', 'Landmark_CarWash']
    .concat(COLS('Col_Lo'), COLS('Col_Hi'), COLS('Col_Full'));
  function bay(face) { return { size: [3, 5], pieces: BAYS, face: face, collide: false }; }

  IB.registerTheme({
    id: 'parking', name: 'Deep Park', family: 'kit-parking', prefix: 'KIT_PARKING_',
    palette: ['#3A86E0', '#2FB06A', '#F4892C', '#A257DA'],
    env: {
      sky: null, clear: '#4E5866', fog: { color: '#4E5866', near: 38, far: 112 }, clouds: false,
      sun: [0.32, 0.86, 0.4],
      ceiling: { height: 7, color: '#EFEBD3' }   // fittings come from the zone's "@layer 7" grid
    },
    // poured concrete, 6 m pour joints (bays, lanes and stains are layer pieces on top)
    floor: {
      color: '#A9A397', trail: '#9F998D', outside: '#A9A397',
      lines: [{ dir: 'x', every: 6, width: 0.035, color: '#958F83', y: 0.006 }, { dir: 'z', every: 6, width: 0.035, color: '#958F83', y: 0.008 }]
    },
    wall: { height: 7, roof: '#8C867D', facing: 'open', choose: chooseWall },
    symbols: {
      // vehicles
      'V': { size: [3, 5], pieces: CARS, flip: true, kind: 'cover', paint: CAR },
      'H': { size: [3, 5], pieces: ['Hatch_Hazard'], face: 0, kind: 'cover', paint: CAR },
      'W': { size: [3, 5], pieces: ['Wreck_Burnt', 'Wreck_Burnt_B', 'CarCovered', 'CarJack'], flip: true, kind: 'cover', paint: CAR },
      'T': { size: [3, 6], pieces: ['Pickup', 'Van', 'Pickup_B', 'Van_Door'], flip: true, kind: 'cover', paint: CAR },
      'X': { size: [3, 8], pieces: ['BoxTruck', 'TowTruck'], flip: true, kind: 'cover', paint: CAR },
      'Y': { size: [4, 10], pieces: ['DeliveryTruck'], face: 0, kind: 'cover', paint: CAR },
      'm': { size: [1, 2], pieces: ['Motorbike', 'Scooter'], flip: true, kind: 'cover', paint: CAR },
      'k': { size: [2, 4], pieces: ['BikeRack'], flip: true, kind: 'cover', paint: CAR },
      'g': { size: [2, 3], pieces: ['Buggy'], flip: true, kind: 'cover' },
      'A': { size: [6, 9], pieces: ['Landmark_CarWash'], face: 0, kind: 'cover' },
      // circulation
      'N': { size: [5, 16], pieces: ['Ramp'], face: 0, kind: 'step', paint: LEVEL },
      'U': { size: [5, 16], pieces: ['Ramp'], face: Math.PI, kind: 'step', paint: LEVEL },
      'R': { size: [5, 8], pieces: ['RampHalf'], face: 0, kind: 'step', paint: LEVEL },
      'Z': { size: [3, 8], pieces: ['Stair'], face: 0, kind: 'step', paint: LEVEL },
      'z': { size: [3, 8], pieces: ['Stair'], face: R90, kind: 'step', paint: LEVEL },
      'q': { size: [3, 8], pieces: ['Stair'], face: -R90, kind: 'step', paint: LEVEL },
      'O': { size: [3, 6], pieces: ['DockRamp'], face: 0, kind: 'step', paint: LEVEL },
      'Q': { size: [2, 3], pieces: ['DockStep'], face: 0, kind: 'step', paint: LEVEL },
      // structure
      'I': { pieces: COLS('Col_Lo'), kind: 'cover', paint: LEVEL },
      'i': { pieces: COLS('Col_Hi'), kind: 'cover', paint: LEVEL },
      'C': { pieces: COLS('Col_Full'), kind: 'cover', paint: LEVEL },
      'u': { deck: { thick: 0.4, color: '#B0AA9E', edge: '#8C867D', under: '#EBE7D0', with: '*' } },
      't': { deck: { thick: 1.8, color: '#B5AFA3', edge: '#9A9488', under: '#9A9488', with: '*' } },
      'd': { deck: { thick: 1.2, color: '#9DA3A8', edge: '#5C6168', under: '#5C6168', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'ri', post: 'RailPost', kind: 'wall' },
      'e': { pieces: ['DockEdge', 'DockEdge', 'DockEdge_L'], rotate: 'edge', collide: false },
      // props
      'B': { size: [1, 4], pieces: ['Barrier_Down', 'Barrier_Up'], face: 0, kind: 'cover' },
      'p': { pieces: ['PayStation'], rotate: 0, kind: 'cover' },
      'o': { pieces: ['Cone', 'Cones'], rotate: 'random90', kind: 'cover' },
      'b': { pieces: ['Bollard'], kind: 'cover' },
      'J': { size: [2, 1], pieces: ['Jersey_C', 'Jersey_P'], flip: true, kind: 'cover' },
      'K': { size: [3, 2], pieces: ['Cage'], flip: true, kind: 'cover' },
      'D': { pieces: ['Drums'], rotate: 'random90', kind: 'cover' },
      'L': { size: [2, 2], pieces: ['Pallets'], flip: true, kind: 'cover' },
      'w': { size: [2, 1], pieces: ['Bins'], flip: true, kind: 'cover' },
      'F': { size: [2, 3], pieces: ['Forklift'], flip: true, kind: 'cover' },
      // markings (floor / deck marking layers)
      '[': bay(0), ']': bay(Math.PI), '(': bay(R90), ')': bay(-R90),
      'v': { pieces: ['Arrow'], rotate: 0, collide: false },
      '^': { pieces: ['Arrow'], rotate: Math.PI, collide: false },
      '<': { pieces: ['Arrow'], rotate: -R90, collide: false },
      '>': { pieces: ['Arrow'], rotate: R90, collide: false },
      ':': { pieces: ['LaneDash'], rotate: 'run', collide: false },
      '|': { pieces: ['Zebra'], rotate: 'run', collide: false },
      '%': { pieces: ['Hatching'], collide: false },
      '!': { pieces: ['Oil_A', 'Oil_B'], rotate: 'random90', collide: false },
      '?': { pieces: ['Puddle'], rotate: 'random90', collide: false },
      '&': { pieces: ['Drain'], collide: false },
      '$': { pieces: ['SpeedBump'], rotate: 'run', collide: false },
      // fittings (hang from the deck underside / the ceiling)
      '=': { pieces: ['Beam'], rotate: 'run', collide: false },
      '+': { pieces: ['BeamX'], collide: false },
      '-': { pieces: ['Duct'], rotate: 'run', collide: false },
      '~': { pieces: ['Pipes'], rotate: 'run', collide: false },
      'l': { pieces: ['Strip'], collide: false },
      'f': { pieces: ['StripOff'], collide: false },
      'x': { pieces: ['ExitSign'], collide: false },
      'c': { pieces: ['CCTV'], rotate: 'random90', collide: false },
      '_': { pieces: ['HeightBar'], collide: false },
      '1': { pieces: ['LevelSign_B1'], collide: false }, '2': { pieces: ['LevelSign_B2'], collide: false },
      '3': { pieces: ['LevelSign_B3'], collide: false }, '4': { pieces: ['LevelSign_B4'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C'], height: 7 },
    hatch: 'Hatch', stand: 'Drums',
    backdrop: { build: buildOverlays },
    budget: { prop: 3000, landmark: 4000, total: 90000 },
    allPieces: function () { return WALLS.concat(OTHER); },
    levels: {
      parking: {
        name: 'Deep Park',
        intro: 'Robots hold every level of the car park. Take the ramps and stairs down to B4 and clear the loading dock.',
        zones: [
          // B1 / B2: the entry level, ticket barriers, two ramps up to a U-shaped deck
          { map: 'parking_1', waves: [[['crawler', 22], ['gunner', 6]], [['crawler', 6], ['bomber', 5], ['gunner', 5], ['blader', 7]], [['crawler', 5], ['drone', 5], ['gunner', 5], ['soldier', 7]], [['crawler', 5], ['bomber', 5], ['gunner', 6], ['soldier', 8]]] },
          // B2 / B3: the split level, a platform at half height between the floor and the deck, the car wash
          { map: 'parking_2', waves: [[['crawler', 22], ['gunner', 6], ['drone', 3]], [['crawler', 6], ['bomber', 5], ['gunner', 6], ['blader', 8]], [['crawler', 6], ['drone', 6], ['gunner', 5], ['soldier', 7]], [['crawler', 5], ['bomber', 5], ['gunner', 6], ['blader', 6], ['soldier', 4]]] },
          // B3 / B4: the deep level and the loading dock, a heavy last wave
          { map: 'parking_3', waves: [[['crawler', 22], ['gunner', 9]], [['crawler', 6], ['bomber', 6], ['drone', 5], ['soldier', 8]], [['crawler', 8], ['gunner', 8], ['drone', 5], ['blader', 7]], [['crawler', 9], ['gunner', 9], ['bomber', 8], ['drone', 4], ['soldier', 13]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
