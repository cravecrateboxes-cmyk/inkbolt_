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
    IB.Assets.load(['common', 'weapons', 'bots', 'gear', 'troopers', Z.themeOf(G.plan).family], function (f) { bootProgress(0.2 + f * 0.7); })
      .then(bootAfterAssets)
      .catch(function (e) {
        G.errors.push(String(e && e.message || e));
        document.getElementById('boot').innerHTML = '<div class="plate ink panel"><h2>Could not load</h2><p>' + String(e && e.message || e) + '</p></div>';
      });
  };
  function bootAfterAssets() {
    FX.init(R.scene); AI.init(R.scene); W.init(R.vmScene); IB.Projectiles.init(R.scene);
    if (IB.Throwables) IB.Throwables.init(R.scene);   // frag cans (G)
    if (IB.WeaponDrops) IB.WeaponDrops.init(R.scene);   // tiered gun / melee drops (soldiers, blade bots)
    if (IB.Launchers) IB.Launchers.init(R.scene);       // launcher rockets, lock markers, rocket crates
    if (IB.Gear) { IB.Gear.init(); IB.Drops.init(R.scene); }   // loot: fps-gear models, world drops
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
    R.applyFogFar();
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
    var shared = new Set(Object.keys(IB.Assets.geo).map(function (k) { return IB.Assets.geo[k]; }).concat(Object.values(G._gunGeo || {})));
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
    if (AI.setupCans) AI.setupCans(G.level);   // hinged spawn-can lids (ai.js)
    R.applyEnv(G.level.theme.env || {});
    AI.setLevel(G.plan.level);
  };
  // a level's theme kit is loaded on demand (embedded in the single-file build, assets/*.glb otherwise)
  G.ensureTheme = function (plan) { return IB.Assets.load([Z.themeOf(plan).family]); };
  G.switchPlan = function (plan) {
    return G.ensureTheme(plan).then(function () { G.plan = plan; G.buildLevel(); });
  };

  // ---------------- armory mounts (Strike Team HQ): real guns on wall racks, gear on benches and shelves ----------------
  /* zone.mounts come from theme pieces ({x, y, z, yaw, kind: 'gun' | 'mod' | 'item', fill}). Each level start rolls what
     hangs there: a rack gun is one of the guns unlocked so far at a weapon tier from ARMORY_TIERS (gray / green / blue
     common, purple very rare, orange never); a bench holds a gun attachment and a shelf a shield cell or vest, made by
     IB.Loot.makeItem at ARMORY_GEAR odds (no Legendary). Look at one and press E (touch: USE) to take it: guns join the
     arsenal like a weapon drop (or upgrade your tier, or break down for gems), gear goes in the bag like a loot drop.
     Drawn as one instanced mesh per model per zone, so a wall of guns costs a few draw calls. */
  var ARMORY_TIERS = { gray: 46, green: 34, blue: 19.25, purple: 0.75, orange: 0 };
  var ARMORY_GEAR = { common: 62, rare: 33, epic: 5, legendary: 0 };
  G.ARMORY_TIERS = ARMORY_TIERS; G.ARMORY_GEAR = ARMORY_GEAR;
  function rollW(w) { var k = Object.keys(w), tot = 0, i; for (i = 0; i < k.length; i++) tot += w[k[i]]; var x = Math.random() * tot; for (i = 0; i < k.length; i++) { if (w[k[i]] <= 0) continue; x -= w[k[i]]; if (x < 0) return k[i]; } return k[0]; }
  var _lm = new THREE.Matrix4(), _lq = new THREE.Quaternion(), _lp = new THREE.Vector3(), _ls = new THREE.Vector3(), _lZ = new THREE.Matrix4().makeScale(0, 0, 0), _lc = new THREE.Color(), _ly = new THREE.Vector3(0, 1, 0);
  function clearLoot() {
    (G.lootMeshes || []).forEach(function (m) { if (m.parent) m.parent.remove(m); if (m.userData.ownGeo) m.geometry.dispose(); });
    G.lootMeshes = []; G.loot = [];
  }
  // world display copy of a gun: the gun mesh plus its detachable mag (revolver: cylinder) at the MAG socket
  G.gunGeo = function (id) {
    G._gunGeo = G._gunGeo || {};
    if (G._gunGeo[id]) return G._gunGeo[id];
    var A = IB.Assets, K = 'WPN_' + id.toUpperCase(), geo = A.get(K), sock = A.node[K + '_MAG'];
    if (A.geo[K + '_Mag'] && sock) {
      try { geo = THREE.BufferGeometryUtils.mergeBufferGeometries([geo.clone(), A.placed(K + '_Mag', new THREE.Matrix4().makeTranslation(sock.position.x, sock.position.y, sock.position.z))], false) || geo; } catch (e) { geo = A.get(K); }
    }
    G._gunGeo[id] = geo;
    return geo;
  };
  /* a gun's transform on its mount: barrel along the rack, right side toward the room, centred along the rack and in
     height, scaled to at most 1.2 and to fit the slot (mount option len x h, default 0.86 m long). With option `back`
     the gun's bounding box rests its back on the mount plane (the theme puts that plane in front of the rack board and
     its pegs), otherwise the box is centred on the mount. Every gun model has its own size and origin. */
  function gunLocal(id, out, fit) {
    var geo = G.gunGeo(id); if (!geo.boundingBox) geo.computeBoundingBox();
    fit = fit || {};
    var bb = geo.boundingBox, len = Math.max(0.2, bb.max.z - bb.min.z), ht = Math.max(0.05, bb.max.y - bb.min.y);
    var sc = Math.min(1.2, (fit.len || 0.86) / len, fit.h ? fit.h / ht : 1.2);
    _lq.setFromAxisAngle(_ly, -Math.PI / 2);
    _lp.set(((bb.max.z + bb.min.z) / 2) * sc, -((bb.max.y + bb.min.y) / 2) * sc, (fit.back ? -bb.min.x : -(bb.max.x + bb.min.x) / 2) * sc);
    return out.compose(_lp, _lq, _ls.set(sc, sc, sc));
  }
  var _lt = new THREE.Matrix4();
  // gear on a bench / shelf (GEAR_* models have their origin where they mount on a gun): 0.8 scale, the visible
  // surface's bounding box (outline shell left out) standing on the mount point, centred on it
  function itemLocal(geo, out) {
    var b = geo.userData.restBox;
    if (!b) {
      var p = geo.attributes.position, hl = geo.attributes.aHull, v = new THREE.Vector3();
      b = geo.userData.restBox = new THREE.Box3();
      for (var i = 0; i < p.count; i++) {
        if (hl && (hl.getX(i) || hl.getY(i) || hl.getZ(i))) continue;
        b.expandByPoint(v.fromBufferAttribute(p, i));
      }
    }
    return out.makeScale(0.8, 0.8, 0.8).setPosition(-(b.min.x + b.max.x) / 2 * 0.8, -b.min.y * 0.8, -(b.min.z + b.max.z) / 2 * 0.8);
  }
  function rackGuns() {
    var out = (IB.ownedWeapons ? IB.ownedWeapons(G.plan.level) : []).filter(function (id) { var d = IB.WEAPONS[id]; return d && d.cls !== 'melee' && IB.Assets.geo['WPN_' + id.toUpperCase()]; });
    return out.length ? out : (IB.MODELLED_WEAPONS || []).filter(function (id) { return IB.Assets.geo['WPN_' + id.toUpperCase()]; });
  }
  function placeLoot() {
    clearLoot();
    if (G.mode === 'title' || !IB.Loot || !IB.WeaponDrops) return;
    var A = IB.Assets, guns = rackGuns(), WD = IB.WeaponDrops, LT = IB.LOOT, AR = G.level.theme.armory || {}, TIERS = AR.tiers || ARMORY_TIERS, GEAR = AR.gear || ARMORY_GEAR;
    var attach = Object.keys(LT.types).filter(function (k) { return LT.slots.indexOf(LT.types[k].slot) >= 0; });
    var worn = Object.keys(LT.types).filter(function (k) { return LT.worn.indexOf(LT.types[k].slot) >= 0; });
    if (!G.worldWpnMat) G.worldWpnMat = R.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0 });
    G.level.zones.forEach(function (z, zi) {
      var groups = {}, tags = [];
      (z.mounts || []).forEach(function (m) {
        if (m.fill < 1 && Math.random() > m.fill) return;   // an empty peg
        var L = { x: m.x, y: m.y, z: m.z, yaw: m.yaw, zone: zi, kind: m.kind, opt: m.opt || null, taken: false }, key;
        if (m.kind === 'gun') {
          L.id = guns[(Math.random() * guns.length) | 0]; L.tier = rollW(TIERS); L.level = G.plan.level;
          if (IB.Launchers) IB.Launchers.rackPick(L);   // levels 14+: now and then a launcher on the rack
          var T = WD.tier(L.tier), def = IB.WEAPONS[L.id], nm = IB.GunLevel ? IB.GunLevel.displayName(def, L.roll) : def.name;
          L.label = 'Take ' + nm; L.sub = T.name + ' · Lv ' + L.level + ' · x' + (T.dmg * (IB.GunLevel ? IB.GunLevel.mul(L.level) : 1)).toFixed(2) + ' damage'; L.color = T.color;
          key = 'WPN:' + L.id; tags.push(L);
        } else {
          var types = m.kind === 'mod' ? attach : worn;
          if (!types.length) return;
          L.item = IB.Loot.makeItem(types[(Math.random() * types.length) | 0], rollW(GEAR), G.plan.level, Math.random);
          key = IB.Loot.modelOf(L.item);
          if (!A.geo[key]) return;
          var RR = LT.rarityById[L.item.rarity];
          L.label = 'Take ' + L.item.name; L.sub = RR.name + ' · ' + IB.Loot.summary(L.item); L.color = RR.color; tags.push(L);
        }
        (groups[key] || (groups[key] = [])).push(L);
        G.loot.push(L);
      });
      Object.keys(groups).forEach(function (key) {
        var list = groups[key], isGun = key.indexOf('WPN:') === 0;
        var geo = isGun ? G.gunGeo(list[0].id) : A.get(key), mat = isGun ? G.worldWpnMat : A.material(key);
        var im = new THREE.InstancedMesh(geo, mat, list.length);
        im.frustumCulled = false;
        var local = isGun ? null : itemLocal(geo, new THREE.Matrix4());
        list.forEach(function (L, i) {
          if (isGun) local = gunLocal(L.id, _lt, L.opt);   // per mount: slots may differ in size
          _lq.setFromAxisAngle(_ly, L.yaw);
          _lm.compose(_lp.set(L.x, L.y, L.z), _lq, _ls.set(1, 1, 1)).multiply(local);
          im.setMatrixAt(i, _lm); L.im = im; L.idx = i;
        });
        z.group.add(im); G.lootMeshes.push(im);
      });
      if (tags.length) {   // a small plate in the rarity / tier colour under each item
        var tg = new THREE.InstancedMesh(new THREE.BoxGeometry(0.34, 0.05, 0.02), new THREE.MeshBasicMaterial({ color: 0xffffff }), tags.length);
        tg.frustumCulled = false; tg.userData.ownGeo = true;
        tags.forEach(function (L, i) {
          _lq.setFromAxisAngle(_ly, L.yaw);
          var t = L.opt && L.opt.tag, cy = Math.cos(L.yaw), sy = Math.sin(L.yaw);   // mount option tag: [dx, dy, dz] mount-local
          if (t) _lp.set(L.x + t[0] * cy + t[2] * sy, L.y + t[1], L.z - t[0] * sy + t[2] * cy);
          else _lp.set(L.x, L.y - (L.kind === 'gun' ? 0.2 : -0.01), L.z);
          _lm.compose(_lp, _lq, _ls.set(1, 1, 1));
          tg.setMatrixAt(i, _lm); tg.setColorAt(i, _lc.set(L.color)); L.tag = tg; L.tagIdx = i;
        });
        z.group.add(tg); G.lootMeshes.push(tg);
      }
    });
  }
  // the armory item the player is looking at, within reach (1.9 m from the eyes, inside a 30 degree cone)
  function nearestLoot() {
    var p = G.player, best = null, bs = 0.52, eye = p.y + 1.5, cp = Math.cos(p.pitch);
    var fx = -Math.sin(p.yaw) * cp, fy = Math.sin(p.pitch), fz = -Math.cos(p.yaw) * cp;
    (G.loot || []).forEach(function (L) {
      if (L.taken || L.zone !== G.zone && L.zone !== G.zone + 1) return;
      var dx = L.x - p.x, dy = L.y + 0.05 - eye, dz = L.z - p.z, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (d > 1.9) return;
      var ang = Math.acos(Math.max(-1, Math.min(1, (dx * fx + dy * fy + dz * fz) / (d || 1))));
      if (ang < bs) { bs = ang; best = L; }
    });
    return best;
  }
  // a rack gun joins the arsenal like a weapon drop (IB.WeaponDrops.acquire): new gun at its tier and level, a better
  // one replaces yours, else gems
  function takeRackGun(id, tier, level, roll) {
    var s = G.slot, line = IB.WeaponDrops.acquire(id, tier, level || G.plan.level, roll);
    HUD.toast(line, 2.4);
    if (HUD.gems) HUD.gems(s.gems || 0, true);
    A.play('pickup');
    if (G.store) G.store.save(s);
    return true;
  }
  function takeLoot(L) {
    var ok;
    if (L.kind === 'gun') ok = takeRackGun(L.id, L.tier, L.level, L.roll);
    else ok = IB.Drops && IB.Drops.collect ? IB.Drops.collect({ it: L.item, x: L.x, z: L.z, on: true, fullT: 0, grp: { visible: true } }, G) : false;
    if (!ok) return false;
    L.taken = true; L.im.setMatrixAt(L.idx, _lZ); L.im.instanceMatrix.needsUpdate = true;
    if (L.tag) { L.tag.setMatrixAt(L.tagIdx, _lZ); L.tag.instanceMatrix.needsUpdate = true; }
    return true;
  }
  function updateLoot() {
    if (!G.loot || !G.loot.length) { if (HUD.use) HUD.use(null); return; }
    var L = G.dead || G.complete || !G.player.alive ? null : nearestLoot();
    if (HUD.use) HUD.use(L ? { key: 'E', text: L.label, sub: L.sub, color: L.color } : null);
    if (L && Inp.usePressed) takeLoot(L);
  }
  G.nearestLoot = nearestLoot; G.takeLoot = takeLoot;

  function resetLevelState() {
    var L = G.level;
    AI.clear(); FX.clear(); IB.Projectiles.clear(); if (IB.SkillFX) IB.SkillFX.clear();
    if (IB.Throwables) IB.Throwables.clear();
    if (IB.WeaponDrops) IB.WeaponDrops.clear();
    if (IB.Launchers) IB.Launchers.clear();
    if (IB.Drops) IB.Drops.clear();
    if (IB.Status) IB.Status.clear();
    L.zones.forEach(function (z, i) {
      z.state = 'idle'; z.wave = -1; z.waveT = 0; z.queue = []; z.clearT = -1; z.spawnedTotal = 0;
      if (z.entryGate) Z.setGate(z.entryGate, i > 0, true);
      Z.setGate(z.exitGate, false, true);
    });
    L.trails.forEach(function (t) { Z.lightTrail(t, 0); t.litT = -1; });
    G.zone = 0; Z.setVisible(L, 0);
    G.pickups.forEach(function (p) { p.mesh.visible = false; p.on = false; });
    L.zones.forEach(function (z) { z.pickups.forEach(function (pk) { G.spawnPickup(pk.kind, pk.x, pk.z, pk.y); }); });
    placeWeaponStands(G.plan.weapons || []);
    placeLoot();
    if (IB.Boom) IB.Boom.levelStart(L, G.plan.level);   // VFX intensity for this level, explosive canisters in later zones
  }

  // ---------------- new weapons waiting at the start of a level ----------------
  // stand mesh per kind: a gun leans on its stock; a melee weapon stands on its pommel; frag cans sit in a little pyramid
  function standItem(id) {
    var A = IB.Assets, def = IB.WEAPONS[id];
    if (def.cls === 'grenade') {
      var g = new THREE.Group(), geo = A.get('HELD_Frag');
      [[-0.17, 0, 0], [0.17, 0, 0], [0, 0.2, 0]].forEach(function (o) { var m = new THREE.Mesh(geo, G.worldWpnMat); m.scale.setScalar(2.2); m.position.set(o[0], o[1] + 0.1, 0); g.add(m); });
      g.position.set(0, 1.02, 0.1);
      return g;
    }
    var gun = new THREE.Mesh(A.get('WPN_' + id.toUpperCase()), G.worldWpnMat);
    if (def.cls === 'melee') {
      gun.scale.setScalar(1.6);
      gun.rotation.set(-0.42, 0.5, 0);                               // standing on its pommel, leaning back on the crate
      gun.position.set(0, 0.5 + (def.id === 'katana' ? 0.36 : def.id === 'eaxe' ? 0.5 : def.id === 'nunchucks' ? 0.35 : 0.18), 0.82);
      return gun;
    }
    gun.scale.setScalar(1.35);
    return gun;
  }
  function placeWeaponStands(ids) {
    (G.weaponStands || []).forEach(function (w) { R.scene.remove(w.group); });
    G.weaponStands = [];
    if (G.mode === 'title') return;
    var z0 = G.level.zones[0], theme = G.level.theme, A = IB.Assets, standName = IB.themePiece(theme, theme.stand || 'Crate');
    if (!G.worldWpnMat) G.worldWpnMat = R.toonMaterial({ map: A.palette.weapons, baked: A.BAKED.weapons });
    ensureSlot();
    ids = ids.filter(function (id) {
      var def = IB.WEAPONS[id]; if (!def) return false;
      if (def.cls === 'grenade') return !!A.geo.HELD_Frag && !G.slot.frag;
      if (def.cls === 'melee') return !!A.node['WPN_' + id.toUpperCase()] && (G.slot.melee || []).indexOf(id) < 0;
      return !!A.node['WPN_' + id.toUpperCase()];
    });
    var n = ids.length, gap = n > 3 ? 1.5 : 1.6;
    ids.forEach(function (id, i) {
      // one row of crates across the start area, centred on the entry (wider rows step back a little at the ends)
      var side = (i - (n - 1) / 2) * 2 * gap;
      var x = z0.entry.x + side, zc = z0.entry.z - 3.8 - (n > 3 && (i === 0 || i === n - 1) ? 0.6 : 0);
      var grp = new THREE.Group(); grp.position.set(x, 0, zc);
      if (A.geo[standName]) grp.add(new THREE.Mesh(A.get(standName), A.mat[A.family[standName]]));
      var item = standItem(id), def = IB.WEAPONS[id];
      if (def.cls !== 'melee' && def.cls !== 'grenade') {
        item.rotation.set(70 * Math.PI / 180, 0.35 * (side > 0 ? -1 : 1), 0);   // standing on its stock, leaning back on the crate
        item.position.set(0, 0.32, 0.72);
      }
      grp.add(item);
      var ring = new THREE.Mesh(new THREE.RingGeometry(0.55, 0.72, 28), new THREE.MeshBasicMaterial({ color: def.cls === 'melee' ? PAL.amber : def.cls === 'grenade' ? PAL.red : PAL.teal, transparent: true, opacity: 0.85 }));
      ring.rotation.x = -Math.PI / 2; ring.position.set(0, 0.02, 0.85); grp.add(ring);
      R.scene.add(grp);
      G.level.world.add(x - 0.5, 0, zc - 0.5, x + 0.5, 1, zc + 0.5, 'cover', 0);
      G.weaponStands.push({ id: id, group: grp, gun: item, ring: ring, x: x, z: zc + 0.85, taken: false });
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
    ensureSlot();
    if (def.cls === 'melee' || def.cls === 'grenade') {
      if (def.cls === 'melee') { grantMelee(w.id); G.slot.meleeSel = w.id; }
      else { G.slot.frag = true; G.grenades = def.carry; }
      w.taken = true; w.group.remove(w.gun); w.ring.visible = false;
      G.store.save(G.slot);
      if (HUD.pickup) HUD.pickup(def.name, def.cls, def.cls === 'melee' ? 'V' : 'G'); else HUD.toast('New: ' + def.name, 2.2);
      A.play('pickup');
      return;
    }
    // the gun joins the arsenal; it is carried at once (taking the place of the gun in hand when the loadout is full)
    if ((G.slot.arsenal || []).indexOf(w.id) < 0) (G.slot.gunLevel = G.slot.gunLevel || {})[w.id] = G.plan.level;   // a stand gun: this level's
    var r = IB.Loadout.pickup(G.slot.loadout || [], G.slot.arsenal || [], IB.Skills.loadoutMax(G.slot.highest), w.id, ws.cur);
    G.slot.arsenal = r.arsenal; G.slot.owned = r.arsenal.slice(); G.slot.loadout = r.loadout;
    if (G.bank) delete G.bank[w.id];   // a fresh gun off the stand comes fully loaded
    W.setLoadout(ws, r.loadout, G.bank);
    W.equip(ws, w.id);
    if (IB.Gear) IB.Gear.refresh(G);   // the replaced gun's attachments go back to the bag
    w.taken = true; w.group.remove(w.gun); w.ring.visible = false;
    G.store.save(G.slot);
    if (HUD.pickup) HUD.pickup(def.name, def.cls, r.slot + 1); else HUD.toast('New weapon: ' + def.name, 2.2);
    A.play('pickup'); A.play('draw');
  }

  // ---------------- progression: arsenal, loadout, skills, player level ----------------
  // arsenal / loadout come from the save (an empty arsenal gets the plan's start guns), trimmed to the 2/3-gun limit
  function syncArmory() {
    ensureSlot();
    var s = G.slot, start = (G.plan.start || ['pip']);
    var ars = IB.Loadout.fixArsenal(s.arsenal && s.arsenal.length ? s.arsenal : (s.owned && s.owned.length ? s.owned : start), W.playable);
    if (!ars.length) ars = IB.Loadout.fixArsenal(start.concat(['pip']), W.playable);
    s.arsenal = ars; s.owned = ars.slice();
    s.loadout = IB.Loadout.fix(s.loadout, ars, IB.Skills.loadoutMax(s.highest));
    return s.loadout;
  }
  G.syncArmory = syncArmory;
  function grantMelee(id) { var m = G.slot.melee || (G.slot.melee = []); if (m.indexOf(id) < 0) m.push(id); }
  /* a save that already cleared a level gets what stood at its start (saves from before these weapons existed, or a
     stand walked past): guns join the arsenal, melee weapons the melee rack, frag cans the belt */
  function grantCleared() {
    ensureSlot();
    var s = G.slot, h = s.highest || 0;
    Object.keys(IB.UNLOCKS || {}).forEach(function (lv) {
      if (+lv > h) return;
      IB.UNLOCKS[lv].forEach(function (id) {
        var def = IB.WEAPONS[id]; if (!def) return;
        if (def.cls === 'melee') { if (IB.Assets.node['WPN_' + id.toUpperCase()]) grantMelee(id); }
        else if (def.cls === 'grenade') s.frag = true;
        else if (W.playable(id) && s.arsenal && s.arsenal.indexOf(id) < 0) s.arsenal.push(id);
      });
    });
    if (s.melee && s.melee.length && s.melee.indexOf(s.meleeSel) < 0) s.meleeSel = s.melee[s.melee.length - 1];
  }
  G.grantCleared = grantCleared;
  G.meleeId = function () { return G.slot && G.slot.melee && G.slot.melee.length ? (G.slot.melee.indexOf(G.slot.meleeSel) >= 0 ? G.slot.meleeSel : G.slot.melee[0]) : null; };
  // stat skills on top of the Upgrade Bench effects; fresh = level start (full health), else keep the damage taken
  function applySkillStats(fresh) {
    var p = G.player, fx = G.fx || {}, sk = IB.SkillFX.fx;
    var hpWas = p.maxHp || 100, hurt = Math.max(0, hpWas - p.health);
    // base health grows with the player level (IB.Damage.playerMaxHp); bench and skills add on top
    var lvHp = IB.Damage.playerMaxHp(IB.Skills.playerLevel(G.slot ? IB.Skills.gained(G.slot) : 0));
    p.maxHp = Math.round(((fx.maxHp || 100) - 100 + lvHp) * sk.maxHpMul);   // Healthy: +% max health
    p.vestHp = IB.Gear && IB.Gear.vestHp ? IB.Gear.vestHp(G) : 0;           // a worn armour vest adds flat health
    p.maxHp += p.vestHp;
    p.health = fresh ? p.maxHp : Math.max(1, Math.min(p.maxHp, p.maxHp - hurt));
    var stWas = p.staminaMax || 4;
    p.staminaMax = 4 * (fx.staminaMul || 1) * sk.staminaMul;   // Stamina: runs last 2.5x longer, 2x faster, half the recharge
    p.stamina = fresh ? p.staminaMax : Math.min(p.staminaMax, p.stamina * p.staminaMax / stWas);
    p.sprintMul = sk.sprintMul; p.staminaRechargeMul = sk.staminaRechargeMul; p.skillMoveMul = sk.moveMul || 1;
    if (G.ws) {
      var wf = G.ws.fx;
      wf.reloadMul = (fx.reloadMul || 1) * sk.reloadMul; wf.recoilMul = (fx.recoilMul || 1) * sk.recoilMul;
      wf.spreadMul = (fx.spreadMul || 1) * sk.spreadMul; wf.magMul = sk.magMul; wf.rateMul = sk.rateMul; wf.swapMul = sk.swapMul;
    }
  }
  // starter gear (IB.LOOT.starters): shields unlock with level 3, armour vests with level 5. The first time a save has
  // cleared that level a common item is put in the bag and worn (drops of that type start at the same point), so
  // every player sees the shield bar from level 4 on and wears a vest from level 6 on. Older saves past those levels
  // get theirs at the next level start.
  function grantStarterShield() {
    if (!IB.Gear || !IB.Loot || !G.slot) return;
    var g = IB.Gear.gear(G), h = G.slot.highest || 0, given = false;
    if (!g) return;
    IB.LOOT.starters.forEach(function (s) {
      if (h < s.cleared || g[s.flag]) return;
      g[s.flag] = true; given = true;
      var item = IB.Loot.makeItem(s.type, 'common', s.cleared, Math.random), slot = IB.Loot.slotOf(item);
      if (IB.Loot.addItem(g, item) && !g[slot]) IB.Loot.equipWorn(g, slot, item.id);
      (G.starterNotes = G.starterNotes || []).push({ item: item, note: s.note });
    });
    if (given) G.store.save(G.slot);
  }
  G.grantStarterShield = grantStarterShield;
  G.progress = function () {
    var h = G.slot ? G.slot.highest || 0 : 0, g = G.slot ? IB.Skills.gained(G.slot) : 0, lv = IB.Skills.playerLevel(g);
    return { highest: h, gained: g, xp: G.slot ? G.slot.xp || 0 : 0, level: lv, title: IB.Skills.rankTitle(lv),
      points: G.slot ? IB.Skills.available(G.slot.skills || {}, g) : 0, earned: IB.Skills.earned(g), loadoutMax: IB.Skills.loadoutMax(h) };
  };
  /* Player XP (data/skills.js IB.XP): robots pay as they are wrecked, a level clear pays a bonus. A level-up raises
     max health at once (the gain is healed), pays skill points up to LV 20, shows a toast and saves. */
  function addXp(n) {
    ensureSlot();
    if (!(n > 0)) return;
    var before = IB.Skills.levelFromXp(G.slot.xp);
    G.slot.xp = (G.slot.xp || 0) + n;
    var after = IB.Skills.levelFromXp(G.slot.xp);
    if (after > before) {
      var pts = IB.Skills.earned(after - 1) - IB.Skills.earned(before - 1), hp0 = G.player.maxHp || 100;
      applySkillStats(false);
      G.player.health = Math.min(G.player.maxHp, G.player.health + Math.max(0, G.player.maxHp - hp0));
      if (G.mode === 'play') {
        HUD.toast('LEVEL UP · LV ' + after + ' ' + IB.Skills.rankTitle(after) + ' · max health ' + Math.round(G.player.maxHp) + (pts ? ' · +' + pts + ' skill point' + (pts > 1 ? 's' : '') + ' (Tab)' : ''), 3.2);
        A.play('hatch');
      }
      hudLevel();
      G.store.save(G.slot);
    }
  }
  G.addXp = addXp;
  function hudLevel() { if (HUD.level) { var pr = G.progress(); HUD.level(pr.level, pr.title, pr.points); } }
  // after the Tab menu: skills may have changed (stats, effects) and so may the loadout
  G.applyProgress = function () {
    ensureSlot();
    IB.SkillFX.refresh(G.slot.skills);
    applySkillStats(false);
    W.setLoadout(G.ws, syncArmory(), G.bank);
    if (IB.Gear) IB.Gear.refresh(G);   // guns joining the loadout get their attachments back
    hudLevel();
  };
  G.openMenu = function (tab) {
    if (G.mode !== 'play' || G.dead || G.complete || !IB.TabMenu) return;
    G.mode = 'menu'; Inp.enabled = false; Inp.reset(); Inp.releaseLock(); IB.Plat.stop();
    HUD.show(false); document.getElementById('touch').hidden = true;
    A.play('ui');
    IB.TabMenu.open(G, tab);
  };
  G.closeMenu = function () {
    if (G.mode !== 'menu') return;
    IB.TabMenu.close();
    G.applyProgress();
    G.store.save(G.slot);
    A.play('uiBack');
    G.resume();
  };

  G.startLevel = function (opts) {
    M.hide();
    G.mode = 'play'; G.dead = false; G.paused = false; G.complete = false;
    if (!G.pickups) initPickups();
    resetLevelState();
    var p = G.player, z0 = G.level.zones[0];
    Object.assign(p, IB.Player.create());
    ensureSlot();
    var fx = IB.Upgrades && G.slot ? IB.Upgrades.effects(G.slot.upgrades || {}) : {};
    G.fx = fx;
    IB.SkillFX.begin(G.slot.skills);
    p.speedMul = fx.speedMul || 1; p.jumpMul = fx.jumpMul || 1; p.doubleJump = !!fx.doubleJump;
    p.x = z0.entry.x; p.z = z0.entry.z; p.y = 0; p.yaw = 0; p.pitch = 0;
    grantCleared();
    if (IB.GunLevel) IB.GunLevel.fill(G.slot);   // guns without an item level (older saves, granted guns) get one
    var owned = syncArmory();
    G.bank = {};
    G.grenades = G.slot.frag ? IB.WEAPONS.frag.carry : 0;
    G.ws = W.create(owned, { magLevel: (G.slot.upgrades && G.slot.upgrades.mag) || 0, magMul: IB.SkillFX.fx.magMul });
    if (IB.Launchers) IB.Launchers.startLevel(G);   // rocket pool from the save, rolled magazines, ammo director
    applySkillStats(true);
    var first = Object.keys(G.ws.guns).sort(function (a, b) { return IB.WEAPONS[b].slot - IB.WEAPONS[a].slot; })[0] || 'pip';
    W.equip(G.ws, first, true);
    grantStarterShield();
    if (IB.Gear) IB.Gear.startLevel(G);   // attachments on the guns, shield full
    G.run = { time: 0, kills: 0, shots: 0, hits: 0, coreHits: 0, deaths: 0, gems: 0, retries: 3, started: false, introT: AUTOTEST ? 0.05 : 2.3,
      xp: 0, g0: G.slot ? IB.Skills.gained(G.slot) : 0 };   // XP earned this run; level-ups gained when it started
    G.shake = 0; G.trauma = 0; G.hitstop = 0; G.deathT = 0;
    G.fade = opts && opts.fadeIn ? { t: 0, dur: 1.3 } : null;
    setDim(G.fade ? 1 : 0);
    HUD.reset(); HUD.show(true); document.getElementById('touch').hidden = !Inp.touch;
    if (G.starterNotes && IB.LootHUD) { G.starterNotes.forEach(function (n) { IB.LootHUD.loot(n.item, n.note); }); G.starterNotes = null; }   // queued one after another
    // a save from before the new skill tree: its points were refunded on load; say so once
    if (G.slot.skillsRefunded) { delete G.slot.skillsRefunded; HUD.toast('New skill tree: your skill points were refunded (Tab)', 4); }
    HUD.pips(G.level.zones.length, 0, 0);
    if (!AUTOTEST) M.intro({ level: G.plan.level, name: G.plan.name, zones: G.level.zones.length, line: G.plan.intro }, 2.2);
    // save at level start
    ensureSlot(); G.slot.level = G.plan.level; G.slot.plan = G.plan.id; G.slot.owned = G.slot.arsenal.slice(); G.store.save(G.slot); G.saved = true;
    hudLevel();
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
    // Handy Helpers left behind in the zone the player just left: powered down quietly (they would only draw fire
    // through the wall); the ones that came along now belong to this zone
    if (i > 0 && AI.dropRogues) AI.dropRogues(z, i);
    if (z.entryGate && i > 0) { Z.setGate(z.entryGate, false); A.play('gateShut', { pos: z.entryGate, gain: 0.9 }); }
    HUD.pips(G.level.zones.length, i, i);
    if (i > 0) HUD.toast('Zone ' + (i + 1) + ' of ' + G.level.zones.length, 1.6);
  }
  function queueWave(z, w) {
    z.wave = w; z.waveT = 0;
    var p = G.player, list = z.plan.waves[w] || [], k = 0;
    var spawns = z.spawns.filter(function (s) { return Math.hypot(s.x - p.x, s.z - p.z) >= 6; });
    if (!spawns.length) spawns = z.spawns.slice();
    var off = (Math.random() * spawns.length) | 0, GAP = (IB.Damage && IB.Damage.SPAWN_GAP) || 0.18;   // a wave trickles in
    list.forEach(function (entry) {
      for (var n = 0; n < entry[1]; n++) {
        var s = spawns[(off + k) % spawns.length];
        var type = AI.types[entry[0]] ? entry[0] : 'crawler';   // robots without a model yet fall back to the Crawler
        z.queue.push({ type: type, x: s.x, y: s.y || 0, z: s.z, t: GAP * k + Math.floor(k / spawns.length) * 0.8, wait: 0 });
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
        // overwhelm control (core/damage.js crowdCap): while the player is already crowded, the next robot waits in
        // its can a moment (at most SPAWN_WAIT_MAX s each); a wave's robots all still come
        var D0 = IB.Damage, crowded = D0 && D0.crowdCap && z.queue.length && AI.crowd(p, D0.CROWD_R) >= D0.crowdCap(G.plan.level || 1);
        for (var q = z.queue.length - 1; q >= 0; q--) {
          var e = z.queue[q]; e.t -= dt;
          if (e.t <= 0 && crowded && e.wait < D0.SPAWN_WAIT_MAX) { e.wait += 0.4 - e.t; e.t = 0.4; continue; }
          if (e.t <= 0) {
            var dx = p.x - e.x, dz = p.z - e.z, d = Math.hypot(dx, dz) || 1, tx = e.x + dx / d * 1.3, tz = e.z + dz / d * 1.3;
            if (!Z.isOpen(z, tx, tz)) { tx = e.x + dx / d * 0.7; tz = e.z + dz / d * 0.7; }
            if (AI.spawn(e.type, e.x, e.z, i, tx, tz, { y: e.y })) { A.play('hop', { pos: e }); z.queue.splice(q, 1); z.spawnedTotal++; }
            else e.t = 0.3;
          }
        }
        var alive = AI.alive(i) + z.queue.length;
        if (z.wave >= 0 && z.wave < z.plan.waves.length - 1 && z.queue.length === 0 && (alive <= 6 || z.waveT > 22)) queueWave(z, z.wave + 1);
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
    if (IB.Boom) IB.Boom.zoneClear(G.level, i, i + 1 >= G.level.zones.length);   // confetti at the gate, fireworks on a level clear
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
    var h0 = G.slot.highest || 0;
    G.slot.highest = Math.max(h0, L);
    var cx = IB.Skills.clearXp(L);   // the level-clear XP bonus (kills paid theirs as they happened)
    G.run.xp += cx; addXp(cx);
    var g0 = G.run.g0 || 0, g1 = IB.Skills.gained(G.slot);
    var lvUp = IB.Skills.playerLevel(g1) - IB.Skills.playerLevel(g0), ptsUp = IB.Skills.earned(g1) - IB.Skills.earned(g0);
    G.slot.stats = G.slot.stats || {};
    G.slot.stats.kills = (G.slot.stats.kills || 0) + G.run.kills;
    G.slot.stats.deaths = (G.slot.stats.deaths || 0) + G.run.deaths;
    G.slot.stats.time = (G.slot.stats.time || 0) + Math.round(G.run.time);
    G.slot.stats.coreHits = (G.slot.stats.coreHits || 0) + G.run.coreHits;
    G.slot.best = G.slot.best || {}; var key = String(L);
    if (!G.slot.best[key] || G.run.time < G.slot.best[key]) G.slot.best[key] = Math.round(G.run.time);
    G.slot.owned = (G.slot.arsenal || []).slice();
    G.lastResults = { time: G.run.time, kills: G.run.kills, corePct: G.run.hits ? Math.round(G.run.coreHits / G.run.hits * 100) : 0, deaths: G.run.deaths,
      gemsRobots: robots, gemsClear: clear, gemsNoDeath: nd, gemsTotal: robots + clear + nd,
      playerLevel: IB.Skills.playerLevel(g1), levelUp: lvUp, pointsUp: ptsUp, xp: G.run.xp, xpClear: cx,
      slotUp: IB.Skills.loadoutMax(G.slot.highest) > IB.Skills.loadoutMax(h0) };
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
    var line = 'Level ' + G.plan.level + ' cleared · ' + r.kills + ' robots · ' + HUD.mmss(r.time) + ' · +' + r.gemsTotal + ' gems' +
      (r.levelUp ? ' · LV ' + r.playerLevel + (r.pointsUp ? ' · +' + r.pointsUp + ' skill point' + (r.pointsUp > 1 ? 's' : '') : '') : '') +
      (r.slotUp ? ' · third gun slot open' : '');
    var t0 = performance.now();
    if (M.loading) M.loading({ level: next.level, name: next.name, line: line }); else M.intro({ level: next.level, name: next.name, zones: next.zones.length, line: line }, 1.6);
    var prog = function (f) { if (M.loadingProgress) M.loadingProgress(f); };
    prog(0.1);
    // build the next level in steps so the loading screen animates. The loader (black screen + 3D gear, ui/loader.js)
    // stays 3.5 s in all (its last 0.32 s fading out), then the level fades in from dark (G.fade, 1.3 s), ready to fight.
    var HOLD = AUTOTEST ? 300 : 3500, OUT = AUTOTEST ? 60 : 320;
    setTimeout(function () {
      G.switchPlan(next).then(function () { prog(0.7); setTimeout(function () {
        try { R.renderer.compile(R.scene, R.camera); } catch (e) { /* first frame compiles anyway */ }
        prog(1);
        setTimeout(function () {
          if (M.loadingHide) M.loadingHide(null, OUT);
          G.startLevel({ fadeIn: true });
        }, Math.max(0, HOLD - OUT - (performance.now() - t0)));
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
  // when badly hurt, eight when critical (< 30 %). New cans land on open, reachable ground 7-22 m away (critical: 4-12 m,
  // checked twice as often; never on top of the player), and show on the radar.
  // health cans restore 40% of max health (40 at LV 1), rounded to 5
  function healAmount() { return Math.max(40, Math.round(G.player.maxHp * 0.4 / 5) * 5); }
  // core/damage.js healthPlan: cans wanted, check interval and landing ring for a health fraction (critical: x2, closer)
  function healthPlan(frac) { return IB.Damage.healthPlan(frac); }
  function healthWanted(frac) { return healthPlan(frac).want; }
  function healthDirector(dt) {
    G.hdT = (G.hdT || 0) - dt;
    if (G.hdT > 0 || !G.run.started || G.dead || G.complete) return;
    G.hdT = 2.5;
    var p = G.player, zi = Z.zoneAt(G.level, p.x, p.z);
    if (zi < 0) return;
    var plan = healthPlan(p.health / p.maxHp);
    G.hdT = plan.every;   // critically hurt: twice as often (and twice as many cans, closer)
    var z = G.level.zones[zi], want = plan.want, have = 0, nav = z.nav, flow = zi === G.zone && nav && !nav.layers && nav.dist;
    G.pickups.forEach(function (pk) { if (pk.on && pk.kind === 'health' && pk.x > z.ox && pk.x < z.ox + z.w && pk.z > z.oz && pk.z < z.oz + z.h) have++; });
    if (have >= want) return;
    for (var tries = 0; tries < 60; tries++) {
      var x = z.ox + 2 + Math.random() * (z.w - 4), zz = z.oz + 2 + Math.random() * (z.h - 4), d = Math.hypot(x - p.x, zz - p.z);
      if (d < plan.dMin || d > plan.dMax || !Z.isOpen(z, x, zz) || !Z.isOpen(z, x + 0.6, zz) || !Z.isOpen(z, x - 0.6, zz) || !Z.isOpen(z, x, zz + 0.6) || !Z.isOpen(z, x, zz - 0.6)) continue;
      // reachable: on the flow field toward the player (zones without walkable layers; the field is fresh every 0.25 s)
      if (flow) { var nc = Z.navCell(z, x, zz); if (nc < 0 || flow[nc] >= 32767) continue; }
      var near = G.pickups.some(function (pk) { return pk.on && Math.hypot(pk.x - x, pk.z - zz) < (plan.critical ? 2.5 : 4); });
      if (near) continue;
      if (G.spawnPickup('health', x, zz)) { FX.puff(x, 0.4, zz, 4, PAL.green, 0.15, 0.45, 1.5); return; }
    }
  }
  G.healthWanted = healthWanted;

  function initPickups() {
    G.pickups = [];
    var geo = { ammo: IB.Assets.get('PICKUP_Ammo'), health: IB.Assets.get('PICKUP_Health') };
    // big levels place up to ~10 of each on the map; robots drop more (ammo) and the health director adds cans
    for (var i = 0; i < 44; i++) {
      var kind = i < 22 ? 'ammo' : 'health';
      var m = new THREE.Mesh(geo[kind], IB.Assets.mat.weapons); m.visible = false; R.scene.add(m);
      G.pickups.push({ kind: kind, mesh: m, on: false, x: 0, y: 0, z: 0 });
    }
  }
  // ---------------- elevators: who rides (the player, ground robots standing on the cab floor) ----------------
  var _riders = [];
  function elevatorRiders(p) {
    _riders.length = 0;
    if (p.alive) _riders.push({ x: p.x, y: p.y, z: p.z, set: function (dh) { p.y += dh; } });
    AI.robots.forEach(function (r) { if (r.on && r.state !== 'pose' && !(AI.VIS[r.type] && AI.VIS[r.type].flying)) _riders.push({ x: r.x, y: r.fy || 0, z: r.z, set: function (dh) { r.fy = (r.fy || 0) + dh; r.gy = (r.gy || 0) + dh; r.y += dh; } }); });
    return _riders;
  }

  G.spawnPickup = function (kind, x, z, y) {
    // rest on the highest floor under its whole footprint (slopes, terrain bumps, decks), so the spinning can never dips
    // an edge into the ground; a hint height (a robot on a deck) finds that deck rather than the floor below it
    if (G.level) {
      var W0 = G.level.world, hint = typeof y === 'number' ? y : 0, top = -1e9;
      for (var k = 0; k < 9; k++) {
        var sx = x + (k ? Math.cos(k * Math.PI / 4) * 0.4 : 0), sz = z + (k ? Math.sin(k * Math.PI / 4) * 0.4 : 0);
        var gy = W0.floorAt ? W0.floorAt(sx, sz, hint + 0.6) : W0.groundAt(sx, sz);
        top = Math.max(top, gy, W0.groundAt(sx, sz));
      }
      y = top;
    } else y = 0;
    for (var i = 0; i < G.pickups.length; i++) {
      var pk = G.pickups[i]; if (pk.on || pk.kind !== kind) continue;
      pk.on = true; pk.x = x; pk.y = y; pk.z = z; pk.mesh.position.set(x, y, z); pk.mesh.visible = true; return pk;
    }
    return null;
  };
  function updatePickups(dt, t) {
    var p = G.player;
    G.pickups.forEach(function (pk, i) {
      if (!pk.on) return;
      if (pk.fullT > 0) pk.fullT -= dt;
      pk.mesh.rotation.y = t * 1.5 + i;
      // hover clear of the floor (its lowest point stays ~22 cm up, so the base and its ink outline never sink in)
      pk.mesh.position.y = (pk.y || 0) + 0.27 + Math.sin(t * 3 + i) * 0.03;
      FX.blob(pk.x, pk.y || 0, pk.z, 0.35);
      if (Math.hypot(p.x - pk.x, p.z - pk.z) < 0.9 && p.y < (pk.y || 0) + 1 && p.y > (pk.y || 0) - 0.8) {
        if (pk.kind === 'health') { if (p.health >= p.maxHp) return; var heal = healAmount(); p.health = Math.min(p.maxHp, p.health + heal); HUD.toast('+' + heal + ' health', 1.2); }
        else {
          // full on every gun (and no frag can to gain): leave the box where it is
          var gotCan = G.slot && G.slot.frag && G.grenades < IB.WEAPONS.frag.carry;
          if (!gotCan && W.ammoFull(G.ws)) { if (!(pk.fullT > 0) && HUD.toast) HUD.toast('Ammo full', 1.0); pk.fullT = 3; return; }
          W.addAmmo(G.ws, 0.5);
          if (gotCan) G.grenades++;
          HUD.toast(gotCan ? 'Ammo + frag can' : 'Ammo', 1.0);
        }
        pk.on = false; pk.mesh.visible = false; A.play('pickup');
      }
    });
  }

  // ---------------- combat glue ----------------
  var _org = new THREE.Vector3(), _end = new THREE.Vector3(), _mz = new THREE.Vector3();
  var _shot = { ox: 0, oy: 0, oz: 0, dx: 0, dy: 0, dz: 0, t: 0, wt: 0, def: null };   // for Stream / Ricochet (skillfx.js)
  function shoot(origin, dir, def) {
    var ox = origin.x, oy = origin.y, oz = origin.z, dx = dir.x, dy = dir.y, dz = dir.z;
    G.run.shots++;
    var wh = G.level.world.ray(ox, oy, oz, dx, dy, dz, 200), wt = wh ? wh.t : 200;
    var whit = wh ? { t: wh.t, box: wh.box, nx: wh.nx, ny: wh.ny, nz: wh.nz } : null;
    var rh = AI.raycast(ox, oy, oz, dx, dy, dz, wt);
    var endT = rh ? rh.t : wt;
    // piercing guns (Needle, Railspike): the round goes on through each robot it hits, weaker each time
    if (rh && def.pierce > 0) {
      rh = { robot: rh.robot, t: rh.t, zone: rh.zone };   // AI.raycast reuses one result object
      var skip = [rh.robot], mul = 1;
      for (var pi = 0; pi < def.pierce; pi++) {
        var nx = AI.raycast(ox, oy, oz, dx, dy, dz, wt, skip);
        if (!nx) break;
        mul *= def.pierceMul || 0.7;
        var nt = nx.t, hr = nx.robot, nz = nx.zone; skip.push(hr);
        var res2 = IB.Damage.hit({ weapon: def, dist: nt, zone: nz, dmgLevel: up('dmg'), coreLevel: up('core'), critLevel: up('crit'), rng: Math.random });
        var pd = res2.damage * mul, ex = ox + dx * nt, ey = oy + dy * nt, ez = oz + dz * nt;
        var pk = AI.damage(hr, pd, { kx: dx * 3, kz: dz * 3 }, onKill);
        if (IB.Boom) IB.Boom.robotHit(hr, ex, ey, ez, dx, dy, dz, nz, pk);
        if (IB.Gear) IB.Gear.onHit(hr, { damage: pd }, nz, def, pk);
      }
    }
    _end.set(ox + dx * endT, oy + dy * endT, oz + dz * endT);
    W.muzzleWorld(R.camera, _mz);
    if (def.fire !== 'auto' || G.run.shots % 2 === 0) { if (IB.Boom) IB.Boom.tracer(_mz.x, _mz.y, _mz.z, _end.x, _end.y, _end.z, def); else FX.tracer(_mz.x, _mz.y, _mz.z, _end.x, _end.y, _end.z); }
    AI.hear(G.player.x, G.player.z, 20 * (def.quiet || 1));   // acid muzzles are silenced
    if (rh) {
      var r = rh.robot, zone = rh.zone;
      var res = IB.Damage.hit({ weapon: def, dist: endT, zone: zone, dmgLevel: up('dmg'), coreLevel: up('core'), critLevel: up('crit'), rng: Math.random, blinded: r.state === 'blinded' });
      G.run.hits++; if (zone === 'core') G.run.coreHits++;
      var dmg = res.damage *= IB.SkillFX.hitMul(zone) * (IB.WeaponDrops ? IB.WeaponDrops.dmgMul(def.id) : 1);   // Heavy Ink, the gun's tier
      _shot.ox = ox; _shot.oy = oy; _shot.oz = oz; _shot.dx = dx; _shot.dy = dy; _shot.dz = dz; _shot.t = rh.t; _shot.wt = wt; _shot.def = def;
      var killed = AI.damage(r, dmg, { kx: dx * 4, kz: dz * 4 }, onKill);
      // Electrify, Stream, Ricochet, Hazard, Hydrate, Chain Reaction
      IB.SkillFX.onHit(r, dmg, zone, killed, _end, onKill, _shot);
      FX.puff(_end.x, _end.y, _end.z, zone === 'core' ? 5 : 3, PAL.ink, 0.12, 0.38, 2.2);
      if (zone === 'core') FX.puff(_end.x, _end.y, _end.z, 2, PAL.amber, 0.08, 0.2, 3);
      if (IB.Boom) IB.Boom.robotHit(r, _end.x, _end.y, _end.z, dx, dy, dz, zone, killed);   // sparks, chips, core pop
      if (!killed) { HUD.hit(zone === 'core' ? 'core' : 'hit'); A.play(zone === 'core' ? 'core' : 'hit'); }
      if (IB.Gear) IB.Gear.onHit(r, res, zone, def, killed);   // damage number, acid DoT
    } else if (whit) {
      if (whit.box && whit.box.kind === 'canister' && IB.Boom) IB.Boom.hitCan(whit.box, def.damage || 15);   // explosive canister
      else if (whit.box && whit.box.kind === 'gate') FX.puff(_end.x, _end.y, _end.z, 3, PAL.ink, 0.1, 0.3, 1.5);
      else FX.impact(_end.x, _end.y, _end.z, whit.nx, whit.ny, whit.nz, Math.random() < 1 / 3);
      if (IB.Boom) IB.Boom.impact(_end.x, _end.y, _end.z, whit.nx, whit.ny, whit.nz, whit.box);   // sparks / chips / dust by surface
    }
  }
  function up(id) { return (G.slot && G.slot.upgrades && G.slot.upgrades[id]) || 0; }
  function onKill(r) {
    G.run.kills++;
    var kx = IB.Skills.killXp(r.type, G.plan.level); G.run.xp += kx; addXp(kx);
    HUD.hit('kill'); A.play('crunch', { pos: r });
    var def = IB.ENEMIES[r.type];
    var drop = IB.Gems ? IB.Gems.robotDrop(r.type, G.plan.level, up('press')) : { chip: 1, shard: 0, core: 0, total: 1 };
    var k;
    var gy = (r.fy || 0) + 0.4;   // from the floor the robot stood on (a deck on levels with walkable surfaces)
    for (k = 0; k < drop.chip; k++) FX.dropGem('chip', r.x, gy, r.z, r.zone);
    for (k = 0; k < drop.shard; k++) FX.dropGem('shard', r.x, gy, r.z, r.zone);
    for (k = 0; k < drop.core; k++) FX.dropGem('core', r.x, gy, r.z, r.zone);
    var w = W.current(G.ws);
    HUD.feed(G.lastKillCls || (w ? w.def.cls : 'pistol'), def ? def.name : r.type, drop.total);
    G.lastKillCls = null;
    if (Math.random() < 0.2) G.spawnPickup('ammo', r.x, r.z);
    else if (G.player.health < G.player.maxHp * 0.4 && Math.random() < 0.25) G.spawnPickup('health', r.x, r.z, r.fy || r.y || 0);
    if (G.fx && G.fx.leech) G.player.health = Math.min(G.player.maxHp, G.player.health + G.fx.leech);
    if (IB.Drops) IB.Drops.onKill(r);   // ~5 % loot drop
    if (IB.Launchers) IB.Launchers.onKill(r);   // launcher drops (levels 14+) and rocket crates (soldiers, when needed)
    if (IB.Gear && IB.Gear.onKill) IB.Gear.onKill(G, r);   // Overcharge shield cells
  }
  G.onKill = onKill;
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
    dmg *= IB.SkillFX.hurtMul();   // Tank
    var through = IB.Gear ? IB.Gear.absorb(G, dmg) : dmg;   // an equipped shield takes it first
    p.health -= through; p.lastHurt = 0;
    A.play(robot.proj ? (robot.type === 'bomber' ? 'boom' : 'boltHit') : 'bite', { pos: robot }); if (through > 0) A.play('hurt', { gain: 0.8 });
    // arc pointing toward the attacker
    var dx = robot.x - p.x, dz = robot.z - p.z;
    var fx = -Math.sin(p.yaw), fz = -Math.cos(p.yaw), rx = Math.cos(p.yaw), rz = -Math.sin(p.yaw);
    HUD.arc(Math.atan2(dx * rx + dz * rz, dx * fx + dz * fz)); // 0 = ahead, + = to the right
    G.shake = Math.max(G.shake, 0.5); G.addTrauma(Math.min(0.5, 0.12 + dmg * 0.012));
    if (HUD.damageFlash) HUD.damageFlash(Math.min(1, through / 30));
    if (p.health <= 0) die(robot);
  };
  function die(robot) {
    var p = G.player;
    p.health = 0; p.alive = false; G.dead = true; G.deathT = 0; G.run.deaths++; G.run.retries--;
    G.killer = robot.killer || (IB.ENEMIES[robot.type] || {}).name || 'Robot';
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
    if (IB.Gear) IB.Gear.fillShield(G);
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
      G.slot.arsenal = G.slot.owned.slice(); G.slot.loadout = G.slot.owned.slice(0, IB.Skills.loadoutMax(0));
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
    M.on('fieldkit', function () { if (G.mode !== 'paused') return; M.hide(); G.mode = 'play'; G.openMenu(); });
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
    var dtRaw = Math.max(0, Math.min(0.1, (now - G.last) / 1000)); G.last = now;   // never negative (a rAF stamp can predate a slow boot)
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
    Z.updateLines(G.level, G.mode === 'paused' || G.mode === 'menu' ? 0 : dtRaw, G.mode === 'play' ? G.player : null);   // moving assembly lines
    if (IB.SkillHUD) IB.SkillHUD.update(G, dtRaw);   // Undercover badge + cloak look
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
    if (Inp.menuPressed && !G.dead && G.run.started) { G.openMenu(); return; }
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
      // V: strike with the melee weapon (a shove until one is picked up); B: next melee weapon; G: throw a frag can
      if (Inp.meleePressed && G.run.started) { var mid = G.meleeId(); if (mid) meleeSwing(mid); else if (W.shove(G.ws)) doShove(); }
      if (Inp.meleeCyclePressed) cycleMelee();
      if (Inp.grenadePressed && G.run.started) { if (G.grenades > 0) W.throwStart(G.ws); else if (G.slot && G.slot.frag) HUD.toast('No frag cans · ammo boxes give one back', 1.4); }
      if (Inp.cloakPressed) IB.SkillFX.tryCloak(p);       // F: Undercover
    }
    // fixed-step simulation
    acc += dt; var steps = 0;
    // presses are held until a fixed step consumes them: on frames shorter than one step (120/144 Hz screens) no
    // step runs, and a press seen only on that frame would otherwise be dropped
    G.jumpLatch = G.jumpLatch || Inp.jumpPressed; G.slideLatch = G.slideLatch || Inp.slidePressed;
    var jump = G.jumpLatch, slidePress = G.slideLatch;
    while (acc >= STEP && steps < 4) {
      acc -= STEP; steps++;
      if (G.level.elevators && G.level.elevators.length) Z.updateElevators(G.level, STEP, elevatorRiders(p));
      if (p.alive) IB.Player.step(p, { mx: G.complete ? 0 : Inp.mx, mz: G.complete ? 0 : Inp.mz, sprint: Inp.sprint && !G.ws.melee, jumpPressed: jump, slidePressed: slidePress, crouch: Inp.crouch }, G.level.world, STEP, footFx);
      jump = false; slidePress = false; G.jumpLatch = false; G.slideLatch = false;
      if (G.run.started) {
        var actx = { player: p, world: G.level.world, level: G.level, activeZone: G.level.zones[G.zone].state === 'active' ? G.zone : -1, hurt: G.hurt, shake: G.addTrauma, onKill: onKill };
        AI.update(STEP, actx);
        IB.Projectiles.update(STEP, actx);
        if (IB.Throwables) IB.Throwables.update(STEP, G.level.world);
        if (IB.Launchers) IB.Launchers.update(STEP, actx);   // rockets and homing missiles in flight
      }
      if (G.run.started && !G.dead) updateZones(STEP);
    }
    if (IB.Status && G.run.started) IB.Status.update(dt, onKill);   // shock / acid damage over time
    if (acc > STEP * 4) acc = 0;
    if (G.run.started && !G.complete && !G.dead) G.run.time += dt;
    // regen (Nanite Welders)
    if (G.fx && G.fx.regen && p.alive && p.lastHurt > 3) p.health = Math.min(p.maxHp, p.health + G.fx.regen * dt);
    IB.SkillFX.regen(p, dt);   // Healthy + Tank repair
    if (G.run.started) IB.SkillFX.update(dt, onKill, p);   // acid pools, wet coats, Undercover timer
    // weapons
    W.update(G.ws, dt, { player: p, cam: R.camera, input: { fire: Inp.fire && p.alive && G.run.started, firePressed: Inp.firePressed && p.alive && G.run.started, aim: Inp.aim && p.alive }, shoot: shoot,
      melee: meleeHit, onThrow: throwFrag, rocket: IB.Launchers ? IB.Launchers.fire : null,
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
    IB.SkillFX.syncMesh(tAll);   // acid pool decals
    updatePickups(dtRaw, tAll);
    if (IB.Throwables) IB.Throwables.sync(tAll);
    if (IB.Drops) { IB.Drops.update(dtRaw, tAll, G); IB.Gear.update(dtRaw, G); }
    if (IB.WeaponDrops) IB.WeaponDrops.update(dtRaw, tAll, G);
    if (IB.Launchers) IB.Launchers.sync(dtRaw, tAll, G);   // rocket meshes, lock brackets, rocket crates
    if (G.mode === 'play') updateLoot();
    var magnet = 2.5 * (1 + 0.5 * up('magnet')) * IB.SkillFX.fx.magnetMul;   // Scrap Magnet
    FX.update(dtRaw, R.camera, p, magnet, collectGem);
    W.pose(G.ws, dtRaw, p, Inp.lookDX, Inp.lookDY, s.headBob, tAll);
    // HUD
    var zn = G.level.zones[G.zone];
    var w = W.current(G.ws);
    HUD.health(p.health, p.maxHp);
    if (w) {
      HUD.ammo(w.mag, w.reserve);
      var WDp = IB.WeaponDrops;
      if (HUD.weapon) HUD.weapon({ id: w.id, name: WDp ? WDp.nameOf(w.id) : w.def.name, cls: w.def.cls, level: WDp ? WDp.levelOf(w.id) : 0, mag: w.mag, magSize: W.magSize(G.ws, w.def), reserve: w.reserve,
        reloading: G.ws.state === 'reload', reloadFrac: G.ws.state === 'reload' ? Math.min(1, G.ws.t / G.ws.reloadT) : 0 });
    }
    if (HUD.stamina) HUD.stamina(p.stamina / (p.staminaMax || 4), p.sliding);
    G.radarT = (G.radarT || 0) - dtRaw;
    if (HUD.radar && G.radarT <= 0) {
      G.radarT = 0.1;
      var rob = [];
      AI.robots.forEach(function (r) { if (r.on && r.state !== 'pose') rob.push({ x: r.x, z: r.z, alert: !(r.rogue > 0) && r.state !== 'idle' && r.state !== 'spawn', rogue: r.rogue > 0 }); });
      var gates = []; G.level.zones.forEach(function (zz) { gates.push({ x: zz.exitGate.x, z: zz.exitGate.z, open: zz.exitGate.open > 0.5 }); });
      var last = G.level.zones[G.level.zones.length - 1];
      HUD.radar({ px: p.x, pz: p.z, yaw: p.yaw, range: 30, robots: rob, gates: gates,
        pickups: (G.weaponStands || []).filter(function (w2) { return !w2.taken; }).map(function (w2) { return { x: w2.x, z: w2.z, kind: 'weapon' }; })
          .concat(G.pickups.filter(function (pk) { return pk.on; }).map(function (pk) { return { x: pk.x, z: pk.z, kind: pk.kind }; }))
          .concat(IB.Drops ? IB.Drops.radar() : []).concat(IB.WeaponDrops ? IB.WeaponDrops.radar() : []).concat(IB.Launchers ? IB.Launchers.radar() : []),
        exit: last.state === 'cleared' ? { x: G.level.hatch.x, z: G.level.hatch.z } : null });
    }
    if (HUD.objective) {
      var obj = zn.state === 'active' ? 'Clear the block · ' + (AI.alive(G.zone) + zn.queue.length + remainingInWaves(zn)) + ' robots' :
        (G.level.zones[G.level.zones.length - 1].state === 'cleared' ? 'Walk the exit path' : 'Follow the arrows to the next gate');
      HUD.objective(obj);
    }
    if (HUD.kit) { var mk = G.meleeId(); HUD.kit(mk ? IB.WEAPONS[mk].name : null, G.slot && G.slot.frag ? G.grenades : -1); }
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

  // ---------------- melee hits, melee rack, frag cans ----------------
  var _mv = new THREE.Vector3();
  /* a melee blow lands (weapons.js calls this at the swing's 'hit' fraction): every robot in range inside the arc, in
     sight; the nearest takes the full blow, the rest x0.6 (nunchucks: all full). Katana: the third swing x comboMul.
     Dagger: x backstab on a robot that has not seen the player or is struck from behind. Voltaxe: shock DoT, then arcs to
     the nearest robots. */
  function meleeHit(def, combo, hitNo) {
    var p = G.player, yaw = p.yaw, fx = -Math.sin(yaw), fz = -Math.cos(yaw), cosArc = Math.cos(def.arc * Math.PI / 360);
    var eyeY = IB.Player.eyeY(p, false), hits = [];
    AI.robots.forEach(function (r) {
      if (!r.on || r.state === 'pose' || r.state === 'spawn' || r.rogue > 0) return;
      var v = AI.VIS[r.type], dx = r.x - p.x, dz = r.z - p.z, d = Math.hypot(dx, dz), reach = d - v.radius;
      if (reach > def.range) return;
      if (r.y + v.y1 < p.y - 0.4 || r.y + v.y0 > p.y + 2.4) return;
      if (d > 0.6 && (dx * fx + dz * fz) / d < cosArc) return;
      if (!G.level.world.los(p.x, eyeY, p.z, r.x, r.y + (v.y0 + v.y1) / 2, r.z)) return;
      hits.push({ r: r, d: reach, dx: dx / (d || 1), dz: dz / (d || 1) });
    });
    hits.sort(function (a, b) { return a.d - b.d; });
    var base = def.damage * ((G.fx && G.fx.meleeMul) || 1) * (IB.SkillFX && IB.SkillFX.hitMul ? IB.SkillFX.hitMul('body') : 1);
    if (def.combo > 1 && combo >= def.combo - 1) base *= def.comboMul || 1;
    if (G.meleeWinded) base *= MELEE_WINDED.dmg;
    if (IB.WeaponDrops) base *= IB.WeaponDrops.dmgMul(def.id);
    var landed = 0;
    hits.forEach(function (h, i) {
      var r = h.r, dmg = base * (i === 0 || def.id === 'nunchucks' ? 1 : 0.6);
      if (def.backstab) {
        var behind = (Math.sin(r.yaw) * -h.dx + Math.cos(r.yaw) * -h.dz) < -0.2;   // the robot faces away from the player
        if (!r.seesPlayer || r.state === 'idle' || behind) dmg *= def.backstab;
      }
      G.lastKillCls = 'melee';
      var kb = (def.knockback || 3) + (combo === 2 ? 3 : 0);
      var killed = AI.damage(r, dmg, { stagger: !!def.stagger || combo === 2 || def.id === 'eaxe', kx: h.dx * kb, kz: h.dz * kb }, onKill);
      landed++;
      var v = AI.VIS[r.type], hy = r.y + (v.y0 + v.y1) / 2;
      if (IB.Boom) IB.Boom.robotHit(r, r.x - h.dx * v.radius, hy, r.z - h.dz * v.radius, h.dx, 0, h.dz, 'body', killed);
      if (IB.Gear && IB.Gear.onHit) IB.Gear.onHit(r, { damage: dmg }, 'body', def, killed);   // damage number
      if (def.shock && !killed && IB.Status) IB.Status.apply(r, 'shock', def.shock.dps * ((AI.hpMul) || 1), def.shock.dur);
      if (def.shock && i === 0) chainZap(r, dmg * def.shock.chainMul, def.shock);
    });
    if (landed) {
      G.hitstop = def.id === 'eaxe' ? 0.07 : 0.045; HUD.hit('hit'); A.play('hit', { pitch: def.id === 'eaxe' ? 0.7 : 1 });
      if (def.id === 'eaxe') { A.play('boltHit'); G.addTrauma(0.25); } else G.addTrauma(0.1);
      AI.hear(p.x, p.z, 8);
    } else {
      // a swing into a wall or cover: chips and a clank
      R.camera.getWorldDirection(_mv);
      var wh = G.level.world.ray(R.camera.position.x, R.camera.position.y, R.camera.position.z, _mv.x, _mv.y, _mv.z, def.range);
      if (wh && hitNo === 0) {
        var ex = R.camera.position.x + _mv.x * wh.t, ey = R.camera.position.y + _mv.y * wh.t, ez = R.camera.position.z + _mv.z * wh.t;
        if (wh.box && wh.box.kind === 'canister' && IB.Boom) IB.Boom.hitCan(wh.box, def.damage);
        else { FX.impact(ex, ey, ez, wh.nx, wh.ny, wh.nz, false); if (IB.Boom) IB.Boom.impact(ex, ey, ez, wh.nx, wh.ny, wh.nz, wh.box); }
        A.play('hit', { pitch: 0.6, gain: 0.6 });
      }
    }
    return landed;
  }
  function chainZap(src, dmg, sh) {
    var near = AI.robots.filter(function (r) { return r.on && r !== src && r.state !== 'spawn' && r.state !== 'pose' && !(r.rogue > 0) && Math.hypot(r.x - src.x, r.z - src.z) < sh.chainRange; })
      .sort(function (a, b) { return Math.hypot(a.x - src.x, a.z - src.z) - Math.hypot(b.x - src.x, b.z - src.z); }).slice(0, sh.chain);
    near.forEach(function (r) {
      var va = AI.VIS[src.type], vb = AI.VIS[r.type];
      if (IB.Boom && IB.Boom.lightning) IB.Boom.lightning(src.x, src.y + (va.y0 + va.y1) / 2, src.z, r.x, r.y + (vb.y0 + vb.y1) / 2, r.z);
      G.lastKillCls = 'melee';
      if (!AI.damage(r, dmg, { stagger: true }, onKill) && IB.Status) IB.Status.apply(r, 'shock', sh.dps * (AI.hpMul || 1), sh.dur);
    });
  }
  G.meleeHit = meleeHit;
  // a swing spends stamina (a share of the pool) and ends a sprint; out of stamina it is slower and weaker
  var MELEE_WINDED = { rate: 1 / 1.5, dmg: 0.6 };
  function meleeSwing(id) {
    var p = G.player, def = IB.WEAPONS[id], max = p.staminaMax || 4, cost = (def.stamina || 0.15) * max;
    if (!W.meleeReady(G.ws)) return;
    G.meleeWinded = p.stamina < cost * 0.5;
    G.ws.fx.meleeRate = G.meleeWinded ? MELEE_WINDED.rate : 1;
    if (W.meleeStart(G.ws, id)) {
      p.stamina = Math.max(0, p.stamina - cost); p.staminaRest = 0; p.sprinting = false;
      if (G.meleeWinded && HUD.toast) HUD.toast('Winded · slower swings', 0.9);
    }
  }
  G.meleeSwing = meleeSwing;
  function cycleMelee() {
    var list = G.slot && G.slot.melee; if (!list || list.length < 2) return;
    var i = list.indexOf(G.meleeId());
    G.slot.meleeSel = list[(i + 1) % list.length];
    HUD.toast('Melee: ' + IB.WEAPONS[G.slot.meleeSel].name + ' (V)', 1.4); A.play('draw');
  }
  // the frag can leaves the support hand (weapons.js throw clip, release frame): from by the left shoulder, along the view
  function throwFrag() {
    if (G.grenades <= 0) return;
    G.grenades--;
    var def = IB.WEAPONS.frag, c = R.camera, p = G.player;
    c.getWorldDirection(_mv);
    var rx = Math.cos(p.yaw), rz = -Math.sin(p.yaw);
    var sp = def.speed || 18, lift = def.throwUp || 4;
    var hpMul = (AI.hpMul || 1) * (1 + 0.2 * up('blast'));
    IB.Throwables.throw(c.position.x - rx * 0.25 + _mv.x * 0.5, c.position.y - 0.1 + _mv.y * 0.5, c.position.z - rz * 0.25 + _mv.z * 0.5,
      _mv.x * sp * 0.68 + p.vx * 0.5, _mv.y * sp * 0.68 + lift * 0.8, _mv.z * sp * 0.68 + p.vz * 0.5, def, hpMul);   // ~12 m on the flat
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
    tabMenu: function (tab) { G.openMenu(tab); }, closeTabMenu: function () { G.closeMenu(); },
    progress: function () {
      var pr = G.progress(); pr.skills = G.slot ? Object.assign({}, G.slot.skills) : {};
      pr.arsenal = G.slot ? G.slot.arsenal.slice() : []; pr.loadout = G.slot ? G.slot.loadout.slice() : [];
      pr.carried = W.ownedSlots(G.ws).map(function (k) { return G.ws.slots[k]; }); return pr;
    },
    setTier: function (t) { G.setTier(t); },
    // skills: set a tree directly (no gates or budget: tests only), force chance skills (id -> 0..1), state
    setSkills: function (sk) { ensureSlot(); G.slot.skills = Object.assign({}, sk); G.applyProgress(); return IB.SkillFX.fx; },
    forceSkill: function (id, p) { if (p === null) delete IB.SkillFX.force[id]; else IB.SkillFX.force[id] = p; IB.SkillFX.refresh(G.slot.skills); },
    skillState: function () {
      var SF = IB.SkillFX, c = SF.cloakState();
      return { cloak: c, cloaked: AI.cloaked, rogues: AI.robots.filter(function (r) { return r.on && r.rogue > 0; }).length,
        pools: SF.activePools(), coats: SF.activeCoats(), stats: Object.assign({}, SF.stats), maxHp: G.player.maxHp, staminaMax: G.player.staminaMax,
        sprintMul: G.player.sprintMul, swapMul: G.ws.fx.swapMul, reloadMul: G.ws.fx.reloadMul, shoveT: G.ws.shoveT,
        seeing: AI.robots.filter(function (r) { return r.on && !(r.rogue > 0) && r.seesPlayer; }).length,
        attacking: AI.robots.filter(function (r) { return r.on && !(r.rogue > 0) && (r.state === 'windup' || r.state === 'attack'); }).length };
    },
    // spawn a robot type at (x, z) in the current zone, awake (returns its slot)
    spawnRobot: function (type, x, z) {
      var r = AI.spawn(type, x, z, G.zone, x, z); if (!r) return -1;
      r.state = 'idle'; r.st = 0; r.x = x; r.z = z; r.y = AI.VIS[type].flying ? r.hy : 0; r.vx = r.vz = 0;
      return r.slot;
    },
    // fire one bullet of the gun in hand from (ox, oy, oz) along (dx, dy, dz) through the normal hit path
    fireRay: function (ox, oy, oz, dx, dy, dz) { var L = Math.hypot(dx, dy, dz) || 1; shoot({ x: ox, y: oy, z: oz }, { x: dx / L, y: dy / L, z: dz / L }, W.current(G.ws).def); },
    // a lethal hit from the player on robot i of type (Handy Helpers can turn it rogue)
    wreck: function (type, slot) { var r = AI.types[type].slots[slot]; return AI.damage(r, r.hp + 1, {}, onKill); },
    robot: function (type, slot) { var r = AI.types[type].slots[slot]; return { on: r.on, hp: r.hp, maxHp: r.maxHp, rogue: r.rogue, state: r.state, x: r.x, z: r.z, wet: r.wet, tgtRogue: !!(r.tgt && r.tgt.rogue > 0) }; },
    setRogueTime: function (t) { AI.robots.forEach(function (r) { if (r.on && r.rogue > 0) r.rogue = t; }); }
  };
  if (IB.GearTest) Object.keys(IB.GearTest).forEach(function (k) { window.__TEST__[k] = IB.GearTest[k]; });   // loot hooks (game/gear.js)
  if (IB.LauncherTest) Object.keys(IB.LauncherTest).forEach(function (k) { window.__TEST__[k] = IB.LauncherTest[k]; });   // launchers.js

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', G.boot); else G.boot();
})(window.IB = window.IB || {});
