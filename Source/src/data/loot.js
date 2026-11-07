/* INKBOLT loot: weapon rarity tiers, weapon mods (attachments) and gear items found on armory walls and benches.
   Pure data + pure functions (unit tested). A gun's live stats are its table entry (IB.WEAPONS) scaled by its rarity
   and by every mod fitted to it: IB.Loot.derive(def, rarity, mods) returns a new def object, the table is untouched.

   Rarity colours follow the usual loot ladder: grey, green, blue, purple (epic), orange (legendary).
   Armory racks roll with ARMORY_WEIGHTS: purple is very rare (0.75 %) and orange never appears there. */
(function (IB) {
  'use strict';
  var RARITY = [
    { id: 'common', name: 'Common', color: '#B9B3A6', dmg: 1.00, mag: 1.00, reload: 1.00, spread: 1.00 },
    { id: 'uncommon', name: 'Uncommon', color: '#55C76A', dmg: 1.07, mag: 1.00, reload: 0.95, spread: 0.95 },
    { id: 'rare', name: 'Rare', color: '#4C9BF2', dmg: 1.15, mag: 1.10, reload: 0.90, spread: 0.88 },
    { id: 'epic', name: 'Epic', color: '#A35CF2', dmg: 1.25, mag: 1.20, reload: 0.85, spread: 0.80 },
    { id: 'legendary', name: 'Legendary', color: '#FF9A1F', dmg: 1.38, mag: 1.30, reload: 0.80, spread: 0.70 }
  ];
  var BY_ID = {}; RARITY.forEach(function (r, i) { r.tier = i; BY_ID[r.id] = r; });

  // police / special-forces armory: weights per rarity (percent)
  var ARMORY_WEIGHTS = { common: 58, uncommon: 31, rare: 10.25, epic: 0.75, legendary: 0 };

  // mods: one per slot on a gun; fitting a mod to a taken slot swaps it. mul: multipliers on the weapon def.
  var MODS = {
    extmag: { id: 'extmag', name: 'Extended Mag', slot: 'mag', mul: { mag: 1.5 }, line: '+50% magazine' },
    speedmag: { id: 'speedmag', name: 'Speed Mag', slot: 'mag', mul: { reload: 0.72 }, line: 'Reload 28% faster' },
    suppressor: { id: 'suppressor', name: 'Suppressor', slot: 'muzzle', mul: { recoil: 0.78, recoilH: 0.7 }, line: 'Less recoil' },
    compensator: { id: 'compensator', name: 'Compensator', slot: 'muzzle', mul: { recoil: 0.85, recoilH: 0.45 }, line: 'Steady climb' },
    longbarrel: { id: 'longbarrel', name: 'Long Barrel', slot: 'barrel', mul: { damage: 1.1, spreadAim: 0.8 }, line: '+10% damage' },
    reddot: { id: 'reddot', name: 'Red Dot Sight', slot: 'optic', mul: { spreadAim: 0.6 }, line: 'Tighter aim' },
    laser: { id: 'laser', name: 'Laser Sight', slot: 'under', mul: { spreadHip: 0.65 }, line: 'Tighter hip fire' },
    grip: { id: 'grip', name: 'Vertical Grip', slot: 'under', mul: { recoil: 0.8, recoilH: 0.6 }, line: 'Less kick' }
  };
  // gear items (used on the spot)
  var ITEMS = {
    vest: { id: 'vest', name: 'Kevlar Vest', armor: 50, line: '+50 armor' },
    medkit: { id: 'medkit', name: 'Med Kit', heal: 60, line: '+60 health' },
    ammobox: { id: 'ammobox', name: 'Ammo Box', ammo: 1, line: 'Full reserve' }
  };
  var MOD_WEIGHTS = { extmag: 18, speedmag: 12, suppressor: 14, compensator: 10, longbarrel: 12, reddot: 14, laser: 10, grip: 10 };
  var ITEM_WEIGHTS = { vest: 30, medkit: 40, ammobox: 30 };

  function rollTable(weights, rng) {
    var keys = Object.keys(weights), total = 0, k;
    for (k = 0; k < keys.length; k++) total += weights[keys[k]];
    var x = rng() * total;
    for (k = 0; k < keys.length; k++) { if (weights[keys[k]] <= 0) continue; x -= weights[keys[k]]; if (x < 0) return keys[k]; }
    for (k = keys.length - 1; k >= 0; k--) if (weights[keys[k]] > 0) return keys[k];
    return keys[0];
  }

  function derive(def, rarity, mods) {
    var R = BY_ID[rarity] || RARITY[0], out = {}, k;
    for (k in def) out[k] = def[k];
    out.base = def; out.rarity = R.id;
    out.damage = def.damage * R.dmg;
    if (def.mag) out.mag = Math.max(1, Math.round(def.mag * R.mag));
    out.reload = def.reload * R.reload;
    out.spreadHip = def.spreadHip * R.spread; out.spreadAim = def.spreadAim * R.spread;
    Object.keys(mods || {}).forEach(function (slot) {
      var M = MODS[mods[slot]]; if (!M || M.slot !== slot) return;
      Object.keys(M.mul).forEach(function (f) {
        if (f === 'mag') out.mag = Math.max(1, Math.round(out.mag * M.mul.mag));
        else if (typeof out[f] === 'number') out[f] = out[f] * M.mul[f];
      });
    });
    return out;
  }

  IB.LOOT = { RARITY: RARITY, RARITY_BY_ID: BY_ID, ARMORY_WEIGHTS: ARMORY_WEIGHTS, MODS: MODS, ITEMS: ITEMS, MOD_WEIGHTS: MOD_WEIGHTS, ITEM_WEIGHTS: ITEM_WEIGHTS };
  IB.Loot = {
    rollRarity: function (rng, weights) { return rollTable(weights || ARMORY_WEIGHTS, rng); },
    rollMod: function (rng) { return rollTable(MOD_WEIGHTS, rng); },
    rollItem: function (rng) { return rollTable(ITEM_WEIGHTS, rng); },
    rollTable: rollTable,
    derive: derive
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
