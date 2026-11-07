/* Theme: Downtown at Dusk (kit-city2). A dense downtown at sunset, built to look nothing like Small City's sunny main
   street or the office skyline: 4-6 storey brownstones, red-brick tenements hung with fire escapes, cream cast-iron
   lofts and lavender deco fronts, warm lit windows, neon sign bands and blade signs over dark shop glass, an elevated
   railway on riveted green steel (one span with a stopped train), a subway entrance, a statue plaza, cabs, box
   trucks, newsstands, hot-dog carts, steam stacks and billboards. Purple-to-tangerine sky, warm haze.
   Built by blender/fam_kit_city2.py; zone layouts by tools/city2_zones.py (src/data/zones/city2_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] cells):
     #  facade (the zone edge is 1 cell thick; inner blocks are thicker and roofed)
     ,  sidewalk     ;  plaza granite     -  |  white lane dash along X / Z     ~  !  double yellow along X / Z
     z  Z  zebra bars along X / Z         o  manhole                          (all of these: no collision)
     i  l  e  w  street light with its arm over the street to the S / N / E / W        I  twin-globe plaza lamp
     t  street tree      m  hydrant / mailbox / news boxes / litter basket      c  trash bags / boxes / pallets
     =  sawhorse (runs)  j  jersey barrier (runs)    s  steam stack     b  bench [2,1]     C  cab / sedan [2,4]
     V  box truck [2,5]  k  newsstand [2,3]          n  hot-dog cart [2,2]               Y  billboard on legs [6,2]
     L  elevated railway span [4,6]     R  span with a stopped train [4,12]   (open underneath: only the columns
        collide; a run must reach the zone edge at both ends, where the facade becomes a dark El portal)
     U  subway entrance [3,5] (opens south)      Q  statue on a granite plinth [4,4] (landmark)
   The wall uses facing 'open'. The chooser cuts every facade run into buildings 4-7 m wide (each with its own style
   and height), puts pilasters on the taller side of a boundary, corner piers where facades meet, a shop door with a
   neon blade sign in each building, three bays of fire escape on brownstones and tenements, plain brick beside inner
   corners and gates, and the El portal where the railway meets the wall. */
