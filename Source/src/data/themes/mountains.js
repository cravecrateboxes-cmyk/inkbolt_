/* Theme: Mountains (kit-mountains) -- campaign level 1, "Pine Ridge".
   An alpine valley chain: slate-blue cliff ridges with snow ledges, snowy pines and spruce stands, a log cabin,
   an A-frame chalet, a fire-lookout tower, a rope bridge over a frozen gorge and a ski lift, under a crisp pale-blue
   sky with misty blue-white depth fog and a ring of snow-capped peaks. Built by blender/fam_kit_mountains.py; zone
   layouts by tools/mountains_zones.py (src/data/zones/mountains_*.txt).

   Cliff wall modules ('#') are pre-rotated per facing: Cliff_<S|N|E|W>_<a><b>, rock face toward the open side.
   a/b are ridge height levels (0..3 = 6.2 / 7.4 / 8.6 / 9.8 m) at the module's two edges, west/east for S|N and
   north/south for E|W. The levels come from smooth functions of the edge position, so neighbouring modules share
   their edge height and the skyline runs on as one jagged ridge. Corners, notches and gate jambs get rock spires. */
(function (IB) {
  'use strict';
  var SOLID = '#GE';
  function solid(grid, c, r) { return SOLID.indexOf(grid.at(c, r)) >= 0; }
  function clampLv(v) { return Math.max(0, Math.min(3, Math.round(v))); }
  // ridge level at a module edge: x = vertical edge line of a horizontal wall in row r; z = horizontal edge of a
  // vertical wall in column c. Slopes stay under one level per metre, so neighbours never step more than one level.
  function lvX(x, r) { return clampLv(1.5 + 1.05 * Math.sin(0.37 * x + 2.1 * r + 0.5) + 0.55 * Math.sin(0.93 * x + 1.3 * r + 2.0)); }
  function lvZ(c, z) { return clampLv(1.5 + 1.05 * Math.sin(0.41 * z + 1.7 * c + 1.1) + 0.5 * Math.sin(0.87 * z + 0.9 * c + 0.3)); }
  var PILLARS = ['Cliff_Pillar_A', 'Cliff_Pillar_B', 'Cliff_Pillar_C'];
  var FACINGS = ['S', 'N', 'E', 'W'];
  function cliffNames() {
    var out = [];
    FACINGS.forEach(function (F) {
      for (var a = 0; a < 4; a++) for (var b = 0; b < 4; b++) {
        if (Math.abs(a - b) > 1) continue;
        out.push('Cliff_' + F + '_' + a + b);
        if (a === b) out.push('Cliff_' + F + '_' + a + b + 'b');
      }
    });
    return out.concat(PILLARS);
  }
  function chooseWall(c, r, horiz, corner, hash, grid) {
    var oN = !solid(grid, c, r - 1), oS = !solid(grid, c, r + 1), oW = !solid(grid, c - 1, r), oE = !solid(grid, c + 1, r);
    if (oN + oS + oW + oE === 1) {     // straight run: horiz is always true here, so the engine leaves the yaw at 0
      var a, b, F;
      if (oS || oN) { a = lvX(c, r); b = lvX(c + 1, r); F = oS ? 'S' : 'N'; }
      else { a = lvZ(c, r); b = lvZ(c, r + 1); F = oE ? 'E' : 'W'; }
      return 'Cliff_' + F + '_' + a + b + (a === b && hash(c * 7 + 3, r * 5 + 1) < 0.35 ? 'b' : '');
    }
    return PILLARS[Math.min(2, Math.floor(hash(c * 11 + 1, r * 13 + 2) * 3))];   // corners, notches, gate jambs
  }

  var ROCKS = ['Boulder_A', 'Boulder_B', 'Boulder_C'];
  var OTHER = ['Treeline_A', 'Treeline_B', 'Outcrop_A', 'Outcrop_B', 'StoneWall_A', 'StoneWall_B', 'Fence', 'LogPile',
    'Crate', 'Bundle', 'Pine_A', 'Pine_B', 'Pine_C', 'SpruceCluster_A', 'SpruceCluster_B', 'Drift_A', 'Drift_B',
    'Meadow_A', 'Meadow_B', 'Pond', 'Creek', 'Signpost', 'LanternPost', 'Skis', 'Campfire',
    'Landmark_Cabin', 'Landmark_Chalet', 'Landmark_Lookout', 'Landmark_RopeBridge', 'Landmark_LiftStation', 'Landmark_LiftLine',
    'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Wood', 'TrailWall_Lantern', 'TrailWall_Drift', 'Hatch',
    'Backdrop_PeakA', 'Backdrop_PeakB', 'Backdrop_PeakC', 'Backdrop_Forest'];

  IB.registerTheme({
    id: 'mountains', name: 'Mountains', family: 'kit-mountains', prefix: 'KIT_MOUNTAINS_',
    // brief section 6 palette: sky blue, pine green, tangerine accent, snow-cream ground
    palette: ['#7AA7E0', '#3F8F6A', '#FF8A3D', '#E8E2D2'],
    // crisp pale-blue sky; misty blue-white fog turns the far peaks into flat pale silhouettes (aerial perspective)
    env: { sky: ['#82C1F0', '#F2F7FC'], fog: { color: '#CCDDEE', near: 42, far: 120 }, sun: [0.5, 0.8, 0.35], clouds: true, ceiling: null },
    // packed snow ground, a trodden earth trail between zones, snowfields outside
    floor: { color: '#E1E8EE', trail: '#CDBDA3', outside: '#D9E3EC' },
    wall: { height: 6, roof: '#EEF3F8', faceOpen: false, choose: chooseWall },
    symbols: {
      '%': { size: [2, 2], pieces: ['Treeline_A', 'Treeline_B'], kind: 'wall' },
      'o': { pieces: ROCKS, rotate: 'random90', kind: 'cover' },
      'O': { size: [2, 2], pieces: ['Outcrop_A', 'Outcrop_B'], flip: true, kind: 'cover' },
      '=': { pieces: ['StoneWall_A', 'StoneWall_B'], rotate: 'run', alternate: true, kind: 'cover' },
      'f': { pieces: ['Fence'], rotate: 'run', kind: 'cover' },
      'x': { pieces: ['LogPile'], rotate: 'run', kind: 'cover' },
      'c': { pieces: ['Crate'], rotate: 'random90', h: 1, stack: { piece: 'Bundle', chance: 0.3, h: 0.62 }, kind: 'cover' },
      't': { pieces: ['Pine_A', 'Pine_B', 'Pine_C'], rotate: 'random90', kind: 'cover' },
      'F': { size: [2, 2], pieces: ['SpruceCluster_A', 'SpruceCluster_B'], flip: true, kind: 'cover' },
      'H': { size: [6, 5], pieces: ['Landmark_Cabin'], kind: 'wall' },
      'A': { size: [5, 6], pieces: ['Landmark_Chalet'], kind: 'wall' },
      'T': { size: [4, 4], pieces: ['Landmark_Lookout'], kind: 'wall' },
      'Y': { size: [14, 4], pieces: ['Landmark_RopeBridge'], kind: 'wall' },
      'J': { size: [5, 4], pieces: ['Landmark_LiftStation'], kind: 'wall' },
      'K': { size: [3, 12], pieces: ['Landmark_LiftLine'], kind: 'wall' },
      'Q': { size: [3, 3], pieces: ['Campfire'], kind: 'cover' },
      'D': { size: [3, 3], pieces: ['Drift_A', 'Drift_B'], collide: false, flip: true },
      'M': { size: [3, 3], pieces: ['Meadow_A', 'Meadow_B'], collide: false, flip: true },
      'W': { size: [4, 4], pieces: ['Pond'], collide: false, flip: true },
      'w': { size: [2, 2], pieces: ['Creek'], collide: false },
      'p': { pieces: ['Signpost', 'LanternPost'], sequence: true, kind: 'deco' },
      'k': { pieces: ['Skis'], rotate: 'random90', kind: 'deco' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // log palisade; firewood, a lantern and a snow drift with skis mixed in per module
    trail: { wall: 'TrailWall', height: 2.6, variants: ['TrailWall', 'TrailWall_Wood', 'TrailWall_Lantern', 'TrailWall_Drift'] },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: { ring: [
      // big snow-capped peaks, far enough out to read as misty silhouettes above the cliff line
      { piece: 'Backdrop_PeakC', count: 4, radius: [74, 96], scale: [1.1, 1.5], squeezeX: 0.9, face: true },
      { piece: 'Backdrop_PeakA', count: 4, radius: [66, 90], scale: [1.0, 1.4], squeezeX: 0.86, face: true },
      { piece: 'Backdrop_PeakB', count: 5, radius: [60, 84], scale: [0.95, 1.35], squeezeX: 0.82, face: true },
      // pine forest on snowy knolls just outside the valley (seen over the treelines, the gates and the exit path)
      { piece: 'Backdrop_Forest', count: 20, radius: [26, 40], scale: [0.95, 1.3], squeezeX: 0.5, face: true }
    ] },
    budget: { prop: 2500, landmark: 5000, total: 60000 },
    allPieces: function () { return cliffNames().concat(ROCKS, OTHER); },
    levels: {
      mountains: {
        name: 'Pine Ridge',
        intro: 'Robots have overrun the ridge trail. Clear each valley to open its gate.',
        zones: [
          // Trailhead Meadow: a gentle first wave, Gunners join from the second wave
          { map: 'mountains_1', waves: [[['crawler', 7]], [['crawler', 7], ['gunner', 1]], [['crawler', 8], ['gunner', 2]]] },
          // Gorge Crossing: three ways past the rope-bridge towers
          { map: 'mountains_2', waves: [[['crawler', 7], ['gunner', 1]], [['crawler', 7], ['gunner', 2]], [['crawler', 7], ['gunner', 2]]] },
          // Summit Lift: the first Drones over the lift line, a pair of Bombers at the very end
          { map: 'mountains_3', waves: [[['crawler', 6], ['drone', 1]], [['crawler', 5], ['gunner', 2]], [['crawler', 4], ['gunner', 1], ['drone', 1], ['bomber', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
