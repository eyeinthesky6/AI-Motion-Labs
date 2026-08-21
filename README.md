# AI Motion Labs

**Video in → reusable motion asset out.**

AI Motion Labs is a model-independent motion infrastructure project. The first goal is intentionally narrow: take a short human-action video, extract motion once, normalize it into a reusable **MotionSpec** asset, and make that asset portable across future renderers, video models, 3D/AR/VR pipelines, training systems, and motion libraries.

The project is **not** starting as another video generator. Existing pose, motion-recovery, animation, and rendering tools already solve large pieces of the stack. Our job is to stitch the good pieces together behind a stable motion asset contract.

## The problem

Human motion is currently trapped inside pixels and inside vendor-specific control formats. Reusing the same action usually means reprocessing the source video, hand-storyboarding it, or adapting it separately for each downstream model. That creates several problems:

- motion is coupled to the original person, background, lighting, and camera;
- pose/motion formats differ by tool and model;
- 2D keypoints, 3D joints, SMPL-family parameters, BVH, glTF and generator controls do not share one clean interchange layer;
- camera motion and human root motion are easily confused;
- temporal continuity, contacts and confidence are often lost between stages;
- the provenance and reuse rights of an extracted asset are rarely recorded;
- the same clip gets expensively re-extracted again and again.

## Core thesis

A useful motion asset should survive changes in renderer, avatar, scene, business use case and generation model.

`video → extraction backend → normalized MotionSpec → reusable asset → adapters`

The **MotionSpec** is the product boundary. Extraction backends are replaceable.

## Foundation scope

### v0: prove the asset boundary

1. Ingest a user-provided local video.
2. Fingerprint and record provenance.
3. Extract a single primary person's pose sequence.
4. Store normalized timestamps, 2D landmarks, 3D/world landmarks when available, confidence and coordinate metadata.
5. Emit a self-describing MotionSpec asset directory.
6. Validate the asset without requiring the extraction model.

The first reference extractor is **MediaPipe Pose Landmarker** because it is light, works on ordinary video, returns 33 landmarks plus world landmarks, and the MediaPipe codebase is Apache-2.0. It is a bootstrap backend, not the final quality ceiling.

### Later, without changing the core asset contract

- MMPose/RTMPose whole-body 2D pose;
- MotionBERT 2D→3D lifting;
- higher-fidelity world-grounded recovery backends;
- temporal cleanup, foot/hand contacts and motion segmentation;
- canonical skeleton/retargeting;
- BVH and glTF exports;
- semantic tags and search;
- video-generator adapters;
- private/team/public motion libraries;
- industrial training and AR/VR adapters.

## Repository map

```text
docs/                         product, architecture, research and build notes
spec/                         MotionSpec JSON Schema
src/aimotionlabs/             core package
  extractors/                 replaceable video→motion backends
examples/                     example manifests/assets
```

Read these first:

- [`docs/PROBLEM.md`](docs/PROBLEM.md) — what we are fixing and what we are not.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — pipeline and component boundaries.
- [`docs/BUILD_ORDER.md`](docs/BUILD_ORDER.md) — implementation order and acceptance gates.
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — MotionSpec and future persistence models.
- [`docs/OSS_RESEARCH_MAP.md`](docs/OSS_RESEARCH_MAP.md) — tools/research to reuse, with licensing notes.
- [`docs/RIGHTS_AND_PROVENANCE.md`](docs/RIGHTS_AND_PROVENANCE.md) — why v0 is upload-first rather than a YouTube downloader.

## MotionSpec v0.1 asset shape

```text
my-motion.motion/
  manifest.json
  payload/
    pose.npz
  preview/              # optional/later
  exports/              # optional/later: BVH, glTF, vendor adapters
```

The manifest records source fingerprint, timebase, coordinate spaces, tracks, extractor version, rights/provenance and quality metadata. Large frame arrays stay in payload files rather than bloating JSON.

## Reference CLI target

```bash
# Install core
pip install -e .

# Install reference video extractor
pip install -e '.[mediapipe]'

# Extract (requires a MediaPipe pose-landmarker .task model path)
motionlab extract input.mp4 --out ./out/my-motion.motion --model ./models/pose_landmarker.task

# Validate an existing asset
motionlab validate ./out/my-motion.motion
```

The CLI and extractor skeleton live in this repo; the first milestone is a reproducible 5–30 second, single-person clip → MotionSpec asset path.

## Design rules

1. **Spec first, model second.** No model-specific representation becomes the canonical storage contract.
2. **Keep raw + normalized.** Preserve provider-native observations and normalization metadata so better processing can be rerun later.
3. **No silent guessing.** Units, axes, confidence, missing frames and interpolation must be explicit.
4. **Provenance is data.** Every asset carries source fingerprint and reuse policy metadata.
5. **Commercial path stays clean.** Research-only models/datasets may be benchmark plugins, not mandatory runtime dependencies.
6. **Short clips first.** Optimize the first loop for roughly 5–30 second clips and one primary person.
7. **Adapters, not forks.** A new extractor or renderer plugs into the same interfaces.

## Status

**Foundation / v0.1.** The repository is being set up around the core `video → MotionSpec asset` pipeline before any creator UI, marketplace, enterprise training layer, or generative rendering product is added.
