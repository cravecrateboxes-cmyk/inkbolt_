/* INKBOLT - skill tree logic, player level, respec, loadout size. Pure, no DOM. Data: src/data/skills.js.
   skills: {id: rank}. Available points are always derived from progress (highest campaign level completed):
   there is no stored point counter, so points cannot drift or be duplicated. */
(function (IB) {
  'use strict';

  function def(id) { var s = IB.SKILL_BY_ID[id]; if (!s) throw new Error('unknown skill ' + id); return s; }
  function rank(skills, id) { var r = skills && skills[id]; return typeof r === 'number' && r > 0 ? Math.floor(r) : 0; }
  function clampLevel(h) { return typeof h === 'number' && h > 0 ? Math.floor(h) : 0; }

  // total points earned once levels 1..highest have been completed
  function earned(highest) {
    var n = 0, top = Math.min(clampLevel(highest), IB.SKILL_LAST_LEVEL);
    for (var L = 1; L <= top; L++) n += IB.SKILL_POINTS_AT[L] || 0;
    return n;
  }
  function totalPoints() { return earned(IB.SKILL_LAST_LEVEL); }
  function spent(skills) {
    var n = 0;
    IB.SKILLS.forEach(function (s) { n += Math.min(rank(skills, s.id), s.max) * s.cost; });
    return n;
  }
  function available(skills, highest) { return earned(highest) - spent(skills); }
  // points spent in the tiers above `tier` (what its gate counts)
  function spentAbove(skills, tier) {
    var n = 0;
    IB.SKILLS.forEach(function (s) { if (s.tier < tier) n += Math.min(rank(skills, s.id), s.max) * s.cost; });
    return n;
  }
  function tierInfo(tier) { return IB.SKILL_TIERS[tier - 1]; }
  function tierUnlocked(skills, tier) { return spentAbove(skills, tier) >= tierInfo(tier).gate; }
  function groupOwner(skills, group) {
    if (!group) return null;
    for (var i = 0; i < IB.SKILLS.length; i++) { var s = IB.SKILLS[i]; if (s.group === group && rank(skills, s.id) > 0) return s.id; }
    return null;
  }

  /* {ok, reason} reason: 'max' | 'tier' | 'exclusive' | 'points' */
  function canBuy(skills, highest, id) {
    var s = def(id), r = rank(skills, id);
    if (r >= s.max) return { ok: false, reason: 'max' };
    if (!tierUnlocked(skills, s.tier)) return { ok: false, reason: 'tier', need: tierInfo(s.tier).gate - spentAbove(skills, s.tier) };
    var owner = groupOwner(skills, s.group);
    if (owner && owner !== id) return { ok: false, reason: 'exclusive', owner: owner };
    if (available(skills, highest) < s.cost) return { ok: false, reason: 'points', need: s.cost - available(skills, highest) };
    return { ok: true };
  }
  // returns a new skills object with one more rank, or null when the purchase is not allowed
  function buy(skills, highest, id) {
    if (!canBuy(skills, highest, id).ok) return null;
    var out = {}; for (var k in skills) if (rank(skills, k) > 0 && IB.SKILL_BY_ID[k]) out[k] = rank(skills, k);
    out[id] = rank(skills, id) + 1;
    return out;
  }

  /* a skills object is valid when every id exists, ranks are within max, every owned skill's tier gate is met,
     at most one skill per exclusive group is owned and spent <= earned */
  function validate(skills, highest) {
    var errors = [];
    if (skills === null || typeof skills !== 'object' || Array.isArray(skills)) return { ok: false, errors: ['not an object'] };
    Object.keys(skills).forEach(function (k) {
      var v = skills[k], s = IB.SKILL_BY_ID[k];
      if (!s) { errors.push('unknown ' + k); return; }
      if (typeof v !== 'number' || v !== Math.floor(v) || v < 0) { errors.push('bad rank ' + k); return; }
      if (v > s.max) errors.push('over max ' + k);
      if (v > 0 && spentAbove(skills, s.tier) < tierInfo(s.tier).gate) errors.push('tier gate ' + k);
    });
    var groups = {};
    IB.SKILLS.forEach(function (s) { if (s.group && rank(skills, s.id) > 0) groups[s.group] = (groups[s.group] || 0) + 1; });
    for (var g in groups) if (groups[g] > 1) errors.push('exclusive ' + g);
    if (spent(skills) > earned(highest)) errors.push('overspent');
    return { ok: errors.length === 0, errors: errors };
  }
  // load-time guard: an invalid tree (hand-edited save, old data) is reset, refunding every point
  function sanitize(skills, highest) {
    var v = validate(skills || {}, highest);
    if (v.ok) { var out = {}; for (var k in skills) if (skills[k] > 0) out[k] = skills[k]; return { skills: out, reset: false }; }
    return { skills: {}, reset: !!skills && Object.keys(skills).length > 0, errors: v.errors };
  }

  /* RESPEC: 40% of the expected gem income per level at the player's progress (IB.Gems.EXPECTED_INCOME,
     interpolated: 45 at L1, 150 at L5, 280 at L10, 600 at L20), rounded to 5, at least 25.
     Against what a no-death clear really pays (IB.Gems.levelIncome) that is 35-65% of one level, about half on
     average: a rethink is affordable but never free, and it grows with the player instead of becoming trivial.
       highest  1   2   5   8   10   15   17   20
       cost     25  30  60  90  110  175  200  240 */
  function expectedIncome(L) {
    var t = (IB.Gems && IB.Gems.EXPECTED_INCOME) || { 1: 45, 5: 150, 10: 280, 20: 600 };
    var ks = Object.keys(t).map(Number).sort(function (a, b) { return a - b; });
    if (L <= ks[0]) return t[ks[0]];
    for (var i = 1; i < ks.length; i++) {
      if (L <= ks[i]) { var a = ks[i - 1], b = ks[i]; return t[a] + (t[b] - t[a]) * (L - a) / (b - a); }
    }
    var p = ks[ks.length - 2], q = ks[ks.length - 1];
    return t[q] + (t[q] - t[p]) / (q - p) * (L - q);
  }
  function respecCost(highest) {
    var L = Math.max(1, clampLevel(highest));
    return Math.max(25, Math.round(0.4 * expectedIncome(L) / 5) * 5);
  }
  /* slot: {skills, gems, highest}. Mutates on success. {ok, cost, reason: 'empty' | 'gems'} */
  function respec(slot) {
    var cost = respecCost(slot.highest);
    if (spent(slot.skills || {}) === 0) return { ok: false, reason: 'empty', cost: cost };
    if ((slot.gems || 0) < cost) return { ok: false, reason: 'gems', cost: cost };
    slot.gems -= cost; slot.skills = {};
    return { ok: true, cost: cost };
  }

  function value(skills, id) { var s = def(id), r = Math.min(rank(skills, id), s.max); return r ? s.ranks[r - 1] : 0; }
  /* runtime multipliers; multiply them onto the Upgrade Bench effects */
  function effects(skills) {
    var v = function (id) { return value(skills || {}, id); }, has = function (id) { return v(id) > 0; };
    var titan = has('tintitan'), rod = has('lightningrod');
    return {
      magMul: 1 + v('overboard') / 100,
      reloadMul: 1 / (1 + v('fastfingers') / 100),    // multiply reload TIME by this
      maxHpAdd: v('tinhide') + (titan ? 40 : 0),
      recoilMul: 1 - v('steadyink') / 100,
      spreadMul: 1 - v('steadyink') / 200,
      magnetMul: 1 + v('scrapmagnet') / 100,
      staminaMul: 1 + v('secondwind') / 100,
      dmgMul: 1 + v('heavyink') / 100,
      coreMul: 1 + v('coredump') / 100,
      rateMul: 1 + v('overclock') / 100,              // divide the time between shots by this
      leech: v('salvagebolts'),
      shock: has('electrify') || rod,
      shockMul: rod ? 1.5 : 1,
      // each hit adds 20% of its damage (2 to 16) as shock over 2 s; IB.Status pools repeated hits
      shockFrac: 0.2, shockMin: 2, shockMax: 16, shockTime: 2,
      chain: has('chainreaction'), chainFrac: 0.35, chainRadius: 3,
      closeCall: has('closecall'),
      arc: rod, arcTargets: 2, arcRange: 8, arcFrac: 0.5,
      dmgTakenMul: titan ? 0.8 : 1,
      regen: titan ? 4 : 0, regenDelay: 2
    };
  }
  // shock damage per second added by one hit (total = dps x shockTime)
  function shockDps(fx, hitDamage) {
    return Math.max(fx.shockMin, Math.min(fx.shockMax, hitDamage * fx.shockFrac)) * fx.shockMul / fx.shockTime;
  }

  function playerLevel(highest) { return Math.min(IB.PLAYER_LEVEL_CAP, 1 + clampLevel(highest)); }
  function rankTitle(level) { return IB.RANK_TITLES[Math.max(1, Math.min(IB.PLAYER_LEVEL_CAP, level | 0))]; }
  function loadoutMax(highest) { var R = IB.LOADOUT_RULES; return clampLevel(highest) >= R.extraAfter ? R.extra : R.base; }

  /* UI line for a skill at a rank: {now, next, maxed} e.g. Overboard at 1 -> now 'Magazine size +10%', next '+20%' */
  function rankText(id, r) {
    var s = def(id), fmt = function (x) { return (s.kind === 'rank' ? '+' : '') + x + s.unit; };
    if (s.kind !== 'rank') return { now: r > 0 ? 'Owned' : 'Not owned', next: r > 0 ? null : 'Unlock', maxed: r > 0 };
    return { now: r > 0 ? s.stat + ' ' + fmt(s.ranks[r - 1]) : 'Not learned yet', next: r < s.max ? s.stat + ' ' + fmt(s.ranks[r]) : null, maxed: r >= s.max };
  }

  IB.Skills = {
    def: def, rank: rank, earned: earned, totalPoints: totalPoints, spent: spent, available: available,
    spentAbove: spentAbove, tierUnlocked: tierUnlocked, canBuy: canBuy, buy: buy, validate: validate,
    sanitize: sanitize, expectedIncome: expectedIncome, respecCost: respecCost, respec: respec, value: value,
    effects: effects, shockDps: shockDps, playerLevel: playerLevel, rankTitle: rankTitle, loadoutMax: loadoutMax,
    rankText: rankText, groupOwner: groupOwner
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
