/* INKBOLT robots: instanced rigid parts, AI state machine (section 4.4), hitscan tests,
   ink-silhouette deaths. Round 1 ships the Crawler; the type table is ready for the rest. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var AI = IB.AI = { robots: [], corpses: [], types: {}, tokens: 0, tokenMax: 3, level: 1 };
  var CAP = 40, CORPSE_CAP = 16;
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
  var _m = new THREE.Matrix4(), _m2 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _v = new THREE.Vector3(), _s = new THREE.Vector3(1, 1, 1), _up = new THREE.Vector3(0, 1, 0), _ax = new THREE.Vector3(1, 0, 0), _c = new THREE.Color(), _dir = { x: 0, z: 0 }, _tmp = [];

  function stat(id, key, fallback) { var e = IB.ENEMIES && IB.ENEMIES[id]; return (e && e[key] !== undefined) ? e[key] : fallback; }

  // ---------------- visual definitions ----------------
  var VIS = AI.VIS = {
    crawler: {
      radius: 0.42, y0: 0.12, y1: 0.86, coreY: 0.86, coreR: 0.17, shadow: 0.5,
      parts: {
        Body: { count: 1, build: function (g) {
          var tin = stat('crawler', 'color', '#C9CFD6');
          g.cyl(0, 0.3, 0, 0.32, 0.31, 0.42, 12, tin);
          g.cyl(0, 0.42, 0, 0.335, 0.335, 0.12, 12, 0xD9663B, { hull: false, noTop: true, noBottom: true });
          g.cyl(0, 0.72, 0, 0.35, 0.35, 0.05, 12, 0xA9B0BA);
          g.box(0, 0.6, 0.31, 0.34, 0.07, 0.06, PAL.ink, { hull: false });
          g.box(0, 0.6, 0.335, 0.22, 0.03, 0.02, PAL.amber, { hull: false });
          g.box(-0.24, 0.52, 0.2, 0.05, 0.05, 0.05, 0x8C93A0, { hull: false });
          g.box(0.24, 0.52, 0.2, 0.05, 0.05, 0.05, 0x8C93A0, { hull: false });
          g.sphere(0, 0.77, 0, 0.14, PAL.core, { ws: 8, hs: 4, sy: 0.6 });
          g.cyl(0.12, 0.76, -0.08, 0.018, 0.018, 0.3, 4, PAL.ink, { hull: false });
        } },
        Leg: { count: 4, build: function (g) {
          // spring coil (zigzag) from hip (y=0) down to a foot pad at y=-0.32
          for (var i = 0; i < 4; i++) g.box((i % 2 ? 0.035 : -0.035), -0.04 - i * 0.065, 0, 0.13, 0.035, 0.06, 0x8C93A0, { hullScale: 0.6 });
          g.box(0, -0.15, 0, 0.03, 0.3, 0.03, PAL.gunmetal, { hull: false });
          g.cyl(0, -0.33, 0, 0.09, 0.07, 0.05, 6, PAL.gunmetal);
        } },
        Light: { count: 1, light: true, build: function (g) { g.box(0, 0, 0, 0.09, 0.09, 0.09, 0xffffff, { hullScale: 0.6 }); } }
      },
      hips: [[-0.25, 0.25], [0.25, 0.25], [0.25, -0.25], [-0.25, -0.25]],
      pose: function (r, set) {
        var bob = Math.abs(Math.sin(r.walk * 2)) * 0.05, crouch = r.crouch;
        var bodyY = bob - crouch * 0.12;
        set('Body', 0, 0, bodyY, 0, 0, 1);
        for (var i = 0; i < 4; i++) {
          var h = VIS.crawler.hips[i], ph = Math.sin(r.walk * 2 + (i % 2) * Math.PI);
          var sc = (0.33 + bodyY) / 0.33 * (1 + ph * 0.06);
          set('Leg', i, h[0], 0.33 + bodyY, h[1], 0, Math.max(0.5, sc));
        }
        set('Light', 0, 0.12, 1.08 + bodyY, -0.08, 0, 1);
      }
    }
  };

  // ---------------- materials / meshes ----------------
  AI.init = function (scene) {
    AI.scene = scene;
    AI.mat = IB.Render.toonMaterial({ fx: true });
    AI.lightMat = IB.Render.toonMaterial({});
    var cmat = new THREE.MeshBasicMaterial({ color: PAL.ink, transparent: true, depthWrite: true });
    cmat.onBeforeCompile = function (sh) {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aOp;\nvarying float vOp;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvOp = aOp;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vOp;').replace('#include <fog_fragment>', 'gl_FragColor.a *= vOp;\n#include <fog_fragment>');
    };
    cmat.customProgramCacheKey = function () { return 'ibcorpse'; };
    AI.corpseMat = cmat;
    Object.keys(VIS).forEach(function (id) {
      var v = VIS[id], T = { id: id, vis: v, parts: {}, slots: [], corpse: null };
      var whole = new IB.Geo();
      Object.keys(v.parts).forEach(function (pn) {
        var P = v.parts[pn], g = new IB.Geo(); P.build(g);
        var geo = g.build(), n = CAP * P.count;
        if (!P.light) { var fx = new THREE.InstancedBufferAttribute(new Float32Array(n * 2), 2); fx.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aFx', fx); }
        var im = new THREE.InstancedMesh(geo, P.light ? AI.lightMat : AI.mat, n);
        im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.frustumCulled = false;
        for (var i = 0; i < n; i++) { im.setMatrixAt(i, ZERO); if (P.light) im.setColorAt(i, _c.set(0x7A6A4A)); }
        scene.add(im);
        T.parts[pn] = { mesh: im, count: P.count };
      });
      // corpse geometry: whole robot in rest pose, all ink
      var cg = new IB.Geo(); v.parts.Body.build(cg);
      if (v.hips) v.hips.forEach(function (h) { cg.setMatrix(new THREE.Matrix4().makeTranslation(h[0], 0.33, h[1])); v.parts.Leg.build(cg); cg.setMatrix(null); });
      var cgeo = cg.build(); cgeo.deleteAttribute('aHull');
      var op = new THREE.InstancedBufferAttribute(new Float32Array(CORPSE_CAP), 1); op.setUsage(THREE.DynamicDrawUsage); cgeo.setAttribute('aOp', op);
      var cm = new THREE.InstancedMesh(cgeo, cmat, CORPSE_CAP);
      cm.instanceMatrix.setUsage(THREE.DynamicDrawUsage); cm.frustumCulled = false;
      for (var k = 0; k < CORPSE_CAP; k++) cm.setMatrixAt(k, ZERO);
      scene.add(cm);
      T.corpse = cm; T.corpses = [];
      for (k = 0; k < CORPSE_CAP; k++) T.corpses.push({ on: false, t: 0, x: 0, y: 0, z: 0, yaw: 0, tip: 1 });
      for (var s = 0; s < CAP; s++) { var r = newRobot(id, s); T.slots.push(r); AI.robots.push(r); }
      AI.types[id] = T;
    });
  };

  function newRobot(type, slot) {
    return { type: type, slot: slot, on: false, state: 'off', st: 0, x: 0, y: 0, z: 0, vx: 0, vz: 0, yaw: 0, hp: 1, maxHp: 1,
      zone: -1, flash: 0, walk: 0, crouch: 0, token: false, bit: false, lx: 0, lz: 0, losT: Math.random() * 0.2, seesPlayer: false,
      zig: Math.random() * 6, sx: 0, sz: 0, tx: 0, tz: 0, kx: 0, kz: 0, alert: 0, blind: 0, wanderT: 0, wx: 0, wz: 0, dmgMul: 1, pose: false, idleT: Math.random() * 5 };
  }

  AI.clear = function () {
    AI.robots.forEach(function (r) { r.on = false; r.state = 'off'; r.token = false; });
    Object.keys(AI.types).forEach(function (id) { AI.types[id].corpses.forEach(function (c) { c.on = false; }); });
    AI.tokens = 0;
  };
  AI.setLevel = function (L) {
    AI.level = L; AI.tokenMax = 3 + Math.floor(L / 5);
    AI.hpMul = IB.Damage ? IB.Damage.enemyHpMul(L) : 1 + 0.06 * (L - 1);
    AI.dmgMul = IB.Damage ? IB.Damage.enemyDmgMul(L) : Math.min(3, 1 + 0.04 * (L - 1));
  };

  /* spawn a robot hopping out of a spawn can at (x,z) toward (tx,tz) */
  AI.spawn = function (type, x, z, zone, tx, tz, opts) {
    var T = AI.types[type]; if (!T) return null;
    var r = null; for (var i = 0; i < CAP; i++) if (!T.slots[i].on) { r = T.slots[i]; break; }
    if (!r) return null;
    opts = opts || {};
    r.on = true; r.zone = zone; r.state = opts.pose ? 'pose' : 'spawn'; r.st = 0; r.pose = !!opts.pose;
    r.maxHp = r.hp = stat(type, 'hp', 30) * (AI.hpMul || 1);
    r.sx = x; r.sz = z; r.x = x; r.z = z; r.y = opts.pose ? 0 : 1.0; r.tx = tx; r.tz = tz;
    r.vx = r.vz = 0; r.kx = r.kz = 0; r.flash = 0; r.crouch = 0; r.token = false; r.alert = 0; r.blind = 0;
    r.yaw = Math.atan2(tx - x, tz - z); r.walk = Math.random() * 3; r.dmgMul = (AI.dmgMul || 1) * (opts.dmgScale || 1);
    if (!opts.pose && IB.FX) IB.FX.puff(x, 1.0, z, 6, PAL.ink, 0.2, 0.6, 2.5);
    return r;
  };

  AI.alive = function (zone) {
    var n = 0; for (var i = 0; i < AI.robots.length; i++) { var r = AI.robots[i]; if (r.on && r.state !== 'pose' && (zone === undefined || r.zone === zone)) n++; }
    return n;
  };
  AI.killAll = function (zone, cb) {
    AI.robots.forEach(function (r) { if (r.on && r.state !== 'pose' && (zone === undefined || r.zone === zone)) AI.kill(r, cb); });
  };
  AI.despawn = function (zone) { AI.robots.forEach(function (r) { if (r.on && (zone === undefined || r.zone === zone)) { releaseToken(r); r.on = false; r.state = 'off'; } }); };

  function releaseToken(r) { if (r.token) { r.token = false; AI.tokens = Math.max(0, AI.tokens - 1); } }
  function setState(r, s) { if ((s !== 'windup' && s !== 'attack') && r.token && s !== 'recover') releaseToken(r); r.state = s; r.st = 0; }

  // hearing: wake robots within radius
  AI.hear = function (x, z, radius) {
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || r.state !== 'idle') continue;
      var dx = r.x - x, dz = r.z - z; if (dx * dx + dz * dz < radius * radius) { setState(r, 'alert'); }
    }
  };

  /* damage: returns true if killed. opts: {stagger, kx, kz} */
  AI.damage = function (r, dmg, opts, onKill) {
    if (!r.on || r.state === 'spawn' || r.state === 'pose') return false;
    opts = opts || {};
    r.hp -= dmg; r.flash = 0.06;
    if (r.state === 'idle') setState(r, 'alert');
    if (r.hp <= 0) { AI.kill(r, onKill); return true; }
    if (dmg >= r.maxHp * 0.25 || opts.stagger) {
      setState(r, 'stagger'); r.kx = opts.kx || 0; r.kz = opts.kz || 0; r.crouch = 0;
    }
    return false;
  };
  AI.kill = function (r, onKill) {
    releaseToken(r);
    r.on = false; r.state = 'off';
    var T = AI.types[r.type], c = null;
    for (var i = 0; i < CORPSE_CAP; i++) if (!T.corpses[i].on) { c = T.corpses[i]; c.idx = i; break; }
    if (!c) { var oldest = 0; for (i = 1; i < CORPSE_CAP; i++) if (T.corpses[i].t > T.corpses[oldest].t) oldest = i; c = T.corpses[oldest]; c.idx = oldest; }
    c.on = true; c.t = 0; c.x = r.x; c.y = r.y; c.z = r.z; c.yaw = r.yaw; c.tip = Math.random() < 0.5 ? 1 : -1;
    if (IB.FX) { IB.FX.chunk(r.x, 0.5, r.z, 3 + ((Math.random() * 4) | 0), 3); IB.FX.puff(r.x, 0.5, r.z, 6, PAL.ink, 0.25, 0.7, 3); }
    if (onKill) onKill(r);
  };

  // ---------------- hitscan ----------------
  function rayCapsule(ox, oy, oz, dx, dy, dz, cx, cz, y0, y1, rad) {
    var best = Infinity;
    var px = ox - cx, pz = oz - cz, a = dx * dx + dz * dz;
    if (a > 1e-8) {
      var b = 2 * (px * dx + pz * dz), c = px * px + pz * pz - rad * rad, disc = b * b - 4 * a * c;
      if (disc >= 0) {
        var t = (-b - Math.sqrt(disc)) / (2 * a);
        if (t > 0) { var y = oy + dy * t; if (y >= y0 && y <= y1) best = t; }
      }
    }
    var ts = raySphere(ox, oy, oz, dx, dy, dz, cx, y0, cz, rad); if (ts < best) best = ts;
    ts = raySphere(ox, oy, oz, dx, dy, dz, cx, y1, cz, rad); if (ts < best) best = ts;
    return best;
  }
  function raySphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, rad) {
    var px = ox - cx, py = oy - cy, pz = oz - cz, b = px * dx + py * dy + pz * dz, c = px * px + py * py + pz * pz - rad * rad, disc = b * b - c;
    if (disc < 0) return Infinity;
    var t = -b - Math.sqrt(disc); return t > 0 ? t : Infinity;
  }
  AI.rayCapsule = rayCapsule; AI.raySphere = raySphere;
  var _hit = { robot: null, t: 0, zone: 'body' };
  AI.raycast = function (ox, oy, oz, dx, dy, dz, maxT, skip) {
    var best = maxT, br = null, bz = 'body';
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || r.state === 'pose' || r === skip || (skip && skip.indexOf && skip.indexOf(r) >= 0)) continue;
      var v = VIS[r.type], bodyY = r.y - r.crouch * 0.12;
      var tb = rayCapsule(ox, oy, oz, dx, dy, dz, r.x, r.z, bodyY + v.y0 + v.radius * 0.5, bodyY + v.y1 - v.radius * 0.5, v.radius);
      var tc = raySphere(ox, oy, oz, dx, dy, dz, r.x, bodyY + v.coreY, r.z, v.coreR);
      var t = Math.min(tb, tc);
      if (t < best) { best = t; br = r; bz = (tc <= tb + 0.12) ? 'core' : 'body'; }
    }
    if (!br) return null;
    _hit.robot = br; _hit.t = best; _hit.zone = bz; return _hit;
  };
  AI.nearest = function (x, z, maxD, filter) {
    var best = maxD * maxD, br = null;
    AI.robots.forEach(function (r) { if (!r.on || r.state === 'pose') return; if (filter && !filter(r)) return; var d = (r.x - x) * (r.x - x) + (r.z - z) * (r.z - z); if (d < best) { best = d; br = r; } });
    return br;
  };

  // ---------------- movement helpers ----------------
  function collide(r, world, rad) {
    world.query(r.x - rad, r.z - rad, r.x + rad, r.z + rad, _tmp);
    for (var i = 0; i < _tmp.length; i++) {
      var b = _tmp[i]; if (b.y1 < 0.3) continue;
      var cx = Math.max(b.x0, Math.min(r.x, b.x1)), cz = Math.max(b.z0, Math.min(r.z, b.z1));
      var dx = r.x - cx, dz = r.z - cz, d2 = dx * dx + dz * dz;
      if (d2 >= rad * rad) continue;
      if (d2 > 1e-8) { var d = Math.sqrt(d2); r.x += dx / d * (rad - d); r.z += dz / d * (rad - d); }
      else { r.x += (r.x < (b.x0 + b.x1) / 2 ? -1 : 1) * 0.05; }
    }
  }
  function turnTo(r, yaw, rate, dt) {
    var d = yaw - r.yaw; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2;
    var m = rate * dt; r.yaw += Math.max(-m, Math.min(m, d));
  }

  /* ctx: {player, world, level, activeZone, hurt(robot, dmg), dt} */
  AI.update = function (dt, ctx) {
    var p = ctx.player, world = ctx.world, i, r;
    var zone = ctx.level && ctx.activeZone >= 0 ? ctx.level.zones[ctx.activeZone] : null;
    if (zone) {
      zone.nav.t -= dt;
      if (zone.nav.t <= 0) { zone.nav.t = 0.25; IB.Zones.flowField(zone, p.x, p.z); }
    }
    for (i = 0; i < AI.robots.length; i++) {
      r = AI.robots[i]; if (!r.on) continue;
      var def = IB.ENEMIES && IB.ENEMIES[r.type] || {};
      var speed = def.speed || 5.0, v = VIS[r.type];
      r.st += dt; r.flash = Math.max(0, r.flash - dt); r.idleT += dt;
      var dx = p.x - r.x, dz = p.z - r.z, dist = Math.sqrt(dx * dx + dz * dz) || 0.001;
      var mvx = 0, mvz = 0, moveSpeed = 0;
      // periodic sight check (staggered)
      r.losT -= dt;
      if (r.losT <= 0 && r.state !== 'pose') {
        r.losT = 0.2;
        r.seesPlayer = p.alive && dist < 25 && world.los(r.x, 0.8, r.z, p.x, p.y + 1.4, p.z);
      }
      switch (r.state) {
        case 'pose':
          r.walk += dt * 0.6; r.crouch = 0.15 + Math.sin(r.idleT * 2.2 + r.slot) * 0.12;
          break;
        case 'spawn': {
          var k = Math.min(1, r.st / 0.8);
          r.x = r.sx + (r.tx - r.sx) * k; r.z = r.sz + (r.tz - r.sz) * k;
          r.y = Math.max(0, (1 - k) * 1.0 + Math.sin(k * Math.PI) * 0.8);
          r.walk += dt * 6;
          if (r.st >= 0.8) { r.y = 0; IB.FX && IB.FX.puff(r.x, 0.1, r.z, 4, PAL.ink, 0.15, 0.45, 2); setState(r, zone && r.zone === ctx.activeZone ? 'alert' : 'idle'); }
          break;
        }
        case 'idle': {
          // wander between nearby points at 40% speed
          r.wanderT -= dt;
          if (r.wanderT <= 0) { r.wanderT = 2 + Math.random() * 2; var a = Math.random() * 6.28; r.wx = r.x + Math.cos(a) * 3; r.wz = r.z + Math.sin(a) * 3; }
          var wx = r.wx - r.x, wz = r.wz - r.z, wl = Math.hypot(wx, wz);
          if (wl > 0.3) { mvx = wx / wl; mvz = wz / wl; moveSpeed = speed * 0.4; }
          var fy = Math.atan2(dx, dz) - r.yaw; while (fy > Math.PI) fy -= 6.283; while (fy < -Math.PI) fy += 6.283;
          if (r.seesPlayer && Math.abs(fy) < Math.PI / 3) setState(r, 'alert');
          break;
        }
        case 'alert':
          turnTo(r, Math.atan2(dx, dz), 8, dt);
          r.alert = 0.4;
          if (r.st >= 0.4) setState(r, 'chase');
          break;
        case 'chase': {
          if (!p.alive) { moveSpeed = 0; break; }
          if (r.seesPlayer && dist < 14) {
            mvx = dx / dist; mvz = dz / dist;
            // zigzag (Crawler): lateral sine weave that fades close in
            var zz = Math.sin(r.zig + r.st * 5.5) * Math.min(1, (dist - 2) / 5) * 0.75;
            var lx = -mvz, lz = mvx; mvx += lx * zz; mvz += lz * zz;
            var ml = Math.hypot(mvx, mvz); mvx /= ml; mvz /= ml;
          } else if (zone && r.zone === ctx.activeZone && IB.Zones.flowDir(zone, r.x, r.z, _dir)) { mvx = _dir.x; mvz = _dir.z; }
          else { mvx = dx / dist; mvz = dz / dist; }
          moveSpeed = speed;
          var reach = def.reach || 2.3;
          if (dist < reach && r.seesPlayer && AI.tokens < AI.tokenMax) { r.token = true; AI.tokens++; setState(r, 'windup'); r.lx = dx / dist; r.lz = dz / dist; }
          break;
        }
        case 'windup': {
          var wu = def.windup || 0.35;
          turnTo(r, Math.atan2(dx, dz), 10, dt);
          r.crouch = Math.min(1, r.st / wu);
          var ph = r.st / wu;
          r.flash = ((ph > 0.05 && ph < 0.3) || (ph > 0.55 && ph < 0.8)) ? 0.02 : r.flash;
          r.lx = dx / dist; r.lz = dz / dist;
          if (r.st >= wu) { setState(r, 'attack'); r.bit = false; r.crouch = 0; }
          break;
        }
        case 'attack': {
          mvx = r.lx; mvz = r.lz; moveSpeed = 9.5;
          r.y = Math.sin(Math.min(1, r.st / 0.24) * Math.PI) * 0.35;
          if (!r.bit && dist < v.radius + 0.35 + 0.45 && Math.abs(p.y - r.y) < 1.2) {
            r.bit = true; ctx.hurt(r, (def.damage || 8) * r.dmgMul);
          }
          if (r.st >= 0.24) { r.y = 0; setState(r, 'recover'); }
          break;
        }
        case 'recover':
          if (r.token) releaseToken(r);
          moveSpeed = 0; r.crouch = Math.max(0, r.crouch - dt * 3);
          if (r.st >= 0.6) setState(r, 'chase');
          break;
        case 'stagger':
          r.x += r.kx * dt; r.z += r.kz * dt; r.kx *= Math.max(0, 1 - 6 * dt); r.kz *= Math.max(0, 1 - 6 * dt);
          r.yaw += dt * 3;
          if (r.st >= 0.6) setState(r, 'chase');
          break;
        case 'blinded':
          r.yaw += dt * 1.5;
          if (r.st >= r.blind) setState(r, 'chase');
          break;
      }
      if (r.state !== 'spawn' && r.state !== 'pose') {
        // smooth velocity
        var tvx = mvx * moveSpeed, tvz = mvz * moveSpeed, blend = Math.min(1, dt * (r.state === 'attack' ? 30 : 10));
        r.vx += (tvx - r.vx) * blend; r.vz += (tvz - r.vz) * blend;
        r.x += r.vx * dt; r.z += r.vz * dt;
        var hs = Math.hypot(r.vx, r.vz);
        r.walk += dt * hs * 1.6;
        if (hs > 0.3 && r.state !== 'stagger') turnTo(r, Math.atan2(r.vx, r.vz), 9, dt);
        if (r.state !== 'windup' && r.state !== 'attack') r.crouch = Math.max(0, r.crouch - dt * 4);
        collide(r, world, v.radius * 0.9);
      }
      r.alert = Math.max(0, r.alert - dt);
    }
    // soft separation (60% of overlap)
    for (i = 0; i < AI.robots.length; i++) {
      var a = AI.robots[i]; if (!a.on || a.state === 'spawn') continue;
      for (var j = i + 1; j < AI.robots.length; j++) {
        var b = AI.robots[j]; if (!b.on || b.state === 'spawn') continue;
        var sx = b.x - a.x, sz = b.z - a.z, rr = VIS[a.type].radius + VIS[b.type].radius, d2 = sx * sx + sz * sz;
        if (d2 < rr * rr && d2 > 1e-6) {
          var d = Math.sqrt(d2), push = (rr - d) * 0.3 / d;
          a.x -= sx * push; a.z -= sz * push; b.x += sx * push; b.z += sz * push;
        }
      }
    }
  };

  // ---------------- render sync ----------------
  var _cur = null;
  function setPart(name, k, lx, ly, lz, rx, sy) {
    var T = AI.types[_cur.type], P = T.parts[name], idx = _cur.slot * P.count + k;
    _v.set(lx, ly, lz); _s.set(1, sy, 1); _q.setFromAxisAngle(_ax, rx || 0);
    _m2.compose(_v, _q, _s);
    _m.multiplyMatrices(_base, _m2);
    P.mesh.setMatrixAt(idx, _m);
    var fx = P.mesh.geometry.attributes.aFx;
    if (fx) fx.setXY(idx, _cur.flash > 0 ? 1 : 0, 0);
    else if (P.mesh.instanceColor) {
      var lit = _cur.alert > 0 ? (Math.sin(_cur.alert * 40) > 0) : (_cur.state === 'chase' || _cur.state === 'windup' || _cur.state === 'attack');
      P.mesh.setColorAt(idx, _c.set(lit ? PAL.amber : 0x7A6A4A));
    }
  }
  var _base = new THREE.Matrix4();
  AI.sync = function () {
    Object.keys(AI.types).forEach(function (id) {
      var T = AI.types[id], hi = -1;
      for (var s = 0; s < CAP; s++) {
        var r = T.slots[s];
        if (r.on) hi = s;
        if (!r.on) { Object.keys(T.parts).forEach(function (pn) { var P = T.parts[pn]; for (var k = 0; k < P.count; k++) P.mesh.setMatrixAt(s * P.count + k, ZERO); }); continue; }
        _cur = r;
        _q.setFromAxisAngle(_up, r.yaw); _v.set(r.x, r.y, r.z); _s.set(1, 1, 1);
        _base.compose(_v, _q, _s);
        T.vis.pose(r, setPart);
        if (IB.FX) IB.FX.blob(r.x, 0, r.z, T.vis.shadow * (1 - Math.min(0.5, r.y)));
      }
      Object.keys(T.parts).forEach(function (pn) {
        var P = T.parts[pn]; P.mesh.instanceMatrix.needsUpdate = true;
        P.mesh.count = (hi + 1) * P.count;   // draw only up to the highest live slot
        if (P.mesh.geometry.attributes.aFx) P.mesh.geometry.attributes.aFx.needsUpdate = true;
        if (P.mesh.instanceColor) P.mesh.instanceColor.needsUpdate = true;
      });
    });
  };

  // corpses: pop 0.3 m up (0.12 s), tip over (0.5 s), fade + sink (0.6 s)
  AI.updateCorpses = function (dt) {
    Object.keys(AI.types).forEach(function (id) {
      var T = AI.types[id], op = T.corpse.geometry.attributes.aOp, hiC = -1;
      for (var i = 0; i < CORPSE_CAP; i++) {
        var c = T.corpses[i];
        if (!c.on) { T.corpse.setMatrixAt(i, ZERO); continue; }
        c.t += dt;
        var y, tip, alpha = 1;
        if (c.t < 0.12) { y = c.y + Math.sin(c.t / 0.12 * Math.PI / 2) * 0.3; tip = 0; }
        else if (c.t < 0.62) { var k = (c.t - 0.12) / 0.5; y = c.y + 0.3 * (1 - k * k); tip = k * k * (Math.PI / 2); }
        else if (c.t < 1.22) { var f = (c.t - 0.62) / 0.6; y = c.y - f * 0.35; tip = Math.PI / 2; alpha = 1 - f; }
        else { c.on = false; T.corpse.setMatrixAt(i, ZERO); continue; }
        _q.setFromAxisAngle(_up, c.yaw);
        var q2 = new THREE.Quaternion().setFromAxisAngle(_ax, tip * c.tip);
        _q.multiply(q2);
        _v.set(c.x, y + (tip > 0 ? 0.3 * Math.sin(tip) : 0), c.z); _s.set(1, 1, 1);
        _m.compose(_v, _q, _s); T.corpse.setMatrixAt(i, _m);
        op.setX(i, alpha); hiC = i;
      }
      T.corpse.count = hiC + 1;
      T.corpse.instanceMatrix.needsUpdate = true; op.needsUpdate = true;
    });
  };
})(window.IB = window.IB || {});
