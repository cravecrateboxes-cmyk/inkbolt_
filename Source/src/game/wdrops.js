/* INKBOLT weapon drops: guns of a quality tier (gray, green, blue, purple, orange) and melee weapons dropped by robots.
   Enemy rows carry the odds (src/data/enemies.js): weaponDrops {gray, green, blue, purple, orange} (soldiers),
   meleeDrop (blade bots drop the katana or the Voltaxe they wield). ai.js / game.js call IB.WeaponDrops.roll(r) /
   IB.WeaponDrops.melee(r, id) on a player kill.
   A dropped gun is one of the guns unlocked up to this level, lying in a tall glowing beam of its tier colour (and on
   the radar). Every drop also has an item level (the campaign level it dropped on; core/gunlevel.js).
   Nothing is picked up by walking over it and nothing is ever broken down into gems: walk up to a gun (its card
   shows) and press E (touch: USE) to take it, or leave it lying there. A model you do not own joins the arsenal and is
   carried at once when a loadout slot is free, otherwise it goes to the backpack. A model you already own is swapped:
   the new one takes its place and the one you had is laid on the floor where the other was.
   Tier x level multiply the gun's damage (dmgMul: game.js shoot / meleeHit, launchers.js) and are saved per gun in
   slot.gunTier / slot.gunLevel (launchers also their rolled magazine and element in slot.gunRoll).
   From campaign level 14 a kill may also drop a launcher (rollLauncher; IB.GunLevel.launcherDropChance).
     IB.WeaponDrops.init(scene) / clear() / update(dt, t, G) / radar() / tierOf(id) / levelOf(id) / dmgMul(id) /
     useTarget(G) / take(d, G) (game.js updateLoot: the E prompt) /
     acquire(id, tier, level, roll) (also used by the armory racks in game.js) */
