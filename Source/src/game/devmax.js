/* INKBOLT - TEMPORARY tester switch (remove before release: delete this file and its <script> line in
   index.src.html). While DEV_MAX is on, the newest save slot is maxed out when the title screen opens:
   every campaign level cleared (max player level, all 22 skill points to spend / respec freely, 3 loadout slots),
   lots of gems, every playable gun in the arsenal, legendary level-20 attachments (max rolls: grip, scope, acid
   muzzle, extended mag) fitted to every gun that takes them, a legendary level-20 Nova shield cell and a legendary
   vest worn, and a spare legendary Overcharge cell in the bag. Never runs in ?autotest=1. */
(function (IB) {
  'use strict';
  var DEV_MAX = true;
  if (!DEV_MAX || new URLSearchParams(location.search).get('autotest') === '1') return;
  var G = IB.Game, toTitle = G.toTitle, done = false;

  function best() { return 0.999; }          // top of every stat range
  function maxOut() {
    var store = G.store, slot = store.newest();
    if (!slot) slot = store.newSlot(store.freeSlot() || 1, (Math.random() * 1e9) | 0);
    var top = IB.CAMPAIGN.length, plans = IB.CAMPAIGN;
    slot.highest = Math.max(slot.highest || 0, 20, top);
    slot.gems = Math.max(slot.gems || 0, 999999);
    slot.plan = slot.plan && IB.LEVEL_PLANS[slot.plan] ? slot.plan : plans[0];
    var guns = IB.WEAPON_ORDER.filter(function (id) { return IB.Weapons.playable(id); });
    slot.arsenal = guns.slice(); slot.owned = guns.slice();
    var pref = ['brick', 'hornet', 'needle', 'longtom', 'triplet', 'rivet', 'handcannon'];
    slot.loadout = pref.filter(function (id) { return guns.indexOf(id) >= 0; }).slice(0, 3);
    // gear: a fresh bag of the best items, one set per gun (the tester bag may go past the normal bag size)
    var L = IB.Loot, g = L.defaultGear();
    IB.LOOT.starters.forEach(function (s) { g[s.flag] = true; });
    function put(item) { if (L.addItem(g, item)) return item; item.id = 'g' + (g.next++); g.inv.push(item); g.found++; return item; }
    function rolls(perkPick) { var i = 0; return function () { return i++ === 3 ? perkPick : 0.999; }; }   // 4th roll: the shield perk
    L.equipShield(g, put(L.makeItem('shield', 'legendary', 20, rolls(0.9))).id);       // Nova
    put(L.makeItem('shield', 'legendary', 20, rolls(0.1)));                             // Overcharge, spare
    L.equipWorn(g, 'armor', put(L.makeItem('armor', 'legendary', 20, best)).id);
    guns.forEach(function (id) {
      var def = IB.WEAPONS[id];
      Object.keys(IB.LOOT.types).forEach(function (type) {
        if (!L.isAttachment({ type: type })) return;
        var probe = L.makeItem(type, 'legendary', 20, best);
        if (!L.compatible(probe, id, def)) return;
        L.attach(g, id, def, put(probe).id);
      });
    });
    slot.gear = g;
    slot.skills = {};                         // all points free: spend / respec as you like in Tab -> Skills
    store.save(slot);
    G.slot = slot;
  }

  G.toTitle = function () {
    if (!done) { done = true; try { maxOut(); } catch (e) { G.errors.push('devmax: ' + e.message); } }
    toTitle.apply(this, arguments);
  };
})(window.IB = window.IB || {});
