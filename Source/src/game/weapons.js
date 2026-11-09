/* INKBOLT weapons: table-driven hitscan guns (semi/auto/burst), spread + recoil rules (5.2),
   reload/draw/holster, quick shove, greybox viewmodel with spring kick. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var W = IB.Weapons = {};
  var D2R = Math.PI / 180;
  var FIRE_SND = { pistol: ['pip', 1], smg: ['buzz', 1], rifle: ['gun', 1.05], sniper: ['gun', 0.62], handcannon: ['gun', 0.78], twintap: ['pip', 1.12],
    whisk: ['buzz', 1.18], hornet: ['buzz', 0.9], longtom: ['gun', 0.82], brick: ['gun', 0.88], triplet: ['gun', 1.12],
    shotgun: ['gun', 0.66], scrapper: ['gun', 0.6], thunder: ['gun', 0.7], vanguard: ['gun', 0.92], railspike: ['gun', 1.3],
    hothead: ['rocket', 1.05], murmur: ['rocket', 0.82] };
  var _dir = new THREE.Vector3(), _right = new THREE.Vector3(), _up = new THREE.Vector3(), _fwd = new THREE.Vector3();

  // ---------------- viewmodel: Blender arms rig (22 bones) + weapon meshes from fps-weapons.glb ----------------
  W.init = function (vmScene) {
    var A = IB.Assets;
    W.vmRoot = new THREE.Group();
    vmScene.add(W.vmRoot);
    W.vmMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons });
    W.vmSkinMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons, skinning: true });
    var rig = W.rig = A.node.ARMS_Rig;
    rig.parent && rig.parent.remove(rig);
    rig.position.set(0, 0, 0); rig.updateMatrixWorld(true);
    W.vmRoot.add(rig);
    var arms = A.node.ARMS;
    arms.material = W.vmSkinMat; arms.frustumCulled = false;
    W.bone = { Weapon: rig.getObjectByName('Weapon'), Mag: rig.getObjectByName('Mag') };
    // rest-pose world matrices (rig space) so meshes modelled in rig space can ride the bones
    W.vmRoot.updateMatrixWorld(true);
    var rigInv = rig.matrixWorld.clone().invert();
    W.restInv = {};
    ['Weapon', 'Mag'].forEach(function (b) {
      var m = new THREE.Matrix4().multiplyMatrices(rigInv, W.bone[b].matrixWorld);
      W.restInv[b] = m.clone().invert();
      W.restPos = W.restPos || {}; W.restPos[b] = new THREE.Vector3().setFromMatrixPosition(m);
    });
    W.mixer = new THREE.AnimationMixer(rig);
    W.clips = {};
    A.gltf.weapons.animations.forEach(function (c) { W.clips[c.name] = c; });
    W.models = {};
    // muzzle flash: layered flat comic star (ink rim, amber star, paper core) with side flares and a forward
    // cone, unlit, parented to the active weapon's MUZZLE socket; scaled per class, two frames (full, then smaller)
    function starGeo(n, r0, r1, jit) {
      var sh = new THREE.Shape();
      for (var i = 0; i <= n * 2; i++) { var a = i / (n * 2) * Math.PI * 2, r = (i % 2 ? r1 : r0) * (1 + (i % 4 === 0 ? jit : 0)); if (i === 0) sh.moveTo(Math.cos(a) * r, Math.sin(a) * r); else sh.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
      return new THREE.ShapeGeometry(sh);
    }
    // layers are merged into one geometry each (vertex colours, drawn in order with no depth test): 3 draw calls
    var _lm = new THREE.Matrix4(), _lc = new THREE.Color();
    function layers(list) {
      var geos = list.map(function (L) {
        var g = L[0].clone(); g.applyMatrix4(_lm.compose(new THREE.Vector3(0, 0, L[3] || 0), new THREE.Quaternion().setFromEuler(new THREE.Euler(L[4] || 0, L[5] || 0, L[6] || 0)), new THREE.Vector3(L[2][0], L[2][1], 1)));
        var n = g.attributes.position.count, c = new Float32Array(n * 3); _lc.set(L[1]);
        for (var i = 0; i < n; i++) { c[i * 3] = _lc.r; c[i * 3 + 1] = _lc.g; c[i * 3 + 2] = _lc.b; }
        g.setAttribute('color', new THREE.BufferAttribute(c, 3)); g.deleteAttribute('uv'); g.deleteAttribute('normal');
        return g;
      });
      var m = new THREE.Mesh(THREE.BufferGeometryUtils.mergeBufferGeometries(geos), new THREE.MeshBasicMaterial({ vertexColors: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide }));
      m.renderOrder = 10; m.frustumCulled = false;
      return m;
    }
    var petal = new THREE.Shape(); petal.moveTo(0, 0); petal.quadraticCurveTo(0.07, 0.03, 0.16, 0); petal.quadraticCurveTo(0.07, -0.03, 0, 0);
    var pg = new THREE.ShapeGeometry(petal), ONE = [1, 1];
    W.flash = new THREE.Group();
    W.flashStar = layers([[starGeo(6, 0.12, 0.058, 0.18), PAL.ink, ONE], [starGeo(6, 0.095, 0.04, 0.18), PAL.amber, ONE], [starGeo(5, 0.05, 0.028, 0), PAL.paper, ONE]]);
    W.flash.add(W.flashStar);
    // side flares (rifles, SMGs, snipers, shotguns): two petals out to the sides
    W.flashSide = layers([[pg, PAL.ink, [1.12, 1.7]], [pg, PAL.ink, [1.12, 1.7], 0, 0, 0, Math.PI], [pg, PAL.amber, ONE], [pg, PAL.amber, ONE, 0, 0, 0, Math.PI]]);
    W.flashSide.renderOrder = 9; W.flash.add(W.flashSide);
    // a cone of fire forward along -z (seen edge-on from behind: a short spike)
    W.flashCone = layers([[pg, PAL.ink, [1.5, 2.2], 0.002, 0, Math.PI / 2, 0], [pg, PAL.amber, [1.4, 1.5], 0, 0, Math.PI / 2, 0]]);
    W.flashCone.renderOrder = 9; W.flash.add(W.flashCone);
    W.flashCore = W.flashStar;
    // rarity flash sets (Tuned and up): the amber layers in the tier's flash tint (core/gunskins.js FEEL)
    W.flashSets = { gray: [W.flashStar, W.flashSide, W.flashCone] };
    var FD = IB.GunSkinData;
    if (FD) ['green', 'blue', 'purple', 'orange'].forEach(function (t) {
      var tc = FD.FEEL[t].flash;
      var st = layers([[starGeo(6, 0.12, 0.058, 0.18), PAL.ink, ONE], [starGeo(6, 0.095, 0.04, 0.18), tc, ONE], [starGeo(5, 0.05, 0.028, 0), PAL.paper, ONE]]);
      var sd = layers([[pg, PAL.ink, [1.12, 1.7]], [pg, PAL.ink, [1.12, 1.7], 0, 0, 0, Math.PI], [pg, tc, ONE], [pg, tc, ONE, 0, 0, 0, Math.PI]]); sd.renderOrder = 9;
      var cn = layers([[pg, PAL.ink, [1.5, 2.2], 0.002, 0, Math.PI / 2, 0], [pg, tc, [1.4, 1.5], 0, 0, Math.PI / 2, 0]]); cn.renderOrder = 9;
      [st, sd, cn].forEach(function (o) { o.visible = false; W.flash.add(o); });
      W.flashSets[t] = [st, sd, cn];
    });
    W.flash.visible = false;
    // things the support hand holds (frag can for a throw, a shell while loading the pump gun) ride the HOLD_L socket
    // on the left hand bone (blender/fam_weapons.py hold_socket)
    W.held = {};
    var hold = rig.getObjectByName('HOLD_L');
    ['Frag', 'Shell'].forEach(function (n) {
      var src = A.node['HELD_' + n]; if (!hold || !src) return;
      var m = new THREE.Mesh(src.geometry, W.vmMat); m.frustumCulled = false; m.visible = false;
      if (n === 'Frag') m.scale.setScalar(0.75);   // read at arm's length right in front of the lens: a little smaller
      hold.add(m); W.held[n] = m;
    });
  };
  function showHeld(n, on) { var m = W.held && W.held[n]; if (m) m.visible = !!on; }
  // flash size per class (pistol 1); and which classes get side flares
  var FLASH_SCALE = { pistol: 0.95, smg: 1.0, rifle: 1.2, sniper: 1.55, shotgun: 1.7, rocket: 1.4, handcannon: 1.45 };
  var FLASH_SIDE = { smg: true, rifle: true, sniper: true, shotgun: true };
  function model(id) {
    if (W.models[id]) return W.models[id];
    var A = IB.Assets, key = 'WPN_' + id.toUpperCase();
    if (!A.node[key]) return null;   // weapon without a Blender model yet
    var gun = A.node[key], mag = A.node[key + '_Mag'];
    [gun, mag].forEach(function (o) { if (o && o.parent) o.parent.remove(o); });
    gun.material = W.vmMat; gun.frustumCulled = false; gun.matrixAutoUpdate = false; gun.matrix.copy(W.restInv.Weapon); gun.visible = false;
    W.bone.Weapon.add(gun);
    if (mag) {
      // the Mag bone is keyed onto each weapon's MAG socket; keep the mesh in rig orientation at the bone head
      mag.material = W.vmMat; mag.frustumCulled = false; mag.matrixAutoUpdate = false;
      mag.matrix.copy(W.restInv.Mag).multiply(new THREE.Matrix4().makeTranslation(W.restPos.Mag.x, W.restPos.Mag.y, W.restPos.Mag.z));
      mag.visible = false; W.bone.Mag.add(mag);
    }
    var muzzle = gun.getObjectByName(key + '_MUZZLE');
    W.models[id] = { mesh: gun, mag: mag, muzzle: muzzle, key: id.toUpperCase() };
    return W.models[id];
  }
  function setFlash(tier) {
    var set = W.flashSets && (W.flashSets[tier] || W.flashSets.gray); if (!set || set[0] === W.flashStar) return;
    [W.flashStar, W.flashSide, W.flashCone].forEach(function (o) { o.visible = false; });
    W.flashStar = W.flashCore = set[0]; W.flashSide = set[1]; W.flashCone = set[2]; W.flashStar.visible = true;
  }
  // rarity skin (src/game/gunskins.js): checked every frame, so a tier upgrade shows at once
  function skinModel(id) {
    var m = W.models[id]; if (!m || !IB.GunSkins || IB.WEAPONS[id].cls === 'melee') return;
    var tier = IB.GunSkins.tierOf(id); if (m.tier === tier) return;
    var mat = IB.GunSkins.material(id, tier, IB.Render.vmOutline);
    m.tier = tier; m.mesh.material = mat; if (m.mag) m.mag.material = mat;
    setFlash(tier);
  }
  function showModel(id, on) {
    var m = W.models[id]; if (!m) return; m.mesh.visible = on; if (m.mag) m.mag.visible = on;
    if (on) skinModel(id);
    if (on && m.muzzle && IB.WEAPONS[id].cls !== 'melee') m.muzzle.add(W.flash);
  }

  // ---------------- arm animation (Blender actions <WEAPON>_<Action>) ----------------
  W.anim = function (s, name, opts) {
    opts = opts || {};
    var m = s.cur && W.models[s.cur]; if (!m) return;
    W.play(m.key, name, opts);
  };
  // play <KEY>_<name> on the arms rig (KEY: a gun or a melee weapon); false when there is no such clip
  W.play = function (key, name, opts) {
    opts = opts || {};
    var clip = W.clips[key + '_' + name]; if (!clip) return false;
    var act = W.mixer.clipAction(clip);
    act.reset(); act.enabled = true; act.setEffectiveWeight(1);
    act.setLoop(opts.once ? THREE.LoopOnce : THREE.LoopRepeat, Infinity);
    act.clampWhenFinished = !!opts.once;
    act.timeScale = opts.timeScale || 1;
    act.play();
    if (W.action && W.action !== act) act.crossFadeFrom(W.action, opts.fade === undefined ? 0.08 : opts.fade, false);
    W.action = act; W.animName = name; W.animOnce = !!opts.once;
    return true;
  };

  // ---------------- state ----------------
  /* owned: array of weapon ids; fx: upgrade effects */
  W.create = function (owned, fx) {
    var s = { guns: {}, slots: {}, cur: null, state: 'idle', t: 0, next: 0, burst: 0, sinceShot: 9, shotsInRow: 0,
      recoilP: 0, recoilY: 0, kickZ: 0, kickZv: 0, kickR: 0, kickRv: 0, swayX: 0, swayY: 0, flashT: 0, reloadT: 0, drawT: 0,
      aim: 0, shoveT: 0, fx: fx || {}, triggerWas: false, pending: null, melee: null, throwing: null, combo: 0, comboT: 9,
      ammo: { rocket: 0 } };   // shared ammo pools: every launcher draws on ammo.rocket (game/launchers.js keeps it saved)
    owned.forEach(function (id) { W.give(s, id); });
    return s;
  };
  // guns with a Blender model are playable: hitscan guns and the launchers (fire 'rocket'); not grenades, melee or the
  // old RL-1 Canister ('projectile', no model)
  W.playable = function (id) {
    var def = IB.WEAPONS[id]; if (!def || def.fire === 'throw' || def.fire === 'melee' || def.fire === 'projectile') return false;
    return !!IB.Assets.node['WPN_' + id.toUpperCase()];
  };
  // slots are loadout positions: keys 1..n switch between the carried guns in loadout order
  W.give = function (s, id) {
    if (!W.playable(id) || !model(id)) return;
    var def = IB.WEAPONS[id];
    s.guns[id] = { id: id, def: def, mag: W.magSize(s, def), reserve: (def.reserve === null || def.reserve === undefined || def.reserve === Infinity) ? Infinity : def.reserve };
    if (def.ammo) {   // launchers: the spare ammo is the shared pool (s.ammo.rocket), not per gun
      var pool = s.ammo || (s.ammo = {}), kind = def.ammo; if (!(pool[kind] >= 0)) pool[kind] = 0;
      Object.defineProperty(s.guns[id], 'reserve', { enumerable: true, get: function () { return pool[kind]; }, set: function (v) { pool[kind] = Math.max(0, v); } });
    }
    if (W.slotOf(s, id) < 0) { var n = 1; while (s.slots[n]) n++; s.slots[n] = id; }
  };
  W.slotOf = function (s, id) { for (var k in s.slots) if (s.slots[k] === id) return +k; return -1; };
  /* carry exactly `ids` (in key order). Guns leaving the loadout park their ammo in `bank` and guns joining it take
     theirs back from there, so swapping in the Tab menu never refills a magazine. */
  W.setLoadout = function (s, ids, bank) {
    bank = bank || {};
    Object.keys(s.guns).forEach(function (k) { bank[k] = { mag: s.guns[k].mag, reserve: s.guns[k].reserve }; });
    var cur = s.cur;
    s.guns = {}; s.slots = {};
    ids.forEach(function (id) { W.give(s, id); var b = bank[id], g = s.guns[id]; if (g && b) { g.mag = Math.min(b.mag, W.magSize(s, g.def)); if (!g.def.ammo) g.reserve = b.reserve; else g._fromBank = true; } });
    if (!s.guns[cur]) { var first = s.slots[1]; s.cur = null; if (first) W.equip(s, first, true); else Object.keys(W.models).forEach(function (k) { showModel(k, false); }); }
    return bank;
  };
  W.magSize = function (s, def) {
    if (def.ammo) return IB.Launchers && IB.Launchers.magOf ? IB.Launchers.magOf(def) : def.mag;   // a launcher's rolled magazine; no bench / skill bonus
    var base = def.mag, rr = def.wyrm && IB.WeaponDrops && IB.WeaponDrops.rollOf ? IB.WeaponDrops.rollOf(def.id) : null;   // Wyrmforged: the rolled magazine
    if (rr && rr.mag) base = rr.mag;
    var m = IB.Upgrades ? IB.Upgrades.magSize(base, s.fx.magLevel || 0) : base;
    return s.fx.magMul && m !== Infinity ? Math.ceil(m * s.fx.magMul - 1e-9) : m;   // Overload skill
  };
  // refill (respawn) and ammo boxes leave the launchers alone: rocket ammo only comes in rocket crates
  W.refill = function (s) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.def.ammo) return; g.mag = W.magSize(s, g.def); g.reserve = (g.def.reserve == null || g.def.reserve === Infinity) ? Infinity : g.def.reserve; }); };
  W.addAmmo = function (s, frac) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.reserve !== Infinity && !g.def.ammo) g.reserve = Math.min(g.def.reserve * 1.5, g.reserve + Math.ceil(g.def.reserve * frac)); }); };
  /* every gun that takes ammo boxes is at its reserve cap (an ammo box would add nothing) */
  W.ammoFull = function (s) {
    return IB.Loadout.ammoFull(s.guns);   // core/loadout.js
  };
  W.current = function (s) { return s.cur ? s.guns[s.cur] : null; };
  W.ownedSlots = function (s) { return Object.keys(s.slots).map(Number).sort(); };

  W.equip = function (s, id, instant) {
    if (!s.guns[id] || (s.cur === id && s.state !== 'holster')) return;
    var sw = s.fx.swapMul || 1;   // Fast Fingers: quicker holster and draw
    if (s.cur && !instant) { s.pending = id; s.state = 'holster'; s.t = 0; W.anim(s, 'Holster', { once: true, timeScale: 1 / sw }); return; }
    Object.keys(W.models).forEach(function (k) { showModel(k, false); });
    s.cur = id; s.state = 'draw'; s.t = 0; s.burst = 0; s.shotsInRow = 0; s.recoilP *= 0.5;
    showModel(id, true);
    if (instant) { s.state = 'idle'; W.anim(s, 'Idle', { fade: 0 }); }
    else W.anim(s, 'Draw', { once: true, fade: 0, timeScale: 1 / sw });
    IB.Audio && IB.Audio.play('draw');
  };
  W.slot = function (s, n) { if (s.slots[n]) W.equip(s, s.slots[n]); };
  W.cycle = function (s, dir) {
    var sl = W.ownedSlots(s); if (sl.length < 2) return;
    var curSlot = W.slotOf(s, s.cur), i = sl.indexOf(curSlot);
    W.slot(s, sl[(i + dir + sl.length) % sl.length]);
  };
  W.reload = function (s) {
    var g = W.current(s); if (!g || s.state !== 'idle') return;
    if (g.mag >= W.magSize(s, g.def) || g.reserve < (g.def.ammoPer || 1)) return;
    s.state = 'reload'; s.t = 0; s.reloadT = g.def.reload * (s.fx.reloadMul || 1); s.burst = 0;
    var rc = W.clips[W.models[s.cur].key + '_Reload'];
    W.anim(s, 'Reload', { once: true, timeScale: rc ? rc.duration / s.reloadT : 1 });   // Fast Fingers rescales the clip
    IB.Audio && IB.Audio.play(g.def.reloadPerShell ? 'magIn' : 'magOut', g.def.reloadPerShell ? { pitch: 1.3, gain: 0.7 } : undefined);
  };
  W.busy = function (s) { return !!(s.melee || s.throwing); };

  // ---------------- melee (V): the gun goes away for one swing of the melee weapon, then comes back ----------------
  /* id: melee weapon id. Swings chain into a combo (each swing plays the next clip) when V comes again inside the
     weapon's comboWindow. ctx.melee(def, comboIndex, hitNo) is called when a blow lands. */
  // V cuts into a reload, a draw or a holster (the swap finishes after the swing); never into another swing or a throw
  W.meleeReady = function (s) { return !s.melee && !s.throwing; };
  W.meleeStart = function (s, id) {
    var def = IB.WEAPONS[id], m = def && model(id);
    if (!m || !W.meleeReady(s)) return false;
    if (s.state === 'reload') { s.state = 'idle'; s._magIn = false; showHeld('Shell', false); }
    if (s.state === 'holster' && s.pending) { s.cur = s.pending; s.pending = null; }   // the swap target comes out after the swing
    s.state = 'idle';
    var clips = def.clips || ['Strike'];
    s.combo = s.comboT < (def.comboWindow || 0.5) ? (s.combo + 1) % clips.length : 0;
    var dur = W.clips[m.key + '_' + clips[s.combo]] ? W.clips[m.key + '_' + clips[s.combo]].duration : def.swing;
    Object.keys(W.models).forEach(function (k) { showModel(k, false); });
    showModel(id, true);
    W.play(m.key, clips[s.combo], { once: true, fade: 0, timeScale: dur / (def.swing / (s.fx.meleeRate || 1)) });
    s.melee = { id: id, def: def, t: 0, dur: def.swing / (s.fx.meleeRate || 1), hits: 0, combo: s.combo };
    s.burst = 0; s.aim = 0;
    IB.Audio && IB.Audio.play('shove', { pitch: id === 'eaxe' ? 0.7 : id === 'dagger' ? 1.35 : 1.05, gain: 1.1 });
    return true;
  };
  function meleeUpdate(s, dt, ctx) {
    var mm = s.melee; mm.t += dt;
    var f = mm.t / mm.dur, d = mm.def;
    if (mm.hits === 0 && f >= d.hit) { mm.hits = 1; if (ctx.melee) ctx.melee(d, mm.combo, 0); }
    if (mm.hits === 1 && d.hit2 && f >= d.hit2) { mm.hits = 2; if (ctx.melee) ctx.melee(d, mm.combo, 1); }
    if (mm.t >= mm.dur) {
      s.melee = null; s.comboT = 0;
      showModel(mm.id, false);
      var cur = s.cur; s.cur = null;
      if (cur) W.equip(s, cur, false);   // the gun is drawn again
    }
  }

  // ---------------- grenade (G): the support hand throws a frag can while the gun dips ----------------
  // the throw clip is generated per gun (<GUN>_Throw, 0.62 s, release at 52 %): ctx.onThrow() spawns the grenade
  var THROW_RELEASE = 0.52, THROW_SHOW = 0.16;
  W.throwStart = function (s) {
    var g = W.current(s); if (!g || s.melee || s.throwing || s.state === 'holster') return false;
    if (s.state === 'draw') s.state = 'idle';
    if (s.state === 'reload') { s.state = 'idle'; s._magIn = false; showHeld('Shell', false); }
    var key = W.models[s.cur].key, clip = W.clips[key + '_Throw'];
    W.play(key, 'Throw', { once: true, fade: 0.05 });
    s.throwing = { t: 0, dur: clip ? clip.duration : 0.62, released: false };
    s.burst = 0;
    return true;
  };
  function throwUpdate(s, dt, ctx) {
    var th = s.throwing; th.t += dt;
    var f = th.t / th.dur;
    showHeld('Frag', f >= THROW_SHOW && !th.released);
    if (!th.released && f >= THROW_RELEASE) { th.released = true; showHeld('Frag', false); if (ctx.onThrow) ctx.onThrow(); IB.Audio && IB.Audio.play('shove', { pitch: 1.4, gain: 0.8 }); }
    if (th.t >= th.dur) s.throwing = null;
  }

  /* Epic (purple) and Legendary (orange) pistols and shotguns are tuned up: a faster fire rate; shotguns also fire more
     pellets (damage per pellet unchanged, so more damage per shot) in a wider cone. {rate, pellets, spread} multipliers. */
  var TIER_MODS = { purple: { rate: 1.15, pellets: 1.25, spread: 1.2 }, orange: { rate: 1.3, pellets: 1.5, spread: 1.4 } };
  W.tierMods = function (d) {
    var out = { rate: 1, pellets: 1, spread: 1 };
    if (!d || (d.cls !== 'pistol' && d.cls !== 'shotgun') || !IB.WeaponDrops) return out;
    var m = TIER_MODS[IB.WeaponDrops.tierOf(d.id).id]; if (!m) return out;
    out.rate = m.rate; if (d.cls === 'shotgun') { out.pellets = m.pellets; out.spread = m.spread; }
    return out;
  };
  // spread cone half-angle (deg) right now
  W.spread = function (s, player) {
    var g = W.current(s); if (!g) return 0;
    var d = g.def, base = (s.aim > 0.5 ? d.spreadAim : d.spreadHip) * (s.fx.spreadMul || 1) * W.tierMods(d).spread;
    if (player.moving) base *= 1.5;
    if (!player.onGround) base *= 2;
    if (s.sinceShot > 0.4) base *= 0.25;
    else base *= 1 + Math.min(6, s.shotsInRow) * 0.05;
    return base;
  };

  /* ctx: {player, cam, input:{fire, firePressed, aim}, shoot(origin, dir, def, shotIdx), dt} */
  W.update = function (s, dt, ctx) {
    var g = W.current(s), p = ctx.player, inp = ctx.input;
    s.t += dt; s.sinceShot += dt; s.next -= dt; s.flashT -= dt; s.shoveT -= dt;
    // recoil recovery: 12 deg/s, faster for small kicks so a single shot settles in ~0.18 s
    if (s.sinceShot > 0.06) {
      var rate = Math.max(12 * D2R, Math.abs(s.recoilP) / 0.18);
      s.recoilP = Math.max(0, s.recoilP - rate * dt);
      s.recoilY *= Math.max(0, 1 - dt / 0.18 * 2.5);
      if (s.sinceShot > 0.3) s.shotsInRow = 0;
    }
    // springs (stiffness 220, damping 18)
    // (sub-stepped: one long frame must not blow the explicit spring up, e.g. a launcher's big kick on a slow phone)
    for (var sn = Math.max(1, Math.ceil(dt / 0.016)), sh = dt / sn, si = 0; si < sn; si++) {
      s.kickZv += (-220 * s.kickZ - 18 * s.kickZv) * sh; s.kickZ += s.kickZv * sh;
      s.kickRv += (-220 * s.kickR - 18 * s.kickRv) * sh; s.kickR += s.kickRv * sh;
    }
    s.comboT += dt;
    if (s.melee) { meleeUpdate(s, dt, ctx); p.aiming = false; s.aim = Math.max(0, s.aim - dt * 14); return; }
    if (s.throwing) throwUpdate(s, dt, ctx);
    var wantAim = inp.aim && s.state !== 'reload' && !p.sprinting && !s.throwing;
    s.aim += ((wantAim ? 1 : 0) - s.aim) * Math.min(1, dt * 14);
    p.aiming = s.aim > 0.5;
    if (!g) return;
    p.weaponMoveMul = g.def.moveMul || 1;
    switch (s.state) {
      case 'holster':
        if (s.t >= 0.2 * (s.fx.swapMul || 1)) { var nid = s.pending; s.pending = null; showModel(s.cur, false); s.cur = null; W.equip(s, nid, false); }
        return;
      case 'draw':
        if (s.t >= 0.3 * (s.fx.swapMul || 1)) s.state = 'idle';
        return;
      case 'reload':
        if (g.def.reloadPerShell) {
          // one shell per cycle (the clip loops); fire with a shell in the tube stops loading
          showHeld('Shell', s.t >= s.reloadT * 0.22 && s.t < s.reloadT * 0.72);
          if (inp.firePressed && g.mag > 0) { s.state = 'idle'; showHeld('Shell', false); break; }
          if (s.t >= s.reloadT) {
            g.mag++; if (g.reserve !== Infinity) g.reserve--;
            IB.Audio && IB.Audio.play('magIn', { pitch: 1.3, gain: 0.7 });
            showHeld('Shell', false);
            if (g.mag < W.magSize(s, g.def) && g.reserve > 0) { s.t = 0; W.anim(s, 'Reload', { once: true, fade: 0, timeScale: (W.clips[W.models[s.cur].key + '_Reload'].duration) / s.reloadT }); }
            else { s.state = 'idle'; IB.Audio && IB.Audio.play('slide'); }
          }
          return;
        }
        if (s.t >= s.reloadT * 0.55 && !s._magIn) { s._magIn = true; IB.Audio && IB.Audio.play('magIn'); }
        if (s.t >= s.reloadT) {
          s._magIn = false;
          var per = g.def.ammoPer || 1, need = W.magSize(s, g.def) - g.mag, take = Math.min(need, Math.floor(g.reserve / per));   // a Murmur salvo takes 2 rockets
          g.mag += take; if (g.reserve !== Infinity) g.reserve -= take * per;
          s.state = 'idle'; IB.Audio && IB.Audio.play('slide');
        }
        return;
    }
    if (p.sprinting || s.throwing) { s.burst = 0; return; }
    var d = g.def;
    var trig = d.fire === 'auto' ? inp.fire : inp.firePressed;
    var rm = (s.fx.rateMul || 1) * W.tierMods(d).rate;   // Rapid skill + Epic / Legendary pistols and shotguns: shorter gaps between shots
    if (s.burst > 0 && s.next <= 0) { fire(s, g, ctx); s.burst--; s.next = (s.burst > 0 ? (d.burstGap || 60 / d.rpm) : Math.max(0, d.cycle - (d.burst - 1) * (d.burstGap || 60 / d.rpm))) / rm; return; }
    if (trig && s.next <= 0 && s.burst === 0) {
      if (g.mag <= 0) { if (inp.firePressed) IB.Audio && IB.Audio.play('dry'); W.reload(s); return; }
      if (d.burst > 1) { s.burst = d.burst; s.next = 0; fire(s, g, ctx); s.burst--; s.next = (d.burstGap || 60 / d.rpm) / rm; }
      else { fire(s, g, ctx); s.next = (d.cycle || 60 / d.rpm) / rm; }
    }
  };

  function fire(s, g, ctx) {
    if (g.mag <= 0) { s.burst = 0; return; }
    var d = g.def, p = ctx.player, cam = ctx.cam;
    // Torpedo (endgame): the last round of a magazine, fired with 1 left, is a torpedo; guns and rocket launchers, not grenades
    var torpedo = g.mag === 1 && s.fx && s.fx.torpedo && d.cls !== 'grenade' && d.cls !== 'melee' && ctx.torpedo;
    g.mag--;
    var spread = W.spread(s, p) * D2R;
    s.sinceShot = 0; s.shotsInRow++;
    cam.getWorldDirection(_fwd);
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion);
    if (torpedo) ctx.torpedo(d, cam, spread);   // game/launchers.js flies the torpedo
    else if (d.fire === 'rocket' && ctx.rocket) ctx.rocket(d, cam, spread);   // launchers: game/launchers.js flies the rockets
    else for (var k = 0, np = Math.round((d.pellets || 1) * W.tierMods(d).pellets); k < np; k++) {
      var a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.tan(spread);
      _dir.copy(_fwd).addScaledVector(_right, Math.cos(a) * r).addScaledVector(_up, Math.sin(a) * r).normalize();
      ctx.shoot(cam.position, _dir, d, k);
    }
    // recoil: climbs over the first 6 shots of auto weapons
    var climb = d.fire === 'auto' ? 0.55 + 0.45 * Math.min(1, (s.shotsInRow - 1) / 5) : 1;
    var rec = d.recoil * (s.fx.recoilMul || 1) * climb * (s.aim > 0.5 ? 0.75 : 1);
    s.recoilP += rec * D2R;
    s.recoilY += (Math.random() * 2 - 1) * (d.recoilH || 0) * (s.fx.recoilMul || 1) * D2R;
    s.kickZv += 1.6 + rec * 0.5; s.kickRv += 2.0 + rec * 1.2;
    s.flashT = 0.055; s.flashCls = d.id === 'handcannon' ? 'handcannon' : d.cls;
    W.anim(s, 'Fire', { once: true, fade: 0.02 });
    if (IB.Boom) IB.Boom.onFire(s, d);   // shell casing from the EJECT socket, muzzle smoke
    // layered shot per class; heavier guns pitch down, light ones up (+/-4% random per shot)
    var snd = FIRE_SND[d.id] || FIRE_SND[d.cls] || ['gun', 1];
    // rarer guns: a touch deeper and punchier, Epic / Legendary with a bright ring on top (core/gunskins.js FEEL)
    var feel = IB.GunSkins && IB.GunSkins.feel(IB.GunSkins.tierOf(d.id)) || { pitch: 1, gain: 1, ring: 0 };
    IB.Audio && IB.Audio.play(snd[0], { pitch: snd[1] * feel.pitch * (1 + (Math.random() * 0.08 - 0.04)), gain: feel.gain });
    if (feel.ring && IB.Audio) IB.Audio.play('pip', { pitch: 1.9 + Math.random() * 0.1, gain: feel.ring });
    if (ctx.onFire) ctx.onFire(d);
  }

  // quick shove with V when no melee weapon is equipped (20 damage)
  W.shove = function (s) {
    if (s.shoveT > 0) return false;
    s.shoveT = 0.5; s.kickZv -= 3; s.kickRv -= 2;
    return true;
  };

  // world-space muzzle point approximation for tracers
  W.muzzleWorld = function (cam, out) {
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion); cam.getWorldDirection(_fwd);
    return out.copy(cam.position).addScaledVector(_right, 0.16).addScaledVector(_up, -0.13).addScaledVector(_fwd, 0.55);
  };

  /* place viewmodel: lookDX/DY for sway, player for bob/sprint */
  // Viewmodel handling (modern-shooter feel): figure-8 walk bob, look-lag sway with rotation, strafe and jump
  // inertia, landing dip, sprint/slide carry (rig actions), and aim-down-sights that puts the real sights on centre.
  var DEFAULT_SIGHT = { pistol: [0, 0.055, -0.06], smg: [0, 0.075, -0.1], rifle: [0, 0.085, -0.1], sniper: [0, 0.1, -0.1] };
  W.sightOf = function (id) {
    var m = W.models[id]; if (!m) return null;
    if (!m.sight) {
      // scoped weapons aim through the eyepiece; everything else along the iron/red-dot sight line
      var sk = m.mesh.getObjectByName('WPN_' + m.key + '_SCOPE') || m.mesh.getObjectByName('WPN_' + m.key + '_SIGHT');
      m.sight = sk ? sk.position.clone() : new THREE.Vector3().fromArray(DEFAULT_SIGHT[IB.WEAPONS[id].cls] || DEFAULT_SIGHT.rifle);
    }
    return m.sight;
  };
  // Procedural handling per weapon class, layered on top of the Blender rig actions (the authored poses come from
  // HANDLING in Source/blender/fam_weapons.py: pistols sprint at high ready, muzzle up by the face; long guns at
  // low ready across the chest). A class missing here (or a key missing in it) takes the 'rifle' value, so a new
  // weapon gets sane handling from its cls alone.
  //   ads        eye distance (m) behind the sight point when aiming
  //   sprintBob  walk-bob scale while sprinting (eased in/out); the pistol's high-ready action carries its own
  //              footfall bob near the face, so it takes less on top
  //   sprintRoll share of the bob's roll kept while sprinting (a raised pistol rolling about the hip pivot swings wide)
  //   fade       crossfade (s) into and out of the sprint loop (weight: heavier guns take longer to come up)
  //   hipX/Y/Z   extra hip-fire offset (m): the bulky launchers sit lower, further right and further out so they
  //              don't fill the screen or cover the HUD (aiming still lines up the sight)
  var VM_CLASS = {
    pistol: { ads: 0.34, sprintBob: 1.15, sprintRoll: 0.45, fade: 0.18 },
    smg: { ads: 0.27, sprintBob: 1.6, sprintRoll: 1, fade: 0.16 },
    rifle: { ads: 0.29, sprintBob: 1.7, sprintRoll: 1, fade: 0.2, hipX: 0, hipY: 0, hipZ: 0 },
    sniper: { ads: 0.13, fade: 0.22 },
    shotgun: { ads: 0.2 }, rocket: { ads: 0.34, hipX: 0.035, hipY: -0.03, hipZ: -0.16 }
  };
  W.vmClass = function (cls) {
    var c = VM_CLASS[cls] || {}, r = VM_CLASS.rifle, out = {};
    Object.keys(r).forEach(function (k) { out[k] = c[k] !== undefined ? c[k] : r[k]; });
    return out;
  };
  var VM_SCALE = 0.85;
  W.pose = function (s, dt, player, lookDX, lookDY, headBob, t) {
    var g = W.current(s), k = Math.min(1, dt * 10), vc = W.vmClass(g ? g.def.cls : 'rifle');
    if (s.melee) g = null;   // melee swing: the arms play the swing clip; no gun handling, no flash
    s.sprintK = (s.sprintK || 0) + ((player.sprinting ? 1 : 0) - (s.sprintK || 0)) * Math.min(1, dt * 8);
    // look sway lags the camera; clamp so fast flicks don't throw the gun off screen
    s.swayX += ((-lookDX * 0.0007) - s.swayX) * k; s.swayY += ((lookDY * 0.0007) - s.swayY) * k;
    s.swayX = Math.max(-0.06, Math.min(0.06, s.swayX)); s.swayY = Math.max(-0.05, Math.min(0.05, s.swayY));
    // strafe + vertical inertia
    var right = player.vx * Math.cos(player.yaw) - player.vz * Math.sin(player.yaw);
    s.strafe = (s.strafe || 0) + ((right / 6) - (s.strafe || 0)) * Math.min(1, dt * 8);
    s.vert = (s.vert || 0) + ((-player.vy * 0.004) - (s.vert || 0)) * Math.min(1, dt * 10);
    s.vert = Math.max(-0.035, Math.min(0.035, s.vert));
    var a = s.aim, hip = 1 - a;
    var portrait = IB.Render.vmCam.aspect < 1;
    var x = (portrait ? 0.13 : 0.19) + vc.hipX * hip, y = -0.13 + vc.hipY * hip, z = -0.5 + vc.hipZ * hip, rx = 0, ry = 0.06, rz = 0;
    // walk cycle: figure-8 with roll; bigger and faster at sprint
    var hs = Math.hypot(player.vx, player.vz), moving = player.onGround && !player.sliding ? Math.min(1, hs / 6) : 0;
    var amt = (headBob ? 1 : 0.6) * moving * (1 + (vc.sprintBob - 1) * s.sprintK) * (1 - a * 0.85), ph = player.bobT;
    x += Math.sin(ph) * 0.013 * amt; y -= Math.abs(Math.cos(ph)) * 0.011 * amt; ry += Math.cos(ph) * 0.012 * amt;
    rz += Math.sin(ph) * 0.03 * amt * (1 + (vc.sprintRoll - 1) * s.sprintK);
    // idle breathing
    y += Math.sin(t * 1.6) * 0.0028 * hip; rx += Math.sin(t * 1.6 + 1) * 0.004 * hip;
    // inertia
    x -= s.strafe * 0.012 * hip; rz -= s.strafe * 0.05; y += s.vert * hip;
    y -= player.dip * 0.45 + (player.landKick || 0) * 0.03;
    rx += s.swayY * 1.4; ry += s.swayX * 1.6;
    // slide carry: the Slide action (gun tucked low and canted in, support arm out for balance) plus a small lean
    // into the slide on top; procedural only for a weapon without a Slide action. Aiming while sliding keeps the
    // two-hand hold (no Slide clip under the sights).
    var slideClip = g && W.clips[W.models[g.id].key + '_Slide'];
    s.slideK = (s.slideK || 0) + ((player.sliding ? 1 : 0) - (s.slideK || 0)) * Math.min(1, dt * 12);
    if (!slideClip) { rz += 0.5 * s.slideK; x -= 0.03 * s.slideK; y -= 0.035 * s.slideK; }
    else { rz += 0.05 * s.slideK * hip; y -= 0.008 * s.slideK * hip; rx -= 0.02 * s.slideK * hip; }
    // aim down sights: blend toward the pose that puts the sight point on the screen centre
    if (g && a > 0.001) {
      var sp = W.sightOf(g.id);
      var ax = -sp.x * VM_SCALE, ay = -sp.y * VM_SCALE, az = -(g.def.adsDist || vc.ads) - sp.z * VM_SCALE;   // adsDist: a mounted scope's eye relief
      x += (ax - x) * a; y += (ay - y) * a; z += (az - z) * a;
      rx *= hip * 0.6 + 0.4 * (1 - a); ry *= hip; rz *= hip * 0.7 + 0.3;
    }
    // arm animation: once-clips (draw, fire, reload, holster) fall back to the Idle / Sprint / Slide loop
    if (s.melee && W.mixer) W.mixer.update(dt);
    if (g && W.mixer) {
      var want = player.sliding && slideClip && a < 0.5 ? 'Slide' : (player.sprinting ? 'Sprint' : 'Idle');
      var busy = W.animOnce && W.action && W.action.isRunning();
      if (!busy && W.animName !== want && s.state !== 'holster') W.anim(s, want, { fade: want === 'Slide' || W.animName === 'Slide' ? 0.12 : (want === 'Sprint' || W.animName === 'Sprint' ? vc.fade : 0.14) });
      W.mixer.update(dt);
    }
    // recoil kick (spring) on top
    z += s.kickZ * 0.02 * (1 - a * 0.5); rx += s.kickR * 0.03 * (1 - a * 0.4);
    W.vmRoot.position.set(x + s.swayX * hip, y + s.swayY * hip, z);
    W.vmRoot.rotation.set(rx, ry, rz);
    W.vmRoot.scale.setScalar(VM_SCALE);
    W.vmRoot.visible = (!!g || !!s.melee) && !s.hidden;
    if (IB.GunSkins) { IB.GunSkins.tick(s.t); if (g) skinModel(s.cur); }
    if (!g) W.flash.visible = false;
    if (g) {
      W.flash.visible = s.flashT > 0 && s.aim < 0.3;   // never over the sights when aiming
      if (W.flash.visible) {
        var cls = s.flashCls || g.def.cls, big = s.flashT > 0.028 ? 1 : 0.62;   // frame 1 full, frame 2 smaller
        W.flash.position.set(0, 0, -0.03);
        W.flash.rotation.z = Math.random() * 6.28;
        var fs = (FLASH_SCALE[cls] || 1) * (0.85 + Math.random() * 0.4) * big; W.flash.scale.set(fs, fs, fs);
        W.flashSide.visible = !!FLASH_SIDE[cls]; W.flashSide.rotation.z = -W.flash.rotation.z + (Math.random() - 0.5) * 0.3;   // flares stay level
        W.flashCone.visible = big === 1;
      }
    }
  };
})(window.IB = window.IB || {});
