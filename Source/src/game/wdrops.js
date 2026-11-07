/* INKBOLT weapon drops: guns of a quality tier (gray, green, blue, purple, orange) and melee weapons dropped by robots.
   Enemy rows carry the odds (src/data/enemies.js): weaponDrops {gray, green, blue, purple, orange} (soldiers),
   meleeDrop (blade bots drop the katana or the Voltaxe they wield). ai.js / game.js call IB.WeaponDrops.roll(r) /
   IB.WeaponDrops.melee(r, id) on a player kill.
   A dropped gun is one of the guns unlocked up to this level, lying in a beam of its tier colour (and on the radar).
   Every drop also has an item level (the campaign level it dropped on; core/gunlevel.js), shown on a label over the
   beam. Walking over it: a gun you do not own joins the arsenal at that tier and level; a better one than yours
   (tier x level, see IB.GunLevel.score) replaces your gun; anything else is broken down into gems (tier value).
   Tier x level multiply the gun's damage (dmgMul: game.js shoot / meleeHit, launchers.js) and are saved per gun in
   slot.gunTier / slot.gunLevel (launchers also their rolled magazine and element in slot.gunRoll).
   From campaign level 14 a kill may also drop a launcher (rollLauncher; IB.GunLevel.launcherDropChance).
     IB.WeaponDrops.init(scene) / clear() / update(dt, t, G) / radar() / tierOf(id) / levelOf(id) / dmgMul(id) /
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
  var CAP = 6, R = 1.3;

  function slot() { return IB.Game && IB.Game.slot; }
  WD.tierOf = function (gunId) { var s = slot(); return WD.tier(s && s.gunTier && s.gunTier[gunId]); };
  function GL() { return IB.GunLevel; }
  function playerLv() { var s = slot(); return IB.Skills && IB.Skills.gained ? IB.Skills.playerLevel(s ? IB.Skills.gained(s) : 0) : 1; }
  function curLevel() { return (IB.Game && IB.Game.plan && IB.Game.plan.level) || 1; }
  /* the level a gun fights at (its own, or player level - 4); melee weapons have none and ride the floor */
  WD.ownLevel = function (gunId) { var s = slot(); return (s && s.gunLevel && s.gunLevel[gunId]) || 1; };
  WD.levelOf = function (gunId) { return GL() ? GL().effective(WD.ownLevel(gunId), playerLv(), curLevel()) : 1; };
  WD.dmgMul = function (gunId) { return WD.tierOf(gunId).dmg * (GL() ? GL().mul(WD.levelOf(gunId)) : 1); };
  WD.rollOf = function (gunId) { var s = slot(), def = IB.WEAPONS[gunId]; return def && GL() && GL().isLauncher(def) ? GL().fixRoll(def, s && s.gunRoll && s.gunRoll[gunId]) : null; };
  WD.nameOf = function (gunId) { var def = IB.WEAPONS[gunId]; return GL() ? GL().displayName(def, WD.rollOf(gunId)) : def.name; };
  /* a gun picked up (drop, armory rack): joins the arsenal, replaces yours if better, else gems. Returns the line. */
  WD.acquire = function (id, tierId, level, roll) {
    var G = IB.Game, s = G.slot, def = IB.WEAPONS[id], gl = GL(), line;
    s.gunTier = s.gunTier || {}; s.arsenal = s.arsenal || []; s.gunLevel = s.gunLevel || {}; s.gunRoll = s.gunRoll || {};
    var have = s.arsenal.indexOf(id) >= 0, nt = WD.tier(tierId), lv = Math.max(1, level || curLevel());
    var launcher = gl && gl.isLauncher(def); if (launcher) roll = gl.fixRoll(def, roll || gl.rollLauncher(def));
    var name = gl ? gl.displayName(def, roll) : def.name, tag = nt.name + ' Lv ' + lv;
    if (!have) {
      s.arsenal.push(id); s.owned = s.arsenal.slice(); s.gunTier[id] = nt.id; s.gunLevel[id] = lv; if (launcher) s.gunRoll[id] = roll;
      line = tag + ' ' + name + ' · in your backpack (Tab)';
      if (launcher && IB.Launchers) IB.Launchers.onAcquire(id, true);
    } else {
      var cur = WD.tierOf(id), now = gl ? gl.score(def, cur.dmg, WD.levelOf(id), WD.rollOf(id)) : cur.dmg, nw = gl ? gl.score(def, nt.dmg, lv, roll) : nt.dmg;
      if (nw > now * 1.0001) {
        s.gunTier[id] = nt.id; s.gunLevel[id] = lv; if (launcher) s.gunRoll[id] = roll;
        line = name + ' upgraded to ' + tag + ' (x' + (nw / now).toFixed(2) + ' power)';
        if (launcher && IB.Launchers) IB.Launchers.onAcquire(id, false);
      } else { s.gems = (s.gems || 0) + nt.gems; line = tag + ' ' + name + ' · broken down for ' + nt.gems + ' gems'; }
    }
    return line;
  };

  WD.init = function (scene) {
    WD.scene = scene;
    var ringGeo = new THREE.RingGeometry(0.5, 0.68, 28), beamGeo = new THREE.CylinderGeometry(0.16, 0.3, 3.2, 10, 1, true);
    for (var i = 0; i < CAP; i++) {
      var grp = new THREE.Group(); grp.visible = false; scene.add(grp);
      var ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.85, depthWrite: false })); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.03; grp.add(ring);
      var beam = new THREE.Mesh(beamGeo, new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.28, depthWrite: false, side: THREE.DoubleSide })); beam.position.y = 1.6; grp.add(beam);
      var spin = new THREE.Group(); spin.position.y = 0.7; grp.add(spin);
      // label over the beam: "Lv 14 · Rare" and the gun's name (a canvas per drop, redrawn when it spawns)
      var cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
      var tex = new THREE.CanvasTexture(cv), label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
      label.scale.set(1.7, 0.425, 1); label.position.y = 2.15; label.renderOrder = 5; grp.add(label);
      WD.list.push({ on: false, grp: grp, ring: ring, beam: beam, spin: spin, mesh: null, id: null, tier: null, melee: false, x: 0, z: 0, t: 0, label: label, cv: cv, tex: tex, level: 1, roll: null });
    }
  };
  WD.clear = function () { WD.list.forEach(function (d) { d.on = false; d.grp.visible = false; }); };

  function drawLabel(d) {
    var c = d.cv.getContext('2d'), def = IB.WEAPONS[d.id], T = WD.tier(d.tier), col = d.melee ? '#FFC23A' : T.color;
    var name = d.melee ? def.name : (GL() ? GL().displayName(def, d.roll) : def.name);
    c.clearRect(0, 0, 256, 64);
    c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.font = '700 22px "Barlow Condensed", "Archivo", sans-serif';
    var top = d.melee ? 'Melee' : 'Lv ' + d.level + ' · ' + T.name;
    c.lineWidth = 6; c.strokeStyle = '#15121C'; c.strokeText(top, 128, 18); c.fillStyle = col; c.fillText(top, 128, 18);
    c.font = '700 24px "Barlow Condensed", "Archivo", sans-serif';
    c.strokeText(name.toUpperCase(), 128, 45); c.fillStyle = '#FFFDF7'; c.fillText(name.toUpperCase(), 128, 45);
    d.tex.needsUpdate = true;
  }
  function spawn(id, tier, x, z, melee, y, level, roll) {
    var A = IB.Assets, node = 'WPN_' + id.toUpperCase();
    if (!A.geo[node]) return null;
    var d = null; for (var i = 0; i < CAP; i++) if (!WD.list[i].on) { d = WD.list[i]; break; }
    if (!d) { d = WD.list[0]; for (i = 1; i < CAP; i++) if (WD.list[i].t > d.t) d = WD.list[i]; }
    if (d.mesh) d.spin.remove(d.mesh);
    if (!WD.mat) WD.mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0 });
    d.mesh = new THREE.Mesh(A.get(node), WD.mat); d.mesh.scale.setScalar(melee ? 1.5 : 1.7);
    if (melee) d.mesh.rotation.set(0, 0, 0.5); else d.mesh.rotation.set(0, 0, 0);
    d.spin.add(d.mesh);
    var floor = IB.Zones && IB.Zones.floorY ? IB.Zones.floorY(x, z, (y || 0) + 0.6) : 0;   // the floor (or deck) it fell on
    d.on = true; d.id = id; d.tier = tier; d.melee = !!melee; d.x = x; d.z = z; d.t = 0; d.y = floor;
    d.level = Math.max(1, level || curLevel()); d.roll = roll || null;
    if (d.label) drawLabel(d);
    d.grp.position.set(x, floor, z); d.grp.visible = true;
    var c = new THREE.Color(melee ? '#FFC23A' : WD.tier(tier).color);
    d.ring.material.color.copy(c); d.beam.material.color.copy(c);
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
    var row = IB.ENEMIES && IB.ENEMIES[r.type], odds = row && row.weaponDrops; if (!odds) return null;
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
    return spawn(id, 'gray', r.x, r.z, true, r.y);
  };

  function take(d, G) {
    var s = G.slot, def = IB.WEAPONS[d.id], HUD = IB.HUD, line;
    d.on = false; d.grp.visible = false;
    if (d.melee) {
      s.melee = s.melee || [];
      if (s.melee.indexOf(d.id) < 0) { s.melee.push(d.id); s.meleeSel = d.id; line = 'New melee · on V'; }
      else { s.gems = (s.gems || 0) + 40; line = 'Already owned · +40 gems'; }
      if (HUD.pickup) HUD.pickup(def.name, 'melee', 'V');
      if (HUD.toast) HUD.toast(line, 1.6);
    } else {
      line = WD.acquire(d.id, d.tier, d.level, d.roll);
      if (HUD.toast) HUD.toast(line, 2.4);
      if (HUD.gems) HUD.gems(s.gems || 0, true);
    }
    if (IB.Audio) IB.Audio.play('pickup');
    if (G.store) G.store.save(s);
  }

  WD.update = function (dt, t, G) {
    var p = G.player;
    for (var i = 0; i < CAP; i++) {
      var d = WD.list[i]; if (!d.on) continue;
      d.t += dt;
      d.spin.rotation.y = t * 1.6 + i; d.spin.position.y = 0.7 + Math.sin(t * 2.4 + i) * 0.08;
      var k = 1 + Math.sin(t * 4 + i) * 0.08; d.ring.scale.set(k, k, k);
      d.beam.material.opacity = 0.2 + 0.1 * Math.sin(t * 3 + i);
      if (p && p.alive && d.t > 0.6 && Math.hypot(p.x - d.x, p.z - d.z) < R && Math.abs(p.y - d.y) < 1.2) take(d, G);
    }
  };
  WD.radar = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { x: d.x, z: d.z, kind: 'weapon' }; }); };
  WD.live = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { id: d.id, tier: d.tier, melee: d.melee, x: d.x, z: d.z, level: d.level, roll: d.roll }; }); };
  // tests: put a drop right in front of the player (level / roll optional)
  WD.testDrop = function (id, tier, melee, level, roll) {
    var p = IB.Game.player, def = IB.WEAPONS[id], gl = GL();
    if (!roll && gl && gl.isLauncher(def)) roll = gl.rollLauncher(def);
    return !!spawn(id, tier || 'blue', p.x - Math.sin(p.yaw) * 2, p.z - Math.cos(p.yaw) * 2, !!melee, p.y, level, roll);
  };
})(window.IB = window.IB || {});
