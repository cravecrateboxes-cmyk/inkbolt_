/* Theme: Lagoon Island (kit-island). A wide tropical island on a bright day with open ocean all around it: sandy
   beaches and grassy dunes, palm groves and jungle thickets, warm basalt rocks, tide pools, freshwater ponds with
   reeds and lily pads, a big lagoon lake with a palm islet, beach huts on stilts, boats pulled up on the sand, crates
   and barrels washed ashore, a ruined lookout, a red-and-white lighthouse and a small research outpost the robots
   have taken over. Built by blender/fam_kit_island.py; zone layouts by tools/island_zones.py
   (src/data/zones/island_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  edge walls (1 cell thick): jungle thickets, basalt outcrops, dunes behind a driftwood fence, in 8 m stretches.
        2 m modules sit on every even cell of a straight run (odd cells: nothing, or a 1 m module at a run end);
        corners and notches get round rock / jungle clumps; the cells beside a gate are left to the frame's jambs.
     { }  sea wall on a west / east zone edge that faces the ocean: a low rock-armoured breakwater with a tall
        collision box (the surf is right behind it: an honest barrier, not a cut-off world edge)
     o rock   O outcrop [2,2]   c crate (stacks)   b barrels   t palm   F palm clump [2,2]   x driftwood (runs)
     f driftwood fence (runs)   = sandbags (runs)   r reeds   p tiki torch / signpost   u beach umbrella
     B boat [4,2]   M grass [3,3]   D dune [3,3]   W pond [4,4]   w tide pool [3,3]   V lagoon [14,10]
     H beach hut [5,5]   L lighthouse [6,6]   T ruined lookout [4,4]   R research outpost [7,5]   A radio mast [2,2]
     Q solar array [3,2]   K robot charger [2,2]
   Water: ponds, tide pools and the lagoon are shallow, wadeable and walkable (no collision; the nav grid is open
   there); only the lagoon's palm islet blocks. Every flat decal sits on its own height in the kit, never on the floor.
   Trails are jungle paths: a boardwalk floor (floor.trailLines planks) between rope railings and hedges.
   Backdrop (backdrop.build, run by zones.js): the island ground is painted in code around the level from the zone
   footprints (grass, sand, wet sand, a foam line, turquoise shallows, deep blue sea out past the fog); the zone
   edges marked `sea` in the plan get a 4.5 m beach strip and then the water. Jungle canopy and palm groves fill the
   land outside the walls, palms and rocks line the shore, a jetty with a moored boat sits off each sea wall, buoys,
   a sailboat and islets dot the sea, an animated surf line and shimmer dashes play on the water. */
