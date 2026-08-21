# Quality and Benchmarks

A motion asset is only useful if we can tell when it is bad.

The project should not hide behind model demos or visual cherry-picking. Every extractor/enricher should be evaluated on the same small rights-clean benchmark corpus, with metrics that correspond to failures humans actually notice.

---

# Quality layers

## Q0 — Technical validity

Can the asset be trusted as a file/data structure?

Checks:

- manifest validates;
- payload exists;
- arrays exist;
- shapes/dtypes match;
- timestamps are monotonic;
- sample counts align;
- coordinate/joint references resolve;
- no unexpected infinities;
- missing values follow the declared policy.

This should be deterministic and model-independent.

## Q1 — Detection coverage

Did the extractor actually see the person?

Metrics:

- frame coverage;
- joint coverage;
- average confidence;
- longest missing span;
- coverage by body region: torso/legs/arms/hands/feet/face where applicable.

A single “mean confidence” is not enough: good torso tracking can hide useless hands.

## Q2 — Temporal stability

Does motion flow continuously rather than jitter/teleport?

Metrics/signals:

- joint velocity spikes;
- acceleration/jerk spikes;
- sudden root/image-center jumps;
- limb-length variance over time;
- left/right joint identity swaps;
- discontinuities around occlusion or turns.

These are not absolute truth metrics, but they are good alarms.

## Q3 — Kinematic plausibility

For canonical/animation-ready tracks:

- stable bone lengths;
- forward-kinematic reconstruction error;
- normalized quaternion error;
- impossible joint-angle warnings where a model is available;
- foot/hand contact consistency;
- foot-skating score during predicted ground contact.

## Q4 — Spatial/world consistency

For world-grounded tracks:

- root path smoothness;
- floor penetration/floating;
- camera-motion vs root-motion consistency;
- static-person / moving-camera tests;
- known-traverse distance tests where available.

## Q5 — Reuse quality

The most important product metric.

Can the asset actually drive another output?

Test:

- retarget to neutral skeleton;
- export to BVH/glTF;
- reopen in an independent tool;
- compare segment start/end poses;
- later: drive two different video/animation backends.

A perfect pose benchmark that cannot be reused is not a successful MotionSpec asset.

---

# Small benchmark corpus first

Start with **10–20 rights-clean clips**, not a giant scraped corpus.

Every clip should have a reason to exist.

## B01 — Static-camera walk

Tests:

- basic body tracking;
- leg cadence;
- root movement;
- foot contacts.

## B02 — Walk toward/away from camera

Tests:

- depth ambiguity;
- scale change;
- crossing limbs.

## B03 — Side profile

Tests:

- self-occlusion;
- left/right stability.

## B04 — Turn/spin

Tests:

- identity/joint swaps;
- temporarily hidden limbs;
- continuity.

## B05 — Fast arms / dance-like movement

Tests:

- motion blur;
- fast joint acceleration;
- temporal jitter.

## B06 — Reach/pick/place product

Tests:

- hand/object interaction;
- arm pose;
- later hand landmarks and contacts.

## B07 — Crouch/kneel/floor contact

Tests:

- unusual body height;
- knees/feet contacts;
- occlusion.

## B08 — Handheld/moving camera

Tests:

- camera/root confusion;
- eventual world grounding.

## B09 — Brief occlusion

Person passes behind a foreground object or arm crosses torso.

Tests:

- missing spans;
- recovery after occlusion;
- no teleport on reappearance.

## B10 — Poor lighting/noisy phone footage

Tests the kind of source that makes the eventual product economically useful.

## Later additions

- loose clothing;
- seated motion;
- stair/step movement;
- two people crossing (even before multi-person support, to test primary-person stability);
- tool use;
- sustained hand gestures;
- extreme crop/partial body.

---

# Benchmark metadata

Do not commit private/reference video casually. Keep a manifest for every benchmark source:

```text
benchmark_id
source_owner
source_sha256
rights_status
public_commit_allowed
scenario_tags
duration
camera_type
known_failure_targets
notes
```

If footage is first-party and cleared for redistribution, a tiny sample can later live under `examples/` or a separate benchmark release. Otherwise keep media private and publish only metadata/results.

---

# v0.1 acceptance thresholds

These are engineering gates, not scientific claims.

For clean single-person 5–30 second benchmark clips:

- 100% assets pass structural validation;
- timestamp sequence is monotonic;
- no silently omitted decoded frames;
- pose is present in at least **95%** of frames for the easy/static baseline set;
- missing spans and confidence are reported;
- skeleton overlay visibly follows the intended primary person;
- source/model/version/options are recorded;
- source video is not required to validate the resulting asset.

Do not force the 95% number onto deliberately hard clips. Their purpose is to reveal failure modes, not make the dashboard green.

---

# Comparative extractor report

Once MMPose is added, produce one table per benchmark run:

| Clip | Extractor | Coverage | Mean confidence | Longest gap | Temporal warnings | Runtime | Notes |
|---|---|---:|---:|---:|---:|---:|---|

Later add:

- hand/foot coverage;
- 3D bone-length variance;
- foot-skate score;
- export/round-trip error;
- GPU/CPU memory;
- cost per processed minute.

The purpose is not to crown a universal winner. We may eventually choose extractors by clip type/cost.

---

# Runtime / economics metrics

Because this is intended to become infrastructure, quality must include cost.

Record per processing run:

```text
video_duration_s
wall_time_s
realtime_factor = wall_time / video_duration
peak_memory
GPU type / CPU type
extractor/model
estimated compute cost
```

A model that improves pose error by 3% but costs 20× more may be the wrong default and a useful premium/enrichment option.

---

# Visual QA outputs

M2 should generate:

1. **overlay preview** — skeleton over original source;
2. **neutral preview** — skeleton only on a clean canvas;
3. **confidence timeline** — textual/JSON first, chart later;
4. **warning list** — exact time ranges for gaps/jumps.

Later animation-ready QA:

- ground plane;
- contact markers;
- root path trace;
- camera path/world view;
- side-by-side original vs reconstructed skeleton.

---

# Useful error metrics when ground truth exists

For public/research benchmark datasets where terms allow:

- MPJPE / PA-MPJPE for 3D joints;
- world/root trajectory error;
- acceleration error;
- foot-skating/contact metrics;
- reprojection error.

Do not report these on ordinary web/user video as if ground truth existed.

---

# MotionSpec-specific benchmark: interoperability

Traditional pose papers optimize pose accuracy. We need an additional benchmark: **interoperability**.

For one canonical animation-ready asset:

```text
MotionSpec
  ├── export BVH → reopen → positions/rotations
  └── export glTF → reopen → positions/rotations
```

Compare:

- duration/timestamps;
- root displacement;
- joint positions after FK;
- local rotation differences;
- start/end pose;
- contact timing where representable.

Success means our asset is not merely “correct inside our Python process.”

---

# Product benchmark: original video vs MotionSpec

Eventually compare two workflows on the same downstream task:

### A. Direct reference

```text
source video → downstream video/animation model
```

### B. MotionSpec

```text
source video → MotionSpec → edit/reuse/adapter → downstream model
```

Measure whether MotionSpec improves:

- provider switching;
- segment reuse;
- continuity across cuts;
- actor/background independence;
- cleanup/editability;
- repeat processing cost;
- search/library reuse;
- output consistency.

If MotionSpec does not win on any of these, the infrastructure is over-engineering. This benchmark keeps the project intellectually honest.
