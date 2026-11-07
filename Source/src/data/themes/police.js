/* Theme: Strike Team HQ (kit-police) -- a police / special-forces base.
   Painted-block rooms under strip lights: a lobby with the star emblem, a briefing room, the armory, a vehicle bay and
   a firing range. Weapon wall racks ('R') carry REAL guns: about 60 % of a rack's four mounts are filled at level
   start, each with a gun unlocked so far at a weapon tier rolled from `armory.tiers` (gray / green / blue common, purple
   very rare, orange never). Workbenches ('b') hold gun attachments and gear shelves ('g') shield cells and vests, made
   by the gear loot system at `armory.gear` odds. Look at one and press E (touch: USE) to take it.
   Built by blender/fam_kit_police.py; zone layouts by tools/police_zones.py (src/data/zones/police_*.txt).

   Symbols: R weapon rack [3,1] (turns to face the room)  b workbench [2,1]  g gear shelf [2,1]  l locker  f cabinet
            k sandbags (runs)  x ammo crate  d desk [2,1]  T briefing table [4,2]  p plant  V SWAT van [3,6]
            J holding cells [4,3]  y range booth (runs)  Y paper target  M floor emblem [4,4] */
(function (IB) {
  'use strict';
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none') return 'Corner';
    var inner = c > 0 && r > 0 && c < grid.w - 1 && r < grid.h - 1;
    if (inner) return 'Wall_A';
    var h = hash(c * 5 + 3, r * 9 + 1);
    if (h < 0.1) return 'Wall_Badge';
    if (h < 0.24) return 'Wall_Board';
    if (h < 0.4) return 'Wall_Window';
    return 'Wall_A';
  }
  // mount points in prefab-local game coordinates: [x, height, z (toward the room = +), yaw offset, kind]
  var RACK = [[-0.7, 1.55, -0.28, 0, 'gun'], [0.7, 1.55, -0.28, 0, 'gun'], [-0.7, 0.95, -0.28, 0, 'gun'], [0.7, 0.95, -0.28, 0, 'gun']];
  var BENCH = [[-0.55, 0.9, 0.05, 0, 'mod'], [0.55, 0.9, 0.05, 0, 'mod']];
  var SHELF = [[-0.5, 1.02, -0.22, 0, 'item'], [0.5, 1.02, -0.22, 0, 'item']];
  var MODS = ['extmag', 'speedmag', 'suppressor', 'compensator', 'longbarrel', 'reddot', 'laser', 'grip'].map(function (m) { return 'Mod_' + m; });
  var ITEMS = ['vest', 'medkit', 'ammobox'].map(function (m) { return 'Item_' + m; });
  var PIECES = ['Wall_A', 'Wall_Board', 'Wall_Badge', 'Wall_Window', 'Corner', 'WeaponRack', 'Workbench', 'GearShelf', 'Locker',
    'Sandbags', 'Crate', 'Desk', 'BriefTable', 'Plant', 'Cabinet', 'Booth', 'Target', 'CeilLight', 'Emblem',
    'Landmark_Van', 'Landmark_Cells', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch'];

  IB.registerTheme({
    id: 'police', name: 'Strike Team HQ', family: 'kit-police', prefix: 'KIT_POLICE_',
    palette: ['#2F4B7C', '#E8B83A', '#BFCCDD', '#C9CDD3'],
    env: {
      sky: null, clear: '#E6EAF0', fog: { color: '#E6EAF0', near: 40, far: 120 }, clouds: false,
      sun: [0.25, 0.45, 0.86],   // low light: the ceiling stays in the light band
      ceiling: { height: 4.0, color: '#EEF1F5', light: 'CeilLight', every: 4, clear: '#', clearR: 1 }
    },
    floor: {
      color: '#C9CDD3', trail: '#D3D6DB', outside: '#C9CDD3',
      lines: [{ dir: 'x', every: 2, width: 0.03, color: '#BBC0C7', y: 0.008 }, { dir: 'z', every: 2, width: 0.03, color: '#BBC0C7', y: 0.0105 }]
    },
    wall: { height: 4.0, roof: '#C2C8D0', facing: 'open', choose: chooseWall },
    symbols: {
      'R': { size: [3, 1], pieces: ['WeaponRack'], orient: 'wall', kind: 'cover', mounts: RACK, fill: 0.6 },
      'b': { size: [2, 1], pieces: ['Workbench'], flip: true, kind: 'cover', mounts: BENCH },
      'g': { size: [2, 1], pieces: ['GearShelf'], orient: 'wall', kind: 'cover', mounts: SHELF },
      'l': { pieces: ['Locker'], rotate: 'edge', kind: 'cover' },
      'f': { pieces: ['Cabinet'], rotate: 'edge', kind: 'cover' },
      'k': { pieces: ['Sandbags'], rotate: 'run', kind: 'cover' },
      'x': { pieces: ['Crate'], rotate: 'random90', h: 0.75, stack: { piece: 'Crate', chance: 0.3, h: 0.75 }, kind: 'cover' },
      'd': { size: [2, 1], pieces: ['Desk'], flip: true, kind: 'cover' },
      'T': { size: [4, 2], pieces: ['BriefTable'], kind: 'cover' },
      'p': { pieces: ['Plant'], rotate: 'random90', kind: 'cover' },
      'V': { size: [3, 6], pieces: ['Landmark_Van'], flip: true, kind: 'wall' },
      'J': { size: [4, 3], pieces: ['Landmark_Cells'], orient: 'wall', kind: 'wall' },
      'y': { pieces: ['Booth'], rotate: 'run', kind: 'cover' },
      'Y': { pieces: ['Target'], rotate: 0, kind: 'cover' },
      'M': { size: [4, 4], pieces: ['Emblem'], collide: false }
    },
    // armory odds (game.js placeLoot): rack guns by weapon tier (src/game/wdrops.js TIERS), bench / shelf gear by rarity
    armory: { tiers: { gray: 46, green: 34, blue: 19.25, purple: 0.75, orange: 0 }, gear: { common: 62, rare: 33, epic: 5, legendary: 0 } },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 4.0 },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: null,
    budget: { prop: 1200, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.concat(MODS, ITEMS); },
    levels: {
      police: {
        name: 'Strike Team HQ',
        intro: 'The armory is open: take real guns off the wall racks and fit mods at the benches (E / USE).',
        zones: [
          { map: 'police_1', waves: [[['crawler', 18], ['gunner', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['blader', 6]], [['crawler', 4], ['drone', 3], ['gunner', 4], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['soldier', 6]]] },
          { map: 'police_2', waves: [[['crawler', 19], ['gunner', 6], ['drone', 2]], [['crawler', 5], ['bomber', 5], ['gunner', 5], ['blader', 6]], [['crawler', 5], ['drone', 4], ['gunner', 5], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['blader', 5]]] },
          { map: 'police_3', waves: [[['crawler', 19], ['gunner', 8]], [['crawler', 5], ['bomber', 5], ['drone', 4], ['soldier', 6]], [['crawler', 7], ['gunner', 7], ['drone', 4], ['blader', 6]], [['crawler', 7], ['gunner', 8], ['bomber', 7], ['drone', 3], ['soldier', 11]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
