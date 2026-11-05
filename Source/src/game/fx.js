/* INKBOLT effects: decal atlas + instanced decals (ring buffer), ink puff particles, scrap chunks,
   tracers, blob shadows, gems. All pooled at load; no allocation in the hot loop. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var FX = IB.FX = {};
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _v = new THREE.Vector3(), _s = new THREE.Vector3(), _n = new THREE.Vector3(), _z = new THREE.Vector3(0, 0, 1), _c = new THREE.Color();
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0), _e = new THREE.Euler();

  // ---------- decal atlas: 4x4 cells of 128 px ----------
  function rngFrom(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function drawSplat(ctx, cx, cy, R, seed, color) {
    var r = rngFrom(seed);
    ctx.fillStyle = color;
    ctx.beginPath();
    var n = 14 + Math.floor(r() * 6);
    for (var i = 0; i <= n; i++) {
      var a = i / n * Math.PI * 2, rr = R * (0.55 + r() * 0.3);
      if (r() < 0.3) rr = R * (0.8 + r() * 0.2);
      var x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr;
      if (i === 0) ctx.moveTo(x, y); else ctx.quadraticCurveTo(cx + Math.cos(a - Math.PI / n) * rr * 1.1, cy + Math.sin(a - Math.PI / n) * rr * 1.1, x, y);
    }
    ctx.fill();
    // spikes + droplets
    for (var k = 0; k < 7; k++) {
      var b = r() * Math.PI * 2, d0 = R * 0.5, d1 = R * (0.9 + r() * 0.25), w = R * (0.06 + r() * 0.06);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(b + 0.25) * d0, cy + Math.sin(b + 0.25) * d0);
      ctx.lineTo(cx + Math.cos(b) * d1, cy + Math.sin(b) * d1);
      ctx.lineTo(cx + Math.cos(b - 0.25) * d0, cy + Math.sin(b - 0.25) * d0); ctx.fill();
      ctx.beginPath(); ctx.arc(cx + Math.cos(b) * (d1 + w * 1.6), cy + Math.sin(b) * (d1 + w * 1.6), w, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawHole(ctx, cx, cy, R, rot) {
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot);
    ctx.fillStyle = '#FFFDF7'; ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#15121C'; ctx.beginPath(); ctx.arc(R * 0.12, R * 0.1, R * 0.78, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = R * 0.16; ctx.strokeStyle = '#15121C'; ctx.beginPath(); ctx.arc(0, 0, R - ctx.lineWidth / 2, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
  }
  FX.makeAtlas = function () {
    return IB.Render.canvasTex(512, 512, function (ctx) {
      ctx.clearRect(0, 0, 512, 512);
      for (var i = 0; i < 4; i++) drawSplat(ctx, i * 128 + 64, 64, 46, 101 + i * 37, '#15121C');
      drawHole(ctx, 64, 192, 30, 0.3); drawHole(ctx, 192, 192, 26, 2.1);
      // white puff blob (tinted per particle) and soft blob shadow
      drawSplat(ctx, 320, 192, 40, 77, '#FFFFFF');
      ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(448, 192, 52, 0, Math.PI * 2); ctx.fill();
    });
  };
  var CELL = { splat: [[0, 0], [1, 0], [2, 0], [3, 0]], hole: [[0, 1], [1, 1]], puff: [2, 1], disc: [3, 1] };

  function atlasMaterial(tex, opts) {
    var m = new THREE.MeshBasicMaterial({ map: tex, alphaTest: 0.5, transparent: !!opts.transparent, depthWrite: !opts.transparent, fog: true,
      polygonOffset: !!opts.offset, polygonOffsetFactor: -2, polygonOffsetUnits: -4, vertexColors: false, opacity: opts.opacity || 1 });
    if (opts.transparent) m.alphaTest = 0.01;
    m.onBeforeCompile = function (sh) {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec2 aUv;')
        .replace('#include <uv_vertex>', 'vUv = uv * 0.25 + aUv;');
    };
    m.customProgramCacheKey = function () { return 'ibatlas' + (opts.transparent ? 't' : 'o'); };
    return m;
  }
  function instancedQuads(geo, mat, n, uvAttr) {
    var im = new THREE.InstancedMesh(geo, mat, n);
    if (uvAttr) { var a = new THREE.InstancedBufferAttribute(new Float32Array(n * 2), 2); a.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aUv', a); }
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    for (var i = 0; i < n; i++) im.setMatrixAt(i, ZERO);
    im.frustumCulled = false;
    return im;
  }
  function setUv(im, i, cell) {
    var a = im.geometry.attributes.aUv;
    // texture v runs bottom-up: row r occupies v in [1-(r+1)/4, 1-r/4]
    a.setXY(i, cell[0] * 0.25, 1 - (cell[1] + 1) * 0.25); a.needsUpdate = true;
  }

  FX.init = function (scene) {
    FX.scene = scene;
    FX.atlas = FX.makeAtlas();
    // decals
    FX.decalCap = 256;
    FX.decals = instancedQuads(new THREE.PlaneGeometry(1, 1), atlasMaterial(FX.atlas, { offset: true }), FX.decalCap, true);
    FX.decalNext = 0; FX.decalCount = 0;
    scene.add(FX.decals);
    // particles (billboards)
    FX.pCap = 320;
    var pg = new THREE.PlaneGeometry(1, 1);
    FX.parts = instancedQuads(pg, atlasMaterial(FX.atlas, {}), FX.pCap, true);
    FX.parts.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(FX.pCap * 3), 3);
    FX.pool = []; for (var i = 0; i < FX.pCap; i++) { FX.pool.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, t: 0, life: 1, s0: 0.2, s1: 0.5, rot: 0, g: 0 }); setUv(FX.parts, i, CELL.puff); }
    scene.add(FX.parts);
    FX.particleScale = 1;
    // chunks
    FX.cCap = 96;
    var cg = new IB.Geo(); cg.box(0, 0, 0, 1, 1, 1, PAL.ink, { hull: false });
    FX.chunks = new THREE.InstancedMesh(cg.build(), new THREE.MeshBasicMaterial({ color: PAL.ink }), FX.cCap);
    FX.chunks.instanceMatrix.setUsage(THREE.DynamicDrawUsage); FX.chunks.frustumCulled = false;
    FX.cPool = []; for (i = 0; i < FX.cCap; i++) { FX.cPool.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, rx: 0, ry: 0, rvx: 0, rvy: 0, t: 0, sx: 0.1, sy: 0.1, sz: 0.1 }); FX.chunks.setMatrixAt(i, ZERO); }
    scene.add(FX.chunks);
    // tracers
    FX.tCap = 64;
    FX.tracers = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xFFF6D8 }), FX.tCap);
    FX.tracers.instanceMatrix.setUsage(THREE.DynamicDrawUsage); FX.tracers.frustumCulled = false;
    FX.tPool = []; for (i = 0; i < FX.tCap; i++) { FX.tPool.push({ on: false, t: 0, ax: 0, ay: 0, az: 0, bx: 0, by: 0, bz: 0 }); FX.tracers.setMatrixAt(i, ZERO); }
    FX.tNext = 0;
    scene.add(FX.tracers);
    // blob shadows
    FX.bCap = 96;
    var bm = atlasMaterial(FX.atlas, { transparent: true, offset: true, opacity: 0.3 });
    bm.color = new THREE.Color(PAL.ink);
    FX.blobs = instancedQuads(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2), bm, FX.bCap, true);
    for (i = 0; i < FX.bCap; i++) setUv(FX.blobs, i, CELL.disc);
    FX.blobN = 0;
    scene.add(FX.blobs);
    // gems
    FX.initGems(scene);
  };

  FX.clear = function () {
    var i;
    for (i = 0; i < FX.decalCap; i++) FX.decals.setMatrixAt(i, ZERO);
    FX.decals.instanceMatrix.needsUpdate = true; FX.decalNext = 0; FX.decalCount = 0;
    FX.pool.forEach(function (p) { p.on = false; });
    FX.cPool.forEach(function (p) { p.on = false; });
    FX.tPool.forEach(function (p) { p.on = false; });
    FX.gems.forEach(function (g) { g.on = false; });
  };

  // ---------- decals ----------
  FX.decal = function (x, y, z, nx, ny, nz, kind, size) {
    var cap = FX.decalLimit || FX.decalCap;
    var i = FX.decalNext; FX.decalNext = (FX.decalNext + 1) % cap;
    _n.set(nx, ny, nz);
    _q.setFromUnitVectors(_z, _n);
    _q2.setFromAxisAngle(_z, Math.random() * Math.PI * 2);
    _q.multiply(_q2);
    _v.set(x + nx * 0.01, y + ny * 0.01, z + nz * 0.01);
    _s.set(size, size, size);
    _m.compose(_v, _q, _s);
    FX.decals.setMatrixAt(i, _m);
    var cell = kind === 'hole' ? CELL.hole[(Math.random() * 2) | 0] : CELL.splat[(Math.random() * 4) | 0];
    setUv(FX.decals, i, cell);
    FX.decals.instanceMatrix.needsUpdate = true;
    FX.decalCount = Math.min(cap, FX.decalCount + 1);
  };
  FX.impact = function (x, y, z, nx, ny, nz, splat) {
    FX.decal(x, y, z, nx, ny, nz, 'hole', 0.16 + Math.random() * 0.05);
    if (splat) { var sz = [0.45, 0.75, 1.1][(Math.random() * 3) | 0]; FX.decal(x, y, z, nx, ny, nz, 'splat', sz); }
    FX.puff(x + nx * 0.05, y + ny * 0.05, z + nz * 0.05, 3, PAL.ink, 0.12, 0.35, 1.5);
  };

  // ---------- particles ----------
  FX.puff = function (x, y, z, n, color, s0, s1, spd, grav) {
    n = Math.max(1, Math.round(n * FX.particleScale));
    for (var k = 0; k < n; k++) {
      var p = null;
      for (var i = 0; i < FX.pCap; i++) { var c = FX.pool[(FX.pNext = ((FX.pNext || 0) + 1) % FX.pCap)]; if (!c.on) { p = c; p.idx = FX.pNext; break; } }
      if (!p) return;
      p.on = true; p.x = x; p.y = y; p.z = z; p.t = 0; p.life = 0.3 + Math.random() * 0.25;
      var a = Math.random() * Math.PI * 2, e = (Math.random() - 0.3) * 1.6, sp = (spd || 2) * (0.4 + Math.random() * 0.8);
      p.vx = Math.cos(a) * sp; p.vz = Math.sin(a) * sp; p.vy = e * sp; p.g = grav || 0;
      p.s0 = s0 || 0.15; p.s1 = s1 || 0.4; p.rot = Math.random() * 6.28;
      _c.set(color === undefined ? PAL.ink : color);
      FX.parts.setColorAt(p.idx, _c);
    }
    FX.parts.instanceColor.needsUpdate = true;
  };

  // ---------- chunks ----------
  FX.chunk = function (x, y, z, n, power) {
    for (var k = 0; k < n; k++) {
      var p = null;
      for (var i = 0; i < FX.cCap; i++) { var c = FX.cPool[(FX.cNext = ((FX.cNext || 0) + 1) % FX.cCap)]; if (!c.on) { p = c; break; } }
      if (!p) return;
      p.on = true; p.t = 0; p.x = x; p.y = y; p.z = z;
      var a = Math.random() * Math.PI * 2, sp = (power || 3) * (0.5 + Math.random());
      p.vx = Math.cos(a) * sp; p.vz = Math.sin(a) * sp; p.vy = 2.5 + Math.random() * 3;
      p.rvx = (Math.random() - 0.5) * 14; p.rvy = (Math.random() - 0.5) * 14; p.rx = 0; p.ry = 0;
      var can = Math.random() < 0.5;
      p.sx = can ? 0.14 : 0.07; p.sy = can ? 0.18 : 0.07; p.sz = can ? 0.14 : 0.16;
    }
  };

  // ---------- tracers ----------
  FX.tracer = function (ax, ay, az, bx, by, bz) {
    var p = FX.tPool[FX.tNext]; FX.tNext = (FX.tNext + 1) % FX.tCap;
    p.on = true; p.t = 0; p.ax = ax; p.ay = ay; p.az = az; p.bx = bx; p.by = by; p.bz = bz;
  };

  // ---------- blob shadows (rebuilt each frame) ----------
  FX.blob = function (x, y, z, r) {
    if (FX.blobN >= FX.bCap) return;
    _m.makeScale(r * 2, 1, r * 2).setPosition(x, y + 0.015, z);
    FX.blobs.setMatrixAt(FX.blobN++, _m);
  };

  // ---------- gems ----------
  FX.initGems = function (scene) {
    var g = new IB.Geo();
    g.sphere(0, 0, 0, 0.16, 0xffffff, { ws: 4, hs: 2, sy: 1.4, hullScale: 1 });
    FX.gemCap = 240;
    FX.gemMesh = new THREE.InstancedMesh(g.build(), IB.Render.toonMaterial({}), FX.gemCap);
    FX.gemMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); FX.gemMesh.frustumCulled = false;
    FX.gems = [];
    for (var i = 0; i < FX.gemCap; i++) { FX.gems.push({ on: false, kind: 'chip', x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, bounced: false, t: 0, fly: false, zone: -1 }); FX.gemMesh.setMatrixAt(i, ZERO); FX.gemMesh.setColorAt(i, _c.set(PAL.chip)); }
    scene.add(FX.gemMesh);
  };
  var GEMCOL = { chip: PAL.chip, shard: PAL.shard, core: PAL.core }, GEMSCALE = { chip: 1, shard: 1.35, core: 1.7 };
  FX.dropGem = function (kind, x, y, z, zone) {
    for (var i = 0; i < FX.gemCap; i++) {
      var g = FX.gems[i]; if (g.on) continue;
      g.on = true; g.kind = kind; g.x = x; g.y = y + 0.3; g.z = z; g.t = 0; g.fly = false; g.bounced = false; g.zone = zone;
      var a = Math.random() * Math.PI * 2, s = 1 + Math.random() * 1.5;
      g.vx = Math.cos(a) * s; g.vz = Math.sin(a) * s; g.vy = 3 + Math.random() * 2;
      FX.gemMesh.setColorAt(i, _c.set(GEMCOL[kind])); FX.gemMesh.instanceColor.needsUpdate = true;
      return g;
    }
    return null;
  };
  FX.vacuumGems = function (zone) { FX.gems.forEach(function (g) { if (g.on && (zone === undefined || g.zone === zone)) g.fly = true; }); };
  FX.countGems = function () { var n = 0; FX.gems.forEach(function (g) { if (g.on) n++; }); return n; };

  /* player: {x,y,z}; magnet radius; onCollect(kind) */
  FX.update = function (dt, cam, player, magnet, onCollect) {
    var i, p;
    // particles
    for (i = 0; i < FX.pCap; i++) {
      p = FX.pool[i];
      if (!p.on) { continue; }
      p.t += dt;
      if (p.t >= p.life) { p.on = false; FX.parts.setMatrixAt(i, ZERO); continue; }
      p.vy -= p.g * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
      p.vx *= 0.92; p.vy *= 0.92; p.vz *= 0.92;
      var k = p.t / p.life, s = p.s0 + (p.s1 - p.s0) * Math.sqrt(k);
      if (k > 0.7) s *= 1 - (k - 0.7) / 0.3;
      _q2.setFromAxisAngle(_z, p.rot);
      _q.copy(cam.quaternion).multiply(_q2);
      _v.set(p.x, p.y, p.z); _s.set(s, s, s);
      _m.compose(_v, _q, _s); FX.parts.setMatrixAt(i, _m);
    }
    FX.parts.instanceMatrix.needsUpdate = true;
    // chunks
    for (i = 0; i < FX.cCap; i++) {
      p = FX.cPool[i]; if (!p.on) continue;
      p.t += dt;
      if (p.t > 1.4) { p.on = false; FX.chunks.setMatrixAt(i, ZERO); continue; }
      p.vy -= 18 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
      if (p.y < p.sy / 2) { p.y = p.sy / 2; p.vy = -p.vy * 0.3; p.vx *= 0.6; p.vz *= 0.6; p.rvx *= 0.5; p.rvy *= 0.5; }
      p.rx += p.rvx * dt; p.ry += p.rvy * dt;
      var sc = p.t > 1.0 ? 1 - (p.t - 1.0) / 0.4 : 1;
      _q.setFromEuler(_e.set(p.rx, p.ry, 0));
      _v.set(p.x, p.y - (p.t > 1 ? (p.t - 1) * 0.3 : 0), p.z); _s.set(p.sx * sc, p.sy * sc, p.sz * sc);
      _m.compose(_v, _q, _s); FX.chunks.setMatrixAt(i, _m);
    }
    FX.chunks.instanceMatrix.needsUpdate = true;
    // tracers (2 frames long)
    for (i = 0; i < FX.tCap; i++) {
      p = FX.tPool[i]; if (!p.on) continue;
      p.t += dt;
      if (p.t > 0.05) { p.on = false; FX.tracers.setMatrixAt(i, ZERO); continue; }
      var dx = p.bx - p.ax, dy = p.by - p.ay, dz = p.bz - p.az, L = Math.sqrt(dx * dx + dy * dy + dz * dz);
      var seg = Math.min(L, 6), f0 = Math.min(1, (p.t / 0.05) * 0.85);
      var cx = p.ax + dx * f0 + dx / L * seg / 2, cy = p.ay + dy * f0 + dy / L * seg / 2, cz = p.az + dz * f0 + dz / L * seg / 2;
      _n.set(dx / L, dy / L, dz / L); _q.setFromUnitVectors(_z, _n);
      _v.set(cx, cy, cz); _s.set(0.025, 0.025, Math.min(seg, L * (1 - f0)));
      _m.compose(_v, _q, _s); FX.tracers.setMatrixAt(i, _m);
    }
    FX.tracers.instanceMatrix.needsUpdate = true;
    // gems
    var t0 = performance.now() * 0.001, gHi = -1;
    for (i = 0; i < FX.gemCap; i++) {
      var g = FX.gems[i]; if (!g.on) continue;
      gHi = i;
      g.t += dt;
      var dxp = player.x - g.x, dyp = (player.y + 0.9) - g.y, dzp = player.z - g.z, d = Math.sqrt(dxp * dxp + dyp * dyp + dzp * dzp);
      if (player.alive && (g.fly || (d < magnet && g.t > 0.35))) {
        g.fly = true;
        var sp = 14 * dt;
        if (d <= sp + 0.35) { g.on = false; FX.gemMesh.setMatrixAt(i, ZERO); onCollect(g.kind); continue; }
        g.x += dxp / d * sp; g.y += dyp / d * sp; g.z += dzp / d * sp;
      } else {
        g.vy -= 18 * dt; g.x += g.vx * dt; g.y += g.vy * dt; g.z += g.vz * dt;
        var rest = 0.3;
        if (g.y < rest) {
          g.y = rest;
          if (!g.bounced) { g.vy = Math.abs(g.vy) * 0.35; g.bounced = true; g.vx *= 0.5; g.vz *= 0.5; }
          else { g.vy = 0; g.vx = 0; g.vz = 0; }
        }
      }
      var sc2 = GEMSCALE[g.kind] * Math.min(1, g.t * 6);
      _q.setFromAxisAngle(_v.set(0, 1, 0), t0 * 2.4 + i);
      _v.set(g.x, g.y + (g.vy === 0 && !g.fly ? Math.sin(t0 * 3 + i) * 0.06 : 0), g.z); _s.set(sc2, sc2, sc2);
      _m.compose(_v, _q, _s); FX.gemMesh.setMatrixAt(i, _m);
      if (!g.fly) FX.blob(g.x, 0, g.z, 0.18 * GEMSCALE[g.kind]);
    }
    FX.gemMesh.instanceMatrix.needsUpdate = true;
    FX.gemMesh.count = gHi + 1;
    // finish blob batch
    for (i = FX.blobN; i < (FX.prevBlobN || FX.bCap); i++) FX.blobs.setMatrixAt(i, ZERO);
    FX.prevBlobN = FX.blobN; FX.blobN = 0;
    FX.blobs.instanceMatrix.needsUpdate = true;
  };
})(window.IB = window.IB || {});
