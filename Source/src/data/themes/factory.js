/* Theme: Robot Works (kit-factory). The enemy's robot assembly plant: tall steel-framed halls with painted block
   dados, blue corrugated siding and a clerestory window band (the dusk sky, smokestacks and sawtooth roofs of the
   works show through), roof trusses with high-bay lamps throwing pools of light, assembly lines building half-done
   Crawlers, Gunners, Bombers and Drones under robot arms, conveyors of parts, crates and pallets, overhead catwalks,
   hazard stripes everywhere, a giant stamping press with its forge, and the supervisor's raised control booth.
   Built by blender/fam_kit_factory.py; zone layouts by tools/industrial_zones.py (src/data/zones/factory_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  walls: on the zone edge, 6 m bays (red I-beam column, then window modules: plain, glints, electrical panel,
        stencilled robot sign, exhaust fan, fire hose); solid siding near the gates; end modules (trims stop short,
        no pipes) beside inside corners; interior '#' = painted block walls
     A  assembly line section [8, 4] (Crawler, Gunner, Bomber, Drone in sequence; runs of them make long lines); the
        belt MOVES: half-built robots ride it out of a feed hood at one end of the run into an exit hood at the other,
        the cleats scroll, neighbouring runs flow opposite ways (theme conveyor option, see zones.js "moving lines")
     R  robot arm cell [2, 2]        =  moving belt conveyor with parts, feed / exit hoods at the run ends (runs)
     c  parts crates (stacked)
     p  pallet of parts [2, 2]       b  drums      g  gas cylinder rack      x  welding screen / tool chest
     K  overhead catwalk [2, 8] (walk under it; runs join end to end)        M  machine tool [3, 2]
     Q  rack of finished robots [6, 2]       W  robot test cage [4, 4]       z  hazard floor pad [2, 2] (no collision)
     T  giant press + forge [10, 8] (landmark, front to the south)          B  raised control booth [8, 6] (landmark)
   Floor decals (lamp pools from the roof trusses, hazard pads, cage floors, the booth's and the press's pools) each sit
   at their own height, so overlapping decals never z-fight. */
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
  // distance (cells) from a wall cell on the north / south edge to the centre of that edge's gate
  function gateDist(grid, c, r) {
    if (r !== 0 && r !== grid.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < grid.w; x++) if (grid.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  var WIN = ['Wall_Win_A', 'Wall_Win_A', 'Wall_Win_B', 'Wall_Win_A', 'Wall_Win_Panel', 'Wall_Win_A', 'Wall_Win_Vent', 'Wall_Win_B', 'Wall_Win_Hose'];
  function pick(list, h) { return list[Math.min(list.length - 1, Math.floor(h * list.length))]; }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = face || faceOf(grid, c, r);
    if (F === 'none' || F === 'corner') return 'Corner';
    var edge = c === 0 || r === 0 || c === grid.w - 1 || r === grid.h - 1;
    var u = (F === 'S' || F === 'N') ? c : r;
    if (!edge) {   // interior block walls
      var h = hash(c * 5 + 3, r * 7 + 1);
      return h < 0.12 ? 'Block_Arrow' : h < 0.2 ? 'Block_Num' : 'Block_Plain';
    }
    var gd = gateDist(grid, c, r);
    if (gd < 4) return gd > 2.6 ? 'Wall_Panel' : 'Wall_Plain';
    if (u % 6 === 0 && runOK(grid, c, r, F, 1)) return 'Wall_Col';
    if (!runOK(grid, c, r, F, 1)) {
      // the run ends in a corner on one or both sides: an end module that keeps its trims and pipes out of the
      // corner square (the module's local +X side is east for S, west for N, north for E, south for W)
      var along = F === 'S' || F === 'N';
      var lo = along ? runOK1(grid, c - 1, r, F) : runOK1(grid, c, r - 1, F), hi = along ? runOK1(grid, c + 1, r, F) : runOK1(grid, c, r + 1, F);
      var plusIsHi = F === 'S' || F === 'W', R = plusIsHi ? !hi : !lo, L = plusIsHi ? !lo : !hi;
      return 'Wall_End' + (L && R ? 'LR' : L ? 'L' : 'R');
    }
    if (u % 6 === 3 && hash(c * 11 + 2, r * 13 + 5) < 0.35) return 'Wall_Win_Sign';
    return pick(WIN, hash(c * 7 + 3, r * 13 + 1));
  }
  var WALLS = ['Wall_Win_A', 'Wall_Win_B', 'Wall_Win_Panel', 'Wall_Win_Sign', 'Wall_Win_Vent', 'Wall_Win_Hose',
    'Wall_Plain', 'Wall_Panel', 'Wall_Col', 'Wall_EndL', 'Wall_EndR', 'Wall_EndLR', 'Corner', 'Block_Plain', 'Block_Arrow', 'Block_Num'];

  IB.registerTheme({
    id: 'factory', name: 'Robot Works', family: 'kit-factory', prefix: 'KIT_FACTORY_',
    palette: ['#5F80A0', '#F2C230', '#EC7A2E', '#B7B3AA'],
    env: {
      // dusk outside the clerestory; a warm industrial haze inside; lamps every 12 m on the roof trusses
      sky: ['#6D8FC9', '#F6B98A'], clouds: true,
      fog: { color: '#D9C6B2', near: 45, far: 150 },
      sun: [0.35, 0.85, 0.4],
      ceiling: { height: 10.0, color: '#8E9097', light: 'CeilTruss', every: 12 }
    },
    // power-floated concrete with saw-cut joints every 4 m; a lighter service-corridor floor
    floor: {
      color: '#ABA8A0', trail: '#B9B5AB', outside: '#7E7A76',
      lines: [{ dir: 'x', every: 4, width: 0.04, color: '#97948C', y: 0.008 }, { dir: 'z', every: 4, width: 0.04, color: '#97948C', y: 0.0105 }]
    },
    wall: { height: 10.4, roof: '#8E9097', facing: 'open', choose: chooseWall },
    symbols: {
      // moving lines: half-built robots ride the assembly belts and parts the conveyors, out of a feed hood at one end
      // of each run and into an exit hood at the other; the belt cleats scroll; a player on a belt top is carried
      'A': { size: [8, 4], pieces: ['Line_Crawler', 'Line_Gunner', 'Line_Bomber', 'Line_Drone'], sequence: true, kind: 'wall',
             conveyor: { speed: 0.55, dir: 'alt', y: 0.884, spacing: 2.6, inset: 0.6, ends: { start: 'Line_Feed', end: 'Line_Exit', at: 0.6 },
                         items: ['LineBot_CrawlerBare', 'LineBot_Gunner', 'LineBot_Bomber', 'LineBot_Crawler', 'LineBot_GunnerBare', 'LineBot_Drone'],
                         cleat: 'Line_Cleat', cleatEvery: 0.8, cleatY: 0.884, carry: { top: 1.05, width: 0.9 } } },
      'R': { size: [2, 2], pieces: ['Arm_A', 'Arm_B'], flip: true, kind: 'cover' },
      '=': { pieces: ['Conveyor'], rotate: 'run', kind: 'cover',
             conveyor: { speed: 0.7, dir: 'alt', y: 0.864, spacing: 1.3, inset: 0.5, ends: { start: 'Conveyor_Feed', end: 'Conveyor_Exit', at: 0.5 },
                         items: ['Item_Can', 'Item_Bottle', 'Item_Drone', 'Item_Wheels'], cleat: 'Belt_Cleat', cleatEvery: 0.5, cleatY: 0.864,
                         carry: { top: 1.0, width: 0.9 } } },
      'c': { pieces: ['Crate_Cans', 'Crate_Wheels', 'Crate_Closed'], h: 0.86, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.5 }, kind: 'cover' },
      'p': { size: [2, 2], pieces: ['Pallet_Bins', 'Pallet_Cans', 'Pallet_Bottles'], flip: true, kind: 'cover' },
      'b': { pieces: ['Drums_A', 'Drums_B'], rotate: 'random90', kind: 'cover' },
      'g': { pieces: ['GasRack'], rotate: 'random90', kind: 'cover' },
      'x': { pieces: ['WeldScreen', 'ToolChest'], rotate: 'random90', sequence: true, kind: 'cover' },
      'K': { size: [2, 8], pieces: ['Catwalk'], kind: 'cover' },
      'M': { size: [3, 2], pieces: ['Machine_Mill', 'Machine_Lathe'], flip: true, kind: 'cover' },
      'Q': { size: [6, 2], pieces: ['Landmark_RobotRack'], flip: true, kind: 'wall' },
      'W': { size: [4, 4], pieces: ['TestCage'], flip: true, kind: 'wall' },
      'z': { size: [2, 2], pieces: ['Hazard_A', 'Hazard_B'], collide: false },
      'T': { size: [10, 8], pieces: ['Landmark_Press'], kind: 'wall' },
      'B': { size: [8, 6], pieces: ['Landmark_Booth'], kind: 'wall' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // end-room back wall faces out (siding toward the lift): turned inward, its half-ceilings overlap the side walls'
    trail: { wall: 'TrailWall', height: 10.4, end: 'TrailWall', endYaw: Math.PI / 2, endLift: 0 },
    hatch: 'Hatch', stand: 'Stand',
    // the works outside the clerestory: one long slice due east, west, north and south of the level, facing it
    backdrop: { ring: [
      { piece: 'Backdrop_Works', count: 4, radius: [60, 60], scale: [1, 1], squeezeX: 0.36, face: true }
    ] },
    budget: { prop: 2000, landmark: 4000, total: 70000 },
    allPieces: function () {
      var out = WALLS.concat(['CeilTruss', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'Backdrop_Works']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        sym[ch].pieces.concat(sym[ch].stack ? [sym[ch].stack.piece] : [], IB.conveyorPieces(sym[ch].conveyor)).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      factory: {
        name: 'Robot Works',
        intro: 'This is where they come from. Shut down the lines, the press shop, then the dispatch floor.',
        zones: [
          // Assembly Hall: 36 robots between the lines
          { map: 'factory_lines', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['crawler', 5], ['bomber', 2], ['gunner', 1], ['soldier', 1]],
            [['crawler', 4], ['gunner', 2], ['drone', 2], ['blader', 1]],
            [['crawler', 5], ['bomber', 3], ['soldier', 1]]] },
          // Press Shop: 37 robots, drones over the press
          { map: 'factory_press', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['drone', 3], ['crawler', 3], ['bomber', 2], ['blader', 2]],
            [['gunner', 3], ['crawler', 4], ['soldier', 2]],
            [['crawler', 4], ['bomber', 2], ['drone', 2], ['blader', 1]]] },
          // Control & Dispatch: 42 robots, the dense finale under the booth
          { map: 'factory_dispatch', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['drone', 2], ['bomber', 2], ['crawler', 4], ['soldier', 2]],
            [['gunner', 3], ['crawler', 4], ['drone', 1], ['soldier', 2]],
            [['crawler', 3], ['bomber', 2], ['gunner', 3], ['drone', 3], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
