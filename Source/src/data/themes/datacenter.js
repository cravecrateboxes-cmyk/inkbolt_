/* Theme: Helix Vault (kit-datacenter) -- a very wide hyperscale data center run by the made-up HELIXA corporation,
   with a secret R&D wing at the back. Three zones under a 6 m dark open ceiling with LED strips and yellow fibre trays:
   1 Data Hall A1: hot / cold aisles of blinking rack rows, CRAC cooling units along the walls, a NOC with a video
     wall behind glass, a storage room behind a security door.
   2 Data Hall B2: north-south rack rows, the secure core (colocation cages round the quantum core), a bolted vault
     (weapon lockers), the UPS / battery room and a glass meeting room.
   3 R&D Wing C3: robot chassis on assembly gantries, holographic design tables, weapon prototypes in containment
     fields, cryo cylinders, the energy test chamber and the Forge (a giant fabrication ring).
   Breakable doors (game/doors.js, symbol option `breakable`): security doors, the vault door, glass doors, cage gates and
   the containment fields take damage from bullets, blades, robot fire and every blast, show dents / cracks and sparks,
   then burst; their collision, the sight lines through them and the nav grid open up. The rooms behind hold loot:
   weapon lockers (guns at `armory.tiers`), gear lockers (shields / vests) and mod benches (attachments) at
   `armory.gear`, and a gun in every containment field.
   Built by blender/fam_kit_datacenter.py (dc_*.py); zone layers by tools/datacenter_zones.py.

   A zone file has three grids: the floor plan, "@layer 0.01" (floor finishes; on wall cells, wall-art codes) and
   "@layer 6" (ceiling fittings hanging from the 6 m ceiling).
   Floor plan:  R r ] [ rack row [3,1] (front S / N / E / W; runs capped with labelled end panels)
     C CRAC unit [3,1] (against a wall)  T clean-agent tanks [2,1]  U UPS cabinets [3,1]  B battery strings [3,1]
     Q power distribution unit [2,1]  N NOC desk [4,2] (faces north)  M meeting table [4,2]  O column
     x server boxes on a pallet  k crash cart  z cable drum  o open floor tile  K quantum core [4,4]
     W weapon locker [3,1] (4 guns)  g gear locker [2,1] (2 shields / vests)  j mod bench [2,1] (2 attachments)
     H holo design table [3,2] (turning hologram)  A mech chassis gantry [4,4]  Y walker chassis gantry [4,4]
     F weapon prototype in a containment field [2,2] (breakable, a gun inside)  Z cryo cylinder  b lab bench [2,1]
     f fabricator [2,2]  e cobot arm  y parts shelf [2,1]  X energy test chamber [6,6]  L the Forge [8,4]
     q glass partition (runs)  w cage partition (runs)
     Doors (breakable): D security door [3,2] and u UPS door [3,2] and V vault door [3,2] (in 2-cell walls: the cells
     count as wall, solid above 2.7 m), d glass door [3,1] and l lab glass door [3,1] (in glass runs), c cage gate [3,1]
   Floor layer: 1 perforated cold-aisle tile  2 hot-aisle tile  3 lab epoxy  4 5 lab floor with a cyan line (X / Z)
     6 carpet  7 NOC dark floor  , secure-room tiles  8 their hazard edge along the walls  9 0 walkway line (X / Z)
     m HELIXA floor emblem [4,4]
     Wall-art codes (on wall cells): i return-air grille  p fire alarm + extinguisher  s I @ hall signs A1 / B2 / C3
     ! emergency power off  | cable risers  v video wall (runs)  n world clocks  t lab blueprint screen  % HELIXA logo
     J observation window  ^ high-voltage sign  & breaker panel  ? louvred vent
   Ceiling layer: - yellow fibre tray  = cable ladder  _ LED strip  + sprinkler main (all runs)  : busbar (runs)
     ; smoke detector + camera  { lab light panel
   The wall chooser styles each module from the floor in front of it: data hall (white panels, teal band), NOC
   (graphite acoustic panels), lab (white with cyan seams), secure rooms (grey block, hazard foot). */
