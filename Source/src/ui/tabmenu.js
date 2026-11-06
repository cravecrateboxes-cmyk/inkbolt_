/* INKBOLT field kit: the in-game Tab menu (Loadout, Gear, Skills). Opened by game.js (G.openMenu) which pauses the
   game and releases the pointer; Tab / Esc / the close button resume (G.closeMenu).
   Keyboard: Q / E switch tabs, arrows move between buttons, Enter selects (Enter on the selected skill spends a point).
   Gear is drawn by the loot system (IB.GearUI.render(container, G)); without it the tab shows an empty state. */
(function (IB) {
  'use strict';
  var T = IB.TabMenu = { tab: 'loadout', sel: null, slotSel: 0, confirmRespec: false };
  var el = null, G = null;
  var TABS = [['loadout', 'Loadout'], ['gear', 'Gear'], ['skills', 'Skills']];
  var ROMAN = ['', 'I', 'II', 'III', 'IV', 'V'];

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function touch() { return !!(IB.Input && IB.Input.touch); }
  function svg(d, vb) { return '<svg viewBox="' + (vb || '0 0 24 24') + '" aria-hidden="true">' + d + '</svg>'; }

  // ---------- skill glyphs (24 x 24, currentColor) ----------
  var ICON = {
    mag: '<path d="M8 2h8l-1.2 20H9.2z" fill="currentColor"/><path d="M10 6h4M10 10h4M10 14h4" stroke="var(--ink)" stroke-width="2"/>',
    reload: '<path d="M19 12a7 7 0 1 1-2.05-4.95" fill="none" stroke="currentColor" stroke-width="3.2"/><path d="M21 3v7h-7z" fill="currentColor"/>',
    armor: '<path d="M12 2 21 6v6c0 5-4 8.5-9 10-5-1.5-9-5-9-10V6z" fill="currentColor"/><path d="M8 9h8M8 13h8" stroke="var(--ink)" stroke-width="2"/>',
    steady: '<circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" stroke-width="3"/><path d="M12 1v6M12 17v6M1 12h6M17 12h6" stroke="currentColor" stroke-width="3"/>',
    magnet: '<path d="M4 3h5v9a3 3 0 0 0 6 0V3h5v9a8 8 0 0 1-16 0z" fill="currentColor"/><path d="M4 7h5M15 7h5" stroke="var(--ink)" stroke-width="2"/>',
    wind: '<path d="M2 7h12a3 3 0 1 0-3-3M2 12h18a3 3 0 1 1-3 3M2 17h9" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="square"/>',
    drop: '<path d="M12 2c4 6 7 9.5 7 13a7 7 0 0 1-14 0c0-3.5 3-7 7-13z" fill="currentColor"/><path d="M9 15a3 3 0 0 0 3 3" fill="none" stroke="var(--ink)" stroke-width="2"/>',
    bolt: '<path d="M14 1 4 14h6l-2 9 11-14h-6z" fill="currentColor"/>',
    core: '<circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="12" cy="12" r="4.5" fill="currentColor"/>',
    gauge: '<path d="M2 17a10 10 0 0 1 20 0z" fill="currentColor"/><path d="M12 17l5-7" stroke="var(--ink)" stroke-width="2.6"/><circle cx="12" cy="17" r="2" fill="var(--ink)"/>',
    burst: '<path d="M12 1l2.4 6.2 6.6-2.4-3.4 6.1L23 14l-6.6.9 1.4 6.6L12 18l-5.8 3.5 1.4-6.6L1 14l5.4-3.1L3 4.8l6.6 2.4z" fill="currentColor"/>',
    heart: '<path d="M12 21 3 12a5 5 0 0 1 9-6 5 5 0 0 1 9 6z" fill="currentColor"/><path d="M12 7l-2 4 3 2-2 4" fill="none" stroke="var(--ink)" stroke-width="2"/>',
    wrench: '<path d="M21 6.5a5 5 0 0 1-7.1 4.6L5 20a2.1 2.1 0 0 1-3-3l8.9-8.9A5 5 0 0 1 17.5 1L14 4.5l1 3.5 3.5 1z" fill="currentColor"/>',
    rod: '<path d="M11 1h2v22h-2z" fill="currentColor"/><path d="M5 4h14M7 8h10" stroke="currentColor" stroke-width="2.4"/><path d="M19 11l-4 5h3l-2 5 5-6h-3z" fill="currentColor"/><path d="M5 11l-3 4h2.5l-1.5 4" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    titan: '<path d="M12 1 22 6.5v11L12 23 2 17.5v-11z" fill="currentColor"/><path d="M7 9h10v3a5 5 0 0 1-10 0z" fill="var(--ink)"/><path d="M9 11h6" stroke="currentColor" stroke-width="1.6"/>',
    lock: '<path d="M7 10V7a5 5 0 0 1 10 0v3" fill="none" stroke="currentColor" stroke-width="2.6"/><rect x="5" y="10" width="14" height="11" fill="currentColor"/>'
  };
  var TAB_ICON = {
    loadout: '<path d="M2 8h16v4h4v3H13v6H9l-1-6H5l-2 4H1l1-5H2z" fill="currentColor"/>',
    gear: '<path d="M12 2 21 6v6c0 5-4 8.5-9 10-5-1.5-9-5-9-10V6z" fill="currentColor"/>',
    skills: '<path d="M12 1l3 7h7l-5.6 4.4 2.1 7.6L12 15.6 5.5 20l2.1-7.6L2 8h7z" fill="currentColor"/>'
  };
  function icon(k) { return svg(ICON[k] || ICON.core); }

  // ---------- open / close ----------
  T.open = function (game, tab) {
    G = game; el = document.getElementById('tabmenu');
    if (tab) T.tab = tab;
    T.confirmRespec = false;
    var lo = G.slot.loadout || [];
    T.slotSel = Math.min(lo.length, G.progress().loadoutMax - 1);
    if (!T.sel || !IB.SKILL_BY_ID[T.sel]) T.sel = firstSuggested();
    el.hidden = false;
    render(true);
  };
  T.close = function () { if (!el) return; el.hidden = true; el.innerHTML = ''; };
  T.isOpen = function () { return !!el && !el.hidden; };
  T.setTab = function (t) { T.tab = t; T.confirmRespec = false; render(true); };

  function firstSuggested() {
    var sk = G.slot.skills || {}, h = G.slot.highest || 0;
    for (var i = 0; i < IB.SKILLS.length; i++) if (IB.Skills.canBuy(sk, h, IB.SKILLS[i].id).ok) return IB.SKILLS[i].id;
    return IB.SKILLS[0].id;
  }

  // ---------- render ----------
  function render(focusFirst) {
    var pr = G.progress(), keepFocus = document.activeElement && el.contains(document.activeElement) ? navKey(document.activeElement) : null;
    var scroll = {}; el.querySelectorAll('.tm-scroll').forEach(function (s) { scroll[s.dataset.pane] = s.scrollTop; });
    var tabs = TABS.map(function (t, i) {
      var badge = t[0] === 'skills' && pr.points > 0 ? '<span class="tm-badge">' + pr.points + '</span>' : '';
      return '<button class="tm-tab" role="tab" data-tab="' + t[0] + '" data-nav id="tmTab_' + t[0] + '" aria-selected="' + (T.tab === t[0]) + '" aria-controls="tmPanel">' +
        svg(TAB_ICON[t[0]]) + '<span>' + t[1] + '</span>' + badge + '</button>';
    }).join('');
    var body = T.tab === 'skills' ? skillsPanel(pr) : T.tab === 'gear' ? gearPanel() : loadoutPanel(pr);
    el.innerHTML = '<div class="tm-scrim" data-act="close"></div>' +
      '<section class="plate ink tm-frame" role="dialog" aria-modal="true" aria-label="Field kit">' +
        '<header class="tm-head">' +
          '<div class="tm-id"><span class="tm-lv"><small>LV</small><b>' + pr.level + '</b></span>' +
            '<span class="tm-idtxt"><b class="tm-title">' + esc(pr.title) + '</b><span class="tm-sub">' + subline(pr) + '</span></span></div>' +
          '<nav class="tm-tabs" role="tablist" aria-label="Field kit">' + tabs + '</nav>' +
          '<div class="tm-meta"><span class="tm-gems" aria-label="Gems"><i class="gem-glyph" aria-hidden="true"></i><b>' + (G.slot.gems || 0) + '</b></span>' +
            '<button class="tm-close" data-act="close" data-nav aria-label="Close and resume">' + svg('<path d="M5 5l14 14M19 5 5 19" stroke="currentColor" stroke-width="3.4"/>') + '<kbd>' + (touch() ? 'Back' : 'Tab') + '</kbd></button></div>' +
        '</header>' +
        '<div class="hazard tm-hazard"></div>' +
        '<div class="tm-body tm-' + T.tab + '" id="tmPanel" role="tabpanel" aria-labelledby="tmTab_' + T.tab + '">' + body + '</div>' +
        '<footer class="tm-foot">' + footer() + '</footer>' +
      '</section>';
    if (T.tab === 'gear') mountGear();
    el.querySelectorAll('.tm-scroll').forEach(function (s) { if (scroll[s.dataset.pane]) s.scrollTop = scroll[s.dataset.pane]; });
    if (focusFirst) { var seln = el.querySelector('.sk-node.sel'); if (seln) seln.scrollIntoView({ block: 'center' }); }
    if (touch()) return;
    var f = keepFocus ? el.querySelector(keepFocus) : null;
    if (!f && focusFirst) f = el.querySelector('.sk-node.sel') || el.querySelector('.lo-slot.sel') || el.querySelector('.tm-body [data-nav]') || el.querySelector('.tm-tab[aria-selected="true"]');
    if (f) f.focus({ preventScroll: !keepFocus });
  }
  function subline(pr) {
    var cleared = pr.highest > 0 ? 'Level ' + pr.highest + ' cleared' : 'No level cleared yet';
    return cleared + ' · ' + pr.earned + ' of ' + IB.Skills.totalPoints() + ' skill points';
  }
  function navKey(a) {
    if (a.dataset.skill) return '[data-skill="' + a.dataset.skill + '"]';
    if (a.dataset.gun) return '[data-gun="' + a.dataset.gun + '"]';
    if (a.dataset.slot) return '[data-slot="' + a.dataset.slot + '"]';
    if (a.dataset.tab) return '[data-tab="' + a.dataset.tab + '"]';
    if (a.dataset.act) return '[data-act="' + a.dataset.act + '"][data-nav]';
    return null;
  }
  function footer() {
    if (touch()) return '<span>Tap a skill, then spend</span><span>Pick a slot, then a gun</span>';
    var mid = T.tab === 'skills' ? '<span><kbd>Enter</kbd> select · again to spend</span>' : T.tab === 'loadout' ? '<span><kbd>Enter</kbd> pick slot, then gun</span>' : '';
    return '<span><kbd>Q</kbd><kbd>E</kbd> tabs</span><span><kbd>Arrows</kbd> move</span>' + mid + '<span><kbd>Tab</kbd><kbd>Esc</kbd> resume</span>';
  }

  // ---------- skills ----------
  function skillsPanel(pr) {
    var sk = G.slot.skills || {}, h = pr.highest;
    var tiers = IB.SKILL_TIERS.map(function (t) {
      var open = IB.Skills.tierUnlocked(sk, t.tier), above = IB.Skills.spentAbove(sk, t.tier);
      var list = IB.SKILLS.filter(function (s) { return s.tier === t.tier; });
      var nodes = list.map(function (s, i) {
        var n = node(s, sk, h, open);
        return t.capstone && i > 0 ? '<span class="sk-or" aria-hidden="true">OR</span>' + n : n;
      }).join('');
      var gate = t.gate ? '<span class="sk-gate"><b>' + t.gate + '</b></span>' : '<span class="sk-gate start"><b>' + ROMAN[t.tier] + '</b></span>';
      // the pipe down to the next gate fills with the points spent toward it
      var nx = IB.SKILL_TIERS[t.tier], seg = nx ? Math.max(0, Math.min(1, (IB.Skills.spentAbove(sk, nx.tier) - t.gate) / (nx.gate - t.gate))) : 0;
      if (nx) gate += '<span class="sk-pipe" style="--seg:' + seg.toFixed(3) + '"><i></i></span>';
      var need = open ? '' : '<span class="sk-need">' + svg(ICON.lock) + 'Spend ' + (t.gate - above) + ' more above</span>';
      return '<div class="sk-tier' + (open ? ' open' : ' locked') + (t.capstone ? ' cap' : '') + '">' +
        '<div class="sk-rail">' + gate + '</div>' +
        '<div class="sk-tierbody"><div class="sk-tierhead"><b>' + (t.capstone ? 'Capstone · pick one' : 'Tier ' + ROMAN[t.tier] + ' · ' + t.name) + '</b>' + need + '</div>' +
        '<div class="sk-row n' + list.length + '">' + nodes + '</div></div></div>';
    }).join('');
    return '<div class="sk-tree tm-scroll" data-pane="tree">' + tiers + '</div>' +
      detail(pr, sk, h);
  }
  function node(s, sk, h, open) {
    var r = IB.Skills.rank(sk, s.id), cb = IB.Skills.canBuy(sk, h, s.id);
    var owner = IB.Skills.groupOwner(sk, s.group), shut = owner && owner !== s.id;
    var pips = '';
    for (var i = 0; i < s.max; i++) pips += '<i' + (i < r ? ' class="on"' : '') + '></i>';
    var cls = 'plate sk-node k-' + s.kind + (r > 0 ? ' owned' : '') + (r >= s.max ? ' maxed' : '') + (!open || shut ? ' dim' : '') + (cb.ok ? ' buyable' : '') + (T.sel === s.id ? ' sel' : '');
    var label = s.name + ', ' + (s.kind === 'rank' ? 'rank ' + r + ' of ' + s.max : r ? 'owned' : 'not owned') + (cb.ok ? ', can spend' : '');
    return '<button class="' + cls + '" data-skill="' + s.id + '" data-nav aria-pressed="' + (T.sel === s.id) + '" aria-label="' + esc(label) + '">' +
      '<span class="sk-ic">' + icon(s.icon) + '</span>' +
      '<span class="sk-name">' + esc(s.name) + '</span>' +
      (s.kind === 'capstone' ? '<span class="sk-cap">' + esc(s.stat) + ' · ' + s.cost + ' pts</span>' : '') +
      '<span class="sk-pips' + (s.max === 1 ? ' one' : '') + '">' + pips + '</span>' +
      (s.kind === 'special' ? '<span class="sk-star" aria-hidden="true">' + svg(ICON.burst) + '</span>' : '') +
      (cb.ok ? '<span class="sk-plus" aria-hidden="true">+</span>' : '') +
      '</button>';
  }
  function detail(pr, sk, h) {
    var s = IB.SKILL_BY_ID[T.sel], r = IB.Skills.rank(sk, s.id), cb = IB.Skills.canBuy(sk, h, s.id), tx = IB.Skills.rankText(s.id, r);
    var kind = s.kind === 'capstone' ? 'Capstone · ' + s.cost + ' points · only one' : s.kind === 'special' ? 'Tier ' + ROMAN[s.tier] + ' · special ability' : 'Tier ' + ROMAN[s.tier] + ' · rank ' + r + ' of ' + s.max;
    var rows = s.kind === 'rank' ? '<div class="sk-ranks">' + s.ranks.map(function (v, i) {
      return '<span class="' + (i < r ? 'on' : i === r ? 'next' : '') + '"><b>+' + v + s.unit + '</b><small>Rank ' + (i + 1) + '</small></span>';
    }).join('') + '</div>' : '';
    var why = { max: r ? 'Fully ranked' : '', tier: 'Spend ' + (cb.need || 0) + ' more point' + (cb.need === 1 ? '' : 's') + ' in the tiers above', exclusive: 'You chose ' + (cb.owner ? IB.SKILL_BY_ID[cb.owner].name : '') + '. Respec to switch.',
      points: pr.points > 0 ? 'Needs ' + s.cost + ' points' : (pr.earned >= IB.Skills.totalPoints() ? 'Every point is spent' : 'Clear the next level for more points') }[cb.reason] || '';
    var buyLabel = cb.ok ? 'Spend ' + s.cost + ' point' + (s.cost > 1 ? 's' : '') : (cb.reason === 'max' ? (s.kind === 'rank' ? 'Maxed' : 'Owned') : 'Locked');
    var cost = IB.Skills.respecCost(h), spent = IB.Skills.spent(sk), canRespec = spent > 0 && (G.slot.gems || 0) >= cost;
    var respecLbl = T.confirmRespec ? 'Confirm reset' : 'Respec tree';
    return '<aside class="sk-detail tm-scroll" data-pane="detail" aria-live="polite">' +
      '<div class="sk-points"><span>Skill points</span><b class="' + (pr.points > 0 ? 'has' : '') + '">' + pr.points + '</b><small>' + spent + ' spent · ' + pr.earned + ' earned</small></div>' +
      '<div class="sk-card k-' + s.kind + '">' +
        '<div class="sk-dhead"><span class="sk-dic">' + icon(s.icon) + '</span><span><b>' + esc(s.name) + '</b><small>' + kind + '</small></span></div>' +
        '<p>' + esc(s.text) + '</p>' + rows +
        (s.kind === 'rank' ? '<div class="sk-now"><span>' + esc(tx.now) + '</span>' + (tx.next ? '<span class="nx">Next: ' + esc(tx.next) + '</span>' : '') + '</div>' : '') +
        (why ? '<div class="sk-why">' + esc(why) + '</div>' : '') +
        '<button class="plate btn primary sk-buy" data-act="buy" data-nav' + (cb.ok ? '' : ' disabled aria-disabled="true"') + '><span>' + buyLabel + '</span></button>' +
      '</div>' +
      '<div class="sk-respec"><span><b>Reset the tree</b><small>All points back · costs gems</small></span>' +
        '<button class="plate btn danger sk-rbtn' + (T.confirmRespec ? ' confirm' : '') + '" data-act="respec" data-nav' + (canRespec ? '' : ' disabled aria-disabled="true"') + '><span>' + respecLbl + '</span><span class="hint"><i class="gem-glyph sm" aria-hidden="true"></i>' + cost + '</span></button></div>' +
      '</aside>';
  }
  function buy(id) {
    var next = IB.Skills.buy(G.slot.skills || {}, G.slot.highest || 0, id);
    if (!next) { IB.Audio && IB.Audio.play('dry'); return; }
    G.slot.skills = next; G.store.save(G.slot);
    IB.Audio && IB.Audio.play('pickup', { pitch: 1.2 });
    T.sel = id; T.confirmRespec = false;
    render();
    var n = el.querySelector('[data-skill="' + id + '"]');
    if (n) { n.classList.add('pop'); }
  }
  function respec() {
    if (!T.confirmRespec) { T.confirmRespec = true; render(); var b = el.querySelector('[data-act="respec"]'); if (b && !touch()) b.focus(); return; }
    var res = IB.Skills.respec(G.slot);
    T.confirmRespec = false;
    if (res.ok) { G.store.save(G.slot); IB.Audio && IB.Audio.play('crunch'); T.sel = firstSuggested(); }
    render();
  }

  // ---------- loadout ----------
  function gunStats(def) {
    var dmg = def.damage * (def.pellets || 1), rpm = def.burst > 1 ? Math.round(60 / def.cycle * def.burst) : Math.round(def.rpm);
    var fx = (G.ws && G.ws.fx) || {}, mag = IB.Weapons.magSize({ fx: fx }, def);
    return [['Damage', dmg, Math.min(1, Math.sqrt(dmg / 160))], ['Rate', rpm, Math.min(1, rpm / 1100)], ['Mag', mag, Math.min(1, mag / 60)]];
  }
  function gunCls(def) { return IB.HUD.clsName(def.cls); }
  function loadoutPanel(pr) {
    var lo = G.slot.loadout || [], ars = G.slot.arsenal || [], max = pr.loadoutMax, slots = '';
    for (var i = 0; i < IB.LOADOUT_RULES.extra; i++) {
      var id = lo[i], def = id && IB.WEAPONS[id];
      if (i >= max) {
        slots += '<div class="plate lo-slot locked"><span class="lo-key">' + (i + 1) + '</span><span class="lo-ic">' + svg(ICON.lock) + '</span><b>Third slot</b><small>Clear level ' + IB.LOADOUT_RULES.extraAfter + '</small></div>';
        continue;
      }
      slots += '<button class="plate lo-slot' + (def ? '' : ' empty') + (T.slotSel === i ? ' sel' : '') + '" data-slot="' + i + '" data-nav aria-pressed="' + (T.slotSel === i) + '" aria-label="Slot ' + (i + 1) + ': ' + (def ? esc(def.name) : 'empty') + '">' +
        '<span class="lo-key">' + (i + 1) + '</span><span class="lo-ic">' + (def ? IB.HUD.icon(def.cls) : '') + '</span>' +
        '<b>' + (def ? esc(def.name) : 'Empty') + '</b><small>' + (def ? gunCls(def) : 'Pick a gun below') + '</small></button>';
    }
    var cards = ars.map(function (id) {
      var def = IB.WEAPONS[id]; if (!def) return '';
      var at = lo.indexOf(id), st = gunStats(def);
      var bars = st.map(function (x) { return '<span class="lo-st"><small>' + x[0] + '</small><i style="--v:' + x[2].toFixed(2) + '"></i><b>' + x[1] + '</b></span>'; }).join('');
      return '<button class="plate lo-card' + (at >= 0 ? ' on' : '') + '" data-gun="' + id + '" data-nav aria-pressed="' + (at >= 0) + '" aria-label="' + esc(def.name) + (at >= 0 ? ', carried in slot ' + (at + 1) : '') + '">' +
        '<span class="lo-cardhead"><span class="lo-ic">' + IB.HUD.icon(def.cls) + '</span><span class="lo-nm"><b>' + esc(def.name) + '</b><small>' + gunCls(def) + '</small></span>' +
        (at >= 0 ? '<span class="lo-badge">' + (at + 1) + '</span>' : '') + '</span>' +
        '<span class="lo-stats">' + bars + '</span></button>';
    }).join('');
    var hint = touch() ? 'Tap a slot, then the gun to carry in it.' : 'Pick a slot, then the gun for it. Keys ' + (max === 3 ? '1 2 3' : '1 2') + ' and the wheel switch between carried guns.';
    return '<div class="lo-carry"><div class="tm-h"><b>Carried</b><span>' + lo.length + ' of ' + max + '</span></div>' +
      '<div class="lo-slots n' + IB.LOADOUT_RULES.extra + '">' + slots + '</div><p class="lo-hint">' + hint + '</p></div>' +
      '<div class="lo-ars tm-scroll" data-pane="ars"><div class="tm-h"><b>Arsenal</b><span>' + ars.length + ' gun' + (ars.length === 1 ? '' : 's') + ' · weapon stands add more</span></div>' +
      '<div class="lo-grid">' + cards + '</div></div>';
  }
  function pickGun(id) {
    var max = G.progress().loadoutMax, lo = G.slot.loadout || [];
    var next = IB.Loadout.assign(lo, max, T.slotSel, id);
    G.slot.loadout = next; G.store.save(G.slot);
    IB.Audio && IB.Audio.play('draw');
    // move the cursor to the next empty slot, if any
    if (next.length < max && next.indexOf(id) >= 0) T.slotSel = next.length;
    else T.slotSel = Math.min(T.slotSel, Math.max(0, next.length - (next.length < max ? 0 : 1)));
    render();
  }

  // ---------- gear (loot system) ----------
  function gearPanel() {
    return '<div class="gear-host tm-scroll" data-pane="gear" id="tmGear"></div>';
  }
  function mountGear() {
    var host = el.querySelector('#tmGear');
    if (IB.GearUI && IB.GearUI.render) {
      try { IB.GearUI.render(host, G); return; } catch (e) { if (G.errors) G.errors.push('GearUI: ' + e.message); }
    }
    host.innerHTML = '<div class="tm-empty"><span class="tm-empty-ic">' + svg(TAB_ICON.gear) + '</span>' +
      '<b>No gear yet</b><p>Shields and gun attachments drop from tough robots. Anything you find shows up here.</p></div>';
  }

  // ---------- input ----------
  function onClick(e) {
    var b = e.target.closest('[data-tab],[data-skill],[data-slot],[data-gun],[data-act]');
    if (!b || !el.contains(b) || b.disabled) return;
    if (b.dataset.tab) { if (T.tab !== b.dataset.tab) { IB.Audio && IB.Audio.play('ui'); T.setTab(b.dataset.tab); } return; }
    if (b.dataset.skill) { if (T.sel !== b.dataset.skill) IB.Audio && IB.Audio.play('ui'); T.sel = b.dataset.skill; T.confirmRespec = false; render(); return; }
    if (b.dataset.slot) { T.slotSel = +b.dataset.slot; IB.Audio && IB.Audio.play('ui'); render(); return; }
    if (b.dataset.gun) { pickGun(b.dataset.gun); return; }
    var a = b.dataset.act;
    if (a === 'close') G.closeMenu();
    else if (a === 'buy') buy(T.sel);
    else if (a === 'respec') respec();
  }
  function move(dir) {
    // every visible button in the frame (the Gear tab's own buttons from IB.GearUI included)
    var list = Array.prototype.slice.call(el.querySelectorAll('.tm-frame button, .tm-frame [data-nav]')).filter(function (b) { return !b.disabled && b.offsetParent !== null; });
    var a = document.activeElement;
    if (!a || list.indexOf(a) < 0) { var f = el.querySelector('.sel[data-nav]') || list[0]; if (f) f.focus(); return; }
    var ra = a.getBoundingClientRect(), ax = ra.left + ra.width / 2, ay = ra.top + ra.height / 2, best = null, bs = Infinity;
    list.forEach(function (b) {
      if (b === a) return;
      var rb = b.getBoundingClientRect(), bx = rb.left + rb.width / 2, by = rb.top + rb.height / 2, dx = bx - ax, dy = by - ay;
      var main = dir === 'right' ? dx : dir === 'left' ? -dx : dir === 'down' ? dy : -dy, side = dir === 'left' || dir === 'right' ? Math.abs(dy) : Math.abs(dx);
      if (main <= 4) return;
      var sc = main + side * 2.2;
      if (sc < bs) { bs = sc; best = b; }
    });
    if (best) { best.focus(); best.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
  }
  function onKey(e) {
    if (!T.isOpen()) return;
    var k = e.key;
    if (k === 'Tab' || k === 'Escape') { e.preventDefault(); e.stopPropagation(); if (!e.repeat) G.closeMenu(); return; }
    if (k === 'q' || k === 'Q' || k === 'e' || k === 'E') {
      e.preventDefault();
      var i = TABS.map(function (t) { return t[0]; }).indexOf(T.tab), d = (k === 'e' || k === 'E') ? 1 : -1;
      IB.Audio && IB.Audio.play('ui'); T.setTab(TABS[(i + d + TABS.length) % TABS.length][0]); return;
    }
    var dirs = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
    if (dirs[k]) { e.preventDefault(); move(dirs[k]); return; }
    if (k === 'Enter' && document.activeElement && document.activeElement.dataset.skill === T.sel && T.tab === 'skills') { e.preventDefault(); buy(T.sel); }
  }
  window.addEventListener('keydown', onKey, true);
  document.addEventListener('click', function (e) { if (T.isOpen() && el.contains(e.target)) onClick(e); });
})(window.IB = window.IB || {});
