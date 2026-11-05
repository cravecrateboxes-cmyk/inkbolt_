/* INKBOLT - Upgrade Bench cards (brief section 5.11). Pure data, no DOM.
   stat / start / step / unit drive the "current to next" line: value(lvl) = start + step * lvl,
   e.g. Heavy Slugs: "Damage 115% to 130%". */
(function (IB) {
  'use strict';

  function U(id, cat, name, effect, max, base, stat, start, step, unit, note) {
    return { id: id, cat: cat, name: name, effect: effect, max: max, base: base,
      stat: stat, start: start, step: step, unit: unit, note: note || null };
  }

  IB.UPGRADES = [
    U('dmg', 'Weapon', 'Heavy Slugs', '+15% weapon damage', 6, 40, 'Damage', 100, 15, '%'),
    U('reload', 'Weapon', 'Quick Hands', '+15% reload speed', 4, 30, 'Reload speed', 100, 15, '%'),
    U('recoil', 'Weapon', 'Steady Grip', '-15% recoil', 4, 30, 'Recoil', 100, -15, '%'),
    U('spread', 'Weapon', 'Tight Choke', '-12% spread', 4, 30, 'Spread', 100, -12, '%'),
    U('mag', 'Weapon', 'Deep Mags', '+20% magazine size (rounded up)', 4, 35, 'Magazine size', 100, 20, '%'),
    U('core', 'Weapon', 'Core Finder', '+15% core-hit damage', 4, 40, 'Core damage', 100, 15, '%'),
    U('crit', 'Weapon', 'Targeting Chip', '+6% chance to deal double damage', 5, 45, 'Crit chance', 0, 6, '%'),
    U('blast', 'Weapon', 'Blast Wrap', '+20% explosion radius (grenades, rockets)', 3, 45, 'Blast radius', 100, 20, '%'),
    U('edge', 'Weapon', 'Edge Hone', '+20% melee damage', 4, 35, 'Melee damage', 100, 20, '%'),
    U('hp', 'Chassis', 'Armor Plating', '+20 max health', 6, 35, 'Max health', 100, 20, ''),
    U('regen', 'Chassis', 'Nanite Welders', 'Repair 1.5 health per second after 3 s without damage', 3, 50, 'Repair', 0, 1.5, ' hp/s'),
    U('speed', 'Chassis', 'Servo Legs', '+8% move speed', 4, 35, 'Move speed', 100, 8, '%'),
    U('jump', 'Chassis', 'Spring Boots', '+15% jump height; level 3 adds a double jump', 3, 40, 'Jump height', 100, 15, '%', 'double jump at level 3'),
    U('leech', 'Chassis', 'Salvage Protocol', 'Each kill repairs 3 health', 3, 45, 'Repair per kill', 0, 3, ' hp'),
    U('magnet', 'Module', 'Gem Magnet', '+50% gem pickup range', 3, 25, 'Pickup range', 2.5, 1.25, ' m'),
    U('press', 'Module', 'Gem Press', '+10% gems from robots', 5, 50, 'Robot gems', 100, 10, '%'),
    U('cans', 'Module', 'Spare Cans', '+1 grenade carried (both types)', 3, 40, 'Extra grenades', 0, 1, ''),
    U('flash', 'Module', 'Flash Shield', '-30% flash-bang blind time on you', 2, 25, 'Blind time', 100, -30, '%'),
    U('stamina', 'Module', 'Sprint Cells', '+25% sprint stamina', 3, 25, 'Sprint stamina', 100, 25, '%')
  ];

  IB.UPGRADE_BY_ID = {};
  IB.UPGRADES.forEach(function (u) { IB.UPGRADE_BY_ID[u.id] = u; });

  IB.BENCH_RULES = { offer: 3, maxBuys: 3, rerollBase: 10, rerollStep: 10, costGrowth: 1.5 };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
