/* Theme: Big Bedroom (kit-bedroom). A "tiny" theme: the player and the trash robots are toy-sized, so a kid's bedroom
   is giant around them (about x6): 18 m walls painted sky blue / lilac / pink with a white skirting board and a
   star-and-cloud border, honey floorboards, a bed you can run under, toy chests, alphabet blocks, a train set,
   crayons, a desk and bookcases. Indoor: no sky, an 18 m ceiling with glow stars and a saucer lamp.

   Map notes (src/data/zones/bedroom_*.txt, 1 char = 1 m):
   - the top-left corner cell holds the wall paint scheme digit (1 sky blue, 2 lilac + night border, 3 pink + rainbow);
     that cell is hidden behind the corner of the room.
   - wall overlays sit in the floor row in front of a wall: W window, q/p posters, f/F wall shelf, d door
     (lower-case q/f and W/d face south or east, so they go on north or west walls; p/F go on south or east walls).
   - T is a 10 x 1 anchor along the headboard: the bed itself reaches 15 m south (or east) of it, so the cells under
     the bed stay free for spawns and lost toys. O/Y/t are 2 x 2 anchors for the round rug, striped rug and train track
     (the track's straights run 5 m north and south of the anchor centre, so a 2-row train 4 rows below it sits on the rails).
   - L, *, M hang from the ceiling (lamp, glow stars, mobile); they never block the floor cell they sit on. */
