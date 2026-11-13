# Look prototype (reference only, not shipped)

These scripts are the throwaway prototype behind `../PLAN.md`. They change nothing in the game: `proto.js` is
injected into the built `Play Inkbolt.html` at run time by Playwright.

Run from this folder, one job at a time (headless Chromium renders on the CPU here):

```bash
node base-shots.js /tmp/look/base stronghold metro
```

```bash
node proto-shots.js /tmp/look/proto stronghold 0 '{}' mid
```

```bash
node proto-shots.js /tmp/look/proto metro 0 '{"grid":true,"indoorAmb":0.20,"fogColor":"#232a36","floorGloss":0.5}' mid,q
```

- `base-shots.js <outDir> <plan...>`: today's look, four automatic views per zone (entry, mid, midback, q).
- `proto-shots.js <outDir> <plan> <zone> '<config JSON>' [views]`: the same views with the prototype applied.
  Config keys are the `DEFAULTS` at the top of `proto.js`.
- `probe.js`: proves `sampler2DArray` in a patched toon material and a multisampled half-float target with a
  readable depth texture in three.js r128.
- `stats.js <plan...>`: draw calls, triangles, meshes and programs per map.
- `baketime.js <plan...>`: time of the light-map bake and the number of light sources found per zone.
- `palettes.json`: every model family's palette cell names (from `ib_lib.PALETTES`), used to guess surface
  classes and find emissive cells.

What is a shortcut here and must be replaced in the real build is listed in section 3 of the plan.
