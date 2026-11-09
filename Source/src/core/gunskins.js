/* INKBOLT gun skins: every gun's own colourway and how each rarity tier (src/game/wdrops.js TIERS) dresses it up.
   Pure, no DOM (unit-tested); src/game/gunskins.js turns a skin into a palette texture + toon material.

   The weapons palette (blender/fam_weapons.py) paints each gun with a handful of cells; a skin recolours them per
   gun and tier and flags some for the shader:
     body  'gunmetal'  receivers, slides, barrels' housings      frame 'gun2'   polymer frames, mags
     acc   'gun3'      handguards, panels, machined accents      furn  'furn'   pistol grips and stocks
     trim  'trim'      accent stripes / rings                    steel 'steel', steel2 'steel2', red 'red', lens 'lens'
   Flags (shader, per cell): 'pat' the material's pattern (wood, carbon, camo, hex, filigree, sheen) in its second
   colour; 'glow' an unlit emissive line that breathes; 'shim' a slow bright sweep (Legendary); 'patshim' both.
   Tiers in a clear progression:
     gray   Standard   the gun's own colourway (natural materials like wood or carbon keep their grain)
     green  Tuned      green accents: green trim, green-tinted panels, brighter steel
     blue   Rare       blue anodised body and panels, ice-blue trims, polished steel, a soft anodising sheen
     purple Epic       deep violet with a patterned finish (camo / hex / carbon by gun), glowing violet details
     orange Legendary  one of several premium finishes picked per gun (S.LEGEND, S.GUNS[id].leg), each with a
                       shimmer sweep and a glow in its own colour: black lacquer + gold filigree, pearl + rose gold,
                       obsidian with molten veins, chrome + oil-slick iridescence, crimson lacquer + engraved silver,
                       aurora nebula, ivory + damascus steel
   Names: Standard guns keep their model name ('AR-22 Rivet'); the other tiers drop the model code for a tier word
   picked per gun ('Tuned Rivet', 'Cobalt Rivet', 'Nightshade Rivet', 'Sunforged Rivet').
   Feel (no stat change): the shot's pitch / punch, an extra ring layer from Epic, the muzzle flash and tracer tints. */
