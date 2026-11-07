/* INKBOLT weapon drops: guns of a quality tier (gray, green, blue, purple, orange) and melee weapons dropped by robots.
   Enemy rows carry the odds (src/data/enemies.js): weaponDrops {gray, green, blue, purple, orange} (soldiers),
   meleeDrop (blade bots drop the katana or the Voltaxe they wield). ai.js / game.js call IB.WeaponDrops.roll(r) /
   IB.WeaponDrops.melee(r, id) on a player kill.
   A dropped gun is one of the guns unlocked up to this level, lying in a beam of its tier colour (and on the radar).
   Walking over it: a gun you do not own joins the arsenal at that tier; a better tier than yours upgrades your gun;
   anything else is broken down into gems. Tiers multiply the gun's damage (TIERS[].dmg, game.js shoot / meleeHit) and
   are saved per gun in slot.gunTier.
     IB.WeaponDrops.init(scene) / clear() / update(dt, t, G) / radar() / tierOf(id) / dmgMul(id) */
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
  WD.dmgMul = function (gunId) { return WD.tierOf(gunId).dmg; };

  WD.init = function (scene) {
    WD.scene = scene;
    var ringGeo = new THREE.RingGeometry(0.5, 0.68, 28), beamGeo = new THREE.CylinderGeometry(0.16, 0.3, 3.2, 10, 1, true);
    for (var i = 0; i < CAP; i++) {
      var grp = new THREE.Group(); grp.visible = false; scene.add(grp);
      var ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.85, depthWrite: false })); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.03; grp.add(ring);
      var beam = new THREE.Mesh(beamGeo, new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.28, depthWrite: false, side: THREE.DoubleSide })); beam.position.y = 1.6; grp.add(beam);
      var spin = new THREE.Group(); spin.position.y = 0.7; grp.add(spin);
      WD.list.push({ on: false, grp: grp, ring: ring, beam: beam, spin: spin, mesh: null, id: null, tier: null, melee: false, x: 0, z: 0, t: 0 });
    }
  };
  WD.clear = function () { WD.list.forEach(function (d) { d.on = false; d.grp.visible = false; }); };

  function spawn(id, tier, x, z, melee, y) {
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
    return spawn(p[Math.floor(rng() * p.length)], tier, r.x, r.z, false, r.y);
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
      s.gunTier = s.gunTier || {}; s.arsenal = s.arsenal || [];
      var have = s.arsenal.indexOf(d.id) >= 0, cur = WD.tierOf(d.id), nt = WD.tier(d.tier);
      if (!have) { s.arsenal.push(d.id); s.owned = s.arsenal.slice(); s.gunTier[d.id] = nt.id; line = nt.name + ' ' + def.name + ' · in your backpack (Tab)'; }
      else if (nt.rank > cur.rank) { s.gunTier[d.id] = nt.id; line = def.name + ' upgraded to ' + nt.name + ' (x' + nt.dmg.toFixed(2) + ' damage)'; }
      else { s.gems = (s.gems || 0) + nt.gems; line = nt.name + ' ' + def.name + ' · broken down for ' + nt.gems + ' gems'; }
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
  WD.live = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { id: d.id, tier: d.tier, melee: d.melee, x: d.x, z: d.z }; }); };
  // tests: put a drop right in front of the player
  WD.testDrop = function (id, tier, melee) { var p = IB.Game.player; return !!spawn(id, tier || 'blue', p.x - Math.sin(p.yaw) * 2, p.z - Math.cos(p.yaw) * 2, !!melee, p.y); };
})(window.IB = window.IB || {});
