# Problem Definition

## One-line problem

**Useful human motion is trapped inside video pixels.**

A short clip contains reusable information about pose, timing, trajectory, contacts and action sequence, but today that information is normally coupled to the original actor, camera, scene and whichever model happens to extract it.

AI Motion Labs exists to separate **motion as an asset** from **video as a rendering of that asset**.

## What is broken today

### 1. Motion is not portable

A pose/control sequence made for one system often cannot be sent cleanly to another. Tools use different joint sets, coordinate conventions, frame rates, body models and confidence semantics.

### 2. Every downstream model wants a different control input

One system wants a reference video, another a pose sequence, another a skeleton animation, another SMPL-family parameters, another keyframes. Users keep re-extracting and adapting the same motion.

### 3. Pixels mix motion with irrelevant information

Background, lighting, identity, clothing, camera shake and compression are baked into video even when the only thing we want is the action.

### 4. Camera motion and person motion get confused

A dancer moving left and a camera panning right can look similar in image coordinates. High-quality reuse needs explicit coordinate spaces and, eventually, a world-grounded root trajectory.

### 5. Temporal information gets destroyed

Frame-by-frame pose extraction can jitter, miss occluded joints and lose contacts. Downstream generation then produces sliding feet, teleports, discontinuities and resets after cuts.

### 6. There is no durable provenance layer

A derived motion asset needs to know where it came from, what extractor produced it, what was inferred/interpolated and whether it may be shared or used commercially.

### 7. Re-extraction is wasteful

Once a useful movement has been extracted and quality-checked, it should be reusable without paying the compute cost again.

## Our first problem boundary

The first milestone is intentionally smaller than a creator platform or video-generation product:

> **Given a user-provided 5–30 second, primarily single-person video, create a self-describing, reusable MotionSpec asset that can be validated without the original extraction model.**

That asset should preserve provider-native observations while being independent of the provider that produced them.

## What v0 must capture

- source fingerprint and technical metadata;
- exact timestamps/timebase;
- joint-set definition;
- 2D observations when available;
- 3D observations when available;
- confidence/visibility;
- coordinate-space definitions;
- extractor/model/version/options;
- missing-frame quality summary;
- rights/provenance metadata;
- payload paths and array shapes/dtypes.

## What v0 deliberately does **not** promise

- perfect 3D reconstruction from arbitrary monocular footage;
- multi-person choreography;
- automatic copyright clearance;
- a YouTube downloader;
- mesh/identity recovery;
- a canonical SMPL/SMPL-X dependency;
- stunt generation or unsafe-action synthesis;
- polished generative rerendering;
- AR/VR simulation;
- marketplace/search UI.

Those can be built on the asset layer later. They should not contaminate the first contract.

## Why model-independent matters

The extraction market is moving too quickly to crown one permanent backend. MediaPipe is cheap and practical. MMPose provides richer whole-body 2D pose. MotionBERT can lift pose sequences into 3D. WHAM/GVHMR-class research improves world-grounded recovery but introduces heavier and sometimes commercially restrictive dependencies.

The system therefore treats **extractors as adapters** and **MotionSpec as the stable boundary**.

## Initial user value before any generative renderer

Even the core asset layer can support:

1. extract once, reuse repeatedly;
2. compare multiple extractors on one clip;
3. normalize timestamps and coordinate metadata;
4. build private motion libraries;
5. deduplicate identical source/action assets;
6. export later to BVH/glTF/vendor controls;
7. preserve source/rights history alongside motion.

## Later products that should sit on top

The same infrastructure can feed:

- D2C/product-demo remakes;
- creator/ad motion templates;
- character/actor replacement;
- training-video standardization;
- industrial procedural assets;
- AR/VR training pipelines;
- animation/robotics retargeting;
- motion search and marketplaces.

These are **applications of MotionSpec**, not reasons to fork the core.

## Success criteria for the foundation

The foundation passes when all of the following are true:

1. A short ordinary MP4 can be processed with one command.
2. The output contains `manifest.json` + binary pose payload.
3. The asset validates on a machine that does not have MediaPipe installed.
4. Missing frames are explicit rather than silently fabricated.
5. A second extractor can be added without changing the core manifest model.
6. Provider-specific coordinate spaces are recorded, not hand-waved.
7. Source video is not required to be redistributed with the asset.
8. Public sharing is off by default unless rights metadata says otherwise.
