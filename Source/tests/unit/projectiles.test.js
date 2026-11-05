'use strict';
// Enemy projectile + blast maths (src/game/projectiles.js helpers; no THREE needed) and the new robot rows (5.7).
const test = require('node:test');
const assert = require('node:assert/strict');
require('../../src/data/enemies.js');
require('../../src/game/projectiles.js');
const IB = globalThis.IB;
const P = IB.Projectiles;
const near = (a, b, eps, msg) => assert.ok(Math.abs(a - b) < (eps || 1e-9), (msg || '') + ` expected ${b}, got ${a}`);

test('segment-segment distance: crossing, parallel, skew, degenerate', () => {
  near(P.segSegDist2(-1, 0, 0, 1, 0, 0, 0, -1, 0, 0, 1, 0), 0);                 // crossing at the origin
  near(P.segSegDist2(-1, 0, 0, 1, 0, 0, -1, 2, 0, 1, 2, 0), 4);                 // parallel 2 m apart
  near(P.segSegDist2(-1, 0, 0, 1, 0, 0, 0, -1, 3, 0, 1, 3), 9);                 // skew, 3 m apart
  near(P.segSegDist2(0, 0, 0, 0, 0, 0, 3, 4, 0, 3, 4, 0), 25);                  // two points
  near(P.segSegDist2(2, 0, 0, 3, 0, 0, -1, 0, 0, 1, 0, 0), 1);                  // collinear, gap of 1 m
  near(P.segSegDist2(0, 5, 0, 0, 5, 0, 0, 0, 0, 0, 1.7, 0), 3.3 * 3.3, 1e-9);  // point above a capsule axis
});

test('bolts hit the player capsule only when they pass within radius (and do not tunnel through)', () => {
  // player at origin, capsule axis y 0.35..1.35, r 0.35; bolt r 0.08
  const hit = (ax, ay, az, bx, by, bz) => P.segHitsCapsule(ax, ay, az, bx, by, bz, 0, 0.35, 1.35, 0, 0.35, 0.08);
  assert.equal(hit(-0.4, 1.2, 5, -0.4, 1.2, -5), true, 'chest-height pass inside 0.43 m');
  assert.equal(hit(0.5, 1.2, 5, 0.5, 1.2, -5), false, 'a sidestep of 0.5 m dodges');
  assert.equal(hit(0, 1.2, 0.3, 0, 1.2, -0.3), true, 'a fast step straight through still hits');
  assert.equal(hit(0, 2.3, 5, 0, 2.3, -5), false, 'over the head');
  assert.equal(hit(0, 1.75, 0.2, 0, 1.75, -0.2), true, 'top of the head (sphere cap)');
  assert.equal(hit(0, 1.2, 4, 0, 1.2, 3.63), false, 'still 3.6 m away this step');
});

test('sphere vs AABB', () => {
  const b = { x0: 0, y0: 0, z0: 0, x1: 1, y1: 1, z1: 1 };
  assert.equal(P.sphereBox(0.5, 0.5, 0.5, 0.1, b), true);
  assert.equal(P.sphereBox(1.05, 0.5, 0.5, 0.08, b), true);
  assert.equal(P.sphereBox(1.1, 0.5, 0.5, 0.08, b), false);
  assert.equal(P.sphereBox(1.05, 1.05, 1.05, 0.08, b), false, 'corner: 0.087 m away');
  assert.equal(P.sphereBox(1.04, 1.04, 1.04, 0.08, b), true);
});

test('blast falloff: full at the centre, (1 - d/R)^0.7, zero at R, halved behind cover', () => {
  near(P.blastDamage(0, 3, 35, false), 35);
  near(P.blastDamage(-0.2, 3, 35, false), 35, 1e-9, 'inside the target counts as the centre');
  near(P.blastDamage(1.5, 3, 35, false), 35 * Math.pow(0.5, 0.7));
  near(P.blastDamage(1.5, 3, 35, true), 35 * Math.pow(0.5, 0.7) / 2);
  assert.equal(P.blastDamage(3, 3, 35, false), 0);
  assert.equal(P.blastDamage(5, 3, 35, false), 0);
  let prev = Infinity;
  for (let d = 0; d < 3; d += 0.25) { const v = P.blastDamage(d, 3, 35, false); assert.ok(v < prev, 'monotonic at ' + d); prev = v; }
});

test('new robot rows match the brief (5.7) and carry what the AI reads', () => {
  const E = IB.ENEMIES;
  const g = E.gunner, b = E.bomber, d = E.drone;
  assert.deepEqual([g.hp, g.speed, g.damage, g.bolts, g.boltSpeed, g.gems.chip], [55, 3.0, 6, 3, 22, 2]);
  assert.deepEqual(g.keepDistance, [8, 16]);
  assert.equal(g.usesCover, true);
  assert.deepEqual([b.hp, b.speed, b.damage, b.blastRadius, b.fuse, b.gems.chip], [25, 4.2, 35, 3, 0.6, 2]);
  assert.equal(b.hurtsRobots, true);
  assert.ok(b.robotDamage > 0);
  assert.deepEqual([d.hp, d.speed, d.damage, d.hover, d.gems.chip, d.flying], [35, 4.5, 5, 3, 3, true]);
  assert.deepEqual(d.keepDistance, [8, 16]);
  // a Crawler (30 HP) at the centre of a Bomber blast dies; at the rim it survives
  assert.ok(P.blastDamage(0, b.blastRadius, b.robotDamage, false) >= E.crawler.hp);
  assert.ok(P.blastDamage(2.5, b.blastRadius, b.robotDamage, false) < E.crawler.hp);
});
