/* Theme: Glimmerdeep Colliery (kit-gemmine). A working coal mine whose No. 3 Seam broke into a cavern of gems.
   Zone 1, No. 3 Seam: a room-and-pillar coal district under a 9 m rock roof. The haulage gallery runs from the entry
   to the exit between two lines of coal pillars under steel arch sets every 4 m, with two tracks and ore carts; the
   ore chute stands over the east track, fed by the raised conveyor catwalk (a belt at 3 m with a walkway and stairs at
   both ends) from the north-east coal face; the haulage winch house, the auxiliary fan with its riser and vent duct,
   lamp strings across the gallery, timbered drifts through the big pillars, roof jacks, cribs, coal heaps; the first
   gem veins glint in the coal faces.
   Zone 2, the Glimmer Vault: a vast natural cavern (walls to 18.4 m, a rock roof with stalactites and hanging
   crystals at 18 m). Giant faceted crystals (diamond, ruby, emerald, sapphire) glow in the dark (theme.glow); the Gem
   Heart in the middle with its scaffold, mining galleries at 4.8 m along the west and north walls, timber platforms at
   2.4 m, rock ledges with ramps at 1.4 m, crystal spires, clusters and clumps, the chasm along the east wall (a
   railing, the hoist at its lip, the far cliff beyond: backdrop.build), the sorting and cutting station on plank
   decking with a track from the entry. Robots climb every stair and ramp (walkable boxes: a layered nav grid).
   Built by blender/fam_kit_gemmine.py (gem_base / gem_seam / gem_cavern.py; the coal mine kit's helpers are imported);
   zone layers by tools/gemmine_zones.py (src/data/zones/gemmine_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  rock: zone 1 coal-mine faces (strata, coal seams, gem veins, lamps on brackets, props, signs, a lamp string);
        zone 2 tall cavern faces (veins, crystal clusters, lanterns) and the chasm edge; corners get all-round lumps
     Y  timbered drift [6, 1] (posts, cap, lagging, plank bulkhead to the roof): runs of Y across a 6 m gap make a tunnel
     A  steel arch set over the 12 m haulage gallery [12, 1] (legs collide, the gallery stays open under it)
     C  ore cart on its rails [1, 2] (coal, empty, or coal with rough gems)
     c  powder / tool crates (stacked)   u  sacks   =  stacked timbers (runs)   b  oil drums   I  roof jack
     O  coal heap [2, 2]   X  timber crib with a roof post [2, 2]   k  belt conveyor (runs)   l  lantern post
     L  work light on a tripod   w  puddle [2, 2]   d  coal dust [2, 2] (no collision)
     Z  ore chute and bin over the east track [10, 8] (track along local x -3.5; the feed belt rises from its east edge)
     B  raised conveyor catwalk [20, 3] (belt at 3 m along the back row, walkway deck along the front, stairs at both
        ends, the belt's incline down to the face conveyor past the east end)
     W  haulage winch house [6, 5] (open to the track; turns its back to the wall)
     F  auxiliary fan [4, 2] against a wall (its riser meets the "@layer 9" vent duct on the cell beyond the block's end)
     H  the Gem Heart [12, 12] (giant crystals on a mound, scaffold deck at 2.4 m on the south flank, stair east)
     N  mining gallery [16, 4] against a wall (deck at 4.8 m, stairs down to both ends, rails)
     M  timber platform [6, 4] (deck at 2.4 m, a stair along its front)   R  rock ledge [8, 4] (1.4 m, plank ramp)
     Q  crystal cluster [2, 2] (ruby, emerald, sapphire, diamond)   q  low crystal clump   V  crystal spire [3, 3]
     D  rock stalagmite [2, 2]
     J  sieve / jig [2, 2]   K  lapidary saw bench [2, 1]   T  lit sorting table [2, 1]   x  crate of rough gems (stacked)
     U  hoist at the chasm lip [4, 4] (back to the chasm: its jib and bucket hang out over the drop)
   "@layer 0" (no walls): -  rail (runs)   p  plank decking [2, 2]; on wall cells the wall codes the chooser reads:
     zone 1: 1 2 3 4 a ruby / emerald / sapphire / diamond vein in the coal, 8 a plain coal seam, 5 6 7 signs (seam,
     haulage, gem vein); zone 2: 1 2 3 4 vein modules, 9 the chasm edge (railing; lamp and sign variants by row)
   "@layer 9" (zone 1, hanging from the roof): v  vent duct (runs)   ~  lamp string (runs, a bulb a metre)
   "@layer 18" (zone 2, no theme ceiling there): r  cavern roof [10, 12]
   Light pools are painted on the floor. Each kind has its own height, so wall lamps (one kind per facing), lantern
   posts, work lights and the prefabs' pools may overlap one another; the maps keep posts >= 5 m apart. */
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
  // cells u-k0 .. u+k1 along the run are all straight wall with the same facing and no wall code
  function runOK(grid, c, r, F, k0, k1) {
    var along = F === 'S' || F === 'N';
    for (var d = -k0; d <= k1; d++) {
      var x = along ? c + d : c, y = along ? r : r + d;
      if (grid.at(x, y) !== '#' || faceOf(grid, x, y) !== F || codeAt(grid, x, y) !== '.') return false;
    }
    return true;
  }
  function layerAt(grid, test) {
    var L = grid.layers || [];
    for (var i = 0; i < L.length; i++) if (test(L[i].y)) return L[i];
    return null;
  }
  // zone 2 is the zone with the roof grid (no theme ceiling there)
  function isCave(grid) {
    if (grid._gmCave === undefined) grid._gmCave = !!layerAt(grid, function (y) { return y > 12; });
    return grid._gmCave;
  }
  function codeAt(grid, c, r) {
    if (grid._gmL0 === undefined) grid._gmL0 = layerAt(grid, function (y) { return y < 1; });
    return grid._gmL0 ? grid._gmL0.at(c, r) : '.';
  }
  var GEM = { '1': 'Ruby', '2': 'Emer', '3': 'Saph', '4': 'Dia' };
  var ROCK = ['Rock_A', 'Rock_B', 'Rock_C'], CAVE = ['Cave_A', 'Cave_B', 'Cave_C'];
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = face || faceOf(grid, c, r), code = codeAt(grid, c, r), u = (F === 'S' || F === 'N') ? c : r;
    if (isCave(grid)) {
      if (code === '9') {
        if (F === 'none' || F === 'corner') return 'Cave_Corner_A';
        return u % 12 === 6 ? 'Chasm_Sign' : u % 6 === 3 ? 'Chasm_Lamp' : (u % 2 ? 'Chasm' : 'Chasm_B');
      }
      // the ends of the chasm edge: all-round rock lumps (the tall faces never end in a flat cut)
      if (codeAt(grid, c, r - 1) === '9' || codeAt(grid, c, r + 1) === '9' || codeAt(grid, c - 1, r) === '9' || codeAt(grid, c + 1, r) === '9') return 'Cave_Corner_B';
      if (F === 'none' || F === 'corner') return hash(c * 7 + 1, r * 5 + 3) < 0.5 ? 'Cave_Corner_A' : 'Cave_Corner_B';
      if (GEM[code]) return 'Cave_' + GEM[code];
      if (u % 8 === 4 && runOK(grid, c, r, F, 3, 3)) return 'Cave_Lamp' + F;
      var hv = hash(c * 11 + 3, r * 17 + 5);
      if (hv < 0.14) return 'Cave_' + ['Ruby', 'Emer', 'Saph', 'Dia'][Math.floor(hv / 0.035)];
      return CAVE[Math.min(2, Math.floor(hash(c * 5 + 1, r * 11 + 7) * 3))];
    }
    if (F === 'none' || F === 'corner') return hash(c * 7 + 1, r * 5 + 3) < 0.5 ? 'Rock_Corner_A' : 'Rock_Corner_B';
    if (GEM[code]) return 'Gem_' + GEM[code];
    if (code === '8') return (u % 2) ? 'Seam_A' : 'Seam_B';
    if (code === '5') return 'Sign_Seam';
    if (code === '6') return 'Sign_Haul';
    if (code === '7') return 'Sign_Gem';
    // wall lamps every 8 m on long straight runs (one pool kind per facing, so facing pools never fight)
    if (u % 8 === 4 && runOK(grid, c, r, F, 4, 4)) return 'Rock_Lamp' + F;
    if (u % 8 === 0 && runOK(grid, c, r, F, 1, 1) && hash(c * 3 + 5, r * 7 + 2) < 0.55) return 'Rock_Prop';
    // coal seams in stretches of 7 m, now and then a glint of gems in them
    var line = (F === 'S' || F === 'N') ? r : c, reg = Math.floor((u + line * 3) / 7);
    if (hash(reg * 13 + 5, line * 7 + 17) < 0.3) {
      var g = hash(c * 19 + 7, r * 23 + 1);
      return g < 0.12 ? 'Gem_' + ['Ruby', 'Emer', 'Saph', 'Dia'][Math.floor(g / 0.03)] : ((u % 2) ? 'Seam_A' : 'Seam_B');
    }
    return ROCK[Math.min(2, Math.floor(hash(c * 5 + 1, r * 11 + 7) * 3))];
  }
  var WALLS = ['Rock_A', 'Rock_B', 'Rock_C', 'Seam_A', 'Seam_B', 'Gem_Ruby', 'Gem_Emer', 'Gem_Saph', 'Gem_Dia',
    'Rock_LampS', 'Rock_LampN', 'Rock_LampE', 'Rock_LampW', 'Rock_Prop', 'Sign_Seam', 'Sign_Haul', 'Sign_Gem',
    'Rock_Corner_A', 'Rock_Corner_B', 'Cave_A', 'Cave_B', 'Cave_C', 'Cave_Ruby', 'Cave_Emer', 'Cave_Saph', 'Cave_Dia',
    'Cave_LampS', 'Cave_LampN', 'Cave_LampE', 'Cave_LampW', 'Cave_Corner_A', 'Cave_Corner_B', 'Chasm', 'Chasm_B',
    'Chasm_Sign', 'Chasm_Lamp'];

  var R90 = Math.PI / 2;
  var SYMBOLS = {
    // ---- zone 1: the coal seam
    'Y': { size: [6, 1], pieces: ['Drift_Plain', 'Drift_Plain', 'Drift_Lamp'], kind: 'wall' },
    'A': { size: [12, 1], pieces: ['Arch', 'Arch', 'Arch_Lamp'], sequence: true, face: 0, kind: 'cover' },
    'C': { size: [1, 2], pieces: ['OreCart_Full', 'OreCart_Gem', 'OreCart_Empty'], kind: 'cover' },
    'c': { pieces: ['Crate_Powder', 'Crate_Tools', 'Crate_Plain'], h: 0.9, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.65 }, kind: 'cover' },
    'u': { pieces: ['Sacks'], rotate: 'random90', kind: 'cover' },
    '=': { pieces: ['Timbers'], rotate: 'run', kind: 'cover' },
    'b': { pieces: ['Drums'], rotate: 'random90', kind: 'cover' },
    'O': { size: [2, 2], pieces: ['CoalHeap_A', 'CoalHeap_B'], flip: true, kind: 'cover' },
    'X': { size: [2, 2], pieces: ['Crib'], kind: 'wall' },
    'I': { pieces: ['RoofJack'], rotate: 'random90', kind: 'wall' },
    'k': { pieces: ['Conveyor_A', 'Conveyor_B'], rotate: 'run', alternate: true, kind: 'cover' },
    'l': { pieces: ['LanternPost'], rotate: 'random90', kind: 'cover' },
    'L': { pieces: ['WorkLight'], rotate: 'random90', kind: 'cover' },
    'w': { size: [2, 2], pieces: ['Puddle_A', 'Puddle_B'], flip: true, collide: false },
    'd': { size: [2, 2], pieces: ['Dust_A', 'Dust_B'], flip: true, collide: false },
    'Z': { size: [10, 8], pieces: ['Landmark_Chute'], face: 0, kind: 'wall' },
    'B': { size: [20, 3], pieces: ['Landmark_BeltBridge'], face: 0, kind: 'wall' },
    'W': { size: [6, 5], pieces: ['Landmark_Winch'], orient: 'wall', kind: 'wall' },
    'F': { size: [4, 2], pieces: ['FanUnit'], orient: 'wall', kind: 'wall' },
    // ---- zone 2: the cavern
    'H': { size: [12, 12], pieces: ['Landmark_GemHeart'], face: 0, kind: 'wall' },
    'N': { size: [16, 4], pieces: ['Landmark_Gallery'], orient: 'wall', kind: 'wall' },
    'M': { size: [6, 4], pieces: ['Platform'], flip: true, kind: 'wall' },
    'R': { size: [8, 4], pieces: ['Ledge'], flip: true, kind: 'wall' },
    'Q': { size: [2, 2], pieces: ['Crystal_Ruby', 'Crystal_Emer', 'Crystal_Saph', 'Crystal_Dia'], flip: true, kind: 'cover' },
    'q': { pieces: ['Clump_A', 'Clump_B'], rotate: 'random90', kind: 'cover' },
    'V': { size: [3, 3], pieces: ['Spire_A', 'Spire_B'], flip: true, kind: 'wall' },
    'D': { size: [2, 2], pieces: ['Stalagmite_A', 'Stalagmite_B'], flip: true, kind: 'wall' },
    'J': { size: [2, 2], pieces: ['Sieve'], flip: true, kind: 'cover' },
    'K': { size: [2, 1], pieces: ['CutBench'], flip: true, kind: 'cover' },
    'T': { size: [2, 1], pieces: ['WorkTable_A', 'WorkTable_B'], flip: true, kind: 'cover' },
    'x': { pieces: ['GemCrate_A', 'GemCrate_B'], h: 0.62, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.25, h: 0.65 }, kind: 'cover' },
    'U': { size: [4, 4], pieces: ['Landmark_Hoist'], orient: 'wall', kind: 'wall' },
    // ---- "@layer 0": rails, decking
    '-': { pieces: ['Rail'], rotate: 'run', collide: false },
    'p': { size: [2, 2], pieces: ['Planks_A', 'Planks_B'], collide: false },
    // ---- "@layer 9": roof fittings (zone 1); "@layer 18": the cavern roof (zone 2)
    'v': { pieces: ['VentDuct'], rotate: 'run', collide: false },
    '~': { pieces: ['LampString_A', 'LampString_B'], rotate: 'run', alternate: true, collide: false },
    'r': { size: [10, 12], pieces: ['CaveRoof_A', 'CaveRoof_B', 'CaveRoof_C'], flip: true, collide: false }
  };

  // glow companions (zones.js theme.glow): every piece with gems, bulbs, lantern glass or lenses has a <Piece>_Glow
  // drawn unlit (its ink outline stays in the piece itself)
  var GLOWING = ['Rock_A', 'Seam_A', 'Gem_Ruby', 'Gem_Emer', 'Gem_Saph', 'Gem_Dia', 'Rock_LampS', 'Rock_LampN', 'Rock_LampE',
    'Rock_LampW', 'Rock_Prop', 'LampString_A', 'LanternPost', 'OreCart_Gem', 'Drift_Lamp', 'Arch_Lamp',
    'Landmark_Chute', 'Landmark_BeltBridge', 'Landmark_Winch', 'FanUnit', 'Cave_Ruby', 'Cave_Emer', 'Cave_Saph', 'Cave_Dia',
    'Cave_LampS', 'Cave_LampN', 'Cave_LampE', 'Cave_LampW', 'Chasm_Lamp', 'CaveRoof_A', 'CaveRoof_B', 'CaveRoof_C',
    'Crystal_Ruby', 'Crystal_Emer', 'Crystal_Saph', 'Crystal_Dia', 'Clump_A', 'Clump_B', 'Spire_A', 'Spire_B', 'Stalagmite_A', 'Stalagmite_B',
    'Landmark_GemHeart', 'Landmark_Gallery', 'Platform', 'Ledge', 'Sieve', 'CutBench', 'WorkTable_A', 'WorkTable_B',
    'GemCrate_A', 'GemCrate_B', 'Landmark_Hoist'];
  var GLOW = {};
  GLOWING.forEach(function (n) { GLOW[n] = { piece: n + '_Glow' }; });

  /* backdrop.build: the chasm beyond zone 2's east edge (the far cliff, its end walls, glowing veins); there is no
     flat outside plane (nothing outside the zones is ever seen but the chasm) */
  var CHASM = { rows: [18, 51] };
  function backdrop(level, api) {
    var Z = level.zones[1];
    if (!Z) return;
    var x = Z.ox + Z.w, z = Z.oz + (CHASM.rows[0] + CHASM.rows[1] + 1) / 2, gn = 'KIT_GEMMINE_Backdrop_Chasm_Glow';
    api.add('Backdrop_Chasm', x, 0, z, 0, 1);
    // its veins drawn unlit like every other glow (backdrop pieces get no glow companions of their own)
    if (typeof THREE !== 'undefined' && IB.Assets && IB.Assets.geo && IB.Assets.geo[gn]) {
      var m = new THREE.Mesh(IB.Assets.get(gn), new THREE.MeshBasicMaterial({ map: IB.Assets.mat['kit-gemmine'].map }));
      m.position.set(x, 0, z);
      level.root.add(m);
    }
  }

  var PIECES = WALLS.concat(['CeilRock', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'Backdrop_Chasm', 'Backdrop_Chasm_Glow']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    d.pieces.concat(d.stack ? [d.stack.piece] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { if (PIECES.indexOf(GLOW[k].piece) < 0) PIECES.push(GLOW[k].piece); });

  IB.registerTheme({
    id: 'gemmine', name: 'Glimmerdeep Colliery', family: 'kit-gemmine', prefix: 'KIT_GEMMINE_',
    palette: ['#25242B', '#A8743F', '#E3264B', '#1FC46C'],
    env: {
      // no sky underground: a dark rock roof over the seam (the cavern brings its own); violet-brown smoky fog
      sky: null, clear: '#120F14', clouds: false,
      fog: { color: '#1E1820', near: 20, far: 92 },
      sun: [0.3, 0.88, 0.37],
      ceiling: { height: 9.0, color: '#2E2724', light: 'CeilRock', every: 16, clear: 'XIZFB#', clearR: 1 }
    },
    floor: { color: '#4A413C', trail: '#5A4B3F', outside: '#0F0C0B' },
    wall: { height: 9.4, roof: '#3B332E', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 9.4, end: 'Rock_B', endYaw: 0 },   // the hatch room's back wall: a plain face module
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: backdrop },
    budget: { prop: 3200, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      gemmine: {
        name: 'Glimmerdeep Colliery',
        intro: 'No. 3 Seam broke into a cavern of gems. Clear the haulage, then the Glimmer Vault, and ride the cage out.',
        zones: [
          // No. 3 Seam: the haulage gallery, the chute and the catwalk, the coal faces
          { map: 'gemmine_1', waves: [
            [['crawler', 20], ['gunner', 12]],
            [['crawler', 9], ['bomber', 2], ['gunner', 7], ['drone', 4], ['soldier', 5], ['blader', 3]],
            [['crawler', 8], ['drone', 6], ['gunner', 8], ['soldier', 6], ['blader', 2]],
            [['crawler', 8], ['bomber', 2], ['gunner', 8], ['drone', 4], ['blader', 3], ['soldier', 5]],
            [['crawler', 8], ['gunner', 10], ['drone', 4], ['soldier', 4], ['blader', 2]]] },
          // the Glimmer Vault: the Gem Heart, the galleries and platforms, the chasm, the sorting station
          { map: 'gemmine_2', ceiling: false, waves: [
            [['crawler', 18], ['gunner', 10], ['drone', 4]],
            [['crawler', 9], ['bomber', 2], ['gunner', 7], ['drone', 4], ['blader', 3], ['soldier', 5]],
            [['crawler', 8], ['drone', 6], ['gunner', 8], ['soldier', 6], ['blader', 2]],
            [['crawler', 8], ['bomber', 2], ['gunner', 8], ['drone', 4], ['soldier', 5], ['blader', 3]],
            [['crawler', 8], ['bomber', 2], ['gunner', 10], ['drone', 4], ['soldier', 4], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
