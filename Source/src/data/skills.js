/* INKBOLT - skill tree, player level and rank titles. Pure data, no DOM. Logic: src/core/skills.js.

   ECONOMY (see tests/unit/skills.test.js)
   Skill points come from campaign progress only: completing level L for the first time pays POINTS_AT[L]
   (1 point, 2 on levels 1, 5, 10, 15 and 17). Level 17 pays the last point; nothing after it.
     after level   1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17
     points        2  3  4  5  7  8  9 10 11 13 14 15 16 17 19 20 22   -> 22 in total
   The tree holds 33 points of normal skills plus two 5-point capstones (43): 22 buys about half of it.
   Tier gates count the points spent in the tiers above: II 3, III 6, IV 9, capstones 13. One capstone costs
   13 + 5 = 18 (first affordable after the level 15 boss, 19 points); both would cost 13 + 10 = 23 > 22, so
   the budget enforces "one capstone" on top of the explicit rule.

   PLAYER LEVEL = 1 + highest campaign level completed, capped at 20 (LEVEL_CAP): level 19 makes you LV 20 and
   the level 20 finale (Compactor Prime) is fought at max level, so every completion that leads somewhere
   raises the level by one. */
(function (IB) {
  'use strict';

  // ranks: the effect value per rank (index 0 = rank 1); unit is appended in the UI
  function S(id, tier, col, name, kind, ranks, unit, stat, text, icon) {
    return { id: id, tier: tier, col: col, name: name, kind: kind, ranks: ranks, max: ranks.length, unit: unit,
      stat: stat, text: text, icon: icon, cost: kind === 'capstone' ? 5 : 1, group: kind === 'capstone' ? 'capstone' : null };
  }

  IB.SKILL_TIERS = [
    { tier: 1, name: 'Tin', gate: 0 },
    { tier: 2, name: 'Bolt', gate: 3 },
    { tier: 3, name: 'Gear', gate: 6 },
    { tier: 4, name: 'Piston', gate: 9 },
    { tier: 5, name: 'Capstone', gate: 13, capstone: true }
  ];

  IB.SKILLS = [
    // tier I: the basics
    S('overboard', 1, 0, 'Overboard', 'rank', [10, 20, 30], '%', 'Magazine size', 'Bigger magazines on every gun.', 'mag'),
    S('fastfingers', 1, 1, 'Fast Fingers', 'rank', [8, 16, 24], '%', 'Reload speed', 'Swap mags quicker.', 'reload'),
    S('tinhide', 1, 2, 'Tin Hide', 'rank', [10, 20, 30], '', 'Max health', 'Extra plating riveted on.', 'armor'),
    // tier II
    S('steadyink', 2, 0, 'Steady Ink', 'rank', [10, 20, 30], '%', 'Less recoil', 'Less kick, and 5% tighter spread per rank.', 'steady'),
    S('scrapmagnet', 2, 1, 'Scrap Magnet', 'rank', [35, 70, 105], '%', 'Gem pickup range', 'Gems jump to you from further away.', 'magnet'),
    S('secondwind', 2, 2, 'Second Wind', 'rank', [15, 30, 45], '%', 'Sprint stamina', 'Sprint and slide for longer.', 'wind'),
    // tier III
    S('heavyink', 3, 0, 'Heavy Ink', 'rank', [4, 8, 12], '%', 'Gun damage', 'Every bullet hits harder.', 'drop'),
    S('electrify', 3, 1, 'Electrify', 'special', [1], '', 'Shock rounds',
      'Hits electrify the robot: 20% of each hit (2 to 16) lands again as shock damage over 2 s.', 'bolt'),
    S('coredump', 3, 2, 'Core Dump', 'rank', [8, 16, 24], '%', 'Core-hit damage', 'Punish robots in the glowing core.', 'core'),
    // tier IV
    S('overclock', 4, 0, 'Overclock', 'rank', [4, 8, 12], '%', 'Fire rate', 'Triggers cycle faster.', 'gauge'),
    S('chainreaction', 4, 1, 'Chain Reaction', 'special', [1], '', 'Junk burst',
      'Wrecked robots burst: 35% of their max health as damage to robots within 3 m. Bursts can chain.', 'burst'),
    S('closecall', 4, 2, 'Close Call', 'special', [1], '', 'Cheat the scrapheap',
      'Once per zone, a hit that would wreck you leaves you on 1 health with 2 s of protection.', 'heart'),
    S('salvagebolts', 4, 3, 'Salvage Bolts', 'rank', [2, 4, 6], '', 'Repair per kill', 'Each wrecked robot repairs you.', 'wrench'),
    // capstones: pick one (5 points, needs 13 spent in tiers I-IV)
    S('lightningrod', 5, 0, 'Lightning Rod', 'capstone', [1], '', 'Storm build',
      'Every hit shocks like Electrify (x1.5). Core hits arc a bolt into the 2 nearest robots within 8 m for 50% of the hit.', 'rod'),
    S('tintitan', 5, 1, 'Tin Titan', 'capstone', [1], '', 'Tank build',
      '+40 max health, 20% less damage taken, and repair 4 health per second after 2 s without being hit.', 'titan')
  ];

  IB.SKILL_BY_ID = {};
  IB.SKILLS.forEach(function (s) { IB.SKILL_BY_ID[s.id] = s; });

  // points paid the first time a campaign level is completed; levels past 17 pay nothing
  IB.SKILL_POINTS_AT = { 1: 2, 2: 1, 3: 1, 4: 1, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1, 10: 2, 11: 1, 12: 1, 13: 1, 14: 1, 15: 2, 16: 1, 17: 2 };
  IB.SKILL_LAST_LEVEL = 17;
  IB.PLAYER_LEVEL_CAP = 20;
  // loadout size: 2 guns, 3 once level 10 (the Dumpster Tank) is beaten
  IB.LOADOUT_RULES = { base: 2, extra: 3, extraAfter: 10 };

  // rank title per player level (HUD "LV 7  GEAR GRINDER")
  IB.RANK_TITLES = [null,
    'Tin Rookie', 'Can Kicker', 'Bolt Botherer', 'Scrap Rat', 'Junk Jockey',
    'Rivet Rattler', 'Gear Grinder', 'Spring Snapper', 'Cog Crusher', 'Bin Breaker',
    'Ink Slinger', 'Wire Wrangler', 'Dent Dealer', 'Piston Puncher', 'Chrome Cracker',
    'Circuit Smasher', 'Scrapyard Sheriff', 'Tin Terror', 'Robot Wrecker', 'Inkbolt Legend'];
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
