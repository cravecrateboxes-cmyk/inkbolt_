/* Theme: Kolvane Station K-7 (kit-arctic) -- an abandoned polar research station of the (made-up) Kolvane Polar
   Institute, buried under ice and snow. Two zones:
     arctic_1  The buried surface works (open sky): a 12 m trench cut down through layered firn (blue-white bands,
               old snow lines, a snow cornice on the rim) to the half-buried station. In the trench: the collapsed
               radar dome (landmark), the snowcat, the fuel depot, sledges, antenna and weather masts out of their
               drifts, a buried hut's roof, the buried 1987 lab module (snow steps up onto its 2.2 m roof); the entry
               ramp up to the surface in the south wall, buried at its foot by a snow slide. The station's upper
               modules (3.7 m ceiling): the corridor, four bunk rooms, comms (the dead terminal), the shaft head room
               (winch, the shaft door: the exit), the mess hall (the ice tore its wall open), the hall and boot room
               behind the airlock, the science office. Frost on everything, ice breaking in, lights dead or flickering.
               Blowing snow drifts over the trench (backdrop.build); antenna masts stand on the surface round the rim.
     arctic_2  The deep labs (12 m ice ceiling): the shaft foot hall, frozen corridors with hanging ice, the
               drill-core archive (racks of core tubes) and the cryo lab (sample tanks, freezers) under 4.4 m lab
               ceilings, the sealed vault (breakable door, the station's security cache inside), the generator hall
               (gensets, boiler, pipes; a catwalk gallery and bridge at 4.5 m), and the ice cavern the drill broke
               into: an ancient ring machine half swallowed by its north wall (landmark; its glyphs pulse), a
               scaffold catwalk in front of it at 4.5 m and a high platform at 7 m.
   Built by blender/fam_kit_arctic.py (arc_*.py); zone layers by tools/arctic_zones.py.

   Floor plan:  # wall (12 m)   doors (frames; their cells count as wall, solid above 2.7 m): D station door [3,2]
     (trench side front)  d interior door [3,1]  B the mess hall breach [3,2]  , the cryo lab breach [3,2]
     L lab door [3,2] (cave side south / east)  l lab door (cave side north / west)  V vault door [3,2] (breakable)
     trench: K collapsed radar dome [8,8]  Q snowcat [4,6]  T fuel tank on a sledge [3,6]  o drums  c crates (stacked)
       Y cargo sledge [2,4]  M antenna mast in its drift [2,2]  H buried hut's roof [6,4]  U buried module [8,3]
       (walkable roof at 2.2 m)  Z / z snow steps up to it rising north / south [3,4]  g generator skid [3,2]
       O snow bank [2,2]  f route flag  W weather mast
     station: m mess table [4,2]  k chair (knocked over)  n galley [4,1]  p pantry [2,1]  b bunk [2,1]  i locker
       e desk [2,1]  t dead terminal [2,1]  R radio rack [2,1]  A map table [3,2]  j boot bench [2,1]
       J parka rack [2,1]  I ice breaking in [2,2]  @ shaft winch [4,3]  x supply boxes  y filing cabinet
     deep labs: C core-tube rack [3,1] (runs capped by end panels)  F core logging table [3,2]  v core boxes
       q cryo sample tank [2,2]  u dewars  s ultra-low freezers [2,1]  [ lab bench [3,1]  ] glove box [3,1]
       ( genset [4,6]  ) boiler [4,4]  } day tank [3,2]  | switchboard [4,1]  & pump [2,1]  { pipe run (runs)
       ! security weapon locker [3,1] (4 guns)  ? gear locker [2,1] (2 shields / vests)  / ice pillar [2,2]
       ; ice spike  $ the frozen relic [14,6] (against the north wall)  X / N steel stair to 4.5 m rising north /
       south [3,8]
   "@layer 0.01" floor finishes: 1 vinyl  2 mess tiles  3 bunk carpet  4 lab tiles  5 steel plate  6 grating
     7 drifted snow  8 papers  9 hazard edge  0 ice sheet
   "@layer 3.7" (station) / "@layer 4.4" (labs) ceiling tiles (each holds a thin box, so flyers keep under it):
     = tile  + light (flickering)  _ dead light  % fallen tile  ~ vent
   "@layer 4.5" / "@layer 7" catwalks: w walkway deck  r rail  < steel stair 4.5 -> 7 m rising north [3,6]
   "@layer 12" cave ceiling: ^ hanging ice [3,3]  * icicles  : work lamp on its cable
   The wall chooser styles each module from what is in front of it: under a ceiling the station (S), its mess
   hall (M) or the labs (L); in the open the trench's firn (F) -- or the station facade where the station is behind
   it --, the caves' glacier ice (C) -- or the lab modules' steel shell where a lab is behind it --, or the
   generator hall's plating (P, steel-plate floor in front). Signs go up beside the doors. */
