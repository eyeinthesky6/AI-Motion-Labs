# Data Model

This document separates two things that should not be confused:

1. **MotionSpec** — the portable asset format that survives outside our service.
2. **Service metadata** — the future database used to index users, versions, collections and processing jobs.

Per-frame motion arrays belong in MotionSpec payload/object storage, **not** in ordinary Postgres rows.

---

# 1. MotionSpec portable asset

## Directory

```text
<asset>.motion/
  manifest.json
  payload/
    pose.npz
  preview/                   # optional
  exports/                   # optional
```

`manifest.json` is human-inspectable metadata. Binary arrays stay in `payload/`.

## `MotionSpecManifest`

| Field | Purpose |
|---|---|
| `schema_name` | Fixed identifier: `motionspec` |
| `schema_version` | Contract version, currently `0.1.0` |
| `asset_id` | Content-derived ID for this extracted asset |
| `created_at` | UTC creation timestamp |
| `source` | Source video fingerprint + technical metadata |
| `extractor` | Producer/model/version/options |
| `coordinate_spaces` | Explicit spaces used by payload arrays |
| `joint_sets` | Named joint definitions/topologies |
| `tracks` | Motion/camera/contact/event tracks |
| `rights` | Source/reuse attestation and sharing policy |
| `quality` | Extraction quality summary |
| `tags` | Optional descriptive tags |

## Source video

The source object stores metadata required for reproducibility/deduplication without forcing the source media itself into the portable asset.

```text
kind
original_filename
sha256
size_bytes
width
height
fps
frame_count
duration_s
```

### Why source SHA-256 matters

- exact-byte dedupe;
- reproducibility;
- provenance/takedown matching;
- avoid storing original video inside every derived asset.

Later we may add a **perceptual media fingerprint**, but it must be a separate field because perceptual similarity and byte identity are different concepts.

---

## Extractor metadata

```text
name
version
model
options
```

This is not decoration. If an extraction result changes after a model upgrade, the asset needs enough information to explain why.

Future additions may include:

- model/checkpoint SHA-256;
- container/environment version;
- hardware/runtime;
- source code revision;
- deterministic/non-deterministic flag.

---

## Coordinate spaces

Every spatial array should resolve to a named `CoordinateSpace`.

```text
id
dimensions
units
handedness
up_axis
forward_axis
origin
notes
```

### Rule: unknown is valid

It is better to store `unknown` than to silently invent an axis or metric scale.

### v0.1 examples

`image_normalized`

- 2D;
- normalized units;
- image origin/top-left semantics;
- y increases downward, represented as `up_axis = -y`.

`mediapipe_pose_world`

- 3D provider-relative coordinates;
- explicitly **not** treated as a world-grounded root trajectory.

### Canonical world space

A project-wide canonical world convention will be introduced only after at least two independent extractors and animation exports are compared. Raw provider spaces will remain preserved even after that decision.

---

## Joint sets

```text
id
joint_names[]
connections[]
provider
```

`connections` describe topology/visual connectivity. They do **not** automatically define a kinematic parent hierarchy.

This distinction matters because animation-ready skeletons need:

- one parent per non-root joint;
- rest offsets;
- local rotation semantics;
- root definition.

Those will be formalized in a later canonical skeleton model rather than smuggled into v0.1 observation tracks.

---

# Tracks

A MotionSpec asset is a collection of synchronized tracks.

Current/planned kinds:

```text
pose_landmarks
joint_positions
joint_rotations
root_trajectory
contacts
camera
events
```

Each track has:

```text
id
kind
joint_set_id          # when applicable
payload_path
arrays[]
```

Each payload-array descriptor stores:

```text
name
dtype
shape
semantics
coordinate_space_id   # when applicable
```

## Why tracks instead of one giant pose tensor

Because a useful motion asset eventually needs synchronized but semantically different data:

- body joints;
- hands/face;
- root translation;
- camera movement;
- contacts;
- semantic events;
- confidence.

A track model allows them to evolve independently while sharing the same time domain.

---

# Time model

## Authoritative time

Per-frame/sample timestamps are authoritative. `fps` is source/container metadata and must not be treated as an exact universal clock.

Reasons:

- variable-frame-rate video;
- dropped/duplicate frames;
- resampling;
- downstream models operating at different rates.

## Planned time semantics

Every dense track should eventually declare either:

- its own `timestamps_ms`; or
- a reference to a shared timebase track.

v0.1 keeps `timestamps_ms` beside the pose arrays in the same payload.

## Segments/events

Sparse events should use explicit timestamps/ranges, for example:

```json
{
  "event_type": "segment",
  "label": "reach_for_product",
  "start_ms": 4120,
  "end_ms": 6880,
  "confidence": 0.91
}
```

---

# Missing and uncertain data

## Missing values

For numeric pose arrays, v0.1 uses NaN for missing joint positions and zero/low confidence for unavailable detections.

Do not silently replace missing observations with `(0,0,0)` because zero can be a valid coordinate.

## Interpolation

When interpolation is added it should produce a **derived track/version** and record:

- interpolation method;
- max gap filled;
- which samples were synthesized;
- producer version.

Raw observations remain available.

---

# Animation-ready schema additions — planned

v0.2/v0.3 will likely need these structures after benchmarking.

## `SkeletonDefinition`

```text
id
joint_names[]
parent_indices[]
rest_offsets[J,3]
root_joint_index
coordinate_space_id
```

## `joint_rotations`

Recommended portable representation:

```text
local_quaternion[T,J,4]
```

But the schema must explicitly state:

- quaternion component order (`xyzw` vs `wxyz`);
- normalization requirement;
- local vs global;
- active/passive convention if needed;
- handedness/axis transforms.

