/* Theme: Deep Coal Mine (kit-coalmine). A big room-and-pillar coal mine far underground: dark faceted rock with
   banded strata and glinting coal seams, coal pillars holding up a low dark roof, timbered drifts with plank
   lagging, narrow-gauge rail with ore carts, belt conveyors, cribs and roof jacks, and warm pools of lantern light.
   Built by blender/fam_kit_coalmine.py; zone layouts by tools/industrial_zones.py (src/data/zones/coalmine_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  rock: faceted strata walls (seams, lamps on brackets, prop timbers, signs, overlooks into the old workings on the
        east / west edges); corners, notches and coal pillars' edges get all-round rock lumps
     Y  timbered drift [6, 1] (posts, cap, lagging, plank bulkhead to the roof): runs of Y across a 6 m gap in the rock
        make a closed tunnel          y  the same with the track (on the cell at local x + 0.5)
     -  rail (1 m, turns with its run)        C  ore cart on its rails [1, 2]
     c  powder / tool crates (stacked)       u  coal sacks         =  stacked timbers (runs)     b  oil drums
     O  coal heap [2, 2]                     X  timber crib with a roof post [2, 2]             I  roof jack
     k  belt conveyor (runs)                 l  lantern post        L  work light on a tripod
     w  puddle [2, 2] (no collision)         d  coal dust spill [2, 2] (no collision)
     T  drill rig at the coal face [8, 5] (booms point north)      H  main shaft headframe + cage [6, 6]
     Z  loading hopper over the track [6, 4] (track along the block's second row)    Q  foreman's shack [5, 4]
   Light pools are painted on the floor. Each kind has its own height, so wall lamps (one kind per facing), lantern
   posts and work lights may overlap one another; the maps keep posts >= 5 m and work lights >= 6 m apart. */
