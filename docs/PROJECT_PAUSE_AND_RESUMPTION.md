# Project Pause Review — September 2026

## Executive decision

**AI Motion Labs is paused as an active product build.**

Do not continue the planned MotionSpec/gateway roadmap simply because the technical foundation exists. Keep the repository as an R&D asset and restart only if a concrete user problem appears that existing video/motion tools do not solve adequately.

The original thesis was technically sound: motion embedded in video can be extracted, represented as reusable data, retargeted and reused across characters, animation, AI video, AR/VR and training. The research also showed that much of the obvious product surface is already available from existing commercial and open-source systems.

The project therefore moved from **"build a model-independent motion infrastructure product"** to **"preserve the research and wait for a validated missing problem."**

---

## What we were trying to achieve

The project began with a simple observation:

> A useful human action should not have to remain trapped inside the pixels of the original video.

The proposed pipeline was:

```text
video
  -> motion/pose extraction
  -> MotionSpec
  -> cleanup + segmentation + metadata
  -> reusable motion/action asset
  -> adapters
       -> AI video
       -> avatars
       -> BVH/glTF/3D
       -> Unity/Unreal/AR/VR
       -> training/simulation
```

Possible products considered around this core included:

1. a searchable reusable motion library;
2. model-independent motion interchange;
3. a conversion/gateway layer between pose, mocap and generator formats;
4. character/action transfer for creators and brands;
5. converting operational videos into training assets;
6. AR/VR training content generation;
7. eventually richer **ActionSpec** assets containing human motion, objects, contacts, camera/environment relationships and semantics.

The repository implemented enough foundation to test this thesis: MotionSpec v0.1, a MediaPipe reference extractor, provenance/rights metadata, validation, quality diagnostics and skeleton-preview tooling.

---

## What changed our view

The market has moved far enough that **video -> motion** and **reference performance -> changed character/video** are no longer scarce capabilities.

For ordinary creators, a growing class of AI video systems already accepts an image/video/reference performance and can preserve or transfer substantial parts of the action while changing the character, scene, clothing, background or visual treatment.

For traditional animation/mocap users, established tools already provide video mocap, retargeting, cleanup and common animation exports.

Therefore the broad consumer proposition:

> "Give us a video and we will extract its motion so you can reuse it"

is not sufficient.

Likewise, a pure interchange standard or protocol is a poor first product for this project: adoption requires ecosystem credibility/network effects, while correct normalization and retargeting demand specialist animation knowledge.

---

## Existing systems/components found

This list is not exhaustive; it records the important categories and references found during the investigation.

### Commercial / product references

**Rokoko Vision / Rokoko Create**
- video-based motion capture;
- editing/cleanup and retargeting;
- animation workflow and common exports;
- strong evidence that generic video-to-mocap is already a product category.

**DeepMotion Animate 3D**
- video-to-3D animation;
- tracking, hands/face options, smoothing/foot locking;
- retargeting and FBX/BVH/GLB-style delivery.

**Plask**
- AI mocap/animation workflow;
- useful reference for capture -> retarget -> animation export.

**Kling Motion Control**
- reference/driving motion applied to a different character;
- evidence that motion transfer is becoming a generator feature rather than separate infrastructure users must understand.

**Luma Modify Video**
- preserves a source performance while modifying character/environment/visual treatment;
- important evidence against building a generic "clean/remake my video" product without a narrower unsolved problem.

### Open-source / research components worth retaining as references

**MediaPipe Pose Landmarker**
- lightweight baseline extractor;
- useful for cheap local experiments;
- not intended as the quality ceiling.

**MMPose / RTMPose**
- richer pose-estimation ecosystem including whole-body keypoints;
- useful if a future problem specifically requires richer body/hand/face observations;
- provider-native joint layouts should remain explicit rather than being silently treated as a universal skeleton.

**WHAM**
- monocular human motion recovery with world-motion reasoning;
- useful technical reference for root/world movement.

**GVHMR**
- strong reference for world-grounded human motion recovery;
- useful for research/benchmarking;
- licensing must be reviewed before any commercial dependency.

**MotionBERT**
- 2D-to-3D motion lifting reference;
- only useful if a future workflow specifically needs that enrichment;
- should not be integrated merely to complete an old roadmap.

**PyMotion**
- reusable motion mathematics, rotations, forward kinematics and BVH operations;
- preferable to writing basic animation mathematics ourselves.

**bvhio**
- lightweight BVH manipulation/read/write reference.

