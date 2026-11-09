/* INKBOLT gun levels, launcher rolls and the rocket ammo director. Pure, no DOM (unit-tested).

   GUN LEVELS. Every gun has an item level: a dropped gun the campaign level it dropped on, a rack / stand gun the
   level it was taken on (saved per gun in slot.gunLevel; older saves give their guns the highest level cleared).
   Damage x mul(level) = 1 + 0.055 (L - 1): x1.72 on 14, x2.10 on 21, x2.60 on 30. Robot health grows
   x(1 + 0.06 (L - 1)) (IB.Damage.enemyHpMul), so a fresh gray gun at level L takes 0-5% more hits on a level-L robot
   than a fresh gray gun did on level 1; its tier (x1.00-1.32), the Upgrade Bench and skills put it ahead.
   Owned guns never fall hopelessly behind: a gun counts as at least (player level - 4, the player level capped at the
   level being played) (`effective`), i.e. about 8%
   fewer damage than a fresh drop late in the game, so new drops stay worth picking up without the old favourite
   becoming useless. The melee weapons (no item level) ride that floor alone.
   A pickup of a gun you own replaces yours when its power (tier x level, launchers also their magazine) beats the
   power your gun has now (effective level); otherwise it is broken down into gems (tier value, as before).

   LAUNCHERS (data/weapons.js `ammo: 'rocket'`): a magazine size rolled per drop (magRoll) and, for the Hothead,
   an element (IB.LAUNCHER_ELEMENTS). They drop from robots on campaign level LAUNCHER_LEVEL (14) and later only
   (i.e. after level 13 is beaten), take no mods, and use rocket ammo, a pool of its own (slot.rockets).

   ROCKET AMMO DIRECTOR. Only soldiers drop rocket crates, and only while the player needs them: need = how far the
   rocket pool (plus crates lying on the map) is below a target (70% of the cap when a launcher is carried, 30%
   when one is only in the backpack, nothing without one), weighted by recent use (rockets fired in the last 90 s).
   A soldier kill drops a crate with chance 0.5 x need, 2-5 rockets (more when the need is bigger); a carried
   launcher with fewer than one salvo left gets a crate after at most 3 soldier kills without one. Never more than
   the level's budget (0.27 rockets per soldier, at least 14): rockets stay a fraction of normal ammo. */