(function (IB) {
  'use strict';
  var CEIL = 18;
  var WALLISH = '#GE';
  var SOLID = '#GE123';          // the scheme digit counts as wall when looking for the open side
  var DIRS = ['S', 'E', 'N', 'W']; // a quarter turn of yaw (three.js, about +Y) turns S into E, E into N ...

  // engine yaw for a '#' cell (mirrors Zones.buildWalls with faceOpen), in quarter turns
  function engineTurns(c, r, grid) {
    function wl(cc, rr) { return WALLISH.indexOf(grid.at(cc, rr)) >= 0; }
    var h = wl(c - 1, r) || wl(c + 1, r), v = wl(c, r - 1) || wl(c, r + 1);
    var q = (!h && v) ? 1 : 0;
    if (q === 0 && !wl(c, r - 1) && wl(c, r + 1)) q = 2;
    if (q !== 0 && !wl(c - 1, r) && wl(c + 1, r)) q = 3;
    return q;
  }
  function chooseWall(c, r, horiz, corner, hash, grid) {
    var m = grid.at(0, 0), scheme = (m === '2' || m === '3') ? m : '1';
    function sd(cc, rr) { return SOLID.indexOf(grid.at(cc, rr)) >= 0; }
    var open = [];
    if (!sd(c, r + 1)) open.push('S');
    if (!sd(c, r - 1)) open.push('N');
    if (!sd(c + 1, r)) open.push('E');
    if (!sd(c - 1, r)) open.push('W');
    if (open.length !== 1) return 'Wall_Corner';
    var want = open[0], q = engineTurns(c, r, grid);
    var authored = DIRS[(DIRS.indexOf(want) - q + 8) % 4];
    if (authored === 'N') return 'Wall_Corner';
    // border motif every other module (star, accent), only where both neighbours continue the same wall face
    var along = (want === 'N' || want === 'S'), k = along ? c : r;
    var motif = 'Plain';
    if (k % 2 === 0) {
      var a1 = along ? [c - 1, r] : [c, r - 1], a2 = along ? [c + 1, r] : [c, r + 1];
      var room = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] }[want];
      var ok = grid.at(a1[0], a1[1]) === '#' && grid.at(a2[0], a2[1]) === '#' &&
        !sd(a1[0] + room[0], a1[1] + room[1]) && !sd(a2[0] + room[0], a2[1] + room[1]);
      if (ok) motif = (k % 4 === 0) ? 'Star' : 'Accent';
    }
    return 'Wall' + scheme + '_' + motif + '_' + authored;
  }

  var BLOCKS = ['Block_A', 'Block_B', 'Block_C', 'Block_D'];
  var POSTERS = ['Poster_A', 'Poster_B', 'Poster_C', 'Poster_D'];
  IB.registerTheme({
    id: 'bedroom', name: 'Big Bedroom', family: 'kit-bedroom', prefix: 'KIT_BEDROOM_',
    palette: ['#8ED2FF', '#FFB4CF', '#FFD45E', '#C79A6B'],
    env: {
      sky: null, clear: '#F7EBDD',
      fog: { color: '#FFF2E4', near: 40, far: 140 },
      // CeilingTile (1 m, every 1 m) hides the engine ceiling: its custom normals face up so it shades light
      ceiling: { height: CEIL, color: '#F6F2FF', light: 'CeilingTile', every: 1 },
      clouds: false
    },
    floor: {
      color: '#DDA96F', trail: '#D49E64',
      lines: [{ dir: 'z', every: 0.9, width: 0.05, color: '#B8814C', y: 0.008 }]
    },
    wall: { height: 18.4, roof: '#FFFFFF', faceOpen: true, choose: chooseWall },
    symbols: {
      'T': { size: [10, 1], pieces: ['Landmark_Bed'], kind: 'wall' },
      'C': { size: [5, 3], pieces: ['ToyChest_A', 'ToyChest_B'], kind: 'cover', sequence: true },
      'c': { pieces: BLOCKS, h: 0.912, rotate: 'random90', stack: { piece: 'Block_E', chance: 0.3, h: 0.912 }, kind: 'cover' },
      '=': { pieces: ['BookStack_A', 'BookStack_B'], h: 1.0, rotate: 'run', alternate: true, kind: 'cover' },
      'D': { size: [8, 4], pieces: ['Desk'], kind: 'wall' },
      'k': { size: [3, 3], pieces: ['Chair'], kind: 'cover' },
      'K': { size: [5, 2], pieces: ['Bookcase'], kind: 'wall' },
      'Q': { size: [5, 2], pieces: ['Bookcase_R'], kind: 'wall' },
      'U': { size: [6, 2], pieces: ['CubeShelf'], kind: 'cover' },
      'N': { size: [3, 3], pieces: ['Nightstand'], kind: 'cover' },
      'X': { size: [6, 6], pieces: ['ToyCastle'], kind: 'cover' },
      'o': { size: [3, 3], pieces: ['Ball'], kind: 'cover', y: 0.07 },
      'v': { size: [3, 2], pieces: ['ToyCar_A', 'ToyCar_B'], kind: 'cover', flip: true, sequence: true },
      'e': { size: [4, 2], pieces: ['TrainEngine'], kind: 'cover' },
      'x': { size: [3, 2], pieces: ['TrainCar_A', 'TrainCar_B'], kind: 'cover', sequence: true },
      'r': { size: [3, 2], pieces: ['CrayonPile_A', 'CrayonPile_B'], kind: 'cover', flip: true, sequence: true, y: 0.04 },
      'l': { size: [5, 1], pieces: ['Pencil'], kind: 'cover', flip: true, y: 0.04 },
      'm': { size: [3, 3], pieces: ['ClothesPile'], kind: 'cover', flip: true },
      'z': { size: [2, 2], pieces: ['BrickTower'], kind: 'cover' },
      'O': { size: [2, 2], pieces: ['Rug_Round'], collide: false },
      'Y': { size: [2, 2], pieces: ['Rug_Stripe'], collide: false },
      't': { size: [2, 2], pieces: ['TrackLoop'], collide: false },
      'W': { size: [9, 1], pieces: ['Window'], kind: 'wall' },
      'q': { size: [4, 1], pieces: POSTERS, collide: false, sequence: true },
      'p': { size: [4, 1], pieces: POSTERS.map(function (n) { return n + '_R'; }), collide: false, sequence: true },
      'f': { size: [5, 1], pieces: ['WallShelf'], collide: false },
      'F': { size: [5, 1], pieces: ['WallShelf_R'], collide: false },
      'd': { size: [6, 1], pieces: ['Door'], kind: 'wall' },
      'L': { pieces: ['CeilingLamp'], y: CEIL, collide: false },
      '*': { pieces: ['CeilingStars_A', 'CeilingStars_B'], y: CEIL, rotate: 'random90', collide: false },
      'M': { pieces: ['Mobile'], y: CEIL, rotate: 'random90', collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 18.3, variants: ['TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_E'] },
    hatch: 'Hatch', stand: 'Block_C',
    backdrop: null,
    budget: { prop: 2000, landmark: 4000, total: 70000 },
    allPieces: function () {
      var out = ['Wall_Corner'];
      ['1', '2', '3'].forEach(function (s) {
        ['Plain', 'Star', 'Accent'].forEach(function (m) { ['S', 'E', 'W'].forEach(function (d) { out.push('Wall' + s + '_' + m + '_' + d); }); });
      });
      var seen = {};
      Object.keys(this.symbols).forEach(function (ch) {
        var d = this.symbols[ch];
        d.pieces.concat(d.stack ? [d.stack.piece] : []).forEach(function (n) { seen[n] = 1; });
      }, this);
      return out.concat(Object.keys(seen), ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'CeilingTile'], this.trail.variants);
    },
    levels: {
      bedroom: {
        name: 'Big Bedroom',
        intro: 'Toy-sized and outnumbered. Clear the floor, the bed, then the desk corner.',
        zones: [
          // 35 + 40 + 53 = 128 robots; the last wave of the desk corner is the dense finale
          { map: 'bedroom_toyspill', waves: [
            [['crawler', 7], ['gunner', 1]],
            [['crawler', 6], ['bomber', 2], ['gunner', 1]],
            [['crawler', 6], ['drone', 2], ['gunner', 1]],
            [['crawler', 5], ['gunner', 2], ['bomber', 2]]
          ] },
          { map: 'bedroom_underbed', waves: [
            [['crawler', 8], ['gunner', 2]],
            [['crawler', 5], ['bomber', 3], ['drone', 1]],
            [['crawler', 6], ['gunner', 3], ['drone', 1]],
            [['crawler', 5], ['bomber', 3], ['gunner', 2], ['drone', 1]]
          ] },
          { map: 'bedroom_deskcorner', waves: [
            [['crawler', 7], ['gunner', 2], ['drone', 1]],
            [['crawler', 6], ['bomber', 3], ['gunner', 2]],
            [['crawler', 7], ['drone', 3], ['bomber', 2]],
            [['crawler', 10], ['gunner', 4], ['bomber', 3], ['drone', 3]]
          ] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
