from __future__ import annotations

from pathlib import Path

import numpy as np

from aimotionlabs.asset import validate_asset


def render_skeleton_preview(
    asset_dir: str | Path,
    output: str | Path,
    *,
    skeleton_only: bool = False,
    scale: float = 1.0,
) -> Path:
    """Render a lightweight human-inspectable skeleton preview from a MotionSpec asset."""
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - optional preview dependency
        raise RuntimeError("Preview rendering requires opencv-python-headless") from exc

    root = Path(asset_dir)
    manifest = validate_asset(root)
    source = root / manifest.source.original_filename
    if not source.exists():
        raise FileNotFoundError(
            "Original source video is not stored inside the MotionSpec asset; "
            "preview requires the original video path to be supplied separately."
        )

    track = next((t for t in manifest.tracks if t.id == "body_pose"), None)
    if track is None:
        raise ValueError("Asset has no body_pose track")

    with np.load(root / track.payload_path, allow_pickle=False) as payload:
        positions = np.asarray(payload["positions_2d"])
        timestamps = np.asarray(payload["timestamps_ms"])

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open source video: {source}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if width <= 0 or height <= 0 or fps <= 0:
        cap.release()
        raise RuntimeError("Could not determine source video dimensions/FPS")

    width = max(1, int(round(width * scale)))
    height = max(1, int(round(height * scale)))
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open preview writer: {output_path}")

    connections = next(
        js.connections for js in manifest.joint_sets if js.id == track.joint_set_id
    )
    frame_index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            canvas = np.zeros_like(frame) if skeleton_only else frame
            if skeleton_only:
                canvas[:] = 245

            if frame_index < len(positions):
                points = positions[frame_index]
                for a, b in connections:
                    if a >= len(points) or b >= len(points):
                        continue
                    pa, pb = points[a], points[b]
                    if not (np.all(np.isfinite(pa)) and np.all(np.isfinite(pb))):
                        continue
                    p1 = (int(round(float(pa[0]) * width)), int(round(float(pa[1]) * height)))
                    p2 = (int(round(float(pb[0]) * width)), int(round(float(pb[1]) * height)))
                    cv2.line(canvas, p1, p2, (40, 40, 40), 2, cv2.LINE_AA)
                for point in points:
                    if not np.all(np.isfinite(point)):
                        continue
                    center = (
                        int(round(float(point[0]) * width)),
                        int(round(float(point[1]) * height)),
                    )
                    cv2.circle(canvas, center, 3, (40, 40, 40), -1, cv2.LINE_AA)

            timestamp = timestamps[min(frame_index, len(timestamps) - 1)] if len(timestamps) else 0
            cv2.putText(
                canvas,
                f"MotionSpec  t={timestamp / 1000.0:.3f}s",
                (16, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (40, 40, 40),
                2,
                cv2.LINE_AA,
            )
            writer.write(canvas)
            frame_index += 1
    finally:
        cap.release()
        writer.release()

    return output_path
