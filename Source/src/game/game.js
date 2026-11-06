/* INKBOLT game: boot, title scene, level flow (zones, waves, gates, trail, hatch), combat glue,
   death/respawn, pause, results + save, performance guard, test hooks. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL, R = IB.Render, Z = IB.Zones, AI = IB.AI, FX = IB.FX, W = IB.Weapons, HUD = IB.HUD, M = IB.Menus, Inp = IB.Input, A = IB.Audio;
  var params = new URLSearchParams(location.search);
  var AUTOTEST = params.get('autotest') === '1';
  var G = IB.Game = { mode: 'boot', errors: [] };
  var STEP = 1 / 60;
  var _v = new THREE.Vector3(), _v2 = new THREE.Vector3();

  // ---------------- storage ----------------
  function lsBackend() {
    var mem = {};
    function ok() { try { var k = '__ib'; localStorage.setItem(k, '1'); localStorage.removeItem(k); return true; } catch (e) { return false; } }
    if (!ok()) return { getItem: function (k) { return k in mem ? mem[k] : null; }, setItem: function (k, v) { mem[k] = String(v); }, removeItem: function (k) { delete mem[k]; }, keys: function () { return Object.keys(mem); } };
    return {
      getItem: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
      setItem: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* quota */ } },
      removeItem: function (k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } },
      keys: function () { var a = []; try { for (var i = 0; i < localStorage.length; i++) a.push(localStorage.key(i)); } catch (e) { /* ignore */ } return a; }
    };
  }

  // ---------------- boot ----------------
  function bootProgress(f) { var b = document.getElementById('bootBar'); if (b) b.style.width = Math.round(f * 100) + '%'; }
  G.boot = function () {
    window.addEventListener('error', function (e) { G.errors.push(String(e.message || e)); });
    window.addEventListener('unhandledrejection', function (e) { G.errors.push('rejection: ' + (e.reason && e.reason.message || e.reason)); });
    IB.Plat.init();
    G.store = IB.Saves.create(lsBackend());
    G.settings = G.store.loadSettings();
    bootProgress(0.2);
    var canvas = document.getElementById('c');
    try { R.init(canvas); } catch (e) {
      document.getElementById('boot').innerHTML = '<div class="plate ink panel"><h2>WebGL is off</h2><p>INKBOLT needs WebGL. Turn on hardware acceleration in your browser settings, then reload.</p></div>';
      return;
    }
    R.renderer.info.autoReset = false;
    var isPhone = Inp.touch || Math.min(window.innerWidth, window.innerHeight) < 500;
    G.applyGraphics(isPhone);
    Inp.init(canvas);
    if (Inp.touch) document.body.classList.add('touch-on');
    HUD.init(); M.init(); wireMenus();
    // Blender GLBs: common, weapons, bots and the title/level-1 kit (brief 4.2 boot order)
    // Blender GLBs: common, weapons, bots and the first level's theme kit (brief 4.2 boot order); other kits load per level
    var saved0 = G.store.newest();
    G.plan = IB.LEVEL_PLANS[params.get('plan') || (saved0 && saved0.plan) || IB.CAMPAIGN[0]] || IB.LEVEL_PLANS[IB.CAMPAIGN[0]];
    IB.Assets.load(['common', 'weapons', 'bots', Z.themeOf(G.plan).family], function (f) { bootProgress(0.2 + f * 0.7); })
      .then(bootAfterAssets)
      .catch(function (e) {
        G.errors.push(String(e && e.message || e));
        document.getElementById('boot').innerHTML = '<div class="plate ink panel"><h2>Could not load</h2><p>' + String(e && e.message || e) + '</p></div>';
      });
  };
  function bootAfterAssets() {
    FX.init(R.scene); AI.init(R.scene); W.init(R.vmScene); IB.Projectiles.init(R.scene);
    G.buildLevel();
    G.player = IB.Player.create();
    G.ws = W.create(['pip', 'buzz'], {});
    W.equip(G.ws, 'pip', true);
    G.applySettings();
    bootProgress(1);
    window.addEventListener('resize', onResize);
    window.addEventListener('orientationchange', function () { setTimeout(onResize, 60); });
    if (window.visualViewport) window.visualViewport.addEventListener('resize', onResize);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) return; if (G.mode === 'play') G.pause(); IB.Plat.stop(); });
    Inp.onUnlock = function () { if (G.mode === 'play' && !G.dead && !AUTOTEST) G.pause(); };
    document.addEventListener('pointerdown', firstGesture, { once: false });
    document.addEventListener('keydown', firstGesture);
    G.last = performance.now();
    requestAnimationFrame(frame);
    if (AUTOTEST) { G.startLevel(); }
    else G.toTitle();
    setTimeout(function () { var b = document.getElementById('boot'); b.classList.add('out'); setTimeout(function () { b.remove(); }, 320); IB.Plat.loaded(); }, 60);
  }
  function firstGesture() { if (!A.ctx) { A.init(); A.setEnabled(G.settings.sfx); } A.resume(); }
  function onResize() { R.resize(); HUD.last.xh = null; if (G.mode === 'title') placeTitleCam(); }

  G.applyGraphics = function (isPhone) {
    var g = G.settings.graphics;
    G.guard = { on: g === 'auto', failed: {}, slowT: 0, fastT: 0, steppedUp: false, samples: [], avg: 16 };
    G.setTier(g === 'high' ? 'high' : g === 'low' ? 'low' : (isPhone ? 'medium' : 'high'));
  };
  var TIERS = {
    high: { decals: 256, particles: 1, fog: 120 }, medium: { decals: 160, particles: 0.7, fog: 100 },
    low: { decals: 96, particles: 0.5, fog: 80 }, potato: { decals: 64, particles: 0.35, fog: 60 }
  };
  var TIER_ORDER = ['potato', 'low', 'medium', 'high'];
  G.setTier = function (t) {
    R.tier = t; var T = TIERS[t];
    FX.decalLimit = T.decals; FX.particleScale = T.particles;
    R.tierFogFar = T.fog;
    if (R.scene.fog) R.scene.fog.far = Math.min(T.fog, R.envFogFar || 999);
    R.resize();
  };
  G.applySettings = function () {
    var s = G.settings;
    R.baseFov = s.fov; R.applyFov();
    if (A.ctx) A.setEnabled(s.sfx);
    document.getElementById('flash').classList.toggle('reduce', !!s.reduceFlash);
  };

  // ---------------- level ----------------
  G.disposeLevel = function () {
    if (!G.level) return;
    var shared = new Set(Object.keys(IB.Assets.geo).map(function (k) { return IB.Assets.geo[k]; }));
    G.level.root.traverse(function (o) {
      if (o.isMesh || o.isInstancedMesh) {
        if (o.geometry && !shared.has(o.geometry)) o.geometry.dispose();
        if (o.material && (o.material.isMeshBasicMaterial || o.material.isShaderMaterial)) o.material.dispose();
      }
    });
    R.scene.remove(G.level.root);
    (G.weaponStands || []).forEach(function (w) { R.scene.remove(w.group); });
    G.weaponStands = [];
    G.level = null;
  };
  G.buildLevel = function () {
    G.disposeLevel();
    G.level = Z.buildLevel(G.plan, R.scene);
    R.applyEnv(G.level.theme.env || {});
    AI.setLevel(G.plan.level);
  };
  // a level's theme kit is loaded on demand (embedded in the single-file build, assets/*.glb otherwise)
  G.ensureTheme = function (plan) { return IB.Assets.load([Z.themeOf(plan).family]); };
  G.switchPlan = function (plan) {
    return G.ensureTheme(plan).then(function () { G.plan = plan; G.buildLevel(); });
  };

  function resetLevelState() {
    var L = G.level;
    AI.clear(); FX.clear(); IB.Projectiles.clear();
    L.zones.forEach(function (z, i) {
      z.state = 'idle'; z.wave = -1; z.waveT = 0; z.queue = []; z.clearT = -1; z.spawnedTotal = 0;
      if (z.entryGate) Z.setGate(z.entryGate, i > 0, true);
      Z.setGate(z.exitGate, false, true);
    });
    L.trails.forEach(function (t) { Z.lightTrail(t, 0); t.litT = -1; });
    G.zone = 0; Z.setVisible(L, 0);
    G.pickups.forEach(function (p) { p.mesh.visible = false; p.on = false; });
    L.zones.forEach(function (z) { z.pickups.forEach(function (pk) { G.spawnPickup(pk.kind, pk.x, pk.z, true); }); });
    placeWeaponStands(G.plan.weapons || []);
  }

  // ---------------- new weapons waiting at the start of a level ----------------
  function placeWeaponStands(ids) {
    (G.weaponStands || []).forEach(function (w) { R.scene.remove(w.group); });
    G.weaponStands = [];
    if (G.mode === 'title') return;
    var z0 = G.level.zones[0], theme = G.level.theme, A = IB.Assets, standName = IB.themePiece(theme, theme.stand || 'Crate');
    if (!G.worldWpnMat) G.worldWpnMat = R.toonMaterial({ map: A.palette.weapons, baked: A.BAKED.weapons });
    ids = ids.filter(function (id) { return A.node['WPN_' + id.toUpperCase()] && IB.WEAPONS[id]; });
    ids.forEach(function (id, i) {
      var side = ids.length === 1 ? 0 : (i === 0 ? -1.6 : 1.6);
      var x = z0.entry.x + side, zc = z0.entry.z - 3.8;
      var grp = new THREE.Group(); grp.position.set(x, 0, zc);
      if (A.geo[standName]) grp.add(new THREE.Mesh(A.get(standName), A.mat[A.family[standName]]));
      var gun = new THREE.Mesh(A.get('WPN_' + id.toUpperCase()), G.worldWpnMat);
      gun.scale.setScalar(1.35);
      gun.rotation.set(70 * Math.PI / 180, 0.35 * (side > 0 ? -1 : 1), 0);   // standing on its stock, leaning back on the crate
      gun.position.set(0, 0.32, 0.72);
      grp.add(gun);
      var ring = new THREE.Mesh(new THREE.RingGeometry(0.55, 0.72, 28), new THREE.MeshBasicMaterial({ color: PAL.teal, transparent: true, opacity: 0.85 }));
      ring.rotation.x = -Math.PI / 2; ring.position.set(0, 0.02, 0.85); grp.add(ring);
      R.scene.add(grp);
      G.level.world.add(x - 0.5, 0, zc - 0.5, x + 0.5, 1, zc + 0.5, 'cover', 0);
      G.weaponStands.push({ id: id, group: grp, gun: gun, ring: ring, x: x, z: zc + 0.85, taken: false });
    });
  }
  function updateWeaponStands(t) {
    var p = G.player;
    (G.weaponStands || []).forEach(function (w) {
      if (w.taken) return;
      var k = 1 + Math.sin(t * 4) * 0.08; w.ring.scale.set(k, k, k);
      if (Math.hypot(p.x - w.x, p.z - w.z) < 1.5 && p.alive) takeWeapon(w);
    });
  }
  function takeWeapon(w) {
    var def = IB.WEAPONS[w.id], ws = G.ws;
    // one weapon per class: the new one replaces the old one (brief 5.2 carrying rule)
    Object.keys(ws.guns).forEach(function (k) { if (IB.WEAPONS[k].cls === def.cls && k !== w.id) { delete ws.guns[k]; if (ws.slots[def.slot] === k) delete ws.slots[def.slot]; } });
    W.give(ws, w.id);
    W.equip(ws, w.id);
    w.taken = true; w.group.remove(w.gun); w.ring.visible = false;
    ensureSlot();
    G.slot.owned = Object.keys(ws.guns);
    G.store.save(G.slot);
    if (HUD.pickup) HUD.pickup(def.name, def.cls); else HUD.toast('New weapon: ' + def.name, 2.2);
    A.play('pickup'); A.play('draw');
  }

  G.startLevel = function (opts) {
    M.hide();
    G.mode = 'play'; G.dead = false; G.paused = false; G.complete = false;
    if (!G.pickups) initPickups();
    resetLevelState();
    var p = G.player, z0 = G.level.zones[0];
    Object.assign(p, IB.Player.create());
    var fx = IB.Upgrades && G.slot ? IB.Upgrades.effects(G.slot.upgrades || {}) : {};
    G.fx = fx;
    p.maxHp = fx.maxHp || 100; p.health = p.maxHp; p.speedMul = fx.speedMul || 1; p.jumpMul = fx.jumpMul || 1; p.doubleJump = !!fx.doubleJump;
    p.staminaMax = 4 * (fx.staminaMul || 1); p.stamina = p.staminaMax;
    p.x = z0.entry.x; p.z = z0.entry.z; p.y = 0; p.yaw = 0; p.pitch = 0;
    ensureSlot();
    var owned = (G.slot.owned && G.slot.owned.length ? G.slot.owned : (G.plan.start || ['pip'])).filter(function (id) { return IB.WEAPONS[id]; });
    G.ws = W.create(owned, { reloadMul: fx.reloadMul, recoilMul: fx.recoilMul, spreadMul: fx.spreadMul, magLevel: (G.slot && G.slot.upgrades && G.slot.upgrades.mag) || 0 });
    var first = Object.keys(G.ws.guns).sort(function (a, b) { return IB.WEAPONS[b].slot - IB.WEAPONS[a].slot; })[0] || 'pip';
    W.equip(G.ws, first, true);
    G.run = { time: 0, kills: 0, shots: 0, hits: 0, coreHits: 0, deaths: 0, gems: 0, retries: 3, started: false, introT: AUTOTEST ? 0.05 : 2.3 };
    G.shake = 0; G.trauma = 0; G.hitstop = 0; G.deathT = 0;
    G.fade = opts && opts.fadeIn ? { t: 0, dur: 1.4 } : null;
    setDim(G.fade ? 1 : 0);
    HUD.reset(); HUD.show(true); document.getElementById('touch').hidden = !Inp.touch;
    HUD.pips(G.level.zones.length, 0, 0);
    if (!AUTOTEST) M.intro({ level: G.plan.level, name: G.plan.name, zones: G.level.zones.length, line: G.plan.intro }, 2.2);
    // save at level start
    ensureSlot(); G.slot.level = G.plan.level; G.slot.plan = G.plan.id; G.slot.owned = Object.keys(G.ws.guns); G.store.save(G.slot); G.saved = true;
    Inp.enabled = true; Inp.reset();
    if (!AUTOTEST) Inp.requestLock();
  };
  function ensureSlot() {
    if (G.slot) return;
    var newest = G.store.newest();
    if (newest) { G.slot = newest; return; }
    var id = G.store.freeSlot() || 1;
    G.slot = G.store.newSlot(id, (Math.random() * 1e9) | 0);
  }

  function startZone(i) {
    var z = G.level.zones[i];
    if (z.state !== 'idle') return;
    z.state = 'active'; z.wave = -1; z.waveT = 0; z.startT = 0; z.queue = []; z.clearT = -1;
    G.zone = i; Z.setVisible(G.level, i);
    if (z.entryGate && i > 0) { Z.setGate(z.entryGate, false); A.play('gateShut', { pos: z.entryGate, gain: 0.9 }); }
    HUD.pips(G.level.zones.length, i, i);
    if (i > 0) HUD.toast('Zone ' + (i + 1) + ' of ' + G.level.zones.length, 1.6);
  }
  function queueWave(z, w) {
    z.wave = w; z.waveT = 0;
    var p = G.player, list = z.plan.waves[w] || [], k = 0;
    var spawns = z.spawns.filter(function (s) { return Math.hypot(s.x - p.x, s.z - p.z) >= 6; });
    if (!spawns.length) spawns = z.spawns.slice();
    var off = (Math.random() * spawns.length) | 0;
    list.forEach(function (entry) {
      for (var n = 0; n < entry[1]; n++) {
        var s = spawns[(off + k) % spawns.length];
        var type = AI.types[entry[0]] ? entry[0] : 'crawler';   // robots without a model yet fall back to the Crawler
        z.queue.push({ type: type, x: s.x, z: s.z, t: 0.18 * k + Math.floor(k / spawns.length) * 0.8 });
        k++;
      }
    });
  }
  function updateZones(dt) {
    var L = G.level, p = G.player;
    // entry triggers: player crosses into the next idle zone past its entry gate
    for (var i = 0; i < L.zones.length; i++) {
      var z = L.zones[i];
      if (z.state === 'idle' && (i === 0 || L.zones[i - 1].state === 'cleared')) {
        var inside = p.x > z.ox + 0.5 && p.x < z.ox + z.w - 0.5 && p.z > z.oz + 0.5 && p.z < z.oz + z.h - 1.6;
        if (i === 0 ? G.run.started : inside) startZone(i);
      }
      if (z.state === 'active') {
        z.startT += dt; z.waveT += dt;
        if (z.wave < 0 && z.startT >= 1.0) queueWave(z, 0);
        for (var q = z.queue.length - 1; q >= 0; q--) {
          var e = z.queue[q]; e.t -= dt;
          if (e.t <= 0) {
            var dx = p.x - e.x, dz = p.z - e.z, d = Math.hypot(dx, dz) || 1, tx = e.x + dx / d * 1.3, tz = e.z + dz / d * 1.3;
            if (!Z.isOpen(z, tx, tz)) { tx = e.x + dx / d * 0.7; tz = e.z + dz / d * 0.7; }
            if (AI.spawn(e.type, e.x, e.z, i, tx, tz)) { A.play('hop', { pos: e }); z.queue.splice(q, 1); z.spawnedTotal++; }
            else e.t = 0.3;
          }
        }
        var alive = AI.alive(i) + z.queue.length;
        if (z.wave >= 0 && z.wave < z.plan.waves.length - 1 && z.queue.length === 0 && (alive <= 4 || z.waveT > 25)) queueWave(z, z.wave + 1);
        if (z.wave === z.plan.waves.length - 1 && alive === 0 && z.queue.length === 0) {
          if (z.clearT < 0) z.clearT = 0;
          z.clearT += dt;
          if (z.clearT >= 0.4) clearZone(i);
        }
      }
    }
    // trail lighting in sequence (one arrow every 0.12 s)
    L.trails.forEach(function (t) {
      if (t.litT < 0) return;
      t.litT += dt;
      var n = Math.min(t.count, Math.floor(t.litT / 0.12) + 1);
      if (n !== t.lit) Z.lightTrail(t, n);
    });
    // gates animate
    L.zones.forEach(function (z) {
      [z.entryGate, z.exitGate].forEach(function (g) {
        if (!g || g.open === g.target) return;
        g.open += Math.sign(g.target - g.open) * g.speed * dt;
        if ((g.target === 1 && g.open > 1) || (g.target === 0 && g.open < 0)) g.open = g.target;
        Z.applyGate(g);
      });
    });
    // exit hatch
    if (L.zones[L.zones.length - 1].state === 'cleared' && !G.complete) {
      // walking the exit waypath: the screen dims with distance, then the next level loads
      var h = L.hatch, f = Math.max(0, Math.min(1, (h.z0 - p.z) / (h.z0 - h.z)));
      if (p.z < h.z0 && Math.abs(p.x - h.x) < 3) setDim(Math.pow(f, 1.4) * 0.96);
      if (f >= 0.95 || Math.hypot(p.x - h.x, p.z - h.z) < h.r) levelExit();
    }
  }
  function clearZone(i) {
    var z = G.level.zones[i];
    z.state = 'cleared';
    FX.vacuumGems(i);
    Z.setGate(z.exitGate, true);
    A.play('gate', { pos: z.exitGate });
    G.level.trails[i].litT = 0;
    Z.setVisible(G.level, i);   // keep this zone (the player stands in it) and the next one drawn
    HUD.pips(G.level.zones.length, i + 1, i + 1);
    HUD.toast(i + 1 < G.level.zones.length ? 'Zone clear. Follow the arrows.' : 'Level clear. Get to the hatch.', 2.4);
  }

  // ---------------- level exit, loading screen, next level ----------------
  function setDim(f) {
    G.dimV = f;
    if (HUD.dim) { HUD.dim(f); return; }
    var el = document.getElementById('dimFallback');
    if (!el) { el = document.createElement('div'); el.id = 'dimFallback'; el.style.cssText = 'position:fixed;inset:0;background:#15121C;pointer-events:none;opacity:0'; document.body.appendChild(el); }
    el.style.opacity = f;
  }
  G.setDim = setDim;
  function bankLevel() {
    var L = G.plan.level, robots = G.run.gems;
    var clear = IB.Gems ? IB.Gems.clearBonus(L) : 15 + 5 * L;
    var nd = G.run.deaths === 0 ? (IB.Gems ? IB.Gems.noDeathBonus(robots) : Math.floor(robots * 0.25)) : 0;
    ensureSlot();
    G.slot.gems = (G.slot.gems || 0) + clear + nd;
    G.slot.highest = Math.max(G.slot.highest || 0, L);
    G.slot.stats = G.slot.stats || {};
    G.slot.stats.kills = (G.slot.stats.kills || 0) + G.run.kills;
    G.slot.stats.deaths = (G.slot.stats.deaths || 0) + G.run.deaths;
    G.slot.stats.time = (G.slot.stats.time || 0) + Math.round(G.run.time);
    G.slot.stats.coreHits = (G.slot.stats.coreHits || 0) + G.run.coreHits;
    G.slot.best = G.slot.best || {}; var key = String(L);
    if (!G.slot.best[key] || G.run.time < G.slot.best[key]) G.slot.best[key] = Math.round(G.run.time);
    G.slot.owned = Object.keys(G.ws.guns);
    G.lastResults = { time: G.run.time, kills: G.run.kills, corePct: G.run.hits ? Math.round(G.run.coreHits / G.run.hits * 100) : 0, deaths: G.run.deaths,
      gemsRobots: robots, gemsClear: clear, gemsNoDeath: nd, gemsTotal: robots + clear + nd };
  }
  function levelExit() {
    var next = G.plan.next && IB.LEVEL_PLANS[G.plan.next];
    if (!next) { levelComplete(); return; }
    G.complete = true; G.mode = 'loading';
    Inp.enabled = false; Inp.releaseLock(); IB.Plat.stop();
    bankLevel();
    var r = G.lastResults;
    G.slot.plan = next.id; G.slot.level = next.level;
    G.store.save(G.slot);
    setDim(1);
    HUD.show(false); document.getElementById('touch').hidden = true;
    var line = 'Level ' + G.plan.level + ' cleared · ' + r.kills + ' robots · ' + HUD.mmss(r.time) + ' · +' + r.gemsTotal + ' gems';
    var t0 = performance.now();
    if (M.loading) M.loading({ level: next.level, name: next.name, line: line }); else M.intro({ level: next.level, name: next.name, zones: next.zones.length, line: line }, 1.6);
    var prog = function (f) { if (M.loadingProgress) M.loadingProgress(f); };
    prog(0.1);
    // build the next level in steps so the loading screen animates
    setTimeout(function () {
      G.switchPlan(next).then(function () { prog(0.7); setTimeout(function () {
        try { R.renderer.compile(R.scene, R.camera); } catch (e) { /* first frame compiles anyway */ }
        prog(1);
        setTimeout(function () {
          if (M.loadingHide) M.loadingHide();
          G.startLevel({ fadeIn: true });
        }, Math.max(0, (AUTOTEST ? 300 : 1700) - (performance.now() - t0)));
      }, 60); });
    }, 120);
  }

  function levelComplete() {
    G.complete = true; G.mode = 'results';
    Inp.enabled = false; Inp.releaseLock(); IB.Plat.stop();
    A.play('hatch');
    bankLevel();
    G.slot.plan = IB.CAMPAIGN[0];
    G.store.save(G.slot);
    setDim(0);
    HUD.show(false); document.getElementById('touch').hidden = true;
    M.results(G.lastResults);
  }

  // ---------------- pickups ----------------
  // ---------------- health director ----------------
  // Watches the player's health and keeps health cans on the map in the current zone: one when healthy, up to four
  // when badly hurt. New cans land on open ground 7-22 m away (never on top of the player), and show on the radar.
  var HEAL = 40;
  function healthWanted(frac) { return frac >= 0.8 ? 1 : frac >= 0.55 ? 2 : frac >= 0.3 ? 3 : 4; }
  function healthDirector(dt) {
    G.hdT = (G.hdT || 0) - dt;
    if (G.hdT > 0 || !G.run.started || G.dead || G.complete) return;
    G.hdT = 2.5;
    var p = G.player, zi = Z.zoneAt(G.level, p.x, p.z);
    if (zi < 0) return;
    var z = G.level.zones[zi], want = healthWanted(p.health / p.maxHp), have = 0;
    G.pickups.forEach(function (pk) { if (pk.on && pk.kind === 'health' && pk.x > z.ox && pk.x < z.ox + z.w && pk.z > z.oz && pk.z < z.oz + z.h) have++; });
    if (have >= want) return;
    for (var tries = 0; tries < 60; tries++) {
      var x = z.ox + 2 + Math.random() * (z.w - 4), zz = z.oz + 2 + Math.random() * (z.h - 4), d = Math.hypot(x - p.x, zz - p.z);
      if (d < 7 || d > 22 || !Z.isOpen(z, x, zz) || !Z.isOpen(z, x + 0.6, zz) || !Z.isOpen(z, x - 0.6, zz) || !Z.isOpen(z, x, zz + 0.6) || !Z.isOpen(z, x, zz - 0.6)) continue;
      var near = G.pickups.some(function (pk) { return pk.on && Math.hypot(pk.x - x, pk.z - zz) < 4; });
      if (near) continue;
      if (G.spawnPickup('health', x, zz)) { FX.puff(x, 0.4, zz, 4, PAL.green, 0.15, 0.45, 1.5); return; }
    }
  }
  G.healthWanted = healthWanted;

  function initPickups() {
    G.pickups = [];
    var geo = { ammo: IB.Assets.get('PICKUP_Ammo'), health: IB.Assets.get('PICKUP_Health') };
    for (var i = 0; i < 28; i++) {
      var kind = i < 10 ? 'ammo' : 'health';
      var m = new THREE.Mesh(geo[kind], IB.Assets.mat.weapons); m.visible = false; R.scene.add(m);
      G.pickups.push({ kind: kind, mesh: m, on: false, x: 0, z: 0 });
    }
  }
  G.spawnPickup = function (kind, x, z) {
    for (var i = 0; i < G.pickups.length; i++) {
      var pk = G.pickups[i]; if (pk.on || pk.kind !== kind) continue;
      pk.on = true; pk.x = x; pk.z = z; pk.mesh.position.set(x, 0, z); pk.mesh.visible = true; return pk;
    }
    return null;
  };
  function updatePickups(dt, t) {
    var p = G.player;
    G.pickups.forEach(function (pk, i) {
      if (!pk.on) return;
      pk.mesh.rotation.y = t * 1.5 + i;
      pk.mesh.position.y = 0.05 + Math.sin(t * 3 + i) * 0.04;
      FX.blob(pk.x, 0, pk.z, 0.35);
      if (Math.hypot(p.x - pk.x, p.z - pk.z) < 0.9 && p.y < 1) {
        if (pk.kind === 'health') { if (p.health >= p.maxHp) return; p.health = Math.min(p.maxHp, p.health + HEAL); HUD.toast('+' + HEAL + ' health', 1.2); }
        else { W.addAmmo(G.ws, 0.5); HUD.toast('Ammo', 1.0); }
        pk.on = false; pk.mesh.visible = false; A.play('pickup');
      }
    });
  }

  // ---------------- combat glue ----------------
  var _org = new THREE.Vector3(), _end = new THREE.Vector3(), _mz = new THREE.Vector3();
  function shoot(origin, dir, def) {
    var ox = origin.x, oy = origin.y, oz = origin.z, dx = dir.x, dy = dir.y, dz = dir.z;
    G.run.shots++;
    var wh = G.level.world.ray(ox, oy, oz, dx, dy, dz, 200), wt = wh ? wh.t : 200;
    var whit = wh ? { t: wh.t, box: wh.box, nx: wh.nx, ny: wh.ny, nz: wh.nz } : null;
    var rh = AI.raycast(ox, oy, oz, dx, dy, dz, wt);
    var endT = rh ? rh.t : wt;
    _end.set(ox + dx * endT, oy + dy * endT, oz + dz * endT);
    W.muzzleWorld(R.camera, _mz);
    if (def.fire !== 'auto' || G.run.shots % 2 === 0) FX.tracer(_mz.x, _mz.y, _mz.z, _end.x, _end.y, _end.z);
    AI.hear(G.player.x, G.player.z, 20);
    if (rh) {
      var r = rh.robot, zone = rh.zone;
      var res = IB.Damage.hit({ weapon: def, dist: endT, zone: zone, dmgLevel: up('dmg'), coreLevel: up('core'), critLevel: up('crit'), rng: Math.random, blinded: r.state === 'blinded' });
      G.run.hits++; if (zone === 'core') G.run.coreHits++;
      var killed = AI.damage(r, res.damage, { kx: dx * 4, kz: dz * 4 }, onKill);
      FX.puff(_end.x, _end.y, _end.z, zone === 'core' ? 5 : 3, PAL.ink, 0.12, 0.38, 2.2);
      if (zone === 'core') FX.puff(_end.x, _end.y, _end.z, 2, PAL.amber, 0.08, 0.2, 3);
      if (!killed) { HUD.hit(zone === 'core' ? 'core' : 'hit'); A.play(zone === 'core' ? 'core' : 'hit'); }
    } else if (whit) {
      if (whit.box && whit.box.kind === 'gate') FX.puff(_end.x, _end.y, _end.z, 3, PAL.ink, 0.1, 0.3, 1.5);
      else FX.impact(_end.x, _end.y, _end.z, whit.nx, whit.ny, whit.nz, Math.random() < 1 / 3);
    }
  }
  function up(id) { return (G.slot && G.slot.upgrades && G.slot.upgrades[id]) || 0; }
  function onKill(r) {
    G.run.kills++;
    HUD.hit('kill'); A.play('crunch', { pos: r });
    var def = IB.ENEMIES[r.type];
    var drop = IB.Gems ? IB.Gems.robotDrop(r.type, G.plan.level, up('press')) : { chip: 1, shard: 0, core: 0, total: 1 };
    var k;
    for (k = 0; k < drop.chip; k++) FX.dropGem('chip', r.x, 0.4, r.z, r.zone);
    for (k = 0; k < drop.shard; k++) FX.dropGem('shard', r.x, 0.4, r.z, r.zone);
    for (k = 0; k < drop.core; k++) FX.dropGem('core', r.x, 0.4, r.z, r.zone);
    var w = W.current(G.ws);
    HUD.feed(G.lastKillCls || (w ? w.def.cls : 'pistol'), def ? def.name : r.type, drop.total);
    G.lastKillCls = null;
    if (Math.random() < 0.2) G.spawnPickup('ammo', r.x, r.z);
    else if (G.player.health < G.player.maxHp * 0.4 && Math.random() < 0.25) G.spawnPickup('health', r.x, r.z);
    if (G.fx && G.fx.leech) G.player.health = Math.min(G.player.maxHp, G.player.health + G.fx.leech);
  }
  function collectGem(kind) {
    var v = IB.Gems ? IB.Gems.VALUES[kind] : 1;
    G.run.gems += v; if (G.slot) G.slot.gems = (G.slot.gems || 0) + v;
    HUD.gems(G.slot ? G.slot.gems : G.run.gems, true);
    A.gem(performance.now() / 1000);
  }
  // screen shake as trauma (0..1): shake = trauma^2, decays over ~0.6 s; the Screen shake setting turns it off
  G.addTrauma = function (t) { G.trauma = Math.min(1, (G.trauma || 0) + t); };
  G.hurt = function (robot, dmg) {
    var p = G.player;
    if (!p.alive || p.protect > 0 || G.complete) return;
    p.health -= dmg; p.lastHurt = 0;
    A.play(robot.proj ? (robot.type === 'bomber' ? 'boom' : 'boltHit') : 'bite', { pos: robot }); A.play('hurt', { gain: 0.8 });
    // arc pointing toward the attacker
    var dx = robot.x - p.x, dz = robot.z - p.z;
    var fx = -Math.sin(p.yaw), fz = -Math.cos(p.yaw), rx = Math.cos(p.yaw), rz = -Math.sin(p.yaw);
    HUD.arc(Math.atan2(dx * rx + dz * rz, dx * fx + dz * fz)); // 0 = ahead, + = to the right
    G.shake = Math.max(G.shake, 0.5); G.addTrauma(Math.min(0.5, 0.12 + dmg * 0.012));
    if (HUD.damageFlash) HUD.damageFlash(Math.min(1, dmg / 30));
    if (p.health <= 0) die(robot);
  };
  function die(robot) {
    var p = G.player;
    p.health = 0; p.alive = false; G.dead = true; G.deathT = 0; G.run.deaths++; G.run.retries--;
    G.killer = (IB.ENEMIES[robot.type] || {}).name || 'Robot';
    document.body.classList.add('dead');
    IB.Plat.stop();
    if (G.run.retries < 0) {
      G.mode = 'fail'; Inp.enabled = false; Inp.releaseLock();
      setTimeout(function () { HUD.show(false); document.body.classList.remove('dead'); M.fail(); }, 900);
      return;
    }
    HUD.elim(true, G.killer.toUpperCase(), 3, G.run.retries);
  }
  function respawn() {
    var p = G.player, z = G.level.zones[G.zone];
    document.body.classList.remove('dead');
    HUD.elim(false);
    p.alive = true; p.health = p.maxHp; p.protect = 2; p.x = z.entry.x; p.z = z.entry.z; p.y = 0; p.vx = p.vz = p.vy = 0; p.yaw = 0; p.pitch = 0;
    G.dead = false;
    // zone reset: its robots respawn at full health; collected gems stay
    AI.despawn(G.zone);
    z.state = 'active'; z.wave = -1; z.waveT = 0; z.startT = 0; z.queue = []; z.clearT = -1;
    W.refill(G.ws);
    IB.Plat.start();
  }

  // ---------------- pause / menus ----------------
  G.pause = function () {
    if (G.mode !== 'play' || G.dead) return;
    G.mode = 'paused'; Inp.enabled = false; Inp.reset(); Inp.releaseLock(); IB.Plat.stop();
    HUD.show(false); document.getElementById('touch').hidden = true;
    M.pause({ level: G.plan.level, levelName: G.plan.name, zone: G.zone + 1, zones: G.level.zones.length, gems: G.slot ? G.slot.gems : 0 });
  };
  G.resume = function () {
    M.hide(); G.mode = 'play'; Inp.enabled = true; Inp.reset();
    HUD.show(true); HUD.last = {}; document.getElementById('touch').hidden = !Inp.touch;
    if (!AUTOTEST) Inp.requestLock();
    IB.Plat.start();
  };
  G.toTitle = function () {
    setDim(0);
    G.mode = 'title'; Inp.enabled = false; Inp.releaseLock(); IB.Plat.stop();
    HUD.show(false); document.getElementById('touch').hidden = true; document.body.classList.remove('dead');
    resetLevelStateForTitle();
    var slot = G.store.newest();
    G.slot = slot || null;
    M.title({ slot: slot, levelName: G.plan.name });
  };
  function resetLevelStateForTitle() {
    if (!G.pickups) initPickups();
    resetLevelState();
    var z = G.level.zones[0];
    // five robots in a loose line facing the player, 8 to 14 m away
    for (var i = 0; i < 5; i++) {
      var x = z.entry.x - 5 + i * 2.5 + (i % 2) * 0.4, zz = z.entry.z - 8 - (i % 3) * 2.2 - (i === 2 ? 1 : 0);
      AI.spawn('crawler', x, zz, 0, z.entry.x, z.entry.z + 4, { pose: true });
    }
    W.equip(G.ws, 'pip', true);
    placeTitleCam();
  }
  function placeTitleCam() {
    var z = G.level.zones[0], portrait = window.innerHeight > window.innerWidth;
    // portrait: pull back (inside the lot) and raise a little so all five robots stay in frame
    G.titleCam = { x: z.entry.x + 0.5, y: 1.55 + (portrait ? 0.35 : 0), z: z.entry.z + (portrait ? 1.2 : 0) };
    R.fovMul = portrait ? 1.12 : 1; R.applyFov();
  }

  function wireMenus() {
    M.on('continue', function () {
      var pl = G.slot && IB.LEVEL_PLANS[G.slot.plan];
      M.wipe(function () { if (pl && pl !== G.plan) G.switchPlan(pl).then(function () { G.startLevel(); }); else G.startLevel(); });
    });
    M.on('new', function () {
      var free = G.store.freeSlot();
      if (!free) { var n = G.store.newest(); free = n ? n.id : 1; }
      G.slot = G.store.newSlot(free, (Math.random() * 1e9) | 0);
      G.slot.plan = IB.CAMPAIGN[0]; G.slot.owned = (IB.LEVEL_PLANS[IB.CAMPAIGN[0]].start || ['pip']).slice();
      G.store.save(G.slot);
      M.wipe(function () { if (G.plan.id !== IB.CAMPAIGN[0]) G.switchPlan(IB.LEVEL_PLANS[IB.CAMPAIGN[0]]).then(function () { G.startLevel(); }); else G.startLevel(); });
    });
    M.on('settings', function () { M.settings(G.settings, M.cur); });
    M.on('setting', function (d) {
      G.settings[d.key] = d.value; G.store.saveSettings(G.settings); G.applySettings();
      if (d.key === 'graphics') G.applyGraphics(Inp.touch);
      if (d.key === 'sfx') { firstGesture(); A.setEnabled(d.value); }
    });
    M.on('back', function () { if (M._settingsFrom === 'pause') { G.mode = 'play'; G.pause(); } else G.toTitle(); });
    M.on('reset', function () { M.confirmReset(); });
    M.on('cancelReset', function () { M.settings(G.settings, M._settingsFrom); });
    M.on('doReset', function () { G.store.resetAll(); G.slot = null; G.settings = G.store.loadSettings(); G.applySettings(); G.toTitle(); });
    M.on('resume', function () { G.resume(); });
    M.on('restart', function () { M.wipe(function () { G.startLevel(); }); });
    M.on('quit', function () { M.wipe(function () { G.toTitle(); }); });
    M.on('next', function () { M.wipe(function () { G.toTitle(); }); });
    M.on('replay', function () { M.wipe(function () { G.startLevel(); }); });
    M.on('retry', function () { M.wipe(function () { G.startLevel(); }); });
    M.on('dismissRotate', function () { G.rotateSeen = true; try { localStorage.setItem('inkbolt.rotateSeen', '1'); } catch (e) { /* ignore */ } G.resume(); });
  }

  // ---------------- frame ----------------
  var acc = 0, tAll = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    var dtRaw = Math.min(0.1, (now - G.last) / 1000); G.last = now;
    perfGuard(dtRaw);
    var dt = dtRaw;
    if (G.hitstop > 0) { G.hitstop -= dt; dt = 0; }
    tAll += dtRaw;
    Inp.update();
    R.renderer.info.reset();
    if (G.mode === 'play') playFrame(dt, dtRaw);
    else if (G.mode === 'title') titleFrame(dtRaw);
    else idleFrame(dtRaw);
    Z.updateClouds(G.level, dtRaw);
    R.render(G.mode === 'play' ? !G.dead && !G.ws.hidden : G.mode === 'title');
    Inp.endFrame();
  }

  function titleFrame(dt) {
    var c = G.titleCam, t = tAll;
    var px = (G.mouseX || 0) * 2 * Math.PI / 180, py = (G.mouseY || 0) * 2 * Math.PI / 180;
    R.camera.position.set(c.x, c.y, c.z);
    R.camera.rotation.set(-0.06 - py * 0.5 + Math.sin(t * 0.7) * 0.004, px * -0.5 + Math.sin(t * 0.4) * 0.01, 0);
    AI.update(dt, { player: { x: c.x, y: 0, z: c.z + 30, alive: false }, world: G.level.world, level: G.level, activeZone: -1, hurt: function () { } });
    AI.sync(); AI.updateCorpses(dt);
    var p = G.player; p.vx = p.vz = 0;
    W.update(G.ws, dt, { player: p, cam: R.camera, input: { fire: false, firePressed: false, aim: false }, shoot: function () { } });
    W.pose(G.ws, dt, p, 0, 0, true, t);
    FX.update(dt, R.camera, p, 0, function () { });
  }
  window.addEventListener('mousemove', function (e) { G.mouseX = (e.clientX / window.innerWidth - 0.5) * 2; G.mouseY = (e.clientY / window.innerHeight - 0.5) * 2; });

  function idleFrame(dt) {
    AI.sync(); AI.updateCorpses(dt);
    FX.update(dt, R.camera, G.player, 0, function () { });
  }

  function playFrame(dt, dtRaw) {
    var p = G.player, s = G.settings;
    if (Inp.pausePressed) { G.pause(); return; }
    if (G.fade) {
      G.fade.t += dtRaw;
      var fk = Math.min(1, G.fade.t / G.fade.dur);
      setDim(1 - fk * fk * (3 - 2 * fk));
      if (fk >= 1) G.fade = null;
    }
    updateWeaponStands(tAll);
    if (G.run && p.alive) healthDirector(dtRaw);
    // intro hold
    if (!G.run.started) {
      G.run.introT -= dtRaw;
      if (G.run.introT <= 0) {
        G.run.started = true; IB.Plat.start();
        if (Inp.touch && window.innerHeight > window.innerWidth && !G.rotateSeen && !AUTOTEST) {
          var seen = false; try { seen = localStorage.getItem('inkbolt.rotateSeen') === '1'; } catch (e) { /* ignore */ }
          if (!seen) { G.mode = 'paused'; Inp.enabled = false; M.rotateHint(); return; }
        }
      }
    }
    // look
    var sens = Inp.touch ? s.touchSens : s.mouseSens;
    var zoomScale = R.fovMul;
    var assist = 1;
    if (Inp.touch && p.alive) {
      R.camera.getWorldDirection(_v);
      if (AI.raycast(R.camera.position.x, R.camera.position.y, R.camera.position.z, _v.x, _v.y, _v.z, 40)) assist = 0.6;
    }
    if (p.alive && !G.complete) IB.Player.look(p, Inp.lookDX * assist, Inp.lookDY * (s.invertY ? -1 : 1) * assist, sens * zoomScale);
    // weapon switching / actions
    if (p.alive) {
      if (Inp.slotPressed) W.slot(G.ws, Inp.slotPressed);
      if (Inp.wheel) W.cycle(G.ws, Inp.wheel > 0 ? 1 : -1);
      if (Inp.reloadPressed) W.reload(G.ws);
      if (Inp.meleePressed && W.shove(G.ws)) doShove();
    }
    // fixed-step simulation
    acc += dt; var steps = 0;
    var jump = Inp.jumpPressed, slidePress = Inp.slidePressed;
    while (acc >= STEP && steps < 4) {
      acc -= STEP; steps++;
      if (p.alive) IB.Player.step(p, { mx: G.complete ? 0 : Inp.mx, mz: G.complete ? 0 : Inp.mz, sprint: Inp.sprint, jumpPressed: jump, slidePressed: slidePress, crouch: Inp.crouch }, G.level.world, STEP, footFx);
      jump = false; slidePress = false;
      if (G.run.started) {
        var actx = { player: p, world: G.level.world, level: G.level, activeZone: G.level.zones[G.zone].state === 'active' ? G.zone : -1, hurt: G.hurt, shake: G.addTrauma, onKill: onKill };
        AI.update(STEP, actx);
        IB.Projectiles.update(STEP, actx);
      }
      if (G.run.started && !G.dead) updateZones(STEP);
    }
    if (acc > STEP * 4) acc = 0;
    if (G.run.started && !G.complete && !G.dead) G.run.time += dt;
    // regen (Nanite Welders)
    if (G.fx && G.fx.regen && p.alive && p.lastHurt > 3) p.health = Math.min(p.maxHp, p.health + G.fx.regen * dt);
    // weapons
    W.update(G.ws, dt, { player: p, cam: R.camera, input: { fire: Inp.fire && p.alive && G.run.started, firePressed: Inp.firePressed && p.alive && G.run.started, aim: Inp.aim && p.alive }, shoot: shoot,
      onFire: function (d) { if (s.shake && (d.cls === 'smg' || d.cls === 'rifle')) G.shake = Math.max(G.shake, 0.15); } });
    // FOV: aim zoom, plus a small widen at sprint and a kick while sliding
    var cw = W.current(G.ws), aimZoom = cw ? (cw.def.scopeZoom ? 1 / cw.def.scopeZoom : (cw.def.aimZoom || 0.85)) : 0.85;
    G.fovKick = (G.fovKick || 0) + (((p.sliding ? 0.1 : p.sprinting ? 0.05 : 0)) - (G.fovKick || 0)) * Math.min(1, dtRaw * 8);
    var targetMul = (1 + (aimZoom - 1) * G.ws.aim) * (1 + G.fovKick);
    if (Math.abs(targetMul - R.fovMul) > 0.002) { R.fovMul = targetMul; R.applyFov(); }
    // death sequence
    if (G.dead) {
      G.deathT += dtRaw;
      var left = Math.max(0, 3 - G.deathT);
      HUD.elim(true, G.killer.toUpperCase(), Math.ceil(left), G.run.retries);
      if (G.deathT >= 3) respawn();
    }
    // camera
    var eye = IB.Player.eyeY(p, s.headBob);
    var tip = G.dead ? Math.min(1, G.deathT / 0.5) : 0;
    G.shake = Math.max(0, G.shake - dtRaw / 0.25 * Math.max(G.shake, 0.3));
    G.trauma = Math.max(0, (G.trauma || 0) - dtRaw * 1.6);
    var tr = s.shake ? G.trauma * G.trauma : 0, sh = s.shake ? G.shake * Math.PI / 180 : 0, tt = tAll * 31;
    var nx = Math.sin(tt * 1.3) * Math.cos(tt * 0.7), ny = Math.sin(tt * 1.1 + 2) * Math.cos(tt * 0.9), nr = Math.sin(tt * 0.8 + 4);
    // camera roll leans into slides and slightly into strafes
    var rightV = p.vx * Math.cos(p.yaw) - p.vz * Math.sin(p.yaw);
    G.roll = (G.roll || 0) + (((p.sliding ? -0.07 : 0) - rightV * 0.0035) - (G.roll || 0)) * Math.min(1, dtRaw * 8);
    R.camera.position.set(p.x, eye - tip * 1.1, p.z);
    R.camera.rotation.set(p.pitch + G.ws.recoilP + (Math.random() - 0.5) * sh * 2 + ny * tr * 0.05 - tip * 0.2 - (p.landKick || 0) * 0.025,
      p.yaw + G.ws.recoilY + (Math.random() - 0.5) * sh * 2 + nx * tr * 0.05, tip * 0.5 + G.roll + nr * tr * 0.06);
    R.camera.updateMatrixWorld();
    A.listener = { x: p.x, z: p.z, yaw: p.yaw };
    // render-side updates
    AI.sync(); AI.updateCorpses(dtRaw);
    updatePickups(dtRaw, tAll);
    var magnet = 2.5 * (1 + 0.5 * up('magnet'));
    FX.update(dtRaw, R.camera, p, magnet, collectGem);
    W.pose(G.ws, dtRaw, p, Inp.lookDX, Inp.lookDY, s.headBob, tAll);
    // HUD
    var zn = G.level.zones[G.zone];
    var w = W.current(G.ws);
    HUD.health(p.health, p.maxHp);
    if (w) {
      HUD.ammo(w.mag, w.reserve);
      if (HUD.weapon) HUD.weapon({ id: w.id, name: w.def.name, cls: w.def.cls, mag: w.mag, magSize: W.magSize(G.ws, w.def), reserve: w.reserve,
        reloading: G.ws.state === 'reload', reloadFrac: G.ws.state === 'reload' ? Math.min(1, G.ws.t / G.ws.reloadT) : 0 });
    }
    if (HUD.stamina) HUD.stamina(p.stamina / (p.staminaMax || 4), p.sliding);
    G.radarT = (G.radarT || 0) - dtRaw;
    if (HUD.radar && G.radarT <= 0) {
      G.radarT = 0.1;
      var rob = [];
      AI.robots.forEach(function (r) { if (r.on && r.state !== 'pose') rob.push({ x: r.x, z: r.z, alert: r.state !== 'idle' && r.state !== 'spawn' }); });
      var gates = []; G.level.zones.forEach(function (zz) { gates.push({ x: zz.exitGate.x, z: zz.exitGate.z, open: zz.exitGate.open > 0.5 }); });
      var last = G.level.zones[G.level.zones.length - 1];
      HUD.radar({ px: p.x, pz: p.z, yaw: p.yaw, range: 30, robots: rob, gates: gates,
        pickups: (G.weaponStands || []).filter(function (w2) { return !w2.taken; }).map(function (w2) { return { x: w2.x, z: w2.z, kind: 'weapon' }; })
          .concat(G.pickups.filter(function (pk) { return pk.on; }).map(function (pk) { return { x: pk.x, z: pk.z, kind: pk.kind }; })),
        exit: last.state === 'cleared' ? { x: G.level.hatch.x, z: G.level.hatch.z } : null });
    }
    if (HUD.objective) {
      var obj = zn.state === 'active' ? 'Clear the block · ' + (AI.alive(G.zone) + zn.queue.length + remainingInWaves(zn)) + ' robots' :
        (G.level.zones[G.level.zones.length - 1].state === 'cleared' ? 'Walk the exit path' : 'Follow the arrows to the next gate');
      HUD.objective(obj);
    }
    HUD.slots(W.ownedSlots(G.ws).map(function (sl) { var id = G.ws.slots[sl]; return { slot: sl, cls: IB.WEAPONS[id].cls, name: IB.WEAPONS[id].name, on: id === G.ws.cur }; }));
    HUD.score(G.zone + 1, G.level.zones.length, G.run.time, zn.state === 'active' ? AI.alive(G.zone) + zn.queue.length + remainingInWaves(zn) : 0);
    HUD.gems(G.slot ? G.slot.gems : G.run.gems, false);
    HUD.crosshair(W.spread(G.ws, p), R.camera.fov, p.sprinting);
    HUD.tick(dtRaw);
  }
  function remainingInWaves(z) {
    var n = 0;
    for (var w = Math.max(0, z.wave + 1); w < z.plan.waves.length; w++) z.plan.waves[w].forEach(function (e) { n += e[1]; });
    return n;
  }
  var footFx = {
    slide: function (on) { if (on) { A.play('shove', { pitch: 0.65, gain: 1.2 }); G.addTrauma(0.12); } },
    jump: function () { A.play('step', { gain: 1.4 }); },
    land: function (fell) { A.play('land', { gain: Math.min(1, 0.4 + fell * 0.3) }); },
    step: function (spr) { A.play('step', { gain: spr ? 1.2 : 0.9, pitch: 0.9 + Math.random() * 0.2 }); }
  };
  function doShove() {
    var p = G.player, fx = -Math.sin(p.yaw), fz = -Math.cos(p.yaw), hitAny = false;
    A.play('shove');
    AI.robots.forEach(function (r) {
      if (!r.on || r.state === 'pose' || r.state === 'spawn') return;
      var dx = r.x - p.x, dz = r.z - p.z, d = Math.hypot(dx, dz);
      if (d > 2.2 || (dx * fx + dz * fz) / (d || 1) < 0.5) return;
      hitAny = true; G.lastKillCls = 'shove';
      AI.damage(r, 20 * (G.fx && G.fx.meleeMul || 1), { stagger: true, kx: dx / d * 6, kz: dz / d * 6 }, onKill);
      FX.puff(r.x, 0.6, r.z, 4, PAL.ink, 0.15, 0.4, 2);
    });
    if (hitAny) { G.hitstop = 0.035; HUD.hit('hit'); A.play('hit'); }
  }

  // ---------------- performance guard ----------------
  function perfGuard(dt) {
    var g = G.guard; if (!g || G.mode !== 'play') return;
    g.samples.push(dt * 1000); var sum = 0;
    while (g.samples.length > 120) g.samples.shift();
    for (var i = 0; i < g.samples.length; i++) sum += g.samples[i];
    g.avg = sum / g.samples.length;
    if (!g.on || g.samples.length < 60) return;
    var idx = TIER_ORDER.indexOf(R.tier);
    if (g.avg > 18.5) { g.slowT += dt; g.fastT = 0; if (g.slowT > 3 && idx > 0) { g.failed[R.tier] = true; G.setTier(TIER_ORDER[idx - 1]); g.slowT = 0; g.samples.length = 0; } }
    else if (g.avg < 12) { g.fastT += dt; g.slowT = 0; if (g.fastT > 10 && !g.steppedUp && idx < 3 && !g.failed[TIER_ORDER[idx + 1]]) { g.steppedUp = true; G.setTier(TIER_ORDER[idx + 1]); g.fastT = 0; g.samples.length = 0; } }
    else { g.slowT = 0; g.fastT = 0; }
  }

  // ---------------- test hooks ----------------
  window.__TEST__ = {
    state: function () {
      if (!G.level || !G.run && G.mode === 'boot') return { mode: G.mode || 'boot', zones: [], errors: G.errors.slice() };
      var L = G.level, info = R.renderer.info;
      return {
        mode: G.mode, zone: G.zone, zones: L.zones.map(function (z) { return z.state; }),
        alive: AI.alive(), aliveInZone: AI.alive(G.zone), queue: L.zones[G.zone].queue ? L.zones[G.zone].queue.length : 0,
        exitGates: L.zones.map(function (z) { return +z.exitGate.open.toFixed(2); }),
        entryGates: L.zones.map(function (z) { return z.entryGate ? +z.entryGate.open.toFixed(2) : null; }),
        trailLit: L.trails.map(function (t) { return t.lit + '/' + t.count; }),
        health: G.player.health, alivePlayer: G.player.alive, pos: [G.player.x, G.player.y, G.player.z],
        gems: G.slot ? G.slot.gems : 0, runGems: G.run ? G.run.gems : 0, kills: G.run ? G.run.kills : 0, deaths: G.run ? G.run.deaths : 0,
        complete: !!G.complete, results: G.lastResults || null, saved: G.store.listSlots().filter(Boolean).length,
        calls: info.render.calls, triangles: info.render.triangles, frameMs: G.guard ? G.guard.avg : 0, tier: R.tier,
        weapon: G.ws.cur, ammo: W.current(G.ws) ? W.current(G.ws).mag : 0, errors: G.errors.slice(), plat: IB.Plat.log.slice(), decals: FX.decalCount
      };
    },
    killZone: function () { AI.killAll(G.zone, onKill); var z = G.level.zones[G.zone]; z.queue.length = 0; if (z.wave < z.plan.waves.length - 1) { z.wave = z.plan.waves.length - 1; } },
    forceWaves: function () { var z = G.level.zones[G.zone]; if (z.wave < 0) queueWave(z, 0); },
    teleport: function (i) {
      var p = G.player, L = G.level;
      if (i === 'hatch') { p.x = L.hatch.x; p.z = L.hatch.z; p.y = 0; return; }
      var z = L.zones[i]; p.x = z.entry.x; p.z = z.entry.z; p.y = 0; p.vx = p.vz = 0;
    },
    teleportTo: function (x, z) { G.player.x = x; G.player.z = z; },
    damagePlayer: function (n) { G.player.protect = 0; G.hurt({ x: G.player.x, z: G.player.z - 1, type: 'crawler' }, n); },
    look: function (yaw, pitch) { G.player.yaw = yaw; G.player.pitch = pitch || 0; },
    pause: function () { G.pause(); }, resume: function () { G.resume(); }, title: function () { G.toTitle(); }, start: function () { G.startLevel(); },
    menu: function (act) { M.act(act); },
    setTier: function (t) { G.setTier(t); }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', G.boot); else G.boot();
})(window.IB = window.IB || {});
