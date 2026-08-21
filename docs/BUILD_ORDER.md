# Build Order

The build order is intentionally biased toward **proving interchange and reuse**, not building a flashy video UI too early.

## North-star foundation test

Take one 5–30 second single-person clip and prove:

```text
video
  → extract
  → MotionSpec asset
  → validate independently
  → inspect/preview
  → export to a second representation
  → reuse without touching the source video again
```

If that loop is solid, creator, product-video, training and AR/VR applications can be layered on top.

---

## M0 — Contract and repository foundation

**Status: started.**

Build:

- Python package and CLI;
- MotionSpec manifest models;
- generic extractor interface;
- MediaPipe reference extractor;
- binary payload packaging;
- validator;
- source hashing and basic rights metadata;
- architecture/research/licensing docs.

Acceptance gate:

- repository can explain the problem and its boundaries without relying on a UI mockup;
- no provider-specific format is declared the universal format;
- asset can be parsed/validated without MediaPipe installed.

Do **not** add yet:

- auth;
- database;
- marketplace;
- payment;
- web UI;
- generative video model;
- YouTube downloader.

---

## M1 — First real `video → MotionSpec` run

Goal: prove that the current code works on ordinary clips before adding sophistication.

Build:

1. lock a known MediaPipe Pose Landmarker model version/checksum in setup docs;
2. use 3–5 legal/owned short benchmark clips;
3. run the CLI end-to-end;
4. validate manifest/payload;
5. fix timestamp/decode edge cases;
6. emit a simple processing report.

Benchmark clips should include:

- full-body walk, static camera;
- side/profile movement;
- fast arm motion;
- a turn/spin;
- short partial occlusion.

Acceptance gate:

- clean full-body clips process without manual frame editing;
- validator passes every generated asset;
- no silent dropped frames;
- detected/missing frame ratio is reported;
- output is reproducible enough that extractor/model/version/options are enough to understand how it was produced.

**Decision after M1:** if MediaPipe's current task/package API differs from the scaffold, fix the adapter rather than changing MotionSpec.

---

## M2 — Make quality visible

Goal: stop judging motion from JSON arrays.

Build:

- preview renderer: original video + skeleton overlay;
- neutral skeleton-only preview on blank background;
- per-frame confidence visualization/logging;
- quality report with coverage and simple temporal signals;
- robust FFmpeg/ffprobe preprocessing path for odd codecs/VFR clips;
- optional resampling into a normalized working video while preserving original timestamps/provenance.

Quality signals:

- pose detection coverage;
- mean joint confidence;
- joint velocity/acceleration spikes;
- limb-length variance;
- root/image jump warnings;
- missing/occluded spans.

Acceptance gate:

A human can look at the preview and immediately answer: **“Did we actually capture the action?”**

---

## M3 — Add a genuinely different 2D extractor

Goal: prove the extractor abstraction is real.

Preferred candidate: **MMPose/RTMPose whole-body**.

Why:

- Apache-2.0 codebase;
- mature OpenMMLab tooling;
- 133-keypoint whole-body configurations cover body, feet, hands and face;
- meaningfully different from MediaPipe.

Build:

- `MMPoseWholeBodyExtractor` plugin;
- explicit MMPose joint-set definition;
- mapping tables where needed;
- same MotionSpec packaging path;
- side-by-side quality comparison.

Acceptance gate:

- one source clip can produce two valid MotionSpec assets from two extractors;
- core packager/validator code does not fork into MediaPipe/MMPose versions;
- richer hand/foot landmarks survive packaging.

If this fails, fix the interface **before** adding 3D.

---

## M4 — 2D sequence → 3D pose enrichment

Goal: add useful 3D without pretending to solve world grounding yet.

Preferred first candidate: **MotionBERT** as an enrichment adapter.

Important constraint: MotionBERT expects a 17-joint H36M-style input, so we need an explicit, tested mapping from the selected 2D track. Never silently throw 133 joints into a 17-joint model.

Build:

- joint-mapping module with versioned mapping definitions;
- `MotionBERT3DEnricher`;
- derived `joint_positions` track;
- parent/source-track lineage metadata;
- 3D skeleton preview;
- basic bone-length and temporal checks.

Acceptance gate:

- the asset contains both original 2D observations and derived 3D;
- derived 3D is labeled with its actual coordinate semantics;
- no claim that it is globally positioned/world grounded unless a later stage provides that.

---

## M5 — Canonical skeleton + animation-ready layer

Goal: cross the line from “pose observations” to “portable animation asset.”

Only make the canonical skeleton decision after M1–M4 data is in hand.

Build:

- versioned canonical skeleton definition;
- provider → canonical joint mappings;
- explicit rest pose/bone offsets;
- canonical local joint rotations;
- root translation/orientation tracks;
- interpolation policy;
- temporal smoothing policy;
- foot-contact estimator;
- rotation convention metadata (quaternion ordering, local/global semantics).

