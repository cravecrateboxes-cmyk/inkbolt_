// INKBOLT HUD lock (tactical look plan, Stage 0.5). Proves the look work never changes the HUD.
//   node Source/tests/e2e/hud-lock.spec.js            check against the committed baselines
//   UPDATE=1 node Source/tests/e2e/hud-lock.spec.js   write the baselines (only ever from the base commit)
// Env: HTML=<file> (default "Play Inkbolt.html"), EXTRA=<query string> (e.g. look=classic), ONLY=files,hud,bars.
// 1. File lock: no diff against the base commit in the HUD files of hard rule 1.2.1.
// 2. HUD pixel lock: the 3D canvas hidden, a fixed dark backdrop, a frozen HUD state; 1280x720, 1920x1080 and
//    844x390 (touch). Pass: at most 0.02% of pixels differ, and none by more than 2/255.
// 3. Enemy bar lock: robots at 5 to 14 m with hurt bars; everything else in the world scene hidden over a fixed
//    clear colour so only the bars are drawn. Pass: 99% of the bar pixels within 3/255.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs'), cp = require('child_process');
const ROOT = path.resolve(__dirname, '../../..');
const BASE_COMMIT = '5cfa145';
const PROTECTED = ['Source/src/ui/hud.js', 'Source/src/ui/hud.css', 'Source/src/ui/hudf.css', 'Source/src/ui/skillhud.js',
  'Source/src/ui/loothud.js', 'Source/src/ui/tabmenu.js', 'Source/src/ui/menus.js', 'Source/src/ui/gear.js',
  'Source/src/ui/fieldkit.css', 'Source/src/ui/ui.css', 'Source/src/ui/loader.js', 'Source/src/ui/loader.css',
  'Source/src/ui/skillicons.js', 'Source/src/game/hpbars.js', 'Source/src/game/dmgnum.js'];
const HTML = process.env.HTML || 'Play Inkbolt.html';
const EXTRA = process.env.EXTRA ? '&' + process.env.EXTRA.replace(/^[?&]/, '') : '';
const UPDATE = process.env.UPDATE === '1';
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : ['files', 'hud', 'bars'];
const BASE_DIR = path.join(__dirname, 'review', 'hud-lock');
const OUT_DIR = path.join(ROOT, 'Source', 'dist', 'hud-lock');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const VIEWS = [
  { name: 'desktop720', w: 1280, h: 720, touch: false },
  { name: 'desktop1080', w: 1920, h: 1080, touch: false },
  { name: 'phone-sideways', w: 844, h: 390, touch: true }
];
let failures = 0;
function fail(msg) { failures++; console.log('FAIL ' + msg); }

function fileLock() {
  const existing = PROTECTED.filter(p => fs.existsSync(path.join(ROOT, p)));
  const r = cp.spawnSync('git', ['diff', '--name-only', BASE_COMMIT, '--', ...existing], { cwd: ROOT, encoding: 'utf8' });
  if (r.status !== 0) return fail('file lock: git diff failed: ' + (r.stderr || '').trim());
  const changed = r.stdout.trim().split('\n').filter(Boolean);
  if (changed.length) fail('file lock: protected HUD files changed since ' + BASE_COMMIT + ': ' + changed.join(', '));
  else console.log('ok   file lock (' + existing.length + ' protected files unchanged since ' + BASE_COMMIT + ')');
}

