// INKBOLT robots of levels 35+ (game/jets.js, troops.js, trooperrig.js; rows in data/enemies.js): on the small greybox
// level with AI.setLevel(35) and the render loop paused, the real Player / AI / projectile code is stepped at 1/60 s:
//   Jet Trooper: one element per robot on its accents; flies outdoors; raises and opens its pods, locks on (red ring,
//     beeps) for 0.8-1 s, fires a 6-rocket volley that hurts the player (electric / acid also over time), cools down;
//     a strafing player takes less; indoors it stays on its feet and dashes; it falls and dies, rolls a drop;
//   Rocket Soldier: the Soldier's body with a Murmur or a Hothead (the player's models), shouldered to fire, rockets
//     hurt the player, far slower than a Soldier's bursts;
//   Blade Bot kusarigama: whirls the chain around the player (damage ticks), throws the sickle (a hit standing still,
//     a miss for a sidestep), reels it in;
//   Singularity: drones, hawks, jets and rocket soldiers are not pulled, a crawler is.
// Run (after tools/build.py): DEV=1 node tests/e2e/jets.spec.js   (SHOTS=1 also writes tests/e2e/review/jets-*.png)
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
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 300000 });
  console.log('# robots of levels 35+ (plan greybox, AI level 35)');
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const G = IB.Game;
    IB.AI.setLevel(35);
    window.__hits = []; window.__drops = [];
    const WD = IB.WeaponDrops, roll0 = WD.roll;
    WD.roll = (r, g) => { __drops.push(['roll', r.type]); return roll0(r, g); };
    window.__sim = (secs, each) => {
      const p = G.player, dt = 1 / 60, idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      const hurt = (src, d) => { const before = p.health; G.hurt(src, d); __hits.push({ type: src.type, proj: !!src.proj, d: +(before - p.health).toFixed(2) }); };
      const c = { player: p, world: G.level.world, level: G.level, activeZone: G.zone, hurt, shake: function () { }, onKill: G.onKill };
      for (let i = 0; i < Math.round(secs * 60); i++) {
        if (each && each(i, p) === 'move') { /* the callback moved the player */ } else IB.Player.step(p, idle, G.level.world, dt, null);
        IB.AI.update(dt, c); IB.Projectiles.update(dt, c); IB.AI.updateCorpses(dt); if (IB.Gear && IB.Gear.update) IB.Gear.update(dt, G);
        if (i % 6 === 0) { IB.AI.sync(); IB.TrooperRig.sync(0.1); }
      }
      IB.AI.sync();
    };
    window.__stage = (list) => {
      const p = G.player, Z = G.level.zones[G.zone];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; r.token = false; } }); IB.AI.tokens = 0;
      G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
      p.protect = 0; p.maxHp = 50000; p.health = 50000; p.alive = true; p.vx = p.vz = p.vy = 0; p.yaw = 0;
      p.x = Z.ox + Z.w / 2; p.z = Z.oz + Z.h / 2 - 5; p.y = 0; __hits.length = 0;
      IB.Troops.grenades.forEach(g => { g.on = false; g.impact = false; });
      IB.Troops.shock.left = 0; IB.Troops.acid.left = 0; IB.Projectiles.bolts.forEach(b => { b.on = false; }); IB.EnemyRockets.clear();
      IB.AI.sync();
      return list.map(([type, dx, dz]) => {
        const slot = __TEST__.spawnRobot(type, p.x + dx, p.z + dz), r = IB.AI.types[type].slots[slot];
        r.state = IB.AI.VIS[type].home; r.st = 0; r.thinkT = 0; r.zone = G.zone; r.yaw = Math.atan2(-dx, -dz); r.seesPlayer = true; r.losT = 0;
        return slot;
      });
    };
  });

  // ---------------- Jet Trooper: each element
  for (const elem of ['shock', 'acid', 'boom']) {
    const s = await pg.evaluate((elem) => {
      const [slot] = __stage([['jet', 2, 9]]), r = IB.AI.types.jet.slots[slot];
      r.elem = elem; r.tint.set(r.def.elementColors[elem]); r.tintHex = r.tint.getHex(); r.vcool = 0.5;
      const out = { elem, tint: r.tintHex.toString(16), maxY: 0, lockMax: 0, lockSeen: 0, podMax: 0, lidMax: 0, shock: 0, acid: 0, lockT: 0, lockStart: -1, fireAt: -1, volleys: 0 };
      const ER = IB.EnemyRockets, f0 = ER.fired;
      __sim(9, (i) => {
        out.maxY = Math.max(out.maxY, r.y - r.fy); out.podMax = Math.max(out.podMax, r.pod); out.lidMax = Math.max(out.lidMax, r.lidA);
        if (r.act === 'volley' && r.state === 'windup') { if (out.lockStart < 0) out.lockStart = i; if (IB.Jets.locks > 0) out.lockSeen++; }
        if (r.act === 'volley' && r.state === 'attack' && out.fireAt < 0) out.fireAt = i;
        out.shock = Math.max(out.shock, IB.Troops.shock.left); out.acid = Math.max(out.acid, IB.Troops.acid.left);
      });
      out.lockT = out.fireAt > 0 && out.lockStart >= 0 ? +((out.fireAt - out.lockStart) / 60).toFixed(2) : -1;
      out.rockets = ER.fired - f0; out.volleys = r.volleys; out.vcool = r.vcool;
      out.rocketHits = __hits.filter(h => h.type === 'jet' && h.proj).length; out.dmg = +__hits.filter(h => h.type === 'jet').reduce((a, h) => a + h.d, 0).toFixed(1);
      out.parts = Object.keys(IB.AI.types.jet.parts).filter(k => IB.AI.types.jet.parts[k].mesh.visible).length;
      return out;
    }, elem);
    check('a ' + elem + ' Jet Trooper flies, wears its element colour and draws all its parts', s.maxY > 2.5 && s.parts >= 12, JSON.stringify([s.tint, s.maxY, s.parts]));
    check('it raises and opens its pods and locks on (red ring) for 0.8-1 s, then fires a 6-rocket volley', s.podMax > 0.9 && s.lidMax > 0.9 && s.lockSeen > 0 &&
      s.lockT >= 0.78 && s.lockT <= 1.1 && s.volleys >= 1 && s.rockets >= 6, JSON.stringify(s));
    check('the volley cools down 6-9 s and the rockets hurt the player' + (elem !== 'boom' ? ' (and ' + elem + ' over time)' : ''),
      s.volleys === 1 && s.vcool > 0 && s.rocketHits > 0 && s.dmg > 0 && (elem === 'shock' ? s.shock > 0 : elem === 'acid' ? s.acid > 0 : true), JSON.stringify(s));
  }
  // dodging: standing still vs strafing hard during the volley
  let s = await pg.evaluate(() => {
    const run = (strafe) => {
      const [slot] = __stage([['jet', 1, 11]]), r = IB.AI.types.jet.slots[slot];
      r.elem = 'boom'; r.vcool = 0.3; r.cool = 99;
      let dir = 1;
      __sim(6, (i, p) => {
        r.cool = 99;   // rockets only
        if (!strafe) return;
        p.x += dir * 6 / 60; if (i % 70 === 0) dir = -dir;   // a jinking sidestep, 6 m/s
        return 'move';
      });
      return +__hits.filter(h => h.type === 'jet').reduce((a, h) => a + h.d, 0).toFixed(1);
    };
    let still = 0, moving = 0; for (let k = 0; k < 3; k++) { still += run(false); moving += run(true); }
    return { still, moving };
  });
  check('the rockets are dodgeable: a strafing player takes much less than one standing still', s.moving < s.still * 0.6, JSON.stringify(s));
  // indoors: low ceiling -> on its feet, dashes
  s = await pg.evaluate(() => {
    const env = IB.Game.level.theme.env, c0 = env.ceiling; env.ceiling = { height: 3.6 };   // an indoor room height
    const [slot] = __stage([['jet', 3, 8]]), r = IB.AI.types.jet.slots[slot];
    r.vcool = 99; let maxY = 0, maxSp = 0;
    __sim(2.5, () => { r.vcool = 99; });   // it lands (it was spawned at its flying height)
    __sim(10, () => { r.vcool = 99; maxY = Math.max(maxY, r.y - r.fy); maxSp = Math.max(maxSp, Math.hypot(r.vx, r.vz)); });
    env.ceiling = c0;
    return { low: r.low, endY: +(r.y - r.fy).toFixed(2), maxY: +maxY.toFixed(2), dashes: r.dashes, maxSp: +maxSp.toFixed(1) };
  });
  check('indoors (low ceiling) a Jet Trooper stays low on its feet and dashes fast across the room', s.low && s.maxY < 1.2 && s.dashes >= 1 && s.maxSp > 7, JSON.stringify(s));
  s = await pg.evaluate(() => {
    const seen = {}; for (let i = 0; i < 30; i++) { const [slot] = __stage([['jet', 2, 9]]); const r = IB.AI.types.jet.slots[slot]; seen[r.elem] = r.tintHex.toString(16); }
    const [slot] = __stage([['jet', 2, 9]]), r = IB.AI.types.jet.slots[slot];
    __sim(1.5);
    IB.AI.damage(r, r.hp + r.shield + 5, {}, IB.Game.onKill);
    return { seen, dead: !r.on, drop: __drops.some(d => d[1] === 'jet') };
  });
  check('Jet Troopers roll all three elements, each in its own colour', Object.keys(s.seen).length === 3 && new Set(Object.values(s.seen)).size === 3, JSON.stringify(s.seen));
  check('a wrecked Jet Trooper dies and rolls a drop', s.dead && s.drop, JSON.stringify(s));

  // ---------------- Rocket Soldier: Hothead and Murmur
  for (const L of ['hothead', 'murmur']) {
    s = await pg.evaluate((L) => {
      const [slot] = __stage([['rocketeer', 2, 12]]), r = IB.AI.types.rocketeer.slots[slot];
      r.launcher = L; r.sloppy = false; IB.AI.sync(); IB.TrooperRig.sync(0.05);
      const R = IB.TrooperRig.live['rocketeer' + slot];
      const out = { L, rig: R ? { body: R.mesh.visible, rl: !!(R.rl && R.rl.visible), id: R.rlId, mask: !!R.mesh.geometry.attributes.aMask } : null, shoulder: 0, bullets: 0 };
      const ER = IB.EnemyRockets, f0 = ER.fired;
      __sim(20, () => { out.shoulder = Math.max(out.shoulder, r.shoulder || 0); IB.Projectiles.bolts.forEach(b => { if (b.on && b.src.type === 'rocketeer') out.bullets++; }); });
      out.rockets = ER.fired - f0;
      out.hits = __hits.filter(h => h.type === 'rocketeer' && h.proj).length; out.dmg = +__hits.filter(h => h.type === 'rocketeer').reduce((a, h) => a + h.d, 0).toFixed(1);
      IB.AI.damage(r, r.hp + r.shield + 5, {}, IB.Game.onKill);
      out.dead = !r.on;
      return out;
    }, L);
    check('a Rocket Soldier with a ' + L + ': the Soldier body (carbine hidden) and the launcher model', s.rig && s.rig.body && s.rig.rl && s.rig.id === L && s.rig.mask, JSON.stringify(s.rig));
    check('it shoulders the launcher, fires rockets (no rifle rounds) that hurt the player, slowly', s.shoulder > 0.9 && s.rockets >= 2 && s.rockets <= (L === 'murmur' ? 16 : 8) && s.bullets === 0 && s.hits > 0 && s.dmg > 0, JSON.stringify(s));
  }

  // ---------------- Blade Bot kusarigama (three rounds each: standing still, then sidestepping every throw)
  s = await pg.evaluate(() => {
    const out = {};
    for (const mode of ['still', 'dodge']) {
      const o = { whirl: 0, throws: 0, maxLen: 0, km: {}, ticks: 0, hits: 0, dmg: 0, chain: false };
      for (let run = 0; run < 3; run++) {
        const [slot] = __stage([['blader', 1.5, 5]]), r = IB.AI.types.blader.slots[slot];
        r.weaponId = 'kusari'; r.cool = 0;
        let dir = 1, lastKm = '';
        __sim(8, (i, p) => {
          if (r.km === 'whirl') o.whirl++;
          if (r.km === 'throw' && lastKm !== 'throw') o.throws++;
          lastKm = r.km; o.km[r.km] = 1; o.maxLen = Math.max(o.maxLen, r.kLen);
          // the sidestep: as the sickle leaves, a 6 m/s step across its line
          if (mode === 'dodge' && r.km === 'throw') { const ux = r.kv.x, uz = r.kv.z, ul = Math.hypot(ux, uz) || 1; p.x += -uz / ul * dir * 6 / 60; p.z += ux / ul * dir * 6 / 60; return 'move'; }
          if (mode === 'dodge' && r.act === 'tell') dir = i % 2 ? -1 : 1;
        });
        o.ticks += r.kTicks; o.hits += r.kHits; o.dmg += __hits.filter(h => h.type === 'blader').reduce((a, h) => a + h.d, 0);
        o.chain = o.chain || (IB.AI.types.blader.parts.Chain.mesh.visible && IB.AI.types.blader.parts.Kusari.mesh.visible && IB.AI.types.blader.parts.Fundo.mesh.visible);
      }
      o.dmg = +o.dmg.toFixed(1);
      out[mode] = o;
    }
    return out;
  });
  check('a kusarigama Blade Bot draws its weight, chain and sickle and whirls the chain around the player (damage ticks)',
    s.still.chain && s.still.whirl > 90 && s.still.ticks >= 6 && s.still.maxLen > 1.6 && s.still.dmg > 0, JSON.stringify(s.still));
  check('then it throws the sickle: it hits a player standing still, a sidestep beats it, and it is reeled back in',
    s.still.throws >= 1 && s.still.hits >= 1 && s.dodge.throws >= 1 && s.dodge.hits <= s.dodge.throws * 0.5   /* few throws per window: a sidestep beats at least half */ && s.still.km.pull, JSON.stringify([s.still, s.dodge]));

  // ---------------- Singularity immunity
  s = await pg.evaluate(() => {
    const G = IB.Game, p = G.player;
    const types = ['drone', 'hawk', 'jet', 'rocketeer', 'crawler'];
    const slots = __stage(types.map((t, i) => [t, -4 + i * 2, 9]));
    const rs = types.map((t, i) => IB.AI.types[t].slots[slots[i]]);
    rs.forEach(r => { r.state = 'idle'; r.seesPlayer = false; r.cool = 99; r.vcool = 99; if (r.type !== 'crawler') r.y = r.fy + 1.2; });
    const x0 = rs.map(r => [r.x, r.z]), cx = p.x, cz = p.z + 13;
    __TEST__.forceVoid(cx, cz, 9, 1.4, 1);
    __sim(1.2, () => { rs.forEach(r => { r.state = 'idle'; r.wanderT = 9; }); });
    return types.map((t, i) => ({ t, moved: +Math.hypot(rs[i].x - x0[i][0], rs[i].z - x0[i][1]).toFixed(2), pull: +(rs[i].pull || 0).toFixed(2) }));
  });
  const im = s.filter(o => o.t !== 'crawler'), cr = s.find(o => o.t === 'crawler');
  check('the Singularity pulls a crawler but not drones, hawks, jet troopers or rocket soldiers', cr.moved > 1 && im.every(o => o.pull === 0 && o.moved < cr.moved * 0.5), JSON.stringify(s));

  if (process.env.SHOTS) {
    const out = path.join(__dirname, 'review'); fs.mkdirSync(out, { recursive: true });
    const shot = async (name, cam, fov) => {
      await pg.evaluate(([cam, fov]) => {
        const R = IB.Render; document.getElementById('hud').style.visibility = 'hidden';
        IB.AI.sync(); R.renderer.info.reset();
        R.camera.position.set(cam[0], cam[1], cam[2]); R.camera.rotation.order = 'YXZ'; R.camera.rotation.set(cam[4], cam[3], 0);
        R.camera.fov = fov; R.camera.updateProjectionMatrix(); R.camera.updateMatrixWorld(); R.render(false);
      }, [cam, fov]);
      await pg.screenshot({ path: path.join(out, name) });
      console.log('wrote', path.join(out, name));
    };
    await pg.screenshot({ path: path.join(out, 'jets-jet.png') });
    const pose = (list, secs) => pg.evaluate(([list, secs]) => {
      const G = IB.Game, p = G.player;
      __stage([]); p.x = -9; p.z = -24; const made = [];
      if (IB.Boom && IB.Boom.clear) IB.Boom.clear(); G.trauma = 0; G.shake = 0;   // no leftover blasts, scorch or shake in the shot
      list.forEach(o => {
        const slot = __TEST__.spawnRobot(o.type, o.x, o.z), r = IB.AI.types[o.type].slots[slot];
        r.zone = G.zone; r.yaw = o.yaw !== undefined ? o.yaw : Math.PI; r.aim = 0; r.state = o.state || 'pose'; r.seesPlayer = !!o.see;
        if (o.elem) { r.elem = o.elem; r.tint.set(r.def.elementColors[o.elem]); r.tintHex = r.tint.getHex(); }
        Object.keys(o.set || {}).forEach(k => { r[k] = o.set[k]; });
        if (o.y !== undefined) { r.y = o.y; r.hy = r.hyT = o.y; }
        made.push([r, o]);
      });
      if (secs) __sim(secs, () => { made.forEach(([r, o]) => { if (o.pin) { r.x = o.x; r.z = o.z; r.vx = r.vz = 0; } Object.keys(o.hold || {}).forEach(k => { r[k] = o.hold[k]; }); }); });
      for (let i = 0; i < 25; i++) { IB.AI.sync(); IB.TrooperRig.sync(0.05); }
    }, [list, secs || 0]);
    // Jet Troopers in their three elements: pods up and open on the left one, one standing, one hovering
    await pose([
      { type: 'jet', x: -10.6, z: -19.6, elem: 'shock', yaw: 3.5, y: 0.9, set: { pod: 1, lidA: 1, podAim: -0.1, thrust: 0.8, air: 1 } },
      { type: 'jet', x: -9.0, z: -19.2, elem: 'acid', yaw: 2.9, y: 0, set: { pod: 0, lidA: 0, thrust: 0, air: 0, hyT: 0, hy: 0 } },
      { type: 'jet', x: -7.4, z: -19.6, elem: 'boom', yaw: 2.4, y: 1.4, set: { pod: 0.6, lidA: 0.4, thrust: 1, air: 1 } }
    ]);
    await shot('jets-jet.png', [-9, 1.6, -23.6, Math.PI, -0.05], 50);
    // Rocket Soldiers: a Hothead and a Murmur on the shoulder, aiming; a kusarigama Blade Bot whirling its chain
    await pose([
      { type: 'rocketeer', x: -10.4, z: -19.4, state: 'windup', see: true, yaw: 3.3, set: { act: 'rl', launcher: 'hothead', trVariant: 1, shoulder: 1, st: 0 }, hold: { act: 'rl', state: 'windup', st: 0.1 } },
      { type: 'rocketeer', x: -8.8, z: -19.4, state: 'windup', see: true, yaw: 2.8, set: { act: 'rl', launcher: 'murmur', trVariant: 0, shoulder: 1, st: 0 }, hold: { act: 'rl', state: 'windup', st: 0.1 } },
      { type: 'rocketeer', x: -7.2, z: -19.4, state: 'keep', yaw: 2.5, set: { launcher: 'hothead', trVariant: 3 }, hold: { state: 'idle', cool: 9 } }
    ], 0.6);
    await shot('jets-rocketeers.png', [-8.8, 1.5, -22.6, Math.PI, -0.04], 48);
    await pose([
      { type: 'blader', x: -9, z: -18.5, state: 'attack', see: true, set: { weaponId: 'kusari', act: 'whirl', km: 'whirl', kR: 2.4, kangV: 13 }, hold: { state: 'attack', act: 'whirl', st: 0.2, km: 'whirl', kR: 2.4, kangV: 13 } },
      { type: 'blader', x: -6.6, z: -18.0, state: 'stalk', yaw: 2.4, set: { weaponId: 'kusari' }, hold: { state: 'idle' } }
    ], 0.4);
    await shot('jets-kusari.png', [-8.4, 3.0, -23.4, Math.PI, -0.42], 55);
    // close-ups: a Jet Trooper with its pods up and open, front three-quarter and from behind; the kusarigama
    const jetClose = { type: 'jet', x: -9, z: -20, elem: 'shock', yaw: 2.75, y: 0, set: { pod: 1, lidA: 1, podAim: 0, thrust: 0.9, air: 0, hyT: 0, hy: 0 } };
    await pose([jetClose]);
    await shot('jets-close-front.png', [-8.4, 1.55, -22.5, Math.PI + 0.22, -0.08], 40);
    await pose([Object.assign({}, jetClose, { elem: 'acid', yaw: 0.45 })]);
    await shot('jets-close-back.png', [-8.4, 2.1, -22.4, Math.PI + 0.22, -0.2], 40);
    await pose([{ type: 'blader', x: -9, z: -20, state: 'attack', see: true, set: { weaponId: 'kusari', act: 'whirl', km: 'whirl', kR: 1.6, kangV: 4 }, hold: { state: 'attack', act: 'whirl', st: 0.2, km: 'whirl', kR: 1.6, kangV: 4 } }], 0.3);
    await shot('jets-close-kusari.png', [-9, 2.2, -23.2, Math.PI, -0.38], 42);
  }

  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