**Wan2.2-Animate**
- particularly relevant downstream/reference implementation;
- uses a driving performance for character animation/replacement;
- its preprocessing should be studied/reused where appropriate instead of recreating equivalent machinery.

**LivePortrait**
- important conceptual precedent: a driving performance can be represented as a reusable motion template for later reuse;
- focused on portraits rather than the full-body problem.

**Motion-X**
- demonstrates large-scale normalized motion datasets with semantic information;
- evidence that searchable/reusable motion libraries are technically viable;
- dataset/research licensing means it is not automatically a commercial content foundation.

**Video Depth Anything and future scene/object tooling**
- potentially relevant only if the project evolves from human motion into action understanding involving objects, contact and environment;
- deliberately deferred.

---

## What appears genuinely painful

Research and practitioner discussion indicate that difficult motion pipelines still have real problems:

- skeleton retargeting across different body proportions;
- foot sliding and contact errors;
- jitter and temporal discontinuities;
- root motion versus camera motion;
- occlusion;
- cleanup after automatic mocap;
- reliable conversion between representations without losing semantics;
- human-object contacts and interaction fidelity;
- precision/continuity requirements in professional animation, VFX, simulation and safety-critical workflows.

These are genuine problems.

However, **a genuine problem is not automatically the right problem for this project**.

Most of these require deep specialist knowledge to evaluate and solve correctly. A visually plausible result can still be technically wrong. Building an error-free normalization/retargeting gateway would push the project toward animation engineering, biomechanics, kinematics and domain-specific QA.

That is a poor fit unless a concrete customer problem makes the required investment worthwhile.

---

## Why the project is paused

### 1. The broad use case is commoditizing

For most ordinary creator workflows, "close enough" motion transfer and video modification are increasingly available directly inside AI video products. Users do not care about the underlying skeleton representation or MotionSpec if the final video looks good.

### 2. MotionSpec risks becoming technology in search of a user

A technically elegant schema, gateway or protocol has little standalone distribution. Users buy outcomes, not interchange architecture.

### 3. Standards/protocols are ecosystem businesses

A new standard becomes valuable when multiple important systems adopt it. A solo project cannot assume that adoption merely because the representation is cleaner.

### 4. The remaining hard problems are specialist problems

High-quality retargeting, motion cleanup, contacts and world-space correctness are not trivial stitching tasks. They require expertise and high-quality evaluation.

### 5. Existing tools should be reused, not rebuilt

If a future product needs motion extraction or animation conversion, first use existing commercial/OSS components. MotionSpec should only reappear if an actual workflow demonstrates that a missing intermediate representation is causing measurable pain.

### 6. Distribution and immediate value matter more than technical novelty

The project currently lacks a proven user who urgently needs this infrastructure. Building deeper infrastructure before that proof would consume engineering and attention without solving the more important problem: delivering an immediately understandable outcome to users.

---

## Current classification

**Status:** PAUSED / R&D REFERENCE

**Not currently:**
- a startup;
- a protocol/standards initiative;
- a mocap competitor;
- a motion marketplace;
- an AR/VR company;
- an industrial-training product.

**What remains valuable:**
- research map;
- MotionSpec experiment;
- extractor abstraction;
- provenance/rights thinking;
- quality diagnostics;
- understanding of the motion/video stack;
- a starting point if a concrete adjacent pain appears.

Do not delete the work. Do not continue it by inertia.

---

## Resumption criteria

Restart active development only if at least one of the following is observed with real users/workflows.

### A. Cross-tool reuse is materially painful

Evidence needed:
- users repeatedly recreate or manually convert the same motion for multiple tools;
- current converters lose important information;
- the problem costs meaningful time/money;
- existing products do not solve it acceptably.

Possible response:
- build the **smallest converter/adapter** that solves the demonstrated pair of systems;
- generalize into a gateway only after repeated demand.

### B. Automatic motion cleanup remains a costly bottleneck

Evidence needed:
- professional users spend substantial manual time fixing predictable mocap defects;
- a narrow class of errors can be automatically corrected and objectively evaluated.

Possible response:
- build the narrow cleanup tool, **not** a new motion standard.

### C. AI-video creators need reusable action assets across generators

Evidence needed:
- creators/agencies maintain many useful reference motions;
- repeatedly locating/re-recording/reformatting those motions is painful;
- simply keeping the original reference video is inadequate;
- portability/search/segmentation creates measurable workflow savings.

Possible response:
- revive a small **Motion Vault / Action Vault**, using existing extraction tools underneath.

### D. Human-object interaction becomes the unsolved constraint

