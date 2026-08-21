from __future__ import annotations

from pathlib import Path

import numpy as np

from aimotionlabs.asset import validate_asset
from aimotionlabs.models import (
    CoordinateSpace,
    ExtractorInfo,
    JointSet,
    MotionSpecManifest,
    MotionTrack,
    PayloadArray,
    QualitySummary,
    SourceVideo,
)


def _build_asset(root: Path) -> Path:
    asset_dir = root / "synthetic.motion"
    payload_dir = asset_dir / "payload"
    payload_dir.mkdir(parents=True)

    timestamps = np.asarray([0, 33, 67], dtype=np.int64)
    positions = np.asarray(
        [
            [[0.1, 0.2], [0.9, 0.2]],
            [[0.2, 0.2], [0.8, 0.2]],
            [[0.3, 0.2], [0.7, 0.2]],
        ],
        dtype=np.float32,
    )
    confidence = np.ones((3, 2), dtype=np.float32)
    np.savez_compressed(
        payload_dir / "pose.npz",
        timestamps_ms=timestamps,
        positions_2d=positions,
        confidence=confidence,
    )

    manifest = MotionSpecManifest(
        asset_id="motion_synthetic",
        created_at="2026-08-21T00:00:00+00:00",
        source=SourceVideo(
            original_filename="synthetic.mp4",
            sha256="0" * 64,
            size_bytes=1,
            width=100,
            height=100,
            fps=30.0,
            frame_count=3,
            duration_s=0.1,
        ),
        extractor=ExtractorInfo(name="synthetic"),
        coordinate_spaces=[
            CoordinateSpace(
                id="image_normalized",
                dimensions=2,
                units="normalized",
                up_axis="-y",
                origin="top-left",
            )
        ],
        joint_sets=[
            JointSet(
                id="two_joint",
                joint_names=["left", "right"],
                connections=[(0, 1)],
                provider="synthetic",
            )
        ],
        tracks=[
            MotionTrack(
                id="body_pose",
                kind="pose_landmarks",
                joint_set_id="two_joint",
                payload_path="payload/pose.npz",
                arrays=[
                    PayloadArray(
                        name="timestamps_ms",
                        dtype="int64",
                        shape=[3],
                        semantics="timestamps",
                    ),
                    PayloadArray(
                        name="positions_2d",
                        dtype="float32",
                        shape=[3, 2, 2],
                        semantics="2D positions",
                        coordinate_space_id="image_normalized",
                    ),
                    PayloadArray(
                        name="confidence",
                        dtype="float32",
                        shape=[3, 2],
                        semantics="confidence",
                    ),
                ],
            )
        ],
        quality=QualitySummary(missing_frame_ratio=0.0, mean_confidence=1.0),
    )
    manifest.save(asset_dir / "manifest.json")
    return asset_dir


def test_validator_does_not_need_extractor_dependencies(tmp_path: Path) -> None:
    asset_dir = _build_asset(tmp_path)
    manifest = validate_asset(asset_dir)

    assert manifest.asset_id == "motion_synthetic"
    assert manifest.extractor.name == "synthetic"


def test_validator_rejects_shape_mismatch(tmp_path: Path) -> None:
    asset_dir = _build_asset(tmp_path)
    manifest = MotionSpecManifest.load(asset_dir / "manifest.json")
    manifest.tracks[0].arrays[1].shape = [99, 2, 2]
    manifest.save(asset_dir / "manifest.json")

    try:
        validate_asset(asset_dir)
    except ValueError as exc:
        assert "Shape mismatch" in str(exc)
    else:
        raise AssertionError("Expected validator to reject mismatched payload shape")