// compare two PNGs with Pillow: prints "<share of pixels differing> <max difference> <share within tol>"
function compare(a, b, tol, mask) {
  const py = `
import sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB'), dtype=np.int16)
b = np.asarray(Image.open(sys.argv[2]).convert('RGB'), dtype=np.int16)
if a.shape != b.shape:
    print('size', a.shape, b.shape); sys.exit(0)
d = np.abs(a - b).max(-1)
m = np.ones(d.shape, bool)
if sys.argv[4] == 'bars':
    # the bar pixels of the baseline, eroded by 1 px: the background behind the bars is graded with the look on,
    # so antialiased edges legitimately differ; the bars' own pixels must not
    bg = np.array([40, 40, 40])
    m = np.abs(a - bg).max(-1) > 6
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        m = m & np.roll(np.roll(m, dy, 0), dx, 1)
n = max(1, int(m.sum()))
print('%.6f %d %.6f %d' % (((d > 0) & m).sum() / n, int(d[m].max()) if m.any() else 0, ((d <= int(sys.argv[3])) & m).sum() / n, n))
`;
  const r = cp.spawnSync('python3', ['-c', py, a, b, String(tol), mask || 'all'], { encoding: 'utf8' });
  const p = r.stdout.trim().split(' ');
  if (p[0] === 'size') return { size: true, text: r.stdout.trim() };
  return { diff: +p[0], max: +p[1], within: +p[2], n: +p[3] };
}

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => {
        if (e) { r.writeHead(404); return r.end(); }
        r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.css') ? 'text/css' : f.endsWith('.woff2') ? 'font/woff2' : 'text/javascript' });
        r.end(d);
      });
    }).listen(0, () => res(s));
  });
}

// a fixed HUD state, then the game loop is stopped so nothing moves
async function freezeHud(pg) {
  await pg.evaluate(() => {
    const G = IB.Game, H = IB.HUD, p = G.player, noop = () => {};
    p.protect = 1e9; G.settings.shake = false; G.trauma = 0;
    IB.AI.robots.forEach(r => { r.on = false; });
    H.health(100, 100); H.health(64, 100);
    H.weapon({ id: 'rivet', name: 'AR-22 Rivet', cls: 'rifle', mag: 22, magSize: 30, reserve: 150, reloading: false, reloadFrac: 0 });
    H.slots([{ slot: 1, cls: 'pistol', name: 'P-12 Warden', on: false }, { slot: 2, cls: 'smg', name: 'KV-9 Buzzsaw', on: false }, { slot: 3, cls: 'rifle', name: 'AR-22 Rivet', on: true }]);
    H.stamina(0.55, false);
    H.score(0, 0, 83, 12);
    if (IB.LootHUD && IB.LootHUD.shield) IB.LootHUD.shield({ cur: 23, max: 34, charging: false });
    ['health', 'ammo', 'weapon', 'slots', 'stamina', 'score', 'kit', 'level', 'gems', 'pips', 'feed', 'toast', 'pickup', 'hit', 'arc', 'damageFlash'].forEach(k => { if (H[k]) H[k] = noop; });
    if (IB.LootHUD) ['shield', 'loot'].forEach(k => { if (IB.LootHUD[k]) IB.LootHUD[k] = noop; });
  });
  await pg.waitForTimeout(2200);   // HUD tweens settle
  await pg.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await pg.waitForTimeout(300);
}

async function hudShot(browser, base, v) {
  const ctx = await browser.newContext({ viewport: { width: v.w, height: v.h }, hasTouch: v.touch, isMobile: v.touch, deviceScaleFactor: 1 });
  const pg = await ctx.newPage(); const logs = [];
  pg.on('pageerror', e => logs.push(e.message));
  await pg.goto(base + '&plan=mountains');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 150000 });
  await pg.evaluate(() => { IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; }); __TEST__.teleport(0); __TEST__.look(0, 0); });
  await pg.waitForTimeout(800);
  await freezeHud(pg);
  await pg.evaluate(() => {
    const c = document.getElementById('c'); c.style.visibility = 'hidden';
    document.documentElement.style.background = '#202028'; document.body.style.background = '#202028';
  });
  const file = path.join(UPDATE ? BASE_DIR : OUT_DIR, 'hud-' + v.name + '.png');
  await pg.screenshot({ path: file, timeout: 240000, animations: 'disabled' });
  await ctx.close();
  return { file, logs };
}

