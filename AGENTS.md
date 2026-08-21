# AI Motion Labs — Agent Instructions

This repository is deliberately building **motion infrastructure before product UI**. Keep that boundary intact.

## Mission

The current job is:

```text
short user-provided video
    → replaceable extraction backend
    → explicit, validated MotionSpec asset
    → independent reuse/export
```

The core value is the reusable asset contract and the plumbing around it. Do not turn the repository into a video-generator frontend.

## Current build gate

Work in the order defined by `docs/BUILD_ORDER.md`.

The immediate executable milestone is **M1: real video → MotionSpec**. M2 is quality/preview. M3 proves a second extractor. Do not skip ahead because a later feature is more visually impressive.

## Hard architectural rules

1. **MotionSpec is the boundary; models are adapters.**
   - Never make MediaPipe, MMPose, SMPL, SMPL-X, MotionBERT, WHAM, GVHMR, or a video-generation vendor the canonical data model.

2. **Preserve provider-native observations.**
   - Normalization/enrichment creates derived tracks/versions.
   - Do not overwrite raw observations with smoothed/lifted/retargeted results.

3. **No silent semantics.**
   - Every spatial array has an explicit coordinate space.
   - Unknown unit/axis/origin stays `unknown` until established.
   - Missing data is explicit; do not replace a missing joint with `(0,0,0)`.

4. **Do not call body-relative 3D world-grounded motion.**
   - MediaPipe world landmarks are useful metric, hip-centered body coordinates.
   - Camera trajectory and global/root trajectory are separate future tracks.

5. **Do not choose the canonical animation skeleton yet.**
   - Compare at least MediaPipe, MMPose/RTMPose, one 3D enrichment path, and BVH/glTF export needs first.

6. **No restricted research dependency in the mandatory commercial core.**
   - Check code, checkpoint, body-model and dataset licenses separately.
   - GVHMR upstream is research/non-commercial unless separately licensed.
   - SMPL/SMPL-X academic assets are not a free commercial dependency.
   - Keep such systems behind optional research/adaptor boundaries.

7. **No YouTube downloader.**
   - v0 ingestion is user-provided video.
   - A public URL is provenance, not permission.

8. **Private by default.**
   - Extraction must never automatically make an asset public/shareable.

9. **Dense arrays do not belong in Postgres.**
   - Portable/object-storage payload for frame data; database later for metadata/indexes/permissions/lineage.

10. **Exports are downstream adapters.**
    - BVH/glTF/vendor formats do not become the canonical store.

## Avoid premature product work

Until the core gates pass, do not add:

- React/Next.js UI;
- login/auth;
- database migrations;
- payments/credits;
- marketplace/social features;
- public motion commons;
- AR/VR app;
- enterprise LMS;
- video-generation vendor integration;
- multi-person production pipeline;
- proprietary model training.

A tiny debug/QA viewer is allowed at M2 because it validates extraction quality.

## Reuse before building

Before implementing motion math, pose estimation, media handling, or exports, check `docs/OSS_RESEARCH_MAP.md`.

Preferred reuse direction:

- MediaPipe — bootstrap pose extractor;
- FFmpeg/ffprobe — robust media preprocessing when M2 requires it;
- MMPose/RTMPose — second/richer whole-body extractor;
- MotionBERT — candidate 2D→3D enrichment after explicit joint mapping;
- PyMotion / bvhio — rotations, FK and BVH plumbing where suitable;
- glTF — open 3D animation export;
- WHAM/GVHMR-class work — world-grounding research/reference, subject to dependency licenses.

Do not copy large chunks of upstream repositories into this repo. Prefer adapters/dependencies/subprocess boundaries with pinned versions.

## Code rules

- Python 3.11+.
- Keep the core package lightweight; heavy ML dependencies are optional extras/plugins.
- Keep extractor imports lazy so `motionlab validate` does not require ML packages.
- New extractor implementations conform to the generic extractor interface rather than adding provider conditionals throughout core code.
- Update MotionSpec deliberately and version it; never change semantics under an existing schema version.
- If runtime models change, regenerate/check `spec/motionspec-v0.1.schema.json`.
- Add only small contract/invariant tests needed to keep the interchange layer trustworthy.
- Generated videos/models/large `.npz` assets stay out of git unless a tiny rights-cleared fixture is deliberately approved.

## Definition of useful work

A change should improve at least one of:

- extraction fidelity;
- explicit semantics;
- provider independence;
- validation/quality visibility;
- reuse/exportability;
- provenance/rights safety;
- processing cost/reproducibility.

If it only makes a demo look more impressive without improving the reusable motion asset, it is probably not core work yet.

## Commercial kill-test

Keep asking:

> Why should a user keep/reuse MotionSpec instead of simply supplying the original reference video to the next model again?

The expected answers are portability, segmentability, editability, model switching, asset search/reuse, provenance, privacy, continuity/cleanup, and reduced repeated extraction. These claims must eventually be measured, not assumed.
