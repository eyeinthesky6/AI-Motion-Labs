# MotionSpec

MotionSpec is the model-independent portable contract for AI Motion Labs.

The current schema is:

- `motionspec-v0.1.schema.json`
- `schema_name = motionspec`
- `schema_version = 0.1.0`

## What the schema covers today

v0.1 is intentionally an **observation asset envelope**, not a claim to have solved universal animation representation.

It standardizes:

- source-video fingerprint/technical metadata;
- extractor/model/version/options;
- named coordinate spaces;
- named joint sets;
- synchronized track descriptors;
- binary payload array names/shapes/dtypes;
- rights/provenance flags;
- basic quality metadata.

The first payload is normally `payload/pose.npz`.

## What the schema does not standardize yet

The following are postponed until we have real results from multiple extractors/exporters:

- canonical humanoid skeleton;
- canonical world-axis convention;
- rest-pose/bone hierarchy;
- quaternion ordering and animation-ready local rotations;
- world-grounded root trajectory;
- contact schema detail;
- camera matrices;
- semantic segment/event payload.

Those will be added as explicit versioned contracts rather than guessed into v0.1.

## Source of truth

Runtime Pydantic models live in:

`src/aimotionlabs/models.py`

The checked JSON Schema is generated from `MotionSpecManifest`. Run:

```bash
python scripts/export_schema.py
```

A test should fail if the checked schema drifts from the runtime model.

## Compatibility policy

During `0.x` development, schema changes may be breaking, but every asset always carries its exact schema version.

Rules:

1. Never reuse a version number for a changed contract.
2. Additive compatible changes can increment patch/minor as appropriate.
3. Breaking structural/semantic changes require a new schema version and migration logic.
4. Preserve original provider observations when generating a richer derived version.
5. Export adapters declare which MotionSpec versions/features they accept.

## Payload principle

JSON is for meaning and references; dense numeric motion stays binary.

Why:

- smaller files;
- fast NumPy loading;
- avoids enormous JSON manifests;
- allows future payload backends (NPZ, Arrow/Parquet, Zarr, etc.) without rewriting top-level product metadata.

NPZ is the bootstrap choice because it has almost zero infrastructure cost. We should only migrate payload format after real scale/interoperability needs justify it.

## Validation layers

### JSON Schema

Useful for language-independent validation of the manifest shape.

### Python/Pydantic

Useful for runtime parsing and typed developer ergonomics.

### Asset validator

Also checks cross-file invariants that JSON Schema cannot:

- referenced payload exists;
- array name exists;
- actual shape/dtype matches descriptor;
- coordinate-space IDs resolve;
- joint-set IDs resolve.

Later it will also validate timestamps, skeleton hierarchies, quaternion normalization and track semantics.

## Interop goal

MotionSpec becomes interesting only when multiple independent systems can both produce and consume it.

Before calling v1 stable, require at minimum:

- 2 independent extraction pipelines;
- 1 normalized animation-ready skeleton path;
- BVH export/readback;
- glTF export/readback;
- one non-animation downstream adapter (for example a video-generation or AR/VR control path).
