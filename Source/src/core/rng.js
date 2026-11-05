/* INKBOLT - seeded random helpers (pure, no DOM). */
(function (IB) {
  'use strict';

  // Classic mulberry32: fast 32-bit seeded PRNG returning floats in [0, 1).
  function mulberry32(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function pick(rng, arr) {
    if (!arr || !arr.length) return undefined;
    return arr[Math.floor(rng() * arr.length)];
  }

  // Float in [a, b).
  function range(rng, a, b) {
    return a + (b - a) * rng();
  }

  // Integer in [a, b] inclusive.
  function int(rng, a, b) {
    return a + Math.floor(rng() * (b - a + 1));
  }

  // Fisher-Yates on a copy; the input is not modified.
  function shuffle(rng, arr) {
    var out = arr.slice();
    for (var i = out.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var t = out[i]; out[i] = out[j]; out[j] = t;
    }
    return out;
  }

  IB.RNG = { mulberry32: mulberry32, pick: pick, range: range, int: int, shuffle: shuffle };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
