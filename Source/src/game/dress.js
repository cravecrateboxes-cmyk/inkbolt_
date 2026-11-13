/* INKBOLT tactical look: world dressing (plan Stage 9). Decals on floors and walls, built once per level from the
   zone grids, deterministic (hash of the cell), no collision, no effect on play.

   Floor decals sit on open floor cells ('.'), weighted toward wall bases, corners and props, never within 1.5 m of
   gates, pickups, spawn cans, weapon stands, doors, elevators, stairs / ramps / decks (walkable boxes) or water, and
   never over a step or an edge (the floor under every corner must agree). Wall decals sit on the open face of wall
   modules, found by a ray against the placed module's own mesh: the decal goes only where all its corners land on
   one flat face of a plain wall (no window, door, shutter, glass, screen or glowing cell).

   Decals are lit (look kind 'decal': light volume + sun + shadow, no tiling detail), alpha-blended, one merged mesh
   per zone in the zone's group (shown and hidden with the zone). Atlas: assets/tex/decals.webp (tools/gen_decals.py),
   cells listed in IB.DECALS (data/decals.gen.js). Rules per look family: looks.js `dress`. Density scales with the
   tier at level build. Only with the look on (classic has no dressing). */
(function (IB) {
  'use strict';
  var D = IB.Dress = { meshes: [], stats: [] };
  var tex = null, mat = null;

  function hash(a, b) { var h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  function rnd(seed) { var s = seed >>> 0 || 1; return function () { s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function pickW(list, r) {
    var tot = 0, i; for (i = 0; i < list.length; i++) tot += list[i][1];
    var x = r * tot; for (i = 0; i < list.length; i++) { x -= list[i][1]; if (x <= 0) return list[i][0]; }
    return list[list.length - 1][0];
  }

  // per decal: size range (m), aspect (h / w), how it turns ('free' any yaw, 'grid' quarter turns), tint (display rgb,
  // multiplied with the cell's grey), strength (alpha scale)
  var TYPES = {
    oil: { s: [0.8, 2.0], tint: [0.30, 0.28, 0.26], k: 0.85 }, oil2: { s: [0.6, 1.4], tint: [0.28, 0.26, 0.25], k: 0.85 },
    water: { s: [0.9, 2.4], tint: [0.55, 0.55, 0.52], k: 0.55 }, water2: { s: [0.8, 1.8], tint: [0.55, 0.53, 0.50], k: 0.55 },
    rust: { s: [0.6, 1.2], a: 2.0, tint: [0.62, 0.36, 0.20], k: 0.75 }, leak: { s: [0.4, 0.9], a: 2.4, tint: [0.40, 0.42, 0.40], k: 0.7 },
    sootStreak: { s: [0.8, 1.6], a: 1.4, tint: [0.25, 0.25, 0.26], k: 0.7 }, soot: { s: [1.0, 2.2], tint: [0.22, 0.22, 0.23], k: 0.7 },
    crack: { s: [0.8, 1.8], tint: [0.30, 0.30, 0.30], k: 0.9 }, crack2: { s: [0.7, 1.4], tint: [0.30, 0.30, 0.30], k: 0.9 },
    crack3: { s: [0.8, 1.6], tint: [0.30, 0.30, 0.30], k: 0.9 },
    tyre: { s: [2.0, 3.0], tint: [0.30, 0.30, 0.30], k: 0.6 }, scuff: { s: [1.2, 2.6], tint: [0.45, 0.43, 0.40], k: 0.5 },
    puddle: { s: [1.0, 2.6], tint: [0.30, 0.32, 0.34], k: 0.7 }, patch: { s: [0.8, 1.6], tint: [1.0, 0.98, 0.95], k: 0.7, turn: 'grid' },
    drain: { s: [0.6, 0.6], tint: [0.55, 0.55, 0.55], k: 1, turn: 'grid' }, manhole: { s: [1.0, 1.0], tint: [0.6, 0.58, 0.55], k: 1 },
    grate: { s: [0.9, 0.9], tint: [0.6, 0.6, 0.6], k: 1, turn: 'grid' },
    arrow: { s: [1.2, 1.6], tint: [0.95, 0.85, 0.40], k: 0.8, turn: 'grid' }, chevrons: { s: [1.4, 1.8], tint: [0.95, 0.80, 0.22], k: 0.85, turn: 'grid' },
    stencilExit: { s: [0.7, 1.0], tint: [0.92, 0.92, 0.88], k: 0.75 }, stencilZone: { s: [0.8, 1.1], tint: [0.92, 0.92, 0.88], k: 0.75 },
    stencilNo: { s: [0.8, 1.1], tint: [0.92, 0.92, 0.88], k: 0.75 }, stencilDanger: { s: [0.8, 1.1], tint: [0.95, 0.80, 0.22], k: 0.8 },
    poster: { s: [0.8, 1.1], a: 1.0, tint: [0.95, 0.90, 0.82], k: 0.95 }, poster2: { s: [0.8, 1.1], tint: [0.85, 0.92, 0.95], k: 0.95 },
    poster3: { s: [0.8, 1.1], tint: [0.95, 0.85, 0.80], k: 0.95 },
    paper: { s: [0.6, 1.0], tint: [0.92, 0.90, 0.85], k: 0.9 }, leaves: { s: [0.7, 1.3], tint: [0.62, 0.48, 0.24], k: 0.9 },
    prints: { s: [0.8, 1.2], tint: [0.32, 0.27, 0.22], k: 0.6 },
    scars: { s: [0.6, 1.0], tint: [0.30, 0.30, 0.30], k: 0.8 }, scars2: { s: [0.6, 1.0], tint: [0.30, 0.30, 0.30], k: 0.8 },
    grime: { s: [1.0, 2.6], tint: [0.40, 0.37, 0.33], k: 0.55 }, grime2: { s: [1.0, 2.6], tint: [0.40, 0.37, 0.33], k: 0.55 },
    grimeBase: { s: [1.0, 1.4], a: 0.55, tint: [0.36, 0.33, 0.30], k: 0.6 },
    moss: { s: [0.8, 1.8], tint: [0.36, 0.48, 0.22], k: 0.7 }
  };
  for (var dg = 0; dg < 10; dg++) TYPES['digit' + dg] = { s: [0.5, 0.7], tint: [0.92, 0.92, 0.88], k: 0.75, turn: 'grid' };
  D.TYPES = TYPES;

  // symbols whose pieces are water (a decal there would float on or sink under the surface)
  var WATER_RX = /water|pond|pool|puddle|lake|river|stream|sea|surf|fountain|tide/i;
  var PLAIN_WALL_BAD = /door|window|glass|shutter|screen|gate|grille|vent|sign|poster|neon|light|lamp|rail|fence|arch|open/i;

  function texture() {
    if (tex) return tex;
    var src = (IB.TEX_DATA || {})['decals.webp'] || 'assets/tex/decals.webp';
    tex = new THREE.TextureLoader().load(src);
    tex.anisotropy = 4; tex.generateMipmaps = true; tex.minFilter = THREE.LinearMipmapLinearFilter;
    return tex;
  }
  function material() {
    if (mat) return mat;
    mat = IB.Render.toonMaterial({ look: 'decal', map: texture(), surf: IB.Surface.surfFlat(1, 0.12) });
    mat.transparent = true; mat.depthWrite = false;
    mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -4;
    return mat;
  }

  // ------------------------------------------------------------------------------------------- geometry buffer
  function Buf() { this.p = []; this.n = []; this.c = []; this.uv = []; this.idx = []; this.count = 0; }
  // a quad: centre, unit axes u (width) and v (height), normal; cell index; tint rgb and alpha strength (vertex
  // colour alpha is not used: the strength scales the tint toward white instead, see below); hts: optional 3 x 3 heights
  Buf.prototype.quad = function (cell, cx, cy, cz, ux, uy, uz, vx, vy, vz, nx, ny, nz, w, h, tint, k, hts) {
    var G = IB.DECALS.grid, col = cell % G, row = Math.floor(cell / G), pad = 0.5 / 128;
    var u0 = col / G + pad, u1 = (col + 1) / G - pad, v1 = 1 - row / G - pad, v0 = 1 - (row + 1) / G + pad;
    var base = this.count, N = hts ? 3 : 2;
    for (var j = 0; j < N; j++) for (var i = 0; i < N; i++) {
      var a = i / (N - 1) - 0.5, b = j / (N - 1) - 0.5;
      var px = cx + ux * a * w + vx * b * h, py = cy + uy * a * w + vy * b * h, pz = cz + uz * a * w + vz * b * h;
      if (hts) py = hts[j * 3 + i];
      this.p.push(px, py, pz); this.n.push(nx, ny, nz);
      // strength: blend the tint toward the alpha-weighted ... simplest correct form: colour = tint, alpha from the
      // texture times k (k rides in the colour's spare channel is not available, so k is applied by premixing below)
      this.c.push(tint[0], tint[1], tint[2], k);
      this.uv.push(u0 + (u1 - u0) * (i / (N - 1)), v1 - (v1 - v0) * (j / (N - 1)));
    }
    for (j = 0; j < N - 1; j++) for (i = 0; i < N - 1; i++) {
      var q = base + j * N + i;
      this.idx.push(q, q + N, q + 1, q + 1, q + N, q + N + 1);
    }
    this.count += N * N;
  };
  Buf.prototype.mesh = function () {
    if (!this.count) return null;
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 4));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('aHull', new THREE.Float32BufferAttribute(new Float32Array(this.count * 3), 3));
    g.setIndex(this.idx);
    g.computeBoundingSphere();
    var m = new THREE.Mesh(g, material());
    m.renderOrder = 2; m.castShadow = false; m.receiveShadow = true; m.userData.noShadow = true; m.userData.dress = true;
    m.matrixAutoUpdate = false;
    return m;
  };

  // ------------------------------------------------------------------------------------------- per zone
  function exclusions(level, zone, grid, theme) {
    var ex = [], Z = IB.Zones;
    function add(x, z, r) { ex.push([x, z, r]); }
    zone.spawns.forEach(function (s) { add(s.x, s.z, 1.5); });
    zone.pickups.forEach(function (s) { add(s.x, s.z, 1.5); });
    (zone.mounts || []).forEach(function (s) { add(s.x, s.z, 1.5); });
    (zone.doors || []).forEach(function (d) { if (d.x !== undefined) add(d.x, d.z, 2.0); });
    (zone.elevators || []).forEach(function (L) { var p = L.group ? L.group.position : L.mesh && L.mesh.position; if (p) add(p.x, p.z, 2.5); });
    // gates and the water / stairs symbols of this theme
    var water = {};
    Object.keys(theme.symbols || {}).forEach(function (ch) {
      var d = theme.symbols[ch], names = [].concat(d.piece || d.pieces || [], d.name || []).join(' ');
      if (WATER_RX.test(names) || d.water) water[ch] = 1;
    });
    for (var r = 0; r < grid.h; r++) for (var c = 0; c < grid.w; c++) {
      var ch = grid.rows[r][c];
      if (ch === 'E' || ch === 'G') add(zone.ox + c + 0.5, zone.oz + r + 0.5, 2.5);
      else if (ch === 'S' || ch === 'a' || ch === 'h' || water[ch]) add(zone.ox + c + 0.5, zone.oz + r + 0.5, 1.5);
    }
    // walkable boxes (stairs, ramps, decks): 1.5 m round their footprint
    var boxes = [];
    zone.world.boxes.forEach(function (b) { if (b.walk && b.zone === zone.idx && b.on !== false) boxes.push(b); });
    return { pts: ex, boxes: boxes, water: water, Z: Z };
  }
  function excluded(E, x, z) {
    for (var i = 0; i < E.pts.length; i++) { var e = E.pts[i], dx = x - e[0], dz = z - e[1]; if (dx * dx + dz * dz < e[2] * e[2]) return true; }
    for (i = 0; i < E.boxes.length; i++) { var b = E.boxes[i]; if (x > b.x0 - 1.5 && x < b.x1 + 1.5 && z > b.z0 - 1.5 && z < b.z1 + 1.5) return true; }
    return false;
  }

  function floorDecals(level, zone, grid, theme, rules, density, E, B, rand, stat) {
    var world = zone.world, terrain = !!(zone.terrain || world.terrains.length);
    var WALLISH = '#GE';
    var rate = 0.055 * density * (rules.density === undefined ? 1 : rules.density);
    for (var r = 1; r < grid.h - 1; r++) for (var c = 1; c < grid.w - 1; c++) {
      if (grid.rows[r][c] !== '.') continue;
      var h0 = hash(zone.idx * 7919 + c * 31, r * 17 + 3);
      // weight: neighbours that are not open floor (walls, props) pull stains toward bases and corners
      var near = 0;
      for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) { var q = grid.at(c + dc, r + dr); if (q !== '.' && q !== ' ') near += WALLISH.indexOf(q) >= 0 ? 1 : 0.7; }
      var p = rate * (1 + near * 0.55);
      if (h0 > p) continue;
      var rr = rnd(Math.floor(h0 * 4294967296) ^ (zone.idx * 977));
      var name = pickW(near > 2 && rules.base ? rules.base : rules.floor, rr());
      var T = TYPES[name], cell = IB.DECALS.cell[name]; if (!T || cell === undefined) continue;
      var w = T.s[0] + (T.s[1] - T.s[0]) * rr(), h = w * (T.a || 1);
      var x = zone.ox + c + 0.5 + (rr() - 0.5) * 0.6, z = zone.oz + r + 0.5 + (rr() - 0.5) * 0.6;
      if (excluded(E, x, z)) { stat.skip++; continue; }
      var yaw = T.turn === 'grid' ? Math.floor(rr() * 4) * Math.PI / 2 : rr() * Math.PI * 2;
      var ca = Math.cos(yaw), sa = Math.sin(yaw), R = Math.max(w, h) * 0.5;
      // footprint: every cell under the decal is floor or a wall/prop (hidden under it), none excluded / water
      var ok = true;
      for (var fz = -1; fz <= 1 && ok; fz++) for (var fx = -1; fx <= 1 && ok; fx++) {
        var sx = x + fx * R * 0.7, sz = z + fz * R * 0.7, ch = grid.at(Math.floor(sx - zone.ox), Math.floor(sz - zone.oz));
        if (ch === 'E' || ch === 'G' || E.water[ch]) ok = false;
        else if (excluded(E, sx, sz)) ok = false;
      }
      if (!ok) { stat.skip++; continue; }
      // the floor under the decal: 3 x 3 samples must agree (flat floors exactly; terrain within 0.25 m of a plane)
      var hts = [], hmin = 1e9, hmax = -1e9;
      for (var j = 0; j < 3; j++) for (var i = 0; i < 3; i++) {
        var a = (i / 2 - 0.5), b2 = (j / 2 - 0.5);
        var px = x + ca * a * w - sa * b2 * h, pz = z + sa * a * w + ca * b2 * h;
        var y = world.groundAt ? world.groundAt(px, pz) : 0;
        hts.push(y); hmin = Math.min(hmin, y); hmax = Math.max(hmax, y);
      }
      if (hmax - hmin > (terrain ? 0.25 : 0.02) || hmin < -50) { stat.skip++; continue; }
      var lift = terrain ? 0.035 : 0.016;
      // painted floors sit at 0.004 (+ sunk depth); the decal goes above the floor lines (0.008 to 0.012)
      for (i = 0; i < 9; i++) hts[i] += lift + (terrain ? 0 : 0.004);
      var k = T.k * (0.55 + 0.45 * rr());
      B.quad(cell, x, hts[4], z, ca, 0, sa, -sa, 0, ca, 0, 1, 0, w, h, T.tint, k, terrain ? hts : null);
      if (!terrain) { /* flat: corners from the centre height */ }
      stat.floor++;
    }
  }

  var _ray = null, _mesh = null, _o = null, _d = null;
  function wallHit(name, mx, mz, myaw, ox, oy, oz, dx, dz) {
    var geo = IB.Assets.geo[name]; if (!geo) return null;
    if (!_ray) { _ray = new THREE.Raycaster(); _mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial()); _o = new THREE.Vector3(); _d = new THREE.Vector3(); }
    _mesh.geometry = geo; _mesh.position.set(mx, 0, mz); _mesh.rotation.set(0, myaw, 0); _mesh.updateMatrixWorld(true);
    _ray.set(_o.set(ox, oy, oz), _d.set(dx, 0, dz)); _ray.far = 1.6;
    var hits = _ray.intersectObject(_mesh, false);
    return hits.length ? hits[0] : null;
  }
  function cellClass(fam, uv) {
    var T = IB.SURFACES && IB.SURFACES[fam]; if (!T || !uv) return 0;
    var i = Math.min(7, Math.floor(uv.x * 8)) + Math.min(7, Math.floor((1 - uv.y) * 8)) * 8;
    return T.cls[i] || 0;
  }

  function why(stat, k) { var w = stat.why || (stat.why = {}); w[k] = (w[k] || 0) + 1; }
  function wallDecals(level, zone, grid, theme, rules, density, E, B, rand, stat) {
    if (!rules.wall || !zone.wallMods) return;
    var rate = 0.30 * density * (rules.density === undefined ? 1 : rules.density) * (rules.wallRate === undefined ? 1 : rules.wallRate);
    var H = (theme.wall && theme.wall.height) || 3;
    var DIR = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
    zone.wallMods.forEach(function (W) {
      var dir = DIR[W.face]; if (!dir) return;
      var h0 = hash(zone.idx * 4111 + W.c * 37, W.r * 53 + 11);
      if (h0 > rate) return;
      if (PLAIN_WALL_BAD.test(W.name)) { stat.skipW++; why(stat, 'name'); return; }
      var rr = rnd(Math.floor(h0 * 4294967296) ^ (zone.idx * 1231 + 7));
      var name = pickW(rules.wall, rr()), T = TYPES[name], cell = IB.DECALS.cell[name];
      if (!T || cell === undefined) return;
      var w = T.s[0] + (T.s[1] - T.s[0]) * rr(), h = w * (T.a || 1);
      var x = zone.ox + W.c + 0.5, z = zone.oz + W.r + 0.5;
      var ex = x + dir[0] * 1.0, ez = z + dir[1] * 1.0;   // the open cell in front
      if (excluded(E, ex, ez)) { stat.skipW++; why(stat, 'excl'); return; }
      if (grid.at(W.c + dir[0], W.r + dir[1]) !== '.') { stat.skipW++; why(stat, 'front'); return; }
      // height of the decal centre: base grime at the floor, streaks hang from near the top, the rest at eye level
      var cy = name === 'grimeBase' ? h / 2 + 0.01 : /rust|leak|sootStreak/.test(name) ? Math.min(H - 0.15, 2.6) - h / 2 : 1.2 + rr() * 0.9;
      if (cy + h / 2 > H - 0.05 || cy - h / 2 < -0.01) { stat.skipW++; why(stat, 'height'); return; }
      var along = (rr() - 0.5) * Math.max(0, 1 - w) ;   // stay on this module
      var tx = -dir[1], tz = dir[0];                     // along the wall
      var px = ex + tx * along, pz = ez + tz * along;
      // five rays (centre, four corners) must land on one flat face of this module, facing the open cell
      var fam = IB.Assets.family[W.name], hit0 = null, okHits = true;
      var probes = [[0, 0], [-0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [0.5, 0.5]];
      for (var i = 0; i < probes.length && okHits; i++) {
        var a = probes[i][0] * w, b = probes[i][1] * h;
        var hit = wallHit(W.name, x, z, W.yaw, px + tx * a, cy + b, pz + tz * a, -dir[0], -dir[1]);
        if (!hit || !hit.face) { okHits = false; why(stat, 'miss'); break; }
        var n = hit.face.normal.clone().transformDirection(_mesh.matrixWorld);
        if (n.x * dir[0] + n.z * dir[1] < 0.95) { okHits = false; why(stat, 'normal'); break; }
        var cls = cellClass(fam, hit.uv);
        if (cls === 11 || cls === 14 || cls === 15) { okHits = false; why(stat, 'glass'); break; }
        if (!hit0) hit0 = hit; else if (Math.abs(hit.distance - hit0.distance) > 0.012) { okHits = false; why(stat, 'flat'); break; }
      }
      if (!okHits) { stat.skipW++; return; }
      var d = hit0.distance - 0.006;
      var cx = px - dir[0] * d, cz = pz - dir[1] * d;
      var k = T.k * (0.6 + 0.4 * rr());
      // u along the wall (left to right seen from the open side), v down (atlas rows are top-down)
      B.quad(cell, cx, cy, cz, -tx * 1, 0, -tz * 1, 0, -1, 0, dir[0], 0, dir[1], w, h, T.tint, k, null);
      stat.wall++;
    });
  }

  // ------------------------------------------------------------------------------------------- clutter (fps-dress.glb)
  // floor pieces: low (under 0.6 m), never solid. wall pieces: back on the wall plane, centre height y
  var WALL_PIECES = { Conduit: { y: 2.3, w: 1.0, h: 0.1 }, JunctionBox: { y: 1.35, w: 0.3, h: 0.35 }, Vent: { y: 1.95, w: 0.42, h: 0.42 },
    Extinguisher: { y: 0.85, w: 0.2, h: 0.65 }, SignWarn: { y: 1.55, w: 0.38, h: 0.32 }, SignExit: { y: 2.05, w: 0.42, h: 0.22 },
    SignPlate: { y: 1.55, w: 0.38, h: 0.32 } };
  var _m4 = null, _q = null, _p = null, _s = null, _yAxis = null;
  function mat4(x, y, z, yaw) {
    if (!_m4) { _m4 = new THREE.Matrix4(); _q = new THREE.Quaternion(); _p = new THREE.Vector3(); _s = new THREE.Vector3(1, 1, 1); _yAxis = new THREE.Vector3(0, 1, 0); }
    _q.setFromAxisAngle(_yAxis, yaw); _p.set(x, y, z); return _m4.clone().compose(_p, _q, _s);
  }
  function hasPiece(n) { return !!(IB.Assets && IB.Assets.geo && IB.Assets.geo['KIT_DRESS_' + n]); }

  function floorClutter(zone, grid, rules, density, E, list, stat) {
    if (!rules.clutter || !rules.clutter.length) return;
    var world = zone.world, terrain = !!(zone.terrain || world.terrains.length);
    var rate = 0.03 * density * (rules.density === undefined ? 1 : rules.density) * (rules.clutterRate === undefined ? 1 : rules.clutterRate);
    for (var r = 1; r < grid.h - 1; r++) for (var c = 1; c < grid.w - 1; c++) {
      if (grid.rows[r][c] !== '.') continue;
      var near = 0, wx = 0, wz = 0;
      for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) { var q = grid.at(c + dc, r + dr); if (q !== '.' && q !== ' ') { near++; wx += dc; wz += dr; } }
      if (near < 2) continue;   // clutter gathers at bases, corners and round props, never in the open
      var h0 = hash(zone.idx * 6151 + c * 41, r * 29 + 5);
      if (h0 > rate * (1 + near * 0.3)) continue;
      var rr = rnd(Math.floor(h0 * 4294967296) ^ (zone.idx * 389 + 3));
      var name = pickW(rules.clutter, rr()); if (!hasPiece(name)) continue;
      // lean toward the walls / props round the cell
      var ln = Math.hypot(wx, wz) || 1, x = zone.ox + c + 0.5 + wx / ln * 0.25 + (rr() - 0.5) * 0.3, z = zone.oz + r + 0.5 + wz / ln * 0.25 + (rr() - 0.5) * 0.3;
      if (excluded(E, x, z)) { stat.skipC++; continue; }
      var yaw = name === 'CableRun' ? (Math.abs(wx) > Math.abs(wz) ? Math.PI / 2 : 0) : rr() * Math.PI * 2;
      var hmin = 1e9, hmax = -1e9;
      for (var k = 0; k < 5; k++) { var o = [[0, 0], [-0.3, -0.3], [0.3, -0.3], [-0.3, 0.3], [0.3, 0.3]][k], y = world.groundAt ? world.groundAt(x + o[0], z + o[1]) : 0; hmin = Math.min(hmin, y); hmax = Math.max(hmax, y); }
      if (hmax - hmin > (terrain ? 0.12 : 0.02) || hmin < -50) { stat.skipC++; continue; }
      list.push(IB.Assets.placed('KIT_DRESS_' + name, mat4(x, hmin + (terrain ? -0.01 : 0.004), z, yaw)));
      stat.clutter++;
    }
  }
  function wallClutter(zone, grid, theme, rules, density, E, list, stat) {
    if (!rules.wallClutter || !rules.wallClutter.length || !zone.wallMods) return;
    var rate = 0.12 * density * (rules.density === undefined ? 1 : rules.density) * (rules.clutterRate === undefined ? 1 : rules.clutterRate);
    var H = (theme.wall && theme.wall.height) || 3, DIR = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
    zone.wallMods.forEach(function (W) {
      var dir = DIR[W.face]; if (!dir) return;
      var h0 = hash(zone.idx * 2879 + W.c * 61, W.r * 23 + 19);
      if (h0 > rate || PLAIN_WALL_BAD.test(W.name)) return;
      var rr = rnd(Math.floor(h0 * 4294967296) ^ (zone.idx * 733 + 5));
      var name = pickW(rules.wallClutter, rr()), P = WALL_PIECES[name];
      if (!P || !hasPiece(name) || P.y + P.h / 2 > H - 0.1) return;
      var x = zone.ox + W.c + 0.5, z = zone.oz + W.r + 0.5, ex = x + dir[0], ez = z + dir[1];
      if (excluded(E, ex, ez) || grid.at(W.c + dir[0], W.r + dir[1]) !== '.') { stat.skipC++; return; }
      var tx = -dir[1], tz = dir[0], fam = IB.Assets.family[W.name], d0 = null, ok = true;
      [[0, 0], [-0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [0.5, 0.5]].forEach(function (pr) {
        if (!ok) return;
        var hit = wallHit(W.name, x, z, W.yaw, ex + tx * pr[0] * P.w, P.y + pr[1] * P.h, ez + tz * pr[0] * P.w, -dir[0], -dir[1]);
        if (!hit || !hit.face) { ok = false; return; }
        var n = hit.face.normal.clone().transformDirection(_mesh.matrixWorld);
        if (n.x * dir[0] + n.z * dir[1] < 0.95) { ok = false; return; }
        var cls = cellClass(fam, hit.uv); if (cls === 11 || cls === 14 || cls === 15) { ok = false; return; }
        if (d0 === null) d0 = hit.distance; else if (Math.abs(hit.distance - d0) > 0.012) ok = false;
      });
      if (!ok) { stat.skipC++; return; }
      var wxp = ex - dir[0] * (d0 - 0.002), wzp = ez - dir[1] * (d0 - 0.002);
      list.push(IB.Assets.placed('KIT_DRESS_' + name, mat4(wxp, P.y - P.h / 2, wzp, Math.atan2(dir[0], dir[1]))));
      stat.clutter++;
    });
  }

  D.build = function (level, look) {
    D.end();
    if (!IB.Look || !IB.Look.on || !IB.DECALS || !level) return;
    var R = IB.Render, theme = level.theme || {}, rules = (look && look.dress) || null;
    if (!rules || rules.off) return;
    var density = IB.LOOKS.tier(R.tier).density;
    if (!(density > 0)) return;
    var t0 = performance.now();
    level.zones.forEach(function (zone) {
      var grid = zone.grid, B = new Buf(), stat = { zone: zone.idx, floor: 0, wall: 0, clutter: 0, skip: 0, skipW: 0, skipC: 0 }, parts = [];
      var E = exclusions(level, zone, grid, theme), rand = rnd(zone.idx * 7 + 1);
      floorDecals(level, zone, grid, theme, rules, density, E, B, rand, stat);
      wallDecals(level, zone, grid, theme, rules, density, E, B, rand, stat);
      floorClutter(zone, grid, rules, density, E, parts, stat);
      wallClutter(zone, grid, theme, rules, density, E, parts, stat);
      var m = B.mesh();
      if (m) { m.updateMatrix(); zone.group.add(m); zone.dress = m; D.meshes.push(m); }
      if (parts.length && IB.Assets.mat.dress) {   // one merged mesh per zone, the family's own world material
        var cm = new THREE.Mesh(IB.Assets.merge(parts), IB.Assets.mat.dress);
        cm.userData.dress = true; zone.group.add(cm); zone.clutter = cm; D.meshes.push(cm);
      }
      D.stats.push(stat);
    });
    D.ms = Math.round(performance.now() - t0);
  };
  D.end = function () {
    D.meshes.forEach(function (m) { if (m.parent) m.parent.remove(m); m.geometry.dispose(); });
    D.meshes = []; D.stats = [];
  };
})(window.IB = window.IB || {});