async function barShot(browser, base) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage(); const logs = [];
  pg.on('pageerror', e => logs.push(e.message));
  await pg.goto(base + '&plan=mountains');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 150000 });
  await pg.evaluate(() => { __TEST__.teleport(0); __TEST__.look(0, 0); IB.Game.player.protect = 1e9; });
  await pg.waitForTimeout(800);
  await pg.evaluate(() => {
    const G = IB.Game, p = G.player, AI = IB.AI;
    AI.robots.forEach(r => { r.on = false; });
    const fx = -Math.sin(p.yaw), fz = -Math.cos(p.yaw), rx = Math.cos(p.yaw), rz = -Math.sin(p.yaw);
    [[-1.4, 5, 'crawler', 0.35], [1.6, 8, 'gunner', 0.6], [-2.6, 11, 'bomber', 0.2], [2.2, 14, 'drone', 0.8]].forEach(([side, fwd, type, frac]) => {
      const x = p.x + fx * fwd + rx * side, z = p.z + fz * fwd + rz * side;
      const s = __TEST__.spawnRobot(type, x, z); if (s < 0) return;
      const r = AI.types[type].slots[s]; r.yaw = Math.atan2(p.x - x, p.z - z); r.hp = r.maxHp * frac;
    });
    AI.update = () => {}; IB.Projectiles.update = () => {}; AI.spawn = () => null;
  });
  await pg.waitForTimeout(4500);   // chip segments follow, hit flashes fade
  await pg.evaluate(() => new Promise(done => {
    const raf = window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame = () => 0;   // stop the game loop
    const R = IB.Render;
    let bars = null;
    R.scene.traverse(o => { if (o.material && o.material.uniforms && o.material.uniforms.uPx && o.material.uniforms.uS) bars = o; });
    // only the bars, through the real render path (R.render -> IB.Post when the look is on), over a flat grey
    const only = new THREE.Scene(); only.add(R.sky); R.sky.visible = false; if (bars) only.add(bars);
    R.scene = only; R.renderer.setClearColor(0x282828, 1);
    document.querySelectorAll('body > *').forEach(e => { if (e.id !== 'c' && !e.contains(document.getElementById('c'))) e.style.visibility = 'hidden'; });
    raf(() => { R.render(false); raf(() => done()); });
  }));
  const file = path.join(UPDATE ? BASE_DIR : OUT_DIR, 'bars-desktop720.png');
  await pg.screenshot({ path: file, timeout: 240000, animations: 'disabled' });
  await ctx.close();
  return { file, logs };
}

(async () => {
  fs.mkdirSync(BASE_DIR, { recursive: true }); fs.mkdirSync(OUT_DIR, { recursive: true });
  if (ONLY.includes('files')) fileLock();
  if (ONLY.includes('hud') || ONLY.includes('bars')) {
    const server = await serve();
    const base = 'http://localhost:' + server.address().port + '/' + encodeURI(HTML) + '?autotest=1' + EXTRA;
    const browser = await chromium.launch({ args: ARGS });
    const jobs = [];
    if (ONLY.includes('hud')) VIEWS.forEach(v => jobs.push(['hud ' + v.name, () => hudShot(browser, base, v), 'all', 2, 0.0002]));
    if (ONLY.includes('bars')) jobs.push(['enemy bars', () => barShot(browser, base), 'bars', 3, 0.01]);
    for (const [name, run, mask, tol, share] of jobs) {
      let res;
      try { res = await run(); } catch (e) { fail(name + ': ' + e.message.slice(0, 200)); continue; }
      if (res.logs.length) fail(name + ': page errors: ' + res.logs.slice(0, 3).join(' | '));
      if (UPDATE) { console.log('base ' + path.relative(ROOT, res.file)); continue; }
      const ref = path.join(BASE_DIR, path.basename(res.file));
      if (!fs.existsSync(ref)) { fail(name + ': no baseline ' + path.relative(ROOT, ref)); continue; }
      const c = compare(ref, res.file, tol, mask);
      if (c.size) { fail(name + ': ' + c.text); continue; }
      const ok = mask === 'bars' ? c.within >= 1 - share : (c.diff <= share && c.max <= tol) || c.diff === 0;
      const line = name + ': ' + (c.diff * 100).toFixed(3) + '% of ' + c.n + ' px differ, max ' + c.max + '/255, ' + (c.within * 100).toFixed(2) + '% within ' + tol;
      if (ok) console.log('ok   ' + line); else fail(line + '  (shot: ' + path.relative(ROOT, res.file) + ')');
    }
    await browser.close(); server.close();
  }
  console.log(failures ? failures + ' HUD lock failure(s)' : 'HUD lock passed');
  process.exit(failures ? 1 : 0);
})();
