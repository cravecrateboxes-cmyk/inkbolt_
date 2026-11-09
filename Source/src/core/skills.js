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
  // points spent in the tiers below `tier` (what its gate counts; the name is from the old top-down layout)
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
  /* runtime numbers for the skill tree (game/skillfx.js, game.js applySkillStats, player.js, weapons.js, ai.js).
     Every multiplier is 1 and every chance 0 with no skills. Damage over time goes through IB.Status pools. */
  function effects(skills) {
    skills = skills || {};
    var v = function (id) { return value(skills, id); }, has = function (id) { return v(id) > 0; }, rk = function (id) { return Math.min(rank(skills, id), def(id).max); };
    var stamina = has('stamina');
    return {
      // trunk
      magMul: 1 + v('overload') / 100,                 // Overload: magazine size
      dmgMul: 1 + v('heavyink') / 100,                 // Heavy Ink: bullet damage
      // tier 2
      pierce: v('stream') / 100, pierceMul: 2,         // Stream: chance to punch through into the robot behind for x2
      shock: has('electrify'), shockFrac: 0.25, shockTime: 5,   // Electrify: 25% of each hit again as shock over 5 s
      rateMul: 1 + v('rapid') / 100,                   // Rapid: divide the time between shots by this
      // tier 3
      pool: v('hazard') / 100, poolTime: 5, poolRadius: 1.3, poolFrac: 0.5, poolMin: 4, poolMax: 30, poolBurn: 5,   // Hazard
      ricochet: v('ricochet') / 100, ricochetRange: 10, ricochetFrac: 0.6,   // Ricochet
      maxHpMul: 1 + v('healthy') / 100,                // Healthy: max health
      regenPct: 0.5 * rk('healthy'),                   // ... and 0.5% of max health per second per rank
      // tier 4 (arsenal)
      boomMul: 1 + v('boom') / 100, grenadeCount: has('boom') ? 1 : 0,   // Boom: frag + rocket damage, one more frag can
      dartMul: 1 + v('dart') / 100,                    // Dart: bullets while zoomed in
      surgeMul: v('surge') / 100, surgeTime: 4,        // Surge Up: move speed after a kill (no stacking)
      // tier 5 (tricks)
      // Stamina: sprint x1.3 on top of the +15% move speed (x1.5 in all; it was a too-fast x2), runs last 2.5x longer,
      // stamina refills in half the time
      sprintMul: stamina ? 1.15 : 1, moveMul: stamina ? 1.15 : 1, staminaMul: stamina ? 2.5 : 1, staminaRechargeMul: stamina ? 0.5 : 1,
      coat: v('hydrate') / 100, coatTime: 6, coatRadius: 3, coatFrac: 0.3, coatMin: 2, coatMax: 18, coatBurn: 5,   // Hydrate
      cloak: has('undercover'), cloakTime: 7.5, cloakCooldown: 25,   // Undercover (F)
      // tier 6 (grit)
      dmgTakenMul: 1 - v('tank') / 100,                // Tank: damage resistance
      regenFlat: rk('tank'),                           // ... and 1 health per second per rank
      regenDelay: 4,                                   // both repairs start after 4 s without damage
      reloadMul: 1 / (1 + v('fastfingers') / 100),     // Fast Fingers: multiply reload TIME by this
      swapMul: 1 / (1 + v('fastfingers') / 100),       // ... and holster / draw time
      // tier 7 (pick one)
      rogue: has('handyhelpers') ? 0.08 : 0, rogueTime: Infinity, rogueDmgMul: 1.5, rogueHpMul: [3, 5],   // Handy Helpers
      torpedo: has('torpedo'), torpedoMul: 5, torpedoRocketMul: 2, torpedoRadius: 4.5, torpedoSlow: 0.25, torpedoSlowTime: 5,   // Torpedo: last round of a magazine
      chain: has('chainreaction') ? 0.1 : 0, chainMin: 2, chainRadius: 4, chainFrac: 0.4, chainCooldown: 1,   // Chain Reaction
      // neutral fields older callers still read (Upgrade Bench stacking, field kit)
      recoilMul: 1, spreadMul: 1, magnetMul: 1, coreMul: 1, leech: 0, maxHpAdd: 0, regen: rk('tank') + 0.5 * rk('healthy')
    };
  }
  // shock damage per second added by one hit (total = dps x shockTime = shockFrac of the hit)
  function shockDps(fx, hitDamage) { return Math.max(0, hitDamage) * fx.shockFrac / fx.shockTime; }
  // acid pool / wet coat strength from the hit that made it (damage per second while a robot stands in it)
  function poolDps(fx, hitDamage) { return Math.max(fx.poolMin, Math.min(fx.poolMax, hitDamage * fx.poolFrac)); }
  function coatDps(fx, hitDamage) { return Math.max(fx.coatMin, Math.min(fx.coatMax, hitDamage * fx.coatFrac)); }
  // health repaired per second after regenDelay s without damage (Healthy % + Tank flat)
  function regenRate(fx, maxHp) { return (fx.regenPct || 0) / 100 * maxHp + (fx.regenFlat || 0); }
  /* Chain Reaction: damage per robot of a group blast. hp = current health of each robot in the group, max = max health.
     Each takes chainFrac of its own max health; if that would wreck every one of them, the toughest survives on 1 hp. */
  function chainDamage(fx, hp, max) {
    var out = hp.map(function (h, i) { return max[i] * fx.chainFrac; });
    var all = hp.length > 0 && hp.every(function (h, i) { return out[i] >= h; });
    if (all) { var k = 0; hp.forEach(function (h, i) { if (h > hp[k]) k = i; }); out[k] = Math.max(0, hp[k] - 1); }
    return out;
  }

  // player level from level-ups gained (g = LV - 1); the skill functions above take g as their progress argument
  function playerLevel(g) { return Math.min(IB.PLAYER_LEVEL_CAP, 1 + clampLevel(g)); }
  // XP (data/skills.js IB.XP): LV for a total, XP needed for a LV, XP for a kill / a level clear at campaign level L
  function xpForLevel(lv) { return IB.XP.need(Math.max(1, Math.min(IB.PLAYER_LEVEL_CAP, lv | 0))); }
  function levelFromXp(xp) {
    var lv = 1; xp = typeof xp === 'number' && xp > 0 ? xp : 0;
    while (lv < IB.PLAYER_LEVEL_CAP && xp >= IB.XP.need(lv + 1)) lv++;
    return lv;
  }
  function killXp(type, L) { var b = IB.XP.kill[type] || IB.XP.killDefault; return Math.round(b * (1 + IB.XP.levelMul * (Math.max(1, L || 1) - 1))); }
  function clearXp(L) { return IB.XP.clear(L); }
  // a save slot's level-ups gained (what the skill functions take)
  function gained(slot) { return levelFromXp(slot && slot.xp) - 1; }
  // {lv, into, span, frac}: progress through the current player level (span 0 at the cap)
  function xpProgress(xp) {
    var lv = levelFromXp(xp), a = IB.XP.need(lv), b = lv < IB.PLAYER_LEVEL_CAP ? IB.XP.need(lv + 1) : a;
    return { lv: lv, into: Math.max(0, (xp || 0) - a), span: b - a, frac: b > a ? Math.min(1, ((xp || 0) - a) / (b - a)) : 1 };
  }
  function rankTitle(level) { return IB.RANK_TITLES[Math.max(1, Math.min(IB.PLAYER_LEVEL_CAP, level | 0))]; }
  function loadoutMax(highest) { var R = IB.LOADOUT_RULES; return clampLevel(highest) >= R.extraAfter ? R.extra : R.base; }

  /* UI line for a skill at a rank: {now, next, maxed} e.g. Overload at 1 -> now 'Magazine size +10%', next '+20%' */
  function rankText(id, r) {
    var s = def(id), fmt = function (x) { return (s.kind === 'rank' ? '+' : '') + x + s.unit; };
    if (s.kind !== 'rank') return { now: r > 0 ? 'Owned' : 'Not owned', next: r > 0 ? null : 'Unlock', maxed: r > 0 };
    return { now: r > 0 ? s.stat + ' ' + fmt(s.ranks[r - 1]) : 'Not learned yet', next: r < s.max ? s.stat + ' ' + fmt(s.ranks[r]) : null, maxed: r >= s.max };
  }

  IB.Skills = {
    def: def, rank: rank, earned: earned, totalPoints: totalPoints, spent: spent, available: available,
    spentAbove: spentAbove, tierUnlocked: tierUnlocked, canBuy: canBuy, buy: buy, validate: validate,
    sanitize: sanitize, expectedIncome: expectedIncome, respecCost: respecCost, respec: respec, value: value,
    effects: effects, shockDps: shockDps, poolDps: poolDps, coatDps: coatDps, regenRate: regenRate, chainDamage: chainDamage, playerLevel: playerLevel, rankTitle: rankTitle, loadoutMax: loadoutMax,
    xpForLevel: xpForLevel, levelFromXp: levelFromXp, killXp: killXp, clearXp: clearXp, gained: gained, xpProgress: xpProgress,
    rankText: rankText, groupOwner: groupOwner
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
