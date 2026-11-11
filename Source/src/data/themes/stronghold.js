/* Theme: Fort Highwatch (kit-stronghold) -- a remote military stronghold built and carved into the west face of a
   very tall, wide mountain massif, late afternoon turning to sunset. Two zones; player travel is north.
   1 The outer works (72 x 64): a broad ledge on the cliff. The cliff rises along the east edge (bunker doors, gun
     casemates and vents set into it) and closes the south-east; the rock spur with the fortified gate (concrete blast
     portal, two bastions, HIGHWATCH lettering) closes the north. A concrete parapet runs along the west edge and the
     ends of the ledge over a sheer drop. Terrace 1 (3.6 m) fills the north-east against the cliff and terrace 2
     (7.2 m) sits on its north part, each reached by a switchback (a 1.8 m flight, a landing, a flight back); a long
     ramp climbs terrace 1 from the south. On the ledge: the helipad with a parked helicopter, fuel bowser, windsock,
     sandbagged gun emplacements on the parapet, pillboxes, the supply dump under camouflage nets, a jeep, sandbag and
     jersey-barrier lines, tank traps, floodlights, comms masts; the radome and a gun nest on terrace 2.
   2 Inside the mountain (75 x 64): carved rock halls under a 12 m rock roof -- the vehicle hangar (armoured truck,
     blast door, mezzanine, workbenches), the ammo depot (racks, shell pallets, the armory cage with gun racks), the
     barracks (bunks, lockers, mess tables), the main gallery, and the landmark: the command centre with the big
     tactical table (a sand-table relief of the valley), consoles, the video wall and the ops balcony. Four doorways
     open from the halls onto the observation terrace cut into the cliff face along the west edge (open sky, AA guns,
     spotting scopes, an observation post on stilts, the flagpole) with the grand vista.
   The vista is level-wide (backdrop.build, never switches between zones): the massif's rock shell above the faces and
   over the halls (snow on its heights), sheer cliffs from every ledge down to the valley 300 m below, the valley floor
   under drifting mist, the opposite range with a waterfall about 500 m away, and far up the valley a second, much
   farther and hazier waterfall falling from the headwall; both scroll (shader) into churning plunge mist. The sky goes
   from blue overhead to a warm orange horizon; a low sun (env.sunColor: warm light) and pink cloud streaks in the west.
   Built by blender/fam_kit_stronghold.py (sh_*.py); zone layers by tools/stronghold_zones.py.

   Zone files: the floor plan, then "@layer 0" wall codes (digits on '#' cells, read by the chooser), then the decks:
     zone 1: 1.8 landing deck, 1.8 its rails, 3.6 terrace 1, 3.6 on terrace 1, 5.4 landing, 5.4 its rails, 7.2 terrace 2,
             7.2 on terrace 2;   zone 2: 2.4 decks, 2.4 on the decks, 12 the cavern roof.
   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z]):
     #  rock: zone 1 cliff faces (14.2 m; 2 m modules, codes 1 bunker door, 2 gun casemate, 3 vent, 4 rock shelf),
        zone 2 hall faces (12 m; codes 5 wall lamp, 6 cable tray + sector sign), the terrace face on zone 2's column 14
        (12 m hall side, 14.2 m terrace side); corners get rock pillars
     n  doorway in the terrace face (wall.passage: clear to 4.2 m, a lintel above)
     {  concrete parapet (runs)   }  parapet post   t  under a terrace (no piece)
     =  sandbag wall (runs)   j  jersey barrier (runs)   x  tank trap   o  boulder   O  big boulder [2,2]
     B  bastion [5,4] (back to the rock)   K  pillbox [4,4]   N M  gun emplacement [3,3] firing west / south
     H  helipad with the helicopter [14,14]   R  radome [4,4]   A  comms mast [2,2]   L  floodlight tower
     c  crates / ammo cans   C  pallet stack under a tarp [2,2]   Z  supply dump under a camouflage net [4,4]
     b  drums   w  windsock   J  jeep [2,4]   g  generator [2,1]   F  fuel bowser [2,4]   q  signpost
     >  concrete ramp 0 -> 1.8 m rising east [6,2]   <  ramp 1.8 -> 3.6 m rising west [6,2]   ^  ramp 0 -> 3.6 m rising
        north [2,12] (placed on a layer they start at the layer height)
     u v  steel stair to a 2.4 m deck rising north / south [2,6]   I  deck post
     T  armoured truck [3,7]   X  hangar blast door [8,1] (back to the wall)   k  workbench [2,1] (back to the wall)
     y  tool chest   e  tyre stack   i  engine hoist   ~  parking bay paint [4,8]   ,  oil stain [2,2]
     Y  ammo rack [4,1]   l  shell pallet   f  armory cage fence (runs)   z  gun rack [2,1] (back to the wall)
     Q  bunk [1,2] (head to the wall)   p  footlocker   @  locker   &  mess table [3,2]
     V  video wall [6,1] (back to the wall)   $  tactical table [6,4]   +  console [2,1]   !  radio rack
     s  spotting scope (looking west)   *  twin AA gun [3,3] (firing west)   |  flagpole
   Layer symbols: D terrace 1 slab (3.6 thick)   U terrace 2 slab (3.6)   d landing slab (1.8)   m steel deck (0.3)
     r  rail (runs)   _  cavern roof [6,8]   (and the props above, at the layer height) */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var WALLISH = '#GEn';
  function isWall(g, c, r) { return WALLISH.indexOf(g.at(c, r)) >= 0; }
  function faceOf(g, c, r) {
    var oS = !isWall(g, c, r + 1), oN = !isWall(g, c, r - 1), oE = !isWall(g, c + 1, r), oW = !isWall(g, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function code(g, c, r) {
    var L = g.layers || [];
    for (var i = 0; i < L.length; i++) if (L[i].y === 0) { var ch = L[i].at(c, r); return /[0-9]/.test(ch) ? ch : ''; }
    return '';
  }
  var STEP = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };   // a module's local +X along its wall (yaw by facing)
  function runCell(g, c, r, F) { return g.at(c, r) === '#' && faceOf(g, c, r) === F && gateDist(g, c, r) > 2.6; }
  var CLIFF = { '1': 'Cliff2_Bunker', '2': 'Cliff2_Slit', '3': 'Cliff2_Vent', '4': 'Cliff2_C' };
  var HALL = { '5': 'Rock2_Lamp', '6': 'Rock2_Cable' };
  /* wall chooser: 2 m modules on every other cell of a straight run, counted from the run's start (the module spans
     its cell and the next one along its local +X), 1 m modules where a run has an odd cell left; pillars on corners.
     Zone 1 (72 wide) gets the 14.2 m cliff faces, zone 2 (75 wide) the 12 m hall faces and, on its column 14, the
     terrace face (and lintels on its doorways). */
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var zone2 = g.w === 75, F = face || faceOf(g, c, r);
    if (g.at(c, r) === 'n') return 'Lintel';
    var terraceFace = zone2 && c === 14;
    if (terraceFace && (r === 0 || r === g.h - 1)) return 'FaceC';
    if (F === 'none' || F === 'corner') return terraceFace ? 'FaceC' : zone2 ? 'RockC' : 'CliffC';
    if (gateDist(g, c, r) < 2.6) return null;   // the gate portal and the rock over it cover these cells
    var d = STEP[F], k = 0;
    while (runCell(g, c - d[0] * (k + 1), r - d[1] * (k + 1), F)) k++;
    if (k % 2) return null;                      // covered by the 2 m module of the cell before it
    var two = runCell(g, c + d[0], r + d[1], F);
    if (terraceFace) return two ? 'Face2' : 'Face1';
    var cd = code(g, c, r) || (two ? code(g, c + d[0], r + d[1]) : '');
    if (!two) return zone2 ? 'Rock1' : 'Cliff1';
    if (zone2) return HALL[cd] || (hash(c * 5 + 1, r * 3 + 7) < 0.5 ? 'Rock2_A' : 'Rock2_B');
    return CLIFF[cd] || (hash(c * 5 + 1, r * 3 + 7) < 0.5 ? 'Cliff2_A' : 'Cliff2_B');
  }

  var SYMBOLS = {
    '{': { pieces: ['Parapet_A', 'Parapet_B', 'Parapet_A', 'Parapet_C'], rotate: 'run', kind: 'wall' },
    '}': { pieces: ['ParapetPost'], kind: 'wall' },
    '=': { pieces: ['Sandbags_A', 'Sandbags_B'], rotate: 'run', alternate: true, kind: 'cover' },
    'j': { pieces: ['Jersey'], rotate: 'run', kind: 'cover' },
    'x': { pieces: ['Hedgehog'], rotate: 'random90', kind: 'cover' },
    'o': { pieces: ['Boulder_A', 'Boulder_B'], rotate: 'random90', kind: 'cover' },
    'O': { size: [2, 2], pieces: ['BoulderBig'], flip: true, kind: 'cover' },
    'B': { size: [5, 4], pieces: ['Bastion'], orient: 'wall', kind: 'cover' },
    'K': { size: [4, 4], pieces: ['Pillbox'], flip: true, kind: 'cover' },
    'N': { size: [3, 3], pieces: ['Emplacement'], face: -R90, kind: 'cover' },
    'M': { size: [3, 3], pieces: ['Emplacement'], face: 0, kind: 'cover' },
    'H': { size: [14, 14], pieces: ['Landmark_Helipad'], with: { Landmark_Helipad: ['Landmark_Helicopter'] }, cols: [], face: 0, kind: 'cover' },
    'R': { size: [4, 4], pieces: ['Landmark_Radar'], face: 0, kind: 'cover' },
    'A': { size: [2, 2], pieces: ['Mast'], flip: true, kind: 'cover' },
    'L': { pieces: ['Flood'], rotate: 'edge', kind: 'cover' },
    'c': { pieces: ['Crate_A', 'Crate_B', 'AmmoCans'], rotate: 'random90', kind: 'cover' },
    'C': { size: [2, 2], pieces: ['Stack'], flip: true, kind: 'cover' },
    'Z': { size: [4, 4], pieces: ['CamoNet'], flip: true, kind: 'cover' },
    'b': { pieces: ['Drums'], rotate: 'random90', kind: 'cover' },
    'w': { pieces: ['Windsock'], rotate: 'random90', kind: 'cover' },
    'J': { size: [2, 4], pieces: ['Jeep'], flip: true, kind: 'cover' },
    'g': { size: [2, 1], pieces: ['Generator'], flip: true, kind: 'cover' },
    'F': { size: [2, 4], pieces: ['Bowser'], flip: true, kind: 'cover' },
    'q': { pieces: ['Signpost'], rotate: 'edge', kind: 'cover' },
    '>': { size: [2, 6], pieces: ['RampLo'], face: -R90, kind: 'cover' },
    '<': { size: [2, 6], pieces: ['RampHi'], face: R90, kind: 'cover' },
    '^': { size: [2, 12], pieces: ['RampLong'], face: 0, kind: 'cover' },
    'u': { size: [2, 6], pieces: ['Stair'], face: 0, kind: 'cover' },
    'v': { size: [2, 6], pieces: ['Stair'], face: Math.PI, kind: 'cover' },
    'I': { pieces: ['DeckPost'], kind: 'cover' },
    'T': { size: [3, 7], pieces: ['Landmark_Truck'], flip: true, kind: 'cover' },
    'X': { size: [8, 1], pieces: ['BlastDoor'], orient: 'wall', kind: 'cover' },
    'k': { size: [2, 1], pieces: ['Workbench'], orient: 'wall', kind: 'cover' },
    'y': { pieces: ['ToolChest'], rotate: 'edge', kind: 'cover' },
    'e': { pieces: ['Tyres'], rotate: 'random90', kind: 'cover' },
    'i': { pieces: ['Hoist'], rotate: 'edge', kind: 'cover' },
    '~': { size: [4, 8], pieces: ['BayPaint'], face: 0, collide: false },
    ',': { size: [2, 2], pieces: ['Stain'], flip: true, collide: false },
    'Y': { size: [4, 1], pieces: ['AmmoRack_A', 'AmmoRack_B'], flip: true, kind: 'cover' },
    'l': { pieces: ['Shells'], rotate: 'random90', kind: 'cover' },
    'f': { pieces: ['FenceHalf'], full: 'FenceFull', links: 'f', post: 'FencePost', kind: 'wall' },
    'z': { size: [2, 1], pieces: ['GunRack'], orient: 'wall', kind: 'cover' },
    'Q': { size: [1, 2], pieces: ['Bunk'], orient: 'wall', kind: 'cover' },
    'p': { pieces: ['Footlocker'], rotate: 'edge', kind: 'cover' },
    '@': { pieces: ['Locker'], rotate: 'edge', kind: 'cover' },
    '&': { size: [3, 2], pieces: ['MessTable'], flip: true, kind: 'cover' },
    'V': { size: [6, 1], pieces: ['VideoWall'], orient: 'wall', kind: 'cover' },
    '$': { size: [6, 4], pieces: ['Landmark_Table'], face: 0, kind: 'cover' },
    '+': { size: [2, 1], pieces: ['Console'], flip: true, kind: 'cover' },
    '!': { pieces: ['RadioRack'], rotate: 'edge', kind: 'cover' },
    's': { pieces: ['Scope'], rotate: -R90, kind: 'cover' },
    '*': { size: [3, 3], pieces: ['AAGun'], face: -R90, kind: 'cover' },
    '|': { pieces: ['Flagpole'], kind: 'cover' },
    // decks (layers): solid concrete terraces and landings, the steel decks in the halls
    'D': { deck: { thick: 3.6, color: '#C4BCAC', edge: '#A39B8D', under: '#8E877C' } },
    'U': { deck: { thick: 3.6, color: '#C9C1B1', edge: '#A8A091', under: '#8E877C' } },
    'd': { deck: { thick: 1.8, color: '#C4BCAC', edge: '#A39B8D', under: '#8E877C' } },
    'm': { deck: { thick: 0.3, color: '#8A9097', edge: '#565D66', under: '#4B5159' } },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    '_': { size: [6, 8], pieces: ['Roof_A', 'Roof_B', 'Roof_A', 'Roof_C'], collide: false }
  };
  // glow companions (zones.js theme.glow): lamps, screens, beacons drawn unlit; blinked by the backdrop tick
  var GLOW = {
    Flood: { piece: 'Flood_Glow' }, Mast: { piece: 'Mast_Glow', groups: 2 }, Landmark_Helipad: { piece: 'Landmark_Helipad_Glow' },
    GateFrame: { piece: 'GateFrame_Glow', groups: 2 }, Rock2_Lamp: { piece: 'Rock2_Lamp_Glow' }, Roof_B: { piece: 'Roof_B_Glow' },
    Console: { piece: 'Console_Glow', groups: 3 }, VideoWall: { piece: 'VideoWall_Glow' }, Landmark_Table: { piece: 'Landmark_Table_Glow' }
  };

  // ======================================================================================== the vista (backdrop.build)
  var VAL = -300;                   // the valley floor, 300 m below the ledge
  function hx(h) { var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE; return new THREE.Color(h); }
  function noise(x, z) { return Math.sin(x * 0.013 + z * 0.007) * 0.6 + Math.sin(z * 0.021 - x * 0.009 + 1.3) * 0.4 + Math.sin(x * 0.041 + z * 0.033 + 2.1) * 0.22; }
  // distance from (x, z) to a polyline [[x, z], ...]
  function segDist(P, x, z) {
    var best = 1e9;
    for (var i = 0; i + 1 < P.length; i++) {
      var ax = P[i][0], az = P[i][1], bx = P[i + 1][0], bz = P[i + 1][1], dx = bx - ax, dz = bz - az, L2 = dx * dx + dz * dz;
      var t = L2 ? Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / L2)) : 0, ex = ax + dx * t - x, ez = az + dz * t - z;
      best = Math.min(best, Math.sqrt(ex * ex + ez * ez));
    }
    return best;
  }
  /* A faceted, flat-shaded mesh with an optional ink hull (inverted shell along the smooth vertex normals), written
     straight into the backdrop's IB.Geo (toon material, fog). tri(a, b, c, colour): a, b, c = [x, y, z], counter-
     clockwise seen from outside. */
  function Mesher(g, ink) {
    this.g = g; this.ink = ink; this.sm = {}; this.hull = [];
  }
  Mesher.prototype.tri = function (a, b, c, col, noHull) {
    var ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, L = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    nx /= L; ny /= L; nz /= L;
    var g = this.g, i0 = g._vert(a[0], a[1], a[2], nx, ny, nz, col), i1 = g._vert(b[0], b[1], b[2], nx, ny, nz, col), i2 = g._vert(c[0], c[1], c[2], nx, ny, nz, col);
    g.idx.push(i0, i1, i2);
    if (!this.ink || noHull) return;
    var self = this, keys = [a, b, c].map(function (p) {
      var k = Math.round(p[0] * 10) + ',' + Math.round(p[1] * 10) + ',' + Math.round(p[2] * 10), s = self.sm[k];
      if (!s) s = self.sm[k] = { p: p, n: [0, 0, 0] };
      s.n[0] += nx * L; s.n[1] += ny * L; s.n[2] += nz * L;
      return k;
    });
    this.hull.push(keys);
  };
  Mesher.prototype.quad = function (a, b, c, d, col, col2) { this.tri(a, b, c, col); this.tri(a, c, d, col2 || col); };
  Mesher.prototype.finish = function (inkCol) {
    if (!this.ink) return;
    var g = this.g, sm = this.sm, idx = {};
    Object.keys(sm).forEach(function (k) {
      var s = sm[k], n = s.n, L = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) || 1;
      idx[k] = g._vert(s.p[0], s.p[1], s.p[2], 0, 1, 0, inkCol, n[0] / L, n[1] / L, n[2] / L);
    });
    this.hull.forEach(function (t) { g.idx.push(idx[t[0]], idx[t[2]], idx[t[1]]); });   // reversed winding
  };

  function rockCol(C, ny, y, top, k) {   // colour of a rock facet from its slope, height and a jitter k
    if (ny > 0.62 && y > top) return C.snow;
    if (ny > 0.8 && y < 120) return k > 0.5 ? C.scrub : C.scrub2;
    if (ny > 0.55) return k > 0.5 ? C.rockL : C.rock3;
    return k > 0.66 ? C.rock2 : k > 0.33 ? C.rock : C.rock3;
  }
  // a heightfield over the grid lines xs x zs, cells kept by keep(cx, cz); flat-shaded facets
  function heightfield(M, xs, zs, H, keep, C, snowTop, hash) {
    var V = [];
    for (var j = 0; j < zs.length; j++) { var row = []; for (var i = 0; i < xs.length; i++) row.push([xs[i], H(xs[i], zs[j]), zs[j]]); V.push(row); }
    for (j = 0; j + 1 < zs.length; j++) for (var i2 = 0; i2 + 1 < xs.length; i2++) {
      if (keep && !keep((xs[i2] + xs[i2 + 1]) / 2, (zs[j] + zs[j + 1]) / 2)) continue;
      var a = V[j][i2], b = V[j][i2 + 1], c = V[j + 1][i2 + 1], d = V[j + 1][i2];
      // two triangles; facing up (counter-clockwise seen from +y: a(x0,z0) d(x0,z1) c(x1,z1) b(x1,z0))
      var k = hash(i2 * 7 + 3, j * 13 + 5);
      [[a, d, c], [a, c, b]].forEach(function (t, ti) {
        var ux = t[1][0] - t[0][0], uy = t[1][1] - t[0][1], uz = t[1][2] - t[0][2], vx = t[2][0] - t[0][0], vy = t[2][1] - t[0][1], vz = t[2][2] - t[0][2];
        var ny = uz * vx - ux * vz, L = Math.sqrt(Math.pow(uy * vz - uz * vy, 2) + ny * ny + Math.pow(ux * vy - uy * vx, 2)) || 1;
        M.tri(t[0], t[1], t[2], rockCol(C, ny / L, (t[0][1] + t[1][1] + t[2][1]) / 3, snowTop, (k + ti * 0.37) % 1));
      });
    }
  }
  /* a sheer cliff hanging from the line a -> b (plan), from y top down to VAL, facing `out` (unit plan vector away
     from the rock). The strata bulge out toward the middle of the run and at depth; the ends stay on the line so the
     neighbouring faces meet. */
  function cliff(M, a, b, top, out, C, hash, seed) {
    var L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(L / 14)), ys = [top, top - 14, top - 55, top - 130, top - 210, VAL - 5];
    var amp = [0, 1.2, 4, 9, 16, 26], pts = [], tx = b[0] - a[0], tz = b[1] - a[1];
    var flip = -tz * out[0] + tx * out[1] < 0;   // the quads below face down x travel; turn them to face `out`
    for (var j = 0; j < ys.length; j++) {
      var row = [];
      for (var i = 0; i <= n; i++) {
        var t = i / n, e = Math.sqrt(Math.sin(Math.PI * t)), h = hash(i * 11 + seed, j * 7 + 3);
        var o = amp[j] * e * (0.45 + 0.9 * h);
        row.push([a[0] + (b[0] - a[0]) * t + out[0] * o, ys[j] + (j && j < ys.length - 1 ? (h - 0.5) * 6 : 0), a[1] + (b[1] - a[1]) * t + out[1] * o]);
      }
      pts.push(row);
    }
    for (j = 0; j + 1 < ys.length; j++) for (var i2 = 0; i2 < n; i2++) {
      var p = pts[j][i2], q = pts[j][i2 + 1], r = pts[j + 1][i2 + 1], s = pts[j + 1][i2], k = hash(i2 * 5 + seed, j * 3 + 1);
      var col = k > 0.66 ? C.rock2 : k > 0.33 ? C.rock : C.rockD, col2 = j > 2 ? C.rockD : (k > 0.5 ? C.rock3 : C.rock);
      if (flip) M.quad(p, q, r, s, col, col2); else M.quad(p, s, r, q, col, col2);
    }
  }

  function buildVista(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var hash = api.hash, g = api.geo, Z1 = level.zones[0], Z2 = level.zones[1] || level.zones[0];
    function endK(v, lo, hi) { var k = Math.max(0, Math.min(1, Math.min(v - lo, hi - v) / 260)); return k * k * (3 - 2 * k); }
    var C = { rock: hx('#A2887A'), rock2: hx('#86716A'), rock3: hx('#B9A08E'), rockL: hx('#C9AE96'), rockD: hx('#6E5D5B'),
      snow: hx('#F6EEE6'), scrub: hx('#8A8F5E'), scrub2: hx('#737A4E'), far: hx('#8C7F8E'), ink: hx('#15121C') };
    // ---- the face line of the massif (plan), from far south to far north: zone 1's south rock wall front, its east
    // wall front, its north wall front (the spur), the terrace face of zone 2 continuing north
    var xC = Z2.ox + 14, xE = Z1.ox + Z1.w - 1, xS = Z1.ox + 30, zN1 = Z1.oz + 1, zS1 = Z1.oz + Z1.h - 1;
    var zFarS = Z1.oz + Z1.h + 950, zFarN = Z2.oz - 1000, TOP = 14;
    var FACE = [[xS, zFarS], [xS, zS1], [xE, zS1], [xE, zN1], [xC, zN1], [xC, zFarN]];
    function xf(z) { return z > zS1 ? xS : z > zN1 ? xE : xC; }
    function rise(d) { return 600 * (1 - Math.exp(-d / 300)) + 30 * (1 - Math.exp(-d / 6)); }
    function Hm(x, z) {
      var d = segDist(FACE, x, z), k = Math.min(1, d / 60);
      return TOP + rise(d) + k * (38 * noise(x, z) + 140 * Math.exp(-(Math.pow(x - xE - 420, 2) + Math.pow(z - Z1.oz + 180, 2)) / 45000) +
        110 * Math.exp(-(Math.pow(x - xC - 380, 2) + Math.pow(z - Z2.oz + 260, 2)) / 30000));
    }
    // grid lines: exact on the face lines, fine near them, coarser away
    var xs = [], zs = [];
    function addLines(arr, base, steps) { var v = base; arr.push(v); steps.forEach(function (s) { v += s; arr.push(v); }); }
    var near = [3, 5, 8, 12, 16, 22];
    addLines(xs, xC, near); addLines(xs, xS, near); addLines(xs, xE, near.concat([26, 34, 45, 60, 80, 110, 140, 180, 220, 260, 300]));
    addLines(zs, zN1, [3, 6, 10]); addLines(zs, zN1, [-3, -6, -10, -14]); addLines(zs, zS1, [3, 6, 10, 14]); addLines(zs, zS1, [-3, -6, -10]);
    for (var zz = zN1 - 30; zz > zFarN; zz -= zz > Z2.oz - 120 ? 16 : 55) zs.push(zz);
    for (zz = zS1 + 30; zz < zFarS; zz += zz < zS1 + 120 ? 16 : 55) zs.push(zz);
    for (zz = zN1 + 18; zz < zS1 - 10; zz += 12) zs.push(zz);
    zs.push(zFarN, zFarS);
    function uniq(a, gap) { a.sort(function (p, q) { return p - q; }); var o = []; a.forEach(function (v) { if (!o.length || v - o[o.length - 1] > gap) o.push(v); }); return o; }
    xs = uniq(xs.filter(function (x) { return x >= xC; }), 1.5); zs = uniq(zs, 1.5);
    [xC, xS, xE].forEach(function (v) { if (xs.indexOf(v) < 0) { xs.push(v); xs.sort(function (p, q) { return p - q; }); } });
    [zN1, zS1].forEach(function (v) { if (zs.indexOf(v) < 0) { zs.push(v); zs.sort(function (p, q) { return p - q; }); } });
    var M = new Mesher(g, true);
    heightfield(M, xs, zs, Hm, function (x, z) { return x > xf(z); }, C, 380, hash);
    // the massif's far ends: rock walls down to the valley along its north, south and east edges
    function endWall(pts, out) {
      for (var i = 0; i + 1 < pts.length; i++) {
        var a = pts[i], b = pts[i + 1], p = [a[0], Hm(a[0], a[1]), a[1]], q = [b[0], Hm(b[0], b[1]), b[1]], r = [b[0], VAL, b[1]], s2 = [a[0], VAL, a[1]];
        var tx = b[0] - a[0], tz = b[1] - a[1], col = hash(i, 91) > 0.5 ? C.rock2 : C.rockD;
        if (-tz * out[0] + tx * out[1] < 0) M.quad(p, q, r, s2, col); else M.quad(p, s2, r, q, col);
      }
    }
    var xMax = xs[xs.length - 1];
    endWall(xs.filter(function (x) { return x >= xC; }).map(function (x) { return [x, zs[0]]; }), [0, -1]);
    endWall(xs.filter(function (x) { return x >= xS; }).map(function (x) { return [x, zs[zs.length - 1]]; }), [0, 1]);
    endWall(zs.map(function (z) { return [xMax, z]; }), [1, 0]);
    // ---- sheer cliffs: below the face where no ledge stands out, under the ledges (zone 1, the terrace), the spur gap
    var Wt = [-1, 0], St = [0, 1], Nt = [0, -1];
    cliff(M, [xS, zFarS], [xS, Z1.oz + Z1.h], TOP, Wt, C, hash, 1);
    cliff(M, [xC, Z1.oz], [xC, Z2.oz + Z2.h], TOP, Wt, C, hash, 2);
    cliff(M, [xC, Z2.oz], [xC, zFarN], TOP, Wt, C, hash, 3);
    cliff(M, [Z1.ox, Z1.oz + Z1.h], [Z1.ox, Z1.oz], 0, Wt, C, hash, 4);
    cliff(M, [xS, Z1.oz + Z1.h], [Z1.ox, Z1.oz + Z1.h], 0, St, C, hash, 5);
    cliff(M, [Z1.ox, Z1.oz], [xC, Z1.oz], 0, Nt, C, hash, 6);
    cliff(M, [Z2.ox, Z2.oz + Z2.h], [Z2.ox, Z2.oz], 0, Wt, C, hash, 7);
    cliff(M, [xC, Z2.oz + Z2.h], [Z2.ox, Z2.oz + Z2.h], 0, St, C, hash, 8);
    cliff(M, [Z2.ox, Z2.oz], [xC, Z2.oz], 0, Nt, C, hash, 9);
    M.finish(C.ink);

    // ---- the valley floor and the ranges round it (no ink: they stand in the haze)
    var F = new Mesher(g, false), cz = (Z1.oz + Z2.oz) / 2;
    var CF = { rock: hx('#9C8494'), rock2: hx('#806C88'), rock3: hx('#B099A4'), rockL: hx('#C9AAA6'), rockD: hx('#62566F'),
      snow: hx('#F8E8E4'), scrub: hx('#858669'), scrub2: hx('#71765F') };
    g.flat([[-3200, cz - 3200], [3200, cz - 3200], [3200, cz + 3200], [-3200, cz + 3200]], VAL, hx('#6F7E6A'));
    // the opposite range (west): a cliff line at XW with a plateau lip, peaks rising behind it
    var XW = Z1.ox - 470, W1Z = Z1.oz - 150;
    function southK(z) { var t = Math.max(0, Math.min(1, (z - cz + 60) / 520)); return t * t * (3 - 2 * t); }
    function Hw(x, z) {
      var t = southK(z), lip = 190 * (1 - t) + 25 * t + 22 * noise(z * 0.7, 11) - 30 * Math.exp(-Math.pow(z - W1Z, 2) / 1500);
      var xw = XW + 30 * Math.sin(z * 0.011) + 14 * Math.sin(z * 0.037 + 1.0);   // the cliff line meanders: buttresses, bays
      var back = Math.max(0, xw - x), cliffK = Math.min(1, back / 46);
      var base = VAL + (lip - VAL) * Math.min(1, cliffK * cliffK * (3 - 2 * cliffK) + 0.05 * Math.sin(cliffK * 9.4 + z * 0.023) * cliffK * (1 - cliffK) * 4);
      return VAL + endK(z, cz - 1500, cz + 1300) * endK(x, XW - 1500, 1e9) * (base - VAL + Math.min(1, back / 150) * (Math.max(0, (480 * (1 - t) + 140 * t) * (1 - Math.exp(-back / 500)) + 90 * noise(x * 1.3, z * 1.1)) +
        (1 - t) * 260 * Math.exp(-(Math.pow(x - XW + 620, 2) + Math.pow(z - W1Z + 200, 2)) / 70000)));
    }
    var wx = [], wz = [];
    for (var x = XW + 60; x > XW - 1500; x -= x > XW - 120 ? 21 : 70) wx.push(x);
    for (var z = cz - 1500; z < cz + 1300; z += Math.abs(z - W1Z) < 120 ? 18 : 60) wz.push(z);
    heightfield(F, uniq(wx, 1), uniq(wz, 1), Hw, null, CF, 330, hash);
    // the headwall far up the valley (north): a high step with a hanging valley lip, the second waterfall
    var HZ = zFarN - 40, W2X = Z1.ox - 300;
    function Hn(x, z) {
      var back = Math.max(0, HZ - z), k = Math.min(1, back / 60), lip = 200 + 40 * noise(x, 3) - 45 * Math.exp(-Math.pow(x - W2X, 2) / 3000);
      return VAL + endK(x, XW - 900, xC + 1100) * endK(z, HZ - 1100, 1e9) * ((lip - VAL) * (k * k * (3 - 2 * k)) + Math.min(1, back / 200) * (380 * (1 - Math.exp(-back / 600)) + 80 * noise(x * 0.9, z * 1.2)));
    }
    var nx2 = [], nz2 = [];
    for (x = XW - 900; x < xC + 1100; x += Math.abs(x - W2X) < 150 ? 25 : 80) nx2.push(x);
    for (z = HZ + 80; z > HZ - 1100; z -= z > HZ - 160 ? 30 : 110) nz2.push(z);
    heightfield(F, uniq(nx2, 1), uniq(nz2, 1), Hn, null, CF, 300, hash);
    // the far ranges south down the valley
    function Hs(x, z) { var back = Math.max(0, z - (zFarS + 260)); return VAL + endK(x, XW - 900, xE + 1000) * endK(z, -1e9, zFarS + 1300) * Math.min(1, back / 120) * (520 * (1 - Math.exp(-back / 500)) + 120 * noise(x, z)); }
    var sx = [], sz = [];
    for (x = XW - 900; x < xE + 1000; x += 90) sx.push(x);
    for (z = zFarS + 120; z < zFarS + 1300; z += 120) sz.push(z);
    heightfield(F, sx, sz, Hs, null, CF, 300, hash);

    // ---- waterfalls: scrolling ribbons down the cliff faces (own shader, its own haze), plunge mist, rivers
    var falls = [];
    var fallMat = function (rep, speed, maxHaze, cols) {
      return new THREE.ShaderMaterial({
        uniforms: { uT: { value: 0 }, uFog: { value: hx('#F4B596') }, uNear: { value: 90 }, uFar: { value: 1500 }, uMax: { value: maxHaze },
          uRep: { value: rep }, uSpd: { value: speed }, uA: { value: hx(cols[0]) }, uB: { value: hx(cols[1]) }, uC: { value: hx(cols[2]) }, uInk: { value: hx(cols[3]) } },
        vertexShader: 'varying vec2 vUv; varying float vD; void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vD = length(mv.xyz); gl_Position = projectionMatrix * mv; }',
        fragmentShader: 'uniform float uT; uniform vec3 uFog; uniform float uNear; uniform float uFar; uniform float uMax; uniform float uRep; uniform float uSpd;\n' +
          'uniform vec3 uA; uniform vec3 uB; uniform vec3 uC; uniform vec3 uInk; varying vec2 vUv; varying float vD;\n' +
          'void main(){ float s = fract(vUv.y * uRep - uT * uSpd + 0.3 * sin(vUv.x * 19.0 + vUv.y * 5.0) + 0.17 * sin(vUv.x * 41.0));\n' +
          '  vec3 c = s < 0.45 ? uA : (s < 0.75 ? uB : uC);\n' +
          '  float e = min(vUv.x, 1.0 - vUv.x); if (e < 0.04) c = uInk; else if (e < 0.1) c = mix(c, uC, 0.6);\n' +
          '  if (vUv.y < 0.025) c = uA;\n' +
          '  float h = clamp((vD - uNear) / (uFar - uNear), 0.0, uMax); gl_FragColor = vec4(mix(c, uFog, h), 1.0); }',
        side: THREE.DoubleSide, fog: false
      });
    };
    function ribbon(path, w0, w1, side, mat, segU) {
      // path: [[x, y, z], ...] down the fall; side: unit plan vector across it
      var pos = [], uv = [], idx = [], n = path.length, cum = [0];
      for (var i = 1; i < n; i++) cum.push(cum[i - 1] + Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1], path[i][2] - path[i - 1][2]));
      for (i = 0; i < n; i++) {
        var t = cum[i] / cum[n - 1], w = w0 + (w1 - w0) * Math.pow(t, 0.7);
        for (var k = 0; k <= segU; k++) {
          var u = k / segU, o = (u - 0.5) * w;
          pos.push(path[i][0] + side[0] * o, path[i][1], path[i][2] + side[1] * o); uv.push(u, cum[i] / 60);
        }
      }
      for (i = 0; i + 1 < n; i++) for (k = 0; k < segU; k++) { var a = i * (segU + 1) + k; idx.push(a, a + segU + 1, a + 1, a + 1, a + segU + 1, a + segU + 2); }
      var geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      geo.setIndex(idx); geo.computeBoundingSphere();
      var mesh = new THREE.Mesh(geo, mat); mesh.frustumCulled = false; mesh.name = 'Waterfall';
      level.root.add(mesh); falls.push(mat);
      return mesh;
    }
    // waterfall 1: over the lip of the opposite range, down its cliff into the valley mist
    var X1 = XW + 30 * Math.sin(W1Z * 0.011) + 14 * Math.sin(W1Z * 0.037 + 1.0);   // the cliff line at the fall
    var lip1 = Hw(X1 - 54, W1Z), path1 = [[X1 - 60, lip1 + 0.5, W1Z]];
    for (var i = 1; i <= 12; i++) {
      var y = lip1 - (lip1 - VAL + 20) * i / 12, fx = X1 - 44 + 44 * Math.min(1, (lip1 - y) / (lip1 - VAL)) + 7 + 12 * Math.pow(i / 12, 2);
      path1.push([Math.max(fx, X1 - 50), y, W1Z + Math.sin(i * 0.7) * 1.5]);
    }
    ribbon(path1, 30, 52, [0, 1], fallMat(1.6, 0.9, 0.8, ['#FFFFFF', '#CFEAF5', '#94C8E2', '#4E7FA6']), 4);
    // waterfall 2: much farther, from the hanging valley in the headwall
    var lip2 = Hn(W2X, HZ - 62), path2 = [[W2X, lip2 + 0.5, HZ - 60]];
    for (i = 1; i <= 10; i++) {
      var y2 = lip2 - (lip2 - VAL + 30) * i / 10, fr = Math.min(1, (lip2 - y2) / (lip2 - VAL));
      path2.push([W2X + Math.sin(i) * 3, y2, HZ - 56 + 56 * fr + 8 + 8 * fr * fr]);
    }
    ribbon(path2, 46, 80, [1, 0], fallMat(1.0, 0.6, 0.7, ['#FFFFFF', '#D8EEF6', '#A6D0E6', '#6A90B0']), 4);
    // rivers on the valley floor from both plunge pools (slow scroll)
    ribbon([[X1 + 10, VAL + 0.6, W1Z], [XW + 60, VAL + 0.6, W1Z + 60], [XW + 120, VAL + 0.6, W1Z + 260], [XW + 90, VAL + 0.6, W1Z + 600], [XW + 160, VAL + 0.6, W1Z + 1100]],
      26, 40, [1, 0], fallMat(0.25, 0.08, 0.9, ['#9CD0E6', '#7DB6D6', '#5E9CC2', '#3E6E92']), 2);
    ribbon([[W2X, VAL + 0.6, HZ + 20], [W2X + 40, VAL + 0.6, HZ + 200], [XW + 60, VAL + 0.6, W1Z - 500], [XW + 10, VAL + 0.6, W1Z - 60]],
      30, 26, [1, 0], fallMat(0.25, 0.08, 0.9, ['#9CD0E6', '#7DB6D6', '#5E9CC2', '#3E6E92']), 2);
    // ---- mist: drifting faceted puffs over the valley floor and churning at the foot of each fall (instanced, unlit)
    var sun = new THREE.Vector3(-0.62, 0.42, 0.52).normalize();
    var puffGeo = (function () {
      var ico = new THREE.IcosahedronGeometry(1, 1), p = ico.attributes.position, col = [], lit = hx('#FFF1E4'), mid = hx('#F2D2C8'), sh = hx('#C9AFC0');
      ico.computeVertexNormals();
      var nm = ico.attributes.normal, tmp = new THREE.Color();
      for (var v = 0; v < p.count; v += 3) {
        var ny = (nm.getY(v) + nm.getY(v + 1) + nm.getY(v + 2)) / 3, dl = ((nm.getX(v) + nm.getX(v + 1) + nm.getX(v + 2)) * sun.x + ny * 3 * sun.y + (nm.getZ(v) + nm.getZ(v + 1) + nm.getZ(v + 2)) * sun.z) / 3;
        tmp.copy(dl > 0.25 ? lit : dl > -0.15 ? mid : sh);
        for (var q = 0; q < 3; q++) col.push(tmp.r, tmp.g, tmp.b);
      }
      ico.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
      return ico;
    })();
    var puffs = [];
    function puffField(list) {
      var im = new THREE.InstancedMesh(puffGeo, new THREE.MeshBasicMaterial({ vertexColors: true, fog: true }), list.length);
      im.frustumCulled = false; im.name = 'Mist';
      list.forEach(function (P, k) { P.im = im; P.k = k; puffs.push(P); });
      level.root.add(im);
      return im;
    }
    var vm = [], n0 = 0;
    for (var gz = zFarN + 150; gz < zFarS; gz += 85) for (var gx = XW - 30; gx < Z1.ox - 30; gx += 90) {
      n0++;
      if (hash(n0, 31) < 0.35) continue;
      var r = 30 + hash(n0, 33) * 45;
      vm.push({ x: gx + (hash(n0, 35) - 0.5) * 50, y: VAL + 8 + hash(n0, 37) * 25, z: gz + (hash(n0, 39) - 0.5) * 50, sx: r * 1.5, sy: r * 0.45, sz: r, ph: hash(n0, 41) * 6.28, drift: 0.6 + hash(n0, 43) });
    }
    puffField(vm);
    var pm = [];
    [[X1 + 6, W1Z, 26, 14], [W2X, HZ + 14, 34, 12]].forEach(function (B, bi) {
      for (var k = 0; k < B[3]; k++) {
        var a = k / B[3] * Math.PI * 2;
        pm.push({ x: B[0] + Math.cos(a) * B[2] * (0.4 + hash(k, 51 + bi) * 0.8), y: VAL + 10 + hash(k, 53 + bi) * 30, z: B[1] + Math.sin(a) * B[2] * (0.4 + hash(k, 55 + bi) * 0.8),
          sx: B[2] * (0.55 + hash(k, 57) * 0.4), sy: B[2] * (0.45 + hash(k, 59) * 0.3), sz: B[2] * (0.55 + hash(k, 61) * 0.4), ph: hash(k, 63) * 6.28, churn: 1 });
      }
    });
    puffField(pm);
    // ---- the low sun, its halo, and pink cloud streaks in the western sky (unlit, beyond the fog)
    var cx = (Z1.ox + Z2.ox) / 2 + 30, sunDir = new THREE.Vector3(-0.9, 0.19, 0.4).normalize();
    function disc(r, col, dist, ord) {
      var m = new THREE.Mesh(new THREE.CircleGeometry(r, 28), new THREE.MeshBasicMaterial({ color: col, fog: false }));
      m.position.set(cx + sunDir.x * dist, sunDir.y * dist, cz + sunDir.z * dist); m.lookAt(cx, 0, cz); m.renderOrder = ord; m.frustumCulled = false; m.name = 'Sun';
      level.root.add(m);
    }
    disc(150, hx('#FFC48A'), 2100, -6); disc(95, hx('#FFDFA6'), 2090, -5); disc(62, hx('#FFF6D6'), 2080, -4);
    // the sunset band: a ring round the level from below the horizon up to 28 degrees, orange-gold low down, pink and
    // mauve higher, blending into the sky dome's blue; warmer toward the sun (drawn first, behind everything)
    var STOPS = [[-0.18, '#F4B596'], [0, '#FFB27C'], [0.07, '#FFA07A'], [0.16, '#F3909A'], [0.27, '#B98BB0'], [0.39, '#7D86C0'], [0.53, '#4B78C2']];
    var band = new IB.Geo(), RB = 2300, NS = 48, glowC = hx('#FFD79E'), tc = new THREE.Color();
    for (var bi = 0; bi < NS; bi++) for (var bj = 0; bj + 1 < STOPS.length; bj++) {
      var q = [[bi, bj], [bi + 1, bj], [bi + 1, bj + 1], [bi, bj + 1]].map(function (P2) {
        var a2 = P2[0] / NS * Math.PI * 2, st = STOPS[P2[1]], dx2 = Math.cos(a2), dz2 = Math.sin(a2);
        var sd = Math.max(0, dx2 * sunDir.x + dz2 * sunDir.z) / Math.hypot(sunDir.x, sunDir.z), w = Math.pow(sd, 6) * (P2[1] < 4 ? 0.75 : 0.2);
        tc.copy(hx(st[1])).lerp(glowC, w);
        return band._vert(cx + dx2 * RB, st[0] * RB, cz + dz2 * RB, -dx2, 0, -dz2, tc.clone());
      });
      band.idx.push(q[0], q[2], q[1], q[0], q[3], q[2]);
    }
    var bandM = new THREE.Mesh(band.build(), new THREE.MeshBasicMaterial({ vertexColors: true, fog: false, depthWrite: false, side: THREE.DoubleSide }));
    bandM.renderOrder = -9; bandM.frustumCulled = false; bandM.name = 'SunsetBand';
    level.root.add(bandM);
    var sk = new Mesher(new IB.Geo(), false), skc = [hx('#F7A3A0'), hx('#FFC694'), hx('#E58FA4'), hx('#F9B8A0')], und = hx('#B98AA8');
    for (var c2 = 0; c2 < 14; c2++) {
      var az = -2.2 + hash(c2, 71) * 1.6 + (c2 > 9 ? 2.2 : 0), dist = 1300 + hash(c2, 73) * 500, hy = 240 + hash(c2, 75) * 320;
      var px = cx + Math.cos(az) * dist, pz = cz + Math.sin(az) * dist, Lh = 220 + hash(c2, 77) * 380, Th = 14 + hash(c2, 79) * 22, ta = az + Math.PI / 2;
      var ux2 = Math.cos(ta) * Lh / 2, uz2 = Math.sin(ta) * Lh / 2, col2 = skc[c2 % 4];
      var A = [px - ux2, hy, pz - uz2], B2 = [px + ux2, hy + Th * 0.2, pz + uz2], T1 = [px - ux2 * 0.4, hy + Th, pz - uz2 * 0.4], T2 = [px + ux2 * 0.5, hy + Th * 0.8, pz + uz2 * 0.5];
      var D1 = [px - ux2 * 0.3, hy - Th * 0.35, pz - uz2 * 0.3], D2 = [px + ux2 * 0.4, hy - Th * 0.3, pz + uz2 * 0.4];
      sk.tri(A, T1, T2, col2); sk.tri(A, T2, B2, col2); sk.tri(A, B2, D2, und); sk.tri(A, D2, D1, und);
      sk.tri(A, T2, T1, col2); sk.tri(A, B2, T2, col2); sk.tri(A, D2, B2, und); sk.tri(A, D1, D2, und);
    }
    var skyM = new THREE.Mesh(sk.g.build(), new THREE.MeshBasicMaterial({ vertexColors: true, fog: false }));
    skyM.renderOrder = -3; skyM.frustumCulled = false; skyM.name = 'SkyStreaks';
    level.root.add(skyM);

    // ---- animation: the falls scroll, the mist drifts and churns, beacons and gate lamps blink
    var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
    function setPuffs(t) {
      for (var k = 0; k < puffs.length; k++) {
        var P = puffs[k], b = P.churn ? 1 + 0.18 * Math.sin(t * 1.3 + P.ph) : 1 + 0.05 * Math.sin(t * 0.25 + P.ph);
        var dz = P.churn ? 0 : Math.sin(t * 0.02 * P.drift + P.ph) * 20, dy = P.churn ? 4 * Math.sin(t * 0.9 + P.ph) : 0;
        _q.setFromAxisAngle(up, P.ph + (P.churn ? t * 0.15 : 0)); _p.set(P.x, P.y + dy, P.z + dz); _s.set(P.sx * b, P.sy * b, P.sz * b);
        P.im.setMatrixAt(P.k, _m.compose(_p, _q, _s));
      }
      level.root.children.forEach(function (o) { if (o.name === 'Mist') o.instanceMatrix.needsUpdate = true; });
    }
    setPuffs(0);
    api.tick(function (dt, t) {
      var R = IB.Render, fog = R && R.scene && R.scene.fog;
      falls.forEach(function (m) { m.uniforms.uT.value = t; if (fog) { m.uniforms.uFog.value.copy(fog.color); m.uniforms.uNear.value = fog.near; m.uniforms.uFar.value = fog.far; } });
      setPuffs(t);
      (level.glows || []).forEach(function (G) {
        if (G.piece === 'Mast_Glow' || G.piece === 'GateFrame_Glow') G.mesh.visible = ((t + G.group * 0.6) % 1.2) < 0.7;
        else if (G.piece === 'Console_Glow') G.mesh.visible = ((t * 0.7 + G.group * 1.3) % 4) > 0.15;
      });
    });
  }

  var PIECES = ['Cliff2_A', 'Cliff2_B', 'Cliff2_C', 'Cliff2_Bunker', 'Cliff2_Slit', 'Cliff2_Vent', 'Cliff1', 'CliffC',
    'Rock2_A', 'Rock2_B', 'Rock2_Lamp', 'Rock2_Cable', 'Rock1', 'RockC', 'Face2', 'Face1', 'FaceC', 'Lintel',
    'GateFrame', 'GateRock', 'GateShutter', 'Hatch', 'TrailWall', 'TrailWall_Lamp', 'TrailWall_Pipe', 'TrailWall_Sign', 'TunnelLamp'];
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    var all = d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []);
    Object.keys(d.with || {}).forEach(function (k) { all = all.concat(d.with[k]); });
    all.forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { if (PIECES.indexOf(GLOW[k].piece) < 0) PIECES.push(GLOW[k].piece); });

  IB.registerTheme({
    id: 'stronghold', name: 'Fort Highwatch', family: 'kit-stronghold', prefix: 'KIT_STRONGHOLD_',
    palette: ['#6B7445', '#FFB27C', '#4B78C2', '#BDB5A6'],
    // late afternoon going to sunset: blue overhead, a warm orange horizon, warm low sun, a peach haze far out
    env: { sky: ['#4B78C2', '#FFB27C'], fog: { color: '#F4B596', near: 90, far: 1500, tierScale: true }, sun: [-0.62, 0.42, 0.52],
      sunColor: '#FFE2C2', clouds: false, far: 2600,
      ceiling: { height: 5.0, color: '#4E4644', light: 'TunnelLamp', every: 4 } },   // the trail tunnels and the hatch room only
    floor: { color: '#B9B1A2', trail: '#8D857A', lines: [{ dir: 'x', every: 4, width: 0.05, color: '#A39B8D' }, { dir: 'z', every: 4, width: 0.05, color: '#A39B8D' }] },
    wall: { height: 12, roof: '#5A504F', facing: 'open', choose: chooseWall, passage: { ch: 'n', solid: [[4.2, 12]] } },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', dress: ['GateRock'], shutter: 'GateShutter', height: 3.4, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_Lamp', 'TrailWall', 'TrailWall_Pipe', 'TrailWall', 'TrailWall_Sign'], height: 5.0 },
    hatch: 'Hatch', stand: 'Crate_A',
    backdrop: { build: buildVista },
    budget: { prop: 1600, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      stronghold: {
        name: 'Fort Highwatch',
        intro: 'Robots have seized Fort Highwatch, high on the mountain. Clear the outer works on the cliff ledge, then take the halls inside the mountain.',
        zones: [
          // the outer works: the ledge, the terraces, the helipad
          { map: 'stronghold_1', ceiling: false, label: 'The Outer Works', waves: [
            [['crawler', 22], ['gunner', 10], ['drone', 5]],
            [['crawler', 18], ['gunner', 8], ['bomber', 2], ['soldier', 6], ['blader', 3]],
            [['crawler', 16], ['drone', 8], ['gunner', 7], ['soldier', 6], ['blader', 3]],
            [['crawler', 16], ['gunner', 8], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 16], ['gunner', 7], ['drone', 4], ['soldier', 5], ['blader', 3]]] },
          // inside the mountain: halls, hangar, depot, command centre, the terrace
          { map: 'stronghold_2', ceiling: false, label: 'Inside the Mountain',
            floor: { color: '#9B9388', lines: [{ dir: 'x', every: 4, width: 0.05, color: '#8B8378' }, { dir: 'z', every: 4, width: 0.05, color: '#8B8378' }] },
            waves: [
              [['crawler', 18], ['gunner', 9], ['drone', 4], ['soldier', 5], ['blader', 2]],
              [['crawler', 16], ['drone', 7], ['gunner', 7], ['soldier', 5], ['blader', 3]],
              [['crawler', 16], ['gunner', 8], ['bomber', 2], ['soldier', 6], ['blader', 3]],
              [['crawler', 15], ['drone', 6], ['gunner', 8], ['soldier', 5], ['blader', 3]],
              [['crawler', 18], ['gunner', 8], ['bomber', 2], ['soldier', 1], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