(function (IB) {
  'use strict';
  var SOLID = '#GE';
  function solid(grid, c, r) { return SOLID.indexOf(grid.at(c, r)) >= 0; }
  // same facing rule as zones.js buildWalls: the open side of a wall cell ('S','N','E','W', 'corner' or 'none')
  function faceOf(grid, c, r) {
    var oS = !solid(grid, c, r + 1), oN = !solid(grid, c, r - 1), oE = !solid(grid, c + 1, r), oW = !solid(grid, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  // cells u-k .. u+k along the run are all straight wall with the same facing
  function runOK(grid, c, r, F, k0, k1) {
    var along = F === 'S' || F === 'N';
    for (var d = -k0; d <= k1; d++) {
      var x = along ? c + d : c, y = along ? r : r + d;
      if (grid.at(x, y) !== '#' || faceOf(grid, x, y) !== F) return false;
    }
    return true;
  }
  function hasRig(grid) {
    if (grid._cmRig === undefined) { grid._cmRig = false; for (var c = 0; c < grid.w; c++) if (grid.at(c, 1) === 'T') grid._cmRig = true; }
    return grid._cmRig;
  }
  var ROCK = ['Rock_A', 'Rock_B', 'Rock_C'];
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = face || faceOf(grid, c, r);
    if (F === 'none' || F === 'corner') return hash(c * 7 + 1, r * 5 + 3) < 0.5 ? 'Rock_Corner_A' : 'Rock_Corner_B';
    var u = (F === 'S' || F === 'N') ? c : r;
    // overlooks on the east / west edges: 4-cell openings every 18 m with solid rock either side
    if ((c === 0 || c === grid.w - 1) && (F === 'E' || F === 'W')) {
      var m = r % 18;
      if (m >= 7 && m <= 10 && runOK(grid, c, r - (m - 7), F, 2, 5)) return 'Rock_Open';
    }
    // the coal face behind the drill rig: one long seam
    if (r === 0 && F === 'S' && hasRig(grid)) return (c % 2) ? 'Seam_A' : 'Seam_B';
    // wall lamps every 8 m on long straight runs (one pool kind per facing, so facing pools never fight)
    if (u % 8 === 4 && runOK(grid, c, r, F, 4, 4)) return 'Rock_Lamp' + F;
    if (u % 8 === 0 && runOK(grid, c, r, F, 1, 1) && hash(c * 3 + 5, r * 7 + 2) < 0.55) return 'Rock_Prop';
    if (u % 8 === 2 && runOK(grid, c, r, F, 1, 1) && hash(c * 13 + 1, r * 3 + 9) < 0.12) return 'Rock_Sign';
    // coal seams in stretches of 7 m
    var line = (F === 'S' || F === 'N') ? r : c, reg = Math.floor((u + line * 3) / 7);
    if (hash(reg * 13 + 5, line * 7 + 17) < 0.3) return (u % 2) ? 'Seam_A' : 'Seam_B';
    return ROCK[Math.min(2, Math.floor(hash(c * 5 + 1, r * 11 + 7) * 3))];
  }
  var WALLS = ['Rock_A', 'Rock_B', 'Rock_C', 'Seam_A', 'Seam_B', 'Rock_LampS', 'Rock_LampN', 'Rock_LampE', 'Rock_LampW',
    'Rock_Prop', 'Rock_Sign', 'Rock_Open', 'Rock_Corner_A', 'Rock_Corner_B'];

  IB.registerTheme({
    id: 'coalmine', name: 'Deep Coal Mine', family: 'kit-coalmine', prefix: 'KIT_COALMINE_',
    palette: ['#25242B', '#A8743F', '#FFD66B', '#54493F'],
    env: {
      // no sky underground: the roof is a dark rock ceiling; warm-brown smoky fog swallows the far end of the halls
      sky: null, clear: '#17120F', clouds: false,
      fog: { color: '#231C18', near: 18, far: 82 },
      // light from high and behind the player's usual heading: floors and robots lit, rock faces mostly in mid tone
      sun: [0.3, 0.88, 0.37],
      ceiling: { height: 9.0, color: '#2E2724', light: 'CeilRock', every: 12 }
    },
    // trodden coal-dust floor, a lighter packed-earth drift floor; the dark of the old workings outside the overlooks
    floor: { color: '#4E433B', trail: '#5A4B3F', outside: '#0F0C0B' },
    wall: { height: 9.4, roof: '#3B332E', facing: 'open', choose: chooseWall },
    symbols: {
      'Y': { size: [6, 1], pieces: ['Drift_Plain', 'Drift_Plain', 'Drift_Lamp'], kind: 'wall' },
      'y': { size: [6, 1], pieces: ['Drift_Rail', 'Drift_Rail', 'Drift_RailLamp'], kind: 'wall' },
      '-': { pieces: ['Rail'], rotate: 'run', collide: false },
      'C': { size: [1, 2], pieces: ['OreCart_Full', 'OreCart_Full', 'OreCart_Empty'], kind: 'cover' },
      'c': { pieces: ['Crate_Powder', 'Crate_Tools', 'Crate_Plain'], h: 0.9, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.65 }, kind: 'cover' },
      'u': { pieces: ['Sacks_A', 'Sacks_B'], rotate: 'random90', kind: 'cover' },
      '=': { pieces: ['Timbers_A', 'Timbers_B'], rotate: 'run', alternate: true, kind: 'cover' },
      'b': { pieces: ['Drums_A', 'Drums_B'], rotate: 'random90', kind: 'cover' },
      'O': { size: [2, 2], pieces: ['CoalHeap_A', 'CoalHeap_B'], flip: true, kind: 'cover' },
      'X': { size: [2, 2], pieces: ['Crib'], kind: 'wall' },
      'I': { pieces: ['RoofJack'], rotate: 'random90', kind: 'wall' },
      'k': { pieces: ['Conveyor_A', 'Conveyor_B'], rotate: 'run', alternate: true, kind: 'cover' },
      'l': { pieces: ['LanternPost'], rotate: 'random90', kind: 'cover' },
      'L': { pieces: ['WorkLight'], rotate: 'random90', kind: 'cover' },
      'w': { size: [2, 2], pieces: ['Puddle_A', 'Puddle_B'], flip: true, collide: false },
      'd': { size: [2, 2], pieces: ['Dust_A', 'Dust_B'], flip: true, collide: false },
      'T': { size: [8, 5], pieces: ['Landmark_DrillRig'], kind: 'wall' },
      'H': { size: [6, 6], pieces: ['Landmark_Headframe'], kind: 'wall' },
      'Z': { size: [6, 4], pieces: ['Landmark_Hopper'], kind: 'wall' },
      'Q': { size: [5, 4], pieces: ['Landmark_Shack'], kind: 'wall' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 9.4 },
    hatch: 'Hatch', stand: 'Stand',
    // the far side of the old workings (seen through the overlooks): one long slice due east, west, north and south
    backdrop: { ring: [
      { piece: 'Backdrop_Cavern', count: 4, radius: [58, 58], scale: [1, 1], squeezeX: 0.36, face: true }
    ] },
    budget: { prop: 2000, landmark: 4000, total: 70000 },
    allPieces: function () {
      var out = WALLS.concat(['CeilRock', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'Backdrop_Cavern']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        sym[ch].pieces.concat(sym[ch].stack ? [sym[ch].stack.piece] : []).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      coalmine: {
        name: 'Deep Seam',
        intro: 'Down the shaft. Clear the haulage, the coal face, then ride the cage out.',
        zones: [
          // Haulage Way: 34 robots, drones come through the drifts from the third wave
          { map: 'coalmine_haulage', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['crawler', 6], ['bomber', 2], ['gunner', 1]],
            [['crawler', 5], ['gunner', 2], ['drone', 2]],
            [['crawler', 5], ['bomber', 2]]] },
          // The Coal Face: 37 robots between conveyors and cribs
          { map: 'coalmine_face', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['drone', 2], ['crawler', 6], ['bomber', 2]],
            [['gunner', 3], ['crawler', 6]],
            [['crawler', 5], ['bomber', 2], ['drone', 2]]] },
          // Main Shaft: 40 robots, the dense finale round the headframe
          { map: 'coalmine_shaft', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['drone', 2], ['bomber', 2], ['crawler', 6]],
            [['gunner', 3], ['crawler', 6], ['drone', 1]],
            [['crawler', 5], ['bomber', 2], ['gunner', 2], ['drone', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
