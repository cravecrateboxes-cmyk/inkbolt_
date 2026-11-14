/* Theme: Abyssal Station Thalassa (kit-seabase) -- a deep-sea research station on the seabed, far below the depth
   anything lives at. Cool steel and teal inside with yellow / orange safety accents; outside the dark teal-black
   water, sediment and rock, distant station pods and pylon beacons, drifting marine snow. Two zones:
   1 Docking & Service Level (72 m): the arrival lock with the decompression chamber, the dive lockers, the pump room,
     the landmark MOON POOL dock (the submersible DSV TRIDENT floating in its cradle under the portal gantry, winches,
     umbilical spools, the work ROV, cargo baskets; the dock control cabin up on a gallery deck with a stair), the
     FLOODED main passage and ballast passage (shin-deep standing water held back by the door coamings, flood barriers
     and sandbags as cover, leaking pipes, emergency lights), the ballast tank room, the cargo hold, the battery room
     and the exit lock. Portholes in the outer hull look into the dark water.
   2 The Research Ring (71 m): the landmark observation hub under a glass dome (survey table with a turning
     holographic seabed relief, a mezzanine on three sides, two stairs) inside a ring corridor; the west and east
     GLASS OBSERVATION CHAMBERS (half-round glass rooms with a glass dome) bulging from the hull into the seabed; glass-
     fronted labs at the ring ends (sample lab, sonar room, tank lab, geology), the core store, comms, the flooded wet
     lab, the instrument bay.
   Built by blender/fam_kit_seabase.py (sb_*.py); zone layers by tools/seabase_zones.py.

   A zone file has the floor plan and these layers: "@layer 0.01" (floor marks), "@layer 0.22" (codes, never symbols:
   ~ flood water, & the moon pool's water, wall art on wall cells; '%' at (0, 0) in the research ring), "@layer 3.2"
   (gallery / mezzanine deck) and one layer per ceiling height ("@layer 4.5", "@layer 6", "@layer 7", "@layer 7.5":
   ceiling tiles, the hub's glass dome).
   Floor plan:  D watertight bulkhead door [3,2] (in 2-cell walls; the cells count as wall, solid above 2.7 m; a
     walkable 0.3 m coaming)   M moon pool [12,10] (+ the submersible and the gantry)   W winch [2,2]
     U umbilical spool [2,2]   V work ROV on its stand [2,2]   K cargo basket [2,2]   C crate stack [2,2]
     c hard case / drum   k tool cart   g gas bottles (back to the wall)   L dive locker [2,1] (against a wall)
     T scuba tank rack [2,1] (against a wall)   y dive gear table [2,1]   B bench [2,1]   p pump set [3,2]
     m manifold [4,1] (against a wall)   t HP air receiver [2,2]   H ballast tank [6,3]   x compressor [2,2]
     j battery rack [3,2]   e electrical cabinet [2,1] (against a wall)   d decompression chamber [5,3] (against a
     wall)   b steel flood barrier (runs)   s sandbag wall (runs)   i floor pipe run (runs)   O column
     N stair [2,7] rising north to the 3.2 m deck   I deck column
     A west observation chamber [12,25] (hull on its east side)   Z east observation chamber [12,25]
     Y hub survey table [9,9]   q glass partition (runs)   f sliding lab door [3,1] (in a glass run)
     R sample tank [2,2]   Q tank bank [4,1] (against a wall)   l lab bench [2,1]   n core rack [2,1] (against a
     wall)   v sonar desk [3,2] (against a wall)   z comms rack [2,1] (against a wall)   X workstation [2,1]
     w chair   F sample fridge
   Deck (3.2): u deck   r guard rail (runs)   J dock control cabin [6,4] (faces south)
   Floor marks (0.01): / hazard stripes   ! FLOOD ZONE stencil [3,1]   ; drain
   Ceilings: = steel deckhead   + caged lamp   - pipe run (runs)   " white panel   ' light panel
     @ the hub's glass dome [17,17] (on the 7 m layer)
   Codes (0.22): ~ flood water   & moon pool water   on wall cells: o porthole (outer hull only)  1 leaking pipe
     2 emergency light   3 DANGER HIGH PRESSURE   4 FLOOD stencil   5 valve panel   6 7 deck / ring signs
     8 fire point   9 sonar screen   0 THALASSA logo
   The wall chooser: service steel in zone 1, research panels in zone 2; the outer hull faces the observation
   notches (floodlights on the notch walls), and the zone's outer ring next to a chamber stays open to the sea. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var ART = {
    S: { o: 'WS_Port', '1': 'WS_Leak', '2': 'WS_Beacon', '3': 'WS_Warn', '4': 'WS_Flood', '5': 'WS_Valve', '6': 'WS_SignDock', '7': 'WS_SignPump', '8': 'WS_Fire' },
    R: { o: 'WR_Port', '1': 'WR_Leak', '2': 'WR_Beacon', '4': 'WR_Flood', '6': 'WR_SignHub', '7': 'WR_SignObs', '8': 'WR_Fire', '9': 'WR_Screen', '0': 'WR_Logo' }
  };
  var PORTS = { WS_Port: 1, WR_Port: 1 };
  var CHAMBER = 'AZ', DOORS = 'D';
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var NB = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]];
  function codesOf(grid) {
    if (grid._sbK === undefined) {
      grid._sbK = null;
      (grid.layers || []).forEach(function (l) { if (Math.abs(l.y - 0.22) < 0.01) grid._sbK = l; });
    }
    return grid._sbK;
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (DOORS.indexOf(grid.at(c, r)) >= 0) return null;   // the bulkhead draws its own frame and header
    var K = codesOf(grid), S = K && K.at(0, 0) === '%' ? 'R' : 'S', k;
    var outer = c === 0 || r === 0 || c === grid.w - 1 || r === grid.h - 1;
    var sea = false;
    for (k = 0; k < NB.length; k++) if (CHAMBER.indexOf(grid.at(c + NB[k][0], r + NB[k][1])) >= 0) sea = true;
    if (sea && outer) return null;   // open to the sea round the observation chambers
    if (face === 'corner' || face === 'none' || !FACE[face]) return sea ? 'CornerH' : 'Corner' + S;
    var d = FACE[face];
    if (CHAMBER.indexOf(grid.at(c + d[0], r + d[1])) >= 0) {   // the outer hull seen from a notch
      var e = Math.min(c, grid.w - 1 - c);
      return (face === 'N' || face === 'S') && (e === 3 || e === 6) ? 'WH_Lamp' : 'WH';
    }
    var piece = K && ART[S][K.at(c, r)];
    if (!piece || (PORTS[piece] && !outer)) return 'W' + S;
    return piece;
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }
  function run(pieces) { return { pieces: pieces, collide: false, rotate: 'run' }; }
  function cover(o) { o.kind = 'cover'; return o; }

  var SYMBOLS = {
    // ---- docking and service level
    'D': { size: [3, 2], pieces: ['Bulkhead'], orient: 'span', kind: 'wall' },
    'M': cover({ size: [12, 10], pieces: ['Landmark_MoonPool'], face: 0, with: { Landmark_MoonPool: ['MoonPool_Sub', 'MoonPool_Crane'] } }),
    'W': cover({ size: [2, 2], pieces: ['Winch'], flip: true }),
    'U': cover({ size: [2, 2], pieces: ['Spool'], flip: true }),
    'V': cover({ size: [2, 2], pieces: ['ROV'], flip: true }),
    'K': cover({ size: [2, 2], pieces: ['Basket'], flip: true }),
    'C': cover({ size: [2, 2], pieces: ['CrateStack'], flip: true }),
    'c': cover({ pieces: ['Crate_A', 'Crate_B', 'Crate_C', 'Crate_A'], rotate: 'random90' }),
    'k': cover({ pieces: ['Cart'], rotate: 'random90' }),
    'g': cover({ pieces: ['Cylinders'], rotate: 'edge' }),
    'L': cover({ size: [2, 1], pieces: ['DiveLocker'], orient: 'wall' }),
    'T': cover({ size: [2, 1], pieces: ['TankRack'], orient: 'wall' }),
    'y': cover({ size: [2, 1], pieces: ['GearTable'], flip: true }),
    'B': cover({ size: [2, 1], pieces: ['Bench'], flip: true }),
    'p': cover({ size: [3, 2], pieces: ['Pump'], flip: true }),
    'm': cover({ size: [4, 1], pieces: ['Manifold'], orient: 'wall' }),
    't': cover({ size: [2, 2], pieces: ['Tank'], flip: true }),
    'H': cover({ size: [6, 3], pieces: ['BallastTank'], flip: true }),
    'x': cover({ size: [2, 2], pieces: ['Compressor'], flip: true }),
    'j': cover({ size: [3, 2], pieces: ['BatteryRack'], flip: true }),
    'e': cover({ size: [2, 1], pieces: ['Cabinet'], orient: 'wall' }),
    'd': cover({ size: [5, 3], pieces: ['DecoChamber'], orient: 'wall' }),
    'b': cover({ pieces: ['Barrier_A'], rotate: 'run' }),
    's': cover({ pieces: ['Barrier_B'], rotate: 'run' }),
    'i': cover({ pieces: ['PipeRun'], rotate: 'run' }),
    'O': cover({ pieces: ['Column'] }),
    'N': { size: [2, 7], pieces: ['Stair'], face: 0, kind: 'step' },
    'I': cover({ pieces: ['DeckColumn'] }),
    // ---- research ring
    'A': cover({ size: [12, 25], pieces: ['Landmark_Obs'], face: 0, with: { Landmark_Obs: ['Obs_Seabed'] } }),
    'Z': cover({ size: [12, 25], pieces: ['Landmark_Obs'], face: Math.PI, with: { Landmark_Obs: ['Obs_Seabed'] } }),
    'Y': cover({ size: [9, 9], pieces: ['Landmark_Hub'], face: 0 }),
    'q': { pieces: ['GlassHalf'], full: 'GlassFull', links: 'qf#', post: 'GlassPost', kind: 'wall' },
    'f': { size: [3, 1], pieces: ['GlassDoor'], orient: 'span', kind: 'wall' },
    'R': cover({ size: [2, 2], pieces: ['SampleTank'] }),
    'Q': cover({ size: [4, 1], pieces: ['TankBank'], orient: 'wall' }),
    'l': cover({ size: [2, 1], pieces: ['LabBench_A', 'LabBench_B'], flip: true }),
    'n': cover({ size: [2, 1], pieces: ['CoreRack'], orient: 'wall' }),
    'v': cover({ size: [3, 2], pieces: ['SonarDesk'], orient: 'wall' }),
    'z': cover({ size: [2, 1], pieces: ['CommsRack'], orient: 'wall' }),
    'X': cover({ size: [2, 1], pieces: ['Workstation'], flip: true }),
    'w': cover({ pieces: ['Chair'], rotate: 'random90' }),
    'F': cover({ pieces: ['LabFridge'], rotate: 'edge' }),
    // ---- gallery / mezzanine deck (layer 3.2)
    'u': { deck: { thick: 0.4, color: '#5D6B75', edge: '#F2C230', under: '#4F5C66', with: '*' } },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    'J': cover({ size: [6, 4], pieces: ['DockCabin'], face: 0 }),
    // ---- floor marks (layer 0.01)
    '/': flat(['F_Hazard']), '!': { size: [3, 1], pieces: ['F_Flood'], collide: false, face: 0 }, ';': flat(['F_Drain']),
    // ---- ceilings (their layers' heights)
    '=': flat(['C_Deck']), '+': flat(['C_DeckLamp']), '-': run(['C_DeckPipe']),
    '"': flat(['C_Panel']), "'": flat(['C_PanelLight']),
    '@': { size: [17, 17], pieces: ['HubDome'], collide: false, face: 0 }
  };

  // glow companions (zones.js theme.glow): glass drawn additive (the sea and the rooms behind show through with a
  // teal sheen), lamps / screens / LEDs unlit; emergency lights flash in two groups, leaks spray, the hologram turns
  var ADD = 'add';
  var GLOW = {
    WS_Port: { piece: 'WS_Port_Glass', blend: ADD }, WR_Port: { piece: 'WR_Port_Glass', blend: ADD },
    TrailWall_B: { piece: 'TrailWall_B_Glass', blend: ADD },
    WS_Beacon: [{ piece: 'Beacon_Lamp', groups: 2 }, { piece: 'Beacon_Ray', groups: 2, blend: ADD }],
    WR_Beacon: [{ piece: 'Beacon_Lamp', groups: 2 }, { piece: 'Beacon_Ray', groups: 2, blend: ADD }],
    WS_Leak: [{ piece: 'WS_Leak_Spray0', blend: ADD }, { piece: 'WS_Leak_Spray1', blend: ADD }],
    WR_Leak: [{ piece: 'WR_Leak_Spray0', blend: ADD }, { piece: 'WR_Leak_Spray1', blend: ADD }],
    WR_Screen: { piece: 'WR_Screen_LED' }, WH_Lamp: [{ piece: 'WH_Lamp_LED' }, { piece: 'WH_Lamp_Beam', blend: ADD }],
    Bulkhead: { piece: 'Bulkhead_LED' },
    GlassFull: { piece: 'GlassFull_Glass', blend: ADD }, GlassHalf: { piece: 'GlassHalf_Glass', blend: ADD },
    GlassDoor: { piece: 'GlassDoor_Glass', blend: ADD },
    C_DeckLamp: { piece: 'C_DeckLamp_LED' }, C_PanelLight: { piece: 'C_PanelLight_LED' },
    Landmark_MoonPool: { piece: 'Landmark_MoonPool_LED' }, MoonPool_Sub: { piece: 'MoonPool_Sub_LED' },
    MoonPool_Crane: { piece: 'MoonPool_Crane_LED' }, ROV: { piece: 'ROV_LED' },
    BatteryRack: { piece: 'BatteryRack_LED' }, Cabinet: { piece: 'Cabinet_LED' }, DecoChamber: { piece: 'DecoChamber_LED' },
    DockCabin: [{ piece: 'DockCabin_LED' }, { piece: 'DockCabin_Glass', blend: ADD }],
    Landmark_Obs: [{ piece: 'Landmark_Obs_Glass', blend: ADD }, { piece: 'Landmark_Obs_LED' }], Obs_Seabed: { piece: 'Obs_Seabed_LED' },
    HubDome: [{ piece: 'HubDome_Glass', blend: ADD }, { piece: 'HubDome_LED' }],
    Landmark_Hub: [{ piece: 'Landmark_Hub_LED' }, { piece: 'Hub_Holo', spin: true, blend: ADD }],
    SampleTank: { piece: 'SampleTank_Glass', blend: ADD }, TankBank: { piece: 'TankBank_Glass', blend: ADD },
    SonarDesk: { piece: 'SonarDesk_LED' }, CommsRack: { piece: 'CommsRack_LED' }, Workstation: { piece: 'Workstation_LED' },
    LabFridge: { piece: 'LabFridge_Glass', blend: ADD }
  };

  // ---------------------------------------------------------------- the sea outside, the water inside (backdrop.build)
  var WATER = { '~': { y: 0.22, c: '#1C6A73', a: 0.5, k: 1.0 }, '&': { y: 0.2, c: '#0B3F4A', a: 0.72, k: 0.55 } };
  var SNOW = '#A9D3D2';
  function waterMat(THREE, W, U) {
    var m = new THREE.MeshBasicMaterial({ color: W.c, transparent: true, opacity: W.a, depthWrite: false });
    m.onBeforeCompile = function (sh) {
      sh.uniforms.uT = U; sh.uniforms.uK = { value: W.k };
      sh.vertexShader = 'varying vec2 vWp;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvWp = position.xz;');
      sh.fragmentShader = 'uniform float uT;\nuniform float uK;\nvarying vec2 vWp;\n' + sh.fragmentShader.replace('#include <color_fragment>',
        '#include <color_fragment>\n' +
        'vec2 q = vWp * uK;\n' +
        'float w1 = sin(q.x * 1.7 + uT * 0.8 + sin(q.y * 0.8 + uT * 0.45) * 1.6);\n' +
        'float w2 = sin(q.y * 1.3 - uT * 0.65 + sin(q.x * 0.6 - uT * 0.35) * 1.4);\n' +
        'float kk = w1 * w2;\n' +
        'float hi = smoothstep(0.58, 0.64, kk), lo = smoothstep(-0.5, -0.62, kk);\n' +
        'diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.72, 0.95, 0.96), hi * 0.75);\n' +
        'diffuseColor.rgb *= 1.0 - lo * 0.3;\n' +
        'diffuseColor.a = mix(diffuseColor.a, 0.9, hi * 0.65);');
    };
    m.customProgramCacheKey = function () { return 'sbwater'; };
    return m;
  }
  function cellRects(L, ch) {   // greedy rectangles of one code in a layer grid
    var used = {}, out = [];
    for (var r = 0; r < L.h; r++) for (var c = 0; c < L.w; c++) {
      if (used[r * L.w + c] || L.at(c, r) !== ch) continue;
      var w = 1; while (c + w < L.w && !used[r * L.w + c + w] && L.at(c + w, r) === ch) w++;
      var h = 1, ok = true;
      while (ok && r + h < L.h) { for (var k = 0; k < w; k++) if (used[(r + h) * L.w + c + k] || L.at(c + k, r + h) !== ch) { ok = false; break; } if (ok) h++; }
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) used[(r + y) * L.w + c + x] = 1;
      out.push([c, r, w, h]);
    }
    return out;
  }
  // the facility's footprint (zones, trails, the exit room): the sea is everywhere else
  function inside(level, x, z, pad) {
    for (var i = 0; i < level.zones.length; i++) {
      var Z = level.zones[i];
      if (x > Z.ox - pad && x < Z.ox + Z.w + pad && z > Z.oz - pad && z < Z.oz + Z.h + pad) return true;
    }
    for (i = 0; i < level.trails.length; i++) {
      var T = level.trails[i];
      if (Math.abs(x - T.x) < 3 + pad && z > Math.min(T.z0, T.z1) - pad && z < Math.max(T.z0, T.z1) + pad) return true;
    }
    var Hh = level.hatch;
    return !!(Hh && Math.abs(x - Hh.x) < 4 + pad && z > Hh.z - 4 - pad && z < Hh.z0 + pad);
  }

  function buildSea(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var g = api.geo, hash = api.hash, Zs = level.zones;
    var X0 = 1e9, X1 = -1e9, Zmin = 1e9, Zmax = -1e9;
    Zs.forEach(function (Z) { X0 = Math.min(X0, Z.ox); X1 = Math.max(X1, Z.ox + Z.w); Zmin = Math.min(Zmin, Z.oz); Zmax = Math.max(Zmax, Z.oz + Z.h); });
    level.trails.forEach(function (T) { Zmin = Math.min(Zmin, T.z1); });
    if (level.hatch) Zmin = Math.min(Zmin, level.hatch.z - 5);
    var CX = (X0 + X1) / 2, CZ = (Zmin + Zmax) / 2;
    // ---- the seabed: a heightfield, flat round the station, rolling further out, a trench falling away east
    function dOut(x, z) {   // distance outside the footprint rectangles (0 inside)
      var d = 1e9;
      Zs.forEach(function (Z) { var dx = Math.max(Z.ox - x, 0, x - Z.ox - Z.w), dz = Math.max(Z.oz - z, 0, z - Z.oz - Z.h); d = Math.min(d, Math.hypot(dx, dz)); });
      level.trails.forEach(function (T) { var dx = Math.max(Math.abs(x - T.x) - 3, 0), dz = Math.max(Math.min(T.z0, T.z1) - z, 0, z - Math.max(T.z0, T.z1)); d = Math.min(d, Math.hypot(dx, dz)); });
      if (level.hatch) { var H = level.hatch, dx = Math.max(Math.abs(x - H.x) - 4, 0), dz = Math.max(H.z - 4 - z, 0, z - H.z0); d = Math.min(d, Math.hypot(dx, dz)); }
      return d;
    }
    function ground(x, z) {
      var d = dOut(x, z), t = Math.min(1, Math.max(0, (d - 2) / 26));
      var n = Math.sin(x * 0.045 + Math.sin(z * 0.03) * 2) * 1.6 + Math.sin(z * 0.06 + x * 0.02) * 1.1 + Math.sin(x * 0.13 - z * 0.11) * 0.5;
      var trench = Math.max(0, x - X1 - 30) * 0.32;
      return -0.06 + t * (n + 0.8) - trench * Math.min(1, t * 2);
    }
    var S = 8, R0 = 190, xs = [], zs = [];
    for (var x = CX - R0; x <= CX + R0 + 0.01; x += S) xs.push(x);
    for (var z = CZ - R0; z <= CZ + R0 + 0.01; z += S) zs.push(z);
    var hs = zs.map(function (zz) { return xs.map(function (xx) { return ground(xx, zz); }); });
    var C1 = new THREE.Color('#2E3C3A'), C2 = new THREE.Color('#3B4743'), C3 = new THREE.Color('#1D2A2C');
    var b0 = g.pos.length / 3;
    for (var j = 0; j < zs.length; j++) for (var i = 0; i < xs.length; i++) {
      var hx = hs[j][Math.min(xs.length - 1, i + 1)] - hs[j][Math.max(0, i - 1)], hz = hs[Math.min(zs.length - 1, j + 1)][i] - hs[Math.max(0, j - 1)][i];
      var nl = Math.hypot(hx, 2 * S, hz), y = hs[j][i];
      var col = (y < -6 ? C3 : hash(i, j) < 0.5 ? C1 : C2).clone();
      g._vert(xs[i], y, zs[j], -hx / nl, 2 * S / nl, -hz / nl, col);
    }
    var NX = xs.length;
    for (j = 0; j < zs.length - 1; j++) for (i = 0; i < NX - 1; i++) {
      var a = b0 + j * NX + i, b = a + 1, c = a + NX, d = c + 1;
      g.idx.push(a, c, b, b, c, d);
    }
    // ---- rocks, spires, distant station pods on legs, pylons, a pipeline: out in the murk
    var PL = [];
    function place(n, x, z, yaw, s) { if (dOut(x, z) < 8) return; PL.push([n, x, z]); api.add(n, x, ground(x, z) - 0.2, z, yaw, s); }
    for (var k = 0; k < 26; k++) {
      var ang = hash(k, 31) * 6.283, rr = 24 + hash(k, 32) * 95;
      place(k % 5 === 0 ? 'BD_Spire' : k % 2 ? 'BD_Rock_A' : 'BD_Rock_B', CX + Math.cos(ang) * rr * 0.75, CZ + Math.sin(ang) * rr, hash(k, 33) * 6.28, 0.8 + hash(k, 34) * 0.9);
    }
    [[-70, 20, 0.4], [85, -40, 1.2], [-55, -110, 2.1], [60, 95, 0.9]].forEach(function (p, q) { place('BD_Pod', CX + p[0], CZ + p[1], p[2], 1.0 + 0.2 * q); });
    [[-40, -30], [38, 30], [-30, 70], [45, -95], [-80, -60]].forEach(function (p, q) { place('BD_Pylon', CX + p[0], CZ + p[1], q * 0.7, 1.0); });
    [[-34, 4, 0.3], [-44, 9, 0.3], [30, -60, 1.4], [33, -70, 1.4]].forEach(function (p) { place('BD_Pipe', CX + p[0], CZ + p[1], p[2], 1.0); });
    if (!THREE || !level.root) return;
    // ---- distant lights (unlit sprites through the murk): pod window bands, pylon beacons, seabed markers
    var cv = typeof document !== 'undefined' && document.createElement('canvas');
    var tex = null;
    if (cv) {
      cv.width = cv.height = 32;
      var cx2 = cv.getContext('2d'), gr = cx2.createRadialGradient(16, 16, 0, 16, 16, 16);
      gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.35, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
      cx2.fillStyle = gr; cx2.fillRect(0, 0, 32, 32);
      tex = new THREE.CanvasTexture(cv);
    }
    var lp = [], lc = [], warm = new THREE.Color('#FFD9A0'), cold = new THREE.Color('#9FF2FF'), red = new THREE.Color('#FF6A4A');
    PL.forEach(function (p, q) {
      var y0 = ground(p[1], p[2]);
      if (p[0] === 'BD_Pod') for (var w = 0; w < 4; w++) { lp.push(p[1] - 3 + w * 2, y0 + 3.9, p[2] + 2.3); lc.push(warm.r, warm.g, warm.b); }
      else if (p[0] === 'BD_Pylon') { lp.push(p[1], y0 + 11.6, p[2]); lc.push(red.r, red.g, red.b); }
      else if (q % 3 === 0) { lp.push(p[1] + 2, y0 + 0.6, p[2] + 1); lc.push(cold.r, cold.g, cold.b); }
    });
    var lg = new THREE.BufferGeometry();
    lg.setAttribute('position', new THREE.Float32BufferAttribute(lp, 3));
    lg.setAttribute('color', new THREE.Float32BufferAttribute(lc, 3));
    var lm = new THREE.PointsMaterial({ size: 2.2, map: tex, vertexColors: true, transparent: true, opacity: 0.85, depthWrite: false, fog: false, blending: THREE.AdditiveBlending });
    var lights = new THREE.Points(lg, lm);
    lights.frustumCulled = false;
    level.root.add(lights);
    // ---- marine snow: drifting motes in the sea round the station, in the notches and over the hub dome
    var SN = [], sp = [];
    function snowBox(x0, x1, y0, y1, z0, z1, n, reject) {
      for (var q = 0, tries = 0; q < n && tries < n * 6; tries++) {
        var sx = x0 + Math.random() * (x1 - x0), sz = z0 + Math.random() * (z1 - z0);
        if (reject && reject(sx, sz)) continue;
        SN.push({ x: sx, z: sz, y0: y0, y1: y1, ph: Math.random() * 6.28, v: 0.08 + Math.random() * 0.12 });
        sp.push(sx, y0 + Math.random() * (y1 - y0), sz); q++;
      }
    }
    Zs.forEach(function (Z) {
      // a band just outside each zone, and every notch of sea (chamber prefab blocks) inside it
      snowBox(Z.ox - 26, Z.ox + Z.w + 26, 0.3, 14, Z.oz - 10, Z.oz + Z.h + 10, 420, function (x, z) { return inside(level, x, z, 0.6); });
      var seen = {};
      for (var r2 = 0; r2 < Z.h; r2++) for (var c2 = 0; c2 < Z.w; c2++) {
        var ch = Z.grid.at(c2, r2); if (CHAMBER.indexOf(ch) < 0 || seen[ch + (c2 < Z.w / 2)]) continue;
        seen[ch + (c2 < Z.w / 2)] = 1;
        var hx = Z.ox + c2 + (ch === 'A' ? 12 : 0), hz = Z.oz + r2 + 12.5;   // the glass D's centre on the hull line
        snowBox(Z.ox + c2 + 0.2, Z.ox + c2 + 11.8, 0.3, 9, Z.oz + r2 + 0.2, Z.oz + r2 + 24.8, 120, function (x, z) { return Math.hypot(x - hx, z - hz) < 10.0; });
      }
      (Z.grid.layers || []).forEach(function (L) {
        cellRects(L, '@').forEach(function (R) { snowBox(Z.ox + R[0], Z.ox + R[0] + R[2], L.y + 4.6, L.y + 14, Z.oz + R[1], Z.oz + R[1] + R[3], 90, null); });
      });
    });
    var sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3));
    var snow = new THREE.Points(sg, new THREE.PointsMaterial({ size: 0.07, color: SNOW, map: tex, transparent: true, opacity: 0.6, depthWrite: false }));
    snow.frustumCulled = false;
    level.root.add(snow);
    // ---- flood water and the moon pool (per zone, shown with the zone): one InstancedMesh per kind and zone
    var U = { value: 0 };
    Zs.forEach(function (Z) {
      var L = null;
      (Z.grid.layers || []).forEach(function (l) { if (Math.abs(l.y - 0.22) < 0.01) L = l; });
      if (!L) return;
      Object.keys(WATER).forEach(function (ch) {
        var W = WATER[ch], P = [], I = [];
        cellRects(L, ch).forEach(function (R) {
          var x0 = Z.ox + R[0], z0 = Z.oz + R[1], x1 = x0 + R[2], z1 = z0 + R[3], n = P.length / 3;
          P.push(x0, W.y, z0, x1, W.y, z0, x1, W.y, z1, x0, W.y, z1);
          I.push(n, n + 2, n + 1, n, n + 3, n + 2);
        });
        if (!I.length) return;
        var wg = new THREE.BufferGeometry();
        wg.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
        wg.setIndex(I);
        wg.computeBoundingSphere();
        var mesh = new THREE.InstancedMesh(wg, waterMat(THREE, W, U), 1);
        mesh.setMatrixAt(0, new THREE.Matrix4());
        mesh.renderOrder = 3;
        mesh.name = 'SeabaseWater';
        Z.group.add(mesh);
        (Z.water || (Z.water = [])).push({ ch: ch, L: L });
      });
    });
    // ---- wading ripples: rings spread from the player's feet and from robots walking in the flood water
    var RN = 14, rings = [], rg = new THREE.RingGeometry(0.82, 1.0, 20);
    rg.rotateX(-Math.PI / 2);
    for (k = 0; k < RN; k++) {
      var rm = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({ color: '#CFF6F4', transparent: true, opacity: 0, depthWrite: false }));
      rm.visible = false; rm.renderOrder = 4; rm.frustumCulled = false;
      level.root.add(rm);
      rings.push({ m: rm, t: 9 });
    }
    var rk = 0;
    function wet(x, z) {
      var zi = IB.Zones.zoneAt(level, x, z); if (zi < 0) return null;
      var Z = Zs[zi], c = Math.floor(x - Z.ox), r = Math.floor(z - Z.oz);
      for (var q = 0; q < (Z.water || []).length; q++) if (Z.water[q].ch === '~' && Z.water[q].L.at(c, r) === '~') return WATER['~'].y;
      return null;
    }
    function ripple(x, y, z, s) { var R = rings[rk++ % RN]; R.t = 0; R.s = s; R.m.position.set(x, y + 0.004, z); R.m.visible = true; }
    var pT = 0, robT = 0;
    // ---- the glows' life: emergency lights flash in two groups, leaks spray, the hub's hologram turns and glitches
    var beac = [], spray = [], holo = [];
    (level.glows || []).forEach(function (G) {
      if (/^Beacon_/.test(G.piece)) beac.push(G);
      else if (/_Spray\d$/.test(G.piece)) spray.push(G);
      else if (G.piece === 'Hub_Holo') holo.push(G);
    });
    var sPos = snow.geometry.attributes.position;
    api.tick(function (dt, t) {
      U.value = t;
      var i2, b;
      for (i2 = 0; i2 < beac.length; i2++) { b = beac[i2]; b.mesh.visible = ((t * 1.25 + b.group * 0.5) % 1) < 0.42; }
      for (i2 = 0; i2 < spray.length; i2++) { b = spray[i2]; b.mesh.visible = (Math.floor(t * 9 + (/0$/.test(b.piece) ? 0 : 1)) % 2) === 0; }
      for (i2 = 0; i2 < holo.length; i2++) {
        b = holo[i2]; b.mesh.rotation.set(0, (b.mesh.userData.yaw0 || 0) + t * 0.3, 0);
        b.mesh.visible = ((t * 0.5 + i2 * 0.3) % 5.0) > 0.07;
      }
      lm.opacity = 0.7 + 0.15 * Math.sin(t * 1.7);
      for (i2 = 0; i2 < SN.length; i2++) {
        var Sx = SN[i2], yy = sPos.getY(i2) - Sx.v * dt;
        if (yy < Sx.y0) yy = Sx.y1;
        sPos.setXYZ(i2, Sx.x + Math.sin(t * 0.3 + Sx.ph) * 0.35, yy, Sx.z + Math.cos(t * 0.23 + Sx.ph) * 0.35);
      }
      sPos.needsUpdate = true;
      for (i2 = 0; i2 < RN; i2++) {
        var R = rings[i2]; if (!R.m.visible) continue;
        R.t += dt;
        var s2 = R.s * (0.25 + R.t * 1.1);
        R.m.scale.set(s2, 1, s2);
        R.m.material.opacity = Math.max(0, 0.55 * (1 - R.t / 1.1));
        if (R.t > 1.1) R.m.visible = false;
      }
      var G = IB.Game, p = G && G.player;
      if (p && G.level === level) {
        pT -= dt;
        var wy = wet(p.x, p.z), sp2 = Math.hypot(p.vx || 0, p.vz || 0);
        if (wy !== null && p.y < 0.35 && sp2 > 0.6 && pT <= 0) { ripple(p.x, wy, p.z, 0.9); pT = 0.3; }
        robT -= dt;
        if (robT <= 0 && IB.AI && IB.AI.robots) {
          robT = 0.45;
          var n2 = 0;
          for (i2 = 0; i2 < IB.AI.robots.length && n2 < 3; i2++) {
            var rb = IB.AI.robots[i2];
            if (!rb.on || rb.type === 'drone' || rb.type === 'hawk' || Math.abs(rb.x - p.x) + Math.abs(rb.z - p.z) > 30) continue;
            var ry = wet(rb.x, rb.z); if (ry === null || (rb.fy || 0) > 0.35 || Math.hypot(rb.vx || 0, rb.vz || 0) < 0.3) continue;
            ripple(rb.x, ry, rb.z, 1.1); n2++;
          }
        }
      }
    });
  }

  var OTHER = ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch',
    'BD_Rock_A', 'BD_Rock_B', 'BD_Spire', 'BD_Pod', 'BD_Pylon', 'BD_Pipe'];
  var PIECES = ['WS', 'WR', 'WH', 'CornerS', 'CornerR', 'CornerH', 'WH_Lamp'].concat(OTHER);
  Object.keys(ART).forEach(function (S) { Object.keys(ART[S]).forEach(function (k) { if (PIECES.indexOf(ART[S][k]) < 0) PIECES.push(ART[S][k]); }); });
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
    if (d.with) Object.keys(d.with).forEach(function (k) { d.with[k].forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); }); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'seabase', name: 'Abyssal Station Thalassa', family: 'kit-seabase', prefix: 'KIT_SEABASE_',
    palette: ['#0D7A76', '#6FE3D9', '#F2C230', '#7D8E99'],
    // no sky: the deep water is a dark teal-black clear colour and fog, so the seabed fades out a few dozen metres
    // past the glass; the trail tube and the exit room have a 4.6 m deckhead (the zones bring their own ceilings)
    env: {
      sky: null, clear: '#041519', fog: { color: '#072830', near: 30, far: 108 }, clouds: false,
      sun: [0.3, 0.9, 0.32],
      ceiling: { height: 4.6, color: '#6B7A84' }
    },
    floor: {
      color: '#56646E', trail: '#56646E', outside: '#2E3C3A',
      lines: [{ dir: 'x', every: 2, width: 0.025, color: '#46525C', y: 0.008 }, { dir: 'z', every: 2, width: 0.025, color: '#46525C', y: 0.0105 }]
    },
    wall: { height: 7.5, roof: '#2E3A42', facing: 'open', choose: chooseWall, passage: { ch: DOORS, solid: [[2.7, 7.5]] } },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_B'], height: 4.6 },
    hatch: 'Hatch', stand: 'Crate_A',
    backdrop: { build: buildSea },
    budget: { prop: 2800, landmark: 4000, total: 52000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      seabase: {
        name: 'Abyssal Station Thalassa',
        intro: 'Robots have seized the deep research station. Wade through the flooded service level, then take back the research ring and its glass observation chambers.',
        zones: [
          // Docking & Service Level: the moon pool dock, the flooded passages, pumps and ballast tanks
          { map: 'seabase_1', ceiling: false, floor: { color: '#5A6872', lines: [{ dir: 'x', every: 2, width: 0.025, color: '#4B5862', y: 0.008 }, { dir: 'z', every: 2, width: 0.025, color: '#4B5862', y: 0.0105 }] },
            waves: [
              [['crawler', 22], ['gunner', 10], ['drone', 4]],
              [['crawler', 12], ['bomber', 2], ['gunner', 7], ['blader', 5], ['soldier', 4]],
              [['crawler', 12], ['drone', 7], ['gunner', 7], ['soldier', 7], ['blader', 2]],
              [['crawler', 14], ['drone', 4], ['bomber', 2], ['gunner', 9], ['soldier', 6], ['blader', 4]],
              [['crawler', 14], ['gunner', 7], ['soldier', 5], ['blader', 3]]] },
          // The Research Ring: the hub under its dome, the ring corridor, the observation chambers, the labs
          { map: 'seabase_2', ceiling: false, floor: { color: '#B4C0C6', lines: [{ dir: 'x', every: 1, width: 0.02, color: '#9EABB2', y: 0.008 }, { dir: 'z', every: 1, width: 0.02, color: '#9EABB2', y: 0.0105 }] },
            waves: [
              [['crawler', 20], ['gunner', 10], ['soldier', 7]],
              [['crawler', 12], ['drone', 6], ['gunner', 8], ['blader', 6]],
              [['crawler', 14], ['bomber', 2], ['gunner', 9], ['soldier', 8], ['blader', 4]],
              [['crawler', 14], ['drone', 6], ['gunner', 10], ['soldier', 7], ['blader', 5]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
