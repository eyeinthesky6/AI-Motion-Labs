from __future__ import annotations

import json
from pathlib import Path

from aimotionlabs.models import MotionSpecManifest


ROOT = Path(__file__).resolve().parents[1]


def test_example_manifest_parses() -> None:
    example = ROOT / "examples" / "manifest.example.json"
    manifest = MotionSpecManifest.model_validate_json(example.read_text(encoding="utf-8"))

    assert manifest.schema_name == "motionspec"
    assert manifest.schema_version == "0.1.0"
    assert manifest.tracks[0].payload_path == "payload/pose.npz"
    assert manifest.rights.public_share_allowed is False


def test_checked_json_schema_matches_runtime_model() -> None:
    expected = MotionSpecManifest.model_json_schema()
    expected["$id"] = (
        "https://raw.githubusercontent.com/eyeinthesky6/AI-Motion-Labs/"
        "main/spec/motionspec-v0.1.schema.json"
    )
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"

    checked = json.loads((ROOT / "spec" / "motionspec-v0.1.schema.json").read_text())
    assert checked == expected