(function (IB) {
  'use strict';
  var TILE = '=-+_%~', DOORS = 'DdBLlV,';
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var NB = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]];
  function layerNear(grid, lo, hi, key) {
    if (grid[key] === undefined) {
      grid[key] = null;
      (grid.layers || []).forEach(function (l) { if (!grid[key] && l.y > lo && l.y < hi) grid[key] = l; });
    }
    return grid[key];
  }
  function indoor(grid, c, r) { var C = layerNear(grid, 3, 5, '_acC'); return !!C && TILE.indexOf(C.at(c, r)) >= 0; }
  function finishAt(grid, c, r) { var F = layerNear(grid, 0, 0.5, '_acF'); return F ? F.at(c, r) : '.'; }
  function surface(grid) { return grid.h > 63; }   // zone 1 (66 rows) is the surface, zone 2 the deep labs
  function gateC(grid, r) {
    var cache = grid._acGate || (grid._acGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows[r] || '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  // the room a door leads into, from the cell beyond the wall (signs beside doors)
  function roomWord(grid, c, r) {
    if (surface(grid)) {
      if (r < 13) return c < 8 ? 'BUNKA' : c < 16 ? 'BUNKB' : c < 24 ? 'BUNKC' : c < 39 ? 'SHAFTK7' : c < 51 ? 'COMMS' : 'BUNKD';
      return c < 23 ? 'MESS' : c < 40 ? 'BOOTROOM' : 'SCIENCE';
    }
    return c < 22 ? 'COREARCHIVE' : r < 38 ? 'CRYOLAB' : 'VAULT3';
  }
  function style(grid, c, r, d) {
    var fc = c + d[0], fr = r + d[1], k;
    if (indoor(grid, fc, fr)) return surface(grid) ? (finishAt(grid, fc, fr) === '2' ? 'M' : 'S') : 'L';
    var behind = false;
    for (k = 1; k <= 3 && !behind; k++) behind = indoor(grid, c - d[0] * k, r - d[1] * k);
    if (surface(grid)) return behind ? 'X' : 'F';
    for (k = 1; k <= 3; k++) if (finishAt(grid, c + d[0] * k, r + d[1] * k) === '5') return 'P';
    return behind ? 'H' : 'C';
  }
  function doorBeside(grid, c, r, d) {   // a door in the same wall line, one or two cells along it
    var ax = d[1] ? 1 : 0, az = d[0] ? 1 : 0;
    for (var s = -1; s <= 1; s += 2) for (var k = 1; k <= 1; k++) if (DOORS.indexOf(grid.at(c + ax * s * k, r + az * s * k)) >= 0) return true;
    return false;
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (DOORS.indexOf(grid.at(c, r)) >= 0) return null;   // the door frame draws its own
    var W = grid.w, H = grid.h, h0 = hash(c * 7 + 3, r * 13 + 1);
    if (face === 'S' || face === 'N') { var g = gateC(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return null; }   // gate jambs
    if (face === 'corner' || face === 'none' || !FACE[face]) {
      var S = '';
      for (var i = 0; i < NB.length && !S; i++) {
        var nc = c + NB[i][0], nr = r + NB[i][1];
        if (indoor(grid, nc, nr)) S = surface(grid) ? (finishAt(grid, nc, nr) === '2' ? 'M' : 'S') : 'L';
      }
      if (!S) S = surface(grid) ? 'F' : (finishAt(grid, c + 1, r) === '5' || finishAt(grid, c - 1, r) === '5' || finishAt(grid, c, r + 1) === '5' || finishAt(grid, c, r - 1) === '5') ? 'P' : 'C';
      return 'Corner' + S;
    }
    var d = FACE[face], u = (face === 'S' || face === 'N') ? c : r, st = style(grid, c, r, d);
    // a sign beside a door, on its corridor / hall / cave side, naming the room behind
    var fc = c + d[0], fr = r + d[1];
    var hallSide = surface(grid) ? ((fr >= 14 && fr <= 17) || (fc >= 24 && fc <= 39 && fr >= 19 && fr <= 24)) : st === 'H';
    var sign = hallSide && doorBeside(grid, c, r, d) ? 'Sign_' + roomWord(grid, c - d[0], r - d[1]) : null;
    var base;
    if (st === 'F') {
      if (surface(grid) && r === H - 1 && c >= 27 && c <= 36) return c === 27 ? 'Ramp_L' : c === 36 ? 'Ramp_R' : (c % 2 ? 'Ramp_M' : 'Ramp_N');
      base = u % 9 === 4 ? 'Firn_Lamp' : h0 < 0.06 ? 'Firn_Pipe' : h0 < 0.1 ? 'Firn_Mark' : ['Firn_A', 'Firn_B', 'Firn_C'][Math.floor(hash(c * 3, r * 5) * 3) % 3];
    } else if (st === 'X') {
      if (r === 33 && c === 34) return ['Fac_A', 'NameBoard'];
      if (r === 33 && c > 34 && c < 46) return h0 < 0.5 ? 'Fac_A' : 'Fac_B';   // under the name board
      base = u % 4 === 2 ? (h0 < 0.3 ? 'Fac_Broken' : 'Fac_Window') : u % 7 === 5 ? 'Fac_Vent' : u % 11 === 3 ? 'Fac_Light' : (h0 < 0.5 ? 'Fac_A' : 'Fac_B');
    } else if (st === 'S' || st === 'M') {
      var outer = c === 0 || c === W - 1 || r === 0 || (r === 32 && face === 'N');
      var open2 = grid.at(c + d[0], r + d[1]) === '.' && grid.at(c + d[0] * 2, r + d[1] * 2) === '.';
      if (outer && u % 4 === 2) base = st + '_Window';
      else if (grid.at(c + d[0], r + d[1]) === 'I') base = st + '_B';
      else if (open2 && h0 < 0.1) base = st + '_Heater';
      else if (st === 'S' && open2 && h0 < 0.15) base = 'S_Notice';
      else if (st === 'S' && h0 < 0.2) base = 'S_Pipe';
      else if (st === 'S' && open2 && h0 < 0.23) base = 'S_Map';
      else if (st === 'M' && open2 && h0 < 0.16) base = 'M_Menu';
      else if (open2 && h0 > 0.97) base = st + '_Breach';
      else base = st + (h0 < 0.8 ? '_A' : '_B');
    } else if (st === 'L') {
      var op = grid.at(c + d[0], r + d[1]) === '.';
      base = op && h0 < 0.1 ? 'L_Screen' : op && h0 < 0.18 ? 'L_Panel' : h0 < 0.65 ? 'L_A' : 'L_B';
    } else if (st === 'H') {
      base = u % 8 === 3 ? 'Shell_Lamp' : h0 < 0.12 ? 'Shell_Window' : (h0 < 0.55 ? 'Shell_A' : 'Shell_B');
    } else if (st === 'P') {
      var op2 = grid.at(c + d[0], r + d[1]) === '.';
      base = u % 7 === 3 ? 'P_Lamp' : h0 < 0.16 ? 'P_Pipes' : op2 && h0 < 0.22 ? 'P_Panel' : (h0 < 0.6 ? 'P_A' : 'P_B');
      if (!sign && h0 > 0.96) sign = 'Sign_POWERHALL';
    } else {
      base = u % 9 === 4 ? 'Cave_Lamp' : h0 < 0.1 ? 'Cave_Cable' : h0 < 0.14 ? 'Cave_Mark' : ['Cave_A', 'Cave_B', 'Cave_C'][Math.floor(hash(c * 5, r * 3) * 3) % 3];
    }
    if (sign && (st === 'F' || st === 'C' || st === 'X')) sign = null;
    if (sign && /_(Lamp|Window|Notice|Map|Menu|Breach|Heater|Panel|Pipes|Screen)$/.test(base)) base = st === 'H' ? 'Shell_A' : st === 'P' ? 'P_A' : st + '_A';
    return sign ? [base, sign] : base;
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }
  function cover(pieces, extra) { return Object.assign({ pieces: pieces, kind: 'cover' }, extra); }
  var R90 = Math.PI / 2;
  // loot in the vault (prefab-local game coordinates: [x, height, z (toward the room = +), yaw offset, kind, options])
  var GUN = { back: true, len: 1.0, h: 0.34, tag: [0, -0.26, -0.016] };
  var LOCKER = [[-0.76, 1.06, -0.415, 0, 'gun', GUN], [0.76, 1.06, -0.415, 0, 'gun', GUN],
    [-0.76, 1.76, -0.415, 0, 'gun', GUN], [0.76, 1.76, -0.415, 0, 'gun', GUN]];
  var SHELF = [[-0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }], [0.5, 1.16, -0.22, 0, 'item', { tag: [0, -0.03, 0.258] }]];
  var VAULT = { hp: 900, debris: 'metal', color: '#8F9AA6', word: 'KA-BOOM!' };
  var SYMBOLS = {
    // ---- doors and breaches (their cells are wall.passage)
    'D': { size: [3, 2], pieces: ['DoorX'], orient: 'span', kind: 'wall' },
    'd': { size: [3, 1], pieces: ['DoorI'], orient: 'span', kind: 'wall' },
    'B': { size: [3, 2], pieces: ['Breach'], orient: 'span', kind: 'wall' },
    ',': { size: [3, 2], pieces: ['BreachIce'], orient: 'span', kind: 'wall' },
    'L': { size: [3, 2], pieces: ['DoorL'], orient: 'span', face: 0, kind: 'wall' },
    'l': { size: [3, 2], pieces: ['DoorL'], orient: 'span', face: Math.PI, kind: 'wall' },
    'V': { size: [3, 2], pieces: ['VaultDoor'], orient: 'span', face: 0, kind: 'wall', breakable: VAULT },
    // ---- the trench
    'K': { size: [8, 8], pieces: ['Landmark_Radome'], flip: true, kind: 'cover' },
    'Q': { size: [4, 6], pieces: ['Snowcat'], flip: true, kind: 'cover' },
    'T': { size: [3, 6], pieces: ['FuelTank'], flip: true, kind: 'cover' },
    'o': cover(['Drums_A', 'Drums_B'], { rotate: 'random90' }),
    'c': cover(['Crate_A', 'Crate_B'], { rotate: 'random90', h: 0.9, stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.5 } }),
    'Y': { size: [2, 4], pieces: ['Sled'], flip: true, kind: 'cover' },
    'M': { size: [2, 2], pieces: ['Mast_A', 'Mast_B'], flip: true, kind: 'cover' },
    'H': { size: [6, 4], pieces: ['BuriedHut'], flip: true, kind: 'cover' },
    'U': { size: [8, 3], pieces: ['BuriedModule'], flip: true, kind: 'step' },
    'Z': { size: [3, 4], pieces: ['StairSnow'], face: 0, kind: 'step' },
    'z': { size: [3, 4], pieces: ['StairSnow'], face: Math.PI, kind: 'step' },
    'g': { size: [3, 2], pieces: ['Genset_S'], flip: true, kind: 'cover' },
    'O': { size: [2, 2], pieces: ['Snowbank_A', 'Snowbank_B'], flip: true, kind: 'cover' },
    'f': cover(['Flag'], { rotate: 'random90' }),
    'W': cover(['WeatherMast'], { rotate: 'random90' }),
    // ---- the station
    'm': { size: [4, 2], pieces: ['MessTable_A', 'MessTable_B'], flip: true, kind: 'cover' },
    'k': cover(['Chair_Down', 'Chair_Up', 'Chair_Down'], { rotate: 'random90' }),
    'n': { size: [4, 1], pieces: ['Galley'], orient: 'wall', kind: 'cover' },
    'p': { size: [2, 1], pieces: ['Pantry'], orient: 'wall', kind: 'cover' },
    'b': { size: [2, 1], pieces: ['Bunk_A', 'Bunk_B'], orient: 'wall', kind: 'cover' },
    'i': cover(['Locker_A', 'Locker_B'], { rotate: 'edge' }),
    'e': { size: [2, 1], pieces: ['Desk'], orient: 'wall', kind: 'cover' },
    't': { size: [2, 1], pieces: ['Terminal'], orient: 'wall', kind: 'cover' },
    'R': { size: [2, 1], pieces: ['RadioRack'], orient: 'wall', kind: 'cover' },
    'A': { size: [3, 2], pieces: ['MapTable'], flip: true, kind: 'cover' },
    'j': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
    'J': { size: [2, 1], pieces: ['ParkaRack'], orient: 'wall', kind: 'cover' },
    'I': { size: [2, 2], pieces: ['IceIntrusion'], orient: 'wall', kind: 'cover' },
    '@': { size: [4, 3], pieces: ['Winch'], face: 0, kind: 'cover' },
    'x': cover(['Boxes_A', 'Boxes_B'], { rotate: 'random90' }),
    'y': cover(['FileCab'], { rotate: 'edge' }),
    // ---- the deep labs
    'C': { size: [3, 1], pieces: ['CoreRack_EndL', 'CoreRack_A', 'CoreRack_EndR'], sequence: 'run', kind: 'cover' },
    'F': { size: [3, 2], pieces: ['CoreTable_A', 'CoreTable_B'], flip: true, kind: 'cover' },
    'v': cover(['CoreBoxes'], { rotate: 'random90' }),
    'q': { size: [2, 2], pieces: ['CryoTank'], flip: true, kind: 'cover' },
    'u': cover(['Dewars'], { rotate: 'random90' }),
    's': { size: [2, 1], pieces: ['Freezer'], orient: 'wall', kind: 'cover' },
    '[': { size: [3, 1], pieces: ['LabBench'], flip: true, kind: 'cover' },
    ']': { size: [3, 1], pieces: ['GloveBox'], orient: 'wall', kind: 'cover' },
    '(': { size: [4, 6], pieces: ['GenSet'], flip: true, kind: 'cover' },
    ')': { size: [4, 4], pieces: ['Boiler'], flip: true, kind: 'cover' },
    '}': { size: [3, 2], pieces: ['DayTank'], flip: true, kind: 'cover' },
    '|': { size: [4, 1], pieces: ['Switchboard'], orient: 'wall', kind: 'cover' },
    '&': { size: [2, 1], pieces: ['Pump'], flip: true, kind: 'cover' },
    '{': cover(['PipeRun'], { rotate: 'run' }),
    '!': { size: [3, 1], pieces: ['Armory'], orient: 'wall', kind: 'cover', mounts: LOCKER, fill: 0.75 },
    '?': { size: [2, 1], pieces: ['GearLocker'], orient: 'wall', kind: 'cover', mounts: SHELF },
    '/': { size: [2, 2], pieces: ['IcePillar'], flip: true, kind: 'cover' },
    ';': cover(['IceSpike'], { rotate: 'random90' }),
    '$': { size: [14, 6], pieces: ['Landmark_Relic'], face: 0, kind: 'cover' },
    'X': { size: [3, 8], pieces: ['Stair45'], face: 0, kind: 'step' },
    'N': { size: [3, 8], pieces: ['Stair45'], face: Math.PI, kind: 'step' },
    '<': { size: [3, 6], pieces: ['Stair70'], face: 0, kind: 'step' },
    // ---- catwalks (layers 4.5 and 7)
    'w': { deck: { thick: 0.25, color: '#A9B3BC', edge: '#5E6974', under: '#4C5560', with: '*' } },
    'r': { pieces: ['Rail'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    // ---- floor finishes (layer 0.01)
    '1': flat(['Fl_Vinyl']), '2': flat(['Fl_Mess']), '3': flat(['Fl_Carpet']), '4': flat(['Fl_Lab']), '5': flat(['Fl_Plate']),
    '6': flat(['Fl_Grate']), '7': flat(['Fl_Snow'], 'random90'), '8': flat(['Fl_Papers'], 'random90'), '9': flat(['Fl_Hazard']),
    '0': flat(['Fl_Ice'], 'random90'),
    // ---- ceiling tiles (layers 3.7 and 4.4): their thin boxes keep flyers under them
    '=': cover(['Ceil_A']), '-': cover(['Ceil_B']), '+': cover(['Ceil_LightOn']), '_': cover(['Ceil_Light']), '%': cover(['Ceil_Broken']), '~': cover(['Ceil_Vent']),
    // ---- the cave ceiling (layer 12)
    '^': { size: [3, 3], pieces: ['IceHang_A', 'IceHang_B'], flip: true, collide: false },
    '*': flat(['Icicles'], 'random90'),
    ':': flat(['CaveLamp'])
  };
  // glow companions (zones.js theme.glow): lamps and screens drawn unlit; lights flicker, the relic's glyphs pulse
  var GLOW = {
    Ceil_LightOn: { piece: 'Ceil_LightOn_LED', groups: 4 }, Firn_Lamp: { piece: 'Firn_Lamp_LED', groups: 3 },
    Cave_Lamp: { piece: 'Cave_Lamp_LED', groups: 3 }, Shell_Lamp: { piece: 'Shell_Lamp_LED', groups: 3 }, P_Lamp: { piece: 'P_Lamp_LED', groups: 3 },
    CaveLamp: { piece: 'CaveLamp_LED', groups: 3 }, Terminal: { piece: 'Terminal_LED' }, CryoTank: { piece: 'CryoTank_LED' },
    Freezer: { piece: 'Freezer_LED' }, Landmark_Relic: { piece: 'Landmark_Relic_LED', blend: 'add' }
  };
  var FLICK = /^(Ceil_LightOn|Firn_Lamp|Cave_Lamp|Shell_Lamp|P_Lamp|CaveLamp)_LED$/;
  /* backdrop.build: the glows' life (failing lights flicker per phase group, one group of each kind is dead, the
     terminal's cursor blinks, the relic pulses), blowing snow over the trench, masts on the surface round the rim */
  function build(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var Z1 = level.zones[0];
    if (Z1) {
      [[-5, 16, 'Mast_A', 0.3], [69, 40, 'Mast_A', 2.0], [-6, 52, 'WeatherMast', 0], [70, 58, 'Mast_B', 1.2], [20, 70, 'Mast_A', 2.6], [48, 72, 'Flag', 0],
        [-4, 34, 'Flag', 0], [68, 22, 'Flag', 0]].forEach(function (p) { api.add(p[2], Z1.ox + p[0], 12, Z1.oz + p[1], p[3], p[2] === 'Mast_A' ? 1.3 : 1.1); });
    }
    if (!THREE || !level.root) return;
    var flick = [], blink = [], relic = [];
    (level.glows || []).forEach(function (G) {
      if (FLICK.test(G.piece)) flick.push(G);
      else if (G.piece === 'Terminal_LED') blink.push(G);
      else if (G.piece === 'Landmark_Relic_LED') { G.mesh.material = G.mesh.material.clone(); G.mesh.material.transparent = true; relic.push(G); }
    });
    // blowing snow: small flakes over the trench, carried by the wind, wrapping round its box
    var flakes = [], snow = null, N = 240;
    if (Z1) {
      var geo = new THREE.OctahedronGeometry(0.045, 0), mat = new THREE.MeshBasicMaterial({ color: 0xF6FAFD });
      snow = new THREE.InstancedMesh(geo, mat, N); snow.frustumCulled = false; Z1.group.add(snow);
      var X0 = Z1.ox + 1, X1 = Z1.ox + Z1.w - 1, ZA = Z1.oz + 33, ZB = Z1.oz + Z1.h - 1;
      for (var i = 0; i < N; i++) flakes.push({ x: X0 + api.hash(i, 1) * (X1 - X0), y: api.hash(i, 2) * 15, z: ZA + api.hash(i, 3) * (ZB - ZA), s: 0.6 + api.hash(i, 4) * 0.9, w: api.hash(i, 5) * 6.28 });
    }
    var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3();
    api.tick(function (dt, t) {
      for (var i = 0; i < flick.length; i++) {
        var G = flick[i], g = G.group, ph = t * (1.7 + g * 0.9) + g * 1.3 + G.zone * 0.7;
        G.mesh.visible = g === 0 ? false : (Math.sin(ph) + Math.sin(ph * 3.7 + 1.1) * 0.6) > -0.9 || (g === 2 && (t % 5) > 4.2);
      }
      for (i = 0; i < blink.length; i++) blink[i].mesh.visible = (t % 1.1) < 0.6;
      for (i = 0; i < relic.length; i++) relic[i].mesh.material.opacity = 0.55 + 0.45 * Math.sin(t * 1.4);
      if (snow) {
        for (i = 0; i < flakes.length; i++) {
          var F = flakes[i];
          F.x += (2.2 + Math.sin(t * 0.7 + F.w)) * dt; F.y -= (0.7 + F.s * 0.4) * dt; F.z += Math.sin(t * 0.9 + F.w) * 0.6 * dt;
          if (F.x > X1) F.x = X0; if (F.y < 0) F.y = 15; if (F.z > ZB) F.z = ZA; if (F.z < ZA) F.z = ZB;
          _p.set(F.x, F.y, F.z); _s.set(F.s, F.s, F.s); snow.setMatrixAt(i, _m.compose(_p, _q, _s));
        }
        snow.instanceMatrix.needsUpdate = true;
      }
    });
  }

  // snow drifts over the trench floor (terrain), the deep labs flat
  function drift(c, r, zi) {
    if (zi !== 0 || r < 35) return 0;
    var v = Math.sin(c * 0.31 + r * 0.17) + 0.7 * Math.sin(c * 0.13 - r * 0.41 + 1.3) + 0.4 * Math.sin(c * 0.57 + r * 0.33 + 0.4) - 0.35;
    return Math.max(0, Math.min(1.0, v * 0.45));
  }
  function tint(c, r, zi, g) {
    if (zi !== 0) return ((Math.sin(c * 0.37 + r * 0.21) + Math.sin(c * 0.11 - r * 0.29)) > 0.6) ? ['#9EC6DC', 0.6] : ['#B5D5E6', 0.85];
    var nearWall = false;
    for (var dr = -1; dr <= 0; dr++) for (var dc = -1; dc <= 0; dc++) if (g.at(c + dc, r + dr) === '#') nearWall = true;
    if (nearWall) return ['#C9D8E4', 0.6];
    if (Math.abs(c - 31.5) < 2 && r > 36) return ['#D3DEE7', 0.5];   // the trodden path to the airlock
    return null;
  }

  var WALLS = ['Firn_A', 'Firn_B', 'Firn_C', 'Firn_Lamp', 'Firn_Pipe', 'Firn_Mark', 'Ramp_L', 'Ramp_M', 'Ramp_N', 'Ramp_R', 'CornerF',
    'Fac_A', 'Fac_B', 'Fac_Window', 'Fac_Broken', 'Fac_Vent', 'Fac_Light', 'NameBoard', 'CornerX',
    'S_A', 'S_B', 'S_Window', 'S_Heater', 'S_Notice', 'S_Pipe', 'S_Breach', 'S_Map', 'CornerS',
    'M_A', 'M_B', 'M_Window', 'M_Heater', 'M_Breach', 'M_Menu', 'CornerM',
    'L_A', 'L_B', 'L_Screen', 'L_Panel', 'L_Window', 'CornerL', 'Shell_A', 'Shell_B', 'Shell_Window', 'Shell_Lamp',
    'P_A', 'P_B', 'P_Pipes', 'P_Panel', 'P_Lamp', 'CornerP', 'Cave_A', 'Cave_B', 'Cave_C', 'Cave_Lamp', 'Cave_Cable', 'Cave_Mark', 'CornerC'];
  ['BUNKA', 'BUNKB', 'BUNKC', 'BUNKD', 'COMMS', 'SHAFTK7', 'SCIENCE', 'BOOTROOM', 'MESS', 'COREARCHIVE', 'CRYOLAB', 'VAULT3', 'POWERHALL'].forEach(function (w) { WALLS.push('Sign_' + w); });
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_End', 'Hatch',
    'VaultDoor_Leaf', 'VaultDoor_Leaf_D1', 'VaultDoor_Leaf_D2', 'VaultDoor_Broken', 'Crate_Lid']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    (d.pieces || []).concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });
  var FLAT = Object.keys(SYMBOLS).filter(function (ch) { return SYMBOLS[ch].kind; }).join('');

  IB.registerTheme({
    id: 'arctic', name: 'Kolvane Station K-7', family: 'kit-arctic', prefix: 'KIT_ARCTIC_',
    palette: ['#AEDDF0', '#F5F9FC', '#F2701E', '#5E6974'],
    env: {
      // a pale overcast polar sky over the trench; cold blue-white mist; the deep labs under a 12 m ice ceiling
      sky: ['#A9BBCC', '#E6ECF1'], fog: { color: '#D9E3EB', near: 40, far: 150, tierScale: true }, clouds: false,   // tierScale: low tiers keep 60 % (potato 75 m), always past the start
      sun: [0.3, 0.85, 0.42],
      ceiling: { height: 12, color: '#7BA3BE' }
    },
    floor: { color: '#E6EDF3', trail: '#9FB6C8', outside: '#E6EDF3',
      trailLines: [{ dir: 'x', every: 1, width: 0.03, color: '#8AA2B6', y: 0.008 }] },
    terrain: { height: drift, paint: tint, flat: FLAT, ramp: [1, 4], low: '#E3EBF2', high: '#F7FAFC', patch: '#D7E2EB', top: 1.0 },
    wall: { height: 12, roof: '#F2F6F9', facing: 'open', choose: chooseWall, cols: true, passage: { ch: DOORS, solid: [[2.7, 12]] } },
    symbols: SYMBOLS,
    glow: GLOW,
    // the security cache behind the vault door (game.js placeLoot)
    armory: { tiers: { gray: 30, green: 44, blue: 20, purple: 5, orange: 1 }, gear: { common: 40, rare: 42, epic: 15, legendary: 3 } },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    // shaft K-7: 12 m of ice strata, steel ribs, lamps and depth plates down to the labs
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall'], height: 12, end: 'TrailWall_End' },
    hatch: 'Hatch', stand: 'Crate_B',
    backdrop: { build: build },
    budget: { prop: 2400, landmark: 4000, total: 50000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      arctic: {
        name: 'Kolvane Station K-7',
        intro: 'Something is frozen in the ice under Kolvane. Fight through the buried station, take the shaft down to the deep labs. Blast the vault open for the security cache.',
        zones: [
          // the buried surface works: the trench, the radar dome, the station's upper modules
          { map: 'arctic_1', ceiling: false, waves: [
            [['crawler', 22], ['gunner', 8], ['drone', 3]],
            [['crawler', 18], ['bomber', 2], ['gunner', 9], ['blader', 6], ['soldier', 5]],
            [['crawler', 8], ['drone', 6], ['gunner', 6], ['soldier', 7]],
            [['crawler', 22], ['bomber', 2], ['gunner', 10], ['drone', 6], ['soldier', 9], ['blader', 6]]] },
          // the deep labs: core archive, cryo lab, vault, generator hall, the relic's cavern
          { map: 'arctic_2', waves: [
            [['crawler', 18], ['gunner', 8], ['drone', 3], ['soldier', 7]],
            [['crawler', 9], ['bomber', 2], ['gunner', 7], ['blader', 6]],
            [['crawler', 18], ['drone', 6], ['gunner', 8], ['bomber', 2], ['soldier', 7], ['blader', 6]],
            [['crawler', 12], ['gunner', 10], ['bomber', 2], ['drone', 4], ['soldier', 7]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
