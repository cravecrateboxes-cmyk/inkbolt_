/* INKBOLT - TEMPORARY tester switch (remove before release: delete this file and its <script> line in
   index.src.html). While DEV_MAX is on, the newest save slot is maxed out when the title screen opens:
   every campaign level cleared, player LV 30 (max XP, all 30 skill points to spend / respec freely, 3 loadout slots),
   every gun Legendary at gun level 30 (launchers with full magazines, Blast Hothead), a full rocket pool,
   lots of gems, every playable gun in the arsenal, legendary level-30 attachments (max rolls: grip, scope, acid
   muzzle, extended mag) fitted to every gun that takes them, a legendary level-30 Nova shield cell and a legendary
   vest worn, and a spare legendary Overcharge cell in the bag. Never runs in ?autotest=1. */
(function (IB) {
  'use strict';
  var DEV_MAX = true;
  if (!DEV_MAX || new URLSearchParams(location.search).get('autotest') === '1') return;
  var G = IB.Game, toTitle = G.toTitle, done = false;

  function best() { return 0.999; }          // top of every stat range
  // the max profile is applied once per save (slot.devMax); after that the save is the player's own progress.
  // force = the level picker: re-max now, keeping the skills already spent
  function maxOut(force) {
    var store = G.store, slot = store.newest();
    if (!slot) slot = store.newSlot(store.freeSlot() || 1, (Math.random() * 1e9) | 0);
    if (slot.devMax && !force) { G.slot = slot; return; }
    slot.devMax = 1;
    var top = IB.CAMPAIGN.length, plans = IB.CAMPAIGN;
    slot.highest = Math.max(slot.highest || 0, 20, top);
    slot.gems = Math.max(slot.gems || 0, 999999);
    slot.xp = Math.max(slot.xp || 0, IB.Skills.xpForLevel(IB.PLAYER_LEVEL_CAP));   // LV 30
    slot.plan = slot.plan && IB.LEVEL_PLANS[slot.plan] ? slot.plan : plans[0];
    var guns = IB.WEAPON_ORDER.filter(function (id) { return IB.Weapons.playable(id); });
    slot.arsenal = guns.slice(); slot.owned = guns.slice();
    slot.gunTier = {}; guns.forEach(function (id) { slot.gunTier[id] = 'orange'; });   // every gun at the top (Legendary) tier
    slot.gunLevel = {}; guns.forEach(function (id) { slot.gunLevel[id] = 30; });       // gun level 30
    slot.gunRoll = {}; guns.forEach(function (id) {                                     // launchers: biggest magazine
      var d = IB.WEAPONS[id]; if (d.magRoll) slot.gunRoll[id] = { mag: d.magRoll[1], elem: d.elements ? 'boom' : 'none' };
      if (d.wyrm) slot.gunRoll[id] = { mag: d.wyrm.mag[1], mult: d.wyrm.mult[1] };   // Wyrmforged: biggest magazine, x3
    });
    slot.rockets = IB.GunLevel ? IB.GunLevel.ROCKET.cap : 16;
    slot.melee = (IB.MELEE_WEAPONS || []).filter(function (id) { return IB.Assets.node['WPN_' + id.toUpperCase()]; });   // every melee weapon (V, B)
    slot.meleeSel = slot.melee.indexOf('katana') >= 0 ? 'katana' : slot.melee[0];
    slot.frag = true;                                                                     // frag cans (G)
    var pref = ['vanguard', 'scrapper', 'railspike', 'brick', 'hornet', 'needle', 'longtom', 'triplet', 'rivet', 'handcannon'];
    slot.loadout = pref.filter(function (id) { return guns.indexOf(id) >= 0; }).slice(0, 3);
    // gear: a fresh bag of the best items, one set per gun (the tester bag may go past the normal bag size)
    var L = IB.Loot, g = L.defaultGear();
    IB.LOOT.starters.forEach(function (s) { g[s.flag] = true; });
    function put(item) { if (L.addItem(g, item)) return item; item.id = 'g' + (g.next++); g.inv.push(item); g.found++; return item; }
    function rolls(perkPick) { var i = 0; return function () { return i++ === 3 ? perkPick : 0.999; }; }   // 4th roll: the shield perk
    L.equipShield(g, put(L.makeItem('shield', 'legendary', 30, rolls(0.9))).id);       // Nova
    put(L.makeItem('shield', 'legendary', 30, rolls(0.1)));                             // Overcharge, spare
    L.equipWorn(g, 'armor', put(L.makeItem('armor', 'legendary', 30, best)).id);
    var CANS = ['acid', 'shock', 'blast', 'void'];
    guns.forEach(function (id, gi) {
      var def = IB.WEAPONS[id];
      Object.keys(IB.LOOT.types).forEach(function (type) {
        if (!L.isAttachment({ type: type })) return;
        // one muzzle can per gun, the four kinds in turn (acid, Arc, Boom, Void) so every kind is in play
        if (CANS.indexOf(type) >= 0) { var want = CANS[gi % 4]; if (!L.compatible(L.makeItem(want, 'legendary', 30, best), id, def)) want = 'shock'; if (type !== want) return; }
        var probe = L.makeItem(type, 'legendary', 30, best);
        if (!L.compatible(probe, id, def)) return;
        L.attach(g, id, def, put(probe).id);
      });
    });
    CANS.forEach(function (t) { put(L.makeItem(t, 'legendary', 30, best)); });   // a spare of each can in the bag
    slot.gear = g;
    if (!force) slot.skills = {};             // all points free: spend / respec as you like in Tab -> Skills
    store.save(slot);
    G.slot = slot;
  }

  // DEV level selector (right edge, title screen and pause menu): click a level to start on it at once. The save is
  // maxed again first, so the newest guns, melee weapons, frag cans and gear are always in it.
  function picker() {
    var el = document.getElementById('devLevels');
    if (!el) {
      el = document.createElement('div'); el.id = 'devLevels';
      el.style.cssText = 'position:fixed;right:12px;top:50%;transform:translateY(-50%);z-index:60;display:flex;flex-direction:column;gap:5px;' +
        'background:rgba(10,14,30,.86);border:3px solid #3FE0D0;padding:8px;max-height:82vh;overflow:auto;font:600 13px Archivo,sans-serif;color:#fff;width:190px';
      el.innerHTML = '<div style="color:#FFD23F;letter-spacing:.06em">DEV · START ON LEVEL</div>' + IB.CAMPAIGN.map(function (id, i) {
        var p = IB.LEVEL_PLANS[id];
        return '<button data-dev-plan="' + id + '" style="min-height:34px;text-align:left;background:#1d2a4a;color:#fff;border:2px solid #3FE0D0;padding:4px 8px;cursor:pointer;font:inherit">' +
          (i + 1) + '. ' + (p.name || id) + '</button>';
      }).join('');
      el.addEventListener('click', function (e) {
        var b = e.target.closest('[data-dev-plan]'); if (!b) return;
        var plan = IB.LEVEL_PLANS[b.getAttribute('data-dev-plan')];
        el.hidden = true;
        var sk = G.slot && G.slot.skills;   // keep the skills already spent
        try { maxOut(true); } catch (err) { G.errors.push('devmax: ' + err.message); }
        if (sk) { G.slot.skills = sk; G.store.save(G.slot); }
        G.slot.plan = plan.id; G.slot.level = plan.level; G.store.save(G.slot);
        IB.Menus.wipe(function () { G.switchPlan(plan).then(function () { G.startLevel(); }); });
      });
      document.body.appendChild(el);
    }
    el.hidden = false;
  }
  setInterval(function () { var el = document.getElementById('devLevels'); if (el) el.hidden = !(G.mode === 'title' || G.mode === 'paused'); }, 300);

  // the Wyrmforged Ironjaw replaces the old one in the tester save: top roll (13 rounds, x3), Legendary, LV 30 gun level
  function wyrmUpdate(slot) {
    if (!slot || slot.wyrmV || !IB.WEAPONS.handcannon) return;
    slot.wyrmV = 1;
    var id = 'handcannon';
    slot.gunRoll = slot.gunRoll || {}; slot.gunRoll[id] = { mag: IB.WEAPONS[id].wyrm.mag[1], mult: IB.WEAPONS[id].wyrm.mult[1] };
    slot.gunTier = slot.gunTier || {}; slot.gunTier[id] = 'orange';
    slot.gunLevel = slot.gunLevel || {}; slot.gunLevel[id] = 30;
    if (slot.arsenal && slot.arsenal.indexOf(id) < 0) slot.arsenal.push(id);
    slot.owned = (slot.arsenal || []).slice();
    G.store.save(slot);
  }

  G.toTitle = function () {
    if (!done) { done = true; try { maxOut(false); } catch (e) { G.errors.push('devmax: ' + e.message); } }
    try { wyrmUpdate(G.store.newest()); } catch (e) { G.errors.push('devmax: ' + e.message); }
    toTitle.apply(this, arguments);
    picker();
  };
})(window.IB = window.IB || {});
