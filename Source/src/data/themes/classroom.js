/* Theme: Classroom (kit-classroom). Campaign level 3, a TINY theme: the player and the trash robots are toy-sized,
   so the furniture is giant (brief 5.12, about x6): desk tops at 4.45 m on steel legs you run under, 2.6 m chair
   seats, 16.6 m walls with daylight window bays, a 21 m chalkboard, a floor globe and the teacher's desk.
   Palette: chalkboard green, honey wood, pale mint / cream walls, light linoleum tiles, crayon primaries. */
(function (IB) {
  'use strict';
  var LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  var DESKS = ['DeskSet_A', 'DeskSet_A', 'DeskSet_B', 'DeskSet_B', 'DeskSet_C', 'DeskSet_D'];
  var BLOCKS = ['Block_R', 'Block_B', 'Block_Y', 'Block_G'];
  var STACKS = ['BookStack_A', 'BookStack_B', 'BookStack_C'];
  var BAGS = ['Backpack_A', 'Backpack_B'];
  var BEANS = ['BeanBag_R', 'BeanBag_B', 'BeanBag_Y'];
  var PAPERS = ['Paper_A', 'Paper_B', 'Paper_C'];
  var FLOORSTUFF = ['Pencil', 'Crayons_A', 'Crayons_B'];
  var BAYS = ['Win_Bay_A', 'Win_Bay_B', 'Win_Bay_C'];
  var TRAILS = ['TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_E'];
  var WALLS = ['Wall_Plain', 'Wall_Corner', 'Wall_Switch', 'Wall_Vent', 'Win_Open', 'Wall_Cork', 'Wall_Map', 'Wall_Clock',
    'Wall_Poster_A', 'Wall_Poster_B', 'Wall_Poster_C'].concat(BAYS);

  // ---- wall layout. Each wall side is laid out along u, which grows to the right of someone facing that wall.
  // Big decor is one piece on its centre cell reaching over plain neighbours: `a` = cells reserved each side.
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  function inGrid(grid, c, r) { return c >= 0 && r >= 0 && c < grid.w && r < grid.h; }
  function openAt(grid, c, r) { return inGrid(grid, c, r) && !wallish(grid.at(c, r)); }
  function wallAt(grid, c, r) { return inGrid(grid, c, r) && wallish(grid.at(c, r)); }
  // the room side of a wall cell, from neighbours inside the grid (grid.at() reports outside cells as wall)
  function sideOf(c, r, grid) {
    if (openAt(grid, c, r + 1)) return 'N';   // room to the south: the north wall
    if (openAt(grid, c, r - 1)) return 'S';
    if (openAt(grid, c + 1, r)) return 'W';
    if (openAt(grid, c - 1, r)) return 'E';
    return null;
  }
  // the yaw (degrees) zones.js buildWalls gives this cell's module (same rules, incl. faceOpen): outside cells count
  // as wall there, so perimeter west/east runs come out as horizontal runs (yaw 0)
  function engineYaw(c, r, horiz, grid) {
    function solid(x, y) { return wallish(grid.at(x, y)); }
    var vert = solid(c, r - 1) || solid(c, r + 1), yaw = (!horiz && vert) ? 90 : 0;
    if (yaw === 0 && !solid(c, r - 1) && solid(c, r + 1)) yaw = 180;
    if (yaw !== 0 && !solid(c - 1, r) && solid(c + 1, r)) yaw = -90;
    return yaw;
  }
  var FACING = { N: 0, S: 180, W: 90, E: -90 };   // module front (game +Z) must turn to the room
  var TURNED = { 90: ['Wall_Plain', 'Win_Open'].concat(BAYS), 270: ['Wall_Plain', 'Wall_Cork', 'Wall_Poster_A', 'Wall_Map', 'Wall_Vent'] };
  function turned(piece, side, c, r, horiz, grid) {
    var d = (((FACING[side] - engineYaw(c, r, horiz, grid)) % 360) + 360) % 360;
    return (d === 90 || d === 270) && TURNED[d].indexOf(piece) >= 0 ? piece + '_R' + d : piece;
  }
  function along(side, c, r, grid) { return side === 'N' ? c : side === 'S' ? grid.w - 1 - c : side === 'W' ? grid.h - 1 - r : r; }
  function lineLen(side, grid) { return side === 'N' || side === 'S' ? grid.w : grid.h; }
  function cellAt(side, u, c, r, grid) {
    if (side === 'N') return [u, r];
    if (side === 'S') return [grid.w - 1 - u, r];
    if (side === 'W') return [c, grid.h - 1 - u];
    return [c, u];
  }
  // the door built-in (GateFrame) covers the two wall cells either side of a gate
  function nearGate(grid, x, y) {
    for (var d = -2; d <= 2; d++) { var g = grid.at(x + d, y); if (g === 'G' || g === 'E') return true; }
    return false;
  }
  // a wall cell facing the room on this side (not a gate, not a corner, not behind the door built-in)
  function faceCell(side, u, c, r, grid) {
    var p = cellAt(side, u, c, r, grid), x = p[0], y = p[1];
    if (grid.at(x, y) !== '#' || nearGate(grid, x, y)) return false;
    var o = side === 'N' ? grid.at(x, y + 1) : side === 'S' ? grid.at(x, y - 1) : side === 'W' ? grid.at(x + 1, y) : grid.at(x - 1, y);
    return !wallish(o);
  }
  function clear(side, u, a, c, r, grid) {
    for (var k = u - a; k <= u + a; k++) if (!faceCell(side, k, c, r, grid)) return false;
    return true;
  }
  // decor slots per side: centre offset o (repeating every `every` cells), piece, reserved half-width a
  function slots(side, grid) {
    var L = lineLen(side, grid), mid = Math.floor(L / 2);
    if (side === 'E') return [{ o: 7, every: 30, p: 'Wall_Cork', a: 5 }, { o: 15, every: 30, p: 'Wall_Poster_A', a: 2 }, { o: 22, every: 30, p: 'Wall_Map', a: 4 }];
    if (side === 'S') return [{ o: 9, p: 'Wall_Cork', a: 5 }, { o: L - 9, p: 'Wall_Poster_B', a: 2 }, { o: mid + 8, p: 'Wall_Poster_C', a: 2 }];
    if (side === 'N' && hasBoard(grid)) return [{ o: mid - 18, p: 'Wall_Clock', a: 2 }, { o: 6, p: 'Wall_Poster_A', a: 2 }, { o: L - 7, p: 'Wall_Poster_B', a: 2 }];
    if (side === 'N') return [{ o: 6, p: 'Wall_Poster_C', a: 2 }, { o: mid - 9, p: 'Wall_Map', a: 4 }, { o: mid + 4, p: 'Wall_Clock', a: 2 },
      { o: mid + 14, p: 'Wall_Cork', a: 5 }, { o: L - 7, p: 'Wall_Poster_B', a: 2 }];
    return [];
  }
  // the front of the class: a zone with the chalkboard ('k') against its north wall gets the alphabet strip above it
  function hasBoard(grid) {
    if (grid._hasBoard === undefined) { grid._hasBoard = false; for (var c = 0; c < grid.w; c++) if (grid.at(c, 1) === 'k') grid._hasBoard = true; }
    return grid._hasBoard;
  }
  function decorAt(side, u, c, r, grid) {
    var S = slots(side, grid);
    for (var i = 0; i < S.length; i++) {
      var d = S[i], centre = d.every ? d.o + d.every * Math.round((u - d.o) / d.every) : d.o;
      if (Math.abs(u - centre) <= d.a && clear(side, centre, d.a, c, r, grid)) return u === centre ? d.p : 'Wall_Plain';
    }
    return null;
  }
  // the alphabet strip runs along the top of the chalkboard's (north) wall, centred, skipping the exit gate
  function letterAt(u, c, r, grid) {
    if (!hasBoard(grid)) return null;
    var a0 = Math.floor(grid.w / 2) - 13, n = 0;
    if (u < a0) return null;
    for (var k = a0; k < u; k++) if (faceCell('N', k, c, r, grid)) n++;
    return n < 26 ? 'Alpha_' + LETTERS[n] : null;
  }
  function pickWall(c, r, side, hash, grid) {
    var u = along(side, c, r, grid);
    if (side === 'W') {   // window bays: 5 cells of glass (centre piece glazes all five), 2-cell piers
      var centre = 5 + 7 * Math.round((u - 5) / 7);
      if (Math.abs(u - centre) <= 2 && clear(side, centre, 3, c, r, grid)) return u === centre ? BAYS[Math.floor(hash(centre, 17) * BAYS.length)] : 'Win_Open';
      return 'Wall_Plain';
    }
    if (side === 'N') { var L = letterAt(u, c, r, grid); if (L) return L; }
    var d = decorAt(side, u, c, r, grid);
    if (d) return d;
    // light switch just past the door built-in, the odd air vent high up
    if ((side === 'N' || side === 'S') && wallAt(grid, c + 3, r) && grid.at(c + 3, r) !== '#' && grid.at(c + 1, r) === '#' && grid.at(c + 2, r) === '#') return 'Wall_Switch';
    if (side !== 'N' && hash(c * 7 + 3, r * 11 + 5) < 0.06) return 'Wall_Vent';
    return 'Wall_Plain';
  }
  function chooseWall(c, r, horiz, corner, hash, grid) {
    if (nearGate(grid, c, r)) return null;   // inside the door built-in (GateFrame): no wall module
    // a real room corner has wall neighbours inside the grid both ways (the engine's `corner` counts outside cells)
    if ((wallAt(grid, c - 1, r) || wallAt(grid, c + 1, r)) && (wallAt(grid, c, r - 1) || wallAt(grid, c, r + 1))) return 'Wall_Corner';
    var side = sideOf(c, r, grid);
    if (!side) return 'Wall_Plain';
    return turned(pickWall(c, r, side, hash, grid), side, c, r, horiz, grid);
  }

  IB.registerTheme({
    id: 'classroom', name: 'Classroom', family: 'kit-classroom', prefix: 'KIT_CLASSROOM_',
    palette: ['#2F6B4F', '#EDBB68', '#BFE6D3', '#E9E3D4'],
    env: {
      sky: null, clear: '#FFF7EA', clouds: false,
      fog: { color: '#FFF4E2', near: 38, far: 135 },
      sun: [0.42, 0.82, 0.38],
      // the ceiling faces down (darkest toon band): white keeps it a soft lavender-grey; troffers every 12 m
      ceiling: { height: 16.5, color: '#FFFFFF', light: 'LightPanel', every: 12 }
    },
    // light linoleum: 2 m tiles (a real 30 cm tile at x6); crossing grout lines sit at different heights
    floor: { color: '#E9E3D4', trail: '#E3DCCB', lines: [
      { dir: 'x', every: 2, width: 0.05, color: '#D7CFBE', y: 0.008 },
      { dir: 'z', every: 2, width: 0.05, color: '#D7CFBE', y: 0.012 }] },
    wall: { height: 16.5, roof: '#FFF6E3', faceOpen: true, choose: chooseWall },
    symbols: {
      // student desk (north part, open to the chair side) + its chair: run under the 4.45 m top
      'D': { size: [6, 7], pieces: DESKS, kind: 'wall' },
      'n': { size: [3, 3], pieces: ['Chair'], flip: true, kind: 'wall' },
      'N': { size: [5, 3], pieces: ['Chair_Fallen'], flip: true, kind: 'cover' },
      '=': { pieces: ['BooksA', 'BooksB'], rotate: 'run', alternate: true, kind: 'cover' },
      'B': { size: [2, 2], pieces: STACKS, flip: true, kind: 'cover' },
      'c': { pieces: BLOCKS, h: 0.96, rotate: 'random90', stack: { piece: 'Block_S', chance: 0.25, h: 0.96 }, kind: 'cover' },
      'K': { size: [3, 2], pieces: BAGS, flip: true, kind: 'cover' },
      'w': { size: [2, 2], pieces: ['Bin'], kind: 'cover' },
      'L': { size: [6, 2], pieces: ['Bookcase'], kind: 'cover' },     // opens to -Y: north walls (rows), west walls (columns)
      'J': { size: [6, 2], pieces: ['BookcaseB'], kind: 'cover' },    // opens to +Y: south walls (rows), east walls (columns)
      'O': { size: [3, 3], pieces: BEANS, flip: true, kind: 'cover' },
      'R': { size: [12, 10], pieces: ['Rug'], collide: false },
      'p': { size: [2, 2], pieces: PAPERS, flip: true, collide: false },
      'l': { size: [3, 1], pieces: FLOORSTUFF, flip: true, kind: 'cover', y: 0.035 },
      'e': { pieces: ['Eraser'], rotate: 'random90', kind: 'cover' },
      'T': { size: [10, 5], pieces: ['Landmark_TeacherDesk'], kind: 'wall' },
      'Q': { size: [4, 4], pieces: ['Landmark_Globe'], kind: 'wall' },
      'k': { size: [22, 1], pieces: ['Landmark_Chalkboard'], kind: 'wall' }
    },
    // the door is a floor-to-ceiling library built-in (covers the wall cells either side, closes the trail ends);
    // the trail is a library aisle of mixed bookcase slices
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05, dress: ['GateBooks'] },
    trail: { wall: 'TrailWall', height: 16.5, variants: TRAILS },
    hatch: 'Hatch', stand: 'Eraser',
    backdrop: null,
    budget: { prop: 2500, landmark: 4000, total: 76000 },
    allPieces: function () {
      var letters = LETTERS.split('').map(function (L) { return 'Alpha_' + L; });
      var turnedPieces = TURNED[90].map(function (n) { return n + '_R90'; }).concat(TURNED[270].map(function (n) { return n + '_R270'; }));
      return WALLS.concat(turnedPieces, letters, DESKS, BLOCKS, ['Block_S'], STACKS, BAGS, BEANS, PAPERS, FLOORSTUFF,
        ['Chair', 'Chair_Fallen', 'BooksA', 'BooksB', 'Bin', 'Bookcase', 'BookcaseB', 'Rug', 'Eraser',
          'Landmark_TeacherDesk', 'Landmark_Globe', 'Landmark_Chalkboard', 'GateFrame', 'GateBooks', 'GateShutter', 'TrailWall',
          'Hatch', 'LightPanel'], TRAILS);
    },
    levels: {
      classroom: {
        name: 'Pop Quiz',
        intro: 'You are pocket-sized now. Duck under the desks.',
        zones: [
          { map: 'classroom_desks', waves: [
            [['crawler', 9], ['gunner', 2]],
            [['crawler', 8], ['gunner', 3], ['bomber', 2]],
            [['crawler', 6], ['drone', 2], ['bomber', 2]]] },
          { map: 'classroom_reading', waves: [
            [['crawler', 8], ['drone', 2]],
            [['bomber', 3], ['crawler', 6]],
            [['gunner', 3], ['crawler', 4], ['blader', 1]],
            [['drone', 2], ['crawler', 4]]] },
          { map: 'classroom_front', waves: [
            [['crawler', 8], ['gunner', 3]],
            [['drone', 3], ['bomber', 3], ['crawler', 4]],
            [['gunner', 4], ['crawler', 5]],
            [['crawler', 2], ['bomber', 2], ['drone', 2], ['blader', 1]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
