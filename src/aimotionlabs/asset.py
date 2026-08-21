from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
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


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _asset_id(source: SourceVideo, extracted: ExtractedMotion) -> str:
    """Build an ID from source, motion bytes and the semantics of those bytes.

    Joint names/coordinate spaces/extractor metadata matter: identical numeric
    arrays with different semantics must not accidentally receive the same ID.
    Rights are intentionally excluded because changing visibility/licensing
    metadata should not mutate the identity of the extracted motion itself.
    """

    digest = hashlib.sha256()
    digest.update(b"motionspec:0.1.0\0")
    digest.update(source.sha256.encode("ascii"))
    digest.update(
        _canonical_json_bytes(
            {
                "extractor": extracted.extractor.model_dump(mode="json"),
                "joint_set": extracted.joint_set.model_dump(mode="json"),
                "coordinate_spaces": [
                    space.model_dump(mode="json") for space in extracted.coordinate_spaces
                ],
                "positions_2d_space_id": extracted.positions_2d_space_id,
                "positions_3d_space_id": extracted.positions_3d_space_id,
            }
        )
    )
    digest.update(np.ascontiguousarray(extracted.timestamps_ms).tobytes())
    for array in (extracted.positions_2d, extracted.positions_3d, extracted.confidence):
        if array is not None:
            contiguous = np.ascontiguousarray(array)
            digest.update(str(contiguous.dtype).encode("ascii"))
            digest.update(_canonical_json_bytes(list(contiguous.shape)))
            digest.update(contiguous.tobytes())
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
                coordinate_space_id=extracted.positions_2d_space_id,
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
                coordinate_space_id=extracted.positions_3d_space_id,
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
        created_at=datetime.now(UTC).isoformat(),
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


def _safe_payload_path(asset_root: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError(f"Payload path must be relative: {relative_path}")

    resolved = (asset_root / path).resolve()
    if not resolved.is_relative_to(asset_root.resolve()):
        raise ValueError(f"Payload path escapes asset directory: {relative_path}")
    return resolved


def validate_asset(asset_dir: str | Path) -> MotionSpecManifest:
    asset_dir = Path(asset_dir)
    manifest = MotionSpecManifest.load(asset_dir / "manifest.json")

    joint_set_ids = {joint_set.id for joint_set in manifest.joint_sets}
    coordinate_ids = {space.id for space in manifest.coordinate_spaces}

    for track in manifest.tracks:
        if track.joint_set_id and track.joint_set_id not in joint_set_ids:
            raise ValueError(f"Track {track.id} refers to unknown joint set {track.joint_set_id}")

        payload_path = _safe_payload_path(asset_dir, track.payload_path)
        if not payload_path.exists():
            raise FileNotFoundError(f"Missing payload: {payload_path}")

        with np.load(payload_path, allow_pickle=False) as payload:
            descriptors = {descriptor.name: descriptor for descriptor in track.arrays}

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

            if "timestamps_ms" in descriptors:
                timestamps = np.asarray(payload["timestamps_ms"])
                if timestamps.ndim != 1:
                    raise ValueError(f"Track {track.id} timestamps_ms must be one-dimensional")
                if timestamps.size == 0:
                    raise ValueError(f"Track {track.id} timestamps_ms must not be empty")
                if np.any(np.diff(timestamps) <= 0):
                    raise ValueError(f"Track {track.id} timestamps_ms must be strictly increasing")

                if track.kind in {"pose_landmarks", "joint_positions", "joint_rotations"}:
                    for name in ("positions_2d", "positions_3d", "confidence"):
                        if name in descriptors and payload[name].shape[0] != timestamps.shape[0]:
                            raise ValueError(
                                f"Track {track.id} array {name} does not match timestamp count"
                            )

    return manifest
