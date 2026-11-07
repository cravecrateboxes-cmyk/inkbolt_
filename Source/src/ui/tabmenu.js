/* INKBOLT field kit: the in-game Tab menu (Inventory, Skills, Character). Opened by game.js (G.openMenu) which pauses
   the game and releases the pointer; Tab / Esc / the close button resume (G.closeMenu).
   Look (ui/fieldkit.css): a holo field-kit device in the comic world. Thick bright bevelled frames inked by hand
   (an SVG displacement filter, #fkInk), blue glass with a grid, scanlines and a painterly grunge texture (drawn once
   on a canvas), the side panels turned towards the middle, the selected thing in a big yellow frame.
   Layout (desktop): an icon tab strip with the tab's name on top, three panels below, a key-hint row. Phones stack
   (upright: the card docks at the bottom) or narrow the panels (sideways: three short scrolling columns).
   Keyboard: Q / E (or the chevrons) switch tabs, arrows move between buttons, Enter selects (Enter on the selected
   skill spends a point; in the inventory Enter equips). The Inventory tab is drawn by IB.GearUI (ui/gear.js).
   Skills: the tree is laid out like the player's sketch (data/skills.js): six rows, the trunk at the bottom and the
   two pick-one endgame skills on top; the UI only reads IB.SKILLS / IB.SKILL_TIERS and the IB.Skills API. */