Evidence needed:
- AI video can reproduce gross body movement but repeatedly fails at precise hand/product/tool interaction;
- this failure matters commercially;
- existing generators cannot fix it through ordinary reference video/control.

Possible response:
- investigate **ActionSpec**: motion + objects + contacts + timing + spatial relationships.
- only build the minimum representation required by the failing workflow.

### E. Precision commercial workflows demand deterministic transfer

Candidate areas:
- VFX/film continuity;
- stunt/choreography previsualization;
- professional animation/game pipelines;
- robotics/humanoid training;
- industrial simulation;
- medical/biomechanical motion;
- safety-critical training.

Evidence needed:
- named buyer/user;
- concrete workflow;
- existing solution and its failure;
- measurable cost/risk of that failure;
- access to a domain expert who can validate correctness.

Without domain validation, do not enter these areas.

---

## Questions to ask before resuming

For every proposed restart, answer these before writing code:

1. **Who exactly has the problem?**
2. **What are they doing today?**
3. **Why is the existing tool/workaround inadequate?**
4. **How frequently does the problem occur?**
5. **What does it cost them in money, time, quality or risk?**
6. **Can we show the improvement in a simple before/after?**
7. **Can a non-specialist judge whether our result is good enough?**
8. **Which existing component already solves 80-90%?**
9. **What is the smallest missing 10% we actually need to build?**
10. **Where can the first 100 relevant users be reached?**
11. **Would they pay/use it without anyone adopting a new protocol?**
12. **If the underlying AI model improves next month, does our product remain useful?**

If these questions do not have convincing answers, leave the project paused.

---

## Specific pain points worth watching

Do not proactively build these. Watch for repeated evidence.

| Pain | Why it may matter | Restart signal |
|---|---|---|
| Cross-skeleton retargeting | Existing motion does not port cleanly | Repeated professional complaints + paid workflow |
| Foot/contact cleanup | Automatic mocap still produces visible errors | High manual cleanup time |
| Root/camera separation | Important for reusable world motion | Existing tools repeatedly misinterpret locomotion |
| Human-object contacts | Critical for products/tools/training | AI video visibly fails despite good references |
| Action segmentation/search | Large motion collections become unusable | Teams already own hundreds/thousands of clips |
| Cross-generator reuse | AI video stack remains fragmented | Agencies repeatedly adapt same action manually |
| Precision continuity | Film/VFX needs deterministic repeatability | Named production workflow and buyer |
| Industrial procedure capture | Tacit motion matters for training | Partner/customer with validated training problem |
| Robotics/simulation transfer | Motion data may be valuable beyond video | Concrete robotics workflow and technical partner |

---

## If resumed: preferred build philosophy

The order is **not** "finish M1, then M2, then M3..." anymore.

Use:

```text
pain
 -> user
 -> current workaround
 -> measurable failure
 -> existing OSS/product
 -> smallest missing component
 -> prototype
 -> user validation
 -> only then generalize
```

Rules:

1. **Reuse first.** Integrate existing tools before implementing algorithms.
2. **Outcome before infrastructure.** Build what the user sees first.
3. **No protocol without demonstrated interoperability demand.**
4. **No public motion library before rights/provenance and actual library demand.**
5. **No arbitrary YouTube scraping/downloading as a core dependency.**
6. **No specialist correctness claims without a domain expert/benchmark.**
7. **No large roadmap before one narrow workflow works.**
8. **MotionSpec is optional.** If an existing representation solves the resumed problem, use it.
9. **Delete unnecessary architecture freely.** Previous work is research, not a commitment.
10. **Set a kill criterion before every restart experiment.**

---

## Recommended first experiment if a relevant opportunity appears

Do not resume by improving the extractor.

Take the user's actual failing workflow and test existing tools end-to-end.

Example:

```text
real source action
 -> best existing extractor/generator
 -> target character/environment/tool
 -> required output
```

Compare:
- quality;
- fidelity;
- manual effort;
- time;
- cost;
- repeatability.

Only when the failure is specific and repeated should AI Motion Labs implement the missing component.

---

## Final project thesis at pause

The durable insight from this project is **not that the world needs MotionSpec**.

It is:

> Human actions are becoming reusable computational assets, but extraction itself is commoditizing. Value will accrue where existing systems still fail to make those actions reliable, portable, searchable, precise or useful inside a specific high-value workflow.

AI Motion Labs should resume only when we can point to one of those failures in the hands of a real user.

Until then, the correct action is to preserve the research and stop building.
