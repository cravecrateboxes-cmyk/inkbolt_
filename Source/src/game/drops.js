/* INKBOLT world loot drops: a drop pod (fps-gear LOOT_Capsule) with a rarity-coloured light ring, ground rings and a
   beam of light, the item model turning above it. Walking over it puts the item in the bag (slot.gear) with a HUD card;
   an empty shield / vest slot or attachment slot on the current gun is filled automatically. Walking up to one and
   looking at it shows its item card floating over it (Drops.peekTarget -> HUD.peek, the same card as in the backpack).
   Drops show on the radar. The beam is a soft column of light with wisps flowing up it, a glowing floor disc and motes
   drifting up; it grows taller, wider and brighter with the rarity (Legendary: orange, tallest). A gun's beam
   (game/wdrops.js) is about twice as tall and wide again, so guns and gear never look alike.
     Drops.onKill(robot)       roll the 5 % drop for a player kill (IB.Loot.rollDrop: rarity odds by campaign level)
     Drops.spawn(item, x, z)   place a drop
     Drops.update(dt, t, G)    animation + pickup
     Drops.peekTarget(G)       the drop whose card shows: {item, uid, wx, wy, wz} or null
   Pooled: LOOT.maxWorld drops (the oldest is recycled). */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var D = IB.Drops = { pool: [], ready: false, uid: 0 };
  // fallback meshes per type (IB.Loot.modelOf picks the rarity's own model: shield cells have four)
  var ITEM_MESH = { shield: 'GEAR_ShieldCell', grip: 'GEAR_Grip', scope: 'GEAR_Scope', acid: 'GEAR_Acid', shock: 'GEAR_Shock', blast: 'GEAR_Blast', void: 'GEAR_Void', mag: 'GEAR_Mag', armor: 'GEAR_Vest' };
  // beam per rarity: [brightness, height, width, motes]: the rarer, the taller, fuller and brighter
  var BEAM = { common: [0.55, 0.78, 0.9, 4], rare: [0.72, 1.0, 1, 6], epic: [0.86, 1.2, 1.1, 8], legendary: [1, 1.45, 1.25, 10] };
  var BEAM_H = 3.1, MOTES = 10, PEEK_R = 6, CLOSE_R = 1.6;
  var _tmp = [];

  // wisps of light: soft slanted streaks that tile both ways; scrolled up the beam they read as light flowing
  function wispTexture() {
    var t = IB.Render.canvasTex(128, 128, function (c) {
      c.clearRect(0, 0, 128, 128);
      for (var k = 0; k < 4; k++) {
        var x0 = k * 32 + 9, amp = 9 + (k % 2) * 6, wd0 = 5 + (k % 3) * 2;
        for (var y = 0; y < 128; y++) {
          var ph = y / 128 * Math.PI * 2, u = x0 + amp * Math.sin(ph + k * 1.7), wd = wd0 + 2.5 * Math.sin(ph * 2 + k), al = 0.5 + 0.4 * Math.sin(ph + k * 2.3);
          for (var o = -128; o <= 128; o += 128) {
            if (u + o + wd < 0 || u + o - wd > 128) continue;
            var g = c.createLinearGradient(u + o - wd, 0, u + o + wd, 0);
            g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,255,255,' + al.toFixed(3) + ')'); g.addColorStop(1, 'rgba(255,255,255,0)');
            c.fillStyle = g; c.fillRect(u + o - wd, y, wd * 2, 1);
          }
        }
      }
    });
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return t;
  }
  function gradTexture(stops) {   // a vertical gradient (v = 0 at the foot): [[v, value 0..1]]
    var t = IB.Render.canvasTex(8, 128, function (c) {
      var g = c.createLinearGradient(0, 128, 0, 0);
      stops.forEach(function (st) { var v = Math.round(st[1] * 255); g.addColorStop(st[0], 'rgb(' + v + ',' + v + ',' + v + ')'); });
      c.fillStyle = g; c.fillRect(0, 0, 8, 128);
    });
    return t;
  }
  function discTexture() {
    return IB.Render.canvasTex(64, 64, function (c) {
      var g = c.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.3, 'rgba(255,255,255,0.5)'); g.addColorStop(0.65, 'rgba(255,255,255,0.14)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, 64, 64);
    });
  }
  function glow(o) {
    var m = { transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false };
    for (var k in o) m[k] = o[k];
    return new THREE.MeshBasicMaterial(m);
  }

  D.init = function (scene) {
    var A = IB.Assets;
    if (!A.geo.LOOT_Capsule) return;
    D.scene = scene;
    // gear models are drawn enlarged on a pod (and on armory shelves): cap their ink outline, so a drop across the
    // zone keeps its real size instead of swelling into a black blob (IB.Render.toonMaterial outMax)
    if (A.mat.gear && A.mat.gear.userData.outMax) A.mat.gear.userData.outMax.value = 0.0225;
    var WDb = IB.WeaponDrops && IB.WeaponDrops.beamTextures ? IB.WeaponDrops.beamTextures() : null;
    var wisp = D.wispTex = wispTexture(), fade = gradTexture([[0, 1], [0.5, 0.45], [1, 0]]), disc = discTexture();
    var haloGeo = new THREE.PlaneGeometry(0.8, BEAM_H); haloGeo.translate(0, BEAM_H / 2 + 0.2, 0);
    var coreGeo = new THREE.CylinderGeometry(0.1, 0.19, BEAM_H * 0.86, 14, 1, true); coreGeo.translate(0, BEAM_H * 0.43 + 0.2, 0);
    var ringGeo = new THREE.RingGeometry(0.42, 0.56, 6, 1); ringGeo.rotateX(-Math.PI / 2); ringGeo.rotateY(Math.PI / 6);
    var waveGeo = new THREE.RingGeometry(0.6, 0.66, 32, 1); waveGeo.rotateX(-Math.PI / 2);
    var discGeo = new THREE.PlaneGeometry(2.1, 2.1); discGeo.rotateX(-Math.PI / 2);
    var spark = WDb ? WDb.spark : disc, shaft = WDb ? WDb.shaft : null;
    D.addSlot = function (i) {
      var grp = new THREE.Group(); grp.visible = false;
      var cap = new THREE.Mesh(A.get('LOOT_Capsule'), A.mat.gear); grp.add(cap);
      var glowMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      var glowM = new THREE.Mesh(A.get('LOOT_Glow'), glowMat); grp.add(glowM);
      var fx = new THREE.Group(); grp.add(fx);
      var haloMat = glow({ map: shaft, opacity: 0.5 }), halo = new THREE.Mesh(haloGeo, haloMat); halo.renderOrder = 3; fx.add(halo);
      var wtex = wisp.clone(); wtex.needsUpdate = true; wtex.repeat.set(2, 1.6);
      var beamMat = glow({ map: wtex, alphaMap: fade, opacity: 0.8 }), beam = new THREE.Mesh(coreGeo, beamMat); beam.renderOrder = 4; fx.add(beam);
      var discMat = glow({ map: disc, opacity: 0.5 }), dsc = new THREE.Mesh(discGeo, discMat); dsc.position.y = 0.03; dsc.renderOrder = 2; fx.add(dsc);
      var ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, depthWrite: false });
      var ring = new THREE.Mesh(ringGeo, ringMat); ring.position.y = 0.025; ring.renderOrder = 2; grp.add(ring);
      var waveMat = glow({ opacity: 0.5 }), wave = new THREE.Mesh(waveGeo, waveMat); wave.position.y = 0.03; wave.renderOrder = 2; fx.add(wave);
      var mp = new Float32Array(MOTES * 3), seed = [];
      for (var k = 0; k < MOTES; k++) seed.push([Math.random() * Math.PI * 2, 0.12 + Math.random() * 0.3, Math.random(), 0.6 + Math.random() * 0.7]);
      var mg = new THREE.BufferGeometry(); mg.setAttribute('position', new THREE.BufferAttribute(mp, 3));
      var motes = new THREE.Points(mg, new THREE.PointsMaterial({ map: spark, size: 0.13, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.9, fog: false }));
      motes.frustumCulled = false; motes.renderOrder = 5; fx.add(motes);
      var spin = new THREE.Group(); spin.position.y = 0.62; grp.add(spin);
      var item = new THREE.Mesh(A.get('GEAR_Grip'), A.mat.gear); spin.add(item);
      var glass = new THREE.Mesh(A.get('GEAR_Acid_Glow'), IB.Gear && IB.Gear.glowMat ? IB.Gear.glowMat : new THREE.MeshBasicMaterial({ color: 0x7BE34A })); glass.visible = false; item.add(glass);
      scene.add(grp);
      D.pool.push({ on: false, grp: grp, fx: fx, glow: glowMat, halo: halo, haloMat: haloMat, beam: beam, beamMat: beamMat, wtex: wtex, discMat: discMat, disc: dsc,
        ring: ring, ringMat: ringMat, wave: wave, waveMat: waveMat, motes: motes, seed: seed, spin: spin, item: item, glass: glass,
        it: null, x: 0, z: 0, t: 0, born: 0, fullT: 0, uid: 0, bright: 1, nm: MOTES });
    };
    for (var i0 = 0; i0 < IB.LOOT.maxWorld; i0++) D.addSlot(i0);
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

  /* y (optional): a height hint (the robot that dropped it, the player): the pod lands on the floor or deck under it */
  D.spawn = function (item, x, z, y) {
    if (!D.ready || !item) return null;
    var G = IB.Game, d = null, i;
    for (i = 0; i < D.pool.length; i++) if (!D.pool[i].on) { d = D.pool[i]; break; }
    // pool full: one more slot. Loot on the ground is never removed; it stays until the player takes it or leaves
    if (!d) { D.addSlot(D.pool.length); d = D.pool[D.pool.length - 1]; }
    var pos = freeSpot(x, z, G);
    d.on = true; d.dropped = false; d.it = item; d.x = pos[0]; d.z = pos[1]; d.t = 0; d.born = performance.now(); d.fullT = 0; d.uid = ++D.uid;
    d.y = typeof y === 'number' && IB.Zones && IB.Zones.floorY ? Math.max(0, IB.Zones.floorY(d.x, d.z, y + 0.6)) : 0;
    var rc = IB.LOOT.rarityById[item.rarity], col = new THREE.Color(rc.color), hot = col.clone().lerp(new THREE.Color(0xffffff), 0.4);
    d.glow.color.copy(col); d.ringMat.color.copy(col); d.haloMat.color.copy(col); d.discMat.color.copy(col); d.waveMat.color.copy(col);
    d.beamMat.color.copy(hot); d.motes.material.color.copy(hot);
    var bs = BEAM[item.rarity] || BEAM.common;
    d.bright = bs[0]; d.nm = bs[3];
    d.fx.scale.set(bs[2], bs[1], bs[2]);
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
    d.grp.position.set(d.x, d.y, d.z); d.grp.scale.setScalar(0.01); d.grp.visible = true;
    if (IB.FX) { IB.FX.puff(d.x, d.y + 0.4, d.z, 8, rc.color === '#E4DFD3' ? PAL.paper : parseInt(rc.color.slice(1), 16), 0.15, 0.5, 3); IB.FX.puff(d.x, d.y + 0.2, d.z, 4, PAL.ink, 0.2, 0.5, 2); }
    if (IB.Gear) IB.Gear.play('lootDrop', { pos: { x: d.x, z: d.z } });
    return d;
  };

  // grey crawlers and exploding bombers never drop armour; every other robot can, at double the armour rate
  var NO_ARMOUR = { crawler: 1, bomber: 1 };
  D.onKill = function (r) {
    var G = IB.Game; if (!D.ready || !G.slot || !G.plan) return null;
    var ctx = { level: G.plan.level, cleared: G.slot.highest || 0 }, armour = !NO_ARMOUR[r.type];
    if (!armour) ctx.exclude = ['armor'];
    var item = IB.Loot.rollDrop(Math.random, ctx), out = item ? D.spawn(item, r.x, r.z, r.y) : null;
    if (armour) {   // the armour vest's share of the drop table, rolled once more: double the armour rate
      var types = IB.Loot.allowedTypes(ctx), tot = 0, w = 0;
      types.forEach(function (t) { tot += t.weight || 0; if (t.id === 'armor') w = t.weight || 0; });
      if (tot > 0 && Math.random() < IB.LOOT.dropChance * (w / tot)) {
        var extra = IB.Loot.makeItem('armor', IB.Loot.rollRarity(Math.random, G.plan.level), G.plan.level, Math.random);
        D.spawn(extra, r.x, r.z, r.y);
      }
    }
    return out;
  };

  function collect(d, G) {
    var g = IB.Gear.gear(G), item = d.it;
    if (!g) return false;
    if (!IB.Loot.addItem(g, item, IB.Gear.bagCap(G))) {
      if (d.fullT <= 0) { d.fullT = 3; IB.HUD.toast('Bag full (' + g.inv.length + '/' + IB.Gear.bagCap(G) + ') · drop or scrap gear in the Inventory (Tab)', 2.4, 'note'); }
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
    if (IB.LootHUD) IB.LootHUD.loot(item, note); else IB.HUD.toast(item.name, 2, 'tick:gear');
    IB.Gear.play('loot');
    var col = parseInt(IB.LOOT.rarityById[item.rarity].color.slice(1), 16);
    IB.FX.puff(d.x, (d.y || 0) + 0.7, d.z, 10, col, 0.12, 0.4, 3.5);
    d.on = false; d.grp.visible = false;
    return true;
  }
  D.collect = collect;

  D.update = function (dt, t, G) {
    if (!D.ready) return;
    var p = G.player, R = IB.LOOT.pickupRadius;
    for (var i = 0; i < D.pool.length; i++) {
      var d = D.pool[i]; if (!d.on) continue;
      d.t += dt; d.fullT -= dt;
      var k = d.t < 0.18 ? d.t / 0.18 * 1.15 : d.t < 0.3 ? 1.15 - (d.t - 0.18) / 0.12 * 0.15 : 1;
      d.grp.scale.setScalar(Math.max(0.01, k));
      d.spin.rotation.y = t * 1.6 + i;
      d.spin.position.y = 0.66 + Math.sin(t * 2.6 + i) * 0.05;
      var pulse = 0.5 + 0.5 * Math.sin(t * 4 + i), br = 0.5 + 0.5 * Math.sin(t * 2.2 + i * 1.3), B = d.bright;
      d.ring.scale.setScalar(1 + pulse * 0.08);
      d.ringMat.opacity = 0.55 + pulse * 0.4;
      // the light flows: wisps climb the beam and drift round it, the halo and the floor glow breathe slowly
      d.wtex.offset.y = -(t * 0.34 + i * 0.21) % 1; d.wtex.offset.x = (t * 0.07 + i * 0.4) % 1;
      d.beam.rotation.y = -t * 0.3 + i;
      if (IB.WeaponDrops && IB.WeaponDrops.faceCamera) IB.WeaponDrops.faceCamera(d.halo, d.x, d.z);
      d.beamMat.opacity = B * (0.6 + 0.25 * br);
      d.haloMat.opacity = B * (0.42 + 0.14 * br);
      d.discMat.opacity = B * (0.4 + 0.18 * br); d.disc.scale.setScalar(0.92 + 0.1 * br);
      var wv = (t * 0.5 + i * 0.29) % 1;
      d.wave.scale.setScalar(0.85 + wv * 1.2); d.waveMat.opacity = B * 0.55 * (1 - wv) * (1 - wv);
      var mp = d.motes.geometry.attributes.position, sd = d.seed, top = BEAM_H * 0.85;
      for (var n = 0; n < sd.length; n++) {
        if (n >= d.nm) { mp.setXYZ(n, 0, -50, 0); continue; }   // fewer motes on the plainer rarities
        var ph = (sd[n][2] + t * 0.2 * sd[n][3]) % 1, ang = sd[n][0] + t * (0.6 + sd[n][3] * 0.6), rr = sd[n][1] * (1 - ph * 0.5);
        mp.setXYZ(n, Math.cos(ang) * rr, 0.25 + ph * top, Math.sin(ang) * rr);
      }
      mp.needsUpdate = true;
      if (IB.FX) IB.FX.blob(d.x, d.y, d.z, 0.42);
      var near = Math.hypot(p.x - d.x, p.z - d.z) < R;
      if (d.dropped) { if (!near) d.dropped = false; }   // dropped by the player: taken again only after stepping away
      else if (p.alive && d.t > IB.LOOT.armTime && Math.abs(p.y - d.y) < 1.2 && near) collect(d, G);
    }
  };
  /* the drop whose item card shows: the nearest one you look at within PEEK_R (or stand next to). Returned as the
     HUD.peek spec {item, uid, wx, wy, wz}; null when there is none. */
  D.peekTarget = function (G) {
    if (!D.ready) return null;
    var p = G.player, best = null, bs = 0;
    if (!p || !p.alive) return null;
    for (var i = 0; i < D.pool.length; i++) {
      var d = D.pool[i]; if (!d.on || d.t < 0.3) continue;
      var dx = d.x - p.x, dz = d.z - p.z, dist = Math.hypot(dx, dz); if (dist > PEEK_R || Math.abs(p.y - d.y) > 2.5) continue;
      var face = dist > 0.01 ? (-Math.sin(p.yaw) * dx - Math.cos(p.yaw) * dz) / dist : 1; if (dist > CLOSE_R && face < 0.86) continue;
      var sc = (dist <= CLOSE_R ? 2 : face) - dist * 0.05; if (sc > bs) { bs = sc; best = d; }
    }
    return best ? { item: best.it, uid: 'drop' + best.uid, wx: best.x, wy: (best.y || 0) + 1.35, wz: best.z } : null;
  };
})(window.IB = window.IB || {});
