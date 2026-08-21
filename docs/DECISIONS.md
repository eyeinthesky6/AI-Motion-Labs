# Architecture Decisions

This is a compact record of decisions that should remain stable while the foundation is built. It exists to prevent each new model/tool from quietly redesigning the repository around itself.

## D001 — The product boundary is MotionSpec

**Decision:** video/pose models are replaceable adapters; MotionSpec is the durable asset/interchange layer.

**Reason:** extraction and generation models will change faster than customer assets should.

**Consequence:** provider-native observations are stored with explicit semantics and can later be enriched/exported without re-reading source pixels.

---

## D002 — Start with observations, not a fake universal skeleton

**Decision:** v0.1 packages exact provider observations, time, confidence, joint topology and coordinate metadata. A canonical animation skeleton is deferred.

**Reason:** MediaPipe 33, COCO-WholeBody 133, H36M 17, SMPL-family joints and common BVH rigs are not interchangeable by naming alone.

**Gate to revisit:** after MMPose + first 3D enrichment + BVH/glTF experiments.

---

## D003 — MediaPipe is the bootstrap extractor, not the quality ceiling

**Decision:** use MediaPipe Pose Landmarker for M1 because it is easy to run locally and provides 33 landmarks plus metric hip-centered world landmarks.

**Reason:** we need to prove asset plumbing before optimizing model quality.

**Consequence:** core code must validate/read assets without MediaPipe installed.

---

## D004 — 3D has multiple meanings

**Decision:** keep these concepts separate:

1. image-space 2D landmarks;
2. body/provider-relative 3D pose;
3. animation-ready local rotations + root motion;
4. world-grounded root/camera trajectories.

**Reason:** calling all of them “3D motion” creates broken reuse and camera/root ambiguity.

---

## D005 — Camera and human root motion are separate tracks

**Decision:** future world-grounding adds explicit `camera` and `root_trajectory` tracks.

**Reason:** image-space motion from a moving camera is not equivalent to a person traversing the world.

---

## D006 — Contacts are data, not a renderer hack

**Decision:** foot/hand contact information becomes an explicit track when the animation-ready layer is added.

**Reason:** contacts help temporal cleanup, foot-skate reduction, retargeting, segmentation and training/AR applications.

---

## D007 — NPZ first; storage format is replaceable

**Decision:** use small JSON manifest + compressed NumPy NPZ payload for v0.

**Reason:** minimal infrastructure, fast iteration and easy validation.

**Deferred alternatives:** Arrow/Parquet/Zarr/custom chunked stores if scale or streaming later requires them.

---

## D008 — Dense motion stays out of Postgres

**Decision:** future hosted service stores frame arrays in object/binary storage and metadata/search/lineage/permissions in Postgres.

**Reason:** per-frame/per-joint relational rows are the wrong cost and access pattern for motion sequences.

---

## D009 — Upload-first, private-first

**Decision:** v0 accepts user-provided files and creates private assets by default.

**Reason:** platform ingestion terms and source rights are a separate problem from motion extraction. YouTube URL downloading is specifically not part of the foundation.

**Consequence:** a public motion library is a later, explicit rights-cleared layer.

---

## D010 — Dependency license is four separate questions

For every ML dependency record independently:

1. code license;
2. pretrained-weight license;
3. body/model-asset license;
4. dataset/data license.

**Decision:** a permissive code repository alone is not enough to make a component mandatory in the commercial core.

**Examples:** upstream GVHMR is non-commercial without another agreement; SMPL/SMPL-X academic assets have separate commercial licensing.

---

## D011 — Restricted research systems remain optional

**Decision:** WHAM/GVHMR/SMPL-family pipelines may be research/benchmark adapters while we evaluate commercial-safe world grounding.

**Reason:** valuable research should inform MotionSpec semantics without contaminating the core's licensing.

---

## D012 — The first second extractor must be materially different

**Decision:** MMPose/RTMPose whole-body is the preferred M3 candidate.

**Reason:** a second MediaPipe-like wrapper would not test model independence. A 133-keypoint whole-body topology forces the asset model to prove it can carry richer hands/feet/face data.

---

## D013 — 2D→3D is enrichment, never replacement

**Decision:** MotionBERT or another lifter creates a derived 3D track/version while retaining original 2D observations.

**Reason:** inferred 3D has different uncertainty/coordinate semantics and may be regenerated with better models later.

---

## D014 — BVH and glTF are interoperability tests

**Decision:** add BVH then glTF after an animation-ready canonical track exists.

**Reason:** successful independent export/readback proves the motion asset is useful outside our own Python code.

**Consequence:** neither BVH nor glTF becomes the canonical internal representation.

---

## D015 — No web product until the local asset loop works

**Decision:** CLI/library → quality preview → second extractor → 3D/canonical layer → open exports before auth/database/marketplace/video-generator UI.

**Reason:** otherwise we risk building a SaaS shell around a motion artifact that is not yet portable or trustworthy.

---

## D016 — Public library is not a raw upload dump

**Decision:** future library has at least private, team and rights-cleared public layers.

**Reason:** quality, provenance and reuse rights differ between assets. Uploading a source should not silently grant strangers commercial reuse.

---

## D017 — Keep the project commercially falsifiable

**Decision:** eventually benchmark:

```text
source video → downstream model
```

against:

```text
source video → MotionSpec → edit/reuse/adapter → downstream model
```

**Reason:** if MotionSpec does not materially improve portability, editability, reuse, continuity, privacy/provenance, provider switching or repeated compute cost, the infrastructure is unnecessary.

This is the kill-test, not a philosophical preference for standards.

---

# Deferred decisions

Do not settle these from taste alone:

- canonical skeleton topology;
- canonical world axes/handedness;
- quaternion convention;
- exact contact representation;
- canonical payload format after NPZ;
- world-grounding production backend;
- public MotionSpec/open-source license;
- hosted product stack;
- marketplace/credit model;
- first paid vertical/application adapter.

Each should be decided from M1–M10 evidence and recorded here when settled.
