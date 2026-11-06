/* INKBOLT damage numbers: comic counters that pop above a robot and rise + fade (DOM overlay, pooled).
     IB.FX.damageNumber(x, y, z, amount, kind)   kind: 'hit' | 'core' | 'crit' | 'shock' | 'acid'
   Each number is one absolutely positioned element moved with a transform (no layout per frame), projected
   from its world point every frame and clamped inside the screen edges. Hits on the same spot within a
   few frames merge into one number (shotgun pellets, SMG streams). */
(function (IB) {
  'use strict';
  var FX = IB.FX = IB.FX || {};
  var CAP = 28, LIFE = { hit: 0.85, core: 1.0, crit: 1.1, shock: 0.75, acid: 0.75 };
  var pool = [], root = null, _v = null, seq = 0;

  function init() {
    if (root) return root;
    var host = document.getElementById('hud') || document.body;
    root = document.createElement('div');
    root.className = 'dmgnums'; root.id = 'dmgNums'; root.setAttribute('aria-hidden', 'true');
    var sv = document.getElementById('scopeView');
    host.insertBefore(root, sv ? sv.nextSibling : host.firstChild);   // over the scope view, under the HUD plates
    for (var i = 0; i < CAP; i++) {
      var el = document.createElement('b'); el.className = 'dmgn'; el.style.opacity = '0';
      root.appendChild(el);
      pool.push({ el: el, on: false, t: 0, life: 1, x: 0, y: 0, z: 0, amt: 0, kind: 'hit', jx: 0, w: 0, id: 0 });
    }
    _v = new THREE.Vector3();
    return root;
  }
  function label(n) { return String(Math.max(1, Math.round(n))); }

  FX.damageNumber = function (x, y, z, amount, kind) {
    if (typeof document === 'undefined' || !(amount > 0)) return null;
    init();
    kind = LIFE[kind] ? kind : 'hit';
    var i, d, best = null, oldest = null;
    // merge into a young number of the same kind at the same spot
    for (i = 0; i < CAP; i++) {
      d = pool[i];
      if (d.on && d.kind === kind && d.t < 0.12 && Math.abs(d.x - x) + Math.abs(d.z - z) < 0.5 && Math.abs(d.y - y) < 0.6) { best = d; break; }
    }
    if (best) {
      best.amt += amount; best.t = Math.min(best.t, 0.05);
      best.el.textContent = label(best.amt) + (kind === 'crit' ? '!' : '');
      return best;
    }
    for (i = 0; i < CAP; i++) { d = pool[i]; if (!d.on) { best = d; break; } if (!oldest || d.t / d.life > oldest.t / oldest.life) oldest = d; }
    d = best || oldest;
    d.on = true; d.t = 0; d.life = LIFE[kind]; d.kind = kind; d.amt = amount; d.id = ++seq;
    d.x = x; d.y = y; d.z = z; d.jx = (Math.random() - 0.5) * 0.5; d.drift = (Math.random() - 0.5) * 0.35;
    d.el.className = 'dmgn ' + kind;
    d.el.textContent = label(amount) + (kind === 'crit' ? '!' : '');
    d.w = 0;   // width measured lazily on the first frame (one read per number)
    return d;
  };

  // pop 0.55 -> 1.25 -> 1.0 in 0.16 s, rise 0.6 m, fade over the last 45 %
  FX.updateNumbers = function (dt, cam) {
    if (!root || !cam) return;
    var W = window.innerWidth, H = window.innerHeight, m = 8, top = 8;
    for (var i = 0; i < CAP; i++) {
      var d = pool[i]; if (!d.on) continue;
      d.t += dt;
      var k = d.t / d.life;
      if (k >= 1) { d.on = false; d.el.style.opacity = '0'; d.el.style.transform = 'translate3d(-999px,-999px,0)'; continue; }
      var rise = (1 - Math.pow(1 - k, 2.2)) * (d.kind === 'shock' || d.kind === 'acid' ? 0.45 : 0.62);
      _v.set(d.x + d.jx + d.drift * k, d.y + rise, d.z).project(cam);
      if (_v.z > 1 || _v.z < -1) { d.el.style.opacity = '0'; continue; }
      if (!d.w) { d.w = d.el.offsetWidth || 40; d.h = d.el.offsetHeight || 30; }
      var sx = (_v.x + 1) / 2 * W, sy = (1 - _v.y) / 2 * H;
      sx = Math.max(m + d.w / 2, Math.min(W - m - d.w / 2, sx));
      sy = Math.max(top + d.h / 2, Math.min(H - m - d.h / 2, sy));
      var s = d.t < 0.08 ? 0.55 + d.t / 0.08 * 0.7 : d.t < 0.16 ? 1.25 - (d.t - 0.08) / 0.08 * 0.25 : 1;
      var a = k < 0.55 ? 1 : 1 - (k - 0.55) / 0.45;
      d.el.style.opacity = a.toFixed(2);
      d.el.style.transform = 'translate3d(' + (sx - d.w / 2).toFixed(1) + 'px,' + (sy - d.h / 2).toFixed(1) + 'px,0) scale(' + s.toFixed(3) + ')';
    }
  };
  FX.clearNumbers = function () { pool.forEach(function (d) { d.on = false; d.el.style.opacity = '0'; }); };
  FX.numbersActive = function () { var n = 0; pool.forEach(function (d) { if (d.on) n++; }); return n; };
  FX.numbersList = function () { return pool.filter(function (d) { return d.on; }).map(function (d) { return { kind: d.kind, amount: Math.round(d.amt), text: d.el.textContent }; }); };

  // ride FX.update (it runs every frame after the camera is placed, in play, title and menus)
  var baseUpdate = FX.update;
  if (baseUpdate && !baseUpdate._nums) {
    FX.update = function (dt, cam) { baseUpdate.apply(FX, arguments); FX.updateNumbers(dt, cam); };
    FX.update._nums = true;
  }
  var baseClear = FX.clear;
  if (baseClear && !baseClear._nums) { FX.clear = function () { baseClear.apply(FX, arguments); FX.clearNumbers(); }; FX.clear._nums = true; }
})(window.IB = window.IB || {});
