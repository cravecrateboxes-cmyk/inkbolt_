/* INKBOLT skill runtime: the combat side of the skill tree (core/skills.js effects(), data in data/skills.js).
   game.js calls these hooks: begin (startLevel), refresh (Tab menu closed), hitMul + onHit (shoot), hurtMul (hurt),
   regen + update (playFrame), tryCloak (F), clear (level reset). Stat skills (magazine, fire rate, reload / swap,
   health, stamina) are applied in game.js applySkillStats, player.js and weapons.js.
     Electrify       every hit adds 25% of its damage as shock over 5 s (IB.Status pools)
     Stream          chance a bullet punches through into the robot behind it for x2
     Ricochet        chance a bullet bounces into another robot within 10 m (line of sight) for 60%, with a tracer
     Hazard          chance a hit leaves a bubbling acid pool on the floor for 5 s; ground robots in it burn (acid, 5 s)
     Hydrate         chance a hit coats the robot in electrified liquid for 6 s (wet blue sheen, drips); every robot within
                     3 m of it takes shock over time (5 s burn)
     Undercover      F: invisible for 5 s (ai.js AI.cloak: robots lose you and search), 30 s cooldown after it wears off
     Healthy / Tank  max health %, damage resistance, repair after 4 s without damage
     Handy Helpers   ai.js AI.rogueChance: a wreck may turn rogue instead and fight for you for 15 s
     Chain Reaction  a hit on a robot with 2+ others within 4 m: 10% chance (1 s cooldown) the group blows up for 40% of
                     each one's max health (core/skills.js chainDamage: never all of them at once)
   Secondary hits (pierce, ricochet) carry Electrify but roll none of the chance skills, so nothing cascades. */
