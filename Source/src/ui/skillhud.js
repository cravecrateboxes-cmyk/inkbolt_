/* INKBOLT skill HUD: the Undercover (F) ability.
     - cooldown badge above the bottom edge (desktop) / the touch button's ring (phone), shown only while the skill is owned
     - the cloak look: pressing F flickers between the normal and the cloaked frame for a moment (a fast fade-flicker),
       then the world sinks into a dark, desaturated blue under a halftone screen and a deep vignette, and every robot
       is drawn with a glowing dark-blue outline (IB.Render.robotOutline). It flickers back out over the last second.
   IB.SkillHUD.update(G, dt) runs every frame from game.js; it reads IB.SkillFX.cloakState(). Styles live here so the
   feature stays in one place. */
(function (IB) {
  'use strict';
  var H = IB.SkillHUD = { el: null, fx: null, btn: null, last: '' };
  var CSS = [
    '#c { transition: filter .07s linear; }',
    'body.cloak-flick #c { filter: contrast(1.15); }',
    '.cloakfx { position: fixed; inset: 0; pointer-events: none; opacity: 0; transition: opacity .07s linear;',
    '  background: radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,.82) 100%); }',
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
  // the badge glyph: a spy's hat brim (no eyes)
  var EYE = '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 30c8 3 28 3 36 0-1 4-10 7-18 7S7 34 6 30z" fill="currentColor"/><path d="M14 29c0-9 3-17 8-17 1 0 2 2 2 2s1-2 2-2c5 0 8 8 8 17-6 2-14 2-20 0z" fill="currentColor"/></svg>';

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
    // the cloak look: a fast fade-flicker going in (about 0.35 s, gaps closing up), the same flicker coming out over
    // the last second
    var el = on ? s.time - s.t : 9;
    var flick = on && ((el < 0.35 && Math.sin(el * el * 260 + el * 40) > (el / 0.35) * 1.6 - 0.8) || (s.t < 1 && Math.sin(s.t * 30) > 0.2));
    // robots glow a dark stealthy blue while hidden (pulsing gently), ink black otherwise
    var RO = IB.Render && IB.Render.robotOutline;
    // while hidden the world goes ink black and grey (render.js CLOAK_WORLD) and robots blaze a bright stealth blue:
    // a thick glowing outline, pulsing, that reads from across the map
    var R = IB.Render, lit = on && !flick ? 1 : on ? 0.45 : 0, pulse = Math.sin(performance.now() * 0.008);
    if (R && R.cloak) { R.cloak.value = lit; R.robotHull.value = 1 + lit * (1.6 + 0.35 * pulse); }
    if (RO) { if (lit) RO.uInk.value.setRGB(0.25 + 0.1 * pulse, 0.78 + 0.12 * pulse, 1.0); else RO.uInk.value.setHex(0x15121C); }
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
