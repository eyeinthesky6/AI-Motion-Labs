# Architecture

## Principle

AI Motion Labs is an **asset infrastructure layer**, not an extraction-model wrapper.

The stable boundary is the MotionSpec asset. Everything that reads pixels, predicts pose, reconstructs 3D, retargets a skeleton, renders an avatar, or talks to a video generator is an adapter around that boundary.

```text
                         ┌─────────────────────────────────────────┐
                         │            downstream adapters          │
                         │ BVH · glTF · video models · AR/VR · API │
                         └────────────────────▲────────────────────┘
                                              │
                                      MotionSpec asset
                                              │
                          ┌───────────────────┴───────────────────┐
                          │ validate · normalize · enrich · segment│
                          └───────────────────▲───────────────────┘
                                              │
                              provider observations / tracks
                                              │
                ┌─────────────────────────────┴─────────────────────────────┐
                │                    extractor adapters                      │
                │ MediaPipe · MMPose/RTMPose · MotionBERT · future HMR     │
                └─────────────────────────────▲─────────────────────────────┘
                                              │
                    probe · decode · timestamps · source fingerprint
                                              │
                                     user-owned video
```

## Why there are multiple motion levels

Calling every pose output "3D motion" creates bad abstractions. We keep the levels separate.

### L0 — Observations

What an extractor actually saw or predicted in its native representation.

Examples:

- normalized 2D MediaPipe landmarks;
- 133-keypoint MMPose whole-body detections;
- provider-relative 3D landmarks;
- per-joint confidence/visibility.

**Rule:** L0 is never silently promoted to world-space animation.

### L1 — Normalized motion

Observations mapped into explicit MotionSpec semantics:

- monotonic timestamps;
- known joint names and topology;
- coordinate-space metadata;
- normalized confidence/missing data;
- optional resampling/smoothing;
- optional mapping to a canonical skeleton.

The current v0.1 implementation mostly packages L0 into a durable L1 envelope. That is deliberate.

### L2 — Animation-ready motion

Derived tracks that can drive a skeleton or avatar:

- local joint rotations;
- root translation/orientation;
- skeletal rest offsets;
- foot/hand contact probabilities;
- physically/kinematically cleaned trajectories.

This level is where BVH/glTF export becomes reliable.

### L3 — Application controls

Adapters translate reusable motion into application-specific controls:

- reference/control video for a generative-video model;
- keyframes/storyboards;
- Unity/Unreal animation assets;
- AR/VR training sequence;
- product-demo template;
- robot/character retargeting.

L3 belongs outside the core extraction contract.

---

## Core components

### 1. Source ingress

**v0:** local/user-provided video file only.

Responsibilities:

- accept a path/file;
- compute SHA-256;
- probe technical metadata;
- record source provenance/rights assertion;
- never assume a URL implies permission to download or reuse.

Later ingress connectors must be explicit plugins with their own policy and authentication rules.

### 2. Video decode/probe

Current bootstrap uses OpenCV for frame decoding and metadata. A later production pipeline should prefer FFmpeg/ffprobe for robust codec/container handling, with OpenCV kept for image conversion and simple processing.

**Important:** source/container FPS is not the canonical timebase. Per-frame timestamps in the payload are authoritative.

### 3. Extractor adapters

All extractors implement one narrow interface:

```python
class MotionExtractor(Protocol):
    def extract(video_path) -> ExtractedMotion: ...
```

`ExtractedMotion` can contain 2D positions, 3D positions, confidence and provider coordinate spaces. It does **not** force all providers into MediaPipe's joint set or coordinate system.

Planned adapters:

- `MediaPipePoseExtractor` — cheap baseline and smoke-test path;
- `MMPoseWholeBodyExtractor` — richer 133-keypoint body/face/hands/feet observations;
- `MotionBERT3DEnricher` — 2D sequence → 3D pose sequence after explicit joint mapping;
- world-grounded HMR adapter — experimental/research lane until commercially safe dependencies are settled.

### 4. MotionSpec packager

Writes a portable directory:

```text
<asset>.motion/
  manifest.json
  payload/
    pose.npz
  preview/                  # optional
  exports/                  # optional
```

The manifest remains small and inspectable. Large frame arrays stay in binary payloads.

### 5. Validator

Validation must work without the original pose model installed.

It checks:

