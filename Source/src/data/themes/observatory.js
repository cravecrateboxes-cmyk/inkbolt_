/* Theme: Vesper Peak Observatory (kit-observatory) -- the last campaign map: a mountaintop observatory above a sea of
   clouds at late dusk, the sky going from the last orange glow in the west to stars overhead, Vesper (the evening star)
   low in the west. Robots hold the summit. Two zones; player travel is north.
   1 The summit compound (72 x 70), snow-dusted rock (theme.terrain: knolls of bare rock, the cleared road and plaza):
     the funicular's upper station closes the south (VESPER SUMMIT RAILWAY, two wings round the entrance court), the
     dome annex closes the north (two wings round the porch with the exit gate; the Great Dome rises behind it), steel
     parapets over the cliffs on the west and east. The radio mast array on its concrete pad (1.5 m, steps up from the
     south) in the north-west; the fenced antenna field in the west: two 10 m dish antennas on their pedestals, VSAT
     dishes, equipment shelters, the overhead cable bridge to the ground station; the ground station building in the
     middle (VESPERLINK) with its roof deck at 3 m (a stair from the south) and the steel gantry east over the road to
     the east terrace (3 m, two concrete stairs): the Halden Dome of 1931 (the landmark: stone drum, copper dome, the
     slit open, the old refractor looking out), the weather mast, the all-sky camera, visitor telescopes, benches; the
     plaza with the summit cairn, the panorama boards at the parapets, the snowcat, the power yard (fuel tanks, the
     generator house), deliveries by the porch, rock outcrops and boulders.
   2 Inside the Great Dome (72 x 68): the dome hall (48 x 48 under the 24 m dome, its slit open to the south) with the
     Vesper 12 m telescope on its fork mount (the landmark), the catwalk ring round it at 4.8 m (two stairs, a bridge
     from the east gallery, which has its own stair), consoles, crates, carts and gas bottles on the floor; the west
     wing: the control room (video wall, operator desks, racks), the spectrograph lab (two spectrographs, the optical
     table, lab benches, star charts), the plate archive (cabinets of glass plates, the light table); the east wing,
     glazed floor to ceiling over the clouds: the star deck (binocular viewers, a viewing deck at 4.8 m along the
     glass) and the cloud lounge (sofas, the COMET CAFE bar); the service hall in the north (the mirror coating chamber,
     a mirror segment on its cart, the scissor lift, the exit gate), the lobby in the south (reception, the telescope
     model, the meteorite, lockers).
   The vista is level-wide (backdrop.build, never switches between zones): the summit's snowy rock falling away in
   cliffs round the compound, the sea of clouds 150 m below drifting slowly, snowy peaks rising out of it, the dusk band
   round the horizon (warm in the west), the stars and Vesper.
   Built by blender/fam_kit_observatory.py (ob_*.py); zone layers by tools/observatory_zones.py.
   Engine: zone plan option `terrain: false` (zones.js buildLevel: an indoor zone of a terrain theme keeps its floor).

   A zone file has the floor plan and layers: "@layer 0.01" facade signs (zone 1), "@layer 0.012" floor finishes
   (zone 2), "@layer 0.02" / "@layer 0.03" (data: wall art codes on the S / E and N / W face of wall cells),
   "@layer 0.04" (data, zone 1: ground codes), "@layer 0.05" (data: the finish scheme each open cell sees on its
   walls), "@layer 1.5" the mast pad, "@layer 3" the terrace, the gantry and what stands on them (zone 1);
   "@layer 4.2" / "5" / "8" / "9" ceilings, "@layer 4.8" the ring, the gallery, the bridge and the star deck,
   "@layer 10" the dome (zone 2). Marker cells (never built): ` under the terrace / the pad, : under a ring column.
   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled, front = +Z unless turned):
     # wall (10 m; the chooser faces every open side in the scheme of the cell it looks onto, art overlays on top)
     D W doorway [2,1] / service doorway [4,1] (wall.passage: solid above 3 m; the frame in the wall line)
     zone 1: { parapet (runs)   f security fence (links)   r rail on the pad / the terrace (links)   d the mast pad
       (1.5 m deck)   U the terrace (3 m deck)   m steel deck (the gantry; zone 2: the ring's bridge, the gallery, the
       star deck)   ' its rail (links)   B K 10 m dish antenna [10,10] (two pointings)   v VSAT dish [2,2]
       M lattice radio mast [3,3]   H equipment shelter [6,4]   C the ground station [10,6] (roof deck at 3 m)
       O the Halden Dome [12,12] (landmark)   X snowcat [3,5]   F fuel tank [2,5]   Z generator house [4,3]
       Q rock outcrop [2,2]   o boulder   i j panorama board [2,1] (at the east / west parapet)   = bench [2,1]
       u steel stair to 3 m [2,6] (rising north)   T Y concrete stair to 3 m [4,6] (rising north / east)
       J steps to 1.5 m [3,3] (rising north)   I gantry column   L lamp post   q summit cairn   ! weather mast
       A all-sky camera   % visitor telescope   c flight cases   y gas bottles   k cable drum   x overhead cable bridge
       (runs)   R equipment cabinet   1 2 facade signs [12,1] (station / annex)
     zone 2: $ the Vesper 12 m telescope [12,12] (landmark)   @ the catwalk ring [26,26] (4.8 m)   N n e steel stair
       to 4.8 m [2,10] (rising north / south / east)   | deck column   * the dome [48,48]   ( the dome floor rings
       [48,48]   ) stone floor [2,2]   ~ carpet [2,2]   - ceiling tiles [2,2]   _ half tiles [2,1]
       s spectrograph [4,2]   , optical table [3,2]   b lab bench [3,1]   p plate cabinet [2,1]   g server racks [2,1]
       z console desk [2,1]   w operator desk [3,1]   V video wall [6,1]   + chair   t plate table [3,2]
       0 instrument crate [2,2]   3 reception [4,2]   4 telescope model [2,2]   5 the meteorite [2,2]   l lockers [2,1]
       ; bench [2,1]   6 planter   9 binocular viewer (looking east)   [ sofa [3,1] (facing east)   ] low table [2,1]
       & cafe bar [4,1]   > mirror coating chamber [6,4]   / mirror cart [4,4]   ? scissor lift [2,3]   ^ tool cabinet
   Wall art codes (data, on wall cells): w window pair (station)   W upper window (annex)   d staff door   v vent
     l wall lamp   c star chart (pairs)   p poster   b whiteboard   x exit point   k clock   g full-height glazing
   Ground codes (0.04): g the road   p the plaza paving   r rough rock (knolls)
   Schemes (0.05): S station  A annex  H dome hall  L lab  C control room  B lobby  V viewing rooms  M service hall */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, PI = Math.PI;
  function T3() { return (typeof window !== 'undefined' && window.THREE) || globalThis.THREE; }

  // ---------------------------------------------------------------- walls
  var DOORS = 'DW', WALLISH = '#GE' + DOORS;
  var SIDES = ['S', 'N', 'E', 'W'];
  var STEP = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  var FYAW = { S: 0, N: PI, E: R90, W: -R90 };
  var RIGHT = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };   // the viewer's right along a face
  var SCHEME = { S: 'FS', A: 'FA', H: 'FH', L: 'FL', C: 'FC', B: 'FB', V: 'FV', M: 'FM' };
  function wl(g, c, r) { return WALLISH.indexOf(g.at(c, r)) >= 0; }
  function data(g, y) {
    var key = '_ob' + y;
    if (g[key] === undefined) { g[key] = null; (g.layers || []).forEach(function (l) { if (Math.abs(l.y - y) < 1e-4) g[key] = l; }); }
    return g[key];
  }
  function codeAt(g, c, r, side) { var L = data(g, side === 'S' || side === 'E' ? 0.02 : 0.03); return L ? L.at(c, r) : '.'; }
  function schemeAt(g, c, r) { var L = data(g, 0.05); return L ? L.at(c, r) : '.'; }
  function gateCell(g, c, r) {   // the gate frame covers the gate and one wall cell either side of it
    if (r !== 0 && r !== g.h - 1) return false;
    var ch = r === 0 ? 'G' : 'E';
    for (var dc = -1; dc <= 1; dc++) if (g.at(c + dc, r) === ch) return true;
    return false;
  }
  function runOf(g, c, r, side, code) {
    var R = RIGHT[side], k = 0;
    while (k < 40 && codeAt(g, c - R[0] * (k + 1), r - R[1] * (k + 1), side) === code && wl(g, c - R[0] * (k + 1), r - R[1] * (k + 1))) k++;
    var m = 0; while (m < 40 && codeAt(g, c + R[0] * (m + 1), r + R[1] * (m + 1), side) === code && wl(g, c + R[0] * (m + 1), r + R[1] * (m + 1))) m++;
    return [k, k + 1 + m];
  }
  function artPiece(g, c, r, side, code, hash) {
    switch (code) {
      case 'w': return 'A_Win';
      case 'W': return 'A_WinUp';
      case 'd': return 'A_Door';
      case 'v': return 'A_Vent';
      case 'l': return 'A_Lamp';
      case 'c': return runOf(g, c, r, side, code)[0] % 2 ? 'A_ChartR' : 'A_ChartL';
      case 'p': return 'A_Poster' + (1 + Math.floor(hash(c * 7 + 3, r * 11 + 5) * 3) % 3);
      case 'b': return 'A_Board';
      case 'x': return 'A_Exit';
      case 'k': return 'A_Clock';
      case 'g': return runOf(g, c, r, side, code)[0] % 2 ? 'TG_N' : 'TG';   // a mullion every 2 m
    }
    return null;
  }
  /* One finish face per open side of a wall cell, turned to that side, in the scheme of the cell it looks onto (a
     doorway cell gets the upper part only: its frame draws the rest); an art code stacks its overlay on it; the glazing
     is a through piece (the whole cell). */
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    if (face === 'none' || gateCell(g, c, r)) return null;
    var door = DOORS.indexOf(g.at(c, r)) >= 0;
    var open = SIDES.filter(function (s) { return !wl(g, c + STEP[s][0], r + STEP[s][1]); });
    if (!open.length) return null;
    var yaw = face === 'corner' ? (!horiz && (wl(g, c, r - 1) || wl(g, c, r + 1)) ? R90 : 0) : FYAW[face];
    var out = [];
    for (var i = 0; i < open.length; i++) {
      var s = open[i], t = FYAW[s] - yaw;
      var code = (face === 'corner' || door) ? '.' : codeAt(g, c, r, s), art = code !== '.' ? artPiece(g, c, r, s, code, hash) : null;
      if (art === 'TG' || art === 'TG_N') return [{ piece: art, turn: t }];
      var plain = (SCHEME[schemeAt(g, c + STEP[s][0], r + STEP[s][1])] || 'FH') + (door ? '_U' : '');
      out.push(t ? { piece: plain, turn: t } : plain);
      if (art) out.push(t ? { piece: art, turn: t } : art);
    }
    return out;
  }

  // ---------------------------------------------------------------- terrain (zone 1): snow, bare rock knolls, the road
  var GROUND = null;
  function groundCode(c, r) {
    if (GROUND === null) {
      GROUND = false;
      var txt = IB.ZONE_MAPS && IB.ZONE_MAPS.observatory_1;
      if (txt && IB.Zones && IB.Zones.parse) { var g = IB.Zones.parse(txt); g.layers.forEach(function (L) { if (Math.abs(L.y - 0.04) < 1e-4) GROUND = L; }); }
    }
    return GROUND ? GROUND.at(c, r) : '.';
  }
  function terrainHeight(c, r, zi) {   // cell corners; rough rock only where all four cells round the corner are rough
    if (zi !== 0) return 0;
    var n = 0;
    for (var dr = -1; dr <= 0; dr++) for (var dc = -1; dc <= 0; dc++) if (groundCode(c + dc, r + dr) === 'r') n++;
    if (!n) return 0;
    var b = 0.55 + 0.35 * Math.sin(c * 0.45 + r * 0.21) + 0.3 * Math.sin(c * 0.19 - r * 0.52 + 1.7);
    return Math.max(0, b) * n / 4 * 1.5;
  }
  function terrainPaint(c, r, zi, grid) {
    if (zi !== 0) return null;
    var L = data(grid, 0.04), k = L ? L.at(Math.min(c, grid.w - 1), Math.min(r, grid.h - 1)) : '.';
    if (k === 'g') return ['#77737C', 0.85];
    if (k === 'p') return ['#B7B3B2', 0.8];
    if (k === 'r') return ['#8C8794', 0.25];
    return null;
  }

  // ---------------------------------------------------------------- symbols
  function pf(size, pieces, extra) { return Object.assign({ size: size, pieces: pieces, kind: 'cover' }, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, rotate: rot, kind: 'cover' }, extra || {}); }
  var FLOOR = { collide: false, face: 0 };
  var SYMBOLS = {
    // ---- doorways (wall.passage cells: the head collides, the frame does not)
    'D': pf([2, 1], ['Door2'], { orient: 'span', kind: 'wall', collide: false }),
    'W': pf([4, 1], ['Door4'], { orient: 'span', kind: 'wall', collide: false }),
    // ---- zone 1: edges, decks, rails
    '{': { pieces: ['Par_A', 'Par_A', 'Par_B'], rotate: 'run', kind: 'wall' },
    'f': { pieces: ['FenceHalf'], full: 'FenceFull', links: 'f', post: 'FencePost', kind: 'wall' },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: "r'", post: 'RailPost', kind: 'wall' },
    "'": { pieces: ['RailHalf'], full: 'RailFull', links: "r'", post: 'RailPost', kind: 'wall' },
    'd': { deck: { thick: 1.5, color: '#CDC9C2', edge: '#9C988F', under: '#8E8A85', with: 'r' } },
    'U': { deck: { thick: 3.0, color: '#D2CEC7', edge: '#A39F97', under: '#8E8A85', with: 'rO!A%aLc=' } },   // the deck runs on under the terrace props (the old dome stood over a hole)
    'm': { deck: { thick: 0.3, color: '#6B7480', edge: '#3A3D46', under: '#4A5059', with: "'" } },
    // ---- zone 1: the antenna field, the masts, the buildings
    'B': pf([10, 10], ['Dish_A'], { face: 0 }),
    'K': pf([10, 10], ['Dish_B'], { face: 0 }),
    'v': pf([2, 2], ['Vsat_A', 'Vsat_B'], { face: 0 }),
    'M': pf([3, 3], ['Mast'], { face: 0 }),
    'H': pf([6, 4], ['Shelter'], { flip: true }),
    'C': pf([10, 6], ['GroundStation'], { face: 0, kind: 'step' }),
    'O': pf([12, 12], ['Landmark_OldDome'], { face: 0 }),
    'X': pf([3, 5], ['Snowcat'], { flip: true }),
    'F': pf([2, 5], ['FuelTank'], { flip: true }),
    'Z': pf([4, 3], ['GenHouse'], { face: 0 }),
    'Q': pf([2, 2], ['Outcrop'], { flip: true }),
    'o': one(['Rock_A', 'Rock_B'], 'random90'),
    'i': pf([2, 1], ['Panorama'], { face: -R90 }),
    'j': pf([2, 1], ['Panorama'], { face: R90 }),
    '=': pf([2, 1], ['Bench'], { flip: true }),
    'u': pf([2, 6], ['Stair30'], { face: 0, kind: 'step' }),
    'T': pf([4, 6], ['StairC'], { face: 0, kind: 'step' }),
    'Y': pf([4, 6], ['StairC'], { face: -R90, kind: 'step' }),
    'J': pf([3, 3], ['Steps15'], { face: 0, kind: 'step' }),
    'I': one(['Post30'], 0),
    'L': one(['Lamp'], 'edge'),
    'q': one(['Cairn'], 0),
    '!': one(['WeatherMast'], 0),
    'A': one(['SkyCam'], 0),
    '%': one(['VisitorScope'], 'random90'),
    'c': one(['Case_A', 'Case_B', 'Case_C'], 'random90'),
    'y': one(['Cylinders'], 'edge'),
    'k': one(['Drum'], 'random90'),
    'x': { pieces: ['Cable_B', 'Cable_A'], rotate: 'run', alternate: true, kind: 'cover' },
    'R': one(['Cabinet'], 'edge'),
    '1': pf([12, 1], ['Sign_Station'], { face: PI, collide: false }),
    '2': pf([12, 1], ['Sign_Annex'], { face: 0, collide: false }),
    // ---- zone 2: the dome hall
    '$': pf([12, 12], ['Landmark_Telescope'], { face: 0 }),
    '@': pf([26, 26], ['Landmark_Ring'], { face: 0, kind: 'step' }),
    'N': pf([2, 10], ['Stair48'], { face: 0, kind: 'step' }),
    'n': pf([2, 10], ['Stair48'], { face: PI, kind: 'step' }),
    'e': pf([2, 10], ['Stair48'], { face: -R90, kind: 'step' }),
    '|': one(['Post48'], 0),
    '*': pf([48, 48], ['Landmark_Dome'], { face: 0, collide: false }),
    '(': pf([48, 48], ['F_DomeFloor'], FLOOR), ')': pf([2, 2], ['F_Stone'], FLOOR), '~': pf([2, 2], ['F_Carpet'], FLOOR),
    '-': pf([2, 2], ['C_Tile', 'C_Tile', 'C_Light'], { face: 0, kind: 'wall' }),
    '_': pf([2, 1], ['C_Tile1'], { face: 0, kind: 'wall' }),
    // ---- zone 2: labs, control room
    's': pf([4, 2], ['Spectro_A', 'Spectro_B'], { flip: true }),
    ',': pf([3, 2], ['OpticTable'], { flip: true }),
    'b': pf([3, 1], ['LabBench'], { orient: 'wall' }),
    'p': pf([2, 1], ['PlateCab'], { orient: 'wall' }),
    'g': pf([2, 1], ['Rack'], { orient: 'wall' }),
    'z': pf([2, 1], ['Console'], { orient: 'wall' }),
    'w': pf([3, 1], ['OpsDesk'], { face: 0 }),
    'V': pf([6, 1], ['VideoWall'], { orient: 'wall' }),
    '+': one(['Chair'], PI),
    't': pf([3, 2], ['PlateTable'], { flip: true }),
    '0': pf([2, 2], ['Crate2'], { flip: true }),
    // ---- zone 2: lobby, viewing rooms, service hall
    '3': pf([4, 2], ['Reception'], { face: 0 }),
    '4': pf([2, 2], ['ScopeModel'], { face: 0 }),
    '5': pf([2, 2], ['Meteorite'], { face: 0 }),
    'l': pf([2, 1], ['Lockers'], { orient: 'wall' }),
    ';': pf([2, 1], ['BenchIn'], { flip: true }),
    '6': one(['Plant'], 'random90'),
    '9': one(['Viewer'], -R90),
    '[': pf([3, 1], ['Sofa'], { face: R90 }),
    ']': pf([2, 1], ['LowTable'], { face: R90 }),
    '&': pf([4, 1], ['CafeBar'], { orient: 'wall' }),
    '>': pf([6, 4], ['Coater'], { face: 0 }),
    '/': pf([4, 4], ['MirrorCart'], { face: 0 }),
    '?': pf([2, 3], ['Lift'], { face: 0 }),
    '^': one(['ToolCab'], 'edge')
  };

  // glow companions (zones.js theme.glow): lamps, screens, beacons drawn unlit; glass additive; blinked by the vista tick
  var ADD = 'add';
  var GLOW = {
    Dish_A: { piece: 'Dish_A_Glow', groups: 2 }, Dish_B: { piece: 'Dish_B_Glow', groups: 2 }, Mast: { piece: 'Mast_Glow', groups: 3 },
    GroundStation: { piece: 'GroundStation_Glow' }, Landmark_OldDome: { piece: 'Landmark_OldDome_Glow' },
    Snowcat: { piece: 'Snowcat_Glow' }, Lamp: { piece: 'Lamp_Glow' }, A_Lamp: { piece: 'A_Lamp_Glow' }, A_Exit: { piece: 'A_Exit_Glow' },
    TG: { piece: 'TG_Glow', blend: ADD }, TG_N: { piece: 'TG_N_Glow', blend: ADD }, Door2: { piece: 'Door2_Glow' }, GateFrame: { piece: 'GateFrame_Glow' },
    C_Light: { piece: 'C_Light_Glow' }, Rack: { piece: 'Rack_Glow', groups: 3 }, Console: { piece: 'Console_Glow', groups: 2 },
    OpsDesk: { piece: 'OpsDesk_Glow', groups: 2 }, VideoWall: { piece: 'VideoWall_Glow' }, LabBench: { piece: 'LabBench_Glow' },
    OpticTable: { piece: 'OpticTable_Glow' }, PlateTable: { piece: 'PlateTable_Glow' }, Reception: { piece: 'Reception_Glow' },
    ScopeModel: { piece: 'ScopeModel_Glow', blend: ADD }, Landmark_Telescope: { piece: 'Landmark_Telescope_Glow' }
  };

  // ======================================================================================== the vista (backdrop.build)
  var CLOUD = -150;   // the sea of clouds below the summit
  function noise(x, z) { return Math.sin(x * 0.013 + z * 0.007) * 0.6 + Math.sin(z * 0.021 - x * 0.009 + 1.3) * 0.4 + Math.sin(x * 0.041 + z * 0.033 + 2.1) * 0.22; }
  /* a faceted, flat-shaded mesh with an optional ink hull (inverted shell along smooth normals) into an IB.Geo */
  function Mesher(g, ink) { this.g = g; this.ink = ink; this.sm = {}; this.hull = []; }
  Mesher.prototype.tri = function (a, b, c, col) {
    var ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, L = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    nx /= L; ny /= L; nz /= L;
    var g = this.g;
    g.idx.push(g._vert(a[0], a[1], a[2], nx, ny, nz, col), g._vert(b[0], b[1], b[2], nx, ny, nz, col), g._vert(c[0], c[1], c[2], nx, ny, nz, col));
    if (!this.ink) return;
    var self = this;
    this.hull.push([a, b, c].map(function (p) {
      var k = Math.round(p[0] * 10) + ',' + Math.round(p[1] * 10) + ',' + Math.round(p[2] * 10), s = self.sm[k];
      if (!s) s = self.sm[k] = { p: p, n: [0, 0, 0] };
      s.n[0] += nx * L; s.n[1] += ny * L; s.n[2] += nz * L;
      return k;
    }));
  };
  Mesher.prototype.finish = function (inkCol) {
    if (!this.ink) return;
    var g = this.g, sm = this.sm, idx = {};
    Object.keys(sm).forEach(function (k) {
      var s = sm[k], n = s.n, L = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) || 1;
      idx[k] = g._vert(s.p[0], s.p[1], s.p[2], 0, 1, 0, inkCol, n[0] / L, n[1] / L, n[2] / L);
    });
    this.hull.forEach(function (t) { g.idx.push(idx[t[0]], idx[t[2]], idx[t[1]]); });
  };

  function buildVista(level, api) {
    var THREE = T3(), hash = api.hash, g = api.geo;
    var Z1 = level.zones[0], Z2 = level.zones[level.zones.length - 1];
    var x0 = Math.min(Z1.ox, Z2.ox), x1 = Math.max(Z1.ox + Z1.w, Z2.ox + Z2.w), z0 = Z2.oz - 32, z1 = Z1.oz + Z1.h;
    var cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
    function hx(h) { return new THREE.Color(h); }
    var C = { snow: hx('#E9ECF4'), snowS: hx('#C8CCDB'), rock: hx('#7D7884'), rockD: hx('#5C5866'), rockL: hx('#A29DA8'), ink: hx('#15121C') };
    // ---- the summit: snowy rock round the compound (just under the floor at its edge), falling away in cliffs to the clouds
    function dOut(x, z) {   // metres outside the level's footprint
      var dx = Math.max(x0 - x, 0, x - x1), dz = Math.max(z0 - z, 0, z - z1);
      return Math.sqrt(dx * dx + dz * dz);
    }
    function Hs(x, z) {
      var d = dOut(x, z);
      if (d <= 0) return -0.25;
      var n = noise(x * 3, z * 3), k = Math.min(1, d / 25);
      var h = -0.25 - d * 0.06 - (d > 6 ? (d - 6) * (d - 6) * 0.03 : 0) + n * k * k * 4;
      return Math.max(CLOUD - 25, Math.min(h, -0.25 - d * 0.02));
    }
    var xs = [], zs = [], v;
    for (v = x0 - 260; v <= x1 + 260; v += (v > x0 - 30 && v < x1 + 30) ? 6 : 14) xs.push(v);
    for (v = z0 - 260; v <= z1 + 260; v += (v > z0 - 30 && v < z1 + 30) ? 6 : 14) zs.push(v);
    [x0, x1].forEach(function (q) { if (xs.indexOf(q) < 0) xs.push(q); }); [z0, z1].forEach(function (q) { if (zs.indexOf(q) < 0) zs.push(q); });
    xs.sort(function (a, b) { return a - b; }); zs.sort(function (a, b) { return a - b; });
    var M = new Mesher(g, true), V = [];
    for (var j = 0; j < zs.length; j++) { var row = []; for (var i = 0; i < xs.length; i++) row.push([xs[i], Hs(xs[i], zs[j]), zs[j]]); V.push(row); }
    for (j = 0; j + 1 < zs.length; j++) for (var i2 = 0; i2 + 1 < xs.length; i2++) {
      var mx = (xs[i2] + xs[i2 + 1]) / 2, mz = (zs[j] + zs[j + 1]) / 2;
      if (dOut(mx, mz) <= 0) continue;   // under the zones and the trails
      var a = V[j][i2], b = V[j][i2 + 1], c = V[j + 1][i2 + 1], d = V[j + 1][i2], k = hash(i2 * 7 + 3, j * 13 + 5);
      [[a, d, c], [a, c, b]].forEach(function (t, ti) {
        var ux = t[1][0] - t[0][0], uy = t[1][1] - t[0][1], uz = t[1][2] - t[0][2], vx = t[2][0] - t[0][0], vy = t[2][1] - t[0][1], vz = t[2][2] - t[0][2];
        var ny = uz * vx - ux * vz, L = Math.sqrt(Math.pow(uy * vz - uz * vy, 2) + ny * ny + Math.pow(ux * vy - uy * vx, 2)) || 1, s = ny / L;
        var kk = (k + ti * 0.37) % 1;
        M.tri(t[0], t[1], t[2], s > 0.8 ? (kk > 0.3 ? C.snow : C.snowS) : s > 0.55 ? (kk > 0.5 ? C.snowS : C.rockL) : kk > 0.5 ? C.rock : C.rockD);
      });
    }
    // ---- peaks rising out of the clouds (faceted cones with ridges, snow above the shoulder)
    for (var p = 0; p < 15; p++) {
      var az = hash(p, 31) * Math.PI * 2, dist = 380 + hash(p, 33) * 1500, ht = CLOUD + 40 + hash(p, 35) * (dist < 700 ? 120 : 190);
      var px = cx + Math.cos(az) * dist, pz = cz + Math.sin(az) * dist, R = (ht - CLOUD) * (1.1 + hash(p, 37) * 0.6), nR = 7 + Math.floor(hash(p, 39) * 3);
      var top = [px + (hash(p, 41) - 0.5) * R * 0.3, ht, pz + (hash(p, 43) - 0.5) * R * 0.3], mid = [], base = [];
      for (var q = 0; q < nR; q++) {
        var aa = q / nR * Math.PI * 2 + hash(p, 45 + q) * 0.4, rr = R * (0.75 + hash(p, 61 + q) * 0.5);
        base.push([px + Math.cos(aa) * rr, CLOUD - 30, pz + Math.sin(aa) * rr]);
        var rm = rr * (0.42 + hash(p, 81 + q) * 0.2), hm = CLOUD + (ht - CLOUD) * (0.5 + hash(p, 91 + q) * 0.15);
        mid.push([px + Math.cos(aa + 0.2) * rm, hm, pz + Math.sin(aa + 0.2) * rm]);
      }
      for (q = 0; q < nR; q++) {
        var q2 = (q + 1) % nR, sn = hash(p, 101 + q);
        M.tri(top, mid[q2], mid[q], sn > 0.25 ? C.snow : C.snowS);
        M.tri(mid[q], mid[q2], base[q2], sn > 0.6 ? C.rockL : C.rock);
        M.tri(mid[q], base[q2], base[q], sn > 0.5 ? C.rockD : C.rock);
      }
    }
    M.finish(C.ink);
    // ---- the sea of clouds: one wide low-poly field of soft swells, lilac in shade, rosy toward the last light
    var cg = new IB.Geo(), cm = new Mesher(cg, false), NR = 22, NA = 48, sunAz = Math.atan2(0.45, -0.75);
    var ring = [];
    for (var ri = 0; ri <= NR; ri++) {
      var rad = 40 + Math.pow(ri / NR, 1.6) * 2500, rowc = [];
      for (var ai = 0; ai < NA; ai++) {
        var an = ai / NA * Math.PI * 2 + (ri % 2) * Math.PI / NA, X = Math.cos(an) * rad, Zc = Math.sin(an) * rad;
        rowc.push([cx + X, CLOUD + 14 * Math.sin(X * 0.011 + Zc * 0.007) + 10 * Math.sin(Zc * 0.019 - X * 0.004 + 2) + 6 * Math.sin(X * 0.031 + Zc * 0.023 + 1), cz + Zc]);
      }
      ring.push(rowc);
    }
    var cTop = hx('#F5F2FB'), cMid = hx('#D3CBE6'), cSh = hx('#9C8FC0'), cRose = hx('#F7C9C2'), tmp = new THREE.Color();
    function ccol(pt, ny) {
      var a = Math.atan2(pt[2] - cz, pt[0] - cx), w = Math.max(0, Math.cos(a - sunAz));
      tmp.copy(ny > 0.995 ? cTop : ny > 0.97 ? cMid : cSh).lerp(cRose, w * w * 0.6);
      return tmp.clone();
    }
    for (ri = 0; ri < NR; ri++) for (ai = 0; ai < NA; ai++) {
      var A = ring[ri][ai], Bq = ring[ri][(ai + 1) % NA], Cq = ring[ri + 1][(ai + 1) % NA], Dq = ring[ri + 1][ai];
      [[A, Dq, Cq], [A, Cq, Bq]].forEach(function (t) {
        var ux = t[1][0] - t[0][0], uy = t[1][1] - t[0][1], uz = t[1][2] - t[0][2], vx = t[2][0] - t[0][0], vy = t[2][1] - t[0][1], vz = t[2][2] - t[0][2];
        var ny = uz * vx - ux * vz, L = Math.sqrt(Math.pow(uy * vz - uz * vy, 2) + ny * ny + Math.pow(ux * vy - uy * vx, 2)) || 1;
        if (ny < 0) { cm.tri(t[0], t[2], t[1], ccol(t[0], -ny / L)); } else cm.tri(t[0], t[1], t[2], ccol(t[0], ny / L));
      });
    }
    var cloudMesh = new THREE.Mesh(cg.build(), IB.Zones.mat);
    cloudMesh.name = 'CloudSea';
    var cloudPivot = new THREE.Group(); cloudPivot.position.set(cx, 0, cz); cloudMesh.position.set(-cx, 0, -cz);
    cloudPivot.add(cloudMesh); level.root.add(cloudPivot);

    // ---- the dusk sky: a dome round the camera like the engine's sky sphere (unlit, drawn first, behind everything) from under the horizon to the zenith -- warm low in the west,
    // mauve, violet, then indigo going to night overhead
    var STOPS = [[-12, '#B391A8'], [0, '#C99AA6'], [3, '#D7A09C'], [7, '#B08AA8'], [13, '#7A6FA8'], [22, '#464C8E'],
      [38, '#262D66'], [60, '#171D47'], [90, '#0F1433']];
    var band = new IB.Geo(), RB = 290, NS = 48, glowC = hx('#FFB070'), tc = new THREE.Color(), sunDir = new THREE.Vector3(-0.75, 0, 0.45).normalize();
    for (var bi = 0; bi < NS; bi++) for (var bj = 0; bj + 1 < STOPS.length; bj++) {
      var qd = [[bi, bj], [bi + 1, bj], [bi + 1, bj + 1], [bi, bj + 1]].map(function (P2) {
        var a2 = P2[0] / NS * Math.PI * 2, st = STOPS[P2[1]], el = st[0] * Math.PI / 180, dx2 = Math.cos(a2), dz2 = Math.sin(a2);
        var sd = Math.max(0, dx2 * sunDir.x + dz2 * sunDir.z), w = Math.pow(sd, 5) * (st[0] < 10 ? 0.75 : st[0] < 25 ? 0.25 : 0);
        tc.copy(hx(st[1])).lerp(glowC, w);
        return band._vert(dx2 * Math.cos(el) * RB, Math.sin(el) * RB, dz2 * Math.cos(el) * RB, -dx2, 0, -dz2, tc.clone());
      });
      band.idx.push(qd[0], qd[2], qd[1], qd[0], qd[3], qd[2]);
    }
    var sky = new THREE.Group(); sky.name = 'DuskSky';
    var bandM = new THREE.Mesh(band.build(), new THREE.MeshBasicMaterial({ vertexColors: true, fog: false, depthWrite: false, side: THREE.DoubleSide }));
    bandM.renderOrder = -9; bandM.frustumCulled = false; sky.add(bandM);
    // ---- the stars (more and brighter with height) and Vesper, the evening star, low in the west
    var N = 700, pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    for (var si = 0; si < N; si++) {
      var u = hash(si, 201), vv = hash(si, 203), el = Math.asin(0.16 + 0.84 * Math.pow(vv, 0.7)), azs = u * Math.PI * 2;
      var R0 = 270, sx = Math.cos(el) * Math.cos(azs), sy = Math.sin(el), sz = Math.cos(el) * Math.sin(azs);
      var bright = Math.min(1, 0.25 + (sy - 0.16) * 1.6) * (0.55 + 0.45 * hash(si, 207)), warm = hash(si, 209);
      pos[si * 3] = sx * R0; pos[si * 3 + 1] = sy * R0; pos[si * 3 + 2] = sz * R0;
      col[si * 3] = bright * (0.9 + 0.1 * warm); col[si * 3 + 1] = bright * 0.93; col[si * 3 + 2] = bright * (1.0 - 0.1 * warm);
    }
    var sgeo = new THREE.BufferGeometry();
    sgeo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); sgeo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    // additive: a faint star low over the bright band adds a little light instead of showing as a dark speck
    var stars = new THREE.Points(sgeo, new THREE.PointsMaterial({ size: 2.0, sizeAttenuation: false, vertexColors: true, fog: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending }));
    stars.renderOrder = -8; stars.frustumCulled = false; stars.name = 'Stars'; sky.add(stars);
    var vd = new THREE.Vector3(-0.86, 0.17, 0.48).normalize();
    [[3.6, '#FFC48A', 0.22], [1.7, '#FFE6C2', 0.5], [0.7, '#FFFBEF', 1]].forEach(function (D, di) {
      var m = new THREE.Mesh(new THREE.CircleGeometry(D[0], 20), new THREE.MeshBasicMaterial({ color: D[1], fog: false, depthWrite: false, transparent: D[2] < 1, opacity: D[2], blending: D[2] < 1 ? THREE.AdditiveBlending : THREE.NormalBlending }));
      m.position.copy(vd.clone().multiplyScalar(260 - di * 0.5)); m.lookAt(0, 0, 0); m.renderOrder = -7; m.frustumCulled = false; m.name = 'Vesper';
      sky.add(m);
    });
    level.root.add(sky);

    // ---- animation: the sky follows the camera, the clouds drift, beacons and racks blink
    api.tick(function (dt, t) {
      var cam = IB.Render && IB.Render.camera;
      if (cam) sky.position.copy(cam.position);
      cloudPivot.rotation.y = t * 0.0025;
      (level.glows || []).forEach(function (G) {
        if (G.piece === 'Mast_Glow' || G.piece === 'Dish_A_Glow' || G.piece === 'Dish_B_Glow') G.mesh.visible = ((t * 0.8 + G.group * 0.45) % 1.5) < 0.8;
        else if (G.piece === 'Rack_Glow') G.mesh.visible = ((t * 2.3 + G.group * 0.7) % 1) < 0.7;
        else if (G.piece === 'Console_Glow' || G.piece === 'OpsDesk_Glow') G.mesh.visible = ((t * 0.5 + G.group * 1.7) % 5) > 0.12;
      });
    });
  }

  // ---------------------------------------------------------------- pieces
  var FACES = Object.keys(SCHEME).map(function (k) { return SCHEME[k]; });
  var PIECES = FACES.concat(FACES.map(function (f) { return f + '_U'; }), ['A_Win', 'A_WinUp', 'A_Door', 'A_Vent', 'A_Lamp',
    'A_ChartL', 'A_ChartR', 'A_Poster1', 'A_Poster2', 'A_Poster3', 'A_Board', 'A_Exit', 'A_Clock', 'TG', 'TG_N',
    'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'Hatch', 'Stand', 'C_TrailLight']);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (gl) { if (PIECES.indexOf(gl.piece) < 0) PIECES.push(gl.piece); }); });
  // every symbol stands on level ground (the knolls rise only in the open)
  var FLAT = Object.keys(SYMBOLS).join('').replace(/[oQ]/g, '') + '`:';   // boulders and outcrops sit in the knolls

  IB.registerTheme({
    id: 'observatory', name: 'Vesper Peak Observatory', family: 'kit-observatory', prefix: 'KIT_OBSERVATORY_',
    palette: ['#2F5EA8', '#E9A48E', '#EEF1F7', '#1B2440'],
    // late dusk: indigo overhead going to stars, a warm band low in the west (backdrop), a soft rosy light from the west
    env: {
      sky: ['#121838', '#3C4486'], fog: { color: '#B391A8', near: 90, far: 1400, tierScale: true }, sun: [-0.7, 0.42, 0.5],
      sunColor: '#FFD9C8', clouds: false, far: 2700,
      ceiling: { height: 3.6, color: '#E3E6EA', light: 'C_TrailLight', every: 3 }   // the link corridors and the hatch room only
    },
    floor: { color: '#DCE0EA', trail: '#C9CDD6', outside: '#C8CCDB' },
    terrain: { height: terrainHeight, paint: terrainPaint, flat: FLAT, ramp: [1, 3.5], low: '#DCE0EA', high: '#8A8592', patch: '#CDD1DD', top: 1.1 },
    wall: { height: 10.0, roof: '#5B6470', facing: 'open', choose: chooseWall, passage: { ch: DOORS, solid: [[3.0, 10.0]] } },
    dataLayers: [0.02, 0.03, 0.04, 0.05],
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall', 'TrailWall_D'], height: 3.6 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: buildVista },
    budget: { prop: 4000, landmark: 9000, total: 70000 },
    allPieces: function () { return PIECES.slice(); },
    chooser: { codeAt: codeAt, schemeAt: schemeAt, artPiece: artPiece, terrainHeight: terrainHeight },
    levels: {
      observatory: {
        name: 'Vesper Peak Observatory',
        intro: 'The last climb: robots have taken Vesper Peak Observatory, high above the clouds. Fight across the summit compound past the dish antennas, the radio masts and the old dome, then into the Great Dome itself -- the telescope floor, the catwalk ring, the labs and the glass rooms over the sea of clouds.',
        zones: [
          // the summit compound; the first wave is light robots only
          { map: 'observatory_1', ceiling: false, label: 'The Summit Compound', waves: [
            [['crawler', 24], ['gunner', 12], ['drone', 6]],
            [['crawler', 20], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 8], ['blader', 5]],
            [['crawler', 15], ['drone', 6], ['gunner', 10], ['soldier', 7], ['blader', 5]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 7], ['blader', 4]],
            [['crawler', 15], ['gunner', 9], ['drone', 5], ['soldier', 6], ['blader', 4]]] },
          // inside the Great Dome
          { map: 'observatory_2', ceiling: false, terrain: false, label: 'The Great Dome',
            floor: { color: '#A3A9B3', trail: '#C9CDD6', lines: [{ dir: 'x', every: 2, width: 0.02, color: '#929AA5', y: 0.008 }, { dir: 'z', every: 2, width: 0.02, color: '#929AA5', y: 0.0105 }] },
            waves: [
              [['crawler', 18], ['gunner', 10], ['drone', 5], ['soldier', 6], ['blader', 5]],
              [['crawler', 16], ['drone', 7], ['gunner', 10], ['soldier', 6], ['blader', 4]],
              [['crawler', 16], ['gunner', 10], ['bomber', 2], ['drone', 3], ['soldier', 6], ['blader', 4]],
              [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 3]],
              [['crawler', 17], ['gunner', 10], ['bomber', 2], ['soldier', 5], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
