from __future__ import annotations

from pathlib import Path

from aimotionlabs.quality import analyze_asset
from tests.test_validator import _build_asset


def test_quality_report_has_core_signals(tmp_path: Path) -> None:
    asset_dir = _build_asset(tmp_path)
    report = analyze_asset(asset_dir)

    assert report["asset_id"] == "motion_synthetic"
    assert report["coverage_ratio"] == 1.0
    assert report["missing_frame_ratio"] == 0.0
    assert report["confidence"]["mean"] == 1.0
    assert report["joint_velocity"]["p95"] is not None
    assert report["normalized_bone_length_std"] is not None


def test_quality_report_flags_low_coverage(tmp_path: Path) -> None:
    asset_dir = _build_asset(tmp_path)
    payload = asset_dir / "payload" / "pose.npz"
    import numpy as np

    with np.load(payload, allow_pickle=False) as data:
        timestamps = data["timestamps_ms"]
        positions = data["positions_2d"].copy()
        confidence = data["confidence"]

    positions[1, :, :] = np.nan
    np.savez_compressed(
        payload,
        timestamps_ms=timestamps,
        positions_2d=positions,
        confidence=confidence,
    )

    # The manifest shape/dtype contract remains valid; this is a quality issue,
    # not a packaging/validation failure.
    report = analyze_asset(asset_dir)
    assert report["coverage_ratio"] < 1.0
    assert "pose coverage below 95%" in report["warnings"]
