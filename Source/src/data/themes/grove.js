/* Theme: Redwood Hollow (kit-grove) -- an old-growth redwood forest on rolling ground, with a walkway level 9 m up.
   Rolling mounds and diagonal ridges (theme.terrain: a heightfield the player, robots, bullets, pickups and props all
   follow; terrain.paint tints the ground: dirt trails, wet mud along the creek, needle duff under the giants), mossy
   cliffs and root-bound earth faces for walls, and climbable redwoods ('Z', 8 x 8) whose railed staircase wraps three sides of
   the trunk (0.375 m rises, collision kind 'step') up to a plank platform at 9 m. Plank bridges ('=' in the zone
   file's "@layer 9" grid) on trestle piers join the platforms; the platform rails are layer-9 pieces too, so a bridge
   can land on any side but the stairwell's. Robots climb the stairs: the nav grid holds every walkable surface
   (ground, treads, platforms, bridges) and the flow field leads them up to a player in the trees.
   Built by blender/fam_kit_grove.py; zone layouts by tools/grove_zones.py (src/data/zones/grove_*.txt).
   The wall modules carry the ridge slope behind them (a crest ~4.5 m above the cliff tops), so the hollow is ringed
   by forested ridges, notched where the trails pass. Backdrop (backdrop.build): a forest floor around the level, more
   giant trunks outside the walls (kept off the trails), and warm light shafts slanting down through the canopy
   (additive, unlit); trunks and shafts are merged per zone and hidden with it.

   Symbols: Z climbable redwood [8,8]  Y giant redwood [4,4]  y young redwood  x snag [2,2]  u stump [2,2]
            L fallen giant [6,2]  l log [3,1]  R boulder [2,2]  r rock  b shrub / huckleberry  n fern  v oxalis
            m mushrooms  w trilliums  p pebbles  e sedge  k creek  W pond [5,5]  C ranger station [7,6]  T tent [3,3]
            F campfire [3,3]  d woodpile [2,1]  i signpost  j lantern  c crate  q barrel  J bridge pier [1,2]
            : dirt trail (ground paint only)   layer 9: = bridge  ^ _ [ ] rail (N S W E edge)  1 2 3 4 rail corner */
