/* Theme: Cinder Ridge Outpost (kit-frontier) -- the last campaign map: a remote frontier settlement in a log stockade
   on a ridge, a ring of snow-capped mountains and endless conifer forest to the horizon, clear late-morning light.
   The defenders' modern supply gear (a diesel generator, solar rows, a radio mast, fuel tanks) stands among the
   rustic timber. Two zones:
   1 The settlement (72 x 70): the log palisade with the main gate and the back gate, timber watchtowers (a stair up to
     a roofed platform 3.6 m up) in the four corners, the main street under the CINDER RIDGE OUTPOST arch, the HOLLIS
     GENERAL STORE (walk-in, a stair to the upstairs storeroom and room, open windows over the street), the CINDER
     RIDGE TRADING POST (walk-in: the counter, goods, the radio desk), the BUNKHOUSE (walk-in: bunks, the mess table),
     log cabins and plank houses (repainted per copy), the CLAIMS & RADIO office, the SMITHY on the square (forge,
     anvil, quench tub), the water tower (landmark) and the well in the square, hitching rails and troughs, wagons and
     carts, the corral and the stable in the west yard, the supply depot in the east yard, woodlots.
   2 The edge of the wild (76 x 72): beyond the back gate, flat ground in the south and two plateaus 3.2 m up in the
     north (theme.terrain) split by a ravine whose floor runs north to the exit gate; the rope bridge joins the
     plateaus; the lookout platform (landmark) on the west plateau's cliff edge faces the wilderness valley; the
     creek runs from its spring at the north wall down the east side past the BRANNOCK SAWMILL, its water wheel (it
     turns) and the flume; CAMP 9 (cook house, wall tents, fire pit, sawhorse, tool rack, log piles); the OLD
     LANTERN MINE in its outcrop on the west wall; groves, fallen trees and boulders as cover; trails up the slopes.
   Built by blender/fam_kit_frontier.py (fr_*.py); zone layouts by tools/frontier_zones.py (src/data/zones/frontier_*.txt).

   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled; R90 / -R90 = front east / west):
     # wall: zone 1 the log palisade (2 logs a metre, rails inside, braced / lantern / patched variants, corner
       bundles); zone 2 the forest edge (rock lumps, some with a conifer) and the rim behind a cliff lip
     ground paint only: , grass   : packed dirt (street, square, trails)   ; trodden earth   . ground
     Zone 1: H general store [10,10] R90   T trading post [10,9] -R90   B bunkhouse [12,8] R90   M smithy [8,7] -R90
             K k log cabin [8,7] R90 / -R90   U u plank house [8,7] R90 / -R90 (both repainted per copy)
             O claims & radio office [8,8] -R90   L stable [10,6] R90   Y y watchtower [3,8] stair south / north
             W water tower [6,6] (landmark)   w well [3,3]   A street arch [12,1] (only its posts collide)
             f corral fence (runs)   r hitching rail [3,1]   t trough [2,1]   b hay bales [2,1]   V covered wagon [3,6]
             v hand cart [2,3]   c crates   $ supply crate   x barrels   d fuel drums   e firewood [2,1]
             q chopping block   l lantern post   n signpost   g generator [2,3]   z solar row [4,2] (to the south)
             m radio mast [2,2]   F fuel tank [3,6]   N supply tent [4,5]   o cable spool   p conifer   j stump
     Zone 2: { } cliff lip (west column / north row: 0.9 m of rock above the plateau, a log rail)   [ ] low lip
             (where a plateau falls away)
             R Q ravine bank west / east (rock wall from the ravine floor past the plateau)   ( ) low bank
             = rope bridge [7,2] (its cribs close the banks under it)   X lookout platform [8,8] (landmark)
             I sawmill [10,8]   J water wheel frame [3,6] (the rotor turns, backdrop.build)   | flume [1,4]
             ~ creek water   Z spring and falls [4,2]   D log deck [6,3]   7 log pile [4,2]   8 lumber [3,2]
             9 felled log [5,1]   0 fallen tree [8,2]   1 boulder [2,2]   ` rock   @ grove [3,3]   ' fern
             C cook house [6,5]   3 wall tent [4,5]   5 fire pit [3,3]   6 sawhorse [2,1]   & log arch [3,5]
             % tool rack [2,1]   ! camp sign   * old mine [8,5] R90 (against the west wall)   + radio relay [2,2]
             ^ lean-to [4,3]   (and c d g j p q $ as in zone 1)
   Terrain (zone 2): plateau height terrainHeight(c, r) at cell corners (the same function as tools/frontier_zones.py),
   ramp [0, 1]: the lips, banks and walls carry the steps, every open slope stays climbable for the robots. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var PLAT = 3.2;

  // ---------------------------------------------------------------- terrain
  function fall(v, a, b) { return v <= a ? 1 : v >= b ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * (v - a) / (b - a)); }
  function terrainHeight(c, r, zi) {
    if (zi !== 1) return 0;
    if (c <= 30) return PLAT * fall(r, 21, 29);
    if (c <= 34) return 0;
    return PLAT * fall(r, 15, 23) * fall(c, 50, 58);
  }
  var PAINT = { ':': ['#A88457', 0.85], ';': ['#8F8A55', 0.6], '~': ['#5C6E4C', 0.9], '.': null, ',': null };
  function paint(c, r, zi, g) {
    var n = { ':': 0, ';': 0, '~': 0 }, any = 0, dc, dr, ch;
    for (dr = -1; dr <= 0; dr++) for (dc = -1; dc <= 0; dc++) {
      ch = g.at(c + dc, r + dr); if (n[ch] !== undefined) { n[ch]++; any++; }
    }
    if (n['~']) return ['#5C6E4C', 0.5 + 0.12 * n['~']];
    if (n[':']) return ['#A88457', 0.35 + 0.15 * n[':']];
    if (n[';']) return ['#8F8A55', 0.25 + 0.1 * n[';']];
    // needle duff under groves and pines, a little rock showing on the plateaus
    for (dr = -2; dr <= 1; dr++) for (dc = -2; dc <= 1; dc++) { ch = g.at(c + dc, r + dr); if (ch === '@' || ch === 'p') return ['#6E6440', 0.35]; }
    var m = Math.sin(c * 0.31 + r * 0.17 + zi * 2.1) + Math.sin(c * 0.13 - r * 0.29 + 2.0);
    return m > 1.1 ? ['#93AA5E', 0.45] : null;
  }

  // ---------------------------------------------------------------- walls
  var SOLID = '#GE';
  function solid(g, c, r) { return SOLID.indexOf(g.at(c, r)) >= 0; }
  function isWild(g) {   // zone 2 (the edge of the wild) has the cliff lips; zone 1 is the stockade
    if (g._frWild === undefined) { g._frWild = false; for (var r = 0; r < g.h && !g._frWild; r++) if (g.rows[r].indexOf('{') >= 0 || g.rows[r].indexOf('}') >= 0) g._frWild = true; }
    return g._frWild;
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  var LIPS = '{}[]';
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var h = hash(c * 7 + 3, r * 5 + 1);
    if (gateDist(g, c, r) < 2.6) return null;          // the gate frame's posts and logs fill the cells beside a gate
    if (!isWild(g)) {
      if (face === 'none' || face === 'corner') return 'Palisade_Corner';
      // the module next to a corner along an east / west wall stops its inner rail short of the corner (the north /
      // south wall's rail runs into the corner there); local +x is north on the west wall, south on the east wall
      var nC = g.at(c, r - 1) === '#' && (r - 1 === 0), sC = g.at(c, r + 1) === '#' && (r + 1 === g.h - 1);
      if ((face === 'E' || face === 'W') && (nC || sC)) return (face === 'E') === nC ? 'Palisade_ER' : 'Palisade_EL';
      return h < 0.12 ? 'Palisade_B' : h < 0.2 ? 'Palisade_C' : h < 0.3 ? 'Palisade_D' : 'Palisade_A';
    }
    if (face === 'none' || face === 'corner') return 'Edge_Corner';
    if (LIPS.indexOf(g.at(c + 1, r)) >= 0 || LIPS.indexOf(g.at(c - 1, r)) >= 0 || LIPS.indexOf(g.at(c, r + 1)) >= 0) return h < 0.5 ? 'Rim_A' : 'Rim_B';
    return h < 0.3 ? 'Edge_A' : h < 0.55 ? 'Edge_B' : h < 0.8 ? 'Edge_C' : 'Edge_D';
  }

  // ---------------------------------------------------------------- symbols
  // palette cells (blender/fr_base.py): plankR 16, plankW 17, plankB 18, plankGr 19, plankG 15
  var CABIN_PAINT = { from: [19], to: [[19], [16], [18], [19], [16]] };
  var HOUSE_PAINT = { from: [17, 18], to: [[17, 18], [15, 16], [16, 17], [18, 17], [19, 17]] };
  function pf(size, pieces, face, extra) { var d = { size: size, pieces: pieces, kind: 'cover' }; if (face !== undefined) d.face = face; return Object.assign(d, extra || {}); }
  var SYMBOLS = {
    // ---- zone 1: the settlement
    'H': pf([10, 10], ['Store'], R90),
    'T': pf([10, 9], ['TradingPost'], -R90),
    'B': pf([12, 8], ['Bunkhouse'], R90),
    'M': pf([8, 7], ['Smithy'], -R90),
    'K': pf([8, 7], ['Cabin'], R90, { paint: CABIN_PAINT }),
    'k': pf([8, 7], ['Cabin'], -R90, { paint: CABIN_PAINT }),
    'U': pf([8, 7], ['House'], R90, { paint: HOUSE_PAINT }),
    'u': pf([8, 7], ['House'], -R90, { paint: HOUSE_PAINT }),
    'O': pf([8, 8], ['Office'], -R90),
    'L': pf([10, 6], ['Stable'], R90),
    'Y': pf([3, 8], ['Tower'], 0),
    'y': pf([3, 8], ['Tower'], Math.PI),
    'W': pf([6, 6], ['Landmark_WaterTower'], 0),
    'w': pf([3, 3], ['Well'], 0),
    'A': pf([12, 1], ['Arch'], 0),
    'f': { pieces: ['FenceHalf'], full: 'FenceFull', links: 'f', post: 'FencePost', kind: 'cover' },
    'r': pf([3, 1], ['HitchRail']),
    't': pf([2, 1], ['Trough']),
    'b': pf([2, 1], ['HayBales'], undefined, { flip: true }),
    'V': pf([3, 6], ['Wagon'], undefined, { flip: true }),
    'v': pf([2, 3], ['Cart'], undefined, { flip: true }),
    'c': { pieces: ['Crate_A', 'Crate_B', 'Crate_A'], rotate: 'random90', kind: 'cover', sink: true },
    '$': { pieces: ['SupplyCrate'], rotate: 'random90', kind: 'cover', sink: true },
    'x': { pieces: ['Barrels'], rotate: 'random90', kind: 'cover', sink: true },
    'd': { pieces: ['Drums'], rotate: 'random90', kind: 'cover', sink: true },
    'e': pf([2, 1], ['Firewood']),
    'q': { pieces: ['ChopBlock'], rotate: 'random90', kind: 'cover', sink: true },
    'l': { pieces: ['LampPost'], rotate: 'edge', edge: ':', kind: 'cover', sink: true },
    'n': { pieces: ['Signpost'], rotate: 'random90', kind: 'cover', sink: true },
    'g': pf([2, 3], ['Generator'], undefined, { flip: true }),
    'z': pf([4, 2], ['Solar'], 0),
    'm': pf([2, 2], ['RadioMast'], 0),
    'F': pf([3, 6], ['FuelTank'], undefined, { flip: true }),
    'N': pf([4, 5], ['SupplyTent'], 0),
    'o': { pieces: ['Spool'], rotate: 'random90', kind: 'cover', sink: true },
    'p': { pieces: ['Pine_A', 'Pine_B', 'Pine_C', 'Pine_B'], rotate: 'random90', kind: 'cover', sink: true },
    'j': { pieces: ['Stump'], rotate: 'random90', kind: 'cover', sink: true },
    // ---- zone 2: the edge of the wild
    '{': { pieces: ['Lip_A', 'Lip_B', 'Lip_C', 'Lip_D'], rotate: R90, kind: 'wall', sink: true, alternate: true },
    '}': { pieces: ['Lip_A', 'Lip_B', 'Lip_C', 'Lip_D'], rotate: 0, kind: 'wall', sink: true, alternate: true },
    '[': { pieces: ['Lip_Low'], rotate: R90, kind: 'wall', sink: true, alternate: true },
    ']': { pieces: ['Lip_Low'], rotate: 0, kind: 'wall', sink: true, alternate: true },
    'R': { pieces: ['Bank_A', 'Bank_B', 'Bank_C'], rotate: R90, kind: 'wall', sink: true, alternate: true },
    'Q': { pieces: ['Bank_A', 'Bank_B', 'Bank_C'], rotate: -R90, kind: 'wall', sink: true, alternate: true },
    '(': { pieces: ['Bank_Low'], rotate: R90, kind: 'wall', sink: true, alternate: true },
    ')': { pieces: ['Bank_Low'], rotate: -R90, kind: 'wall', sink: true, alternate: true },
    '=': pf([7, 2], ['Bridge'], 0),
    'X': pf([8, 8], ['Landmark_Lookout'], 0),
    'I': pf([10, 8], ['Mill'], 0),
    'J': pf([3, 6], ['WheelFrame'], 0),
    '|': pf([1, 4], ['Flume'], 0),
    '~': { pieces: ['Water_A', 'Water_B', 'Water_C', 'Water_A'], rotate: 'random90', collide: false, sink: true },
    'Z': pf([4, 2], ['Falls'], 0),
    'D': pf([6, 3], ['LogDeck'], undefined, { flip: true }),
    '7': pf([4, 2], ['LogPile'], undefined, { flip: true }),
    '8': pf([3, 2], ['Lumber'], undefined, { flip: true }),
    '9': pf([5, 1], ['Log'], undefined, { flip: true }),
    '0': pf([8, 2], ['FallenTree'], undefined, { flip: true }),
    '1': pf([2, 2], ['Boulder_A', 'Boulder_B'], undefined, { flip: true }),
    '`': { pieces: ['Rock'], rotate: 'random90', kind: 'cover', sink: true },
    '@': pf([3, 3], ['Grove_A', 'Grove_B'], undefined, { flip: true }),
    "'": { pieces: ['Fern'], rotate: 'random90', collide: false, sink: true },
    'C': pf([6, 5], ['CookShack'], 0),
    '3': pf([4, 5], ['Tent'], 0),
    '5': pf([3, 3], ['FirePit'], 0),
    '6': pf([2, 1], ['Sawhorse'], undefined, { flip: true }),
    '&': pf([3, 5], ['LogArch'], undefined, { flip: true }),
    '%': pf([2, 1], ['ToolRack'], undefined, { flip: true }),
    '!': { pieces: ['CampSign'], rotate: 'edge', edge: ':', kind: 'cover', sink: true },
    '*': pf([8, 5], ['Mine'], R90),
    '+': pf([2, 2], ['Relay'], 0),
    '^': pf([4, 3], ['LeanTo'], 0)
  };
  var GLOW = { LampPost: { piece: 'LampPost_Glow' }, RadioMast: { piece: 'RadioMast_Glow', groups: 2 }, FirePit: { piece: 'FirePit_Glow' } };
  var FLAT = 'HTBMKkUuOLYyWwCIJZ*35';

  // ---------------------------------------------------------------- the land round the level (backdrop.build)
  /* Level-wide (nothing here belongs to a zone, so nothing switches when the player crosses between the zones):
     the forest floor of the ridge, the cliff on the west side down into the valley, the valley floor far below,
     instanced conifers on both (chunked by sector so the camera culls the ones behind it; outlined near the walls,
     outline-free further out), and the mountains: three ranges round the horizon that follow the camera like the sky
     dome (snow caps, aerial haze, ink ridge lines; never fogged out). The water wheel's rotor turns. */
  var VALLEY = -46;
  function buildLand(level, api) {
    var T = typeof THREE !== 'undefined' ? THREE : null;
    var hash = api.hash, zones = level.zones;
    var x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    zones.forEach(function (z) { x0 = Math.min(x0, z.ox); x1 = Math.max(x1, z.ox + z.w); z0 = Math.min(z0, z.oz); z1 = Math.max(z1, z.oz + z.h); });
    var hz = level.hatch ? level.hatch.z : z0 - 26;
    var zN = Math.min(z0, hz - 6);
    var cx = (x0 + x1) / 2, cz = (zN + z1) / 2;
    function cliffX(z) { return x0 - 7 - 2.5 * Math.sin(z * 0.045) - 1.5 * Math.sin(z * 0.13 + 1.0) - (z < zN - 30 ? (zN - 30 - z) * 0.35 : 0) - (z > z1 + 30 ? (z - z1 - 30) * 0.35 : 0); }
    // ---- ground: the ridge top east of the cliff edge, the valley floor, the cliff face between them
    var G = api.geo, FAR = 700, STEP = 6;
    var ridge = '#56783F', valley = '#4F7444';
    for (var zz = zN - FAR; zz < z1 + FAR; zz += STEP) {
      var a0 = cliffX(zz), a1 = cliffX(zz + STEP);
      G.flat([[a0, zz], [x1 + FAR, zz], [x1 + FAR, zz + STEP], [a1, zz + STEP]], -0.03, ridge);
      G.flat([[cx - FAR - 300, zz], [a0 - 9, zz], [a1 - 9, zz + STEP], [cx - FAR - 300, zz + STEP]], VALLEY, valley);
    }
    if (T) {
      var C = [new T.Color('#8C857A'), new T.Color('#756F66'), new T.Color('#9C9284'), new T.Color('#5E5A55')], ink = new T.Color('#15121C');
      var BANDS = [0, -2.5, -12, -23, -34, VALLEY];
      for (zz = zN - FAR; zz < z1 + FAR; zz += STEP / 2) {
        var p0 = cliffX(zz), p1 = cliffX(zz + STEP / 2);
        for (var bi = 0; bi < BANDS.length - 1; bi++) {
          var ya = BANDS[bi], yb = BANDS[bi + 1], f0 = -ya * 0.17, f1 = -yb * 0.17;   // the face leans out as it drops
          var j0 = (hash(Math.round(zz * 2), bi) - 0.5) * 2.2, j1 = (hash(Math.round(zz * 2) + 1, bi) - 0.5) * 2.2;
          var col = bi === 0 ? ink : C[(bi + (hash(Math.round(zz), 9) < 0.3 ? 1 : 0)) % C.length];
          var a = G._vert(p0 - f0 + (bi ? j0 * 0.3 : 0), ya, zz, -1, 0.2, 0, col), b = G._vert(p1 - f0 + (bi ? j1 * 0.3 : 0), ya, zz + STEP / 2, -1, 0.2, 0, col);
          var c = G._vert(p1 - f1 + j1, yb, zz + STEP / 2, -1, 0.2, 0, col), d = G._vert(p0 - f1 + j0, yb, zz, -1, 0.2, 0, col);
          G.idx.push(a, d, c, a, c, b);
        }
      }
    }
    // keep-outs: the zones and their walls, the trails, the hatch room
    var keep = [];
    zones.forEach(function (z) { keep.push([z.ox - 1.5, z.oz - 1.5, z.ox + z.w + 1.5, z.oz + z.h + 1.5]); });
    level.trails.forEach(function (t) { keep.push([t.x - 4.2, Math.min(t.z0, t.z1) - 1, t.x + 4.2, Math.max(t.z0, t.z1) + 1]); });
    if (level.hatch) keep.push([level.hatch.x - 6, level.hatch.z - 6, level.hatch.x + 6, (level.hatch.z0 || level.hatch.z) + 1]);
    function clear(x, z, r) {
      for (var i = 0; i < keep.length; i++) { var k = keep[i]; if (x > k[0] - r && x < k[2] + r && z > k[1] - r && z < k[3] + r) return false; }
      return true;
    }
    function outDist(x, z) { var d = 1e9; keep.forEach(function (k) { d = Math.min(d, Math.max(k[0] - x, x - k[2], k[1] - z, z - k[3], 0)); }); return d; }
    // ---- trees: [x, y, z, yaw, scale] per kind, then one InstancedMesh per kind and 30-degree sector
    var lists = { Backdrop_Pine: [], Backdrop_Fir: [], Backdrop_PineLow: [] }, n = 0;
    function plant(x, y, z, near) {
      n++;
      var s = 0.8 + hash(n, 13) * 0.55, yaw = hash(n, 11) * 6.28;
      var kind = near ? (hash(n, 9) < 0.7 ? 'Backdrop_Pine' : 'Backdrop_Fir') : 'Backdrop_PineLow';
      lists[kind].push([x, y, z, yaw, near ? s : s * 1.35]);
    }
    var gx, gz;
    for (gx = x0 - 60; gx <= x1 + 230; gx += 4.6) for (gz = zN - 230; gz <= z1 + 230; gz += 4.6) {
      n++;
      var x = gx + (hash(n, 3) - 0.5) * 3.6, z = gz + (hash(n, 5) - 0.5) * 3.6;
      if (x < cliffX(z) + 2.5) continue;
      if (!clear(x, z, 1.4)) continue;
      var od = outDist(x, z);
      if (od < 18) { if (hash(n, 17) < 0.8) plant(x, -0.05, z, true); }
      else if (od < 50) { if (hash(n, 17) < 0.36) plant(x, -0.1, z, false); }
      else if (hash(n, 17) < 0.13 + 0.03 * Math.min(4, (od - 50) / 40)) plant(x, -0.1, z, false);
    }
    // the valley floor: open stands and dense forest down to the river flats, far below the cliff
    for (gx = x0 - 300; gx < x0 - 12; gx += 10) for (gz = zN - 230; gz <= z1 + 230; gz += 10) {
      n++;
      var vx = gx + (hash(n, 3) - 0.5) * 7, vz = gz + (hash(n, 5) - 0.5) * 7;
      if (vx > cliffX(vz) - 12) continue;
      var river = Math.abs(vx - (x0 - 150 + 25 * Math.sin(vz * 0.012))) < 9;
      if (!river && hash(n, 19) < 0.5) plant(vx, VALLEY - 0.1, vz, false);
    }
    if (T && IB.Assets && IB.Assets.geo) {
      var TH = IB.THEME_DEFS.frontier, _m = new T.Matrix4(), _q = new T.Quaternion(), _p = new T.Vector3(), _s = new T.Vector3(), UP = new T.Vector3(0, 1, 0);
      Object.keys(lists).forEach(function (kind) {
        var full = IB.themePiece(TH, kind), geo = IB.Assets.get(full);
        if (!geo) return;
        var bySec = {};
        lists[kind].forEach(function (t) { var a = Math.floor((Math.atan2(t[2] - cz, t[0] - cx) + Math.PI) / (Math.PI / 6)); (bySec[a] || (bySec[a] = [])).push(t); });
        Object.keys(bySec).forEach(function (k) {
          var L = bySec[k], g = new T.BufferGeometry();
          g.setIndex(geo.index); Object.keys(geo.attributes).forEach(function (an) { g.setAttribute(an, geo.attributes[an]); });
          var im = new T.InstancedMesh(g, IB.Assets.material(full), L.length), bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9, by0 = 1e9;
          L.forEach(function (t, i) {
            _q.setFromAxisAngle(UP, t[3]); _p.set(t[0], t[1], t[2]); _s.set(t[4], t[4], t[4]);
            im.setMatrixAt(i, _m.compose(_p, _q, _s));
            bx0 = Math.min(bx0, t[0]); bx1 = Math.max(bx1, t[0]); bz0 = Math.min(bz0, t[2]); bz1 = Math.max(bz1, t[2]); by0 = Math.min(by0, t[1]);
          });
          // the instances' own bounds, so the camera culls a whole sector behind it
          var c3 = new T.Vector3((bx0 + bx1) / 2, by0 + 8, (bz0 + bz1) / 2);
          g.boundingSphere = new T.Sphere(c3, Math.hypot(bx1 - bx0, bz1 - bz0) / 2 + 18);
          im.name = 'Forest_' + kind + '_' + k;
          level.root.add(im);
        });
      });
    }
    if (!T) return;
    // ---- the mountains: three ranges on a ring that follows the camera (like the sky dome)
    var ring = new T.Group(); ring.name = 'Mountains';
    var pos = [], colr = [], idx = [];
    function vtx(x, y, z, c) { pos.push(x, y, z); colr.push(c.r, c.g, c.b); return pos.length / 3 - 1; }
    var fogC = new T.Color('#CFE3EE');
    var RANGES = [
      { R: 470, base: -160, h: [70, 170], snow: 0.55, rock: '#A7B7CE', rock2: '#97A9C3', snowC: '#EEF3FA', seed: 1, n: 150 },
      { R: 430, base: -160, h: [45, 120], snow: 0.62, rock: '#7F96B3', rock2: '#6F86A4', snowC: '#F7FAFD', seed: 2, n: 170 },
      { R: 395, base: -160, h: [14, 38], snow: 2, rock: '#4C6B67', rock2: '#41605C', snowC: '#FFFFFF', seed: 3, n: 260, trees: true }
    ];
    RANGES.forEach(function (RG) {
      var N = RG.n, ridgeP = [], rockC = new T.Color(RG.rock), rockC2 = new T.Color(RG.rock2), snowC = new T.Color(RG.snowC);
      var inkC = new T.Color('#3A4256').lerp(rockC, RG.trees ? 0.2 : 0.35), haze = rockC.clone().lerp(fogC, RG.trees ? 0.45 : 0.6);
      for (var i = 0; i <= N; i++) {
        var a = i / N * Math.PI * 2, u = i / N * 6.2832 * 3 + RG.seed;
        var hh = 0.5 + 0.28 * Math.sin(u * 1.0) + 0.2 * Math.sin(u * 2.3 + 1.7) + 0.12 * Math.sin(u * 5.1 + 0.4) + 0.08 * Math.sin(u * 11.0 + RG.seed);
        hh = Math.max(0, Math.min(1, hh));
        var h = RG.h[0] + (RG.h[1] - RG.h[0]) * hh * hh * (RG.trees ? 1 : 1.25);
        if (RG.trees) h += (i % 2 ? 4.5 : 0) * (0.6 + 0.4 * hash(i, 41));   // tree tips along the forested foothills
        else h += (hash(i, 43 + RG.seed) - 0.5) * 9;
        ridgeP.push([Math.cos(a) * RG.R, Math.sin(a) * RG.R, h]);
      }
      for (i = 0; i < N; i++) {
        var A = ridgeP[i], B = ridgeP[i + 1], cA = (i % 7 < 3) ? rockC : rockC2;
        var lowA = -4, lowB = -4;
        // the foot sinks into the haze (the fogged ground out there is the fog colour), the face above it, the
        // snow caps, the ink ridge line on top
        var v0 = vtx(A[0], RG.base, A[1], fogC), v1 = vtx(B[0], RG.base, B[1], fogC), v2 = vtx(B[0], lowB, B[1], haze), v3 = vtx(A[0], lowA, A[1], haze);
        idx.push(v0, v1, v2, v0, v2, v3);
        var top = RG.h[0] + (RG.h[1] - RG.h[0]) * RG.snow;
        var sA = Math.min(A[2] - 0.1, A[2] > top ? top + (hash(i, 51) - 0.5) * 6 : A[2]), sB = Math.min(B[2] - 0.1, B[2] > top ? top + (hash(i + 1, 51) - 0.5) * 6 : B[2]);
        var w0 = vtx(A[0], lowA, A[1], haze), w1 = vtx(B[0], lowB, B[1], haze), w2 = vtx(B[0], sB, B[1], cA), w3 = vtx(A[0], sA, A[1], cA);
        idx.push(w0, w1, w2, w0, w2, w3);
        if (A[2] > top || B[2] > top) {
          var s0 = vtx(A[0], sA, A[1], snowC), s1 = vtx(B[0], sB, B[1], snowC), s2 = vtx(B[0], B[2], B[1], snowC), s3 = vtx(A[0], A[2], A[1], snowC);
          idx.push(s0, s1, s2, s0, s2, s3);
        }
        var k0 = vtx(A[0] * 0.999, A[2] - 0.15, A[1] * 0.999, inkC), k1 = vtx(B[0] * 0.999, B[2] - 0.15, B[1] * 0.999, inkC);
        var k2 = vtx(B[0] * 0.999, B[2] + 1.3, B[1] * 0.999, inkC), k3 = vtx(A[0] * 0.999, A[2] + 1.3, A[1] * 0.999, inkC);
        idx.push(k0, k1, k2, k0, k2, k3);
      }
    });
    var mg = new T.BufferGeometry();
    mg.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
    mg.setAttribute('color', new T.Float32BufferAttribute(colr, 3));
    mg.setIndex(idx);
    var mm = new T.Mesh(mg, new T.MeshBasicMaterial({ vertexColors: true, fog: false, side: T.DoubleSide }));
    mm.frustumCulled = false; mm.renderOrder = -8;
    ring.add(mm);
    level.root.add(ring);
    // ---- the water wheel's rotor (one per wheel frame, in its zone's group) turns with the flow
    var rotors = [], full = IB.themePiece(IB.THEME_DEFS.frontier, 'Wheel_Rotor');
    if (IB.Assets && IB.Assets.geo && IB.Assets.geo[full]) zones.forEach(function (zn) {
      var g = zn.grid, seen = {};
      for (var r = 0; r < g.h; r++) for (var c = 0; c < g.w; c++) {
        if (g.rows[r][c] !== 'J' || seen[c + ',' + r]) continue;
        var w = 0, d = 0; while (g.rows[r][c + w] === 'J') w++; while (r + d < g.h && g.rows[r + d][c] === 'J') d++;
        for (var rr = r; rr < r + d; rr++) for (var c2 = c; c2 < c + w; c2++) seen[c2 + ',' + rr] = 1;
        var wx = zn.ox + c + w / 2, wz = zn.oz + r + d / 2, wy = level.world ? level.world.groundAt(wx, wz) : 0;
        var mesh = new T.Mesh(IB.Assets.get(full), IB.Assets.material(full));
        mesh.position.set(wx, wy + 2.95, wz); zn.group.add(mesh); rotors.push(mesh);
      }
    });
    api.tick(function (dt, t) {
      var cam = IB.Render && IB.Render.camera;
      if (cam) { ring.position.x = cam.position.x; ring.position.z = cam.position.z; }
      for (var i = 0; i < rotors.length; i++) rotors[i].rotation.x = -t * 0.55;
    });
  }

  var PIECES = ['Palisade_A', 'Palisade_B', 'Palisade_C', 'Palisade_D', 'Palisade_EL', 'Palisade_ER', 'Palisade_Corner', 'Edge_A', 'Edge_B', 'Edge_C', 'Edge_D',
    'Edge_Corner', 'Rim_A', 'Rim_B', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'Hatch',
    'LampPost_Glow', 'RadioMast_Glow', 'FirePit_Glow', 'Wheel_Rotor', 'Backdrop_Pine', 'Backdrop_Fir', 'Backdrop_PineLow'];
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'frontier', name: 'Cinder Ridge Outpost', family: 'kit-frontier', prefix: 'KIT_FRONTIER_',
    palette: ['#2F6B46', '#B27B4A', '#A9473A', '#5FA8E8'],
    // clear late morning: a deep blue sky paling to the horizon, light haze, the sun high in the south-east
    env: { sky: ['#4E9BE6', '#D6ECF8'], fog: { color: '#CFE3EE', near: 90, far: 340, tierScale: true }, sun: [0.4, 0.88, 0.42], clouds: true, ceiling: null, far: 520 },
    floor: { color: '#7FA453', trail: '#9C7B50', outside: '#56783F' },
    terrain: { height: terrainHeight, paint: paint, flat: FLAT, ramp: [0, 1], low: '#7FA453', high: '#90A85E', patch: '#749C4C', top: 3.2 },
    wall: { height: 4.0, roof: '#56783F', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.4, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall_D'], height: 2.6 },
    hatch: 'Hatch', stand: 'Crate_A',
    backdrop: { build: buildLand },
    budget: { prop: 4800, landmark: 2600, total: 50000 },
    terrainHeight: terrainHeight,
    allPieces: function () { return PIECES.slice(); },
    levels: {
      frontier: {
        name: 'Cinder Ridge Outpost',
        intro: 'The robots hold Cinder Ridge, the last outpost before the wild. Take the stockade street by street, then follow the logging road past the sawmill and up to the lookout.',
        zones: [
          // the settlement: the main street, the square, the yards; the first wave is light robots only
          { map: 'frontier_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 5]],
            [['crawler', 14], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['drone', 8], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 3]],
            [['crawler', 14], ['gunner', 9], ['drone', 5], ['soldier', 6], ['blader', 3]]] },
          // the edge of the wild: the mill yard, the camp, the ravine, the plateaus
          { map: 'frontier_2', waves: [
            [['crawler', 16], ['gunner', 10], ['drone', 5], ['soldier', 6]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 4], ['blader', 4]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 4], ['blader', 3]],
            [['crawler', 16], ['gunner', 9], ['bomber', 2], ['soldier', 4], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
