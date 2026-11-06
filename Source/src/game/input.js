/* INKBOLT input: desktop (pointer lock, drag fallback, WASD) and touch (floating left stick, right drag look, buttons). */
(function (IB) {
  'use strict';
  var I = IB.Input = {
    mx: 0, mz: 0, lookDX: 0, lookDY: 0, fire: false, aim: false, sprint: false,
    jumpPressed: false, firePressed: false, reloadPressed: false, meleePressed: false, pausePressed: false,
    slotPressed: 0, wheel: 0, keys: {}, locked: false, dragging: false, touch: false, enabled: false, lastLook: 0
  };
  var canvas;

  I.init = function (cv) {
    canvas = cv;
    I.touch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0 && matchMedia('(pointer: coarse)').matches);
    window.addEventListener('keydown', function (e) {
      if (e.repeat) { if (I.enabled && gameKey(e.code)) e.preventDefault(); return; }
      I.keys[e.code] = true;
      if (!I.enabled) return;
      switch (e.code) {
        case 'Space': I.jumpPressed = true; break;
        case 'KeyR': I.reloadPressed = true; break;
        case 'KeyF': I.meleePressed = true; break;
        case 'Escape': case 'KeyP': I.pausePressed = true; break;
        case 'KeyC': case 'ControlLeft': I.slidePressed = true; break;
        case 'Tab': I.menuPressed = true; break;   // field kit (loadout, gear, skills); Tab never moves focus in play
        default: if (/^Digit[1-9]$/.test(e.code)) I.slotPressed = +e.code.slice(5);
      }
      if (gameKey(e.code)) e.preventDefault();
    });
    window.addEventListener('keyup', function (e) { I.keys[e.code] = false; });
    window.addEventListener('blur', function () { I.keys = {}; I.fire = false; I.aim = false; });
    // mouse
    canvas.addEventListener('mousedown', function (e) {
      if (!I.enabled || I.touch) return;
      if (!I.locked) { I.requestLock(); I.dragging = true; }
      if (e.button === 0) { I.fire = true; I.firePressed = true; }
      if (e.button === 2) I.aim = true;
    });
    window.addEventListener('mouseup', function (e) { if (e.button === 0) I.fire = false; if (e.button === 2) I.aim = false; I.dragging = false; });
    window.addEventListener('mousemove', function (e) {
      if (!I.enabled || I.touch) return;
      if (I.locked || I.dragging) { I.lookDX += e.movementX || 0; I.lookDY += e.movementY || 0; }
    });
    canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    window.addEventListener('wheel', function (e) { if (I.enabled) I.wheel += Math.sign(e.deltaY); }, { passive: true });
    document.addEventListener('pointerlockchange', function () {
      var was = I.locked;
      I.locked = document.pointerLockElement === canvas;
      if (was && !I.locked && I.enabled && I.onUnlock) I.onUnlock();
    });
    if (I.touch) I.buildTouch();
  };
  function gameKey(c) { return /^(Space|Key[WASDQRFPC]|Arrow|Digit|ShiftLeft|ShiftRight|ControlLeft|Tab)/.test(c); }
  I.requestLock = function () {
    if (I.touch || !canvas.requestPointerLock) return;
    try { var p = canvas.requestPointerLock(); if (p && p.catch) p.catch(function () { /* drag-to-look fallback */ }); } catch (e) { /* fallback */ }
  };
  I.releaseLock = function () { if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); };

  I.update = function () {
    if (I.touch) return;
    var k = I.keys;
    var x = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0);
    var z = (k.KeyS || k.ArrowDown ? 1 : 0) - (k.KeyW || k.ArrowUp ? 1 : 0);
    I.mx = x; I.mz = z; I.sprint = !!(k.ShiftLeft || k.ShiftRight);
    I.crouch = !!(k.KeyC || k.ControlLeft);
  };
  I.endFrame = function () {
    I.lookDX = 0; I.lookDY = 0; I.jumpPressed = false; I.firePressed = false; I.reloadPressed = false;
    I.meleePressed = false; I.pausePressed = false; I.slotPressed = 0; I.wheel = 0; I.swapPressed = false; I.slidePressed = false; I.menuPressed = false;
  };
  I.reset = function () { I.fire = I.aim = false; I.mx = I.mz = 0; I.keys = {}; I.endFrame(); if (I.stick) I.stick.id = null; };

  // ---------------- touch ----------------
  I.buildTouch = function () {
    var root = document.getElementById('touch');
    root.innerHTML =
      '<div class="stick" id="stick"><div class="stick-knob" id="stickKnob"></div></div>' +
      '<button class="tbtn tfire" id="tFire" aria-label="Fire">' + svgFire() + '</button>' +
      '<button class="tbtn taim" id="tAim" aria-label="Aim">' + svgAim() + '</button>' +
      '<button class="tbtn treload" id="tReload" aria-label="Reload">R</button>' +
      '<button class="tbtn tswap" id="tSwap" aria-label="Swap weapon">' + svgSwap() + '</button>' +
      '<button class="tbtn tjump" id="tJump" aria-label="Jump">' + svgJump() + '</button>' +
      '<button class="tbtn tslide" id="tSlide" aria-label="Slide or crouch" style="width:56px;height:56px;right:calc(var(--sar) + 200px);bottom:calc(var(--sab) + 140px)">' + svgSlide() + '</button>';
    var stick = I.stick = { id: null, ox: 0, oy: 0, el: document.getElementById('stick'), knob: document.getElementById('stickKnob') };
    var look = { id: null, x: 0, y: 0 };
    function hold(id, down, up) {
      var el = document.getElementById(id);
      el.addEventListener('touchstart', function (e) { e.preventDefault(); e.stopPropagation(); el.classList.add('down'); down(); for (var i = 0; i < e.changedTouches.length; i++) el._tid = e.changedTouches[i].identifier; }, { passive: false });
      var end = function (e) { e.preventDefault(); el.classList.remove('down'); if (up) up(); };
      el.addEventListener('touchend', end, { passive: false }); el.addEventListener('touchcancel', end, { passive: false });
      // fire button also steers look while held (thumb drag)
      el.addEventListener('touchmove', function (e) {
        if (id !== 'tFire') return;
        e.preventDefault();
        for (var i = 0; i < e.changedTouches.length; i++) { var t = e.changedTouches[i]; if (el._lx !== undefined) { I.lookDX += (t.clientX - el._lx) * 1.6; I.lookDY += (t.clientY - el._ly) * 1.6; } el._lx = t.clientX; el._ly = t.clientY; }
      }, { passive: false });
      el.addEventListener('touchend', function () { el._lx = undefined; });
    }
    hold('tFire', function () { I.fire = true; I.firePressed = true; }, function () { I.fire = false; });
    hold('tAim', function () { I.aim = !I.aim; });
    hold('tReload', function () { I.reloadPressed = true; });
    hold('tSwap', function () { I.swapPressed = true; I.wheel += 1; });
    hold('tJump', function () { I.jumpPressed = true; });
    hold('tSlide', function () { I.slidePressed = true; I.crouch = true; }, function () { I.crouch = false; });
    var layer = document.getElementById('touchLayer');
    layer.addEventListener('touchstart', function (e) {
      if (!I.enabled) return;
      e.preventDefault();
      for (var i = 0; i < e.changedTouches.length; i++) {
        var t = e.changedTouches[i];
        if (t.clientX < window.innerWidth * 0.45 && stick.id === null) {
          stick.id = t.identifier; stick.ox = t.clientX; stick.oy = t.clientY;
          stick.el.style.left = t.clientX + 'px'; stick.el.style.top = t.clientY + 'px'; stick.el.classList.add('on');
          stick.knob.style.transform = 'translate(-50%,-50%)';
        } else if (look.id === null) { look.id = t.identifier; look.x = t.clientX; look.y = t.clientY; }
      }
    }, { passive: false });
    layer.addEventListener('touchmove', function (e) {
      e.preventDefault();
      for (var i = 0; i < e.changedTouches.length; i++) {
        var t = e.changedTouches[i];
        if (t.identifier === stick.id) {
          var dx = t.clientX - stick.ox, dy = t.clientY - stick.oy, R = 56, d = Math.hypot(dx, dy);
          var k = d > R ? R / d : 1;
          I.mx = dx / R * k; I.mz = dy / R * k;
          I.sprint = d > R * 0.9 && dy < -R * 0.5;
          stick.knob.style.transform = 'translate(calc(-50% + ' + (dx * k) + 'px), calc(-50% + ' + (dy * k) + 'px))';
        } else if (t.identifier === look.id) {
          I.lookDX += (t.clientX - look.x) * 1.6; I.lookDY += (t.clientY - look.y) * 1.6; look.x = t.clientX; look.y = t.clientY;
        }
      }
    }, { passive: false });
    var end = function (e) {
      for (var i = 0; i < e.changedTouches.length; i++) {
        var t = e.changedTouches[i];
        if (t.identifier === stick.id) { stick.id = null; I.mx = I.mz = 0; I.sprint = false; stick.el.classList.remove('on'); }
        if (t.identifier === look.id) look.id = null;
      }
    };
    layer.addEventListener('touchend', end); layer.addEventListener('touchcancel', end);
  };
  function svgFire() { return '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="12" fill="none" stroke="currentColor" stroke-width="4"/><path d="M24 4v10M24 34v10M4 24h10M34 24h10" stroke="currentColor" stroke-width="4"/></svg>'; }
  function svgAim() { return '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="14" fill="none" stroke="currentColor" stroke-width="4"/><circle cx="24" cy="24" r="3" fill="currentColor"/></svg>'; }
  function svgSwap() { return '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M10 18h26l-7-7M38 30H12l7 7" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/></svg>'; }
  function svgSlide() { return '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 34h26l8-6M14 26l8-8 8 4" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/><circle cx="30" cy="12" r="4" fill="currentColor"/></svg>'; }
  function svgJump() { return '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 8 10 24h8v14h12V24h8z" fill="currentColor"/></svg>'; }
})(window.IB = window.IB || {});
