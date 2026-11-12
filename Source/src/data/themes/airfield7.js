/* Theme: Airfield 7 (kit-airfield7) -- a made-up remote military air base of the made-up 7th Air Wing on the arid
   steppe: flat sun-bleached land and dry scrub to the horizon, low ochre hills far off, a hot hazy afternoon. The base
   is under lockdown: T-wall blast barriers ring its areas and the runway has been closed with concrete barriers,
   jersey barrier lines and tank traps. Two zones; player travel is north.
   1 The flight line (76 x 78): the main runway crosses the zone east - west (rows 6-23, asphalt, edge lines, the
     centreline; it runs on for kilometres past both side walls, where the zone is closed by low runway-closure
     barriers so the runway is seen running away to its thresholds, 09 in the west and 27 in the east), the taxiway
     parallel to it (rows 28-37) with two link taxiways and their holding markings, sand and scrub strips between them,
     the concrete apron (rows 40-76). The spawn is behind the transport (a made-up four-turboprop "Hauler" with its
     rear ramp down: walk up into the hold, cargo strapped at the front), the fuel bowser at its wing. Two fighter
     revetments (earth berms on gabion faces) on the west apron, each with a made-up "Kestrel F7" fighter nose out
     under its covers; the control tower (landmark: the ops annex whose roof terrace at 3.6 m is reached by a steel
     stair, the shaft and the glass cab) with the crash tender on the east apron, a fighter on its stand with its tug;
     a fighter taxiing west on the taxiway; the runway control caravan at the link; on the runway a fighter that
     rolled out, a tug with a munitions trailer, the barrier lines; AA guns in sandbag nests and the windsock on the
     north shoulder.
   2 The hangar area (72 x 74): the hardened aircraft shelter (landmark: a camouflage-painted concrete barrel vault,
     its sliding door leaves telescoped open, the jet-blast port in the back wall) with a fighter under maintenance
     (canopy raised, boarding ladder, panels open); the maintenance hangar (tan cladding, trusses, the crane beam):
     the tool crib, workbenches, parts racks, the lathe, the drill press, an engine on its dolly; the engine test
     stand (an engine on its thrust cradle, the blast deflector, the test cabin); the ordnance igloo (earth-covered,
     door open, bomb racks inside) with munitions trailers and the forklift; the barracks block with its gallery at
     3.2 m and a stair at each end; the yard with picnic tables and the flagpole; the supply dump under a camouflage
     net; sandbag positions, light masts.
   Built by blender/fam_kit_airfield7.py (af_*.py); zone layouts by tools/airfield7_zones.py (src/data/zones/airfield7_*.txt).
   Sandbags, jersey barriers, tank traps, the AA guns, crates, drums, the jeep, the generator, the camouflage net,
   pallet stacks and the flagpole are kit-stronghold pieces, the forklift a kit-parking piece (theme option `families`).

   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled; fronts / noses point south at 0, R90 = east):
     # wall: T-wall blast barriers (3.6 m, their own collision), the runway-closure barriers (1.1 m) where the runway
       and its shoulders meet the side walls of zone 1, corner pillars
     T control tower [12, 12] (landmark)   Q transport [30, 28] (nose north, ramp down south)
     R revetment [18, 18] (open east)   F K W V fighter [10, 16] nose south / east / west / north (closed canopy,
     covers)   M fighter under maintenance [10, 16] (nose south)   X crash tender [3, 10]   B fuel bowser [3, 8]
     C runway caravan [3, 6]   U tug [2, 3]   O munitions trailer [2, 4]   g ground power unit [2, 2]
     n m v taxiway signs [2, 1] (location, direction, runway holding)   l runway edge light   i taxiway light
     w windsock   L floodlight mast   c chocks   b tool chest   f fire bottle   t tyres   s u scrub
     H hardened aircraft shelter [28, 30] (landmark, door south)   N maintenance hangar [28, 22] (doors south)
     Y barracks [26, 10] (gallery south)   D ordnance igloo [12, 16] (door west)   Z engine test stand [10, 14]
     (intake west)   z tool crib [8, 5]   q workbench [3, 1]   1 2 parts racks [4, 1]   3 lathe [3, 1]
     4 drill press   5 engine on its dolly [2, 4]   p picnic table [2, 2]
     kit-stronghold: = sandbags (runs)   j jersey barrier (runs)   x tank trap   A AA gun [3, 3]   k crates
       d drums   J jeep [2, 4]   y generator [2, 1]   & camouflage net over a supply dump [4, 4]   $ pallet stack
       [2, 2]   | flagpole;   kit-parking: 8 forklift [2, 3]
   Layer: "@layer 0" holds the aircraft and the gear inside the revetments, the shelter and the hangar (F K W V M,
   g b f t c, z q 1 2 3 4 5).
   Backdrop (backdrop.build, level-wide, so nothing switches between the zones): the steppe to the horizon (sand,
   scrub patches, dirt tracks), the runway with its markings running out to both thresholds (piano keys, 09 / 27,
   touchdown bars), the floor paint of both zones (the runway, the taxiway and its links, the sand strips, holding
   markings, the apron lead-in lines, the hangar area's sand yards and roads), distant base buildings (shelters,
   hangars, a radar tower, a water tower), a big windsock by the runway, and low ochre hills on a ring that follows
   the camera. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, KS = 'KIT_STRONGHOLD_', KP = 'KIT_PARKING_';
  var RWY = [6, 24], TWY = [28, 38], LINKS = [[11, 18], [60, 67]], APRON = 40;   // zone 1 rows / link columns

  // ---------------------------------------------------------------- walls
  function kindOf(g) {   // zone 1 (the flight line) holds the transport
    if (g._aK === undefined) { g._aK = 'z2'; for (var r = 0; r < g.h; r++) if (g.rows[r].indexOf('Q') >= 0) { g._aK = 'z1'; break; } }
    return g._aK;
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function twall(i) {
    if (i % 11 === 5) return 'TWall_Light';
    if (i % 23 === 9) return 'TWall_Sign';
    if (i % 19 === 14) return 'TWall_Crest';
    if (i % 13 === 3) return 'TWall_Num';
    if (i % 29 >= 20 && i % 29 <= 25) return 'TWall_Wire';
    return i % 2 ? 'TWall_B' : 'TWall_A';
  }
  var BAR = [RWY[0] - 4, RWY[1] + 3];   // zone 1 side-wall rows closed by barriers (the runway and its shoulders)
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var W = g.w - 1, H = g.h - 1;
    if (gateDist(g, c, r) < 2.6) return null;   // the gate frame's pylons fill the cells beside a gate
    if ((r === 0 || r === H) && (c === 0 || c === W)) return 'TWall_Corner';
    if (kindOf(g) === 'z1' && (c === 0 || c === W)) {
      if (r >= BAR[0] && r < BAR[1]) return (r % 3) ? 'Barrier_A' : 'Barrier_B';
      if (r === BAR[0] - 1 || r === BAR[1]) return 'TWall_End';
    }
    return twall(c === 0 || c === W ? r + (c ? 7 : 0) : c + (r ? 3 : 0));
  }

  // ---------------------------------------------------------------- symbols
  function pf(size, pieces, face, extra) { var d = { size: size, pieces: pieces, kind: 'cover' }; if (face !== undefined) d.face = face; return Object.assign(d, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, kind: 'cover', rotate: rot === undefined ? 'random90' : rot }, extra || {}); }
  function jet(face, extra) { return pf([10, 16], ['Fighter'], face, { with: { Fighter: [extra || 'Fighter_Canopy'] } }); }
  var SYMBOLS = {
    'T': pf([12, 12], ['Landmark_Tower'], 0),
    'Q': pf([30, 28], ['Transport'], Math.PI),
    'R': pf([18, 18], ['Revetment'], R90),
    'F': jet(0), 'K': jet(R90), 'W': jet(-R90), 'V': jet(Math.PI),
    'M': jet(0, 'Fighter_Open'),
    'X': pf([3, 10], ['Tender'], undefined, { flip: true }),
    'B': pf([3, 8], ['Bowser'], undefined, { flip: true }),
    'C': pf([3, 6], ['Caravan'], undefined, { flip: true }),
    'U': pf([2, 3], ['Tug'], undefined, { flip: true }),
    'O': pf([2, 4], ['MunTrailer'], undefined, { flip: true }),
    'g': pf([2, 2], ['GPU'], undefined, { flip: true }),
    'n': pf([2, 1], ['Sign_A'], 0), 'm': pf([2, 1], ['Sign_B'], 0), 'v': pf([2, 1], ['Sign_Hold'], 0),
    'l': one(['RwyLight'], 0, { collide: false }),
    'i': one(['TaxiLight'], 0, { collide: false }),
    'w': one(['Windsock'], 0),
    'L': one(['LightMast'], 'edge'),
    'c': one(['Chocks'], 0),
    'b': one(['ToolChest']),
    'f': one(['FireBottle']),
    't': one(['Tyres']),
    's': one(['Scrub_A'], 'random90', { collide: false }),
    'u': one(['Scrub_B'], 'random90', { collide: false }),
    'H': pf([28, 30], ['Landmark_HAS'], 0),
    'N': pf([28, 22], ['Hangar'], 0),
    'Y': pf([26, 10], ['Barracks'], 0),
    'D': pf([12, 16], ['Igloo'], -R90),
    'Z': pf([10, 14], ['TestStand'], -R90),
    'z': pf([8, 5], ['ToolCrib'], 0),
    'q': pf([3, 1], ['Workbench']),
    '1': pf([4, 1], ['RackA']),
    '2': pf([4, 1], ['RackB']),
    '3': pf([3, 1], ['Lathe']),
    '4': one(['DrillPress'], 0),
    '5': pf([2, 4], ['EngineDolly'], undefined, { flip: true }),
    'p': pf([2, 2], ['Picnic'], undefined, { flip: true }),
    // kit-stronghold and kit-parking pieces
    '=': { pieces: [KS + 'Sandbags_A', KS + 'Sandbags_B'], rotate: 'run', alternate: true, kind: 'cover' },
    'j': { pieces: [KS + 'Jersey'], rotate: 'run', kind: 'cover' },
    'x': one([KS + 'Hedgehog']),
    'A': pf([3, 3], [KS + 'AAGun'], 0),
    'k': one([KS + 'Crate_A', KS + 'Crate_B', KS + 'AmmoCans']),
    'd': one([KS + 'Drums']),
    'J': pf([2, 4], [KS + 'Jeep'], undefined, { flip: true }),
    'y': pf([2, 1], [KS + 'Generator'], undefined, { flip: true }),
    '&': pf([4, 4], [KS + 'CamoNet'], undefined, { flip: true }),
    '$': pf([2, 2], [KS + 'Stack'], undefined, { flip: true }),
    '|': one([KS + 'Flagpole'], 0),
    '8': pf([2, 3], [KP + 'Forklift'], undefined, { flip: true })
  };

  // ---------------------------------------------------------------- the steppe, the runway, the floor paint (backdrop.build)
  /* Level-wide: built once in level.root, so nothing here switches or pops as the player crosses between the zones. */
  function buildLand(level, api) {
    var T = typeof THREE !== 'undefined' ? THREE : null;
    var G = api.geo, hash = api.hash, Z = level.zones, Z1 = Z[0], Z2 = Z[1] || Z[0];
    var X0 = Z1.ox, XE = Z1.ox + Z1.w, cx = (X0 + XE) / 2, cz = (Z2.oz + Z1.oz + Z1.h) / 2;
    var sand = '#D3B580', sandD = '#BFA06A', scrub = '#A5A05E', asph = '#5F5C57', white = '#EEEDE6', yel = '#F0C22E', conc = '#C9C1AE';
    function rect(x0, z0, x1, z1, y, c) { G.flat([[x0, z0], [x1, z0], [x1, z1], [x0, z1]], y, c); }
    // ---- the steppe: one big sheet, scrub patches and dirt tracks (outside the zones)
    rect(cx - 1800, cz - 1800, cx + 1800, cz + 1800, -0.03, sand);
    var n = 0;
    function inside(x, z, pad) {
      return Z.some(function (q) { return x > q.ox - pad && x < q.ox + q.w + pad && z > q.oz - pad && z < q.oz + q.h + pad; });
    }
    for (var gx = -1000; gx <= 1000; gx += 42) for (var gz = -1000; gz <= 1000; gz += 42) {
      n++;
      var sx = cx + gx + (hash(n, 3) - 0.5) * 30, sz = cz + gz + (hash(n, 5) - 0.5) * 30;
      if (inside(sx, sz, 30)) continue;
      if (sz > Z1.oz + RWY[0] - 40 && sz < Z1.oz + RWY[1] + 40) continue;   // keep the runway strip clean
      var L = 8 + hash(n, 7) * 20, w = 3 + hash(n, 9) * 6, k = hash(n, 11);
      G.flat([[sx - L, sz - w], [sx + L * 0.7, sz - w * 0.8], [sx + L, sz + w * 0.5], [sx - L * 0.6, sz + w]], -0.025, k < 0.45 ? scrub : k < 0.8 ? sandD : '#C9AE78');
    }
    // dirt tracks: one round the base, one off to the south-east
    var rz0 = Z2.oz - 30, rz1 = Z1.oz + Z1.h + 26, rx0 = X0 - 34, rx1 = XE + 34;
    [[rx0, rz0, rx1, rz0 + 5], [rx0, rz1 - 5, rx1, rz1], [rx0, rz0, rx0 + 5, Z1.oz + RWY[0] - 30], [rx1 - 5, rz0, rx1, Z1.oz + RWY[0] - 30],
     [rx0, Z1.oz + RWY[1] + 30, rx0 + 5, rz1], [rx1 - 5, Z1.oz + RWY[1] + 30, rx1, rz1]].forEach(function (t) { rect(t[0], t[1], t[2], t[3], -0.022, '#B99B68'); });
    // ---- the runway: asphalt from far west to far east, shoulders, edge lines, centreline, thresholds, numbers
    var r0 = Z1.oz + RWY[0], r1 = Z1.oz + RWY[1], rc = (r0 + r1) / 2, TW = X0 - 520, TE = XE + 520;
    function strip(x0, x1, z0, z1, c, y) {   // in the zone over its floor, outside it over the steppe
      var yi = y === undefined ? 0.02 : y;
      if (x0 < X0) rect(x0, z0, Math.min(x1, X0), z1, yi - 0.026, c);
      if (x1 > XE) rect(Math.max(x0, XE), z0, x1, z1, yi - 0.026, c);
      if (x1 > X0 && x0 < XE) rect(Math.max(x0, X0), z0, Math.min(x1, XE), z1, yi, c);
    }
    strip(TW - 60, TE + 60, r0, r1, asph);
    strip(TW - 60, TE + 60, r0 - 3, r0, '#C2A773');
    strip(TW - 60, TE + 60, r1, r1 + 3, '#C2A773');
    strip(TW, TE, r0 + 0.5, r0 + 1.4, white, 0.04);
    strip(TW, TE, r1 - 1.4, r1 - 0.5, white, 0.04);
    for (var dx = TW + 40; dx < TE - 40; dx += 50) strip(dx, dx + 30, rc - 0.45, rc + 0.45, white, 0.04);
    [[TW, 1], [TE, -1]].forEach(function (E) {   // threshold piano keys, touchdown bars and the aiming point
      var x = E[0], s = E[1];
      for (var k = 0; k < 8; k++) { var z = r0 + 2 + k * 2.0; if (k === 3 || k === 4) continue; strip(Math.min(x, x + s * 30), Math.max(x, x + s * 30), z, z + 1.4, white, 0.04); }
      strip(Math.min(x - s * 2, x - s * 1), Math.max(x - s * 2, x - s * 1), r0 + 1.4, r1 - 1.4, white, 0.04);
      [150, 300].forEach(function (d) { [r0 + 3.5, r1 - 5.5].forEach(function (z) { strip(Math.min(x + s * d, x + s * (d + 22)), Math.max(x + s * d, x + s * (d + 22)), z, z + 2, white, 0.04); }); });
    });
    api.add('Rwy09', TW + 45, -0.025, rc, -R90, 1);
    api.add('Rwy27', TE - 45, -0.025, rc, R90, 1);
    // ---- zone 1 floor paint: the sand strips, the taxiway and its links, holding markings, the apron lines
    var oz = Z1.oz;
    rect(X0, oz + 1, XE, oz + RWY[0] - 3, 0.01, sand);
    rect(X0, oz + RWY[1] + 3, XE, oz + TWY[0], 0.01, sand);
    rect(X0, oz + TWY[1], XE, oz + APRON, 0.01, sand);
    rect(X0, oz + TWY[0], XE, oz + TWY[1], 0.02, '#8F8B83');
    LINKS.forEach(function (Lk) { rect(X0 + Lk[0], oz + RWY[1], X0 + Lk[1], oz + TWY[0], 0.03, '#8F8B83'); });
    var tc = oz + (TWY[0] + TWY[1]) / 2;
    rect(X0 + 1, tc - 0.08, XE - 1, tc + 0.08, 0.04, yel);
    LINKS.forEach(function (Lk) {
      var lx = X0 + (Lk[0] + Lk[1]) / 2;
      rect(lx - 0.08, oz + RWY[1], lx + 0.08, tc - 0.08, 0.045, yel);
      // the runway holding position: two solid lines and two dashed lines across the link
      [0.0, 0.45].forEach(function (d) { rect(X0 + Lk[0] + 0.3, oz + RWY[1] + 3.4 + d, X0 + Lk[1] - 0.3, oz + RWY[1] + 3.6 + d, 0.06, yel); });
      for (var xx = X0 + Lk[0] + 0.3; xx < X0 + Lk[1] - 0.6; xx += 1.2) [1.1, 1.55].forEach(function (d) { rect(xx, oz + RWY[1] + 3.4 + d, xx + 0.7, oz + RWY[1] + 3.6 + d, 0.06, yel); });
    });
    // taxiway edge lines (yellow) and the apron's lead-in lines to each stand
    rect(X0 + 1, oz + TWY[0] + 0.2, XE - 1, oz + TWY[0] + 0.35, 0.04, yel);
    rect(X0 + 1, oz + TWY[1] - 0.35, XE - 1, oz + TWY[1] - 0.2, 0.04, yel);
    [[37.0, TWY[1], 42.6], [67.0, TWY[1], 56.8]].forEach(function (Ld) { rect(X0 + Ld[0] - 0.08, oz + Ld[1], X0 + Ld[0] + 0.08, oz + Ld[2], 0.04, yel); });
    [49, 67].forEach(function (zz) { rect(X0 + 19.2, oz + zz - 0.08, X0 + 30, oz + zz + 0.08, 0.04, yel); });
    rect(X0 + 29.92, oz + TWY[1], X0 + 30.08, oz + 67.08, 0.04, yel);
    for (var wz = oz + 41; wz < oz + 76; wz += 3) rect(X0 + 53.0, wz, X0 + 53.15, wz + 1.6, 0.04, white);   // the service-road edge
    rect(X0 + 1, oz + 75.9, XE - 1, oz + 76.05, 0.04, white);
    // ---- zone 2 floor paint: sand round the igloo and the test stand, the road's centre line, the HAS lead-in
    if (Z[1]) {
      var x2 = Z2.ox, z2 = Z2.oz;
      rect(x2 + 44, z2 + 45, x2 + Z2.w - 1, z2 + Z2.h - 1, 0.01, sand);
      rect(x2 + 52, z2 + 26, x2 + Z2.w - 1, z2 + 45, 0.01, sand);
      rect(x2 + 1, z2 + 1, x2 + 43, z2 + 2, 0.01, sand);
      rect(x2 + 41, z2 + 1, x2 + Z2.w - 1, z2 + 3.4, 0.01, sand);
      for (var yz = z2 + 2; yz < z2 + Z2.h - 2; yz += 4) rect(x2 + 35.42, yz, x2 + 35.58, yz + 2, 0.04, white);
      rect(x2 + 15.92, z2 + 32, x2 + 16.08, z2 + 38.5, 0.04, yel);
      rect(x2 + 15.92, z2 + 38.42, x2 + 35.3, z2 + 38.58, 0.04, yel);
      rect(x2 + 3, z2 + 63.2, x2 + 29, z2 + 63.35, 0.04, white);
      rect(x2 + 44.5, z2 + 15, x2 + 69.5, z2 + 15.15, 0.04, white);   // the barracks yard's kerb line
    }
    // ---- distant base buildings: aircraft shelters, hangars, a radar tower, a water tower (low poly, fogged)
    [[X0 - 170, oz - 60], [X0 - 210, oz - 10], [XE + 160, oz - 80], [XE + 200, oz - 30], [XE + 240, oz + 20]].forEach(function (P, i) {
      G.sphere(P[0], 0, P[1], 14, i % 2 ? '#B9B19E' : '#A8A08D', { ws: 10, hs: 6, sy: 0.62 });
    });
    [[X0 - 120, oz + 120, 40, 28], [XE + 140, oz + 140, 34, 24], [cx - 30, Z2.oz - 160, 60, 30]].forEach(function (P) {
      G.box(P[0], 5, P[1], P[2], 10, P[3], '#CDBE9C');
      G.box(P[0], 10.6, P[1], P[2] + 0.6, 1.2, P[3] + 0.6, '#A3957A', { hull: false });
    });
    G.cyl(XE + 90, 0, Z2.oz - 60, 1.4, 1.0, 26, 8, '#9A9C96');
    G.box(XE + 90, 27, Z2.oz - 60, 4.5, 2.6, 4.5, '#E3D4B4');
    G.sphere(XE + 90, 31.5, Z2.oz - 60, 3.0, '#EEEDE6', { ws: 10, hs: 6 });
    [[X0 - 70, Z2.oz + 30]].forEach(function (P) {
      for (var q = 0; q < 4; q++) G.cyl(P[0] + (q % 2 ? 3 : -3), 0, P[1] + (q < 2 ? 3 : -3), 0.25, 0.25, 16, 5, '#7A7C78', { hull: false });
      G.cyl(P[0], 16, P[1], 5.5, 5.5, 6, 12, '#E3D4B4');
      G.cyl(P[0], 22, P[1], 5.5, 0.4, 2.2, 12, '#C2AE88');
    });
    // a big windsock by the runway, west of the zone
    api.add('Windsock', X0 - 60, -0.03, r1 + 14, 0, 1.6);
    if (!T) return;
    // ---- the hills: low ochre ranges on a ring that follows the camera (like the sky dome)
    var ring = new T.Group(); ring.name = 'Hills';
    var pos = [], colr = [], idx = [];
    function vtx(x, y, z, c) { pos.push(x, y, z); colr.push(c.r, c.g, c.b); return pos.length / 3 - 1; }
    var fogC = new T.Color('#E9DCC2');
    [{ R: 760, h: [26, 88], rock: '#B99A78', rock2: '#AC8E6E', seed: 1, n: 120 },
     { R: 640, h: [10, 36], rock: '#A78A62', rock2: '#9B7F58', seed: 2, n: 160 }].forEach(function (RG) {
      var N = RG.n, P = [], c1 = new T.Color(RG.rock), c2 = new T.Color(RG.rock2), haze = c1.clone().lerp(fogC, 0.55), ink = new T.Color('#5A4A3E').lerp(c1, 0.45);
      for (var i = 0; i <= N; i++) {
        var a = i / N * Math.PI * 2, u = i / N * 6.2832 * 3 + RG.seed;
        var hh = 0.5 + 0.3 * Math.sin(u) + 0.18 * Math.sin(u * 2.7 + 1.1) + 0.1 * Math.sin(u * 6.3 + 0.5);
        hh = Math.max(0, Math.min(1, hh));
        P.push([Math.cos(a) * RG.R, Math.sin(a) * RG.R, RG.h[0] + (RG.h[1] - RG.h[0]) * hh * hh + (hash(i, 40 + RG.seed) - 0.5) * 4]);
      }
      for (i = 0; i < N; i++) {
        var A = P[i], B = P[i + 1], cA = (i % 5 < 2) ? c1 : c2;
        var v0 = vtx(A[0], -60, A[1], fogC), v1 = vtx(B[0], -60, B[1], fogC), v2 = vtx(B[0], -2, B[1], haze), v3 = vtx(A[0], -2, A[1], haze);
        idx.push(v0, v1, v2, v0, v2, v3);
        var w0 = vtx(A[0], -2, A[1], haze), w1 = vtx(B[0], -2, B[1], haze), w2 = vtx(B[0], B[2], B[1], cA), w3 = vtx(A[0], A[2], A[1], cA);
        idx.push(w0, w1, w2, w0, w2, w3);
        var k0 = vtx(A[0] * 0.999, A[2] - 0.2, A[1] * 0.999, ink), k1 = vtx(B[0] * 0.999, B[2] - 0.2, B[1] * 0.999, ink);
        var k2 = vtx(B[0] * 0.999, B[2] + 1.2, B[1] * 0.999, ink), k3 = vtx(A[0] * 0.999, A[2] + 1.2, A[1] * 0.999, ink);
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
    api.tick(function () {
      var cam = IB.Render && IB.Render.camera;
      if (cam) { ring.position.x = cam.position.x; ring.position.z = cam.position.z; }
    });
  }

  var PIECES = ['TWall_A', 'TWall_B', 'TWall_Num', 'TWall_Crest', 'TWall_Light', 'TWall_Sign', 'TWall_Wire', 'TWall_End', 'TWall_Corner',
    'Barrier_A', 'Barrier_B', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'Hatch',
    'Fighter_Canopy', 'Fighter_Open', 'Rwy09', 'Rwy27'];
  var BORROWED = [];   // kit-stronghold / kit-parking pieces (theme option `families`)
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (!d.pieces) return;
    d.pieces.forEach(function (n) {
      if (n.indexOf('KIT_') === 0) { if (BORROWED.indexOf(n) < 0) BORROWED.push(n); } else if (PIECES.indexOf(n) < 0) PIECES.push(n);
    });
  });

  IB.registerTheme({
    id: 'airfield7', name: 'Airfield 7', family: 'kit-airfield7', prefix: 'KIT_AIRFIELD7_', families: ['kit-stronghold', 'kit-parking'],
    palette: ['#CBC3B0', '#C9A974', '#6B7F4A', '#B8342C'],
    // a hot, hazy afternoon on the steppe: a pale blue sky going to a dusty horizon, a warm sun high in the south-west
    env: { sky: ['#5C95CF', '#EBDDC2'], fog: { color: '#E9DCC2', near: 110, far: 720, tierScale: true }, sun: [-0.4, 0.86, 0.32], sunColor: '#FFF3DE',
      clouds: true, ceiling: null, far: 950 },
    floor: { color: '#C9C1AE', trail: '#B9A77F', lines: [{ dir: 'x', every: 5, width: 0.04, color: '#B6AE9B', y: 0.006 }, { dir: 'z', every: 5, width: 0.04, color: '#B6AE9B', y: 0.007 }] },
    wall: { height: 1.1, roof: '#A8A08E', facing: 'open', choose: chooseWall, cols: true },
    symbols: SYMBOLS,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall_D'], height: 2.6 },
    hatch: 'Hatch', stand: KS + 'Crate_A',
    backdrop: { build: buildLand },
    budget: { prop: 4800, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.slice(); }, borrowed: BORROWED,
    levels: {
      airfield7: {
        name: 'Airfield 7',
        intro: 'Robots have overrun Airfield 7, a remote air base on the steppe. Fight across the flight line past the control tower and the runway, then clear the shelters and hangars.',
        zones: [
          // the flight line: the apron, the taxiway, the runway; the first wave is light robots only
          { map: 'airfield7_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 6]],
            [['crawler', 19], ['gunner', 11], ['bomber', 2], ['soldier', 7], ['blader', 5]],
            [['crawler', 15], ['drone', 8], ['gunner', 9], ['soldier', 7], ['blader', 4]],
            [['crawler', 19], ['gunner', 11], ['bomber', 2], ['soldier', 7], ['blader', 5]],
            [['crawler', 15], ['gunner', 9], ['drone', 6], ['soldier', 6], ['blader', 3]]] },
          // the hangar area: the shelter, the hangar, the test stand, the igloo, the barracks
          { map: 'airfield7_2', waves: [
            [['crawler', 17], ['gunner', 10], ['drone', 5], ['soldier', 5], ['blader', 3]],
            [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 5], ['blader', 3]],
            [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 17], ['gunner', 9], ['bomber', 2], ['soldier', 5], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