Never rely on “every library knows what a quaternion means.” They do not.

## `root_trajectory`

Keep root movement separate from limb pose:

```text
translation[T,3]
orientation[T,4]
```

This allows:

- in-place looping;
- path replacement;
- camera-independent reuse;
- retargeting to different scenes.

## `contacts`

```text
contact_probability[T,C]
contact_names[C]
```

Examples:

- `left_heel_ground`;
- `left_toe_ground`;
- `right_heel_ground`;
- `right_toe_ground`;
- `left_hand_object`.

Binary contact can be derived using thresholds; preserve probability when possible.

## `camera`

Possible arrays:

```text
intrinsics[T,3,3] or static [3,3]
extrinsics[T,4,4]
focal_length...
```

Camera data must say exactly which transformation direction it represents (world→camera or camera→world).

---

# Lineage and versions

Motion processing should form a DAG, not destructive edits.

Example:

```text
source video
   ↓
asset A — MediaPipe observations
   ↓
asset B — smoothed observations
   ↓
asset C — MotionBERT 3D enrichment
   ↓
asset D — canonical skeleton + contacts
   ├── BVH export
   └── glTF export
```

Future lineage fields should include:

```text
parent_asset_ids[]
operation
producer
producer_version
options
created_at
```

An editor trim/split is also an operation and should retain source time ranges.

---

# Rights/provenance model

Current fields:

```text
source_attestation
public_share_allowed
commercial_reuse_allowed
license_id
source_url
notes
```

This model is deliberately conservative:

- public sharing defaults to `false`;
- unknown rights remain unknown;
- a technical extraction does not magically grant reuse rights.

Later service-level records may need evidence documents, grants, takedown status and jurisdiction-specific notes. See `RIGHTS_AND_PROVENANCE.md`.

---

# Quality model

v0.1:

```text
missing_frame_ratio
mean_confidence
warnings[]
```

Planned additions:

```text
coverage_by_joint
bone_length_variance
velocity_spike_score
acceleration_spike_score
foot_skate_score
root_jump_score
occlusion_spans
quality_grade
benchmark_version
```

Quality metrics should be versioned because the algorithms used to calculate them will improve.

---

# 2. Future hosted-service data model

Do not implement this database until the local pipeline is proven. This is the target so that early code does not paint us into a corner.

## `source_videos`

```text
id
owner_id
sha256
perceptual_hash?        # later
storage_uri             # private source, if retained
original_filename
technical_metadata_json
rights_status
created_at
deleted_at
```

## `extraction_runs`

```text
id
source_video_id
extractor_name
extractor_version
model_id/checkpoint_hash
options_json
status
started_at
finished_at
error_json
compute_metadata_json
```

## `motion_assets`

```text
id                     # stable logical asset
owner_id
current_version_id
visibility             # private/team/public
created_at
deleted_at
```

## `motion_asset_versions`

```text
id
motion_asset_id
motionspec_version
content_hash
manifest_uri
payload_prefix_uri
parent_version_ids[]
operation
producer_json
quality_report_id
rights_record_id
created_at
```

## `motion_segments`

```text
id
asset_version_id
start_ms
end_ms
label
confidence
embedding?              # vector later
key_pose_refs_json
created_by              # model/user
```

A segment should reference a parent asset/time range before we decide whether to materialize a separate payload.

## `export_artifacts`

```text
id
asset_version_id
adapter
adapter_version
format                  # bvh/gltf/vendor-X/etc.
uri
settings_json
created_at
```

## `rights_records`

```text
id
source_video_id
attestation
license_id
commercial_reuse_allowed
public_share_allowed
evidence_uri?
source_url?
notes
created_at
```

## `quality_reports`

```text
id
asset_version_id
metric_version
metrics_json
warnings_json
created_at
```

## `collections`

```text
id
owner/team
name
visibility
```

Join table `collection_assets` links assets/segments to collections.

## `tags`

Keep human tags and machine semantics distinguishable:

```text
asset_id_or_segment_id
tag
source                  # user/model/import
confidence?
model_version?
```

---

# What should **not** go in Postgres

Avoid a table with one row per frame or joint. A 30-second 30-fps whole-body clip already becomes tens/hundreds of thousands of numbers; large libraries make that approach expensive and awkward.

Keep these in object/binary storage:

- dense positions;
- rotations;
- confidence arrays;
- contact arrays;
- camera matrices;
- previews;
- exports.

Use Postgres for discoverability, permissions, lineage, metadata and indexes.

---

# Search/embedding model — later

Semantic motion search can use an embedding per asset/segment, stored in a vector index such as pgvector once the product needs it.

Do not make an embedding the asset identity. Similar motions should be searchable while remaining distinct provenance/versioned objects.

Potential searchable features:

- semantic text description;
- normalized motion embedding;
- duration;
- body-part involvement;
- speed/energy;
- contacts;
- locomotion/path properties;
- source/rights filters.

---

# Data-model invariants

These should become validator checks over time:

1. Track payload paths are relative to the asset root.
2. Every referenced joint set exists.
3. Every referenced coordinate space exists.
4. Shape/dtype in manifest equals payload.
5. Timestamps are monotonic.
6. Track sample counts align with their timebase.
7. Quaternion tracks are finite and normalized within tolerance.
8. Parent hierarchy has exactly one root and no cycles.
9. Missing values are explicit.
10. Derived tracks retain producer/lineage information.
11. Public sharing cannot be enabled merely by an extractor.
12. Source media is not assumed to be redistributable because a derived asset exists.

The point of MotionSpec is not merely to store arrays. It is to make the **meaning of those arrays explicit enough that another system can safely reuse them**.
