/* INKBOLT status effects on robots: damage over time ('shock' blue sparks, 'acid' green drips). Burns last 5-7 s:
   Electrify 5 s, Hydrate / Hazard 5 s after the last exposure, acid muzzles 5 / 6 / 7 s by rarity.
     IB.Status.apply(robot, kind, dps, dur)   adds dps x dur damage to the robot's pool of that kind and keeps it
                                              burning for at least dur seconds (re-applying stacks the pool, so an
                                              SMG and a sniper get the same share of acid per point of damage)
     IB.Status.update(dt, onKill)             drains every pool evenly over its remaining time; ticks land every
                                              0.4 s through AI.damage (kills go through the normal onKill path) and
                                              pop a coloured damage number
   Pooled entries, no allocation per frame. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var S = IB.Status = { list: [], TICK: 0.4, CAP: 64 };
  var KINDS = {
    shock: { colors: [0x5FC2FF, 0xFFFDF7, 0x2F7BEA], sound: 'zap' },
    acid: { colors: [0x7BE34A, 0xC8FF8A, 0x3FAE2A], sound: 'sizzle' }
  };
  S.KINDS = KINDS;
  for (var i = 0; i < S.CAP; i++) S.list.push({ on: false, r: null, kind: '', pool: 0, left: 0, acc: 0, tick: 0, fx: 0, total: 0, wait: 0 });

  function entry(r, kind) {
    var free = null;
    for (var i = 0; i < S.CAP; i++) {
      var e = S.list[i];
      if (e.on && e.r === r && e.kind === kind) return e;
      if (!e.on && !free) free = e;
    }
    if (!free) return null;
    free.on = true; free.r = r; free.kind = kind; free.pool = 0; free.left = 0; free.acc = 0; free.tick = S.TICK * 0.5; free.fx = 0; free.total = 0; free.wait = 0;
    return free;
  }
  /* returns the status entry (or null when the robot cannot take it) */
  S.apply = function (r, kind, dps, dur) {
    if (!r || !r.on || r.rogue > 0 || r.state === 'pose' || r.state === 'spawn' || !KINDS[kind] || !(dps > 0) || !(dur > 0)) return null;
    var e = entry(r, kind); if (!e) return null;
    e.pool += dps * dur;
    e.left = Math.max(e.left, dur);
    return e;
  };
  S.has = function (r, kind) { for (var i = 0; i < S.CAP; i++) { var e = S.list[i]; if (e.on && e.r === r && (!kind || e.kind === kind)) return true; } return false; };
  S.active = function () { var n = 0; for (var i = 0; i < S.CAP; i++) if (S.list[i].on) n++; return n; };
  // drop every status on one robot (a wreck turned rogue by Handy Helpers fights on clean)
  S.clearRobot = function (r) { for (var i = 0; i < S.CAP; i++) { var e = S.list[i]; if (e.on && e.r === r) { e.on = false; e.r = null; } } };
  S.clear = function () { for (var i = 0; i < S.CAP; i++) { S.list[i].on = false; S.list[i].r = null; } };

  function robotTop(r) { var v = IB.AI.VIS[r.type]; return r.y + (v ? v.y1 : 0.9); }
  function deal(e, onKill) {
    var r = e.r, amt = e.acc; e.acc = 0;
    if (amt <= 0 || !r.on) return;
    e.total += amt;
    if (IB.FX && IB.FX.damageNumber) IB.FX.damageNumber(r.x, robotTop(r) + 0.15, r.z, amt, e.kind);
    IB.AI.damage(r, amt, {}, onKill);
  }
  // per-kind visuals, a few particles per second per robot
  function sparks(e, dt) {
    var r = e.r, v = IB.AI.VIS[r.type], K = KINDS[e.kind], FX = IB.FX; if (!FX || !v) return;
    e.fx -= dt; if (e.fx > 0) return;
    var rad = v.radius, y0 = r.y + v.y0, y1 = r.y + v.y1, a = Math.random() * Math.PI * 2;
    var x = r.x + Math.cos(a) * rad * 0.9, z = r.z + Math.sin(a) * rad * 0.9, y = y0 + (y1 - y0) * (0.2 + Math.random() * 0.8);
    if (IB.Boom && IB.Boom.ready) {
      // comic arcs crawling over the body + sparks (shock); drips, popping bubbles and sizzle steam (acid)
      e.fx = e.kind === 'shock' ? 0.07 : 0.08;
      IB.Boom.statusFx(e.kind, r, x, y, z, rad, y0, y1);
      FX.puff(x, y, z, 1, K.colors[(Math.random() * 2) | 0], 0.07, 0.16, e.kind === 'shock' ? 3 : 0.5, e.kind === 'shock' ? 0 : 6);
      if (e.kind === 'acid' && Math.random() < 0.15 && IB.Audio) IB.Audio.play('sizzle', { pos: r, gain: 0.25 });
      return;
    }
    if (e.kind === 'shock') {
      e.fx = 0.06;
      FX.puff(x, y, z, 2, K.colors[(Math.random() * 2) | 0], 0.09, 0.2, 4.5);
      // a little zig-zag arc jumping across the body now and then
      if (Math.random() < 0.35 && FX.tracer) {
        var b = a + 1.2 + Math.random() * 1.6, mx = r.x + Math.cos((a + b) / 2) * rad * 1.25, mz = r.z + Math.sin((a + b) / 2) * rad * 1.25, my = y + (Math.random() - 0.5) * 0.3;
        FX.tracer(x, y, z, mx, my, mz);
        FX.tracer(mx, my, mz, r.x + Math.cos(b) * rad * 0.9, y + (Math.random() - 0.5) * 0.3, r.z + Math.sin(b) * rad * 0.9);
      }
    } else {
      e.fx = 0.07;
      // drips fall off the body; now and then a bubble pops up off the top
      FX.puff(x, y, z, 1, K.colors[Math.random() < 0.7 ? 0 : 2], 0.1, 0.16, 0.5, 9);
      if (Math.random() < 0.35) FX.puff(r.x + (Math.random() - 0.5) * rad, y1, r.z + (Math.random() - 0.5) * rad, 1, K.colors[1], 0.07, 0.2, 0.4, -2);
    }
  }
  S.update = function (dt, onKill) {
    if (!(dt > 0)) return;
    for (var i = 0; i < S.CAP; i++) {
      var e = S.list[i]; if (!e.on) continue;
      var r = e.r;
      if (!r || !r.on || r.state === 'pose' || r.rogue > 0) { e.on = false; e.r = null; continue; }
      var take = e.left > dt ? e.pool * dt / e.left : e.pool;
      e.pool -= take; e.acc += take; e.left -= dt; e.tick -= dt;
      sparks(e, dt);
      // a long, thin burn lands once at least a whole point has built up, so the coloured numbers stay honest
      // (or after 1.2 s at the latest)
      e.wait += dt;
      if (e.tick <= 0 || e.left <= 0) { e.tick = S.TICK; if (e.acc >= 1 || e.wait >= 1.2 || e.left <= 0) { e.wait = 0; deal(e, onKill); } }
      if (e.left <= 0 || e.pool <= 1e-6) { if (e.acc > 0) deal(e, onKill); e.on = false; e.r = null; }
    }
  };
})(window.IB = window.IB || {});
