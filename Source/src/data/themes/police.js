/* Theme: Strike Team HQ (kit-police) -- a police / special-forces base.
   Rooms with their own finish: a lobby (navy wainscot, gold rail, two-tone tiles, the star emblem, the front desk),
   a briefing room (oak panelling, carpet, projector screen, rows of seats), armories (slate block walls, rubber floor,
   steel gun walls, workbenches, gear shelving), an operations room (console walls, desk pods), a locker room, a
   firing range (acoustic panels, booths, robot-silhouette targets, backstop, baffles) and a vehicle garage (block
   walls, roller doors, bay lines, SWAT vans, holding cells, tool chests, drums and tyres).
   Weapon walls ('R') carry REAL guns: about 60 % of a wall's four slots are filled at level start, each with a gun
   unlocked so far at a weapon tier rolled from `armory.tiers` (gray / green / blue common, purple very rare, orange
   never). Workbenches ('b') hold gun attachments and gear shelves ('g') shield cells and vests, made by the gear loot
   system at `armory.gear` odds. Look at one and press E (touch: USE) to take it.
   Built by blender/fam_kit_police.py; zone layouts by tools/police_zones.py (src/data/zones/police_*.txt).

   A zone file has three grids: the floor plan, "@layer 0.008" (floor finishes; on wall cells, wall-art codes) and
   "@layer 4" (ceiling structure and lamps, hanging from the 4 m ceiling).
   Floor plan:  R weapon wall [3,1] (turns to face the room)  b workbench [2,1]  g gear shelf [2,1]  l locker
     f filing cabinet  k sandbags (runs)  x crate / ammo cans  K desk pod [2,2]  T briefing row [4,2] (faces north)
     U lectern  p plant  B waiting bench [2,1]  o vending / water cooler  H gear stand  z tool chest  t drums / tyres
     X pallet [2,2]  D ops console [4,1]  Q front desk [6,2]  V SWAT van [3,6]  J holding cell [4,3]
     y range booth [3,2] (counter to the north)  Y target
   Floor layer: 1 lobby tile  2 carpet  3 armory rubber  4 garage concrete  5 range  6 pale tile  7 entry mat
     / hazard stripes  ^ firing line  , lane line  - | garage line (X / Z)  _ : armory line (X / Z)  M emblem [4,4]
     Wall-art codes (on wall cells): w window  v projector screen (runs)  F flag  W whiteboard  m map  n notice board
     e badge  c clock  u door  s sign  C cage window  A first aid  Z extinguisher  r roller door (runs)  O tool board
     I panel / warning light  K backstop
   Ceiling layer: i panel light  j high-bay lamp  = ! + beam (X / Z / crossing)  ~ ; duct (X / Z)  * baffle
     [ ] doorway lintel (X / Z)
   The wall chooser styles each module from the floor finish in front of it (lobby, office, armory, garage, range,
   cells), turns the art code on the cell into that style's piece and splits runs (screen, roller door) into
   left end / middle / right end parts. */
