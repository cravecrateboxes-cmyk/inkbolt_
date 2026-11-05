/* INKBOLT - Upgrade Bench logic (brief section 5.11). Pure, no DOM. */
(function (IB) {
  'use strict';

  function round5(x) { return Math.round(x / 5) * 5; }

  function def(id) {
    var u = IB.UPGRADE_BY_ID[id];
    if (!u) throw new Error('unknown upgrade ' + id);
    return u;
  }

  // Price of buying the next level when the card is at currentLevel; null when already at max.
  function cost(id, currentLevel) {
    var u = def(id);
    var lv = currentLevel || 0;
    if (lv >= u.max) return null;
    return round5(u.base * Math.pow(1.5, lv));
  }

  function levelOf(owned, id) { return (owned && owned[id]) || 0; }

  // n distinct card ids that are not at max level (fewer if not enough remain).
  function draw(owned, rng, n) {
    var count = n === undefined ? 3 : n;
    var pool = IB.UPGRADES.filter(function (u) { return levelOf(owned, u.id) < u.max; })
      .map(function (u) { return u.id; });
    return IB.RNG.shuffle(rng, pool).slice(0, count);
  }

  function rerollCost(rerollsSoFar) { return 10 + 10 * (rerollsSoFar || 0); }

  function magSize(baseMag, lvl) {
    if (baseMag === Infinity) return Infinity;
    return Math.ceil(baseMag * (1 + 0.2 * (lvl || 0)) - 1e-9);
  }

  function effects(owned) {
    var g = function (id) { return levelOf(owned, id); };
    var jump = 1 + 0.15 * g('jump');
    return {
      dmgLevel: g('dmg'),
      reloadMul: 1 / (1 + 0.15 * g('reload')),   // multiply reload TIME by this
      recoilMul: 1 - 0.15 * g('recoil'),
      spreadMul: 1 - 0.12 * g('spread'),
      magLevel: g('mag'),
      magMul: 1 + 0.2 * g('mag'),               // use magSize() for the rounded-up count
      coreLevel: g('core'),
      critLevel: g('crit'),
      critChance: 0.06 * g('crit'),
      blastLevel: g('blast'),
      blastMul: 1 + 0.2 * g('blast'),
      edgeLevel: g('edge'),
      meleeMul: 1 + 0.2 * g('edge'),
      maxHp: 100 + 20 * g('hp'),
      regen: 1.5 * g('regen'),                  // hp/s ...
      regenDelay: 3,                            // ... after 3 s without damage
      speedMul: 1 + 0.08 * g('speed'),
      jumpMul: jump,                            // jump HEIGHT multiplier
      jumpVelMul: Math.sqrt(jump),              // matching jump velocity multiplier
      doubleJump: g('jump') >= 3,
      leech: 3 * g('leech'),
      magnetRadius: 2.5 * (1 + 0.5 * g('magnet')),
      pressLevel: g('press'),
      extraCans: g('cans'),
      flashMul: 1 - 0.3 * g('flash'),
      staminaMul: 1 + 0.25 * g('stamina')
    };
  }

  function fmt(v, unit) {
    var r = Math.round(v * 100) / 100;
    return String(r) + unit;
  }

  /* {effect, stat, from, to, text, maxed, level, max}
     e.g. cardText('dmg', 1) -> {stat:'Damage', from:'115%', to:'130%', text:'Damage 115% to 130%'}. */
  function cardText(id, currentLevel) {
    var u = def(id);
    var lv = currentLevel || 0;
    var maxed = lv >= u.max;
    var from = fmt(u.start + u.step * lv, u.unit);
    var to = fmt(u.start + u.step * Math.min(u.max, lv + 1), u.unit);
    if (id === 'jump' && lv + 1 === 3) to += ' + double jump';
    var text = maxed ? u.stat + ' ' + from + ' (max)' : u.stat + ' ' + from + ' to ' + to;
    return { effect: u.effect, stat: u.stat, from: from, to: to, text: text, maxed: maxed, level: lv, max: u.max };
  }

  IB.Upgrades = {
    round5: round5, cost: cost, draw: draw, rerollCost: rerollCost, effects: effects,
    magSize: magSize, cardText: cardText
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
