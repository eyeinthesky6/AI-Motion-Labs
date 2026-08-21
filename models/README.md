# External Models

Pretrained model bundles are **not committed to this repository**.

Reasons:

- they are large;
- model/checkpoint licensing can differ from repository code licensing;
- we want exact producer/checkpoint provenance in every MotionSpec asset;
- silent replacement of a `latest` model would make benchmark results hard to reproduce.

## MediaPipe Pose Landmarker — M1 baseline

Official model overview:

https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/index#models

For the first M1 run, use the official **Pose Landmarker Full / float16** bundle unless the benchmark shows a reason to prefer Lite or Heavy:

https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task

Save it locally as:

```text
models/pose_landmarker_full.task
```

This file is ignored by git.

### Before calling the M1 baseline reproducible

Record in the benchmark/run notes:

```text
filename
source_url
downloaded_at
sha256
file_size
mediapipe_package_version
```

Then add the observed SHA-256 to the M1 benchmark manifest/setup note. The current Google URL uses `latest`, so **do not pretend the URL alone pins a model version**.

The extractor already records the model filename and MediaPipe package version in MotionSpec. A later producer-provenance revision should also record the checkpoint SHA-256 directly in the manifest/run metadata.

## License rule

Never infer a checkpoint/model/body-model license only from the code repository's license. For every new model dependency, review separately:

1. code license;
2. checkpoint/weights terms;
3. body/model-asset terms;
4. data/dataset terms.

See `docs/OSS_RESEARCH_MAP.md`.

## Future model directories

Suggested local layout:

```text
models/
  pose_landmarker_full.task
  mmpose/                 # later, not committed
  motionbert/             # later, not committed
  research/               # restricted benchmark-only assets
```

Never commit registered/restricted SMPL/SMPL-X assets or other model files whose license prohibits redistribution.