(function (IB) {
  'use strict';
  var FSTYLE = { '1': 'L', '7': 'L', 'M': 'L', '2': 'O', '3': 'A', '_': 'A', ':': 'A', '4': 'G', '-': 'G', '|': 'G',
    '5': 'R', '^': 'R', ',': 'R', '6': 'C' };
  var ART = {
    L: { w: 'WL_Window', e: 'WL_Badge', n: 'WL_Board', c: 'WL_Clock', F: 'WL_Flag', u: 'WL_Door', s: 'WL_Sign' },
    O: { w: 'WO_Window', W: 'WO_White', m: 'WO_Map', c: 'WO_Clock', F: 'WO_Flag', n: 'WO_Board', u: 'WO_Door', v: 'WO_Screen' },
    A: { s: 'WA_Sign', C: 'WA_Cage', A: 'WA_Aid', Z: 'WA_Ext', u: 'WA_Door', n: 'WA_Board' },
    G: { r: 'WG_Roller', O: 'WG_Tools', I: 'WG_Panel', Z: 'WG_Ext', w: 'WG_Window', s: 'WG_Sign', n: 'WG_Board' },
    R: { K: 'WR_Back', s: 'WR_Sign', I: 'WR_Light', w: 'WR_Window' },
    C: { s: 'WC_Sign', n: 'WC_Board', c: 'WC_Clock', u: 'WC_Door' }
  };
  var RUNS = { WO_Screen: 1, WG_Roller: 1 };   // drawn over several modules: L / M / R parts
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };   // the module's local -X neighbour (yaw per face)
  var NB = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]];
  function floorOf(grid) {
    if (grid._polF === undefined) {
      grid._polF = null;
      (grid.layers || []).forEach(function (l) { if (!grid._polF && l.y < 1) grid._polF = l; });
    }
    return grid._polF;
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = floorOf(grid), S = '', k;
    if (face === 'corner' || face === 'none' || !FACE[face]) {
      for (k = 0; F && k < NB.length && !S; k++) S = FSTYLE[F.at(c + NB[k][0], r + NB[k][1])] || '';
      return 'Corner' + (S || 'L');
    }
    if (!F) return 'WL';
    var d = FACE[face];
    for (k = 1; k <= 4 && !S; k++) S = FSTYLE[F.at(c + d[0] * k, r + d[1] * k)] || '';
    S = S || 'L';
    var code = F.at(c, r), piece = ART[S][code];
    if (!piece) return 'W' + S;
    if (RUNS[piece]) {
      var L = LEFT[face], hasL = F.at(c + L[0], r + L[1]) === code, hasR = F.at(c - L[0], r - L[1]) === code;
      return piece + (!hasL ? 'L' : !hasR ? 'R' : 'M');
    }
    return piece;
  }
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }

  // mount points in prefab-local game coordinates: [x, height, z (toward the room = +), yaw offset, kind, options]
  //   guns: the gun's back rests on the mount plane (back: true), 3.5 cm in front of the rack board, scaled to fit
  //   len x h, centred on (x, height); tag: the tier / rarity plate's offset from the mount (on the slot's label,
  //   the bench's front edge, the shelf's lip)
  var GUN = { back: true, len: 1.0, h: 0.34, tag: [0, -0.26, -0.016] };
  var RACK = [[-0.72, 1.05, -0.415, 0, 'gun', GUN], [0.72, 1.05, -0.415, 0, 'gun', GUN],
    [-0.72, 1.75, -0.415, 0, 'gun', GUN], [0.72, 1.75, -0.415, 0, 'gun', GUN]];
  var BENCH = [[-0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }], [0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }]];
  var SHELF = [[-0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }], [0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }]];
  var SYMBOLS = {
    // ---- floor plan
    'R': { size: [3, 1], pieces: ['WeaponRack'], orient: 'wall', kind: 'cover', mounts: RACK, fill: 0.6 },
    'b': { size: [2, 1], pieces: ['Workbench'], flip: true, kind: 'cover', mounts: BENCH },
    'g': { size: [2, 1], pieces: ['GearShelf'], orient: 'wall', kind: 'cover', mounts: SHELF },
    'l': { pieces: ['Locker', 'Locker', 'Locker_B'], rotate: 'edge', kind: 'cover' },
    'f': { pieces: ['Cabinet'], rotate: 'edge', kind: 'cover' },
    'k': { pieces: ['Sandbags'], rotate: 'run', kind: 'cover' },
    'x': { pieces: ['Crate', 'Crate_W', 'AmmoCans'], rotate: 'random90', h: 0.75, stack: { piece: 'Crate', chance: 0.3, h: 0.75 }, kind: 'cover' },
    'K': { size: [2, 2], pieces: ['DeskPod'], flip: true, kind: 'cover' },
    'T': { size: [4, 2], pieces: ['BriefRow'], kind: 'cover' },
    'U': { pieces: ['Lectern'], rotate: 0, kind: 'cover' },
    'p': { pieces: ['Plant', 'Plant_B'], rotate: 'random90', kind: 'cover' },
    'B': { size: [2, 1], pieces: ['WaitBench'], flip: true, kind: 'cover' },
    'o': { pieces: ['Vending', 'Cooler'], rotate: 'edge', kind: 'cover' },
    'H': { pieces: ['GearStand'], rotate: 'edge', kind: 'cover' },
    'z': { pieces: ['ToolChest'], rotate: 'edge', kind: 'cover' },
    't': { pieces: ['Drums', 'Tyres'], rotate: 'random90', kind: 'cover' },
    'X': { size: [2, 2], pieces: ['Pallet'], kind: 'cover' },
    'D': { size: [4, 1], pieces: ['OpsConsole'], orient: 'wall', kind: 'cover' },
    'Q': { size: [6, 2], pieces: ['Landmark_FrontDesk'], kind: 'cover' },
    'V': { size: [3, 6], pieces: ['Landmark_Van'], flip: true, kind: 'wall' },
    'J': { size: [4, 3], pieces: ['Landmark_Cells'], orient: 'wall', kind: 'wall' },
    'y': { size: [3, 2], pieces: ['Booth'], kind: 'cover' },
    'Y': { pieces: ['Target'], rotate: 0, kind: 'cover' },
    // ---- floor layer (flat, no collision)
    '1': flat(['Floor_LobbyA', 'Floor_LobbyB'], 0, true),
    '2': flat(['Floor_CarpetA', 'Floor_CarpetB'], 0, true),
    '3': flat(['Floor_Rubber']),
    '4': flat(['Floor_Conc', 'Floor_Conc', 'Floor_Conc', 'Floor_ConcJ', 'Floor_Conc', 'Floor_Conc', 'Floor_Conc', 'Floor_ConcStain', 'Floor_Conc', 'Floor_Conc']),
    '5': flat(['Floor_Range']),
    '6': flat(['Floor_PaleA']),
    '7': flat(['Floor_Mat']),
    '/': flat(['Floor_Hazard']),
    '^': flat(['Floor_RangeLine']),
    ',': flat(['Floor_RangeLane']),
    '-': flat(['Floor_ConcLine'], 0), '|': flat(['Floor_ConcLine'], Math.PI / 2),
    '_': flat(['Floor_RubberLine'], 0), ':': flat(['Floor_RubberLine'], Math.PI / 2),
    'M': { size: [4, 4], pieces: ['Emblem'], collide: false },
    // ---- ceiling layer (hanging from y = 4)
    'i': flat(['Ceil_Panel']), 'j': flat(['Ceil_HighBay']),
    '=': flat(['Beam'], 0), '!': flat(['Beam'], Math.PI / 2), '+': flat(['BeamX']),
    '~': flat(['Duct'], 0), ';': flat(['Duct'], Math.PI / 2),
    '*': flat(['Baffle']), '[': flat(['Lintel'], 0), ']': flat(['Lintel'], Math.PI / 2)
  };
  // every character a zone's floor plan can hold: the ceiling's auto lights skip them all (the zones light themselves
  // from the ceiling layer; the corridors and the hatch room keep the auto lights)
  var ALL = '.#SPEGah' + Object.keys(SYMBOLS).join('');
  var WALLS = [];
  Object.keys(ART).forEach(function (S) {
    WALLS.push('W' + S, 'Corner' + S);
    Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (RUNS[p]) WALLS.push(p + 'L', p + 'M', p + 'R'); else WALLS.push(p); });
  });
  var PIECES = WALLS.concat(['CeilLight', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Board', 'TrailWall_Badge',
    'TrailWall_Window', 'Hatch', 'Crate']);
  Object.keys(SYMBOLS).forEach(function (ch) { SYMBOLS[ch].pieces.forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); }); });

  IB.registerTheme({
    id: 'police', name: 'Strike Team HQ', family: 'kit-police', prefix: 'KIT_POLICE_',
    palette: ['#2D4F8E', '#F0B530', '#D6E2EE', '#B8C8DA'],
    env: {
      sky: null, clear: '#D3DCE8', fog: { color: '#D3DCE8', near: 38, far: 115 }, clouds: false,
      sun: [0.3, 0.4, 0.87],   // low light from the south-east: walls facing south / east lit, the ceiling in the mid band
      ceiling: { height: 4.0, color: '#E4E9F0', light: 'CeilLight', every: 4, clear: ALL, clearR: 0 }
    },
    floor: {
      color: '#AEB0AE', trail: '#B8C8DA', outside: '#AEB0AE',
      trailLines: [{ dir: 'x', every: 1, width: 0.03, color: '#8FA2B8', y: 0.008 }, { dir: 'z', every: 1, width: 0.03, color: '#8FA2B8', y: 0.0105 }]
    },
    wall: { height: 4.0, roof: '#C2C8D0', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    // armory odds (game.js placeLoot): rack guns by weapon tier (src/game/wdrops.js TIERS), bench / shelf gear by rarity
    armory: { tiers: { gray: 46, green: 34, blue: 19.25, purple: 0.75, orange: 0 }, gear: { common: 62, rare: 33, epic: 5, legendary: 0 } },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 4.0, variants: ['TrailWall', 'TrailWall_Board', 'TrailWall', 'TrailWall_Badge', 'TrailWall', 'TrailWall_Window'], end: 'TrailWall' },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: null,
    budget: { prop: 2000, landmark: 4000, total: 70000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      police: {
        name: 'Strike Team HQ',
        intro: 'The armory is open: take real guns off the weapon walls and fit mods at the benches (E / USE).',
        zones: [
          { map: 'police_1', waves: [[['crawler', 18], ['gunner', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['blader', 6]], [['crawler', 4], ['drone', 3], ['gunner', 4], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['soldier', 6]]] },
          { map: 'police_2', waves: [[['crawler', 19], ['gunner', 6], ['drone', 2]], [['crawler', 5], ['bomber', 5], ['gunner', 5], ['blader', 6]], [['crawler', 5], ['drone', 4], ['gunner', 5], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['blader', 5]]] },
          { map: 'police_3', waves: [[['crawler', 19], ['gunner', 8]], [['crawler', 5], ['bomber', 5], ['drone', 4], ['soldier', 6]], [['crawler', 7], ['gunner', 7], ['drone', 4], ['blader', 6]], [['crawler', 7], ['gunner', 8], ['bomber', 7], ['drone', 3], ['soldier', 11]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
