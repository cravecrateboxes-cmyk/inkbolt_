/* INKBOLT - loot tables: rarities, rarity odds per campaign level, item types, stat ranges, shield perks, slots and
   attachment compatibility. Pure data, no DOM.
   An enemy kill drops an item with chance LOOT.dropChance (overall). The item type is rolled from the types
   allowed right now (shields only after the player has cleared campaign level 3, vests after level 5), then a
   rarity from LOOT.rarityOdds for the campaign level being played, then each stat uniformly inside the rarity's
   range, scaled by the campaign level (LOOT.levelScale, see core/loot.js). Epic and Legendary shield cells also
   roll one perk (LOOT.perks).
   Stat units: fractions are reductions / bonuses (0.12 = 12 %), zoom is the optic magnification, shield capacity
   is hit points, delay seconds without damage before the cell recharges, rate hit points per second, vest hp is
   extra max health.

   Slots are data: a type's `slot` is either one of LOOT.slots (gun attachments, kept per gun in gear.attach) or one
   of LOOT.worn (player slots: gear.shield, gear.armor hold the id of the worn item). A new attachment type only needs
   a TYPES entry with a slot in LOOT.slots (plus its model + effect in game/gear.js and its card keys in ui/gear.js). */
(function (IB) {
  'use strict';

  // `weight` = the level-1 odds (rarityOdds below is what the game rolls with)
  var RARITIES = [
    { id: 'common', name: 'Common', weight: 70, color: '#E4DFD3', ink: '#15121C' },
    { id: 'rare', name: 'Rare', weight: 24, color: '#4A9BFF', ink: '#15121C' },
    { id: 'epic', name: 'Epic', weight: 6, color: '#B77BFF', ink: '#15121C' },
    { id: 'legendary', name: 'Legendary', weight: 0, color: '#FF9A2E', ink: '#15121C', minLevel: 6 }
  ];

  /* Rarity odds (%) by the campaign level being played: the row with the highest `from` <= level is used.
     Levels 1-3 roll exactly as before (70 / 24 / 6); Legendary items only drop from level 6 on.
        level   common  rare  epic  legendary
        1-3       70     24     6      0
        4         66     26     8      0
        5         62     28    10      0
        6         56     29    12      3
        7         52     30    14      4
        8         48     31    16      5
        9         44     32    18      6
        10        40     33    20      7
        11        36     34    22      8
        12        33     34    24      9
        13        30     35    25     10
        15        27     35    26     12
        17+       24     35    27     14            */
  var RARITY_ODDS = [
    { from: 1, w: [70, 24, 6, 0] },
    { from: 4, w: [66, 26, 8, 0] },
    { from: 5, w: [62, 28, 10, 0] },
    { from: 6, w: [56, 29, 12, 3] },
    { from: 7, w: [52, 30, 14, 4] },
    { from: 8, w: [48, 31, 16, 5] },
    { from: 9, w: [44, 32, 18, 6] },
    { from: 10, w: [40, 33, 20, 7] },
    { from: 11, w: [36, 34, 22, 8] },
    { from: 12, w: [33, 34, 24, 9] },
    { from: 13, w: [30, 35, 25, 10] },
    { from: 15, w: [27, 35, 26, 12] },
    { from: 17, w: [24, 35, 27, 14] },
    { from: 20, w: [20, 34, 30, 16] },   // late game: better finds as the robots get stronger
    { from: 25, w: [16, 33, 32, 19] }
  ];

  // lo/hi per rarity. `better: 'low'` means a smaller number is the better roll (recharge delay).
  // `scale`: 'shield' grows with the campaign level (enemy damage does too), 'mod' grows a little, none = flat.
  var TYPES = {
    shield: {
      id: 'shield', slot: 'shield', name: 'Shield cell', weight: 30, minCleared: 3,
      names: { common: 'Tin Cell', rare: 'Volt Cell', epic: 'Storm Cell', legendary: 'Nova Cell' },
      // a Blender model per rarity (the pickup, the inventory picture)
      models: { common: 'GEAR_ShieldCell', rare: 'GEAR_ShieldCell_Rare', epic: 'GEAR_ShieldCell_Epic', legendary: 'GEAR_ShieldCell_Legendary' },
      perks: ['overcharge', 'nova'],
      stats: {
        capacity: { common: [22, 36], rare: [36, 51], epic: [51, 68], legendary: [68, 87], scale: 'shield', curve: 0.0008, round: 1 },   // x1.5 base; curve: x(1 + c (L - 1)^2) more on top, so late cells hold far more
        delay: { common: [5.0, 4.4], rare: [4.4, 3.7], epic: [3.7, 3.0], legendary: [3.0, 2.5], better: 'low', round: 0.1 },
        rate: { common: [9, 13.5], rare: [13.5, 19.5], epic: [19.5, 27], legendary: [27, 36], scale: 'shield', curve: 0.0008, round: 0.5 }   // grows with capacity: refill time unchanged
      }
    },
    armor: {
      id: 'armor', slot: 'armor', name: 'Armour vest', weight: 18, minCleared: 5,
      names: { common: 'Tin Vest', rare: 'Plate Vest', epic: 'Bulwark Rig', legendary: 'Juggernaut' },
      models: { common: 'GEAR_Vest', rare: 'GEAR_Vest', epic: 'GEAR_Vest', legendary: 'GEAR_Vest' },
      stats: {
        // dr: share of the damage that reaches health that the vest stops (after the shield); hp: extra max health
        dr: { common: [0.04, 0.07], rare: [0.07, 0.10], epic: [0.10, 0.13], legendary: [0.13, 0.17], max: 0.2, round: 0.01 },
        hp: { common: [5, 10], rare: [10, 16], epic: [16, 24], legendary: [24, 32], scale: 'shield', round: 1 }
      }
    },
    grip: {
      id: 'grip', slot: 'grip', name: 'Grip', weight: 26, classes: ['smg', 'rifle', 'sniper', 'shotgun'],
      names: { common: 'Stub Grip', rare: 'Brace Grip', epic: 'Anchor Grip', legendary: 'Titan Grip' },
      stats: {
        recoil: { common: [0.08, 0.13], rare: [0.13, 0.19], epic: [0.19, 0.26], legendary: [0.26, 0.33], scale: 'mod', max: 0.45, round: 0.01 },
        spread: { common: [0.04, 0.08], rare: [0.08, 0.12], epic: [0.12, 0.16], legendary: [0.16, 0.21], scale: 'mod', max: 0.3, round: 0.01 }
      }
    },
    scope: {
      id: 'scope', slot: 'scope', name: 'Scope', weight: 24, classes: ['smg', 'rifle'], noScoped: true,
      names: { common: 'Peep Scope', rare: 'Spyglass', epic: 'Hawkeye', legendary: 'Oracle' },
      stats: {
        zoom: { common: [1.3, 1.5], rare: [1.5, 1.8], epic: [1.8, 2.2], legendary: [2.2, 2.6], max: 2.8, round: 0.1 },
        aimSpread: { common: [0.15, 0.25], rare: [0.25, 0.35], epic: [0.35, 0.45], legendary: [0.45, 0.55], scale: 'mod', max: 0.7, round: 0.01 }
      }
    },
    acid: {
      id: 'acid', slot: 'muzzle', name: 'Acid muzzle', weight: 20, classes: ['pistol', 'smg', 'rifle', 'sniper'],
      names: { common: 'Fizz Can', rare: 'Etch Can', epic: 'Melt Can', legendary: 'Ruin Can' },
      stats: {
        // share of each hit that burns on as acid over dur seconds (long burn: total +20% over the old 2-3 s, per second
        // about half as much, so it reads as a lingering burn rather than a burst)
        acid: { common: [0.14, 0.22], rare: [0.22, 0.31], epic: [0.31, 0.42], legendary: [0.42, 0.54], scale: 'mod', max: 0.7, round: 0.01 },
        dur: { common: [5.0, 5.0], rare: [6.0, 6.0], epic: [7.0, 7.0], legendary: [8.0, 8.0], round: 0.1 }
      },
      quiet: 0.55    // robots hear a silenced shot at 55 % of the normal radius
    },
    // more muzzle cans (same slot as the acid can; one per gun). chance = share of hits that trigger the effect
    shock: {
      id: 'shock', slot: 'muzzle', minCleared: 3, name: 'Arc can', weight: 12, classes: ['pistol', 'smg', 'rifle', 'sniper', 'shotgun'],
      names: { common: 'Spark Can', rare: 'Arc Can', epic: 'Tesla Can', legendary: 'Storm Can' },
      models: { common: 'GEAR_Shock', rare: 'GEAR_Shock', epic: 'GEAR_Shock', legendary: 'GEAR_Shock' },
      stats: {
        // a hit shocks the robot (arc share of the hit over 3 s) and jumps to the nearest robot within 5 m for the same
        chance: { common: [0.10, 0.16], rare: [0.16, 0.22], epic: [0.22, 0.30], legendary: [0.30, 0.38], max: 0.45, round: 0.01 },
        arc: { common: [0.25, 0.35], rare: [0.35, 0.45], epic: [0.45, 0.58], legendary: [0.58, 0.72], scale: 'mod', max: 0.9, round: 0.01 }
      }
    },
    blast: {
      id: 'blast', slot: 'muzzle', minCleared: 5, name: 'Boom can', weight: 12, classes: ['pistol', 'smg', 'rifle', 'sniper', 'shotgun'],
      names: { common: 'Pop Can', rare: 'Boom Can', epic: 'Blast Can', legendary: 'Ruin Can' },
      models: { common: 'GEAR_Blast', rare: 'GEAR_Blast', epic: 'GEAR_Blast', legendary: 'GEAR_Blast' },
      stats: {
        // a hit sets off a small blast (2.4 m) on the robot: power x the hit's damage to every robot in reach (never the player)
        chance: { common: [0.06, 0.09], rare: [0.09, 0.12], epic: [0.12, 0.16], legendary: [0.16, 0.20], max: 0.25, round: 0.01 },
        power: { common: [0.6, 0.8], rare: [0.8, 1.0], epic: [1.0, 1.3], legendary: [1.3, 1.6], scale: 'mod', max: 2, round: 0.05 }
      }
    },
    void: {
      id: 'void', slot: 'muzzle', minCleared: 7, name: 'Void can', weight: 10, classes: ['pistol', 'smg', 'rifle', 'sniper', 'shotgun'],
      names: { common: 'Sink Can', rare: 'Void Can', epic: 'Vortex Can', legendary: 'Singularity' },
      models: { common: 'GEAR_Void', rare: 'GEAR_Void', epic: 'GEAR_Void', legendary: 'GEAR_Void' },
      stats: {
        // a hit opens a singularity on the robot for 1.4 s: robots within radius are pulled in toward it (group them up for
        // a frag can)
        chance: { common: [0.04, 0.06], rare: [0.06, 0.08], epic: [0.08, 0.11], legendary: [0.11, 0.14], max: 0.18, round: 0.01 },
        radius: { common: [5, 6], rare: [6, 7], epic: [7, 8], legendary: [8, 9.5], round: 0.1 }
      }
    },
    mag: {
      id: 'mag', slot: 'mag', name: 'Extended mag', weight: 22, classes: ['pistol', 'smg', 'rifle', 'sniper', 'shotgun'],
      noActions: ['revolver'],   // a cylinder takes no magazine
      names: { common: 'Clip Sleeve', rare: 'Long Mag', epic: 'Drum Mag', legendary: 'Bottomless' },
      stats: {
        // mag: extra rounds per magazine (at least +1); reload: shorter reload time
        mag: { common: [0.15, 0.25], rare: [0.25, 0.38], epic: [0.38, 0.52], legendary: [0.52, 0.7], scale: 'mod', max: 0.9, round: 0.01 },
        reload: { common: [0.04, 0.08], rare: [0.08, 0.12], epic: [0.12, 0.16], legendary: [0.16, 0.21], scale: 'mod', max: 0.3, round: 0.01 }
      }
    }
  };

  /* Shield perks: Epic and Legendary cells roll one. Values per rarity [lo, hi] (scale like a shield stat when `scale`).
       overcharge  a kill starts the recharge at once and speeds it up by `v` (fraction) for `secs` seconds
       nova        when the cell breaks: a shock burst that staggers robots within `radius` m and deals `v` damage;
                   once per charge (re-armed when the cell is full again) */
  var PERKS = {
    overcharge: { id: 'overcharge', name: 'Overcharge', v: { epic: [0.4, 0.6], legendary: [0.7, 1.0] }, round: 0.05, secs: 4 },
    nova: { id: 'nova', name: 'Nova', v: { epic: [24, 34], legendary: [190, 260] }, scale: 'shield', round: 1, radius: { epic: 4.5, legendary: 18 } }   // legendary: x5 damage, x3 reach
  };

  IB.LOOT = {
    dropChance: 0.05,          // per player kill, any item
    invCap: 40,                // the full-size bag: items carried (equipped ones included), reached at player LV invCapLevel
    invStart: 16,              // bag size at player LV 1; it grows a slot or two every level (core/loot.js bagCap)
    invCapLevel: 20,
    /* Legendary gun attachments are rare finds: a Legendary attachment roll stays Legendary one time in three,
       otherwise it drops as an Epic or a Rare one (even odds). Shield cells and vests are not affected. */
    legendaryAttachKeep: 1 / 3,
    /* stat growth with the campaign level L: x(1 + k (min(L, knee) - 1) + k2 max(0, L - knee)), capped.
       Levels 1-3 grow as before (k); past the knee shields grow about as fast as the robots' pressure
       (core/damage.js), so a cell on levels 10-13 soaks a similar share of a health bar as on level 4.
         L        1     3     6    10    13    20
         shield 1.00  1.08  1.35  1.71  1.98  2.61
         mod    1.00  1.03  1.12  1.24  1.33  1.50      */
    levelScale: { shield: { k: 0.04, knee: 3, k2: 0.1, cap: 5.78 }, mod: { k: 0.015, knee: 3, k2: 0.03, cap: 2.44 } },   // caps reached at level 50 (the beta level cap)
    rarities: RARITIES,
    rarityById: RARITIES.reduce(function (m, r) { m[r.id] = r; return m; }, {}),
    rarityOdds: RARITY_ODDS,
    types: TYPES,
    perks: PERKS,
    perkFrom: ['epic', 'legendary'],
    slots: ['grip', 'scope', 'muzzle', 'mag'],           // gun attachment slots, in card order
    slotNames: { grip: 'Grip', scope: 'Scope', muzzle: 'Muzzle', mag: 'Mag', shield: 'Shield', armor: 'Armour' },
    worn: ['shield', 'armor'],                           // player slots (gear[slot] = item id)
    // HUD shield bar colour per tier (ui/loothud.js)
    shieldTint: { common: '#5FD0FF', rare: '#6FA2FF', epic: '#C08BFF', legendary: '#FFA640' },
    // starter items handed out once (game.js): a common shield cell after level 3, a common vest after level 5
    starters: [{ flag: 'starter', type: 'shield', cleared: 3, note: 'Shields unlocked' }, { flag: 'starterVest', type: 'armor', cleared: 5, note: 'Armour unlocked' }],
    // world drop: how close the player walks to collect it, and how long it waits before it may be collected
    pickupRadius: 1.25, armTime: 0.6, maxWorld: 40
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
