/* INKBOLT skill runtime: the combat side of the skill tree (core/skills.js effects()). game.js calls these hooks from
   startLevel (begin), shoot (hitMul, onHit), onKill, hurt (hurtMul, closeCall), playFrame (update).
   Stat skills (magazine, reload, recoil, health, stamina, magnet, fire rate) are applied in game.startLevel. */
(function (IB) {
  'use strict';
  var SF = IB.SkillFX = { fx: null, shocked: [], chainDepth: 0, closeUsed: {} };
  var BLUE = 0x2F7BEA, PALE = 0x8ED2FF;

  SF.begin = function (skills) {
    SF.fx = IB.Skills.effects(skills || {});
    SF.shocked.length = 0; SF.chainDepth = 0; SF.closeUsed = {};
    return SF.fx;
  };
  // skills changed mid-level (Tab menu): new effects, but Close Call stays spent for the zones it was used in
  SF.refresh = function (skills) { SF.fx = IB.Skills.effects(skills || {}); return SF.fx; };
  // multiplier on one bullet's damage (Heavy Ink, Core Dump)
  SF.hitMul = function (zone) { var f = SF.fx; if (!f) return 1; return f.dmgMul * (zone === 'core' ? f.coreMul : 1); };

  // shock damage-over-time: the loot system's IB.Status when it is there, a small local tick otherwise
  function shock(r, dps, dur) {
    if (IB.Status && IB.Status.apply) { IB.Status.apply(r, 'shock', dps, dur); return; }
    // same rule as IB.Status: every hit adds dps x dur to the robot's pool, which drains over the duration
    for (var i = 0; i < SF.shocked.length; i++) if (SF.shocked[i].r === r) { var e = SF.shocked[i]; e.pool += dps * dur; e.t = Math.max(e.t, dur); return; }
    SF.shocked.push({ r: r, pool: dps * dur, t: dur, acc: 0, tick: 0.25, puff: 0 });
  }
  SF.shock = shock;
  function num(x, y, z, n, kind) { if (IB.FX && IB.FX.damageNumber) IB.FX.damageNumber(x, y, z, n, kind); }

  /* after a bullet landed: r robot, dmg final damage, killed, end hit point, onKill callback */
  SF.onHit = function (r, dmg, zone, killed, end, onKill) {
    var f = SF.fx; if (!f) return;
    if (f.shock && !killed && r.on) shock(r, IB.Skills.shockDps(f, dmg), f.shockTime);
    if (f.arc && zone === 'core') arc(r, end, dmg * f.arcFrac, onKill);
  };
  // Lightning Rod: a bolt from the hit robot into the nearest others
  function arc(src, end, dmg, onKill) {
    var f = SF.fx, list = [];
    IB.AI.robots.forEach(function (o) {
      if (o === src || !o.on || o.state === 'pose' || o.state === 'spawn') return;
      var d = Math.hypot(o.x - src.x, o.z - src.z); if (d <= f.arcRange) list.push({ o: o, d: d });
    });
    list.sort(function (a, b) { return a.d - b.d; });
    list.slice(0, f.arcTargets).forEach(function (e) {
      var o = e.o, oy = o.y + 0.6;
      if (IB.FX) { IB.FX.tracer(end.x, end.y, end.z, o.x, oy, o.z); IB.FX.puff(o.x, oy, o.z, 4, BLUE, 0.08, 0.22, 2.4); IB.FX.puff(o.x, oy, o.z, 2, PALE, 0.05, 0.14, 3); }
      num(o.x, oy + 0.5, o.z, dmg, 'shock');
      if (!IB.AI.damage(o, dmg, {}, onKill) && o.on) shock(o, IB.Skills.shockDps(f, dmg), f.shockTime);
    });
    if (list.length && IB.FX && IB.FX.word && Math.random() < 0.35) IB.FX.word('ZAP', end.x, end.y + 0.5, end.z, 1.2);
    if (list.length && IB.Audio) IB.Audio.play('boltHit', { pos: src, gain: 0.5, pitch: 1.6 });
  }

  /* a robot the player wrecked: Salvage Bolts repair, Chain Reaction burst (bursts may chain, 4 deep at most) */
  SF.onKill = function (r, player, onKill) {
    var f = SF.fx; if (!f) return;
    if (f.leech && player && player.alive) player.health = Math.min(player.maxHp, player.health + f.leech);
    if (f.chain && SF.chainDepth < 4) {
      var dmg = (r.maxHp || 30) * f.chainFrac, R = f.chainRadius;
      if (IB.FX) { IB.FX.puff(r.x, 0.6, r.z, 8, 0x15121C, 0.2, 0.6, 4); IB.FX.puff(r.x, 0.6, r.z, 5, 0xFFB21E, 0.1, 0.3, 4.5); }
      if (IB.FX && IB.FX.word && SF.chainDepth === 0 && Math.random() < 0.3) IB.FX.word('KRUNCH', r.x, 1.4, r.z, 1.3);
      SF.chainDepth++;
      IB.AI.robots.forEach(function (o) {
        if (o === r || !o.on || o.state === 'pose' || o.state === 'spawn') return;
        var dx = o.x - r.x, dz = o.z - r.z, d = Math.hypot(dx, dz); if (d > R) return;
        num(o.x, o.y + 1, o.z, dmg, 'hit');
        IB.AI.damage(o, dmg, { kx: dx / (d || 1) * 4, kz: dz / (d || 1) * 4 }, onKill);
      });
      SF.chainDepth--;
    }
  };

  // damage the player takes is scaled by this (Tin Titan)
  SF.hurtMul = function () { return SF.fx ? SF.fx.dmgTakenMul : 1; };
  // Close Call: true when the skill saves the player this time (once per zone)
  SF.closeCall = function (p, zone) {
    var f = SF.fx; if (!f || !f.closeCall || SF.closeUsed[zone]) return false;
    SF.closeUsed[zone] = true; p.health = 1; p.protect = 2;
    return true;
  };
  // Tin Titan repair after regenDelay seconds without damage
  SF.regen = function (p, dt) {
    var f = SF.fx; if (!f || !f.regen || !p.alive || p.lastHurt <= f.regenDelay) return;
    p.health = Math.min(p.maxHp, p.health + f.regen * dt);
  };

  // local shock tick (only while IB.Status is missing)
  SF.update = function (dt, onKill) {
    for (var i = SF.shocked.length - 1; i >= 0; i--) {
      var e = SF.shocked[i], r = e.r;
      if (!r.on) { SF.shocked.splice(i, 1); continue; }
      var drain = e.t > dt ? e.pool * dt / e.t : e.pool;
      e.pool -= drain; e.acc += drain; e.t -= dt; e.tick -= dt; e.puff -= dt;
      if (e.puff <= 0 && IB.FX) { e.puff = 0.18; IB.FX.puff(r.x + (Math.random() - 0.5) * 0.5, r.y + 0.4 + Math.random() * 0.6, r.z + (Math.random() - 0.5) * 0.5, 1, Math.random() < 0.5 ? BLUE : PALE, 0.04, 0.12, 2); }
      // damage lands in 0.25 s ticks so numbers read as a rhythm, not a blur
      if (e.tick <= 0 || e.t <= 0) {
        var n = e.acc; e.acc = 0; e.tick = 0.25;
        if (n > 0) { num(r.x, r.y + 1.1, r.z, n, 'shock'); IB.AI.damage(r, n, {}, onKill); }
      }
      if (e.t <= 0 || !r.on) SF.shocked.splice(i, 1);
    }
  };
  SF.clear = function () { SF.shocked.length = 0; };
})(window.IB = window.IB || {});
