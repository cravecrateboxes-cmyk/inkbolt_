/* INKBOLT - weapon unlock-by-level table (brief section 5.2). Pure data + helpers, no DOM. */
(function (IB) {
  'use strict';

  // campaign level -> weapons waiting on stands at its start (mirrors src/data/levelplans.js): melee and grenades are all
  // in hand by level 5
  IB.UNLOCKS = {1: ['pip', 'buzz'], 2: ['rivet', 'handcannon'], 3: ['triplet', 'whisk', 'dagger'], 4: ['longtom', 'hornet', 'frag', 'nunchucks'],
    5: ['brick', 'twintap', 'katana', 'eaxe'], 6: ['needle'], 7: ['scrapper'], 8: ['vanguard'], 9: ['thunder'], 11: ['railspike']};

  function unlockLevels() {
    return Object.keys(IB.UNLOCKS).map(Number).sort(function (a, b) { return a - b; });
  }

  // Weapon ids unlocked at or below `highestLevel`, in unlock order.
  IB.ownedWeapons = function (highestLevel) {
    var out = [];
    unlockLevels().forEach(function (lv) {
      if (lv <= highestLevel) out.push.apply(out, IB.UNLOCKS[lv]);
    });
    return out;
  };

  // Weapons granted at the start of `level` (copy; empty if none).
  IB.unlocksAt = function (level) {
    return (IB.UNLOCKS[level] || []).slice();
  };

  // Level that unlocks weapon `id`, or null.
  IB.unlockLevelOf = function (id) {
    var lv = unlockLevels();
    for (var i = 0; i < lv.length; i++) if (IB.UNLOCKS[lv[i]].indexOf(id) >= 0) return lv[i];
    return null;
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
