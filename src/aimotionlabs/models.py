from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceVideo(StrictModel):
    kind: Literal["local_upload", "owned_url_import", "licensed_source"] = "local_upload"
    original_filename: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: float = Field(gt=0)
    frame_count: int = Field(gt=0)
    duration_s: float = Field(gt=0)


class ExtractorInfo(StrictModel):
    name: str
    version: str | None = None
    model: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class CoordinateSpace(StrictModel):
    id: str
    dimensions: Literal[2, 3]
    units: Literal["normalized", "pixels", "meters", "provider_world", "unknown"]
    handedness: Literal["right", "left", "unknown"] = "unknown"
    up_axis: Literal["+x", "-x", "+y", "-y", "+z", "-z", "unknown"] = "unknown"
    forward_axis: Literal["+x", "-x", "+y", "-y", "+z", "-z", "unknown"] = "unknown"
    origin: str
    notes: str | None = None


class JointSet(StrictModel):
    id: str
    joint_names: list[str]
    connections: list[tuple[int, int]] = Field(default_factory=list)
    provider: str | None = None


class PayloadArray(StrictModel):
    name: str
    dtype: str
    shape: list[int]
    semantics: str
    coordinate_space_id: str | None = None


class MotionTrack(StrictModel):
    id: str
    kind: Literal[
        "pose_landmarks",
        "joint_positions",
        "joint_rotations",
        "root_trajectory",
        "contacts",
        "camera",
        "events",
    ]
    joint_set_id: str | None = None
    payload_path: str
    arrays: list[PayloadArray]


class RightsMetadata(StrictModel):
    source_attestation: Literal[
        "user_claims_rights",
        "licensed",
        "public_domain",
        "open_license",
        "unknown",
    ] = "unknown"
    public_share_allowed: bool = False
    commercial_reuse_allowed: bool | None = None
    license_id: str | None = None
    source_url: str | None = None
    notes: str | None = None


class QualitySummary(StrictModel):
    missing_frame_ratio: float = Field(ge=0.0, le=1.0)
    mean_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class MotionSpecManifest(StrictModel):
    schema_name: Literal["motionspec"] = "motionspec"
    schema_version: Literal["0.1.0"] = "0.1.0"
    asset_id: str
    created_at: str
    source: SourceVideo
    extractor: ExtractorInfo
    coordinate_spaces: list[CoordinateSpace]
    joint_sets: list[JointSet]
    tracks: list[MotionTrack]
    rights: RightsMetadata = Field(default_factory=RightsMetadata)
    quality: QualitySummary
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, manifest_path: str | Path) -> "MotionSpecManifest":
        return cls.model_validate_json(Path(manifest_path).read_text(encoding="utf-8"))

    def save(self, manifest_path: str | Path) -> None:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
