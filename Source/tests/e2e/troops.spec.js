// INKBOLT Soldier + Blade Bot (game/troops.js). On the small greybox level, with the render loop paused, the real
// Player / AI / projectile code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time):
//   a Soldier's shield soaks damage before its health drops and recharges; the health bar carries its shield row;
//   a Soldier throws a grenade (at most 3) that goes off and hurts the player; a Soldier rifle-butts the player up close;
//   a Blade Bot spins up, dashes spinning ~19 rev/s, cuts the player and ends up dizzy; kills call IB.WeaponDrops.
// Run (after tools/build.py): node tests/e2e/troops.spec.js   (SHOTS=1 also writes tests/e2e/review/troops-*.png)
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
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=greybox');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
  console.log('# Soldier + Blade Bot (plan greybox)');
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const G = IB.Game;
    window.__hits = [];
    window.__drops = [];
    // spy on the real drop module (keeps update / radar working)
    const WD = IB.WeaponDrops, roll0 = WD.roll, melee0 = WD.melee;
    WD.roll = (r, g) => { __drops.push(['roll', r.type]); return roll0(r, g); };
    WD.melee = (r, id, g) => { __drops.push(['melee', r.type, id]); return melee0(r, id, g); };
    // __sim(secs): steps player, robots, bolts, blasts; the player's hurt is recorded (source type, kind, damage)
    window.__sim = (secs) => {
      const p = G.player, dt = 1 / 60, idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      const hurt = (src, d) => { const before = p.health; G.hurt(src, d); __hits.push({ type: src.type, proj: !!src.proj, act: src.act || '', d: +(before - p.health).toFixed(2) }); };
      const c = { player: p, world: G.level.world, level: G.level, activeZone: G.zone, hurt, shake: function () { }, onKill: G.onKill };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, c); IB.Projectiles.update(dt, c); IB.AI.updateCorpses(dt); }
      IB.AI.sync();
    };
    // a clean stage: no waves, the player (lots of health, not protected) at (px, pz); robots of a type at offsets
    window.__stage = (list) => {
      const p = G.player, Z = G.level.zones[G.zone];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; r.token = false; } }); IB.AI.tokens = 0;
      G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
      p.protect = 0; p.maxHp = 5000; p.health = 5000; p.alive = true; p.vx = p.vz = p.vy = 0; p.yaw = 0;
      p.x = Z.ox + Z.w / 2; p.z = Z.oz + Z.h / 2 - 5; p.y = 0; __hits.length = 0;
      IB.Troops.grenades.forEach(g => { g.on = false; });
      return list.map(([type, dx, dz]) => {
        const slot = __TEST__.spawnRobot(type, p.x + dx, p.z + dz), r = IB.AI.types[type].slots[slot];
        r.state = IB.AI.VIS[type].home; r.st = 0; r.thinkT = 0; r.zone = G.zone; r.yaw = Math.atan2(-dx, -dz); r.seesPlayer = true; r.losT = 0;
        return slot;
      });
    };
  });

  // ---------------- Soldier: shield then health, recharge, shield row on the health bar
  let s = await pg.evaluate(() => {
    const [slot] = __stage([['soldier', 0, 9]]), r = IB.AI.types.soldier.slots[slot], out = { slot, maxShield: r.maxShield, maxHp: r.maxHp };
    r.cool = r.ncool = r.mcool = 99;
    IB.AI.damage(r, 20, {}, IB.Game.onKill); out.a = { hp: r.hp, shield: r.shield };
    IB.AI.damage(r, r.shield + 10, {}, IB.Game.onKill); out.b = { hp: r.hp, shield: r.shield };
    __sim(1); out.c = { shield: r.shield };
    __sim(4.5); out.d = { shield: r.shield };
    IB.HPBars.update(0.1, IB.Render.camera); out.bar = r._hb ? r._hb.sh : null;
    out.look = { armour: r.armour, torso: r.torso, helm: r.helm, tint: r.tintHex };
    return out;
  });
  check('a Soldier spawns with a shield pool scaled like its health', s.maxShield > 0 && Math.abs(s.maxShield / s.maxHp - 60 / 80) < 1e-6, JSON.stringify(s));
  check('the shield soaks a hit first (health untouched)', s.a.hp === s.maxHp && Math.abs(s.a.shield - (s.maxShield - 20)) < 1e-6, JSON.stringify(s.a));
  check('past the shield, health drops', s.b.shield === 0 && Math.abs(s.b.hp - (s.maxHp - 10)) < 1e-6, JSON.stringify(s.b));
  check('the shield waits out its delay, then recharges', s.c.shield === 0 && s.d.shield > 0, JSON.stringify([s.c, s.d]));
  check('its health bar shows the shield row', s.bar !== null && s.bar > 0 && s.bar <= 1, String(s.bar));

  // ---------------- Soldier: grenades (max 3), they go off and hurt the player
  s = await pg.evaluate(() => {
    const [slot] = __stage([['soldier', 2, 10]]), r = IB.AI.types.soldier.slots[slot];
    let thrown = 0, seen = 0, t = 0, hp0 = IB.Game.player.health;
    while (t < 30 && r.on) {
      r.cool = 99; r.mcool = 99; if (r.state === 'keep') r.ncool = Math.min(r.ncool, 0);
      const n0 = r.nades; __sim(0.25); t += 0.25;
      if (r.nades < n0) thrown += n0 - r.nades;
      seen = Math.max(seen, IB.Troops.stats().nades);
    }
    return { thrown, left: r.nades, seen, t, blast: __hits.filter(h => h.type === 'soldier' && h.proj).length, dmg: hp0 - IB.Game.player.health };
  });
  check('a Soldier throws grenades, 3 at most', s.thrown === 3 && s.left === 0 && s.seen >= 1, JSON.stringify(s));
  check('its grenades go off and hurt the player', s.blast >= 1 && s.dmg > 0, JSON.stringify(s));

  // ---------------- Soldier: melee up close
  s = await pg.evaluate(() => {
    const [slot] = __stage([['soldier', 0, 1.6]]), r = IB.AI.types.soldier.slots[slot];
    let t = 0, acts = new Set();
    while (t < 4 && !__hits.some(h => h.type === 'soldier' && !h.proj)) { r.cool = 99; r.ncool = 99; __sim(0.1); t += 0.1; if (r.act) acts.add(r.act); }
    return { t, acts: [...acts], hits: __hits.filter(h => h.type === 'soldier') };
  });
  check('a Soldier rifle-butts the player within reach', s.acts.includes('melee') && s.hits.some(h => !h.proj && h.d > 0), JSON.stringify(s));

  // ---------------- Blade Bot: spin-up, dash, cut, dizzy
  s = await pg.evaluate(() => {
    const [slot] = __stage([['blader', 0, 7]]), r = IB.AI.types.blader.slots[slot];
    r.cool = 0;
    let t = 0, states = [], top = 0, dizzy = false, cut = null;
    while (t < 8) {
      __sim(0.05); t += 0.05;
      const k = r.state + ':' + r.act; if (states[states.length - 1] !== k) states.push(k);
      top = Math.max(top, r.spinV / (Math.PI * 2));
      if (!cut) cut = __hits.find(h => h.type === 'blader' && !h.proj) || null;
      if (cut && r.state === 'recover' && r.act === 'dash') { dizzy = true; break; }
    }
    return { weapon: r.weaponId, states, top: +top.toFixed(1), cut, dizzy, smear: IB.Troops.stats().smears, t: +t.toFixed(2) };
  });
  check('a Blade Bot spins up and dashes at the player', s.states.includes('windup:dash') && s.states.includes('attack:dash'), JSON.stringify(s.states));
  check('the blade spins extremely fast in the dash (>= 15 rev/s) with a smear arc', s.top >= 15, 'rev/s ' + s.top);
  check('the dash cuts the player', !!(s.cut && s.cut.d > 0), JSON.stringify(s.cut) + ' ' + s.weapon);
  check('it overshoots and stays dizzy', s.dizzy, JSON.stringify(s.states));
  // standing next to it: a spin slash in place
  s = await pg.evaluate(() => {
    const [slot] = __stage([['blader', 0, 1.4]]), r = IB.AI.types.blader.slots[slot];
    r.cool = 99; let t = 0;
    while (t < 3 && !__hits.some(h => h.type === 'blader')) { __sim(0.1); t += 0.1; }
    return { act: r.act, hits: __hits.filter(h => h.type === 'blader').length, t };
  });
  check('right next to it, a spin slash cuts the player', s.hits > 0, JSON.stringify(s));

  // ---------------- kills: the drop hooks
  s = await pg.evaluate(() => {
    const [a, b] = __stage([['soldier', 3, 8], ['blader', -3, 8]]);
    const wb = IB.AI.types.blader.slots[b].weaponId;
    const sr = IB.AI.types.soldier.slots[a]; IB.AI.damage(sr, sr.hp + sr.shield + 1, {}, IB.Game.onKill); __TEST__.wreck('blader', b);
    return { drops: __drops.slice(), wb };
  });
  check('player kills roll weapon drops (Soldier: roll, Blade Bot: its melee weapon)', s.drops.some(d => d[0] === 'roll' && d[1] === 'soldier') && s.drops.some(d => d[0] === 'melee' && d[2] === s.wb), JSON.stringify(s));

  if (process.env.SHOTS) {
    const out = path.join(__dirname, 'review'); fs.mkdirSync(out, { recursive: true });
    await pg.setViewportSize({ width: 960, height: 540 });
    // line-up: six armour colours (both torsos, all helmets) and both Blade Bot weapons
    await pg.evaluate(() => {
      const G = IB.Game, p = G.player;
      __stage([]); p.x = -9; p.z = -22;   // an open corner of the lot
      const looks = [[0, 'A', 'A'], [1, 'B', 'B'], [2, 'A', 'C'], [3, 'B', 'A'], [4, 'A', 'B'], [5, 'B', 'C']];
      looks.forEach(([a, t, h], i) => {
        const slot = __TEST__.spawnRobot('soldier', p.x - 3.4 + i * 1.36, p.z + 4.6), r = IB.AI.types.soldier.slots[slot];
        r.state = 'pose'; r.armour = a; r.torso = t; r.helm = h; r.tint.set(r.def.armour[a]); r.yaw = 0.25 * Math.sin(i * 1.7) + Math.PI; r.aim = -0.1;
      });
      ['katana', 'eaxe'].forEach((w, i) => { const slot = __TEST__.spawnRobot('blader', p.x - 1.5 + i * 3, p.z + 7.4), r = IB.AI.types.blader.slots[slot]; r.state = 'pose'; r.weaponId = w; r.reach = w === 'eaxe' ? 1.32 : 1.5; r.yaw = Math.PI + 0.5; });
      p.yaw = Math.PI; p.pitch = -0.08;
    });
    const shot = async (name, camY, pitch) => {
      await pg.evaluate(([camY, pitch]) => {
        const R = IB.Render, p = IB.Game.player; document.getElementById('hud').style.visibility = 'hidden';
        // a new render frame (the game resets renderer.info each frame; buffers upload once per frame)
        IB.AI.sync(); R.renderer.info.reset(); R.camera.position.set(p.x, camY, p.z); R.camera.rotation.set(pitch, Math.PI, 0); R.camera.updateMatrixWorld(); R.render(false);
      }, [camY, pitch]);
      await pg.screenshot({ path: path.join(out, name) });
      console.log('wrote', path.join(out, name));
    };
    await shot('troops-lineup.png', 1.5, -0.1);
    // in action: a Soldier mid-throw, one firing, a live grenade with its ring, a Blade Bot dashing at full spin
    await pg.evaluate(() => {
      const G = IB.Game, p = G.player;
      __stage([]); p.x = -9; p.z = -22;
      const mk = (type, dx, dz) => { const s = __TEST__.spawnRobot(type, p.x + dx, p.z + dz), r = IB.AI.types[type].slots[s]; r.yaw = Math.atan2(-dx, -dz); r.seesPlayer = true; return r; };
      const a = mk('soldier', -2.2, 6.5); a.state = 'windup'; a.act = 'nade'; a.st = 0.5; a.throwL = -2.3; a.holdNade = true; a.aim = 0.05; a.legMove = 0;
      const b = mk('soldier', 2.6, 8); b.state = 'attack'; b.act = 'fire'; b.aim = -0.05; b.kick = 1; b.legMove = 1; b.walk = 1.1; b.legRel = 0.9;
      const c = mk('blader', 0.4, 3.6); c.weaponId = 'katana'; c.reach = 1.5; c.state = 'attack'; c.act = 'dash'; c.spinV = 120; c.bspin = 1.3; c.lean = 0.22;
      const g = IB.Troops.grenades[0]; g.on = true; g.t = 1.4; g.fuse = 2.1; g.rest = true; g.x = p.x - 1.2; g.y = 0.07; g.z = p.z + 5; g.R = 3.4;
      p.yaw = Math.PI;
    });
    await shot('troops-action.png', 1.55, -0.12);
  }

  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
