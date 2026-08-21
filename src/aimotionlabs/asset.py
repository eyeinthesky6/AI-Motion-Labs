from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from aimotionlabs.extractors.base import ExtractedMotion
from aimotionlabs.models import (
    MotionSpecManifest,
    MotionTrack,
    PayloadArray,
    QualitySummary,
    RightsMetadata,
    SourceVideo,
)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def probe_video(video_path: str | Path) -> SourceVideo:
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - extraction-only dependency
        raise RuntimeError("Video probing requires opencv-python-headless") from exc

    path = Path(video_path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if width <= 0 or height <= 0 or fps <= 0 or frame_count <= 0:
        raise RuntimeError("Could not determine valid video metadata")

    return SourceVideo(
        original_filename=path.name,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration_s=frame_count / fps,
    )


def _asset_id(source: SourceVideo, extracted: ExtractedMotion) -> str:
    digest = hashlib.sha256()
    digest.update(source.sha256.encode())
    digest.update(extracted.extractor.name.encode())
    digest.update((extracted.extractor.model or "").encode())
    digest.update(extracted.timestamps_ms.tobytes())
    for array in (extracted.positions_2d, extracted.positions_3d, extracted.confidence):
        if array is not None:
            digest.update(np.ascontiguousarray(array).tobytes())
    return f"motion_{digest.hexdigest()[:24]}"


def package_motion_asset(
    *,
    video_path: str | Path,
    extracted: ExtractedMotion,
    out_dir: str | Path,
    rights: RightsMetadata | None = None,
) -> MotionSpecManifest:
    source = probe_video(video_path)
    out = Path(out_dir)
    payload_dir = out / "payload"
    payload_dir.mkdir(parents=True, exist_ok=True)

    arrays: dict[str, np.ndarray] = {"timestamps_ms": extracted.timestamps_ms}
    descriptors = [
        PayloadArray(
            name="timestamps_ms",
            dtype=str(extracted.timestamps_ms.dtype),
            shape=list(extracted.timestamps_ms.shape),
            semantics="monotonic frame timestamp in milliseconds",
        )
    ]

    if extracted.positions_2d is not None:
        arrays["positions_2d"] = extracted.positions_2d
        descriptors.append(
            PayloadArray(
                name="positions_2d",
                dtype=str(extracted.positions_2d.dtype),
                shape=list(extracted.positions_2d.shape),
                semantics="provider-native 2D joint positions",
                coordinate_space_id="image_normalized",
            )
        )

    if extracted.positions_3d is not None:
        arrays["positions_3d"] = extracted.positions_3d
        descriptors.append(
            PayloadArray(
                name="positions_3d",
                dtype=str(extracted.positions_3d.dtype),
                shape=list(extracted.positions_3d.shape),
                semantics="provider-native 3D joint positions",
                coordinate_space_id="mediapipe_pose_world",
            )
        )

    if extracted.confidence is not None:
        arrays["confidence"] = extracted.confidence
        descriptors.append(
            PayloadArray(
                name="confidence",
                dtype=str(extracted.confidence.dtype),
                shape=list(extracted.confidence.shape),
                semantics="per-frame per-joint observation confidence",
            )
        )

    payload_path = payload_dir / "pose.npz"
    np.savez_compressed(payload_path, **arrays)

    basis = extracted.positions_2d if extracted.positions_2d is not None else extracted.positions_3d
    if basis is None:
        missing_ratio = 1.0
    else:
        frame_present = np.any(np.isfinite(basis), axis=tuple(range(1, basis.ndim)))
        missing_ratio = float(1.0 - np.mean(frame_present))

    mean_confidence = None
    if extracted.confidence is not None:
        valid = extracted.confidence > 0
        if np.any(valid):
            mean_confidence = float(np.mean(extracted.confidence[valid]))

    warnings: list[str] = []
    if missing_ratio > 0.05:
        warnings.append(f"pose missing in {missing_ratio:.1%} of decoded frames")
    if source.frame_count != len(extracted.timestamps_ms):
        warnings.append(
            "container frame count differs from decoded/extracted frame count; "
            "timestamps in payload are authoritative"
        )

    manifest = MotionSpecManifest(
        asset_id=_asset_id(source, extracted),
        created_at=datetime.now(timezone.utc).isoformat(),
        source=source,
        extractor=extracted.extractor,
        coordinate_spaces=extracted.coordinate_spaces,
        joint_sets=[extracted.joint_set],
        tracks=[
            MotionTrack(
                id="body_pose",
                kind="pose_landmarks",
                joint_set_id=extracted.joint_set.id,
                payload_path="payload/pose.npz",
                arrays=descriptors,
            )
        ],
        rights=rights or RightsMetadata(),
        quality=QualitySummary(
            missing_frame_ratio=missing_ratio,
            mean_confidence=mean_confidence,
            warnings=warnings,
        ),
    )
    manifest.save(out / "manifest.json")
    return manifest


def validate_asset(asset_dir: str | Path) -> MotionSpecManifest:
    asset_dir = Path(asset_dir)
    manifest = MotionSpecManifest.load(asset_dir / "manifest.json")

    joint_set_ids = {joint_set.id for joint_set in manifest.joint_sets}
    coordinate_ids = {space.id for space in manifest.coordinate_spaces}

    for track in manifest.tracks:
        if track.joint_set_id and track.joint_set_id not in joint_set_ids:
            raise ValueError(f"Track {track.id} refers to unknown joint set {track.joint_set_id}")

        payload_path = asset_dir / track.payload_path
        if not payload_path.exists():
            raise FileNotFoundError(f"Missing payload: {payload_path}")

        with np.load(payload_path, allow_pickle=False) as payload:
            for descriptor in track.arrays:
                if descriptor.name not in payload:
                    raise ValueError(
                        f"Payload {track.payload_path} is missing array {descriptor.name}"
                    )
                array = payload[descriptor.name]
                if list(array.shape) != descriptor.shape:
                    raise ValueError(
                        f"Shape mismatch for {descriptor.name}: "
                        f"manifest={descriptor.shape}, payload={list(array.shape)}"
                    )
                if str(array.dtype) != descriptor.dtype:
                    raise ValueError(
                        f"Dtype mismatch for {descriptor.name}: "
                        f"manifest={descriptor.dtype}, payload={array.dtype}"
                    )
                if (
                    descriptor.coordinate_space_id
                    and descriptor.coordinate_space_id not in coordinate_ids
                ):
                    raise ValueError(
                        f"Array {descriptor.name} refers to unknown coordinate space "
                        f"{descriptor.coordinate_space_id}"
                    )

    return manifest
