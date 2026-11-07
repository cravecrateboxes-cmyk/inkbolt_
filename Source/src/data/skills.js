/* INKBOLT - skill tree, player level and rank titles. Pure data, no DOM. Logic: src/core/skills.js.

   ECONOMY (see tests/unit/skills.test.js)
   Skill points come from campaign progress only: completing level L for the first time pays POINTS_AT[L]
   (2 a level early on, 3 later, 4 on levels 10 and 15). Level 16 (the last campaign level) pays the last point.
     after level   1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
     points        2  4  6  8 11 13 15 17 20 24 27 30 33 36 40 43   -> 43 in total = the whole tree
   The tree holds 33 points of normal skills plus two 5-point endgame skills (43). However the points are spent,
   the top is always reachable: by the last level every skill, both endgame ones included, can be owned.

   PLAYER LEVEL = 1 + highest campaign level completed, capped at 20 (LEVEL_CAP): level 19 makes you LV 20 and
   the level 20 finale (Compactor Prime) is fought at max level, so every completion that leads somewhere
   raises the level by one. */
(function (IB) {
  'use strict';

  // ranks: the effect value per rank (index 0 = rank 1); unit is appended in the UI
  function S(id, tier, col, name, kind, ranks, unit, stat, text, icon) {
    return { id: id, tier: tier, col: col, name: name, kind: kind, ranks: ranks, max: ranks.length, unit: unit,
      stat: stat, text: text, icon: icon, cost: kind === 'capstone' ? 5 : 1, group: null };
  }

  /* The tree is laid out as the player's sketch: six rows, the trunk at the bottom, the two endgame skills on top.
     Tier 1 = bottom row (trunk) ... tier 6 = top row (endgame). Gates count points spent in lower tiers.
       row (top->bottom)  tier  skills
       1                  6     Handy Helpers* | Chain Reaction*        (* endgame, 5 points each)
       2                  5     Tank | Fast Fingers
       3                  4     Stamina (special) | Hydrate | Undercover (special)
       4                  3     Hazard | Ricochet | Healthy
       5                  2     Stream | Electrify (special) | Rapid
       6                  1     Overload | Heavy Ink
     Normal skills hold 30 + 3 = 33 points; an endgame skill needs 14 below it + 5 = 19 (first affordable after
     level 9); the whole tree (43) is paid for by level 16. */
  IB.SKILL_TIERS = [
    { tier: 1, name: 'Trunk', gate: 0 },
    { tier: 2, name: 'Rounds', gate: 2 },
    { tier: 3, name: 'Hazards', gate: 5 },
    { tier: 4, name: 'Tricks', gate: 8 },
    { tier: 5, name: 'Grit', gate: 11 },
    { tier: 6, name: 'Endgame', gate: 14, capstone: true }
  ];

  // params: the numbers the runtime uses (per rank where an array); text is the player-facing description
  IB.SKILLS = [
    // tier 1 (trunk)
    S('overload', 1, 0, 'Overload', 'rank', [10, 20, 30], '%', 'Magazine size', 'Larger magazines on every gun.', 'mag'),
    S('heavyink', 1, 1, 'Heavy Ink', 'rank', [4, 8, 12], '%', 'Bullet damage', 'Your bullets deal increased damage.', 'drop'),
    // tier 2
    S('stream', 2, 0, 'Stream', 'rank', [6, 12, 18], '%', 'Pierce chance',
      'Each bullet that hits an enemy has a chance to punch through and hit the enemy behind it for double (x2) damage.', 'pierce'),
    S('electrify', 2, 1, 'Electrify', 'special', [1], '', 'Shock rounds',
      'Your rounds become electrical: every hit shocks the robot for 25% of its damage again over 5 s.', 'bolt'),
    S('rapid', 2, 2, 'Rapid', 'rank', [4, 8, 12], '%', 'Fire rate', 'Increases your fire rate.', 'gauge'),
    // tier 3
    S('hazard', 3, 0, 'Hazard', 'rank', [5, 10, 15], '%', 'Acid pool chance',
      'Hits have a chance to leave a pool of acid on the ground for 5 s. Robots that walk through it take acid damage.', 'acid'),
    S('ricochet', 3, 1, 'Ricochet', 'rank', [8, 16, 24], '%', 'Ricochet chance',
      'Your bullets have a chance to ricochet into another robot within 10 m for 60% damage.', 'ricochet'),
    S('healthy', 3, 2, 'Healthy', 'rank', [8, 16, 24], '%', 'Max health',
      'Increases your max health and slowly regenerates 0.5% of it per second per rank after 4 s without damage.', 'heart'),
    // tier 4
    S('stamina', 4, 0, 'Stamina', 'special', [1], '', 'Marathon',
      'You move 15% faster, sprint 50% faster, your running lasts 2.5x longer, and stamina recharges in half the time.', 'run'),
    S('hydrate', 4, 1, 'Hydrate', 'rank', [6, 12, 18], '%', 'Coat chance',
      'Your bullets have a chance to coat a robot in electrified liquid for 6 s. Robots that come within 3 m of it take shock damage over time.', 'water'),
    S('undercover', 4, 2, 'Undercover', 'special', [1], '', 'Cloak (F)',
      'Press F: you go invisible and robots cannot see you for 5 s. Cooldown 30 s. The screen turns comic black, grey and white while it lasts.', 'cloak'),
    // tier 5
    S('tank', 5, 0, 'Tank', 'rank', [5, 10, 15], '%', 'Damage resistance',
      'Increases damage resistance and repairs 1 health per second per rank, starting after 4 s without taking damage (like a shield).', 'armor'),
    S('fastfingers', 5, 1, 'Fast Fingers', 'rank', [10, 20, 30], '%', 'Reload and swap speed', 'Increases weapon swap speed and reload speed.', 'reload'),
    // tier 6: endgame (both can be owned)
    S('handyhelpers', 6, 0, 'Handy Helpers', 'capstone', [1], '', 'Rogue bots',
      'When you wreck a robot there is an 8% chance it turns rogue instead and fights for you for 15 s.', 'helper'),
    S('chainreaction', 6, 1, 'Chain Reaction', 'capstone', [1], '', 'Group blast',
      'Shooting a robot with 2 or more others within 4 m has a 10% chance to blow the whole group up for 40% of each robot\'s max health. They do not all die at once.', 'burst')
  ];

  IB.SKILL_BY_ID = {};
  IB.SKILLS.forEach(function (s) { IB.SKILL_BY_ID[s.id] = s; });

  // points paid the first time a campaign level is completed; levels past 17 pay nothing
  IB.SKILL_POINTS_AT = { 1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 2, 7: 2, 8: 2, 9: 3, 10: 4, 11: 3, 12: 3, 13: 3, 14: 3, 15: 4, 16: 3 };
  IB.SKILL_LAST_LEVEL = 16;
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
