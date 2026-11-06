/* INKBOLT skill HUD: the Undercover (F) ability.
     - cooldown badge above the bottom edge (desktop) / the touch button's ring (phone), shown only while the skill is owned
     - the cloak look: the world turns comic black, grey and white (CSS filter on the game canvas) under a halftone
       dot screen and an ink vignette; the HUD stays in colour. It flickers back in the last second.
   IB.SkillHUD.update(G, dt) runs every frame from game.js; it reads IB.SkillFX.cloakState(). Styles live here so the
   feature stays in one place. */
(function (IB) {
  'use strict';
  var H = IB.SkillHUD = { el: null, fx: null, btn: null, last: '' };
  var CSS = [
    'body.cloak-on #c { filter: grayscale(1) contrast(1.55) brightness(1.06); }',
    'body.cloak-flick #c { filter: grayscale(.55) contrast(1.25); }',
    '.cloakfx { position: fixed; inset: 0; pointer-events: none; opacity: 0; transition: opacity .18s;',
    '  background: radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(12,11,16,.62) 100%),',
    '    radial-gradient(circle, rgba(18,16,24,.36) 30%, transparent 33%) 0 0 / 6px 6px; mix-blend-mode: multiply; }',
    '.cloakfx::after { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(-58deg, rgba(255,255,255,.07) 0 2px, transparent 2px 9px); }',
    'body.cloak-on .cloakfx { opacity: 1; } body.cloak-flick .cloakfx { opacity: .45; }',
    '.cloakhud { position: fixed; left: 50%; bottom: calc(var(--sab, 0px) + 112px); transform: translateX(-50%); display: flex; align-items: center; gap: 8px;',
    '  padding: 5px 12px 5px 6px; border-radius: 22px; background: rgba(34,29,44,.78); box-shadow: 0 0 0 3px #15121C; color: #FFFDF7;',
    '  font: 900 13px "Archivo", sans-serif; font-stretch: 125%; letter-spacing: .04em; pointer-events: none; opacity: var(--hud-a, 1); }',
    '.cloakhud[hidden] { display: none; }',
    '.cloakhud .ck-ring { position: relative; width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center;',
    '  background: conic-gradient(#12C7B6 calc(var(--k, 1) * 360deg), rgba(255,253,247,.16) 0); }',
    '.cloakhud .ck-ring::before { content: ""; position: absolute; inset: 4px; border-radius: 50%; background: #221D2C; }',
    '.cloakhud .ck-ring svg { position: relative; width: 18px; height: 18px; }',
    '.cloakhud .ck-key { display: inline-grid; place-items: center; min-width: 18px; height: 18px; padding: 0 3px; border-radius: 4px; background: #FFFDF7; color: #15121C; font-size: 11px; }',
    '.cloakhud.ready .ck-txt { color: #12C7B6; } .cloakhud.on { background: #FFFDF7; color: #15121C; } .cloakhud.on .ck-ring::before { background: #FFFDF7; }',
    '.cloakhud.on .ck-ring { background: conic-gradient(#15121C calc(var(--k, 1) * 360deg), rgba(21,18,28,.15) 0); }',
    'body.touch-on .cloakhud { display: none; }',
    '.touch .tcloak { background: conic-gradient(rgba(18,199,182,.9) calc(var(--k, 1) * 360deg), rgba(34,29,44,.74) 0) !important; }',
    '.touch .tcloak.cool { color: rgba(255,253,247,.5); } .touch .tcloak.on { background: #FFFDF7 !important; color: #15121C; }'
  ].join('\n');
  var EYE = '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 26c6-10 30-10 36 0-6 10-30 10-36 0z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/><circle cx="24" cy="26" r="5.5" fill="currentColor"/><path d="M9 41 39 11" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/></svg>';

  function init() {
    if (H.el || typeof document === 'undefined' || !document.body) return;
    var st = document.createElement('style'); st.id = 'skillHudCss'; st.textContent = CSS; document.head.appendChild(st);
    var fx = H.fx = document.createElement('div'); fx.className = 'cloakfx'; fx.id = 'cloakFx'; fx.setAttribute('aria-hidden', 'true');
    var cv = document.getElementById('c');
    if (cv && cv.parentNode) cv.parentNode.insertBefore(fx, cv.nextSibling); else document.body.appendChild(fx);
    var el = H.el = document.createElement('div'); el.className = 'cloakhud'; el.id = 'cloakHud'; el.hidden = true;
    el.innerHTML = '<span class="ck-ring">' + EYE + '</span><span class="ck-key">F</span><span class="ck-txt">UNDERCOVER</span>';
    document.body.appendChild(el);
    H.txt = el.querySelector('.ck-txt');
  }

  H.update = function (G) {
    init(); if (!H.el) return;
    var SF = IB.SkillFX, s = SF && SF.cloakState ? SF.cloakState() : null;
    var live = G.mode === 'play' || G.mode === 'paused' || G.mode === 'menu';
    var on = !!(s && s.active && live), show = !!(s && s.owned && G.mode === 'play' && !G.dead);
    // the cloak look; flickers back to colour over its last second
    var flick = on && s.t < 1 && Math.sin(s.t * 30) > 0.2;
    document.body.classList.toggle('cloak-on', on && !flick);
    document.body.classList.toggle('cloak-flick', on && flick);
    var k = !s ? 1 : s.active ? s.t / s.time : s.cd > 0 ? 1 - s.cd / s.cooldown : 1;
    var state = !s ? '' : s.active ? 'on' : s.cd > 0 ? 'cool' : 'ready';
    var label = state === 'on' ? 'HIDDEN ' + Math.ceil(s.t) + 's' : state === 'cool' ? Math.ceil(s.cd) + 's' : 'UNDERCOVER';
    if (H.el.hidden === show) H.el.hidden = !show;
    if (show) {
      H.el.style.setProperty('--k', k.toFixed(3));
      var key = state + label;
      if (key !== H.last) { H.last = key; H.el.className = 'cloakhud ' + state; H.txt.textContent = label; }
    }
    var btn = H.btn || (H.btn = document.getElementById('tCloak'));
    if (btn) {
      if (btn.hidden === !!(s && s.owned)) btn.hidden = !(s && s.owned);
      if (s && s.owned) { btn.style.setProperty('--k', k.toFixed(3)); btn.classList.toggle('on', state === 'on'); btn.classList.toggle('cool', state === 'cool'); }
    }
  };
})(window.IB = window.IB || {});
