/* INKBOLT - loot logic (pure, no DOM): drop rolls (rarity odds by campaign level), item stat generation, shield
   perks, attachment compatibility, weapon modifiers, player shield and vest math and the gear inventory stored in
   the save slot (slot.gear: inv, attach {weapon: {slot: id}}, and one id per worn slot: shield, armor).
   rng: a function returning [0, 1) (Math.random in the game, a seeded RNG in tests). */
(function (IB) {
  'use strict';

  function T() { return IB.LOOT; }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function roundTo(x, step) { if (!step) return x; var k = Math.round(x / step) * step; return +k.toFixed(step < 1 ? String(step).split('.')[1].length : 0); }
  function pickWeighted(list, rng) {
    var sum = 0, i; for (i = 0; i < list.length; i++) sum += list[i].weight;
    var r = rng() * sum;
    for (i = 0; i < list.length; i++) { r -= list[i].weight; if (r < 0 && list[i].weight > 0) return list[i]; }
    for (i = list.length - 1; i >= 0; i--) if (list[i].weight > 0) return list[i];
    return list[list.length - 1];
  }

  // campaign-level stat growth: x(1 + k (min(L, knee) - 1) + k2 max(0, L - knee)), capped (data/loot.js)
  function levelMul(kind, L) {
    var s = T().levelScale[kind]; if (!s) return 1;
    L = Math.max(1, L || 1);
    return Math.min(s.cap, 1 + s.k * (Math.min(L, s.knee) - 1) + s.k2 * Math.max(0, L - s.knee));
  }

  /* ctx: {cleared} = highest campaign level completed. Shields / vests need cleared >= minCleared. */
  function allowedTypes(ctx) {
    var cleared = (ctx && ctx.cleared) || 0, out = [];
    Object.keys(T().types).forEach(function (k) { var t = T().types[k]; if (!t.minCleared || cleared >= t.minCleared) out.push(t); });
    return out;
  }
  function rollType(rng, ctx) { return pickWeighted(allowedTypes(ctx), rng).id; }
  /* rarity odds (percent per rarity, LOOT.rarities order) for campaign level L: the LOOT.rarityOdds row with the
     highest `from` <= L */
  function rarityOdds(L) {
    var rows = T().rarityOdds, w = rows[0].w;
    L = Math.max(1, L || 1);
    for (var i = 0; i < rows.length; i++) if (rows[i].from <= L) w = rows[i].w;
    return w;
  }
  function rollRarity(rng, level) {
    var w = rarityOdds(level), list = T().rarities.map(function (r, i) { return { id: r.id, weight: w[i] || 0 }; });
    return pickWeighted(list, rng).id;
  }

  /* the perk of a shield item, rolled now (Epic / Legendary only): {id, v, radius?, secs?} or null */
  function rollPerk(type, rarity, L, rng) {
    var td = T().types[type];
    if (!td || !td.perks || T().perkFrom.indexOf(rarity) < 0) return null;
    var pd = T().perks[td.perks[Math.min(td.perks.length - 1, Math.floor(rng() * td.perks.length))]], r = pd.v[rarity];
    var v = r[0] + (r[1] - r[0]) * rng();
    if (pd.scale) v *= levelMul(pd.scale, L);
    var p = { id: pd.id, v: roundTo(v, pd.round) };
    if (pd.radius) p.radius = pd.radius[rarity];
    if (pd.secs) p.secs = pd.secs;
    return p;
  }

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
    var perk = rollPerk(type, rarity, L, rng);
    if (perk) item.perk = perk;
    return item;
  }

  /* ctx: {level, cleared, chance?}; returns a new item or null (no drop) */
  function rollDrop(rng, ctx) {
    var chance = ctx && ctx.chance !== undefined ? ctx.chance : T().dropChance;
    if (rng() >= chance) return null;
    var type = rollType(rng, ctx);
    return makeItem(type, rollRarity(rng, ctx && ctx.level), ctx && ctx.level, rng);
  }
  /* Blender model node for an item ({type, rarity}): shield cells have one per rarity */
  function modelOf(item) {
    var td = item && T().types[item.type]; if (!td) return null;
    return (td.models && (td.models[item.rarity] || td.models.common)) || td.model || null;
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
      case 'shock': return [{ k: 'Arc chance', v: pct(s.chance) }, { k: 'Shock', v: '+' + pct(s.arc) + ', jumps 5 m' }];
      case 'blast': return [{ k: 'Blast chance', v: pct(s.chance) }, { k: 'Blast', v: 'x' + s.power.toFixed(2) + ' hit, 2.4 m' }];
      case 'void': return [{ k: 'Pull chance', v: pct(s.chance) }, { k: 'Pull radius', v: s.radius.toFixed(1) + ' m' }];
      case 'mag': return [{ k: 'Magazine', v: '+' + pct(s.mag) }, { k: 'Reload', v: '-' + pct(s.reload) }];
      case 'armor': return [{ k: 'Armour', v: '-' + pct(s.dr) + ' dmg' }, { k: 'Max health', v: '+' + s.hp }];
    }
    return [];
  }
  function summary(item) { return statLines(item).map(function (l) { return l.k + ' ' + l.v; }).join(' · '); }
  /* the shield perk as {id, name, short, text} (or null) */
  function perkLine(item) {
    var p = item && item.perk, pd = p && T().perks[p.id]; if (!pd) return null;
    if (p.id === 'overcharge') return { id: p.id, name: pd.name, short: '+' + pct(p.v) + ' recharge on kill', text: 'A kill starts the recharge at once, ' + pct(p.v) + ' faster for ' + (p.secs || pd.secs) + ' s' };
    if (p.id === 'nova') return { id: p.id, name: pd.name, short: p.v + ' shock burst, ' + p.radius + ' m', text: 'When the cell breaks: a shock burst, ' + p.v + ' damage to robots within ' + p.radius + ' m and a stagger (once per charge)' };
    return { id: p.id, name: pd.name, short: '', text: '' };
  }

  // ---------------- attachments ----------------
  function slotOf(item) { var td = item && T().types[item.type]; return td ? td.slot : null; }
  function isAttachment(item) { return T().slots.indexOf(slotOf(item)) >= 0; }
  function isWorn(item) { return T().worn.indexOf(slotOf(item)) >= 0; }
  /* the item type that fills a slot (the first one: muzzle -> acid), for empty-slot pictures */
  function typeForSlot(sl) { var ks = Object.keys(T().types); for (var i = 0; i < ks.length; i++) if (T().types[ks[i]].slot === sl) return ks[i]; return sl; }
  /* can this attachment go on weapon id with def? (class list; scopes never on weapons that already have optics;
     `noActions`: no magazine on a revolver) */
  function compatible(item, id, def) {
    if (!item || !def || !isAttachment(item)) return false;
    var td = T().types[item.type];
    if (td.classes && td.classes.indexOf(def.cls) < 0) return false;
    if (td.noScoped && (def.scopeZoom > 0 || (IB.SCOPED_WEAPONS && IB.SCOPED_WEAPONS.indexOf(id) >= 0))) return false;
    if (td.noActions && def.action && td.noActions.indexOf(def.action) >= 0) return false;
    return true;
  }
  function slotsFor(id, def) {
    return T().slots.filter(function (sl) {
      return Object.keys(T().types).some(function (k) { var td = T().types[k]; return td.slot === sl && compatible({ type: k }, id, def); });
    });
  }

  /* weapon def with attachments applied (a new object; the table entry is left alone).
     mods: {grip?, scope?, muzzle?, mag?} items */
  function applyMods(def, mods) {
    var d = {}, k;
    for (k in def) d[k] = def[k];
    mods = mods || {};
    var g = mods.grip, s = mods.scope, m = mods.muzzle, mg = mods.mag;
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
    if (m && (m.type === 'shock' || m.type === 'blast' || m.type === 'void')) { d.can = { type: m.type, stats: m.stats }; d.mods.muzzle = m; }
    // extended mag: more rounds (always at least one more), shorter reload
    if (mg && mg.type === 'mag' && def.mag > 0) {
      d.mag = Math.max(def.mag + 1, Math.round(def.mag * (1 + mg.stats.mag)));
      d.reload = def.reload * (1 - mg.stats.reload);
      d.mods.mag = mg;
    }
    return d;
  }

  // ---------------- player shield ----------------
  /* state from an equipped shield item (or null): starts full. perk: {id, v, radius?, secs?} (Epic / Legendary);
     nova: the Nova burst is armed (set while the cell is full, used up when it breaks);
     boostT / boost: Overcharge seconds left / recharge bonus */
  function shieldState(item) {
    if (!item || item.type !== 'shield') return null;
    return { max: item.stats.capacity, cur: item.stats.capacity, delay: item.stats.delay, rate: item.stats.rate, since: 99, charging: false,
      rarity: item.rarity, perk: item.perk || null, nova: !!(item.perk && item.perk.id === 'nova'), boostT: 0, boost: 0 };
  }
  /* damage hits the shield first; returns {through, absorbed, broke, nova} and resets the recharge delay
     (nova: this hit broke an armed Nova cell: the game fires the burst) */
  function absorb(st, dmg) {
    if (!st || dmg <= 0) return { through: dmg, absorbed: 0, broke: false, nova: false };
    st.since = 0; st.charging = false; st.boostT = 0;
    var a = Math.min(st.cur, dmg), had = st.cur > 0;
    st.cur -= a;
    var broke = had && st.cur <= 0, nova = broke && st.nova === true;
    if (nova) st.nova = false;
    return { through: dmg - a, absorbed: a, broke: broke, nova: nova };
  }
  /* Overcharge: a kill starts the recharge at once (the delay is skipped) and speeds it up for a few seconds.
     Returns true when it did something (the cell was not full). */
  function shieldKill(st) {
    if (!st || !st.perk || st.perk.id !== 'overcharge' || st.cur >= st.max) return false;
    st.since = Math.max(st.since, st.delay);
    st.boostT = st.perk.secs || T().perks.overcharge.secs; st.boost = st.perk.v;
    return true;
  }
  /* advance time: returns 'start' when recharging begins, 'full' when it tops up, else null */
  function tickShield(st, dt) {
    if (!st) return null;
    st.since += dt;
    if (st.boostT > 0) st.boostT = Math.max(0, st.boostT - dt);
    var novaCell = st.perk && st.perk.id === 'nova';
    if (st.cur >= st.max) { st.cur = st.max; if (novaCell) st.nova = true; var was = st.charging; st.charging = false; return was ? 'full' : null; }
    if (st.since < st.delay) return null;
    var ev = st.charging ? null : 'start';
    st.charging = true;
    st.cur = Math.min(st.max, st.cur + st.rate * (st.boostT > 0 ? 1 + (st.boost || 0) : 1) * dt);
    if (st.cur >= st.max) { st.charging = false; if (novaCell) st.nova = true; return 'full'; }
    return ev;
  }

  // ---------------- vest ----------------
  /* {dr, hp} of a worn vest (zeros without one) */
  function armorOf(item) {
    if (!item || item.type !== 'armor') return { dr: 0, hp: 0 };
    return { dr: clamp(item.stats.dr || 0, 0, T().types.armor.stats.dr.max), hp: Math.max(0, item.stats.hp || 0) };
  }
  /* damage that reaches health through the vest */
  function armorCut(item, dmg) { return dmg * (1 - armorOf(item).dr); }

  // ---------------- inventory (slot.gear) ----------------
  function defaultGear() { return { inv: [], shield: null, armor: null, attach: {}, next: 1, found: 0 }; }
  function isObj(o) { return o !== null && typeof o === 'object' && !Array.isArray(o); }
  /* repair a stored gear object: drops unknown item types and dangling references (saves from before the vest have
     no `armor`: it starts empty; a stored perk that is not known is dropped) */
  function migrateGear(g) {
    var d = defaultGear();
    if (!isObj(g)) return d;
    var out = { inv: [], shield: null, armor: null, attach: {}, next: typeof g.next === 'number' ? g.next : 1, found: typeof g.found === 'number' ? g.found : 0 };
    T().starters.forEach(function (s) { if (g[s.flag] === true) out[s.flag] = true; });   // starter items already handed out
    var ids = {};
    (Array.isArray(g.inv) ? g.inv : []).forEach(function (it) {
      if (!isObj(it) || !T().types[it.type] || !T().rarityById[it.rarity] || !isObj(it.stats) || ids[it.id]) return;
      if (it.perk !== undefined && !(isObj(it.perk) && T().perks[it.perk.id] && typeof it.perk.v === 'number')) delete it.perk;
      ids[it.id] = true; out.inv.push(it);
      var n = parseInt(String(it.id).replace(/\D/g, ''), 10); if (n >= out.next) out.next = n + 1;
    });
    T().worn.forEach(function (sl) { if (g[sl] && ids[g[sl]] && slotOf(find(out, g[sl])) === sl) out[sl] = g[sl]; });
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
  /* worn slots (shield, armor): wear item id there (null takes it off) */
  function equipWorn(g, slot, id) {
    if (T().worn.indexOf(slot) < 0) return false;
    var it = id && find(g, id); if (id && (!it || slotOf(it) !== slot)) return false;
    g[slot] = id || null; return true;
  }
  function worn(g, slot) { return g && g[slot] ? find(g, g[slot]) : null; }
  /* the worn slot item id is in, or null */
  function wornSlot(g, id) { for (var i = 0; i < T().worn.length; i++) if (g[T().worn[i]] === id) return T().worn[i]; return null; }
  function equipShield(g, id) { return equipWorn(g, 'shield', id); }
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
    T().worn.forEach(function (sl) { if (g[sl] === id) g[sl] = null; });
    var at = attachedTo(g, id); if (at) delete g.attach[at.weapon][at.slot];
    return true;
  }
  /* weapons that are no longer carried lose their attachments (the items stay in the bag) */
  function prune(g, owned) { Object.keys(g.attach).forEach(function (w) { if (owned.indexOf(w) < 0) delete g.attach[w]; }); }
  function rarityRank(id) { for (var i = 0; i < T().rarities.length; i++) if (T().rarities[i].id === id) return i; return 0; }

  IB.Loot = {
    levelMul: levelMul, allowedTypes: allowedTypes, rollType: rollType, rarityOdds: rarityOdds, rollRarity: rollRarity, rollPerk: rollPerk,
    makeItem: makeItem, rollDrop: rollDrop, modelOf: modelOf,
    acidStats: acidStats, statLines: statLines, summary: summary, perkLine: perkLine,
    slotOf: slotOf, isAttachment: isAttachment, isWorn: isWorn, typeForSlot: typeForSlot, compatible: compatible, slotsFor: slotsFor,
    applyMods: applyMods, shieldState: shieldState, absorb: absorb, shieldKill: shieldKill, tickShield: tickShield, armorOf: armorOf, armorCut: armorCut,
    defaultGear: defaultGear, migrateGear: migrateGear, find: find, addItem: addItem, attachedTo: attachedTo, weaponItems: weaponItems,
    equipWorn: equipWorn, worn: worn, wornSlot: wornSlot, equipShield: equipShield, attach: attach, detach: detach, discard: discard, prune: prune,
    rarityRank: rarityRank, clamp: clamp
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