(function (IB) {
  'use strict';
  function hgt(c, r, zi) {
    var k = zi * 1.7;
    var mounds = 1.2 * Math.sin(0.19 * c + 1.3 + k) * Math.sin(0.17 * r + 0.6 + k) + 0.6 * Math.sin(0.41 * c - 0.27 * r + k);
    var band = ((r + 0.35 * c + 7 * zi) % 18 + 18) % 18, ridge = 1.8 * Math.max(0, 1 - Math.abs(band - 9) / 3.8);
    return Math.max(0, 0.74 * (1.0 + mounds + ridge));   // slopes stay under the robots' 0.4 m step per nav cell
  }
  // ground tint per terrain vertex (c, r): the four cells around it
  function paint(c, r, zi, g) {
    var trail = 0, water = 0, tree = 0, wet = 0, dc, dr, ch;
    for (dr = -1; dr <= 0; dr++) for (dc = -1; dc <= 0; dc++) {
      ch = g.at(c + dc, r + dr);
      if (ch === ':') trail++; else if (ch === 'k' || ch === 'W') water++; else if ('ZYxu'.indexOf(ch) >= 0) tree++;
    }
    if (water) return ['#5B4733', 0.9];
    for (dr = -3; dr <= 2; dr++) for (dc = -3; dc <= 2; dc++) { ch = g.at(c + dc, r + dr); if (ch === 'k' || ch === 'W') wet++; }
    if (trail) return ['#A9825A', 0.3 + 0.16 * trail];
    if (wet) return ['#4F8A36', Math.min(0.7, 0.12 * wet)];
    if (tree) return ['#8B5E3A', 0.5 + 0.1 * tree];
    var m = Math.sin(c * 0.31 + r * 0.17 + zi * 2.1) + Math.sin(c * 0.13 - r * 0.29 + 2.0) + 0.5 * Math.sin(c * 0.71 + r * 0.53);
    if (m > 0.8) return ['#7DBE4A', Math.min(0.65, (m - 0.8) * 1.3)];      // oxalis carpets
    if (m < -0.9) return ['#7A5636', Math.min(0.6, (-0.9 - m) * 1.1)];     // dark needle duff
    return null;
  }
  // ---------------------------------------------------------------- zone edges: cliffs / banks, 2 m modules
  var SOLID = '#GE';
  function solid(g, c, r) { return SOLID.indexOf(g.at(c, r)) >= 0; }
  function faceOf(g, c, r) {
    var oS = !solid(g, c, r + 1), oN = !solid(g, c, r - 1), oE = !solid(g, c + 1, r), oW = !solid(g, c - 1, r);
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
  function inRun(g, c, r, F) { return g.at(c, r) === '#' && faceOf(g, c, r) === F && gateDist(g, c, r) > 2.6; }
  var STYLES = ['Cliff', 'Cliff', 'Roots', 'Cliff', 'Cliff', 'Cliff', 'Roots', 'Cliff', 'Cliff'];
  function chooseWall(c, r, horiz, corner, hash, g) {
    var F = faceOf(g, c, r);
    if (F === 'none' || F === 'corner') return hash(c * 3 + 1, r * 7 + 2) < 0.5 ? 'Corner_A' : 'Corner_B';
    if (gateDist(g, c, r) < 2.6) return null;          // the gate frame's rock jambs fill the cells beside a gate
    var along = F === 'S' || F === 'N', u = along ? c : r;
    var seg = Math.floor(u / 7), st = STYLES[Math.floor(hash(seg * 13 + (along ? r : c) * 7 + 3, along ? 1 : 2) * STYLES.length)];
    if (u % 2 === 0) return st + ((u >> 1) % 2 ? '_B' : '_A');   // 2 m module, centred on its cell; A / B alternate
    var prev = along ? inRun(g, c - 1, r, F) : inRun(g, c, r - 1, F), next = along ? inRun(g, c + 1, r, F) : inRun(g, c, r + 1, F);
    var pc = along ? faceOf(g, c - 1, r) : faceOf(g, c, r - 1), nc = along ? faceOf(g, c + 1, r) : faceOf(g, c, r + 1);
    if ((!prev && (pc === 'corner' || pc === 'none')) || (!next && (nc === 'corner' || nc === 'none'))) return null;   // the corner pile covers it
    return (!prev || !next) ? st + '_1' : null;          // odd cells are covered by their neighbours' 2 m modules
  }

  // ---------------------------------------------------------------- forest outside the walls (zones.js backdrop.build)
  var SUN = [0.5, 0.82, 0.3];
  function buildForest(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var zones = level.zones, theme = level.theme, hash = api.hash;
    var bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
    zones.forEach(function (z) { bx0 = Math.min(bx0, z.ox); bx1 = Math.max(bx1, z.ox + z.w); bz0 = Math.min(bz0, z.oz); bz1 = Math.max(bz1, z.oz + z.h); });
    if (level.hatch) bz0 = Math.min(bz0, level.hatch.z - 10);
    // forest floor (one quad far past the fog) with darker duff and fern-green patches
    api.geo.flat([[bx0 - 160, bz0 - 160], [bx1 + 160, bz0 - 160], [bx1 + 160, bz1 + 160], [bx0 - 160, bz1 + 160]], -0.03, new THREE.Color('#62803A'));
    // keep-outs: the zones (and their wall modules), the trails between them, the hatch path, the entry behind zone 1
    var keep = [];
    zones.forEach(function (z) { keep.push([z.ox - 1.2, z.oz - 1.2, z.ox + z.w + 1.2, z.oz + z.h + 1.2]); });
    level.trails.forEach(function (t) { keep.push([t.x - 4.2, Math.min(t.z0, t.z1) - 1, t.x + 4.2, Math.max(t.z0, t.z1) + 1]); });
    if (level.hatch) keep.push([level.hatch.x - 6, level.hatch.z - 6, level.hatch.x + 6, level.hatch.z0 + 1]);
    function clear(x, z, r) {
      for (var i = 0; i < keep.length; i++) { var k = keep[i]; if (x > k[0] - r && x < k[2] + r && z > k[1] - r && z < k[3] + r) return false; }
      return true;
    }
    function zoneOf(x, z) {   // nearest zone (each outside point dresses one zone's group, hidden with it)
      var best = 0, bd = 1e9;
      zones.forEach(function (Z, i) {
        var dx = Math.max(Z.ox - x, 0, x - Z.ox - Z.w), dz = Math.max(Z.oz - z, 0, z - Z.oz - Z.h), d = Math.hypot(dx, dz);
        if (d < bd) { bd = d; best = i; }
      });
      return { i: best, d: bd };
    }
    var lists = zones.map(function () { return {}; });
    var _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _p = new THREE.Vector3(), _s = new THREE.Vector3();
    function put(zi, name, x, y, z, yaw, s) {
      var full = IB.themePiece(theme, name), fam = IB.Assets.family[full];
      _q.setFromAxisAngle(_up, yaw); _p.set(x, y, z); _s.set(s, s, s);
      (lists[zi][fam] || (lists[zi][fam] = [])).push(IB.Assets.placed(full, new THREE.Matrix4().compose(_p, _q, _s)));
    }
    // giant trunks: a near ring right behind the walls (their crowns close the sky line) and a looser mid ring
    var step = 10, gx, gz, k = 0;
    for (gx = bx0 - 40; gx <= bx1 + 40; gx += step) for (gz = bz0 - 40; gz <= bz1 + 40; gz += step) {
      k++;
      var x = gx + (hash(k, 3) - 0.5) * step * 0.8, z = gz + (hash(k, 5) - 0.5) * step * 0.8, Z = zoneOf(x, z), s;
      if (Z.d < 10) {
        s = 0.8 + hash(k, 7) * 0.55;
        if (!clear(x, z, 1.5 + 2.1 * s)) continue;
        put(Z.i, hash(k, 9) < 0.5 ? 'Backdrop_Trunk_A' : 'Backdrop_Trunk_B', x, 0, z, hash(k, 11) * 6.28, s);
      } else if (Z.d < 34 && hash(k, 13) < 0.4) {
        s = 0.75 + hash(k, 7) * 0.45;
        if (!clear(x, z, 3)) continue;
        put(Z.i, hash(k, 9) < 0.6 ? 'Backdrop_Trunk_C' : 'Backdrop_Trunk_A', x, 0, z, hash(k, 11) * 6.28, s);
      }
    }
    zones.forEach(function (Z, i) {
      Object.keys(lists[i]).forEach(function (fam) {
        var m = new THREE.Mesh(IB.Assets.merge(lists[i][fam]), IB.Assets.mat[fam]);
        Z.group.add(m);
      });
    });
    // light shafts: crossed quads slanting toward the sun, warm and additive, brightest a few metres up
    var mat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
    var sv = new THREE.Vector3(SUN[0], SUN[1], SUN[2]).normalize(), u1 = new THREE.Vector3().crossVectors(sv, _up).normalize(), u2 = new THREE.Vector3().crossVectors(sv, u1).normalize();
    var PROF = [[0, 0.0], [0.07, 0.12], [0.4, 0.08], [1, 0.0]];   // (fraction of length, intensity)
    zones.forEach(function (Z, zi) {
      var pos = [], cols = [], idx = [], n = 0, L = 42;
      for (var tries = 0; tries < 60 && n < 7; tries++) {
        var c = 4 + Math.floor(hash(zi * 31 + tries, 41) * (Z.w - 8)), r = 4 + Math.floor(hash(zi * 31 + tries, 43) * (Z.h - 8));
        if ('.:nvwpe'.indexOf(Z.grid.at(c, r)) < 0) continue;
        n++;
        var x = Z.ox + c + 0.5, z = Z.oz + r + 0.5, y = level.world.groundAt(x, z), w = 1.6 + hash(zi, tries) * 2.2;
        [u1, u2].forEach(function (u) {
          var base = pos.length / 3;
          PROF.forEach(function (P) {
            var t = P[0] * L, wi = w * (0.8 + 0.5 * P[0]), I = P[1];
            for (var sgn = -1; sgn <= 1; sgn += 2) {
              pos.push(x + sv.x * t + u.x * wi * sgn / 2, y + sv.y * t + u.y * wi * sgn / 2, z + sv.z * t + u.z * wi * sgn / 2);
              cols.push(1.0 * I, 0.93 * I, 0.62 * I);
            }
          });
          for (var q = 0; q < PROF.length - 1; q++) { var a = base + q * 2; idx.push(a, a + 1, a + 3, a, a + 3, a + 2); }
        });
      }
      if (!n) return;
      var g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
      g.setIndex(idx);
      var mesh = new THREE.Mesh(g, mat);
      mesh.renderOrder = 5; mesh.frustumCulled = false;
      Z.group.add(mesh);
    });
    api.tick(function (dt, t) { var v = 0.85 + 0.15 * Math.sin(t * 0.45); mat.color.setRGB(v, v, v); });
  }

  var R90 = Math.PI / 2;
  var PIECES = ['Landmark_Redwood_A', 'Landmark_Redwood_B', 'Landmark_Giant_A', 'Landmark_Giant_B', 'Redwood_Young_A', 'Redwood_Young_B',
    'Redwood_Young_C', 'Snag', 'Stump', 'Log_Big', 'Log_Small', 'Rock_A', 'Rock_B', 'Boulder_A', 'Boulder_B', 'Pebbles', 'Fern_A', 'Fern_B',
    'Fern_C', 'Shrub_A', 'Shrub_B', 'Huckleberry', 'Clover_A', 'Clover_B', 'Mushrooms_A', 'Mushrooms_B', 'Trillium', 'Sedge', 'Creek_A',
    'Creek_B', 'Creek_C', 'Pond', 'Landmark_Cabin', 'Tent', 'Campfire', 'Woodpile', 'Signpost', 'Lantern', 'Crate', 'Barrel', 'Bridge',
    'Rail', 'Rail_Corner', 'Pier', 'Cliff_A', 'Cliff_B', 'Cliff_1', 'Roots_A', 'Roots_B', 'Roots_1', 'Corner_A', 'Corner_B', 'GateFrame',
    'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Backdrop_Trunk_A', 'Backdrop_Trunk_B', 'Backdrop_Trunk_C'];

  IB.registerTheme({
    id: 'grove', name: 'Redwood Hollow', family: 'kit-grove', prefix: 'KIT_GROVE_',
    palette: ['#9C4A2B', '#2E7840', '#E3A645', '#7ECB58'],
    env: { sky: ['#86C0E0', '#DEE5C8'], fog: { color: '#DEE5C8', near: 24, far: 112 }, sun: SUN, clouds: true, ceiling: null },
    floor: { color: '#72923F', trail: '#A9825A', outside: '#62803A' },
    terrain: { height: hgt, paint: paint, flat: 'ZWkCTFJ', ramp: [1, 5], low: '#6F8F3C', high: '#A4BA5A', patch: '#9A7347', top: 3 },
    wall: { height: 6, roof: '#5E8A3A', facing: 'open', choose: chooseWall },
    symbols: {
      'Z': { size: [8, 8], pieces: ['Landmark_Redwood_A', 'Landmark_Redwood_B'], face: 0, kind: 'step' },
      'Y': { size: [4, 4], pieces: ['Landmark_Giant_A', 'Landmark_Giant_B'], flip: true, kind: 'cover' },
      'y': { pieces: ['Redwood_Young_A', 'Redwood_Young_B', 'Redwood_Young_C'], rotate: 'random90', sink: true, kind: 'cover' },
      'x': { size: [2, 2], pieces: ['Snag'], flip: true, kind: 'cover' },
      'u': { size: [2, 2], pieces: ['Stump'], flip: true, kind: 'cover' },
      'L': { size: [6, 2], pieces: ['Log_Big'], flip: true, kind: 'cover' },
      'l': { size: [3, 1], pieces: ['Log_Small'], flip: true, kind: 'cover' },
      'R': { size: [2, 2], pieces: ['Boulder_A', 'Boulder_B'], flip: true, kind: 'cover' },
      'r': { pieces: ['Rock_A', 'Rock_B'], rotate: 'random90', sink: true, kind: 'cover' },
      'b': { pieces: ['Shrub_A', 'Shrub_B', 'Huckleberry'], rotate: 'random90', sink: true, kind: 'cover' },
      'n': { pieces: ['Fern_A', 'Fern_B', 'Fern_C'], rotate: 'random90', sink: true, collide: false },
      'v': { pieces: ['Clover_A', 'Clover_B'], rotate: 'random90', sink: true, collide: false },
      'm': { pieces: ['Mushrooms_A', 'Mushrooms_B'], rotate: 'random90', sink: true, collide: false },
      'w': { pieces: ['Trillium'], rotate: 'random90', sink: true, collide: false },
      'p': { pieces: ['Pebbles'], rotate: 'random90', sink: true, collide: false },
      'e': { pieces: ['Sedge'], rotate: 'random90', sink: true, collide: false },
      'k': { pieces: ['Creek_A', 'Creek_A', 'Creek_B', 'Creek_C'], rotate: 'random90', collide: false },
      'W': { size: [5, 5], pieces: ['Pond'], flip: true, collide: false },
      'C': { size: [7, 6], pieces: ['Landmark_Cabin'], kind: 'cover' },
      'T': { size: [3, 3], pieces: ['Tent'], flip: true, kind: 'cover' },
      'F': { size: [3, 3], pieces: ['Campfire'], kind: 'cover' },
      'd': { size: [2, 1], pieces: ['Woodpile'], flip: true, kind: 'cover' },
      'i': { pieces: ['Signpost'], rotate: 'random90', sink: true, kind: 'cover' },
      'j': { pieces: ['Lantern'], rotate: 'random90', sink: true, kind: 'cover' },
      'c': { pieces: ['Crate'], rotate: 'random90', sink: true, kind: 'cover' },
      'q': { pieces: ['Barrel'], rotate: 'random90', sink: true, kind: 'cover' },
      'J': { size: [1, 2], pieces: ['Pier'], kind: 'cover' },
      '=': { pieces: ['Bridge'], rotate: 'edge', kind: 'deck' },
      '^': { pieces: ['Rail'], rotate: 0, kind: 'cover' },
      '_': { pieces: ['Rail'], rotate: Math.PI, kind: 'cover' },
      '[': { pieces: ['Rail'], rotate: R90, kind: 'cover' },
      ']': { pieces: ['Rail'], rotate: -R90, kind: 'cover' },
      '1': { pieces: ['Rail_Corner'], rotate: 0, kind: 'cover' },
      '2': { pieces: ['Rail_Corner'], rotate: -R90, kind: 'cover' },
      '3': { pieces: ['Rail_Corner'], rotate: Math.PI, kind: 'cover' },
      '4': { pieces: ['Rail_Corner'], rotate: R90, kind: 'cover' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C'], height: 2.6 },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: { build: buildForest },
    budget: { prop: 2500, landmark: 8000, total: 60000 },
    allPieces: function () { return PIECES; },
    levels: {
      grove: {
        name: 'Redwood Hollow',
        intro: 'Climb the stairs up the giant redwoods and hold the walkways. The robots will climb after you.',
        zones: [
          { map: 'grove_1', waves: [[['crawler', 20], ['gunner', 5]], [['crawler', 5], ['bomber', 4], ['gunner', 4], ['blader', 6]], [['crawler', 4], ['drone', 5], ['gunner', 4], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['soldier', 7]]] },
          { map: 'grove_2', waves: [[['crawler', 20], ['gunner', 5], ['drone', 3]], [['crawler', 5], ['bomber', 5], ['gunner', 5], ['blader', 7]], [['crawler', 5], ['drone', 5], ['gunner', 5], ['soldier', 6]], [['crawler', 4], ['bomber', 4], ['gunner', 5], ['blader', 6]]] },
          { map: 'grove_3', waves: [[['crawler', 20], ['gunner', 8]], [['crawler', 5], ['bomber', 5], ['drone', 5], ['soldier', 7]], [['crawler', 7], ['gunner', 7], ['drone', 5], ['blader', 6]], [['crawler', 8], ['gunner', 8], ['bomber', 7], ['drone', 4], ['soldier', 12]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
