/* INKBOLT menus: title, settings (+ reset confirm), pause, results, fail, level intro, rotate hint.
   One primary button per screen; keyboard (Tab/arrows/Enter/Esc) and mouse/touch. */
(function (IB) {
  'use strict';
  var M = IB.Menus = { cur: null, stack: [] };
  var ov;

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
  function splatMark() { return '<svg class="splat-mark" viewBox="-25 -25 50 50" aria-hidden="true"><path d="' + SPLAT + '" fill="currentColor"/></svg>'; }

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
        var list = Array.prototype.slice.call(ov.querySelectorAll('.btn, .switch, .range, .seg button'));
        var i = list.indexOf(document.activeElement);
        if (document.activeElement && document.activeElement.classList.contains('range') && false) return;
        e.preventDefault();
        var n = list[(i + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length]; if (n) n.focus();
      }
    });
    window.addEventListener('keydown', function (e) {
      if (ov.hidden || e.key !== 'Escape') return;
      var back = ov.querySelector('[data-esc]');
      if (back) { e.preventDefault(); M.act(back.dataset.act, back); }
    });
  };
  M.handlers = {};
  M.on = function (act, fn) { M.handlers[act] = fn; };
  M.act = function (act, el) { var f = M.handlers[act]; if (f) f(el); };

  M.hide = function () { ov.hidden = true; ov.innerHTML = ''; ov.className = 'overlay'; M.cur = null; };
  function show(name, html, dim, focusSel) {
    M.cur = name; ov.hidden = false; ov.className = 'overlay' + (dim ? ' dim' : '');
    ov.innerHTML = html;
    var f = ov.querySelector(focusSel || '.btn.primary') || ov.querySelector('.btn');
    if (f && !IB.Input.touch) f.focus({ preventScroll: true });
    ov.scrollTop = 0;
  }
  M.isOpen = function () { return !ov.hidden; };

  function btn(act, label, cls, hint, extra) {
    return '<button class="plate btn ' + (cls || '') + '" data-act="' + act + '"' + (extra || '') + '><span>' + label + '</span>' + (hint ? '<span class="hint">' + hint + '</span>' : (cls && cls.indexOf('primary') >= 0 ? splatMark() : '')) + '</button>';
  }

  // ---------- title ----------
  M.title = function (d) {
    var cont = d.slot ? btn('continue', 'Continue', 'primary', 'Level ' + d.slot.level + ' · ' + d.levelName) : '';
    var html = '<div class="screen title-screen">' +
      '<div class="title-left">' + M.logo() +
      '<div class="tagline">Clear the town. Crush the trash bots.</div>' +
      '<nav class="menu" aria-label="Main menu">' + cont +
      btn('new', d.slot ? 'New game' : 'Play', d.slot ? '' : 'primary', d.slot ? null : 'Toy Town') +
      btn('settings', 'Settings') + '</nav></div></div>';
    show('title', html, false);
  };

  // ---------- settings ----------
  M.settings = function (s, from) {
    function sw(key, label) { return '<div class="setting"><label for="s_' + key + '">' + label + '</label><input class="switch" type="checkbox" id="s_' + key + '" data-key="' + key + '"' + (s[key] ? ' checked' : '') + '></div>'; }
    function sl(key, label, min, max, step, fmt) {
      return '<div class="setting slider"><label for="s_' + key + '">' + label + '</label><span class="val" id="v_' + key + '">' + fmt(s[key]) + '</span>' +
        '<input class="range" type="range" id="s_' + key + '" data-key="' + key + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + s[key] + '"></div>';
    }
    function seg(key, label, opts) {
      return '<div class="setting"><span>' + label + '</span><div class="seg" role="group" aria-label="' + label + '">' + opts.map(function (o) {
        return '<button data-key="' + key + '" data-val="' + o[0] + '" aria-pressed="' + (s[key] === o[0]) + '">' + o[1] + '</button>'; }).join('') + '</div></div>';
    }
    var f1 = function (v) { return (+v).toFixed(1); };
    var html = '<div class="screen center-screen"><section class="plate ink panel" aria-label="Settings">' +
      '<h2>Settings</h2><div class="hazard"></div><div class="settings-list">' +
      sw('sfx', 'Sound effects') +
      sl('mouseSens', 'Mouse sensitivity', 0.1, 3, 0.1, f1) +
      sl('touchSens', 'Touch look sensitivity', 0.1, 3, 0.1, f1) +
      sl('fov', 'Field of view', 70, 100, 1, function (v) { return v + '°'; }) +
      sw('invertY', 'Invert Y') +
      seg('graphics', 'Graphics', [['auto', 'Auto'], ['high', 'High'], ['low', 'Low']]) +
      sw('shake', 'Screen shake') + sw('headBob', 'Head bob') + sw('reduceFlash', 'Reduce flash') +
      '</div>' + btn('back', 'Done', 'primary', null, ' data-esc="1"') +
      btn('reset', 'Reset progress', 'danger') +
      '</section></div>';
    show('settings', html, true);
    M._settingsFrom = from;
    ov.querySelectorAll('input').forEach(function (el) {
      el.addEventListener('input', function () {
        var k = el.dataset.key, v = el.type === 'checkbox' ? el.checked : +el.value;
        if (el.type === 'range') document.getElementById('v_' + k).textContent = k === 'fov' ? v + '°' : v.toFixed(1);
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
  };
  M.confirmReset = function () {
    var html = '<div class="screen center-screen"><section class="plate ink panel" role="alertdialog" aria-label="Reset progress">' +
      '<h2>Reset progress</h2><p>Delete all 3 save slots and settings? This cannot be undone.</p>' +
      '<div class="row-actions">' + btn('cancelReset', 'Cancel', 'primary', null, ' data-esc="1"') + btn('doReset', 'Delete', 'danger') + '</div></section></div>';
    show('reset', html, true);
  };

  // ---------- pause ----------
  M.controlsCard = function () {
    if (IB.Input.touch) return '<div class="controls-card"><kbd>Left thumb</kbd><span>Move (push far to sprint)</span><kbd>Right thumb</kbd><span>Look</span><kbd>Fire</kbd><span>Hold to shoot, drag to aim</span></div>';
    return '<div class="controls-card"><kbd>WASD</kbd><span>Move</span><kbd>Mouse</kbd><span>Look · left fire · right aim</span><kbd>Space</kbd><span>Jump</span><kbd>Shift</kbd><span>Sprint</span><kbd>R</kbd><span>Reload</span><kbd>1–9 / wheel</kbd><span>Weapons</span><kbd>F</kbd><span>Shove</span><kbd>Esc</kbd><span>Pause</span></div>';
  };
  M.pause = function (d) {
    var html = '<div class="screen center-screen"><section class="plate ink panel two-col" aria-label="Paused">' +
      '<h2>Paused</h2><div class="hazard"></div>' +
      '<div class="menu">' + btn('resume', 'Resume', 'primary', null, ' data-esc="1"') + btn('restart', 'Restart level') + btn('settings', 'Settings') + btn('quit', 'Quit to title') + '</div>' +
      '<div class="menu"><div class="kv"><span>' + d.levelName + '</span><b>Level ' + d.level + '</b><span>Zone</span><b>' + d.zone + '/' + d.zones + '</b><span>Gems</span><b>' + d.gems + '</b></div>' + M.controlsCard() + '</div>' +
      '</section></div>';
    show('pause', html, true);
  };

  // ---------- results ----------
  M.results = function (d) {
    var html = '<div class="screen center-screen"><section class="plate ink panel two-col" aria-label="Level cleared">' +
      '<h2>Level cleared</h2><div class="hazard"></div>' +
      '<div class="kv"><span>Time</span><b>' + IB.HUD.mmss(d.time) + '</b><span>Robots crushed</span><b>' + d.kills + '</b><span>Core hits</span><b>' + d.corePct + '%</b><span>Deaths</span><b>' + d.deaths + '</b></div>' +
      '<div class="menu"><div class="kv"><span class="sub">Robots</span><b class="sub">' + d.gemsRobots + '</b><span class="sub">Clear bonus</span><b class="sub">' + d.gemsClear + '</b><span class="sub">No-death bonus</span><b class="sub">' + d.gemsNoDeath + '</b>' +
      '<span class="total">Gems earned</span><b class="total">' + d.gemsTotal + '</b></div>' +
      btn('next', 'Continue', 'primary') + btn('replay', 'Replay level') + '</div>' +
      '</section></div>';
    show('results', html, true);
  };
  M.fail = function () {
    var html = '<div class="screen center-screen"><section class="plate red panel" aria-label="Out of retries">' +
      '<h2>Out of retries</h2><p>The trash bots hold this level for now. Try it again from the start.</p>' +
      '<div class="row-actions">' + btn('retry', 'Retry level', 'primary') + btn('quit', 'Quit to title') + '</div></section></div>';
    show('fail', html, true);
  };
  M.message = function (title, text, act, label) {
    var html = '<div class="screen center-screen"><section class="plate ink panel" aria-label="' + title + '"><h2>' + title + '</h2><p>' + text + '</p>' + btn(act, label, 'primary', null, ' data-esc="1"') + '</section></div>';
    show('message', html, true);
  };
  M.resumePlate = function () {
    var html = '<div class="screen center-screen"><button class="plate btn primary" data-act="resume" data-esc="1"><span>Click to resume</span></button></div>';
    show('resumePlate', html, true);
  };
  M.rotateHint = function () {
    var html = '<div class="screen center-screen"><section class="plate ink panel" aria-label="Rotate"><h2>Turn sideways</h2><p>Turn your phone sideways for a wider view. Playing upright works too.</p>' + btn('dismissRotate', 'Got it', 'primary', null, ' data-esc="1"') + '</section></div>';
    show('rotate', html, true);
  };

  // level intro card (non-blocking)
  M.intro = function (d, secs) {
    var el = document.createElement('div');
    el.className = 'intro';
    el.innerHTML = '<section class="plate ink panel"><span class="lvl">Level ' + d.level + ' · ' + d.zones + ' zones</span><h2>' + d.name + '</h2>' + (d.line ? '<p>' + d.line + '</p>' : '') + '</section>';
    document.body.appendChild(el);
    setTimeout(function () { el.style.transition = 'opacity .3s'; el.style.opacity = 0; setTimeout(function () { el.remove(); }, 320); }, (secs || 2.2) * 1000);
  };
  M.wipe = function (cb) {
    var w = document.createElement('div'); w.className = 'wipe in'; document.body.appendChild(w);
    setTimeout(function () { if (cb) cb(); w.className = 'wipe out'; setTimeout(function () { w.remove(); }, 380); }, 360);
  };
})(window.IB = window.IB || {});