(function (IB) {
  'use strict';
  var GL = {};
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }

  // ---------------- gun levels ----------------
  GL.STEP = 0.055; GL.CATCHUP = 4; GL.MAX = 40;
  GL.mul = function (L) { return 1 + GL.STEP * (clamp(Math.round(+L || 1), 1, GL.MAX) - 1); };
  /* the level a gun fights at: its own, or 4 below the player level when that is higher. The floor never runs ahead of
     the campaign level being played (planLv; the player level is XP-based and can outrun it). */
  GL.effective = function (own, playerLv, planLv) {
    var ref = Math.min(playerLv || 1, planLv || playerLv || 1);
    return clamp(Math.max(Math.round(+own || 1), ref - GL.CATCHUP), 1, GL.MAX);
  };
  GL.power = function (tierMul, level) { return (tierMul || 1) * GL.mul(level); };
  /* a gun from an older save (no level yet): the highest level cleared */
  GL.defaultLevel = function (highest) { return clamp(Math.round(+highest || 0), 1, GL.MAX); };
  /* give every arsenal gun without a level one (saves.js migrate, game level start); returns the slot */
  GL.fill = function (slot) {
    if (!slot) return slot;
    if (!slot.gunLevel || typeof slot.gunLevel !== 'object' || Array.isArray(slot.gunLevel)) slot.gunLevel = {};
    var d = GL.defaultLevel(slot.highest);
    (slot.arsenal || []).forEach(function (id) { var v = slot.gunLevel[id]; if (typeof v !== 'number' || !(v >= 1)) slot.gunLevel[id] = d; });
    if (!slot.gunRoll || typeof slot.gunRoll !== 'object' || Array.isArray(slot.gunRoll)) slot.gunRoll = {};
    if (typeof slot.rockets !== 'number' || !(slot.rockets >= 0)) slot.rockets = 0;
    return slot;
  };

  // ---------------- launchers ----------------
  GL.LAUNCHER_LEVEL = 14;
  GL.isLauncher = function (def) { return !!(def && def.ammo === 'rocket'); };
  GL.launchers = function () { return Object.keys(IB.WEAPONS || {}).filter(function (k) { return GL.isLauncher(IB.WEAPONS[k]); }); };
  function elements() { return IB.LAUNCHER_ELEMENTS || { none: { id: 'none', name: '', weight: 1 } }; }
  GL.element = function (id) { var E = elements(); return E[id] || E.none; };
  /* a fresh launcher's roll: {mag, elem} (elem 'none' for launchers without elements) */
  GL.rollLauncher = function (def, rng) {
    rng = rng || Math.random;
    var r = def.magRoll || [def.mag, def.mag], mag = r[0] + Math.floor(rng() * (r[1] - r[0] + 1));
    var elem = 'none';
    if (def.elements) {
      var E = elements(), ks = Object.keys(E), tot = 0, i;
      for (i = 0; i < ks.length; i++) tot += E[ks[i]].weight || 0;
      var x = rng() * tot;
      for (i = 0; i < ks.length; i++) { x -= E[ks[i]].weight || 0; if (x < 0) { elem = ks[i]; break; } }
    }
    return { mag: clamp(mag, r[0], r[1]), elem: elem };
  };
  /* a Wyrmforged gun's roll: {mag, mult}. mag 8-13, higher at higher player levels (LV 1 -> low, LV 30 -> high);
     mult 2 or 3 (the damage multiplier). */
  GL.wyrmRoll = function (def, playerLv, rng) {
    rng = rng || Math.random;
    var R = def.wyrm, lvF = (clamp(Math.round(+playerLv) || 1, 1, 30) - 1) / 29;
    var mag = Math.round(R.mag[0] + (R.mag[1] - R.mag[0]) * clamp(0.6 * rng() + 0.4 * lvF, 0, 1));
    return { mag: mag, mult: rng() < 0.5 ? R.mult[0] : R.mult[1] };
  };
  GL.fixWyrm = function (def, roll) {
    var R = def.wyrm, o = roll || {};
    return { mag: clamp(Math.round(+o.mag || R.mag[0]), R.mag[0], R.mag[1]), mult: +o.mult === R.mult[1] ? R.mult[1] : R.mult[0] };
  };
  GL.fixRoll = function (def, roll) {
    var r = def.magRoll || [def.mag, def.mag], o = roll || {};
    return { mag: clamp(Math.round(+o.mag || def.mag), r[0], r[1]), elem: def.elements && elements()[o.elem] ? o.elem : 'none' };
  };
  /* power of a gun for "is this pickup better": tier x level, launchers x (mag / base mag)^0.35 */
  GL.score = function (def, tierMul, level, roll) {
    var p = GL.power(tierMul, level);
    if (GL.isLauncher(def) && roll) p *= Math.pow((roll.mag || def.mag) / def.mag, 0.35);
    return p;
  };
  GL.displayName = function (def, roll) {
    if (!def) return '';
    var e = def.elements && roll ? GL.element(roll.elem) : null;
    if (!(e && e.name)) return def.name;
    var p = def.name.split(' ');   // 'RL-3 Hothead' + Volt -> 'Volt Hothead' (fits the HUD plate)
    return e.name + ' ' + (p.length > 1 ? p.slice(1).join(' ') : def.name);
  };
  /* chance that a player kill on campaign level L drops a launcher (soldiers more often), and which one */
  GL.LAUNCHER_DROP = { soldier: 0.012, other: 0.0016 };   // doubled with the other guns
  GL.launcherDropChance = function (type, L) {
    if ((L || 0) < GL.LAUNCHER_LEVEL) return 0;
    return type === 'soldier' ? GL.LAUNCHER_DROP.soldier : GL.LAUNCHER_DROP.other;
  };
  GL.LAUNCHER_TIERS = { gray: 50, green: 28, blue: 15, purple: 5.5, orange: 1.5 };
  GL.RACK_LAUNCHER = 0.03;   // share of armory rack guns that are a launcher (levels 14+)

  // ---------------- rocket ammo director ----------------
  GL.ROCKET = { cap: 16, start: 6, carriedTarget: 0.7, packTarget: 0.3, useWindow: 90, useFull: 6, maxChance: 0.5, pity: 3,
    budgetPerSoldier: 0.27, minBudget: 14, dropWeight: { soldier: 1, blader: 0.5 } };
  /* which kills can drop a rocket crate, and how often vs a soldier (melee bladers: half the chance) */
  GL.rocketDropWeight = function (type) { return GL.ROCKET.dropWeight[type] || 0; };
  /* st: {owned, carried, ammo, pending (rockets in crates on the map), used (rockets fired in the last 90 s), per
     (rockets a shot of the carried launcher takes)} -> 0..1 */
  GL.rocketNeed = function (st) {
    var R = GL.ROCKET;
    if (!st || !st.owned) return 0;
    var have = (st.ammo || 0) + (st.pending || 0);
    if (have >= R.cap) return 0;
    var target = R.cap * (st.carried ? R.carriedTarget : R.packTarget);
    if (have >= target) return 0;
    var need = 1 - have / target, use = clamp((st.used || 0) / R.useFull, 0, 1);
    need *= st.carried ? 0.55 + 0.45 * use : 0.5;
    return clamp(need, 0, 1);
  };
  /* rockets the director may drop on a level (soldier count; bladers also drop crates now, but share this same
     budget, so a level's rocket economy is unchanged) */
  GL.rocketBudget = function (soldiers) { return Math.max(GL.ROCKET.minBudget, Math.round((soldiers || 0) * GL.ROCKET.budgetPerSoldier)); };
  /* one soldier kill: rockets in the crate it drops (0 = none). st also: dry (soldier kills since the last crate),
     dropped (rockets dropped this level), budget, w (drop weight of the killed robot, default 1: a blader 0.5) */
  GL.rocketDrop = function (st, rng) {
    rng = rng || Math.random;
    var R = GL.ROCKET, need = GL.rocketNeed(st);
    if (need <= 0) return 0;
    var left = (st.budget === undefined ? Infinity : st.budget) - (st.dropped || 0);
    if (left <= 0) return 0;
    var have = (st.ammo || 0) + (st.pending || 0);
    var pity = st.carried && have < (st.per || 1) && (st.dry || 0) >= R.pity - 1;
    var w = st.w === undefined ? 1 : st.w;
    if (w <= 0) return 0;
    if (!pity && rng() >= R.maxChance * need * w) return 0;
    return Math.max(1, Math.min(R.cap - have, left, 2 + Math.round(3 * need)));
  };

  // ---------------- balance helpers (unit-tested intent) ----------------
  /* damage of one shot on the robot it is aimed at (body hit, no crits): direct + full splash; salvo for the Murmur */
  GL.shotDamage = function (def) {
    if (GL.isLauncher(def)) return (def.missiles || 1) * ((def.damage || 0) + (def.splash || 0));
    return (def.damage || 0) * (def.pellets || 1) * (def.burst > 1 ? def.burst : 1);
  };
  /* single-target damage per second over a full magazine + reload */
  GL.sustainedDps = function (def, mag) {
    mag = mag || def.mag;
    var perShot = GL.shotDamage(def), shots = def.burst > 1 ? mag / def.burst : mag;
    var cyc = def.cycle || 60 / def.rpm;
    var reload = def.reloadPerShell ? def.reload * mag : def.reload;
    return perShot * shots / (shots * cyc + reload);
  };

  IB.GunLevel = GL;
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
