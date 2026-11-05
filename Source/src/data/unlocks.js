/* INKBOLT - weapon unlock-by-level table (brief section 5.2). Pure data + helpers, no DOM. */
(function (IB) {
  'use strict';

  IB.UNLOCKS = {1: ['pip'], 3: ['buzz'], 4: ['frag'], 5: ['rivet'], 6: ['popflash'], 7: ['katana'],
    8: ['handcannon'], 9: ['needle'], 10: ['whisk'], 11: ['triplet'], 12: ['cancannon'], 13: ['longtom'],
    14: ['fireaxe'], 16: ['twintap'], 17: ['hornet'], 18: ['brick'], 25: ['scrapper']};

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
