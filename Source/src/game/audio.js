/* INKBOLT audio: every SFX synthesised at load into AudioBuffers (no files, no music).
   Master bus with compressor, 24-voice cap (oldest stolen), equal-power stereo pan, distance gain to 0 at 40 m. */
(function (IB) {
  'use strict';
  var A = IB.Audio = { ctx: null, bufs: {}, voices: [], enabled: true, maxVoices: 24, ready: false, duck: 1, gemChain: 0, gemT: 0 };
  var SR = 44100;

  function noise(len) { var a = new Float32Array(len); for (var i = 0; i < len; i++) a[i] = Math.random() * 2 - 1; return a; }
  // simple one-pole filters
  function lowpass(a, fc) { var y = 0, k = 1 - Math.exp(-2 * Math.PI * fc / SR); for (var i = 0; i < a.length; i++) { y += k * (a[i] - y); a[i] = y; } return a; }
  function highpass(a, fc) { var y = 0, x0 = 0, k = Math.exp(-2 * Math.PI * fc / SR); for (var i = 0; i < a.length; i++) { var x = a[i]; y = k * (y + x - x0); x0 = x; a[i] = y; } return a; }
  function band(a, fc, q) { return highpass(lowpass(a, fc * (1 + 1 / q)), fc / (1 + 1 / q)); }
  function env(a, att, dec, curve) { var n = a.length, at = Math.max(1, att * SR); for (var i = 0; i < n; i++) { var e = i < at ? i / at : Math.pow(Math.max(0, 1 - (i - at) / Math.max(1, dec * SR)), curve || 2); a[i] *= e; } return a; }
  function mix(dst, src, gain, offset) { offset = Math.floor((offset || 0) * SR); for (var i = 0; i < src.length && i + offset < dst.length; i++) dst[i + offset] += src[i] * gain; return dst; }
  function tone(len, f0, f1, type) { var a = new Float32Array(len), ph = 0; for (var i = 0; i < len; i++) { var f = f0 + (f1 - f0) * i / len; ph += 2 * Math.PI * f / SR; a[i] = type === 'sq' ? (Math.sin(ph) > 0 ? 1 : -1) : Math.sin(ph); } return a; }
  function len(s) { return Math.floor(s * SR); }
  function norm(a, peak) { var m = 0; for (var i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i])); var g = m > 0 ? peak / m : 1; for (i = 0; i < a.length; i++) a[i] *= g; return a; }
  function click(dur) { return env(highpass(noise(len(dur)), 3000), 0.0005, dur, 3); }

  var RECIPES = {
    // Pip: click transient, 2.4 kHz noise snap, short bright tail
    pip: function () { var o = new Float32Array(len(0.22)); mix(o, click(0.005), 0.9); mix(o, env(band(noise(len(0.08)), 2400, 1.5), 0.001, 0.07, 2), 1.2); mix(o, env(highpass(noise(len(0.2)), 4000), 0.002, 0.18, 3), 0.25); mix(o, env(tone(len(0.05), 180, 90), 0.001, 0.05, 2), 0.5); return norm(o, 0.8); },
    // Buzz: fast buzz noise, low rattle, casing ticks
    buzz: function () { var o = new Float32Array(len(0.14)); mix(o, click(0.004), 0.7); mix(o, env(band(noise(len(0.06)), 1600, 1.2), 0.001, 0.05, 2), 1.0); mix(o, env(lowpass(noise(len(0.09)), 300), 0.002, 0.08, 2), 0.8); mix(o, env(band(noise(len(0.01)), 6000, 3), 0.0005, 0.01, 2), 0.3, 0.09); return norm(o, 0.7); },
    gun: function () { var o = new Float32Array(len(0.3)); mix(o, click(0.005), 0.8); mix(o, env(band(noise(len(0.12)), 1200, 1), 0.001, 0.11, 2), 1); mix(o, env(tone(len(0.12), 120, 50), 0.001, 0.12, 2), 0.7); return norm(o, 0.85); },
    dry: function () { return norm(env(band(noise(len(0.03)), 3500, 4), 0.0005, 0.03, 3), 0.4); },
    magOut: function () { var o = new Float32Array(len(0.12)); mix(o, env(band(noise(len(0.05)), 2200, 3), 0.0005, 0.04, 3), 1); mix(o, env(tone(len(0.06), 900, 700), 0.0005, 0.05, 3), 0.3); return norm(o, 0.45); },
    magIn: function () { var o = new Float32Array(len(0.12)); mix(o, env(band(noise(len(0.04)), 1500, 2), 0.0005, 0.035, 3), 1); mix(o, env(tone(len(0.05), 600, 500), 0.0005, 0.04, 3), 0.4); return norm(o, 0.55); },
    slide: function () { var o = new Float32Array(len(0.16)); mix(o, env(band(noise(len(0.05)), 2800, 2), 0.001, 0.05, 2), 1); mix(o, env(band(noise(len(0.05)), 1800, 2), 0.0005, 0.04, 3), 1, 0.07); return norm(o, 0.5); },
    draw: function () { return norm(env(band(noise(len(0.08)), 2000, 1.5), 0.01, 0.07, 2), 0.25); },
    hit: function () { var o = new Float32Array(len(0.07)); mix(o, env(band(noise(len(0.06)), 3200, 3), 0.0005, 0.05, 3), 1); mix(o, env(tone(len(0.06), 1400, 1100, 'sq'), 0.0005, 0.04, 3), 0.15); return norm(o, 0.45); },
    core: function () { var o = new Float32Array(len(0.1)); mix(o, env(band(noise(len(0.08)), 4500, 3), 0.0005, 0.07, 3), 1); mix(o, env(tone(len(0.09), 2400, 2000), 0.0005, 0.08, 3), 0.25); return norm(o, 0.5); },
    // robot death: can crunch + bolt rattle
    crunch: function () { var o = new Float32Array(len(0.5)); mix(o, env(band(noise(len(0.18)), 900, 0.8), 0.001, 0.16, 1.5), 1); for (var i = 0; i < 5; i++) mix(o, env(band(noise(len(0.03)), 3000 + i * 500, 4), 0.0005, 0.025, 3), 0.5, 0.12 + i * 0.06 + Math.random() * 0.03); mix(o, env(tone(len(0.12), 220, 110), 0.001, 0.12, 2), 0.4); return norm(o, 0.8); },
    bite: function () { var o = new Float32Array(len(0.12)); mix(o, env(band(noise(len(0.05)), 2600, 2), 0.0005, 0.05, 3), 1); mix(o, env(band(noise(len(0.05)), 2000, 2), 0.0005, 0.05, 3), 1, 0.05); return norm(o, 0.6); },
    hurt: function () { var o = new Float32Array(len(0.25)); mix(o, env(lowpass(noise(len(0.2)), 400), 0.002, 0.2, 2), 1); mix(o, env(tone(len(0.15), 140, 70), 0.002, 0.15, 2), 0.6); return norm(o, 0.8); },
    hop: function () { var o = new Float32Array(len(0.18)); mix(o, env(band(noise(len(0.1)), 1300, 2), 0.002, 0.08, 2), 1); mix(o, env(band(noise(len(0.04)), 2600, 3), 0.0005, 0.03, 3), 0.6, 0.1); return norm(o, 0.45); },
    clank: function () { var o = env(band(noise(len(0.05)), 2400, 4), 0.0005, 0.04, 3); return norm(o, 0.25); },
    windup: function () { var o = new Float32Array(len(0.32)); var t = env(tone(len(0.3), 500, 1400, 'sq'), 0.01, 0.3, 1); lowpass(t, 2500); mix(o, t, 0.4); mix(o, env(highpass(noise(len(0.3)), 3000), 0.02, 0.28, 1), 0.3); return norm(o, 0.35); },
    // gate: heavy shutter roll + latch clunk
    gate: function () { var o = new Float32Array(len(1.4)); var r = lowpass(noise(len(1.2)), 500); for (var i = 0; i < r.length; i++) r[i] *= (0.6 + 0.4 * Math.sin(i / SR * 2 * Math.PI * 22)) * Math.min(1, i / (0.08 * SR)) * Math.max(0, 1 - i / r.length); mix(o, r, 1); mix(o, env(band(noise(len(0.12)), 700, 1), 0.001, 0.11, 2), 1.4, 1.2); mix(o, env(tone(len(0.12), 90, 60), 0.001, 0.12, 2), 0.8, 1.2); return norm(o, 0.75); },
    gateShut: function () { var o = new Float32Array(len(0.8)); var r = lowpass(noise(len(0.55)), 450); for (var i = 0; i < r.length; i++) r[i] *= (0.6 + 0.4 * Math.sin(i / SR * 2 * Math.PI * 30)) * Math.min(1, i / (0.04 * SR)); mix(o, r, 0.9); mix(o, env(band(noise(len(0.14)), 500, 1), 0.001, 0.13, 2), 1.6, 0.58); mix(o, env(tone(len(0.14), 80, 50), 0.001, 0.14, 2), 1, 0.58); return norm(o, 0.8); },
    gem: function () { var o = new Float32Array(len(0.06)); mix(o, env(band(noise(len(0.04)), 5200, 5), 0.0005, 0.035, 3), 1); mix(o, env(tone(len(0.05), 3300, 3300), 0.0005, 0.04, 4), 0.12); return norm(o, 0.35); },
    pickup: function () { var o = new Float32Array(len(0.2)); mix(o, env(band(noise(len(0.05)), 1800, 2), 0.0005, 0.05, 3), 1); mix(o, env(band(noise(len(0.05)), 2600, 2), 0.0005, 0.05, 3), 1, 0.08); return norm(o, 0.5); },
    step: function () { return norm(env(lowpass(noise(len(0.05)), 900), 0.001, 0.045, 2), 0.12); },
    land: function () { return norm(env(lowpass(noise(len(0.1)), 500), 0.001, 0.09, 2), 0.3); },
    ui: function () { return norm(env(band(noise(len(0.025)), 3000, 3), 0.0005, 0.02, 3), 0.3); },
    uiBack: function () { return norm(env(band(noise(len(0.03)), 1800, 3), 0.0005, 0.025, 3), 0.3); },
    hatch: function () { var o = new Float32Array(len(0.7)); mix(o, env(lowpass(noise(len(0.5)), 700), 0.02, 0.45, 1.5), 0.8); mix(o, env(band(noise(len(0.1)), 900, 1), 0.001, 0.1, 2), 1.2, 0.45); return norm(o, 0.7); },
    shove: function () { var o = new Float32Array(len(0.18)); mix(o, env(band(noise(len(0.15)), 800, 0.7), 0.01, 0.14, 2), 1); return norm(o, 0.5); },
    servo: function () { var o = new Float32Array(len(0.5)); var t = tone(len(0.5), 210, 210, 'sq'); lowpass(t, 900); mix(o, t, 0.4); mix(o, band(noise(len(0.5)), 1200, 2), 0.2); return norm(o, 0.25); },
    // enemy bolt: hollow pipe "thoomp" + falling zap
    bolt: function () { var o = new Float32Array(len(0.2)); var z = env(tone(len(0.16), 1500, 420, 'sq'), 0.001, 0.15, 2); lowpass(z, 3200); mix(o, z, 0.35); mix(o, env(band(noise(len(0.05)), 900, 1.2), 0.001, 0.045, 2), 0.9); mix(o, env(tone(len(0.08), 160, 90), 0.001, 0.08, 2), 0.6); return norm(o, 0.55); },
    // bolt hits something: short crackle + thud
    boltHit: function () { var o = new Float32Array(len(0.14)); mix(o, env(band(noise(len(0.06)), 2600, 2), 0.0005, 0.05, 3), 1); mix(o, env(tone(len(0.07), 260, 120), 0.001, 0.07, 2), 0.5); return norm(o, 0.5); },
    // Bomber fuse: 0.6 s fizz rising in pitch with sparky crackles
    fuse: function () { var n = len(0.62), o = new Float32Array(n); var h = highpass(noise(n), 2500); for (var i = 0; i < n; i++) h[i] *= (0.35 + 0.65 * i / n) * (0.7 + 0.3 * Math.sin(i / SR * 2 * Math.PI * 34)); mix(o, h, 0.6); for (var k = 0; k < 9; k++) mix(o, env(band(noise(len(0.012)), 4200 + k * 300, 4), 0.0005, 0.01, 3), 0.5, k * 0.065 + Math.random() * 0.02); var t = env(tone(len(0.6), 700, 1900, 'sq'), 0.05, 0.58, 0.5); lowpass(t, 2400); mix(o, t, 0.12); return norm(o, 0.5); },
    // Bomber blast: low boom, noisy body, glass and can rattle
    boom: function () { var o = new Float32Array(len(1.0)); mix(o, env(tone(len(0.5), 95, 32), 0.002, 0.5, 1.6), 1); mix(o, env(lowpass(noise(len(0.8)), 700), 0.002, 0.75, 1.8), 1.2); mix(o, env(band(noise(len(0.3)), 2400, 1), 0.001, 0.25, 2), 0.5); for (var i = 0; i < 4; i++) mix(o, env(band(noise(len(0.03)), 3400 + i * 600, 4), 0.0005, 0.025, 3), 0.35, 0.12 + i * 0.07); return norm(o, 0.95); },
    // Drone windup: rotor whine spinning up
    rotor: function () { var n = len(0.45), o = new Float32Array(n), ph = 0; for (var i = 0; i < n; i++) { var f = 140 + 260 * (i / n); ph += 2 * Math.PI * f / SR; o[i] = (Math.sin(ph) > 0 ? 1 : -1) * (0.6 + 0.4 * Math.sin(ph * 0.25)); } lowpass(o, 1800); mix(o, env(band(noise(n), 1600, 2), 0.05, 0.4, 1), 0.3); env(o, 0.06, 0.4, 0.8); return norm(o, 0.35); }
  };

  A.init = function () {
    if (A.ctx) return;
    var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    try { A.ctx = new AC(); } catch (e) { return; }
    SR = A.ctx.sampleRate;
    A.comp = A.ctx.createDynamicsCompressor();
    A.comp.threshold.value = -14; A.comp.ratio.value = 4; A.comp.attack.value = 0.003; A.comp.release.value = 0.15;
    A.master = A.ctx.createGain(); A.master.gain.value = A.enabled ? 0.8 : 0;
    A.master.connect(A.comp); A.comp.connect(A.ctx.destination);
    Object.keys(RECIPES).forEach(function (k) {
      var data = RECIPES[k](), b = A.ctx.createBuffer(1, data.length, SR);
      b.getChannelData(0).set(data); A.bufs[k] = b;
    });
    A.ready = true;
  };
  A.resume = function () { if (A.ctx && A.ctx.state === 'suspended') A.ctx.resume(); };
  A.setEnabled = function (on) { A.enabled = on; if (A.master) A.master.gain.setTargetAtTime(on ? 0.8 * A.duck : 0, A.ctx.currentTime, 0.02); };
  A.mute = function (m) { if (A.master) A.master.gain.setTargetAtTime(m || !A.enabled ? 0 : 0.8, A.ctx.currentTime, 0.02); };

  /* opts: {pitch, gain, pos:{x,z}, listener:{x,z,yaw}} */
  A.play = function (name, opts) {
    if (!A.ready || !A.enabled) return;
    var buf = A.bufs[name]; if (!buf) return;
    opts = opts || {};
    var gain = opts.gain === undefined ? 1 : opts.gain, pan = 0;
    if (opts.pos && A.listener) {
      var L = A.listener, dx = opts.pos.x - L.x, dz = opts.pos.z - L.z, d = Math.sqrt(dx * dx + dz * dz);
      gain *= Math.max(0, 1 - d / 40);
      if (gain <= 0.01) return;
      var rx = Math.cos(L.yaw), rz = -Math.sin(L.yaw); // listener right vector
      pan = d > 0.5 ? Math.max(-1, Math.min(1, (dx * rx + dz * rz) / d)) : 0;
    }
    // voice stealing: drop the oldest quiet voice first
    if (A.voices.length >= A.maxVoices) {
      var vi = 0; for (var i = 0; i < A.voices.length; i++) if (A.voices[i].g < A.voices[vi].g || (A.voices[i].g === A.voices[vi].g && A.voices[i].t < A.voices[vi].t)) vi = i;
      try { A.voices[vi].src.stop(); } catch (e) { /* already stopped */ }
      A.voices.splice(vi, 1);
    }
    var src = A.ctx.createBufferSource(); src.buffer = buf;
    src.playbackRate.value = opts.pitch || 1;
    var g = A.ctx.createGain(); g.gain.value = gain;
    var node = g;
    if (A.ctx.createStereoPanner) { var p = A.ctx.createStereoPanner(); p.pan.value = pan; g.connect(p); node = p; }
    src.connect(g); node.connect(A.master);
    var v = { src: src, g: gain, t: A.ctx.currentTime };
    A.voices.push(v);
    src.onended = function () { var k = A.voices.indexOf(v); if (k >= 0) A.voices.splice(k, 1); };
    src.start();
  };
  // gem tick pitch rises +1 semitone per gem within 0.5 s, capped at +6
  A.gem = function (now) {
    if (now - A.gemT < 0.5) A.gemChain = Math.min(6, A.gemChain + 1); else A.gemChain = 0;
    A.gemT = now;
    A.play('gem', { pitch: Math.pow(2, A.gemChain / 12) });
  };
})(window.IB = window.IB || {});
