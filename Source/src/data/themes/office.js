/* Theme: Office Skyscraper (kit-office). A corporate floor high in a midtown New York tower: grey-blue carpet tiles,
   white / fabric cubicle pods, oak desks, glass meeting rooms, a walnut-and-stone sky lobby around the elevator core,
   and floor-to-ceiling curtain walls looking out over a hazy skyline of deco spires, glass towers and water tanks.

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  wall: curtain-wall bays on the zone edge (piers every 6 m, lobby stone / walnut near the gates),
        drywall partitions inside (art, whiteboards, doors, screens), four-sided cores at junctions and columns
     =  lateral file run        c  copier / printer / archive boxes     F  tall cabinet / bookcase
     p  floor plant             r  server rack (runs)                   k  kitchen counter run (sink, coffee, microwave)
     f  fridge / snack machine  w  water cooler / recycling bins
     K  cubicle pod [4,4]       b  bench desks [4,3]                    M  glass meeting room [8,6]
     D  executive desk [4,3]    L  lounge [4,3]                         T  elevator core [12,6] (landmark)
     R  reception desk [6,3]    m  marble floor tile [4,4] (no collision)
   The wall chooser gets (c, r, horiz, corner, hash, grid). Edge cells on the east / west sides arrive with horiz set
   (the engine counts the outside of the grid as wall and places them unrotated), so it hands back the pre-turned
   _W / _E window modules; if the engine ever turns those cells itself (horiz false) the plain modules are used. */
