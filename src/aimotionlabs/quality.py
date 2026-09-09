from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from aimotionlabs.asset import validate_asset


def _finite_frame_mask(values: np.ndarray) -> np.ndarray:
    if values.ndim < 2:
        raise ValueError("Expected a frame-major array")
    return np.any(np.isfinite(values), axis=tuple(range(1, values.ndim)))


def _median_frame_interval_ms(timestamps_ms: np.ndarray) -> float | None:
    if timestamps_ms.size < 2:
        return None
    return float(np.median(np.diff(timestamps_ms)))


def _joint_velocity_stats(
    positions: np.ndarray, timestamps_ms: np.ndarray
) -> dict[str, float | None]:
    if positions.ndim != 3 or positions.shape[0] < 2:
        return {"median": None, "p95": None, "max": None}

    dt = np.diff(timestamps_ms).astype(np.float64) / 1000.0
    valid_dt = dt > 0
    if not np.any(valid_dt):
        return {"median": None, "p95": None, "max": None}

    delta = np.diff(positions.astype(np.float64), axis=0)
    speed = np.linalg.norm(delta, axis=-1)
    valid = np.isfinite(speed)
    speed = speed[valid]
    # Repeat dt for each joint and discard intervals that are not valid.
    dt_per_joint = np.repeat(dt[:, None], positions.shape[1], axis=1)[valid]
    valid_speed = dt_per_joint > 0
    speed = speed[valid_speed] / dt_per_joint[valid_speed]
    if speed.size == 0:
        return {"median": None, "p95": None, "max": None}
    return {
        "median": float(np.median(speed)),
        "p95": float(np.percentile(speed, 95)),
        "max": float(np.max(speed)),
    }


def _limb_length_variance(positions: np.ndarray, connections: list[tuple[int, int]]) -> float | None:
    if positions.ndim != 3 or not connections:
        return None
    lengths: list[np.ndarray] = []
    for a, b in connections:
        if a >= positions.shape[1] or b >= positions.shape[1]:
            continue
        vector = positions[:, a, :] - positions[:, b, :]
        length = np.linalg.norm(vector.astype(np.float64), axis=-1)
        length = length[np.isfinite(length)]
        if length.size >= 2:
            median = np.median(length)
            if median > 1e-9:
                lengths.append(length / median)
    if not lengths:
        return None
    normalized = np.concatenate(lengths)
    return float(np.std(normalized))


def analyze_asset(asset_dir: str | Path) -> dict[str, Any]:
    """Calculate non-destructive QA signals from a MotionSpec asset.

    This report intentionally does not alter the manifest. It is a diagnostic
    layer for M2; future quality summaries can be promoted into the spec only
    after their semantics are stable.
    """
    root = Path(asset_dir)
    manifest = validate_asset(root)
    track = next((t for t in manifest.tracks if t.id == "body_pose"), None)
    if track is None:
        raise ValueError("Asset has no body_pose track")

    payload_path = root / track.payload_path
    with np.load(payload_path, allow_pickle=False) as payload:
        timestamps = np.asarray(payload["timestamps_ms"])
        positions_2d = np.asarray(payload["positions_2d"]) if "positions_2d" in payload else None
        positions_3d = np.asarray(payload["positions_3d"]) if "positions_3d" in payload else None
        confidence = np.asarray(payload["confidence"]) if "confidence" in payload else None

    basis = positions_2d if positions_2d is not None else positions_3d
    coverage = float(np.mean(_finite_frame_mask(basis))) if basis is not None else 0.0

    confidence_mean = None
    confidence_p10 = None
    if confidence is not None:
        valid = confidence[np.isfinite(confidence)]
        if valid.size:
            confidence_mean = float(np.mean(valid))
            confidence_p10 = float(np.percentile(valid, 10))

    joint_set = next(js for js in manifest.joint_sets if js.id == track.joint_set_id)
    velocity_source = positions_3d if positions_3d is not None else positions_2d

    report: dict[str, Any] = {
        "asset_id": manifest.asset_id,
        "source": manifest.source.model_dump(mode="json"),
        "extractor": manifest.extractor.model_dump(mode="json"),
        "frames": int(timestamps.size),
        "duration_s": float(manifest.source.duration_s),
        "median_frame_interval_ms": _median_frame_interval_ms(timestamps),
        "coverage_ratio": coverage,
        "missing_frame_ratio": 1.0 - coverage,
        "confidence": {
            "mean": confidence_mean,
            "p10": confidence_p10,
        },
        "joint_velocity": _joint_velocity_stats(velocity_source, timestamps)
        if velocity_source is not None
        else None,
        "normalized_bone_length_std": _limb_length_variance(
            positions_3d if positions_3d is not None else positions_2d,
            joint_set.connections,
        )
        if velocity_source is not None
        else None,
        "manifest_warnings": list(manifest.quality.warnings),
    }

    warnings: list[str] = []
    if coverage < 0.95:
        warnings.append("pose coverage below 95%")
    if confidence_p10 is not None and confidence_p10 < 0.35:
        warnings.append("10th percentile joint confidence is below 0.35")
    velocity = report["joint_velocity"]
    if velocity and velocity["p95"] is not None and velocity["max"] is not None:
        if velocity["max"] > max(10.0, float(velocity["p95"]) * 8.0):
            warnings.append("large velocity spike detected; inspect temporal continuity")
    if report["normalized_bone_length_std"] is not None and report["normalized_bone_length_std"] > 0.08:
        warnings.append("bone-length variance is high; inspect pose jitter/occlusion")
    report["warnings"] = warnings
    return report
