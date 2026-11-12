/* INKBOLT HUD (section 2.4). DOM writes only when a value changes; per-frame calls are cached.
   Layout: objective + gems top-left, scoreboard top-centre, radar + kill feed top-right,
   health + stamina bottom-left, weapon slots + weapon/ammo plate bottom-right (phones: see ui.css). */
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
    shotgun: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M1 6h37v3H1zM10 10h18v3H10zM6 9h6l-3 8H3z" fill="currentColor"/></svg>',
    grenade: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M14 5h12v13H14zM17 1h6v3h-6zM24 2h6v2h-6z" fill="currentColor"/></svg>',
    melee: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M2 12 30 4l4 2-26 10zM30 4l6-2 2 3-4 1z" fill="currentColor"/></svg>',
    shove: '<svg viewBox="0 0 40 20" aria-hidden="true"><path d="M8 6h18l6 4-6 4H8z" fill="currentColor"/></svg>'
  };
  var CLS_NAME = { pistol: 'Pistol', smg: 'SMG', rifle: 'Rifle', sniper: 'Sniper', rocket: 'Launcher', shotgun: 'Shotgun', grenade: 'Grenade', melee: 'Melee', shove: 'Shove' };
  var CLS_SLOT = { pistol: 1, smg: 2, rifle: 3, sniper: 4, rocket: 5, melee: 6, shotgun: 9 };
  H.icon = function (cls) { return ICONS[cls] || ICONS.pistol; };
  H.clsName = function (cls) { return CLS_NAME[cls] || 'Weapon'; };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function touch() { return !!(IB.Input && IB.Input.touch) || document.body.classList.contains('touch-on'); }

  H.init = function () {
    H.el = {
      hud: $('hud'), gems: $('gems'), gemCount: $('gemCount'), scZone: $('scZone'), scTime: $('scTime'), scLeft: $('scLeft'), pips: $('pips'),
      feed: $('feed'), xhair: $('xhair'), hitmark: $('hitmark'), arcs: $('arcs'), health: $('health'), hpFill: $('hpFill'), hpNum: $('hpNum'),
      slots: $('slots'), ammo: $('ammo'), ammoMag: $('ammoMag'), ammoRes: $('ammoRes'), toast: $('toast'), elim: $('elim'),
      elimName: $('elimName'), elimCount: $('elimCount'), elimRetries: $('elimRetries'),
      radar: $('radar'), radarCv: $('radarCv'),
      weapon: $('weapon'), wpnName: $('wpnName'), wpnIcon: $('wpnIcon'), wpnCls: $('wpnCls'), magStrip: $('magStrip'), magFill: $('magFill'),
      prompt: $('prompt'), promptKey: $('promptKey'), promptText: $('promptText'), promptFill: $('promptFill'),
      hpChip: $('hpChip'), stamina: $('stamina'), stFill: $('stFill'), dim: $('dim'), hurt: $('hurt'), hurtFlash: $('hurtFlash'),
      pickup: $('pickup'), pickupIcon: $('pickupIcon'), pickupName: $('pickupName'), pickupLine: $('pickupLine'),
      pauseBtn: $('pauseBtn'),
      lvTag: $('lvTag'), lvNum: $('lvNum'), xpFill: $('xpFill'), xpGain: $('xpGain'), xpNum: $('xpNum'), xpPlus: $('xpPlus'), lvPts: $('lvPts'), lvPtsN: $('lvPtsN'), lvKey: $('lvKey'), menuBtn: $('menuBtn'), menuDot: $('menuDot'),
     
      ticker: $('ticker'), callRows: $('callRows'), notice: $('notice'), noteT: $('noteT'), noteS: $('noteS'),
      toastT: $('toastT'), toastS: $('toastS'), pickupHdL: $('pickupHdL')
    };
    H.arcs = [];
    for (var i = 0; i < 6; i++) {
      var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.innerHTML = '<path class="ink" d="M-44 -124 A131 131 0 0 1 44 -124"/><path d="M-42 -124.5 A131 131 0 0 1 42 -124.5"/><path class="tip" d="M-9 -133 L0 -143 L9 -133 L0 -137Z"/>';
      g.style.opacity = 0; H.el.arcs.appendChild(g);
      H.arcs.push({ g: g, t: 0, ang: 0 });
    }
    H.feedRows = [];
    H.wpn = { id: '', name: '', cls: 'pistol', mag: 0, magSize: 0, reserve: 0, reloading: false, reloadFrac: 0 };
    // touch pause button: feeds the same input flag as Esc
    if (H.el.pauseBtn) {
      var press = function (e) { e.preventDefault(); e.stopPropagation(); if (IB.Input) IB.Input.pausePressed = true; };
      H.el.pauseBtn.addEventListener('touchstart', press, { passive: false });
      H.el.pauseBtn.addEventListener('click', press);
    }
    // touch menu button (loadout / gear / skills): same flag as the Tab key
    if (H.el.menuBtn) {
      var menu = function (e) { e.preventDefault(); e.stopPropagation(); if (IB.Input) IB.Input.menuPressed = true; };
      H.el.menuBtn.addEventListener('touchstart', menu, { passive: false });
      H.el.menuBtn.addEventListener('click', menu);
    }
    if (H.el.radarCv) H.radarCtx = H.el.radarCv.getContext('2d');
    // the desktop layout is drawn for 1920x1080: smaller windows scale it down (phones keep their own sizes)
    var fit = function () { var sc = Math.min(window.innerWidth / 1920, window.innerHeight / 1080); H.el.hud.style.setProperty('--hs', Math.max(0.7, Math.min(1.15, Math.pow(sc, 0.8))).toFixed(3)); };
    fit(); window.addEventListener('resize', fit);
  };
  H.show = function (on) { H.el.hud.hidden = !on; if (!on) { H.el.hurt.classList.remove('low'); H.damageFlash(0); } else if (H.lowHp) H.el.hurt.classList.add('low'); };

  function set(key, val, fn) { if (H.last[key] !== val) { H.last[key] = val; fn(val); } }
  H.reset = function () {
    H.last = {}; H.el.feed.innerHTML = ''; H.feedRows = []; H.lowHp = false; H.hpPct = null;
    for (var k in WL) WL[k] = typeof WL[k] === 'number' ? -2 : null; WL.state = '';
    H.el.hurt.classList.remove('low'); H.damageFlash(0);   // dim is left alone: game.js owns the fade across level loads
    H.el.pickup.hidden = true; H.el.hud.classList.remove('picking'); H.el.prompt.hidden = true; H.el.toast.hidden = true;
    H.el.notice.hidden = true; H.el.hud.classList.remove('noting'); H.el.ticker.innerHTML = ''; H.el.callRows.innerHTML = ''; rows = []; H.lastObj = null;
    pickT = 0; toastT = 0; hitT = 0; ntT = 0;
  };

  /* player XP bar above the health plate: LV badge, progress to the next level (IB.Skills.xpProgress: {lv, into, span,
     frac}), unspent skill points (+ the Tab hint). gain > 0 (XP just earned) flashes the gained stretch of the bar and
     pops a "+N XP" tick (gains close together add up); a level-up snaps the bar back to empty. MAX at the level cap. */
  var xpAt = -1e9, xpSum = 0;
  H.level = function (lv, points, prog, gain) {
    var el = H.el; if (!el.lvTag) return;
    prog = prog || { lv: lv, into: 0, span: 0, frac: 0 };
    var max = !prog.span, pct = max ? 100 : Math.max(0, Math.min(100, prog.frac * 100));
    set('lv', lv + '|' + points, function () {
      el.lvNum.textContent = lv;
      el.lvPts.hidden = !(points > 0); el.lvPtsN.textContent = '+' + points;
      el.lvKey.textContent = touch() ? 'pts' : 'Tab';
      el.lvTag.classList.toggle('max', max);
      if (el.menuDot) el.menuDot.hidden = !(points > 0);
    });
    set('xp', lv + '|' + pct.toFixed(1), function () {
      var prev = H.xpLv === lv ? H.xpPct : null;
      el.xpFill.style.width = pct + '%'; el.xpNum.innerHTML = max ? 'MAX' : Math.floor(prog.into) + '<small>/' + prog.span + ' XP</small>';
      el.lvTag.setAttribute('aria-label', 'Level ' + lv + (max ? ', max level' : ', ' + Math.floor(prog.into) + ' of ' + prog.span + ' XP to level ' + (lv + 1)) + (points > 0 ? ', ' + points + ' skill points to spend' : ''));
      // the stretch just earned glows, then fades (same level only; a level-up starts the bar over)
      el.xpGain.style.left = (prev == null || prev > pct ? 0 : prev) + '%'; el.xpGain.style.width = Math.max(0, pct - (prev == null || prev > pct ? 0 : prev)) + '%';
      el.xpFill.classList.toggle('snap', prev == null);
      H.xpLv = lv; H.xpPct = pct;
    });
    if (gain > 0) {
      var now = performance.now(); xpSum = now - xpAt < 1200 ? xpSum + gain : gain; xpAt = now;
      el.xpPlus.textContent = '+' + Math.round(xpSum) + ' XP';
      el.lvTag.classList.remove('gain'); void el.lvTag.offsetWidth; el.lvTag.classList.add('gain');
    }
  };
  H.gems = function (n, pulse) {
    set('gems', n, function (v) { H.el.gemCount.textContent = Number(v).toLocaleString('en-US'); });
    if (pulse) { H.el.gems.classList.remove('pulse'); void H.el.gems.offsetWidth; H.el.gems.classList.add('pulse'); }
  };
  function mmss(t) { t = Math.max(0, Math.floor(t)); var m = Math.floor(t / 60), s = t % 60; return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s; }
  H.mmss = mmss;
  H.score = function (zone, total, time, left) {
    set('zone', zone + '/' + total, function () { H.el.scZone.innerHTML = 'ZONE <b>' + zone + '/' + total + '</b>'; });
    /* no on-screen timer: the run clock is still kept for the results screen */
    set('left', left, function (v) { H.el.scLeft.innerHTML = '<b>' + v + '</b> LEFT'; H.el.scLeft.classList.toggle('zero', v === 0); });
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
      var pct = Math.max(0, Math.min(100, hp / max * 100));
      H.el.hpNum.textContent = v; H.el.hpFill.style.width = pct + '%';
      // trailing damage chip: holds the old width, then drains after a beat (CSS transition); healing snaps it
      var chip = H.el.hpChip;
      if (chip) {
        var heal = H.hpPct == null || pct > H.hpPct;
        if (heal !== H.chipSnap) { H.chipSnap = heal; chip.classList.toggle('snap', heal); }
        chip.style.width = pct + '%'; H.hpPct = pct;
      }
      var low = hp < 30 && hp > 0;
      H.el.health.classList.toggle('low', low);
      H.el.health.style.setProperty('--ticks', Math.max(2, Math.round(max / 10)));
      if (low !== H.lowHp) { H.lowHp = low; H.el.hurt.classList.toggle('low', low && !H.el.hud.hidden); }
    });
  };

  /* ---------- weapon + ammo ---------- */
  // d: {id, name, cls, mag, magSize, reserve, reloading, reloadFrac}; any field may be omitted to keep the last value.
  // Called every frame: compares primitives and only touches the DOM on change (no closures or string keys).
  var WL = { id: null, name: null, cls: null, melee: null, size: -1, mag: -1, res: -2, fill: -1, state: '', out: null, pfill: -1 };
  H.weapon = function (d) {
    var w = H.wpn, el = H.el, L = WL;
    if (d.id !== undefined) w.id = d.id;
    if (d.name !== undefined) w.name = d.name;
    if (d.cls !== undefined) w.cls = d.cls;
    if (d.level !== undefined) w.level = d.level;
    if (d.mag !== undefined) w.mag = d.mag;
    if (d.magSize !== undefined) w.magSize = d.magSize;
    if (d.reserve !== undefined) w.reserve = d.reserve;
    if (d.reloading !== undefined) w.reloading = d.reloading;
    if (d.reloadFrac !== undefined) w.reloadFrac = d.reloadFrac;
    if (w.id !== L.id || w.name !== L.name || w.cls !== L.cls || w.level !== L.level) {
      L.id = w.id; L.name = w.name; L.cls = w.cls; L.level = w.level;
      el.wpnName.textContent = String(CLS_NAME[w.cls] || 'Weapon').toUpperCase();
      // the name in its tier colour from Tuned up ('Cobalt Rivet' in blue: core/gunskins.js names)
      var tc = IB.WeaponDrops && IB.WEAPONS && IB.WEAPONS[w.id] && w.cls !== 'melee' && w.cls !== 'shove' ? IB.WeaponDrops.tierOf(w.id) : null;
      el.wpnName.style.color = tc && tc.rank > 0 ? tc.color : '';
      el.wpnIcon.innerHTML = H.icon(w.cls);
      var gunLv = w.level > 0 && w.cls !== 'melee' && w.cls !== 'shove';   // gun item level (core/gunlevel.js)
      el.wpnCls.innerHTML = (gunLv ? 'LV ' + w.level : '') + (tc && tc.rank > 0 && tc.name ? (gunLv ? ' · ' : '') + '<b>' + esc(tc.name) + '</b>' : '');
    }
    var melee = w.cls === 'melee' || w.cls === 'shove';
    if (melee !== L.melee) { L.melee = melee; el.weapon.classList.toggle('melee', melee); L.mag = -1; }
    var size = Math.max(1, w.magSize || w.mag || 1);
    if (size !== L.size) { L.size = size; el.magStrip.style.setProperty('--seg', (size > 40 ? 100 / Math.ceil(size / 5) : 100 / size) + '%'); }
    var res = w.reserve == null ? Infinity : w.reserve;
    if (w.mag !== L.mag || res !== L.res) {
      L.mag = w.mag; L.res = res;
      el.ammoMag.textContent = melee ? '–' : w.mag;
      el.ammoRes.innerHTML = melee ? '' : '<i>/</i>' + (res === Infinity ? '∞' : res);
    }
    var frac = Math.max(0, Math.min(1, w.mag / size));
    var state = melee ? 'ok' : w.reloading ? 'reload' : w.mag === 0 ? 'empty' : frac <= 0.25 ? 'low' : 'ok';
    var fill = w.reloading ? Math.max(0, Math.min(1, w.reloadFrac || 0)) : frac;
    var fq = Math.round(fill * 200);
    if (fq !== L.fill) { L.fill = fq; el.magFill.style.clipPath = 'inset(0 ' + ((1 - fq / 200) * 100).toFixed(1) + '% 0 0)'; }
    var outOfAll = state === 'empty' && res === 0;
    if (state !== L.state || outOfAll !== L.out) {
      L.state = state; L.out = outOfAll;
      el.weapon.classList.toggle('low', state === 'low');
      el.weapon.classList.toggle('empty', state === 'empty');
      el.weapon.classList.toggle('reloading', state === 'reload');
      el.prompt.hidden = !(state === 'empty' || state === 'reload' || (state === 'low' && res !== 0));
      el.prompt.className = 'prompt ' + state;
      if (state === 'reload') { el.promptKey.hidden = true; el.promptText.textContent = 'Reloading'; }
      else if (outOfAll) { el.promptKey.hidden = true; el.promptText.textContent = 'No ammo · swap weapon'; }
      else { el.promptKey.hidden = false; el.promptKey.textContent = 'R'; el.promptText.textContent = state === 'low' ? 'Low ammo' : 'Reload'; }
    }
    if (state === 'reload') { var pq = Math.round(fill * 100); if (pq !== L.pfill) { L.pfill = pq; el.promptFill.style.width = pq + '%'; el.prompt.style.setProperty('--p', pq + '%'); } }
  };
  // legacy: keeps name/class from the last HUD.weapon call
  var AMMO = { mag: 0, reserve: 0, magSize: 0 };
  H.ammo = function (mag, res) { AMMO.mag = mag; AMMO.reserve = res; AMMO.magSize = Math.max(H.wpn.magSize || 0, mag); H.weapon(AMMO); };

  /* equipment row over the weapon plate: the melee weapon on V and the frag cans on G (count; -1 = not owned yet).
     The phone melee / grenade buttons show with them. */
  var KL = { m: undefined, g: undefined };
  H.kit = function (meleeName, grenades) {
    if (meleeName === KL.m && grenades === KL.g) return;
    KL.m = meleeName; KL.g = grenades;
    var k = $('kit'); if (!k) return;
    k.hidden = !meleeName && grenades < 0;
    $('kitMelee').hidden = !meleeName;
    if (meleeName) { $('kitMeleeName').textContent = String(meleeName).toUpperCase(); $('kitMeleeIc').innerHTML = ICONS.melee; }
    $('kitGren').hidden = grenades < 0;
    if (grenades >= 0) { $('kitGrenN').textContent = '\u00D7' + grenades; $('kitGrenIc').innerHTML = ICONS.grenade; $('kitGren').classList.toggle('none', grenades === 0); }
    var tm = $('tMelee'), tg = $('tGren'), tn = $('tGrenN');
    if (tm) tm.hidden = !meleeName;
    if (tg) { tg.hidden = grenades < 0; tg.classList.toggle('none', grenades === 0); }
    if (tn) tn.textContent = grenades > 0 ? grenades : '';
  };

  /* list: [{slot, cls, name?, on}] */
  H.slots = function (list) {
    var key = list.map(function (s) { return s.slot + s.cls + (s.on ? '*' : ''); }).join(',');
    set('slots', key, function () {
      H.el.slots.innerHTML = list.map(function (s) {
        return '<div class="wd s' + s.slot + (s.on ? ' on' : '') + '"' + (s.name ? ' title="' + esc(s.name) + '"' : '') + '><em class="nu">' + s.slot + '</em><span>' + H.icon(s.cls) + '</span></div>';
      }).join('');
    });
  };

  H.objective = function () {};   // no on-screen objective
  H.mission = function () {};

  /* spreadDeg, vfovDeg, hidden */
  H.crosshair = function (spreadDeg, vfov, hidden) {
    var gap = 4 + Math.tan(spreadDeg * Math.PI / 180) / Math.tan(vfov * Math.PI / 360) * (window.innerHeight / 2);
    gap = Math.round(Math.min(60, gap));
    set('xh', gap + (hidden ? 'h' : ''), function () { H.el.xhair.style.setProperty('--gap-x', gap + 'px'); H.el.xhair.classList.toggle('hide', !!hidden); });
  };
  var hitT = 0;
  H.hit = function (kind) {
    var el = H.el.hitmark;
    el.setAttribute('class', 'hitmark');
    void el.getBoundingClientRect();
    el.setAttribute('class', 'hitmark on' + (kind === 'core' ? ' core' : '') + (kind === 'kill' ? ' kill' : ''));
    hitT = kind === 'kill' ? 0.32 : 0.14;
    if (kind === 'kill') { H.el.xhair.classList.remove('kick'); void H.el.xhair.offsetWidth; H.el.xhair.classList.add('kick'); }
  };
  /* angle: radians, 0 = straight ahead, positive = to the right */
  H.arc = function (angle) {
    var a = H.arcs[0]; for (var i = 1; i < H.arcs.length; i++) if (H.arcs[i].t < a.t) a = H.arcs[i];
    a.t = 0.8; a.ang = angle;
    a.g.setAttribute('transform', 'rotate(' + (angle * 180 / Math.PI).toFixed(1) + ')');
  };

  /* kill feed: weapon icon, weapon name, robot name, gem gain. weaponName is optional:
     it falls back to the current weapon's name when the class matches. */
  H.feed = function (cls, name, gems, weaponName) {
    if (!weaponName && H.wpn && H.wpn.cls === cls) weaponName = H.wpn.name;
    var row = document.createElement('div');
    row.className = 'kf';
    row.innerHTML = '<span class="feed-wpn">' + esc(H.clsName(cls)) + '</span>' +
      '<b class="feed-bot d">' + esc(name) + '</b>' + (gems ? '<em class="feed-gem nu">+' + gems + '</em>' : '');
    H.el.feed.insertBefore(row, H.el.feed.firstChild);
    H.feedRows.unshift({ el: row, t: 0 });
    while (H.feedRows.length > 4) { var r = H.feedRows.pop(); r.el.remove(); }
  };
  var toastT = 0;
  /* "E  Take ..." prompt for armory loot within reach (touch: the USE button shows instead of the key) */
  var USE = { on: false, text: '', color: '' };
  H.use = function (d) {
    var el = H.el.use || (H.el.use = document.getElementById('usePrompt')), tb = H.el.tUse || (H.el.tUse = document.getElementById('tUse'));
    if (!el) return;
    var on = !!d;
    if (on !== USE.on) { USE.on = on; el.hidden = !on; if (tb) tb.hidden = !on; }
    H.peek('rack', on && d.gun ? d.gun : on && d.item ? { item: d.item, uid: d.uid, wx: d.wx, wy: d.wy, wz: d.wz } : null);
    if (on && (d.text !== USE.text || d.color !== USE.color)) {
      USE.text = d.text; USE.color = d.color;
      var tk = ('ontouchstart' in window); el.classList.toggle('tk', tk);
      el.querySelector('.key').textContent = tk ? 'USE' : d.key;
      el.querySelector('.ut').textContent = d.text;
      el.querySelector('.us').textContent = d.sub || '';
      el.style.setProperty('--rar', d.color || '#12C7B6');
    }
  };
  /* item card for a gun or a piece of gear in the world you walk up to / look at (what E would take: source 'use';
     armory rack: 'rack'; gun on the floor: 'drop'; gear on the floor: 'gear'; in that order). spec for a gun
     {id, tier, level, roll, melee}, for gear {item, uid}; plus the world point wx, wy, wz the card floats over; or null.
     The card (IB.GearUI.peekHtml / peekItemHtml) is rebuilt only when the target changes; a picture still being drawn
     swaps in by itself (IB.Thumbs). */
  var PEEK = { use: null, rack: null, drop: null, gear: null, key: '' };
  function peekCur() { return PEEK.use || PEEK.rack || PEEK.drop || PEEK.gear; }
  /* the card floats in the world over its gun: project the gun's point each frame, anchor the card's bottom centre
     there, scale with distance, keep it on screen */
  var _pv = null;
  H.peekTrack = function () {
    var p = peekCur(), el = H.el.peek, cam = IB.Render && IB.Render.camera;
    if (!p || !el || el.hidden || !cam || p.wx === undefined) return;
    _pv = _pv || new THREE.Vector3(); _pv.set(p.wx, p.wy, p.wz).project(cam);
    if (_pv.z > 1) { el.style.opacity = 0; return; }
    var W = window.innerWidth, Hh = window.innerHeight, x = (_pv.x * 0.5 + 0.5) * W, y = (-_pv.y * 0.5 + 0.5) * Hh;
    var pl = IB.Game && IB.Game.player, d = pl ? Math.hypot(p.wx - pl.x, p.wz - pl.z) : 4, k = Math.max(0.55, Math.min(1, 3.2 / Math.max(1, d)));
    var w = el.offsetWidth * k, h = el.offsetHeight * k;
    x = Math.max(w / 2 + 8, Math.min(W - w / 2 - 8, x)); y = Math.max(h + 8, Math.min(Hh - 8, y));
    el.style.opacity = 1;
    el.style.transform = 'translate(' + (x - w / 2).toFixed(1) + 'px,' + (y - h).toFixed(1) + 'px) scale(' + k.toFixed(3) + ')';
  };
  H.peek = function (src, spec) {
    PEEK[src] = spec || null;
    var p = peekCur(), el = H.el.peek;
    var key = !p ? '' : p.item ? ['item', p.uid, p.item.name, p.item.rarity, p.item.level, IB.Game && IB.Game.ws ? IB.Game.ws.cur : ''].join('|') :
      [p.id, p.tier, p.level, p.melee ? 1 : 0, p.roll ? p.roll.mag + p.roll.elem : '', IB.WeaponDrops ? IB.WeaponDrops.tierOf(p.id).id + IB.WeaponDrops.ownLevel(p.id) : ''].join('|');
    if (key === PEEK.key) return;
    PEEK.key = key;
    if (!el) {
      if (!p) return;
      el = H.el.peek = document.createElement('div'); el.className = 'peek-card'; el.id = 'peekCard';
      (document.getElementById('hud') || document.body).appendChild(el);
    }
    el.hidden = !p;
    if (p) {
      var GUi = IB.GearUI, html = !GUi ? '' : p.item ? (GUi.peekItemHtml ? GUi.peekItemHtml(IB.Game, p.item) : '') : (GUi.peekHtml ? GUi.peekHtml(IB.Game, p) : '');
      el.innerHTML = html; el.hidden = !html; el.style.opacity = 0;   // placed by peekTrack before it shows
      el.style.setProperty('--rar', p.item ? IB.LOOT.rarityById[p.item.rarity].color : p.melee ? '#FFC23A' : IB.WeaponDrops ? IB.WeaponDrops.tier(p.tier).color : '#2EEAD8');
    }
  };
  H.peekKey = function () { return PEEK.key; };
  /* Messages go to one of four lanes so a 1 s status never fights a level-up:
       'call'       small hairline callout under the crosshair (weapon / body status)
       'tick[:tone]' pickup ticker right of the crosshair; tone hp | ammo | gear
       'note'       notice card in the top-right loot slot (needs the player to open Tab)
       'banner'     big hairline banner, upper centre (default) */
  var rows = [], ntT = 0;
  function keyify(t) { return esc(t).replace(/\((Tab|V|E|G|R|F|B)\)/g, '<span class="k">$1</span>'); }
  function splitAt(text) {   // 'Title · rest' | 'Title: rest' | 'Title. rest'
    var m = /^(.*?)(?: · |: |\. )(.*)$/.exec(text);
    return m ? [m[1], m[2].replace(/\.$/, '')] : [text.replace(/\.$/, ''), ''];
  }
  function addRow(box, cls, html, life, max, key) {
    for (var i = rows.length - 1; i >= 0; i--) if (rows[i].key === key && rows[i].box === box) { rows[i].t = 0; rows[i].life = life; rows[i].el.classList.remove('out'); return; }
    var el = document.createElement('div'); el.className = cls; el.innerHTML = html;
    box.insertBefore(el, box.firstChild);
    rows.unshift({ el: el, box: box, t: 0, life: life, key: key });
    var n = 0; for (i = 0; i < rows.length; i++) if (rows[i].box === box && ++n > max) { rows[i].el.remove(); rows.splice(i, 1); i--; }
  }
  H.toast = function (text, secs, lane) {
    var ln = String(lane || 'banner').split(':'), kind = ln[0], life = secs || 2.5, P;
    if (kind === 'tick') { addRow(H.el.ticker, 'tkr ' + (ln[1] || ''), '<i></i>' + keyify(text), life, 4, 't' + text); return; }
    if (kind === 'call') { P = splitAt(text); addRow(H.el.callRows, 'c1' + (/^(Winded|No )/.test(text) ? ' warn' : ''), keyify(P[0]) + (P[1] ? '<small>' + keyify(P[1]) + '</small>' : ''), life, 3, 'c' + text); return; }
    if (kind === 'note') {
      P = splitAt(text); var el = H.el;
      el.noteT.textContent = P[0]; el.noteS.innerHTML = keyify(P[1]); el.hud.classList.add('noting');
      el.notice.hidden = false; el.notice.classList.remove('out', 'on'); void el.notice.offsetWidth; el.notice.classList.add('on'); ntT = life; return;
    }
    var lv = /^LEVEL UP/i.test(text); P = lv ? (function () { var a = text.split(' · '); return [a.slice(0, 2).join(' · '), a.slice(2).join(' · ')]; })() : splitAt(text);
    var b = H.el.toast; H.el.toastT.textContent = lv ? 'Level up · ' + P[0].split(' · ')[1] : P[0]; H.el.toastS.innerHTML = keyify(P[1]);
    b.className = 'banner' + (lv || /clear/i.test(P[0]) ? ' yl' : '');
    b.hidden = false; toastT = life; b.style.animation = 'none'; void b.offsetWidth; b.style.animation = '';
  };
  H.elim = function (show, name, count, retries) {
    H.el.elim.hidden = !show;
    if (show) {
      set('elim', name + count + ':' + retries, function () {
        H.el.elimName.textContent = name; H.el.elimCount.textContent = 'Back in ' + count; H.el.elimRetries.textContent = 'Retries left ' + retries;
      });
    } else H.last.elim = null;
  };

  /* new-weapon banner */
  var pickT = 0;
  H.pickup = function (name, cls, slot) {
    slot = slot || CLS_SLOT[cls];
    H.el.pickupIcon.innerHTML = H.icon(cls);
    H.el.pickupName.textContent = String(name).toUpperCase();
    var how = cls === 'melee' ? (touch() ? 'tap the blade button' : 'press V to strike · B: next melee') :
      cls === 'grenade' ? (touch() ? 'tap the can button to throw' : 'press G to throw') :
      touch() ? 'tap swap to equip' : (slot ? 'press ' + slot + ' to equip' : 'equipped');
    H.el.pickupHdL.textContent = 'New ' + H.clsName(cls).toLowerCase().replace('smg', 'SMG');
    H.el.pickupLine.innerHTML = esc(how.charAt(0).toUpperCase() + how.slice(1)).replace(/^Press (\w) /, 'Press <span class="k">$1</span> ');
    H.el.toast.hidden = true; toastT = 0;
    H.el.hud.classList.add('picking');
    H.el.pickup.hidden = false; H.el.pickup.classList.remove('out', 'on'); void H.el.pickup.offsetWidth; H.el.pickup.classList.add('on');
    pickT = 3.2;
  };

  /* sprint stamina 0..1; hidden when full */
  H.stamina = function (f, sliding) {
    var q = Math.round(Math.max(0, Math.min(1, f)) * 100);
    set('st', q + (sliding ? 1000 : 0), function () {
      H.el.stamina.classList.toggle('on', q < 100);
      H.el.stamina.classList.toggle('slide', !!sliding);
      H.el.stamina.classList.toggle('low', q < 25);
      H.el.stFill.style.width = q + '%';
    });
  };

  /* full-screen ink darkening 0..1 (waypath walk-in and fade back). The HUD and touch buttons fade out over the last 40 %. */
  H.dim = function (f) {
    f = Math.max(0, Math.min(1, f || 0));
    var q = Math.round(f * 500) / 500;
    set('dim', q, function () {
      var el = H.el.dim;
      el.style.visibility = q > 0 ? 'visible' : 'hidden';
      el.style.setProperty('--tone', Math.pow(q, 1.35).toFixed(3));
      el.style.setProperty('--vig', Math.min(1, q * 1.8).toFixed(3));
      var hudA = q <= 0.6 ? 1 : Math.max(0, 1 - (q - 0.6) / 0.35);
      document.body.style.setProperty('--hud-a', hudA.toFixed(3));
    });
  };

  /* hurt: Alert Red ink hatching at the screen edges, 0..1 */
  H.damageFlash = function (f) {
    var q = Math.round(Math.max(0, Math.min(1, f || 0)) * 100);
    set('dmg', q, function () { H.el.hurtFlash.style.opacity = (q / 100).toFixed(2); });
  };

  /* ---------- radar ---------- */
  // d: {px, pz, yaw, range, robots:[{x,z,alert}], gates:[{x,z,open}], pickups:[{x,z,kind}], exit:{x,z}|null}
  // yaw 0 faces -Z; positive yaw turns left. Up on the radar is the view direction.
  var PT = { x: 0, y: 0, edge: false };
  var PICK = { health: '#5BCF4A', ammo: '#5B9BF5', weapon: '#FFB21E', gem: '#2EEAD8', rockets: '#FF7A2E' };
  H.radar = function (d) {
    var cv = H.el.radarCv, ctx = H.radarCtx; if (!ctx || !d) return;
    if (H.el.radar.hidden) H.el.radar.hidden = false;
    var css = cv.clientWidth || 160, dpr = Math.min(2, window.devicePixelRatio || 1), px = Math.round(css * dpr);
    if (cv.width !== px) { cv.width = px; cv.height = px; }
    var S = px, c = S / 2, R = S / 2 - 2 * dpr, range = d.range || 30, k = R / range;
    var sy = Math.sin(d.yaw || 0), cy = Math.cos(d.yaw || 0);
    var fx = -sy, fz = -cy, rx = cy, rz = -sy;
    function map(x, z, clamp) {
      var dx = x - d.px, dz = z - d.pz, u = (dx * rx + dz * rz) * k, v = -(dx * fx + dz * fz) * k;
      var m = Math.max(Math.abs(u), Math.abs(v)), lim = R - 8 * dpr, edge = false;   // square map: clamp by the larger axis
      if (m > lim) { if (!clamp) return null; u *= lim / m; v *= lim / m; edge = true; }
      PT.x = c + u; PT.y = c + v; PT.edge = edge; return PT;
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, S, S);
    // glass face clipped to a cut-corner square; the frame is drawn last
    var cut = Math.round(S * 0.09);
    ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(0, 0, S, S, S * 0.05); else ctx.rect(0, 0, S, S); ctx.save(); ctx.clip();
    ctx.fillStyle = 'rgba(5, 8, 14, .62)'; ctx.fillRect(0, 0, S, S);
    // grid: 10 m hairlines
    ctx.strokeStyle = 'rgba(120, 220, 230, 0)'; ctx.lineWidth = dpr;
    var step = 10 * k;
    ctx.beginPath();
    for (var g = c % step; g < S; g += step) { ctx.moveTo(g, 0); ctx.lineTo(g, S); ctx.moveTo(0, g); ctx.lineTo(S, g); }
    ctx.stroke();
    // view cone: teal, fading out with range
    var cg = ctx.createRadialGradient(c, c, 0, c, c, R * 1.1);
    cg.addColorStop(0, 'rgba(244, 247, 251, .24)'); cg.addColorStop(1, 'rgba(244, 247, 251, .06)');
    ctx.fillStyle = cg;
    ctx.beginPath(); ctx.moveTo(c, c); ctx.arc(c, c, R * 1.5, -Math.PI / 2 - 0.62, -Math.PI / 2 + 0.62); ctx.closePath(); ctx.fill();
    // range rings
    ctx.strokeStyle = 'rgba(244, 247, 251, .4)'; ctx.lineWidth = 1.5 * dpr; ctx.setLineDash([4 * dpr, 4 * dpr]);
    ctx.beginPath(); ctx.arc(c, c, R / 2, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
    var i, p;
    // gates: teal bars (closed = dark-cored)
    var gates = d.gates || [];
    for (i = 0; i < gates.length; i++) {
      p = map(gates[i].x, gates[i].z, true);
      ctx.save(); ctx.translate(p.x, p.y);
      ctx.fillStyle = 'rgba(8, 12, 22, .85)'; ctx.fillRect(-7 * dpr, -3.5 * dpr, 14 * dpr, 7 * dpr);
      ctx.fillStyle = gates[i].open ? '#2EEAD8' : '#1C8F86'; ctx.fillRect(-5.5 * dpr, -2 * dpr, 11 * dpr, 4 * dpr);
      if (!gates[i].open) { ctx.fillStyle = 'rgba(8, 12, 22, .9)'; ctx.fillRect(-1 * dpr, -2 * dpr, 2 * dpr, 4 * dpr); }
      ctx.restore();
    }
    // pickups
    var pk = d.pickups || [];
    for (i = 0; i < pk.length; i++) {
      p = map(pk[i].x, pk[i].z, pk[i].kind === 'loot'); if (!p) continue;   // loot stays pinned to the edge
      if (pk[i].kind === 'loot') { diamond(ctx, p.x, p.y, 7 * dpr, 'rgba(8, 12, 22, .9)'); diamond(ctx, p.x, p.y, 4.8 * dpr, pk[i].color || '#FFFDF7'); continue; }
      ctx.fillStyle = 'rgba(8, 12, 22, .9)'; ctx.fillRect(p.x - 4.5 * dpr, p.y - 4.5 * dpr, 9 * dpr, 9 * dpr);
      ctx.fillStyle = pk[i].color || PICK[pk[i].kind] || '#FFFDF7'; ctx.fillRect(p.x - 3 * dpr, p.y - 3 * dpr, 6 * dpr, 6 * dpr);
    }
    // exit: teal hex bolt, clamped to the edge
    if (d.exit) {
      p = map(d.exit.x, d.exit.z, true);
      hex(ctx, p.x, p.y, 8 * dpr, 'rgba(8, 12, 22, .9)'); hex(ctx, p.x, p.y, 5.6 * dpr, '#2EEAD8');
      ctx.fillStyle = 'rgba(8, 12, 22, .9)'; ctx.beginPath(); ctx.arc(p.x, p.y, 1.8 * dpr, 0, Math.PI * 2); ctx.fill();
    }
    // robots: red pips with a soft glow (alerted ones bigger and brighter)
    var rb = d.robots || [];
    for (i = 0; i < rb.length; i++) {
      var r = rb[i]; p = map(r.x, r.z, false); if (!p) continue;
      var rad = (r.alert ? 4.4 : 3.6) * dpr * (S > 140 * dpr ? 1 : 0.85);
      ctx.fillStyle = r.alert ? 'rgba(255, 75, 62, .28)' : 'rgba(255, 255, 255, .14)'; ctx.beginPath(); ctx.arc(p.x, p.y, rad * 2.1, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(8, 12, 22, .9)'; ctx.beginPath(); ctx.arc(p.x, p.y, rad + 1.2 * dpr, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = r.alert ? '#FF5A52' : '#D9605A'; ctx.beginPath(); ctx.arc(p.x, p.y, rad, 0, Math.PI * 2); ctx.fill();
    }
    // player arrow
    ctx.save(); ctx.translate(c, c);
    ctx.beginPath(); ctx.moveTo(0, -8.5 * dpr); ctx.lineTo(6.5 * dpr, 7 * dpr); ctx.lineTo(0, 3.5 * dpr); ctx.lineTo(-6.5 * dpr, 7 * dpr); ctx.closePath();
    ctx.lineJoin = 'round'; ctx.lineWidth = 2.5 * dpr; ctx.strokeStyle = 'rgba(8, 12, 22, .9)'; ctx.stroke();
    ctx.fillStyle = '#FFFFFF'; ctx.fill();
    ctx.restore();
    ctx.restore();
  };
  function octo(ctx, S, cut, inset) {
    var a = inset, b = S - inset;
    ctx.beginPath(); ctx.moveTo(a + cut, a); ctx.lineTo(b - cut * 0.4, a); ctx.lineTo(b, a + cut * 0.4); ctx.lineTo(b, b - cut); ctx.lineTo(b - cut, b);
    ctx.lineTo(a + cut * 0.4, b); ctx.lineTo(a, b - cut * 0.4); ctx.lineTo(a, a + cut); ctx.closePath();
  }
  function diamond(ctx, x, y, r, col) { ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath(); ctx.fill(); }
  function hex(ctx, x, y, r, col) {
    ctx.fillStyle = col; ctx.beginPath();
    for (var i = 0; i < 6; i++) { var a = i * Math.PI / 3; ctx[i ? 'lineTo' : 'moveTo'](x + Math.cos(a) * r, y + Math.sin(a) * r); }
    ctx.closePath(); ctx.fill();
  }


  H.tick = function (dt) {
    if (hitT > 0) { hitT -= dt; if (hitT <= 0) H.el.hitmark.setAttribute('class', 'hitmark'); }
    if (toastT > 0) { toastT -= dt; if (toastT <= 0) H.el.toast.hidden = true; }
    if (ntT > 0) { ntT -= dt; if (ntT <= 0.3 && !H.el.notice.classList.contains('out')) H.el.notice.classList.add('out'); if (ntT <= 0) { H.el.notice.hidden = true; H.el.hud.classList.remove('noting'); } }
    for (var q = rows.length - 1; q >= 0; q--) {
      var rw = rows[q]; rw.t += dt;
      if (rw.t > rw.life - 0.25 && !rw.el.classList.contains('out')) rw.el.classList.add('out');
      if (rw.t > rw.life) { rw.el.remove(); rows.splice(q, 1); }
    }
    if (pickT > 0) {
      pickT -= dt;
      if (pickT <= 0.3 && !H.el.pickup.classList.contains('out')) H.el.pickup.classList.add('out');
      if (pickT <= 0) { H.el.pickup.hidden = true; H.el.hud.classList.remove('picking'); }
    }
    for (var i = 0; i < H.arcs.length; i++) {
      var a = H.arcs[i];
      if (a.t > 0) { a.t -= dt; a.g.style.opacity = Math.max(0, Math.min(1, a.t / 0.3)).toFixed(2); }
    }
    for (i = H.feedRows.length - 1; i >= 0; i--) {
      var r = H.feedRows[i]; r.t += dt;
      if (r.t > 4 && !r.out) { r.out = true; r.el.classList.add('out'); }
      if (r.t > 4.3) { r.el.remove(); H.feedRows.splice(i, 1); }
    }
  };
})(window.IB = window.IB || {});
