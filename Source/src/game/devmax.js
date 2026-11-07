/* INKBOLT - TEMPORARY tester switch (remove before release: delete this file and its <script> line in
   index.src.html). While DEV_MAX is on, the newest save slot is maxed out when the title screen opens:
   every campaign level cleared (max player level, all 22 skill points to spend / respec freely, 3 loadout slots),
   lots of gems, every playable gun in the arsenal, epic level-20 attachments (max rolls) fitted to every gun that
   takes them, and an epic level-20 shield worn. Never runs in ?autotest=1. */
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
    slot.melee = (IB.MELEE_WEAPONS || []).filter(function (id) { return IB.Assets.node['WPN_' + id.toUpperCase()]; });   // every melee weapon (V, B)
    slot.meleeSel = slot.melee.indexOf('katana') >= 0 ? 'katana' : slot.melee[0];
    slot.frag = true;                                                                     // frag cans (G)
    var pref = ['vanguard', 'scrapper', 'railspike', 'brick', 'hornet', 'needle', 'longtom', 'triplet', 'rivet', 'handcannon'];
    slot.loadout = pref.filter(function (id) { return guns.indexOf(id) >= 0; }).slice(0, 3);
    // gear: a fresh bag of the best items, one set per gun
    var L = IB.Loot, g = L.defaultGear();
    g.starter = true;
    var shield = L.addItem(g, L.makeItem('shield', 'epic', 20, best));
    L.equipShield(g, shield.id);
    guns.forEach(function (id) {
      var def = IB.WEAPONS[id];
      ['grip', 'scope', 'acid'].forEach(function (type) {
        var probe = L.makeItem(type, 'epic', 20, best);
        if (!L.compatible(probe, id, def)) return;
        var it = L.addItem(g, probe);
        if (it) L.attach(g, id, def, it.id);
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