(function (IB) {
  'use strict';
  var SOLID = '#GE{}';
  function solid(g, c, r) { return SOLID.indexOf(g.at(c, r)) >= 0; }
  function faceOf(g, c, r) {
    var oS = !solid(g, c, r + 1), oN = !solid(g, c, r - 1), oE = !solid(g, c + 1, r), oW = !solid(g, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  // distance (cells) from a wall cell on the north / south edge to the centre of that edge's gate
  function gateDist(g, c, r) {
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function inRun(g, c, r, F) { return g.at(c, r) === '#' && faceOf(g, c, r) === F && gateDist(g, c, r) > 2.6; }
  var STYLES = ['Jungle', 'Jungle', 'Rocks', 'Jungle', 'Dune', 'Rocks', 'Jungle', 'Dune', 'Jungle'];
  function chooseWall(c, r, horiz, corner, hash, g) {
    var F = faceOf(g, c, r);
    if (F === 'none' || F === 'corner') return hash(c * 3 + 1, r * 7 + 2) < 0.5 ? 'Corner_A' : 'Corner_B';
    if (gateDist(g, c, r) < 2.6) return null;          // the gate frame's rock jambs fill the cells beside a gate
    var along = F === 'S' || F === 'N', u = along ? c : r;
    var seg = Math.floor(u / 8), st = STYLES[Math.floor(hash(seg * 13 + (along ? r : c) * 7 + 3, along ? 1 : 2) * STYLES.length)];
    if (u % 2 === 0) return st + (hash(c * 5 + 1, r * 3 + 7) < 0.5 ? '_A' : '_B');   // 2 m module, centred on its cell
    var prev = along ? inRun(g, c - 1, r, F) : inRun(g, c, r - 1, F), next = along ? inRun(g, c + 1, r, F) : inRun(g, c, r + 1, F);
    return (!prev || !next) ? st + '_1' : null;          // odd cells are covered by their neighbours' 2 m modules
  }
  var WALLS = ['Jungle_A', 'Jungle_B', 'Jungle_1', 'Rocks_A', 'Rocks_B', 'Rocks_1', 'Dune_A', 'Dune_B', 'Dune_1', 'Corner_A', 'Corner_B'];
  var SEAWALL = ['SeaWall_A', 'SeaWall_A', 'SeaWall_A', 'SeaWall_B', 'SeaWall_A', 'SeaWall_A', 'SeaWall_A', 'SeaWall_A', 'SeaWall_A', 'SeaWall_A', 'SeaWall_C', 'SeaWall_A', 'SeaWall_A', 'SeaWall_A'];

  // ---------------------------------------------------------------- island ground + backdrop (zones.js backdrop.build)
  var SEA_M = 4.5, LAND_M = 50;          // land beyond a zone edge: a beach strip on sea edges, wide island elsewhere
  // ground bands by signed distance from the coast (m, + = out to sea), each on its own height (outer = lower)
  var BANDS = [
    { d0: -9, d1: -1.2, y: -0.03, c: '#F0DAA0' },    // dry sand
    { d0: -1.2, d1: 0, y: -0.04, c: '#D7B983' },     // wet sand
    { d0: 0, d1: 1.3, y: -0.05, c: '#F6FFFF' },      // foam line
    { d0: 1.3, d1: 10, y: -0.08, c: '#5FD8D6' },     // turquoise shallows
    { d0: 10, d1: 26, y: -0.10, c: '#35B4D6' },      // reef blue
    { d0: 26, d1: 'far', y: -0.13, c: '#2687C6' }    // deep sea, out past the fog
  ];
  var GRASS = { y: -0.02, c: '#8FCB63' }, SURF = { y: -0.06, c: '#F6FFFF' };
  function sdRect(x, z, b, r) {
    var hx = (b.x1 - b.x0) / 2 - r, hz = (b.z1 - b.z0) / 2 - r;
    var qx = Math.abs(x - (b.x0 + b.x1) / 2) - hx, qz = Math.abs(z - (b.z0 + b.z1) / 2) - hz;
    return Math.hypot(Math.max(qx, 0), Math.max(qz, 0)) + Math.min(Math.max(qx, qz), 0) - r;
  }
  function smin(a, b, k) { var h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; }

  function buildIsland(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var zones = level.zones, last = zones.length - 1, hz = level.hatch ? level.hatch.z : zones[last].oz - 30;
    var rects = [], seaEdges = [], keep = [];
    zones.forEach(function (z, i) {
      var sea = (z.plan && z.plan.sea) || '';
      var mW = sea.indexOf('W') >= 0 ? SEA_M : LAND_M, mE = sea.indexOf('E') >= 0 ? SEA_M : LAND_M;
      rects.push({ x0: z.ox - mW, x1: z.ox + z.w + mE, z0: i === last ? Math.min(z.oz, hz) - 34 : z.oz - 6, z1: z.oz + z.h + (i === 0 ? 36 : 6) });
      if (mW === SEA_M) seaEdges.push({ x: z.ox, z0: z.oz, z1: z.oz + z.h, s: -1 });
      if (mE === SEA_M) seaEdges.push({ x: z.ox + z.w, z0: z.oz, z1: z.oz + z.h, s: 1 });
      keep.push([z.ox - 1.5, z.oz - 1.5, z.ox + z.w + 1.5, z.oz + z.h + 1.5]);
    });
    level.trails.forEach(function (t) { keep.push([t.x - 4, t.z1 - 1, t.x + 4, t.z0 + 1]); });
    if (level.hatch) keep.push([level.hatch.x - 5, level.hatch.z - 5, level.hatch.x + 5, level.hatch.z0 + 1]);
    function seaDist(x, z) {
      var d = 1e9;
      seaEdges.forEach(function (e) { var dz = Math.max(e.z0 - z, 0, z - e.z1); d = Math.min(d, Math.hypot(x - e.x, dz)); });
      return d;
    }
    // signed land field: < 0 on the island. Smooth union of the zone footprints with their margins, plus a slow
    // wobble that fades out near the sea walls (their beach strip stays exactly SEA_M wide)
    function field(x, z) {
      var f = 1e9;
      for (var i = 0; i < rects.length; i++) f = smin(f, sdRect(x, z, rects[i], 9), 14);
      var w = Math.min(1, Math.max(0, (seaDist(x, z) - 8) / 16));
      return f + w * (4.5 * Math.sin(x * 0.083 + z * 0.047 + 0.6) + 3.0 * Math.sin(x * 0.031 - z * 0.071 + 2.1));
    }
    var bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
    rects.forEach(function (b) { bx0 = Math.min(bx0, b.x0); bx1 = Math.max(bx1, b.x1); bz0 = Math.min(bz0, b.z0); bz1 = Math.max(bz1, b.z1); });
    var cx = (bx0 + bx1) / 2, cz = (bz0 + bz1) / 2, RMAX = Math.hypot(bx1 - bx0, bz1 - bz0) / 2 + 40;
    // coastline: outermost crossing along N rays from the island centre (star-shaped by construction)
    var N = 360, rad = [], i, k;
    for (i = 0; i < N; i++) {
      var a = i / N * Math.PI * 2, dx = Math.cos(a), dz = Math.sin(a), r = RMAX;
      while (r > 2 && field(cx + dx * r, cz + dz * r) > 0) r -= 2;
      var lo = r, hi = r + 2;
      for (k = 0; k < 12; k++) { var mid = (lo + hi) / 2; if (field(cx + dx * mid, cz + dz * mid) > 0) hi = mid; else lo = mid; }
      rad.push((lo + hi) / 2);
    }
    for (k = 0; k < 2; k++) rad = rad.map(function (v, j) { return 0.25 * rad[(j + N - 1) % N] + 0.5 * v + 0.25 * rad[(j + 1) % N]; });
    var C = rad.map(function (v, j) { var a = j / N * Math.PI * 2; return [cx + Math.cos(a) * v, cz + Math.sin(a) * v]; });
    var NRM = C.map(function (p, j) {
      var q0 = C[(j + N - 1) % N], q1 = C[(j + 1) % N], tx = q1[0] - q0[0], tz = q1[1] - q0[1], L = Math.hypot(tx, tz) || 1;
      return [tz / L, -tx / L];
    });
    function off(j, d) { return [C[j][0] + NRM[j][0] * d, C[j][1] + NRM[j][1] * d]; }
    function far(j) { var a = j / N * Math.PI * 2; return [cx + Math.cos(a) * 640, cz + Math.sin(a) * 640]; }
    var g = api.geo;
    for (i = 0; i < N; i++) {          // grass core (fan from the centre)
      var j1 = (i + 1) % N;
      g.flat([[cx, cz], off(i, BANDS[0].d0), off(j1, BANDS[0].d0)], GRASS.y, GRASS.c);
    }
    BANDS.forEach(function (B) {
      for (var i2 = 0; i2 < N; i2++) {
        var j2 = (i2 + 1) % N;
        var a0 = off(i2, B.d0), a1 = off(j2, B.d0), b1 = B.d1 === 'far' ? far(j2) : off(j2, B.d1), b0 = B.d1 === 'far' ? far(i2) : off(i2, B.d1);
        g.flat([a0, a1, b1, b0], B.y, B.c);
      }
    });

    // ---- pieces on the land and at sea
    var hash = api.hash;
    function pick(list, h) { return list[Math.min(list.length - 1, Math.floor(h * list.length))]; }
    var CANOPY = ['Backdrop_Jungle_A', 'Backdrop_Jungle_B'], GROVE = ['Backdrop_Palms_A', 'Backdrop_Palms_B', 'Backdrop_Jungle_A'];
    // jungle canopy right behind every land edge of every zone (seen over the thicket walls)
    zones.forEach(function (z, zi) {
      var sea = (z.plan && z.plan.sea) || '';
      var edges = [{ n: 'N', y: z.oz - 5.5, a: z.ox, b: z.ox + z.w, yaw: 0 }, { n: 'S', y: z.oz + z.h + 5.5, a: z.ox, b: z.ox + z.w, yaw: Math.PI }];
      if (sea.indexOf('W') < 0) edges.push({ n: 'W', x: z.ox - 5.5, a: z.oz, b: z.oz + z.h, yaw: Math.PI / 2 });
      if (sea.indexOf('E') < 0) edges.push({ n: 'E', x: z.ox + z.w + 5.5, a: z.oz, b: z.oz + z.h, yaw: -Math.PI / 2 });
      edges.forEach(function (e, ei) {
        for (var t = e.a + 4; t < e.b - 3; t += 10.5) {
          var hh = hash(zi * 31 + ei * 7 + Math.round(t), 17), x = e.x !== undefined ? e.x + (hh - 0.5) * 1.5 : t + (hh - 0.5) * 2, zz = e.y !== undefined ? e.y + (hh - 0.5) * 1.5 : t + (hh - 0.5) * 2;
          if (e.n === 'S' && zi > 0) break;                  // the gap between two zones is filled from the zone south of it
          if (e.n === 'N' && zi < last) zz = z.oz - 6;       // ... on the middle line of the 12 m gap
          var halfW = e.y !== undefined ? 5.2 : 3.2, halfD = e.y !== undefined ? 3.2 : 5.2;
          if (!keepOut(x, zz, halfW, halfD)) continue;
          if (field(x, zz) > -4) continue;
          api.add(pick(CANOPY, hash(zi + 3, Math.round(t * 3))), x, 0, zz, e.yaw + (hh > 0.5 ? Math.PI : 0), 0.95 + hh * 0.25);
        }
      });
    });
    function keepOut(x, z, hx, hzz) {
      for (var q = 0; q < keep.length; q++) { var K = keep[q]; if (x + hx > K[0] && x - hx < K[2] && z + hzz > K[1] && z - hzz < K[3]) return false; }
      return true;
    }
    // palm groves and more jungle further inland
    for (var gx = bx0; gx < bx1; gx += 24) for (var gz = bz0; gz < bz1; gz += 24) {
      var h1 = hash(Math.round(gx) + 500, Math.round(gz) + 500), px = gx + (h1 - 0.5) * 10, pz = gz + (hash(Math.round(gx), Math.round(gz) + 77) - 0.5) * 10;
      if (field(px, pz) > -11 || !keepOut(px, pz, 11, 11)) continue;
      api.add(pick(GROVE, hash(Math.round(px), 91)), px, 0, pz, h1 * 6.28, 0.9 + h1 * 0.4);
    }
    // the shore: palms leaning out over the sand, rocks in the surf (none in front of a sea wall's view lane)
    for (i = 0; i < N; i += 3) {
      var hs = hash(i, 301);
      var nearSea = seaDist(C[i][0], C[i][1]) < 10;
      if (hs < 0.45 && !nearSea) {
        var p1 = off(i, -5 - hs * 4);
        if (keepOut(p1[0], p1[1], 2, 2)) api.add(pick(['Palm_A', 'Palm_B', 'Palm_C'], hash(i, 302)), p1[0], 0, p1[1], Math.atan2(NRM[i][0], NRM[i][1]) + Math.PI, 1.0 + hs * 0.3);
      } else if (hs > 0.86) {
        var p2 = off(i, nearSea ? 5 + hs * 3 : 1.5);
        api.add('Backdrop_Rocks', p2[0], -0.005, p2[1], hs * 9.0, 0.8 + hs * 0.5);
      }
    }
    // off each sea wall: a jetty running out from the beach with a boat tied up, rocks off the ends of the wall
    seaEdges.forEach(function (e, ei) {
      var zc = (e.z0 + e.z1) / 2 + (ei % 2 ? 8 : -8), x0 = e.x + e.s * (SEA_M + 1.5);
      api.add('Jetty', x0 + e.s * 4, 0, zc, e.s > 0 ? -Math.PI / 2 : Math.PI / 2, 1);
      api.add('Boat_A', x0 + e.s * 5.5, -0.16, zc + 2.4, 0, 1);
      api.add('Backdrop_Rocks', e.x + e.s * 9, -0.005, e.z0 + 3, 1.3 + ei, 1.1);
      api.add('Backdrop_Rocks', e.x + e.s * 10, -0.005, e.z1 - 4, 2.1 + ei, 0.9);
    });
    // at sea: buoys, a sailboat and islets (inside the fog's reach, so they read as far away rather than vanish)
    var sea = [['Backdrop_Buoy', 16, 22, 1, 0.08], ['Backdrop_Sailboat', 60, 75, 1.4, 0.0], ['Backdrop_Islet_A', 62, 80, 1.2, 0.0], ['Backdrop_Islet_B', 45, 60, 1.0, 0.0]];
    var counts = [6, 3, 4, 5];
    sea.forEach(function (S, si) {
      for (var n = 0; n < counts[si]; n++) {
        var j = Math.floor((n + hash(si, n) * 0.6 + si * 0.21) / counts[si] * N) % N, d = S[1] + (S[2] - S[1]) * hash(n, si + 40);
        var p = off(j, d);
        api.add(S[0], p[0], -0.1 - S[4], p[1], hash(n, si) * 6.28, S[3] * (0.85 + 0.3 * hash(si, n + 9)));
      }
    });

    // ---- animated water: a surf line breathing in and out along the shore, shimmer dashes blinking on the sea
    if (!THREE || !IB.Assets || !level.root) return;
    var sg = new IB.Geo();
    for (i = 0; i < N; i++) { var jj = (i + 1) % N; sg.flat([off(i, 2), off(jj, 2), off(jj, 2.6), off(i, 2.6)], SURF.y, SURF.c); }
    var surf = new THREE.Mesh(sg.build(), IB.Zones.mat);
    surf.frustumCulled = false;
    level.root.add(surf);
    var spos = surf.geometry.attributes.position;
    var GL = IB.themePiece(IB.THEME_DEFS.island, 'Sea_Glint'), NG = 150;
    var gm = IB.Assets.get(GL) && new THREE.InstancedMesh(IB.Assets.get(GL), IB.Assets.material(GL), NG);
    var gl = [];
    for (i = 0; i < NG; i++) {
      var jg = Math.floor(hash(i, 601) * N), dg = 5 + Math.pow(hash(i, 602), 1.6) * 70, pg = off(jg, dg);
      gl.push({ x: pg[0], z: pg[1], yaw: Math.atan2(NRM[jg][0], NRM[jg][1]) + Math.PI / 2, ph: hash(i, 603) * 6.28, sp: 0.6 + hash(i, 604) * 0.8, s: 0.8 + hash(i, 605) * 1.2 });
    }
    if (gm) { gm.frustumCulled = false; level.root.add(gm); }
    var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);
    api.tick(function (dt, t) {
      var w = 0.45 * Math.sin(t * 0.7) + 0.25 * Math.sin(t * 1.9 + 1.0);
      for (var q = 0; q < N; q++) {
        var j3 = (q + 1) % N, dd = 2.2 + w + 0.25 * Math.sin(q * 0.37 + t * 1.3), dd1 = 2.2 + w + 0.25 * Math.sin(j3 * 0.37 + t * 1.3);
        var A = off(q, dd), Bv = off(j3, dd1), Cc = off(j3, dd1 + 0.55), D = off(q, dd + 0.55);
        spos.setXYZ(q * 4, A[0], SURF.y, A[1]); spos.setXYZ(q * 4 + 1, Bv[0], SURF.y, Bv[1]);
        spos.setXYZ(q * 4 + 2, Cc[0], SURF.y, Cc[1]); spos.setXYZ(q * 4 + 3, D[0], SURF.y, D[1]);
      }
      spos.needsUpdate = true;
      if (!gm) return;
      for (var q2 = 0; q2 < gl.length; q2++) {
        var G = gl[q2], s = Math.max(0, Math.sin(t * G.sp + G.ph)) * G.s;
        _q.setFromAxisAngle(UP, G.yaw); _p.set(G.x, -0.06, G.z); _s.set(s + 0.001, 1, s + 0.001);
        gm.setMatrixAt(q2, _m.compose(_p, _q, _s));
      }
      gm.instanceMatrix.needsUpdate = true;
    });
  }

  var OTHER = ['SeaWall_A', 'SeaWall_B', 'SeaWall_C', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Fern', 'TrailWall_Torch',
    'TrailWall_Palm', 'Hatch', 'Jetty', 'Boat_A', 'Palm_A', 'Palm_B', 'Palm_C', 'Backdrop_Jungle_A', 'Backdrop_Jungle_B',
    'Backdrop_Palms_A', 'Backdrop_Palms_B', 'Backdrop_Rocks', 'Backdrop_Islet_A', 'Backdrop_Islet_B', 'Backdrop_Buoy',
    'Backdrop_Sailboat', 'Sea_Glint'];

  IB.registerTheme({
    id: 'island', name: 'Lagoon Island', family: 'kit-island', prefix: 'KIT_ISLAND_',
    palette: ['#2FA0E8', '#3DAA5C', '#F2DDA4', '#5FD8D6'],
    // bright tropical noon: deep blue zenith, pale sea-haze horizon; the fog is the horizon colour, so the ocean
    // runs out into the sky with no edge
    env: { sky: ['#2F9BEA', '#D2F0FF'], fog: { color: '#D2F0FF', near: 60, far: 140 }, sun: [0.45, 0.85, 0.3], clouds: true, ceiling: null },
    // sand everywhere in the zones; the trails between them are plank boardwalks
    floor: { color: '#EFD9A2', trail: '#C8955E', outside: '#8FCB63',
      trailLines: [{ dir: 'x', every: 0.42, width: 0.05, color: '#9E6C3E', y: 0.009 }] },
    wall: { height: 4.2, roof: '#3DAA5C', facing: 'open', choose: chooseWall },
    symbols: {
      '{': { pieces: SEAWALL, rotate: Math.PI / 2, h: 4.2, kind: 'wall' },
      '}': { pieces: SEAWALL, rotate: -Math.PI / 2, h: 4.2, kind: 'wall' },
      'o': { pieces: ['Rock_A', 'Rock_B', 'Rock_C'], rotate: 'random90', h: 1.1, kind: 'cover' },
      'O': { size: [2, 2], pieces: ['Outcrop_A', 'Outcrop_B'], flip: true, kind: 'cover' },
      'c': { pieces: ['Crate_A', 'Crate_B'], rotate: 'random90', h: 0.86, stack: { piece: 'Crate_Small', chance: 0.3, h: 0.48 }, kind: 'cover' },
      'b': { pieces: ['Barrel_A', 'Barrel_B'], rotate: 'random90', h: 0.9, kind: 'cover' },
      't': { pieces: ['Palm_A', 'Palm_B', 'Palm_C'], rotate: 'random90', kind: 'cover' },
      'F': { size: [2, 2], pieces: ['PalmClump_A', 'PalmClump_B'], flip: true, kind: 'cover' },
      'x': { pieces: ['Driftwood'], rotate: 'run', kind: 'cover' },
      'f': { pieces: ['Fence'], rotate: 'run', kind: 'cover' },
      '=': { pieces: ['Sandbags'], rotate: 'run', kind: 'cover' },
      'r': { pieces: ['Reeds'], rotate: 'random90', collide: false },
      'p': { pieces: ['TikiTorch', 'Signpost', 'TikiTorch'], sequence: true, kind: 'deco' },
      'u': { pieces: ['Umbrella'], rotate: 'random90', kind: 'deco' },
      'B': { size: [4, 2], pieces: ['Boat_A', 'Boat_B'], flip: true, kind: 'cover' },
      'M': { size: [3, 3], pieces: ['Grass_A', 'Grass_B'], flip: true, collide: false },
      'D': { size: [3, 3], pieces: ['Dune_Patch_A', 'Dune_Patch_B'], flip: true, collide: false },
      'W': { size: [4, 4], pieces: ['Pond_A', 'Pond_B'], flip: true, collide: false },
      'w': { size: [3, 3], pieces: ['TidePool_A', 'TidePool_B'], flip: true, collide: false },
      'V': { size: [14, 10], pieces: ['Lagoon'], flip: true, kind: 'cover' },
      'H': { size: [5, 5], pieces: ['Landmark_Hut'], flip: true, kind: 'wall' },
      'L': { size: [6, 6], pieces: ['Landmark_Lighthouse'], kind: 'wall' },
      'T': { size: [4, 4], pieces: ['Landmark_Lookout'], flip: true, kind: 'wall' },
      'R': { size: [7, 5], pieces: ['Landmark_Outpost'], flip: true, kind: 'wall' },
      'A': { size: [2, 2], pieces: ['Mast'], kind: 'cover' },
      'Q': { size: [3, 2], pieces: ['Solar'], flip: true, kind: 'cover' },
      'K': { size: [2, 2], pieces: ['Charger'], flip: true, kind: 'cover' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // jungle path: rope railing and hedge, with ferns, tiki torches and palms mixed in per module
    trail: { wall: 'TrailWall', height: 2.6, variants: ['TrailWall', 'TrailWall_Fern', 'TrailWall_Torch', 'TrailWall_Palm', 'TrailWall_Fern'] },
    hatch: 'Hatch', stand: 'Crate_A',
    backdrop: { build: buildIsland },
    budget: { prop: 1600, landmark: 4000, total: 80000 },
    allPieces: function () {
      var out = WALLS.concat(OTHER);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        sym[ch].pieces.concat(sym[ch].stack ? [sym[ch].stack.piece] : []).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      island: {
        name: 'Lagoon Island',
        intro: 'The robots have taken the island. Clear the beach, the lagoon, then their outpost at the lighthouse.',
        zones: [
          // Landing Beach (sea wall to the east): 40 robots
          { map: 'island_beach', sea: 'E', waves: [
            [['crawler', 8], ['gunner', 2]],
            [['crawler', 4], ['bomber', 2], ['gunner', 2], ['blader', 2]],
            [['crawler', 4], ['drone', 2], ['gunner', 1], ['soldier', 2]],
            [['crawler', 3], ['bomber', 2], ['gunner', 2], ['soldier', 2]]] },
          // The Lagoon (sea wall to the west): 42 robots, drones over the water
          { map: 'island_lagoon', sea: 'W', waves: [
            [['crawler', 8], ['gunner', 2], ['drone', 1]],
            [['crawler', 4], ['bomber', 3], ['gunner', 2], ['blader', 2]],
            [['crawler', 4], ['drone', 3], ['gunner', 2], ['soldier', 2]],
            [['crawler', 3], ['bomber', 2], ['gunner', 2], ['blader', 2]]] },
          // Lighthouse Point and the robots' outpost (sea wall to the east): 52 robots, the dense finale
          { map: 'island_point', sea: 'E', waves: [
            [['crawler', 8], ['gunner', 3]],
            [['crawler', 4], ['bomber', 3], ['drone', 2], ['soldier', 2]],
            [['crawler', 5], ['gunner', 3], ['drone', 2], ['blader', 2]],
            [['crawler', 6], ['gunner', 4], ['bomber', 3], ['drone', 1], ['soldier', 4]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
