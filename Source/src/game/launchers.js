/* INKBOLT launchers (round 5): the RL-3 Hothead (rapid-fire elemental rockets) and the ML-6 Murmur (homing salvo),
   their rockets in flight, blasts, lock-on brackets, the rocket ammo pool and the rocket ammo director.
   Tables: src/data/weapons.js (hothead, murmur, IB.LAUNCHER_ELEMENTS); rules: src/core/gunlevel.js (levels, rolls,
   director); models: blender/fam_weapons.py (WPN_HOTHEAD / WPN_MURMUR, PROJ_Rocket, PICKUP_Rockets).
   Contract (game.js):
     init(scene) / clear() / startLevel(G)        pools; rocket pool from slot.rockets, magazines loaded from it
     fire(def, cam, spread)                       weapons.js fire() for fire 'rocket' (one rocket, or one salvo)
     update(dt, ctx)                              fixed step: flight, homing, impacts, blasts (ctx: player, world, onKill)
     sync(dt, t, G)                               render: rocket meshes, trails, lock brackets, crates, canister glow
     onKill(robot)                                launcher drops (levels 14+) and rocket crates (soldiers; bladers at half the chance)
     magOf(def) / rackPick(L) / onAcquire(id, isNew) / radar()
   Rocket ammo: G.ws.ammo.rocket is the spare pool (every launcher's `reserve`); slot.rockets saves the total
   (spare + loaded), and a level start loads the carried launchers' magazines from it, so a level never hands out
   free rockets. Normal ammo boxes and respawns never refill rockets: only rocket crates do. */
