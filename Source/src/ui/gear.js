/* INKBOLT inventory: guns carried, shield, gun attachments and the backpack, in one screen.
     IB.GearUI.render(containerEl, G)   fills containerEl (the Inventory tab of the field kit): the item card + ammo on
                                        the left, EQUIPPED in the middle (weapon slots 1-3, slot 3 locked until level 10
                                        is cleared, the attachment slots under each carried gun, the shield slot, gems),
                                        BACKPACK on the right (weapons, attachments, shields). Changes apply at once
                                        (IB.Gear.refresh) and are saved.
     IB.GearUI.open(G)                  the same screen in the overlay, paused (tests, or a menu without tabs).
     IB.GearUI.reset(G)                 cursor back to the first free weapon slot (the field kit calls it on open).
   Selecting: mouse and keyboard act at once (hover / focus previews the card, click / Enter equips);
   touch taps select first (the card shows the item with its actions), a second tap on the same tile equips.
   Buttons use data-gact (not data-act) so the host menu's click handler never sees them. */
(function (IB) {
  'use strict';
  var GU = IB.GearUI = { state: { slot: 0, sel: null, target: null, confirm: null } };
  var S = GU.state, ptr = null;
  var esc = function (s) { return IB.LootHUD ? IB.LootHUD.esc(s) : String(s); };
  function icon(t) { return IB.LootHUD ? IB.LootHUD.icon(t) : ''; }
  function sfx(n) { if (IB.Audio) IB.Audio.play(n || 'ui'); }
  function svg(d, cls) { return '<svg class="' + (cls || 'g24') + '" viewBox="0 0 24 24" aria-hidden="true">' + d + '</svg>'; }
  function touch() { return !!(IB.Input && IB.Input.touch); }
  var LOCK = '<path d="M7 10V7a5 5 0 0 1 10 0v3" fill="none" stroke="currentColor" stroke-width="2.6"/><rect x="5" y="10" width="14" height="11" fill="currentColor"/><path d="M12 14v3" stroke="var(--ink)" stroke-width="2.4"/>';
  var CHECK = '<path d="M3 12.5 9 18 21 6" fill="none" stroke="currentColor" stroke-width="3.6"/>';
  var PLUS = '<path d="M12 4v16M4 12h16" stroke="currentColor" stroke-width="3.4"/>';
  var ACIDI = '<path d="M12 2c4 6 7 9.5 7 13a7 7 0 0 1-14 0c0-3.5 3-7 7-13z" fill="currentColor"/><path d="M9 15a3 3 0 0 0 3 3" fill="none" stroke="var(--ink)" stroke-width="2"/>';
  var SHOCKI = '<path d="M14 1 4 14h6l-2 9 11-14h-6z" fill="currentColor"/>';
  // stat glyphs for the item card
  var SI = {
    dmg: '<circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M12 1v7M12 16v7M1 12h7M16 12h7" stroke="currentColor" stroke-width="2.6"/>',
    acc: '<path d="M12 3v18M3 12h18" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="currentColor"/>',
    rate: '<path d="M4 6h10l-2-3M4 12h14M4 18h10l-2 3" fill="none" stroke="currentColor" stroke-width="2.6"/>',
    reload: '<path d="M19 12a7 7 0 1 1-2.05-4.95" fill="none" stroke="currentColor" stroke-width="3"/><path d="M21 3v7h-7z" fill="currentColor"/>',
    mag: '<path d="M8 2h8l-1.2 20H9.2z" fill="currentColor"/><path d="M10 7h4M10 11h4M10 15h4" stroke="var(--ink)" stroke-width="1.8"/>',
    recoil: '<path d="M4 20 18 6M12 4h8v8" fill="none" stroke="currentColor" stroke-width="3"/>',
    cap: '<path d="M12 2 21 6v6c0 5-4 8.5-9 10-5-1.5-9-5-9-10V6z" fill="currentColor"/>',
    delay: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="3"/><path d="M12 6.5V12l4 2.5" fill="none" stroke="currentColor" stroke-width="2.4"/>',
    zoom: '<circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="3"/><path d="M15 15l6 6" stroke="currentColor" stroke-width="3.4"/>',
    acid: ACIDI, noise: '<path d="M3 9h4l5-5v16l-5-5H3z" fill="currentColor"/><path d="M16 9l5 6M21 9l-5 6" stroke="currentColor" stroke-width="2.4"/>'
  };

  // ---------- gun presentation: grade colour (by when it unlocks), maker, flavour ----------
  var GRADES = [[3, 'Standard', '#E4DFD3'], [7, 'Tuned', '#6BE05A'], [11, 'Rare', '#4A9BFF'], [15, 'Epic', '#B77BFF'], [99, 'Prime', '#FF9A2E']];
  function grade(def) { var u = def.unlock || 1; for (var i = 0; i < GRADES.length; i++) if (u <= GRADES[i][0]) return { name: GRADES[i][1], color: GRADES[i][2] }; return { name: 'Prime', color: '#FF9A2E' }; }
  var MAKERS = { P: 'Pocketworks', R: 'Revolta', KV: 'Kettlevolt', AR: 'Rivetech', DMR: 'Longreach', LMG: 'Brickhaus', SR: 'Pinpoint', RL: 'Canworks', M: 'Junkpop', FX: 'Junkpop', Mk: 'Edgeworks', BA: 'Edgeworks', SG: 'Scrapyard Arms' };
  function maker(def) { var p = String(def.name).split('-')[0]; return MAKERS[p] || 'Inkworks'; }
  var FLAVOR = {
    pip: 'Old faithful. Never runs dry.', handcannon: 'Six reasons to stay down.', twintap: 'Say it twice.', buzz: 'Bzzzzzzzt.',
    whisk: 'Spray first. Aim later.', hornet: 'Float like a can, sting like a hornet.', rivet: 'Holds the whole town together.',
    triplet: 'Three\'s company.', longtom: 'Reach out and dent someone.', brick: 'Laying down the foundations.',
    needle: 'Through the eye, through the core.', cancannon: 'Return to sender.', frag: 'Pull pin. Throw can. Run.',
    popflash: 'Lights out, bots.', katana: 'Quiet. Sharp. Final.', fireaxe: 'Knock knock.', scrapper: 'Up close and impersonal.',
    shield: 'Charge it up, then hide behind it.', grip: 'Steady hands, steady ink.', scope: 'Eyes on the core.', acid: 'Hiss. Fizz. Melt.'
  };
  function rarity(it) { return IB.LOOT.rarityById[it.rarity]; }

  // ---------- data access ----------
  function gearOf(G) { return IB.Gear && IB.Gear.gear(G); }
  function loadout(G) { return (G.slot && G.slot.loadout && G.slot.loadout.length) ? G.slot.loadout.slice() : (G.ws ? IB.Weapons.ownedSlots(G.ws).map(function (k) { return G.ws.slots[k]; }) : []); }
  function arsenal(G) { return (G.slot && G.slot.arsenal) || loadout(G); }
  function maxSlots(G) { return G.progress ? G.progress().loadoutMax : IB.Skills.loadoutMax((G.slot && G.slot.highest) || 0); }
  function skillFx(G) { return IB.Skills.effects((G.slot && G.slot.skills) || {}); }
  function modsDef(g, w) { return IB.Loot.applyMods(IB.WEAPONS[w], g ? IB.Loot.weaponItems(g, w) : {}); }
  // where an item is: {worn} | {w, slot, carried} | null (loose in the backpack)
  function placeOf(g, it, lo) {
    if (g.shield === it.id) return { worn: true };
    var at = IB.Loot.attachedTo(g, it.id);
    return at ? { w: at.weapon, slot: at.slot, carried: lo.indexOf(at.weapon) >= 0 } : null;
  }

  /* gun card stats with skills applied: [{key, label, icon, v, txt, better}] */
  function gunStats(G, w, g) {
    var d = modsDef(g, w), fx = skillFx(G), wfx = (G.ws && G.ws.fx) || {};
    var dmg = d.damage * (d.pellets || 1) * fx.dmgMul;
    var rate = d.cycle > 0 ? (d.burst > 1 ? d.burst / d.cycle : 1 / d.cycle) * fx.rateMul : 0;
    var mag = IB.Weapons.magSize({ fx: { magMul: fx.magMul, magLevel: wfx.magLevel || 0 } }, d);
    var rl = d.reload * fx.reloadMul * ((G.fx && G.fx.reloadMul) || 1);
    var acc = Math.max(5, Math.min(99.5, 100 - d.spreadHip * 12));
    var out = [{ key: 'dmg', label: 'Damage', icon: 'dmg', v: dmg, txt: (d.pellets > 1 ? Math.round(d.damage * fx.dmgMul) + ' x' + d.pellets : String(Math.round(dmg))), better: 'high' }];
    if (d.spreadHip > 0) out.push({ key: 'acc', label: 'Accuracy', icon: 'acc', v: acc, txt: acc.toFixed(1), better: 'high' });
    if (rate > 0) out.push({ key: 'rate', label: 'Fire rate', icon: 'rate', v: rate, txt: rate.toFixed(1) + '/s', better: 'high' });
    if (d.reload > 0) out.push({ key: 'reload', label: 'Reload', icon: 'reload', v: rl, txt: rl.toFixed(1) + ' s', better: 'low' });
    if (d.mag > 0) out.push({ key: 'mag', label: 'Magazine', icon: 'mag', v: mag, txt: mag === Infinity ? '∞' : String(mag), better: 'high' });
    if (d.recoil > 0) out.push({ key: 'recoil', label: 'Recoil', icon: 'recoil', v: d.recoil, txt: d.recoil.toFixed(2), better: 'low' });
    return { lines: out, def: d, fx: fx };
  }
  var ITEM_KEYS = { shield: [['capacity', 'cap', 'high'], ['rate', 'rate', 'high'], ['delay', 'delay', 'low']], grip: [['recoil', 'recoil', 'high'], ['spread', 'acc', 'high']],
    scope: [['zoom', 'zoom', 'high'], ['aimSpread', 'acc', 'high']], acid: [['acid', 'acid', 'high'], [null, 'noise']] };
  function itemStats(it) {
    var keys = ITEM_KEYS[it.type] || [];
    return IB.Loot.statLines(it).map(function (l, i) { var k = keys[i] || []; return { key: k[0], label: l.k, icon: k[1] || 'dmg', v: k[0] ? it.stats[k[0]] : 0, txt: l.v, better: k[2] }; });
  }
  function cmpMark(a, b) {
    if (!b || a.v == null || b.v == null || !a.better || Math.abs(a.v - b.v) < 1e-6) return '';
    var up = a.better === 'low' ? a.v < b.v : a.v > b.v;
    return '<i class="cmp ' + (up ? 'up' : 'dn') + '" aria-label="' + (up ? 'better' : 'worse') + '">' + (up ? '▲' : '▼') + '</i>';
  }
  function statList(lines, vs) {
    var by = {}; (vs || []).forEach(function (l) { by[l.key || l.label] = l; });
    return '<ul class="ic-stats">' + lines.map(function (l) {
      return '<li>' + svg(SI[l.icon] || SI.dmg) + '<span>' + esc(l.label) + '</span><b>' + esc(l.txt) + '</b>' + cmpMark(l, by[l.key || l.label]) + '</li>';
    }).join('') + '</ul>';
  }

  // ---------- card (left column) ----------
  function cardFor(G, g, spec) {
    var lo = loadout(G), max = maxSlots(G);
    if (!spec) return '<div class="holo hsel inv-card empty"><p class="ic-empty">Point at a gun or a piece of gear to see its card.</p></div>';
    if (spec.k === 'lock') {
      return '<div class="holo hsel inv-card locked"><div class="ic-req">Weapon slot 3</div><b class="ic-name">' + svg(LOCK, 'g24 ic-lock') + 'Locked</b>' +
        '<p class="ic-note">Beat level ' + IB.LOADOUT_RULES.extraAfter + ' (the Dumpster Tank) to carry a third gun.</p></div>';
    }
    if (spec.k === 'emptyslot') {
      return '<div class="holo hsel inv-card empty"><div class="ic-req">Weapon slot ' + (spec.i + 1) + '</div><b class="ic-name">Empty slot</b>' +
        '<p class="ic-note">' + (touch() ? 'Tap a gun in the backpack to carry it here.' : 'Pick a gun from the backpack to carry it here. Keys 1–' + max + ' switch guns in the fight.') + '</p></div>';
    }
    if (spec.k === 'empty' || spec.k === 'emptyshield') {
      var slotName = spec.k === 'emptyshield' ? 'Shield' : IB.LOOT.slotNames[spec.slot];
      var fits = g.inv.filter(function (it) { return spec.k === 'emptyshield' ? it.type === 'shield' && g.shield !== it.id : IB.Loot.slotOf(it) === spec.slot && IB.Loot.compatible(it, spec.w, IB.WEAPONS[spec.w]); });
      var minC = IB.LOOT.types.shield.minCleared, cleared = (G.slot && G.slot.highest) || 0;
      var note = spec.k === 'emptyshield' && cleared < minC ? 'Shield cells start dropping after level ' + minC + '.' :
        fits.length ? fits.length + ' in your backpack fit' + (fits.length === 1 ? 's' : '') + ' here: they glow yellow.' : 'Nothing in your backpack fits. Robots drop gear now and then (about one in twenty).';
      return '<div class="holo hsel inv-card empty"><div class="ic-req">' + (spec.w ? esc(IB.WEAPONS[spec.w].name) : 'Equipped') + '</div><b class="ic-name">Empty ' + esc(slotName.toLowerCase()) + ' slot</b><p class="ic-note">' + esc(note) + '</p></div>';
    }
    var acts = '', head = '', body = '', foot = '', tag = '', color = '#E4DFD3';
    if (spec.k === 'gun') {
      var w = spec.id, def = IB.WEAPONS[w]; if (!def) return cardFor(G, g, null);
      var at = lo.indexOf(w), st = gunStats(G, w, g), gr = grade(def), items = IB.Loot.weaponItems(g, w);
      color = gr.color;
      var cmpW = at < 0 ? lo[Math.min(S.slot, lo.length - 1)] : null, vs = cmpW && cmpW !== w ? gunStats(G, cmpW, g).lines : null;
      head = '<div class="ic-req">' + (at >= 0 ? svg(CHECK, 'g24 ic-check') : '') + gr.name + ' · ' + IB.HUD.clsName(def.cls) + ' · unlocks at level ' + (def.unlock || 1) + '</div>' +
        '<b class="ic-name">' + esc(def.name) + '</b>' + (vs ? '<div class="ic-vs">Compared with ' + esc(IB.WEAPONS[cmpW].name) + '</div>' : '');
      var notes = ['<p class="flav">' + esc(FLAVOR[w] || '') + '</p>'];
      if (st.def.acid) notes.push('<p>Acid +' + Math.round(st.def.acid * 100) + '% of each hit over ' + st.def.acidDur.toFixed(1) + ' s</p>');
      if (st.fx.shock) notes.push('<p>Shock rounds (Electrify)</p>');
      if (st.def.optic) notes.push('<p>Scope ' + (1 / st.def.aimZoom).toFixed(1) + 'x zoom</p>');
      if (def.scopeZoom) notes.push('<p>Built-in ' + def.scopeZoom + 'x scope</p>');
      if (def.splash) notes.push('<p>Splash damage, ' + def.radius + ' m radius</p>');
      if (def.reserve === Infinity) notes.push('<p>Unlimited spare ammo</p>');
      Object.keys(items).forEach(function (sl) { notes.push('<p class="ic-mod" style="--rar:' + rarity(items[sl]).color + '">' + IB.LOOT.slotNames[sl] + ': <b>' + esc(items[sl].name) + '</b></p>'); });
      body = statList(st.lines, vs) + '<div class="ic-notes">' + notes.join('') + '</div>';
      var elem = st.def.acid ? svg(ACIDI, 'g24 ic-elem acid') : st.fx.shock ? svg(SHOCKI, 'g24 ic-elem shock') : '';
      foot = '<div class="ic-foot"><span class="ic-maker">' + esc(maker(def)) + '</span>' + elem + '<span class="ic-gun">' + IB.HUD.icon(def.cls) + '</span></div>';
      tag = at >= 0 ? 'Carried · key ' + (at + 1) : 'In backpack';
      if (at >= 0) {
        for (var k = 0; k < max; k++) if (k !== at && (k < lo.length || (k === lo.length && at !== lo.length - 1))) acts += '<button class="btn gu-btn" data-gact="moveslot" data-w="' + w + '" data-to="' + k + '">To slot ' + (k + 1) + '</button>';
        if (lo.length > 1) acts += '<button class="btn gu-btn" data-gact="unequipgun" data-w="' + w + '">Unequip</button>';
      } else {
        var tgt = Math.min(S.slot, max - 1);
        acts += '<button class="btn gu-btn primary" data-gact="equipgun" data-gun="' + w + '">' + (lo[tgt] ? 'Swap into slot ' + (tgt + 1) : 'Carry in slot ' + (tgt + 1)) + '</button>';
      }
    } else if (spec.k === 'item') {
      var it = IB.Loot.find(g, spec.id); if (!it) return cardFor(G, g, null);
      var rc = rarity(it), pl = placeOf(g, it, lo), L = IB.Loot;
      color = rc.color;
      // compare against what the target / the same slot already holds
      var other = null;
      if (it.type === 'shield' && !pl && g.shield) other = L.find(g, g.shield);
      if (it.type !== 'shield' && !(pl && pl.w)) { var tw = S.target ? S.target.w : lo[S.slot]; var cur = tw && L.weaponItems(g, tw)[L.slotOf(it)]; if (cur && cur.id !== it.id) other = cur; }
      head = '<div class="ic-req">' + (pl ? svg(CHECK, 'g24 ic-check') : '') + rc.name + ' · ' + IB.LootHUD.typeName(it.type) + ' · found on level ' + it.level + '</div>' +
        '<b class="ic-name">' + esc(it.name) + '</b>' + (other ? '<div class="ic-vs">Compared with ' + esc(other.name) + '</div>' : '');
      body = statList(itemStats(it), other ? itemStats(other) : null) + '<div class="ic-notes"><p class="flav">' + esc(FLAVOR[it.type] || '') + '</p>' +
        (it.type !== 'shield' ? '<p>Fits ' + esc(IB.LOOT.types[it.type].classes.map(function (c) { return IB.HUD.clsName(c); }).join(', ')) + (IB.LOOT.types[it.type].noScoped ? ' without optics' : '') + '</p>' : '') + '</div>';
      foot = '<div class="ic-foot"><span class="ic-maker">' + esc(IB.LootHUD.typeName(it.type)) + '</span><span class="ic-gun ic-item">' + icon(it.type) + '</span></div>';
      tag = pl ? (pl.worn ? 'Equipped shield' : 'On ' + IB.WEAPONS[pl.w].name) : 'In backpack';
      if (it.type === 'shield') {
        acts += pl ? '<button class="btn gu-btn" data-gact="unequip" data-id="' + it.id + '">Unequip</button>'
          : '<button class="btn gu-btn primary" data-gact="equip" data-id="' + it.id + '">Equip</button>';
      } else {
        var fitsW = lo.filter(function (x) { return L.compatible(it, x, IB.WEAPONS[x]); });
        if (fitsW.length) {
          acts += '<div class="seg gu-fit" role="group" aria-label="Fit to">' + fitsW.map(function (x) {
            var on = pl && pl.w === x;
            return '<button data-gact="' + (on ? 'detach' : 'fit') + '" data-id="' + it.id + '" data-w="' + x + '" aria-pressed="' + !!on + '" title="' + (on ? 'Take off ' : 'Fit to ') + esc(IB.WEAPONS[x].name) + '">' +
              '<span class="gu-wicon">' + IB.HUD.icon(IB.WEAPONS[x].cls) + '</span>' + esc(shortName(IB.WEAPONS[x])) + '</button>';
          }).join('') + '</div>';
          if (pl && pl.w) acts += '<button class="btn gu-btn" data-gact="detach" data-id="' + it.id + '">Take off</button>';
        } else acts += '<span class="gu-nofit">Fits none of your carried guns</span>';
      }
      var sure = S.confirm === it.id;
      acts += '<button class="btn danger gu-btn gu-discard' + (sure ? ' sure' : '') + '" data-gact="discard" data-id="' + it.id + '">' + (sure ? (touch() ? 'Tap again to scrap' : 'Click again to scrap') : 'Scrap') + '</button>';
    }
    return '<div class="holo hsel inv-card" style="--rar:' + color + '">' + head + body + foot + '<div class="ic-tag">' + esc(tag) + '</div>' +
      (acts ? '<div class="gu-acts">' + acts + '</div>' : '') + '</div>';
  }
  function shortName(def) { var p = String(def.name).split(' '); return p.length > 1 ? p.slice(1).join(' ') : def.name; }

  // ---------- equipped column ----------
  function chipHtml(G, g, w, sl) {
    var it = IB.Loot.weaponItems(g, w)[sl], selE = S.sel && S.sel.k === 'empty' && S.sel.w === w && S.sel.slot === sl;
    if (!it) return '<button class="cell inv-chip empty' + (selE ? ' sel' : '') + '" data-gact="chip" data-w="' + w + '" data-sl="' + sl + '" data-k="c_' + w + '_' + sl + '" data-nav aria-label="' + IB.LOOT.slotNames[sl] + ' slot on ' + esc(IB.WEAPONS[w].name) + ': empty">' +
      svg(PLUS, 'g24 chip-plus') + '<span>' + IB.LOOT.slotNames[sl] + '</span></button>';
    var rc = rarity(it), sel = S.sel && S.sel.k === 'item' && S.sel.id === it.id;
    return '<button class="cell inv-chip filled' + (sel ? ' sel' : '') + '" style="--rar:' + rc.color + '" data-gact="item" data-item="' + it.id + '" data-w="' + w + '" data-k="i_' + it.id + '" data-nav aria-label="' + IB.LOOT.slotNames[sl] + ': ' + esc(it.name) + '">' +
      '<span class="chip-ic">' + icon(it.type) + '</span><span>' + esc(it.name) + '</span></button>';
  }
  function equippedCol(G, g) {
    var lo = loadout(G), max = maxSlots(G), rows = '';
    for (var i = 0; i < IB.LOADOUT_RULES.extra; i++) {
      var w = lo[i], def = w && IB.WEAPONS[w];
      if (i >= max) {
        rows += '<div class="inv-wrow"><span class="inv-num">' + (i + 1) + '</span><button class="cell lo-slot inv-wslot locked" data-gact="lock" data-k="s' + i + '" data-nav aria-label="Weapon slot ' + (i + 1) + ': locked until level ' + IB.LOADOUT_RULES.extraAfter + ' is cleared">' +
          svg(LOCK, 'g24 ws-lock') + '<span class="ws-txt"><b>Locked</b><small>Clear level ' + IB.LOADOUT_RULES.extraAfter + '</small></span></button></div>';
        continue;
      }
      var sel = S.slot === i, gr = def ? grade(def) : null;
      var chips = def ? IB.Loot.slotsFor(w, def).map(function (sl) { return chipHtml(G, g, w, sl); }).join('') : '';
      rows += '<div class="inv-wrow' + (sel ? ' cur' : '') + '"><span class="inv-num">' + (i + 1) + '</span>' +
        '<button class="cell lo-slot inv-wslot' + (def ? '' : ' empty') + (sel ? ' sel' : '') + '"' + (gr ? ' style="--rar:' + gr.color + '"' : '') + ' data-gact="slot" data-slot="' + i + '" data-k="s' + i + '" data-nav aria-pressed="' + sel + '" aria-label="Slot ' + (i + 1) + ': ' + (def ? esc(def.name) : 'empty') + '">' +
          (def ? '<span class="ws-gun">' + IB.HUD.icon(def.cls) + '</span><span class="ws-txt"><b>' + esc(def.name) + '</b><small>' + IB.HUD.clsName(def.cls) + ' · ' + gr.name + '</small></span>'
            : '<span class="ws-gun none">' + svg(PLUS) + '</span><span class="ws-txt"><b>Empty</b><small>' + (touch() ? 'Tap' : 'Pick') + ' a gun in the backpack</small></span>') +
        '</button>' + (chips ? '<div class="inv-chips n' + IB.Loot.slotsFor(w, def).length + '">' + chips + '</div>' : '') + '</div>';
    }
    var sh = g.shield ? IB.Loot.find(g, g.shield) : null, ps = G.player && G.player.shield;
    var shSel = S.sel && ((S.sel.k === 'item' && sh && S.sel.id === sh.id) || S.sel.k === 'emptyshield');
    var shield = sh ? '<button class="cell inv-shield filled' + (shSel ? ' sel' : '') + '" style="--rar:' + rarity(sh).color + '" data-gact="item" data-item="' + sh.id + '" data-k="i_' + sh.id + '" data-nav aria-label="Shield: ' + esc(sh.name) + '">' +
        '<span class="sh-ic">' + icon('shield') + '</span><span class="ws-txt"><b>' + esc(sh.name) + '</b><small>' + rarity(sh).name + ' shield cell</small></span>' +
        '<b class="sh-cap">' + (ps ? Math.ceil(ps.cur) + '<small>/' + ps.max + '</small>' : sh.stats.capacity) + '</b></button>'
      : '<button class="cell inv-shield empty' + (shSel ? ' sel' : '') + '" data-gact="shieldslot" data-k="shield" data-nav aria-label="Shield slot: empty"><span class="sh-ic">' + icon('shield') + '</span><span class="ws-txt"><b>No shield</b><small>' +
        ((G.slot && G.slot.highest || 0) >= IB.LOOT.types.shield.minCleared ? 'Equip a cell from the backpack' : 'Drops after level ' + IB.LOOT.types.shield.minCleared) + '</small></span></button>';
    return '<section class="holo inv-eq tm-scroll" data-pane="eq" aria-label="Equipped">' +
      '<h3 class="inv-h">' + IB.Menus.glyph('emblem') + 'Equipped<span>' + lo.length + '/' + max + ' guns</span></h3>' +
      '<div class="inv-wslots">' + rows + '</div>' +
      '<div class="inv-gear"><span class="inv-gl">' + svg(SI.cap) + '</span>' + shield + '</div>' +
      '<div class="inv-bar"><span class="inv-gems" aria-label="' + ((G.slot && G.slot.gems) || 0) + ' gems"><i class="gem-glyph" aria-hidden="true"></i><b aria-hidden="true">' + String((G.slot && G.slot.gems) || 0).split('').map(function (c) { return '<i>' + c + '</i>'; }).join('') + '</b></span><span class="inv-bag">Bag <b>' + g.inv.length + '/' + IB.LOOT.invCap + '</b></span></div>' +
      '</section>';
  }

  // ---------- backpack column ----------
  function backpackCol(G, g) {
    var lo = loadout(G), L = IB.Loot;
    var guns = arsenal(G).filter(function (w) { return lo.indexOf(w) < 0 && IB.WEAPONS[w]; });
    var loose = g.inv.filter(function (it) { var p = placeOf(g, it, lo); return !p || (p.w && !p.carried); });
    loose.sort(function (a, b) { return L.rarityRank(b.rarity) - L.rarityRank(a.rarity) || b.level - a.level || (a.id < b.id ? -1 : 1); });
    var tgt = S.sel && (S.sel.k === 'empty' || S.sel.k === 'emptyshield') ? S.sel : null;
    function fits(it) { if (!tgt) return false; if (tgt.k === 'emptyshield') return it.type === 'shield'; return L.slotOf(it) === tgt.slot && L.compatible(it, tgt.w, IB.WEAPONS[tgt.w]); }
    var gunT = guns.map(function (w) {
      var def = IB.WEAPONS[w], gr = grade(def), sel = S.sel && S.sel.k === 'gun' && S.sel.id === w, n = Object.keys(L.weaponItems(g, w)).length;
      return '<button class="cell lo-card inv-item gun' + (sel ? ' sel' : '') + (tgt ? ' faded' : '') + '" style="--rar:' + gr.color + '" data-gact="gun" data-gun="' + w + '" data-k="g_' + w + '" data-nav aria-label="' + esc(def.name) + ', ' + IB.HUD.clsName(def.cls) + '">' +
        '<span class="it-ic">' + IB.HUD.icon(def.cls) + '</span><span class="it-txt"><b>' + esc(def.name) + '</b><small>' + IB.HUD.clsName(def.cls) + ' · ' + gr.name + (n ? ' · ' + n + ' mod' + (n > 1 ? 's' : '') : '') + '</small></span></button>';
    }).join('');
    function itemTile(it) {
      var rc = rarity(it), sel = S.sel && S.sel.k === 'item' && S.sel.id === it.id, p = placeOf(g, it, lo), f = fits(it);
      return '<button class="cell inv-item gu-item ' + it.rarity + (sel ? ' sel' : '') + (f ? ' fits' : tgt ? ' faded' : '') + '" style="--rar:' + rc.color + '" data-gact="item" data-item="' + it.id + '" data-k="i_' + it.id + '" data-nav aria-label="' + esc(it.name) + ', ' + rc.name + ' ' + IB.LootHUD.typeName(it.type) + '">' +
        '<span class="it-ic">' + icon(it.type) + '</span><span class="it-txt"><b>' + esc(it.name) + '</b><small>' + rc.name + ' · ' + IB.LootHUD.typeName(it.type) + ' · Lv ' + it.level + (p && p.w ? ' · on ' + esc(shortName(IB.WEAPONS[p.w])) : '') + '</small></span>' +
        (f ? '<span class="it-fit" aria-hidden="true">' + svg(PLUS) + '</span>' : '') + '</button>';
    }
    var mods = loose.filter(function (it) { return it.type !== 'shield'; }), shields = loose.filter(function (it) { return it.type === 'shield'; });
    function cat(name, n, html, empty) { return '<h4 class="inv-cat"><span>' + name + '</span><i>' + n + '</i></h4>' + (html || '<p class="inv-none">' + empty + '</p>'); }
    return '<section class="holo inv-bp" aria-label="Backpack">' +
      '<h3 class="inv-h">' + svg(SI.mag) + 'Backpack<span>' + (guns.length + loose.length) + ' items</span></h3>' +
      '<div class="inv-bplist tm-scroll" data-pane="bp">' +
        cat('Weapons', guns.length, gunT, 'Every gun you own is carried. Weapon stands add more.') +
        cat('Attachments', mods.length, mods.map(itemTile).join(''), 'Grips, scopes and acid muzzles drop from robots.') +
        cat('Shields', shields.length, shields.map(itemTile).join(''), (G.slot && G.slot.highest || 0) >= IB.LOOT.types.shield.minCleared ? 'No spare shield cells.' : 'Shield cells drop after level ' + IB.LOOT.types.shield.minCleared + '.') +
      '</div></section>';
  }

  // ---------- ammo panel ----------
  function ammoPanel(G) {
    if (!G.ws) return '';
    var rows = IB.Weapons.ownedSlots(G.ws).map(function (k) {
      var id = G.ws.slots[k], gun = G.ws.guns[id]; if (!gun) return '';
      var size = IB.Weapons.magSize(G.ws, gun.def), res = gun.reserve === Infinity ? '∞' : gun.reserve;
      return '<li class="' + (G.ws.cur === id ? 'cur' : '') + '"><span class="am-ic">' + IB.HUD.icon(gun.def.cls) + '</span><span class="am-n">' + esc(shortName(gun.def)) + '</span>' +
        '<b>' + gun.mag + '<small>/' + size + '</small></b><b class="am-res">' + res + '</b></li>';
    }).join('');
    return '<section class="holo inv-ammo" aria-label="Ammo"><h3 class="inv-h">' + svg(SI.mag) + 'Ammo<span class="am-cols"><i>Mag</i><i>Spare</i></span></h3><ul class="am-list">' + rows + '</ul></section>';
  }

  // ---------- render ----------
  function specFor(el) {
    if (!el) return null;
    var d = el.dataset;
    if (d.gact === 'lock') return { k: 'lock' };
    if (d.gact === 'slot') { var lo = curG ? loadout(curG) : []; return lo[+d.slot] ? { k: 'gun', id: lo[+d.slot] } : { k: 'emptyslot', i: +d.slot }; }
    if (d.gact === 'gun') return { k: 'gun', id: d.gun };
    if (d.gact === 'item') return { k: 'item', id: d.item };
    if (d.gact === 'chip') return { k: 'empty', w: d.w, slot: d.sl };
    if (d.gact === 'shieldslot') return { k: 'emptyshield' };
    return null;
  }
  function selSpec(G) {
    if (S.sel) return S.sel.k === 'slot' ? (loadout(G)[S.sel.i] ? { k: 'gun', id: loadout(G)[S.sel.i] } : { k: 'emptyslot', i: S.sel.i }) : S.sel;
    var w = loadout(G)[S.slot];
    return w ? { k: 'gun', id: w } : { k: 'emptyslot', i: S.slot };
  }
  var curG = null, curRoot = null, shown = '', quiet = false;
  function setCard(spec) {
    if (!curRoot) return;
    var host = curRoot.querySelector('.inv-cardhost'); if (!host) return;
    var key = JSON.stringify(spec) + '|' + S.confirm;
    if (key === shown) return;
    shown = key;
    host.innerHTML = cardFor(curG, gearOf(curG), spec);
  }

  GU.reset = function (G) {
    var lo = loadout(G), max = maxSlots(G);
    S.slot = Math.min(lo.length, max - 1); S.sel = null; S.target = null; S.confirm = null;
  };
  GU.render = function (root, G) {
    if (!root || !G) return;
    var g = gearOf(G);
    if (!g) { root.innerHTML = '<p class="gu-note">Start a game to collect gear.</p>'; return; }
    // the selection may point at something that is gone (scrapped, moved)
    if (S.sel && S.sel.k === 'item' && !IB.Loot.find(g, S.sel.id)) S.sel = null;
    if (S.sel && S.sel.k === 'gun' && loadout(G).indexOf(S.sel.id) >= 0) S.sel = { k: 'slot', i: loadout(G).indexOf(S.sel.id) };
    S.slot = Math.max(0, Math.min(S.slot, maxSlots(G) - 1));
    var focusK = document.activeElement && root.contains(document.activeElement) && document.activeElement.dataset.k;
    var scroll = {}; root.querySelectorAll('.tm-scroll').forEach(function (s) { scroll[s.dataset.pane] = s.scrollTop; });
    curG = G; curRoot = root; shown = '';
    root.classList.add('invui');
    root.innerHTML = '<div class="inv-left tm-scroll" data-pane="left"><div class="inv-cardhost tm-scroll" data-pane="card" aria-live="polite"></div>' + ammoPanel(G) + '</div>' +
      equippedCol(G, g) + backpackCol(G, g);
    setCard(selSpec(G));
    root.querySelectorAll('.tm-scroll').forEach(function (s) { if (scroll[s.dataset.pane]) s.scrollTop = scroll[s.dataset.pane]; });
    if (focusK && !touch()) { var f = root.querySelector('[data-k="' + focusK + '"]'); if (f) { quiet = true; f.focus({ preventScroll: true }); quiet = false; } }
    if (!root._gearBound) {
      root._gearBound = true;
      root.addEventListener('pointerdown', function (e) { ptr = e.pointerType || 'mouse'; }, true);
      root.addEventListener('click', function (e) {
        var b = e.target.closest('[data-gact]'); if (!b || !root.contains(b)) return;
        e.stopPropagation();
        var how = ptr; ptr = null;
        GU.act(root, root._G || IB.Game, b.dataset.gact, b.dataset.id || b.dataset.item, b.dataset.w, b, how);
      });
      // hover / focus previews the card; leaving the screen shows the selection again
      var preview = function (e) { if (root !== curRoot || quiet) return; var t = e.target.closest && e.target.closest('[data-gact]'); var sp = t && specFor(t); if (sp) setCard(sp); };
      root.addEventListener('pointerover', function (e) { if (e.pointerType === 'mouse') preview(e); });
      root.addEventListener('focusin', function (e) { if (!touch()) preview(e); });
      root.addEventListener('pointerleave', function () { if (root === curRoot && curG) setCard(selSpec(curG)); });
    }
    root._G = G;
  };

  /* act: slot | gun | equipgun | moveslot | unequipgun | item | chip | shieldslot | lock | equip | unequip | fit | detach | discard
     how: the pointer type of the click ('touch' selects first; anything else acts at once) */
  GU.act = function (root, G, act, id, w, el, how) {
    var L = IB.Loot, g = IB.Gear.gear(G); if (!g) return false;
    var ok = false, fill = false, gearChanged = false, d = (el && el.dataset) || {};
    var lo = loadout(G), max = maxSlots(G), soft = how === 'touch';
    if (act !== 'discard') S.confirm = null;
    function select(sel) { S.sel = sel; sfx('ui'); }
    switch (act) {
      case 'lock': select(null); setCard({ k: 'lock' }); sfx('dry'); return false;
      case 'slot': S.slot = +d.slot; S.target = null; select({ k: 'slot', i: +d.slot }); break;
      case 'gun':
        if (soft && !(S.sel && S.sel.k === 'gun' && S.sel.id === d.gun)) { select({ k: 'gun', id: d.gun }); break; }
        ok = pickGun(G, d.gun); break;
      case 'equipgun': ok = pickGun(G, d.gun); break;
      case 'moveslot': {
        var next = IB.Loadout.assign(lo, max, +d.to, w);
        if (next.indexOf(w) < 0) next = lo;   // never drop a gun by moving it
        G.slot.loadout = next; S.slot = next.indexOf(w); S.sel = { k: 'slot', i: S.slot }; ok = true; sfx('draw'); break;
      }
      case 'unequipgun':
        if (lo.length > 1) { G.slot.loadout = lo.filter(function (x) { return x !== w; }); S.sel = { k: 'gun', id: w }; S.slot = Math.min(S.slot, G.slot.loadout.length); ok = true; sfx('uiBack'); }
        break;
      case 'chip': S.target = { w: d.w, slot: d.sl }; select({ k: 'empty', w: d.w, slot: d.sl }); break;
      case 'shieldslot': S.target = null; select({ k: 'emptyshield' }); break;
      case 'item': {
        var it = L.find(g, id); if (!it) break;
        var pl = placeOf(g, it, lo);
        var again = S.sel && S.sel.k === 'item' && S.sel.id === id;
        // fitted / worn items and touch first taps just select; a loose item acts at once (mouse, keys) or on the second tap
        if (pl && (pl.worn || pl.carried)) { select({ k: 'item', id: id }); break; }
        if (soft && !again) { select({ k: 'item', id: id }); break; }
        if (it.type === 'shield') { ok = L.equipShield(g, id); gearChanged = ok; fill = false; if (ok) { S.sel = { k: 'item', id: id }; act = 'equip'; } break; }
        var tw = defaultTarget(G, g, it, lo);
        if (tw) { ok = L.attach(g, tw, IB.WEAPONS[tw], id); gearChanged = ok; act = 'fit'; S.target = null; }
        S.sel = { k: 'item', id: id };
        if (!tw) sfx('dry');
        break;
      }
      case 'equip': ok = L.equipShield(g, id); gearChanged = ok; break;
      case 'unequip': ok = L.equipShield(g, null); gearChanged = ok; break;
      case 'fit': ok = L.attach(g, w, IB.WEAPONS[w], id); gearChanged = ok; S.sel = { k: 'item', id: id }; S.target = null; break;
      case 'detach': { var at = L.attachedTo(g, id); ok = !!at && L.detach(g, at.weapon, at.slot); gearChanged = ok; S.sel = { k: 'item', id: id }; break; }
      case 'discard':
        if (S.confirm !== id) { S.confirm = id; sfx('ui'); GU.render(root, G); return false; }
        S.confirm = null; ok = L.discard(g, id); gearChanged = ok; S.sel = null; break;
    }
    if (ok && gearChanged) {
      // a newly equipped shield starts empty and charges up (no free refill from swapping cells mid-fight)
      IB.Gear.refresh(G, fill);
      if (act === 'equip' && G.player.shield) { G.player.shield.cur = 0; G.player.shield.since = G.player.shield.delay; }
      sfx(act === 'discard' ? 'uiBack' : act === 'fit' || act === 'equip' ? 'magIn' : 'ui');
    }
    if (ok) IB.Gear.save(G);
    // standalone panel (no field kit to apply it on close): a loadout change takes effect at once
    if (ok && !gearChanged && G.applyProgress && !(IB.TabMenu && IB.TabMenu.isOpen())) G.applyProgress();
    GU.render(root, G);
    return ok;
  };
  // where a loose attachment goes on a plain click: the picked empty slot, else the selected gun, else the first carried gun with room
  function defaultTarget(G, g, it, lo) {
    var L = IB.Loot, sl = L.slotOf(it), ok = function (x) { return x && L.compatible(it, x, IB.WEAPONS[x]); };
    if (S.target && S.target.slot === sl && ok(S.target.w)) return S.target.w;
    if (ok(lo[S.slot])) return lo[S.slot];
    var free = lo.filter(function (x) { return ok(x) && !L.weaponItems(g, x)[sl]; });
    return free[0] || lo.filter(ok)[0] || null;
  }
  function pickGun(G, id) {
    var max = maxSlots(G), lo = loadout(G);
    var next = IB.Loadout.assign(lo, max, S.slot, id);
    G.slot.loadout = next;
    sfx('draw');
    // move the cursor to the next empty slot, if any
    if (next.length < max && next.indexOf(id) >= 0) S.slot = next.length;
    else S.slot = Math.min(S.slot, Math.max(0, next.length - (next.length < max ? 0 : 1)));
    S.sel = { k: 'slot', i: next.indexOf(id) };
    if (IB.Gear) IB.Gear.refresh(G);
    return true;
  }

  GU.open = function (G) {
    if (G.mode === 'play') G.pause();
    var ov = document.getElementById('overlay');
    ov.hidden = false; ov.className = 'overlay dim ov-gear';
    GU.reset(G);
    ov.innerHTML = '<div class="screen gear-screen"><div class="gear-top">' + IB.Menus.crumb(['Paused', 'Inventory']) +
      '<button class="btn primary" data-act="resume" data-esc="1"><span class="btn-l">Back to the fight</span></button></div>' +
      '<div id="gearRoot" class="gear-standalone"></div></div>';
    if (IB.Menus) IB.Menus.cur = 'gear';
    ov.scrollTop = 0;
    GU.render(document.getElementById('gearRoot'), G);
  };
})(window.IB = window.IB || {});
