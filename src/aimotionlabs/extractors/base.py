from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from aimotionlabs.models import CoordinateSpace, ExtractorInfo, JointSet


@dataclass(slots=True)
class ExtractedMotion:
    """Provider output before it is packaged as MotionSpec.

    Arrays are deliberately generic. A backend may provide only 2D positions,
    only 3D positions, or both. The package layer records exactly what exists.
    """

    timestamps_ms: np.ndarray
    positions_2d: np.ndarray | None
    positions_3d: np.ndarray | None
    confidence: np.ndarray | None
    joint_set: JointSet
    coordinate_spaces: list[CoordinateSpace]
    extractor: ExtractorInfo
    positions_2d_space_id: str | None = None
    positions_3d_space_id: str | None = None


class MotionExtractor(Protocol):
    def extract(self, video_path: str | Path) -> ExtractedMotion:
        """Extract motion observations from a video file."""
        ...
