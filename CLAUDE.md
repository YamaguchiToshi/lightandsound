# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An interactive light-and-sound environment (音と光のインタラクティブ環境) for children with severe
physical/multiple disabilities. Tilting an iPad, touching the screen, or pressing an assistive switch
makes particles of light stream across the canvas while a fluid soundscape responds — the point is a
legible **cause & effect** loop, not a game.

The entire application is **one file**: `index.html` (~2000 lines — CSS `<style>` at 22–356, markup,
then all JS in `<script>` at 527–2000). There is **no build step, no package.json, no dependencies,
and no test suite**. Vanilla Canvas 2D + Web Audio API only. Keep it that way: the app must run
offline as a PWA and from a plain static host, so do not add CDN links, npm packages, or a bundler.

## Commands

```bash
# Local HTTPS server (required: iOS Safari gates DeviceOrientation + Web Audio behind HTTPS)
python3 serve_https.py 8443       # serves repo root at https://<lan-ip>:8443/ with cert.pem/key.pem
```

Verification is manual, in a browser — open the page, press start, and exercise tilt/pointer/switch
input. There is nothing to lint or test.

Deployment is automatic: any push to `main` triggers `.github/workflows/deploy.yml`, which uploads
the repository root as-is to GitHub Pages (<https://yamaguchitoshi.github.io/lightandsound/>).
`.nojekyll` must stay present.

## Architecture

### The interaction contract

Everything here serves one loop: **a child acts, and light and sound answer.** Four input modalities —
device tilt, pointer, touch, and assistive switch — are normalized by `VirtualGravity` into a single
2D vector (`gx`, `gy`, clamped to ±`TUNING.gravity.range`), and every subsystem downstream reads only
that vector. This is why a child who can only tap a switch gets the same response as one who can tilt
the iPad: the modality is erased at the input boundary rather than compensated for later. One
`requestAnimationFrame` loop in `App.loop()` drives it:

```
tilt    ┐
pointer ├→ VirtualGravity.update() → gx, gy →  ParticleSystem.updateAndDraw()  →  light (Canvas)
touch   │       (index.html:1043)                        │
switch  ┘                                                └→ metrics → AudioSystem.processFrame() → sound
```

Note the asymmetry: **sound is not driven by the input, it is driven by the light.** `processFrame`
never receives `gx`/`gy`; it receives aggregated particle-field state, so sound is a second-order
consequence of the action and always lags the visuals (numbers under "Response timing" below). Keep
that ordering — sound driven per-particle straight from input was deliberately abandoned because it
degenerates into machine-gun beeps.

The `metrics` object returned by `updateAndDraw` (`meanSpeed`, `centroidX/Y`, `pooledRatio`,
`maxEnergy`, `salientParticle`, `width`, `height`) is the **only** coupling between the visual and
audio engines. Audio never reads particles directly; it reads that aggregate. Preserve the boundary.

Top-level pieces, in file order:

| Lines | Piece | Notes |
|---|---|---|
| 536 | `THEMES` | 6 color palettes; deliberately no pure `#ffffff` (anti-blowout) |
| 602 | `CONFIG` | single mutable global, read live every frame by every subsystem |
| 627–748 | `TUNING`, `PARTICLE_LAYERS`, `SWITCH_KEYS`, `SCALES`, `MODAL_PARTIALS`, `SLIDERS`, `SELECTS` | tuning constants and lookup tables the classes below are driven by |
| 750–853 | `SimplexNoise`, `getFractalPotential`, `getCurl` | 3-octave FBM curl noise → divergence-free flow |
| 855 | `VirtualGravity` | DeviceOrientation, pointer, and Space/Enter/arrow switch input |
| 1071 | `Particle` | one of three depth layers, drawn from `PARTICLE_LAYERS` |
| 1240 | `ParticleSystem` | resize/DPR handling, separation pass, additive draw, metric extraction |
| 1440 | `AudioSystem` | Macro (noise + drone) / Meso (granular) / Micro (modal bell) → reverb → out |
| 1779 | `App` | config restore, UI wiring, the rAF loop |

The tables are the seam to edit for tuning work: layer composition lives only in `PARTICLE_LAYERS`
(share, size, sensitivity, alpha, trail length), key mappings only in `SWITCH_KEYS`, and the numbers
that shape feel but are not exposed in the settings panel only in `TUNING`. `AudioSystem` routes every
voice through `_routeToOutput(node, pan, time)`, which builds the panner → master + reverb-send tail;
do not hand-wire those connections again.

### CONFIG and settings

`CONFIG` is read fresh each frame, so most parameter changes take effect immediately with no rebuild.
Two exceptions: `particleCount` is reconciled every frame by `ParticleSystem.adjustParticleCount()`,
and `colorTheme` must be changed via `particleSystem.applyTheme(key)` (which recolors existing
particles) rather than by assigning `CONFIG.colorTheme` directly.

`CONFIG` is persisted wholesale to `localStorage` under the key `lightandsound_config` and merged
back over the defaults at startup. Adding a setting means three coordinated edits: a default in
`CONFIG`, a control in the settings-panel markup using the `param-<slug>` / `val-<slug>` (slider) or
`select-<slug>` (dropdown) id convention, and a row in the `SLIDERS` or `SELECTS` table. `App.initUI()`
binds both tables generically, so persistence and label updates come for free; a row's optional
`apply(app, value)` runs side effects (volume, theme) and `toggles` shows or hides a dependent item.
A stale saved value will override a changed default on a returning device — rename the key or the
config field if that matters.

The panel is split into a short always-visible section (the things a teacher retunes per child —
volume, palette, input mode, response strength, switch behavior, screen type) and `<details
class="settings-group">` blocks for the rest (光の詳細 / 音の詳細 / 操作の詳細 / 使い方とヒント).
Because binding is by id, markup can be moved between groups freely without touching the tables —
but `debug-gx` / `debug-gy` / `debug-switch` must stay in the DOM (they now live inside 操作の詳細;
`App.loop` writes them every frame from cached references, and a collapsed `<details>` still keeps
its children in the document). Labels are plain Japanese aimed at teachers rather than the parameter
names; `DOCUMENTATION.md` §5 maps every on-screen label to its `CONFIG` key.

`DOCUMENTATION.md` §5 is the authoritative table of every parameter (default, range, meaning); keep
it in sync when parameters change.

### iOS / startup constraints

`startApp()` must call `audioSystem.init()` and `resume()` **synchronously** at the top of the user
gesture handler, before any `await` — iOS Safari will not unlock an AudioContext otherwise. The
`DeviceOrientationEvent.requestPermission()` dialog is requested only when `CONFIG.inputMode` is not
`switch` or `pointer`, so switch users are never blocked by a sensor prompt they cannot answer.

### Accessibility contract

Two pillars, both load-bearing. Weakening either is a regression even when it looks like a taste
change.

**1. Switch input is a first-class control path, not a fallback.** **Space = tilt right, Enter = tilt
left** (arrows mirror them; `SWITCH_KEYS` is the only mapping table). `CONFIG.switchMode` selects
`hybrid` (default — hold accelerates, release coasts for `switchPulseDuration`), `hold`, or `pulse`.
The hybrid coast exists so a child capable of only a momentary tap still gets a sustained, legible
response. Do not make a change that reduces switch input to a subset of pointer input.

**2. Sound carries the position and motion of the light, for children who cannot see it.** Stereo pan
is not ambience — it is the horizontal axis of the display, rendered for the ears. Every layer is
panned independently from live particle state:

| what the light does | how the sound says it | code |
|---|---|---|
| centroid X of the moving particles | pan of the whole fluid-noise bed (follow τ 0.06 s) | `index.html:1749` |
| where the stream texture is | pan of each granular grain, ±0.09 jitter | `index.html:1664` |
| X of the most energetic particle | pan of the crystal bell — widest of the three (×1.25) | `index.html:1683` |
| Y of that same particle | pitch of the bell (high = up, low = down) | `index.html:1677`, `getFrequencyForY` |
| flow speed | bandpass cutoff 320→3120 Hz, grain rate ~8–40/s | `index.html:1742`, `index.html:1756` |
| light pooled against an edge | everything fades toward silence | `index.html:1714`, `edgePoolFade` |

`computeStereoPan()` (`index.html:1632`) maps screen X to pan as `sign · |signed|^exponent`, where
`exponent = 1 / (1 + (stereoWidth · multiplier − 1) · 2)`. `stereoWidth` therefore controls the
**sharpness of the curve near center**, not a gain on the pan value — the mapping stays monotonic and
always reaches exactly ±1.0 at the screen edge, so every horizontal position is a distinguishable
position. This replaced a `|signed|^0.65 · stereoWidth · multiplier` form that clipped: at the default
1.45 the bell hard-panned from x≈0.70 outward, collapsing the outer 30% of each side into one
indistinguishable position, and raising `stereoWidth` made it worse (39% at 2.2). If you touch this
function, check the whole 0→1 sweep, not just the center. The per-layer multipliers differ on purpose —
bed 1.15, grains 1.05, bell 1.25: the transient the ear localizes best spreads fastest.

So none of the following are cosmetic audio tweaks; each deletes information a non-sighted child is
relying on:

- mapping bell pitch to anything other than Y, or randomizing it
- lowering `stereoWidth`'s default or ceiling, linearizing the pan curve, or reintroducing any form that clips at ±1.0 before the screen edge
- collapsing the three layers onto one panner
- raising reverb send on the localizing voices — diffuse reverb is the main enemy of direction on
  speakers, so the bell and grains deliberately route through drier sub-buses
  (`TUNING.audio.reverbSendBell` 0.45, `reverbSendGrain` 0.70) via `_routeToOutput`'s `sendBus`
  argument. The bell's own 1.2 s modal ring is oscillator envelope, not reverb, so drying it does not
  cost the "clear afterglow" the spec asks for
- raising `TUNING.audio.grainPanJitter` — ±0.03 keeps grains from collapsing to one point without
  smearing the position they are reporting
- lengthening the pan follow time constants

(Grain *pitch* alone carries no position — `index.html:1647` picks randomly from the upper half of the
scale, and grains convey position through pan only. That asymmetry is fine; do not "fix" it by making
the bell behave the same way.)

**Playback is stereo speakers, not headphones** (stated by the project owner). That rules out ITD and
HRTF approaches, and it makes physical setup dominate: speaker spacing *is* the width of the audible
screen, and a listener off the centre line loses pan information to the precedence effect. See
`DOCUMENTATION.md` §4.2 ④ for the setup guidance. The panning is equal-power amplitude only, with no
phase tricks, so it stays mono-safe.

### Response timing, and when the app goes quiet

Read off the constants rather than estimated:

| path | rise |
|---|---|
| input → light | `TUNING.gravity.switchAttack` 0.22 (~70 ms) plus particle acceleration; effectively immediate |
| input → fluid stream | the above + `smoothMeanSpeed` 0.12 (~130 ms, `index.html:1720`) + gain τ 0.08 s ≈ **300 ms** |
| input → drone rising | `smoothDroneEnergy` 0.04 ≈ **400 ms** (`index.html:1728`) |
| input → drone falling | 0.006 ≈ **2.8 s** (`index.html:1730`) — deliberately long; the "breathing" silence of `DOCUMENTATION.md` §1.2 |

Three conditions make input produce no sound at all, all in `processFrame`:

| condition | effect | line |
|---|---|---|
| `pooledRatio > 0.45` — light pooled against the edges | `edgePoolFade` attenuates **all** audio; it is a ramp, not a switch — 0.5→×0.89, 0.6→×0.67, 0.75→×0.33, and full silence only at 0.90 (90% of particles within 85 px of an edge) | 1714 |
| `smoothMeanSpeed ≤ 0.35` | no granular stream | 1755 |
| `maxEnergy ≤ 1.2` | no crystal bell | 1766 |

The first is specified behavior, not a bug (`DOCUMENTATION.md` §4.2 ⑤: pooling at an edge quiets the
room until the child tilts back the other way). Reaching true silence needs extreme pooling, so in
practice a held switch usually still produces a quiet response — but at the extreme a child could
previously reach a state where neither light nor sound answered. The edge anchor below now covers that
case. Treat any further change there as a design decision, not a tuning tweak.

### Ripple layer — why there are two canvases

Tap/click spawns an expanding light ripple (`Ripple`, `ParticleSystem.spawnRipple`) plus a water-drop
sound. It is drawn on a **second canvas** (`#ripple-layer`), not on `#stage`, and that separation is
load-bearing: `#stage` deliberately retains ~97% of each frame (that is what makes particle trails
work), so a ring stroked there every frame leaves every past ring behind and the result reads as a
concentric bullseye disc rather than a spreading wave. The ripple layer is cleared every frame instead.
It composites with `mix-blend-mode: screen` so ripples add to the light field rather than occlude it,
and `screen` cannot exceed 1.0, which keeps the anti-blowout rule intact. `drawRipples` toggles the
layer's `display` so a frame with no ripples costs nothing. Do not "simplify" this back into one canvas.

A passing wavefront also **pushes the particles** (`applyRippleForces`). The radial profile is
`sin(π · offset/reach)` — outward ahead of the crest, inward behind it, as in a real progressive wave —
so net transport is small. That sign matters: a purely outward shove sweeps particles to the walls under
repeated tapping, which raises `pooledRatio` and silences the audio via `edgePoolFade`. Measured: 20
rapid taps leave `pooledRatio` unchanged at any strength tested. `Ripple.activeFronts()` is shared by
`draw()` and the force pass so the wave you see and the wave that pushes are always the same geometry.
`TUNING.ripple.pushStrength` is 45; 0 disables the interaction and ≥80 reads as an explosion rather than
a ripple, which fights the app's calm and can startle.

Input mapping is intentional and asymmetric (`App.initUI`'s `pointerdown` handler): **touch and pen
ripple at the point touched; a mouse left-click ripples at a random position.** A switch wired to a
mouse click has no meaningful location, so inventing one is more honest than always using the pointer's
resting spot. `TUNING.ripple.brightness` is the single knob for tuning ripple visibility on a projector.

The drop sound (`triggerWaterDrop`) synthesizes the Minnaert bubble model: the "plop" of a stone is
mostly the entrained air bubble, whose frequency **rises** as it decays — a plain decaying sine does not
read as water. Three parts: a 50 ms broadband splash, the main bubble (rising ×1.55 over ~0.18 s), and
2–3 delayed micro-bubbles. X drives pan; Y drives the main bubble's pitch (top = smaller stone = higher),
matching the bell's Y→pitch direction so the two never disagree about height.

### Edge anchor

When light accumulates against the left or right wall, `updateEdgeAnchor` fires `triggerEdgeAnchor`
**once**, hard-panned to ±1.0 (`CONFIG.edgeAnchor`, default `'on'`). It is an absolute reference point,
so three properties are deliberate and must survive any edit:

- **Invariant timbre and pitch.** Always the same short broadband burst plus a fixed C5 partial
  (`TUNING.audio.edgeAnchorFreq` 523.25 Hz, a member of all three `SCALES`). If it varied with position
  it would be content, not a landmark.
- **Bypasses `edgePoolFade`.** The anchor is needed exactly when pooling has quieted everything else,
  so its gain is `TUNING.audio.edgeAnchorVolume` alone.
- **Broadband, and the driest voice in the mix** (`reverbSendAnchor` 0.25). High-frequency content is
  what makes a transient localizable on speakers; a low sine would be an anchor nobody could place.

Firing uses hysteresis on the per-side ratios `metrics.pooledLeftRatio` / `pooledRightRatio`
(`edgeAnchorOn` 0.30 → `edgeAnchorOff` 0.18) plus a 0.4 s minimum interval, so it does not chatter
around the threshold while a switch is held.

Also note that `CONFIG.gravityAxes` defaults to `x-only`, which zeroes `gy` outright
(`index.html:1060`). Vertical tilt, the up/down arrow keys, and the Y component of touch are all
collected but discarded by default; only `xy` lets them do anything.

### Projector mode

`CONFIG.displayMode === 'projector'` (the default) boosts particle radius, streak width, and halo
alpha, and raises the trail-fade floor (`0.04` vs `0.02`) to fight black-level lift on conference-room
projectors. Anything that touches particle sizing, alpha, or trail decay needs checking in **both**
modes.

## Design source of truth

`deep-research-report-1.md` (fluid/visual) and `deep-research-report-2.md` (audio/perception) are the
research basis for the engines; `light_and_sound_interactive_environment_spec_v0.1.md` is the original
spec. Consult them before changing the noise field, layer composition, or the Macro/Meso/Micro audio
split — the current constants are deliberate, not arbitrary.

## Conventions

UI strings, code comments, and all documentation are in Japanese; commit messages are English
Conventional Commits (`feat:`, `docs:`, `ci:`). `cert.pem` / `key.pem` are self-signed dev-only certs
committed intentionally for LAN testing on iPad.
