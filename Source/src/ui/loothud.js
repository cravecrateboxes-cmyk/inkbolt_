/* INKBOLT loot HUD: the shield bar above health and the loot card (name, rarity, level, key stats) shown when a
   drop is picked up. DOM is created on first use inside #hud; per-frame calls only write on change. */
(function (IB) {
  'use strict';
  var LH = IB.LootHUD = {};
  var el = null, last = { q: -1, max: -1, on: null }, cardT = 0, flashT = 0;

  var ICON = {
    shield: '<svg viewBox="-20 -20 40 40" aria-hidden="true"><polygon points="0,-17 14.7,-8.5 14.7,8.5 0,17 -14.7,8.5 -14.7,-8.5" fill="currentColor" stroke="#15121C" stroke-width="3" stroke-linejoin="round"/><path d="M2-11-6 2h5l-2 9 9-13H1z" fill="#15121C"/></svg>',
    grip: '<svg viewBox="-20 -20 40 40" aria-hidden="true"><path d="M-12-15h24v7H5l1 4v19l-3 3h-8l-2-3V-4l1-4h-6z" fill="currentColor" stroke="#15121C" stroke-width="3" stroke-linejoin="round"/><path d="M-3 0h7M-3 5h7M-3 10h7" stroke="#15121C" stroke-width="2.5"/></svg>',
    scope: '<svg viewBox="-20 -20 40 40" aria-hidden="true"><path d="M-17-8h8l3 3h12l3-4h8v14h-8l-3-4H-6l-3 3h-8z" fill="currentColor" stroke="#15121C" stroke-width="3" stroke-linejoin="round"/><path d="M-4 5v6h8V5" fill="none" stroke="#15121C" stroke-width="3"/><circle cx="14" cy="-2" r="2.5" fill="#15121C"/></svg>',
    acid: '<svg viewBox="-20 -20 40 40" aria-hidden="true"><path d="M-17-6h6v-3h22l4 3v12l-4 3h-22v-3h-6z" fill="currentColor" stroke="#15121C" stroke-width="3" stroke-linejoin="round"/><path d="M-6-9v18M6-9v18" stroke="#15121C" stroke-width="2.5"/><path d="M0-17c3 4 4 6 4 8a4 4 0 0 1-8 0c0-2 1-4 4-8z" fill="#7BE34A" stroke="#15121C" stroke-width="2.5"/></svg>'
  };
  LH.icon = function (type) { return ICON[type] || ICON.grip; };
  var TYPE_NAME = { shield: 'Shield cell', grip: 'Grip', scope: 'Scope', acid: 'Acid muzzle' };
  LH.typeName = function (t) { return TYPE_NAME[t] || 'Gear'; };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  LH.esc = esc;

  function ensure() {
    if (el) return el;
    var hud = document.getElementById('hud'); if (!hud) return null;
    var bl = hud.querySelector('.hud-bl'), health = document.getElementById('health');
    var bar = document.createElement('div');
    bar.className = 'plate ink shieldbar'; bar.id = 'shieldBar'; bar.hidden = true;
    bar.innerHTML = '<svg class="sh-glyph" viewBox="-12 -12 24 24" aria-hidden="true"><polygon points="0,-10.5 9.1,-5.25 9.1,5.25 0,10.5 -9.1,5.25 -9.1,-5.25"/><path d="M1.4-6.6-3.6 1.2h3.1l-1.2 5.4 5.4-7.8H.6z"/></svg>' +
      '<div class="sh-bar"><i class="sh-fill" id="shFill"></i><i class="sh-ticks"></i></div><b id="shNum">0</b>';
    if (bl && health) bl.insertBefore(bar, health); else hud.appendChild(bar);
    var card = document.createElement('div');
    card.className = 'lootcard'; card.id = 'lootCard'; card.hidden = true;
    card.innerHTML = '<div class="plate ink loot-card" id="lootCardIn"><span class="loot-icon" id="lootIcon"></span><span class="loot-txt">' +
      '<span class="loot-rar" id="lootRar"></span><b class="loot-name" id="lootName"></b><span class="loot-stats" id="lootStats"></span><span class="loot-note" id="lootNote"></span></span></div>';
    hud.appendChild(card);
    var sv = document.createElement('div');
    sv.className = 'scopeview'; sv.id = 'scopeView'; sv.style.opacity = '0'; sv.style.visibility = 'hidden';
    var posts = '', i;
    for (i = 0; i < 4; i++) {
      var r = i * 90;
      posts += '<rect x="-2.2" y="-84" width="4.4" height="64" transform="rotate(' + r + ')"/>';
      posts += '<rect x="-0.6" y="-20" width="1.2" height="16.5" transform="rotate(' + r + ')"/>';
    }
    sv.innerHTML = '<svg viewBox="-100 -100 200 200" preserveAspectRatio="xMidYMid meet" aria-hidden="true">' +
      '<defs><radialGradient id="svVig"><stop offset=".62" stop-color="#15121C" stop-opacity="0"/><stop offset="1" stop-color="#15121C" stop-opacity=".55"/></radialGradient>' +
      '<pattern id="svDots" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r=".9" fill="#15121C"/></pattern>' +
      '<radialGradient id="svDotMask"><stop offset=".78" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></radialGradient>' +
      '<mask id="svM"><circle r="84" fill="url(#svDotMask)"/></mask></defs>' +
      '<path fill="#15121C" fill-rule="evenodd" d="M-3000-3000H3000V3000H-3000Z M0-84A84 84 0 1 0 0 84A84 84 0 1 0 0-84Z"/>' +
      '<circle r="84" fill="rgba(134,234,242,.07)"/><circle r="84" fill="url(#svVig)"/><circle r="84" fill="url(#svDots)" mask="url(#svM)"/>' +
      '<g fill="#15121C">' + posts + '</g><circle r="1.9" fill="#FFB21E" stroke="#15121C" stroke-width="1"/>' +
      '<circle r="88" fill="none" stroke="#15121C" stroke-width="9"/><circle r="87.5" fill="none" stroke="#5A586D" stroke-width="4"/>' +
      '<path d="M-62-52A81 81 0 0 1-24-77" fill="none" stroke="#FFFDF7" stroke-opacity=".45" stroke-width="3.2" stroke-linecap="round"/>' +
      '<path d="M-70-34A81 81 0 0 1-66-44" fill="none" stroke="#FFFDF7" stroke-opacity=".45" stroke-width="3.2" stroke-linecap="round"/></svg>';
    hud.insertBefore(sv, hud.firstChild);
    el = { sv: sv, svK: -1, bar: bar, fill: bar.querySelector('#shFill'), num: bar.querySelector('#shNum'), card: card, cardIn: card.querySelector('#lootCardIn'),
      icon: card.querySelector('#lootIcon'), rar: card.querySelector('#lootRar'), name: card.querySelector('#lootName'), stats: card.querySelector('#lootStats'), note: card.querySelector('#lootNote') };
    return el;
  }
  LH.ensure = ensure;

  /* st: player shield state {cur, max, charging} or null (no shield equipped: the bar hides) */
  LH.shield = function (st) {
    if (!ensure()) return;
    var on = !!st;
    if (on !== last.on) { last.on = on; el.bar.hidden = !on; last.q = -1; var hud = document.getElementById('hud'); if (hud) hud.classList.toggle('has-shield', on); }
    if (!on) return;
    var q = Math.max(0, Math.ceil(st.cur)), f = Math.round(st.cur / st.max * 400);
    if (q !== last.q || st.max !== last.max || f !== last.f) {
      last.q = q; last.max = st.max; last.f = f;
      el.num.textContent = q;
      el.fill.style.width = (f / 4).toFixed(2) + '%';
      el.bar.style.setProperty('--ticks', Math.max(2, Math.round(st.max / 10)));
      el.bar.classList.toggle('empty', st.cur <= 0);
    }
    var ch = !!st.charging;
    if (ch !== last.ch) { last.ch = ch; el.bar.classList.toggle('charging', ch); }
  };
  /* mounted-scope view, 0..1 (driven by the aim blend) */
  LH.scope = function (k) {
    if (!ensure()) return;
    var q = Math.round(k * 50) / 50;
    if (q === el.svK) return;
    el.svK = q;
    el.sv.style.visibility = q > 0 ? 'visible' : 'hidden';
    el.sv.style.opacity = q.toFixed(2);
    el.sv.style.transform = 'scale(' + (1.12 - 0.12 * q).toFixed(3) + ')';
    var hud = document.getElementById('hud'); if (hud) hud.classList.toggle('scoped', q > 0.5);
  };
  LH.shieldHit = function (broke) {
    if (!ensure()) return;
    var b = el.bar;
    b.classList.remove('hit', 'broke'); void b.offsetWidth; b.classList.add(broke ? 'broke' : 'hit');
    flashT = broke ? 0.5 : 0.18;
    var hurt = document.getElementById('hurt');
    if (hurt) { hurt.classList.remove('shielded'); void hurt.offsetWidth; hurt.classList.add('shielded'); }
  };
  LH.shieldEvent = function (ev) {
    if (!ensure()) return;
    if (ev === 'full') { el.bar.classList.remove('full'); void el.bar.offsetWidth; el.bar.classList.add('full'); }
  };

  /* loot card: item from IB.Loot.makeItem; note: second line ('Shield equipped', 'In your bag'...) */
  LH.loot = function (item, note) {
    if (!ensure()) return;
    var rc = IB.LOOT.rarityById[item.rarity];
    el.cardIn.style.setProperty('--rar', rc.color);
    el.card.className = 'lootcard ' + item.rarity;
    el.icon.innerHTML = ICON[item.type] || '';
    el.rar.textContent = rc.name + ' · Lv ' + item.level + ' · ' + LH.typeName(item.type);
    el.name.textContent = String(item.name).toUpperCase();
    el.stats.innerHTML = IB.Loot.statLines(item).map(function (l) { return '<i>' + esc(l.k) + ' <b>' + esc(l.v) + '</b></i>'; }).join('');
    el.note.textContent = note || '';
    el.card.hidden = false; el.card.classList.remove('on', 'out'); void el.card.offsetWidth; el.card.classList.add('on');
    var hud = document.getElementById('hud'); if (hud) hud.classList.add('looting');
    cardT = 3.6;
  };
  LH.reset = function () {
    if (!el) return;
    el.card.hidden = true; cardT = 0; LH.scope(0);
    var hud = document.getElementById('hud'); if (hud) hud.classList.remove('looting');
    last = { q: -1, max: -1, on: null };
  };
  LH.tick = function (dt) {
    if (!el) return;
    if (cardT > 0) {
      cardT -= dt;
      if (cardT <= 0.3 && !el.card.classList.contains('out')) el.card.classList.add('out');
      if (cardT <= 0) { el.card.hidden = true; var hud = document.getElementById('hud'); if (hud) hud.classList.remove('looting'); }
    }
    if (flashT > 0) { flashT -= dt; if (flashT <= 0) el.bar.classList.remove('hit', 'broke'); }
  };
})(window.IB = window.IB || {});