(function (IB) {
  'use strict';
  var WD = IB.WeaponDrops = { list: [] };
  var TIERS = WD.TIERS = [
    { id: 'gray', name: 'Standard', color: '#C9C6BE', dmg: 1.00, gems: 15 },
    { id: 'green', name: 'Tuned', color: '#6BE05A', dmg: 1.07, gems: 30 },
    { id: 'blue', name: 'Rare', color: '#4A9BFF', dmg: 1.14, gems: 60 },
    { id: 'purple', name: 'Epic', color: '#B77BFF', dmg: 1.22, gems: 110 },
    { id: 'orange', name: 'Legendary', color: '#FF9A2E', dmg: 1.32, gems: 200 }
  ];
  var BY = {}; TIERS.forEach(function (t, i) { t.rank = i; BY[t.id] = t; });
  WD.tier = function (id) { return BY[id] || BY.gray; };
  var CAP = 8, USE_R = 2.4, CLOSE_R = 1.2, PEEK_R = 7;   // E reach (looking at it), reach whatever you look at, card distance

  function slot() { return IB.Game && IB.Game.slot; }
  WD.tierOf = function (gunId) { var s = slot(); return WD.tier(s && s.gunTier && s.gunTier[gunId]); };
  function GL() { return IB.GunLevel; }
  function playerLv() { var s = slot(); return IB.Skills && IB.Skills.gained ? IB.Skills.playerLevel(s ? IB.Skills.gained(s) : 0) : 1; }
  function curLevel() { return (IB.Game && IB.Game.plan && IB.Game.plan.level) || 1; }
  /* the level a gun fights at (its own, or player level - 4); melee weapons have none and ride the floor */
  WD.ownLevel = function (gunId) { var s = slot(); return (s && s.gunLevel && s.gunLevel[gunId]) || 1; };
  WD.levelOf = function (gunId) { return GL() ? GL().effective(WD.ownLevel(gunId), playerLv(), curLevel()) : 1; };
  /* level 21+ guns (their own gun level): the top tiers hit harder on top of the tier multiplier, orange the most */
  WD.LATE_BOOST = { level: 21, blue: 1.04, purple: 1.07, orange: 1.15 };
  WD.lateBoost = function (tierId, lv) { return lv >= WD.LATE_BOOST.level ? WD.LATE_BOOST[tierId] || 1 : 1; };
  WD.dmgMul = function (gunId) { var r = WD.rollOf(gunId); return WD.lateBoost(WD.tierOf(gunId).id, WD.ownLevel(gunId)) * WD.tierOf(gunId).dmg * (GL() ? GL().mul(WD.levelOf(gunId)) : 1) * (r && r.mult ? r.mult : 1); };
  WD.rollOf = function (gunId) {
    var s = slot(), def = IB.WEAPONS[gunId], gl = GL(), saved = s && s.gunRoll && s.gunRoll[gunId];
    if (!def || !gl) return null;
    if (gl.isLauncher(def)) return gl.fixRoll(def, saved);
    if (def.magRange) {   // the Warden: its magazine is rolled the first time it is needed, then kept in the save
      if (!saved && s) { s.gunRoll = s.gunRoll || {}; saved = s.gunRoll[gunId] = gl.rollMagRange(def); }
      return gl.fixMagRange(def, saved);
    }
    return def.wyrm ? gl.fixWyrm(def, saved) : null;
  };
  // the player level a new drop's roll uses (XP-based, 1-30)
  function playerLv() { return IB.Game && IB.Game.progress ? IB.Game.progress().level : 1; }
  /* display name: the model name (launchers with their element), dressed by the tier (core/gunskins.js: 'Cobalt Rivet') */
  WD.skinName = function (gunId, tierId, roll) {
    var def = IB.WEAPONS[gunId], base = GL() ? GL().displayName(def, roll) : def.name;
    return IB.GunSkinData ? IB.GunSkinData.name(gunId, WD.tier(tierId).id, base) : base;
  };
  WD.nameOf = function (gunId) { return WD.skinName(gunId, WD.tierOf(gunId).id, WD.rollOf(gunId)); };
  /* a gun taken (floor drop, armory rack). A model you do not own joins the arsenal and is carried at once when a
     loadout slot is free, otherwise it waits in the backpack. A model you already own is swapped: the new one takes
     its place (its attachments stay on) and the one you had comes back as `old` {id, tier, level, roll} for the caller
     to lay on the floor. Nothing is broken down. Returns {line, old, carried, key}. */
  WD.acquire = function (id, tierId, level, roll) {
    var G = IB.Game, s = G.slot, def = IB.WEAPONS[id], gl = GL(), line, old = null, carried = false, key = 0;
    s.gunTier = s.gunTier || {}; s.arsenal = s.arsenal || []; s.gunLevel = s.gunLevel || {}; s.gunRoll = s.gunRoll || {};
    var have = s.arsenal.indexOf(id) >= 0, nt = WD.tier(tierId), lv = Math.max(1, level || curLevel());
    var launcher = gl && gl.isLauncher(def); if (launcher) roll = gl.fixRoll(def, roll || gl.rollLauncher(def));
    var wyrm = gl && def.wyrm; if (wyrm) roll = gl.fixWyrm(def, roll || gl.wyrmRoll(def, playerLv()));
    var name = WD.skinName(id, nt.id, roll);
    if (have) old = { id: id, tier: WD.tierOf(id).id, level: WD.ownLevel(id), roll: s.gunRoll[id] || null };
    else { s.arsenal.push(id); s.owned = s.arsenal.slice(); }
    s.gunTier[id] = nt.id; s.gunLevel[id] = lv;
    if (roll) s.gunRoll[id] = roll; else delete s.gunRoll[id];
    var lo = (s.loadout || []).slice(), max = G.progress ? G.progress().loadoutMax : 2;
    if (!have && lo.indexOf(id) < 0 && lo.length < max) { lo.push(id); s.loadout = lo; carried = true; if (G.bank) delete G.bank[id]; }   // a fresh gun comes loaded
    key = lo.indexOf(id) + 1;
    if (G.ws && IB.Weapons && key > 0) {   // the carried guns follow at once (a swapped gun keeps its rounds, cut to its magazine)
      IB.Weapons.setLoadout(G.ws, lo, G.bank);
      if (IB.Gear) IB.Gear.refresh(G);
    }
    if (launcher && IB.Launchers) IB.Launchers.onAcquire(id, !have);
    if (old) line = 'Swapped for ' + name + ' · ' + nt.name + ' Lv ' + lv;
    else line = name + (carried ? ' · carried on key ' + key : ' · in your backpack (Tab)');
    return { line: line, old: old, carried: carried, key: key };
  };

  /* The gun beam: taller, wider and brighter than any gear beam, so a gun reads as a gun from across the zone.
     Layers, in the tier colour: a soft shaft of light that always faces you (darker toward its edges, so it reads on
     a white wall as well as in a dark hall), a bright core, ribbons of light winding up round it, a glowing floor
     disc, two ground rings (one breathing, one spreading out and fading) and sparks drifting up. Textures are drawn
     once and shared (also by the gear beams in game/drops.js); each drop owns only its materials (their colour). */
  var BEAM_H = 7.5;
  function tex(w, h, draw) { var t = IB.Render.canvasTex(w, h, draw); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t; }
  // a shaft of light seen from the side: soft across (bright middle, darker rim), bright at the foot, gone at the top
  function shaftTex(tight) {
    var t = IB.Render.canvasTex(64, 128, function (c) {
      c.clearRect(0, 0, 64, 128);
      for (var x = 0; x < 64; x++) {
        var u = (x + 0.5) / 32 - 1, a = Math.exp(-u * u * (tight ? 7 : 3.4)) * (1 - u * u), sh = Math.round(255 * (tight ? 1 : 0.5 + 0.5 * Math.exp(-u * u * 7)));
        var g = c.createLinearGradient(0, 0, 0, 128), col = sh + ',' + sh + ',' + sh;
        g.addColorStop(0, 'rgba(' + col + ',0)'); g.addColorStop(0.3, 'rgba(' + col + ',' + (a * 0.42).toFixed(3) + ')'); g.addColorStop(0.7, 'rgba(' + col + ',' + (a * 0.82).toFixed(3) + ')'); g.addColorStop(1, 'rgba(' + col + ',' + a.toFixed(3) + ')');
        c.fillStyle = g; c.fillRect(x, 0, 1, 128);
      }
    });
    return t;
  }
  function ribbonTex() {   // slanted ribbons of light that tile in both directions (they wind up the core as it scrolls)
    return tex(128, 128, function (c) {
      c.clearRect(0, 0, 128, 128);
      for (var k = 0; k < 3; k++) {
        var x0 = k * 128 / 3;
        for (var y = 0; y < 128; y++) {
          var u = (x0 + y * 0.5 + 6 * Math.sin(y / 128 * Math.PI * 2 + k)) % 128, wd = 6 + 3 * Math.sin(y / 128 * Math.PI * 4 + k * 2);
          for (var o = -128; o <= 128; o += 128) {
            if (u + o + wd < 0 || u + o - wd > 128) continue;
            var g = c.createLinearGradient(u + o - wd, 0, u + o + wd, 0);
            g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,255,255,0.95)'); g.addColorStop(1, 'rgba(255,255,255,0)');
            c.fillStyle = g; c.fillRect(u + o - wd, y, wd * 2, 1);
          }
        }
      }
    });
  }
  function fadeTex() {   // vertical fade used as the alpha of the ribbons (they die out toward the top)
    return tex(8, 128, function (c) {
      var g = c.createLinearGradient(0, 0, 0, 128);
      g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(0.45, 'rgba(110,110,110,1)'); g.addColorStop(1, 'rgba(255,255,255,1)');
      c.fillStyle = g; c.fillRect(0, 0, 8, 128);
    });
  }
  function discTex() {
    return IB.Render.canvasTex(128, 128, function (c) {
      var g = c.createRadialGradient(64, 64, 0, 64, 64, 64);
      g.addColorStop(0, 'rgba(255,255,255,0.95)'); g.addColorStop(0.3, 'rgba(255,255,255,0.5)'); g.addColorStop(0.65, 'rgba(255,255,255,0.16)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, 128, 128);
    });
  }
  function sparkTex() {
    return IB.Render.canvasTex(32, 32, function (c) {
      var g = c.createRadialGradient(16, 16, 0, 16, 16, 16);
      g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.3, 'rgba(255,255,255,0.7)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, 32, 32);
    });
  }
  // translucent, unlit, never fogged, drawn over the world without writing depth
  function glow(map, extra) {
    var o = { map: map, transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false };
    if (extra) for (var k in extra) o[k] = extra[k];
    return new THREE.MeshBasicMaterial(o);
  }
  WD.beamTextures = function () { return WD.tex || (WD.tex = { shaft: shaftTex(false), coreShaft: shaftTex(true), ribbon: ribbonTex(), fade: fadeTex(), disc: discTex(), spark: sparkTex() }); };
  WD.glowMaterial = glow;
  // turn a shaft plane (it stands on the drop, facing +z) toward the camera
  WD.faceCamera = function (mesh, x, z) { var c = IB.Render && IB.Render.camera; if (c) mesh.rotation.y = Math.atan2(c.position.x - x, c.position.z - z); };
  var SPARKS = 14;
  WD.init = function (scene) {
    WD.scene = scene;
    var T = WD.beamTextures();
    var haloGeo = new THREE.PlaneGeometry(2.1, BEAM_H); haloGeo.translate(0, BEAM_H / 2, 0);
    var hotGeo = new THREE.PlaneGeometry(0.62, BEAM_H * 0.92); hotGeo.translate(0, BEAM_H * 0.46, 0);
    var coreGeo = new THREE.CylinderGeometry(0.16, 0.3, BEAM_H * 0.8, 16, 1, true); coreGeo.translate(0, BEAM_H * 0.4, 0);
    var ringGeo = new THREE.RingGeometry(0.62, 0.8, 40), waveGeo = new THREE.RingGeometry(0.86, 0.96, 40), discGeo = new THREE.PlaneGeometry(3, 3);
    for (var i = 0; i < CAP; i++) {
      var grp = new THREE.Group(); grp.visible = false; scene.add(grp);
      var fx = new THREE.Group(); grp.add(fx);   // everything that glows (scaled as the drop pops in)
      var halo = new THREE.Mesh(haloGeo, glow(T.shaft, { opacity: 0.6 })); halo.renderOrder = 3; fx.add(halo);
      var hot = new THREE.Mesh(hotGeo, glow(T.coreShaft, { opacity: 0.9 })); hot.renderOrder = 4; fx.add(hot);
      var coreTex = T.ribbon.clone(); coreTex.needsUpdate = true; coreTex.repeat.set(2, 2.5);
      var core = new THREE.Mesh(coreGeo, glow(coreTex, { opacity: 0.7, alphaMap: T.fade })); core.renderOrder = 5; fx.add(core);
      var disc = new THREE.Mesh(discGeo, glow(T.disc, { opacity: 0.6 })); disc.rotation.x = -Math.PI / 2; disc.position.y = 0.04; disc.renderOrder = 2; fx.add(disc);
      var ring = new THREE.Mesh(ringGeo, glow(null, { opacity: 0.95 })); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.05; ring.renderOrder = 3; fx.add(ring);
      var wave = new THREE.Mesh(waveGeo, glow(null, { opacity: 0.6 })); wave.rotation.x = -Math.PI / 2; wave.position.y = 0.045; wave.renderOrder = 3; fx.add(wave);
      var sp = new Float32Array(SPARKS * 3), seed = [];
      for (var k = 0; k < SPARKS; k++) seed.push([Math.random() * Math.PI * 2, 0.18 + Math.random() * 0.5, Math.random(), 0.5 + Math.random() * 0.8]);
      var sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
      var sparks = new THREE.Points(sg, new THREE.PointsMaterial({ map: T.spark, size: 0.2, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.95, fog: false }));
      sparks.frustumCulled = false; sparks.renderOrder = 5; fx.add(sparks);
      var spin = new THREE.Group(); spin.position.y = 0.95; grp.add(spin);
      WD.list.push({ on: false, grp: grp, fx: fx, halo: halo, hot: hot, core: core, coreTex: coreTex, disc: disc, ring: ring, wave: wave, sparks: sparks, seed: seed,
        spin: spin, mesh: null, id: null, tier: null, melee: false, x: 0, z: 0, t: 0, level: 1, roll: null });
    }
  };
  WD.clear = function () { WD.list.forEach(function (d) { d.on = false; d.grp.visible = false; }); if (IB.HUD && IB.HUD.peek) IB.HUD.peek('drop', null); };

  // enemies that never drop guns or armour: the grey crawler and the exploding bomber
  var NO_GUN = { crawler: 1, bomber: 1 };
  WD.OTHER_GUN_CHANCE = 0.05;   // 2.5 % doubled, for every robot except soldiers' own table
  function def0(id) { return IB.WEAPONS && IB.WEAPONS[id]; }
  function G0() { return IB.Game; }
  var OUT_MAX = 0.006;   // ink outline cap for the turning gun (it is drawn 1.7x): it keeps its size at any distance
  function spawn(id, tier, x, z, melee, y, level, roll) {
    var A = IB.Assets, node = 'WPN_' + id.toUpperCase();
    if (!A.geo[node]) return null;
    var d = null; for (var i = 0; i < CAP; i++) if (!WD.list[i].on) { d = WD.list[i]; break; }
    if (!d) { d = WD.list[0]; for (i = 1; i < CAP; i++) if (WD.list[i].t > d.t) d = WD.list[i]; }
    if (d.mesh) d.spin.remove(d.mesh);
    if (!WD.mat) WD.mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0, outMax: OUT_MAX });
    d.mesh = new THREE.Mesh(G0() && G0().gunGeo && !melee ? G0().gunGeo(id) : A.get(node), !melee && IB.GunSkins ? IB.GunSkins.material(id, tier, null, OUT_MAX) : WD.mat);   // rarity skin, magazine in
    d.mesh.scale.setScalar(melee ? 1.5 : 1.7);
    if (melee) d.mesh.rotation.set(0, 0, 0.5); else d.mesh.rotation.set(0, 0, 0);
    d.spin.add(d.mesh);
    var floor = IB.Zones && IB.Zones.floorY ? IB.Zones.floorY(x, z, (y || 0) + 0.6) : 0;   // the floor (or deck) it fell on
    d.on = true; d.id = id; d.tier = tier; d.melee = !!melee; d.x = x; d.z = z; d.t = 0; d.y = floor;
    d.level = Math.max(1, level || curLevel()); d.roll = roll || null;
    if (!d.roll && !melee && IB.GunLevel && def0(id) && def0(id).wyrm) d.roll = IB.GunLevel.wyrmRoll(def0(id), playerLv());
    d.grp.position.set(x, floor, z); d.grp.visible = true; d.fx.scale.set(0.01, 0.01, 0.01);
    var c = new THREE.Color(melee ? '#FFC23A' : WD.tier(tier).color), hot = c.clone().lerp(new THREE.Color(0xffffff), 0.6);
    d.halo.material.color.copy(c); d.disc.material.color.copy(c); d.wave.material.color.copy(c); d.ring.material.color.copy(c);
    d.hot.material.color.copy(hot); d.core.material.color.copy(hot); d.sparks.material.color.copy(hot);
    // the rarer the gun, the taller and fuller its beam (a melee weapon gets the plain one)
    d.rank = melee ? 0 : WD.tier(tier).rank; d.tall = 0.72 + 0.07 * d.rank; d.wide = 0.9 + 0.06 * d.rank;
    if (IB.Audio) IB.Audio.play('pickup', { pos: { x: x, z: z }, pitch: 0.7, gain: 0.6 });
    return d;
  }

  // the guns that can drop on this level: every gun unlocked up to it (falls back to the arsenal)
  function pool() {
    var L = (IB.Game && IB.Game.plan && IB.Game.plan.level) || 1, out = [];
    (IB.ownedWeapons ? IB.ownedWeapons(L) : []).forEach(function (id) { if (IB.Weapons.playable(id)) out.push(id); });
    if (!out.length && slot() && slot().arsenal) out = slot().arsenal.slice();
    return out;
  }
  /* a soldier (or any robot whose row has weaponDrops) was wrecked by the player: maybe drop a gun */
  WD.roll = function (r, rng) {
    rng = rng || Math.random;
    var row = IB.ENEMIES && IB.ENEMIES[r.type], odds = row && row.weaponDrops;
    if (!odds) {   // every other robot: 5% per kill in total, split like the soldiers' gun drops (crawlers and bombers never)
      if (NO_GUN[r.type]) return null;
      var sold = IB.ENEMIES && IB.ENEMIES.soldier && IB.ENEMIES.soldier.weaponDrops || {}, tot = 0, k;
      Object.keys(sold).forEach(function (t) { tot += sold[t]; });
      odds = {}; Object.keys(sold).forEach(function (t) { odds[t] = tot ? sold[t] * WD.OTHER_GUN_CHANCE / tot : 0; });
    }
    var x = rng(), acc = 0, tier = null;
    for (var i = TIERS.length - 1; i >= 0; i--) { acc += odds[TIERS[i].id] || 0; if (x < acc) { tier = TIERS[i].id; break; } }
    if (!tier) return null;
    var p = pool(); if (!p.length) return null;
    return spawn(p[Math.floor(rng() * p.length)], tier, r.x, r.z, false, r.y, curLevel());
  };
  /* any player kill from campaign level 14 on: maybe a launcher (soldiers more often): RL-3 Hothead 60 %, ML-6 Murmur
     40 %, its tier from GunLevel.LAUNCHER_TIERS, magazine and element rolled now */
  WD.rollLauncher = function (r, rng) {
    rng = rng || Math.random;
    var gl = GL(); if (!gl) return null;
    if (rng() >= gl.launcherDropChance(r.type, curLevel())) return null;
    var id = rng() < 0.6 ? 'hothead' : 'murmur', def = IB.WEAPONS[id]; if (!def || !IB.Weapons.playable(id)) return null;
    return spawn(id, WD.rollTier(gl.LAUNCHER_TIERS, rng), r.x, r.z, false, r.y, curLevel(), gl.rollLauncher(def, rng));
  };
  WD.rollTier = function (w, rng) {
    var tot = 0, k; for (k in w) tot += w[k];
    var x = (rng || Math.random)() * tot; for (k in w) { x -= w[k]; if (x < 0) return k; }
    return 'gray';
  };
  /* a blade bot was wrecked: maybe drop the melee weapon it wields */
  WD.melee = function (r, id, rng) {
    rng = rng || Math.random;
    var row = IB.ENEMIES && IB.ENEMIES[r.type], ch = row && row.meleeDrop !== undefined ? row.meleeDrop : 0.07;
    if (!id || !IB.WEAPONS[id] || rng() >= ch) return null;
    var sl = slot(); if (sl && sl.melee && sl.melee.indexOf(id) >= 0) return null;   // you carry it already: nothing to take
    return spawn(id, 'gray', r.x, r.z, true, r.y);
  };

  /* E on a drop: a melee weapon goes on V; a gun is taken by WD.acquire (a swapped-out gun of yours lands where
     this one lay) */
  function take(d, G) {
    var s = G.slot, def = IB.WEAPONS[d.id], HUD = IB.HUD;
    if (!d.on || !s) return false;
    var x = d.x, z = d.z, y = d.y;
    d.on = false; d.grp.visible = false;
    if (d.melee) {
      s.melee = s.melee || [];
      if (s.melee.indexOf(d.id) < 0) s.melee.push(d.id);
      s.meleeSel = d.id;
      if (HUD.pickup) HUD.pickup(def.name, 'melee', 'V');
      if (HUD.toast) HUD.toast(def.name + ' · on V', 1.8);
    } else {
      var r = WD.acquire(d.id, d.tier, d.level, d.roll);
      if (r.old) spawn(r.old.id, r.old.tier, x, z, false, y, r.old.level, r.old.roll);
      if (HUD.toast) HUD.toast(r.line, 2.4);   // the gun in hand stays in hand: the new one waits on its key
    }
    if (IB.Audio) IB.Audio.play('pickup');
    if (IB.FX) IB.FX.puff(x, (y || 0) + 0.9, z, 10, parseInt((d.melee ? '#FFC23A' : WD.tier(d.tier).color).slice(1), 16), 0.14, 0.45, 3.5);
    if (G.store) G.store.save(s);
    return true;
  }
  WD.take = take;
  /* what E would do with drop d right now: {text, sub} for the prompt */
  function promptFor(d, G) {
    var s = G.slot, def = IB.WEAPONS[d.id];
    if (d.melee) return { text: 'Take ' + def.name, sub: 'Melee · goes on V' };
    var T = WD.tier(d.tier), name = WD.skinName(d.id, d.tier, d.roll), have = s && (s.arsenal || []).indexOf(d.id) >= 0;
    var lo = (s && s.loadout) || [], max = G.progress ? G.progress().loadoutMax : 2, sub;
    if (have) sub = 'Swap · your ' + WD.tierOf(d.id).name + ' Lv ' + WD.ownLevel(d.id) + ' stays here';
    else sub = lo.length < max ? 'Carried on key ' + (lo.length + 1) : 'Goes to your backpack';
    return { text: (have ? 'Swap for ' : 'Take ') + name, sub: T.name + ' · Lv ' + d.level + ' · ' + sub };
  }
  /* the drop E would take: the one you stand over, else the one you look at within reach. {d, text, sub, color, gun} */
  WD.useTarget = function (G) {
    var p = G.player, best = null, bs = -1;
    if (!p || !p.alive) return null;
    for (var i = 0; i < CAP; i++) {
      var q = WD.list[i]; if (!q.on || q.t < 0.35) continue;
      var dx = q.x - p.x, dz = q.z - p.z, dist = Math.hypot(dx, dz); if (dist > USE_R || Math.abs(p.y - q.y) > 1.6) continue;
      var face = dist > 0.01 ? (-Math.sin(p.yaw) * dx - Math.cos(p.yaw) * dz) / dist : 1;
      if (dist > CLOSE_R && face < 0.6) continue;
      var sc = (dist <= CLOSE_R ? 2 : face) - dist * 0.2; if (sc > bs) { bs = sc; best = q; }
    }
    if (!best) return null;
    var pr = promptFor(best, G);
    return { d: best, text: pr.text, sub: pr.sub, color: best.melee ? '#FFC23A' : WD.tier(best.tier).color,
      gun: { id: best.id, tier: best.tier, level: best.level, roll: best.roll, melee: best.melee, wx: best.x, wy: (best.y || 0) + 1.9, wz: best.z } };
  };

  WD.update = function (dt, t, G) {
    var p = G.player;
    if (IB.GunSkins) IB.GunSkins.tick(t);
    for (var i = 0; i < CAP; i++) {
      var d = WD.list[i]; if (!d.on) continue;
      d.t += dt;
      var pop = d.t < 0.22 ? d.t / 0.22 * 1.12 : d.t < 0.36 ? 1.12 - (d.t - 0.22) / 0.14 * 0.12 : 1;   // the beam shoots up, overshoots, settles
      d.fx.scale.set(Math.max(0.01, pop) * d.wide, Math.max(0.01, pop * pop) * d.tall, Math.max(0.01, pop) * d.wide);
      d.spin.rotation.y = t * 1.5 + i; d.spin.position.y = 0.95 + Math.sin(t * 2.2 + i) * 0.09;
      var br = 0.5 + 0.5 * Math.sin(t * 2.6 + i * 1.7);   // slow breath
      WD.faceCamera(d.halo, d.x, d.z); d.hot.rotation.y = d.halo.rotation.y;
      d.halo.material.opacity = 0.66 + 0.16 * br;
      d.hot.material.opacity = 0.78 + 0.18 * br;
      d.core.material.opacity = 0.55 + 0.25 * br;
      d.coreTex.offset.y = -(t * 0.42 + i * 0.13) % 1; d.coreTex.offset.x = (t * 0.11 + i * 0.3) % 1;   // ribbons climb and wind round
      d.core.rotation.y = t * 0.35 + i;
      d.disc.material.opacity = 0.5 + 0.22 * br; d.disc.scale.setScalar(0.9 + 0.12 * br);
      var k = 1 + 0.06 * br; d.ring.scale.set(k, k, k); d.ring.rotation.z = t * 0.5;
      var wv = (t * 0.55 + i * 0.37) % 1;   // a ring spreading out over the floor and fading
      d.wave.scale.setScalar(0.9 + wv * 1.5); d.wave.material.opacity = 0.6 * (1 - wv) * (1 - wv);
      var sp = d.sparks.geometry.attributes.position, sd = d.seed, top = BEAM_H * 0.8;
      for (var n = 0; n < sd.length; n++) {
        var ph = (sd[n][2] + t * 0.16 * sd[n][3]) % 1, ang = sd[n][0] + t * (0.5 + sd[n][3] * 0.5), rr = sd[n][1] * (1 - ph * 0.55);
        sp.setXYZ(n, Math.cos(ang) * rr, 0.15 + ph * top, Math.sin(ang) * rr);
      }
      sp.needsUpdate = true;
      d.sparks.material.opacity = 0.75 + 0.2 * br;
    }
    // weapon card for the drop you walk up to and look at (HUD peek panel; rebuilt only when the target changes)
    var best = null, bs = 0;
    if (p && p.alive) for (i = 0; i < CAP; i++) {
      var q = WD.list[i]; if (!q.on) continue;
      var dx = q.x - p.x, dz = q.z - p.z, dist = Math.hypot(dx, dz); if (dist > PEEK_R || Math.abs(p.y - q.y) > 2.5) continue;
      var face = dist > 0.01 ? (-Math.sin(p.yaw) * dx - Math.cos(p.yaw) * dz) / dist : 1; if (dist > CLOSE_R && face < 0.82) continue;
      var sc = (dist <= CLOSE_R ? 2 : face) - dist * 0.05; if (sc > bs) { bs = sc; best = q; }
    }
    WD.peeked = best;
    if (IB.HUD && IB.HUD.peek) IB.HUD.peek('drop', best ? { id: best.id, tier: best.tier, level: best.level, roll: best.roll, melee: best.melee, wx: best.x, wy: (best.y || 0) + 1.9, wz: best.z } : null);
  };
  WD.radar = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { x: d.x, z: d.z, kind: 'weapon' }; }); };
  WD.live = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { id: d.id, tier: d.tier, melee: d.melee, x: d.x, z: d.z, level: d.level, roll: d.roll }; }); };
  // the player drops a gun (Inventory): it lands at x, z with its tier, level and roll and leaves the arsenal (its
  // attachments go back to the bag, see Gear.refresh prune). The last carried gun cannot be dropped. Returns false if
  // the gun is not owned, is the only one carried, or has no model.
  WD.dropGun = function (id, x, z) {
    var G = IB.Game, s = G && G.slot, p = G && G.player;
    if (!s || !p || !s.arsenal || s.arsenal.indexOf(id) < 0) return false;
    var lo = s.loadout || [], at = lo.indexOf(id);
    if (at >= 0 && lo.length <= 1) return false;
    var d = spawn(id, WD.tierOf(id).id, x, z, false, p.y, WD.ownLevel(id), s.gunRoll ? s.gunRoll[id] : null);
    if (!d) return false;
    if (at >= 0) s.loadout = lo.filter(function (k) { return k !== id; });
    s.arsenal = s.arsenal.filter(function (k) { return k !== id; }); s.owned = s.arsenal.slice();
    if (s.gunTier) delete s.gunTier[id]; if (s.gunLevel) delete s.gunLevel[id]; if (s.gunRoll) delete s.gunRoll[id];
    if (G.bank) delete G.bank[id];
    return true;
  };
  // lay a gun {id, tier, level, roll} on the floor at x, z (a gun swapped out at an armory rack)
  WD.layDown = function (g, x, z, y) { return spawn(g.id, g.tier, x, z, false, y, g.level, g.roll); };
  // tests: put a drop right in front of the player (level / roll optional)
  WD.testDrop = function (id, tier, melee, level, roll) {
    var p = IB.Game.player, def = IB.WEAPONS[id], gl = GL();
    if (!roll && gl && gl.isLauncher(def)) roll = gl.rollLauncher(def);
    return !!spawn(id, tier || 'blue', p.x - Math.sin(p.yaw) * 2, p.z - Math.cos(p.yaw) * 2, !!melee, p.y, level, roll);
  };
})(window.IB = window.IB || {});