(function (IB) {
  'use strict';
  var FSTYLE = { '1': 'H', '2': 'H', '9': 'H', '0': 'H', '7': 'N', '3': 'L', '4': 'L', '5': 'L', 'm': 'L', '6': 'L', '8': 'R', ',': 'R' };
  var ART = {
    H: { i: 'WH_Grille', p: 'WH_Panel', s: 'WH_SignA', I: 'WH_SignB', '@': 'WH_SignC', '!': 'WH_Epo', '|': 'WH_Riser' },
    N: { v: 'WN_Video', n: 'WN_Clock' },
    L: { t: 'WL_Screen', '%': 'WL_Logo', J: 'WL_Window', '@': 'WH_SignC' },
    R: { '^': 'WR_Sign', '&': 'WR_Panel', '?': 'WR_Vent', p: 'WH_Panel' }
  };
  var RUNS = { WN_Video: 1 };
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var LEFT = { S: [-1, 0], N: [1, 0], E: [0, 1], W: [0, -1] };
  var NB = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]];
  var DOORS = 'DuV';
  function floorOf(grid) {
    if (grid._dcF === undefined) {
      grid._dcF = null;
      (grid.layers || []).forEach(function (l) { if (!grid._dcF && l.y < 1) grid._dcF = l; });
    }
    return grid._dcF;
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (DOORS.indexOf(grid.at(c, r)) >= 0) return null;   // the door prefab draws its own frame and header
    var F = floorOf(grid), S = '', k;
    if (face === 'corner' || face === 'none' || !FACE[face]) {
      for (k = 0; F && k < NB.length && !S; k++) S = FSTYLE[F.at(c + NB[k][0], r + NB[k][1])] || '';
      return 'Corner' + (S || 'H');
    }
    if (!F) return 'WH';
    var d = FACE[face];
    for (k = 1; k <= 4 && !S; k++) S = FSTYLE[F.at(c + d[0] * k, r + d[1] * k)] || '';
    S = S || 'H';
    var code = F.at(c, r), piece = ART[S][code];
    if (!piece) return 'W' + S;
    if (RUNS[piece]) {
      var L = LEFT[face], hasL = F.at(c + L[0], r + L[1]) === code, hasR = F.at(c - L[0], r - L[1]) === code;
      return piece + (!hasL ? 'L' : !hasR ? 'R' : 'M');
    }
    return piece;
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }
  function run(piece) { return { pieces: [piece], collide: false, rotate: 'run' }; }

  // rack rows: the first / last prefab of a run carries the end panel on its outer end (local -X / +X)
  var MID = ['RackRow_A', 'RackRow_C', 'RackRow_A', 'RackRow_D', 'RackRow_A', 'RackRow_C'];
  function rack(face, reversed) {
    var p = reversed ? ['RackRow_EndR'].concat(MID, ['RackRow_EndL']) : ['RackRow_EndL'].concat(MID, ['RackRow_EndR']);
    return { size: [3, 1], pieces: p, face: face, sequence: 'run', kind: 'cover' };
  }
  var R90 = Math.PI / 2;
  // loot mounts in prefab-local game coordinates: [x, height, z (toward the room = +), yaw offset, kind, options]
  var GUN = { back: true, len: 1.0, h: 0.34, tag: [0, -0.26, -0.016] };
  var LOCKER = [[-0.76, 1.06, -0.415, 0, 'gun', GUN], [0.76, 1.06, -0.415, 0, 'gun', GUN],
    [-0.76, 1.76, -0.415, 0, 'gun', GUN], [0.76, 1.76, -0.415, 0, 'gun', GUN]];
  var SHELF = [[-0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }], [0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }]];
  var BENCH = [[-0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }], [0.48, 0.926, 0.18, 0, 'mod', { tag: [0, -0.036, 0.253] }]];
  var POD = [[0, 1.3, -0.05, 0, 'gun', { back: true, len: 0.95, h: 0.36, tag: [0, -0.325, 0.185] }]];
  // breakable doors (hp in level-1 damage units: a Rivet does 22 a round, a frag can 150 at the centre, x4 on doors)
  var SEC = { hp: 420, debris: 'metal', color: '#3A4048', word: 'KRUNCH!', leaf: 'SecDoor' };
  var VAULT = { hp: 900, debris: 'metal', color: '#8E99A5', word: 'KA-BOOM!' };
  var GLASS = { hp: 110, debris: 'glass', color: '#9FD6E8', word: 'KRAK!', leaf: 'GlassDoor' };
  var CAGE = { hp: 240, debris: 'mesh', color: '#7C8792', word: 'KA-CHUNK!' };
  var FIELD = { hp: 260, debris: 'field', color: '#3BD8F0', word: 'ZZAP!', blend: 'add' };

  var SYMBOLS = {
    // ---- data halls
    'R': rack(0, false), 'r': rack(Math.PI, true), ']': rack(R90, false), '[': rack(-R90, true),
    'C': { size: [3, 1], pieces: ['Crac'], orient: 'wall', kind: 'cover' },
    'T': { size: [2, 1], pieces: ['Tanks'], orient: 'wall', kind: 'cover' },
    'U': { size: [3, 1], pieces: ['Ups'], orient: 'wall', kind: 'cover' },
    'B': { size: [3, 1], pieces: ['Batteries'], flip: true, kind: 'cover' },
    'Q': { size: [2, 1], pieces: ['Pdu'], orient: 'wall', kind: 'cover' },
    'N': { size: [4, 2], pieces: ['NocDesk'], face: Math.PI, kind: 'cover' },
    'M': { size: [4, 2], pieces: ['MeetTable'], kind: 'cover' },
    'O': { pieces: ['Column'], kind: 'cover' },
    'x': { pieces: ['Boxes', 'Boxes_B'], rotate: 'random90', kind: 'cover' },
    'k': { pieces: ['CrashCart'], rotate: 'random90', kind: 'cover' },
    'z': { pieces: ['CableDrum'], rotate: 'random90', kind: 'cover' },
    'o': { pieces: ['TileOpen'], rotate: 'random90', kind: 'cover' },
    'K': { size: [4, 4], pieces: ['Landmark_Quantum'], kind: 'cover' },
    'W': { size: [3, 1], pieces: ['Armory'], orient: 'wall', kind: 'cover', mounts: LOCKER, fill: 0.75 },
    'g': { size: [2, 1], pieces: ['GearLocker'], orient: 'wall', kind: 'cover', mounts: SHELF },
    'j': { size: [2, 1], pieces: ['ModBench'], orient: 'wall', kind: 'cover', mounts: BENCH },
    // ---- R&D wing
    'H': { size: [3, 2], pieces: ['HoloTable', 'HoloTable_B'], flip: true, kind: 'cover' },
    'A': { size: [4, 4], pieces: ['Landmark_GantryMech'], flip: true, kind: 'cover' },
    'Y': { size: [4, 4], pieces: ['Landmark_GantryWalker'], flip: true, kind: 'cover' },
    'F': { size: [2, 2], pieces: ['FieldPod'], face: 0, kind: 'cover', mounts: POD, breakable: FIELD },
    'Z': { pieces: ['CryoPod_A', 'CryoPod_B', 'CryoPod_A'], rotate: 'edge', kind: 'cover' },
    'b': { size: [2, 1], pieces: ['LabBench_Arm', 'LabBench_Chip', 'LabBench_Parts'], flip: true, kind: 'cover' },
    'f': { size: [2, 2], pieces: ['Fabricator'], flip: true, kind: 'cover' },
    'e': { pieces: ['Cobot'], rotate: 'random90', kind: 'cover' },
    'y': { size: [2, 1], pieces: ['PartsShelf'], orient: 'wall', kind: 'cover' },
    'X': { size: [6, 6], pieces: ['Landmark_Chamber'], face: 0, kind: 'cover' },
    'L': { size: [8, 4], pieces: ['Landmark_Forge'], face: 0, kind: 'cover' },
    // ---- partitions (runs) and breakable doors
    'q': { pieces: ['GlassHalf'], full: 'GlassFull', links: 'qdl#', post: 'GlassPost', kind: 'wall' },
    'w': { pieces: ['CageHalf'], full: 'CageFull', links: 'wc#', post: 'CagePost', kind: 'wall' },
    'D': { size: [3, 2], pieces: ['SecDoor'], orient: 'span', kind: 'wall', breakable: SEC },
    'u': { size: [3, 2], pieces: ['SecDoorUPS'], orient: 'span', kind: 'wall', breakable: SEC },
    'V': { size: [3, 2], pieces: ['VaultDoor'], orient: 'span', kind: 'wall', breakable: VAULT },
    'd': { size: [3, 1], pieces: ['GlassDoor'], orient: 'span', kind: 'wall', breakable: GLASS },
    'l': { size: [3, 1], pieces: ['GlassDoorLab'], orient: 'span', kind: 'wall', breakable: GLASS },
    'c': { size: [3, 1], pieces: ['CageGate'], orient: 'span', kind: 'wall', breakable: CAGE },
    // ---- floor layer (flat, no collision)
    '1': flat(['Floor_Perf']), '2': flat(['Floor_Hot']), '3': flat(['Floor_Lab']),
    '4': flat(['Floor_LabLine']), '5': flat(['Floor_LabLine'], R90), '6': flat(['Floor_Carpet']), '7': flat(['Floor_Dark']),
    '8': { pieces: ['Floor_Hazard'], collide: false, rotate: 'edge', edge: ',' }, ',': flat(['Floor_Secure']),
    '9': flat(['Floor_Line']), '0': flat(['Floor_Line'], R90),
    'm': { size: [4, 4], pieces: ['Floor_Emblem'], collide: false },
    // ---- ceiling layer (hanging from y = 6)
    '-': run('Tray'), '=': run('Ladder'), '_': run('LightL'), '+': run('Pipe'), ':': run('Busway'),
    ';': flat(['Sensors']), '{': flat(['LabPanel'])
  };
  // glow companions (zones.js theme.glow): LEDs and screens drawn unlit, rack LEDs blinking in four phase groups,
  // holograms turning over their tables, the test chamber's core pulsing (backdrop.build animates them)
  var GLOW = {
    Crac: { piece: 'Crac_LED' }, Ups: { piece: 'Ups_LED' }, NocDesk: { piece: 'NocDesk_LED' }, CrashCart: { piece: 'CrashCart_LED' },
    WN_VideoL: { piece: 'WN_VideoL_LED' }, WN_VideoM: { piece: 'WN_VideoM_LED' }, WN_VideoR: { piece: 'WN_VideoR_LED' },
    WN_Clock: { piece: 'WN_Clock_LED' }, WL_Screen: { piece: 'WL_Screen_LED' }, LightL: { piece: 'LightL_LED' }, LabPanel: { piece: 'LabPanel_LED' },
    HoloTable: [{ piece: 'HoloTable_LED' }, { piece: 'Holo_Mech', spin: true, blend: 'add' }],
    HoloTable_B: [{ piece: 'HoloTable_B_LED' }, { piece: 'Holo_Gun', spin: true, blend: 'add' }],
    Landmark_Quantum: { piece: 'Landmark_Quantum_LED' }, CryoPod_A: { piece: 'CryoPod_A_LED' }, CryoPod_B: { piece: 'CryoPod_B_LED' },
    Fabricator: { piece: 'Fabricator_LED' }, Landmark_GantryMech: { piece: 'Landmark_GantryMech_LED' },
    Landmark_GantryWalker: { piece: 'Landmark_GantryWalker_LED' }, Landmark_Forge: { piece: 'Landmark_Forge_LED' },
    Landmark_Chamber: [{ piece: 'Landmark_Chamber_LED' }, { piece: 'Chamber_Core', spin: true, blend: 'add' }]
  };
  ['A', 'C', 'D', 'EndL', 'EndR'].forEach(function (k) {
    GLOW['RackRow_' + k] = [{ piece: 'RackRow_' + k + '_LED' }, { piece: 'RackRow_' + k + '_Blink', groups: 4 }];
  });
  /* the glows' life: rack LEDs blink in four phase groups at their own rates, holograms turn and flicker now and then,
     the chamber core pulses (its own copy of the additive material), the Forge's ring breathes */
  function animate(level, api) {
    var spin = [], blink = [], core = [], forge = [];
    (level.glows || []).forEach(function (G) {
      if (G.def.spin && /^Holo_/.test(G.piece)) spin.push(G);
      else if (G.piece === 'Chamber_Core') { G.mesh.material = G.mesh.material.clone(); core.push(G); }
      else if (/_Blink$/.test(G.piece)) blink.push(G);
      else if (G.piece === 'Landmark_Forge_LED') forge.push(G);
    });
    var RATE = [1.3, 2.2, 3.4, 5.1];
    api.tick(function (dt, t) {
      for (var i = 0; i < blink.length; i++) { var b = blink[i], ph = (t * RATE[b.group] + b.group * 0.37 + b.zone * 0.11) % 1; b.mesh.visible = ph < 0.55; }
      for (i = 0; i < spin.length; i++) {
        var s = spin[i];
        s.mesh.rotation.set(0, (s.mesh.userData.yaw0 || 0) + t * (0.45 + 0.1 * (i % 3)), 0);
        s.mesh.visible = ((t * 0.7 + i * 0.29) % 4.0) > 0.06;   // a hologram glitch every few seconds
      }
      for (i = 0; i < core.length; i++) core[i].mesh.material.opacity = 0.65 + 0.35 * Math.sin(t * 3.1 + i);
      for (i = 0; i < forge.length; i++) forge[i].mesh.visible = (t % 2.6) > 0.08;
    });
  }

  var ALL = '.#SPEGah' + Object.keys(SYMBOLS).join('');
  var WALLS = [];
  Object.keys(ART).forEach(function (S) {
    WALLS.push('W' + S, 'Corner' + S);
    Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (RUNS[p]) WALLS.push(p + 'L', p + 'M', p + 'R'); else if (WALLS.indexOf(p) < 0) WALLS.push(p); });
  });
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch',
    'SecDoor_Leaf', 'SecDoor_Leaf_D1', 'SecDoor_Leaf_D2', 'SecDoor_Broken', 'VaultDoor_Leaf', 'VaultDoor_Leaf_D1', 'VaultDoor_Leaf_D2', 'VaultDoor_Broken',
    'GlassDoor_Leaf', 'GlassDoor_Leaf_D1', 'GlassDoor_Leaf_D2', 'GlassDoor_Broken', 'CageGate_Leaf', 'CageGate_Leaf_D1', 'CageGate_Leaf_D2', 'CageGate_Broken',
    'FieldPod_Leaf', 'FieldPod_Leaf_D1', 'FieldPod_Leaf_D2', 'FieldPod_Broken']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'datacenter', name: 'Helix Vault', family: 'kit-datacenter', prefix: 'KIT_DATACENTER_',
    palette: ['#12C7B6', '#3FE6F5', '#F2F5F7', '#3A4048'],
    env: {
      sky: null, clear: '#323A44', fog: { color: '#3A4350', near: 42, far: 130 }, clouds: false,
      sun: [0.35, 0.82, 0.45],
      ceiling: { height: 6.0, color: '#2B3038' }   // fittings come from the zone's "@layer 6" grid
    },
    // raised-floor tiles on a 1 m grid
    floor: {
      color: '#D3DAE0', trail: '#C8D1D9', outside: '#D3DAE0',
      lines: [{ dir: 'x', every: 1, width: 0.025, color: '#AEB9C3', y: 0.006 }, { dir: 'z', every: 1, width: 0.025, color: '#AEB9C3', y: 0.008 }]
    },
    wall: { height: 6.0, roof: '#2B3038', facing: 'open', choose: chooseWall, passage: { ch: DOORS, solid: [[2.7, 6.0]] } },
    symbols: SYMBOLS,
    glow: GLOW,
    // the rooms behind breakable doors pay off: better odds than the police armory (game.js placeLoot)
    armory: { tiers: { gray: 38, green: 42, blue: 15, purple: 4, orange: 1 }, gear: { common: 46, rare: 38, epic: 13, legendary: 3 } },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C'], height: 6.0 },
    hatch: 'Hatch', stand: 'Boxes',
    backdrop: { build: animate },
    budget: { prop: 2400, landmark: 4000, total: 70000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      datacenter: {
        name: 'Helix Vault',
        intro: 'Shoot or blast the locked doors open: the vault, the cages and the containment fields hold loot.',
        zones: [
          // Data Hall A1: hot / cold aisles, the NOC, a storage room
          { map: 'datacenter_1', waves: [[['crawler', 22], ['gunner', 6]], [['crawler', 9], ['bomber', 2], ['gunner', 6], ['blader', 8]], [['crawler', 7], ['drone', 5], ['gunner', 5], ['soldier', 7]], [['crawler', 10], ['bomber', 2], ['gunner', 7], ['soldier', 8], ['blader', 3]]] },
          // Data Hall B2: the secure core, the vault, the UPS room
          { map: 'datacenter_2', waves: [[['crawler', 22], ['gunner', 7], ['drone', 3]], [['crawler', 9], ['bomber', 2], ['gunner', 7], ['blader', 9]], [['crawler', 7], ['drone', 6], ['gunner', 5], ['soldier', 8]], [['crawler', 10], ['bomber', 2], ['gunner', 7], ['blader', 7], ['soldier', 5]]] },
          // R&D Wing C3: gantries, holo tables, containment fields, the Forge
          { map: 'datacenter_3', waves: [[['crawler', 22], ['gunner', 9], ['drone', 2]], [['crawler', 11], ['bomber', 2], ['drone', 5], ['soldier', 9]], [['crawler', 9], ['gunner', 8], ['drone', 5], ['blader', 9]], [['crawler', 14], ['gunner', 10], ['bomber', 2], ['drone', 4], ['soldier', 12], ['blader', 6]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
