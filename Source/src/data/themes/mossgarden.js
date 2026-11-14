/* Theme: Mosswood Gardens (kit-mossgarden) -- a landscaped garden on a clear spring afternoon behind old mossy stone
   walls, woodland and the house (made-up Mosswood estate) beyond them. Two zones:
   1 The formal garden (72 x 70): the tiered FOUNTAIN on its round cobbled plaza (the landmark: an octagonal basin,
     three brimming bowls, falling water drawn additive), four parterres of box hedge round tulip beds, roses,
     lavender and spiral topiary, the raised TERRACE (2.34 m) across the north-west with balustrades, urn piers, a
     flower border along the wall, the wisteria pergola, tea tables and a belvedere at the head of the grand stair
     (a side stair and an east stair too), two wall fountains under its balustrade, the rose walk under iron rose
     arches, the GLASSHOUSE (walk-in: a white iron palm house with a barrel vault and a ridge lantern, raised beds of
     made-up exotics, two parasol palms, a lily pool, glass drawn additive), yew screens round the entry court, and
     three huge old trees (two oaks and a cedar, trunks 3 m across, canopies 9 m up).
   2 The wild garden (74 x 70): the reflecting pool on the axis from the entry gate (wadeable, walkable coping), the
     stream from the grotto spring on the west wall to the culvert in the east wall (an animated ribbon; wade it,
     cross on the two arched stone bridges or the stepping stones), the RUINED FOLLY on a 3 m mound (the landmark: a
     broken ring of columns, a fragment of entablature and dome ribs, the plinth steps), the hedge maze in the north-east
     (2.7 m yew, 2 m corridors, the armillary room, an arch at the entrance), the gazebo by the stream, the nursery yard
     (potting shed, benches, cold frames, compost bays, barrow, pots), wildflower meadows, tree ferns, lumenbell pods
     (a made-up species: lantern pods with glowing cores, theme.glow pulses them), mossy boulders, fallen logs and
     three more huge trees.
   Built by blender/fam_kit_mossgarden.py (mg_*.py); zone layouts by tools/mossgarden_zones.py, which reads GARDEN
   below (paths, plaza rings, the stream, the terrace and the mound) so the cobbled paths and the stream drawn here
   and the cells the layout keeps clear for them agree.

   Ground: the theme's terrain (flat but for the terrace and the mound) painted as mown lawn (zone 1 in stripes),
   gravel, wild grass and moss; the cobbled paths and plaza rings (a canvas texture of inked cobbles on the world's toon
   material, kerbs with an ink edge) and the stream (its own shader: flowing streaks, foam at the banks) are smooth
   ribbons laid over it by backdrop.build (no stepped edges). The terrace's ring cells stand on the slope from the
   terrace down to the garden, so their symbols use the engine option onTerrain: false (zones.js buildCells).
   Backdrop (level-wide): woodland round the walls (instanced by kind and sector), the house on its rise in the north,
   bank stones and reeds along the stream.
   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled; R90 / -R90 = front east / west):
     # wall: the old garden wall (2 m modules plain / ivy / pier, 1 m fillers, corner piers)
     ground: . lawn   ; cobbled path / plaza (ribbon drawn by the theme)   : gravel   _ terrace lawn   ~ stream water
     and its banks (zone 2)
     Terrace (zone 1): B | balustrade module on the south row / the east column (its front, the walk side, turned
             to the terrace; every 6th has a pier and an urn)   K corner pier   Q ^ back border against the north /
             west garden wall (a planter)   U grand stair [5,5] rising north
             u side stair [3,5] rising north   Y east stair [5,3] rising west (TerraceStairS turned)
             p wisteria pergola [6,4]   e tea table [2,2]
     Hedges (link runs): l box hedge 0.6 m   m mid hedge 1.25 m   H yew 2.7 m (the maze, the entry screens)
     F the tiered fountain [9,9] (landmark, zone 1)   w wall fountain [3,1] (front south, its back on the terrace wall)
     W wall fountain [3,1] against the garden wall (orient wall)   X the glasshouse [14,10] (doors west, east, south)
     R rose arch [4,1] over a north-south path   r rose bush   y hydrangea   b tulip bed [4,2] (repainted per copy)
     v lavender drift [3,2]   n wildflower meadow [2,2]   s spiral topiary   c cone yew   o ball topiary
     L lamp post   j k bench [2,1] facing south / north   < > bench [1,2] (turned) facing west / east   q urn
     d sundial   A armillary   g signpost   O giant oak [4,4]   C giant cedar [4,4]   f tree fern [2,2]   z fern
     x lumenbell pods   @ mossy boulder [2,2]   % mossy rock   = fallen log [4,1]
     Zone 2: M the ruined folly [7,7] (landmark, on the mound)   Z gazebo [5,5]   D stone bridge [3,5] (walk N-S)
             i stepping stones   V reflecting pool [3,16]   N grotto spring [4,2] (orient wall)   I culvert [3,1]
             (orient wall)   & maze arch [4,1]   $ potting shed [5,4] (front west)   T potting bench [2,1]
             t cold frame [2,1]   ! compost bays [2,1]   ? wheelbarrow [1,2]   + stacked pots   * seedling crate */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;

  // ---------------------------------------------------------------- the garden's ground plan (read by tools/mossgarden_zones.py)
  // zone-local metres (x east, z south); paths: { w, pts } (Catmull-Rom through pts); plazas: [cx, cz, inner r, outer r];
  // terrace: [c0, r0, c1, r1, h] corner range lifted to h (zone 1); mound: [cx, cz, plateau r, foot r, h] (zone 2)
  var GARDEN = /*GARDEN*/{
    "terrace": [2, 2, 44, 12, 2.34],
    "mound": [17.5, 15.5, 6.0, 13.0, 3.0],
    "paths": [
      [
        { "w": 3.0, "pts": [[35.5, 17.4], [35.5, 23.0], [35.5, 30.2]] },
        { "w": 3.0, "pts": [[35.5, 46.8], [35.5, 56.0], [35.5, 67.0]] },
        { "w": 2.4, "pts": [[27.0, 38.5], [22.0, 38.1], [17.5, 40.3], [13.0, 39.5], [9.0, 38.6]] },
        { "w": 2.4, "pts": [[44.0, 38.5], [48.0, 38.8], [52.4, 40.0]] },
        { "w": 2.4, "pts": [[9.5, 17.4], [9.1, 21.0], [9.0, 28.0], [9.0, 36.0], [9.0, 44.0], [9.4, 52.0], [11.6, 58.4], [16.0, 62.4], [24.0, 64.6], [33.8, 65.6]] },
        { "w": 2.6, "pts": [[41.6, 32.1], [46.0, 32.5], [54.0, 32.6], [59.4, 30.6], [61.5, 25.0], [61.5, 15.0], [61.5, 1.4]] },
        { "w": 2.2, "pts": [[59.0, 45.3], [60.0, 50.0], [60.4, 56.0], [57.0, 61.6], [48.0, 64.6], [37.2, 65.6]] },
        { "w": 2.2, "pts": [[48.6, 6.0], [52.0, 8.6], [56.5, 9.4], [60.6, 9.0]] }
      ],
      [
        { "w": 2.4, "pts": [[16.2, 66.8], [13.6, 62.0], [13.3, 52.0], [13.6, 42.6], [15.6, 38.4], [17.5, 37.5]] },
        { "w": 2.4, "pts": [[18.8, 66.8], [21.4, 62.0], [21.7, 52.0], [21.4, 42.6], [19.4, 38.4], [17.5, 37.5]] },
        { "w": 2.4, "pts": [[17.5, 31.6], [19.6, 28.4], [23.6, 25.4], [26.0, 21.0], [25.4, 16.6], [21.6, 15.3]] },
        { "w": 2.4, "pts": [[20.8, 12.2], [24.8, 8.6], [30.4, 5.6], [36.0, 3.2], [37.5, 1.4]] },
        { "w": 2.2, "pts": [[52.5, 32.6], [55.0, 29.6], [58.6, 27.2], [60.5, 25.4]] },
        { "w": 2.2, "pts": [[52.5, 38.5], [55.6, 39.4], [60.5, 39.6]] },
        { "w": 2.2, "pts": [[60.5, 45.4], [60.2, 49.2], [58.0, 52.6]] },
        { "w": 2.4, "pts": [[21.8, 46.2], [28.0, 45.0], [36.0, 43.4], [44.0, 41.0], [50.0, 39.6], [52.5, 38.5]] },
        { "w": 2.2, "pts": [[43.6, 13.6], [40.4, 9.8], [37.6, 5.2]] }
      ]
    ],
    "plazas": [[[35.5, 38.5, 4.42, 9.0]], [[17.5, 15.5, 3.45, 4.8]]],
    "streams": [[], [{ "w": 2.6, "pts": [[2.5, 32.9], [8.0, 34.4], [14.0, 35.0], [17.5, 34.6], [22.0, 33.5], [28.0, 33.0], [34.0, 34.4], [40.0, 36.4], [46.0, 37.0], [52.0, 36.0], [58.0, 35.0], [64.0, 36.0], [72.55, 36.6]] }]]
  }/*END*/;
  var TER = GARDEN.terrace[4];

  // ---------------------------------------------------------------- terrain: the terrace (zone 1) and the mound (zone 2)
  function terrainHeight(c, r, zi) {
    var T = GARDEN.terrace, M = GARDEN.mound;
    if (zi === 0) return (c >= T[0] && c <= T[2] && r >= T[1] && r <= T[3]) ? T[4] : 0;
    if (zi !== 1) return 0;
    var d = Math.hypot(c - M[0], r - M[1]);
    if (d <= M[2]) return M[4];
    if (d >= M[3]) return 0;
    var k = (M[3] - d) / (M[3] - M[2]);
    return M[4] * k * k * (3 - 2 * k);
  }
  function near(g, c, r, set, rad) {
    for (var dr = -rad; dr < rad; dr++) for (var dc = -rad; dc < rad; dc++) if (set.indexOf(g.at(c + dc, r + dr)) >= 0) return true;
    return false;
  }
  function paint(c, r, zi, g) {
    var n = { ':': 0, '~': 0, '_': 0, ',': 0 }, ch, dc, dr;
    for (dr = -1; dr <= 0; dr++) for (dc = -1; dc <= 0; dc++) { ch = g.at(c + dc, r + dr); if (n[ch] !== undefined) n[ch]++; }
    if (n['~']) return ['#3E6A48', 0.55 + 0.11 * n['~']];
    if (n[':']) return ['#DCCFB0', 0.3 + 0.17 * n[':']];
    if (near(g, c, r, 'OC', 4)) return ['#4F8A40', 0.55];
    if (zi === 0) {
      if (n['_']) return [(Math.floor(r / 2) % 2) ? '#8BCB60' : '#7DC157', 0.6];
      return [(Math.floor((c + 1) / 3) % 2) ? '#88C95E' : '#77BC55', 0.55];
    }
    if (n[',']) return ['#9DBD58', 0.35 + 0.12 * n[',']];
    var m = Math.sin(c * 0.29 + r * 0.17) + Math.sin(c * 0.11 - r * 0.31 + 2.0);
    if (near(g, c, r, 'fzx@%=', 2)) return ['#5E9446', 0.5];
    return m > 0.9 ? ['#97C25E', 0.45] : (m < -1.1 ? ['#5F9E4A', 0.4] : null);
  }

  // ---------------------------------------------------------------- walls: 2 m modules paired along each run
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
  // a 2 m module covers its own cell and the next one along its local +X (east on a north wall, west on a south wall,
  // north on an east wall, south on a west wall); cells pair up from even u and the pair's module stands in the cell
  // whose +X neighbour is the other one
  var DIRX = { S: 1, N: -1, E: -1, W: 1 };
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var F = face || faceOf(g, c, r);
    if (F === 'none' || F === 'corner') return 'WallCorner';
    if (gateDist(g, c, r) < 2.6) return null;
    var along = F === 'S' || F === 'N', u = along ? c : r, s = DIRX[F];
    var anchor = s > 0 ? (u % 2 === 0) : (u % 2 === 1);
    function cell(du) { return along ? inRun(g, c + du, r, F) : inRun(g, c, r + du, F); }
    if (anchor) {
      if (!cell(s)) return 'Wall1';
      var h = hash(c * 5 + 1, r * 3 + 7);
      return h < 0.09 ? 'Wall2_C' : h < 0.27 ? 'Wall2_B' : 'Wall2_A';
    }
    return cell(-s) ? null : 'Wall1';
  }

  // ---------------------------------------------------------------- symbols
  // palette cells (blender/mg_base.py): tulip 32, tulipY 33, tulipP 34, tulipO 35, tulipW 36, tulipV 37, rose 38,
  // roseP 39, lav 40, lav2 41, water 48
  var TULIPS = { from: [32], to: [[32], [33], [34], [35], [36], [37], [34], [33]] };
  var ROSES = { from: [38], to: [[38], [39], [36], [33], [38]] };
  var HYDRA = { from: [40, 41], to: [[40, 41], [39, 38], [48, 49], [36, 39]] };
  function pf(size, pieces, face, extra) { var d = { size: size, pieces: pieces, kind: 'cover' }; if (face !== undefined) d.face = face; return Object.assign(d, extra || {}); }
  function hedge(kind) { return { pieces: [kind + 'Half'], full: kind + 'Full', post: kind + 'Post', links: { Box: 'l', Mid: 'm', Yew: 'H&' }[kind], kind: 'cover' }; }
  var SYMBOLS = {
    // terrace
    // (the ring cells sit on the terrain's slope from the terrace down to the garden: onTerrain false stands them on 0)
    'B': { pieces: ['TerraceWall', 'TerraceWall', 'TerraceWall', 'TerraceWall_P', 'TerraceWall', 'TerraceWall'], alternate: true, rotate: Math.PI, kind: 'cover', onTerrain: false },
    '|': { pieces: ['TerraceWall', 'TerraceWall', 'TerraceWall', 'TerraceWall_P', 'TerraceWall', 'TerraceWall'], alternate: true, rotate: -R90, kind: 'cover', onTerrain: false },
    'K': { pieces: ['TerraceCorner'], kind: 'cover', onTerrain: false },
    'Q': { pieces: ['TerraceBack_A', 'TerraceBack_B'], alternate: true, rotate: 0, kind: 'cover', onTerrain: false },
    '^': { pieces: ['TerraceBack_A', 'TerraceBack_B'], alternate: true, rotate: R90, kind: 'cover', onTerrain: false },
    'U': pf([5, 5], ['TerraceStair'], 0),
    'u': pf([3, 5], ['TerraceStairS'], 0),
    'Y': pf([3, 5], ['TerraceStairS'], R90),
    'p': pf([6, 4], ['Pergola'], 0),
    'e': pf([2, 2], ['TeaTable'], undefined, { flip: true }),
    // hedges
    'l': hedge('Box'), 'm': hedge('Mid'), 'H': hedge('Yew'),
    // water, buildings, big plants
    'F': pf([9, 9], ['Landmark_Fountain'], 0),
    'w': pf([3, 1], ['WallFountain'], 0),
    'W': pf([3, 1], ['WallFountain'], undefined, { orient: 'wall' }),
    'X': pf([14, 10], ['Landmark_Glasshouse'], 0),
    'R': pf([4, 1], ['RoseArch'], 0),
    'O': pf([4, 4], ['Landmark_Oak_A', 'Landmark_Oak_B'], undefined, { flip: true }),
    'C': pf([4, 4], ['Landmark_Cedar'], undefined, { flip: true }),
    'f': pf([2, 2], ['TreeFern'], undefined, { flip: true }),
    '@': pf([2, 2], ['MossBoulder'], undefined, { flip: true }),
    '=': pf([4, 1], ['FallenLog'], undefined, { flip: true }),
    // beds and plants
    'b': { size: [4, 2], pieces: ['TulipBed'], flip: true, collide: false, paint: TULIPS },
    'v': { size: [3, 2], pieces: ['Lavender'], flip: true, collide: false },
    'n': { size: [2, 2], pieces: ['Meadow'], flip: true, collide: false },
    'r': { pieces: ['RoseBush'], rotate: 'random90', kind: 'cover', paint: ROSES },
    'y': { pieces: ['Hydrangea'], rotate: 'random90', kind: 'cover', paint: HYDRA },
    's': { pieces: ['Spiral'], rotate: 'random90', kind: 'cover' },
    'c': { pieces: ['ConeTopiary'], kind: 'cover' },
    'o': { pieces: ['BallTopiary'], kind: 'cover' },
    'z': { pieces: ['Fern'], rotate: 'random90', collide: false },
    'x': { pieces: ['GlowPod'], rotate: 'random90', kind: 'cover' },
    '%': { pieces: ['MossRock'], rotate: 'random90', kind: 'cover' },
    // garden furniture
    'L': { pieces: ['LampPost'], kind: 'cover' },
    'j': pf([2, 1], ['Bench'], 0), 'k': pf([2, 1], ['Bench'], Math.PI),
    '<': pf([2, 1], ['Bench'], -R90), '>': pf([2, 1], ['Bench'], R90),
    'q': { pieces: ['Urn'], kind: 'cover', paint: TULIPS },
    'd': { pieces: ['Sundial'], kind: 'cover' },
    'A': { pieces: ['Armillary'], kind: 'cover' },
    'g': { pieces: ['Signpost_A', 'Signpost_B'], kind: 'cover', rotate: 'edge', edge: ';' },
    // zone 2
    'M': pf([7, 7], ['Landmark_Folly'], 0),
    'Z': pf([5, 5], ['Gazebo'], 0),
    'D': pf([3, 5], ['Bridge'], 0),
    'i': { pieces: ['SteppingStone'], rotate: 'random90', collide: false },
    'V': pf([3, 16], ['ReflectPool'], 0),
    'N': pf([4, 2], ['Grotto'], undefined, { orient: 'wall' }),
    'I': pf([3, 1], ['Culvert'], undefined, { orient: 'wall' }),
    '&': pf([4, 1], ['MazeArch'], 0),
    '$': pf([5, 4], ['Shed'], -R90),
    'T': pf([2, 1], ['PottingBench'], undefined, { orient: 'wall' }),
    't': pf([2, 1], ['ColdFrame'], undefined, { flip: true }),
    '!': pf([2, 1], ['Compost'], undefined, { orient: 'wall' }),
    '?': pf([1, 2], ['Wheelbarrow'], undefined, { flip: true }),
    '+': { pieces: ['PotStack'], rotate: 'random90', kind: 'cover' },
    '*': { pieces: ['Crate_Seed'], rotate: 'random90', kind: 'cover' }
  };
  var GLOW = {
    GlowPod: { piece: 'GlowPod_Glow', groups: 3 },
    LampPost: { piece: 'LampPost_Glow' },
    Landmark_Fountain: { piece: 'Fountain_Spray', blend: 'add' },
    WallFountain: { piece: 'WallFountain_Spray', blend: 'add' },
    Grotto: { piece: 'Grotto_Spray', blend: 'add' },
    Landmark_Glasshouse: { piece: 'Glasshouse_Glass', blend: 'add' }
  };

  // ---------------------------------------------------------------- shared curve sampling (tools/mossgarden_zones.py mirrors it)
  function catmull(pts, step) {
    var P = [pts[0]].concat(pts, [pts[pts.length - 1]]), out = [];
    for (var i = 0; i + 3 < P.length; i++) {
      var a = P[i], b = P[i + 1], c = P[i + 2], d = P[i + 3], L = Math.hypot(c[0] - b[0], c[1] - b[1]), n = Math.max(2, Math.ceil(L / step));
      for (var k = (i ? 1 : 0); k <= n; k++) {
        var t = k / n, t2 = t * t, t3 = t2 * t;
        out.push([0, 1].map(function (j) { return 0.5 * (2 * b[j] + (-a[j] + c[j]) * t + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * t2 + (-a[j] + 3 * b[j] - 3 * c[j] + d[j]) * t3); }));
      }
    }
    return out;
  }
  // even arc-length samples (spacing ds) with unit normals
  function resample(pts, ds) {
    var P = catmull(pts, 0.2), cum = [0], i;
    for (i = 1; i < P.length; i++) cum.push(cum[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    var L = cum[cum.length - 1], n = Math.max(1, Math.round(L / ds)), out = [], j = 0;
    for (var k = 0; k <= n; k++) {
      var s = k / n * L;
      while (j < cum.length - 2 && cum[j + 1] < s) j++;
      var f = (s - cum[j]) / Math.max(1e-6, cum[j + 1] - cum[j]);
      out.push({ x: P[j][0] + (P[j + 1][0] - P[j][0]) * f, z: P[j][1] + (P[j + 1][1] - P[j][1]) * f, s: s });
    }
    for (k = 0; k < out.length; k++) {
      var A = out[Math.max(0, k - 1)], B = out[Math.min(out.length - 1, k + 1)], tx = B.x - A.x, tz = B.z - A.z, tl = Math.hypot(tx, tz) || 1;
      out[k].nx = -tz / tl; out[k].nz = tx / tl;
    }
    return out;
  }
  function distPoly(S, x, z) { var d = 1e9; for (var i = 0; i < S.length; i++) d = Math.min(d, Math.hypot(S[i].x - x, S[i].z - z)); return d; }

  // a 1.68 m square of inked cobbles in staggered courses (canvas texture, repeats along the paths)
  function cobbleTexture(T, hash) {
    if (cobbleTexture.tex) return cobbleTexture.tex;
    var N = 256, cv = document.createElement('canvas'); cv.width = cv.height = N;
    var g = cv.getContext('2d'), STONE = ['#CFC4AE', '#BDB19A', '#DAD0BA', '#ADA08A', '#C6BBA2'], rows = 4, cols = 4, h = N / rows, w = N / cols;
    g.fillStyle = '#6E6557'; g.fillRect(0, 0, N, N);
    for (var r = 0; r < rows; r++) for (var c = -1; c <= cols; c++) {
      var x = c * w + (r % 2) * w / 2, y = r * h, k = hash(r * 7 + c + 11, c * 3 + r + 5);
      var j1 = (hash(r, c) - 0.5) * 5, j2 = (hash(c, r + 9) - 0.5) * 5, m = 5;
      var x0 = x + m + j1, x1 = x + w - m + j2, y0 = y + m, y1 = y + h - m, rad = 14;
      g.beginPath();
      g.moveTo(x0 + rad, y0); g.lineTo(x1 - rad, y0); g.quadraticCurveTo(x1, y0, x1, y0 + rad); g.lineTo(x1, y1 - rad); g.quadraticCurveTo(x1, y1, x1 - rad, y1);
      g.lineTo(x0 + rad, y1); g.quadraticCurveTo(x0, y1, x0, y1 - rad); g.lineTo(x0, y0 + rad); g.quadraticCurveTo(x0, y0, x0 + rad, y0);
      g.fillStyle = STONE[Math.floor(k * STONE.length)]; g.fill();
      g.lineWidth = 4; g.strokeStyle = '#2E2923'; g.stroke();
      g.fillStyle = 'rgba(255,255,255,0.22)'; g.fillRect(x0 + 8, y0 + 6, (x1 - x0) * 0.45, 5);
    }
    var t = new T.CanvasTexture(cv);
    t.wrapS = t.wrapT = T.RepeatWrapping; t.anisotropy = 4;
    return (cobbleTexture.tex = t);
  }

  // ---------------------------------------------------------------- backdrop: ground, woodland, the house, paths, stream
  function buildGarden(level, api) {
    var T = typeof THREE !== 'undefined' ? THREE : null;
    var hash = api.hash, zones = level.zones, G = api.geo, world = level.world;
    var x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    zones.forEach(function (z) { x0 = Math.min(x0, z.ox); x1 = Math.max(x1, z.ox + z.w); z0 = Math.min(z0, z.oz); z1 = Math.max(z1, z.oz + z.h); });
    var hz = level.hatch ? level.hatch.z : z0 - 26, zN = Math.min(z0, hz - 8), cx = (x0 + x1) / 2, cz = (zN + z1) / 2;
    if (!T) return;
    var C = function (h) { return new T.Color(h); };
    // ---- the meadow and woodland floor round the walls
    G.flat([[cx - 800, cz - 800], [cx + 800, cz - 800], [cx + 800, cz + 800], [cx - 800, cz + 800]], -0.04, C('#5F9A47'));
    // ---- cobbled paths and plaza rings: smooth ribbons textured with inked cobbles (one canvas texture, the world's
    // toon material), kerbs and their ink edge as vertex-coloured strips (zone-local data -> world)
    var MORTAR = C('#7A7062'), KERB = C('#D9CFBA'), INK = C('#2A2622');
    function gy(x, z) { return world.groundAt(x, z); }
    function quad(a, b, c, d, col) {   // [x, y, z] corners in order round the quad, facing up
      var i0 = G._vert(a[0], a[1], a[2], 0, 1, 0, col), i1 = G._vert(b[0], b[1], b[2], 0, 1, 0, col), i2 = G._vert(c[0], c[1], c[2], 0, 1, 0, col), i3 = G._vert(d[0], d[1], d[2], 0, 1, 0, col);
      var ux = b[0] - a[0], uz = b[2] - a[2], vx = d[0] - a[0], vz = d[2] - a[2];
      if (uz * vx - ux * vz > 0) G.idx.push(i0, i1, i2, i0, i2, i3); else G.idx.push(i0, i2, i1, i0, i3, i2);
    }
    var TILE = 1.68, cob = cobbleTexture(T, hash), RB = { pos: [], nor: [], col: [], uv: [], hull: [], idx: [] };
    function rv(x, y, z, u, v, c) { RB.pos.push(x, y, z); RB.nor.push(0, 1, 0); RB.col.push(c.r, c.g, c.b); RB.uv.push(u, v); RB.hull.push(0, 0, 0); return RB.pos.length / 3 - 1; }
    function rquad(a, b, c, d) { var ux = b[0] - a[0], uz = b[2] - a[2], vx = d[0] - a[0], vz = d[2] - a[2]; if (uz * vx - ux * vz > 0) RB.idx.push(a[3], b[3], c[3], a[3], c[3], d[3]); else RB.idx.push(a[3], c[3], b[3], a[3], d[3], c[3]); }
    zones.forEach(function (Z, zi) {
      var paths = (GARDEN.paths[zi] || []).map(function (p) { return { w: p.w, S: resample(p.pts.map(function (q) { return [Z.ox + q[0], Z.oz + q[1]]; }), 0.42) }; });
      var plazas = (GARDEN.plazas[zi] || []).map(function (q) { return [Z.ox + q[0], Z.oz + q[1], q[2], q[3]]; });
      var KW = 0.2, tint = zi === 1 ? C('#E2EED0') : C('#FFFFFF');
      function covered(x, z, self) {   // inside another path or a plaza ring (its kerb would cut across the join)
        for (var i = 0; i < paths.length; i++) if (i !== self && distPoly(paths[i].S, x, z) < paths[i].w / 2 + KW - 0.02) return true;
        for (i = 0; i < plazas.length; i++) { var d = Math.hypot(x - plazas[i][0], z - plazas[i][1]); if (d < plazas[i][3] + KW - 0.02 && d > plazas[i][2] - 0.05) return true; }
        return false;
      }
      paths.forEach(function (P, pi) {
        var S = P.S, hw = P.w / 2, yo = 0.03 + 0.006 * pi, u0 = hash(pi, zi) * 3;
        function at(k, t, dy) { var q = S[k], x = q.x + q.nx * t, z = q.z + q.nz * t; return [x, gy(x, z) + yo + (dy || 0), z]; }
        function rat(k, t) { var p = at(k, t, 0.004); p.push(rv(p[0], p[1], p[2], u0 + (t + hw) / TILE, S[k].s / TILE, tint)); return p; }
        var prev = [rat(0, -hw - 0.02), rat(0, hw + 0.02)];
        for (var k = 0; k + 1 < S.length; k++) {
          var cur = [rat(k + 1, -hw - 0.02), rat(k + 1, hw + 0.02)];
          rquad(prev[0], prev[1], cur[1], cur[0]);
          prev = cur;
          if (k % 2) continue;
          var k2 = Math.min(k + 2, S.length - 1);   // kerbs and their ink edge: one strip per two cobble rows
          quad(at(k, -hw - KW), at(k, hw + KW), at(k2, hw + KW), at(k2, -hw - KW), MORTAR);
          [-1, 1].forEach(function (sd) {
            var mx = (S[k].x + S[k2].x) / 2 + (S[k].nx + S[k2].nx) / 2 * sd * (hw + KW / 2), mz = (S[k].z + S[k2].z) / 2 + (S[k].nz + S[k2].nz) / 2 * sd * (hw + KW / 2);
            if (covered(mx, mz, pi)) return;
            var a = sd * hw, b = sd * (hw + KW), e = sd * (hw + KW - 0.045);
            quad(at(k, a, 0.008), at(k, e, 0.008), at(k2, e, 0.008), at(k2, a, 0.008), KERB);
            quad(at(k, e, 0.01), at(k, b, 0.01), at(k2, b, 0.01), at(k2, e, 0.01), INK);
          });
        }
      });
      plazas.forEach(function (Q) {
        var yo = 0.03 + 0.006 * 9, R0 = Q[2], R1 = Q[3], NA = Math.ceil(2 * Math.PI * (R1 + KW) / 0.5), k, j;
        function pt(a, r, dy) { var x = Q[0] + Math.cos(a) * r, z = Q[1] + Math.sin(a) * r; return [x, gy(x, z) + yo + (dy || 0), z]; }
        var NR = Math.max(1, Math.round((R1 - R0) / 1.0)), rows = [];
        for (j = 0; j <= NR; j++) {
          var rr = R0 + (R1 + 0.02 - R0) * j / NR, row = [];
          for (k = 0; k <= NA; k++) { var a = k / NA * 2 * Math.PI, p = pt(a, rr, 0.004); p.push(rv(p[0], p[1], p[2], a * (R0 + R1) / 2 / TILE, rr / TILE, tint)); row.push(p); }
          rows.push(row);
        }
        for (j = 0; j < NR; j++) for (k = 0; k < NA; k++) rquad(rows[j][k], rows[j][k + 1], rows[j + 1][k + 1], rows[j + 1][k]);
        for (k = 0; k < NA; k++) {
          var a0 = k / NA * 2 * Math.PI, a1 = (k + 1) / NA * 2 * Math.PI;
          quad(pt(a0, R1 - 0.05), pt(a0, R1 + KW), pt(a1, R1 + KW), pt(a1, R1 - 0.05), MORTAR);
          quad(pt(a0, R1, 0.008), pt(a0, R1 + KW - 0.045, 0.008), pt(a1, R1 + KW - 0.045, 0.008), pt(a1, R1, 0.008), KERB);
          quad(pt(a0, R1 + KW - 0.045, 0.01), pt(a0, R1 + KW, 0.01), pt(a1, R1 + KW, 0.01), pt(a1, R1 + KW - 0.045, 0.01), INK);
        }
      });
    });
    if (RB.idx.length) {
      var rg = new T.BufferGeometry();
      rg.setAttribute('position', new T.Float32BufferAttribute(RB.pos, 3));
      rg.setAttribute('normal', new T.Float32BufferAttribute(RB.nor, 3));
      rg.setAttribute('color', new T.Float32BufferAttribute(RB.col, 3));
      rg.setAttribute('uv', new T.Float32BufferAttribute(RB.uv, 2));
      rg.setAttribute('aHull', new T.Float32BufferAttribute(RB.hull, 3));
      rg.setIndex(RB.idx); rg.computeBoundingSphere();
      var rm = new T.Mesh(rg, IB.Render.toonMaterial({ map: cob })); rm.name = 'Cobbles';
      level.root.add(rm);
    }
    // ---- the stream: an animated ribbon (own shader with the fog's haze), bank stones and reeds along it
    var streamMats = [];
    zones.forEach(function (Z, zi) {
      (GARDEN.streams[zi] || []).forEach(function (st) {
        var S = resample(st.pts.map(function (q) { return [Z.ox + q[0], Z.oz + q[1]]; }), 0.5), hw = st.w / 2, pos = [], uv = [], idx = [];
        for (var k = 0; k < S.length; k++) {
          for (var e = 0; e <= 4; e++) {
            var t = -1 + e / 2, x = S[k].x + S[k].nx * t * (hw + 0.25), z = S[k].z + S[k].nz * t * (hw + 0.25);
            pos.push(x, 0.045, z); uv.push(t, S[k].s);
          }
        }
        for (k = 0; k + 1 < S.length; k++) for (e = 0; e < 4; e++) { var a = k * 5 + e; idx.push(a, a + 1, a + 5, a + 1, a + 6, a + 5); }
        var geo = new T.BufferGeometry();
        geo.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
        geo.setAttribute('uv', new T.Float32BufferAttribute(uv, 2));
        geo.setIndex(idx); geo.computeVertexNormals(); geo.computeBoundingSphere();
        var F = (IB.THEME_DEFS.mossgarden.env.fog || {});
        var mat = new T.ShaderMaterial({
          uniforms: { uT: { value: 0 }, uDeep: { value: C('#2C8FC0') }, uShal: { value: C('#5FCBE6') }, uFoam: { value: C('#E9FBFF') }, uBank: { value: C('#3F5E3A') },
            uFog: { value: C(F.color || '#DDEFF2') }, uNear: { value: F.near || 55 }, uFar: { value: F.far || 240 } },
          vertexShader: 'varying vec2 vUv; varying float vD; void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vD = length(mv.xyz); gl_Position = projectionMatrix * mv; }',
          fragmentShader: 'uniform float uT; uniform vec3 uDeep; uniform vec3 uShal; uniform vec3 uFoam; uniform vec3 uBank; uniform vec3 uFog; uniform float uNear; uniform float uFar;\n' +
            'varying vec2 vUv; varying float vD;\n' +
            'void main(){ float a = abs(vUv.x); vec3 c = mix(uDeep, uShal, smoothstep(0.25, 0.85, a));\n' +
            '  float f = fract(vUv.y * 0.42 - uT * 0.55 + 0.35 * sin(vUv.x * 5.0 + vUv.y * 0.6) + 0.2 * sin(vUv.y * 1.7));\n' +
            '  if (f < 0.07 && a < 0.8) c = mix(c, uFoam, 0.75);\n' +
            '  if (a > 0.86) c = mix(uFoam, uBank, smoothstep(0.92, 0.99, a));\n' +
            '  float h = clamp((vD - uNear) / (uFar - uNear), 0.0, 1.0); gl_FragColor = vec4(mix(c, uFog, h * 0.9), 1.0); }'
        });
        var mesh = new T.Mesh(geo, mat); mesh.name = 'Stream'; level.root.add(mesh); streamMats.push(mat);
        // bank stones and reeds on both banks, clear of the bridges, stepping stones and the grotto / culvert
        var grid = Z.grid;
        for (k = 1; k + 1 < S.length; k++) {
          [-1, 1].forEach(function (sd) {
            var h1 = hash(k * 3 + sd, zi * 7 + 5);
            if (h1 < 0.3 || k % 2) return;
            var off = hw + 0.35 + hash(k, sd * 9) * 0.35, x = S[k].x + S[k].nx * sd * off, z = S[k].z + S[k].nz * sd * off;
            var c = Math.floor(x - Z.ox), r = Math.floor(z - Z.oz), ch = grid.at(c, r);
            if (ch !== '~' && ch !== '.' && ch !== ',') return;
            for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) if ('DiNI'.indexOf(grid.at(c + dc, r + dr)) >= 0) return;
            api.add(h1 < 0.78 ? (h1 < 0.54 ? 'BankStone_A' : 'BankStone_B') : 'Reeds', x, 0.0, z, hash(k, sd) * 6.28, 0.8 + hash(sd, k) * 0.5);
          });
        }
      });
    });
    // ---- keep-outs, then the woodland belt (instanced by kind and 30-degree sector) and the far trees
    var keep = [];
    zones.forEach(function (z) { keep.push([z.ox - 1.5, z.oz - 1.5, z.ox + z.w + 1.5, z.oz + z.h + 1.5]); });
    level.trails.forEach(function (t) { keep.push([t.x - 4.2, Math.min(t.z0, t.z1) - 1, t.x + 4.2, Math.max(t.z0, t.z1) + 1]); });
    if (level.hatch) keep.push([level.hatch.x - 6, level.hatch.z - 6, level.hatch.x + 6, (level.hatch.z0 || level.hatch.z) + 1]);
    function outDist(x, z) { var d = 1e9; keep.forEach(function (k) { d = Math.min(d, Math.max(k[0] - x, x - k[2], k[1] - z, z - k[3], 0)); }); return d; }
    var lists = { Backdrop_Tree_A: [], Backdrop_Tree_B: [], Backdrop_Tree_C: [] }, n = 0, gx, gz;
    for (gx = x0 - 90; gx <= x1 + 90; gx += 6.5) for (gz = zN - 90; gz <= z1 + 90; gz += 6.5) {
      n++;
      var x = gx + (hash(n, 3) - 0.5) * 5, z = gz + (hash(n, 5) - 0.5) * 5, od = outDist(x, z);
      if (od < 2.5) continue;
      var p = od < 14 ? 0.27 : od < 40 ? 0.07 : 0.025;
      if (hash(n, 17) > p) continue;
      var kind = hash(n, 9) < 0.3 ? 'Backdrop_Tree_B' : hash(n, 9) < 0.62 ? 'Backdrop_Tree_C' : 'Backdrop_Tree_A';
      lists[kind].push([x, -0.05, z, hash(n, 11) * 6.28, (od < 16 ? 0.85 : 1.05) + hash(n, 13) * 0.45]);
    }
    if (IB.Assets && IB.Assets.geo) {
      var TH = IB.THEME_DEFS.mossgarden, _m = new T.Matrix4(), _q = new T.Quaternion(), _p = new T.Vector3(), _s = new T.Vector3(), UP = new T.Vector3(0, 1, 0);
      Object.keys(lists).forEach(function (kind) {
        var full = IB.themePiece(TH, kind), geo = IB.Assets.get(full);
        if (!geo) return;
        var bySec = {};
        lists[kind].forEach(function (t) { var a = Math.floor((Math.atan2(t[2] - cz, t[0] - cx) + Math.PI) / (Math.PI / 6)); (bySec[a] || (bySec[a] = [])).push(t); });
        Object.keys(bySec).forEach(function (k) {
          var L = bySec[k], g = new T.BufferGeometry();
          g.setIndex(geo.index); Object.keys(geo.attributes).forEach(function (an) { g.setAttribute(an, geo.attributes[an]); });
          var im = new T.InstancedMesh(g, IB.Assets.material(full), L.length), bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
          L.forEach(function (t, i) {
            _q.setFromAxisAngle(UP, t[3]); _p.set(t[0], t[1], t[2]); _s.set(t[4], t[4], t[4]);
            im.setMatrixAt(i, _m.compose(_p, _q, _s));
            bx0 = Math.min(bx0, t[0]); bx1 = Math.max(bx1, t[0]); bz0 = Math.min(bz0, t[2]); bz1 = Math.max(bz1, t[2]);
          });
          g.boundingSphere = new T.Sphere(new T.Vector3((bx0 + bx1) / 2, 8, (bz0 + bz1) / 2), Math.hypot(bx1 - bx0, bz1 - bz0) / 2 + 16);
          im.name = 'Woods_' + kind + '_' + k;
          level.root.add(im);
        });
      });
    }
    // the house on its rise far beyond the north wall, a lawn sweeping up to it
    var mz = zN - 115;
    G.flat([[cx - 70, mz - 40], [cx + 70, mz - 40], [cx + 90, mz + 30], [cx - 90, mz + 30]], -0.02, C('#6EA850'));
    api.add('Backdrop_Manor', cx + 8, 0.0, mz, 0, 1.6);
    // ---- animation: the stream flows, lumenbell pods pulse in three phase groups
    api.tick(function (dt, t) {
      for (var i = 0; i < streamMats.length; i++) streamMats[i].uniforms.uT.value = t;
      var gl = level.glows || [];
      for (i = 0; i < gl.length; i++) {
        var E = gl[i];
        if (E.piece !== 'GlowPod_Glow') continue;
        var k = 0.72 + 0.28 * Math.sin(t * 1.6 + E.group * 2.1);
        if (E.mesh.material && E.mesh.material.color) {
          if (!E.mat) { E.mat = E.mesh.material.clone(); E.mesh.material = E.mat; }
          E.mat.color.setScalar(k);
        }
      }
    });
  }

  var PIECES = ['Wall2_A', 'Wall2_B', 'Wall2_C', 'Wall1', 'WallCorner', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B',
    'TrailWall_C', 'Hatch', 'Crate', 'Backdrop_Tree_A', 'Backdrop_Tree_B', 'Backdrop_Tree_C', 'Backdrop_Manor', 'BankStone_A',
    'BankStone_B', 'Reeds'];
  Object.keys(GLOW).forEach(function (k) { PIECES.push(GLOW[k].piece); });
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'mossgarden', name: 'Mosswood Gardens', family: 'kit-mossgarden', prefix: 'KIT_MOSSGARDEN_',
    palette: ['#3F914A', '#E8DEC8', '#F2384A', '#5ACCEA'],
    env: { sky: ['#3C9BE6', '#DDF1F4'], fog: { color: '#DDEFF2', near: 55, far: 240, tierScale: true }, sun: [0.5, 0.82, 0.28], clouds: true, ceiling: null },
    floor: { color: '#7CC35A', trail: '#D6CBB0', outside: '#5F9A47' },
    terrain: { height: terrainHeight, paint: paint, flat: '', ramp: [0, 1], low: '#7CC35A', high: '#86C85E', patch: '#74BC55', top: 3 },
    wall: { height: 3.6, roof: '#86B851', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.4, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall', 'TrailWall_B', 'TrailWall', 'TrailWall_C'], height: 2.6 },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: { build: buildGarden },
    budget: { prop: 2500, landmark: 8000, total: 52000 },
    garden: GARDEN, terrainHeight: terrainHeight, sampleCurve: resample,
    allPieces: function () { return PIECES.slice(); },
    levels: {
      mossgarden: {
        name: 'Mosswood Gardens',
        intro: 'Robots have overrun Mosswood Gardens. Clear the formal garden round the great fountain, then push through the wild garden to the ruined folly. Hedges stop bullets; the terrace and the mound give you high ground.',
        zones: [
          // the formal garden: fountain, parterres, terrace, glasshouse
          { map: 'mossgarden_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 5]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['drone', 8], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 19], ['gunner', 10], ['bomber', 2], ['soldier', 7], ['blader', 4]],
            [['crawler', 14], ['gunner', 9], ['drone', 6], ['soldier', 6], ['blader', 3]]] },
          // the wild garden: stream, bridges, maze, folly on the mound
          { map: 'mossgarden_2', waves: [
            [['crawler', 16], ['gunner', 10], ['drone', 5], ['soldier', 6]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 5], ['blader', 4]],
            [['crawler', 14], ['drone', 7], ['gunner', 9], ['soldier', 4], ['blader', 3]],
            [['crawler', 16], ['gunner', 9], ['bomber', 2], ['soldier', 4], ['blader', 4], ['drone', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
