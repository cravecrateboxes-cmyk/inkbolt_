/* INKBOLT rooftops: open air between buildings, falls that kill, and wooden planks that robots throw down across the
   gaps (generic: theme.rooftop; first used by Zenith Command's roof zone, theme 'highrise').

   A rooftop zone is a zone whose floor plan holds the theme's void symbol. Its cells are:
     void (rooftop.void, e.g. '_')   open air down to the street: the world's ground there is `depth` m down
     plank site (rooftop.site, '%') / laid plank (rooftop.laid, '$')   void cells a plank spans: a rectangle at least
                                     two cells wide whose two ends (along its long axis) touch roofs (pick characters
                                     that are not theme symbols: the zone builds every theme symbol it finds)
     anything else on the floor plan the zone's own roof at y = 0; deck symbols on "@layer <y>" grids over void cells
                                     are the roofs of the neighbouring buildings at that height (theme deck options)
   Built here (Rooftops.build, from zones.js buildLevel):
     * world void masks: World.groundAt answers -depth over void cells, floorAt / rays / the nav grid follow it, so
       anyone who walks off an edge falls (zones.js voidAt)
     * roof edges: a parapet piece along every edge that faces open air, a low kerb (rooftop.kerb.h, under a robot's
       stride, a step for the player) where a plank lands and one cell either side; collision boxes per edge cell
     * the buildings' masses under every roof (solid boxes down to the street, so nobody falls "into" a building;
       zone.roofs lists them for the city below, which draws their facades)
     * planks laid at the start (rooftop.laid): the exit route never depends on a robot
   Runtime (Rooftops.update, every fixed step):
     * falls: the player below the kill height (the zone's lowest roof - rooftop.drop) dies (G.fallDeath); a ground
       robot that drops below it is wrecked (kill credit only: its gems are lost in the street); flyers are kept
       above rooftop.flyFloor over open air
     * planks: a robot of a `crew` type standing near one end of an empty site, on a roof the player is not on, throws a
       plank up and kicks it down across the gap (rooftop.delay s later; one plank every rooftop.gap s per zone). The
       plank swings up, tips over and slams down (thud, dust, a comic word); it then becomes walkable boxes (stepped
       when the roofs differ in height), the kerbs under it stop blocking, and the zone's nav grid is rebuilt, so
       robots path across it after the player, and the player can walk it too.
   Planks stay where they fall for the rest of the level (Rooftops.reset puts the start state back on a restart). */
