# OSS + Research Reuse Map

The guiding rule is simple:

> **Do not rebuild solved research plumbing. Build the interchange, quality, provenance and adapter layer around it.**

At the same time, a permissive GitHub repository license does **not** automatically mean its pretrained weights, body models or training datasets are commercially reusable. We track those separately.

Last reviewed: **2026-08-21**. Licenses and upstream terms can change; re-check before shipping a commercial dependency.

---

# Proposed stack at a glance

| Stage | First choice | Why | Commercial lane |
|---|---|---|---|
| Decode/probe | FFmpeg/ffprobe + OpenCV | battle-tested media handling | check FFmpeg build; OpenCV permissive |
| Cheap pose baseline | MediaPipe Pose Landmarker | easy local bootstrap, 33 pose landmarks | green for code; verify model terms |
| Rich whole-body 2D | MMPose / RTMPose | mature, 133-keypoint whole-body configs | green for code; audit checkpoint |
| 2D → 3D sequence | MotionBERT | mature motion representation / 3D lifting | green for code; audit weights/data |
| Rotation/FK/BVH math | PyMotion | MIT, useful motion primitives | green |
| BVH I/O alternate | bvhio | MIT, simple hierarchy/edit/export | green |
| Open 3D export | glTF 2.0 | interoperable skeletal animation format | green/open spec |
| World grounding reference | WHAM | strong world-grounded recovery research | yellow: code MIT, dependency/license review |
| World grounding benchmark | GVHMR | strong gravity/world recovery research | red for commercial core unless licensed |
| Large motion research | Motion-X / Motion-X++ | proves large-scale video→motion annotation | research/reference; non-commercial access |
| Dance benchmark | AIST++ | multi-view dance, 3D/cameras | research/reference; video terms separate |

---

# 1. Media ingestion and preprocessing

## FFmpeg / ffprobe

**Use for:**

- probing container/codec metadata;
- robust decoding/transcoding;
- variable-frame-rate normalization when needed;
- preview generation;
- splitting/trimming without inventing our own media stack.

Upstream: https://ffmpeg.org/

**License note:** FFmpeg can be LGPL or GPL depending on build/configuration and linked components. Prefer invoking an appropriately licensed system/bundled binary rather than casually embedding an unknown GPL-enabled build into a proprietary distribution.

**Build decision:** v0 code currently uses OpenCV for simplicity. Introduce ffprobe/FFmpeg at M2 when real-world codec/VFR cases appear.

## OpenCV

**Use for:**

- frame decode in bootstrap path;
- colorspace conversion;
- debug overlays;
- light image preprocessing.

Upstream: https://github.com/opencv/opencv

Do not use OpenCV as the semantic motion layer; it is just media/CV plumbing.

---

# 2. Fast baseline pose extraction

## MediaPipe Pose Landmarker

Upstream:

- https://github.com/google-ai-edge/mediapipe
- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python

What we reuse:

- video-mode pose tracking;
- 33 body landmarks;
- normalized image landmarks;
- provider world landmarks;
- visibility/presence signals.

Why first:

- comparatively light integration;
- no reason to build our own pose detector merely to prove MotionSpec;
- MediaPipe source is Apache-2.0.

What we **do not** assume:

- MediaPipe's skeleton is our forever canonical skeleton;
- its provider world landmarks are a true global root trajectory;
- code license automatically settles every downloaded `.task` model/checkpoint term.

Repo status: **implemented as the reference extractor**.

---

# 3. Rich whole-body 2D extraction

## MMPose + RTMPose

Upstream: https://github.com/open-mmlab/mmpose

MMPose is Apache-2.0 and supports a broad pose-estimation model zoo. Its whole-body RTMPose configuration includes **133 keypoints**, giving us a materially richer test of MotionSpec than MediaPipe alone.

What we reuse:

- person/pose inference tooling;
- whole-body body/foot/hand/face keypoints;
- pretrained pose checkpoints after per-checkpoint license review;
- format definitions/mapping references.

Why important:

A second extractor with a different joint topology is the quickest way to discover whether our so-called model-independent format is actually independent.

Planned status: **M3**.

---

# 4. 2D sequence → 3D pose

## MotionBERT

Upstream: https://github.com/Walter0807/MotionBERT

Official repository license: Apache-2.0.

Useful properties:

- motion representation model rather than single-frame-only thinking;
- official in-the-wild inference path for custom videos;
- 3D pose task and motion representations;
- documented use of a 17-joint H36M-style input.

What we reuse:

- pretrained model/inference where terms allow;
- temporal 2D→3D enrichment;
- ideas for sequence handling and benchmarking.

Integration requirement:

```text
MediaPipe/MMPose joint set
      ↓ explicit mapping
H36M-style 17-joint sequence
      ↓ MotionBERT
3D derived track
```

Never perform an undocumented joint conversion.

License caution:

The code license is permissive, but the datasets used in research/training (for example Human3.6M/AMASS and others) have their own terms. Check released checkpoint terms and intended commercial use separately before product deployment.

Planned status: **M4**.

---

# 5. World-grounded human motion recovery