(function (IB) {
  'use strict';
  // must mirror STYLES in blender/fam_kit_city2.py: [material, storeys]
  var STY = [['B', 5], ['K', 6], ['I', 4], ['D', 6], ['K', 5], ['B', 4], ['I', 5], ['D', 5]];
  var NSTY = STY.length, ESC = 'BK';
  var WIDTHS = [5, 6, 4, 7, 5, 4, 6], WSUM = 37;
  var CARS = ['Cab', 'Sedan_Plum', 'CabAd', 'Sedan_Teal', 'Cab'];
  var FURNITURE = ['Hydrant', 'Mailbox', 'NewsBoxes', 'TrashCan'], JUNK = ['TrashBags', 'Boxes', 'Pallets'];

  function segment(pos, line, hash) {
    var p = pos + Math.floor(hash(line * 7 + 3, 11) * WSUM), cyc = Math.floor(p / WSUM), q = p - cyc * WSUM, k = 0;
    while (q >= WIDTHS[k]) { q -= WIDTHS[k]; k++; }
    return { b: cyc * WIDTHS.length + k, i: q, w: WIDTHS[k] };
  }
  // neighbouring buildings never share a style
  function styleOf(b, line, hash) { var s = (Math.floor(hash(line * 5 + 1, 17) * NSTY) + b * 3 + Math.floor(hash(b + 50, line + 99) * 2)) % NSTY; return s < 0 ? s + NSTY : s; }
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  // building run of a facade cell: position along the run and the run's line (rows for N/S faces, columns for E/W)
  function runAt(c, r, ns, hash) { var line = ns ? r : c + 997, g = segment(ns ? c : r, line, hash); return { g: g, s: styleOf(g.b, line, hash), line: line }; }

  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none' || !face) {
      var a = STY[runAt(c, r, true, hash).s], b = STY[runAt(c, r, false, hash).s], t = a[1] >= b[1] ? a : b;
      return 'Corner_' + t[0] + t[1];
    }
    var ns = face === 'S' || face === 'N', dc = ns ? 1 : 0, dr = ns ? 0 : 1;
    var fc = c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), fr = r + (face === 'S' ? 1 : face === 'N' ? -1 : 0);
    var R = runAt(c, r, ns, hash), g = R.g, s = R.s, st = STY[s], n = st[1];
    var front = grid.at(fc, fr);
    if (front === 'L' || front === 'R') return 'Portal_' + s;                      // the El runs into the facade
    for (var d = -2; d <= 2; d++) { var q = grid.at(c + d * dc, r + d * dr); if (q === 'G' || q === 'E') return 'Pilaster_' + st[0] + n; }
    if (wallish(grid.at(fc - dc, fr - dr)) || wallish(grid.at(fc + dc, fr + dr))) return 'Blank_' + st[0] + n;   // inner corner
    var nPrev = STY[styleOf(g.b - 1, R.line, hash)][1], nNext = STY[styleOf(g.b + 1, R.line, hash)][1];
    if ((g.i === 0 && n >= nPrev) || (g.i === g.w - 1 && n > nNext)) return 'Pilaster_' + st[0] + n;
    var door = 1 + Math.floor(hash(g.b + 7, R.line) * (g.w - 2));
    if (g.i === door) return 'Door_' + s;
    if (ESC.indexOf(st[0]) >= 0 && g.w >= 6) {                                      // three bays of fire escape (wide buildings)
      var e0 = door <= 2 ? door + 1 : door - 3, k = g.i - e0;
      if (k >= 0 && k < 3) return ['EscB_', 'EscA_', 'EscC_'][k] + s;
    }
    return Math.abs(g.i - door) % 2 === 1 ? (hash(c * 3 + 1, r * 7 + 2) < 0.5 ? 'Win_' : 'Win2_') + s : 'Pier_' + s;
  }

  function wallPieces() {
    var out = [], seen = {};
    for (var s = 0; s < NSTY; s++) {
      out.push('Win_' + s, 'Win2_' + s, 'Door_' + s, 'Pier_' + s, 'Portal_' + s);
      if (ESC.indexOf(STY[s][0]) >= 0) out.push('EscA_' + s, 'EscB_' + s, 'EscC_' + s);
    }
    STY.forEach(function (t) { var k = t[0] + t[1]; if (!seen[k]) { seen[k] = 1; out.push('Pilaster_' + k, 'Corner_' + k, 'Blank_' + k); } });
    return out;
  }
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }

  IB.registerTheme({
    id: 'city2', name: 'Downtown at Dusk', family: 'kit-city2', prefix: 'KIT_CITY2_',
    palette: ['#8E5644', '#FF4FA8', '#45E6F2', '#F6C33B'],
    // sunset: violet zenith to a tangerine horizon, warm rose haze, a low sun from the west
    env: { sky: ['#4E4793', '#FF9F6E'], fog: { color: '#C98A8C', near: 48, far: 150 }, sun: [-0.78, 0.42, 0.3], clouds: true, ceiling: null },
    floor: { color: '#4F4C5C', trail: '#625D6C', outside: '#3C3946' },
    wall: { height: 8, roof: '#4C4656', facing: 'open', choose: chooseWall },
    symbols: {
      ',': flat(['Walk', 'WalkB'], 0, true),
      ';': flat(['Plaza', 'PlazaB'], 0, true),
      '-': flat(['LaneW'], 0), '|': flat(['LaneW'], Math.PI / 2),
      '~': flat(['LaneY'], 0), '!': flat(['LaneY'], Math.PI / 2),
      'z': flat(['Zebra'], 0), 'Z': flat(['Zebra'], Math.PI / 2),
      'o': flat(['Manhole']),
      'i': { pieces: ['Lamp'], rotate: 0, kind: 'prop' },
      'l': { pieces: ['Lamp'], rotate: Math.PI, kind: 'prop' },
      'e': { pieces: ['Lamp'], rotate: Math.PI / 2, kind: 'prop' },
      'w': { pieces: ['Lamp'], rotate: -Math.PI / 2, kind: 'prop' },
      'I': { pieces: ['LampP'], kind: 'prop' },
      't': { pieces: ['StreetTree'], rotate: 'random90', kind: 'prop' },
      'm': { pieces: FURNITURE, rotate: 'random90', kind: 'cover' },
      'c': { pieces: JUNK, rotate: 'random90', kind: 'cover' },
      '=': { pieces: ['Sawhorse'], rotate: 'run', kind: 'cover' },
      'j': { pieces: ['Jersey'], rotate: 'run', kind: 'cover' },
      's': { pieces: ['SteamStack'], rotate: 'random90', kind: 'prop' },
      'b': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      'C': { size: [2, 4], pieces: CARS, flip: true, kind: 'cover' },
      'V': { size: [2, 5], pieces: ['Truck'], flip: true, kind: 'cover' },
      'k': { size: [2, 3], pieces: ['Newsstand'], flip: true, kind: 'cover' },
      'n': { size: [2, 2], pieces: ['HotDog'], kind: 'cover' },
      'Y': { size: [6, 2], pieces: ['Billboard'], kind: 'wall' },
      'L': { size: [4, 6], pieces: ['El_A', 'El_A', 'El_B'], kind: 'wall' },
      'R': { size: [4, 12], pieces: ['Landmark_ElTrain'], kind: 'wall' },
      'U': { size: [3, 5], pieces: ['Landmark_Subway'], kind: 'wall' },
      'Q': { size: [4, 4], pieces: ['Landmark_Statue'], kind: 'wall' }
    },
    // the gates are bridge buildings over the street (closed to the rooflines); the passages between blocks are
    // 16 m brick alleys, so nothing of the next block shows over them
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 16 },
    hatch: 'Hatch', stand: 'Boxes',
    backdrop: { ring: [
      { piece: 'Backdrop_Block', count: 14, radius: [20, 30], scale: [0.95, 1.2], face: true, squeezeX: 0.75 },
      { piece: 'Backdrop_Tower', count: 8, radius: [36, 48], scale: [0.9, 1.25], face: true, squeezeX: 0.8 },
      { piece: 'Backdrop_Spire', count: 2, radius: [50, 56], scale: [1.0, 1.1], face: true, squeezeX: 0.85 }
    ] },
    budget: { prop: 2500, landmark: 5000, total: 70000 },
    allPieces: function () {
      var out = wallPieces().concat(['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Backdrop_Block', 'Backdrop_Tower', 'Backdrop_Spire']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) { sym[ch].pieces.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    levels: {
      city2: {
        name: 'Downtown at Dusk',
        intro: 'The lights are on and the robots own the avenue. Clear three blocks before nightfall.',
        zones: [
          // El Avenue: crawlers down the avenue, gunners behind the parked cabs, a drone under the El
          { map: 'city2_avenue', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['crawler', 4], ['gunner', 3], ['soldier', 1]],
            [['crawler', 3], ['gunner', 2], ['drone', 1], ['blader', 1]],
            [['crawler', 3], ['gunner', 2], ['soldier', 1]]] },
          // Statue Plaza: bombers across the open granite, gunners on the ring road
          { map: 'city2_plaza', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['crawler', 3], ['bomber', 3], ['blader', 1]],
            [['gunner', 3], ['drone', 1], ['crawler', 2], ['soldier', 2]],
            [['crawler', 3], ['bomber', 2], ['gunner', 2], ['blader', 1]]] },
          // The Crossing: everything at once round the two blocks and under the train
          { map: 'city2_crossing', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['bomber', 3], ['crawler', 3], ['drone', 1], ['soldier', 1]],
            [['gunner', 3], ['crawler', 3], ['soldier', 2]],
            [['crawler', 2], ['bomber', 2], ['gunner', 2], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
