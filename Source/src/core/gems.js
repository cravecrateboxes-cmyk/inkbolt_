/* INKBOLT - gem economy (brief sections 5.7, 5.8, 5.10). Pure, no DOM. */
(function (IB) {
  'use strict';

  var VALUES = { chip: 1, shard: 5, core: 25 };

  function value(g) { return (g.chip || 0) * VALUES.chip + (g.shard || 0) * VALUES.shard + (g.core || 0) * VALUES.core; }

  // Shard-tier = the robot's base drop includes at least one Shard (Shieldbot, Bruiser, Bin Hive).
  function isShardTier(typeId) {
    var e = IB.ENEMIES[typeId];
    return !!(e && e.gems.shard > 0);
  }

  /* Drop for one robot at level L. Shard-tier robots get floor(L/4) extra Chips.
     Gem Press: +10% per level of the robot's total, rounded down, paid as Chips;
     at least 1 extra on Shard-tier robots when pressLevel > 0. */
  function robotDrop(typeId, L, pressLevel) {
    var e = IB.ENEMIES[typeId];
    if (!e) throw new Error('unknown robot ' + typeId);
    var chip = e.gems.chip || 0, shard = e.gems.shard || 0, core = e.gems.core || 0;
    var shardTier = shard > 0;
    if (shardTier) chip += Math.floor((L || 1) / 4);
    var press = pressLevel || 0;
    if (press > 0) {
      var base = value({ chip: chip, shard: shard, core: core });
      var extra = Math.floor(base * 0.1 * press + 1e-9);
      if (shardTier) extra = Math.max(1, extra);
      chip += extra;
    }
    return { chip: chip, shard: shard, core: core, total: value({ chip: chip, shard: shard, core: core }) };
  }

  // Boss drop (5.8 table); Gem Press applies (rounded down). No per-level extra Chips.
  function bossDrop(bossId, pressLevel) {
    var b = IB.BOSSES[bossId];
    if (!b) throw new Error('unknown boss ' + bossId);
    var chip = b.gems.chip || 0, shard = b.gems.shard || 0, core = b.gems.core || 0;
    var press = pressLevel || 0;
    if (press > 0) chip += Math.floor(value(b.gems) * 0.1 * press + 1e-9);
    return { chip: chip, shard: shard, core: core, total: value({ chip: chip, shard: shard, core: core }) };
  }

  function clearBonus(L) { return 15 + 5 * L; }
  function noDeathBonus(earned) { return Math.floor(0.25 * earned); }
  function replay(n) { return Math.floor(n / 2); }

  // Count robots in generated zones: [{spawns:[{type}]}] -> {crawler: n, ...}.
  function mixFromZones(zones) {
    var m = {};
    zones.forEach(function (z) { z.spawns.forEach(function (s) { m[s.type] = (m[s.type] || 0) + 1; }); });
    return m;
  }

  /* Estimated gems for one full clear of level L.
     opts: {noDeath (default true), pressLevel (0), mix (override, required past L20 unless a
     generated level is passed as opts.level), boss (override id), replay (false)}.
     earned = robot + boss drops; no-death bonus = 25% of earned (robots + boss, not the clear bonus).
     Bin Hive children and ammo drops are not counted. */
  function levelIncome(L, opts) {
    var o = opts || {};
    var info = IB.LEVELS[L];
    var mix = o.mix || (o.level ? mixFromZones(o.level.zones) : (info ? info.mix : null));
    if (!mix) throw new Error('levelIncome: no enemy mix for level ' + L);
    var boss = o.boss !== undefined ? o.boss : (o.level ? o.level.boss : IB.bossForLevel(L));
    var press = o.pressLevel || 0;
    var robots = 0;
    for (var id in mix) robots += robotDrop(id, L, press).total * mix[id];
    var bossGems = boss ? bossDrop(boss, press).total : 0;
    var earned = robots + bossGems;
    var clear = clearBonus(L);
    var nd = o.noDeath === false ? 0 : noDeathBonus(earned);
    var total = earned + clear + nd;
    if (o.replay) total = replay(total);
    return { robots: robots, boss: bossGems, earned: earned, clear: clear, noDeath: nd, total: total };
  }

  IB.Gems = {
    VALUES: VALUES, value: value, isShardTier: isShardTier, robotDrop: robotDrop, bossDrop: bossDrop,
    clearBonus: clearBonus, noDeathBonus: noDeathBonus, replay: replay, mixFromZones: mixFromZones,
    levelIncome: levelIncome,
    EXPECTED_INCOME: { 1: 45, 5: 150, 10: 280, 20: 600 }
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
