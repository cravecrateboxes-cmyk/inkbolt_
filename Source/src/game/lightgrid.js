/* INKBOLT light volume (tactical look, Stage 4). The lamps that are modelled in a map become its lights: no theme
   data is needed, so every map (and every future map) is lit by its own fittings.
   1. Emitters (collect): every triangle of a merged kit mesh painted with an emissive palette cell
      (IB.SURFACES[fam].emit > 0), every face of the zone's glow companions (lamp lenses often exist only there;
      *_Blink pieces at half strength), trails and the hatch room. Merged on a 1.6 m hash: area-weighted position
      and colour. Strength = min(2.2, area * 2.4) * class weight * look.grid.emit[cell]. At most 256 per zone.
   2. Volume (bake): one level-wide grid, 1 m cells in X/Z, Y slices at 0.9 m then every 2.6 m (at most 6).
      Cell = sum of strength * colour * 9 / (1 + d^2) * (1 - d / radius), x0.12 when the sight line is blocked.
      Solid cells are filled from open neighbours; 3x3 blur per slice. Alpha = sky visibility, from the drawn
      geometry (a top-down depth render of each zone; roofs and awnings are often visual only), 5x5 blur.
      Stored as a 2D atlas of the slices (RGBA8, rgb = sqrt(light / 4)), sampled with manual slice interpolation
      (works on WebGL1 and WebGL2 alike).
   3. Time-sliced: the starting zone bakes during the loading screen, the others at most 4 ms a frame.
   CPU twin: sampleAt(x, y, z) for the viewmodel light link. */
