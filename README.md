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

The first reference extractor is **MediaPipe Pose Landmarker** because it is light, works on ordinary video, returns 33 landmarks plus metric hip-centered world landmarks, and the MediaPipe codebase is Apache-2.0. It is a bootstrap backend, not the final quality ceiling.

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
AGENTS.md                     guardrails for AI/code agents
docs/                         product, architecture, research and build notes
models/                       external-model setup notes; model files ignored
spec/                         MotionSpec JSON Schema
scripts/                      spec/dev helper scripts
src/aimotionlabs/             core package
  extractors/                 replaceable video→motion backends
examples/                     example manifests/assets
tests/                        small contract/validator tests
```

Read these first:

- [`AGENTS.md`](AGENTS.md) — scope/architecture rules for coding agents.
- [`docs/PROBLEM.md`](docs/PROBLEM.md) — what we are fixing and what we are not.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — pipeline, motion levels and component boundaries.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — initial architecture decisions and deliberately deferred choices.
- [`docs/BUILD_ORDER.md`](docs/BUILD_ORDER.md) — staged implementation order and acceptance gates.
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — MotionSpec and future hosted-service data models.
- [`docs/OSS_RESEARCH_MAP.md`](docs/OSS_RESEARCH_MAP.md) — tools/research to reuse, with commercial-license lanes.
- [`docs/RIGHTS_AND_PROVENANCE.md`](docs/RIGHTS_AND_PROVENANCE.md) — upload-first rights/provenance policy and why v0 is not a YouTube downloader.
- [`docs/QUALITY_AND_BENCHMARKS.md`](docs/QUALITY_AND_BENCHMARKS.md) — how we decide whether an extracted motion is actually usable.
- [`models/README.md`](models/README.md) — external-model/checkpoint handling for reproducible runs.
- [`spec/README.md`](spec/README.md) — MotionSpec contract/versioning rules.
- [`spec/motionspec-v0.1.schema.json`](spec/motionspec-v0.1.schema.json) — current machine-readable manifest schema.

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

# Put the official Pose Landmarker model under models/; see models/README.md

# Extract
motionlab extract input.mp4 --out ./out/my-motion.motion --model ./models/pose_landmarker_full.task

# Validate an existing asset
motionlab validate ./out/my-motion.motion

# Inspect summary
motionlab inspect ./out/my-motion.motion
```

The first executable milestone is a reproducible 5–30 second, single-person clip → MotionSpec asset path.

## Development checks

Core tests deliberately do **not** install MediaPipe. That proves existing MotionSpec assets can be parsed and validated without the ML extraction environment.

```bash
pip install -e '.[dev]'
ruff check .
pytest -q
python scripts/export_schema.py
```

GitHub Actions is configured to run Ruff + the core tests on pushes/PRs.

## Design rules

1. **Spec first, model second.** No model-specific representation becomes the canonical storage contract.
2. **Keep raw + normalized.** Preserve provider-native observations and normalization metadata so better processing can be rerun later.
3. **No silent guessing.** Units, axes, confidence, missing frames and interpolation must be explicit.
4. **Provenance is data.** Every asset carries source fingerprint and reuse policy metadata.
5. **Commercial path stays clean.** Research-only models/datasets may be benchmark plugins, not mandatory runtime dependencies.
6. **Short clips first.** Optimize the first loop for roughly 5–30 second clips and one primary person.
7. **Adapters, not forks.** A new extractor or renderer plugs into the same interfaces.
8. **Motion quality must be visible.** Coverage, discontinuities and later contacts/export error are measured rather than hidden.

## Project/repository license status

**No project-wide open-source license has been selected yet.** The repository is public, but do not assume that means unrestricted reuse of AI Motion Labs code. We should choose the project license deliberately once the split between open MotionSpec/interchange pieces and any proprietary product/service layer is decided.

Third-party dependencies, pretrained weights, body models and research datasets retain their own licenses; see `docs/OSS_RESEARCH_MAP.md`.

## Status

**Foundation / v0.1 scaffold complete.** The repository now has the MotionSpec data contract, reference extractor interface + MediaPipe adapter, asset packager/validator, CLI, machine-readable schema, core contract tests/CI, agent guardrails, and the architecture/build/research/rights/quality documents. The model-independent packager/validator has also been smoke-tested with a synthetic payload in an isolated local harness.

**Next executable milestone:** M1 — run the actual MediaPipe path on a small rights-clean clip set, record the checkpoint hash/runtime/coverage, fix real decode/extraction issues, and then add skeleton preview/QA before MMPose or any product UI.
