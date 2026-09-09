# Research Update — September 2026

This note records the current evidence used to keep the core implementation reuse-first.

## MMPose / RTMPose

Official MMPose is Apache-2.0 and supports 2D multi-person pose, hands, face, 133-keypoint whole-body pose and 3D mesh recovery. Its RTMPose whole-body configuration explicitly uses **133 keypoints**. The project also documents video inference and model aliases.

Use: **M3 second extractor / richer hands-feet-face observations**.

Do not make MMPose's 133-keypoint layout the canonical MotionSpec skeleton. Preserve it as a provider-native joint set and map explicitly when needed.

Sources:
- https://github.com/open-mmlab/mmpose
- https://github.com/open-mmlab/mmpose/blob/main/configs/wholebody_2d_keypoint/rtmpose/coco-wholebody/rtmpose-x_8xb32-270e_coco-wholebody-384x288.py
- https://github.com/open-mmlab/mmpose/blob/main/demo/docs/en/2d_wholebody_pose_demo.md

## MotionBERT

MotionBERT's official repository is Apache-2.0. Its 3D pose configuration uses **17 H36M joints**, and its documentation explicitly says other keypoint formats must be converted before inference. It supports sequences up to 243 frames in the referenced workflow.

Use: **M4 2D→3D enrichment adapter**, with a versioned explicit joint mapping. Never silently pass MediaPipe-33 or WholeBody-133 arrays into a 17-joint model.

Sources:
- https://github.com/Walter0807/MotionBERT
- https://github.com/Walter0807/MotionBERT/blob/main/configs/pose3d/MB_ft_h36m.yaml

## PyMotion

PyMotion provides NumPy/PyTorch motion operations, quaternion and rotation conversions, forward kinematics, BVH read/write and skeleton operations. Its package is useful as a processing library rather than a canonical asset format.

Use: **M5 canonical animation layer**, especially rotations, FK and BVH handling.

Source:
- https://github.com/UPC-ViRVIG/pymotion

## bvhio

bvhio is MIT licensed and provides read/write/edit/create support for BVH hierarchical 3D transforms.

Use: **M6 BVH interoperability/reference implementation**. It is a lightweight alternative/reference to PyMotion's BVH support.

Sources:
- https://github.com/Wasserwecken/bvhio
- https://github.com/Wasserwecken/bvhio/blob/main/LICENSE

## glTF

Khronos glTF 2.0 supports articulated/skinned animation through joint hierarchies and node transform animation. Animation samplers reference time/value accessors, making it a practical interchange target once MotionSpec has a canonical skeleton and rotations.

Use: **M6 export**, not canonical storage.

Sources:
- https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc

## Decision

The core remains deliberately boring:

```text
video
  → provider-native observations
  → MotionSpec
  → explicit mappings/enrichment
  → canonical animation layer
  → independent exports/adapters
```

This lets us swap MediaPipe, MMPose, MotionBERT, future world-grounding models and commercial generators without rewriting the asset contract.

## Licensing warning

Repository code licenses are not enough to establish commercial safety for every checkpoint, body model or dataset. Every future adapter must record code, weights, body-model and dataset licensing separately before becoming a production dependency.
