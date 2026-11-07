// INKBOLT viewmodel screenshots (arms + guns in the real game). Not a test: a review tool.
//   node tests/e2e/viewmodel-shots.js [outdir] [W,H]        (serves the repo, opens Source/dev.html)
//   WEAPONS=pip,rivet picks the guns (idle, sprint, slide, reload, ADS each); GEAR=1 fits every attachment each gun takes
//   SHOTS=pip:Slide:0.3:slide,katana:Strike:0.42,rivet:Idle:0:ads   explicit list (weapon:action:time[:sprint|slide|ads])
//   (melee weapons play their swing clips frozen at the time given; CROP=x,y,w,h crops every shot)
// Every shot freezes one frame of one arm action (<WEAPON>_<Action> at a fraction of its length) with the
// game's own W.pose on top (sprint bob, ADS blend), robots and HUD hidden, so shots are repeatable.
// Join them into a sheet with: python3 blender/review_arms.py --tiles <outdir>/*.png --out sheet.png
// Build first (python3 tools/build.py) so dev.html exists; it loads assets/*.glb directly.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const OUT = path.resolve(process.argv[2] || path.join(__dirname, 'screens', 'viewmodel'));
const [VW, VH] = (process.argv[3] || '1280,720').split(',').map(Number);
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
// [weapon id, action, time 0..1, {sprint, aim}]
const SHOTS = [];
const MODE = { sprint: { sprint: 1 }, slide: { slide: 1 }, ads: { aim: 1 } };
if (process.env.SHOTS) {
  for (const sp of process.env.SHOTS.split(',')) { const [id, act, at, m] = sp.split(':'); SHOTS.push([id, act, +(at || 0), Object.assign({}, MODE[m] || {})]); }
} else {
  for (const id of (process.env.WEAPONS || 'pip,buzz,rivet').split(',')) {
    SHOTS.push([id, 'Idle', 0, {}], [id, 'Sprint', 0.25, { sprint: 1 }], [id, 'Slide', 0.3, { slide: 1 }], [id, 'Reload', 0.53, {}], [id, 'Idle', 0, { aim: 1 }]);
  }
}
const CROP = process.env.CROP ? (([x, y, width, height]) => ({ x, y, width, height }))(process.env.CROP.split(',').map(Number)) : undefined;
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = await serve();
  const browser = await chromium.launch({ args: ARGS });
  const pg = await (await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1 })).newPage();
  const logs = [];
  pg.on('pageerror', e => logs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
  await pg.goto('http://localhost:' + server.address().port + '/Source/dev.html?autotest=1');
  await pg.waitForFunction(() => window.__TEST__ && IB.Game.mode === 'play', null, { timeout: 60000 });
  if (process.env.GEAR) await pg.evaluate(() => { window.__GEAR = true; });
  await pg.evaluate((yaw) => {
    const G = IB.Game, W = IB.Weapons;
    G.player.protect = 1e9; G.guard.on = false; __TEST__.setTier('high'); G.player.yaw = yaw; G.player.pitch = 0.05;
    G.run.started = false; G.run.introT = 1e9;   // hold the intro: no waves, no robots wandering into the shot
    IB.MODELLED_WEAPONS.forEach(id => W.give(G.ws, id));
    ['hud', 'touch'].forEach(id => { const el = document.getElementById(id); if (el) el.style.visibility = 'hidden'; });
    const orig = W.pose;
    W.pose = function (s, dt, player) {
      const o = window.__VM; if (!o) return orig.apply(this, arguments);
      IB.AI.robots.forEach(r => { if (r.on) r.y = -50; });
      const sp = o.sprint ? 7.2 : 0;
      const fp = Object.assign({}, player, { vx: -Math.sin(player.yaw) * sp, vz: -Math.cos(player.yaw) * sp, vy: 0, onGround: true, sliding: !!o.slide,
        sprinting: !!o.sprint, dip: 0, landKick: 0, bobT: 0 });
      Object.assign(s, { flashT: 0, aim: o.aim || 0, sprintK: o.sprint ? 1 : 0, kickZ: 0, kickZv: 0, kickR: 0, kickRv: 0, swayX: 0, swayY: 0, strafe: 0, vert: 0, slideK: o.slide ? 1 : 0 });
      const clip = W.clips[(o.key || W.models[s.cur].key) + '_' + o.act];
      W.mixer.stopAllAction();
      const act = W.mixer.clipAction(clip); act.reset(); act.setEffectiveWeight(1); act.play(); act.time = o.at * clip.duration;
      W.action = act; W.animName = o.slide ? 'Slide' : o.sprint ? 'Sprint' : 'Idle'; W.animOnce = false;
      orig.call(this, s, 0, fp, 0, 0, true, 0);
    };
    // GEAR=1: every gun wears every attachment it takes (legendary grip, scope, acid muzzle, extended mag)
    if (window.__GEAR) {
      const L = IB.Loot, g = IB.Gear.gear(G);
      IB.MODELLED_WEAPONS.forEach(id => Object.keys(IB.LOOT.types).forEach(t => {
        const it = L.makeItem(t, 'legendary', 12, Math.random);
        if (L.compatible(it, id, IB.WEAPONS[id])) { L.addItem(g, it) || (it.id = 'x' + Math.random(), g.inv.push(it)); L.attach(g, id, IB.WEAPONS[id], it.id); }
      }));
      G.slot.arsenal = IB.MODELLED_WEAPONS.slice(); IB.Gear.refresh(G);
    }
  }, +(process.env.YAW || 0.9));
  for (const [id, act, at, o] of SHOTS) {
    await pg.evaluate(([id, act, at, o]) => {
      const G = IB.Game, W = IB.Weapons;
      IB.Input.aim = !!o.aim;
      const s = G.ws;
      if (IB.WEAPONS[id].cls === 'melee') {
        // freeze one frame of a swing: start it, then make it last forever (no hit, no re-draw of the gun)
        s.melee = null; W.meleeStart(s, id); s.melee.dur = 1e9; s.melee.hits = 2; o = Object.assign({ key: id.toUpperCase() }, o);
      } else { s.melee = null; W.equip(s, id, true); s.state = 'idle'; }
      window.__VM = Object.assign({ act: act, at: at }, o);
    }, [id, act, at, o]);
    await pg.waitForTimeout(700);
    const name = [id, act.toLowerCase() + (at ? Math.round(at * 100) : ''), o.aim ? 'ads' : o.sprint ? 'sprint' : o.slide ? 'slide' : ''].filter(Boolean).join('-');
    await pg.screenshot({ path: path.join(OUT, name + '.png'), timeout: 180000, clip: CROP });
    console.log('shot', name);
  }
  if (logs.length) console.log('page errors:', logs.join(' | '));
  await browser.close(); server.close();
  process.exit(logs.length ? 1 : 0);
})();
