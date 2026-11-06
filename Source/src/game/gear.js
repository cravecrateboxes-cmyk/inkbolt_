/* INKBOLT gear runtime: the loot inventory in play.
     Gear.refresh(G, fill)    weapon defs with attachments applied (stats), attachment meshes on the first-person
                              guns (MUZZLE socket: acid muzzle, SIGHT/SCOPE: scope, under the barrel: grip), ADS
                              through the scope's eye point, and the equipped shield (fill: start it full)
     Gear.absorb(G, dmg)      player damage hits the shield first; returns what goes through to health
     Gear.onHit(...)          bullet hit glue from game.js shoot(): damage number + acid DoT
     Gear.update(dt, G)       shield recharge, HUD shield bar, acid glass pulse
   Models come from fps-gear.glb (blender/fam_gear.py). */
(function (IB) {
  'use strict';
  var Gear = IB.Gear = { vm: {} };
  var L = function () { return IB.Loot; };
  if (IB.Assets && IB.Assets.BAKED) IB.Assets.BAKED.gear = 0.0035;   // attachments carry the viewmodel shell (fam_gear.py)

  // ---------------- sounds (synthesised into IB.Audio's buffers when audio starts) ----------------
  function synth(A) {
    var SR = A.ctx.sampleRate;
    function n(len) { var a = new Float32Array(len); for (var i = 0; i < len; i++) a[i] = Math.random() * 2 - 1; return a; }
    function len(s) { return Math.floor(s * SR); }
    function lp(a, fc) { var y = 0, k = 1 - Math.exp(-2 * Math.PI * fc / SR); for (var i = 0; i < a.length; i++) { y += k * (a[i] - y); a[i] = y; } return a; }
    function hp(a, fc) { var y = 0, x0 = 0, k = Math.exp(-2 * Math.PI * fc / SR); for (var i = 0; i < a.length; i++) { var x = a[i]; y = k * (y + x - x0); x0 = x; a[i] = y; } return a; }
    function env(a, at, dec, c) { var N = a.length, A0 = Math.max(1, at * SR); for (var i = 0; i < N; i++) a[i] *= i < A0 ? i / A0 : Math.pow(Math.max(0, 1 - (i - A0) / Math.max(1, dec * SR)), c || 2); return a; }
    function tone(N, f0, f1, sq) { var a = new Float32Array(N), ph = 0; for (var i = 0; i < N; i++) { ph += 2 * Math.PI * (f0 + (f1 - f0) * i / N) / SR; a[i] = sq ? (Math.sin(ph) > 0 ? 1 : -1) : Math.sin(ph); } return a; }
    function mix(d, s, g, off) { off = Math.floor((off || 0) * SR); for (var i = 0; i < s.length && i + off < d.length; i++) d[i + off] += s[i] * g; return d; }
    function norm(a, p) { var m = 0, i; for (i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i])); for (i = 0; i < a.length; i++) a[i] *= m ? p / m : 1; return a; }
    var R = {
      // shield takes a hit: glassy crackle over a soft thump
      shieldHit: function () { var o = new Float32Array(len(0.18)); mix(o, env(hp(n(len(0.12)), 3500), 0.001, 0.11, 2), 0.8); mix(o, env(tone(len(0.12), 900, 600), 0.001, 0.1, 2), 0.35); mix(o, env(lp(n(len(0.1)), 400), 0.001, 0.09, 2), 0.6); return norm(o, 0.5); },
      // shield breaks: falling zap + shatter
      shieldBreak: function () { var o = new Float32Array(len(0.5)); mix(o, env(tone(len(0.4), 1400, 180, true), 0.002, 0.4, 1.4), 0.25); lp(o, 2600); mix(o, env(hp(n(len(0.35)), 2500), 0.001, 0.32, 1.6), 0.9); for (var i = 0; i < 5; i++) mix(o, env(hp(n(len(0.02)), 5000), 0.0005, 0.018, 3), 0.5, 0.05 + i * 0.05); return norm(o, 0.6); },
      // recharge starts: rising hum
      shieldUp: function () { var o = new Float32Array(len(0.55)); var t = env(tone(len(0.5), 220, 880, true), 0.06, 0.48, 0.7); lp(t, 1800); mix(o, t, 0.4); mix(o, env(tone(len(0.5), 440, 1760), 0.06, 0.48, 0.8), 0.25); return norm(o, 0.32); },
      // topped up: two-note chime
      shieldFull: function () { var o = new Float32Array(len(0.35)); mix(o, env(tone(len(0.18), 1320, 1320), 0.002, 0.17, 3), 0.6); mix(o, env(tone(len(0.2), 1980, 1980), 0.002, 0.19, 3), 0.6, 0.09); return norm(o, 0.3); },
      // loot drops: thunk + sparkle; picked up: rising arpeggio
      lootDrop: function () { var o = new Float32Array(len(0.6)); mix(o, env(lp(n(len(0.12)), 500), 0.001, 0.11, 2), 0.9); mix(o, env(tone(len(0.1), 160, 80), 0.001, 0.1, 2), 0.6); [1568, 2093, 2637].forEach(function (f, i) { mix(o, env(tone(len(0.18), f, f), 0.002, 0.17, 3), 0.28, 0.12 + i * 0.07); }); return norm(o, 0.55); },
      loot: function () { var o = new Float32Array(len(0.5)); [784, 1175, 1568, 2349].forEach(function (f, i) { mix(o, env(tone(len(0.16), f, f), 0.002, 0.15, 3), 0.4, i * 0.055); }); mix(o, env(hp(n(len(0.3)), 6000), 0.01, 0.28, 2), 0.12); return norm(o, 0.45); },
      // DoT ticks
      zap: function () { var o = new Float32Array(len(0.09)); mix(o, env(hp(n(len(0.08)), 4000), 0.0005, 0.07, 2), 0.7); mix(o, env(tone(len(0.07), 2400, 900, true), 0.0005, 0.06, 2), 0.2); return norm(o, 0.25); },
      sizzle: function () { var o = new Float32Array(len(0.16)); var h = hp(n(len(0.15)), 5000); for (var i = 0; i < h.length; i++) h[i] *= 0.6 + 0.4 * Math.sin(i / SR * 2 * Math.PI * 47); mix(o, env(h, 0.01, 0.14, 1.5), 1); return norm(o, 0.2); }
    };
    Object.keys(R).forEach(function (k) { var d = R[k](), b = A.ctx.createBuffer(1, d.length, SR); b.getChannelData(0).set(d); A.bufs[k] = b; });
  }
  if (IB.Audio && !IB.Audio._gear) {
    var baseInit = IB.Audio.init;
    IB.Audio.init = function () { baseInit.apply(IB.Audio, arguments); if (IB.Audio.ctx && !IB.Audio.bufs.loot) { try { synth(IB.Audio); } catch (e) { /* audio is optional */ } } };
    IB.Audio._gear = true;
  }
  function play(n, o) { if (IB.Audio) IB.Audio.play(n, o); }
  Gear.play = play;

  // ---------------- init ----------------
  Gear.init = function () {
    var A = IB.Assets, R = IB.Render;
    if (!A.palette.gear) return;
    Gear.vmMat = R.toonMaterial({ uni: R.vmOutline, map: A.palette.gear, baked: A.BAKED.gear });
    Gear.glowMat = new THREE.MeshBasicMaterial({ color: 0x7BE34A });
    Gear.ready = true;
    if (IB.LootHUD) IB.LootHUD.ensure();
  };

  // ---------------- inventory access ----------------
  Gear.gear = function (G) {
    if (!G.slot) return null;
    if (!G.slot.gear || !G.slot._gearOk) { G.slot.gear = L().migrateGear(G.slot.gear); Object.defineProperty(G.slot, '_gearOk', { value: true, enumerable: false, configurable: true, writable: true }); }
    return G.slot.gear;
  };
  Gear.save = function (G) { if (G.store && G.slot) G.store.save(G.slot); };

  // ---------------- first-person attachments ----------------
  // per weapon: mount points in gun space, found once from its sockets and its mesh
  var _p = null;
  function mounts(m, id) {
    if (m.gearMounts) return m.gearMounts;
    var key = 'WPN_' + m.key, mesh = m.mesh;
    function sk(s) { var o = mesh.getObjectByName(key + s); return o ? o.position.clone() : null; }
    var muz = sk('_MUZZLE') || new THREE.Vector3(0, 0.03, -0.25), sight = sk('_SIGHT') || new THREE.Vector3(0, 0.08, 0.08), mag = sk('_MAG') || new THREE.Vector3(0, -0.04, -0.06);
    var pos = mesh.geometry.attributes.position, hull = mesh.geometry.attributes.aHull, n = pos.count, i, x, y, z;
    // scope: eye 3 cm ahead of the sight point, axis above everything under the tube (rear sight, reflex boxes)
    var zEye = sight.z - 0.03, top = sight.y - 0.02;
    // underside profile between the muzzle and the mag, 1 cm bins (barrel vs handguard)
    var z0 = muz.z, nb = Math.max(1, Math.ceil((mag.z - muz.z) / 0.01)), bins = [];
    for (i = 0; i < nb; i++) bins.push(Infinity);
    for (i = 0; i < n; i++) {
      if (hull && (hull.getX(i) !== 0 || hull.getY(i) !== 0 || hull.getZ(i) !== 0)) continue;
      x = pos.getX(i); y = pos.getY(i); z = pos.getZ(i);
      if (Math.abs(x) < 0.02 && z < zEye + 0.01 && z > zEye - 0.115 && y > top) top = y;
      if (Math.abs(x) < 0.014 && z >= z0 && z < mag.z && y < muz.y) { var b = Math.floor((z - z0) / 0.01); if (y < bins[b]) bins[b] = y; }
    }
    // grip: ~9.5 cm behind the muzzle (out past the support glove, so it reads), but never under a bare barrel:
    // it moves back to the first bin where a handguard reaches 1.6 cm below the bore; always 6 cm ahead of the mag
    var guard = -1;
    for (i = 0; i < nb; i++) if (bins[i] < muz.y - 0.016) { guard = i; break; }
    var zg = muz.z + 0.095;
    if (guard >= 0) zg = Math.max(zg, z0 + guard * 0.01 + 0.03);
    zg = Math.min(zg, mag.z - 0.06);
    var bot = Infinity, bg = Math.floor((zg - z0) / 0.01);
    for (i = Math.max(0, bg - 2); i <= Math.min(nb - 1, bg + 2); i++) bot = Math.min(bot, bins[i]);
    if (bot === Infinity) bot = muz.y - 0.025;
    var axis = Math.max(sight.y + 0.008, top + 0.0118 + 0.004);
    m.gearMounts = {
      muzzle: new THREE.Vector3(muz.x, muz.y, muz.z + 0.012),
      scope: new THREE.Vector3(sight.x, axis, zEye),
      sightZ: sight.z,
      grip: new THREE.Vector3(0, bot + 0.0015, zg)
    };
    return m.gearMounts;
  }
  Gear.mounts = function (id) { var m = IB.Weapons.models && IB.Weapons.models[id]; return m ? mounts(m, id) : null; };
  var MESH = { grip: 'GEAR_Grip', scope: 'GEAR_Scope', muzzle: 'GEAR_Acid' };
  var ADS_DIST = { pistol: 0.34, smg: 0.22, rifle: 0.17, sniper: 0.13 };   // weapons.js defaults
  function vmPart(m, slot) {
    m.gearParts = m.gearParts || {};
    if (m.gearParts[slot]) return m.gearParts[slot];
    var A = IB.Assets, mesh = new THREE.Mesh(A.get(MESH[slot]), Gear.vmMat);
    mesh.frustumCulled = false; mesh.name = 'VM_' + MESH[slot];
    if (slot === 'muzzle') {
      var glow = new THREE.Mesh(A.get('GEAR_Acid_Glow'), Gear.glowMat); glow.frustumCulled = false; mesh.add(glow);
      var tip = new THREE.Object3D(); tip.position.copy(A.node.GEAR_Acid_TIP.position); tip.scale.setScalar(0.6); tip.name = 'VM_ACID_TIP'; mesh.add(tip);
      mesh.userData.tip = tip;
    }
    mesh.position.copy(mounts(m)[slot]);
    m.mesh.add(mesh);
    m.gearParts[slot] = mesh;
    return mesh;
  }
  /* show the attachment meshes for weapon id (items by slot), move the muzzle flash and the ADS eye point */
  function dressViewmodel(id, items, isCur) {
    var W = IB.Weapons, m = W.models && W.models[id];
    if (!m || !Gear.ready) return;
    IB.LOOT.slots.forEach(function (sl) {
      var on = !!items[sl];
      if (on) vmPart(m, sl).visible = true;
      else if (m.gearParts && m.gearParts[sl]) m.gearParts[sl].visible = false;
    });
    // muzzle flash rides the acid can's tip
    if (!m.muzzle0) m.muzzle0 = m.muzzle || null;
    var want = items.muzzle ? m.gearParts.muzzle.userData.tip : m.muzzle0;
    if (want && m.muzzle !== want) { m.muzzle = want; if (isCur && W.flash) want.add(W.flash); }
    // ADS: the scope's eye point replaces the gun's sight point
    if (items.scope) { var eye = IB.Assets.node.GEAR_Scope_EYE ? IB.Assets.node.GEAR_Scope_EYE.position : new THREE.Vector3(); m.sight = m.gearParts.scope.position.clone().add(eye); m.sightScoped = true; }
    else if (m.sightScoped) { m.sight = null; m.sightScoped = false; }
  }
  Gear.dressViewmodel = dressViewmodel;

  // ---------------- refresh: stats + viewmodel + shield ----------------
  Gear.refresh = function (G, fill) {
    var g = Gear.gear(G); if (!g || !G.ws) return;
    var owned = Object.keys(G.ws.guns);
    L().prune(g, owned);
    owned.forEach(function (id) {
      var gun = G.ws.guns[id], items = L().weaponItems(g, id);
      gun.def = L().applyMods(IB.WEAPONS[id], items);
      // ADS keeps the camera where the iron sights put it (the eye point is further forward), so the arms never clip
      if (items.scope) { var mt = Gear.mounts(id); gun.def.adsDist = (ADS_DIST[gun.def.cls] || 0.25) + (mt ? (mt.sightZ - mt.scope.z) * 0.85 : 0); }
      dressViewmodel(id, items, G.ws.cur === id);
    });
    var p = G.player, it = g.shield ? L().find(g, g.shield) : null;
    if (!it) { p.shield = null; }
    else if (!p.shield || p.shield.id !== it.id || fill) {
      var st = L().shieldState(it); st.id = it.id;
      if (p.shield && p.shield.id === it.id && !fill) st.cur = Math.min(st.max, p.shield.cur);
      p.shield = st;
    }
    if (IB.LootHUD) IB.LootHUD.shield(p.shield);
  };
  Gear.startLevel = function (G) { if (IB.LootHUD) IB.LootHUD.reset(); Gear.refresh(G, true); };
  Gear.fillShield = function (G) { var s = G.player && G.player.shield; if (s) { s.cur = s.max; s.since = 99; s.charging = false; } };

  // ---------------- damage in / out ----------------
  Gear.absorb = function (G, dmg) {
    var p = G.player, st = p.shield; if (!st) return dmg;
    var r = L().absorb(st, dmg);
    if (r.absorbed > 0) {
      play(r.broke ? 'shieldBreak' : 'shieldHit', { gain: 0.9 });
      if (IB.LootHUD) IB.LootHUD.shieldHit(r.broke);
    }
    return r.through;
  };
  /* res: IB.Damage.hit result; zone 'core'|'body'; killed: AI.damage returned true */
  Gear.onHit = function (r, res, zone, def, killed) {
    var v = IB.AI.VIS[r.type], top = r.y + (v ? v.y1 : 0.9) + 0.22;
    if (IB.FX.damageNumber) IB.FX.damageNumber(r.x, top, r.z, res.damage, res.crit ? 'crit' : zone === 'core' ? 'core' : 'hit');
    if (!killed && def.acid > 0 && IB.Status) IB.Status.apply(r, 'acid', res.damage * def.acid / def.acidDur, def.acidDur);
  };

  // ---------------- per frame ----------------
  Gear.update = function (dt, G) {
    var p = G.player, st = p && p.shield;
    if (st && p.alive) {
      var ev = L().tickShield(st, dt);
      if (ev === 'start') play('shieldUp', { gain: 0.7 });
      else if (ev === 'full') play('shieldFull', { gain: 0.6 });
      if (ev && IB.LootHUD) IB.LootHUD.shieldEvent(ev);
    }
    if (IB.LootHUD) { IB.LootHUD.shield(st); IB.LootHUD.tick(dt); }
    // a mounted scope: past ~70 % aim the comic scope view fades in and the viewmodel steps aside
    var w = G.ws && IB.Weapons.current(G.ws), k = w && w.def.optic && p.alive ? Math.max(0, Math.min(1, (G.ws.aim - 0.7) / 0.22)) : 0;
    if (IB.LootHUD) IB.LootHUD.scope(k);
    if (G.ws) G.ws.hidden = k >= 0.98;
    if (Gear.glowMat) { var k = 0.5 + 0.5 * Math.sin(performance.now() * 0.006); Gear.glowMat.color.setRGB(0.48 + 0.3 * k, 0.89 + 0.1 * k, 0.29 + 0.25 * k); }
  };

  // ---------------- test hooks (merged into window.__TEST__ by game.js) ----------------
  IB.GearTest = {
    // force a world drop in front of the player: type 'shield'|'grip'|'scope'|'acid', rarity, distance (m)
    forceDrop: function (type, rarity, dist) {
      var G = IB.Game, p = G.player, d = dist === undefined ? 4 : dist;
      var item = L().makeItem(type || 'grip', rarity || 'rare', G.plan.level, Math.random);
      return IB.Drops.spawn(item, p.x - Math.sin(p.yaw) * d, p.z - Math.cos(p.yaw) * d) ? item : null;
    },
    drops: function () { return IB.Drops.list(); },
    gearState: function () {
      var G = IB.Game, g = Gear.gear(G), p = G.player, w = IB.Weapons.current(G.ws);
      return { inv: g ? g.inv.map(function (i) { return { id: i.id, type: i.type, rarity: i.rarity, name: i.name }; }) : [], shield: g && g.shield, attach: g ? JSON.parse(JSON.stringify(g.attach)) : {},
        playerShield: p.shield ? { cur: p.shield.cur, max: p.shield.max } : null, health: p.health,
        weapon: w ? { id: w.id, recoil: w.def.recoil, spreadHip: w.def.spreadHip, spreadAim: w.def.spreadAim, aimZoom: w.def.aimZoom, acid: w.def.acid || 0, baseRecoil: IB.WEAPONS[w.id].recoil, baseAimZoom: IB.WEAPONS[w.id].aimZoom } : null,
        vm: w && IB.Weapons.models[w.id] && IB.Weapons.models[w.id].gearParts ? Object.keys(IB.Weapons.models[w.id].gearParts).filter(function (k) { return IB.Weapons.models[w.id].gearParts[k].visible; }) : [],
        numbers: IB.FX.numbersList ? IB.FX.numbersList() : [], statuses: IB.Status ? IB.Status.active() : 0 };
    },
    attach: function (id, wid) { var G = IB.Game, g = Gear.gear(G); wid = wid || G.ws.cur; var ok = L().attach(g, wid, IB.WEAPONS[wid], id); Gear.refresh(G); Gear.save(G); return ok; },
    equipShield: function (id) { var G = IB.Game, ok = L().equipShield(Gear.gear(G), id); Gear.refresh(G, true); Gear.save(G); return ok; },
    gear: function () { IB.GearUI.open(IB.Game); },
    status: function (kind, dps, dur) { var r = IB.AI.robots.find(function (x) { return x.on && x.state !== 'pose' && x.state !== 'spawn'; }); return r ? !!IB.Status.apply(r, kind, dps, dur) : false; }
  };
})(window.IB = window.IB || {});
