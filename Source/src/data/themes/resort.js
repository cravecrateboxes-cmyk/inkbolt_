/* Theme: Palmyra Cove Resort (kit-resort) -- a luxury tropical resort (made-up Palmyra Cove brand) on the west shore
   of an island, bright tropical daylight, open ocean all round. Two zones:
   1 The resort grounds (72 x 64): the open-air lobby pavilion under a two-tier thatched roof (reception, woven screen
     with the resort's name), the lagoon pool with its thatched swim-up bar, loungers, umbrellas and cabanas round the
     paved pool deck, tiki torches, the beach with lounger pairs, kayak racks and the towel hut, a boardwalk over the
     sand, a garden lounge, the service yard, and the first treehouse villa on a platform in two giant palms.
   2 The canopy (76 x 68): four long, wide tree platforms 7.5 m up in eight enormous palms (the landmark: the CANOPY
     SUITE on the centre platform), rope bridges between them, five broken limbs and fallen fronds leaning against
     them as ramps (walkable by the player and the robots), and ground cover below: fallen trunks, snapped stumps,
     coconut piles, crates, a broken-down golf cart. A fall from the canopy just drops you to the ground.
   Built by blender/fam_kit_resort.py (rs_*.py); zone layers by tools/resort_zones.py (src/data/zones/resort_*.txt).

   A zone file has the floor plan and five layers: "@layer 0.2" boardwalk slabs, "@layer 0.2" their plank decals,
   "@layer 7.5" platform slabs and rope bridges, "@layer 7.5" the platforms' plank / joist decals, "@layer 7.5" what
   stands on the platforms. The ground is flat sand; theme.terrain paints lawn, paths and wet sand from the plan
   (and a shade under each platform).
   Floor plan (1 cell = 1 m; prefab sizes [x, z]):
     #  hedge walls on a coral-stone kerb (2 m modules; some with a palm behind), round corner clumps
     {  shore rocks and a rope fence on the west edge (the beach and the sea lie behind)
     , lawn   ; paved path / pool deck   ~ wet sand   . sand   (ground paint only)
     L lobby pavilion [14,10]   Q lagoon pool with the swim-up bar [20,12]   C K N cabana [4,4] open south / west / east
     l sun lounger [1,2] (head north)   j sun lounger [2,1] (head east, facing the sea)   u thatched umbrella + table
     t tiki torch   o rattan lounge set [3,2]   q stone planter   p palm   Y tall palm [2,2]   f hibiscus bush
     g dune grass   k coconut pile   c supply crates   y kayak rack [3,1]   T towel hut [3,2]   n signpost
     X broken-down golf cart [2,3]   F fallen palm trunk [6,2]   U snapped stump [2,2]   e fallen frond [2,4]
     Z giant treehouse palm [4,4] (its collar and knee braces carry the platform above)   I deck post
     ^ v > <  broken limb / fallen frond ramp [2,13] rising north / south / east / west (its top end against a
              platform edge; 52 walkable steps of 0.144 m)
   Layer 0.2: w boardwalk slab   d b plank decal [4,2] (two symbols for neighbouring strips)
   Layer 7.5: D platform slab   = rope bridge [3,2]   J plank + joist decal [4,2]
              r rail (runs)   V W [ ] villa [6,5] open south / north / east / west   M CANOPY SUITE [8,6] open south
              H hammock [3,1]   (o t c k q as on the ground) */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var SOLID = '#GE{';
  function solid(g, c, r) { return SOLID.indexOf(g.at(c, r)) >= 0; }
  function faceOf(g, c, r) {
    var oS = !solid(g, c, r + 1), oN = !solid(g, c, r - 1), oE = !solid(g, c + 1, r), oW = !solid(g, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function inRun(g, c, r, F) { return g.at(c, r) === '#' && faceOf(g, c, r) === F && gateDist(g, c, r) > 2.6; }
  function chooseWall(c, r, horiz, corner, hash, g) {
    var F = faceOf(g, c, r);
    if (F === 'none' || F === 'corner') return hash(c * 3 + 1, r * 7 + 2) < 0.5 ? 'Corner_A' : 'Corner_B';
    if (gateDist(g, c, r) < 2.6) return null;          // the gate frame's posts and hedge clumps fill the cells beside a gate
    var along = F === 'S' || F === 'N', u = along ? c : r;
    var pc = along ? faceOf(g, c - 1, r) : faceOf(g, c, r - 1), nc = along ? faceOf(g, c + 1, r) : faceOf(g, c, r + 1);
    if (u % 2 === 0) {
      // a module poking half a cell into a corner: A on north / south runs, B on east / west runs (kerb tops never coplanar)
      if (pc === 'corner' || pc === 'none' || nc === 'corner' || nc === 'none') return along ? 'Hedge_A' : 'Hedge_B';
      var h = hash(c * 5 + 1, r * 3 + 7); return h < 0.16 ? 'Hedge_C' : h < 0.55 ? 'Hedge_B' : 'Hedge_A';
    }
    var prev = along ? inRun(g, c - 1, r, F) : inRun(g, c, r - 1, F), next = along ? inRun(g, c + 1, r, F) : inRun(g, c, r + 1, F);
    if ((!prev && (pc === 'corner' || pc === 'none')) || (!next && (nc === 'corner' || nc === 'none'))) return null;   // the corner clump covers it
    return (!prev || !next) ? 'Hedge_1' : null;        // odd cells are covered by their neighbours' 2 m modules
  }

  // ---------------------------------------------------------------- ground paint (flat sand + lawn / paths / wet sand)
  var PAINT = { ',': 'lawn', ';': 'path', '~': 'wet', '.': 'sand' };
  function deckOver(g, c, r) {
    var L = g.layers || [];
    for (var i = 0; i < L.length; i++) if (L[i].y > 5 && L[i].at(c, r) === 'D') return true;
    return false;
  }
  function paint(c, r, zi, g) {
    var n = { lawn: 0, path: 0, wet: 0, sand: 0 }, tot = 0, shade = 0, dc, dr, k;
    for (var rad = 1; rad <= 3 && !tot; rad++) {
      for (dr = -rad; dr < rad; dr++) for (dc = -rad; dc < rad; dc++) {
        k = PAINT[g.at(c + dc, r + dr)];
        if (k) { n[k]++; tot++; }
      }
    }
    for (dr = -1; dr <= 0; dr++) for (dc = -1; dc <= 0; dc++) if (deckOver(g, c + dc, r + dr)) shade++;
    if (!tot) return null;
    var best = 'sand';
    ['lawn', 'path', 'wet'].forEach(function (q) { if (n[q] > n[best]) best = q; });
    var a = n[best] / tot;
    if (shade >= 2) return best === 'lawn' ? ['#5C9C47', 0.95] : ['#CBAE78', 0.85];
    if (best === 'lawn') return [Math.floor(c / 3) % 2 ? '#7DC65A' : '#88CD63', 0.35 + 0.65 * a];
    if (best === 'path') return ['#EFE5CF', 0.3 + 0.7 * a];
    if (best === 'wet') return ['#D7BB86', 0.3 + 0.6 * a];
    return null;
  }

  // ---------------------------------------------------------------- the island round the level and the sea (backdrop.build)
  function superellipse(cx, cz, hx, hz, n, N) {
    var out = [];
    for (var i = 0; i < N; i++) {
      var a = i / N * Math.PI * 2, c = Math.cos(a), s = Math.sin(a);
      out.push([cx + hx * (c < 0 ? -1 : 1) * Math.pow(Math.abs(c), 2 / n), cz + hz * (s < 0 ? -1 : 1) * Math.pow(Math.abs(s), 2 / n)]);
    }
    return out;
  }
  function buildIsland(level, api) {
    var THREE = (typeof window !== 'undefined' && window.THREE) || globalThis.THREE;
    var zones = level.zones, hash = api.hash;
    var x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    zones.forEach(function (z) { x0 = Math.min(x0, z.ox); x1 = Math.max(x1, z.ox + z.w); z0 = Math.min(z0, z.oz); z1 = Math.max(z1, z.oz + z.h); });
    if (level.hatch) z0 = Math.min(z0, level.hatch.z - 12);
    // bands from the beach out: [west offset, other sides offset, y, colour]; the west wall is the shore line
    var BANDS = [[30, 58, -0.36, '#2DB9D7'], [12.5, 40, -0.3, '#52D8E2'], [9.2, 36.6, -0.24, '#F2FFFF'], [8.6, 36, -0.18, '#D7BB86'],
      [6.5, 34, -0.12, '#F1DCA4'], [0, 27, -0.06, '#7DBF58']];
    api.geo.flat([[x0 - 700, z0 - 700], [x1 + 700, z0 - 700], [x1 + 700, z1 + 700], [x0 - 700, z1 + 700]], -0.42, new THREE.Color('#1F90C5'));
    BANDS.forEach(function (B) {
      var a = x0 - B[0], b = x1 + B[1], c = z0 - B[1], d = z1 + B[1];
      api.geo.flat(superellipse((a + b) / 2, (c + d) / 2, (b - a) / 2, (d - c) / 2, 9, 72), B[2], new THREE.Color(B[3]));
    });
    // keep-outs: the zones and their walls, the trails, the hatch room
    var keep = [];
    zones.forEach(function (z) { keep.push([z.ox - 1.5, z.oz - 1.5, z.ox + z.w + 1.5, z.oz + z.h + 1.5]); });
    level.trails.forEach(function (t) { keep.push([t.x - 4.5, Math.min(t.z0, t.z1) - 1, t.x + 4.5, Math.max(t.z0, t.z1) + 1]); });
    if (level.hatch) keep.push([level.hatch.x - 7, level.hatch.z - 7, level.hatch.x + 7, (level.hatch.z0 || level.hatch.z) + 1]);
    function clear(x, z, r) {
      for (var i = 0; i < keep.length; i++) { var k = keep[i]; if (x > k[0] - r && x < k[2] + r && z > k[1] - r && z < k[3] + r) return false; }
      return true;
    }
    var n = 0;
    // palms and jungle on the land (north, east, south of the zones), palms leaning out over the beach (west)
    for (var gx = x0 - 4; gx <= x1 + 26; gx += 8) for (var gz = z0 - 26; gz <= z1 + 26; gz += 8) {
      n++;
      var x = gx + (hash(n, 3) - 0.5) * 6, z = gz + (hash(n, 5) - 0.5) * 6;
      if (x < x0 - 1) { if (x > x0 - 5 && hash(n, 7) < 0.55 && clear(x, z, 2)) api.add(hash(n, 9) < 0.5 ? 'Backdrop_Palm_A' : 'Backdrop_Palm_B', x, -0.1, z, -R90 + (hash(n, 11) - 0.5) * 1.2, 0.9 + hash(n, 13) * 0.3); continue; }
      var out = Math.max(x0 - x, x - x1, z0 - z, z - z1, 0);
      if (out > 22 || !clear(x, z, 2.5) || hash(n, 17) < 0.25) continue;
      if (out < 8 || hash(n, 15) < 0.35) api.add(hash(n, 9) < 0.5 ? 'Backdrop_Palm_A' : 'Backdrop_Palm_B', x, -0.06, z, hash(n, 11) * 6.28, 0.85 + hash(n, 13) * 0.4);
      else api.add(hash(n, 9) < 0.5 ? 'Backdrop_Jungle_A' : 'Backdrop_Jungle_B', x, -0.04 - hash(n, 19) * 0.3, z, hash(n, 11) * 6.28, 0.9 + hash(n, 13) * 0.5);
    }
    // overwater bungalows on jetties off the beach, islets far out
    zones.forEach(function (Z, zi) {
      var zc = Z.oz + Z.h * (zi ? 0.35 : 0.6);
      api.add('Backdrop_Jetty', x0 - 13, -0.36, zc, R90, 1);
      api.add('Backdrop_Jetty', x0 - 25, -0.36, zc, R90, 1);
      api.add('Backdrop_Bungalow', x0 - 34, -0.36, zc - 4, -R90, 1);
      api.add('Backdrop_Bungalow', x0 - 34, -0.36, zc + 5, -R90 + 0.1, 1);
      api.add('Backdrop_Bungalow', x0 - 26, -0.36, zc - 9, Math.PI, 1);
    });
    [[x0 - 150, z0 + 40, 2.2], [x0 - 230, z1 - 30, 3.0], [(x0 + x1) / 2 - 40, z0 - 200, 2.6], [x1 + 170, z1 + 60, 2.4], [x0 - 120, z1 + 150, 1.8]].forEach(function (I, i) {
      api.add('Backdrop_Islet', I[0], -0.45, I[1], i * 1.7, I[2]);
    });
  }

  var LIMB = ['Ramp_Limb', 'Ramp_LimbB', 'Ramp_Frond'];
  var SYMBOLS = {
    '{': { pieces: ['Shore_A', 'Shore_B', 'Shore_A', 'Shore_C', 'Shore_B', 'Shore_A', 'Shore_C'], rotate: R90, kind: 'wall' },
    'L': { size: [14, 10], pieces: ['Landmark_Lobby'], face: 0, kind: 'cover' },
    'Q': { size: [20, 12], pieces: ['Landmark_Pool'], face: 0, kind: 'cover' },
    'C': { size: [4, 4], pieces: ['Cabana'], face: 0, kind: 'cover' },
    'K': { size: [4, 4], pieces: ['Cabana'], face: -R90, kind: 'cover' },
    'N': { size: [4, 4], pieces: ['Cabana'], face: R90, kind: 'cover' },
    'l': { size: [1, 2], pieces: ['Lounger_A', 'Lounger_B'], face: 0, kind: 'cover' },
    'j': { size: [1, 2], pieces: ['Lounger_A', 'Lounger_B'], face: -R90, kind: 'cover' },
    'u': { pieces: ['Umbrella'], rotate: 'random90', kind: 'cover' },
    't': { pieces: ['Torch'], rotate: 'random90', kind: 'cover' },
    'o': { size: [3, 2], pieces: ['LoungeSet'], flip: true, kind: 'cover' },
    'q': { pieces: ['Planter'], rotate: 'random90', kind: 'cover' },
    'p': { pieces: ['Palm_A', 'Palm_B', 'Palm_C'], rotate: 'random90', kind: 'cover' },
    'Y': { size: [2, 2], pieces: ['TallPalm_A', 'TallPalm_B'], flip: true, kind: 'cover' },
    'f': { pieces: ['Bush_A', 'Bush_B'], rotate: 'random90', kind: 'cover' },
    'g': { pieces: ['DuneGrass'], rotate: 'random90', collide: false },
    'k': { pieces: ['CoconutPile'], rotate: 'random90', kind: 'cover' },
    'c': { pieces: ['Crate_A', 'Crate_B', 'Crate_A'], rotate: 'random90', kind: 'cover' },
    'y': { size: [3, 1], pieces: ['Kayaks'], flip: true, kind: 'cover' },
    'T': { size: [3, 2], pieces: ['TowelHut'], face: 0, kind: 'cover' },
    'n': { pieces: ['Signpost'], rotate: 'edge', edge: ',', kind: 'cover' },
    'X': { size: [2, 3], pieces: ['GolfCart'], flip: true, kind: 'cover' },
    'F': { size: [6, 2], pieces: ['FallenTrunk'], flip: true, kind: 'cover' },
    'U': { size: [2, 2], pieces: ['Stump'], flip: true, kind: 'cover' },
    'e': { size: [2, 4], pieces: ['FallenFrond'], flip: true, collide: false },
    'Z': { size: [4, 4], pieces: ['Landmark_GiantPalm_A', 'Landmark_GiantPalm_B'], face: 0, kind: 'cover' },
    'I': { pieces: ['DeckPost'], kind: 'cover' },
    '^': { size: [2, 13], pieces: LIMB, face: 0, kind: 'cover' },
    'v': { size: [2, 13], pieces: LIMB, face: Math.PI, kind: 'cover' },
    '>': { size: [2, 13], pieces: LIMB, face: -R90, kind: 'cover' },
    '<': { size: [2, 13], pieces: LIMB, face: R90, kind: 'cover' },
    // boardwalks (layer 0.2)
    'w': { deck: { thick: 0.2, color: '#D9A56E', edge: '#9A6238', under: '#6A4428' } },
    'd': { size: [4, 2], pieces: ['Planks'], collide: false },
    'b': { size: [4, 2], pieces: ['Planks'], collide: false },
    // tree platforms (layer 7.5)
    'D': { deck: { thick: 0.35, color: '#D29A62', edge: '#8E5832', under: '#6E4426' } },
    'J': { size: [4, 2], pieces: ['PlanksJ'], collide: false },
    '=': { size: [3, 2], pieces: ['Bridge'], kind: 'cover' },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' },
    'V': { size: [6, 5], pieces: ['Villa'], face: 0, kind: 'cover' },
    'W': { size: [6, 5], pieces: ['Villa'], face: Math.PI, kind: 'cover' },
    '[': { size: [6, 5], pieces: ['Villa'], face: R90, kind: 'cover' },
    ']': { size: [6, 5], pieces: ['Villa'], face: -R90, kind: 'cover' },
    'M': { size: [8, 6], pieces: ['Landmark_Villa'], face: 0, kind: 'cover' },
    'H': { size: [3, 1], pieces: ['Hammock'], flip: true, kind: 'cover' }
  };
  var GLOW = { Torch: { piece: 'Torch_Flame' } };

  var PIECES = ['Hedge_A', 'Hedge_B', 'Hedge_C', 'Hedge_1', 'Corner_A', 'Corner_B', 'GateFrame', 'GateShutter', 'TrailWall',
    'TrailWall_B', 'TrailWall_C', 'Hatch', 'Torch_Flame', 'Backdrop_Palm_A', 'Backdrop_Palm_B', 'Backdrop_Jungle_A', 'Backdrop_Jungle_B',
    'Backdrop_Islet', 'Backdrop_Bungalow', 'Backdrop_Jetty'];
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'resort', name: 'Palmyra Cove Resort', family: 'kit-resort', prefix: 'KIT_RESORT_',
    palette: ['#3FAE58', '#52D8E2', '#F07A52', '#F3DFA8'],
    env: { sky: ['#2F9BEA', '#D2F0FF'], fog: { color: '#D2F0FF', near: 50, far: 190, tierScale: true }, sun: [0.45, 0.85, 0.3], clouds: true, ceiling: null },
    floor: { color: '#F1DCA4', trail: '#EFE5CF', outside: '#7DBF58' },
    terrain: { height: function () { return 0; }, paint: paint, flat: '', ramp: [1, 2], low: '#F1DCA4', high: '#F1DCA4', patch: '#EAD196', top: 3 },
    wall: { height: 3.6, roof: '#3E9A50', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.4, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall'], height: 2.6 },
    hatch: 'Hatch', stand: 'Crate_A',
    backdrop: { build: buildIsland },
    budget: { prop: 1600, landmark: 3500, total: 45000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      resort: {
        name: 'Palmyra Cove Resort',
        intro: 'Robots have taken over Palmyra Cove. Clear the resort grounds, then climb the broken limbs into the canopy villas. A fall only drops you to the sand.',
        zones: [
          // the resort grounds: lobby, lagoon pool, beach, the first treehouse
          { map: 'resort_1', waves: [
            [['crawler', 20], ['gunner', 10], ['drone', 4]],
            [['crawler', 16], ['gunner', 7], ['bomber', 2], ['soldier', 5], ['blader', 3]],
            [['crawler', 12], ['drone', 7], ['gunner', 7], ['soldier', 6], ['blader', 3]],
            [['crawler', 14], ['gunner', 8], ['bomber', 2], ['soldier', 6], ['blader', 3]],
            [['crawler', 14], ['gunner', 6], ['drone', 3], ['soldier', 5], ['blader', 3]]] },
          // the canopy: platforms, bridges, broken-limb ramps, cover below
          { map: 'resort_2', waves: [
            [['crawler', 16], ['gunner', 9], ['drone', 4], ['soldier', 5]],
            [['crawler', 14], ['drone', 6], ['gunner', 7], ['blader', 3]],
            [['crawler', 15], ['gunner', 8], ['bomber', 2], ['soldier', 6], ['blader', 3]],
            [['crawler', 14], ['drone', 6], ['gunner', 8], ['soldier', 6], ['blader', 3]],
            [['crawler', 15], ['gunner', 7], ['bomber', 2], ['soldier', 4], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
