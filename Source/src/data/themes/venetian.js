/* Theme: Ca' Doranza (kit-venetian) -- a made-up Venetian mansion compound on a canal: the campo before it and the
   mansion's inner courtyard, late afternoon light warming the stucco. Two zones; player travel is north.
   1 The Campo dei Venti (76 x 70): a paved campo (grey trachyte, white Istrian stone bands, cobbled fondamenta and
     lanes) ringed by stucco houses of two and three storeys in ochre, terracotta, rose and cream (white stone
     courses, green louvred shutters, Gothic French windows on flower-covered balconies, geraniums trailing from the
     window boxes, shop windows and arched doors, bracket lanterns, terracotta roofs and funnel chimneys). The
     player comes in through the portal of the lane in the south-west; the fondamenta runs along the canal on the
     north side behind its stone balustrade (benches, goods off the boats, a hand cart, the flower stall) to the exit
     portal at the foot of the mansion's private bridge. The Fountain of the Four Winds (landmark: an octagonal
     basin, four great stone scrolls pouring jets, the tazza and its falling sheet, the gilt armillary sphere); Caffe
     Zanetto against the west houses (walk-in: the bar, bottle shelves, tables, a stair up to the roof terrace at
     3.6 m) with its terrace of parasol tables and planters; Pasticceria Brolo against the east houses (walk-in: the
     pastry counter, the coffee bar) with its terrace; the Loggia dei Mercanti in the south-east (an open arcade,
     produce on its bench, its stair up to the roof terrace at 3.6 m); market stalls, the mask and postcard kiosk,
     two well-heads, lamp posts, benches, lemon trees and urns.
   2 The courtyard of Ca' Doranza (66 x 72): the mansion's wings on three sides (rose stucco, three tall storeys,
     Gothic balconies; the canal wing on the south with the water gate and, toward the canal, its own Gothic facade,
     the east wing, the main house on the north with its portal), a brick garden wall on the west. The cloister in
     the middle: two rings of Istrian columns every 3 m with round arches between them round the garden, the upper
     walk on top (a deck at 4.32 m with balustrades both sides) and the roof loggia (columns, a tiled hip roof) over
     the north range; the grand staircase (landmark: two marble flights with a landing, a red runner, balustraded
     side walls, gilt lanterns and urns) up from the forecourt to the south range, and two brick service stairs up
     to the west and east ranges. In the garden the second fountain (a marble basin, a fluted column, a bowl, four
     jets), four parterres of roses, cypresses and lemon trees on gravel; the forecourt behind the water gate with
     two well-heads; the north court (parterres, stone tables, hedges, cypresses); the west garden (hedges,
     cypresses); the east service yard (the boat under repair on its trestles, crates, barrels, the cart).
   The trail between the zones is the mansion's private bridge over the canal (balustrades over the water), the
   exit path a lane between house walls. Built by blender/fam_kit_venetian.py (ven_*.py); zone layouts by
   tools/venetian_zones.py (src/data/zones/venetian_*.txt).

   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled; R90 / -R90 = front east / west):
     # wall: zone 1 the house fronts (buildings 3-8 m wide, four colours (wall.paint), two heights; windows, piers,
       lanterns, chimneys, doors, shop windows, balcony groups, quoins where houses meet), the quay balustrade over
       the canal (north); zone 2 the mansion's fronts (north, east), the canal wing (south: its canal face behind),
       the garden wall (west); the portal facades over the gates are placed by backdrop.build
     Zone 1: F the Fountain of the Four Winds [14,14] (landmark)   K Caffe Zanetto [10,8] R90 (walk-in, roof terrace)
             k Pasticceria Brolo [8,7] -R90 (walk-in)   L the Loggia dei Mercanti [16,6] (roof terrace, stair east)
             t cafe table (two chairs)   u parasol table [2,2] (four chairs, repainted per copy)   p planter [2,1]
             n menu board   Y kiosk [3,3]   X flower stall [3,2]   M market stall [3,2] (two paint jobs)
             v hand cart [2,3]   c crates   x barrels
     Zone 2: O cloister column   Z the grand staircase [8,8] (landmark, rises north)   i j service stair [2,6] R90 /
             -R90 (rises west / east)   Q the garden fountain [6,6]   R parterre [6,4]   H box hedge (links)
             y cypress in a pot   T stone table with benches [3,2]   g the boat under repair [3,11]
     Both: w well-head [2,2]   l lamp post (glow)   q lemon tree in a pot   U urn on a pedestal   B stone bench [2,1]
   Layer symbols: zone 1 "@layer 0": , cobbles   - | white stone band along X / Z   + band crossing (no collision);
     "@layer 3.6": r balustrade (links) on the roof terraces of the cafe and the loggia.
     Zone 2 "@layer 0": A V cloister arch [2,1] along X / Z (between columns 3 m apart; no collision)   : gravel;
     "@layer 4.32": = the upper walk's deck, r its balustrades (links), W the roof loggia [13,4].
   Backdrop (backdrop.build, level-wide, so nothing switches between the zones): the canal between the zones and on
   east and west to the haze, its quay walls, the bridge under the trail, the palazzi along both banks, moored
   boats and striped mooring poles, the roofs of the city round both zones with chimneys, a campanile and a domed
   church, the garden trees beyond the garden wall, the portal facades over the gates. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var WATER = -1.25, H3 = 10.4, H2 = 7.6, HP = 12.2;

  // ---------------------------------------------------------------- walls
  function kindOf(g) {   // zone 1 (the campo) holds the fountain; zone 2 the grand staircase
    if (g._vK === undefined) { g._vK = 'court'; for (var r = 0; r < g.h; r++) if (g.rows[r].indexOf('F') >= 0) { g._vK = 'campo'; break; } }
    return g._vK;
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  // module-local +X in grid steps for a module facing S / N / E / W (the engine's yaw 0, pi, pi/2, -pi/2)
  var LDIR = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };
  var FACE = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var BUILT = 'KkL';   // prefabs that stand against the houses (nothing may stand out of the front behind them)
  var WIDTHS = [6, 4, 7, 5, 8, 4, 6, 5, 7, 3];
  function sideOf(g, c, r) {   // the wall line a ring cell belongs to and its facing
    var W = g.w - 1, H = g.h - 1;
    if (r === 0) return 'S'; if (r === H) return 'N'; if (c === 0) return 'E'; if (c === W) return 'W';
    return null;
  }
  /* The houses along one wall line of the campo (cached per grid): positions along the line in module-local +X order,
     split at the gates and the corners into buildings WIDTHS wide, each with a style (paint) and a height; the
     buildings beside a gate are three storeys (the portal's facade is). Returns pos -> { i, w, s, tall, prev, next }. */
  function houses(g, face) {
    var cache = g._vH || (g._vH = {});
    if (cache[face]) return cache[face];
    var W = g.w - 1, H = g.h - 1, cells = [];
    if (face === 'S' || face === 'N') { var rr = face === 'S' ? 0 : H; for (var c = 1; c < W; c++) cells.push([c, rr]); }
    else { var cc = face === 'E' ? 0 : W; for (var r = 1; r < H; r++) cells.push([cc, r]); }
    var L = LDIR[face];
    if (L[0] < 0 || L[1] < 0) cells.reverse();
    var runs = [], cur = [];
    cells.forEach(function (p) {
      if (g.at(p[0], p[1]) !== '#' || gateDist(g, p[0], p[1]) < 2.6) { if (cur.length) runs.push(cur); cur = []; return; }
      cur.push(p);
    });
    if (cur.length) runs.push(cur);
    var map = {}, line = face.charCodeAt(0);
    runs.forEach(function (run, ri) {
      var B = [], x = 0, wi = Math.floor(hh(ri + 3, line) * WIDTHS.length);
      while (x < run.length) {
        var w = WIDTHS[wi++ % WIDTHS.length];
        if (run.length - (x + w) < 3) w = run.length - x;
        B.push({ a: x, b: x + w - 1 }); x += w;
      }
      B.forEach(function (b, bi) {
        var s = Math.floor(hh(bi * 5 + ri * 31 + 1, line) * 4);
        if (bi > 0 && s === B[bi - 1].s) s = (s + 1) % 4;
        b.s = s; b.tall = hh(bi * 7 + ri * 13 + 2, line + 5) < 0.62;
      });
      // beside a gate (the run's end next to it) the house is tall
      [0, B.length - 1].forEach(function (k) { var p = run[k === 0 ? 0 : run.length - 1]; if (gateNear(g, p[0], p[1])) B[k].tall = true; });
      B.forEach(function (b, bi) {
        for (var q = b.a; q <= b.b; q++) map[run[q][0] + ',' + run[q][1]] = { i: q - b.a, w: b.b - b.a + 1, s: b.s, tall: b.tall, prev: B[bi - 1] || null, next: B[bi + 1] || null, first: q === 0, last: q === run.length - 1 };
      });
    });
    cache[face] = map;
    return map;
  }
  function gateNear(g, c, r) { return gateDist(g, c, r) < 4; }
  function behindBuilt(g, c, r, face) { var f = FACE[face]; return BUILT.indexOf(g.at(c + f[0], r + f[1])) >= 0; }
  function cornerNext(g, c, r) {   // an inner corner: the cell along the line next to this one is a zone corner
    var W = g.w - 1, H = g.h - 1;
    return (c === 0 || c === W) ? (r === 1 ? 'N' : r === H - 1 ? 'S' : null) : null;
  }
  function campoModule(g, c, r, face, hash) {
    var map = houses(g, face), b = map[c + ',' + r];
    if (!b) return null;
    var T = b.tall ? 'H3_' : 'H2_', i = b.i, w = b.w;
    // the ends of a line (beside a zone corner or a gate) and the taller side of a boundary between two houses
    if (b.first || b.last) {
      var cn = cornerNext(g, c, r);
      if (cn && (c === 0 || c === g.w - 1) && !(face === 'E' && r === 1) && !(face === 'W' && r === 1)) {
        // an inner corner of the ring (the E / W fronts take the cut courses): which local end touches the corner
        var L = LDIR[face], toward = (cn === 'S') ? [0, 1] : [0, -1];
        return T + ((L[0] === toward[0] && L[1] === toward[1]) ? 'InR' : 'InL');
      }
      return T + 'Quoin';
    }
    if (i === 0 && b.prev && (b.tall || !b.prev.tall)) return T + 'Quoin';
    if (i === w - 1 && b.next && b.tall && !b.next.tall) return T + 'Quoin';
    var built = behindBuilt(g, c, r, face);
    var mid = Math.floor(w / 2);
    if (!built && w >= 6 && i >= mid - 1 && i <= mid + 1) return T + (i === mid - 1 ? 'BalL' : i === mid ? 'BalM' : 'BalR');
    var h = hh(c * 3 + 1, r * 7 + 2), door = 1 + Math.floor(hh(c + r, w) * Math.max(1, w - 2));
    if (built) return T + ((i % 2) ? 'Pier' : 'Plain');
    if (i === door && w >= 4) return T + (h < 0.45 ? 'Door' : 'Shop');
    if (i % 2 === 0) {
      if (b.tall && h < 0.14) return 'H3_PierC';
      return T + (h > 0.62 ? 'PierL' : 'Pier');
    }
    if (!b.tall) return 'H2_Win';
    return 'H3_' + (h < 0.3 ? 'WinF' : h < 0.55 ? 'WinC' : 'Win');
  }
  function quayModule(c) { var k = c % 8; return k === 4 ? 'Quay_P' : k === 1 ? 'Quay_R' : 'Quay_A'; }
  function palazzo(g, c, r, face, canal) {
    // the mansion: bays of pier / window, a balcony group every 12 m, doors on the courtyard, lanterns
    var L = LDIR[face], pos = (face === 'S' || face === 'N') ? c : r, P = canal ? 'C_' : 'HP_';
    if (L[0] < 0 || L[1] < 0) pos = (face === 'S' || face === 'N' ? g.w : g.h) - 1 - pos;
    var k = pos % 16;
    if (k >= 7 && k <= 9) return P + (k === 7 ? 'BalL' : k === 8 ? 'BalM' : 'BalR');
    if (k === 0) return P + 'Quoin';
    if (k % 2 === 1) return P + (canal ? (k === 3 || k === 13 ? 'WinC' : 'Win') : (k === 13 && pos % 32 === 13 ? 'Door' : 'Win'));
    return P + (k === 2 || k === 14 ? 'PierL' : 'Pier');
  }
  function gardenWall(r) { var k = r % 9; return k === 2 ? 'GW_V' : k === 5 ? 'GW_N' : k === 7 ? 'GW_L' : r === 34 ? 'GW_D' : 'GW_A'; }
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var K = kindOf(g), W = g.w - 1, H = g.h - 1;
    if (gateDist(g, c, r) < 2.6) return null;   // the portal's piers fill the cells beside a gate
    var cornerCell = (c === 0 || c === W) && (r === 0 || r === H);
    if (K === 'campo') {
      if (cornerCell) return houseAt(g, c, r === 0 ? 1 : H - 1, c === 0 ? 'E' : 'W').tall ? 'H3_Corner' : 'H2_Corner';
      if (r === 0) return quayModule(c);
      var f = sideOf(g, c, r);
      return campoModule(g, c, r, f, hash);
    }
    if (cornerCell) return 'HP_Corner';
    if (c === 0) return gardenWall(r);
    var f2 = sideOf(g, c, r);
    if (c === W && (r === 1 || r === H - 1)) return 'HP_In' + (r === H - 1 ? 'R' : 'L');   // facing west, local +X is south
    if (c === W) return palazzo(g, c, r, f2, false);
    if (r === 0 && (c === 1 || c === W - 1)) return 'HP_Quoin';
    if (r === H && (c === 1 || c === W - 1)) return 'C_Quoin';
    return palazzo(g, c, r, f2, r === H);
  }
  function houseAt(g, c, r, face) { return houses(g, face)[c + ',' + r] || { tall: true }; }
  // wall.paint: the campo's houses in four colours (stucco cells 8-10: ochre as modelled, terracotta 11-13, rose
  // 14-16, cream 17-19); the mansion all rose
  var STYLE = [null, [11, 12, 13], [14, 15, 16], [17, 18, 19]];
  function paintWall(c, r, g, face) {
    var to;
    if (kindOf(g) === 'court') to = STYLE[2];
    else {
      var W = g.w - 1, H = g.h - 1;
      if (r === 0 && c > 0 && c < W) return null;
      var f = sideOf(g, c, r), rr = r, ff = f;
      if ((c === 0 || c === W) && (r === 0 || r === H)) { rr = r === 0 ? 1 : H - 1; ff = c === 0 ? 'E' : 'W'; }
      var b = houses(g, ff)[c + ',' + rr];
      to = b ? STYLE[b.s] : null;
    }
    return to ? [[8, to[0]], [9, to[1]], [10, to[2]]] : null;
  }

  // ---------------------------------------------------------------- symbols
  function pf(size, pieces, face, extra) { var d = { size: size, pieces: pieces, kind: 'cover' }; if (face !== undefined) d.face = face; return Object.assign(d, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, kind: 'cover', rotate: rot === undefined ? 'random90' : rot }, extra || {}); }
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }
  // paint jobs (palette cells, blender/ven_base.py): awnR 51, awnG 52, shut 28, fOrange 44, lemon 62, fRed 41, leafL 47,
  // fPurp 43, leaf 45
  var PARASOL = { from: [51], to: [[51], [52], [28], [51], [52], [44]] };
  var STALL = { from: [51, 62, 44, 41, 47], to: [[51, 62, 44, 41, 47], [52, 43, 45, 62, 41], [28, 41, 62, 47, 44]] };
  var SYMBOLS = {
    // ---- zone 1
    'F': pf([14, 14], ['Landmark_Fountain'], 0, { kind: 'wall' }),
    'K': pf([10, 8], ['Cafe_A'], R90),
    'k': pf([8, 7], ['Cafe_B'], -R90),
    'L': pf([16, 6], ['Loggia'], 0),
    't': one(['CafeTable']),
    'u': pf([2, 2], ['ParasolSet'], undefined, { flip: true, paint: PARASOL }),
    'p': pf([2, 1], ['Planter'], undefined, { flip: true }),
    'n': one(['Menu'], 'edge'),
    'Y': pf([3, 3], ['Kiosk'], 0),
    'X': pf([3, 2], ['FlowerStall'], 0),
    'M': pf([3, 2], ['Stall'], undefined, { flip: true, paint: STALL }),
    'v': pf([2, 3], ['HandCart'], undefined, { flip: true }),
    'c': one(['Crates']),
    'x': one(['Barrels']),
    // ---- zone 2
    'O': one(['Column'], 0),
    'Z': pf([8, 8], ['Landmark_Stair'], 0),
    'i': pf([2, 6], ['Stair'], R90),
    'j': pf([2, 6], ['Stair'], -R90),
    'Q': pf([6, 6], ['Fountain2'], 0),
    'R': pf([6, 4], ['Parterre'], undefined, { flip: true }),
    'H': { pieces: ['HedgeHalf'], full: 'HedgeFull', links: 'H', post: 'HedgePost', kind: 'cover' },
    'y': one(['Cypress']),
    'T': pf([3, 2], ['StoneTable'], undefined, { flip: true }),
    'g': pf([3, 11], ['Gondola'], undefined, { flip: true }),
    // ---- both
    'w': pf([2, 2], ['Well'], 0),
    'l': one(['LampPost'], 0),
    'q': one(['LemonPot']),
    'U': one(['Urn']),
    'B': pf([2, 1], ['Bench'], undefined, { flip: true }),
    // ---- layers
    ',': flat(['Cobble_A', 'Cobble_B'], 0, true),
    '-': flat(['Band'], 0), '|': flat(['Band'], R90), '+': flat(['BandX'], 0),
    ':': flat(['Gravel'], 0),
    'r': { pieces: ['BalHalf'], full: 'BalFull', links: 'r', post: 'BalPost', kind: 'cover' },
    'A': { size: [2, 1], pieces: ['Arch'], face: 0, collide: false },
    'V': { size: [2, 1], pieces: ['Arch'], face: R90, collide: false },
    '=': { deck: { thick: 0.3, color: '#E8E1D2', edge: '#EFE9DC', under: '#F1E3C6' } },
    'W': pf([13, 4], ['Pavilion'], 0)
  };
  var GLOW = { LampPost: { piece: 'LampPost_Glow' }, Landmark_Stair: { piece: 'Landmark_Stair_Glow' } };

  // ---------------------------------------------------------------- the canal, the city round the zones (backdrop.build)
  /* Level-wide: built once in level.root, so nothing here switches or pops as the player crosses between the zones. */
  function buildCity(level, api) {
    var G = api.geo, hash = api.hash, Z = level.zones, Z1 = Z[0], Z2 = Z[1] || Z[0];
    var cz0 = Z2.oz + Z2.h, cz1 = Z1.oz;          // the canal between the zones: south bank z1, north bank z0
    var X0 = Math.min(Z1.ox, Z2.ox) - 160, X1 = Math.max(Z1.ox + Z1.w, Z2.ox + Z2.w) + 160;
    var STU = ['#E0A659', '#CF6E45', '#DE9A8B', '#EAD7B0', '#D9B48A', '#C98E6A'], ROOF = '#B85A36', ROOFD = '#93452A';
    var STONE = '#EFE9DC', WIN = '#3A4C5E', SHUT = '#3E7556', T = THREE;
    // a vertical quad in the plane z = zf facing dir (+1 south, -1 north): a flat turned up (2 triangles, no box)
    function vquad(x0, x1, y0, y1, zf, dir, c) {
      G.setMatrix(new T.Matrix4().makeTranslation(0, 0, zf).multiply(new T.Matrix4().makeRotationX(dir > 0 ? Math.PI / 2 : -Math.PI / 2)));
      G.flat(dir > 0 ? [[x0, -y0], [x1, -y0], [x1, -y1], [x0, -y1]] : [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], 0, c);
      G.setMatrix(null);
    }
    // ---- the canal: the water, light ripple bands, the quay walls on both banks beyond the zones
    G.flat([[X0, cz0], [X1, cz0], [X1, cz1], [X0, cz1]], WATER, '#3F8F93');
    for (var i = 0; i < 70; i++) {
      var rx = X0 + hash(i, 3) * (X1 - X0), rz = cz0 + 1.5 + hash(i, 5) * (cz1 - cz0 - 3), L = 2 + hash(i, 7) * 5;
      G.flat([[rx - L, rz - 0.08], [rx + L, rz - 0.08], [rx + L, rz + 0.08], [rx - L, rz + 0.08]], WATER + 0.01, hash(i, 9) < 0.5 ? '#86C8C2' : '#4FA0A4');
    }
    // ---- houses along the banks beyond the zones (each a block with window rows, a roof cap, a few chimneys)
    function house(x0, x1, zf, dir, k, h) {   // front on the plane z = zf facing dir (+1 south, -1 north), depth 10
      var d = 10, zb = zf - dir * d, zc = (zf + zb) / 2, w = x1 - x0, cx = (x0 + x1) / 2, col = STU[Math.floor(hash(k, 11) * STU.length)];
      G.box(cx, (h + WATER) / 2, zc, w, h - WATER, d, col, { hull: true });
      G.box(cx, h + 0.15, zc, w + 0.4, 0.3, d + 0.4, STONE, { hull: false });
      G.box(cx, h + 0.9, zc, w - 0.6, 1.2, d - 2, ROOF, { hull: true });
      var fz = zf + dir * 0.02, n = Math.max(1, Math.floor(w / 1.8)), near = Math.abs(cx - level.zones[0].exitGate.x) < 60;
      for (var fl = 0; fl < 3; fl++) {
        var y0 = 1.6 + fl * 3.2; if (y0 + 1.6 > h - 0.5) break;
        if (!near) { vquad(x0 + 0.5, x1 - 0.5, y0, y0 + 1.5, fz, dir, fl ? WIN : SHUT); continue; }   // far off: one band a floor
        for (var j = 0; j < n; j++) {
          var wx = x0 + (j + 0.5) * w / n;
          vquad(wx - 0.3, wx + 0.3, y0, y0 + 1.6, fz, dir, hash(k * 7 + j, fl) < 0.4 ? SHUT : WIN);
        }
        if (fl === 1 && hash(k, 17) < 0.5) G.box(cx, y0 - 0.1, zf + dir * 0.35, Math.min(w - 1, 3.2), 0.15, 0.7, STONE, { hull: true });
      }
      vquad(x0, x1, WATER, 0.5, fz, dir, STONE);
      if (hash(k, 19) < 0.7) { var chx = x0 + 1 + hash(k, 21) * (w - 2); G.box(chx, h + 2.0, zc, 0.5, 2.2, 0.5, col, { hull: true }); G.cyl(chx, h + 3.1, zc, 0.25, 0.55, 0.7, 7, '#B0563B'); }
    }
    function bankRow(xa, xb, zf, dir, seed) {   // houses from xa to xb along a bank (or a lane), widths 6-11
      var x = xa, k = seed;
      while (x < xb - 3) {
        var w = Math.min(xb - x, 6 + Math.floor(hash(k, 1) * 6)), h = 8 + Math.floor(hash(k, 2) * 4) * 1.5;
        house(x, x + w, zf, dir, k++, h); x += w;
      }
    }
    var s1 = Z1.ox, e1 = Z1.ox + Z1.w, s2 = Z2.ox, e2 = Z2.ox + Z2.w;
    bankRow(X0 + 40, s1, cz1, -1, 100); bankRow(e1, X1 - 40, cz1, -1, 200);       // the south bank, facing north
    bankRow(X0 + 40, s2, cz0, 1, 300); bankRow(e2, X1 - 40, cz0, 1, 400);         // the north bank, facing south
    // quay wall faces under the houses beyond the zones are their stone bases; a walkway kerb line
    // ---- mooring poles: striped paline in groups off both banks, a few moored boats
    var poles = [], boats = [];
    for (var p = 0; p < 14; p++) {
      var px = X0 + 50 + hash(p, 23) * (X1 - X0 - 100), bank = hash(p, 25) < 0.5;
      if (Math.abs(px - Z1.exitGate.x) < 8) continue;
      poles.push([px, bank ? cz1 - 1.6 : cz0 + 1.6]);
      if (hash(p, 27) < 0.45) boats.push([px + 4.5, bank ? cz1 - 2.4 : cz0 + 2.4]);
    }
    poles.forEach(function (q, j) {
      for (var b = 0; b < 4; b++) G.cyl(q[0], WATER - 0.5 + b * 0.9, q[1], 0.13, 0.13, 0.9, 5, b % 2 ? '#F2E8D0' : (j % 2 ? '#B5302E' : '#2F5F92'), { hull: false, noTop: b < 3, noBottom: true });
    });
    boats.forEach(function (b, j) { api.add('Backdrop_Boat', b[0], WATER + 0.25, b[1], R90 + (hash(j, 29) - 0.5) * 0.2, 1); });
    // ---- the bridge under the trail: the deck slab, abutments at both banks, an arch ring on both faces
    var bx = Z1.exitGate.x, bl = cz1 - cz0;
    G.box(bx, -0.33, (cz0 + cz1) / 2, 4.4, 0.62, bl, '#E3DCCD', { hull: false });
    [cz0 + 1.4, cz1 - 1.4].forEach(function (zz) { G.box(bx, (WATER - 0.6 - 0.62) / 2, zz, 4.6, -0.62 - WATER + 0.6, 2.8, '#CBC2AE', { hull: true }); });
    for (var a = 0; a <= 8; a++) {
      var t = a / 8, ang = Math.PI * t, rz = (cz0 + cz1) / 2 - Math.cos(ang) * (bl / 2 - 2.8), ry = WATER + Math.sin(ang) * 0.9 - 0.62;
      [-1, 1].forEach(function (s) { G.box(bx + s * 2.21, Math.max(WATER, ry) + 0.0, rz, 0.04, 0.3, bl / 9, '#EFE9DC', { hull: false }); });
    }
    // ---- the city's roofs round both zones (beyond the walls): blocks of roof with chimneys, a campanile, a dome
    function roofBlock(x, z, w, d, h, k) {
      var col = STU[Math.floor(hash(k, 31) * STU.length)];
      G.box(x, h / 2, z, w, h, d, col, { hull: true });
      G.box(x, h + 0.7, z, w - 0.6, 1.4, d - 0.6, hash(k, 33) < 0.5 ? ROOF : ROOFD, { hull: true });
      if (hash(k, 35) < 0.6) { var chx = x + (hash(k, 37) - 0.5) * (w - 2); G.box(chx, h + 2.2, z + (hash(k, 39) - 0.5) * (d - 2), 0.5, 2.0, 0.5, col, { hull: true }); }
    }
    function ringAround(Zx, seed, skipSouth, skipNorth) {
      var k = seed;
      for (var side = 0; side < 4; side++) {
        if ((side === 2 && skipSouth) || (side === 0 && skipNorth)) continue;
        var horiz = side === 0 || side === 2, len = horiz ? Zx.w + 30 : Zx.h, n = Math.ceil(len / 12);
        for (var j = 0; j < n; j++) {
          var t = (j + 0.5) * len / n, depth = 8 + hash(k, 41) * 6, h = 11 + hash(k, 43) * 5;
          var x, z;
          if (side === 0) {
            x = Zx.ox - 15 + t; z = Zx.oz - 5 - depth / 2;
            // the exit lane and the hatch room run north from the last zone's portal: the houses stand either side
            var gx = Zx.exitGate.x, bw = len / n - 0.4;
            if (Zx === Z[Z.length - 1] && Math.abs(x - gx) < bw / 2 + 3.6) {
              var l0 = x - bw / 2, l1 = x + bw / 2;
              if (l0 < gx - 3.6) roofBlock((l0 + gx - 3.6) / 2, z, gx - 3.6 - l0, depth, h, k);
              if (l1 > gx + 3.6) roofBlock((gx + 3.6 + l1) / 2, z, l1 - gx - 3.6, depth, h, k + 1);
              k += 2; continue;
            }
          }
          else if (side === 2) { x = Zx.ox - 15 + t; z = Zx.oz + Zx.h + 5 + depth / 2; }
          else if (side === 1) { x = Zx.ox + Zx.w + 5 + depth / 2; z = Zx.oz + t; }
          else { x = Zx.ox - 5 - depth / 2; z = Zx.oz + t; }
          roofBlock(x, z, horiz ? len / n - 0.4 : depth, horiz ? depth : len / n - 0.4, h, k++);
        }
      }
    }
    ringAround(Z1, 500, false, true);
    ringAround(Z2, 700, true, false);
    // the garden beyond zone 2's garden wall: trees and cypresses instead of the roofs on that side
    for (var tI = 0; tI < 18; tI++) {
      var tx = Z2.ox - 2.5 - hash(tI, 51) * 3, tz = Z2.oz + 4 + tI * (Z2.h - 8) / 17;
      if (tI % 3 === 1) G.cyl(tx, 0, tz, 0.9, 0.0, 9 + hash(tI, 53) * 3, 7, '#2D5A3A');
      else { G.cyl(tx, 0, tz, 0.25, 0.2, 3.5, 6, '#6E4A30'); G.sphere(tx, 5.2, tz, 2.4 + hash(tI, 55), '#4E9442', { ws: 6, hs: 4 }); }
    }
    // a campanile north-east of the courtyard, a domed church west of the campo
    var kx = Z2.ox + Z2.w + 34, kz = Z2.oz + 10;
    G.box(kx, 18, kz, 7, 36, 7, '#B0563B', { hull: true });
    G.box(kx, 36 + 3.5, kz, 7.6, 7, 7.6, '#EFE9DC', { hull: true });
    [-1, 1].forEach(function (s) { G.box(kx + s * 3.82, 39.5, kz, 0.04, 4, 4.6, '#2B2D33', { hull: false }); G.box(kx, 39.5, kz + s * 3.82, 4.6, 4, 0.04, '#2B2D33', { hull: false }); });
    G.box(kx, 43.5, kz, 6.4, 1.0, 6.4, '#EFE9DC', { hull: true });
    G.cyl(kx, 44, kz, 4.4, 0.0, 9, 4, '#5FA592', { hull: true });
    G.sphere(kx, 53.4, kz, 0.6, '#E3B24A', { ws: 8, hs: 6, hull: false });
    var dx = Z1.ox - 46, dz = Z1.oz + 30;
    G.box(dx, 9, dz, 26, 18, 30, '#EAD7B0', { hull: true });
    G.cyl(dx, 18, dz, 7, 7, 5, 12, '#EFE9DC', { hull: true });
    G.sphere(dx, 23, dz, 7.2, '#8E9AA4', { ws: 12, hs: 8, sy: 0.9 });
    G.cyl(dx, 29, dz, 1.2, 1.0, 3, 8, '#EFE9DC', { hull: true });
    G.sphere(dx, 32.6, dz, 0.7, '#E3B24A', { ws: 8, hs: 6, hull: false });
    // ---- the back of the main house over the exit lane (its modules face the courtyard), either side of the portal
    if (Z[1]) {
      var bgx = Z2.exitGate.x, bz = Z2.oz - 0.5;
      [[Z2.ox, bgx - 2.5], [bgx + 2.5, Z2.ox + Z2.w]].forEach(function (s) {
        G.box((s[0] + s[1]) / 2, HP / 2, bz - 0.005, s[1] - s[0], HP, 0.99, '#DE9A8B', { hull: false });
        G.box((s[0] + s[1]) / 2, HP - 0.2, bz - 0.55, s[1] - s[0], 0.4, 0.2, '#EFE9DC', { hull: false });
        for (var wx = s[0] + 1.5; wx < s[1] - 1; wx += 3) vquad(wx - 0.3, wx + 0.3, 9.0, 10.8, bz - 0.51, -1, WIN);
      });
    }
    // ---- the portal facades over the gates (the gates are placed by the engine with the portal frame)
    if (Z1.entryGate) api.add('GateTop_3', Z1.entryGate.x, 0, Z1.entryGate.z, Math.PI, 1);
    if (Z[1]) {
      if (Z2.entryGate) api.add('GateTop_C', Z2.entryGate.x, 0, Z2.entryGate.z, Math.PI, 1);
      api.add('GateTop_P', Z2.exitGate.x, 0, Z2.exitGate.z, 0, 1);
    }
  }

  var PIECES = ['GateFrame', 'GateShutter', 'GateTop_3', 'GateTop_P', 'GateTop_C', 'Bridge_A', 'Bridge_B', 'Calle_A', 'Calle_B', 'Calle_C',
    'Hatch', 'Quay_A', 'Quay_P', 'Quay_R', 'HP_Corner', 'H3_Corner', 'H2_Corner', 'Backdrop_Boat', 'LampPost_Glow', 'Landmark_Stair_Glow',
    'GW_A', 'GW_V', 'GW_N', 'GW_L', 'GW_D'];
  ['Win', 'WinC', 'WinF', 'Pier', 'PierL', 'PierC', 'Door', 'Shop', 'Plain', 'BalL', 'BalM', 'BalR', 'Quoin', 'InL', 'InR'].forEach(function (k) { PIECES.push('H3_' + k); });
  ['Win', 'Pier', 'PierL', 'Door', 'Shop', 'Plain', 'BalL', 'BalM', 'BalR', 'Quoin', 'InL', 'InR'].forEach(function (k) { PIECES.push('H2_' + k); });
  ['Win', 'Pier', 'PierL', 'Door', 'BalL', 'BalM', 'BalR', 'Quoin', 'InL', 'InR'].forEach(function (k) { PIECES.push('HP_' + k); });
  ['Win', 'WinC', 'Pier', 'PierL', 'BalL', 'BalM', 'BalR', 'Quoin', 'InL', 'InR'].forEach(function (k) { PIECES.push('C_' + k); });
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (!d.pieces) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'venetian', name: "Ca' Doranza", family: 'kit-venetian', prefix: 'KIT_VENETIAN_',
    palette: ['#E0A659', '#DE9A8B', '#3F8F93', '#EFE9DC'],
    // late afternoon: a clear sky going gold toward the horizon, a warm low sun from the west, a light haze
    env: { sky: ['#6FA8DE', '#F4D7AE'], fog: { color: '#EED6B6', near: 70, far: 280 }, sun: [-0.62, 0.62, 0.32], sunColor: '#FFE6C2', clouds: true, ceiling: null },
    floor: { color: '#9B958D', trail: '#C9C0B2', lines: [{ dir: 'x', every: 1, width: 0.03, color: '#8A847D', y: 0.005 }, { dir: 'z', every: 1, width: 0.03, color: '#8A847D', y: 0.005 }],
      trailLines: [{ dir: 'x', every: 0.5, width: 0.025, color: '#B5AC9F', y: 0.006 }] },
    wall: { height: 1.1, roof: '#B85A36', facing: 'open', choose: chooseWall, paint: paintWall, cols: true },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // the trail between the zones is the private bridge over the canal; the exit path a lane between house walls
    trail: { wall: 'Calle_A', variants: ['Calle_B', 'Calle_C', 'Calle_A'], height: 3.4, byTrail: { 0: { wall: 'Bridge_A', variants: ['Bridge_A', 'Bridge_B', 'Bridge_A'], height: 1.1 } } },
    hatch: 'Hatch', stand: 'Crates',
    backdrop: { build: buildCity },
    budget: { prop: 4400, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      venetian: {
        name: "Ca' Doranza",
        intro: "Robots have taken Ca' Doranza, a mansion on the canal. Clear the Campo dei Venti from the cafes to the fountain, cross the bridge and take back the courtyard and its cloister.",
        zones: [
          // the campo: the fountain, the cafes and their terraces, the loggia; the first wave is light robots only
          { map: 'venetian_1', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 6]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 7], ['blader', 4]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 7], ['blader', 4]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 6], ['blader', 5]],
            [['crawler', 17], ['gunner', 10], ['drone', 7], ['soldier', 6], ['blader', 3]]] },
          // the courtyard: the cloister and its upper walk, the grand staircase, the gardens
          { map: 'venetian_2', waves: [
            [['crawler', 18], ['gunner', 11], ['drone', 5], ['soldier', 6], ['blader', 5]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 6], ['blader', 4]],
            [['crawler', 18], ['gunner', 11], ['bomber', 2], ['soldier', 5], ['blader', 4]],
            [['crawler', 17], ['drone', 8], ['gunner', 10], ['soldier', 5], ['blader', 3]],
            [['crawler', 19], ['gunner', 11], ['bomber', 2], ['soldier', 4]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