(function (IB) {
  'use strict';
  var LG = IB.LightGrid = { ready: false, stats: [] };
  var CELL = 1.6, RAD = 13, SLICE0 = 0.9, SLICE_DY = 2.6, MAX_SLICES = 6, CAP = 256, BUDGET_MS = 3;   // 3 ms of work plus at most one unit (< 2 ms measured) stays under the 6 ms gate
  var V = null;   // { ox, oz, W, H, n, y0, data (Float32 rgb+a per cell), tex, bytes, zones: [...] }
  var queue = [], famOf = null;

  function luma(c) { return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; }
  function hexRgb(h) { return [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]; }

  // ---------------- 1. emitters ----------------
  function addTris(hash, geo, mtx, fam, all, mult, look) {
    var T = IB.SURFACES[fam]; if (!T) return;
    var pos = geo.attributes.position, uv = geo.attributes.uv; if (!uv) return;
    var idx = geo.index ? geo.index.array : null, n = idx ? idx.length : pos.count;
    var P = pos.array, UV = uv.array, ov = (look && look.grid && look.grid.emit) || {};
    var e = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    for (var t = 0; t < n; t += 3) {
      var i0 = idx ? idx[t] : t, i1 = idx ? idx[t + 1] : t + 1, i2 = idx ? idx[t + 2] : t + 2;
      var cell = Math.min(7, Math.floor(UV[i0 * 2] * 8)) + 8 * Math.min(7, Math.floor((1 - UV[i0 * 2 + 1]) * 8));
      if (cell >= T.cls.length) continue;
      // glow companions: emissive cells at their weight, other painted faces (lenses in plain colours) at 0.5;
      // glass and water faces are reflections, not lights (metro's glass companions)
      var cl = T.cls[cell];
      var w = all ? (cl === 15 ? T.emit[cell] : cl === 11 || cl === 14 ? 0 : 0.5) : T.emit[cell];
      if (!(w > 0)) continue;
      if (ov[T.names[cell]] !== undefined) w *= ov[T.names[cell]];
      a.set(P[i0 * 3], P[i0 * 3 + 1], P[i0 * 3 + 2]); b.set(P[i1 * 3], P[i1 * 3 + 1], P[i1 * 3 + 2]); c.set(P[i2 * 3], P[i2 * 3 + 1], P[i2 * 3 + 2]);
      if (mtx) { a.applyMatrix4(mtx); b.applyMatrix4(mtx); c.applyMatrix4(mtx); }
      b.sub(a); c.sub(a); e.crossVectors(b, c);
      var area = e.length() / 2; if (area < 1e-5) continue;
      var mx = a.x + (b.x + c.x) / 3, my = a.y + (b.y + c.y) / 3, mz = a.z + (b.z + c.z) / 3;
      var key = Math.floor(mx / CELL) + ',' + Math.floor(my / CELL) + ',' + Math.floor(mz / CELL), E = hash.get(key);
      if (!E) { E = { x: 0, y: 0, z: 0, a: 0, r: 0, g: 0, b: 0, w: 0, ny: 0, lamp: 0 }; hash.set(key, E); }
      var col = hexRgb(T.col[cell]), k = area * w * mult;
      var sk = fam + ':' + T.names[cell] + (all ? '*' : ''); LG.cellStats[sk] = (LG.cellStats[sk] || 0) + k;   // diagnostics: light per cell
      E.ny += (e.y / (2 * area)) * k; if (T.names[cell] && /^(lamp|light|bulb|sodium|lit)/i.test(T.names[cell])) E.lamp += k;   // facing (lamp cones)
      E.x += mx * k; E.y += my * k; E.z += mz * k; E.a += area * mult; E.w += k; E.r += col[0] * k; E.g += col[1] * k; E.b += col[2] * k;
    }
  }
  function famMap() {
    var A = IB.Assets, m = new Map();
    Object.keys(A.mat).forEach(function (f) { m.set(A.mat[f], f); });
    return m;
  }
  function collectGroup(hash, group, look, skip) {
    group.updateMatrixWorld(true);
    group.traverse(function (o) {
      if (!o.isMesh || !o.geometry || (skip && skip.has(o))) return;
      var fam = famOf.get(o.material);
      if (fam) addTris(hash, o.geometry, o.matrixWorld, fam, false, 1, look);
    });
  }
  function finish(hash) {
    var out = [];
    hash.forEach(function (E) {
      if (E.w < 1e-4) return;
      var s = Math.min(2.2, E.a * 2.4) * (E.w / E.a);
      out.push({ x: E.x / E.w, y: E.y / E.w, z: E.z / E.w, s: s, r: E.r / E.w, g: E.g / E.w, b: E.b / E.w, ny: E.ny / E.w, lamp: E.lamp / E.w });
    });
    out.sort(function (p, q) { return q.s - p.s; });
    return out.slice(0, CAP);
  }
  LG.cellStats = {};
  LG.collect = function (level, look) {
    famOf = famMap(); LG.cellStats = {};
    var zones = level.zones.map(function (zone, zi) {
      var hash = new Map(), glowSet = new Set();
      (level.glows || []).forEach(function (g) {
        if (g.zone !== zi || !g.mesh || /Glass$/i.test(g.piece || '')) return;   // glass companions are not lights
        glowSet.add(g.mesh);
        var fam = null, map = g.mesh.material && g.mesh.material.map;
        famOf.forEach(function (f, m) { if (!fam && m.map === map) fam = f; });
        if (!fam) return;
        g.mesh.updateMatrixWorld(true);
        addTris(hash, g.mesh.geometry, g.mesh.matrixWorld, fam, true, /_Blink$/.test(g.piece || '') ? 0.5 : 1, look);
      });
      collectGroup(hash, zone.group, look, glowSet);
      return finish(hash);
    });
    var extra = new Map();
    (level.trails || []).forEach(function (t) { collectGroup(extra, t.group, look); });
    if (level.hatch) collectGroup(extra, level.hatch.group, look);
    return { zones: zones, extra: finish(extra) };
  };

  // ---------------- 2. sky visibility from the drawn geometry ----------------
  var skyRT = null, skyCam = null;
  function topHeights(level, zone, R) {
    var W = Math.ceil(zone.w * 2), H = Math.ceil(zone.h * 2), r = R.renderer;
    if (!skyRT || skyRT.width !== W || skyRT.height !== H) {
      if (skyRT) skyRT.dispose();
      skyRT = new THREE.WebGLRenderTarget(W, H, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, format: THREE.RGBAFormat, type: THREE.UnsignedByteType });
    }
    var TOP = 300, FAR = 600;
    skyCam = skyCam || new THREE.OrthographicCamera(-1, 1, 1, -1, 0, FAR);
    skyCam.left = -zone.w / 2; skyCam.right = zone.w / 2; skyCam.top = zone.h / 2; skyCam.bottom = -zone.h / 2; skyCam.near = 0; skyCam.far = FAR;
    skyCam.position.set(zone.ox + zone.w / 2, TOP, zone.oz + zone.h / 2); skyCam.up.set(0, 0, -1); skyCam.lookAt(zone.ox + zone.w / 2, 0, zone.oz + zone.h / 2);
    skyCam.updateProjectionMatrix(); skyCam.updateMatrixWorld();
    var sc = R.scene, vis = [], prevOverride = sc.overrideMaterial, prevTarget = r.getRenderTarget(), cc = new THREE.Color(), ca = r.getClearAlpha();
    r.getClearColor(cc);
    sc.children.forEach(function (o) { vis.push(o.visible); if (o !== level.root) o.visible = false; });
    var rvis = level.root.children.map(function (o) { return o.visible; });   // only this zone's own geometry
    level.root.children.forEach(function (o) { o.visible = o === zone.group; });
    var fog = sc.fog; sc.fog = null;
    sc.overrideMaterial = IB.Shadows.depthMat(false);
    r.setClearColor(0x000000, 1); r.setRenderTarget(skyRT); r.clear(true, true, true);
    r.render(sc, skyCam);
    var px = new Uint8Array(W * H * 4);
    r.readRenderTargetPixels(skyRT, 0, 0, W, H, px);
    sc.overrideMaterial = prevOverride; sc.fog = fog;
    sc.children.forEach(function (o, i) { o.visible = vis[i]; });
    level.root.children.forEach(function (o, i) { o.visible = rvis[i]; });
    r.setRenderTarget(prevTarget); r.setClearColor(cc, ca);
    // unpack (three packDepthToRGBA) -> height of the topmost surface; rows: y = 0 is the camera's bottom (+z side)
    var out = new Float32Array(W * H), k = 255 / 256;
    for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
      var o = (j * W + i) * 4;
      var d = (px[o] / 255 / 16777216 + px[o + 1] / 255 / 65536 + px[o + 2] / 255 / 256 + px[o + 3] / 255) * k;
      out[(H - 1 - j) * W + i] = d > 0.995 ? -1e9 : TOP - d * FAR;   // row 0 = the zone's -z edge
    }
    return { W: W, H: H, h: out };
  }

  // ---------------- 3. the volume ----------------
  function zoneOf(level, x, z) {
    for (var i = 0; i < level.zones.length; i++) { var Zn = level.zones[i]; if (x >= Zn.ox && x < Zn.ox + Zn.w && z >= Zn.oz && z < Zn.oz + Zn.h) return i; }
    return -1;
  }
  LG.begin = function (level, look) {
    LG.end();
    var t0 = performance.now(); LG.maxSliceMs = 0; LG.maxFrameMs = 0; LG.unitMax = {}; LG.unitHist = null;
    var em = LG.collect(level, look);
    // bounds: zones + trails + hatch
    var x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9, ymax = 0;
    level.zones.forEach(function (Zn) {
      x0 = Math.min(x0, Zn.ox); z0 = Math.min(z0, Zn.oz); x1 = Math.max(x1, Zn.ox + Zn.w); z1 = Math.max(z1, Zn.oz + Zn.h);
      if (Zn.nav && Zn.nav.h) for (var i = 0; i < Zn.nav.h.length; i++) ymax = Math.max(ymax, Zn.nav.h[i]);
    });
    var bb = new THREE.Box3();
    (level.trails || []).concat(level.hatch ? [level.hatch] : []).forEach(function (t) {
      bb.setFromObject(t.group); if (bb.isEmpty()) return;
      x0 = Math.min(x0, bb.min.x); z0 = Math.min(z0, bb.min.z); x1 = Math.max(x1, bb.max.x); z1 = Math.max(z1, bb.max.z);
    });
    x0 = Math.floor(x0) - 2; z0 = Math.floor(z0) - 2; x1 = Math.ceil(x1) + 2; z1 = Math.ceil(z1) + 2;
    var W = x1 - x0, H = z1 - z0, n = Math.max(1, Math.min(MAX_SLICES, Math.ceil((ymax + 2 - SLICE0) / SLICE_DY) + 1));
    var env = (level.theme || {}).env || {};
    var sky0 = env.sky ? 1 : 0;
    V = { ox: x0, oz: z0, W: W, H: H, n: n, y0: SLICE0, data: new Float32Array(W * H * n * 4), bytes: new Uint8Array(W * H * n * 4), em: em, level: level, look: look, done: {} };
    // until a zone is baked: a flat low light and the theme's sky flag
    for (var c = 0; c < W * H * n; c++) { V.data[c * 4 + 3] = sky0; V.bytes[c * 4] = V.bytes[c * 4 + 1] = V.bytes[c * 4 + 2] = 0; V.bytes[c * 4 + 3] = sky0 * 255; }
    // every emitter is looked up from a 13 m bucket hash
    V.lights = em.zones.reduce(function (a, l) { return a.concat(l); }, []).concat(em.extra);
    V.bucket = new Map();
    V.lights.forEach(function (L, i) {
      var bx = Math.floor(L.x / RAD), bz = Math.floor(L.z / RAD), key = bx + ',' + bz;
      (V.bucket.get(key) || V.bucket.set(key, []).get(key)).push(i);
    });
    var tex = new THREE.DataTexture(V.bytes, W, H * n, THREE.RGBAFormat);
    tex.magFilter = tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false; tex.flipY = false;
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping; tex.needsUpdate = true;
    V.tex = tex;
    var U = IB.Look.U;
    U.uGrid.value = tex; U.uGridO.value.set(x0, z0, 1 / W, 1 / H); U.uGridY.value.set(SLICE0, SLICE_DY, n, 0.5 / H);
    U.uGridI.value = look.grid.intensity; U.uGridOn.value = 1;
    LG.stats = em.zones.map(function (l, i) { return { zone: i, lights: l.length, ms: 0 }; });
    LG.collectMs = performance.now() - t0;
    // queue every zone (the start zone first, baked now: the loading screen covers it)
    queue = level.zones.map(function (_, i) { return i; });
    // sky visibility needs a GPU render and a read-back per zone (a pipeline stall): all zones now, under the loader,
    // so the time-sliced bake during play is CPU work only
    var ts = performance.now(); V.tops = level.zones.map(function (Zn) { return skyTopOf(level, Zn); });
    LG.skyMs = Math.round(performance.now() - ts);
    LG.ready = true;
    return V;
  };
  LG.prioritise = function (zi) {
    var k = queue.indexOf(zi); if (k > 0) { queue.splice(k, 1); queue.unshift(zi); }
    if (zi + 1 < (V ? V.level.zones.length : 0)) { var k2 = queue.indexOf(zi + 1); if (k2 > 1) { queue.splice(k2, 1); queue.splice(1, 0, zi + 1); } }
  };

  // one zone's job: rows of cells over its rect (+2 m margin), all slices; then sky, fill, blur, upload
  function job(zi) {
    var level = V.level, Zn = level.zones[zi], world = level.world;
    var i0 = Math.max(0, Math.floor(Zn.ox - V.ox) - 2), i1 = Math.min(V.W, Math.ceil(Zn.ox + Zn.w - V.ox) + 2);
    var j0 = Math.max(0, Math.floor(Zn.oz - V.oz) - 2), j1 = Math.min(V.H, Math.ceil(Zn.oz + Zn.h - V.oz) + 2);
    return { zi: zi, Zn: Zn, world: world, i0: i0, i1: i1, j0: j0, j1: j1, s: 0, j: j0, ms: 0, phase: 'light' };
  }
  var cur = null;
  function unit(ph, t0) {
    var d = performance.now() - t0, U = LG.unitMax || (LG.unitMax = {}); if (!(U[ph] >= d)) U[ph] = +d.toFixed(1);
    var Hh = LG.unitHist || (LG.unitHist = { n: 0, over2: 0, over6: 0 }); Hh.n++; if (d > 2) Hh.over2++; if (d > 6) Hh.over6++;
  }
  function cellLight(x, y, z, world, out) {
    var r = 0, g = 0, b = 0, bx = Math.floor(x / RAD), bz = Math.floor(z / RAD);
    for (var dx = -1; dx <= 1; dx++) for (var dz = -1; dz <= 1; dz++) {
      var list = V.bucket.get((bx + dx) + ',' + (bz + dz)); if (!list) continue;
      for (var k = 0; k < list.length; k++) {
        var L = V.lights[list[k]], ex = L.x - x, ez = L.z - z, ey = L.y - y, d2 = ex * ex + ez * ez;
        if (d2 > RAD * RAD) continue;
        var dd = d2 + Math.max(0.36, ey * ey), d = Math.sqrt(dd);
        if (d >= RAD) continue;
        var I = L.s * 9 / (1 + dd) * (1 - d / RAD);
        if (I < 0.004) continue;
        if (world && !world.los(x, y, z, L.x, L.y - Math.sign(ey) * 0.25, L.z)) I *= 0.12;
        r += L.r * I; g += L.g * I; b += L.b * I;
      }
    }
    out[0] = r; out[1] = g; out[2] = b;
  }
  var _o = [0, 0, 0];
  // every phase checks the deadline between small units (one cell, one band of rows), so a frame never runs far over budget
  function step(J, deadline) {
    var Zn = J.Zn;
    while (J.phase === 'light') {
      if (performance.now() > deadline) return false;
      var tl = performance.now(), y = V.y0 + J.s * SLICE_DY, base = J.s * V.W * V.H, iEnd = Math.min(J.i1, (J.i === undefined ? J.i0 : J.i) + 1);
      for (var i = J.i === undefined ? J.i0 : J.i; i < iEnd; i++) {
        var x = V.ox + i + 0.5, z = V.oz + J.j + 0.5, c = (base + J.j * V.W + i) * 4;
        var zi = zoneOf(V.level, x, z);
        if (zi >= 0 && zi !== J.zi) continue;   // another zone's cell: its own job bakes it
        cellLight(x, y, z, J.world, _o);
        V.data[c] = _o[0]; V.data[c + 1] = _o[1]; V.data[c + 2] = _o[2];
      }
      J.i = iEnd; unit('light', tl);
      if (J.i >= J.i1) { J.i = J.i0; if (++J.j >= J.j1) { J.j = J.j0; if (++J.s >= V.n) { J.phase = 'skyTop'; J.s = 0; } } }
    }
    if (J.phase === 'skyTop') {
      if (performance.now() > deadline) return false;
      var t0 = performance.now(); skyTop(J); J.skyMs = performance.now() - t0; J.phase = 'sky';
    }
    while (J.phase === 'sky') {
      if (performance.now() > deadline) return false;
      var tq = performance.now(), dq = skySlice(J, J.s); unit('sky', tq);
      if (dq && ++J.s >= V.n) { J.s = 0; J.phase = 'post'; }
    }
    while (J.phase === 'post') {
      if (performance.now() > deadline) return false;
      var tp = performance.now(), dp = postSlice(J, J.s); unit('post', tp);
      if (dp && ++J.s >= V.n) J.phase = 'upload';
    }
    if (J.phase === 'upload') {
      if (performance.now() > deadline) return false;
      V.tex.needsUpdate = true;
      V.done[J.zi] = true;
      return true;
    }
    return true;
  }
  function engineCeilOf(level, Zn) { var env = (level.theme || {}).env || {}; return !!(env.ceiling && (!Zn.plan || Zn.plan.ceiling !== false)); }   // zones.js addCeiling
  function skyTopOf(level, Zn) {
    var env = (level.theme || {}).env || {};
    if (!env.sky || engineCeilOf(level, Zn)) return null;
    try { return topHeights(level, Zn, IB.Render); } catch (e) { return null; }
  }
  function skyTop(J) {
    J.engineCeil = engineCeilOf(V.level, J.Zn); J.open = 0; J.total = 0;
    J.top = V.tops ? V.tops[J.zi] : skyTopOf(V.level, J.Zn);
  }
  /* Sky and post passes run in bands of BAND rows (each call does one band and returns true when the slice is done),
     so no single unit of work takes more than a couple of milliseconds. */
  var BAND = 10;
  function band(J, sub) {   // rows [r0, r1) of the current band of sub-pass `sub`; advances; null when the sub-pass is done
    if (J.sub !== sub) { J.sub = sub; J.row = J.j0; }
    if (J.row >= J.j1) return null;
    var r0 = J.row; J.row = Math.min(J.j1, J.row + BAND); return [r0, J.row];
  }
  function skySlice(J, s) {
    var level = V.level, Zn = J.Zn, env = (level.theme || {}).env || {}, engineCeil = J.engineCeil, top = J.top;
    var W = V.W, y = V.y0 + s * SLICE_DY, base = s * W * V.H, w2 = J.i1 - J.i0, h2 = J.j1 - J.j0, i, j, R;
    if (J.sub === undefined || J.sub < 0) { J.tmp = new Float32Array(w2 * h2); J.sub = -1; }
    if (J.sub <= 0 && (R = band(J, 0))) {
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) {
        var x = V.ox + i + 0.5, z = V.oz + j + 0.5, v = 0;
        if (env.sky && !engineCeil) {
          if (top) {
            var ti = Math.floor((x - Zn.ox) * 2), tj = Math.floor((z - Zn.oz) * 2);
            if (ti < 0 || tj < 0 || ti >= top.W || tj >= top.H) v = 1;
            else { var hmax = Math.max(top.h[tj * top.W + ti], ti + 1 < top.W ? top.h[tj * top.W + ti + 1] : -1e9, tj + 1 < top.H ? top.h[(tj + 1) * top.W + ti] : -1e9); v = hmax <= y + 0.5 ? 1 : 0; }
          } else v = 1;
        }
        J.tmp[(j - J.j0) * w2 + (i - J.i0)] = v;
        if (s === 0) { J.total++; J.open += v; }
      }
      return false;
    }
    // 5x5 blur; a mostly open zone never drops below 0.25 (colonnades, awnings keep partial sky light)
    if ((R = band(J, 1))) {
      var floorV = J.total && J.open / J.total > 0.4 ? 0.25 : 0, tmp = J.tmp;
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) {
        var zi = zoneOf(V.level, V.ox + i + 0.5, V.oz + j + 0.5);
        if (zi >= 0 && zi !== J.zi) continue;
        var sum = 0, cnt = 0;
        for (var dj = -2; dj <= 2; dj++) for (var di = -2; di <= 2; di++) {
          var ii = i + di - J.i0, jj = j + dj - J.j0;
          if (ii < 0 || jj < 0 || ii >= w2 || jj >= h2) continue;
          sum += tmp[jj * w2 + ii]; cnt++;
        }
        V.data[(base + j * W + i) * 4 + 3] = Math.max(floorV * (env.sky && !engineCeil ? 1 : 0), cnt ? sum / cnt : 0);
      }
      return false;
    }
    J.sub = -1; J.tmp = null;
    return true;
  }
  function postSlice(J, s) {
    var W = V.W, H = V.H, Zn = J.Zn, Z = IB.Zones, base = s * W * H, w2 = J.i1 - J.i0, h2 = J.j1 - J.j0, i, j, ch, R;
    if (J.sub === undefined || J.sub < 0) { J.mask = new Uint8Array(w2 * h2); J.ptmp = new Float32Array(w2 * h2 * 3); J.sub = -1; }
    var mask = J.mask;
    // 0: which cells are solid
    if (J.sub <= 0 && (R = band(J, 0))) {
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) {
        var x = V.ox + i + 0.5, z = V.oz + j + 0.5;
        if (x >= Zn.ox && x < Zn.ox + Zn.w && z >= Zn.oz && z < Zn.oz + Zn.h && !Z.isOpen(Zn, x, z)) mask[(j - J.j0) * w2 + (i - J.i0)] = 1;
      }
      return false;
    }
    // 1: solid cells take the mean of their open neighbours (bilinear filtering must not pull darkness out of walls)
    if (J.sub <= 1 && (R = band(J, 1))) {
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) {
        if (!mask[(j - J.j0) * w2 + (i - J.i0)]) continue;
        var r = 0, g = 0, b = 0, n = 0;
        for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++) {
          var ii = i + di, jj = j + dj; if (ii < 0 || jj < 0 || ii >= W || jj >= H) continue;
          if (ii >= J.i0 && ii < J.i1 && jj >= J.j0 && jj < J.j1 && mask[(jj - J.j0) * w2 + (ii - J.i0)]) continue;
          var o = (base + jj * W + ii) * 4; r += V.data[o]; g += V.data[o + 1]; b += V.data[o + 2]; n++;
        }
        if (n) { var o2 = (base + j * W + i) * 4; V.data[o2] = r / n; V.data[o2 + 1] = g / n; V.data[o2 + 2] = b / n; }
      }
      return false;
    }
    // 2: 3x3 blur of the light (centre weight 2)
    if (J.sub <= 2 && (R = band(J, 2))) {
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) for (ch = 0; ch < 3; ch++) {
        var sum = 0, cnt = 0;
        for (dj = -1; dj <= 1; dj++) for (di = -1; di <= 1; di++) {
          ii = i + di; jj = j + dj; if (ii < J.i0 || jj < J.j0 || ii >= J.i1 || jj >= J.j1) continue;
          var wgt = (di === 0 && dj === 0) ? 2 : 1; sum += V.data[(base + jj * W + ii) * 4 + ch] * wgt; cnt += wgt;
        }
        J.ptmp[((j - J.j0) * w2 + (i - J.i0)) * 3 + ch] = sum / cnt;
      }
      return false;
    }
    // 3: encode
    if ((R = band(J, 3))) {
      for (j = R[0]; j < R[1]; j++) for (i = J.i0; i < J.i1; i++) {
        var zi = zoneOf(V.level, V.ox + i + 0.5, V.oz + j + 0.5);
        if (zi >= 0 && zi !== J.zi) continue;
        var c = (base + j * W + i) * 4;
        for (ch = 0; ch < 3; ch++) {
          var v = J.ptmp[((j - J.j0) * w2 + (i - J.i0)) * 3 + ch];
          V.data[c + ch] = v; V.bytes[c + ch] = Math.round(Math.sqrt(Math.min(1, v / 4)) * 255);
        }
        V.bytes[c + 3] = Math.round(Math.max(0, Math.min(1, V.data[c + 3])) * 255);
      }
      return false;
    }
    J.sub = -1; J.mask = null; J.ptmp = null;
    return true;
  }

  // per frame: bake for at most BUDGET_MS (or everything for `all`)
  LG.work = function (budgetMs) {
    if (!V) return true;
    var t0 = performance.now(), deadline = t0 + (budgetMs === undefined ? BUDGET_MS : budgetMs);
    while (performance.now() < deadline) {
      if (!cur) { if (!queue.length) return true; cur = job(queue.shift()); }
      var a = performance.now(), fin = step(cur, deadline);
      cur.ms += performance.now() - a;
      if (fin) { LG.stats[cur.zi].ms = Math.round(cur.ms); LG.stats[cur.zi].skyMs = Math.round(cur.skyMs || 0); cur = null; }
    }
    var dt = performance.now() - t0;
    LG.maxSliceMs = Math.max(LG.maxSliceMs || 0, dt);
    if (budgetMs === undefined) LG.maxFrameMs = Math.max(LG.maxFrameMs || 0, dt); // per-frame slices only (gate: 6 ms)
    return !cur && !queue.length;
  };
  LG.idle = function () { return !V || (!cur && !queue.length); };
  LG.bakeZoneNow = function (zi) { LG.prioritise(zi); var guard = 0; while (!(V && V.done[zi]) && guard++ < 1e4) LG.work(50); };

  // CPU sample (viewmodel link): { local: [r, g, b] linear light, sky: 0..1 }
  LG.sampleAt = function (x, y, z) {
    if (!V) return null;
    var fx = x - V.ox - 0.5, fz = z - V.oz - 0.5, fy = Math.max(0, Math.min(V.n - 1, (y - V.y0) / SLICE_DY));
    var i0 = Math.max(0, Math.min(V.W - 1, Math.floor(fx))), j0 = Math.max(0, Math.min(V.H - 1, Math.floor(fz))), s0 = Math.floor(fy);
    var i1 = Math.min(V.W - 1, i0 + 1), j1 = Math.min(V.H - 1, j0 + 1), s1 = Math.min(V.n - 1, s0 + 1);
    var tx = Math.max(0, Math.min(1, fx - i0)), tz = Math.max(0, Math.min(1, fz - j0)), ty = fy - s0, out = [0, 0, 0, 0];
    for (var ch = 0; ch < 4; ch++) {
      var v = 0;
      [[s0, 1 - ty], [s1, ty]].forEach(function (S) {
        var b = S[0] * V.W * V.H, d = V.data;
        var a0 = d[(b + j0 * V.W + i0) * 4 + ch] * (1 - tx) + d[(b + j0 * V.W + i1) * 4 + ch] * tx;
        var a1 = d[(b + j1 * V.W + i0) * 4 + ch] * (1 - tx) + d[(b + j1 * V.W + i1) * 4 + ch] * tx;
        v += (a0 * (1 - tz) + a1 * tz) * S[1];
      });
      out[ch] = v;
    }
    return { local: [out[0], out[1], out[2]], sky: out[3] };
  };

  LG.end = function () {
    if (V && V.tex) V.tex.dispose();
    V = null; queue = []; cur = null; LG.ready = false; LG.maxSliceMs = 0;
    if (IB.Look && IB.Look.U) { IB.Look.U.uGridOn.value = 0; IB.Look.U.uGrid.value = null; }
  };
  LG.lights = function () { return V ? V.lights : []; };
  LG.info = function () { return V ? { W: V.W, H: V.H, n: V.n, lights: V.lights.length, zones: LG.stats, collectMs: Math.round(LG.collectMs), maxSliceMs: +(LG.maxSliceMs || 0).toFixed(1), maxFrameMs: +(LG.maxFrameMs || 0).toFixed(1), unitMax: LG.unitMax || {}, unitHist: LG.unitHist || null, skyMs: LG.skyMs } : null; };
})(window.IB = window.IB || {});
