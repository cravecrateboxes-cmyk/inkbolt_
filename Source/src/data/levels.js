/* INKBOLT - theme kits and the level 1-20 plan (brief section 6, boss rotation 5.8). Pure data, no DOM.
   Palettes: [main, secondary, accent prop, ground]. */
(function (IB) {
  'use strict';

  function T(id, name, palette, tiny) { return { id: id, name: name, palette: palette, tiny: !!tiny }; }

  // 18 kits. carpark (L11) reuses toytown with variant 'lot'; L12 / L15 share stockpile (L15 variant 'dock').
  IB.THEMES = {
    bedroom: T('bedroom', 'Kid\'s Bedroom', ['#8ED2FF', '#FFB4CF', '#FFD45E', '#C79A6B'], true),
    backyard: T('backyard', 'Backyard', ['#7FD36B', '#FFFFFF', '#FF8A3D', '#B98A5A'], true),
    kitchen: T('kitchen', 'Kitchen', ['#FFF0A8', '#5FC6E8', '#F0443A', '#E9D3B0'], true),
    classroom: T('classroom', 'Classroom', ['#2F6B4F', '#F6D57A', '#FF7FB0', '#D7B98E'], true),
    pool: T('pool', 'Pool', ['#5BD3F0', '#FFFFFF', '#FF8A3D', '#F6D57A']),
    mountains: T('mountains', 'Mountains', ['#7AA7E0', '#3F8F6A', '#FF8A3D', '#E8E2D2']),
    hospital: T('hospital', 'Hospital', ['#BFEFE6', '#FFFFFF', '#F0443A', '#DDE6EA']),
    toytown: T('toytown', 'Toy Town', ['#FF8A3D', '#FF7FB0', '#8A6CD8', '#F6D57A']),
    arctic: T('arctic', 'Arctic Land', ['#DFF4FF', '#7FB8F0', '#FF8A3D', '#FFFFFF']),
    military: T('military', 'Military Base', ['#9FB06A', '#E8D9A8', '#F0443A', '#C9B68A']),
    stockpile: T('stockpile', 'Stockpile Club', ['#FF6B4A', '#FFF0A8', '#2F7BEA', '#D9D4C7']),
    construction: T('construction', 'Construction Site', ['#FFC23A', '#8A6CD8', '#F0443A', '#C8B9A0']),
    bowling: T('bowling', 'Bowling Alley', ['#2C2A6E', '#FF7FB0', '#12C7B6', '#E8C68E']),
    rooftops: T('rooftops', 'Rooftops', ['#8ED2FF', '#FF8A3D', '#8A6CD8', '#BDB3A6']),
    arcade: T('arcade', 'Arcade', ['#3A2F7A', '#12C7B6', '#FF7FB0', '#5B4F9E']),
    stormdrain: T('stormdrain', 'Storm Drain', ['#6FB7A8', '#A9C9D6', '#FFC23A', '#7D8C8A']),
    junkyard: T('junkyard', 'Junkyard', ['#D9663B', '#8A6CD8', '#F6D57A', '#A6927A']),
    recycling: T('recycling', 'Recycling Plant', ['#4FA36A', '#12C7B6', '#FFB21E', '#B4BCB8'])
  };
  IB.THEME_ORDER = ['bedroom', 'backyard', 'kitchen', 'classroom', 'pool', 'mountains', 'hospital', 'toytown',
    'arctic', 'military', 'stockpile', 'construction', 'bowling', 'rooftops', 'arcade', 'stormdrain',
    'junkyard', 'recycling'];

  function mix(cr, gu, bo, to, dr, sh, br, bh) {
    var m = {};
    var v = { crawler: cr, gunner: gu, bomber: bo, tosser: to, drone: dr, shieldbot: sh, bruiser: br, binhive: bh };
    for (var k in v) if (v[k]) m[k] = v[k];
    return m;
  }

  function L(level, theme, variant, name, scale, zones, arena, m, boss, palette) {
    return { level: level, theme: theme, variant: variant, name: name, scale: scale, zones: zones,
      arena: arena, mix: m, boss: boss, palette: palette };
  }

  IB.LEVELS = [
    null,
    L(1, 'bedroom', null, 'Kid\'s Bedroom', 'tiny', 3, false, mix(18), null, ['#8ED2FF', '#FFB4CF', '#FFD45E', '#C79A6B']),
    L(2, 'backyard', null, 'Backyard', 'tiny', 3, false, mix(16, 4), null, ['#7FD36B', '#FFFFFF', '#FF8A3D', '#B98A5A']),
    L(3, 'kitchen', null, 'Kitchen', 'tiny', 3, false, mix(14, 6, 3), null, ['#FFF0A8', '#5FC6E8', '#F0443A', '#E9D3B0']),
    L(4, 'classroom', null, 'Classroom', 'tiny', 4, false, mix(14, 6, 4, 2), null, ['#2F6B4F', '#F6D57A', '#FF7FB0', '#D7B98E']),
    L(5, 'pool', null, 'Pool', 'full', 3, true, mix(12, 6, 4, 2), 'skimmer', ['#5BD3F0', '#FFFFFF', '#FF8A3D', '#F6D57A']),
    L(6, 'mountains', null, 'Mountains', 'full', 4, false, mix(12, 6, 4, 3, 4), null, ['#7AA7E0', '#3F8F6A', '#FF8A3D', '#E8E2D2']),
    L(7, 'hospital', null, 'Hospital', 'full', 4, false, mix(12, 6, 4, 2, 4, 2), null, ['#BFEFE6', '#FFFFFF', '#F0443A', '#DDE6EA']),
    L(8, 'toytown', null, 'Toy Town', 'full', 4, false, mix(12, 8, 4, 3, 4, 2, 1), null, ['#FF8A3D', '#FF7FB0', '#8A6CD8', '#F6D57A']),
    L(9, 'arctic', null, 'Arctic Land', 'full', 4, false, mix(12, 8, 5, 3, 5, 3, 2), null, ['#DFF4FF', '#7FB8F0', '#FF8A3D', '#FFFFFF']),
    L(10, 'military', null, 'Military Base', 'full', 3, true, mix(12, 8, 5, 4, 4, 3, 2), 'dumpstertank', ['#9FB06A', '#E8D9A8', '#F0443A', '#C9B68A']),
    L(11, 'toytown', 'lot', 'Car Park and Billboards', 'full', 5, false, mix(14, 8, 6, 4, 5, 3, 2, 1), null, ['#8ED2FF', '#FF7FB0', '#FFD45E', '#9AA0AA']),
    L(12, 'stockpile', null, 'Stockpile Club', 'huge', 5, false, mix(16, 8, 6, 4, 6, 4, 2, 1), null, ['#FF6B4A', '#FFF0A8', '#2F7BEA', '#D9D4C7']),
    L(13, 'construction', null, 'Construction Site', 'full', 5, false, mix(14, 10, 6, 5, 6, 4, 3, 1), null, ['#FFC23A', '#8A6CD8', '#F0443A', '#C8B9A0']),
    L(14, 'bowling', null, 'Bowling Alley', 'full', 5, false, mix(14, 10, 6, 4, 6, 5, 3, 2), null, ['#2C2A6E', '#FF7FB0', '#12C7B6', '#E8C68E']),
    L(15, 'stockpile', 'dock', 'Stockpile Club Warehouse', 'huge', 4, true, mix(14, 8, 6, 4, 6, 4, 2, 1), 'cartcolossus', ['#BFE6FF', '#FF6B4A', '#FFD45E', '#CFCFCF']),
    L(16, 'rooftops', null, 'Rooftops', 'full', 5, false, mix(16, 10, 6, 5, 8, 5, 3, 2), null, ['#8ED2FF', '#FF8A3D', '#8A6CD8', '#BDB3A6']),
    L(17, 'arcade', null, 'Arcade', 'full', 5, false, mix(16, 10, 7, 5, 8, 5, 4, 2), null, ['#3A2F7A', '#12C7B6', '#FF7FB0', '#5B4F9E']),
    L(18, 'stormdrain', null, 'Storm Drain', 'full', 6, false, mix(18, 10, 8, 5, 8, 6, 4, 2), null, ['#6FB7A8', '#A9C9D6', '#FFC23A', '#7D8C8A']),
    L(19, 'junkyard', null, 'Junkyard', 'full', 6, false, mix(18, 12, 8, 6, 8, 6, 5, 3), null, ['#D9663B', '#8A6CD8', '#F6D57A', '#A6927A']),
    L(20, 'recycling', null, 'Recycling Plant', 'full', 4, true, mix(16, 10, 8, 6, 8, 6, 4, 2), 'compactorprime', ['#4FA36A', '#12C7B6', '#FFB21E', '#B4BCB8'])
  ];

  IB.BOSS_ROTATION = ['skimmer', 'dumpstertank', 'cartcolossus', 'compactorprime'];
  IB.BOSS_MODIFIERS = ['fasterTells', 'extraWave', 'shorterWindow'];

  IB.isBossLevel = function (level) { return level >= 5 && level % 5 === 0; };

  // Boss id for a level (null on non-boss levels). Rotation repeats every 20 levels.
  IB.bossForLevel = function (level) {
    if (!IB.isBossLevel(level)) return null;
    return IB.BOSS_ROTATION[(level / 5 - 1) % 4];
  };

  // After level 20: +35% HP and one added modifier per loop (loop 1 = levels 25-40, loop 2 = 45-60...).
  IB.bossScale = function (level) {
    var loop = level > 20 ? Math.floor((level - 1) / 20) : 0;
    var mods = [];
    for (var i = 0; i < loop; i++) mods.push(IB.BOSS_MODIFIERS[i % IB.BOSS_MODIFIERS.length]);
    return { loop: loop, hpMul: 1 + 0.35 * loop, modifiers: loop, mods: mods };
  };

  // Level data for 1..20; null beyond (use IB.LevelGen.generate).
  IB.levelInfo = function (level) { return IB.LEVELS[level] || null; };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
