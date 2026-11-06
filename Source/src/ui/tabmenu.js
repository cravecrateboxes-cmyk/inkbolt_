/* INKBOLT field kit: the in-game Tab menu (Inventory, Skills, Character). Opened by game.js (G.openMenu) which pauses
   the game and releases the pointer; Tab / Esc / the close button resume (G.closeMenu).
   Layout (desktop): an icon tab strip on top with the active tab's name, three holo panels below — the side panels
   turned a little towards the middle — and a key-hint row. Phones stack or narrow the panels.
   Keyboard: Q / E (or the chevrons) switch tabs, arrows move between buttons, Enter selects (Enter on the selected
   skill spends a point; in the inventory Enter equips). The Inventory tab is drawn by IB.GearUI (ui/gear.js). */
(function (IB) {
  'use strict';
  var T = IB.TabMenu = { tab: 'inventory', sel: null, confirmRespec: false };
  var el = null, G = null;
  var TABS = [['inventory', 'Inventory'], ['skills', 'Skills'], ['character', 'Character']];
  var ALIAS = { loadout: 'inventory', gear: 'inventory' };
  var ROMAN = ['', 'I', 'II', 'III', 'IV', 'V'];

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function touch() { return !!(IB.Input && IB.Input.touch); }
  function svg(d, cls) { return '<svg' + (cls ? ' class="' + cls + '"' : '') + ' viewBox="0 0 24 24" aria-hidden="true">' + d + '</svg>'; }

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
    inventory: '<path d="M2 8h16v4h4v3H13v6H9l-1-6H5l-2 4H1l1-5H2z" fill="currentColor"/>',
    skills: '<path d="M12 1l3 7h7l-5.6 4.4 2.1 7.6L12 15.6 5.5 20l2.1-7.6L2 8h7z" fill="currentColor"/>',
    character: '<circle cx="12" cy="7" r="5" fill="currentColor"/><path d="M2 23c0-6 4.5-9 10-9s10 3 10 9z" fill="currentColor"/>'
  };
  function icon(k) { return svg(ICON[k] || ICON.core); }
  var CHEV = '<path d="M15 3 6 12l9 9" fill="none" stroke="currentColor" stroke-width="4"/>';

  // ---------- open / close ----------
  T.open = function (game, tab) {
    G = game; el = document.getElementById('tabmenu');
    if (tab) T.tab = ALIAS[tab] || tab;
    if (!TABS.some(function (t) { return t[0] === T.tab; })) T.tab = 'inventory';
    T.confirmRespec = false;
    if (IB.GearUI && IB.GearUI.reset) IB.GearUI.reset(G);
    if (!T.sel || !IB.SKILL_BY_ID[T.sel]) T.sel = firstSuggested();
    el.hidden = false;
    render(true);
  };
  T.close = function () { if (!el) return; el.hidden = true; el.innerHTML = ''; };
  T.isOpen = function () { return !!el && !el.hidden; };
  T.setTab = function (t) { T.tab = ALIAS[t] || t; T.confirmRespec = false; render(true); };
  function stepTab(d) {
    var i = TABS.map(function (t) { return t[0]; }).indexOf(T.tab);
    IB.Audio && IB.Audio.play('ui'); T.setTab(TABS[(i + d + TABS.length) % TABS.length][0]);
  }

  function firstSuggested() {
    var sk = G.slot.skills || {}, h = G.slot.highest || 0;
    for (var i = 0; i < IB.SKILLS.length; i++) if (IB.Skills.canBuy(sk, h, IB.SKILLS[i].id).ok) return IB.SKILLS[i].id;
    return IB.SKILLS[0].id;
  }

  // ---------- render ----------
  function render(focusFirst) {
    var pr = G.progress(), keepFocus = document.activeElement && el.contains(document.activeElement) ? navKey(document.activeElement) : null;
    var scroll = {}; el.querySelectorAll('.tm-scroll').forEach(function (s) { scroll[s.dataset.pane] = s.scrollTop; });
    var tabs = TABS.map(function (t) {
      var badge = t[0] === 'skills' && pr.points > 0 ? '<span class="tm-badge">' + pr.points + '</span>' : '';
      return '<button class="tm-tab" role="tab" data-tab="' + t[0] + '" data-nav id="tmTab_' + t[0] + '" aria-selected="' + (T.tab === t[0]) + '" aria-controls="tmPanel" aria-label="' + t[1] + '">' +
        '<span class="tm-tab-ic">' + svg(TAB_ICON[t[0]]) + '</span><span class="tm-tab-l">' + t[1] + '</span>' + badge + '</button>';
    }).join('');
    var body = T.tab === 'skills' ? skillsPanel(pr) : T.tab === 'character' ? characterPanel(pr) : inventoryPanel();
    var cur = TABS.filter(function (t) { return t[0] === T.tab; })[0][1];
    el.innerHTML = '<div class="tm-scrim" data-act="close"></div>' +
      '<section class="tm-frame" role="dialog" aria-modal="true" aria-label="Field kit">' +
        '<header class="tm-head">' +
          '<div class="tm-id"><span class="lvb tm-lv"><small>LV</small><b>' + pr.level + '</b></span>' +
            '<span class="tm-idtxt"><b class="tm-title">' + esc(pr.title) + '</b><span class="tm-sub">' + subline(pr) + '</span></span></div>' +
          '<nav class="tm-tabs" role="tablist" aria-label="Field kit">' + (touch() ? '' : '<kbd class="qe">Q</kbd>') + tabs + '<b class="tm-curlbl" aria-hidden="true">' + cur + '</b>' + (touch() ? '' : '<kbd class="qe">E</kbd>') + '</nav>' +
          '<div class="tm-meta"><span class="tm-gems" aria-label="Gems"><i class="gem-glyph" aria-hidden="true"></i><b>' + (G.slot.gems || 0) + '</b></span>' +
            '<button class="tm-close" data-act="close" data-nav aria-label="Close and resume">' + svg('<path d="M5 5l14 14M19 5 5 19" stroke="currentColor" stroke-width="3.4"/>') + '<kbd>' + (touch() ? 'Back' : 'Tab') + '</kbd></button></div>' +
        '</header>' +
        '<div class="tm-body tm-scroll tm-' + T.tab + '" data-pane="body" id="tmPanel" role="tabpanel" aria-labelledby="tmTab_' + T.tab + '">' + body +
          '<button class="tm-chev l" data-step="-1" aria-label="Previous tab">' + svg(CHEV) + '</button><button class="tm-chev r" data-step="1" aria-label="Next tab">' + svg(CHEV) + '</button>' +
        '</div>' +
        '<footer class="tm-foot">' + footer() + '</footer>' +
      '</section>';
    if (T.tab === 'inventory') mountGear();
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
    if (a.dataset.k) return '[data-k="' + a.dataset.k + '"]';
    if (a.dataset.tab) return '[data-tab="' + a.dataset.tab + '"]';
    if (a.dataset.act) return '[data-act="' + a.dataset.act + '"][data-nav]';
    return null;
  }
  function footer() {
    if (touch()) return '';
    var mid = T.tab === 'skills' ? '<span><kbd>Enter</kbd>Select · again to spend</span>' : T.tab === 'inventory' ? '<span><kbd>Enter</kbd>Select / equip</span><span><kbd>Mouse</kbd>Point to inspect</span>' : '';
    return '<span><kbd>Q</kbd><kbd>E</kbd>Tabs</span><span><kbd>Arrows</kbd>Move</span>' + mid + '<span><kbd>Tab</kbd><kbd>Esc</kbd>Resume</span>';
  }

  // ---------- skills ----------
  function rankBadge(s, r) {
    var cls = r >= s.max ? 'r-max' : r > 0 ? 'r-part' : 'r-zero';
    return '<span class="sk-rank ' + cls + '">' + r + '/' + s.max + '</span>';
  }
  function skillsPanel(pr) {
    var sk = G.slot.skills || {}, h = pr.highest;
    var tiers = IB.SKILL_TIERS.slice().reverse().map(function (t, ri) {
      var open = IB.Skills.tierUnlocked(sk, t.tier), above = IB.Skills.spentAbove(sk, t.tier);
      var list = IB.SKILLS.filter(function (s) { return s.tier === t.tier; });
      var nodes = list.map(function (s, i) {
        var n = node(s, sk, h, open);
        return t.capstone && i > 0 ? '<span class="sk-or" aria-hidden="true">OR</span>' + n : n;
      }).join('');
      // the pipe up to the next gate fills with the points spent toward it
      var nx = IB.SKILL_TIERS[t.tier], seg = nx ? Math.max(0, Math.min(1, (IB.Skills.spentAbove(sk, nx.tier) - t.gate) / (nx.gate - t.gate))) : 0;
      var gate = '<span class="sk-gate" title="' + (t.gate ? t.gate + ' points in the tiers below open this tier' : 'Open from the start') + '">' + (open ? '' : svg(ICON.lock, 'sk-glock')) + '<b>' + (t.capstone ? ROMAN[5] : ROMAN[t.tier]) + '</b><small>' + t.gate + '</small></span>' +
        (nx ? '<span class="sk-pipe' + (ri === 1 ? ' top' : '') + '" style="--seg:' + seg.toFixed(3) + '"><i></i></span>' : '');
      var need = open ? '' : '<span class="sk-need">' + svg(ICON.lock) + (t.gate - above) + ' more</span>';
      return '<div class="sk-tier t' + t.tier + (open ? ' open' : ' locked') + (t.capstone ? ' cap' : '') + '">' +
        '<div class="sk-rail">' + gate + '</div>' +
        '<div class="sk-tierbody">' + (t.capstone ? '<div class="sk-caphead"><b>Capstone</b><span>Pick one · ' + t.gate + ' points below</span>' + need + '</div>' : '') +
        '<div class="sk-row n' + list.length + '">' + nodes + '</div>' + (t.capstone ? '' : '<span class="sk-tname">' + ROMAN[t.tier] + ' · ' + t.name + need + '</span>') + '</div></div>';
    }).join('');
    var spent = IB.Skills.spent(sk);
    return '<div class="sk-left">' + detail(pr, sk, h) + plate(pr, sk, h) + '</div>' +
      '<div class="holo sk-treebox"><div class="sk-tree tm-scroll" data-pane="tree">' + tiers + '</div>' +
        '<div class="sk-treefoot"><b>Scrap tree</b><span class="sk-spent" title="Points spent in the tree">' + spent + '</span></div></div>' +
      bonusPanel(sk);
  }
  function node(s, sk, h, open) {
    var r = IB.Skills.rank(sk, s.id), cb = IB.Skills.canBuy(sk, h, s.id);
    var owner = IB.Skills.groupOwner(sk, s.group), shut = owner && owner !== s.id;
    var cls = 'sk-node k-' + s.kind + (r > 0 ? ' owned' : '') + (r >= s.max ? ' maxed' : '') + (!open || shut ? ' dim' : '') + (cb.ok ? ' buyable' : '') + (T.sel === s.id ? ' sel' : '');
    var label = s.name + ', ' + (s.kind === 'rank' ? 'rank ' + r + ' of ' + s.max : r ? 'owned' : 'not owned') + (cb.ok ? ', can spend' : '');
    return '<button class="' + cls + '" data-skill="' + s.id + '" data-nav aria-pressed="' + (T.sel === s.id) + '" aria-label="' + esc(label) + '">' +
      '<span class="cell sk-tile"><span class="sk-ic">' + icon(s.icon) + '</span>' + rankBadge(s, r) +
        (s.kind === 'special' ? '<span class="sk-star" aria-hidden="true">' + svg(ICON.burst) + '</span>' : '') +
        (cb.ok ? '<span class="sk-plus" aria-hidden="true">+</span>' : '') + '</span>' +
      '<span class="sk-name">' + esc(s.name) + '</span>' +
      (s.kind === 'capstone' ? '<span class="sk-cap">' + esc(s.stat) + ' · ' + s.cost + ' pts</span>' : '') +
      '</button>';
  }
  function detail(pr, sk, h) {
    var s = IB.SKILL_BY_ID[T.sel], r = IB.Skills.rank(sk, s.id), cb = IB.Skills.canBuy(sk, h, s.id), tx = IB.Skills.rankText(s.id, r);
    var tierName = IB.SKILL_TIERS[s.tier - 1].name;
    var kind = s.kind === 'capstone' ? 'Capstone · ' + s.cost + ' points · only one' : s.kind === 'special' ? 'Tier ' + ROMAN[s.tier] + ' · ' + tierName + ' · special ability' : 'Tier ' + ROMAN[s.tier] + ' · ' + tierName;
    var rows = s.kind === 'rank' ? '<div class="sk-ranks">' + s.ranks.map(function (v, i) {
      return '<span class="' + (i < r ? 'on' : i === r ? 'next' : '') + '"><b>+' + v + s.unit + '</b><small>Rank ' + (i + 1) + '</small></span>';
    }).join('') + '</div>' : '';
    var lines = s.kind === 'rank' ? '<div class="sk-lines">' + (r > 0 ? '<p><span>Current:</span> ' + esc(tx.now) + '</p>' : '') +
      (tx.next ? '<p class="nx"><span>Next level:</span> ' + esc(tx.next) + '</p>' : '<p class="mx"><span>Maxed out</span></p>') + '</div>'
      : '<div class="sk-lines"><p class="' + (r ? 'mx' : 'nx') + '"><span>' + (r ? 'Owned' : 'Unlock:') + '</span> ' + esc(s.stat) + '</p></div>';
    var why = { max: '', tier: 'Spend ' + (cb.need || 0) + ' more point' + (cb.need === 1 ? '' : 's') + ' in the tiers below', exclusive: 'You chose ' + (cb.owner ? IB.SKILL_BY_ID[cb.owner].name : '') + '. Respec to switch.',
      points: pr.points > 0 ? 'Needs ' + s.cost + ' points' : (pr.earned >= IB.Skills.totalPoints() ? 'Every point is spent' : 'Clear the next level for more points') }[cb.reason] || '';
    var buyLabel = cb.ok ? 'Spend ' + s.cost + ' point' + (s.cost > 1 ? 's' : '') : (cb.reason === 'max' ? (s.kind === 'rank' ? 'Maxed' : 'Owned') : 'Locked');
    return '<div class="holo hsel sk-card k-' + s.kind + '" aria-live="polite">' +
        '<div class="sk-dhead"><span class="sk-dic">' + icon(s.icon) + '</span><span class="sk-dtxt"><b>' + esc(s.name) + '</b><small>' + kind + '</small></span>' + rankBadge(s, r) + '</div>' +
        '<p class="sk-text">' + esc(s.text) + '</p>' + lines + rows +
        (why ? '<div class="sk-why">' + svg(ICON.lock) + esc(why) + '</div>' : '') +
        '<button class="btn primary sk-buy" data-act="buy" data-nav' + (cb.ok ? '' : ' disabled aria-disabled="true"') + '><span class="btn-l">' + buyLabel + '</span></button>' +
      '</div>';
  }
  function plate(pr, sk, h) {
    var cost = IB.Skills.respecCost(h), spent = IB.Skills.spent(sk), canRespec = spent > 0 && (G.slot.gems || 0) >= cost;
    var respecLbl = T.confirmRespec ? 'Confirm reset' : 'Respec tree';
    return '<div class="holo sk-plate">' +
      '<div class="sk-who"><span class="lvb"><small>LV</small><b>' + pr.level + '</b></span><span><b class="sk-whoname">' + esc(pr.title) + '</b><small>Scrapper · ' + spent + ' spent · ' + pr.earned + ' earned</small></span></div>' +
      '<div class="sk-points"><span>Skill points</span><b class="' + (pr.points > 0 ? 'has' : '') + '">' + pr.points + '</b></div>' +
      '<div class="sk-respec"><span><b>Reset the tree</b><small>All points back · costs gems</small></span>' +
        '<button class="btn danger sk-rbtn' + (T.confirmRespec ? ' confirm' : '') + '" data-act="respec" data-nav' + (canRespec ? '' : ' disabled aria-disabled="true"') + '><span class="btn-l">' + respecLbl + '</span><span class="hint"><i class="gem-glyph sm" aria-hidden="true"></i>' + cost + '</span></button></div>' +
      '</div>';
  }
  function bonusPanel(sk) {
    var rows = IB.SKILLS.filter(function (s) { return IB.Skills.rank(sk, s.id) > 0; }).map(function (s) {
      var r = IB.Skills.rank(sk, s.id), tx = IB.Skills.rankText(s.id, r);
      var v = s.kind === 'rank' ? '+' + s.ranks[r - 1] + s.unit : 'On';
      return '<li class="k-' + s.kind + '">' + icon(s.icon) + '<span><b>' + esc(s.name) + '</b><small>' + esc(s.kind === 'rank' ? s.stat : s.stat) + '</small></span><em>' + esc(v) + '</em></li>';
    }).join('');
    var total = 0; IB.SKILLS.forEach(function (s) { total += s.max * s.cost; });
    return '<aside class="holo sk-bonus" aria-label="Active bonuses"><h3 class="inv-h">' + IB.Menus.glyph('star') + 'Active bonuses</h3>' +
      '<div class="tm-scroll sk-blist" data-pane="bonus">' + (rows ? '<ul>' + rows + '</ul>' : '<p class="inv-none">No skills yet. Pick one in the tree and spend a point.</p>') + '</div>' +
      '<div class="sk-bfoot"><span>Tree</span><b>' + IB.Skills.spent(sk) + '<small>/' + total + '</small></b></div></aside>';
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

  // ---------- inventory (IB.GearUI) ----------
  function inventoryPanel() { return '<div class="gear-host" id="tmGear"></div>'; }
  function mountGear() {
    var host = el.querySelector('#tmGear');
    if (IB.GearUI && IB.GearUI.render) {
      try { IB.GearUI.render(host, G); return; } catch (e) { if (G.errors) G.errors.push('GearUI: ' + e.message); }
    }
    host.innerHTML = '<div class="tm-empty"><b>Inventory unavailable</b></div>';
  }

  // ---------- character ----------
  function characterPanel(pr) {
    var sk = G.slot.skills || {}, fx = IB.Skills.effects(sk), gfx = G.fx || {}, g = IB.Gear && IB.Gear.gear(G);
    var cap = IB.PLAYER_LEVEL_CAP, next = pr.level < cap ? IB.Skills.rankTitle(pr.level + 1) : null;
    var lvPct = Math.round(Math.min(1, (pr.level - 1) / (cap - 1)) * 100), ptPct = Math.round(pr.earned / IB.Skills.totalPoints() * 100);
    var hp = Math.round((gfx.maxHp || 100) * (fx.maxHpMul || 1)) + (fx.maxHpAdd || 0);
    var sh = g && g.shield ? IB.Loot.find(g, g.shield) : null;
    function pct(m) { var v = Math.round((m - 1) * 100); return (v >= 0 ? '+' : '') + v + '%'; }
    function row(ic, k, v, hl) { return '<li' + (hl ? ' class="hl"' : '') + '>' + (ICON[ic] ? icon(ic) : IB.Menus.glyph(ic)) + '<span>' + k + '</span><b>' + v + '</b></li>'; }
    var stats = '<ul class="ch-stats">' +
      row('heart', 'Max health', hp, fx.maxHpMul > 1) +
      row('armor', 'Shield', sh ? sh.stats.capacity + ' · ' + sh.stats.rate + '/s' : 'None', !!sh) +
      row('drop', 'Gun damage', pct(fx.dmgMul), fx.dmgMul > 1) +
      row('core', 'Core-hit damage', pct(fx.coreMul), fx.coreMul > 1) +
      row('gauge', 'Fire rate', pct(fx.rateMul), fx.rateMul > 1) +
      row('reload', 'Reload speed', pct(1 / fx.reloadMul), fx.reloadMul < 1) +
      row('mag', 'Magazine size', pct(fx.magMul), fx.magMul > 1) +
      row('steady', 'Recoil', pct(fx.recoilMul), fx.recoilMul < 1) +
      row('wind', 'Sprint stamina', pct(fx.staminaMul), fx.staminaMul > 1) +
      row('magnet', 'Gem pickup range', pct(fx.magnetMul), fx.magnetMul > 1) +
      row('wrench', 'Repair per kill', fx.leech ? '+' + fx.leech : '—', fx.leech > 0) +
      '</ul>';
    var perks = [];
    if (fx.shock) perks.push(['bolt', 'Shock rounds']);
    if (fx.cloak) perks.push(['cloak', 'Undercover (F)']);
    if (fx.sprintMul > 1) perks.push(['run', 'Marathon']);
    if (fx.chain) perks.push(['burst', 'Chain Reaction']);
    if (fx.rogue) perks.push(['helper', 'Handy Helpers']);
    var st = G.slot.stats || {}, run = G.run || {};
    var ars = (G.slot.arsenal || []).length, all = Object.keys(IB.WEAPONS).filter(function (w) { return !IB.Weapons.playable || IB.Weapons.playable(w); }).length;
    function rec(k, v) { return '<li><span>' + k + '</span><b>' + v + '</b></li>'; }
    return '<div class="holo ch-id">' +
        '<div class="ch-badge"><svg viewBox="-50 -50 100 100" aria-hidden="true"><polygon points="44,0 22,38 -22,38 -44,0 -22,-38 22,-38"/></svg><span><small>LV</small><b>' + pr.level + '</b></span></div>' +
        '<b class="ch-title">' + esc(pr.title) + '</b><span class="ch-sub">Scrapper · player level ' + pr.level + ' of ' + cap + '</span>' +
        '<div class="ch-bar"><span>Rank</span><i><i style="width:' + lvPct + '%"></i></i><b>' + pr.level + '/' + cap + '</b></div>' +
        '<div class="ch-bar"><span>Skill pts</span><i><i style="width:' + ptPct + '%"></i></i><b>' + pr.earned + '/' + IB.Skills.totalPoints() + '</b></div>' +
        '<p class="ch-next">' + (next ? 'Next rank: <b>' + esc(next) + '</b> after clearing level ' + (pr.highest + 1) + '.' : 'Top rank reached. Legend status.') + '</p>' +
        (perks.length ? '<div class="ch-perks">' + perks.map(function (p) { return '<span>' + icon(p[0]) + esc(p[1]) + '</span>'; }).join('') + '</div>' : '') +
      '</div>' +
      '<section class="holo ch-mid" aria-label="Stats"><h3 class="inv-h">' + IB.Menus.glyph('emblem') + 'Combat stats<span>skills + bench</span></h3><div class="tm-scroll" data-pane="stats">' + stats + '</div></section>' +
      '<aside class="holo ch-rec" aria-label="Service record"><h3 class="inv-h">' + IB.Menus.glyph('star') + 'Service record</h3><div class="tm-scroll" data-pane="rec">' +
        '<h4 class="inv-cat"><span>This level</span></h4><ul class="ch-list">' + rec('Level', G.plan ? G.plan.level + ' · ' + esc(G.plan.name) : '—') + rec('Time', IB.HUD.mmss(run.time || 0)) + rec('Robots crushed', run.kills || 0) + rec('Retries left', Math.max(0, run.retries == null ? 0 : run.retries)) + '</ul>' +
        '<h4 class="inv-cat"><span>Career</span></h4><ul class="ch-list">' + rec('Levels cleared', pr.highest) + rec('Robots crushed', (st.kills || 0) + (run.kills || 0)) + rec('Deaths', (st.deaths || 0) + (run.deaths || 0)) +
          rec('Time played', IB.HUD.mmss((st.time || 0) + (run.time || 0))) + rec('Guns owned', ars + '/' + all) + rec('Gear found', g ? g.found || 0 : 0) + rec('Gems', G.slot.gems || 0) + '</ul>' +
      '</div></aside>';
  }

  // ---------- input ----------
  function onClick(e) {
    var b = e.target.closest('[data-tab],[data-skill],[data-step],[data-act]');
    if (!b || !el.contains(b) || b.disabled) return;
    if (b.dataset.tab) { if (T.tab !== b.dataset.tab) { IB.Audio && IB.Audio.play('ui'); T.setTab(b.dataset.tab); } return; }
    if (b.dataset.step) { stepTab(+b.dataset.step); return; }
    if (b.dataset.skill) { if (T.sel !== b.dataset.skill) IB.Audio && IB.Audio.play('ui'); T.sel = b.dataset.skill; T.confirmRespec = false; render(); return; }
    var a = b.dataset.act;
    if (a === 'close') G.closeMenu();
    else if (a === 'buy') buy(T.sel);
    else if (a === 'respec') respec();
  }
  function move(dir) {
    // every visible button in the frame (the inventory's own buttons from IB.GearUI included)
    var list = Array.prototype.slice.call(el.querySelectorAll('.tm-frame button, .tm-frame [data-nav]')).filter(function (b) { return !b.disabled && b.offsetParent !== null && !b.classList.contains('tm-chev'); });
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
    if (k === 'q' || k === 'Q' || k === 'e' || k === 'E') { e.preventDefault(); stepTab(k === 'e' || k === 'E' ? 1 : -1); return; }
    var dirs = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
    if (dirs[k]) { e.preventDefault(); move(dirs[k]); return; }
    if (k === 'Enter' && document.activeElement && document.activeElement.dataset.skill === T.sel && T.tab === 'skills') { e.preventDefault(); buy(T.sel); }
  }
  window.addEventListener('keydown', onKey, true);
  document.addEventListener('click', function (e) { if (T.isOpen() && el.contains(e.target)) onClick(e); });
})(window.IB = window.IB || {});