(function (IB) {
  'use strict';
  var T = IB.TabMenu = { tab: 'inventory', sel: null, confirmRespec: false };
  var el = null, G = null;
  var TABS = [['inventory', 'Inventory'], ['skills', 'Skills'], ['character', 'Character']];
  var ALIAS = { loadout: 'inventory', gear: 'inventory' };
  var ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI'];
  var FR = '<i class="fr" aria-hidden="true"><i></i></i>';
  // node x per tier in the player's sketch (units: -220..220 across the tree), tier 1 = bottom row
  var LAYOUT = { 6: [-112, 112], 5: [-72, 72], 4: [-124, 0, 124], 3: [-158, 0, 158], 2: [-158, 0, 158], 1: [-72, 72] };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function touch() { return !!(IB.Input && IB.Input.touch); }
  function svg(d, cls, vb) { return '<svg' + (cls ? ' class="' + cls + '"' : '') + ' viewBox="' + (vb || '0 0 24 24') + '" aria-hidden="true">' + d + '</svg>'; }
  function skIcon(k, cls) { return IB.SkillIcons ? IB.SkillIcons.svg(k, cls) : ''; }
  var LOCK = '<path d="M7 10V7a5 5 0 0 1 10 0v3" fill="none" stroke="currentColor" stroke-width="2.8"/><rect x="5" y="10" width="14" height="11" rx="1" fill="currentColor"/><path d="M12 14v3" stroke="#15121C" stroke-width="2.4"/>';
  // tab icons: chunky inked glyphs (64 x 64)
  var INK = ' stroke="#15121C" stroke-width="4" stroke-linejoin="round"';
  var TAB_ICON = {
    inventory: '<path d="M8 15V10H15V15H51V11H56V15H60V31H36L33 37H29L32 57H11L16 31H6V15Z" fill="currentColor"' + INK + '/><path d="M29 31C28 39 31 42 37 41" fill="none" stroke="#15121C" stroke-width="3.6" stroke-linecap="round"/><path d="M11 21H55" stroke="#FFFDF7" stroke-width="3" stroke-linecap="round" opacity=".7"/><path d="M20 37L18 51" stroke="#15121C" stroke-width="2.6" stroke-linecap="round" opacity=".6"/>',
    skills: '<path d="M32 4L40 22L59 24L45 37L49 57L32 47L15 57L19 37L5 24L24 22Z" fill="currentColor"' + INK + '/><path d="M32 18L36 28L45 29L38 35" fill="none" stroke="#FFFDF7" stroke-width="3" stroke-linecap="round" opacity=".7"/>',
    character: '<circle cx="32" cy="21" r="13" fill="currentColor"' + INK + '/><path d="M8 60C8 44 18 36 32 36C46 36 56 44 56 60Z" fill="currentColor"' + INK + '/><path d="M24 15C26 12 29 11 32 11" fill="none" stroke="#FFFDF7" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
  };
  var CHEV = '<path d="M38 6 12 32l26 26h14L26 32 52 6Z" fill="currentColor" stroke="#15121C" stroke-width="4" stroke-linejoin="round"/>';

  // ---------- one-time art: hand-inked edge filter + painterly grunge texture ----------
  var art = false;
  function ensureArt() {
    if (art) return; art = true;
    if (!document.getElementById('fkDefs')) {
      document.body.insertAdjacentHTML('beforeend', '<svg id="fkDefs" width="0" height="0" style="position:absolute;width:0;height:0" aria-hidden="true">' +
        '<filter id="fkInk" x="-1%" y="-1%" width="102%" height="102%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="7" result="n"/>' +
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="3.4" xChannelSelector="R" yChannelSelector="G"/></filter></svg>');
    }
    try {
      var N = 256, cv = document.createElement('canvas'); cv.width = cv.height = N;
      var x = cv.getContext('2d'), seed = 11;
      var rnd = function () { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
      x.lineCap = 'round';
      // soft broad brush strokes in two directions, then ink speckle: reads as painted, not as a pattern
      for (var i = 0; i < 70; i++) {
        var px = rnd() * N, py = rnd() * N, len = 40 + rnd() * 120, a = (rnd() < 0.7 ? -0.5 : 0.9) + (rnd() - 0.5) * 0.5, w = 10 + rnd() * 26;
        var light = rnd() < 0.5;
        x.strokeStyle = light ? 'rgba(200,240,255,' + (0.012 + rnd() * 0.022).toFixed(3) + ')' : 'rgba(4,10,30,' + (0.025 + rnd() * 0.04).toFixed(3) + ')';
        x.lineWidth = w;
        for (var ox = -N; ox <= N; ox += N) for (var oy = -N; oy <= N; oy += N) {
          x.beginPath(); x.moveTo(px + ox, py + oy); x.quadraticCurveTo(px + ox + Math.cos(a) * len * 0.5 + (rnd() - 0.5) * 20, py + oy + Math.sin(a) * len * 0.5 + (rnd() - 0.5) * 20, px + ox + Math.cos(a) * len, py + oy + Math.sin(a) * len); x.stroke();
        }
      }
      for (var k = 0; k < 40; k++) {
        var hx = rnd() * N, hy = rnd() * N, hl = 6 + rnd() * 14, ha = -0.8 + (rnd() - 0.5) * 0.4;
        x.strokeStyle = 'rgba(220,250,255,' + (0.03 + rnd() * 0.04).toFixed(3) + ')'; x.lineWidth = 1 + rnd() * 1.5;
        x.beginPath(); x.moveTo(hx, hy); x.lineTo(hx + Math.cos(ha) * hl, hy + Math.sin(ha) * hl); x.stroke();
      }
      for (var j = 0; j < 1400; j++) { x.fillStyle = rnd() < 0.5 ? 'rgba(255,255,255,.05)' : 'rgba(0,0,20,.1)'; x.fillRect(rnd() * N | 0, rnd() * N | 0, 1 + (rnd() < 0.2), 1); }
      document.documentElement.style.setProperty('--grunge', 'url(' + cv.toDataURL('image/png') + ')');
    } catch (e) { /* the frames work without the texture */ }
  }

  // ---------- open / close ----------
  T.open = function (game, tab) {
    G = game; el = document.getElementById('tabmenu');
    ensureArt();
    if (tab) T.tab = ALIAS[tab] || tab;
    if (!TABS.some(function (t) { return t[0] === T.tab; })) T.tab = 'inventory';
    T.confirmRespec = false;
    if (IB.GearUI && IB.GearUI.reset) IB.GearUI.reset(G);
    if (!T.sel || !IB.SKILL_BY_ID[T.sel]) T.sel = firstSuggested();
    el.hidden = false;
    el.classList.add('opening'); clearTimeout(T._openT); T._openT = setTimeout(function () { if (el) el.classList.remove('opening'); }, 260);
    render(true);
  };
  T.close = function () { if (!el) return; el.hidden = true; el.innerHTML = ''; T._shown = null; };
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
    // panes keep their scroll across re-renders of the same tab only
    var scroll = {}; if (T._shown === T.tab) el.querySelectorAll('.tm-scroll').forEach(function (s) { scroll[s.dataset.pane] = s.scrollTop; });
    T._shown = T.tab;
    var tabs = TABS.map(function (t) {
      var badge = t[0] === 'skills' && pr.points > 0 ? '<span class="tm-badge">' + pr.points + '</span>' : '';
      return '<button class="tm-tab" role="tab" data-tab="' + t[0] + '" data-nav id="tmTab_' + t[0] + '" aria-selected="' + (T.tab === t[0]) + '" aria-controls="tmPanel" aria-label="' + t[1] + '">' + FR +
        svg(TAB_ICON[t[0]], 'tm-tab-ic', '0 0 64 64') + badge + '</button>';
    }).join('');
    var body = T.tab === 'skills' ? skillsPanel(pr) : T.tab === 'character' ? characterPanel(pr) : inventoryPanel();
    var cur = TABS.filter(function (t) { return t[0] === T.tab; })[0][1];
    el.innerHTML = '<div class="tm-scrim" data-act="close"></div>' +
      '<section class="tm-frame" role="dialog" aria-modal="true" aria-label="Field kit">' +
        '<header class="tm-head">' +
          '<div class="tm-id">' + lvBadge(pr.level, 'tm-lv') +
            '<span class="tm-idtxt"><b class="tm-title">' + esc(pr.title) + '</b><span class="tm-sub">' + (pr.highest > 0 ? 'Level ' + pr.highest + ' cleared' : 'Rookie') + '</span></span></div>' +
          '<nav class="tm-tabs" role="tablist" aria-label="Field kit">' + (touch() ? '' : '<kbd class="qe">Q</kbd>') + tabs +
            '<b class="tm-curlbl" aria-hidden="true">' + FR + '<span>' + cur + '</span></b>' + (touch() ? '' : '<kbd class="qe">E</kbd>') + '</nav>' +
          '<div class="tm-meta"><span class="tm-gems" aria-label="Gems"><i class="gem-glyph" aria-hidden="true"></i><b>' + (G.slot.gems || 0) + '</b></span>' +
            '<button class="tm-close" data-act="close" data-nav aria-label="Close and resume">' + FR + svg('<path d="M5 5l14 14M19 5 5 19" stroke="currentColor" stroke-width="3.6" stroke-linecap="round"/>') + (touch() ? '' : '<kbd>Tab</kbd>') + '</button></div>' +
        '</header>' +
        '<div class="tm-body tm-scroll tm-' + T.tab + '" data-pane="body" id="tmPanel" role="tabpanel" aria-labelledby="tmTab_' + T.tab + '">' + body +
          '<button class="tm-chev l" data-step="-1" aria-label="Previous tab">' + svg(CHEV, '', '0 0 64 64') + '</button><button class="tm-chev r" data-step="1" aria-label="Next tab">' + svg(CHEV, '', '0 0 64 64') + '</button>' +
        '</div>' +
        '<footer class="tm-foot">' + footer() + '</footer>' +
      '</section>';
    if (T.tab === 'inventory') mountGear();
    el.querySelectorAll('.tm-scroll').forEach(function (s) { if (scroll[s.dataset.pane]) s.scrollTop = scroll[s.dataset.pane]; });
    if (focusFirst && T.tab === 'skills') { var tr = el.querySelector('.sk-treewrap'), seln = el.querySelector('.sk-node.sel'); if (tr && seln && tr.scrollHeight > tr.clientHeight + 4) seln.scrollIntoView({ block: 'center' }); }
    if (touch()) return;
    var f = keepFocus ? el.querySelector(keepFocus) : null;
    if (!f && focusFirst) f = el.querySelector('.sk-node.sel') || el.querySelector('.lo-slot.sel') || el.querySelector('.tm-body [data-nav]') || el.querySelector('.tm-tab[aria-selected="true"]');
    if (f) f.focus({ preventScroll: !keepFocus });
  }
  function lvBadge(lv, cls) { return '<span class="fk-lv ' + (cls || '') + '">' + svg('<polygon points="30,2 56,17 56,47 30,62 4,47 4,17"/>', 'fk-hex', '0 0 60 64') + '<span><small>LV</small><b>' + lv + '</b></span></span>'; }
  function navKey(a) {
    if (a.dataset.skill) return '[data-skill="' + a.dataset.skill + '"]';
    if (a.dataset.k) return '[data-k="' + a.dataset.k + '"]';
    if (a.dataset.tab) return '[data-tab="' + a.dataset.tab + '"]';
    if (a.dataset.act) return '[data-act="' + a.dataset.act + '"][data-nav]';
    return null;
  }
  function footer() {
    if (touch()) return '';
    var mid = T.tab === 'skills' ? '<span><kbd>Enter</kbd>Select · again to spend</span>' : T.tab === 'inventory' ? '<span><kbd>Enter</kbd>Equip</span><span><kbd>Mouse</kbd>Inspect</span>' : '';
    return '<span><kbd>Q</kbd><kbd>E</kbd>Tabs</span><span><kbd>Arrows</kbd>Move</span>' + mid + '<span><kbd>Tab</kbd><kbd>Esc</kbd>Resume</span>';
  }

  // ---------- skills ----------
  function rankBadge(s, r) {
    return '<span class="sk-rank' + (s.max === 1 ? ' one' : '') + (r >= s.max ? ' full' : '') + '">' + r + '/' + s.max + '</span>';
  }
  function state(s, sk, h) {
    var r = IB.Skills.rank(sk, s.id), cb = IB.Skills.canBuy(sk, h, s.id), open = IB.Skills.tierUnlocked(sk, s.tier);
    var owner = IB.Skills.groupOwner ? IB.Skills.groupOwner(sk, s.group) : null, shut = owner && owner !== s.id;
    return { r: r, cb: cb, open: open && !shut, st: r >= s.max ? 'max' : r > 0 ? 'part' : open && !shut ? 'open' : 'locked' };
  }
  function tierSkills(t) { return IB.SKILLS.filter(function (s) { return s.tier === t; }).sort(function (a, b) { return (a.col || 0) - (b.col || 0); }); }
  function xs(t, n) {
    var L = LAYOUT[t];
    if (L && L.length === n) return L;
    var out = []; for (var i = 0; i < n; i++) out.push(n === 1 ? 0 : -150 + 300 * i / (n - 1));
    return out;
  }
  function skillsPanel(pr) {
    var sk = G.slot.skills || {}, h = pr.highest, rows = IB.SKILL_TIERS.length;
    var nodes = '', lines = '', gates = '', pos = {}, lit = 0;
    IB.SKILL_TIERS.forEach(function (t) {
      var row = rows - t.tier, list = tierSkills(t.tier), X = xs(t.tier, list.length);
      var open = IB.Skills.tierUnlocked(sk, t.tier);
      if (open) lit = Math.max(lit, t.tier);
      list.forEach(function (s, i) {
        pos[s.id] = { x: X[i], y: row * 100 + 50, tier: t.tier };
        nodes += node(s, sk, h, X[i], row, !!t.capstone);
      });
      if (t.capstone && list.length === 2) nodes += '<span class="sk-or" style="--x:0;--r:' + row + '" aria-hidden="true">OR</span>';
      if (!open) {
        var need = t.gate - IB.Skills.spentAbove(sk, t.tier);
        gates += '<span class="sk-gate" style="--r:' + row + '" title="Spend ' + need + ' more point' + (need === 1 ? '' : 's') + ' in the rows below">' + svg(LOCK) + '<b>' + need + '</b></span>';
      }
    });
    // ink branches: every node reaches down to its nearest node in the row below; the trunk roots the bottom row
    function seg(a, b, cls) { lines += '<line class="' + cls + '" x1="' + a.x + '" y1="' + a.y + '" x2="' + b.x + '" y2="' + b.y + '"/>'; }
    var segs = [];
    IB.SKILL_TIERS.forEach(function (t) {
      if (t.tier === 1) { tierSkills(1).forEach(function (s) { segs.push([{ x: 0, y: rows * 100 + 30 }, pos[s.id], s, null]); }); return; }
      var up = tierSkills(t.tier), dn = tierSkills(t.tier - 1), used = {};
      function near(a, list) { var best = null, bd = Infinity; list.forEach(function (b) { var d = Math.abs(pos[b.id].x - pos[a.id].x); if (d < bd - 1) { bd = d; best = b; } }); return best; }
      up.forEach(function (a) { var b = near(a, dn); if (b) { segs.push([pos[b.id], pos[a.id], a, b]); used[b.id] = 1; } });
      dn.forEach(function (b) { if (!used[b.id]) { var a = near(b, up); if (a) segs.push([pos[b.id], pos[a.id], a, b]); } });
    });
    segs.forEach(function (g) {
      var a = g[2], b = g[3], openA = IB.Skills.tierUnlocked(sk, a.tier), ownA = IB.Skills.rank(sk, a.id) > 0, ownB = !b || IB.Skills.rank(sk, b.id) > 0;
      seg(g[0], g[1], 'ink'); seg(g[0], g[1], ownA && ownB ? 'own' : openA ? 'lit' : 'off');
    });
    var spent = IB.Skills.spent(sk);
    var tree = '<div class="sk-treewrap tm-scroll" data-pane="tree"><div class="sk-tree" style="--rows:' + rows + ';--lit:' + lit + '">' +
      '<i class="sk-litfill" aria-hidden="true"></i>' +
      '<svg class="sk-branches" viewBox="-220 0 440 ' + (rows * 100) + '" preserveAspectRatio="none" aria-hidden="true">' + lines + '</svg>' +
      gates + nodes + '</div></div>';
    return '<div class="sk-left">' + detail(pr, sk, h) + plate(pr, sk, h) + '</div>' +
      '<section class="ep sk-treebox" aria-label="Skill tree">' + FR + tree +
        '<div class="sk-treefoot"><b>Scrap Tree</b><span class="sk-spent" title="Points spent in the tree">' + spent + '</span></div></section>' +
      bonusPanel(sk);
  }
  function node(s, sk, h, x, row, cap) {
    var q = state(s, sk, h);
    var cls = 'sk-node tile st-' + q.st + (cap ? ' cap' : '') + (q.cb.ok ? ' buyable' : '') + (T.sel === s.id ? ' sel' : '');
    var label = s.name + ', ' + (s.max > 1 ? 'rank ' + q.r + ' of ' + s.max : q.r ? 'owned' : 'not owned') + (q.cb.ok ? ', can spend' : '');
    return '<button class="' + cls + '" data-skill="' + s.id + '" data-nav style="--x:' + x + ';--r:' + row + '" aria-pressed="' + (T.sel === s.id) + '" aria-label="' + esc(label) + '">' + FR +
      '<span class="sk-ic">' + skIcon(s.icon) + '</span>' + rankBadge(s, q.r) + '</button>';
  }
  function rankLines(s, r) {
    if (IB.Skills.rankText) { try { return IB.Skills.rankText(s.id, r); } catch (e) { /* fall through */ } }
    var f = function (v) { return s.stat + ' +' + v + (s.unit || ''); };
    return s.max > 1 ? { now: r ? f(s.ranks[r - 1]) : null, next: r < s.max ? f(s.ranks[r]) : null } : { now: r ? 'Owned' : null, next: r ? null : 'Unlock' };
  }
  function detail(pr, sk, h) {
    var s = IB.SKILL_BY_ID[T.sel], q = state(s, sk, h), r = q.r, cb = q.cb, tx = rankLines(s, r);
    var tier = IB.SKILL_TIERS[s.tier - 1] || {};
    var kind = s.kind === 'capstone' ? 'Endgame · pick one' : (tier.name || 'Tier ' + ROMAN[s.tier]) + (s.kind === 'special' ? ' · special' : '');
    var lines = s.max > 1 ? (r > 0 && tx.now ? '<p><span>Current:</span> ' + esc(tx.now) + '</p>' : '') + (tx.next ? '<p class="nx"><span>Next level:</span> ' + esc(tx.next) + '</p>' : '<p class="mx">Maxed out</p>')
      : '<p class="' + (r ? 'mx' : 'nx') + '"><span>' + (r ? 'Owned:' : 'Unlocks:') + '</span> ' + esc(s.stat) + '</p>';
    var ranks = s.max > 1 ? '<div class="sk-ranks">' + s.ranks.map(function (v, i) { return '<span class="' + (i < r ? 'on' : i === r ? 'next' : '') + '">+' + v + (s.unit || '') + '</span>'; }).join('') + '</div>' : '';
    var owner = cb.owner && IB.SKILL_BY_ID[cb.owner];
    var why = { max: '', tier: 'Spend ' + (cb.need || 0) + ' more point' + (cb.need === 1 ? '' : 's') + ' in the rows below', exclusive: 'You picked ' + (owner ? owner.name : 'the other one') + '. Respec to switch.',
      points: pr.points > 0 ? 'Needs ' + s.cost + ' points' : (pr.earned >= IB.Skills.totalPoints() ? 'Every point is spent' : 'Clear the next level for a point') }[cb.reason] || '';
    var buyLabel = cb.ok ? 'Spend ' + s.cost + ' point' + (s.cost > 1 ? 's' : '') : (cb.reason === 'max' ? (s.max > 1 ? 'Maxed' : 'Owned') : 'Locked');
    return '<div class="ep hsel sk-card st-' + q.st + '" aria-live="polite">' + FR +
        '<div class="sk-dhead"><span class="sk-dic tile st-' + q.st + '">' + FR + skIcon(s.icon) + '</span><span class="sk-dtxt"><b>' + esc(s.name) + '</b><small>' + esc(kind) + '</small></span>' + rankBadge(s, r) + '</div>' +
        '<p class="sk-text">' + esc(s.text) + '</p><div class="sk-lines">' + lines + '</div>' + ranks +
        (why ? '<div class="sk-why">' + svg(LOCK) + esc(why) + '</div>' : '') +
        '<button class="btn primary sk-buy" data-act="buy" data-nav' + (cb.ok ? '' : ' disabled aria-disabled="true"') + '><span class="btn-l">' + buyLabel + '</span></button>' +
      '</div>';
  }
  function plate(pr, sk, h) {
    var cost = IB.Skills.respecCost(h), spent = IB.Skills.spent(sk), canRespec = spent > 0 && (G.slot.gems || 0) >= cost;
    return '<div class="ep sk-plate">' + FR +
      '<div class="sk-who">' + lvBadge(pr.level) + '<b class="sk-whoname">' + esc(pr.title) + '</b></div>' +
      '<div class="sk-points"><span>Skill points</span><b class="' + (pr.points > 0 ? 'has' : '') + '">' + pr.points + '</b></div>' +
      '<button class="btn danger sk-rbtn' + (T.confirmRespec ? ' confirm' : '') + '" data-act="respec" data-nav' + (canRespec ? '' : ' disabled aria-disabled="true"') + '><span class="btn-l">' + (T.confirmRespec ? 'Confirm reset' : 'Respec') + '</span><span class="hint"><i class="gem-glyph sm" aria-hidden="true"></i>' + cost + '</span></button>' +
      '</div>';
  }
  function bonusPanel(sk) {
    var rows = IB.SKILLS.filter(function (s) { return IB.Skills.rank(sk, s.id) > 0; }).map(function (s) {
      var r = IB.Skills.rank(sk, s.id), v = s.max > 1 ? '+' + s.ranks[Math.min(r, s.max) - 1] + (s.unit || '') : 'On';
      return '<li>' + skIcon(s.icon, 'skic sm') + '<span><b>' + esc(s.name) + '</b><small>' + esc(s.stat) + '</small></span><em>' + esc(v) + '</em></li>';
    }).join('');
    var total = 0; IB.SKILLS.forEach(function (s) { total += s.max * s.cost; });
    return '<aside class="ep sk-bonus" aria-label="Active skills">' + FR + '<h3 class="ep-h sm">Active</h3>' +
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
  // reads the skill table and the player directly (no assumption about IB.Skills.effects field names)
  function characterPanel(pr) {
    var sk = G.slot.skills || {}, g = IB.Gear && IB.Gear.gear(G), p = G.player || {};
    var cap = IB.PLAYER_LEVEL_CAP, next = pr.level < cap ? IB.Skills.rankTitle(pr.level + 1) : null;
    var lvPct = Math.round(Math.min(1, (pr.level - 1) / (cap - 1)) * 100), ptPct = Math.round(pr.earned / IB.Skills.totalPoints() * 100);
    var sh = g && g.shield ? IB.Loot.find(g, g.shield) : null;
    function row(ic, k, v, hl) { return '<li' + (hl ? ' class="hl"' : '') + '>' + skIcon(ic, 'skic sm') + '<span>' + esc(k) + '</span><b>' + esc(v) + '</b></li>'; }
    var vs = g ? IB.Loot.worn(g, 'armor') : null, va = IB.Loot.armorOf(vs), shp = sh && IB.Loot.perkLine(sh);
    var stats = row('heart', 'Health', Math.round(p.maxHp || 100), false) +
      row('bolt', 'Shield', sh ? sh.stats.capacity + ' · ' + sh.stats.rate + '/s' + (shp ? ' · ' + shp.name : '') : 'None', !!sh) +
      row('armor', 'Armour', vs ? '-' + Math.round(va.dr * 100) + '% · +' + va.hp + ' hp' : 'None', !!vs);
    IB.SKILLS.forEach(function (s) {
      var r = IB.Skills.rank(sk, s.id);
      if (s.max > 1) stats += row(s.icon, s.stat, r ? '+' + s.ranks[Math.min(r, s.max) - 1] + (s.unit || '') : '—', r > 0);
    });
    var perks = IB.SKILLS.filter(function (s) { return s.max === 1 && IB.Skills.rank(sk, s.id) > 0; });
    var st = G.slot.stats || {}, run = G.run || {}, mmss = IB.HUD && IB.HUD.mmss ? IB.HUD.mmss : function (t) { return Math.round(t) + ' s'; };
    var ars = (G.slot.arsenal || []).length, all = Object.keys(IB.WEAPONS).filter(function (w) { return !IB.Weapons.playable || IB.Weapons.playable(w); }).length;
    function rec(k, v) { return '<li><span>' + k + '</span><b>' + v + '</b></li>'; }
    return '<div class="ep hsel ch-id">' + FR +
        lvBadge(pr.level, 'ch-badge') +
        '<b class="ch-title">' + esc(pr.title) + '</b><span class="ch-sub">Scrapper · LV ' + pr.level + ' of ' + cap + '</span>' +
        '<div class="ch-bar"><span>Rank</span><i><i style="width:' + lvPct + '%"></i></i><b>' + pr.level + '/' + cap + '</b></div>' +
        '<div class="ch-bar"><span>Points</span><i><i style="width:' + ptPct + '%"></i></i><b>' + pr.earned + '/' + IB.Skills.totalPoints() + '</b></div>' +
        '<p class="ch-next">' + (next ? 'Next rank: <b>' + esc(next) + '</b>' : 'Top rank reached.') + '</p>' +
        (perks.length ? '<div class="ch-perks">' + perks.map(function (s) { return '<span>' + skIcon(s.icon, 'skic sm') + esc(s.name) + '</span>'; }).join('') + '</div>' : '') +
      '</div>' +
      '<section class="ep ch-mid" aria-label="Stats">' + FR + '<h3 class="ep-h">' + IB.Menus.glyph('emblem') + 'Combat stats</h3><div class="tm-scroll" data-pane="stats"><ul class="ch-stats">' + stats + '</ul></div></section>' +
      '<aside class="ep ch-rec" aria-label="Service record">' + FR + '<h3 class="ep-h sm">Record</h3><div class="tm-scroll" data-pane="rec">' +
        '<h4 class="inv-cat"><span>This level</span></h4><ul class="ch-list">' + rec('Level', G.plan ? G.plan.level + ' · ' + esc(G.plan.name) : '—') + rec('Time', mmss(run.time || 0)) + rec('Robots crushed', run.kills || 0) + rec('Retries left', Math.max(0, run.retries == null ? 0 : run.retries)) + '</ul>' +
        '<h4 class="inv-cat"><span>Career</span></h4><ul class="ch-list">' + rec('Levels cleared', pr.highest) + rec('Robots crushed', (st.kills || 0) + (run.kills || 0)) + rec('Deaths', (st.deaths || 0) + (run.deaths || 0)) +
          rec('Time played', mmss((st.time || 0) + (run.time || 0))) + rec('Guns owned', ars + '/' + all) + rec('Gear found', g ? g.found || 0 : 0) + rec('Gems', G.slot.gems || 0) + '</ul>' +
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
  try { ensureArt(); } catch (e) { /* drawn again on first open */ art = false; }
  window.addEventListener('keydown', onKey, true);
  document.addEventListener('click', function (e) { if (T.isOpen() && el.contains(e.target)) onClick(e); });
})(window.IB = window.IB || {});