(function (IB) {
  'use strict';
  var WIN = ['Win_A', 'Win_A', 'Win_B', 'Win_A', 'Win_C', 'Win_B', 'Win_A'];
  var DRY = ['Dry_A', 'Dry_A', 'Dry_Art', 'Dry_A', 'Dry_Board', 'Dry_A', 'Dry_Door', 'Dry_Ext', 'Dry_A', 'Dry_Screen'];
  function pick(list, h) { return list[Math.min(list.length - 1, Math.floor(h * list.length))]; }
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  // gate centres per grid (north row G, south row E), cached on the grid object
  function gates(grid) {
    if (grid._officeGates) return grid._officeGates;
    var g = [], e = [];
    for (var c = 0; c < grid.w; c++) { if (grid.at(c, 0) === 'G') g.push(c); if (grid.at(c, grid.h - 1) === 'E') e.push(c); }
    grid._officeGates = { g: g.length ? (g[0] + g[g.length - 1] + 1) / 2 : -99, e: e.length ? (e[0] + e[e.length - 1] + 1) / 2 : -99 };
    return grid._officeGates;
  }
  function chooseWall(c, r, horiz, corner, hash, grid) {
    var W = grid.w, Hh = grid.h, west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1;
    if ((west || east) && (north || south)) return 'WinCorner_' + (north ? 'N' : 'S') + (west ? 'W' : 'E');
    if (west || east) {
      if (wallish(grid.at(west ? 1 : c - 1, r))) return 'Core';          // an interior wall meets the facade
      var side = horiz ? (west ? '_W' : '_E') : '';
      if (r % 6 === 3) return 'WinCol' + side;
      return pick(WIN, hash(c * 7 + 3, r * 13 + 1)) + side;
    }
    if (north || south) {
      if (wallish(grid.at(c, north ? 1 : r - 1))) return 'Core';
      var gc = north ? gates(grid).g : gates(grid).e, d = Math.abs(c + 0.5 - gc);
      if (d < 4) return 'LobbyStone';
      if (d < 9) return (Math.floor(d) % 3 === 1) ? 'LobbyWoodSconce' : 'LobbyWood';
      if (c % 6 === 3) return 'WinCol';
      return pick(WIN, hash(c * 7 + 3, r * 13 + 1));
    }
    // interior: four-sided cores at junctions, thick blocks and lone columns; partitions on straight runs
    var vert = wallish(grid.at(c, r - 1)) || wallish(grid.at(c, r + 1));
    if (corner || !(horiz || vert)) return 'Core';
    return pick(DRY, hash(c * 5 + 1, r * 11 + 7));
  }

  IB.registerTheme({
    id: 'office', name: 'Office Skyscraper', family: 'kit-office', prefix: 'KIT_OFFICE_',
    palette: ['#7FA3C4', '#DDBE8F', '#12C7B6', '#B9C4D0'],
    env: {
      sky: ['#7EC4F2', '#CCDCE8'], fog: { color: '#CCDCE8', near: 40, far: 125 }, clouds: true,
      // a low, southern sun: floors and south faces lit, the ceiling a light 0.9 band (never the purple shadow band)
      sun: [0.12, 0.45, 0.885],
      ceiling: { height: 4.0, color: '#F7F7F4', light: 'CeilLight', every: 4 }
    },
    // grey-blue carpet tiles; polished concrete corridors; the city haze below the windows
    floor: {
      color: '#B9C4D0', trail: '#D3D7DC', outside: '#CCDCE8',
      lines: [{ dir: 'x', every: 1, width: 0.03, color: '#A9B5C3', y: 0.008 }, { dir: 'z', every: 1, width: 0.03, color: '#A9B5C3', y: 0.0105 }]
    },
    wall: { height: 4.0, roof: '#C9CED6', faceOpen: true, choose: chooseWall },
    showAllZones: true,   // glass walls all round: every wing of the floor stays drawn (Z.setVisible)
    symbols: {
      '=': { pieces: ['File_A', 'File_B', 'File_C', 'File_A'], h: 1.03, rotate: 'run', kind: 'cover' },
      'c': { pieces: ['Copier', 'Printer', 'Boxes'], h: 1.1, rotate: 'random90', kind: 'cover' },
      'F': { pieces: ['Tall_A', 'Tall_B'], h: 1.85, rotate: 'random90', kind: 'cover' },
      'p': { pieces: ['Plant_Fig', 'Plant_Snake', 'Plant_Palm'], h: 0.6, rotate: 'random90', kind: 'cover' },
      'r': { pieces: ['Rack_A', 'Rack_B'], h: 2.1, rotate: 'run', alternate: true, kind: 'cover' },
      'k': { pieces: ['Counter_Plain', 'Counter_Sink', 'Counter_Coffee', 'Counter_Micro'], h: 0.94, rotate: 0, sequence: true, kind: 'cover' },
      'f': { pieces: ['Fridge', 'Vending'], h: 1.85, rotate: 0, sequence: true, kind: 'cover' },
      'w': { pieces: ['Cooler', 'Bins'], h: 1.45, rotate: 0, sequence: true, kind: 'cover' },
      'K': { size: [4, 4], pieces: ['Cubicle_A', 'Cubicle_B'], flip: true, kind: 'cover' },
      'b': { size: [4, 3], pieces: ['Bench_A'], flip: true, kind: 'cover' },
      'M': { size: [8, 6], pieces: ['Meeting_A', 'Meeting_B'], flip: true, kind: 'wall' },
      'D': { size: [4, 3], pieces: ['Exec_A'], kind: 'cover' },
      'L': { size: [4, 3], pieces: ['Lounge_A', 'Lounge_B'], flip: true, kind: 'cover' },
      'T': { size: [12, 6], pieces: ['Landmark_Elevators'], kind: 'wall' },
      'R': { size: [6, 3], pieces: ['Landmark_Reception'], kind: 'cover' },
      'm': { size: [4, 4], pieces: ['FloorMarble'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.99, shutterHeight: 3.05 },
    // corridor drywall with framed prints, whiteboards, status screens and fire cabinets mixed in
    trail: { wall: 'TrailWall', height: 4.0, variants: ['TrailWall', 'TrailWall_Art', 'TrailWall_Board', 'TrailWall_Screen', 'TrailWall_Ext'],
      end: 'TrailWall' },   // the express elevator stands against the hatch room's back wall
    hatch: 'Hatch', stand: 'Stand',
    // the skyline: one long layered slice of Manhattan (cloud banks, pre-war rooftops with water tanks, mid towers,
    // deco spires and glass needles). Ring 0 with count 4 lands exactly due east, south, west and north of the level's
    // centre, each copy facing it; rr = (level half-length) + 52 and squeezeX puts the side rows 52 m from the centre
    // line (about 24 m outside the windows) and the end rows 52 m beyond the first and last zones.
    backdrop: { ring: [
      { piece: 'Backdrop_Skyline', count: 4, radius: [52, 52], scale: [1, 1], squeezeX: 0.347, face: true }
    ] },
    // the city 58 floors down (see Z.buildCityBelow): streets, rooftops and water tanks under the haze
    below: { depth: 170, haze: '#CCDCE8', hazeTop: 0.18, hazeBottom: 0.6, glass: '#6F8FB0',
      // footprints of the Backdrop_Skyline buildings (fam_kit_office.py backdrop_skyline: near blocks, mid towers,
      // far towers): [x along the row, front depth, width, depth, colour, window colour]. Keep in sync with the kit.
      skyline: [
        [-109, 7, 16, 12, '#CB937A', '#64798E'],
        [-88, 7, 18, 14, '#E8DECB', '#64798E'],
        [-66, 6, 15, 11, '#C9A574', '#64798E'],
        [-44, 8, 19, 13, '#CB937A', '#64798E'],
        [-22, 7, 16, 12, '#D3C6AE', '#64798E'],
        [0, 6, 18, 14, '#CB937A', '#64798E'],
        [22, 7, 15, 12, '#E8DECB', '#64798E'],
        [44, 8, 17, 13, '#C9A574', '#64798E'],
        [66, 6, 16, 12, '#CB937A', '#64798E'],
        [88, 7, 18, 14, '#D3C6AE', '#64798E'],
        [110, 8, 14, 11, '#CB937A', '#64798E'],
        [-100, 25, 16, 12, '#D3C6AE', '#64798E'],
        [-70, 25, 14, 12, '#A9CDE2', '#87AFCB'],
        [-40, 25, 15, 11, '#CB937A', '#64798E'],
        [-8, 26, 18, 12, '#D3C6AE', '#64798E'],
        [26, 26, 14, 12, '#A9CDE2', '#87AFCB'],
        [58, 25, 16, 11, '#CB937A', '#64798E'],
        [92, 26, 17, 12, '#D3C6AE', '#64798E'],
        [-90, 40, 16, 16, '#A9CDE2', '#87AFCB'],
        [-56, 42, 18, 16, '#E8DECB', '#64798E'],
        [-22, 41, 9, 9, '#A4D0C6', '#87AFCB'],
        [12, 40, 22, 16, '#E8DECB', '#64798E'],
        [46, 41, 26, 12, '#D3C6AE', '#64798E'],
        [80, 42, 18, 16, '#E8DECB', '#64798E'],
        [110, 42, 9, 9, '#A4D0C6', '#87AFCB']
      ] },
    budget: { prop: 2500, landmark: 4000, total: 70000 },
    allPieces: function () {
      var out = [];
      ['A', 'B', 'C'].forEach(function (k) { ['', '_W', '_E'].forEach(function (s) { out.push('Win_' + k + s); }); });
      ['', '_W', '_E'].forEach(function (s) { out.push('WinCol' + s); });
      ['NW', 'NE', 'SE', 'SW'].forEach(function (s) { out.push('WinCorner_' + s); });
      DRY.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      out = out.concat(['Core', 'LobbyWood', 'LobbyWoodSconce', 'LobbyStone', 'CeilLight', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Art', 'TrailWall_Board', 'TrailWall_Screen', 'TrailWall_Ext', 'Hatch', 'Stand',
        'Backdrop_Skyline']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) { sym[ch].pieces.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    levels: {
      office: {
        name: 'Sky Floor 58',
        intro: 'Fifty-eight floors up. Clear the cubicles, the glass wing, then the sky lobby.',
        zones: [
          { map: 'office_cubicles', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['crawler', 6], ['bomber', 2], ['gunner', 1]],
            [['crawler', 4], ['gunner', 2], ['drone', 2], ['blader', 1]],
            [['crawler', 5], ['bomber', 3]]] },
          { map: 'office_wing', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['drone', 3], ['crawler', 5], ['bomber', 1]],
            [['gunner', 3], ['crawler', 5], ['blader', 1]],
            [['crawler', 3], ['bomber', 2], ['drone', 2], ['soldier', 1]]] },
          { map: 'office_lobby', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['drone', 2], ['bomber', 2], ['crawler', 5], ['blader', 1]],
            [['gunner', 3], ['crawler', 6], ['drone', 1]],
            [['crawler', 4], ['bomber', 3], ['gunner', 2], ['drone', 2], ['soldier', 1]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
