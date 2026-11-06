/* INKBOLT - TEMPORARY tester switch (remove before release: delete this file and its <script> line in
   index.src.html). While DEV_MAX is on, the newest save slot is maxed out when the title screen opens:
   every campaign level cleared (max player level, all 22 skill points to spend / respec freely, 3 loadout slots),
   lots of gems, every playable gun in the arsenal, epic level-20 attachments (max rolls) fitted to every gun that
   takes them, an epic level-20 shield worn, and a level picker on the title screen. Never runs in ?autotest=1. */
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

  // level picker: every campaign level, on the title screen only
  function picker() {
    var el = document.getElementById('devLevels');
    if (!el) {
      el = document.createElement('div'); el.id = 'devLevels';
      el.style.cssText = 'position:fixed;right:16px;bottom:72px;z-index:60;display:flex;flex-direction:column;gap:6px;' +
        'background:rgba(10,14,30,.82);border:3px solid #3FE0D0;padding:10px;max-height:70vh;overflow:auto;font:600 14px Archivo,sans-serif;color:#fff';
      el.innerHTML = '<div style="color:#FFD23F">TEST: PICK A LEVEL</div>' + IB.CAMPAIGN.map(function (id, i) {
        var p = IB.LEVEL_PLANS[id];
        return '<button data-dev-plan="' + id + '" style="min-height:40px;text-align:left;background:#1d2a4a;color:#fff;border:2px solid #3FE0D0;padding:6px 10px;cursor:pointer">' +
          (i + 1) + '. ' + (p.name || id) + '</button>';
      }).join('');
      el.addEventListener('click', function (e) {
        var b = e.target.closest('[data-dev-plan]'); if (!b) return;
        var plan = IB.LEVEL_PLANS[b.getAttribute('data-dev-plan')];
        el.hidden = true;
        G.slot.plan = plan.id; G.store.save(G.slot);
        IB.Menus.wipe(function () { G.switchPlan(plan).then(function () { G.startLevel(); }); });
      });
      document.body.appendChild(el);
    }
    el.hidden = false;
  }
  setInterval(function () { var el = document.getElementById('devLevels'); if (el && G.mode !== 'title') el.hidden = true; }, 500);

  G.toTitle = function () {
    if (!done) { done = true; try { maxOut(); } catch (e) { G.errors.push('devmax: ' + e.message); } }
    toTitle.apply(this, arguments);
    picker();
  };
})(window.IB = window.IB || {});
