/* Theme: Pelagic Airbase (kit-pelagic) -- a made-up offshore military air platform far out at sea, open ocean to
   the horizon all round and no land in sight; escort warships keep station a few hundred metres off. The platform
   stands 26 m above the water on great columns; its extra-long runway runs the whole length of the deck on the east
   side (past both zones and on north to the far end). Clear midday. Two zones; player travel is north.
   1 The flight deck (78 x 76): the runway (cols 52-75: edge lines, centreline, the threshold, the 36, arresting
     wires across the landing area), the deck edges over the sea with railings and outboard safety nets, the
     flight-operations block along the south (the entry gate is its door), the blast fence (north, with the exit
     gate) and the emergency barricade net across the runway. The player starts beside the light aircraft with its
     canopy swung open and the boarding stair against it. The island control tower (landmark: gallery at 3.6 m up a
     stair, offices, the flight-control cab, the mast with radars) between the apron and the runway; the helicopter
     dock on the north-west deck edge (a 2.4 m deck on posts, two stairs, the helicopter on its pad, stores under
     it); the flight line (two fighters, wings folded), an engine run-up spot and a fighter lined up on the runway,
     each with its raised jet blast deflector; ordnance staging (bomb and missile carts), deck tractors, the crash
     tender, ground power units, fire stations, floodlight masts.
   2 The hangar deck (64 x 76): the inner platform module, 12 m wider to the west. HANGAR 1 and HANGAR 2 (24 x 20,
     doors open south, a 9.6 m roof on trusses) each with a fighter under maintenance (canopy raised, panels open,
     boarding ladder), its engine on a stand, a hoist, work stands, tool chests and a mezzanine at 3.0 m along the
     back wall (stair, rails, bench and shelving under it); the approach-control tower (landmark: balcony at 3.6 m)
     by the runway fence; two cargo lifts with cargo on them, the fuel farm (three tanks in a bund), the fuel line
     to the fuel points between the hangars, the container yard (one container stacked), a fighter towed out of
     hangar 2, ordnance carts, the hangar deck's crash tender.
   Built by blender/fam_kit_pelagic.py (pel_*.py); zone layouts by tools/pelagic_zones.py (src/data/zones/pelagic_*.txt).

   Floor plan symbols (1 cell = 1 m; prefab sizes [x, z] as modelled; R90 = turned a quarter, noses point south at 0):
     # wall: the deck-edge railing with its safety net (west / east edges, 1.2 m), the blast fence (3.6 m; zone 1
       north and runway south, zone 2 north / south / east), the runway barricade net (zone 1 north over the runway),
       the flight-operations block front (zone 1 south: windows, doors, the PELAGIC AIRBASE - FLIGHT OPERATIONS band)
     I island control tower [10, 20] (landmark)   W approach-control tower [8, 12] (landmark)
     A B hangar 1 / 2 [24, 20] (doors south)   L light aircraft [10, 10] (nose north)
     J j fighter, wings spread [12, 16] nose south / north   K k fighter, wings folded [8, 16] nose south / north
     M fighter under maintenance [12, 16] (layer 0 inside a hangar)   D jet blast deflector [8, 2] (raised, facing
     north)   T tractor [2, 4]   3 tractor, tow bar north   O bomb cart [2, 3]   Z missile cart [2, 3]
     F crash tender [3, 7]   q ground power unit [2, 2]   u U stair to the 2.4 m dock rising north / west [2, 6]
     i stair to the 3.0 m mezzanine rising north [2, 8]   p dock post   ! mezzanine post
     w arresting wire (runs along X)   x wire sheave   c chocks   b tool chest   e fire extinguisher
     f fire station   g gas bottles   n ammo crates   d drums   o cargo pallet   l floodlight mast
     C cargo lift [7, 7]   X container [3, 6] (repainted per copy)   V fuel tank [3, 8]   y fuel point [2, 2]
     - bund kerb (links)   ~ fuel line (links)   N engine stand [2, 5]   s work stand [2, 3]   H hoist [3, 2]
     z workbench [2, 1]   Q parts shelving [3, 1]
   Layer symbols: = dock deck (2.4)   m mezzanine deck (3.0)   r rail (links)   @ helipad markings [16, 16]
     Y helicopter [8, 14]   (and X on the 2.59 layer: a stacked container; o n on the 0.012 layer: cargo on a lift)
   Backdrop (backdrop.build, level-wide, so nothing switches between the zones): the ocean 26 m down to the horizon
   with swell bands and whitecaps, the platform deck round the zones (the runway and its markings run on to the far
   north end), the deck-edge fascias and railings, the flight-operations block behind zone 1, the box girder under
   the deck, the columns and their braces down to the sea with foam round them, cranes, a radome and masts at the
   far end, three escort warships (two classes) with their wakes. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, SEA = -26;
  var RWY = [52, 76];   // zone 1 runway columns

  // ---------------------------------------------------------------- walls
  function kindOf(g) {   // zone 1 (the flight deck) holds the island; zone 2 the hangars
    if (g._pK === undefined) { g._pK = 'deck2'; for (var r = 0; r < g.h; r++) if (g.rows[r].indexOf('I') >= 0) { g._pK = 'deck1'; break; } }
    return g._pK;
  }
  function gateDist(g, c, r) {   // cells from a north / south edge wall cell to the centre of that edge's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  function edge(c, r, h) {   // deck-edge railing modules: a stanchion every 2 m, a lifebuoy, a hose box, a light
    var k = (r + c) % 24;
    if (k === 7) return 'Edge_Ring';
    if (k === 15) return 'Edge_Hose';
    if (k === 19) return 'Edge_Light';
    return r % 2 ? 'Edge_B' : 'Edge_A';
  }
  function fence(i, h) {
    if (i % 9 === 4) return 'Fence_Light';
    if (i % 17 === 11) return 'Fence_Sign';
    return i % 2 ? 'Fence_B' : 'Fence_A';
  }
  var OPS_SIGN = [30, 43];   // zone 1 south wall: the lettering band over these columns (module k = 43 - c)
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    var K = kindOf(g), W = g.w - 1, H = g.h - 1;
    if (gateDist(g, c, r) < 2.6) return null;   // the gate frame's pylons fill the cells beside a gate
    if (K === 'deck1') {
      if (r === 0 && c === 0) return 'Corner_NW_W';
      if (r === 0 && c === W) return 'Corner_NE_E';
      if (r === H && c === 0) return 'Ops_Corner';
      if (r === H && c === W) return 'Corner_SE_E';
      if (c === 0 || c === W) return edge(c, r, hash);
      if (r === 0) {
        if (c >= RWY[0]) return (c - RWY[0]) % 4 === 0 ? 'Barricade_Post' : 'Barricade_Net';
        if (c >= 18 && c <= 20) return 'Fence_DeckB_' + (c - 18);
        return fence(c, hash);
      }
      // the south wall: the flight-operations block west of the runway, the blast fence behind the threshold
      if (c >= RWY[0]) return fence(c + 3, hash);
      if (c === RWY[0] - 1) return 'Ops_End';
      if (c >= OPS_SIGN[0] && c <= OPS_SIGN[1]) return 'Ops_Sign_' + (OPS_SIGN[1] - c);
      if (c % 12 === 6) return 'Ops_Door';
      if (c % 12 === 3 || c === 48) return 'Ops_Vent';
      return c % 3 === 1 ? 'Ops_Plain' : 'Ops_Win';
    }
    if (r === 0 && c === 0) return 'Corner_NW_W';
    if (r === H && c === 0) return 'Corner_SW_W';
    if (r === 0 && c === W) return 'Corner_NE';
    if (r === H && c === W) return 'Corner_SE';
    if (c === 0) return edge(c, r, hash);
    if (c === W) return (r >= 44 && r <= 46) ? 'Fence_DeckB_' + (r - 44) : fence(r, hash);
    return fence(c, hash);
  }

  // ---------------------------------------------------------------- symbols
  function pf(size, pieces, face, extra) { var d = { size: size, pieces: pieces, kind: 'cover' }; if (face !== undefined) d.face = face; return Object.assign(d, extra || {}); }
  function one(pieces, rot, extra) { return Object.assign({ pieces: pieces, kind: 'cover', rotate: rot || 'random90' }, extra || {}); }
  // container paint: palette cells (blender/pel_base.py) cont1 46, cont2 47, cont3 48, cont4 49, blue 27, orange 24
  var CONT_PAINT = { from: [46], to: [[46], [47], [48], [49], [27], [24], [47], [48]] };
  var JET = function (wings, canopy, face) { return pf([wings === 'Jet_WingsFold' ? 8 : 12, 16], ['Jet_Body'], face, { with: { Jet_Body: [wings, canopy] } }); };
  var SYMBOLS = {
    'I': pf([10, 20], ['Landmark_Island'], 0, { with: { Landmark_Island: ['Landmark_IslandTop'] } }),
    'W': pf([8, 12], ['Landmark_Tower2'], 0),
    'A': pf([24, 20], ['Landmark_Hangar1'], 0, { with: { Landmark_Hangar1: ['Landmark_HangarRoof'] } }),
    'B': pf([24, 20], ['Landmark_Hangar2'], 0, { with: { Landmark_Hangar2: ['Landmark_HangarRoof'] } }),
    'L': pf([10, 10], ['Plane'], Math.PI),
    'J': JET('Jet_Wings', 'Jet_Canopy', 0),
    'j': JET('Jet_Wings', 'Jet_Canopy', Math.PI),
    'K': JET('Jet_WingsFold', 'Jet_Canopy', 0),
    'k': JET('Jet_WingsFold', 'Jet_Canopy', Math.PI),
    'M': JET('Jet_Wings', 'Jet_Open', 0),
    'D': pf([8, 2], ['JBD'], 0),
    'T': pf([2, 4], ['Tractor'], undefined, { flip: true }),
    '3': pf([2, 4], ['Tractor'], Math.PI),
    'O': pf([2, 3], ['BombCart'], undefined, { flip: true }),
    'Z': pf([2, 3], ['MissileCart'], undefined, { flip: true }),
    'F': pf([3, 7], ['Tender'], undefined, { flip: true }),
    'q': pf([2, 2], ['GPU'], undefined, { flip: true }),
    'u': pf([2, 6], ['Stair24'], 0),
    'U': pf([2, 6], ['Stair24'], R90),
    'i': pf([2, 8], ['Stair30'], 0),
    'p': one(['DeckPost'], 0),
    '!': one(['DeckPost3'], 0),
    'w': { pieces: ['Wire_A', 'Wire_B'], rotate: 'run', collide: false, alternate: true },
    'x': { pieces: ['WireEnd'], rotate: 0, collide: false },
    'c': one(['Chocks']),
    'b': one(['ToolChest']),
    'e': one(['Extinguisher']),
    'f': one(['FireStation'], 'edge'),
    'g': one(['Gas']),
    'n': one(['Crates']),
    'd': one(['Drums']),
    'o': one(['Pallet']),
    'l': one(['Floodlight'], 0),
    'C': pf([7, 7], ['CargoLift'], 0),
    'X': pf([3, 6], ['Container'], undefined, { flip: true, paint: CONT_PAINT }),
    'V': pf([3, 8], ['FuelTank'], undefined, { flip: true }),
    'y': pf([2, 2], ['FuelPoint'], undefined, { flip: true }),
    '-': { pieces: ['BundHalf'], full: 'BundFull', links: '-', post: 'BundPost', kind: 'cover' },
    '~': { pieces: ['PipeHalf'], full: 'PipeFull', links: '~', post: 'PipePost', kind: 'cover' },
    'N': pf([2, 5], ['EngineStand'], undefined, { flip: true }),
    's': pf([2, 3], ['WorkStand'], undefined, { flip: true }),
    'H': pf([3, 2], ['Hoist'], undefined, { flip: true }),
    'z': pf([2, 1], ['Bench'], 0),
    'Q': pf([3, 1], ['Shelf'], 0),
    // layers
    '=': { deck: { thick: 0.3, color: '#5E646B', edge: '#4A5058', under: '#40454C' } },
    'm': { deck: { thick: 0.3, color: '#8E969C', edge: '#5B636C', under: '#6B737A' } },
    'r': { pieces: ['RailHalf'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'cover' },
    '@': pf([16, 16], ['Helipad'], 0, { collide: false }),
    'Y': pf([8, 14], ['Helicopter'], 0)
  };

  // ---------------------------------------------------------------- the sea and the platform (backdrop.build)
  /* Level-wide: built once in level.root, so nothing here switches or pops as the player crosses between the zones. */
  function buildSea(level, api) {
    var T = typeof THREE !== 'undefined' ? THREE : null;
    var G = api.geo, hash = api.hash, Z = level.zones, Z1 = Z[0], Z2 = Z[1] || Z[0];
    var X0 = Z1.ox, XE = Z1.ox + Z1.w, XW = Math.min(X0, Z2.ox);
    var zS = Z1.oz + Z1.h + 34, zN = Math.min(Z2.oz, level.hatch ? level.hatch.z - 6 : Z2.oz) - 110;
    var hz0 = Z2.oz - 24, hz1 = Z2.oz + Z2.h + 8;   // the hangar-deck module (west of the main deck)
    var cx = (X0 + XE) / 2, cz = (zN + zS) / 2;
    var deckC = '#575D65', edgeC = '#6B7682', under = '#3E444C', ink = '#15121C';
    // ---- the ocean: one big sheet, swell bands and whitecaps on it
    G.flat([[cx - 1700, cz - 1700], [cx + 1700, cz - 1700], [cx + 1700, cz + 1700], [cx - 1700, cz + 1700]], SEA, '#2A76AE');
    var n = 0;
    for (var gx = -900; gx <= 900; gx += 60) for (var gz = -900; gz <= 900; gz += 60) {
      n++;
      var sx = cx + gx + (hash(n, 3) - 0.5) * 40, sz = cz + gz + (hash(n, 5) - 0.5) * 40;
      if (sx > XW - 6 && sx < XE + 6 && sz > zN - 6 && sz < zS + 6) continue;
      var L = 14 + hash(n, 7) * 26, w = 1.2 + hash(n, 9) * 1.6, k = hash(n, 11);
      G.flat([[sx - L, sz - w], [sx + L, sz - w * 0.6], [sx + L * 0.8, sz + w], [sx - L * 0.9, sz + w * 0.7]], SEA + 0.15, k < 0.5 ? '#3586BE' : '#2369A0');
      if (hash(n, 13) < 0.35) G.flat([[sx - 2.5, sz - 0.5], [sx + 2.8, sz - 0.3], [sx + 2.2, sz + 0.6], [sx - 2.0, sz + 0.5]], SEA + 0.3, '#E8F5FA');
    }
    // ---- the platform deck round the zones (the zones lay their own floor 3 cm above it), its edges and railings
    G.flat([[X0, zN], [XE, zN], [XE, zS], [X0, zS]], -0.03, deckC);
    G.flat([[XW, hz0], [X0, hz0], [X0, hz1], [XW, hz1]], -0.03, deckC);
    function edgeRun(x0, z0, x1, z1, nx, nz) {   // a deck-edge fascia with a railing and a net, outward normal (nx, nz)
      var Lr = Math.hypot(x1 - x0, z1 - z0), mx = (x0 + x1) / 2 + nx * 0.12, mz = (z0 + z1) / 2 + nz * 0.12;
      var sxr = Math.abs(x1 - x0) + Math.abs(nx) * 0.24, szr = Math.abs(z1 - z0) + Math.abs(nz) * 0.24;
      G.box(mx, -0.8, mz, sxr, 1.6, szr, edgeC, { hull: false });
      G.box(mx - nx * 0.5, 1.12, mz - nz * 0.5, Math.abs(x1 - x0) || 0.07, 0.07, Math.abs(z1 - z0) || 0.07, '#F2C230', { hull: false });
      G.box(mx - nx * 0.5, 0.62, mz - nz * 0.5, Math.abs(x1 - x0) || 0.04, 0.9, Math.abs(z1 - z0) || 0.04, '#B7A97F', { hull: false });
      for (var t = 0; t <= Lr; t += 2) {
        var px = x0 + (x1 - x0) * t / Lr - nx * 0.5, pz = z0 + (z1 - z0) * t / Lr - nz * 0.5;
        G.box(px, 0.58, pz, 0.08, 1.16, 0.08, '#F2C230', { hull: false });
      }
    }
    // west edge of the main deck south of the hangar module and north of it; the east edge outside zone 1; the ends
    edgeRun(X0, Z1.oz + Z1.h, X0, zS, -1, 0);
    if (Z1.oz > hz1) edgeRun(X0, hz1, X0, Z1.oz, -1, 0);
    edgeRun(X0, zN, X0, hz0, -1, 0);
    edgeRun(XE, Z1.oz + Z1.h, XE, zS, 1, 0);
    edgeRun(XE, zN, XE, Z1.oz, 1, 0);
    edgeRun(X0, zS, XE, zS, 0, 1);
    edgeRun(X0, zN, XE, zN, 0, -1);
    if (XW < X0) {
      edgeRun(XW, hz0, XW, Z2.oz, -1, 0);
      edgeRun(XW, Z2.oz + Z2.h, XW, hz1, -1, 0);
      edgeRun(XW, hz0, X0, hz0, 0, -1);
      edgeRun(XW, hz1, X0, hz1, 0, 1);
    }
    // the box girder under the deck and the columns down to the sea, braces between them, foam round the columns
    G.box(cx, -3.2, cz, XE - X0 - 1.0, 3.2, zS - zN - 1.0, under, { hull: false, noBottom: false });
    G.box((XW + X0) / 2 + 0.5, -3.2, (hz0 + hz1) / 2, X0 - XW + 1.0, 3.2, hz1 - hz0 - 1.0, under, { hull: false });
    var cols = [];
    for (var zz = zN + 18; zz < zS - 10; zz += 52) { cols.push([X0 + 9, zz]); cols.push([XE - 9, zz]); }
    cols.push([XW + 6, (hz0 + hz1) / 2]);
    cols.forEach(function (p, i) {
      G.cyl(p[0], SEA - 2, p[1], 4.6, 4.2, -4.8 - SEA + 2, 14, '#6F7B88');
      G.cyl(p[0], SEA - 0.5, p[1], 5.6, 5.6, 2.4, 14, '#E2B23A', { hull: false });
      G.flat([[p[0] - 7.5, p[1] - 2], [p[0] - 2, p[1] - 7.5], [p[0] + 2, p[1] - 7.5], [p[0] + 7.5, p[1] - 2], [p[0] + 7.5, p[1] + 2], [p[0] + 2, p[1] + 7.5], [p[0] - 2, p[1] + 7.5], [p[0] - 7.5, p[1] + 2]], SEA + 0.25, '#EAF6FA');
    });
    for (var ci = 0; ci + 2 < cols.length - 1; ci += 2) {
      [0, 1].forEach(function (s) {
        var a = cols[ci + s], b = cols[ci + 2 + s];
        if (!b) return;
        var mz = (a[1] + b[1]) / 2;
        G.box(a[0], -14, mz, 1.0, 1.0, b[1] - a[1], '#626D79', { hull: false });
      });
    }
    // ---- the flight-operations block behind zone 1's south wall (its front is the wall modules), a door header
    var oz = Z1.oz + Z1.h;
    G.box(X0 + RWY[0] / 2, 3.78, oz + 12.5, RWY[0], 7.56, 25, '#D8D6CF', { hull: true });
    G.box(X0 + RWY[0] / 2, 7.66, oz + 12.5, RWY[0] + 0.3, 0.2, 25.3, '#ECEBE6', { hull: false });
    for (var ui = 0; ui < 6; ui++) G.box(X0 + 6 + ui * 8, 8.3, oz + 8 + (ui % 2) * 8, 3.0, 1.1, 2.2, '#A7A49B', { hull: true });
    G.cyl(X0 + 44, 7.7, oz + 18, 0.15, 0.08, 12, 6, '#5A626C');
    if (Z1.entryGate) {
      // the facade over the door: the modules' front plane is 0.95 m inside the zone's south edge
      var gx = Z1.entryGate.x, fz = oz - 0.95;
      G.box(gx, (4.05 + 7.3) / 2, oz - 0.475, 3.1, 7.3 - 4.05, 0.95, '#D8D6CF', { hull: false });
      G.box(gx - 2.0, (4.55 + 7.3) / 2, oz - 0.475, 0.9, 7.3 - 4.55, 0.95, '#D8D6CF', { hull: false });
      G.box(gx + 2.0, (4.55 + 7.3) / 2, oz - 0.475, 0.9, 7.3 - 4.55, 0.95, '#D8D6CF', { hull: false });
      G.box(gx, 7.45, oz - 0.525, 5.0, 0.3, 1.05, '#ECEBE6', { hull: false });
      G.box(gx, 5.35, fz - 0.01, 3.6, 1.9, 0.02, '#2C5A70', { hull: false });
      for (var mi = -1; mi <= 1; mi++) G.box(gx + mi * 1.2, 5.35, fz - 0.03, 0.06, 1.9, 0.02, '#363C45', { hull: false });
    }
    // ---- the runway's markings, from the threshold in zone 1 to the far north end
    var rx0 = X0 + RWY[0], rx1 = X0 + RWY[1], rc = (rx0 + rx1) / 2, thr = Z1.oz + 67.5;
    var white = '#EEF0F0', yel = '#F2C230';
    [rx0 + 0.6, rx1 - 0.6].forEach(function (x) { G.flat([[x - 0.45, zN + 6], [x + 0.45, zN + 6], [x + 0.45, thr + 6.5], [x - 0.45, thr + 6.5]], 0.012, white); });
    for (var dz = thr - 14; dz > zN + 14; dz -= 18) G.flat([[rc - 0.45, dz - 9], [rc + 0.45, dz - 9], [rc + 0.45, dz], [rc - 0.45, dz]], 0.012, white);
    for (var bi = 0; bi < 10; bi++) {
      if (bi === 4 || bi === 5) continue;
      var bx = rx0 + 1.8 + bi * 2.1;
      G.flat([[bx, thr], [bx + 1.5, thr], [bx + 1.5, thr + 6], [bx, thr + 6]], 0.012, white);
    }
    G.flat([[rx0 + 1.2, thr - 0.9], [rx1 - 1.2, thr - 0.9], [rx1 - 1.2, thr - 0.3], [rx0 + 1.2, thr - 0.3]], 0.012, white);
    for (var tz = thr - 40; tz > zN + 40; tz -= 30) [-1, 1].forEach(function (s) {
      for (var q = 0; q < 3; q++) { var x = rc + s * (3.0 + q * 1.4); G.flat([[x - 0.45, tz - 22], [x + 0.45, tz - 22], [x + 0.45, tz], [x - 0.45, tz]], 0.012, white); }
    });
    // the landing area's yellow foul line (west edge of the runway) and taxi lead-in lines across the apron
    G.flat([[rx0 - 1.3, zN + 6], [rx0 - 1.0, zN + 6], [rx0 - 1.0, thr + 6.5], [rx0 - 1.3, thr + 6.5]], 0.011, yel);
    [[X0 + 25.5, Z1.oz + 1, Z1.oz + 22], [X0 + 34.0, Z1.oz + 19, Z1.oz + 22], [X0 + 44.0, Z1.oz + 19, Z1.oz + 22]].forEach(function (L) {
      G.flat([[L[0] - 0.12, L[1]], [L[0] + 0.12, L[1]], [L[0] + 0.12, L[2]], [L[0] - 0.12, L[2]]], 0.011, yel);
    });
    G.flat([[X0 + 25.38, Z1.oz + 21.88], [X0 + 51, Z1.oz + 21.88], [X0 + 51, Z1.oz + 22.12], [X0 + 25.38, Z1.oz + 22.12]], 0.011, yel);
    api.add('RwyNum', rc, 0, thr - 8, 0, 1);
    // the hangar deck: yellow lead-in lines out of each hangar door to the apron line, a white walkway along the west
    if (Z[1]) {
      [14, 50].forEach(function (c) { var x = Z2.ox + c; G.flat([[x - 0.12, Z2.oz + 23.2], [x + 0.12, Z2.oz + 23.2], [x + 0.12, Z2.oz + 44.12], [x - 0.12, Z2.oz + 44.12]], 0.011, yel); });
      G.flat([[Z2.ox + 13.88, Z2.oz + 43.88], [Z2.ox + 50.12, Z2.oz + 43.88], [Z2.ox + 50.12, Z2.oz + 44.12], [Z2.ox + 13.88, Z2.oz + 44.12]], 0.011, yel);
      for (var wz = Z2.oz + 44; wz < Z2.oz + 73; wz += 2.5) G.flat([[Z2.ox + 1.6, wz], [Z2.ox + 1.8, wz], [Z2.ox + 1.8, wz + 1.4], [Z2.ox + 1.6, wz + 1.4]], 0.011, white);
    }
    // ---- the far end of the platform: a radome, masts, a pedestal crane on each module; the escort ships
    G.sphere(XE - 18, 7.0, zN + 26, 7.5, '#ECEBE6', { ws: 12, hs: 8 });
    G.cyl(XE - 18, 0, zN + 26, 3.0, 3.0, 4.0, 10, '#A7A49B');
    [[XE - 34, zN + 18, 22], [XE - 40, zN + 40, 16]].forEach(function (m) { G.cyl(m[0], 0, m[1], 0.35, 0.2, m[2], 6, '#5A626C'); });
    if (!T) return;
    [[XW + 5, hz0 + 6, 0.6], [X0 + 5, zS - 6, 0.9]].forEach(function (k) {   // pedestal cranes, booms out over the sea
      var px = k[0], pz = k[1], a = k[2], dx = -Math.sin(a) * 0.73, dz2 = Math.cos(a) * 0.73;
      G.cyl(px, 0, pz, 1.6, 1.6, 7.5, 10, '#F2C230');
      G.box(px, 8.5, pz, 3.2, 2.0, 3.2, '#E8A13A');
      G.setMatrix(new T.Matrix4().makeTranslation(px + dx * 11, 9.5 + 0.68 * 11, pz + dz2 * 11).multiply(new T.Matrix4().makeRotationY(-a)).multiply(new T.Matrix4().makeRotationX(-0.75)));
      G.box(0, 0, 0, 1.1, 1.1, 22, '#F2C230');
      G.setMatrix(null);
    });
    // the escort ships: two frigates and a destroyer standing off the platform, their wakes
    var ships = [['Backdrop_Frigate', XE + 230, Z1.oz - 70, 0.12, 118], ['Backdrop_Destroyer', XW - 280, Z1.oz - 260, -0.08, 150], ['Backdrop_Frigate', XE + 420, Z1.oz + 300, 0.3, 118]];
    ships.forEach(function (S) {
      var yaw = Math.PI + S[3], sx2 = Math.sin(yaw), cz2 = Math.cos(yaw);
      api.add(S[0], S[1], SEA, S[2], yaw, 1);
      var ax = S[1] - sx2 * S[4] / 2, az = S[2] - cz2 * S[4] / 2;
      for (var d = 0; d < 180; d += 12) {
        var hw = 5 + d * 0.18, px = ax - sx2 * d, pz = az - cz2 * d;
        G.flat([[px - cz2 * hw, pz + sx2 * hw], [px + cz2 * hw, pz - sx2 * hw], [px + cz2 * hw - sx2 * 8, pz - sx2 * hw - cz2 * 8], [px - cz2 * hw - sx2 * 8, pz + sx2 * hw - cz2 * 8]], SEA + 0.2, d < 60 ? '#E8F5FA' : '#7FC0E0');
      }
    });
  }

  var PIECES = ['Edge_A', 'Edge_B', 'Edge_Ring', 'Edge_Hose', 'Edge_Light', 'Corner_NW_W', 'Corner_SW_W', 'Corner_NE_E', 'Corner_SE_E', 'Corner_NE',
    'Corner_SE', 'Fence_A', 'Fence_B', 'Fence_Sign', 'Fence_Light', 'Fence_DeckB_0', 'Fence_DeckB_1', 'Fence_DeckB_2', 'Barricade_Net', 'Barricade_Post',
    'Ops_Win', 'Ops_Plain', 'Ops_Door', 'Ops_Vent', 'Ops_End', 'Ops_Corner', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C',
    'TrailWall_D', 'Hatch', 'Backdrop_Frigate', 'Backdrop_Destroyer', 'RwyNum', 'Jet_Wings', 'Jet_WingsFold', 'Jet_Canopy', 'Jet_Open', 'Landmark_IslandTop', 'Landmark_HangarRoof'];
  for (var k = 0; k < 14; k++) PIECES.push('Ops_Sign_' + k);
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (!d.pieces) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (PIECES.indexOf(n) < 0) PIECES.push(n); });
  });

  IB.registerTheme({
    id: 'pelagic', name: 'Pelagic Airbase', family: 'kit-pelagic', prefix: 'KIT_PELAGIC_',
    palette: ['#565C64', '#F2C230', '#2F6FB8', '#8E99A5'],
    // a clear day far out at sea: deep blue overhead paling to the horizon; the fog is the horizon colour, so the
    // ocean runs into the sky with no edge
    env: { sky: ['#3F8BD6', '#D4E9F5'], fog: { color: '#D4E9F5', near: 120, far: 720, tierScale: true }, sun: [0.45, 0.85, 0.3], clouds: true, ceiling: null, far: 950 },
    floor: { color: '#5A6068', trail: '#6B7178', lines: [{ dir: 'x', every: 4, width: 0.03, color: '#535960', y: 0.006 }, { dir: 'z', every: 4, width: 0.03, color: '#535960', y: 0.008 }] },
    wall: { height: 1.2, roof: '#5A6068', facing: 'open', choose: chooseWall, cols: true },
    symbols: SYMBOLS,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall_D'], height: 2.6 },
    hatch: 'Hatch', stand: 'Crates',
    backdrop: { build: buildSea },
    budget: { prop: 2400, landmark: 4000, total: 60000 },
    allPieces: function () { return PIECES.slice(); },
    levels: {
      pelagic: {
        name: 'Pelagic Airbase',
        intro: 'Robots have seized Pelagic Airbase, a fortified air platform far out at sea. Fight across the flight deck past the island tower, then clear the hangar deck.',
        zones: [
          // the flight deck: the apron, the island, the runway; the first wave is light robots only
          { map: 'pelagic_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 6]],
            [['crawler', 15], ['gunner', 10], ['bomber', 2], ['soldier', 6], ['blader', 4]],
            [['crawler', 14], ['drone', 8], ['gunner', 9], ['soldier', 6], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 7], ['blader', 4]],
            [['crawler', 15], ['gunner', 9], ['drone', 6], ['soldier', 6], ['blader', 4]]] },
          // the hangar deck: the hangars, the tower, the fuel farm, the container yard
          { map: 'pelagic_2', waves: [
            [['crawler', 17], ['gunner', 10], ['drone', 5], ['soldier', 6]],
            [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 4]],
            [['crawler', 16], ['gunner', 10], ['bomber', 2], ['soldier', 5], ['blader', 4]],
            [['crawler', 15], ['drone', 7], ['gunner', 9], ['soldier', 5], ['blader', 4]],
            [['crawler', 17], ['gunner', 9], ['bomber', 2], ['soldier', 4], ['blader', 4]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
