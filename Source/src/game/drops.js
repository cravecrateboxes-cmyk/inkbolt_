/* INKBOLT world loot drops: a drop pod (fps-gear LOOT_Capsule) with a rarity-coloured light ring, ground ring and
   beam, the item model turning above it. Walking over it puts the item in the bag (slot.gear) with a HUD card;
   an empty shield / vest slot or attachment slot on the current gun is filled automatically. Drops show on the radar;
   the beam grows taller and brighter with the rarity (Legendary: orange, tallest).
     Drops.onKill(robot)       roll the 5 % drop for a player kill (IB.Loot.rollDrop: rarity odds by campaign level)
     Drops.spawn(item, x, z)   place a drop
     Drops.update(dt, t, G)    animation + pickup
   Pooled: LOOT.maxWorld drops (the oldest is recycled). */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var D = IB.Drops = { pool: [], ready: false };
  // fallback meshes per type (IB.Loot.modelOf picks the rarity's own model: shield cells have four)
  var ITEM_MESH = { shield: 'GEAR_ShieldCell', grip: 'GEAR_Grip', scope: 'GEAR_Scope', acid: 'GEAR_Acid', mag: 'GEAR_Mag', armor: 'GEAR_Vest' };
  // beam per rarity: [opacity, height, width]: the rarer, the taller and brighter
  var BEAM = { common: [0.42, 0.8, 1], rare: [0.58, 1.05, 1], epic: [0.7, 1.25, 1.1], legendary: [0.82, 1.55, 1.3] };
  var _tmp = [];

  function beamTexture() {
    return IB.Render.canvasTex(32, 128, function (ctx) {
      var g = ctx.createLinearGradient(0, 0, 0, 128);
      g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.55, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,1)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, 32, 128);
      // comic speed bands
      ctx.globalCompositeOperation = 'destination-out';
      for (var y = 6; y < 128; y += 22) { ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(0, y, 32, 7); }
    });
  }

  D.init = function (scene) {
    var A = IB.Assets;
    if (!A.geo.LOOT_Capsule) return;
    D.scene = scene;
    var tex = beamTexture();
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    D.beamTex = tex;
    var beamGeo = new THREE.CylinderGeometry(0.13, 0.17, 2.6, 14, 1, true); beamGeo.translate(0, 1.5, 0);
    var ringGeo = new THREE.RingGeometry(0.42, 0.56, 6, 1); ringGeo.rotateX(-Math.PI / 2); ringGeo.rotateY(Math.PI / 6);
    for (var i = 0; i < IB.LOOT.maxWorld; i++) {
      var grp = new THREE.Group(); grp.visible = false;
      var cap = new THREE.Mesh(A.get('LOOT_Capsule'), A.mat.gear); grp.add(cap);
      var glowMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      var glow = new THREE.Mesh(A.get('LOOT_Glow'), glowMat); grp.add(glow);
      var beamMat = new THREE.MeshBasicMaterial({ color: 0xffffff, map: tex, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide, fog: true });
      var beam = new THREE.Mesh(beamGeo, beamMat); beam.renderOrder = 3; grp.add(beam);
      var ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, depthWrite: false });
      var ring = new THREE.Mesh(ringGeo, ringMat); ring.position.y = 0.025; ring.renderOrder = 2; grp.add(ring);
      var spin = new THREE.Group(); spin.position.y = 0.62; grp.add(spin);
      var item = new THREE.Mesh(A.get('GEAR_Grip'), A.mat.gear); spin.add(item);
      var glass = new THREE.Mesh(A.get('GEAR_Acid_Glow'), IB.Gear && IB.Gear.glowMat ? IB.Gear.glowMat : new THREE.MeshBasicMaterial({ color: 0x7BE34A })); glass.visible = false; item.add(glass);
      scene.add(grp);
      D.pool.push({ on: false, grp: grp, glow: glowMat, beam: beam, beamMat: beamMat, ring: ring, ringMat: ringMat, spin: spin, item: item, glass: glass,
        it: null, x: 0, z: 0, t: 0, born: 0, fullT: 0 });
    }
    D.ready = true;
  };
  D.clear = function () { D.pool.forEach(function (d) { d.on = false; d.grp.visible = false; d.it = null; }); };
  D.list = function () { return D.pool.filter(function (d) { return d.on; }).map(function (d) { return { x: d.x, z: d.z, type: d.it.type, rarity: d.it.rarity, name: d.it.name }; }); };
  D.radar = function () {
    var out = [];
    for (var i = 0; i < D.pool.length; i++) { var d = D.pool[i]; if (d.on) out.push({ x: d.x, z: d.z, kind: 'loot', color: IB.LOOT.rarityById[d.it.rarity].color }); }
    return out;
  };

  // drops never land inside a box (drones die over crates): nudge toward the player until the spot is clear
  function freeSpot(x, z, G) {
    var w = G.level && G.level.world, p = G.player;
    if (!w) return [x, z];
    function blocked(px, pz) {
      w.query(px - 0.35, pz - 0.35, px + 0.35, pz + 0.35, _tmp);
      for (var i = 0; i < _tmp.length; i++) { var b = _tmp[i]; if (b.y0 < 0.6 && b.y1 > 0.15) return true; }
      return false;
    }
    if (!blocked(x, z)) return [x, z];
    var dx = p.x - x, dz = p.z - z, dl = Math.hypot(dx, dz) || 1;
    for (var s = 0.4; s <= 4; s += 0.4) { var nx = x + dx / dl * s, nz = z + dz / dl * s; if (!blocked(nx, nz)) return [nx, nz]; }
    return [x, z];
  }

  D.spawn = function (item, x, z) {
    if (!D.ready || !item) return null;
    var G = IB.Game, d = null, i;
    for (i = 0; i < D.pool.length; i++) if (!D.pool[i].on) { d = D.pool[i]; break; }
    if (!d) { d = D.pool[0]; for (i = 1; i < D.pool.length; i++) if (D.pool[i].born < d.born) d = D.pool[i]; }
    var pos = freeSpot(x, z, G);
    d.on = true; d.it = item; d.x = pos[0]; d.z = pos[1]; d.t = 0; d.born = performance.now(); d.fullT = 0;
    var rc = IB.LOOT.rarityById[item.rarity], col = new THREE.Color(rc.color);
    d.glow.color.copy(col); d.beamMat.color.copy(col); d.ringMat.color.copy(col);
    var bs = BEAM[item.rarity] || BEAM.common;
    d.beamMat.opacity = bs[0];
    d.beam.scale.set(bs[2], bs[1], bs[2]);
    var A = IB.Assets, node = IB.Loot.modelOf(item);
    var geo = A.get(node && A.geo[node] ? node : ITEM_MESH[item.type]);
    d.item.geometry = geo;
    if (!geo.boundingBox) geo.computeBoundingBox();
    var bb = geo.boundingBox, c = new THREE.Vector3(); bb.getCenter(c);
    var sz = new THREE.Vector3(); bb.getSize(sz);
    var k = item.type === 'shield' || item.type === 'armor' ? 2.6 : item.type === 'mag' ? 2.8 : 2.4;
    d.item.scale.setScalar(k);
    d.item.position.set(-c.x * k, -c.y * k, -c.z * k);
    // long attachments lie along the turn axis a bit tilted so their side profile reads
    d.item.rotation.set(item.type === 'grip' ? 0 : 0, 0, 0);
    d.spin.rotation.set(item.type === 'scope' || item.type === 'acid' ? 0.35 : 0, 0, item.type === 'scope' || item.type === 'acid' ? 0.25 : 0);
    d.glass.visible = item.type === 'acid';
    d.grp.position.set(d.x, 0, d.z); d.grp.scale.setScalar(0.01); d.grp.visible = true;
    if (IB.FX) { IB.FX.puff(d.x, 0.4, d.z, 8, rc.color === '#E4DFD3' ? PAL.paper : parseInt(rc.color.slice(1), 16), 0.15, 0.5, 3); IB.FX.puff(d.x, 0.2, d.z, 4, PAL.ink, 0.2, 0.5, 2); }
    if (IB.Gear) IB.Gear.play('lootDrop', { pos: { x: d.x, z: d.z } });
    return d;
  };

  D.onKill = function (r) {
    var G = IB.Game; if (!D.ready || !G.slot || !G.plan) return null;
    var item = IB.Loot.rollDrop(Math.random, { level: G.plan.level, cleared: G.slot.highest || 0 });
    return item ? D.spawn(item, r.x, r.z) : null;
  };

  function collect(d, G) {
    var g = IB.Gear.gear(G), item = d.it;
    if (!g) return false;
    if (!IB.Loot.addItem(g, item)) {
      if (d.fullT <= 0) { d.fullT = 3; IB.HUD.toast('Bag full · discard gear in the Gear tab', 2); }
      return false;
    }
    // fill an empty slot right away: shield, or a compatible attachment slot on the gun in hand
    var note = 'In your bag';
    var worn = IB.Loot.isWorn(item) ? IB.Loot.slotOf(item) : null;
    if (worn && !g[worn]) { IB.Loot.equipWorn(g, worn, item.id); note = worn === 'shield' ? 'Shield equipped' : 'Vest equipped'; }
    else if (IB.Loot.isAttachment(item) && G.ws && G.ws.cur) {
      var wid = G.ws.cur, def = IB.WEAPONS[wid], sl = IB.Loot.slotOf(item);
      if (IB.Loot.compatible(item, wid, def) && !IB.Loot.weaponItems(g, wid)[sl]) { IB.Loot.attach(g, wid, def, item.id); note = 'Fitted to ' + def.name; }
    }
    IB.Gear.refresh(G, item.type === 'shield' && g.shield === item.id);
    IB.Gear.save(G);
    if (IB.LootHUD) IB.LootHUD.loot(item, note); else IB.HUD.toast(item.name, 2);
    IB.Gear.play('loot');
    var col = parseInt(IB.LOOT.rarityById[item.rarity].color.slice(1), 16);
    IB.FX.puff(d.x, 0.7, d.z, 10, col, 0.12, 0.4, 3.5);
    d.on = false; d.grp.visible = false;
    return true;
  }
  D.collect = collect;

  D.update = function (dt, t, G) {
    if (!D.ready) return;
    var p = G.player, R = IB.LOOT.pickupRadius;
    if (D.beamTex) D.beamTex.offset.y = (t * 0.6) % 1;
    for (var i = 0; i < D.pool.length; i++) {
      var d = D.pool[i]; if (!d.on) continue;
      d.t += dt; d.fullT -= dt;
      var k = d.t < 0.18 ? d.t / 0.18 * 1.15 : d.t < 0.3 ? 1.15 - (d.t - 0.18) / 0.12 * 0.15 : 1;
      d.grp.scale.setScalar(Math.max(0.01, k));
      d.spin.rotation.y = t * 1.6 + i;
      d.spin.position.y = 0.66 + Math.sin(t * 2.6 + i) * 0.05;
      var pulse = 0.5 + 0.5 * Math.sin(t * 4 + i);
      d.ring.scale.setScalar(1 + pulse * 0.08);
      d.ringMat.opacity = 0.55 + pulse * 0.4;
      if (IB.FX) IB.FX.blob(d.x, 0, d.z, 0.42);
      if (p.alive && d.t > IB.LOOT.armTime && p.y < 1.2 && Math.hypot(p.x - d.x, p.z - d.z) < R) collect(d, G);
    }
  };
})(window.IB = window.IB || {});
