// INKBOLT robots of levels 20+ (game/troops.js, trooperrig.js, ai.js; rows in data/enemies.js): on the small greybox
// level with AI.setLevel(20) and the render loop paused, the real Player / AI / projectile code is stepped at 1/60 s:
//   Robot Trooper ('mech'): drawn on the trooper rig as the robot body, fires normal carbine rounds only (no grenades),
//     hurts the player, a lighter armour pool than the Soldier, dies (rig death), rolls a weapon drop;
//   Grenadier: the Soldier's body with the launcher (its carbine hidden), lobs 40 mm grenades with a red ring at the
//     landing spot that burst and hurt the player, far slower than a Soldier's bursts, drops like a Soldier;
//   Hawk: one round type per Hawk shown by its accent colour; normal / shock / acid / explosive rounds hurt the
//     player with the right effect; it falls and blows up when wrecked, rolls a drop;
//   Crawler: half wear the advanced skin on level 20 (both colour splits, some specked), none on level 19; both bite.
// Run (after tools/build.py): node tests/e2e/latebots.spec.js   (DEV=1 uses Source/dev.html; SHOTS=1 also writes
// tests/e2e/review/latebots-*.png)
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
let fails = 0;
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : '')); if (!ok) fails++; }
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

(async () => {
  const srv = await serve(), page = process.env.DEV ? 'Source/dev.html' : 'Play%20Inkbolt.html';
  const base = 'http://localhost:' + srv.address().port + '/' + page;
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=greybox');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 180000 });
  console.log('# robots of levels 20+ (plan greybox, AI level 20)');
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const G = IB.Game;
    IB.AI.setLevel(20);
    window.__hits = []; window.__drops = [];
    const WD = IB.WeaponDrops, roll0 = WD.roll;
    WD.roll = (r, g) => { __drops.push(['roll', r.type]); return roll0(r, g); };
    window.__sim = (secs, each) => {
      const p = G.player, dt = 1 / 60, idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      const hurt = (src, d) => { const before = p.health; G.hurt(src, d); __hits.push({ type: src.type, proj: !!src.proj, d: +(before - p.health).toFixed(2) }); };
      const c = { player: p, world: G.level.world, level: G.level, activeZone: G.zone, hurt, shake: function () { }, onKill: G.onKill };
      for (let i = 0; i < Math.round(secs * 60); i++) {
        IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, c); IB.Projectiles.update(dt, c); IB.AI.updateCorpses(dt);
        if (each) each(i);
        if (i % 6 === 0) { IB.AI.sync(); IB.TrooperRig.sync(0.1); }   // the trooper rig places the muzzles (and animates)
      }
      IB.AI.sync();
    };
    window.__stage = (list) => {
      const p = G.player, Z = G.level.zones[G.zone];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; r.token = false; } }); IB.AI.tokens = 0;
      G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
      p.protect = 0; p.maxHp = 5000; p.health = 5000; p.alive = true; p.vx = p.vz = p.vy = 0; p.yaw = 0;
      p.x = Z.ox + Z.w / 2; p.z = Z.oz + Z.h / 2 - 5; p.y = 0; __hits.length = 0;
      IB.Troops.grenades.forEach(g => { g.on = false; g.impact = false; });
      IB.Troops.shock.left = 0; IB.Troops.acid.left = 0; IB.Projectiles.bolts.forEach(b => { b.on = false; });
      IB.AI.sync();
      return list.map(([type, dx, dz]) => {
        const slot = __TEST__.spawnRobot(type, p.x + dx, p.z + dz), r = IB.AI.types[type].slots[slot];
        r.state = IB.AI.VIS[type].home; r.st = 0; r.thinkT = 0; r.zone = G.zone; r.yaw = Math.atan2(-dx, -dz); r.seesPlayer = true; r.losT = 0;
        return slot;
      });
    };
    window.__rig = (type, slot) => { const R = IB.TrooperRig.live[type + slot]; return R ? { body: R.mesh.visible, mech: !!(R.mech && R.mech.visible), gl: !!(R.gl && R.gl.visible), mask: !!R.mesh.geometry.attributes.aMask } : null; };
  });

  // ---------------- Robot Trooper
  let s = await pg.evaluate(() => {
    const [slot] = __stage([['mech', 1.5, 10]]), r = IB.AI.types.mech.slots[slot];
    r.sloppy = false;   // a steady shot (about 40 % aim wide on purpose)
    IB.AI.sync();
    const out = { rig: __rig('mech', slot), maxShield: r.maxShield, maxHp: r.maxHp, nades: r.nades, kinds: {}, t: 0 };
    const seen = new Set();
    __sim(10, () => { IB.Projectiles.bolts.forEach(b => { if (b.on && b.src.type === 'mech' && !seen.has(b)) { seen.add(b); out.kinds[b.kind] = (out.kinds[b.kind] || 0) + 1; } }); });
    out.hits = __hits.filter(h => h.type === 'mech').length; out.dmg = __hits.filter(h => h.type === 'mech').reduce((a, h) => a + h.d, 0);
    out.thrown = IB.Troops.stats().nades;
    const sol = IB.ENEMIES.soldier, D = IB.Damage;
    out.soldierPool = (sol.hp + sol.shield) * D.enemyHpMul(20); out.gunnerPool = IB.ENEMIES.gunner.hp * D.enemyHpMul(20);
    IB.AI.damage(r, r.hp + r.shield + 5, {}, IB.Game.onKill);
    out.dead = !r.on; out.drop = __drops.some(d => d[1] === 'mech'); out.dying = IB.TrooperRig.dying.length;
    return out;
  });
  check('a Robot Trooper is drawn as the robot body on the trooper rig', s.rig && s.rig.mech && !s.rig.body && !s.rig.gl, JSON.stringify(s.rig));
  check('it fires normal rounds only and hurts the player', Object.keys(s.kinds).length === 1 && s.kinds.bullet > 0 && s.hits > 0 && s.dmg > 0, JSON.stringify([s.kinds, s.hits, s.dmg]));
  check('no grenades; a lighter armour pool than the Soldier, tougher than a Gunner', s.nades === 0 && s.thrown === 0 && s.maxShield > 0 &&
    s.maxHp + s.maxShield < s.soldierPool && s.maxHp + s.maxShield > s.gunnerPool, JSON.stringify(s));
  check('it dies (rig death) and rolls a weapon drop', s.dead && s.drop && s.dying > 0, JSON.stringify([s.dead, s.drop, s.dying]));

  // ---------------- Grenadier
  s = await pg.evaluate(() => {
    const [slot] = __stage([['grenadier', 2, 11]]), r = IB.AI.types.grenadier.slots[slot];
    r.sloppy = false;
    IB.AI.sync();
    const out = { rig: __rig('grenadier', slot), ring: 0, shells0: IB.Troops.stats().shells, bullets: 0 };
    let land = null;
    __sim(20, () => {
      const g = IB.Troops.grenades.find(q => q.on && q.impact);
      if (g && !g.rest) { out.ring = Math.max(out.ring, 1); if (!land) land = { lx: g.lx, lz: g.lz, px: IB.Game.player.x, pz: IB.Game.player.z }; }
      IB.Projectiles.bolts.forEach(b => { if (b.on && b.src.type === 'grenadier') out.bullets++; });
    });
    out.shells = IB.Troops.stats().shells - out.shells0;
    out.land = land ? +Math.hypot(land.lx - land.px, land.lz - land.pz).toFixed(2) : null;
    out.blast = __hits.filter(h => h.type === 'grenadier' && h.proj).length;
    out.dmg = __hits.filter(h => h.type === 'grenadier').reduce((a, h) => a + h.d, 0);
    // a Soldier over the same time: its rounds
    const [s2] = __stage([['soldier', 2, 11]]), q = IB.AI.types.soldier.slots[s2];
    q.ncool = 99; let rounds = 0; const seen = new Set();
    __sim(20, () => { q.ncool = 99; IB.Projectiles.bolts.forEach(b => { if (b.on && b.src.type === 'soldier' && !seen.has(b)) { seen.add(b); rounds++; } }); });
    out.soldierRounds = rounds;
    const [s3] = __stage([['grenadier', 3, 8]]), g3 = IB.AI.types.grenadier.slots[s3];
    IB.AI.damage(g3, g3.hp + g3.shield + 5, {}, IB.Game.onKill);
    out.dead = !g3.on; out.drop = __drops.some(d => d[1] === 'grenadier');
    return out;
  });
  check('a Grenadier is the Soldier body with the launcher, its carbine hidden', s.rig && s.rig.body && s.rig.gl && s.rig.mask && !s.rig.mech, JSON.stringify(s.rig));
  check('it lobs grenades with a red ring where they land, near the player', s.shells >= 2 && s.ring > 0 && s.land !== null && s.land < 2.5, JSON.stringify(s));
  check('its grenades burst and hurt the player (no rifle rounds)', s.blast >= 1 && s.dmg > 0 && s.bullets === 0, JSON.stringify(s));
  check('it fires far slower than a Soldier (shells vs rounds in 20 s)', s.shells * 3 < s.soldierRounds && s.shells <= 7, s.shells + ' shells vs ' + s.soldierRounds + ' rounds');
  check('it dies and rolls a Soldier-like drop', s.dead && s.drop, JSON.stringify([s.dead, s.drop]));

  // ---------------- Hawk: each round type
  const kinds = ['bullet', 'shock', 'acid', 'boom'];
  for (const kind of kinds) {
    s = await pg.evaluate((kind) => {
      const [slot] = __stage([['hawk', 2, 9]]), r = IB.AI.types.hawk.slots[slot];
      r.round = kind; r.tint.set(r.def.roundColors[kind]); r.tintHex = r.tint.getHex();
      const out = { kind, kinds: {}, shock: 0, acid: 0, y: 0, tint: r.tintHex.toString(16) };
      const seen = new Set();
      __sim(7, () => {
        IB.Projectiles.bolts.forEach(b => { if (b.on && b.src.type === 'hawk' && !seen.has(b)) { seen.add(b); out.kinds[b.kind] = (out.kinds[b.kind] || 0) + 1; } });
        out.shock = Math.max(out.shock, IB.Troops.shock.left); out.acid = Math.max(out.acid, IB.Troops.acid.left); out.y = Math.max(out.y, r.y);
      });
      out.hits = __hits.filter(h => h.type === 'hawk').length; out.dmg = __hits.filter(h => h.type === 'hawk').reduce((a, h) => a + h.d, 0);
      return out;
    }, kind);
    const eff = kind === 'shock' ? s.shock > 0 : kind === 'acid' ? s.acid > 0 : true;
    check('a ' + kind + ' Hawk flies, fires ' + kind + ' rounds only and hurts the player' + (kind === 'shock' || kind === 'acid' ? ' over time' : ''),
      Object.keys(s.kinds).length === 1 && s.kinds[kind] > 0 && s.hits > 0 && s.dmg > 0 && eff && s.y > 2, JSON.stringify(s));
  }
  s = await pg.evaluate(() => {
    const seen = {}; for (let i = 0; i < 40; i++) { const [slot] = __stage([['hawk', 2, 9]]); const r = IB.AI.types.hawk.slots[slot]; seen[r.round] = r.tintHex.toString(16); }
    const [slot] = __stage([['hawk', 2, 9]]), r = IB.AI.types.hawk.slots[slot];
    IB.AI.damage(r, r.hp + 5, {}, IB.Game.onKill);
    return { seen, dead: !r.on, drop: __drops.some(d => d[1] === 'hawk') };
  });
  check('Hawks come in all four round types, each in its own accent colour', Object.keys(s.seen).length === 4 && new Set(Object.values(s.seen)).size === 4, JSON.stringify(s.seen));
  check('a wrecked Hawk drops out of the air and rolls a drop', s.dead && s.drop, JSON.stringify(s));

  // ---------------- Crawler skins
  s = await pg.evaluate(() => {
    const count = (L) => {
      IB.AI.setLevel(L); const out = { skin: 0, grey: 0, black: 0, specks: 0, n: 0 };
      for (let k = 0; k < 6; k++) {
        const list = []; for (let i = 0; i < 20; i++) list.push(['crawler', (i % 5) * 1.2 - 2.4, 6 + Math.floor(i / 5) * 1.2]);
        const slots = __stage(list);
        slots.forEach(sl => { const r = IB.AI.types.crawler.slots[sl]; out.n++; if (r.skin) { out.skin++; out[r.split]++; if (r.specks) out.specks++; } });
      }
      IB.AI.sync();
      const T = IB.AI.types.crawler.parts; out.drawn = { Body2: T.Body2.mesh.visible, Leg2: T.Leg2.mesh.visible, Specks: T.Specks.mesh.visible };
      return out;
    };
    const L19 = count(19), L20 = count(20);
    // both skins bite and die
    const [a, b] = __stage([['crawler', 0.6, 1.6], ['crawler', -0.6, 1.6]]), ra = IB.AI.types.crawler.slots[a], rb = IB.AI.types.crawler.slots[b];
    ra.skin = 0; rb.skin = 1; rb.tint = rb.tint || new THREE.Color(); rb.tint2 = rb.tint2 || new THREE.Color();
    __sim(3);
    const bites = __hits.filter(h => h.type === 'crawler' && !h.proj).length;
    IB.AI.damage(ra, ra.hp + 1, {}, IB.Game.onKill); IB.AI.damage(rb, rb.hp + 1, {}, IB.Game.onKill);
    return { L19, L20, bites, dead: !ra.on && !rb.on };
  });
  check('no advanced Crawler skin before level 20', s.L19.skin === 0 && !s.L19.drawn.Body2, JSON.stringify(s.L19));
  check('on level 20 about half the Crawlers wear the advanced skin, both colour splits, some specked',
    s.L20.skin > s.L20.n * 0.3 && s.L20.skin < s.L20.n * 0.7 && s.L20.grey > 0 && s.L20.black > 0 && s.L20.specks > 0 && s.L20.specks < s.L20.skin && s.L20.drawn.Body2 && s.L20.drawn.Leg2, JSON.stringify(s.L20));
  check('Crawlers of both skins bite the player and die', s.bites > 0 && s.dead, JSON.stringify([s.bites, s.dead]));

  if (process.env.SHOTS) {
    const out = path.join(__dirname, 'review'); fs.mkdirSync(out, { recursive: true });
    await pg.setViewportSize({ width: 1280, height: 720 });
    // cam: [x, y, z, yaw, pitch] (yaw pi looks +z); the open corner of the greybox lot around (-9, -20)
    const shot = async (name, cam, fov) => {
      await pg.evaluate(([cam, fov]) => {
        const R = IB.Render; document.getElementById('hud').style.visibility = 'hidden';
        IB.AI.sync(); R.renderer.info.reset();   // a new render frame: instance buffers upload once per frame
        R.camera.position.set(cam[0], cam[1], cam[2]); R.camera.rotation.order = 'YXZ'; R.camera.rotation.set(cam[4], cam[3], 0);
        R.camera.fov = fov; R.camera.updateProjectionMatrix(); R.camera.updateMatrixWorld(); R.render(false);
      }, [cam, fov]);
      await pg.screenshot({ path: path.join(out, name) });
      console.log('wrote', path.join(out, name));
    };
    await pg.screenshot({ path: path.join(out, 'latebots-troopers.png') });   // lets the last game frame go by
    const pose = (list, sim) => pg.evaluate(([list, sim]) => {
      const G = IB.Game, p = G.player;
      __stage([]); p.x = -9; p.z = sim ? -22 : -30; const pins = [];
      list.forEach(o => {
        const slot = __TEST__.spawnRobot(o.type, o.x, o.z), r = IB.AI.types[o.type].slots[slot];
        r.zone = G.zone; r.yaw = o.yaw !== undefined ? o.yaw : Math.PI; r.aim = 0; r.state = o.state || 'pose'; r.seesPlayer = !!o.see;
        Object.keys(o.set || {}).forEach(k => { r[k] = o.set[k]; });
        if (o.type === 'hawk' && o.round) { r.round = o.round; r.tint.set(r.def.roundColors[o.round]); r.tintHex = r.tint.getHex(); }
        if (o.type === 'crawler' && o.skin !== undefined) {
          r.skin = o.skin; r.tint = r.tint || new THREE.Color(); r.tint2 = r.tint2 || new THREE.Color();
          const S = IB.AI.SKIN2, dark = o.split === 'black'; r.tint.set(dark ? S.black : S.grey); r.tint2.set(dark ? S.grey : S.black); r.split = o.split; r.specks = !!o.specks;
        }
        if (o.y !== undefined) r.y = o.y;
        if (o.pin) pins.push([r, o.x, o.z]);
      });
      // in action: run until rounds are in the air (pinned troopers hold their spot instead of taking cover); else let
      // the rigs settle into their poses
      if (sim) for (let i = 0; i < 240 && IB.Projectiles.bolts.filter(b => b.on && b.t > 0.08).length + IB.Troops.grenades.filter(g => g.on && g.impact && g.t > 0.3).length < sim; i++) {
        __sim(1 / 30); pins.forEach(([r, x, z]) => { r.x = x; r.z = z; r.vx = r.vz = 0; });
      }
      for (let i = 0; i < 25; i++) { IB.AI.sync(); IB.TrooperRig.sync(0.05); }
    }, [list, sim || 0]);
    // Robot Troopers in four colourways, two Grenadiers, a Soldier for comparison
    await pose([
      { type: 'mech', x: -11.2, z: -19.4, state: 'keep', see: true, yaw: 3.3, set: { trVariant: 0 } }, { type: 'mech', x: -10.2, z: -19.4, state: 'keep', see: true, yaw: 2.6, set: { trVariant: 1 } },
      { type: 'mech', x: -9.2, z: -19.4, state: 'keep', see: true, yaw: 3.9, set: { trVariant: 2 } }, { type: 'mech', x: -8.2, z: -19.4, state: 'idle', yaw: 0.4, set: { trVariant: 3 } },
      { type: 'grenadier', x: -7.2, z: -19.4, state: 'keep', see: true, yaw: 3.4, set: { trVariant: 0 } }, { type: 'grenadier', x: -6.2, z: -19.4, state: 'keep', see: true, yaw: 2.2, set: { trVariant: 2 } },
      { type: 'soldier', x: -5.2, z: -19.4, state: 'keep', see: true, yaw: 3.0, set: { trVariant: 0 } }
    ]);
    await shot('latebots-troopers.png', [-8.2, 1.25, -24.2, Math.PI, -0.02], 45);
    // Hawks: normal (white), shock (blue), acid (green), explosive (orange); an old Drone behind
    await pose([
      { type: 'hawk', x: -10.4, z: -19.4, round: 'bullet', yaw: 2.6, y: 1.7 }, { type: 'hawk', x: -9.0, z: -19.0, round: 'shock', yaw: 3.5, y: 2.1 },
      { type: 'hawk', x: -7.6, z: -19.4, round: 'acid', yaw: 1.6, y: 1.6 }, { type: 'hawk', x: -9.0, z: -17.4, round: 'boom', yaw: -1.2, y: 2.6 },
      { type: 'drone', x: -6.4, z: -16.8, yaw: 3.6, y: 2.4 }
    ]);
    await shot('latebots-hawks.png', [-9, 2.2, -22.4, Math.PI, -0.06], 42);
    // Crawlers: the old tin can, the advanced skin grey / black (some specked); a Gunner and a Bomber (levels 1-19)
    await pose([
      { type: 'crawler', x: -10.2, z: -19.8, skin: 1, split: 'grey', specks: true, yaw: 2.6 }, { type: 'crawler', x: -9.0, z: -19.6, skin: 1, split: 'black', specks: true, yaw: 3.6 },
      { type: 'crawler', x: -7.8, z: -19.8, skin: 1, split: 'grey', yaw: 3.0 }, { type: 'crawler', x: -9.6, z: -18.4, skin: 0 },
      { type: 'crawler', x: -8.4, z: -18.4, skin: 1, split: 'black', yaw: 0.6 }, { type: 'gunner', x: -11.2, z: -17.6, yaw: 2.8 }, { type: 'bomber', x: -6.8, z: -17.6 }
    ]);
    await shot('latebots-crawlers.png', [-9, 1.7, -21.8, Math.PI, -0.36], 46);
    // in action: Hawks firing shock and acid rounds, Robot Troopers firing, a Grenadier's grenade in flight over its ring
    await pose([
      { type: 'hawk', x: -11, z: -15, round: 'shock', state: 'keep', see: true, y: 3, set: { cool: 0 } }, { type: 'hawk', x: -9, z: -14.5, round: 'acid', state: 'keep', see: true, y: 3, set: { cool: 0 } },
      { type: 'mech', x: -10, z: -15, state: 'keep', see: true, pin: true, set: { cool: 0, sloppy: false } },
      { type: 'grenadier', x: -8, z: -16, state: 'keep', see: true, pin: true, set: { cool: 0, sloppy: false, trVariant: 1 } }
    ], 5);
    await shot('latebots-action.png', [-6.6, 1.7, -21.0, 2.6, -0.02], 60);
  }

  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
