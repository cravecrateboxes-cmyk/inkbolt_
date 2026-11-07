/* Theme: Heavy Works (kit-factory2). The plant where the enemy builds its BIG robots: 16 m halls with oxide-red block
   plinths, deep-teal corrugated siding, a crane runway on corbels along every wall and a high clerestory onto a late
   dusk (blast furnaces, cooling stacks, a goliath crane); roof bays with high-bay lamps, some with an overhead bridge
   crane carrying an armour plate or a mech leg. On the floor the moving build lines: walker mechs and tread bruisers
   (4-7 m tall) ride skids out of the feed house, through the drivetrain, armour and paint booths (bare chassis frame
   -> drivetrain fitted -> armour plated in primer -> painted orange / teal and cream) into the dispatch house; belts of
   parts, weld cells with sparks, chassis jigs, plate machines, leg racks, stacked plates and giant wheels, a fenced
   test track a finished bruiser laps, and the Titan dock (a 10 m mech in its scaffold).
   Built by blender/fam_kit_factory2.py; zone layouts by tools/heavy_zones.py (src/data/zones/factory2_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  walls: zone edge = window modules (plain, glints, panel, bay number, duct, hose) with an I-beam column every
        6 m, plain modules near the gates, end modules beside inside corners; interior '#' = block walls
     L  walker build line [14, 8], runs of four (feed house + drivetrain booth, armour booth, paint booth, dispatch
        house); the walkers move east through the stages (moving line, see `conveyor`)
     U  bruiser build line, the same tiles with tread bruisers riding it
     =  moving belt of parts (plates, hubs, rams, lamp pods) between a feed and an exit hood (runs)
     C  weld cell [4, 4]     X  chassis jig [6, 4]     M  plate machine [4, 2]     l  leg rack [4, 2]
     p  armour plates [2, 2]     w  wheels / tread coil [2, 2]     c  parts crates     b  drums     x  gas cart / weld screen
     z  hazard floor pad [2, 2] (no collision)     T  test track [16, 12] (a finished bruiser laps it)     D  Titan dock [10, 8]
   Floor decals (lamp pools, track beds, hazard pads, cells, test track, dock) each sit at their own height. */