(function (IB) {
  'use strict';
  var L = IB.Launchers = { rockets: [], crates: [], locks: [], salvo: [], bomblets: [], used: [], stats: { fired: 0, salvos: 0, blasts: 0, robotHits: 0, selfDamage: 0, crates: 0, crateRockets: 0 } };
  var GL = function () { return IB.GunLevel; };
  var ROCKET_CAP = 32, CRATE_CAP = 6, LOCK_CAP = 5, BOMB_CAP = 12;
  var PLAYER_R = 0.35, PLAYER_H = 1.7;
  var _v = new THREE.Vector3(), _d = new THREE.Vector3(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(), _m = new THREE.Matrix4();
  var _nz = new THREE.Vector3(0, 0, -1), _c = new THREE.Color(), ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
  var SELF = { type: 'rocket', killer: 'Your own rocket', x: 0, z: 0, proj: true };

  function G() { return IB.Game; }
  function up(id) { var s = G() && G().slot; return (s && s.upgrades && s.upgrades[id]) || 0; }
  function elemOf(def, roll) { return def.elements && roll && GL() ? GL().element(roll.elem) : (IB.LAUNCHER_ELEMENTS ? IB.LAUNCHER_ELEMENTS.none : { color: '#FFB21E', splashMul: 1, radiusMul: 1 }); }

  // ---------------- init / pools ----------------
  L.init = function (scene) {
    var A = IB.Assets;
    L.scene = scene;
    var mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0 });
    if (A.geo.PROJ_Rocket) {
      L.mesh = new THREE.InstancedMesh(A.get('PROJ_Rocket'), mat, ROCKET_CAP);
      L.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); L.mesh.frustumCulled = false; L.mesh.count = 0; scene.add(L.mesh);
    }
    // exhaust flare at each rocket's tail (element colour)
    L.glow = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), ROCKET_CAP);
    L.glow.instanceMatrix.setUsage(THREE.DynamicDrawUsage); L.glow.frustumCulled = false; L.glow.count = 0;
    for (var i = 0; i < ROCKET_CAP; i++) L.glow.setColorAt(i, _c.set(0xffffff));
    scene.add(L.glow);
    for (i = 0; i < ROCKET_CAP; i++) L.rockets.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, sp: 0, t: 0, def: null, elem: null, mul: 1, lock: null, homing: false, sc: 1, puff: 0, color: '#FFB21E' });
    for (i = 0; i < BOMB_CAP; i++) L.bomblets.push({ on: false, t: 0, x: 0, y: 0, z: 0, R: 1, D: 0, def: null });
    var cg = A.geo.PICKUP_Rockets ? A.get('PICKUP_Rockets') : A.get('PICKUP_Ammo');
    for (i = 0; i < CRATE_CAP; i++) {
      var m = new THREE.Mesh(cg, A.mat.weapons); m.visible = false; m.scale.setScalar(0.9); scene.add(m);
      L.crates.push({ on: false, mesh: m, x: 0, y: 0, z: 0, n: 0, t: 0, fullT: 0 });
    }
    initLocks();
  };
  L.clear = function () {
    L.rockets.forEach(function (r) { r.on = false; });
    L.bomblets.forEach(function (b) { b.on = false; });
    L.crates.forEach(function (c) { c.on = false; c.mesh.visible = false; });
    L.locks.forEach(function (k) { k.on = false; k.el.hidden = true; });
    L.salvo.length = 0; L.used.length = 0;
    if (L.mesh) L.mesh.count = 0; if (L.glow) L.glow.count = 0;
  };

  // ---------------- rocket ammo pool ----------------
  function pool() { var g = G(); return g && g.ws && g.ws.ammo ? g.ws.ammo : { rocket: 0 }; }
  function launcherIds(list) { return (list || []).filter(function (id) { return GL() && GL().isLauncher(IB.WEAPONS[id]); }); }
  /* rockets loaded in launcher magazines (carried ones, and the ones parked in the Tab-menu bank) */
  function loaded() {
    var g = G(), n = 0, seen = {};
    if (!g || !g.ws) return 0;
    Object.keys(g.ws.guns).forEach(function (id) { var gun = g.ws.guns[id]; if (gun.def.ammo) { n += gun.mag * (gun.def.ammoPer || 1); seen[id] = true; } });
    Object.keys(g.bank || {}).forEach(function (id) { var d = IB.WEAPONS[id]; if (!seen[id] && d && d.ammo && g.bank[id]) n += (g.bank[id].mag || 0) * (d.ammoPer || 1); });
    return n;
  }
  L.total = function () { return pool().rocket + loaded(); };
  L.magOf = function (def) {
    var WD = IB.WeaponDrops, roll = WD && WD.rollOf ? WD.rollOf(def.id) : null;
    return roll ? roll.mag : def.mag;
  };
  /* a launcher gun object that joined the carried guns: its magazine is filled from the pool, not for free */
  function settle() {
    var g = G(); if (!g || !g.ws) return;
    var P = pool();
    Object.keys(g.ws.guns).forEach(function (id) {
      var gun = g.ws.guns[id]; if (!gun.def.ammo || gun._settled) return;
      gun._settled = true;
      if (gun._fromBank) return;
      var per = gun.def.ammoPer || 1, want = gun.mag, k = Math.max(0, Math.min(want, Math.floor(P.rocket / per)));
      gun.mag = k; P.rocket -= k * per;
    });
  }
  L.startLevel = function (g) {
    L.clear();
    var s = g.slot, P = pool();
    P.rocket = Math.max(0, (s && s.rockets) || 0);
    settle();
    L.dropped = 0; L.dry = 0;
    var soldiers = 0, bladers = 0;
    ((g.plan && g.plan.zones) || []).forEach(function (z) { (z.waves || []).forEach(function (w) { w.forEach(function (e) { if (e[0] === 'soldier') soldiers += e[1]; else if (e[0] === 'blader') bladers += e[1]; }); }); });
    L.soldiers = soldiers; L.bladers = bladers;
    L.budget = GL() ? GL().rocketBudget(soldiers) : 12;
  };
  /* a launcher joined the arsenal (isNew) or replaced yours: a new one comes with one magazine of rockets */
  L.onAcquire = function (id, isNew) {
    var g = G(), def = IB.WEAPONS[id]; if (!g || !def || !isNew) return;
    var cap = GL() ? GL().ROCKET.cap : 16, P = pool();
    P.rocket = Math.max(P.rocket, Math.min(cap - loaded(), P.rocket + L.magOf(def) * (def.ammoPer || 1)));
    if (g.slot) g.slot.rockets = L.total();
  };

  // ---------------- firing ----------------
  function dmgMul(def) {
    var WD = IB.WeaponDrops, sk = IB.SkillFX && IB.SkillFX.hitMul ? IB.SkillFX.hitMul('body') : 1;
    return (WD ? WD.dmgMul(def.id) : 1) * (1 + 0.15 * up('dmg')) * sk;
  }
  function spawnRocket(def, x, y, z, dx, dy, dz, speed, opts) {
    var r = null, i;
    for (i = 0; i < ROCKET_CAP; i++) if (!L.rockets[i].on) { r = L.rockets[i]; break; }
    if (!r) { r = L.rockets[0]; for (i = 1; i < ROCKET_CAP; i++) if (L.rockets[i].t > r.t) r = L.rockets[i]; }
    var n = Math.hypot(dx, dy, dz) || 1;
    r.on = true; r.t = 0; r.x = x; r.y = y; r.z = z; r.sp = speed; r.vx = dx / n * speed; r.vy = dy / n * speed; r.vz = dz / n * speed;
    r.def = def; r.elem = opts.elem; r.mul = opts.mul; r.lock = opts.lock || null; r.homing = !!opts.lock; r.sc = opts.sc || 1; r.puff = 0;
    r.color = opts.elem && opts.elem.color || '#FFB21E'; r.life = def.life || 2.4; r.delay = opts.delay || 0;
    return r;
  }
  // where the crosshair points: first robot or world surface along the camera ray (max m)
  function aimPoint(cam, max, out) {
    var g = G(), o = cam.position; cam.getWorldDirection(_d);
    var wh = g.level.world.ray(o.x, o.y, o.z, _d.x, _d.y, _d.z, max), t = wh ? wh.t : max;
    var rh = IB.AI.raycast(o.x, o.y, o.z, _d.x, _d.y, _d.z, t);
    if (rh) t = rh.t;
    return out.set(o.x + _d.x * t, o.y + _d.y * t, o.z + _d.z * t);
  }
  var _aim = new THREE.Vector3(), _mz = new THREE.Vector3(), _rt = new THREE.Vector3(), _upv = new THREE.Vector3();
  L.fire = function (def, cam, spread) {
    var g = G(), WD = IB.WeaponDrops, roll = WD && WD.rollOf ? WD.rollOf(def.id) : null, el = elemOf(def, roll), mul = dmgMul(def);
    IB.Weapons.muzzleWorld(cam, _mz);
    cam.getWorldDirection(_d); _mz.addScaledVector(_d, 0.25);
    L.stats.fired += def.ammoPer || 1;
    var now = g.run ? g.run.time : 0; for (var u = 0; u < (def.ammoPer || 1); u++) L.used.push(now);
    if (g.addTrauma) g.addTrauma(def.launcher === 'homing' ? 0.22 : 0.16);
    if (IB.AI && IB.AI.hear) IB.AI.hear(g.player.x, g.player.z, 22);
    if (def.launcher === 'homing') return salvo(def, cam, el, mul);
    // straight rocket from the muzzle to the crosshair point, inside the spread cone
    aimPoint(cam, 160, _aim);
    var dx = _aim.x - _mz.x, dy = _aim.y - _mz.y, dz = _aim.z - _mz.z, dl = Math.hypot(dx, dy, dz);
    if (dl < 2.5) { dx = _d.x; dy = _d.y; dz = _d.z; dl = 1; }
    _rt.set(1, 0, 0).applyQuaternion(cam.quaternion); _upv.set(0, 1, 0).applyQuaternion(cam.quaternion);
    var a = Math.random() * Math.PI * 2, rr = Math.sqrt(Math.random()) * Math.tan(spread || 0);
    dx = dx / dl + (_rt.x * Math.cos(a) + _upv.x * Math.sin(a)) * rr; dy = dy / dl + (_rt.y * Math.cos(a) + _upv.y * Math.sin(a)) * rr; dz = dz / dl + (_rt.z * Math.cos(a) + _upv.z * Math.sin(a)) * rr;
    spawnRocket(def, _mz.x, _mz.y, _mz.z, dx, dy, dz, def.speed || 40, { elem: el, mul: mul, sc: 1 });
    if (IB.FX) IB.FX.puff(_mz.x, _mz.y, _mz.z, 4, 0xE9E4F0, 0.12, 0.3, 1.6);
  };

  // ---------------- Torpedo (endgame skill, skills.js): the last round of a gun's magazine ----------------
  // a fast rocket with no direct hit: torpedoMul x the gun's shot damage as a wide splash; the robots it hurts are slowed
  var TORPEDO = { id: 'torpedo', name: 'Torpedo', damage: 0, splash: 0, radius: 4.5, exponent: 0.7, speed: 34, life: 2.2, turn: 0, knockback: 8, slow: 0.25, slowTime: 5 };
  var TORPEDO_EL = { id: 'torpedo', name: '', color: '#5FE3FF', splashMul: 1, radiusMul: 1.15 };
  L.torpedo = function (gun, cam, spread) {
    var sk = IB.SkillFX && IB.SkillFX.fx ? IB.SkillFX.fx : {};
    var base = (GL() ? GL().shotDamage(gun) : gun.damage) * dmgMul(gun);
    var def = Object.assign({}, TORPEDO, { splash: base * (sk.torpedoMul || 5), radius: sk.torpedoRadius || 4.5, slow: sk.torpedoSlow || 0, slowTime: sk.torpedoSlowTime || 5 });
    IB.Weapons.muzzleWorld(cam, _mz);
    cam.getWorldDirection(_d); _mz.addScaledVector(_d, 0.25);
    aimPoint(cam, 160, _aim);
    var dx = _aim.x - _mz.x, dy = _aim.y - _mz.y, dz = _aim.z - _mz.z, dl = Math.hypot(dx, dy, dz);
    if (dl < 2.5) { dx = _d.x; dy = _d.y; dz = _d.z; dl = 1; }
    _rt.set(1, 0, 0).applyQuaternion(cam.quaternion); _upv.set(0, 1, 0).applyQuaternion(cam.quaternion);
    var a = Math.random() * Math.PI * 2, rr = Math.sqrt(Math.random()) * Math.tan(spread || 0);
    dx = dx / dl + (_rt.x * Math.cos(a) + _upv.x * Math.sin(a)) * rr; dy = dy / dl + (_rt.y * Math.cos(a) + _upv.y * Math.sin(a)) * rr; dz = dz / dl + (_rt.z * Math.cos(a) + _upv.z * Math.sin(a)) * rr;
    spawnRocket(def, _mz.x, _mz.y, _mz.z, dx, dy, dz, def.speed, { elem: TORPEDO_EL, mul: 1, sc: 0.8 });
    if (IB.Audio) IB.Audio.play('missile', { pitch: 1.25, gain: 0.5 });
    if (IB.FX) IB.FX.puff(_mz.x, _mz.y, _mz.z, 3, 0x5FE3FF, 0.1, 0.25, 1.2);
  };

  // ---------------- Murmur: locks and the salvo ----------------
  function center(r) { var v = IB.AI.VIS[r.type]; return r.y + (v ? (v.y0 + v.y1) / 2 : 0.6); }
  function lockable(r) { return r.on && !(r.rogue > 0) && r.state !== 'spawn' && r.state !== 'pose' && r.state !== 'off'; }
  var THREAT = { soldier: 0.25, bruiser: 0.25, blader: 0.15, bomber: 0.2, shieldbot: 0.1 };
  /* up to def.locks targets in front: robots in the lock cone with a clear line, best first (centre of the view,
     close, threatening: winding up, attacking or seeing you, heavy types); with fewer robots the aim point and
     spots around it fill the rest. [{robot|null, x, y, z}] */
  L.computeLocks = function (def, cam) {
    var g = G(), AI = IB.AI, o = cam.position, world = g.level.world, out = [], cand = [];
    cam.getWorldDirection(_d);
    var cosCone = Math.cos((def.lockCone || 26) * Math.PI / 180), range = def.lockRange || 60;
    AI.robots.forEach(function (r) {
      if (!lockable(r)) return;
      var cy = center(r), dx = r.x - o.x, dy = cy - o.y, dz = r.z - o.z, d = Math.hypot(dx, dy, dz);
      if (d > range || d < 1) return;
      var c = (dx * _d.x + dy * _d.y + dz * _d.z) / d; if (c < cosCone) return;
      if (!world.los(o.x, o.y, o.z, r.x, cy, r.z)) return;
      var ang = Math.acos(Math.min(1, c)) / ((def.lockCone || 26) * Math.PI / 180);
      var threat = (THREAT[r.type] || 0) + (r.state === 'windup' || r.state === 'attack' ? 0.3 : r.seesPlayer ? 0.12 : 0);
      cand.push({ robot: r, x: r.x, y: cy, z: r.z, score: ang + 0.7 * d / range - threat });
    });
    cand.sort(function (a, b) { return a.score - b.score; });
    for (var i = 0; i < cand.length && out.length < (def.locks || 5); i++) out.push(cand[i]);
    if (out.length < (def.locks || 5)) {
      aimPoint(cam, range, _aim);
      var base = { x: _aim.x, y: _aim.y, z: _aim.z }, n = (def.locks || 5) - out.length;
      if (!out.length) { out.push({ robot: null, x: base.x, y: base.y, z: base.z }); n--; }   // no robots: the aim point first
      var dist = Math.hypot(base.x - o.x, base.z - o.z), rad = Math.max(1.6, Math.min(4, dist * 0.12));
      var yaw = Math.atan2(_d.x, _d.z);
      for (var j = 0; j < n; j++) {
        var a = yaw + Math.PI / 2 + j * (Math.PI * 2 / n);
        var px = base.x + Math.sin(a) * rad, pz = base.z + Math.cos(a) * rad;
        var fy = world.floorAt ? world.floorAt(px, pz, base.y + 0.5) : 0;
        out.push({ robot: null, x: px, y: Math.max(fy + 0.3, Math.min(base.y, fy + 1.2)), z: pz });
      }
    }
    return out;
  };
  function salvo(def, cam, el, mul) {
    var locks = L.computeLocks(def, cam), n = def.missiles || 6;
    L.stats.salvos++;
    showLocks(locks, true);
    _rt.set(1, 0, 0).applyQuaternion(cam.quaternion); _upv.set(0, 1, 0).applyQuaternion(cam.quaternion);
    // the best lock gets the spare missiles (6 over 5 locks: the first one takes two)
    for (var i = 0; i < n; i++) {
      var lk = locks[i % locks.length], a = (i / n) * Math.PI * 2 + 0.4;
      // fan out of the tubes: forward, then up / sideways before they curve in
      var fx = _d.x * 0.75 + _rt.x * Math.cos(a) * 0.55 + _upv.x * (0.45 + Math.sin(a) * 0.35);
      var fy = _d.y * 0.75 + _rt.y * Math.cos(a) * 0.55 + _upv.y * (0.45 + Math.sin(a) * 0.35);
      var fz = _d.z * 0.75 + _rt.z * Math.cos(a) * 0.55 + _upv.z * (0.45 + Math.sin(a) * 0.35);
      L.salvo.push({ t: i * 0.055, def: def, x: _mz.x, y: _mz.y, z: _mz.z, dx: fx, dy: fy, dz: fz, lock: lk, el: el, mul: mul });
    }
  }

  // ---------------- blasts ----------------
  function covered(world, ax, ay, az, bx, by, bz) {
    var dx = bx - ax, dy = by - ay, dz = bz - az, d = Math.hypot(dx, dy, dz);
    if (d < 0.25) return false;
    var h = world.ray(ax, ay, az, dx / d, dy / d, dz / d, d - 0.2);
    return !!(h && h.box);
  }
  function dmgNum(r, dmg, kind) { var v = IB.AI.VIS[r.type]; if (IB.FX.damageNumber) IB.FX.damageNumber(r.x, r.y + (v ? v.y1 : 0.9) + 0.22, r.z, dmg, kind || 'hit'); }
  /* the blast of one rocket: direct hit (robot | null), splash with falloff (x0.5 behind cover) on robots, the
     element on top, self damage like a frag (35 % of the splash, at most 35), canisters, comic explosion */
  function blast(x, y, z, def, el, mul, direct, ctx, small) {
    mul *= IB.SkillFX && IB.SkillFX.boomMul ? IB.SkillFX.boomMul() : 1;   // Boom: rocket damage
    var g = G(), AI = IB.AI, world = ctx.world, p = ctx.player, Dm = IB.Damage;
    var R = Dm.blastRadius((def.radius || 3) * (el.radiusMul || 1), up('blast')) * (small ? small.R : 1);
    var D = (small ? small.D : def.splash * (el.splashMul || 1)) * mul, i, hits = [];
    L.stats.blasts++; L.stats.last = [+x.toFixed(2), +y.toFixed(2), +z.toFixed(2)];
    if (direct && lockable(direct) && !small) {
      var dd = def.damage * mul, killed = AI.damage(direct, dd, { kx: 0, kz: 0, stagger: true }, ctx.onKill);
      dmgNum(direct, dd, 'core'); L.stats.robotHits++;
      if (!killed && IB.HUD.hit) IB.HUD.hit('hit');
    }
    for (i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!lockable(r)) continue;
      var v = AI.VIS[r.type], ry = Math.max(r.y + v.y0, Math.min(r.y + v.y1, y));
      var hx = r.x - x, hz = r.z - z, hd = Math.hypot(hx, hz), d = Math.hypot(hd, ry - y) - v.radius;
      if (d >= R) continue;
      var sd = Dm.splash(D, R, d, def.exponent === undefined ? 0.8 : def.exponent, covered(world, x, y, z, r.x, ry, r.z));
      if (sd <= 0.5) continue;
      var kb = (def.knockback || 6) * (1 - Math.max(0, d) / R) / (hd || 1);
      hits.push(r);
      var k2 = AI.damage(r, sd, { kx: hx * kb, kz: hz * kb, stagger: d < R * 0.6 }, ctx.onKill);
      dmgNum(r, sd, 'hit'); L.stats.robotHits++;
      if (def.slow > 0) { r.slowT = def.slowTime; r.slowMul = def.slow; }   // Torpedo: the robots it hurts are slowed
      if (!k2 && el.dot && IB.Status) IB.Status.apply(r, el.id, sd * el.dot / el.dur, el.dur);
    }
    // the player: a frag's share, capped
    if (p && p.alive) {
      var cy = Math.max(p.y + PLAYER_R, Math.min(p.y + PLAYER_H - PLAYER_R, y));
      var dp = Math.hypot(p.x - x, cy - y, p.z - z) - PLAYER_R;
      if (dp < R) {
        var self = Math.min(def.selfCap || 35, (def.selfMul || 0.35) * Dm.splash(D, R, dp, def.exponent || 0.8, covered(world, x, y, z, p.x, p.y + 1, p.z)));
        if (self > 0.5 && g.hurt) { SELF.x = x; SELF.z = z; g.hurt(SELF, self); L.stats.selfDamage += self; }
      }
    }
    // effects
    var B = IB.Boom && IB.Boom.ready ? IB.Boom : null, c = new THREE.Color(el.color || '#FFB21E').getHex();
    if (IB.Audio) IB.Audio.play('boom', { pos: { x: x, z: z }, gain: small ? 0.55 : def.launcher === 'homing' ? 0.7 : 1, pitch: small ? 1.4 : def.launcher === 'homing' ? 1.2 : 1 });
    if (B) { B.blast(x, y, z, R, 'rocket'); B.onBlast(x, y, z, R); }
    if (IB.FX) IB.FX.puff(x, y + 0.2, z, small ? 3 : 6, c, 0.14, 0.45, 3);
    if (IB.AI.hear) IB.AI.hear(x, z, 18);
    if (small) return;
    if (el.id === 'shock') {
      if (B) B.zap(x, y, z, R * 0.45, c);
      // arcs jump to the nearest robots just outside the blast
      var near = [];
      for (i = 0; i < AI.robots.length; i++) {
        var o = AI.robots[i]; if (!lockable(o) || hits.indexOf(o) >= 0) continue;
        var od = Math.hypot(o.x - x, o.z - z); if (od < el.arcRange + R) near.push({ r: o, d: od });
      }
      near.sort(function (a, b) { return a.d - b.d; });
      near.slice(0, el.arcs || 3).forEach(function (n) {
        var cyy = center(n.r), ad = D * (el.arcMul || 0.35);
        if (B) B.lightning(x, y, z, n.r.x, cyy, n.r.z);
        var k3 = AI.damage(n.r, ad, { stagger: false }, ctx.onKill); dmgNum(n.r, ad, 'shock');
        if (!k3 && IB.Status) IB.Status.apply(n.r, 'shock', ad * el.dot / el.dur, el.dur);
      });
      if (IB.Audio) IB.Audio.play('zap', { pos: { x: x, z: z } });
    } else if (el.id === 'acid') {
      if (B) B.sparks(x, y, z, 0, 0.8, 0, 14, c);
      var fy = world.floorAt ? world.floorAt(x, z, y + 0.3) : 0;
      if (y - fy < 1.6 && IB.SkillFX && IB.SkillFX.acidPool) IB.SkillFX.acidPool(x, z, D * el.dot / el.poolLife * 0.6, el.poolLife, el.pool);
      if (IB.Audio) IB.Audio.play('sizzle', { pos: { x: x, z: z } });
    } else if (el.id === 'boom') {
      // bomblets: small blasts scattered around, a moment later
      for (i = 0; i < (el.bomblets || 3); i++) {
        var b = null; for (var k = 0; k < BOMB_CAP; k++) if (!L.bomblets[k].on) { b = L.bomblets[k]; break; }
        if (!b) break;
        var a = Math.random() * Math.PI * 2, rr = R * (0.45 + Math.random() * 0.4);
        var bx = x + Math.cos(a) * rr, bz = z + Math.sin(a) * rr, by = world.floorAt ? world.floorAt(bx, bz, y + 0.5) + 0.3 : 0.3;
        b.on = true; b.t = 0.14 + i * 0.09 + Math.random() * 0.06; b.x = bx; b.y = by; b.z = bz; b.def = def; b.mul = mul;
        b.R = (el.bombletR || 1.6) / ((def.radius || 3) * (el.radiusMul || 1)); b.D = def.splash * (el.splashMul || 1) * (el.bombletMul || 0.25); b.el = el;
        if (IB.FX) IB.FX.chunk(x, y, z, 1, 6);
      }
    }
  }

  // ---------------- simulation ----------------
  var _tmp = [];
  L.update = function (dt, ctx) {
    var AI = IB.AI, world = ctx.world, i, k;
    // salvo missiles leave the tubes one after another
    for (i = L.salvo.length - 1; i >= 0; i--) {
      var sv = L.salvo[i]; sv.t -= dt; if (sv.t > 0) continue;
      L.salvo.splice(i, 1);
      spawnRocket(sv.def, sv.x, sv.y, sv.z, sv.dx, sv.dy, sv.dz, (sv.def.speed || 30) * 0.45, { elem: sv.el, mul: sv.mul, lock: sv.lock, sc: 0.55 });
      if (IB.Audio) IB.Audio.play('missile', { pitch: 0.9 + Math.random() * 0.25, gain: 0.7 });
    }
    for (i = 0; i < BOMB_CAP; i++) { var b = L.bomblets[i]; if (b.on && (b.t -= dt) <= 0) { b.on = false; blast(b.x, b.y, b.z, b.def, b.el, b.mul, null, ctx, { R: b.R, D: b.D }); } }
    for (i = 0; i < ROCKET_CAP; i++) {
      var r = L.rockets[i]; if (!r.on) continue;
      r.t += dt;
      var d = r.def;
      if (r.homing && r.t > 0.1) {
        var lk = r.lock, tx = lk.x, ty = lk.y, tz = lk.z;
        if (lk.robot && lockable(lk.robot)) { lk.x = tx = lk.robot.x; lk.y = ty = center(lk.robot); lk.z = tz = lk.robot.z; }
        var ex = tx - r.x, ey = ty - r.y, ez = tz - r.z, el2 = Math.hypot(ex, ey, ez) || 1;
        var turn = Math.min(1, (d.turn || 6) * dt * (0.6 + Math.min(1.2, r.t)));
        var nx = r.vx / r.sp + (ex / el2 - r.vx / r.sp) * turn, ny = r.vy / r.sp + (ey / el2 - r.vy / r.sp) * turn, nz = r.vz / r.sp + (ez / el2 - r.vz / r.sp) * turn;
        var nl = Math.hypot(nx, ny, nz) || 1;
        r.sp = Math.min((d.speed || 30) * 1.3, r.sp + 34 * dt);
        r.vx = nx / nl * r.sp; r.vy = ny / nl * r.sp; r.vz = nz / nl * r.sp;
        // proximity fuse on its own target
        if (lk.robot && lockable(lk.robot) && el2 < AI.VIS[lk.robot.type].radius + 0.45) { r.on = false; blast(r.x, r.y, r.z, d, r.elem, r.mul, lk.robot, ctx); lockDone(lk); continue; }
        if (!lk.robot && el2 < 0.5) { r.on = false; blast(tx, ty, tz, d, r.elem, r.mul, null, ctx); lockDone(lk); continue; }
      }
      if (r.t > r.life) { r.on = false; blast(r.x, r.y, r.z, d, r.elem, r.mul, null, ctx); if (r.lock) lockDone(r.lock); continue; }
      var sx = r.x + r.vx * dt, sy = r.y + r.vy * dt, sz = r.z + r.vz * dt, ux = r.vx / r.sp, uy = r.vy / r.sp, uz = r.vz / r.sp, step = r.sp * dt;
      var pr = (d.projRadius || 0.12) * r.sc;
      // robots along the step (capsule test, as the robots' own bolts do)
      var hitR = null;
      for (k = 0; k < AI.robots.length && !hitR; k++) {
        var o = AI.robots[k]; if (!lockable(o)) continue;
        var v = AI.VIS[o.type];
        if (IB.Projectiles.segHitsCapsule(r.x, r.y, r.z, sx, sy, sz, o.x, o.y + v.y0 + v.radius * 0.5, o.y + v.y1 - v.radius * 0.5, o.z, v.radius, pr)) hitR = o;
      }
      if (hitR) { r.on = false; blast(sx - ux * 0.1, sy - uy * 0.1, sz - uz * 0.1, d, r.elem, r.mul, hitR, ctx); if (r.lock) lockDone(r.lock); continue; }
      var h = world.ray(r.x, r.y, r.z, ux, uy, uz, step + pr);
      if (h) {
        r.on = false;
        var hx = r.x + ux * h.t + h.nx * 0.12, hy = r.y + uy * h.t + h.ny * 0.12, hz = r.z + uz * h.t + h.nz * 0.12;
        if (h.box && h.box.kind === 'canister' && IB.Boom) IB.Boom.hitCan(h.box, 999);
        blast(hx, hy, hz, d, r.elem, r.mul, null, ctx);
        if (r.lock) lockDone(r.lock);
        continue;
      }
      r.x = sx; r.y = sy; r.z = sz;
    }
  };

  // ---------------- lock brackets (DOM, over the HUD) ----------------
  function initLocks() {
    var host = document.getElementById('hud') || document.body;
    var css = document.createElement('style');
    css.textContent = '.lk-layer{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:6}' +
      '.lk{position:absolute;left:0;top:0;width:46px;height:46px;margin:-23px 0 0 -23px;will-change:transform;transition:opacity .12s}' +
      '.lk i{position:absolute;width:13px;height:13px;border:3.5px solid #FFB21E;filter:drop-shadow(0 0 0 #15121C) drop-shadow(1.5px 1.5px 0 #15121C)}' +
      '.lk i:nth-child(1){left:0;top:0;border-right:0;border-bottom:0}.lk i:nth-child(2){right:0;top:0;border-left:0;border-bottom:0}' +
      '.lk i:nth-child(3){left:0;bottom:0;border-right:0;border-top:0}.lk i:nth-child(4){right:0;bottom:0;border-left:0;border-top:0}' +
      '.lk b{position:absolute;left:50%;top:-17px;transform:translateX(-50%);font:700 12px/1 "Barlow Condensed",sans-serif;letter-spacing:.08em;color:#FFFDF7;' +
      'background:#F0443A;padding:2px 5px;border:2px solid #15121C;white-space:nowrap}' +
      '.lk.pre{opacity:.55}.lk.pre i{border-color:#FFE7A8;border-width:2.5px}.lk.pre b{display:none}' +
      '.lk.on i{border-color:#F0443A}.lk.spot i{border-style:dashed}';
    document.head.appendChild(css);
    L.layer = document.createElement('div'); L.layer.className = 'lk-layer'; host.appendChild(L.layer);
    for (var i = 0; i < LOCK_CAP; i++) {
      var el = document.createElement('div'); el.className = 'lk'; el.hidden = true;
      el.innerHTML = '<i></i><i></i><i></i><i></i><b>LOCK</b>';
      L.layer.appendChild(el);
      L.locks.push({ on: false, el: el, t: 0, lock: null, live: false, pre: false, cls: '' });
    }
  }
  function showLocks(list, live) {
    for (var i = 0; i < LOCK_CAP; i++) {
      var k = L.locks[i], lk = list[i];
      if (!lk) { if (!live || !k.live) { k.on = false; k.el.hidden = true; } continue; }
      k.on = true; k.lock = lk; k.live = !!live; k.pre = !live; k.t = 0; k.left = live ? 2.6 : 0.3;
      if (live) { lk.marker = k; if (IB.Audio) setTimeout(function () { IB.Audio.play('lock', { gain: 0.6 }); }, i * 40); }
    }
  }
  function lockDone(lk) { var k = lk && lk.marker; if (k && k.lock === lk) { k.pending = (k.pending || 0) + 1; if (k.pending >= 1) k.left = Math.min(k.left, 0.18); } }
  var _p = new THREE.Vector3();
  function syncLocks(dt, g) {
    var cam = IB.Render.camera, w = g.ws && IB.Weapons.current(g.ws), W2 = window.innerWidth, H2 = window.innerHeight;
    // preview while the Murmur is up and ready (a few times a second)
    var ready = w && w.def.launcher === 'homing' && g.ws.state === 'idle' && !g.player.sprinting && g.player.alive && g.mode === 'play' && !g.ws.melee;
    L.preT = (L.preT || 0) - dt;
    var anyLive = L.locks.some(function (k) { return k.on && k.live; });
    if (ready && !anyLive && L.preT <= 0) {
      // preview the robots it would lock (just the aim point when there are none; the spots around it only at launch)
      L.preT = 0.2; var pv = L.computeLocks(w.def, cam), rb = pv.filter(function (k) { return k.robot; });
      showLocks(rb.length ? rb : pv.slice(0, 1), false);
    }
    if (!ready && !anyLive) L.locks.forEach(function (k) { if (k.pre) { k.on = false; k.el.hidden = true; } });
    for (var i = 0; i < LOCK_CAP; i++) {
      var k = L.locks[i]; if (!k.on) continue;
      k.t += dt; k.left -= dt;
      if (k.left <= 0 && k.live) { k.on = false; k.el.hidden = true; k.live = false; k.pending = 0; continue; }
      if (k.pre && k.left <= 0 && !ready) { k.on = false; k.el.hidden = true; continue; }
      var lk = k.lock, x = lk.x, y = lk.y, z = lk.z;
      if (lk.robot && lockable(lk.robot)) { x = lk.robot.x; y = center(lk.robot); z = lk.robot.z; }
      _p.set(x, y, z).project(cam);
      if (_p.z > 1 || _p.z < -1) { k.el.hidden = true; continue; }
      var sx = (_p.x * 0.5 + 0.5) * W2, sy = (-_p.y * 0.5 + 0.5) * H2;
      var sc = k.live ? (k.t < 0.16 ? 1.9 - 0.9 * k.t / 0.16 : 1) : 0.8, rot = k.live && k.t < 0.16 ? 45 * (1 - k.t / 0.16) : 0;
      k.el.hidden = false;
      var cls = 'lk' + (k.live ? ' on' : ' pre') + (lk.robot ? '' : ' spot');
      if (cls !== k.cls) { k.cls = cls; k.el.className = cls; }
      k.el.style.transform = 'translate(' + sx.toFixed(1) + 'px,' + sy.toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg) scale(' + sc.toFixed(3) + ')';
      k.el.style.opacity = k.live && k.left < 0.2 ? (k.left / 0.2).toFixed(2) : '';
    }
  }

  // ---------------- rocket crates (dropped by soldiers) ----------------
  function pending() { var n = 0; L.crates.forEach(function (c) { if (c.on) n += c.n; }); return n; }
  L.spawnCrate = function (x, z, y, n) {
    var c = null, i; for (i = 0; i < CRATE_CAP; i++) if (!L.crates[i].on) { c = L.crates[i]; break; }
    if (!c) { c = L.crates[0]; for (i = 1; i < CRATE_CAP; i++) if (L.crates[i].t > c.t) c = L.crates[i]; }
    var g = G(), W0 = g.level && g.level.world, fy = W0 && W0.floorAt ? W0.floorAt(x, z, (y || 0) + 0.6) : 0;
    c.on = true; c.x = x; c.z = z; c.y = fy; c.n = n; c.t = 0; c.fullT = 0; c.mesh.visible = true; c.mesh.position.set(x, fy + 0.25, z);
    L.stats.crates++; L.stats.crateRockets += n;
    if (IB.FX) IB.FX.puff(x, fy + 0.4, z, 5, 0xFF7A2E, 0.12, 0.4, 1.8);
    return c;
  };
  function syncCrates(dt, t, g) {
    var p = g.player, cap = GL() ? GL().ROCKET.cap : 16;
    L.crates.forEach(function (c, i) {
      if (!c.on) return;
      c.t += dt;
      c.mesh.rotation.y = t * 1.3 + i; c.mesh.position.y = c.y + 0.25 + Math.sin(t * 3 + i) * 0.03;
      if (IB.FX && IB.FX.blob) IB.FX.blob(c.x, c.y, c.z, 0.38);
      if (!p.alive || Math.hypot(p.x - c.x, p.z - c.z) > 0.95 || p.y > c.y + 1 || p.y < c.y - 0.8) return;
      var room = cap - L.total();
      if (room <= 0) { if (c.fullT <= 0 && IB.HUD.toast) IB.HUD.toast('Rockets full (' + cap + ')', 1.2); c.fullT = 3; c.fullT -= dt; return; }
      var take = Math.min(room, c.n);
      pool().rocket += take; c.n -= take;
      if (IB.HUD.toast) IB.HUD.toast('+' + take + ' rocket' + (take > 1 ? 's' : ''), 1.2);
      if (IB.Audio) IB.Audio.play('pickup', { pitch: 0.8 });
      if (c.n <= 0) { c.on = false; c.mesh.visible = false; }
    });
    L.crates.forEach(function (c) { if (c.on && c.fullT > 0) c.fullT -= dt; });
  }
  L.radar = function () { return L.crates.filter(function (c) { return c.on; }).map(function (c) { return { x: c.x, z: c.z, kind: 'rockets' }; }); };

  /* the director's view of the player right now (core/gunlevel.js rocketNeed / rocketDrop) */
  L.directorState = function () {
    var g = G(), s = g.slot || {}, ws = g.ws, owned = launcherIds(s.arsenal).length > 0, per = 0, carried = false;
    if (ws) Object.keys(ws.guns).forEach(function (id) { var d = ws.guns[id].def; if (d.ammo) { carried = true; per = Math.max(per, d.ammoPer || 1); } });
    var now = g.run ? g.run.time : 0, win = GL() ? GL().ROCKET.useWindow : 90;
    while (L.used.length && L.used[0] < now - win) L.used.shift();
    return { owned: owned, carried: carried, ammo: L.total(), pending: pending(), used: L.used.length, per: per || 1, dry: L.dry || 0, dropped: L.dropped || 0, budget: L.budget };
  };
  L.onKill = function (r) {
    if (IB.WeaponDrops && IB.WeaponDrops.rollLauncher) IB.WeaponDrops.rollLauncher(r);
    var w = GL() ? GL().rocketDropWeight(r.type) : 0;   // soldiers 1, melee bladers 0.5
    if (w <= 0) return;
    var st = L.directorState(); st.w = w;
    var n = GL().rocketDrop(st);
    if (n > 0) { L.spawnCrate(r.x + 0.5, r.z + 0.3, r.fy || r.y || 0, n); L.dropped = (L.dropped || 0) + n; L.dry = 0; }
    else if (st.owned) L.dry = (L.dry || 0) + 1;
  };
  /* an armory rack gun on levels 14+: now and then a launcher instead */
  L.rackPick = function (rk) {
    var g = G(), gl = GL(); if (!gl || !g.plan || g.plan.level < gl.LAUNCHER_LEVEL || Math.random() >= gl.RACK_LAUNCHER) return;
    var id = Math.random() < 0.6 ? 'hothead' : 'murmur'; if (!IB.Weapons.playable(id)) return;
    rk.id = id; rk.roll = gl.rollLauncher(IB.WEAPONS[id]); rk.tier = IB.WeaponDrops.rollTier(gl.LAUNCHER_TIERS);
  };

  // ---------------- render ----------------
  var _glowHex = {};
  function glowFor(g) {
    // the Hothead's element canister glows in its element's colour (viewmodel, at the WPN_HOTHEAD_ELEM socket)
    var W = IB.Weapons, m = W.models && W.models.hothead; if (!m) return;
    if (!m.elemGlow) {
      var sock = m.mesh.getObjectByName('WPN_HOTHEAD_ELEM'); if (!sock) { m.elemGlow = false; return; }
      var geo = new THREE.CylinderGeometry(0.0128, 0.0128, 0.13, 10); geo.rotateX(Math.PI / 2);
      m.elemGlow = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xffffff })); m.elemGlow.frustumCulled = false;
      sock.add(m.elemGlow);
    }
    if (!m.elemGlow) return;
    var roll = IB.WeaponDrops.rollOf('hothead'), el = elemOf(IB.WEAPONS.hothead, roll);
    var hex = _glowHex[el.id] || (_glowHex[el.id] = new THREE.Color(el.id === 'none' ? '#FFD86A' : el.color));
    m.elemGlow.material.color.copy(hex).multiplyScalar(0.8 + 0.2 * Math.sin((g.run ? g.run.time : 0) * 7));
  }
  L.sync = function (dt, t, g) {
    settle();
    var i, n = 0;
    for (i = 0; i < ROCKET_CAP; i++) {
      var r = L.rockets[i]; if (!r.on) continue;
      _d.set(r.vx, r.vy, r.vz).divideScalar(r.sp || 1);
      _q.setFromUnitVectors(_nz, _d);
      _v.set(r.x, r.y, r.z);
      if (L.mesh) { _m.compose(_v, _q, _s.set(r.sc, r.sc, r.sc)); L.mesh.setMatrixAt(n, _m); }
      var fl = 0.075 * r.sc * (0.85 + Math.random() * 0.4);
      _v.set(r.x - _d.x * 0.27 * r.sc, r.y - _d.y * 0.27 * r.sc, r.z - _d.z * 0.27 * r.sc);
      _m.compose(_v, _q, _s.set(fl, fl, fl * 1.8)); L.glow.setMatrixAt(n, _m); L.glow.setColorAt(n, _c.set(r.color));
      n++;
      // smoke trail: grey puffs with a touch of the element colour
      r.puff -= dt;
      if (r.puff <= 0 && IB.FX) {
        r.puff = r.sc < 1 ? 0.045 : 0.03;
        IB.FX.puff(_v.x, _v.y, _v.z, 1, Math.random() < 0.3 ? r.color : 0xE9E4F0, 0.07 * r.sc + 0.05, 0.26 * r.sc + 0.1, 0.25, -0.4);
      }
    }
    if (L.mesh) { L.mesh.count = n; L.mesh.instanceMatrix.needsUpdate = true; }
    L.glow.count = n; L.glow.instanceMatrix.needsUpdate = true; if (L.glow.instanceColor) L.glow.instanceColor.needsUpdate = true;
    syncCrates(dt, t, g);
    syncLocks(dt, g);
    glowFor(g);
    if (g.slot && g.ws) g.slot.rockets = L.total();
  };

  // ---------------- test hooks (merged into window.__TEST__ by game.js) ----------------
  IB.LauncherTest = {
    // give a launcher: arsenal + loadout (in hand), roll {mag, elem}, tier, level, and the rocket pool
    giveLauncher: function (id, o) {
      o = o || {};
      var g = G(), s = g.slot, def = IB.WEAPONS[id], gl = GL();
      s.arsenal = s.arsenal || []; if (s.arsenal.indexOf(id) < 0) s.arsenal.push(id);
      s.gunTier = s.gunTier || {}; s.gunTier[id] = o.tier || 'gray';
      s.gunLevel = s.gunLevel || {}; s.gunLevel[id] = o.level || (g.plan && g.plan.level) || 14;
      s.gunRoll = s.gunRoll || {}; s.gunRoll[id] = gl.fixRoll(def, { mag: o.mag || def.mag, elem: o.elem || 'none' });
      var lo = (s.loadout || []).filter(function (x) { return x !== id; }); lo.unshift(id); s.loadout = lo.slice(0, IB.Skills.loadoutMax(s.highest || 0));
      if (g.bank) delete g.bank[id];
      IB.Weapons.setLoadout(g.ws, s.loadout, g.bank);
      var gun = g.ws.guns[id]; if (gun) { gun._settled = true; gun.mag = IB.Weapons.magSize(g.ws, def); }
      pool().rocket = o.rockets === undefined ? 10 : o.rockets;
      IB.Weapons.equip(g.ws, id, true);
      return !!gun;
    },
    // pull the trigger once through the weapon code (as a click would)
    fireLauncher: function () {
      var g = G(), ws = g.ws, gun = IB.Weapons.current(ws); if (!gun || !gun.def.ammo) return false;
      ws.next = 0; ws.state = 'idle'; ws.burst = 0;
      var mag = gun.mag;
      IB.Weapons.update(ws, 0.001, { player: g.player, cam: IB.Render.camera, input: { fire: true, firePressed: true, aim: false }, shoot: function () { }, rocket: L.fire });
      return gun.mag < mag;
    },
    launcherState: function () {
      var g = G(), gun = g.ws && IB.Weapons.current(g.ws);
      return { pool: pool().rocket, total: L.total(), saved: g.slot ? g.slot.rockets : 0, inFlight: L.rockets.filter(function (r) { return r.on; }).length + L.salvo.length,
        locks: L.locks.filter(function (k) { return k.on && k.live; }).length, previews: L.locks.filter(function (k) { return k.on && k.pre && !k.el.hidden; }).length,
        crates: L.crates.filter(function (c) { return c.on; }).map(function (c) { return { x: c.x, z: c.z, n: c.n }; }),
        dropped: L.dropped || 0, budget: L.budget, dry: L.dry || 0, weapon: gun ? gun.id : null, mag: gun ? gun.mag : 0,
        magSize: gun ? IB.Weapons.magSize(g.ws, gun.def) : 0, state: g.ws ? g.ws.state : '', stats: Object.assign({}, L.stats),
        director: L.directorState(), need: GL() ? GL().rocketNeed(L.directorState()) : 0 };
    },
    computeLocks: function () { var w = IB.Weapons.current(G().ws); return L.computeLocks(w ? w.def : IB.WEAPONS.murmur, IB.Render.camera).map(function (k) { return { robot: !!k.robot, type: k.robot ? k.robot.type : null, x: k.x, y: k.y, z: k.z }; }); },
    spawnCrate: function (n, dx, dz) { var p = G().player; return !!L.spawnCrate(p.x + (dx || 0), p.z + (dz === undefined ? -2.5 : dz), p.y, n || 3); },
    // a player kill of a soldier through the director (no robot needed)
    bladerKill: function (x, z) { var p = G().player; L.onKill({ type: 'blader', x: x === undefined ? p.x + 3 : x, z: z === undefined ? p.z - 3 : z, y: 0, fy: 0 }); return L.dropped || 0; },
    soldierKill: function (x, z) { var p = G().player; L.onKill({ type: 'soldier', x: x === undefined ? p.x + 3 : x, z: z === undefined ? p.z - 3 : z, y: 0, fy: 0 }); return L.dropped || 0; },
    setRockets: function (n) { pool().rocket = n; },
    clearCrates: function () { L.crates.forEach(function (c) { c.on = false; c.mesh.visible = false; }); }
  };
})(window.IB = window.IB || {});
