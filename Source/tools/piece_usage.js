// Kit piece usage (tactical look plan Stage 11.1): which pieces of a theme's kit cover the most screen.
//   node Source/tools/piece_usage.js [outFile.json] [plan ...]        (default: every campaign plan)
// Builds each level in the page with ?zcheck=1 (zones.js then tags every placed piece: Z.pidNames), counts the
// placements of each piece and its visible area (sum of the bounding-box face areas x count), and writes a ranked
// list per theme. The top 15 to 25 pieces of a kit cover most of what the player sees: they get the detail first.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const OUT = path.resolve(process.argv[2] || 'Source/dist/look/piece-usage.json');
let PLANS = process.argv.slice(3);

(async () => {
  const server = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.webp') ? 'image/webp' : 'text/javascript' }); r.end(d); }); }).listen(0, () => res(s)); });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(process.env.HTML || 'Play Inkbolt.html') + '?autotest=1&zcheck=1&look=classic';
  const browser = await chromium.launch({ args: ARGS });
  const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
  if (!PLANS.length) {
    const pg = await browser.newPage();
    await pg.goto(base + '&plan=mountains');
    await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 180000 });
    PLANS = await pg.evaluate(() => Object.keys(IB.LEVEL_PLANS || {}).filter(k => k !== 'toytown'));
    await pg.close();
  }
  for (const plan of PLANS) {
    const pg = await browser.newPage({ viewport: { width: 320, height: 180 } });
    try {
      await pg.goto(base + '&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 240000 });
      const rows = await pg.evaluate(() => {
        const cnt = {};
        Object.values(IB.Zones.pidNames).forEach(n => { cnt[n] = (cnt[n] || 0) + 1; });
        IB.Zones.pidNames = {};
        return Object.keys(cnt).map(n => {
          const g = IB.Assets.geo[n]; if (!g.boundingBox) g.computeBoundingBox();
          const s = g.boundingBox.getSize(new THREE.Vector3());
          const area = 2 * (s.x * s.y + s.y * s.z + s.x * s.z);
          const tris = (g.index ? g.index.count : g.attributes.position.count) / 3;
          return { name: n, family: IB.Assets.family[n], count: cnt[n], area: +(area * cnt[n]).toFixed(1), tris };
        }).sort((a, b) => b.area - a.area);
      });
      out[plan] = rows;
      const tot = rows.reduce((t, r) => t + r.area, 0);
      let acc = 0, k = 0; for (const r of rows) { acc += r.area; k++; if (acc >= tot * 0.8) break; }
      console.log(plan, rows.length, 'pieces;', k, 'cover 80% of the area; top:', rows.slice(0, 5).map(r => r.name.replace(/^KIT_[A-Z0-9]+_/, '') + 'x' + r.count).join(' '));
    } catch (e) { console.log(plan, 'FAIL', e.message.slice(0, 160)); }
    await pg.close();
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(out));
  }
  await browser.close(); server.close();
})();
