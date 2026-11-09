/* INKBOLT - skill tree, player level and rank titles. Pure data, no DOM. Logic: src/core/skills.js.

   ECONOMY (see tests/unit/skills.test.js)
   PLAYER LEVEL comes from XP, as in a looter shooter: every robot you wreck pays XP (by type, x the level you are
   playing), and clearing a level pays a bonus (IB.XP). LV 1-30 (PLAYER_LEVEL_CAP); the XP needed for LV n is
   IB.XP.need(n), tuned so that playing the campaign through (most robots wrecked) puts you around LV N+1 after
   level N, and maps added later keep carrying you towards LV 30. Replaying earlier maps also pays, just less.
   Every LV raises max health (core/damage.js playerMaxHp) and better gear keeps dropping (item level = the level
   you play).

   SKILL POINTS: one point for every player level gained, and the first level-up pays 2: 30 in total, the last at LV 30.
   Points are never stored: they are derived from the level.
   The tree holds 42 normal points plus 2 endgame points, so 30 buys a build, not the whole tree (respec to change it).
   The gates are low so the top is always reachable: any 9 points below open the endgame row. The two endgame skills
   cost 1 point and you pick ONE of them (respec to switch), so 24 points spent below still leave the point for it.
   In core/skills.js the skill functions take g (level-ups gained, = Skills.gained(slot)).
*/
(function (IB) {
  'use strict';

  // ranks: the effect value per rank (index 0 = rank 1); unit is appended in the UI
  function S(id, tier, col, name, kind, ranks, unit, stat, text, icon) {
    return { id: id, tier: tier, col: col, name: name, kind: kind, ranks: ranks, max: ranks.length, unit: unit,
      stat: stat, text: text, icon: icon, cost: 1, group: kind === 'capstone' ? 'endgame' : null };
  }

  /* The tree is laid out as the player's sketch: six rows, the trunk at the bottom, the two endgame skills on top.
     Tier 1 = bottom row (trunk) ... tier 7 = top row (endgame). Gates count points spent in lower tiers.
       row (top->bottom)  tier  skills
       1                  6     Handy Helpers* | Chain Reaction*        (* endgame, 5 points each)
       2                  5     Tank | Fast Fingers
       3                  4     Stamina (special) | Hydrate | Undercover (special)
       4                  3     Hazard | Ricochet | Healthy
       5                  2     Stream | Electrify (special) | Rapid
       6                  1     Overload | Heavy Ink */
  IB.SKILL_TIERS = [
    { tier: 1, name: 'Trunk', gate: 0 },
    { tier: 2, name: 'Rounds', gate: 1 },
    { tier: 3, name: 'Hazards', gate: 3 },
    { tier: 4, name: 'Arsenal', gate: 5 },
    { tier: 5, name: 'Tricks', gate: 5 },
    { tier: 6, name: 'Grit', gate: 7 },
    { tier: 7, name: 'Endgame', gate: 9, capstone: true }
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
    // tier 4 (arsenal)
    S('boom', 4, 0, 'Boom', 'rank', [10, 20, 30], '%', 'Blast damage',
      'Rocket launcher and frag can damage increase, and you carry one more frag can.', 'boom'),
    S('dart', 4, 1, 'Dart', 'rank', [6, 12, 18], '%', 'Scoped damage',
      'Bullets deal more damage while you are zoomed in (aiming down the sights).', 'dart'),
    S('surge', 4, 2, 'Surge Up', 'rank', [9, 18, 27], '%', 'Move speed',
      'Each kill speeds you up for 4 seconds. Kills refresh the boost; it does not stack.', 'surge'),
    // tier 5 (tricks)
    S('stamina', 5, 0, 'Stamina', 'special', [1], '', 'Marathon',
      'You move 15% faster, sprint 30% faster, your running lasts 2.5x longer, and stamina recharges in half the time.', 'run'),
    S('hydrate', 5, 1, 'Hydrate', 'rank', [6, 12, 18], '%', 'Coat chance',
      'Your bullets have a chance to coat a robot in electrified liquid for 6 s. Robots that come within 3 m of it take shock damage over time.', 'water'),
    S('undercover', 5, 2, 'Undercover', 'special', [1], '', 'Cloak (F)',
      'Press F: you go invisible and robots cannot see you for 7 s. Cooldown 25 s. The screen turns comic black, grey and white while it lasts.', 'cloak'),
    // tier 6 (grit)
    S('tank', 6, 0, 'Tank', 'rank', [5, 10, 15], '%', 'Damage resistance',
      'Increases damage resistance and repairs 1 health per second per rank, starting after 4 s without taking damage (like a shield).', 'armor'),
    S('fastfingers', 6, 1, 'Fast Fingers', 'rank', [10, 20, 30], '%', 'Reload and swap speed', 'Increases weapon swap speed and reload speed.', 'reload'),
    // tier 7: endgame (pick one)
    S('handyhelpers', 7, 0, 'Handy Helpers', 'capstone', [1], '', 'Rogue bots',
      'When you wreck a robot there is an 8% chance it turns rogue instead and fights for you until it is destroyed, with 3-5x its health and 1.5x its damage.', 'helper'),
    S('torpedo', 7, 2, 'Torpedo', 'capstone', [1], '', 'Last-round torpedo',
      'Your last round in each magazine becomes a torpedo, 5x base damage (2x for rocket launchers) in a wide splash that slows what it hits for 5 s.', 'torpedo'),
    S('chainreaction', 7, 1, 'Chain Reaction', 'capstone', [1], '', 'Group blast',
      'Shooting a robot with 2 or more others within 4 m has a 10% chance to blow the whole group up for 40% of each robot\'s max health. They do not all die at once.', 'burst')
  ];

  IB.SKILL_BY_ID = {};
  IB.SKILLS.forEach(function (s) { IB.SKILL_BY_ID[s.id] = s; });

  // points paid on gaining a player level (key = level-ups gained, LV - 1); nothing after LV 20
  IB.SKILL_POINTS_AT = {};
  for (var pk = 1; pk <= 29; pk++) IB.SKILL_POINTS_AT[pk] = 1;   // one point per level-up (key = level-ups gained)
  IB.SKILL_POINTS_AT[1] = 2;                                   // the first level-up pays 2: 30 in total by LV 30
  IB.SKILL_POINTS_MAX = 30;
  IB.SKILL_LAST_LEVEL = IB.SKILL_POINTS_MAX;   // the last point (30) comes with LV 30
  IB.PLAYER_LEVEL_CAP = 30;
  /* XP: per robot wrecked = kill[type] x (1 + 0.1 (L - 1)) at campaign level L; clearing level L pays clear(L).
     need(n) = total XP to reach LV n: 900 (n - 1) + 49.3 (n - 1)^2.73 (LV 2 900, LV 10 ~28k, LV 20 ~170k, LV 30 ~510k). */
  IB.XP = {
    kill: { crawler: 10, drone: 10, bomber: 12, gunner: 14, tosser: 14, shieldbot: 18, bruiser: 30, binhive: 30, soldier: 30, blader: 30,
      skimmer: 400, dumpstertank: 500, cartcolossus: 600, compactorprime: 800 },
    killDefault: 10,
    levelMul: 0.1,
    clear: function (L) { return 150 + 60 * Math.max(1, L); },
    need: function (n) { var k = Math.max(0, n - 1); return Math.round(900 * k + 49.3 * Math.pow(k, 2.73)); }
  };
  // loadout size: 2 guns, 3 once level 10 (the Dumpster Tank) is beaten
  IB.LOADOUT_RULES = { base: 2, extra: 3, extraAfter: 10 };

  // rank title per player level (HUD "LV 7  GEAR GRINDER")
  IB.RANK_TITLES = [null,
    'Tin Rookie', 'Can Kicker', 'Bolt Botherer', 'Scrap Rat', 'Junk Jockey',
    'Rivet Rattler', 'Gear Grinder', 'Spring Snapper', 'Cog Crusher', 'Bin Breaker',
    'Ink Slinger', 'Wire Wrangler', 'Dent Dealer', 'Piston Puncher', 'Chrome Cracker',
    'Circuit Smasher', 'Scrapyard Sheriff', 'Tin Terror', 'Robot Wrecker', 'Inkbolt Legend',
    'Iron Inker', 'Steel Scribbler', 'Titan Tagger', 'Mech Marker', 'Chassis Chaser',
    'Gantry Ghost', 'Foundry Phantom', 'Core Cracker', 'Overlord Breaker', 'Inkbolt Eternal'];
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
