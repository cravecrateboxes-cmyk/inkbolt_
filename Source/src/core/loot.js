/* INKBOLT - loot logic (pure, no DOM): drop rolls, item stat generation, attachment compatibility, weapon
   modifiers, player shield math and the gear inventory stored in the save slot (slot.gear).
   rng: a function returning [0, 1) (Math.random in the game, a seeded RNG in tests). */
(function (IB) {
  'use strict';

  function T() { return IB.LOOT; }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function roundTo(x, step) { if (!step) return x; var k = Math.round(x / step) * step; return +k.toFixed(step < 1 ? String(step).split('.')[1].length : 0); }
  function pickWeighted(list, rng) {
    var sum = 0, i; for (i = 0; i < list.length; i++) sum += list[i].weight;
    var r = rng() * sum;
    for (i = 0; i < list.length; i++) { r -= list[i].weight; if (r < 0) return list[i]; }
    return list[list.length - 1];
  }

  // campaign-level stat growth: x(1 + k (L - 1)), capped
  function levelMul(kind, L) {
    var s = T().levelScale[kind]; if (!s) return 1;
    return Math.min(s[1], 1 + s[0] * Math.max(0, (L || 1) - 1));
  }

  /* ctx: {cleared} = highest campaign level completed. Shields need cleared >= minCleared. */
  function allowedTypes(ctx) {
    var cleared = (ctx && ctx.cleared) || 0, out = [];
    Object.keys(T().types).forEach(function (k) { var t = T().types[k]; if (!t.minCleared || cleared >= t.minCleared) out.push(t); });
    return out;
  }
  function rollType(rng, ctx) { return pickWeighted(allowedTypes(ctx), rng).id; }
  function rollRarity(rng) { return pickWeighted(T().rarities, rng).id; }

  /* one item, stats generated now: type id, rarity id, campaign level */
  function makeItem(type, rarity, level, rng) {
    var td = T().types[type], L = Math.max(1, level || 1);
    var item = { type: type, rarity: rarity, level: L, name: td.names[rarity], stats: {} };
    Object.keys(td.stats).forEach(function (k) {
      var s = td.stats[k], r = s[rarity], v = r[0] + (r[1] - r[0]) * rng();
      if (s.scale) v *= levelMul(s.scale, L);
      if (s.max !== undefined) v = Math.min(s.max, v);
      item.stats[k] = roundTo(v, s.round);
    });
    if (type === 'scope') item.name += ' ' + item.stats.zoom.toFixed(1) + 'x';
    return item;
  }

  /* ctx: {level, cleared, chance?}; returns a new item or null (no drop) */
  function rollDrop(rng, ctx) {
    var chance = ctx && ctx.chance !== undefined ? ctx.chance : T().dropChance;
    if (rng() >= chance) return null;
    return makeItem(rollType(rng, ctx), rollRarity(rng), ctx && ctx.level, rng);
  }

  function pct(x) { return Math.round(x * 100) + '%'; }
  /* display lines [{k, v}] for HUD toasts and the gear panel */
  /* acid muzzles from saves made before the long burn (2 / 2.5 / 3 s) read as the new ones (5 / 6 / 7 s, +20% acid) */
  function acidStats(st) {
    if (st.dur < 4) return { acid: Math.round(st.acid * 1.2 * 100) / 100, dur: st.dur * 2 + 1 };
    return { acid: st.acid, dur: st.dur };
  }
  function statLines(item) {
    var s = item.stats;
    switch (item.type) {
      case 'shield': return [{ k: 'Capacity', v: String(s.capacity) }, { k: 'Recharge', v: s.rate + '/s' }, { k: 'Delay', v: s.delay.toFixed(1) + ' s' }];
      case 'grip': return [{ k: 'Recoil', v: '-' + pct(s.recoil) }, { k: 'Spread', v: '-' + pct(s.spread) }];
      case 'scope': return [{ k: 'Zoom', v: s.zoom.toFixed(1) + 'x' }, { k: 'Aim spread', v: '-' + pct(s.aimSpread) }];
      case 'acid': var ac = acidStats(s); return [{ k: 'Acid', v: '+' + pct(ac.acid) + ' over ' + ac.dur.toFixed(1) + ' s' }, { k: 'Noise', v: '-' + pct(1 - T().types.acid.quiet) }];
    }
    return [];
  }
  function summary(item) { return statLines(item).map(function (l) { return l.k + ' ' + l.v; }).join(' · '); }

  // ---------------- attachments ----------------
  function slotOf(item) { return item ? T().types[item.type].slot : null; }
  function isAttachment(item) { var s = slotOf(item); return s === 'grip' || s === 'scope' || s === 'muzzle'; }
  /* can this attachment go on weapon id with def? (class list; scopes never on weapons that already have optics) */
  function compatible(item, id, def) {
    if (!item || !def || !isAttachment(item)) return false;
    var td = T().types[item.type];
    if (td.classes && td.classes.indexOf(def.cls) < 0) return false;
    if (td.noScoped && (def.scopeZoom > 0 || (IB.SCOPED_WEAPONS && IB.SCOPED_WEAPONS.indexOf(id) >= 0))) return false;
    return true;
  }
  function slotsFor(id, def) {
    return T().slots.filter(function (sl) {
      return Object.keys(T().types).some(function (k) { var td = T().types[k]; return td.slot === sl && compatible({ type: k }, id, def); });
    });
  }

  /* weapon def with attachments applied (a new object; the table entry is left alone).
     mods: {grip?, scope?, muzzle?} items */
  function applyMods(def, mods) {
    var d = {}, k;
    for (k in def) d[k] = def[k];
    mods = mods || {};
    var g = mods.grip, s = mods.scope, m = mods.muzzle;
    d.base = def; d.mods = {};
    if (g && g.type === 'grip') {
      var rk = 1 - g.stats.recoil, sk = 1 - g.stats.spread;
      d.recoil = def.recoil * rk; d.recoilH = (def.recoilH || 0) * rk;
      d.spreadHip = def.spreadHip * sk; d.spreadAim = def.spreadAim * sk;
      d.mods.grip = g;
    }
    if (s && s.type === 'scope') {
      d.spreadAim = d.spreadAim * (1 - s.stats.aimSpread);
      d.aimZoom = Math.min(def.aimZoom || 0.85, 1 / s.stats.zoom);
      d.optic = true;
      d.mods.scope = s;
    }
    if (m && m.type === 'acid') {
      var as = acidStats(m.stats); d.acid = as.acid; d.acidDur = as.dur; d.quiet = T().types.acid.quiet;
      d.mods.muzzle = m;
    }
    return d;
  }

  // ---------------- player shield ----------------
  /* state from an equipped shield item (or null): starts full */
  function shieldState(item) {
    if (!item || item.type !== 'shield') return null;
    return { max: item.stats.capacity, cur: item.stats.capacity, delay: item.stats.delay, rate: item.stats.rate, since: 99, charging: false };
  }
  /* damage hits the shield first; returns {through, absorbed, broke} and resets the recharge delay */
  function absorb(st, dmg) {
    if (!st || dmg <= 0) return { through: dmg, absorbed: 0, broke: false };
    st.since = 0; st.charging = false;
    var a = Math.min(st.cur, dmg), had = st.cur > 0;
    st.cur -= a;
    return { through: dmg - a, absorbed: a, broke: had && st.cur <= 0 };
  }
  /* advance time: returns 'start' when recharging begins, 'full' when it tops up, else null */
  function tickShield(st, dt) {
    if (!st) return null;
    st.since += dt;
    if (st.cur >= st.max) { st.cur = st.max; var was = st.charging; st.charging = false; return was ? 'full' : null; }
    if (st.since < st.delay) return null;
    var ev = st.charging ? null : 'start';
    st.charging = true;
    st.cur = Math.min(st.max, st.cur + st.rate * dt);
    if (st.cur >= st.max) { st.charging = false; return 'full'; }
    return ev;
  }

  // ---------------- inventory (slot.gear) ----------------
  function defaultGear() { return { inv: [], shield: null, attach: {}, next: 1, found: 0 }; }
  function isObj(o) { return o !== null && typeof o === 'object' && !Array.isArray(o); }
  /* repair a stored gear object: drops unknown item types and dangling references */
  function migrateGear(g) {
    var d = defaultGear();
    if (!isObj(g)) return d;
    var out = { inv: [], shield: null, attach: {}, next: typeof g.next === 'number' ? g.next : 1, found: typeof g.found === 'number' ? g.found : 0 };
    if (g.starter === true) out.starter = true;   // the level-3 starter shield was handed out
    var ids = {};
    (Array.isArray(g.inv) ? g.inv : []).forEach(function (it) {
      if (!isObj(it) || !T().types[it.type] || !T().rarityById[it.rarity] || !isObj(it.stats) || ids[it.id]) return;
      ids[it.id] = true; out.inv.push(it);
      var n = parseInt(String(it.id).replace(/\D/g, ''), 10); if (n >= out.next) out.next = n + 1;
    });
    if (g.shield && ids[g.shield] && find(out, g.shield).type === 'shield') out.shield = g.shield;
    if (isObj(g.attach)) Object.keys(g.attach).forEach(function (w) {
      var a = g.attach[w]; if (!isObj(a)) return;
      T().slots.forEach(function (sl) { var it = a[sl] && find(out, a[sl]); if (it && slotOf(it) === sl) { out.attach[w] = out.attach[w] || {}; out.attach[w][sl] = it.id; } });
    });
    return out;
  }
  function find(g, id) { for (var i = 0; i < g.inv.length; i++) if (g.inv[i].id === id) return g.inv[i]; return null; }
  /* add a rolled item; returns it with an id, or null when the bag is full */
  function addItem(g, item) {
    if (g.inv.length >= T().invCap) return null;
    item.id = 'g' + (g.next++);
    g.inv.push(item); g.found = (g.found || 0) + 1;
    return item;
  }
  function attachedTo(g, id) {
    for (var w in g.attach) for (var sl in g.attach[w]) if (g.attach[w][sl] === id) return { weapon: w, slot: sl };
    return null;
  }
  function weaponItems(g, wid) {
    var a = g.attach[wid] || {}, out = {};
    T().slots.forEach(function (sl) { if (a[sl]) { var it = find(g, a[sl]); if (it) out[sl] = it; } });
    return out;
  }
  function equipShield(g, id) { var it = id && find(g, id); if (id && (!it || it.type !== 'shield')) return false; g.shield = id || null; return true; }
  /* attach item id to weapon wid (def for compatibility); moves it off any other weapon, replaces what was there */
  function attach(g, wid, def, id) {
    var it = find(g, id); if (!it || !compatible(it, wid, def)) return false;
    var at = attachedTo(g, id); if (at) delete g.attach[at.weapon][at.slot];
    g.attach[wid] = g.attach[wid] || {};
    g.attach[wid][slotOf(it)] = id;
    return true;
  }
  function detach(g, wid, slot) { if (g.attach[wid] && g.attach[wid][slot]) { delete g.attach[wid][slot]; return true; } return false; }
  function discard(g, id) {
    var i = -1; for (var k = 0; k < g.inv.length; k++) if (g.inv[k].id === id) i = k;
    if (i < 0) return false;
    g.inv.splice(i, 1);
    if (g.shield === id) g.shield = null;
    var at = attachedTo(g, id); if (at) delete g.attach[at.weapon][at.slot];
    return true;
  }
  /* weapons that are no longer carried lose their attachments (the items stay in the bag) */
  function prune(g, owned) { Object.keys(g.attach).forEach(function (w) { if (owned.indexOf(w) < 0) delete g.attach[w]; }); }
  function rarityRank(id) { return { common: 0, rare: 1, epic: 2 }[id] || 0; }

  IB.Loot = {
    levelMul: levelMul, allowedTypes: allowedTypes, rollType: rollType, rollRarity: rollRarity, makeItem: makeItem, rollDrop: rollDrop,
    acidStats: acidStats, statLines: statLines, summary: summary, slotOf: slotOf, isAttachment: isAttachment, compatible: compatible, slotsFor: slotsFor,
    applyMods: applyMods, shieldState: shieldState, absorb: absorb, tickShield: tickShield,
    defaultGear: defaultGear, migrateGear: migrateGear, find: find, addItem: addItem, attachedTo: attachedTo, weaponItems: weaponItems,
    equipShield: equipShield, attach: attach, detach: detach, discard: discard, prune: prune, rarityRank: rarityRank, clamp: clamp
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
