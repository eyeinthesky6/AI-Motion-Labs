from __future__ import annotations

from pathlib import Path

import numpy as np

from aimotionlabs.extractors.base import ExtractedMotion
from aimotionlabs.models import CoordinateSpace, ExtractorInfo, JointSet


MEDIAPIPE_POSE_33 = [
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
]

# Connectivity is descriptive, not a kinematic parent tree.
MEDIAPIPE_POSE_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (29, 31),
    (27, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (30, 32),
    (28, 32),
]


class MediaPipePoseExtractor:
    """Bootstrap extractor using MediaPipe Pose Landmarker video mode.

    MediaPipe is intentionally treated as a replaceable provider. Its landmarks
    are preserved in provider-native form; MotionSpec does not make them the
    canonical skeleton for all future backends.
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.model_path = Path(model_path)
        self.min_detection_confidence = min_detection_confidence
        self.min_presence_confidence = min_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence

    def extract(self, video_path: str | Path) -> ExtractedMotion:
        try:
            import cv2
            import mediapipe as mp
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError(
                "MediaPipe extraction requires: pip install -e '.[mediapipe]'"
            ) from exc

        if not self.model_path.exists():
            raise FileNotFoundError(f"MediaPipe model not found: {self.model_path}")

        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            cap.release()
            raise RuntimeError("Video FPS could not be determined")

        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=self.min_detection_confidence,
            min_pose_presence_confidence=self.min_presence_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_segmentation_masks=False,
        )

        timestamps: list[int] = []
        positions_2d: list[np.ndarray] = []
        positions_3d: list[np.ndarray] = []
        confidence: list[np.ndarray] = []

        frame_index = 0
        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
            while True:
                ok, frame_bgr = cap.read()
                if not ok:
                    break

                timestamp_ms = int(round(frame_index * 1000.0 / fps))
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=np.ascontiguousarray(frame_rgb),
                )
                result = landmarker.detect_for_video(mp_image, timestamp_ms)

                p2 = np.full((33, 2), np.nan, dtype=np.float32)
                p3 = np.full((33, 3), np.nan, dtype=np.float32)
                conf = np.zeros((33,), dtype=np.float32)

                if result.pose_landmarks:
                    for i, landmark in enumerate(result.pose_landmarks[0]):
                        p2[i] = (float(landmark.x), float(landmark.y))
                        visibility = landmark.visibility
                        presence = landmark.presence
                        scores = [x for x in (visibility, presence) if x is not None]
                        conf[i] = float(min(scores)) if scores else 1.0

                if result.pose_world_landmarks:
                    for i, landmark in enumerate(result.pose_world_landmarks[0]):
                        p3[i] = (float(landmark.x), float(landmark.y), float(landmark.z))

                timestamps.append(timestamp_ms)
                positions_2d.append(p2)
                positions_3d.append(p3)
                confidence.append(conf)
                frame_index += 1

        cap.release()

        if not timestamps:
            raise RuntimeError("No frames were decoded from the input video")

        return ExtractedMotion(
            timestamps_ms=np.asarray(timestamps, dtype=np.int64),
            positions_2d=np.stack(positions_2d),
            positions_3d=np.stack(positions_3d),
            confidence=np.stack(confidence),
            joint_set=JointSet(
                id="mediapipe_pose_33",
                joint_names=MEDIAPIPE_POSE_33,
                connections=MEDIAPIPE_POSE_CONNECTIONS,
                provider="mediapipe",
            ),
            coordinate_spaces=[
                CoordinateSpace(
                    id="image_normalized",
                    dimensions=2,
                    units="normalized",
                    handedness="unknown",
                    up_axis="-y",
                    forward_axis="unknown",
                    origin="top-left of image; x/y normalized by image dimensions",
                ),
                CoordinateSpace(
                    id="mediapipe_pose_world",
                    dimensions=3,
                    units="provider_world",
                    handedness="unknown",
                    up_axis="unknown",
                    forward_axis="unknown",
                    origin="MediaPipe provider-native pose world origin",
                    notes=(
                        "Provider-relative world landmarks. Do not interpret this as a "
                        "world-grounded root trajectory without an additional recovery stage."
                    ),
                ),
            ],
            extractor=ExtractorInfo(
                name="mediapipe_pose_landmarker",
                version=getattr(mp, "__version__", None),
                model=self.model_path.name,
                options={
                    "num_poses": 1,
                    "min_pose_detection_confidence": self.min_detection_confidence,
                    "min_pose_presence_confidence": self.min_presence_confidence,
                    "min_tracking_confidence": self.min_tracking_confidence,
                },
            ),
        )
