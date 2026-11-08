/* INKBOLT - arsenal and loadout rules. Pure, no DOM.
   arsenal: every gun the player owns (weapon stands add to it). loadout: the guns carried into a level, in key order
   (loadout[0] is key 1). Size: IB.Skills.loadoutMax(highest) = 2, or 3 after level 10. */
(function (IB) {
  'use strict';

  function uniq(a) { var out = []; (a || []).forEach(function (id) { if (typeof id === 'string' && out.indexOf(id) < 0) out.push(id); }); return out; }

  // arsenal: unique known weapon ids; ok(id) optionally filters (e.g. weapons without a model)
  function fixArsenal(arsenal, ok) {
    return uniq(arsenal).filter(function (id) { return IB.WEAPONS[id] && (!ok || ok(id)); });
  }
  // loadout: unique, owned, at most max; an empty one is filled with the first guns of the arsenal
  function fix(loadout, arsenal, max) {
    var out = uniq(loadout).filter(function (id) { return arsenal.indexOf(id) >= 0; }).slice(0, Math.max(1, max));
    if (!out.length) out = arsenal.slice(0, Math.max(1, max));
    return out;
  }
  /* put `id` into slot index `si` (0-based). Equipped elsewhere -> the two slots swap; already in that slot ->
     it is taken out (unless it is the last gun); beyond the filled slots -> appended. Returns a new array. */
  function assign(loadout, max, si, id) {
    var L = loadout.slice(), j = L.indexOf(id);
    si = Math.max(0, Math.min(max - 1, si | 0));
    if (si >= L.length) {
      if (j >= 0) L.splice(j, 1);
      if (L.length < max) L.push(id);
      return L;
    }
    if (j === si) { if (L.length > 1) L.splice(si, 1); return L; }
    if (j >= 0) { L[j] = L[si]; L[si] = id; return L; }
    L[si] = id;
    return L;
  }
  /* a gun picked up from a weapon stand: joins the arsenal; carried at once if there is room, otherwise it takes
     the place of the gun in hand (that one stays in the arsenal). {arsenal, loadout, slot (0-based)} */
  function pickup(loadout, arsenal, max, id, curId) {
    var A = uniq(arsenal.concat([id])), L = loadout.slice(), at = L.indexOf(id);
    if (at < 0) {
      if (L.length < max) { L.push(id); at = L.length - 1; }
      else { at = Math.max(0, L.indexOf(curId)); if (L.indexOf(curId) < 0) at = L.length - 1; L[at] = id; }
    }
    return { arsenal: A, loadout: L, slot: at };
  }

  /* ammo boxes: a gun's spare-ammo cap (1.5 x its reserve), and whether every carried gun that takes boxes is full
     (guns: {id: {def, reserve}}; infinite reserves and rocket launchers (def.ammo) never take boxes). A box walked over
     while this is true stays where it is (game.js updatePickups). */
  var RESERVE_CAP = 1.5;
  function reserveCap(def) { return Math.floor(def.reserve * RESERVE_CAP); }
  function ammoFull(guns) {
    return Object.keys(guns || {}).every(function (k) { var g = guns[k]; return g.reserve === Infinity || !!g.def.ammo || g.reserve >= reserveCap(g.def); });
  }
  IB.Loadout = { uniq: uniq, fixArsenal: fixArsenal, fix: fix, assign: assign, pickup: pickup, reserveCap: reserveCap, ammoFull: ammoFull, RESERVE_CAP: RESERVE_CAP };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
