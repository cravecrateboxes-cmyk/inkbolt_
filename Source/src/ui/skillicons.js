/* INKBOLT skill icons: one hand-inked comic illustration per IB.SKILLS icon key, as inline SVG (64 x 64 view box).
   Every piece has a 3 px ink outline, a flat base tone, a shadow tone on the side away from the top-left light and
   a paper highlight. Locked skills are greyed by CSS (filter), so the art itself is always in full colour.
     IB.SkillIcons.svg(key, cls)  -> '<svg ...>' markup (unknown keys get the burst) */
(function (IB) {
  'use strict';
  var K = '#15121C';                                      // ink
  var O = ' stroke="' + K + '" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"';
  var O2 = ' stroke="' + K + '" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"';
  var HL = ' fill="none" stroke="#FFFDF7" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"';
  function p(d, fill, extra) { return '<path d="' + d + '" fill="' + fill + '"' + (extra || '') + '/>'; }
  function ink(d, w) { return '<path d="' + d + '" fill="none" stroke="' + K + '" stroke-width="' + (w || 3) + '" stroke-linecap="round" stroke-linejoin="round"/>'; }
  function hl(d, op) { return '<path d="' + d + '"' + HL + (op ? ' opacity="' + op + '"' : '') + '/>'; }
  function c(x, y, r, fill, extra) { return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + fill + '"' + (extra || '') + '/>'; }
  // a brass cartridge standing at (x, y) (base centre), height h, tilted by deg
  function round(x, y, h, deg) {
    var w = h * 0.36, t = h * 0.42;
    return '<g transform="translate(' + x + ' ' + y + ') rotate(' + deg + ')">' +
      p('M' + (-w / 2) + ' 0V' + (-h + t) + 'H' + (w / 2) + 'V0Z', '#FFC23A', O2) +
      p('M' + (w / 2 - w * 0.34) + ' -1V' + (-h + t + 1) + 'H' + (w / 2 - 1) + 'V-1Z', '#D98A12') +
      p('M' + (-w / 2) + ' ' + (-h + t) + 'C' + (-w / 2) + ' ' + (-h + t * 0.35) + ' ' + (-w * 0.2) + ' ' + (-h) + ' 0 ' + (-h) + 'C' + (w * 0.2) + ' ' + (-h) + ' ' + (w / 2) + ' ' + (-h + t * 0.35) + ' ' + (w / 2) + ' ' + (-h + t) + 'Z', '#E8743B', O2) +
      '<path d="M' + (-w * 0.18) + ' -3V' + (-h + t + 2) + '" stroke="#FFF1D6" stroke-width="1.8" stroke-linecap="round"/></g>';
  }

  var ART = {
    // Boom: a ribbed frag can with a pulled pin and lever, a rocket blasting off with a flame, and smoke puffs
    boom: function () {
      return '<g transform="translate(45 27) rotate(-42) scale(1.15)">' +
          p('M-22 -2.5 L-30 -6 L-27 0 L-30 6 L-22 2.5Z', '#FFB21E', O2) + p('M-21 -1 L-26 0 L-21 1Z', '#FFF1A8') +
          p('M-13 -4.5H12V4.5H-13Z', '#E9EEF7', O2) + hl('M-9 -2.2H7', .9) +
          p('M12 -4.5 L19 0 L12 4.5Z', '#F0443A', O2) +
          p('M-13 -4.5 L-19 -10 L-17 -3Z', '#F0443A', O2) + p('M-13 4.5 L-19 10 L-17 3Z', '#F0443A', O2) +
          c(-2, 0, 2.6, '#3E86D8', O2) + c(-3, -1, 0.9, '#D8EEFF') +
        '</g>' +
        c(48, 46, 4, '#E9EEF7', O2) + c(55, 52, 3, '#E9EEF7', O2) + c(41, 53, 2.4, '#E9EEF7', O2) +
        p('M24 21C13 21 7 29 7 39S15 57 25 57S42 48 42 38S35 21 24 21Z', '#6E8B3D', O) +
        p('M36 29C40 33 41 38 40 43S35 53 27 55C33 52 35 46 35 40S34 33 36 29Z', '#44592A') +
        p('M12 36C14 31 18 28 24 27', 'none', HL) +
        p('M11 45C16 40 20 39 27 40', 'none', ' stroke="#A9C96A" stroke-width="2.4" stroke-linecap="round"') +
        p('M14 35Q24 29 34 35', 'none', ' stroke="#44592A" stroke-width="2.2" stroke-linecap="round"') +
        p('M15 46Q24 40 34 46', 'none', ' stroke="#44592A" stroke-width="2.2" stroke-linecap="round"') +
        p('M20 21H29V14H20Z', '#3B4A3A', O2) + p('M22 15.5H27', 'none', ' stroke="#8A94A8" stroke-width="1.6"') +
        p('M28 17C33 11 39 10 43 12L43 16C39 14 34 15 30 21Z', '#C8D0DE', O2) +
        ink('M29 11a4 4 0 1 1 1 5', 2.2) +
        p('M9 10l2 4 4-1-2 4 3 3-4 0-1 4-2-4-4 1 2-4-3-3 4 0z', '#FFD23F', O2) +
        c(60, 6, 1.8, '#FFD23F', O2);
    },
    // Dart: a scope with a glass lens, reticle and mount screws, and a dart striking it
    dart: function () {
      return c(30, 30, 21, '#2E3850', O) + c(30, 30, 17, '#5C6B8A', O2) +
        c(30, 10, 2, '#C8D0DE', O2) + c(30, 50, 2, '#C8D0DE', O2) + c(10, 30, 2, '#C8D0DE', O2) + c(50, 30, 2, '#C8D0DE', O2) +
        c(30, 30, 13, '#CFEFFF', O2) +
        p('M30 17A13 13 0 0 1 43 30L36 30A6 6 0 0 0 30 24Z', '#8FD0F2') +
        p('M20 26A11 11 0 0 1 29 19', 'none', HL.replace('stroke-width="2.6"', 'stroke-width="2.6"')) +
        p('M26 30H34M30 26V34', 'none', ' stroke="#2E3850" stroke-width="1.8" stroke-linecap="round"') +
        ink('M30 19V41M19 30H41', 1.8) +
        c(30, 30, 2.8, '#F0443A', O2) + c(29, 29, 0.9, '#FFD2C8') +
        '<g transform="translate(42 42) rotate(42) scale(1.1)">' +
          p('M4 -2.6H17V2.6H4Z', '#C8D0DE', O2) + hl('M6 -1.2H15', .9) +
          p('M17 -2.6 L22 -6 L21 -1Z', '#FFB21E', O2) + p('M17 2.6 L22 6 L21 1Z', '#FFB21E', O2) +
          p('M0 0 L7 -4 L6 0 L7 4Z', '#E9EEF7', O2) +
        '</g>' +
        p('M55 27l2 4 4-1-2 4 3 3-4 0-1 4-2-4-4 1 2-4-3-3 4 0z', '#FFD23F', O2) +
        c(58, 40, 1.8, '#FFD23F', O2) + c(4, 56, 2.4, '#8FD0F2', O2);
    },
    // Surge Up: two speed chevrons with sparks
    surge: function () {
      return p('M10 14L30 32L10 50L16 56L38 32L16 8Z', '#2FB8FF', O) +
        p('M12 17L26 32L12 47', 'none', HL.replace('stroke-width="2.6"', 'stroke-width="2.2"')) +
        p('M30 14L50 32L30 50L36 56L58 32L36 8Z', '#FFD23F', O) +
        p('M32 17L46 32L32 47', 'none', HL.replace('stroke-width="2.6"', 'stroke-width="2.2"')) +
        p('M52 6l2 4 4-1-2 4 3 3-4 0-1 4-2-4-4 1 2-4-3-3 4 0z', '#FFFDF7', O2) +
        c(6, 58, 2.6, '#FFD23F', O2);
    },
    // Overload: a fat curved magazine, rounds spilling out of the top
    mag: function () {
      return round(25, 25, 21, -22) + round(39, 25, 21, 22) + round(32, 23, 22, 0) +
        p('M18 24H46L49 60H23Z', '#5C6B8A', O) +
        p('M40 27H45.5L48 57H42.5Z', '#3E4963') +
        p('M18 24H46V30H18Z', '#8A9AB8', O2) +
        p('M26 37H40M26.6 44H40.8M27.2 51H41.6', 'none', ' stroke="' + K + '" stroke-width="2.4" stroke-linecap="round"') +
        hl('M22.5 34L24 55', '.85') +
        p('M53 6l2 5 5-2-2 5 5 2-5 2 2 5-5-2-2 5-2-5-5 2 2-5-5-2 5-2-2-5 5 2z', '#FFD23F', O2) +
        p('M8 10l4 4M4 20l5 0', 'none', ' stroke="' + K + '" stroke-width="2.6" stroke-linecap="round"');
    },
    // Heavy Ink: a heavy ink drop with a round sinking into it, splash beads
    drop: function () {
      return p('M32 6C40 19 50 29 50 41A18 18 0 0 1 14 41C14 29 24 19 32 6Z', '#3B4FC8', O) +
        p('M44 30C48 35 50 38 50 41A18 18 0 0 1 32 59C42 55 47 46 44 30Z', '#28339A') +
        hl('M21 38C21 32 24 26 27 21', '.9') + c(21, 44, 1.9, '#FFFDF7') +
        round(32, 27, 26, 180) +
        p('M24 27C27 25 37 25 40 27', 'none', ' stroke="#8EA0FF" stroke-width="2.4" stroke-linecap="round"') +
        c(8, 54, 3, '#3B4FC8', O2) + c(56, 52, 2.4, '#3B4FC8', O2) + c(53, 14, 2.2, '#3B4FC8', O2) + c(11, 16, 1.8, '#3B4FC8', O2);
    },
    // Stream: a round punching through a steel plate, speed streaks, a second target behind
    pierce: function () {
      return p('M43 8L54 12V54L43 58Z', '#9AA6BE', O) + p('M49 10.5L54 12V54L49 56Z', '#6B7792') +
        p('M10 28H30V38H10Z', 'none') +
        ink('M4 24H16M2 33H14M4 42H16', 3) +
        p('M18 27H34L44 33L34 39H18Z', '#FFC23A', O) + p('M34 27L44 33L34 39Z', '#E8743B', O2) + p('M18 35H34V39H18Z', '#D98A12') +
        hl('M21 30H31', '.9') +
        p('M44 25l3 8-3 8 6-5 6 6-2-9 6-4-8 0z', '#FFFDF7', O2) +
        p('M40 22l2-6 3 6M40 44l2 6 3-6', 'none', ' stroke="' + K + '" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"');
    },
    // Electrify: a chunky lightning bolt with sparks
    bolt: function () {
      return p('M37 3L13 36H29L23 61L51 24H34L42 3Z', '#FFD23F', O) +
        p('M42 3L34 24H51L47 29H30Z', '#F29A1D') + p('M29 36L23 61L30 50L33 36Z', '#F29A1D') +
        hl('M34 9L22 30', '.95') +
        p('M7 14l4 3M5 24l5-1M55 40l5 1M52 50l4 4M56 31l5-3', 'none', ' stroke="#6CC8FF" stroke-width="3" stroke-linecap="round"') +
        ink('M7 14l4 3M5 24l5-1M55 40l5 1M52 50l4 4M56 31l5-3', 1.2);
    },
    // Rapid: a speedo dial pinned in the red
    gauge: function () {
      return p('M6 46A26 26 0 0 1 58 46Z', '#FFF1D6', O) +
        p('M44 25A26 26 0 0 1 58 46H47A15 15 0 0 0 40 33Z', '#F0443A') +
        p('M6 46A26 26 0 0 1 58 46', 'none', O) +
        ink('M13 39L17 41M18 28L21 31M30 22V26M42 25L40 29', 2.6) +
        p('M30 46L51 29L35 49Z', K) + c(32, 46, 5.5, '#5C6B8A', O2) + c(30.5, 44.5, 1.6, '#FFFDF7') +
        p('M4 46H60V53H4Z', '#5C6B8A', O) + p('M4 50H60V53H4Z', '#3E4963') +
        hl('M12 34C15 28 21 23 27 21', '.8') +
        p('M52 12l3-6M58 18l5-3M45 9l0-6', 'none', ' stroke="' + K + '" stroke-width="3" stroke-linecap="round"');
    },
    // Hazard: a bubbling acid puddle with a drip
    acid: function () {
      return p('M6 48C6 42 15 39 22 40C26 34 40 34 44 39C52 37 60 42 58 48C57 55 44 57 32 56C18 57 7 55 6 48Z', '#8BEA4F', O) +
        p('M10 51C18 54 44 55 55 50C54 54 44 56 32 56C20 56 12 55 10 51Z', '#3E9B2E') +
        hl('M14 45C17 43 21 43 24 44', '.85') +
        c(36, 27, 6, '#8BEA4F', O) + c(34, 25, 1.8, '#FFFDF7') +
        c(22, 21, 4, '#8BEA4F', O2) + c(46, 15, 3.4, '#8BEA4F', O2) + c(30, 10, 2.4, '#8BEA4F', O2) +
        p('M44 44c0 4-2 6-4 6s-4-2-4-6', '#3E9B2E', O2) +
        p('M26 45c0 0 2 3 0 4', 'none', ' stroke="#D6FF9E" stroke-width="2.4" stroke-linecap="round"');
    },
    // Ricochet: a round bouncing off a brick wall, spark at the hit
    ricochet: function () {
      return p('M3 6H17V60H3Z', '#E8743B', O) + p('M12 6H17V60H12Z', '#B8552A') +
        ink('M3 18H17M3 31H17M3 44H17M10 6V18M8 31V44M12 18V31M6 44V60', 2.2) +
        '<path d="M17 36L33 52L46 22" fill="none" stroke="#FFFDF7" stroke-width="3" stroke-dasharray="5 4" stroke-linecap="round"/>' +
        p('M17 36l6-7-1 6 7-2-5 5 6 3-7 0 2 6-5-4-3 6z', '#FFD23F', O2) +
        '<g transform="translate(49 15) rotate(-62)">' + p('M-6 -5H6L13 0L6 5H-6Z', '#FFC23A', O2) + p('M6 -5L13 0L6 5Z', '#E8743B', O2) + '</g>' +
        ink('M54 31l7 3M51 37l5 6', 2.6);
    },
    // Healthy: a comic heart with a health cross and a shine
    heart: function () {
      return p('M32 57L9 34C2 27 3 15 12 10C20 6 27 10 32 17C37 10 44 6 52 10C61 15 62 27 55 34Z', '#F0443A', O) +
        p('M55 34L32 57L36 45C47 38 54 29 55 18C60 23 59 30 55 34Z', '#A82A23') +
        p('M27 22H37V29H44V39H37V46H27V39H20V29H27Z', '#FFFDF7', O2) +
        hl('M11 22C11 17 14 14 18 13', '.95');
    },
    // Stamina: a winged sneaker with speed lines
    run: function () {
      return ink('M2 28H12M4 37H13M2 46H10', 3) +
        p('M24 14C30 12 38 14 42 18L44 26C42 28 40 32 40 34C48 36 56 38 59 43C61 47 59 52 55 52H20C16 52 15 48 16 44Z', '#F0443A', O) +
        p('M16 44H59C60 48 58 52 55 52H20C16 52 15 48 16 44Z', '#FFFDF7', O) +
        p('M40 34C48 36 56 38 59 43L56 44C53 40 46 38 38 37Z', '#A82A23') +
        ink('M30 26L36 24M31 32L38 30', 2.4) +
        p('M24 14C20 8 14 6 8 8C12 10 14 12 15 14C10 13 7 15 5 18C11 18 15 19 18 22Z', '#FFFDF7', O2) +
        hl('M22 20C21 27 21 34 20 40', '.8');
    },
    // Hydrate: a water drop with a bolt inside
    water: function () {
      return p('M32 5C41 19 51 29 51 41A19 19 0 0 1 13 41C13 29 23 19 32 5Z', '#4AA8FF', O) +
        p('M45 30C49 35 51 38 51 41A19 19 0 0 1 32 60C43 55 48 46 45 30Z', '#2563C9') +
        p('M34 24L23 41H31L27 54L41 35H33L38 24Z', '#FFD23F', O2) +
        hl('M20 36C20 31 23 26 26 22', '.95') + c(19.5, 42, 1.8, '#FFFDF7') +
        ink('M8 20l4 2M56 18l-4 3', 2.6);
    },
    // Undercover: a spy fedora over a domino mask, a fading dotted trail
    cloak: function () {
      return p('M8 30C14 31 22 32 32 32C42 32 50 31 56 30C55 34 46 37 32 37C18 37 9 34 8 30Z', '#3A3550', O) +
        p('M17 30C17 20 20 10 26 10C29 10 30 13 32 13C34 13 35 10 38 10C44 10 47 20 47 30C40 32 24 32 17 30Z', '#4A4164', O) +
        p('M17 26C25 28 39 28 47 26V30C39 32 25 32 17 30Z', '#F0443A', O2) +
        p('M38 10C44 10 47 20 47 26C44 26 43 18 38 10Z', '#2B2340') +
        hl('M23 14C21 18 20 22 20 25', '.7') +
        p('M9 42C14 39 22 39 27 42C29 43 35 43 37 42C42 39 50 39 55 42C57 48 54 53 47 53C41 53 38 50 32 49C26 50 23 53 17 53C10 53 7 48 9 42Z', '#2B2A33', O) +
        hl('M14 45C20 43 26 44 30 46', '.35') +
        '<g fill="#A6DBE6"><circle cx="5" cy="58" r="1.4"/><circle cx="12" cy="59" r="1.8"/><circle cx="52" cy="59" r="1.8"/><circle cx="59" cy="58" r="1.4"/></g>';
    },
    // Tank: a riveted steel shield with a hazard stripe and a dent
    armor: function () {
      return p('M32 4L55 12V32C55 46 45 55 32 60C19 55 9 46 9 32V12Z', '#8E9BB5', O) +
        p('M32 4L55 12V32C55 46 45 55 32 60Z', '#66728E') +
        p('M14 24L50 24V33L14 33Z', '#FFD23F', O2) +
        '<path d="M18 24L14 29M27 24L20 33M36 24L29 33M45 24L38 33M50 26L47 33" stroke="' + K + '" stroke-width="3"/>' +
        c(16, 15, 2, K) + c(48, 15, 2, K) + c(16, 42, 2, K) + c(48, 42, 2, K) + c(32, 51, 2, K) +
        p('M34 40l4 3-2 3 4 2', 'none', ' stroke="' + K + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"') +
        hl('M14 15V22M32 9L19 13', '.9');
    },
    // Fast Fingers: chasing reload arrows round a magazine, speed ticks
    reload: function () {
      var top = 'M12 32A20 20 0 0 1 49 24', bot = 'M52 36A20 20 0 0 1 15 44';
      return '<path d="' + top + '" fill="none" stroke="' + K + '" stroke-width="11" stroke-linecap="round"/><path d="' + top + '" fill="none" stroke="#FF8A3D" stroke-width="5.4" stroke-linecap="round"/>' +
        '<path d="' + bot + '" fill="none" stroke="' + K + '" stroke-width="11" stroke-linecap="round"/><path d="' + bot + '" fill="none" stroke="#FF8A3D" stroke-width="5.4" stroke-linecap="round"/>' +
        p('M41 21L59 19L53 37Z', '#FF8A3D', O) + p('M53 37L59 19L55 20L51 31Z', '#C25A1C') +
        p('M23 47L5 45L11 27Z', '#FF8A3D', O) + p('M11 27L5 45L9 44L13 33Z', '#C25A1C') +
        hl('M18 22C21 19 25 17 29 16', '.9') +
        p('M26 27H38L39 45H27Z', '#5C6B8A', O2) + p('M34 28H38L39 44H34.5Z', '#3E4963') +
        p('M27 27C27 22 30 20 32 20C34 20 37 22 37 27Z', '#FFC23A', O2) +
        ink('M44 50l4 5M50 46l6 3', 2.6);
    },
    // Handy Helpers: a turned (ally) Crawler, no face: a teal tin can on spring legs with its gold core dome and amber
    // antenna light, an ally chevron painted on its side, a wrench over its shoulder and a little spark of help
    helper: function () {
      var leg = function (x, k) {
        return p('M' + x + ' 48l' + (-3 * k) + ' 3l' + (6 * k) + ' 2.5l' + (-6 * k) + ' 2.5l' + (3 * k) + ' 2', 'none', ' stroke="' + K + '" stroke-width="5.4" stroke-linecap="round" stroke-linejoin="round"') +
          p('M' + x + ' 48l' + (-3 * k) + ' 3l' + (6 * k) + ' 2.5l' + (-6 * k) + ' 2.5l' + (3 * k) + ' 2', 'none', ' stroke="#9AA6BE" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"') +
          p('M' + (x - 4) + ' 60.5C' + (x - 4) + ' 58 ' + (x + 4) + ' 58 ' + (x + 4) + ' 60.5Z', '#5C6B8A', O2);
      };
      return p('M37 33L52 13', 'none', ' stroke="' + K + '" stroke-width="8" stroke-linecap="round"') +
        p('M37 33L52 13', 'none', ' stroke="#9AA6BE" stroke-width="4" stroke-linecap="round"') +
        p('M49 8C52 3 59 3 61 8L56 10L57 15L52 16C49 13 48 11 49 8Z', '#9AA6BE', O2) +
        leg(17, 1) + leg(26, -1) + leg(38, 1) + leg(47, -1) +
        ink('M22 18V8', 3) + c(22, 6.5, 3.6, '#FFB21E', O2) + c(21, 5.4, 1.1, '#FFFDF7') +
        p('M22 22C22 15 42 15 42 22Z', '#FFC23A', O) + p('M35 16.4C39 17.4 42 19.4 42 22H36Z', '#D98A12') + hl('M26 19.5C27.5 18.5 29.5 18 31.5 18', '.9') +
        p('M10 22H54V44C54 47 52 49 49 49H15C12 49 10 47 10 44Z', '#12C7B6', O) +
        p('M45 23.5H52.5V44C52.5 46 51 47.5 49 47.5H45Z', '#0B8F83') +
        p('M10 22H54V28H10Z', '#3FDECF', O2) +
        p('M23 44L32 35.5L41 44L41 38.5L32 30L23 38.5Z', '#FFFDF7', O2) +
        hl('M14.5 32V43', '.85') +
        p('M5 12l1.6 3.4 3.4 1.6-3.4 1.6L5 22l-1.6-3.4L0 17l3.4-1.6z', '#FFD23F', O2) +
        ink('M58 30l4-2M58 36l5 1', 2.4);
    },
    // Chain Reaction: a big comic blast and two smaller ones going off from it
    burst: function () {
      return p('M30 6L35 20L48 12L44 26L59 27L47 36L56 47L42 45L40 59L31 49L21 58L21 44L7 46L16 35L5 27L19 25L15 11L27 19Z', '#F0443A', O) +
        p('M30 15L34 25L43 20L40 30L50 31L41 37L47 44L38 42L36 51L30 44L23 50L24 41L15 42L21 35L14 29L23 28L21 19L28 24Z', '#FF8A3D') +
        p('M30 24L33 30L38 28L36 34L41 36L35 38L36 43L31 40L27 44L27 39L22 38L26 35L23 31L28 31Z', '#FFD23F') +
        c(30, 34, 3, '#FFFDF7') +
        p('M53 6l2 4 4-1-2 4 3 3-4 0-1 4-2-4-4 1 2-4-3-3 4 0z', '#FFD23F', O2) +
        p('M8 54l2 4 4-1-2 4 3 3-4 0-1 4-2-4-4 1 2-4-3-3 4 0z', '#FFD23F', O2) +
        c(58, 58, 3, '#4A4164', O2) + c(4, 8, 2.4, '#4A4164', O2);
    }
  };
  var cache = {};
  IB.SkillIcons = {
    keys: Object.keys(ART),
    svg: function (key, cls) {
      var k = ART[key] ? key : 'burst';
      if (!cache[k]) cache[k] = ART[k]();
      return '<svg class="' + (cls || 'skic') + '" viewBox="0 0 64 64" aria-hidden="true">' + cache[k] + '</svg>';
    }
  };
})(window.IB = window.IB || {});