Reuse:

- **PyMotion** for quaternion/rotation operations, FK and BVH utilities where suitable;
- **bvhio** as an alternate lightweight BVH I/O/reference implementation.

Acceptance gate:

- forward kinematics reconstructs positions close to the canonical position track;
- motion can be retargeted to a neutral skeleton without depending on the source person's pixels;
- contact-aware cleanup measurably reduces foot skating on benchmark clips.

---

## M6 — First independent exports

Goal: prove MotionSpec is useful outside our own code.

Build in this order:

1. BVH export;
2. glTF 2.0 skeletal animation export;
3. simple Blender/three.js viewer test;
4. optional Unity/Unreal import recipe.

Acceptance gate:

- export from MotionSpec, reopen using an independent reader/tool, and compare timing/root/joint motion;
- round-trip error is measured rather than eyeballed only.

**Why this matters:** if MotionSpec cannot leave our repository cleanly, it is not yet infrastructure.

---

## M7 — World grounding / camera separation

Goal: recover motion that remains meaningful when the camera moves.

Research candidates:

- WHAM — strong reference, MIT code, but its runnable workflow depends on separately licensed SMPL-family models and other weights;
- GVHMR — excellent research benchmark, but upstream license is non-commercial, so **do not make it a production core dependency** without a commercial agreement;
- future commercially clean world-grounding models/adapters.

Build:

- `camera` track contract;
- `root_trajectory` contract;
- gravity/world coordinate metadata;
- world-vs-camera motion benchmark;
- experimental plugin boundary for restricted research models.

Acceptance gate:

On a moving-camera clip, the system can distinguish “camera moved” from “person traversed the world” well enough to make the resulting root trajectory reusable.

---

## M8 — Motion segmentation and semantic assets

Goal: turn a 30-second clip into reusable pieces rather than one opaque blob.

Build:

- temporal segment model: start/end timestamp, label, confidence;
- automatic candidate cuts at pauses/contact/action changes;
- user trim/split/merge operations;
- semantic descriptions/tags;
- motion embedding/fingerprint for similarity search;
- key-pose extraction;
- continuity metadata: segment start/end pose signatures.

Acceptance gate:

A user can extract `walk → turn → reach → pick-up` as separate reusable segments while retaining their relationship to the source asset.

This is the bridge to the original “automatic storyboard” use case.

---

## M9 — Private motion library

Goal: make extraction compound in value.

Build:

- object storage + Postgres metadata index;
- asset/version lineage;
- private vault first;
- collections/tags/search;
- dedupe by source/content hash;
- semantic similarity search;
- export history;
- deletion/retention controls.

Do **not** start with an open public commons. Rights and quality are easier to control in a private library.

Acceptance gate:

A user uploads a clip once, then reuses one extracted segment in a new project without reprocessing the source video.

---

## M10 — One commercial adapter, not ten

At this point choose a wedge based on observed demand.

Candidate adapters:

- character/product-video rerendering;
- D2C product demonstration;
- creator/ad action templates;
- training/SOP conversion;
- AR/VR training content export;
- generative-video motion-control adapter.

Build **one** end-to-end adapter and measure whether MotionSpec materially improves cost, consistency or editability over feeding the original reference video directly into the downstream model.

Acceptance gate:

We can answer quantitatively:

> “Why does this customer need MotionSpec rather than just giving the source video to Kling/Seedance/Luma/etc.?”

If the answer is weak, do not build the marketplace/product layer yet.

---

# Parallel research tracks

These can run without blocking the core CLI.

## A. Licensing/commercial dependency audit

For every candidate, separately record:

- repository code license;
- pretrained-weight license;
- body-model license;
- training/evaluation dataset license;
- redistribution rights;
- commercial-use rights.

A permissive GitHub repo license does **not** automatically make its weights/models/datasets commercially safe.

## B. Canonical representation study

Compare:

- MediaPipe 33;
- COCO/COCO-WholeBody 133;
- H36M 17;
- SMPL/SMPL-X joints/parameters;
- common BVH humanoid skeletons;
- glTF skin/node animation needs.

The goal is not to invent another body model. It is to create a clean mapping/interchange layer.

## C. Benchmark corpus

Create a tiny rights-clean benchmark set we can commit metadata for and reproduce:

- static camera;
- handheld/moving camera;
- dance/fast movement;
- hands/product interaction;
- occlusion;
- crouch/floor contact;
- loose clothing;
- poor lighting.

Avoid starting with giant datasets. Ten difficult, well-understood clips will teach us more about the plumbing than a million uninspected clips.

---

# What not to build until the core passes

- general video editor;
- avatar marketplace;
- payments/credits;
- social feed;
- public YouTube ingestion;
- proprietary foundation model;
- full 3D scene reconstruction;
- enterprise LMS;
- VR headset application;
- multi-person choreography at production quality.

Those are products **on top of** the motion layer. The first job is to make motion a trustworthy reusable asset.
