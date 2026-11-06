/* INKBOLT - loot tables: rarities, item types, stat ranges, attachment compatibility. Pure data, no DOM.
   An enemy kill drops an item with chance LOOT.dropChance (overall). The item type is rolled from the types
   allowed right now (shields only after the player has cleared campaign level 3), then a rarity, then each stat
   uniformly inside the rarity's range, scaled by the campaign level (see core/loot.js).
   Stat units: fractions are reductions / bonuses (0.12 = 12 %), zoom is the optic magnification, shield capacity
   is hit points, delay seconds without damage before the cell recharges, rate hit points per second. */
(function (IB) {
  'use strict';

  var RARITIES = [
    { id: 'common', name: 'Common', weight: 70, color: '#E4DFD3', ink: '#15121C' },
    { id: 'rare', name: 'Rare', weight: 24, color: '#4A9BFF', ink: '#15121C' },
    { id: 'epic', name: 'Epic', weight: 6, color: '#B77BFF', ink: '#15121C' }
  ];

  // lo/hi per rarity. `better: 'low'` means a smaller number is the better roll (recharge delay).
  // `scale`: 'shield' grows with the campaign level (enemy damage does too), 'mod' grows a little, none = flat.
  var TYPES = {
    shield: {
      id: 'shield', slot: 'shield', name: 'Shield cell', weight: 30, minCleared: 3,
      names: { common: 'Tin Cell', rare: 'Volt Cell', epic: 'Storm Cell' },
      stats: {
        capacity: { common: [15, 24], rare: [24, 34], epic: [34, 45], scale: 'shield', round: 1 },
        delay: { common: [5.0, 4.4], rare: [4.4, 3.7], epic: [3.7, 3.0], better: 'low', round: 0.1 },
        rate: { common: [6, 9], rare: [9, 13], epic: [13, 18], scale: 'shield', round: 0.5 }
      }
    },
    grip: {
      id: 'grip', slot: 'grip', name: 'Grip', weight: 26, classes: ['smg', 'rifle', 'sniper'],
      names: { common: 'Stub Grip', rare: 'Brace Grip', epic: 'Anchor Grip' },
      stats: {
        recoil: { common: [0.08, 0.13], rare: [0.13, 0.19], epic: [0.19, 0.26], scale: 'mod', max: 0.35, round: 0.01 },
        spread: { common: [0.04, 0.08], rare: [0.08, 0.12], epic: [0.12, 0.16], scale: 'mod', max: 0.22, round: 0.01 }
      }
    },
    scope: {
      id: 'scope', slot: 'scope', name: 'Scope', weight: 24, classes: ['smg', 'rifle'], noScoped: true,
      names: { common: 'Peep Scope', rare: 'Spyglass', epic: 'Hawkeye' },
      stats: {
        zoom: { common: [1.3, 1.5], rare: [1.5, 1.8], epic: [1.8, 2.2], max: 2.5, round: 0.1 },
        aimSpread: { common: [0.15, 0.25], rare: [0.25, 0.35], epic: [0.35, 0.45], scale: 'mod', max: 0.55, round: 0.01 }
      }
    },
    acid: {
      id: 'acid', slot: 'muzzle', name: 'Acid muzzle', weight: 20, classes: ['pistol', 'smg', 'rifle', 'sniper'],
      names: { common: 'Fizz Can', rare: 'Etch Can', epic: 'Melt Can' },
      stats: {
        acid: { common: [0.12, 0.18], rare: [0.18, 0.26], epic: [0.26, 0.35], scale: 'mod', max: 0.45, round: 0.01 },
        dur: { common: [2.0, 2.0], rare: [2.5, 2.5], epic: [3.0, 3.0], round: 0.1 }
      },
      quiet: 0.55    // robots hear a silenced shot at 55 % of the normal radius
    }
  };

  IB.LOOT = {
    dropChance: 0.05,          // per player kill, any item
    invCap: 30,                // items carried (equipped ones included)
    levelScale: { shield: [0.04, 1.8], mod: [0.015, 1.25] },   // x(1 + k (L - 1)) capped
    rarities: RARITIES,
    rarityById: RARITIES.reduce(function (m, r) { m[r.id] = r; return m; }, {}),
    types: TYPES,
    slots: ['grip', 'scope', 'muzzle'],
    slotNames: { grip: 'Grip', scope: 'Scope', muzzle: 'Muzzle' },
    // world drop: how close the player walks to collect it, and how long it waits before it may be collected
    pickupRadius: 1.25, armTime: 0.6, maxWorld: 8
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