(function (IB) {
  'use strict';
  var SOLID = '#GE';
  function solid(grid, c, r) { return SOLID.indexOf(grid.at(c, r)) >= 0; }
  function faceOf(grid, c, r) {
    var oS = !solid(grid, c, r + 1), oN = !solid(grid, c, r - 1), oE = !solid(grid, c + 1, r), oW = !solid(grid, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  function runOK(grid, c, r, F, k) {
    var along = F === 'S' || F === 'N';
    for (var d = -k; d <= k; d++) {
      var x = along ? c + d : c, y = along ? r : r + d;
      if (grid.at(x, y) !== '#' || faceOf(grid, x, y) !== F) return false;
    }
    return true;
  }
  function runOK1(grid, c, r, F) { return grid.at(c, r) === '#' && faceOf(grid, c, r) === F; }
  function gateDist(grid, c, r) {
    if (r !== 0 && r !== grid.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < grid.w; x++) if (grid.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  var WIN = ['Wall_Win_A', 'Wall_Win_A', 'Wall_Win_B', 'Wall_Win_A', 'Wall_Win_Panel', 'Wall_Win_A', 'Wall_Win_Duct', 'Wall_Win_B', 'Wall_Win_Hose'];
  function pick(list, h) { return list[Math.min(list.length - 1, Math.floor(h * list.length))]; }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = face || faceOf(grid, c, r);
    if (F === 'none' || F === 'corner') return 'Corner';
    var edge = c === 0 || r === 0 || c === grid.w - 1 || r === grid.h - 1;
    var u = (F === 'S' || F === 'N') ? c : r;
    if (!edge) { var h = hash(c * 5 + 3, r * 7 + 1); return h < 0.12 ? 'Block_Arrow' : h < 0.2 ? 'Block_Num' : 'Block_Plain'; }
    var gd = gateDist(grid, c, r);
    if (gd < 4) return gd > 2.6 ? 'Wall_Panel' : 'Wall_Plain';
    if (u % 6 === 0 && runOK(grid, c, r, F, 1)) return 'Wall_Col';
    if (!runOK(grid, c, r, F, 1)) {
      var along = F === 'S' || F === 'N';
      var lo = along ? runOK1(grid, c - 1, r, F) : runOK1(grid, c, r - 1, F), hi = along ? runOK1(grid, c + 1, r, F) : runOK1(grid, c, r + 1, F);
      var plusIsHi = F === 'S' || F === 'W', R = plusIsHi ? !hi : !lo, L = plusIsHi ? !lo : !hi;
      return 'Wall_End' + (L && R ? 'LR' : L ? 'L' : 'R');
    }
    if (u % 12 === 3 && hash(c * 11 + 2, r * 13 + 5) < 0.5) return 'Wall_Win_Sign';
    return pick(WIN, hash(c * 7 + 3, r * 13 + 1));
  }
  var WALLS = ['Wall_Win_A', 'Wall_Win_B', 'Wall_Win_Panel', 'Wall_Win_Sign', 'Wall_Win_Duct', 'Wall_Win_Hose',
    'Wall_Plain', 'Wall_Panel', 'Wall_Col', 'Wall_EndL', 'Wall_EndR', 'Wall_EndLR', 'Corner', 'Block_Plain', 'Block_Arrow', 'Block_Num'];
  var BAYS = ['CeilBay', 'CeilBay', 'CeilBay_Plate', 'CeilBay', 'CeilBay_Leg'];
  // a rounded rectangle (half sizes a, b, corner radius r) as a closed polyline, counter-clockwise seen from above
  function loop(a, b, r, n) {
    var pts = [], corners = [[a - r, b - r, 0], [-(a - r), b - r, 1], [-(a - r), -(b - r), 2], [a - r, -(b - r), 3]];
    corners.forEach(function (C) {
      for (var i = 0; i <= n; i++) { var t = (C[2] + i / n) * Math.PI / 2; pts.push([C[0] + Math.cos(t) * r, C[1] + Math.sin(t) * r]); }
    });
    return pts;
  }
  // the build line: one tile kind per stage station; the mechs pop in inside the feed house (2.1 m in) and out
  // inside the dispatch house, and change stage in the middle of each booth (tile-local x = 4.75)
  function buildLine(stages) {
    return { size: [14, 8], pieces: ['Jig_Feed', 'Jig_Armour', 'Jig_Paint', 'Jig_Dispatch'], sequence: 'run', kind: 'wall',
      conveyor: { speed: 0.45, dir: 1, y: 0, spacing: 9.0, inset: 2.1, items: [stages],
        stations: { Jig_Feed: 4.75, Jig_Armour: 4.75, Jig_Paint: 4.75 }, cleat: 'Track_Slat', cleatEvery: 1.0, cleatY: 0.028 } };
  }

  IB.registerTheme({
    id: 'factory2', name: 'Heavy Works', family: 'kit-factory2', prefix: 'KIT_FACTORY2_',
    palette: ['#1F5A63', '#F07A22', '#A8442E', '#EFE3C4'],
    env: {
      // late dusk outside the clerestory (an orange furnace glow on the horizon); a warm, smoky haze in the halls
      sky: ['#3A5576', '#F29A55'], clouds: true,
      fog: { color: '#C9B49A', near: 55, far: 175 },
      sun: [-0.4, 0.8, 0.45],
      ceiling: { height: 16.0, color: '#7F858C', light: BAYS, every: 12 }
    },
    floor: {
      color: '#A39E96', trail: '#B3AEA5', outside: '#6E6A66',
      lines: [{ dir: 'x', every: 4, width: 0.05, color: '#8F8A82', y: 0.008 }, { dir: 'z', every: 4, width: 0.05, color: '#8F8A82', y: 0.0105 }]
    },
    wall: { height: 16.4, roof: '#7F858C', facing: 'open', choose: chooseWall },
    symbols: {
      'L': buildLine(['Mech_Walker_Frame', 'Mech_Walker_Drive', 'Mech_Walker_Armour', 'Mech_Walker_Paint']),
      'U': buildLine(['Mech_Bruiser_Frame', 'Mech_Bruiser_Drive', 'Mech_Bruiser_Armour', 'Mech_Bruiser_Paint']),
      '=': { pieces: ['Belt'], rotate: 'run', kind: 'cover',
             conveyor: { speed: 0.6, dir: 'alt', y: 0.844, spacing: 1.4, inset: 0.5, ends: { start: 'Belt_Feed', end: 'Belt_Exit', at: 0.5 },
                         items: ['Part_Plate', 'Part_Hub', 'Part_Piston', 'Part_Lamp'], cleat: 'Belt_Cleat', cleatEvery: 0.5, cleatY: 0.844,
                         carry: { top: 0.98, width: 0.9 } } },
      'C': { size: [4, 4], pieces: ['WeldCell_A', 'WeldCell_B'], flip: true, kind: 'cover' },
      'X': { size: [6, 4], pieces: ['ChassisJig_Bruiser', 'ChassisJig_Walker'], flip: true, kind: 'wall' },
      'M': { size: [4, 2], pieces: ['Machine_Brake', 'Machine_Plasma'], flip: true, kind: 'cover' },
      'l': { size: [4, 2], pieces: ['LegRack'], flip: true, kind: 'cover' },
      'p': { size: [2, 2], pieces: ['Plates_Flat', 'Plates_Rack'], kind: 'cover' },
      'w': { size: [2, 2], pieces: ['Wheels_Stack', 'Wheels_Cradle', 'Wheels_Coil'], kind: 'cover' },
      'c': { pieces: ['Crate_Open', 'Crate_Closed'], h: 0.9, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.5 }, kind: 'cover' },
      'b': { pieces: ['Drums_A', 'Drums_B'], rotate: 'random90', kind: 'cover' },
      'x': { pieces: ['GasCart', 'WeldScreen'], rotate: 'random90', sequence: true, kind: 'cover' },
      'z': { size: [2, 2], pieces: ['Hazard_A', 'Hazard_B'], collide: false },
      // the test track: a finished bruiser laps the lane (a closed loop in the prefab's own metres)
      'T': { size: [16, 12], pieces: ['TestTrack'], kind: 'wall',
             conveyor: { path: loop(5.9, 3.9, 1.5, 6), speed: 2.4, n: 2, y: 0, items: ['Mech_Bruiser_Test'] } },
      'D': { size: [10, 8], pieces: ['Landmark_Titan'], kind: 'wall' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 16.4, end: 'TrailWall', endYaw: Math.PI / 2, endLift: 0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { ring: [
      { piece: 'Backdrop_Heavy', count: 4, radius: [60, 60], scale: [1, 1], squeezeX: 0.36, face: true }
    ] },
    budget: { prop: 3000, landmark: 5000, total: 70000 },
    allPieces: function () {
      var out = WALLS.concat(BAYS, ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'Backdrop_Heavy']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        sym[ch].pieces.concat(sym[ch].stack ? [sym[ch].stack.piece] : [], IB.conveyorPieces(sym[ch].conveyor)).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out.filter(function (n, i) { return out.indexOf(n) === i; });
    },
    levels: {
      factory2: {
        name: 'Heavy Works',
        intro: 'The big ones are built here. Stop the chassis hall, the armour shop, then the dispatch floor.',
        zones: [
          // Chassis Hall: 42 robots around the walker line
          { map: 'factory2_chassis', waves: [
            [['crawler', 7], ['gunner', 3]],
            [['crawler', 6], ['bomber', 3], ['gunner', 2]],
            [['gunner', 3], ['drone', 3], ['crawler', 5]],
            [['crawler', 6], ['bomber', 2], ['gunner', 2]]] },
          // Armour & Test: 44 robots, drones over the bruiser line and the test track
          { map: 'factory2_armour', waves: [
            [['crawler', 6], ['gunner', 3], ['drone', 1]],
            [['drone', 3], ['crawler', 6], ['bomber', 2]],
            [['gunner', 4], ['crawler', 6], ['bomber', 1]],
            [['crawler', 6], ['bomber', 3], ['drone', 3]]] },
          // Dispatch & the Titan: 50 robots, the dense finale under the Titan
          { map: 'factory2_dispatch', waves: [
            [['crawler', 7], ['gunner', 3], ['drone', 1]],
            [['drone', 3], ['bomber', 3], ['crawler', 6]],
            [['gunner', 4], ['crawler', 7], ['drone', 2]],
            [['crawler', 6], ['bomber', 3], ['gunner', 3], ['drone', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