(function (IB) {
  'use strict';
  var R = IB.Rooftops = {};
  var DIRS = [[0, 1, 0], [0, -1, Math.PI], [1, 0, Math.PI / 2], [-1, 0, -Math.PI / 2]];   // [dc, dr, yaw of an edge piece facing that way]

  function opt(theme) { return theme.rooftop || {}; }
  R.has = function (grid, theme) {
    var O = theme.rooftop; if (!O) return false;
    var v = O.void || '_';
    for (var r = 0; r < grid.h; r++) if (grid.rows[r].indexOf(v) >= 0) return true;
    return false;
  };
  function rectsOf(W, H, test) {
    var used = new Uint8Array(W * H), out = [];
    for (var r = 0; r < H; r++) for (var c = 0; c < W; c++) {
      if (used[r * W + c] || !test(c, r)) continue;
      var w = 1; while (c + w < W && !used[r * W + c + w] && test(c + w, r)) w++;
      var h = 1, ok = true;
      while (ok && r + h < H) { for (var k = 0; k < w; k++) if (used[(r + h) * W + c + k] || !test(c + k, r + h)) { ok = false; break; } if (ok) h++; }
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) used[(r + y) * W + c + x] = 1;
      out.push({ c: c, r: r, w: w, h: h });
    }
    return out;
  }

  /* ---------------- build ---------------- */
  R.build = function (level, zone, grid, theme, world, g, P) {
    var O = opt(theme), W = grid.w, H = grid.h, V = O.void || '_', SITE = O.site || '%', LAID = O.laid || '$';
    var depth = O.depth || 150, voidY = -depth;
    var hgt = new Float32Array(W * H), kind = new Uint8Array(W * H);   // kind: 0 void, 1 roof, 2 wall / gate
    var decks = {};
    Object.keys(theme.symbols || {}).forEach(function (ch) { if (theme.symbols[ch].deck) decks[ch] = theme.symbols[ch].deck; });
    var r, c, i;
    for (r = 0; r < H; r++) for (c = 0; c < W; c++) {
      var ch = grid.rows[r][c];
      if (ch === V || ch === SITE || ch === LAID) { kind[r * W + c] = 0; hgt[r * W + c] = voidY; }
      else if (ch === '#' || ch === 'G' || ch === 'E') { kind[r * W + c] = 2; hgt[r * W + c] = 0; }
      else { kind[r * W + c] = 1; hgt[r * W + c] = 0; }
    }
    // neighbouring roofs: deck cells on the layers over void cells
    var thick = {};
    grid.layers.forEach(function (lg) {
      // a deck with `with: '*'` claims every filled cell of its layer (props, spawns and pickups stand on the roof)
      var all = null;
      for (r = 0; r < H && !all; r++) for (c = 0; c < W && !all; c++) { var d0 = decks[lg.rows[r][c]]; if (d0 && d0.with === '*') all = d0; }
      for (r = 0; r < H; r++) for (c = 0; c < W; c++) {
        var ch = lg.rows[r][c], d = decks[ch] || (all && ch !== '.' && ch !== '#' ? all : null);
        if (!d || kind[r * W + c] !== 0 || grid.rows[r][c] !== V) continue;
        kind[r * W + c] = 1; hgt[r * W + c] = lg.y; thick[r * W + c] = d.thick || 0.4;
      }
    });
    function roofAt(cc, rr) { return cc >= 0 && rr >= 0 && cc < W && rr < H && kind[rr * W + cc] === 1; }
    function hAt(cc, rr) { return hgt[rr * W + cc]; }
    // roof ids: 4-connected cells of one height
    var id = new Int16Array(W * H).fill(-1), nRoof = 0, low = 0;
    for (i = 0; i < W * H; i++) {
      if (kind[i] !== 1 || id[i] >= 0) continue;
      var q = [i]; id[i] = nRoof;
      while (q.length) {
        var k0 = q.pop(), kc = k0 % W, kr = (k0 / W) | 0;
        low = Math.min(low, hgt[k0]);
        DIRS.forEach(function (D) {
          var nc = kc + D[0], nr = kr + D[1];
          if (!roofAt(nc, nr)) return;
          var n = nr * W + nc; if (id[n] >= 0 || Math.abs(hgt[n] - hgt[k0]) > 0.05) return;
          id[n] = nRoof; q.push(n);
        });
      }
      nRoof++;
    }
    var Z = { voidY: voidY, killY: low - (O.drop || 8), id: id, hgt: hgt, kind: kind, w: W, h: H, sites: [], planks: [], kerbs: [], zone: zone, theme: theme,
      flyFloor: O.flyFloor === undefined ? 2 : O.flyFloor, gapT: 0 };
    zone.roof = Z;
    (level.roofZones || (level.roofZones = [])).push(Z);
    // open air under everything but the zone's own roof (a neighbouring roof is a deck over the void)
    world.addVoid(zone.ox, zone.oz, W, H, function (cc, rr) { var i = rr * W + cc; return kind[i] === 0 || (kind[i] === 1 && hgt[i] !== 0) ? voidY : null; });

    // roof surfaces: the zone's own roof is painted here (the void cells stay open); decks paint themselves
    var F = theme.floor || {}, roofCol = new THREE.Color(F.color || '#9A9C9E');
    rectsOf(W, H, function (cc, rr) { return kind[rr * W + cc] === 1 && hAt(cc, rr) === 0; }).forEach(function (Rc) {
      g.flat([[zone.ox + Rc.c, zone.oz + Rc.r], [zone.ox + Rc.c + Rc.w, zone.oz + Rc.r], [zone.ox + Rc.c + Rc.w, zone.oz + Rc.r + Rc.h], [zone.ox + Rc.c, zone.oz + Rc.r + Rc.h]], 0.004, roofCol);
    });

    // plank sites (both symbols): rectangles of site cells; the long axis spans the gap
    [[SITE, false], [LAID, true]].forEach(function (S) {
      rectsOf(W, H, function (cc, rr) { return grid.rows[rr][cc] === S[0]; }).forEach(function (Rc) {
        var alongZ = Rc.h >= Rc.w, ends;
        if (alongZ) ends = [{ c: Rc.c, r: Rc.r - 1, dc: 0, dr: -1 }, { c: Rc.c, r: Rc.r + Rc.h, dc: 0, dr: 1 }];
        else ends = [{ c: Rc.c - 1, r: Rc.r, dc: -1, dr: 0 }, { c: Rc.c + Rc.w, r: Rc.r, dc: 1, dr: 0 }];
        var ok = ends.every(function (e) { return roofAt(e.c, e.r); });
        if (!ok) { if (typeof console !== 'undefined') console.warn('rooftops: plank site without roofs at both ends', zone.idx, Rc); return; }
        var cw = alongZ ? Rc.w : Rc.h;   // cells across
        ends.forEach(function (e) {
          e.h = hAt(e.c, e.r); e.roof = id[e.r * W + e.c];
          // the kerb line: the edge of the end cell facing the gap; centre across the site
          var ax = zone.ox + (alongZ ? Rc.c + cw / 2 : (e.dc < 0 ? Rc.c : Rc.c + Rc.w));
          var az = zone.oz + (alongZ ? (e.dr < 0 ? Rc.r : Rc.r + Rc.h) : Rc.r + cw / 2);
          e.x = ax; e.z = az;
        });
        Z.sites.push({ rect: Rc, alongZ: alongZ, across: cw, ends: ends, laid: false, start: S[1], t: 0, anim: null, plank: null, by: null });
      });
    });
    // edges: parapets, and kerbs within one cell of a plank landing
    var kerbCell = {};
    var KW = (O.kerb && O.kerb.reach) || 1;
    Z.sites.forEach(function (s) {
      s.ends.forEach(function (e) {
        for (var k = -KW; k < s.across + KW; k++) {
          var cc = s.alongZ ? s.rect.c + k : e.c, rr = s.alongZ ? e.r : s.rect.r + k;
          kerbCell[cc + ',' + rr + ',' + (-e.dc) + ',' + (-e.dr)] = true;
        }
      });
    });
    var PAR = O.parapet || {}, KB = O.kerb || {}, parH = PAR.h || 1.1, kerbH = KB.h || 0.3, parT = PAR.t || 0.3, kerbT = KB.t || 0.25;
    Z.kerbH = kerbH;
    for (r = 0; r < H; r++) for (c = 0; c < W; c++) {
      if (kind[r * W + c] !== 1) continue;
      var h0 = hAt(c, r), x0 = zone.ox + c, z0 = zone.oz + r;
      // which sides are edges (open air or a roof at another height)
      var edge = DIRS.map(function (D) {
        var nc = c + D[0], nr = r + D[1];
        if (nc < 0 || nr < 0 || nc >= W || nr >= H) return true;
        var nk = kind[nr * W + nc];
        if (nk === 2) return false;
        return nk === 0 || Math.abs(hgt[nr * W + nc] - h0) > 0.05;
      });
      DIRS.forEach(function (D, di) {
        if (!edge[di]) return;
        var isKerb = kerbCell[c + ',' + r + ',' + D[0] + ',' + D[1]];
        // an east / west edge stops short where the cell also has a north / south edge (that one runs the full length)
        var cut = '';
        if (D[0]) {
          var nS = edge[0], nN = edge[1];
          // local -X end of a module facing east is north (yaw pi/2: local -X -> +Z... see below)
          var lo = D[0] > 0 ? nS : nN, hi = D[0] > 0 ? nN : nS;   // facing east: local -X = south; facing west: local -X = north
          cut = (lo ? 'L' : '') + (hi ? 'R' : '');
        }
        var spec = isKerb ? KB : PAR, piece = (spec.piece || (isKerb ? 'Kerb' : 'Parapet')) + cut;
        P.add(piece, x0 + 0.5, h0, z0 + 0.5, D[2]);
        // collision: the strip along that edge, inside the cell
        var t = isKerb ? kerbT : parT, top = h0 + (isKerb ? kerbH : parH);
        var bx0 = x0, bx1 = x0 + 1, bz0 = z0, bz1 = z0 + 1;
        if (D[1] > 0) bz0 = z0 + 1 - t; else if (D[1] < 0) bz1 = z0 + t; else if (D[0] > 0) bx0 = x0 + 1 - t; else bx1 = x0 + t;
        var b = world.add(bx0, h0 - 0.02, bz0, bx1, top, bz1, 'wall', zone.idx);
        if (isKerb) Z.kerbs.push({ b: b, c: c, r: r, dc: D[0], dr: D[1] });
      });
    }
    // building masses under every roof (and under the zone's wall cells), for collision and for the city below
    var FAC = O.facades || [['#8E9AA8', '#56667A']];
    zone.roofs = [];
    var massRects = [];
    var keyOf = function (cc, rr) { var k = kind[rr * W + cc]; return k === 0 ? null : (k === 2 ? 0 : hgt[rr * W + cc] - (thick[rr * W + cc] || 0)); };
    var used = new Uint8Array(W * H);
    for (r = 0; r < H; r++) for (c = 0; c < W; c++) {
      var kk = keyOf(c, r); if (kk === null || used[r * W + c]) continue;
      var w2 = 1; while (c + w2 < W && !used[r * W + c + w2] && keyOf(c + w2, r) === kk) w2++;
      var h2 = 1, ok2 = true;
      while (ok2 && r + h2 < H) { for (var k2 = 0; k2 < w2; k2++) if (used[(r + h2) * W + c + k2] || keyOf(c + k2, r + h2) !== kk) { ok2 = false; break; } if (ok2) h2++; }
      for (var yy = 0; yy < h2; yy++) for (var xx = 0; xx < w2; xx++) used[(r + yy) * W + c + xx] = 1;
      massRects.push({ c: c, r: r, w: w2, h: h2, top: kk });
    }
    massRects.forEach(function (Rc) {
      var x0 = zone.ox + Rc.c, z0 = zone.oz + Rc.r, x1 = x0 + Rc.w, z1 = z0 + Rc.h;
      var rid = id[Rc.r * W + Rc.c]; if (rid < 0) { for (var k3 = 0; k3 < DIRS.length && rid < 0; k3++) { var nc = Rc.c + DIRS[k3][0], nr = Rc.r + DIRS[k3][1]; if (roofAt(nc, nr)) rid = id[nr * W + nc]; } }
      var F2 = FAC[(rid < 0 ? 0 : rid) % FAC.length];
      world.add(x0, voidY, z0, x1, Rc.top - 0.02, z1, 'wall', zone.idx).noRay = true;
      zone.roofs.push([x0, z0, x1, z1, Rc.top - 0.02, F2[0], F2[1], F2[2] || 3.8]);
    });
    // rooftop.gateHead: a piece over the entry gate where the zone's wall rises past the gate frame (the roof's door
    // in a taller facade)
    if (O.gateHead) for (r = 0; r < H; r++) {
      var e0 = grid.rows[r].indexOf('E'), e1 = grid.rows[r].lastIndexOf('E');
      if (e0 >= 0) P.add(O.gateHead, zone.ox + (e0 + e1 + 1) / 2, 0, zone.oz + r + 0.5, 0);
    }
    // planks laid from the start
    Z.sites.forEach(function (s) { if (s.start) layPlank(Z, s, s.ends[0], true); });
  };

  /* ---------------- planks ---------------- */
  var PL = { w: 1.5, t: 0.08, overhang: 0.55 };
  function plankSpec(Z) { var O = opt(Z.theme).plank || {}; return { w: O.width || PL.w, t: O.thick || PL.t, oh: O.overhang === undefined ? PL.overhang : O.overhang, pieces: O.pieces || { 5: 'Plank_5', 7: 'Plank_7', 9: 'Plank_9' } }; }
  // geometry of a plank across site s: from the kerb top at end a to the kerb top at the other end
  function plankLine(Z, s, a) {
    var b = s.ends[0] === a ? s.ends[1] : s.ends[0], S = plankSpec(Z), kh = Z.kerbH;
    var ax = a.x, az = a.z, bx = b.x, bz = b.z, ay = a.h + kh, by = b.h + kh;
    var span = Math.hypot(bx - ax, bz - az), need = span + 2 * S.oh, L = 0, best = 1e9;
    Object.keys(S.pieces).forEach(function (k) { var n = +k; if (n >= need - 0.01 && n < best) { best = n; L = n; } });
    if (!L) { Object.keys(S.pieces).forEach(function (k) { L = Math.max(L, +k); }); }
    var ux = (bx - ax) / span, uz = (bz - az) / span;
    var oh = (L - span) / 2;
    return { a: a, b: b, ax: ax, ay: ay, az: az, bx: bx, by: by, bz: bz, span: span, L: L, oh: oh, ux: ux, uz: uz,
      yaw: Math.atan2(-uz, ux), pitch: Math.atan2(by - ay, span), piece: S.pieces[L], w: S.w, t: S.t };
  }
  // the plank's transform: its own frame has the board along local +X (centre at the origin, top face at y = t)
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(0, 0, 0, 'YZX'), _p = new THREE.Vector3(), _s = new THREE.Vector3(1, 1, 1), _off = new THREE.Matrix4();
  function poseMatrix(Ln, px, py, pz, pitch, along, out) {
    // pivot (px, py, pz) on the plank's underside, `along` m from its A end; tilted `pitch` (up toward B)
    _e.set(0, Ln.yaw, pitch); _q.setFromEuler(_e);
    out.compose(_p.set(px, py, pz), _q, _s);
    _off.makeTranslation(Ln.L / 2 - along, 0, 0);
    return out.multiply(_off);
  }
  function plankMesh(Z, Ln) {
    var A = IB.Assets, name = IB.themePiece(Z.theme, Ln.piece);
    var mesh = new THREE.Mesh(A.get(name), A.material(name));
    mesh.matrixAutoUpdate = false;
    Z.zone.group.add(mesh);
    return mesh;
  }
  // walkable boxes along a laid plank (stepped where the roofs differ in height), as wide as the board
  function plankBoxes(Z, Ln) {
    var world = Z.zone.world, out = [], dh = Ln.by - Ln.ay, total = Ln.span + 2 * Ln.oh;
    // short steps on a sloped board: two nav samples 0.5 m apart never differ by more than a robot's step
    var n = Math.abs(dh) < 0.01 ? 1 : Math.max(Math.ceil(Math.abs(dh) / 0.12), Math.ceil(total / 0.25));
    var x0 = Ln.ax - Ln.ux * Ln.oh, z0 = Ln.az - Ln.uz * Ln.oh, hw = Ln.w / 2;
    for (var k = 0; k < n; k++) {
      var s0 = total * k / n, s1 = total * (k + 1) / n, mid = (s0 + s1) / 2 - Ln.oh;
      var top = Ln.ay + Ln.t + dh * Math.max(0, Math.min(1, mid / Ln.span));
      var ax = x0 + Ln.ux * s0, az = z0 + Ln.uz * s0, bx = x0 + Ln.ux * s1, bz = z0 + Ln.uz * s1;
      var px = Math.abs(Ln.uz) * hw, pz = Math.abs(Ln.ux) * hw;
      var b = world.add(Math.min(ax, bx) - px, top - 0.3, Math.min(az, bz) - pz, Math.max(ax, bx) + px, top, Math.max(az, bz) + pz, 'deck', Z.zone.idx);
      b.walk = true; world.walkN++; b.plank = true;
      out.push(b);
    }
    return out;
  }
  function layPlank(Z, s, a, instant) {
    var Ln = plankLine(Z, s, a);
    s.laid = true; s.line = Ln;
    s.mesh = plankMesh(Z, Ln);
    if (instant) { finishPlank(Z, s, true); return; }
    s.anim = { t: 0, a: a, rx: s.by ? s.by.x : Ln.ax, ry: s.by ? s.by.y + 1.2 : Ln.ay + 1.2, rz: s.by ? s.by.z : Ln.az };
    poseAnim(Z, s);
  }
  var T_LIFT = 0.32, T_TIP = 0.62;
  function poseAnim(Z, s) {
    var Ln = s.line, A0 = s.anim, t = A0.t, M = s.mesh.matrix;
    if (t < T_LIFT) {   // thrown up: from the robot's hands to upright on the kerb, spinning up to vertical
      var k = t / T_LIFT, e = 1 - (1 - k) * (1 - k);
      var px = A0.rx + (Ln.ax - A0.rx) * e, pz = A0.rz + (Ln.az - A0.rz) * e, py = A0.ry + (Ln.ay - A0.ry) * e + Math.sin(k * Math.PI) * 0.8;
      poseMatrix(Ln, px, py, pz, (35 + 55 * e) * Math.PI / 180, 0, M);
    } else {            // kicked over: falls about its foot on the kerb, faster and faster, onto the far roof
      var k2 = Math.min(1, (t - T_LIFT) / T_TIP), th = Math.PI / 2 - (Math.PI / 2 - Ln.pitch) * k2 * k2;
      var along = Ln.oh * k2;   // the foot slides back over the kerb as it comes down (it ends with its overhang)
      poseMatrix(Ln, Ln.ax, Ln.ay, Ln.az, th, along, M);
    }
    s.mesh.matrixWorldNeedsUpdate = true;
  }
  function finishPlank(Z, s, quiet) {
    var Ln = s.line;
    poseMatrix(Ln, Ln.ax, Ln.ay, Ln.az, Ln.pitch, Ln.oh, s.mesh.matrix);
    s.mesh.matrixWorldNeedsUpdate = true;
    s.anim = null;
    s.boxes = plankBoxes(Z, Ln);
    // the kerbs under the board stop blocking (robots and the player walk onto it); the others stay
    var hw = Ln.w / 2 + 0.05;
    Z.kerbs.forEach(function (K) {
      var b = K.b, cx = (b.x0 + b.x1) / 2, cz = (b.z0 + b.z1) / 2;
      [Ln.a, Ln.b].forEach(function (e) {
        var near = s.alongZ ? Math.abs(cz - e.z) < 0.6 && b.x1 > e.x - hw && b.x0 < e.x + hw : Math.abs(cx - e.x) < 0.6 && b.z1 > e.z - hw && b.z0 < e.z + hw;
        if (near) b.on = false;
      });
    });
    if (!quiet) {
      if (IB.Zones && IB.Zones.rebuildNav) IB.Zones.rebuildNav(Z.zone);
      slamFx(Z, Ln);
    }
  }
  function slamFx(Z, Ln) {
    var mx = (Ln.ax + Ln.bx) / 2, mz = (Ln.az + Ln.bz) / 2;
    if (IB.Boom && IB.Boom.dustLine) IB.Boom.dustLine(Ln.ax, Ln.ay + 0.1, Ln.az, Ln.bx, Ln.by + 0.1, Ln.bz, Ln.w);
    else if (IB.FX) { IB.FX.puff(Ln.bx, Ln.by + 0.2, Ln.bz, 10, 0xE6DCC8, 0.25, 0.7, 2.5); IB.FX.puff(Ln.ax, Ln.ay + 0.2, Ln.az, 6, 0xE6DCC8, 0.25, 0.6, 2); }
    if (IB.Boom && IB.Boom.word) IB.Boom.word('WHAM!', Ln.bx, Ln.by + 1.1, Ln.bz, 1.7, true);
    if (IB.Audio) { IB.Audio.play('clank', { pos: { x: mx, z: mz }, gain: 1.2, pitch: 0.5 }); IB.Audio.play('land', { pos: { x: Ln.bx, z: Ln.bz }, gain: 1, pitch: 0.7 }); }
    var G = IB.Game;
    if (G && G.player && G.addTrauma) { var d = Math.hypot(G.player.x - mx, G.player.z - mz); if (d < 14) G.addTrauma(0.25 * (1 - d / 14)); }
  }

  /* ---------------- runtime ---------------- */
  function roofIdAt(Z, x, y, z) {
    var c = Math.floor(x - Z.zone.ox), r = Math.floor(z - Z.zone.oz);
    if (c < 0 || r < 0 || c >= Z.w || r >= Z.h) return -1;
    var i = r * Z.w + c;
    if (Z.kind[i] !== 1 || Math.abs(y - Z.hgt[i]) > 0.7) return -1;
    return Z.id[i];
  }
  R.roofIdAt = roofIdAt;
  function crewOf(Z) { var O = opt(Z.theme); return O.crew || ['soldier', 'gunner', 'blader', 'crawler', 'bomber']; }
  function rnd(a, b) { return a + Math.random() * (b - a); }
  R.update = function (dt, ctx) {
    var level = ctx.level; if (!level || !level.roofZones) return;
    var p = ctx.player, AI = IB.AI, VIS = AI.VIS || {};
    level.roofZones.forEach(function (Z) {
      var zi = Z.zone.idx, O = opt(Z.theme);
      // the player falls
      if (p.alive && p.y < Z.killY && p.x > Z.zone.ox && p.x < Z.zone.ox + Z.w && p.z > Z.zone.oz && p.z < Z.zone.oz + Z.h && IB.Game && IB.Game.fallDeath) IB.Game.fallDeath();
      // robots fall / flyers stay up
      AI.robots.forEach(function (r) {
        if (!r.on || r.zone !== zi || r.state === 'spawn' || r.state === 'pose') return;
        if (VIS[r.type] && VIS[r.type].flying) {
          var c = Math.floor(r.x - Z.zone.ox), rr = Math.floor(r.z - Z.zone.oz);
          if (c >= 0 && rr >= 0 && c < Z.w && rr < Z.h && Z.kind[rr * Z.w + c] === 0 && r.y < Z.flyFloor) r.y = Z.flyFloor;
          return;
        }
        if ((r.gy !== undefined ? r.gy : r.y) < Z.killY) { AI.kill(r, null, true); if (IB.Game && IB.Game.fallKill) IB.Game.fallKill(r); return; }
        if (r.state !== 'stagger') keepOnPlank(Z, r);   // a robot knocked about on a plank can go over the side
      });
      // plank animations
      Z.sites.forEach(function (s) {
        if (!s.anim) return;
        s.anim.t += dt;
        if (s.anim.t >= T_LIFT + T_TIP) finishPlank(Z, s, false); else poseAnim(Z, s);
      });
      // robots throw planks
      Z.gapT -= dt;
      if (Z.zone.state !== 'active' || ctx.activeZone !== zi || Z.gapT > 0) return;
      var crew = crewOf(Z), reach = O.reach || 4.5, pr = roofIdAt(Z, p.x, p.y, p.z), D = O.delay || [1.5, 3.5];
      for (var si = 0; si < Z.sites.length; si++) {
        var s = Z.sites[si]; if (s.laid) continue;
        var who = null, from = null;
        for (var ei = 0; ei < 2 && !who; ei++) {
          var e = s.ends[ei];
          if (e.roof === pr) continue;   // the player stands on this roof already: nothing to cross toward
          for (var k = 0; k < AI.robots.length; k++) {
            var r = AI.robots[k];
            if (!r.on || r.zone !== zi || crew.indexOf(r.type) < 0 || r.state === 'spawn' || r.state === 'pose' || r.state === 'idle' || r.rogue > 0) continue;
            if (Math.abs((r.fy || 0) - e.h) > 0.6 || Math.hypot(r.x - e.x, r.z - e.z) > reach) continue;
            who = r; from = e; break;
          }
        }
        if (!who) { s.t = Math.max(0, s.t - dt); continue; }
        if (!s.wait) s.wait = rnd(D[0], D[1]);
        s.t += dt;
        if (s.t < s.wait) continue;
        s.by = { x: who.x, y: who.fy || 0, z: who.z };
        layPlank(Z, s, from, false);
        Z.gapT = O.gap === undefined ? 4 : O.gap;
        break;
      }
    });
  };
  // a ground robot crossing a plank keeps its feet on the board (its strafing and dodging run along it): over open air
  // next to a laid plank, it is pulled back inside the board's width
  function keepOnPlank(Z, r) {
    var c = Math.floor(r.x - Z.zone.ox), rr = Math.floor(r.z - Z.zone.oz);
    if (c < 0 || rr < 0 || c >= Z.w || rr >= Z.h || Z.kind[rr * Z.w + c] === 1 && Z.hgt[rr * Z.w + c] === 0) return;
    for (var i = 0; i < Z.sites.length; i++) {
      var s = Z.sites[i], Ln = s.line; if (!s.laid || s.anim || !Ln) continue;
      var dx = r.x - Ln.ax, dz = r.z - Ln.az, along = dx * Ln.ux + dz * Ln.uz, side = -dx * Ln.uz + dz * Ln.ux;
      if (along < -0.2 || along > Ln.span + 0.2 || Math.abs(side) > Ln.w / 2 + 0.7) continue;
      var lim = Ln.w / 2 - 0.25;
      if (Math.abs(side) > lim) {
        var k = (Math.abs(side) - lim) * (side > 0 ? 1 : -1);
        r.x += Ln.uz * k; r.z -= Ln.ux * k;
      }
      return;
    }
  }
  // a restart of the level: planks back to their start state
  R.reset = function (level) {
    (level && level.roofZones || []).forEach(function (Z) {
      var rebuilt = false;
      Z.sites.forEach(function (s) {
        if (!s.laid || s.start) return;
        if (s.mesh && s.mesh.parent) s.mesh.parent.remove(s.mesh);
        (s.boxes || []).forEach(function (b) { b.on = false; b.walk = false; });
        s.laid = false; s.anim = null; s.mesh = null; s.boxes = null; s.t = 0; s.wait = 0; rebuilt = true;
      });
      Z.kerbs.forEach(function (K) { K.b.on = true; });
      Z.sites.forEach(function (s) { if (s.laid && s.start) finishKerbs(Z, s); });
      Z.gapT = 0;
      if (rebuilt && IB.Zones && IB.Zones.rebuildNav) IB.Zones.rebuildNav(Z.zone);
    });
  };
  function finishKerbs(Z, s) {
    var Ln = s.line, hw = Ln.w / 2 + 0.05;
    Z.kerbs.forEach(function (K) {
      var b = K.b, cx = (b.x0 + b.x1) / 2, cz = (b.z0 + b.z1) / 2;
      [Ln.a, Ln.b].forEach(function (e) {
        var near = s.alongZ ? Math.abs(cz - e.z) < 0.6 && b.x1 > e.x - hw && b.x0 < e.x + hw : Math.abs(cx - e.x) < 0.6 && b.z1 > e.z - hw && b.z0 < e.z + hw;
        if (near) b.on = false;
      });
    });
  }
  // test hook: lay the plank of site i from its end e (0 / 1) now, with the full animation
  R.forceLay = function (level, zi, i, e) {
    var Z = (level.roofZones || []).filter(function (q) { return q.zone.idx === zi; })[0];
    if (!Z || !Z.sites[i] || Z.sites[i].laid) return false;
    var s = Z.sites[i]; s.by = null; layPlank(Z, s, s.ends[e || 0], false); return true;
  };
  R.info = function (level) {
    return (level && level.roofZones || []).map(function (Z) {
      return { zone: Z.zone.idx, killY: Z.killY, voidY: Z.voidY, sites: Z.sites.map(function (s) {
        return { laid: s.laid, start: s.start, anim: !!s.anim, ends: s.ends.map(function (e) { return { x: e.x, z: e.z, h: e.h, roof: e.roof }; }) };
      }) };
    });
  };
})(window.IB = window.IB || {});