(function (IB) {
  'use strict';
  var S = {};
  // the weapons palette cells, in Blender order (fam_weapons.py: ib_lib BASE + the weapons list); the runtime indexes
  // the 8 x 8 cell grid with these
  S.CELLS = ['HULL', 'ink', 'paper', 'white', 'teal', 'amber', 'gunmetal', 'red', 'gun2', 'gun3', 'steel', 'steel2', 'brass',
    'lens', 'glove', 'glove2', 'glove3', 'sleeve', 'sleeve2', 'sleeve3', 'chip', 'chip2', 'ammo', 'ammo2', 'ammo3', 'health',
    'health2', 'health3', 'glove4', 'olive', 'olive2', 'olive3', 'furn', 'trim'];
  var ROLE = { body: 'gunmetal', frame: 'gun2', acc: 'gun3', furn: 'furn', trim: 'trim', steel: 'steel', steel2: 'steel2', red: 'red', lens: 'lens' };
  S.ROLE = ROLE;
  S.PATTERNS = { none: 0, camo: 1, hex: 2, carbon: 3, wood: 4, filigree: 5, sheen: 6, veins: 7, oil: 8, aurora: 9, damascus: 10, pearl: 11 };

  /* per gun: base colourway (Standard), the Standard material pattern (pat: {type, on: [roles], col}),
     the Epic pattern and the Legendary furniture tone. Colours chosen to read in the toon ramp next to the ink. */
  var STEEL = '#B7BDC9', STEEL2 = '#8C92A3';
  S.GUNS = {
    pip: { body: '#4C5A78', frame: '#2F303C', acc: '#7D8BA8', furn: '#363445', trim: '#FFB21E', epic: 'carbon', leg: 'pearl', note: 'slate-blue slide, black polymer' },
    handcannon: { body: '#8E97A6', frame: '#5D6575', acc: '#6B7384', furn: '#7A4627', trim: '#E3B04B', steel: '#CDD3DC',
      pat: { type: 'wood', on: ['furn'], col: '#4F2A15' }, epic: 'carbon', leg: 'damascus', note: 'stainless frame, walnut grips' },
    twintap: { body: '#3B3F4A', frame: '#C9573F', acc: '#E27B5E', furn: '#B44C37', trim: '#FFE08A', epic: 'hex', leg: 'oil', note: 'coral polymer, dark slide' },
    buzz: { body: '#3A3A44', frame: '#D9A21B', acc: '#4B4B57', furn: '#2E2E37', trim: '#F0443A', epic: 'carbon', leg: 'gold', note: 'safety-yellow polymer' },
    whisk: { body: '#2E7F86', frame: '#22303A', acc: '#3FA7A8', furn: '#22303A', trim: '#FFB21E', epic: 'hex', leg: 'aurora', note: 'teal anodised, gunmetal frame' },
    hornet: { body: '#D88A1E', frame: '#2A2730', acc: '#F2B233', furn: '#2A2730', trim: '#FFE3A0', epic: 'hex', leg: 'obsidian', note: 'hornet amber and black' },
    rivet: { body: '#4A4A54', frame: '#B89A6A', acc: '#C9AE7E', furn: '#AE9061', trim: '#FFB21E', epic: 'camo', leg: 'gold', note: 'desert-tan furniture' },
    triplet: { body: '#3F4554', frame: '#6E7A44', acc: '#8D9A5A', furn: '#5C6738', trim: '#F2D14B', epic: 'camo', leg: 'crimson', note: 'olive drab' },
    longtom: { body: '#3E4250', frame: '#30323C', acc: '#8B5A33', furn: '#8B5A33', trim: '#E8C27A',
      pat: { type: 'wood', on: ['furn', 'acc'], col: '#5A3519' }, epic: 'camo', leg: 'gold', note: 'blued steel, oiled walnut' },
    brick: { body: '#5A5E52', frame: '#4A5240', acc: '#717A62', furn: '#3F4636', trim: '#FF8A1E', epic: 'camo', leg: 'oil', note: 'field grey-green' },
    needle: { body: '#3A3D46', frame: '#4E6B45', acc: '#6C8A5E', furn: '#4E6B45', trim: '#E9D58A', epic: 'camo', leg: 'damascus', note: 'forest-green chassis' },
    scrapper: { body: '#3C3A42', frame: '#2F2D34', acc: '#5A5662', furn: '#9A6236', trim: '#F0443A',
      pat: { type: 'wood', on: ['furn'], col: '#633A1C' }, epic: 'carbon', leg: 'crimson', note: 'parkerised steel, wood stock' },
    thunder: { body: '#2E3442', frame: '#3B4FA0', acc: '#5B73D8', furn: '#2B3150', trim: '#FFE14A', epic: 'hex', leg: 'aurora', note: 'indigo polymer, volt-yellow' },
    vanguard: { body: '#3B3E46', frame: '#6B6F5A', acc: '#888C72', furn: '#55594A', trim: '#D9DCC4', epic: 'camo', leg: 'gold', note: 'ranger green' },
    railspike: { body: '#30333C', frame: '#E6E4EE', acc: '#2B2D34', furn: '#E6E4EE', trim: '#1FD1E0', lens: '#7CF3FF',
      pat: { type: 'carbon', on: ['acc', 'body'], col: '#4A4E5A' }, epic: 'hex', leg: 'oil', note: 'white polymer, carbon rails, cyan' },
    hothead: { body: '#3E3C46', frame: '#B8432F', acc: '#D9623E', furn: '#3E3C46', trim: '#FFC23A', epic: 'carbon', leg: 'obsidian', note: 'brick-red tubes' },
    murmur: { body: '#2F4A4C', frame: '#24343A', acc: '#4F8C88', furn: '#24343A', trim: '#B7F0E0', epic: 'hex', leg: 'pearl', note: 'deep teal, mint trims' }
  };
  /* Legendary finishes, one per gun (S.GUNS[id].leg); only some are gold. c: role colours; flag: shader flags per
     role; pat / patCol: the finish pattern on 'pat' cells (oil, aurora and pearl colour themselves); patGlow: the
     pattern is emissive (molten veins); glow: the glow cells' colour; shim: the sweep's colour; word: tier names. */
  S.LEGEND = {
    gold: { word: ['Sunforged', 'Goldcrest', 'Kingsgold'], pat: 'filigree', patCol: '#D9A441', glow: '#FFB347', shim: '#FFEBB3',
      c: { body: '#241C28', frame: '#2F2329', acc: '#E2AA45', furn: '#5B2A1C', steel: '#F4D88A', steel2: '#C99A45', trim: '#FFB347', lens: '#FFD27A', red: '#FF8A2E' },
      flag: { furn: 'pat', acc: 'shim', steel: 'shim', steel2: 'shim', body: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    pearl: { word: ['Seraph', 'Pearlcrest', 'Rosemoon'], pat: 'pearl', patCol: '#F6D9E4', glow: '#FFB8C8', shim: '#FFF1F4',
      c: { body: '#ECE8EF', frame: '#D9D3DE', acc: '#D8957C', furn: '#E7DFE6', steel: '#EAB6A0', steel2: '#B97A66', trim: '#FFB8C8', lens: '#FFD6E0', red: '#FF8FB0' },
      flag: { body: 'patshim', frame: 'pat', furn: 'pat', acc: 'shim', steel: 'shim', steel2: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    obsidian: { word: ['Magmaborn', 'Cinderheart', 'Obsidian'], pat: 'veins', patCol: '#FF7A1F', patGlow: 1, glow: '#FF8A2E', shim: '#FFB070',
      c: { body: '#17141A', frame: '#211B22', acc: '#2A2229', furn: '#1C171D', steel: '#5B5560', steel2: '#3C363F', trim: '#FF8A2E', lens: '#FFB45A', red: '#FF5A1F' },
      flag: { body: 'patshim', frame: 'pat', furn: 'pat', acc: 'pat', steel: 'shim', steel2: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    oil: { word: ['Prismatic', 'Spectre', 'Mirage'], pat: 'oil', patCol: '#9AD8FF', glow: '#8FF4FF', shim: '#FFFFFF',
      c: { body: '#C9D0DA', frame: '#2A2D36', acc: '#B6BECB', furn: '#24262E', steel: '#EEF2F7', steel2: '#AEB7C6', trim: '#8FF4FF', lens: '#C7A2FF', red: '#FF7AE0' },
      flag: { body: 'patshim', acc: 'patshim', steel: 'shim', steel2: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    crimson: { word: ['Bloodroyal', 'Cardinal', 'Vermilion'], pat: 'filigree', patCol: '#BCC1CB', patS: 0.62, glow: '#FF6A6A', shim: '#FFF4F0',
      c: { body: '#6E0F1E', frame: '#620D1B', acc: '#C9CED8', furn: '#5A0C18', steel: '#E7EAF0', steel2: '#A9AFBC', trim: '#F2F4F8', lens: '#FF8C8C', red: '#FF5A5A' },
      flag: { body: 'patshim', frame: 'patshim', furn: 'pat', acc: 'shim', steel: 'shim', steel2: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    aurora: { word: ['Starfall', 'Nebula', 'Borealis'], pat: 'aurora', patCol: '#6AF0D0', glow: '#7CFFE0', shim: '#E6FFFA',
      c: { body: '#141A3A', frame: '#1A1433', acc: '#2A2F5E', furn: '#1D1840', steel: '#D9E2F5', steel2: '#9AA6C8', trim: '#7CFFE0', lens: '#E09BFF', red: '#FF7AD8' },
      flag: { body: 'patshim', frame: 'pat', acc: 'pat', furn: 'pat', steel: 'shim', trim: 'glow', lens: 'glow', red: 'glow' } },
    damascus: { word: ['Damask', 'Tempered', 'Ivorybrand'], pat: 'damascus', patCol: '#3A3E47', glow: '#9FE8FF', shim: '#F4F8FF',
      c: { body: '#A7ACB5', frame: '#3A3640', acc: '#B9BDC5', furn: '#EDE3CF', steel: '#D5D9E0', steel2: '#8E939E', trim: '#D9B676', lens: '#B6EEFF', red: '#E0A060' },
      flag: { body: 'patshim', acc: 'pat', steel: 'shim', steel2: 'shim', trim: 'shim', lens: 'glow', red: 'glow' } }
  };
  var DEF = { body: '#5A586D', frame: '#48475A', acc: '#6E6B85', furn: '#4A4257', trim: '#FFB21E', epic: 'carbon' };

  // ---------- colour helpers (hex <-> rgb, mix) ----------
  function rgb(h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
  function hex(c) { return '#' + c.map(function (v) { var s = Math.max(0, Math.min(255, Math.round(v))).toString(16); return s.length < 2 ? '0' + s : s; }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = rgb(a), y = rgb(b); return hex([0, 1, 2].map(function (i) { return x[i] + (y[i] - x[i]) * t; })); }
  S.mix = mix; S.rgb = rgb;

  S.TIER_IDS = ['gray', 'green', 'blue', 'purple', 'orange'];
  function rankOf(t) { var i = S.TIER_IDS.indexOf(t); return i < 0 ? 0 : i; }
  S.rank = rankOf;

  /* the skin of a gun at a tier: { cells: {cellName: {hex, flag}}, pat: {type, col, scale}, glow, shimmer } */
  S.skin = function (gunId, tier) {
    var g = S.GUNS[gunId] || DEF, r = rankOf(tier), c = {}, flag = {}, pat = { type: 'none', col: '#000000', scale: 1 };
    var k; for (k in ROLE) c[k] = g[k] || DEF[k] || null;
    c.steel = g.steel || STEEL; c.steel2 = g.steel2 || STEEL2; c.red = g.red || '#F0443A'; c.lens = g.lens || '#86EAF2';
    if (g.pat) { pat = { type: g.pat.type, col: g.pat.col, scale: 1 }; g.pat.on.forEach(function (role) { flag[role] = 'pat'; }); }
    var glow = '#000000', shimmer = 0, legend = null;
    if (r === 1) {          // Tuned: green accents
      c.trim = '#6BE05A'; c.acc = mix(c.acc, '#4FB04A', 0.72); c.steel = mix(c.steel, '#FFFFFF', 0.2);
      if (g.pat && g.pat.on.indexOf('acc') >= 0) c.acc = g.acc;   // keep a wooden handguard wooden
    } else if (r === 2) {   // Rare: blue anodised + trims
      c.body = mix(c.body, '#2B5FC9', 0.84); c.acc = mix(c.acc, '#4A8DF0', 0.78); c.frame = mix(c.frame, '#22345A', 0.78);
      c.furn = g.pat && g.pat.type === 'wood' ? c.furn : mix(c.furn, '#1A2644', 0.8);
      c.trim = '#A6DCFF'; c.steel = '#DCE3EE'; c.steel2 = '#A9B6CC'; c.lens = '#9FE6FF';
      if (!g.pat || g.pat.type !== 'wood') { flag.acc = 'pat'; flag.body = 'pat'; pat = { type: 'sheen', col: '#7FB6FF', scale: 1 }; }
      else if (flag.acc === 'pat') c.acc = g.acc;   // a wooden handguard stays wood
    } else if (r === 3) {   // Epic: violet, patterned finish, glowing details
      c.body = '#35214F'; c.acc = '#8B4FE6'; c.frame = mix(c.frame, '#1E1428', 0.62); c.furn = '#3F2766'; c.steel = '#C9BEE0'; c.steel2 = '#8D7FB0';
      c.trim = '#E59BFF'; c.lens = '#F0B8FF'; c.red = '#FF6AD5';
      var et = g.epic || 'carbon';
      pat = { type: et, col: et === 'carbon' ? '#5A3C86' : et === 'hex' ? '#B98AFF' : '#9A6FE0', scale: 1 };
      flag = { furn: 'pat', frame: 'pat' }; if (et !== 'camo') flag.body = 'pat';
      flag.trim = 'glow'; flag.lens = 'glow'; flag.red = 'glow'; glow = '#D98BFF';
    } else if (r === 4) {   // Legendary: the gun's premium finish (S.LEGEND)
      var L = S.LEGEND[g.leg] || S.LEGEND.gold;
      for (k in L.c) c[k] = L.c[k];
      pat = { type: L.pat, col: L.patCol, scale: L.patS || 1 };
      flag = {}; for (k in L.flag) flag[k] = L.flag[k];
      glow = L.glow; shimmer = 1;
      legend = { id: S.LEGEND[g.leg] ? g.leg : 'gold', shimCol: L.shim, patGlow: L.patGlow || 0 };
    }
    var cells = {};
    for (k in ROLE) if (c[k]) cells[ROLE[k]] = { hex: c[k], flag: flag[k] || null };
    return { gun: gunId, tier: S.TIER_IDS[r], cells: cells, pat: pat, glow: glow, shimmer: shimmer,
      shimCol: legend ? legend.shimCol : '#FFEBB3', patGlow: legend ? legend.patGlow : 0, legend: legend ? legend.id : null };
  };

  // ---------- names ----------
  S.WORDS = {
    green: ['Tuned', 'Honed', 'Keen', 'Trued'],
    blue: ['Cobalt', 'Azure', 'Bluesteel', 'Tidewater'],
    purple: ['Nightshade', 'Phantom', 'Hexweave', 'Umbral'],
    orange: ['Sunforged', 'Goldcrest', 'Dawnfire', 'Kingsgold']
  };
  function hash(s) { var h = 7; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return h; }
  S.word = function (gunId, tier) {
    var g = S.GUNS[gunId], w = tier === 'orange' && g && S.LEGEND[g.leg] ? S.LEGEND[g.leg].word : S.WORDS[tier]; return w ? w[hash(String(gunId)) % w.length] : ''; };
  /* display name: base = the gun's name (or GunLevel.displayName with a launcher's element) */
  S.name = function (gunId, tier, base) {
    var w = S.word(gunId, tier); if (!w) return base;
    var p = String(base).split(' ');
    var core = p.length > 1 && /\d/.test(p[0]) ? p.slice(1).join(' ') : base;   // 'AR-22 Rivet' -> 'Rivet'
    return w + ' ' + core;
  };

  // ---------- feel: shot sound, muzzle flash and tracer tints (no stat change) ----------
  S.FEEL = {
    gray: { pitch: 1.00, gain: 1.00, ring: 0, flash: '#FFB21E', tracer: '#FFB21E' },
    green: { pitch: 0.99, gain: 1.04, ring: 0, flash: '#B5F06A', tracer: '#C6F58A' },
    blue: { pitch: 0.975, gain: 1.08, ring: 0, flash: '#8CCBFF', tracer: '#A6DCFF' },
    purple: { pitch: 0.96, gain: 1.12, ring: 0.16, flash: '#E08CFF', tracer: '#E59BFF' },
    orange: { pitch: 0.945, gain: 1.16, ring: 0.22, flash: '#FFC23A', tracer: '#FFD56A' }
  };
  S.feel = function (tier) { return S.FEEL[S.TIER_IDS[rankOf(tier)]]; };

  IB.GunSkinData = S;
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
