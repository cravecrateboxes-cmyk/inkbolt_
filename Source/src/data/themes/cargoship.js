/* Theme: Halcyon Vega (kit-cargoship) -- a very big container ship of the (made-up) Halcyon Lines at sea, open ocean
   to the horizon all round, no land in sight. The player goes deeper into the ship zone by zone: the main deck under
   the sky, down a stair trunk into a cargo hold, then through a watertight door into the engine room.
   Built by blender/fam_kit_cargoship.py (cargo_*.py); zone layers by tools/cargoship_zones.py.

   Zone 1, the main deck (no ceiling): the bulwarks are the west / east walls, the forecastle bulkhead the south wall
   (the bow, its breakwater and foremast stand beyond it), the white front of the superstructure the north wall (the
   accommodation tower, bridge wings, radar mast, funnel and lifeboats rise over it). Hatch covers are solid decks
   1.8 m up ("@layer 1.8") carrying the container stacks; steel stairs climb onto them from the cross-deck lanes.
   Zone 2, a cargo hold, and zone 3, the engine room, are under a 13 m deckhead (env.ceiling) with gantry walkways /
   upper flats at 5.2 m ("@layer 5.2", thin grating decks with rails, reached by stair towers). The stair trunks
   between zones are 13 m shafts with landings. Each zone has its own floor paint (zone plan `floor`: deck green,
   tank top, floor plates; zones.js).

   Symbols (1 cell = 1 m; prefab sizes [x, z] in cells; the theme repaints every container stack (BOX paint slots)):
   main deck   1 2 3 4  40 ft double stack, 1 - 4 tiers [5,12] (reefers, the line's own teal boxes, stepped tops)
               5 6      20 ft double stack, 1 / 2 tiers [5,6]      T tank container [3,6]   F flat rack [3,12]
               t hatch cover (solid deck, 1.8 m)   L lashing bridge [6,2] (walk under it)   K deck crane [4,4]
               W mooring winch [4,3]   b bitts [2,1]   V hold ventilator [2,2]   c lashing-gear cage [3,2]
               B lifeboat davit (boat outboard to the west) [3,8]   R rescue-boat davit (outboard to the east) [3,8]
               m foam monitor   o rope coil   D drums   v mushroom vent   x manhole
               Z / U steel stair onto a hatch cover rising north / south [3,4]
   hold        e i j k l  container cell with cell guides: empty, 1 - 4 tiers [3,13]   f cell with a yacht on a
               flat rack [3,13]   Y transformer on skids [4,6]   d cable drums [2,2]   I pipe stack [3,6]
   engine room M main engine [11,24] (with its top and aft parts)   g generator set [4,9]   u purifiers [2,2]
               q pumps [2,1]   A starting-air bottles [2,1]   O auxiliary boiler [3,3]   J engine control room [8,6]
               (on the east flat, its windows west)   H workshop bench [4,1]   Q main switchboard [6,1]
               C valve manifold [2,1]   z settling tank [4,3]   y shaft line [3,1] (a bearing every third cell)
   both        w walkway / upper flat (grating deck, 0.3 m)   r walkway rail   X / N steel stair rising north /
               south to 5.2 m [3,10]
   markings    : walkway line   % hazard hatching   ! rust   & oil   ; hatch seam   ` twistlock sockets
               7 8 9 hatch numbers   | grating   @ bilge well
   deckhead    = hatch-cover girder   _ daylight slot between hatch panels   n hanging lamp   + crane rail
               * crane bridge   ~ pipe rack   - duct   ^ chain hoist (an overlay mesh that swings slowly)
   Backdrop (backdrop.build): the ocean down at the waterline (13 m below the main deck) out past the fog, the hull
   sides with their boot top, the bow (forecastle piece) and the stern, a Kelvin wake spreading from the bow and a
   churned wake astern, sea glints and foam flecks drifting aft (the ship is under way), gulls wheeling round the
   superstructure, a feeder ship far out; overlays: chain hoists swaying on the deckhead, the propeller shaft
   turning. Nothing rolls or sways the camera. */
