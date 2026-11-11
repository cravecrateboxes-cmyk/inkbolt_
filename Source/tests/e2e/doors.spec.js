// INKBOLT breakable doors (game/doors.js, theme symbol option `breakable`) on Helix Vault (plan 'datacenter'):
//  1. a security door blocks the player, shots, sight lines and the nav grid; the player SHOOTS it open through the
//     normal hit path (__TEST__.fireRay): it goes through its damage stages (dented, then torn), bursts, and then the
//     player walks through, sight lines cross it, its nav cells open and a Crawler paths through it to the player;
//  2. a FRAG CAN thrown at another security door blasts it open (Throwables -> Projectiles.explode -> Doors.blast);
//  3. ROBOT FIRE wears a glass door down (Projectiles bolts) and robot grenades / bomber blasts count too;
//  4. a weapon prototype in a containment field cannot be taken until the field is broken (mount lock);
//  5. a level restart shuts every door again (collision, sight and nav back).
// The render loop is paused and the real Player / AI / Projectiles / Throwables code is stepped at 1/60 s.
// Run (after tools/build.py): node tests/e2e/doors.spec.js     SHOTS=1 -> tests/e2e/review/doors-*.png
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
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=datacenter');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  await pg.evaluate(() => {
    window.__raf = window.requestAnimationFrame;
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) {
        IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); IB.Projectiles.update(dt, ctx);
        IB.Throwables.update(dt, G.level.world); IB.AI.updateCorpses(dt);
      }
    };
    window.__route = (zi, pts, secs) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, n = 0;
      while (k < pts.length && n++ < secs * 60) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.25) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
      }
      return { reached: k, of: pts.length, x: +(p.x - Z.ox).toFixed(2), z: +(p.z - Z.oz).toFixed(2) };
    };
    window.__place = (zi, x, z) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      G.zone = zi; IB.Zones.setVisible(G.level, zi);
      p.protect = 1e9; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = 0; p.vx = p.vz = p.vy = 0; p.onGround = true;
    };
    // the door of a zone nearest to zone-local (x, z), and its state
    window.__door = (zi, x, z) => {
      const Z = IB.Game.level.zones[zi];
      let best = null, bd = 1e9;
      IB.Doors.list().forEach(d => { if (d.zone !== zi) return; const k = Math.hypot(d.x - Z.ox - x, d.z - Z.oz - z); if (k < bd) { bd = k; best = d; } });
      return best;
    };
    window.__probe = (zi, d) => {
      const G = IB.Game, Z = G.level.zones[zi], w = G.level.world, nx = -d.az, nz = d.ax;
      // two points 1.6 m either side of the door at chest height, the nav cell in the middle of the opening
      const a = [d.x + nx * 1.6, 1.3, d.z + nz * 1.6], b = [d.x - nx * 1.6, 1.3, d.z - nz * 1.6];
      const c = IB.Zones.navCell(Z, d.x, d.z), rec = Z.doors[d.i];
      return { los: w.los(a[0], a[1], a[2], b[0], b[1], b[2]), navOpen: c >= 0 && !Z.nav.blocked[c], boxesOn: rec.boxes.every(b2 => b2.on),
        mesh: rec.meshes.map(m => m ? m.visible : null), hp: +rec.hp.toFixed(1), state: rec.state, broken: rec.broken };
    };
  });

  // ---------------- 1. shoot a security door open (zone 1, the hall door west of the spine)
  let d = await pg.evaluate(() => { __place(0, 18.5, 39.0); return __door(0, 18.5, 35.0); });
  check('zone 1 has its breakable doors (security, glass)', !!d && d.piece === 'SecDoor', JSON.stringify(d && { piece: d.piece, x: d.x, z: d.z, w: d.w, h: d.h, hp0: d.hp0 }));
  let p = await pg.evaluate(dd => __probe(0, dd), d);
  check('the closed door blocks sight lines and the nav grid', !p.los && !p.navOpen && p.boxesOn, JSON.stringify(p));
  let r = await pg.evaluate(() => __route(0, [[18.5, 30.0]], 6));
  check('... and the player: walking north stops at the door', r.reached === 0 && r.z > 35.2, JSON.stringify(r));
  const shots = await pg.evaluate(dd => {
    const G = IB.Game, p = G.player, Z = G.level.zones[0], st = [];
    __place(0, 18.5, 39.0);
    let n = 0;
    while (!Z.doors[dd.i].broken && n < 400) {
      const ox = p.x, oy = 1.5, oz = p.z, tx = dd.x + (Math.random() - 0.5) * 1.6, ty = 0.4 + Math.random() * 2, tz = dd.z;
      __TEST__.fireRay(ox, oy, oz, tx - ox, ty - oy, tz - oz); n++;
      const rec = Z.doors[dd.i];
      if (!st.length || st[st.length - 1] !== (rec.broken ? 3 : rec.state)) st.push(rec.broken ? 3 : rec.state);
    }
    return { n, stages: st, gun: __TEST__.state().weapon };
  }, d);
  check('shooting it (the normal bullet path) dents it, tears it, then bursts it', shots.stages.join(',') === '0,1,2,3' && shots.n > 10 && shots.n < 400, JSON.stringify(shots));
  if (process.env.SHOTS) {
    await pg.evaluate(() => { const p = IB.Game.player; p.yaw = 0; p.pitch = 0; window.requestAnimationFrame = window.__raf; });
    await pg.waitForTimeout(1500);
    await pg.screenshot({ path: path.join(__dirname, 'review', 'doors-shot-open.png') });
    await pg.evaluate(() => { window.requestAnimationFrame = () => 1; });
  }
  p = await pg.evaluate(dd => __probe(0, dd), d);
  check('broken: its boxes are off, the leaf mesh is gone and the wreck shows, sight lines cross it', p.broken && !p.boxesOn && p.los && p.mesh[0] === false && p.mesh[3] === true, JSON.stringify(p));
  check('... and the nav grid opened in the doorway', p.navOpen, JSON.stringify(p));
  r = await pg.evaluate(() => __route(0, [[18.5, 33.0], [18.5, 30.5]], 8));
  check('the player walks through the broken door', r.reached === 2, JSON.stringify(r));
  // a Crawler in the hall north of the door finds the way through it to the player in the lobby
  const chase = await pg.evaluate(() => {
    __place(0, 18.5, 41.0);
    const Z = IB.Game.level.zones[0], slot = __TEST__.spawnRobot('crawler', Z.ox + 18.5, Z.oz + 27.5);
    const rb = IB.AI.types.crawler.slots[slot]; rb.state = IB.AI.VIS.crawler.home; rb.st = 0; rb.thinkT = 0; rb.zone = 0;
    rb.def = Object.assign({}, rb.def, { range: -9 });
    let t = 0, best = 99;
    while (t < 40) { __sim(0.5, 0); t += 0.5; if (!rb.on) break; best = Math.min(best, Math.hypot(rb.x - IB.Game.player.x, rb.z - IB.Game.player.z)); if (best < 3 && rb.z - Z.oz > 37) break; }
    return { on: rb.on, z: +(rb.z - Z.oz).toFixed(2), x: +(rb.x - Z.ox).toFixed(2), best: +best.toFixed(2), t };
  });
  check('a Crawler paths through the broken door to the player behind it', chase.z > 36.5 && chase.best < 4, JSON.stringify(chase));

  // ---------------- 2. a frag can blasts the east hall door open
  const d2 = await pg.evaluate(() => { __place(0, 55.5, 41.0); IB.AI.robots.forEach(r => { r.on = false; }); return __door(0, 55.5, 35.0); });
  const g = await pg.evaluate(dd => {
    const G = IB.Game, p = G.player, def = IB.WEAPONS.frag, Z = G.level.zones[0], st0 = __probe(0, dd);
    // lob it from the player toward the foot of the door; it bounces off the leaf and goes off at the door
    const dx = dd.x - p.x, dz = (dd.z + 1.3) - p.z, L = Math.hypot(dx, dz);
    IB.Throwables.throw(p.x, 1.4, p.z, dx / L * 6.5, 3.2, dz / L * 6.5, def, IB.AI.hpMul || 1);
    const blasts0 = IB.Doors.stats.blasts;
    __sim(3.5, 0);
    return { before: st0, after: __probe(0, dd), blasts: IB.Doors.stats.blasts - blasts0, hp0: Z.doors[dd.i].hp0 };
  }, d2);
  check('a frag can thrown at the second security door blasts it open', g.blasts >= 1 && g.after.broken && !g.after.boxesOn, JSON.stringify(g));
  check('... sight lines and the nav grid open through it', g.after.los && g.after.navOpen && !g.before.los && !g.before.navOpen, JSON.stringify([g.before.los, g.before.navOpen, g.after.los, g.after.navOpen]));

  // ---------------- 3. robot fire wears a glass door down (the NOC's glass door)
  const d3 = await pg.evaluate(() => { __place(0, 44.0, 44.5); return __door(0, 46.5, 44.5); });
  const rf = await pg.evaluate(dd => {
    const G = IB.Game, Z = G.level.zones[0], rec = Z.doors[dd.i], hp0 = rec.hp;
    let n = 0;
    // a Gunner's bolts from inside the NOC at the player behind the glass: they hit the door
    while (!rec.broken && n < 300) {
      IB.Projectiles.fire(dd.x + 3, 1.2, dd.z + (Math.random() - 0.5), -1, 0, 0, 30, 12 * (IB.AI.hpMul || 1), { type: 'gunner', x: dd.x + 3, z: dd.z }, 0);
      __sim(0.2, 0); n++;
    }
    return { piece: dd.piece, hp0, broken: rec.broken, bolts: n };
  }, d3);
  check('robot bolts break a glass door', rf.piece === 'GlassDoor' && rf.broken && rf.bolts < 300, JSON.stringify(rf));

  // ---------------- 4. a containment field locks its prototype gun until it breaks (zone 3)
  const lock = await pg.evaluate(() => {
    const G = IB.Game, Z = G.level.zones[2], pods = Z.doors.filter(r => r.piece === 'FieldPod');
    const locked = (G.loot || []).filter(L => L.zone === 2 && L.lock && L.lock.piece === 'FieldPod');
    if (!pods.length || !locked.length) return { pods: pods.length, locked: locked.length };
    const L = locked[0], pod = L.lock;
    __place(2, 0, 0);
    G.zone = 2;
    const p = G.player;
    // stand 1.1 m in front of the pod, looking at the gun
    p.x = pod.x; p.z = pod.z + 1.25; p.y = 0;
    p.yaw = Math.atan2(-(L.x - p.x), -(L.z - p.z)); p.pitch = Math.atan2(L.y - (p.y + 1.5), Math.hypot(L.x - p.x, L.z - p.z));
    const before = G.nearestLoot();
    IB.Doors.blast(pod.x, 1.2, pod.z, 4, 2000);
    const after = G.nearestLoot();
    return { pods: pods.length, locked: locked.length, before: !!before, broken: pod.broken, after: after === L };
  });
  check('a prototype gun in a containment field cannot be taken until the field breaks, then it can', lock.pods >= 4 && lock.locked >= 1 && !lock.before && lock.broken && lock.after, JSON.stringify(lock));

  // ---------------- 5. a level restart shuts every door again
  const reset = await pg.evaluate(dd => {
    IB.Doors.reset(IB.Game.level);
    const all = IB.Doors.list();
    return { open: all.filter(x => x.broken).length, n: all.length, probe: __probe(0, dd) };
  }, d);
  check('restart: every door is whole and shut again, sight and nav blocked', reset.open === 0 && reset.n >= 12 && !reset.probe.los && !reset.probe.navOpen && reset.probe.boxesOn, JSON.stringify(reset));

  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
