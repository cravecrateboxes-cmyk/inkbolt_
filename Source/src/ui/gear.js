/* INKBOLT Gear tab: what the player carries and wears.
     IB.GearUI.render(containerEl, G)   fills containerEl (the Gear tab of the in-game menu): equipped shield, each
                                        carried gun with its attachment slots, and the bag (equip / fit to a gun /
                                        move / detach / discard with a confirm tap). Changes apply at once
                                        (IB.Gear.refresh) and are saved.
     IB.GearUI.open(G)                  standalone panel in the overlay (tests, or a menu without tabs).
   Buttons use data-gact (not data-act) so the host menu's click handler never sees them. */
(function (IB) {
  'use strict';
  var GU = IB.GearUI = {};
  var esc = function (s) { return IB.LootHUD ? IB.LootHUD.esc(s) : String(s); };
  function icon(t) { return IB.LootHUD ? IB.LootHUD.icon(t) : ''; }
  function shortName(def) { var p = String(def.name).split(' '); return p.length > 1 ? p.slice(1).join(' ') : def.name; }
  function sfx(n) { if (IB.Audio) IB.Audio.play(n || 'ui'); }
  function owned(G) { return G.ws ? Object.keys(G.ws.guns).sort(function (a, b) { return IB.WEAPONS[a].slot - IB.WEAPONS[b].slot; }) : (G.slot && G.slot.owned) || []; }

  function rarityLine(it) { var rc = IB.LOOT.rarityById[it.rarity]; return rc.name + ' · Lv ' + it.level + ' · ' + IB.LootHUD.typeName(it.type); }
  function stats(it) { return IB.Loot.statLines(it).map(function (l) { return '<i>' + esc(l.k) + ' <b>' + esc(l.v) + '</b></i>'; }).join(''); }

  function itemCard(it, G, g, confirmId) {
    var L = IB.Loot, rc = IB.LOOT.rarityById[it.rarity], at = L.attachedTo(g, it.id), worn = g.shield === it.id;
    var where = worn ? 'Equipped' : at ? 'On ' + IB.WEAPONS[at.weapon].name : '';
    var acts = '';
    if (it.type === 'shield') {
      acts += worn ? '<button class="plate btn gu-btn" data-gact="unequip" data-id="' + it.id + '">Unequip</button>'
        : '<button class="plate btn gu-btn primary" data-gact="equip" data-id="' + it.id + '">Equip</button>';
    } else {
      var fits = owned(G).filter(function (w) { return L.compatible(it, w, IB.WEAPONS[w]); });
      if (fits.length) {
        acts += '<div class="seg gu-fit" role="group" aria-label="Fit to">' + fits.map(function (w) {
          var on = at && at.weapon === w;
          return '<button data-gact="' + (on ? 'detach' : 'fit') + '" data-id="' + it.id + '" data-w="' + w + '" aria-pressed="' + !!on + '" title="' + esc(IB.WEAPONS[w].name) + '">' +
            '<span class="gu-wicon">' + IB.HUD.icon(IB.WEAPONS[w].cls) + '</span>' + esc(shortName(IB.WEAPONS[w])) + '</button>';
        }).join('') + '</div>';
      } else acts += '<span class="gu-nofit">Fits none of your guns</span>';
    }
    var sure = confirmId === it.id;
    acts += '<button class="plate btn danger gu-btn gu-discard' + (sure ? ' sure' : '') + '" data-gact="discard" data-id="' + it.id + '">' + (sure ? 'Tap again to scrap' : 'Scrap') + '</button>';
    return '<div class="plate ink gu-item ' + it.rarity + (worn || at ? ' worn' : '') + '" style="--rar:' + rc.color + '" data-item="' + it.id + '">' +
      '<span class="gu-icon">' + icon(it.type) + '</span>' +
      '<div class="gu-info"><span class="gu-rar">' + esc(rarityLine(it)) + '</span><b class="gu-name">' + esc(String(it.name).toUpperCase()) + '</b>' +
      '<span class="gu-stats">' + stats(it) + '</span>' + (where ? '<span class="gu-where">' + esc(where) + '</span>' : '') + '</div>' +
      '<div class="gu-acts">' + acts + '</div></div>';
  }

  function weaponRow(w, G, g) {
    var L = IB.Loot, def = IB.WEAPONS[w], items = L.weaponItems(g, w), slots = L.slotsFor(w, def);
    var cells = slots.map(function (sl) {
      var it = items[sl];
      if (!it) return '<div class="gu-slot empty"><span class="gu-slot-k">' + IB.LOOT.slotNames[sl] + '</span><span class="gu-slot-v">Empty</span></div>';
      var rc = IB.LOOT.rarityById[it.rarity];
      return '<div class="gu-slot ' + it.rarity + '" style="--rar:' + rc.color + '"><span class="gu-slot-k">' + IB.LOOT.slotNames[sl] + '</span><span class="gu-slot-v">' + esc(it.name) + '</span></div>';
    }).join('');
    var live = G.ws && G.ws.guns[w] ? G.ws.guns[w].def : def;
    var mods = [];
    if (live.recoil < def.recoil - 1e-9) mods.push('Recoil ' + Math.round((1 - live.recoil / def.recoil) * -100) + '%');
    if (live.aimZoom < (def.aimZoom || 0.85) - 1e-9) mods.push('Zoom ' + (1 / live.aimZoom).toFixed(1) + 'x');
    if (live.acid) mods.push('Acid +' + Math.round(live.acid * 100) + '%');
    return '<div class="plate ink gu-wpn"><div class="gu-wpn-h"><span class="gu-wicon">' + IB.HUD.icon(def.cls) + '</span><b>' + esc(def.name) + '</b>' +
      (mods.length ? '<span class="gu-mods">' + esc(mods.join(' · ')) + '</span>' : '') + '</div>' +
      '<div class="gu-slots">' + (cells || '<div class="gu-slot empty"><span class="gu-slot-v">No attachment slots</span></div>') + '</div></div>';
  }

  GU.render = function (root, G) {
    if (!root || !G) return;
    var g = IB.Gear.gear(G);
    if (!g) { root.innerHTML = '<p class="gu-note">Start a game to collect gear.</p>'; return; }
    var L = IB.Loot, confirmId = root.dataset.confirm || '';
    var sh = g.shield ? L.find(g, g.shield) : null, ps = G.player && G.player.shield;
    var cleared = (G.slot && G.slot.highest) || 0, minC = IB.LOOT.types.shield.minCleared;
    var shieldHtml = sh ? '<div class="plate ink gu-shield ' + sh.rarity + '" style="--rar:' + IB.LOOT.rarityById[sh.rarity].color + '"><span class="gu-icon">' + icon('shield') + '</span>' +
      '<div class="gu-info"><span class="gu-rar">' + esc(rarityLine(sh)) + '</span><b class="gu-name">' + esc(sh.name.toUpperCase()) + '</b><span class="gu-stats">' + stats(sh) + '</span></div>' +
      (ps ? '<b class="gu-cap">' + Math.ceil(ps.cur) + '<span>/' + ps.max + '</span></b>' : '') + '</div>'
      : '<div class="gu-slot empty wide"><span class="gu-slot-k">Shield</span><span class="gu-slot-v">' + (cleared >= minC ? 'None equipped' : 'Shield cells start dropping after level ' + minC) + '</span></div>';
    var list = g.inv.slice().sort(function (a, b) {
      var wa = (g.shield === a.id || L.attachedTo(g, a.id)) ? 1 : 0, wb = (g.shield === b.id || L.attachedTo(g, b.id)) ? 1 : 0;
      return wb - wa || L.rarityRank(b.rarity) - L.rarityRank(a.rarity) || b.level - a.level || (a.id < b.id ? -1 : 1);
    });
    root.innerHTML = '<div class="gearui">' +
      '<section class="gu-col"><h3 class="gu-h">Shield</h3>' + shieldHtml +
      '<h3 class="gu-h">Guns</h3><div class="gu-weapons">' + owned(G).map(function (w) { return weaponRow(w, G, g); }).join('') + '</div></section>' +
      '<section class="gu-col"><h3 class="gu-h">Bag <span class="gu-count">' + g.inv.length + '/' + IB.LOOT.invCap + '</span></h3>' +
      (list.length ? '<div class="gu-bag">' + list.map(function (it) { return itemCard(it, G, g, confirmId); }).join('') + '</div>'
        : '<p class="gu-note">No gear yet. Robots drop a shield cell or a gun attachment now and then (about one in twenty). Walk over the beam to pick it up.</p>') +
      '</section></div>';
    if (!root._gearBound) {
      root._gearBound = true;
      root.addEventListener('click', function (e) {
        var b = e.target.closest('[data-gact]'); if (!b || !root.contains(b)) return;
        e.stopPropagation();
        GU.act(root, root._G || IB.Game, b.dataset.gact, b.dataset.id, b.dataset.w);
      });
    }
    root._G = G;
  };

  GU.act = function (root, G, act, id, w) {
    var L = IB.Loot, g = IB.Gear.gear(G); if (!g) return false;
    var ok = false, fill = false;
    if (act !== 'discard') delete root.dataset.confirm;
    switch (act) {
      case 'equip': ok = L.equipShield(g, id); fill = false; break;
      case 'unequip': ok = L.equipShield(g, null); break;
      case 'fit': ok = L.attach(g, w, IB.WEAPONS[w], id); break;
      case 'detach': { var at = L.attachedTo(g, id); ok = !!at && L.detach(g, at.weapon, at.slot); break; }
      case 'discard':
        if (root.dataset.confirm !== id) { root.dataset.confirm = id; sfx('ui'); GU.render(root, G); return false; }
        delete root.dataset.confirm; ok = L.discard(g, id); break;
    }
    if (ok) {
      // a newly equipped shield starts empty and charges up (no free refill from swapping cells mid-fight)
      IB.Gear.refresh(G, fill);
      if (act === 'equip' && G.player.shield) { G.player.shield.cur = 0; G.player.shield.since = G.player.shield.delay; }
      IB.Gear.save(G);
      sfx(act === 'discard' ? 'uiBack' : act === 'fit' || act === 'equip' ? 'magIn' : 'ui');
    }
    GU.render(root, G);
    return ok;
  };

  GU.open = function (G) {
    if (G.mode === 'play') G.pause();
    var ov = document.getElementById('overlay');
    ov.hidden = false; ov.className = 'overlay dim';
    ov.innerHTML = '<div class="screen center-screen"><section class="plate ink panel gear-panel" aria-label="Gear">' +
      '<h2>Gear</h2><div class="hazard"></div><div id="gearRoot"></div>' +
      '<button class="plate btn primary" data-act="resume" data-esc="1"><span>Back to the fight</span></button></section></div>';
    if (IB.Menus) IB.Menus.cur = 'gear';
    ov.scrollTop = 0;
    GU.render(document.getElementById('gearRoot'), G);
  };
})(window.IB = window.IB || {});