This is one of the technically hardest and most valuable layers because moving cameras otherwise contaminate root movement.

## WHAM

Upstream: https://github.com/yohanshin/WHAM

Paper/code goal: reconstruct **world-grounded humans with accurate 3D motion**, including camera-motion handling and contact-aware trajectory reasoning.

Repository license: MIT.

However, its documented setup requires separate registration/download of SMPL-family body-model assets and multiple other model/data dependencies. So we classify WHAM as:

**YELLOW — excellent research/reference/plugin candidate; commercial dependency chain must be audited.**

How to use it now:

- study world/camera/root separation;
- benchmark difficult moving-camera clips;
- keep behind an optional adapter;
- do not make the entire MotionSpec core depend on SMPL.

## GVHMR

Upstream: https://github.com/zju3dv/GVHMR

GVHMR performs world-grounded recovery using gravity-view coordinates and is a valuable accuracy/reference benchmark.

But its upstream LICENSE allows use/copy/modification/distribution for **educational, research and non-profit purposes only** and explicitly prohibits commercial use without contacting the authors.

It also requires registered SMPL/SMPL-X assets and other checkpoints.

Classification:

**RED for the default commercial runtime unless a commercial license is obtained.**

We can still:

- read the paper/code;
- benchmark internally where license permits;
- learn what a good MotionSpec world/camera/root representation needs;
- swap in a commercially usable implementation later.

---

# 6. SMPL / SMPL-X body models

Academic sites:

- https://smpl.is.tue.mpg.de/
- https://smpl-x.is.tue.mpg.de/

These models are enormously influential and many HMR repos emit SMPL/SMPL-X parameters. That does **not** mean MotionSpec should become SMPL-X-with-a-new-name.

The current official SMPL/SMPL-X model license is for non-commercial scientific/educational use, with separate commercial licensing available through Meshcapade/Max Planck channels.

Architecture decision:

- MotionSpec may store/export an **optional SMPL/SMPL-X adapter track**;
- the canonical core must not require users to accept a research-only body-model license;
- do not redistribute restricted model files;
- if a paid product later benefits enough from SMPL-X, obtain the appropriate commercial license rather than engineering around the license by pretending derived parameters are unrelated.

This separation is one major reason for a model-independent asset contract.

---

# 7. Motion math / skeleton manipulation

## PyMotion

Upstream: https://github.com/UPC-ViRVIG/pymotion

License: MIT.

Useful existing functions include:

- quaternion operations/conversions;
- rotation matrices, axis-angle, Euler and 6D rotations;
- forward kinematics;
- BVH reader/writer;
- mirroring;
- skeleton operations;
- NumPy and PyTorch implementations.

**Strong reuse candidate for M5.**

We should wrap it behind our motion-math/export layer rather than copy its algorithms into the repo.

## bvhio

Upstream: https://github.com/Wasserwecken/bvhio

License: MIT.

Useful for:

- BVH read/write/create;
- hierarchical transforms;
- local/world joint handling;
- animation editing.

Use as:

- alternate exporter/reference implementation;
- interoperability test;
- potentially the simplest first BVH writer if it fits our canonical skeleton.

Having two independent BVH readers/writers available is useful for testing that our exports are not accidentally tailored to one library.

## fairmotion

Upstream: https://github.com/facebookresearch/fairmotion

Useful research/reference library for motion processing and character animation. The project is archived, so treat it as **reference code**, not a new hard dependency unless we have a specific reason.

---

# 8. Interchange/export formats

## BVH

Old but valuable because it is easy to inspect and widely accepted by animation tooling.

Use for:

- first animation-ready export;
- debugging joint hierarchy and local rotations;
- Blender/Unity/Unreal import tests.

Do not make BVH canonical: it is weak for rich metadata, multiple synchronized tracks and modern provenance.

## glTF 2.0

Specification: https://registry.khronos.org/glTF/

Why useful:

- open interoperable 3D asset format;
- skeletal skins;
- animation channels for node translation/rotation/scale;
- natural route to web viewers and many 3D engines.

Use MotionSpec for **motion intelligence/provenance**, glTF for **portable rendered/rigged output**.

Possible later formats:

- USD/USDZ for pro/Apple/AR pipelines;
- FBX only through an adapter/tool because the format/ecosystem is less clean as a core open contract.

---

# 9. Research datasets / annotation pipelines

Datasets are useful to benchmark and learn from, but we should not start by ingesting millions of clips.

## Motion-X / Motion-X++

Upstream: https://github.com/IDEA-Research/Motion-X

Why it matters:

- demonstrates a pipeline that converts massive online video + existing motion datasets into unified whole-body motion/text annotations;
- reports **81.1K motion clips and 15.6M whole-body poses**;
- uses SMPL-X representations and semantic labels;
- explicitly does not freely redistribute all original RGB videos.

Current download instructions require authorization for **non-commercial purposes** and inherit terms from constituent datasets.

Use it for:

- architecture/reference ideas;
- schema comparison;
- research benchmark if terms permit;
- understanding useful semantic labels.

