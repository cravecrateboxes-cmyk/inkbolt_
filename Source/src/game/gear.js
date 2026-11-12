/* INKBOLT gear runtime: the loot inventory in play.
     Gear.refresh(G, fill)    weapon defs with attachments applied (stats), attachment meshes on the first-person
                              guns (MUZZLE socket: acid muzzle, SIGHT/SCOPE: scope, under the barrel: grip), ADS
                              through the scope's eye point, under the magazine: extended mag), the equipped shield
                              (fill: start it full) and the worn vest's extra max health
     Gear.absorb(G, dmg)      player damage hits the shield first, the vest cuts what goes on; returns what reaches
                              health (an armed Nova cell that breaks queues its shock burst)
     Gear.onHit(...)          bullet hit glue from game.js shoot(): damage number + acid DoT
     Gear.onKill(G, r)        a player kill: Overcharge cells start recharging at once, faster
     Gear.vestHp(G)           the worn vest's extra max health (game.js adds it in applySkillStats)
     Gear.update(dt, G)       shield recharge, Nova burst, HUD shield bar, acid glass pulse
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
      // Nova: a fat electric whump (low sweep + crackle); Overcharge: a quick rising zing
      shieldNova: function () { var o = new Float32Array(len(0.7)); var t = env(tone(len(0.6), 900, 70, true), 0.002, 0.6, 1.3); lp(t, 2200); mix(o, t, 0.5); mix(o, env(lp(n(len(0.4)), 300), 0.001, 0.38, 1.6), 0.9); mix(o, env(hp(n(len(0.5)), 3000), 0.002, 0.48, 1.8), 0.6); for (var i = 0; i < 6; i++) mix(o, env(hp(n(len(0.02)), 4500), 0.0005, 0.018, 3), 0.45, 0.04 + i * 0.07); return norm(o, 0.7); },
      overcharge: function () { var o = new Float32Array(len(0.4)); mix(o, env(tone(len(0.32), 330, 1320, true), 0.01, 0.3, 1.2), 0.3); lp(o, 2600); mix(o, env(tone(len(0.3), 660, 2640), 0.01, 0.28, 1.4), 0.3); return norm(o, 0.32); },
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
    if (IB.GunSkins && IB.GunSkins.tactical) IB.GunSkins.tactical(Gear.vmMat);   // attachments shade like the guns they sit on
    Gear.glowMat = new THREE.MeshBasicMaterial({ color: 0x7BE34A });
    Gear.glowMats = { acid: Gear.glowMat };
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
  // bag size right now: grows with the player level (IB.Loot.bagCap: 16 at LV 1 to 40 at LV 20)
  Gear.bagCap = function (G) { var lv = G && G.progress ? G.progress().level : 1; return L().bagCap ? L().bagCap(lv) : IB.LOOT.invCap; };

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
  /* extended mag: where it rides on the gun's own magazine mesh (mag-local): the magazine's base plate, i.e. its biggest
     downward face near the bottom (raked pistol mags and curved rifle mags lean, so its normal gives the axis), the
     plate's centre and its footprint (x width, depth across the axis) */
  var MAG_W = 0.026, MAG_D = 0.036;   // GEAR_Mag's inner footprint (fam_gear.py build_mag)
  function magMount(m) {
    if (m.magMount !== undefined) return m.magMount;
    m.magMount = null;
    var mg = m.mag, geo = mg && mg.geometry; if (!geo || !geo.index) return null;
    var pos = geo.attributes.position, hull = geo.attributes.aHull, idx = geo.index, i;
    function solid(i) { return !hull || (hull.getX(i) === 0 && hull.getY(i) === 0 && hull.getZ(i) === 0); }
    function P(i) { return new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i)); }
    var y0 = Infinity, pts = [];
    for (i = 0; i < pos.count; i++) if (solid(i)) { var p = P(i); pts.push(p); y0 = Math.min(y0, p.y); }
    if (pts.length < 8) return null;
    // downward faces within 2 cm of the lowest point, merged by normal: the largest group is the base plate
    var groups = [], e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), nrm = new THREE.Vector3();
    for (i = 0; i < idx.count; i += 3) {
      var a = idx.getX(i), b = idx.getX(i + 1), c = idx.getX(i + 2);
      if (!solid(a) || !solid(b) || !solid(c)) continue;
      var A = P(a), B = P(b), C = P(c);
      nrm.crossVectors(e1.subVectors(B, A), e2.subVectors(C, A));
      var area = nrm.length() / 2; if (area < 1e-7) continue;
      nrm.normalize();
      if (nrm.y > -0.6 || Math.abs(nrm.x) > 0.3 || Math.min(A.y, B.y, C.y) > y0 + 0.02) continue;
      var gr = null;
      for (var k = 0; k < groups.length; k++) if (groups[k].n.dot(nrm) > 0.995) { gr = groups[k]; break; }
      if (!gr) { gr = { n: nrm.clone(), area: 0 }; groups.push(gr); }
      gr.area += area;
    }
    if (!groups.length) return null;
    groups.sort(function (p, q) { return q.area - p.area; });
    var axis = groups[0].n.clone().negate(); axis.x = 0; axis.normalize();
    var wv = new THREE.Vector3(0, -axis.z, axis.y);   // depth direction, square to the axis and to x
    var tmin = Infinity;
    pts.forEach(function (p) { tmin = Math.min(tmin, p.dot(axis)); });
    var x0 = Infinity, x1 = -Infinity, s0 = Infinity, s1 = -Infinity;
    pts.forEach(function (p) { if (p.dot(axis) < tmin + 0.003) { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); var s = p.dot(wv); s0 = Math.min(s0, s); s1 = Math.max(s1, s); } });
    var w = x1 - x0, d = s1 - s0;
    m.magMount = { pos: new THREE.Vector3((x0 + x1) / 2, 0, 0).addScaledVector(wv, (s0 + s1) / 2).addScaledVector(axis, tmin),
      quat: new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), axis),
      scale: new THREE.Vector3(Math.max(0.5, w / MAG_W), Math.max(0.7, Math.min(1.05, (w / MAG_W + d / MAG_D) / 2)), Math.max(0.5, d / MAG_D)) };
    return m.magMount;
  }
  var MESH = { grip: 'GEAR_Grip', scope: 'GEAR_Scope', muzzle: 'GEAR_Acid', mag: 'GEAR_Mag' };
  var MAG_VISUAL = { pistol: true, smg: true, rifle: true, sniper: true };   // shotgun tubes / cylinders: stats only
  var ADS_DIST = { pistol: 0.34, smg: 0.22, rifle: 0.17, sniper: 0.13 };   // weapons.js defaults
  // muzzle cans: one model per can type (acid, Arc, Boom, Void), each with its glowing glass core and TIP socket
  var _cg = new THREE.Color();
  var CAN_MESH = { acid: 'GEAR_Acid', shock: 'GEAR_Shock', blast: 'GEAR_Blast', void: 'GEAR_Void' };
  var CAN_GLOW = { acid: [0x7BE34A, 0xC8FF8A], shock: [0x3FB4FF, 0xBDF0FF], blast: [0xFF7A1E, 0xFFD27A], void: [0x9A5BFF, 0xE0C8FF] };
  function vmPart(m, slot, type) {
    m.gearParts = m.gearParts || {};
    var key = slot === 'muzzle' ? 'muzzle.' + (type || 'acid') : slot;
    if (m.gearParts[key] !== undefined) return m.gearParts[key];
    var A = IB.Assets, node = slot === 'muzzle' ? CAN_MESH[type] || MESH.muzzle : MESH[slot];
    if (!node || !A.geo[node]) { m.gearParts[key] = null; return null; }
    var mesh = new THREE.Mesh(A.get(node), Gear.vmMat);
    mesh.frustumCulled = false; mesh.name = 'VM_' + node;
    if (slot === 'muzzle') {
      var gm = Gear.glowMats[type] || (Gear.glowMats[type] = new THREE.MeshBasicMaterial({ color: (CAN_GLOW[type] || CAN_GLOW.acid)[0] }));
      var glow = new THREE.Mesh(A.get(node + '_Glow'), gm); glow.frustumCulled = false; mesh.add(glow);
      var tip = new THREE.Object3D(); tip.position.copy(A.node[node + '_TIP'].position); tip.scale.setScalar(0.6); tip.name = 'VM_CAN_TIP'; mesh.add(tip);
      mesh.userData.tip = tip;
    }
    if (slot === 'mag') {
      // rides the magazine (so it drops out and comes back with it on a reload)
      var mm = magMount(m), def = IB.WEAPONS[m.id];
      if (!mm || !def || !MAG_VISUAL[def.cls]) { m.gearParts[slot] = null; return null; }
      mesh.position.copy(mm.pos); mesh.quaternion.copy(mm.quat); mesh.scale.copy(mm.scale);
      m.mag.add(mesh);
    } else {
      mesh.position.copy(mounts(m)[slot]);
      m.mesh.add(mesh);
    }
    m.gearParts[key] = mesh;
    return mesh;
  }
  /* show the attachment meshes for weapon id (items by slot), move the muzzle flash and the ADS eye point */
  function dressViewmodel(id, items, isCur) {
    var W = IB.Weapons, m = W.models && W.models[id];
    if (!m || !Gear.ready) return;
    m.id = m.id || id;
    IB.LOOT.slots.forEach(function (sl) {
      if (sl === 'muzzle') {   // hide every can model, show the one fitted
        Object.keys(m.gearParts || {}).forEach(function (k) { if (k.indexOf('muzzle.') === 0 && m.gearParts[k]) m.gearParts[k].visible = false; });
        if (items.muzzle) { var cp = vmPart(m, 'muzzle', items.muzzle.type); if (cp) cp.visible = true; }
        return;
      }
      var on = !!items[sl], part = on ? vmPart(m, sl) : m.gearParts && m.gearParts[sl];
      if (part) part.visible = on;
    });
    // muzzle flash rides the acid can's tip
    if (!m.muzzle0) m.muzzle0 = m.muzzle || null;
    var can = items.muzzle && m.gearParts['muzzle.' + items.muzzle.type];
    var want = can ? can.userData.tip : m.muzzle0;
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
    // attachments stay on every gun in the arsenal (a gun parked by the Tab loadout keeps its mods)
    L().prune(g, owned.concat((G.slot && G.slot.arsenal) || []));
    owned.forEach(function (id) {
      var gun = G.ws.guns[id], items = L().weaponItems(g, id);
      gun.def = L().applyMods(IB.WEAPONS[id], items);
      // a mag taken off: the rounds that no longer fit go back to the spare ammo
      var size = IB.Weapons.magSize(G.ws, gun.def);
      if (gun.mag > size) { if (gun.reserve !== Infinity) gun.reserve += gun.mag - size; gun.mag = size; }
      // ADS keeps the camera where the iron sights put it (the eye point is further forward), so the arms never clip
      if (items.scope) { var mt = Gear.mounts(id); gun.def.adsDist = (ADS_DIST[gun.def.cls] || 0.25) + (mt ? (mt.sightZ - mt.scope.z) * 0.85 : 0); }
      dressViewmodel(id, items, G.ws.cur === id);
    });
    var p = G.player, it = g.shield ? L().find(g, g.shield) : null;
    if (!it) { p.shield = null; }
    else if (!p.shield || p.shield.id !== it.id || fill) {
      var st = L().shieldState(it); st.id = it.id;
      if (p.shield && p.shield.id === it.id && !fill) { st.cur = Math.min(st.max, p.shield.cur); st.nova = p.shield.nova && st.nova; st.since = p.shield.since; }
      p.shield = st;
    }
    // vest: extra max health (game.js applySkillStats counts it in; a vest put on / taken off here moves the cap,
    // health itself never goes up from swapping vests)
    var hp = Gear.vestHp(G), dv = hp - (p.vestHp || 0);
    if (dv) { p.maxHp = Math.max(1, (p.maxHp || 100) + dv); p.vestHp = hp; p.health = Math.min(p.maxHp, fill && dv > 0 ? p.health + dv : p.health); }
    if (IB.LootHUD) IB.LootHUD.shield(p.shield);
  };
  Gear.vestHp = function (G) { var g = Gear.gear(G); return g ? L().armorOf(L().worn(g, 'armor')).hp : 0; };
  Gear.startLevel = function (G) {
    voids.length = 0; if (IB.LootHUD) IB.LootHUD.reset(); Gear.novaQ = 0; Gear.refresh(G, true); };
  Gear.fillShield = function (G) { var s = G.player && G.player.shield; if (s) { s.cur = s.max; s.since = 99; s.charging = false; s.boostT = 0; if (s.perk && s.perk.id === 'nova') s.nova = true; } };

  // ---------------- damage in / out ----------------
  Gear.absorb = function (G, dmg) {
    var p = G.player, st = p.shield, through = dmg;
    if (st) {
      var r = L().absorb(st, dmg);
      if (r.absorbed > 0) {
        play(r.broke ? 'shieldBreak' : 'shieldHit', { gain: 0.9 });
        if (IB.LootHUD) IB.LootHUD.shieldHit(r.broke);
      }
      // the burst goes off next frame (this runs inside a robot's attack)
      if (r.nova) Gear.novaQ = 0.05;
      through = r.through;
    }
    var g = Gear.gear(G), vest = g && L().worn(g, 'armor');
    if (vest && through > 0) through = L().armorCut(vest, through);
    return through;
  };
  /* Nova: shock burst round the player: damage + stagger + a short shock burn on every robot in reach */
  Gear.nova = function (G) {
    var p = G.player, st = p && p.shield, pk = st && st.perk;
    if (!pk || pk.id !== 'nova' || !p.alive) return 0;
    var R = pk.radius || 5, n = 0, B = IB.Boom && IB.Boom.ready ? IB.Boom : null;
    (IB.AI.robots || []).forEach(function (r) {
      if (!r.on || r.state === 'spawn' || r.state === 'pose' || r.rogue > 0) return;
      var dx = r.x - p.x, dz = r.z - p.z, d = Math.hypot(dx, dz); if (d > R) return;
      var k = d > 0.01 ? 1 / d : 0, ry = (r.y || 0) + 0.6;
      if (B) B.arc(p.x, 1.0, p.z, r.x, ry, r.z, 0x5FC2FF, 0.3, 0.9);
      var killed = IB.AI.damage(r, pk.v, { stagger: true, kx: dx * k * 6, kz: dz * k * 6 }, G.onKill);
      if (!killed && IB.Status) IB.Status.apply(r, 'shock', pk.v * 0.08, 2.5);
      if (IB.FX.damageNumber) { var v = IB.AI.VIS && IB.AI.VIS[r.type]; IB.FX.damageNumber(r.x, (r.y || 0) + (v ? v.y1 : 0.9) + 0.22, r.z, pk.v, 'shock'); }
      n++;
    });
    if (B) { B.zap(p.x, 1.0, p.z, 1.6, 0x5FC2FF); B.zap(p.x, 0.5, p.z, 1.1, 0xFFFDF7); }
    if (IB.FX && IB.FX.puff) { for (var i = 0; i < 10; i++) { var a = i / 10 * Math.PI * 2; IB.FX.puff(p.x + Math.cos(a) * R * 0.5, 0.4, p.z + Math.sin(a) * R * 0.5, 1, 0x5FC2FF, 0.12, 0.4, 4); } }
    play('shieldNova', { gain: 1 });
    if (G.addTrauma) G.addTrauma(0.3);
    if (IB.LootHUD) IB.LootHUD.perk('nova');
    Gear.novaCount = (Gear.novaCount || 0) + 1; Gear.novaLast = n;
    return n;
  };
  /* a player kill: Overcharge starts the recharge at once and speeds it up */
  Gear.onKill = function (G) {
    var st = G.player && G.player.shield;
    if (st && L().shieldKill(st)) { play('overcharge', { gain: 0.7 }); if (IB.LootHUD) IB.LootHUD.perk('overcharge'); return true; }
    return false;
  };
  /* res: IB.Damage.hit result; zone 'core'|'body'; killed: AI.damage returned true */
  Gear.onHit = function (r, res, zone, def, killed) {
    var v = IB.AI.VIS[r.type], top = r.y + (v ? v.y1 : 0.9) + 0.22;
    if (IB.FX.damageNumber) IB.FX.damageNumber(r.x, top, r.z, res.damage, res.crit ? 'crit' : zone === 'core' ? 'core' : 'hit');
    if (!killed && def.acid > 0 && IB.Status) IB.Status.apply(r, 'acid', res.damage * def.acid / def.acidDur, def.acidDur);
    if (def.can && Math.random() < def.can.stats.chance) canFx(def.can, r, res.damage, killed);
  };

  // ---------------- Arc / Boom / Void cans ----------------
  var AI_ = function () { return IB.AI; }, voids = [];
  function mid(r) { var v = IB.AI.VIS[r.type]; return r.y + (v ? (v.y0 + v.y1) / 2 : 0.6); }
  function canFx(can, r, dmg, killed) {
    var G = IB.Game, AI = AI_(), st = can.stats, y = mid(r);
    if (can.type === 'shock') {
      // the robot is shocked, then the arc jumps to the nearest robot within 5 m
      if (!killed && IB.Status) IB.Status.apply(r, 'shock', dmg * st.arc / 3, 3);
      var best = null, bd = 5;
      AI.robots.forEach(function (o) { if (o.on && o !== r && o.state !== 'spawn' && o.state !== 'pose' && !(o.rogue > 0)) { var d = Math.hypot(o.x - r.x, o.z - r.z); if (d < bd) { bd = d; best = o; } } });
      if (IB.Boom) IB.Boom.zap(r.x, y, r.z, 0.5);
      if (best) {
        if (IB.Boom && IB.Boom.lightning) IB.Boom.lightning(r.x, y, r.z, best.x, mid(best), best.z);
        if (!AI.damage(best, dmg * st.arc, { stagger: false }, G.onKill) && IB.Status) IB.Status.apply(best, 'shock', dmg * st.arc / 3, 3);
      }
      play('boltHit', { gain: 0.5, pitch: 1.4 });
    } else if (can.type === 'blast') {
      // a small blast on the robot: robots only (the player takes nothing from their own can)
      if (IB.Projectiles) IB.Projectiles.explode(r.x, y, r.z, 2.4, 0, dmg * st.power, { type: 'blast', x: r.x, z: r.z });
    } else if (can.type === 'void') {
      voids.push({ x: r.x, y: y, z: r.z, r: r, t: 1.4, R: st.radius });
      play('shove', { pitch: 0.5, gain: 0.8 });
    }
  }
  // singularities: robots within reach are dragged toward the centre (stopping short of it and of walls)
  function tickVoids(dt) {
    var AI = AI_(), Z = IB.Zones, L = IB.Game.level;
    for (var i = voids.length - 1; i >= 0; i--) {
      var v = voids[i]; v.t -= dt;
      if (v.r && v.r.on) { v.x = v.r.x; v.z = v.r.z; }
      if (v.t <= 0) { voids.splice(i, 1); continue; }
      if (IB.FX) { var a = Math.random() * 6.28, rr = 0.6 + Math.random() * v.R * 0.4; IB.FX.puff(v.x + Math.cos(a) * rr, v.y, v.z + Math.sin(a) * rr, 1, 0x9A5BFF, 0.06, 0.18, 0.5); }
      AI.robots.forEach(function (o) {
        if (!o.on || o === v.r || o.state === 'spawn' || o.state === 'pose' || o.rogue > 0 || (IB.AI.VIS[o.type] && IB.AI.VIS[o.type].flying && o.y > 2)) return;
        var dx = v.x - o.x, dz = v.z - o.z, d = Math.hypot(dx, dz);
        if (d > v.R) return;
        // how hard it is pulled (0..1): the bodies lean, drag, lift and flail by it (trooperrig.js, AI.sync)
        var k = Math.min(1, 0.45 + 0.6 * (1 - d / v.R)) * Math.min(1, v.t / 0.25);
        if (k > (o.pullTgt || 0)) { o.pullTgt = k; o.pullX = v.x; o.pullZ = v.z; }
        if (d < 1.1) return;
        var step = Math.min(d - 1.1, dt * (3 + 6 * (1 - d / v.R))), nx = o.x + dx / d * step, nz = o.z + dz / d * step;
        var zi = Z.zoneAt(L, nx, nz);
        if (zi >= 0 && Z.isOpen(L.zones[zi], nx, nz)) { o.x = nx; o.z = nz; }
      });
    }
  }
  Gear.voidCount = function () { return voids.length; };
  // the pull each robot feels, eased in and out so the bodies never snap (r.pull 0..1, r.pullT its own clock)
  function easePull(dt) {
    var rs = IB.AI && IB.AI.robots; if (!rs) return;
    for (var i = 0; i < rs.length; i++) {
      var o = rs[i]; if (!o.pull && !o.pullTgt) continue;
      var tg = o.on ? o.pullTgt || 0 : 0;
      o.pull = (o.pull || 0) + (tg - (o.pull || 0)) * Math.min(1, dt * (tg > o.pull ? 5 : 2.6));
      if (o.pull < 0.005 && !tg) o.pull = 0;
      o.pullT = (o.pullT || 0) + dt; o.pullTgt = 0;
    }
  }

  // ---------------- per frame ----------------
  Gear.update = function (dt, G) {
    if (voids.length) tickVoids(dt);
    easePull(dt);
    var p = G.player, st = p && p.shield;
    if (st && p.alive) {
      var ev = L().tickShield(st, dt);
      if (ev === 'start') play('shieldUp', { gain: 0.7 });
      else if (ev === 'full') play('shieldFull', { gain: 0.6 });
      if (ev && IB.LootHUD) IB.LootHUD.shieldEvent(ev);
    }
    if (Gear.novaQ > 0) { Gear.novaQ -= dt; if (Gear.novaQ <= 0) { Gear.novaQ = 0; Gear.nova(G); } }
    if (IB.LootHUD) { IB.LootHUD.shield(st); IB.LootHUD.tick(dt); }
    // a scope (a fitted one, or the tube scope built into the gun: def.scopeZoom / def.scopeView): past ~70 % aim the
    // comic scope view fades in and the viewmodel steps aside. Without it the eye sits inside the gun's own scope tube
    // and the target is hidden behind its dark barrel and lens.
    var w = G.ws && IB.Weapons.current(G.ws), scoped = w && (w.def.optic || w.def.scopeZoom > 0 || w.def.scopeView);
    var k = scoped && p.alive && !G.ws.melee ? Math.max(0, Math.min(1, (G.ws.aim - 0.7) / 0.22)) : 0;
    if (IB.LootHUD) IB.LootHUD.scope(k);
    if (G.ws) G.ws.hidden = k >= 0.98;
    if (Gear.glowMat) { var k = 0.5 + 0.5 * Math.sin(performance.now() * 0.006); Gear.glowMat.color.setRGB(0.48 + 0.3 * k, 0.89 + 0.1 * k, 0.29 + 0.25 * k);
      Object.keys(Gear.glowMats).forEach(function (t) { if (t === 'acid') return; var c = CAN_GLOW[t]; Gear.glowMats[t].color.setHex(c[0]).lerp(_cg.setHex(c[1]), k * 0.6); }); }
  };

  /* an item for the test hooks: a given perk is forced by re-rolling (epic / legendary shields) */
  Gear.testItem = function (type, rarity, level, perk) {
    var G = IB.Game, lv = level || (G.plan && G.plan.level) || 1, it = null;
    for (var i = 0; i < 64; i++) { it = L().makeItem(type || 'grip', rarity || 'rare', lv, Math.random); if (!perk || (it.perk && it.perk.id === perk)) break; }
    return it;
  };

  // ---------------- test hooks (merged into window.__TEST__ by game.js) ----------------
  IB.GearTest = {
    // force a world drop in front of the player: type 'shield'|'grip'|'scope'|'acid'|'mag'|'armor', rarity, distance (m),
    // level (default: the level played), perk id for a shield ('overcharge'|'nova', epic / legendary only)
    forceDrop: function (type, rarity, dist, level, perk) {
      var G = IB.Game, p = G.player, d = dist === undefined ? 4 : dist;
      var item = Gear.testItem(type, rarity, level, perk);
      return IB.Drops.spawn(item, p.x - Math.sin(p.yaw) * d, p.z - Math.cos(p.yaw) * d, p.y) ? item : null;
    },
    // put an item straight into the bag (no drop): returns its id
    giveItem: function (type, rarity, level, perk) {
      var G = IB.Game, g = Gear.gear(G), it = L().addItem(g, Gear.testItem(type, rarity, level, perk));
      Gear.save(G); return it ? it.id : null;
    },
    drops: function () { return IB.Drops.list(); },
    // a Void singularity at (x, z) (height y, reach R m, t s), as a Void can opens one on a hit
    forceVoid: function (x, z, R, t, y) { voids.push({ x: x, y: y === undefined ? 1 : y, z: z, r: null, t: t || 1.4, R: R || 6 }); return voids.length; },
    gearState: function () {
      var G = IB.Game, g = Gear.gear(G), p = G.player, w = IB.Weapons.current(G.ws);
      return { inv: g ? g.inv.map(function (i) { return { id: i.id, type: i.type, rarity: i.rarity, name: i.name, perk: i.perk ? i.perk.id : null }; }) : [], shield: g && g.shield, armor: g && g.armor,
        attach: g ? JSON.parse(JSON.stringify(g.attach)) : {},
        playerShield: p.shield ? { cur: p.shield.cur, max: p.shield.max, rarity: p.shield.rarity, perk: p.shield.perk ? p.shield.perk.id : null, nova: p.shield.nova, boostT: p.shield.boostT, charging: p.shield.charging } : null,
        health: p.health, maxHp: p.maxHp, vestHp: p.vestHp || 0, novas: Gear.novaCount || 0, novaHit: Gear.novaLast || 0,
        weapon: w ? { id: w.id, recoil: w.def.recoil, spreadHip: w.def.spreadHip, spreadAim: w.def.spreadAim, aimZoom: w.def.aimZoom, acid: w.def.acid || 0, baseRecoil: IB.WEAPONS[w.id].recoil, baseAimZoom: IB.WEAPONS[w.id].aimZoom,
          mag: w.def.mag, baseMag: IB.WEAPONS[w.id].mag, magSize: IB.Weapons.magSize(G.ws, w.def), reload: w.def.reload, baseReload: IB.WEAPONS[w.id].reload } : null,
        vm: w && IB.Weapons.models[w.id] && IB.Weapons.models[w.id].gearParts ? Object.keys(IB.Weapons.models[w.id].gearParts).filter(function (k) { var q = IB.Weapons.models[w.id].gearParts[k]; return q && q.visible; }).map(function (k) { return k.split('.')[0]; }) : [],
        numbers: IB.FX.numbersList ? IB.FX.numbersList() : [], statuses: IB.Status ? IB.Status.active() : 0 };
    },
    attach: function (id, wid) { var G = IB.Game, g = Gear.gear(G); wid = wid || G.ws.cur; var ok = L().attach(g, wid, IB.WEAPONS[wid], id); Gear.refresh(G); Gear.save(G); return ok; },
    equipShield: function (id) { var G = IB.Game, ok = L().equipShield(Gear.gear(G), id); Gear.refresh(G, true); Gear.save(G); return ok; },
    equipWorn: function (slot, id) { var G = IB.Game, ok = L().equipWorn(Gear.gear(G), slot, id); Gear.refresh(G, slot === 'shield'); Gear.save(G); return ok; },
    // a player kill for Overcharge (no robot needed)
    gearKill: function () { return Gear.onKill(IB.Game); },
    gear: function () { IB.GearUI.open(IB.Game); },
    status: function (kind, dps, dur) { var r = IB.AI.robots.find(function (x) { return x.on && x.state !== 'pose' && x.state !== 'spawn'; }); return r ? !!IB.Status.apply(r, kind, dps, dur) : false; }
  };
})(window.IB = window.IB || {});
