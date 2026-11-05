/* INKBOLT HUD (section 2.4). DOM writes only when a value changes. */
(function (IB) {
  'use strict';
  var H = IB.HUD = { last: {} };
  var $ = function (id) { return document.getElementById(id); };

  var ICONS = {
    pistol: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M4 5h26v6H16l-2 7H8l2-7H4z" fill="currentColor"/></svg>',
    smg: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M2 5h32v3h4v3H22v7h-5l-1-7h-4l-2 5H6l1-5H2z" fill="currentColor"/></svg>',
    rifle: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M1 6h36v3H24v8h-5l-1-5h-6l-3 5H4l3-6H1z" fill="currentColor"/></svg>',
    sniper: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M1 8h38v2H24v7h-4l-1-5H6l-3 5H1zM12 4h10v3H12z" fill="currentColor"/></svg>',
    rocket: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M2 6h30l6 4-6 4H2zM14 14h5v5h-5z" fill="currentColor"/></svg>',
    melee: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M2 12 30 4l4 2-26 10zM30 4l6-2 2 3-4 1z" fill="currentColor"/></svg>',
    shove: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M8 6h18l6 4-6 4H8z" fill="currentColor"/></svg>'
  };
  H.icon = function (cls) { return ICONS[cls] || ICONS.pistol; };

  H.init = function () {
    H.el = {
      hud: $('hud'), gems: $('gems'), gemCount: $('gemCount'), scZone: $('scZone'), scTime: $('scTime'), scLeft: $('scLeft'), pips: $('pips'),
      feed: $('feed'), xhair: $('xhair'), hitmark: $('hitmark'), arcs: $('arcs'), health: $('health'), hpFill: $('hpFill'), hpNum: $('hpNum'),
      slots: $('slots'), ammo: $('ammo'), ammoMag: $('ammoMag'), ammoRes: $('ammoRes'), toast: $('toast'), elim: $('elim'),
      elimName: $('elimName'), elimCount: $('elimCount'), elimRetries: $('elimRetries')
    };
    H.arcs = [];
    for (var i = 0; i < 6; i++) {
      var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.innerHTML = '<path class="ink" d="M-34 -120 A124 124 0 0 1 34 -120"/><path d="M-32 -120 A124 124 0 0 1 32 -120"/>';
      g.style.opacity = 0; H.el.arcs.appendChild(g);
      H.arcs.push({ g: g, t: 0, ang: 0 });
    }
    H.feedRows = [];
  };
  H.show = function (on) { H.el.hud.hidden = !on; };

  function set(key, val, fn) { if (H.last[key] !== val) { H.last[key] = val; fn(val); } }
  H.reset = function () { H.last = {}; H.el.feed.innerHTML = ''; H.feedRows = []; };

  H.gems = function (n, pulse) {
    set('gems', n, function (v) { H.el.gemCount.textContent = v; });
    if (pulse) { H.el.gems.classList.remove('pulse'); void H.el.gems.offsetWidth; H.el.gems.classList.add('pulse'); }
  };
  function mmss(t) { t = Math.max(0, Math.floor(t)); var m = Math.floor(t / 60), s = t % 60; return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s; }
  H.mmss = mmss;
  H.score = function (zone, total, time, left) {
    set('zone', zone + '/' + total, function () { H.el.scZone.textContent = 'ZONE ' + zone + '/' + total; });
    set('time', mmss(time), function (v) { H.el.scTime.textContent = v; });
    set('left', left, function (v) { H.el.scLeft.textContent = v + ' LEFT'; });
  };
  H.pips = function (total, cur, cleared) {
    set('pips', total + ':' + cur + ':' + cleared, function () {
      var s = ''; for (var i = 0; i < total; i++) s += '<i class="' + (i < cleared ? 'done' : (i === cur ? 'cur' : '')) + '"></i>';
      H.el.pips.innerHTML = s;
    });
  };
  H.health = function (hp, max) {
    var v = Math.max(0, Math.ceil(hp));
    set('hp', v + '/' + max, function () {
      H.el.hpNum.textContent = v; H.el.hpFill.style.width = Math.max(0, Math.min(100, hp / max * 100)) + '%';
      H.el.health.classList.toggle('low', hp < 30);
    });
  };
  H.ammo = function (mag, res) {
    set('ammo', mag + '/' + res, function () {
      H.el.ammoMag.textContent = mag; H.el.ammoRes.textContent = '/ ' + (res === Infinity ? '∞' : res);
      H.el.ammo.classList.toggle('empty', mag === 0);
    });
  };
  /* list: [{slot, cls, on}] */
  H.slots = function (list) {
    var key = list.map(function (s) { return s.slot + (s.on ? '*' : ''); }).join(',');
    set('slots', key, function () {
      H.el.slots.innerHTML = list.map(function (s) {
        return '<div class="plate ink slot' + (s.on ? ' on' : '') + '"><span class="key">' + s.slot + '</span>' + H.icon(s.cls) + '</div>';
      }).join('');
    });
  };
  /* spreadDeg, vfovDeg, hidden */
  H.crosshair = function (spreadDeg, vfov, hidden) {
    var gap = 4 + Math.tan(spreadDeg * Math.PI / 180) / Math.tan(vfov * Math.PI / 360) * (window.innerHeight / 2);
    gap = Math.round(Math.min(60, gap));
    set('xh', gap + (hidden ? 'h' : ''), function () { H.el.xhair.style.setProperty('--gap-x', gap + 'px'); H.el.xhair.classList.toggle('hide', !!hidden); });
  };
  var hitT = 0;
  H.hit = function (kind) {
    var el = H.el.hitmark;
    el.setAttribute('class', 'hitmark on' + (kind === 'core' ? ' core' : '') + (kind === 'kill' ? ' kill' : ''));
    hitT = kind === 'kill' ? 0.22 : 0.12;
  };
  /* angle: radians, 0 = straight ahead, positive = to the right */
  H.arc = function (angle) {
    var a = H.arcs[0]; for (var i = 1; i < H.arcs.length; i++) if (H.arcs[i].t < a.t) a = H.arcs[i];
    a.t = 0.8; a.ang = angle;
  };
  H.feed = function (cls, name, gems) {
    var row = document.createElement('div');
    row.className = 'plate ink feed-row';
    row.innerHTML = H.icon(cls) + '<span>' + name + '</span>' + (gems ? '<span class="feed-gem">+' + gems + '</span>' : '');
    H.el.feed.insertBefore(row, H.el.feed.firstChild);
    H.feedRows.unshift({ el: row, t: 0 });
    while (H.feedRows.length > 4) { var r = H.feedRows.pop(); r.el.remove(); }
  };
  var toastT = 0;
  H.toast = function (text, secs) { H.el.toast.textContent = text; H.el.toast.hidden = false; toastT = secs || 2.5; H.el.toast.style.animation = 'none'; void H.el.toast.offsetWidth; H.el.toast.style.animation = ''; };
  H.elim = function (show, name, count, retries) {
    H.el.elim.hidden = !show;
    if (show) { H.el.elimName.textContent = name; H.el.elimCount.textContent = 'Back in ' + count; H.el.elimRetries.textContent = 'Retries left ' + retries; }
  };

  H.tick = function (dt) {
    if (hitT > 0) { hitT -= dt; if (hitT <= 0) H.el.hitmark.setAttribute('class', 'hitmark'); }
    if (toastT > 0) { toastT -= dt; if (toastT <= 0) H.el.toast.hidden = true; }
    for (var i = 0; i < H.arcs.length; i++) {
      var a = H.arcs[i];
      if (a.t > 0) { a.t -= dt; a.g.style.opacity = Math.max(0, Math.min(1, a.t / 0.3)); a.g.setAttribute('transform', 'rotate(' + (a.ang * 180 / Math.PI) + ')'); }
    }
    for (i = H.feedRows.length - 1; i >= 0; i--) {
      var r = H.feedRows[i]; r.t += dt;
      if (r.t > 4 && !r.out) { r.out = true; r.el.classList.add('out'); }
      if (r.t > 4.3) { r.el.remove(); H.feedRows.splice(i, 1); }
    }
  };
})(window.IB = window.IB || {});