Do **not** build the commercial motion library by copying Motion-X data wholesale.

## AIST++

Dataset site: https://google.github.io/aistplusplus_dataset/

Useful properties:

- 1,408 dance motion sequences;
- over 10M annotated frames;
- multi-view camera intrinsics/extrinsics;
- 2D/3D keypoints and SMPL-format motion annotations;
- good stress-test domain for fast motion and continuity.

Important rights split:

- the AIST++ API code is Apache-2.0;
- the underlying dance videos/music require agreement to the separate AIST Dance Video Database terms;
- SMPL visualization/model use has its own license.

Use primarily as a benchmark/research reference rather than assuming “dataset exists” equals unrestricted product rights.

## AMASS / Human3.6M / 3DPW / RICH / EMDB etc.

These repeatedly appear in 3D human-motion papers. Each has its own registration and usage terms.

Rule:

**Reference datasets by exact license/version. Never create a generic `research-data/` bucket and assume commercial reuse.**

---

# 10. Video-platform ingestion

## YouTube

Current YouTube API Services Developer Policies state that API clients must not download/import/backup/cache/store copies of YouTube audiovisual content without prior written approval, and also restrict non-API methods of retrieving YouTube API data/content.

Therefore:

- **no YouTube URL downloader in v0**;
- user uploads a file they are entitled to process;
- future platform connectors require separate terms/policy review;
- provenance can record a source URL, but a URL is not a license.

See `RIGHTS_AND_PROVENANCE.md`.

---

# 11. Semantic segmentation/search — later

We do not need a bespoke motion-language foundation model on day one.

Potential existing pieces to evaluate after motion geometry works:

- VLM captioning of short clips/keyframes;
- MotionBERT-style motion embeddings;
- text-motion research models;
- simple signal-based segmentation using velocity/contact pauses;
- pgvector/vector search for segments.

A surprisingly good first segmenter may be **kinematic heuristics + VLM labels**, rather than another large training project.

---

# Dependency policy

Every dependency gets four fields before production use:

```text
code_license
weights_license
model/body-model_license
dataset/data_license
```

And three decisions:

```text
can_use_commercially?
can_redistribute?
can_make_mandatory_core_dependency?
```

## Green

Permissive enough for intended use after checkpoint-specific review.

Examples/candidates:

- MediaPipe code — Apache-2.0;
- MMPose code — Apache-2.0;
- MotionBERT code — Apache-2.0;
- PyMotion — MIT;
- bvhio — MIT;
- glTF specification.

## Yellow

Useful but commercial/dependency chain needs explicit review.

Examples:

- FFmpeg distribution/build configuration;
- WHAM workflow;
- checkpoints trained on restricted datasets;
- AIST++ dataset materials;
- SMPL/SMPL-X-related adapters when commercial licensing is not yet in place.

## Red

Must not be shipped in the default commercial core under current known terms without a new license/agreement.

Examples:

- upstream GVHMR commercial use;
- Motion-X data as a commercial foundation under its current non-commercial access terms;
- research-only SMPL/SMPL-X model assets without commercial license;
- arbitrary YouTube download/import as a product feature under current API policies.

---

# Research questions we actually need to answer

Do not collect papers for decoration. Each research item should resolve one engineering decision.

1. **What is the best inexpensive L0 pose source?**
   - Benchmark MediaPipe vs RTMPose.

2. **How much does 2D→3D lifting help reuse compared with reference-video control?**
   - Test MotionBERT on difficult actions.

3. **How much of “bad motion” is camera/root confusion?**
   - Benchmark moving-camera clips against WHAM/GVHMR-class references.

4. **What minimum skeleton is enough for D2C/creator use?**
   - Body-only vs whole-body/hands.

5. **Can contacts/cleanup reduce the failures users notice most?**
   - Quantify foot skating, teleporting and pose discontinuity.

6. **Which canonical representation round-trips cleanly into both BVH and glTF?**
   - Decide only after export experiments.

7. **Does MotionSpec add value versus simply handing the original video to a motion-control video model?**
   - Measure reuse, editability, segmentation, privacy, provider switching and compute savings.

That last question is the commercial kill-test. If we cannot demonstrate meaningful reusable value, we should not hide behind infrastructure complexity.

---

# Sources to keep bookmarked

- MediaPipe: https://github.com/google-ai-edge/mediapipe
- MediaPipe Pose docs: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
- MMPose: https://github.com/open-mmlab/mmpose
- MotionBERT: https://github.com/Walter0807/MotionBERT
- WHAM: https://github.com/yohanshin/WHAM
- GVHMR: https://github.com/zju3dv/GVHMR
- SMPL-X license: https://smpl-x.is.tue.mpg.de/modellicense.html
- PyMotion: https://github.com/UPC-ViRVIG/pymotion
- bvhio: https://github.com/Wasserwecken/bvhio
- Motion-X: https://github.com/IDEA-Research/Motion-X
- AIST++: https://google.github.io/aistplusplus_dataset/
- glTF: https://registry.khronos.org/glTF/
- YouTube API developer policies: https://developers.google.com/youtube/terms/developer-policies