(function (IB) {
  'use strict';
  var SF = IB.SkillFX = { fx: null, pools: [], coats: [], cloakT: 0, cloakCd: 0, chainCd: 0, force: {}, stats: { pierce: 0, ricochet: 0, pools: 0, coats: 0, chains: 0 } };
  var PALE = 0x8ED2FF, WET = 0x5FC2FF, ACID = 0x7BE34A, ACID_LT = 0xC8FF8A;
  var POOL_CAP = 10, COAT_CAP = 10, TICK = 0.25;
  for (var i = 0; i < POOL_CAP; i++) SF.pools.push({ on: false, x: 0, z: 0, t: 0, life: 5, R: 1.3, dps: 0, tick: 0, puff: 0, seed: 0 });
  for (i = 0; i < COAT_CAP; i++) SF.coats.push({ on: false, r: null, t: 0, dps: 0, tick: 0, drip: 0 });

  function AI() { return IB.AI; }
  function world() { return IB.Game && IB.Game.level && IB.Game.level.world; }
  function num(x, y, z, n, kind) { if (IB.FX && IB.FX.damageNumber) IB.FX.damageNumber(x, y, z, n, kind); }
  function boom() { return IB.Boom && IB.Boom.ready ? IB.Boom : null; }
  // SF.force[id] overrides a chance (test hooks: 1 = always, 0 = never)
  function chance(id, p) { var f = SF.force[id]; return Math.random() < (f !== undefined ? f : p); }
  function fightable(o) { return o && o.on && o.state !== 'pose' && o.state !== 'spawn' && !(o.rogue > 0); }
  function mid(o) { var v = AI().VIS[o.type]; return o.y + (v ? (v.y0 + v.y1) * 0.5 : 0.5); }
  function top(o) { var v = AI().VIS[o.type]; return o.y + (v ? v.y1 : 0.9) + 0.22; }

  function applyAI() {
    var f = SF.fx, A = AI(); if (!A || !f) return;
    A.rogueChance = SF.force.rogue !== undefined ? SF.force.rogue : f.rogue;
    A.rogueTime = f.rogueTime; A.rogueDmgMul = f.rogueDmgMul;
  }
  SF.begin = function (skills) {
    SF.fx = IB.Skills.effects(skills || {});
    SF.clear();
    ensureMesh();
    applyAI();
    return SF.fx;
  };
  // skills changed mid-level (Tab menu): new numbers; an Undercover cloak in progress ends if the skill was refunded
  SF.refresh = function (skills) {
    SF.fx = IB.Skills.effects(skills || {});
    if (!SF.fx.cloak) endCloak();
    applyAI();
    return SF.fx;
  };
  // multiplier on one bullet's damage (Heavy Ink)
  SF.hitMul = function () { return SF.fx ? SF.fx.dmgMul : 1; };

  function shock(r, dps, dur) { if (IB.Status && IB.Status.apply) IB.Status.apply(r, 'shock', dps, dur); }
  SF.shock = shock;
  function electrify(r, dmg, killed) {
    var f = SF.fx;
    if (f.shock && !killed && r.on && !(r.rogue > 0)) shock(r, IB.Skills.shockDps(f, dmg), f.shockTime);
  }
  // a pierce / ricochet hit on o: damage, number, sparks, Electrify
  function secondary(o, d, x, y, z, dx, dy, dz, kind, onKill) {
    var killed = AI().damage(o, d, { kx: dx * 3, kz: dz * 3 }, onKill);
    num(o.x, top(o), o.z, d, kind);
    if (IB.Boom) IB.Boom.robotHit(o, x, y, z, dx, dy, dz, 'body', killed);
    if (IB.Audio) IB.Audio.play('hit', { pos: o, gain: 0.7, pitch: 1.15 });
    electrify(o, d, killed);
    return killed;
  }

  /* after a bullet landed. r robot, dmg final damage, killed, end hit point, onKill callback,
     shot {ox, oy, oz, dx, dy, dz, t (hit distance), wt (wall distance), def} for the player's own bullets (null = secondary) */
  SF.onHit = function (r, dmg, zone, killed, end, onKill, shot) {
    var f = SF.fx; if (!f) return;
    electrify(r, dmg, killed);
    if (!shot) return;
    var ex = end.x, ey = end.y, ez = end.z;
    if (f.pierce > 0 && chance('stream', f.pierce)) pierce(r, dmg, ex, ey, ez, shot, onKill);
    if (f.ricochet > 0 && chance('ricochet', f.ricochet)) ricochet(r, dmg, ex, ey, ez, shot, onKill);
    if (f.pool > 0 && chance('hazard', f.pool)) addPool(r.x, r.z, IB.Skills.poolDps(f, dmg));
    if (f.coat > 0 && r.on && !(r.rogue > 0) && chance('hydrate', f.coat)) addCoat(r, IB.Skills.coatDps(f, dmg));
    if (f.chain > 0 && SF.chainCd <= 0) chainReaction(r, ex, ez, onKill);
  };

  // Stream: the bullet carries on past r into whatever robot is behind it (up to the wall it would have hit)
  function pierce(r, dmg, ex, ey, ez, shot, onKill) {
    var rem = shot.wt - shot.t - 0.05; if (rem < 0.3) return;
    var sx = ex + shot.dx * 0.05, sy = ey + shot.dy * 0.05, sz = ez + shot.dz * 0.05;
    var h = AI().raycast(sx, sy, sz, shot.dx, shot.dy, shot.dz, rem, r);
    if (!h) return;
    var o = h.robot, t = h.t, hx = sx + shot.dx * t, hy = sy + shot.dy * t, hz = sz + shot.dz * t;
    SF.stats.pierce++;
    if (IB.Boom) IB.Boom.tracer(ex, ey, ez, hx, hy, hz, { cls: 'sniper' });
    secondary(o, dmg * SF.fx.pierceMul, hx, hy, hz, shot.dx, shot.dy, shot.dz, 'crit', onKill);
    if (IB.Boom && Math.random() < 0.35) IB.Boom.word('POW!', hx, hy + 0.7, hz, 1.2);
  }
  // Ricochet: bounce off the hit point into the nearest other robot within range that the hit point can see
  function ricochet(r, dmg, ex, ey, ez, shot, onKill) {
    var f = SF.fx, A = AI(), w = world(), best = null, bd = f.ricochetRange * f.ricochetRange;
    for (var i = 0; i < A.robots.length; i++) {
      var o = A.robots[i]; if (o === r || !fightable(o)) continue;
      var dx = o.x - ex, dz = o.z - ez, oy = mid(o), dy = oy - ey, d2 = dx * dx + dy * dy + dz * dz;
      if (d2 >= bd) continue;
      if (w && !w.los(ex, ey, ez, o.x, oy, o.z)) continue;
      bd = d2; best = o;
    }
    if (!best) return;
    var by = mid(best), L = Math.sqrt(bd) || 1;
    SF.stats.ricochet++;
    var B = boom();
    if (B) { B.tracer(ex, ey, ez, best.x, by, best.z, shot.def); B.sparks(ex, ey, ez, (best.x - ex) / L, (by - ey) / L, (best.z - ez) / L, 5, 0xFFE15A); }
    else if (IB.FX) IB.FX.tracer(ex, ey, ez, best.x, by, best.z);
    if (IB.Audio) IB.Audio.play('clank', { pos: best, gain: 0.5, pitch: 1.8 });
    secondary(best, dmg * f.ricochetFrac, best.x, by, best.z, (best.x - ex) / L, (by - ey) / L, (best.z - ez) / L, 'hit', onKill);
  }

  // ---------------- Hazard: acid pools ----------------
  function addPool(x, z, dps) {
    var f = SF.fx, free = null, oldest = null;
    for (var i = 0; i < POOL_CAP; i++) {
      var p = SF.pools[i];
      if (p.on && Math.hypot(p.x - x, p.z - z) < p.R * 1.2) { p.t = Math.min(p.t, 0.25); p.life = f.poolTime + p.t; p.dps = Math.max(p.dps, dps); return p; }   // tops up a pool already there
      if (!p.on && !free) free = p;
      if (p.on && (!oldest || p.life - p.t < oldest.life - oldest.t)) oldest = p;
    }
    var q = free || oldest;
    q.on = true; q.x = x; q.z = z; q.t = 0; q.life = f.poolTime; q.R = f.poolRadius; q.dps = dps; q.tick = TICK; q.puff = 0; q.seed = Math.random();
    SF.stats.pools++;
    if (IB.FX) IB.FX.puff(x, 0.15, z, 5, ACID, 0.1, 0.3, 2.2, 3);
    if (IB.Audio) IB.Audio.play('sizzle', { pos: q, gain: 0.6 });
    return q;
  }
  function updatePools(dt) {
    var f = SF.fx, A = AI();
    for (var i = 0; i < POOL_CAP; i++) {
      var p = SF.pools[i]; if (!p.on) continue;
      p.t += dt; if (p.t >= p.life) { p.on = false; continue; }
      p.tick -= dt; p.puff -= dt;
      if (p.puff <= 0 && IB.FX) {
        // bubbles rise and pop off the surface
        p.puff = 0.12 + Math.random() * 0.16;
        var a = Math.random() * Math.PI * 2, rr = Math.sqrt(Math.random()) * p.R * 0.75;
        IB.FX.puff(p.x + Math.cos(a) * rr, 0.06, p.z + Math.sin(a) * rr, 1, Math.random() < 0.6 ? ACID_LT : ACID, 0.05, 0.13, 0.35, -1.6);
      }
      if (p.tick > 0 || !f) continue;
      p.tick = TICK;
      // ground robots standing in it: acid that keeps burning for poolBurn s after they walk out
      for (var k = 0; k < A.robots.length; k++) {
        var o = A.robots[k]; if (!fightable(o) || o.y > 0.6) continue;
        var v = A.VIS[o.type]; if (v && v.flying) continue;
        if (Math.hypot(o.x - p.x, o.z - p.z) > p.R + (v ? v.radius * 0.6 : 0.2)) continue;
        if (IB.Status) IB.Status.apply(o, 'acid', p.dps * TICK / f.poolBurn, f.poolBurn);
      }
    }
  }

  // ---------------- Hydrate: electrified coats ----------------
  function addCoat(r, dps) {
    var f = SF.fx, free = null;
    for (var i = 0; i < COAT_CAP; i++) {
      var c = SF.coats[i];
      if (c.on && c.r === r) { c.t = f.coatTime; c.dps = Math.max(c.dps, dps); r.wet = c.t; return c; }
      if (!c.on && !free) free = c;
    }
    if (!free) return null;
    free.on = true; free.r = r; free.t = f.coatTime; free.dps = dps; free.tick = 0.05; free.drip = 0;
    r.wet = free.t;
    SF.stats.coats++;
    var y = mid(r);
    if (IB.FX) { IB.FX.puff(r.x, y + 0.3, r.z, 6, WET, 0.08, 0.22, 2.2, 6); IB.FX.puff(r.x, y, r.z, 3, 0xFFFDF7, 0.05, 0.12, 2.5, 4); }
    if (IB.Boom && IB.Boom.ready) IB.Boom.zap(r.x, y, r.z, 0.7, WET);
    if (IB.Audio) IB.Audio.play('zap', { pos: r, gain: 0.5 });
    return free;
  }
  function updateCoats(dt) {
    var f = SF.fx, A = AI(), B = boom();
    for (var i = 0; i < COAT_CAP; i++) {
      var c = SF.coats[i]; if (!c.on) continue;
      var r = c.r;
      if (!r || !r.on || r.rogue > 0) { if (r) r.wet = 0; c.on = false; c.r = null; continue; }
      c.t -= dt; r.wet = Math.max(0, c.t);
      if (c.t <= 0) { c.on = false; c.r = null; r.wet = 0; continue; }
      var v = A.VIS[r.type], rad = v ? v.radius : 0.4, y0 = r.y + (v ? v.y0 : 0.1), y1 = r.y + (v ? v.y1 : 0.9);
      c.drip -= dt;
      if (c.drip <= 0 && IB.FX) {
        // drips run off the body and fall; now and then a little crackle of blue
        c.drip = 0.07 + Math.random() * 0.06;
        var a = Math.random() * Math.PI * 2;
        IB.FX.puff(r.x + Math.cos(a) * rad * 0.85, y0 + (y1 - y0) * (0.3 + Math.random() * 0.7), r.z + Math.sin(a) * rad * 0.85, 1, Math.random() < 0.7 ? WET : PALE, 0.05, 0.09, 0.3, 11);
        if (B && Math.random() < 0.12) B.arc(r.x + Math.cos(a) * rad, y0 + (y1 - y0) * Math.random(), r.z + Math.sin(a) * rad, r.x - Math.cos(a) * rad, y0 + (y1 - y0) * Math.random(), r.z - Math.sin(a) * rad, WET, 0.09, 0.4);
      }
      c.tick -= dt; if (c.tick > 0 || !f) continue;
      c.tick = TICK;
      var ry = (y0 + y1) * 0.5;
      for (var k = 0; k < A.robots.length; k++) {
        var o = A.robots[k]; if (!fightable(o)) continue;
        var dx = o.x - r.x, dz = o.z - r.z, oy = mid(o), dy = oy - ry;
        if (dx * dx + dy * dy + dz * dz > f.coatRadius * f.coatRadius) continue;
        if (IB.Status) IB.Status.apply(o, 'shock', c.dps * TICK / f.coatBurn, f.coatBurn);
        if (o !== r && B && Math.random() < 0.3) B.arc(r.x, ry, r.z, o.x, oy, o.z, WET, 0.12, 0.45);   // the charge jumps across
      }
    }
  }

  // ---------------- Chain Reaction ----------------
  var _grp = [], _hp = [], _max = [];
  function chainReaction(r, ex, ez, onKill) {
    var f = SF.fx, A = AI(), cx = r.on ? r.x : ex, cz = r.on ? r.z : ez, R = f.chainRadius, others = 0;
    _grp.length = 0;
    for (var i = 0; i < A.robots.length; i++) {
      var o = A.robots[i]; if (!fightable(o)) continue;
      if (Math.hypot(o.x - cx, o.z - cz) > R) continue;
      _grp.push(o); if (o !== r) others++;
    }
    if (others < f.chainMin || !chance('chain', f.chain)) return;
    SF.chainCd = f.chainCooldown; SF.stats.chains++;
    _hp.length = _max.length = 0;
    _grp.forEach(function (o) { _hp.push(o.hp); _max.push(o.maxHp); });
    var dmg = IB.Skills.chainDamage(f, _hp, _max), B = boom();
    if (B) { B.chainBurst(cx, cz, R); B.word('KA-BOOM!', cx, 2.2, cz, 2.2, true); }
    if (IB.Audio) IB.Audio.play('boom', { pos: { x: cx, z: cz }, gain: 1 });
    if (IB.Game && IB.Game.addTrauma) IB.Game.addTrauma(0.3);
    var list = _grp.slice();
    list.forEach(function (o, k) {
      if (!o.on || o.rogue > 0) return;
      var dx = o.x - cx, dz = o.z - cz, d = Math.hypot(dx, dz) || 1;
      if (B) B.explode(o.x, mid(o), o.z, o.type, 0.7, true);   // a comic blast on every robot of the group
      num(o.x, top(o), o.z, dmg[k], 'crit');
      AI().damage(o, dmg[k], { stagger: true, kx: dx / d * 5, kz: dz / d * 5 }, onKill);
    });
  }

  // ---------------- player side ----------------
  // damage the player takes is scaled by this (Tank)
  SF.hurtMul = function () { return SF.fx ? SF.fx.dmgTakenMul : 1; };
  SF.closeCall = function () { return false; };   // retired skills (old saves are refunded)
  SF.onKill = function () { };
  // Healthy (% of max health) + Tank (flat) repair after regenDelay s without damage
  SF.regen = function (p, dt) {
    var f = SF.fx; if (!f || !p.alive || p.lastHurt <= f.regenDelay || p.health >= p.maxHp) return;
    var r = IB.Skills.regenRate(f, p.maxHp); if (r > 0) p.health = Math.min(p.maxHp, p.health + r * dt);
  };

  // ---------------- Undercover ----------------
  SF.cloakState = function () {
    var f = SF.fx, owned = !!(f && f.cloak);
    return { owned: owned, active: SF.cloakT > 0, t: SF.cloakT, cd: SF.cloakCd, time: f ? f.cloakTime : 5, cooldown: f ? f.cloakCooldown : 30,
      ready: owned && SF.cloakT <= 0 && SF.cloakCd <= 0 };
  };
  SF.tryCloak = function (p) {
    var f = SF.fx; if (!f || !f.cloak || !p || !p.alive) return false;
    if (SF.cloakT > 0 || SF.cloakCd > 0) { if (IB.Audio) IB.Audio.play('dry', { gain: 0.6 }); return false; }
    SF.cloakT = f.cloakTime; SF.cloakCd = f.cloakCooldown;   // the cooldown runs once the cloak wears off
    if (AI()) AI().cloak(true, p.x, p.z);
    if (IB.FX) IB.FX.puff(p.x, 1.0, p.z, 10, 0x15121C, 0.2, 0.6, 2.6);
    if (IB.Audio) { IB.Audio.play('shove', { pitch: 0.5, gain: 0.9 }); IB.Audio.play('ui', { pitch: 0.6 }); }
    return true;
  };
  function endCloak() {
    if (SF.cloakT > 0) { SF.cloakT = 0; if (IB.Audio) IB.Audio.play('uiBack', { pitch: 0.7 }); }
    if (AI() && AI().cloaked) AI().cloak(false);
  }
  SF.endCloak = endCloak;

  SF.update = function (dt, onKill, p) {
    if (!(dt > 0)) return;
    if (SF.cloakT > 0) { SF.cloakT -= dt; if (SF.cloakT <= 0 || (p && !p.alive)) endCloak(); }
    else if (SF.cloakCd > 0) SF.cloakCd = Math.max(0, SF.cloakCd - dt);
    SF.chainCd = Math.max(0, SF.chainCd - dt);
    updatePools(dt);
    updateCoats(dt);
  };
  SF.syncMesh = function (t) { syncMesh(t); };
  SF.clear = function () {
    SF.pools.forEach(function (p) { p.on = false; });
    SF.coats.forEach(function (c) { if (c.r) c.r.wet = 0; c.on = false; c.r = null; });
    SF.cloakT = 0; SF.cloakCd = 0; SF.chainCd = 0;
    if (AI()) AI().cloaked = false;
    if (SF.mesh) { SF.mesh.count = 0; SF.mesh.visible = false; }
  };
  // a launcher's Acid rocket (game/launchers.js): an acid pool of its own size and life, whatever the skills
  SF.acidPool = function (x, z, dps, life, R) { if (!SF.fx) return null; var q = addPool(x, z, dps); if (life) q.life = q.t + life; if (R) q.R = R; return q; };
  SF.activePools = function () { return SF.pools.filter(function (p) { return p.on; }).length; };
  SF.activeCoats = function () { return SF.coats.filter(function (c) { return c.on; }).length; };

  // ---------------- acid pool decal: one instanced draw, a bubbling comic puddle in a shader ----------------
  var POOL_VERT = [
    'attribute vec4 aPool;',
    'varying vec2 vUv; varying vec4 vP;',
    'void main() { vUv = uv; vP = aPool; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4( position, 1.0 ); }'
  ].join('\n');
  // aPool: x seed, y alpha, z spread (0..1 as it splashes out), w unused
  var POOL_FRAG = [
    'uniform float uTime;',
    'varying vec2 vUv; varying vec4 vP;',
    'float hash( vec2 p ) { return fract( sin( dot( p, vec2( 127.1, 311.7 ) ) ) * 43758.5453 ); }',
    'void main() {',
    '  vec2 p = vUv * 2.0 - 1.0; float r = length( p ), a = atan( p.y, p.x ), s = vP.x * 6.283;',
    '  float edge = ( 0.8 + 0.07 * sin( a * 3.0 + s ) + 0.05 * sin( a * 5.0 + s * 2.3 + uTime * 0.8 ) + 0.035 * sin( a * 9.0 - uTime * 1.4 + s ) ) * vP.z;',
    '  if ( r > edge ) discard;',
    '  float k = r / max( edge, 0.001 );',
    '  vec3 ink = vec3( 0.08, 0.07, 0.11 ), lt = vec3( 0.78, 1.0, 0.54 ), md = vec3( 0.48, 0.89, 0.29 ), dk = vec3( 0.24, 0.66, 0.16 );',
    '  vec3 col = k < 0.42 ? lt : ( k < 0.8 ? md : dk );',
    '  vec2 hc = fract( p * 11.0 ) - 0.5;',   // halftone dots toward the rim
    '  if ( length( hc ) < 0.42 * smoothstep( 0.5, 0.95, k ) ) col = dk * 0.72;',
    '  vec2 bp = p * 3.6 + vec2( s, s * 0.7 ); vec2 bi = floor( bp ); vec2 bf = fract( bp ) - 0.5;',   // bubbles grow and pop
    '  float h = hash( bi + vP.x * 13.0 ); float cyc = fract( uTime * ( 0.45 + h * 0.8 ) + h * 7.0 );',
    '  vec2 off = ( vec2( hash( bi + 1.7 ), hash( bi + 4.1 ) ) - 0.5 ) * 0.35;',
    '  float br = 0.3 * cyc, bd = length( bf - off );',
    '  if ( h > 0.3 && k < 0.82 ) {',
    '    if ( cyc < 0.9 ) { if ( bd < br ) col = mix( lt, vec3( 1.0 ), 0.3 ); if ( abs( bd - br ) < 0.055 ) col = ink; if ( length( bf - off + vec2( br * 0.35, -br * 0.35 ) ) < br * 0.22 ) col = vec3( 1.0 ); }',
    '    else if ( bd < br * 1.35 && bd > br * 0.9 && fract( a * 1.2 + h ) < 0.6 ) col = ink;',   // pop: a broken ring
    '  }',
    '  if ( k > 0.9 ) col = ink;',   // ink outline
    '  gl_FragColor = vec4( col, vP.y );',
    '}'
  ].join('\n');
  var _m4 = null;
  function ensureMesh() {
    if (SF.mesh || typeof THREE === 'undefined' || !IB.Render || !IB.Render.scene) return;
    var geo = new THREE.PlaneGeometry(2, 2); geo.rotateX(-Math.PI / 2);
    var at = new THREE.InstancedBufferAttribute(new Float32Array(POOL_CAP * 4), 4); at.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aPool', at);
    var mat = new THREE.ShaderMaterial({ uniforms: { uTime: { value: 0 } }, vertexShader: POOL_VERT, fragmentShader: POOL_FRAG,
      transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    var im = new THREE.InstancedMesh(geo, mat, POOL_CAP);
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.frustumCulled = false; im.renderOrder = 2; im.count = 0; im.visible = false;
    IB.Render.scene.add(im);
    SF.mesh = im; SF.poolAttr = at; _m4 = new THREE.Matrix4();
  }
  function syncMesh(t) {
    var im = SF.mesh; if (!im) return;
    var n = 0;
    for (var i = 0; i < POOL_CAP; i++) {
      var p = SF.pools[i]; if (!p.on) continue;
      var grow = Math.min(1, p.t / 0.22), left = p.life - p.t;
      var spread = 0.55 + 0.45 * (1 - Math.pow(1 - grow, 3)), alpha = Math.min(1, left / 0.6) * 0.95;
      _m4.makeScale(p.R, 1, p.R).setPosition(p.x, 0.03, p.z);
      im.setMatrixAt(n, _m4);
      SF.poolAttr.setXYZW(n, p.seed, alpha, spread, 0);
      n++;
    }
    im.count = n; im.visible = n > 0;
    if (n) { im.instanceMatrix.needsUpdate = true; SF.poolAttr.needsUpdate = true; im.material.uniforms.uTime.value = t; }
  }
})(window.IB = window.IB || {});
