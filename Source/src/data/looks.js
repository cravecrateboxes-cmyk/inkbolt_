/* INKBOLT tactical look data (plan: Source/docs/tactical-look/PLAN.md, sections 4 and 6).
   Pure data + resolve(); loads in node for unit tests. A look = defaults <- family preset <- theme entry <- tier.
   Every map gets a correct look with no entry here: resolve() guesses the family from the theme's env (sky or not,
   fog brightness, sun height). A theme entry is tuning on top. Colours are display-referred [r, g, b] 0..1 unless
   named otherwise; light intensities are in the shader's linear light (section 5.4). */
(function (IB) {
  'use strict';
  var LOOKS = IB.LOOKS = {};

  LOOKS.defaults = {
    family: 'urban-ext', type: 'ext-day',
    sunI: 1.5, sunColor: null,                       // null: the theme's env.sunColor or white
    ambSky: [0.55, 0.66, 0.85], ambGround: [0.34, 0.30, 0.27], ambI: 0.40, ambFloor: 0.03,
    albSat: 0.96, albGain: 0.90, albCeil: 0.80,
    fog: { length: 160, far: null, color: null, sunGlow: [1.0, 0.86, 0.66] },   // length: metres to 63% haze at ground level
    ink: { color: '#0C0B10', px: 1.5, base: 0.0045, fade: [45, 110], vmPx: 1.3 },
    sky: { clouds: 0.5, sunDisc: true },
    floor: { cls: 1, gloss: 0.14 },                  // surface class of the code-built floor of this theme
    wet: 0, dust: null, exposure: 1.0,
    grade: { sat: 0.98, contrast: 0.20, lo: [0.96, 1.0, 1.06], hi: [1.05, 1.0, 0.94] },
    bloom: { amount: 0.5, knee: 0.35 }, vignette: 0.35, grain: 0.028,
    grid: { intensity: 1.0, radius: 13, emit: {} },  // emit: { cellName: multiplier }
    indoorAmb: 0.20
  };

  // section 4.4
  LOOKS.families = {
    'mil-ext': { type: 'ext-day', sunI: 1.6, ambI: 0.36, fog: { length: 230, sunGlow: [1.0, 0.84, 0.62] }, dust: 'wind',
      grade: { sat: 0.96, contrast: 0.22, lo: [0.95, 1.0, 1.07], hi: [1.06, 1.0, 0.92] } },
    'urban-ext': { type: 'ext-day', sunI: 1.5, ambI: 0.42, fog: { length: 260 },
      grade: { sat: 0.98, contrast: 0.20, lo: [0.95, 1.0, 1.07], hi: [1.03, 1.0, 0.97] } },
    'wild-ext': { type: 'ext-day', sunI: 1.4, ambI: 0.46, ambGround: [0.30, 0.34, 0.24], fog: { length: 150 }, dust: 'pollen',
      grade: { sat: 1.0, contrast: 0.18, lo: [0.97, 1.0, 1.04], hi: [1.03, 1.0, 0.96] } },
    'ind-int': { type: 'int-ind', ambI: 0.40, indoorAmb: 0.30, ambFloor: 0.025, fog: { length: 110 }, dust: 'beams',
      grade: { sat: 0.95, contrast: 0.22, lo: [0.94, 1.0, 1.08], hi: [1.06, 1.0, 0.92] }, floor: { cls: 1, gloss: 0.2 } },
    'dark-int': { type: 'int-dark', ambI: 0.34, indoorAmb: 0.20, ambFloor: 0.02, fog: { length: 55 }, dust: 'heavy', grid: { intensity: 0.55 },
      grade: { sat: 1.0, contrast: 0.28, lo: [0.93, 1.0, 1.09], hi: [1.05, 1.0, 0.93] }, bloom: { amount: 0.65, knee: 0.3 }, vignette: 0.42 },
    'civic-int': { type: 'int-lit', ambI: 0.50, indoorAmb: 0.55, ambFloor: 0.03, fog: { length: 320 },
      grade: { sat: 0.97, contrast: 0.18, lo: [0.98, 1.0, 1.03], hi: [1.02, 1.0, 0.98] }, floor: { cls: 10, gloss: 0.45 }, vignette: 0.28 },
    'giant-room': { type: 'int-lit', ambI: 0.55, indoorAmb: 0.60, ambSky: [0.80, 0.74, 0.66], ambGround: [0.40, 0.33, 0.27], ambFloor: 0.05,
      fog: { length: 420, sunGlow: [1.0, 0.88, 0.70] }, dust: 'motes', floor: { cls: 4, gloss: 0.22 },
      grade: { sat: 1.0, contrast: 0.16, lo: [0.99, 1.0, 1.02], hi: [1.04, 1.0, 0.95] }, vignette: 0.28 }
  };

  /* Stage 9 dressing (dress.js): decal names from data/decals.gen.js with weights. floor: open floor; base: floor cells
     hemmed in by walls or props (bases, corners); wall: plain wall faces. density scales the rates (the tier's
     density multiplies at level build); wallRate scales the wall rate only; off: true builds nothing. clutter /
     wallClutter: pieces of fps-dress.glb (KIT_DRESS_<name>, blender/fam_dress.py) on floor cells by walls and props /
     on plain wall faces; clutterRate scales both. A theme entry
     may replace any list (Stage 10). */
  LOOKS.dress = {
    'mil-ext': { density: 1.0, clutter: [['RubbleA', 2], ['RubbleB', 2], ['BrickPile', 1], ['Carton', 1], ['Sandbags', 1], ['TyreOld', 0.6], ['PipeOffcut', 1], ['CanLying', 1], ['StonesA', 1]], wallClutter: [['JunctionBox', 2], ['SignWarn', 1], ['Conduit', 2], ['Extinguisher', 1]],
      floor: [['oil', 3], ['tyre', 2], ['grime', 3], ['crack', 2], ['crack2', 1], ['patch', 1], ['scuff', 1], ['chevrons', 0.4], ['paper', 0.5]],
      base: [['grime2', 3], ['oil2', 2], ['crack3', 1], ['leaves', 0.5]],
      wall: [['grimeBase', 4], ['rust', 2], ['sootStreak', 1], ['scars', 1], ['scars2', 0.6], ['stencilDanger', 0.6], ['stencilZone', 0.6], ['crack3', 0.6]] },
    'urban-ext': { density: 1.0, clutter: [['Litter', 3], ['Can', 1], ['CanLying', 1], ['Bottle', 1], ['Carton', 1], ['CartonFlat', 1], ['LeafPile', 1], ['RubbleB', 1], ['Brick', 1]], wallClutter: [['Conduit', 2], ['JunctionBox', 2], ['Vent', 1], ['SignPlate', 1]],
      floor: [['oil', 2], ['water', 2], ['crack', 2], ['crack2', 1], ['manhole', 0.5], ['drain', 0.6], ['paper', 1], ['leaves', 1], ['grime', 3], ['patch', 1], ['tyre', 0.6]],
      base: [['grime2', 3], ['paper', 1], ['leaves', 1], ['water2', 1]],
      wall: [['grimeBase', 4], ['leak', 2], ['water2', 1], ['poster', 1], ['poster2', 1], ['poster3', 1], ['stencilNo', 0.5], ['crack3', 0.6]] },
    'wild-ext': { density: 0.7, clutter: [['StonesA', 2], ['StonesB', 2], ['GrassTuft', 3], ['GrassTuft2', 3], ['LeafPile', 1]],
      floor: [['leaves', 3], ['moss', 2], ['grime', 2], ['prints', 0.5]],
      base: [['moss', 2], ['leaves', 2], ['grime2', 1]],
      wall: [['grimeBase', 3], ['moss', 2], ['water2', 1], ['crack3', 0.5]] },
    'ind-int': { density: 1.0, clutter: [['CableCoil', 2], ['PipeOffcut', 2], ['PalletBroken', 1], ['Bucket', 1], ['CableRun', 2], ['Carton', 1], ['Can', 1]], wallClutter: [['Conduit', 3], ['JunctionBox', 2], ['Vent', 2], ['Extinguisher', 1], ['SignWarn', 1]],
      floor: [['oil', 3], ['oil2', 2], ['grime', 3], ['crack', 1], ['scuff', 2], ['grate', 0.6], ['drain', 0.6], ['chevrons', 0.6], ['puddle', 0.6], ['patch', 1]],
      base: [['oil2', 2], ['grime2', 3], ['water', 1]],
      wall: [['grimeBase', 4], ['rust', 2], ['leak', 2], ['stencilZone', 0.6], ['stencilDanger', 0.6], ['digit1', 0.2], ['digit2', 0.2], ['digit3', 0.2], ['digit4', 0.2], ['scars', 0.5]] },
    'dark-int': { density: 1.0, clutter: [['Litter', 2], ['RubbleA', 1], ['Bottle', 1], ['CanLying', 1], ['CartonFlat', 1], ['Bucket', 0.6]], wallClutter: [['Conduit', 3], ['JunctionBox', 2], ['SignExit', 1], ['Vent', 1]],
      floor: [['water', 3], ['puddle', 2], ['grime', 3], ['crack', 2], ['crack2', 1], ['oil', 1], ['paper', 1], ['drain', 0.5]],
      base: [['grime2', 3], ['water2', 2], ['paper', 1]],
      wall: [['grimeBase', 4], ['leak', 3], ['rust', 1], ['poster', 0.6], ['poster3', 0.6], ['sootStreak', 1], ['crack3', 1]] },
    'civic-int': { density: 0.55, wallRate: 0.6, clutterRate: 0.4, clutter: [['Litter', 1], ['CartonFlat', 0.5], ['Bucket', 0.5]], wallClutter: [['Extinguisher', 2], ['SignExit', 1], ['Vent', 1]],
      floor: [['scuff', 3], ['water', 1], ['grime', 2], ['paper', 0.6]],
      base: [['grime2', 2], ['scuff', 1]],
      wall: [['grimeBase', 3], ['scars', 0.4], ['water2', 0.5]] },
    'giant-room': { density: 0.5, wallRate: 0.5, clutter: [], wallClutter: [],   // adult-scale clutter reads as crumbs in a giant room
      floor: [['scuff', 3], ['water', 1], ['grime', 1], ['paper', 0.8]],
      base: [['grime2', 1], ['scuff', 1]],
      wall: [['grimeBase', 3], ['scars', 0.3]] }
  };
  Object.keys(LOOKS.dress).forEach(function (f) { if (LOOKS.families[f]) LOOKS.families[f].dress = LOOKS.dress[f]; });

  // section 8: family and scene type of every theme; pilots carry rough tuning (final tuning is Stage 10)
  LOOKS.themes = {
    mountains: { family: 'wild-ext', type: 'ext-snow', albCeil: 0.80, sunI: 0.85, ambI: 0.38, fog: { length: 170 }, floor: { cls: 13, gloss: 0.25 },
      dress: { density: 0.35, floor: [['prints', 2], ['grime', 1]], base: [['grime2', 1]], wall: [['grimeBase', 2], ['crack3', 1]], clutter: [['StonesA', 1], ['StonesB', 1]] } },
    smallcity: { family: 'urban-ext', type: 'ext-day', sunI: 1.35, sunColor: '#FFDDB4', ambI: 0.38 },   // late afternoon: a warmer, lower-key sun
    classroom: { family: 'giant-room', type: 'int-lit' },
    office: { family: 'civic-int', type: 'int-lit' },
    bedroom: { family: 'giant-room', type: 'int-lit', floor: { cls: 4, gloss: 0.24 }, ambI: 0.66, indoorAmb: 0.72, albSat: 1.0, grade: { sat: 1.06, contrast: 0.14 } },
    coalmine: { family: 'dark-int', type: 'int-dark', indoorAmb: 0.55, ambI: 0.42, ambFloor: 0.05, grid: { intensity: 2.2 }, exposure: 1.15 },   // was 36-79% near black: lamps on rock need help to read
    castle: { family: 'urban-ext', type: 'ext-day', floor: { cls: 8, gloss: 0.08 }, sunI: 1.3, albCeil: 0.74 },   // pale sandstone: keep it off white
    city2: { family: 'urban-ext', type: 'ext-dusk', exposure: 0.9, bloom: { amount: 0.38 } },   // lit windows everywhere: keep them off white
    factory: { family: 'ind-int', type: 'int-ind' },
    livingroom: { family: 'giant-room', type: 'int-lit' },
    garden: { family: 'wild-ext', type: 'ext-day', floor: { cls: 7, gloss: 0.06 }, sunI: 1.25 },
    factory2: { family: 'ind-int', type: 'int-ind', indoorAmb: 0.42, grid: { intensity: 1.25 } },   // heavy plant at dusk: was murky (mean 0.21)
    island: { family: 'wild-ext', type: 'ext-day', floor: { cls: 6, gloss: 0.04 }, sunI: 1.15, albCeil: 0.70 },   // white sand: keep the beach off white
    mall: { family: 'civic-int', type: 'int-lit', floor: { cls: 10, gloss: 0.40 }, ambI: 0.42, indoorAmb: 0.45, grid: { intensity: 0.72 }, grade: { sat: 1.0, contrast: 0.22 } },
    police: { family: 'ind-int', type: 'int-ind', exposure: 0.86, albCeil: 0.72, indoorAmb: 0.24 },   // white tiled floor clipped
    grove: { family: 'wild-ext', type: 'ext-day', floor: { cls: 6, gloss: 0.04 } },
    spire: { family: 'civic-int', type: 'int-lit' },
    foundry: { family: 'ind-int', type: 'int-ind', indoorAmb: 0.48, grid: { intensity: 1.4 } },   // 30 m halls: lamps far from the floor
    parking: { family: 'ind-int', type: 'int-ind', wet: 0.5 },
    hotel: { family: 'civic-int', type: 'int-lit' },
    techhq: { family: 'civic-int', type: 'int-lit' },
    cargoship: { family: 'mil-ext', type: 'ext-day', floor: { cls: 3, gloss: 0.3 }, wet: 0.3, ambI: 0.50, indoorAmb: 0.35 },   // open sea: lots of sky fill between the containers
    datacenter: { family: 'ind-int', type: 'int-ind', floor: { cls: 10, gloss: 0.4 }, grid: { emit: {} } },
    downtown: { family: 'urban-ext', type: 'ext-day', floor: { cls: 12, gloss: 0.12 }, sunI: 1.35, ambI: 0.38 },
    highrise: { family: 'civic-int', type: 'int-lit' },
    gemmine: { family: 'dark-int', type: 'int-dark', indoorAmb: 0.42, ambI: 0.40, ambFloor: 0.04, grid: { intensity: 1.5 }, exposure: 1.08 },
    megastore: { family: 'ind-int', type: 'int-lit', ambI: 0.50, indoorAmb: 0.60, grid: { intensity: 1.2 } },
    townhomes: { family: 'urban-ext', type: 'ext-day' },
    arctic: { family: 'dark-int', type: 'int-dark', floor: { cls: 13, gloss: 0.3 } },
    resort: { family: 'wild-ext', type: 'ext-day' },
    scrapyard: { family: 'mil-ext', type: 'ext-night', sky: { sunDisc: false }, sunI: 0.6, ambI: 0.25, wet: 0.5 },
    seabase: { family: 'dark-int', type: 'int-dark', wet: 0.4 },
    stronghold: { family: 'mil-ext', type: 'ext-dusk', sky: { sunDisc: false }, sunI: 1.5, ambI: 0.38, ambSky: [0.62, 0.60, 0.72], ambGround: [0.52, 0.40, 0.30], sunColor: '#FFD6AE', indoorAmb: 0.8, grid: { intensity: 2.0 }, floor: { cls: 1, gloss: 0.12 }, albSat: 1.0, fog: { length: 260, sunGlow: [1.0, 0.72, 0.48] } },
    airport: { family: 'civic-int', type: 'int-lit' },
    frontier: { family: 'wild-ext', type: 'ext-day' },
    academy: { family: 'civic-int', type: 'int-lit' },
    mossgarden: { family: 'wild-ext', type: 'ext-day', sunI: 1.2, exposure: 0.92, albCeil: 0.74 },   // pale glasshouse and stream: keep under white
    pelagic: { family: 'mil-ext', type: 'ext-day', floor: { cls: 3, gloss: 0.3 } },
    icecream: { family: 'civic-int', type: 'int-lit', ambI: 0.70, indoorAmb: 0.70 },
    venetian: { family: 'urban-ext', type: 'ext-day', sunI: 1.3, sunColor: '#FFE2BE', albCeil: 0.76 },   // late afternoon on pale paving
    metro: { family: 'dark-int', type: 'int-dark', wet: 0.2, ambI: 0.24, indoorAmb: 0.16, grid: { intensity: 0.36 }, floor: { cls: 10, gloss: 0.35 } },
    toyfactory: { family: 'ind-int', type: 'int-lit', ambI: 0.55, indoorAmb: 0.55 },
    airfield7: { family: 'mil-ext', type: 'ext-day', floor: { cls: 12, gloss: 0.12 }, sunI: 1.4, exposure: 0.95 },   // hazy steppe: pale apron, keep it under white
    riviera: { family: 'civic-int', type: 'int-lit' },
    observatory: { family: 'mil-ext', type: 'ext-dusk', sky: { sunDisc: false } },
    toytown: { family: 'urban-ext', type: 'ext-day' }
  };

  // section 6: what each tier draws. Tiers change quality, never the lighting design (hard rule 5).
  LOOKS.tiers = {
    high:   { shadow: 4096, shadowType: 'pcfsoft', shadowSpan: 70, detail: 2, normalDetail: true, flashes: 4, post: true, msaa: 4, bloom: 5, vignette: true, dust: 1, density: 1 },
    medium: { shadow: 2048, shadowType: 'pcf', shadowSpan: 70, detail: 1, normalDetail: true, flashes: 4, post: true, msaa: 2, bloom: 3, vignette: true, dust: 1, density: 0.75 },
    low:    { shadow: 1024, shadowType: 'basic', shadowSpan: 45, detail: 0, normalDetail: false, flashes: 2, post: false, msaa: 0, bloom: 0, vignette: false, dust: 0.4, density: 0.5 },
    potato: { shadow: 0, shadowType: 'none', shadowSpan: 0, detail: -1, normalDetail: false, flashes: 1, post: false, msaa: 0, bloom: 0, vignette: false, dust: 0, density: 0.25 }
  };

  function isObj(v) { return v && typeof v === 'object' && !Array.isArray(v); }
  function merge(dst, src) {
    if (!src) return dst;
    for (var k in src) {
      if (isObj(src[k])) dst[k] = merge(isObj(dst[k]) ? dst[k] : {}, src[k]);
      else if (Array.isArray(src[k])) dst[k] = src[k].slice();
      else if (src[k] !== undefined) dst[k] = src[k];
    }
    return dst;
  }
  function lum(hex) {
    var h = String(hex || '#888888').replace('#', ''), n = parseInt(h.length === 3 ? h.replace(/./g, '$&$&') : h, 16);
    return (0.2126 * ((n >> 16) & 255) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255;
  }

  // a theme with no entry (a future map): family and scene type from its env
  LOOKS.guess = function (env) {
    env = env || {};
    var fog = env.fog || {};
    if (!env.sky) {
      var l = lum(fog.color || env.clear);
      if (l < 0.28) return { family: 'dark-int', type: 'int-dark' };
      if (l < 0.55) return { family: 'ind-int', type: 'int-ind' };
      return { family: 'civic-int', type: 'int-lit' };
    }
    var s = env.sun || [0.42, 0.82, 0.38], L = Math.sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2]) || 1;
    var up = s[1] / L;
    if (lum(env.sky[0]) < 0.2) return { family: 'mil-ext', type: 'ext-night' };
    return { family: 'urban-ext', type: up < 0.5 ? 'ext-dusk' : 'ext-day' };
  };

  // defaults <- family <- theme (deep merge); env is the theme's env (used when the theme has no entry)
  LOOKS.resolve = function (themeId, env) {
    var t = LOOKS.themes[themeId] || LOOKS.guess(env);
    var fam = t.family || LOOKS.defaults.family;
    var out = merge(merge(merge({}, LOOKS.defaults), LOOKS.families[fam] || {}), t);
    out.family = fam; out.themeId = themeId; out.guessed = !LOOKS.themes[themeId];
    return out;
  };
  LOOKS.tier = function (name) { return LOOKS.tiers[name] || LOOKS.tiers.high; };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
