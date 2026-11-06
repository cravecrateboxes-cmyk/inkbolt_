/* INKBOLT menus: title, settings (+ reset confirm), pause, results, fail, level intro, rotate hint, loading.
   Look: "holo ink" — translucent teal panels with a bright bevelled rim and a 3 px ink outline, chamfered corners,
   scanlines + hex texture, condensed headline type (Archivo wdth axis), the selected entry in yellow with a bolt
   emblem. Lists are left-aligned so the live 3D scene stays visible on the right.
   One primary button per screen; keyboard (Tab/arrows/Enter/Esc, Q/E for settings categories) and mouse/touch. */
(function (IB) {
  'use strict';
  var M = IB.Menus = { cur: null, stack: [] };
  var ov;

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  M.esc = esc;
  function touch() { return !!(IB.Input && IB.Input.touch); }

  // ink splat outline: blobby core with a few long spikes (same family as the wall decal)
  function splatPath() {
    var pts = [], n = 18, i;
    for (i = 0; i < n; i++) {
      var a = i / n * Math.PI * 2, spike = (i % 5 === 1 || i % 7 === 3), r = spike ? 21 + (i % 3) * 2 : 11 + ((i * 7) % 5);
      pts.push([Math.cos(a) * r, Math.sin(a) * r]);
    }
    var d = '', f = function (v) { return v.toFixed(1); };
    for (i = 0; i < n; i++) {
      var p = pts[i], q = pts[(i + 1) % n], mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
      if (i === 0) d += 'M' + f((pts[n - 1][0] + p[0]) / 2) + ' ' + f((pts[n - 1][1] + p[1]) / 2);
      d += 'Q' + f(p[0]) + ' ' + f(p[1]) + ' ' + f(mx) + ' ' + f(my);
    }
    return d + 'Z';
  }
  var SPLAT = splatPath();
  M.SPLAT = SPLAT;
  M.boltSvg = function () {
    return '<svg class="bolt" viewBox="-50 -50 100 100" aria-hidden="true">' +
      '<polygon points="44,0 22,38 -22,38 -44,0 -22,-38 22,-38" fill="#FFFDF7" stroke="#15121C" stroke-width="6"/>' +
      '<circle r="26" fill="none" stroke="#15121C" stroke-width="3" opacity=".35"/>' +
      '<path d="' + SPLAT + '" fill="#15121C" transform="scale(1.55) rotate(18)"/>' +
      '<circle r="10" fill="#15121C"/><circle r="10" fill="none" stroke="#FFFDF7" stroke-width="2.4" stroke-dasharray="20 60" transform="rotate(200)"/>' +
      '</svg>';
  };
  M.logo = function () {
    return '<div class="plate ink logo" role="img" aria-label="INKBOLT">' +
      '<span class="logo-word" aria-hidden="true">INKB' + M.boltSvg() + 'LT</span><i class="logo-tab" aria-hidden="true"></i></div>';
  };

  // ---------- small glyphs (24 x 24, currentColor) shared by the menus and the field kit ----------
  var G24 = {
    emblem: '<polygon points="12,1.5 21.5,7 21.5,17 12,22.5 2.5,17 2.5,7" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M13.6 4.6 7.4 13.2h4l-1.2 6.2 6.4-8.8h-4z" fill="currentColor"/>',
    clock: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="3"/><path d="M12 6.5V12l4 2.5" fill="none" stroke="currentColor" stroke-width="2.6"/>',
    bot: '<path d="M6 7h12v10H6z" fill="currentColor"/><path d="M11 3h2v4h-2zM3 10h3v4H3zM18 10h3v4h-3zM7 17h3v4H7zM14 17h3v4h-3z" fill="currentColor"/><path d="M8.5 11h7" stroke="var(--ink)" stroke-width="2.4"/>',
    core: '<circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="12" cy="12" r="4.5" fill="currentColor"/>',
    skull: '<path d="M12 2a8.5 8.5 0 0 0-8.5 8.5c0 3 1.5 5 3.5 6V21h10v-4.5c2-1 3.5-3 3.5-6A8.5 8.5 0 0 0 12 2z" fill="currentColor"/><circle cx="8.6" cy="11" r="2.1" fill="var(--ink)"/><circle cx="15.4" cy="11" r="2.1" fill="var(--ink)"/><path d="M10 18v3M14 18v3" stroke="var(--ink)" stroke-width="1.6"/>',
    gem: '<path d="M12 2 21 9.5 12 22 3 9.5z" fill="currentColor"/><path d="M3 9.5h18M12 2 8 9.5 12 22l4-12.5z" fill="none" stroke="var(--ink)" stroke-width="1.4" opacity=".5"/>',
    star: '<path d="M12 1l3 7h7l-5.6 4.4 2.1 7.6L12 15.6 5.5 20l2.1-7.6L2 8h7z" fill="currentColor"/>',
    heart: '<path d="M12 21 3 12a5 5 0 0 1 9-6 5 5 0 0 1 9 6z" fill="currentColor"/>',
    shield: '<path d="M12 2 21 6v6c0 5-4 8.5-9 10-5-1.5-9-5-9-10V6z" fill="currentColor"/>',
    phone: '<rect x="7" y="2" width="10" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M10 18.5h4" stroke="currentColor" stroke-width="2"/>',
    rotate: '<path d="M20 12a8 8 0 0 1-14 5.3M4 12a8 8 0 0 1 14-5.3" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M19 2v6h-6zM5 22v-6h6z" fill="currentColor"/>',
    warn: '<path d="M12 2 23 21H1z" fill="currentColor"/><path d="M12 9v5M12 16.5v2" stroke="var(--ink)" stroke-width="2.6"/>'
  };
  M.glyph = function (k, cls) { return '<svg class="' + (cls || 'g24') + '" viewBox="0 0 24 24" aria-hidden="true">' + (G24[k] || G24.emblem) + '</svg>'; };
  M.G24 = G24;
  // "[Enter] Select  [Esc] Back" key hints row (keyboard only)
  M.keyHints = function (list) {
    if (touch()) return '';
    return '<div class="keyhints" aria-hidden="true">' + list.map(function (h) { return '<span><kbd>' + h[0] + '</kbd>' + h[1] + '</span>'; }).join('') + '</div>';
  };
  M.crumb = function (parts) {
    return '<div class="crumb">' + parts.map(function (p, i) { return i === parts.length - 1 ? '<b>' + esc(p) + '</b>' : '<span>' + esc(p) + '</span><i>/</i>'; }).join('') + '</div>';
  };

  M.init = function () {
    ov = document.getElementById('overlay');
    window.addEventListener('keydown', function (e) { if (e.key === 'Tab' || e.key.indexOf('Arrow') === 0) document.body.classList.add('kbd'); });
    window.addEventListener('pointerdown', function () { document.body.classList.remove('kbd'); });
    ov.addEventListener('click', function (e) {
      var b = e.target.closest('[data-act]'); if (!b) return;
      IB.Audio && IB.Audio.play(b.dataset.act === 'back' ? 'uiBack' : 'ui');
      M.act(b.dataset.act, b);
    });
    ov.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        var list = Array.prototype.slice.call(ov.querySelectorAll('.btn, .set-cat[aria-selected="true"], .switch, .range, .seg button')).filter(function (b) { return b.offsetParent !== null && !b.disabled; });
        var i = list.indexOf(document.activeElement);
        // inside a segmented control, up/down leaves the whole group
        if (i >= 0 && list[i].closest('.seg')) {
          var grp = list[i].closest('.seg'), step = e.key === 'ArrowDown' ? 1 : -1;
          while (list[i] && list[i].closest('.seg') === grp) i += step;
          i -= step;
        }
        e.preventDefault();
        var n = list[(i + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length]; if (n) n.focus();
      } else if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && document.activeElement && document.activeElement.classList.contains('set-cat')) {
        e.preventDefault(); M.settingsCat(e.key === 'ArrowRight' ? 1 : -1, true);
      } else if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && document.activeElement && document.activeElement.closest('.seg')) {
        var bs = Array.prototype.slice.call(document.activeElement.closest('.seg').querySelectorAll('button')), j = bs.indexOf(document.activeElement);
        var nb = bs[j + (e.key === 'ArrowRight' ? 1 : -1)]; if (nb) { e.preventDefault(); nb.focus(); }
      }
    });
    window.addEventListener('keydown', function (e) {
      if (ov.hidden) return;
      if (M.cur === 'settings' && (e.key === 'q' || e.key === 'Q' || e.key === 'e' || e.key === 'E')) { e.preventDefault(); M.settingsCat(e.key === 'e' || e.key === 'E' ? 1 : -1, true); return; }
      if (e.key !== 'Escape') return;
      var back = ov.querySelector('[data-esc]');
      if (back) { e.preventDefault(); M.act(back.dataset.act, back); }
    });
    // the description line under the settings list follows focus and hover
    function desc(e) {
      var row = e.target.closest && e.target.closest('[data-desc]'), d = document.getElementById('setDesc');
      if (!row || !d) return;
      d.textContent = row.dataset.desc;
      ov.querySelectorAll('.setting.cur').forEach(function (r) { if (r !== row) r.classList.remove('cur'); });
      row.classList.add('cur');
    }
    ov.addEventListener('focusin', desc);
    ov.addEventListener('pointerover', desc);
  };
  M.handlers = {};
  M.on = function (act, fn) { M.handlers[act] = fn; };
  M.act = function (act, el) { var f = M.handlers[act]; if (f) f(el); };

  M.hide = function () { ov.hidden = true; ov.innerHTML = ''; ov.className = 'overlay'; M.cur = null; };
  function show(name, html, dim, focusSel) {
    M.cur = name; ov.hidden = false; ov.className = 'overlay ov-' + name + (dim ? ' dim' : '');
    ov.innerHTML = html;
    var f = ov.querySelector(focusSel || '.btn.primary') || ov.querySelector('.btn');
    if (f && !touch()) f.focus({ preventScroll: true });
    ov.scrollTop = 0;
  }
  M.isOpen = function () { return !ov.hidden; };

  function btn(act, label, cls, hint, extra) {
    return '<button class="btn ' + (cls || '') + '" data-act="' + act + '"' + (extra || '') + '><span class="btn-l">' + label + '</span>' + (hint ? '<span class="hint">' + hint + '</span>' : '') + '</button>';
  }
  // big condensed main-menu entry: emblem (shown when selected) + label + optional sub line
  function entry(act, label, cls, sub, extra) {
    return '<button class="btn mm-item ' + (cls || '') + '" data-act="' + act + '"' + (extra || '') + '>' + M.glyph('emblem', 'mm-emb') +
      '<span class="btn-l">' + label + '</span>' + (sub ? '<span class="hint">' + sub + '</span>' : '') + '</button>';
  }
  M.btn = btn;

  var TIPS = [
    ['Hey, scrapper!', 'Shoot the glowing core on a robot\'s back for bonus damage. The trash bots hate that.'],
    ['Pro tip', 'Hit Tab mid-fight to open the field kit: swap guns, fit attachments and spend skill points. Time stops while it is open.'],
    ['Listen up', 'Shield cells soak damage before your health and recharge after a short break. Duck behind a crate!'],
    ['Did you know?', 'About one robot in twenty drops loot. Follow the coloured beam: blue is rare, purple is epic.'],
    ['Word of advice', 'Clear level 10 to unlock a third carry slot. Three guns, zero excuses.']
  ];

  // ---------- title ----------
  M.title = function (d) {
    var s = d.slot, sub = s ? 'Level ' + s.level + ' · ' + esc(d.levelName) : '';
    var items = (s ? entry('continue', 'Continue', 'primary', sub) : '') +
      entry('new', s ? 'New game' : 'Play', s ? '' : 'primary', s ? null : 'Toy Town') +
      entry('settings', 'Settings');
    var card = '';
    if (s) {
      var lv = IB.Skills ? IB.Skills.playerLevel(s.highest || 0) : 1, title = IB.Skills ? IB.Skills.rankTitle(lv) : '';
      var pct = Math.round(Math.min(1, (s.highest || 0) / 20) * 100);
      var when = s.saved && IB.Saves ? IB.Saves.ago(Date.now() - s.saved) : '';
      card = '<aside class="holo save-card" aria-label="Save slot ' + s.id + '">' +
        '<div class="sc-head">' + M.glyph('emblem', 'g24 sc-ic') + '<b>Save slot ' + s.id + '</b><span>' + esc(when) + '</span></div>' +
        '<div class="sc-row sel"><span class="lvb"><small>LV</small>' + lv + '</span><b class="sc-name">' + esc(title) + '</b><span class="sc-gems">' + M.glyph('gem') + (s.gems || 0) + '</span></div>' +
        '<div class="sc-row"><span>Next up</span><b>Level ' + s.level + ' · ' + esc(d.levelName) + '</b></div>' +
        '<div class="sc-row"><span>Campaign</span><i class="sc-bar"><i style="width:' + pct + '%"></i></i><b>' + (s.highest || 0) + '/20</b></div>' +
        '</aside>';
    }
    var tip = TIPS[(Math.random() * TIPS.length) | 0];
    var html = '<div class="screen title-screen">' +
      '<div class="mm-col">' + M.logo() + '<div class="tagline">Clear the town. Crush the trash bots.</div>' +
        M.crumb(['Main menu']) + '<nav class="menu mm-list" aria-label="Main menu">' + items + '</nav></div>' +
      card +
      '<div class="tipbox" role="note"><b>' + tip[0] + '</b><p>' + tip[1] + '</p></div>' +
      M.keyHints([['Enter', 'Select'], ['↑↓', 'Move']]) +
      '</div>';
    show('title', html, false);
  };

  // ---------- settings ----------
  // categories: Video / Audio / Controls / Gameplay; each row has a description shown on the line under the list
  var CATS = [['video', 'Video'], ['audio', 'Audio'], ['controls', 'Controls'], ['gameplay', 'Gameplay']];
  M._cat = 'video';
  M.settings = function (s, from) {
    M._settingsS = s;
    if (from !== undefined && from !== 'settings') M._settingsFrom = from;
    renderSettings();
  };
  M.settingsCat = function (d, focus) {
    var i = CATS.map(function (c) { return c[0]; }).indexOf(M._cat);
    M._cat = CATS[(i + d + CATS.length) % CATS.length][0];
    IB.Audio && IB.Audio.play('ui');
    renderSettings(focus ? '.set-cat[aria-selected="true"]' : null);
  };
  function renderSettings(focusSel) {
    var s = M._settingsS, from = M._settingsFrom;
    function row(key, label, desc, ctl, cls) {
      return '<div class="setting' + (cls ? ' ' + cls : '') + '" data-desc="' + esc(desc) + '">' + ctl(key, label) + '</div>';
    }
    function sw(key, label, desc) {
      return row(key, label, desc, function () {
        return '<label for="s_' + key + '">' + M.glyph('emblem', 'set-emb') + label + '</label><span class="sw-wrap"><span class="sw-txt" aria-hidden="true">' + (s[key] ? 'On' : 'Off') + '</span>' +
          '<input class="switch" type="checkbox" id="s_' + key + '" data-key="' + key + '"' + (s[key] ? ' checked' : '') + '></span>';
      });
    }
    function sl(key, label, desc, min, max, step, fmt) {
      return row(key, label, desc, function () {
        var f = (s[key] - min) / (max - min);
        return '<label for="s_' + key + '">' + M.glyph('emblem', 'set-emb') + label + '</label><span class="val" id="v_' + key + '">' + fmt(s[key]) + '</span>' +
          '<input class="range" type="range" id="s_' + key + '" data-key="' + key + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + s[key] + '" style="--f:' + f.toFixed(3) + '">';
      }, 'slider');
    }
    function seg(key, label, desc, opts) {
      return row(key, label, desc, function () {
        return '<span class="set-l">' + M.glyph('emblem', 'set-emb') + label + '</span><div class="seg" role="group" aria-label="' + label + '">' + opts.map(function (o) {
          return '<button data-key="' + key + '" data-val="' + o[0] + '" aria-pressed="' + (s[key] === o[0]) + '">' + o[1] + '</button>'; }).join('') + '</div>';
      });
    }
    var f1 = function (v) { return (+v).toFixed(1); }, deg = function (v) { return v + '°'; };
    var rows = {
      video: sl('fov', 'Field of view', 'How wide you see. Higher shows more of the lot; lower feels closer and punchier.', 60, 130, 1, deg) +
        seg('graphics', 'Graphics', 'Auto picks the detail level for your device and drops it if frames get slow.', [['auto', 'Auto'], ['high', 'High'], ['low', 'Low']]) +
        sw('reduceFlash', 'Reduce flash', 'Tones down muzzle flashes, explosions and the hit flash.'),
      audio: sw('sfx', 'Sound effects', 'Guns, robots, pickups and menu clicks.'),
      controls: sl('mouseSens', 'Mouse sensitivity', 'How far the view turns per mouse move.', 0.1, 3, 0.1, f1) +
        sl('touchSens', 'Touch look sensitivity', 'How far the view turns when you drag on the right side of the screen.', 0.1, 3, 0.1, f1) +
        sw('invertY', 'Invert Y', 'Push up to look down, like a flight stick.'),
      gameplay: sw('shake', 'Screen shake', 'Camera kick from explosions, big guns and hits you take.') +
        sw('headBob', 'Head bob', 'The view bounces a little while you walk and sprint.')
    };
    var tabs = CATS.map(function (c) {
      return '<button class="set-cat" role="tab" data-cat="' + c[0] + '" aria-selected="' + (M._cat === c[0]) + '">' + c[1] + '</button>';
    }).join('');
    var html = '<div class="screen set-screen">' +
      '<section class="holo set-col" aria-label="Settings">' +
        M.crumb([from === 'pause' ? 'Paused' : 'Main menu', 'Settings', CATS.filter(function (c) { return c[0] === M._cat; })[0][1]]) +
        '<div class="set-cats" role="tablist" aria-label="Settings categories">' + (touch() ? '' : '<kbd class="qe">Q</kbd>') + tabs + (touch() ? '' : '<kbd class="qe">E</kbd>') + '</div>' +
        '<div class="settings-list" role="tabpanel">' + rows[M._cat] + '</div>' +
        '<p class="set-desc" id="setDesc" aria-live="polite">' + (rows[M._cat].match(/data-desc="([^"]*)"/) || [0, ''])[1] + '</p>' +
        '<div class="set-actions">' + btn('back', 'Done', 'primary', null, ' data-esc="1"') + btn('reset', 'Reset progress', 'danger') + '</div>' +
      '</section>' +
      M.keyHints([['Q E', 'Category'], ['↑↓', 'Move'], ['←→', 'Adjust'], ['Esc', 'Back']]) +
      '</div>';
    show('settings', html, true, focusSel);
    var first = ov.querySelector('.setting'); if (first) first.classList.add('cur');
    ov.querySelectorAll('.set-cat').forEach(function (b) {
      b.addEventListener('click', function () { if (M._cat === b.dataset.cat) return; M._cat = b.dataset.cat; IB.Audio && IB.Audio.play('ui'); renderSettings('.set-cat[aria-selected="true"]'); });
    });
    ov.querySelectorAll('input').forEach(function (el) {
      el.addEventListener('input', function () {
        var k = el.dataset.key, v = el.type === 'checkbox' ? el.checked : +el.value;
        if (el.type === 'range') {
          document.getElementById('v_' + k).textContent = k === 'fov' ? v + '°' : v.toFixed(1);
          el.style.setProperty('--f', ((v - +el.min) / (+el.max - +el.min)).toFixed(3));
        } else { var t = el.parentNode.querySelector('.sw-txt'); if (t) t.textContent = v ? 'On' : 'Off'; }
        M.act('setting', { key: k, value: v });
      });
    });
    ov.querySelectorAll('.seg button').forEach(function (b) {
      b.addEventListener('click', function () {
        b.parentNode.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        M.act('setting', { key: b.dataset.key, value: b.dataset.val });
      });
    });
  }
  M.confirmReset = function () {
    var html = '<div class="screen center-screen"><section class="holo panel warn" role="alertdialog" aria-label="Reset progress">' +
      '<header class="pn-head">' + M.glyph('warn', 'g24 pn-ic') + '<span class="pn-kicker">Settings · danger zone</span><h2>Reset progress</h2></header>' +
      '<p>Delete all 3 save slots and settings? Levels, gems, skills and gear go back to zero. This cannot be undone.</p>' +
      '<div class="row-actions">' + btn('cancelReset', 'Cancel', 'primary', null, ' data-esc="1"') + btn('doReset', 'Delete', 'danger') + '</div></section></div>';
    show('reset', html, true);
  };

  // ---------- pause ----------
  M.controlsCard = function () {
    if (touch()) return '<div class="controls-card"><kbd>Left thumb</kbd><span>Move (push far to sprint)</span><kbd>Right thumb</kbd><span>Look</span><kbd>Fire</kbd><span>Hold to shoot, drag to aim</span><kbd>Grid button</kbd><span>Inventory · skills</span></div>';
    return '<div class="controls-card"><kbd>WASD</kbd><span>Move</span><kbd>Mouse</kbd><span>Look · left fire · right aim</span><kbd>Space</kbd><span>Jump</span><kbd>Shift</kbd><span>Sprint</span><kbd>C</kbd><span>Slide · crouch</span><kbd>R</kbd><span>Reload</span><kbd>1–3 / wheel</kbd><span>Carried guns</span><kbd>Tab</kbd><span>Inventory · skills</span><kbd>F</kbd><span>Shove</span><kbd>Esc</kbd><span>Pause</span></div>';
  };
  M.pause = function (d) {
    var html = '<div class="screen side-screen pause-screen">' +
      '<div class="mm-col">' + M.crumb(['Level ' + d.level, 'Paused']) + '<h1 class="mm-title">Paused</h1>' +
        '<nav class="menu mm-list" aria-label="Pause menu">' + entry('resume', 'Resume', 'primary', null, ' data-esc="1"') + entry('fieldkit', 'Inventory & skills', '', touch() ? null : 'Tab') +
        entry('restart', 'Restart level') + entry('settings', 'Settings') + entry('quit', 'Quit to title') + '</nav></div>' +
      '<aside class="holo pz-card" aria-label="Level">' +
        '<div class="pz-head"><span class="pn-kicker">Level ' + d.level + '</span><b>' + esc(d.levelName) + '</b></div>' +
        '<div class="pz-stats"><span>' + M.glyph('emblem') + 'Zone <b>' + d.zone + '/' + d.zones + '</b></span><span>' + M.glyph('gem') + 'Gems <b>' + d.gems + '</b></span></div>' +
        M.controlsCard() + '</aside>' +
      M.keyHints([['Enter', 'Select'], ['Esc', 'Resume']]) +
      '</div>';
    show('pause', html, true);
  };

  // ---------- results ----------
  function statRow(g, label, v, cls) { return '<div class="rs-row' + (cls ? ' ' + cls : '') + '">' + M.glyph(g) + '<span>' + label + '</span><b>' + v + '</b></div>'; }
  M.results = function (d) {
    var lvl = d.levelUp ? '<div class="rs-lvup"><span class="lvb"><small>LV</small>' + d.playerLevel + '</span><span><b>Level up!</b><small>Player level</small></span>' +
      '<span class="rs-lvtxt">LV ' + d.playerLevel + (d.pointsUp ? ' · +' + d.pointsUp + ' skill pt' + (d.pointsUp > 1 ? 's' : '') : '') + '</span></div>' : '';
    var html = '<div class="screen center-screen"><section class="holo panel res-panel" aria-label="Level cleared">' +
      '<header class="pn-head">' + M.glyph('star', 'g24 pn-ic') + '<span class="pn-kicker">Hatch reached</span><h2>Level cleared</h2></header>' +
      '<div class="rs-grid">' +
        '<div class="rs-col">' + statRow('clock', 'Time', IB.HUD.mmss(d.time)) + statRow('bot', 'Robots crushed', d.kills) + statRow('core', 'Core hits', d.corePct + '%') + statRow('skull', 'Deaths', d.deaths) + '</div>' +
        '<div class="rs-col rs-gems">' + statRow('bot', 'Robots', d.gemsRobots, 'sub') + statRow('star', 'Clear bonus', d.gemsClear, 'sub') + statRow('heart', 'No-death bonus', d.gemsNoDeath, 'sub') +
          '<div class="rs-total"><span>Gems earned</span><b><i class="gem-glyph" aria-hidden="true"></i>' + d.gemsTotal + '</b></div>' + lvl + '</div>' +
      '</div>' +
      '<div class="row-actions">' + btn('next', 'Continue', 'primary') + btn('replay', 'Replay level') + '</div>' +
      '</section></div>';
    show('results', html, true);
  };
  M.fail = function () {
    var html = '<div class="screen center-screen"><section class="holo panel warn" aria-label="Out of retries">' +
      '<header class="pn-head">' + M.glyph('skull', 'g24 pn-ic') + '<span class="pn-kicker">Scrapped</span><h2>Out of retries</h2></header>' +
      '<p>The trash bots hold this level for now. Try it again from the start.</p>' +
      '<div class="row-actions">' + btn('retry', 'Retry level', 'primary') + btn('quit', 'Quit to title') + '</div></section></div>';
    show('fail', html, true);
  };
  M.message = function (title, text, act, label) {
    var html = '<div class="screen center-screen"><section class="holo panel" aria-label="' + esc(title) + '"><header class="pn-head"><h2>' + title + '</h2></header><p>' + text + '</p>' + btn(act, label, 'primary', null, ' data-esc="1"') + '</section></div>';
    show('message', html, true);
  };
  M.resumePlate = function () {
    var html = '<div class="screen center-screen"><button class="btn primary resume-plate" data-act="resume" data-esc="1">' + M.glyph('emblem', 'mm-emb') + '<span class="btn-l">Click to resume</span></button></div>';
    show('resumePlate', html, true);
  };
  M.rotateHint = function () {
    var html = '<div class="screen center-screen"><section class="holo panel rot-panel" aria-label="Rotate">' +
      '<div class="rot-art" aria-hidden="true">' + M.glyph('phone', 'rot-phone') + M.glyph('rotate', 'rot-arrows') + '</div>' +
      '<header class="pn-head"><span class="pn-kicker">Tip</span><h2>Turn sideways</h2></header><p>Turn your phone sideways for a wider view. Playing upright works too.</p>' + btn('dismissRotate', 'Got it', 'primary', null, ' data-esc="1"') + '</section></div>';
    show('rotate', html, true);
  };

  // level intro banner (non-blocking): thin rules, kicker, big condensed name, line
  M.intro = function (d, secs) {
    var el = document.createElement('div');
    el.className = 'intro';
    el.innerHTML = '<section class="intro-card"><span class="lvl">Level ' + d.level + ' · ' + d.zones + ' zones</span><h2>' + esc(d.name) + '</h2>' + (d.line ? '<p>' + esc(d.line) + '</p>' : '') + '</section>';
    document.body.appendChild(el);
    setTimeout(function () { el.style.transition = 'opacity .3s'; el.style.opacity = 0; setTimeout(function () { el.remove(); }, 320); }, (secs || 2.2) * 1000);
  };
  // ---------- between-levels loading screen ----------
  // Interlocking gears (meshing phase computed so teeth never overlap), a hex bolt hub with the bullet hole,
  // and the ink splat behind them. Pure inline SVG + CSS animation.
  function gearPath(n, rp) {
    var ro = rp + 4.2, ri = rp - 4.2, step = Math.PI * 2 / n, d = '', f = function (v) { return v.toFixed(2); };
    for (var i = 0; i < n; i++) {
      var a = i * step, pts = [[ri, a - step * 0.5], [ri, a - step * 0.31], [ro, a - step * 0.2], [ro, a + step * 0.2], [ri, a + step * 0.31]];
      for (var j = 0; j < pts.length; j++) d += (i === 0 && j === 0 ? 'M' : 'L') + f(Math.cos(pts[j][1]) * pts[j][0]) + ' ' + f(Math.sin(pts[j][1]) * pts[j][0]);
    }
    return d + 'Z';
  }
  function gear(n, x, y, phaseDeg, dir, cls, hub) {
    var rp = n * 2.6, period = n * 0.16;   // same tooth module: angular speed ~ 1/n, so the train turns together
    var spokes = '<circle class="g-groove" r="' + (rp * 0.74).toFixed(1) + '"/>';
    if (rp > 40) for (var s = 0; s < 6; s++) spokes += '<circle class="g-hole" r="' + (rp * 0.085).toFixed(1) + '" cx="' + (Math.cos(s * 1.0472 + 0.5) * rp * 0.53).toFixed(1) + '" cy="' + (Math.sin(s * 1.0472 + 0.5) * rp * 0.53).toFixed(1) + '"/>';
    return '<g transform="translate(' + x.toFixed(1) + ' ' + y.toFixed(1) + ') rotate(' + phaseDeg.toFixed(2) + ')">' +
      '<g class="gear ' + cls + '" style="animation-duration:' + period.toFixed(2) + 's;animation-direction:' + (dir > 0 ? 'normal' : 'reverse') + '">' +
      '<circle r="' + (rp + 8) + '" fill="none" stroke="none"/>' +
      '<path class="g-body" d="' + gearPath(n, rp) + '"/>' + spokes +
      '<circle class="g-rim" r="' + (rp * 0.3).toFixed(1) + '"/>' + (hub || '') + '</g></g>';
  }
  // place gear b (nb teeth) meshing with gear a at angle theta; returns {x, y, phase}
  function mesh(a, nb, theta) {
    var ra = a.n * 2.6, rb = nb * 2.6, dist = ra + rb;
    var fa = ((theta - a.phase * Math.PI / 180) / (Math.PI * 2 / a.n)) % 1; if (fa < 0) fa += 1;
    var phase = theta + Math.PI - (Math.PI * 2 / nb) * (0.5 - fa);
    return { n: nb, x: a.x + Math.cos(theta) * dist, y: a.y + Math.sin(theta) * dist, phase: phase * 180 / Math.PI, dir: -a.dir };
  }
  function loadingArt() {
    var A = { n: 22, x: 0, y: 0, phase: 0, dir: 1 };
    var B = mesh(A, 12, -0.62), C = mesh(A, 9, 2.25), D = mesh(B, 8, -1.9);
    var hub = '<polygon class="g-bolt" points="15,0 7.5,13 -7.5,13 -15,0 -7.5,-13 7.5,-13"/><circle class="g-shot" r="4.6"/>';
    var smallHub = '<polygon class="g-bolt sm" points="7,0 3.5,6 -3.5,6 -7,0 -3.5,-6 3.5,-6"/>';
    return '<svg class="ld-art" viewBox="-114 -134 232 232" aria-hidden="true">' +
      '<path class="ld-splat" d="' + SPLAT + '" transform="translate(6 -10) scale(4.6) rotate(-12)"/>' +
      gear(D.n, D.x, D.y, D.phase, D.dir, 'g-amber', smallHub) +
      gear(B.n, B.x, B.y, B.phase, B.dir, 'g-teal', smallHub) +
      gear(C.n, C.x, C.y, C.phase, C.dir, 'g-amber', smallHub) +
      gear(A.n, A.x, A.y, A.phase, A.dir, 'g-paper', hub) +
      '</svg>';
  }
  var ld = null, ldT = 0;
  // d: {level, name, line, palette?: [4 hex]}
  M.loading = function (d) {
    d = d || {};
    if (!ld) ld = document.getElementById('loading');
    clearTimeout(ldT);
    var strip = (d.palette || []).slice(0, 4).map(function (c) { return '<i style="background:' + c + '"></i>'; }).join('');
    var tip = TIPS[(Math.random() * TIPS.length) | 0];
    ld.innerHTML = '<div class="ld-inner">' +
      '<div class="ld-stage">' + loadingArt() + '</div>' +
      '<div class="ld-copy">' +
        '<span class="ld-level"><span>Level <b>' + (d.level || 1) + '</b></span>' + (strip ? '<span class="ld-pal">' + strip + '</span>' : '') + '</span>' +
        '<h2 class="ld-name">' + esc(d.name || '') + '</h2>' +
        (d.line ? '<p class="ld-line">' + esc(d.line) + '</p>' : '') +
        '<div class="ld-progress"><div class="ld-track"><i id="ldFill"></i></div><b id="ldPct">0%</b></div>' +
        '<div class="tipbox ld-tip" role="note"><b>' + tip[0] + '</b><p>' + tip[1] + '</p></div>' +
      '</div></div><div class="ld-logo">' + M.logo() + '</div><div class="ld-hazard" aria-hidden="true"></div>';
    ld.className = 'loading';
    ld.hidden = false;
    ld.setAttribute('role', 'status'); ld.setAttribute('aria-label', 'Loading level ' + (d.level || 1));
    M.loadingProgress(0);
  };
  M.loadingProgress = function (f) {
    if (!ld || ld.hidden) return;
    f = Math.max(0, Math.min(1, f || 0));
    var fill = document.getElementById('ldFill'), pct = document.getElementById('ldPct');
    if (fill) fill.style.width = (f * 100).toFixed(1) + '%';
    if (pct) pct.textContent = Math.round(f * 100) + '%';
  };
  // fades the screen out (0.45 s); cb runs once it is gone
  M.loadingHide = function (cb) {
    if (!ld || ld.hidden) { if (cb) cb(); return; }
    M.loadingProgress(1);
    ld.classList.add('out');
    clearTimeout(ldT);
    ldT = setTimeout(function () { ld.hidden = true; ld.className = 'loading'; ld.innerHTML = ''; if (cb) cb(); }, 460);
  };
  M.isLoading = function () { return !!ld && !ld.hidden; };

  M.wipe = function (cb) {
    var w = document.createElement('div'); w.className = 'wipe in'; document.body.appendChild(w);
    setTimeout(function () { if (cb) cb(); w.className = 'wipe out'; setTimeout(function () { w.remove(); }, 380); }, 360);
  };
})(window.IB = window.IB || {});