- manifest schema;
- referenced payloads exist;
- array names exist;
- shapes/dtypes match the manifest;
- joint-set and coordinate-space references resolve;
- later: timestamp monotonicity, finite-value rules and track-specific invariants.

This is important because a reusable asset should not depend on the environment that created it.

### 6. Normalizers/enrichers

A normalizer reads an existing MotionSpec version and adds a derived track or creates a new asset version. It should never destroy the original observations.

Examples:

- resample to 30 fps;
- temporal smoothing;
- infer missing joints;
- map MediaPipe/MMPose joints to a canonical skeleton;
- infer contacts;
- estimate local rotations;
- recover a root trajectory;
- segment the clip into meaningful moves.

Every enrichment records its producer/model/options and parent asset/version.

### 7. Export adapters

Export is intentionally downstream of MotionSpec.

Target order:

1. debug skeleton preview;
2. BVH;
3. glTF animation;
4. vendor/video-model adapters;
5. Unity/Unreal/AR/VR convenience packages.

BVH and glTF are exports, not the canonical database representation.

---

## Raw vs canonical representations

The project will preserve **both**:

1. provider-native tracks for reproducibility; and
2. derived canonical tracks for portability.

We should not rush to invent a universal skeleton before we have compared at least MediaPipe, MMPose and one 3D recovery pipeline. The canonical coordinate convention and skeleton topology are therefore a **v0.2 decision**, not hard-coded into v0.1.

This is a feature, not indecision: provider data remains useful even if our canonical mapping changes.

## Camera is a separate track

Image-space movement combines subject motion and camera motion. A reusable asset must eventually represent them independently.

Planned tracks:

- `camera`: intrinsics/extrinsics or estimated camera trajectory;
- `root_trajectory`: person movement in recovered world/gravity coordinates;
- `joint_positions` / `joint_rotations`: body pose relative to the chosen space.

This separation is required for moving-camera footage, VR placement and believable retargeting.

## Contacts are first-class

Foot sliding is one of the easiest ways to expose bad generated motion. We therefore plan contact probabilities/events as explicit tracks rather than a rendering-specific hack.

Typical contacts:

- left/right heel and toe;
- hands on surfaces/tools;
- knees/other body contacts when useful.

The exact contact estimator can change without changing the core concept.

---

## Storage architecture

### Portable asset

A MotionSpec asset is independently transferable and should work on a filesystem, object store or archive.

### Service database — later

When a hosted product is added, Postgres stores **metadata and indexes**, not per-frame pose arrays.

Good candidates:

- asset IDs/hashes/owners;
- versions and lineage;
- processing runs;
- quality summaries;
- rights/provenance;
- tags/semantic embeddings;
- collections and access controls;
- exports.

Frame arrays live in object storage (S3-compatible/Supabase Storage/etc.).

### Dedupe

We keep two useful identities:

- **source hash** — identical uploaded bytes;
- **asset/content ID** — source + extractor/model + extracted payload.

Later we can add perceptual/source-video hashing and motion-similarity fingerprints, but neither belongs in the first milestone.

---

## Service architecture — only after the CLI works

Do not begin with queues, microservices or a web dashboard.

The progression should be:

```text
CLI/library
   ↓
local deterministic pipeline
   ↓
worker job abstraction
   ↓
object storage + metadata DB
   ↓
HTTP/API
   ↓
creator/library UI
```

The expensive ML components should eventually run as isolated workers. The MotionSpec core itself should remain lightweight enough to validate, inspect and transform assets without GPU dependencies.

## Failure philosophy

Motion extraction is probabilistic. The infrastructure should expose uncertainty instead of hiding it.

- Missing frame → NaN/missing marker + confidence, not fabricated certainty.
- Unknown axis/unit → `unknown`, not an invented convention.
- No reliable root trajectory → omit the track.
- Interpolation → record that it happened.
- Commercially restricted model → plugin/research lane, not hidden in the production core.

## Versioning

MotionSpec uses explicit semantic schema versions.

- `0.1.x`: provider observations + durable envelope;
- `0.2.x`: canonical skeleton/normalization decision;
- `0.3.x`: animation-ready rotations/root/contact conventions;
- `1.0`: first stable interchange contract after at least two independent extractors and two independent exporters round-trip successfully.

Breaking schema changes require a migration path. Asset lineage should preserve the source version rather than mutating history.
