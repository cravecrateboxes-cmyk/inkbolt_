/* INKBOLT inventory: guns carried, shield, gun attachments and the backpack, in one screen.
     IB.GearUI.render(containerEl, G)   fills containerEl (the Inventory tab of the field kit): the item card (rarity
                                        title bar, stat rows, compare marks, the item's picture) + ammo on the left, EQUIPPED in the middle (weapon slots 1-3, slot 3 locked until level 10
                                        is cleared, the attachment slots under each carried gun, the worn slots: shield and
                                        armour vest, gems), BACKPACK on the right (weapons, attachments, shields, armour). Changes apply at once
                                        (IB.Gear.refresh) and are saved.
     IB.GearUI.open(G)                  the same screen in the overlay, paused (tests, or a menu without tabs).
     IB.GearUI.reset(G)                 cursor back to the first free weapon slot (the field kit calls it on open).
   Selecting: mouse and keyboard act at once (hover / focus previews the card, click / Enter equips);
   touch taps select first (the card shows the item with its actions), a second tap on the same tile equips.
   Pictures are the real models rendered by IB.Thumbs (ui/thumbs.js); styles in ui/fieldkit.css.
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
    acid: ACIDI, noise: '<path d="M3 9h4l5-5v16l-5-5H3z" fill="currentColor"/><path d="M16 9l5 6M21 9l-5 6" stroke="currentColor" stroke-width="2.4"/>',
    armor: '<path d="M4 3h5l2 3h2l2-3h5l1 7-2 2v10H5V12l-2-2z" fill="currentColor"/><path d="M8 13l4 3 4-3" fill="none" stroke="var(--ink)" stroke-width="2"/>',
    hp: '<path d="M12 21C5 15.5 2 12.3 2 8.4A5 5 0 0 1 12 6a5 5 0 0 1 10 2.4c0 3.9-3 7.1-10 12.6z" fill="currentColor"/><path d="M12 9v7M8.5 12.5h7" stroke="var(--ink)" stroke-width="2.4"/>'
  };

  // ---------- gun presentation: grade colour (by when it unlocks) ----------
  var GRADES = [[3, 'Standard', '#E4DFD3'], [7, 'Tuned', '#6BE05A'], [11, 'Rare', '#4A9BFF'], [15, 'Epic', '#B77BFF'], [99, 'Prime', '#FF9A2E']];
  // a gun's colour is its quality tier (gray / green / blue / purple / orange: IB.WeaponDrops, raised by tiered drops)
  function grade(def) {
    if (IB.WeaponDrops) { var t = IB.WeaponDrops.tierOf(def.id); return { name: t.name, color: t.color }; }
    var u = def.unlock || 1; for (var i = 0; i < GRADES.length; i++) if (u <= GRADES[i][0]) return { name: GRADES[i][1], color: GRADES[i][2] }; return { name: 'Prime', color: '#FF9A2E' }; }
  function clsName(c) { return IB.HUD && IB.HUD.clsName ? IB.HUD.clsName(c) : c; }
  function clsIcon(c) { return IB.HUD && IB.HUD.icon ? IB.HUD.icon(c) : ''; }
  // pictures: the real model rendered by IB.Thumbs, else the class / type glyph
  function gunPic(w, cls) { var d = IB.WEAPONS[w], fb = '<span class="pic-fb">' + clsIcon(d && d.cls) + '</span>'; return IB.Thumbs ? IB.Thumbs.pic('gun', w, cls || 'gpic', fb) : '<span class="' + (cls || 'gpic') + '">' + fb + '</span>'; }
  // rarity: types with a model per rarity (shield cells) draw that rarity's own model
  function perRarity(type) { var td = IB.LOOT.types[type], m = td && td.models; if (!m) return false; var k = Object.keys(m); return k.some(function (r) { return m[r] !== m[k[0]]; }); }
  function gearPic(type, cls, rar) {
    var fb = '<span class="pic-fb">' + icon(type) + '</span>', id = rar && perRarity(type) ? type + '.' + rar : type;
    return IB.Thumbs ? IB.Thumbs.pic('gear', id, cls || 'gpic', fb) : '<span class="' + (cls || 'gpic') + '">' + fb + '</span>';
  }
  function itemPic(it, cls) { return gearPic(it.type, cls, it.rarity); }
  function slotName(sl) { return IB.LOOT.slotNames[sl] || sl; }
  var WORN_EMPTY = { shield: 'No shield', armor: 'No vest' };
  var FR = '<i class="fr" aria-hidden="true"><i></i></i>';
  function rarity(it) { return IB.LOOT.rarityById[it.rarity]; }

  // ---------- data access ----------
  function gearOf(G) { return IB.Gear && IB.Gear.gear(G); }
  function loadout(G) { return (G.slot && G.slot.loadout && G.slot.loadout.length) ? G.slot.loadout.slice() : (G.ws ? IB.Weapons.ownedSlots(G.ws).map(function (k) { return G.ws.slots[k]; }) : []); }
  function arsenal(G) { return (G.slot && G.slot.arsenal) || loadout(G); }
  function maxSlots(G) { return G.progress ? G.progress().loadoutMax : IB.Skills.loadoutMax((G.slot && G.slot.highest) || 0); }
  function skillFx(G) { return IB.Skills.effects((G.slot && G.slot.skills) || {}); }
  function modsDef(g, w) { return IB.Loot.applyMods(IB.WEAPONS[w], g ? IB.Loot.weaponItems(g, w) : {}); }
  // where an item is: {worn, slot} | {w, slot, carried} | null (loose in the backpack)
  function placeOf(g, it, lo) {
    var ws = IB.Loot.wornSlot(g, it.id);
    if (ws) return { worn: true, slot: ws };
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
  // per item type: the statLines rows in order as [stat key, glyph, which way is better] (for the compare marks)
  var ITEM_KEYS = { shield: [['capacity', 'cap', 'high'], ['rate', 'rate', 'high'], ['delay', 'delay', 'low']], grip: [['recoil', 'recoil', 'high'], ['spread', 'acc', 'high']],
    scope: [['zoom', 'zoom', 'high'], ['aimSpread', 'acc', 'high']], acid: [['acid', 'acid', 'high'], [null, 'noise']],
    shock: [['chance', 'rate', 'high'], ['arc', 'acid', 'high']], blast: [['chance', 'rate', 'high'], ['power', 'recoil', 'high']],
    void: [['chance', 'rate', 'high'], ['radius', 'zoom', 'high']],
    mag: [['mag', 'mag', 'high'], ['reload', 'reload', 'high']], armor: [['dr', 'armor', 'high'], ['hp', 'hp', 'high']] };
  // the perk of a shield cell as a highlighted card row
  function perkRow(it) {
    var pl = IB.Loot.perkLine(it); if (!pl) return '';
    return '<div class="ic-perk ' + pl.id + '">' + (IB.LootHUD ? IB.LootHUD.perkIcon(pl.id) : '') + '<b>' + esc(pl.name) + '</b><span>' + esc(pl.text) + '</span></div>';
  }
  // what an attachment fits, from its type's data
  function fitsNote(td) {
    var t = 'Fits ' + td.classes.map(clsName).join(', ');
    if (td.noScoped) t += ' without optics';
    if (td.noActions) t += ' (not ' + td.noActions.map(function (a) { return a + 's'; }).join(', ') + ')';
    return t;
  }
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
      return '<li>' + svg(SI[l.icon] || SI.dmg, 'g24 ic-si') + '<span>' + esc(l.label) + '</span><b>' + esc(l.txt) + '</b>' + cmpMark(l, by[l.key || l.label]) + '</li>';
    }).join('') + '</ul>';
  }

  // ---------- card (left column) ----------
  // BL2-style item card: yellow frame, rarity title bar, plain stat rows with small glyphs, notes, the picture big
  function cardShell(color, req, title, body, pic, tag, acts, cls) {
    return '<div class="ep hsel inv-card' + (cls ? ' ' + cls : '') + '" style="--rar:' + color + '">' + FR +
      (req ? '<div class="ic-req">' + req + '</div>' : '') +
      '<div class="ic-bar"><b class="ic-name">' + title + '</b></div>' + body +
      (pic || tag ? '<div class="ic-foot">' + (tag ? '<span class="ic-tag">' + esc(tag) + '</span>' : '') + (pic || '') + '</div>' : '') +
      (acts ? '<div class="gu-acts">' + acts + '</div>' : '') + '</div>';
  }
  function note(t) { return '<p class="ic-note">' + esc(t) + '</p>'; }
  function cardFor(G, g, spec) {
    var lo = loadout(G), max = maxSlots(G);
    if (!spec) return cardShell('#5FD0FF', '', 'Inventory', note('Point at a gun or a piece of gear to see its card.'), '', '', '', 'empty');
    if (spec.k === 'lock') return cardShell('#8C98AE', 'Weapon slot 3', svg(LOCK, 'g24 ic-lock') + 'Locked', note('Beat level ' + IB.LOADOUT_RULES.extraAfter + ' to carry a third gun.'), '', '', '', 'locked');
    if (spec.k === 'emptyslot') {
      return cardShell('#5FD0FF', 'Weapon slot ' + (spec.i + 1), 'Empty slot',
        note(touch() ? 'Tap a gun in the backpack to carry it here.' : 'Pick a gun from the backpack. Keys 1–' + max + ' switch guns.'), '', '', '', 'empty');
    }
    if (spec.k === 'empty' || spec.k === 'emptyworn') {
      var worn = spec.k === 'emptyworn', type = IB.Loot.typeForSlot(spec.slot);
      var fits = g.inv.filter(function (it) { return worn ? IB.Loot.slotOf(it) === spec.slot && g[spec.slot] !== it.id : IB.Loot.slotOf(it) === spec.slot && IB.Loot.compatible(it, spec.w, IB.WEAPONS[spec.w]); });
      var minC = (IB.LOOT.types[type] && IB.LOOT.types[type].minCleared) || 0, cleared = (G.slot && G.slot.highest) || 0;
      var t = worn && cleared < minC ? IB.LOOT.types[type].name + 's drop after level ' + minC + '.' :
        fits.length ? fits.length + ' in your backpack fit' + (fits.length === 1 ? 's' : '') + '. They glow yellow.' : 'Nothing in the backpack fits. Robots drop gear now and then.';
      return cardShell('#5FD0FF', spec.w ? esc(IB.WEAPONS[spec.w].name) : 'Equipped', 'Empty ' + esc(slotName(spec.slot)), note(t), gearPic(type, 'ic-pic ghost'), '', '', 'empty');
    }
    var acts = '', req = '', body = '', pic = '', tag = '', color = '#E4DFD3', title = '';
    if (spec.k === 'gun') {
      var w = spec.id, def = IB.WEAPONS[w]; if (!def) return cardFor(G, g, null);
      var at = lo.indexOf(w), st = gunStats(G, w, g), gr = grade(def), items = IB.Loot.weaponItems(g, w);
      color = gr.color; title = esc(def.name);
      var cmpW = at < 0 ? lo[Math.min(S.slot, lo.length - 1)] : null, vs = cmpW && cmpW !== w ? gunStats(G, cmpW, g).lines : null;
      req = (at >= 0 ? svg(CHECK, 'g24 ic-check') : '') + '<span>' + gr.name + ' ' + esc(clsName(def.cls)) + '</span><span>Lv ' + (def.unlock || 1) + '</span>';
      var notes = [];
      if (st.def.acid) notes.push('Acid +' + Math.round(st.def.acid * 100) + '% of each hit over ' + st.def.acidDur.toFixed(1) + ' s');
      if (st.fx.shock) notes.push('Shock rounds');
      if (st.def.optic) notes.push('Scope ' + (1 / st.def.aimZoom).toFixed(1) + 'x zoom');
      if (st.def.mods && st.def.mods.mag) notes.push('Extended mag: +' + (st.def.mag - def.mag) + ' rounds, ' + Math.round(st.def.mods.mag.stats.reload * 100) + '% faster reload');
      if (def.scopeZoom) notes.push('Built-in ' + def.scopeZoom + 'x scope');
      if (def.splash) notes.push('Splash damage, ' + def.radius + ' m');
      if (def.reserve === Infinity) notes.push('Unlimited spare ammo');
      var mods = Object.keys(items).map(function (sl) { return '<li style="--rar:' + rarity(items[sl]).color + '">' + itemPic(items[sl], 'ic-modpic') + '<b>' + esc(items[sl].name) + '</b></li>'; }).join('');
      body = (vs ? '<div class="ic-vs">vs ' + esc(IB.WEAPONS[cmpW].name) + '</div>' : '') + statList(st.lines, vs) +
        (notes.length ? '<ul class="ic-notes">' + notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>' : '') +
        (mods ? '<ul class="ic-mods">' + mods + '</ul>' : '');
      var elem = st.def.acid ? svg(ACIDI, 'g24 ic-elem acid') : st.fx.shock ? svg(SHOCKI, 'g24 ic-elem shock') : '';
      pic = elem + gunPic(w, 'ic-pic');
      tag = at >= 0 ? 'Key ' + (at + 1) : 'Backpack';
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
      color = rc.color; title = esc(it.name);
      var other = null, isWorn = L.isWorn(it), wsl = L.slotOf(it);
      if (isWorn && !pl && g[wsl]) other = L.find(g, g[wsl]);
      if (!isWorn && !(pl && pl.w)) { var tw = S.target ? S.target.w : lo[S.slot]; var cur = tw && L.weaponItems(g, tw)[wsl]; if (cur && cur.id !== it.id) other = cur; }
      req = (pl ? svg(CHECK, 'g24 ic-check') : '') + '<span>' + rc.name + ' ' + esc(IB.LootHUD.typeName(it.type)) + '</span><span>Lv ' + it.level + '</span>';
      var inotes = [];
      if (!isWorn) inotes.push(fitsNote(IB.LOOT.types[it.type]));
      if (it.type === 'armor') inotes.push('Cuts the damage that gets past your shield');
      if (other && other.perk && !it.perk) inotes.push('No perk (yours: ' + L.perkLine(other).name + ')');
      body = (other ? '<div class="ic-vs">vs ' + esc(other.name) + '</div>' : '') + statList(itemStats(it), other ? itemStats(other) : null) + perkRow(it) +
        (inotes.length ? '<ul class="ic-notes">' + inotes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>' : '');
      pic = itemPic(it, 'ic-pic gear');
      tag = pl ? (pl.worn ? 'Equipped' : 'On ' + shortName(IB.WEAPONS[pl.w])) : 'Backpack';
      if (isWorn) {
        acts += pl ? '<button class="btn gu-btn" data-gact="unequip" data-id="' + it.id + '">Unequip</button>'
          : '<button class="btn gu-btn primary" data-gact="equip" data-id="' + it.id + '">' + (other ? 'Swap in' : 'Equip') + '</button>';
      } else {
        var fitsW = lo.filter(function (x) { return L.compatible(it, x, IB.WEAPONS[x]); });
        if (fitsW.length) {
          acts += '<div class="seg gu-fit" role="group" aria-label="Fit to">' + fitsW.map(function (x) {
            var on = pl && pl.w === x;
            return '<button data-gact="' + (on ? 'detach' : 'fit') + '" data-id="' + it.id + '" data-w="' + x + '" aria-pressed="' + !!on + '" title="' + (on ? 'Take off ' : 'Fit to ') + esc(IB.WEAPONS[x].name) + '">' +
              gunPic(x, 'gu-wpic') + '<span>' + esc(shortName(IB.WEAPONS[x])) + '</span></button>';
          }).join('') + '</div>';
          if (pl && pl.w) acts += '<button class="btn gu-btn" data-gact="detach" data-id="' + it.id + '">Take off</button>';
        } else acts += '<span class="gu-nofit">Fits none of your carried guns</span>';
      }
      var sure = S.confirm === it.id;
      acts += '<button class="btn danger gu-btn gu-discard' + (sure ? ' sure' : '') + '" data-gact="discard" data-id="' + it.id + '">' + (sure ? (touch() ? 'Tap again to scrap' : 'Click again to scrap') : 'Scrap') + '</button>';
    }
    return cardShell(color, req, title, body, pic, tag, acts, '');
  }
  function shortName(def) { var p = String(def.name).split(' '); return p.length > 1 ? p.slice(1).join(' ') : def.name; }

  // ---------- equipped column ----------
  // big framed slots with the gun picture; each carried gun's attachment slots as small framed boxes under it
  function chipHtml(G, g, w, sl) {
    var it = IB.Loot.weaponItems(g, w)[sl], selE = S.sel && S.sel.k === 'empty' && S.sel.w === w && S.sel.slot === sl;
    var type = IB.Loot.typeForSlot(sl);
    if (!it) return '<button class="tile inv-chip empty' + (selE ? ' sel' : '') + '" data-gact="chip" data-w="' + w + '" data-sl="' + sl + '" data-k="c_' + w + '_' + sl + '" data-nav aria-label="' + slotName(sl) + ' slot on ' + esc(IB.WEAPONS[w].name) + ': empty">' + FR +
      gearPic(type, 'chip-pic ghost') + '<span class="chip-plus" aria-hidden="true">+</span><span class="chip-l">' + slotName(sl) + '</span></button>';
    var rc = rarity(it), sel = S.sel && S.sel.k === 'item' && S.sel.id === it.id;
    return '<button class="tile inv-chip filled ' + it.rarity + (sel ? ' sel' : '') + '" style="--rar:' + rc.color + '" data-gact="item" data-item="' + it.id + '" data-w="' + w + '" data-k="i_' + it.id + '" data-nav aria-label="' + slotName(sl) + ': ' + esc(it.name) + '">' + FR +
      itemPic(it, 'chip-pic') + '<span class="chip-l">' + esc(it.name) + '</span></button>';
  }
  /* a worn slot (shield, armour) in the EQUIPPED column: picture, name, the key number on the right */
  function wornTile(G, g, sl) {
    var it = IB.Loot.worn(g, sl), type = IB.Loot.typeForSlot(sl), td = IB.LOOT.types[type];
    var sel = S.sel && ((S.sel.k === 'item' && it && S.sel.id === it.id) || (S.sel.k === 'emptyworn' && S.sel.slot === sl));
    if (!it) {
      var open = !td.minCleared || ((G.slot && G.slot.highest) || 0) >= td.minCleared;
      return '<button class="tile inv-shield inv-worn empty' + (sel ? ' sel' : '') + '" data-gact="wornslot" data-sl="' + sl + '" data-k="w_' + sl + '" data-nav aria-label="' + slotName(sl) + ' slot: empty">' + FR +
        gearPic(type, 'sh-pic ghost') + '<span class="ws-name">' + (open ? WORN_EMPTY[sl] || 'Empty' : td.name + 's after level ' + td.minCleared) + '</span></button>';
    }
    var big;
    if (sl === 'shield') { var ps = G.player && G.player.shield; big = ps && ps.id === it.id ? Math.ceil(ps.cur) + '<small>/' + ps.max + '</small>' : String(it.stats.capacity); }
    else { var a = IB.Loot.armorOf(it); big = '-' + Math.round(a.dr * 100) + '%<small>+' + a.hp + ' hp</small>'; }
    var pl = IB.Loot.perkLine(it);
    return '<button class="tile inv-shield inv-worn filled ' + it.rarity + (sel ? ' sel' : '') + '" style="--rar:' + rarity(it).color + '" data-gact="item" data-item="' + it.id + '" data-k="i_' + it.id + '" data-nav aria-label="' + slotName(sl) + ': ' + esc(it.name) + '">' + FR +
      itemPic(it, 'sh-pic') + '<span class="ws-name">' + esc(it.name) + (pl ? '<i class="ws-perk ' + pl.id + '">' + (IB.LootHUD ? IB.LootHUD.perkIcon(pl.id) : '') + esc(pl.name) + '</i>' : '') + '</span>' +
      '<b class="sh-cap' + (sl === 'shield' ? '' : ' vest') + '">' + big + '</b></button>';
  }
  // melee weapon on V (and the frag cans on G): one tile; the backpack's Melee shelf picks which weapon is on V
  function meleeTile(G, id, on) {
    var def = IB.WEAPONS[id];
    return '<button class="tile inv-item gun melee' + (on ? ' sel' : '') + '" style="--rar:' + (on ? '#FFC23A' : grade(def).color) + '" data-gact="melee" data-melee="' + id + '" data-nav aria-pressed="' + !!on + '" aria-label="' + esc(def.name) + ', melee' + (on ? ', on V' : '') + '">' + FR +
      gunPic(id, 'it-pic') + '<span class="it-name">' + esc(def.name) + '</span>' + (on ? '<span class="it-mods" aria-hidden="true">V</span>' : '') + '</button>';
  }
  function meleeRow(G) {
    var id = G.meleeId && G.meleeId();
    if (!id) return '';
    var cans = G.slot && G.slot.frag ? ' · Frag cans ×' + (G.grenades || 0) + ' (G)' : '';
    return '<h4 class="inv-cat"><span>Melee (V)' + esc(cans) + '</span></h4><div class="inv-grid guns">' + meleeTile(G, id, true) + '</div>';
  }
  function equippedCol(G, g) {
    var lo = loadout(G), max = maxSlots(G), rows = '';
    for (var i = 0; i < IB.LOADOUT_RULES.extra; i++) {
      var w = lo[i], def = w && IB.WEAPONS[w];
      if (i >= max) {
        rows += '<div class="inv-wrow"><span class="inv-num">' + (i + 1) + '</span><button class="tile lo-slot inv-wslot locked" data-gact="lock" data-k="s' + i + '" data-nav aria-label="Weapon slot ' + (i + 1) + ': locked until level ' + IB.LOADOUT_RULES.extraAfter + ' is cleared">' + FR +
          svg(LOCK, 'g24 ws-lock') + '<span class="ws-name">Level ' + IB.LOADOUT_RULES.extraAfter + '</span></button></div>';
        continue;
      }
      var sel = S.slot === i, gr = def ? grade(def) : null;
      var slots = def ? IB.Loot.slotsFor(w, def) : [];
      var chips = slots.map(function (sl) { return chipHtml(G, g, w, sl); }).join('');
      rows += '<div class="inv-wrow' + (sel ? ' cur' : '') + '"><span class="inv-num">' + (i + 1) + '</span>' +
        '<button class="tile lo-slot inv-wslot' + (def ? '' : ' empty') + (sel ? ' sel' : '') + '"' + (gr ? ' style="--rar:' + gr.color + '"' : '') + ' data-gact="slot" data-slot="' + i + '" data-k="s' + i + '" data-nav aria-pressed="' + sel + '" aria-label="Slot ' + (i + 1) + ': ' + (def ? esc(def.name) : 'empty') + '">' + FR +
          (def ? gunPic(w, 'ws-pic') + '<span class="ws-name">' + esc(def.name) + '</span>' : '<span class="ws-plus" aria-hidden="true">+</span><span class="ws-name">' + (touch() ? 'Tap' : 'Pick') + ' a gun</span>') +
        '</button>' + (chips ? '<div class="inv-chips n' + slots.length + '">' + chips + '</div>' : '') + '</div>';
    }
    var worn = IB.LOOT.worn.map(function (sl) { return '<div class="inv-gear"><span class="inv-gl">' + svg(sl === 'shield' ? SI.cap : SI[sl] || SI.cap) + '</span>' + wornTile(G, g, sl) + '</div>'; }).join('');
    var gems = String((G.slot && G.slot.gems) || 0);
    return '<section class="ep inv-eq" aria-label="Equipped">' + FR +
      '<h3 class="ep-h">' + IB.Menus.glyph('emblem') + 'Equipped<span>' + lo.length + '/' + max + '</span></h3>' +
      '<div class="inv-eqbody tm-scroll" data-pane="eq"><div class="inv-wslots">' + rows + '</div>' + worn + meleeRow(G) + '</div>' +
      '<div class="inv-bar"><span class="inv-gems" aria-label="' + gems + ' gems"><i class="gem-glyph" aria-hidden="true"></i><b aria-hidden="true">' + gems.split('').map(function (c) { return '<i>' + c + '</i>'; }).join('') + '</b></span>' +
        '<span class="inv-bag">Bag <b>' + g.inv.length + '/' + IB.LOOT.invCap + '</b></span></div>' +
      '</section>';
  }

  // ---------- backpack column ----------
  function backpackCol(G, g) {
    var lo = loadout(G), L = IB.Loot;
    var guns = arsenal(G).filter(function (w) { return lo.indexOf(w) < 0 && IB.WEAPONS[w]; });
    var loose = g.inv.filter(function (it) { var p = placeOf(g, it, lo); return !p || (p.w && !p.carried); });
    loose.sort(function (a, b) { return L.rarityRank(b.rarity) - L.rarityRank(a.rarity) || b.level - a.level || (a.id < b.id ? -1 : 1); });
    var tgt = S.sel && (S.sel.k === 'empty' || S.sel.k === 'emptyworn') ? S.sel : null;
    function fits(it) { if (!tgt) return false; if (tgt.k === 'emptyworn') return L.slotOf(it) === tgt.slot; return L.slotOf(it) === tgt.slot && L.compatible(it, tgt.w, IB.WEAPONS[tgt.w]); }
    var gunT = guns.map(function (w) {
      var def = IB.WEAPONS[w], gr = grade(def), sel = S.sel && S.sel.k === 'gun' && S.sel.id === w, n = Object.keys(L.weaponItems(g, w)).length;
      return '<button class="tile lo-card inv-item gun' + (sel ? ' sel' : '') + (tgt ? ' faded' : '') + '" style="--rar:' + gr.color + '" data-gact="gun" data-gun="' + w + '" data-k="g_' + w + '" data-nav aria-label="' + esc(def.name) + ', ' + clsName(def.cls) + '">' + FR +
        gunPic(w, 'it-pic') + '<span class="it-name">' + esc(def.name) + '</span>' + (n ? '<span class="it-mods" aria-hidden="true">+' + n + '</span>' : '') + '</button>';
    }).join('');
    function itemTile(it) {
      var rc = rarity(it), sel = S.sel && S.sel.k === 'item' && S.sel.id === it.id, f = fits(it);
      return '<button class="tile inv-item gu-item ' + it.rarity + (sel ? ' sel' : '') + (f ? ' fits' : tgt ? ' faded' : '') + '" style="--rar:' + rc.color + '" data-gact="item" data-item="' + it.id + '" data-k="i_' + it.id + '" data-nav aria-label="' + esc(it.name) + ', ' + rc.name + ' ' + IB.LootHUD.typeName(it.type) + '">' + FR +
        itemPic(it, 'it-pic') + '<span class="it-name">' + esc(it.name) + '</span>' + (it.perk ? '<span class="it-perk ' + it.perk.id + '" aria-hidden="true">' + (IB.LootHUD ? IB.LootHUD.perkIcon(it.perk.id) : '') + '</span>' : '') +
        (f ? '<span class="it-fit" aria-hidden="true">+</span>' : '') + '</button>';
    }
    function cat(name, n, html, empty, cls) { return '<h4 class="inv-cat"><span>' + name + '</span></h4>' + (html ? '<div class="inv-grid ' + cls + '">' + html + '</div>' : '<p class="inv-none">' + empty + '</p>'); }
    var mods = loose.filter(function (it) { return L.isAttachment(it); }), cleared = (G.slot && G.slot.highest) || 0;
    var attNames = Object.keys(IB.LOOT.types).filter(function (k) { return IB.LOOT.slots.indexOf(IB.LOOT.types[k].slot) >= 0; }).map(function (k) { return IB.LOOT.types[k].name.toLowerCase() + 's'; });
    // one backpack shelf per worn slot (shields, armour)
    var wornCats = IB.LOOT.worn.map(function (sl) {
      var type = L.typeForSlot(sl), td = IB.LOOT.types[type], list = loose.filter(function (it) { return L.slotOf(it) === sl; });
      var empty = !td.minCleared || cleared >= td.minCleared ? 'No spare ' + td.name.toLowerCase() + 's.' : td.name + 's drop after level ' + td.minCleared + '.';
      return cat(sl === 'shield' ? 'Shields' : 'Armour', list.length, list.map(itemTile).join(''), empty, 'gear');
    }).join('');
    return '<section class="ep inv-bp" aria-label="Backpack">' + FR +
      '<h3 class="ep-h">' + svg(SI.mag) + 'Backpack<span>' + (guns.length + loose.length) + '</span></h3>' +
      '<div class="inv-bplist tm-scroll" data-pane="bp">' +
        cat('Weapons', guns.length, gunT, 'Every gun you own is carried.', 'guns') +
        ((G.slot && G.slot.melee && G.slot.melee.length) ? cat('Melee (click to put on V)', G.slot.melee.length, G.slot.melee.map(function (m) { return meleeTile(G, m, m === G.meleeId()); }).join(''), '', 'guns') : '') +
        cat('Attachments', mods.length, mods.map(itemTile).join(''), attNames.slice(0, -1).join(', ').replace(/^./, function (c) { return c.toUpperCase(); }) + ' and ' + attNames[attNames.length - 1] + ' drop from robots.', 'gear') +
        wornCats +
      '</div></section>';
  }

  // ---------- ammo panel ----------
  function ammoPanel(G) {
    if (!G.ws) return '';
    var rows = IB.Weapons.ownedSlots(G.ws).map(function (k) {
      var id = G.ws.slots[k], gun = G.ws.guns[id]; if (!gun) return '';
      var size = IB.Weapons.magSize(G.ws, gun.def), res = gun.reserve === Infinity ? '∞' : gun.reserve;
      return '<li class="' + (G.ws.cur === id ? 'cur' : '') + '">' + gunPic(id, 'am-pic') +
        '<b>' + gun.mag + '<small>/' + size + '</small></b><b class="am-res">' + res + '</b></li>';
    }).join('');
    return '<section class="ep inv-ammo" aria-label="Ammo">' + FR + '<h3 class="ep-h sm">Ammo<span class="am-cols"><i>Mag</i><i>Spare</i></span></h3><ul class="am-list">' + rows + '</ul></section>';
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
    if (d.gact === 'wornslot') return { k: 'emptyworn', slot: d.sl };
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
    root.innerHTML = '<div class="inv-left"><div class="inv-cardhost tm-scroll" data-pane="card" aria-live="polite"></div>' + ammoPanel(G) + '</div>' +
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

  /* act: slot | gun | equipgun | moveslot | unequipgun | item | chip | wornslot | lock | equip | unequip | fit | detach | discard
     how: the pointer type of the click ('touch' selects first; anything else acts at once) */
  GU.act = function (root, G, act, id, w, el, how) {
    var L = IB.Loot, g = IB.Gear.gear(G); if (!g) return false;
    var ok = false, fill = false, gearChanged = false, d = (el && el.dataset) || {}, wornSl = null;
    var lo = loadout(G), max = maxSlots(G), soft = how === 'touch';
    if (act !== 'discard') S.confirm = null;
    function select(sel) { S.sel = sel; sfx('ui'); }
    switch (act) {
      case 'lock': select(null); setCard({ k: 'lock' }); sfx('dry'); return false;
      case 'melee': if (G.slot && d.melee) { G.slot.meleeSel = d.melee; ok = true; sfx('draw'); } break;
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
      case 'wornslot': S.target = null; select({ k: 'emptyworn', slot: d.sl }); break;
      case 'item': {
        var it = L.find(g, id); if (!it) break;
        var pl = placeOf(g, it, lo);
        var again = S.sel && S.sel.k === 'item' && S.sel.id === id;
        // fitted / worn items and touch first taps just select; a loose item acts at once (mouse, keys) or on the second tap
        if (pl && (pl.worn || pl.carried)) { select({ k: 'item', id: id }); break; }
        if (soft && !again) { select({ k: 'item', id: id }); break; }
        if (L.isWorn(it)) { ok = L.equipWorn(g, L.slotOf(it), id); gearChanged = ok; fill = false; if (ok) { S.sel = { k: 'item', id: id }; act = 'equip'; wornSl = L.slotOf(it); } break; }
        var tw = defaultTarget(G, g, it, lo);
        if (tw) { ok = L.attach(g, tw, IB.WEAPONS[tw], id); gearChanged = ok; act = 'fit'; S.target = null; }
        S.sel = { k: 'item', id: id };
        if (!tw) sfx('dry');
        break;
      }
      case 'equip': { var ei = L.find(g, id); wornSl = ei && L.slotOf(ei); ok = !!ei && L.equipWorn(g, wornSl, id); gearChanged = ok; break; }
      case 'unequip': { var ws = L.wornSlot(g, id); ok = !!ws && L.equipWorn(g, ws, null); gearChanged = ok; break; }
      case 'fit': ok = L.attach(g, w, IB.WEAPONS[w], id); gearChanged = ok; S.sel = { k: 'item', id: id }; S.target = null; break;
      case 'detach': { var at = L.attachedTo(g, id); ok = !!at && L.detach(g, at.weapon, at.slot); gearChanged = ok; S.sel = { k: 'item', id: id }; break; }
      case 'discard':
        if (S.confirm !== id) { S.confirm = id; sfx('ui'); GU.render(root, G); return false; }
        S.confirm = null; ok = L.discard(g, id); gearChanged = ok; S.sel = null; break;
    }
    if (ok && gearChanged) {
      // a newly equipped shield starts empty and charges up (no free refill from swapping cells mid-fight)
      IB.Gear.refresh(G, fill);
      if (act === 'equip' && wornSl === 'shield' && G.player.shield) { G.player.shield.cur = 0; G.player.shield.since = G.player.shield.delay; }
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