(function (IB) {
  'use strict';
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  var R90 = Math.PI / 2, SEA = -13;

  // ---- container paint: the stacks use four slot pairs (cells 40 - 47); each placed stack gets four line colours
  var SLOTS = [40, 41, 42, 43, 44, 45, 46, 47];
  var MAINS = [40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60];
  var BOX = { from: SLOTS, to: [] };
  for (var j = 0; j < 28; j++) {
    var job = [], used = {};
    for (var s = 0; s < 4; s++) {
      var k = Math.floor(hh(j * 4 + s, 17) * MAINS.length), m = MAINS[k];
      while (used[m]) { k = (k + 1) % MAINS.length; m = MAINS[k]; }
      used[m] = 1; job.push(m, m + 1);
    }
    BOX.to.push(job);
  }

  // ---- which zone a grid is: the main deck (64 rows), the engine room (holds the main engine), else the hold
  function kindOf(g) {
    if (g._csK === undefined) {
      var engine = false;
      (g.rows || []).forEach(function (row) { if (row.indexOf('M') >= 0) engine = true; });
      g._csK = g.h >= 60 ? 'deck' : engine ? 'er' : 'hold';
    }
    return g._csK;
  }
  function gateC(grid, r) {
    var cache = grid._csGate || (grid._csGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows[r] || '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  // the line's name over the upper decks of the superstructure front: HALCYON left of the door, LINES right of it
  var NAME = [{ word: 'HALCYON', c0: 7, n: 10 }, { word: 'LINES', c0: 36, n: 7 }];
  function corner(kind, c, r, grid) {
    var ns = r < grid.h / 2 ? 'N' : 'S', ew = c < grid.w / 2 ? 'W' : 'E';
    var k = kind === 'deck' ? (ns === 'N' ? 'DeckN' : 'DeckS') : kind === 'er' ? 'Er' : 'Hold';
    return 'Corner_' + k + '_' + ns + ew;
  }
  function chooseWall(c, r, horiz, cornerCell, hash, grid, face) {
    var kind = kindOf(grid);
    if (face === 'corner' || face === 'none') return corner(kind, c, r, grid);
    var ns = face === 'S' || face === 'N';
    if (ns) { var g = gateC(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return null; }   // the door portal's jambs
    var u = ns ? c : r, W = grid.w, H = grid.h, x;
    if (kind === 'deck') {
      if (face === 'S') {   // superstructure front
        for (var i = 0; i < NAME.length; i++) {
          var N = NAME[i];
          if (c >= N.c0 && c < N.c0 + N.n) return ['Sup_Top', 'Sup_' + N.word + '_' + (c - N.c0)];
        }
        if (c <= 2 || c >= W - 3) return 'Sup_Blank';
        if (c === 9 || c === W - 10) return 'Sup_Door';
        if (c === 4 || c === W - 5) return 'Sup_Vent';
        return 'Sup_Win';
      }
      if (face === 'N') {   // forecastle bulkhead
        if (c === Math.floor(W / 2)) return 'Fc_Door';
        if (c === 10 || c === W - 11) return 'Fc_Ladder';
        if (c === 5 || c === W - 6) return 'Fc_Vent';
        if (c === 31) return 'Fc_Sign';
        return 'Fc_Plain';
      }
      // bulwarks: fairleads by the mooring stations, open railing amidships, hose boxes, deck lights, lashing racks
      if (r < 7 || r > H - 9) return r % 3 === 1 ? 'Bul_Chock' : 'Bul_Plain';
      if (r % 12 === 6) return 'Bul_Light';
      if (r % 18 === 9) return 'Bul_Hose';
      if (r % 14 === 3) return 'Bul_Lash';
      return Math.floor(r / 8) % 2 ? 'Bul_Rail' : 'Bul_Plain';
    }
    if (kind === 'hold') {
      if (ns) {   // corrugated transverse bulkheads, the hold number painted big
        var c0 = face === 'S' ? 8 : W - 13;
        if (c >= c0 && c < c0 + 5) return ['Hb_Plain', 'Hb_Num_' + (c - c0)];
        if (c === 5 || c === W - 6) return 'Hb_Ladder';
        if (c % 8 === 4) return 'Hb_Lamp';
        if (c % 16 === 12) return 'Hb_Vent';
        return hash(c, r) < 0.18 ? 'Hb_Rust' : 'Hb_Plain';
      }
      if (r === 10 || r === H - 11) return 'Hs_Ladder';
      if (r % 8 === 4) return 'Hs_Lamp';
      if (r % 4 === 0) return 'Hs_Web';
      if (r % 8 === 2) return 'Hs_Pipe';
      return 'Hs_Plain';
    }
    // engine room plating
    x = u % 12;
    if (u === 7 || u === (ns ? W : H) - 8) return 'Er_Ladder';
    if (x === 3) return 'Er_Pipes';
    if (x === 6) return 'Er_Lamp';
    if (x === 9) return 'Er_Tray';
    if (x === 0 && ns) return 'Er_Panel';
    if (x === 11 && !ns) return 'Er_Sign';
    return 'Er_Plain';
  }

  // ---------------------------------------------------------------- the ship, the sea, the wake (zones.js backdrop.build)
  function buildShip(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var Z = level.zones, Z1 = Z[0], X0 = Z1.ox, X1 = Z1.ox + Z1.w, CX = (X0 + X1) / 2, hash = api.hash, g = api.geo;
    var zFwd = Z1.oz + Z1.h, zStem = zFwd + 44.5, zAft = Z1.oz;
    Z.forEach(function (z) { zAft = Math.min(zAft, z.oz); });
    level.trails.forEach(function (t) { zAft = Math.min(zAft, t.z1); });
    if (level.hatch) zAft = Math.min(zAft, level.hatch.z - 4);
    zAft -= 8;
    var zc = (zAft + zStem) / 2;
    // the ocean, out past the fog (its far colour is the horizon), and a deeper band near the hull
    g.flat([[CX - 700, zc - 700], [CX + 700, zc - 700], [CX + 700, zc + 700], [CX - 700, zc + 700]], SEA - 0.02, '#2F7DB9');
    // hull sides along the parallel body (bulwark top down to the waterline, black boot top), the stern
    var hullR = '#B23A2E', boot = '#26232B';
    [[X0, -1], [X1, 1]].forEach(function (S) {
      var x = S[0] + S[1] * 0.26, L = zFwd - zAft;
      g.box(x, (-0.02 + SEA + 2) / 2, (zFwd + zAft) / 2, 0.5, -0.02 - SEA - 2, L, hullR, { hull: false, noBottom: true });
      g.box(x + S[1] * 0.02, SEA + 1.0, (zFwd + zAft) / 2, 0.5, 2.0, L, boot, { hull: false, noBottom: true });
    });
    g.box(CX, (SEA + 14) / 2, zAft - 0.25, X1 - X0, 14 - SEA, 0.5, hullR, { hull: false, noBottom: true });
    g.box(CX, SEA + 1.0, zAft - 0.27, X1 - X0 + 0.04, 2.0, 0.5, boot, { hull: false, noBottom: true });
    // the Kelvin wake: two arms of broken foam spreading from the bow at 19.5 degrees; churned water astern
    var foam = '#F4FCFF', churn = '#5FC4D8', ta = Math.tan(19.5 * Math.PI / 180);
    [-1, 1].forEach(function (sg) {
      for (var d = 6; d < 330; d += 9) {
        var w0 = 0.8 + d * 0.012, len = 5 + hash(d, sg + 5) * 3, x0 = CX + sg * (d * ta + 3), z0 = zStem - 6 - d, x1 = CX + sg * ((d + len) * ta + 3), z1 = z0 - len;
        g.flat([[x0 - sg * w0, z0], [x0 + sg * w0, z0], [x1 + sg * w0, z1], [x1 - sg * w0, z1]], SEA + 0.03, foam);
      }
    });
    for (var d2 = 0; d2 < 300; d2 += 6) {
      var hw = 22 + d2 * 0.12, zz = zAft - d2;
      g.flat([[CX - hw, zz], [CX + hw, zz], [CX + hw + 0.7, zz - 6], [CX - hw - 0.7, zz - 6]], SEA + 0.01, churn);
      for (var q = 0; q < 3; q++) {
        var fx = CX + (hash(d2, q + 1) - 0.5) * hw * 1.6, fw = 1.5 + hash(q, d2) * 3;
        g.flat([[fx - fw, zz - 1], [fx + fw, zz - 1.4], [fx + fw * 0.8, zz - 4], [fx - fw * 0.9, zz - 3.6]], SEA + 0.03, foam);
      }
    }
    // bow wave rolling off the stem
    [-1, 1].forEach(function (sg) {
      for (var k2 = 0; k2 < 7; k2++) {
        var a0 = zStem - 5 - k2 * 5, wx = CX + sg * (2 + k2 * 3.4);
        g.flat([[wx, a0], [wx + sg * 3.5, a0 - 1], [wx + sg * 5.5, a0 - 5], [wx + sg * 1.5, a0 - 4]], SEA + 0.04, foam);
      }
    });
    // ---- pieces: the bow, the accommodation tower and funnel over the superstructure, lifeboats, a feeder far out
    api.add('Backdrop_Forecastle', CX, 0, zFwd, 0, 1);
    api.add('Backdrop_Deckhouse', CX, 13.0, Z1.oz - 3, 0, 1);
    api.add('Backdrop_Funnel', CX, 13.0, Z1.oz - 27, 0, 1);
    api.add('Davit_Lifeboat', X0 + 2.5, 13.0, Z1.oz - 10, 0, 1);
    api.add('Davit_Lifeboat', X1 - 2.5, 13.0, Z1.oz - 10, Math.PI, 1);
    api.add('Backdrop_Feeder', CX + 120, SEA, Z1.oz + 40, 0.5, 1.4);

    if (!THREE || !IB.Assets || !level.root) return;
    var TH = IB.THEME_DEFS.cargoship, A = IB.Assets;
    function inst(name, n) {
      var full = IB.themePiece(TH, name), geo = A.get(full);
      if (!geo) return null;
      var im = new THREE.InstancedMesh(geo, A.material(full), n);
      im.frustumCulled = false; level.root.add(im); return im;
    }
    var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);
    // sea glints and foam flecks drift aft past the ship (it is under way); they wrap round a window about it
    var SPAN = 300, NG = 150, NF = 110, gl = inst('Sea_Glint', NG), fl = inst('Foam_Fleck', NF), glints = [], flecks = [];
    function sidePos(i, k, near, far) {
      var sd = hash(i, k) < 0.5 ? -1 : 1, off = near + Math.pow(hash(i, k + 1), 1.4) * (far - near);
      return { x: sd < 0 ? X0 - off : X1 + off, z: zc + (hash(i, k + 2) - 0.5) * SPAN };
    }
    for (var i = 0; i < NG; i++) { var p = sidePos(i, 600, 15, 140); glints.push({ x: p.x, z: p.z, ph: hash(i, 603) * 6.28, sp: 0.6 + hash(i, 604) * 0.8, s: 0.8 + hash(i, 605) * 1.3, yaw: (hash(i, 606) - 0.5) * 0.6 }); }
    for (i = 0; i < NF; i++) { var pf = sidePos(i, 700, 4, 90); flecks.push({ x: pf.x, z: pf.z, s: 0.6 + hash(i, 703) * 1.2, yaw: hash(i, 704) * 6.28 }); }
    var V = 5.5;   // m/s the water slides aft
    // gulls wheeling round the superstructure and over the bow
    var NGU = 7, gu = inst('Gull', NGU), gulls = [];
    for (i = 0; i < NGU; i++) gulls.push({ cx: CX + (hash(i, 801) - 0.5) * 70, cz: (i < 4 ? Z1.oz - 10 : zFwd + 10) + (hash(i, 802) - 0.5) * 30, r: 12 + hash(i, 803) * 20,
      y: 18 + hash(i, 804) * 16, w: (0.18 + hash(i, 805) * 0.12) * (i % 2 ? 1 : -1), ph: hash(i, 806) * 6.28 });
    // overlays in the zones (hidden with them): chain hoists that sway, the propeller shaft that turns
    var hooks = [], shafts = [];
    Z.forEach(function (zn) {
      (zn.grid.layers || []).forEach(function (lg) {
        for (var r = 0; r < lg.h; r++) for (var c = 0; c < lg.w; c++) {
          if (lg.rows[r][c] !== '^') continue;
          var full = IB.themePiece(TH, 'ChainHook'), geo = A.get(full); if (!geo) continue;
          var mh = new THREE.Mesh(geo, A.material(full));
          mh.position.set(zn.ox + c + 0.5, lg.y, zn.oz + r + 0.5); zn.group.add(mh);
          hooks.push({ m: mh, ph: hash(c, r) * 6.28 });
        }
      });
      var G0 = zn.grid, runs = {};
      for (var r2 = 0; r2 < G0.h; r2++) for (var c2 = 0; c2 < G0.w; c2++) if (G0.rows[r2][c2] === 'y' && (c2 === 0 || G0.rows[r2][c2 - 1] !== 'y')) {
        var key = c2; (runs[key] || (runs[key] = [])).push(r2);
      }
      Object.keys(runs).forEach(function (key) {
        var rows = runs[key], full = IB.themePiece(TH, 'ShaftSpin'); if (!A.get(full)) return;
        var r0 = Math.min.apply(null, rows), r1 = Math.max.apply(null, rows), zm = (r0 + r1 + 1) / 2, list = [];
        rows.forEach(function (rr) { list.push(A.placed(full, new THREE.Matrix4().makeTranslation(0, -1.4, rr + 0.5 - zm))); });
        var ms = new THREE.Mesh(A.merge(list), A.material(full));
        ms.position.set(zn.ox + (+key) + 1.5, 1.4, zn.oz + zm); zn.group.add(ms); shafts.push(ms);
      });
    });
    api.tick(function (dt, t) {
      var lo = zc - SPAN / 2;
      if (gl) for (var a = 0; a < glints.length; a++) {
        var G = glints[a]; G.z -= V * dt; if (G.z < lo) G.z += SPAN;
        var sc = Math.max(0, Math.sin(t * G.sp + G.ph)) * G.s;
        _q.setFromAxisAngle(UP, G.yaw); _p.set(G.x, SEA + 0.05, G.z); _s.set(sc + 0.001, 1, sc + 0.001);
        gl.setMatrixAt(a, _m.compose(_p, _q, _s));
      }
      if (gl) gl.instanceMatrix.needsUpdate = true;
      if (fl) for (a = 0; a < flecks.length; a++) {
        var F = flecks[a]; F.z -= V * dt; if (F.z < lo) F.z += SPAN;
        _q.setFromAxisAngle(UP, F.yaw); _p.set(F.x, SEA + 0.06, F.z); _s.set(F.s, 1, F.s);
        fl.setMatrixAt(a, _m.compose(_p, _q, _s));
      }
      if (fl) fl.instanceMatrix.needsUpdate = true;
      if (gu) for (a = 0; a < gulls.length; a++) {
        var U = gulls[a], an = U.ph + t * U.w;
        _p.set(U.cx + Math.cos(an) * U.r, U.y + Math.sin(t * 0.5 + U.ph) * 1.5, U.cz + Math.sin(an) * U.r);
        _q.setFromAxisAngle(UP, -an + (U.w > 0 ? Math.PI : 0)); _s.set(1.6, 1.6, 1.6);
        gu.setMatrixAt(a, _m.compose(_p, _q, _s));
      }
      if (gu) gu.instanceMatrix.needsUpdate = true;
      for (a = 0; a < hooks.length; a++) { var Hk = hooks[a]; Hk.m.rotation.z = 0.05 * Math.sin(t * 0.8 + Hk.ph); Hk.m.rotation.x = 0.035 * Math.sin(t * 0.57 + Hk.ph * 1.7); }
      for (a = 0; a < shafts.length; a++) shafts[a].rotation.z = t * 7.0;
    });
  }

  // ---------------------------------------------------------------- pieces
  var WALLS = [];
  ['Plain', 'Rail', 'Chock', 'Hose', 'Lash', 'Light'].forEach(function (v) { WALLS.push('Bul_' + v); });
  ['Win', 'Blank', 'Door', 'Vent', 'Top'].forEach(function (v) { WALLS.push('Sup_' + v); });
  NAME.forEach(function (N) { for (var k = 0; k < N.n; k++) WALLS.push('Sup_' + N.word + '_' + k); });
  ['Plain', 'Door', 'Ladder', 'Vent', 'Sign'].forEach(function (v) { WALLS.push('Fc_' + v); });
  ['Plain', 'Ladder', 'Lamp', 'Rust', 'Vent'].forEach(function (v) { WALLS.push('Hb_' + v); });
  for (var n7 = 0; n7 < 5; n7++) WALLS.push('Hb_Num_' + n7);
  ['Plain', 'Web', 'Pipe', 'Ladder', 'Lamp'].forEach(function (v) { WALLS.push('Hs_' + v); });
  ['Plain', 'Pipes', 'Panel', 'Tray', 'Ladder', 'Lamp', 'Sign'].forEach(function (v) { WALLS.push('Er_' + v); });
  [['DeckN', 'NW'], ['DeckN', 'NE'], ['DeckS', 'SW'], ['DeckS', 'SE']].forEach(function (k) { WALLS.push('Corner_' + k[0] + '_' + k[1]); });
  ['Hold', 'Er'].forEach(function (k) { ['NW', 'NE', 'SW', 'SE'].forEach(function (c) { WALLS.push('Corner_' + k + '_' + c); }); });
  var OTHER = ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_End', 'Hatch', 'ChainHook', 'ShaftSpin',
    'Backdrop_Forecastle', 'Backdrop_Deckhouse', 'Backdrop_Funnel', 'Backdrop_Feeder', 'Gull', 'Sea_Glint', 'Foam_Fleck', 'Davit_Lifeboat'];
  function ord(pieces, extra) { return Object.assign({ pieces: pieces }, extra); }
  var COVER = { kind: 'cover' };
  function stackSym(size, pieces) { return Object.assign({ size: size, pieces: pieces, flip: true, kind: 'cover', paint: BOX }); }

  IB.registerTheme({
    id: 'cargoship', name: 'Halcyon Vega', family: 'kit-cargoship', prefix: 'KIT_CARGOSHIP_',
    palette: ['#B23A2E', '#4F8A5E', '#1F9C98', '#2F7DB9'],
    // a clear day at sea: blue zenith, pale haze at the horizon; the fog is the horizon colour, so the ocean runs into
    // the sky with no edge. The hold and the engine room are under the 13 m deckhead (zone 1 has none)
    env: {
      sky: ['#3C8FD8', '#D6EAF5'], fog: { color: '#D6EAF5', near: 60, far: 150 }, sun: [0.45, 0.85, 0.3], clouds: true,
      ceiling: { height: 13, color: '#8E9A9C' }
    },
    // main deck paint with plate seams; the hold and the engine room bring their own floors (zone plan `floor`)
    floor: {
      color: '#4F8A5E', trail: '#8E979B', outside: '#4F8A5E',
      lines: [{ dir: 'x', every: 2.4, width: 0.03, color: '#467D54', y: 0.006 }, { dir: 'z', every: 6, width: 0.03, color: '#467D54', y: 0.008 }],
      trailLines: [{ dir: 'x', every: 0.5, width: 0.03, color: '#7A8387', y: 0.009 }]
    },
    wall: { height: 13, roof: '#8E9A9C', facing: 'open', choose: chooseWall },
    symbols: {
      // main deck: containers on the hatch covers
      '1': stackSym([5, 12], ['S40_1A', 'S40_1A', 'S40_1R']),
      '2': stackSym([5, 12], ['S40_2A', 'S40_2B']),
      '3': stackSym([5, 12], ['S40_3A']),
      '4': stackSym([5, 12], ['S40_4A', 'S40_4B']),
      '5': stackSym([5, 6], ['S20_1A']),
      '6': stackSym([5, 6], ['S20_2A']),
      'T': { size: [3, 6], pieces: ['Tank_20'], flip: true, kind: 'cover' },
      'F': { size: [3, 12], pieces: ['Flat_Boat', 'Flat_Mach'], flip: true, kind: 'cover' },
      't': { deck: { thick: 1.8, color: '#77937F', edge: '#4F8A5E', under: '#4F8A5E', with: '*' } },
      'L': { size: [6, 2], pieces: ['LB_A', 'LB_B'], flip: true, kind: 'cover' },
      'K': { size: [4, 4], pieces: ['Landmark_Crane'], face: 0, kind: 'cover', with: { Landmark_Crane: ['Landmark_CraneJib'] } },
      'W': { size: [4, 3], pieces: ['Winch_A', 'Winch_B'], flip: true, kind: 'cover' },
      'b': { size: [2, 1], pieces: ['Bitts'], kind: 'cover' },
      'V': { size: [2, 2], pieces: ['HoldVent'], kind: 'cover' },
      'c': { size: [3, 2], pieces: ['LashCage'], flip: true, kind: 'cover' },
      'B': { size: [3, 8], pieces: ['Davit_Lifeboat'], face: 0, kind: 'cover' },
      'R': { size: [3, 8], pieces: ['Davit_Rescue'], face: Math.PI, kind: 'cover' },
      'm': ord(['FoamMonitor'], { rotate: 'random90', kind: 'cover' }),
      'o': ord(['RopeCoil'], COVER),
      'D': ord(['Drums'], { rotate: 'random90', kind: 'cover' }),
      'v': ord(['MushroomVent'], COVER),
      'x': ord(['Manhole'], COVER),
      'Z': { size: [3, 4], pieces: ['StairH'], face: 0, kind: 'step' },
      'U': { size: [3, 4], pieces: ['StairH'], face: Math.PI, kind: 'step' },
      // hold
      'e': stackSym([3, 13], ['Cell_0']),
      'i': stackSym([3, 13], ['Cell_1']),
      'j': stackSym([3, 13], ['Cell_2']),
      'k': stackSym([3, 13], ['Cell_3']),
      'l': stackSym([3, 13], ['Cell_4']),
      'f': stackSym([3, 13], ['Cell_Flat']),
      'Y': { size: [4, 6], pieces: ['Transformer'], flip: true, kind: 'cover' },
      'd': { size: [2, 2], pieces: ['CableDrums'], flip: true, kind: 'cover' },
      'I': { size: [3, 6], pieces: ['PipeStack'], flip: true, kind: 'cover' },
      // engine room
      'M': { size: [11, 24], pieces: ['Landmark_Engine'], face: 0, kind: 'cover', with: { Landmark_Engine: ['Landmark_EngineTop', 'Landmark_EngineAft'] } },
      'g': { size: [4, 9], pieces: ['Genset_A', 'Genset_B'], flip: true, kind: 'cover' },
      'u': { size: [2, 2], pieces: ['Purifiers'], flip: true, kind: 'cover' },
      'q': { size: [2, 1], pieces: ['Pumps'], flip: true, kind: 'cover' },
      'A': { size: [2, 1], pieces: ['AirBottles'], flip: true, kind: 'cover' },
      'O': { size: [3, 3], pieces: ['Boiler'], face: 0, kind: 'cover' },
      'J': { size: [8, 6], pieces: ['Landmark_ECR'], face: -R90, kind: 'wall' },
      'H': { size: [4, 1], pieces: ['Workshop'], orient: 'wall', kind: 'cover' },
      'Q': { size: [6, 1], pieces: ['Switchboard'], orient: 'wall', kind: 'cover' },
      'C': { size: [2, 1], pieces: ['Manifold'], flip: true, kind: 'cover' },
      'z': { size: [4, 3], pieces: ['Tank'], orient: 'wall', kind: 'cover' },
      'y': { size: [3, 1], pieces: ['Shaft', 'Shaft', 'ShaftBearing'], sequence: true, face: 0, kind: 'cover' },
      // walkways, rails and the tall stairs (hold, engine room)
      'w': { deck: { thick: 0.3, color: '#B9C2CB', edge: '#4F5865', under: '#6E7780', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
      'X': { size: [3, 10], pieces: ['StairW'], face: 0, kind: 'step' },
      'N': { size: [3, 10], pieces: ['StairW'], face: Math.PI, kind: 'step' },
      // markings
      ':': ord(['WalkLine'], { rotate: 'run', collide: false }),
      '%': ord(['Hatching'], { collide: false }),
      '!': ord(['Rust'], { rotate: 'random90', collide: false }),
      '&': ord(['Oil'], { rotate: 'random90', collide: false }),
      ';': ord(['Seam'], { rotate: 'run', collide: false }),
      '`': ord(['Sockets'], { rotate: 'random90', collide: false }),
      '7': ord(['HatchNo_1'], { collide: false }), '8': ord(['HatchNo_2'], { collide: false }), '9': ord(['HatchNo_3'], { collide: false }),
      '|': ord(['Grate'], { collide: false }),
      '@': ord(['Bilge'], { collide: false }),
      // deckhead fittings (hang from 13 m)
      '=': ord(['Girder'], { rotate: 'run', collide: false }),
      '_': ord(['Slot'], { rotate: 'run', collide: false }),
      'n': ord(['Lamp'], { collide: false }),
      '+': ord(['CraneRail'], { rotate: 'run', collide: false }),
      '*': ord(['CraneBridge'], { rotate: 'run', collide: false }),
      '~': ord(['PipeRack'], { rotate: 'run', collide: false }),
      '-': ord(['Duct'], { rotate: 'run', collide: false })
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    // stair trunks: 13 m shafts with landings, ladders, deck doors, lamps
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall'], height: 13, end: 'TrailWall_End' },
    hatch: 'Hatch', stand: 'Drums',
    backdrop: { build: buildShip },
    budget: { prop: 3000, landmark: 4000, total: 60000 },
    allPieces: function () {
      var out = WALLS.concat(OTHER), sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var d = sym[ch], list = (d.pieces || []).concat(d.full ? [d.full] : [], d.post ? [d.post] : []);
        if (d.with) Object.keys(d.with).forEach(function (k) { list = list.concat(d.with[k]); });
        list.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      cargoship: {
        name: 'Halcyon Vega',
        intro: 'Robots have seized a container ship in mid-ocean. Clear the main deck, then fight your way down through the hold to the engine room.',
        zones: [
          // the main deck: hatch covers and container stacks, lanes and walkways, the superstructure ahead
          { map: 'cargoship_1', ceiling: false, waves: [
            [['crawler', 22], ['gunner', 6], ['drone', 3]],
            [['crawler', 7], ['bomber', 2], ['gunner', 7], ['blader', 8]],
            [['crawler', 7], ['drone', 6], ['gunner', 5], ['soldier', 9]],
            [['crawler', 6], ['bomber', 2], ['gunner', 7], ['soldier', 8], ['blader', 4]]] },
          // a cargo hold: container cells, gantry walkways at 5.2 m
          { map: 'cargoship_2', floor: { color: '#8F8A7E', lines: [{ dir: 'x', every: 3, width: 0.03, color: '#7F7A6F', y: 0.006 }, { dir: 'z', every: 3, width: 0.03, color: '#7F7A6F', y: 0.008 }] },
            waves: [
            [['crawler', 22], ['gunner', 7], ['drone', 2]],
            [['crawler', 7], ['bomber', 2], ['gunner', 7], ['blader', 8]],
            [['crawler', 7], ['drone', 5], ['gunner', 6], ['soldier', 9]],
            [['crawler', 6], ['bomber', 2], ['gunner', 7], ['blader', 7], ['soldier', 5]]] },
          // the engine room: the main engine, its platforms and the upper flats, a heavy last stand
          { map: 'cargoship_3', floor: { color: '#9AA1A6', lines: [{ dir: 'x', every: 1, width: 0.025, color: '#80878C', y: 0.006 }, { dir: 'z', every: 1, width: 0.025, color: '#80878C', y: 0.008 }] },
            waves: [
            [['crawler', 22], ['gunner', 9], ['drone', 2]],
            [['crawler', 8], ['bomber', 2], ['drone', 5], ['soldier', 10]],
            [['crawler', 8], ['gunner', 9], ['drone', 5], ['blader', 8]],
            [['crawler', 10], ['gunner', 10], ['bomber', 2], ['drone', 4], ['soldier', 13], ['blader', 6]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
